from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.schemas import CreateCampaignRequest
from app.services.campaigns import create_campaign, with_campaign_prefix


@dataclass
class FakeKeitaro:
    offers: dict[int, dict] = field(default_factory=dict)
    domains: dict[int, dict] = field(default_factory=dict)
    campaigns: dict[int, dict] = field(default_factory=dict)
    streams: dict[int, dict] = field(default_factory=dict)
    created_campaign: dict | None = None
    created_streams: list[dict] = field(default_factory=list)
    next_campaign_id: int = 50
    next_stream_id: int = 200

    def get_offer(self, offer_id: int) -> dict:
        return self.offers[offer_id]

    def get_domain(self, domain_id: int) -> dict:
        return self.domains[domain_id]

    def list_stream_filters(self) -> list[dict]:
        return [{"value": "country"}]

    def list_stream_actions(self) -> list[dict]:
        return [{"key": "http"}]

    def list_offers(self) -> list[dict]:
        return list(self.offers.values())

    def create_campaign(self, payload: dict) -> dict:
        campaign_id = self.next_campaign_id
        self.next_campaign_id += 1
        created = {"id": campaign_id, **payload}
        self.created_campaign = created
        self.campaigns[campaign_id] = created
        return created

    def create_stream(self, payload: dict) -> dict:
        stream_id = self.next_stream_id
        self.next_stream_id += 1
        created = {"id": stream_id, **payload}
        self.created_streams.append(created)
        self.streams[stream_id] = created
        return created

    def get_campaign(self, campaign_id: int) -> dict:
        return self.campaigns[campaign_id]

    def get_campaign_streams(self, campaign_id: int) -> list[dict]:
        return [stream for stream in self.streams.values() if stream.get("campaign_id") == campaign_id]


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> FakeKeitaro:
    return FakeKeitaro(
        offers={18813: {"id": 18813, "name": "Flexacil"}},
        domains={1813: {"id": 1813, "name": "kylovoa.com"}},
    )


def test_create_campaign_matches_tz(db: Session, client: FakeKeitaro) -> None:
    payload = CreateCampaignRequest(
        name="campaign1",
        country_code="de",
        offer_id=18813,
        domain_id=1813,
        group_id=42,
        traffic_source_id=7,
    )
    result = create_campaign(db, client, payload)

    assert client.created_campaign is not None
    assert client.created_campaign["name"] == "test_ukolov_campaign1"
    assert client.created_campaign["type"] == "position"
    assert client.created_campaign["domain_id"] == 1813
    assert client.created_campaign["group_id"] == 42
    assert client.created_campaign["traffic_source_id"] == 7

    assert len(client.created_streams) == 2
    geo, offers = client.created_streams
    assert geo["type"] == "regular"
    assert geo["schema"] == "redirect"
    assert geo["action_payload"] == "https://www.google.com"
    assert geo["filters"] == [{"name": "country", "mode": "accept", "payload": ["DE"]}]
    assert offers["type"] == "default"
    assert offers["offers"] == [{"offer_id": 18813, "share": 100, "state": "active"}]

    google = next(stream for stream in result.streams if "Google" in stream.name)
    offer_stream = next(stream for stream in result.streams if stream.name == "Offers")
    assert google.offers == []
    assert offer_stream.offers[0].keitaro_offer_id == 18813
    assert offer_stream.offers[0].share == 100
    assert result.name.startswith("test_ukolov_")


def test_prefix_helper() -> None:
    assert with_campaign_prefix("campaign1", "test_ukolov_") == "test_ukolov_campaign1"
    assert with_campaign_prefix("test_ukolov_campaign1", "test_ukolov_") == "test_ukolov_campaign1"
