# Codex on building `knee.lenses` — second reading, 2026-10-11

**Protocol.** The lead's own design was written first, in `workbench/consults/lenses.md`, before this
was opened. Codex is one independent voice, never warrant (`AGENTS.md`, law 9). GPT-6.1 Sol at high
effort, model-only home, read-only. No pixels, no identifiers were sent.

**What the lead takes from it.** Three corrections it reached that Fable reached independently, which
makes them evidence rather than one voice: there must NOT be one middle per series; the ternary band
must carry the witness population's own spread and not only voxel noise; and the structural fat
bootstrap as proposed does not identify fat. Its own strongest contribution is naming CORRESPONDENCE
as the missing contract, and the marginal-combination trap it prevents: one part of an object writing
"bright on non-FS" and another writing "dark on FS", combined into false evidence that any one place
showed both.

---

## Codex's answer, verbatim

## 1. Point-wise sampling: yes, but correspondence is the missing contract

**A conjunction does not require a common grid. It requires evidence that its readings concern the same tissue.** A common grid would not supply that evidence by itself.

Your existing B2 establishes a conversation between same-orientation acquisitions. Extending that to different orientations introduces a new obligation: object correspondence across acquisitions. DICOM LPS coordinates give physical geometry, but movement between series can put different tissue at the same coordinate.

There is also a sampling issue independent of movement. An MRI voxel measures signal over a spatial support; it is not an infinitesimal point. A thin cartilage layer might occupy most of one acquisition’s voxel and very little of another’s.

I would distinguish two permissible conjunctions:

- **Place conjunction:** native measurements have overlapping physical support, and that support is sufficiently contained within the same matched tissue territory.
- **Object conjunction:** different native measurements belong to the same matched object, but do not necessarily measure the same part of it. This supports an object-level statement only.

That distinction prevents a specific error: one part of an object writes “bright on non-FS,” another writes “dark on FS,” and their marginal counts are incorrectly combined into evidence that any place exhibited both.

A deterministic, non-interpolating construction is possible:

1. Represent each native sampling cell in physical coordinates.
2. Establish candidate object correspondence, retaining ambiguity.
3. Select native cells whose supports lie sufficiently inside the corresponding territory.
4. For place conjunctions, retain the physical intersection of the contributing supports.
5. Abstain where correspondence, containment, or overlap is inadequate.

“Enough containment” needs a recorded argument. Using the nominal voxel box is a geometric approximation to measurement support, not an exact account of the acquisition’s point-spread function.

Nearest-native-voxel sampling is another possible primitive, provided it reports displacement and support. It cannot silently assert “same place.”

**Interpolation is unnecessary if silence is permitted.** It becomes necessary only if you require a numerical reading at every arbitrary coordinate. Your native bilinear profiles already interpolate locally; that is compatible with avoiding resampled volumes. If reused here, record the contributing native samples and weights, and distinguish noise propagation from tissue-mixing error. Averaging reduces noise; it does not establish that the average belongs to one tissue.

My recommendation is native measurements first, local interpolation only where explicitly admitted, and silence across unsupported slice gaps. I cannot determine from this text whether your present object machinery supplies cross-orientation correspondence.

## 2. Structural bootstrap: the peripheral band is a candidate, not a fat witness

Your air-connectivity boundary can work exactly as described while the proposed fat reference still fails.

The band immediately inside that boundary contains skin before it contains subcutaneous fat. Depending on location, it can also contain superficial fascia, vessels, edema, scar, and partial-volume mixtures. Over the anterior patella, the subcutaneous layer can be thin enough that a fixed inward band reaches tendon, retinaculum, or bone. A lean knee can leave no sufficiently pure fat support at the acquisition’s resolution.

Thus, **position establishes “peripheral soft tissue,” not “fat.”**

A better structural candidate is a compartment:

- outside a candidate deep fascial envelope;
- inside the skin envelope;
- excluding the boundary layers themselves;
- retaining only portions thick enough to contain native measurement supports.

That is stronger than a fixed shell, but identifying the fascial envelope is additional work. I do not assume it is already solved. Failure to resolve it should leave a peripheral candidate, not promote that candidate to certified fat.

Other anatomically constrained candidates—such as the infrapatellar fat pad—can provide independent corroboration. They also have pathology and partial-volume failure modes, so they should not become unconditional standards.

I would separate the bootstrap into:

**structural candidate → relational acquisition evidence → admitted witness.**

This need not be circular. Candidate identity can be tested through pairwise within-acquisition orderings and suppression behavior before any candidate becomes the calibration reference. Where several assignments remain consistent, retain the ambiguity.

The other proposed references need the same treatment:

- **Muscle:** “bulk non-bone soft tissue” is not an identity. Tendons, fat, vessels, and segmentation mistakes enter that population. A bounded muscle-belly candidate is stronger than a volume winner.
- **Fluid:** a recess-shaped space is a candidate. Synovial thickening, blood, debris, and partial volume can occupy it. Distension alone does not establish a homogeneous fluid witness.

The bootstrap should be allowed to produce **no admitted reference**. A reference manufactured by necessity would undermine every later row.

## 3. The ternary band: use uncertainty of the comparison, not just voxel noise

Your construction is sound in principle, with one correction: the band should describe the resolution of **the difference being measured**.

For a transformed measurement \(x\) and a reference middle \(m\), define

\[
D=x-m,\qquad U=\text{uncertainty of }D.
\]

Then, with recorded argument \(k\):

\[
d=
\begin{cases}
-1 & D<-kU\\
0 & |D|\leq kU\\
+1 & D>kU.
\end{cases}
\]

If \(x\) and \(m\) each have uncertainty, both contribute. Their covariance matters when they share samples or noise. A median over many reference places does not have the uncertainty of one voxel.

Two distinctions matter:

- **Reference-estimation uncertainty** concerns how precisely you estimated the middle.
- **Reference heterogeneity** concerns whether one middle represents the witness population at all.

A heterogeneous mixture can yield a very precise median and still be an invalid reference. Do not hide that failure by widening the ternary band. Similarly, correspondence error and partial volume are not automatically additional Gaussian flicker.

### What sets the middle?

**No single whole-series median supports all the tissue statements you listed.** Its population changes with field of view, anatomy, and pathology. Being scanner-local does not make it semantically stable.

I would use named, witness-relative rows. For example:

- signal relative to admitted muscle;
- signal relative to admitted fat;
- signal relative to admitted fluid;
- signal relative to an admitted dark structural witness.

For each row, the middle is the robust location of that row’s admitted witness population, measured in the same acquisition. A median is reasonable for a sufficiently homogeneous population of eligible interior supports. It does not repair a contaminated population.

The witness population and resulting middle should be fixed before evaluating target objects. Otherwise an abnormal target can move its own standard.

This also resolves cartilage’s two-sided description: **below fluid and above meniscus are two comparisons**, not one “intermediate” threshold.

I read “STATIC MIDDLE” as requiring a stable reference for a declared row. Under that interpretation, a series-specific calibration is consistent with the thesis. If it instead means one universal raw-intensity middle, your proposal conflicts with it; the supplied description does not settle that semantic point.

Finally, \(k\) specifies an instrument’s resolution or error tolerance. Nothing supplied selects a unique value. It needs an explicit measurement rationale, never selection for label separation.

## 4. Row layout: separate acquisition, scale, and relation

I would preserve acquisition as the lens axis, while avoiding a forced translation of every sibling instrument.

**At native-support scale**, carry:

- witness-relative transformed signal;
- eligibility and measurement support;
- local gradient magnitude, with physical units and uncertainty;
- signed boundary-normal change where a boundary supplies the normal.

A gradient is inherently a multi-sample measurement. Its support must say so.

**At neighbourhood scale**, use physical dimensions rather than a fixed 16×16 count:

- local contrast against a declared surrounding population;
- dispersion beyond expected noise;
- boundary-normal profile shape;
- persistence or interruption of a band or layer;
- support fractions for each ternary digit.

Different voxel spacings make 16×16 different anatomical instruments. Physical neighbourhood dimensions should be arguments.

**At object scale**, carry:

- per-acquisition distributions of place readings;
- physically weighted support and unread support;
- heterogeneity and connected regions of differing readings;
- the amount of support on which a cross-acquisition conjunction was actually observed.

“Most places bright” and “a small bright region inside a dark object” must remain distinguishable.

**At plate or acquisition-field scale**, carry:

- witness locations and adequacy;
- reference uncertainty and consistency;
- regional signal or noise variation;
- acquisition coverage and declared acquisition role.

These describe the instrument and its context. They should not silently become tissue votes.

For the sibling’s named readings:

- **Gradient:** retains a direct analogue.
- **Contrast:** becomes comparison against a named witness or neighbourhood.
- **Split Quality:** belongs where there is an actual proposed partition—particularly object-production provenance.
- **Dark Share:** becomes the supported share below a declared middle, with unread support separately represented.
- **Composite:** should remain the bundle or a declared concurrence result. An arithmetic score would introduce compensation between instruments.

For relational banks, I would prioritize inward/outward normals, facing surfaces, enclosing relations, and anatomically meaningful directions. Eight compass directions can remain descriptive, but LPS directions alone do not encode “toward the opposing articular surface.”

For provenance banks, retain the object seed, prominence, basin construction, native contributing voxels, and conversation outcomes. Preserve B2’s eleven named outcomes alongside any numeric rows derived from them; a single conversation score would erase different remedies.

Every row needs, at minimum, its instrument identity, acquisition, scale, middle, band arguments, physical support, digit, and silence reason. Aggregation needs separate counts or volumes for −1, 0, +1, and unread support. Otherwise shading can make one readable place look unanimous.

## 5. A concrete high-confidence failure: a cyst becomes “marrow edema”

Consider a well-resolved intraosseous or subchondral cyst:

- dark on T1;
- bright on fluid-sensitive fat-suppressed imaging;
- enclosed by bone.

It satisfies your stated marrow-edema conjunction, potentially with clean measurements and strong acquisition agreement. Yet a bounded fluid cavity is not the same finding as edema distributed through marrow.

**The measurements can all be correct while the tissue interpretation is wrong.**

The conjunction establishes a multicontrast signal pattern inside bone. Distinguishing edema from a cavity requires spatial organization: cavity boundary, relationship to marrow, trabecular context, and relation to the articular surface. Some cases will remain indeterminate at available resolution.

Another failure is slow-flowing blood in a vessel: it can be T1-dark and T2/FS-bright, resembling a fluid witness. Vessel continuity and tubular topology matter.

This is why I would have later predicates consume names such as **T1-low/FS-high intrabone region** before assigning a finding. `lenses` supplies the readings; object and relation structure establish what those readings mean.

There is also a false-confidence mechanism independent of tissue ambiguity: two similar FS acquisitions are not automatically independent witnesses. Shared suppression failure, partial volume, or correspondence error can make them agree. Independence needs an account of shared failure modes, not merely distinct series identifiers.

## 6. Compute shape and cache boundary

These are implementation inferences, not timings. The text gives no volume dimensions or measured bottleneck, so I cannot establish feasibility within nine hours.

**NumPy suits** contiguous array work:

- variance-stabilising transforms;
- reference statistics;
- ternary comparisons;
- simple finite differences;
- masks and grouped support reductions.

Avoid allocating a full image-sized array for every possible row. Keep compact shared primitives and derive rows over eligible supports.

**Numba suits** irregular repeated work:

- native point and profile sampling;
- geometry-aware eligibility checks;
- traversal of sparse object places;
- cross-acquisition support matching;
- object-by-acquisition accumulation.

Your existing reference/SAME discipline is the appropriate admission route. Optimizations need to preserve digits, eligibility, silence reasons, and support—not merely approximate numeric agreement.

**Nothing supplied justifies new C or Rust.** First determine whether runtime is dominated by decoding, dense image operations, or irregular geometry. A compiled extension is warranted only for a measured residual that the existing implementations cannot adequately address.

I would cache at four boundaries:

1. **Acquisition primitives:** decoded stored values, geometry, noise-law results, transformed values.
2. **Object primitives:** territories, boundaries, normals, and construction provenance.
3. **Correspondence primitives:** source/recipient sample mappings, contributing indices and weights, eligibility, displacement, and support.
4. **Measurements before digitization:** witness statistics, differences, and uncertainties.

The fourth boundary makes changing a recorded band argument cheap without repeating decoding or geometry.

Keys need content identity, relevant DICOM geometry and intensity interpretation, algorithm versions, and applicable arguments. Correspondence keys need both acquisitions and the object/frame versions. Witness-derived measurements also need witness identity and selection provenance.

A filename is insufficient. Study identity is insufficient. A series UID alone does not establish unchanged pixels or geometry.

For execution, process studies independently and release their working volumes. Cache the reusable geometry and primitives rather than materializing a dense grid of every acquisition pair and row. I would measure bytes read, peak memory, native samples visited, and time per stage before choosing further optimization.

## 7. The questions still missing

**What establishes object identity across orientations?**  
B1 supplies per-slice territories, and B2 supplies same-orientation conversation. The cross-orientation conjunction needs an explicit identity contract between them.

**Which acquisitions does each conjunction require?**  
“Dark on everything available” is weaker than “dark on every required instrument.” Missing T1 cannot satisfy fluid’s T1 clause. Acquisition role also needs more than a coarse label where sequence parameters materially alter contrast.

**What makes a witness admissible?**  
Specify structural evidence, minimum eligible support, contamination checks, agreement requirements, and named failure outcomes. This is the foundation of the middle.

**How are spatial shading and fat-suppression failure handled?**  
A series-specific scalar reference addresses global scaling. It does not guarantee comparability across spatial bias within that series. A local-reference instrument would need its own explicit definition and provenance.

**Which findings are observable at the available resolution?**  
If no native support fits inside a structure, no amount of cross-acquisition agreement establishes a pure reading of that structure.

**Where does each row enter a decision?**  
Before expanding the bank, trace each proposed measurement to the object or relation predicate that consumes it. Otherwise a large fingerprint can remain descriptively rich but operationally inert.

**How does abstention reach the required numerical submission?**  
The benchmark eventually requires numbers. Define that export policy explicitly, preserving abstention internally and ensuring that a numeric fallback never becomes evidence of normality.

My strongest recommendation is to make **support, correspondence, and witness admissibility** first-class contracts before expanding the row catalogue. Those determine whether a conjunction is evidence about one tissue at all.
