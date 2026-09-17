import { useState, type FormEvent } from "react";
import { createProduct, deleteProduct, syncProducts, updateProduct } from "../api";
import type {
  Contract,
  ContractLine,
  Product,
  ProductType,
  ServiceOrderType,
  Skill,
} from "../types";
import { BackButton, DetailField } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";

interface Props {
  products: Product[];
  contracts: Contract[];
  skills: Skill[];
  serviceOrderTypes: ServiceOrderType[];
  onChanged: () => void | Promise<void>;
}

export function ProductsView({ products, contracts, skills, serviceOrderTypes, onChanged }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);
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
    const productLines: ContractLine[] = contracts.flatMap((contract) =>
      contract.lines.filter((line) =>
        line.required_products.some((product) => product.id === selected.id)
      )
    );
    return (
      <ProductDetail
        product={selected}
        productLines={productLines}
        skills={skills}
        serviceOrderTypes={serviceOrderTypes}
        onChanged={onChanged}
        onDeleted={() => setSelectedId(null)}
        onBack={() => setSelectedId(null)}
      />
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900">Products</h2>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleRefresh}
            disabled={refreshing}
            className="text-sm px-3 py-1.5 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50 disabled:opacity-50"
          >
            {refreshing ? "Refreshing…" : "Refresh from Tripletex"}
          </button>
          <button
            type="button"
            onClick={() => setCreating((prev) => !prev)}
            className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white"
          >
            {creating ? "Cancel" : "Create Product"}
          </button>
        </div>
      </div>
      {refreshMessage && <p className="text-sm text-red-600 mb-3">{refreshMessage}</p>}

      {creating && (
        <CreateProductForm
          skills={skills}
          serviceOrderTypes={serviceOrderTypes}
          onCreated={async (product) => {
            setCreating(false);
            await onChanged();
            setSelectedId(product.id);
          }}
        />
      )}

      <ListTable
        items={products}
        getKey={(product) => product.id}
        onSelect={(product) => setSelectedId(product.id)}
        emptyMessage="No products."
        columns={[
          { header: "Number", render: (product) => product.number },
          { header: "Type", render: (product) => product.product_type },
          { header: "Name", render: (product) => product.name },
          {
            header: "Service Order Type",
            render: (product) => product.service_order_type?.name ?? "—",
          },
          {
            header: "Skills",
            render: (product) =>
              product.skills.length === 0
                ? "—"
                : product.skills.map((skill) => skill.name).join(", "),
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

interface CreateProductFormProps {
  skills: Skill[];
  serviceOrderTypes: ServiceOrderType[];
  onCreated: (product: Product) => void | Promise<void>;
}

function CreateProductForm({ skills, serviceOrderTypes, onCreated }: CreateProductFormProps) {
  const [productType, setProductType] = useState<ProductType>("TJN");
  const [number, setNumber] = useState("");
  const [name, setName] = useState("");
  const [skillIds, setSkillIds] = useState<number[]>([]);
  const [serviceOrderTypeId, setServiceOrderTypeId] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggleSkill(skillId: number) {
    setSkillIds((prev) =>
      prev.includes(skillId) ? prev.filter((id) => id !== skillId) : [...prev, skillId]
    );
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!number || !name) return;
    setSubmitting(true);
    setError(null);
    try {
      const product = await createProduct({
        product_type: productType,
        number,
        name,
        skill_ids: skillIds,
        service_order_type_id: serviceOrderTypeId,
      });
      await onCreated(product);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create product");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mb-4 flex flex-wrap items-end gap-2 rounded-md border border-slate-200 bg-white p-3"
    >
      <div>
        <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">Type</label>
        <select
          value={productType}
          onChange={(event) => setProductType(event.target.value as ProductType)}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
        >
          <option value="TJN">TJN — Tjeneste</option>
          <option value="PRD">PRD — Produkt</option>
        </select>
      </div>
      <div>
        <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">Number</label>
        <input
          type="text"
          value={number}
          onChange={(event) => setNumber(event.target.value)}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
          required
        />
      </div>
      <div>
        <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">Name</label>
        <input
          type="text"
          value={name}
          onChange={(event) => setName(event.target.value)}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
          required
        />
      </div>
      <div>
        <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">
          Service Order Type
        </label>
        <select
          value={serviceOrderTypeId ?? ""}
          onChange={(event) =>
            setServiceOrderTypeId(event.target.value ? Number(event.target.value) : null)
          }
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
        >
          <option value="">None</option>
          {serviceOrderTypes.map((type) => (
            <option key={type.id} value={type.id}>
              {type.name}
            </option>
          ))}
        </select>
      </div>
      <div className="w-full">
        <label className="block text-xs uppercase tracking-wide text-slate-400 mb-1">
          Required Skills
        </label>
        <div className="flex flex-wrap gap-3">
          {skills.map((skill) => (
            <label key={skill.id} className="flex items-center gap-1 text-sm">
              <input
                type="checkbox"
                checked={skillIds.includes(skill.id)}
                onChange={() => toggleSkill(skill.id)}
              />
              {skill.name}
            </label>
          ))}
          {skills.length === 0 && <span className="text-sm text-slate-500">No skills yet.</span>}
        </div>
      </div>
      <button
        type="submit"
        disabled={submitting}
        className="text-sm px-3 py-1.5 rounded-md bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-50"
      >
        {submitting ? "Creating…" : "Create"}
      </button>
      {error && <p className="text-xs text-red-600 w-full">{error}</p>}
    </form>
  );
}

interface ProductDetailProps {
  product: Product;
  productLines: ContractLine[];
  skills: Skill[];
  serviceOrderTypes: ServiceOrderType[];
  onChanged: () => void | Promise<void>;
  onDeleted: () => void;
  onBack: () => void;
}

function ProductDetail({
  product,
  productLines,
  skills,
  serviceOrderTypes,
  onChanged,
  onDeleted,
  onBack,
}: ProductDetailProps) {
  const [productType, setProductType] = useState<ProductType>(product.product_type);
  const [number, setNumber] = useState(product.number);
  const [name, setName] = useState(product.name);
  const [skillIds, setSkillIds] = useState<number[]>(product.skills.map((skill) => skill.id));
  const [serviceOrderTypeId, setServiceOrderTypeId] = useState<number | null>(
    product.service_order_type?.id ?? null
  );
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggleSkill(skillId: number) {
    setSkillIds((prev) =>
      prev.includes(skillId) ? prev.filter((id) => id !== skillId) : [...prev, skillId]
    );
    setDirty(true);
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await updateProduct(product.id, {
        product_type: productType,
        number,
        name,
        skill_ids: skillIds,
        service_order_type_id: serviceOrderTypeId,
      });
      setDirty(false);
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save product");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    setError(null);
    try {
      await deleteProduct(product.id);
      await onChanged();
      onDeleted();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete product");
      setDeleting(false);
    }
  }

  return (
    <div>
      <BackButton label="Products" onClick={onBack} />
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-900">
          {product.number} {product.name}
        </h2>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleSave}
            disabled={saving || !dirty}
            className="text-sm px-3 py-1.5 rounded-md bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save Changes"}
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={deleting}
            className="text-sm px-3 py-1.5 rounded-md border border-red-300 text-red-700 hover:bg-red-50 disabled:opacity-50"
          >
            {deleting ? "Deleting…" : "Soft-delete Product"}
          </button>
        </div>
      </div>
      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      <DetailField label="Type">
        <select
          value={productType}
          onChange={(event) => {
            setProductType(event.target.value as ProductType);
            setDirty(true);
          }}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
        >
          <option value="TJN">TJN — Tjeneste</option>
          <option value="PRD">PRD — Produkt</option>
        </select>
      </DetailField>
      <DetailField label="Number">
        <input
          type="text"
          value={number}
          onChange={(event) => {
            setNumber(event.target.value);
            setDirty(true);
          }}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
        />
      </DetailField>
      <DetailField label="Name">
        <input
          type="text"
          value={name}
          onChange={(event) => {
            setName(event.target.value);
            setDirty(true);
          }}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
        />
      </DetailField>
      <DetailField label="Service Order Type">
        <select
          value={serviceOrderTypeId ?? ""}
          onChange={(event) => {
            setServiceOrderTypeId(event.target.value ? Number(event.target.value) : null);
            setDirty(true);
          }}
          className="text-sm border border-slate-300 rounded-md px-2 py-1"
        >
          <option value="">None</option>
          {serviceOrderTypes.map((type) => (
            <option key={type.id} value={type.id}>
              {type.name}
            </option>
          ))}
        </select>
      </DetailField>
      <DetailField label="Required Skills">
        <div className="flex flex-wrap gap-3">
          {skills.map((skill) => (
            <label key={skill.id} className="flex items-center gap-1 text-sm">
              <input
                type="checkbox"
                checked={skillIds.includes(skill.id)}
                onChange={() => toggleSkill(skill.id)}
              />
              {skill.name}
            </label>
          ))}
          {skills.length === 0 && <span className="text-sm text-slate-500">No skills yet.</span>}
        </div>
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
