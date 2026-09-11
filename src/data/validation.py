"""
src/data/validation.py — Data Quality Audit for F1 Super Intelligence
======================================================================
Runs a comprehensive audit on the season_laps DataFrame.
Every finding is surfaced — never hidden.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import (
    REQUIRED_LAP_COLUMNS,
    VALID_COMPOUNDS,
    MIN_LAP_TIME_SEC,
    MAX_LAP_TIME_SEC,
    MIN_POSITION,
    MAX_POSITION,
    MIN_LAP_NUMBER,
    MAX_LAP_NUMBER,
    MIN_STINT,
    MAX_STINT,
    RACES_2025,
    TEAMS_2025,
    SEASON_YEAR,
    TOTAL_ROUNDS,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AuditFinding:
    """A single data quality finding."""
    category: str
    severity: str       # CRITICAL / WARNING / INFO
    description: str
    count: int = 0
    detail: Any = None


@dataclass
class AuditReport:
    """Complete data quality audit report."""
    row_count: int = 0
    column_count: int = 0
    findings: List[AuditFinding] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    passed: bool = True

    def add(self, finding: AuditFinding) -> None:
        self.findings.append(finding)
        if finding.severity == "CRITICAL":
            self.passed = False

    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "CRITICAL")

    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "WARNING")

    def info_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "INFO")

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([
            {
                "Category": f.category,
                "Severity": f.severity,
                "Description": f.description,
                "Count": f.count,
            }
            for f in self.findings
        ])


def audit_dataframe(df: pd.DataFrame) -> AuditReport:
    """
    Run a full data quality audit on a season_laps DataFrame.
    Returns an AuditReport with all findings.
    """
    report = AuditReport()
    report.row_count = len(df)
    report.column_count = len(df.columns)

    logger.info(f"Starting audit: {report.row_count} rows, {report.column_count} columns")

    # ── 1. Row count ─────────────────────────────────────────
    report.summary["row_count"] = report.row_count
    report.add(AuditFinding(
        category="Structure",
        severity="INFO",
        description=f"Total rows: {report.row_count}",
        count=report.row_count,
    ))

    # ── 2. Column check ──────────────────────────────────────
    missing_cols = [c for c in REQUIRED_LAP_COLUMNS if c not in df.columns]
    if missing_cols:
        report.add(AuditFinding(
            category="Schema",
            severity="CRITICAL",
            description=f"Missing required columns: {missing_cols}",
            count=len(missing_cols),
            detail=missing_cols,
        ))
    else:
        report.add(AuditFinding(
            category="Schema",
            severity="INFO",
            description="All required columns present.",
            count=0,
        ))

    # ── 3. Duplicate rows ────────────────────────────────────
    dup_count = df.duplicated().sum()
    report.summary["duplicate_rows"] = int(dup_count)
    report.add(AuditFinding(
        category="Duplicates",
        severity="WARNING" if dup_count > 0 else "INFO",
        description=f"Duplicate rows: {dup_count}",
        count=int(dup_count),
    ))

    # ── 4. Missing values per column ─────────────────────────
    for col in REQUIRED_LAP_COLUMNS:
        if col not in df.columns:
            continue
        n_missing = int(df[col].isna().sum())
        if n_missing > 0:
            pct = n_missing / report.row_count * 100
            sev = "CRITICAL" if pct > 20 else "WARNING"
            report.add(AuditFinding(
                category="Missing Values",
                severity=sev,
                description=f"'{col}' missing: {n_missing} rows ({pct:.1f}%)",
                count=n_missing,
            ))
        report.summary[f"missing_{col}"] = n_missing

    # ── 5. Invalid lap times ─────────────────────────────────
    if "LapTime" in df.columns:
        lt = pd.to_numeric(df["LapTime"], errors="coerce")
        n_invalid = int((lt < MIN_LAP_TIME_SEC).sum() + (lt > MAX_LAP_TIME_SEC).sum())
        n_too_low = int((lt < MIN_LAP_TIME_SEC).sum())
        n_too_high = int((lt > MAX_LAP_TIME_SEC).sum())
        if n_invalid > 0:
            report.add(AuditFinding(
                category="Data Integrity",
                severity="WARNING",
                description=f"Lap times outside valid range [{MIN_LAP_TIME_SEC}–{MAX_LAP_TIME_SEC}s]: {n_invalid} (too low: {n_too_low}, too high: {n_too_high})",
                count=n_invalid,
            ))
        report.summary["invalid_lap_times"] = n_invalid

    # ── 6. Invalid positions ─────────────────────────────────
    if "Position" in df.columns:
        pos = pd.to_numeric(df["Position"], errors="coerce").dropna()
        n_bad_pos = int(((pos < MIN_POSITION) | (pos > MAX_POSITION)).sum())
        if n_bad_pos > 0:
            report.add(AuditFinding(
                category="Data Integrity",
                severity="WARNING",
                description=f"Invalid positions (outside 1–20): {n_bad_pos}",
                count=n_bad_pos,
            ))
        report.summary["invalid_positions"] = n_bad_pos

    # ── 7. Invalid lap numbers ───────────────────────────────
    if "LapNumber" in df.columns:
        ln = pd.to_numeric(df["LapNumber"], errors="coerce").dropna()
        n_bad_lap = int(((ln < MIN_LAP_NUMBER) | (ln > MAX_LAP_NUMBER)).sum())
        if n_bad_lap > 0:
            report.add(AuditFinding(
                category="Data Integrity",
                severity="WARNING",
                description=f"Invalid lap numbers (outside 1–{MAX_LAP_NUMBER}): {n_bad_lap}",
                count=n_bad_lap,
            ))

    # ── 8. Unknown tyre compounds ────────────────────────────
    if "Compound" in df.columns:
        valid_set = set(VALID_COMPOUNDS + ["UNKNOWN"])
        unknown_compounds = df["Compound"].dropna().apply(
            lambda x: str(x).strip().upper()
        )
        n_unknown = int((~unknown_compounds.isin(valid_set)).sum())
        unique_compounds = df["Compound"].unique().tolist()
        report.add(AuditFinding(
            category="Compounds",
            severity="WARNING" if n_unknown > 0 else "INFO",
            description=f"Unique compounds found: {unique_compounds}. Unknown: {n_unknown}",
            count=n_unknown,
        ))

    # ── 9. Race coverage ─────────────────────────────────────
    if "Race" in df.columns:
        found_races = set(df["Race"].dropna().unique())
        expected_races = set(RACES_2025)
        missing_races = expected_races - found_races
        extra_races = found_races - expected_races

        report.summary["races_found"] = sorted(list(found_races))
        report.summary["races_missing"] = sorted(list(missing_races))
        report.summary["race_count"] = len(found_races)

        if missing_races:
            report.add(AuditFinding(
                category="Calendar Coverage",
                severity="CRITICAL",
                description=f"Missing races from 2025 calendar: {sorted(missing_races)}",
                count=len(missing_races),
                detail=sorted(list(missing_races)),
            ))
        else:
            report.add(AuditFinding(
                category="Calendar Coverage",
                severity="INFO",
                description=f"All {TOTAL_ROUNDS} races present.",
                count=0,
            ))

        if extra_races:
            report.add(AuditFinding(
                category="Calendar Coverage",
                severity="WARNING",
                description=f"Unexpected race labels (not in 2025 calendar): {sorted(extra_races)}",
                count=len(extra_races),
                detail=sorted(list(extra_races)),
            ))

    # ── 10. Driver coverage ──────────────────────────────────
    if "Driver" in df.columns:
        drivers_found = df["Driver"].nunique()
        report.summary["driver_count"] = drivers_found
        report.add(AuditFinding(
            category="Drivers",
            severity="INFO",
            description=f"Unique drivers found: {drivers_found}",
            count=drivers_found,
        ))

    # ── 11. Team coverage ────────────────────────────────────
    if "Team" in df.columns:
        teams_found = df["Team"].dropna().unique().tolist()
        unknown_teams = [t for t in teams_found if t not in TEAMS_2025]
        report.summary["team_count"] = len(teams_found)
        if unknown_teams:
            report.add(AuditFinding(
                category="Teams",
                severity="WARNING",
                description=f"Teams not in 2025 constructor list: {unknown_teams}",
                count=len(unknown_teams),
                detail=unknown_teams,
            ))

    # ── 12. Year check ───────────────────────────────────────
    if "Year" in df.columns:
        years = df["Year"].dropna().unique().tolist()
        bad_years = [y for y in years if int(y) != SEASON_YEAR]
        if bad_years:
            report.add(AuditFinding(
                category="Data Integrity",
                severity="WARNING",
                description=f"Unexpected years in dataset: {bad_years}",
                count=len(bad_years),
                detail=bad_years,
            ))

    # ── 13. Per-race lap counts ──────────────────────────────
    if "Race" in df.columns and "LapNumber" in df.columns:
        race_laps = df.groupby("Race")["LapNumber"].count().to_dict()
        report.summary["laps_per_race"] = race_laps

    logger.info(
        f"Audit complete. "
        f"CRITICAL: {report.critical_count()}, "
        f"WARNING: {report.warning_count()}, "
        f"INFO: {report.info_count()}"
    )
    return report
