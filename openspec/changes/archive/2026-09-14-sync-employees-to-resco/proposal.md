## Why

Technicians need to exist as Users in Resco (the field service mobile CRM at `https://sfm.rescocrm.com`) so they can log into the Resco mobile app, but there's no connection between fms_ros's employee records and Resco today. Resco's User entity requires first name, last name, email, and mobile phone — none of which fms_ros currently collects (`Employee` has only a single free-text `name`, no email or phone at all) — so there's nothing to sync until fms_ros collects that data itself first.

## What Changes

- Add `first_name`, `last_name`, `email`, and `mobile_phone` to the employee data model, collected via the Employee Management UI's create/edit form.
- `Employee.name` becomes a value derived from `first_name` + `last_name` rather than independently editable — the create/edit form no longer accepts a separate `name` input, and the database computes it automatically so no code path can set it out of step with first/last name.
- Add a new Resco integration: sync (create or update) each employee as a User in Resco, pushing first name, last name, email, and mobile phone. An employee missing email or mobile phone (both required by Resco) is skipped and reported rather than failing the whole sync.
- The sync runs two ways: automatically (best-effort, non-blocking) whenever an employee is created or updated, and on demand via a manual "Sync to Resco" action for the full employee list — matching the existing Tripletex sync UI pattern.
- fms_ros remembers each employee's Resco User ID after its first successful sync, so later syncs update the same Resco record instead of creating duplicates.

## Capabilities

### New Capabilities
- `resco-integration`: pushes employee data to Resco as Users, keyed by a remembered Resco User ID, skipping and reporting employees missing Resco's required fields.

### Modified Capabilities
- `employees`: the employee data model gains `first_name`, `last_name`, `email`, and `mobile_phone`; `name` becomes derived from first/last name instead of directly settable.

## Impact

- `backend/app/models.py` + a new Alembic migration: `Employee` gains `first_name`, `last_name` (`NOT NULL`, backfilled by splitting existing `name` values), `email`, `mobile_phone` (both nullable — not every existing employee has this data yet), `resco_user_id` (nullable). `name` is dropped as a regular column and re-added as a Postgres generated column (`GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED`), so it can never be set directly by application code.
- `backend/app/schemas.py`: `EmployeeCreate`/`EmployeeUpdate` drop `name`, add `first_name`/`last_name`/`email`/`mobile_phone` (email/phone optional); `EmployeeOut` gains the same fields (including the still-present, now-computed `name`).
- `backend/app/main.py`: `create_employee`/`update_employee` stop setting `name`; both call the Resco sync for that one employee after commit, best-effort (a Resco failure doesn't fail the request). New endpoint to manually trigger a full sync.
- New `backend/app/resco.py`: a Resco API client (auth, base URL from settings/`.local/` credential file, mirroring `tripletex.py`'s pattern) and the sync function itself (create-or-update per employee, skip-and-report on missing required fields or API failure).
- `backend/app/config.py`: Resco base URL / auth settings.
- `frontend/src/employee-management/EmployeesView.tsx`: replace the `name` input with `first_name`/`last_name`/`email`/`mobile_phone` fields; add a "Sync to Resco" button and per-employee sync status/result display.
- `frontend/src/api.ts`, `frontend/src/types.ts`: updated employee request/response shapes; new Resco sync endpoint client.

**Resolved (design.md elaborates):** the Resco API is confirmed as its OData v4 service at `https://sfm.rescocrm.com/odata/v4/sfm`, authenticating via HTTP Basic auth (username/password, stored in `backend/.env` alongside `TOMTOM_API_KEY`), with the User entity as `systemuser` (fields `firstname`/`lastname`/`internalemailaddress`/`mobilephone`). Verified with a live create/update/delete round-trip during implementation.
