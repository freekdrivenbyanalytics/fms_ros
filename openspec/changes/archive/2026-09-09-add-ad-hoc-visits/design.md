## Context

`ServiceVisit.contract_line_id` is a required (non-null) foreign key; duration and required skills are always read through the contract line (`backend/app/models.py`). There is no existing endpoint to create a service visit directly — visits only come from `generate_occurrence_dates` at contract-line creation (`backend/app/main.py::create_contract_line`) or, after this change's sibling `cap-contract-line-visit-horizon`, from the extend-visits operation. `POST /assignments` (`create_assignment`) already does the minimal work of assigning an employee to a visit at a given start time — it checks the visit and employee exist and the visit isn't already assigned, computes `planned_end` from the contract line's `duration_minutes`, and does *not* itself re-check skills, region, working hours, or overlap; that enforcement today lives only in the solver's proposal logic and (per `Applying a proposed schedule`) in trusting a previously-generated proposal. See proposal.md - Why for the product motivation.

## Goals / Non-Goals

**Goals:**
- Reuse the existing `ServiceVisit`/`ContractLine`/`Assignment` model as-is — an ad-hoc visit is exactly like any other visit, just created and assigned at booking time instead of generated-then-later-assigned.
- Reuse `resolve_employee_schedule` and the same skill/region conditions the solver payload builder already applies, so "free slot" means the same thing "the optimizer would consider this feasible" means.
- Keep the free-slot search self-contained (no new dependency, no change to `solver/`).

**Non-Goals:**
- Travel-time-aware slot filtering. A returned slot is feasible on working hours, skills, region, and non-overlap alone; it is not checked against the region driving-time matrix for whether the employee can plausibly reach it from a neighboring visit. Per the user's explicit "keep this as simple as possible for now," this is deferred — flagged in the UI copy or follow-up, not solved here.
- Re-validating a slot's feasibility server-side at booking time beyond what `POST /assignments` already does (visit exists, employee exists, visit not already assigned). A slot could theoretically become stale between being listed and being booked (another booking fills the same gap); this mirrors the same race `POST /assignments` already tolerates for manual assignment today, so it is not a new gap this feature introduces, and is not worth new locking/re-validation machinery for a staff-operated, low-volume, keep-it-simple first version.
- Customer authentication. The action is reachable by anyone who can open the Customer Portal, exactly like every other Customer Portal view today.
- The future "offers" concept the user mentioned — noted as context for why this lives in the Customer Portal, not built here.

## Decisions

- **14-day search horizon.** Long enough to be useful for "pick a time this week or next," short enough to keep the search cheap and the returned slot list reviewable. Not made configurable — no stated need yet.
- **Free-slot search is a straight gap-finder, not a solver call.** For each of the next 14 dates, for each employee with the contract line's required skills and region scope, resolve that date's working-hours window (`resolve_employee_schedule`), gather the employee's existing assignments that date, and return every gap at least `duration_minutes` long as a slot. This is deliberately simpler than invoking Timefold: it's placing one visit into existing open time, not jointly optimizing many, so a direct gap scan is both correct and far cheaper.
- **Booking calls the same assignment path as manual assignment**, parameterized with a freshly created service visit instead of an existing one — new logic is only "create the visit," not "assign it." Keeps the one behavioral surface (what makes an assignment valid) in one place.
- **No new field marks a visit as "ad-hoc."** Per the spec's "otherwise an ordinary visit" requirement — nothing downstream (solver, Admin Portal, reporting) needs to distinguish how a visit came to exist. If that need arises later (e.g., for the "offers" feature), it can be added then.

## Risks / Trade-offs

- [A slot could be geographically impractical for the employee despite being time-feasible] → Accepted for now per Non-Goals; worth a driving-time-aware follow-up once this ships and is used.
- [Anyone reaching the Customer Portal can book a visit for any customer, with no identity check] → Matches the Customer Portal's current no-auth stance everywhere else; will be closed off once customer authentication is added, which the user has explicitly deferred.
