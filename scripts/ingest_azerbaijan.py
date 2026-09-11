"""
scripts/ingest_azerbaijan.py — Ingest 2025 Azerbaijan Grand Prix Data
====================================================================
Pulls official 2025 Azerbaijan Grand Prix (Baku) timing and lap data
from OpenF1 (session_key 9904), converts it to the standard 9-column
format, merges it into season_laps.csv, and recomputes all intelligence
layers to complete the full 24-round 2025 season.
"""

import sys
import shutil
from pathlib import Path
import requests
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import SEASON_LAPS_CSV, RACES_2025
from src.utils.logging import get_logger

logger = get_logger(__name__)

BAKU_SESSION_KEY = 9904
OPENF1_BASE_URL = "https://api.openf1.org/v1"


def fetch_baku_data() -> pd.DataFrame:
    """Fetch and format 2025 Baku GP laps from OpenF1."""
    logger.info(f"Fetching OpenF1 data for Baku 2025 (session {BAKU_SESSION_KEY})...")
    
    laps_url = f"{OPENF1_BASE_URL}/laps?session_key={BAKU_SESSION_KEY}"
    drivers_url = f"{OPENF1_BASE_URL}/drivers?session_key={BAKU_SESSION_KEY}"
    stints_url = f"{OPENF1_BASE_URL}/stints?session_key={BAKU_SESSION_KEY}"
    pos_url = f"{OPENF1_BASE_URL}/position?session_key={BAKU_SESSION_KEY}"

    laps_resp = requests.get(laps_url, timeout=30)
    drivers_resp = requests.get(drivers_url, timeout=30)
    stints_resp = requests.get(stints_url, timeout=30)
    pos_resp = requests.get(pos_url, timeout=30)

    if laps_resp.status_code != 200 or not laps_resp.json():
        raise RuntimeError(f"Failed to fetch Baku laps: status {laps_resp.status_code}")

    df_laps = pd.DataFrame(laps_resp.json())
    df_drivers = pd.DataFrame(drivers_resp.json()) if drivers_resp.status_code == 200 else pd.DataFrame()
    df_stints = pd.DataFrame(stints_resp.json()) if stints_resp.status_code == 200 else pd.DataFrame()
    df_pos = pd.DataFrame(pos_resp.json()) if pos_resp.status_code == 200 else pd.DataFrame()

    df_laps["date_start_dt"] = pd.to_datetime(df_laps["date_start"], format="ISO8601")
    if not df_pos.empty and "date" in df_pos.columns:
        df_pos["date_dt"] = pd.to_datetime(df_pos["date"], format="ISO8601")

    # Driver mapping
    driver_meta = {}
    if not df_drivers.empty:
        for _, d in df_drivers.iterrows():
            num = d["driver_number"]
            driver_meta[num] = {
                "Driver": d.get("name_acronym") or d.get("broadcast_name", "")[:3],
                "Team": d.get("team_name") or "Unknown"
            }

    records = []
    for _, lap in df_laps.iterrows():
        num = lap["driver_number"]
        lap_no = lap["lap_number"]
        lap_time = lap.get("lap_duration")
        lap_start = lap["date_start_dt"]

        # Position
        pos_val = np.nan
        if not df_pos.empty:
            driver_pos = df_pos[df_pos["driver_number"] == num]
            if not driver_pos.empty:
                diffs = (driver_pos["date_dt"] - lap_start).abs()
                pos_val = float(driver_pos.loc[diffs.idxmin()]["position"])

        meta = driver_meta.get(num, {"Driver": str(num), "Team": "Unknown"})

        # Stint & compound
        compound = "UNKNOWN"
        stint_no = 1
        if not df_stints.empty:
            matching_stints = df_stints[
                (df_stints["driver_number"] == num) &
                (df_stints["lap_start"] <= lap_no) &
                (df_stints["lap_end"] >= lap_no)
            ]
            if not matching_stints.empty:
                compound = matching_stints.iloc[0].get("compound", "UNKNOWN")
                stint_no = matching_stints.iloc[0].get("stint_number", 1)
            else:
                matching_driver_stints = df_stints[df_stints["driver_number"] == num].sort_values("lap_start")
                if not matching_driver_stints.empty:
                    compound = matching_driver_stints.iloc[-1].get("compound", "UNKNOWN")
                    stint_no = matching_driver_stints.iloc[-1].get("stint_number", 1)

        records.append({
            "Driver": meta["Driver"],
            "Team": meta["Team"],
            "LapNumber": float(lap_no),
            "LapTime": float(lap_time) if pd.notna(lap_time) else np.nan,
            "Compound": str(compound).upper(),
            "Stint": float(stint_no),
            "Position": pos_val,
            "Race": "Azerbaijan",
            "Year": 2025
        })

    baku_df = pd.DataFrame(records)
    logger.info(f"Successfully processed {len(baku_df)} Baku laps for {baku_df['Driver'].nunique()} drivers.")
    return baku_df


def merge_and_update_dataset():
    """Download Baku data, merge with existing season_laps, and update CSV."""
    print("=" * 60)
    print("F1 SUPER INTELLIGENCE — Ingesting Azerbaijan (Baku) 2025")
    print("=" * 60)

    # 1. Load existing
    if not SEASON_LAPS_CSV.exists():
        print(f"Error: {SEASON_LAPS_CSV} not found.")
        return False

    existing_df = pd.read_csv(SEASON_LAPS_CSV)
    print(f"\n[1] Existing dataset: {len(existing_df):,} rows, {existing_df['Race'].nunique()} races.")

    if "Azerbaijan" in existing_df["Race"].values:
        print("    Notice: Azerbaijan already present in dataset. Replacing with fresh data...")
        existing_df = existing_df[existing_df["Race"] != "Azerbaijan"]

    # 2. Backup existing
    backup_path = SEASON_LAPS_CSV.with_name("season_laps_backup_23races.csv")
    if not backup_path.exists():
        shutil.copyfile(SEASON_LAPS_CSV, backup_path)
        print(f"    Backup created: {backup_path}")

    # 3. Fetch Baku data from OpenF1
    print("\n[2] Fetching Baku 2025 data from OpenF1...")
    try:
        baku_df = fetch_baku_data()
        print(f"    Fetched {len(baku_df)} laps across {baku_df['Driver'].nunique()} drivers.")
    except Exception as e:
        print(f"    Error fetching Baku data: {e}")
        return False

    # 4. Merge
    print("\n[3] Merging into complete 24-round season dataset...")
    full_df = pd.concat([existing_df, baku_df], ignore_index=True)
    full_df.to_csv(SEASON_LAPS_CSV, index=False)
    print(f"    Saved updated dataset to {SEASON_LAPS_CSV} ({len(full_df):,} rows, {full_df['Race'].nunique()} races).")

    # 5. Recompute all intelligence layers
    print("\n[4] Rebuilding all intelligence layers across all 24 rounds...")
    from src.intelligence.engine import run_full_pipeline
    from src.data.local import load_season_laps
    
    # Force reload cached data
    load_season_laps(force_reload=True)
    results = run_full_pipeline(force_reload=True)

    # Rebuild championship snapshots
    from src.intelligence.championship import build_championship_progression, save_championship_snapshots
    df_laps, _ = load_season_laps(force_reload=True)
    prog = build_championship_progression(df_laps)
    save_championship_snapshots(prog)

    print("\n" + "=" * 60)
    print(f"✅ Season complete: 24 / 24 Rounds updated successfully!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    merge_and_update_dataset()
