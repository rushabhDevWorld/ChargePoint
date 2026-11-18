from datetime import timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import config
from app.models import HealthReport, StationStatus
from app.schemas import HealthReportIn, MetricsOut, RegionMetrics
from app.scoring import calculate_score


def _as_utc(dt):
    # SQLite hands back naive datetimes, Postgres doesn't. Treat naive as UTC.
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def ingest_report(db: Session, data: HealthReportIn) -> StationStatus:
    score = calculate_score(data.connectivity_status, data.latency_ms, data.error_count)

    db.add(
        HealthReport(
            station_id=data.station_id,
            reported_at=data.timestamp,
            connectivity_status=data.connectivity_status,
            latency_ms=data.latency_ms,
            error_count=data.error_count,
            firmware_version=data.firmware_version,
            region=data.region,
            score=score,
        )
    )

    status = db.get(StationStatus, data.station_id)
    if status is None:
        status = StationStatus(station_id=data.station_id)
        db.add(status)

    # reports can arrive late or out of order; an old one must not overwrite a newer one
    is_newer = status.last_reported_at is None or _as_utc(data.timestamp) >= _as_utc(
        status.last_reported_at
    )
    if is_newer:
        status.last_reported_at = data.timestamp
        status.connectivity_status = data.connectivity_status
        status.latency_ms = data.latency_ms
        status.error_count = data.error_count
        status.firmware_version = data.firmware_version
        status.region = data.region
        status.score = score
        status.is_poor = score < config.POOR_SCORE_THRESHOLD

    db.commit()
    db.refresh(status)
    return status


def get_station(db: Session, station_id: str) -> StationStatus | None:
    return db.get(StationStatus, station_id)


def get_poor_stations(db: Session) -> list[StationStatus]:
    query = (
        select(StationStatus)
        .where(StationStatus.is_poor.is_(True))
        .order_by(StationStatus.score)
    )
    return list(db.scalars(query))


def get_metrics(db: Session) -> MetricsOut:
    total, poor, avg_latency, avg_score = db.execute(
        select(
            func.count(),
            func.count().filter(StationStatus.is_poor.is_(True)),
            func.coalesce(func.avg(StationStatus.latency_ms), 0),
            func.coalesce(func.avg(StationStatus.score), 0),
        )
    ).one()

    region_rows = db.execute(
        select(
            StationStatus.region,
            func.count(),
            func.avg(StationStatus.latency_ms),
        )
        .where(StationStatus.region.is_not(None))
        .group_by(StationStatus.region)
        .order_by(StationStatus.region)
    ).all()

    return MetricsOut(
        total_stations=total,
        poor_stations=poor,
        avg_latency_ms=float(avg_latency),
        avg_score=float(avg_score),
        regions=[
            RegionMetrics(region=r, stations=n, avg_latency_ms=float(lat))
            for r, n, lat in region_rows
        ],
    )


def get_history(db: Session, station_id: str, limit: int = 20) -> list[HealthReport]:
    query = (
        select(HealthReport)
        .where(HealthReport.station_id == station_id)
        .order_by(HealthReport.reported_at.desc())
        .limit(limit)
    )
    return list(db.scalars(query))
