import { useState } from "react";
import type { Contract } from "../types";
import { BackButton, DetailField } from "./DetailField";
import { ListTable } from "./ListTable";

interface Props {
  contracts: Contract[];
}

export function ContractsView({ contracts }: Props) {
  const [selected, setSelected] = useState<Contract | null>(null);

  if (selected) {
    return (
      <div>
        <BackButton label="Contracts" onClick={() => setSelected(null)} />
        <h2 className="text-xl font-semibold text-slate-900 mb-4">
          Contract #{selected.id} — {selected.customer_location.customer.name}
        </h2>
        <DetailField label="Customer Location">
          {selected.customer_location.address} ({selected.customer_location.region?.name ?? "region not yet assigned"})
        </DetailField>
        <DetailField label="Start Date">{selected.start_date}</DetailField>
        <DetailField label="Interval">Every {selected.interval_days} days</DetailField>
        <DetailField label="Duration">{selected.duration_minutes} minutes</DetailField>
        <DetailField label="Required Skills">
          {selected.required_skills.length === 0
            ? "—"
            : selected.required_skills.map((skill) => skill.name).join(", ")}
        </DetailField>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-slate-900 mb-4">Contracts</h2>
      <ListTable
        items={contracts}
        getKey={(contract) => contract.id}
        onSelect={setSelected}
        emptyMessage="No contracts."
        columns={[
          { header: "Customer", render: (contract) => contract.customer_location.customer.name },
          { header: "Location", render: (contract) => contract.customer_location.address },
          { header: "Interval", render: (contract) => `${contract.interval_days}d` },
          { header: "Duration", render: (contract) => `${contract.duration_minutes} min` },
          {
            header: "Required Skills",
            render: (contract) =>
              contract.required_skills.map((skill) => skill.name).join(", ") || "—",
          },
        ]}
      />
    </div>
  );
}
