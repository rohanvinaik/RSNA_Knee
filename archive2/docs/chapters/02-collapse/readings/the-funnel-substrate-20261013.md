# The substrate for the two processes: facts mined from the code (2026-10-13)

Facts only, mined by cheap readers that read the named files whole (Haiku), with file:line; the
lead's notes are labelled. Gathered before the plan for the two processes
(`openspec/changes/the-funnel/design.md` §8) is written, so its rules build on what exists.

## The two halves and the band: `knee.collapse.structure.read_structure`

- Computes, on ONE plane (pipeline `_structure`, the series' `selected_slice`, pipeline.py:248),
  only when an analysis request is given (pipeline.py:245-246): the air and the leg at native
  scale (border level, air = dark components touching the border, leg = the rest with holes
  filled, structure.py:528-559); the squint inside the leg (`physical_squint`, inside tiles =
  coverage above 0.5, structure.py:585-604); the axis from the header (`axis_code`: rows, columns
  or normal, whichever has the largest LPS z cosine; `superior_code` the way up,
  structure.py:633-656); the profile superior first and its dip; the two basins and the seam.
- **The basins** (structure.py:746-769, gated at 788-805): seeds are the first and last fifth
  (`seed_fraction` 0.2) of the inside tiles' extent along the header's axis, superior first, from
  positions only (structure.py:722-743); the field is the squint median at inside tiles, negated
  when the series table's fluid-sensitive flag is "1" (the told sign, structure.py:766, 65-74);
  smoothed by a Gaussian of one tile (structure.py:768); `watershed(-smooth, markers=seeds,
  mask=inside)`: basin 1 is the superior seed's, basin 2 the inferior's (structure.py:769).
- **The seam** (structure.py:782-785): the tiles of either basin with a four-neighbour in the
  other, "a relation, never a dark band".
- Gates: the flag must be a bool, the axis in-plane (rows or columns), some tile inside, both
  seeds non-empty; else basins and seam are zeros and `why` says why. On the axial the axis is
  the stack normal, so no basins are read there.
- The record: `StructureReading` (structure.py:113-152): `basins` int8 tile grid (0, 1, 2),
  `seam` bool tile grid, `axis`, `superior`, `profile`, `dip`, `dark`, `bodies`, counts, `why`.
- Its docstring's own scope (structure.py:34-37): the fuller mechanism (plateaus and the deepest
  dip in noise units, seeding with the plateau interiors) "is a later increment".

*The lead's note:* this is the common-sense pass at tile scale. Run on every slice of the squint
stack, inside the first lens's kept tiles instead of its own native air and leg, it gives the two
halves and the band per slice cheaply.

## The route today: `knee.pipeline.run_study` (pipeline.py:322-598)

In order: read_study (361); read_pairs (366); per series: read_regime (377), read_squint_stack
(381, every slice, no request needed), `_structure` (384, one slice, request only), read_lenses
(390, the whole volume), `_measure` (396, request only: `measure_series`); read_lineups (409);
read_first_lens (430); read_tile_digits (444); read_conjunction (462, recipients); read_depth
(476); the conversation (489-504, request with conversation only); per series:
read_ownership_members (521), read_relations (522), read_bundles (530); read_findings (578);
read_output (579). `SeriesRun` fields: pipeline.py:118-180; `StudyRun`: 202-209.

## The high-resolution lenses: `knee.objects` (mined 2026-10-13, five files read whole)

- **`measure_series`** (analysis.py:147-175, body `_measure_series` 178-294) reads ONE slice,
  `selected_slice(len(volume), request.slice_index)` (187), the plane as stored with no resampling
  (217), and hands the whole plane to `read_interiors` (221-233) and its arrays to
  `boundary_census` (236-246) when `prominence_mm` is set. `AnalysisRequest` fields and refusals:
  analysis.py:59-125.
- **`read_interiors(plane, spacing_rc, split, prominence_mm, offsets_mm, backend="reference", *,
  metric_rc=None)`** (interiors.py:151-269) runs on any 2-D plane, whole: `dark = available &
  (plane <= split)` (195-199); the Euclidean distance from dark or unavailable places in mm
  (212-222); peaks by `h_maxima` at `prominence_mm` (223-227, `prominent_peaks` 137-148);
  `watershed(-distance, markers, mask=interior)` territories (231-234); every directed
  four-neighbour edge of a territory with what lies across it, `EDGE_KINDS` low_signal,
  peer_territory, acquisition_missing, frame, unseeded_available (`boundary_edges` 71-102,
  codes 30-36); a profile along each edge's normal at `offsets_mm` (242-244) and the dark band
  across it, `TRACE_CODES` bracketed, no_dark_bracket, multiple_brackets, missing_profile,
  frame_clipped, empty_profile, invalid_measurement (`dark_bands` 105-134, codes 21-29). Its
  record `InteriorReading` (50-68) carries dark, available, distance_mm, markers, labels, edges,
  profiles, band_low_mm, band_high_mm, trace points and codes. Codes: measured, empty_plane,
  no_finite_support, split_unavailable, no_interior_seeds.
- **`sample_profiles`** (profiles.py:86-153) samples the native plane bilinearly at given points
  along given normals only, reference and Numba twin (`profile_samples_reference` 26-56,
  `jit_profile_kernel` 59-65).
- **`converse`** (conversation.py:387-476) exchanges each same-orientation peer's bracketed dark
  bands into the recipient's plane (`exchange` 216-384) and subdivides the recipient's
  territories by the concurrent and the conditional barriers (`subdivide` 106-139); codes
  measured, solitary, recipient_unavailable.
- **`boundary_census`** (boundaries.py:169-286) counts, per territory, its peak height and its
  edges by kind, and per touching pair the divide sites and the saddle (`pair_code` 72-111).

*The lead's note:* these are his attached sheet's lenses (distance from dark, interior peaks,
territories, native edges, dark-band traces). They run on one slice over the whole picture;
nothing hands them the place the squint found, so the place is handed to them as a crop.

## The twelve, the ownership, the bundles and the output (mined 2026-10-13, eight files read whole)

- **`read_findings(series, correspondence_declared=False)`** (predicates/findings.py:371-454)
  always returns twelve rows; `finding_code` (119-197) returns only refusals and abstentions
  (`CODES` 65-76; comment 63-64: "none decides anything about a knee"). `form_given` is
  hard-coded False (356) and `prior_outcome_offered` False (358), so every construction row that
  passes its subject checks returns `form_not_given`, and `correspondence_declared` cannot change
  a code. Rows 2 to 11 filter interstice records by kind only (345), so rows 2, 3, 4 read one
  candidate set, as do 5, 6, 7 and 9, 11. No numeric measurement is read (43-44).
- **`read_output`** (output/projection.py:176-244) joins the twelve to the competition's columns
  (`COLUMN_BY_INDEX` 46-59) and returns `projection_undeclared` with no rows while no `Projection`
  is given (62-72, 228-237); `submission_rows` (247-268) refuses unless `present`.
- **`read_bundles`** (vectors/bundles.py:972-1015) counts, per territory of the selected native
  plane's `interiors.labels`, lens digits, lens standing, edges by kind and trace code, seeds, and
  the slab codes against every other acquisition; four banks always unavailable (85-93).
- **`read_ownership`** (ownership/claims.py:164-219) partitions one field into claimed, residual
  and unread places; `read_ownership_members` (351-416) seats the solitary and the conversed
  parses and keeps where they disagree.

*The lead's note:* nothing downstream reads a measurement of a knee yet. The twelve need the
drawn objects, a reading of what is wrong with each, and the form his to declare.
