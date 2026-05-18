import type { SummaryMetric } from "../../api/types";
import { formatShortTime, formatUnit, formatValue } from "../../utils/formatters";
import { MicroChart } from "./MicroChart";

type MiniChartRailProps = {
  metrics: SummaryMetric[];
  selectedLabel: string;
  onSelect: (label: string) => void;
};

export function MiniChartRail({ metrics, selectedLabel, onSelect }: MiniChartRailProps) {
  return (
    <aside className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="grid grid-cols-1 gap-2 p-3 sm:grid-cols-2 xl:grid-cols-2">
        {metrics.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-200 p-4 text-sm text-slate-500 sm:col-span-2">
            No mini chart data available.
          </div>
        ) : (
          metrics.map((metric) => {
            const selected = metric.label === selectedLabel;

            return (
              <button
                key={metric.label}
                type="button"
                onClick={() => onSelect(metric.label)}
                className={`flex h-[130px] flex-col rounded-lg border p-3 text-left transition hover:border-slate-300 hover:bg-slate-50 ${
                  selected ? "border-teal-600 bg-teal-50" : "border-slate-200 bg-white"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold text-slate-800">{metric.label}</div>
                    <div className="mt-1 text-xs text-slate-500">Updated {formatShortTime(metric.latest_time)}</div>
                  </div>
                  <div className="shrink-0 text-right">
                    <div className="text-sm font-semibold text-slate-950">{formatValue(metric.latest_value)}</div>
                    <div className="text-xs text-slate-500">{formatUnit(metric.unit)}</div>
                  </div>
                </div>
                <div className="mt-auto pt-3">
                  <MicroChart data={metric.series} active={selected} />
                </div>
              </button>
            );
          })
        )}
      </div>
    </aside>
  );
}
