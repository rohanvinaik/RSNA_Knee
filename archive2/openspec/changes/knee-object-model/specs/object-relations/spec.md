## ADDED Requirements

### Requirement: An interstice is constructed from facing objects, never detected
The system SHALL construct each interstice as a relation between a facing pair of
resolved objects, not as a region found by a detector, a threshold or a learned
appearance. An interstice SHALL exist exactly when its two objects are resolved
and face each other, and SHALL carry the identity of both.

#### Scenario: Both objects resolved
- **WHEN** the femur and tibia are resolved and face each other
- **THEN** their interstice exists as a relation carrying both identities, with
  no search performed over the field

#### Scenario: One object unresolved
- **WHEN** one of a facing pair is not resolved
- **THEN** the interstice is not constructed, and every finding whose subject it
  is abstains with a named code rather than reading a partial region

### Requirement: Compartments are enumerated by the bones
The system SHALL enumerate the medial, lateral, intercondylar and patellofemoral
compartments from which bone surfaces face each other, so that a compartment
cannot be missed and none is produced without its bounding surfaces. The
enumeration SHALL NOT come from a fixed anatomical template.

#### Scenario: The femur presents two condyles
- **WHEN** the femur's articular surface resolves as two condylar regions facing
  the tibia
- **THEN** exactly two tibiofemoral compartments are enumerated, with the
  intercondylar interstice between them

#### Scenario: The patella is out of the acquired field
- **WHEN** no patella is resolved in a series
- **THEN** no patellofemoral interstice is enumerated for it, and PF findings
  abstain for that series rather than defaulting to absent

### Requirement: A relation carries gap, walls, fill and contents
The system SHALL measure, for each interstice, the extent across it (gap), the
bounding surface of each object (walls), what occupies it (fill), and any
resolved object lying within it (contents). Each SHALL be recorded in named
physical units with its support, and a reading not made SHALL be silence rather
than a zero.

#### Scenario: Gap measured where walls are supported
- **WHEN** both walls are supported along a stretch of the interstice
- **THEN** the gap is recorded in millimetres along that stretch, with its support

#### Scenario: A wall is unsupported
- **WHEN** one wall is clipped by the acquired field or unresolved
- **THEN** the gap over that stretch is recorded as unread, never as zero or as a
  narrowed gap

### Requirement: Spans and the envelope are distinct from interstitial content
The system SHALL represent a span — an object attached to two bones and running
outside the interstice between them — distinctly from the contents of that
interstice. It SHALL represent the capsule as an envelope whose volume exceeds
the union of the interstices, including the suprapatellar recess.

#### Scenario: The medial span
- **WHEN** the medial collateral structure is resolved
- **THEN** it is recorded as a span of the femur and tibia, outside their
  interstice, and is not treated as interstitial content

#### Scenario: The envelope exceeds the interstices
- **WHEN** the capsule is resolved
- **THEN** its volume includes recesses lying outside every constructed
  interstice, and its extent is recorded as the envelope's own
