import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Bucket, MeasurementPoint, TimeRange } from "../../api/types";
import { formatDateTime, formatLabelWithUnit, formatUnit, formatValue } from "../../utils/formatters";

type ExpandedChartProps = {
  label: string;
  unit?: string | null;
  bucket: Bucket;
  timeRange: TimeRange;
  data: MeasurementPoint[];
  loading: boolean;
};

export function ExpandedChart({ label, unit, bucket, timeRange, data, loading }: ExpandedChartProps) {
  const displayUnit = unit ?? data.find((point) => point.unit)?.unit ?? null;

  return (
    <section className="flex flex-col rounded-lg border border-slate-200 bg-white p-4 shadow-sm xl:h-[568px]">
      <div className="mb-4 flex flex-col gap-1 md:flex-row md:items-end md:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-950">
            {formatLabelWithUnit(label || "Sensor", displayUnit)}
          </h2>
          <p className="text-sm text-slate-500">
            {bucket} bucket · {timeRange} range
          </p>
        </div>
        <span className="text-sm text-slate-500">{loading ? "Loading" : `${data.length} points`}</span>
      </div>

      <div className="h-[360px] w-full xl:min-h-0 xl:flex-1">
        {data.length === 0 ? (
          <div className="flex h-full items-center justify-center rounded-lg border border-dashed border-slate-300 text-sm text-slate-500">
            {loading ? "Loading series data..." : "No series data available for this selection."}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 8, right: 20, bottom: 8, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#dbe3ef" />
              <XAxis
                dataKey="colombia_time"
                tickFormatter={formatDateTime}
                minTickGap={28}
                tick={{ fontSize: 12, fill: "#64748b" }}
              />
              <YAxis tick={{ fontSize: 12, fill: "#64748b" }} width={56} />
              <Tooltip
                labelFormatter={(value) => formatDateTime(String(value))}
                formatter={(value) => [`${formatValue(Number(value))} ${formatUnit(displayUnit)}`.trim(), label]}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#0f766e"
                strokeWidth={2.5}
                dot={false}
                connectNulls={false}
                name={label}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </section>
  );
}
