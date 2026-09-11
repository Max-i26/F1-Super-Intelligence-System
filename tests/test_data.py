"""
tests/test_data.py — Data Layer Tests
"""
import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def make_sample_df():
    return pd.DataFrame({
        "Driver": ["NOR", "VER", "PIA", "NOR", "VER"],
        "Team": ["McLaren", "Red Bull", "McLaren", "McLaren", "Red Bull"],
        "LapNumber": [1.0, 1.0, 1.0, 2.0, 2.0],
        "LapTime": [90.1, 90.5, 91.2, 90.2, 90.4],
        "Compound": ["SOFT", "MEDIUM", "SOFT", "SOFT", "MEDIUM"],
        "Stint": [1.0, 1.0, 1.0, 1.0, 1.0],
        "Position": [1.0, 2.0, 3.0, 1.0, 2.0],
        "Race": ["Bahrain", "Bahrain", "Bahrain", "Bahrain", "Bahrain"],
        "Year": [2025, 2025, 2025, 2025, 2025],
    })


def test_normalization_race():
    from src.data.normalization import normalize_race_name
    assert normalize_race_name("bahrain") == "Bahrain"
    assert normalize_race_name("austin") == "USA"
    assert normalize_race_name("baku") == "Azerbaijan"


def test_normalization_compound():
    from src.data.normalization import normalize_compound
    assert normalize_compound("soft") == "SOFT"
    assert normalize_compound("MEDIUM") == "MEDIUM"
    assert normalize_compound("PURPLE") == "UNKNOWN"
    assert normalize_compound(None) == "UNKNOWN"


def test_normalization_apply(monkeypatch):
    from src.data.normalization import apply_normalization
    df = make_sample_df()
    result = apply_normalization(df)
    assert "RaceRound" in result.columns
    assert result["RaceRound"].notna().all()


def test_validation_required_columns():
    from src.data.validation import audit_dataframe
    df = make_sample_df()
    report = audit_dataframe(df)
    # Should have no CRITICAL findings on a valid sample
    schema_criticals = [f for f in report.findings if f.severity == "CRITICAL" and f.category == "Schema"]
    assert len(schema_criticals) == 0


def test_validation_missing_columns():
    from src.data.validation import audit_dataframe
    df = make_sample_df().drop(columns=["LapTime"])
    report = audit_dataframe(df)
    criticals = [f for f in report.findings if f.severity == "CRITICAL"]
    assert len(criticals) > 0


def test_filter_valid_laps():
    from src.data.local import filter_valid_laps
    df = make_sample_df()
    df.loc[0, "LapTime"] = 10.0   # Too low
    df.loc[1, "LapTime"] = None   # NaN
    valid = filter_valid_laps(df)
    assert len(valid) == 3
    assert valid["LapTime"].notna().all()
    assert (valid["LapTime"] >= 60.0).all()
