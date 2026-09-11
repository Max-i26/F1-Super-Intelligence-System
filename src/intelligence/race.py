"""
src/intelligence/race.py — Race Intelligence for F1 Super Intelligence
=======================================================================
Computes per-race and per-driver-per-race metrics.
All computations are NaN-safe and use robust statistics.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import RACE_ROUND, COMPOUND_COLORS, POINTS_FOR_POSITION
from src.utils.metrics import (
    representative_pace,
    trimmed_mean,
    consistency_score,
    degradation_slope,
    position_gain,
    safe_int,
    safe_float,
)
from src.data.local import filter_valid_laps
from src.utils.logging import get_logger

logger = get_logger(__name__)


def compute_race_summary(race_df: pd.DataFrame, race_name: str) -> Dict[str, Any]:
    """
    Compute race-level summary metrics.
    Input: all laps for ONE race.
    """
    valid = filter_valid_laps(race_df)
    summary = {
        "race": race_name,
        "race_round": RACE_ROUND.get(race_name),
        "total_laps_in_dataset": len(race_df),
        "valid_laps": len(valid),
        "drivers": sorted(race_df["Driver"].dropna().unique().tolist()),
        "num_drivers": race_df["Driver"].nunique(),
        "teams": sorted(race_df["Team"].dropna().unique().tolist()),
        "num_teams": race_df["Team"].nunique(),
        "compounds_used": sorted(race_df["Compound"].dropna().unique().tolist()),
    }

    # Fastest lap overall
    if len(valid) > 0:
        fastest_idx = valid["LapTime"].idxmin()
        summary["fastest_lap_time"] = safe_float(valid.loc[fastest_idx, "LapTime"])
        summary["fastest_lap_driver"] = valid.loc[fastest_idx, "Driver"]
        summary["fastest_lap_number"] = safe_int(valid.loc[fastest_idx, "LapNumber"])

        summary["median_lap_time"] = safe_float(valid["LapTime"].median())
        summary["mean_lap_time"] = safe_float(valid["LapTime"].mean())
        summary["pace_spread"] = safe_float(valid["LapTime"].max() - valid["LapTime"].min())
    else:
        summary.update({
            "fastest_lap_time": None, "fastest_lap_driver": None,
            "fastest_lap_number": None, "median_lap_time": None,
            "mean_lap_time": None, "pace_spread": None,
        })

    # Max lap number → race length estimate
    max_race_lap = 0
    if "LapNumber" in race_df.columns:
        max_race_lap = safe_int(race_df["LapNumber"].max()) or 0
        summary["max_lap_number"] = max_race_lap

    # Starting / finishing positions
    if "Position" in race_df.columns:
        first_lap = race_df[race_df["LapNumber"] == race_df["LapNumber"].min()]
        last_lap = race_df[race_df["LapNumber"] == race_df["LapNumber"].max()]

        start_positions = first_lap.set_index("Driver")["Position"].dropna().to_dict()
        finish_positions = last_lap.set_index("Driver")["Position"].dropna().to_dict()
        summary["start_positions"] = {k: safe_int(v) for k, v in start_positions.items()}
        summary["finish_positions"] = {k: safe_int(v) for k, v in finish_positions.items()}

        # Winner = driver with position 1 on last lap
        winner = [d for d, p in finish_positions.items() if safe_int(p) == 1]
        summary["winner"] = winner[0] if winner else None
        podium = sorted(
            [(d, safe_int(p)) for d, p in finish_positions.items() if safe_int(p) is not None and safe_int(p) <= 3],
            key=lambda x: x[1]
        )
        summary["podium"] = [d for d, _ in podium]

    # Stint / strategy distribution
    if "Stint" in race_df.columns:
        max_stints_per_driver = race_df.groupby("Driver")["Stint"].max()
        summary["avg_stints"] = safe_float(max_stints_per_driver.mean(), ndigits=1)
        summary["max_stints"] = safe_int(max_stints_per_driver.max())

    # Retirement / DNF detection (drivers completing < 90% of max laps)
    driver_max_laps = race_df.groupby("Driver")["LapNumber"].max().to_dict()
    dnfs = [d for d, laps in driver_max_laps.items() if max_race_lap > 0 and laps < (0.9 * max_race_lap)]
    summary["dnfs"] = dnfs
    summary["classified_finishers"] = len(driver_max_laps) - len(dnfs)

    return summary


def compute_driver_race_metrics(
    race_df: pd.DataFrame,
    driver: str,
    race_name: str,
    all_drivers_valid: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """
    Compute driver-level metrics within a single race.
    all_drivers_valid: valid laps for all drivers (used for teammate comparison).
    """
    driver_df = race_df[race_df["Driver"] == driver].copy()
    valid = filter_valid_laps(driver_df)
    max_race_lap = race_df["LapNumber"].max() if "LapNumber" in race_df.columns else 0
    driver_laps_completed = len(driver_df)

    m: Dict[str, Any] = {
        "driver": driver,
        "race": race_name,
        "race_round": RACE_ROUND.get(race_name),
        "total_laps": driver_laps_completed,
        "valid_laps": len(valid),
        "team": driver_df["Team"].iloc[0] if len(driver_df) > 0 else None,
        "is_classified": (driver_laps_completed >= 0.9 * max_race_lap) if max_race_lap > 0 else True,
        "status": "FIN" if (max_race_lap > 0 and driver_laps_completed >= 0.9 * max_race_lap) else "DNF",
    }

    # Pace metrics
    if len(valid) >= 3:
        m["best_lap"] = safe_float(valid["LapTime"].min())
        m["rep_pace"] = representative_pace(valid["LapTime"])
        m["median_pace"] = safe_float(valid["LapTime"].median())
        m["pace_std"] = safe_float(valid["LapTime"].std())
        m["pace_iqr"] = safe_float(
            valid["LapTime"].quantile(0.75) - valid["LapTime"].quantile(0.25)
        )
        m["consistency"] = consistency_score(valid["LapTime"])
    else:
        m.update({
            "best_lap": safe_float(valid["LapTime"].min()) if len(valid) > 0 else None,
            "rep_pace": None, "median_pace": None,
            "pace_std": None, "pace_iqr": None, "consistency": None,
        })

    # Positions
    if "Position" in driver_df.columns and len(driver_df) > 0:
        sorted_laps = driver_df.sort_values("LapNumber")
        first_pos = sorted_laps["Position"].dropna().iloc[0] if sorted_laps["Position"].notna().any() else None
        last_pos = sorted_laps["Position"].dropna().iloc[-1] if sorted_laps["Position"].notna().any() else None
        m["starting_position"] = safe_int(first_pos)
        m["finishing_position"] = safe_int(last_pos)
        m["position_gain"] = position_gain(first_pos, last_pos)
    else:
        m.update({"starting_position": None, "finishing_position": None, "position_gain": None})

    # Stints
    if "Stint" in driver_df.columns:
        stints = driver_df["Stint"].dropna()
        m["pit_stop_count"] = safe_int(stints.max() - 1) if len(stints) > 0 else None
        m["stint_count"] = safe_int(stints.max()) if len(stints) > 0 else None

    # Compounds used
    if "Compound" in driver_df.columns:
        m["compounds_used"] = sorted(driver_df["Compound"].dropna().unique().tolist())

    # Race pace trend (first half vs second half)
    if len(valid) >= 6:
        mid = len(valid) // 2
        first_half_pace = valid.iloc[:mid]["LapTime"].median()
        second_half_pace = valid.iloc[mid:]["LapTime"].median()
        m["first_half_pace"] = safe_float(first_half_pace)
        m["second_half_pace"] = safe_float(second_half_pace)
        if first_half_pace and second_half_pace:
            m["race_pace_delta"] = safe_float(second_half_pace - first_half_pace)
    else:
        m.update({"first_half_pace": None, "second_half_pace": None, "race_pace_delta": None})

    # Degradation estimate (overall stint)
    if len(valid) >= 5 and "LapNumber" in valid.columns:
        m["degradation_slope"] = degradation_slope(valid["LapTime"], valid["LapNumber"])
    else:
        m["degradation_slope"] = None

    return m


def compute_race_teammate_battles(race_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute intra-team head-to-head comparison for a single race.
    Returns DataFrame with: team, driver_1, driver_2, finish_1, finish_2,
                           pace_1, pace_2, pace_delta, ahead_driver
    """
    valid_all = filter_valid_laps(race_df)
    teams = race_df["Team"].dropna().unique()
    records = []

    for team in sorted(teams):
        team_laps = race_df[race_df["Team"] == team]
        team_drivers = team_laps["Driver"].dropna().unique().tolist()
        if len(team_drivers) >= 2:
            d1, d2 = team_drivers[0], team_drivers[1]
            m1 = compute_driver_race_metrics(race_df, d1, race_df["Race"].iloc[0], valid_all)
            m2 = compute_driver_race_metrics(race_df, d2, race_df["Race"].iloc[0], valid_all)

            f1 = m1.get("finishing_position")
            f2 = m2.get("finishing_position")
            p1 = m1.get("rep_pace")
            p2 = m2.get("rep_pace")

            pace_delta = round(p1 - p2, 3) if (p1 is not None and p2 is not None) else None
            ahead = None
            if f1 is not None and f2 is not None:
                ahead = d1 if f1 < f2 else (d2 if f2 < f1 else "TIE")

            records.append({
                "team": team,
                "driver_1": d1,
                "driver_2": d2,
                "finish_1": f1,
                "finish_2": f2,
                "pace_1": p1,
                "pace_2": p2,
                "pace_delta": pace_delta,
                "ahead_driver": ahead,
            })

    return pd.DataFrame(records)


def build_race_intelligence(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build race-level intelligence for all races in the DataFrame.
    Returns a DataFrame with one row per race.
    """
    records = []
    races = sorted(df["Race"].dropna().unique(), key=lambda r: RACE_ROUND.get(r, 99))
    logger.info(f"Building race intelligence for {len(races)} races...")
    for race in races:
        race_df = df[df["Race"] == race]
        summary = compute_race_summary(race_df, race)
        records.append(summary)
    result = pd.DataFrame(records)
    logger.info(f"Race intelligence built: {len(result)} races.")
    return result


def build_driver_race_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build driver-level per-race metrics for all drivers and races.
    Returns a DataFrame with one row per (driver, race).
    """
    records = []
    races = sorted(df["Race"].dropna().unique(), key=lambda r: RACE_ROUND.get(r, 99))
    logger.info(f"Building driver race metrics for {len(races)} races...")
    for race in races:
        race_df = df[df["Race"] == race]
        valid_all = filter_valid_laps(race_df)
        drivers = race_df["Driver"].dropna().unique()
        for driver in drivers:
            m = compute_driver_race_metrics(race_df, driver, race, valid_all)
            records.append(m)
    result = pd.DataFrame(records)
    logger.info(f"Driver race metrics built: {len(result)} records.")
    return result


def generate_race_debrief(race_df: pd.DataFrame, race_name: str) -> str:
    """
    Synthesizes an evidence-backed, factual Grand Prix summary debrief based on measurable race telemetry.
    """
    summary = compute_race_summary(race_df, race_name)
    winner = summary.get("winner", "Unknown")
    podium = summary.get("podium", [])
    fastest_driver = summary.get("fastest_lap_driver", "—")
    fastest_lap = summary.get("fastest_lap_time")
    dnfs = summary.get("dnfs", [])
    round_no = RACE_ROUND.get(race_name, "?")
    total_laps = summary.get("max_lap_number", 0)

    podium_str = ", ".join([f"P{i+1}: {d}" for i, d in enumerate(podium)]) if podium else "—"
    fastest_str = f"{fastest_driver} ({fastest_lap:.3f}s on Lap {summary.get('fastest_lap_number', '—')})" if fastest_lap else "—"

    debrief = (
        f"### 🏁 Round {round_no} · {race_name} Grand Prix Debrief\n\n"
        f"- **Race Victory:** **{winner}** claimed P1 after {total_laps} completed laps.\n"
        f"- **Podium Classification:** {podium_str}.\n"
        f"- **Fastest Lap Award:** {fastest_str}.\n"
        f"- **Race Pace Baseline:** Whole-grid median representative lap pace was **{summary.get('median_lap_time', 0):.3f}s**.\n"
        f"- **Retirements / DNFs:** {len(dnfs)} driver(s) retired from the session ({', '.join(dnfs) if dnfs else 'None'}).\n"
    )
    return debrief

