import { useEffect, useState } from "react";
import type { Contract, CustomerLocation } from "../types";
import { BackButton, DetailField } from "./DetailField";
import { ListTable } from "./ListTable";

interface Props {
  customerLocations: CustomerLocation[];
  contracts: Contract[];
  initialSelectedId?: number;
  onInitialSelectionConsumed?: () => void;
}

export function CustomerLocationsView({
  customerLocations,
  contracts,
  initialSelectedId,
  onInitialSelectionConsumed,
}: Props) {
  const [selected, setSelected] = useState<CustomerLocation | null>(() =>
    initialSelectedId !== undefined
      ? customerLocations.find((location) => location.id === initialSelectedId) ?? null
      : null
  );

  useEffect(() => {
    if (initialSelectedId !== undefined) {
      onInitialSelectionConsumed?.();
    }
  }, []);

  if (selected) {
    const locationLines = contracts.flatMap((contract) =>
      contract.lines.filter((line) => line.customer_location.id === selected.id)
    );
    return (
      <div>
        <BackButton label="Customer Locations" onClick={() => setSelected(null)} />
        <h2 className="text-xl font-semibold text-slate-900 mb-4">{selected.address}</h2>
        <DetailField label="Customer">{selected.customer.name}</DetailField>
        <DetailField label="Region">{selected.region?.name ?? "Not yet assigned"}</DetailField>
        <DetailField label="Coordinates">
          {selected.latitude !== null && selected.longitude !== null
            ? `${selected.latitude.toFixed(4)}, ${selected.longitude.toFixed(4)}`
            : "Not yet resolved"}
        </DetailField>
        <DetailField label="Contract Lines">
          {locationLines.length === 0 ? (
            "—"
          ) : (
            <ul className="space-y-1">
              {locationLines.map((line) => (
                <li key={line.id}>
                  Every {line.interval_days} days, {line.duration_minutes} min —{" "}
                  {line.required_skills.map((skill) => skill.name).join(", ") ||
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
          { header: "Region", render: (location) => location.region?.name ?? "—" },
        ]}
      />
    </div>
  );
}
