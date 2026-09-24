import { useState, type FormEvent } from "react";
import {
  createCustomerLocation,
  deleteCustomerLocation,
  syncCustomerLocationsToResco,
  updateCustomerLocation,
  updateCustomerLocationCoordinates,
} from "../api";
import type { Customer, CustomerLocation, RescoSyncSummary } from "../types";
import { BackButton, DetailField } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";
import { SyncStatusBadge } from "../shared/SyncStatusBadge";

interface Props {
  customerLocations: CustomerLocation[];
  customers: Customer[];
  onChanged: () => void | Promise<void>;
}

export function CustomerLocationsView({ customerLocations, customers, onChanged }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncSummary, setSyncSummary] = useState<RescoSyncSummary | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [createSyncWarning, setCreateSyncWarning] = useState<string | null>(null);

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
        initialSyncWarning={createSyncWarning}
        onChanged={onChanged}
        onDeleted={() => setSelectedId(null)}
        onBack={() => setSelectedId(null)}
      />
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900">Customer Locations</h2>
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
            {creating ? "Cancel" : "Create Customer Location"}
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
        <CreateCustomerLocationForm
          customers={customers}
          onCreated={async (location) => {
            setCreating(false);
            setCreateSyncWarning(location.sync_warning);
            await onChanged();
            setSelectedId(location.id);
          }}
        />
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
          {
            header: "Sync status",
            render: (location) => (
              <div className="flex gap-1">
                <SyncStatusBadge label="Tripletex" synced={location.tripletex_id !== null} />
                <SyncStatusBadge label="Resco" synced={location.resco_asset_id !== null} />
              </div>
            ),
          },
        ]}
      />
    </div>
  );
}

interface CreateCustomerLocationFormProps {
  customers: Customer[];
  onCreated: (location: CustomerLocation) => void | Promise<void>;
}

function CreateCustomerLocationForm({ customers, onCreated }: CreateCustomerLocationFormProps) {
  const [customerId, setCustomerId] = useState<number | "">(customers[0]?.id ?? "");
  const [addressLine1, setAddressLine1] = useState("");
  const [addressLine2, setAddressLine2] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [city, setCity] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!customerId || !addressLine1) return;
    setSubmitting(true);
    setError(null);
    try {
      const location = await createCustomerLocation({
        customer_id: customerId,
        address_line_1: addressLine1,
        address_line_2: addressLine2 || null,
        postal_code: postalCode || null,
        city: city || null,
      });
      await onCreated(location);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create customer location");
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
        <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">
          Customer
        </label>
        <select
          value={customerId}
          onChange={(event) => setCustomerId(Number(event.target.value))}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
          required
        >
          {customers.map((customer) => (
            <option key={customer.id} value={customer.id}>
              {customer.name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">
          Address Line 1
        </label>
        <input
          type="text"
          value={addressLine1}
          onChange={(event) => setAddressLine1(event.target.value)}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
          required
        />
      </div>
      <div>
        <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">
          Address Line 2
        </label>
        <input
          type="text"
          value={addressLine2}
          onChange={(event) => setAddressLine2(event.target.value)}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
        />
      </div>
      <div>
        <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">
          Postal Code
        </label>
        <input
          type="text"
          value={postalCode}
          onChange={(event) => setPostalCode(event.target.value)}
          className="text-sm border border-slate-300 rounded-md px-2 py-1 w-24"
        />
      </div>
      <div>
        <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">City</label>
        <input
          type="text"
          value={city}
          onChange={(event) => setCity(event.target.value)}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
        />
      </div>
      <button
        type="submit"
        disabled={submitting || customers.length === 0}
        className="text-sm px-3 py-1.5 rounded-md bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-50"
      >
        {submitting ? "Creating…" : "Create"}
      </button>
      {error && <p className="text-xs text-red-600 w-full">{error}</p>}
      {customers.length === 0 && (
        <p className="text-xs text-slate-500 w-full">Create a customer first.</p>
      )}
    </form>
  );
}

interface CustomerLocationDetailProps {
  location: CustomerLocation;
  initialSyncWarning?: string | null;
  onChanged: () => void | Promise<void>;
  onDeleted: () => void;
  onBack: () => void;
}

function CustomerLocationDetail({
  location,
  initialSyncWarning = null,
  onChanged,
  onDeleted,
  onBack,
}: CustomerLocationDetailProps) {
  const [addressLine1, setAddressLine1] = useState(location.address_line_1 ?? "");
  const [addressLine2, setAddressLine2] = useState(location.address_line_2 ?? "");
  const [postalCode, setPostalCode] = useState(location.postal_code ?? "");
  const [city, setCity] = useState(location.city ?? "");
  const [addressDirty, setAddressDirty] = useState(false);
  const [savingAddress, setSavingAddress] = useState(false);
  const [addressError, setAddressError] = useState<string | null>(null);
  const [syncWarning, setSyncWarning] = useState<string | null>(initialSyncWarning);

  const [latitude, setLatitude] = useState(
    location.latitude !== null ? String(location.latitude) : ""
  );
  const [longitude, setLongitude] = useState(
    location.longitude !== null ? String(location.longitude) : ""
  );
  const [coordinatesLocked, setCoordinatesLocked] = useState(location.coordinates_locked);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  async function handleSaveAddress() {
    if (!addressLine1) return;
    setSavingAddress(true);
    setAddressError(null);
    setSyncWarning(null);
    try {
      const updated = await updateCustomerLocation(location.id, {
        address_line_1: addressLine1,
        address_line_2: addressLine2 || null,
        postal_code: postalCode || null,
        city: city || null,
      });
      setSyncWarning(updated.sync_warning);
      setAddressDirty(false);
      await onChanged();
    } catch (err) {
      setAddressError(err instanceof Error ? err.message : "Failed to save address");
    } finally {
      setSavingAddress(false);
    }
  }

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

  async function handleDelete() {
    setDeleting(true);
    setDeleteError(null);
    try {
      await deleteCustomerLocation(location.id);
      await onChanged();
      onDeleted();
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Failed to delete customer location");
      setDeleting(false);
    }
  }

  return (
    <div>
      <BackButton label="Customer Locations" onClick={onBack} />
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900">{location.address}</h2>
        <button
          type="button"
          onClick={handleDelete}
          disabled={deleting}
          className="text-sm px-3 py-1.5 rounded-md border border-red-300 text-red-700 hover:bg-red-50 disabled:opacity-50"
        >
          {deleting ? "Deleting…" : "Soft-delete Location"}
        </button>
      </div>
      {deleteError && <p className="text-sm text-red-600 mb-3">{deleteError}</p>}

      <DetailField label="Customer">{location.customer.name}</DetailField>
      <DetailField label="Region">{location.region?.name ?? "Not yet assigned"}</DetailField>

      <DetailField label="Address">
        <div className="flex flex-wrap items-end gap-2">
          <div>
            <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">
              Address Line 1
            </label>
            <input
              type="text"
              value={addressLine1}
              onChange={(event) => {
                setAddressLine1(event.target.value);
                setAddressDirty(true);
              }}
              className="text-sm border border-slate-300 rounded-md px-2 py-1"
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">
              Address Line 2
            </label>
            <input
              type="text"
              value={addressLine2}
              onChange={(event) => {
                setAddressLine2(event.target.value);
                setAddressDirty(true);
              }}
              className="text-sm border border-slate-300 rounded-md px-2 py-1"
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">
              Postal Code
            </label>
            <input
              type="text"
              value={postalCode}
              onChange={(event) => {
                setPostalCode(event.target.value);
                setAddressDirty(true);
              }}
              className="text-sm border border-slate-300 rounded-md px-2 py-1 w-24"
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">
              City
            </label>
            <input
              type="text"
              value={city}
              onChange={(event) => {
                setCity(event.target.value);
                setAddressDirty(true);
              }}
              className="text-sm border border-slate-300 rounded-md px-2 py-1"
            />
          </div>
          <button
            type="button"
            onClick={handleSaveAddress}
            disabled={savingAddress || !addressDirty}
            className="text-sm px-3 py-1.5 rounded-md bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-50"
          >
            {savingAddress ? "Saving…" : "Save Address"}
          </button>
          {addressError && <p className="text-xs text-red-600 w-full">{addressError}</p>}
          {syncWarning && <p className="text-xs text-amber-600 w-full">{syncWarning}</p>}
        </div>
      </DetailField>

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
      <DetailField label="Tripletex Sync Status">
        {location.tripletex_id
          ? `Synced (Tripletex ID ${location.tripletex_id})`
          : "Not yet synced"}
      </DetailField>
      <DetailField label="Resco Functional Location ID"><span className="break-all select-text">{location.resco_functional_location_id ?? "Not yet synced"}</span></DetailField>
      <DetailField label="Resco Asset ID">
        <span className="break-all select-text">{location.resco_asset_id ?? "Not yet synced"}</span>
      </DetailField>
    </div>
  );
}
