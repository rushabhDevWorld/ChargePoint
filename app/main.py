from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app import service
from app.database import Base, engine, get_db
from app.schemas import HealthReportIn, MetricsOut, ReportHistoryOut, StationHealthOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    # fine for the exercise; a real deployment would use Alembic migrations
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Network Hygiene Service", version="0.1.0", lifespan=lifespan)


@app.post("/reports", response_model=StationHealthOut, status_code=201)
def submit_report(report: HealthReportIn, db: Session = Depends(get_db)):
    return service.ingest_report(db, report)


@app.get("/stations/poor", response_model=list[StationHealthOut])
def list_poor_stations(db: Session = Depends(get_db)):
    return service.get_poor_stations(db)


@app.get("/stations/{station_id}/health", response_model=StationHealthOut)
def station_health(station_id: str, db: Session = Depends(get_db)):
    station = service.get_station(db, station_id)
    if station is None:
        raise HTTPException(status_code=404, detail=f"No data for station {station_id}")
    return station


@app.get("/stations/{station_id}/history", response_model=list[ReportHistoryOut])
def station_history(
    station_id: str,
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    if service.get_station(db, station_id) is None:
        raise HTTPException(status_code=404, detail=f"No data for station {station_id}")
    return service.get_history(db, station_id, limit)


@app.get("/metrics", response_model=MetricsOut)
def metrics(db: Session = Depends(get_db)):
    return service.get_metrics(db)


@app.get("/health")
def health():
    return {"status": "ok"}


# --- simple dashboard (plain HTML/JS, no build step) ---
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC_DIR / "index.html")
