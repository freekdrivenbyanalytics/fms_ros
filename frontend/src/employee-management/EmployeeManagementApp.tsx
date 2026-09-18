import { useEffect, useState } from "react";
import { listEmployees, listRegions, listSkills, logout } from "../api";
import { useRequireRole } from "../shared/auth";
import type { Employee, Region, Skill } from "../types";
import { EmployeesView } from "./EmployeesView";

async function handleLogout() {
  await logout();
  window.location.href = "/login.html";
}

export function EmployeeManagementApp() {
  const { loading: authLoading } = useRequireRole("admin");
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [viewingAsEmployeeId, setViewingAsEmployeeId] = useState<number | null>(null);

  async function reload() {
    const [employeesData, regionsData, skillsData] = await Promise.all([
      listEmployees(),
      listRegions(),
      listSkills(),
    ]);
    setEmployees(employeesData);
    setRegions(regionsData);
    setSkills(skillsData);
  }

  useEffect(() => {
    reload()
      .catch((err) => setLoadError(err instanceof Error ? err.message : "Failed to load data"))
      .finally(() => setLoading(false));
  }, []);

  if (authLoading || loading) {
    return <div className="p-8 text-slate-500">Loading…</div>;
  }

  if (loadError) {
    return <div className="p-8 text-red-600">Failed to load data: {loadError}</div>;
  }

  const visibleEmployees =
    viewingAsEmployeeId === null
      ? employees
      : employees.filter((employee) => employee.id === viewingAsEmployeeId);

  return (
    <div className="min-h-screen bg-slate-50 flex">
      <aside className="w-56 shrink-0 bg-white border-r border-slate-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-lg font-semibold text-slate-900">Employee Management</h1>
          <button
            type="button"
            onClick={handleLogout}
            className="text-xs text-slate-500 hover:text-slate-800 underline"
          >
            Log out
          </button>
        </div>

        <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">
          Viewing as
        </label>
        <select
          value={viewingAsEmployeeId ?? ""}
          onChange={(event) =>
            setViewingAsEmployeeId(
              event.target.value === "" ? null : Number(event.target.value)
            )
          }
          className="w-full text-sm border border-slate-300 rounded-md px-2 py-1 mb-4"
        >
          <option value="">All employees</option>
          {employees.map((employee) => (
            <option key={employee.id} value={employee.id}>
              {employee.name}
            </option>
          ))}
        </select>

        <div className="mt-2 pt-4 border-t border-slate-200">
          <div className="text-xs uppercase tracking-wide text-slate-400 mb-2 px-3">
            Other portals
          </div>
          <nav className="flex flex-col gap-1">
            <a
              href="/index.html"
              className="text-left rounded-md px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
            >
              Planning
            </a>
            <a
              href="/customer-portal.html"
              className="text-left rounded-md px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
            >
              Customer Portal
            </a>
            <a
              href="/admin-portal.html"
              className="text-left rounded-md px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
            >
              Admin Portal
            </a>
          </nav>
        </div>
      </aside>
      <main className="flex-1 p-8">
        <EmployeesView
          employees={visibleEmployees}
          regions={regions}
          skills={skills}
          onChanged={reload}
        />
      </main>
    </div>
  );
}
