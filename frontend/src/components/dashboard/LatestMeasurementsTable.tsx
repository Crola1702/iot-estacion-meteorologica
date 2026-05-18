import type { MeasurementPoint } from "../../api/types";
import { formatDateTime, formatUnit, formatValue } from "../../utils/formatters";

type LatestMeasurementsTableProps = {
  measurements: MeasurementPoint[];
};

export function LatestMeasurementsTable({ measurements }: LatestMeasurementsTableProps) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-950">Latest measurements</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-normal text-slate-500">
            <tr>
              <th className="px-4 py-3 font-semibold">Label</th>
              <th className="px-4 py-3 font-semibold">Value</th>
              <th className="px-4 py-3 font-semibold">Unit</th>
              <th className="px-4 py-3 font-semibold">Colombia Time</th>
              <th className="px-4 py-3 font-semibold">Stored Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {measurements.length === 0 ? (
              <tr>
                <td className="px-4 py-5 text-slate-500" colSpan={5}>
                  No measurements available.
                </td>
              </tr>
            ) : (
              measurements.map((measurement) => (
                <tr key={measurement.label}>
                  <td className="px-4 py-3 font-medium text-slate-900">{measurement.label}</td>
                  <td className="px-4 py-3 text-slate-700">{formatValue(measurement.value)}</td>
                  <td className="px-4 py-3 text-slate-700">{formatUnit(measurement.unit)}</td>
                  <td className="px-4 py-3 text-slate-700">{formatDateTime(measurement.colombia_time)}</td>
                  <td className="px-4 py-3 text-slate-700">{formatDateTime(measurement.stored_time)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
