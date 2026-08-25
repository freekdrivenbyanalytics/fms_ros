import { useState } from "react";
import type { Customer, CustomerLocation } from "../types";
import { BackButton, DetailField } from "./DetailField";
import { ListTable } from "./ListTable";

interface Props {
  customers: Customer[];
  customerLocations: CustomerLocation[];
}

export function CustomersView({ customers, customerLocations }: Props) {
  const [selected, setSelected] = useState<Customer | null>(null);

  if (selected) {
    const locations = customerLocations.filter(
      (location) => location.customer.id === selected.id
    );
    return (
      <div>
        <BackButton label="Customers" onClick={() => setSelected(null)} />
        <h2 className="text-xl font-semibold text-slate-900 mb-4">{selected.name}</h2>
        <DetailField label="Customer Locations">
          {locations.length === 0 ? (
            "—"
          ) : (
            <ul className="space-y-1">
              {locations.map((location) => (
                <li key={location.id}>
                  {location.address} ({location.region.name})
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
      <h2 className="text-xl font-semibold text-slate-900 mb-4">Customers</h2>
      <ListTable
        items={customers}
        getKey={(customer) => customer.id}
        onSelect={setSelected}
        emptyMessage="No customers."
        columns={[{ header: "Name", render: (customer) => customer.name }]}
      />
    </div>
  );
}
