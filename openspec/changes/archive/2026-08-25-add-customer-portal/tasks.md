## 1. Backend: New List Endpoints

- [x] 1.1 Add `GET /regions` to `backend/app/main.py` returning `list[RegionOut]`, ordered by `id`.
- [x] 1.2 Add `GET /skills` returning `list[SkillOut]`, ordered by `id`.
- [x] 1.3 Add `GET /customers` returning `list[CustomerOut]`, ordered by `id`.
- [x] 1.4 Add `GET /customer-locations` returning `list[CustomerLocationOut]`, eager-loading `customer` and `region`, ordered by `id`.
- [x] 1.5 Add `GET /contracts` returning `list[ContractOut]`, eager-loading `customer_location` (with its `customer`/`region`) and `required_skills`, ordered by `id`.
- [x] 1.6 Manually verify each new endpoint via `/docs` or `curl` returns data matching the existing seed data.

## 2. Frontend: API Client

- [x] 2.1 Add `listRegions`, `listSkills`, `listCustomers`, `listCustomerLocations`, `listContracts` functions to `frontend/src/api.ts`, following the existing `listEmployees`/`listServiceVisits` pattern.

## 3. Frontend: Customer Portal Entry Point

- [x] 3.1 Add `frontend/customer-portal.html` (mirroring `index.html`) that loads `frontend/src/customer-portal/main.tsx`.
- [x] 3.2 Register `customer-portal.html` in `vite.config.ts`'s `build.rollupOptions.input` alongside the default `index.html` entry.
- [x] 3.3 Add a plain link ("Customer Portal") to `frontend/src/App.tsx`'s header pointing at `/customer-portal.html`.

## 4. Frontend: Customer Portal Shell

- [x] 4.1 Create `frontend/src/customer-portal/CustomerPortalApp.tsx`: on mount, fetch employees, customers, customer locations, contracts, regions, and skills in parallel; render a loading/error state consistent with `App.tsx`'s existing pattern.
- [x] 4.2 Add the Customer Portal's own top-level navigation (tabs or sidebar for the six entities) with no shared header/nav elements from the Planning app.
- [x] 4.3 Create shared presentational components `frontend/src/customer-portal/ListTable.tsx` and `frontend/src/customer-portal/DetailField.tsx` for consistent list/detail rendering across entity views.

## 5. Frontend: Entity Views

- [x] 5.1 `EmployeesView`: list of employees; detail view shows the employee's own fields, its Regions, and its Skills.
- [x] 5.2 `CustomersView`: list of customers; detail view shows the customer's own fields and its Customer Locations.
- [x] 5.3 `CustomerLocationsView`: list of customer locations; detail view shows its own fields, its Customer, its Region, and the Contracts at that location.
- [x] 5.4 `ContractsView`: list of contracts; detail view shows its own fields, its Customer Location, and its required Skills.
- [x] 5.5 `SkillsView`: list of skills; detail view shows the skill's own fields, the Employees who possess it, and the Contracts that require it.
- [x] 5.6 `RegionsView`: list of regions; detail view shows the region's own fields, the Employees scoped to it, and the Customer Locations in it.
- [x] 5.7 For each of the six views, implement the list→detail toggle (selecting a row shows its detail view with a "back to list" control) and confirm no create/edit/delete control exists anywhere in any view.

## 6. Verification

- [x] 6.1 Run the backend and frontend dev servers; open `/customer-portal.html` directly and confirm it renders with no Planning navigation visible.
- [x] 6.2 For each of the six entity views, verify the list shows all seed records and that opening an item shows the relationships specified in specs/customer-portal/spec.md (Customer→Locations; Location→Customer/Region/Contracts; Contract→Location/Skills; Employee→Regions/Skills; Skill→Employees/Contracts; Region→Employees/Locations).
- [x] 6.3 Confirm the existing Planning app (`/index.html`) still works unchanged, including its new "Customer Portal" link.
- [x] 6.4 Run `npm run build` and confirm both `index.html` and `customer-portal.html` are emitted in the build output.
