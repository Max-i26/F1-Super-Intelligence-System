"""
src/intelligence/tyres.py — Tyre & Stint Intelligence
======================================================
Context-aware tyre degradation analysis, tyre age modeling,
compound performance benchmarking, and cliff detection.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import RACE_ROUND, VALID_COMPOUNDS
from src.utils.metrics import (
    representative_pace, degradation_slope, safe_float, safe_int
)
from src.data.local import filter_valid_laps
from src.utils.logging import get_logger

logger = get_logger(__name__)


def build_stints(driver_race_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Extract stint-by-stint data for a driver in one race.
    Input: all laps for a single driver in a single race.
    """
    stints = []
    if "Stint" not in driver_race_df.columns or "LapNumber" not in driver_race_df.columns:
        return stints

    stint_groups = driver_race_df.groupby("Stint")

    for stint_num, stint_df in stint_groups:
        stint_valid = filter_valid_laps(stint_df)
        compound = stint_df["Compound"].mode().iloc[0] if len(stint_df) > 0 else "UNKNOWN"
        start_lap = safe_int(stint_df["LapNumber"].min())
        end_lap = safe_int(stint_df["LapNumber"].max())
        length = (end_lap - start_lap + 1) if (start_lap and end_lap) else None

        s: Dict[str, Any] = {
            "stint_num": safe_int(stint_num),
            "compound": compound,
            "start_lap": start_lap,
            "end_lap": end_lap,
            "length": length,
            "total_laps": len(stint_df),
            "valid_laps": len(stint_valid),
        }

        if len(stint_valid) >= 3:
            s["rep_pace"] = representative_pace(stint_valid["LapTime"])
            s["best_lap"] = safe_float(stint_valid["LapTime"].min())
            s["pace_std"] = safe_float(stint_valid["LapTime"].std())
            # Degradation: slope in seconds per lap
            s["degradation_slope"] = degradation_slope(
                stint_valid["LapTime"], stint_valid["LapNumber"]
            )
            # First lap vs last lap delta
            first_pace = safe_float(stint_valid.sort_values("LapNumber").iloc[0]["LapTime"])
            last_pace = safe_float(stint_valid.sort_values("LapNumber").iloc[-1]["LapTime"])
            if first_pace and last_pace:
                s["performance_drop"] = safe_float(last_pace - first_pace)
            else:
                s["performance_drop"] = None

            # Detect cliff (if degradation significantly accelerated in final 3 laps)
            s["cliff_detected"], s["cliff_lap"] = detect_tyre_cliff(stint_valid)
        else:
            s.update({
                "rep_pace": None, "best_lap": None, "pace_std": None,
                "degradation_slope": None, "performance_drop": None,
                "cliff_detected": False, "cliff_lap": None,
            })

        stints.append(s)

    return stints


def detect_tyre_cliff(stint_valid_df: pd.DataFrame) -> Tuple[bool, Optional[int]]:
    """
    Detect if tyre experienced a severe degradation 'cliff'.
    Returns (cliff_detected: bool, cliff_lap: Optional[int]).
    """
    if len(stint_valid_df) < 8:
        return False, None

    sorted_df = stint_valid_df.sort_values("LapNumber")
    main_body = sorted_df.iloc[:-3]
    final_laps = sorted_df.iloc[-3:]

    main_median = main_body["LapTime"].median()
    final_median = final_laps["LapTime"].median()

    # If final 3 laps are >1.5s slower than the main body median, flag as cliff
    if final_median - main_median > 1.5:
        cliff_lap = safe_int(final_laps.iloc[0]["LapNumber"])
        return True, cliff_lap

    return False, None


def compute_compound_degradation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes season-wide aggregate performance metrics per tyre compound.
    Returns: compound, rep_pace, median_pace, avg_degradation_slope, avg_stint_length, total_stints
    """
    valid_df = filter_valid_laps(df)
    records = []

    for compound in VALID_COMPOUNDS:
        c_laps = valid_df[valid_df["Compound"] == compound]
        if len(c_laps) >= 10:
            rep = representative_pace(c_laps["LapTime"])
            med = safe_float(c_laps["LapTime"].median())

            # Stint lengths and slopes for this compound
            stint_lens = []
            slopes = []
            for _, s_df in df[df["Compound"] == compound].groupby(["Race", "Driver", "Stint"]):
                s_valid = filter_valid_laps(s_df)
                stint_lens.append(len(s_df))
                if len(s_valid) >= 5:
                    sl = degradation_slope(s_valid["LapTime"], s_valid["LapNumber"])
                    if sl is not None and -0.1 < sl < 0.5:
                        slopes.append(sl)

            avg_slope = round(float(np.mean(slopes)), 4) if slopes else 0.05
            avg_len = round(float(np.mean(stint_lens)), 1) if stint_lens else 0.0

            records.append({
                "compound": compound,
                "rep_pace": rep,
                "median_pace": med,
                "avg_degradation_slope": avg_slope,
                "avg_stint_length": avg_len,
                "total_stints": len(stint_lens),
                "total_laps": len(c_laps),
            })

    return pd.DataFrame(records)


def build_tyre_intelligence(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build stint-level tyre intelligence for all drivers and races.
    Returns a long-format DataFrame with one row per stint.
    """
    records = []
    races = df["Race"].dropna().unique()
    logger.info(f"Building tyre intelligence for {len(races)} races...")

    for race in races:
        race_df = df[df["Race"] == race]
        drivers = race_df["Driver"].dropna().unique()
        for driver in drivers:
            driver_df = race_df[race_df["Driver"] == driver]
            stints = build_stints(driver_df)
            for stint in stints:
                stint["driver"] = driver
                stint["race"] = race
                stint["race_round"] = RACE_ROUND.get(race)
                stint["team"] = driver_df["Team"].mode().iloc[0] if len(driver_df) > 0 else None
                records.append(stint)

    result = pd.DataFrame(records)
    if "race_round" in result.columns:
        result = result.sort_values(["race_round", "driver", "stint_num"]).reset_index(drop=True)
    logger.info(f"Tyre intelligence built: {len(result)} stints.")
    return result


def compound_pace_comparison(df: pd.DataFrame, race: str) -> pd.DataFrame:
    """
    Compare representative pace by tyre compound for a given race.
    Returns a DataFrame: compound, rep_pace, median_pace, sample_size.
    """
    race_df = df[df["Race"] == race]
    valid = filter_valid_laps(race_df)
    records = []
    for compound in VALID_COMPOUNDS:
        c_laps = valid[valid["Compound"] == compound]["LapTime"]
        if len(c_laps) >= 3:
            records.append({
                "compound": compound,
                "rep_pace": representative_pace(c_laps),
                "median_pace": safe_float(c_laps.median()),
                "best_pace": safe_float(c_laps.min()),
                "sample_size": len(c_laps),
            })
    return pd.DataFrame(records)
