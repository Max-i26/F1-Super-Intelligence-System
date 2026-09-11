"""
config.py — Central Configuration for F1 Super Intelligence
============================================================
All constants, paths, thresholds, and mappings live here.
Never hard-code values in other modules.
"""

import os
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# PROJECT ROOT
# ─────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data" / "2025"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
INTELLIGENCE_DIR = DATA_DIR / "intelligence"
EXTERNAL_DIR = DATA_DIR / "external"
CACHE_DIR = ROOT_DIR / ".cache"

# ─────────────────────────────────────────────────────────────
# SEASON
# ─────────────────────────────────────────────────────────────
SEASON_YEAR = 2025
TOTAL_ROUNDS = 24

# Official 2025 F1 Calendar — 24 rounds in order
RACES_2025 = [
    "Australia",
    "China",
    "Japan",
    "Bahrain",
    "Saudi Arabia",
    "Miami",
    "Imola",
    "Monaco",
    "Spain",
    "Canada",
    "Austria",
    "Silverstone",
    "Belgium",
    "Hungary",
    "Netherlands",
    "Italy",
    "Azerbaijan",
    "Singapore",
    "USA",
    "Mexico",
    "Brazil",
    "Las Vegas",
    "Qatar",
    "Abu Dhabi",
]

# Round number lookup (1-indexed)
RACE_ROUND = {race: i + 1 for i, race in enumerate(RACES_2025)}

# ─────────────────────────────────────────────────────────────
# RACE NAME NORMALIZATION
# Maps raw dataset labels → canonical names in RACES_2025
# Add entries here when raw data uses different spellings.
# ─────────────────────────────────────────────────────────────
RACE_NAME_MAP = {
    # Common variants
    "australian grand prix": "Australia",
    "chinese grand prix": "China",
    "japanese grand prix": "Japan",
    "bahrain grand prix": "Bahrain",
    "saudi arabian grand prix": "Saudi Arabia",
    "saudi arabia": "Saudi Arabia",
    "miami grand prix": "Miami",
    "emilia romagna grand prix": "Imola",
    "emilia-romagna": "Imola",
    "monaco grand prix": "Monaco",
    "spanish grand prix": "Spain",
    "canadian grand prix": "Canada",
    "austrian grand prix": "Austria",
    "british grand prix": "Silverstone",
    "british": "Silverstone",
    "uk": "Silverstone",
    "belgium": "Belgium",
    "belgian grand prix": "Belgium",
    "hungarian grand prix": "Hungary",
    "dutch grand prix": "Netherlands",
    "netherlands": "Netherlands",
    "dutch": "Netherlands",
    "italian grand prix": "Italy",
    "azerbaijani grand prix": "Azerbaijan",
    "baku": "Azerbaijan",
    "singapore grand prix": "Singapore",
    "united states grand prix": "USA",
    "united states": "USA",
    "austin": "USA",
    "cota": "USA",
    "mexican grand prix": "Mexico",
    "mexico city grand prix": "Mexico",
    "brazil": "Brazil",
    "brazilian grand prix": "Brazil",
    "sao paulo grand prix": "Brazil",
    "las vegas grand prix": "Las Vegas",
    "qatar grand prix": "Qatar",
    "abu dhabi grand prix": "Abu Dhabi",
}

# ─────────────────────────────────────────────────────────────
# OFFICIAL 2025 CHAMPIONSHIP — GROUND TRUTH
# DO NOT derive this from analytical scores.
# Source: OpenF1 championship data / official FIA results.
# ─────────────────────────────────────────────────────────────
CHAMPION_2025 = "NOR"  # Lando Norris

OFFICIAL_2025_DRIVERS_STANDINGS = [
    {"rank": 1, "driver": "NOR", "full_name": "Lando Norris"},
    {"rank": 2, "driver": "VER", "full_name": "Max Verstappen"},
    {"rank": 3, "driver": "PIA", "full_name": "Oscar Piastri"},
]

# ─────────────────────────────────────────────────────────────
# DRIVERS — 2025 Grid
# ─────────────────────────────────────────────────────────────
DRIVERS_2025 = {
    "NOR": {"full_name": "Lando Norris",          "team": "McLaren",        "number": 4},
    "VER": {"full_name": "Max Verstappen",        "team": "Red Bull",       "number": 1},
    "PIA": {"full_name": "Oscar Piastri",         "team": "McLaren",        "number": 81},
    "HAM": {"full_name": "Lewis Hamilton",        "team": "Ferrari",        "number": 44},
    "LEC": {"full_name": "Charles Leclerc",       "team": "Ferrari",        "number": 16},
    "RUS": {"full_name": "George Russell",        "team": "Mercedes",       "number": 63},
    "ANT": {"full_name": "Andrea Kimi Antonelli", "team": "Mercedes",       "number": 12},
    "SAI": {"full_name": "Carlos Sainz",          "team": "Williams",       "number": 55},
    "ALO": {"full_name": "Fernando Alonso",       "team": "Aston Martin",   "number": 14},
    "STR": {"full_name": "Lance Stroll",          "team": "Aston Martin",   "number": 18},
    "GAS": {"full_name": "Pierre Gasly",          "team": "Alpine",         "number": 10},
    "DOO": {"full_name": "Jack Doohan",           "team": "Alpine",         "number": 7},
    "ALB": {"full_name": "Alexander Albon",       "team": "Williams",       "number": 23},
    "COL": {"full_name": "Franco Colapinto",      "team": "Alpine",         "number": 43},
    "TSU": {"full_name": "Yuki Tsunoda",          "team": "Red Bull",       "number": 22},
    "HAD": {"full_name": "Isack Hadjar",          "team": "Racing Bulls",   "number": 6},
    "LAW": {"full_name": "Liam Lawson",           "team": "Racing Bulls",   "number": 30},
    "HUL": {"full_name": "Nico Hulkenberg",       "team": "Sauber",         "number": 27},
    "BOR": {"full_name": "Gabriel Bortoleto",     "team": "Sauber",         "number": 5},
    "OCO": {"full_name": "Esteban Ocon",          "team": "Haas",           "number": 31},
    "BEA": {"full_name": "Oliver Bearman",        "team": "Haas",           "number": 87},
}

# Driver abbreviation normalization map (raw → canonical 3-letter code)
DRIVER_ABBR_MAP = {
    # Canonical codes (identity mapping)
    abbr: abbr for abbr in DRIVERS_2025.keys()
}
# Add common variants
DRIVER_ABBR_MAP.update({
    "Norris": "NOR", "Verstappen": "VER", "Piastri": "PIA",
    "Hamilton": "HAM", "Leclerc": "LEC", "Russell": "RUS",
    "Sainz": "SAI", "Alonso": "ALO", "Stroll": "STR",
    "Gasly": "GAS", "Doohan": "DOO", "Albon": "ALB",
    "Colapinto": "COL", "Tsunoda": "TSU", "Hadjar": "HAD",
    "Hulkenberg": "HUL", "Bortoleto": "BOR", "Ocon": "OCO",
    "Bearman": "BEA", "Antonelli": "ANT",
})

# ─────────────────────────────────────────────────────────────
# TEAMS — 2025 Constructors
# ─────────────────────────────────────────────────────────────
TEAMS_2025 = [
    "McLaren",
    "Red Bull",
    "Ferrari",
    "Mercedes",
    "Aston Martin",
    "Alpine",
    "Williams",
    "Racing Bulls",
    "Sauber",
    "Haas",
]

# Team name normalization
TEAM_NAME_MAP = {
    "mclaren": "McLaren",
    "red bull": "Red Bull",
    "red bull racing": "Red Bull",
    "ferrari": "Ferrari",
    "mercedes": "Mercedes",
    "aston martin": "Aston Martin",
    "alpine": "Alpine",
    "williams": "Williams",
    "racing bulls": "Racing Bulls",
    "rb": "Racing Bulls",
    "visa cashapp rb": "Racing Bulls",
    "sauber": "Sauber",
    "kick sauber": "Sauber",
    "haas": "Haas",
    "haas f1 team": "Haas",
}

# ─────────────────────────────────────────────────────────────
# TYRE COMPOUNDS
# ─────────────────────────────────────────────────────────────
VALID_COMPOUNDS = ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]
COMPOUND_COLORS = {
    "SOFT": "#E8002D",         # Red
    "MEDIUM": "#FFF200",       # Yellow
    "HARD": "#FFFFFF",         # White
    "INTERMEDIATE": "#39B54A", # Green
    "WET": "#0067FF",          # Blue
    "UNKNOWN": "#888888",
}

# ─────────────────────────────────────────────────────────────
# DATA QUALITY THRESHOLDS
# ─────────────────────────────────────────────────────────────
MIN_LAP_TIME_SEC = 60.0        # Minimum credible lap time (seconds)
MAX_LAP_TIME_SEC = 300.0       # Maximum credible lap time (safety car / red flag)
MIN_POSITION = 1
MAX_POSITION = 20
MIN_LAP_NUMBER = 1
MAX_LAP_NUMBER = 80
MIN_STINT = 1
MAX_STINT = 5
OUTLIER_IQR_FACTOR = 3.0      # IQR multiplier for pace outlier detection
PACE_TRIM_PERCENTILE = 5      # % trimmed from each end for trimmed mean

# ─────────────────────────────────────────────────────────────
# DATA FILE PATHS
# ─────────────────────────────────────────────────────────────
# Input
SEASON_LAPS_CSV = PROCESSED_DIR / "season_laps.csv"

# Intelligence outputs
RACE_INTELLIGENCE_CSV     = INTELLIGENCE_DIR / "race_intelligence.csv"
DRIVER_EVOLUTION_CSV      = INTELLIGENCE_DIR / "driver_evolution.csv"
DRIVER_PROFILES_CSV       = INTELLIGENCE_DIR / "driver_profiles.csv"
CHAMPIONSHIP_SNAPSHOTS_CSV = INTELLIGENCE_DIR / "championship_snapshots.csv"
TELEMETRY_FEATURES_CSV    = INTELLIGENCE_DIR / "telemetry_features.csv"
ANOMALY_EVENTS_CSV        = INTELLIGENCE_DIR / "anomaly_events.csv"

# Audit output
AUDIT_REPORT_CSV = INTELLIGENCE_DIR / "data_audit_report.csv"

# ─────────────────────────────────────────────────────────────
# OPENF1 API
# ─────────────────────────────────────────────────────────────
OPENF1_BASE_URL = "https://api.openf1.org/v1"
OPENF1_TIMEOUT_SEC = 15
OPENF1_MAX_RETRIES = 3
OPENF1_RETRY_DELAY_SEC = 2.0
OPENF1_CACHE_TTL_SEC = 3600 * 6  # 6 hours

# ─────────────────────────────────────────────────────────────
# REQUIRED DATASET COLUMNS
# ─────────────────────────────────────────────────────────────
REQUIRED_LAP_COLUMNS = [
    "Driver",
    "Team",
    "LapNumber",
    "LapTime",
    "Compound",
    "Stint",
    "Position",
    "Race",
    "Year",
]

# ─────────────────────────────────────────────────────────────
# F1 POINTS SYSTEM (standard)
# ─────────────────────────────────────────────────────────────
POINTS_FOR_POSITION = {
    1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
    6: 8,  7: 6,  8: 4,  9: 2,  10: 1,
}
FASTEST_LAP_POINT = 1  # Awarded to driver in top 10 with fastest lap

# ─────────────────────────────────────────────────────────────
# UI THEME
# ─────────────────────────────────────────────────────────────
THEME_BG_PRIMARY   = "#0A0A0A"
THEME_BG_SECONDARY = "#111111"
THEME_BG_CARD      = "#161616"
THEME_BG_PANEL     = "#1A1A1A"
THEME_GOLD         = "#D4AF37"
THEME_GOLD_LIGHT   = "#F5D060"
THEME_WHITE        = "#F0F0F0"
THEME_GREY         = "#888888"
THEME_RED          = "#E8002D"
THEME_GREEN        = "#39B54A"
THEME_ORANGE       = "#FF6B00"

# Chart defaults
CHART_HEIGHT_DEFAULT = 450
CHART_HEIGHT_TALL    = 600
CHART_HEIGHT_COMPACT = 300
CHART_TEMPLATE       = "plotly_dark"
