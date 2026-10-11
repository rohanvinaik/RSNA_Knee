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

### Requirement: The edges come from the series' own population
The system SHALL read the pair of edges from the distribution of the series being read, never from a
fixed level, a corpus-wide value, or any quantity derived from a label or a score.

#### Scenario: Two series of one knee
- **WHEN** two acquisitions of the same knee are read
- **THEN** each is read against its own edges, and neither is rescaled toward the other

#### Scenario: A population too small to place edges
- **WHEN** the series' population holds too few readings to place a pair of edges
- **THEN** the stage returns a named code and writes no digits for that series

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
