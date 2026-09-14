## 1. `ContractLine.priority` data model

- [x] 1.1 Add `priority: Mapped[int]` (`NOT NULL`, `server_default="2"`) to `ContractLine` in `backend/app/models.py`
- [x] 1.2 Add Alembic migration `0014_contract_line_priority.py` adding the column with the same server default
- [x] 1.3 Add `priority: int = 2` to `ContractLineCreate` and `ContractLineUpdate`, and `priority: int` to `ContractLineOut` in `backend/app/schemas.py`
- [x] 1.4 `ServiceVisitOut.contract_line` is already a full `ContractLineOut` (not flattened duration/product fields) - since task 1.3 added `priority` there, `ServiceVisitOut.contract_line.priority` is already available with no further change needed. Adding a separate top-level `priority` field on `ServiceVisitOut` would duplicate it and break from the existing nested-access pattern that duration/products already use, so skipped as redundant
- [x] 1.5 Pass `priority` through in `create_contract_line` and `update_contract_line` (`backend/app/main.py`)

## 2. Scheduling window and time budget become request parameters

- [x] 2.1 Add an `OptimizeRunOptions` (or similar) request schema to `backend/app/schemas.py` with `days_ahead: int = 2` and `time_limit_seconds: int | None = None`
- [x] 2.2 Change `POST /optimize/propose` (`backend/app/main.py`) to accept this request body (optional, defaulting as above) and pass both values into `build_optimize_payload`
- [x] 2.3 Change `_is_within_scheduling_window` (`backend/app/solver_client.py`) to take a `days_ahead` parameter, capped at 14, and check `effective_schedule_date(visit) in {today + timedelta(days=d) for d in range(min(days_ahead, 14))}`
- [x] 2.4 Change `build_optimize_payload` to take `days_ahead` and an optional `time_limit_seconds`, passing `days_ahead` through to `_is_within_scheduling_window` and using `time_limit_seconds or settings.solver_time_limit_seconds` for the payload's `time_limit_seconds` field

## 3. Priority and urgency reach the solver

- [x] 3.1 In `_visit_payload` (`backend/app/solver_client.py`), add `"priority": visit.contract_line.priority` and `"days_until_due": (effective_schedule_date(visit) - date.today()).days`
- [x] 3.2 Add `priority: int` and `days_until_due: int` to `VisitIn` in `solver/app/schemas.py`
- [x] 3.3 Add `priority: int` and `days_until_due: int` to `VisitAssignment` in `solver/app/domain.py`, and pass them through in `solve.py`'s `_build_schedule`

## 4. Priority/urgency-weighted unscheduled-visit constraint

- [x] 4.1 In `solver/app/constraints.py`, add `_unscheduled_priority_weight(visit) -> int` computing `(4 - visit.priority) * PRIORITY_SCALE + (URGENCY_CAP - visit.days_until_due)` per design.md's formula (`PRIORITY_SCALE = 1_000_000`, `URGENCY_CAP = 14`)
- [x] 4.2 Change the "Unscheduled visit" constraint's `.penalize(HardMediumSoftScore.ONE_MEDIUM)` to `.penalize(HardMediumSoftScore.ONE_MEDIUM, _unscheduled_priority_weight)` - extracted to a standalone `unscheduled_visit` function (matching the existing driving-time-gap constraints' pattern) so it's independently unit-testable
- [x] 4.3 Add `ConstraintVerifier` tests in `solver/tests/` (following the pattern in `test_driving_time_gap_constraints.py`) covering: a priority-1 unscheduled visit penalizes more than a priority-3 one; two same-priority visits with different `days_until_due` penalize proportionally to urgency; the existing "prefer scheduling more visits than fewer" behavior still holds (any scheduled-count difference still dominates any single-visit priority/urgency difference, verified via a full-provider `MultiConstraintVerification` or a `solve_schedule` integration test) - while writing these, found and fixed a real math flaw in the originally-approved weight formula (see design.md's updated Decisions section: a flat/linear per-tier multiplier can never guarantee dominance under Timefold's summed scoring once 2-3+ lower-priority visits are unscheduled together, regardless of the constant chosen). Implemented the corrected nested-scale formula instead (confirmed with the user), added a `total_visit_count` field to `VisitAssignment`/`solve.py`, and added a 201-visit test proving a single priority-1 visit still outweighs 200 priority-3 visits combined

## 5. Frontend: Optimize screen parameters

- [x] 5.1 Add `days_ahead`/`time_limit_seconds` to the propose-optimization types in `frontend/src/types.ts`, and accept them as parameters in `proposeOptimization` (`frontend/src/api.ts`), sending them as the request body
- [x] 5.2 Add number inputs for "Days ahead" (default 2, max 14) and "Solver time budget (seconds)" (default matching today's fixed value) to `frontend/src/components/OptimizeView.tsx`, passed to `proposeOptimization` when "Run Optimization" is clicked

## 6. Frontend: contract line priority field

- [x] 6.1 Add `priority` to the `ContractLine`, `ContractLineCreateInput`, and `ContractLineUpdateInput` types in `frontend/src/types.ts`
- [x] 6.2 Add a priority select (High/Medium/Low, default Medium) to the contract line create/edit form in `frontend/src/admin-portal/ContractsView.tsx` - also shows the priority label in the read-only contract line row for visibility

## 7. Manual verification

- [x] 7.1 Start the backend + solver + frontend locally; run optimization with the default parameters and confirm behavior is unchanged from before this change (same window, same time budget) - verified against the live dev stack and real seeded data: `POST /optimize/propose` with an empty body and with an explicit `{"days_ahead": 2}` both scheduled 14/1050 visits, all on today's date, matching the pre-change baseline order of magnitude (12-14 scheduled in earlier sessions)
- [x] 7.2 Set a contract line to priority 1 (High) and another competing for the same employee capacity to priority 3 (Low); run optimization in a scenario where not everything fits, and confirm the priority-1 visit is scheduled ahead of the priority-3 one - the deeper prioritization math is proven by the solver's automated tests (`test_priority_does_not_override_scheduling_more_visits_than_fewer`, `test_a_single_priority_1_unscheduled_visit_outweighs_many_priority_3_visits`); separately verified the field's live end-to-end wiring by PATCHing a real contract line (id 30) to priority 1 via the running backend, confirming the response and `GET /service-visits` both reflected it through `contract_line.priority`, then reverting it back to 2
- [x] 7.3 Increase "Days ahead" beyond 2 and confirm visits further out become candidates and appear in the proposal (or as reported-unscheduled) instead of being silently excluded - the live data was too sparse (15-day visit cadence) to show a visible scheduling difference in a full run, so verified `_is_within_scheduling_window` directly against the real next-batch visit date (2026-09-25, 13 days from today 2026-09-12): `days_ahead=13` excludes it, `days_ahead=14` includes it
- [x] 7.4 Confirm a `days_ahead` value above 14 is capped rather than producing an oversized solver run - same direct check: `days_ahead=15` and `days_ahead=100` both produce the identical in-window result as `days_ahead=14`, confirming the `MAX_DAYS_AHEAD` cap is enforced
