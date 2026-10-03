# The design walk: the design read against the lens principle (2026-10-03)

The principle is the rigid oracle and supersedes the architecture document (founder, 2026-10-02 23:59:57Z). This file
reads the design, KNEE_ARCHITECTURE ("ARCH") and the book, against it. Every classification here is a **proposal** for
the founder's ruling. He: "with an interpretation provided by the structure of the problem space (And me, you with my
approval)". Nothing in the design changes until he rules.

## The test, in his words (`../../FOUNDING_PROMPTS.md`)

- A lens "simply measures … Properly-designed lenses are never wrong, by definition" (23:50:20Z).
- Lenses "that do not encode a specific 1:1 relationship to a specific element of "truth", do not have authority to
  warrant a decision unilaterally" (23:50:20Z).
- "A single lens can assign a value (or assign that something is *not* <X> …), but only if it is inherently a
  measurement of truth." [3,5,7] warrants "only odd primes", not "always only odd primes", unless "ANOTHER lens says
  that the set is complete as is"; then "the truth is a CONJUNCTION of both lenses" (00:10:18Z).
- "+1/0/-1 for both": "assignment/abstention/rejection" for a lens with a strict warrant; "evidence for/abstention/
  evidence against" for one that is directional only. The truth table is "an explicitly encoded operation in balanced
  ternary, a strictly defined subset of the truth table, possibly … more than one single path to truth" (00:18:12Z).
- Which combinations reject or abstain: "That's what building this project is meant to answer". A committee decides:
  "a positive decision, a negative decision, an ambiguous one, or even … a majority decision with a noted dissention".
  Independence is not required: "dissention between lenses that are otherwise positively correlated can be some of
  the most *valuable* pieces of data". "The enemy isn't correctness or noise, it's *entropy*" (00:27:25Z).

## The classes

| class | meaning | consequence |
|---|---|---|
| **M** | a measurement: one objective fact | stands; a lens is never wrong |
| **T1** | a statement of truth that *is* what one lens measured | one lens may assign or reject: +1/0/−1 as assignment/abstention/rejection |
| **C** | a statement that needs a conjunction: other lenses (often completeness or coverage) and a law of the problem's structure | warranted only as that conjunction, which is an encoded path of the truth table. Until he approves it, the single reading is directional evidence |
| **B** | a statement beyond any measurement listed for it | not warranted. Either restated as evidence or as what was measured, or defined carefully by him |
| **R** | a rule of the design that conflicts with his committee or independence words | proposed for change; he rules |

## Part 1. The lenses, and what each "rules out" (ARCH §2.8, Tables 2.8a and 2.8b)

ARCH rule 4, "Each lens declares whether it counts for, against or both", is read under the principle as follows. A
direction *of the measurement*, such as brighter or darker, or rising along ⟨x,y⟩, is M. A "counts for or against a
finding" is the meaning layer: T1 or C where warranted, otherwise evidence.

| # | lens | measures (Table 2.8a) | "rules out" (Table 2.8b) | proposed class | why |
|---|---|---|---|---|---|
| 1 | Deviation | z of the voxel against its series type's reference | "digit 0: no lesion at this voxel, in this series" | value M; the rule-out **B** | it measured "the value lies within the population's tolerance". "No lesion" is a tissue state it did not measure: the "always odd primes" case. Unless he *defines* lesion as deviation beyond tolerance, the licensed digit is directional evidence against a lesion, not a rejection |
| 2 | λ-trajectory | the shape of identity × fidelity as the zone blends toward its reference (bands of ‖z‖²/p̂_S; the placement margin) | "MONO_UP: the structure is normal, as read. MONO_DOWN: it may not be where the atlas puts it" | value M; MONO_UP's "normal" **B** unless defined; MONO_DOWN's "may not be" is evidence | MONO_UP measured "deviation energy within its range in health". "Normal" claims more, and "as read" already hedges it |
| 3 | Signature | the pattern of contrast digits at one place across co-registered series | "FS-dark is not fluid; T1-bright marrow is not edema" | digits M; both rule-outs **C** | each joins a measured digit to a signal law (fluid is FS-bright; edema is T1-dark) under stated conditions (ARCH Table 4.1: "red marrow; no T1 series; T1-bright blood products"). Encoded meaning, not a single reading's authority |
| 4 | Magic angle | θ, the fiber's angle to B0 | "outside the window: the instrument's explanation" | θ M; the rule-out **C** (close to T1) | θ outside the window joined to the dipolar law (3cos²θ − 1) rules out the magic-angle explanation of short-TE brightening |
| 5 | Fat suppression | the share of fat voxels left FS-bright and T1-bright | "edema and Hoffa signal where FS brightness is unsuppressed fat" | share M; the rule-out **C** | FS-bright with T1-bright, joined to the suppression law. A conjunction of two contrasts and a law |
| 6 | Coverage | effective slices crossing the zone along the question's axis | "a series as witness for a structure (its silence there is not absence)" | **T1** | "this series cannot see that zone along that axis" is what it measured |
| 7 | Surface contact | slices on which a deviant component inside the dark meniscus touches its surface | "a tear: in a segment dark on every covering slice, or where intrasubstance signal makes no contact" | count M; "no tear" **C** | no contact on any covering slice, *and* every slice covered (completeness), *and* the two-slice-touch law. Exactly the [3,5,7] completeness case. Q3 (does degeneration count?) stays his |
| 8 | Bow tie | contiguous slices on which the body is one band joining the horns | "a displaced bucket-handle fragment" | count M; the rule-out **C**; "for, when fewer than expected" is evidence | the expected count, sagittal coverage of the body, and the displacement law |
| 9 | Extrusion | mm of meniscus beyond the plateau margin | "extrusion, where the edge lies within the margin" | **T1** | extrusion *is* meniscus beyond the margin, so "no extrusion" is what it measured (silent where an osteophyte blurs the margin) |
| 10 | Continuity | the longest run along the centerline without fibrous signature, against the ligament's own reference | "a complete tear, where the band is whole; a partial tear, in uniformly fibrous segments" | run M; "no complete tear" **C**; "no partial tear" **C**; "no injury" (the official label) **B** | a whole band plus coverage of the whole band rules out a complete tear. A partial tear needs the signal law too. The official label is "injury", and a sprain can leave the band whole, so continuity cannot reject the label (the fact the accord recorded) |
| 11 | Angle | the angle between the ACL band's axis and the roof line | "nothing on its own" | M; "for only" is evidence | consistent already |
| 12 | Recess volume | fluid-signature volume per recess | "effusion, where every recess is empty" | volume M; "no effusion" **C** | every recess empty, *and* every recess seen (coverage, so the set is complete), *and* the law that joint fluid pools in the recesses |
| 13 | Neck | whether a fluid path joins the collection to the joint between the tendons | "Baker's, for a collection with no neck" | M; "not Baker's" **C** | "no neck seen" joined to the anatomic definition of a Baker's cyst, with resolution enough to see a neck. "A neck thinner than a slice" is a failure ARCH names: silence, not absence |
| 14 | Marrow | edema-signature extent, with depth | "edema, where marrow is T1-bright" | extent M; the rule-out **C** | as lens 3's T1 rule, with its conditions |
| 15 | Line | the length of a linear dark component reaching cortex | "nothing on its own; "a fracture lies within edema" censors lines outside edema" | M; "for only" is evidence; the censor **C**, conditional | his words: "fractures have concomitant edema when they're relatively fresh". So the censor holds for fresh fractures. Whether gold counts old fractures is a fact ARCH leaves open ("old fractures, if gold counts them") |
| 16 | Fat pad | the FS-bright share of normally dark fat | "Hoffa-synovitis, where the pad is uniformly dark" | share M; the rule-out is **evidence against**, not a rejection | synovitis is read "through surrogates" without contrast (ARCH §2.5). A surrogate's absence is directional evidence |
| 17 | Cartilage | the share of the plate where cartilage gives way to fluid or bone | "cartilage loss, where the plate is intact" | M; "no cartilage loss" **C** | an intact plate joined to the conditions that let it be seen ("no fluid outlines the surface; oblique cuts" are its silences) |
| 18 | Gap | femur–tibia distance per compartment | "nothing on its own" | M; "for only" is evidence | consistent already |
| 19 | Margin | bone-signature volume beyond the reference bone surface | "osteophytes (not OA), where margins are smooth" | M; "no osteophytes" **C** (close to T1) | an osteophyte *is* outgrowth beyond the margin; resolution and the "MONO_DOWN bone" silence condition it. It does not touch OA, an assembly, as ARCH says |

**What Part 1 suggests, in one line each** (for his ruling):
- **A measured fact can stand alone.** Of the nineteen, only Coverage (6) and Extrusion (9) give a rejection that *is*
  their measurement.
- **Most rule-outs are conjunctions.** They need completeness (coverage) and a law, as in the [3,5,7] case, so they
  belong in the encoded truth table as paths, not in the lens.
- **Two rule-outs claim beyond their measurement.** The Deviation lens's "no lesion" and the λ-trajectory's
  "normal" are B unless he defines lesion and normal as the measured deviation.
- **One rule-out is evidence only.** The fat pad's is a surrogate.
- **One label needs its own reading.** Continuity cannot reject the official "injury".

## Part 2. The committee, and independence

His words (00:27:25Z), read with Codex's qualifications (`codex_lens_principle_answer3.md`):
- a committee may output a positive decision, a negative one, an ambiguous one, or a majority with a noted dissent;
- when a particular majority warrants a decision is to be *established*, not assumed;
- independence is no universal precondition, and correlated agreement gains no warrant by default;
- dependence is still measured, as information.

| # | the rule in the design | proposed class | why | proposal, for his ruling |
|---|---|---|---|---|
| 2.1 | ARCH §5.3: "A majority stands only when its dissenter is set aside so". COMMITTEE's 3–1 majority is dropped, and every disagreement stays open (also THESIS §10.2's recall: "Two or more are a disagreement, kept") | **R** | it prohibits an output he names as valid ("All are valid and sane outputs of a committee process") | the committee's outputs include "a majority decision with a noted dissention", and an ambiguous decision. *When* a majority warrants is a path of the encoded truth table, found by building. No blanket rule either way |
| 2.2 | ARCH §4.4: "Agreement counts only between voices whose independence has been measured". The gate makes a pair "two voices" only below a bar (§5.3, §6.2.2) | **R** | "Oh no, not at all". Independence is not a prerequisite | the gate's measurements stay, as information: φ, κ, the κ map, and dissent among correlated lenses above all. They stop being a seat that silences a voice. How correlated agreement weighs is established, not assumed |
| 2.3 | ARCH §4.1's partition: "A body lying in F's excluded part is censored for F, absolutely", from "at least one entitled excluder" | **R** | absolute on one reading, where Part 1 finds most exclusions to be conjunctions (C) | absolute only where the exclusion is T1. A C exclusion is a path of the truth table, and its single reading is evidence against |
| 2.4 | The book: K13a (the gate before the loop, `bar_unset` means nothing concurs) and K14 (INSUFFICIENT; CONCUR only over `independent_measured` pairs) | **R** | the same independence precondition, inherited from ARCH and the accord | as 2.2 |
| 2.5 | ARCH's decision words (PRESENT, ABSENT, DISAGREE, ABSTAIN; §5.2, Table 5.16) | to check against his outputs | his set is positive, negative, ambiguous, and majority with noted dissent. ARCH has no word for a majority carrying a dissent | a majority decision with its dissent recorded beside it, if he agrees |

## Part 3. Noise and entropy (to follow)
