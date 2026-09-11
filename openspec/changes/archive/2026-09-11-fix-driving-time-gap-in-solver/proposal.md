## Why

The solver only prevents proposed visits for the same employee from time-overlapping; it does not require a gap between the end of one visit and the start of the next large enough to actually drive between their locations. Driving time is only scored as a soft preference, so the solver can (and does) propose back-to-back visits at different locations with zero minutes to travel between them, producing schedules a planner cannot actually execute.

## What Changes

- Add a hard constraint: for two same-employee-same-day visits (proposed-proposed and proposed-existing pairs), the gap between the earlier visit's end time and the later visit's start time must be at least the driving time between their locations (looked up from the region driving-time matrix, falling back to the existing distance-based estimate when no matrix entry covers the pair).
- Add the same hard constraint for an employee's home-to-first-visit leg: the first visit of the day must start no earlier than the employee's day-start plus the home-to-visit driving time.
- Keep the existing soft "minimize total travel time" constraints as-is; the new constraints only add a hard feasibility floor, they don't change what's being minimized.

## Capabilities

### Modified Capabilities
- `route-optimization`: the "Proposed schedule respects hard constraints" requirement gains a driving-time-gap rule, and a new hard-constraint requirement covers the home-to-first-visit leg.

## Impact

- `solver/app/constraints.py`: new hard constraints for inter-visit and home-to-visit driving-time gaps, reusing the existing `DrivingTimeFact` lookups and Haversine fallback already used by the soft travel-time constraints.
- No API or schema changes; `OptimizeRequest`/`OptimizeResponse` payloads are unchanged.
- Proposed schedules may leave more visits unscheduled than before in tightly packed cases, since some previously "feasible" back-to-back placements no longer satisfy the hard constraints.
