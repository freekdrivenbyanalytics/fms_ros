import { useState } from "react";
import type { Customer } from "../types";
import { BackButton } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";
import { CustomerDashboard } from "./CustomerDashboard";

interface Props {
  customers: Customer[];
  onRefresh: () => void;
  refreshing: boolean;
}

export function CustomersView({ customers, onRefresh, refreshing }: Props) {
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
