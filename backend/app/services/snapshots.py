from __future__ import annotations

from app.models import Stream, StreamOffer
from app.schemas import CampaignOut, StreamOfferOut, StreamOut
from app.services.weights import OfferShare, redistribute


def snapshot_from_stream(stream: Stream) -> dict:
    return {
        "offers": [
            {
                "keitaro_offer_id": offer.keitaro_offer_id,
                "name": offer.name,
                "share": offer.share,
                "is_pinned": offer.is_pinned,
                "status": offer.status,
            }
            for offer in stream.offers
        ]
    }


def active_signature(offers: list[StreamOffer] | list[dict]) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    for offer in offers:
        if isinstance(offer, dict):
            if offer.get("status") != "active":
                continue
            pairs.append((int(offer["keitaro_offer_id"]), int(offer["share"])))
        else:
            if offer.status != "active":
                continue
            pairs.append((offer.keitaro_offer_id, offer.share))
    return sorted(pairs)


def refresh_dirty(stream: Stream) -> None:
    snapshot = stream.published_snapshot or {"offers": []}
    stream.is_dirty = active_signature(stream.offers) != active_signature(snapshot.get("offers", []))


def redistribute_stream(stream: Stream) -> None:
    shares = [
        OfferShare(
            keitaro_offer_id=offer.keitaro_offer_id,
            share=offer.share,
            is_pinned=offer.is_pinned,
            status=offer.status,
        )
        for offer in stream.offers
    ]
    redistribute(shares)
    by_id = {item.keitaro_offer_id: item for item in shares}
    for offer in stream.offers:
        updated = by_id[offer.keitaro_offer_id]
        offer.share = updated.share
    refresh_dirty(stream)


def stream_to_out(stream: Stream) -> StreamOut:
    offers = [
        StreamOfferOut(
            keitaro_offer_id=offer.keitaro_offer_id,
            name=offer.name,
            share=offer.share,
            is_pinned=offer.is_pinned,
            status=offer.status,
        )
        for offer in stream.offers
    ]
    return StreamOut(
        id=stream.id,
        keitaro_id=stream.keitaro_id,
        name=stream.name,
        is_dirty=stream.is_dirty,
        has_offers=any(True for _ in stream.offers),
        offers=offers,
    )


def campaign_to_out(campaign, streams: list[Stream] | None = None) -> CampaignOut:
    stream_models = streams if streams is not None else list(campaign.streams)
    return CampaignOut(
        keitaro_id=campaign.keitaro_id,
        name=campaign.name,
        alias=campaign.alias,
        domain_id=campaign.domain_id,
        group_id=campaign.group_id,
        traffic_source_id=campaign.traffic_source_id,
        campaign_url=campaign.campaign_url,
        streams=[stream_to_out(stream) for stream in stream_models],
    )
