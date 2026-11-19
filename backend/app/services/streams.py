from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload

from app.keitaro.client import KeitaroClient, KeitaroError
from app.models import Campaign, Stream, StreamOffer
from app.schemas import CampaignOut
from app.services.snapshots import (
    campaign_to_out,
    refresh_dirty,
    redistribute_stream,
    snapshot_from_stream,
)


def fetch_streams(db: Session, client: KeitaroClient, campaign_id: int) -> CampaignOut:
    remote_campaign = client.get_campaign(campaign_id)
    local = db.get(Campaign, campaign_id)
    if local is None:
        local = Campaign(keitaro_id=campaign_id)
        db.add(local)
    local.name = str(remote_campaign.get("name") or local.name or f"Campaign {campaign_id}")
    local.alias = str(remote_campaign.get("alias") or local.alias or "")
    if remote_campaign.get("domain_id") is not None:
        local.domain_id = remote_campaign.get("domain_id")
    if remote_campaign.get("group_id") is not None:
        local.group_id = remote_campaign.get("group_id")
    if remote_campaign.get("traffic_source_id") is not None:
        local.traffic_source_id = remote_campaign.get("traffic_source_id")

    offer_names = _offer_names(client)
    remote_streams = client.get_campaign_streams(campaign_id)
    seen_ids: set[int] = set()

    for remote in remote_streams:
        stream_id = int(remote["id"])
        seen_ids.add(stream_id)
        stream = db.query(Stream).filter(Stream.keitaro_id == stream_id).one_or_none()
        if stream is None:
            stream = Stream(keitaro_id=stream_id, campaign_id=campaign_id, name=str(remote.get("name") or f"Stream {stream_id}"))
            db.add(stream)
            db.flush()
        stream.campaign_id = campaign_id
        stream.name = str(remote.get("name") or stream.name)
        _merge_offers(stream, remote.get("offers") or [], offer_names)

    stale_query = db.query(Stream).filter(Stream.campaign_id == campaign_id)
    stale = (
        stale_query.filter(Stream.keitaro_id.notin_(seen_ids)).all()
        if seen_ids
        else stale_query.all()
    )
    for stream in stale:
        db.delete(stream)

    db.commit()
    return _load_campaign(db, campaign_id)


def add_offer(db: Session, client: KeitaroClient, stream_id: int, offer_id: int) -> CampaignOut:
    stream = _get_stream(db, stream_id)
    existing = _find_offer(stream, offer_id)
    if existing and existing.status == "active":
        raise HTTPException(status_code=409, detail="Оффер уже в этом потоке")

    offer = client.get_offer(offer_id)
    name = str(offer.get("name") or f"Offer #{offer_id}")
    if existing:
        existing.status = "active"
        existing.name = name
        existing.is_pinned = False
    else:
        stream.offers.append(
            StreamOffer(
                keitaro_offer_id=offer_id,
                name=name,
                share=0,
                is_pinned=False,
                status="active",
            )
        )
    redistribute_stream(stream)
    db.commit()
    return _load_campaign(db, stream.campaign_id)


def remove_offer(db: Session, stream_id: int, offer_id: int) -> CampaignOut:
    stream = _get_stream(db, stream_id)
    offer = _require_offer(stream, offer_id)
    offer.status = "removed"
    offer.share = 0
    offer.is_pinned = False
    redistribute_stream(stream)
    db.commit()
    return _load_campaign(db, stream.campaign_id)


def restore_offer(db: Session, stream_id: int, offer_id: int) -> CampaignOut:
    stream = _get_stream(db, stream_id)
    offer = _require_offer(stream, offer_id)
    offer.status = "active"
    redistribute_stream(stream)
    db.commit()
    return _load_campaign(db, stream.campaign_id)


def pin_offer(db: Session, stream_id: int, offer_id: int, pinned: bool, share: int | None) -> CampaignOut:
    stream = _get_stream(db, stream_id)
    offer = _require_offer(stream, offer_id)
    if offer.status != "active":
        raise HTTPException(status_code=400, detail="Закрепить можно только активный оффер")
    if share is not None:
        offer.share = share
    offer.is_pinned = pinned
    _validate_pinned_sum(stream)
    redistribute_stream(stream)
    db.commit()
    return _load_campaign(db, stream.campaign_id)


def push_stream(db: Session, client: KeitaroClient, stream_id: int) -> CampaignOut:
    stream = _get_stream(db, stream_id)
    payload = {
        "offers": [
            {
                "offer_id": offer.keitaro_offer_id,
                "share": offer.share,
                "state": "active",
            }
            for offer in stream.offers
            if offer.status == "active"
        ]
    }
    client.update_stream(stream.keitaro_id, payload)
    stream.published_snapshot = snapshot_from_stream(stream)
    stream.is_dirty = False
    db.commit()
    return _load_campaign(db, stream.campaign_id)


def cancel_stream(db: Session, stream_id: int) -> CampaignOut:
    stream = _get_stream(db, stream_id)
    snapshot_offers = (stream.published_snapshot or {}).get("offers", [])
    snapshot_ids = {int(item["keitaro_offer_id"]) for item in snapshot_offers}

    for offer in list(stream.offers):
        if offer.keitaro_offer_id not in snapshot_ids:
            stream.offers.remove(offer)
            db.delete(offer)

    by_id = {offer.keitaro_offer_id: offer for offer in stream.offers}
    for item in snapshot_offers:
        offer_id = int(item["keitaro_offer_id"])
        offer = by_id.get(offer_id)
        if offer is None:
            offer = StreamOffer(keitaro_offer_id=offer_id, stream=stream)
            db.add(offer)
        offer.name = str(item.get("name") or f"Offer #{offer_id}")
        offer.share = int(item.get("share") or 0)
        offer.is_pinned = bool(item.get("is_pinned"))
        offer.status = str(item.get("status") or "active")

    db.flush()
    stream.is_dirty = False
    db.commit()
    return _load_campaign(db, stream.campaign_id)


def _merge_offers(stream: Stream, remote_offers: list[dict], offer_names: dict[int, str]) -> None:
    remote_by_id: dict[int, dict] = {}
    for item in remote_offers:
        offer_id = item.get("offer_id")
        nested = item.get("offer")
        if offer_id is None and isinstance(nested, dict):
            offer_id = nested.get("id")
        if offer_id is None:
            continue
        remote_by_id[int(offer_id)] = item
        nested_name = nested.get("name") if isinstance(nested, dict) else None
        if nested_name:
            offer_names[int(offer_id)] = str(nested_name)

    local_by_id = {offer.keitaro_offer_id: offer for offer in stream.offers}

    if not stream.is_dirty:
        for offer_id, remote in remote_by_id.items():
            local = local_by_id.get(offer_id)
            if local is None:
                local = StreamOffer(keitaro_offer_id=offer_id, stream=stream)
                stream.offers.append(local)
            local.status = "active"
            local.share = int(remote.get("share") or 0)
            local.name = offer_names.get(offer_id, local.name or f"Offer #{offer_id}")
        for local in stream.offers:
            if local.keitaro_offer_id not in remote_by_id and local.status == "active":
                local.status = "removed"
                local.share = 0
                local.is_pinned = False
        stream.published_snapshot = snapshot_from_stream(stream)
        stream.is_dirty = False
        return

    for local in stream.offers:
        if local.status == "active" and local.keitaro_offer_id not in remote_by_id:
            local.status = "removed"
            local.share = 0
            local.is_pinned = False
    for offer_id, remote in remote_by_id.items():
        if offer_id in local_by_id:
            continue
        stream.offers.append(
            StreamOffer(
                keitaro_offer_id=offer_id,
                name=offer_names.get(offer_id, f"Offer #{offer_id}"),
                share=int(remote.get("share") or 0),
                is_pinned=False,
                status="active",
            )
        )
    refresh_dirty(stream)


def _offer_names(client: KeitaroClient) -> dict[int, str]:
    try:
        offers = client.list_offers()
    except KeitaroError:
        return {}
    names: dict[int, str] = {}
    for offer in offers:
        if offer.get("id") is None:
            continue
        names[int(offer["id"])] = str(offer.get("name") or f"Offer #{offer['id']}")
    return names


def _get_stream(db: Session, stream_id: int) -> Stream:
    stream = (
        db.query(Stream)
        .options(selectinload(Stream.offers))
        .filter(Stream.id == stream_id)
        .one_or_none()
    )
    if stream is None:
        raise HTTPException(status_code=404, detail="Поток не найден")
    return stream


def _find_offer(stream: Stream, offer_id: int) -> StreamOffer | None:
    for offer in stream.offers:
        if offer.keitaro_offer_id == offer_id:
            return offer
    return None


def _require_offer(stream: Stream, offer_id: int) -> StreamOffer:
    offer = _find_offer(stream, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Оффера нет в этом потоке")
    return offer


def _validate_pinned_sum(stream: Stream) -> None:
    pinned_sum = sum(offer.share for offer in stream.offers if offer.status == "active" and offer.is_pinned)
    if pinned_sum > 100:
        raise HTTPException(status_code=400, detail="Сумма закреплённых долей не может быть больше 100%")


def _load_campaign(db: Session, campaign_id: int) -> CampaignOut:
    campaign = (
        db.query(Campaign)
        .options(selectinload(Campaign.streams).selectinload(Stream.offers))
        .filter(Campaign.keitaro_id == campaign_id)
        .one_or_none()
    )
    if campaign is None:
        raise HTTPException(status_code=404, detail="Кампания не найдена")
    streams = sorted(campaign.streams, key=lambda item: item.keitaro_id)
    return campaign_to_out(campaign, streams)
