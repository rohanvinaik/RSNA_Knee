# Tasks

## 1. Packet A: physical frame, squint, and profiles

- [x] 1.1 Record the compute contract for the reference and twin, including shapes, axes, dtype, units, access order, P×S scratch bound, and at most four source reads per sample; verify the contract is carried with the kernel and does not copy the whole volume to float64.
- [x] 1.2 Implement patient-space plane mapping and inverse projection from original DICOM geometry; verify round trips for valid oblique planes and named unreadable outcomes for absent, singular, and malformed geometry, including axial superior without an image-row fallback.
- [x] 1.3 Implement physical squints with median, minimum, maximum, finite coverage, and native bounds; verify ragged remainder tiles and confirm source values are unchanged.
- [x] 1.4 Implement the native Python profile reference for finite increasing physical offsets and unit physical row/column normals; verify empty profiles, malformed inputs, positive-weight missing support, zero-weight non-finite neighbors, outside-rectangle support, NaN retention, and slopes.
- [x] 1.5 Implement `profile_support_code` with the five named outcomes; verify intent cases first, then record current Detective standing for the pure decision.
- [x] 1.6 Implement the Numba twin with `fastmath=False` and `nogil=True`, requested/effective backend recording, and explicit refusal for an unavailable requested backend; verify same-environment SAME for values, mask, slopes, dtype, shape, signed zero, and NaN standing.

## 2. Packet A: production route and returned record

- [x] 2.1 Implement `measure_series` over the Chapter 1 series record and route `run_study` through it without rereading each series; verify the real production entry point reads each series once and carries the measurement record downstream.
- [x] 2.2 Make measurement outputs read-only to consumers and connect rendering and telemetry to those exact returned values; verify the rendered and observed records match the production measurement record.
- [x] 2.3 Add the development-only acyclic Hamilton graph using the same production measurement functions; verify graph execution returns the same records and residual scheduling remains an explicit loop rather than a graph cycle.
- [x] 2.4 Produce the Packet A source-lineage and digest receipt with requested/effective backend, geometry and profile outputs, real-entry-point run, and current Detective standing; verify the receipt against a run across all 58 studies and profile the production route with behavior and counted work recorded separately.

Evidence: `docs/chapters/02-collapse/measurements/physical-packet-a.md`.
Resume: `docs/chapters/02-collapse/RESUME.md`. Completion records the declared
measurement contracts, not anatomical contour completion or unconditional mutant
pinning. Recompute current standing with `just packet-status`.

## 3. Packet B: candidate interiors and supported contour chains

- [x] 3.1 Persist the founder's surrounding-field / no-noise teaching and B1's bounded geometric contract; distinguish low signal, availability, search guards, territory, observed boundary and ownership.
- [x] 3.2 Implement geometric distances, explicit prominence markers, all four-connected territories and directed native edges; retain nearest guard causes and the rounded-coordinate metric error bound.
- [x] 3.3 Reuse reference/JIT native sampling for unique bounded dark intervals, preserving open, multiple, missing and clipped outcomes; test empty, missing, frame and affine-intensity cases and pin the pure named border decision with its actual qualifications.
- [x] 3.4 Wire B1 through the existing read-once production route, record/checkpoint all 58 studies, and compare every B1 saved array/code against reference and JIT within the recorded environment.
- [x] 3.5 Produce and inspect the surrounding-field, interiors and native-traces color image series under data/pictures; bind their receipt/array/image identities and retain telemetry through the same production entry.
- [x] 3.6 Trace the general lens conversation and refinement in the thesis and live cell route, work out the knee boundary exchange with Fable, and specify supported-chain movement/band contracts. Preserve the founder's shared-object relation and use his coronal pair only as an example.
- [x] 3.7 Implement the general same-knee conversation in the production study route, exchanging boundary constraints across participating measurements and retaining separate originals, refinements, source provenance and disputes. Show before / exchange / after series across views, including the founder's example.
- [ ] 3.8 Implement the admitted connectivity-within-bands and constrained contour-shortening reference operation; verify closure is reported per chain and candidate gaps, unsupported places, original/refined traces, shed places, and clipping remain inspectable in the visual packet.

B1 evidence: `docs/chapters/02-collapse/measurements/geometric-interiors-b1.md`.
Its completion is the declared geometric measurement, not final anatomical ownership.
Recompute source/proof standing with `just interiors-status`.

B2 exchange evidence: `docs/chapters/02-collapse/measurements/same-knee-conversation-b2.md`.
Recompute it with `just conversation-status` and its staged photo lineage with
`just conversation-picture-status`. Tasks 3.6–3.7 establish original-band
exchange, bounded intersections and two retained connectivity maps. Generic
closure/shortening remains 3.8; no anatomical ownership is implied.

## 4. Packet C: facing surfaces, interstitial region, and extent

- [ ] 4.1 After the founder records the knee teaching, specify facing-surface and finite interstitial-region measurements, including extent and separately acquired view conversation; verify the contract records support and unresolved places without assigning tissue identity from position alone.
- [ ] 4.2 Implement and present the admitted measurements through neighboring physical slices and separately acquired views; verify source coordinates, extent, coverage, alignment uncertainty, and disagreements are visible in the paired visual packet.

## 5. Packet D: ownership, own-signal views, and residual scheduling

- [ ] 5.1 Record the founder's knee version of peer ownership, containment, own-signal views, and residual rereading before deciding loop semantics; verify the packet preserves unclaimed and disputed regions and names no missing reading as rejection.
- [ ] 5.2 Implement residual scheduling only after that teaching is recorded; verify a candidate's own samples remain unchanged when peer objects are excluded from its search/display and that excluded, unclaimed, and disputed source data remain reachable.
