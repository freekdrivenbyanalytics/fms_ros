import { useState } from "react";
import { acknowledgeServiceRequest } from "../api";
import type { ServiceRequest } from "../types";

interface Props {
  serviceRequests: ServiceRequest[];
  onChanged: () => void | Promise<void>;
}

export function ServiceRequestsView({ serviceRequests, onChanged }: Props) {
  const [acknowledgingId, setAcknowledgingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleAcknowledge(id: number) {
    setAcknowledgingId(id);
    setError(null);
    try {
      await acknowledgeServiceRequest(id);
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to acknowledge request");
    } finally {
      setAcknowledgingId(null);
    }
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-slate-900 mb-4">Service Requests</h2>
      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      {serviceRequests.length === 0 ? (
        <p className="text-sm text-slate-500">No pending service requests.</p>
      ) : (
        <ul className="space-y-2">
          {serviceRequests.map((request) => (
            <li
              key={request.id}
              className="rounded-md border border-slate-200 bg-white p-3 text-sm flex items-start justify-between gap-4"
            >
              <div>
                <div className="font-medium text-slate-800">
                  {request.customer.name} — {request.product.number} {request.product.name}
                </div>
                <div className="text-slate-600 mt-1">{request.customer_location.address}</div>
                {request.note && (
                  <div className="text-slate-500 mt-1 italic">"{request.note}"</div>
                )}
                <div className="text-xs text-slate-400 mt-1">
                  Requested {new Date(request.created_at).toLocaleString()}
                </div>
              </div>
              <button
                type="button"
                onClick={() => handleAcknowledge(request.id)}
                disabled={acknowledgingId === request.id}
                className="shrink-0 text-sm px-3 py-1.5 rounded-md bg-slate-900 text-white hover:bg-slate-700 disabled:opacity-50"
              >
                {acknowledgingId === request.id ? "Acknowledging…" : "Acknowledge"}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
