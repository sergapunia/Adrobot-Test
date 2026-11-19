from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db import Base, engine
from app.keitaro.client import KeitaroError
from app.routers import campaigns, catalogs, streams

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Keitaro", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(catalogs.router)
app.include_router(campaigns.router)
app.include_router(streams.router)


@app.exception_handler(KeitaroError)
async def keitaro_error_handler(_request: Request, exc: KeitaroError) -> JSONResponse:
    return JSONResponse(status_code=min(exc.status_code, 599) if exc.status_code >= 400 else 502, content={"detail": exc.message})


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
