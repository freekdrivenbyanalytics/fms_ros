import { useEffect, useState } from "react";
import { listAssignments, listEmployees, listServiceVisits } from "./api";
import { AssignedVisitList } from "./components/AssignedVisitList";
import { DayPlanningView } from "./components/DayPlanningView";
import { EmployeeList } from "./components/EmployeeList";
import { OptimizeView } from "./components/OptimizeView";
import { UnassignedVisitList } from "./components/UnassignedVisitList";
import type { Assignment, Employee, ServiceVisit } from "./types";

type View = "assign" | "planning" | "optimize";

const VIEW_TITLES: Record<View, string> = {
  assign: "Manual Assignment",
  planning: "Day Planning",
  optimize: "Optimize",
};

function toIsoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function addDays(d: Date, days: number): Date {
  const result = new Date(d);
  result.setDate(result.getDate() + days);
  return result;
}

function defaultEndDate(): string {
  return toIsoDate(addDays(new Date(), 7));
}

function endOfCurrentWeek(): string {
  const today = new Date();
  const day = today.getDay(); // Sunday = 0 ... Saturday = 6
  const daysUntilSunday = day === 0 ? 0 : 7 - day;
  return toIsoDate(addDays(today, daysUntilSunday));
}

function fourWeeksOut(): string {
  return toIsoDate(addDays(new Date(), 28));
}

function App() {
  const [view, setView] = useState<View>("assign");
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [visits, setVisits] = useState<ServiceVisit[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [visitsEndDate, setVisitsEndDate] = useState(defaultEndDate());
  const [visitsLoading, setVisitsLoading] = useState(false);

  useEffect(() => {
    Promise.all([listEmployees(), listAssignments()])
      .then(([employeesData, assignmentsData]) => {
        setEmployees(employeesData);
        setAssignments(assignmentsData);
      })
      .catch((err) =>
        setLoadError(err instanceof Error ? err.message : "Failed to load data")
      );
  }, []);

  useEffect(() => {
    setVisitsLoading(true);
    listServiceVisits({ endDate: visitsEndDate })
      .then(setVisits)
      .catch((err) =>
        setLoadError(err instanceof Error ? err.message : "Failed to load data")
      )
      .finally(() => {
        setVisitsLoading(false);
        setLoading(false);
      });
  }, [visitsEndDate]);

  function handleAssigned(assignment: Assignment) {
    setAssignments((prev) => [...prev, assignment]);
    setVisits((prev) =>
      prev.map((visit) =>
        visit.id === assignment.service_visit_id
          ? { ...visit, status: "assigned" }
          : visit
      )
    );
  }

  function handleOptimizationApplied(created: Assignment[]) {
    setAssignments((prev) => {
      const byVisit = new Map(prev.map((a) => [a.service_visit_id, a]));
      for (const assignment of created) byVisit.set(assignment.service_visit_id, assignment);
      return Array.from(byVisit.values());
    });
    setVisits((prev) =>
      prev.map((visit) => {
        const match = created.find((a) => a.service_visit_id === visit.id);
        return match ? { ...visit, status: "assigned" } : visit;
      })
    );
  }

  function handleUnassigned(serviceVisitId: number) {
    setAssignments((prev) => prev.filter((a) => a.service_visit_id !== serviceVisitId));
    setVisits((prev) =>
      prev.map((visit) =>
        visit.id === serviceVisitId ? { ...visit, status: "unassigned" } : visit
      )
    );
  }

  function handlePinChanged(assignment: Assignment) {
    setAssignments((prev) =>
      prev.map((a) => (a.service_visit_id === assignment.service_visit_id ? assignment : a))
    );
  }

  const unassignedVisits = visits.filter((visit) => visit.status === "unassigned");
  const assignedVisits = visits.filter((visit) => visit.status === "assigned");

  if (loading) {
    return <div className="p-8 text-slate-500">Loading…</div>;
  }

  if (loadError) {
    return <div className="p-8 text-red-600">Failed to load data: {loadError}</div>;
  }

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <h1 className="text-2xl font-semibold text-slate-900">{VIEW_TITLES[view]}</h1>
        <nav className="flex gap-2">
          <button
            type="button"
            onClick={() => setView("assign")}
            className={`rounded-md px-3 py-1.5 text-sm font-medium ${
              view === "assign"
                ? "bg-slate-900 text-white"
                : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
            }`}
          >
            Manual Assignment
          </button>
          <button
            type="button"
            onClick={() => setView("planning")}
            className={`rounded-md px-3 py-1.5 text-sm font-medium ${
              view === "planning"
                ? "bg-slate-900 text-white"
                : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
            }`}
          >
            Day Planning
          </button>
          <button
            type="button"
            onClick={() => setView("optimize")}
            className={`rounded-md px-3 py-1.5 text-sm font-medium ${
              view === "optimize"
                ? "bg-slate-900 text-white"
                : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
            }`}
          >
            Optimize
          </button>
          <a
            href="/customer-portal.html"
            className="rounded-md px-3 py-1.5 text-sm font-medium bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
          >
            Customer Portal
          </a>
          <a
            href="/employee-management.html"
            className="rounded-md px-3 py-1.5 text-sm font-medium bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
          >
            Employee Management
          </a>
          <a
            href="/admin-portal.html"
            className="rounded-md px-3 py-1.5 text-sm font-medium bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
          >
            Admin Portal
          </a>
        </nav>
      </div>

      {view === "assign" && (
        <>
          <div className="flex flex-wrap items-center gap-2 mb-4 bg-white rounded-lg border border-slate-200 p-3">
            <label className="text-sm text-slate-500">
              Show visits requested before today through
            </label>
            <input
              type="date"
              value={visitsEndDate}
              onChange={(event) => setVisitsEndDate(event.target.value)}
              className="text-sm border border-slate-300 rounded-md px-2 py-1"
            />
            <button
              type="button"
              onClick={() => setVisitsEndDate(endOfCurrentWeek())}
              className="text-sm px-3 py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50"
            >
              This Week
            </button>
            <button
              type="button"
              onClick={() => setVisitsEndDate(fourWeeksOut())}
              className="text-sm px-3 py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50"
            >
              4 Weeks
            </button>
            {visitsLoading && <span className="text-xs text-slate-400">Refreshing…</span>}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
            <EmployeeList employees={employees} />
            <UnassignedVisitList
              visits={unassignedVisits}
              employees={employees}
              onAssigned={handleAssigned}
            />
            <AssignedVisitList
              visits={assignedVisits}
              assignments={assignments}
              onUnassigned={handleUnassigned}
              onPinChanged={handlePinChanged}
            />
          </div>
        </>
      )}
      {view === "planning" && (
        <DayPlanningView employees={employees} assignments={assignments} />
      )}
      {view === "optimize" && <OptimizeView onApplied={handleOptimizationApplied} />}
    </div>
  );
}

export default App;
