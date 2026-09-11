"""
tests/test_simulation.py — Unit Tests for Monte Carlo Race Simulator
====================================================================
"""

import pytest
import pandas as pd
import numpy as np

from src.intelligence.simulation import run_monte_carlo_race_simulation
from src.ui.charts import race_simulation_probability_chart


@pytest.fixture
def mock_sim_race_df():
    records = []
    drivers = ["NOR", "VER", "PIA", "LEC"]
    teams = {"NOR": "McLaren", "VER": "Red Bull", "PIA": "McLaren", "LEC": "Ferrari"}

    for lap in range(1, 25):
        for pos, driver in enumerate(drivers, 1):
            # NOR is fastest (84.0s), LEC is slowest (85.5s)
            pace = 84.0 + pos * 0.4 + np.random.normal(0, 0.1)
            records.append({
                "Race": "Silverstone",
                "LapNumber": lap,
                "Driver": driver,
                "Team": teams[driver],
                "LapTime": pace,
                "Position": pos,
                "Stint": 1 if lap < 12 else 2,
                "Compound": "MEDIUM",
            })
    return pd.DataFrame(records)


def test_run_monte_carlo_race_simulation(mock_sim_race_df):
    sim_df = run_monte_carlo_race_simulation(mock_sim_race_df, "Silverstone", n_simulations=200, seed=42)
    assert not sim_df.empty
    assert len(sim_df) == 4
    assert "win_probability_pct" in sim_df.columns
    assert "podium_probability_pct" in sim_df.columns
    assert "points_probability_pct" in sim_df.columns
    assert "expected_finish_pos" in sim_df.columns

    # Fastest driver on P1 grid (NOR) should have the highest win probability
    assert sim_df.iloc[0]["driver"] == "NOR"
    assert sim_df.iloc[0]["win_probability_pct"] > 0.0

    # Total win probabilities sum to ~100%
    assert 95.0 <= sim_df["win_probability_pct"].sum() <= 105.0


def test_race_simulation_probability_chart(mock_sim_race_df):
    sim_df = run_monte_carlo_race_simulation(mock_sim_race_df, "Silverstone", n_simulations=50, seed=1)
    fig = race_simulation_probability_chart(sim_df, "Silverstone")
    assert fig is not None

