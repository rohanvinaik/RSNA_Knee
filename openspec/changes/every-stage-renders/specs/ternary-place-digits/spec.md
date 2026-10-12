## ADDED Requirements

### Requirement: A place's reading is one balanced-ternary digit against a pair of edges
The system SHALL write each place's reading in one acquisition as a single digit — below, at, or
above — against a **pair of edges**, a low and a high, with both edges belonging to the middle row.
The digit SHALL be derived from the edges supplied as arguments, and the edges SHALL NOT be literals
in the body.

#### Scenario: A reading sits between the edges
- **WHEN** a place's value lies at or between the low and the high edge
- **THEN** its digit is the middle one, and both edges are recorded with the reading

#### Scenario: A reading sits outside the edges
- **WHEN** a place's value lies strictly below the low edge, or strictly above the high edge
- **THEN** its digit is the lower or the upper one accordingly

#### Scenario: An edge was not supplied
- **WHEN** either edge is absent or not finite
- **THEN** the place's digit is not written, the reading returns a named code, and no digit is
  substituted

#### Scenario: The scalar decision names its refusal precisely
- **WHEN** `digit_code(place_value, low_edge, high_edge, population_count, minimum_population)`
  is called
- **THEN** negative counts/bars or reversed finite edges return `invalid_measurement`; otherwise
  zero population or missing/nonfinite edges return `no_edges`; a population below the supplied
  minimum returns `population_too_small`; an absent/nonfinite place returns `place_unread`
- **AND** only after these checks do finite places return `below`, `at`, or `above`, with both
  edges in `at`, including equal edges
- **AND** no population bar or edge is substituted by a body constant

### Requirement: The edges come from the series' own population
The system SHALL read the pair of edges from the distribution of the series being read, never from a
fixed level, a corpus-wide value, or any quantity derived from a label or a score.

#### Scenario: Two series of one knee
- **WHEN** two acquisitions of the same knee are read
- **THEN** each is read against its own edges, and neither is rescaled toward the other

#### Scenario: A population too small to place edges
- **WHEN** the series' population holds too few readings to place a pair of edges
- **THEN** the stage returns a named code and writes no digits for that series

### Requirement: The edge population has exact provenance
The regime SHALL hand on the exact foreground count used for its existing terciles and the
minimum population argument used by that measurement. The lenses SHALL consume these with the
existing edge pair, without reconstructing a count from a rounded share or repeating quantiles.
The current minimum of eight is inherited from `_shape_readings`, not newly chosen for a score.

#### Scenario: The edge record is incomplete
- **WHEN** no edge population count was handed on
- **THEN** the stage returns `item_unread`, records the count as absent, and writes no digits

### Requirement: Native digit maps retain their scope
The lenses SHALL write the complete native series volume in its stored slice/row/column order,
using uint8 named-code indices and int8 digits -1/0/+1, with 2 meaning no digit. Returned arrays
SHALL be read-only. The writer SHALL save the selected acquired plane from these maps using the
same slice index as the objects measurement, recording that plane scope rather than claiming
the saved picture depicts the whole volume. All seven named codes SHALL have their counts kept.

#### Scenario: A numeric map matches the scalar decision
- **WHEN** a finite or unread native value is written against a supplied pair
- **THEN** its map code matches `digit_code` exactly, including boundary ties and silences

#### Scenario: The saved native plane is drawn
- **WHEN** `workbench.render.lens_frames` receives a production receipt
- **THEN** it verifies the saved uint8 codes and int8 digits against their recorded shapes and
  content digests, and passes those arrays and recorded edge metadata through `knee.pictures.lenses`
- **AND** it draws -1, 0 and +1 in three colours and 2 as silence, without computing digits,
  counts, positions, edges, correspondence or identity; a missing plane shows its named absence

#### Scenario: The real run evidences production and consumption
- **WHEN** Chapter 1's analysis entry point writes one study's receipt
- **THEN** it keeps that study's ledger events, including `lenses.produced` and `lenses.consumed`
  counts, so a saved map alone is never offered as evidence of its wiring

### Requirement: The reading declares the correction it does not apply
The system SHALL record, with every set of digits, which spatial normalisation was applied. In this
change that value SHALL be the one meaning none, and the system SHALL NOT claim a local structural
correction it did not perform.

#### Scenario: The record is written
- **WHEN** a series' digits are recorded
- **THEN** the record carries the normalisation field, and its value says that no spatial correction
  was applied

#### Scenario: A spatially varying edge is attempted
- **WHEN** an edge would vary from place to place within one series
- **THEN** the contract refuses it, because this change's edges are per series and a varying edge
  would assert the correction the founder has not given

### Requirement: Silence is kept, and a digit is never a decision
The system SHALL leave a place's reading silent where the acquisition did not read it, SHALL keep
that silence distinct from the middle digit, and SHALL NOT let any digit decide what a place is.

#### Scenario: A place is not read in one acquisition
- **WHEN** a place has no value in an acquisition
- **THEN** its row for that acquisition is silent, and it is not written as the middle digit

#### Scenario: A conjunction across acquisitions is requested
- **WHEN** a caller asks what tissue a place holds
- **THEN** the stage does not answer, because a digit is a measurement and the conjunction that
  would name a tissue is not this stage's to make
