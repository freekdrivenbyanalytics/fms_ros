# Proposal

## Why

`add-multi-day-scheduling-window` (archived) made a visit's proposed date a genuine solver decision instead of a fixed input. At realistic data volume (~150 candidate visits, 3 employees) this measurably degrades solve quality: at `days_ahead=7` with the (now days_ahead-scaled) default time budget, the solver schedules roughly a quarter of what the old single-day behavior scheduled, and almost never spreads visits to later days at all — undermining the very capability that change shipped. Investigating the cause here (not just tuning the time budget, which that change already tried and found insufficient) found the real bottleneck: Timefold's construction heuristic phase itself doesn't finish initializing a ~150-visit problem within a practical time budget (confirmed via direct engine logs - "terminated early with step count (9)... solution may not be fully initialized" - after which local search barely runs at all), and the new `date` planning variable roughly triples the per-step candidate space, making an already-marginal construction-heuristic throughput (28 steps/30s at 1 day) worse (9 steps/30s at 7 days). A separate, definite bug compounds this: `solver/app/solve.py`'s `unimproved_spent_limit` is computed as `min(1, time_limit_seconds)`, which evaluates to exactly 1 second regardless of the configured time budget, artificially truncating whatever local search does get a chance to run.

## What Changes

- Fix the `unimproved_spent_limit` bug in `solver/app/solve.py` - a definite, low-risk correctness fix regardless of which broader strategy is chosen.
- Make `parallel` execution mode's region-disjoint splitting apply above a visit-count threshold even when the caller requests `single` mode, since splitting a run into independent per-region-group solves is the only change validated so far to bring problem size back within what the construction heuristic can actually finish (the archived change's own manual verification showed two disjoint groups of 62 and 29 visits both converging cleanly and spreading across days in ~20-40s, where the unsplit 150-visit run could not). **BREAKING**: for a run large enough to cross the threshold, `execution_mode: "single"` no longer means "solved as one problem" - this changes an explicit promise in the existing spec.
- Investigate (exploratory, results may be "no viable change found") reducing construction heuristic's per-step cost directly - a cheaper/faster Timefold construction heuristic configuration and/or narrowing the `date` candidate domain specifically during construction (before local search widens it back out) - as a complementary, longer-term improvement that also helps runs too small to benefit from region-splitting, or with only one region.

## Capabilities

### Modified Capabilities
- `route-optimization`: "A proposed schedule run's execution mode is configurable" - `single` mode's "entire run solved as one problem" guarantee no longer holds unconditionally; above a problem-size threshold the run is split into independent region groups the same way `parallel` mode already does, regardless of the requested mode.

## Impact

- `solver/app/solve.py`: `unimproved_spent_limit` fix; possible construction-heuristic configuration changes from the exploratory investigation.
- `backend/app/main.py`, `backend/app/solver_client.py`: `propose_optimization`'s `execution_mode` handling - `build_parallel_group_payloads`/`build_optimize_payload` selection needs to account for the new threshold rather than only the caller's requested mode.
- `openspec/changes/archive/2026-09-19-add-multi-day-scheduling-window/design.md`: this change's own design.md supersedes that change's Risks section for the multi-day search-space concern, with the corrected root-cause finding (construction-heuristic throughput, not local search escaping a pileup as originally guessed) and a validated fix direction.
