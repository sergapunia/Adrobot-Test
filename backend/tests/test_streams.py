from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models import Campaign
from app.services import streams as stream_service


@dataclass
class FakeKeitaro:
    offers: dict[int, dict] = field(default_factory=dict)
    streams: dict[int, dict] = field(default_factory=dict)
    campaign: dict = field(default_factory=lambda: {"id": 10, "name": "Test", "alias": "test"})
    pushed: dict[int, dict] = field(default_factory=dict)

    def get_campaign(self, campaign_id: int) -> dict:
        return {**self.campaign, "id": campaign_id}

    def get_campaign_streams(self, _campaign_id: int) -> list[dict]:
        return list(self.streams.values())

    def list_offers(self) -> list[dict]:
        return list(self.offers.values())

    def get_offer(self, offer_id: int) -> dict:
        return self.offers[offer_id]

    def update_stream(self, stream_id: int, payload: dict) -> dict:
        self.pushed[stream_id] = payload
        self.streams[stream_id] = {
            **self.streams.get(stream_id, {"id": stream_id, "name": "Offers"}),
            "offers": payload["offers"],
        }
        return self.streams[stream_id]


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(Campaign(keitaro_id=10, name="Test", alias="test"))
    session.commit()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> FakeKeitaro:
    return FakeKeitaro(
        offers={
            1: {"id": 1, "name": "Offer A"},
            2: {"id": 2, "name": "Offer B"},
            3: {"id": 3, "name": "Offer C"},
            4: {"id": 4, "name": "Offer D"},
        },
        streams={
            101: {"id": 101, "name": "AU → Google", "offers": []},
            102: {"id": 102, "name": "Offers", "offers": [{"offer_id": 1, "share": 100}]},
        },
    )


def _offers_stream(campaign):
    return next(stream for stream in campaign.streams if stream.name == "Offers")


def test_fetch_keeps_empty_stream_as_stub(db: Session, client: FakeKeitaro) -> None:
    campaign = stream_service.fetch_streams(db, client, 10)
    google = next(stream for stream in campaign.streams if "Google" in stream.name)
    offers = _offers_stream(campaign)
    assert google.offers == []
    assert not google.has_offers
    assert offers.offers[0].share == 100
    assert not offers.is_dirty


def test_add_recalculates_shares_and_marks_dirty(db: Session, client: FakeKeitaro) -> None:
    stream_service.fetch_streams(db, client, 10)
    stream = _offers_stream(stream_service.fetch_streams(db, client, 10))
    campaign = stream_service.add_offer(db, client, stream.id, 2)
    stream = _offers_stream(campaign)
    assert stream.is_dirty
    assert sorted(offer.share for offer in stream.offers if offer.status == "active") == [50, 50]


def test_four_offers_are_25_each(db: Session, client: FakeKeitaro) -> None:
    stream_service.fetch_streams(db, client, 10)
    stream_id = _offers_stream(stream_service.fetch_streams(db, client, 10)).id
    stream_service.add_offer(db, client, stream_id, 2)
    stream_service.add_offer(db, client, stream_id, 3)
    campaign = stream_service.add_offer(db, client, stream_id, 4)
    shares = [offer.share for offer in _offers_stream(campaign).offers if offer.status == "active"]
    assert shares == [25, 25, 25, 25]


def test_remove_zeros_share_and_keeps_row(db: Session, client: FakeKeitaro) -> None:
    stream_service.fetch_streams(db, client, 10)
    stream_id = _offers_stream(stream_service.fetch_streams(db, client, 10)).id
    stream_service.add_offer(db, client, stream_id, 2)
    campaign = stream_service.remove_offer(db, stream_id, 2)
    removed = next(offer for offer in _offers_stream(campaign).offers if offer.keitaro_offer_id == 2)
    assert removed.status == "removed"
    assert removed.share == 0


def test_cancel_drops_unpublished_add(db: Session, client: FakeKeitaro) -> None:
    stream_service.fetch_streams(db, client, 10)
    stream_id = _offers_stream(stream_service.fetch_streams(db, client, 10)).id
    stream_service.add_offer(db, client, stream_id, 2)
    campaign = stream_service.cancel_stream(db, stream_id)
    stream = _offers_stream(campaign)
    assert not stream.is_dirty
    assert [offer.keitaro_offer_id for offer in stream.offers] == [1]


def test_pin_is_kept_when_adding(db: Session, client: FakeKeitaro) -> None:
    stream_service.fetch_streams(db, client, 10)
    stream_id = _offers_stream(stream_service.fetch_streams(db, client, 10)).id
    stream_service.add_offer(db, client, stream_id, 2)
    stream_service.add_offer(db, client, stream_id, 3)
    stream_service.add_offer(db, client, stream_id, 4)
    stream_service.pin_offer(db, stream_id, 1, True, None)
    campaign = stream_service.remove_offer(db, stream_id, 4)
    pinned = next(offer for offer in _offers_stream(campaign).offers if offer.keitaro_offer_id == 1)
    assert pinned.share == 25
    active = [offer.share for offer in _offers_stream(campaign).offers if offer.status == "active"]
    assert sum(active) == 100


def test_push_sends_only_active_offers(db: Session, client: FakeKeitaro) -> None:
    stream_service.fetch_streams(db, client, 10)
    stream_id = _offers_stream(stream_service.fetch_streams(db, client, 10)).id
    stream_service.add_offer(db, client, stream_id, 2)
    stream_service.remove_offer(db, stream_id, 2)
    stream_service.push_stream(db, client, stream_id)
    payload = client.pushed[102]
    assert [item["offer_id"] for item in payload["offers"]] == [1]


def test_bring_back_restores_share(db: Session, client: FakeKeitaro) -> None:
    stream_service.fetch_streams(db, client, 10)
    stream_id = _offers_stream(stream_service.fetch_streams(db, client, 10)).id
    stream_service.add_offer(db, client, stream_id, 2)
    stream_service.remove_offer(db, stream_id, 2)
    campaign = stream_service.restore_offer(db, stream_id, 2)
    restored = next(offer for offer in _offers_stream(campaign).offers if offer.keitaro_offer_id == 2)
    assert restored.status == "active"
    assert sorted(offer.share for offer in _offers_stream(campaign).offers if offer.status == "active") == [50, 50]


def test_cancel_after_remove_restores_published(db: Session, client: FakeKeitaro) -> None:
    stream_service.fetch_streams(db, client, 10)
    stream_id = _offers_stream(stream_service.fetch_streams(db, client, 10)).id
    stream_service.remove_offer(db, stream_id, 1)
    campaign = stream_service.cancel_stream(db, stream_id)
    offer = _offers_stream(campaign).offers[0]
    assert offer.status == "active"
    assert offer.share == 100
    assert not _offers_stream(campaign).is_dirty


def test_fetch_marks_keitaro_deletions_removed(db: Session, client: FakeKeitaro) -> None:
    stream_service.fetch_streams(db, client, 10)
    stream_id = _offers_stream(stream_service.fetch_streams(db, client, 10)).id
    stream_service.add_offer(db, client, stream_id, 2)
    stream_service.push_stream(db, client, stream_id)
    client.streams[102]["offers"] = [{"offer_id": 1, "share": 100}]
    campaign = stream_service.fetch_streams(db, client, 10)
    removed = next(offer for offer in _offers_stream(campaign).offers if offer.keitaro_offer_id == 2)
    assert removed.status == "removed"
    assert removed.share == 0
