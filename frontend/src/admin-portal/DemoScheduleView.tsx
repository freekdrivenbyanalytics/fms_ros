import { useState } from "react";
import { refreshDemoSchedule } from "../api";
import type { DemoScheduleRefreshSummary } from "../types";

interface Props {
  onChanged: () => void | Promise<void>;
}

export function DemoScheduleView({ onChanged }: Props) {
  const [confirming, setConfirming] = useState(false);
  const [running, setRunning] = useState(false);
  const [summary, setSummary] = useState<DemoScheduleRefreshSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleConfirm() {
    setRunning(true);
    setError(null);
    setSummary(null);
    try {
      const result = await refreshDemoSchedule();
      setSummary(result);
      setConfirming(false);
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to refresh demo schedule");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-slate-900 mb-4">Demo</h2>

      <div className="rounded-md border border-slate-200 bg-white p-4 max-w-xl">
        <h3 className="text-sm font-medium text-slate-900">Refresh demo schedule</h3>
        <p className="mt-1 text-sm text-slate-600">
          Shifts every service visit's date forward so the earliest one starts today (keeping
          the spacing between visits), and clears every assignment — including pinned ones —
          back to unassigned. Local only: no Tripletex calls, no changes to customers,
          contracts, or employees.
        </p>

        {!confirming && (
          <button
            type="button"
            onClick={() => setConfirming(true)}
            className="mt-3 rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white"
          >
            Refresh Demo Schedule
          </button>
        )}

        {confirming && (
          <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 p-3">
            <p className="text-sm text-amber-800">
              This will shift visit dates and unassign every visit, including pinned ones. This
              can't be undone. Continue?
            </p>
            <div className="mt-2 flex gap-2">
              <button
                type="button"
                onClick={handleConfirm}
                disabled={running}
                className="rounded-md bg-amber-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
              >
                {running ? "Refreshing…" : "Yes, refresh"}
              </button>
              <button
                type="button"
                onClick={() => setConfirming(false)}
                disabled={running}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

        {summary && (
          <div className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
            Shifted visit dates forward by {summary.days_shifted} day
            {summary.days_shifted === 1 ? "" : "s"} and unassigned {summary.visits_unassigned}{" "}
            visit{summary.visits_unassigned === 1 ? "" : "s"}.
          </div>
        )}
      </div>
    </div>
  );
}
