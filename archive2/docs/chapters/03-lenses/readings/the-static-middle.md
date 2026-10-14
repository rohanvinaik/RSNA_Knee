# The static middle: what the thesis says, and what the sibling built

**Both oracles, read for one question** on 2026-10-11: *what is a digit written against?* The thesis
was read whole (§7, `v7_parts/06_language.md`, 268 lines); the sibling was traced and its units read
whole. This reading includes the code miner's own erratum, which corrected its first answer.

**Why it matters here.** `knee.lenses.digits.digit_code` was already built and pinned taking a
`witness_middle` plus a band computed from spreads. The thesis says something different in SHAPE, and
the difference is not cosmetic.

## What the thesis says (§7.2, verbatim)

> "The static middle is the fixed reference a metric's digit is written against. There is one for
> each metric and lens, the same for every place and time point of a movie. **It is a pair of edges,
> a low and a high.** The digit is −1 below the low edge, +1 above the high one, and 0 between them."

> "Where a metric has many readings in the movie, its edges stand at their **terciles**, so that its
> three digits are **equally likely** within the movie."

> "The middle is read once for each movie, cheaply and in real time, at the start of the run." …
> "It is read off the movie the system is handed, and once read **it never moves within the run**."

> "**No middle is chosen to separate confirmed cases.**"

> "A middle is also distinct from the camera's dark: the one is **the reference of a digit**, the
> other **the baseline of a black**."

And on silence, which the knee's build already matches:

> "A reading made at its middle is the digit 0, **written in its row like any other digit**."
> "A reading never made leaves its bank silent, and a silent bank is **the informational zero**, 'no
> reading here', which makes no claim. It is left out of every comparison, of dot products and norms
> alike, so it never counts for or against anything."

**Why terciles** is information-theoretic, and the founder's own words are in the sibling's record:
*«every metric in balanced ternary against a defined static "middle"»*, and *«So a blanced-ternary
digit containing only 1.6 bits is fine, since we're combining data sources»*. Equal-likelihood digits
carry the full 1.6 bits.

**What §7 does NOT say**, reported as absence rather than inferred: no formula for the terciles, no
estimator or tie rule, no rule for a metric with few readings, no rule for a reading exactly on an
edge ("between them" is the only wording), and no rule for a row with a zero count inside a bank that
IS written — its silence rule is stated for a whole bank.

## What the sibling actually built

`digit_of(value, middle)`: `if value is None or isnan: return None` → **writes no row**;
`if number < low: return -1`; `return 1 if number > high else 0`. **Both edges belong to the 0 row.**
`test_middles`: `low, high = np.quantile(finite, (1/3, 2/3))`.

### The population IS structurally selected — the erratum's correction

The miner's first answer said the middles are "distribution quantiles over pooled values"; its
erratum replaced that. There are two kinds of population:

- **Structurally selected before the quantiles**: `voxel@<lens>` intensity and depth take only places
  where `lit = ~black & isfinite(light)` — the black is that lens's own stage 1/2 mask; and `own`
  takes the finite light and slice of each taken cell's footprint voxels through its band, i.e. a
  **resolved object supplies its own population**.
- **Pooled with no place filter**: the neighbourhood squares, the per-frame readings, the plate, and
  every candidate at taking.

So the honest statement is neither "witness tissue" nor "naive pooling": **structure selects WHICH
places enter the population; the distribution's own terciles then set the edges.** The miner is
explicit that *"Neither function picks a reference region as a standard."*

### The spatial problem is solved BEFORE the digit, not by the middle

This is the part that bears hardest on the knee's coil-falloff problem:

- `frame_dark_of` calibrates the dark **per frame and per depth**. The founder, 2026-09-28: *"The
  'dark' level isn't universal, it's frame/lens specific. The *concept* is the exact same, the
  calibration is for each frame and z-axis position."*
- a per-time-point **noise curve** converts counts to flicker units;
- **the haze**, *"the founder's smarter dark"*: the mean light over nearby gaps between bodies —
  places that are imaged and curve up like a hollow, within a neighbourhood radius — *"it rises with
  the glow of a crowded plate and falls to the dark in an empty one."* His objection that drove it:
  *«"black" signal isn't a single level, but is heavily influenced by the local environment»*.

So: **local structural baseline → noise units → static tercile edges.** The middle never carries the
spatial correction.

### Two gaps §7 leaves open, which the sibling answers in code

- **"A metric with few readings"** — §7 gives no rule. `layout.test_middles` (`layout.py:661-678`)
  does: `if finite.size < 3: continue`, so the pair gets **no middle at all**, and `middle_of` then
  raises rather than inventing one. A middle that cannot be read is absent, not guessed.
- **A per-object own baseline was tried and measured as mostly silent.** The older
  `hdc/position.mine_zero` returns an infinite tolerance below two points, and
  `docs/HDC_SUBSTRATE.md:350-356` records that on wave 1 **78.3% of all position-family readings were
  cold start**, and 100% at the first two frames of every window. That is evidence about a design the
  knee might otherwise reach for: an object compared against its own history cannot speak early, and
  for a knee study — which is a still, with no history at all — it could never speak.

## The tension this created — SETTLED by the founder, 2026-10-11

> **RULED. "Your inference is correct."** — the founder, on the reconciliation below
> (`../teachings.md`). The knee takes **tercile edges after a local structural normalisation**. The
> witness-tissue middle is withdrawn, and with it the three-fat-witness apparatus and the
> per-witness spread that entered the band.
>
> The table and the inference below are kept as the record of how the question was reached, **not as
> an open question**. A reader arriving here should not conclude the project is blocked on it; what
> remains open is what his ruling did not touch — the knee's own local baseline, which Fable's
> levels consult says is *multiplicative* and so cannot be the sibling's additive haze.

### How it was reached, kept as the record

| | a middle is | spatial variation handled by |
|---|---|---|
| thesis + sibling | a pair of edges at the **terciles** of the movie's own readings | a **local structural baseline** (the haze) applied before the digit |
| Codex + Fable (`witnesses-*.md`) | a named **tissue witness's** location and spread | three fat witnesses, their disagreement measuring the field |

The lead's reading of the reconciliation, **labelled as the lead's inference**: the haze's analogue
handles coil falloff locally and for free *because it is local*, and the tissue conjunction then comes
from rows **across acquisitions** rather than from the middle. If that holds, `witnesses.py` is a far
smaller thing than either reader proposed, and `digit_code` must change shape from centre-plus-band
to **a pair of edges** before anything consumes it.

## Two facts about the sibling, reported and not acted on

1. Its middles are **still marked a proposal**: `middles_read.py` says the table is "marked a
   proposal until he has read it", and the table every vector was written against carries
   `"test": true`. The miner found no record of the founder's ruling in what it read.
2. **A contradiction in its own record.** `layout.py` and `b0_vectors.py` say the provisional test
   table is "never shipped, never used for a kept vector"; `teach_grind.py` and the churn plan ship
   it and write every vector against it. Per the erratum, the `[0.0, 0.0]` entries ARE consulted on
   that path for `taking/*`, where a zero-width middle makes the digit the value's sign.

## What this changes in the knee's build

- **`digit_code`'s shape is wrong against the oracle** — centre+band where the thesis says two edges.
  Nothing consumes it yet, so the cost of changing it now is one pinned module.
- **Its silence rules are right** and match §7 exactly: a reading at the middle is a written 0; a
  reading never made writes no row and is left out of every comparison.
- **Codex's question "which spread enters `digit_code`?"** partly dissolves under the tercile shape:
  edges read off the distribution carry no spread argument at all. What remains is whether an
  admission failure can still hide, which it can if the population is selected badly.
