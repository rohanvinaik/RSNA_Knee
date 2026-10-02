# The Knee by the Recipe: Laws, Lenses and Agencies

**Status:** DRAFT for founder sign-off (2026-10-02). Not a build spec until signed. This works the
recipe of *What an \<Object> Is* (Vinaik and Claude, 2026-10-01, §13.1) for RSNA Knee Abnormality
Detection. It fills in the intelligence layer that `THEORY_OF_THE_CASE.md` Part III left as a sketch,
on top of the data layer of Part II.

**Supremacy.** This document is derived. Where it is silent, ambiguous or wrong, these govern: the
founder's statements, the thesis, `THEORY_OF_THE_CASE.md` (its Laws 1–8 are binding here), and the
cell-tracking project's `HDC_SUBSTRATE.md`. The two uploaded sources are pinned below; add them to
`REFERENCE_MANIFEST.yaml` on sign-off.

| Source | sha256 |
|---|---|
| *What an \<Object> Is* (`what_an_object_is.md`) | `93c7438d9532dd3ea88f77250b3c148c4a35f371d3103025774a95b86d95ad7d` |
| `HDC_SUBSTRATE.md` (cell-tracking project) | `0fd0df63eeed1a7d546ef86b0a14bb507f764193edacf05fe28a7e8897ea15b4` |

## The task in the founder's words (verbatim)

> "We just need to build the right set of laws and lenses in this domain, and "KneeDiff" […] and the
> λ-trajectory are just the first and most elegant of them, with that document I uploaded last time
> as a rich vein to mine for even more!" (2026-10-02)

> "Where an image is showing just a generic shape of a knee, resolvable as a hypervector
> representation of the knee, kind of like stage 1/2 from the thesis there resolves away the
> "background" cleanly, so no heavy compute or reasoning is wasted on that which we know is
> insignificant. So the "knee", or the lesions, it can become MUCH more than 0.1% of the volume of the
> image." (2026-10-02)

---

## 0. The mechanism, restated (AGENTS.md step 2: confirm or correct)

- **The platonic reference.** For each kind of series, N registered true normals are squashed, voxel
  by voxel, into a distribution (mean, spread). The spread is the voxel's tolerance: wide where normal
  knees vary, narrow where they agree.
- **The subtract (KneeDiff).** A study is registered into the same space. Each voxel's deviation from
  its reference distribution is z = (x − μ − smooth trend) / max(σ, floor). Voxels the reference
  licenses (|z| < 3) are **the knee's black**: the stage 1/2 of the thesis, resolved away, so no
  reasoning is spent on them. As in the thesis, the black deletes nothing. It is a decision kept as a
  record, and the voxels stay for any lens that reads raw data (the λ-trajectory does). What survives
  is **the residual**, and the residual is the picture everything after reads. In it, lesions are a
  large share of what is left, not 0.1%.
- **A lens** is a cheap, deliberately lossy view that measures one thing and knows no question
  (thesis §3.2). Here there is one lens per term of a law (§3 below).
- **The λ-trajectory.** For an always-present structure, sweep how hard its prior is applied (λ = 0
  raw data, λ = 1 full consensus) and read the shape of the confidence curve:
  - `MONO_UP`: the structure matches normal;
  - `PEAK_DROP`: the structure is there and deviates, so a finding;
  - `MONO_DOWN`: wrong lens, meaning the structure is not where the atlas puts it. That is the
    registration-error channel;
  - `AMBIGUOUS`: flag.
- **Do not port the genomic reading of tightness.** In GenomeVault a large deviation where the law is
  tight means an error. In KneeDiff a large deviation where the population is tight means pathology.
  The knee keeps two separate references, and they must stay separate: the population spread, for
  pathology, and the registration law (the NCC score; `MONO_DOWN`), for input error.

---

## 1. From cells to knees: what changes

| | Cells (the thesis) | Knees (here) |
|---|---|---|
| The \<object> | A nucleus. How many is unknown; find them all | Two kinds. **Structures** are always present, one of each, placed by the atlas (ACL, menisci, MCL, cartilage plates, bones). **Lesion-objects** are present or absent, and live in the residual (fluid collections, marrow edema, fracture lines, signal inside a tear) |
| The question | Is this one cell? Where did it go? Did it divide? | Is this known structure abnormal? Is there a lesion-object, where is it, and which finding is it? |
| Time | ~100 time points; anchors, following, division | None. One static study |
| Independent views | Four focus lenses, each at its own depth | ~5.5 series per study (24,371 series over 4,407 studies): planes × contrasts |
| Teaching signal | An expert's calls, a few dozen | A radiologist's report on every training study (~4,400, in about a dozen languages, often naming locations), plus 58 gold re-reads |
| Output | Every cell at every time point, linked | 12 graded scores, ranked by macro-AUC |

**Consequence.** Most of H1's object-finding comes free: the atlas places the structures, and
KneeDiff clears the normal knee. The work is in **meaning** (H3, H4) and in **concurrence across
series**. Today's build reads one series per study, so every concurrence has a single voice.

---

## 2. The laws (recipe step 1)

**L1. Anatomy: the platonic knee.** Every knee has the same structures in the same arrangement, one
of each. After mm-true registration with chirality made canonical, each voxel's normal intensity is a
distribution (KneeDiff). *One structure, one place:* every voxel belongs to exactly one zone.

**L2. MR signal: the instrument's physics.** A tissue's brightness is set by its relaxation under the
sequence, and fat suppression removes fat's signal. So a tissue has a **signature**: one digit per
contrast bank.

| Tissue | Fluid-sensitive, fat-suppressed (PD/T2 FS) | T1 |
|---|---|---|
| Free fluid (effusion, cyst) | + | − |
| Fat (marrow, Hoffa's pad, subcutaneous) | − | + |
| Fibrous (ligament, tendon, meniscus, cortex) | − | − |
| Marrow edema (contusion) | + (inside bone) | − |
| Hyaline cartilage | 0 (intermediate) | 0 |

**A finding is a zone together with a change of signature.** A meniscus zone (normally `−,−`) turning
`+` on FS is fluid signal in a meniscus. A bone zone (normally `−` on FS, `+` on T1) turning `+,−` is
edema. In residual terms: the voxel deviates from its own normal, and the signature names what the
deviation is. The contrast banks play the role of GenomeVault's complementary banks, each silent
where the other speaks.

A **law-given censor** comes with L2: the *magic-angle effect*. A fibrous structure lying near 55° to
the main field brightens on short-TE sequences only. Signal seen on short TE but absent on long TE, at
that angle, is the instrument, not a tear.

**L3. Acquisition: the squint.** Each series is sharp in-plane (sub-millimetre) and coarse between
slices (~3–4 mm). A structure is read in the series whose plane holds its long axis:
- **sagittal:** ACL, PCL, the meniscal horns;
- **coronal:** MCL, LCL, the meniscal bodies, the tibiofemoral joint space;
- **axial:** patellofemoral cartilage, the retinacula.

This is the thesis's "each lens at its own sharpest depth," moved from depth to plane.

**L4. Pathology: radiology's own laws.** Each term below becomes a lens.
- *Tear, in fibrous structures.* Normally dark on every sequence; a tear is fluid signal within. For
  a meniscus, the signal must reach an articular surface on at least two slices: the radiologists'
  two-slice-touch rule (De Smet and Tuite, 2006). Intrasubstance signal that does not reach the
  surface is degeneration, the canonical near miss.
- *Ligament course.* The ACL runs parallel to the intercondylar roof. A tear shows as a gap, as fluid
  signal, or as a flatter course.
- *Fluid.* Joint fluid pools in the recesses, so an effusion is a recess (first the suprapatellar)
  distended beyond normal. A Baker's cyst is fluid in the bursa between the medial gastrocnemius head
  and the semimembranosus tendon, joined to the joint by a neck between them.
- *Marrow.* A contusion is edema: geographic, often under the cartilage. A fracture is a line inside
  the edema (dark on T1) that reaches the cortex.
- *Synovitis, without contrast.* A change of signal in Hoffa's fat pad (FS-bright in fat that should
  be FS-dark), and effusion-synovitis. These are the MOAKS surrogates.
- *OA, by compartment.* Cartilage loss, joint-space narrowing, marginal osteophytes, lesions in the
  bone under the cartilage, meniscal extrusion. MOAKS gives the subregions.

**L5. Mechanism: how events co-occur.** An injury writes a pattern across structures:
- **pivot-shift:** ACL tear, with "kissing" contusions on the lateral femoral condyle and the
  posterolateral tibial plateau;
- **valgus:** MCL, with lateral-compartment contusion;
- **patellar dislocation:** contusions on the medial patella and the lateral femoral condyle;
- **dashboard:** contusion on the anterior tibia, with PCL injury.

OA is compartmental: its signs co-locate in one compartment. These are the knee's "events keep the
domain's rules," and they let agencies corroborate one another (supporting only, §6).

---

## 3. The lenses, one per law term (recipe step 2)

Each lens may abstain. Nothing is averaged, and only the commit reads a lens as for or against.

| Lens | Law | Reads | Measures (one thing) | Its one open quantity |
|---|---|---|---|---|
| Deviation (KneeDiff) | L1 | every series, every zone | ternary digit against the voxel's own normal | z threshold (~3) |
| Signature | L2 | one voxel across co-registered series | which contrast banks deviate, and which way | none (signs) |
| Plane | L3 | the series whose plane holds the structure | where in the study to read the structure | the plane, given by anatomy |
| Surface contact | L4 tear | meniscus zones, sagittal and coronal | slices on which deviant signal touches the zone's surface | minimum slices (2) |
| Course | L4 ligament | ACL, PCL and MCL centerlines from landmarks | continuity of the dark band; its angle to the notch roof | sampling step |
| Recess volume | L4 fluid | suprapatellar recess, posterior recesses, popliteal zone | fluid-signature volume; distension | none |
| Marrow | L4 marrow | bone zones | edema-signature extent; under the cartilage or deep | minimum extent |
| Line | L4 fracture | inside committed edema, after its halo is removed | a linear component in what is left | minimum length |
| Fat pad | L4 synovitis | Hoffa zone (to add) | FS-bright share in normally FS-dark fat | none |
| Gap | L4 OA | compartment zones | femur–tibia distance; nearly free from `anatomy.joint_line` | none |
| Margin | L4 OA | compartment margins | marginal outgrowth in the residual | none |
| λ-trajectory | structure prior | each always-present structure | the trajectory's shape | the λ grid |
| Magic angle | L2 censor | fibrous zones, short-TE vs long-TE series | the structure's angle to the main field; signal present only at short TE | none |

---

## 4. One study, start to finish

```
 A STUDY: ~5–6 series (planes × contrasts), each a 2.5-D stack
     |
 PRIORS, read once from the DICOM headers: vendor, field strength, sequence family, fat suppression,
     plane, spacing -> the regime key
     |
 PER SERIES, each in its own canonical space against its own platonic reference
     register (mm-true, chirality-canonical): the one bounded utility (Law 3)
     KneeDiff -> THE BLACK: what the reference licenses, resolved away
     |
     +--> STRUCTURE LENSES: for each always-present structure, the λ-trajectory over its zone
     |        MONO_UP normal · PEAK_DROP abnormal · MONO_DOWN not where the atlas puts it
     v
 THE RESIDUAL: only what the reference does not license. Lesions are now a large share of it
     |
 THE LOOP on the residual, round by round:
     bodies    contiguous same-sign deviant regions, by zone; specks below a law's minimum cleared
     lenses    each structure read in its plane; signature across contrasts; contact, course, volume
     commit    by concurrence of independent views (planes, contrasts); disagreement kept; may abstain
     pull-out  each committed lesion-object leaves with its halo (partial-volume rim; edema around a line)
     re-read   the residual again: the site search, and reaching inside committed edema for a fracture line
     ... until a round takes nothing: THE EMPTIED BOX
     |
 THE CANDIDATES, each written in one language: zone, signature digits per contrast, shape, surface
     contact, route out of the loop, regime
     |
 THE AGENCIES (§5): recall against cases within a trust radius; censors veto; concurrence decides or abstains
     |
 EMISSION: 12 graded scores (§9)
```

**Middles live on the residual.** A residual metric's static middle is set at that metric's terciles
over the residual cells of the teaching studies, never over raw voxels. Once the black is cleared,
"top third" means top third of what deviates.

---

## 5. Clean signals and the agencies (recipe steps 4 and 6)

**The reports teach; gold establishes.** A report is one radiologist's original read, in words,
independent of every pixel computation. That makes it clean for what an agency learns. It is noisy as
a label: the II.7 parser scores 77.7% against gold, and gold is an expert *re-reading the images*. So
even a perfect report reader is capped around 0.88–0.92 against gold (an 18th-place write-up,
<https://huggingface.co/blog/bishnoiyash/rsna-competetion>). Hence:
- reports, through the parser, are the **expert's calls**: they become cases, each keeping its source;
- the 58 gold studies and the held-out true normals **establish**;
- a disagreement between report and gold is a finding, kept.

**Localized calls.** Extend the II.7 parser to pull out location words (posterior horn, body, anterior
horn; medial or lateral; condyle, plateau, patella; recess names). A report sentence then becomes a
call on a (zone, finding) pair: the knee's version of an expert's call on a candidate.

| Agency | Its question | Its oracle (teaching only) | Law checks that support it | Findings it serves |
|---|---|---|---|---|
| Fluid | Is there excess fluid, and where? | localized report calls; gold | fluid only in recesses and bursae; a Baker's is posteromedial, with its neck | Effusion, Baker's, Synovitis (with the fat-pad lens) |
| Marrow | Is there edema? Is there a line in it? | report calls (bruise, contusion, fracture); gold | edema inside bone; a fracture line inside edema, reaching cortex | Contusion, Fracture |
| Fibrous structures | Is this ligament or meniscus torn? | localized tear and degeneration calls; gold | a meniscal tear touches the surface on ≥2 slices; a ligament tear breaks continuity or course | ACL, MCL, Medial Meniscus, Lateral Meniscus |
| Compartments | Is this compartment degenerated? | report OA and chondral calls with a compartment; gold | OA signs co-locate in one compartment | Medial OA, Lateral OA, PF OA |
| Every finding (the count's analog) | Was any finding missed? | the report's list of findings: which ones, never where | every reported finding is explained by some committed object | all |

The **every-finding agency** mirrors the thesis's every-cell agency. In teaching, "the report says
this knee has a Baker's cyst" means keep looking (site search, reaching down). It supports and never
trims: nothing committed is removed to match a report.

Across agencies, the **mechanism laws (L5)** are concurrence between independent questions. A
PEAK_DROP on the ACL together with committed contusions in the pivot-shift pattern corroborate each
other. Each is still established only by its own oracle.

---

## 6. The law checks (recipe step 5)

All of these support a judgment; none establishes one.
- **One lesion, one place, across views.** A lesion seen on sagittal must land in the same
  patient-space place on coronal or axial, where they cover it. This is the knee's sandwich: two
  views in place of two anchors.
- **No two objects in one space.** One tissue and one lesion per voxel; zones are exclusive.
- **Well formed.** Shape and size laws per object: a tear is thin and touches a surface; edema is
  geographic; a cyst is rounded and has its neck; an effusion lies in the recesses.
- **The emptied box.** After every commit, no lesion-shaped deviation is left in the residual.
- **Events keep the rules.** Mechanism patterns (L5); OA's compartment coherence; a fracture lies
  inside edema.

---

## 7. Measure the substrate before teaching (recipe step 7)

- **H2's bridge.** Do the profiles of objects the reports call apart actually differ? Name the hard
  pairs and measure each:
  - meniscal tear vs. intrasubstance degeneration (see Q3);
  - contusion vs. fracture;
  - effusion vs. synovitis;
  - MCL sprain vs. a normal MCL.
- **View independence.** This is the gate from `HDC_SUBSTRATE.md` F.4 #4. Measure the errors of
  sagittal vs. coronal vs. axial lenses, and of FS vs. T1, on gold, before their agreement counts.
  Independence must come from different evidence, not different encodings.
- **The make-or-break**, the repo's fixed instrument, rerun on the multi-series substrate.

---

## 8. Teaching and judging (recipe steps 8 and 9)

- **Curriculum, one per agency, in order of what each consumes.**
  1. *Fluid,* first: an effusion changes how everything else looks.
  2. *Marrow.*
  3. *Fibrous structures:* they need contact and course.
  4. *Compartments:* they need several co-located signs.
  5. *Every finding,* last.
- **Teaching sheets.** The structure proposes candidates; localized report calls word them; the
  founder's eye takes the hard sheets. Near misses become censors carrying a *named* difference. The
  surface-contact digit separating a tear from intrasubstance signal is the textbook case.
- **Memory is cases, never prototypes** (thesis §7.1). Each case is kept, recall goes to the nearest
  case within a trust radius set against chance, and censors veto. `tools/lens_eval2.py`'s
  majority-bundled prototypes stay as a data-layer instrument, never as the decision.
- **Judging.** Each agency by its trajectory on held-out gold: identified, abstained and wrong, per
  finding, never summed. Then one end-to-end number: macro-AUC on gold.

---

## 9. The output contract (macro-AUC)

AUC rewards order and nothing else. Decide-or-abstain alone would pile ties at 0.5. Proposal:
**emit a rank, not a verdict.**
- Score each finding from its evidence, ordered: first its decision (+1, abstain, −1), then how many
  independent views concur, then the recall margin or the λ-peak height.
- Decided positives map above 0.5 and decided negatives below.
- Abstentions sit at 0.5, ordered among themselves by partial evidence.

This bends Law 7 ("abstain → 0.5") without fabricating confidence: the numbers are ranks, not
probabilities. **Founder decision** (Q4).

---

## 10. What this changes in the current build

- **Series.** Fetch each study's planes and contrasts (the `train_series.csv` flags), register each
  into its own canonical space, and squash one platonic reference per series type.
- **Atlas.** Add zones for the meniscal horns and bodies, the ACL and PCL centerlines, the MCL band,
  Hoffa's fat pad, and the cartilage plates per compartment. Add coronal and axial atlases.
- **Parser.** Extract locations, so calls are localized.
- **Memory.** Cases, trust radii, censors, as in §8.
- **Template stubs.** `domain_classifier`, `bank_evaluator`, `emission_policy`, `coherence`,
  `healing`, `lexicon`, `evidence` and `pipeline` are text-extraction scaffold. Repurpose them as the
  agencies and the emission policy, or delete them (Q7).

---

## 11. Open questions for the founder

1. **The laws.** What is missing or wrong in L1–L5?
2. **The λ peak.** With an additive overlay and a dot-product decode, the raw margin is linear in λ,
   so the peak must come from a nonlinearity. Which one does GenomeVault use (normalization, a
   best-vs-second margin, quantizing after the overlay)? If it is normalization, the sweep reduces to
   a closed form in a few λ = 0 quantities.
3. **Meniscus labels.** A third-party summary describes them as "tear/degeneration". If degeneration
   counts as positive, the two-slice-touch difference separates two positives, not a positive from a
   negative, and the censor flips role. Verify against the competition's label definitions.
4. **Emission.** Rank abstentions by partial evidence, or keep them all at exactly 0.5?
5. **The expert.** Reports as localized calls for teaching, gold for establishing, and your eye on
   the hard sheets: right split?
6. **Series scope.** A reference for every plane × contrast, or start with sagittal FS, coronal FS
   and one T1?
7. **The template stubs.** Repurpose as the agencies, or delete?
