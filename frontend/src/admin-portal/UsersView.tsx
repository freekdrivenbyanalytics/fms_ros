import { useState, type FormEvent } from "react";
import { resetUserPassword, updateUserAdmin, updateUserCustomers } from "../api";
import type { Customer, User } from "../types";
import { BackButton, DetailField } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";

interface Props {
  users: User[];
  customers: Customer[];
  onChanged: () => void | Promise<void>;
}

export function UsersView({ users, customers, onChanged }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const selected = users.find((user) => user.id === selectedId) ?? null;

  if (selected) {
    return (
      <UserDetail
        user={selected}
        customers={customers}
        onChanged={onChanged}
        onBack={() => setSelectedId(null)}
      />
    );
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-slate-900 mb-4">Users</h2>
      <ListTable
        items={users}
        getKey={(user) => user.id}
        onSelect={(user) => setSelectedId(user.id)}
        emptyMessage="No users."
        columns={[
          { header: "Email", render: (user) => user.email },
          { header: "Admin", render: (user) => (user.is_admin ? "Yes" : "No") },
          {
            header: "Assigned customers",
            render: (user) => String(user.customer_ids.length),
          },
        ]}
      />
    </div>
  );
}

interface UserDetailProps {
  user: User;
  customers: Customer[];
  onChanged: () => void | Promise<void>;
  onBack: () => void;
}

function UserDetail({ user, customers, onChanged, onBack }: UserDetailProps) {
  const [customerIds, setCustomerIds] = useState<number[]>(user.customer_ids);
  const [isAdmin, setIsAdmin] = useState(user.is_admin);
  const [savingCustomers, setSavingCustomers] = useState(false);
  const [savingAdmin, setSavingAdmin] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggleCustomer(id: number) {
    setCustomerIds((prev) =>
      prev.includes(id) ? prev.filter((existing) => existing !== id) : [...prev, id]
    );
  }

  async function handleSaveCustomers() {
    setSavingCustomers(true);
    setError(null);
    try {
      await updateUserCustomers(user.id, { customer_ids: customerIds });
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update assigned customers");
    } finally {
      setSavingCustomers(false);
    }
  }

  async function handleToggleAdmin() {
    setSavingAdmin(true);
    setError(null);
    try {
      const next = !isAdmin;
      await updateUserAdmin(user.id, next);
      setIsAdmin(next);
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update admin status");
    } finally {
      setSavingAdmin(false);
    }
  }

  return (
    <div>
      <BackButton label="Users" onClick={onBack} />
      <h2 className="text-xl font-semibold text-slate-900 mb-4">{user.email}</h2>

      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      <DetailField label="Admin">
        <button
          type="button"
          onClick={handleToggleAdmin}
          disabled={savingAdmin}
          className="text-sm px-3 py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50 disabled:opacity-50"
        >
          {savingAdmin ? "Saving…" : isAdmin ? "Revoke admin" : "Grant admin"}
        </button>
      </DetailField>

      <DetailField label="Assigned customers">
        <div className="max-h-64 overflow-y-auto space-y-1 mb-2">
          {customers.map((customer) => (
            <label key={customer.id} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={customerIds.includes(customer.id)}
                onChange={() => toggleCustomer(customer.id)}
              />
              {customer.name}
            </label>
          ))}
        </div>
        <button
          type="button"
          onClick={handleSaveCustomers}
          disabled={savingCustomers}
          className="text-sm px-3 py-1.5 rounded-md bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-50"
        >
          {savingCustomers ? "Saving…" : "Save assigned customers"}
        </button>
      </DetailField>

      <DetailField label="Reset password">
        <ResetPasswordForm userId={user.id} />
      </DetailField>
    </div>
  );
}

interface ResetPasswordFormProps {
  userId: number;
}

function ResetPasswordForm({ userId }: ResetPasswordFormProps) {
  const [password, setPassword] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!password) return;
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await resetUserPassword(userId, password);
      setMessage("Password reset.");
      setPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reset password");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-center gap-2">
      <input
        type="password"
        placeholder="New password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        className="text-sm border border-slate-300 rounded-md px-2 py-1"
        required
      />
      <button
        type="submit"
        disabled={saving}
        className="text-sm px-3 py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50 disabled:opacity-50"
      >
        {saving ? "Saving…" : "Reset password"}
      </button>
      {message && <span className="text-xs text-emerald-700">{message}</span>}
      {error && <span className="text-xs text-red-600">{error}</span>}
    </form>
  );
}
