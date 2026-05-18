import type { ApiStatus, Bucket, Sensor, TimeRange } from "../../api/types";
import { AUTO_REFRESH_MS, DISPLAY_TIMEZONE, STATION_ID } from "../../utils/constants";
import { AutoRefreshToggle } from "../controls/AutoRefreshToggle";
import { BucketFilter } from "../controls/BucketFilter";
import { SensorFilter } from "../controls/SensorFilter";
import { TimeRangeFilter } from "../controls/TimeRangeFilter";

type SidePanelProps = {
  apiStatus: ApiStatus;
  sensors: Sensor[];
  selectedLabel: string;
  bucket: Bucket;
  timeRange: TimeRange;
  autoRefresh: boolean;
  isRefreshing: boolean;
  onSelectedLabelChange: (label: string) => void;
  onBucketChange: (bucket: Bucket) => void;
  onTimeRangeChange: (range: TimeRange) => void;
  onAutoRefreshChange: (enabled: boolean) => void;
  onRefresh: () => void;
};

export function SidePanel({
  apiStatus,
  sensors,
  selectedLabel,
  bucket,
  timeRange,
  autoRefresh,
  isRefreshing,
  onSelectedLabelChange,
  onBucketChange,
  onTimeRangeChange,
  onAutoRefreshChange,
  onRefresh,
}: SidePanelProps) {
  return (
    <aside className="flex min-w-0 flex-col gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm lg:sticky lg:top-4 lg:self-start">
      <section>
        <h2 className="text-sm font-semibold text-slate-950">Station</h2>
        <dl className="mt-3 space-y-2 text-sm">
          <div>
            <dt className="text-slate-500">ID</dt>
            <dd className="font-medium text-slate-800">{STATION_ID}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Timezone</dt>
            <dd className="font-medium text-slate-800">{DISPLAY_TIMEZONE}</dd>
          </div>
          <div>
            <dt className="text-slate-500">API</dt>
            <dd className="font-medium capitalize text-slate-800">{apiStatus}</dd>
          </div>
        </dl>
      </section>

      <section className="border-t border-slate-200 pt-4">
        <h2 className="text-sm font-semibold text-slate-950">Filters</h2>
        <div className="mt-3 flex flex-col gap-3">
          <SensorFilter sensors={sensors} value={selectedLabel} onChange={onSelectedLabelChange} />
          <BucketFilter value={bucket} onChange={onBucketChange} />
          <TimeRangeFilter value={timeRange} onChange={onTimeRangeChange} />
        </div>
      </section>

      <section className="border-t border-slate-200 pt-4">
        <h2 className="text-sm font-semibold text-slate-950">Refresh</h2>
        <div className="mt-3 flex flex-col gap-3">
          <button
            type="button"
            onClick={onRefresh}
            disabled={isRefreshing}
            className="rounded-md bg-slate-950 px-3 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {isRefreshing ? "Refreshing" : "Refresh now"}
          </button>
          <AutoRefreshToggle
            checked={autoRefresh}
            intervalMs={AUTO_REFRESH_MS}
            onChange={onAutoRefreshChange}
          />
        </div>
      </section>

    </aside>
  );
}
