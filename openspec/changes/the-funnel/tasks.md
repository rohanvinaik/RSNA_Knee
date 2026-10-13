# Tasks: the funnel

The build order is the dependency order Codex and the lead settled: 0, 1, 3a, 2, 3b, 3c, 4, 5, 5b,
6, 7, 8, 9, 10, 11, with the route (13) and the pictures (12) wired per unit, never after. Every
unit is built under the loop of `docs/STAGE_CONTRACT.md` ("How a UNIT gets built"): declared here
first; its module docstring naming the thesis role and the founder's words; the pure decision
first, total over its arguments, returning a named code, every bar an argument; PEP 316
contracts; two-sign intent tests calling the function directly; `just detective converge` with
every survivor judged; `just crosshair`; wired so something on the route consumes it; rendered;
run on the one real study through `just analyze-objects`; re-pinned; `just gate`; recorded in
`docs/chapters/02-collapse/README.md`. "Verify" below names what is specific to the unit. A task
is checked only with its declared evidence. The records' shapes and codes are in `design.md` §2;
the constants and their provenance in §3. Anatomical words below are the designer's glosses; no
record, code name or picture carries one.

The eye-checks (E1 to E5) are the founder's; the build pauses at each. A workflow that carries the
mechanical parts runs up to the next eye-check and stops.

## 0. The study: the free lenses, paired

- [ ] 0.1 `knee.study.pairs`: `pair_code(n_bright, n_dark) -> str` over `PAIR_CODES`, and
  `read_pairs(study) -> AcquisitionPairs` from the series table's `anatomical_plane`,
  `fluid_sensitive` and `fat_suppression`; verify the one study yields two `paired` planes and one
  `solitary`, that a plane with three series is `surplus` with all three kept, and that no header
  description is read.
- [ ] 0.2 Declare the module in `docs/places.json`; add the pairs to the study drawer's caption and
  the receipt; verify `just places` reports it reached.

## 1. The squint over the stack, in millimetres

- [ ] 1.1 `knee.collapse.squint_stack.read_squint_stack(series, tile_mm) -> SquintStack`: one
  `physical_squint` per slice, `centres_lps` from `PlaneFrame.from_dicom(position[z],
  orientation[z], spacing).to_patient(tile centres)`; verify against the saved run's selected-slice
  squint that the chosen slice's medians are byte-identical, that the centre of tile (0, 0) equals
  the slice's `ImagePositionPatient` offset by half a tile in both in-plane directions, and that a
  series without a stacked volume returns the named absence.
- [ ] 1.2 Picture: the squint at the walk slices over the acquired planes, through `knee.pictures`
  and a view-sheet panel; verify the renderer only arranges.
- [ ] 1.3 Budget: the squint stack's counted work per series under its `ComputeContract`, beside
  the whole-volume digit maps' counted work on the same series, reported separately from any
  profiler; verify the ratio is recorded in the chapter's measurements.

## 3a. The line-up, by place on the knee

- [ ] 3a.1 `knee.collapse.lineup.match_code(distance_mm, half_tile_mm, partner_exists) -> str` over
  `MATCH_CODES`, pure; `line_up(recipient: SquintStack, partner: SquintStack, geometry) ->
  LineUp` with `partner_slice`, `slab`, `partner_tile`, `distance_mm`, `codes`; verify on the
  coronal pair that every leg-region tile of the fat-dark series matches a fat-bright tile within
  half a tile, that the matched tile's native bounds on the fat-bright plane overlap the recipient
  tile's millimetre footprint, that the two coronal series' chosen slices are within half a slice
  thickness of each other along the normal, and that a solitary series yields `partner_unavailable`
  everywhere.
- [ ] 3a.2 Picture: the recipient grid with the partner's tile centres drawn over the recipient
  plane; verify by eye on the coronal pair that the two grids lie over the same knee (this is the
  "scootch").

## 2. The first lens: background versus leg, per view, frozen

- [ ] 2.1 `knee.collapse.first_lens.tile_code(all_dark, any_dark, air_connected, beside_air,
  finite) -> str` over `TILE_CODES`, pure and total, pinned; `read_first_lens(stack: SquintStack,
  split: float) -> FirstLens` with four-connected air from the picture's border within each slice;
  verify both signs: a dark tile enclosed by leg tiles is `leg` (the dark interior of a bone on the
  fat-dark series), a mixed tile beside air is `undecided`, a NaN split abstains on the series with
  `split_unavailable`, and no `background` tile is adjacent to a `leg` tile without an `undecided`
  tile between them or a straight all-dark boundary.
- [ ] 2.2 Freeze: the record is saved once per series by the writer and read back by every later
  operation from the saved run, never recomputed; verify with the ledger that no later operation
  records a read of a `background` tile, and that the record carries the split it used and the rule
  version.
- [ ] 2.3 Picture: per view, the tiles by code over the acquired plane at the walk slices; a
  view-sheet panel; verify the renderer only arranges.
- [ ] 2.4 **E1 (his).** The five sheets in front of him: he confirms, per view, that no background
  tile holds any part of the knee and that the undecided ring sits where the skin is. A view that
  fails gets its own rule, declared here as a new task with its provenance before it is written.

## 3b. The tile digits, over the leg

- [ ] 3b.1 Make the tercile rule public: `knee.collapse.regime.tercile_edges(values,
  minimum_population) -> (low, high, count)`, the one rule `_shape_readings` already applies; verify
  `read_regime`'s terciles are byte-identical before and after.
- [ ] 3b.2 `knee.lenses.tiles.read_tile_digits(stack: SquintStack, first: FirstLens,
  minimum_population) -> TileDigits`: edges from the medians of every `leg` tile of the series;
  digits by `place_codes_reference` with `background` and `undecided` tiles handed NaN; verify
  silence is 2 and never 0, that the count equals the number of leg tiles, and that the fat-bright
  coronal's `above` tiles lie inside the two big bright regions by eye.
- [ ] 3b.3 Picture: the digit grid over the plane with silence drawn as silence; a view-sheet panel.

## 3c. The conjunction, per pair

- [ ] 3c.1 `knee.lenses.conjunction.conjunction_code(partner_digit, own_digit, match) -> str` over
  `CONJUNCTION_CODES`, pure and total over the digit values including silence, pinned;
  `read_conjunction(own: TileDigits, partner: TileDigits, lineup: LineUp) -> Conjunction`; verify
  the twelve codes are exhaustive over the 4 × 4 digit pairs and the match codes, that no code
  carries a tissue word, and that on the coronal pair the `above_below` tiles fill the two big
  regions and the `below_below` tiles trace the dark line between them.
- [ ] 3c.2 Picture: the conjunction code as colour over the recipient plane; a view-sheet panel.

## 4. The depth collapse: each lens at its own slice

- [ ] 4.1 `knee.collapse.depth.chosen_slice(readings, minimum_valid) -> (index | None, code)` over
  `CHOICE_CODES`, pure and total, pinned; verify both signs: a single peak is chosen, an exact tie
  takes the middle of the tied run and says so, all-NaN abstains, and fewer than `minimum_valid`
  finite readings abstains.
- [ ] 4.2 The four cheap readings per slice over the squint stack and the first lens: `leg_share`,
  `dark_share`, `split_quality` (Otsu's between-group share over the leg tiles' medians),
  `fat_share` (where a pair exists); each a measurement returning `float64 (Z,)` with NaN for
  silence; verify each is computed from the squint alone, in one pass, and that on the one study
  every series yields at least one chosen slice.
- [ ] 4.3 `read_depth(stack, first, digits, conjunction, minimum_valid) -> DepthCollapse` with the
  chosen slices deduped and each lens's choice recorded; the route reads in full only these slices;
  verify with the ledger that no later operation reads a slice outside the chosen set.
- [ ] 4.4 Reconcile with the cell build: the literal rule by which its lenses pick their slice
  (traced from `cell_tracking/src/cell_tracking/`, the collapse module), its tie and abstention
  handling; record the trace in `readings/`; where it differs from 4.1, put the difference to the
  founder before admitting the unit.
- [ ] 4.5 Picture: the four readings as curves over Z with each lens's slice marked, and the chosen
  slices drawn; a view-sheet panel naming the chosen slice.
- [ ] 4.6 **E2 (his).** Per view, the curves and the chosen slices: he confirms they are the slices
  to read, or names the reading that would choose better, declared here before it is written.

## 5. The dome at the squint

- [ ] 5.1 Refactor: one `knee.objects.dome.dome(interior, spacing, prominence_mm) -> (height,
  peaks, labels)` shared by `read_interiors` and the tile dome; verify `read_interiors` on the
  saved run is byte-identical before and after.
- [ ] 5.2 `knee.objects.tile_dome.read_tile_dome(stack, first, conjunction | None, split,
  prominence_tile_mm, slice_index) -> TileDome` with the obstacle set of `design.md` R5; verify on
  the coronal fat-dark chosen slice that the two tallest peaks lie inside the two big bright
  regions of the fat-bright partner, that no territory crosses a `below_below` run, and that an
  unseeded interior tile stays 0.
- [ ] 5.3 Picture: territories and peaks on the squint over the plane; a view-sheet panel.

## 5b. The selection by structural facts, and the laterality sign

- [ ] 5b.1 The facts per territory (`design.md` R5b), as measurements from the labels, the centres
  in LPS, the header's axes (`superior_code`, exists) and the conjunction; verify each fact is a
  number or a bool with its unit and frame, and none is a name.
- [ ] 5b.2 Pure decisions, pinned: `big_pair_code`, `anterior_small_code`, `lateral_witness_code`,
  `axial_code`, each total, each returning a role code or a named absence; verify both signs for
  each: the two largest are `superior_big` and `inferior_big` by the header's axis; a tie in area
  is broken by superior position and recorded; one big territory only is `one_big_only`; the axial
  takes `central_big` and `anterior_small` and never `superior_big`.
- [ ] 5b.3 `knee.objects.laterality`: the `lateral_sign` from `lateral_small_ringed`'s side along
  the frame's left-right axis (`OBJECT_MODEL.md`, laterality: `S × A` is patient-left; the witness
  gives the sign); abstain with `side_abstained` when no witness; verify a coronal series without
  the witness abstains and every side-dependent code downstream abstains with it.
- [ ] 5b.4 `read_selection(dome, facts, plane_kind) -> Selection` with object records `(index,
  role_code, facts, tiles)`; verify no record field holds an anatomical word.
- [ ] 5b.5 Picture: territories by role code with the facts beside each index; a view-sheet panel.
- [ ] 5b.6 **E3 (his).** Per chosen slice, the objects by role: he confirms the two big ones, the
  small anterior one on the sagittal, the small ringed one on the coronal, and the axial's own
  two, or names the fact that would select better.

## 6. The edge at native resolution, in the strip; the outline

- [ ] 6.1 `knee.objects.strip.edge_points(labels, bounds_rc, object_index) -> (points, normals)`
  at the midpoints of the object's tile boundary segments in native rc, outward normals;
  `read_strip(plane, spacing, points, normals, strip_mm, split, prominence_native_mm) -> Strip`
  using `sample_profiles` and `dark_bands` with offsets spanning `±strip_mm`; verify the profiles
  are cast only at those points, that the number of samples equals points × offsets, that a point
  whose profile leaves the plane is `frame_clipped`, and that on the coronal fat-dark chosen slice
  the bracketed bands lie on the dark line between the two big objects by eye.
- [ ] 6.2 The partner's bands transported to the same points through `exchange` where a pair exists;
  verify the exchange codes are kept per point and nothing is merged.
- [ ] 6.3 The strip's native digits against the terciles of the object's own pixels; verify the
  population is the object's tiles' pixels and nothing outside.
- [ ] 6.4 `knee.objects.outline.pull_taut(points, leeway_mm, area_tiles, topology) -> (outline,
  shed)`: the thesis §6.1's three pulls, each a pure step, with the leeway from the flicker at the
  light divided by the slope across the band; verify the outline keeps the tile territory's area
  within one tile and its topology, that no point moves farther than its leeway, and that a
  dumbbell with a waist deeper than the leeway keeps its waist.
- [ ] 6.5 Picture: boundary points by outcome and the taut outline over the plane, the strip
  visible, silence elsewhere; a view-sheet panel.
- [ ] 6.6 **E4 (his).** The native boundaries and outlines on the chosen slices: he confirms the
  lines are where the bones end, or names the pattern the lens misses.

## 7. The facing pairs

- [ ] 7.1 `knee.relations.facing.facing_code(sites, gap_sites, minimum_sites, both_selected) ->
  str`, pure, pinned; `read_facing(dome, selection, minimum_sites) -> FacingPairs` over
  `boundary_census` and `boundary_edges` on the tile labels; verify on the coronal that the two
  big objects face with `gap_tiles` on the dark line, that two objects touching without a gap are
  `touching_no_gap`, and that an unselected territory is never in a facing pair.
- [ ] 7.2 Picture: each facing pair's gap tiles drawn between its objects; a view-sheet panel.

## 8. The interstices, and the round-2 objects inside them

- [ ] 8.1 `knee.relations.interstice.read_interstices(facing, strips, conjunction, plane,
  lateral_sign) -> tuple[InterstitialRecord]` with extent, walls (`wall_code`, pure, pinned), fill
  (`fill_code`, pure), contents as round-2 objects with `position_code`, and `side_code` (pure,
  pinned); verify a pair with one unbracketed wall records the wall `unreadable` and never a zero
  gap, that contents are read only inside the extent, that a sagittal big pair yields a `central`
  content where the dark band runs between the bones, that side codes abstain without the witness,
  and that `relations.code` leaves `construction_absent` for the first time on the real study.
- [ ] 8.2 Replace the shell: `knee.relations.shell.read_relations` returns the constructed
  interstices and keeps the pairings record beside them; verify `test_relations_shell` is updated
  with both signs and the receipt carries both records.
- [ ] 8.3 Picture: each interstice between its objects with its walls' codes and contents outlined;
  a view-sheet panel.

## 9. The spans and the envelope: round 3

- [ ] 9.1 `knee.relations.spans.read_spans(conjunction, selection, interstices, lateral_sign) ->
  tuple[Span]`; verify a span touches both big objects' territories, lies outside every
  interstice, and carries a side code or its abstention.
- [ ] 9.2 `knee.relations.envelope.read_envelope(conjunction, interstices, selection) -> Envelope`
  with tiles, outline, `posterior_pouch` and `neck_tiles`; verify the envelope is connected to an
  interstice's extent, that its tile count exceeds the union of the interstices' gap tiles on the
  sagittal fat-dark chosen slice, and that a posterior component with no connection is kept as a
  separate named record, never merged.
- [ ] 9.3 Picture: spans and envelope over the plane by index; a view-sheet panel.
- [ ] 9.4 **E5 (his).** The interstices with their walls, fill and contents, the spans and the
  envelope: he confirms the spaces and what is in them, or names what the round missed.

## 10. Ownership and the residual

- [ ] 10.1 `read_ownership` over the combined tile label map of rounds 1 to 3, round order
  deciding a disputed tile with the dispute kept; verify every tile inside the leg is owned or
  `unassigned`, that the residual's conjunction codes are counted, and that no round deletes a
  claim.
- [ ] 10.2 Picture: the residual over the plane; a view-sheet panel.

## 11. Bundles, predicates, output

- [ ] 11.1 `read_bundles` keyed on the funnel's objects: tile digits per object, strip digits where
  made, the conjunction counts, lineage (`came_out`: the round and the rule); verify unavailable
  banks are named and never zeroed.
- [ ] 11.2 `read_findings` selects each subject by role and side code as `design.md` R11 states;
  verify every one of the twelve names the role it read or the role it lacked, and that no
  predicate's scope is the whole field.
- [ ] 11.3 Contusion's interior reading: the object's tile digits and their variance as the
  measurement; native digits inside the object only when this predicate asks, scoped to the object;
  verify the native pass is never run unasked and never outside the object. His ruling stands:
  whether the squint suffices is found when diagnosis is attempted.
- [ ] 11.4 Output unchanged: the companion record every run; rows refused while the projection is
  undeclared; verify the receipt carries every new record.

## 12. The pictures

- [ ] 12.1 One arrangement in `knee.pictures` per new record (R0 to R10), each only arranging;
  `test_a_stage_is_not_built_until_it_renders` and `test_no_stage_imports_the_drawing_layer` keep
  passing.
- [ ] 12.2 One panel per new record on the view sheets, in route order, silent readings saying so
  in their own panel; verify `all_frames` draws every drawing on the one study.

## 13. The route

- [ ] 13.1 `AnalysisRequest` gains `strip_mm`, `prominence_tile_mm`, `minimum_valid`,
  `half_tile_mm` and `whole_field: bool = False`, each validated with a named refusal; verify the
  defaults are the constants of `design.md` §3 and that each carries its provenance in the
  docstring.
- [ ] 13.2 `run_study` in the funnel's order (`design.md` §1), each operation consuming only kept
  records, the whole-field forms called only under `whole_field=True`; verify
  `test_pipeline_composition` over the synthetic corpus that every producer has a consumer and
  every consumer a producer in the new order, that the first lens precedes every reader of the
  leg, that the line-up precedes the first lens where a pair exists, and that nothing reads a
  slice outside the chosen set.
- [ ] 13.3 `ROUTE` standings updated honestly per stage; `just unit` prints the new loop; `docs/
  PIPELINE.md` and `docs/BUILD_PLAN.md` describe the funnel; `docs/places.json` declares every new
  module; verify `just places`, `just imports`, `just graph` and `just gate` pass.
- [ ] 13.4 The one-study run through `just analyze-objects` with every new record saved and every
  picture drawn, the receipt composing; verify `just composition` on the run.
- [ ] 13.5 Counted work: the funnel's budget per series beside the whole-field route's on the same
  study, both from the ledger, profiler behaviour reported separately; verify the record is in the
  chapter's measurements with the date and commit.

## 14. The 58, as engineering

- [ ] 14.1 The funnel over the 58 through the real entry point: per view, the first lens's codes
  tabulated; the chosen slices; the selection codes per plane kind; the facing pairs; the
  interstices' wall codes; reported identified / abstained / unreadable per class, never one
  number.
- [ ] 14.2 Where a view fails his eye on the one study or a class fails on the 58, the fix is
  declared here as a new task with its provenance before it is written.
