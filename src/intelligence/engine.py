"""
src/intelligence/engine.py — Intelligence Engine Orchestrator
=============================================================
Single entry point for all intelligence computations.
Reads from local data, runs all modules, and saves outputs.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import (
    RACE_INTELLIGENCE_CSV,
    DRIVER_EVOLUTION_CSV,
    DRIVER_PROFILES_CSV,
    ANOMALY_EVENTS_CSV,
    INTELLIGENCE_DIR,
    SEASON_YEAR,
)
from src.data.local import load_season_laps, filter_valid_laps
from src.intelligence.race import build_race_intelligence, build_driver_race_metrics
from src.intelligence.driver import build_all_driver_profiles, build_all_driver_evolution
from src.intelligence.tyres import build_tyre_intelligence
from src.intelligence.strategy import build_all_strategies
from src.intelligence.anomalies import compile_all_anomalies
from src.intelligence.teams import (
    compute_team_season_trajectory,
    compute_team_driver_contributions,
    compute_team_pit_stop_efficiency,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)

METADATA = {
    "generated_at": None,
    "source": "season_laps.csv",
    "source_version": "2025",
    "season_year": SEASON_YEAR,
}


def _save(df: pd.DataFrame, path: Path, label: str) -> None:
    """Save a DataFrame to CSV, creating parent dirs if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved {label}: {len(df)} rows → {path}")


def run_full_pipeline(force_reload: bool = False) -> Dict[str, pd.DataFrame]:
    """
    Run all intelligence modules and save outputs.

    Returns a dict of all computed DataFrames:
        {
          "race_intelligence": ...,
          "driver_race_metrics": ...,
          "driver_profiles": ...,
          "driver_evolution": ...,
          "tyre_intelligence": ...,
          "strategy_intelligence": ...,
          "team_trajectory": ...,
          "team_contributions": ...,
          "team_pit_efficiency": ...,
          "anomaly_events": ...,
        }
    """
    logger.info("=" * 60)
    logger.info("F1 SUPER INTELLIGENCE — Running Full Pipeline")
    logger.info("=" * 60)

    METADATA["generated_at"] = datetime.datetime.utcnow().isoformat()

    # ── Load data ─────────────────────────────────────────────
    df, audit = load_season_laps(force_reload=force_reload)
    logger.info(
        f"Data loaded: {len(df)} rows, {df['Race'].nunique()} races, "
        f"{df['Driver'].nunique()} drivers"
    )

    results = {}

    # ── Race Intelligence ─────────────────────────────────────
    race_intel = build_race_intelligence(df)
    driver_race = build_driver_race_metrics(df)
    _save(race_intel, RACE_INTELLIGENCE_CSV, "Race Intelligence")
    _save(driver_race, INTELLIGENCE_DIR / "driver_race_metrics.csv", "Driver Race Metrics")
    results["race_intelligence"] = race_intel
    results["driver_race_metrics"] = driver_race

    # ── Driver Profiles ───────────────────────────────────────
    driver_profiles = build_all_driver_profiles(df)
    _save(driver_profiles, DRIVER_PROFILES_CSV, "Driver Profiles")
    results["driver_profiles"] = driver_profiles

    # ── Driver Evolution ──────────────────────────────────────
    driver_evolution = build_all_driver_evolution(df)
    _save(driver_evolution, DRIVER_EVOLUTION_CSV, "Driver Evolution")
    results["driver_evolution"] = driver_evolution

    # ── Tyre Intelligence ─────────────────────────────────────
    tyre_intel = build_tyre_intelligence(df)
    tyre_path = INTELLIGENCE_DIR / "tyre_intelligence.csv"
    _save(tyre_intel, tyre_path, "Tyre Intelligence")
    results["tyre_intelligence"] = tyre_intel

    # ── Strategy Intelligence ─────────────────────────────────
    strategy_intel = build_all_strategies(df)
    strategy_path = INTELLIGENCE_DIR / "strategy_intelligence.csv"
    _save(strategy_intel, strategy_path, "Strategy Intelligence")
    results["strategy_intelligence"] = strategy_intel

    # ── Team Intelligence ─────────────────────────────────────
    team_traj = compute_team_season_trajectory(df)
    team_contrib = compute_team_driver_contributions(df)
    team_pit = compute_team_pit_stop_efficiency(df)
    _save(team_traj, INTELLIGENCE_DIR / "team_season_trajectory.csv", "Team Trajectory")
    _save(team_contrib, INTELLIGENCE_DIR / "team_driver_contributions.csv", "Team Driver Contributions")
    _save(team_pit, INTELLIGENCE_DIR / "team_pit_efficiency.csv", "Team Pit Stop Efficiency")
    results["team_trajectory"] = team_traj
    results["team_contributions"] = team_contrib
    results["team_pit_efficiency"] = team_pit

    # ── Anomaly Events ────────────────────────────────────────
    anomaly_events = compile_all_anomalies(df)
    _save(anomaly_events, ANOMALY_EVENTS_CSV, "Anomaly Events")
    results["anomaly_events"] = anomaly_events

    logger.info("=" * 60)
    logger.info("Pipeline complete.")
    logger.info("=" * 60)
    return results


def load_prebuilt() -> Dict[str, Optional[pd.DataFrame]]:
    """
    Load pre-built intelligence CSVs from disk (fast path for the dashboard).
    Returns None for any file not yet generated.
    """
    paths = {
        "race_intelligence": RACE_INTELLIGENCE_CSV,
        "driver_race_metrics": INTELLIGENCE_DIR / "driver_race_metrics.csv",
        "driver_profiles": DRIVER_PROFILES_CSV,
        "driver_evolution": DRIVER_EVOLUTION_CSV,
        "tyre_intelligence": INTELLIGENCE_DIR / "tyre_intelligence.csv",
        "strategy_intelligence": INTELLIGENCE_DIR / "strategy_intelligence.csv",
        "team_trajectory": INTELLIGENCE_DIR / "team_season_trajectory.csv",
        "team_contributions": INTELLIGENCE_DIR / "team_driver_contributions.csv",
        "team_pit_efficiency": INTELLIGENCE_DIR / "team_pit_efficiency.csv",
        "anomaly_events": ANOMALY_EVENTS_CSV,
    }
    result = {}
    for key, path in paths.items():
        if path.exists():
            result[key] = pd.read_csv(path)
            logger.info(f"Loaded prebuilt: {key} ({len(result[key])} rows)")
        else:
            result[key] = None
            logger.warning(f"Prebuilt not found: {path}")
    return result

