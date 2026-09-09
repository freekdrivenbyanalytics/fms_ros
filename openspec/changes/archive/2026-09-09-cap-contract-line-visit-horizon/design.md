## Context

`generate_occurrence_dates` (`backend/app/visit_generation.py`) is pure: given `start_date`, `interval_days`, `end_date`, it returns the full list of occurrence dates, defaulting the horizon to `OPEN_ENDED_HORIZON_DAYS` (365) after `start_date` when `end_date` is `None`. It's called once, at contract-line creation (`backend/app/main.py::create_contract_line`), which inserts one `ServiceVisit` row per date. There is no scheduler or background-job infrastructure in this codebase (no Celery/APScheduler/cron integration) — the one existing "runs later, on demand" pattern is the driving-times computation: a manual button in the Admin Portal hitting a synchronous POST endpoint. See proposal.md - Why for the row-count motivation.

## Goals / Non-Goals

**Goals:**
- Cap newly generated occurrences to 90 days ahead for open-ended lines.
- Provide a way to keep an open-ended line's visits flowing past that 90-day window without manual per-line intervention.
- Follow the existing on-demand/manual-trigger architectural pattern rather than introducing new infrastructure.

**Non-Goals:**
- Adding a scheduler/cron dependency to the backend. The extend-visits endpoint is designed to be safe to call from an *external* scheduler (OS Task Scheduler, cron, a hosting platform's scheduled job) if the user wants full automation, but wiring that up is an operational choice outside this change.
- Cleaning up the ~97,000 already-generated visits that exceed the new 90-day horizon under the old 365-day rule. They're valid, already-generated data (some already assigned); deleting future-dated-but-unassigned visits is a separate, riskier data decision the user should make explicitly, not something this change does implicitly as a side effect of lowering the constant.
- Changing behavior for bounded (`end_date` set) contract lines at all.

## Decisions

- **90-day horizon, matching the Admin Portal's bounded display window.** The `speed-up-admin-portal-loading` change bounds what's shown/fetched to 30 days past / 90 days future. Using the same 90-day figure here means that once both changes ship, "all of a line's generated visits" and "what's visible in the Admin Portal" converge for lines kept topped up — no visits are silently generated-but-invisible.
- **Bulk extend-all endpoint, not per-line.** A per-contract-line button would require an admin to remember and click it for every open-ended line individually. A single bulk operation (`POST /contract-lines/extend-visits`) that walks every open-ended line and tops up whichever have fallen behind is both simpler to trigger and safe to call repeatedly (idempotent no-op for lines already at the horizon), so there's no cost to calling it often "just in case."
- **Idempotency via "furthest existing occurrence," not a stored watermark.** Extending a line queries `MAX(requested_date)` for that line's existing service visits (falling back to the line's `start_date` if it has none, which shouldn't happen post-creation) and generates only dates after that, up to the new horizon. This needs no new column or migration — the existing `service_visits` table is already the source of truth for "what's been generated."
- **Synchronous request/response, matching driving-times.** With 12 contract lines today, extending all of them is cheap. If contract-line count grows enough for this to matter, the existing driving-times computation would hit the same scaling wall first (it's O(locations²) against an external API per region) — revisit both together if that happens, rather than over-building this one now.

## Risks / Trade-offs

- [Nobody clicks "Extend recurring visits" for months] → An open-ended line's visits simply stop generating past its last topped-up date until someone does. This is a strict improvement over today (where the same failure mode exists implicitly once the fixed 365-day window from creation passes) and is mitigated by the button being on the same view admins already use for contract-line management; wiring an external scheduler to hit the endpoint removes the risk entirely for a user who wants that.
- [Lowering `OPEN_ENDED_HORIZON_DAYS` doesn't retroactively shrink the ~97k already-generated visits] → Intentional (see Non-Goals). Flagged here so it isn't mistaken for a bug when the visit count doesn't drop after this change ships.
