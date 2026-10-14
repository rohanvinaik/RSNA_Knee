# Codex on the witnesses — second reading, 2026-10-11

**Protocol.** The lead's own design was written first, in `workbench/consults/witnesses.md`, before
this was opened. Codex is one independent voice, never warrant (`AGENTS.md`, law 9). GPT-6.1 Sol at
high effort, model-only home, read-only. No pixels and no identifiers were sent.

**The sentence the lead takes as the correction.** *"Resolving a compartment establishes where a
witness could live; it does not establish the material occupying it."* And its strongest form at the
end: an admitted witness needs TWO SEPARATELY EARNED CLAIMS -- its anatomical identity, and its
suitability as a material reference for this acquisition and spatial scope. Neither follows from the
other, and the lead's design had conflated them.

**What it reached that Fable reached independently**, and so is evidence rather than one voice: the
compartment/material distinction; that marrow can be drawn from the very object carrying the finding;
that Hoffa's posterior boundary as stated is wrong; that "large and fascia-bounded" is not an identity
for muscle; that a required fluid witness is not defensible; and that the between-witness disagreement
is CONFOUNDED and cannot be attributed to coil falloff alone.

**Its own strongest contribution**: the four failure codes are four different facts, not four
spellings of "fat absent" -- `BOUNDARY_UNRESOLVED`, `INSUFFICIENT_NATIVE_SUPPORT`,
`ACQUISITION_EVIDENCE_UNAVAILABLE`, `SINGLE_LEVEL_INCOMPATIBLE`; that a failed homogeneity test must
return `SINGLE_LEVEL_INCOMPATIBLE` and never `TISSUE_MIXTURE_CONFIRMED`, because mixture, spatial
bias and partial volume remain different explanations; and the question that lands on code already
pinned -- WHICH SPREAD ENTERS `digit_code`? Noise uncertainty, uncertainty in the estimated middle,
unresolved spatial variation and material heterogeneity are four distinct quantities, and
`witness_spread` currently admits all four, so the band could silently absorb an admission failure.

---

## Codex's answer, verbatim

## 1. Structural admission: the compartment is not yet the tissue

Your object-first design is sound, but its critical distinction needs to be explicit: **resolving a compartment establishes where a witness could live; it does not establish the material occupying it.** Acquisition evidence must carry that second obligation. A structurally correct compartment can contain uniformly abnormal tissue, so even a perfect homogeneity test cannot replace it.

**Subcutaneous fat.** “The first dark line inward” can be a fibrous septum within fat, a vessel wall, or an aponeurotic/tendinous surface where the fat layer is thin. Over the patella, the skin-to-first-dark-line compartment can include dermis and almost no fully supported fat. With subcutaneous edema, hemorrhage or postoperative scar, the anatomically correct subcutaneous compartment contains something other than a usable fat standard. On an FS acquisition, suppressed fat and fascia can both be dark: the required boundary may have no measurable contrast.

The air-connectivity condition establishes an exposed body surface. It does not identify the deep fascia or prove that the intervening compartment contains fat. Admission needs a resolved *skin–subcutaneous interface* and a resolved *deep boundary*, rather than treating the air–skin boundary as the beginning of pure fat.

**Marrow.** A correctly resolved cortical dome can enclose red marrow, fatty marrow, trabeculae, vessels, marrow edema, hemorrhage or an infiltrative lesion. Normal hematopoietic marrow alone defeats “bone interior means fat,” especially near the distal femur. A fracture-associated marrow abnormality gives the more dangerous case: the reference is drawn from the object carrying the finding.

The cortex establishes **medullary location**. It does not establish **fatty marrow composition**. Native-support eligibility excludes cortical partial volume but does not exclude internal trabecular partial volume.

**Hoffa’s fat pad.** The patellar tendon and trochlea do not close a unique three-dimensional compartment. Depending on slice and extent, the space between them includes synovium, joint fluid, fibrous bands and vessels. Distally, the anterior tibia becomes relevant; a trochlear boundary cannot simply be extended through slabs where it is absent. Medial, lateral and superior boundaries also matter.

Even a correctly identified Hoffa object may contain impingement-related edema, synovitis, hemorrhage or postoperative fibrosis. Superolateral Hoffa edema is a concrete case where the anatomical identity remains correct and the fat-reference identity fails.

**Muscle.** A fascia-bounded compartment away from air and bone can contain several muscles plus intermuscular fat, vessels, nerves and aponeuroses. The popliteal region is an obvious counterexample to identity by those exclusions. Within an actual muscle, an intramuscular tendon or fatty replacement can occupy eligible native supports. Strain, denervation edema or diffuse fatty infiltration can also make a structurally valid muscle unsuitable as a normal-muscle standard.

A muscle witness therefore needs an identified muscle belly and exclusions for its resolved internal structures. “Fascia-bounded non-bone compartment” remains a candidate code.

My confidence is high in these anatomical counterexamples. Whether your already-resolved objects distinguish them is unknown from the supplied text.

## 2. The circularity can be bounded—and sometimes avoided

A dark-line detector need not depend on a fat witness. It can detect a **local contrast relation**: a connected band measurably lower than its adjacent supports, with uncertainty expressed through the pinned noise law. Its contrast bar is an argument. Geometry then determines whether that band has the required continuity and anatomical relationship.

That gives a non-circular dependency order:

1. Native measurement support, noise and slab availability.
2. Local interfaces and relative contrast.
3. Structurally resolved candidate compartments.
4. Acquisition evidence for their proposed material identities.
5. Frozen witness populations and summaries.
6. Target digits.

The distinction is between “this band is darker than its neighbors” and “this band is dark against an admitted tissue standard.” The former can precede the standard.

However, **a locally dark band is still not necessarily fascia or cortex**. Geometry and acquisition evidence must resolve its identity, or the candidate remains unresolved. Where fat suppression erases the fascia–fat interface, this order should return silence; it cannot manufacture the boundary.

If your structural resolver already uses the fat digits that these witnesses will establish, then there is a real dependency cycle. The smallest honest version is a provisional, locally contrast-supported candidate followed by an explicit consistency check. Keep the provisional code, forbid it from evaluating findings, and admit only when the stated constraints hold. If different admissible interpretations produce different witnesses, return `AMBIGUOUS_WITNESS`. Convergence of an iteration alone does not establish anatomical correctness.

## 3. A deterministic noise test can refuse a single level; it cannot prove tissue purity

There is an unavoidable limit here: **two tissues can have indistinguishable readings in the available acquisitions.** No deterministic intensity test can always detect their mixture. Conversely, one tissue under a varying receive field can produce a heterogeneous intensity population.

The honest measurable question is:

> Is this structurally selected population compatible with one transformed signal level under the noise law?

For independent, approximately Gaussian transformed measurements \(z_i\), with noise uncertainties \(\sigma_i\), a concrete test is

\[
Q=\min_\mu\sum_i\frac{(z_i-\mu)^2}{\sigma_i^2}.
\]

Under that null, \(Q\) has a \(\chi^2_{n-1}\) distribution. Refuse the single-level model when

\[
Q>\chi^2_{n-1}(1-\alpha),
\]

where **\(\alpha\) is a declared false-refusal policy argument**, never selected against gold labels. This is a noise-calibrated decision bar, not a tissue-separation cut.

There are three necessary qualifications:

- “One flicker equals one sigma” does not alone establish Gaussian tails or independence. If the pinned law does not provide those, the stated chi-square calibration is unavailable.
- Correlated reconstruction noise requires the corresponding covariance-aware residual statistic and null calibration. Counting correlated voxels as independent would manufacture evidence.
- The population must be selected structurally and frozen. Removing intensity outliers until it passes would manufacture a homogeneous witness.

A failed test should return something like `SINGLE_LEVEL_INCOMPATIBLE`, **not `TISSUE_MIXTURE_CONFIRMED`**. Mixture, spatial bias and unresolved partial volume remain different explanations.

A pass means `NOISE_COMPATIBLE`; it does not mean histologically pure. Small populations should also carry their limited ability to detect heterogeneity. A precise median and a passed weak test are not sufficient admission evidence.

For your per-slice middle, test compatibility at the scope that middle represents. If a slice contains a spatial gradient beyond noise, a scalar slice reference is inadequate even when every support contains fat. Widening its tissue band would conceal the spatial failure.

## 4. Fluid: sensible to omit as a required witness, unjustified to forbid categorically

I know of no knee fluid compartment that guarantees enough pure native support in every normal study. Physiological synovial fluid exists, but its thin distribution may provide no eligible supports. A distended recess, bursa or cyst can provide measurable fluid, but its availability may itself be associated with pathology.

So **a required fluid witness is not defensible**.

Nevertheless, “the recess is an effusion finding” does not by itself invalidate the fluid signal as an optional reference. Fluid amount and fluid composition are different properties. A sufficiently supported population of simple fluid could provide acquisition evidence while effusion is decided from the constructed compartment’s extent. Hemorrhagic, proteinaceous or debris-containing fluid would require refusal or a different identity.

The risks are that witness availability becomes coupled to the finding, or that the target supplies its own material standard. Those dependencies must remain explicit.

Your replacement comparisons are useful proposed relations, but they need acquisition eligibility: actual T1/T2 weighting, effective fat suppression and valid muscle/fat references. Tissue existing anatomically does not guarantee an admitted witness in the acquired field of view.

## 5. Preserve three rows; do not require blind agreement between them

I would emit all three comparisons, with separate admission codes, locations, spreads and slice/series provenance. Three scalar comparisons per place are unlikely to be the significant computational cost.

Nearest-witness selection introduces an artificial seam: a small movement across the selection boundary can change the reference and digit without changing the tissue. Distance also does not guarantee matching receive sensitivity or fat suppression.

But **three emitted rows do not justify an unconditional tissue conjunction over all three**. A fat place can be above one remote fat witness and below another because of exactly the spatial disagreement you intend to measure. Requiring identical responses would turn the stool’s information into a refusal condition.

The consumer needs an explicit account of comparability: either the rows remain contextual relations, or a stated spatial model transports references to the place before a tissue decision. Without such an account, neither “nearest” nor “all three” establishes a location-independent tissue class.

There is also an attribution limit. Disagreement between these witnesses contains contributions from receive-field variation, spatially varying fat suppression, different fat/water composition and witness contamination. **The disagreement is measured; its exclusive attribution to coil falloff is not established by three fat objects alone.** Keep your bias-field reading, but distinguish its directly observed component from the causal interpretation. Three locations also cannot identify an arbitrary three-dimensional field merely by having three different radii.

## 6. What I expect to fail first across studies

I cannot determine the earliest empirical failure across your 58 studies from this text.

My prediction is that **resolving a fascia-bounded, fully supported subcutaneous population across acquisitions** fails before the statistical middle does. Thin anterior fat, thick or anisotropic supports, cropping and weak fascia contrast under FS are ordinary acquisition conditions.

The honest output would distinguish:

- `BOUNDARY_UNRESOLVED`: a required interface is not established.
- `INSUFFICIENT_NATIVE_SUPPORT`: the compartment exists but supplies no eligible measurements.
- `ACQUISITION_EVIDENCE_UNAVAILABLE`: material identity cannot be checked.
- `SINGLE_LEVEL_INCOMPATIBLE`: the selected readings cannot support one level.

Those are different facts, not four spellings of “fat absent.”

The next failure I would watch is slice-to-series fallback. A series middle is a different spatial reference; it does not repair a missing local witness. If consumed without that distinction, the output can contain confident digits that change systematically along the stack while anatomy remains stable. A global population may either fail compatibility because of genuine spatial variation or pass with a precise middle that is locally inappropriate.

## 7. The questions still missing

**What makes acquisition evidence specific to the named tissue?** This is the largest unfinished contract. Structure plus noise compatibility can admit a uniform scar, a uniformly edematous marrow region or the wrong uniformly dark compartment. Each witness needs stated positive material evidence, its required acquisitions and its refusal codes.

**What does “native support fits” mean physically?** Voxel dimensions alone do not describe the reconstruction response. Real supports can have tails, and through-plane slice profiles are not ideal boxes. Eligibility needs a declared support model; any tolerated contribution outside the compartment must be an argument.

**Can the witness itself carry the finding?** Freezing it before target evaluation prevents target-dependent adaptation. It does not prevent a diseased marrow or Hoffa population from becoming the frozen standard. You need an explicit dependency record wherever a candidate witness overlaps the object or relation being evaluated.

**How are references carried between acquisitions?** A witness resolved in one series does not automatically provide the same material support in another. Registration uncertainty, different orientations and slab gaps can turn valid structural identity into unavailable acquisition evidence.

**Which spread enters `digit_code`?** Noise uncertainty, uncertainty in the estimated middle, unresolved spatial variation and material heterogeneity are distinct quantities. Their roles must be named before anything is placed in `witness_spread`; otherwise the band can silently absorb an admission failure.

The strongest version of your design is therefore an admitted object with **two separately earned claims**: its anatomical identity, and its suitability as a material reference for this acquisition and spatial scope. Neither claim follows automatically from the other.
