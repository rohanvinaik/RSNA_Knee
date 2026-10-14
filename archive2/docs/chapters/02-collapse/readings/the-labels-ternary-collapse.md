# The gold labels' ternary collapse, and what it reaches

2026-10-10. The founder, on learning that borderline findings were graded negative: "I do NOT NOT
NOT enjoy that they assigned ambiguous findings to a negative label. That's ML slop and it will
FUCK with what I'm trying to do... Disagreement or uncertainty is NOT a negative. That's how you
get shit data." He intends to re-grade the ambiguous cases himself.

## What happened, in the project's own terms

The annotators ran a committee: two subspecialty MSK radiologists reading independently, a third
adjudicating disagreement. That is this project's own structure. Then they **collapsed the ternary
into a binary by folding abstention into rejection**:

    published Y = 1  <=>  adjudicated T = +1
    published Y = 0  <=>  adjudicated T in {-1, 0}

The assignment survives intact. The distinction between rejection and abstention does not.

## The negative class holds THREE states, not two

**This corrects the lead's first reading, which had it as two.** Codex supplied the distinction and
it is load-bearing:

| state inside Y = 0 | what it is | is it a defect? |
|---|---|---|
| confident absence | nothing is there | no — a true rejection |
| **confident subthreshold presence** | something is there, below the definition's floor | **no — a correct rejection under the stated rubric** |
| genuine abstention | the readers were on the fence | **yes — this is the corruption** |

The second row matters because the competition's definitions carry **explicit severity floors**:
effusion and Baker's require "moderate or large"; OA requires "roughly 1 cm or greater" at ">50% of
cartilage thickness"; ACL requires ">50% of fibers disrupted" and grades "mild signal change,
degeneration, or thickening without discontinuity" negative.

So a radiologist who sees a mild effusion and grades Effusion = 0 **is not abstaining**. They are
rejecting, correctly, against a definition that asks for moderate-or-large. Codex, verbatim: "'Mild
effusion' is not necessarily an abstention about 'moderate or large effusion.'"

**Only the third row is the epistemological defect the founder objects to.** The first two are the
rubric working as designed. Conflating all three would be the lead making the mirror-image of the
host's error.

Fable reached the same three-way split independently, and added the structure that matters most:

> "**The mix differs per finding**: findings with written floors (OA, effusion, Baker's, ACL,
> meniscus) carry a large 0_subfloor; **fracture, contusion, MCL fold mostly 0_fence**."

So **the defect is concentrated**. Where the definition states a severity floor, most negatives are
legitimate sub-floor rejections. Where it does not — Acute fracture ("an acute cortical break or
fracture line") and Contusion ("bone marrow edema-like signal from impact, without a discrete
fracture line") carry no severity floor at all — the negatives are dominated by genuine folded
abstentions. **Those are the findings to re-grade first.**

### The category name must carry its floor

> "The category names: '**Effusion**' outruns its warrant; the category is
> **EFFUSION_MODERATE_PLUS**."

This is the oracle's point 5 ("a category's name never outruns its warrant") applied to the
competition's own labels. What the data calls Effusion is *effusion at moderate-or-greater
severity*. Every category with a floor must be named with it, or the build inherits a name that
claims more than the column holds.

## What a 1 and a 0 each warrant

- **A 1 warrants an adjudicated assignment under the competition's definition.** The folding does
  not damage it. The positive class is high purity, and deliberately so: the bar was set high and
  borderline cases were pushed away from it.
- **A 0 warrants only that a qualifying finding was not assigned.** It does not warrant absence. It
  cannot be read as a rejection without further evidence.

The corruption is **one-directional**: positives are clean, negatives are mixed.

## Measured: the size of the affected class

| quantity | value |
|---|---|
| label cells over the 58 studies | 696 |
| **negative cells — the class holding the folded abstentions** | **456 (65.5%)** |
| studies with a report (the third leg) | **58 of 58** |
| report length, characters | min 183, median 1212, max 3891 |
| writing systems | 28 Latin, 27 Latin with diacritics, 3 Latin + Cyrillic |

The third leg is fully available and substantial. Nothing is a stub.

**What is not estimated:** the participant audit's 25 report-positive-against-label-negative cells
out of 155 label-negatives is **not** an estimate of the folded-abstention fraction. Codex: "its
discrepancies mix threshold differences, omissions and actual disagreements." Scaling it to 456
cells gives an upper bound on all three mixed, not a count of the defect.

## Where the corruption reaches, and where it does not

| part of the design | reached? |
|---|---|
| **Artifact A, the disagreement geography** | **No.** It is built from images and geometry alone and consults no label. Dispersion, coverage and the entropy/structure split do not change because a label was collapsed. *The caveat: it becomes contaminated the moment a label is used to choose any of its parameters.* |
| **Artifact B, the label-aware normal reference** | **Directly, and worst.** Treating every 0 as permission to contribute "normal" tissue admits uncertain and subthreshold-affected tissue into a reference whose whole purpose is to be normal. And even a confident rejection does not certify every mapped location as unaffected. |
| acceptance readings on the 58 | yes — any count of "wrong" against a contaminated negative class misreports |
| a check that scores abstention-against-zero as a correct rejection | yes — that is the host's error, re-inherited |
| any finding-to-region eligibility rule derived from these labels | yes |

**This is a strong argument for building A first and fully.** It is the part of Chapter 2 the
corruption cannot touch, and it is the chapter's core product.

## The scoring consequence — and it is better than feared

Partition the published negatives into confident negatives and borderline, the latter a fraction
alpha. Then the benchmark splits pairwise:

    AUC = (1 - alpha) * AUC(positives, confident negatives)
        +      alpha  * AUC(positives, borderline)

Codex's result, which substantially defuses the concern:

> "Raising scores for correctly detected borderline findings hurts benchmark AUC **when those
> scores cross published-positive scores**. If they remain below every positive, there is no AUC
> penalty. **Ordering borderline cases above other negatives does not itself affect AUC.**"

So **correctly detecting the borderline cases is free**, provided they rank *below* the true
positives. The metric does not force us to reproduce the collapse. It punishes only one thing:
ranking a borderline case above a confident positive. If a promotion reverses a fraction r of
positive-borderline pairs, the loss is alpha * r, divided by twelve in the macro average.

The design consequence is a **required ordering**, not a required blindness:

    confident positive  >  borderline present  >  confident absent

Fable quantifies both sides of it. Let phi be the folded fraction of a finding's negatives:

> "A **severity-blind** detector scoring folded cases like positives has **AUC_max = 1 - phi/2**:
> effusion with ~10 mild among 23 negatives, phi ~ 0.43, **ceiling ~ 0.78**."

> "A **ternary-ordered** output, assignment > abstention > rejection, **with assignment ordered by
> distance above the floor** (extent_mm, fibre fraction, cartilage depth), **pays nothing**: clear
> positives outrank folded, folded outrank absent, AUC -> 1."

**That is the mechanism, and it is concrete.** Ordering assignments by *how far above the stated
floor* they sit — millimetres of extent, fraction of fibres disrupted, depth of cartilage loss —
puts clear positives above borderline ones automatically, which is exactly what the metric needs.
The floor is a measurement named in the category, never a level tuned until the labels agree.

> "The fold punishes only a system that **cannot order clear from borderline**; abstention sits in
> the middle, never at the bottom."

Two cautions for reading our own numbers: phi differs per finding, so the macro-average mixes
different ceilings; and at 9 positives (MCL) **an AUC's standard error is about 0.1**, so a
per-finding reading on the 58 is very loose. Report each finding three ways — the binary as given,
with folded candidates removed, and against the founder's re-grade — plus identified / abstained /
wrong per cell. **A miss against a folded 0 is never "wrong"; it is an unresolved row.**

## Can the report re-expand the collapsed state?

Partly, and the lead's first hypothesis was wrong about how.

**The lead proposed** that severity words ("mild", "minimal", "leve", "mínima") are the fingerprint
of a folded abstention. **They are not.** They are the fingerprint of *confident subthreshold
presence* — the second row above, which is a correct rejection under the rubric. Codex separated
them, and the separation is the useful part:

| report shows, against a 0 label | what it marks |
|---|---|
| "possible", "equivocal", "cannot exclude", "suspicious for" | **candidate folded abstention** — the actual defect |
| definite "mild", "minimal", "trace"; degeneration without discontinuity | **subthreshold presence** — a correct rejection, not a defect |
| explicit finding-specific denial ("no meniscal tear", "lateral meniscus normal") | report rejection |
| silence on the finding | report abstention — *omission is not denial* |
| definite "moderate", "large", or qualifying measurement | **sharp conflict** with the 0 |

The limit, stated honestly: the reports re-expand **the evidence ledger** into assertion,
rejection, uncertainty, omission and severity. They **cannot uniquely recover the annotators'
erased state**. The Turkish example proves it — "Lateral menisküs normal" against a label of 1
shows the report leg cannot reconstruct the image committee's conclusion either.

That is the three-legged stool behaving exactly as the founder described: each leg correct in its
own frame, none complete, and the disagreements carrying the most information.

### Two corrections that change the fingerprint ranking

A second, independent Fable reading (spawned by the lead in error, then answered before the
stand-down landed) produced two corrections neither prior consultant made. Both hold.

**Correction 1 — the severity-word mapping is per-finding, and must abstain where the axes do not
match.**

> "severity -> subthreshold holds **only where the floor is a grade on the report's scale**:
> effusion, Baker's, synovitis, ACL ('mild signal change' explicitly negative). For **OA** (>= 1 cm,
> >50% depth) and **meniscus** (surface contact on two images), **'mild' lies on another axis**:
> mild degeneration is a different category, not a mild tear. The lexicon abstains there."

OA's floor is a size and depth criterion; the meniscus floor is morphological (does the signal
reach the surface, on two images). A report saying "mild meniscal degeneration" is **not** reporting
a mild tear — it is reporting a different finding, one the definition explicitly excludes. Mapping
a grade word onto a non-grade floor is a category error. **The lexicon is per finding, and
abstains where the report's axis and the definition's axis differ.**

**Correction 2 — the hedge belongs to the reader, the fold belongs to the committee. This inverts
the ranking.**

> "hedging is the **reader's** abstention; the fold was the **committee's**. One reader can
> confidently report what the stricter committee could not decide. So the stronger fingerprint of a
> folded abstention is **a confident grade at or straddling the floor** ('moderate',
> 'small-to-moderate', 'massive synovitis' -> 0), or presence asserted without a grade where the
> floor is a grade."

The lead had hedges as the primary fingerprint. They are not. A hedge tells us the *signing
radiologist* was unsure; it says little about what the *committee* did. A **confident** at-floor
grade against a 0 is stronger evidence of a folded abstention, because someone confident saw it and
the committee still did not assign. Both Fable readings reached this independently — the first
called floor-straddling "the highest-value tier".

**The corrected ranking of fold evidence, strongest first:**

1. a confident grade **at or straddling the floor**, against a 0
2. presence asserted **without a grade**, where the floor is a grade
3. a **hedge** against a 0 — the reader's own abstention

### The five codes the conjunction yields

Re-expanding a 0 by conjunction with the report leg gives named codes, not a binary:

| code | state | what it is |
|---|---|---|
| `ABSENT_CONCURRED` | reject | explicit negation and a 0; two legs agree |
| `SUBTHRESHOLD_CONCURRED` | reject *under the rubric* | present, graded below the floor, and a 0 |
| `FOLD_SUSPECT` | **abstain — queue it** | the fold's fingerprints above |
| `REPORT_SILENT` | abstain | the structure is never named; silence is not denial |
| `UNPARSED` | silence | the lexicon could not read it; **never read a parse failure as absent** |

### The sub-floor class is a resource, not contamination

The sharpest point in the second reading, and it reverses the framing:

> "**SUBTHRESHOLD_CONCURRED is the prize**, since it shows **where the floor sits in image terms**,
> measured on **two-lens-concordant populations** rather than fitted."

These are cases where both written legs agree a finding is present *and* below the floor. They are
therefore a set of **known-mild exemplars, free of charge**, which locate the definition's floor in
image measurements — millimetres of extent, fraction of fibres, depth of cartilage loss — **by
measurement on a concordant population, never by tuning against a score**. That is exactly what
Law 4 permits and what the ordering in the scoring section needs.

### A second fence fingerprint, and the unresolved class

Fable adds a marker class neither the lead nor Codex had: a **floor-straddling grade** against a 0
— "mild-to-moderate", "small-to-moderate", "moderate / mässig / orta / moderado", "high-grade
partial", "near-complete", "grade 2-3 signal", "extending to the surface", "condropatía grado III".
There the single reader sat *at or over* the floor while the committee put it under. That is the
second fingerprint of a folded abstention.

And for an **unqualified positive** against a 0 ("Baker-Zyste" with no size), the text cannot
resolve it — but artifact A can: "the pocket extent at the region measures the severity the report
omitted: small -> subfloor, at the floor -> fence, large -> true disagreement." The image leg
settles what the text leaves open.

### The multilingual side-word traps — high stakes, easily missed

These would swap **the same four findings the laterality mirror governs**:

| language | the trap |
|---|---|
| Spanish | **"menisco interno / externo"** means medial / lateral, not internal / external. **"ligamento lateral interno" is the MCL** — despite containing the word "lateral" |
| German | **Innenmeniskus / Außenmeniskus** = medial / lateral; **Innenband** = MCL |
| Turkish | **iç / dış** = medial / lateral |

> "a side word read literally swaps the same four findings the mirror did."

Two further mappings, stated as domain facts: **chondromalacia grades map onto the OA floor
directly (III-IV = >50% thickness)**, and **bone marrow edema = contusion**. Negation scope is the
sentence, and the token must govern the finding noun; an itemized template line ("Menisken:
unauffällig") is a negation, not silence.

## What the design must not do

- Convert a 0 into known absence, or into unrestricted eligibility for the normal reference.
- Convert report omission into rejection.
- Convert every mild finding into a qualifying positive — that is the mirror of the host's error.
- Silently overwrite image labels with report assertions.
- Declare low dispersion or absent coverage to be known irrelevance.
- Move a squint scale, a noise level, a severity bar or a score mapping to improve agreement with
  the labels. That is fitting, and Law 4 forbids it.
- Average disagreeing states together, which hides them.
- Re-use the founder's hand-regraded cases as independent evidence after using them to change the
  system. That is leakage.

Original gold, report readings, image readings and manual rulings stay **separately traceable**.
Original gold stays immutable.

## What to hand the founder for his manual pass

A study-by-finding adjudication queue, ranked so the shortest pass does the most work. Each item
carries:

- the original gold cell and the competition's exact definition for that finding;
- the report passage, with assertion / denial / hedge / severity tagged, and a faithful translation;
- the image evidence at native resolution with its coordinates and physical measurements, in the
  sequence that shows it — for a meniscal tear, the two images the definition requires; for OA, the
  extent in millimetres and the thickness fraction; for effusion and Baker's, the severity evidence
  rather than the noun alone;
- whether the case is currently contributing to the normal reference, and what admitting it would
  do;
- missing evidence marked explicitly as missing.

Ranked: direct qualifying contradiction first, then explicit uncertainty or near-floor evidence,
then an unqualified report assertion against a 0, then missing-evidence cases. Definite
subthreshold cases are shown as their own group, since they are not defects. Positive-label
against report-denial conflicts are listed separately.

**His ruling is recorded as a ternary state** — assignment, rejection or abstention relative to the
stated definition — with a separate subthreshold-presence tag, never as a flipped bit. With
rationale, evidence coordinates, date and which version of the definition it was made against. The
re-graded corpus is ternary; it does not repeat the collapse.

### The one move that makes his pass short

Fable's sizing, and the structural point inside it:

> "**The sub-floor set is one grouped policy item with counts per finding, not rows.**"

He does not rule 30 times on whether a mild effusion counts. He rules **once**, as policy, and it
applies to the whole sub-floor class. Only the fence and conflict cases need per-case judgement.

> "Size, from the audit: ~10% of 696 pairs -> ~70 folded candidates plus ~50 FN-type; the policy
> ruling removes about half; **~60 per-case rows**."

Tiers, ranked so the shortest pass does the most:

1. above-floor positive against a 0; a label 1 against an explicit negation; laterality mismatches
2. floor-straddling grades
3. hedged
4. unqualified positives, with the image's measured extent beside them

Within a tier, **nearest the floor first**, by the image measurement, and **grouped by finding** so
he stays in one diagnostic mode rather than switching anatomy every row. Each row carries the
label, the verbatim sentence with its language and a gloss, the marker class, the pocket's
extent / sign / peak / recurrence (or "no pocket", with n_p), and a contact sheet: the squinted map
with the pocket outlined, the native slice at its centroid, and the population median beside it.

Seed the queue with a few **controls** — label 0 with an explicit negation and no pocket — so the
pass itself can be checked.

`gold_v2` is kept apart from the original, append-only, each ruling carrying the evidence digest
and the lexicon version it was made against.

### Fable's additions to "must not"

- Choose a level or extent floor so that mild cases fall below it **"because the labels say 0"**.
  The floor is a measurement named in the category, never a level tuned until the labels agree.
- Edit the marker lexicon until the re-expanded labels agree with the system. The lexicon is
  **authored per language and frozen before any image result**.
- Let the report override the committee **for scoring**: the hidden test labels follow the
  committee's rule. The report re-expands the state **for the build and for the founder**, not for
  the competition's definition.
- Discard the report leg over the 17 cases where it missed a true positive.
- Name a category without its floor.
- **Build the lexicon as a feature that separates 1 from 0.** That is Popery. The lexicon is a
  lens: it measures what the signing reader asserted and how surely, and **knows no question**. It
  is asked of every report, not of the positives.
- **Read a parse failure as absent.** `UNPARSED` is silence, never rejection.
- **Cite the 82.5% as the report leg's reliability.** It mixes three different kinds of
  disagreement — threshold, omission and genuine conflict — and the audit parsed *presence* without
  parsing *grade*, so its "false positives" include concordant sub-floor cases that are not errors
  at all.
- **Emit an abstention as 0.0.** That reproduces the host's fold in our own output. The three
  states' *order* must survive emission; the values themselves are the founder's.

### The queue is smaller than first estimated

Three sizings were given. The difference is whether the floor check runs before the queue is built:

| source | estimate | condition |
|---|---|---|
| Fable, first reading | ~60 per-case rows | after one policy ruling clears the sub-floor set |
| Fable, second reading | **20-40 pairs** | after the **per-finding floor check** removes concordant-mild |
| Codex | not sized | — |

The second is smaller because the floor check is per finding and abstains where the axes do not
match, so fewer rows survive into the queue. Run the floor check first.

His ruling per pair is one of four codes — `PRESENT_AT_FLOOR`, `PRESENT_SUBTHRESHOLD`, `ABSENT`,
`CANNOT_TELL` — with the view and slice he judged from. **`CANNOT_TELL` stays 0**: the queue does
not force a decision it cannot warrant. The table is versioned and sits **beside** the competition's
labels, never overwriting them. The harness reads it as a second truth column **for acceptance
only**; the competition's labels remain the scoring column, because the hidden test applies the
committee's rule.

`SUBTHRESHOLD_CONCURRED` goes to him as a **batch for wholesale confirmation**, not as rows.
