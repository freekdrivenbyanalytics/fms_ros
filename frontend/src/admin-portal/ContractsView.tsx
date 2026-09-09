import { useState, type ChangeEvent, type FormEvent } from "react";
import {
  createContract,
  createContractLine,
  deleteContract,
  deleteContractLine,
  extendContractLineVisits,
  updateContractLine,
} from "../api";
import type {
  Contract,
  ContractLine,
  Customer,
  CustomerLocation,
  Product,
  ServiceVisit,
} from "../types";
import { BackButton, DetailField } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";

interface Props {
  contracts: Contract[];
  customers: Customer[];
  customerLocations: CustomerLocation[];
  serviceVisits: ServiceVisit[];
  products: Product[];
  onChanged: () => void | Promise<void>;
}

export function ContractsView({
  contracts,
  customers,
  customerLocations,
  serviceVisits,
  products,
  onChanged,
}: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [creatingContract, setCreatingContract] = useState(false);
  const [extendingVisits, setExtendingVisits] = useState(false);
  const [extendVisitsMessage, setExtendVisitsMessage] = useState<string | null>(null);

  const selected = contracts.find((contract) => contract.id === selectedId) ?? null;

  async function handleExtendVisits() {
    setExtendingVisits(true);
    setExtendVisitsMessage(null);
    try {
      const summary = await extendContractLineVisits();
      setExtendVisitsMessage(
        `Extended ${summary.lines_extended} line${summary.lines_extended === 1 ? "" : "s"}, ` +
          `created ${summary.visits_created} visit${summary.visits_created === 1 ? "" : "s"}.`
      );
      await onChanged();
    } catch (err) {
      setExtendVisitsMessage(
        err instanceof Error ? err.message : "Failed to extend recurring visits"
      );
    } finally {
      setExtendingVisits(false);
    }
  }

  if (selected) {
    return (
      <ContractDetail
        contract={selected}
        customerLocations={customerLocations}
        serviceVisits={serviceVisits}
        products={products}
        onChanged={onChanged}
        onDeleted={() => setSelectedId(null)}
        onBack={() => setSelectedId(null)}
      />
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900">Contracts</h2>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleExtendVisits}
            disabled={extendingVisits}
            className="text-sm px-3 py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50 disabled:opacity-50"
          >
            {extendingVisits ? "Extending…" : "Extend recurring visits"}
          </button>
          <button
            type="button"
            onClick={() => setCreatingContract((prev) => !prev)}
            className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white"
          >
            {creatingContract ? "Cancel" : "Create Contract"}
          </button>
        </div>
      </div>
      {extendVisitsMessage && (
        <p className="text-sm text-slate-600 mb-3">{extendVisitsMessage}</p>
      )}

      {creatingContract && (
        <CreateContractForm
          customers={customers}
          onCreated={async (contract) => {
            setCreatingContract(false);
            await onChanged();
            setSelectedId(contract.id);
          }}
        />
      )}

      <ListTable
        items={contracts}
        getKey={(contract) => contract.id}
        onSelect={(contract) => setSelectedId(contract.id)}
        emptyMessage="No contracts."
        columns={[
          { header: "Customer", render: (contract) => contract.customer.name },
          { header: "Lines", render: (contract) => String(contract.lines.length) },
        ]}
      />
    </div>
  );
}

interface CreateContractFormProps {
  customers: Customer[];
  onCreated: (contract: Contract) => void | Promise<void>;
}

function CreateContractForm({ customers, onCreated }: CreateContractFormProps) {
  const [customerId, setCustomerId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!customerId) return;
    setSubmitting(true);
    setError(null);
    try {
      const contract = await createContract({ customer_id: Number(customerId) });
      await onCreated(contract);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create contract");
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
          onChange={(event) => setCustomerId(event.target.value)}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
          required
        >
          <option value="" disabled>
            Select customer
          </option>
          {customers.map((customer) => (
            <option key={customer.id} value={customer.id}>
              {customer.name}
            </option>
          ))}
        </select>
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

interface ContractDetailProps {
  contract: Contract;
  customerLocations: CustomerLocation[];
  serviceVisits: ServiceVisit[];
  products: Product[];
  onChanged: () => void | Promise<void>;
  onDeleted: () => void;
  onBack: () => void;
}

function ContractDetail({
  contract,
  customerLocations,
  serviceVisits,
  products,
  onChanged,
  onDeleted,
  onBack,
}: ContractDetailProps) {
  const [addingLine, setAddingLine] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ownLocations = customerLocations.filter(
    (location) => location.customer.id === contract.customer.id
  );

  async function handleDeleteContract() {
    setDeleting(true);
    setError(null);
    try {
      await deleteContract(contract.id);
      await onChanged();
      onDeleted();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete contract");
      setDeleting(false);
    }
  }

  return (
    <div>
      <BackButton label="Contracts" onClick={onBack} />
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900">
          Contract #{contract.id} — {contract.customer.name}
        </h2>
        <button
          type="button"
          onClick={handleDeleteContract}
          disabled={deleting}
          className="text-sm px-3 py-1.5 rounded-md border border-red-300 text-red-700 hover:bg-red-50 disabled:opacity-50"
        >
          {deleting ? "Deleting…" : "Soft-delete Contract"}
        </button>
      </div>
      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      <DetailField label="Contract Lines">
        {contract.lines.length === 0 ? (
          "—"
        ) : (
          <ul className="space-y-2">
            {contract.lines.map((line) => (
              <ContractLineRow
                key={line.id}
                line={line}
                locations={ownLocations}
                visits={serviceVisits.filter((visit) => visit.contract_line.id === line.id)}
                products={products}
                onChanged={onChanged}
              />
            ))}
          </ul>
        )}
      </DetailField>

      <div className="mt-3">
        <button
          type="button"
          onClick={() => setAddingLine((prev) => !prev)}
          className="text-sm px-3 py-1.5 rounded-md bg-slate-900 text-white"
        >
          {addingLine ? "Cancel" : "Add Contract Line"}
        </button>
        {addingLine && (
          <ContractLineForm
            contractId={contract.id}
            locations={ownLocations}
            products={products}
            onSaved={async () => {
              setAddingLine(false);
              await onChanged();
            }}
          />
        )}
      </div>
    </div>
  );
}

interface ContractLineRowProps {
  line: ContractLine;
  locations: CustomerLocation[];
  visits: ServiceVisit[];
  products: Product[];
  onChanged: () => void | Promise<void>;
}

function ContractLineRow({ line, locations, visits, products, onChanged }: ContractLineRowProps) {
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDelete() {
    setDeleting(true);
    setError(null);
    try {
      await deleteContractLine(line.id);
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete contract line");
      setDeleting(false);
    }
  }

  if (editing) {
    return (
      <li className="rounded-md border border-slate-200 p-3">
        <ContractLineForm
          contractId={line.contract_id}
          existingLine={line}
          locations={locations}
          products={products}
          onSaved={async () => {
            setEditing(false);
            await onChanged();
          }}
          onCancel={() => setEditing(false)}
        />
      </li>
    );
  }

  return (
    <li className="rounded-md border border-slate-200 p-3 text-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="font-medium text-slate-800">
            {line.customer_location.address} ({line.customer_location.region?.name ?? "no region"})
          </div>
          <div className="text-slate-600 mt-1">
            Every {line.interval_days} days, {line.duration_minutes} min — {line.start_date}
            {line.end_date ? ` to ${line.end_date}` : ""}
          </div>
          <div className="mt-1 flex flex-wrap gap-1">
            {line.required_products.length === 0 ? (
              <span className="text-slate-400">no products required</span>
            ) : (
              line.required_products.map((product) => (
                <span
                  key={product.id}
                  className="inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700"
                >
                  {product.number} {product.name}
                </span>
              ))
            )}
          </div>
        </div>
        <div className="shrink-0 flex flex-col items-end gap-1">
          <button
            type="button"
            onClick={() => setEditing(true)}
            className="text-xs px-2 py-1 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50"
          >
            Edit
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={deleting}
            className="text-xs px-2 py-1 rounded-md border border-red-300 text-red-700 hover:bg-red-50 disabled:opacity-50"
          >
            {deleting ? "Deleting…" : "Delete"}
          </button>
        </div>
      </div>
      <div className="mt-2 pt-2 border-t border-slate-100">
        <div className="text-xs uppercase tracking-wide text-slate-400 mb-1">
          Generated Visits
        </div>
        {visits.length === 0 ? (
          <p className="text-xs text-slate-400">No visits generated yet.</p>
        ) : (
          <ul className="flex flex-wrap gap-1">
            {visits.map((visit) => (
              <li
                key={visit.id}
                className={`inline-block rounded-full px-2 py-0.5 text-xs ${
                  visit.status === "assigned"
                    ? "bg-emerald-50 text-emerald-700"
                    : "bg-amber-50 text-amber-700"
                }`}
              >
                {visit.requested_date} — {visit.status}
              </li>
            ))}
          </ul>
        )}
      </div>
      {error && <p className="text-xs text-red-600 mt-2">{error}</p>}
    </li>
  );
}

interface ContractLineFormProps {
  contractId: number;
  existingLine?: ContractLine;
  locations: CustomerLocation[];
  products: Product[];
  onSaved: () => void | Promise<void>;
  onCancel?: () => void;
}

function ContractLineForm({
  contractId,
  existingLine,
  locations,
  products,
  onSaved,
  onCancel,
}: ContractLineFormProps) {
  const [customerLocationId, setCustomerLocationId] = useState(
    existingLine ? String(existingLine.customer_location.id) : ""
  );
  const [startDate, setStartDate] = useState(existingLine?.start_date ?? "");
  const [endDate, setEndDate] = useState(existingLine?.end_date ?? "");
  const [noEndDate, setNoEndDate] = useState(existingLine ? existingLine.end_date === null : false);
  const [intervalDays, setIntervalDays] = useState(
    existingLine ? String(existingLine.interval_days) : ""
  );
  const [durationMinutes, setDurationMinutes] = useState(
    existingLine ? String(existingLine.duration_minutes) : ""
  );
  const [productIds, setProductIds] = useState<number[]>(
    existingLine ? existingLine.required_products.map((product) => product.id) : []
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleProductSelectionChange(event: ChangeEvent<HTMLSelectElement>) {
    setProductIds(Array.from(event.target.selectedOptions, (option) => Number(option.value)));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!customerLocationId || !startDate || !intervalDays || !durationMinutes) return;
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        customer_location_id: Number(customerLocationId),
        start_date: startDate,
        end_date: noEndDate ? null : (endDate || null),
        interval_days: Number(intervalDays),
        duration_minutes: Number(durationMinutes),
        required_product_ids: productIds,
      };
      if (existingLine) {
        await updateContractLine(existingLine.id, payload);
      } else {
        await createContractLine(contractId, payload);
      }
      await onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save contract line");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mt-3 flex flex-col gap-2 rounded-md border border-slate-200 bg-white p-3"
    >
      <select
        value={customerLocationId}
        onChange={(event) => setCustomerLocationId(event.target.value)}
        className="text-sm border border-slate-300 rounded-md px-2 py-1"
        required
      >
        <option value="" disabled>
          Select customer location
        </option>
        {locations.map((location) => (
          <option key={location.id} value={location.id}>
            {location.address}
          </option>
        ))}
      </select>
      <div className="flex gap-2">
        <input
          type="date"
          value={startDate}
          onChange={(event) => setStartDate(event.target.value)}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
          required
        />
        <input
          type="date"
          value={noEndDate ? "2099-12-31" : endDate}
          onChange={(event) => setEndDate(event.target.value)}
          placeholder="End date (optional)"
          disabled={noEndDate}
          className="text-sm border border-slate-300 rounded-md px-2 py-1 disabled:bg-slate-100 disabled:text-slate-400"
        />
        <label className="flex items-center gap-1 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={noEndDate}
            onChange={(event) => setNoEndDate(event.target.checked)}
          />
          No end date
        </label>
      </div>
      <div className="flex gap-2">
        <input
          type="number"
          min={1}
          value={intervalDays}
          onChange={(event) => setIntervalDays(event.target.value)}
          placeholder="Interval (days)"
          className="text-sm border border-slate-300 rounded-md px-2 py-1 w-36"
          required
        />
        <input
          type="number"
          min={1}
          value={durationMinutes}
          onChange={(event) => setDurationMinutes(event.target.value)}
          placeholder="Duration (min)"
          className="text-sm border border-slate-300 rounded-md px-2 py-1 w-36"
          required
        />
      </div>
      <div>
        <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">
          Required products
        </label>
        <select
          multiple
          value={productIds.map(String)}
          onChange={handleProductSelectionChange}
          className="text-sm border border-slate-300 rounded-md px-2 py-1 w-full min-h-24"
        >
          {products.map((product) => (
            <option key={product.id} value={product.id}>
              {product.number} {product.name}
            </option>
          ))}
        </select>
      </div>
      {error && <p className="text-xs text-red-600">{error}</p>}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={submitting}
          className="text-sm px-3 py-1 rounded-md bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-50"
        >
          {submitting ? "Saving…" : "Save"}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="text-sm px-3 py-1 rounded-md border border-slate-300"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
