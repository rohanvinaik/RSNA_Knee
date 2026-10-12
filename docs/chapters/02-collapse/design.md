# Chapter 2 — the design

2026-10-10. Written before the build, per SPINE step 5. Every element carries its provenance:
**[F]** the founder's words, **[T]** a thesis section, **[C]** a sibling-code symbol,
**[M]** a measurement made here, **[A]** a consultant (admissible because he asked for a
consult-worked design; never warrant under Law 9).

## Scope of this dated design

This is the 2026-10-10 population-collapse design and its noise-law plan. It is
retained as intent/history, not a description of the current native-digit or
object-analysis entry point. Later founder teachings refine the route, runtime
vocabulary, static middle and breadth-first build; start at `../../OBJECT_MODEL.md`,
`../../PIPELINE.md` and `../../BUILD_PLAN.md`. No population reference is claimed
implemented by this document. The cited `ch3_the_level_problem.md` was retired;
current static-middle teaching is in `../03-lenses/teachings.md`.

## What the chapter produces

A **disagreement geography** per view: a map over a common physical frame saying where the 58
studies genuinely differ, with its complement positively named as the knee's black. Not a
diagnosis, not a clean normal. **[F]** "a single, resolvable starting ground that highlights what
ACTUALLY matters".

The collapsed axis is the **population**. The warrant is the founder's law **[F]**: knee imaging
is highly structured, patients are told not to move, every knee looks like a knee. The thesis
permits flattening only what the laws hold nearly constant **[T §4.5]**.

**The math [T §1.3]:** pooling n readings raises SNR by sqrt(n), and "blur is pooling in space" —
so the squint (over tiles) and the population stack (over studies) are one operation on two axes.
Measured: n = 58 **[M]**, so the gain is ~7.6x. There is no unlabeled pool on disk **[M]**.

## Law 5 argument for reuse

Law 5 permits reuse only where a chapter argues it is the best approach. Three sibling units are
ported, and the argument is the same in each case: each solves a problem this chapter provably
has, and each encodes a measured failure we would otherwise rediscover.

| ported | why | the measured failure it already encodes |
|---|---|---|
| `physics/flicker.py` + `flicker_units` **[C]** | differences must be commensurable across intensity before they can be compared | a reading in raw units means different things at different brightness |
| `instruments/change.py::change_field` **[C]** | the difference field, as signed regions at a declared level, measuring and classifying nothing | "it calls none of them nothing"; the unchanged share is reported, never discarded |
| `instruments/background.py::embryo_background` **[C]** | one global reference, never a per-window floor | "a pure-noise window can no longer set its own floor, so its own max no longer clears it" |

The structure is kept; the **noise family is replaced**, because MR is not a photon counter.

## The stages, in order

| # | stage | provenance |
|---|---|---|
| 1 | **regime key** per series: the noise law, zero share, signedness, normalization flag, laterality | [T §5.1] cheap readings taken once where their input first exists |
| 2 | **flicker units**: the variance-stabilizing transform, tabulated per series | [C] `flicker_units`, [A] Rician family |
| 3 | ~~level map per series: decile landmarks~~ **REFRAMED 2026-10-10: dark-referenced ternary encoding and whole-field regime indexing.** There is no level map. See `ch3_the_level_problem.md` | [F] the confluent/sparse homology; [C] `light_above`, `digit_of`, `regime_facet`; [T] §5.1 |
| 4 | **laterality and the mirror**: derived reading, tag as a concurring check | [M] 181/336 series carry no tag |
| 5 | **the squint**: tile medians at a physical scale, with the fill rule | [T §1.3, §13.4] |
| 6 | **the common frame**: physical millimetres, coverage mask propagated | [M] pixel grids differ 8x; physical extent does not |
| 7 | **registration**: similarity transform from gross landmarks, a search over a known family | [A] |
| 8 | **the population reference**: per place, median m_p, spread s_p, coverage n_p, leave-one-out | [A] |
| 9 | **the difference field**: signed connected regions at a declared level, in population sigmas | [C] `change_field` |
| 10 | **region measurements**: extent, fill, sign, peak, N-coherence, recurrence. **No classifier** | [C] "it calls none of them nothing" |

## Stage 1 in detail — the first build unit

### The noise law: keep the structure, replace the family

The sibling fits `sigma^2 = a + b*brightness` because a photon counter jitters more where it is
brighter **[C]**. MR magnitude is Rician: in that parameterization it is **b ~ 0 with a
sub-additive dark end**, so the affine fit would read a false positive slope **[A]**. Keep one law
per series, the transform as the integral of dv/sigma(v), and a linear continuation below a floor.
Replace `(a, b)` with `(sigma_g, L)`.

Derived constants, not picks: Rayleigh variance 0.429 sigma^2; E[M^2] = A^2 + 2L sigma_g^2 exactly;
the moment ratio E[M^4]/E[M^2]^2 = (L+1)/L, so **L = 1/(ratio - 1)**; MAD-to-sigma 1/0.6745;
1.4826 as its reciprocal form.

### Two estimators that must concur

**[A]**, and justified by measurement **[M]**: 62 of 336 series are over 20% zeros, where an
air-based estimator has no air and returns zero — the zero-fill failure verbatim **[C]**.

- **E_bg** — the quiet population, taken as the lowest share of finite values *wherever it lives*,
  never a designated corner. This is `region_background`'s move **[C]**: noise is "the robust
  spread of the below-level voxels". It abstains, with a named code, when that population is
  degenerate (all zeros, or no spread).
- **E_fg** — the bright regime, from pseudo-residuals against neighbours at a lag beyond the noise
  correlation length. Robust to a masked background, because it never reads the background.

Concurrence within sampling error is **the measurement that one stationary law holds**;
disagreement is **a named code, never a refit** **[A]**.

The sampling error of a sigma estimate from n samples is **sigma/sqrt(2n)** — derived. How many
standard errors count as concurrence is a **bar**, and under Law 4 it is written down before the
run it judges. It is therefore an explicit argument to the decision, never a constant inside it.

### What is measured, decided, and orchestrated (kept apart, [T §13.7])

- `noise.py` — **measurements**: quiet population, moment ratio, Rayleigh sigma, pseudo-residuals,
  MAD sigma. Each returns a number or a field with its scope.
- `codes.py` — **decisions**: named codes, total over their arguments, pure, Detective-pinnable.
- `regime.py` — **orchestration**: a `Series` in, a `RegimeKey` out. Moves values; decides nothing.

### Named codes stage 1 must return

Every zero kept apart, as Chapter 1 does **[C]** `stack_codes`:

- the quiet population: `readable` / `background_masked` / `no_spread` / `too_few`
- the coil count: `single` / `multi` / `implausible_ratio` / `unmeasurable`
- concurrence: `concur` / `disagree` / `bg_abstained` / `fg_abstained` / `both_abstained`
- storage: `unsigned` / `signed_nonnegative` / `signed_negative` **[M]** 103/336 declare signed,
  5 actually hold negatives, all ORIGINAL/PRIMARY/GDC
- normalization: `normalized` / `plain` / `unknown` — **[M]** `NORM` appears in 65 series, and a
  vendor gain field makes sigma_g spatially varying **[A]**

## Bars, and what is the founder's

Under Law 4 no level is chosen to separate gold or to move a score, and every bar is written
before the run it judges. These are **not** settled and must not be invented:

| open | status |
|---|---|
| the change level, in population sigmas | **his** — the sibling's contract says "the level is the founder's" **[C]** |
| the coverage count n_p below which a place abstains | **his** |
| concurrence tolerance, in standard errors | **his**; the standard error itself is derived |
| the quiet-population share | to be derived from the measured zero-share distribution, not picked |
| the smallest region that must survive the squint | **his**, or from the finding-to-region map |

Consultant-suggested numbers that are **picks, not bars**, and are recorded as such rather than
used: fill 0.3-1, U1 ~ 2 mm, U2 ~ 3 mm, the >= 32 mm bias tile, M/sigma >= 3.

## The finding-to-region map (artifact B, not needed for stage 1)

His ruling **[F]**: "that's actually an objective fact, not something I should be vibing in chat
about. Find what the current standard approach assigns for them."

The standard is MOAKS, with WORMS behind it. MOAKS assigns findings to named subregions **and to
specific views**: effusion-synovitis on axial (retropatellar space, suprapatellar bursa, capsule);
Hoffa synovitis in the infrapatellar fat pad on sagittal; meniscus anterior and posterior horns on
sagittal and body on coronal, medial and lateral; ACL intact-vs-tear with marrow lesion at its
insertion or origin; Baker's cyst in the popliteal fossa; cartilage and marrow lesions over 14-15
subregions (patella medial/lateral, femur trochlea/central/posterior medial and lateral, tibia
anterior/central/posterior medial and lateral, subspinous).

**Source still pending** for MCL and Fracture: MOAKS scores neither (it is an OA instrument).
WORMS (Peterfy 2004) covers the collaterals. Each finding gets a cited source or is marked
"source pending" — never filled from priors.

## Logged, and immaterial by definition

His ruling **[F]**: "the domain space is defined by the competition. If it's not one of the 12,
then to me it doesn't exist. Log it, we'll come back to it when it comes to 'noise correction' if
needed, but for establishing the ground for this project, it's immaterial by definition."

**Log:** a stubborn-minority region belonging to none of the 12 — a discoid meniscus, a bipartite
patella, a rare normal variant — is not a category of this chapter. Chapter 2 does not model it,
name it, or abstain on it. Revisit only at a noise-correction pass, if one is needed.

## Build-time and run-time

- The population reference is built offline and shipped as a private dataset with lineage and
  checksums (Law 7, override 7).
- The per-study difference field is computed at run time, inside the kernel's budget (override 6).
- **Every reading on the 58 uses the leave-one-out reference**, or it is leakage **[A]**.
- Every kernel has a NumPy reference first; an accelerated twin only through the SAME harness
  (override 2).

## The null suite (the chapter's acceptance, written before the runs)

**[A]**, with Codex's correction that an air null is a predicted excursion rate, not zero regions:

| null | required |
|---|---|
| study against itself | no region at any level |
| study against itself, shifted one tile | only edge dipoles; this **measures** sigma_align's signature |
| two same-weighting series of one study | specks at the predicted rate, no lumps |
| air | speck rate 2*Phi(-level); unavailable where the background is masked |
| odd/even corpus halves | pocket-map overlap far above chance |
| un-mirrored knee | unchanged share collapses |
| per-place permutation over studies | N-coherence to zero |
| reference with and without study i | the 1/n_p self-share |
