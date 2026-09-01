import { useState } from "react";
import type { CustomerLocation, Region } from "../types";
import { BackButton, DetailField } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";

interface Props {
  regions: Region[];
  customerLocations: CustomerLocation[];
}

export function RegionsView({ regions, customerLocations }: Props) {
  const [selected, setSelected] = useState<Region | null>(null);

  if (selected) {
    const regionLocations = customerLocations.filter(
      (location) => location.region?.id === selected.id
    );
    return (
      <div>
        <BackButton label="Regions" onClick={() => setSelected(null)} />
        <h2 className="text-xl font-semibold text-slate-900 mb-4">{selected.name}</h2>
        <DetailField label="Customer Locations in this region">
          {regionLocations.length === 0 ? (
            "—"
          ) : (
            <ul className="space-y-1">
              {regionLocations.map((location) => (
                <li key={location.id}>
                  {location.customer.name} — {location.address}
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
      <h2 className="text-xl font-semibold text-slate-900 mb-4">Regions</h2>
      <ListTable
        items={regions}
        getKey={(region) => region.id}
        onSelect={setSelected}
        emptyMessage="No regions."
        columns={[{ header: "Name", render: (region) => region.name }]}
      />
    </div>
  );
}
