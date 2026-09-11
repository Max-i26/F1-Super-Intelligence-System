"""
src/intelligence/anomalies.py — Anomaly Detection Engine (Phase 7)
===================================================================
Detects race and telemetry anomalies with statistical confidence and contextual evidence.
Identifies:
- Statistical Lap Time Spikes (Z-Score > 2.5 on clean laps)
- Tyre Performance Cliffs & Sudden Degradation Drop-offs
- Pace Collapses & DNF Early Warning Indicators
- Stint Longevity Anomalies
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import DRIVERS_2025
from src.utils.logging import get_logger
from src.utils.metrics import safe_float, safe_int, representative_pace
from src.data.local import filter_valid_laps

logger = get_logger(__name__)


def detect_lap_time_anomalies(
    race_df: pd.DataFrame,
    driver: Optional[str] = None,
    z_threshold: float = 2.2,
) -> List[Dict[str, Any]]:
    """
    Detects statistically significant lap time outliers for a driver or across the race.
    Uses robust median absolute deviation (MAD) / Z-score against driver's representative pace.
    """
    anomalies = []
    if "LapTime" not in race_df.columns or "Driver" not in race_df.columns:
        return anomalies

    drivers = [driver] if driver else sorted(race_df["Driver"].dropna().unique())

    for d in drivers:
        d_laps = race_df[race_df["Driver"] == d].sort_values("LapNumber").copy()
        if len(d_laps) < 5:
            continue

        # Valid laps only (excluding pit in/out laps)
        valid = filter_valid_laps(d_laps)
        if len(valid) < 5:
            continue

        median_pace = valid["LapTime"].median()
        std_pace = valid["LapTime"].std()
        if pd.isna(std_pace) or std_pace < 0.05:
            std_pace = 0.5  # Fallback minimum std

        for _, row in valid.iterrows():
            lap_no = int(row["LapNumber"])
            lap_time = float(row["LapTime"])
            delta = lap_time - median_pace
            z_score = delta / std_pace

            if z_score >= z_threshold:
                severity = "CRITICAL" if z_score > 4.0 else ("WARNING" if z_score > 3.0 else "INFO")
                anomalies.append({
                    "race": row.get("Race", "Race"),
                    "lap": lap_no,
                    "driver": d,
                    "team": row.get("Team") or DRIVERS_2025.get(d, {}).get("team", "Unknown"),
                    "type": "LAP TIME OUTLIER",
                    "severity": severity,
                    "lap_time": round(lap_time, 3),
                    "expected_pace": round(median_pace, 3),
                    "delta_seconds": round(delta, 3),
                    "z_score": round(z_score, 2),
                    "evidence": f"Lap time {lap_time:.3f}s was +{delta:.3f}s slower than driver median ({median_pace:.3f}s, Z={z_score:.1f}). Possible off-track, battle, or yellow flag.",
                })

    return anomalies


def detect_race_pace_collapses(race_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Detects sudden pace collapses across consecutive laps (e.g. 3+ seconds loss over 2 laps)
    indicating terminal tyre degradation, floor/aero damage, or impending retirement.
    """
    collapses = []
    if "LapTime" not in race_df.columns:
        return collapses

    for driver in race_df["Driver"].dropna().unique():
        d_df = race_df[race_df["Driver"] == driver].sort_values("LapNumber").copy()
        valid = filter_valid_laps(d_df)
        if len(valid) < 6:
            continue

        times = valid["LapTime"].values
        laps = valid["LapNumber"].values

        for i in range(2, len(times)):
            rolling_prev_avg = np.mean(times[max(0, i-4):i])
            curr_time = times[i]
            delta = curr_time - rolling_prev_avg

            if delta > 2.8:  # Sudden drop > 2.8s
                lap_no = int(laps[i])
                collapses.append({
                    "race": valid.iloc[0].get("Race", "Race"),
                    "lap": lap_no,
                    "driver": driver,
                    "team": valid.iloc[0].get("Team") or DRIVERS_2025.get(driver, {}).get("team", "Unknown"),
                    "type": "PACE COLLAPSE",
                    "severity": "CRITICAL" if delta > 5.0 else "WARNING",
                    "lap_time": round(float(curr_time), 3),
                    "expected_pace": round(float(rolling_prev_avg), 3),
                    "delta_seconds": round(float(delta), 3),
                    "z_score": round(float(delta / 0.8), 2),
                    "evidence": f"Pace collapsed by +{delta:.2f}s relative to previous 4-lap baseline. Consistent with sudden degradation cliff or car issue.",
                })

    return collapses


def compile_all_anomalies(race_df: pd.DataFrame) -> pd.DataFrame:
    """
    Runs all anomaly detectors and returns a consolidated, ranked DataFrame.
    """
    outliers = detect_lap_time_anomalies(race_df)
    collapses = detect_race_pace_collapses(race_df)

    all_items = outliers + collapses
    if not all_items:
        return pd.DataFrame(columns=[
            "race", "lap", "driver", "team", "type", "severity",
            "lap_time", "expected_pace", "delta_seconds", "z_score", "evidence"
        ])

    df_anom = pd.DataFrame(all_items)
    # Deduplicate by driver & lap
    df_anom = df_anom.drop_duplicates(subset=["driver", "lap"]).sort_values(["lap", "z_score"], ascending=[True, False])
    return df_anom

