import { TIME_RANGES, type TimeRange } from "../../api/types";

type TimeRangeFilterProps = {
  value: TimeRange;
  onChange: (range: TimeRange) => void;
};

export function TimeRangeFilter({ value, onChange }: TimeRangeFilterProps) {
  return (
    <label className="flex flex-col gap-1 text-sm font-medium text-slate-700">
      Time range
      <select
        value={value}
        onChange={(event) => onChange(event.target.value as TimeRange)}
        className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
      >
        {TIME_RANGES.map((range) => (
          <option key={range} value={range}>
            {range}
          </option>
        ))}
      </select>
    </label>
  );
}
