import { useState, type FormEvent } from "react";
import {
  createEmployee,
  createScheduleOverride,
  createScheduleOverridesBulk,
  createScheduleTemplate,
  deleteEmployee,
  deleteScheduleOverride,
  deleteScheduleTemplate,
  updateEmployee,
  updateScheduleOverride,
  updateScheduleTemplate,
} from "../api";
import type {
  DayType,
  Employee,
  EmployeeScheduleDayOverride,
  EmployeeScheduleTemplate,
  Region,
  Skill,
} from "../types";
import { BackButton, DetailField } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";

interface Props {
  employees: Employee[];
  regions: Region[];
  skills: Skill[];
  onChanged: () => void | Promise<void>;
}

export function EmployeesView({ employees, regions, skills, onChanged }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);

  const selected = employees.find((employee) => employee.id === selectedId) ?? null;

  if (selected) {
    return (
      <EmployeeDetail
        employee={selected}
        regions={regions}
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
        <h2 className="text-xl font-semibold text-slate-900">Employees</h2>
        <button
          type="button"
          onClick={() => setCreating((prev) => !prev)}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white"
        >
          {creating ? "Cancel" : "Create Employee"}
        </button>
      </div>

      {creating && (
        <EmployeeForm
          regions={regions}
          skills={skills}
          onSaved={async (employee) => {
            setCreating(false);
            await onChanged();
            setSelectedId(employee.id);
          }}
        />
      )}

      <ListTable
        items={employees}
        getKey={(employee) => employee.id}
        onSelect={(employee) => setSelectedId(employee.id)}
        emptyMessage="No employees."
        columns={[
          { header: "Name", render: (employee) => employee.name },
          {
            header: "Regions",
            render: (employee) => employee.regions.map((region) => region.name).join(", ") || "—",
          },
          {
            header: "Skills",
            render: (employee) => employee.skills.map((skill) => skill.name).join(", ") || "—",
          },
        ]}
      />
    </div>
  );
}

interface EmployeeFormProps {
  regions: Region[];
  skills: Skill[];
  existingEmployee?: Employee;
  onSaved: (employee: Employee) => void | Promise<void>;
  onCancel?: () => void;
}

function EmployeeForm({ regions, skills, existingEmployee, onSaved, onCancel }: EmployeeFormProps) {
  const [name, setName] = useState(existingEmployee?.name ?? "");
  const [latitude, setLatitude] = useState(
    existingEmployee ? String(existingEmployee.latitude) : ""
  );
  const [longitude, setLongitude] = useState(
    existingEmployee ? String(existingEmployee.longitude) : ""
  );
  const [regionIds, setRegionIds] = useState<number[]>(
    existingEmployee ? existingEmployee.regions.map((region) => region.id) : []
  );
  const [skillIds, setSkillIds] = useState<number[]>(
    existingEmployee ? existingEmployee.skills.map((skill) => skill.id) : []
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggle(setter: typeof setRegionIds, id: number) {
    setter((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!name || !latitude || !longitude || regionIds.length === 0) return;
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        name,
        latitude: Number(latitude),
        longitude: Number(longitude),
        region_ids: regionIds,
        skill_ids: skillIds,
      };
      const employee = existingEmployee
        ? await updateEmployee(existingEmployee.id, payload)
        : await createEmployee(payload);
      await onSaved(employee);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save employee");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mb-4 flex flex-col gap-2 rounded-md border border-slate-200 bg-white p-3"
    >
      <input
        type="text"
        value={name}
        onChange={(event) => setName(event.target.value)}
        placeholder="Name"
        className="text-sm border border-slate-300 rounded-md px-2 py-1"
        required
      />
      <div className="flex gap-2">
        <input
          type="number"
          step="any"
          value={latitude}
          onChange={(event) => setLatitude(event.target.value)}
          placeholder="Latitude"
          className="text-sm border border-slate-300 rounded-md px-2 py-1 w-36"
          required
        />
        <input
          type="number"
          step="any"
          value={longitude}
          onChange={(event) => setLongitude(event.target.value)}
          placeholder="Longitude"
          className="text-sm border border-slate-300 rounded-md px-2 py-1 w-36"
          required
        />
      </div>
      <div>
        <div className="text-xs uppercase tracking-wide text-slate-400 mb-1">Regions</div>
        <div className="flex flex-wrap gap-2">
          {regions.map((region) => (
            <label key={region.id} className="flex items-center gap-1 text-sm">
              <input
                type="checkbox"
                checked={regionIds.includes(region.id)}
                onChange={() => toggle(setRegionIds, region.id)}
              />
              {region.name}
            </label>
          ))}
        </div>
      </div>
      <div>
        <div className="text-xs uppercase tracking-wide text-slate-400 mb-1">Skills</div>
        <div className="flex flex-wrap gap-2">
          {skills.map((skill) => (
            <label key={skill.id} className="flex items-center gap-1 text-sm">
              <input
                type="checkbox"
                checked={skillIds.includes(skill.id)}
                onChange={() => toggle(setSkillIds, skill.id)}
              />
              {skill.name}
            </label>
          ))}
        </div>
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

interface EmployeeDetailProps {
  employee: Employee;
  regions: Region[];
  skills: Skill[];
  onChanged: () => void | Promise<void>;
  onDeleted: () => void;
  onBack: () => void;
}

function EmployeeDetail({
  employee,
  regions,
  skills,
  onChanged,
  onDeleted,
  onBack,
}: EmployeeDetailProps) {
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDelete() {
    setDeleting(true);
    setError(null);
    try {
      await deleteEmployee(employee.id);
      await onChanged();
      onDeleted();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete employee");
      setDeleting(false);
    }
  }

  return (
    <div>
      <BackButton label="Employees" onClick={onBack} />
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900">{employee.name}</h2>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setEditing((prev) => !prev)}
            className="text-sm px-3 py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50"
          >
            {editing ? "Cancel" : "Edit"}
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={deleting}
            className="text-sm px-3 py-1.5 rounded-md border border-red-300 text-red-700 hover:bg-red-50 disabled:opacity-50"
          >
            {deleting ? "Deleting…" : "Soft-delete Employee"}
          </button>
        </div>
      </div>
      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      {editing ? (
        <EmployeeForm
          regions={regions}
          skills={skills}
          existingEmployee={employee}
          onSaved={async () => {
            setEditing(false);
            await onChanged();
          }}
          onCancel={() => setEditing(false)}
        />
      ) : (
        <>
          <DetailField label="Location">
            {employee.latitude.toFixed(4)}, {employee.longitude.toFixed(4)}
          </DetailField>
          <DetailField label="Regions">
            {employee.regions.map((region) => region.name).join(", ") || "—"}
          </DetailField>
          <DetailField label="Skills">
            {employee.skills.map((skill) => skill.name).join(", ") || "—"}
          </DetailField>
        </>
      )}

      <ScheduleTemplatesSection employee={employee} onChanged={onChanged} />
      <ScheduleOverridesSection employee={employee} onChanged={onChanged} />
    </div>
  );
}

interface ScheduleTemplatesSectionProps {
  employee: Employee;
  onChanged: () => void | Promise<void>;
}

function ScheduleTemplatesSection({ employee, onChanged }: ScheduleTemplatesSectionProps) {
  const [adding, setAdding] = useState(false);

  return (
    <div className="mt-6">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wide">
          Schedule Templates
        </h3>
        <button
          type="button"
          onClick={() => setAdding((prev) => !prev)}
          className="text-sm px-3 py-1.5 rounded-md bg-slate-900 text-white"
        >
          {adding ? "Cancel" : "Apply Template"}
        </button>
      </div>
      {adding && (
        <ScheduleTemplateForm
          employeeId={employee.id}
          onSaved={async () => {
            setAdding(false);
            await onChanged();
          }}
        />
      )}
      {employee.schedule_templates.length === 0 ? (
        <p className="text-sm text-slate-500">No schedule templates.</p>
      ) : (
        <ul className="space-y-2">
          {employee.schedule_templates.map((template) => (
            <ScheduleTemplateRow key={template.id} template={template} onChanged={onChanged} />
          ))}
        </ul>
      )}
    </div>
  );
}

interface ScheduleTemplateRowProps {
  template: EmployeeScheduleTemplate;
  onChanged: () => void | Promise<void>;
}

function ScheduleTemplateRow({ template, onChanged }: ScheduleTemplateRowProps) {
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDelete() {
    setDeleting(true);
    setError(null);
    try {
      await deleteScheduleTemplate(template.id);
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete template");
      setDeleting(false);
    }
  }

  if (editing) {
    return (
      <li className="rounded-md border border-slate-200 p-3">
        <ScheduleTemplateForm
          employeeId={template.employee_id}
          existingTemplate={template}
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
            {template.start_date} to {template.end_date ?? "ongoing"}
          </div>
          <div className="text-slate-600 mt-1">
            {template.work_start.slice(0, 5)}–{template.work_end.slice(0, 5)}, max{" "}
            {template.max_hours_per_day}h/day
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

interface ScheduleTemplateFormProps {
  employeeId: number;
  existingTemplate?: EmployeeScheduleTemplate;
  onSaved: () => void | Promise<void>;
  onCancel?: () => void;
}

function ScheduleTemplateForm({
  employeeId,
  existingTemplate,
  onSaved,
  onCancel,
}: ScheduleTemplateFormProps) {
  const [startDate, setStartDate] = useState(existingTemplate?.start_date ?? "");
  const [endDate, setEndDate] = useState(existingTemplate?.end_date ?? "");
  const [workStart, setWorkStart] = useState(existingTemplate?.work_start.slice(0, 5) ?? "08:00");
  const [workEnd, setWorkEnd] = useState(existingTemplate?.work_end.slice(0, 5) ?? "16:00");
  const [maxHoursPerDay, setMaxHoursPerDay] = useState(
    existingTemplate ? String(existingTemplate.max_hours_per_day) : "8"
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!startDate || !workStart || !workEnd || !maxHoursPerDay) return;
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        start_date: startDate,
        end_date: endDate || null,
        work_start: workStart,
        work_end: workEnd,
        max_hours_per_day: Number(maxHoursPerDay),
        lunch_type: "none" as const,
        lunch_start: null,
        lunch_end: null,
        lunch_duration_minutes: null,
      };
      if (existingTemplate) {
        await updateScheduleTemplate(existingTemplate.id, payload);
      } else {
        await createScheduleTemplate(employeeId, payload);
      }
      await onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save template");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mb-3 flex flex-col gap-2 rounded-md border border-slate-200 bg-white p-3"
    >
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
          placeholder="End date (optional = ongoing)"
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
        />
      </div>
      <div className="flex gap-2">
        <input
          type="time"
          value={workStart}
          onChange={(event) => setWorkStart(event.target.value)}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
          required
        />
        <input
          type="time"
          value={workEnd}
          onChange={(event) => setWorkEnd(event.target.value)}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
          required
        />
        <input
          type="number"
          min={1}
          step="any"
          value={maxHoursPerDay}
          onChange={(event) => setMaxHoursPerDay(event.target.value)}
          placeholder="Max hours/day"
          className="text-sm border border-slate-300 rounded-md px-2 py-1 w-32"
          required
        />
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

interface ScheduleOverridesSectionProps {
  employee: Employee;
  onChanged: () => void | Promise<void>;
}

function ScheduleOverridesSection({ employee, onChanged }: ScheduleOverridesSectionProps) {
  const [adding, setAdding] = useState(false);
  const [markingRange, setMarkingRange] = useState(false);

  return (
    <div className="mt-6">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wide">
          Day Overrides
        </h3>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setMarkingRange((prev) => !prev)}
            className="text-sm px-3 py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50"
          >
            {markingRange ? "Cancel" : "Mark Holiday/Sick"}
          </button>
          <button
            type="button"
            onClick={() => setAdding((prev) => !prev)}
            className="text-sm px-3 py-1.5 rounded-md bg-slate-900 text-white"
          >
            {adding ? "Cancel" : "Adjust a Day"}
          </button>
        </div>
      </div>
      {markingRange && (
        <BulkMarkForm
          employeeId={employee.id}
          onSaved={async () => {
            setMarkingRange(false);
            await onChanged();
          }}
        />
      )}
      {adding && (
        <ScheduleOverrideForm
          employeeId={employee.id}
          onSaved={async () => {
            setAdding(false);
            await onChanged();
          }}
        />
      )}
      {employee.schedule_overrides.length === 0 ? (
        <p className="text-sm text-slate-500">No day overrides.</p>
      ) : (
        <ul className="space-y-2">
          {employee.schedule_overrides.map((override) => (
            <ScheduleOverrideRow key={override.id} override={override} onChanged={onChanged} />
          ))}
        </ul>
      )}
    </div>
  );
}

interface ScheduleOverrideRowProps {
  override: EmployeeScheduleDayOverride;
  onChanged: () => void | Promise<void>;
}

function ScheduleOverrideRow({ override, onChanged }: ScheduleOverrideRowProps) {
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDelete() {
    setDeleting(true);
    setError(null);
    try {
      await deleteScheduleOverride(override.id);
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete override");
      setDeleting(false);
    }
  }

  if (editing) {
    return (
      <li className="rounded-md border border-slate-200 p-3">
        <ScheduleOverrideForm
          employeeId={override.employee_id}
          existingOverride={override}
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
            {override.date} — {override.day_type}
          </div>
          {override.day_type === "working" && (
            <div className="text-slate-600 mt-1">
              {override.work_start ? override.work_start.slice(0, 5) : "—"}–
              {override.work_end ? override.work_end.slice(0, 5) : "—"}
              {override.overtime_minutes ? (
                <span className="ml-2 text-amber-700">
                  +{override.overtime_minutes} min overtime (not used by the optimizer yet)
                </span>
              ) : null}
            </div>
          )}
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

interface ScheduleOverrideFormProps {
  employeeId: number;
  existingOverride?: EmployeeScheduleDayOverride;
  onSaved: () => void | Promise<void>;
  onCancel?: () => void;
}

function ScheduleOverrideForm({
  employeeId,
  existingOverride,
  onSaved,
  onCancel,
}: ScheduleOverrideFormProps) {
  const [date, setDate] = useState(existingOverride?.date ?? "");
  const [dayType, setDayType] = useState<DayType>(existingOverride?.day_type ?? "working");
  const [workStart, setWorkStart] = useState(existingOverride?.work_start?.slice(0, 5) ?? "");
  const [workEnd, setWorkEnd] = useState(existingOverride?.work_end?.slice(0, 5) ?? "");
  const [maxHoursPerDay, setMaxHoursPerDay] = useState(
    existingOverride?.max_hours_per_day != null ? String(existingOverride.max_hours_per_day) : ""
  );
  const [overtimeMinutes, setOvertimeMinutes] = useState(
    existingOverride?.overtime_minutes != null ? String(existingOverride.overtime_minutes) : ""
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!existingOverride && !date) return;
    setSubmitting(true);
    setError(null);
    try {
      const isWorking = dayType === "working";
      const payload = {
        date,
        day_type: dayType,
        work_start: isWorking && workStart ? workStart : null,
        work_end: isWorking && workEnd ? workEnd : null,
        max_hours_per_day:
          isWorking && maxHoursPerDay ? Number(maxHoursPerDay) : null,
        overtime_minutes: isWorking && overtimeMinutes ? Number(overtimeMinutes) : null,
      };
      if (existingOverride) {
        await updateScheduleOverride(existingOverride.id, payload);
      } else {
        await createScheduleOverride(employeeId, payload);
      }
      await onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save day override");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mb-3 flex flex-col gap-2 rounded-md border border-slate-200 bg-white p-3"
    >
      <div className="flex gap-2">
        {!existingOverride && (
          <input
            type="date"
            value={date}
            onChange={(event) => setDate(event.target.value)}
            className="text-sm border border-slate-300 rounded-md px-2 py-1"
            required
          />
        )}
        <select
          value={dayType}
          onChange={(event) => setDayType(event.target.value as DayType)}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
        >
          <option value="working">Working (adjusted hours)</option>
          <option value="holiday">Holiday</option>
          <option value="sick">Sick</option>
        </select>
      </div>
      {dayType === "working" && (
        <>
          <div className="flex gap-2">
            <input
              type="time"
              value={workStart}
              onChange={(event) => setWorkStart(event.target.value)}
              className="text-sm border border-slate-300 rounded-md px-2 py-1"
              placeholder="Start"
            />
            <input
              type="time"
              value={workEnd}
              onChange={(event) => setWorkEnd(event.target.value)}
              className="text-sm border border-slate-300 rounded-md px-2 py-1"
              placeholder="End"
            />
            <input
              type="number"
              min={1}
              step="any"
              value={maxHoursPerDay}
              onChange={(event) => setMaxHoursPerDay(event.target.value)}
              placeholder="Max hours/day (optional)"
              className="text-sm border border-slate-300 rounded-md px-2 py-1 w-44"
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">
              Overtime (minutes) — not currently used by the route optimizer
            </label>
            <input
              type="number"
              min={0}
              value={overtimeMinutes}
              onChange={(event) => setOvertimeMinutes(event.target.value)}
              placeholder="0"
              className="text-sm border border-slate-300 rounded-md px-2 py-1 w-44"
            />
          </div>
        </>
      )}
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

interface BulkMarkFormProps {
  employeeId: number;
  onSaved: () => void | Promise<void>;
}

function BulkMarkForm({ employeeId, onSaved }: BulkMarkFormProps) {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [dayType, setDayType] = useState<"holiday" | "sick">("holiday");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!startDate || !endDate) return;
    setSubmitting(true);
    setError(null);
    try {
      await createScheduleOverridesBulk(employeeId, {
        start_date: startDate,
        end_date: endDate,
        day_type: dayType,
      });
      await onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to mark days");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mb-3 flex flex-wrap items-end gap-2 rounded-md border border-slate-200 bg-white p-3"
    >
      <input
        type="date"
        value={startDate}
        onChange={(event) => setStartDate(event.target.value)}
        className="text-sm border border-slate-300 rounded-md px-2 py-1"
        required
      />
      <span className="text-sm text-slate-400">to</span>
      <input
        type="date"
        value={endDate}
        onChange={(event) => setEndDate(event.target.value)}
        className="text-sm border border-slate-300 rounded-md px-2 py-1"
        required
      />
      <select
        value={dayType}
        onChange={(event) => setDayType(event.target.value as "holiday" | "sick")}
        className="text-sm border border-slate-300 rounded-md px-2 py-1"
      >
        <option value="holiday">Holiday</option>
        <option value="sick">Sick</option>
      </select>
      <button
        type="submit"
        disabled={submitting}
        className="text-sm px-3 py-1.5 rounded-md bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-50"
      >
        {submitting ? "Marking…" : "Mark"}
      </button>
      {error && <p className="text-xs text-red-600 w-full">{error}</p>}
    </form>
  );
}
