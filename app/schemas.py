from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthReportIn(BaseModel):
    station_id: str = Field(min_length=1, max_length=64)
    timestamp: datetime
    connectivity_status: Literal["online", "offline"]
    latency_ms: int = Field(ge=0)
    error_count: int = Field(ge=0)
    firmware_version: str
    # not in the original spec; added so we can aggregate per region
    region: str | None = None


class StationHealthOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    station_id: str
    last_reported_at: datetime
    connectivity_status: str
    latency_ms: int
    error_count: int
    firmware_version: str
    region: str | None
    score: int
    is_poor: bool


class RegionMetrics(BaseModel):
    region: str
    stations: int
    avg_latency_ms: float


class MetricsOut(BaseModel):
    total_stations: int
    poor_stations: int
    avg_latency_ms: float
    avg_score: float
    regions: list[RegionMetrics]


class ReportHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reported_at: datetime
    connectivity_status: str
    latency_ms: int
    error_count: int
    firmware_version: str
    region: str | None
    score: int
