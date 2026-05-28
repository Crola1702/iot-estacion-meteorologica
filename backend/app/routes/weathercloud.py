import logging
import math
from datetime import timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from ..config import settings
from ..database import get_pool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weathercloud")

FIELD_MAPPING: dict[str, str] = {
    "Temp.":     "temp",
    "Hum":       "hum",
    "Pr. Aire":  "bar",
    "Precip.":   "rain",
    "Velocidad": "wspd",
    "Direcc.":   "wdir",
    "GHI":       "srad",
    "Rad.":      "uvi",
}

# Fields that WeatherCloud expects in tenths (value × 10, as integer)
_TENTH_FIELDS = {"temp", "bar", "rain", "wspd", "uvi", "dew"}

# Fields that cannot be physically negative (sensor noise can produce small negatives)
_NON_NEGATIVE_FIELDS = {"srad", "uvi", "rain", "wspd", "hum"}


def _calculate_dew_point(temp_c: float | None, hum_pct: float | None) -> float | None:
    if temp_c is None or hum_pct is None:
        return None
    if not (-40 <= temp_c <= 60) or not (0 < hum_pct <= 100):
        return None
    a, b = 17.27, 237.7
    gamma = (a * temp_c / (b + temp_c)) + math.log(hum_pct / 100.0)
    return (b * gamma) / (a - gamma)


def _reduce_pressure_to_sea_level(p_hpa: float, alt_m: float = 2640, temp_c: float = 15.0) -> float:
    exponent = -5.257
    base = 1 - (0.0065 * alt_m) / (temp_c + 0.0065 * alt_m + 273.15)
    return p_hpa * (base ** exponent)


def _build_wc_packet(pivoted: dict[str, Any], latest_time: Any) -> dict[str, Any]:
    packet: dict[str, Any] = {
        "wid": settings.weathercloud_id,
        "key": settings.weathercloud_key,
    }

    temp_c = pivoted.get("Temp.")
    missing = [label for label in FIELD_MAPPING if pivoted.get(label) is None]
    if missing:
        logger.warning("WC packet: missing sensor labels (will be omitted): %s", missing)

    for label, wc_field in FIELD_MAPPING.items():
        raw = pivoted.get(label)
        if raw is None:
            continue

        if wc_field == "bar":
            reduced = _reduce_pressure_to_sea_level(raw, temp_c=temp_c if temp_c is not None else 15.0)
            logger.debug(
                "Pressure reduction: %.2f hPa (station) → %.2f hPa (sea level, temp=%.1f°C)",
                raw, reduced, temp_c if temp_c is not None else 15.0,
            )
            value = reduced
        else:
            value = raw

        if wc_field in _NON_NEGATIVE_FIELDS and value < 0:
            logger.debug("Clamping %s (wc=%s) from %.4f to 0 (sensor noise)", label, wc_field, value)
            value = 0.0

        if wc_field in _TENTH_FIELDS:
            packet[wc_field] = int(round(value * 10))
        else:
            packet[wc_field] = int(round(value))

    dew = _calculate_dew_point(temp_c, pivoted.get("Hum"))
    if dew is not None:
        packet["dew"] = int(round(dew * 10))
        logger.debug("Dew point calculated: %.2f°C → %d (tenths)", dew, packet["dew"])
    else:
        logger.warning("Dew point could not be calculated (temp=%s, hum=%s)", temp_c, pivoted.get("Hum"))

    if latest_time is not None:
        ts = latest_time.astimezone(timezone.utc)
        packet["date"] = ts.strftime("%Y%m%d")
        packet["time"] = ts.strftime("%H%M%S")

    return packet


@router.get("/health")
async def weathercloud_health():
    configured = bool(settings.weathercloud_id and settings.weathercloud_key)
    return {
        "enabled": settings.weathercloud_enabled,
        "configured": configured,
        "wid": "***" if settings.weathercloud_id else None,
        "sync_interval_minutes": settings.weathercloud_sync_interval_minutes,
    }


@router.get("/sync-latest")
async def sync_latest(pool: AsyncConnectionPool = Depends(get_pool)):
    if not settings.weathercloud_enabled:
        logger.debug("WC sync skipped: integration is disabled")
        return {"status": "disabled"}

    if not (settings.weathercloud_id and settings.weathercloud_key):
        logger.warning("WC sync skipped: WEATHERCLOUD_ID or WEATHERCLOUD_KEY not set")
        return {"status": "not_configured"}

    query = """
        SELECT DISTINCT ON (label) time, label, value
        FROM measurements
        WHERE station_id = %s
          AND time > NOW() - INTERVAL '30 minutes'
        ORDER BY label, time DESC
    """

    logger.debug("Querying DB for latest measurements (station=%s, window=30min)", settings.default_station_id)
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, (settings.default_station_id,))
            rows = await cur.fetchall()

    if not rows:
        logger.warning("WC sync: no measurements in the last 30 minutes for station '%s'", settings.default_station_id)
        return {"status": "no_data"}

    found_labels = [row["label"] for row in rows]
    latest_time = max(row["time"] for row in rows)
    logger.debug("DB returned %d rows — labels: %s — latest: %s", len(rows), found_labels, latest_time)

    pivoted: dict[str, Any] = {row["label"]: row["value"] for row in rows}
    packet = _build_wc_packet(pivoted, latest_time)

    visible_packet = {k: v for k, v in packet.items() if k not in ("wid", "key")}
    logger.debug("Sending WC packet: %s", visible_packet)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                settings.weathercloud_api_url,
                params=packet,
                timeout=10,
            )
        wc_response = response.text

        if response.status_code == 429:
            logger.warning("WC sync: rate limited (429) — retry in next interval")
        elif response.is_success:
            logger.info("WC sync OK — HTTP %s, response=%r, packet=%s", response.status_code, wc_response, visible_packet)
        else:
            logger.error("WC sync failed — HTTP %s, response=%r", response.status_code, wc_response)

        status = "success" if response.is_success else "error"

    except httpx.TimeoutException:
        logger.error("WC sync: request timed out after 10s (url=%s)", settings.weathercloud_api_url)
        return {"status": "error", "error": "Request timed out"}
    except Exception as exc:
        logger.exception("WC sync: unexpected error sending request")
        return {"status": "error", "error": str(exc)}

    return {
        "status": status,
        "timestamp": str(latest_time),
        "packet": visible_packet,
        "wc_response": wc_response,
    }


@router.post("/test-credentials")
async def test_credentials():
    if not (settings.weathercloud_id and settings.weathercloud_key):
        logger.warning("Credential test skipped: no credentials configured")
        return {"credentials_valid": False, "http_status": None, "wc_response": "No credentials configured"}

    logger.info("Testing WeatherCloud credentials for wid=***")
    test_packet = {
        "wid": settings.weathercloud_id,
        "key": settings.weathercloud_key,
        "temp": 200,
        "hum": 50,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                settings.weathercloud_api_url,
                params=test_packet,
                timeout=10,
            )
        valid = response.is_success
        logger.info("Credential test result: valid=%s, HTTP %s, response=%r", valid, response.status_code, response.text)
        return {
            "credentials_valid": valid,
            "http_status": response.status_code,
            "wc_response": response.text,
        }
    except Exception as exc:
        logger.exception("Credential test request failed")
        return {"credentials_valid": False, "http_status": None, "wc_response": str(exc)}
