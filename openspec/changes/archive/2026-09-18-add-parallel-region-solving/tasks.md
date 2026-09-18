## 1. Live verification (before building on top of either assumption)

- [x] 1.1 Start the solver service with `uvicorn app.main:app --workers 4` locally; confirm each worker process independently completes its own JVM warm-up (a distinct "Solver warm-up complete" log line per worker, or the pre-existing warm-up failure noted in `add-skills-and-service-order-types`'s tasks.md — either way, confirm N independent worker processes actually start and each can serve a solve)
- [x] 1.2 Fire two genuinely concurrent `POST /optimize` requests (two different small, valid payloads, sent at the same time) at the multi-worker solver service; confirm both return correct, independent results and neither blocks on the other for the full duration of both combined

## 2. Backend — region grouping

- [x] 2.1 Add a pure function (e.g. `group_regions_by_shared_employees(employees, region_ids) -> list[set[int]]`) to `backend/app/solver_client.py` (or a new `backend/app/solver_partitioning.py`): builds the region-adjacency graph (an edge between two regions whenever one employee is scoped to both) restricted to the given region ids, and returns its connected components
- [x] 2.2 Unit-test this function directly (no DB, no HTTP): disjoint regions produce separate groups; a multi-region employee merges their regions into one group; a chain of shared employees transitively merges three or more regions into one group

## 3. Backend — parallel payload building and dispatch

- [x] 3.1 Add a function building one group's solver payload as a real subset of the full run's employees/visits/driving-times/existing-assignments (only rows belonging to that group's regions/employees), reusing `build_optimize_payload`'s existing per-item payload builders (`_employee_payload`, `_visit_payload`, etc.) rather than duplicating them
- [x] 3.2 Add `execution_mode: Literal["single", "parallel"] = "single"` to `OptimizeRunOptions` (`backend/app/schemas.py`)
- [x] 3.3 In `solver_client.py` (or `main.py`'s propose-optimization endpoint), when `execution_mode == "parallel"`: compute the run's regions-with-ready-visits, group them via task 2.1, and if there are 2 or more groups, build one payload per group and dispatch them concurrently via a `ThreadPoolExecutor` wrapping the existing `httpx.post` call in `request_proposal`; merge every group's `scheduled`/`unscheduled_visit_ids` into one `OptimizationProposal`
- [x] 3.4 When `execution_mode == "single"`, or `parallel` mode's grouping yields exactly one group, behavior is unchanged — a single call exactly as today (do not introduce a thread pool or any new code path for this case)
- [x] 3.5 Ensure a failure in any one group's HTTP call surfaces as a clear error for the whole run (matching today's single-call error handling), rather than silently returning a partial proposal

## 4. Solver deployment

- [x] 4.1 Document the `--workers N` startup flag for the solver service (README or equivalent), with a sensible default suggestion (e.g. 4) and a note that each worker boots its own JVM and consumes memory accordingly

## 5. Frontend

- [x] 5.1 Add `execution_mode: "single" | "parallel"` to `OptimizeRunOptions` in `frontend/src/types.ts`
- [x] 5.2 Add an "Execution mode" selector (Standard / Parallel by region) to `frontend/src/components/OptimizeView.tsx`, alongside the existing days-ahead/time-limit controls, defaulting to Standard
- [x] 5.3 Pass the selected mode through `proposeOptimization` (`frontend/src/api.ts`) to the backend

## 6. Manual verification

- [x] 6.1 Run a proposal in `single` mode; confirm the result is unchanged from before this change (same scheduled/unscheduled visits for the same input, modulo the solver's own run-to-run variance)
- [x] 6.2 Run the same proposal in `parallel` mode against a dataset with genuinely employee-disjoint regions; confirm it returns a merged proposal and completes in less wall-clock time than `single` mode for the same input
- [x] 6.3 Run `parallel` mode against a dataset where every region shares at least one employee (fully connected); confirm it falls back to a single solve and returns the same result `single` mode would, rather than erroring
- [x] 6.4 Confirm no employee receives two conflicting proposed assignments when regions are split into groups (spot-check a multi-region employee's proposed visits land within one consistent group's results)
- [x] 6.5 Kill one solver worker process mid-run (simulating a crash) and confirm the run surfaces a clear error rather than hanging indefinitely or silently dropping that group's visits
