import { useState, type FormEvent } from "react";
import {
  createContract,
  createContractLine,
  deleteContract,
  deleteContractLine,
  updateContractLine,
} from "../api";
import type { Contract, ContractLine, Customer, CustomerLocation, Skill } from "../types";
import { BackButton, DetailField } from "./DetailField";
import { ListTable } from "./ListTable";

interface Props {
  contracts: Contract[];
  customers: Customer[];
  customerLocations: CustomerLocation[];
  skills: Skill[];
  onChanged: () => void | Promise<void>;
}

export function ContractsView({
  contracts,
  customers,
  customerLocations,
  skills,
  onChanged,
}: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [creatingContract, setCreatingContract] = useState(false);

  const selected = contracts.find((contract) => contract.id === selectedId) ?? null;

  if (selected) {
    return (
      <ContractDetail
        contract={selected}
        customerLocations={customerLocations}
        skills={skills}
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
        <button
          type="button"
          onClick={() => setCreatingContract((prev) => !prev)}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white"
        >
          {creatingContract ? "Cancel" : "Create Contract"}
        </button>
      </div>

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
  skills: Skill[];
  onChanged: () => void | Promise<void>;
  onDeleted: () => void;
  onBack: () => void;
}

function ContractDetail({
  contract,
  customerLocations,
  skills,
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
                skills={skills}
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
            skills={skills}
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
  skills: Skill[];
  onChanged: () => void | Promise<void>;
}

function ContractLineRow({ line, locations, skills, onChanged }: ContractLineRowProps) {
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
          skills={skills}
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
            {line.required_skills.length === 0 ? (
              <span className="text-slate-400">no skills required</span>
            ) : (
              line.required_skills.map((skill) => (
                <span
                  key={skill.id}
                  className="inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700"
                >
                  {skill.name}
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
      {error && <p className="text-xs text-red-600 mt-2">{error}</p>}
    </li>
  );
}

interface ContractLineFormProps {
  contractId: number;
  existingLine?: ContractLine;
  locations: CustomerLocation[];
  skills: Skill[];
  onSaved: () => void | Promise<void>;
  onCancel?: () => void;
}

function ContractLineForm({
  contractId,
  existingLine,
  locations,
  skills,
  onSaved,
  onCancel,
}: ContractLineFormProps) {
  const [customerLocationId, setCustomerLocationId] = useState(
    existingLine ? String(existingLine.customer_location.id) : ""
  );
  const [startDate, setStartDate] = useState(existingLine?.start_date ?? "");
  const [endDate, setEndDate] = useState(existingLine?.end_date ?? "");
  const [intervalDays, setIntervalDays] = useState(
    existingLine ? String(existingLine.interval_days) : ""
  );
  const [durationMinutes, setDurationMinutes] = useState(
    existingLine ? String(existingLine.duration_minutes) : ""
  );
  const [skillIds, setSkillIds] = useState<number[]>(
    existingLine ? existingLine.required_skills.map((skill) => skill.id) : []
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggleSkill(skillId: number) {
    setSkillIds((prev) =>
      prev.includes(skillId) ? prev.filter((id) => id !== skillId) : [...prev, skillId]
    );
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
        end_date: endDate || null,
        interval_days: Number(intervalDays),
        duration_minutes: Number(durationMinutes),
        required_skill_ids: skillIds,
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
          value={endDate}
          onChange={(event) => setEndDate(event.target.value)}
          placeholder="End date (optional)"
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
        />
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
      <div className="flex flex-wrap gap-2">
        {skills.map((skill) => (
          <label key={skill.id} className="flex items-center gap-1 text-sm">
            <input
              type="checkbox"
              checked={skillIds.includes(skill.id)}
              onChange={() => toggleSkill(skill.id)}
            />
            {skill.name}
          </label>
        ))}
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
