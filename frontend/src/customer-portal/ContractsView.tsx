import { useState } from "react";
import { bookAdHocVisit, getFreeSlots } from "../api";
import type { Contract, ContractLine, FreeSlot, ServiceVisit } from "../types";
import { BackButton, DetailField } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";

interface Props {
  contracts: Contract[];
  serviceVisits: ServiceVisit[];
  onChanged: () => void | Promise<void>;
}

export function ContractsView({ contracts, serviceVisits, onChanged }: Props) {
  const [selected, setSelected] = useState<Contract | null>(null);

  if (selected) {
    return (
      <div>
        <BackButton label="Contracts" onClick={() => setSelected(null)} />
        <h2 className="text-xl font-semibold text-slate-900 mb-4">
          Contract #{selected.id} — {selected.customer.name}
        </h2>

        <DetailField label="Contract Lines">
          {selected.lines.length === 0 ? (
            "—"
          ) : (
            <ul className="space-y-2">
              {selected.lines.map((line) => {
                const visits = serviceVisits.filter(
                  (visit) => visit.contract_line.id === line.id
                );
                return (
                  <li key={line.id} className="rounded-md border border-slate-200 p-3 text-sm">
                    <div className="font-medium text-slate-800">
                      {line.customer_location.address} (
                      {line.customer_location.region?.name ?? "no region"})
                    </div>
                    <div className="text-slate-600 mt-1">
                      Every {line.interval_days} days, {line.duration_minutes} min —{" "}
                      {line.start_date}
                      {line.end_date ? ` to ${line.end_date}` : ""}
                    </div>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {line.required_skills.length === 0 ? (
                        <span className="text-slate-400">no skills required</span>
                      ) : (
                        line.required_skills.map((skill) => (
                          <span
                            key={skill.id}
                            className="inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700"
                          >
                            {skill.name}
                          </span>
                        ))
                      )}
                    </div>
                    <div className="mt-2 pt-2 border-t border-slate-100">
                      <div className="text-xs uppercase tracking-wide text-slate-400 mb-1">
                        Generated Visits
                      </div>
                      {visits.length === 0 ? (
                        <p className="text-xs text-slate-400">No visits generated yet.</p>
                      ) : (
                        <ul className="flex flex-wrap gap-1">
                          {visits.map((visit) => (
                            <li
                              key={visit.id}
                              className={`inline-block rounded-full px-2 py-0.5 text-xs ${
                                visit.status === "assigned"
                                  ? "bg-emerald-50 text-emerald-700"
                                  : "bg-amber-50 text-amber-700"
                              }`}
                            >
                              {visit.requested_date} — {visit.status}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                    <div className="mt-2 pt-2 border-t border-slate-100">
                      <BookAdHocVisit line={line} onBooked={onChanged} />
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </DetailField>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-slate-900 mb-4">Contracts</h2>
      <ListTable
        items={contracts}
        getKey={(contract) => contract.id}
        onSelect={setSelected}
        emptyMessage="No contracts."
        columns={[
          { header: "Customer", render: (contract) => contract.customer.name },
          { header: "Lines", render: (contract) => String(contract.lines.length) },
        ]}
      />
    </div>
  );
}

interface BookAdHocVisitProps {
  line: ContractLine;
  onBooked: () => void | Promise<void>;
}

function BookAdHocVisit({ line, onBooked }: BookAdHocVisitProps) {
  const [open, setOpen] = useState(false);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [slots, setSlots] = useState<FreeSlot[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [booking, setBooking] = useState(false);
  const [booked, setBooked] = useState<FreeSlot | null>(null);

  async function handleOpen() {
    setOpen(true);
    setBooked(null);
    setError(null);
    setLoadingSlots(true);
    try {
      setSlots(await getFreeSlots(line.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load free slots");
    } finally {
      setLoadingSlots(false);
    }
  }

  async function handleBook(slot: FreeSlot) {
    setBooking(true);
    setError(null);
    try {
      await bookAdHocVisit(line.id, { employee_id: slot.employee_id, start: slot.start });
      setBooked(slot);
      setSlots([]);
      await onBooked();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to book slot");
    } finally {
      setBooking(false);
    }
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={handleOpen}
        className="text-xs px-2 py-1 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-50"
      >
        Book ad-hoc visit
      </button>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <div className="text-xs uppercase tracking-wide text-slate-400">Book Ad-Hoc Visit</div>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="text-xs text-slate-400 hover:text-slate-600"
        >
          Close
        </button>
      </div>

      {booked && (
        <p className="text-xs text-emerald-700 mb-2">
          Booked {new Date(booked.start).toLocaleString()} with {booked.employee_name}.
        </p>
      )}
      {error && <p className="text-xs text-red-600 mb-2">{error}</p>}

      {loadingSlots ? (
        <p className="text-xs text-slate-400">Loading free slots…</p>
      ) : slots.length === 0 && !booked ? (
        <p className="text-xs text-slate-400">No free slots available.</p>
      ) : (
        <ul className="flex flex-wrap gap-1">
          {slots.map((slot, index) => (
            <li key={`${slot.employee_id}-${slot.start}-${index}`}>
              <button
                type="button"
                onClick={() => handleBook(slot)}
                disabled={booking}
                className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 hover:bg-slate-200 disabled:opacity-50"
              >
                {new Date(slot.start).toLocaleString()} — {slot.employee_name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
