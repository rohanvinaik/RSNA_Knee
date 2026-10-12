Founder correction, 2026-10-12: "I don't know, that should resolve experientially, when actually
running and seeing it in action". Named decisions precede the numeric projection's declaration.

## ADDED Requirements

### Requirement: Each finding is a named decision over a named subject
The system SHALL evaluate each of the twelve findings as a decision returning a named code, over the
subject the object model gives it, and in this change that code SHALL be the one meaning abstained,
accompanied by the reason it abstained.

#### Scenario: A finding is evaluated
- **WHEN** a finding is asked of a study
- **THEN** it returns the abstention code together with a reason naming what was not resolved, and
  the reason is not the same for every finding unless the same thing was missing

#### Scenario: A subject does not exist
- **WHEN** a finding's subject is an element no stage has resolved
- **THEN** the abstention names the missing subject, rather than reporting the finding as absent

### Requirement: Abstention is never a negative
The system SHALL NOT let an abstention be recorded, serialised or read as a rejection of the
finding, and SHALL NOT admit any input from a label, a score or a previous run's outcome into the
decision.

#### Scenario: A finding abstains
- **WHEN** a finding returns its abstention
- **THEN** no record states that the finding is absent, and nothing downstream treats the abstention
  as a negative reading

#### Scenario: A label is offered to the stage
- **WHEN** a caller supplies a gold label or a previous score
- **THEN** the stage refuses it, because an input of that kind could only move a decision toward an
  answer that is already known

### Requirement: The submission's number is declared before CSV emission
The system SHALL take the value written for an abstaining finding as an argument declared in this
specification before a run emits a submission CSV, and SHALL NOT choose it by reference to a score,
a prevalence, a metric or a label. Runs that record and render named decisions SHALL NOT require a
numeric projection. The value remains undeclared while those readings are inspected.

#### Scenario: Named decisions run before a numeric projection is declared
- **WHEN** the abstention value is undeclared
- **THEN** the system can run, record and render named decisions, and refuses submission CSV
  emission rather than supplying a default number

#### Scenario: The file is written
- **WHEN** the submission file is produced
- **THEN** every row carries the declared value, and the run's record names that value and where it
  was declared

#### Scenario: A value is proposed from a measurement
- **WHEN** a value is suggested because it scores better
- **THEN** the contract refuses it, because that is choosing a bar to move a number

### Requirement: The submission is never the only record
The system SHALL write, in the same run as the submission file, a companion record holding each
finding's named code and reason, such that the submission is derivable from the record and never the
reverse.

#### Scenario: A run produces a submission
- **WHEN** the submission file is written
- **THEN** the companion record of codes and reasons is written in the same run, and a submission
  without it is refused

#### Scenario: A reader asks what the file means
- **WHEN** a consumer reads the submission's numbers
- **THEN** the companion record says every row abstained, because a number in that column cannot
  carry silence and the file alone cannot say what it is
