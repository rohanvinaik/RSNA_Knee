READ-ONLY. Do not run any command or read any file. Answer from this text alone.

# The project (hold this before reading the question)

A **classical-AI, no-machine-learning** computer vision system for RSNA Knee Abnormality
Detection: 12 binary findings per knee MRI study, scored by macro-averaged ROC-AUC. No model, no
fitted weight, no learned embedding. Do not propose one; if your answer contains one it is wrong.
The founder has built working systems this way in harder domains.

Its epistemology is **balanced ternary** and it is rigid:
- an **assignment** (+1) states the thing is known to be present;
- a **rejection** (-1) states it is known to be absent;
- an **abstention** (0) states neither is known. "Silence is an informational zero, never a default
  negative score."
- "Decide or abstain; never mislabel. Unknown is not false."
- "There is no noise": in a lawful domain, confidently resolving something as not-useful is itself
  information. Only genuine entropy is noise.
- **The three-legged stool**: when sources of truth are each correct but incomplete and
  overlapping, the places where they appear to disagree are not noise to wipe away but some of the
  most informative data available.

# The discovery

The competition's gold labels were made this way, per the host:

> "Each study in the annotated reference set was **independently labeled by two
> subspecialty-trained MSK radiologists, with disagreements adjudicated by a third radiologist** to
> produce a single consensus ground truth."

> "In each case, **ambiguous or borderline findings ('on the fence') were graded as negative to
> favor specificity**."

So the annotators ran a committee with concurrence and adjudication — and then **collapsed their
ternary into a binary by folding abstention into rejection.**

The founder's reaction, verbatim: "I do NOT NOT NOT enjoy that they assigned ambiguous findings to
a negative label. That's ML slop and it will FUCK with what I'm trying to do... Disagreement or
uncertainty is NOT a negative. That's how you get shit data."

## The corpus and the other two legs

- **58 studies** carry the 12 expert labels. Those are the only labeled studies on disk.
- Every study is paired with its **original radiology report**, written by **one signing
  radiologist for clinical care**, multilingual.
- The host: where image and report disagree, the **image-derived label is authoritative**, and
  "only a small sample of provided data contains both. **It is intended to help participants
  surface this conclusion.**"
- The host on why they disagree: "clinical reports typically involve one signing radiologist who
  created it for clinical care, and the image-based labels uses multiple readers with **stricter
  image-based thresholds**."

A participant audited 20 of the 58 by report text alone (240 decisions): **82.5% agreement**,
positive predictive 73.1%, positive recall 80.0% (TP 68, FP 25, FN 17, TN 130). Their published
examples of disagreement include:

| report says | label says |
|---|---|
| "There is a **mild** knee effusion." | Effusion = 0 |
| "Leve derrame articular con **mínima** sinovitis" (mild effusion with minimal synovitis) | Effusion = 0, Synovitis = 0 |
| impression: "Synovitis of left knee and massive joint effusion" | Effusion = 1, Synovitis = 0 |
| German report states "Baker-Zyste" | Baker's cyst = 0 |
| Turkish report: "Lateral menisküs normal" | Lateral meniscus tear = 1 |

Several label definitions carry explicit severity floors: OA requires an area "roughly 1 cm or
greater" at ">50% of cartilage thickness"; effusion and Baker's require "moderate or large";
meniscal tear requires surface contact "on at least two images"; ACL requires ">50% of fibers
disrupted" and explicitly grades "mild signal change, degeneration, or thickening without
discontinuity" negative.

# The current design, for context

Chapter 2 builds a **disagreement geography**: register the 58 studies per view into one physical
frame, squint to coarse tiles, and read where the population genuinely differs, with the
complement positively named as the domain's "black". Two artifacts were planned:
- **A, label-free**: the frame, the per-place dispersion, coverage, the entropy/structure split.
  Built from images alone; consults no label.
- **B, label-aware**: a per-place reference built from the studies whose labels do not implicate
  that place, via a finding-to-region map.

# The questions

Answer inside this epistemology. Be concrete. At most 900 words.

1. **Characterize the corruption exactly.** It is one-directional. State precisely what is and is
   not damaged: what does a 1 warrant, what does a 0 warrant, and what is the resulting asymmetry
   between the two classes? Be rigorous about what can still be asserted.

2. **Which parts of the design does it actually reach?** Artifact A consults no labels. Does the
   corruption touch it at all? Where exactly does it bite — artifact B, the acceptance bars, the
   scoring, something else?

3. **Can the third leg re-expand the collapsed state?** The reports are the other written leg. If a
   0 means "confidently absent OR on the fence", can the report text separate those two
   sub-populations? What specifically in the report would be the fingerprint of a folded
   abstention, and what would distinguish it from a genuine confident absence? Note the severity
   words in the examples above.

4. **The scoring consequence.** The metric is macro-averaged ROC-AUC against these labels. If a
   fraction of the negatives are actually borderline positives, what does that do to a system that
   correctly detects them? Quantify the direction and shape of the effect. What does it mean for
   reading our own acceptance numbers on the 58?

5. **What must the design NOT do.** Name the specific mistakes available here — ways a build could
   silently inherit or amplify the collapse, or could "fix" it in a way that is really fitting to
   labels.

6. **The founder intends to re-grade the ambiguous cases by hand.** What should the system hand him
   to make that tractable — what exactly should be surfaced, ranked how, and in what form, so that
   his manual pass is as short as possible and his rulings are durable?
