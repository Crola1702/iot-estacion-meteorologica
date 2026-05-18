import { BUCKETS, type Bucket } from "../../api/types";

type BucketFilterProps = {
  value: Bucket;
  onChange: (bucket: Bucket) => void;
};

export function BucketFilter({ value, onChange }: BucketFilterProps) {
  return (
    <label className="flex flex-col gap-1 text-sm font-medium text-slate-700">
      Bucket
      <select
        value={value}
        onChange={(event) => onChange(event.target.value as Bucket)}
        className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
      >
        {BUCKETS.map((bucket) => (
          <option key={bucket} value={bucket}>
            {bucket}
          </option>
        ))}
      </select>
    </label>
  );
}
