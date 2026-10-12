Declared 2026-10-12 from `docs/HANDOFF_WIRING.md` and its Codex reading, under the founder's
instruction the same day: "I need the thing to actually work and be wired right, after which I can
actually do the REAL work." Every requirement here is about COMPOSITION: a value computed once
reaching the stage that reads it, with the ledger as the evidence and never the artifact.

## ADDED Requirements

### Requirement: The route runs in dependency order and the conversation precedes its readers
The system SHALL measure every series of a study, then converse between same-orientation
acquisitions, then partition, relate, bundle, predicate and project — so that the conversation's
refined parse is an input to the stages that read a parse, never a record computed after them.

#### Scenario: The conversation is read by ownership
- **WHEN** a study runs with the conversation requested
- **THEN** the ledger records `conversation.produced` before any `ownership.produced`, and
  ownership records `conversation.consumed_by.ownership`

#### Scenario: The conversation is not requested
- **WHEN** a study runs without the conversation
- **THEN** every series carries no conversation reading, ownership seats only the solitary parse,
  and the route still completes with every stage present

### Requirement: Ownership seats one member per parse and keeps their disagreement
The system SHALL read ownership once per parse available — the solitary parse from the interiors,
and where the conversation read the series, its concurrent and conditional subdivisions — each with
the same partition reading, and SHALL retain the places where the solitary and concurrent claims
differ as a measurement. No member SHALL be a fallback for another and no field SHALL name a winner.

#### Scenario: The conversation could not read the series
- **WHEN** the conversation returns `recipient_unavailable` for a series
- **THEN** ownership seats exactly one member, the solitary parse, and names why the others are absent

#### Scenario: Two parses disagree
- **WHEN** the solitary and concurrent claims differ at some places
- **THEN** both readings are retained unchanged and the disagreement mask and its count are recorded

### Requirement: Relations carries its pairings and names the construction it owes
The system SHALL have the relations stage read the sample-supported pairings itself and carry them
in its record, SHALL keep its code `construction_absent` while no interstice extent is constructed,
and SHALL declare the record shape (`Interstice`: a structural kind and two indexed extents) that
the construction fills so the predicates stage reads one shape before and after it lands.

#### Scenario: Pairs are retained inside the relations record
- **WHEN** a series resolves interiors with bracketed profiles
- **THEN** `relations.pairings` holds the same pairing reading the pairing unit returns for that
  series, and `relations.interstices` is empty with `code` `construction_absent`

#### Scenario: A malformed predecessor
- **WHEN** relations is handed something that is not an interiors reading
- **THEN** it returns `construction_absent`, attempts no pairing, says so, and never raises

### Requirement: Predicates read per-finding construction facts from relations
The system SHALL give each finding the structural KIND of construction its subject requires, and
SHALL read the study's constructions of that kind from the relations records: none constructed →
`subject_unconstructed`; exactly one → its two indexed extents are the subjects; several → the
finding abstains with `dispatch_undeclared`, because the rule choosing among them is the founder's.
No construction fact SHALL be hardcoded, and no global construction flag SHALL supply a subject.

#### Scenario: Nothing is constructed
- **WHEN** every relations record holds no interstice
- **THEN** every construction-satisfied finding returns `subject_unconstructed`, read from the records

#### Scenario: Several constructions of one kind
- **WHEN** two constructions of the required kind exist for a study
- **THEN** the finding returns `dispatch_undeclared` and names no subject

### Requirement: A consumed event is recorded by the consumer
The system SHALL record `<producer>.consumed_by.<consumer>` inside the consuming stage at the point
it reads the producer's record, and SHALL NOT record consumption from the route after production.
Every `<stage>.produced` event of a full run SHALL have at least one consumer event.

#### Scenario: A stage produces a record nothing reads
- **WHEN** a run's ledger holds `<stage>.produced` and no `<stage>.consumed_by.<other>`
- **THEN** the composition test fails naming that stage

### Requirement: Every stage is named in the attendance roster
The system SHALL return, per study, a roster naming every route stage with the code that stage
itself returned, so a run's coverage is read as a population rather than a high-water mark.

#### Scenario: A stage ran and abstained
- **WHEN** a stage returns a named silence for a study
- **THEN** the roster carries that stage with that code, and the stage is not reported as absent

### Requirement: The output stage refuses a CSV without a declared projection and writes the companion record
The system SHALL map each finding's index to the competition's column by a declared table that is a
bijection onto the competition's labels, SHALL write the companion record of codes and reasons on
every run, and SHALL refuse submission rows with a named code while the numeric projection is
undeclared.

#### Scenario: The projection is undeclared
- **WHEN** output runs with no declared projection
- **THEN** its code is `projection_undeclared`, the companion record is complete, and no row is written

#### Scenario: The correspondence is checked
- **WHEN** the index-to-column table is compared with the competition's labels
- **THEN** every label appears exactly once and every index maps to exactly one label
