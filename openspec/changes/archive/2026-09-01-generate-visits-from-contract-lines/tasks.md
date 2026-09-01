## 1. Backend: occurrence-date generation

- [x] 1.1 Create `backend/app/visit_generation.py` with `generate_occurrence_dates(start_date: date, interval_days: int, end_date: date | None) -> list[date]`: steps from `start_date` by `interval_days` while `<= end_date` (or `<= start_date + timedelta(days=365)` (one year) when `end_date` is `None`); treats `interval_days <= 0` as a single occurrence at `start_date` (defensive guard, no infinite loop).
- [x] 1.2 Unit-verify `generate_occurrence_dates` directly (a quick script, not a new test framework): bounded end_date case, open-ended one-year-horizon case, `interval_days <= 0` case, and an `end_date` equal to `start_date` (exactly one occurrence).

## 2. Backend: wire generation into contract line creation

- [x] 2.1 In `create_contract_line` (`backend/app/main.py`): after building and flushing the `ContractLine` (so it has an id), call `generate_occurrence_dates` and create one `ServiceVisit` per returned date, linked via `contract_line_id`, before the final commit.
- [x] 2.2 Confirm `update_contract_line` is unchanged — it must not call the generation function or otherwise touch `ServiceVisit` rows.
- [x] 2.3 Verify via API: creating a contract line with an `end_date` generates exactly the expected visit dates; creating one with no `end_date` generates visits up to 1 year out; updating an existing contract line's dates/interval afterward creates no new visits and leaves existing ones untouched.

## 3. Backend: date-range filtering on the list endpoint

- [x] 3.1 Add optional `start_date: date | None` and `end_date: date | None` query parameters to `GET /service-visits` (`list_service_visits`); filter `ServiceVisit.requested_date` against whichever bounds are provided, applying no filter for an omitted bound.
- [x] 3.2 Verify via API: no params returns everything (today's behavior, unchanged); `end_date` alone returns only visits on/before it; `start_date` alone returns only visits on/after it; both together return the inclusive range.

## 4. Frontend: types and API client

- [x] 4.1 Update `listServiceVisits` in `frontend/src/api.ts` to accept optional `{ startDate?: string; endDate?: string }` and forward them as query params.

## 5. Frontend: Customer Portal shows a contract line's generated visits

- [x] 5.1 Fetch `listServiceVisits()` in `frontend/src/customer-portal/CustomerPortalApp.tsx` (or pass down however `ContractsView` best receives it) and thread it through to `ContractLineRow` in `frontend/src/customer-portal/ContractsView.tsx`.
- [x] 5.2 In `ContractLineRow`, show the service visits generated from that line (requested date + status), with an empty-state message when there are none.

## 6. Frontend: Manual Assignment date-range control

- [x] 6.1 In `frontend/src/App.tsx`'s `assign` view, add date-range state: an `endDate` defaulting to `today + 7 days`, plus "This Week" (end of the current ISO calendar week) and "4 Weeks" (`today + 28 days`) preset controls that set `endDate`; refetch `listServiceVisits({ endDate })` (no `startDate`, so overdue visits are never excluded) when it changes.
- [x] 6.2 Add the date-range control (manual date picker + the two presets) to the assign view's UI, visible above the three lists.
- [x] 6.3 Confirm both `UnassignedVisitList` and `AssignedVisitList` reflect the same filtered `visits` data (the existing `unassignedVisits`/`assignedVisits` derivation from the shared `visits` state already gives this "whole board" sharing for free once the fetch itself is date-filtered).

## 7. End-to-end verification

- [x] 7.1 Run `tsc -b` and confirm the frontend type-checks cleanly.
- [x] 7.2 Launch frontend + backend and manually confirm in the browser: creating a contract line in the Customer Portal produces visits that show up both on the contract line's own row and on the Manual Assignment board (if within the default range); the date-range control's default, "This Week", and "4 Weeks" presets all correctly include overdue visits and adjust the upper bound; updating a contract line does not create or remove any visits.
- [x] 7.3 Confirm `openspec validate --strict` passes for the change before archiving.
