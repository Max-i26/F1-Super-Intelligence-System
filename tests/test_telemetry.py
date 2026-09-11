"""
tests/test_telemetry.py — Unit Tests for Telemetry Intelligence Engine (Phase 7)
=================================================================================
"""

import pytest
import pandas as pd
import numpy as np

from src.intelligence.telemetry import (
    generate_synthetic_telemetry,
    extract_telemetry_features,
    compare_driver_telemetry,
)


def test_generate_synthetic_telemetry():
    t_df = generate_synthetic_telemetry(
        driver="NOR",
        lap_time=84.5,
        race_name="Australia",
        n_points=150,
        seed=42,
    )
    assert not t_df.empty
    assert len(t_df) == 150
    assert "speed_kmh" in t_df.columns
    assert "throttle_pct" in t_df.columns
    assert "brake_pct" in t_df.columns
    assert "gear" in t_df.columns
    assert "rpm" in t_df.columns
    assert "distance_m" in t_df.columns

    # Speeds should be physically realistic for F1
    assert t_df["speed_kmh"].min() >= 60.0
    assert t_df["speed_kmh"].max() <= 360.0
    assert t_df["gear"].min() >= 1
    assert t_df["gear"].max() <= 8


def test_extract_telemetry_features():
    t_df = generate_synthetic_telemetry("VER", 84.0, "Australia", n_points=100, seed=1)
    feats = extract_telemetry_features(t_df)

    assert "top_speed_kmh" in feats
    assert "min_speed_kmh" in feats
    assert "avg_speed_kmh" in feats
    assert "avg_corner_speed_kmh" in feats
    assert "full_throttle_pct" in feats
    assert "heavy_brake_pct" in feats

    assert feats["top_speed_kmh"] >= feats["min_speed_kmh"]
    assert 0.0 <= feats["full_throttle_pct"] <= 100.0


def test_compare_driver_telemetry():
    t1 = generate_synthetic_telemetry("NOR", 84.0, "Australia", n_points=100, seed=1)
    t2 = generate_synthetic_telemetry("VER", 84.3, "Australia", n_points=100, seed=2)

    comp = compare_driver_telemetry(t1, t2)
    assert not comp.empty
    assert "speed_delta_kmh" in comp.columns
    assert "throttle_delta_pct" in comp.columns
    assert "brake_delta_pct" in comp.columns

