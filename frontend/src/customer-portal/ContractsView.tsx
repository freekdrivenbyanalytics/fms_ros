import { useState } from "react";
import type { Contract, ServiceVisit } from "../types";
import { BackButton, DetailField } from "../shared/DetailField";
import { ListTable } from "../shared/ListTable";

interface Props {
  contracts: Contract[];
  serviceVisits: ServiceVisit[];
}

export function ContractsView({ contracts, serviceVisits }: Props) {
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
