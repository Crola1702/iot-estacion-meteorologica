import { useCallback, useEffect, useMemo, useState } from "react";
import { getSensors } from "./api/client";
import type { ApiStatus, Bucket, Sensor, TimeRange } from "./api/types";
import { AppShell } from "./components/layout/AppShell";
import { SidePanel } from "./components/layout/SidePanel";
import { ExpandedChart } from "./components/dashboard/ExpandedChart";
import { KpiGrid } from "./components/dashboard/KpiGrid";
import { MiniChartRail } from "./components/dashboard/MiniChartRail";
import { StatusBanner } from "./components/dashboard/StatusBanner";
import { useApiHealth } from "./hooks/useApiHealth";
import { useAutoRefresh } from "./hooks/useAutoRefresh";
import { useLatestMeasurements } from "./hooks/useLatestMeasurements";
import { useMeasurementSeries } from "./hooks/useMeasurementSeries";
import { AUTO_REFRESH_MS, DEFAULT_BUCKET, DEFAULT_TIME_RANGE } from "./utils/constants";

function App() {
  const { apiStatus, checkHealth, setApiStatus } = useApiHealth();
  const { latest, loadLatest } = useLatestMeasurements();
  const { summary, series, isLoadingSeries, loadSummary, loadSeries } = useMeasurementSeries();
  const [sensors, setSensors] = useState<Sensor[]>([]);
  const [selectedLabel, setSelectedLabel] = useState("");
  const [bucket, setBucket] = useState<Bucket>(DEFAULT_BUCKET);
  const [timeRange, setTimeRange] = useState<TimeRange>(DEFAULT_TIME_RANGE);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const availableLabels = useMemo(() => {
    const sensorLabels = sensors.map((sensor) => sensor.label);
    const summaryLabels = summary.map((metric) => metric.label);
    const latestLabels = latest.map((measurement) => measurement.label);
    return Array.from(new Set([...sensorLabels, ...summaryLabels, ...latestLabels]));
  }, [latest, sensors, summary]);

  const displaySensors = useMemo(() => {
    if (sensors.length > 0) {
      return sensors;
    }

    return availableLabels.map((label) => ({
      station_id: "",
      slot: label,
      label,
      quantity: null,
      unit: null,
    }));
  }, [availableLabels, sensors]);

  const selectedMetric = useMemo(
    () => summary.find((metric) => metric.label === selectedLabel),
    [selectedLabel, summary],
  );

  const refreshDashboard = useCallback(async () => {
    setIsRefreshing(true);
    setError(null);
    setApiStatus("loading");

    try {
      await checkHealth();
      setApiStatus("connected");

      const [sensorResponse] = await Promise.all([
        getSensors(),
        loadLatest(),
        loadSummary(bucket, timeRange, 30),
        selectedLabel ? loadSeries(selectedLabel, bucket, timeRange, 1000) : Promise.resolve([]),
      ]);

      setSensors(sensorResponse.data);
    } catch (caught) {
      setApiStatus("unavailable");
      setError(caught instanceof Error ? caught.message : "Unable to load dashboard data");
    } finally {
      setIsRefreshing(false);
    }
  }, [bucket, checkHealth, loadLatest, loadSeries, loadSummary, selectedLabel, setApiStatus, timeRange]);

  useEffect(() => {
    void refreshDashboard();
  }, [refreshDashboard]);

  useEffect(() => {
    setSelectedLabel((current) => {
      if (current && availableLabels.includes(current)) {
        return current;
      }
      return availableLabels.includes("Temp.") ? "Temp." : availableLabels[0] ?? "";
    });
  }, [availableLabels]);

  useEffect(() => {
    if (!selectedLabel) {
      return;
    }

    void loadSeries(selectedLabel, bucket, timeRange, 1000).catch((caught) => {
      setError(caught instanceof Error ? caught.message : "Unable to load series data");
    });
  }, [bucket, loadSeries, selectedLabel, timeRange]);

  useAutoRefresh(autoRefresh, AUTO_REFRESH_MS, refreshDashboard);

  const bannerMessage =
    error ??
    (apiStatus === "connected" && summary.length === 0
      ? "The database has no measurements yet."
      : null);

  return (
    <AppShell
      sidePanel={
        <SidePanel
          apiStatus={apiStatus as ApiStatus}
          sensors={displaySensors}
          selectedLabel={selectedLabel}
          bucket={bucket}
          timeRange={timeRange}
          autoRefresh={autoRefresh}
          isRefreshing={isRefreshing}
          onSelectedLabelChange={setSelectedLabel}
          onBucketChange={setBucket}
          onTimeRangeChange={setTimeRange}
          onAutoRefreshChange={setAutoRefresh}
          onRefresh={refreshDashboard}
        />
      }
    >
      <StatusBanner message={bannerMessage} />
      <KpiGrid metrics={summary} selectedLabel={selectedLabel} onSelect={setSelectedLabel} />
      <section className="grid min-w-0 grid-cols-1 items-start gap-4 xl:grid-cols-[minmax(0,1fr)_460px]">
        <ExpandedChart
          label={selectedLabel}
          unit={selectedMetric?.unit}
          bucket={bucket}
          timeRange={timeRange}
          data={series}
          loading={isLoadingSeries}
        />
        <MiniChartRail metrics={summary} selectedLabel={selectedLabel} onSelect={setSelectedLabel} />
      </section>
    </AppShell>
  );
}

export default App;
