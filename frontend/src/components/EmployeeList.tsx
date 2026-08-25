import { useMemo, useState } from "react";
import type { Employee } from "../types";
import { collectFilterOptions, filterItems } from "../lib/listFilter";
import { InfoBox } from "./InfoBox";
import { ListFilterBar } from "./ListFilterBar";

export function EmployeeList({ employees }: { employees: Employee[] }) {
  const [search, setSearch] = useState("");
  const [regionIds, setRegionIds] = useState<number[]>([]);
  const [skillIds, setSkillIds] = useState<number[]>([]);

  const extract = (employee: Employee) => ({
    name: employee.name,
    regions: employee.regions,
    skills: employee.skills,
  });

  const { regions: regionOptions, skills: skillOptions } = useMemo(
    () => collectFilterOptions(employees, extract),
    [employees]
  );

  const filteredEmployees = useMemo(
    () => filterItems(employees, extract, search, regionIds, skillIds),
    [employees, search, regionIds, skillIds]
  );

  return (
    <section className="bg-white rounded-lg border border-slate-200 p-4">
      <h2 className="text-lg font-medium text-slate-900 mb-3">Employees</h2>
      <ListFilterBar
        search={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search by name…"
        regionOptions={regionOptions}
        selectedRegionIds={regionIds}
        onRegionIdsChange={setRegionIds}
        skillOptions={skillOptions}
        selectedSkillIds={skillIds}
        onSkillIdsChange={setSkillIds}
      />
      {employees.length === 0 ? (
        <p className="text-sm text-slate-500">No employees.</p>
      ) : filteredEmployees.length === 0 ? (
        <p className="text-sm text-slate-500">No matches for the current search/filters.</p>
      ) : (
        <ul className="space-y-2">
          {filteredEmployees.map((employee) => (
            <li
              key={employee.id}
              className="text-sm border border-slate-100 rounded-md p-2"
            >
              <InfoBox
                summary={
                  <div>
                    <div className="font-medium text-slate-800">{employee.name}</div>
                    <div className="text-slate-500">
                      {employee.work_start.slice(0, 5)}–{employee.work_end.slice(0, 5)}
                    </div>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {employee.regions.map((region) => (
                        <span
                          key={region.id}
                          className="inline-block rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600"
                        >
                          {region.name}
                        </span>
                      ))}
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
                }
              >
                <div>
                  Regions: {employee.regions.map((region) => region.name).join(", ")}
                </div>
                <div>
                  Location: {employee.latitude.toFixed(4)}, {employee.longitude.toFixed(4)}
                </div>
              </InfoBox>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
