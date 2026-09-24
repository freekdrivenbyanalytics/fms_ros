import { useRef, useState } from "react";
import { reconcileScheduledAssignments, syncAssignmentStatuses } from "../api";
import type { RescoStatusSyncSummary } from "../types";

export function RescoStatusActions({ onChanged, allowReconcile = false, disabled = false }: {
  onChanged: () => Promise<void>;
  allowReconcile?: boolean;
  disabled?: boolean;
}) {
  const inFlight = useRef(false);
  const [busy, setBusy] = useState<"sync" | "reconcile" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ action: "sync" | "reconcile"; summary: RescoStatusSyncSummary } | null>(null);

  async function run(action: "sync" | "reconcile") {
    if (inFlight.current || disabled) return;
    if (action === "reconcile" && !window.confirm("Unassign visits planned before today whose Work Orders are currently Scheduled in Resco? This includes pinned visits. Their Work Orders will be reset to Draft where possible, and failed Draft resets will be retried.")) return;
    inFlight.current = true;
    setBusy(action);
    setError(null);
    setResult(null);
    try {
      const summary = await (action === "sync" ? syncAssignmentStatuses() : reconcileScheduledAssignments());
      setResult({ action, summary });
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Resco operation failed");
    } finally {
      inFlight.current = false;
      setBusy(null);
    }
  }

  return <div className="mb-4">
    <div className="flex flex-wrap gap-2">
      <button type="button" disabled={disabled || busy !== null} onClick={() => run("sync")}
        className="rounded-md bg-emerald-600 px-3 py-2 text-sm text-white disabled:opacity-50">
        {busy === "sync" ? "Syncing..." : "Sync from Resco"}
      </button>
      {allowReconcile && <button type="button" disabled={disabled || busy !== null} onClick={() => run("reconcile")}
        className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900 disabled:opacity-50">
        {busy === "reconcile" ? "Unassigning..." : "Unassign past Scheduled visits"}
      </button>}
    </div>
    <p className="mt-2 text-xs text-slate-500">Sync refreshes the last-known Resco statuses.</p>
    {allowReconcile && <p className="mt-1 text-xs text-slate-500">Unassign checks current statuses, unassigns past planned visits still Scheduled (including pinned visits), and resets their Work Orders to Draft. It also retries failed Draft resets.</p>}
    {error && <p role="alert" className="mt-2 text-sm text-red-600">{error}</p>}
    {result && <div role="status" className="mt-2 text-sm text-slate-700">
      {result.summary.pulled} statuses updated; {result.summary.skipped} unsynced; {result.summary.failed} failed.
      {result.action === "reconcile" && <span> {result.summary.reconciled} unassigned; {result.summary.reconciliation_skipped} reconciliation checks skipped; {result.summary.reset_failed} Draft resets failed.</span>}
      {(result.summary.errors.length > 0 || result.summary.skip_reasons.length > 0) && <details className="mt-2 text-amber-700">
        <summary>View failures and skipped assignments</summary>
        <ul>{[...result.summary.errors, ...result.summary.skip_reasons].map((message, i) => <li key={i}>{message}</li>)}</ul>
      </details>}
    </div>}
  </div>;
}
