from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_keitaro
from app.keitaro.client import KeitaroClient
from app.schemas import CampaignOut, CreateCampaignRequest
from app.services import campaigns as campaign_service
from app.services import streams as stream_service

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.get("", response_model=list[CampaignOut])
def list_campaigns(db: Session = Depends(get_db)) -> list[CampaignOut]:
    return campaign_service.list_campaigns(db)


@router.post("", response_model=CampaignOut)
def create_campaign(
    payload: CreateCampaignRequest,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(get_keitaro),
) -> CampaignOut:
    return campaign_service.create_campaign(db, client, payload)


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(get_keitaro),
) -> CampaignOut:
    return campaign_service.get_campaign(db, client, campaign_id)


@router.post("/{campaign_id}/fetch-streams", response_model=CampaignOut)
def fetch_streams(
    campaign_id: int,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(get_keitaro),
) -> CampaignOut:
    return stream_service.fetch_streams(db, client, campaign_id)
