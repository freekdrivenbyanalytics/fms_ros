import { useState } from "react";
import type { Customer, CustomerLocation } from "../types";
import { BackButton, DetailField } from "./DetailField";
import { ListTable } from "./ListTable";

interface Props {
  customers: Customer[];
  customerLocations: CustomerLocation[];
  scopedCustomer?: Customer;
  onSelectLocation: (locationId: number) => void;
}

export function CustomersView({
  customers,
  customerLocations,
  scopedCustomer,
  onSelectLocation,
}: Props) {
  const [selected, setSelected] = useState<Customer | null>(null);

  if (scopedCustomer) {
    return (
      <CustomerDetail
        customer={scopedCustomer}
        customerLocations={customerLocations}
        onSelectLocation={onSelectLocation}
      />
    );
  }

  if (selected) {
    return (
      <div>
        <BackButton label="Customers" onClick={() => setSelected(null)} />
        <CustomerDetail
          customer={selected}
          customerLocations={customerLocations}
          onSelectLocation={onSelectLocation}
        />
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
        columns={[
          { header: "ID", render: (customer) => customer.id },
          { header: "Name", render: (customer) => customer.name },
        ]}
      />
    </div>
  );
}

interface CustomerDetailProps {
  customer: Customer;
  customerLocations: CustomerLocation[];
  onSelectLocation: (locationId: number) => void;
}

function CustomerDetail({ customer, customerLocations, onSelectLocation }: CustomerDetailProps) {
  const locations = customerLocations.filter(
    (location) => location.customer.id === customer.id
  );

  return (
    <div>
      <h2 className="text-xl font-semibold text-slate-900 mb-4">{customer.name}</h2>
      <DetailField label="ID">{customer.id}</DetailField>
      <DetailField label="Customer Locations">
        {locations.length === 0 ? (
          "—"
        ) : (
          <ul className="space-y-1">
            {locations.map((location) => (
              <li key={location.id}>
                <button
                  type="button"
                  onClick={() => onSelectLocation(location.id)}
                  className="text-sky-700 hover:underline"
                >
                  {location.address} ({location.region.name})
                </button>
              </li>
            ))}
          </ul>
        )}
      </DetailField>
    </div>
  );
}
