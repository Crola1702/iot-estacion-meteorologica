import type { SummaryMetric } from "../../api/types";
import { formatShortTime, formatUnit, formatValue } from "../../utils/formatters";
import { MicroChart } from "./MicroChart";

type MetricCardProps = {
  metric: SummaryMetric;
  selected: boolean;
  onSelect: (label: string) => void;
};

export function MetricCard({ metric, selected, onSelect }: MetricCardProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(metric.label)}
      onDoubleClick={() => onSelect(metric.label)}
      className={`min-h-[150px] rounded-lg border bg-white p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md ${
        selected ? "border-teal-600 ring-2 ring-teal-100" : "border-slate-200"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate text-sm font-semibold text-slate-700">{metric.label}</h3>
          <p className="mt-2 text-2xl font-semibold text-slate-950">
            {formatValue(metric.latest_value)}
            {formatUnit(metric.unit) ? (
              <span className="ml-1 text-sm font-medium text-slate-500">{formatUnit(metric.unit)}</span>
            ) : null}
          </p>
        </div>
        <span className="rounded-md border border-slate-200 px-2 py-1 text-xs font-medium text-slate-500">
          Open
        </span>
      </div>
      <div className="mt-4">
        <MicroChart data={metric.series} active={selected} />
      </div>
      <p className="mt-3 text-xs text-slate-500">Updated {formatShortTime(metric.latest_time)}</p>
    </button>
  );
}
