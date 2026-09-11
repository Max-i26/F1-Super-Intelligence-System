"""
src/data/local.py — Local Data Loader for F1 Super Intelligence
================================================================
Single entry point for loading and preparing the season_laps.csv dataset.
Applies normalization and returns a clean DataFrame.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import SEASON_LAPS_CSV, REQUIRED_LAP_COLUMNS
from src.data.normalization import apply_normalization
from src.data.validation import audit_dataframe, AuditReport
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Module-level cache — loaded once per session
_df_cache: Optional[pd.DataFrame] = None
_audit_cache: Optional[AuditReport] = None


def _load_raw() -> pd.DataFrame:
    """Load raw season_laps.csv with type coercion."""
    path = SEASON_LAPS_CSV
    if not path.exists():
        raise FileNotFoundError(
            f"season_laps.csv not found at: {path}\n"
            f"Please place your processed lap data at:\n  {path}"
        )
    logger.info(f"Loading: {path}")
    df = pd.read_csv(
        path,
        dtype={
            "Driver": str,
            "Team": str,
            "Compound": str,
            "Race": str,
        },
    )
    # Coerce numeric columns safely
    for col in ["LapNumber", "LapTime", "Stint", "Position", "Year"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    logger.info(f"Raw load: {len(df)} rows × {len(df.columns)} columns")
    return df


def load_season_laps(
    force_reload: bool = False,
) -> Tuple[pd.DataFrame, AuditReport]:
    """
    Load, normalize, and audit the season_laps dataset.

    Returns:
        (df, audit_report)
        - df: Normalized DataFrame
        - audit_report: AuditReport with all quality findings

    The result is cached in memory for the session.
    Use force_reload=True to bypass cache.
    """
    global _df_cache, _audit_cache
    if _df_cache is not None and not force_reload:
        return _df_cache, _audit_cache

    # Load raw
    df = _load_raw()

    # Normalize
    df = apply_normalization(df)

    # Audit (post-normalization, so race names are canonical)
    report = audit_dataframe(df)

    _df_cache = df
    _audit_cache = report
    return df, report


def get_races(df: pd.DataFrame) -> list:
    """Return race names sorted chronologically by RaceRound."""
    if "RaceRound" in df.columns:
        mapping = (
            df[["Race", "RaceRound"]].drop_duplicates()
            .dropna(subset=["Race"])
            .sort_values("RaceRound")
        )
        return mapping["Race"].tolist()
    return sorted(df["Race"].dropna().unique().tolist())


def get_drivers(df: pd.DataFrame, race: Optional[str] = None) -> list:
    """Return sorted list of driver abbreviations, optionally filtered by race."""
    sub = df if race is None else df[df["Race"] == race]
    return sorted(sub["Driver"].dropna().unique().tolist())


def get_teams(df: pd.DataFrame, race: Optional[str] = None) -> list:
    """Return sorted list of team names, optionally filtered by race."""
    sub = df if race is None else df[df["Race"] == race]
    return sorted(sub["Team"].dropna().unique().tolist())


def filter_race(df: pd.DataFrame, race: str) -> pd.DataFrame:
    """Return rows for a single race, sorted by Driver then LapNumber."""
    return df[df["Race"] == race].sort_values(["Driver", "LapNumber"]).reset_index(drop=True)


def filter_driver(df: pd.DataFrame, driver: str, race: Optional[str] = None) -> pd.DataFrame:
    """Return rows for a single driver, optionally within a race."""
    sub = df if race is None else df[df["Race"] == race]
    return sub[sub["Driver"] == driver].sort_values("LapNumber").reset_index(drop=True)


def filter_valid_laps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows where LapTime is NaN or outside the valid range.
    Does NOT modify df in-place.
    """
    from config import MIN_LAP_TIME_SEC, MAX_LAP_TIME_SEC
    return df[
        df["LapTime"].notna()
        & (df["LapTime"] >= MIN_LAP_TIME_SEC)
        & (df["LapTime"] <= MAX_LAP_TIME_SEC)
    ].copy()
