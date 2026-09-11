"""
src/ui/theme.py — Black/Gold/Dark Futuristic Theme
===================================================
All visual styling for the F1 Super Intelligence platform.
Injected as custom CSS into Streamlit.
"""

import streamlit as st

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import (
    THEME_BG_PRIMARY, THEME_BG_SECONDARY, THEME_BG_CARD, THEME_BG_PANEL,
    THEME_GOLD, THEME_GOLD_LIGHT, THEME_WHITE, THEME_GREY,
    THEME_RED, THEME_GREEN, THEME_ORANGE,
    CHART_TEMPLATE,
)

PLOTLY_LAYOUT = dict(
    template=CHART_TEMPLATE,
    paper_bgcolor=THEME_BG_CARD,
    plot_bgcolor=THEME_BG_CARD,
    font=dict(color=THEME_WHITE, family="Inter, sans-serif", size=12),
    title=dict(font=dict(color=THEME_GOLD, size=16)),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor=THEME_GREY,
        borderwidth=0,
        font=dict(color=THEME_WHITE),
    ),
    xaxis=dict(
        gridcolor="#2a2a2a",
        linecolor="#333",
        tickcolor="#555",
        zerolinecolor="#2a2a2a",
        tickfont=dict(color=THEME_GREY),
    ),
    yaxis=dict(
        gridcolor="#2a2a2a",
        linecolor="#333",
        tickcolor="#555",
        zerolinecolor="#2a2a2a",
        tickfont=dict(color=THEME_GREY),
    ),
    margin=dict(l=50, r=30, t=60, b=50),
)

CSS = f"""
<style>
/* ── Base ──────────────────────────────────────────────── */
html, body, [class*="css"] {{
    background-color: {THEME_BG_PRIMARY};
    color: {THEME_WHITE};
    font-family: 'Inter', 'Segoe UI', sans-serif;
}}

/* ── Streamlit app background ──────────────────────────── */
.stApp {{
    background-color: {THEME_BG_PRIMARY};
}}

/* ── Main block ─────────────────────────────────────────── */
.block-container {{
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}}

/* ── Sidebar ────────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    background-color: {THEME_BG_SECONDARY};
    border-right: 1px solid #2a2a2a;
}}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] .stRadio label {{
    color: {THEME_GREY} !important;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}

/* ── Headers ────────────────────────────────────────────── */
h1, h2, h3 {{
    color: {THEME_GOLD} !important;
    font-weight: 700;
    letter-spacing: 0.02em;
}}
h4, h5, h6 {{
    color: {THEME_WHITE} !important;
}}

/* ── Metric cards ───────────────────────────────────────── */
[data-testid="stMetric"] {{
    background-color: {THEME_BG_CARD};
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 1rem 1.2rem;
}}
[data-testid="stMetricLabel"] {{
    color: {THEME_GREY} !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}}
[data-testid="stMetricValue"] {{
    color: {THEME_GOLD} !important;
    font-size: 1.6rem !important;
    font-weight: 700;
}}
[data-testid="stMetricDelta"] {{
    font-size: 0.82rem !important;
}}

/* ── Selectboxes / widgets ─────────────────────────────── */
.stSelectbox select,
.stMultiSelect [data-baseweb="select"] {{
    background-color: {THEME_BG_PANEL} !important;
    border-color: #2a2a2a !important;
    color: {THEME_WHITE} !important;
}}

/* ── Buttons ────────────────────────────────────────────── */
.stButton > button {{
    background-color: {THEME_BG_PANEL};
    color: {THEME_GOLD};
    border: 1px solid {THEME_GOLD};
    border-radius: 6px;
    font-size: 0.82rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    transition: all 0.2s;
}}
.stButton > button:hover {{
    background-color: {THEME_GOLD};
    color: {THEME_BG_PRIMARY};
}}

/* ── Tabs ───────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    background-color: {THEME_BG_SECONDARY};
    border-bottom: 1px solid {THEME_GOLD};
}}
.stTabs [data-baseweb="tab"] {{
    color: {THEME_GREY};
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}
.stTabs [aria-selected="true"] {{
    color: {THEME_GOLD} !important;
    border-bottom: 2px solid {THEME_GOLD} !important;
}}

/* ── DataFrames ─────────────────────────────────────────── */
.stDataFrame {{
    background-color: {THEME_BG_CARD};
    border: 1px solid #2a2a2a;
    border-radius: 6px;
}}

/* ── Dividers ───────────────────────────────────────────── */
hr {{
    border-color: #2a2a2a !important;
}}

/* ── Custom cards ───────────────────────────────────────── */
.f1-card {{
    background-color: {THEME_BG_CARD};
    border: 1px solid #2a2a2a;
    border-left: 3px solid {THEME_GOLD};
    border-radius: 8px;
    padding: 1rem 1.4rem;
    margin-bottom: 1rem;
}}
.f1-alert-critical {{
    border-left-color: {THEME_RED} !important;
}}
.f1-alert-warning {{
    border-left-color: {THEME_ORANGE} !important;
}}
.f1-alert-ok {{
    border-left-color: {THEME_GREEN} !important;
}}

/* ── Badge ──────────────────────────────────────────────── */
.f1-badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}
.f1-badge-gold    {{ background-color: {THEME_GOLD}; color: {THEME_BG_PRIMARY}; }}
.f1-badge-red     {{ background-color: {THEME_RED}; color: white; }}
.f1-badge-green   {{ background-color: {THEME_GREEN}; color: white; }}
.f1-badge-grey    {{ background-color: #333; color: {THEME_GREY}; }}

/* ── Page header banner ─────────────────────────────────── */
.f1-header {{
    background: linear-gradient(135deg, #0d0d0d 0%, #1a1400 100%);
    border-bottom: 1px solid {THEME_GOLD};
    padding: 1.2rem 2rem;
    margin-bottom: 1.5rem;
}}
.f1-header h1 {{
    margin: 0;
    font-size: 1.6rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}}
.f1-header p {{
    margin: 0.2rem 0 0 0;
    color: {THEME_GREY};
    font-size: 0.78rem;
    letter-spacing: 0.06em;
}}

/* ── Scrollbar ──────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: {THEME_BG_PRIMARY}; }}
::-webkit-scrollbar-thumb {{ background: #333; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: {THEME_GOLD}; }}
</style>
"""


def apply_theme() -> None:
    """Inject the full F1 Super Intelligence CSS theme into the Streamlit app."""
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "") -> None:
    """Render a styled page header banner."""
    html = f"""
    <div class="f1-header">
        <h1>⚡ {title}</h1>
        {"<p>" + subtitle + "</p>" if subtitle else ""}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def card(content: str, style: str = "") -> None:
    """Render content inside a styled card div."""
    st.markdown(
        f'<div class="f1-card {style}">{content}</div>',
        unsafe_allow_html=True
    )


def badge(text: str, color: str = "gold") -> str:
    """Return an HTML badge string."""
    return f'<span class="f1-badge f1-badge-{color}">{text}</span>'


def severity_color(severity: str) -> str:
    """Map severity label to a theme color."""
    return {
        "CRITICAL": THEME_RED,
        "WARNING": THEME_ORANGE,
        "INFO": THEME_GREEN,
        "OK": THEME_GREEN,
    }.get(severity.upper(), THEME_GREY)


def plotly_layout(**overrides) -> dict:
    """Return the default Plotly layout dict, with optional overrides."""
    layout = dict(PLOTLY_LAYOUT)
    layout.update(overrides)
    return layout
