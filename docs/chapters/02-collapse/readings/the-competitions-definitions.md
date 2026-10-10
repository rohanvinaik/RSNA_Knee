# The competition's own definitions — the tightest source for the 12

2026-10-10. From the competition's pinned Overview discussion (topic 733343, "Courtesy of Dr.
Jacob Kazam") and the host's answers in topic 733826. The founder's ruling was that the
finding-to-region map "is actually an objective fact... Find what the current standard approach
assigns for them." **The competition defines the domain, so its own definitions are the tightest
source and they outrank MOAKS and WORMS here.**

## The host's rulings (topic 733826, answering a participant audit)

| question | the host's answer |
|---|---|
| Were labels assigned independently from the images, not extracted from reports? | **"Yes"** |
| If image and report disagree, is the image-derived label authoritative? | **"Yes. Note that only a small sample of provided data contains both. It is intended to help participants surface this conclusion."** |
| Does a negative label mean confirmed absent, or not annotated? | **"It means the finding was annotated as absent"** |
| Are bilateral examinations associated with one StudyInstanceUID? | **"Yes. In clinical practice, both knees may occasionally be scanned under one StudyInstanceUID... the released report text or DICOM metadata was adjusted as needed to provide sufficient information for participants to disambiguate"** |
| Are the discrepancies annotation errors? | **"Discrepancies are plausible and expected because clinical reports typically involve one signing radiologist who created it for clinical care, and the image-based labels uses multiple readers with stricter image-based thresholds."** |

**A negative is a reading, not silence.** This is the host's own word and it settles a question that
mattered: a 0 in `train.csv` is an annotated absence, so `label_code`'s "0" is a measurement and
only a blank is "not_given".

## The three-legged stool is in this data by design

The founder, 2026-10-10: "when sources of truth are defined as correct but are incomplete but
overlapping in their coverage, then the places in which they seem to disagree are not noise to wipe
away, but are some of the MOST informative information we can have."

The host built exactly that, deliberately: **"It is intended to help participants surface this
conclusion."** The legs, each correct in its own frame:

| leg | who made it | its frame | its bias |
|---|---|---|---|
| the 12 labels | **two MSK radiologists independently, a third adjudicating disagreement** | research, image-only | stricter image thresholds; borderline graded negative |
| the report | **one signing radiologist** | clinical care | looser, prose, multilingual, written for a clinician |
| the images | the scanner | physics | what is actually there |

A participant's audit of 20 of the 58 (240 decisions) measured the first two legs against each
other: **82.5% agreement, positive predictive 73.1%, positive recall 80.0%** (TP 68, FP 25, FN 17,
TN 130). Examples where they diverge include a report whose impression reads "Synovitis of left
knee and massive joint effusion" against labels Effusion=1, Synovitis=0, and a Turkish report
stating "Lateral menisküs normal" against Lateral meniscus tear=1.

**That ~17.5% is not noise to clean. It is the stool's third leg speaking.**

## The label definitions, verbatim in criteria

The host's framing, which is this project's own law stated by the annotators:

> "In each case, **ambiguous or borderline findings ("on the fence") were graded as negative to
> favor specificity**."

> "Each study in the annotated reference set was **independently labeled by two subspecialty-trained
> MSK radiologists, with disagreements adjudicated by a third radiologist** to produce a single
> consensus ground truth. Labels are assigned at the level of the whole examination, for a single
> knee."

The gold labels are themselves a committee resolving by concurrence with adjudication, and they
abstain toward negative. The ground truth was built under this project's own epistemology.

### The three compartments (the competition's partition)

- **Medial**: between the medial femoral condyle and the medial tibial plateau, inner side.
- **Lateral**: between the lateral femoral condyle and the lateral tibial plateau, outer side.
- **Patellofemoral**: between the patella and the femoral trochlea, the groove on the front of the
  femur.

### The 12, with region and criterion

| finding | region | criterion, and what is graded negative |
|---|---|---|
| ACL tear | intercondylar notch (intra-articular) | complete discontinuity, or **>50% of fibers disrupted**; with or without secondary pivot-shift bone contusions. Mild signal change, degeneration or thickening without discontinuity is **negative** |
| MCL tear | along the inner side of the knee | high-grade partial or complete **acute** tear, disrupted fibers **and** edema within and adjacent. Low-grade sprains and chronic or remote stress changes are **negative** |
| Medial meniscus tear | medial meniscus | abnormal signal definitely contacting the meniscal **surface on at least two images**, or a morphologic abnormality (truncated, diminutive, displaced fragment). Intrasubstance degeneration not reaching the surface is **negative** |
| Lateral meniscus tear | lateral meniscus | the same criteria |
| Medial OA | medial compartment | a moderate or large area, **roughly 1 cm or greater**, of high-grade cartilage loss, **greater than 50% of cartilage thickness**, with or without subchondral marrow changes |
| Lateral OA | lateral compartment | the same |
| PF OA | patellofemoral compartment | the same |
| Joint effusion | the joint cavity | a **moderate or large** amount of fluid distending the joint |
| Synovitis | the synovial lining | inflammation and **thickening** of the synovial lining |
| Baker (popliteal) cyst | behind the knee, the characteristic location | a **moderate or large** fluid collection |
| Contusion | bone marrow of femur, tibia, patella | bone marrow edema-like signal from impact, **without a discrete fracture line** |
| Acute fracture | cortical bone | an acute **cortical break or fracture line** |

**Contusion and Fracture are defined against each other**: the same marrow signal is Contusion when
there is no discrete fracture line and Fracture when there is a cortical break. This is the thesis's
own bone example (§1.2) in the competition's words: "the edema around a fresh break is evidence for
one question... for another, where exactly the fracture runs, it is signal to take out of view."

MOAKS scores neither MCL nor acute fracture, which is why it could not supply those two. The
competition does. **No finding is now "source pending."**

### Scale criteria the speck can use, from the host rather than picked

- OA: an area **roughly 1 cm or greater**, at **>50% of cartilage thickness**.
- Meniscus tear: signal reaching the surface on **at least two images**.
- Effusion, Baker's: **moderate or large**, not any amount.

These are the domain's own statements of the smallest thing that counts, which is what §13.4's
upper bound needs.

### Plane assignments, from the host

> "the cruciate ligaments and menisci are well evaluated on **sagittal and coronal** images, and the
> patellofemoral cartilage on **axial** images."

### Why fluid-sensitive and fat-suppressed are perfectly correlated here

Measured earlier: 192 series carry both flags, 144 carry neither, none carries one alone. The
host's definition explains it, and it is not an artifact:

> "For the purpose of the 2026 Knee Abnormality Challenge, a 'fluid sensitive' sequence refers to
> one in which edema, hemorrhage, and other types of fluid appear bright **and fat is suppressed in
> some way**."

Fat suppression is part of the definition of fluid-sensitive in this corpus. The two columns are
one reading, by construction.

## Laterality, reconsidered

Measured: 181 of 336 series carry no laterality tag; 155 carry `Laterality` (96 R, 59 L).

The host's answer reframes this. Bilateral studies exist, and **"the released report text or DICOM
metadata was adjusted as needed to provide sufficient information for participants to
disambiguate."** So the tag's presence is likely targeted at the cases where it is needed to
disambiguate, not a uniform guarantee. It is still not a reliable universal lookup, so the mirror
remains a derived reading with the tag as a concurring check — but this is a deliberate design, not
an oversight.

## The mirror's geometry, from a public write-up (topic 746792)

A data-geometry fact, not an architecture: the mirror operation **differs by plane**.

> "Sagittal left/right mirroring **reverses the three slice channels**; coronal and axial mirroring
> **flips image width**."

A sagittal stack runs medial-to-lateral through the knee, so mirroring it is reversing the stack
order; a coronal or axial slice holds the medial-lateral axis in-plane, so mirroring it is a width
flip. The same write-up reports that a plane-agnostic width flip across every plane did **not** help
(0.940 to 0.939) while the plane-aware anatomical mirror did (+0.001) — evidence that the
plane-aware operation is the correct one.

## What is on Kaggle's side but not on disk here

The same write-up: "We trained on **4,349 report-labeled competition studies**; the 58
expert-labeled studies were excluded from training but reused for selection." So the 4,349 studies
that are table rows here do have pixels and reports **on the competition's side**. The founder,
2026-10-10: "There is no unlabeled pool--there is in the competition itself. But that's a LOT of
data, only worth adding in what we need, if it actually is helpful for the build."

Not fetched. Recorded as available if a measurement later shows it would help.

## Not taken

The public leaderboard's top single-model recipe is a CoAtNet at 0.949. Under this project's law a
competitor's completed score is a **greenfield ceiling, not ours**, and their design is never
grafted on. Nothing architectural is taken from it. What is taken here is the mirror's geometry,
which is a fact about the data, and the corpus accounting.
