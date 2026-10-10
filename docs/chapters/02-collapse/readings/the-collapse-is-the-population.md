# Chapter 2 — the collapse, resolved

2026-10-10. The lead's reading after: §4 whole, §5 whole, the symbolic trace of cell_tracking's
stage 0, two measurements of the corpus, and consultations with Fable and Codex. The founder's
teaching is in `src/knee/collapse/__init__.py`.

## What the collapse is, here

Cell tracking collapsed **depth** and **time**. The knee collapses the **population**.

The warrant is the same shape the thesis requires — a domain law that holds something nearly
constant, and the collapse flattens only that. The founder's law: knee MRI is highly structured,
patients are positioned and told not to move, every knee looks like a knee, and the tibiofemoral
joint line is a gross landmark in every study. So the population holds anatomy nearly constant.

The product is **not** a diagnosis and **not** a clean "normal". It is a *geography*: a map over a
common physical frame saying where studies genuinely disagree, with its complement positively
named as the knee's black.

## Why the mechanism works (the mechanical argument)

Pathology in the knee has an **address**. The ACL is in the intercondylar notch; the menisci at the
joint line; effusion in the suprapatellar pouch and the recesses; the MCL on the medial side; OA at
the articular surfaces. That is anatomy, not a statistical assumption.

Stack many registered knees and read where they disagree:

| source of difference | behaviour across studies | signature |
|---|---|---|
| acquisition noise | independent | concentrates nowhere |
| patient-to-patient anatomy | smooth, global | drift, not pockets |
| pathology | constrained to sites | concentrates where findings live |

The disagreement field has structure **because diseases have locations**. The founder's "the
baseline isn't noisiness, it's *entropy*" is the information-theoretic statement of this: entropy
has no address, structure has an address, and stacking is the operation that separates them.

## The operation, in order

1. **Group by view.** Six views, measured. Compare only within a view; fluid and marrow flip sign
   between weightings, so stacking across them is meaningless.
2. **One physical frame.** Millimetres, from DICOM geometry (Chapter 1 has it). Never a pixel
   frame — in-plane sampling varies 8x across the corpus.
3. **Mirror left knees to right.** Laterality from the tag, confirmed by the fibula's side.
   Unflipped laterality swaps medial for lateral, which is fatal for exactly four of the 12
   (Medial/Lateral Meniscus, Medial/Lateral OA).
4. **Normalize intensity per series.** MRI has no calibrated unit. Without this, "subtract"
   compares scanner gains. Either within-series quantile rank, or anchor dark = cortical bone and
   bright = fat (non-fat-sat) / fluid (fat-sat).
5. **Squint.** Median per tile at a physical scale.
6. **Align** by gross landmarks, a search over a known family, never a fit.
7. **Read the per-place distribution.** At each place p over the n_p studies present: the median
   m_p, the dispersion, and every residual. **Not** a single summary number.

## The discriminator — what actually separates entropy from structure

**Dispersion alone is not it, and this is the sharpest technical point.** Misregistration variance
goes as |grad m_p|^2 * sigma_align^2, so a plain dispersion map lights up **bone cortices** — the
steepest gradients in the image — and not pathology. The fix is mechanical and stays a measurement:
measure sigma_align from the landmark scatter, predict the edge variance, and carry it as its own
profile.

"Stubborn" holds four profiles, not two. Only the last is diagnostic:

1. spiky, per-study — entropy
2. smooth per-study trend — coil bias, positioning
3. stubborn-homogeneous — ordinary anatomic variation (size, cartilage thickness, marrow, vessels)
4. **stubborn-minority** — a subset of studies deviating in one direction at one place

What separates (4) is **distribution shape across the stack, not spread**. Three readings, each a
measurement against a derived reference, none a chosen threshold:

- **Tail excess.** SD_p / (1.4826 * MAD_p), or (Q95-Q5)/(Q75-Q25) against its Gaussian value 2.44.
  A homogeneous spread sits at the reference; a minority mixture exceeds it. The reference is
  *derived from the Gaussian*, not picked to separate gold.
- **Tail sign.** The skew's direction against the sequence's known physics (fluid reads bright on
  a fluid-sensitive sequence).
- **Across-study coherence of neighbours.** The correlation, over the study axis, of r_p with r_q
  at neighbouring places. Entropy gives ~0. Structure means *the same studies* deviate at p and at
  q. This is precisely the founder's "the variance isn't in one random study at a few random spots,
  it's PERSISTENT and consistent."

A **pocket** is a connected set of coherent places spanning at least the speck size. That
requirement doubles as the multiplicity control over ~10^5 places at N=58.

**On convergence, stated accurately.** The lead's pre-consult file
(`ch2_my_reading_before_consult.md`) records only one discriminator in writing: persistence under
stacking. The three sharpened statistics (pocket >= speck size, across-study coherence, tail
excess) came from Fable. The lead had reasoned toward scale and split-half reproducibility in
session but **did not write them down before opening the consultant's output**, so this is not an
independent convergence and must not be cited as one. Credit for the precise statistics is
Fable's. Under Law 9 a second reader is never warrant: these are admitted because the founder
asked for a consult-worked design, and they are marked as the consultant's throughout.

## Prevalence does not break it — it flips the sign

Measured: Effusion is positive in 35/58 (60%); MCL in 9/58 (15.5%).

Where prevalence exceeds 50% at a place, m_p is the **modal** knee, not the normal one, and the
normals become the tail. **The shape statistics still flag the place; only the direction reading
inverts.** The site is found either way. This is why the product is a disagreement geography and
not a "normal" reference — and it is why reducing a place to variance is wrong: variance is
maximized at 50% prevalence and weak at 15%, so a one-number summary systematically under-weights
the rare findings. The whole per-place distribution is the information. That is "score is
information, never a target" applied at the voxel.

## Stage 1/2 mapped to the knee

§5.2's black is **two filters in order of seniority**. The senior is "narrow and knowably correct";
where it fires "it decides alone". The junior "refines only what the senior keeps" and is local.
And §5.2: **"Stage 1 deletes nothing"** — a removal is "a decision by a reading entitled to make
it, kept as a record, never a discard."

The knee's version, following the founder's definition of black ("the space of the data that does
not actually ever relate in any way to the 12 possible categories, and the context needed to
resolve them"):

- **Senior filter** — anatomical reach. Outside the knee, or beyond the distance from the joint
  line within which any of the 12 can occur. Narrow, knowably correct, decides alone where it
  fires. This is the founder's own speck teaching: "if a knee diagnosis can only appear within X cm
  from the tibia-femur conjunction site, then stuff that's too far from it... isn't what we need."
- **Junior filter** — population silence. Within what the senior keeps, the places where the
  population never disagrees. If every study reads the same there, that place carries no
  discriminative information for any of the 12. Local, and it defers to the senior.

**Stage 2, the speck**, is scale: a pocket narrower than the smallest resolvable diagnosable damage
is not a finding, exactly as cell tracking removed "bodies narrower than 2 um".

## The squint's scale is derived, not picked

Three bounds, all measured, written before the run:

1. tile >= the coarsest through-plane spacing in the corpus (measured: up to 5.0 mm)
2. tile >= 2 * sigma_align, from the landmark scatter (to be measured)
3. tile < the span of the smallest region that must survive **as a region** (the meniscus body,
   2-5 mm)

**These cannot coexist isotropically with 4-5 mm slices.** The derived answer is therefore
**anisotropic**: in-plane about 2 * sigma_align, through-plane native. That incongruity is real and
goes to the founder.

Noise-floor check, both sides measured: the tile-median SD in air (outside the leg) must fall
below the stack's MAD.

A sub-millimetre finding (a meniscal tear line) is invisible at squint scale. **That is not a
flaw**: the collapse finds the *site*; the loop reaches down and resolves it. The bar is that the
meniscus survives as a region, not that the tear is visible.

## Two artifacts, and where the circularity actually is

- **A, label-free.** The frame, the dispersion geography, the coverage counts, the
  entropy/structure split. Unlabeled studies (4,410 available) may contribute. Its median is
  **modal**, never "normal".
- **B, label-aware normal.** Per place, the median over studies whose labels do not implicate that
  place — which requires an **authored finding-to-region map** (ACL -> notch, Medial Meniscus ->
  medial meniscus, Effusion -> cavity and pouch, Baker's -> popliteal fossa, Contusion/Fracture ->
  marrow). Study-level labels do not say which voxels are affected; that map is domain knowledge
  and is the founder's to author.

There is **no circularity between A and B**. The circularity is in **measurement**: scoring a
labeled study against a B that excluded its own lesion is leakage. Every bar read on the 58 must
use B built without study i. The hidden test is clean.

## What goes to the founder

1. Does the knee's collapse also flatten **depth within a view**, or does the population collapse
   stand alone and each view stay a 3-D stack? His "each image in the study" suggests slices are
   kept.
2. The squint tile cannot satisfy all three bounds isotropically. Anisotropic — in-plane fine,
   through-plane native — is the derived answer. Confirm.
3. What is the smallest feature that must survive the squint **as a region**? This sets the tile
   ceiling and is a domain question.
4. The finding-to-region map for artifact B. Which anatomical region does each of the 12
   implicate?
5. Rare variants (discoid meniscus, bipartite patella) are stubborn-minority too, and are not any
   of the 12. Are those the proper abstentions?
