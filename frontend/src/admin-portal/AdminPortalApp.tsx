import { useEffect, useState } from "react";
import { listContracts, listCustomerLocations, listEmployees, listRegions, listSkills } from "../api";
import type { Contract, CustomerLocation, Employee, Region, Skill } from "../types";
import { RegionsView } from "./RegionsView";
import { SkillsView } from "./SkillsView";

type Entity = "regions" | "skills";

const ENTITY_LABELS: Record<Entity, string> = {
  regions: "Regions",
  skills: "Skills",
};

const ENTITY_ORDER: Entity[] = ["regions", "skills"];

export function AdminPortalApp() {
  const [entity, setEntity] = useState<Entity>("regions");
  const [regions, setRegions] = useState<Region[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [customerLocations, setCustomerLocations] = useState<CustomerLocation[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  async function reload() {
    const [regionsData, skillsData, employeesData, customerLocationsData, contractsData] =
      await Promise.all([
        listRegions(),
        listSkills(),
        listEmployees(),
        listCustomerLocations(),
        listContracts(),
      ]);
    setRegions(regionsData);
    setSkills(skillsData);
    setEmployees(employeesData);
    setCustomerLocations(customerLocationsData);
    setContracts(contractsData);
  }

  useEffect(() => {
    reload()
      .catch((err) => setLoadError(err instanceof Error ? err.message : "Failed to load data"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="p-8 text-slate-500">Loading…</div>;
  }

  if (loadError) {
    return <div className="p-8 text-red-600">Failed to load data: {loadError}</div>;
  }

  return (
    <div className="min-h-screen bg-slate-50 flex">
      <aside className="w-56 shrink-0 bg-white border-r border-slate-200 p-4">
        <h1 className="text-lg font-semibold text-slate-900 mb-4">Admin Portal</h1>
        <nav className="flex flex-col gap-1">
          {ENTITY_ORDER.map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => setEntity(key)}
              className={`text-left rounded-md px-3 py-2 text-sm font-medium ${
                entity === key
                  ? "bg-slate-900 text-white"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {ENTITY_LABELS[key]}
            </button>
          ))}
        </nav>
      </aside>
      <main className="flex-1 p-8">
        {entity === "regions" && (
          <RegionsView
            regions={regions}
            employees={employees}
            customerLocations={customerLocations}
            onChanged={reload}
          />
        )}
        {entity === "skills" && (
          <SkillsView skills={skills} employees={employees} contracts={contracts} onChanged={reload} />
        )}
      </main>
    </div>
  );
}
