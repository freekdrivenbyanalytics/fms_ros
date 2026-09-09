## 1. Backend: free-slot search

- [x] 1.1 Add a module (e.g. `backend/app/ad_hoc_visits.py`) with a `find_free_slots(db, contract_line) -> list[FreeSlot]` function: for each of the next 14 dates, for each employee scoped to the contract line's customer location's region and holding all its required skills, resolve the working-hours window via `resolve_employee_schedule`, gather that employee's existing assignments for the date, and yield every gap of at least `duration_minutes`.
- [x] 1.2 Add `GET /contract-lines/{line_id}/free-slots` returning the found slots (employee id/name, date, start/end minutes). Implemented as full `start`/`end` datetimes rather than separate date + minutes fields, matching this API layer's existing convention (`AssignmentCreate.planned_start: datetime`) rather than the solver's internal minutes-since-midnight convention — same information, no spec impact.
- [x] 1.3 Add a response schema for a free slot in `backend/app/schemas.py`.

## 2. Backend: booking

- [x] 2.1 Add `POST /contract-lines/{line_id}/ad-hoc-visits` accepting `{employee_id, start}`: create the `ServiceVisit(contract_line_id, requested_date=start.date())`, then reuse `create_assignment`'s logic (extracted to a shared `_assign_visit` helper) to create the `Assignment` and set `status = ASSIGNED`, in one transaction.
- [x] 2.2 Add a request/response schema pair for the booking call (`AdHocVisitCreate` request; response reuses `AssignmentOut`, which already matches what's returned).

## 3. Frontend: Customer Portal Contracts view

- [x] 3.1 Add `getFreeSlots(lineId)` and `bookAdHocVisit(lineId, payload)` to `frontend/src/api.ts`.
- [x] 3.2 Add a "Book ad-hoc visit" action to each contract line row in `frontend/src/customer-portal/ContractsView.tsx` that fetches and shows free slots, lets the user pick one, and confirms the booking.
- [x] 3.3 Show "No free slots available" when the list is empty; show the booked visit's date/time/employee on success; refresh the view's data (`onChanged`) after booking. `ContractsView` gained an `onChanged` prop (it had none before, being read-only); `CustomerPortalApp.tsx` wires it to a new `reloadContractsAndVisits` reload function.

## 4. Verification

- [x] 4.1 Confirm a contract line with a qualifying employee and open working hours returns at least one free slot spanning the visit's duration.
- [x] 4.2 Confirm an employee missing a required skill, or scoped to a different region, never appears in the results.
- [x] 4.3 Confirm booking a slot creates a service visit with status `assigned` and the matching assignment, retrievable via the existing `/service-visits` and `/assignments` endpoints.
- [x] 4.4 Confirm the booked visit shows up correctly in the Admin Portal's Contracts view and is a normal (re-optimizable, if unpinned) candidate for a future proposed schedule.
