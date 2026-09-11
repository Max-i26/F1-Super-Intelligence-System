"""
scripts/ingest_openf1.py — OpenF1 Ingestion Helper
===================================================
Tests OpenF1 connectivity and fetches available 2025 session metadata
and championship data.
"""

import sys
import json
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import EXTERNAL_DIR, SEASON_YEAR
from src.data.openf1 import get_client
from src.utils.logging import get_logger

logger = get_logger(__name__)


def main():
    print("=" * 60)
    print("F1 SUPER INTELLIGENCE — OpenF1 Ingestion Test")
    print("=" * 60)

    client = get_client()
    EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[1] Checking OpenF1 Connectivity...")
    available = client.is_available()
    if available:
        print("    [ONLINE] OpenF1 API is reachable.")
    else:
        print("    [OFFLINE] OpenF1 API is unreachable or returned non-200. Operating in offline fallback mode.")

    if available:
        print(f"\n[2] Ingesting {SEASON_YEAR} Sessions...")
        sessions = client.get_sessions(year=SEASON_YEAR)
        if sessions:
            sessions_file = EXTERNAL_DIR / f"sessions_{SEASON_YEAR}.json"
            with open(sessions_file, "w", encoding="utf-8") as f:
                json.dump(sessions, f, indent=2)
            print(f"    Saved {len(sessions)} session records to {sessions_file}")

        print(f"\n[3] Ingesting {SEASON_YEAR} Driver Championship...")
        drivers = client.get_championship_drivers(year=SEASON_YEAR)
        if drivers:
            drivers_file = EXTERNAL_DIR / f"championship_drivers_{SEASON_YEAR}.json"
            with open(drivers_file, "w", encoding="utf-8") as f:
                json.dump(drivers, f, indent=2)
            print(f"    Saved {len(drivers)} driver championship records to {drivers_file}")

        print(f"\n[4] Ingesting {SEASON_YEAR} Constructor Championship...")
        teams = client.get_championship_teams(year=SEASON_YEAR)
        if teams:
            teams_file = EXTERNAL_DIR / f"championship_teams_{SEASON_YEAR}.json"
            with open(teams_file, "w", encoding="utf-8") as f:
                json.dump(teams, f, indent=2)
            print(f"    Saved {len(teams)} team championship records to {teams_file}")

    print("\n" + "=" * 60)
    print("Ingestion script finished.")
    print("=" * 60)


if __name__ == "__main__":
    main()
