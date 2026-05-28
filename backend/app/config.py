from functools import lru_cache
import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


load_dotenv(".env")
load_dotenv("backend/.env")


class Settings:
    def __init__(self) -> None:
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/sensor_db",
        )
        self.default_station_id = os.getenv(
            "DEFAULT_STATION_ID",
            "uniandes-meteo-01",
        )
        self.display_timezone = os.getenv(
            "DISPLAY_TIMEZONE",
            "America/Bogota",
        )
        self.backend_cors_origins = os.getenv(
            "BACKEND_CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        )
        self.weathercloud_enabled = os.getenv("WEATHERCLOUD_ENABLED", "false").lower() == "true"
        self.weathercloud_id = os.getenv("WEATHERCLOUD_ID") or None
        self.weathercloud_key = os.getenv("WEATHERCLOUD_KEY") or None
        self.weathercloud_api_url = os.getenv(
            "WEATHERCLOUD_API_URL",
            "https://api.weathercloud.net/v01/set",
        )
        self.weathercloud_sync_interval_minutes = int(
            os.getenv("WEATHERCLOUD_SYNC_INTERVAL_MINUTES", "5")
        )

    @property
    def timezone(self) -> ZoneInfo:
        return ZoneInfo(self.display_timezone)

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
