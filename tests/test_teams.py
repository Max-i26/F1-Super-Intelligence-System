"""
tests/test_teams.py — Unit Tests for Constructor Intelligence Engine (Phase 8)
==============================================================================
"""

import pytest
import pandas as pd
import numpy as np

from src.intelligence.teams import (
    compute_team_season_trajectory,
    compute_team_driver_contributions,
    compute_team_pit_stop_efficiency,
)


@pytest.fixture
def mock_teams_df():
    """Generates multi-race team dataset."""
    records = []
    races = ["Australia", "China", "Japan"]
    drivers_by_team = {
        "McLaren": ["NOR", "PIA"],
        "Red Bull": ["VER", "TSU"],
    }

    for race in races:
        for team, drivers in drivers_by_team.items():
            for d_idx, driver in enumerate(drivers):
                for lap in range(1, 15):
                    # McLaren is faster by 0.5s than Red Bull
                    base_pace = 84.0 if team == "McLaren" else 84.5
                    lap_time = base_pace + d_idx * 0.2 + np.random.normal(0, 0.05)
                    stint = 1 if lap < 8 else 2

                    records.append({
                        "Race": race,
                        "LapNumber": lap,
                        "Driver": driver,
                        "Team": team,
                        "LapTime": lap_time,
                        "Position": 1,
                        "Stint": stint,
                        "Compound": "MEDIUM",
                    })
    return pd.DataFrame(records)


def test_compute_team_season_trajectory(mock_teams_df):
    traj = compute_team_season_trajectory(mock_teams_df)
    assert not traj.empty
    assert "team" in traj.columns
    assert "pace_delta_to_median" in traj.columns
    assert len(traj) == 6  # 2 teams x 3 races

    # McLaren should have negative pace delta to median (faster)
    mclaren_traj = traj[traj["team"] == "McLaren"]
    assert (mclaren_traj["pace_delta_to_median"] < 0).all()


def test_compute_team_driver_contributions(mock_teams_df):
    contrib = compute_team_driver_contributions(mock_teams_df)
    assert not contrib.empty
    assert len(contrib) == 2  # 2 teams
    assert "driver_1" in contrib.columns
    assert "driver_2" in contrib.columns
    assert "pace_delta_s" in contrib.columns
    assert "faster_driver" in contrib.columns


def test_compute_team_pit_stop_efficiency(mock_teams_df):
    pit_eff = compute_team_pit_stop_efficiency(mock_teams_df)
    assert not pit_eff.empty
    assert "avg_pit_stops_per_race" in pit_eff.columns
    assert "one_stop_pct" in pit_eff.columns
    assert (pit_eff["one_stop_pct"] == 100.0).all()

