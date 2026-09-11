"""
src/data/openf1.py — OpenF1 API Client for F1 Super Intelligence
=================================================================
Resilient API client with:
  - Timeout
  - Retry with exponential backoff
  - Rate-limit awareness
  - File-based caching (TTL-based)
  - Clean error handling
  - Never crashes the dashboard if API is unavailable

Offline-first: local analysis works without this module.
"""

import time
import requests
from typing import Optional, List, Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import (
    OPENF1_BASE_URL,
    OPENF1_TIMEOUT_SEC,
    OPENF1_MAX_RETRIES,
    OPENF1_RETRY_DELAY_SEC,
    OPENF1_CACHE_TTL_SEC,
    SEASON_YEAR,
)
from src.utils.caching import cache_get, cache_set
from src.utils.logging import get_logger

logger = get_logger(__name__)


class OpenF1Client:
    """
    HTTP client for the OpenF1 REST API.

    Usage:
        client = OpenF1Client()
        sessions = client.get_sessions(year=2025)
        laps = client.get_laps(session_key=1234, driver_number=4)
    """

    def __init__(
        self,
        base_url: str = OPENF1_BASE_URL,
        timeout: int = OPENF1_TIMEOUT_SEC,
        max_retries: int = OPENF1_MAX_RETRIES,
        retry_delay: float = OPENF1_RETRY_DELAY_SEC,
        cache_ttl: int = OPENF1_CACHE_TTL_SEC,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.cache_ttl = cache_ttl
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})

    def _get(self, endpoint: str, params: Dict[str, Any]) -> Optional[List[Dict]]:
        """
        Make a GET request to OpenF1 with retry and caching.
        Returns parsed JSON (list of dicts) or None on failure.
        """
        # Build cache key from URL + sorted params
        cache_key = f"openf1:{endpoint}:{sorted(params.items())}"
        cached = cache_get(cache_key, self.cache_ttl)
        if cached is not None:
            return cached

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"OpenF1 GET {url} params={params} (attempt {attempt})")
                resp = self._session.get(url, params=params, timeout=self.timeout)

                if resp.status_code == 200:
                    data = resp.json()
                    cache_set(cache_key, data)
                    logger.info(f"OpenF1 OK: {len(data)} records from {endpoint}")
                    return data

                elif resp.status_code == 429:
                    logger.warning(f"OpenF1 rate-limited. Waiting {self.retry_delay * attempt}s...")
                    time.sleep(self.retry_delay * attempt)

                elif resp.status_code in (500, 502, 503, 504):
                    logger.warning(f"OpenF1 server error {resp.status_code}. Retrying...")
                    time.sleep(self.retry_delay * attempt)

                else:
                    logger.error(f"OpenF1 unexpected status {resp.status_code} for {url}")
                    return None

            except requests.Timeout:
                logger.warning(f"OpenF1 timeout (attempt {attempt}) for {url}")
                time.sleep(self.retry_delay)
            except requests.ConnectionError:
                logger.warning(f"OpenF1 connection error (attempt {attempt}) for {url}")
                time.sleep(self.retry_delay)
            except Exception as e:
                logger.error(f"OpenF1 unexpected error: {e}")
                return None

        logger.error(f"OpenF1 all {self.max_retries} attempts failed for {url}")
        return None

    # ─────────────────────────────────────────────────────────
    # Sessions
    # ─────────────────────────────────────────────────────────
    def get_sessions(self, year: int = SEASON_YEAR) -> Optional[List[Dict]]:
        """Get all sessions for a given year."""
        return self._get("sessions", {"year": year})

    def get_session_key(self, year: int, circuit_short_name: str, session_name: str = "Race") -> Optional[int]:
        """Find a session key for a specific circuit and session type."""
        sessions = self.get_sessions(year)
        if not sessions:
            return None
        for s in sessions:
            if (
                s.get("year") == year
                and s.get("session_name", "").lower() == session_name.lower()
                and circuit_short_name.lower() in s.get("circuit_short_name", "").lower()
            ):
                return s.get("session_key")
        return None

    # ─────────────────────────────────────────────────────────
    # Laps
    # ─────────────────────────────────────────────────────────
    def get_laps(self, session_key: int, driver_number: Optional[int] = None) -> Optional[List[Dict]]:
        """Get lap data for a session, optionally filtered by driver number."""
        params = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        return self._get("laps", params)

    # ─────────────────────────────────────────────────────────
    # Car Telemetry
    # ─────────────────────────────────────────────────────────
    def get_car_data(self, session_key: int, driver_number: int) -> Optional[List[Dict]]:
        """Get car telemetry (speed, throttle, brake, RPM, gear) for a driver."""
        return self._get("car_data", {"session_key": session_key, "driver_number": driver_number})

    # ─────────────────────────────────────────────────────────
    # Position
    # ─────────────────────────────────────────────────────────
    def get_position(self, session_key: int, driver_number: Optional[int] = None) -> Optional[List[Dict]]:
        """Get position data for a session."""
        params = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        return self._get("position", params)

    # ─────────────────────────────────────────────────────────
    # Stints
    # ─────────────────────────────────────────────────────────
    def get_stints(self, session_key: int, driver_number: Optional[int] = None) -> Optional[List[Dict]]:
        """Get stint data (compound, lap start/end) for a session."""
        params = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        return self._get("stints", params)

    # ─────────────────────────────────────────────────────────
    # Pit Stops
    # ─────────────────────────────────────────────────────────
    def get_pit_stops(self, session_key: int) -> Optional[List[Dict]]:
        """Get pit stop data for a session."""
        return self._get("pit", {"session_key": session_key})

    # ─────────────────────────────────────────────────────────
    # Weather
    # ─────────────────────────────────────────────────────────
    def get_weather(self, session_key: int) -> Optional[List[Dict]]:
        """Get weather data for a session."""
        return self._get("weather", {"session_key": session_key})

    # ─────────────────────────────────────────────────────────
    # Race Control
    # ─────────────────────────────────────────────────────────
    def get_race_control(self, session_key: int) -> Optional[List[Dict]]:
        """Get race control events (flags, SC, VSC, incidents)."""
        return self._get("race_control", {"session_key": session_key})

    # ─────────────────────────────────────────────────────────
    # Drivers
    # ─────────────────────────────────────────────────────────
    def get_drivers(self, session_key: int) -> Optional[List[Dict]]:
        """Get driver information for a session."""
        return self._get("drivers", {"session_key": session_key})

    # ─────────────────────────────────────────────────────────
    # Championship
    # ─────────────────────────────────────────────────────────
    def get_championship_drivers(self, year: int = SEASON_YEAR) -> Optional[List[Dict]]:
        """Get driver championship standings for a year."""
        return self._get("championship_drivers", {"year": year})

    def get_championship_teams(self, year: int = SEASON_YEAR) -> Optional[List[Dict]]:
        """Get constructor/team championship standings for a year."""
        return self._get("championship_teams", {"year": year})

    # ─────────────────────────────────────────────────────────
    # Intervals (gaps between drivers)
    # ─────────────────────────────────────────────────────────
    def get_intervals(self, session_key: int) -> Optional[List[Dict]]:
        """Get time intervals/gaps between drivers."""
        return self._get("intervals", {"session_key": session_key})

    def is_available(self) -> bool:
        """Quick connectivity check. Returns True if OpenF1 is reachable."""
        try:
            resp = self._session.get(
                f"{self.base_url}/sessions",
                params={"year": SEASON_YEAR, "session_name": "Race"},
                timeout=5,
            )
            return resp.status_code == 200
        except Exception:
            return False


# Module-level singleton
_client: Optional[OpenF1Client] = None


def get_client() -> OpenF1Client:
    """Return the module-level OpenF1Client singleton."""
    global _client
    if _client is None:
        _client = OpenF1Client()
    return _client
