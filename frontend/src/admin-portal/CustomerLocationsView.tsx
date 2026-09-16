import { useState, type FormEvent } from "react";
import { syncCustomerLocationsToResco, updateCustomerLocationCoordinates } from "../api";
import type { CustomerLocation, RescoSyncSummary } from "../types";
import { BackButton, DetailField } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";

interface Props {
  customerLocations: CustomerLocation[];
  onChanged: () => void | Promise<void>;
}

export function CustomerLocationsView({ customerLocations, onChanged }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncSummary, setSyncSummary] = useState<RescoSyncSummary | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);

  const selected = customerLocations.find((location) => location.id === selectedId) ?? null;

  async function handleSyncToResco() {
    setSyncing(true);
    setSyncError(null);
    setSyncSummary(null);
    try {
      const summary = await syncCustomerLocationsToResco();
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
      <CustomerLocationDetail
        location={selected}
        onChanged={onChanged}
        onBack={() => setSelectedId(null)}
      />
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900">Customer Locations</h2>
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
