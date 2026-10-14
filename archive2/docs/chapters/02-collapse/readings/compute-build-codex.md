# The accepted object toolkit: organization and compute packets

2026-10-10. The founder approved `object-resolution-toolkit-codex.md` and requested project
organization tooling, telemetry, computation-shape planning, atomic work and Detective pins.

## Reading before implementation

The current thesis compute-contract section is **§13.5, Contracts and Compiled Twins**, not the
older §12.5 pointer in the global record. I read it whole. It requires a plain reference, exact
agreement within an environment and contracts carried as data. §13.7 separates measurement,
decision and orchestration. A miner read current §13 whole and Detective's deterministic SICP
§§6–8: computation shape determines candidate transformations; behavior and counted work have
separate ledgers; every transformation names its proof gate first.

I symbolically traced the cell `contract.Contract`, `accel.set_mode`, and
`outlines.pulled_taut` reference consumer. The wrapper retains the reference, selects its twin,
leases bounded scratch and keeps arithmetic order. The cell's current optional Numba fallback
does not satisfy this repository's required-backend refusal rule; that policy is not ported.
A miner read the complete contract, arena, executor and SAME testing units. These facts guide
engineering, not anatomical meaning.

## Decisions for this build

- **Hamilton, dev-side:** an executable graph of the same production measurement functions.
  The DAG covers one acyclic measurement pass. The future residual loop stays an explicit loop,
  not a cycle disguised as a DAG. Graph validation is structural evidence, never anatomy evidence.
- **OpenSpec:** one declared change with ordered packets and scenario contracts. The chapter
  records and founder's words remain authoritative. No generated client instruction files replace
  AGENTS.md. OpenSpec commands run with `OPENSPEC_TELEMETRY=0`.
- **Packet A, physical measurements:** DICOM frame; physical squint with ragged-edge coverage;
  native bilinear border profiles, slopes and missing support; requested/effective backend;
  read-only records; production entry point; real-corpus receipt and profiles.
- **Packet B:** candidate interiors and supported contour chains; movement bands and barriers are
  explicit inputs; closure is per chain and candidate gaps remain recorded.
- **Packet C:** facing surfaces, the finite interstitial region, extent and cross-view conversation.
- **Packet D:** peer ownership, containment, own-signal views and residual scheduling. Its knee
  teaching is recorded before loop semantics become production decisions.

The measurement interface carries the physical tile size, profile offsets, probe locations and
direction explicitly. None is a classification threshold. Demonstration settings are recorded,
not installed as anatomical admission bars. Profiles with missing support retain NaN and a named
support code. Axial superior direction is not replaced silently with an image-row default.

The first numeric twin is a repeated bilinear sample loop over P profiles × S offsets, with at
most four source reads per sample. Reference Python establishes order; Numba compiles the same
numeric body with `fastmath=False`, `nogil=True`. Output scratch is bounded by P×S, never a whole
float64 copy of the volume. SAME compares value, mask, slopes, dtype, shape, signed zero and NaN
standing. Execution provenance differs by design and is recorded separately.

NumPy/library-shaped squint work remains NumPy. C/C++ is reserved in these packets for a measured
memory-bound tiled kernel; Rust for exact integer/bit-level scans if that computation arises.
Their admission gates are the same reference/SAME obligations plus sanitizer/toolchain receipts.
No speed claim or native rewrite is licensed merely because its language is available.

Every packet records real entry-point consumers, reference contracts, source lineage, source
digest and current Detective standing. Generated characterization never substitutes for intent
tests. Profilers run the production route; paired budget counts accompany any eventual speed claim.
Linux/Kaggle compatibility remains a separate DEPLOY proof, not something a macOS VERIFY run establishes.

## Packet A contract

`PlaneFrame` maps native row/column coordinates into DICOM patient millimetres using original
position, orientation and spacing. The inverse projects into the same plane. Singular, absent or
malformed geometry is unreadable, not a negative anatomical finding.

`physical_squint(plane, spacing_rc, tile_mm)` returns median, minimum, maximum, finite coverage and
native bounds for every physical tile. Remainder tiles survive. It never changes the source image.

`sample_profiles(plane, points_rc, normals_rc, offsets_mm, spacing_rc, backend)` returns samples,
valid support, distances, slopes and a named support code. The normal components are in physical
row/column directions; each is unit length. Only positive-weight contributors must be finite.
Coordinates outside the acquired rectangle are missing, without clamping/extrapolation. Profiles
can be empty. Offsets must be finite and strictly increasing; invalid shape/spacing/direction
raises a named validation error. No profile operation names a tissue or lesion.

`profile_support_code(requested, supported)` returns `invalid_counts`, `empty_request`,
`no_support`, `partial_support` or `complete_support`. Its intent tests precede the Detective walk.

`measure_series` consumes the series already read by Chapter 1. `run_study` reads each series once
and optionally carries the returned measurement record. Hamilton consumes the same functions.
Rendering and telemetry observe these returned values and compute no substitute segmentation.
