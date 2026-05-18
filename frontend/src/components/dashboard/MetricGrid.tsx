import type { SummaryMetric } from "../../api/types";
import { MetricCard } from "./MetricCard";

type MetricGridProps = {
  metrics: SummaryMetric[];
  selectedLabel: string;
  onSelect: (label: string) => void;
};

export function MetricGrid({ metrics, selectedLabel, onSelect }: MetricGridProps) {
  if (metrics.length === 0) {
    return (
      <section className="rounded-lg border border-slate-200 bg-white p-5 text-sm text-slate-600">
        No summary measurements are available yet.
      </section>
    );
  }

  return (
    <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {metrics.map((metric) => (
        <MetricCard
          key={metric.label}
          metric={metric}
          selected={metric.label === selectedLabel}
          onSelect={onSelect}
        />
      ))}
    </section>
  );
}
