import type {
  Bucket,
  HealthResponse,
  LatestResponse,
  SensorsResponse,
  SeriesResponse,
  SummaryResponse,
  TimeRange,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const REQUEST_TIMEOUT_MS = 10000;

async function request<T>(path: string): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      signal: controller.signal,
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      let detail = `Request failed with status ${response.status}`;
      try {
        const payload = await response.json();
        detail = typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail);
      } catch {
        detail = response.statusText || detail;
      }
      throw new Error(detail);
    }

    return response.json() as Promise<T>;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("Request timed out");
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

function encodeQuery(params: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) {
      query.set(key, String(value));
    }
  });

  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

export function getHealth() {
  return request<HealthResponse>("/health");
}

export function getSensors() {
  return request<SensorsResponse>("/sensors");
}

export function getLatestMeasurements() {
  return request<LatestResponse>("/dashboard/latest");
}

export function getDashboardSummary(bucket: Bucket | string, range: TimeRange | string, points = 30) {
  const query = encodeQuery({ bucket, range, points });
  return request<SummaryResponse>(`/dashboard/summary${query}`);
}

export function getSeries(label: string, bucket: Bucket | string, range: TimeRange | string, limit = 1000) {
  const query = encodeQuery({ bucket, range, limit });
  return request<SeriesResponse>(`/dashboard/series/${encodeURIComponent(label)}${query}`);
}
