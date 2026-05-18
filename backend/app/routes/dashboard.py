from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query
from psycopg.rows import dict_row

from ..config import settings
from ..database import get_pool
from ..utils import (
    database_error,
    parse_labels,
    resolve_time_range,
    validate_bucket,
)


router = APIRouter(prefix="/dashboard")


@router.get("/latest")
async def get_dashboard_latest():
    db_pool = get_pool()

    query = """
        SELECT DISTINCT ON (label)
            time AT TIME ZONE %s AS colombia_time,
            time AS stored_time,
            station_id,
            label,
            value,
            unit
        FROM measurements
        WHERE station_id = %s
        ORDER BY label, time DESC;
    """

    try:
        async with db_pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    query,
                    (settings.display_timezone, settings.default_station_id),
                )
                rows = await cur.fetchall()

        return {
            "station_id": settings.default_station_id,
            "timezone": settings.display_timezone,
            "count": len(rows),
            "data": rows,
        }

    except Exception as e:
        raise database_error(e)


@router.get("/summary")
async def get_dashboard_summary(
    bucket: str = Query(default="5 minutes"),
    range_value: str = Query(default="24h", alias="range"),
    points: int = Query(default=30, ge=1, le=500),
):
    db_pool = get_pool()
    bucket = validate_bucket(bucket)
    range_start, range_end = resolve_time_range(None, None, range_value)
    if bucket == "raw":
        bucket = "1 minute"

    latest_query = """
        SELECT DISTINCT ON (label)
            label,
            value AS latest_value,
            unit,
            time AT TIME ZONE %s AS latest_time
        FROM measurements
        WHERE station_id = %s
        ORDER BY label, time DESC;
    """
    series_query = """
        WITH query_params AS (
            SELECT
                %s::interval AS bucket_interval,
                %s::timestamptz AS start_time,
                %s::timestamptz AS end_time
        ),
        aggregated AS (
            SELECT
                time_bucket(query_params.bucket_interval, time) AS bucket_time,
                label,
                AVG(value) AS value
            FROM measurements
            CROSS JOIN query_params
            WHERE station_id = %s
              AND time >= query_params.start_time
              AND time <= query_params.end_time
            GROUP BY bucket_time, label
        ),
        ranked AS (
            SELECT
                bucket_time,
                label,
                value,
                ROW_NUMBER() OVER (
                    PARTITION BY label
                    ORDER BY bucket_time DESC
                ) AS row_number
            FROM aggregated
        )
        SELECT
            bucket_time AT TIME ZONE %s AS colombia_time,
            label,
            value
        FROM ranked
        WHERE row_number <= %s
        ORDER BY label ASC, bucket_time ASC;
    """

    try:
        async with db_pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    latest_query,
                    (settings.display_timezone, settings.default_station_id),
                )
                latest_rows = await cur.fetchall()

                await cur.execute(
                    series_query,
                    (
                        bucket,
                        range_start,
                        range_end,
                        settings.default_station_id,
                        settings.display_timezone,
                        points,
                    ),
                )
                series_rows = await cur.fetchall()

        summary_by_label = {
            row["label"]: {
                "label": row["label"],
                "unit": row["unit"],
                "latest_value": row["latest_value"],
                "latest_time": row["latest_time"],
                "series": [],
            }
            for row in latest_rows
        }

        for row in series_rows:
            item = summary_by_label.get(row["label"])
            if item is None:
                continue

            item["series"].append(
                {
                    "time": row["colombia_time"],
                    "value": row["value"],
                }
            )

        return {
            "station_id": settings.default_station_id,
            "timezone": settings.display_timezone,
            "bucket": bucket,
            "range": range_value,
            "points": points,
            "data": list(summary_by_label.values()),
        }

    except Exception as e:
        raise database_error(e)


@router.get("/series/{label}")
async def get_dashboard_series_by_label(
    label: str,
    start: Optional[datetime] = Query(default=None),
    end: Optional[datetime] = Query(default=None),
    range_value: str = Query(default="24h", alias="range"),
    bucket: str = Query(default="1 minute"),
    limit: int = Query(default=1000, ge=1, le=10000),
):
    db_pool = get_pool()
    bucket = validate_bucket(bucket)
    range_start, range_end = resolve_time_range(start, end, range_value)

    if bucket == "raw":
        query = """
            SELECT
                time AT TIME ZONE %s AS colombia_time,
                time AS stored_time,
                station_id,
                label,
                value,
                unit
            FROM measurements
            WHERE station_id = %s
              AND label = %s
              AND time >= %s
              AND time <= %s
            ORDER BY time ASC
            LIMIT %s;
        """
        params = (
            settings.display_timezone,
            settings.default_station_id,
            label,
            range_start,
            range_end,
            limit,
        )
    else:
        query = """
            WITH query_params AS (
                SELECT %s::interval AS bucket_interval
            )
            SELECT
                time_bucket(query_params.bucket_interval, time) AT TIME ZONE %s AS colombia_time,
                MIN(time) AS stored_time,
                station_id,
                label,
                AVG(value) AS value,
                MAX(unit) AS unit,
                COUNT(*) AS sample_count
            FROM measurements
            CROSS JOIN query_params
            WHERE station_id = %s
              AND label = %s
              AND time >= %s
              AND time <= %s
            GROUP BY time_bucket(query_params.bucket_interval, time), station_id, label
            ORDER BY stored_time ASC
            LIMIT %s;
        """
        params = (
            bucket,
            settings.display_timezone,
            settings.default_station_id,
            label,
            range_start,
            range_end,
            limit,
        )

    try:
        async with db_pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, params)
                rows = await cur.fetchall()

        return {
            "station_id": settings.default_station_id,
            "label": label,
            "bucket": bucket,
            "range": range_value,
            "timezone": settings.display_timezone,
            "count": len(rows),
            "data": rows,
        }

    except Exception as e:
        raise database_error(e)


@router.get("/series")
async def get_dashboard_series(
    labels: Optional[str] = Query(default=None),
    start: Optional[datetime] = Query(default=None),
    end: Optional[datetime] = Query(default=None),
    range_value: str = Query(default="24h", alias="range"),
    bucket: str = Query(default="1 minute"),
    limit: int = Query(default=1000, ge=1, le=10000),
):
    db_pool = get_pool()
    bucket = validate_bucket(bucket)
    selected_labels = parse_labels(labels)
    range_start, range_end = resolve_time_range(start, end, range_value)

    if bucket == "raw":
        query = """
            SELECT
                time AT TIME ZONE %s AS colombia_time,
                label,
                value,
                unit
            FROM measurements
            WHERE station_id = %s
              AND (%s::text[] IS NULL OR label = ANY(%s::text[]))
              AND time >= %s
              AND time <= %s
            ORDER BY time ASC
            LIMIT %s;
        """
        params = (
            settings.display_timezone,
            settings.default_station_id,
            selected_labels,
            selected_labels,
            range_start,
            range_end,
            limit,
        )
    else:
        query = """
            WITH query_params AS (
                SELECT %s::interval AS bucket_interval
            )
            SELECT
                time_bucket(query_params.bucket_interval, time) AT TIME ZONE %s AS colombia_time,
                label,
                AVG(value) AS value,
                MAX(unit) AS unit
            FROM measurements
            CROSS JOIN query_params
            WHERE station_id = %s
              AND (%s::text[] IS NULL OR label = ANY(%s::text[]))
              AND time >= %s
              AND time <= %s
            GROUP BY time_bucket(query_params.bucket_interval, time), label
            ORDER BY colombia_time ASC
            LIMIT %s;
        """
        params = (
            bucket,
            settings.display_timezone,
            settings.default_station_id,
            selected_labels,
            selected_labels,
            range_start,
            range_end,
            limit,
        )

    try:
        async with db_pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, params)
                rows = await cur.fetchall()

        series: dict[str, list[dict[str, object]]] = {}
        for row in rows:
            series.setdefault(row["label"], []).append(
                {
                    "time": row["colombia_time"],
                    "value": row["value"],
                    "unit": row["unit"],
                }
            )

        return {
            "station_id": settings.default_station_id,
            "bucket": bucket,
            "range": range_value,
            "timezone": settings.display_timezone,
            "series": series,
        }

    except Exception as e:
        raise database_error(e)
