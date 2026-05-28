import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(levelname)-8s %(name)s — %(message)s",
)
from .database import close_pool, open_pool
from .routes import dashboard, health, measurements, sensors
from .routes import weathercloud
from .scheduler import weather_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await open_pool()
    weather_scheduler.start()
    yield
    weather_scheduler.stop()
    await close_pool()


app = FastAPI(
    title="Sutron X100 Timescale API",
    description="HTTP API for receiving Sutron X100 JSON measurements and saving them into TimescaleDB.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=(
        r"^http://("
        r"localhost|127\.0\.0\.1|"
        r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"192\.168\.\d{1,3}\.\d{1,3}|"
        r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}"
        r"):5173$"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Sutron X100 Timescale API running",
        "station_id": settings.default_station_id,
        "incoming_timestamp_assumption": "sensor_timestamp is UTC",
        "display_timezone": settings.display_timezone,
        "storage_format": "label and unit are saved separately",
        "scheduler_jobs": weather_scheduler.get_jobs(),
    }


app.include_router(health.router)
app.include_router(measurements.router)
app.include_router(sensors.router)
app.include_router(dashboard.router)
app.include_router(weathercloud.router)
