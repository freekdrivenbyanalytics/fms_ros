## Context

No auth code, no `User` model, no auth libraries, and no outbound-email capability exist anywhere in this project today (confirmed live: grepped `backend/app/` for auth/login/jwt/session/password patterns — the only hits are Tripletex/Resco third-party API credentials). The frontend is 4 independent Vite multi-page apps (`index.html`, `admin-portal.html`, `employee-management.html`, `customer-portal.html`), each its own React root with no shared shell, and a single shared `frontend/src/api.ts` used by all of them. CORS is already explicit-origin (`http://localhost:5173`/`127.0.0.1:5173`, not `"*"`), just missing `allow_credentials`. `Customer.email` is nullable, Tripletex-sourced, and has no uniqueness constraint — not usable as a join key for user↔customer assignment.

## Goals / Non-Goals

**Goals:**
- A real login, shared across all four portals via one session cookie.
- Two roles only: admin (everything) and customer user (their assigned customers, Customer Portal only) — no finer-grained permissions in this change.
- Self-service sign-up with zero access by default; an admin grants real access afterward.

**Non-Goals:**
- Self-service "forgot password" via email — deferred per explicit decision; admin resets a password directly instead. No email-sending integration is added in this change.
- Any role beyond admin/customer-user (no "read-only staff," no per-feature permissions).
- OAuth/SSO, MFA, or password complexity/rotation policies — plain email+password now, explicitly meant to be replaced by "more complex/secure login routines later."
- Redesigning what the Customer Portal shows — that's `redesign-customer-portal-dashboard`. This change only adds the login gate and role-based scoping around the portal that already exists.

## Decisions

**Session = a signed JWT in an httpOnly cookie, not a server-side session table.** Stateless (no new table to prune/expire), and simplest to share across all four static-site apps served from the same origin. Alternatives considered: server-side sessions (a `sessions` table) — rejected for now as unneeded complexity given there's no logout-everywhere/session-revocation requirement yet; that can be added later without changing the login/cookie contract. The JWT carries `{user_id, is_admin, exp}`; every request re-derives the customer-assignment list from the database rather than embedding it in the token, so revoking a customer assignment takes effect on the very next request rather than waiting for the token to expire.

**New `bcrypt` + `PyJWT` dependencies, not a framework like `fastapi-users`.** The auth surface here is small (signup, login, logout, one admin-driven reset) and doesn't need a full user-management framework; two focused, widely-used libraries keep the addition auditable and match this project's existing preference for direct, explicit code (e.g. `TripletexClient`/`RescoClient` are hand-rolled, not wrapped in a generic API-client library).

**A real `user_customers` association table (user_id, customer_id), not a join against `Customer.email`.** `Customer.email` is nullable, unconstrained, and Tripletex-sourced (can change or go blank on the next sync) — using it as an identity join would silently break a user's access whenever that field changes. The association is a first-class table, managed only by admins, independent of anything Tripletex sends.

**Access control is centralized in `backend/app/auth.py`'s FastAPI dependencies (`require_admin`, `require_customer_access`), applied per-endpoint — not a single global middleware.** Endpoints already vary widely in shape (some serve Planning, some Admin Portal, some are shared); a per-endpoint dependency (added to each router function's signature, the same way `db: Session = Depends(get_db)` already is) is more consistent with the codebase's existing FastAPI-idiomatic style than a path-prefix-based middleware, and makes each endpoint's access requirement visible at its own definition rather than in a separate routing table.

**A new `login.html` 5th entry point, not per-app inline login forms.** One shared login page/component avoids writing near-identical login UI four times, and gives a single place to add "more complex/secure login routines later" (the user's own stated intent) without touching four separate apps again.

**Frontend auth-gating pattern: each app's root component calls `GET /auth/me` on mount; while pending, render nothing (or a spinner); on a role mismatch, `window.location.href` to `login.html?next=<current path>`.** This is a client-side redirect, not a hard security boundary by itself — the real enforcement is server-side (`require_admin`/`require_customer_access` on every endpoint), so a user who briefly sees an empty shell before redirect never actually receives any protected data (every API call they'd make is independently rejected).

**`credentials: "include"` is added once, in `api.ts`'s shared `fetch` wrapper (`handleResponse`'s caller), not on every individual call site.** All ~80 exported functions in `api.ts` already funnel through the same `fetch(...)` + `handleResponse(res)` shape; wrapping that shared entry point is a single, low-risk change instead of touching every call site.

## Risks / Trade-offs

**A JWT that only carries `{user_id, is_admin}` means every request does at least one extra DB round-trip (loading the user and, for customer sessions, their assigned customers) to check access.** → Accepted: this app's traffic is low-volume internal tooling, not a high-throughput public API; correctness (assignment changes apply immediately) matters more here than shaving one query.

**No password-reset email means a customer user who forgets their password must contact staff.** → Accepted per explicit decision; documented in the proposal as the deliberate v1 behavior, not an oversight.

**Making Planning/Admin Portal/Employee Management admin-only is a bigger behavior change than the user's own wording emphasized (they described customer users and a Users page, not literally locking down the staff tools).** → This is called out explicitly in the proposal's "What Changes" as a **BREAKING** change and flagged again here: a login page that doesn't actually gate anything would make "admin has access to everything" a no-op statement, so gating the staff portals is treated as the necessary, intended consequence of adding real login — not scope creep — but it's flagged clearly so it can be corrected if that's not what's wanted.

## Migration Plan

- New tables: `users` (`id`, `email` unique not null, `password_hash` not null, `is_admin` bool default false, `delete_flag` bool default false), `user_customers` (`user_id`, `customer_id`).
- New `Settings.jwt_secret_key: str` (env-configured, no default in any committed file — required at startup, matching how `Settings.tripletex_base_url` etc. already work).
- Purely additive: no existing table or column changes.
- Seed step (one-off script, not a migration): create `sfm_admin` with a freshly generated password, printed once. Must be run once, manually, after the migration, before any admin-gated portal is reachable — documented clearly in tasks.md so this isn't missed.
