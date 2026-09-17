import { useState, type FormEvent } from "react";
import { createServiceOrderType, deleteServiceOrderType, updateServiceOrderType } from "../api";
import type { Product, ServiceOrderType } from "../types";
import { BackButton, DetailField } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";

interface Props {
  serviceOrderTypes: ServiceOrderType[];
  products: Product[];
  onChanged: () => void | Promise<void>;
}

export function ServiceOrderTypesView({ serviceOrderTypes, products, onChanged }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);

  const selected = serviceOrderTypes.find((type) => type.id === selectedId) ?? null;

  if (selected) {
    const typeProducts = products.filter(
      (product) => product.service_order_type?.id === selected.id
    );
    return (
      <ServiceOrderTypeDetail
        serviceOrderType={selected}
        typeProducts={typeProducts}
        onChanged={onChanged}
        onDeleted={() => setSelectedId(null)}
        onBack={() => setSelectedId(null)}
      />
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900">Service Order Types</h2>
        <button
          type="button"
          onClick={() => setCreating((prev) => !prev)}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white"
        >
          {creating ? "Cancel" : "Create Service Order Type"}
        </button>
      </div>

      {creating && (
        <CreateServiceOrderTypeForm
          onCreated={async (serviceOrderType) => {
            setCreating(false);
            await onChanged();
            setSelectedId(serviceOrderType.id);
          }}
        />
      )}

      <ListTable
        items={serviceOrderTypes}
        getKey={(type) => type.id}
        onSelect={(type) => setSelectedId(type.id)}
        emptyMessage="No service order types."
        columns={[
          { header: "Name", render: (type) => type.name },
          {
            header: "Products",
            render: (type) =>
              String(products.filter((p) => p.service_order_type?.id === type.id).length),
          },
        ]}
      />
    </div>
  );
}

interface CreateServiceOrderTypeFormProps {
  onCreated: (serviceOrderType: ServiceOrderType) => void | Promise<void>;
}

function CreateServiceOrderTypeForm({ onCreated }: CreateServiceOrderTypeFormProps) {
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!name) return;
    setSubmitting(true);
    setError(null);
    try {
      const serviceOrderType = await createServiceOrderType({ name });
      await onCreated(serviceOrderType);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create service order type");
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

interface ServiceOrderTypeDetailProps {
  serviceOrderType: ServiceOrderType;
  typeProducts: Product[];
  onChanged: () => void | Promise<void>;
  onDeleted: () => void;
  onBack: () => void;
}

function ServiceOrderTypeDetail({
  serviceOrderType,
  typeProducts,
  onChanged,
  onDeleted,
  onBack,
}: ServiceOrderTypeDetailProps) {
  const [name, setName] = useState(serviceOrderType.name);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await updateServiceOrderType(serviceOrderType.id, { name });
      setDirty(false);
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save service order type");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    setError(null);
    try {
      await deleteServiceOrderType(serviceOrderType.id);
      await onChanged();
      onDeleted();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete service order type");
      setDeleting(false);
    }
  }

  return (
    <div>
      <BackButton label="Service Order Types" onClick={onBack} />
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900">{serviceOrderType.name}</h2>
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
            {deleting ? "Deleting…" : "Soft-delete Service Order Type"}
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

      <DetailField label="Products assigned this service order type">
        {typeProducts.length === 0
          ? "—"
          : typeProducts.map((product) => `${product.number} ${product.name}`).join(", ")}
      </DetailField>
    </div>
  );
}
