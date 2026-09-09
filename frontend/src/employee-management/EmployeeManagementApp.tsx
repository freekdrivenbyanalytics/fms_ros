import { useEffect, useState } from "react";
import { listEmployees, listProducts, listRegions } from "../api";
import type { Employee, Product, Region } from "../types";
import { EmployeesView } from "./EmployeesView";

export function EmployeeManagementApp() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  async function reload() {
    const [employeesData, regionsData, productsData] = await Promise.all([
      listEmployees(),
      listRegions(),
      listProducts(),
    ]);
    setEmployees(employeesData);
    setRegions(regionsData);
    setProducts(productsData);
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
        <h1 className="text-lg font-semibold text-slate-900 mb-4">Employee Management</h1>
      </aside>
      <main className="flex-1 p-8">
        <EmployeesView employees={employees} regions={regions} products={products} onChanged={reload} />
      </main>
    </div>
  );
}
