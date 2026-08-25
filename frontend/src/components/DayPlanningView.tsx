import { useState } from "react";
import type { Assignment, Employee } from "../types";
import { InfoBox } from "./InfoBox";

interface Props {
  employees: Employee[];
  assignments: Assignment[];
}

const WINDOW_START_HOUR = 6;
const WINDOW_END_HOUR = 20;
const HOUR_MARKS = [6, 8, 10, 12, 14, 16, 18, 20];

export function DayPlanningView({ employees, assignments }: Props) {
  const [date, setDate] = useState(() => todayKey());

  function goToPrevDay() {
    setDate((prev) => shiftDateKey(prev, -1));
  }

  function goToNextDay() {
    setDate((prev) => shiftDateKey(prev, 1));
  }

  const dayAssignments = assignments.filter(
    (assignment) => localDateKey(assignment.planned_start) === date
  );
  const assignmentsByEmployee = new Map<number, Assignment[]>();
  for (const assignment of dayAssignments) {
    const list = assignmentsByEmployee.get(assignment.employee_id) ?? [];
    list.push(assignment);
    assignmentsByEmployee.set(assignment.employee_id, list);
  }

  return (
    <section className="bg-white rounded-lg border border-slate-200 p-4">
      <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
        <h2 className="text-lg font-medium text-slate-900">Day Planning</h2>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={goToPrevDay}
            aria-label="Previous day"
            className="rounded-md border border-slate-200 px-2 py-1 text-sm text-slate-600 hover:bg-slate-50"
          >
            ‹
          </button>
          <input
            type="date"
            value={date}
            onChange={(event) => setDate(event.target.value)}
            className="rounded-md border border-slate-200 px-2 py-1 text-sm text-slate-700"
          />
          <button
            type="button"
            onClick={goToNextDay}
            aria-label="Next day"
            className="rounded-md border border-slate-200 px-2 py-1 text-sm text-slate-600 hover:bg-slate-50"
          >
            ›
          </button>
        </div>
      </div>

      {employees.length === 0 ? (
        <p className="text-sm text-slate-500">No employees.</p>
      ) : (
        <div>
          <div className="grid grid-cols-[200px_1fr] mb-1">
            <div />
            <div className="relative h-5 text-xs text-slate-400">
              {HOUR_MARKS.map((hour) => (
                <span
                  key={hour}
                  className="absolute -translate-x-1/2"
                  style={{ left: `${hourOffsetPercent(hour)}%` }}
                >
                  {formatHour(hour)}
                </span>
              ))}
            </div>
          </div>

          <div className="border-t border-slate-100 divide-y divide-slate-100">
            {employees.map((employee) => {
              const employeeAssignments = assignmentsByEmployee.get(employee.id) ?? [];
              return (
                <div key={employee.id} className="grid grid-cols-[200px_1fr] items-stretch">
                  <div className="py-2 pr-3 text-sm">
                    <div className="font-medium text-slate-800">{employee.name}</div>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {employee.skills.map((skill) => (
                        <span
                          key={skill.id}
                          className="inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700"
                        >
                          {skill.name}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="relative h-16 border-l border-slate-100">
                    {employeeAssignments.map((assignment) => {
                      const left = timeOffsetPercent(assignment.planned_start);
                      const right = timeOffsetPercent(assignment.planned_end);
                      const width = Math.max(right - left, 2);
                      const visit = assignment.service_visit;
                      const location = visit.contract.customer_location;

                      return (
                        <div
                          key={assignment.service_visit_id}
                          className="absolute z-10 top-2 bottom-2 rounded-md border border-sky-300 bg-sky-100 px-2 py-1 text-xs shadow-sm"
                          style={{ left: `${left}%`, width: `${width}%` }}
                        >
                          <InfoBox
                            summary={
                              <div className="truncate font-medium text-sky-900">
                                {location.customer.name}
                              </div>
                            }
                          >
                            <div>{location.customer.name}</div>
                            <div>{location.address}</div>
                            <div>{location.region.name}</div>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {visit.contract.required_skills.map((skill) => (
                                <span
                                  key={skill.id}
                                  className="inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700"
                                >
                                  {skill.name}
                                </span>
                              ))}
                            </div>
                            <div className="mt-1">
                              {formatTimeRange(assignment.planned_start, assignment.planned_end)}
                            </div>
                          </InfoBox>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
}

function localDateKey(iso: string): string {
  const d = new Date(iso);
  return formatDateKey(d);
}

function todayKey(): string {
  return formatDateKey(new Date());
}

function formatDateKey(date: Date): string {
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function shiftDateKey(key: string, deltaDays: number): string {
  const [year, month, day] = key.split("-").map(Number);
  const date = new Date(year, month - 1, day);
  date.setDate(date.getDate() + deltaDays);
  return formatDateKey(date);
}

function timeOffsetPercent(iso: string): number {
  const d = new Date(iso);
  const minutes = d.getHours() * 60 + d.getMinutes();
  const windowStart = WINDOW_START_HOUR * 60;
  const windowEnd = WINDOW_END_HOUR * 60;
  const clamped = Math.min(Math.max(minutes, windowStart), windowEnd);
  return ((clamped - windowStart) / (windowEnd - windowStart)) * 100;
}

function hourOffsetPercent(hour: number): number {
  const windowStart = WINDOW_START_HOUR * 60;
  const windowEnd = WINDOW_END_HOUR * 60;
  return (((hour * 60) - windowStart) / (windowEnd - windowStart)) * 100;
}

function formatHour(hour: number): string {
  return `${String(hour).padStart(2, "0")}:00`;
}

function formatTimeRange(start: string, end: string): string {
  const fmt = (value: string) =>
    new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return `${fmt(start)} – ${fmt(end)}`;
}
