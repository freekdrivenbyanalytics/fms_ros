import { useState, type FormEvent } from "react";
import { createSkill, deleteSkill, updateSkill } from "../api";
import type { Product, Skill } from "../types";
import { BackButton, DetailField } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";

interface Props {
  skills: Skill[];
  products: Product[];
  onChanged: () => void | Promise<void>;
}

export function SkillsView({ skills, products, onChanged }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);

  const selected = skills.find((skill) => skill.id === selectedId) ?? null;

  if (selected) {
    const skillProducts = products.filter((product) =>
      product.skills.some((skill) => skill.id === selected.id)
    );
    return (
      <SkillDetail
        skill={selected}
        skillProducts={skillProducts}
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
            header: "Products",
            render: (skill) =>
              String(products.filter((p) => p.skills.some((s) => s.id === skill.id)).length),
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
  skillProducts: Product[];
  onChanged: () => void | Promise<void>;
  onDeleted: () => void;
  onBack: () => void;
}

function SkillDetail({ skill, skillProducts, onChanged, onDeleted, onBack }: SkillDetailProps) {
  const [name, setName] = useState(skill.name);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await updateSkill(skill.id, { name });
      setDirty(false);
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
        <h2 className="text-xl font-semibold text-slate-900">{skill.name}</h2>
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
            {deleting ? "Deleting…" : "Soft-delete Skill"}
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

      <DetailField label="Products requiring this skill">
        {skillProducts.length === 0
          ? "—"
          : skillProducts.map((product) => `${product.number} ${product.name}`).join(", ")}
      </DetailField>
    </div>
  );
}
