from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_keitaro
from app.keitaro.client import KeitaroClient
from app.schemas import AddOfferRequest, CampaignOut, PinOfferRequest
from app.services import streams as stream_service

router = APIRouter(prefix="/api/streams", tags=["streams"])


@router.post("/{stream_id}/offers", response_model=CampaignOut)
def add_offer(
    stream_id: int,
    payload: AddOfferRequest,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(get_keitaro),
) -> CampaignOut:
    return stream_service.add_offer(db, client, stream_id, payload.offer_id)


@router.post("/{stream_id}/offers/{offer_id}/remove", response_model=CampaignOut)
def remove_offer(stream_id: int, offer_id: int, db: Session = Depends(get_db)) -> CampaignOut:
    return stream_service.remove_offer(db, stream_id, offer_id)


@router.post("/{stream_id}/offers/{offer_id}/restore", response_model=CampaignOut)
def restore_offer(stream_id: int, offer_id: int, db: Session = Depends(get_db)) -> CampaignOut:
    return stream_service.restore_offer(db, stream_id, offer_id)


@router.post("/{stream_id}/offers/{offer_id}/pin", response_model=CampaignOut)
def pin_offer(
    stream_id: int,
    offer_id: int,
    payload: PinOfferRequest,
    db: Session = Depends(get_db),
) -> CampaignOut:
    return stream_service.pin_offer(db, stream_id, offer_id, payload.pinned, payload.share)


@router.post("/{stream_id}/push", response_model=CampaignOut)
def push_stream(
    stream_id: int,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(get_keitaro),
) -> CampaignOut:
    return stream_service.push_stream(db, client, stream_id)


@router.post("/{stream_id}/cancel", response_model=CampaignOut)
def cancel_stream(stream_id: int, db: Session = Depends(get_db)) -> CampaignOut:
    return stream_service.cancel_stream(db, stream_id)
