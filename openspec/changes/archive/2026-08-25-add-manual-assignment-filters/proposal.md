## Why

The manual-assignment page's three columns (Employees, Unassigned Visits, Assigned Visits) already show region and skill tags on every card, but there's no way to narrow a long list down to just the employees or visits that matter for the region/skill combination a planner is currently working on, or to jump straight to a known customer or employee by name.

## What Changes

- Add, to each of the three columns on the manual-assignment page (Employees, Unassigned Visits, Assigned Visits), independent controls: a text search box and two multi-select filters (Region, Skill).
- Search matches on name/address: for Employees, the employee's name; for Unassigned Visits and Assigned Visits, the visit's customer name or location address.
- Each multi-select filter (Region, Skill) narrows a column's list to cards having at least one of the selected regions AND at least one of the selected skills, when both filters have selections; an empty filter selection applies no restriction on that dimension.
- Search and both filters combine (AND) within a column; each column's search/filter state is independent of the other two columns.
- No backend changes: filtering and search run client-side over the already-fetched `employees`, `visits` (unassigned/assigned split), reusing existing region/skill data already present on each item.

## Capabilities

### Modified Capabilities
- `assignments`: The "View employees and visits for assignment" requirement gains per-column search and region/skill filtering.

## Impact

- **Affected code**: `frontend/src/components/EmployeeList.tsx`, `UnassignedVisitList.tsx`, `AssignedVisitList.tsx` — add local search/filter state and controls to each; no changes to `frontend/src/api.ts` or the backend.
- **Affected systems**: Frontend only. No backend, API, or database schema changes.
- **Dependencies**: None planned — filtering is plain array filtering over data already in memory.
