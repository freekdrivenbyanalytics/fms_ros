## 1. Employee data model

- [x] 1.1 Add `first_name`, `last_name` (`String`, `NOT NULL`), `email`, `mobile_phone` (`String`, nullable), and `resco_user_id` (`String`, nullable) to `Employee` in `backend/app/models.py`
- [x] 1.2 Change `Employee.name` to a SQLAlchemy `Mapped[str]` column defined with `sa.Computed("first_name || ' ' || last_name", persisted=True)` instead of a regular column
- [x] 1.3 Add an Alembic migration that: adds `first_name`/`last_name` as nullable, backfills them by splitting each existing `name` on the first space (first word → `first_name`, remainder → `last_name`, falling back to the whole value in `first_name` with an empty `last_name` if there's no space), alters both to `NOT NULL`; adds `email`, `mobile_phone`, `resco_user_id` as nullable; drops the old `name` column and re-adds it as a generated column per 1.2

## 2. Backend schemas and endpoints

- [x] 2.1 In `backend/app/schemas.py`: remove `name` from `EmployeeCreate`/`EmployeeUpdate`, add `first_name: str`, `last_name: str`, `email: str | None = None`, `mobile_phone: str | None = None`; add the same four fields plus the (still-present, now-computed) `name` to `EmployeeOut`
- [x] 2.2 Add a `RescoSyncSummary` schema (e.g. `created: int`, `updated: int`, `skipped: int`, `failed: int`, `errors: list[str]`) and an `EmployeeRescoSyncResult` schema (e.g. `status: Literal["synced", "skipped", "failed"]`, `detail: str | None`) to `backend/app/schemas.py`
- [x] 2.3 Update `create_employee`/`update_employee` (`backend/app/main.py`) to set `first_name`/`last_name`/`email`/`mobile_phone` instead of `name`, and after commit, call the new per-employee Resco sync function, attaching its result to the response (extend `EmployeeOut` or wrap the response - your call, keep it simple) without letting a sync failure affect the employee create/update's own success
- [x] 2.4 Add `POST /employees/sync-resco` calling the manual full-sync function and returning `RescoSyncSummary`

## 3. Resco client

- [x] 3.1 Add `resco_base_url`, `resco_username`, and `resco_password` settings to `backend/app/config.py`, sourced from `backend/.env` the same way `tomtom_api_key` is (corrected mid-implementation: Resco's confirmed auth is HTTP Basic username/password, not an API-key file — see updated design.md); base URL remains a placeholder pending confirmed Resco API details
- [x] 3.2 Create `backend/app/resco.py` with a `RescoClient` class (base URL + `httpx.BasicAuth` using `resco_username`/`resco_password` from settings) and `create_user`/`update_user` methods sending first name, last name, email, and mobile phone (corrected mid-implementation after live verification: entity set is `systemuser` (not `/User`), and the email field is `internalemailaddress`; `update_user` uses OData's `systemuser('{id}')` key syntax)
- [x] 3.3 Add `sync_employee(db, employee) -> EmployeeRescoSyncResult` in `resco.py`: skip (no API call) if `email` or `mobile_phone` is missing; otherwise create or update via `RescoClient` depending on whether `resco_user_id` is already set, persisting a newly-returned Resco User ID on success
- [x] 3.4 Add `sync_all_employees(db) -> RescoSyncSummary` iterating every non-deleted employee through `sync_employee` and tallying the result counts

## 4. Frontend

- [x] 4.1 Update `Employee`, `EmployeeCreateInput`, `EmployeeUpdateInput` in `frontend/src/types.ts`: drop `name` from the input types, add `first_name`, `last_name`, `email`, `mobile_phone`; keep `name` on the read-only `Employee` type
- [x] 4.2 In `frontend/src/employee-management/EmployeesView.tsx`, replace the single `name` input in the create/edit form with `first_name`, `last_name`, `email`, and `mobile_phone` inputs (email/phone not required); keep displaying `employee.name` everywhere it's already shown (list, detail header)
- [x] 4.3 Add a "Sync to Resco" button (e.g. near the employee list, matching the existing Tripletex "Sync Products"-style pattern) calling the new manual sync endpoint and showing the returned summary (created/updated/skipped/failed counts and any error messages)
- [x] 4.4 Add the corresponding `api.ts` client functions and response types for the manual sync endpoint

## 5. Manual verification

- [x] 5.1 Run the migration against the dev database; confirm the three existing employees ("Alice Johnson", "Bram de Vries", "John Johnson") get correctly split `first_name`/`last_name`, and that `SELECT name FROM employees` still returns the original full names via the generated column (verified against 4 seeded employees incl. "Chen Wei")
- [x] 5.2 Confirm attempting to `UPDATE employees SET name = ...` directly (or via any code path) is rejected by Postgres, proving the column can no longer be set directly
- [x] 5.3 Create and edit an employee through the UI with the new fields; confirm the displayed name updates correctly when first/last name change (verified via browser: created "Verify One", edited last name to "Two", header updated to "Verify Two"; test employees soft-deleted afterward, seed data untouched)
- [x] 5.4 Trigger a manual Resco sync against the seeded employees (none of which have email/mobile phone yet) and confirm all are reported as skipped, not failed, and that the sync summary renders correctly in the UI (verified via `POST /employees/sync-resco` -> `{"created":0,"updated":0,"skipped":3,"failed":0,"errors":[]}`, and in the browser: clicking "Sync to Resco" rendered "Resco sync: 0 created, 0 updated, 3 skipped, 0 failed")
- [x] 5.5 Fill in email and mobile phone for one employee, trigger a sync, and confirm `RescoClient` builds the expected create/update request — upgraded beyond structural-only verification once the user supplied real `RESCO_USERNAME`/`RESCO_PASSWORD` credentials and the real API contract (see design.md): performed a live end-to-end round-trip against the real Resco org using Alice Johnson with real contact info (user's own email/phone, used with permission) — automatic sync on update returned `"status":"synced"` and persisted a real `resco_user_id`; manual `POST /employees/sync-resco` then correctly used that remembered ID to update (not recreate) the same record (`{"created":0,"updated":1,"skipped":2,"failed":0}`). The test record was deleted from Resco afterward and the employee's email/phone/resco_user_id reverted to blank, restoring original seed state.
