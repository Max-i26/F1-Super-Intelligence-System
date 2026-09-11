"""
src/ui/components.py — Reusable UI Components
==============================================
Shared components used across all dashboard pages.
"""

import streamlit as st
import pandas as pd
from typing import Optional, List, Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import (
    THEME_GOLD, THEME_GOLD_LIGHT, THEME_WHITE, THEME_GREY,
    THEME_RED, THEME_GREEN, THEME_ORANGE,
    THEME_BG_PRIMARY, THEME_BG_SECONDARY, THEME_BG_CARD, THEME_BG_PANEL
)
from src.ui.theme import card, badge, severity_color


def kpi_row(metrics: List[Dict[str, Any]]) -> None:
    """
    Render a row of KPI metric cards.
    Each dict: {"label": str, "value": str/int/float, "delta": optional str, "help": optional str}
    """
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            st.metric(
                label=m.get("label", ""),
                value=m.get("value", "—"),
                delta=m.get("delta"),
                help=m.get("help"),
            )


def data_health_badge(audit_report) -> None:
    """
    Show a compact data health indicator based on audit report.
    """
    if audit_report is None:
        st.warning("⚠ No audit report available.")
        return

    crit = audit_report.critical_count()
    warn = audit_report.warning_count()

    if crit > 0:
        color, icon, label = THEME_RED, "🔴", f"DATA CRITICAL ({crit} issues)"
    elif warn > 0:
        color, icon, label = THEME_ORANGE, "🟡", f"DATA WARNINGS ({warn})"
    else:
        color, icon, label = THEME_GREEN, "🟢", "DATA HEALTHY"

    st.markdown(
        f"<span style='color:{color}; font-size:0.8rem; font-weight:600; "
        f"letter-spacing:0.08em;'>{icon} {label}</span>",
        unsafe_allow_html=True,
    )


def audit_table(audit_report) -> None:
    """Render the full audit findings as a styled table."""
    if audit_report is None:
        return
    df = audit_report.to_dataframe()
    if len(df) == 0:
        st.success("No audit findings.")
        return

    def row_style(row):
        if row["Severity"] == "CRITICAL":
            return [f"background-color: rgba(232,0,45,0.12)"] * len(row)
        elif row["Severity"] == "WARNING":
            return [f"background-color: rgba(255,107,0,0.10)"] * len(row)
        return [""] * len(row)

    styled = df.style.apply(row_style, axis=1)
    st.dataframe(styled, use_container_width=True, hide_index=True)


def race_selector(races: List[str], label: str = "Select Race") -> str:
    """Sidebar race selector. Returns selected race name."""
    return st.sidebar.selectbox(label, races)


def driver_selector(drivers: List[str], label: str = "Select Driver", multi: bool = False):
    """Sidebar driver selector. Returns selected driver(s)."""
    if multi:
        return st.sidebar.multiselect(label, drivers, default=drivers[:2] if len(drivers) >= 2 else drivers)
    return st.sidebar.selectbox(label, drivers)


def section_header(title: str, subtitle: str = "", icon: str = "") -> None:
    """Render a section header with optional icon and subtitle."""
    icon_str = f"{icon} " if icon else ""
    st.markdown(f"### {icon_str}{title}")
    if subtitle:
        st.markdown(f"<p style='color:{THEME_GREY}; font-size:0.82rem; margin-top:-0.5rem;'>{subtitle}</p>",
                    unsafe_allow_html=True)


def official_vs_analytical_banner() -> None:
    """Show the important disclaimer separating official from analytical data."""
    st.markdown(
        f"""
        <div style='background:rgba(212,175,55,0.07); border:1px solid rgba(212,175,55,0.3);
                    border-radius:8px; padding:0.7rem 1rem; margin-bottom:1rem;
                    font-size:0.78rem; color:{THEME_GREY};'>
        ⚡ <b style='color:{THEME_GOLD};'>Official</b> championship data comes from validated FIA/OpenF1 sources.
        &nbsp;&nbsp;|&nbsp;&nbsp;
        📊 <b style='color:#44AAFF;'>Analytical</b> scores are computed from race/lap data and are
        <b>not</b> equivalent to official championship points.
        </div>
        """,
        unsafe_allow_html=True,
    )


def no_data_message(context: str = "") -> None:
    """Show a consistent 'no data' placeholder."""
    msg = f"No data available{' for ' + context if context else ''}."
    st.markdown(
        f"<div style='color:{THEME_GREY}; text-align:center; padding:2rem; "
        f"border:1px solid #2a2a2a; border-radius:8px;'>📭 {msg}</div>",
        unsafe_allow_html=True,
    )


def openf1_status_banner(is_available: bool) -> None:
    """Show OpenF1 API availability status."""
    if is_available:
        st.markdown(
            f"<span style='color:{THEME_GREEN}; font-size:0.75rem;'>🟢 OpenF1 API — Connected</span>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<span style='color:{THEME_ORANGE}; font-size:0.75rem;'>"
            f"🟡 OpenF1 API — Unavailable. Local historical analysis remains active.</span>",
            unsafe_allow_html=True,
        )


def compound_legend() -> None:
    """Render a tyre compound colour legend."""
    from config import COMPOUND_COLORS
    legend_html = " &nbsp; ".join([
        f"<span style='color:{color}; font-size:0.78rem; font-weight:600;'>⬤ {c}</span>"
        for c, color in COMPOUND_COLORS.items() if c != "UNKNOWN"
    ])
    st.markdown(legend_html, unsafe_allow_html=True)
