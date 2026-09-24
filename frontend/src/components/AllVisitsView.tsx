import { useEffect, useState } from "react";
import { RescoStatusActions } from "./RescoStatusActions";
import { listAssignments, listServiceVisits } from "../api";
import type { Assignment, ServiceVisit } from "../types";

export function AllVisitsView({ onChanged }: { onChanged: () => Promise<void> }) {
  const [visits, setVisits] = useState<ServiceVisit[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  const byVisit = new Map(assignments.map((a) => [a.service_visit_id, a]));
  return <section className="rounded-lg border border-slate-200 bg-white p-4">
    <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
      <p className="text-sm text-slate-600">Every visit, including completed and unassigned visits.</p>
    </div>
    <RescoStatusActions allowReconcile disabled={loading} onChanged={async () => {
      await Promise.all([load(), onChanged()]);
    }} />
    {error && <p role="alert" className="mb-3 text-red-600">{error}</p>}
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
