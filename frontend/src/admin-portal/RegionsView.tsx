import { useState, type FormEvent } from "react";
import { createRegion, deleteRegion, updateRegion } from "../api";
import type { CustomerLocation, Employee, GeoPoint, Region } from "../types";
import { BackButton, DetailField } from "../shared/DetailField";
import { GeoShapeEditor } from "../shared/GeoShapeEditor";
import { ListTable } from "../shared/ListTable";

interface Props {
  regions: Region[];
  employees: Employee[];
  customerLocations: CustomerLocation[];
  onChanged: () => void | Promise<void>;
}

export function RegionsView({ regions, employees, customerLocations, onChanged }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);

  const selected = regions.find((region) => region.id === selectedId) ?? null;

  if (selected) {
    const regionEmployees = employees.filter((employee) =>
      employee.regions.some((region) => region.id === selected.id)
    );
    const regionLocations = customerLocations.filter(
      (location) => location.region?.id === selected.id
    );
    return (
      <RegionDetail
        region={selected}
        regionEmployees={regionEmployees}
        regionLocations={regionLocations}
        onChanged={onChanged}
        onDeleted={() => setSelectedId(null)}
        onBack={() => setSelectedId(null)}
      />
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900">Regions</h2>
        <button
          type="button"
          onClick={() => setCreating((prev) => !prev)}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white"
        >
          {creating ? "Cancel" : "Create Region"}
        </button>
      </div>

      {creating && (
        <CreateRegionForm
          onCreated={async (region) => {
            setCreating(false);
            await onChanged();
            setSelectedId(region.id);
          }}
        />
      )}

      <ListTable
        items={regions}
        getKey={(region) => region.id}
        onSelect={(region) => setSelectedId(region.id)}
        emptyMessage="No regions."
        columns={[
          { header: "Name", render: (region) => region.name },
          {
            header: "Geo-shape",
            render: (region) => (region.geo_shape ? `${region.geo_shape.length} points` : "—"),
          },
          {
            header: "Employees",
            render: (region) =>
              String(employees.filter((e) => e.regions.some((r) => r.id === region.id)).length),
          },
          {
            header: "Customer Locations",
            render: (region) =>
              String(customerLocations.filter((l) => l.region?.id === region.id).length),
          },
        ]}
      />
    </div>
  );
}

interface CreateRegionFormProps {
  onCreated: (region: Region) => void | Promise<void>;
}

function CreateRegionForm({ onCreated }: CreateRegionFormProps) {
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!name) return;
    setSubmitting(true);
    setError(null);
    try {
      const region = await createRegion({ name, geo_shape: null });
      await onCreated(region);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create region");
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

interface RegionDetailProps {
  region: Region;
  regionEmployees: Employee[];
  regionLocations: CustomerLocation[];
  onChanged: () => void | Promise<void>;
  onDeleted: () => void;
  onBack: () => void;
}

function RegionDetail({
  region,
  regionEmployees,
  regionLocations,
  onChanged,
  onDeleted,
  onBack,
}: RegionDetailProps) {
  const [name, setName] = useState(region.name);
  const [geoShape, setGeoShape] = useState<GeoPoint[] | null>(region.geo_shape);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await updateRegion(region.id, { name, geo_shape: geoShape });
      setDirty(false);
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save region");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    setError(null);
    try {
      await deleteRegion(region.id);
      await onChanged();
      onDeleted();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete region");
      setDeleting(false);
    }
  }

  return (
    <div>
      <BackButton label="Regions" onClick={onBack} />
      <div className="flex items-center justify-between mb-4">
        <input
          type="text"
          value={name}
          onChange={(event) => {
            setName(event.target.value);
            setDirty(true);
          }}
          className="text-xl font-semibold text-slate-900 border border-transparent hover:border-slate-300 focus:border-slate-300 rounded-md px-1 -ml-1"
        />
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
            {deleting ? "Deleting…" : "Soft-delete Region"}
          </button>
        </div>
      </div>
      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      <DetailField label="Geo-shape">
        <GeoShapeEditor
          value={region.geo_shape}
          onChange={(points) => {
            setGeoShape(points);
            setDirty(true);
          }}
        />
      </DetailField>

      <DetailField label="Employees scoped to this region">
        {regionEmployees.length === 0
          ? "—"
          : regionEmployees.map((employee) => employee.name).join(", ")}
      </DetailField>
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
