import { useEffect, useState } from "react";
import { listAssignments, listServiceVisits, syncAssignmentStatuses } from "../api";
import type { Assignment, RescoStatusSyncSummary, ServiceVisit } from "../types";

export function AllVisitsView({ onChanged }: { onChanged: () => Promise<void> }) {
  const [visits, setVisits] = useState<ServiceVisit[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<RescoStatusSyncSummary | null>(null);

  async function load() {
    const [allVisits, allAssignments] = await Promise.all([listServiceVisits(), listAssignments()]);
    setVisits(allVisits);
    setAssignments(allAssignments);
  }
  useEffect(() => {
    Promise.all([listServiceVisits(), listAssignments()])
      .then(([allVisits, allAssignments]) => {
        setVisits(allVisits);
        setAssignments(allAssignments);
      })
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false));
  }, []);

  async function sync() {
    if (!window.confirm("Refresh statuses from Resco? Assignments planned before today whose current Work Order status is Scheduled will be unassigned, including pinned assignments. Their Work Orders will be reset to Draft where possible. Failed resets will be retried.")) return;
    setBusy(true);
    setError(null);
    try {
      setSummary(await syncAssignmentStatuses());
      await Promise.all([load(), onChanged()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Status update failed");
    } finally {
      setBusy(false);
    }
  }

  const byVisit = new Map(assignments.map((a) => [a.service_visit_id, a]));
  return <section className="rounded-lg border border-slate-200 bg-white p-4">
    <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
      <p className="text-sm text-slate-600">Every visit, including completed and unassigned visits.</p>
      <button type="button" disabled={busy || loading} onClick={sync}
        className="rounded-md bg-emerald-600 px-3 py-2 text-sm text-white disabled:opacity-50">
        {busy ? "Updating..." : "Update status from Resco"}
      </button>
    </div>
    <p className="mb-3 text-xs text-slate-500">Updates current statuses. Past planned assignments still Scheduled in Resco are unassigned, including pinned visits, and their Work Orders are reset to Draft where possible. Failed resets are retried on the next update.</p>
    {error && <p role="alert" className="mb-3 text-red-600">{error}</p>}
    {summary && <div role="status" className="mb-4 text-sm text-slate-700">
      {summary.pulled} statuses updated; {summary.skipped} unsynced; {summary.failed} failed;
      {" "}{summary.reconciled} unassigned; {summary.reconciliation_skipped} reconciliation checks skipped;
      {" "}{summary.reset_failed} Draft resets failed.
      {(summary.errors.length > 0 || summary.skip_reasons.length > 0) && <details className="mt-2 text-amber-700">
        <summary>View failures and skipped assignments</summary>
        <ul>{[...summary.errors, ...summary.skip_reasons].map((message, i) => <li key={i}>{message}</li>)}</ul>
      </details>}
    </div>}
    {loading ? <p>Loading...</p> : <div className="overflow-x-auto"><table className="w-full text-left text-sm">
      <thead><tr className="border-b text-slate-500"><th className="p-2">Visit</th><th className="p-2">Customer / location</th><th className="p-2">Requested</th><th className="p-2">Assignment</th><th className="p-2">Status</th></tr></thead>
      <tbody>{visits.map((visit) => {
        const assignment = byVisit.get(visit.id);
        const location = visit.contract_line.customer_location;
        return <tr key={visit.id} className="border-b border-slate-100 align-top">
          <td className="p-2">{visit.id}</td><td className="p-2">{location.customer.name}<div className="text-xs text-slate-500">{location.address}</div></td>
          <td className="p-2">{visit.requested_date}</td>
          <td className="p-2">{assignment ? <>{assignment.employee.name}<div>{assignment.planned_start.replace("T", " ")}</div>
            <details className="text-xs text-slate-500"><summary>Resco IDs</summary>
              <div className="break-all select-text">Work Order: {assignment.resco_work_order_id ?? "Not synced"}</div>
              <div className="break-all select-text">Schedule: {assignment.resco_work_order_schedule_id ?? "Not synced"}</div>
            </details></> : "Unassigned"}</td>
          <td className="p-2">{visit.status}{assignment?.resco_status && <div className="text-emerald-700">{assignment.resco_status}</div>}
            {visit.unassigned_reason && <div className="text-amber-700">{visit.unassigned_reason}</div>}</td>
        </tr>;
      })}</tbody>
    </table>{visits.length === 0 && <p className="p-2 text-slate-500">No visits.</p>}</div>}
  </section>;
}
