## Context

See proposal.md - Why. Today `create_contract_line` (backend/app/main.py) only persists the `ContractLine` row; the only code that has ever created `ServiceVisit` rows is `seed.py`'s one-off fixture loop (`for occurrence in range(2)` — a hardcoded count, ignoring `end_date` entirely). `GET /service-visits` (`list_service_visits`) returns every visit unconditionally; nothing in this codebase currently paginates or date-filters it. `solver_client.py` queries `ServiceVisit` directly via SQLAlchemy — it never calls this HTTP endpoint — so it is unaffected by anything in this change. There is no background job runner (no Celery, no cron) anywhere in this stack, which is why an open-ended contract line's occurrences can only be generated up to a fixed horizon at creation time, not indefinitely.

## Goals / Non-Goals

**Goals:**
- Generate the right set of unassigned service visits exactly once, at contract-line creation time.
- Keep the Manual Assignment board usable once visit volume grows from automatic generation, via a shared date-range control that never hides a still-unassigned backlog item.

**Non-Goals:**
- Topping up an open-ended contract line's occurrences once the one-year horizon is reached (no scheduler exists to do this; explicitly deferred per your answer).
- Regenerating, adjusting, or deleting visits when a contract line is updated (per your answer: create only).
- Any change to `seed.py`'s own fixture generation, or to the route optimizer's visit selection.
- Pagination of `GET /service-visits` — the new query params are a date filter, not a page/limit mechanism.

## Decisions

### D1: Occurrence-date computation is a small shared function, not inlined in the endpoint
Add `generate_occurrence_dates(start_date, interval_days, end_date) -> list[date]` (e.g. in a new `backend/app/visit_generation.py`, mirroring the `employee_schedule.py` precedent of a small dedicated module rather than growing `main.py` further): starting at `start_date`, step by `interval_days` while the running date is `<= end_date` (or `<= start_date + 365 days` (one year) when `end_date` is `None`). `create_contract_line` calls this, then builds one `ServiceVisit` per date. Kept separate from the endpoint so it stays trivially unit-testable and is available if a later change wants to reuse it (e.g., a future "top up" job).

### D2: one-year horizon is a plain constant, not a configurable setting
A hardcoded `OPEN_ENDED_HORIZON_DAYS = 365` constant. Alternative considered: an environment-configurable horizon. Rejected as unnecessary configuration surface for a value with no other consumer yet; trivial to promote to a setting later if needed.

### D3: `interval_days <= 0` is guarded defensively in the generation function, not newly validated on the schema
`ContractLineCreate.interval_days` has no positivity constraint today, and this change doesn't add one (out of scope — an existing gap, not something this change introduces). Because a zero-or-negative interval would otherwise infinite-loop the new date-stepping function, `generate_occurrence_dates` treats `interval_days <= 0` as "one occurrence, at start_date only," rather than looping. This is purely a defensive guard in the new code, not a behavior change to contract line validation.

### D4: The Manual Assignment date range has only an upper bound, never a lower one
Per your answer, the same control governs both the unassigned and assigned visit lists ("whole board"). Rather than invent two different lower-bound rules (unbounded for unassigned, windowed for assigned), the range is unbounded-past for both: simpler to explain, and consistent with "we don't miss any visits" without introducing an asymmetry the request never asked for. Only the upper bound moves: default `today + 7 days`, "This Week" → end of the current ISO calendar week (Monday–Sunday, so "end" is the coming Sunday, or today if today is Sunday), "4 Weeks" → `today + 28 days`. The frontend only ever needs to send `end_date` to the list endpoint for this board; `start_date` stays available on the endpoint for generality but this board never uses it.

### D5: Date filtering happens server-side via optional query params, not client-side
`GET /service-visits?start_date=...&end_date=...`, both optional, filtering on `requested_date`. Chosen over client-side filtering (the existing pattern for the Customer Portal's search/filter UI) because visit volume is now expected to grow from automatic generation (up to ~1 year × however many contract lines exist), and filtering server-side avoids shipping an ever-growing full visit list to the browser just to immediately discard most of it. Omitting both params preserves today's unfiltered behavior exactly, so no existing caller breaks.

## Risks / Trade-offs

- [Risk] An open-ended contract line's occurrences stop being generated after one year, with no mechanism in this change to extend them later. → Mitigation: explicitly called out as a known limitation in proposal.md; a future change can add a "top up" trigger (e.g., on next portal visit, or a real scheduler) without changing today's generation rule.
- [Risk] A contract line with a very short `interval_days` and a very distant `end_date` (or a long default horizon) could generate a large number of visits in one request. → Mitigation: acceptable for this iteration's expected data volumes (single-digit-to-low-double-digit contract lines in seed/dev data); worth revisiting if real usage shows otherwise.
- [Trade-off] Applying one unbounded-past rule to both visit lists (D4) means the assigned list, in principle, could show a very old assignment if one existed. In practice assignments are typically recent (created via propose/apply or manual assignment near the visit's date), so this is not expected to be a real problem, and it avoids a second, unrequested filtering rule.
