## Why

None of the four portals (Planning, Admin Portal, Employee Management, Customer Portal) have any login today — anyone who can reach a URL can see and, in the staff portals, edit everything. The Customer Portal's own spec is explicit about this ("the system SHALL NOT perform any authentication or authorization based on the switcher's selection") and describes itself as a tool for a "business user" (staff), not real end-customers. Before real customers can be given portal access (the next change, `redesign-customer-portal-dashboard`, gives them a proper dashboard), there needs to be a real notion of who is logged in, what they're allowed to see, and a way for staff to grant a specific customer's data to a specific person.

## What Changes

- Add a `User` entity (email, password, admin flag) and self-service sign-up (email + password, no email verification). A newly signed-up user has no access to anything until an admin either marks them an admin or assigns them to one or more customers.
- Add a many-to-many `User` ↔ `Customer` assignment, plus a new Admin Portal "Users" view to manage it (list users, toggle admin, assign/unassign customers, reset a user's password).
- Add a shared login page (a new `login.html` entry point) with session-cookie-based login/logout, used by all four portals.
- **BREAKING**: Planning, Admin Portal, and Employee Management now require an authenticated **admin** session — every route in these three portals redirects to the login page if the visitor isn't a logged-in admin. The Customer Portal requires an authenticated session of either kind: an admin gets today's unrestricted "preview any customer" switcher, unchanged; a customer user only ever sees the customer(s) assigned to them, with no way to pick a different one.
- "Forgot password" is admin-driven for now, not a self-service email flow: an admin resets a user's password directly from the new Users view. No outbound email integration is added in this change.
- Seed one initial admin account (`sfm_admin`, a generated strong password reported once at seed time, not committed anywhere) so there's a way to log in and grant everyone else access.

## Capabilities

### New Capabilities
- `user-auth`: user accounts, sign-up, login/logout sessions, admin-driven password reset, the user↔customer assignment, and which of the four portals require which kind of session.

### Modified Capabilities
- `admin-portal`: gains a "Users" view (list/assign-customers/toggle-admin/reset-password), reachable only to an authenticated admin (all of Admin Portal now requires one).
- `customer-portal`: the existing customer switcher becomes admin-only (still an unrestricted preview, unchanged in that mode); a customer-role session has no switcher and is scoped to only their assigned customer(s) — the portal's own "no authentication" statement no longer holds.

## Impact

- `backend/app/models.py`: new `User` model (`id`, `email` unique, `password_hash`, `is_admin`, `delete_flag`); new `user_customers` association table.
- `backend/requirements.txt`: adds `bcrypt` (password hashing) and `PyJWT` (session token signing) — no libraries for this exist in the project today.
- `backend/app/auth.py` (new): password hashing, JWT issuing/verification, a `get_current_user`/`require_admin`/`require_customer_access` set of FastAPI dependencies.
- `backend/app/schemas.py`, `backend/app/main.py`: new `/auth/signup`, `/auth/login`, `/auth/logout`, `/auth/me` endpoints; new admin-only `/users`, `/users/{id}/customers`, `/users/{id}/reset-password` endpoints; every existing endpoint gains the appropriate `require_admin`/`require_customer_access` dependency per portal.
- `backend/app/config.py`: new `jwt_secret_key` setting, following the existing `Settings`/`.env` convention.
- `backend/app/main.py`: `CORSMiddleware` gains `allow_credentials=True` with an explicit origin list (already explicit, not `"*"` — compatible).
- `frontend/src/api.ts`: every request now sends `credentials: "include"` (centralized in the shared `fetch` wrapper) so the session cookie is sent cross-port in dev.
- New `frontend/login.html` + `frontend/src/login/` (a 5th Vite multi-page entry): login form, calls `/auth/login`, redirects to the right portal (or a `?next=` target) on success; a "create account" link to `/auth/signup`.
- `frontend/src/App.tsx`, `AdminPortalApp.tsx`, `EmployeeManagementApp.tsx`, `CustomerPortalApp.tsx`: each checks `/auth/me` on load and redirects to `login.html?next=...` when the session doesn't satisfy that portal's requirement.
- New `frontend/src/admin-portal/UsersView.tsx` + API client functions.
- A one-off script (matching the `backend/scripts/` precedent) seeds the `sfm_admin` account with a randomly generated password, printed once for the operator to record.
