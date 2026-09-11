"""
src/utils/logging.py — Centralized Logging for F1 Super Intelligence
=====================================================================
All modules import get_logger() from here.
"""

import logging
import sys
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

_FORMATTER = logging.Formatter(
    "[%(asctime)s] [%(levelname)-8s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a named logger that writes to console and a log file."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # Already configured

    logger.setLevel(level)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(_FORMATTER)
    logger.addHandler(ch)

    # File handler
    fh = logging.FileHandler(LOG_DIR / "f1_intelligence.log", encoding="utf-8")
    fh.setFormatter(_FORMATTER)
    logger.addHandler(fh)

    logger.propagate = False
    return logger
