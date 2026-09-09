## Context

`Skill` (`backend/app/models.py:114-128`) is a purely local, hand-CRUD'd entity: `id`, `name`, `delete_flag`, joined to `Employee` via `employee_skills` and to `ContractLine` via `contract_line_skills` — both plain many-to-many tables. `backend/app/tripletex.py` already has a full, working sync pattern for two other Tripletex-sourced entities (`sync_customers`, `sync_customer_locations`): authenticate via a refresh-token-derived session (`TripletexClient`), page through `GET {base_url}/customer` and `GET {base_url}/deliveryAddress` with `from`/`count`, map Tripletex's camelCase fields to local snake_case attributes, and upsert-by-Tripletex-id with soft-delete-if-missing / restore-if-reappearing, logging every change to a `*SyncLog` table.

Tripletex's public API confirms a `GET /product` endpoint exists with exactly the same shape: `id`, `number`, `name`, `isInactive` fields; `from`/`count` pagination; and a `number` query parameter that filters "containing" a substring — so `number=TJN` can do the TJN-prefix filtering server-side, at the API call, rather than fetching everything and filtering client-side.

The seed script (`backend/app/seed.py`) already calls the live Tripletex API for customers/locations on every run (`sync_customers(db)`, `sync_customer_locations(db)`, lines 33-34); skills, by contrast, are fabricated locally via a `_get_or_create` helper. This proposal brings skills' seeding in line with customers/locations: a real sync call, then picking specific known product numbers from what comes back.

10 capability spec files reference "skill" in some form; see proposal.md's Capabilities section for the full list.

## Goals / Non-Goals

**Goals:**
- Mirror the existing Tripletex sync pattern exactly — no new sync architecture, just a new entity following the established shape.
- Filter to TJN-numbered products at the Tripletex API call itself (`number=TJN`), not by fetching everything and filtering afterward.
- Preserve the exact multi-association shape skills had on both sides (an employee can hold several products; a contract line can require several products) — per explicit user decision, only the contract-line form's *control* becomes a dropdown, not the underlying data model.
- One coherent, single change — despite touching many files, this is one behavioral shift (skill → Tripletex product) applied consistently, not several unrelated concerns.

**Non-Goals:**
- No skill-to-product data migration. Existing skill assignments are lost (see Risks). This is a deliberate, irreversible migration per the user's explicit "remove the skills interface and tables" instruction.
- No change to the Employee form's control shape. It stays a multi-select (checkboxes today), just re-pointed at products instead of skills — the user's request only called out a *dropdown* for the contract-line control specifically.
- No local product editing of any kind (name, create, delete) — Tripletex is the sole master, exactly like customers.
- No "offers" concept (mentioned as future context in an earlier, unrelated change) — out of scope here.
- No credential-exposure requirement for the new sync (mirrors `sync_customers`, which has none documented either — proportionate, not a new gap).

## Decisions

- **Multi-select on both sides, confirmed by the user.** A contract line can require several products (not narrowed to one), and an employee can hold several products. This keeps the solver's existing subset-match logic (`required_product_ids.issubset(employee.product_ids)`) unchanged in shape — only the field/constraint names change from skill to product.
- **Read-only Products view + sync trigger in the Admin Portal, confirmed by the user.** Placed where Skills lived (replacing its nav entry), not in the Customer Portal (where the Customers sync trigger lives) — Products is masterdata for staffing qualification, which is Admin Portal's domain, not customer-facing browsing.
- **TJN-prefix filtering happens client-side, after fetching.** Tripletex's public API spec suggested `number` supports a "containing" filter, but a live call against this project's actual tenant returned a 422 ("must be a comma-separated list of positive integers") for `number=TJN` — the real endpoint's `number` param filters by numeric id, not by product-number substring. Confirmed via a live call: `GET /product` with no filter returns all 21 products in this tenant (including `TJN10001 Vaktmesteravtale 1-45`, matching the user's example exactly), so client-side `str.startswith("TJN")` after an unfiltered fetch is both correct and cheap at this scale.
- **Destructive migration, no data preservation.** The new Alembic migration drops `skills`, `employee_skills`, `contract_line_skills` outright and creates `products`, `employee_products`, `contract_line_products`. There is no automated mapping from a skill name ("Electrical") to a Tripletex product number ("TJN10001") — inventing one would be guessing at business meaning that isn't ours to assume. Existing skill-based assignments are lost; reseeding (or a real Tripletex product sync) is how the system regains its qualification data.
- **Seed script mirrors the customer/location pattern**: call `sync_products(db)` for real (hitting live Tripletex, filtered to TJN), then randomly assign whichever of TJN10001/TJN10018/TJN10010 come back to the seeded employees and contract lines. Names for TJN10018/TJN10010 aren't fabricated — they come from the real synced data, exactly like customer names already do.
- **Purpose sections are hand-edited at archive time, not via delta.** Per OpenSpec's own rule (a delta's `## Purpose` is ignored for an existing capability), the `contracts`, `customer-portal`, and `route-optimization` main specs' Purpose text (which mention "skill") need a direct edit when this change is archived — flagged here so it isn't missed.
- **Two scenario titles keep their old "skill" wording even though their body text now says "product"**: `route-optimization`'s "Proposal respects required skills" and `assignments`'s "Planner filters a list by region and skill." Both are one scenario inside an otherwise-stable, multi-scenario requirement; OpenSpec's delta model matches MODIFIED requirements and (implicitly) their scenarios by title, so renaming just the title would either silently orphan the original scenario or force reproducing every sibling scenario twice for one label fix. Accepted as a minor, deliberate terminology artifact rather than a correctness problem.

## Risks / Trade-offs

- [Existing skill-to-employee/contract-line assignments are permanently lost] → Explicitly requested by the user ("remove the skills interface and tables"); mitigated by the seed script re-establishing sample data, and by the fact that a real deployment would re-run the product sync and reassign qualifications through the new UI.
- [Two scenario titles now say "skill" while their bodies say "product"] → Documented above; a future cosmetic-only change could retitle them via a proper requirement-level REMOVE+ADD if desired.
- [The exact Tripletex `/product` field names (`number`, `name`, `isInactive`) are taken from Tripletex's public API spec, not verified against this project's own Tripletex tenant] → Task list includes verifying field names against a real sync call before considering the sync "done," the same diligence `sync_customers`/`sync_customer_locations` already required when they were first built.
