## 1. Backend endpoint

- [x] 1.1 Add a function (e.g. in `backend/app/reset_demo_data.py` or a new small module) that: queries the minimum `ServiceVisit.requested_date` across all service visits, computes `offset_days = max(0, (today - earliest).days)`, and if `offset_days > 0` updates every `ServiceVisit.requested_date` by adding `offset_days`
- [x] 1.2 In the same function, delete every `Assignment` row (pinned or not) and set every service visit whose status was `ASSIGNED` back to `UNASSIGNED`, in the same database transaction as the date shift
- [x] 1.3 Add `POST /demo/refresh-schedule` to `backend/app/main.py` calling this function and returning a small summary (e.g. `{"days_shifted": int, "visits_unassigned": int}`)
- [x] 1.4 Add the corresponding Pydantic response schema to `backend/app/schemas.py`

## 2. Frontend

- [x] 2.1 Add an `api.ts` client function (e.g. `refreshDemoSchedule()`) and matching response type in `frontend/src/types.ts`
- [x] 2.2 Add a "Demo" entry to the Admin Portal nav (`frontend/src/admin-portal/AdminPortalApp.tsx`) and a small view component with a button that triggers the refresh after an inline confirmation step (not a native browser `confirm()` dialog — follow the existing toggle/expand-to-confirm patterns already used elsewhere in the Admin Portal), then shows the returned summary and reloads the portal's data

## 3. Manual verification

- [x] 3.1 Start the backend + frontend locally against the current demo dataset (which has visits dated in the past), trigger the refresh, and confirm the earliest service visit's requested date becomes today and every other visit's date shifted by the same number of days (spacing preserved) - verified against the live dev stack: earliest visit was 2026-09-10 (today was 2026-09-11), `POST /demo/refresh-schedule` returned `{"days_shifted":1,"visits_unassigned":42}`, and a direct DB check confirmed both `MIN(requested_date)` and `MAX(requested_date)` shifted by exactly 1 day (2026-09-10→2026-09-11, 2026-12-09→2026-12-10), preserving the range/spacing
- [x] 3.2 Confirm every assignment (including any pinned one) is gone afterward and the previously-assigned visits show as unassigned in the Manual Assignment view - `assignments` table had 0 rows and all 1050 service visits read `status='unassigned'` after the refresh (DB-verified); also exercised the full UI flow (Admin Portal → Demo tab → Refresh Demo Schedule → inline confirm → "Yes, refresh") and got the matching summary message
- [x] 3.3 Trigger the refresh a second time immediately after (nothing now in the past) and confirm no visit dates change the second time - second `POST /demo/refresh-schedule` returned `{"days_shifted":0,"visits_unassigned":0}`, and `MIN`/`MAX(requested_date)` were unchanged
