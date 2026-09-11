"""
scripts/build_championship.py — Build Championship Snapshots & Standings
========================================================================
Builds and saves official 2025 driver and constructor championship standings
and estimated race-by-race snapshots to data/2025/intelligence/.
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    CHAMPIONSHIP_SNAPSHOTS_CSV,
    INTELLIGENCE_DIR,
)
from src.data.local import load_season_laps
from src.intelligence.championship import (
    get_official_driver_standings,
    get_official_constructor_standings,
    validate_standings,
    build_championship_progression,
    save_championship_snapshots,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


def main():
    print("=" * 60)
    print("F1 SUPER INTELLIGENCE — Building Championship Layer (Phase 2)")
    print("=" * 60)

    INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Driver Standings (Ground Truth)
    print("\n[1] Fetching Official Driver Standings...")
    driver_standings = get_official_driver_standings(use_api=True)
    val_report = validate_standings(driver_standings)
    if val_report["passed"]:
        print("    [PASS] Driver standings validated (Norris P1, Verstappen P2, Piastri P3)")
    else:
        print(f"    [FAIL] Validation issues: {val_report['issues']}")

    driver_standings_path = INTELLIGENCE_DIR / "official_driver_standings.csv"
    driver_standings.to_csv(driver_standings_path, index=False)
    print(f"    Saved: {driver_standings_path} ({len(driver_standings)} drivers)")

    # 2. Constructor Standings (Ground Truth)
    print("\n[2] Fetching Official Constructor Standings...")
    constructor_standings = get_official_constructor_standings(use_api=True)
    constructor_standings_path = INTELLIGENCE_DIR / "official_constructor_standings.csv"
    constructor_standings.to_csv(constructor_standings_path, index=False)
    print(f"    Saved: {constructor_standings_path} ({len(constructor_standings)} constructors)")

    # 3. Race-by-Race Progression Snapshots
    print("\n[3] Building Race-by-Race Championship Snapshots...")
    try:
        df, _ = load_season_laps()
        progression = build_championship_progression(df)
        save_championship_snapshots(progression)
        print(f"    Saved: {CHAMPIONSHIP_SNAPSHOTS_CSV} ({len(progression)} snapshots)")
    except Exception as e:
        print(f"    [ERROR] Could not build snapshots from lap data: {e}")

    print("\n" + "=" * 60)
    print("Phase 2 Championship Truth Layer Complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
