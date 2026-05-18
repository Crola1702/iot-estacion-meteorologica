import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException


ALLOWED_BUCKETS = {"raw", "1 minute", "5 minutes", "15 minutes", "1 hour", "1 day"}
ALLOWED_RANGES = {
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}

logger = logging.getLogger(__name__)


def validate_bucket(bucket: str) -> str:
    if bucket not in ALLOWED_BUCKETS:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid bucket",
                "allowed_values": sorted(ALLOWED_BUCKETS),
            },
        )

    return bucket


def resolve_time_range(
    start: Optional[datetime],
    end: Optional[datetime],
    range_value: str,
) -> tuple[datetime, datetime]:
    if start is not None and end is not None:
        return start, end

    if range_value not in ALLOWED_RANGES:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid range",
                "allowed_values": sorted(ALLOWED_RANGES),
            },
        )

    resolved_end = end or datetime.now(timezone.utc)
    resolved_start = start or resolved_end - ALLOWED_RANGES[range_value]
    return resolved_start, resolved_end


def parse_labels(labels: Optional[str]) -> Optional[list[str]]:
    if labels is None:
        return None

    parsed = [label.strip() for label in labels.split(",") if label.strip()]
    return parsed or None


def database_error(exc: Exception) -> HTTPException:
    logger.exception("Database query failed", exc_info=exc)
    return HTTPException(
        status_code=500,
        detail="Database query failed",
    )
