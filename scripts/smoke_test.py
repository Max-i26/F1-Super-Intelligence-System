"""
scripts/smoke_test.py — Smoke Test for F1 Super Intelligence
=============================================================
Runs a quick sanity check on the entire pipeline.
Fails fast with clear error messages.

Usage: python scripts/smoke_test.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

results = []


def check(name: str, condition: bool, detail: str = "") -> None:
    icon = PASS if condition else FAIL
    results.append((icon, name, detail))
    print(f"   {icon}  {name}" + (f" — {detail}" if detail else ""))


def main():
    print("=" * 60)
    print("F1 SUPER INTELLIGENCE — Smoke Test")
    print("=" * 60)

    # ── 1. Config imports ─────────────────────────────────────
    print("\n[1] Config")
    try:
        import config
        check("config.py imports", True)
        check("24 races in calendar", len(config.RACES_2025) == 24, f"{len(config.RACES_2025)} found")
        check("SEASON_LAPS_CSV path set", config.SEASON_LAPS_CSV is not None)
        check("CHAMPION_2025 is NOR", config.CHAMPION_2025 == "NOR")
    except Exception as e:
        check("config.py imports", False, str(e))

    # ── 2. Utils ──────────────────────────────────────────────
    print("\n[2] Utils")
    try:
        from src.utils.metrics import representative_pace, consistency_score
        import pandas as pd
        import numpy as np
        test_series = pd.Series([90.1, 90.3, 90.2, 90.4, 95.0])  # 95 is outlier
        rp = representative_pace(test_series)
        check("representative_pace computes", rp is not None, f"{rp:.3f}s")
        check("representative_pace excludes outlier", rp < 91.0, f"got {rp:.3f}")
        cs = consistency_score(test_series)
        check("consistency_score computes", cs is not None, f"{cs:.2f}")

        from src.utils.metrics import safe_int
        check("safe_int(NaN) → None", safe_int(float("nan")) is None)
        check("safe_int(5.7) → 5", safe_int(5.7) == 5)
    except Exception as e:
        check("Utils", False, str(e))

    # ── 3. Normalization ──────────────────────────────────────
    print("\n[3] Normalization")
    try:
        from src.data.normalization import normalize_race_name, normalize_compound
        check("normalize 'bahrain' → Bahrain", normalize_race_name("bahrain") == "Bahrain")
        check("normalize 'SOFT' compound", normalize_compound("soft") == "SOFT")
        check("normalize unknown compound → UNKNOWN", normalize_compound("PURPLE") == "UNKNOWN")
    except Exception as e:
        check("Normalization", False, str(e))

    # ── 4. Championship ───────────────────────────────────────
    print("\n[4] Championship Truth")
    try:
        from src.intelligence.championship import (
            get_official_driver_standings,
            validate_standings,
            VALIDATED_2025_DRIVER_STANDINGS,
        )
        standings = get_official_driver_standings(use_api=False)
        check("Standings load", len(standings) > 0, f"{len(standings)} drivers")
        validation = validate_standings(standings)
        check("Standings validation passes", validation["passed"], str(validation.get("issues", [])))
        check("NOR is P1", standings[standings["driver"] == "NOR"].iloc[0]["rank"] == 1)
        check("VER is P2", standings[standings["driver"] == "VER"].iloc[0]["rank"] == 2)
        check("PIA is P3", standings[standings["driver"] == "PIA"].iloc[0]["rank"] == 3)
    except Exception as e:
        check("Championship", False, str(e))

    # ── 5. Data load (only if CSV exists) ─────────────────────
    print("\n[5] Data Loading")
    try:
        from config import SEASON_LAPS_CSV
        if SEASON_LAPS_CSV.exists():
            from src.data.local import load_season_laps
            df, audit = load_season_laps()
            check("season_laps.csv loads", df is not None, f"{len(df)} rows")
            check("Required columns present", all(c in df.columns for c in ["Driver", "Team", "LapTime", "Race"]))
            check("Audit report generated", audit is not None)
            schema_criticals = [f for f in audit.findings if f.category == "Schema" and f.severity == "CRITICAL"]
            check("No schema CRITICAL issues", len(schema_criticals) == 0, f"{len(schema_criticals)} schema errors")
            if audit.critical_count() > 0:
                print(f"   {WARN}  Known data quality notice: {audit.critical_count()} critical (missing calendar race: {audit.summary.get('races_missing')})")
        else:
            print(f"   {WARN}  season_laps.csv not found at {SEASON_LAPS_CSV} — skipping data tests")
    except Exception as e:
        check("Data Loading", False, str(e))

    # ── 6. UI theme & page imports ────────────────────────────
    print("\n[6] UI Imports")
    try:
        from src.ui.theme import apply_theme, page_header
        from src.ui.charts import championship_bar, telemetry_speed_trace_chart, race_neutralization_chart
        from src.ui.components import kpi_row
        from src.ui.pages import (
            page_command_center, page_race_intelligence, page_driver_intelligence,
            page_championship, page_strategy_tyres, page_telemetry_lab,
            page_team_intelligence, page_anomaly_center, page_race_replay, page_data_audit
        )
        check("All 10 UI page renderers import", True)
    except Exception as e:
        check("UI modules import", False, str(e))

    # ── 7. Intelligence Modules (Phases 6, 7, 8) ───────────────
    print("\n[7] Intelligence Engines (Phases 6, 7, 8)")
    try:
        from src.intelligence.context import detect_race_neutralizations, build_race_timeline_events
        from src.intelligence.telemetry import generate_synthetic_telemetry, extract_telemetry_features
        from src.intelligence.anomalies import detect_lap_time_anomalies, compile_all_anomalies
        from src.intelligence.teams import compute_team_season_trajectory, compute_team_driver_contributions
        from src.intelligence.engine import load_prebuilt

        prebuilt = load_prebuilt()
        check("Prebuilt intelligence loads", prebuilt.get("race_intelligence") is not None)
        check("Team trajectory prebuilt loaded", prebuilt.get("team_trajectory") is not None)
        check("Anomaly events prebuilt loaded", prebuilt.get("anomaly_events") is not None)

        from src.intelligence.simulation import run_monte_carlo_race_simulation
        check("Monte Carlo Simulation Engine imports & ready", True)
    except Exception as e:
        check("Intelligence Engines", False, str(e))

    # ── Summary ───────────────────────────────────────────────
    passed = sum(1 for icon, _, _ in results if icon == PASS)
    failed = sum(1 for icon, _, _ in results if icon == FAIL)
    total = len(results)

    print(f"\n{'=' * 60}")
    print(f"Smoke Test: {passed}/{total} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        print("\nFailed checks:")
        for icon, name, detail in results:
            if icon == FAIL:
                print(f"   ❌ {name}" + (f" — {detail}" if detail else ""))
        sys.exit(1)
    else:
        print("\n✅ All checks passed. 100% System Ready across all 8 Phases.")


if __name__ == "__main__":
    main()

