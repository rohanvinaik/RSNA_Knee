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
2  first lens   per tile per slice: background | not_background | undecided; frozen; the senior filter
3a line-up      per pair: for each tile of one acquisition, the tile of the other at the same mm
3b tile digits  per series: one digit per kept tile against the terciles of the kept tiles
3c conjunction  per pair: the ordered pair of digits at each tile, as a named code
4  depth        per series: cheap readings per slice; each lens stands at its peak slice
   ---- everything below runs only on the chosen slices, only on tiles the first lens did not clear ----
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

**R0 `AcquisitionPairs`** (`knee.study.pairs`, new). Per study, one record per plane present in
the series table: `(plane, bright_uids, dark_uids, unreadable_uids, code)`, from
`SeriesRow.anatomical_plane`, `fluid_sensitive`, `fat_suppression` (the competition's own flags,
told). Pure decision `pair_code(n_bright: int, n_dark: int) -> str` over `PAIR_CODES = ("paired",
"solitary", "surplus", "none", "invalid_count")`: exactly one of each flavour is `paired`; one
series of a plane is `solitary`; more than two is `surplus` (all kept, none paired); a plane whose
every series has an unreadable flag is `none` (a plane absent from the table has no record at all);
a negative count is `invalid_count`, the refusal. (Brought to the packet as built, 2026-10-13: the
plan had said a pair-tuple record and four codes.)

**R1 `SquintStack`** (`knee.collapse.squint_stack`, new orchestration over existing
`knee.collapse.physical.physical_squint(plane, spacing_rc, tile_mm)` and
`knee.collapse.physical.PlaneFrame.from_dicom / to_patient`). Per series: `median, minimum,
maximum, coverage: float64 (Z, TR, TC)`; `centres_lps: float64 (Z, TR, TC, 3)` mm, the LPS
position of each tile's centre; `bounds_rc: int64 (TR, TC, 4)` half-open native bounds;
`tile_shape_rc`; `tile_mm`; `code` from `("present", "no_stacked_volume", "geometry_unreadable")`.
Empty tiles NaN. Picture: the squint over the acquired plane at the walk slices.

**R2 `FirstLens`** (`knee.collapse.first_lens`, new). Per series: `codes: uint8 (Z, TR, TC)` over
`TILE_CODES = ("background", "not_background", "undecided", "tile_empty")`; `split: float` (the
series' own valley, `RegimeKey.background_split`, exists); `why`. Measurement: `all_dark =
maximum <= split`; `air = all_dark tiles four-connected (within the slice) to the picture's
border`. Pure decision `tile_code(finite: bool, all_dark: bool, any_dark: bool, air_connected:
bool, beside_air: bool) -> str`: not finite -> `tile_empty`; all_dark and air_connected ->
`background`; any_dark and (beside_air or touches the border) and not all_dark -> `undecided`;
else `not_background`. A dark tile not connected to the border (a dark interior) is
`not_background`. The record is frozen: computed once, saved, handed to every later operation;
nothing later reads a `background` tile; `undecided` and `not_background` tiles both go on
(Codex's first correction: silence settles nothing). Picture: tiles by code over the acquired
plane, per view, at the walk slices. His check, per view: no background tile holds any part of
the knee. **The third word** was `leg` until 2026-10-13; the founder agreed that day that it said
more than the lens measured ("what the lens leaves is simply 'not background'": "Good."), and the
word changed with the stored index unchanged. **E1 passed the same day by his ruling** (tasks.md
2.4): the lens is right wherever it clears and clears as much air as there is; on the two
sagittals and the fat-bright coronal the knee fills the frame, the one-tile ring at the border
covers the margin, and the few corner tiles of air carried along are the buffer he accepted.

**R3a `LineUp`** (`knee.collapse.lineup`, new; uses `centres_lps` and `SeriesGeometry.along_normal`,
exist). Per pair, from the fat-dark series as recipient: `partner_slice: int64 (Z,)`, the partner
slice nearest along the normal; `slab: uint8 (Z,)` over `("in_slab", "nearest_only", "no_partner")`
(within half the recipient slice thickness or not); `partner_tile: int64 (Z, TR, TC, 2)`, the
partner tile whose centre is nearest in mm; `distance_mm: float64 (Z, TR, TC)`; `codes: uint8` over
`MATCH_CODES = ("matched", "beyond_half_tile", "partner_unavailable", "invalid_measurement")`.
Pure decision `match_code(distance_mm, half_tile_mm, partner_exists) -> str`; `slab_code` beside
it over `SLAB_CODES`. Geometry only; no population, so it precedes R2 in dependency terms and R2
reads one squint per series (Codex's second correction: no cycle). **`beyond_half_tile` is a
reading kept, never a refusal**: the conjunction (R3c) reads the named partner tile whatever the
distance, and only `partner_unavailable` has nothing to read. The founder, 2026-10-13, confirming
the lead's restatement: "The half-a-tile bar is my invention. The distance is a reading to keep;
refusing the overlap on it was never your rule." On the one study's coronal pair the fat-bright
field is 10 mm narrower, so the recipient's outer ring of forty tiles carries that word with its
distance; each still names the partner tile whose footprint overlaps it. Picture: the recipient's
tile grid with the partner's tile centres drawn over it, both over the recipient plane.

**R3b `TileDigits`** (`knee.lenses.tiles`, new; reuses `knee.lenses.places.place_codes_reference`
and `knee.lenses.digits.digit_code`, exist, and the tercile rule now private in
`knee.collapse.regime._shape_readings`, made public as `tercile_edges(values, minimum_population)
-> (low, high, count)`, one rule). Per series: population = the medians of every tile the first
lens did not clear (`not_background` and `undecided`) over the whole series, with a finite median;
`low_edge, high_edge, population_count, minimum_population`; `codes: uint8 (Z, TR, TC)` indexing
`DIGIT_CODES` and `digits: int8 (Z, TR, TC)` with -1, 0, +1 and 2 for silence, where `background`
and `tile_empty` tiles are handed NaN and so read `place_unread`. Pure decision
`tile_population_code(tile_code) -> str` over `("counted", "cleared", "empty", "unknown_code")`.
His answers settle the population: "the terciles over the leg tiles" ("Yup, that should do",
2026-10-13 06:16Z) and, the same day, the lead's restatement he confirmed with "Good.": "They are
read over everything the lens did not clear ... The skin tiles stay in play. Only what was cleared
is never read again." Picture: the digit grid over the plane, silence drawn as silence.

**R3c `Conjunction`** (`knee.lenses.conjunction`, new). Per pair, per recipient tile: the ordered
pair (digit of the fat-bright partner tile, digit of the fat-dark tile) as one code from
`CONJUNCTION_CODES`, the nine ordered pairs named `<partner>_<own>` by their digits
(`above_below`, `at_at`, `below_below`, ...) plus `("partner_silent", "self_silent",
"unmatched")`, twelve over the readings, and `invalid_measurement`, the refusal outside that
domain. Pure decision `conjunction_code(partner_digit: int, own_digit: int, match: str) -> str`:
a refusal first; `unmatched` where the line-up named no partner tile (`partner_unavailable`, or
its own refusal); the recipient's own silence before the partner's; `matched` and
`beyond_half_tile` both read (R3a). The names carry no tissue word; the design glosses
(`above_below` is fat; `below_below` is cortex, tendon, ligament, meniscus; `*_above` on the
fat-dark is fluid-like) live here and in `docs/OBJECT_MODEL.md`, never in a record. The record
rides on the recipient; a solitary series and a partner carry none. Picture: the conjunction code
as colour over the recipient plane.

**R4 `DepthCollapse`** (`knee.collapse.depth`, new). Per series, over the squint stack: four cheap
readings per slice, each a lens in the thesis's sense, `float64 (Z,)` with NaN for silence:
`kept_share` (tiles the first lens did not clear, over tiles holding a finite pixel), `dark_share`
(kept tiles with median at or below the split, over kept tiles; the thesis's own Dark Share),
`split_quality` (Otsu's between-class share over the kept tiles' medians, exact over the sorted
values; the thesis's own Split Quality), and, where a conjunction rides on the series,
`above_below_share` (`above_below` tiles over tiles whose conjunction is one of the nine read
pairs; named `fat_share` until 2026-10-13, when its verifier caught a tissue word in a record
against R3c's own rule). Pure decision
`chosen_slice(readings: tuple[float, ...], minimum_valid: int) -> (index | None, code)` over
`CHOICE_CODES = ("chosen", "tie_middle", "all_silent", "too_few_valid", "invalid_measurement")`:
the slice where the reading is largest; an exact tie takes the middle of the tied slices (the lower
middle of an even count); fewer than `minimum_valid` finite readings abstains; a bar or a reading
that is not a number is the refusal. `read_depth(stack, first, conjunction | None, split,
minimum_valid)`. The chosen slices (one per lens, deduped) are the series' flat pictures; nothing
below reads any other slice in full. The founder, 2026-10-13, confirming the restatement: the cheap
number on every slice is how the thesis finds the one slice to read; "not every slice" is about
the expensive work. The cell build's literal rule is traced in task 4.4 and reconciled before this
unit is admitted. Picture: the four readings as curves over Z with each lens's chosen slice
marked, and the chosen slices themselves. His check: the chosen slices, per view.

**R5 `TileDome`** (`knee.objects.tile_dome`, new; reuses `knee.objects.interiors.prominent_peaks`
and the watershed call of `read_interiors`, refactored into one shared `dome(interior: bool (H,W),
spacing: (float, float), prominence_mm) -> (height, peaks, labels)` used at both scales). Per
series that reads objects (the fat-dark recipient of a paired plane, or a series whose plane is
not paired), per chosen slice, **per border**: `obstacle: bool (TR, TC)` = `background` ∪ the kept
tiles the border names; `cleared: bool (TR, TC)` the `background` tiles; `interior` = kept tiles
(`not_background` and `undecided` alike: the buffer at the skin stays in play, his ruling; the
first wording made `undecided` an obstacle and the Codex check of 2026-10-13 caught it) not
obstacle; `height: float64 (TR, TC)` mm, the Euclidean distance from the nearest obstacle or
frame; `peaks: int64 (P, 2)` tile rc; `labels: int32 (TR, TC)`, 0 where unseeded; `peak_height_mm
(P,)`; `border`. Prominence is `prominence_tile_mm`. **Withdrawn 2026-10-13 (§8, §9): the squint
localizes and draws no line, so no border is chosen at the squint; the code keeps both borders as
readings off the line-drawing path.** **The border, two members** (`BORDER_CODES`):
on a paired plane, `dark_on_both` makes a `below_below` tile an obstacle (the object model's row,
"cortex, tendon, ligament, meniscus: dark on everything"), and `edge_of_bright_partner` makes a
tile whose fat-bright partner digit was read and is not `above` an obstacle (the interior is the
body bright on the fat-bright, its border where that falls off); every silence leaves a kept tile
interior under both; on a solitary plane both read the series' split. Both are seated, his ruling
of 2026-10-12 ("we always keep information we compute ... keep everything, including where
things conflict"): measured on the one study at 8 mm the dark line between the two bones is
narrower than a tile, so `dark_on_both` leaves them one territory on most middle slices while
`edge_of_bright_partner` parts them on every middle slice of both paired views
(`docs/chapters/02-collapse/measurements/the-funnel-dome-border-20261013.md`); every stage below
is read once per dome and every record names its border; he chooses at E3. Picture: territories
and peaks on the squint over the plane, the two borders side by side.

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
exist). Per object, per border: `edge_points: float64 (N, 2)` native rc at EVERY native pixel along
the object's tile boundary segments (corrected 2026-10-13 from one point per segment midpoint,
which put the casts a tile apart and could miss a break between them: the Codex check and the
strip builder both caught it; his "fine-grained targeting and boundary-drawing" is at native
resolution), `normals (N, 2)` outward, `beyond_tiles (N, 2)` the tile each profile enters;
profiles cast at native resolution at offsets spanning `±strip_mm`; `codes (N,)` over
`TRACE_CODES` (exist); `band_mm (N, 2)` for bracketed rows; the partner's bands transported to
the same points through `exchange` where a pair exists, with `EXCHANGE_CODES` (exist): **not built
yet** (task 6.2: `exchange` needs both planes' frames, the partner's own split and its slab
thickness, and its design is open; until then a partner is refused by name and `exchange_codes`
is empty); `native_digits` for the strip's pixels against the terciles of the object's own pixels
(his answer: "then each object's own places"); `strip_mask: bool (R, C)`.
Nothing outside the strip is read at native resolution, except inside an object when a predicate
asks (task 11.3). Then `knee.objects.outline` (new, the thesis §6.1): the boundary pulled taut by
the three pulls with a leeway from the flicker, returning `outline (M, 2)` and `shed` places.
Picture: the native boundary points by outcome and the taut outline over the plane, the strip
visible, silence elsewhere.

**R7 `FacingPairs`** (`knee.relations.facing`, new; reuses `knee.objects.boundaries.boundary_census`
and `knee.objects.interiors.boundary_edges` on the tile labels, exist). Per series, per chosen
slice, per border: for each pair of selected objects, `sites: int` (four-adjacent tile
crossings), `gap_tiles: bool (TR, TC)`: the four-connected chains of dark obstacle tiles (an
obstacle the first lens did not clear, never the air) between the two objects that touch both, so
a gap two or three tiles wide counts (corrected 2026-10-13 from "obstacle tiles touching both"
on the Codex check), `saddle_mm`; pure decision `facing_code(sites, gap_sites, minimum_sites,
both_selected) -> str` over `("facing", "touching_no_gap", "not_selected", "too_few_sites")`.
This is Codex's third correction: the producer the plan lacked. Open: the "between" region is
the lead's projection rule, and its checker showed it can empty under a strongly tilted pair;
it is checked on the real run before E3 and loosened only if it fires. Picture: each facing
pair's gap tiles drawn between its two objects.

**R8 `Interstice`** (`knee.relations.interstice`, new, replacing the construction-absence shell of
`knee.relations.shell` while keeping `Interstice(kind, first, second, series_uid, provenance)` and
`KINDS`, exist). Per facing pair, per border: `extent: bool (TR, TC)` at tile scale (the packet as
built; this line said native pixels until 2026-10-13), the gap tiles together with every kept tile
between the two territories, never a cleared one; `walls`: per side, per profile, the
digit sequence from the object's band outward, read into `WALL_CODES = ("plate_layer_fill",
"plate_fill", "unreadable")` by `wall_code(sequence) -> str` (plate = the dark band; layer = an
intermediate run before the fill); `fill_code(counts) -> str` over the conjunction codes present in
the extent; `contents`: four-connected bodies of `below_below` pixels inside the extent, each a
round-2 object `(index, "content", pair_index, position_code)` with `position_code` over
`("peripheral", "central")` by its distance from the leg border along the pair's axis; `side_code
(position_left_right, lateral_sign) -> str` over `("medial", "lateral", "side_abstained")`.
Picture: each interstice drawn between its two objects with its walls' codes and its contents
outlined.

**R9 `Spans` and `Envelope`** (`knee.relations.spans`, new). Spans: four-connected bodies of
`below_below` tiles outside every interstice that touch both big objects' territories, with
`side_code`; role `span`; with no interstice present on the slice the spans abstain
(`predecessor_absent`), since a body inside a space cannot then be told from a span. Envelope:
the four-connected component of fat-dark `above` tiles (fluid-like) adjacent to any interstice's
extent, with `tiles`, `outline`, and `posterior_pouch`: its tiles posterior to the big objects'
posterior faces, with the narrowest connection width in tiles as `neck_tiles`, counted only over
components joining the pouch to the rest; `unjoined`, every fluid-like component touching no
interstice, kept beside the envelope and never merged; role `envelope`. Both per border. Round 3.
Picture: spans and envelope over the plane by index.

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
| `prominence_tile_mm` | 8 | one tile. At 8 mm tiles the distance map's height at a bone's centre is about half its width, so the patella (20 to 25 mm) and the fibula's head (15 to 20 mm) stand 8 to 12 mm; a two-tile floor would hide both, and the fibula is the laterality sign. The thesis's law: "Nothing is cut on strength, so a bright nucleus never silences a dim one" (§6.2); the selection facts pick the objects, extra peaks are kept. Corrected 2026-10-13 from the lead's first proposal of two tiles, on a side agent's arithmetic relayed by the founder | him, by eye |
| `prominence_native_mm` | 3 | the saved runs (`codex-closeout-review-jit-20261012`) | him |
| `minimum_sites` | 1 | the existing default of `boundary_census` | him |
| `minimum_tiles` (selection) | 4 | four tiles at 8 mm is 32 mm across, below any big object and above a speck; the lead's (`knee.objects.selection.MINIMUM_TILES`) | him, by eye |
| `border` (dome) | both, `dark_on_both` and `edge_of_bright_partner` | two members seated, never one chosen (R5) | him, at E3 |
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
- *Step 3*: ties by first in scan order and recorded; unmatched tiles named; the distance is a
  reading and never a refusal (his ruling of 2026-10-13); the kept mask is the recipient's;
  terciles over the series' kept tiles (his answer 4, and "everything the lens did not clear",
  2026-10-13); the table reads what the two acquisitions supply and abstains on the rest; no other
  orientation participates (his answer 2).
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
| R2 | five sheets, one per view: the tiles by code over the plane | no background tile holds knee; the undecided ring is where the skin is. **Passed 2026-10-13 by his ruling** (tasks.md 2.4) |
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

## 8. The two processes (2026-10-13, his correction; supersedes R4's readings and R5 to R9's scale)

His words (`docs/chapters/02-collapse/teachings.md`, "THE TWO PROCESSES"): "The "squint" is for
localization of the expensive compute process, not for drawing a line strongly. The other
operation is for fine-drawing of borders. 8mm tiles can't refine the border because that was never
their job." The thesis says the same: the cheap readings "point, and never decide alone ... It
narrows where the expensive work runs" (§5.1); the squint's bodies "lie on the cells" (§4.6); the
border is drawn at full resolution, "no border is known more finely than the flicker" (§6.1). What
R5 to R9 got wrong, and why: they drew lines at 8 mm (a dome split by a tissue rule, a gap from
tile projections, menisci, cruciates and the inner-side line as dark tiles), and R13 took the
common-sense localization (the two basins and the seam from the header's axis) off the default
route. The lead's reading of the pictures, structure by structure, is
`docs/chapters/02-collapse/readings/the-funnel-common-sense-pass-lead-20261013.md`.

**Process 1, the squint: where each structure is** (tile scale, every slice, cheap; points and
never decides alone; with buffer, his "some buffer is perfectly fine"):

- the leg: the first lens (R2, built);
- the two halves and the band between them, by the header's up-down axis on a view whose plane
  holds that axis (coronal, sagittal): the basins and the seam, run on every slice; on the axial
  the up-down axis is the stack, so the band is the run of slices at the joint;
- the slices to read, by where the structures sit: the slices where the band crosses the leg (the
  two bones and the joint), each compartment's slices, the middle slices (the patella, the notch,
  the pouch above the patella); each structure stands at its own slices, as each lens stands at
  its own sharpest slice in the thesis;
- the places of the rest by their fixed position relative to the halves and the band: the
  patella (the bright body in front of the lower end of the upper half, above the band), the
  fibula head (the bright body below the outer end of the lower half, toward the back), the notch
  (the middle of the band between the two rounded ends), the compartments (the band either side
  of the notch), the pouches (bright on the fat-dark: above the patella in front of the upper
  half; behind the knee on the inner side);
- the side: the outer side is where the fibula head is.

**Process 2, the high-resolution lenses: the border, drawn only in those places** (native pixels):

- each bone's edge, densest where it faces the band (the strip, R6, one cast per boundary pixel);
- the band's walls (plate, layer, fill: R8's wall code over native profiles across the band);
- what lies in the band: the menisci (the dark wedges at its ends), the cruciates (the dark bands
  crossing the notch); the patellofemoral band's walls;
- the inner-side line along the band's height, outside it;
- the fluid's edge in each pouch, its fill, the posterior pouch, and the lining where the
  post-contrast flag says contrast was given;
- each bone's inside, where a finding asks (contusion, fracture).

**The twelve** read off what process 2 drew, each a named code with the measurement it read; the
numeric projection and the expected readings stay his.

Every lens and unit already built stays (his "Keep all"); the tile-scale units of R5 to R9 stay in
the tree as squint readings and off the line-drawing path. The two-border seating of R5 is
withdrawn. The exact rule of each piece is written with the substrate's facts in hand, before it
is built.

## 9. The exact rules of the two processes (2026-10-14)

Written after reading every slice of every acquisition of the one study (contact sheets,
`data/pictures/the-funnel-contact-20261014/`) and measuring the cheap halves on every slice
(`data/pictures/the-funnel-halves-probe-20261014/`; probes `probe_halves.py` and
`probe_halves_plateau.py` in the session scratchpad). His words that set them: "(1) high-level
localization and targeting, and (2) fine-grained targeting and boundary-drawing"; "we define that,
by looking at it (common-sense border estimation) and by using domain knowledge for where these
elements are supposed to be on these really fixed and almost identical-looking images"; "a lil bit
of extra compute requirement, some buffer, is perfectly fine"; "Not every slice, not even CLOSE";
the fat-bright and the fat-dark of a plane are "basically 'lenses' that are given to us for free",
"the same fucking image, just sorta scootch it a bit"; the axial is "a completely different picture
... Different photo with different rules/roles/objects"; the interior peaks pick "<object>s that
are potentially significant, treating them as physical objects that are grounded and connected as
a singular whole ... what is 'wrong' with the coherent object that is grounded to those interior
peaks". The thesis: each lens "stands at its own sharpest slice" (§4.2); the cheap readings "point,
and never decide alone ... It narrows where the expensive work runs" (§5.1); the plain part is
taken first and the residual read again with that context (§1.9).

**The whole method, as a child would say it** (his words, 2026-10-14: "The reasoning you use when
applying any solution using the lenses should be explainable to a child ... If you can't explain
it to a child, you don't understand it"). Every rule below is one of these sentences made exact.
1. The front-on and side-on pictures (coronal, sagittal) always look the same: a big bone on top, a
   big bone underneath, and a line between them across the middle of the picture. The pictures
   across the leg (axial) are a different picture with their own rules.
2. Squint at every picture, so it is cheap, and throw away the black around the leg. On the
   picture where the bones are bright (the fat-bright one), look down the middle of the leg from
   top to bottom: the line between the bones is the darkest spot with bright above and below.
   Everything joined to the top bright part is the top half, everything joined to the bottom bright
   part is the bottom half, and where they meet is the line. The fat-dark picture is the same
   picture with its colours changed (bones dark, fluid bright), so it takes the same halves,
   shifted into place.
3. The pictures where the line sits at the same height, in the middle, are the ones that cut
   through the joint; there are many in a row. Pick the middle one of the row; on the side-on
   pictures also pick the middle of each side's part of the row.
4. Put a box around the line, tall enough to hold both bones' ends, and look closely only inside
   the box.
5. Inside the box, each thing is found from the spot deepest inside it, the spot farthest from any
   dark edge. The big things just above the line are the top bone (from behind it shows as two
   round ends); the big things just below are the bottom bone. The kneecap is the next one, in
   front of the top bone just above the line, ringed with dark like the big bones. The small bone is
   the round one tucked up against one end of the bottom bone toward the back, with a thin dark
   line between them, and that end is the outer side.
6. Everything else is found by where it sits next to those. On the front-on picture there is a dark
   wedge at each end of the line, the inner one and the outer one; on a side-on picture that side's
   wedge shows twice, at the front and at the back of the line. Dark bands cross the middle of the
   line, and the one asked about runs from the top bone's back down to the front of the bottom
   bone's middle. A thin dark line runs along the inner side. There is a pocket above the kneecap
   with its lining, and a space behind the inner side of the knee.
7. Then ask what is wrong with each one, the way you would by looking: is a bone's rim broken or a
   dark line across its inside; is its inside lit unevenly; is the cushion between two bones thin;
   is a wedge lit up inside; is a band broken; is there fluid where there should not be, or a thick
   lining round it.

**What the pictures fix** (the header gives the directions; the study is one knee):
- coronal, front to back (the header's higher index is toward the back here): the kneecap face-on;
  the front of the upper bone with the bright pouch on the fat-dark; the joint, with both bones,
  the band, a dark wedge at each end and a thin dark line along one side; the notch in the middle
  of the band with dark bands crossing it, and the small bone below one end of the lower bone; the
  two rounded ends of the upper bone seen from behind; the soft tissue behind the knee;
- sagittal, side to side: soft tissue; a compartment (a rounded end over the flat top, a dark wedge
  at the front and the back of the band); the middle (the kneecap in front of the lower end of the
  upper bone, the notch with its crossing dark bands, the pouch above the kneecap); the other
  compartment, with the small bone below the back of the lower bone; soft tissue;
- axial, bottom to top: the lower bone with the small bone beside it toward the back; the joint;
  the kneecap over the groove of the upper bone with bright between; the pouch in front of the
  upper bone.

**Measured, 2026-10-14, the one study.** The existing basins seeded from the first and last fifths
of the leg find the joint on the coronal fat-bright slices 11 to 24 and on the sagittal fat-bright
slices 10 to 23, and fail on the sagittal's inner compartment, slices 3 to 9: the upper basin floods
down the bright front and takes the lower bone. Seeded instead from the two bright stretches either
side of the deepest enclosed dip of the profile (the chapter's own recorded rule, "markers from
anatomy, not from maxima", README's earlier mechanism, item 3; `structure.py`'s "later
increment"), the band step is 9 to 11 of 20 on every sagittal slice 5 to 31 and 10 to 11 of 19 on
every coronal slice 10 to 24, the middle of the picture, and the crossing follows the joint on
each of them; it wanders only on the slices with no joint (the kneecap slices, the soft tissue at
the stack's ends, behind the knee). On the fat-dark coronal the existing reading wraps the lower
basin round the bright fluid at the sides (the field gallery, slice 15), which is why the halves
are read on the fat-bright and carried.

### Process 1, the squint: where (8 mm tiles, every slice, cheap)

**P1 `Halves`** (`knee.collapse.halves`, new; reuses `structure._profile`, `_along_first`,
`_from_along_first`, `_seam`, `axis_code`, `superior_code`, the watershed call of `_basins`, which
become public where needed). Per series of a paired coronal or sagittal plane, read on the
fat-bright of the pair, per slice z: `inside` = the first lens's kept tiles (`not_background`,
`undecided`) with a finite median; `profile` = the central-third per-step median, superior first;
`band_step: int16 (Z,)`, the deepest enclosed dip, -1 for none; `dip_share: float64 (Z,)`, its
depth over its enclosing level; seeds = the central-third inside tiles `seed_offsets` steps above
the band (upper, 1) and below it (lower, 2); `basins: int8 (Z, TR, TC)` by the existing watershed
on the field under the told sign; `seam: bool (Z, TR, TC)`; `codes: uint8 (Z,)` over `HALF_CODES =
("read", "nothing_kept", "no_enclosed_dip", "seeds_empty", "axis_not_in_plane", "sign_unread",
"no_partner", "invalid_measurement")` (`no_partner`: a carried slice whose line-up names no partner
slice); `source: str`, `"own"` or `"carried"`.
Pure decision `enclosed_dip(profile: tuple[float, ...]) -> tuple[int, str]` over `("read",
"no_enclosed_dip", "invalid_measurement")`: the step whose depth below `min(brightest above,
brightest below)` is largest and positive, ties to the first, with `read`; no finite step with a
finite step on each side, or no positive depth, is `(-1, "no_enclosed_dip")`; an entry that is not a
float is `(-1, "invalid_measurement")`; NaN entries are silence, skipped. Which series reads: on a
`paired` plane (R0) the fat-bright reads under its own sign and the fat-dark carries it, each of its
tiles taking the basin of its line-up partner tile at its partner slice (R3a), a tile with no
partner reading 0, `source` `"carried"`; every other coronal or sagittal series (a `solitary`
plane of either flavour, every series of a `surplus` plane) reads on its own under its told sign,
`source` `"own"`. The axial has no in-plane up-down axis and is read by its own rule (P3). Constant
`seed_offsets = (2, 3)`: 16 to 24 mm inside each bone from the band, the lead's, from the pictures
(each bone's end is several tiles tall); his to change. Picture: every slice with the seam drawn
over the plane and the band step written, as the probe's.

**P2 `BandRun` and the stills** (`knee.collapse.stills`, a new module beside `knee.collapse.depth`,
whose four readings stay). Per series that reads its own halves (the fat-bright of a paired plane, or a series with
`source` `"own"`): first the level, the median band step over the slices whose band step is read
and lies in the middle third of that slice's inside extent along the axis; then the band run, the
longest contiguous run of such slices whose band step lies within one step of the level, the
earlier run on a tie. Pure decision `band_run(steps: tuple[int, ...], extents: tuple[tuple[int,
int], ...]) -> tuple[int, int, str]` over `("run", "no_run", "invalid_measurement")`, `steps` the
band step per slice (-1 unread) and `extents` each slice's first and last inside step; `no_run`
returns `(-1, -1, "no_run")`. The stills, by the fixed layout (his Q5), each a position in the run:
coronal `middle` (the run's middle slice) and `back` (three quarters of the run toward the end the
header says is posterior); sagittal `side_low` (one fifth along the run), `middle` (one half) and
`side_high` (four fifths), the centres of the two compartments and of the middle. The fat-dark's
stills are its slices whose line-up partner is the fat-bright still. Constant `still_buffer = 0`
slices either side, his to widen. On the one study these are coronal 17 and 21, sagittal 10, 18
and 26: by eye, a compartment, the middle with the notch and the kneecap, and the other
compartment; the mid-joint with both wedges and the side line; the notch with the small bone below
one end. Picture: the band step over z with the run and the stills marked, and the stills.

**P3 the axial levels** (`knee.collapse.axial_levels`, new, solitary, its own rules). Built after
its own probe is read, in the second wave; the paired views carry every one of the twelve, and the
axial joins as an independent view of the kneecap's joint, the pouch and the back of the knee. Its
rules are written to this section before it is built. *Measured 2026-10-14, the first axial probe
(`probe_axial.py`, `data/pictures/the-funnel-halves-probe-20261014/05-Axial-squint-digits.png`):*
the tile digits do not pick out the bone on the axial fat-dark. The dark third is the ring at the
leg's edge, the bright third the calf and the fluid, and the bones sit in the middle third,
unmarked. On his attached sheet the axial's two biggest interior peaks sit in the bones. So the
axial's cheap pass is the distance from dark at the squint (the tile dome, R5, reading the
series' own split), not the digits; its rule is written from that probe. *Measured the same day,
the second axial probe (`probe_axial_dome.py`, `05-Axial-squint-dome.png`):* with every tile that
holds any pixel at or below the split counted as a wall (the squint's minimum, so a thin dark rim
inside a tile still walls it), the shared dome at 8 mm and a one-tile prominence puts its biggest
territory on the bone on nearly every slice: the lower bone on the low slices, the upper bone from
the joint up, its shaft at the top, where the calf and thigh muscles form big territories too but
sit behind and beside it. A child's sentence for the axial follows from it: "on a slice across the
leg, the bone is the biggest smooth thing near the middle, walled by a thin dark rim".

**P4 the boxes** (`knee.collapse.boxes`, new). Per still: the native bounds of the tiles from
`band_step - box_above` to `band_step + box_below` along the axis, across every column that holds a
kept tile, one tile of buffer all round, clipped to the picture; `box_above = 5`, `box_below = 5`
(the bones' ends, the band and everything in it, the side lines); on the sagittal middle still
`box_above = 9`, to hold the pouch above the kneecap. The fat-dark's box is the fat-dark tiles whose
partner tile lies in the fat-bright box, plus the buffer. Nothing outside a box is read at native
resolution. Constants the lead's, from the pictures; his to change. Picture: the boxes over the
stills.

### Process 2, the native lenses: the borders, drawn only in the boxes

**N1 `BoxDrawing`** (`knee.objects.box_drawing`, new; reuses `read_interiors` whole, unchanged).
Per still, per acquisition of the pair, each in its own pixels: `read_interiors` on the box's crop
with the series' own split, `prominence_native_mm` and offsets of every pixel within `±strip_mm`;
every array kept with the crop's origin, so each coordinate maps back to the plane. This is his
attached sheet's set of lenses (distance from dark, interior peaks, territories, native edges,
dark-band traces), run where the squint said the joint is. Two facts of `read_interiors` that every
reader of this record respects: the crop's own edge is an obstacle of the distance map (it pads
the interior with False), so a peak pressed against the crop's edge is a fact about the box and is
named by its distance to that edge; and a territory's edges along the crop's edge are of kind
`frame`, with their traces `frame_clipped` (`border_codes.border_code`, read whole 2026-10-14),
and an edge whose profile runs past the crop reads `missing_profile`, so no reading counts either
as an open rim. Picture: his sheet's columns, over the box, for each still and acquisition.

**N2 `Objects`** (`knee.objects.by_peaks`, new). Per still, per acquisition: every territory with
its peak (row, column, height in mm), the half its peak lies in (the tile basin at the peak), its
pixel count and its bounds. Pure decisions, each total, each returning a named code:
- `giant_code(heights_in_half)`: the upper giant is every territory whose peak lies in the upper
  half, whose peak height is at least `giant_share = 0.5` of the highest peak in that half, and
  which has a pixel within one tile of the seam: "the big bright things just above the line", so a
  top bone that shows as two round ends (the coronal back still) is both of them; the lower giant
  likewise below; `("found", "no_peak_in_half")`, with the territories kept in peak order;
- the band, native: per column across the axis (per row on a view whose axis runs along columns),
  the distance along the axis from the upper giant's last pixel to the lower giant's first pixel,
  in mm, `band_mm (A,)`, NaN where either is absent; the band's span is the columns where it reads;
- the band's parts, along its span: on the coronal stills, the middle is the central fifth, the
  ends are the outer fifth at each end (`band_end_a` at the lower column indices, `band_end_b`: the
  inner wedge and the outer wedge, one per side), and the two compartments are the span between
  each end and the middle (`band_span_a`, `band_span_b`), where the bones press on each other; on
  the sagittal side stills the ends are the front fifth and the back fifth (`band_end_front`,
  `band_end_back`: the front and back of that side's one wedge, by the header's front) and the span
  between them is `band_span`; on the sagittal middle still, `band_middle` is the central three
  fifths, where the notch is;
- `small_body_code(...)`: "the round one tucked up against one end of the bottom bone toward the
  back, with a thin dark line between them": on the coronal back still, every territory, not the
  lower giant, whose peak lies in the lower half within `small_body_mm = 40` below the line and
  outside the band's middle three fifths, and which comes within `small_body_gap_mm = 5` of the
  lower giant (the small bone meets the big one across a thin joint, so their territories are
  parted by a dark line and need not touch); each candidate is kept with its rim reading and its
  roundness (N3), since a lump of fat reads like a bone's inside on both acquisitions and the dark
  rim and the round shape are what tell them apart by eye; the side holding the candidate with the
  highest peak is the outer side; `("side_a", "side_b", "both_sides", "neither_side")`; the
  sagittal repeats it below the back of the lower giant on its two side stills, and the two views'
  answers are kept side by side, concurrence or disagreement;
- `front_body_code(...)`: on the sagittal middle still, a territory, not the upper giant, whose peak
  lies in the upper half within `front_steps = 5` steps above the band and in the front fifth of
  the leg's extent across the axis (front by the header); `("found", "none", "tie")`;
- the places, by position relative to those, each a pixel mask kept under a positional code (the
  band's parts above are places too, the band's native pixels between the giants over those
  columns): `front_upper` (sagittal middle: above the front body's top and in front of the upper
  giant's front: the pocket); `front_upper_rim` (the pixels of `front_upper` between the fat-dark's
  lower and upper tercile edges lying within `rim_mm = 3` of its bright pixels: the pocket's
  lining); `front_lower` (sagittal middle: below the front body and in front of the band: the pad,
  kept as a place he can read); `back` (each sagittal side still only, where front and back lie in
  the picture: behind both giants' back pixels, within `back_steps = 3` steps of the line; on a
  coronal still front and back run across the slices, so there is no `back` place there);
  `side_a_outside` and `side_b_outside` (coronal middle: outside each giant's outer pixel on that
  side, across the line's height `± side_mm = 20`); `front_band` (sagittal middle: between the
  front body's back pixel and the upper giant's front pixel, per row).
Constants the lead's, from the pictures; his to change. Picture: each still with the giants, the
band's span and its middle, the ends, the small body, the front body and the places outlined by
their codes.

**N3 `Readings`** (`knee.predicates.readings`, new; measurements, never decisions). The same
small set on every object and every place, keyed by its code, per still and acquisition, NaN where
the object or place is absent, so each lens measures one thing and knows no question:
- per object (each giant, the front body, the small body): its area in mm²; its peak's height in
  mm; its roundness, its area over the area of a circle as wide as its longest extent; its rim:
  the count of its edges against dark (`low_signal`) whose trace is `bracketed`, the count whose
  trace is not, and the longest run of consecutive rim points not bracketed, in mm along the rim,
  with `frame` and `missing_profile` edges counted apart and never as open ("is the rim broken");
  its inside: the dark components (pixels at or below the split, four-connected) lying more than
  `inside_mm = 2` inside its edge, their count and the longest one's length in mm ("does a dark
  line cross it"); the median and interquartile range of its pixels ("is it lit unevenly"); and
  the area of the largest connected patch of its own brightest quarter (pixels above its own upper
  quartile), in mm² ("the brightest bits of an even bone are sprinkled; a bright patch is one
  piece"), each per acquisition;
- per place: its area in mm²; the share of its pixels at or below the split (dark), above the
  acquisition's upper tercile edge (bright), and above its lower tercile edge; its largest dark
  component and its largest bright component, each's area in mm² and length in mm; and, for the
  band's parts and `front_band`, the median gap in mm ("is the cushion thin");
- the wedge, in each band end: the largest dark component there (dark on both acquisitions), its
  area in mm², the bright pixels of the fat-dark inside its outline pulled taut (its convex hull),
  their area in mm², and whether any of them reaches the hull's edge ("is it lit up inside, and
  does the bright reach its surface");
- the crossing band, in `band_middle` on the sagittal middle still: every dark component there
  with the slope of its long axis; the band asked about is the longest one sloping down toward the
  front; its length in mm, the longest gap along it in mm, and the bright share of the fat-dark
  inside its hull ("is it whole and dark");
- the inner line, in the side place on the inner side: the longest dark component running along
  the up-down axis, its length in mm and its median thickness across in mm, and the bright area of
  the fat-dark in the place ("is it thick, broken, or wrapped in bright");
- the pocket's lining: the area of `front_upper_rim` over the length of the bright region's edge,
  in mm, its mean thickness ("a thick grey rim round the fluid").
The tercile edges are the existing rule (`tercile_edges`) over the box's kept native pixels of
that acquisition. Picture: each still with every object and place outlined and its readings
written beside its code.

**N4 the twelve, each a child's question about what can be seen** (`knee.predicates.findings`,
exists, extended). His words, 2026-10-14: "diagnosis of the 12 conditions is common-sense reasoning
based on knee anatomy we can see"; "If you can't explain it to a child, you don't understand it".
Each row points at its subject as R11 and the object model already say, asks its question, and
carries the readings that answer it beside its code; the subject and the question are written in
the design and the docstring only, and records carry the finding's index and the subject's code:
- 0, fracture: is a bone's rim broken, or does a dark line cross its inside? (every object, on the
  fat-bright: the longest run of rim not bracketed; the longest dark component inside);
- 1, bruise in a bone: is a bone's inside unevenly lit, its brightest bits in one patch rather than
  sprinkled? (every object, on the fat-dark: the interquartile range over the median; the largest
  patch of its brightest quarter), his words: "Bones should be pretty flat within the internal
  fill of the <object>, a contusion should show up as unexpected variance in signal intensity";
- 2 and 3, the worn joint on one side: is the cushion between the two big bones thin on that side,
  where they press on each other? (`band_span_a`/`band_span_b` on the coronal middle still and the
  side still's `band_span`, named inner and outer once the side is known: the median gap);
- 4, the worn joint behind the kneecap: is the cushion between the kneecap and the top bone thin?
  (`front_band`: the median gap);
- 5 and 6, the torn wedge on one side: is the wedge on that side lit up inside, with the bright
  reaching its surface, or is it missing? (the coronal middle still's band end on that side, and
  that side still's front and back ends: the wedge's area, the bright inside it, whether it reaches
  the edge);
- 7, the band crossing the middle: is the band running from the top bone's back down to the front
  of the bottom bone's middle whole and dark, or broken or lit up? (the crossing band: its length,
  its longest gap, its bright share);
- 8, the thin line on the inner side: is it thick, broken, or wrapped in bright? (the inner line:
  its length, its thickness, the bright around it);
- 9, fluid in the pocket above the kneecap: is the pocket full of bright? (`front_upper`: its
  largest bright component's area on the fat-dark; some fluid is normal, and how much counts is
  his);
- 10, the lining: is there a thick grey rim round the fluid in the pocket? (the pocket's lining:
  its mean thickness), the object model's subject for this row, the envelope's lining (R11); the
  pad's readings (`front_lower`) are kept beside it for him to read;
- 11, the bubble behind the knee: is there a bright bubble behind the inner side of the knee?
  (`back` on the inner side still: its largest bright component's area on the fat-dark).
Inner and outer come from the small body; with none, the side rows abstain with that reason and
keep `side_a`/`side_b`. `form_given` stays False and every code stays `form_not_given`: how much
counts is his, "derived experimentally" (2026-10-13). The output stays `projection_undeclared`.
The Codex check of 2026-10-14 (`readings/the-funnel-two-processes-codex-20261014.md`) found the
errors these rules now correct: the child's first sentences said what the axial and the fat-dark
do not show; a coronal still has no in-picture front and back; the small bone meets the big one
across a joint; the band's "ends" change meaning between views; several readings counted pixels
where the question asks about a shape; and the pad was not this row's subject.

**Not in this plan: the corpus table.** Reading the route over the 58 labelled studies, and how
its readings are laid beside the competition's labels, is his call to make and is offered to him;
nothing here builds it.

**The numbers in these rules**, each an argument, written before the run that judges it (law 4),
none chosen to separate any label:

| constant | value | where it comes from | who changes it |
|---|---|---|---|
| `seed_offsets` | 2 and 3 tiles | each bone's end is several tiles tall in every picture looked at; 16 to 24 mm inside it | him, by eye |
| `still_buffer` | 0 slices | "not every slice, not even close"; the stills alone first | him |
| still positions | coronal 1/2 and 3/4 toward the back; sagittal 1/5, 1/2, 4/5 | the fixed layout: the middle of the joint, the notch behind it; the middle of each side and of the middle | him, by eye |
| `box_above`, `box_below` | 5 and 5 tiles; 9 above on the sagittal middle | tall enough to hold both bones' ends; the pocket reaches about 70 mm above the line | him, by eye |
| `giant_share` | 0.5 | "the big things": a top bone's two round ends stand about equally deep | him, by eye |
| `small_body_mm`, `small_body_gap_mm` | 40 mm, 5 mm | the small bone sits within a few centimetres below the line, across a thin joint | him, by eye |
| `front_steps` | 5 tiles | the kneecap sits just above the line, within 40 mm | him, by eye |
| `back_steps` | 3 tiles | the space behind the knee at the line's height | him, by eye |
| `side_mm` | 20 mm | the inner line runs a few centimetres either side of the joint | him, by eye |
| `inside_mm` | 2 mm | a dark line inside, not the dark rim | him |
| `rim_mm` | 3 mm | the lining is a thin layer round the fluid | him, by eye |
| `prominence_native_mm`, `strip_mm` | 3 mm, 6 mm | §3, exist | him |

**Waves.** Wave 1, in parallel, each builder confined to its own module, test and picture: P1, P2,
P4, N1. Wave 2: N2, then N3 and N4. Wave 3: the route (`knee.pipeline`, behind the existing
`AnalysisRequest`, reading the stills instead of `selected_slice`), the view sheets, and the real
run on the one study, every picture redrawn and looked at by the lead before it goes to him. Then
his eye-check; then P3. Every name a builder writes (module, record, field, code, filename, picture
title) carries no anatomical or tissue word; anatomy lives in the design, the docstrings and the
conversation.
