"""
scripts/audit_season.py — Data Quality Audit Script
=====================================================
Run this to get a full audit report on your season_laps.csv.
Usage: python scripts/audit_season.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.local import load_season_laps
from src.data.validation import AuditReport
from config import RACES_2025


def main():
    print("=" * 60)
    print("F1 SUPER INTELLIGENCE — Season Data Audit")
    print("=" * 60)

    try:
        df, report = load_season_laps()
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

    print(f"\n📊 DATASET OVERVIEW")
    print(f"   Rows:    {len(df):,}")
    print(f"   Columns: {len(df.columns)}")
    print(f"   Races:   {df['Race'].nunique()} / 24")
    print(f"   Drivers: {df['Driver'].nunique()}")
    print(f"   Teams:   {df['Team'].nunique()}")

    print(f"\n📋 AUDIT RESULTS")
    print(f"   🔴 CRITICAL: {report.critical_count()}")
    print(f"   🟡 WARNING:  {report.warning_count()}")
    print(f"   🟢 INFO:     {report.info_count()}")

    print("\n📝 FINDINGS:")
    for finding in report.findings:
        icon = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🟢"}.get(finding.severity, "⚪")
        print(f"   {icon} [{finding.category}] {finding.description}")
        if finding.detail and finding.severity in ("CRITICAL", "WARNING"):
            print(f"      Detail: {finding.detail}")

    # ── Calendar check ────────────────────────────────────────
    print("\n🗓️  2025 CALENDAR CHECK:")
    found = set(df["Race"].unique())
    for i, race in enumerate(RACES_2025, 1):
        status = "✅" if race in found else "❌ MISSING"
        print(f"   Round {i:>2}  {race:<20} {status}")

    # ── Missing value summary ─────────────────────────────────
    print("\n📉 MISSING VALUES:")
    for col in df.columns:
        n = df[col].isna().sum()
        if n > 0:
            pct = n / len(df) * 100
            print(f"   {col:<15} {n:>5} ({pct:.1f}%)")

    print(f"\n{'=' * 60}")
    print(f"Audit complete. Overall status: {'✅ PASS' if report.passed else '❌ ISSUES FOUND'}")
    print("=" * 60)

    # Save audit report
    from config import AUDIT_REPORT_CSV, INTELLIGENCE_DIR
    INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)
    df_report = report.to_dataframe()
    df_report.to_csv(AUDIT_REPORT_CSV, index=False)
    print(f"\nAudit report saved: {AUDIT_REPORT_CSV}")


if __name__ == "__main__":
    main()
