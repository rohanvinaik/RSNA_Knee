## ADDED Requirements

### Requirement: Surrounding readings actively constrain geometric interiors
The system SHALL consume the existing finite low-signal split on the native
plane, retain finite support separately, and compute an explicitly orthogonal
spacing-metric distance to low signal, missing support and a virtual frame guard.
The nearest guard cause and retained-DICOM metric error bound SHALL be recorded.
It SHALL retain every proposed territory and unseeded place without inferring
anatomical ownership or universal irrelevance from intensity.

#### Scenario: Narrow connecting passage
- **WHEN** two broad above-split interiors connect through a narrow passage
- **THEN** declared physical prominence markers and four-connected negative-distance watershed can propose separate territories, with their divides recorded as proposals

#### Scenario: Missing split or support
- **WHEN** the split is unavailable or the source is empty or nonfinite
- **THEN** the system returns distinct named readings, retains actual availability, and emits no negative anatomical assertion

### Requirement: Native border readings preserve support and ambiguity
The system SHALL enumerate all directed territory edges and their bounding causes,
sample unchanged source signal along stated physical-unit edge normals, and record
the dark interval only when a complete profile contains exactly one interval with
strictly above-split endpoints on both sides. Multiple, absent, unbounded, missing,
and frame-clipped readings SHALL remain distinct. No forced closure or ownership
transfer SHALL be made by this reading.

#### Scenario: Multiple dark intervals
- **WHEN** the acquired normal profile contains more than one dark run
- **THEN** it returns `multiple_brackets` and no unique midpoint trace

#### Scenario: Edge reaches the frame
- **WHEN** a territory edge faces outside acquisition
- **THEN** it remains recorded as `frame_clipped` rather than a closed anatomical border

### Requirement: Geometric readings compose through the production route
The optional geometric reading SHALL execute within the read-once study route,
using its returned regime split. Unavailable separately requested patient-axis
profiles SHALL NOT suppress in-plane geometric measurements. Hamilton SHALL
observe those returned records.

#### Scenario: Axial with superior profile unavailable
- **WHEN** the requested direction has no in-plane support
- **THEN** its named outcome is preserved while any available geometric interior and border reading is carried forward

### Requirement: Each stage produces source-linked color photos
Each stage SHALL save source-linked color photo series under the project's
`data/pictures/object-toolkit/` folder. The renderer SHALL observe the saved
production arrays and SHALL NOT compute a substitute segmentation.

#### Scenario: Staged visual accounting
- **WHEN** saved geometric records are rendered
- **THEN** original/red surrounding field, distance/seeds/interiors and proposed/supported native traces appear as separate color series with unresolved regions visible

### Requirement: Proofs and checkpoints bind the measured records
Receipts/checkpoints SHALL retain arrays, quantities, causes, settings, versioned
tie behavior, digests and counted work. SAME SHALL compare reference, JIT and
saved geometric records within one environment.

#### Scenario: Recompute standing after a source change
- **WHEN** an imported production source differs from the run's saved digest
- **THEN** the status reports stale even if an older reference/JIT comparison passed
