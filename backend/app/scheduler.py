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
            "WeatherScheduler started — wc_sync every %d min",
            settings.weathercloud_sync_interval_minutes,
        )

    async def _sync(self) -> None:
        logger.info("Scheduler firing wc_sync")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:8000/weathercloud/sync-latest",
                    timeout=30,
                )
            try:
                body = response.json()
                status = body.get("status", "unknown")
                wc_resp = body.get("wc_response", "")
            except Exception:
                status = "unknown"
                wc_resp = response.text

            if status == "success":
                logger.info("wc_sync completed — status=%s, wc_response=%r", status, wc_resp)
            elif status in ("disabled", "not_configured", "no_data"):
                logger.warning("wc_sync not sent — status=%s", status)
            else:
                logger.error("wc_sync failed — status=%s, wc_response=%r", status, wc_resp)

        except httpx.TimeoutException:
            logger.error("wc_sync: request to sync-latest timed out after 30s")
        except Exception:
            logger.exception("wc_sync: unexpected error")

    def stop(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("WeatherScheduler stopped")

    def get_jobs(self) -> list[dict]:
        return [
            {"id": job.id, "next_run": str(job.next_run_time)}
            for job in self._scheduler.get_jobs()
        ]


weather_scheduler = WeatherScheduler()
