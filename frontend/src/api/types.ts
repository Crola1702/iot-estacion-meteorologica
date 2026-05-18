export const BUCKETS = ["raw", "1 minute", "5 minutes", "15 minutes", "1 hour", "1 day"] as const;
export const TIME_RANGES = ["1h", "6h", "24h", "7d", "30d"] as const;

export type Bucket = (typeof BUCKETS)[number];
export type TimeRange = (typeof TIME_RANGES)[number];
export type ApiStatus = "connected" | "loading" | "unavailable";

export type Sensor = {
  station_id: string;
  slot: string;
  label: string;
  quantity: string | null;
  unit: string | null;
  min_valid?: number | null;
  max_valid?: number | null;
};

export type MeasurementPoint = {
  colombia_time: string;
  stored_time?: string;
  station_id?: string;
  label: string;
  value: number | null;
  unit: string | null;
  sample_count?: number;
};

export type SummarySeriesPoint = {
  time: string;
  value: number | null;
};

export type SummaryMetric = {
  label: string;
  unit: string | null;
  latest_value: number | null;
  latest_time: string | null;
  series: SummarySeriesPoint[];
};

export type HealthResponse = {
  status: string;
  database: string;
};

export type SensorsResponse = {
  station_id: string;
  count: number;
  data: Sensor[];
};

export type LatestResponse = {
  station_id: string;
  timezone: string;
  count: number;
  data: MeasurementPoint[];
};

export type SummaryResponse = {
  station_id: string;
  timezone: string;
  bucket: string;
  points: number;
  data: SummaryMetric[];
};

export type SeriesResponse = {
  station_id: string;
  label: string;
  bucket: string;
  range: string;
  timezone: string;
  count: number;
  data: MeasurementPoint[];
};
