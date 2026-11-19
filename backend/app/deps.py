from fastapi import HTTPException

from app.keitaro.client import KeitaroClient, KeitaroError


def get_keitaro() -> KeitaroClient:
    try:
        return KeitaroClient()
    except KeitaroError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
