import { Line, LineChart, ResponsiveContainer } from "recharts";
import type { SummarySeriesPoint } from "../../api/types";

type MicroChartProps = {
  data: SummarySeriesPoint[];
  active?: boolean;
};

export function MicroChart({ data, active = false }: MicroChartProps) {
  if (data.length === 0) {
    return <div className="h-12 rounded border border-dashed border-slate-200" />;
  }

  return (
    <div className="h-12 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={active ? "#0f766e" : "#2563eb"}
            strokeWidth={2}
            dot={false}
            connectNulls={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
