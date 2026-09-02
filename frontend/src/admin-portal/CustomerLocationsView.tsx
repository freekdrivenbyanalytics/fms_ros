import { useState, type FormEvent } from "react";
import { updateCustomerLocationCoordinates } from "../api";
import type { CustomerLocation } from "../types";
import { BackButton, DetailField } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";

interface Props {
  customerLocations: CustomerLocation[];
  onChanged: () => void | Promise<void>;
}

export function CustomerLocationsView({ customerLocations, onChanged }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const selected = customerLocations.find((location) => location.id === selectedId) ?? null;

  if (selected) {
    return (
      <CustomerLocationDetail
        location={selected}
        onChanged={onChanged}
        onBack={() => setSelectedId(null)}
      />
    );
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-slate-900 mb-4">Customer Locations</h2>
      <ListTable
        items={customerLocations}
        getKey={(location) => location.id}
        onSelect={(location) => setSelectedId(location.id)}
        emptyMessage="No customer locations."
        columns={[
          { header: "Address", render: (location) => location.address },
          { header: "Customer", render: (location) => location.customer.name },
          { header: "Region", render: (location) => location.region?.name ?? "—" },
          {
            header: "Coordinates Locked",
            render: (location) => (location.coordinates_locked ? "Yes" : "No"),
          },
        ]}
      />
    </div>
  );
}

interface CustomerLocationDetailProps {
  location: CustomerLocation;
  onChanged: () => void | Promise<void>;
  onBack: () => void;
}

function CustomerLocationDetail({ location, onChanged, onBack }: CustomerLocationDetailProps) {
  const [latitude, setLatitude] = useState(
    location.latitude !== null ? String(location.latitude) : ""
  );
  const [longitude, setLongitude] = useState(
    location.longitude !== null ? String(location.longitude) : ""
  );
  const [coordinatesLocked, setCoordinatesLocked] = useState(location.coordinates_locked);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!latitude || !longitude) return;
    setSaving(true);
    setError(null);
    try {
      await updateCustomerLocationCoordinates(location.id, {
        latitude: Number(latitude),
        longitude: Number(longitude),
        coordinates_locked: coordinatesLocked,
      });
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save coordinates");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <BackButton label="Customer Locations" onClick={onBack} />
      <h2 className="text-xl font-semibold text-slate-900 mb-4">{location.address}</h2>

      <DetailField label="Customer">{location.customer.name}</DetailField>
      <DetailField label="Region">{location.region?.name ?? "Not yet assigned"}</DetailField>

      <DetailField label="Coordinates">
        <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-2">
          <div>
            <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">
              Latitude
            </label>
            <input
              type="number"
              step="any"
              value={latitude}
              onChange={(event) => setLatitude(event.target.value)}
              className="text-sm border border-slate-300 rounded-md px-2 py-1 w-36"
              required
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">
              Longitude
            </label>
            <input
              type="number"
              step="any"
              value={longitude}
              onChange={(event) => setLongitude(event.target.value)}
              className="text-sm border border-slate-300 rounded-md px-2 py-1 w-36"
              required
            />
          </div>
          <label className="flex items-center gap-1 text-sm mb-2">
            <input
              type="checkbox"
              checked={coordinatesLocked}
              onChange={(event) => setCoordinatesLocked(event.target.checked)}
            />
            Don't overwrite on refresh
          </label>
          <button
            type="submit"
            disabled={saving}
            className="text-sm px-3 py-1.5 rounded-md bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save Coordinates"}
          </button>
          {error && <p className="text-xs text-red-600 w-full">{error}</p>}
        </form>
      </DetailField>
    </div>
  );
}
