import { useEffect, useState } from "react";
import {
  listContracts,
  listCustomerLocations,
  listCustomers,
  listEmployees,
  listRegions,
  listSkills,
} from "../api";
import type { Contract, Customer, CustomerLocation, Employee, Region, Skill } from "../types";
import { ContractsView } from "./ContractsView";
import { CustomerLocationsView } from "./CustomerLocationsView";
import { CustomersView } from "./CustomersView";
import { EmployeesView } from "./EmployeesView";
import { RegionsView } from "./RegionsView";
import { SkillsView } from "./SkillsView";

type Entity =
  | "employees"
  | "customers"
  | "customer-locations"
  | "contracts"
  | "skills"
  | "regions";

const ENTITY_LABELS: Record<Entity, string> = {
  employees: "Employees",
  customers: "Customers",
  "customer-locations": "Customer Locations",
  contracts: "Contracts",
  skills: "Skills",
  regions: "Regions",
};

const ENTITY_ORDER: Entity[] = [
  "employees",
  "customers",
  "customer-locations",
  "contracts",
  "skills",
  "regions",
];

export function CustomerPortalApp() {
  const [entity, setEntity] = useState<Entity>("employees");
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [customerLocations, setCustomerLocations] = useState<CustomerLocation[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      listEmployees(),
      listCustomers(),
      listCustomerLocations(),
      listContracts(),
      listRegions(),
      listSkills(),
    ])
      .then(
        ([
          employeesData,
          customersData,
          customerLocationsData,
          contractsData,
          regionsData,
          skillsData,
        ]) => {
          setEmployees(employeesData);
          setCustomers(customersData);
          setCustomerLocations(customerLocationsData);
          setContracts(contractsData);
          setRegions(regionsData);
          setSkills(skillsData);
        }
      )
      .catch((err) =>
        setLoadError(err instanceof Error ? err.message : "Failed to load data")
      )
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
        <h1 className="text-lg font-semibold text-slate-900 mb-4">Customer Portal</h1>
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
        {entity === "employees" && <EmployeesView employees={employees} />}
        {entity === "customers" && (
          <CustomersView customers={customers} customerLocations={customerLocations} />
        )}
        {entity === "customer-locations" && (
          <CustomerLocationsView customerLocations={customerLocations} contracts={contracts} />
        )}
        {entity === "contracts" && <ContractsView contracts={contracts} />}
        {entity === "skills" && (
          <SkillsView skills={skills} employees={employees} contracts={contracts} />
        )}
        {entity === "regions" && (
          <RegionsView
            regions={regions}
            employees={employees}
            customerLocations={customerLocations}
          />
        )}
      </main>
    </div>
  );
}
