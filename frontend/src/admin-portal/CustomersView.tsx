import { useState } from "react";
import { syncCustomersToResco } from "../api";
import type { Customer, RescoSyncSummary } from "../types";
import { BackButton, DetailField } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";

interface Props {
  customers: Customer[];
  onChanged: () => void | Promise<void>;
}

export function CustomersView({ customers, onChanged }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncSummary, setSyncSummary] = useState<RescoSyncSummary | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);

  const selected = customers.find((customer) => customer.id === selectedId) ?? null;

  async function handleSyncToResco() {
    setSyncing(true);
    setSyncError(null);
    setSyncSummary(null);
    try {
      const summary = await syncCustomersToResco();
      setSyncSummary(summary);
      await onChanged();
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Failed to sync to Resco");
    } finally {
      setSyncing(false);
    }
  }

  if (selected) {
    return (
      <div>
        <BackButton label="Customers" onClick={() => setSelectedId(null)} />
        <CustomerDetail customer={selected} />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900">Customers</h2>
        <button
          type="button"
          onClick={handleSyncToResco}
          disabled={syncing}
          className="text-sm px-3 py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50 disabled:opacity-50"
        >
          {syncing ? "Syncing…" : "Sync to Resco"}
        </button>
      </div>

      {syncError && <p className="text-sm text-red-600 mb-3">{syncError}</p>}
      {syncSummary && (
        <div className="mb-4 rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
          <div>
            Resco sync: {syncSummary.created} created, {syncSummary.updated} updated,{" "}
            {syncSummary.skipped} skipped, {syncSummary.failed} failed
          </div>
          {syncSummary.errors.length > 0 && (
            <ul className="mt-1 list-disc list-inside text-red-600">
              {syncSummary.errors.map((message, index) => (
                <li key={index}>{message}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      <ListTable
        items={customers}
        getKey={(customer) => customer.id}
        onSelect={(customer) => setSelectedId(customer.id)}
        emptyMessage="No customers."
        columns={[
          { header: "Name", render: (customer) => customer.name },
          { header: "Email", render: (customer) => customer.email || "—" },
          { header: "Phone", render: (customer) => customer.phone_number || "—" },
          {
            header: "Org Number",
            render: (customer) => customer.organization_number || "—",
          },
          {
            header: "Resco",
            render: (customer) => (customer.resco_account_id ? "Synced" : "—"),
          },
        ]}
      />
    </div>
  );
}

interface CustomerDetailProps {
  customer: Customer;
}

function CustomerDetail({ customer }: CustomerDetailProps) {
  return (
    <div>
      <h2 className="text-xl font-semibold text-slate-900 mb-4">{customer.name}</h2>
      <DetailField label="Email">{customer.email || "—"}</DetailField>
      <DetailField label="Phone">{customer.phone_number || "—"}</DetailField>
      <DetailField label="Organization Number">
        {customer.organization_number || "—"}
      </DetailField>
      <DetailField label="Resco Sync Status">
        {customer.resco_account_id ? "Synced" : "Not yet synced"}
      </DetailField>
    </div>
  );
}
