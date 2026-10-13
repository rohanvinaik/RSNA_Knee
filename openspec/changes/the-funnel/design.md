# Design: the funnel

Provenance: the founder's words of 2026-10-12 and 2026-10-13, verbatim in
`docs/chapters/02-collapse/teachings.md` ("THE FUNNEL", "THE SQUINT LINES THE FREE LENSES UP",
"his answers to the five questions"); the thesis §1.3, §1.5, §1.9, §1.11, §4, §4.5, §4.6, §5.1,
§5.2, §5.4, §5.6, §6.1, §6.2, §7.3, §13.6, §13.7 (quoted with line numbers in
`docs/chapters/02-collapse/readings/the-funnel-plan-lead-20261013.md` and
`workbench/consults/the-funnel-plan-prompt-20261013.md`); the Codex consult of 2026-10-13
(`readings/the-funnel-plan-codex-20261013.md`), whose four provable corrections and two additions
are taken; the code maps mined 2026-10-13 (the scratchpad's `mine-study-collapse.md`,
`mine-lenses-objects.md`, `mine-thesis-collapse.md`), which name what exists. The settled record
(`docs/OBJECT_MODEL.md`, `docs/PIPELINE_AS_OBJECT.md`, `docs/STAGE_CONTRACT.md`) is not reopened.

## 1. The decision

The route is a funnel. In order, per study:

```
0  study        the series, their geometry in mm, the same-orientation pairs
1  squint       every slice of every series as mm tiles, each tile's centre in the scanner's mm
2  first lens   per tile per slice: background | leg | undecided; frozen; the senior filter
3a line-up      per pair: for each tile of one acquisition, the tile of the other at the same mm
3b tile digits  per series: one digit per leg tile against the terciles of the leg tiles
3c conjunction  per pair: the ordered pair of digits at each tile, as a named code
4  depth        per series: cheap readings per slice; each lens stands at its peak slice
   ---- everything below runs only on the chosen slices, only inside the leg ----
5  tile dome    distance from the obstacles over the tiles; peaks by prominence; territories
5b selection    objects from territories by structural facts; the laterality sign
6  strip        the native edge, in a strip along each object's tile boundary; the outline
7  facing       pairs of selected objects that face across gap tiles
8  interstice   per facing pair: extent, walls, fill, contents -> round-2 objects
9  spans, envelope                                              -> round-3 objects
10 ownership    every tile owned or unassigned; the residual
11 bundles, predicates, output
```

Each numbered row is one or a few compute operations, each a pure function of kept readings,
parallel over series, tiles or objects, computed once and consulted. The nine route packages keep
their names; the operations live inside them (`study`: 0; `collapse`: 1, 2, 3a, 4; `lenses`: 3b,
3c; `objects`: 5, 5b, 6; `relations`: 7, 8, 9; `ownership`: 10; `vectors`, `predicates`,
`output`: 11).

## 2. The records, in order

Every array states shape, dtype, axis order, units and frame. Z is the slice index in stack order;
TR, TC the tile rows and columns; R, C the native rows and columns. Named codes are tuples on the
module that decides them. "Exists" names the symbol reused; "new" is written under this change.

**R0 `AcquisitionPairs`** (`knee.study.pairs`, new). Per study: `pairs: tuple[(uid_a, uid_b,
plane, code)]`, from `SeriesRow.anatomical_plane`, `fluid_sensitive`, `fat_suppression` (the
competition's own flags, told). Pure decision `pair_code(n_bright: int, n_dark: int) -> str` over
`PAIR_CODES = ("paired", "solitary", "surplus", "none")`: exactly one of each flavour is `paired`;
one series of a plane is `solitary`; more than two is `surplus` (all kept, none paired); no series
of a plane is `none`.

**R1 `SquintStack`** (`knee.collapse.squint_stack`, new orchestration over existing
`knee.collapse.physical.physical_squint(plane, spacing_rc, tile_mm)` and
`knee.collapse.physical.PlaneFrame.from_dicom / to_patient`). Per series: `median, minimum,
maximum, coverage: float64 (Z, TR, TC)`; `centres_lps: float64 (Z, TR, TC, 3)` mm, the LPS
position of each tile's centre; `bounds_rc: int64 (TR, TC, 4)` half-open native bounds;
`tile_shape_rc`; `tile_mm`; `code` from `("present", "no_stacked_volume", "geometry_unreadable")`.
Empty tiles NaN. Picture: the squint over the acquired plane at the walk slices.

**R2 `FirstLens`** (`knee.collapse.first_lens`, new). Per series: `codes: uint8 (Z, TR, TC)` over
`TILE_CODES = ("background", "leg", "undecided", "tile_empty")`; `split: float` (the series' own
valley, `RegimeKey.background_split`, exists); `why`. Measurement: `all_dark = maximum <= split`;
`air = all_dark tiles four-connected (within the slice) to the picture's border`. Pure decision
`tile_code(all_dark: bool, any_dark: bool, air_connected: bool, beside_air: bool, finite: bool)
-> str`: not finite -> `tile_empty`; all_dark and air_connected -> `background`; any_dark and
(beside_air or touches the border) and not all_dark -> `undecided`; else `leg`. A dark tile not
connected to the border (a dark interior) is `leg`. The record is frozen: computed once, saved,
handed to every later operation; nothing later reads a `background` tile; `undecided` and `leg`
tiles both go on (Codex's first correction: silence settles nothing). Picture: tiles by code over
the acquired plane, per view, at the walk slices. His check, per view: no background tile holds
any part of the knee.

**R3a `LineUp`** (`knee.collapse.lineup`, new; uses `centres_lps` and `SeriesGeometry.along_normal`,
exist). Per pair, from the fat-dark series as recipient: `partner_slice: int64 (Z,)`, the partner
slice nearest along the normal; `slab: uint8 (Z,)` over `("in_slab", "nearest_only", "no_partner")`
(within half the recipient slice thickness or not); `partner_tile: int64 (Z, TR, TC, 2)`, the
partner tile whose centre is nearest in mm; `distance_mm: float64 (Z, TR, TC)`; `codes: uint8` over
`MATCH_CODES = ("matched", "beyond_half_tile", "partner_unavailable")`. Pure decision
`match_code(distance_mm, half_tile_mm, partner_exists) -> str`. Geometry only; no population,
so it precedes R2 in dependency terms and R2 reads one squint per series (Codex's second
correction: no cycle). Picture: the recipient's tile grid with the partner's tile centres drawn
over it, both over the recipient plane.

**R3b `TileDigits`** (`knee.lenses.tiles`, new; reuses `knee.lenses.places.place_codes_reference`
and `knee.lenses.digits.digit_code`, exist, and the tercile rule now private in
`knee.collapse.regime._shape_readings`, made public as `tercile_edges(values, minimum_population)
-> (low, high, count)`, one rule). Per series: population = the medians of every `leg` tile over
the whole series; `low_edge, high_edge, count`; `digits: int8 (Z, TR, TC)` with -1, 0, +1 and 2
for silence, where `background` and `undecided` tiles are handed NaN and so read `place_unread`.
His answer settles the population: "the terciles over the leg tiles". Picture: the digit grid over
the plane, silence drawn as silence.

**R3c `Conjunction`** (`knee.lenses.conjunction`, new). Per pair, per recipient tile: the ordered
pair (digit of the fat-bright partner tile, digit of the fat-dark tile) as one code from
`CONJUNCTION_CODES`, the nine ordered pairs named by their digits (`above_below`, `at_at`,
`below_below`, ...) plus `("partner_silent", "self_silent", "unmatched")`. Pure decision
`conjunction_code(partner_digit: int, own_digit: int, match: str) -> str`. The names carry no
tissue word; the design glosses (`above_below` is fat; `below_below` is cortex, tendon, ligament,
meniscus; `*_above` on the fat-dark is fluid-like) live here and in `docs/OBJECT_MODEL.md`, never
in a record. A solitary series has no conjunction (`unmatched` everywhere). Picture: the
conjunction code as colour over the recipient plane.

**R4 `DepthCollapse`** (`knee.collapse.depth`, new). Per series, over the squint stack: four cheap
readings per slice, each a lens in the thesis's sense, `float64 (Z,)` with NaN for silence:
`leg_share` (leg tiles over all tiles), `dark_share` (tiles with median at or below the split, over
leg tiles; the thesis's own Dark Share), `split_quality` (Otsu's between-group share over the leg
tiles' medians; the thesis's own), and, where a pair exists, `fat_share` (`above_below` tiles over
matched leg tiles). Pure decision `chosen_slice(readings: tuple[float, ...], minimum_valid: int)
-> (index | None, code)` over `CHOICE_CODES = ("chosen", "tie_middle", "all_silent",
"too_few_valid")`: the slice where the reading peaks; an exact tie takes the middle of the tied
run; fewer than `minimum_valid` finite readings abstains. The chosen slices (one per lens, deduped)
are the series' flat pictures; nothing below reads any other slice in full. The cell build's
literal rule is traced in task 4.4 and reconciled before this unit is admitted. Picture: the four
readings as curves over Z with each lens's chosen slice marked, and the chosen slices themselves.
His check: the chosen slices, per view.

**R5 `TileDome`** (`knee.objects.tile_dome`, new; reuses `knee.objects.interiors.prominent_peaks`
and the watershed call of `read_interiors`, refactored into one shared `dome(interior: bool (H,W),
spacing: (float, float), prominence_mm) -> (height, peaks, labels)` used at both scales). Per
series, per chosen slice: `obstacle: bool (TR, TC)` = `background` ∪ `undecided` ∪ (paired:
`below_below` tiles; solitary: tiles with median at or below the split); `interior` = leg tiles
not obstacle; `height: float64 (TR, TC)` mm, the Euclidean distance from the nearest obstacle or
frame; `peaks: int64 (P, 2)` tile rc; `labels: int32 (TR, TC)`, 0 where unseeded; `peak_height_mm
(P,)`. Prominence is `prominence_tile_mm`. Picture: territories and peaks on the squint over the
plane.

**R5b `Selection`** (`knee.objects.selection` and `knee.objects.laterality`, new; reuses
`knee.collapse.structure.superior_code` and the LPS axes). Per series, per chosen slice: per
territory the facts `tiles: int`, `centre_lps (3,)`, `extent_superior_mm`, `touches_leg_border:
bool`, `ringed: bool` (enclosed by `below_below` or obstacle tiles on all sides), `superior_rank`,
`anterior_rank`, `left_right_mm`. Pure decisions, one per view kind (the kind is
`SeriesRow.anatomical_plane`, told): `big_pair_code(areas, superior_positions, minimum_tiles) ->
str` over `("selected", "one_big_only", "tie", "none")`, naming the two largest territories
`superior_big` and `inferior_big`; `anterior_small_code(...)` on the sagittal: the territory
anterior to `superior_big`'s inferior end and smaller than it -> `anterior_small`;
`lateral_witness_code(...)` on the coronal: a small ringed territory inferior to `inferior_big`'s
superior face -> `lateral_small_ringed`, whose side along the frame's left-right axis is the
`lateral_sign` (`OBJECT_MODEL.md`, laterality); `axial_code(...)` on the axial: the largest
territory -> `central_big`, the territory anterior to it -> `anterior_small`. Every other
territory is `unselected` and kept. An object record is `(index, role_code, facts, tiles)`; the
role codes are structural words, never anatomy. His answer settles that each view has its own rule
and nothing is carried between views. Picture: territories by role code with the facts written
beside each index.

**R6 `Strip`** (`knee.objects.strip`, new; reuses `knee.objects.profiles.sample_profiles`,
`knee.objects.interiors.dark_bands`, `knee.objects.conversation.exchange`, `place_codes_reference`,
exist). Per object: `edge_points: float64 (N, 2)` native rc at the midpoints of the object's tile
boundary segments, `normals (N, 2)` outward; profiles cast at native resolution at offsets spanning
`±strip_mm`; `codes (N,)` over `TRACE_CODES` (exist); `band_mm (N, 2)` for bracketed rows; the
partner's bands transported to the same points through `exchange` where a pair exists, with
`EXCHANGE_CODES` (exist); `native_digits` for the strip's pixels against the terciles of the
object's own pixels (his answer: "then each object's own places"); `strip_mask: bool (R, C)`.
Nothing outside the strip is read at native resolution, except inside an object when a predicate
asks (task 11.3). Then `knee.objects.outline` (new, the thesis §6.1): the boundary pulled taut by
the three pulls with a leeway from the flicker, returning `outline (M, 2)` and `shed` places.
Picture: the native boundary points by outcome and the taut outline over the plane, the strip
visible, silence elsewhere.

**R7 `FacingPairs`** (`knee.relations.facing`, new; reuses `knee.objects.boundaries.boundary_census`
and `knee.objects.interiors.boundary_edges` on the tile labels, exist). Per series, per chosen
slice: for each pair of selected objects, `sites: int` (four-adjacent tile crossings),
`gap_tiles: bool (TR, TC)` (obstacle tiles touching both), `saddle_mm`; pure decision
`facing_code(sites, gap_sites, minimum_sites, both_selected) -> str` over `("facing",
"touching_no_gap", "not_selected", "too_few_sites")`. This is Codex's third correction: the
producer the plan lacked. Picture: each facing pair's gap tiles drawn between its two objects.

**R8 `Interstice`** (`knee.relations.interstice`, new, replacing the construction-absence shell of
`knee.relations.shell` while keeping `Interstice(kind, first, second, series_uid, provenance)` and
`KINDS`, exist). Per facing pair: `extent: bool (R, C)` native, the pixels between the two objects'
bands along the shared normals plus the gap tiles' pixels; `walls`: per side, per profile, the
digit sequence from the object's band outward, read into `WALL_CODES = ("plate_layer_fill",
"plate_fill", "unreadable")` by `wall_code(sequence) -> str` (plate = the dark band; layer = an
intermediate run before the fill); `fill_code(counts) -> str` over the conjunction codes present in
the extent; `contents`: four-connected bodies of `below_below` pixels inside the extent, each a
round-2 object `(index, "content", pair_index, position_code)` with `position_code` over
`("peripheral", "central")` by its distance from the leg border along the pair's axis; `side_code
(position_left_right, lateral_sign) -> str` over `("medial", "lateral", "side_abstained")`.
Picture: each interstice drawn between its two objects with its walls' codes and its contents
outlined.

**R9 `Spans` and `Envelope`** (`knee.relations.spans`, `knee.relations.envelope`, new). Spans: four-
connected bodies of `below_below` tiles outside every interstice that touch both big objects'
territories, with `side_code`; role `span`. Envelope: the four-connected component of fat-dark
`above` tiles (fluid-like) adjacent to any interstice's extent, with `tiles`, `outline`, and
`posterior_pouch`: its tiles posterior to the big objects' posterior faces, with the narrowest
connection width in tiles as `neck_tiles`; role `envelope`. Round 3. Picture: spans and envelope
over the plane by index.

**R10 `Ownership`** (`knee.ownership.claims.read_ownership`, exists, applied to the tile label map
of every object of rounds 1 to 3). `residual: bool (TR, TC)` with the conjunction codes of the
residual tiles counted. Picture: the residual.

**R11 bundles, predicates, output** (`knee.vectors.bundles.read_bundles`,
`knee.predicates.findings.read_findings`, `knee.output.projection.read_output`, exist). The bundles
count the tile digits and the strip digits per object. The predicates select subjects by role and
side codes: Fracture and Contusion on `superior_big`, `inferior_big`, `anterior_small`,
`lateral_small_ringed` (Contusion reads the object's interior digits at tile scale, and at native
scale inside the object only when it asks: his answer, "we shall see"); Medial, Lateral and PF OA
on the facing pairs' walls by side (PF = the pair with `anterior_small`); the Menisci on
`peripheral` contents by side; ACL on the `central` content of the sagittal's big pair; MCL on the
`medial` span; Effusion, Synovitis and Baker's on the envelope (fill, lining, `posterior_pouch`),
with the post-contrast flag from the regime. Every decision a named code with its reason; the
expected reading `e` and the numeric projection stay his to declare.

**R12 pictures.** One arrangement in `knee.pictures` per new record, arranging values only, and one
panel per new record on the view sheets (`workbench.render.view_frames`), so the five sheets he
reads show every reading of the funnel in route order.

**R13 the route.** `knee.pipeline.run_study` in the order of §1. `AnalysisRequest` gains the bars
of §3 as arguments. The whole-field forms (`read_structure`'s air and leg, basins, seam and bodies;
`read_lenses` over the volume; `measure_series`' whole-plane interiors, traces and conversation;
the sampled pairings) stay in the tree, callable through a `whole_field: bool = False` request
flag and drawable from a saved run; the route does not call them by default. `ROUTE` reports each
stage's standing honestly.

## 3. The design constants, each an argument with its provenance

| constant | value proposed | provenance | who changes it |
|---|---|---|---|
| `tile_mm` | 8 | his "16x16 grid" on "256x256" at about half a millimetre a pixel; the lead's arithmetic | him, by eye |
| `half_tile_mm` (line-up match) | `tile_mm / 2` | a tile centre nearer than half a tile is the same patch; the lead's | him |
| `strip_mm` | 6 | twice the native prominence the saved runs used (3 mm), so the strip holds the dark band and a tile's rounding; the lead's | him, by eye |
| `prominence_tile_mm` | 16 | two tiles: a peak must stand two tiles above its saddle at the squint; the lead's | him, by eye |
| `prominence_native_mm` | 3 | the saved runs (`codex-closeout-review-jit-20261012`) | him |
| `minimum_sites` | 1 | the existing default of `boundary_census` | him |
| `minimum_valid` (depth lenses) | 8 | a lens needs eight slices with a reading to stand anywhere; the lead's | him |
| `minimum_population` (terciles) | `RegimeKey.tercile_minimum_population` | exists | him |
| `offsets_mm` (strip profiles) | every pixel from `-strip_mm` to `+strip_mm` | the strip's own width | follows `strip_mm` |

Each is declared with the general pattern it encodes, per his ruling on fitting (2026-10-12):
a constant found by looking is legitimate when the rule it serves describes how the anatomy
presents in images generally; the guard is him. None is chosen to separate gold.

## 4. Where every choice Codex named is settled

Codex's §2 list (`readings/the-funnel-plan-codex-20261013.md`), item by item:

- *Across stages* (measurement/decision boundaries; argument and provenance contracts; named
  outcomes for missing, empty, malformed or conflicting inputs; ties; which exclusions have
  authority for which consumers; what a visually accepted step is): the unit loop of
  `docs/STAGE_CONTRACT.md` per task; only `background` excludes; a step is accepted when his
  eye-check (§5) passes on the one study.
- *Step 0*: pairing from the competition's own flags; `surplus` and `none` named; the post-contrast
  flag stays the regime's (`normalization_code`, exists) and is a founder item where it is silent.
- *Step 1*: tile size (§3); grid origin the picture's corner (as `physical_squint` has it); partial
  tiles keep their true coverage (exists); every slice.
- *Step 2*: population the whole stacked volume (exists); an absent valley is `split_unavailable`
  and the lens abstains on the series; connectivity four-connected within the slice; mixed tiles
  `undecided` (his answer 1); `frozen` means computed once per series and saved, the rule itself
  being the same for every series until his eye says a view needs its own; acceptance is per view
  on the one study, then the 58 as engineering.
- *Step 3*: ties by first in scan order and recorded; unmatched tiles named; the leg mask is the
  recipient's; terciles over the series' leg tiles (his answer 4); the table reads what the two
  acquisitions supply and abstains on the rest; no other orientation participates (his answer 2).
- *Step 4*: the obstacle set and the interior as in R5; prominence as in §3; ties in area by
  superior position, recorded; missing or surplus territories named by the selection codes; the
  axial has its own rule (his answer 2); identity across slices is not asked, since only chosen
  slices are read (his answer 5).
- *Step 5*: strip width (§3); the outline preserves the area and topology of the object's tile
  territory; concurrence and disagreement with the partner kept by `EXCHANGE_CODES` (exist).
- *Step 6*: the facing-pair graph is R7; extent, walls, fill and contents as in R8; menisci are
  `peripheral` contents and cruciates `central`, by position only; laterality by R5b's sign; the PF
  control is the other facing pairs of the same study, recorded as such.
- *Step 7*: spans and the envelope as in R9; a broken or missing structure is a named absence of
  the role, never a zero.
- *Step 8*: claims are exclusive per tile by round order (round 1 first); disputes kept
  (`read_ownership`, exists); pull-out between rounds is the claim itself; termination when a
  round claims nothing.
- *Step 9*: counts over tiles and, where made, strip pixels, keyed as such; subjects by role and
  side codes; an unresolved subject abstains with the role it lacked.

## 5. What goes in front of him, in order (the eye-checks)

Each is the smallest set of pictures whose confirmation makes the next units generative. The
build pauses at each until he has looked.

| after | he looks at | he confirms |
|---|---|---|
| R2 | five sheets, one per view: the tiles by code over the plane | no background tile holds knee; the undecided ring is where the skin is |
| R4 | per view, the four readings over Z and the chosen slices | the chosen slices are the ones to read |
| R5, R5b | per chosen slice, the territories by role with their facts | the two big ones, the small anterior one, the small ringed one are what they should be |
| R6 | the native boundaries and outlines | the lines are where the bones end |
| R8, R9 | the interstices with walls, fill and contents; spans; envelope | the spaces and what is in them are right |

## 6. What stays, and what is off the route

Every lens that exists stays (his ruling: "Keep all"). The whole-field forms are not deleted, not
archived, and not on the default route; they run under `whole_field=True` and draw from a saved
run. The old view-sheet panels remain drawable; the new panels join them.

## 7. Who writes what

Under his 2026-10-11 authorization, a sub-agent or a workflow may write a unit's body, its
renderer, its serializer and its characterization tests, and run the gate; the lead writes the
module docstring against the thesis, the pure decision's contract, the two-sign intent tests, the
bars and their provenance, judges every Detective survivor, wires the unit into the route and
admits it; he looks at each eye-check and rules on every constant marked his. A body lands only
with its certificate and after the lead has read it.
