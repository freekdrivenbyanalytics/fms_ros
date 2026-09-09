import { useState } from "react";
import { syncProducts } from "../api";
import type { Contract, ContractLine, Employee, Product } from "../types";
import { BackButton, DetailField } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";

interface Props {
  products: Product[];
  employees: Employee[];
  contracts: Contract[];
  onChanged: () => void | Promise<void>;
}

export function ProductsView({ products, employees, contracts, onChanged }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null);

  const selected = products.find((product) => product.id === selectedId) ?? null;

  async function handleRefresh() {
    setRefreshing(true);
    setRefreshMessage(null);
    try {
      await syncProducts();
      await onChanged();
    } catch (err) {
      setRefreshMessage(
        err instanceof Error ? err.message : "Failed to refresh products"
      );
    } finally {
      setRefreshing(false);
    }
  }

  if (selected) {
    const productEmployees = employees.filter((employee) =>
      employee.products.some((product) => product.id === selected.id)
    );
    const productLines: ContractLine[] = contracts.flatMap((contract) =>
      contract.lines.filter((line) =>
        line.required_products.some((product) => product.id === selected.id)
      )
    );
    return (
      <ProductDetail
        product={selected}
        productEmployees={productEmployees}
        productLines={productLines}
        onBack={() => setSelectedId(null)}
      />
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900">Products</h2>
        <button
          type="button"
          onClick={handleRefresh}
          disabled={refreshing}
          className="text-sm px-3 py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50 disabled:opacity-50"
        >
          {refreshing ? "Refreshing…" : "Refresh from Tripletex"}
        </button>
      </div>
      {refreshMessage && <p className="text-sm text-red-600 mb-3">{refreshMessage}</p>}

      <ListTable
        items={products}
        getKey={(product) => product.id}
        onSelect={(product) => setSelectedId(product.id)}
        emptyMessage="No products."
        columns={[
          { header: "Number", render: (product) => product.number },
          { header: "Name", render: (product) => product.name },
          {
            header: "Employees",
            render: (product) =>
              String(
                employees.filter((e) => e.products.some((p) => p.id === product.id)).length
              ),
          },
          {
            header: "Contract Lines",
            render: (product) =>
              String(
                contracts
                  .flatMap((c) => c.lines)
                  .filter((line) => line.required_products.some((p) => p.id === product.id))
                  .length
              ),
          },
        ]}
      />
    </div>
  );
}

interface ProductDetailProps {
  product: Product;
  productEmployees: Employee[];
  productLines: ContractLine[];
  onBack: () => void;
}

function ProductDetail({ product, productEmployees, productLines, onBack }: ProductDetailProps) {
  return (
    <div>
      <BackButton label="Products" onClick={onBack} />
      <h2 className="text-xl font-semibold text-slate-900 mb-4">
        {product.number} {product.name}
      </h2>

      <DetailField label="Employees who hold this product">
        {productEmployees.length === 0
          ? "—"
          : productEmployees.map((employee) => employee.name).join(", ")}
      </DetailField>
      <DetailField label="Contract lines requiring this product">
        {productLines.length === 0 ? (
          "—"
        ) : (
          <ul className="space-y-1">
            {productLines.map((line) => (
              <li key={line.id}>
                {line.customer_location.customer.name} — {line.customer_location.address}
              </li>
            ))}
          </ul>
        )}
      </DetailField>
    </div>
  );
}
