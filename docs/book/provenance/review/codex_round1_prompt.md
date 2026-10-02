READ-ONLY CONSULTATION. Do not run any command, do not read any file, do not write anything. Everything you
need is in this message. You are an independent second reader of a design document, consulted by Claude (the
lead implementer) on behalf of the project's founder, Rohan. Your reading is one voice, never a verdict.

# 1. What you are reading, and why

`docs/KNEE_ARCHITECTURE.md` (pasted in full at the end, after the project's canon documents) is a DRAFT design for
the founder's entry in the Kaggle competition "RSNA Knee Abnormality Detection": per knee-MRI study, 12 binary
findings (ACL, MCL, Medial Meniscus, Lateral Meniscus, Medial OA, Lateral OA, PF OA, Effusion, Synovitis, Baker's,
Contusion, Fracture), scored by macro-averaged ROC-AUC. The founder asked for this document to be read "as a thesis
for how the project should be built", worked through, and agreed on. Claude has read it in full and written its
own reading, which you will be shown in a second round. This first round asks for YOUR independent reading.

# 2. The project's law — read this before forming any view (it is load-bearing, and it is the founder's)

- **The architecture is NOT machine learning.** AI is the genus; ML (gradient-fit models over data) is one narrow,
  avoidable species; classical AI (symbolic, vector-symbolic/HDC, deterministic data geometry) is the architecture
  here; story-understanding (the founder's Regenesis) is yet another thing. The founder: "The architecture IS no ML.
  I bite my thumb at ML. Maybe I'll end up using some small model somewhere for some reason, but NO, the
  architecture is NOT NOT NOT ML." The one sanctioned bounded utility is registration.
- **Know the bias.** Language models are disproportionately drawn to ML and reflexively skeptical of classical AI;
  the words "Kaggle", "vision", "medical imaging", "AUC" fire that prior. Its tells: "the leaderboard will be won by
  a CNN/transformer ensemble"; "this is really ML, just small/downstream"; "a model is needed for the pixels";
  using "no algorithm beats its data" as a covert re-entry point for a model. Do NOT propose a model, a CNN, a
  transformer, an ensemble, a classifier, a fitted weight, or "a small learned component" anywhere. Do NOT reframe
  the design as ML. If you think something cannot work, say what STRUCTURE (law, lens, view, reference, check) is
  missing — "iterate the encoder/structure, never model capacity" (the project's Law 5).
- **The founder's track record** is the existence proof he cites: a leaderboard-ceiling score on one competition
  with 99.8% of decisions made by a deterministic data-geometry stack; money won on another with an LLM touching
  <1% of cells; a leaderboard-beating ARC-AGI result from a deterministic story engine.
- **Structure-first epistemology ("the Sherlock strategy").** A score is information about what a module does,
  never a target to fit. Precision over coverage: modules decide or abstain, never mislabel. A competitor's score
  is a greenfield ceiling, not this design's. Recurse on the hard residual: ask why it is hard; the answer is
  usually the next structure. The structure does the understanding and hands any solver a bounded, typed problem.
- **No Popery** (named by the founder). Committee designs are conciliar: every member is an independent authority
  that measures ONE thing about an object and knows no question; a body is one of the annotator's questions and
  holds the signs; truth is assigned by concurrence and refused on disagreement; the clear majority is assigned
  its role and pulled out, and the conclave reconvenes on the remainder. Popery = one external "correct" pipeline
  tuned toward a predetermined verdict — the ML prior re-entering as the SHAPE of the build even with no model.
  Tells: a harness that fixes one question with a labelled denominator and grades a body by precision; a member
  conceived as a feature that separates positives from negatives; a docstring that states a member's sign; a
  module named for a role; a stopping rule phrased as one role's recall; seating decided by discrimination on one
  query; "the next structure" chosen because a table moved. The regime instead: a harness asks every question of
  every object and reports identified / abstained / wrong per class of object and role. The check: would a domain
  undergraduate, rattling off what the project produces, be doing the task?
- **"There is no noise"** (founder, 2026-10-02): a lens that never resolves a signal is a perfect lens for where
  the signal is NOT; failures with a structural predictor are information, not errors.
- **Scope ruling** (founder): compute budget and deadline are out of scope — "This is about planning, theory, and
  ideation." Do not argue from time or compute.
- **Authority order:** the founder's verbatim statements > the canon (the thesis *What an <Object> Is*, *Law as
  Architecture*, the GenomeVault HDC canon, THEORY_OF_THE_CASE and its Laws 1–8) > this draft. You will see
  THEORY_OF_THE_CASE, AGENTS and FOUNDING_RECORD below; the thesis and LAA themselves are not included (the draft
  quotes them heavily) — where you would need them, say "cannot determine from the text" rather than guess.

# 3. Facts Claude gathered that the draft does not contain (measured 2026-10-02; treat as evidence)

From the competition's own pages (Kaggle):
- Submission columns, from the Evaluation page and matching the local `sample_submission.csv`:
  `StudyInstanceUID,ACL,MCL,Medial Meniscus,Lateral Meniscus,Medial OA,Lateral OA,PF OA,Effusion,Synovitis,Baker's,Contusion,Fracture`.
- Official label definitions: ACL "anterior cruciate ligament injury"; MCL "medial collateral ligament injury";
  Medial/Lateral Meniscus "meniscus tear"; Medial/Lateral OA "osteoarthritis of the medial/lateral tibiofemoral
  compartment"; PF OA "patellofemoral osteoarthritis"; Effusion "joint effusion / excess fluid"; Synovitis
  "inflammation of the joint lining"; Baker's "Baker's cyst"; Contusion "bone contusion / bone bruise"; Fracture
  "fracture". The pages do NOT say how test labels were produced.
- "Only a small subset of training studies carry per-condition labels. We also provide the original text of the
  radiology report from which you may wish to derive the labels for the remaining studies." Test has no report.
- "Every DICOM has been stripped to an allowlisted set of 86 metadata tags." "The prevalence of abnormalities is not
  guaranteed to be the same across the training, public leaderboard, and final evaluation datasets." Freely and
  publicly available external data is allowed.

From the local data:
- DICOM tag survival, 45 sampled series (all sagittal fluid-sensitive fat-suppressed, the one series per study the
  current build fetched): RepetitionTime, EchoTime, EchoTrainLength, FlipAngle, ScanningSequence, SequenceVariant,
  ScanOptions, MagneticFieldStrength, SpacingBetweenSlices present in 39/45; Manufacturer, model, geometry
  (ImagePositionPatient/OrientationPatient, PixelSpacing, SliceThickness), FrameOfReferenceUID in 45/45;
  InversionTime is on the allowlist but empty in the sample; SeriesDescription sometimes "DummySeriesDesc!". Vendors:
  GE, Siemens, Philips, Toshiba; fields 1.5 T and 3 T. Every sampled series with tags is 2-D spin echo (fast/turbo
  spin echo; echo train length 4–70); one axial "fluid-sensitive FS" series elsewhere is a 3-D DESS gradient echo
  (TR 18 ms, TE 7 ms). Sagittal FS series: TR median 3000 ms, TE median 34 ms (range 12–82).
- Series inventory, all 4,407 training studies / 24,371 series (`train_series.csv` flags Anatomical_Plane ×
  Fluid_Sensitive × Fat_Suppression): the flags take only TWO contrast classes — fluid-sensitive+fat-suppressed, and
  non-fluid-sensitive+non-suppressed ("T1-like"); no series is flagged fluid-sensitive non-FS or non-fluid FS.
  Counts: Sag T1-like 5,197; Axial FS 4,719; Sag FS 4,667; Coronal FS 4,624; Coronal T1-like 3,985; Axial T1-like
  1,179. Mean 5.53 series/study (min 3, max 14). 57% of studies (2,516) have exactly {Sag FS, Sag T1-like, Cor FS,
  Cor T1-like, Ax FS}. 100% have all three planes; 100% axial FS; 94% sagittal FS; 96% coronal FS; 100% at least
  one T1-like series. A same-plane pair of two FS fluid-sensitive series exists in 23% of studies (could be a TE
  contrast or a repeat — unverified). Whether "T1-like" ever means PD without fat suppression is not decidable from
  the flags.

# 4. What to produce (be concrete; quote section numbers; label your inferences as inferences)

A. **The mechanism in your own words**, at data-flow level, in ≤15 lines: what the platonic reference is, what
   "subtract" computes numerically, what a lens is, what the λ-trajectory decides, how a finding gets its score.
B. **What is strong** — the moves you would keep as they are, and why (≤8 bullets).
C. **What is wrong, weak, missing, or unverifiable** — ranked by how load-bearing it is, each with: the section,
   the problem, the evidence (from the text or the facts above), and a STRUCTURAL change you would make. Check in
   particular: (i) the feasibility of Layer 1 (the MR signal equation inverted per place, Part 3 §3.3) given the
   measured inventory; (ii) whether the λ-trajectory closed form (Part 4 §4.5) is mathematically right and whether
   reducing it to a function of ‖z‖²/p̂_S loses what the founder meant by it; (iii) the emission rule and its AUC
   facts (Part 6 §6.1); (iv) whether anything in the design re-admits ML or fitting (Part 5 §5.5 memory, §5.8 lens
   families, Part 3 specialists); (v) any No Popery tells; (vi) whether thin structures (menisci, ligaments,
   cartilage) are read at a scale the registration and the 3–4 mm slices support; (vii) internal contradictions.
D. **Short answers to the founder's 16 open rulings** (Part 6 §6.7), one or two lines each, saying where the facts
   in §3 above settle one.
E. **What you are least sure of.**

Do not pad. Do not hedge everything. Disagree with the draft wherever you think it is wrong, and say so plainly.

# 5. The documents

The canon documents follow, then the draft in full. Each is delimited by a line `===== FILE: <path> =====`.


## Appended verbatim after this header (sha256 at the time of the call)

- `docs/THEORY_OF_THE_CASE.md` (as of commit f405450): 59e916c5400d3cba59a2c08b97edc94ebeeb21b0215e0c6de4fd1a950a4d590f
- `AGENTS.md` (as of commit f405450): 0cac8721156ef358591a71f1534160d79dfe9162b6e3ca713bc27ba2a86454fe
- `docs/FOUNDING_RECORD.md` (as of commit f405450): 46fdec436d11d567fe362f0af546ab98636edafe916e39418f347e72a40ef835
- `docs/KNEE_ARCHITECTURE.md` (as of commit f405450): d913777da4425a3d994a85adf9e5cc03c842de033379b9ccd60c51722732ced1
