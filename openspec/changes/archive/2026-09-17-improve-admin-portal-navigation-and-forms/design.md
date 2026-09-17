## Context

Four independent Vite multi-page apps exist today (`index.html` = Planning, `customer-portal.html`, `employee-management.html`, `admin-portal.html`), each its own React root with its own `<aside>` sidebar. Only Planning's `App.tsx` links out to the other three (plain `<a href="...">` tags next to its Manual Assignment/Day Planning/Optimize view buttons); the other three sidebars have zero cross-links to each other or back to Planning. `CustomerPortalApp.tsx` already has a "Viewing as" `<select>` above its entity nav (`viewingAsCustomerId: number | null`, with an "All customers" option) that `EmployeeManagementApp.tsx` lacks. `EmployeesView.tsx`'s `EmployeeForm` toggles skills via a generic `toggle(setSkillIds, id)` helper against a `skillIds: number[]` array. `ContractsView.tsx`'s contract-line form has no heading over its date/interval/duration row, unlike "Required products" which has one. `ContractLine.interval_days: int` is a flat day count; `visit_generation.py`'s `generate_occurrence_dates`/`extend_occurrence_dates` step purely by `timedelta(days=interval_days)`. The only interval value in use today is 15 (`reset_demo_data.py`'s `CONTRACT_LINE_INTERVAL_DAYS`, applied to all ~150 demo contract lines).

## Goals / Non-Goals

**Goals:**
- Every portal can reach every other portal via a small, consistent set of links, without turning the four apps into one shared shell.
- Employee Management gets the same "pick one or all" ergonomics Customer Portal already has.
- Contract-line recurrence can express "every month" or "every quarter" without day-count drift.
- No behavior change to anything else about contract lines/visits (priority, required products, soft-delete, generation horizon).

**Non-Goals:**
- A shared app shell, unified routing, or a single-page-app merge of the four portals — they remain four separate builds; this only adds links between them.
- Any change to authentication/access control here — that's `add-user-authentication`. These nav links are visible to whoever can already reach any portal today (nothing gates them).
- A fully generic recurrence engine (arbitrary N-of-unit, "every 5th Tuesday", etc.) — the fixed combination list below is deliberately small.

## Decisions

**Cross-portal links are added as plain sidebar links, reusing the exact pattern Planning's `App.tsx` already uses** (`<a href="/admin-portal.html">`, etc.) — no new shared component, no routing library. Each of the three other sidebars gets links to the *other three* (Admin Portal links to Planning + Customer Portal + Employee Management; etc.). This requires a MODIFIED requirement on each portal's "separate top-level area" spec (all three currently say "sharing no header or navigation elements with X") to carve out this specific, small exception — everything else about the portals staying visually/structurally separate is unchanged.

**Employee Management's selector copies Customer Portal's `viewingAsCustomerId` pattern verbatim**, renamed to `viewingAsEmployeeId: number | null`, filtering `EmployeesView`'s list the same way. No new backend endpoint — filtering happens client-side against the already-fetched employee list, exactly like Customer Portal does today.

**"Select all skills" is a one-line `setSkillIds(skills.map(s => s.id))` button** next to the existing skills checkbox list — no new backend behavior, since `EmployeeUpdate`/`EmployeeCreate` already accept an arbitrary `skill_ids` array.

**Contract-line recurrence becomes `interval_unit: Literal["week", "month", "quarter"]` + `interval_count: int`, restricted to a fixed allow-list** (week: 1-4, month: 1-3, quarter: 1 only) validated server-side (not just hidden in the UI dropdown) via a shared constant, matching how `ProductCreate`'s `product_type` is already a `Literal["TJN", "PRD"]`. This is a deliberately small, curated set ("simplicity is key" per the request) rather than a free N×unit combinator.

**Month/quarter stepping is implemented with a small stdlib-only helper, no new dependency.** `python-dateutil` is not installed anywhere in this project; adding a real calendar-month-add helper (add N months to a date, clamping the day-of-month to the target month's actual last day via `calendar.monthrange`) is ~10 lines and avoids pulling in a new library for one function. A quarter is exactly 3 months for this purpose. `week` stays a plain `timedelta(weeks=interval_count)` — weeks are already a fixed 7 days, no calendar-awareness needed there.

**Every occurrence is computed as N months after the original `start_date`, never as N months after the previous occurrence.** Found during manual verification (task 7.3): iteratively stepping from the previous occurrence permanently drifts a day-31 start down to day-28 the first time it clamps (Jan 31 → Feb 28 → Mar 28 → Apr 28 ...) instead of the expected Jan 31 → Feb 28 → Mar 31 → Apr 30. `nth_occurrence(start_date, unit, count, n)` computes the n-th occurrence directly from `start_date`, so each month's clamping is independent. `extend_occurrence_dates` therefore also takes the line's `start_date` (not just its furthest-generated date) so extension continues the same anchored sequence rather than restarting drift from wherever generation last stopped.

**Migration approximates every existing contract line's `interval_days` to the nearest supported combination.** The only value in live use today is 15 days, which maps to `week`/2 (14 days — a 1-day approximation, accepted since this is demo data, not a real customer commitment). The migration converts by nearest-day-equivalent: rows within a few days of a supported week/month value snap to it; anything with no reasonable nearby match (unlikely given today's single value) falls back to `week`/4 (28 days, the closest supported ceiling) rather than failing the migration. This is a one-time, additive-in-spirit conversion — no data is lost, only `interval_days` is replaced by its nearest `interval_unit`/`interval_count` equivalent.

## Risks / Trade-offs

**The interval-model change is `**BREAKING**`**: `ContractLineCreate`/`ContractLineUpdate`'s `interval_days` field disappears entirely, replaced by `interval_unit`/`interval_count`. → Mitigated by the migration converting existing rows in place (see above) and by this being the only consumer of that schema shape (no external API contract to preserve).

**A monthly/quarterly interval's calendar-month stepping means the *number of days* between two consecutive visits varies** (28-31 days for month, ~90-92 for quarter) — this is intentional (matches what "every month" actually means to a planner) but is a real behavior difference from every other interval-driven computation in this codebase, which has so far always assumed a fixed day-count cadence. Reviewed `visit_generation.py`'s only two functions and confirmed neither is used anywhere that assumes a constant day delta between occurrences (both just emit a `list[date]`).

## Migration Plan

- `contract_lines.interval_days` (int, not null) → dropped.
- `contract_lines.interval_unit` (string, not null) and `contract_lines.interval_count` (int, not null) → added.
- Data migration step (same Alembic revision): for every existing row, compute the nearest supported `(interval_unit, interval_count)` from its `interval_days` value using the day-equivalent mapping above, and set the two new columns before dropping `interval_days`.
- No changes to `service_visits` rows themselves — already-generated visits keep their `requested_date`; only future generation/regeneration uses the new interval representation.
