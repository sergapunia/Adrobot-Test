from __future__ import annotations

from pydantic import BaseModel, Field


class CatalogItem(BaseModel):
    id: int
    name: str


class CreateCatalogItem(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class CreateCampaignRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    country_code: str = Field(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$")
    offer_id: int = Field(gt=0)
    domain_id: int = Field(gt=0)
    group_id: int | None = None
    traffic_source_id: int = Field(gt=0)


class StreamOfferOut(BaseModel):
    keitaro_offer_id: int
    name: str
    share: int
    is_pinned: bool
    status: str


class StreamOut(BaseModel):
    id: int
    keitaro_id: int
    name: str
    is_dirty: bool
    has_offers: bool
    offers: list[StreamOfferOut]


class CampaignOut(BaseModel):
    keitaro_id: int
    name: str
    alias: str
    domain_id: int | None
    group_id: int | None
    traffic_source_id: int | None
    campaign_url: str | None
    streams: list[StreamOut] = []


class AddOfferRequest(BaseModel):
    offer_id: int = Field(gt=0)


class PinOfferRequest(BaseModel):
    pinned: bool
    share: int | None = Field(default=None, ge=0, le=100)
