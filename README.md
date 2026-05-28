# Video prueba concepto
https://youtube.com/shorts/ACczfs93TCw?feature=share

# Estación Meteorológica IoT — Universidad de los Andes

Sistema de monitoreo en tiempo real para la estación meteorológica [Sutron XLink 100](https://www.sutron.com/product/xlink-100-satellite-datalogger/) instalada en el campus de la Universidad de los Andes (Bogotá, Colombia, ~2640 m s.n.m.).

## Arquitectura

```
Sutron XLink 100
      │
      │  POST /measurements  (JSON)
      ▼
  FastAPI (Python)
      │
      │  psycopg3 (async)
      ▼
  TimescaleDB
      │
      │  GET /dashboard/*
      ▼
  React + Recharts
```

El dispositivo envía paquetes JSON con lecturas de los sensores. El backend las almacena en una hipertabla de TimescaleDB. El frontend hace polling al backend para mostrar el dashboard.

**Sensores configurados:** GHI, Rad. (irradiancia), Temp., Hum, Pr. Aire, Velocidad, Direcc. (viento), Precip.

## Puesta en marcha

### Prerrequisitos

- Docker y Docker Compose

### 1. Configurar variables de entorno

```bash
cp .env.example .env
```

Las variables por defecto funcionan sin cambios para desarrollo local.

### 2. Levantar el stack

```bash
docker compose up --build
```

| Servicio | URL |
|---|---|
| Dashboard | http://localhost:5173 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| TimescaleDB | localhost:5432 |

### 3. Poblar la base de datos (opcional)

Para generar datos sintéticos y ver el dashboard con datos:

```bash
pip install psycopg
python scripts/populate_db.py --hours 24 --interval-minutes 1
```

## Desarrollo local

### Backend

```bash
pip install -r backend/requirements.txt
# Requiere TimescaleDB corriendo en localhost:5432
cd backend
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173
npm run build   # build de producción
npm run lint
```

## Estructura del proyecto

```
backend/          FastAPI + psycopg3
  app/
    routes/       measurements, dashboard, sensors, health
    config.py     variables de entorno
    database.py   pool de conexiones async
    schemas.py    modelos Pydantic para paquetes del dispositivo
    utils.py      validación de bucket/range, manejo de errores
db/
  init.sql        esquema TimescaleDB, agregados continuos, datos iniciales
frontend/         React + TypeScript + Vite + Tailwind + Recharts
  src/
    api/          cliente HTTP y tipos TypeScript
    components/   layout, dashboard (KPI, gráficas), controles
    hooks/        useApiHealth, useAutoRefresh, useMeasurementSeries
scripts/
  populate_db.py  generador de datos sintéticos para desarrollo
Xlink100/         scripts de diagnóstico para comunicación directa con el dispositivo (TCP)
```

## Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/sensor_db` | Conexión a TimescaleDB |
| `DEFAULT_STATION_ID` | `uniandes-meteo-01` | ID de estación aceptado por la API |
| `DISPLAY_TIMEZONE` | `America/Bogota` | Zona horaria de las respuestas |
| `BACKEND_CORS_ORIGINS` | `http://localhost:5173,...` | Orígenes CORS permitidos |
| `VITE_API_BASE_URL` | `http://localhost:8000` | URL base del backend (build time) |

> Los timestamps del dispositivo se interpretan siempre como UTC y se convierten a `DISPLAY_TIMEZONE` en las respuestas de la API.
