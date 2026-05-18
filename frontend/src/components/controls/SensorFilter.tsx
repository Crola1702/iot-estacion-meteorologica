import type { Sensor } from "../../api/types";

type SensorFilterProps = {
  sensors: Sensor[];
  value: string;
  onChange: (label: string) => void;
};

export function SensorFilter({ sensors, value, onChange }: SensorFilterProps) {
  return (
    <label className="flex flex-col gap-1 text-sm font-medium text-slate-700">
      Sensor
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
      >
        {sensors.map((sensor) => (
          <option key={sensor.label} value={sensor.label}>
            {sensor.label}
          </option>
        ))}
      </select>
    </label>
  );
}
