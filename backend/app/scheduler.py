import logging

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .config import settings

logger = logging.getLogger(__name__)


class WeatherScheduler:
    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler()

    def start(self) -> None:
        self._scheduler.add_job(
            self._sync,
            "interval",
            minutes=settings.weathercloud_sync_interval_minutes,
            id="wc_sync",
            coalesce=True,
            max_instances=1,
        )
        self._scheduler.start()
        logger.info(
            "WeatherScheduler started (interval: %d min)",
            settings.weathercloud_sync_interval_minutes,
        )

    async def _sync(self) -> None:
        async with httpx.AsyncClient() as client:
            try:
                await client.get(
                    "http://localhost:8000/weathercloud/sync-latest",
                    timeout=30,
                )
            except Exception:
                logger.exception("Scheduled WeatherCloud sync failed")

    def stop(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("WeatherScheduler stopped")

    def get_jobs(self) -> list[dict]:
        return [
            {"id": job.id, "next_run": str(job.next_run_time)}
            for job in self._scheduler.get_jobs()
        ]


weather_scheduler = WeatherScheduler()
