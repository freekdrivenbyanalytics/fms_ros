import { useState, type FormEvent } from "react";
import { createSkill, deleteSkill, updateSkill } from "../api";
import type { Contract, ContractLine, Employee, Skill } from "../types";
import { BackButton, DetailField } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";

interface Props {
  skills: Skill[];
  employees: Employee[];
  contracts: Contract[];
  onChanged: () => void | Promise<void>;
}

export function SkillsView({ skills, employees, contracts, onChanged }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);

  const selected = skills.find((skill) => skill.id === selectedId) ?? null;

  if (selected) {
    const skillEmployees = employees.filter((employee) =>
      employee.skills.some((skill) => skill.id === selected.id)
    );
    const skillLines: ContractLine[] = contracts.flatMap((contract) =>
      contract.lines.filter((line) =>
        line.required_skills.some((skill) => skill.id === selected.id)
      )
    );
    return (
      <SkillDetail
        skill={selected}
        skillEmployees={skillEmployees}
        skillLines={skillLines}
        onChanged={onChanged}
        onDeleted={() => setSelectedId(null)}
        onBack={() => setSelectedId(null)}
      />
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900">Skills</h2>
        <button
          type="button"
          onClick={() => setCreating((prev) => !prev)}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white"
        >
          {creating ? "Cancel" : "Create Skill"}
        </button>
      </div>

      {creating && (
        <CreateSkillForm
          onCreated={async (skill) => {
            setCreating(false);
            await onChanged();
            setSelectedId(skill.id);
          }}
        />
      )}

      <ListTable
        items={skills}
        getKey={(skill) => skill.id}
        onSelect={(skill) => setSelectedId(skill.id)}
        emptyMessage="No skills."
        columns={[
          { header: "Name", render: (skill) => skill.name },
          {
            header: "Employees",
            render: (skill) =>
              String(employees.filter((e) => e.skills.some((s) => s.id === skill.id)).length),
          },
          {
            header: "Contract Lines",
            render: (skill) =>
              String(
                contracts
                  .flatMap((c) => c.lines)
                  .filter((line) => line.required_skills.some((s) => s.id === skill.id)).length
              ),
          },
        ]}
      />
    </div>
  );
}

interface CreateSkillFormProps {
  onCreated: (skill: Skill) => void | Promise<void>;
}

function CreateSkillForm({ onCreated }: CreateSkillFormProps) {
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!name) return;
    setSubmitting(true);
    setError(null);
    try {
      const skill = await createSkill({ name });
      await onCreated(skill);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create skill");
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

interface SkillDetailProps {
  skill: Skill;
  skillEmployees: Employee[];
  skillLines: ContractLine[];
  onChanged: () => void | Promise<void>;
  onDeleted: () => void;
  onBack: () => void;
}

function SkillDetail({
  skill,
  skillEmployees,
  skillLines,
  onChanged,
  onDeleted,
  onBack,
}: SkillDetailProps) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(skill.name);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await updateSkill(skill.id, { name });
      setEditing(false);
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save skill");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    setError(null);
    try {
      await deleteSkill(skill.id);
      await onChanged();
      onDeleted();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete skill");
      setDeleting(false);
    }
  }

  return (
    <div>
      <BackButton label="Skills" onClick={onBack} />
      <div className="flex items-center justify-between mb-4">
        {editing ? (
          <input
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="text-xl font-semibold text-slate-900 border border-slate-300 rounded-md px-1"
          />
        ) : (
          <h2 className="text-xl font-semibold text-slate-900">{skill.name}</h2>
        )}
        <div className="flex gap-2">
          {editing ? (
            <>
              <button
                type="button"
                onClick={handleSave}
                disabled={saving}
                className="text-sm px-3 py-1.5 rounded-md bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-50"
              >
                {saving ? "Saving…" : "Save"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setName(skill.name);
                  setEditing(false);
                }}
                className="text-sm px-3 py-1.5 rounded-md border border-slate-300"
              >
                Cancel
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={() => setEditing(true)}
              className="text-sm px-3 py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50"
            >
              Edit
            </button>
          )}
          <button
            type="button"
            onClick={handleDelete}
            disabled={deleting}
            className="text-sm px-3 py-1.5 rounded-md border border-red-300 text-red-700 hover:bg-red-50 disabled:opacity-50"
          >
            {deleting ? "Deleting…" : "Soft-delete Skill"}
          </button>
        </div>
      </div>
      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      <DetailField label="Employees who hold this skill">
        {skillEmployees.length === 0
          ? "—"
          : skillEmployees.map((employee) => employee.name).join(", ")}
      </DetailField>
      <DetailField label="Contract lines requiring this skill">
        {skillLines.length === 0 ? (
          "—"
        ) : (
          <ul className="space-y-1">
            {skillLines.map((line) => (
              <li key={line.id}>
                {line.customer_location.customer.name} — {line.customer_location.address}
              </li>
            ))}
          </ul>
        )}
      </DetailField>
    </div>
  );
}
