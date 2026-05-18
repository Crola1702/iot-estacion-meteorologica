import type { Bucket, TimeRange } from "../api/types";

export const STATION_ID = "uniandes-meteo-01";
export const DISPLAY_TIMEZONE = "America/Bogota";
export const DEFAULT_BUCKET: Bucket = "5 minutes";
export const DEFAULT_TIME_RANGE: TimeRange = "24h";
export const AUTO_REFRESH_MS = 60000;
