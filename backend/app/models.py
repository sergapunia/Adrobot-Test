from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    keitaro_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    alias: Mapped[str] = mapped_column(String(255))
    domain_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    group_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    traffic_source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    campaign_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    streams: Mapped[list[Stream]] = relationship(back_populates="campaign", cascade="all, delete-orphan")


class Stream(Base):
    __tablename__ = "streams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keitaro_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.keitaro_id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    is_dirty: Mapped[bool] = mapped_column(Boolean, default=False)
    published_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    campaign: Mapped[Campaign] = relationship(back_populates="streams")
    offers: Mapped[list[StreamOffer]] = relationship(
        back_populates="stream",
        cascade="all, delete-orphan",
        order_by="StreamOffer.id",
    )


class StreamOffer(Base):
    __tablename__ = "stream_offers"
    __table_args__ = (UniqueConstraint("stream_id", "keitaro_offer_id", name="uq_stream_offer"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stream_id: Mapped[int] = mapped_column(ForeignKey("streams.id"), index=True)
    keitaro_offer_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(255))
    share: Mapped[int] = mapped_column(Integer, default=0)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default="active")

    stream: Mapped[Stream] = relationship(back_populates="offers")
