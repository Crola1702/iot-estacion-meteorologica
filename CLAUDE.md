# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IoT weather station dashboard for the Sutron XLink 100 data logger installed at Universidad de los Andes (Bogotá, Colombia). The system receives JSON measurement packets from the device, stores them in TimescaleDB, and serves a React dashboard.

## Development Commands

### Full stack (Docker)
```bash
cp .env.example .env         # configure environment
docker compose up --build    # start all services
```

### Backend (local dev)
```bash
pip install -r backend/requirements.txt
# Requires TimescaleDB running on localhost:5432
uvicorn app.main:app --reload   # run from inside backend/
```

### Frontend (local dev)
```bash
cd frontend
npm install
npm run dev      # starts at http://localhost:5173
npm run build    # type-check + production build
npm run lint     # eslint
```

### Seed the database with synthetic data
```bash
python scripts/populate_db.py --hours 24 --interval-minutes 1
python scripts/populate_db.py --clear   # wipe existing data first
```

## Architecture

```
Sutron XLink 100 → POST /measurements → FastAPI → TimescaleDB
                                                        ↑
                        React frontend ← GET /dashboard/*
```

### Backend (`backend/`)

FastAPI app using `psycopg` (v3, async) with a connection pool. No ORM — all queries are raw SQL.

- `app/config.py` — `Settings` class reads env vars; `settings` singleton used everywhere
- `app/database.py` — async connection pool lifecycle; `get_pool()` used as a dependency in routes
- `app/schemas.py` — Pydantic models for the inbound measurement packet from the device
- `app/utils.py` — shared helpers: `validate_bucket`, `resolve_time_range`, `parse_labels`, `database_error`
- `app/routes/measurements.py` — `POST /measurements` ingests device data; `GET /measurements` and `GET /measurements/{label}` for raw reads
- `app/routes/dashboard.py` — `GET /dashboard/latest`, `/dashboard/summary`, `/dashboard/series/{label}`, `/dashboard/series`
- `app/routes/sensors.py` — `GET /sensors` lists configured sensor slots
- `app/routes/health.py` — `GET /` info, `GET /health` DB ping

**Timestamp handling:** `sensor_timestamp` from the device is always treated as UTC regardless of the string value. It is stored in UTC, then converted to `DISPLAY_TIMEZONE` (default `America/Bogota`) for API responses.

**Single-station design:** The system is hardcoded to one station (`DEFAULT_STATION_ID`). Measurements are rejected unless they match the configured station ID.

### Database (`db/init.sql`)

TimescaleDB on PostgreSQL 16. Key schema:
- `stations` — station metadata (one row for `uniandes-meteo-01`)
- `sensors` — sensor slots (M1–M8); `measurements.label` has a FK to `sensors(station_id, label)`, so labels must be pre-registered
- `measurements` — hypertable on `time`; PK is `(time, station_id, label)`; compressed after 7 days

Continuous aggregate views:
- `measurements_1min` — 1-minute buckets, refreshed every minute
- `measurements_hourly` — 1-hour buckets, refreshed every 5 minutes

Sensor labels: `GHI`, `Rad.`, `Temp.`, `Hum`, `Pr. Aire`, `Velocidad`, `Direcc.`, `Precip.`

### Frontend (`frontend/`)

React 18 + TypeScript + Vite + Tailwind CSS + Recharts. No routing library — single-page app.

- `src/api/client.ts` — typed fetch wrappers for all backend endpoints; `VITE_API_BASE_URL` env var configures the base URL
- `src/api/types.ts` — all shared TypeScript types and the `BUCKETS`/`TIME_RANGES` const arrays
- `src/App.tsx` — root state: selected label, bucket, time range, auto-refresh; coordinates all data fetching
- `src/hooks/` — `useApiHealth`, `useAutoRefresh`, `useLatestMeasurements`, `useMeasurementSeries`
- `src/components/layout/` — `AppShell` (two-column layout), `SidePanel` (controls)
- `src/components/dashboard/` — `KpiGrid`, `MiniChartRail`, `ExpandedChart`, `StatusBanner`

Dashboard data flow: `App` → `refreshDashboard()` calls `/dashboard/summary` (KPI cards + mini-charts) and `/dashboard/series/{label}` (expanded chart). Auto-refresh runs every `AUTO_REFRESH_MS` (defined in `src/utils/constants.ts`).

**Bucket options:** `raw`, `1 minute`, `5 minutes`, `15 minutes`, `1 hour`, `1 day`  
**Range options:** `1h`, `6h`, `24h`, `7d`, `30d`

### Xlink100 utilities (`Xlink100/`)

Standalone Python scripts for directly querying the Sutron XLink 100 over TCP (port 3001, host `192.168.88.1`). These are diagnostic/development tools, not part of the deployed stack.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/sensor_db` | psycopg connection string |
| `DEFAULT_STATION_ID` | `uniandes-meteo-01` | Station ID accepted by the API |
| `DISPLAY_TIMEZONE` | `America/Bogota` | Timezone for API responses |
| `BACKEND_CORS_ORIGINS` | `http://localhost:5173,...` | Comma-separated allowed origins |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Frontend → backend base URL (build-time) |
