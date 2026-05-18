import type { SummaryMetric } from "../../api/types";
import { formatShortTime, formatUnit, formatValue } from "../../utils/formatters";

type KpiGridProps = {
  metrics: SummaryMetric[];
  selectedLabel: string;
  onSelect: (label: string) => void;
};

export function KpiGrid({ metrics, selectedLabel, onSelect }: KpiGridProps) {
  if (metrics.length === 0) {
    return (
      <section className="rounded-lg border border-slate-200 bg-white p-5 text-sm text-slate-600">
        No summary measurements are available yet.
      </section>
    );
  }

  return (
    <section className="grid grid-cols-2 gap-3 lg:grid-cols-4 2xl:grid-cols-8">
      {metrics.map((metric) => {
        const selected = metric.label === selectedLabel;

        return (
          <button
            key={metric.label}
            type="button"
            onClick={() => onSelect(metric.label)}
            className={`min-h-[112px] rounded-lg border bg-white p-4 text-left shadow-sm transition hover:border-slate-300 hover:shadow-md ${
              selected ? "border-teal-600 ring-2 ring-teal-100" : "border-slate-200"
            }`}
          >
            <div className="truncate text-sm font-semibold text-slate-600">{metric.label}</div>
            <div className="mt-2 flex items-baseline gap-1">
              <span className="text-2xl font-semibold text-slate-950">{formatValue(metric.latest_value)}</span>
              {formatUnit(metric.unit) ? (
                <span className="text-xs font-medium text-slate-500">{formatUnit(metric.unit)}</span>
              ) : null}
            </div>
            <div className="mt-3 text-xs text-slate-500">Updated {formatShortTime(metric.latest_time)}</div>
          </button>
        );
      })}
    </section>
  );
}
