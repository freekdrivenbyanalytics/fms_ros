## Context

`solver/app/constraints.py` already computes driving time between every same-employee-same-day visit pair (and the home-to-first-visit leg) as a **soft** penalty, using a `DrivingTimeFact` join when one covers the leg and a Haversine-based fallback otherwise (see `pair_kind_joiners`, `employee_leg_kind_joiners`, `_earlier_location_id`/`_later_location_id`, `_pair_fallback_minutes`, `_employee_fallback_minutes`). The only **hard** timing constraint today is "Overlapping proposed visits" / "Overlapping existing assignment", which checks `Joiners.overlapping(start_minutes, end_minutes)` and says nothing about the gap between non-overlapping visits. See proposal.md for why that's a bug.

## Goals / Non-Goals

**Goals:**
- Make "not enough time to drive between two same-day visits" a hard infeasibility, using the same driving-time lookups (matrix + fallback) already wired up for the soft constraints.
- Cover all three leg shapes already scored softly: proposed↔proposed, proposed↔existing, and employee-home↔first-visit.

**Non-Goals:**
- Sequencing/routing (deciding visit order beyond pairwise gap checking) — out of scope, same as today's soft constraints.
- Changing the soft travel-time-minimization objective itself.

## Decisions

**Directional pairing instead of symmetric earlier/later helpers.** The existing soft constraints use `_earlier_location_id`/`_later_location_id` to pick which location is the join key regardless of which visit comes first, because for a symmetric sum-of-driving-time score it doesn't matter which visit is "first". The new hard constraint is direction-sensitive (the gap is `later.start - earlier.end`, not the reverse), so each new constraint filters on `a.start_minutes < b.start_minutes` (or joins against the already-ordered `EmployeeDaySchedule`/existing-assignment pairing) before computing the gap, then reuses the same `_earlier_location_id`/`_later_location_id` joiners to find the matching `DrivingTimeFact` for that ordered pair.

**Flat `ONE_HARD` penalty per violation, not shortfall-weighted.** The existing "Overlapping proposed visits" hard constraint also penalizes with a flat `HardMediumSoftScore.ONE_HARD` rather than weighting by the size of the overlap. The new gap constraints follow the same pattern for consistency, and because Timefold's local search in this codebase already converges on the existing flat-hard constraints without needing a magnitude-based gradient.

**Reuse the existing fallback structure (matched/`if_not_exists` pairs).** Each new hard constraint is added as two constraints — one joined to `DrivingTimeFact` (real matrix entry), one `if_not_exists` using the Haversine fallback — mirroring exactly how "Travel time between proposed visits" and "Travel time between proposed visits (fallback estimate)" are split today. This keeps the fallback semantics (distance-estimate when no matrix entry exists) identical between the soft-score and new hard-feasibility constraints.

**New hard constraints added (four, mirroring the existing soft-constraint split):**
1. Proposed↔proposed: `later.start_minutes - earlier.end_minutes < drivingTime` → hard penalty (matrix entry).
2. Proposed↔proposed fallback: same, using `_pair_fallback_minutes` when no matrix entry exists.
3. Proposed↔existing: same shape, ordered against `ExistingAssignmentFact.start_minutes`/`end_minutes`.
4. Proposed↔existing fallback.
5. Employee home→first-visit: `visit.start_minutes - schedule.start_minutes < drivingTime` → hard penalty (matrix entry), joined through `EmployeeDaySchedule` the same way "Outside working hours" already is.
6. Employee home→first-visit fallback: using `_employee_fallback_minutes`.

(Six total, not four — proposed↔existing needed both directions since an existing assignment can fall before or after a proposed visit; existing "Travel time to existing assignment" already handles this by joining without an order filter, since the soft score doesn't care about direction. The hard constraint reintroduces the earlier/later ordering the same way the proposed↔proposed one does.)

## Risks / Trade-offs

**Previously "feasible" tightly-packed schedules become infeasible, so more visits may go unscheduled.** This is the intended effect of the fix — a schedule with no drive time between visits was never actually executable — but it means demo/seed data or existing tests that assumed back-to-back placements will need their fixtures adjusted (e.g. `openspec/changes/archive/.../reset demo data` scenarios) if they hard-code zero-gap visit pairs. → Mitigation: covered by tasks.md; check solver test fixtures for zero-gap pairs when implementing.

**Flat hard penalty gives the solver a smaller gradient per violation** than a shortfall-weighted penalty would (a 1-minute shortfall costs the same one hard point as a 60-minute shortfall). → Mitigation: same trade-off already accepted for the overlap constraint in this codebase; revisit only if solver quality regresses in practice.
