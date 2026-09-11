"""
src/data/normalization.py — Race/Driver/Team Name Normalization
===============================================================
Ensures that raw data labels are mapped to canonical names
defined in config.py before any analysis is performed.
"""

import pandas as pd
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import (
    RACE_NAME_MAP,
    DRIVER_ABBR_MAP,
    TEAM_NAME_MAP,
    RACES_2025,
    RACE_ROUND,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


def normalize_race_name(raw: str) -> str:
    """
    Map a raw race label to the canonical 2025 calendar name.
    Case-insensitive. Returns original if no mapping found.
    """
    if pd.isna(raw):
        return "UNKNOWN"
    canonical = RACE_NAME_MAP.get(str(raw).strip().lower(), None)
    if canonical is None:
        # Try direct match with calendar
        for race in RACES_2025:
            if race.lower() == str(raw).strip().lower():
                return race
        logger.warning(f"Unknown race name: '{raw}' — keeping as-is")
        return str(raw).strip()
    return canonical


def normalize_driver(raw: str) -> str:
    """Map a raw driver label to canonical 3-letter abbreviation."""
    if pd.isna(raw):
        return "UNK"
    mapped = DRIVER_ABBR_MAP.get(str(raw).strip(), None)
    if mapped is None:
        logger.debug(f"Unknown driver abbreviation: '{raw}'")
        return str(raw).strip().upper()[:3]
    return mapped


def normalize_team(raw: str) -> str:
    """Map a raw team label to canonical team name."""
    if pd.isna(raw):
        return "UNKNOWN"
    mapped = TEAM_NAME_MAP.get(str(raw).strip().lower(), None)
    if mapped is None:
        logger.debug(f"Unknown team name: '{raw}'")
        return str(raw).strip()
    return mapped


def normalize_compound(raw: str) -> str:
    """Normalize tyre compound label to uppercase."""
    if pd.isna(raw):
        return "UNKNOWN"
    upper = str(raw).strip().upper()
    valid = ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]
    return upper if upper in valid else "UNKNOWN"


def apply_normalization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all normalizations to a season_laps DataFrame in-place.
    Adds RaceRound column.
    Returns the normalized DataFrame.
    """
    logger.info("Applying normalization to lap dataset...")
    df = df.copy()

    # Normalize Race
    df["Race"] = df["Race"].apply(normalize_race_name)

    # Normalize Driver
    df["Driver"] = df["Driver"].apply(normalize_driver)

    # Normalize Team
    df["Team"] = df["Team"].apply(normalize_team)

    # Normalize Compound
    df["Compound"] = df["Compound"].apply(normalize_compound)

    # Add RaceRound (chronological order per 2025 calendar)
    df["RaceRound"] = df["Race"].map(RACE_ROUND)

    unmapped_races = df[df["RaceRound"].isna()]["Race"].unique()
    if len(unmapped_races) > 0:
        logger.warning(f"Races not mapped to round numbers: {list(unmapped_races)}")

    logger.info(
        f"Normalization complete. "
        f"Races: {df['Race'].nunique()}, "
        f"Drivers: {df['Driver'].nunique()}, "
        f"Teams: {df['Team'].nunique()}"
    )
    return df
