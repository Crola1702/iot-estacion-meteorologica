import { useCallback, useState } from "react";
import { getDashboardSummary, getSeries } from "../api/client";
import type { Bucket, MeasurementPoint, SummaryMetric, TimeRange } from "../api/types";

export function useMeasurementSeries() {
  const [summary, setSummary] = useState<SummaryMetric[]>([]);
  const [series, setSeries] = useState<MeasurementPoint[]>([]);
  const [isLoadingSeries, setIsLoadingSeries] = useState(false);

  const loadSummary = useCallback(async (bucket: Bucket, range: TimeRange, points = 30) => {
    const response = await getDashboardSummary(bucket, range, points);
    setSummary(response.data);
    return response.data;
  }, []);

  const loadSeries = useCallback(
    async (label: string, bucket: Bucket, range: TimeRange, limit = 1000) => {
      if (!label) {
        setSeries([]);
        return [];
      }

      setIsLoadingSeries(true);
      try {
        const response = await getSeries(label, bucket, range, limit);
        setSeries(response.data);
        return response.data;
      } finally {
        setIsLoadingSeries(false);
      }
    },
    [],
  );

  return {
    summary,
    series,
    isLoadingSeries,
    loadSummary,
    loadSeries,
  };
}
