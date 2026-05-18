#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import os
import random
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import psycopg
from psycopg import OperationalError


DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/sensor_db"
DEFAULT_STATION_ID = "uniandes-meteo-01"


@dataclass(frozen=True)
class Sensor:
    slot: str
    label: str
    quantity: str
    unit: str | None


SENSORS = [
    Sensor("M1", "GHI", "irradiance", "Wm2"),
    Sensor("M2", "Rad.", "irradiance", "Wm2"),
    Sensor("M3", "Temp.", "temperature", "C"),
    Sensor("M4", "Hum", "humidity", "%"),
    Sensor("M5", "Pr. Aire", "pressure", "hPa"),
    Sensor("M6", "Velocidad", "wind_speed", "m/s"),
    Sensor("M7", "Direcc.", "wind_dir", None),
    Sensor("M8", "Precip.", "precipitation", "mmh"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Populate TimescaleDB with synthetic weather station measurements."
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        help="PostgreSQL connection URL. Defaults to DATABASE_URL or local Docker DB.",
    )
    parser.add_argument(
        "--station-id",
        default=DEFAULT_STATION_ID,
        help="Station id to seed.",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Number of hours of measurements to insert.",
    )
    parser.add_argument(
        "--interval-minutes",
        type=int,
        default=1,
        help="Minutes between samples.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for repeatable values.",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete existing measurements for the station before inserting.",
    )
    return parser.parse_args()


def daylight_factor(timestamp: datetime) -> float:
    hour = timestamp.hour + timestamp.minute / 60
    if hour < 6 or hour > 18:
        return 0.0

    return math.sin(math.pi * (hour - 6) / 12)


def sensor_value(sensor: Sensor, timestamp: datetime) -> float:
    daylight = daylight_factor(timestamp)
    minute_of_day = timestamp.hour * 60 + timestamp.minute
    daily_wave = math.sin(2 * math.pi * minute_of_day / 1440)

    if sensor.label == "GHI":
        return max(0.0, 820 * daylight + random.gauss(0, 28))
    if sensor.label == "Rad.":
        return max(0.0, 760 * daylight + random.gauss(0, 24))
    if sensor.label == "Temp.":
        return 14.5 + 8.0 * daylight + random.gauss(0, 0.45)
    if sensor.label == "Hum":
        return min(100.0, max(35.0, 74 - 20 * daylight + random.gauss(0, 2.5)))
    if sensor.label == "Pr. Aire":
        return 746.0 + 1.6 * daily_wave + random.gauss(0, 0.25)
    if sensor.label == "Velocidad":
        return max(0.0, 1.8 + 1.2 * daylight + random.gauss(0, 0.55))
    if sensor.label == "Direcc.":
        return (120 + 45 * daily_wave + random.gauss(0, 18)) % 360
    if sensor.label == "Precip.":
        raining = 15 <= timestamp.hour <= 17 and random.random() < 0.18
        return round(random.uniform(0.1, 2.8), 2) if raining else 0.0

    raise ValueError(f"Unhandled sensor label: {sensor.label}")


def build_rows(station_id: str, hours: int, interval_minutes: int) -> list[tuple]:
    if hours <= 0:
        raise ValueError("--hours must be greater than 0")
    if interval_minutes <= 0:
        raise ValueError("--interval-minutes must be greater than 0")

    end = datetime.now(UTC).replace(second=0, microsecond=0)
    start = end - timedelta(hours=hours)
    step = timedelta(minutes=interval_minutes)

    rows = []
    timestamp = start
    while timestamp <= end:
        for sensor in SENSORS:
            rows.append(
                (
                    timestamp,
                    station_id,
                    sensor.label,
                    round(sensor_value(sensor, timestamp), 3),
                    sensor.unit,
                )
            )
        timestamp += step

    return rows


def ensure_station_and_sensors(conn: psycopg.Connection, station_id: str) -> None:
    conn.execute(
        """
        INSERT INTO stations (
            id,
            name,
            organization,
            latitude,
            longitude,
            altitude_m,
            timezone,
            device_model
        )
        VALUES (
            %s,
            'Estacion Universidad Andes',
            'Universidad de los Andes',
            4.6020,
            -74.0660,
            2640,
            'America/Bogota',
            'Sutron XLink 100'
        )
        ON CONFLICT (id) DO NOTHING;
        """,
        (station_id,),
    )

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO sensors (
                station_id,
                slot,
                label,
                quantity,
                unit
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (station_id, slot) DO UPDATE SET
                label = EXCLUDED.label,
                quantity = EXCLUDED.quantity,
                unit = EXCLUDED.unit;
            """,
            [
                (station_id, sensor.slot, sensor.label, sensor.quantity, sensor.unit)
                for sensor in SENSORS
            ],
        )


def populate(args: argparse.Namespace) -> int:
    random.seed(args.seed)
    rows = build_rows(args.station_id, args.hours, args.interval_minutes)

    with psycopg.connect(args.database_url) as conn:
        ensure_station_and_sensors(conn, args.station_id)

        if args.clear:
            conn.execute(
                "DELETE FROM measurements WHERE station_id = %s;",
                (args.station_id,),
            )

        with conn.cursor() as cur:
            cur.executemany(
                """
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
                """,
                rows,
            )

    return len(rows)


def main() -> None:
    args = parse_args()
    try:
        inserted = populate(args)
    except OperationalError as exc:
        print(
            f"Could not connect to the database at {args.database_url}. "
            "Make sure TimescaleDB is running and the connection URL is correct.",
            file=sys.stderr,
        )
        print(f"psycopg error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(
        f"Seeded {inserted} measurements for {args.station_id} "
        f"({args.hours}h every {args.interval_minutes} min)."
    )


if __name__ == "__main__":
    main()
