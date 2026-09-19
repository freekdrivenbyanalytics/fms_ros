# Spec Delta

## MODIFIED Requirements

### Requirement: Proposed schedule keeps each visit's effective schedule date
The system SHALL propose a planned start time for a service visit on any date within the run's scheduling window — not only that visit's own requested date — bounded to today or later, and SHALL NOT propose a date outside that window.

#### Scenario: Proposed time stays on the visit's requested date when not yet passed
- **WHEN** a proposed schedule assigns a service visit whose requested date has not passed, and that date can accommodate the visit within the hard constraints
- **THEN** the proposed planned start time falls on that visit's requested date, per the system's preference for a visit's own requested date over any other date in the window

#### Scenario: A visit whose requested date has passed is rescheduled to today
- **WHEN** a proposed schedule assigns a service visit whose requested date has already passed, and today can accommodate the visit within the hard constraints
- **THEN** the proposed planned start time falls on today's date

#### Scenario: Proposed date may move elsewhere within the scheduling window when necessary
- **WHEN** a proposed schedule assigns a service visit whose requested date (or, for an already-passed requested date, today) cannot accommodate it within the hard constraints
- **THEN** the proposed planned start time falls on another date within the scheduling window instead, never earlier than today and never outside the window

#### Scenario: Proposed date never precedes today or leaves the scheduling window
- **WHEN** a proposed schedule assigns any service visit
- **THEN** the proposed planned start time is never earlier than today and never falls outside the run's scheduling window

## ADDED Requirements

### Requirement: Proposed schedule prefers a visit's nominal requested date
Among schedules that satisfy the hard constraints, the system SHALL prefer placing each visit as close as possible to its own requested date, whether earlier or later within the scheduling window, with the preference weakening the further a placement drifts from that date.

#### Scenario: A visit is proposed on its requested date when feasible
- **WHEN** a proposed schedule can place a visit on its own requested date without violating any hard constraint
- **THEN** the system prefers that date over any other date in the scheduling window, all else being equal

#### Scenario: A visit drifts only as far as necessary when its requested date isn't feasible
- **WHEN** a visit's requested date has no feasible placement within the hard constraints
- **THEN** the system prefers the feasible date closest to that requested date over one further away

### Requirement: Proposed schedule discourages visiting a contract line sooner than its requested interval
Among schedules that satisfy the hard constraints, the system SHALL prefer a schedule that keeps at least the contract line's requested interval between a visit's proposed date and the *nominal* (requested) date of that contract line's immediately preceding occurrence, not the preceding occurrence's actual proposed or applied date — so a delay to one visit does not license progressively earlier drift for every occurrence after it. This preference SHALL NOT prevent a visit from being scheduled sooner than that interval when doing so is otherwise the best available placement; it only disfavors that placement relative to one respecting the interval, and SHALL be weighted more weakly than the preference for a visit's own requested date.

#### Scenario: A visit is proposed at least the requested interval after the previous occurrence's nominal date
- **WHEN** a proposed schedule can place a visit at least the contract line's requested interval after its previous occurrence's requested date, without violating any hard constraint
- **THEN** the system prefers that placement over one landing sooner than the interval

#### Scenario: A delayed previous occurrence does not license further drift
- **WHEN** a contract line's previous occurrence was itself proposed or applied later than its own requested date
- **THEN** the system still measures the requested interval from that previous occurrence's requested date, not from the date it actually happened, when preferring a placement for the following occurrence

#### Scenario: The interval preference yields to a feasible on-schedule placement
- **WHEN** a visit's own requested date has capacity available and satisfies every hard constraint, even though fewer than the requested interval's days have passed since the previous occurrence's requested date
- **THEN** the system still prefers that requested date over a later date chosen solely to satisfy the interval preference

#### Scenario: A contract line's first occurrence has no interval preference
- **WHEN** a visit is the earliest occurrence of its contract line, with no preceding occurrence
- **THEN** the interval preference does not apply to that visit
