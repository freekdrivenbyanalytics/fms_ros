import { useState, type FormEvent } from "react";
import { createAssignment } from "../api";
import type { Assignment, Employee, ServiceVisit } from "../types";

interface ListProps {
  visits: ServiceVisit[];
  employees: Employee[];
  onAssigned: (assignment: Assignment) => void;
}

export function UnassignedVisitList({ visits, employees, onAssigned }: ListProps) {
  return (
    <section className="bg-white rounded-lg border border-slate-200 p-4">
      <h2 className="text-lg font-medium text-slate-900 mb-3">Unassigned Visits</h2>
      {visits.length === 0 ? (
        <p className="text-sm text-slate-500">No unassigned visits.</p>
      ) : (
        <ul className="space-y-3">
          {visits.map((visit) => (
            <VisitRow
              key={visit.id}
              visit={visit}
              employees={employees}
              onAssigned={onAssigned}
            />
          ))}
        </ul>
      )}
    </section>
  );
}

interface RowProps {
  visit: ServiceVisit;
  employees: Employee[];
  onAssigned: (assignment: Assignment) => void;
}

function VisitRow({ visit, employees, onAssigned }: RowProps) {
  const [open, setOpen] = useState(false);
  const [employeeId, setEmployeeId] = useState("");
  const [plannedStart, setPlannedStart] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!employeeId || !plannedStart) return;

    setSubmitting(true);
    setError(null);
    try {
      const assignment = await createAssignment({
        service_visit_id: visit.id,
        employee_id: Number(employeeId),
        planned_start: new Date(plannedStart).toISOString(),
      });
      onAssigned(assignment);
      setOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to assign visit");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <li className="border border-slate-100 rounded-md p-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="font-medium text-slate-800 text-sm">{visit.customer_name}</div>
          <div className="text-xs text-slate-500">{visit.address}</div>
          <div className="text-xs text-slate-500">
            {visit.duration_minutes} min · requested {visit.requested_date}
          </div>
        </div>
        <button
          type="button"
          onClick={() => setOpen((prev) => !prev)}
          className="shrink-0 text-sm px-3 py-1 rounded-md bg-slate-900 text-white hover:bg-slate-700"
        >
          Assign
        </button>
      </div>

      {open && (
        <form onSubmit={handleSubmit} className="mt-3 flex flex-col gap-2">
          <select
            value={employeeId}
            onChange={(event) => setEmployeeId(event.target.value)}
            className="text-sm border border-slate-300 rounded-md px-2 py-1"
            required
          >
            <option value="" disabled>
              Select employee
            </option>
            {employees.map((employee) => (
              <option key={employee.id} value={employee.id}>
                {employee.name}
              </option>
            ))}
          </select>
          <input
            type="datetime-local"
            value={plannedStart}
            onChange={(event) => setPlannedStart(event.target.value)}
            className="text-sm border border-slate-300 rounded-md px-2 py-1"
            required
          />
          {error && <p className="text-xs text-red-600">{error}</p>}
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={submitting}
              className="text-sm px-3 py-1 rounded-md bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-50"
            >
              {submitting ? "Assigning…" : "Confirm"}
            </button>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="text-sm px-3 py-1 rounded-md border border-slate-300"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </li>
  );
}
