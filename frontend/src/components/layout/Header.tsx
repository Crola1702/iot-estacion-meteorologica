import type { ApiStatus } from "../../api/types";
import { STATION_ID } from "../../utils/constants";
import { formatShortTime } from "../../utils/formatters";

type HeaderProps = {
  apiStatus: ApiStatus;
  isRefreshing: boolean;
  lastRefresh: Date | null;
  onRefresh: () => void;
};

export function Header({ apiStatus, isRefreshing, lastRefresh, onRefresh }: HeaderProps) {
  const statusClasses = {
    connected: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    loading: "bg-amber-50 text-amber-700 ring-amber-200",
    unavailable: "bg-rose-50 text-rose-700 ring-rose-200",
  };

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-3 px-4 py-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-950">Weather Station Dashboard</h1>
          <p className="mt-1 text-sm text-slate-500">{STATION_ID}</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <span className={`rounded-full px-3 py-1 text-sm font-medium ring-1 ${statusClasses[apiStatus]}`}>
            API {apiStatus === "connected" ? "Connected" : apiStatus === "loading" ? "Loading" : "Unavailable"}
          </span>
          <span className="text-sm text-slate-500">
            Last refresh {lastRefresh ? formatShortTime(lastRefresh.toISOString()) : "--"}
          </span>
          <button
            type="button"
            onClick={onRefresh}
            disabled={isRefreshing}
            className="rounded-md bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {isRefreshing ? "Refreshing" : "Refresh"}
          </button>
        </div>
      </div>
    </header>
  );
}
