from datetime import datetime

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class HealthReport(Base):
    """Raw history: every report we receive is stored here."""

    __tablename__ = "health_reports"
    __table_args__ = (Index("ix_reports_station_time", "station_id", "reported_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[str] = mapped_column(String(64))
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    connectivity_status: Mapped[str] = mapped_column(String(10))
    latency_ms: Mapped[int]
    error_count: Mapped[int]
    firmware_version: Mapped[str] = mapped_column(String(32))
    region: Mapped[str | None] = mapped_column(String(32))
    score: Mapped[int]


class StationStatus(Base):
    """One row per station with its latest state.

    Kept apart from the history table so that "latest status" and
    "poor stations" don't have to scan every report ever received.
    """

    __tablename__ = "station_status"

    station_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    last_reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    connectivity_status: Mapped[str] = mapped_column(String(10))
    latency_ms: Mapped[int]
    error_count: Mapped[int]
    firmware_version: Mapped[str] = mapped_column(String(32))
    region: Mapped[str | None] = mapped_column(String(32), index=True)
    score: Mapped[int]
    is_poor: Mapped[bool] = mapped_column(index=True)
