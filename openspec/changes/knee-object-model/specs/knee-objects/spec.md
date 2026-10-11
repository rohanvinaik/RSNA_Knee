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

### Requirement: The frame fixes the left–right axis; a witness fixes its lateral sign
The system SHALL derive the patient left–right AXIS from the LPS frame's
right-handedness, with superior witnessed by the direction the femoral shaft
leaves the condyles and anterior by where the patella sits. It SHALL NOT treat
that axis as the anatomical lateral direction: `S × A` is patient-left, which is
lateral for a left knee and **medial for a right one**, so the SIGN requires a
witness that is lateral in both legs. The system SHALL take that sign from the
fibula, with the fabella, the popliteus groove and the condylar asymmetries
available for concurrence, and SHALL NOT require the DICOM laterality tag, which
is absent from 181 of 336 series.

#### Scenario: A laterality witness is resolved
- **WHEN** the fibula is resolved beside the tibia
- **THEN** its direction along the frame's left–right axis is recorded as lateral,
  medial is its opposite, and the knee's side follows from it

#### Scenario: No laterality witness resolves
- **WHEN** neither the fibula nor a secondary witness is resolved in the acquired
  field, which is common since the fibular head sits 1–2 cm below the lateral
  plateau
- **THEN** medial/lateral is abstained with a named code, because the frame fixes
  the axis and never its anatomical sign, and every side-dependent finding
  abstains rather than being assigned a side

#### Scenario: Two laterality witnesses disagree
- **WHEN** the fibula and a secondary witness place lateral at opposite ends of
  the axis
- **THEN** both readings are kept and the side is abstained, rather than resolved
  in favour of either

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
