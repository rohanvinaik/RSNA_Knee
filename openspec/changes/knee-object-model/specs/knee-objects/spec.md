## ADDED Requirements

### Requirement: Objects are resolved from geometry, never recognised
The system SHALL resolve each knee element from the data's own geometry and the
anatomy's invariant relations, and SHALL NOT use stored cases, learned
resemblance or an anatomical atlas during the object parse. An object's identity
SHALL follow from invariant relations — position in the patient frame, adjacency,
and relative extent — so that no element requires recall to be named.

#### Scenario: A bone is identified by its relations
- **WHEN** two large bone territories face each other across the articulation
- **THEN** the superior is the femur and the inferior the tibia, settled by the
  patient frame alone, with no stored case consulted

#### Scenario: Recall is requested during the parse
- **WHEN** any object-parse step would need a confirmed case to proceed
- **THEN** it abstains with a named code rather than consulting memory, because
  recall belongs to the diagnosis stage

### Requirement: Laterality is settled by the fibula, not by the tag
The system SHALL derive the lateral direction in patient coordinates from the
fibula's position relative to the tibia, which is invariant in both legs. It
SHALL NOT require the DICOM laterality tag, which is absent from 181 of 336
series. Where the fibula is not resolved within the acquired field, the system
SHALL abstain on medial/lateral with a named code.

#### Scenario: Fibula present
- **WHEN** a small bone territory is resolved adjacent to the tibia
- **THEN** its direction from the tibia is recorded as the lateral direction, and
  medial is its opposite

#### Scenario: Fibula out of field
- **WHEN** no fibula territory is resolved in the acquired field
- **THEN** medial/lateral is abstained with a named code, and every finding that
  depends on it is abstained rather than assigned a side

### Requirement: The residual is pulled out until nothing significant is unassigned
The system SHALL re-read the unassigned field after each round of resolved
objects, using the fact that the residual is definitionally not what has already
been resolved. Each round SHALL record what it claimed, what it left, and why.
The parse SHALL be reported complete only when every element significant to the
knee's operation is resolved or explicitly abstained on.

#### Scenario: A round claims nothing new
- **WHEN** a residual round resolves no further object
- **THEN** the remaining material is retained whole as typed residue with its
  readings, and the parse reports which elements are still unresolved

#### Scenario: Significance is asserted without warrant
- **WHEN** a round would admit an element on appearance alone
- **THEN** it is refused, since an unresolved boundary stays visible and the
  founder supplies the anatomical call

### Requirement: Every place is accounted for and nothing is deleted
The system SHALL retain every source place through the parse. Unclaimed,
disputed and abstained places SHALL remain reachable with their readings, and a
removal SHALL be a recorded decision by a reading entitled to make it, never a
deletion of source data.

#### Scenario: Two objects claim one place
- **WHEN** two resolved objects both claim a place
- **THEN** the dispute is kept with both claims, and ownership is settled by the
  ownership map rather than by order or by the stronger signal
