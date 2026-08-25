import { useState } from "react";
import type { Employee } from "../types";
import { BackButton, DetailField } from "./DetailField";
import { ListTable } from "./ListTable";

interface Props {
  employees: Employee[];
}

export function EmployeesView({ employees }: Props) {
  const [selected, setSelected] = useState<Employee | null>(null);

  if (selected) {
    return (
      <div>
        <BackButton label="Employees" onClick={() => setSelected(null)} />
        <h2 className="text-xl font-semibold text-slate-900 mb-4">{selected.name}</h2>
        <DetailField label="Work Hours">
          {selected.work_start.slice(0, 5)}–{selected.work_end.slice(0, 5)}
        </DetailField>
        <DetailField label="Location">
          {selected.latitude.toFixed(4)}, {selected.longitude.toFixed(4)}
        </DetailField>
        <DetailField label="Regions">
          {selected.regions.length === 0
            ? "—"
            : selected.regions.map((region) => region.name).join(", ")}
        </DetailField>
        <DetailField label="Skills">
          {selected.skills.length === 0
            ? "—"
            : selected.skills.map((skill) => skill.name).join(", ")}
        </DetailField>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-slate-900 mb-4">Employees</h2>
      <ListTable
        items={employees}
        getKey={(employee) => employee.id}
        onSelect={setSelected}
        emptyMessage="No employees."
        columns={[
          { header: "Name", render: (employee) => employee.name },
          {
            header: "Regions",
            render: (employee) =>
              employee.regions.map((region) => region.name).join(", ") || "—",
          },
          {
            header: "Skills",
            render: (employee) =>
              employee.skills.map((skill) => skill.name).join(", ") || "—",
          },
        ]}
      />
    </div>
  );
}
