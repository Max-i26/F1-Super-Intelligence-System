"""
src/intelligence/teams.py — Constructor Intelligence Engine (Phase 8)
======================================================================
Computes constructor pace trajectory across 24 rounds, intra-team driver
contribution split, development index, and pit stop operational metrics.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import RACE_ROUND, RACES_2025, TEAMS_2025, DRIVERS_2025
from src.utils.logging import get_logger
from src.utils.metrics import representative_pace, safe_float, safe_int
from src.data.local import filter_valid_laps

logger = get_logger(__name__)


def compute_team_season_trajectory(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes round-by-round representative pace delta to grid median for each constructor.
    Enables tracking of in-season aerodynamic and mechanical car development.
    """
    if "Race" not in df.columns or "LapTime" not in df.columns or "Team" not in df.columns:
        return pd.DataFrame()

    valid = filter_valid_laps(df)
    records = []

    for race in df["Race"].dropna().unique():
        r_valid = valid[valid["Race"] == race]
        if r_valid.empty:
            continue

        grid_median = r_valid["LapTime"].median()
        round_no = RACE_ROUND.get(race, 0)

        for team in r_valid["Team"].dropna().unique():
            t_laps = r_valid[r_valid["Team"] == team]
            if len(t_laps) < 10:
                continue

            t_rep_pace = representative_pace(t_laps["LapTime"]) or t_laps["LapTime"].median()
            delta_to_grid = t_rep_pace - grid_median

            records.append({
                "race": race,
                "race_round": round_no,
                "team": team,
                "rep_pace": round(float(t_rep_pace), 3),
                "grid_median_pace": round(float(grid_median), 3),
                "pace_delta_to_median": round(float(delta_to_grid), 3),
                "total_team_laps": len(t_laps),
            })

    traj_df = pd.DataFrame(records)
    if not traj_df.empty:
        traj_df = traj_df.sort_values(["team", "race_round"]).reset_index(drop=True)
    return traj_df


def compute_team_driver_contributions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes intra-team pace and lap contribution breakdown between teammates.
    """
    if "Team" not in df.columns or "Driver" not in df.columns:
        return pd.DataFrame()

    records = []
    teams = sorted(df["Team"].dropna().unique())

    for team in teams:
        t_df = df[df["Team"] == team]
        drivers = sorted(t_df["Driver"].dropna().unique())
        if len(drivers) < 2:
            continue

        d1, d2 = drivers[0], drivers[1]
        d1_df = t_df[t_df["Driver"] == d1]
        d2_df = t_df[t_df["Driver"] == d2]

        d1_valid = filter_valid_laps(d1_df)
        d2_valid = filter_valid_laps(d2_df)

        d1_pace = representative_pace(d1_valid["LapTime"]) if not d1_valid.empty else None
        d2_pace = representative_pace(d2_valid["LapTime"]) if not d2_valid.empty else None

        pace_gap = (d1_pace - d2_pace) if (d1_pace and d2_pace) else 0.0

        records.append({
            "team": team,
            "driver_1": d1,
            "driver_2": d2,
            "d1_laps": len(d1_df),
            "d2_laps": len(d2_df),
            "d1_rep_pace": round(float(d1_pace), 3) if d1_pace else None,
            "d2_rep_pace": round(float(d2_pace), 3) if d2_pace else None,
            "pace_delta_s": round(float(pace_gap), 3),
            "faster_driver": d1 if pace_gap < 0 else (d2 if pace_gap > 0 else "Tied"),
        })

    return pd.DataFrame(records)


def compute_team_pit_stop_efficiency(df: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluates pit stop execution frequency, stint management, and multi-stop rate by team.
    """
    if "Stint" not in df.columns or "Team" not in df.columns:
        return pd.DataFrame()

    records = []
    for team in df["Team"].dropna().unique():
        t_df = df[df["Team"] == team]
        drivers = t_df["Driver"].dropna().unique()

        stints_per_driver_race = []
        for race in t_df["Race"].dropna().unique():
            r_df = t_df[t_df["Race"] == race]
            for d in drivers:
                d_r = r_df[r_df["Driver"] == d]
                if not d_r.empty and "Stint" in d_r.columns:
                    stints_per_driver_race.append(d_r["Stint"].nunique())

        avg_stints = np.mean(stints_per_driver_race) if stints_per_driver_race else 2.0
        avg_stops = max(0.0, avg_stints - 1.0)

        records.append({
            "team": team,
            "avg_pit_stops_per_race": round(float(avg_stops), 2),
            "total_driver_starts": len(stints_per_driver_race),
            "one_stop_pct": round(float(np.mean([s == 2 for s in stints_per_driver_race]) * 100), 1) if stints_per_driver_race else 50.0,
            "multi_stop_pct": round(float(np.mean([s > 2 for s in stints_per_driver_race]) * 100), 1) if stints_per_driver_race else 50.0,
        })

    return pd.DataFrame(records).sort_values("avg_pit_stops_per_race").reset_index(drop=True)

