"""Send some fake reports so the dashboard has something to show.

    python scripts/seed.py                      # service on localhost:8000
    python scripts/seed.py http://host:8000
"""
import random
import sys
from datetime import datetime, timedelta, timezone

import httpx

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
REGIONS = ["us-west", "us-east", "eu-west", "ap-south"]
STATIONS = 40
REPORTS_PER_STATION = 12

random.seed(7)
now = datetime.now(timezone.utc)
sent = 0

with httpx.Client(base_url=BASE_URL, timeout=10) as client:
    for n in range(1, STATIONS + 1):
        station_id = f"st-{n:03d}"
        region = REGIONS[n % len(REGIONS)]
        flaky = n % 5 == 0  # every 5th station has a bad network

        for i in range(REPORTS_PER_STATION):
            minutes_ago = (REPORTS_PER_STATION - i) * 10
            offline = flaky and random.random() < 0.6
            report = {
                "station_id": station_id,
                "timestamp": (now - timedelta(minutes=minutes_ago)).isoformat(),
                "connectivity_status": "offline" if offline else "online",
                "latency_ms": random.randint(400, 1200) if flaky else random.randint(30, 220),
                "error_count": random.randint(5, 20) if flaky else random.randint(0, 3),
                "firmware_version": "2.1.0" if n % 3 else "2.0.4",
                "region": region,
            }
            client.post("/reports", json=report).raise_for_status()
            sent += 1

print(f"sent {sent} reports for {STATIONS} stations")
