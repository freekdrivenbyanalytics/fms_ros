## Context

Three independent pieces of new configurability, of very different weight:

- **Scheduling window** (`days_ahead`): purely a backend filtering concern. `solver_client.py`'s `_is_within_scheduling_window` hardcodes `today` and `today + 1 day`; `build_optimize_payload` calls it while building candidate visits. Neither the solver nor its domain model know about "the window" at all — the backend simply never includes an out-of-window visit in the payload.
- **Solver time budget** (`time_limit_seconds`): already a per-request field on `solver/app/schemas.py`'s `OptimizeRequest` (`solve.py` already reads `request.time_limit_seconds` with a fallback). The backend just needs to stop always overriding it with `settings.solver_time_limit_seconds` and instead pass through a caller-supplied value.
- **Priority/urgency-weighted unscheduled-visit penalty**: the one piece with real design content. Today's "Unscheduled visit" constraint (`solver/app/constraints.py`) is `penalize(HardMediumSoftScore.ONE_MEDIUM)` with no weight function — every unscheduled visit costs exactly 1 medium point, so the solver has no way to prefer dropping a low-priority visit over a high-priority one, or a distant one over an urgent one.

Because the first two are simple per-request values (not something the constraint logic needs to know), this design focuses on the third.

## Goals / Non-Goals

**Goals:**
- Make priority strictly dominant over urgency, and both dominant over nothing else changing: a schedule that drops any single priority-1 visit must always score worse (on the medium band) than one that drops any combination of priority-2/3 visits instead, regardless of how many.
- Keep this entirely within the existing medium band — it must not change the existing hard-feasibility or soft-travel-time behavior, and must not weaken "prefer scheduling more visits than fewer" as a baseline.
- Keep priority and urgency as plain per-visit data the constraint reads, not new solver-run configuration — so no change to how `SolverConfig`/`define_constraints` are wired up.

**Non-Goals:**
- A fourth score band, or per-priority score bands (`HardMediumSoftScore` has exactly three levels; introducing a new one would mean swapping the whole score type and touching every existing constraint's return type).
- Sequencing or reordering already-scheduled visits by priority — priority only affects which visits get left out, not the order or timing of ones that are scheduled.

## Decisions

**Priority is a plain contract-line field (1/2/3), not an enum, and a visit's priority is read through its contract line rather than duplicated.** This matches the existing pattern for duration and required products (see `service-visits`' "duration and product requirements are read through the contract line"). Using small integers directly (rather than a `Priority` enum with names) keeps the weight arithmetic below trivial — "1 = high" reads naturally and sorts the same direction as "closer to zero is more important," matching how `days_until_due` also sorts smaller-is-more-urgent.

**The medium penalty is a single weighted constraint, not separate constraints per priority tier.** Timefold's `penalize(ONE_MEDIUM, weight_fn)` takes one integer per match; encoding priority and urgency as one combined integer avoids needing three (or nine) near-duplicate constraint definitions.

**The weight uses nested per-tier scaling, not a flat multiplier — a flat one cannot work.** The first version of this design used `weight(visit) = (4 - priority) * PRIORITY_SCALE + urgency` with a large fixed `PRIORITY_SCALE`. That's broken: Timefold *sums* constraint match weights across every matching entity into one score component, it does not take a max. A lower tier's own per-visit weight is already the same order of magnitude as the gap to the tier above it, so summing just 2-3 lower-tier visits overtakes one higher-tier visit — regardless of how large a *fixed* (or even visit-count-scaled-linearly) `PRIORITY_SCALE` is. This was caught while writing the constraint tests (a 3-visit case broke the intended dominance) and is not fixable by tuning the constant.

The corrected weight uses nested scaling, where each tier's constant is sized to exceed the maximum possible *sum* of every visit at the tier(s) below it, using `n` = this run's total visit count (an absolute upper bound on how many visits could ever be simultaneously unscheduled in one run) and `U` = `URGENCY_CAP + 1` (a strict upper bound on the urgency term):

```
urgency = URGENCY_CAP - visit.days_until_due          # in [1, URGENCY_CAP]
tier_2  = n * U + 1                                     # exceeds n visits' worth of priority 3's max weight
tier_1  = n * (tier_2 + U) + 1                           # exceeds n visits' worth of priority 2's max weight

weight(priority=3) = urgency
weight(priority=2) = tier_2 + urgency
weight(priority=1) = tier_1 + urgency
```

This holds regardless of how many lower-priority visits are unscheduled at once (verified with a 201-visit test: one priority-1 visit outweighs 200 priority-3 visits combined), because each tier's constant is derived *from n*, not a constant guessed in advance. `n` travels as a plain field on every `VisitAssignment` (`total_visit_count`, set once in `solve.py`'s `_build_schedule` from `len(request.visits)`) rather than as solver-run configuration, keeping with this design's goal of priority/urgency being per-visit data. Alternative considered: a tuple/lexicographic score type — rejected because it would require replacing `HardMediumSoftScore` everywhere, a much larger change for the same practical effect.

**`days_until_due` is precomputed by the backend, not derived in the solver.** The backend already computes each visit's `effective_schedule_date`; `days_until_due = (effective_schedule_date(visit) - date.today()).days` is one line in `_visit_payload`. The alternative — giving the solver a `today` fact and having constraints do the date arithmetic — would add a new fact type and joins for no benefit, since the backend already owns all date logic today (see `effective_schedule_date`, `_is_within_scheduling_window`).

**`days_ahead` is capped at 14.** This bounds solver problem size (consistent with why the window was limited to 2 days in the first place — see the archived `limit-solver-scheduling-window` change) and gives `URGENCY_CAP` a small, fixed value that the nested weight formula's tier constants are built from.

**`ContractLine.priority` is `NOT NULL` with a server-side default of `2`.** Matches the existing pattern for `delete_flag` and `pinned` — every existing row gets a value via the migration's `server_default` without a backfill step, and the column can never be null in application code.

## Risks / Trade-offs

**A large `days_ahead` value increases solver problem size and may push runs toward the (now also configurable) time budget.** This is an accepted trade-off inherent to the feature — the planner explicitly asked for more scope, and the 14-day cap plus configurable time budget together bound the worst case. → No further mitigation planned for v1.

**The nested weight formula's tier constants grow with `n` (this run's visit count), so very large `n` means very large integers.** For `n` in the thousands the constants stay comfortably within a 64-bit integer range (Timefold's score components are backed by longs), so this isn't a practical concern at any scale this system is likely to reach; it would only matter if `n` grew into the billions. → No mitigation planned; revisit only if `n` ever approaches that order of magnitude.
