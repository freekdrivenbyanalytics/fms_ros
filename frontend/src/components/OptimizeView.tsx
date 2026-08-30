import { useState } from "react";
import { applyOptimization, proposeOptimization } from "../api";
import type { Assignment, OptimizationApplyResult, OptimizationProposal } from "../types";

interface OptimizeViewProps {
  onApplied: (created: Assignment[]) => void;
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function OptimizeView({ onApplied }: OptimizeViewProps) {
  const [proposal, setProposal] = useState<OptimizationProposal | null>(null);
  const [running, setRunning] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [applyResult, setApplyResult] = useState<OptimizationApplyResult | null>(null);

  async function handleRun() {
    setRunning(true);
    setError(null);
    setApplyResult(null);
    try {
      const result = await proposeOptimization();
      setProposal(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run optimization");
    } finally {
      setRunning(false);
    }
  }

  async function handleApply() {
    if (!proposal || proposal.scheduled.length === 0) return;
    setApplying(true);
    setError(null);
    try {
      const result = await applyOptimization(
        proposal.scheduled.map((item) => ({
          service_visit_id: item.service_visit_id,
          employee_id: item.employee_id,
          planned_start: item.planned_start,
        }))
      );
      setApplyResult(result);
      onApplied(result.created);
      setProposal(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to apply proposal");
    } finally {
      setApplying(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={handleRun}
          disabled={running}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {running ? "Running…" : "Run Optimization"}
        </button>
        {proposal && proposal.scheduled.length > 0 && (
          <button
            type="button"
            onClick={handleApply}
            disabled={applying}
            className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {applying ? "Applying…" : "Apply All"}
          </button>
        )}
      </div>

      {error && <div className="text-sm text-red-600">{error}</div>}

      {applyResult && (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
          Created {applyResult.created.length} assignment
          {applyResult.created.length === 1 ? "" : "s"}.
          {applyResult.skipped_visit_ids.length > 0 && (
            <>
              {" "}
              Skipped {applyResult.skipped_visit_ids.length} visit(s) already assigned
              elsewhere.
            </>
          )}
        </div>
      )}

      {proposal && (
        <div className="space-y-4">
          <div className="overflow-x-auto rounded-md border border-slate-200 bg-white">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-slate-500">Visit</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-500">Customer</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-500">Employee</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-500">Requested</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-500">
                    Proposed time
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {proposal.scheduled.map((item) => {
                  const rescheduled =
                    item.planned_start.slice(0, 10) !== item.service_visit.requested_date;
                  return (
                    <tr key={item.service_visit_id}>
                      <td className="px-3 py-2 text-slate-900">#{item.service_visit_id}</td>
                      <td className="px-3 py-2 text-slate-600">
                        {item.service_visit.contract.customer_location.customer.name}
                      </td>
                      <td className="px-3 py-2 text-slate-600">{item.employee.name}</td>
                      <td
                        className={`px-3 py-2 ${
                          rescheduled ? "text-amber-700 font-medium" : "text-slate-600"
                        }`}
                      >
                        {item.service_visit.requested_date}
                        {rescheduled ? " (rescheduled)" : ""}
                      </td>
                      <td className="px-3 py-2 text-slate-600">
                        {formatDateTime(item.planned_start)} – {formatDateTime(item.planned_end)}
                      </td>
                    </tr>
                  );
                })}
                {proposal.scheduled.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-3 py-6 text-center text-slate-400">
                      No visits could be scheduled.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {proposal.unscheduled_visit_ids.length > 0 && (
            <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
              {proposal.unscheduled_visit_ids.length} visit(s) could not be scheduled: visits{" "}
              {proposal.unscheduled_visit_ids.map((id) => `#${id}`).join(", ")}.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
