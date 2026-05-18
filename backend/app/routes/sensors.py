from fastapi import APIRouter
from psycopg.rows import dict_row

from ..config import settings
from ..database import get_pool
from ..utils import database_error


router = APIRouter()


@router.get("/sensors")
async def get_sensors():
    db_pool = get_pool()

    query = """
        SELECT
            station_id,
            slot,
            label,
            quantity,
            unit,
            min_valid,
            max_valid
        FROM sensors
        WHERE station_id = %s
        ORDER BY slot;
    """

    try:
        async with db_pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, (settings.default_station_id,))
                rows = await cur.fetchall()

        return {
            "station_id": settings.default_station_id,
            "count": len(rows),
            "data": rows,
        }

    except Exception as e:
        raise database_error(e)
