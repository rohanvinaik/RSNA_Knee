# Stage 3 reframed: there is no level map

2026-10-10. The lead proposed a Nyúl-Udupa intensity standardization and found a fatal flaw in it.
The founder's answer: that cannot be a blocker, because the sibling project solved the homologous
problem — a confluent plate carries far more global signal than a sparse one. He was right, and
the answer is not a level map at all.

## The flaw in the obvious approach

Flicker units cancel **gain** but not **SNR**: coil, field strength, bandwidth, averages and voxel
size change tissue contrast without changing the noise scale. Left alone that is a whole-field
sheet in the residual.

The standard fix is histogram-landmark standardization. It cannot be used here: the foreground
histogram **moves when there is pathology**, and on a fluid-sensitive sequence **the brightest
tissue is fluid** — which is effusion, Baker's cyst and oedema, three of the twelve. The obvious
bright anchor is the most contaminated choice available, on the sequence where those three live.

## What the sibling actually does — read from its code

**There is no bright anchor anywhere in it.** The chain is:

1. **`cassette/instrument.py::light_above`** — a place's value is read as its light *above a
   measured level*, in noise units. "`level` is one number (the dark) or a field of the
   brightness's shape (a slice's haze)... **Graded, never cut: a place below the level reads a
   negative number.**" A never-imaged place reads NaN.
2. **`cassette/layout.py::digit_of`** — that excess becomes a balanced-ternary digit against a
   `(low, high)` band: "-1 below low, 0 from low to high, +1 above high; None for a value not
   read."
3. **`substrate/compose/facets.py::regime_facet`** — density is kept as "an **exact token** for the
   embryo density regime (`sparse` / `dense`)", not divided out.

And §5.1's cheap readings, which the founder pointed at directly: "The readings of the whole field,
taken once for the movie, are the **priors**: its density, its distribution (even, spiky or
one-sided), its profile down the depth, and whether and how the plate drifts. Their words form the
**regime key** under which a case from this field is kept." These readings "**point, and never
decide alone**."

**So the global level is never normalized away. It is measured once, named, and carried as the
condition under which two fields are comparable.**

## The reframe

> "**Yes: under the per-series branch, reframe it as dark-referenced ternary encoding and
> whole-field regime indexing — not histogram level equalization.**" — Codex

Stage 3's output is therefore: the **graded excess** above the measured quiet level in noise units,
the **digit field** against a versioned middle, the **middle's provenance**, and the **regime
readings**. Stage 1 already supplies the dark, label-free, and an effusion does not touch it.

## Exactly what each step does and does not handle

| nuisance | handled? | by what |
|---|---|---|
| digital/scanner **gain** | **yes** | scaling signal and its measured noise law together leaves dark-referenced noise units invariant |
| acquisition **SNR** | **partly** | per-series middles remove a common positive affine change of the excess; **tissue-dependent contrast change, spatial shading and noise-driven rank changes remain**. Corpus middles would not remove it at all |
| **composition** (a large effusion) | **no, and this is the point** | neither branch removes it safely. Per-series quantiles move with composition; corpus middles stay fixed while occupancy changes. **The regime readings retain that change as information** |

The honest statement of the cost, which must not be glossed:

> "per-series digits can suppress a global nuisance sheet, but they **also suppress a genuinely
> global signal increase**. Keeping the graded excess and whole-field readings makes that loss
> explicit."

That is exactly why the graded excess is kept beside the digit, and why the regime key carries the
global reading. The digit alone cannot tell a global gain from a global signal increase; the pair
can.

## Terciles against the tail, quantified

The lead asked whether a mid-quantile band is materially safer than upper landmarks, or whether
that was wishful. Codex quantified it. With a fraction epsilon of the foreground replaced by a
bright finding:

| epsilon | lower tercile moves to rank | upper tercile moves to rank | the 95th percentile |
|---|---|---|---|
| 5% | 0.351 | 0.702 | reaches the baseline's upper endpoint |
| 10% | 0.370 | 0.741 | **falls inside the finding's own population** |

The displacement is `dQ(q) ~ epsilon * q / f(Q(q))`, so **low baseline density near a quantile
amplifies even modest contamination**.

> "Terciles are materially less vulnerable to small upper-tail additions, **but not invariant**.
> Keeping epsilon < 1/3 prevents an entirely upper-tail finding from capturing the upper tercile;
> it does not guarantee a stable band."

So the band is **safer, not safe**, and its safety condition is stateable: epsilon below a third,
sufficient distribution density at the band, and movement below a tolerance declared in advance.

## A trap the lead must not fall into

> "Crucially, **'share above this series' upper tercile' is approximately one-third by
> construction: it cannot measure density.** Composition requires a separately anchored reading."

Any occupancy reading must be anchored on a level **not** derived from the same distribution's own
quantiles. The regime key as built anchors its foreground share on the **quiet level** — the top of
the dark population, which comes from stage 1 — so it is separately anchored. That is correct, and
it is correct for a reason worth keeping written down.

## The regime token must expose, never excuse

> "Regime conditioning that **hides** exceptional composition: conceptual error. The token must
> **preserve and expose** the difference, not certify it as nuisance."

A bright-rich regime is **evidence**. It must never become permission to normalize away fluid. This
is No Popery at the level of the regime: the token conditions comparability, it does not license a
verdict.

## MRI-specific breaks that microscopy does not have

| break | kind |
|---|---|
| receive-coil sensitivity is **multiplicative**, so "a slice's haze" does **not** port as a subtractive field — subtracting an additive haze does not correct shading | conceptual: the knee's haze analogue, if any, is a division |
| different sequence weightings change the **order** of tissue brightness; treating that as global gain is a conceptual error, and separate weighting banks are the answer | conceptual — already handled by never stacking across weightings |
| transition-region inaccuracy in the stabilizer propagates into the bands | engineering; the measured transform quality (within 7% through the transition, 11% low at pure noise) is the stated bound |
| a numerical zero need not mean never-imaged | engineering: an explicit validity mask, already known |
| cropping and anisotropic partial volume change foreground proportions **without pathology changing** | engineering: coverage and resolution belong in the regime key |
| an effusion large enough to move the middle | **conceptual: treating per-series quantiles as composition-invariant is an error.** This is the one to hold onto |

## Settled from §7, read whole

**The middles are PER MOVIE.** §7.2, verbatim:

> "The middle is read once for each movie, cheaply and in real time, at the start of the run. **It
> is read off the movie the system is handed**, and once read it never moves within the run."

> "There is one for each metric and lens, the same for every place and time point of a movie."

> "Within a movie the middle never moves, so every digit of the movie is written against one
> reference and compares with every other, across its places and its time points."

No corpus reference appears anywhere in §7. And Law 4 is stated in the thesis's own words:

> "**No middle is chosen to separate confirmed cases.**"

### Two corrections to the lead's chain

**1. The dark is NOT the digit's reference.** §7.2:

> "A middle is also distinct from the camera's dark: **the one is the reference of a digit, the
> other the baseline of a black.**"

Two things doing two different jobs. The lead had collapsed them into one chain. The dark is the
baseline a black is cleared against; the middle is the band a digit is written against. They are
read differently and used differently.

**2. The value is NOT discarded.** §7.2:

> "**The value itself is kept beside the digit.** A quantity enters computation at its value, and
> comparison and recall by its digit."

The ternary reduction is for **comparison and recall only**. Arithmetic runs on the value. This
matters downstream: a digit is not a replacement for the reading.

### The gap, at exactly the quantity in question

The tercile rule is **conditional**. §7.2:

> "**Where a metric has many readings in the movie**, its edges stand at their terciles, so that
> its three digits are equally likely within the movie."

But the plate facet is "read once, at the start of the movie" — **one reading per movie**, which
cannot supply terciles. So §7 states a per-movie *source* for every middle, tercile *edges* only
for metrics with many readings, and **for a once-per-movie whole-field reading it does not state
where the edges come from at all.** That unspecified quantity is precisely the global level. §5.1
is the likeliest place it is settled and has not been read for this.

### No bright anchor, confirmed

> "both edges come from the same tercile rule, so the scale is anchored on neither extreme but on
> the movie's own distribution of that metric."

The dark end is the only stated baseline. Brightness enters §7 only as a **spatial** centre (the
composite's nearest bright spot), never as a scale reference.

**Terminology collision to avoid in the port:** in §7 "anchor" never means a scale anchor — it
means a time point where the heavy analysis runs.

### What sparse/dense actually is in the sibling

TASK_TAXONOMY §3 gives **no rule, no threshold and no deciding measurement** for the token. It is
attached per embryo, and it is **not about signal level at all** — it is read off graph degrees
(interior orphans, ends, divisions, step medians). Regime recognition at inference is explicitly
out of scope there: "this is authoring input, never an inference-time source."

So the density token's *use* ports, but its *reading* does not: the knee must derive its regime
from label-free image readings, not from an authored token.

> "Do not run one global pipeline; **route by regime**." — what the token is for.

## The composition answer, quantified

Fable settles the effusion worry with a number. The key distinction is **where the middle's edges
are read from**:

- At a **fluid voxel the value does not change with how much fluid there is.** Only the middle can
  move.
- A **tercile** middle moves with composition (quantile q goes to q/(1-f)).
- A **valley** middle — edges at the valleys between the foreground histogram's modes, rather than
  at quantiles — moves by about `sigma^2 * ln(mass ratio) / delta_mu`. Fluid against muscle on a
  fat-suppressed sequence has `delta_mu ~ 30 sigma`, so **doubling the fluid mass moves the valley
  by about 0.02 sigma. Nothing.**

And the tercile's safe condition, with its arithmetic: safe while `f < 1 - (2/3)/F(valley)`, about
**26%** with the bright mode holding 10% of a normal fat-suppressed foreground. A large effusion is
50-100 mL in 1-2 L of imaged tissue, so **f ~ 3-8%: safe**. The 95th percentile is never safe,
since 0.95 exceeds F(valley).

> "Terciles are safe against the finding and **unsafe against the field**."

What is *not* small is habitus, field of view, and a fat fraction running 10-40%. Those go in the
regime key, or the band reads valleys.

## The consequence that changes the stack

SNR splits in two, and only one half is cancelled:

- **b1, a common scalar** (voxel volume, averages, bandwidth, B0, coil): one factor on every tissue.
  Cancelled by the **digit**, if and only if the middle is per-series. **But the VALUE keeps it.**
- **b2, contrast** (TE, TR, TI, fat suppression, relaxation at field strength): changes tissue
  **ratios**, not a common factor. **Nothing in the chain handles it.** It is a regime axis read
  from headers, and comparability is key equality.

> "the VALUE a_p keeps b1, so any stack built on values still carries b1 as a per-study whole-field
> sheet; **the stack must be built on digits**, or on anchor-scaled values."

And the per-place reference then becomes the carrier's own form:

> "at place p the reference within a key is the population's **digit count table**
> (n_-1, n_0, n_+1), a truth table; a study's change at p is its digit against that table;
> **s_p becomes the place's digit entropy**."

That is §13.1's bundle exactly — "Its **count table** holds how many times each row of each bank
was written" — and §1.6's point that a truth table and its Hadamard expansion are two views of one
object. The population reference at a place is a count table, which is what the carrier already is.

## Stage 3, as it should now be built

Three things, not a level map:

1. **The knee's `Middles` table.** Per series, band edges in noise units, read from the
   foreground's **valleys** (terciles only where a series is unimodal), **named for what they were
   read from**, and versioned — the sibling's `Middles` carries "a name saying what they were read
   from" for exactly this reason.
2. **The regime key.** Headers (plane, weighting, TE/TR/TI bins, field strength, voxel size, field
   of view, extent, vendor, zero share) plus the millisecond whole-field readings: foreground area
   at the joint line, the histogram's mode count, positions and masses, the bright-mode mass on a
   fluid-sensitive sequence as the knee's sparse/dense, the superior-inferior profile, phase-encode
   anisotropy, clipped share, metal. Comparability is **key equality**.
3. **The level kept as a reading** — dark, muscle mode, bright mode, S/I profile, in noise units.
   **Reported, never applied.**

## Two rulings for the founder

1. **Valleys or terciles** for the middle's edges.
2. **Values or digits** into the stack. The value residual keeps one use either way: it measures
   b1 as a per-study sheet, which is how the sheet becomes visible rather than hidden.
