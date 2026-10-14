# The squint stack's counted work, beside the whole-volume digit maps' — 2026-10-13

The-funnel task 1.3 (`openspec/changes/the-funnel/tasks.md`), the budget of the funnel's
operation 1 (`knee.collapse.squint_stack`, task 1.1). Every number here is read from the ledger of
one real run, `data/measurements/the-funnel-phase-a-20261013/receipt.json` (SHA-256
`2202ef0fd22d4b5d4ff3cd1537a98b2c75036e8b22e4519bfa8b9673969e100f`), or computed from the arrays
that run saved; nothing is recalled or estimated. The run, re-made 2026-10-13 after the unit's
repair so the receipt binds to the final sources: `just analyze-objects --uid
1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149 --tile-mm 8 --span-mm 3
--samples 13 --axis superior --backend jit --prominence-mm 3 --out
data/measurements/the-funnel-phase-a-20261013`. The tile is the funnel's declared 8 mm
(`design.md` §3; the lead's ruling of 2026-10-13: the real study runs at the design's tile, never
3); the other settings are those of the saved run `codex-closeout-review-jit-20261012`. Five series
measured, no failures; 14 drawings drawn and 2 not drawn: the first-lens sheets and the view sheets
both refuse the lens's third word `not_background` (`first_lens_vocabulary_uncoloured`, `KeyError`),
because the lead's rename of that word (R2, 2026-10-13) has not yet reached those two drawers; that
is unit 2's propagation, not this unit's.

**Counted work and profiler behaviour are reported separately** (`docs/STAGE_CONTRACT.md`). This
record holds counted work only: the ledger was untimed (`elapsed_ns` is null on every one of its
156 events), and no profiler was run on this unit. A wall-clock reading of the stack is a separate
measurement, owed with `just profile-calls` and pyperf, and is not implied here.

## What is counted

- **The stack**, under `knee.collapse.squint_stack.CONTRACT` (`work`: "TR * TC affine maps per
  slice; the stack is Z of them") and `knee.collapse.physical.CONTRACT` for the per-slice squint
  it calls ("per-tile finite scan/extraction, median selection and extrema reductions"): the
  ledger's `squint_stack.produced` records `slices` (Z) and `tiles` (Z · TR · TC), which is the
  number of affine maps made and the number of tile medians taken. Every native place is read once
  by the per-tile scan, so the stack's source reads are the volume's places, Z · R · C.
- **The whole-volume digit maps**, the lenses stage's `lenses.produced` on the same series in the
  same run: `places` (Z · R · C, one ternary digit per native place per seated member, two members)
  and `output_bytes` (five bytes per place: two members' code and digit, and the standing).

## The table, per series, from the ledger, at the 8 mm tile

| series (view) | Z | plane R × C | tile px | grid TR × TC | **stack tiles** (Z·TR·TC) | **digit-map places** (Z·R·C) | places per tile | stack output bytes | digit-map output bytes |
|---|---|---|---|---|---|---|---|---|---|
| …517371931282 (Sagittal, fs 0, fat 0) | 36 | 400 × 400 | 20 × 20 | 20 × 20 | 14,400 | 5,760,000 | 400.0 | 819,200 | 28,800,000 |
| …854063726441 (Coronal, fs 0, fat 0) | 30 | 384 × 384 | 21 × 21 | 19 × 19 | 10,830 | 4,423,680 | 408.5 | 618,032 | 22,118,400 |
| …928971904198 (Coronal, fs 1, fat 1) | 30 | 320 × 320 | 16 × 16 | 20 × 20 | 12,000 | 3,072,000 | 256.0 | 684,800 | 15,360,000 |
| …109474719429 (Sagittal, fs 1, fat 1) | 36 | 320 × 320 | 16 × 16 | 20 × 20 | 14,400 | 3,686,400 | 256.0 | 819,200 | 18,432,000 |
| …529101229430 (Axial, fs 1, fat 1) | 32 | 320 × 320 | 16 × 16 | 20 × 20 | 12,800 | 3,276,800 | 256.0 | 729,600 | 16,384,000 |
| **all five** | 164 | | | | **64,430** | **20,218,880** | **313.8** | 3,670,832 | 101,094,400 |

Reading the columns:

- `stack tiles` and `digit-map places` are the ledger's own counts (`squint_stack.produced.tiles`,
  `lenses.produced.places`), per series in route order; the totals are their sums.
- `places per tile` is `digit-map places / stack tiles`: how many native places one tile median
  stands for. It is 256 where an 8 mm tile is 16 × 16 px (0.5 mm pixels, 320 px planes that the
  tiles divide exactly), 400 where it is 20 × 20 px (0.4 mm pixels, a 400 px plane divided
  exactly), and 408.5 where it is 21 × 21 px (0.390625 mm pixels), below the 441 of a whole tile
  because a 384 px plane under 21 px tiles has 19 tiles across (399 px), so the last tile in each
  direction holds 6 px, kept at its true coverage.
- `stack output bytes` is computed from the saved arrays: 56 bytes per tile (four float64 maps and
  a float64 LPS centre) plus 32 bytes per grid tile for the one int64 bounds grid every slice
  shares; `digit-map output bytes` is the ledger's `lenses.produced.output_bytes`.
- The ratio of counted work, digit-map places to stack tiles, is **313.8 : 1 over the study**,
  400 : 1 and 408.5 : 1 on the two 0.4 mm series and 256 : 1 on the three 0.5 mm series; of
  output bytes, 27.5 : 1. Against the earlier 3 mm run's 45.4 : 1 (below), the 8 mm tile cuts the
  tile count by 6.9 (444,888 to 64,430), beside the lead's expectation of about 7.1 from the
  tile-area ratio (8/3)²; the difference is the whole-pixel rounding of each tile.

## What the same run established about the stack itself (task 1.1's checks)

Computed by a scratch probe over the receipt and the saved arrays (not kept; the numbers are
here):

- all five series `present`, 164 slices squinted, 0 tiles with no finite pixel; the grid guard,
  which since the repair compares every slice's tile count, tile size in pixels and bounds with the
  first slice's, found one grid on every slice of every series;
- on every series the selected slice's four maps from the stack are **byte-identical** to the
  objects stage's own saved squint of that plane (`median`, `minimum`, `maximum`, `coverage`),
  and the stack's one bounds grid is identical to that squint's; re-squinting the saved plane
  through `physical_squint` is byte-identical to the stack's slice;
- on every series the corner tile's saved centre equals the slice's `ImagePositionPatient` offset
  by half a tile of pixel centres along both in-plane directions, to 1e-9 mm (for the first
  series: origin (−96.346, −141.058, 85.894), centre (−97.028, −136.807, 82.678)); every tile
  centre maps back to native within 2e-13 px of its tile's pixel midpoint through
  `PlaneFrame.to_native`;
- the ledger order per series is `study.consumed_by.collapse`, `study.consumed_by.squint_stack`,
  `squint_stack.produced`, `collapse.produced`;
- `just composition` on the run: `dangling:first_lens,lineup`, no phantom consumer, the
  conversation before ownership. The stack is produced five times (ledger index 5 first) and
  **consumed by the line-up and the first lens** (`squint_stack.consumed_by.lineup` twice,
  `squint_stack.consumed_by.first_lens` five times), and the pairs by the line-up, so neither
  dangles any longer; what dangles now is the line-up and the first lens, whose readers are the
  later units (3b, 3c, 4). The two composition tests in `tests/knee/test_pipeline_composition.py`
  fail on `first_lens` alone (the synthetic corpus has no paired plane, so no line-up is produced
  there), by the lead's ruling reported and not changed.

## What is not measured here

- Wall-clock time of the stack, and the drawing pass (pictures were on; their cost is the
  artifact's, not the analysis's).
- The 58: this is the one-study demonstration; the corpus run is engineering (task 14.1).

## The earlier run at 3 mm, superseded

The first measurement of this unit was made the same day at `--tile-mm 3` (the settings of the
saved run `codex-closeout-review-jit-20261012`, not the funnel's tile), into the same directory,
whose receipt the 8 mm run above has since overwritten. Its numbers are kept here as the record of
that run, labelled as past and no longer re-verifiable from disk; nothing below is current.

| series (view) | Z | plane R × C | tile px | grid TR × TC | stack tiles | digit-map places | places per tile | stack output bytes | digit-map output bytes |
|---|---|---|---|---|---|---|---|---|---|
| …517371931282 (Sagittal, fs 0, fat 0) | 36 | 400 × 400 | 8 × 8 | 50 × 50 | 90,000 | 5,760,000 | 64.0 | 5,120,000 | 28,800,000 |
| …854063726441 (Coronal, fs 0, fat 0) | 30 | 384 × 384 | 8 × 8 | 48 × 48 | 69,120 | 4,423,680 | 64.0 | 3,944,448 | 22,118,400 |
| …928971904198 (Coronal, fs 1, fat 1) | 30 | 320 × 320 | 6 × 6 | 54 × 54 | 87,480 | 3,072,000 | 35.1 | 4,992,192 | 15,360,000 |
| …109474719429 (Sagittal, fs 1, fat 1) | 36 | 320 × 320 | 6 × 6 | 54 × 54 | 104,976 | 3,686,400 | 35.1 | 5,971,968 | 18,432,000 |
| …529101229430 (Axial, fs 1, fat 1) | 32 | 320 × 320 | 6 × 6 | 54 × 54 | 93,312 | 3,276,800 | 35.1 | 5,318,784 | 16,384,000 |
| all five | 164 | | | | 444,888 | 20,218,880 | 45.4 | 25,347,392 | 101,094,400 |

At that run the stack was consumed by no stage (`dangling:pairs,squint_stack`), because the
line-up and the first lens were declared and not yet built; both have since landed and read it.
