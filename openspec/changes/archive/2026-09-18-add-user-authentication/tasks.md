## 1. Data model

- [x] 1.1 Add `User` model (`id`, `email` unique not null, `password_hash` not null, `is_admin` bool default false, `delete_flag` bool default false) to `backend/app/models.py`
- [x] 1.2 Add `user_customers` (User↔Customer, many-to-many) association table
- [x] 1.3 Add an Alembic migration creating `users` and `user_customers`. Migration `0022_users_and_user_customers.py` run successfully (0021 → 0022); confirmed the `users` table is queryable.
- [x] 1.4 Add `jwt_secret_key: str` to `Settings` in `backend/app/config.py`. Since this field has no default (secret must not have a committed fallback), added a generated value to the gitignored `backend/.env` so `alembic/env.py` (which imports `app.config` at import time) and every script keep working.

## 2. Backend — password hashing and sessions

- [x] 2.1 Add `bcrypt` and `PyJWT` to `backend/requirements.txt`; install them
- [x] 2.2 Create `backend/app/auth.py`: `hash_password`/`verify_password` (bcrypt), `create_session_token`/`decode_session_token` (JWT, `{user_id, is_admin, exp}`, signed with `Settings.jwt_secret_key`)
- [x] 2.3 Add `get_current_user(request, db) -> User | None` reading the session cookie, verifying the JWT, and loading the `User` (returns `None` if no/invalid/expired cookie or the user no longer exists/is deleted)
- [x] 2.4 Add `require_admin(user: User | None = Depends(get_current_user)) -> User` raising 401/403 when not an admin
- [x] 2.5 Add `require_customer_access(customer_id: int, user: User | None = Depends(get_current_user), db: Session = Depends(get_db))` raising 401/403 unless the user is an admin or has that customer assigned. Also added `require_session` (any logged-in user) and `customer_scope_ids(user)` (`None` = unrestricted admin, else the assigned id list) — needed because the Customer Portal's actual read endpoints are unscoped lists with no `customer_id` path param, which task 5.2 itself anticipates ("or an admin-or-assigned check"). `require_customer_access` remains available as specified for any endpoint keyed by a single `customer_id`.

## 3. Backend — auth endpoints

- [x] 3.1 Add `POST /auth/signup` (email, password): rejects a duplicate email, creates a non-admin `User` with no customers assigned
- [x] 3.2 Add `POST /auth/login` (email, password): verifies credentials, sets an httpOnly session cookie (`SameSite=Lax`), returns the same shape as `/auth/me`
- [x] 3.3 Add `POST /auth/logout`: clears the session cookie
- [x] 3.4 Add `GET /auth/me`: returns `{id, email, is_admin, customer_ids}` for a valid session, or an explicit "not logged in" shape (not an error) for none. Returns `null` (response_model `CurrentUserOut | None`) rather than a 401 for the anonymous case, matching the delta spec's "an anonymous caller SHALL receive an indication that they are not logged in rather than an error."

## 4. Backend — Users admin endpoints

- [x] 4.1 Add `UserOut`/`UserCreate` (signup)/`UserLoginRequest`/`UserCustomersUpdate`/`UserPasswordReset` schemas to `backend/app/schemas.py`. Also added `CurrentUserOut` (for `/auth/me`) and `UserAdminUpdate` (for the admin-toggle endpoint), both implied by tasks 3.4/4.4 but not named explicitly in this task's list.
- [x] 4.2 Add `GET /users` (admin-only): list all non-deleted users with email, is_admin, and customer_ids
- [x] 4.3 Add `PATCH /users/{user_id}/customers` (admin-only): replace a user's assigned customers with the given list
- [x] 4.4 Add `PATCH /users/{user_id}/admin` (admin-only): set a user's `is_admin` flag
- [x] 4.5 Add `POST /users/{user_id}/reset-password` (admin-only): set a new password for a user directly

## 5. Backend — gate every existing endpoint

- [x] 5.1 Add `Depends(require_admin)` to every endpoint that only exists for Planning, the Admin Portal, or Employee Management (i.e. everything except the Customer Portal's own read/booking endpoints and the new `/auth/*` endpoints). Applied via `dependencies=[Depends(require_admin)]` on 57 route decorators (verified programmatically: every one of the 76 registered routes is now gated by `require_admin`, `require_session`, or is an intentionally-public `/auth/*` endpoint — none left ungated).
- [x] 5.2 Add `Depends(require_customer_access)` (or an admin-or-assigned check) to the Customer Portal's read endpoints (`/customers`, `/customer-locations`, `/contracts`, `/service-visits` as used by the Customer Portal, ad-hoc free-slots/booking), scoping results to the caller's assigned customers unless they're an admin. Used the "admin-or-assigned check" alternative the task text itself allows: added `require_session` (any logged-in user) plus `customer_scope_ids(user)` (`None` for admin = unrestricted, else the assigned id list) to `app/auth.py`, since these are unscoped list endpoints with no `customer_id` path param for the literal `require_customer_access` dependency to bind to. `GET /customers`/`/customer-locations`/`/contracts`/`/service-visits` filter their query by the scope when non-admin; `GET /contract-lines/{id}/free-slots` and `POST /contract-lines/{id}/ad-hoc-visits` check the line's own customer against the scope via a new `_check_contract_line_customer_access` helper. `POST /customers/sync` (the Customer Portal's own Tripletex-refresh trigger) is gated with plain `require_session`, unscoped, since it's a global sync with no single customer to restrict.
- [x] 5.3 Add `allow_credentials=True` to `CORSMiddleware` in `backend/app/main.py` (origins are already explicit, not `"*"`)

## 6. Backend — seed script

- [x] 6.1 Write `backend/scripts/seed_admin_user.py` (matching the `seed_tripletex_customer_contacts.py` precedent): creates `sfm_admin` with a freshly generated strong password if it doesn't already exist, and prints the password once. Docstring's run command uses `-m scripts.seed_admin_user` (not a direct file path) since the script imports `app.*`, which is only resolvable when the backend directory itself is on `sys.path` (module invocation), not when the script's own directory is (direct-path invocation) — verified by testing both.
- [x] 6.2 Run the migration, then run the seed script once against the dev database; record the password reported. Migration `0022` already applied (see 1.3). Seed script run successfully: created `sfm_admin` (id=1, is_admin=true). **Password reported to the user in this session's reply — not recorded anywhere in the repo.**

## 7. Frontend — shared plumbing

- [x] 7.1 Add `credentials: "include"` to the shared `fetch` call inside `frontend/src/api.ts` (one place, used by every exported function). No such wrapper existed yet (each function called `fetch` directly) — added a one-line `apiFetch(input, init)` wrapper right after `handleResponse` and mechanically renamed all 62 call sites from `fetch(` to `apiFetch(` (verified via `tsc -b`: zero errors, and confirmed no call site other than the wrapper's own body was skipped).
- [x] 7.2 Add `User`, `UserCreateInput` (signup), `LoginInput`, `CurrentUser` (`{id, email, is_admin, customer_ids}` or `null`), `UserCustomersInput` types to `frontend/src/types.ts`
- [x] 7.3 Add `signup`, `login`, `logout`, `getCurrentUser`, `listUsers`, `updateUserCustomers`, `updateUserAdmin`, `resetUserPassword` client functions to `frontend/src/api.ts`
- [x] 7.4 Add a small `useCurrentUser()`/`requireRole()` helper (new `frontend/src/shared/auth.ts`) that calls `getCurrentUser()` and redirects to `login.html?next=<path>` on a role mismatch, for reuse by all four app roots. Implemented as `useRequireRole(role: "admin" | "any")`, returning `{ user, loading }` so callers render nothing while the check is pending.

## 8. Frontend — login page

- [x] 8.1 Add `frontend/login.html` as a new Vite multi-page entry (mirroring `admin-portal.html`'s structure) and `frontend/src/login/LoginApp.tsx`. Also added the entry to `vite.config.ts`'s `rollupOptions.input` (not explicitly listed as a sub-task, but required for the new page to build) — verified via `npm run build`.
- [x] 8.2 Build the login form (email, password, submit → `login()`), a link to a sign-up form (email, password, confirm password → `signup()`), and redirect to `?next=` (or a sensible default per role: admin → `/index.html`, customer → `/customer-portal.html`) on success
- [x] 8.3 Show a clear error on failed login/signup (wrong credentials, duplicate email) without revealing which of email/password was wrong. Relies on the backend's already-generic error message ("Incorrect email or password") for the login case; the signup case surfaces the backend's own "Email already in use" message, which is a duplicate-email case, not a password-guessing vector.

## 9. Frontend — gate the four portals

- [x] 9.1 Add the `requireRole("admin")` check to `frontend/src/App.tsx`'s root component
- [x] 9.2 Add the `requireRole("admin")` check to `frontend/src/admin-portal/AdminPortalApp.tsx`
- [x] 9.3 Add the `requireRole("admin")` check to `frontend/src/employee-management/EmployeeManagementApp.tsx`
- [x] 9.4 Add the `requireRole("any")` check (admin or customer) to `frontend/src/customer-portal/CustomerPortalApp.tsx`; when the session is a customer user, hide the "viewing as" switcher entirely and scope all three entity views to their `customer_ids` (the backend already enforces this — the frontend change here is just not rendering the unrestricted-pick UI for a customer session). The three entity views themselves needed no changes — they already just render whatever `customers`/`customerLocations`/`contracts` arrays they're given, and the backend's `GET /customers`/`/customer-locations`/`/contracts` now return only the caller's scope for a non-admin session.
- [x] 9.5 Add a "Log out" control to each of the four portals' sidebars, calling `logout()` and redirecting to `login.html`

## 10. Frontend — Users admin view

- [x] 10.1 Create `frontend/src/admin-portal/UsersView.tsx` (list/detail, following `RegionsView.tsx`'s shape): list shows email, admin flag, assigned-customer count; detail shows/edits assigned customers (multi-select against the existing customers list) and the admin toggle, plus a "reset password" action (enter a new password, save)
- [x] 10.2 Wire `UsersView` into `AdminPortalApp.tsx`'s entity list/nav. Added `listUsers()` to `reload()`, a `users` state slot, and a "Users" entry to `ENTITY_ORDER`/`ENTITY_LABELS`. Verified via `npm run build`: full production build succeeds with zero errors.

## 11. Manual verification

- [x] 11.1 Run the migration and the seed script; confirm `sfm_admin` can log in. Migration and seed already run (see 1.3, 6.2). Found and fixed a real bug during live verification: the login form's email `<input type="email" required>` silently blocks submitting a non-email-shaped identifier like `sfm_admin` via native browser validation (the backend's `User.email` column is just a string, no email-format constraint) — changed to `type="text"` with placeholder "Email or username". Verified `sfm_admin` can now log in successfully (see 11.2 below, done alongside this).
- [x] 11.2 Sign up a new user; confirm they can log in but see no data anywhere and are redirected away from all four portals except being allowed into a logged-in (but empty) Customer Portal. Found and fixed a second real bug: `POST /auth/signup` returned the raw SQLAlchemy `User` object instead of building `UserOut`, and `UserOut.customer_ids` isn't a real column on `User` (it's derived from the `user.customers` relationship) — FastAPI's response serialization failed with a 503 `ResponseValidationError`. Fixed by returning `_user_out(user)` (the same mapper every other `/users/*` endpoint already used correctly). Verified: signed up `testcustomer@example.com`, logged in successfully, redirected to Customer Portal (non-admin default) showing "No customers.", with no "Viewing as" switcher rendered.
- [x] 11.3 As `sfm_admin`, assign a customer to the new user via the Users view; confirm that user's Customer Portal now shows exactly that customer's data, with no switcher and no way to see any other customer. Verified via the actual Users view UI: checked "Bergsameie" and saved; confirmed via `GET /users` the assignment persisted (`customer_ids: [122307350]`); logged in as the test user and confirmed their Customer Portal showed exactly that one customer, no switcher.
- [x] 11.4 As the customer user, attempt to hit a Customer Portal API endpoint for a different customer id directly; confirm it is rejected. Verified two ways: `GET /regions` (admin-only) → 403 "Admin access required"; `GET /contract-lines/119/free-slots` (a line belonging to a different customer, id 122307467) → 403 "Customer access required". Confirmed the positive case too: their own line (id 31, under the assigned customer) → 200.
- [x] 11.5 As the customer user, attempt to open Admin Portal / Employee Management / Planning directly; confirm each redirects to login. Verified: navigating to `admin-portal.html`, `employee-management.html`, and `index.html` each redirected to `login.html?next=<path>`.
- [x] 11.6 As `sfm_admin`, confirm the Customer Portal's switcher still works exactly as before (unrestricted preview of any customer). Verified: switcher lists all 151 customers for the admin session; selecting "Bergsameie" correctly scoped the Customers view to that one customer's detail page, exactly as pre-auth behavior.
- [x] 11.7 Reset the test user's password from the Users view; confirm they can log in with the new password and not the old one. Verified via the actual UI form: reset to a new password, saw "Password reset."; confirmed the old password now returns 401 and the new one returns 200.
- [x] 11.8 Toggle the test user to admin; confirm they immediately gain access to all four portals; revoke it and confirm access reverts. Verified via the Users view's "Grant admin" button: `GET /regions` (admin-only) went from 403 to 200 on the very next request with no re-login of any kind beyond the existing session. Revoked via "Revoke admin" (API): `/regions` reverted to 403 and `/customers` reverted to the scoped single-customer result.
- [x] 11.9 Log out from each portal; confirm the session cookie is cleared and protected pages redirect to login again. Verified: clicking "Log out" redirected to `login.html`; confirmed via direct API calls that `GET /auth/me` returned `null` and `GET /customers` returned 401 afterward; confirmed navigating back to `customer-portal.html` redirected to `login.html?next=...` again.

**Two real bugs found and fixed during this manual verification pass** (both now corrected in the implementation, not deferred):
1. Login form's `<input type="email">` rejected non-email identifiers like `sfm_admin` via native browser validation — changed to `type="text"`.
2. `POST /auth/signup` returned a raw `User` ORM object instead of `_user_out(user)`, causing every signup to fail with a 503 `ResponseValidationError` on the `customer_ids` field.
