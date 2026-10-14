# Spec Delta

## Purpose

Defines physical-coordinate measurements and their support and execution records for Chapter 2. These measurements preserve acquired values and make missing support explicit without assigning anatomical meaning.

## ADDED Requirements

### Requirement: Plane geometry maps native coordinates to patient space
The measurement system SHALL map native row/column coordinates to DICOM patient millimetres using original position, orientation, and spacing, and SHALL provide the inverse projection into the same plane.

#### Scenario: Valid oblique plane
- **WHEN** a plane has valid position, orientation, and spacing, including an oblique orientation
- **THEN** native coordinates map to patient millimetres and project back into that same plane

#### Scenario: Missing or malformed geometry
- **WHEN** plane geometry is absent, singular, or malformed
- **THEN** the plane is reported unreadable and no negative anatomical finding is emitted

#### Scenario: Axial superior direction
- **WHEN** measurements use an axial series
- **THEN** superior direction is derived from the measured plane and stack geometry, without substituting an image-row default

#### Scenario: Rounded header directions
- **WHEN** admitted direction cosines contain their original header rounding
- **THEN** physical length and profile direction use the retained basis metric, with source coordinates unchanged

### Requirement: Physical squints retain coverage and native bounds
The system SHALL measure every requested physical tile and return its median, minimum, maximum, finite coverage, and native bounds without modifying source values.

#### Scenario: Ragged edge tiles
- **WHEN** the image dimensions do not divide evenly into the requested physical tiles
- **THEN** remainder tiles are measured and their native bounds and finite coverage are returned

### Requirement: Native profiles preserve physical sampling and support
The system SHALL sample profiles at strictly increasing finite physical offsets using unit normals in physical row/column directions, returning sample values, support, distances, slopes, and a named support code.

#### Scenario: Valid bilinear sample with a non-finite zero-weight neighbor
- **WHEN** a sample has a non-finite source value only at a contributor whose bilinear weight is zero
- **THEN** that value does not invalidate the sample

#### Scenario: Positive-weight contributor is missing
- **WHEN** a positive-weight bilinear contributor is non-finite or the sample coordinate lies outside the acquired rectangle
- **THEN** the sample is unsupported, remains NaN, and is not clamped or extrapolated

#### Scenario: Empty profile request
- **WHEN** the point and normal arrays contain no profiles and offsets are otherwise valid
- **THEN** the operation returns empty profile-shaped outputs without failing

#### Scenario: Malformed profile arguments
- **WHEN** array shapes, spacing, direction, or offsets are invalid, or offsets are not finite and strictly increasing
- **THEN** the operation raises a named validation error

#### Scenario: Profile measures signal only
- **WHEN** a profile is sampled
- **THEN** its record describes values, distances, slopes, and support without naming tissue or lesion

#### Scenario: Adjacent sample support
- **WHEN** either member of an adjacent pair is unsupported
- **THEN** its slope remains NaN; otherwise the slope is their value difference divided by physical offset difference

#### Scenario: Unsupported JIT dtype
- **WHEN** JIT is requested for a plane outside its admitted native integer/float32/float64 dtype contract
- **THEN** a named dtype error refuses that execution rather than silently copying or changing backend

### Requirement: Profile support is a named count decision
The support decision SHALL return `invalid_counts`, `empty_request`, `no_support`, `partial_support`, or `complete_support` from the requested and supported counts.

#### Scenario: Invalid support counts
- **WHEN** requested or supported counts are invalid
- **THEN** the decision returns `invalid_counts`

#### Scenario: Empty support request
- **WHEN** the requested count is zero and counts are valid
- **THEN** the decision returns `empty_request`

#### Scenario: No supported samples
- **WHEN** a non-empty valid request has zero supported samples
- **THEN** the decision returns `no_support`

#### Scenario: Partial and complete support
- **WHEN** a valid request has some but not all samples supported, or all samples supported
- **THEN** the decision returns `partial_support` or `complete_support`, respectively

### Requirement: Reference and accelerated execution preserve SAME
The numeric reference and its accelerated twin SHALL agree within one environment on values, masks, slopes, dtype, shape, signed zero, and NaN standing; execution provenance SHALL be recorded separately.

#### Scenario: Same-environment exact comparison
- **WHEN** the reference and twin run with equivalent inputs in the same environment
- **THEN** all specified outputs and NaN standing agree, including signed zero, while execution provenance remains separately observable

#### Scenario: Required backend unavailable
- **WHEN** a caller explicitly requests a backend that is unavailable
- **THEN** execution refuses with a named unavailable-backend outcome and does not silently fall back

### Requirement: Production measurement consumes each series once
The production study route SHALL measure the series already read by Chapter 1, decode each series' pixels once, and make the returned measurement record available to downstream consumers. A separate source-byte hashing pass SHALL be recorded independently of that decode claim.

#### Scenario: Measurement through the production entry point
- **WHEN** a study is run through the production entry point
- **THEN** each series is read once, its measurement record is carried forward, and rendering and telemetry observe that returned record

#### Scenario: One series has invalid selected geometry
- **WHEN** an individual series has malformed geometry or an unavailable selected plane
- **THEN** it carries a named reading with validation detail while other series' records remain available

### Requirement: Development graph observes production measurements
The development Hamilton graph SHALL represent one acyclic measurement pass using the same production measurement functions; graph validation SHALL report structure and SHALL NOT assert anatomical correctness.

#### Scenario: Graph execution
- **WHEN** the development graph executes a measurement pass
- **THEN** it invokes the same measurement functions as the production route and exposes their returned records

#### Scenario: Residual work remains iterative
- **WHEN** future residual scheduling is represented
- **THEN** it remains an explicit loop and is not encoded as a cycle in the measurement graph

### Requirement: Measurement receipts preserve provenance
Each measurement receipt SHALL record source lineage and digest, requested and effective backend, measurement outputs, real-entry-point execution, and current Detective standing.

#### Scenario: Receipt accompanies production measurement
- **WHEN** a production measurement run completes
- **THEN** its receipt identifies the source and digest, records the requested and effective backend and returned measurements, and records the current Detective standing

#### Scenario: Study checkpoint survives interruption
- **WHEN** a study completes or fails after writing partial records
- **THEN** an atomic study checkpoint records request, source/writer identity, saved records and failures before the next study proceeds

#### Scenario: Resume detects changed proof inputs
- **WHEN** a production source, proof receipt, saved artifact or verifier changes after a SAME run
- **THEN** computed resume status exposes the stale link and does not declare that proof current

### Requirement: Each distinct step produces a saved image series
Each distinct admitted build step SHALL save a source-linked image series rendered from its actual production records, including unresolved support and coordinates.

#### Scenario: Packet A visualization
- **WHEN** Packet A's saved records are rendered
- **THEN** acquired images, full recorded background annotations, physical squints, native sample locations and measured profiles are visible with an explicit color legend and a manifest linking source plane, slice, probe, receipt and artifacts

#### Scenario: Background split annotation retains the production reading
- **WHEN** the regime returns a finite whole-series background split
- **THEN** its acquired-plane comparison mask is saved and displayed in red, while supported profile samples use cyan and missing support uses magenta

#### Scenario: Background split unavailable
- **WHEN** no finite split is returned
- **THEN** no background mask is fabricated and the display names that annotation unavailable
