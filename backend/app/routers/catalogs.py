from fastapi import APIRouter, Depends, Query

from app.deps import get_keitaro
from app.keitaro.client import KeitaroClient
from app.schemas import CatalogItem, CreateCatalogItem

router = APIRouter(prefix="/api/catalogs", tags=["catalogs"])


def _items(rows: list[dict], query: str | None = None) -> list[CatalogItem]:
    items: list[CatalogItem] = []
    needle = (query or "").strip().lower()
    for row in rows:
        if row.get("id") is None:
            continue
        name = str(row.get("name") or f"#{row['id']}")
        item = CatalogItem(id=int(row["id"]), name=name)
        if needle and needle not in name.lower() and needle not in str(item.id):
            continue
        items.append(item)
    return items


def _item(row: dict) -> CatalogItem:
    return CatalogItem(id=int(row["id"]), name=str(row.get("name") or f"#{row['id']}"))


@router.get("/domains", response_model=list[CatalogItem])
def list_domains(client: KeitaroClient = Depends(get_keitaro)) -> list[CatalogItem]:
    return _items(client.list_domains())


@router.get("/groups", response_model=list[CatalogItem])
def list_groups(client: KeitaroClient = Depends(get_keitaro)) -> list[CatalogItem]:
    return _items(client.list_groups("campaigns"))


@router.get("/traffic-sources", response_model=list[CatalogItem])
def list_traffic_sources(client: KeitaroClient = Depends(get_keitaro)) -> list[CatalogItem]:
    return _items(client.list_traffic_sources())


@router.post("/domains", response_model=CatalogItem)
def create_domain(
    payload: CreateCatalogItem,
    client: KeitaroClient = Depends(get_keitaro),
) -> CatalogItem:
    return _item(client.create_domain(payload.name))


@router.post("/groups", response_model=CatalogItem)
def create_group(
    payload: CreateCatalogItem,
    client: KeitaroClient = Depends(get_keitaro),
) -> CatalogItem:
    return _item(client.create_group(payload.name))


@router.post("/traffic-sources", response_model=CatalogItem)
def create_traffic_source(
    payload: CreateCatalogItem,
    client: KeitaroClient = Depends(get_keitaro),
) -> CatalogItem:
    return _item(client.create_traffic_source(payload.name))


@router.get("/offers", response_model=list[CatalogItem])
def list_offers(
    q: str | None = Query(default=None),
    client: KeitaroClient = Depends(get_keitaro),
) -> list[CatalogItem]:
    return _items(client.list_offers(), q)
