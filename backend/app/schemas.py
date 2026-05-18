from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from .config import settings


class MeasurementItem(BaseModel):
    slot: str = Field(..., examples=["M1"])
    label: str = Field(..., examples=["GHI"])
    value: Optional[float] = Field(None, examples=[735.0])
    unit: Optional[str] = Field(None, examples=["Wm2"])
    sensor_timestamp: str = Field(..., examples=["2026/05/13T22:00:00"])

    def parsed_time(self) -> datetime:
        naive_time = datetime.strptime(
            self.sensor_timestamp,
            "%Y/%m/%dT%H:%M:%S",
        )
        utc_time = naive_time.replace(tzinfo=timezone.utc)
        return utc_time.astimezone(settings.timezone)


class MeasurementPacket(BaseModel):
    station_id: str = Field(default_factory=lambda: settings.default_station_id)
    ingested_at: Optional[datetime] = None
    measurement_count: Optional[int] = None
    measurements: list[MeasurementItem]
