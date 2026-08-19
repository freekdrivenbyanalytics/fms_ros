import type { Employee } from "../types";

export function EmployeeList({ employees }: { employees: Employee[] }) {
  return (
    <section className="bg-white rounded-lg border border-slate-200 p-4">
      <h2 className="text-lg font-medium text-slate-900 mb-3">Employees</h2>
      {employees.length === 0 ? (
        <p className="text-sm text-slate-500">No employees.</p>
      ) : (
        <ul className="space-y-2">
          {employees.map((employee) => (
            <li key={employee.id} className="text-sm">
              <div className="font-medium text-slate-800">{employee.name}</div>
              <div className="text-slate-500">
                {employee.work_start.slice(0, 5)}–{employee.work_end.slice(0, 5)}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
