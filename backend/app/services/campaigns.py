from __future__ import annotations

import re
import secrets
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.keitaro.client import KeitaroClient, KeitaroError
from app.models import Campaign
from app.schemas import CampaignOut, CreateCampaignRequest
from app.services.snapshots import campaign_to_out
from app.services.streams import fetch_streams


GOOGLE_URL = "https://www.google.com"


def with_campaign_prefix(name: str, prefix: str | None = None) -> str:
    cleaned = name.strip()
    tag = prefix or settings.campaign_name_prefix
    if cleaned.lower().startswith(tag.lower()):
        return f"{tag}{cleaned[len(tag):]}"
    return f"{tag}{cleaned}"


def create_campaign(db: Session, client: KeitaroClient, payload: CreateCampaignRequest) -> CampaignOut:
    country = payload.country_code.upper()
    client.get_offer(payload.offer_id)
    name = with_campaign_prefix(payload.name)

    campaign_body: dict[str, Any] = {
        "name": name,
        "alias": _make_alias(name),
        "type": "position",
        "state": "active",
        "domain_id": payload.domain_id,
        "traffic_source_id": payload.traffic_source_id,
    }
    if payload.group_id:
        campaign_body["group_id"] = payload.group_id

    created = client.create_campaign(campaign_body)
    campaign_id = int(created["id"])
    alias = str(created.get("alias") or campaign_body["alias"])
    campaign_url = _campaign_url(client, payload.domain_id, alias)

    geo_stream = {
        "campaign_id": campaign_id,
        "type": "regular",
        "name": f"{country} → Google",
        "position": 1,
        "schema": "redirect",
        "action_type": _http_action_type(client),
        "action_payload": GOOGLE_URL,
        "collect_clicks": True,
        "filters": [
            {
                "name": _country_filter_name(client),
                "mode": "accept",
                "payload": [country],
            }
        ],
    }
    offer_stream = {
        "campaign_id": campaign_id,
        "type": "default",
        "name": "Offers",
        "position": 2,
        "schema": "landings",
        "action_type": _http_action_type(client),
        "collect_clicks": True,
        "offers": [
            {
                "offer_id": payload.offer_id,
                "share": 100,
                "state": "active",
            }
        ],
    }

    try:
        client.create_stream(geo_stream)
        client.create_stream(offer_stream)
    except KeitaroError:
        raise

    local = db.get(Campaign, campaign_id)
    if local is None:
        local = Campaign(keitaro_id=campaign_id)
        db.add(local)
    local.name = name
    local.alias = alias
    local.domain_id = payload.domain_id
    local.group_id = payload.group_id
    local.traffic_source_id = payload.traffic_source_id
    local.campaign_url = campaign_url
    db.commit()

    return fetch_streams(db, client, campaign_id)


def get_campaign(db: Session, client: KeitaroClient, campaign_id: int) -> CampaignOut:
    local = db.get(Campaign, campaign_id)
    if local is not None and local.streams:
        return campaign_to_out(local)

    remote = client.get_campaign(campaign_id)
    if local is None:
        local = Campaign(
            keitaro_id=campaign_id,
            name=str(remote.get("name") or f"Campaign {campaign_id}"),
            alias=str(remote.get("alias") or ""),
            domain_id=remote.get("domain_id"),
            group_id=remote.get("group_id"),
            traffic_source_id=remote.get("traffic_source_id"),
            campaign_url=_campaign_url(client, remote.get("domain_id"), str(remote.get("alias") or "")),
        )
        db.add(local)
        db.commit()
    return campaign_to_out(local)


def list_campaigns(db: Session) -> list[CampaignOut]:
    campaigns = db.query(Campaign).order_by(Campaign.created_at.desc()).all()
    return [campaign_to_out(campaign) for campaign in campaigns]


def _make_alias(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40].strip("-")
    suffix = secrets.token_hex(3)
    return f"{slug}-{suffix}" if slug else suffix


def _campaign_url(client: KeitaroClient, domain_id: int | None, alias: str) -> str | None:
    if not domain_id or not alias:
        return None
    try:
        domain = client.get_domain(int(domain_id))
    except KeitaroError:
        return None
    host = str(domain.get("name") or "").rstrip("/")
    if not host:
        return None
    if not host.startswith("http"):
        host = f"https://{host}"
    return f"{host}/{alias}"


def _country_filter_name(client: KeitaroClient) -> str:
    try:
        filters = client.list_stream_filters()
    except KeitaroError:
        return "country"
    names = [_filter_key(item) for item in filters]
    for candidate in ("country", "geo"):
        if candidate in names:
            return candidate
    return "country"


def _http_action_type(client: KeitaroClient) -> str:
    try:
        actions = client.list_stream_actions()
    except KeitaroError:
        return "http"
    keys = [str(item.get("key") or item.get("type") or "").lower() for item in actions]
    for candidate in ("http", "redirect"):
        if candidate in keys:
            return candidate
    return "http"


def _filter_key(item: dict[str, Any]) -> str:
    return str(item.get("value") or item.get("name") or item.get("key") or "").lower()
