import { useEffect, useState } from "react";
import { listAssignments, listEmployees, listServiceVisits } from "./api";
import { AssignedVisitList } from "./components/AssignedVisitList";
import { EmployeeList } from "./components/EmployeeList";
import { UnassignedVisitList } from "./components/UnassignedVisitList";
import type { Assignment, Employee, ServiceVisit } from "./types";

function App() {
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
      <h1 className="text-2xl font-semibold text-slate-900 mb-6">Manual Assignment</h1>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <EmployeeList employees={employees} />
        <UnassignedVisitList
          visits={unassignedVisits}
          employees={employees}
          onAssigned={handleAssigned}
        />
        <AssignedVisitList visits={assignedVisits} assignments={assignments} />
      </div>
    </div>
  );
}

export default App;
