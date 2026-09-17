## Context

fms_ros had a `Skill` entity once before: migration `0003_contracts_and_skills.py` created `skills`, `employee_skills` (Employee↔Skill), and `contract_skills` (Skill↔Contract). Migration `0013_replace_skills_with_products.py` (commit `201759a`) dropped all three tables outright — its own comment says *"skills and their assignments are not carried over to products — the two are different data sources with no defined mapping between them"* — and replaced them with the current `Product`/`employee_products`/`contract_line_products` model. No employee-skill data survived that migration to carry forward here; this change starts fresh.

Today's qualification check ("can this employee do this visit") lives in three places, all doing the same `employee.products ⊇ visit.required_products` comparison:
- `backend/app/ad_hoc_visits.py`, `_qualifying_employees`: `required_product_ids.issubset({p.id for p in employee.products})`.
- `solver/app/constraints.py`, `_missing_products`: `not visit.required_product_ids.issubset(visit.employee.product_ids)`, wired as the `HardMediumSoftScore.ONE_HARD` constraint `"Missing required product"`. The solver's own domain (`solver/app/domain.py`) represents both sides as plain `frozenset[int]` — `Employee.product_ids`, `VisitAssignment.required_product_ids`.
- `backend/app/solver_client.py`, `build_optimize_payload`: sends `employee.products` and `visit.contract_line.required_products` ids into the solver payload as `product_ids`/`required_product_ids`.

`Product` (`backend/app/models.py`) is otherwise exactly what `add-master-data-crud` leaves it: `id` (Tripletex id), `number`, `name`, `delete_flag`, `resco_product_id`, plus `employees` (via `employee_products`) and `contract_lines` (via `contract_line_products`). Live data: `employee_products` currently has 7 rows across 2 of the 3 active employees (Bram de Vries: 4 products, John Johnson: 3, **Alice Johnson: 0** — she is not qualified for any visit today under the current model); `contract_line_products` has 150 rows linking contract lines to products.

## Goals / Non-Goals

**Goals:**
- `Skill` and `ServiceOrderType` as new, local-only entities (no Tripletex/Resco involvement — the proposal is explicit these live in fms_ros only), each with full Admin Portal CRUD, matching the shape of every other local masterdata entity (`Region`, and now `Skill`/`ServiceOrderType`).
- Employee qualification becomes skill-based end to end: `ad_hoc_visits.py`, the Timefold solver, and the Manual Assignment UI all agree on "employee holds every skill the visit's required products require."
- `Employee.products`/`employee_products` removed outright — this change does not keep them around as a deprecated, unused parallel path.

**Non-Goals:**
- Migrating the 7 existing `employee_products` rows into anything — per Context, there's no defined mapping from "held this product" to "holds this skill," same reasoning migration 0013 used when it went the other direction. The 3 active employees get skills assigned fresh, per this change's own demo-data task, matching exactly what the user specified.
- Any Tripletex/Resco integration for Skill or ServiceOrderType — confirmed local-only per the proposal.
- A skill hierarchy, skill levels, or certification/expiry dates — a skill is just a name an employee either holds or doesn't.
- Changing what a contract line requires — contract lines keep requiring products, unchanged; only the employee side of the match moves to skills.

## Decisions

**`Skill` and `ServiceOrderType` are flat, minimal entities (id, name, soft-delete flag) — no fields beyond that.** Matches `Region`'s shape exactly (the simplest existing local masterdata entity) and everything the user actually asked for; nothing else was requested.

**`product_skills` (Product↔Skill, many-to-many) and `employee_skills` (Employee↔Skill, many-to-many) are new association tables; `service_order_type_id` is a nullable FK on `Product`.** Nullable because only the 4 demo products (see below) get one assigned by this change — every other real, Tripletex-sourced product (including TJN10004, which is deliberately left out of this scheme) is untouched and simply has none, which the `products` spec delta already states as a valid, retrievable state ("Product with no service order type").

**`employee_products` and `Employee.products` are dropped outright, not deprecated.** The user was explicit ("not the products as we currently have"), and per Context there's no reason to keep a table nothing reads anymore. `ad_hoc_visits.py`, `solver/app/domain.py`, `solver/app/constraints.py`, and `backend/app/solver_client.py` are updated in the same change to read skills instead — there is no intermediate state where both exist.

**The skill check is computed by joining through products at query/payload-build time, not by denormalizing "effective skills" onto anything.** A visit's required skills = the union of `product.skills` for every product its contract line requires; an employee qualifies when their skills are a superset of that union. This is computed fresh in `_qualifying_employees`, in `build_optimize_payload` (sent to the solver as plain id sets, same shape as today's `product_ids`/`required_product_ids` — the solver's own domain and constraint logic barely change beyond a rename, since it's still just two `frozenset[int]` and a subset check), and in the service-visit list endpoint (for display). No caching or materialized view — visit/product/employee counts here are small (hundreds, not millions), matching how `required_product_ids` is already computed the same way today.

**Demo data is a one-off script, not permanent tooling** (matching the Tripletex-contact-seeding precedent from the Resco integration work), run once during implementation. This reuses 4 existing, already-synced-from-Tripletex products rather than creating new ones — decided after discovering live that none of the 4 real demo products' Tripletex names are actually about winter work except one that wasn't originally picked for it:
- 2 skills: "Inspeksjon (vaktmester)", "Snømåking".
- 2 service order types: "Generelle vaktmestertjenester", "Vaktmestertjenester (vinter)".
- Product assignments (no products are created — all 4 already exist locally, synced from real Tripletex products):
  - `TJN10001`/`TJN10002`/`TJN10003` ("Vaktmesteravtale 1-45"/"1-23"/"1-12"): service order type "Generelle vaktmestertjenester", requiring skill "Inspeksjon (vaktmester)". Names/descriptions are left as-is.
  - `TJN10010` ("Vintervedlikehold liten" — Tripletex's own name already describes winter maintenance): service order type "Vaktmestertjenester (vinter)", requiring both "Inspeksjon (vaktmester)" and "Snømåking". Its name is left as-is since it already fits.
  - `TJN10004` ("Vaktmesteravtale 2-45") is deliberately excluded from this scheme — no service order type, no required skills. Every contract line that currently requires it (~40, from `reset_demo_data.py`'s demo dataset) has its `required_products` association changed to `TJN10010` instead, so those visits' required skills come from the winter service order type going forward. `TJN10004` itself keeps existing as an ordinary, untyped product with no contract lines pointing at it after this runs.
- Employee skills — inverted from a plain "the newest employee is special" pattern to match the existing "held back" precedent in `reset_demo_data.py` (where all-but-the-last employee get the fuller capability set): Alice Johnson and Bram de Vries get both "Inspeksjon (vaktmester)" and "Snømåking"; John Johnson (the highest-id active employee) gets only "Inspeksjon (vaktmester)" — he is the one held back from winter-qualified work, not the one uniquely qualified for it.
- This task depends on `add-master-data-crud`'s `PATCH /products` endpoint existing (to persist `skill_ids`/`service_order_type_id` on the 4 reused products) — see proposal.md. It no longer depends on that change's `POST /products` endpoint, since no product is created.

## Risks / Trade-offs

**Dropping `employee_products` loses today's 7 real employee-product associations (Bram de Vries: 4 products, John Johnson: 3) with no migration path.** → Accepted per Context/Non-Goals: there's no defined product→skill mapping to migrate through (the same conclusion migration 0013 reached in the opposite direction), and this change's own demo-data task immediately re-establishes real qualifications for all 3 active employees under the new model — nobody ends up unqualified who wasn't already going to be reassigned skills anyway.

**The Timefold solver's domain/constraint changes are a rename plus a data-source change (`frozenset[int]` of product ids → `frozenset[int]` of skill ids), not a new kind of check** — low risk of behavioral surprise, but still needs the existing solver test suite (`solver/tests/`) updated everywhere it constructs a `VisitAssignment`/`Employee` with `product_ids`/`required_product_ids`, since those fields are renamed.

## Migration Plan

- New tables: `skills`, `service_order_types`, `product_skills`, `employee_skills`. New column: `products.service_order_type_id` (nullable FK).
- Dropped: `employee_products` table, and the `Employee.products`/`Product.employees` relationship in `backend/app/models.py`.
- No backfill for the new tables (they start empty; the demo-data script populates them). No backfill needed for `service_order_type_id` (nullable, existing products stay null).
- This is destructive for `employee_products` specifically (see Risks) — everything else is additive.
