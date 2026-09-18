import { useEffect, useState } from "react";
import {
  listContracts,
  listCustomerLocations,
  listCustomers,
  listEmployees,
  listProducts,
  listRegions,
  listServiceOrderTypes,
  listServiceRequests,
  listServiceVisits,
  listSkills,
  listUsers,
  logout,
} from "../api";
import { useRequireRole } from "../shared/auth";
import type {
  Contract,
  Customer,
  CustomerLocation,
  Employee,
  Product,
  Region,
  ServiceOrderType,
  ServiceRequest,
  ServiceVisit,
  Skill,
  User,
} from "../types";
import { ContractsView } from "./ContractsView";
import { CustomerLocationsView } from "./CustomerLocationsView";
import { CustomersView } from "./CustomersView";
import { DemoScheduleView } from "./DemoScheduleView";
import { ProductsView } from "./ProductsView";
import { RegionsView } from "./RegionsView";
import { ServiceOrderTypesView } from "./ServiceOrderTypesView";
import { ServiceRequestsView } from "./ServiceRequestsView";
import { SkillsView } from "./SkillsView";
import { UsersView } from "./UsersView";

async function handleLogout() {
  await logout();
  window.location.href = "/login.html";
}

type Entity =
  | "regions"
  | "products"
  | "skills"
  | "service-order-types"
  | "contracts"
  | "customers"
  | "customer-locations"
  | "users"
  | "service-requests"
  | "demo";

const ENTITY_LABELS: Record<Entity, string> = {
  regions: "Regions",
  products: "Products",
  skills: "Skills",
  "service-order-types": "Service Order Types",
  contracts: "Contracts",
  customers: "Customers",
  "customer-locations": "Customer Locations",
  users: "Users",
  "service-requests": "Service Requests",
  demo: "Demo",
};

const ENTITY_ORDER: Entity[] = [
  "regions",
  "products",
  "skills",
  "service-order-types",
  "contracts",
  "customers",
  "customer-locations",
  "users",
  "service-requests",
  "demo",
];

export function AdminPortalApp() {
  const { loading: authLoading } = useRequireRole("admin");
  const [entity, setEntity] = useState<Entity>("regions");
  const [regions, setRegions] = useState<Region[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [serviceOrderTypes, setServiceOrderTypes] = useState<ServiceOrderType[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [customerLocations, setCustomerLocations] = useState<CustomerLocation[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [serviceVisits, setServiceVisits] = useState<ServiceVisit[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [serviceRequests, setServiceRequests] = useState<ServiceRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  async function reload() {
    const [
      regionsData,
      productsData,
      skillsData,
      serviceOrderTypesData,
      employeesData,
      customersData,
      customerLocationsData,
      contractsData,
      serviceVisitsData,
      usersData,
      serviceRequestsData,
    ] = await Promise.all([
      listRegions(),
      listProducts(),
      listSkills(),
      listServiceOrderTypes(),
      listEmployees(),
      listCustomers(),
      listCustomerLocations(),
      listContracts(),
      listServiceVisits(),
      listUsers(),
      listServiceRequests(),
    ]);
    setRegions(regionsData);
    setProducts(productsData);
    setSkills(skillsData);
    setServiceOrderTypes(serviceOrderTypesData);
    setEmployees(employeesData);
    setCustomers(customersData);
    setCustomerLocations(customerLocationsData);
    setContracts(contractsData);
    setServiceVisits(serviceVisitsData);
    setUsers(usersData);
    setServiceRequests(serviceRequestsData);
  }

  useEffect(() => {
    reload()
      .catch((err) => setLoadError(err instanceof Error ? err.message : "Failed to load data"))
      .finally(() => setLoading(false));
  }, []);

  if (authLoading || loading) {
    return <div className="p-8 text-slate-500">Loading…</div>;
  }

  if (loadError) {
    return <div className="p-8 text-red-600">Failed to load data: {loadError}</div>;
  }

  return (
    <div className="min-h-screen bg-slate-50 flex">
      <aside className="w-56 shrink-0 bg-white border-r border-slate-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-lg font-semibold text-slate-900">Admin Portal</h1>
          <button
            type="button"
            onClick={handleLogout}
            className="text-xs text-slate-500 hover:text-slate-800 underline"
          >
            Log out
          </button>
        </div>
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
        <div className="mt-6 pt-4 border-t border-slate-200">
          <div className="text-xs uppercase tracking-wide text-slate-400 mb-2 px-3">
            Other portals
          </div>
          <nav className="flex flex-col gap-1">
            <a
              href="/index.html"
              className="text-left rounded-md px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
            >
              Planning
            </a>
            <a
              href="/customer-portal.html"
              className="text-left rounded-md px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
            >
              Customer Portal
            </a>
            <a
              href="/employee-management.html"
              className="text-left rounded-md px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
            >
              Employee Management
            </a>
          </nav>
        </div>
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
        {entity === "products" && (
          <ProductsView
            products={products}
            contracts={contracts}
            skills={skills}
            serviceOrderTypes={serviceOrderTypes}
            onChanged={reload}
          />
        )}
        {entity === "skills" && (
          <SkillsView skills={skills} products={products} onChanged={reload} />
        )}
        {entity === "service-order-types" && (
          <ServiceOrderTypesView
            serviceOrderTypes={serviceOrderTypes}
            products={products}
            onChanged={reload}
          />
        )}
        {entity === "contracts" && (
          <ContractsView
            contracts={contracts}
            customers={customers}
            customerLocations={customerLocations}
            serviceVisits={serviceVisits}
            products={products}
            onChanged={reload}
          />
        )}
        {entity === "customers" && (
          <CustomersView customers={customers} onChanged={reload} />
        )}
        {entity === "customer-locations" && (
          <CustomerLocationsView
            customerLocations={customerLocations}
            customers={customers}
            onChanged={reload}
          />
        )}
        {entity === "users" && (
          <UsersView users={users} customers={customers} onChanged={reload} />
        )}
        {entity === "service-requests" && (
          <ServiceRequestsView serviceRequests={serviceRequests} onChanged={reload} />
        )}
        {entity === "demo" && <DemoScheduleView onChanged={reload} />}
      </main>
    </div>
  );
}
