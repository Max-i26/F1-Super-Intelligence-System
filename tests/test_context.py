"""
tests/test_context.py — Unit Tests for External Race Context & Race Replay (Phase 6)
=====================================================================================
"""

import pytest
import pandas as pd
import numpy as np

from src.intelligence.context import (
    detect_race_neutralizations,
    build_race_timeline_events,
    get_lap_snapshot,
    get_circuit_environmental_profile,
)


@pytest.fixture
def mock_race_df():
    """Generates a realistic 10-lap race DataFrame with SC and pit stop events."""
    records = []
    drivers = ["NOR", "VER", "PIA", "LEC"]
    teams = {"NOR": "McLaren", "VER": "Red Bull", "PIA": "McLaren", "LEC": "Ferrari"}

    for lap in range(1, 11):
        for pos, driver in enumerate(drivers, 1):
            base_time = 85.0 + pos * 0.2
            # Lap 5 is a Safety Car period (time inflation > 1.35x)
            if lap == 5:
                lap_time = base_time * 1.45
            else:
                lap_time = base_time

            # Driver NOR pits on lap 6
            stint = 1 if lap < 6 else 2
            compound = "MEDIUM" if stint == 1 else "HARD"

            records.append({
                "Race": "Australia",
                "LapNumber": lap,
                "Driver": driver,
                "Team": teams[driver],
                "LapTime": lap_time,
                "Position": pos,
                "Stint": stint,
                "Compound": compound,
            })
    return pd.DataFrame(records)


def test_detect_race_neutralizations(mock_race_df):
    neut_df = detect_race_neutralizations(mock_race_df)
    assert not neut_df.empty
    assert "status" in neut_df.columns
    assert "LapNumber" in neut_df.columns

    # Lap 1 should be START
    lap1 = neut_df[neut_df["LapNumber"] == 1]
    assert "START" in lap1["status"].iloc[0]

    # Lap 5 should be detected as SAFETY CAR
    lap5 = neut_df[neut_df["LapNumber"] == 5]
    assert "SAFETY CAR" in lap5["status"].iloc[0]


def test_build_race_timeline_events(mock_race_df):
    events = build_race_timeline_events(mock_race_df, "Australia")
    assert isinstance(events, list)
    assert len(events) >= 3

    event_types = [e["type"] for e in events]
    assert any("LIGHTS OUT" in t for t in event_types)
    assert any("SAFETY CAR" in t for t in event_types)
    assert any("CHEQUERED FLAG" in t for t in event_types)


def test_get_lap_snapshot(mock_race_df):
    snapshot = get_lap_snapshot(mock_race_df, lap_number=7)
    assert not snapshot.empty
    assert len(snapshot) == 4
    assert "Position" in snapshot.columns
    assert "Driver" in snapshot.columns
    assert "TyreAge" in snapshot.columns
    assert "Compound" in snapshot.columns

    # Check that NOR is on Stint 2 with TyreAge 2
    nor_row = snapshot[snapshot["Driver"] == "NOR"].iloc[0]
    assert nor_row["Stint"] == 2
    assert nor_row["TyreAge"] == 2
    assert nor_row["Compound"] == "HARD"


def test_get_circuit_environmental_profile():
    prof_monaco = get_circuit_environmental_profile("Monaco")
    assert "ambient_temp" in prof_monaco
    assert "track_temp" in prof_monaco
    assert "humidity" in prof_monaco
    assert "Low Speed Street" in prof_monaco["type"]

    prof_unknown = get_circuit_environmental_profile("NonExistentRace")
    assert "ambient_temp" in prof_unknown

