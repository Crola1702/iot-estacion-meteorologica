from typing import Optional

from fastapi import HTTPException
from psycopg_pool import AsyncConnectionPool

from .config import settings


pool: Optional[AsyncConnectionPool] = None


async def open_pool() -> None:
    global pool

    pool = AsyncConnectionPool(
        conninfo=settings.database_url,
        min_size=1,
        max_size=10,
        open=False,
    )
    await pool.open()


async def close_pool() -> None:
    global pool

    if pool is not None:
        await pool.close()
        pool = None


def get_pool() -> AsyncConnectionPool:
    if pool is None:
        raise HTTPException(
            status_code=500,
            detail="Database pool not initialized",
        )

    return pool
