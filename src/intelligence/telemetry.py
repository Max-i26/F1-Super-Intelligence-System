"""
src/intelligence/telemetry.py — Telemetry Intelligence Engine (Phase 7)
========================================================================
Processes high-frequency or representative car telemetry profiles (Speed, Throttle, Brake, Gear, RPM).
Provides corner-by-corner speed comparison, apex speed extraction, and driver telemetry overlays.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import DRIVERS_2025, TEAMS_2025
from src.utils.logging import get_logger
from src.utils.metrics import safe_float

logger = get_logger(__name__)


def generate_synthetic_telemetry(
    driver: str,
    lap_time: float,
    race_name: str,
    n_points: int = 200,
    seed: Optional[int] = None,
) -> pd.DataFrame:
    """
    Generates a realistic distance-based telemetry trace (Speed, Throttle, Brake, Gear, RPM)
    calibrated to the driver's lap time and representative circuit profile.
    Useful for detailed turn-by-turn visualization when high-frequency API data is offline.
    """
    if seed is not None:
        np.random.seed(seed)
    else:
        # Deterministic seed based on driver & lap time
        np.random.seed(abs(hash(f"{driver}_{race_name}_{round(lap_time, 2)}")) % (2**31))

    # Normalized track distance from 0m to 5200m (typical F1 circuit length)
    track_length = 5200.0
    distance = np.linspace(0, track_length, n_points)

    # Base profile: 12 corners with braking zones and straights
    corner_locs = [350, 750, 1150, 1600, 2050, 2500, 2950, 3400, 3850, 4250, 4650, 5000]
    
    speed_base = np.full(n_points, 315.0)  # Top speed baseline
    throttle_base = np.full(n_points, 100.0)
    brake_base = np.zeros(n_points)
    
    # Scale speed by driver lap time (faster lap -> higher average speed)
    pace_factor = 85.0 / max(lap_time, 60.0)
    
    for c_idx, c_dist in enumerate(corner_locs):
        c_speed = 85.0 + (c_idx % 4) * 35.0  # Varying corner speeds (85 to 190 km/h)
        for i, d in enumerate(distance):
            dist_to_c = abs(d - c_dist)
            if dist_to_c < 120.0:
                t = dist_to_c / 120.0
                speed_base[i] = min(speed_base[i], c_speed + (315.0 - c_speed) * (t**1.5))
                if d < c_dist:
                    brake_base[i] = max(brake_base[i], 100.0 * (1.0 - t))
                    throttle_base[i] = min(throttle_base[i], 10.0 * t)
                else:
                    throttle_base[i] = min(throttle_base[i], 100.0 * t)
                    brake_base[i] = 0.0

    driver_hash = abs(hash(driver)) % 100
    driver_offset = (driver_hash - 50) / 50.0  # -1.0 to +1.0 km/h
    
    speed = np.clip(speed_base * pace_factor + driver_offset, 60.0, 350.0)
    throttle = np.clip(throttle_base + np.random.normal(0, 1.5, n_points), 0.0, 100.0)
    brake = np.clip(brake_base + np.random.normal(0, 1.0, n_points), 0.0, 100.0)
    
    # Calculate Gear from Speed
    gear = np.select(
        [speed < 90, speed < 130, speed < 170, speed < 215, speed < 260, speed < 300],
        [2, 3, 4, 5, 6, 7],
        default=8
    )
    
    rpm = np.clip(10000 + (speed / (gear * 40.0)) * 2500 + np.random.normal(0, 50, n_points), 8000, 14800)

    return pd.DataFrame({
        "distance_m": np.round(distance, 1),
        "speed_kmh": np.round(speed, 1),
        "throttle_pct": np.round(throttle, 1),
        "brake_pct": np.round(brake, 1),
        "gear": gear.astype(int),
        "rpm": np.round(rpm, 0).astype(int),
        "driver": driver,
        "lap_time": round(float(lap_time), 3),
    })


def extract_telemetry_features(telemetry_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes key telemetry KPI features:
    - Top Speed (km/h)
    - Minimum Apex Speed (km/h)
    - Full Throttle Percentage (% of lap distance)
    - Heavy Braking Distance (% of lap distance)
    - Average Corner Speed (km/h)
    """
    if telemetry_df.empty:
        return {}

    top_speed = float(telemetry_df["speed_kmh"].max())
    min_speed = float(telemetry_df["speed_kmh"].min())
    full_throttle_pct = float((telemetry_df["throttle_pct"] > 95.0).mean() * 100.0)
    heavy_brake_pct = float((telemetry_df["brake_pct"] > 50.0).mean() * 100.0)
    avg_speed = float(telemetry_df["speed_kmh"].mean())

    cornering_points = telemetry_df[telemetry_df["speed_kmh"] < 220.0]
    avg_corner_speed = float(cornering_points["speed_kmh"].mean()) if not cornering_points.empty else min_speed

    return {
        "top_speed_kmh": round(top_speed, 1),
        "min_speed_kmh": round(min_speed, 1),
        "avg_speed_kmh": round(avg_speed, 1),
        "avg_corner_speed_kmh": round(avg_corner_speed, 1),
        "full_throttle_pct": round(full_throttle_pct, 1),
        "heavy_brake_pct": round(heavy_brake_pct, 1),
    }


def compare_driver_telemetry(
    d1_telemetry: pd.DataFrame,
    d2_telemetry: pd.DataFrame
) -> pd.DataFrame:
    """
    Aligns two driver telemetry traces by track distance and computes delta metrics:
    - Speed delta (km/h, positive = Driver 1 faster)
    - Throttle delta
    - Brake delta
    """
    if d1_telemetry.empty or d2_telemetry.empty:
        return pd.DataFrame()

    merged = pd.merge_asof(
        d1_telemetry.sort_values("distance_m"),
        d2_telemetry.sort_values("distance_m"),
        on="distance_m",
        suffixes=("_d1", "_d2")
    )

    merged["speed_delta_kmh"] = np.round(merged["speed_kmh_d1"] - merged["speed_kmh_d2"], 2)
    merged["throttle_delta_pct"] = np.round(merged["throttle_pct_d1"] - merged["throttle_pct_d2"], 2)
    merged["brake_delta_pct"] = np.round(merged["brake_pct_d1"] - merged["brake_pct_d2"], 2)

    return merged

