## 1. Backend: lower the horizon and support extension

- [x] 1.1 Change `OPEN_ENDED_HORIZON_DAYS` from 365 to 90 in `backend/app/visit_generation.py`.
- [x] 1.2 Add a function (e.g. `extend_occurrence_dates(furthest_existing: date, interval_days: int, new_horizon: date) -> list[date]`) that returns only the occurrence dates strictly after `furthest_existing` up to `new_horizon`.
- [x] 1.3 Add `POST /contract-lines/extend-visits` in `backend/app/main.py`: for every non-deleted contract line with `end_date IS NULL`, find `MAX(requested_date)` among its existing service visits (or its `start_date` if it has none), compute the missing occurrences out to 90 days from today via 1.2, and insert the corresponding `ServiceVisit` rows. Return a summary (e.g. lines extended, visits created).
- [x] 1.4 Add a schema for the summary response (mirroring `DrivingTimeComputeSummary`'s shape).

## 2. Frontend: trigger and feedback

- [x] 2.1 Add `extendContractLineVisits()` to `frontend/src/api.ts`.
- [x] 2.2 Add an "Extend recurring visits" button to `ContractsView.tsx`, following the same in-progress/result/error pattern as `RegionsView.tsx`'s "Compute driving times" button.
- [x] 2.3 Refresh the contracts/service-visits data (`onChanged`) after a successful extension so newly generated visits and updated `visit_count`s appear.

## 3. Verification

- [x] 3.1 Create an open-ended contract line and confirm it generates visits only 90 days out, not 365.
- [x] 3.2 Trigger extend-visits immediately after creation and confirm it's a no-op (line is already at the horizon).
- [x] 3.3 Manually back-date a line's furthest visit (or simulate time passing) and confirm extend-visits fills the gap without duplicating existing visits.
- [x] 3.4 Confirm a bounded (`end_date` set) contract line is untouched by extend-visits.
