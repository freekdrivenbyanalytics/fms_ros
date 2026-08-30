## Why

A `Contract` today is tied directly to one customer location, mixing two different concerns: "which customer do we have an agreement with" and "which of that customer's locations gets recurring service, on what schedule, needing what skills." A customer with several locations (now a real, common case since locations sync from Tripletex) can't have one contract covering multiple sites with different schedules per site. Splitting `Contract` (customer-level) from a new `ContractLine` (location-level, carrying the schedule/skill details) fixes that, and — since this data is fully local (not Tripletex-sourced) — this is also the first entity the Customer Portal needs real create/update/delete capability for, not just read-only browsing.

## What Changes

- **BREAKING**: `Contract` is split into `Contract` (id, the customer it belongs to, soft-delete) and `ContractLine` (id, the contract it belongs to, the customer location it applies to, start date, end date, interval in days, visit duration, required skills, soft-delete). Every field a contract carries today except its customer/customer-location link moves to `ContractLine`.
- `ServiceVisit` is generated from a `ContractLine`, not a `Contract` directly — its duration and required skills are now read through the contract line. This ripples through everywhere a service visit's contract data is read: the assignments/optimize endpoints, the solver payload builder, and the frontend's Unassigned Visits, Assigned Visits, and Day Planning views all read through `contract_line` instead of `contract`.
- The Customer Portal gains create, update, and soft-delete for both `Contract` and `ContractLine` — the first write capability anywhere in the Customer Portal, which has been read-only until now. Creating a contract picks a customer; creating a line under it picks one of that customer's locations plus its schedule/skill details. Soft-deleting a `Contract` cascades to soft-delete all of its `ContractLine`s; a `ContractLine` can also be soft-deleted on its own without affecting its parent contract. Every other entity in the portal (Employees, Customers, Customer Locations, Skills, Regions) stays read-only.
- Out of scope: nothing automatically generates new `ServiceVisit` rows from a `ContractLine`'s schedule. Visit creation stays exactly as manual/seed-driven as it is today — a `ContractLine`'s start/end date, interval, and duration are data for this change, not a running scheduler. (Confirmed with the user.)
- Out of scope: soft-deleting a `Contract` or `ContractLine` does not hide, cancel, or otherwise affect any `ServiceVisit`s already generated from it — consistent with how deleting a `Customer` or `CustomerLocation` today never cascades to hide the contracts/visits under it.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `contracts`: "Contract data model" is replaced by a slimmer version (id, customer, soft-delete); adds "Contract Line data model", "A contract can have multiple lines", "A contract line can require multiple skills", "Create, update, and soft-delete a contract", "Create, update, and soft-delete a contract line", and "Soft-deleting a contract cascades to its lines".
- `service-visits`: "Service visit data model" and "List service visits by assignment status" are updated to read a visit's duration/skills/location through its contract line rather than a contract directly.
- `customer-portal`: "Customer Portal is read-only" is narrowed to exclude Contracts and Contract Lines; "Detail view shows an item and its relationships" (Contract detail) and "Skill detail" scenarios are updated for the new shape; adds requirements for creating, updating, and soft-deleting a contract and a contract line from the portal.

## Impact

- **Backend**: `backend/app/models.py` — `Contract` slims down to `id`/`customer_id`/`delete_flag`; new `ContractLine` model carries what `Contract` used to (customer_location_id, start_date, end_date, interval_days, duration_minutes, delete_flag) plus its own `required_skills` M2M (`contract_line_skills`, replacing `contract_skills`); `ServiceVisit.contract_id` becomes `ServiceVisit.contract_line_id`. A migration truncates and rebuilds this part of the schema, the same disruptive shape as the Tripletex customer/location migrations, since this is a structural split, not an additive change. New endpoints: `POST /contracts`, `PATCH /contracts/{id}`, `DELETE /contracts/{id}` (soft), `POST /contracts/{id}/lines`, `PATCH /contract-lines/{id}`, `DELETE /contract-lines/{id}` (soft). `backend/app/solver_client.py` and `backend/app/main.py`'s assignment/optimize logic read `visit.contract_line.*` instead of `visit.contract.*`.
- **Frontend**: `frontend/src/types.ts`'s `ServiceVisit.contract` becomes `contract_line: ContractLine`; `UnassignedVisitList.tsx`, `AssignedVisitList.tsx`, `DayPlanningView.tsx`, and `OptimizeView.tsx` updated to read through it. Customer Portal's `ContractsView.tsx` gains create/update/soft-delete forms for both contracts and contract lines; `SkillsView.tsx`'s "Contracts that require it" becomes "Contract Lines that require it".
- **Seed data**: `backend/app/seed.py`'s fixture contracts are rebuilt as one `Contract` per customer with one `ContractLine` per location, instead of one `Contract` per location.
