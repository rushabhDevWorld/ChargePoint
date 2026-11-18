# Network Hygiene Service

A small FastAPI microservice that ingests EV charging station health reports,
computes a **network hygiene score** (0-100), flags stations with poor scores, and
exposes REST APIs plus a simple dashboard.

**Stack:** Python 3.12, FastAPI, SQLAlchemy 2, PostgreSQL, pytest, plain HTML/JS for the UI.

| Document | What is in it |
|----------|---------------|
| [docs/DESIGN.md](docs/DESIGN.md) | Architecture, data model, scaling, AWS mapping, security, testing, CI/CD |
| [docs/AI_USAGE.md](docs/AI_USAGE.md) | Which AI tools I used, where they helped, where they didn't |

---

## Quick start (Docker)

You need Docker Desktop (or Docker Engine with the Compose plugin).

```bash
docker compose up --build
```

Then, in a second terminal, load some demo data:

```bash
docker compose exec api python scripts/seed.py
```

| What | URL |
|------|-----|
| Dashboard | http://localhost:8000/ |
| Swagger UI | http://localhost:8000/docs |
| OpenAPI spec | http://localhost:8000/openapi.json |

Stop with `Ctrl+C`, then `docker compose down` (add `-v` to also wipe the database).

## Run without Docker for the app

You still need a PostgreSQL. The compose file can start just that.

```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements.txt

docker compose up -d db                # PostgreSQL only
uvicorn app.main:app --reload
python scripts/seed.py                 # optional demo data
```

`DATABASE_URL` and `HYGIENE_THRESHOLD` can be set as environment variables
(defaults are in `app/config.py`).

## Run the tests

```bash
pytest
```

Tests use in-memory SQLite, so no database or Docker is needed.

---

## API

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/reports` | Submit a health report |
| GET | `/stations/{id}/health` | Latest status of one station |
| GET | `/stations/{id}/history?limit=20` | Recent reports for one station (newest first) |
| GET | `/stations/poor` | Stations below the score threshold, worst first |
| GET | `/metrics` | Totals, average latency/score overall and per region |
| GET | `/health` | Liveness check |

Example:

```bash
curl -X POST localhost:8000/reports -H 'Content-Type: application/json' -d '{
  "station_id": "st-001",
  "timestamp": "2026-01-01T10:00:00Z",
  "connectivity_status": "offline",
  "latency_ms": 900,
  "error_count": 12,
  "firmware_version": "2.1.0",
  "region": "us-west"
}'

curl localhost:8000/stations/st-001/health
curl localhost:8000/stations/poor
curl localhost:8000/metrics
```

## Hygiene score

Starts at 100 and loses points for:

| Condition | Penalty |
|-----------|---------|
| Offline | -50 |
| Latency above 200 ms | -1 per extra 40 ms (max -25) |
| Errors | -2 each (max -25) |

A station is **poor** when its score is below **60** (`HYGIENE_THRESHOLD`).
See `app/scoring.py`.

## Dashboard

Open http://localhost:8000/. It shows fleet totals, average latency per region, the
list of poor stations (click one for details and a score trend), and a station lookup.
It is one HTML file (`app/static/index.html`) with no build step, and refreshes every
10 seconds.

## Project layout

```
app/
  main.py        routes + dashboard mount
  service.py     business logic (ingest, queries, metrics)
  scoring.py     score formula (pure function)
  models.py      SQLAlchemy tables
  schemas.py     request/response models
  config.py      env settings
  database.py    engine and session
  static/        dashboard (index.html)
scripts/seed.py  demo data generator
tests/           unit + API tests
docs/            design doc, AI usage
```

## Assumptions

- Added an optional `region` field to the report, because per-region metrics need it.
- Reports can arrive late or out of order. All are stored, but only the newest one
  (by report timestamp) updates a station's current status.
- Tables are created on startup. A real deployment would use Alembic migrations.
- No authentication yet. See the security section of the design doc.
