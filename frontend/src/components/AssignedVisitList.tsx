import type { Assignment, ServiceVisit } from "../types";
import { InfoBox } from "./InfoBox";

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
                <InfoBox
                  summary={
                    <div>
                      <div className="font-medium text-slate-800">
                        {visit.contract.customer_location.customer.name}
                      </div>
                      <div className="flex flex-wrap gap-1 mt-1">
                        <span className="inline-block rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                          {visit.contract.customer_location.region.name}
                        </span>
                        {visit.contract.required_skills.map((skill) => (
                          <span
                            key={skill.id}
                            className="inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700"
                          >
                            {skill.name}
                          </span>
                        ))}
                      </div>
                      {assignment && (
                        <div className="text-xs text-slate-600 mt-1">
                          {assignment.employee.name} ·{" "}
                          {formatRange(assignment.planned_start, assignment.planned_end)}
                        </div>
                      )}
                    </div>
                  }
                >
                  <div>{visit.contract.customer_location.customer.name}</div>
                  <div>{visit.contract.customer_location.address}</div>
                  <div>
                    {visit.contract.customer_location.latitude.toFixed(4)},{" "}
                    {visit.contract.customer_location.longitude.toFixed(4)}
                  </div>
                </InfoBox>
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
