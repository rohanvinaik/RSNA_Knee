## ADDED Requirements

### Requirement: A profile is row counts over named banks
The system SHALL write an object's profile as counts of its places' readings, one row per value a
bank can hold, and SHALL carry every bank the design names, whether or not this build can write it.

#### Scenario: A bank this build can write
- **WHEN** a bank's quantity is held in some stage's record for the object's places
- **THEN** its rows carry the counts, and the record names the stage the quantity came from

#### Scenario: A bank this build cannot write
- **WHEN** no stage's record holds the quantity a bank would count
- **THEN** that bank appears with a named unavailable status, and **not** as rows of zero, because a
  zero count asserts that the reading was made and found nothing

### Requirement: A bank is never renamed onto a different measurement
The system SHALL write a bank only from the quantity that bank names, and SHALL NOT record an
existing measurement under the name of a bank it has not been shown to be.

#### Scenario: An existing measurement resembles a bank
- **WHEN** a measurement already in a record could plausibly fill a bank whose definition is not
  settled
- **THEN** it is written under its own name, and the unsettled bank stays unavailable, because
  writing it there would assert an equivalence nobody has made

### Requirement: A profile declares the dimensionality it was read in
The system SHALL record how many planes an object's places were drawn from, and SHALL NOT present a
reading taken on a single plane as evidence about a volume.

#### Scenario: The object came from one plane
- **WHEN** a profile is written for an object resolved on one selected plane
- **THEN** the record states that one plane was read, and no field of it claims depth, volume, or
  continuity through the stack

### Requirement: A profile asserts nothing about what the object is
The system SHALL keep a profile a record of readings and their counts, and SHALL NOT derive from it
an identity, an admission, or a resemblance judgement in this change.

#### Scenario: Two objects have similar profiles
- **WHEN** two objects' profiles hold similar counts
- **THEN** the stage records both and draws no conclusion, because comparing profiles to decide
  identity is a later stage's question and not this one's
