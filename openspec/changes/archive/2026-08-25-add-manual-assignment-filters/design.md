## Context

`frontend/src/components/EmployeeList.tsx`, `UnassignedVisitList.tsx`, and `AssignedVisitList.tsx` each render one of the three columns on the manual-assignment page (`frontend/src/App.tsx`), receiving already-fetched `employees`/`visits`/`assignments` as props with no local filtering today. `Employee` carries `regions: Region[]` and `skills: Skill[]` directly; `ServiceVisit` carries region and skills at `contract.customer_location.region` and `contract.required_skills`. `AssignedVisitList` renders from `visits` (assigned ones) joined against `assignments` for the employee — its cards show the visit's region/skills, matching `UnassignedVisitList`. See proposal.md - Why / What Changes for motivation and scope.

## Goals / Non-Goals

**Goals:**
- Give each of the three columns independent search + region/skill multi-select filtering without touching the backend or the data already fetched in `App.tsx`.
- Share the filter-bar UI and matching logic across the three columns so the three implementations don't drift.

**Non-Goals:**
- No persistence of filter/search state across reloads or across switching to the Day Planning view.
- No filtering by anything other than name/address (search) and region/skill (filters) — e.g. no date-range or duration filtering in this change.

## Decisions

- **One reusable `ListFilterBar` component + one reusable filtering hook**, e.g. `frontend/src/components/ListFilterBar.tsx` and a small `useListFilter`-style helper, parameterized by the region/skill options to offer and a per-item `(item) => { name, address?, regions, skills }` extractor. Each of the three list components owns its own `ListFilterBar` instance (independent state, per the confirmed "independent per column" scope) and calls the shared matcher to filter its own array before rendering. Alternative considered: copy-paste the same filter UI and logic into all three components — rejected because the three lists share the exact same filter shape (search + region multi-select + skill multi-select) and duplicating it three times risks the columns silently drifting in behavior.
- **Filter options (which regions/skills appear in each column's dropdowns) are derived from that column's own full item list** (e.g. Employees' region dropdown lists only regions actually used by an employee), not from a separate `/regions`/`/skills` endpoint — no such endpoint exists today, and the data already in memory is sufficient. Alternative considered: fetch `/regions` and `/skills` for a complete, always-full options list — rejected as an unnecessary new API surface for an option set already fully derivable from loaded data.
- **AssignedVisitList filters using the visit's region/skills** (its `contract.customer_location.region` / `contract.required_skills`), consistent with `UnassignedVisitList`, not the assigned employee's region/skills — assignment cards are keyed on the visit throughout the app today, and mixing in employee-derived filtering would make the three columns' filter semantics inconsistent.
- **Matching is case-insensitive substring search** on the extracted name/address, and a card matches the region/skill filters when it has at least one selected region (if any selected) AND at least one selected skill (if any selected) — this is the "Multi-select dropdowns" behavior already confirmed with the user.

## Risks / Trade-offs

- [A column showing "No results" when filters are too narrow could look like the list is broken/empty] → Show a distinct empty-state message ("No matches for the current search/filters") separate from the existing "No employees."/"No unassigned visits." empty state, so a filtered-to-zero list reads differently from a genuinely empty list.
- [Deriving filter options from loaded data means an option (e.g. a region) with zero current items in a column never appears in that column's dropdown] → Acceptable: the option would filter to nothing anyway, so omitting it doesn't reduce what a planner can actually select usefully.
