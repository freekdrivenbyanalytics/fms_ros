import { useEffect, useState } from "react";
import { listAssignments, listEmployees, listServiceVisits } from "./api";
import { AssignedVisitList } from "./components/AssignedVisitList";
import { DayPlanningView } from "./components/DayPlanningView";
import { EmployeeList } from "./components/EmployeeList";
import { UnassignedVisitList } from "./components/UnassignedVisitList";
import type { Assignment, Employee, ServiceVisit } from "./types";

type View = "assign" | "planning";

function App() {
  const [view, setView] = useState<View>("assign");
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [visits, setVisits] = useState<ServiceVisit[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([listEmployees(), listServiceVisits(), listAssignments()])
      .then(([employeesData, visitsData, assignmentsData]) => {
        setEmployees(employeesData);
        setVisits(visitsData);
        setAssignments(assignmentsData);
      })
      .catch((err) =>
        setLoadError(err instanceof Error ? err.message : "Failed to load data")
      )
      .finally(() => setLoading(false));
  }, []);

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
        <h1 className="text-2xl font-semibold text-slate-900">
          {view === "assign" ? "Manual Assignment" : "Day Planning"}
        </h1>
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
        </nav>
      </div>

      {view === "assign" ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          <EmployeeList employees={employees} />
          <UnassignedVisitList
            visits={unassignedVisits}
            employees={employees}
            onAssigned={handleAssigned}
          />
          <AssignedVisitList visits={assignedVisits} assignments={assignments} />
        </div>
      ) : (
        <DayPlanningView employees={employees} assignments={assignments} />
      )}
    </div>
  );
}

export default App;
