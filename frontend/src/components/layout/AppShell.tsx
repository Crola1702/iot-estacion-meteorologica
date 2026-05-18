import type { ReactNode } from "react";

type AppShellProps = {
  sidePanel: ReactNode;
  children: ReactNode;
};

export function AppShell({ sidePanel, children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-slate-100 text-slate-950">
      <div className="mx-auto grid w-full max-w-[1600px] grid-cols-1 gap-4 px-4 py-4 lg:grid-cols-[280px_minmax(0,1fr)]">
        {sidePanel}
        <main className="flex min-w-0 flex-col gap-4">{children}</main>
      </div>
    </div>
  );
}
