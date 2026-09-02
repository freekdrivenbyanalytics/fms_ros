import { useEffect, useState } from "react";
import {
  listContracts,
  listCustomerLocations,
  listCustomers,
  listEmployees,
  listRegions,
  listServiceVisits,
  listSkills,
} from "../api";
import type {
  Contract,
  Customer,
  CustomerLocation,
  Employee,
  Region,
  ServiceVisit,
  Skill,
} from "../types";
import { ContractsView } from "./ContractsView";
import { CustomerLocationsView } from "./CustomerLocationsView";
import { RegionsView } from "./RegionsView";
import { SkillsView } from "./SkillsView";

type Entity = "regions" | "skills" | "contracts" | "customer-locations";

const ENTITY_LABELS: Record<Entity, string> = {
  regions: "Regions",
  skills: "Skills",
  contracts: "Contracts",
  "customer-locations": "Customer Locations",
};

const ENTITY_ORDER: Entity[] = ["regions", "skills", "contracts", "customer-locations"];

export function AdminPortalApp() {
  const [entity, setEntity] = useState<Entity>("regions");
  const [regions, setRegions] = useState<Region[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [customerLocations, setCustomerLocations] = useState<CustomerLocation[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [serviceVisits, setServiceVisits] = useState<ServiceVisit[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  async function reload() {
    const [
      regionsData,
      skillsData,
      employeesData,
      customersData,
      customerLocationsData,
      contractsData,
      serviceVisitsData,
    ] = await Promise.all([
      listRegions(),
      listSkills(),
      listEmployees(),
      listCustomers(),
      listCustomerLocations(),
      listContracts(),
      listServiceVisits(),
    ]);
    setRegions(regionsData);
    setSkills(skillsData);
    setEmployees(employeesData);
    setCustomers(customersData);
    setCustomerLocations(customerLocationsData);
    setContracts(contractsData);
    setServiceVisits(serviceVisitsData);
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
        {entity === "contracts" && (
          <ContractsView
            contracts={contracts}
            customers={customers}
            customerLocations={customerLocations}
            serviceVisits={serviceVisits}
            skills={skills}
            onChanged={reload}
          />
        )}
        {entity === "customer-locations" && (
          <CustomerLocationsView customerLocations={customerLocations} onChanged={reload} />
        )}
      </main>
    </div>
  );
}
