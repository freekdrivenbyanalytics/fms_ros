## Context

Investigated live before writing this: the installed `timefold==1.24.0b0` package's `SolverConfig.move_thread_count` (real multithreaded move evaluation) raises `RequiresEnterpriseError` at solve time unless a separate `timefold-solver-enterprise` package is installed (`is_enterprise_installed()` in `_timefold_java_interop.py` checks for it and isn't found in this venv). This is a compiled-in commercial licensing gate, not an open-source limitation with a source-level fix — "branching the open source repo and fixing this" was the original request's framing, but there is no bug to fix; forking the repo to bypass the check would mean circumventing Timefold's commercial license, which this design does not do.

The solver already runs as its own separate FastAPI microservice (`solver/app/main.py`, port 8100 by default via `settings.solver_base_url`), talked to over plain HTTP from the backend (`solver_client.py`'s `request_proposal`). `solve_schedule` (`solver/app/solve.py`) already builds a fresh `SolverConfig`/`Solver` per call — no shared global solver state between requests. `build_optimize_payload` (`backend/app/solver_client.py`) already assembles `employees`/`visits`/`existing_assignments`/`driving_times` from the database per run. `Employee` can be scoped to more than one `Region` (`employee_regions`, many-to-many); `DrivingTime` rows are already region-scoped (a `region_id` column).

## Goals / Non-Goals

**Goals:**
- Real wall-clock speedup for a run whose regions are mostly employee-disjoint, without touching Timefold's own solving code or requiring any paid license.
- Zero behavior change when `execution_mode` is left at its default (`single`).
- Provably never double-book an employee as a side effect of splitting a run into concurrent solves.

**Non-Goals:**
- Any change to Timefold's own constraint logic, domain classes, or `SolverConfig` — every concurrent solve is the exact same unmodified single-threaded solve that already runs today, just several of them at once.
- Squeezing out the theoretical maximum parallelism (e.g. splitting a single large connected region-group further) — if the regions in scope for a run all end up in one group, this design intentionally falls back to solving them together, not attempting a more aggressive (and much riskier) decomposition.
- Load-balancing or autoscaling the number of worker processes — a fixed, operator-configured worker count is enough for this change.

## Decisions

**Parallelism comes from running N genuinely separate OS processes (`uvicorn --workers N` for the solver service), not from Python `multiprocessing` inside the backend, and not from relying on concurrent threads sharing one embedded JVM.** Each uvicorn worker is its own OS process with its own Python interpreter and, critically, its own independently-started embedded JVM (JPype's JVM is a one-per-process resource, started via the existing `ensure_jvm_env()`/warm-up path in `solver/app/main.py`'s lifespan, which every worker process already runs independently today for a single-worker deployment). This sidesteps any question of whether Timefold/JPype safely supports multiple concurrent solves sharing one JVM from separate threads — a question this design does not need to answer, since concurrent requests here always land on separate processes with separate JVMs. Alternative considered: keep one solver worker process and have it handle concurrent requests on separate threads (Starlette already thread-pools sync endpoints) — rejected as the riskier option; it would work only if JPype's per-thread JVM attachment is fully safe for concurrent independent `Solver` instances, which is plausible but unverified, versus `--workers N` process isolation, which needs no such assumption.

**The backend fires concurrent HTTP requests to the (now multi-worker) solver service using a `ThreadPoolExecutor` around the existing synchronous `httpx.post` call in `request_proposal`, not `asyncio`.** The rest of the FastAPI backend is written synchronously throughout (no `async def` endpoints, no `httpx.AsyncClient` anywhere); introducing `asyncio` for just this one path would be a bigger, more invasive change than wrapping the existing blocking call in a thread pool, which achieves the same concurrent-dispatch goal with a two-line change at the call site.

**Region grouping is connected components over an undirected graph: regions are nodes, an edge connects two regions whenever at least one employee is scoped to both.** Built once per run from the same `employees` list `build_optimize_payload` already loads (each `Employee.regions`), restricted to regions that actually have a ready-to-schedule visit this run (a region with no candidate visits doesn't need its own group). This is the only grouping rule that can *prove* no employee crosses a group boundary — anything looser (e.g. grouping by geographic proximity, or by driving-time-matrix membership) could still let a multi-region employee's two regions land in different groups.

**Each group's solver payload is a real subset, not the full payload with irrelevant rows left in**: only that group's regions' employees, only visits whose region is in that group, only driving-time rows for that group's regions, and only existing (locked) assignments belonging to one of that group's included employees. This keeps each concurrent solve's problem size proportional to its own group rather than the whole company, which is the entire point of splitting the work.

**`time_limit_seconds` is applied unchanged, per group** (not divided by the number of groups) — since each group solves concurrently on its own process/core, giving each the same time budget as a `single`-mode run would use keeps solution quality comparable to today's while still cutting wall-clock time relative to solving everything sequentially in one call.

**Merging results is a plain concatenation**: every group's `scheduled` list and `unscheduled_visit_ids` list are concatenated into one `OptimizationProposal`, since groups by construction never reference the same visit or employee.

## Risks / Trade-offs

**Total CPU/JVM memory usage scales with the number of concurrently-running worker processes** (each boots its own JVM) — a real resource cost, not just a wall-clock win. → Mitigated by making the worker count an explicit, operator-set deployment parameter (not auto-scaled), so it can be sized to the actual machine running the solver service.

**A run whose regions are heavily interconnected by multi-region employees gets little or no speedup from `parallel` mode** (most or all regions end up in one group). → This is inherent to the safety guarantee (never split a shared employee across concurrent solves) and is surfaced honestly rather than worked around: the spec explicitly documents the fall-back-to-single-solve behavior rather than promising parallelism regardless of the region graph's shape.

**This is the first multi-process deployment concern introduced into what has otherwise been a single-process solver service** — worth a live check during implementation that `uvicorn --workers N` actually starts N independent, healthy JVMs locally (each worker's own startup log should show its own warm-up) before relying on it, following this project's established practice of verifying integration points live rather than assuming.

## Migration Plan

- No database change.
- Deployment change: the solver service's start command gains `--workers N` (N left as an operator-chosen constant for now, e.g. 4, documented alongside the existing `uvicorn` invocation) — purely additive; `--workers 1` (or omitting the flag) reproduces today's exact deployment.
- `OptimizeRunOptions.execution_mode` defaults to `single`, so no caller (frontend or otherwise) is affected until they explicitly opt into `parallel`.
