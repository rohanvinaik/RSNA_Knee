## ADDED Requirements

### Requirement: Every finding names its subject before it is measured
The system SHALL measure each finding only on its resolved indexed object,
relation, span or envelope, retaining the earlier facts selecting that subject.
Subject classes and predicates SHALL follow `docs/OBJECT_MODEL.md`. Production
records and dispatch SHALL NOT require anatomical names. A whole-field
measurement SHALL NOT be a finding’s predicate.

#### Scenario: A predicate is asked of a resolved subject
- **WHEN** a finding's subject is resolved for a study
- **THEN** the predicate is measured on that subject alone, in named physical
  units, and the measurement records which series supported it

#### Scenario: A whole-image measurement is proposed for a finding
- **WHEN** a measurement's scope is the field rather than an indexed structural subject
- **THEN** it is refused as a finding's predicate, because a finding is a
  statement about an object and not a pattern in a picture

### Requirement: An unresolved subject abstains and is never a negative
The system SHALL abstain on a finding whose subject is not resolved, returning a
named code that says why. An abstention SHALL remain distinct from a confident
absence at every stage, including the emitted output, and SHALL NOT be folded to
a negative.

#### Scenario: Subject not resolved
- **WHEN** the capsule is not resolved for a study
- **THEN** Effusion and Synovitis abstain with a named code, and neither is
  recorded as absent

#### Scenario: Side undetermined
- **WHEN** medial/lateral is abstained because superior or anterior could not be
  witnessed in the acquired field
- **THEN** the four side-dependent findings abstain, rather than being assigned
  to a default side

### Requirement: A predicate's bar is declared before the run that judges it
The system SHALL declare every level, radius and tolerance a predicate reads as a
recorded argument, written down before the run it judges. No bar SHALL be chosen
to separate the gold labels, to match a prevalence, or to move a score.

#### Scenario: A bar would be fitted to the labels
- **WHEN** a level is proposed because it separates positive from negative studies
- **THEN** it is refused, and the measurement is reported per class instead so the
  founder supplies the meaning

#### Scenario: Measurements reported for the founder's reading
- **WHEN** a predicate has been measured over the corpus
- **THEN** its values are reported per class of subject with examples, in plain
  prose, and the word for what they mean is left to the founder

### Requirement: The output carries twelve confidences with abstention preserved
The system SHALL emit one confidence per finding per study, ordered so that a
clear positive outranks a borderline one and a borderline outranks a confident
absence. The serialized schema SHALL mirror the competition's submission format,
and the record behind it SHALL retain each finding's subject, predicate reading,
supporting series, and abstentions with their reasons.

#### Scenario: Submission is written
- **WHEN** the twelve confidences are emitted for a study
- **THEN** the columns and identifier match `sample_submission.csv` exactly, and
  the kept record retains what was known before each value

#### Scenario: Every finding abstained
- **WHEN** no subject for a study could be resolved
- **THEN** the submission still carries a value for every column, and the kept
  record states that each was an abstention rather than a measured absence
