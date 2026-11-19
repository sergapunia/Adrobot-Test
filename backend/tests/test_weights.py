from app.services.weights import OfferShare, redistribute


def _ids(shares: list[int], pinned: list[bool] | None = None) -> list[OfferShare]:
    flags = pinned or [False] * len(shares)
    return [
        OfferShare(keitaro_offer_id=index + 1, share=share, is_pinned=flag, status="active")
        for index, (share, flag) in enumerate(zip(shares, flags, strict=True))
    ]


def test_three_offers_split_34_33_33() -> None:
    offers = redistribute(_ids([0, 0, 0]))
    assert [offer.share for offer in offers] == [34, 33, 33]
    assert sum(offer.share for offer in offers) == 100


def test_four_offers_split_evenly() -> None:
    offers = redistribute(_ids([0, 0, 0, 0]))
    assert [offer.share for offer in offers] == [25, 25, 25, 25]


def test_removed_offers_get_zero() -> None:
    offers = [
        OfferShare(1, 50, False, "active"),
        OfferShare(2, 50, False, "removed"),
        OfferShare(3, 0, False, "active"),
    ]
    redistribute(offers)
    by_id = {offer.keitaro_offer_id: offer.share for offer in offers}
    assert by_id[2] == 0
    assert by_id[1] + by_id[3] == 100


def test_pinned_share_is_kept() -> None:
    offers = [
        OfferShare(1, 25, True, "active"),
        OfferShare(2, 0, False, "active"),
        OfferShare(3, 0, False, "active"),
    ]
    redistribute(offers)
    assert offers[0].share == 25
    assert sorted(offer.share for offer in offers[1:]) == [37, 38]
    assert sum(offer.share for offer in offers) == 100


def test_bring_back_keeps_pin() -> None:
    offers = [
        OfferShare(1, 25, True, "active"),
        OfferShare(2, 75, False, "active"),
        OfferShare(3, 0, False, "active"),
    ]
    redistribute(offers)
    assert offers[0].share == 25
    assert offers[1].share + offers[2].share == 75
    assert sum(offer.share for offer in offers) == 100
