import { useState } from "react";
import type { Contract, CustomerLocation } from "../types";
import { BackButton, DetailField } from "./DetailField";
import { ListTable } from "./ListTable";

interface Props {
  customerLocations: CustomerLocation[];
  contracts: Contract[];
}

export function CustomerLocationsView({ customerLocations, contracts }: Props) {
  const [selected, setSelected] = useState<CustomerLocation | null>(null);

  if (selected) {
    const locationContracts = contracts.filter(
      (contract) => contract.customer_location.id === selected.id
    );
    return (
      <div>
        <BackButton label="Customer Locations" onClick={() => setSelected(null)} />
        <h2 className="text-xl font-semibold text-slate-900 mb-4">{selected.address}</h2>
        <DetailField label="Customer">{selected.customer.name}</DetailField>
        <DetailField label="Region">{selected.region.name}</DetailField>
        <DetailField label="Coordinates">
          {selected.latitude.toFixed(4)}, {selected.longitude.toFixed(4)}
        </DetailField>
        <DetailField label="Contracts">
          {locationContracts.length === 0 ? (
            "—"
          ) : (
            <ul className="space-y-1">
              {locationContracts.map((contract) => (
                <li key={contract.id}>
                  Every {contract.interval_days} days, {contract.duration_minutes} min —{" "}
                  {contract.required_skills.map((skill) => skill.name).join(", ") ||
                    "no skills required"}
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
      <h2 className="text-xl font-semibold text-slate-900 mb-4">Customer Locations</h2>
      <ListTable
        items={customerLocations}
        getKey={(location) => location.id}
        onSelect={setSelected}
        emptyMessage="No customer locations."
        columns={[
          { header: "Address", render: (location) => location.address },
          { header: "Customer", render: (location) => location.customer.name },
          { header: "Region", render: (location) => location.region.name },
        ]}
      />
    </div>
  );
}
