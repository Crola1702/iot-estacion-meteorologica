type AutoRefreshToggleProps = {
  checked: boolean;
  intervalMs: number;
  onChange: (enabled: boolean) => void;
};

export function AutoRefreshToggle({ checked, intervalMs, onChange }: AutoRefreshToggleProps) {
  return (
    <label className="flex items-center justify-between gap-3 text-sm font-medium text-slate-800">
      <span>
        Auto-refresh
        <span className="block text-xs font-normal text-slate-500">{Math.round(intervalMs / 1000)}s interval</span>
      </span>
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        className="h-4 w-4 rounded border-slate-300"
      />
    </label>
  );
}
