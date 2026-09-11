"""
tests/test_strategy.py — Strategy Intelligence Tests
"""
import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def make_strategy_df():
    """Driver with a two-stop strategy: SOFT → MEDIUM → HARD"""
    laps = list(range(1, 58))
    compounds = ["SOFT"] * 20 + ["MEDIUM"] * 20 + ["HARD"] * 17
    stints = [1] * 20 + [2] * 20 + [3] * 17
    return pd.DataFrame({
        "Driver": ["NOR"] * 57,
        "Team": ["McLaren"] * 57,
        "LapNumber": laps,
        "LapTime": [90.0 + i * 0.03 for i in range(57)],
        "Compound": compounds,
        "Stint": stints,
        "Position": [1] * 57,
        "Race": ["Bahrain"] * 57,
        "Year": [2025] * 57,
        "RaceRound": [4] * 57,
    })


def test_strategy_summary_stop_count():
    from src.intelligence.strategy import build_strategy_summary
    df = make_strategy_df()
    summary = build_strategy_summary(df, "NOR", "Bahrain")
    assert summary["stop_count"] == 2
    assert summary["stint_count"] == 3
    assert summary["strategy_type"] == "Two-stop"


def test_strategy_compound_sequence():
    from src.intelligence.strategy import build_strategy_summary
    df = make_strategy_df()
    summary = build_strategy_summary(df, "NOR", "Bahrain")
    assert summary["compound_sequence"] == ["SOFT", "MEDIUM", "HARD"]


def test_strategy_stint_lengths():
    from src.intelligence.strategy import build_strategy_summary
    df = make_strategy_df()
    summary = build_strategy_summary(df, "NOR", "Bahrain")
    assert summary["stint_lengths"] == [20, 20, 17]


def test_detect_tyre_cliff():
    from src.intelligence.tyres import detect_tyre_cliff
    # Normal laps then huge drop in final 3 laps
    normal_laps = [90.0, 90.1, 90.2, 90.2, 90.3, 90.4]
    cliff_laps = [92.5, 93.2, 94.0]
    df = pd.DataFrame({
        "LapNumber": list(range(1, 10)),
        "LapTime": normal_laps + cliff_laps
    })
    has_cliff, cliff_lap = detect_tyre_cliff(df)
    assert has_cliff is True
    assert cliff_lap == 7


def test_compute_compound_degradation_matrix():
    from src.intelligence.tyres import compute_compound_degradation_matrix
    df = make_strategy_df()
    matrix = compute_compound_degradation_matrix(df)
    assert not matrix.empty
    assert "compound" in matrix.columns
    assert "avg_degradation_slope" in matrix.columns


def test_compute_undercut_battles():
    from src.intelligence.strategy import compute_undercut_overcut_battles
    # Create two drivers: D1 pits lap 15 from P2; D2 pits lap 17 from P1. D1 jumps D2.
    df = pd.DataFrame({
        "Driver": ["NOR"] * 30 + ["VER"] * 30,
        "Team": ["McLaren"] * 30 + ["Red Bull"] * 30,
        "LapNumber": list(range(1, 31)) * 2,
        "LapTime": [90.0] * 60,
        "Compound": (["MEDIUM"] * 14 + ["HARD"] * 16) + (["MEDIUM"] * 16 + ["HARD"] * 14),
        "Stint": ([1] * 14 + [2] * 16) + ([1] * 16 + [2] * 14),
        "Position": ([2] * 14 + [1] * 16) + ([1] * 16 + [2] * 14),
        "Race": ["Bahrain"] * 60,
        "Year": [2025] * 60,
    })
    battles = compute_undercut_overcut_battles(df)
    assert not battles.empty
    assert battles.iloc[0]["attacker"] == "NOR"
    assert battles.iloc[0]["defender"] == "VER"
    assert battles.iloc[0]["successful"] == True
    assert battles.iloc[0]["outcome"] == "PASSED ⚡"


def test_build_race_strategies():
    from src.intelligence.strategy import build_race_strategies
    df = make_strategy_df()
    result = build_race_strategies(df, "Bahrain")
    assert len(result) == 1
    assert result.iloc[0]["driver"] == "NOR"


def test_simulate_undercut_window():
    from src.intelligence.strategy import simulate_undercut_window
    sim = simulate_undercut_window(gap_seconds=1.5, fresh_tyre_delta_per_lap=1.2, laps_ahead=2)
    assert sim["feasible"] is True
    assert sim["undercut_margin_seconds"] == 0.90
    assert "BOX NOW" in sim["recommendation"]

    sim_fail = simulate_undercut_window(gap_seconds=3.5, fresh_tyre_delta_per_lap=1.0, laps_ahead=2)
    assert sim_fail["feasible"] is False
    assert sim_fail["undercut_margin_seconds"] < 0
    assert "STAY OUT" in sim_fail["recommendation"]

