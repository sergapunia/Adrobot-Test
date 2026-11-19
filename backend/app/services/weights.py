from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OfferShare:
    keitaro_offer_id: int
    share: int
    is_pinned: bool
    status: str


def redistribute(offers: list[OfferShare]) -> list[OfferShare]:
    """Split 100% across active offers, keeping pinned shares fixed.

    Remainder from integer division goes to the first unpinned offers,
    so three unpinned offers become 34/33/33.
    """
    for offer in offers:
        if offer.status != "active":
            offer.share = 0

    active = [offer for offer in offers if offer.status == "active"]
    pinned = [offer for offer in active if offer.is_pinned]
    unpinned = [offer for offer in active if not offer.is_pinned]

    pinned_sum = sum(offer.share for offer in pinned)
    remainder = max(0, 100 - pinned_sum)

    if not unpinned:
        return offers

    base, extra = divmod(remainder, len(unpinned))
    for index, offer in enumerate(unpinned):
        offer.share = base + (1 if index < extra else 0)
    return offers
