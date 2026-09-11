"""
tests/test_championship.py — Championship Truth Layer Tests
============================================================
CRITICAL: These tests ensure official standings are NEVER
derived from analytical scores.
"""
import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_champion_is_norris():
    from config import CHAMPION_2025
    assert CHAMPION_2025 == "NOR", "2025 champion must be Lando Norris (NOR)"


def test_official_standings_load():
    from src.intelligence.championship import get_official_driver_standings
    standings = get_official_driver_standings(use_api=False)
    assert len(standings) > 0
    assert "driver" in standings.columns
    assert "rank" in standings.columns
    assert "points" in standings.columns


def test_top3_standings():
    from src.intelligence.championship import get_official_driver_standings
    standings = get_official_driver_standings(use_api=False)
    assert standings[standings["driver"] == "NOR"].iloc[0]["rank"] == 1
    assert standings[standings["driver"] == "VER"].iloc[0]["rank"] == 2
    assert standings[standings["driver"] == "PIA"].iloc[0]["rank"] == 3


def test_validation_passes():
    from src.intelligence.championship import get_official_driver_standings, validate_standings
    standings = get_official_driver_standings(use_api=False)
    result = validate_standings(standings)
    assert result["passed"], f"Validation failed: {result['issues']}"


def test_norris_most_points():
    from src.intelligence.championship import get_official_driver_standings
    standings = get_official_driver_standings(use_api=False)
    max_pts_driver = standings.sort_values("points", ascending=False).iloc[0]["driver"]
    assert max_pts_driver == "NOR", "NOR must have the most points"


def test_constructor_standings_load():
    from src.intelligence.championship import get_official_constructor_standings
    constructors = get_official_constructor_standings(use_api=False)
    assert len(constructors) > 0
    assert "team" in constructors.columns
    assert "points" in constructors.columns


def test_championship_progression_not_official():
    """Ensure championship progression is clearly marked as estimate, not official."""
    import pandas as pd
    from src.intelligence.championship import build_championship_progression

    df = pd.DataFrame({
        "Driver": ["NOR", "VER", "NOR", "VER"],
        "Team": ["McLaren", "Red Bull", "McLaren", "Red Bull"],
        "LapNumber": [1.0, 1.0, 70.0, 70.0],
        "LapTime": [90.0, 90.5, 90.1, 90.6],
        "Compound": ["SOFT", "SOFT", "HARD", "HARD"],
        "Stint": [1.0, 1.0, 2.0, 2.0],
        "Position": [1.0, 2.0, 1.0, 2.0],
        "Race": ["Bahrain", "Bahrain", "Bahrain", "Bahrain"],
        "Year": [2025, 2025, 2025, 2025],
        "RaceRound": [4, 4, 4, 4],
    })

    prog = build_championship_progression(df)
    # Ensure is_official is always False for estimated progression
    assert "is_official" in prog.columns
    assert (prog["is_official"] == False).all(), "Progression estimates must be marked is_official=False"
