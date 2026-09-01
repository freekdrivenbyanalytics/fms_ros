import { useEffect, useState } from "react";
import {
  listContracts,
  listCustomerLocations,
  listCustomers,
  listSkills,
  syncCustomers,
} from "../api";
import type { Contract, Customer, CustomerLocation, Skill } from "../types";
import { ContractsView } from "./ContractsView";
import { CustomerLocationsView } from "./CustomerLocationsView";
import { CustomersView } from "./CustomersView";

type Entity = "customers" | "customer-locations" | "contracts";

const ENTITY_LABELS: Record<Entity, string> = {
  customers: "Customers",
  "customer-locations": "Customer Locations",
  contracts: "Contracts",
};

const ENTITY_ORDER: Entity[] = ["customers", "customer-locations", "contracts"];

export function CustomerPortalApp() {
  const [entity, setEntity] = useState<Entity>("customers");
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [customerLocations, setCustomerLocations] = useState<CustomerLocation[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [viewingAsCustomerId, setViewingAsCustomerId] = useState<number | null>(null);
  const [pendingLocationId, setPendingLocationId] = useState<number | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([listCustomers(), listCustomerLocations(), listContracts(), listSkills()])
      .then(([customersData, customerLocationsData, contractsData, skillsData]) => {
        setCustomers(customersData);
        setCustomerLocations(customerLocationsData);
        setContracts(contractsData);
        setSkills(skillsData);
      })
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

  const scopedCustomer = customers.find((customer) => customer.id === viewingAsCustomerId);

  function handleSelectLocation(locationId: number) {
    setEntity("customer-locations");
    setPendingLocationId(locationId);
  }

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

  async function handleContractsChanged() {
    setContracts(await listContracts());
  }

  return (
    <div className="min-h-screen bg-slate-50 flex">
      <aside className="w-56 shrink-0 bg-white border-r border-slate-200 p-4">
        <h1 className="text-lg font-semibold text-slate-900 mb-4">Customer Portal</h1>

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
        {entity === "customers" && (
          <div>
            {refreshError && (
              <p className="text-sm text-red-600 mb-3">
                Failed to refresh: {refreshError}
              </p>
            )}
            <CustomersView
              customers={customers}
              customerLocations={customerLocations}
              scopedCustomer={scopedCustomer}
              onSelectLocation={handleSelectLocation}
              onRefresh={handleRefresh}
              refreshing={refreshing}
            />
          </div>
        )}
        {entity === "customer-locations" && (
          <CustomerLocationsView
            customerLocations={customerLocations}
            contracts={contracts}
            initialSelectedId={pendingLocationId ?? undefined}
            onInitialSelectionConsumed={() => setPendingLocationId(null)}
          />
        )}
        {entity === "contracts" && (
          <ContractsView
            contracts={contracts}
            customers={customers}
            customerLocations={customerLocations}
            skills={skills}
            onChanged={handleContractsChanged}
          />
        )}
      </main>
    </div>
  );
}
