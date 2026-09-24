# AGENTS.md

Orientation for a coding agent picking up this repo (`fms_ros`, a field-service planning app). It records
**architecture, conventions, decisions that aren't obvious from the code, known limitations, and how to run/test things**.

**It deliberately does not restate behavior.** Required behavior lives in OpenSpec (`openspec/specs/<capability>/spec.md`);
the *why* behind non-trivial decisions lives in each change's `design.md` under `openspec/changes/archive/<date>-<name>/`.
When this file and a spec disagree, the spec wins - then fix this file. `README.md` covers first-time setup (parts of it
are stale, see "Known limitations").

---

## 1. Workflow: OpenSpec drives everything

Every non-trivial change here went through OpenSpec (`schema: spec-driven`, `openspec/config.yaml`):
`proposal.md` -> delta `specs/<capability>/spec.md` -> `design.md` -> `tasks.md` -> implement -> archive (which syncs deltas
into `openspec/specs/`). Slash commands live in `.claude/commands/opsx/` (`/opsx:propose`, `/opsx:apply`, `/opsx:archive`,
`/opsx:sync`, `/opsx:explore`, `/opsx:update`); the matching skills are in `.claude/skills/openspec-*`.

- Look up behavior first: `openspec list --specs`, `openspec show <capability> --type spec`.
- History and rationale: `ls openspec/changes/archive` (~45 archived changes, dated). Read the relevant `design.md` before
  redesigning anything - most "why is it like this" questions are answered there.
- **Resco status tracking**: archived at `openspec/changes/archive/2026-09-23-add-resco-work-order-status-tracking/`.
  Implementation is present; five verification tasks remain unchecked in its `tasks.md`. Read its `design.md` for the
  current-status-only decision and durable Draft-reset retries. No active change remains after this archive.
- Validate before archiving: `openspec validate <change> --strict`, and `openspec validate --specs` for main specs.
- Delta-spec rules that bite (all learned the hard way):
  - A `MODIFIED` requirement replaces the whole block: its header text must match the main spec **exactly**, and it must
    carry **every** existing scenario (same titles) or validation/archive refuses. You can rewrite scenario bodies, not titles.
  - To change a requirement's title or flip its meaning, use `REMOVED` (with **Reason**/**Migration**) + `ADDED`, not `MODIFIED`.
  - Plan-only commands (`/opsx:propose`) must not edit application code; `/opsx:apply` implements and ticks `tasks.md`
    checkboxes as it goes. Record surprises found mid-implementation in the change's `design.md`/`tasks.md` rather than
    silently absorbing scope.
- Commits are plain, lowercase, one per change (e.g. `local first masterdata sync`). Nothing pushes/commits automatically.

## 2. System overview

Three deployables plus Postgres:

| Part | Path | Stack | Port |
|---|---|---|---|
| Backend API | `backend/` | FastAPI, SQLAlchemy 2, Alembic, psycopg3, pydantic v2 | 8000 |
| Solver microservice | `solver/` | FastAPI + Timefold Solver (Python binding over the Java engine via JPype; JDK bundled by `jdk4py`) | 8100 |
| Frontend | `frontend/` | Vite + React 19 + TypeScript + Tailwind 4, Leaflet | 5173 |
| Database | `docker-compose.yml` | Postgres 16 (db/user/password all `fms_ros`) | 5432 |

External systems (both optional at runtime - see decisions below): **Tripletex** (accounting; customers/locations/products),
**Resco** (mobile CRM the field crew uses; OData v4, Basic auth), **TomTom** (driving-time matrices, day routes), **Nominatim**
(geocoding, 1 req/s rate limit via geopy).

### Domain in one paragraph

Customers have locations (each in a region). Contracts have contract lines (location + required products + interval +
duration + priority) that generate `ServiceVisit`s on a cadence anchored at the line's `start_date`. A visit is
`unassigned`/`assigned`; assigning creates an `Assignment` (**primary key is `service_visit_id`** - one assignment per visit,
no own id) with an employee and planned start/end. Employees have skills, regions, products, and a working-hours schedule
(template + per-day override). A visit is doable by an employee iff they cover its region and hold every skill required by
its contract line's products (`app/qualification.py`). The optimizer (solver service) proposes assignments; planners review
and apply. Entity list: `backend/app/models.py` (single file, ~25 tables). Note there is no ERD in the repo.

### Backend layout (`backend/app/`)

- `main.py` - **all** routes in one ~2100-line module (no routers). Grouped by resource; auth guard via `dependencies=[Depends(...)]`.
- `models.py` / `schemas.py` - SQLAlchemy models / pydantic in/out models (one file each, `Out` models use `from_attributes`).
- `auth.py` - JWT (HS256) in an httpOnly `session` cookie, 7-day TTL, bcrypt. Guards: `require_admin`, `require_session`
  (any logged-in user), `require_customer_access`; `customer_scope_ids(user)` returns `None` for admin, else the customer ids a
  customer-role user may see. Customer-portal endpoints must filter with it.
- `solver_client.py` - builds solver payloads from the DB, dispatches (single or per-region-group parallel), see section 4.
- `tripletex.py`, `resco.py` - external clients + sync functions (section 5).
- `visit_generation.py` (calendar-correct cadence math: months/quarters are calendar steps, not fixed day counts),
  `ad_hoc_visits.py` (free-slot search, 14-day horizon, 15-min steps), `employee_schedule.py` (template/override resolution),
  `tomtom_routing.py`, `geocoding.py`, `geofencing.py` (point-in-polygon region assignment), `solver_partitioning.py`
  (region grouping by shared employees), `demo_schedule_refresh.py`, `reset_demo_data.py`, `seed.py`, `demo_data/*.csv`.
- `alembic/versions/00NN_*.py` - hand-numbered linear migrations; DB head is `0027` (durable Resco Draft-reset context).
- `scripts/` - one-off, manually run, **not** part of startup/seed (`seed_admin_user`, Tripletex contact seeding, skill assignment).

### Solver layout (`solver/app/`)

- `domain.py` - `VisitAssignment` (planning entity: variables `employee`, `start_minutes`, `date`), `Schedule` (solution), facts.
- `constraints.py` - all constraints, hard/medium/soft tiers, documented weights. `solve.py` - request -> `Schedule` -> solve -> response.
- `schemas.py` - the HTTP contract with the backend. `jvm.py` - must run before any `timefold` import (sets `JAVA_HOME`/`PATH`).
- `solver/README.md` explains *how the optimizer scores/decides* (joint not greedy; hard > medium > soft; travel time is a
  pairwise-clustering proxy, not route optimization). Read it before touching `constraints.py`.

### Frontend layout (`frontend/src/`)

Not a router SPA: **five Vite HTML entry points** (`vite.config.ts`), each a separate React root:
`index.html` -> `App.tsx` (the **Planning** portal: Manual Assignment / Day Planning / Optimize tabs, admin only),
`admin-portal.html` (`admin-portal/`, master-data CRUD), `customer-portal.html` (`customer-portal/`, read-mostly, scoped to the
user's customers), `employee-management.html`, `login.html`. Navigation between portals is plain `<a href>`. State is local
`useState` per view; there is no store/query library. `api.ts` is the single HTTP layer (`apiFetch` sends cookies; base URL from
`VITE_API_URL`), `types.ts` mirrors backend schemas by hand (**keep both in sync when a `*Out` schema changes**),
`shared/auth.ts` (`useRequireRole`) redirects to login client-side (real enforcement is server-side).

## 3. Conventions

**Python (backend + solver)**
- Python 3.12, type-hinted, `X | None` unions, SQLAlchemy 2 `Mapped[...]`/`mapped_column`, no repo-wide formatter/linter config
  (follow surrounding style, ~100 col). Route handlers take `db: Session = Depends(get_db)`.
- **Soft delete everywhere**, never hard delete (except the demo reset script). Two flags exist on Customer/CustomerLocation/Product:
  `delete_flag` (set by the old Tripletex pull reconcile; effectively legacy now) and `archived` (set by the local delete
  endpoints). List queries filter **both**. Other entities use `delete_flag`.
- Datetimes are **naive** and carry no timezone anywhere in the app. Only the Resco payload builder localizes to `Europe/Oslo`
  (`_to_resco_datetime`). Don't introduce tz-aware datetimes elsewhere.
- Failures of secondary integrations must not fail the primary write: catch broadly (`except Exception`), log a warning,
  and report via a return value. Established shapes: `*RescoSyncResult` (`synced|skipped|failed`), `RescoSyncSummary`
  (created/updated/skipped/failed/errors), and the transient `sync_warning: str | None` on `Customer/Product/CustomerLocation` `*Out`.
- Transient response-only attributes are set on the ORM instance after the last commit (never re-`refresh()` afterwards) and
  surfaced through `from_attributes`.
- Code comments are sparse and explain **why** (constraints, incidents). Keep that; don't narrate the obvious.
- Tests are plain `pytest` functions; helper stand-ins for ORM objects (`_Visit`, `_Employee`) are the norm for pure logic.

**Frontend**
- Function components + hooks, Tailwind utility classes inline (slate palette; emerald = primary action, amber = warning,
  red = error). Shared bits in `shared/` (`ListTable`, `DetailField`/`BackButton`, `SyncStatusBadge`, `GeoShapeEditor`).
- List view -> detail view pattern per entity (`selectedId` state; `onChanged()` refetches from the parent). Transient
  `sync_warning` from create/update responses is captured from the mutation's return value and shown inline in amber.
- Type-check with `tsc -b` (part of `npm run build`), lint with `oxlint`. Both should be clean before you finish.

## 4. Key design decisions (pointers, not restatements)

- **fms_ros is the master for masterdata; Tripletex/Resco are downstream** (`local-first-masterdata-sync`). Customer /
  CustomerLocation / Product ids are **fms_ros-assigned**; the Tripletex id is a separate nullable `tripletex_id`
  (migration `0025` back-filled it from the old id, so legacy rows have `id == tripletex_id` - never rely on that for new rows).
  Create = persist locally, *then* best-effort push; the backend starts and works with both integrations unreachable; **no sync
  runs at startup**. The "Sync to Tripletex" button (`POST /customers/sync`, `/products/sync`, admin-only) is a *push/bootstrap*:
  create-if-no-`tripletex_id`, else update; customers are processed before their locations. It processes the **entire table**,
  not just recent rows. Never send a local `.id` to a Tripletex API - use `.tripletex_id`.
- **Multi-day scheduling** (`add-multi-day-scheduling-window`, `improve-multi-day-solve-quality`): visit `date` is a solver
  planning variable over the run's window (`days_ahead`, default 2, capped at `MAX_DAYS_AHEAD = 14` in `solver_client.py`).
  Two soft preferences with a deliberate ~10:1 ratio: stay near the visit's *nominal* `requested_date`, and keep the contract
  interval measured from the previous occurrence's **nominal** (not actual) date, so a delayed visit doesn't drag the schedule
  (revenue-critical - see that change's design). `effective_schedule_date` floors past-due visits to today.
- **Solver concurrency**: the solver keeps **one process-wide `SolverFactory`** (lock-guarded, `solve.py`) and applies the
  per-request time budget via `SolverConfigOverride`. Building the factory per request races inside JPype under concurrent
  requests. Do not "simplify" this back. Timefold's Community Edition is in use: `nearby_distance_meter_function` and
  `move_thread_count` raise `RequiresEnterpriseError`.
- **Execution modes**: `single` (default) or `parallel`. Above `settings.parallel_split_visit_threshold` (75 ready visits) a
  run is split into independent region groups even in `single` mode (`solver_client.resolve_run_payloads`); regions sharing an
  employee stay together, so a multi-region employee defeats splitting. Default time budget scales with window size
  (`_default_time_limit_seconds`, cap 90s); solver `unimproved_spent_limit` = `max(5, budget // 3)`. Constraint construction
  heuristic throughput, not local search, is the bottleneck at ~150 visits (see `improve-multi-day-solve-quality/design.md`).
- **Pinned/locked assignments**: pinned, or already started, assignments are fixed facts for the solver; everything else is a
  candidate. See the `assignments` spec for the past-Scheduled reconciliation exception.
- **Resco Work Order = two records**: `fs_workorder` (name, customer, asset) + child `fs_workorderschedule` (start/end/resource),
  employee's `fs_resource` looked up by `__targetid_id`. `Assignment` stores both Resco ids. Resco pushes are triggered inline
  after the write; this codebase never deletes anything in Resco. Functional-location/Asset mapping, customer contacts,
  status reads and conditional Draft resets are documented in the archived status-tracking change above.
- **Driving times**: per-region TomTom matrix persisted in `driving_times` (`origin/destination` are `(kind, id)` pairs, not FKs);
  missing pairs fall back to a Haversine estimate at 40 km/h in the solver, so travel is never free.
- **Demo data**: `reset_demo_data.py --confirm` (destructive, wipes local *and* Tripletex customers) and
  `POST /demo/refresh-schedule` shift/reseed demo visits. Specs: `demo-data-reset`, `demo-schedule-refresh`.

## 5. Development commands

Shell is Windows; the Bash tool (Git Bash) works and venvs are `.venv/Scripts/...`. Run each service from its own directory.

```sh
docker compose up -d                                   # Postgres
# backend/
.venv/Scripts/python.exe -m alembic upgrade head       # apply migrations (also: alembic current)
.venv/Scripts/python.exe -m uvicorn app.main:app --reload            # :8000, docs at /docs
.venv/Scripts/python.exe -m scripts.seed_admin_user    # one-time; prints the admin password once (login "sfm_admin")
# solver/
.venv/Scripts/python.exe -m uvicorn app.main:app --port 8100 --workers 4   # multi-process; --reload and --workers are mutually exclusive
# frontend/
npm run dev        # :5173      npm run build   # tsc -b + vite build      npx oxlint
.\start-dev.ps1    # everything at once (solver runs with --workers 4, so no hot reload for solver code)
```

Config: `backend/.env` (copy `.env.example`). **`JWT_SECRET_KEY` is required (no default) but is missing from `.env.example`** -
the backend won't start without it. Also `DATABASE_URL`, `TOMTOM_API_KEY`, `RESCO_USERNAME`/`RESCO_PASSWORD`;
Tripletex uses a refresh token read from `backend/.local/api_key` (gitignored, not in `.env`). `frontend/.env`: `VITE_API_URL`.
Never commit credentials; do not print `.env`/`.local/api_key`.

New migration: add `backend/alembic/versions/00NN_<slug>.py` by hand (next number, `down_revision` = previous), keep it additive
where possible (see `0025` for a data-preserving example), run `alembic upgrade head` locally, and update `models.py` to match.

## 6. Testing

```sh
# backend/   (32 tests, ~2s)         # solver/   (~30 tests, ~20-30s: boots a JVM)
.venv/Scripts/python.exe -m pytest tests/ -q
```

- **Backend tests touch the real dev Postgres** (`SessionLocal`); there is no isolated test DB or conftest. Tests that create rows
  (`test_masterdata_local_first_sync.py`, `test_bootstrap_sync.py`) mock Tripletex/Resco/geocoding and delete their rows in
  `finally`; when deleting a Customer/Product/Location you must first delete its `*SyncLog` rows (FK). A failed run can leave rows
  behind that make the next run fail on unique `tripletex_id` - clean them up by hand. The bootstrap-sync functions iterate the
  whole table, so tests assert on *their own* rows, not global call counts, and also write harmless extra sync-log rows for
  real records. Never run those functions unmocked against the real integrations (they'd push every real customer).
- Pure-logic backend tests (`test_plan_from_floor`, `test_solver_partitioning`, `test_split_decision`,
  `test_compute_previous_occurrences`) use stand-in objects and need no DB.
- **Solver constraint tests** use `ConstraintVerifier`. Use `.penalizes_by(N)` (total weighted score) for weighted
  `.penalize(ONE_SOFT, lambda...)` constraints and `.penalizes(N)` (match count) only for flat-weight ones. End-to-end tests call
  `solve_schedule` directly with `time_limit_seconds` of a few seconds.
- `Windows fatal exception: access violation` printed by faulthandler during solver pytest is a **known benign** JPype/JVM
  artifact - trust the final pass/fail line.
- Frontend has **no automated tests**; verify with `npx tsc -b`, `npx oxlint`, and by exercising the UI in a browser.
- Live checks against Resco are established practice for schema work (inspect `$metadata`, create a throwaway record) - but Resco
  cannot be cleaned up by this codebase, so keep them minimal and name them clearly; Tripletex offers `delete_customer`.
- Prefer verifying by calling functions directly (a Python one-off with `PYTHONPATH=backend`) over relying on a `--reload`
  server having picked up changes.

## 7. Known limitations and gotchas

- **Stale pieces after the local-first change** (not fixed): `backend/app/seed.py` still calls `sync_customers/_locations/_products`,
  which used to *pull* from Tripletex and now *push* - on an empty DB `seed.py` creates no customers/locations/products and
  the rest of its script assumes they exist. `backfill_location_coordinates.py`'s docstring describes the old pull sync.
  `README.md` says "first slice", omits `JWT_SECRET_KEY`, and documents a single-worker solver; treat `start-dev.ps1` as truth.
- The old pull-only Customer columns (address JSON blobs, invoice flags, categories, ...) are dead weight; only name/email/phone/
  organization_number are edited or pushed. The client methods `get_products`/`get_delivery_addresses` are unused.
- **Tripletex demo/sandbox account is expired/down**; the connected credential also returned `403` on customer create. Expect
  Tripletex pushes to fail with a `sync_warning` - that is the designed degraded mode, not a bug. Resco (`sfm`) works and holds
  a few stray "Manual Verify ..." test records from verification.
- **Solver scale**: ~150 visits in one connected region group exceeds what the construction heuristic finishes in a practical
  budget; a multi-region employee (region graph connected) defeats the splitter. One employee per region splits cleanly
  (measured 125/150 scheduled across 7 days). Enterprise-only Timefold features are the known next lever.
- Solver on Windows with `--workers N` can occasionally lose one worker to `WinError 10022` at startup; uvicorn respawns it (see `solver/README.md`).
- `main.py` and `models.py` are single large files; `GET /assignments` and `/service-visits` return unbounded lists (the board
  filters client-side), and Nominatim geocoding is sequential at 1 req/s, so bulk location creation is slow.
- Resco status refresh is on demand; there is no background polling. Audit API errors do not block current-status sync.
  Remaining live visual verification is recorded in the archived status-tracking tasks.
- The frontend duplicates backend types by hand and has no test coverage; response-shape changes are easy to miss in `types.ts`.
