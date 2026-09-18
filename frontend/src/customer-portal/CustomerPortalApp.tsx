import { useEffect, useState } from "react";
import {
  listContracts,
  listCustomerLocations,
  listCustomers,
  listServiceVisits,
  logout,
  syncCustomers,
} from "../api";
import { useRequireRole } from "../shared/auth";
import type { Contract, Customer, CustomerLocation, ServiceVisit } from "../types";
import { ContractsView } from "./ContractsView";
import { CustomerDashboard } from "./CustomerDashboard";
import { CustomerLocationsView } from "./CustomerLocationsView";
import { CustomersView } from "./CustomersView";

async function handleLogout() {
  await logout();
  window.location.href = "/login.html";
}

type Entity = "customers" | "customer-locations" | "contracts";

const ENTITY_LABELS: Record<Entity, string> = {
  customers: "Customers",
  "customer-locations": "Customer Locations",
  contracts: "Contracts",
};

const ENTITY_ORDER: Entity[] = ["customers", "customer-locations", "contracts"];

export function CustomerPortalApp() {
  const { user, loading: authLoading } = useRequireRole("any");
  const [entity, setEntity] = useState<Entity>("customers");
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [customerLocations, setCustomerLocations] = useState<CustomerLocation[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [serviceVisits, setServiceVisits] = useState<ServiceVisit[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [viewingAsCustomerId, setViewingAsCustomerId] = useState<number | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([listCustomers(), listCustomerLocations(), listContracts(), listServiceVisits()])
      .then(([customersData, customerLocationsData, contractsData, serviceVisitsData]) => {
        setCustomers(customersData);
        setCustomerLocations(customerLocationsData);
        setContracts(contractsData);
        setServiceVisits(serviceVisitsData);
      })
      .catch((err) =>
        setLoadError(err instanceof Error ? err.message : "Failed to load data")
      )
      .finally(() => setLoading(false));
  }, []);

  async function reloadContractsAndVisits() {
    const [contractsData, serviceVisitsData] = await Promise.all([
      listContracts(),
      listServiceVisits(),
    ]);
    setContracts(contractsData);
    setServiceVisits(serviceVisitsData);
  }

  if (authLoading || loading) {
    return <div className="p-8 text-slate-500">Loading…</div>;
  }

  if (loadError) {
    return <div className="p-8 text-red-600">Failed to load data: {loadError}</div>;
  }

  const isAdmin = user?.is_admin ?? false;
  // The one customer currently "in scope": explicitly via the admin switcher, or
  // automatically the sole customer of a non-admin session. Once set, the
  // consolidated dashboard replaces the Customers/Customer Locations/Contracts
  // tabs entirely rather than just the old Customer-detail view (see design.md).
  const dashboardCustomerId = isAdmin
    ? viewingAsCustomerId
    : user && user.customer_ids.length === 1
      ? user.customer_ids[0]
      : null;

  async function handleRefresh() {
    setRefreshing(true);
    setRefreshError(null);
    try {
      await syncCustomers();
      const [customersData, customerLocationsData, contractsData] = await Promise.all([
        listCustomers(),
        listCustomerLocations(),
        listContracts(),
      ]);
      setCustomers(customersData);
      setCustomerLocations(customerLocationsData);
      setContracts(contractsData);
    } catch (err) {
      setRefreshError(err instanceof Error ? err.message : "Failed to refresh");
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex">
      <aside className="w-56 shrink-0 bg-white border-r border-slate-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-lg font-semibold text-slate-900">Customer Portal</h1>
          <button
            type="button"
            onClick={handleLogout}
            className="text-xs text-slate-500 hover:text-slate-800 underline"
          >
            Log out
          </button>
        </div>

        {isAdmin && (
          <>
            <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">
              Viewing as
            </label>
            <select
              value={viewingAsCustomerId ?? ""}
              onChange={(event) =>
                setViewingAsCustomerId(
                  event.target.value === "" ? null : Number(event.target.value)
                )
              }
              className="w-full text-sm border border-slate-300 rounded-md px-2 py-1 mb-4"
            >
              <option value="">All customers</option>
              {customers.map((customer) => (
                <option key={customer.id} value={customer.id}>
                  {customer.name}
                </option>
              ))}
            </select>
          </>
        )}

        {dashboardCustomerId === null && (
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
        )}
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
              href="/employee-management.html"
              className="text-left rounded-md px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
            >
              Employee Management
            </a>
            <a
              href="/admin-portal.html"
              className="text-left rounded-md px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
            >
              Admin Portal
            </a>
          </nav>
        </div>
      </aside>
      <main className="flex-1 p-8">
        {dashboardCustomerId !== null ? (
          <CustomerDashboard customerId={dashboardCustomerId} />
        ) : (
          <>
            {entity === "customers" && (
              <div>
                {refreshError && (
                  <p className="text-sm text-red-600 mb-3">
                    Failed to refresh: {refreshError}
                  </p>
                )}
                <CustomersView
                  customers={customers}
                  onRefresh={handleRefresh}
                  refreshing={refreshing}
                />
              </div>
            )}
            {entity === "customer-locations" && (
              <CustomerLocationsView
                customerLocations={customerLocations}
                contracts={contracts}
              />
            )}
            {entity === "contracts" && (
              <ContractsView
                contracts={contracts}
                serviceVisits={serviceVisits}
                onChanged={reloadContractsAndVisits}
              />
            )}
          </>
        )}
      </main>
    </div>
  );
}
