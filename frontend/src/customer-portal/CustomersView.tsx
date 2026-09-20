import { useState } from "react";
import type { Customer } from "../types";
import { BackButton } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";
import { CustomerDashboard } from "./CustomerDashboard";

interface Props {
  customers: Customer[];
}

export function CustomersView({ customers }: Props) {
  const [selected, setSelected] = useState<Customer | null>(null);

  if (selected) {
    return (
      <div>
        <BackButton label="Customers" onClick={() => setSelected(null)} />
        <CustomerDashboard customerId={selected.id} />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900">Customers</h2>
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
