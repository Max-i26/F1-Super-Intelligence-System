"""
src/intelligence/driver.py — Driver Intelligence for F1 Super Intelligence
===========================================================================
Builds complete driver profiles, performance radar dimensions,
rolling form & momentum curves, teammate head-to-head records,
and season evolution data across all 24 rounds.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import RACE_ROUND, RACES_2025, DRIVERS_2025, POINTS_FOR_POSITION
from src.utils.metrics import (
    representative_pace,
    consistency_score,
    degradation_slope,
    position_gain,
    safe_int,
    safe_float,
    trimmed_mean,
)
from src.data.local import filter_valid_laps
from src.utils.logging import get_logger

logger = get_logger(__name__)


def build_driver_profile(df: pd.DataFrame, driver: str) -> Dict[str, Any]:
    """
    Build a complete season profile for a single driver.
    Covers all races in the dataset.
    """
    driver_df = df[df["Driver"] == driver].copy()
    valid = filter_valid_laps(driver_df)

    # Basic identity
    profile: Dict[str, Any] = {
        "driver": driver,
        "team": driver_df["Team"].mode().iloc[0] if len(driver_df) > 0 else None,
        "full_name": DRIVERS_2025.get(driver, {}).get("full_name", driver),
        "races": sorted(driver_df["Race"].dropna().unique().tolist(), key=lambda r: RACE_ROUND.get(r, 99)),
        "race_count": driver_df["Race"].nunique(),
        "total_laps": len(driver_df),
        "valid_laps": len(valid),
    }

    # Season pace metrics
    if len(valid) >= 5:
        profile["best_lap_ever"] = safe_float(valid["LapTime"].min())
        profile["rep_pace_season"] = representative_pace(valid["LapTime"])
        profile["median_pace_season"] = safe_float(valid["LapTime"].median())
        profile["pace_std_season"] = safe_float(valid["LapTime"].std())
        profile["consistency_season"] = consistency_score(valid["LapTime"])
    else:
        profile.update({
            "best_lap_ever": None, "rep_pace_season": None,
            "median_pace_season": None, "pace_std_season": None,
            "consistency_season": None,
        })

    # Finishing positions
    if "Position" in driver_df.columns:
        finish_positions = []
        start_positions = []
        for race in profile["races"]:
            race_laps = driver_df[driver_df["Race"] == race].sort_values("LapNumber")
            first_pos = race_laps["Position"].dropna().iloc[0] if race_laps["Position"].notna().any() else None
            last_pos = race_laps["Position"].dropna().iloc[-1] if race_laps["Position"].notna().any() else None
            if first_pos is not None:
                start_positions.append(safe_int(first_pos))
            if last_pos is not None:
                finish_positions.append(safe_int(last_pos))

        valid_finishes = [p for p in finish_positions if p is not None]
        profile["avg_finish_position"] = safe_float(
            sum(valid_finishes) / len(valid_finishes), ndigits=1
        ) if valid_finishes else None
        profile["best_finish"] = safe_int(min(valid_finishes)) if valid_finishes else None
        profile["worst_finish"] = safe_int(max(valid_finishes)) if valid_finishes else None
        profile["podiums"] = sum(1 for p in valid_finishes if p <= 3)
        profile["wins"] = sum(1 for p in valid_finishes if p == 1)
        profile["top10_finishes"] = sum(1 for p in valid_finishes if p <= 10)

        # Average position gain
        gains = [s - f for s, f in zip(start_positions, finish_positions) if s is not None and f is not None]
        profile["avg_position_gain"] = safe_float(sum(gains) / len(gains), ndigits=1) if gains else 0.0

    # Tyre usage
    if "Compound" in driver_df.columns:
        compound_counts = driver_df["Compound"].value_counts().to_dict()
        profile["compound_usage"] = compound_counts

    # Average stints per race
    if "Stint" in driver_df.columns:
        avg_stints = driver_df.groupby("Race")["Stint"].max().mean()
        profile["avg_stints_per_race"] = safe_float(avg_stints, ndigits=1)

    return profile


def build_driver_evolution(df: pd.DataFrame, driver: str) -> pd.DataFrame:
    """
    Build race-by-race evolution data for a driver across all 24 rounds.
    Includes rolling momentum, relative grid pace delta, and stint stats.
    """
    driver_df = df[df["Driver"] == driver].copy()
    valid_all = filter_valid_laps(df)
    races = sorted(driver_df["Race"].dropna().unique(), key=lambda r: RACE_ROUND.get(r, 99))

    records = []
    for race in races:
        race_df = driver_df[driver_df["Race"] == race]
        valid = filter_valid_laps(race_df)
        race_all_valid = valid_all[valid_all["Race"] == race]

        # Calculate grid median representative pace for relative index
        grid_median_pace = None
        if len(race_all_valid) > 0:
            grid_median_pace = race_all_valid["LapTime"].median()

        rec: Dict[str, Any] = {
            "driver": driver,
            "race": race,
            "race_round": RACE_ROUND.get(race),
        }

        # Pace
        if len(valid) >= 3:
            rep = representative_pace(valid["LapTime"])
            rec["rep_pace"] = rep
            rec["best_lap"] = safe_float(valid["LapTime"].min())
            rec["median_pace"] = safe_float(valid["LapTime"].median())
            rec["consistency"] = consistency_score(valid["LapTime"])
            # Relative pace delta to race median (negative = faster than grid median)
            if rep is not None and grid_median_pace is not None:
                rec["relative_pace_to_median"] = safe_float(rep - grid_median_pace)
            else:
                rec["relative_pace_to_median"] = None
        else:
            rec.update({
                "rep_pace": None, "best_lap": None, "median_pace": None,
                "consistency": None, "relative_pace_to_median": None
            })

        # Position
        if "Position" in race_df.columns:
            sorted_laps = race_df.sort_values("LapNumber")
            first_pos = sorted_laps["Position"].dropna().iloc[0] if sorted_laps["Position"].notna().any() else None
            last_pos = sorted_laps["Position"].dropna().iloc[-1] if sorted_laps["Position"].notna().any() else None
            f_pos = safe_int(last_pos)
            rec["starting_position"] = safe_int(first_pos)
            rec["finishing_position"] = f_pos
            rec["position_gain"] = position_gain(first_pos, last_pos)
            rec["points_estimate"] = POINTS_FOR_POSITION.get(f_pos, 0) if f_pos else 0
        else:
            rec.update({
                "starting_position": None, "finishing_position": None,
                "position_gain": None, "points_estimate": 0
            })

        # Stints
        if "Stint" in race_df.columns:
            rec["stint_count"] = safe_int(race_df["Stint"].max())
            rec["pit_stop_count"] = max(0, safe_int(race_df["Stint"].max()) - 1) if safe_int(race_df["Stint"].max()) else None

        # Degradation
        if len(valid) >= 5 and "LapNumber" in valid.columns:
            rec["degradation_slope"] = degradation_slope(valid["LapTime"], valid["LapNumber"])
        else:
            rec["degradation_slope"] = None

        records.append(rec)

    result = pd.DataFrame(records)
    if "race_round" in result.columns:
        result = result.sort_values("race_round").reset_index(drop=True)

    # Compute rolling form indicators (3-race rolling finish)
    if "finishing_position" in result.columns and len(result) >= 3:
        result["rolling_3_finish"] = result["finishing_position"].rolling(3, min_periods=1).mean().round(1)
        result["rolling_3_rep_pace"] = result["rep_pace"].rolling(3, min_periods=1).mean().round(3)
        # Form momentum: compare last 3 finish vs earlier
        momentum_diff = result["finishing_position"].diff(1)
        result["position_momentum"] = momentum_diff.apply(
            lambda d: "IMPROVING 📈" if d < 0 else ("SLIPPING 📉" if d > 0 else "LEVEL ⚖️")
        )

    return result


def detect_driver_milestones(evolution_df: pd.DataFrame, driver: str) -> List[Dict[str, str]]:
    """
    Detect significant season milestones and inflection points for a driver.
    """
    d_evo = evolution_df[evolution_df["driver"] == driver].sort_values("race_round")
    if d_evo.empty:
        return []

    milestones = []

    # 1. Best Finish
    best_row = d_evo.loc[d_evo["finishing_position"].idxmin()] if d_evo["finishing_position"].notna().any() else None
    if best_row is not None:
        milestones.append({
            "type": "🏆 Peak Result",
            "title": f"P{int(best_row['finishing_position'])} at {best_row['race']}",
            "description": f"Best finishing position of the season (Round {int(best_row['race_round'])})"
        })

    # 2. Biggest Position Gain
    if "position_gain" in d_evo.columns and d_evo["position_gain"].notna().any():
        max_gain_row = d_evo.loc[d_evo["position_gain"].idxmax()]
        gain_val = int(max_gain_row["position_gain"])
        if gain_val > 0:
            milestones.append({
                "type": "⚡ Biggest Charge",
                "title": f"+{gain_val} Positions at {max_gain_row['race']}",
                "description": f"Grid P{int(max_gain_row.get('starting_position', 0))} → Finish P{int(max_gain_row['finishing_position'])}"
            })

    # 3. Best Relative Pace
    if "relative_pace_to_median" in d_evo.columns and d_evo["relative_pace_to_median"].notna().any():
        best_pace_row = d_evo.loc[d_evo["relative_pace_to_median"].idxmin()]
        pace_val = float(best_pace_row["relative_pace_to_median"])
        if pace_val < 0:
            milestones.append({
                "type": "🏎️ Dominant Pace",
                "title": f"{abs(pace_val):.3f}s faster than grid median",
                "description": f"Highest relative pace advantage achieved at {best_pace_row['race']}"
            })

    # 4. Highest Consistency Race
    if "consistency" in d_evo.columns and d_evo["consistency"].notna().any():
        best_cons_row = d_evo.loc[d_evo["consistency"].idxmax()]
        milestones.append({
            "type": "🎯 Peak Metronomic Consistency",
            "title": f"{float(best_cons_row['consistency']):.1f}/100 at {best_cons_row['race']}",
            "description": f"Most consistent rhythm of the season"
        })

    return milestones


def compute_driver_radar_dimensions(df: pd.DataFrame, driver: str) -> Dict[str, float]:
    """
    Compute 5 normalized empirical radar dimensions (0–100 scale) for a driver.
    - Raw Pace: Based on representative lap pace ranking vs grid
    - Consistency: Based on coefficient of variation across all season laps
    - Racecraft: Based on net positions gained from start to finish
    - Tyre Management: Based on stint degradation slopes (lower slope -> higher score)
    - Reliability: Percentage of race laps completed vs max possible
    """
    driver_df = df[df["Driver"] == driver]
    valid_driver = filter_valid_laps(driver_df)
    valid_all = filter_valid_laps(df)

    if len(valid_driver) < 10:
        return {
            "Raw Pace": 50.0,
            "Consistency": 50.0,
            "Racecraft": 50.0,
            "Tyre Management": 50.0,
            "Finishing Rate": 50.0,
        }

    # 1. Raw Pace (lower lap time percentile)
    driver_rep = representative_pace(valid_driver["LapTime"])
    all_reps = [representative_pace(valid_all[valid_all["Driver"] == d]["LapTime"]) for d in df["Driver"].unique()]
    valid_reps = [r for r in all_reps if r is not None]
    if valid_reps and driver_rep:
        min_p = min(valid_reps)
        max_p = max(valid_reps)
        pace_score = max(0.0, min(100.0, (1.0 - (driver_rep - min_p) / (max_p - min_p + 1e-6)) * 100))
    else:
        pace_score = 60.0

    # 2. Consistency Score
    cons_score = consistency_score(valid_driver["LapTime"]) or 50.0

    # 3. Racecraft / Position Gain
    first_laps = driver_df.groupby("Race")["Position"].first()
    last_laps = driver_df.groupby("Race")["Position"].last()
    gains = (first_laps - last_laps).dropna()
    avg_gain = gains.mean() if len(gains) > 0 else 0.0
    racecraft_score = max(10.0, min(100.0, 50.0 + (avg_gain * 12.0)))

    # 4. Tyre Management
    if "Stint" in driver_df.columns:
        slopes = []
        for _, s_df in driver_df.groupby(["Race", "Stint"]):
            s_valid = filter_valid_laps(s_df)
            if len(s_valid) >= 5:
                sl = degradation_slope(s_valid["LapTime"], s_valid["LapNumber"])
                if sl is not None:
                    slopes.append(sl)
        avg_slope = np.median(slopes) if slopes else 0.05
        tyre_score = max(10.0, min(100.0, (1.0 - (max(0.0, avg_slope) / 0.15)) * 100))
    else:
        tyre_score = 60.0

    # 5. Finishing Rate / Laps completed
    total_driver_laps = len(driver_df)
    max_possible_laps = df.groupby("Race")["LapNumber"].max().sum()
    finishing_score = max(20.0, min(100.0, (total_driver_laps / (max_possible_laps + 1e-6)) * 100))

    return {
        "Raw Pace": round(float(pace_score), 1),
        "Consistency": round(float(cons_score), 1),
        "Racecraft": round(float(racecraft_score), 1),
        "Tyre Management": round(float(tyre_score), 1),
        "Finishing Rate": round(float(finishing_score), 1),
    }


def compute_driver_teammate_summary(df: pd.DataFrame, driver: str) -> Dict[str, Any]:
    """
    Compute season-long head-to-head comparison between a driver and their teammate(s).
    """
    delta_df = build_teammate_delta(df)
    d_deltas = delta_df[delta_df["driver"] == driver]
    
    if len(d_deltas) == 0:
        return {
            "teammate": "N/A",
            "races_together": 0,
            "faster_races": 0,
            "slower_races": 0,
            "avg_pace_delta": None,
        }

    teammate_name = d_deltas["teammate"].mode().iloc[0]
    total_races = len(d_deltas)
    pace_deltas = d_deltas["pace_delta"].dropna()
    avg_pace_delta = round(float(pace_deltas.mean()), 3) if len(pace_deltas) > 0 else None

    faster_count = sum(1 for d in pace_deltas if d < 0)
    slower_count = sum(1 for d in pace_deltas if d > 0)

    return {
        "teammate": teammate_name,
        "races_together": total_races,
        "faster_races": faster_count,
        "slower_races": slower_count,
        "avg_pace_delta": avg_pace_delta,
    }


def build_teammate_delta(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each race, compute pace delta between teammates.
    Returns a DataFrame with columns: Race, Driver, Teammate, PaceDelta (seconds).
    Positive delta = driver is slower than teammate.
    """
    records = []
    races = df["Race"].dropna().unique()
    valid_df = filter_valid_laps(df)

    for race in races:
        race_valid = valid_df[valid_df["Race"] == race]
        driver_pace = {}
        driver_team = {}
        for driver in race_valid["Driver"].unique():
            d_laps = race_valid[race_valid["Driver"] == driver]["LapTime"]
            pace = representative_pace(d_laps)
            team_rows = race_valid[race_valid["Driver"] == driver]["Team"]
            team = team_rows.mode().iloc[0] if len(team_rows) > 0 else None
            if pace is not None and team is not None:
                driver_pace[driver] = pace
                driver_team[driver] = team

        from collections import defaultdict
        team_drivers: Dict[str, List[str]] = defaultdict(list)
        for d, t in driver_team.items():
            team_drivers[t].append(d)

        for team, drivers in team_drivers.items():
            if len(drivers) >= 2:
                d1, d2 = drivers[0], drivers[1]
                if d1 in driver_pace and d2 in driver_pace:
                    records.append({
                        "race": race,
                        "race_round": RACE_ROUND.get(race),
                        "team": team,
                        "driver": d1,
                        "teammate": d2,
                        "driver_pace": driver_pace[d1],
                        "teammate_pace": driver_pace[d2],
                        "pace_delta": round(driver_pace[d1] - driver_pace[d2], 4),
                    })
                    records.append({
                        "race": race,
                        "race_round": RACE_ROUND.get(race),
                        "team": team,
                        "driver": d2,
                        "teammate": d1,
                        "driver_pace": driver_pace[d2],
                        "teammate_pace": driver_pace[d1],
                        "pace_delta": round(driver_pace[d2] - driver_pace[d1], 4),
                    })

    result = pd.DataFrame(records)
    if "race_round" in result.columns:
        result = result.sort_values(["team", "driver", "race_round"]).reset_index(drop=True)
    return result


def build_all_driver_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """Build profiles for all drivers in the dataset."""
    drivers = df["Driver"].dropna().unique()
    logger.info(f"Building profiles for {len(drivers)} drivers...")
    profiles = [build_driver_profile(df, d) for d in drivers]
    return pd.DataFrame(profiles)


def build_all_driver_evolution(df: pd.DataFrame) -> pd.DataFrame:
    """Build evolution data for all drivers in the dataset."""
    drivers = df["Driver"].dropna().unique()
    logger.info(f"Building evolution data for {len(drivers)} drivers...")
    all_records = []
    for d in drivers:
        evo = build_driver_evolution(df, d)
        all_records.append(evo)
    if all_records:
        return pd.concat(all_records, ignore_index=True)
    return pd.DataFrame()
