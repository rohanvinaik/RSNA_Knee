# Design

## Responsibility in the current build

This change owns the substrate packets, including supported-contour-chains added
after the original proposal. The immediate breadth-first route belongs to
`every-stage-renders`; full object/relation/predicate/deployment work belongs to
`knee-object-model`. B2’s two maps remain source evidence; the founder’s one-name
conversation intent requires a deliberate exposed-standing contract, preserving
originals and dissent. No merge rule is inferred here.

## Context

See [proposal.md](proposal.md) for the motivation and scope. Chapter 1 reads each study and its series; Chapter 2's production measurement consumes that series. The pre-packet study route reread series. The admitted route decodes once, while workbench panels observe the returned values. The thesis compute contract requires a plain reference, a twin that agrees within one environment, and contracts carried as data.

## Goals / Non-Goals

**Goals:**

- Make Packet A's patient geometry, physical coverage, native profile support, and provenance observable through one production measurement record.
- Keep the numeric reference and compiled twin behaviorally identical within an environment, including masks and NaN standing.
- Let development graph execution, rendering, profiling, and telemetry observe the same production functions and returned records.
- Resolve geometric interiors and native boundary evidence using the existing surrounding-field measurements, keeping all territories and unresolved divisions.
- Build a general conversation between same-orientation readings of the same knee, grounded in the thesis and live cell implementation, with staged pictures of its exchanges and refinements.

**Non-Goals:**

- Assign anatomical identity, boundary admission, tissue meaning, or finding labels.
- Set physical scales or movement bars from gold labels or leaderboard scores.
- Invent anatomical admission or ownership rules for the subsequent packets.
- Claim Linux/Kaggle compatibility from a macOS verification run.

## Decisions

- **One physical coordinate contract:** PlaneFrame maps native row/column coordinates through original DICOM position, orientation, and spacing into patient millimetres, with an inverse projection into that plane. Missing, singular, or malformed geometry is unreadable input and produces a named validation outcome; it is not an anatomical negative.
- **Retain the actual coordinate metric:** Rounded header directions remain unchanged. Project a patient direction with the retained basis pseudoinverse and normalize by its actual patient-space length. Row/column physical coefficients use the resulting Gram metric, not an assumed identity matrix. This coordinate interface is separate from the thesis's constructed orthogonality of claims and carrier rows.
- **Keep acquired support explicit:** Physical squints preserve remainder tiles and return median, minimum, maximum, finite coverage, and native bounds. Profile sampling uses native values and physical offsets. Out-of-acquisition coordinates are missing; only positive-weight bilinear contributors need finite values. No border clamp or extrapolation fills unsupported samples.
- **State support and slopes precisely:** The acquired rectangle is the pixel-centre domain `[0,R-1] × [0,C-1]`. Support conjoins coordinate inclusion and finite positive-weight contributors. Slopes use adjacent supported samples divided by their physical offset difference; a missing member leaves the slope missing. A single requested offset is zero.
- **Separate measurement from policy:** Profile support classification is a named pure decision over counts. Its codes are `invalid_counts`, `empty_request`, `no_support`, `partial_support`, and `complete_support`. Missing support remains NaN with its support status; no profile is named for tissue or lesion.
- **Reference before twin:** A repeated Python bilinear loop establishes arithmetic order for P profiles by S offsets, with at most four source reads per sample. The Numba twin uses the same body with `fastmath=False` and `nogil=True`. SAME compares values, mask, slopes, dtype, shape, signed zero, and NaN standing within one environment. Execution provenance is recorded separately. An explicitly requested unavailable backend is refused.
- **Bound scratch to requested work:** Output scratch is bounded by P×S; the implementation does not make a whole-volume float64 copy. Source arrays remain unmodified, and newly owned output arrays are read-only.
- **Route through the existing read:** `measure_series` consumes the series already read by Chapter 1; `run_study` decodes each series' pixels once and can carry the resulting measurement record. A separate source hashing pass is allowed. The renderer and telemetry observe that record. Hamilton is development-only: its DAG wraps one production run rather than representing each internal kernel operation as a node; residual iteration remains a later explicit loop.
- **Keep evidence with the run:** The Packet A receipt records source lineage and digest, requested/effective backend, geometry/profile outputs, real-entry-point execution, and current Detective standing. Profiling follows the production route; behavior and counted work remain separate. Deployment compatibility is a separate Linux/Kaggle proof.
- **Checkpoint and visualize actual records:** Each completed or partial study publishes an atomic checkpoint. The final receipt distinguishes requested studies, successfully saved series and failures, hashes all imported production sources, and retains selected plane identity and orientation spread. Per-series geometry/index failures remain named readings. SAME binds receipt, artifacts and verifier; resume status checks those links. The image series binds the same records and source coordinates. Rendering contains no substitute segmentation.
- **B1 surrounding-to-interior constraint:** Low signal and missing acquisition bound the above-split geometric search; a virtual frame guard bounds the computation. Record each nearest cause and the error bound from the retained rounded DICOM metric. Four-connected prominence markers and watershed retain all proposed territories, including small and unseeded regions. This measurement makes no anatomical assignment.
- **B1 native boundary evidence:** Enumerate every directed territory edge, sample original values with the reference/JIT contract, and retain dark-interval endpoints and midpoint only under the declared complete, unique, bounded-interval predicate. Open, multiple, missing and clipped outcomes remain named. A profile window measures a band; it is not a declaration of cortical thickness.
- **B2 shared objects:** The founder's relation is the same knee and its objects, seen through different measurements. The cell-instance depth-nearness/stacked-cell rules do not become knee identity tests. General boundary exchange belongs in the production study route, preserving each lens's readings; the founder's specific coronal pair remains an illustrative inspection case. Coordinate projection expresses evidence in native arrays without making a local region ID into an anatomical identity.

## Risks / Trade-offs

- [A malformed orientation or spacing makes a plane unreadable] → Preserve the named validation outcome and source geometry in the receipt so the failure remains inspectable.
- [A boundary sample has partial or no support] → Retain NaN samples and explicit masks/codes instead of extending values beyond the acquired rectangle.
- [A compiled twin changes floating-point details] → Gate admission on the same-environment SAME fields, including signed zero and NaN standing, with reference execution available.
- [A development graph drifts from production behavior] → Build graph nodes from the same production measurement functions and treat graph validation as structural evidence only.
- [A local run is mistaken for deployment proof] → Record environment provenance and keep Linux/Kaggle compatibility as a separate deployment check.

## Migration Plan

There is no data migration in Packet A. Add the measurement contract at the existing Chapter 2 boundary, route the already-read series to it once, and expose its returned record to downstream rendering. Retain the reference path for environments where the compiled twin is not requested; fail explicitly when a required backend is unavailable.

## Open Questions

None for Packet A's specified measurement behavior. Anatomical admission conditions, physical demonstration scales, uncertainty calibration, and assignment policy remain for founder-led visual packets and are not design questions settled here.
