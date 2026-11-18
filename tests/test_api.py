import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    # in-memory SQLite keeps the tests fast and dependency free
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def report(station_id="st-1", ts="2026-01-01T10:00:00Z", status="online",
           latency=80, errors=0, region="us-west"):
    return {
        "station_id": station_id,
        "timestamp": ts,
        "connectivity_status": status,
        "latency_ms": latency,
        "error_count": errors,
        "firmware_version": "1.2.0",
        "region": region,
    }


def test_submit_and_fetch_status(client):
    assert client.post("/reports", json=report()).status_code == 201

    res = client.get("/stations/st-1/health")
    assert res.status_code == 200
    assert res.json()["score"] == 100
    assert res.json()["is_poor"] is False


def test_unknown_station_is_404(client):
    assert client.get("/stations/nope/health").status_code == 404


def test_invalid_report_is_422(client):
    bad = report(latency=-5, status="sleeping")
    assert client.post("/reports", json=bad).status_code == 422


def test_poor_stations_listed_worst_first(client):
    client.post("/reports", json=report("good"))
    client.post("/reports", json=report("bad", status="offline", latency=900, errors=20))
    client.post("/reports", json=report("meh", status="offline", latency=300, errors=4))

    res = client.get("/stations/poor")
    assert [s["station_id"] for s in res.json()] == ["bad", "meh"]


def test_older_report_does_not_overwrite_newer(client):
    client.post("/reports", json=report("st-2", ts="2026-01-01T12:00:00Z"))
    client.post("/reports", json=report("st-2", ts="2026-01-01T09:00:00Z",
                                        status="offline", latency=900, errors=20))

    data = client.get("/stations/st-2/health").json()
    assert data["connectivity_status"] == "online"
    assert data["score"] == 100


def test_metrics_per_region(client):
    client.post("/reports", json=report("a", latency=100, region="us-west"))
    client.post("/reports", json=report("b", latency=300, region="us-west"))
    client.post("/reports", json=report("c", latency=50, region="eu-west"))

    data = client.get("/metrics").json()
    assert data["total_stations"] == 3
    regions = {r["region"]: r for r in data["regions"]}
    assert regions["us-west"]["avg_latency_ms"] == 200.0
    assert regions["eu-west"]["stations"] == 1


def test_history_returns_newest_first(client):
    client.post("/reports", json=report("st-3", ts="2026-01-01T10:00:00Z", latency=50))
    client.post("/reports", json=report("st-3", ts="2026-01-01T11:00:00Z", latency=70))

    res = client.get("/stations/st-3/history?limit=10")
    assert res.status_code == 200
    assert [r["latency_ms"] for r in res.json()] == [70, 50]


def test_history_unknown_station_is_404(client):
    assert client.get("/stations/nope/history").status_code == 404


def test_dashboard_is_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Network Hygiene Dashboard" in res.text
