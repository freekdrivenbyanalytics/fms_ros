import { useState, type FormEvent } from "react";
import { createCustomer, deleteCustomer, syncCustomersToResco, updateCustomer } from "../api";
import type { Customer, RescoSyncSummary } from "../types";
import { BackButton, DetailField } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";

interface Props {
  customers: Customer[];
  onChanged: () => void | Promise<void>;
}

export function CustomersView({ customers, onChanged }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);
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
      <CustomerDetail
        customer={selected}
        onChanged={onChanged}
        onDeleted={() => setSelectedId(null)}
        onBack={() => setSelectedId(null)}
      />
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900">Customers</h2>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleSyncToResco}
            disabled={syncing}
            className="text-sm px-3 py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50 disabled:opacity-50"
          >
            {syncing ? "Syncing…" : "Sync to Resco"}
          </button>
          <button
            type="button"
            onClick={() => setCreating((prev) => !prev)}
            className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white"
          >
            {creating ? "Cancel" : "Create Customer"}
          </button>
        </div>
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

      {creating && (
        <CreateCustomerForm
          onCreated={async (customer) => {
            setCreating(false);
            await onChanged();
            setSelectedId(customer.id);
          }}
        />
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

interface CreateCustomerFormProps {
  onCreated: (customer: Customer) => void | Promise<void>;
}

function CreateCustomerForm({ onCreated }: CreateCustomerFormProps) {
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!name) return;
    setSubmitting(true);
    setError(null);
    try {
      const customer = await createCustomer({ name });
      await onCreated(customer);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create customer");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mb-4 flex flex-wrap items-end gap-2 rounded-md border border-slate-200 bg-white p-3"
    >
      <div>
        <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">Name</label>
        <input
          type="text"
          value={name}
          onChange={(event) => setName(event.target.value)}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
          required
        />
      </div>
      <button
        type="submit"
        disabled={submitting}
        className="text-sm px-3 py-1.5 rounded-md bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-50"
      >
        {submitting ? "Creating…" : "Create"}
      </button>
      {error && <p className="text-xs text-red-600 w-full">{error}</p>}
    </form>
  );
}

interface CustomerDetailProps {
  customer: Customer;
  onChanged: () => void | Promise<void>;
  onDeleted: () => void;
  onBack: () => void;
}

function CustomerDetail({ customer, onChanged, onDeleted, onBack }: CustomerDetailProps) {
  const [name, setName] = useState(customer.name);
  const [email, setEmail] = useState(customer.email ?? "");
  const [phoneNumber, setPhoneNumber] = useState(customer.phone_number ?? "");
  const [organizationNumber, setOrganizationNumber] = useState(
    customer.organization_number ?? ""
  );
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await updateCustomer(customer.id, {
        name,
        email: email || null,
        phone_number: phoneNumber || null,
        organization_number: organizationNumber || null,
      });
      setDirty(false);
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save customer");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    setError(null);
    try {
      await deleteCustomer(customer.id);
      await onChanged();
      onDeleted();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete customer");
      setDeleting(false);
    }
  }

  return (
    <div>
      <BackButton label="Customers" onClick={onBack} />
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900">{customer.name}</h2>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleSave}
            disabled={saving || !dirty}
            className="text-sm px-3 py-1.5 rounded-md bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save Changes"}
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={deleting}
            className="text-sm px-3 py-1.5 rounded-md border border-red-300 text-red-700 hover:bg-red-50 disabled:opacity-50"
          >
            {deleting ? "Deleting…" : "Soft-delete Customer"}
          </button>
        </div>
      </div>
      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      <DetailField label="Name">
        <input
          type="text"
          value={name}
          onChange={(event) => {
            setName(event.target.value);
            setDirty(true);
          }}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
        />
      </DetailField>
      <DetailField label="Email">
        <input
          type="text"
          value={email}
          onChange={(event) => {
            setEmail(event.target.value);
            setDirty(true);
          }}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
        />
      </DetailField>
      <DetailField label="Phone">
        <input
          type="text"
          value={phoneNumber}
          onChange={(event) => {
            setPhoneNumber(event.target.value);
            setDirty(true);
          }}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
        />
      </DetailField>
      <DetailField label="Organization Number">
        <input
          type="text"
          value={organizationNumber}
          onChange={(event) => {
            setOrganizationNumber(event.target.value);
            setDirty(true);
          }}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
        />
      </DetailField>
      <DetailField label="Resco Sync Status">
        {customer.resco_account_id ? "Synced" : "Not yet synced"}
      </DetailField>
    </div>
  );
}
