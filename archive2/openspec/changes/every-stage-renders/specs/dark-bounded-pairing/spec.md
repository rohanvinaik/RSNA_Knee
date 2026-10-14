## ADDED Requirements

### Requirement: A bracketed profile retains categorical support at both sides
The system SHALL read all positive-weight native bilinear contributors at the existing sample
positions immediately flanking one bracketed dark run. It SHALL retain those labels and coordinates,
and SHALL NOT average labels, choose a nearest label, or add a threshold or radius.
Positive weight SHALL mean the existing sampler's float64 product is greater than zero, with the
same arithmetic order; this is sampled machine support, not an assertion about exact real weights.

#### Scenario: Contributors disagree
- **WHEN** a side has contributors belonging to different positive extents
- **THEN** the construction records a named ambiguity and assigns no far-side extent

#### Scenario: A categorical average invents an extent
- **WHEN** equally weighted contributors have labels 1 and 3
- **THEN** the record retains both labels and never assigns label 2 from their average

### Requirement: A pair requires two distinct supported extents
The system SHALL name a pair only when the existing trace is bracketed, all near contributors belong
to its positive source label, and all far contributors belong to one different positive label.
Missing, unassigned, mixed, source-mismatch and same-object outcomes SHALL remain distinct.

#### Scenario: Both sides are supported
- **WHEN** the near footprint unanimously carries the source label and the far footprint unanimously
  carries one different positive label
- **THEN** the profile records the pair, its native coordinates and its original bracket limits

#### Scenario: The far side is the source again
- **WHEN** both supported footprints carry the source label
- **THEN** the result is `same_object`, never a pair of distinct extents

### Requirement: A sampled pair preserves its scope and every refusal
The system SHALL retain every profile's named outcome and original trace code. Stage-level missing
inputs SHALL use the shared absence vocabulary. Pairings SHALL be recorded as selected-plane,
sample-supported evidence, never as a continuous gap, volume, anatomical role or complete interstice.
The renderer SHALL arrange the returned coordinates and codes without constructing its own geometry.

#### Scenario: The predecessor is absent
- **WHEN** no interior record is supplied
- **THEN** pairing returns `predecessor_absent` and the renderer shows that named absence

#### Scenario: A profile cannot support a pair
- **WHEN** the trace or either footprint is unread or unassigned
- **THEN** its named refusal is retained and no pair is substituted

### Requirement: The pairing record preserves the native measurement schema
The system SHALL retain P profile rows: source labels int32[P], far labels int32[P] (zero when
not paired), trace codes uint8[P], outcome codes uint8[P], flanking positions float64[P,2,2]
in native row/column coordinates, contributor labels int32[P,2,4] and original limits
float64[P,2] in mm. Side order is near/far, corner order is 00/01/10/11; -1 means zero weight
and -2 unread support. Counts SHALL include every named outcome. Outputs SHALL be immutable.

#### Scenario: A zero-weight corner is outside the image
- **WHEN** a position lies exactly on the final row or column
- **THEN** its zero-weight corner is inactive and does not make the positive-weight support unread
