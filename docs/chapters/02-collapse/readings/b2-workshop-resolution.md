# B2 workshop resolution and implementation contract

2026-10-11. The lead's own reading preceded Fable. The consultation sent abstract
reasoning and founder instructions only, with no source/data/identifiers.

Fable usefully identified an undefined barrier set and undeclared raster
connectivity. The implementation will retain **two** explicit connectivity
readings: barriers supported by intersecting native sample runs, and barriers
conditional on a donor-only reading as well. Both original and resulting maps
remain present. A conditional subdivision is not a change in anatomical ownership.

Fable's inference that an available non-dark recipient reading necessarily
contradicts an object boundary is rejected. Darkness is a scoped predicate, not
the definition of all anatomical borders; the founder explicitly teaches that
each valid discrimination can contribute. Keep the non-dark result and the
donor constraint separately. The same-knee relation is the founder's premise,
not a hypothesis to replace with a proximity score.

## Fixed interfaces

- All ordered same-orientation sequence pairs in one study participate. Exchanges
  consume **original B1** records only, never another exchange's derived trace.
- A donor contributes its unique bounded dark-run edges. Native and patient
  coordinates, donor edge/territory, split, offsets and interval bounds remain
  accessible. Intersections/midpoints are **derived**, never new raw samples.
- Projection keeps signed off-plane distances and plane-normal angle. Recipient
  coverage is its **DICOM SliceThickness / 2** around the selected plane. This
  is acquired slab support, not object nearness or a claim that two sections
  have identical shapes. Unknown slab thickness remains `slab_support_unknown`;
  out-of-slab segments remain `outside_slab`. All four transported band corners
  must lie in the slab before that segment becomes a raster constraint.
- Re-read unchanged recipient samples with its own split and requested offsets.
  Read every contiguous dark run. A donor envelope that selects exactly one
  **bounded** recipient run resolves that run even if other runs occur elsewhere
  in the profile. Multiple matching runs, an unbounded matching run, missing
  samples, no matching observed run and missing geometry remain named.
- Sample runs describe sampled predicates, never cortical thickness. For
  rasterization, use the sample-cell envelope (half the declared profile step
  beyond first/last sample centres) and half the donor native edge's tangent
  extent. This is a representation contract, not calibrated uncertainty. A
  concurrent envelope never claims finer resolution than the coarser sample step.
- A convex transported band marks every recipient pixel cell it intersects
  (supercover, inclusive boundary). Original territories are subdivided with
  **four-connectivity** inside their own original labels. A barrier place is
  retained explicitly rather than assigned away. No small piece is dropped.
- `concurrent` barriers contribute to both connectivity readings. `peer_only`
  barriers contribute to the conditional reading. Other codes contribute to
  neither. Each exchange retains its own mask; combined masks have declared OR
  semantics and are geometric readings, never votes or anatomical decisions.

## Production, checks and pictures owed

Append an explicit conversation request to the existing analysis settings. After
all per-series measurements, the existing study route returns one conversation
record per series. The existing writer saves those exact records/checkpoints;
Hamilton consumes counts from them. No drawing/development dependency enters
production. Native sampling and repeated band rasterization keep strict
reference/JIT twins with exact same-environment comparison.

Tests must distinguish empty/unavailable/slab/missing/disjoint/open/multiple
outcomes, preserve every source sample and original label, prevent recursively
borrowed evidence, keep original-parent identity for subdivisions, and show a
synthetic donor-only boundary separating a recipient's connected territory.
Production and SAME run over the 58. Pictures show originals, exchanged bands,
native concurrence/disputes, and both connectivity readings across all views.
They are written beneath `data/pictures/object-toolkit/conversation-b2/`.

Generic constrained contour shortening remains a separate task (3.8). This
increment's improved boundary traces come from declared run selection and
intersection; it does not import the cell's roundness/oval or noise parameters.
