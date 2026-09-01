import { useEffect, useState } from "react";
import { listCustomerLocations, listEmployees, listRegions } from "../api";
import type { CustomerLocation, Employee, Region } from "../types";
import { RegionsView } from "./RegionsView";

export function AdminPortalApp() {
  const [regions, setRegions] = useState<Region[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [customerLocations, setCustomerLocations] = useState<CustomerLocation[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  async function reload() {
    const [regionsData, employeesData, customerLocationsData] = await Promise.all([
      listRegions(),
      listEmployees(),
      listCustomerLocations(),
    ]);
    setRegions(regionsData);
    setEmployees(employeesData);
    setCustomerLocations(customerLocationsData);
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
      </aside>
      <main className="flex-1 p-8">
        <RegionsView
          regions={regions}
          employees={employees}
          customerLocations={customerLocations}
          onChanged={reload}
        />
      </main>
    </div>
  );
}
