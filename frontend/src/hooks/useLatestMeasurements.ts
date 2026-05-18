import { useCallback, useState } from "react";
import { getLatestMeasurements } from "../api/client";
import type { MeasurementPoint } from "../api/types";

export function useLatestMeasurements() {
  const [latest, setLatest] = useState<MeasurementPoint[]>([]);
  const [isLoadingLatest, setIsLoadingLatest] = useState(false);

  const loadLatest = useCallback(async () => {
    setIsLoadingLatest(true);
    try {
      const response = await getLatestMeasurements();
      setLatest(response.data);
      return response.data;
    } finally {
      setIsLoadingLatest(false);
    }
  }, []);

  return { latest, isLoadingLatest, loadLatest };
}
