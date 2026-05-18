CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS stations (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    organization  TEXT,
    latitude      DOUBLE PRECISION,
    longitude     DOUBLE PRECISION,
    altitude_m    DOUBLE PRECISION,
    timezone      TEXT DEFAULT 'America/Bogota',
    device_model  TEXT,
    serial_number TEXT,
    installed_at  TIMESTAMPTZ DEFAULT NOW(),
    metadata      JSONB
);

CREATE TABLE IF NOT EXISTS sensors (
    id          SERIAL PRIMARY KEY,
    station_id  TEXT NOT NULL REFERENCES stations(id) ON DELETE CASCADE,
    slot        TEXT NOT NULL,
    label       TEXT NOT NULL,
    quantity    TEXT,
    unit        TEXT,
    min_valid   DOUBLE PRECISION,
    max_valid   DOUBLE PRECISION,
    metadata    JSONB,
    UNIQUE (station_id, slot),
    UNIQUE (station_id, label)
);

CREATE TABLE IF NOT EXISTS measurements (
    time        TIMESTAMPTZ NOT NULL,
    station_id  TEXT NOT NULL,
    label       TEXT NOT NULL,
    value       DOUBLE PRECISION,
    unit        TEXT,
    PRIMARY KEY (time, station_id, label),
    FOREIGN KEY (station_id, label)
        REFERENCES sensors(station_id, label)
        ON DELETE CASCADE
);

SELECT create_hypertable(
    'measurements',
    'time',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_meas_station_label_time
ON measurements (station_id, label, time DESC);

ALTER TABLE measurements SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'station_id, label'
);

SELECT add_compression_policy(
    'measurements',
    INTERVAL '7 days',
    if_not_exists => TRUE
);

CREATE MATERIALIZED VIEW IF NOT EXISTS measurements_1min
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS bucket,
    station_id,
    label,
    unit,
    AVG(value) AS avg_value,
    MAX(value) AS max_value,
    MIN(value) AS min_value,
    STDDEV(value) AS std_value,
    COUNT(*) AS sample_count
FROM measurements
GROUP BY bucket, station_id, label, unit
WITH NO DATA;

SELECT add_continuous_aggregate_policy(
    'measurements_1min',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE
);

CREATE MATERIALIZED VIEW IF NOT EXISTS measurements_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    station_id,
    label,
    unit,
    AVG(value) AS avg_value,
    MAX(value) AS max_value,
    MIN(value) AS min_value,
    COUNT(*) AS sample_count
FROM measurements
GROUP BY bucket, station_id, label, unit
WITH NO DATA;

SELECT add_continuous_aggregate_policy(
    'measurements_hourly',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '5 minutes',
    if_not_exists => TRUE
);

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
    'uniandes-meteo-01',
    'Estacion Universidad Andes',
    'Universidad de los Andes',
    4.6020,
    -74.0660,
    2640,
    'America/Bogota',
    'Sutron XLink 100'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO sensors (
    station_id,
    slot,
    label,
    quantity,
    unit
)
VALUES
    ('uniandes-meteo-01', 'M1', 'GHI',       'irradiance',    'Wm2'),
    ('uniandes-meteo-01', 'M2', 'Rad.',      'irradiance',    'Wm2'),
    ('uniandes-meteo-01', 'M3', 'Temp.',     'temperature',   'C'),
    ('uniandes-meteo-01', 'M4', 'Hum',       'humidity',      '%'),
    ('uniandes-meteo-01', 'M5', 'Pr. Aire',  'pressure',      'hPa'),
    ('uniandes-meteo-01', 'M6', 'Velocidad', 'wind_speed',    'm/s'),
    ('uniandes-meteo-01', 'M7', 'Direcc.',   'wind_dir',      NULL),
    ('uniandes-meteo-01', 'M8', 'Precip.',   'precipitation', 'mmh')
ON CONFLICT (station_id, slot) DO NOTHING;
