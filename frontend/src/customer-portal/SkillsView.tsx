import { useState } from "react";
import type { Contract, Skill } from "../types";
import { BackButton, DetailField } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";

interface Props {
  skills: Skill[];
  contracts: Contract[];
}

export function SkillsView({ skills, contracts }: Props) {
  const [selected, setSelected] = useState<Skill | null>(null);

  if (selected) {
    const skillLines = contracts.flatMap((contract) =>
      contract.lines.filter((line) =>
        line.required_skills.some((skill) => skill.id === selected.id)
      )
    );
    return (
      <div>
        <BackButton label="Skills" onClick={() => setSelected(null)} />
        <h2 className="text-xl font-semibold text-slate-900 mb-4">{selected.name}</h2>
        <DetailField label="Contract lines requiring this skill">
          {skillLines.length === 0 ? (
            "—"
          ) : (
            <ul className="space-y-1">
              {skillLines.map((line) => (
                <li key={line.id}>
                  {line.customer_location.customer.name} — {line.customer_location.address}
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
