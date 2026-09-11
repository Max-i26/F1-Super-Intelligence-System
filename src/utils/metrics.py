"""
src/utils/metrics.py — Statistical Metrics for F1 Super Intelligence
=====================================================================
Robust, reusable metric calculations used across all intelligence modules.
All functions handle NaN, missing data, and edge cases explicitly.
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple

from src.utils.logging import get_logger

logger = get_logger(__name__)


def trimmed_mean(series: pd.Series, pct: float = 5.0) -> Optional[float]:
    """
    Calculate trimmed mean, removing `pct` percent from each tail.
    Returns None if insufficient data.
    """
    clean = series.dropna()
    if len(clean) < 3:
        return None
    lo = np.percentile(clean, pct)
    hi = np.percentile(clean, 100 - pct)
    trimmed = clean[(clean >= lo) & (clean <= hi)]
    if len(trimmed) == 0:
        return float(clean.median())
    return float(trimmed.mean())


def representative_pace(
    lap_times: pd.Series,
    iqr_factor: float = 3.0,
    trim_pct: float = 5.0,
) -> Optional[float]:
    """
    Robust representative lap time.
    Steps:
      1. Drop NaN.
      2. Remove IQR-based outliers.
      3. Return trimmed mean of the remaining values.
    """
    clean = lap_times.dropna()
    if len(clean) < 3:
        return float(clean.median()) if len(clean) > 0 else None

    q1 = clean.quantile(0.25)
    q3 = clean.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - iqr_factor * iqr
    upper = q3 + iqr_factor * iqr
    filtered = clean[(clean >= lower) & (clean <= upper)]

    if len(filtered) < 2:
        filtered = clean  # Fallback to all data

    return trimmed_mean(filtered, pct=trim_pct)


def pace_delta(time_a: Optional[float], time_b: Optional[float]) -> Optional[float]:
    """
    Difference between two lap times in seconds.
    Positive means time_a is slower than time_b.
    Returns None if either is None.
    """
    if time_a is None or time_b is None:
        return None
    if pd.isna(time_a) or pd.isna(time_b):
        return None
    return round(float(time_a) - float(time_b), 4)


def consistency_score(lap_times: pd.Series) -> Optional[float]:
    """
    Consistency = 1 / coefficient of variation (lower CV → higher score).
    Returns a 0–100 score. Returns None if insufficient data.
    """
    clean = lap_times.dropna()
    if len(clean) < 3:
        return None
    mean = clean.mean()
    std = clean.std()
    if mean == 0 or pd.isna(mean) or pd.isna(std):
        return None
    cv = std / mean
    # Map CV to 0–100: CV=0 → 100, CV=0.05 → 0 (typical F1 range)
    score = max(0.0, min(100.0, (1.0 - cv / 0.05) * 100))
    return round(score, 2)


def degradation_slope(lap_times: pd.Series, lap_numbers: pd.Series) -> Optional[float]:
    """
    Estimate tyre degradation as the slope (sec/lap) of a linear regression
    of lap_times vs lap_numbers within a stint.
    Returns None if insufficient data.
    """
    clean_mask = lap_times.notna() & lap_numbers.notna()
    times = lap_times[clean_mask].values
    laps = lap_numbers[clean_mask].values
    if len(times) < 3:
        return None
    try:
        slope = float(np.polyfit(laps, times, 1)[0])
        return round(slope, 5)
    except Exception:
        return None


def position_gain(start_pos: Optional[float], finish_pos: Optional[float]) -> Optional[int]:
    """
    Positions gained = start_pos - finish_pos.
    Positive means improved (e.g., start 10th, finish 5th → +5).
    Returns None if either position is unavailable.
    """
    if start_pos is None or finish_pos is None:
        return None
    if pd.isna(start_pos) or pd.isna(finish_pos):
        return None
    return int(round(float(start_pos) - float(finish_pos)))


def safe_int(value) -> Optional[int]:
    """Safely convert to int, returning None for NaN/None."""
    if value is None or pd.isna(value):
        return None
    return int(value)


def safe_float(value, ndigits: int = 4) -> Optional[float]:
    """Safely convert to float, returning None for NaN/None."""
    if value is None or pd.isna(value):
        return None
    return round(float(value), ndigits)


def percentile_rank(value: float, series: pd.Series) -> Optional[float]:
    """
    Return the percentile rank of `value` within `series` (0–100).
    100 = best (lowest lap time). 0 = worst.
    """
    clean = series.dropna()
    if len(clean) == 0 or pd.isna(value):
        return None
    rank = (clean > value).sum() / len(clean) * 100
    return round(float(rank), 2)


def pace_percentile(lap_time: float, all_times: pd.Series) -> Optional[float]:
    """
    Returns how good a lap time is relative to all others.
    100 = fastest, 0 = slowest.
    """
    return percentile_rank(lap_time, all_times)
