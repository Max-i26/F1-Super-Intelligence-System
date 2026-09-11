"""
tests/test_driver_metrics.py — Driver Intelligence Tests
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def make_driver_df():
    """Sample multi-race driver dataset."""
    return pd.DataFrame({
        "Driver": ["NOR"] * 20 + ["VER"] * 20,
        "Team": ["McLaren"] * 20 + ["Red Bull"] * 20,
        "LapNumber": list(range(1, 21)) * 2,
        "LapTime": [90.0 + i * 0.05 for i in range(20)] + [90.5 + i * 0.04 for i in range(20)],
        "Compound": ["SOFT"] * 10 + ["HARD"] * 10 + ["SOFT"] * 10 + ["HARD"] * 10,
        "Stint": [1] * 10 + [2] * 10 + [1] * 10 + [2] * 10,
        "Position": [1] * 10 + [1] * 10 + [2] * 10 + [2] * 10,
        "Race": ["Bahrain"] * 40,
        "Year": [2025] * 40,
        "RaceRound": [4] * 40,
    })


def test_representative_pace_excludes_outlier():
    from src.utils.metrics import representative_pace
    s = pd.Series([90.1, 90.2, 90.3, 90.2, 90.1, 200.0])  # 200 = pit/SC lap
    rp = representative_pace(s)
    assert rp is not None
    assert rp < 91.0, f"Outlier not excluded: {rp}"


def test_consistency_score_range():
    from src.utils.metrics import consistency_score
    consistent = pd.Series([90.0, 90.1, 90.0, 90.1, 90.0])
    inconsistent = pd.Series([90.0, 95.0, 88.0, 93.0, 91.0])
    cs_c = consistency_score(consistent)
    cs_i = consistency_score(inconsistent)
    assert cs_c is not None
    assert cs_i is not None
    assert cs_c > cs_i, "Consistent series should score higher"
    assert 0 <= cs_c <= 100


def test_degradation_slope():
    from src.utils.metrics import degradation_slope
    laps = pd.Series([1, 2, 3, 4, 5, 6, 7, 8])
    times = pd.Series([90.0, 90.3, 90.6, 90.9, 91.2, 91.5, 91.8, 92.1])
    slope = degradation_slope(times, laps)
    assert slope is not None
    assert abs(slope - 0.3) < 0.05, f"Expected slope ~0.3, got {slope}"


def test_position_gain():
    from src.utils.metrics import position_gain
    assert position_gain(10, 5) == 5
    assert position_gain(5, 10) == -5
    assert position_gain(None, 5) is None
    assert position_gain(float("nan"), 5) is None


def test_build_driver_profile():
    from src.intelligence.driver import build_driver_profile
    df = make_driver_df()
    profile = build_driver_profile(df, "NOR")
    assert profile["driver"] == "NOR"
    assert profile["race_count"] == 1
    assert profile["total_laps"] == 20
    assert profile["team"] == "McLaren"


def test_build_driver_evolution():
    from src.intelligence.driver import build_driver_evolution
    df = make_driver_df()
    evo = build_driver_evolution(df, "NOR")
    assert len(evo) == 1
    assert "rep_pace" in evo.columns
    assert "finishing_position" in evo.columns
    assert "points_estimate" in evo.columns


def test_detect_driver_milestones():
    from src.intelligence.driver import detect_driver_milestones
    sample_evo = pd.DataFrame({
        "driver": ["NOR", "NOR"],
        "race": ["Australia", "Monaco"],
        "race_round": [1, 8],
        "starting_position": [3, 1],
        "finishing_position": [1, 1],
        "position_gain": [2, 0],
        "relative_pace_to_median": [-0.5, -0.8],
        "consistency": [95.0, 92.0]
    })
    milestones = detect_driver_milestones(sample_evo, "NOR")
    assert len(milestones) > 0
    assert any("Peak Result" in m["type"] for m in milestones)


def test_compute_driver_radar_dimensions():
    from src.intelligence.driver import compute_driver_radar_dimensions
    df = make_driver_df()
    dims = compute_driver_radar_dimensions(df, "NOR")
    assert isinstance(dims, dict)
    assert "Raw Pace" in dims
    assert "Consistency" in dims
    assert "Racecraft" in dims
    assert "Tyre Management" in dims
    assert "Finishing Rate" in dims
    for k, v in dims.items():
        assert 0.0 <= v <= 100.0, f"Dimension {k} out of range: {v}"


def test_teammate_delta_direction():
    from src.intelligence.driver import build_teammate_delta
    df = make_driver_df()
    delta_df = build_teammate_delta(df)
    if len(delta_df) > 0:
        nor_row = delta_df[(delta_df["driver"] == "NOR") & (delta_df["race"] == "Bahrain")]
        if len(nor_row) > 0:
            assert nor_row.iloc[0]["pace_delta"] < 0
