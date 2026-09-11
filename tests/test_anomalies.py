"""
tests/test_anomalies.py — Unit Tests for Anomaly Detection Engine (Phase 7)
===========================================================================
"""

import pytest
import pandas as pd
import numpy as np

from src.intelligence.anomalies import (
    detect_lap_time_anomalies,
    detect_race_pace_collapses,
    compile_all_anomalies,
)


@pytest.fixture
def mock_anomaly_df():
    """Generates a dataset with normal laps and one intentional pace outlier."""
    records = []
    # 15 clean laps around 85.0s
    for lap in range(1, 16):
        lap_time = 85.0 + np.random.normal(0, 0.2)
        # Lap 8 is an extreme outlier +6s
        if lap == 8:
            lap_time = 91.5

        records.append({
            "Race": "Australia",
            "LapNumber": lap,
            "Driver": "NOR",
            "Team": "McLaren",
            "LapTime": lap_time,
            "Position": 1,
            "Stint": 1,
            "Compound": "MEDIUM",
        })
    return pd.DataFrame(records)


def test_detect_lap_time_anomalies(mock_anomaly_df):
    anomalies = detect_lap_time_anomalies(mock_anomaly_df, driver="NOR")
    assert len(anomalies) >= 1

    outlier_laps = [a["lap"] for a in anomalies]
    assert 8 in outlier_laps

    anom = next(a for a in anomalies if a["lap"] == 8)
    assert anom["z_score"] > 2.2
    assert "evidence" in anom


def test_detect_race_pace_collapses():
    # Build 10 laps where laps 7-9 collapse by +4s
    records = []
    for lap in range(1, 11):
        lap_time = 85.0 if lap < 7 else 89.5
        records.append({
            "Race": "Monaco",
            "LapNumber": lap,
            "Driver": "VER",
            "Team": "Red Bull",
            "LapTime": lap_time,
            "Position": 1,
            "Stint": 1,
            "Compound": "HARD",
        })
    df = pd.DataFrame(records)
    collapses = detect_race_pace_collapses(df)
    assert len(collapses) >= 1
    assert collapses[0]["driver"] == "VER"
    assert collapses[0]["type"] == "PACE COLLAPSE"


def test_compile_all_anomalies(mock_anomaly_df):
    df_all = compile_all_anomalies(mock_anomaly_df)
    assert not df_all.empty
    assert "severity" in df_all.columns
    assert "z_score" in df_all.columns
    assert "evidence" in df_all.columns

