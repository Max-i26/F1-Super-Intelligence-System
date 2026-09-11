"""
src/intelligence/strategy.py — Strategy Intelligence
=====================================================
Analyzes pit stop strategies, compound sequences, undercut/overcut
battles, and strategic efficiency across the 2025 championship.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import RACE_ROUND
from src.utils.metrics import representative_pace, safe_float, safe_int, position_gain
from src.data.local import filter_valid_laps
from src.utils.logging import get_logger

logger = get_logger(__name__)


def build_strategy_summary(driver_race_df: pd.DataFrame, driver: str, race: str) -> Dict[str, Any]:
    """
    Build a complete strategy summary for a driver in one race.
    """
    s: Dict[str, Any] = {
        "driver": driver,
        "race": race,
        "race_round": RACE_ROUND.get(race),
    }

    if "Stint" not in driver_race_df.columns:
        return s

    # Compound sequence
    stint_compounds = (
        driver_race_df.sort_values("LapNumber")
        .groupby("Stint")["Compound"]
        .agg(lambda x: x.mode().iloc[0] if len(x) > 0 else "UNKNOWN")
    )
    s["compound_sequence"] = stint_compounds.tolist()
    s["stop_count"] = len(stint_compounds) - 1
    s["stint_count"] = len(stint_compounds)
    s["strategy_type"] = _classify_strategy(len(stint_compounds))

    # Stint lengths
    stint_lengths = (
        driver_race_df.groupby("Stint")["LapNumber"]
        .agg(lambda x: int(x.max() - x.min() + 1))
    )
    s["stint_lengths"] = stint_lengths.tolist()

    # Pit lap numbers (lap where new stint starts)
    pit_laps = []
    sorted_stints = driver_race_df.sort_values("LapNumber").groupby("Stint")["LapNumber"]
    lap_ranges = [(int(g.min()), int(g.max())) for _, g in sorted_stints]
    for i in range(1, len(lap_ranges)):
        pit_laps.append(lap_ranges[i][0])
    s["pit_laps"] = pit_laps

    # Strategy efficiency: pace achieved per stint
    valid = filter_valid_laps(driver_race_df)
    stint_paces = {}
    for stint_num in driver_race_df["Stint"].dropna().unique():
        s_valid = valid[valid["Stint"] == stint_num]["LapTime"]
        pace = representative_pace(s_valid)
        if pace:
            stint_paces[int(stint_num)] = pace
    s["stint_paces"] = stint_paces

    # Position change
    if "Position" in driver_race_df.columns:
        sorted_laps = driver_race_df.sort_values("LapNumber")
        first_pos = sorted_laps["Position"].dropna().iloc[0] if sorted_laps["Position"].notna().any() else None
        last_pos = sorted_laps["Position"].dropna().iloc[-1] if sorted_laps["Position"].notna().any() else None
        s["starting_position"] = safe_int(first_pos)
        s["finishing_position"] = safe_int(last_pos)
        s["position_gain"] = position_gain(first_pos, last_pos)

    return s


def _classify_strategy(stint_count: int) -> str:
    """Classify a strategy by number of stints."""
    mapping = {1: "Zero-stop", 2: "One-stop", 3: "Two-stop", 4: "Three-stop"}
    return mapping.get(stint_count, f"{stint_count - 1}-stop")


def compute_undercut_overcut_battles(race_df: pd.DataFrame) -> pd.DataFrame:
    """
    Detects tactical undercut and overcut battles in a Grand Prix.
    Identifies drivers who pitted within 1–3 laps of each other while in close track proximity.
    """
    if "Stint" not in race_df.columns or "Position" not in race_df.columns:
        return pd.DataFrame()

    # Find pit stop lap and in-lap position for each driver
    driver_stops = []
    for driver in race_df["Driver"].dropna().unique():
        d_df = race_df[race_df["Driver"] == driver].sort_values("LapNumber")
        stints = d_df.groupby("Stint")
        if len(stints) >= 2:
            stint_keys = sorted(stints.groups.keys())
            # For each pit stop
            for i in range(len(stint_keys) - 1):
                cur_stint = d_df[d_df["Stint"] == stint_keys[i]]
                next_stint = d_df[d_df["Stint"] == stint_keys[i+1]]
                pit_lap = int(next_stint["LapNumber"].min())
                pos_before = cur_stint["Position"].dropna().iloc[-1] if cur_stint["Position"].notna().any() else np.nan
                # Position 3 laps after stop
                after_stop = next_stint[next_stint["LapNumber"] >= pit_lap + 2]
                pos_after = after_stop["Position"].dropna().iloc[0] if not after_stop.empty and after_stop["Position"].notna().any() else np.nan

                driver_stops.append({
                    "driver": driver,
                    "stop_num": i + 1,
                    "pit_lap": pit_lap,
                    "pos_before": safe_int(pos_before),
                    "pos_after": safe_int(pos_after),
                })

    if not driver_stops:
        return pd.DataFrame()

    df_stops = pd.DataFrame(driver_stops)
    battles = []

    # Compare pairs of drivers who pitted on similar stop_num within 3 laps of each other
    for s_num in df_stops["stop_num"].unique():
        s_df = df_stops[df_stops["stop_num"] == s_num].sort_values("pit_lap")
        stops_list = s_df.to_dict("records")
        for i in range(len(stops_list)):
            for j in range(i + 1, len(stops_list)):
                d1 = stops_list[i]
                d2 = stops_list[j]
                lap_diff = d2["pit_lap"] - d1["pit_lap"]
                # Pitted 1 to 3 laps apart
                if 1 <= lap_diff <= 3:
                    # Check if they were close in position (within 3 spots before stop)
                    p1_before = d1["pos_before"]
                    p2_before = d2["pos_before"]
                    if p1_before and p2_before and abs(p1_before - p2_before) <= 3:
                        p1_after = d1["pos_after"]
                        p2_after = d2["pos_after"]
                        
                        # Did early stopper (d1) jump the late stopper (d2)?
                        undercut_success = False
                        if p1_before > p2_before and p1_after and p2_after and p1_after < p2_after:
                            undercut_success = True

                        battles.append({
                            "attacker": d1["driver"],
                            "defender": d2["driver"],
                            "attacker_pit_lap": d1["pit_lap"],
                            "defender_pit_lap": d2["pit_lap"],
                            "gap_laps": lap_diff,
                            "attacker_pos_before": p1_before,
                            "defender_pos_before": p2_before,
                            "attacker_pos_after": p1_after,
                            "defender_pos_after": p2_after,
                            "tactic": "Undercut",
                            "successful": bool(undercut_success),
                            "outcome": "PASSED ⚡" if undercut_success else ("HELD 🛡️" if (p2_after and p1_after and p2_after <= p1_after) else "TIE"),
                        })

    return pd.DataFrame(battles)


def build_race_strategies(df: pd.DataFrame, race: str) -> pd.DataFrame:
    """
    Build strategy summaries for all drivers in a race.
    """
    race_df = df[df["Race"] == race]
    records = []
    for driver in race_df["Driver"].dropna().unique():
        driver_df = race_df[race_df["Driver"] == driver]
        summary = build_strategy_summary(driver_df, driver, race)
        records.append(summary)
    return pd.DataFrame(records)


def build_all_strategies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build strategy summaries for all races and drivers.
    """
    records = []
    races = df["Race"].dropna().unique()
    logger.info(f"Building strategy intelligence for {len(races)} races...")
    for race in races:
        race_df = df[df["Race"] == race]
        for driver in race_df["Driver"].dropna().unique():
            driver_df = race_df[race_df["Driver"] == driver]
            summary = build_strategy_summary(driver_df, driver, race)
            records.append(summary)
    result = pd.DataFrame(records)
    logger.info(f"Strategy intelligence built: {len(result)} records.")
    return result


def simulate_undercut_window(
    gap_seconds: float,
    fresh_tyre_delta_per_lap: float = 1.2,
    laps_ahead: int = 2,
) -> Dict[str, Any]:
    """
    Simulates the mathematical feasibility of an undercut attempt given current interval gap,
    expected fresh tyre performance advantage per lap, and laps before defender stops.
    """
    total_gain = fresh_tyre_delta_per_lap * laps_ahead
    undercut_margin = total_gain - gap_seconds
    is_feasible = undercut_margin > 0.0

    return {
        "gap_seconds": round(float(gap_seconds), 2),
        "laps_ahead": int(laps_ahead),
        "total_fresh_tyre_gain": round(float(total_gain), 2),
        "undercut_margin_seconds": round(float(undercut_margin), 2),
        "feasible": bool(is_feasible),
        "confidence": "HIGH" if undercut_margin > 0.5 else ("MARGINAL" if is_feasible else "UNLIKELY"),
        "recommendation": "BOX NOW FOR UNDERCUT ⚡" if is_feasible else "STAY OUT / OVERCUT CANDIDATE 🛡️"
    }

