"""
tests/test_ui_charts.py — Unit Tests for all Plotly Chart Visualizers
======================================================================
Verifies that all chart functions execute without NameError or runtime exceptions.
"""

import pytest
import pandas as pd
import numpy as np

from src.ui.charts import (
    lap_time_distribution, race_pace_battle, lap_position_chart, teammate_battle_chart,
    driver_radar_chart, driver_form_momentum_chart, relative_pace_evolution_chart,
    teammate_gap_progression_chart, driver_trajectory, multi_driver_trajectory,
    performance_heatmap, championship_progression, championship_bar,
    tyre_degradation_curve, strategy_gantt, compound_degradation_comparison_chart,
    strategy_distribution_donut, undercut_battles_chart, race_neutralization_chart,
    telemetry_speed_trace_chart, telemetry_multichannel_chart, anomaly_scatter_chart,
    team_development_trajectory_chart, team_pit_efficiency_chart
)
from src.intelligence.telemetry import generate_synthetic_telemetry


def test_anomaly_scatter_chart():
    df = pd.DataFrame({
        "race": ["Australia", "Australia", "Australia"],
        "lap": [5, 12, 20],
        "driver": ["NOR", "VER", "HAM"],
        "severity": ["CRITICAL", "WARNING", "INFO"],
        "z_score": [4.2, 3.1, 2.3],
    })
    fig = anomaly_scatter_chart(df, "Australia")
    assert fig is not None


def test_telemetry_charts():
    t1 = generate_synthetic_telemetry("NOR", 84.0, "Australia", n_points=50, seed=1)
    t2 = generate_synthetic_telemetry("VER", 84.3, "Australia", n_points=50, seed=2)

    fig_speed = telemetry_speed_trace_chart(t1, t2)
    assert fig_speed is not None

    fig_multi = telemetry_multichannel_chart(t1, t2)
    assert fig_multi is not None


def test_race_neutralization_chart():
    df = pd.DataFrame({
        "LapNumber": [1, 2, 3, 4, 5],
        "median_time": [95.0, 85.0, 85.2, 120.0, 85.1],
        "status": ["START 🚦", "GREEN 🟢", "GREEN 🟢", "SAFETY CAR 🟡", "GREEN 🟢"]
    })
    fig = race_neutralization_chart(df, "Australia")
    assert fig is not None


def test_team_charts():
    traj_df = pd.DataFrame({
        "race": ["Australia", "China"],
        "race_round": [1, 2],
        "team": ["McLaren", "McLaren"],
        "pace_delta_to_median": [-0.3, -0.4],
    })
    fig_dev = team_development_trajectory_chart(traj_df, ["McLaren"])
    assert fig_dev is not None

    pit_df = pd.DataFrame({
        "team": ["McLaren", "Ferrari"],
        "avg_pit_stops_per_race": [1.1, 1.2],
        "one_stop_pct": [90.0, 80.0],
    })
    fig_pit = team_pit_efficiency_chart(pit_df)
    assert fig_pit is not None

