import { useState } from "react";
import type { Contract, Employee, Skill } from "../types";
import { BackButton, DetailField } from "./DetailField";
import { ListTable } from "./ListTable";

interface Props {
  skills: Skill[];
  employees: Employee[];
  contracts: Contract[];
}

export function SkillsView({ skills, employees, contracts }: Props) {
  const [selected, setSelected] = useState<Skill | null>(null);

  if (selected) {
    const skillEmployees = employees.filter((employee) =>
      employee.skills.some((skill) => skill.id === selected.id)
    );
    const skillContracts = contracts.filter((contract) =>
      contract.required_skills.some((skill) => skill.id === selected.id)
    );
    return (
      <div>
        <BackButton label="Skills" onClick={() => setSelected(null)} />
        <h2 className="text-xl font-semibold text-slate-900 mb-4">{selected.name}</h2>
        <DetailField label="Employees with this skill">
          {skillEmployees.length === 0
            ? "—"
            : skillEmployees.map((employee) => employee.name).join(", ")}
        </DetailField>
        <DetailField label="Contracts requiring this skill">
          {skillContracts.length === 0 ? (
            "—"
          ) : (
            <ul className="space-y-1">
              {skillContracts.map((contract) => (
                <li key={contract.id}>
                  {contract.customer_location.customer.name} —{" "}
                  {contract.customer_location.address}
                </li>
              ))}
            </ul>
          )}
        </DetailField>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-slate-900 mb-4">Skills</h2>
      <ListTable
        items={skills}
        getKey={(skill) => skill.id}
        onSelect={setSelected}
        emptyMessage="No skills."
        columns={[{ header: "Name", render: (skill) => skill.name }]}
      />
    </div>
  );
}
