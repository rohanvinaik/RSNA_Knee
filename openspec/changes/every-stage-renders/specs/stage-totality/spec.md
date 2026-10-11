## ADDED Requirements

### Requirement: One shared vocabulary names every absence
The system SHALL declare a single vocabulary of absence codes that every stage uses, and SHALL
distinguish at least three silences: a predecessor that is absent, a predecessor present but holding
nothing, and a predecessor present whose particular item was not read. A stage SHALL NOT coin a
private code for a silence the shared vocabulary already names.

#### Scenario: Two stages report the same silence
- **WHEN** two stages each find their predecessor's record absent
- **THEN** both return the same named code from the shared vocabulary

#### Scenario: An empty predecessor is not an absent one
- **WHEN** a predecessor's record is present and holds no items
- **THEN** the stage returns the code for an empty predecessor, distinct from the code for an absent
  one, and the two are never conflated in any record or picture

### Requirement: A stage is total over a missing predecessor
The system SHALL ensure every stage runs to completion when its input is absent, returning a named
code rather than raising, and SHALL NOT substitute a default value, a zero, or a neighbouring
reading for an input it did not receive.

#### Scenario: A stage runs with its input absent
- **WHEN** a stage is asked for a study whose predecessor stage returned an absence
- **THEN** it returns a record carrying the named absence and the stage completes without raising

#### Scenario: A default is never substituted
- **WHEN** a value a stage would read is not present
- **THEN** the record carries the absence by name, and no numeric default appears in its place

### Requirement: Every stage renders, including when it has nothing
The system SHALL give every stage of the route a renderer, and that renderer SHALL produce a picture
both when the stage has a record and when it has only an absence. A renderer SHALL only arrange
values the stage computed and SHALL NOT compute a value, a classification or a position of its own.

#### Scenario: A stage with nothing to show
- **WHEN** a stage returns only a named absence
- **THEN** its renderer still produces a picture, and that picture states which absence it is

#### Scenario: A renderer is asked for something the stage did not compute
- **WHEN** a picture would require a value the stage's record does not hold
- **THEN** the renderer does not compute it, and the picture shows the value as absent

### Requirement: No stage names anatomy or admits an object
The system SHALL NOT allow any stage record, code or picture to carry an anatomical name, assert
that a reading is a particular tissue, or mark a resolved element as an admitted object. A record
schema SHALL NOT contain a field whose values are anatomical names.

#### Scenario: A territory is recorded
- **WHEN** a stage records a resolved territory
- **THEN** it carries an index and its provenance only, and no field of the record names a bone, a
  tissue or a joint

#### Scenario: A picture is drawn
- **WHEN** a stage's picture is rendered
- **THEN** its labels identify elements by index and by what was measured, never by an anatomical
  name
