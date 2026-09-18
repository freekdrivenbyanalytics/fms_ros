import { useEffect, useState, type FormEvent } from "react";
import { createServiceRequest, getCustomerDashboard, listProducts } from "../api";
import type { CustomerDashboard as CustomerDashboardData, Product } from "../types";
import { DetailField } from "../shared/DetailField";
import { BookAdHocVisit, formatInterval } from "./ContractsView";

interface Props {
  customerId: number;
}

export function CustomerDashboard({ customerId }: Props) {
  const [dashboard, setDashboard] = useState<CustomerDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  async function reload() {
    const data = await getCustomerDashboard(customerId);
    setDashboard(data);
  }

  useEffect(() => {
    setLoading(true);
    setLoadError(null);
    reload()
      .catch((err) => setLoadError(err instanceof Error ? err.message : "Failed to load data"))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customerId]);

  if (loading) {
    return <div className="text-slate-500">Loading…</div>;
  }

  if (loadError || dashboard === null) {
    return (
      <div className="text-red-600">Failed to load dashboard: {loadError ?? "Unknown error"}</div>
    );
  }

  const { customer, customer_locations, contracts, upcoming_visits } = dashboard;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900 mb-2">{customer.name}</h2>
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <DetailField label="ID">{customer.id}</DetailField>
          <DetailField label="Customer Number">{customer.customer_number ?? "—"}</DetailField>
          <DetailField label="Organization Number">
            {customer.organization_number || "—"}
          </DetailField>
          <DetailField label="Email">{customer.email || "—"}</DetailField>
          <DetailField label="Invoice Email">{customer.invoice_email || "—"}</DetailField>
          <DetailField label="Phone">{customer.phone_number || "—"}</DetailField>
          <DetailField label="Mobile">{customer.phone_number_mobile || "—"}</DetailField>
          <DetailField label="Language">{customer.language || "—"}</DetailField>
          <DetailField label="Type">
            {[
              customer.is_customer ? "Customer" : null,
              customer.is_supplier ? "Supplier" : null,
              customer.is_inactive ? "Inactive" : null,
            ]
              .filter(Boolean)
              .join(", ") || "—"}
          </DetailField>
          <DetailField label="Website">{customer.website || "—"}</DetailField>
        </div>
      </div>

      <section className="bg-white rounded-lg border border-slate-200 p-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-3">
          Locations
        </h3>
        {customer_locations.length === 0 ? (
          <p className="text-sm text-slate-400">No locations on file.</p>
        ) : (
          <ul className="space-y-1">
            {customer_locations.map((location) => (
              <li key={location.id} className="text-sm text-slate-700">
                {location.address} ({location.region?.name ?? "region not yet assigned"})
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="bg-white rounded-lg border border-slate-200 p-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-3">
          Upcoming Visits
        </h3>
        {upcoming_visits.length === 0 ? (
          <p className="text-sm text-slate-400">No upcoming visits scheduled.</p>
        ) : (
          <ul className="space-y-1">
            {upcoming_visits.map((visit) => (
              <li key={visit.id} className="text-sm text-slate-700 flex items-center gap-2">
                <span
                  className={`inline-block rounded-full px-2 py-0.5 text-xs ${
                    visit.status === "assigned"
                      ? "bg-emerald-50 text-emerald-700"
                      : "bg-amber-50 text-amber-700"
                  }`}
                >
                  {visit.status}
                </span>
                {visit.requested_date} — {visit.contract_line.customer_location.address}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="bg-white rounded-lg border border-slate-200 p-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-3">
          Contracts
        </h3>
        {contracts.length === 0 ? (
          <p className="text-sm text-slate-400">No contracts on file.</p>
        ) : (
          <ul className="space-y-2">
            {contracts.flatMap((contract) =>
              contract.lines.map((line) => (
                <li key={line.id} className="rounded-md border border-slate-200 p-3 text-sm">
                  <div className="font-medium text-slate-800">
                    {line.customer_location.address} (
                    {line.customer_location.region?.name ?? "no region"})
                  </div>
                  <div className="text-slate-600 mt-1">
                    {formatInterval(line.interval_unit, line.interval_count)},{" "}
                    {line.duration_minutes} min — {line.start_date}
                    {line.end_date ? ` to ${line.end_date}` : ""}
                  </div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {line.required_products.length === 0 ? (
                      <span className="text-slate-400">no products required</span>
                    ) : (
                      line.required_products.map((product) => (
                        <span
                          key={product.id}
                          className="inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700"
                        >
                          {product.number} {product.name}
                        </span>
                      ))
                    )}
                  </div>
                  <div className="mt-2 pt-2 border-t border-slate-100">
                    <BookAdHocVisit line={line} onBooked={reload} />
                  </div>
                </li>
              ))
            )}
          </ul>
        )}
      </section>

      <section className="bg-slate-50 rounded-lg border border-dashed border-slate-300 p-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-2">
          Offers
        </h3>
        <p className="text-sm text-slate-400">No offers yet — check back here later.</p>
      </section>

      <ExtraServices customerId={customerId} locations={customer_locations} />
    </div>
  );
}

interface ExtraServicesProps {
  customerId: number;
  locations: CustomerDashboardData["customer_locations"];
}

function ExtraServices({ customerId, locations }: ExtraServicesProps) {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [productId, setProductId] = useState<number | "">("");
  const [locationId, setLocationId] = useState<number | "">("");
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    listProducts()
      .then(setProducts)
      .catch((err) => setLoadError(err instanceof Error ? err.message : "Failed to load data"))
      .finally(() => setLoading(false));
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (productId === "" || locationId === "") return;
    setSubmitting(true);
    setSubmitError(null);
    setSubmitted(false);
    try {
      await createServiceRequest({
        customer_id: customerId,
        customer_location_id: locationId,
        product_id: productId,
        note: note || null,
      });
      setSubmitted(true);
      setProductId("");
      setLocationId("");
      setNote("");
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Failed to submit request");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="bg-white rounded-lg border border-slate-200 p-4">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-3">
        Request an Extra Service
      </h3>

      {loading ? (
        <p className="text-sm text-slate-400">Loading…</p>
      ) : loadError ? (
        <p className="text-sm text-red-600">{loadError}</p>
      ) : products.length === 0 ? (
        <p className="text-sm text-slate-400">No extra services are currently available.</p>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-2">
          <DetailField label="Service">
            <select
              value={productId}
              onChange={(event) =>
                setProductId(event.target.value === "" ? "" : Number(event.target.value))
              }
              required
              className="w-full text-sm border border-slate-300 rounded-md px-2 py-1"
            >
              <option value="">Select a service…</option>
              {products.map((product) => (
                <option key={product.id} value={product.id}>
                  {product.number} {product.name}
                </option>
              ))}
            </select>
          </DetailField>
          <DetailField label="Location">
            <select
              value={locationId}
              onChange={(event) =>
                setLocationId(event.target.value === "" ? "" : Number(event.target.value))
              }
              required
              className="w-full text-sm border border-slate-300 rounded-md px-2 py-1"
            >
              <option value="">Select a location…</option>
              {locations.map((location) => (
                <option key={location.id} value={location.id}>
                  {location.address}
                </option>
              ))}
            </select>
          </DetailField>
          <DetailField label="Note (optional)">
            <textarea
              value={note}
              onChange={(event) => setNote(event.target.value)}
              rows={2}
              className="w-full text-sm border border-slate-300 rounded-md px-2 py-1"
            />
          </DetailField>
          {submitError && <p className="text-sm text-red-600">{submitError}</p>}
          {submitted && <p className="text-sm text-emerald-700">Request submitted.</p>}
          <button
            type="submit"
            disabled={submitting}
            className="text-sm px-3 py-1.5 rounded-md bg-slate-900 text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {submitting ? "Submitting…" : "Submit request"}
          </button>
        </form>
      )}
    </section>
  );
}
