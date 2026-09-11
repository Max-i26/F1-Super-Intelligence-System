"""
tests/test_race_metrics.py — Race Intelligence Tests
"""
import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def make_race_df():
    return pd.DataFrame({
        "Driver": ["NOR", "VER", "PIA"] * 10,
        "Team": ["McLaren", "Red Bull", "McLaren"] * 10,
        "LapNumber": sorted(list(range(1, 11)) * 3),
        "LapTime": [90.0, 90.5, 91.2] * 10,
        "Compound": ["SOFT"] * 15 + ["MEDIUM"] * 15,
        "Stint": [1] * 15 + [2] * 15,
        "Position": [1, 2, 3] * 10,
        "Race": ["Bahrain"] * 30,
        "Year": [2025] * 30,
        "RaceRound": [4] * 30,
    })


def test_race_summary_computes():
    from src.intelligence.race import compute_race_summary
    df = make_race_df()
    summary = compute_race_summary(df, "Bahrain")
    assert summary["race"] == "Bahrain"
    assert summary["num_drivers"] == 3
    assert summary["fastest_lap_time"] is not None
    assert summary["fastest_lap_driver"] == "NOR"


def test_race_summary_winner():
    from src.intelligence.race import compute_race_summary
    df = make_race_df()
    summary = compute_race_summary(df, "Bahrain")
    assert summary.get("winner") == "NOR"
    assert len(summary.get("podium", [])) == 3


def test_driver_race_metrics():
    from src.intelligence.race import compute_driver_race_metrics
    df = make_race_df()
    m = compute_driver_race_metrics(df, "NOR", "Bahrain")
    assert m["driver"] == "NOR"
    assert m["race"] == "Bahrain"
    assert m["best_lap"] is not None
    assert m["best_lap"] <= 90.1
    assert m["status"] == "FIN"


def test_compute_race_teammate_battles():
    from src.intelligence.race import compute_race_teammate_battles
    df = make_race_df()
    tm_df = compute_race_teammate_battles(df)
    assert not tm_df.empty
    assert "McLaren" in tm_df["team"].values
    mcl_row = tm_df[tm_df["team"] == "McLaren"].iloc[0]
    assert mcl_row["driver_1"] in ["NOR", "PIA"]
    assert mcl_row["driver_2"] in ["NOR", "PIA"]
    assert mcl_row["pace_delta"] is not None


def test_build_race_intelligence():
    from src.intelligence.race import build_race_intelligence
    df = make_race_df()
    result = build_race_intelligence(df)
    assert len(result) == 1
    assert "race" in result.columns
    assert "fastest_lap_driver" in result.columns


def test_build_driver_race_metrics_all():
    from src.intelligence.race import build_driver_race_metrics
    df = make_race_df()
    result = build_driver_race_metrics(df)
    assert len(result) == 3  # 3 drivers × 1 race
    assert set(result["driver"].unique()) == {"NOR", "VER", "PIA"}


def test_generate_race_debrief():
    from src.intelligence.race import generate_race_debrief
    df = make_race_df()
    debrief = generate_race_debrief(df, "Bahrain")
    assert "Bahrain Grand Prix Debrief" in debrief
    assert "Race Victory" in debrief
    assert "Podium Classification" in debrief

