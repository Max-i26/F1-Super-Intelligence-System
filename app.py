"""
app.py — F1 Super Intelligence — Main Streamlit Application
============================================================
Run with:  streamlit run app.py
Never run with: python app.py

Architecture:
  - Loads data once on session start
  - Sidebar navigation routes to page modules
  - All computation happens in src/ — never in this file
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ui.theme import apply_theme
from src.ui.pages import (
    page_command_center,
    page_race_intelligence,
    page_driver_intelligence,
    page_championship,
    page_strategy_tyres,
    page_telemetry_lab,
    page_team_intelligence,
    page_anomaly_center,
    page_race_replay,
    page_data_audit,
)

# ─────────────────────────────────────────────────────────────
# STREAMLIT PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="F1 Super Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": "F1 Super Intelligence — 2025 Season Analytics Platform",
    },
)

# Apply global theme
apply_theme()


# ─────────────────────────────────────────────────────────────
# DATA LOADING (cached per session)
# ─────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading F1 Intelligence data...")
def load_all_data():
    """
    Load all intelligence data once per session.
    Returns a dict of DataFrames and metadata.
    """
    data = {}

    # Local lap data
    try:
        from src.data.local import load_season_laps
        df, audit = load_season_laps()
        data["df"] = df
        data["audit"] = audit
    except FileNotFoundError as e:
        data["df"] = None
        data["audit"] = None
        data["load_error"] = str(e)

    # Pre-built intelligence CSVs (fast path)
    try:
        from src.intelligence.engine import load_prebuilt
        prebuilt = load_prebuilt()
        data.update(prebuilt)
    except Exception as e:
        pass

    # Championship progression
    try:
        if data.get("df") is not None:
            from src.intelligence.championship import build_championship_progression
            data["championship_progression"] = build_championship_progression(data["df"])
    except Exception as e:
        data["championship_progression"] = None

    # OpenF1 availability
    try:
        from src.data.openf1 import get_client
        data["openf1_available"] = get_client().is_available()
    except Exception:
        data["openf1_available"] = False

    return data


# ─────────────────────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────────────────────────
PAGES = {
    "🏠 Command Center":     page_command_center,
    "🏁 Race Intelligence":  page_race_intelligence,
    "👤 Driver Intelligence": page_driver_intelligence,
    "🏆 Championship":       page_championship,
    "🔧 Strategy & Tyres":   page_strategy_tyres,
    "📡 Telemetry Lab":      page_telemetry_lab,
    "🏗️ Team Intelligence":  page_team_intelligence,
    "⚠️ Anomaly Center":     page_anomaly_center,
    "▶️ Race Replay":        page_race_replay,
    "🔍 Data Audit":         page_data_audit,
}

with st.sidebar:
    st.markdown(
        """
        <div style='text-align:center; padding:0.5rem 0 1rem 0;'>
            <div style='font-size:1.4rem; font-weight:900; color:#D4AF37;
                        letter-spacing:0.15em;'>⚡ F1 INTEL</div>
            <div style='font-size:0.65rem; color:#888; letter-spacing:0.1em;'>2025 SEASON</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    page_name = st.radio("Navigation", list(PAGES.keys()), label_visibility="collapsed")
    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.65rem; color:#666; text-align:center;'>"
        "F1 Super Intelligence<br>2025 Official Edition · Full Grid</div>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────
# RENDER SELECTED PAGE
# ─────────────────────────────────────────────────────────────
data = load_all_data()

# Show load error if any
if "load_error" in data and data["load_error"]:
    st.error(
        f"⚠ **Data Load Error:** {data['load_error']}\n\n"
        "Please ensure `data/2025/processed/season_laps.csv` exists.\n"
        "Check `config.py` → `SEASON_LAPS_CSV` path."
    )

# Render the selected page
page_fn = PAGES.get(page_name)
if page_fn:
    page_fn(data)
