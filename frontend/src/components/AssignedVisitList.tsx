import type { Assignment, ServiceVisit } from "../types";

interface Props {
  visits: ServiceVisit[];
  assignments: Assignment[];
}

export function AssignedVisitList({ visits, assignments }: Props) {
  const assignmentByVisit = new Map(assignments.map((a) => [a.service_visit_id, a]));

  return (
    <section className="bg-white rounded-lg border border-slate-200 p-4">
      <h2 className="text-lg font-medium text-slate-900 mb-3">Assigned Visits</h2>
      {visits.length === 0 ? (
        <p className="text-sm text-slate-500">No assigned visits.</p>
      ) : (
        <ul className="space-y-3">
          {visits.map((visit) => {
            const assignment = assignmentByVisit.get(visit.id);
            return (
              <li key={visit.id} className="border border-slate-100 rounded-md p-3 text-sm">
                <div className="font-medium text-slate-800">{visit.customer_name}</div>
                <div className="text-xs text-slate-500">{visit.address}</div>
                {assignment && (
                  <div className="text-xs text-slate-600 mt-1">
                    {assignment.employee.name} ·{" "}
                    {formatRange(assignment.planned_start, assignment.planned_end)}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

function formatRange(start: string, end: string): string {
  const fmt = (value: string) =>
    new Date(value).toLocaleString([], { dateStyle: "short", timeStyle: "short" });
  return `${fmt(start)} – ${fmt(end)}`;
}
