## 1. Backend: window filter

- [x] 1.1 In `build_optimize_payload` (`backend/app/solver_client.py`), filter `ready_visits` to those with `effective_schedule_date(v)` in `{today, tomorrow}`; add the rest to `excluded_visit_ids` alongside the existing ungeocoded/regionless exclusions.
- [x] 1.2 Confirm `candidate_dates` (used to fetch `EmployeeDaySchedule`s) is derived from the now-filtered visit set, so no unnecessary schedule lookups happen for dates outside the window.

## 2. Verification

- [x] 2.1 Create service visits requested today, tomorrow, and 5 days out; request a proposed schedule and confirm only the today/tomorrow visits appear in `scheduled` or contribute a feasible proposal, and the 5-days-out visit appears in `unscheduled_visit_ids`.
- [x] 2.2 Confirm a visit whose requested date has already passed (rescheduled to today via `effective_schedule_date`) is still considered.
- [x] 2.3 Confirm existing pinned/started assignments outside the window are unaffected (still returned by `/assignments`, not touched by proposal generation).
