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

    for label, wc_field in FIELD_MAPPING.items():
        raw = pivoted.get(label)
        if raw is None:
            continue

        if wc_field == "bar":
            value = _reduce_pressure_to_sea_level(raw, temp_c=temp_c if temp_c is not None else 15.0)
        else:
            value = raw

        if wc_field in _TENTH_FIELDS:
            packet[wc_field] = int(round(value * 10))
        else:
            packet[wc_field] = int(round(value))

    dew = _calculate_dew_point(temp_c, pivoted.get("Hum"))
    if dew is not None:
        packet["dew"] = int(round(dew * 10))

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
        return {"status": "disabled"}

    if not (settings.weathercloud_id and settings.weathercloud_key):
        return {"status": "not_configured"}

    query = """
        SELECT DISTINCT ON (label) time, label, value
        FROM measurements
        WHERE station_id = %s
          AND time > NOW() - INTERVAL '30 minutes'
        ORDER BY label, time DESC
    """

    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, (settings.default_station_id,))
            rows = await cur.fetchall()

    if not rows:
        return {"status": "no_data"}

    pivoted: dict[str, Any] = {row["label"]: row["value"] for row in rows}
    latest_time = max(row["time"] for row in rows)

    packet = _build_wc_packet(pivoted, latest_time)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                settings.weathercloud_api_url,
                params=packet,
                timeout=10,
            )
        wc_response = response.text
        status = "success" if response.is_success else "error"
        logger.info("WeatherCloud sync: HTTP %s — %s", response.status_code, wc_response)
    except Exception as exc:
        logger.exception("WeatherCloud sync request failed")
        return {"status": "error", "error": str(exc)}

    return {
        "status": status,
        "timestamp": str(latest_time),
        "packet": {k: v for k, v in packet.items() if k not in ("wid", "key")},
        "wc_response": wc_response,
    }


@router.post("/test-credentials")
async def test_credentials():
    if not (settings.weathercloud_id and settings.weathercloud_key):
        return {"credentials_valid": False, "http_status": None, "wc_response": "No credentials configured"}

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
        return {
            "credentials_valid": response.is_success,
            "http_status": response.status_code,
            "wc_response": response.text,
        }
    except Exception as exc:
        logger.exception("WeatherCloud credential test failed")
        return {"credentials_valid": False, "http_status": None, "wc_response": str(exc)}
