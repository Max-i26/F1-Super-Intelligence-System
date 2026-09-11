"""
src/intelligence/context.py — External Race Context & Race Replay Engine
========================================================================
Extracts race neutralization events (SC/VSC), chronological event timelines,
weather & thermal conditions, and lap-by-lap race replay snapshots.
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import RACE_ROUND, COMPOUND_COLORS
from src.utils.metrics import representative_pace, safe_float, safe_int
from src.data.local import filter_valid_laps
from src.utils.logging import get_logger

logger = get_logger(__name__)


def detect_race_neutralizations(race_df: pd.DataFrame) -> pd.DataFrame:
    """
    Detects Safety Car (SC), Virtual Safety Car (VSC), and Green flag phases
    by analyzing whole-grid lap time inflation across each lap of the race.
    Returns a DataFrame: LapNumber, MedianLapTime, LapStatus ('GREEN', 'SC', 'VSC', 'START')
    """
    if "LapNumber" not in race_df.columns or "LapTime" not in race_df.columns:
        return pd.DataFrame()

    valid = filter_valid_laps(race_df)
    if len(valid) == 0:
        return pd.DataFrame()

    rep_pace_baseline = representative_pace(valid["LapTime"]) or valid["LapTime"].median()

    lap_stats = (
        race_df.groupby("LapNumber")
        .agg(
            median_time=("LapTime", "median"),
            driver_count=("Driver", "count"),
            valid_count=("LapTime", lambda x: filter_valid_laps(pd.DataFrame({"LapTime": x}))["LapTime"].count()),
        )
        .reset_index()
        .sort_values("LapNumber")
    )

    statuses = []
    for _, row in lap_stats.iterrows():
        lap_no = int(row["LapNumber"])
        med = row["median_time"]

        if lap_no == 1:
            statuses.append("START 🚦")
        elif pd.isna(med) or med is None:
            statuses.append("GREEN 🟢")
        elif med > rep_pace_baseline * 1.35:
            statuses.append("SAFETY CAR 🟡")
        elif med > rep_pace_baseline * 1.18:
            statuses.append("VSC ⚠️")
        else:
            statuses.append("GREEN 🟢")

    lap_stats["status"] = statuses
    lap_stats["baseline_pace"] = round(float(rep_pace_baseline), 3)
    return lap_stats


def build_race_timeline_events(race_df: pd.DataFrame, race_name: str) -> List[Dict[str, Any]]:
    """
    Compiles an annotated chronological timeline of all key events in a Grand Prix:
    - Lights Out & Start
    - Safety Car / VSC deployments
    - Lead changes
    - Pit stops
    - Retirements / DNFs
    - Chequered Flag
    """
    events = []
    if "LapNumber" not in race_df.columns:
        return events

    max_lap = int(race_df["LapNumber"].max()) if race_df["LapNumber"].notna().any() else 0
    if max_lap == 0:
        return events

    # 1. Race Start
    events.append({
        "lap": 1,
        "type": "🚦 LIGHTS OUT",
        "headline": f"{race_name} Grand Prix — Race Start",
        "description": f"All 20 cars take the start for Round {RACE_ROUND.get(race_name, '?')}.",
        "severity": "info"
    })

    # 2. Safety Car / VSC detections
    neut_df = detect_race_neutralizations(race_df)
    if not neut_df.empty:
        prev_status = "GREEN 🟢"
        for _, row in neut_df.iterrows():
            curr_status = row["status"]
            lap_no = int(row["LapNumber"])
            if lap_no > 1 and curr_status != prev_status:
                if "SAFETY CAR" in curr_status:
                    events.append({
                        "lap": lap_no,
                        "type": "🟡 SAFETY CAR",
                        "headline": f"Safety Car Deployed (Lap {lap_no})",
                        "description": f"Field neutralized. Median lap times inflated to {row['median_time']:.1f}s.",
                        "severity": "warning"
                    })
                elif "VSC" in curr_status:
                    events.append({
                        "lap": lap_no,
                        "type": "⚠️ VSC",
                        "headline": f"Virtual Safety Car (Lap {lap_no})",
                        "description": "Virtual Safety Car delta enforced across all sectors.",
                        "severity": "warning"
                    })
            prev_status = curr_status

    # 3. Pit Stops
    if "Stint" in race_df.columns:
        for driver in race_df["Driver"].dropna().unique():
            d_df = race_df[race_df["Driver"] == driver].sort_values("LapNumber")
            stints = d_df.groupby("Stint")
            if len(stints) >= 2:
                for s_idx, (stint_num, s_laps) in enumerate(stints):
                    if s_idx > 0:
                        pit_lap = int(s_laps["LapNumber"].min())
                        new_compound = s_laps["Compound"].mode().iloc[0] if len(s_laps) > 0 else "TYRES"
                        events.append({
                            "lap": pit_lap,
                            "type": "🔧 PIT STOP",
                            "headline": f"{driver} Pit Stop (Lap {pit_lap})",
                            "description": f"{driver} switches to {new_compound} compound for Stint {int(stint_num)}.",
                            "severity": "info"
                        })

    # 4. Lead Changes
    if "Position" in race_df.columns:
        p1_laps = race_df[race_df["Position"] == 1].sort_values("LapNumber")
        prev_leader = None
        for _, row in p1_laps.iterrows():
            curr_leader = row["Driver"]
            lap_no = int(row["LapNumber"])
            if prev_leader is not None and curr_leader != prev_leader:
                events.append({
                    "lap": lap_no,
                    "type": "👑 LEAD CHANGE",
                    "headline": f"{curr_leader} Takes the Race Lead (Lap {lap_no})",
                    "description": f"Lead transferred from {prev_leader} to {curr_leader}.",
                    "severity": "success"
                })
            prev_leader = curr_leader

    # 5. Retirements / DNFs
    driver_max_laps = race_df.groupby("Driver")["LapNumber"].max().to_dict()
    for driver, laps in driver_max_laps.items():
        if max_lap > 0 and laps < 0.9 * max_lap:
            events.append({
                "lap": int(laps),
                "type": "💥 RETIREMENT",
                "headline": f"{driver} Retires from the Race (Lap {int(laps)})",
                "description": f"{driver} out of the Grand Prix after completing {int(laps)} laps.",
                "severity": "error"
            })

    # 6. Chequered Flag
    winner_row = race_df[(race_df["LapNumber"] == max_lap) & (race_df["Position"] == 1)]
    winner_name = winner_row["Driver"].iloc[0] if not winner_row.empty else "Winner"
    events.append({
        "lap": max_lap,
        "type": "🏁 CHEQUERED FLAG",
        "headline": f"{winner_name} Wins the {race_name} Grand Prix!",
        "description": f"Race distance of {max_lap} laps completed.",
        "severity": "success"
    })

    # Sort events chronologically by lap
    events.sort(key=lambda x: x["lap"])
    return events


def get_lap_snapshot(race_df: pd.DataFrame, lap_number: int) -> pd.DataFrame:
    """
    Returns the exact grid running order, tyre age, compound, and interval gaps
    for all drivers at a specific lap number during the Grand Prix.
    """
    if "LapNumber" not in race_df.columns:
        return pd.DataFrame()

    # Get data up to this lap for each driver
    past_laps = race_df[race_df["LapNumber"] <= lap_number].copy()
    if past_laps.empty:
        return pd.DataFrame()

    current_laps = race_df[race_df["LapNumber"] == lap_number].copy()
    if current_laps.empty:
        # Fallback to latest available lap on or before lap_number
        idx = past_laps.groupby("Driver")["LapNumber"].idxmax()
        current_laps = past_laps.loc[idx].copy()

    # Calculate tyre age (laps on current stint)
    records = []
    for _, row in current_laps.iterrows():
        driver = row["Driver"]
        d_past = past_laps[past_laps["Driver"] == driver].sort_values("LapNumber")
        cur_stint = row.get("Stint", 1)
        stint_start_lap = d_past[d_past["Stint"] == cur_stint]["LapNumber"].min()
        tyre_age = int(lap_number - stint_start_lap + 1) if pd.notna(stint_start_lap) else 1

        records.append({
            "Position": safe_int(row.get("Position")),
            "Driver": driver,
            "Team": row.get("Team", "Unknown"),
            "LastLapTime": safe_float(row.get("LapTime")),
            "Compound": row.get("Compound", "UNKNOWN"),
            "Stint": safe_int(cur_stint),
            "TyreAge": tyre_age,
            "TotalLaps": len(d_past),
        })

    snapshot_df = pd.DataFrame(records)
    if "Position" in snapshot_df.columns and snapshot_df["Position"].notna().any():
        snapshot_df = snapshot_df.sort_values("Position").reset_index(drop=True)

    return snapshot_df


def get_circuit_environmental_profile(race_name: str) -> Dict[str, Any]:
    """
    Provides estimated track environmental context (ambient, track temp, humidity, risk of rain)
    for each 2025 circuit based on geographic & historical seasonal patterns.
    """
    PROFILES = {
        "Bahrain": {"ambient_temp": "28°C", "track_temp": "34°C", "humidity": "45%", "rain_risk": "0%", "type": "Night / Desert"},
        "Saudi Arabia": {"ambient_temp": "30°C", "track_temp": "36°C", "humidity": "50%", "rain_risk": "0%", "type": "High Speed Street"},
        "Australia": {"ambient_temp": "22°C", "track_temp": "32°C", "humidity": "60%", "rain_risk": "15%", "type": "Semi-Permanent"},
        "Japan": {"ambient_temp": "17°C", "track_temp": "25°C", "humidity": "65%", "rain_risk": "35%", "type": "High Downforce"},
        "China": {"ambient_temp": "21°C", "track_temp": "29°C", "humidity": "55%", "rain_risk": "20%", "type": "Front Limited"},
        "Miami": {"ambient_temp": "29°C", "track_temp": "48°C", "humidity": "75%", "rain_risk": "25%", "type": "High Thermal"},
        "Imola": {"ambient_temp": "24°C", "track_temp": "38°C", "humidity": "50%", "rain_risk": "20%", "type": "Traditional European"},
        "Monaco": {"ambient_temp": "23°C", "track_temp": "42°C", "humidity": "65%", "rain_risk": "10%", "type": "Low Speed Street"},
        "Spain": {"ambient_temp": "28°C", "track_temp": "46°C", "humidity": "45%", "rain_risk": "5%", "type": "Aero Reference"},
        "Canada": {"ambient_temp": "20°C", "track_temp": "33°C", "humidity": "70%", "rain_risk": "40%", "type": "Stop & Go"},
        "Austria": {"ambient_temp": "25°C", "track_temp": "44°C", "humidity": "40%", "rain_risk": "30%", "type": "Short / Elevation"},
        "Silverstone": {"ambient_temp": "19°C", "track_temp": "28°C", "humidity": "72%", "rain_risk": "50%", "type": "High Speed Corners"},
        "Belgium": {"ambient_temp": "18°C", "track_temp": "24°C", "humidity": "80%", "rain_risk": "65%", "type": "Variable Microclimate"},
        "Hungary": {"ambient_temp": "32°C", "track_temp": "52°C", "humidity": "35%", "rain_risk": "10%", "type": "Maximum Downforce"},
        "Netherlands": {"ambient_temp": "20°C", "track_temp": "29°C", "humidity": "75%", "rain_risk": "45%", "type": "Banked Seaside"},
        "Italy": {"ambient_temp": "31°C", "track_temp": "49°C", "humidity": "40%", "rain_risk": "5%", "type": "Temple of Speed"},
        "Azerbaijan": {"ambient_temp": "26°C", "track_temp": "38°C", "humidity": "55%", "rain_risk": "5%", "type": "Long Straight Street"},
        "Singapore": {"ambient_temp": "30°C", "track_temp": "38°C", "humidity": "85%", "rain_risk": "30%", "type": "Extreme Night Street"},
        "USA": {"ambient_temp": "27°C", "track_temp": "41°C", "humidity": "45%", "rain_risk": "15%", "type": "Bumpy High Energy"},
        "Mexico": {"ambient_temp": "22°C", "track_temp": "45°C", "humidity": "30%", "rain_risk": "10%", "type": "High Altitude (2,200m)"},
        "Brazil": {"ambient_temp": "23°C", "track_temp": "37°C", "humidity": "78%", "rain_risk": "60%", "type": "Unpredictable / Rain"},
        "Las Vegas": {"ambient_temp": "12°C", "track_temp": "15°C", "humidity": "25%", "rain_risk": "0%", "type": "Cold Night Street"},
        "Qatar": {"ambient_temp": "26°C", "track_temp": "31°C", "humidity": "60%", "rain_risk": "0%", "type": "High Lateral G"},
        "Abu Dhabi": {"ambient_temp": "27°C", "track_temp": "33°C", "humidity": "55%", "rain_risk": "0%", "type": "Twilight Finale"},
    }
    return PROFILES.get(race_name, {
        "ambient_temp": "24°C", "track_temp": "35°C", "humidity": "50%", "rain_risk": "10%", "type": "Grand Prix Circuit"
    })
