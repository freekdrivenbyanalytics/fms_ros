import { useMemo, useState } from "react";
import { setAssignmentPinned, unassignVisit } from "../api";
import { collectFilterOptions, filterItems } from "../lib/listFilter";
import type { Assignment, ServiceVisit } from "../types";
import { InfoBox } from "./InfoBox";
import { ListFilterBar } from "./ListFilterBar";

interface Props {
  visits: ServiceVisit[];
  assignments: Assignment[];
  onUnassigned: (serviceVisitId: number) => void;
  onPinChanged: (assignment: Assignment) => void;
}

function extract(visit: ServiceVisit) {
  return {
    name: visit.contract.customer_location.customer.name,
    address: visit.contract.customer_location.address,
    regions: visit.contract.customer_location.region ? [visit.contract.customer_location.region] : [],
    skills: visit.contract.required_skills,
  };
}

export function AssignedVisitList({ visits, assignments, onUnassigned, onPinChanged }: Props) {
  const [search, setSearch] = useState("");
  const [regionIds, setRegionIds] = useState<number[]>([]);
  const [skillIds, setSkillIds] = useState<number[]>([]);

  const assignmentByVisit = new Map(assignments.map((a) => [a.service_visit_id, a]));

  const { regions: regionOptions, skills: skillOptions } = useMemo(
    () => collectFilterOptions(visits, extract),
    [visits]
  );

  const filteredVisits = useMemo(
    () => filterItems(visits, extract, search, regionIds, skillIds),
    [visits, search, regionIds, skillIds]
  );

  return (
    <section className="bg-white rounded-lg border border-slate-200 p-4">
      <h2 className="text-lg font-medium text-slate-900 mb-3">Assigned Visits</h2>
      <ListFilterBar
        search={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search by customer or address…"
        regionOptions={regionOptions}
        selectedRegionIds={regionIds}
        onRegionIdsChange={setRegionIds}
        skillOptions={skillOptions}
        selectedSkillIds={skillIds}
        onSkillIdsChange={setSkillIds}
      />
      {visits.length === 0 ? (
        <p className="text-sm text-slate-500">No assigned visits.</p>
      ) : filteredVisits.length === 0 ? (
        <p className="text-sm text-slate-500">No matches for the current search/filters.</p>
      ) : (
        <ul className="space-y-3">
          {filteredVisits.map((visit) => {
            const assignment = assignmentByVisit.get(visit.id);
            if (!assignment) return null;
            return (
              <AssignedVisitCard
                key={visit.id}
                visit={visit}
                assignment={assignment}
                onUnassigned={onUnassigned}
                onPinChanged={onPinChanged}
              />
            );
          })}
        </ul>
      )}
    </section>
  );
}

interface CardProps {
  visit: ServiceVisit;
  assignment: Assignment;
  onUnassigned: (serviceVisitId: number) => void;
  onPinChanged: (assignment: Assignment) => void;
}

function AssignedVisitCard({ visit, assignment, onUnassigned, onPinChanged }: CardProps) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const plannedDate = assignment.planned_start.slice(0, 10);
  const rescheduled = plannedDate !== visit.requested_date;

  async function handleUnassign() {
    setBusy(true);
    setError(null);
    try {
      await unassignVisit(visit.id);
      onUnassigned(visit.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to unassign visit");
      setBusy(false);
    }
  }

  async function handleTogglePin() {
    setBusy(true);
    setError(null);
    try {
      const updated = await setAssignmentPinned(visit.id, !assignment.pinned);
      onPinChanged(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update pin");
    } finally {
      setBusy(false);
    }
  }

  return (
    <li className="border border-slate-100 rounded-md p-3 text-sm">
      <div className="flex items-start justify-between gap-3">
        <InfoBox
          summary={
            <div>
              <div className="font-medium text-slate-800 flex items-center gap-2">
                {visit.contract.customer_location.customer.name}
                {assignment.pinned && (
                  <span className="inline-block rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800">
                    Pinned
                  </span>
                )}
              </div>
              <div className="flex flex-wrap gap-1 mt-1">
                <span className="inline-block rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                  {visit.contract.customer_location.region?.name ?? "No region"}
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
              <div className="text-xs text-slate-600 mt-1">
                {assignment.employee.name} ·{" "}
                {formatRange(assignment.planned_start, assignment.planned_end)}
              </div>
              <div
                className={`text-xs mt-0.5 ${
                  rescheduled ? "text-amber-700 font-medium" : "text-slate-400"
                }`}
              >
                Requested {visit.requested_date}
                {rescheduled ? " (rescheduled)" : ""}
              </div>
            </div>
          }
        >
          <div>{visit.contract.customer_location.customer.name}</div>
          <div>{visit.contract.customer_location.address}</div>
          <div>
            {visit.contract.customer_location.latitude !== null &&
            visit.contract.customer_location.longitude !== null
              ? `${visit.contract.customer_location.latitude.toFixed(4)}, ${visit.contract.customer_location.longitude.toFixed(4)}`
              : "Coordinates not yet resolved"}
          </div>
        </InfoBox>
        <div className="shrink-0 flex flex-col items-end gap-1">
          <button
            type="button"
            onClick={handleTogglePin}
            disabled={busy}
            className={`text-xs px-2 py-1 rounded-md border disabled:opacity-50 ${
              assignment.pinned
                ? "bg-amber-50 border-amber-200 text-amber-800 hover:bg-amber-100"
                : "bg-white border-slate-300 text-slate-600 hover:bg-slate-50"
            }`}
          >
            {assignment.pinned ? "Unpin" : "Pin"}
          </button>
          <button
            type="button"
            onClick={handleUnassign}
            disabled={busy}
            className="text-xs px-2 py-1 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50 disabled:opacity-50"
          >
            Unassign
          </button>
        </div>
      </div>
      {error && <p className="text-xs text-red-600 mt-2">{error}</p>}
    </li>
  );
}

function formatRange(start: string, end: string): string {
  const fmt = (value: string) =>
    new Date(value).toLocaleString([], { dateStyle: "short", timeStyle: "short" });
  return `${fmt(start)} – ${fmt(end)}`;
}
