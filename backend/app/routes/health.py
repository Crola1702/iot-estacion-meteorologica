from fastapi import APIRouter, HTTPException

from ..config import settings
from ..database import get_pool


router = APIRouter()


@router.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Sutron X100 Timescale API running",
        "station_id": settings.default_station_id,
        "incoming_timestamp_assumption": "sensor_timestamp is UTC",
        "display_timezone": settings.display_timezone,
        "storage_format": "label and unit are saved separately",
    }


@router.get("/health")
async def health_check():
    db_pool = get_pool()

    try:
        async with db_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1;")
                await cur.fetchone()

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Database connection failed",
        )
