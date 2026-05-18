import { useEffect } from "react";

export function useAutoRefresh(
  enabled: boolean,
  intervalMs: number,
  callback: () => void | Promise<void>,
) {
  useEffect(() => {
    if (!enabled) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      void callback();
    }, intervalMs);

    return () => window.clearInterval(intervalId);
  }, [callback, enabled, intervalMs]);
}
