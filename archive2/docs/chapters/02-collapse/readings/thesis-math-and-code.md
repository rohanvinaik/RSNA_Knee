# Chapter 2 — the thesis's math and the sibling code that implements it

2026-10-10. Sections read whole: §4 (03_collapse.md), §5 (04_structure.md), §13 (12_methods.md),
§1.1-§1.6 (01_information.md, lines 1-703). Symbolic trace via Serena on cell_tracking.

## 1. The squint's math — and the unification

§1.3, verbatim:

> "Let a reading spread over N dimensions, with a signal s lying in the k of them that a question
> reads, and independent variation of power sigma^2 in every dimension. Projecting the reading onto
> those k dimensions keeps all of the signal and only k of the N shares of variation ... so the
> ratio of signal to variation rises by a factor of N/k."

> "**Pooling is the commonest case, with k = 1.** If n places share one level s, each with
> independent variation eps_i of standard deviation sigma, their mean is ybar = s + (1/n) sum
> eps_i, sd(ybar) = sigma/sqrt(n), so the **signal-to-noise ratio of the amplitude rises by
> sqrt(n)**, and that of the power by n. **Blur is pooling in space.**"

**This is the collapse's math, and it unifies the two moves.** The squint pools over *space*
(tile medians). The population collapse pools over *studies*. They are the same operation on
different axes, and each raises SNR by sqrt(n).

**The quantitative prediction.** Structure (a persistent offset at a place) does not shrink under
pooling; entropy shrinks as 1/sqrt(n). So the contrast between them grows as sqrt(n):

| studies pooled | contrast gain |
|---|---|
| 58 labeled | ~7.6x |
| n unlabeled, if usable | sqrt(n) |

**Unverified:** 4410 is the count of study *rows in the tables* (train plus test), not the count of
studies whose pixels are on disk. The local test series are probably only the public sample. The
usable number must be counted through `open_corpus` before any claim of a 66x gain is made, and
the founder has said "We only need the 58 labeled studies." Whether unlabeled studies enter at all
is his ruling, not a consequence of this arithmetic. It can be tested directly: compute the map on nested subsets and watch the
structure-to-entropy contrast scale as sqrt(n). If it does not, something is wrong with the
registration or the normalization, not with the idea.

§1.4 states the same law on the time axis: "A steady drift at velocity v grows in proportion to
the span, and a random wander ... grows as the span's square root, so doubling a span doubles the
one and multiplies the other by only sqrt(2)." The knee's axis is the population, and the law is
identical.

**A squinted view is a measurement, not an approximation.** §1.3: "A squinted view is **lossless
for what it measures**. A tile's median is exactly that tile's median, with no error in it. The
view is lossy only against the full-fidelity signal it was made from."

## 2. The six views are the thesis's two photographs

§1.3, verbatim — this answers the founder's "how each instrument can serve as a lens":

> "A face is often recorded in two photographs, one from the front and one in profile: two views at
> right angles. The front view shows how far apart the eyes are and how wide the mouth is. The
> profile shows how far the nose stands out and how the jaw is set, which no front view can show.
> **Neither photograph is the face, and neither is wrong about it.** Each is a projection of the
> head onto one plane, exact about what it shows and silent about the rest, and what the face is,
> is what the two recover together. **Since each recovers what the other cannot, neither is judged
> by how much of the face it shows alone.**"

The knee's six views are those photographs. Sagittal reads the ACL and the menisci in profile;
coronal reads the collaterals and the joint space; axial reads the patellofemoral joint and the
posterior structures; the fluid-sensitive weighting reads fluid and oedema, the other reads
anatomy. **No view is judged by what it shows alone.**

And the chain rule, §1.3: I(X; Y1, Y2) = I(X; Y1) + I(X; Y2 | Y1) >= I(X; Y1), which "**needs no
assumption of independence**". A second view never lowers what is known, and correlation between
views costs nothing. This is the oracle's point 8 ("correlation isn't damning in and of itself")
in its formal form.

## 3. The thesis's own bone example — two of the 12 labels

§1.2, verbatim, and it is directly about this domain:

> "one identified thing can matter to two questions at once. **In an image of a bone, the edema
> around a fresh break is evidence for one question, whether a line that looks like a fracture is
> an active one. For another, where exactly the fracture runs, it is signal to take out of view.**
> Evidence for one question and signal to take out of another's view are two relevances of the same
> thing, and **to take a thing out of one question's view is not to count it as evidence against
> anything.**"

Contusion (marrow oedema) and Fracture are two of the competition's 12. The thesis already states
their relation: the same measured thing serves one question as evidence and another as signal to
remove, and removal is never a negative.

## 4. Randomness vs unprocessed information — the exact split

§1.2: H(X) = I(X;S,M) [**unprocessed information** — what more structure or an unmade reading
would remove] + H(X|S,M) [**randomness** — what nothing removes].

> "In a closed, lawful domain, nothing measured is noise... 'Noise' names the limit of a model, not
> a property of the world."

> "**Randomness, and neither noise nor error, is what a system cannot learn from.** A reading that
> is wrong, or noisy, with a legible trace of how it came to be so, is information: the trace says
> what went wrong and where."

The founder's "the baseline isn't noisiness, it's *entropy*" is this split exactly. The
disagreement map's job is to sort each place into the two terms.

## 5. §13.4 — the Precision Ladder: how the squint's scale is derived

This answers the open question of how coarse the view may be. It is **measured, rung by rung**.

> "**A decision drawn more finely than its data is less correct.** So a categorical decision, such
> as whether a cell is there, reads only as finely as it needs to, and fine arithmetic runs only
> where the system points to something significant."

The table's method, verbatim from the 8-bit cache row:

> "8 bits changed a movie's run **less than a random +-1-count nudge did**, 6 bits lost an
> annotated cell, 4 bits broke the composite"

**The derivation is a comparison against the data's own noise.** A reduction is free when its
effect on the outcome is smaller than the effect of a perturbation at the noise scale. Then walk
down the ladder and name the rung where something breaks. Not a tuned threshold — a measurement
against the noise floor, with the failure boundaries recorded.

The information ceiling is stated too: "a voxel spans 40 to 115 steps of the camera's flicker
(5.3 to 6.8 bits)". You cannot usefully carry more precision than the noise admits.

And the transform: "The cache takes the square root because the camera's flicker grows as the
square root of the light, **so the flicker spans about the same number of the code's steps at
every brightness**." Quantize in the variance-stabilized domain.

> "Each coarser rung is a new version of its encoding, **measured before use**, never a silent
> change of type."

## 6. The code: the noise law and its closed-form transform

`physics/flicker.py`:
- `flicker_equation(xs, sig, cnt) -> (a, b)`: "sigma^2 = a + b * brightness, least squares over the
  bins weighted by sqrt(count)."
- `frame_flicker(vol) -> (a, b, floor)`: the frame's own equation and floor.

`instruments/support.py`, `flicker_units(v, a, b, floor)`: the integral of dv/sigma(v) for
sigma^2 = a + b*v, in closed form — `(2/b)*sqrt(a + b*v)` above the floor, linear below. **After
it, one unit is one sigma at any brightness.** Derived from the measured law; nothing is fitted
to labels.

Each frame is read through its **own** equation (there is a test pinning exactly this).

## 7. The code: `change_field` — the difference field, already solved

`instruments/change.py`, contract verbatim:

> "About three quarters of the voxels never change between frames; the change resolves into
> **specks, cell-sized lumps and half-field sheets**... **Each region is somebody's reading (Law
> 34): a speck is the camera's photon statistics, a lump an object moving or changing, a sheet the
> specimen and the optics.** This hands each region on; **it calls none of them nothing**, and
> absence of change never says a cell is absent (Law 33).
>
> Change per voxel is the difference **in flicker units**, each frame read through its OWN flicker
> equation. Voxels that are fill (exact 0) in either frame are excluded. Regions are the connected
> components of change >= level (brighter) and <= -level (dimmer), **labelled separately by sign**.
> The level is the founder's. **Nothing below it is discarded: it is the unchanged share, and a
> later read may re-run at another level.** A repeated frame gives no region (the control)."

Each `ChangeRegion` carries: `sign`, `n_voxels`, `extent_um` (**physical units**), `fill` (region
voxels over bounding-box voxels — compactness), `peak_flickers`, `centroid_vox`. `ChangeField`
carries `unchanged_share`: "the share of imaged voxels in no region: **reported, never
discarded**."

**The instrument measures and classifies nothing.** The three-way sort is a later body's reading.
This is No Popery in the code.

**There is a null control**: `test_duplicate_transition_has_no_regions`.

## 8. The code: `embryo_background` — the global-reference lesson

`instruments/background.py`:

> "ONE fixed reference for the whole embryo, **not a per-window floor** ... This is the E4 fix — **a
> pure-noise window can no longer set its own floor, so its own max no longer clears it.**"

> "**Only MEASURED voxels count.** A camera's offset keeps every measured voxel above zero, so an
> exact 0 is fill — a region of the volume that was never imaged (**padding after registration or
> cropping**) — and a NaN is unmeasured too."

Measured consequence recorded in the code: "5 of 71 samples carry 5-28% zero fill, which pulled
the level down by up to half and set the noise to 0 when fill passed half the dark voxels."

Both lessons transfer directly: the knee's dispersion reference must be global per view, never
per-place-neighbourhood, or a pure-entropy place clears itself; and registration fill must be
excluded from every statistic, with coverage counted per place.

`region_background` reads a local `(level, noise)` where noise is "the robust spread (MAD ->
sigma) of the **below-level** voxels" — the noise is read from the quiet part only.

## 9. §13.7 — the module shape for Chapter 2

> "Functions are of three kinds, kept apart. A **measurement** returns a number or a field, with
> its scope and provenance. A **decision** returns an answer or an abstention, with the evidence it
> rested on, as a named word and never a bare true or false. An **orchestration** only moves values
> between stages."

> "Every categorical finding is kept as data where it is made: who made it, from which state and
> inputs, whether it answered, abstained or found a disagreement, and why... An abstention is kept
> like an answer, with the reason none was warranted."

## 10. §13.2 — how a level is used

> "A cosine is tested against a **level**, a ratio of two whole numbers **written down before the
> run it judges**."

> "The contract is **never a cosine per bank, averaged**. An average would give each bank one vote
> whatever it holds, and its answers would change with how the rows are grouped."

> "A comparison answers in words, 'reaches', 'short' or 'silent', so a pair with nothing to compare
> **abstains instead of failing**."
