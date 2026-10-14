# Chapter 2 — the flicker port, the profiles, the nulls, the squint scale

2026-10-10. Consultation round 2 (Fable and Codex, both on the cell-tracking code trace and the
measured corpus). The lead's own measurements are in `ch2_measured_noise_floor.md` and
`ch2_measured_geometry_spread.md`. Second readers are one voice, never a verdict.

**A provenance correction, recorded because the record must be accurate.** The round-2 prompt
(`scratchpad/ch2_consult_round2.md`) opens with a correction of a round-1 answer. That correction
was written for **Codex**, whose round 1 contained the category error it names (judging a stage-0
device by whether it delivers a diagnostic verdict). The lead reused the same prompt file for
**Fable**, whose round 1 contained no such error — it had already named the statistics and given
the anisotropic tile. Fable received a rebuke meant for another reader, answered under its rules
regardless, and flagged the misattribution itself. The error is the lead's. Nothing in Fable's
round-1 or round-2 content is retracted by it.

## 1. The flicker port: keep the structure, replace the family

The sibling code fits `sigma^2 = a + b * brightness` because a photon counter jitters more where
it is brighter. **MR magnitude does not work that way.** In `flicker_equation`'s terms, MR is
**b ~ 0 with a sub-additive dark end**, and the affine fit would read a false positive slope.

So: **keep the structure** — one law per series, the transform as the integral of dv/sigma(v), a
linear continuation below a floor — and **replace the family `(a, b)` with `(sigma_g, L)`**.

The Rician law, for per-channel complex noise sigma_g:
- At A = 0 it is Rayleigh: mean 1.253 sigma_g, variance 0.429 sigma_g^2.
- **E[M^2] = A^2 + 2 sigma_g^2, exactly.** So A^2 is read as `M^2 - 2 sigma_g^2`, unbiased, and
  **never as M^2**.
- Var(M) rises monotonically from 0.43 sigma_g^2 to sigma_g^2 (0.86 at A/sigma_g = 2, 0.94 at 3).
  The whole swing is about 2.3x — far gentler than the photon case.
- Bias reaches 1.25 sigma_g at the dark end.
- Multi-coil sum-of-squares is noncentral-chi with 2L degrees of freedom,
  E[M^2] = A^2 + 2L sigma_g^2, and **L is measured from the background moment ratio
  E[M^4]/E[M^2]^2 = (L+1)/L**.

### Two estimators, required to concur

This is the answer to the failure the lead measured (air-based sigma returns 0.0 on
background-suppressed series).

- **E_bg** — measured air voxels, never fill: sigma_g^2 = mean(M^2) / 2L, with L from the moment
  ratio.
- **E_fg** — the Gaussian regime, voxels with M/sigma_g >= 3 (**a bound derived from the Rician
  law, not chosen**): pseudo-residual eps = (M - mean of 4 neighbours) * sqrt(4/5), then
  sigma_g = MAD(eps)/0.6745. Neighbours must be at a lag >= the noise correlation length (the
  lag-1 autocorrelation of eps; **zero-filled 960 matrices show 0.5-0.7, where lag 1 under-reads
  sigma_g** — and this corpus contains 960 matrices).

> "E_bg ~ E_fg within sampling error (~ sigma/sqrt(2n)) is **the measurement that one stationary
> law holds**. Disagreement is a **named code, never a refit**."

That is No Popery applied to the noise law itself: two independent authorities, concurrence
assigns, disagreement is kept as a finding.

### The transform

f(M) = integral from 0 to M of dv/sigma(v), with sigma^2(v) the Rician variance at the measured
(sigma_g, L) — closed form in I0 and I1, **tabulated once per series (4096 entries) by
quadrature**. Above about 3 sigma_g it reduces to M/sigma_g minus a constant, which is exactly
`flicker_units`' `b <= 0` branch. Below, f' stretches the dark end by up to 1.53x, **so air is
unit-sigma too** — which the air null needs.

### What breaks it, and how each is detected

| cause | effect | detector |
|---|---|---|
| vendor normalization (PURE, SCIC, CLEAR, prescan-normalize) | sigma_g becomes a smooth field sigma_g(x) | E_bg != E_fg, **and coarse-tile (>= 32 mm) sigma varying beyond sampling error**; the measured field then divides both |
| parallel imaging (GRAPPA/SENSE) | g-factor non-stationarity, correlated noise, non-Rician background | approximate stabilizer, **non-integer L reported** |
| vendor background masking | no measured air | **E_bg abstains, code BACKGROUND_MASKED**; the moment identity failing is the detector |
| sigma_g < 1 LSB after RescaleSlope | unmeasurable | a named code |
| motion ghosts | eps anisotropic along phase-encode vs readout | a sheet (see profiles) |

**The limit, stated plainly:** "M/sigma_g cancels gain but **not SNR** (coil, field, bandwidth,
averages, voxel size): **flicker units normalize noise, not level.**" A per-series *level* map is
a separate operation — foreground decile landmarks measured from the series alone — and its
residual is a sheet.

## 2. The knee's `change_field`

- `before` = the view's reference: per-place median `m_p` over the `n_p` studies measured there,
  in level-mapped flicker units.
- `after` = study i, registered, squinted, in its own units.
- `change_{i,p} = (x_{i,p} - m_p) / s_p`, with **`s_p` = 1.4826 * MAD over the stack at p**.

> "the reference read through its OWN noise law, **which the population measures per place instead
> of inferring from brightness**"

That is what the population axis gives that a two-frame difference cannot: a per-place noise
reading, measured, not modelled. Floored at `sigma_tile,i = sigma_g,i * sqrt(pi / 2 n_i)`, the
tile median's derived noise — the below-floor branch.

- `level_flickers` = the founder's level, in **population sigmas**. Nothing below it is discarded;
  re-runnable at another level.
- `unchanged_share` = places measured in i and covered (n_p >= the declared count) that fall in no
  region. This is **the founder's "most of it subtracts out into near-noise", as a number**. A
  study far below the corpus's typical share is itself a sheet event.
- What the population axis loses relative to time: **"sign means brighter/dimmer than the
  reference, never appeared/vanished."**

## 3. The profiles, with their measured separators

| profile | separators |
|---|---|
| **speck** | extent <= speck size; peak just above level; random sign; N-coherence ~ 0; **per-study count matching the predicted rate 2*Phi(-level) * tiles** |
| **lump** | extent between speck size and structure scale; fill 0.3-1; one sign; N-coherent; plus recurrence (studies carrying an overlapping same-sign lump there) and tail excess |
| **sheet** | level-map residual (whole field, one sign, low peak); coil falloff / fat-sat failure (small distance to the imaged boundary, ~half field); motion ghosts (bbox aspect along phase-encode); **misregistration: edge adjacency, the fraction within one tile of high \|grad m\|, with an opposite-sign twin — a dipole**; laterality (both signs, unchanged_share collapses) |
| **fill** | not a region at all |

The **dipole** is the distinctive misregistration signature: a shift makes a bright region on one
side of an edge and a dark one on the other. It is measurable and it is not a lump.

The speck count has a **predicted rate**, so the instrument's own noise behaviour is checkable
rather than assumed.

## 4. The global-reference lesson, ported exactly

The knee's version of the E4 failure, naming the view at risk:

> "`s_p` from n_p = 13 (Axial (0,0)) is itself a draw; **a chance-tight place sets a tiny s_p and a
> modest residual clears the level** — the per-window floor, per place."

Measured: Axial (0,0) is present in only 13 of the 58. Also at risk: a per-window *bright* anchor,
which can be the lesion itself.

Fixes: one sigma_g per series; one level map per series from the whole histogram; **s_p floored by
sigma_tile,i and reported beside the view-wide median, so `s_p / median(s)` is a reading carried on
every region**; no s_p below the coverage count.

**Fill, defined completely:** exact 0, NaN, outside the FOV, beyond the end slabs' half-thickness,
padding. Never in E_bg, the histogram, the tile median (**a tile under half measured is fill — the
median's breakdown point**), n_p, change, or `unchanged_share`'s denominator. Fill share and n_p
are reported.

> "A masked background counted as data gives sigma_g = 0: **the zero-fill lesson verbatim.**"

Independently derived, and it matches what the lead measured on this corpus.

## 5. The null suite

| null | what must happen | what it calibrates |
|---|---|---|
| study against itself | no region at any level | exactness |
| **study against itself shifted one tile** | only edge dipoles, variance \|grad m\|^2 delta^2 | **measures sigma_align's own signature** |
| two same-weighting series of one study | specks at the predicted rate, small motion sheets, **no lumps** | the instrument on real repeat data |
| air | speck rate = 2*Phi(-level), nothing else | the dark end of the transform (unavailable when masked) |
| **odd/even corpus halves** | pocket-map Jaccard >> chance overlap | the concurrence of the map itself |
| un-mirrored knee | **unchanged_share collapses** | laterality, before anything else runs |
| **per-place permutation over N** | coherence -> 0 | the N-coherence statistic's own null |
| B against B_{-i} | the 1/n_p self-share | leave-one-out leakage |
| level sweep in air | follows the Gaussian tail | the level's meaning |

Codex's caution stands and is right: an air null is **not** "no regions" — the Rayleigh
distribution has unbounded support. Its null is the **predicted excursion rate**. "No pocket
whatsoever" is an exact-copy requirement, not a stochastic-air one.

## 6. The squint scale, derived per axis

Per axis: `max(L1, L2, L3) <= t <= min(U1, U2)`.

**Lower bounds**
- L1: the coarsest native sample at that view — measured: 0.8 mm in-plane, slice spacing to 5.0 mm
  (median 3-3.5).
- L2: **2 * sigma_align**, the MAD->sigma scatter of landmark positions after alignment, per axis.
- L3: the noise correlation length (eps autocorrelation below 1/e; about 0.5-1 mm on zero-filled
  matrices).

**Upper bounds**
- U1: the thinnest structure that must survive **as a band** — cartilage 2-4 mm, meniscus 2-5 mm,
  MCL 2-4 mm, measured on m as band width: about 2 mm.
- U2: the smallest pocket divided by 3, so that `fill` is readable: about 3 mm.

**In-plane:** 0.8 <= t <= 2 mm, **satisfiable if and only if sigma_align <= 1 mm. That is the
registration bar, and it is written before the run.**

**Through-plane:** L1 reaches 5 mm, above U1. **Not satisfiable isotropically.** Derived:
t_xy = 2 mm; t_z = native spacing when sigma_align,z <= spacing/2, else twice the spacing, against
a depth upper bound of the medial-lateral separation (~40 mm), which holds.

### The anisotropy resolves itself

> "**Every structure's thin dimension is in-plane in some view: the three-plane protocol is itself
> the answer to the anisotropy.**"

The ACL is thin, and sagittal reads it in-plane. The MCL is thin, and coronal reads it in-plane.
The protocol acquires three planes precisely because each structure is resolved in-plane in at
least one of them. So through-plane coarseness in one view is not a loss — the view that reads
that structure in-plane carries it. This is §1.3's two photographs again, and it **withdraws the
lead's escalation of the anisotropy as a problem**.

Also measured: n_i per tile spans 6 to 400 across the 0.1-0.8 mm corpus, so sigma_tile,i is
per study, never one number.
