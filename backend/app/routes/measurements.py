from fastapi import APIRouter, HTTPException, Query
from psycopg.rows import dict_row

from ..config import settings
from ..database import get_pool
from ..schemas import MeasurementPacket
from ..utils import database_error


router = APIRouter()


@router.post("/measurements")
async def save_measurements(packet: MeasurementPacket):
    db_pool = get_pool()

    if packet.station_id != settings.default_station_id:
        raise HTTPException(
            status_code=400,
            detail=f"Only station_id '{settings.default_station_id}' is supported",
        )

    if not packet.measurements:
        raise HTTPException(
            status_code=400,
            detail="No measurements provided",
        )

    if packet.measurement_count is not None:
        if packet.measurement_count != len(packet.measurements):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"measurement_count is {packet.measurement_count}, "
                    f"but received {len(packet.measurements)} measurements"
                ),
            )

    try:
        rows = [
            (
                item.parsed_time(),
                packet.station_id,
                item.label,
                item.value,
                item.unit,
            )
            for item in packet.measurements
        ]

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid sensor_timestamp format. "
                "Expected YYYY/MM/DDTHH:MM:SS. "
                f"Error: {e}"
            ),
        )

    query = """
        INSERT INTO measurements (
            time,
            station_id,
            label,
            value,
            unit
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (time, station_id, label)
        DO UPDATE SET
            value = EXCLUDED.value,
            unit = EXCLUDED.unit;
    """

    try:
        async with db_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.executemany(query, rows)
                await conn.commit()

        return {
            "status": "saved",
            "station_id": packet.station_id,
            "incoming_timestamp_assumption": "UTC",
            "converted_timezone": settings.display_timezone,
            "inserted_measurements": len(rows),
            "labels": [item.label for item in packet.measurements],
            "first_measurement_colombia_time": rows[0][0],
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to save measurements",
        )


@router.get("/measurements")
async def get_latest_measurements(
    limit: int = Query(default=50, ge=1, le=1000),
):
    db_pool = get_pool()

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
        ORDER BY time DESC
        LIMIT %s;
    """

    try:
        async with db_pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    query,
                    (settings.display_timezone, settings.default_station_id, limit),
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


@router.get("/measurements/{label}")
async def get_measurements_by_label(
    label: str,
    limit: int = Query(default=50, ge=1, le=1000),
):
    db_pool = get_pool()

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
        ORDER BY time DESC
        LIMIT %s;
    """

    try:
        async with db_pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    query,
                    (settings.display_timezone, settings.default_station_id, label, limit),
                )
                rows = await cur.fetchall()

        return {
            "station_id": settings.default_station_id,
            "label": label,
            "timezone": settings.display_timezone,
            "count": len(rows),
            "data": rows,
        }

    except Exception as e:
        raise database_error(e)
