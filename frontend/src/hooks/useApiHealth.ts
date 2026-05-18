import { useCallback, useEffect, useState } from "react";
import { getHealth } from "../api/client";
import type { ApiStatus } from "../api/types";

export function useApiHealth() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>("loading");

  const checkHealth = useCallback(async () => {
    setApiStatus("loading");
    try {
      await getHealth();
      setApiStatus("connected");
      return true;
    } catch {
      setApiStatus("unavailable");
      return false;
    }
  }, []);

  useEffect(() => {
    void checkHealth();
  }, [checkHealth]);

  return { apiStatus, checkHealth, setApiStatus };
}
