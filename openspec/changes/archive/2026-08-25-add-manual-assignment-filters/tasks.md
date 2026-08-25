## 1. Shared Filter Bar

- [x] 1.1 Create `frontend/src/components/ListFilterBar.tsx`: a search input plus Region and Skill multi-select controls, taking the available region/skill options and emitting the current search text and selected region/skill ids.
- [x] 1.2 Create a shared filtering helper (e.g. `frontend/src/lib/listFilter.ts`) that, given a list of items and a per-item `{ name, address?, regions, skills }` extractor plus the current search text and selected region/skill ids, returns the matching subset: case-insensitive substring match on name/address, and region/skill filters applying only when a selection is made (item matches if it has at least one selected region AND at least one selected skill, per dimension with a selection).

## 2. Wire Into Each Column

- [x] 2.1 In `EmployeeList.tsx`, derive region/skill options from the employees list, add a `ListFilterBar`, and filter the rendered employees using the shared helper (extractor: name, regions, skills — no address).
- [x] 2.2 In `UnassignedVisitList.tsx`, derive region/skill options from the unassigned visits list, add a `ListFilterBar`, and filter the rendered visits using the shared helper (extractor: customer name, location address, visit's region, visit's required skills).
- [x] 2.3 In `AssignedVisitList.tsx`, derive region/skill options from the assigned visits list, add a `ListFilterBar`, and filter the rendered visits using the shared helper (same extractor shape as 2.2, using the visit's region/skills, not the assigned employee's).
- [x] 2.4 Ensure each column's filter/search state is local to that column (no shared state across Employees / Unassigned Visits / Assigned Visits).

## 3. Empty States

- [x] 3.1 In each of the three list components, show a distinct "No matches for the current search/filters" message when the unfiltered list is non-empty but the filtered result is empty, separate from the existing "no items at all" empty state.

## 4. Verification

- [x] 4.1 Run the frontend dev server and manually verify per column: typing in search narrows to matching name/address, selecting region and/or skill filters narrows correctly (including combining search + filters), clearing search/filters restores the full list, filtering one column does not affect the other two, and a filtered-to-zero result shows the distinct "no matches" message rather than the generic empty-list message.
