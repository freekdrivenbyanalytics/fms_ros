import { useState } from "react";
import type { Customer, CustomerLocation } from "../types";
import { BackButton, DetailField } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";

interface Props {
  customers: Customer[];
  customerLocations: CustomerLocation[];
  scopedCustomer?: Customer;
  onSelectLocation: (locationId: number) => void;
  onRefresh: () => void;
  refreshing: boolean;
}

export function CustomersView({
  customers,
  customerLocations,
  scopedCustomer,
  onSelectLocation,
  onRefresh,
  refreshing,
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
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900">Customers</h2>
        <button
          type="button"
          onClick={onRefresh}
          disabled={refreshing}
          className="text-sm px-3 py-1.5 rounded-md bg-slate-900 text-white hover:bg-slate-700 disabled:opacity-50"
        >
          {refreshing ? "Refreshing…" : "Refresh"}
        </button>
      </div>
      <ListTable
        items={customers}
        getKey={(customer) => customer.id}
        onSelect={setSelected}
        emptyMessage="No customers."
        columns={[
          { header: "ID", render: (customer) => customer.id },
          { header: "Name", render: (customer) => customer.name },
          { header: "Customer #", render: (customer) => customer.customer_number ?? "—" },
          { header: "Email", render: (customer) => customer.email || "—" },
          { header: "Phone", render: (customer) => customer.phone_number || "—" },
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
      <DetailField label="Customer Number">{customer.customer_number ?? "—"}</DetailField>
      <DetailField label="Organization Number">
        {customer.organization_number || "—"}
      </DetailField>
      <DetailField label="Email">{customer.email || "—"}</DetailField>
      <DetailField label="Invoice Email">{customer.invoice_email || "—"}</DetailField>
      <DetailField label="Phone">{customer.phone_number || "—"}</DetailField>
      <DetailField label="Mobile">{customer.phone_number_mobile || "—"}</DetailField>
      <DetailField label="Language">{customer.language || "—"}</DetailField>
      <DetailField label="Type">
        {[
          customer.is_customer ? "Customer" : null,
          customer.is_supplier ? "Supplier" : null,
          customer.is_inactive ? "Inactive" : null,
        ]
          .filter(Boolean)
          .join(", ") || "—"}
      </DetailField>
      <DetailField label="Website">{customer.website || "—"}</DetailField>
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
                  {location.address} ({location.region?.name ?? "region not yet assigned"})
                </button>
              </li>
            ))}
          </ul>
        )}
      </DetailField>
    </div>
  );
}
