## ADDED Requirements

### Requirement: Connection is licensed by support, never by appearance
The system SHALL join two boundary readings into one chain only where a measured
reading licenses the join. It SHALL NOT bridge a gap because the result would
look like a plausible outline.

#### Scenario: Two readings are separated by supported material
- **WHEN** the places between two boundary readings carry a reading that licenses
  the join under the declared contract
- **THEN** they are joined into one chain, and the licensing reading is recorded
  with the join

#### Scenario: Two readings are separated by nothing measured
- **WHEN** the places between two boundary readings carry no reading at all
- **THEN** the chain is left open there, the gap is retained with its extent, and
  no segment is drawn across it

### Requirement: Movement is bounded by a measured allowance
The system SHALL allow a chain's point to move only within an allowance derived
from measurements at that point, and SHALL bound the total displacement from the
position it was traced at rather than per step. An allowance that cannot be
measured SHALL be named, never assumed.

#### Scenario: A point sits on a sharply localised reading
- **WHEN** the reading at a point localises it tightly
- **THEN** its allowance is correspondingly small, and the refinement cannot move
  it beyond that allowance however many passes run

#### Scenario: An allowance cannot be measured
- **WHEN** the quantities an allowance is derived from are not read at a point
- **THEN** that point's allowance is recorded as unmeasured with a named code,
  and the record says so rather than substituting a default

### Requirement: Closure is reported per chain and is never required
The system SHALL report, for each chain, whether it closed, and SHALL NOT treat
closure as a condition of success. An open chain is an admissible outcome and
SHALL be returned as one.

#### Scenario: A chain closes
- **WHEN** a chain's supported segments meet
- **THEN** its closure standing is recorded as closed, with the support behind
  each arc retained

#### Scenario: A chain does not close
- **WHEN** a chain's supported segments do not meet
- **THEN** it is returned open with its closure standing recorded, because
  requiring closure would oblige the operation to invent the missing boundary

### Requirement: What refinement sheds is kept
The system SHALL retain the original trace beside every refined one, together
with the places the refinement shed, the chains it left open, competing
subdivisions and any clipping. Nothing SHALL be deleted in the course of
refinement.

#### Scenario: A refinement moves a boundary
- **WHEN** a chain is refined within its allowance
- **THEN** both the original and the refined trace are returned, and the places
  the refinement no longer covers are retained as a finding

#### Scenario: The visual packet is produced
- **WHEN** the operation's picture is rendered
- **THEN** every arc is shown with what supports it, and gaps, shed places,
  open chains and clipping are visible rather than smoothed away
