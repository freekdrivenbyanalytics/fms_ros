import { useState } from "react";
import type { RescoSyncSummary } from "../types";

export function RescoSyncButton({ sync, onChanged }: {
  sync: () => Promise<RescoSyncSummary>;
  onChanged: () => void | Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<RescoSyncSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  async function run() {
    setBusy(true); setError(null); setResult(null);
    try { setResult(await sync()); await onChanged(); }
    catch (err) { setError(err instanceof Error ? err.message : "Sync failed"); }
    finally { setBusy(false); }
  }
  return <div className="mb-3 text-sm">
    <button type="button" disabled={busy} onClick={run}
      className="rounded-md border border-slate-300 px-3 py-1.5 disabled:opacity-50">
      {busy ? "Syncing…" : "Sync to Resco"}
    </button>
    {result && <div role="status" className="mt-2 text-slate-600">
      Created: {result.created}, updated: {result.updated}, skipped: {result.skipped}, failed: {result.failed}
      {result.errors.map((message, index) => <p className="text-amber-700" key={index}>{message}</p>)}
    </div>}
    {error && <p role="alert" className="text-red-600">{error}</p>}
  </div>;
}
