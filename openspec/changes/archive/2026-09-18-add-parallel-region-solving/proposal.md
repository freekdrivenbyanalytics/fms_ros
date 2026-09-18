## Why

A schedule run's solve time grows with problem size (employees × visits × candidate start times), and today every run — regardless of size — solves the entire company as one problem on one CPU core. Timefold's own built-in multithreaded move evaluation (`move_thread_count`) turned out, on investigation, to require a paid `timefold-solver-enterprise` license that isn't installed (`RequiresEnterpriseError` is raised the moment it's set to anything but its default `NONE`) — this is a licensing boundary, not a bug, so it is not something to work around by patching the open-source package. Real parallelism is still achievable a different way: most regions don't share any employees, so their sub-problems are already independent and can be solved concurrently on separate CPU cores without touching Timefold's own threading at all.

## What Changes

- Add an `execution_mode` parameter (`single`, the existing default, or `parallel`) to a schedule-proposal run, exposed as a choice on the Optimize page, following the same plumbing already used for `days_ahead`/`time_limit_seconds`.
- When `parallel` is selected: partition this run's ready-to-schedule visits by region, group regions that share at least one scoped employee into a single group (since splitting those across independent solves could let two concurrent solves double-book the same employee), and solve each fully independent region-group concurrently, each as its own ordinary (unmodified) Timefold solve. Results are merged back into one proposal, identical in shape to today's response.
- If every region in scope for a run turns out to share employees transitively (one connected group), `parallel` mode has nothing to split and transparently falls back to today's single solve — never an error, never worse than `single` mode.
- The solver service starts with multiple worker processes (`uvicorn --workers N`) so concurrent solves run in genuinely separate OS processes, each with its own independent embedded JVM — no shared state between them, and no change to Timefold's own solving code.

## Capabilities

### Modified Capabilities
- `route-optimization`: a proposed-schedule run gains an `execution_mode` parameter; `parallel` mode's region-partitioning behavior and its safety guarantee (never splits a region-group that shares an employee) become part of the spec.

## Impact

- `backend/app/schemas.py`: `OptimizeRunOptions` gains `execution_mode: Literal["single", "parallel"] = "single"`.
- `backend/app/solver_client.py`: new region-partitioning logic (connected components of regions by shared employee scoping); when `parallel` mode applies and yields 2+ groups, builds one solver payload per group and fires them concurrently (a `ThreadPoolExecutor` around the existing synchronous `httpx.post` call — no new async runtime), then merges the responses. When it yields exactly 1 group, or `execution_mode` is `single`, behavior is byte-for-byte identical to today's single call.
- `solver/`: no change to `solve.py`/`domain.py`/`constraints.py` — each concurrent call runs the exact same unmodified single-process solve Timefold already does today, just N of them at once, in separate worker processes. Only the process's own startup command changes (`--workers N`).
- `frontend/src/types.ts`, `frontend/src/api.ts`: `OptimizeRunOptions` gains `execution_mode`.
- `frontend/src/components/OptimizeView.tsx`: a new "Execution mode" selector (Standard / Parallel by region), alongside the existing days-ahead/time-limit controls.
- No database schema change.
