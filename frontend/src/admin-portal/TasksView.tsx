import { useState, type FormEvent } from "react";
import { deleteTask, saveTask } from "../api";
import type { PortalTask } from "../types";
import { ListTable } from "../shared/ListTable";
import { BackButton } from "../shared/DetailField";

export function TasksView({ tasks, onChanged }: { tasks: PortalTask[]; onChanged: () => Promise<void> }) {
  const [selected, setSelected] = useState<number | "new" | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const task = tasks.find(t => t.id === selected);
  return <div>
    {warning && <p role="status" className="mb-3 text-amber-700">{warning}</p>}
    {selected !== null ? <TaskEditor key={selected} task={task} onBack={() => setSelected(null)}
      onSaved={async warning => { setWarning(warning); await onChanged(); setSelected(null); }} /> : <>
      <div className="mb-4 flex justify-between"><h2 className="text-xl font-semibold">Tasks</h2>
        <button className="rounded bg-emerald-600 px-3 py-2 text-white" onClick={() => { setWarning(null); setSelected("new"); }}>Create Task</button>
      </div>
      <ListTable items={tasks} getKey={t => t.id} onSelect={t => setSelected(t.id)} emptyMessage="No tasks."
        columns={[{ header: "Name", render: t => t.name },
          { header: "Duration (minutes)", render: t => t.estimated_duration_minutes ?? "—" },
          { header: "Service Order Types", render: t => t.service_order_types.map(s => s.name).join(", ") || "—" }]} />
    </>}
  </div>;
}

function TaskEditor({ task, onSaved, onBack }: {
  task?: PortalTask; onSaved: (warning: string | null) => Promise<void>; onBack: () => void;
}) {
  const [name, setName] = useState(task?.name ?? "");
  const [description, setDescription] = useState(task?.description ?? "");
  const [duration, setDuration] = useState(task?.estimated_duration_minutes?.toString() ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(null);
    try {
      const result = await saveTask(task?.id ?? null, { name: name.trim(), description: description || null,
        estimated_duration_minutes: duration ? Number(duration) : null });
      await onSaved(result.sync_warning);
    } catch (err) { setError(err instanceof Error ? err.message : "Save failed"); }
    finally { setBusy(false); }
  }
  async function remove() {
    if (!task) return;
    setBusy(true); setError(null);
    try { await onSaved((await deleteTask(task.id)).sync_warning); }
    catch (err) { setError(err instanceof Error ? err.message : "Delete failed"); }
    finally { setBusy(false); }
  }
  const inputClass = "block w-full rounded border border-slate-300 p-2";
  return <div className="max-w-xl">
    <BackButton label="Tasks" onClick={onBack} />
    <h2 className="mb-4 text-xl font-semibold">{task ? task.name : "Create Task"}</h2>
    <form onSubmit={submit} className="space-y-4">
      <label className="block">Name<input className={inputClass} value={name} onChange={e => setName(e.target.value)} required maxLength={160} /></label>
      <label className="block">Description<textarea aria-label="Description" className={inputClass} value={description} onChange={e => setDescription(e.target.value)} maxLength={2000} /></label>
      <label className="block">Estimated duration (minutes)<input className={inputClass} type="number" min="1" step="1" value={duration} onChange={e => setDuration(e.target.value)} /></label>
      {task && <p>Service Order Types: {task.service_order_types.map(t => t.name).join(", ") || "None"}</p>}
      {error && <p role="alert" className="text-red-600">{error}</p>}
      <button disabled={busy || !name.trim()} className="rounded bg-emerald-600 px-3 py-2 text-white disabled:opacity-50">{busy ? "Saving…" : "Save Task"}</button>
      {task && <button type="button" disabled={busy} onClick={remove} className="ml-3 text-red-700">Soft-delete Task</button>}
    </form>
  </div>;
}
