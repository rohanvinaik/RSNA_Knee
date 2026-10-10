# Knee as Law — A Classical-AI Architecture for RSNA Knee Abnormality Detection

> **The rigid oracle supersedes this document** (added 2026-10-03, at the founder's word). He wrote: "Note this
> principle will even supercede the atchitecture document as well. The concept is the rigid oracle, the design is
> something we're working on building in session" (2026-10-02 23:59:57Z). The principle, in twelve points with his
> words, heads `AGENTS.md`, `docs/book/CONSTRAINT_BLOCK.md` and `docs/THEORY_OF_THE_CASE.md`. Where this
> document conflicts with it, the principle wins.

**Status.** DRAFT for founder sign-off, 2026-10-02. Not a build specification until signed. This document
supersedes and expands `docs/KNEE_RECIPE.md` (RECIPE), the first working of the recipe for the knee, which
is kept as that first working. It fills the intelligence layer that `docs/THEORY_OF_THE_CASE.md` (THEORY)
Part III left as a sketch, on the data layer of THEORY Part II. Its grounding is the session brief of
2026-10-02 (BRIEF), whose design, layers 0–9, it specifies layer by layer. It was drafted as six Parts from
the same sources, each source read first-hand, and edited here for one voice. Where two Parts treated the
same matter, the fuller treatment stands and the other points to it; every citation and every verbatim
quotation is kept exact.

**Supremacy.** This document is derived. Where it is silent, ambiguous or wrong, the following govern, in
this order:
1. the founder's statements, verbatim: FOUNDING, and the rulings recorded in BRIEF §3;
2. the canon: the documents in `docs/canon/`, THEORY (whose Laws 1–8 bind here), AGENTS and the decision
   records in `decisions/`. Within the canon, BRIEF yields to the others where they conflict (BRIEF,
   preamble);
3. this document.

**Standing law** (THEORY Part IV; AGENTS; FOUNDING; NOML). The architecture is not ML. No CNN, transformer
or fitted model is proposed, and the design is never framed as "small ML". Registration is the one
sanctioned bounded utility (Law 3). The data layer narrows and never decides a finding (Law 4). Nothing is
submitted without the founder's explicit go (Law 8).

**Conventions.**
- *Status words.* **BUILT**: in the repository, with its code path. **DESIGNED**: specified here, not yet
  built. **OPEN**: a founder decision, or a measurement not yet made. **Departure** marks a place where the
  knee leaves a source, and says why.
- *Citations* give a source's short name (the table below) and the source's own section: THESIS §4.2,
  LADDER v5, ZONES Rank 2. A bare § belongs to a source when it follows that source's name in the same
  citation, as in (THESIS §7.1, §7.4), or stands in a table row or column headed by the source, as in the
  Sources table and the THESIS columns of Tables 1.6 and 4.5. Code is cited by path, with the function or
  line where it matters.
- *Cross-references* inside this document read Part N §N.M, or Part N Table N.M. A bare §N.M that follows
  no source's name is a section of this document.
- *Founder quotations* are verbatim and carry their date: (founder, 2026-10-02). Each ruling is quoted in
  full where its mechanism is built or its case is made, and elsewhere in exact fragments with a pointer.
- *Numbered families.* Layers 0–9 are the design's layers, numbered as in BRIEF §5. L1–L5 are the domain
  laws (Part 2). Laws 1–8 are the project laws (THEORY Part IV). H1–H4 are the thesis's hypotheses (THESIS
  §1.4). Q1–Q7 are the open questions carried from RECIPE §11, gathered with the rest in Part 6 §6.7. R1–R5
  and QZ1–QZ4 are the perturbation families (Part 4 Table 4.3); in Part 3's equations R2 is instead the
  relaxation rate 1/T2. Lenses are numbered 1–19 (Part 2 Table 2.8a). The founder's rulings are numbered 1–9
  as in BRIEF §3.
- *Fixed names.* The λ-trajectory's four words are MONO_UP, PEAK_DROP, MONO_DOWN and AMBIGUOUS (SYNTH's
  MONOTONIC_INCREASE, PEAK_THEN_DROP, MONOTONIC_DECREASE and AMBIGUOUS). The five agencies are fluid,
  marrow, fibrous structures, compartments and every finding. The two references are the population
  reference (the pathology axis) and the constraint reference (the input-error axis).

**Sources.** The canon and the project records, with the short names used in citations and their sha256 at
the time of writing.

| Short name | Path | What it is | sha256 |
|---|---|---|---|
| THESIS | `docs/canon/what_an_object_is.md` | *What an \<Object> Is* (Vinaik and Claude, 2026-10-01): classical-AI computer vision, worked on 4-D fluorescence microscopy of cells. H1–H4 (§1.4); laws (§2); collapse and squint (§3); the loop (§4); the one language (§6); K-lines and censors (§7); teaching (§8); the society (§10); the recipe (§13.1) and the falsifiers (§13.3) | `93c7438d9532dd3ea88f77250b3c148c4a35f371d3103025774a95b86d95ad7d` |
| LAA | `docs/canon/law_as_architecture.md` | *Law as Architecture*: the law's structure becomes the network's topology. Composed specialists (§5), Kanerva memory (§6), near-miss censors (§7), regime stratification (§8), coherent-replicate imputation (§9), delta-method uncertainty (§10), generalization (§11), falsifiers (§12) | `c6b441edffa984537665bb8f5a14df25e6df7c0ddf202b866a006b67592aecbc` |
| HDCSUB | `docs/canon/HDC_SUBSTRATE.md` | The GenomeVault HDC mechanisms, transferred to cell tracking: Parts A–F; the header ruling (F.0), the 20-bit header (F.1), the E10 trajectory byte (F.2), the precision ladder (F.3), corrections (F.4) | `0fd0df63eeed1a7d546ef86b0a14bb507f764193edacf05fe28a7e8897ea15b4` |
| LENS | `docs/canon/MULTI_MODAL_LENS_STRATEGY.md` | Lens discovery by grid search, local minima and Ward clustering (Phases 1–3); edge-case validation (Phase 4); λ-trajectory profiling (Phase 5) | `b803b3cede646277397ec77e6dcd8747881387a82959e8f6de387ae103d27624` |
| SYNTH | `docs/canon/ACCURACY_OPTIMIZATION_SYNTHESIS.md` | GenomeVault's accuracy synthesis: correction layers 0–5, the three-way distinction (Part II), trajectory patterns and complementary sparsity (Part III), the E10 header (Parts VII–VIII) | `6af156e1c522eae1fdce763d78a34a572bf4c15cfaf67ecc40b21fed94f7faad` |
| COMMITTEE | `docs/canon/CLINICAL_COMMITTEE_ERROR_CORRECTION_ARCHITECTURE.md` | Four independent encoders; unanimous, majority, tie and all-zero-margin outcomes; dissenter analysis; the 36,210× joint-error clustering (§4.2) | `3f4c9b0bb6ee016768457c0eab131a9bdd9775cd21ac9e3c6603f85dd63ac00e` |
| TIERED | `docs/canon/TIERED_UNCERTAINTY_AWARE_ARCHITECTURE.md` | Tier 0, Tier 1 and Tier 2; the writes-per-dimension law (§0, §2.2); margin-0 errors predictable, margin-2 errors not (§3.1.1) | `a08f6f68a3ca6a6be91206aa4dba62c5c439a48cf03f86127139ff1af9ad203c` |
| BRIEF | `docs/canon/SESSION_BRIEF_2026-10-02.md` | The grounding of this document: the founder's rulings (§3), the verified findings (§4), the design's layers 0–9 (§5), the laws condensed (§6), the open questions (§7) | `6215967be99e02ec2b72363bbff360476ea0811afba00d5f697b45ffb31d03b6` |
| THEORY | `docs/THEORY_OF_THE_CASE.md` | The RSNA Knee theory of the case: the data layer (Part II), the intelligence-layer sketch (Part III), Laws 1–8 (Part IV), the pathology record (Part V) | `59e916c5400d3cba59a2c08b97edc94ebeeb21b0215e0c6de4fd1a950a4d590f` |
| AGENTS | `AGENTS.md` | Onboarding and the anti-solipsism protocol | `0cac8721156ef358591a71f1534160d79dfe9162b6e3ca713bc27ba2a86454fe` |
| FOUNDING | `docs/FOUNDING_RECORD.md` | The founder's verbatim canon, 2026-08-18 | `46fdec436d11d567fe362f0af546ab98636edafe916e39418f347e72a40ef835` |
| NOML | `decisions/2026-08-18-classical-ai-no-ml-data-layer.md` | The founding decision: a classical-AI entry with no ML; the data layer as a GDiff port | `edbe0dd7713b70feab2c270f72124a6145872594f6a894d77372aae96f37efbc` |
| VERDICT | `decisions/2026-08-28-make-or-break-verdict-is-auc-based.md` | The make-or-break instrument: peak local survivor density, rank AUC | `b9cb6a1da107a7f9647894c5a33992adde206a3fdbc5f6a2a3d62671732fffec` |
| LADDER | `decisions/2026-08-29-encoder-iteration-ladder.md` | The encoder iteration ladder; the v5 substrate reset (all v1–v4 numbers dead); the first v5 readings | `338fc583591eba9c8a6f92a873c9852538a6b52169d911382fe5dba2e26b78a6` |
| ZONES | `decisions/2026-08-30-anatomical-zone-architecture.md` | Template-space zone label volumes; NCC refinement and a QC gate (Rank 2); multi-atlas fusion (Rank 4); an unbiased template (Rank 5) | `74aaed8db09fe02a1047957cbed77a9d4c3e2bed0aa0bb1f4b23637072b339b5` |
| — | `decisions/README.md` | The decision log's format and use | `bae86a0062a53a24ed9b1f822fa0bbff518d7d9e5f5ec2ed533b74c9ac80c73c` |
| RECIPE | `docs/KNEE_RECIPE.md` | The first draft of the recipe worked for the knee: laws L1–L5, lenses, agencies, law checks, output contract, questions Q1–Q7. Superseded by this document | `a017ab5ec2b86309bfa3e2f6be9e2a8fb58381fcb15ab43f202feba57d319c65` with its supersession note; `4caaa3feeeb79c1a64b5b198fb1e86d7707bba4596e34c2c63d6bf50eb5fa1ba` before the note was added |
| PRIORART | `docs/LANDMARK_PRIOR_ART.md` | The landmark and atlas research fleet | `3f3fbe413bf3816b7c5cf0d6fc1e80e9868236f1c8a40aa5cd99a445b678dd9a` |

GenomeVault's public tree is read for its ideas only, since the founder is "rebuilding it completely from
scratch." (founder, 2026-10-02; the ruling is quoted in full in Part 1 §1.2). The files read first-hand,
under `/home/user/rohanvinaik/genomevault/genomevault/hdv_validation/hdc_experimentation/`, are these.

| File | Read for | sha256 |
|---|---|---|
| `query/biophysical_query_engine.py` | the F.1 header: percentile calibrator, 20-bit signature, bitwise vote (Part 3 §3.2.2) | `45998b65ad1c823a3712bc8540b6ea3a2c6dabde2bced1ab71c6541417188f7a` |
| `decoders/lens_aware_decoder_CORRECTED_3TERNARY.py` | the additive lens overlay, and the degenerate confidence at line 371 (Part 4 §4.5) | `9d0616a741a7b980d9831b3604a70bff3a962863f5919c26bf2affb64856ce06` |
| `query/lens_aware_simd_query_engine.py` | a second confidence, and a ternary search for λ (Part 4 §4.5) | `ddfe39ae221ad7f7110ca6175d59eef311e11aa1bf7534610c20b7ff72b55d31` |
| `docs/reports/SPARSE_POSITION_CODEBOOK_FIX_REPORT.md` | listed in BRIEF §1; not cited here | `a7377912ffe6738621d5dccf4dd53ab81bea1002764540230e3fea94e0efddb2` |

The built code is cited by path under `src/RSNA_Knee/` and `tools/`, and listed with its fate in Part 6
Table 6.5. The radiology and statistics literature outside the canon is listed at the ends of Parts 2, 4
and 5.

## Abstract

This document specifies the knee-as-law architecture for RSNA Knee Abnormality Detection: twelve binary
findings per knee MRI study, scored by macro-averaged ROC-AUC. It instantiates for the knee the
classical-AI thesis of *What an \<Object> Is*, joined with *Law as Architecture* and the GenomeVault HDC
mechanisms. It contains no machine learning. Registration is the one bounded utility, the data layer
narrows and never decides, and nothing is fitted across studies.

Part 1 states the case. The knee meets the thesis's precondition and is the easier domain. Its objects are
structures, always present, and lesion-objects, found in the residual. Under the stance that there is no
noise, it is read against two references that are never merged: the population, for pathology, and the
constraints, for input error. Part 2 states five domain laws and nineteen lenses, one per law term, each
with what it rules out and where it is blind. Part 3 builds the substrate: headers as metadata, the MR
signal equation as the network, KneeDiff over tissue parameters, and an exact ledger with the codebook as
quantizer. Part 4 builds the reading: exclusion and a hardness map drawn from true normals, perturbation as
the knee's anchors, a loop that takes each lesion-object out with its halo, and a closed-form λ-trajectory.
Part 5 builds the society: five agencies, the series as committee, tiers, individual cases recalled within
trust radii, censors, and teaching in which reports teach and gold establishes. Part 6 emits ranks in three
registers, sets the measurements and nine falsifiers, lays out a ten-phase build from the existing code,
and gathers the founder's open rulings.

## Table of Contents

- [Abstract](#abstract)
- [Part 1 — The case: the thesis instantiated for the knee](#part-1--the-case-the-thesis-instantiated-for-the-knee)
  - [1.1 The problem, as the competition poses it](#11-the-problem-as-the-competition-poses-it)
  - [1.2 Lineage: one thesis, three running instances](#12-lineage-one-thesis-three-running-instances)
  - [1.3 Why the knee is the easier domain](#13-why-the-knee-is-the-easier-domain)
  - [1.4 The precondition, checked clause by clause](#14-the-precondition-checked-clause-by-clause)
  - [1.5 The knee's \<object>: structures and lesion-objects](#15-the-knees-object-structures-and-lesion-objects)
  - [1.6 Cells and knees, side by side](#16-cells-and-knees-side-by-side)
  - [1.7 There is no noise: information and entropy](#17-there-is-no-noise-information-and-entropy)
  - [1.8 Two references, never merged](#18-two-references-never-merged)
  - [1.9 The laws that govern this document, and what it replaces](#19-the-laws-that-govern-this-document-and-what-it-replaces)
  - [1.10 The whole design on one page](#110-the-whole-design-on-one-page)
  - [1.11 A reading guide to Parts 2–6](#111-a-reading-guide-to-parts-26)
- [Part 2 — The laws and the lenses (recipe steps 1–3)](#part-2--the-laws-and-the-lenses-recipe-steps-13)
  - [2.1 What a law is, and what each law must yield](#21-what-a-law-is-and-what-each-law-must-yield)
  - [2.2 L1 — Anatomy: one knee, one of each, one structure per place](#22-l1--anatomy-one-knee-one-of-each-one-structure-per-place)
  - [2.3 L2 — The MR signal: the instrument's physics](#23-l2--the-mr-signal-the-instruments-physics)
  - [2.4 L3 — Acquisition: the plane, the slice, and partial volume](#24-l3--acquisition-the-plane-the-slice-and-partial-volume)
  - [2.5 L4 — Pathology: radiology's own laws](#25-l4--pathology-radiologys-own-laws)
  - [2.6 L5 — Mechanism: how events co-occur](#26-l5--mechanism-how-events-co-occur)
  - [2.7 The knee's collapse: plane per structure, and the squint](#27-the-knees-collapse-plane-per-structure-and-the-squint)
  - [2.8 The lenses, one per law term (recipe step 2)](#28-the-lenses-one-per-law-term-recipe-step-2)
  - [2.9 Priors and regime keys (recipe step 3)](#29-priors-and-regime-keys-recipe-step-3)
  - [2.10 Zones the laws need from the atlas](#210-zones-the-laws-need-from-the-atlas)
  - [2.11 What this Part leaves open](#211-what-this-part-leaves-open)
- [Part 3 — The substrate: headers, the signal-equation law, KneeDiff in physics space, and the one language (layers 0, 1, 2 and 4)](#part-3--the-substrate-headers-the-signal-equation-law-kneediff-in-physics-space-and-the-one-language-layers-0-1-2-and-4)
  - [3.1 The order of knowing, and the rule that joins layers 1 and 2](#31-the-order-of-knowing-and-the-rule-that-joins-layers-1-and-2)
  - [3.2 Layer 0 — Headers: metadata, never meaning](#32-layer-0--headers-metadata-never-meaning)
  - [3.3 Layer 1 — The law as the computation: the MR signal equation](#33-layer-1--the-law-as-the-computation-the-mr-signal-equation)
  - [3.4 Layer 2 — KneeDiff in physics space](#34-layer-2--kneediff-in-physics-space)
  - [3.5 Layer 4 — The one language: the exact ledger, with the codebook as quantizer](#35-layer-4--the-one-language-the-exact-ledger-with-the-codebook-as-quantizer)
  - [3.6 What this Part hands on, the build order, and what stays open](#36-what-this-part-hands-on-the-build-order-and-what-stays-open)
- [Part 4 — Seeing: exclusion, the hardness map, perturbation anchors, the loop, and the λ-trajectory (layers 3, 5, 6 and 7)](#part-4--seeing-exclusion-the-hardness-map-perturbation-anchors-the-loop-and-the-λ-trajectory-layers-3-5-6-and-7)
  - [4.1 Exclusion: how a lens says "not here"](#41-exclusion-how-a-lens-says-not-here)
  - [4.2 The hardness map: where the views go blind in health](#42-the-hardness-map-where-the-views-go-blind-in-health)
  - [4.3 Perturbation anchors: a truth that survives a small step either way](#43-perturbation-anchors-a-truth-that-survives-a-small-step-either-way)
  - [4.4 The loop on the residual: commit, take out with the halo, read again](#44-the-loop-on-the-residual-commit-take-out-with-the-halo-read-again)
  - [4.5 The λ-trajectory: an explicit peak, and what it reduces to](#45-the-λ-trajectory-an-explicit-peak-and-what-it-reduces-to)
  - [4.6 What the four layers hand on](#46-what-the-four-layers-hand-on)
- [Part 5 — The society: agencies, the series committee, tiers, memory, censors, and teaching (layer 8)](#part-5--the-society-agencies-the-series-committee-tiers-memory-censors-and-teaching-layer-8)
  - [5.1 The society, and the rules every agency keeps](#51-the-society-and-the-rules-every-agency-keeps)
  - [5.2 The five agencies](#52-the-five-agencies)
  - [5.3 The committee is the series](#53-the-committee-is-the-series)
  - [5.4 Tiers: where the work goes](#54-tiers-where-the-work-goes)
  - [5.5 Memory: cases, recalled by concurrence within a trust radius](#55-memory-cases-recalled-by-concurrence-within-a-trust-radius)
  - [5.6 Censors: law-given, and written from near misses](#56-censors-law-given-and-written-from-near-misses)
  - [5.7 Teaching: reports teach, gold establishes, the founder's eye takes the hard sheets](#57-teaching-reports-teach-gold-establishes-the-founders-eye-takes-the-hard-sheets)
  - [5.8 Lens families: discovered by grid, checked on planted lesions](#58-lens-families-discovered-by-grid-checked-on-planted-lesions)
  - [5.9 The three-way split, made four by two references](#59-the-three-way-split-made-four-by-two-references)
  - [5.10 What the society hands on, the build order, and what stays open](#510-what-the-society-hands-on-the-build-order-and-what-stays-open)
- [Part 6 — Emission, measurement, falsifiers, and the build plan (layer 9; recipe steps 7 and 9)](#part-6--emission-measurement-falsifiers-and-the-build-plan-layer-9-recipe-steps-7-and-9)
  - [6.1 Layer 9 — Emission: a rank read off the kept record](#61-layer-9--emission-a-rank-read-off-the-kept-record)
  - [6.2 Recipe step 7 — Measure the substrate before anything is taught](#62-recipe-step-7--measure-the-substrate-before-anything-is-taught)
  - [6.3 Recipe step 9 — Judge each agency by its trajectory](#63-recipe-step-9--judge-each-agency-by-its-trajectory)
  - [6.4 What would show the design wrong: nine falsifiers, measured on the knee](#64-what-would-show-the-design-wrong-nine-falsifiers-measured-on-the-knee)
  - [6.5 The caveat that remains: confident joint errors](#65-the-caveat-that-remains-confident-joint-errors)
  - [6.6 The build plan, from the code that exists](#66-the-build-plan-from-the-code-that-exists)
  - [6.7 Open questions for the founder](#67-open-questions-for-the-founder)
- [Appendix A — Concordance](#appendix-a--concordance)
- [Appendix B — Glossary](#appendix-b--glossary)

## Part 1 — The case: the thesis instantiated for the knee

This Part states the case the later Parts build on: the problem (§1.1); the lineage, and where the knee
departs from it (§1.2); why the knee is the easier domain (§1.3); the thesis's precondition, checked clause by
clause (§1.4); the knee's \<object> (§1.5), set beside the cells (§1.6); the stance that there is no noise
(§1.7) and the two references it requires (§1.8); the laws that govern the design, and its relation to THEORY
and RECIPE (§1.9); the design on one page (§1.10); and a reading guide (§1.11). Sources, their short names and
the status words are set out in the front matter.

### 1.1 The problem, as the competition poses it

RSNA Knee Abnormality Detection asks, for each knee study, twelve binary findings: ACL, MCL, Medial
Meniscus, Lateral Meniscus, Medial OA, Lateral OA, PF OA, Effusion, Synovitis, Baker's, Contusion and
Fracture (THEORY Part I; `src/RSNA_Knee/report_parser.py`). The pictures are **MRI, not X-ray** (BRIEF §2),
and the difference is the thesis's own: the two are separate rows of the five domains it works by its
recipe (THESIS §13.2). A radiograph has already flattened depth, so shadows add along each ray. An MR
image's brightness is set by each tissue's magnetic relaxation under the sequence, and anatomy is
contiguous from slice to slice. Every law in this document is a law of the MRI row.

*Table 1.1. The competition, as the record states it.*

| What | The fact | Source |
|---|---|---|
| The record | About 5.5 series per study (24,371 over 4,407 training studies): planes × contrasts, flagged Anatomical_Plane × Fluid_Sensitive × Fat_Suppression; about 820,000 slices, 570 GB | RECIPE §1; THEORY Part I |
| The metric | Macro-averaged ROC-AUC: each finding's AUC over all test studies, then the unweighted mean; rank-based, ties averaged | THEORY Part I; `src/RSNA_Knee/scoring.py` |
| The test set | About 1,300 studies, images only | THEORY Part I |
| Gold | 58 training studies labeled by an expert re-reading the images. Every one carries at least one positive finding: no all-negative knee | BRIEF §2; LADDER; `tools/register_and_export.py` |
| Reports | Free text for every training study, about a dozen languages (English 1,729, Spanish 674, Turkish 546, Croatian or Serbian in Latin script 385, Greek 321, Dutch or German 253, Bulgarian or Serbian in Cyrillic 220, others in the tail); train-only | `src/RSNA_Knee/report_parser.py`; THEORY II.7 |
| The reports' ceiling | A perfect report reader scores about 0.88–0.92 against gold; the repository's parser scores 77.7% against gold | RECIPE §5; LADDER |
| The meniscus targets | "tear/degeneration" per a third-party summary; unverified | RECIPE §11, Q3 |

The kernel runs with the internet off for at most 9 hours (THEORY Part I), but the founder ruled the compute
budget and the deadline out of scope: "This is about planning, theory, and ideation." (founder, 2026-10-02;
BRIEF §2).

Four properties of the metric shape the design.
- *Order only.* AUC reads a finding's scores only as a ranking of studies, so a score is a rank key, not a
  probability, and calibration earns nothing. Ties cost: a design that only decides or abstains piles its
  abstentions on one value (RECIPE §9). Part 6 §6.1 grades the ranks; the tension with Law 7 is OPEN (Q4).
- *Macro over findings.* Each finding weighs a twelfth whatever its prevalence, and one the design cannot
  read costs its twelfth in full.
- *Per study.* No place is scored, yet place is how a finding is read. Grid zones capped the lens layer
  exactly where anatomy is small or thin (ZONES, Context), and localization is the frontier others report
  too (LADDER, v5).
- *Twelve numbers.* The thesis holds that "No single number means anything here" (THESIS §6.7). The
  emitted number orders the studies; the kept record of readings, cases and abstentions says why (Law 7;
  Part 6 §6.1).

The teaching material is lopsided. Gold is clean and expert, but small, and it holds no normal knee. The
true normals the reference needs were therefore harvested from the reports: 799 all-negative candidates,
of which 80 were fetched and registered, 50 squashed into the reference and 30 held out (LADDER). Reports
cover every training study and are independent of every pixel computation, but they are noisy as labels and
absent at test (RECIPE §5). Reports teach; gold establishes (Part 5 §5.7).

The build today reads one series per study, sagittal, fluid-sensitive and fat-suppressed (BRIEF §4;
LADDER). Every concurrence in it has a single voice, and the MCL and the joint spaces, read mostly on coronal
images, are read from the wrong plane. All v1–v4 numbers died in the substrate reset of 2026-08-30, when the
reference was found to have squashed mirror-image knees together since v1. On the v5 space (mm-true,
chirality-canonical), the first make-or-break reading on Effusion rose from AUC 0.58 to 0.68 as the detrend
scale went from off to σ = 24, and several held-out true normals still saturate (LADDER). These readings
test the substrate, not the design that follows.

### 1.2 Lineage: one thesis, three running instances

The design descends from three running instances of one idea: "A problem's structure carries information
from outside any local question into it" (THESIS §1.5).

**The thesis**, *What an \<Object> Is*, argues that a computer can understand a picture by reasoning from
what its objects are and how the instrument makes them visible (THESIS Abstract). It states the claim as
four hypotheses, each resting on the one before and each carried by a bridge (THESIS §1.4):

*Table 1.2. The thesis's four hypotheses, each carried by a bridge (THESIS §1.4).*

| | Hypothesis | Its bridge |
|---|---|---|
| H1 | *Vision built from the laws:* lossy views the laws license; borders in the data's topology; each \<object> taken out with the signal it spreads, the residual read again | The laws license exactly these losses and removals; what is left is a typed residue, not noise |
| H2 | *One exact language:* ternary digits against static middles, in banks of exactly orthogonal rows, bundled as whole-number counts, one cosine, an exact decode | The profiles keep the distinctions each question needs; measured, never assumed |
| H3 | *The bundles are K-lines:* a confirmed case cues a K-line, its −1 digits are censors; taught once, the memory moves the line the structure draws | Similar situations generally lead to similar results |
| H4 | *A society learns only the residue:* agencies with their own questions and clean signals; truth by concurrence; decide or abstain | Law checks support a judgment; an independent signal establishes it |

Nothing in the thesis's architecture names a nucleus except its laws, its lenses and its teaching (THESIS
§13.1, §14). Its MRI row reads: an organ or a lesion; relaxation under the sequence, and anatomy contiguous
from slice to slice; one lens per sequence; a radiologist's calls (THESIS §13.2). This document works that
row for the knee.

**Law as Architecture** concerns a known law whose few coefficients drift with regime, seen through a gapped
or locally ambiguous signal (LAA §1). Its six claims (LAA §2): the equation's structure becomes the network's
topology, as composed first-order specialists judged only at the composite; thin unknowns are recalled by
resemblance; near-miss censors make the impossible unrepresentable; regimes are stratified; missing inputs are
conditioned from coherent replicates; uncertainty propagates through the law's own Jacobian (LAA §5–10). LAA
names "medical imaging from sparse views" among its settings (LAA §11), and the knee has the signature: a
known forward law (the MR signal equation, Part 2 §2.3 and Part 3 §3.3), thin unknowns (each voxel's tissue
parameters), incomplete observation (a few contrasts, some series missing), and replicates (one knee under
several sequences).

**GenomeVault**, read through HDCSUB, supplies the substrate and the machine of the intelligence layer:
"the margin IS the confidence" (HDCSUB A.1); ternary as the minimum alphabet for orthogonal decomposition,
with complementary banks so that "you always have at least one clean signal to trust" (HDCSUB A.3); tiers
(HDCSUB B.1); a committee of encoders for which "Independence is the whole game" (HDCSUB B.2); lens families
found as local minima, the λ-trajectory, and the three-way distinction of encoding error, real variant and
input error (HDCSUB B.3); the header as "metadata", not a verdict on meaning (HDCSUB F.0); and the
corrections of HDCSUB F.4. The founder adds "the codebook serving as a lossy compression of scalar
intensity, the strict orthogonality serving for directionality encoding, and the balanced ternary used to
encode presence, absence, or orthogonality to the measure being encoded in that dimension", and "The
headers are cheap signals, not defining elements." (founder, 2026-10-02). The knee takes the ideas, not the
code: "don't worry about trying to actually use the code from GenomeVault. The ideas are elegant, the
encoding is genuinely primitive. I'll be rebuilding it completely from scratch." (founder, 2026-10-02). The
founder's charge: "We just need to build the right set of laws and lenses in this domain, and "KneeDiff"
[…] and the λ-trajectory are just the first and most elegant of them, with that document I uploaded last
time as a rich vein to mine for even more!" (founder, 2026-10-02).

Two outside precedents stand behind particular moves. Crowded-field photometry (DAOPHOT) and radio
astronomy's CLEAN subtract each source with its point-spread function and detect again on the residual;
their known failure, rings and holes, is what the thesis's post-take check looks for (BRIEF §4; THESIS
§4.5). The λ-trajectory detects prior–data conflict, and its closest classical relative is the power prior
of Ibrahim and Chen (2000) (BRIEF §4).

Where the knee departs from a source, it says so:

*Table 1.3. Where the knee departs from its sources.*

| A source says | The knee does instead | Why |
|---|---|---|
| A large residual where the law is tight is an error; where loose, a real variant (SYNTH Layer 2) | A large deviation where the *population* is tight is pathology; input error is read on a separate reference | §1.8 |
| "Vibe collapse" is validated (TIERED §2.3) | Not used | Its committed results lose all four comparisons (HDCSUB F.4 #1) |
| Recall returns a closeness-weighted blend (LAA §6); memory "calibrated from the report-derived labels" (THEORY Part III); one majority-bundled prototype per finding (`tools/lens_eval2.py`) | Individual cases with their sources, recalled within a trust radius set against chance; prototypes only as a data-layer instrument | "a sum would lose which readings occurred together in each case" (THESIS §7.1, §7.4; RECIPE §8) |
| Regimes by one of three stratified-regression designs, all fitted: a block-diagonal design, clustered regression or a mixture-of-experts gate (LAA §8; LAA §2) | Only the block-diagonal partition: known, sharp boundaries given by the header, with strict no-contamination. Per-regime references (median, MAD) and medians over individual cases taken at read time replace the per-block regression (Part 3 §3.3.5) | Every design fits a regression (Law 1); clustered regression and the gate also learn the partition |
| The replicate is a neighboring instance (LAA §9) | The replicate is the physics: one knee under several sequences | BRIEF §5, layer 1; Part 3 §3.3.6 |
| About 95% of chunks expected MONO_UP (SYNTH Part VIII) | The knee measures its own distribution of shapes | E10 measured 62.0% AMBIGUOUS, 31.5% PEAK_DROP (HDCSUB F.2) |
| λ as an additive overlay, dot-product decode (GenomeVault's public lens decoder) | An explicit peak: identity(λ) × fidelity(λ) (Part 4 §4.5) | The raw margin is then linear in λ, and the decoder's `best/total` confidence is degenerate (BRIEF §4) |
| PEAK_DROP is "structurally ACL but abnormal", MONO_DOWN is a misplaced zone, and emission reads the λ-peak height, since "Peak height = confidence" (BRIEF §5, layers 7 and 9; THEORY II.5) | identity(λ) is the same for every study, so the words are bands of ‖z‖²/p̂_S; "structurally S" is the placement margin m; emission reads H = Q, which keeps the drop's order (Part 4 §4.5; Part 6 §6.1.3) | In the closed form the peak's height falls as the deviation grows, and the trajectory adds no rank beyond the windowed ‖z‖² |
| Every surviving voxel superposed into D = 4096 at K = 4 random dimensions (`src/RSNA_Knee/hdc_encoder.py`; THEORY II.4) | The exact ledger: one Sylvester-Hadamard row per value, whole-number counts (THESIS §6.1; Part 3 §3.5) | About 2 or more writes per dimension, past TIERED's collapse line near 1.5 (BRIEF §4; TIERED §2.2), a line itself documented-only (HDCSUB F.4 #5) |
| A truth survives a small step either way in time (THESIS §3.4) | A step either way in space and in encoding (Part 4 §4.3) | A study has no time |
| The anatomical forward model is wired as the network (THEORY Part III) | The MR signal equation is; anatomy enters as the population reference and as censors (Part 3 §3.3; Part 5 §5.6) | Its form is exactly known |

### 1.3 Why the knee is the easier domain

The thesis was built on the harder domain on purpose. The founder: "The project here...is meant to resolve
"is knee" or "sad knee". MUCH more forgiving." (founder, 2026-10-02). GenomeVault's committee answered
3,695,997 clinical positions with no error among the 99.99992% it auto-accepted (COMMITTEE, Executive
Summary). The cells ask for every nucleus at every time point, each within 7 µm of the hosts' annotation
(THESIS §2.4). For the cells the founder reports, from work not yet in the thesis text, that 100% of
annotated nuclei are captured cleanly; that the loop runs 14 to 16 rounds to empty the box, with every
annotated cell out in rounds 1 to 3; that cleanly resolved positions lie under 2 µm from the annotation;
and that the full pipeline is not yet complete (founder, 2026-10-02; BRIEF §3, item 7).

The knee is more forgiving on five counts.
1. *The question is categorical, and only its order is scored:* "is knee" or "sad knee", per study and per
   finding. That is the squint's best case, a question that "needs a reading only to fall on the right side
   of a line" (THESIS §3.5).
2. *The structures are known in advance.* One of each, in one arrangement (L1), placed by the atlas; for
   structures H1's object-finding comes free, and "how many?" never arises (RECIPE §1).
3. *There is no time:* no anchors, no following, no identity across frames, no division.
4. *The views differ in physics, not only in focus.* The cells had four focus lenses on one signal; a knee
   study has about 5.5 series differing in plane and contrast, which disagree for reasons a law names (L2,
   L3).
5. *Every training study comes with an expert's words:* a report for each of 4,407 studies, where the
   cells were taught a few dozen calls (THESIS §8).

On other counts the knee is harder. Its labels are noisy, and binary over graded conditions (OA, meniscal
degeneration, synovitis). Gold holds no normal knee. The menisci and the MCL lie at the scale of the 3–4 mm
slice spacing (L3), where partial volume blurs them. Protocols span vendors and countries. A study's series
must be put into one space, and the patient may move between them. And registration errors poison
everything after them silently, as the mirror-image squash did (§1.1; LADDER).

So most of H1 comes free, and the work moves to meaning (H3, H4) and to concurrence across series (RECIPE
§1). Because registration can fail silently, it is read on an axis of its own (§1.8). And since a study
holds few lesion-objects, its loop should empty in few rounds: an expectation, DESIGNED here, to be
measured, not assumed.

### 1.4 The precondition, checked clause by clause

The thesis holds where the precondition of its companion paper holds (THESIS §1.3); the thesis shows the
cells meeting it (THESIS §2.6), maps four of its clauses to steps of the recipe (THESIS §13.1), and names six
findings that would show it wrong in a domain (THESIS §13.3). For the knee:

**Clause 1: "The domain's laws can be stated".** It holds. L1–L5 are stated in RECIPE §2: anatomy, MR signal,
acquisition, pathology (for instance the two-slice-touch rule for meniscal tears, De Smet and Tuite 2006) and
mechanism. This document adds L2's formal content, the spin-echo signal equation S ≈ PD × (1 − e^(−TR/T1)) ×
e^(−TE/T2), with TR and TE read from the headers (Part 2 §2.3; Part 3 §3.3). A law is "a physical or
biological regularity the system reasons from" (THESIS §2); L4's rules are clinical regularities of that kind.
*It could fail* by a missing law (OPEN, Q1), or a signal equation that cannot be made to hold under unknown
receiver gain, fat suppression and fast-spin-echo effects (OPEN; Part 3 §3.3.9). *It is measured* by the first
falsifier, lenses that cannot resolve most of the problem in concurrence (THESIS §13.3 #1), per finding on
gold and by whether the box empties.

**Clause 2: "Its state is discrete, with one true answer at each moment".** It holds for the internal state
and by convention for the labels. A study is one moment; each voxel belongs to one zone and holds one tissue
and at most one lesion (L1; RECIPE §6). But the OA findings, synovitis and meniscal degeneration are graded
processes the labels binarize, so their true answer is a labeler's threshold on a continuum. *It could
fail* where a binarization is too soft for any reading to rank, or if the meniscus targets count
degeneration as positive (OPEN, Q3), which turns the canonical near miss into a second positive. *It is
measured* by report–gold agreement per finding: a map of which findings are soft, kept as information (Part
5 §5.7).

**Clause 3: "Each of its instrument's lossy views ... can be read against one law".** It holds, and the
build does not yet exercise it. A **lens** is "a cheap, deliberately lossy view that measures one thing and
knows no question" (THESIS §3.2). A knee's primary views are its series: each reads one plane sharply and
the through-plane direction coarsely (L3), under one contrast that writes one digit of a tissue's signature
(L2). A structure is read in the series whose plane holds its long axis, "each lens at its own sharpest
depth," moved from depth to plane (RECIPE §2, L3). The loss is licensed because the knee does not change
between the series of one sitting; where it does, by motion, that is an input error (§1.8). *It could fail*
for thin structures oblique to every plane, for motion, and for views with correlated errors. *It is
measured* by the independence gate (HDCSUB F.4 #4) on the knee's own evidence: the errors of sagittal,
coronal and axial readings, and of fluid-sensitive and T1 readings, measured on gold before their agreement
counts (RECIPE §7). With one series per study, the gate cannot yet run.

**Clause 4: "Each learner has a signal that is clean for what it learns".** It holds, with a caveat about
noise. Clean means independent of what is learned (THESIS §10.1), not free of error. Reports are clean,
being independent of every pixel computation, and noisy (RECIPE §5); gold is clean, expert and small; the
true normals were chosen from text alone (LADDER); lesions planted in true normals are clean by
construction for validating a lens (LENS Phase 4; Part 5 §5.8). *It could fail* by circularity, as when the
negative prototype's members also built the reference, so "their own residuals are biased low"
(`tools/lens_eval2.py`); or by a "true normal" whose report missed a lesion, widening the reference exactly
where that lesion should stand out. *It is measured* by the second falsifier (THESIS §13.3 #2): every case
keeps its source, no agency is taught by the cases it settled itself (THESIS §10.3), and no held-out normal
is a member of the reference.

**Clause 5: "The laws can be checked on the output."** It holds for the kept record, not for the twelve
numbers. RECIPE §6's checks run on the committed objects: one lesion, one place across views, the knee's
sandwich with two views in place of two anchors (THESIS §11.5); no two objects in one space; each object
well formed; the emptied box; events that keep the rules. *It could fail* by a confident joint error, every
view agreeing and wrong, which passes every check, as two carries "can agree on the same wrong neighbor"
(THESIS §11.5; BRIEF §5). *It is measured* off the output, since law checks only support (THESIS §10.5): by
gold read as near misses, and the censors they write (THESIS §7.6; Part 5 §5.6).

*Table 1.4. The precondition, clause by clause.*

| Clause | Knee | Status | Falsifier (THESIS §13.3) |
|---|---|---|---|
| Laws stated | L1–L5 and the signal equation | Holds; Q1 open | #1 |
| Discrete state | Zones, structures, lesion-objects; binary labels over some graded conditions | Holds internally; by convention for OA, synovitis, degeneration | #3 |
| Lossy views against one law | Plane (L3), contrast (L2), population (L1) | Holds; unexercised while one series is read | #1, #3 |
| A clean signal per learner | Reports teach; gold establishes; true normals; planted lesions; landmarks | Holds; reports noisy, gold small and all-positive | #2 |
| Laws checked on the output | One place across views, one space, well formed, emptied box, mechanism | Holds on the record; a confident joint error passes | #2 |

### 1.5 The knee's \<object>: structures and lesion-objects

An **\<object>**, in the thesis, is contiguous and closed, persistent, moved by physics, and signaling by
known laws (THESIS §1.2). A knee holds two kinds (RECIPE §1). A **structure** is always present, one of
each, placed by the atlas: the ACL and PCL, the menisci, the MCL, the cartilage plates, the bones, the
recesses, the fat pad. Its only question is whether it is abnormal. A **lesion-object** is present or
absent and lives in the residual: a fluid collection, a marrow edema, a fracture line, the fluid signal
inside a tear. Its questions are whether it is there, where, and which finding it serves.

The two kinds live on opposite sides of the subtract. KneeDiff (BUILT; `src/RSNA_Knee/kneediff.py`,
`src/RSNA_Knee/platonic_reference.py`) squashes N registered true normals, voxel by voxel, into a mean μ and
a spread σ, and writes each voxel of a study as z = (x − μ − trend) / max(σ, floor), the trend a mask-aware
low-frequency field (THEORY II.2–II.3; RECIPE §0). Voxels with |z| under the threshold (3 in the current
tools) are licensed by the population: they are **the knee's black**, the thesis's stage 1/2 resolved away,
a decision kept as a record and never a discard (THESIS §4.2; RECIPE §0). What survives is **the residual**.
The founder:

> "Where an image is showing just a generic shape of a knee, resolvable as a hypervector representation of
> the knee, kind of like stage 1/2 from the thesis there resolves away the "background" cleanly, so no heavy
> compute or reasoning is wasted on that which we know is insignificant. So the "knee", or the lesions, it
> can become MUCH more than 0.1% of the volume of the image." (founder, 2026-10-02)

In the residual a lesion is a large share of what is left, so the static middles of residual metrics are
set over the residual cells of the teaching studies, never over raw voxels (RECIPE §4; Part 3 §3.4.4).

A normal structure lies in the black. It is read against its own prior by the λ-trajectory (Part 4 §4.5) and
by the lenses its law names: continuity and course for a ligament, surface contact for a meniscus (RECIPE §3;
Part 2 Table 2.8a). It is never taken out; it is the frame the residual is read in. A lesion-object is a
contiguous region of same-sign deviation in a zone, with a signature its law names (L2) and a place its law
allows (L4). It is committed by concurrence across series and taken out with its **halo**, the signal its law
says it spreads: an effusion with its partial-volume rim, an edema around its fracture line (Part 4 §4.4).

Two of the thesis's marks are translated. *Persistent* means persistent across views, one lesion landing in
one place on every series that covers it (RECIPE §6), and under small perturbation (Part 4 §4.3). *Moved by
physics* becomes placed under anatomy: fluid pools in the recesses, a Baker's cyst lies between the medial
gastrocnemius and the semimembranosus with a neck to the joint, edema lies inside bone, a fracture line
reaches the cortex (L4). One structure per place is the thesis's one cell to one place (THESIS §2.3, §5.3).

A **finding** is a zone together with a change of signature (RECIPE §2): a meniscus zone, dark on every
sequence in health, turning bright on the fluid-sensitive series. The twelve findings fall into three kinds
of reading (DESIGNED, from RECIPE §2–§5): the state of a structure; the presence of a lesion-object; and the
state of a compartment, an assembly of signs that co-locate in it.

*Table 1.5. The twelve findings, by kind of reading, zone, plane and law.*

| Finding | Kind | Zone: BUILT in `src/RSNA_Knee/anatomy.py`, or to add (RECIPE §10) | Plane (L3) | What makes it readable (L2, L4) |
|---|---|---|---|---|
| ACL | Structure | Intercondylar notch; ACL centerline to add | Sagittal | A low-signal band parallel to the notch roof, striated and less dark than the PCL in health, so read against its own reference; a gap, fluid signal or a flatter course |
| MCL | Structure | No dedicated zone yet; MCL band to add | Coronal | A continuous dark band; signal within or around it |
| Medial, Lateral Meniscus | Structure | Medial, lateral compartment; horns and bodies to add | Sagittal (horns), coronal (bodies) | Dark on every sequence; signal reaching an articular surface on two or more slices |
| Medial, Lateral OA | Compartment state | Medial, lateral compartment; cartilage plates to add | Coronal | Cartilage loss, joint-space narrowing, marginal osteophytes, lesions under the cartilage, meniscal extrusion, co-located (MOAKS subregions) |
| PF OA | Compartment state | Retropatellar | Axial | The same signs, patellofemoral |
| Effusion | Lesion-object (fluid) | Suprapatellar recess | Sagittal, axial | Fluid signature (fluid-sensitive bright, T1 dark) distending the recess |
| Synovitis | Lesion-object (signal in fat) | Hoffa's fat pad to add | Sagittal | Fluid-sensitive brightness in fat that should be dark; effusion-synovitis (MOAKS surrogates), read once the effusion is out |
| Baker's | Lesion-object (fluid) | Popliteal | Axial, sagittal | Fluid between the medial gastrocnemius and the semimembranosus, with a neck to the joint |
| Contusion | Lesion-object (edema) | Femur, tibia, patella | Any | Fluid-sensitive bright and T1 dark inside bone; geographic, often under the cartilage |
| Fracture | Lesion-object (line) | Femur, tibia, patella | Any; the line on T1 | A T1-dark line inside edema reaching the cortex, read once the edema is out |

### 1.6 Cells and knees, side by side

*Table 1.6. Cells and knees, side by side.*

| | Cells (THESIS) | Knees (here) |
|---|---|---|
| The \<object> | A nucleus; how many is unknown (§2.1) | Structures, one of each, placed by the atlas; lesion-objects in the residual (§1.5) |
| The question | Is this one cell? Where did it go? Did it divide? | Is this structure abnormal? Is there a lesion-object, where, and which finding? |
| The record | About 100 time points, each 64 slices of 256 × 256 voxels (§2.1) | About 5.5 series, each sharp in-plane, about 3–4 mm between slices (L3) |
| Time | Three anchors, following, division (§3.4, §11) | None; series replace time points, perturbation replaces the step either way (Part 4 §4.3) |
| The collapse | Each lens at its own sharpest depth (§3) | Each structure in the plane that holds its long axis; each contrast one digit of a signature (RECIPE §2) |
| Independent views | Four focus lenses on one signal (§3.2) | The series, differing in plane and physics: the committee (Part 5 §5.3) |
| The black | The camera's dark, then the local haze, per frame and depth (§4.2) | What the true normals license, per voxel and series type (§1.5; Part 3 §3.4.3) |
| The halo | A nucleus's spread light, by the inverse-square law (§5.5) | An effusion's partial-volume rim; edema around a fracture line (Part 4 §4.4) |
| One to one place | One cell to one place (§2.3, §5.3) | One structure per place; one tissue, at most one lesion, per voxel (L1; RECIPE §6) |
| The two-sided check | The sandwich between anchors (§11.5) | One lesion, one place across views (RECIPE §6) |
| Teaching | A few dozen expert calls, in a few hours (§8) | A report on every training study; 58 gold re-reads; the founder's eye on hard sheets (RECIPE §5, §8) |
| The count's analog | The hosts' count: how many, never which (§2.4, §10.1) | The report's list of findings: which, never where (RECIPE §5) |
| Output | Every nucleus at every time point, linked, within 7 µm (§2.4) | Twelve rank-ordered scores per study, judged by macro-AUC |

What carries over unchanged is what the thesis says carries (THESIS §13.1): the loop that empties the box,
the one language, the K-lines and censors, decide or abstain, and the society. What belongs to time (the
anchors, the following, the Ephemeris move, division) is dropped.

### 1.7 There is no noise: information and entropy

The founder, on the stance this design keeps:

> "the *real* problem isn't "target" vs "failure", but "information" vs "entropy". If you have some sort of
> analysis lens that is NEVER able to resolve the signal you want...well, isn't that a *perfect* lens for
> where your signal is *not*?? That IS information! Knowing where something is NOT is extremely useful for
> knowing where something is! In the clinical committee doc, that isn't a failure--"oh no, some spots are
> 36,210x harder to resolve". It's *information*--"hey, I now have an EXTREMELY divergent signal that
> differentiates parts of the genome in a structurally-relevant way, and can be used to provide information
> about how that bit of DNA actually behaves!"" (founder, 2026-10-02)

The thesis states the stance twice. Of its stage 1: "That is what there is no noise means: a removal is a
decision by a reading entitled to make it, kept as a record, never a discard. The principle does not deny
what an expert calls noise, light that belongs to no cell. It says that nothing is discarded unexplained,
and that a disagreement between correct readings is information." (THESIS §4.2). And as **reading by
exclusion**: "a reading that is poor at finding a signal can be reliable at saying where the signal is not"
(THESIS §3.6). Law 6 is the project's form: deviation is the pathology channel, "not noise to suppress"
(THEORY Part IV).

The genomic evidence is exact. Four independent encoders failed together at 2 positions where independence
predicted 0.00006, a ratio of 36,210, which the committee's authors read as "actually beneficial: these
positions can be detected and flagged" (COMMITTEE §4.2); the flagged positions share a structural type: N
bases, GC content of 70–78%, homopolymers, repeats (COMMITTEE §6.2). TIERED gives the other half: errors at
margin 0 are predictable from the vector's own features (d = 1.95 for its total magnitude), while errors at
margin 2 spread uniformly across GC content, base type and magnitude (TIERED §3.1.1). The first kind of
failure is information about the structure; the second is, for that set of lenses, entropy. Part 4 §4.2 reads
both results in full and builds the hardness map on them.

The design makes the stance a typing of every reading (DESIGNED; Part 3 §3.5.3; Part 4 §4.1–§4.2). A lens's
output at a place carries exactly one of five meanings, each written differently:

*Table 1.7. The five meanings a reading can carry.*

| Meaning | How it is written | What fixes its meaning | Example in the knee |
|---|---|---|---|
| **Present** | +1 on the target's question | The lens's own law | Fluid signature in a meniscus, touching its surface |
| **Excluded** | −1 on the target's question: an **exclusion mark** | A positive reading of something a law makes incompatible with the target | T1-bright fatty marrow excludes edema; a continuous dark band excludes a tear along it; an empty recess excludes effusion; a dark meniscus without surface contact excludes a tear |
| **At its middle** | 0, a written row (THESIS §6.2) | The static middle | Cartilage of intermediate signal |
| **Blind here** | A silent bank, the informational zero (THESIS §6.3) | The **hardness map**: where this view goes blank, or misleads, even in health | The meniscus–capsule junction; partial-volume edges; fibrous tissue near the magic angle, which brightens on short-TE series only (L2) |
| **Unexplained** | Kept as a finding, with its context | Nothing yet: the share no law explains | Deviation no lens claims once the box is emptied |

A lens's reading at its middle is written as a row of its own bank; on a finding's question it is
*orthogonal*, read and bearing neither for nor against (Part 3 §3.5.3 keeps these three zeros apart). A
reading taken where the input breaks a constraint is unverifiable whatever its digit, and is judged on the
second reference (§1.8).

The **hardness map** is the founder's ruling applied to COMMITTEE §4.2 and TIERED §3.1.1 (BRIEF §5, layer 3).
Built from true normals, which carry no target, it marks where a view goes blank or misleads, or the views
disagree, in health: places where the views are structurally blind, not places where something is missing. It
is a structural lens that reads nothing in a study and says where each view's silence is expected. A silence
on the map counts neither for nor against; a silence off it is itself a deviation; and a zone where every
series is blind is kept as hardness information, the knee's Tier 2, never guessed (TIERED §1.2; Part 5 §5.4).

The thesis supplies the guardrails. An exclusion mark is a reading of something else, never an inference
from a missing positive: "The negative is a fact of its own, given or confirmed by the expert, never inferred
because a positive match is missing" (THESIS §7.3). "A reading never made is not a low reading" (THESIS
§6.3). And a refusal "says the question was not resolved there, never that nothing is there"; it writes no
censor (THESIS §10.3, §7.5). The founder's never-resolving lens is information about a place and a lens,
measured once in health, not a verdict on any one study.

The distinction also sets the work list. A failure with a predictor (a place, an orientation, a regime)
belongs on the hardness map or in a censor. A failure with none is the share no law yet explains, and Law 5
says to suppose first that the signal is missing information, never that capacity is (THEORY Part IV). The
stance has a dynamic form too: a lawful removal changes what the remainder means, as in the Monty Hall
problem (THESIS §4.6). Once an effusion is out with its rim, the fat pad and the posteromedial neck are read
for synovitis and a Baker's cyst; once an edema is out, a line left inside it is a fracture (BRIEF §5,
layer 6; Part 4 §4.4).

*How the stance can fail, and how that is measured.* A map built from too few normals, or one regime, marks as
blind places that are only unseen; one built from normals whose reports missed a lesion marks that lesion's
place blind. Both are measured with lesions planted in true normals (LENS Phase 4; Part 5 §5.8; Part 4 §4.2):
recovery off the map should be high, and where recovery fails should be the map's places, the same across
regimes, for a reason a law names.

### 1.8 Two references, never merged

GenomeVault reads tightness one way: "Large residuals in structurally constrained positions → errors";
"Large residuals in variable positions → real variants (keep!)" (SYNTH Layer 2). The knee reads it the other
way. KneeDiff divides each deviation by the population's spread (`residual_z` in
`src/RSNA_Knee/kneediff.py`), so a deviation where normal knees agree is large and is the pathology signal,
while the same deviation where they vary is licensed and resolves away (THEORY II.2). The genomic reading
cannot be ported (RECIPE §0).

It did answer a question the knee still has: when is a deviation the input's fault? In the genome one
reference served both purposes. In the knee a large deviation in a tight place may be a lesion, a zone the
registration misplaced, or the signature of a vendor, of motion or of the magic angle. So the knee keeps two
references and never merges them (RECIPE §0; BRIEF §4):
- **The population reference**, the pathology axis: the per-voxel distribution of true normals, per series
  type and regime (Part 2 §2.9; Part 3 §3.4). Does this knee deviate from what normal knees license here?
- **The constraint reference**, the input-error axis: the laws that make the comparison valid. Is the
  comparison valid here? Its readings are the chirality decision (LADDER, v5; BUILT in
  `tools/register_and_export.py`); the landmark check by normalized cross-correlation (ZONES, Rank 2;
  decided, not built); the signal equation's misfit across series (Part 3 §3.3.8); stability under perturbation,
  and the axis along which a reading flips (Part 4 §4.3); and the λ-trajectory's placement margin, read where a
  structure's confidence falls steadily as its prior is applied (MONO_DOWN; Part 4 §4.5).

*Table 1.8. The two references, crossed.*

| | Constraints hold | Constraints broken |
|---|---|---|
| **Small deviation from the population** | Normal: the black | Unverifiable: a misplaced zone can show normal tissue from elsewhere. Kept, never read as normal |
| **Large deviation from the population** | A candidate: pathology, or a rare normal variant, settled by the split of what survives (SYNTH Part II's three-way distinction, made four in Part 5 §5.9) | Input error: re-register, perturb or set aside; never a finding |

The mechanism (DESIGNED):
- *Reads:* each deviant region's z against the population, and the study's constraint readings, per zone
  where they are local.
- *Computes:* nothing that combines them. Each axis has its own banks (H2), so neither outvotes the other.
- *Emits:* one cell of the table above, kept with the readings behind it.
- *Licensed by:* L1 for the population; Law 3, L2 and L3 for the constraints.
- *Fails:* (i) by a confident joint error, all series agreeing and wrong with every constraint satisfied,
  which neither axis sees (BRIEF §5); (ii) by a population too thin to be honestly tight, since a spread from
  few references has heavy tails and n = 20 inflates P(|z| > 3) about 2.8 times (VERDICT); (iii) by a
  constraint false alarm on unusual but normal anatomy.
- *Measured by:* lesions planted in true normals, with and without deliberate misregistration (Part 3 §3.3.10;
  Part 4 §4.3): the population reference should rise for the lesion and the constraint reference for the
  misregistration, never the reverse. Each held-out true normal that still saturates on v5 (LADDER) must be
  explained on one axis or the other. Failure (i) is measured on gold read as near misses (Part 5 §5.6; Part 6
  §6.5).

One ambiguity is resolved only by keeping the axes apart. A structure whose trajectory falls steadily may be
misplaced, an input error, or absent, as after a complete tear. If the constraint reference holds, with the
landmarks in place and the neighboring structures rising steadily, the fall is a population-axis reading, a
candidate absent or grossly abnormal structure, handed to the agency that reads the structure (layer 8; for a
ligament or meniscus, the fibrous-structures agency), which alone decides (Law 4). The fall is that reading;
if the constraints are broken, the fall is a registration alarm (DESIGNED; Part 4 §4.5).

### 1.9 The laws that govern this document, and what it replaces

Two families of law govern, and they are not to be confused. The **project laws**, Laws 1–8 of THEORY Part
IV, govern what the design may be. The **domain laws**, L1–L5 (RECIPE §2) with the signal equation as the
formal content of L2, are what the design reasons from. The first project law in the founder's words: "The
architecture IS no ML. I bite my thumb at ML. Maybe I'll end up using some small model somewhere for some
reason, but NO, the architecture is NOT NOT NOT ML." (founder, 2026-08-18; FOUNDING). The design is never
framed as "small ML" (BRIEF §3, item 9).

*Table 1.9. Where the project laws bind.*

| Project law (THEORY Part IV) | Where it binds here |
|---|---|
| 1. The architecture is not ML | Layer 1's specialists invert a known equation per voxel, with TR and TE from the headers; nothing is fitted across studies. Memory holds individual cases, never weights (THESIS §1.3, §7.1). Of LAA §8's three stratified-regression designs (all fitted: LAA §2), only the block-diagonal partition is kept: known, sharp boundaries from the header, with strict no-contamination. Per-regime references (median, MAD) and medians over individual cases taken at read time replace its per-block regression (Part 3 §3.3.5); clustered regression and a mixture-of-experts gate are dropped, since they also learn the partition |
| 2. No smuggling | The reports' noise is answered by gold, near misses and censors (Part 5 §5.6–§5.7), never by a model that "cleans" labels |
| 3. One bounded utility: registration | Affine then B-spline, mask-aware (`tools/register_and_export.py`), on a deliberately coarse mesh of [10, 10, 4] control points, for condyle-scale correspondence "without lesion-scale warps that would erase the pathology signal" (LADDER): bounded so that it cannot erase what it serves. A small keypoint network is permitted but not needed (ZONES). The founding decision names registration and normalization the single sanctioned bounded utility (NOML, Decision 1) |
| 4. The data layer narrows; it never decides a finding | Layers 0–7 narrow, encode and propose; layer 8 decides or abstains, and layer 9 emits a rank that decides nothing (Part 6 §6.1.2). A header is metadata (HDCSUB F.0). No finding is decided by confidence-coupling (Part 5 §5.1; Part 6 §6.1.2) |
| 5. Iterate the encoder, not the model | LADDER is this law at work: a plateau means missing information, so the next move is another law, lens or view |
| 6. Margin and deviation are signal, not error | The stance of §1.7 |
| 7. Provenance and abstention (→ 0.5) | Every score traces to readings, cases and laws; abstaining at 0.5 versus ranking by partial evidence is OPEN (Q4; Part 6 §6.1) |
| 8. Never auto-submit | Part 6 §6.6.3 ends at an expected score surfaced for the founder, not at a submission |

**Relation to THEORY.** THEORY records the data layer in full (THEORY Part II) and sketches the intelligence
layer "to be designed" (THEORY Part III). This document fills THEORY Part III, specifying its five elements
(law as topology, recollective memory, near-miss censors, regime stratification, delta-method confidence)
mechanism by mechanism, with the MR signal equation as the law wired in. THEORY's Part II stands, changed
where Table 1.3 says: physics-space KneeDiff, the exact ledger, the explicit λ peak, and tiers keyed by the
header with the series as committee. THEORY Part III's first question, whether the reference absorbs normal
variation and leaves only pathology, remains the first test, now on v5 (LADDER). THEORY's laws bind, and its
record of the two deaths (THEORY Part V) is what this document must not repeat.

**Relation to RECIPE.** RECIPE, the first draft of the recipe worked for the knee, is superseded and
expanded: its laws, lens table, agencies, law checks, output-contract proposal and questions Q1–Q7 are
kept; layers 0–9 are added; and two of its warnings become mechanisms, the two references (§1.8, from RECIPE
§0) and cases, not prototypes (Part 5 §5.5, from RECIPE §8). Authority runs as RECIPE's own supremacy clause set
it: the founder's verbatim statements over everything, then the canon and THEORY's laws, then this document
(RECIPE, Supremacy; BRIEF, preamble).

*Table 1.10. What is built, designed and open.*

| Element | Status | Where |
|---|---|---|
| Scorer: macro-AUC, rank-based, ties averaged | BUILT | `src/RSNA_Knee/scoring.py` |
| Report parser: twelve labels, multilingual, negation and laterality; 77.7% against gold | BUILT | `src/RSNA_Knee/report_parser.py`; LADDER |
| Registration v5: mm-true, chirality-canonical, N4, knee mask, affine then B-spline | BUILT, one series per study | `tools/register_and_export.py` |
| Platonic reference and KneeDiff on raw intensity, with detrend | BUILT | `src/RSNA_Knee/platonic_reference.py`, `src/RSNA_Knee/kneediff.py` |
| Template anatomy: bone masks, landmarks, a twelve-label zone volume from one template study | BUILT; awaiting the founder's eye-check | `src/RSNA_Knee/anatomy.py`, `tools/build_atlas.py`; LADDER |
| Make-or-break: rank AUC of peak local survivor density | BUILT | `tools/make_or_break.py`; VERDICT |
| Encoding v1 (random sparse superposition); lens read by majority-bundled prototypes | BUILT; to be replaced (Part 3 §3.5.1) and demoted to an instrument (Part 5 §5.5) | `src/RSNA_Knee/hdc_encoder.py`, `tools/lens_eval2.py` |
| Landmark check by normalized cross-correlation; multi-atlas fusion; an unbiased template | Decided, not built | ZONES |
| Eight text-extraction template modules | Scaffold; repurpose or delete (OPEN, Q7) | `src/RSNA_Knee/`; BRIEF §4 |
| Layers 0–9 | DESIGNED | Parts 2–6 |
| Q1–Q7; the signal equation's feasibility; jitter magnitudes; the hardness map's construction; the planted-lesion library | OPEN | BRIEF §7; Part 6 §6.7 |

### 1.10 The whole design on one page

```
 A STUDY: ~5.5 series (plane x contrast), each sharp in-plane, ~3-4 mm between slices
                                       |
 (0) HEADERS, metadata never meaning: DICOM tags (vendor, field strength, TR/TE/TI, fat
     suppression, plane, spacing); the series inventory; later, whole-vector aggregates
     (fluid share, deviant count, trajectory shape, lambda*) --> REGIME KEY, the "Cmd-F"
                                       |
 REGISTRATION (Law 3, the one bounded utility): mm-true, chirality-canonical, coarse
     B-spline, one kept transform per study; the landmark check ................. [C]
                                       |
 (1) THE LAW AS THE NETWORK: S ~ PD (1 - e^(-TR/T1)) e^(-TE/T2), seen once per series;
     one specialist per term -> tissue parameters per voxel, with delta-method spread;
     missing series imputed by the law; the law's misfit kept as information ....... [C]
                                       |
 (2) KNEEDIFF IN PHYSICS SPACE: each voxel against the true normals (mu, sigma) .... [P]
     -> THE BLACK (licensed: resolved away, kept as a record)    -> THE RESIDUAL
            |                                                          |
            | the structures, always present                           | lesion-objects
            v                                                          v
 (7) LAMBDA-TRAJECTORY per structure         (3) EXCLUSION LENSES: "not here" marks;
     x(l) = (1 - l) x + l mu                          the HARDNESS MAP (blank in health)
     confidence = identity x fidelity        (4) THE ENCODING: the exact ledger; banks are
     MONO_UP    normal                                physics quantities; ternary present,
     PEAK_DROP  abnormal ............ [P]             absent, orthogonal; one cosine
     MONO_DOWN  alarm or absent -------+     (5) PERTURBATION: registration jitter and
            |                          +------>       quantizer-edge shifts -> stability
            |                                         fraction, flip axis ............ [C]
            |                                (6) THE LOOP: commit by concurrence across the
            |                                     series; take out with the halo; read the
            |                                     residual again until the box is empty
            +------------------------+-------------------------------+
                                     v
 (8) THE SOCIETY: agencies (fluid, marrow, fibrous structures, compartments, every finding);
     the committee is the series; tiers; memory of individual cases within a trust radius;
     censors, law-given and from near misses; reports teach, gold establishes; lens
     families checked on planted lesions; zone lambda-bounds; cross-contrast consistency;
     the split (input error / instrument / normal variant / pathology). Decides or abstains.
                                     |
 (9) EMISSION: three registers by the society's word (decided present / open / decided
     absent); the decided registers ordered by the concurrence count c, the stability
     digit, then the host deviation H (the windowed lambda-drop); the open register at 0.5,
     or by the lean and L5 digits if Q4 allows; Tier 2 and unverifiable fixed at 0.5; the
     law's sigma acts inside z and through a guard --> 12 rank-ordered scores per study,
     judged by macro-AUC

 (n) a layer, numbered as in BRIEF §5; L1-L5 always name the domain laws (Part 2)
 [P] a reading on the population reference (pathology)
 [C] a reading on the constraint reference (input error); the two are never merged (§1.8)
 Layers 0-7 narrow, encode and propose (Law 4); layer 8 decides or abstains; layer 9 emits.
 All of it is DESIGNED. BUILT today: registration, and KneeDiff on raw intensity, one series (§1.9).
```

*Figure 1.1.* The design on one page. Headers point and never decide; registration puts the series in one
space. The signal equation recovers each voxel's tissue parameters, and KneeDiff compares them with the true
normals: what the population licenses is the black, the rest the residual. Structures are read against their
own priors by the λ-trajectory, whose steady fall goes to the placement margin: below zero it raises a
registration alarm, and above its null range it is a candidate absent structure for the society to decide; the
residual is read by exclusion lenses, written in the exact ledger, tested under perturbation and emptied by the
loop. The society decides or abstains; the emission ranks.

### 1.11 A reading guide to Parts 2–6

The later Parts follow the recipe (THESIS §13.1), each using only what earlier Parts make. Part 2 works the
domain's own steps, the laws, the lenses and the priors (recipe steps 1–3), with each law's check on the
output (step 5). Parts 3 and 4 build what the recipe says carries over unchanged, the one language and the
loop that empties the box, in the order a study is read: Part 3 the substrate (layers 0, 1, 2 and 4), Part 4
the reading of it (layers 3, 5, 6 and 7). Part 5 is the society (layer 8): its clean signals, its agencies
and their teaching (steps 4, 6 and 8). Part 6 emits (layer 9), measures the substrate and judges each agency
(steps 7 and 9), names what would show the design wrong, and lays out the build.

*Table 1.11. Where each layer and step is designed.*

| Part | Layers; recipe steps | The questions it answers |
|---|---|---|
| 2 | the laws every layer reasons from; steps 1–3 and 5 | What the five laws L1–L5 state, license and check; which lens reads each law term, what it rules out and where it is blind; the knee's collapse and squint; the priors as regime keys; the zones the lenses need from the atlas |
| 3 | registration's front end; layers 0, 1, 2 and 4 | What the headers carry, and may and may not do; how the signal equation becomes the network, and what its specialists recover per voxel; how the reference moves into physics space; what the black and the residual are, numerically; how every reading is written in the exact ledger, with the codebook as quantizer |
| 4 | layers 3, 5, 6 and 7 | How a lens writes "not here", and how the hardness map is built; how perturbation tests a reading, and what a flip's axis says; how a lesion-object is committed by concurrence, taken out with its halo, and the residual read again; how the λ-trajectory gets an explicit peak, and what each shape routes |
| 5 | layer 8; steps 4, 6 and 8 | The agencies, the committee of series, the tiers, the memory of cases, the censors, the teachers, the lens families and planted lesions, and the split of what survives into input error, instrument, normal variant and pathology |
| 6 | layer 9; steps 7 and 9 | The emission and its tension with Law 7; measuring the substrate before anything is taught; judging each agency by its trajectory; the falsifiers, measured on the knee; the confident joint error; the build from the code that exists; the open questions |

A builder reads Parts 2–6 in order, with Part 6 §6.6 as the master sequence of the build. A reader checking
the no-ML law reads §1.9, then the specialists of Part 3 §3.3 and the memory of Part 5 §5.5, where a fitted
model would most easily be smuggled in. The founder's open decisions are gathered in Part 6 §6.7. Appendix A
maps every layer and mechanism to its sources and its build status, and Appendix B defines the terms.

## Part 2 — The laws and the lenses (recipe steps 1–3)

The recipe of *What an \<Object> Is* sets the architecture up for a domain in nine steps, each using only what
earlier steps make (THESIS §13.1). This Part works the first three for the knee: state the laws, name one lens
per term of the law, and read the priors as regime keys. Each law also carries its check on the output, which
is recipe step 5. The Part supersedes RECIPE §2–§3. It also adds three things those sections left implicit:
the knee's collapse (THESIS §3), the exclusion each lens writes, and the zones the lenses need from the atlas.
The founder set the task:

> "We just need to build the right set of laws and lenses in this domain, and "KneeDiff" […] and the
> λ-trajectory are just the first and most elegant of them, with that document I uploaded last time as
> a rich vein to mine for even more!" (founder, 2026-10-02)

Nothing here is a fitted model. The laws are stated, each lens is a fixed measurement with one open
quantity, and the priors are read off headers and cheap whole-knee readings. Registration is the one
bounded utility (THEORY Part IV, Law 3), and the data layer narrows and never decides (Law 4). The laws
serve every layer: Part 3 builds the signal-equation network on L2 (§2.3.2), and Part 4 builds the
exclusion lenses and the hardness map on the lens tables of §2.8.

### 2.1 What a law is, and what each law must yield

"By a **law** we mean a physical or biological regularity the system reasons from" (THESIS §2). Step 1
asks for "the regularities that make the picture, not regularities found in its pixels" (THESIS
§13.1). The knee has five laws: anatomy (L1), the MR signal (L2), acquisition (L3), radiology's laws
of pathology (L4) and injury mechanism (L5) (RECIPE §2; BRIEF §6). Each is given in four parts:
- a **statement**;
- its **consequences**: the losses and removals it licenses (H1's bridge, THESIS §1.4);
- its **lens terms**, one lens each (§2.8);
- its **checkable output**: a test on the output alone that supports a judgment and never
  establishes one (THESIS §2.6, §4.8, §13.1 step 5).

With these laws the knee meets the thesis's precondition (THESIS §1.3), as Part 1 §1.4 checks clause by
clause: its laws can be stated; its state is discrete, each structure one, and torn or not, and each finding
present or absent, with gold the nearest thing to the true answer (BRIEF §2); each lens is read against one
law term; reports teach and gold establishes (RECIPE §5); and each law has a check on the output.

**The stance: there is no noise** (Part 1 §1.7, where the founder's ruling is quoted in full). In the thesis a
removal is "a decision by a reading entitled to make it, kept as a record, never a discard", and "nothing is
discarded unexplained, and [...] a disagreement between correct readings is information" (THESIS §4.2). For
the founder, a lens that never resolves the signal is "a *perfect* lens for where your signal is *not*"
(founder, 2026-10-02). So every law below says what it explains away, and every lens says what it rules out
and where it is blind. Together the laws carry one accounting check (end of §2.6): every deviant voxel ends up
explained.

### 2.2 L1 — Anatomy: one knee, one of each, one structure per place

**Statement.** Every knee has the same structures in the same arrangement, one of each. After mm-true
registration with chirality made canonical, each voxel's normal intensity in a series type is a
distribution, and every voxel belongs to exactly one structure (RECIPE §2 L1; BRIEF §6).

**Consequences.**
1. *The platonic reference licenses normal variation.* True normals are squashed, voxel by voxel, into
   a mean and a spread, and the spread is the voxel's tolerance (THEORY II.2). Each voxel's deviation
   is z = (x − μ − trend) / max(σ, floor), and what survives is the deviation the reference does not
   license (THEORY II.3). **BUILT:** `src/RSNA_Knee/platonic_reference.py`
   (`build_reference`, `detrended_residual_map`) and `src/RSNA_Knee/kneediff.py` (`residual_z`,
   `classify_cell`).
2. *Structures are found for free.* The atlas places every always-present structure, so only
   lesion-objects are searched for, in the residual (RECIPE §1). Suppose the atlas places a structure
   and the data does not show it. Then it is either a finding (an ACL absent from the notch) or an input
   error (a misplaced zone, or a structure outside the field). The constraint reference (item 5)
   decides which.
3. *One knee shape.* The side comes from the sign of the image center's patient-x, with the Laterality
   tag as fallback, and left knees are mirrored to canonical-right. **BUILT:**
   `tools/register_and_export.py` (`derive_side`, `load_canonical_volume`), with 97.8% tag agreement
   (LADDER v5). Before v5 the reference squashed mirror-image knees together, so every pre-v5 number is
   dead (LADDER, substrate reset).
4. *Exclusive zones.* The label volume paints each voxel once, and the paint order is the precedence.
   The same code already confines the condyle search to a band from just below the joint line upward,
   since points far below it are "anatomically impossible" (**BUILT:** `src/RSNA_Knee/anatomy.py`,
   `build_zone_labels`).
5. *Two references, kept apart* (Part 1 §1.8 sets out the design in full). **Departure** from SYNTH
   Part IV, Layer 2. There, a large residual where the position is tightly constrained is an encoding
   error, corrected toward the template. A large residual at a variable position is a real variant, and
   is kept. KneeDiff reads tightness the other way. A large deviation where the *population* is tight is
   pathology, and the strongest kind (RECIPE §0: "Do not port the genomic reading of tightness"). So the
   knee keeps two references that are never merged (BRIEF §4):
   - the **population reference**, whose spread σ is what pathology is read against;
   - the **constraint reference**, against which input error is read. For L1 its reading is placement,
     the registration's agreement with the atlas: the NCC score (ZONES Rank 2, designed but not built)
     and the λ-trajectory's MONO_DOWN, settled by its placement margin (Part 4 §4.5).

   A deviation is read as pathology only where the constraint reference puts the voxel where the atlas
   says it is.
6. *Normal variants are L1 terms.* Small normal structures make signal that is not pathology:
   - the transverse meniscal ligament, at the anterior horn of the lateral meniscus;
   - the meniscofemoral ligaments and the popliteus hiatus, at its posterior horn. These are the classic
     pseudotears;
   - the physeal scar, a normal line across the closed growth plate;
   - red marrow.

   Each goes into the atlas (§2.10) or into a censor, so that its signal is explained (SYNTH Part II,
   Problem 3: "Real variants look like errors").

**Lens terms.** The population term is read by the Deviation lens, and the structure term by the
λ-trajectory lens (§2.8).

**Checkable output.**
- The zones partition the knee mask, one label per voxel.
- Each always-present structure yields exactly one record per study: a reading, or an abstention with
  its cause.
- No two committed lesion-objects hold one voxel (RECIPE §6).
- Each landmark lands within the registration's precision. Template-propagated knee landmarks have
  errors of 2.05 ± 1.30 mm, 92% of them within 4 mm (ZONES, Rationale). A landmark outside that is an
  input error.

**How it fails, and how that is measured.** The reference fails in two ways:
- *Too few normals.* σ estimated from few normals has t-tails: at n = 20, P(|z| > 3) is inflated about
  2.8× (VERDICT).
- *Mixed regimes.* These leave uniform-sign deviant patches over flat tissue. That diagnosis comes
  from LADDER v2, whose numbers are dead, though the diagnostic method survives.

Both are measured on held-out true normals, by the survival fraction and the peak masked window
density (`kneediff.survival_fraction`, `platonic_reference.max_masked_window_density`), and by the
make-or-break AUC (VERDICT). The first v5 readings: AUC 0.58 without detrending, and 0.66–0.68 with
the detrend scale in [16, 32] (LADDER, v5 first readings).

### 2.3 L2 — The MR signal: the instrument's physics

**Statement.** A voxel's intensity in a series is set by its tissue's proton density and by the
tissue's relaxation under the series' sequence. For spin echo with TR well above TE,

  S ≈ g · PD · (1 − e^(−TR/T1)) · e^(−TE/T2),

where g is the series' unknown receiver gain. Fat suppression removes fat's signal (BRIEF §5 layer 1).
TR, TE and TI are written in each series' header. The **signatures** of RECIPE §2 L2 follow:

*Table 2.3a. The signatures, derived from the signal equation.*

| Tissue | Fluid-sensitive, fat-suppressed | T1 | From the equation |
|---|---|---|---|
| Free fluid (effusion, cyst, fluid in a tear) | + | − | long T2 survives a long TE; long T1 barely recovers at a short TR |
| Fat (marrow, Hoffa's pad, subcutaneous) | − | + | short T1 recovers at a short TR; suppressed on FS |
| Fibrous (ligament, tendon, meniscus, cortex) | − | − | T2 too short to survive any TE |
| Marrow edema (contusion) | + (in bone) | − | water raises PD, T1 and T2 in fatty marrow |
| Hyaline cartilage | 0 | 0 | intermediate |

The fibrous row is the rule, and the normal ACL its known exception: it is striated, with intermediate signal
on PD and T1, most near its tibial insertion, and less dark than the PCL. So the ACL's fibrous signature is
read against the ACL's own population reference, never as an absolute dark digit (§2.8, lens 10).

**Consequences.**
1. *A finding is a zone together with a change of signature* (RECIPE §2). A meniscus turning + on FS
   holds fluid. Bone turning +,− holds edema.
2. *The contrasts are complementary banks,* each silent where another speaks (RECIPE §2; HDCSUB A.3).
   The cleaner pathway does the rejecting (SYNTH Part III, "Complementary Sparsity: Using the Cleaner
   Pathway"). In bone, T1 is the clean pathway. So T1-bright marrow rules out edema even where fat
   suppression is unreliable.
3. *Cross-contrast consistency is a check.* All the series covering a place must name one tissue
   change. A disagreement is either the instrument or a reason to abstain (SYNTH Part IV, Layer 0,
   where each bank "opens a door").
4. *Signs survive the unknown gain,* since each series is read against the reference for its own series
   type. Magnitudes need ratios (BRIEF §5 layer 1).
5. *The fat row depends on the sequence.* Fast spin-echo T2 leaves fat bright unless fat is suppressed.
   STIR suppresses by T1, so it nulls any tissue whose T1 is near fat's. The header says which row
   applies (§2.9).
6. *The law's unexplained part is information.* It is typed by the instrument terms that explain it,
   listed next.

**Lens terms.** Relaxation is read by the Signature lens; the magic angle and fat suppression by
their censor lenses (§2.8, lenses 3–5).

**The instrument's terms are law-given censors.** "A *law-given censor* is a law that forbids
outright, and it is absolute" (THESIS §7.5). Each term below removes *evidence*, never a finding. Each
also leaves a hardness mark where its lens is blind.

*Table 2.3b. The instrument's terms, as law-given censors.*

| Term | The law | What it censors | What it leaves blind |
|---|---|---|---|
| Magic angle | ordered collagen near 54.7° to B0 brightens on short TE | short-TE-only signal in fibrous tissue inside the window (§2.3.1) | short-TE tear evidence inside the window |
| Fat-suppression failure | spectral suppression fails where B0 is inhomogeneous (field edges, off-center, near metal) | FS-bright, T1-bright signal: unsuppressed fat, not edema or synovitis | edema and Hoffa readings there, unless T1 covers |
| Chemical shift | fat–water interfaces shift along the frequency-encoding axis | bands at the subchondral plate, which can be read as cartilage change or a line | the plate on the shifted side |
| Truncation | ringing runs parallel to sharp edges at coarse matrices | thin intrameniscal lines parallel to the surface | lines at the ringing period |
| Susceptibility | metal makes signal voids with bright rims | deviation around hardware | the hardware region (§2.9) |
| Motion | ghosts along the phase-encoding axis; shifts between series | duplicated edges; signatures assembled from misplaced places | the ghosted band; the shifted places |

#### 2.3.1 The magic angle, as a law-given censor

**The law.** In ordered collagen, the dipolar interaction that keeps T2 very short depends on
(3cos²θ − 1), where θ is the fibers' angle to the main field B0. Near θ = 54.7° this term vanishes, so T2
lengthens and the tissue brightens on short-TE sequences (T1, proton density, gradient echo). At long
TE the effect is gone (RECIPE §2: "Signal seen on short TE but absent on long TE, at that angle, is the
instrument, not a tear"). The classic knee site is the upsloping posterior horn of the lateral meniscus,
near its root (Peterfy et al. 1994).

**What it reads.**
- Each fibrous zone's local fiber direction from the atlas (a meniscus's circumferential direction, a
  ligament's centerline tangent), carried into the study's patient space.
- B0's direction for the study's magnet.
- Each covering series' TE class, from its header.

**What it computes.** θ at each fibrous voxel. Inside the window, it computes whether the deviant
signal is present on short TE and absent on long TE.

**What it emits.**
- *Inside the window:* a censor mark, so short-TE evidence cannot count for a tear. It also emits a
  hardness mark, since the short-TE lenses are blind to tears there. A tear inside the window must be
  shown by long-TE fluid or by shape (the bow tie, a displaced fragment).
- *Outside the window:* an exclusion of the instrument's explanation. Short-TE-only signal there stays
  as evidence of a tear or of degeneration, for the surface-contact lens to type.

The lens removes evidence, never a finding (THESIS §4.8).

**What licenses it.** L2 alone, absolutely, within its window (THESIS §7.5).

**How it fails.**
- *Wrong B0.* In a closed-bore magnet, B0 runs along the bore, the patient's S-I axis. A vertical-field
  open or extremity magnet puts B0 across the leg. B0's direction is a regime word (§2.9). Which
  magnet models are vertical-field is **OPEN**.
- *Wrong fiber direction.* The atlas direction reaches the study's patient space only through the
  study's own transform. `tools/register_and_export.py` discards that transform today (ZONES,
  Consequences; PRIORART §2, Recipe A, step 5). The canonical box is axis-aligned in patient space
  (`load_canonical_volume`), so its S-I axis is B0 before registration, but not after it. Keeping the
  transform is a build dependency of this lens.
- *Flexion.* Flexion changes θ, so it is read as a prior (§2.9).
- *No long-TE series.* Then the window is blind, and the lens says so.

**How the failure is measured.** The law predicts its own signature on true normals. Take the rate of
short-TE-only deviant signal in fibrous zones, binned by θ. It must peak near 55°. That one curve checks
the law, the fiber directions and the B0 assumption together, and a flat curve means one of them is
wrong. On gold, the tears that lie inside the window measure what the censor costs.

#### 2.3.2 L2 as the bridge to the signal-equation network (Part 3 §3.3)

The signature table is the ternary shadow of the equation. Given a series' TR, TE and TI, the sign of
the equation's response to a tissue change predicts the digit. Water entering fatty marrow raises PD, T1
and T2. That raises S on a long-TE fat-suppressed series and lowers it on a short-TR T1 series. This is
the edema row, derived rather than memorized. With about 5.5 series per study (BRIEF §2), each place is
one law observed several times.

The Signature lens (§2.8, lens 3) reads only signs. It needs co-registration and does not need g. Part 3 reads
magnitudes. It inverts the law at each place for quasi-quantitative PD, T1 and T2, as ratios. That
inversion gives four things:
- the reference can be squashed over tissue parameters rather than raw intensity (BRIEF §5 layer 2;
  Part 3 §3.4);
- a missing series can be imputed from the law (LAA §9, with the physics as the coherent replicate;
  Part 3 §3.3.6);
- the law's unexplained part can be read as the instrument's signature (Part 3 §3.3.8);
- uncertainty can be carried by the delta method (LAA §10; Part 3 §3.3.7).

This Part hands Part 3 five things:
- the law;
- the series inventory and headers (§2.9);
- the per-plane grids and cross-series correspondence (§2.4);
- the censors, as the law's known unexplained terms;
- the signature digits, which any inversion must reproduce. An inversion whose signs disagree with the
  Signature lens is a fact about the inversion.

**Departure** from LAA's wording. LAA casts its specialists as "vibing" coefficients. In LAA, "the
signal against which training is measured" is their composition, in the grey-box line of universal
differential equations and physics-informed networks (LAA §2, §5). The knee keeps LAA's structure but
not that wording. Each place's unknowns are solved from this study's observations by inverting a known
equation, the regime that "inverts a known law" (LAA §1). Nothing is fitted across a corpus (THESIS
§1.3; THEORY Part IV, Law 1). **Status:** no code reads TR, TE or TI yet (§2.9). The network is
**DESIGNED** in Part 3 §3.3. Whether it is feasible, given receiver gain, fast spin echo and fat
suppression, is **OPEN** (BRIEF §7; Part 3 §3.3.9).

### 2.4 L3 — Acquisition: the plane, the slice, and partial volume

**Statement.** Each series is sharp in its plane (sub-millimeter) and coarse between slices (about
3–4 mm). Each structure is read in the series whose plane suits the question asked of it (RECIPE §2 L3;
BRIEF §6):

*Table 2.4. The plane that reads each structure's question.*

| Structure | Question | Plane, and why |
|---|---|---|
| ACL, PCL | continuity; course | sagittal (oblique sagittal where the protocol tilts it): the long axis lies in the plane |
| Meniscal horns | surface contact | sagittal: the horn's section lies in the plane, and the horn runs along the slice axis |
| Meniscal bodies | surface contact; extrusion | coronal: the same, for the body |
| MCL | continuity; fluid around the band | coronal: its thin dimension and its long axis both lie in the plane (axial shows its section) |
| LCL (not scored; read for L1's completeness, **DESIGNED** addition) | continuity | coronal, on the posterior slices: its long axis, from the lateral femoral epicondyle to the fibular head, lies near the plane |
| Tibiofemoral gap, cartilage | gap; plate integrity | coronal (sagittal for the posterior condyles) |
| Patellofemoral joint | cartilage; margins | axial (sagittal corroborates) |
| Baker's cyst | the neck between the medial gastrocnemius and semimembranosus tendons | axial, with sagittal for extent (**DESIGNED** addition) |
| Suprapatellar recess, Hoffa's pad | volume; signal share | sagittal (axial corroborates) |

**Consequences.**
1. *Two rules of orientation, one per kind of question.* A *continuity* question is read with the
   structure's long axis in the plane. A *cross-section* question is read with the long axis along the
   slice axis, so that the structure's section lies in the plane. Both are "the thesis's "each lens at
   its own sharpest depth," moved from depth to plane" (RECIPE §2 L3).
2. *Partial volume is what the coarse axis loses.* A structure thinner than the slice, or oblique to it,
   is averaged with its neighbors. Deviation at such an edge is the instrument. It belongs to the
   hardness map, not to the residual (BRIEF §5 layer 3; Part 4 §4.2).
3. *Counts are in slices, but the laws are in millimeters.* A lesion of extent e along the slice axis
   appears on at most about e/spacing + 1 slices. So every slice-count law is read with the header's
   spacing (SliceThickness, SpacingBetweenSlices) beside it.
4. *Each plane needs its own grid.* The v5 grid is the sagittal squint: 32 samples over 110 mm
   medial–lateral (3.4 mm), and 224 samples over 150 mm on each in-plane axis (0.67 mm). **BUILT:**
   `tools/register_and_export.py` (`CANON_SHAPE`, `CANON_FOV_MM`), with the axis semantics in
   `src/RSNA_Knee/anatomy.py`. A coronal series resampled into this grid would lose its fine
   medial–lateral sampling. So the coronal grid is coarse anterior–posterior, and the axial grid coarse
   superior–inferior, over the same physical box (**DESIGNED**; RECIPE §10).
5. *Cross-series correspondence is tag arithmetic.* A study's series normally share a DICOM frame of
   reference (FrameOfReferenceUID). So a place in one series is a place in another, up to patient motion
   between series. **DESIGNED:** each study is registered once. The registration is computed on one
   series and carried to the rest through the shared frame. Each series is then resampled onto its own
   plane's grid. The v5 loader centers each series' box on that series' own center
   (`load_canonical_volume`), so a study's series must first be given one shared center.
6. *The knee is scanned supine and unloaded.* The gap on MRI understates the narrowing a weight-bearing
   radiograph would show. So a normal gap rules out nothing (§2.8, lens 18).
7. *Independent views are different evidence.* Two lenses on one series are one voice, while sagittal
   and coronal, or FS and T1, are two. "Independence must come from different evidence, not different
   encodings" (RECIPE §7; HDCSUB F.4 #4). Today every concurrence has one voice, since the build reads
   one series per study (BRIEF §4; `tools/fetch_labeled_studies.py`, `pick_series`).

**Lens terms.** The plane is read by the Coverage lens (§2.8, lens 6).

**Checkable output.**
- *One lesion, one place.* A lesion committed on sagittal lands at the same patient-space place on
  coronal and axial, wherever they cover it, within the correspondence radius (the Signature lens's
  open quantity, §2.8). In RECIPE §6's words, this is "the knee's sandwich: two views in place of two anchors".
- *Extent agrees* across planes, within one slice spacing.
- *Provenance.* Each structure's reading names the plane that read it.

**How it fails, and how that is measured.**
- *Motion between series* breaks correspondence. It is measured per study as landmark disagreement
  between series (NCC per series, designed in ZONES Rank 2 but not built).
- *A mislabeled or oblique protocol* is found by comparing the `train_series.csv` plane flag with
  ImageOrientationPatient.

### 2.5 L4 — Pathology: radiology's own laws

**Statement.** Each finding has a defined appearance in a defined place. Each also has a near miss
that differs from it in one nameable respect (THESIS §7.6; RECIPE §2 L4; BRIEF §6).

*Table 2.5. The pathology law per finding, with its near miss.*

| Finding | Law term | Plane · zone | Near miss, and the one difference |
|---|---|---|---|
| Medial, Lateral Meniscus | signal reaching an articular surface on ≥ 2 slices (the two-slice-touch rule, De Smet and Tuite 2006), or abnormal shape (no bow tie; a displaced fragment) | horns sagittal, bodies coronal · meniscal zones (to add) | degeneration: intrasubstance signal that does not reach a surface. The difference is surface contact. Whether degeneration is a negative or a second positive is Q3 |
| ACL | fibers broken; fluid in the band; a course flatter than the intercondylar roof (Blumensaat's line) | sagittal · ACL tube, roof line (to add) | mucoid degeneration: signal without a break or a change of course |
| MCL | fluid around an intact band (sprain); the band thickened, interrupted or absent (tear) | coronal · MCL band and shell (to add) | bursal fluid: it lies beside the band, not around it |
| Effusion | recesses distended by fluid, the suprapatellar first | sagittal, axial · zone 4; posterior recesses (to add) | physiological fluid: a volume within the normal spread |
| Synovitis | without contrast: FS-bright signal in Hoffa's pad, and effusion-synovitis (the MOAKS surrogates; Hunter et al. 2011) | sagittal, axial · Hoffa's pad (to add) | the pad's normal clefts and vessels: thin, tubular, in known places |
| Baker's | fluid in the gastrocnemio-semimembranosus bursa, with a neck to the joint between the medial gastrocnemius and semimembranosus tendons | axial · zone 5, split; tendon zones (to add) | a parameniscal cyst or ganglion: there is no neck. A parameniscal cyst also points to a tear |
| Contusion | geographic edema-signature marrow, often subchondral | all planes · bone subregions (to add) | red marrow: T1 brighter than muscle. An OA marrow lesion: under cartilage loss, in a narrowed compartment |
| Fracture | a dark line inside edema, reaching cortex | sagittal, coronal · committed edema | the physeal scar: a line without edema |
| Medial, Lateral, PF OA | by compartment: cartilage loss, narrowing, marginal osteophytes, subchondral marrow lesions, meniscal extrusion (MOAKS subregions) | coronal; axial for PF · zones 6, 7, 2; plates (to add) | one sign alone: OA's signs co-locate (L5) |

**Consequences.**
1. Each term becomes a lens (§2.8). Each near miss, once an independent signal confirms it, becomes a censor
   carrying its named difference (Part 5 §5.6, Table 5.11). The surface-contact digit that separates a tear
   from intrasubstance signal is the textbook case (THESIS §7.6; RECIPE §8).
2. **DESIGNED,** toward Q1: cartilage loss and meniscal extrusion are both in RECIPE §2 L4, but neither
   had a lens. Three more terms are added here: the bow-tie count, the Baker's neck read on axial, and
   the physeal scar. The physeal scar makes "a fracture lies within edema" a censor.
3. Some terms couple to L3. A normal meniscal body shows its continuous bow-tie shape on two contiguous
   sagittal slices at 4–5 mm (Helms et al. 1998). At this dataset's 3–4 mm, the expected count is
   measured on true normals for each spacing.
4. The competition's label definitions fix which near misses are negatives. Four of them are **OPEN**
   (Q3, extended): the meniscus (tear, or tear and degeneration), the MCL (sprain, or tear only),
   Contusion (whether OA marrow lesions count) and Baker's (from what size).

**Lens terms.** One lens per term: lenses 7–19 (§2.8).

**Checkable output: each object is well formed** (RECIPE §6).
- A tear is thin and touches a surface.
- Edema is geographic and lies inside bone.
- A fracture line lies inside edema and reaches cortex.
- A cyst is rounded and has its neck.
- An effusion lies in the recesses.
- Hoffa's signal lies inside the pad.

An object that fails its shape law is not committed as that finding. It stays in the residual for the
next round (the loop, layer 6; Part 4 §4.4).

### 2.6 L5 — Mechanism: how events co-occur

**Statement.** An injury writes a pattern across structures (RECIPE §2 L5; BRIEF §6):

*Table 2.6. The mechanism patterns.*

| Mechanism | Pattern |
|---|---|
| Pivot shift | ACL tear; contusions of the lateral femoral condyle and the posterolateral tibial plateau |
| Valgus | MCL injury; lateral-compartment contusion |
| Lateral patellar dislocation | contusions of the medial patella and the lateral femoral condyle |
| Dashboard | anterior tibial contusion; PCL injury |
| Hyperextension (**DESIGNED** addition) | contusions of the anterior femoral condyle and the anterior tibial plateau; ACL or PCL |
| OA | its signs co-locate in one compartment |

**Consequences.** L5 is read on the record of committed objects, not on pixels, so it has no pixel lens.
It is concurrence between independent questions. A PEAK_DROP on the ACL and contusions in the pivot-shift
pattern corroborate each other, and each is still established only by its own oracle (RECIPE §5). L5
supports only (RECIPE §2 L5: "supporting only, §6"; RECIPE §6: "All of these support a judgment; none
establishes one"), and like RECIPE §5's every-finding agency it "supports and never trims". A pattern with a
missing member opens a site search where that member should be (Part 4 §4.4). Nothing committed is removed to
complete or break a pattern.

L5 also excludes. Take a subchondral edema-signature in a narrowed compartment with marginal
osteophytes. It fits no injury pattern, and it fits OA's compartment law. That is what separates a
contusion from an OA marrow lesion. The mechanism sites must therefore exist as named marrow subregions
(§2.10).

**Checkable output: events keep the rules** (THESIS §13.1 step 5; RECIPE §6).
- Every committed contusion belongs to a pattern or to OA's compartment, or else is flagged as
  unexplained.
- Every fracture lies within edema.
- OA's signs co-locate.

**How it fails, and how that is measured.** A real injury can lack its pattern, so L5 never decides.
**DESIGNED:** the patterns are measured on text, independently of the pixels, as the co-occurrence of
findings and locations in the parsed reports. The parser is **BUILT** (`src/RSNA_Knee/report_parser.py`);
location extraction is **DESIGNED** (RECIPE §5, "Localized calls").

**The accounting check, over all five laws.** Every voxel the Deviation lens finds deviant is
explained, in the end, by exactly one of four causes:
- a committed lesion-object (L4);
- the instrument (L2's censors);
- a normal variant (L1);
- an input error (the constraint reference: L1's placement, or L3's correspondence).

Otherwise it stands inside an open question the structure hands on, typed by how it arose. In THESIS
§1.4 (H1's bridge), the residue is the questions left open, never the residual data. Three of the four
causes are SYNTH's three-way distinction (SYNTH Part II): its encoding error is the knee's instrument,
its real variant the knee's normal variant, and its input error the knee's input error. Pathology is
the knee's fourth cause. The check is also the emptied box written as a law check (RECIPE §6; THESIS
§4.7). Part 5 §5.9 makes the four causes the society's split, each read on its own reference.

### 2.7 The knee's collapse: plane per structure, and the squint

The collapse is H1's first move: stop rereading what the laws hold nearly constant (THESIS §3).

**The warrant** (THESIS §3.1). For cells, a nucleus's depth barely changes, so "the collapse makes
several flat pictures, each at its own depth, never one". A knee structure barely changes along its own
long axis over a few millimeters: a ligament along its fibers, a meniscus along its circumference. So
the coarse slice axis may lie along that direction, or the long axis may lie in the plane, by L3's two
rules. No one plane suits every structure, so the knee is read in several planes, never one.
**Departure:** for cells the system chooses the depths. For the knee the protocol has already chosen
the planes. The system chooses which plane reads which question, and the Coverage lens (§2.8) measures
what each plane can see.

**Planes as lenses at their own depth** (THESIS §3.2): "Lenses at about one depth read one plane two
ways, and each corrects the other's borders; lenses at different depths are the three-dimensional
structure itself." In the knee, two contrasts in one plane read that plane two ways (the signature, L2).
Two planes are the three-dimensional knee itself (L3's one lesion, one place).

**The composite, with the plane kept as a number** (THESIS §3.3). **DESIGNED:** in the study's patient
space, each place is shown from the series whose plane best reads its zone's question, and that series
is kept as a number. The composite catches deviation that no single plane draws as a body, such as a
lesion oblique to every plane. Like the cells' composite, "it never pulls a cell and never decides alone:
it points". Here it points to sites for the site search (layer 6; Part 4 §4.4).

**No time** (THESIS §3.4). A static study has no anchors. The anchors' test, "A truth that survives a
small step either way is real", moves to small registration jitters and mild codebook shifts (BRIEF §5
layer 5; Part 4 §4.3). Under the exact ledger a codebook shift becomes a shift of the quantizer's edges
(Part 3 §3.5.3).

**The squint** (THESIS §3.5). The questions are categorical, and the metric rewards order alone:

> "The project here...is meant to resolve "is knee" or "sad knee". MUCH more forgiving." (founder,
> 2026-10-02)

So each voxel is read as a digit against its own normal, and each zone as a few counts. The protocol's
slice spacing is itself a squint, licensed wherever a structure is invariant along the slice axis. "No
reduction adds information to the data; it removes, faster than the answer, the variation the answer
would otherwise have to see through" (THESIS §3.5). How coarse a view may be is measured on a precision
ladder (THESIS §12.4). **DESIGNED** for the knee, the ladder has four rungs:
1. DICOM integers;
2. the N4-corrected, normalized float (`n4_correct`, `normalize_intensity`, BUILT);
3. z;
4. the digit.

Each rung is measured before use against the make-or-break instrument and against phantoms. Part 3
§3.5.5 (Table 3.8) amends the ladder for physics space, where the normalized-float rung survives only on
the degraded path.
**Departure:** the squint is not "vibe collapse" (TIERED §2.3). Vibe collapse's own committed results
refute it (HDCSUB F.4 #1).

**What is removed, and what is kept** (THESIS §3.6). The black is the knee's stage 1/2, which "resolves
away the "background" cleanly" (founder, 2026-10-02; quoted in full in Part 1 §1.5, and built in Part 3
§3.4.3). As in the thesis, the black deletes nothing. Licensed voxels stay for any lens that reads raw data
(RECIPE §0), and the share cleared is measured. The pre-v5 figure of ≥ 96% is dead (LADDER, substrate
reset), and v5's share has yet to be measured. Reading by exclusion completes the collapse: "a reading
that is poor at finding a signal can be reliable at saying where the signal is not" (THESIS §3.6).

### 2.8 The lenses, one per law term (recipe step 2)

**Rules every lens keeps.**
1. **One thing, and no question.** A lens is "a cheap, deliberately lossy view that measures one thing
   and knows no question" (THESIS §3.2). Only the commit reads a lens as for or against (THESIS §4.5).
   **Departure** from RECIPE §3, in two places. Its Course lens measured two things, so it is split into
   Continuity and Angle. Its Plane lens measured only "where in the study to read the structure", with "the
   plane, given by anatomy" as its open quantity: a routing fixed by anatomy rather than a measurement, so it
   becomes the Coverage lens.
2. **One open quantity,** "chosen from a few physically sane values" (THESIS §13.1 step 2). This rule
   fixes each law lens's default value. Where several values are sane, the choice is measured: by the rate
   of "for" readings on held-out true normals, at a fixed detection rate of planted phantoms. The value is
   never chosen to separate gold cases, just as the static middle is "never chosen to separate confirmed
   cases" (THESIS §6.2). LENS Phases 1–3 discover lens *families*. That is the society's work (layer 8; Part
   5 §5.8), not the open quantity of a law lens: a family is a separate frozen configuration, chosen by
   aggregate prevalence matching, the count's analog (THESIS §10.1), and then validated on phantoms and
   gold. It never moves a lens's default.
3. **Silence is not zero.** "A reading never made is not a low reading" (THESIS §6.3), and "at the
   middle" is a written row (THESIS §6.2). **Departure** in BUILT code:
   - `src/RSNA_Knee/hdc_encoder.py` (`ternary_cell`) writes the licensed voxel as 0, and the encoder
     drops every 0;
   - `tools/lens_eval2.py` also writes off-mask voxels as 0.

   So "licensed here" and "never read" are one symbol there. The licensed 0 is the Deviation lens's
   exclusion mark, and it must be written (the encoding, layer 4; Part 3 §3.5.3).
4. **A declared direction.** "A narrow reading may count one way only" (THESIS §4.5). Each lens
   declares whether it counts for, against or both (Table 2.8b).
5. **Exclusion marks.** A lens that may count against writes not-here marks. They divide each zone into
   excluded, unexcluded and unreadable parts. Findings are sought where the exclusions run out, and a
   lawful exclusion changes what the rest means (THESIS §4.6, the Monty Hall move; Part 4 §4.1).
6. **What every lens emits:**
   - its value;
   - its digit against a static middle, set once on the residual cells of the teaching studies (THESIS
     §6.2; RECIPE §4);
   - its not-here marks;
   - its silences, each with a cause;
   - the series, plane and contrast it read (RECIPE §7).
7. **Common silences.** Any lens falls silent where:
   - its series is absent;
   - the Coverage lens gives its zone too few slices;
   - the registration gate fails for its zone (NCC, ZONES Rank 2; MONO_DOWN with a registration alarm on the
     anchoring structure, Part 4 §4.5);
   - a law-given censor has removed its evidence.
8. **How every lens's failure is measured.** Three instruments do it:
   - *held-out true normals,* where any "for" reading is false, mapped by zone. LADDER lists 50 normals
     in the reference, 30 held out, and 799 parser-harvested candidates;
   - *synthetic lesion phantoms,* planted in true normals with known signature, size and slice count.
     These are the knee's version of LENS Phase 4's edge cases and of VERDICT's amplitude response curve;
   - *gold* (58 studies).

*Table 2.8a. What each lens reads and measures.*

| # | Lens | Law | Reads: series · plane · zone | Measures (one thing) | Open quantity | Status |
|---|---|---|---|---|---|---|
| 1 | Deviation | L1 population | every series and zone: each voxel against its series type's reference, in its regime | z = (x − μ − trend) / max(σ, floor), as a digit | z threshold {2.5, 3, 3.5}; 3 in use | BUILT: `kneediff.residual_z`, `classify_cell`; `platonic_reference.detrended_residual_map`; `hdc_encoder.ternary_cell` |
| 2 | λ-trajectory | L1 structure | each always-present structure's zone, in its plane | the shape of identity(λ) × fidelity(λ) as the zone is blended toward its reference, x(λ) = (1 − λ)x + λμ | the λ grid {0, 0.2, …, 1} (LENS Phase 5) | DESIGNED (layer 7; Part 4 §4.5) |
| 3 | Signature | L2 relaxation | one patient-space place, across all co-registered series | the pattern of contrast digits, named by the equation's signs for each series' TR, TE and TI | correspondence radius {½, 1} × the coarser series' slice spacing | DESIGNED |
| 4 | Magic angle | L2 censor | fibrous zones; fiber direction; B0; TE class | θ, the fiber's angle to B0 | window {±10°, ±15°} about 54.7° | DESIGNED |
| 5 | Fat suppression | L2 censor | the FS series, with T1, in fat zones (marrow, Hoffa's pad, subcutaneous) | the share of fat voxels left FS-bright and T1-bright | none | DESIGNED |
| 6 | Coverage | L3 | each series' geometry, against each structure's zone and question axis | effective slices: those crossing the zone with the question's axis within tolerance (in the plane for continuity; along the slice normal for cross-section) | obliquity tolerance {15°, 30°} | DESIGNED; plane-flag routing BUILT (`pick_series`) |
| 7 | Surface contact | L4 meniscal tear | meniscal horns (sagittal), bodies (coronal) | slices on which a deviant component inside the dark meniscus touches its femoral or tibial surface (not the capsular side) | minimum slices 2 (De Smet and Tuite 2006); 1 is kept as "possible" | DESIGNED |
| 8 | Bow tie | L4 meniscal shape | meniscal bodies, sagittal | contiguous slices on which the body is one band joining the horns | none: the expected count is measured per spacing | DESIGNED |
| 9 | Extrusion | L4 OA and meniscus | coronal mid-body: the body and the tibial margin | mm of meniscus beyond the plateau margin | none | DESIGNED |
| 10 | Continuity | L4 ligament | ACL and PCL tubes (sagittal); MCL band (coronal); LCL band (coronal; not scored) | the longest run along the centerline without fibrous signature, each sample read against the ligament's own population reference, never an absolute dark digit (the normal ACL is striated, with intermediate signal) | sampling step {0.5, 1} mm | DESIGNED |
| 11 | Angle | L4 ACL course | the ACL band (from lens 10); the roof line; sagittal | the angle between the band's principal axis and the roof line | the segment: {distal half, whole band} | DESIGNED |
| 12 | Recess volume | L4 fluid | suprapatellar (4), posterior recesses, gutters, MCL shell | fluid-signature volume per recess (mm³) | none | DESIGNED; zone 4 BUILT |
| 13 | Neck | L4 Baker's | axial: the posteromedial popliteal region and two tendon zones | whether a fluid path joins the collection to the joint between the tendons | none | DESIGNED |
| 14 | Marrow | L4 marrow | bones (8–10), by subregion | edema-signature extent, with depth kept beside it | minimum extent {3, 5} mm | DESIGNED |
| 15 | Line | L4 fracture | committed edema, with its halo out (layer 6; Part 4 §4.4); T1, FS | the length of a linear dark component reaching cortex | minimum length {3, 5} mm | DESIGNED |
| 16 | Fat pad | L4 synovitis | Hoffa's pad; FS, sagittal and axial | the FS-bright share of normally dark fat | none | DESIGNED |
| 17 | Cartilage | L4 OA | plates by MOAKS subregion; fluid-sensitive series | the share of the plate where cartilage gives way to fluid or bone | shell depth {2, 3} mm | DESIGNED |
| 18 | Gap | L4 OA | compartments (6, 7); bone masks; coronal | the femur–tibia distance per compartment (median, with the minimum beside it) | none | `anatomy.joint_line` BUILT (one median midpoint); per compartment DESIGNED (ZONES item 3) |
| 19 | Margin | L4 OA | compartment and patellar margins | bone-signature volume beyond the reference bone surface | none | DESIGNED |

L5 has no pixel lens (§2.6).

*Table 2.8b. How each lens counts, what it rules out, when it falls silent, and how it fails.*

| # | Counts | Rules out ("not here") | Also silent when | Fails by · measured by |
|---|---|---|---|---|
| 1 | both | digit 0: no lesion at this voxel, in this series | the regime's reference has too few normals | misregistered edges; t-tails (VERDICT); mixed regimes · survival and peak masked density on true normals; make-or-break AUC |
| 2 | both | MONO_UP: the structure is normal, as read. MONO_DOWN: it may not be where the atlas puts it (routed to the constraint reference, where the placement margin decides: Part 4 §4.5) | AMBIGUOUS: kept as a word, never a vote | no peak without a nonlinearity (BRIEF §4; Q2); hand-set shape thresholds (±0.02, drop > 0.1: SYNTH Part IV, Layer 3) · shapes on true normals (E10 measured 62% AMBIGUOUS where SYNTH Part VIII expected 95% MONO_UP: HDCSUB F.2); phantoms should give PEAK_DROP; misregistration beyond δ: m < 0 and the alarm |
| 3 | both; T1-bright in bone counts only against edema | what its signs contradict: FS-dark is not fluid; T1-bright marrow is not edema | fewer than two contrasts cover the place; a partial-volume edge | motion between series; failed suppression; no T1 · cross-series landmark disagreement; edema rate in bone on true normals; phantoms |
| 4 | censor | outside the window: the instrument's explanation | no fiber direction; B0 unknown | wrong B0; discarded transform; flexion; no long TE · θ-binned rate on true normals (a peak at 55°); gold tears inside the window |
| 5 | censor | edema and Hoffa signal where FS brightness is unsuppressed fat | no T1 (then a regional word only) | real edema in a failed region is masked · map of unsuppressed fat on true normals, by regime |
| 6 | neither: it licenses speech and silence | a series as witness for a structure (its silence there is not absence) | geometry tags missing | mislabeled oblique protocols; motion · plane flag against ImageOrientationPatient; phantoms at known obliquity |
| 7 | both | a tear: in a segment dark on every covering slice, or where intrasubstance signal makes no contact (degeneration is not excluded: Q3) | fewer than 2 covering slices; the meniscus–capsule junction; the magic-angle censor | pseudotears; truncation; partial volume at the surface · false contact on true normals by subregion (the hardness map); phantoms at known slice counts; gold |
| 8 | for, when fewer than expected | a displaced bucket-handle fragment | body not covered sagittally | small menisci; spacing · counts on true normals per spacing |
| 9 | for | extrusion, where the edge lies within the margin | an osteophyte blurs the margin (defer to lens 19) | osteophytes; rotation · true normals; gold OA |
| 10 | both | a complete tear, where the band is whole; a partial tear, in uniformly fibrous segments | the ACL's femoral attachment on sagittal, partial-volumed with the lateral condyle: read coronal | mucoid degeneration; grafts; oblique partial volume; normal striation, the ACL's intermediate signal near its tibial insertion · false gaps on true normals; planted gaps |
| 11 | for only | nothing on its own | no band to measure; flexion outside the prior's range | flexion; a mis-traced roof · angles on true normals, by flexion word |
| 12 | both | effusion, where every recess is empty | a recess cut off by the field (lens 6) | physiological fluid; truncation by the field · volumes on true normals; gold Effusion |
| 13 | both | Baker's, for a collection with no neck | no axial series | a neck thinner than a slice; rupture · gold Baker's; the normal bursal volume (OPEN) |
| 14 | both | edema, where marrow is T1-bright | suppression failed (lens 5) and no T1 | red marrow; OA marrow lesions; post-surgical marrow · rate on true normals by subregion; phantoms; gold Contusion |
| 15 | for only (an unseen line in dense edema at 3–4 mm is not "no fracture") | nothing on its own; "a fracture lies within edema" censors lines outside edema | no committed edema | physeal scar; vessels; chemical shift · lines on true normals (all must be censored); phantoms; gold Fracture |
| 16 | both | Hoffa-synovitis, where the pad is uniformly dark | suppression failed at the pad | clefts and vessels; arthroscopy portals; impingement · shares on true normals; gold Synovitis |
| 17 | both | cartilage loss, where the plate is intact | no fluid outlines the surface; oblique cuts of curved surfaces | partial volume; chemical shift; magic-angle lamination · true normals by subregion; gold OA |
| 18 | for only (supine and unloaded: L3) | nothing on its own | bone masks fail | flexion, varus or valgus in the coil · per-compartment distribution on true normals |
| 19 | both | osteophytes (not OA), where margins are smooth | the bone is MONO_DOWN | partial volume at curved margins; warps (the B-spline mesh is kept coarse so that lesion-scale outgrowth survives: LADDER, standing findings) · true normals; gold OA |

The brief's four exclusions (BRIEF §5 layer 3) are rows of this table:
- T1-bright marrow excludes edema (lenses 3, 14);
- a continuous dark band excludes a tear (lens 10);
- an empty recess excludes effusion (lens 12);
- a short-T2 meniscus without surface contact excludes a tear (lens 7).

**What the silences build.** Some views go blank even in health: at the meniscus–capsule junction, at
partial-volume edges, in the magic-angle window, at the pseudotear sites. There, a lens that never
resolves the signal is "a *perfect* lens for where your signal is *not*" (founder, 2026-10-02). Collected
over true normals, the silences and false readings form the **hardness map** (BRIEF §5 layer 3). Two
GenomeVault findings are read here the way the founder reads them, as structural signal:
- COMMITTEE §4.2's joint-error clustering: 2 joint errors where 0.00006 were expected, a ratio of
  36,210×;
- TIERED §3.1.1's finding that margin-0 errors are predictable.

The hardness map is built in Part 4 §4.2 (layer 3).

### 2.9 Priors and regime keys (recipe step 3)

The recipe: "The priors, cheap readings of the whole field taken once, point and never decide alone.
Their words key every case, since a quantity means one thing within a regime and another across
regimes" (THESIS §13.1 step 3; §4.1). LAA says the same: "the regime must be part of the key before the
law's unknowns are read off the memory" (LAA §8). For the founder, the headers
"are cheap signals, not defining elements", there for the equivalent of "CMD-F" (founder, 2026-10-02);
and in his earlier ruling of 2026-09-21, "The header is "metadata", not a verdict on meaning" (HDCSUB
F.0). Both rulings are quoted in full in Part 3 §3.2.1, which builds the header.

**Header priors: per series, and exact by definition.**

*Table 2.9. The header words.*

| Word | Source | What it keys | Status |
|---|---|---|---|
| plane | ImageOrientationPatient; the Anatomical_Plane flag | L3 routing; the grid | flag BUILT (`pick_series`); orientation used for slice order, resampling and side (`load_series_volume`, `load_canonical_volume`, `derive_side`), not kept as a word |
| contrast family | RepetitionTime, EchoTime, InversionTime, ScanningSequence, SequenceVariant, EchoTrainLength; the Fluid_Sensitive flag | which equation term dominates (L2; Part 3 §3.3.3); short or long TE (lens 4) | tags unread; flag BUILT |
| fat suppression | ScanOptions (vendor-specific); STIR, by inversion time; the Fat_Suppression flag | which tissue is dark by design; how suppression fails | flag BUILT |
| field, vendor | MagneticFieldStrength, Manufacturer, ManufacturerModelName | the reference regime; B0's direction (lens 4) | unread |
| geometry | PixelSpacing, SliceThickness, SpacingBetweenSlices | slice counts in mm (L3, L4) | used inside resampling, but not kept as a word |
| side | ImagePositionPatient and ImageOrientationPatient; Laterality | chirality | BUILT (`derive_side`) |
| frame | FrameOfReferenceUID | cross-series correspondence (L3) | unread |
| inventory | the study's set of (plane, contrast, suppression) | which lenses can speak; which series Part 3 §3.3.6 imputes | flags BUILT, used only to pick one series |

Which tags survive the competition's anonymization is **OPEN**, and is the first thing measured. An
absent tag writes the word "unknown", never a guess.

**Field priors: per study, cheap readings of the whole knee (DESIGNED).** The thesis reads a plate's
density, its distribution ("even, spiky or one-sided"), its depth profile and its drift (THESIS §4.1).
The knee reads:
- *coverage:* the knee mask's share of the box, and whether the suprapatellar recess and the MCL band
  lie inside the field (`knee_mask`, BUILT);
- *placement:* the landmark NCC (ZONES Rank 2, not built), and the deformation the B-spline needed
  (computed in `register_full`, but discarded);
- *the residual's distribution:* the survival fraction (`kneediff.survival_fraction`, BUILT) and its
  shape. An *even* residual means a regime mismatch (LADDER v2). A *one-sided* residual means a smooth
  field across the box. A *spiky* residual means local deviation, which is the case for lesions;
- *fluid share* (BRIEF §5 layer 0);
- *marrow regime:* T1 marrow brightness against muscle, red or yellow, read from the image rather than
  from demographic tags;
- *positioning:* flexion and rotation, from the femoral and tibial bone axes. These key the Angle lens
  and θ;
- *hardware:* susceptibility voids, under which the local lenses fall silent.

**The regime key and the references.** These words form the key every case is kept under (THESIS §4.1;
LAA §6). A coarse subset of them also stratifies the platonic reference: plane, contrast family,
suppression, field strength, perhaps vendor. That gives one reference per series type per regime,
squashed only from that regime's true normals, block-diagonally "with strict no-contamination" (LAA §8).
LADDER's "Levers still in reserve" already names regime stratification as "usable at the reference level
as per-regime references".

**Departure** from LAA §8. Of LAA §8's three stratified-regression designs, all fitted (LAA §2: the unknowns
are "fit and recalled *block-diagonally*"), the knee keeps only the block-diagonal partition: boundaries
"known and sharp", which the headers supply, with "strict no-contamination". It replaces the per-block
regression with per-regime references (median, MAD; Part 3 §3.4.2) and medians over individual cases taken at
read time (Part 3 §3.3.5), so nothing is fitted (THEORY Part IV, Law 1). Spatially clustered regression and a
mixture-of-experts gate are dropped because they also learn the partition.

The key's grain is measured, not chosen. A cell of the key with too few true normals gives t-tailed σ
(VERDICT), so it falls back to its parent key: field, then vendor, then sequence. A split that leaves the
reference's per-voxel distributions unchanged is merged. Static middles do not move with the regime;
the regime enters only through the reference and the key (THESIS §6.2; RECIPE §4).

**What a prior may do, and how it fails.** A prior points: to a reference, to the lenses that can speak,
to a plane, to the cases recall searches. It never decides a finding (THESIS §4.1; THEORY Part IV, Law
4). And "a header that disagrees with a body is a fact about the header, recorded, never an override"
(HDCSUB F.5).

Aggregates written later on a structure's vector are headers too: the deviant count, the fluid share, the
trajectory's shape and λ* (Part 4 §4.5), after E10's trajectory byte and its λ_opt (HDCSUB F.2; SYNTH Part
VIII). They let Tier 0 skip a quiet zone (TIERED §1.2; Part 3 §3.2.5; Part 5 §5.4), and they make the store
searchable by Cmd-F. Their routing saving must be measured here, in work counted per study (Part 3 §3.2.6),
since E10's speed-up was not delivered (HDCSUB F.2).

A prior fails in three ways: by absence, by aliasing (two protocols under one word), or by
over-splitting. These are measured by tag survival, by the false survival rate per regime on held-out
true normals, and by a make-or-break run per regime.

### 2.10 Zones the laws need from the atlas

**BUILT.** A template-space label volume, derived from the template's bone geometry and indexed
directly by every registered study (ZONES items 2–3; `src/RSNA_Knee/anatomy.py`; `tools/build_atlas.py`).
Voxels are the sagittal grid's: 0.67 mm in the plane, 3.4 mm medial–lateral.

*Table 2.10a. The built zones (`ZONE_NAMES`).*

| Id | `ZONE_NAMES` | Derived from |
|---|---|---|
| 1 | joint_line_slab | ±15 voxels of the joint line; never painted, since the slab goes to zones 6 and 7 |
| 2 | retropatellar | a 15-voxel slab behind the patella |
| 3 | intercondylar_notch | ±3 medial–lateral samples of the notch saddle, ±25 voxels of the joint line |
| 4 | suprapatellar_recess | above the patella's superior pole, in front of the femur |
| 5 | popliteal | behind the femur, within ±40 voxels of the joint line |
| 6, 7 | medial, lateral compartment | the slab, split at the notch |
| 8–10 | femur, tibia, patella bone | dark marrow components (fat-suppressed polarity), grouped by centroid |
| 11 | other_knee_tissue | the rest of the body mask |

The landmarks behind these zones:
- the joint line is the median midpoint of the femur's inferior edge and the tibia's superior edge
  (`joint_line`);
- the condyles and the notch come from the distal femur's height field (`condyles_and_notch`);
- bone grouping raises an error rather than fabricate a split (`classify_bone_groups`).

The one human artifact is the eye-check of the template bone masks. The template is a single study,
which is a known bias (ZONES items 3 and 5).

**DESIGNED: zones to add** (RECIPE §10).

*Table 2.10b. Zones to add.*

| Zone | Derived from | Lenses | Plane |
|---|---|---|---|
| Meniscal horns (4) and bodies (2) | each compartment's peripheral joint-space wedge between condyle and plateau, from the inter-bone gap (ZONES item 3). The horns are split at the condyle's distal point (PRIORART §3, "meniscal corner sub-zones") | 2, 4, 7–9 | sagittal (horns), coronal (bodies) |
| ACL and PCL tubes; roof line | ACL: from the lateral condyle's notch wall, posteriorly, to the anterior intercondylar tibia. PCL: from the medial condyle's notch wall, anteriorly, to the posterior intercondylar tibia. Both need a tibial eminence landmark: the maximum of the tibia's height field between the plateaus, the analogue of `condyles_and_notch`. The roof line is the notch roof's cortex in the notch's mid-sagittal slice | 2, 4, 6, 10, 11 | sagittal |
| MCL band and periligamentous shell | the medial cortices of femur and tibia, across the joint line (PRIORART §3) | 2, 10, 12 | coronal |
| LCL band (not scored; for L1's completeness) | from the lateral femoral epicondyle to the fibular head, across the joint line. It needs a fibular-head landmark, which the BUILT bone groups (femur, tibia, patella) lack | 2, 10 | coronal |
| Hoffa's fat pad | below the patella's inferior pole, behind the patellar tendon, in front of the notch, above the anterior tibia | 5, 16 | sagittal, axial |
| Cartilage plates (MOAKS subregions) | shells 2–3 mm deep on the articular surfaces facing the joint | 17, 19 | all |
| Marrow subregions, with the L5 sites | the bone zones split by MOAKS subregion and by depth. Named sites: the lateral femoral condyle, the posterolateral tibial plateau, the medial patella, the anterior tibia | 14, 15 | all |
| Posterior recesses and gutters | the capsular spaces behind and beside the condyles | 12 | sagittal, axial |
| Baker's region and two tendons | the posteromedial part of zone 5 at the joint line; the medial gastrocnemius and semimembranosus tendons | 13 | axial |
| Pseudotear sites | the transverse ligament, the meniscofemoral ligaments, the popliteus hiatus | L1 licensing; the hardness map | sagittal, coronal |

Two later Parts add to this list: muscle and subcutaneous-fat reference zones for the gain specialist
(Part 3 §3.3.3), and a cortical shell for the fluid-in-cortex censor (Part 5 §5.6, Table 5.10).

**Coronal and axial atlases (DESIGNED; the route is OPEN).** The v5 atlas is painted on the sagittal
grid, at 3.4 mm medial–lateral. Resampled to the coronal grid, it cannot supply the medial–lateral
boundaries that a band a few millimeters thick needs. There are two routes:
- paint each plane's zones from its own template bone masks, by the same rules. `build_zone_labels`
  reads axis semantics, not planes, so its rules carry over;
- paint once on a fine patient-space atlas, then resample to every grid.

Either way, a structure's zone must agree across planes. That agreement is itself an L1 and L3 check.

**Soft boundaries.** Multi-atlas fusion gives each voxel a vote fraction over the zones (ZONES Rank 4).
L1's one-place law reads the zone with the largest fraction. The fraction itself is kept, because a
voxel the atlases dispute is a partial-volume edge, and that is information for the hardness map.

**How zones fail, and how that is measured.**
- *Misregistration:* measured by the NCC gate (ZONES Rank 2).
- *Template bias:* addressed by the unbiased template (ZONES Rank 5).
- *A rule that does not fit an unusual knee:* caught by the one-time eye-check, and per study by a
  placement margin below zero (Part 4 §4.5).

### 2.11 What this Part leaves open

- **Q1, the laws.** The additions in §2.3 (instrument terms), §2.5 (cartilage, extrusion, the bow tie,
  the axial neck, the physeal scar) and §2.6 (hyperextension) need founder sign-off.
- **Q3, extended.** The label scope of the meniscus, MCL, Contusion and Baker's findings. Each one
  fixes which near miss counts as a negative.
- **The two-slice-touch rule across planes.** Do a sagittal and a coronal image at one place count as two
  slices? The surface-contact lens keeps its per-plane counts and the cross-plane concurrence apart,
  so either reading can be applied.
- **The headers.** Which tags survive anonymization, and which magnets are vertical-field.
- **The planes.** Per-plane atlases (§2.10), and one registration per study carried to all its series
  (§2.4).
- **The signal equation's feasibility** (BRIEF §7), in Part 3 §3.3.9.
- **The sane values** of Table 2.8a, each to be measured as §2.8 rule 2 says.

Part 6 §6.7 gathers these, with every other Part's open questions, for the founder.

*External radiology references:* De Smet AA, Tuite MJ (2006), the two-slice-touch rule, AJR; Helms CA
et al. (1998), the absent bow-tie sign, AJR; Hunter DJ et al. (2011), MOAKS, Osteoarthritis and
Cartilage; Peterfy CG et al. (1994), the magic angle in the lateral meniscus, AJR.

## Part 3 — The substrate: headers, the signal-equation law, KneeDiff in physics space, and the one language (layers 0, 1, 2 and 4)

This Part specifies layers 0, 1, 2 and 4 of the knee-as-law design (BRIEF §5): the headers; the MR signal
equation, used as the computation; KneeDiff moved into tissue-parameter space; and the one language every
later reading is written in. Together these layers are the **substrate**. From a study's five or six series
they make three things: a black, resolved away; a residual, which the later layers read; and profiles,
which the society compares. In THEORY's terms the substrate is the data layer, which "NARROWS and ENCODES;
it never DECIDES a finding" (THEORY Part II). In the thesis's terms it is stage 0, stage 1 and §6's
language, worked for the knee.

The layers that read what the substrate makes are designed in Part 4 (layers 3, 5, 6 and 7); the society
(layer 8) is Part 5, and emission (layer 9) is Part 6.

Three project laws bind everything here:
- *Nothing is fitted* (THEORY Part IV, Laws 1–2; BRIEF §3, item 9). Each unknown is read from a header,
  solved from the study's own pixels by inverting a known equation, or recalled from cases measured on true
  normals.
- *Registration is the one bounded utility,* run once per study (Law 3).
- *Nothing here decides a finding* (Law 4).

GenomeVault's ideas are used; its code is not: "I'll be rebuilding it completely from scratch." (founder,
2026-10-02; the ruling is quoted in full in Part 1 §1.2).

### 3.1 The order of knowing, and the rule that joins layers 1 and 2

```
 THE SERIES OF ONE STUDY (~5.5: plane x contrast)
   +-- (0a) TAG HEADER, before any pixel: regime key, inventory, identifiable set ... exact by definition
 REGISTRATION, once per study (Law 3): one transform, carried to every series via the shared frame;
   |   stored values kept (no per-series N4, rescale or histogram match before the law)
 (1) THE LAW: two first-order relaxation laws composed by each series' timing, seen once per series
   |   -> per place: PD-ish, T1-ish, T2-ish, FF-ish, each with delta-method sigma, or a silence + cause
   |   -> per series: the law's residual, typed ............................................ [C]
 (2) KNEEDIFF IN PHYSICS SPACE: each parameter against the true normals of its regime ......... [P]
   |   -> THE BLACK (licensed; a decision kept as a record)     -> THE RESIDUAL
 (4) THE LEDGER: every reading a row of an exact bank; each zone a table of whole-number counts
   +-- (0b) ZONE WORD: paired bits read off the counts; later, stability and the trajectory byte
   v
 layers 3, 5, 6, 7 read the residual (Part 4); layer 8 decides or abstains (Part 5); layer 9 emits (Part 6)
```

*Figure 3.1.* The substrate, in the order things become known. [C] marks a reading on the constraint
reference (input error), and [P] a reading on the population reference (pathology). The two references are
never merged (Part 1 §1.8). Numbers in parentheses are layers (BRIEF §5); L1–L5 remain the domain laws.

The header fills in three steps:
1. the tag words, before any pixel is read;
2. the zone word's first pairs, after layers 1, 2 and 4;
3. its stability pair and trajectory byte, after layers 5 and 7.

HDCSUB F.1 calls such a header "zeroth-order (a region)", available "at frame one". A bit not yet known
reads `00`, the paired form's abstention.

**Ratios before normalization (DESIGNED).** The BUILT front end (`tools/register_and_export.py`) treats
each series alone:
- `n4_correct` divides the series by its own bias field;
- `normalize_intensity` maps its own 2nd–98th percentiles to [0, 1];
- `histogram_match` forces its histogram onto the template study's;
- `register_full` warps it to the template separately.

Each of these multiplies one series by a factor field of its own. That destroys what layer 1 reads, the
ratio of two series at one place. So layer 1 reads stored values, mapped by RescaleSlope and
RescaleIntercept (plus a vendor's private scale, where present). It reads them through one transform per
study, computed on one series and carried to the rest through their shared frame of reference (Part 2
§2.4, item 5). That has two consequences:
- the transform must be kept, though `register_full` discards it today (ZONES, Consequences);
- a study's series must share one box center, though `load_canonical_volume` centers each on its own.

The B-spline mesh stays at [10, 10, 4], for "condyle-scale correspondence without lesion-scale warps"
(LADDER, standing findings). The receive coil's sensitivity is common to series from one coil and cancels
in their ratios. So N4 is applied, if at all, only to the proton-density map after the solve. The BUILT
chain remains the degraded path for any series the law cannot read (§3.3.9).

### 3.2 Layer 0 — Headers: metadata, never meaning

| Layer 0 | |
|---|---|
| Reads | DICOM tags; the series inventory; each zone's count table and footprint (layer 4, §3.5); later, layer 5's stability and layer 7's trajectory (Part 4 §4.3, §4.5) |
| Computes | words, exact by definition; two bitmaps; paired bits at percentile or law-given edges |
| Emits | a tag header per study; a 32-bit word per zone and one per study |
| Licensed by | HDCSUB F.0 (metadata, not meaning); Law 4 (the data layer may narrow) |
| Fails by | absent or aliased words; a quiet word over a finding; a saving that never arrives |
| Measured by | tag survival; the skip-miss rate on gold and phantoms; work counts per study (zones skipped by Tier 0; invocations of layers 3 and 5–7; perturbations and sweep twins run); trajectory shapes on true normals (§3.2.6) |

#### 3.2.1 The ruling

The founder, asked whether a percentile-calibrated header was an oracle in a new coat: "Precisely. The
header is "metadata", not a verdict on meaning. Like the committee members, it simply reads out data that
is correct by definition." (HDCSUB F.0). And, on its use:

> "attaching metadata "headers" to hypervectors so they're classifiable by whole-vector aggregate
> data...The headers are cheap signals, not defining elements. If you want to do the equivalent of CMD-F
> for a profile, they're there for you. otherwise, just ignore them! I call it "metadata"" (founder,
> 2026-10-02)

The founding canon already pointed to GenomeVault's "metadata labelling and processing" (FOUNDING, "On the
multi-scale / cross-pixel concept"). In this design a quantile of the data can play three roles, and the
ruling keeps them apart:

| A data quantile that... | Example | Standing |
|---|---|---|
| decides what a reading means, "where "bright" stops being bright" | a z cut that makes a voxel a lesion | forbidden; it is "the founder's to give" (HDCSUB F.0) |
| writes a digit compared only through cases | the static middle at terciles (THESIS §6.2) | the representation, which "decides nothing" (THESIS §6.7) |
| routes work or orders a search | the header's edges | metadata: it narrows (Law 4) |

#### 3.2.2 The F.1 precedent, read first-hand

`genomevault/hdv_validation/hdc_experimentation/query/biophysical_query_engine.py` holds the 20-bit
signature (HDCSUB F.1). Its main features:
- *Ten opposed pairs in a `uint32`* (`LAYER_NAMES`, line 28), such as `AT_DOMINANT`/`GC_DOMINANT`, so that
  `00`, the header abstaining, is representable.
- *Bank magnitudes as the only input* (`AdaptiveThresholdCalibrator`, line 64).
- *Edges set mostly at corpus percentiles* (lines 97–157).
- *A bitwise vote:* a chunk passes if `match_counts >= int(num_required * threshold)` (lines 426–468).
- *An `expected_genome_fraction` declared by each named query* (lines 491–557).

The file corrects F.1's summary twice:
- *Not every edge is a percentile,* although F.1 says "Nothing is hand-set". Composition is a direct
  comparison (lines 229–231). Flexibility uses an absolute 20 (line 108: "Absolute threshold (small)").
  Resonance uses fixed ratio bands (lines 148–151 and 268–273: "not percentile-based"). The knee labels
  every edge as either a corpus percentile or a point the law gives.
- *The docstring's "470× faster than k-mer approach" (line 9) is not exercised by this file.* Its stages 1
  and 2 are placeholders (lines 375–413).

#### 3.2.3 The E10 trajectory byte, and its caution

E10's eight-byte chunk header includes a **trajectory byte**:
- *bits 0–1* hold the λ-trajectory's shape: `00` MONO_UP, `01` PEAK_DROP, `10` MONO_DOWN, `11` AMBIGUOUS;
- *bits 2–7* hold the decode λ, scaled to 0–63 (SYNTH Part VIII; HDCSUB F.2).

SYNTH calls the shape "the **unifying signal**" (SYNTH Part VIII). MONO_UP routes to an aggressive path.
PEAK_DROP routes to a preserve path: "a real deviation is here — break the chain, preserve it" (HDCSUB
F.2). The knee follows F.2's reading of the E10 configuration, which gives the shape its own byte; SYNTH
Part VII's planning schema had folded it into `flags`.

E10 was measured on 10,000 chunks (HDCSUB F.2):
- *The index itself delivered:* 45.0 MB for 5.9 M chunks, with family prediction at 100.00%.
- *The routing did not:* 9,923 ns routed against 11,058 ns unrouted, or 1.11×. The expectation was 1.55×.
- *The shapes were not the expected ones.* About 95% MONO_UP had been expected (SYNTH Part IV, Layer 3;
  Part VIII). The measured split was 62.0% AMBIGUOUS, 31.5% PEAK_DROP, 5.1% MONO_UP and 1.3% MONO_DOWN.

So a header can be accurate while its saving fails. And a byte whose commonest value is AMBIGUOUS routes
little.

#### 3.2.4 The knee's header layout (DESIGNED)

**The tag header** holds the words of Part 2 §2.9: plane, contrast family, fat suppression, field, vendor,
geometry, side, frame. An absent tag writes the word `unknown`. Three derived words complete it:
- **Inventory**, 40 bits: which series exist, by plane (sagittal, coronal, axial, other) × family
  (T1-like, PD-like, T2-like, inversion recovery, gradient echo) × suppression (yes or no). The family is
  read from TR, TE, TI and ScanningSequence, and cross-checked against the Fluid_Sensitive and
  Fat_Suppression flags.
- **Identifiable set**, 12 bits: which law terms (§3.3.3) the inventory identifies. It covers T1, T2 and
  FF, in each plane group and across planes, and is computed from the inventory alone.
- **Regime key**: field strength, vendor, B0's axis, and each series' sequence family and suppression
  method. A thin cell falls back to field, then vendor, then sequence (Part 2 §2.9).

**The zone word** is one `uint32` per zone, in F.1's form, with E10's byte inside. It is read off the
zone's count table (§3.5.4), and one pair off its footprint. Nothing is re-read from the image.

*Table 3.1. The zone word.*

| Bits | Pair | High bit when | Low bit when | Read off | Edge |
|---|---|---|---|---|---|
| 0–1 | DEVIATION | residual share > p80 | < p20 | deviation banks | percentile |
| 2–3 | POLARITY | bright residual > dark | dark > bright | deviation banks | symmetry; `00` if equal or none |
| 4–5 | FLUID | fluid-word share > p80 | < p20 | signature bank | percentile |
| 6–7 | WATER-IN-FAT | edema-like share > p80 | < p20 | signature bank, fat-bearing zones (`00` elsewhere) | percentile |
| 8–9 | MISFIT | nonzero law-digit share > p80 | < p20 | law banks | percentile |
| 10–11 | CONCENTRATION | peak local residual density over zone mean > p80 (spiky) | < p20 (even) | footprint | percentile |
| 12–13 | EXCLUSION | excluded share > p80 | < p20 | question banks (layer 3; Part 4 §4.1) | percentile |
| 14–15 | BLINDNESS | silent share > p80 | < p20 | coverage bank; hardness map (layer 3; Part 4 §4.2) | percentile |
| 16–17 | STABILITY | stability fraction > p80 | < p20 | layer 5 (Part 4 §4.3) | percentile |
| 18–19 | COVERAGE | ≥ 2 effective slices for the zone's question | < 2 | Part 2 lens 6 | law-given: the two-slice minimum |
| 20–27 | trajectory byte | shape, 2 bits; λ* (E10's λ_opt), 6 bits | | layer 7 (Part 4 §4.5) | E10's form |
| 28–31 | flags | TRAJECTORY_READ, IMPUTED, CENSORED, OUT_OF_FIELD | | layers 1, 3, 7 | words |

**Calibration.** Percentile edges are taken per zone and per coarse regime, over the zone words of every
encoded training study. No label is used. A percentile needs none, and F.1 calibrates on "the corpus's OWN
bank distribution". The edges are versioned, fixed before the runs they serve, and applied unchanged to
test studies. The levels p80 and p20 are routing choices, set by the skip-miss rate (§3.2.6), never by how
well they separate gold.

The **study word** applies the same pairs to the whole-knee bundle. A study's header comes to under 200
bytes for 30 zones. It is a kept value, "made once where it becomes known, and handed to every consumer"
(THESIS §12.6).

#### 3.2.5 What the header routes

*Table 3.2. Routes.*

| Reading | Route | Kind |
|---|---|---|
| identifiable set | which layer-1 specialists speak, per plane | exact, before any pixel |
| regime key | which reference (layer 2) and which coefficient cases (§3.3.5) | exact, with fallback |
| inventory | which lenses can speak at all (Part 2 §2.8, rule 7); what layer 1 may impute | exact |
| DEVIATION low, MISFIT low, FLUID and WATER-IN-FAT not high | **Tier 0**: the zone skips layers 3 and 5–7; its profile and word go forward | narrows (TIERED §1.2; Part 5 §5.4) |
| MISFIT high | the constraint reference first: motion typing and re-registration | narrows |
| BLINDNESS high, every covering series silent for the zone's question | **Tier 2**: kept as hardness information, never guessed (TIERED §1.2, §4.1; BRIEF §5, layer 8; Part 5 §5.4) | keeps |
| PEAK_DROP | E10's preserve path: the structure read in full at λ* | narrows |
| MONO_DOWN | the placement-margin test (layer 7, Part 4 §4.5): m < 0 → the registration alarm and layer 5's expensive families; m above its null range → the structure word goes to its agency (Part 1 §1.8) | narrows |
| any query | Cmd-F | orders |

Two rules govern every route (DESIGNED):
1. **A header may drop work, never a case.** Choosing which of a study's own zones get the expensive layers
   is narrowing (Law 4). Over the memory, a header may order a scan but never shorten it, "since agreement
   of signs is no bound on the cosine of counts" (THESIS §12.1). A scan drops a case only on an exact
   bound (THESIS §12.2).
2. **A skip is not an exclusion.** An exclusion is a positive reading of something incompatible with the
   target (Part 1 §1.7; Part 4 §4.1; THESIS §7.3), and a skip reads nothing. A skipped zone reaches the
   society as its cheap profile, recorded as `skipped_by_header`. No header bit enters a decision or a score,
   and "a header that disagrees with a body is a fact about the header, recorded, never an override" (HDCSUB
   F.5).

**Cmd-F** is F.1's bitwise vote with a declared expected share. It serves four uses:
- teaching sheets (RECIPE §8);
- the hardness map (layer 3; Part 4 §4.2);
- failure audits, for example held-out true normals with DEVIATION high, split by MISFIT, which sorts
  LADDER's saturation pockets onto the right axis;
- ordering recall scans, under rule 1.

The expected share is a check. A query for effusion-like recesses should return about the reports'
Effusion prevalence. If it does not, that is a fact about the header or the query.

#### 3.2.6 How the header fails, and how that is measured

- *Absent or aliased words.* A missing tag writes `unknown`. Two protocols under one word return
  two-humped coefficients (§3.3.5). Tag survival over the corpus is measured first, at no pixel cost.
- *A quiet header over a finding.* This is the **skip-miss rate**: the share of gold finding-bearing zones,
  and of zones holding a planted phantom (§3.3.10), that Tier 0 would skip. Each miss names the pair that
  hid it. Tier 0 is switched on only when the rate is near zero.
- *A saving that never arrives.* The zone word exists only after layers 1, 2 and 4 have read every voxel. So
  it can save only layers 3 and 5–7 and recall. The largest saving is likely in layer 5, which multiplies its
  work by the number of perturbations. The saving is measured in work counted per study, with routing and
  without, as falsifier 6 counts cost (Part 6 §6.4): zones skipped by Tier 0, invocations of layers 3 and
  5–7, and perturbations and sweep twins run. Seconds on the build machine, if recorded at all, are
  informational only and never a go/no-go, since the founder ruled the compute budget out of scope (BRIEF §2).
  E10 delivered 1.11× where 1.55× was expected.
- *A byte that carries little.* The trajectory shapes are measured on held-out true normals, where they
  should be nearly all MONO_UP. E10's 62% AMBIGUOUS is the precedent for a byte that routes almost
  nothing.
- *Unstable edges.* Edges recomputed on half the corpus must change few words on the other half.

### 3.3 Layer 1 — The law as the computation: the MR signal equation

| Layer 1 | |
|---|---|
| Reads | stored values of every series, through the study's one transform; TR, TE, TI and suppression from the headers; regime coefficients recalled by the regime key |
| Computes | per place and scale, the tissue parameters that, composed through the law, reproduce every covering series; per series, its gain |
| Emits | PD-ish, T1-ish, T2-ish and FF-ish with delta-method σ, or a silence with its cause; each series' residual, typed; imputed series, marked |
| Licensed by | L2, the MR signal law (Part 2 §2.3); LAA's law-as-architecture (LAA §2, §5) |
| Fails by | a law incomplete for a regime; a σ that does not track error; biased recovery; mistyped motion |
| Measured by | leave-one-series-out on true normals; σ calibration; physics phantoms; known shifts (§3.3.10) |

#### 3.3.1 Why the knee is LAA's case

LAA addresses problems where "a known physical law relates observable signals to a hidden state we want,
but the unknowns inside the law are not constants", and where the signal that would pin them is incomplete
(LAA abstract; §1). It names "medical imaging from sparse views" among them (LAA §11). The knee fits that
description exactly:
- *The law is known:* "A tissue's brightness is set by its magnetic relaxation under the sequence" (THESIS
  §13.2, MRI row).
- *The sequence's parameters* are in each series' header.
- *Its unknowns drift* with vendor, field and sequence.
- *Each study observes it about 5.5 times* (BRIEF §2), never often enough to pin every unknown everywhere.

LAA's load-bearing move is that "the governing equation's *structure* becomes the network's *topology*":
"An nth-order law is realized as *n* composed first-order specialists", judged only at the composite (LAA
abstract; §5). For the knee this is literal. Between pulses, magnetization obeys two first-order relaxation
laws, the Bloch equations without excitation:

```
 dM_z/dt  = (M_0 − M_z) / T1        longitudinal recovery
 dM_xy/dt = −M_xy / T2              transverse decay
```

The spin-echo signal composes them through the sequence's timing: recovery over TR (after an inversion at
TI, for STIR), excitation, then decay to the echo at TE. So the law splits into a **recovery specialist**,
which owns T1, and a **decay specialist**, which owns T2, composed by multiplication, with scale and
compartment terms beside them. The recipe asks for exactly this: "Name one lens per term of the law"
(THESIS §13.1, step 2).

**Departures.**
- *From THESIS §13.2's MRI row,* which names one lens per sequence. Here there is one specialist per term,
  and each sequence is one observation of the law.
- *From LAA's training vocabulary, as Part 2 §2.3.2 records.* Each place's unknowns are solved from this
  study's own series. That is LAA's regime that "*inverts a known law*" (LAA §1). Only regime coefficients
  pass between studies (§3.3.5). Solving for T2 from two echoes is a measurement, like the camera's dark
  (THESIS §4.2), not a model.
- *From THEORY Part III,* which sketched "a **Society of first-order finding-specialists**". The law wired
  in here is the instrument's physics. Findings belong to the society (layer 8; Part 5).

#### 3.3.2 The composed law

In logs, for series s at place v:

```
 ℓ̂_s(v) =  γ_s                          gain      one per series: receiver gain, vendor scaling
         + log P(v)                     density   P = ρ·c, the coil's sensitivity c folded in: "PD-ish"
         + log E1(TR_s, TI_s; T1(v))    recovery  1 − e^(−TR/T1); STIR: abs(1 − 2e^(−TI/T1) + e^(−TR/T1))
         − TE_s · R2(v)                 decay     R2 = 1/T2; in fibrous tissue, with the angle term
         + log F_s(f(v), ε_s(v))        fat       F = (1 − f) + f · w_s · ε_s; ε = 1 without suppression
         + μ_s,k                        regime    recalled correction for tissue class k (§3.3.5)
 r_s(v) = ℓ_s(v) − ℓ̂_s(v)               the only residual that exists
```

The terms are read as follows:
- *Header quantities.* TR, TE (the effective echo, for fast spin echo), TI and the suppression method come
  from the header.
- *The magic angle.* In fibrous tissue the decay carries the fibers' angle θ to B0:
  R2(θ) = R2,iso + R2,aniso · ((3cos²θ − 1)/2)². This is the magic angle as a term of the law (Part 2
  §2.3.1).
- *Fat.* w_s is fat's relaxation-weighted signal relative to water's, from regime constants. Under STIR,
  fat is nulled through the recovery term instead.

Three properties carry the design:
- *Ratios cancel what the series share.* Between two series at one place, P(v) cancels, coil included,
  and only γ_s − γ_t remains: one number per pair of series, not one per place.
- *The decay is linear.* A TE contrast gives R2 by subtraction and division.
- *Complementary transparency is in the law.* In water tissue f = 0, so the fat term vanishes. Each term is
  silent where its tissue is absent: the OTP's "0 = "look elsewhere"" (HDCSUB A.3), written by physics.

Physical bounds are law-given censors, which make the impossible "*unrepresentable*" (LAA §2):
0 ≤ f ≤ 1, 0 ≤ ε ≤ 1, P > 0, T2 ≤ 2·T1. A solution that would leave this domain is not clipped; its
residual is typed (§3.3.8).

#### 3.3.3 The specialists, and supervision only at the composite

*Table 3.3. One specialist per term (DESIGNED).*

| Specialist | Owns | Isolated by | Speaks in | Emits | Silent when (cause kept) |
|---|---|---|---|---|---|
| Gain | γ_s | a reference tissue read in the series, against its recalled regime value: muscle everywhere, marrow fat where unsuppressed | every series | γ_s with its spread; whether two reference tissues agree | no normal reference tissue in the field |
| Decay | R2 = 1/T2 | two series differing in TE, same fat state, similar TR | water tissues; marrow water once f is known | T2-ish with σ, θ-corrected in fibrous zones | no TE contrast in the plane group; both signals at the noise floor (fibrous tissue, cortex) |
| Recovery | T1 | two series differing in TR, or one inversion recovery, same fat state | water tissues | T1-ish with σ | no TR contrast; T1 beyond what the pair resolves (σ unbounded) |
| Fat | f; ε_s | a suppressed and an unsuppressed series of comparable TR and TE, or STIR beside T1 | marrow, Hoffa's pad, subcutaneous fat | FF-ish; the suppression-residual map ε_s | no such pair; water tissue (transparent) |
| Density | log P | what the other terms leave | every place | PD-ish, relative only | never silent; compared across studies only through layer 2 |

The gain specialist needs reference-tissue zones the atlas lacks: muscle and subcutaneous fat. These are
added beside Part 2 §2.10's list (DESIGNED).

**Supervision only at the composite.** No specialist's output is compared with a target, since no
tissue-parameter maps exist to compare it with. At each place, the joint solution is the parameter set
that, composed through the law, reproduces every covering series within its σ. "None is supervised alone.
The only error that exists is between the *composed* prediction ... and the observed" (LAA §4). Each
specialist owns one term and composes with the others through the law's own operators. So "there is no
flexible blob to absorb a neighbor's contribution" (LAA §5), and that is why a regime coefficient means
something stable enough to store.

**The loop** transposes LAA's grey-box loop (LAA §4):
1. solve the terms the identifiable set names, place by place, at each scale (§3.3.4);
2. recall the regime coefficients (§3.3.5);
3. pin each gain on its reference tissues and re-solve, repeating steps 2–3 until the gains settle;
4. impute absent series along identified terms (§3.3.6);
5. propagate σ (§3.3.7) and type the residual (§3.3.8).

**What a study can identify** depends on its inventory:
- sagittal PD FS beside sagittal T2 FS, or one dual-echo series, is a TE contrast, so decay speaks there;
- sagittal PD beside sagittal PD FS is a fat contrast;
- coronal T1 beside coronal PD FS or STIR changes TR, TE and fat state at once, so only the joint solve
  speaks, with regime constants;
- a plane with one series identifies nothing alone. It contributes at the region scale.

How often each pairing occurs is the first measurement (OPEN), from `train_series.csv` and the tags. It
also informs Q6 (series scope), since the series worth fetching are those that make terms identifiable.

#### 3.3.4 Two scales: the plane group and the region

Each series is sharp in-plane and 3–4 mm thick across it (L3; Part 2 §2.4), so planes differ in
point-spread function. Solving one place from a sagittal and a coronal series would mix two averages of its
tissue and read partial volume as physics. So the law runs at two scales, and every value keeps its scale:
- **The plane-group scale** solves voxel by voxel, from the series sharing a plane, on that plane's grid
  (Part 2 §2.4, item 4). It serves thin structures read in-plane: menisci, ligaments.
- **The region scale** solves across planes, after every series is blurred in patient space to the
  coarsest slice spacing among them. It serves geographic findings: edema, effusion, the fat pad.

Correspondence between series is tag arithmetic up to patient motion (Part 2 §2.4, item 5). Motion is not
assumed away; it is read in the residual (§3.3.8).

#### 3.3.5 Regime coefficients, recalled

The headers do not give everything the law needs. The missing coefficients are:
- magnetization transfer, which darkens cartilage and muscle in multi-slice fast spin echo;
- J-coupling, which brightens fat;
- the effective TE of long echo trains;
- suppression baselines;
- fat's relaxation constants;
- each vendor's noise.

These are LAA's "thin" unknowns (LAA §4), and they vary by regime (LAA §8). Each is the law's systematic
residual in health: the median of r_s over tissue class k, across one regime's true normals, for one series
family. Measured in health, the law's unexplained part *is* the regime's coefficient. Measured in one study,
beyond that coefficient, it is information about the study (§3.3.8).

Each normal's coefficients are one case, kept under its tag header, since the priors' "words form the
**regime key** a case from this field is kept under" (THESIS §4.1; LAA §6). Recall goes by the regime key
with Part 2 §2.9's fallback. The coefficient used is the recalled cases' median, and its σ is their spread
(§3.3.7).

**Departure** from LAA §6, where "a context near several stored ones returns their blend". Here the cases
stay individual (THESIS §7.1), and the median is taken at read time, never stored. Keeping the cases apart
exposes aliasing: two protocols under one word return two-humped coefficients, which is the signal to split
the key (Part 2 §2.9).

**Departure** from LAA §8. Of its three stratified-regression designs, all fitted (LAA §2), the knee keeps
only the block-diagonal partition: boundaries "known and sharp", given by the headers, with strict
no-contamination. The per-block regression is replaced by the median over the regime's individual cases,
taken at read time as above, and by per-regime references (§3.4.2). Spatially clustered regression and a
mixture-of-experts gate are dropped because they also learn the partition (Part 2 §2.9; Law 1).

#### 3.3.6 Missing series, imputed by the law

LAA recovers a missing input from "coherent replicates", other instances of one physical system. This
refinement "*conditions the engine's inputs*" and never carries the inference (LAA §2, §9). In the knee the
replicates are the study's other series: one object, seen under several known sequences. The replicate is
the physics (BRIEF §5, layer 1).

- *What it computes.* The solved parameters at a place are run forward under an absent series' nominal TR,
  TE and fat state. LAA's "**Shape from the field, level from the self**" (LAA §9) turns over. The shape,
  the tissue parameters, comes from the study. The level, the absent series' gain, suppression residual and
  noise, comes from the regime's cases.
- *Its limit.* A series is imputed only along terms the present series identify. With no TR contrast there
  is no T1 and no imputed T1-weighted series. The lens that needs one stays silent, with that cause.
- *The coherence gate,* after LAA's order parameter (LAA §9), is the share of covering series whose residual
  lies within 2σ at a place. Where they cohere, the imputed value comes with its propagated σ. Where they do
  not, nothing is imputed, and "the system correctly trusts the local signal over the field".
- *Provenance.* An imputed series is marked in every reading it feeds. It is **never a voice in
  concurrence**: it is a function of the series that made it, so it carries no independent evidence (Part 2
  §2.4, item 7; RECIPE §7). Layer 2 needs no imputation, since it compares tissue parameters, not series.
- *The check* is leave-one-series-out. On true normals with three or more series, each series in turn is
  imputed from the rest. The normalized error e(v) = (ℓ_s − ℓ̂_s)/σ̂_s should be standard normal wherever the
  law holds.

#### 3.3.7 Uncertainty by the delta method

Because the law is the computation, uncertainty is "*propagated through the law's own structure*" (LAA §2,
§10; THEORY Part III). For the decay specialist, with ΔTE = TE_s − TE_t > 0:

```
 R2     = [ (γ_s − γ_t) + (μ_s − μ_t) − (ℓ_s − ℓ_t) ] / ΔTE
 σ²(R2) = [ σ²(ℓ_s) + σ²(ℓ_t) + σ²(γ_s − γ_t) + σ²(μ_s − μ_t) ] / ΔTE²   (+ covariance terms)
```

Covariances enter where inputs share a source, such as a gain and a coefficient read off one reference
tissue. These are the law's cross-terms (LAA §5).

At adequate signal, σ(ℓ) ≈ σ_noise/S, so dark places get wide bars unprompted. The recovery specialist
inverts a monotone function of T1, and its σ is the observation σ over that function's slope. The slope
vanishes when both TRs recover the tissue fully, or neither does, so T1 falls silent by propagation alone.

Below a signal-to-noise floor, the magnitude image's Rician bias breaks the linearization. There a
specialist is silent with the cause `below_noise_floor`: the honest statement that a meniscus's T2 cannot be
measured at clinical echo times. Phantoms (§3.3.10) locate the floor.

σ goes three places:
- into layer 2's z (§3.4.2), so a deviation measured with a wide bar counts less;
- into the MISFIT pair;
- into the emission, as "the law's uncertainty" (BRIEF §5, layer 9; Part 6 §6.1.3).

The claim is one of calibration: "error rises precisely where the propagated bar widens" (LAA §12).

#### 3.3.8 The law's unexplained part is information

The founder's ruling on a lens that never resolves its signal, "That IS information!" (founder,
2026-10-02; quoted in full in Part 1 §1.7), holds for the law's residual too. Each failure to explain has a
signature, and the signature says something about the place.

*Table 3.4. The residual, typed (DESIGNED).*

| Type | Signature in r_s(v) | Explained by | Emits | Goes to |
|---|---|---|---|---|
| Motion between series | a dipole along edges, in one series against the rest: r ≈ ∇ℓ_s · δ | nothing in the law: input error | local shift δ, with significance | constraint reference (Part 1 §1.8): re-register (Law 3), or withhold cross-series readings there |
| Ghosting | edges repeated along the phase-encoding axis (from the header), one series | motion during that series | the ghost band | hardness map (layer 3; Part 4 §4.2) |
| Magic angle | positive at short TE only, fibrous zones, θ near 54.7° | the R2(θ) term | θ-corrected T2-ish; the window | Part 2 §2.3.1's censor |
| Suppression failure | suppressed series bright where the unsuppressed one shows fat; smooth, peripheral | ε_s(v) near 1 | the ε map | Part 2 lens 5; censor on edema and Hoffa readings |
| Partial volume | at tissue boundaries, strongest across each series' thick axis, differing by plane | two tissues in one voxel | edge mark | hardness map |
| Noise floor | positive in dark tissue, growing with TE | Rician bias | silence below the floor | hardness map ("blind here") |
| Susceptibility | voids with bright rims, every series | metal or gas | hardware mark | Part 2 §2.9's hardware prior |
| Regime signature | systematic over a tissue class across a regime's normals | μ_s,k | — | absorbed into the coefficient (§3.3.5) |
| Unexplained | none of the above | — | kept as a finding with its context | Part 1 §1.7; Part 4 §4.4; Part 5 |

Two notes complete the table:
- *Out-of-vocabulary is not a residual.* The law can fit a place that L2's tissue table cannot name, such
  as water with a short T1 (blood products) or a void in every series. The Signature lens writes `unnamed`,
  and the reading is kept for the society.
- *The typical magic-angle brightening is already licensed* by the population reference, wherever normal
  knees put a fiber at the same angle. What survives it comes from a study positioned differently, so θ is
  computed per study (Part 2 §2.3.1).

**The genomic reading of tightness, kept here.** SYNTH reads a large residual "in structurally constrained
positions" as an error and one "in variable positions" as a real variant (SYNTH Part IV, Layer 2). RECIPE
§0 forbids porting that reading to KneeDiff, where a large deviation in a tight population is pathology
(Part 1 §1.8). It is, though, the right reading for the law's residual:
- where the law is tight (one tissue, good signal, series that agree elsewhere), a large typed residual is
  input error;
- where the law is loose (boundaries, low signal), a large residual says little.

Two differences from SYNTH remain. Nothing is corrected toward a template, as SYNTH's
`correct_toward_template` does: a typed residual routes and is recorded. And an untyped residual in a tight
place is kept, not called an error. In the same way, the residual makes SYNTH's cross-bank check
quantitative. SYNTH asks whether "All banks point to same nucleotide" (SYNTH Part IV, Layer 0). The law
asks whether one set of tissue parameters explains every series, and by how much it does not.

#### 3.3.9 Feasibility, stated honestly

*Table 3.5. Caveats (BRIEF §7).*

| Caveat | Why it bites | Response | Status |
|---|---|---|---|
| Unknown receiver gain | absolute intensity means nothing across series | ratios; one γ per series, pinned on reference tissue; PD-ish relative | DESIGNED |
| Per-series intensity filters | a vendor's normalization filter makes c differ between series | read from the header where recorded; else a smooth residual between series | OPEN |
| The built front end | `n4_correct`, `normalize_intensity`, `histogram_match` rescale each series alone | stored values with rescale, one transform per study (§3.1) | DESIGNED; changes `tools/register_and_export.py` |
| Fast spin echo | effective TE; bright J-coupled fat; magnetization transfer; short-T2 blurring; stimulated echoes in 3-D variants | regime coefficients measured in health; "-ish" values | OPEN: their size per regime |
| Fat suppression | ε varies in space; water saturated where B0 is off; STIR nulls any tissue with fat's T1 | two-compartment fat term; ε map; STIR via recovery | DESIGNED |
| Co-registration | planes differ in point-spread function; motion between series | one transform; two scales; motion typed | DESIGNED |
| Magic angle | T2 depends on fiber orientation | the R2(θ) term; positioning read per study | DESIGNED (Part 2 §2.3.1) |
| Few series per plane | many terms unidentified | identifiable set; silence with cause | OPEN: the corpus's inventories |
| Absent tags | no TR or TE, no law | the series falls back to the built raw path | OPEN (Part 2 §2.9) |
| Noise | Rician floor; parallel imaging makes noise vary in space | SNR floor; noise read in homogeneous tissue | DESIGNED |

Where the law cannot run, a series is read as today: KneeDiff on raw intensity against its series type's
reference (BUILT). The header records each series' path.

#### 3.3.10 How layer 1 fails, and how that is measured

- *A law incomplete for a regime.* The leave-one-series-out error is measured on held-out true normals, by
  regime, tissue class and series family. The rate of |e| > 3 should be near the Gaussian rate, and an
  excess names a missing term. Law 5 supposes missing information, never missing capacity.
- *A σ that does not track error.* Binned by σ̂, the empirical error must rise with it (LAA §12).
- *Coefficients without a stable meaning.* LAA predicts the decomposition "*preserves the coefficients'
  physical meaning* well enough to store and recall across instances" (LAA §12). A regime's coefficients,
  measured on two disjoint halves of its normals, must agree within their spread.
- *Biased recovery,* measured with **physics phantoms** (DESIGNED). A lesion is planted in a true normal's
  tissue parameters, such as raised marrow water fraction and T2 over a geographic blob. It is then
  forward-modeled through every series of that study, with the study's own gains, suppression residuals,
  coefficients and noise. So it is consistent across series, which a lesion painted into one series' pixels
  never is. Rerunning layers 1–2 then measures four things:
  - recovery of the planted parameters;
  - σ's calibration;
  - a rise on the population reference;
  - no rise on the constraint reference.

  Swept over amplitude, it gives VERDICT's response curve in physical units; that instrument "requires AUC to
  rise with amplitude". It seeds the phantom library (BRIEF §7; Part 5 §5.8), the knee's form of LENS Phase
  4's edge cases. A phantom the law built is always explained by the law, so phantoms test recovery and σ. The
  law's completeness is tested by leave-one-series-out and by gold.
- *Mistyped motion.* One series of a true normal is shifted by a known δ. The motion type must recover δ,
  and nothing must rise on the population reference.

### 3.4 Layer 2 — KneeDiff in physics space

| Layer 2 | |
|---|---|
| Reads | layer 1's tissue parameters and σ for the study; the same for the true normals of its regime and identifiable set |
| Computes | per parameter and place, a robust reference (μ, spread, n) and z with the study's own measurement noise in the denominator |
| Emits | the black (licensed places, kept as a record); the residual; z per parameter; reference silences with their cause |
| Licensed by | L1, the platonic knee: one normal arrangement, with a per-voxel licence (Part 2 §2.2; THEORY II.2–II.3) |
| Fails by | thin or contaminated references; a wrong merge of regimes; a misplaced zone read as pathology |
| Measured by | the fixed make-or-break instrument; false survival on held-out true normals; leave-one-normal-out (§3.4.5); the constraint reference for misplaced zones (Part 1 §1.8) |

#### 3.4.1 What is built, and what the ladder taught

**BUILT.**
- `src/RSNA_Knee/platonic_reference.py` squashes registered references into a per-voxel (μ, σ, n). It uses
  the mean and sample deviation, or a weighted form for a Byzantine weighted vote (`build_reference`).
- `residual_map` computes z = (x − μ)/max(σ, floor). `detrended_residual_map` first removes a mask-aware
  Gaussian trend per slice. `max_masked_window_density` gives the peak survivor density over knee tissue.
- `src/RSNA_Knee/kneediff.py` holds the scalar definitions. They answer in named codes: `classify_cell`
  says "within_tolerance" or "deviant", never a bool.
- The GenomeVault port carries `ConsensusBase` as (μ, σ, n). It omits the consecutive-disagreement decay
  and the IUPAC codes as "wrong physics for pixels" (VERDICT, Consequences).

**The ladder, read as a record of diseases.** Every rung repaired one object: "the per-cell LICENSE (what
intensity the reference tolerates where) is what each rung has been repairing" (LADDER, standing
findings). v1, with an affine registration only, showed boundary misalignment. v2 added N4, a mask and a
B-spline, and found "regional intensity offsets 4–6σ", a "Scanner/protocol contrast-ratio mismatch that
p2–p98 scaling cannot reconcile". v3 added histogram matching and v4 a low-frequency detrend.

Then came the reset. The reference "had been squashing mirror-image knees together since v1", so "all
v1–v4 numbers are DEAD". They are kept only as "the historical record of the diagnostic method working"
(LADDER, substrate reset).

The first readings on v5 used Effusion, with 50 true-normal references, 30 held-out true normals and 35
gold positives. The AUC was 0.58 with no detrend and at σ = 8, 0.67 at 16, 0.68 at 24 and 0.66 at 32. And
"several held-out TRUE normals still peg density 1.0" (LADDER, v5).

v2's disease is what layer 1 removes. A contrast-ratio mismatch is a difference of TR, TE and suppression,
which the law explains from the headers. Histogram matching forced one series' intensity distribution onto
another's, blind to which tissue was where. In physics space the law does that reconciliation, place by
place.

#### 3.4.2 The reference over tissue parameters (DESIGNED)

The reference is kept per coarse regime, identifiable set, parameter p, scale and place v. Each holds three
quantities:
- μ_p(v), the median of x_p(v) over the normals in which p is identified at v;
- s_p(v), equal to 1.4826 × the median absolute deviation. This robust spread keeps a "normal" whose report
  missed a lesion from pulling the licence much. It is the Byzantine idea, at the voxel, and it is needed
  because even a perfect report reader is capped near 0.88–0.92 against gold (BRIEF §2);
- n_p(v), the number of normals that spoke there.

The population spread holds both biology and the normals' measurement noise. Its biological part is
σ²_bio = max(s_p² − mean σ²_meas, floor²). A study is read with its own measurement noise:

```
 z_p(v) = ( x_p(v) − μ_p(v) ) / √( σ²_bio,p(v) + σ²_meas,p(v) )
```

So the floor becomes physical. `residual_z`'s docstring calls `sigma_floor` "a tolerance, not a fudge";
here the tolerance is the study's own delta-method σ. Where n_p(v) is too small for an honest spread, the
reference is silent at v for p or falls back to its parent key (Part 2 §2.9). At n = 20 a per-voxel σ
inflates P(|z| > 3) about 2.8 times (VERDICT).

**What it should take over (falsifiable).**
- *Histogram matching should become unnecessary,* since the law explains protocol contrast.
- *The detrend should shrink,* since the receive field cancels in ratios. A smooth transmit-field effect on
  fast-spin-echo refocusing may remain.

LADDER's v5 readings found detrend "still required on v5, with a robust σ∈[16,32] plateau" on the raw
substrate (LADDER, v5 first readings); whether it is needed in physics space is open, and the re-sweep of
§3.4.5 settles it. Both predictions are measured on the fixed instrument (§3.4.5).

**Pooling.** Tissue parameters are meant to mean the same thing across protocols. So regimes whose
per-voxel references agree are merged, raising n (Part 2 §2.9: "A split that leaves the reference's
per-voxel distributions unchanged is merged"). A merge the law licenses is the most direct cure for small-n
tails.

#### 3.4.3 The black, by seniority

The founder's ruling: stage 1/2 "resolves away the "background" cleanly, so no heavy compute or reasoning is
wasted on that which we know is insignificant. So the "knee", or the lesions, it can become MUCH more than
0.1% of the volume of the image." (founder, 2026-10-02). In the thesis this is stage 1, where "Two filters
act in order of seniority" (THESIS §4.2). The knee's two filters (DESIGNED):
- **The senior** clears places with no tissue to read: outside the body mask, or outside every series'
  field. It is narrow and knowably correct, and it decides alone. The body mask is the per-slice-filled one
  in `src/RSNA_Knee/anatomy.py`, since `knee_mask`'s Otsu mask excludes dark marrow (measured 2026-08-31;
  comments in `bone_masks` and `build_zone_labels`).
- **The junior** speaks only inside what the senior keeps. A place is black when every identified
  parameter lies within the licence (|z_p| below the threshold) and its signature word is its zone's normal
  one. The population spread plays the thesis's haze, and the junior "refines only after deferring".

The black deletes nothing: "a removal is a decision by a reading entitled to make it, kept as a record,
never a discard" (THESIS §4.2). A black voxel keeps its values for any lens that reads raw data (RECIPE §0).
It writes the sparse vector (§3.5.4), including the deviation bank's licensed row. That row is the Deviation
lens's exclusion mark, "no lesion at this voxel" (Part 2 §2.8, rule 3), so it is written, never dropped.
Black is silence in the full analysis, "Yet black is not nothing" (THESIS §6.3).

The threshold holds a stated false-survival rate on held-out true normals. Because that rate compounds over
the four parameters a place can have, the threshold is set per identifiable set. It is never set to
separate gold (Part 2 §2.8, rule 2). The share cleared on v5 is measured. The pre-v5 "≥96% of cells zero
out" is dead (LADDER).

#### 3.4.4 The residual, and middles set on it

What survives is the **residual**, and in it lesions are a large share. Its digits need middles:

> "Middles live on the residual. A residual metric's static middle is set at that metric's terciles over
> the residual cells of the teaching studies, never over raw voxels. Once the black is cleared, "top third"
> means top third of what deviates." (RECIPE §4)

The static middle "is set once ... It never moves per movie or per plate, and is never chosen to separate
confirmed cases" (THESIS §6.2). For the knee:
- it is set once, over the residual cells of the teaching studies, which are the report-labeled pool and
  the true normals;
- it is never set over gold, which establishes and does not teach (RECIPE §5);
- it is never moved per regime (Part 2 §2.9).

In physics space the residual metrics are each parameter's z and the parameter values of residual voxels.
Layer 2 is Part 1 §1.8's population reference, and layer 1's typed residual belongs to its constraint
reference. The two write separate banks (§3.5.4), so neither outvotes the other.

#### 3.4.5 How layer 2 fails, and how that is measured

- *Against the fixed instrument.* The make-or-break harness "is the fixed instrument across rungs — the
  verdict codes and the AUC statistic do not move between iterations" (LADDER, Consequences; VERDICT). It
  is run on the v5 Effusion layout: physics-space z against raw z on the same studies, with the detrend
  re-swept in both. The live baseline is 0.58 with no detrend and 0.68 at σ = 24. The run needs every series
  of those studies; `pick_series` (`tools/fetch_labeled_studies.py`) fetches one today.
- *Saturated true normals.* Each held-out true normal that still pegs density 1.0 must be explained on one
  axis: MISFIT high, or a typed population deviation. A Cmd-F audit finds them (§3.2.5).
- *Thin or contaminated references.* Measured by false survival on held-out normals, binned by n_p(v), and
  by leave-one-normal-out survival. A normal that looks abnormal against the rest goes to the founder's eye,
  never silently dropped.
- *A wrong merge.* Measured by survival per regime, before and after the merge.

### 3.5 Layer 4 — The one language: the exact ledger, with the codebook as quantizer

| Layer 4 | |
|---|---|
| Reads | every reading of layers 0–3 and 5–7: tissue parameters, z, signature words, law digits and types, question calls, orientations, coverage |
| Computes | for each reading, the row its quantizer level or word lights; count tables per zone and study; one whole-number cosine; the exact decode |
| Emits | zone and study profiles with footprints; packed signs; named differences |
| Licensed by | H2, one exact language (THESIS §1.4, §6, §12) |
| Fails by | a substrate that loses a distinction a question needs; silence miswritten; a rung too fine or too coarse |
| Measured by | H2's bridge on the hard pairs; tests that pin the three zeros; the precision ladder (§3.5.6) |

#### 3.5.1 Why the built encoder is replaced

Read line by line, `src/RSNA_Knee/hdc_encoder.py` departs from the language in eight places:
1. *Random codes.* Each voxel gets K = 4 random dimensions in D = 4,096 (lines 35–36, 100) and random signs
   (line 101). The docstring promises "Hadamard-derived signs" (lines 7–11), but the code draws them with
   `rng.choice`. So interference is statistical, where GenomeVault's mature form cancels it "*exactly*, not
   statistically" (HDCSUB A.2).
2. *One accumulator per zone.* `encode_zones` adds every survivor of a zone into one D-wide accumulator
   (lines 117–133), at survivors × 4 / 4,096 writes per dimension. BRIEF §4 estimates this above 2, past
   TIERED's ~1.5 collapse line (TIERED §0, §2.2). That law is itself "DOCUMENTED-ONLY" (HDCSUB F.4 #5), so
   this estimate calls for measurement, not a verdict.
3. *Signs, not counts.* `encode_study` keeps `np.sign` of the zone and study accumulators (lines 143–147).
   That loses the exact decode and the named difference (THESIS §6.6, §7.6). And signs bound nothing:
   u = 3h₁ + 2h₂ and v = 2h₁ + 3h₂ have a count cosine of 12/13 and a sign cosine of 0 (THESIS §12.1).
4. *The licensed voxel vanishes.* `ternary_cell` writes it as 0, and the encoder drops every 0 (lines
   123–127). So "licensed here" and "never read" become one symbol (Part 2 §2.8, rule 3; THESIS §6.3).
5. *Not the one comparison.* `similarity` divides a float dot product by the square root of nonzero counts
   (lines 151–156). It is not a whole-number cosine of count tables against a pre-set level (THESIS §12.2).
6. *Prototypes.* `bundle_prototype` majority-bundles (lines 159–164). `tools/lens_eval2.py` builds one
   prototype per finding with it (lines 133–159), which THESIS §7.1 forbids: "a sum would lose which
   readings occurred together in each case" (BRIEF §4).
7. *Recall nothing asks for.* A position codebook recalls "an individual entity from a superposition of
   thousands" (HDCSUB A.1). The knee keeps each voxel's place beside the profile, as the footprint (THESIS
   §6.5). No question recalls a voxel out of a bundle.
8. *Independence by seeds.* Codes that collide need a seed per committee member, because "Same collisions →
   Same errors" (COMMITTEE §1.2; HDCSUB F.4 #4). Exact rows do not collide, so "Independence must come from
   different evidence, not different encodings" (RECIPE §7). In the knee that evidence is the series.

Two things are kept: the zone label volume (`zone_labels`; ZONES, Rank 1), and the sign convention as the
deviation bank's outer rows. `hdc_encoder.py` is frozen as the v1 instrument's encoder, so `lens_eval2.py`
still runs. The ledger never imports it.

#### 3.5.2 The carrier

The ledger is THESIS §6 and §12, built from specification as a new module, with no GenomeVault code (ruling
6; DESIGNED).
- **Banks.** A bank is 512 dimensions holding one kind of reading. Its rows are Sylvester-Hadamard rows,
  H[i, j] = (−1)^popcount(i AND j), in an order seeded by the bank's number. So H Hᵀ = 512 I: "Rows cancel
  exactly, so values written in one bank never blur" (THESIS §12.1).
- **Bundles.** A reading lights one row. A **bundle** is its **count table**, kept as "whole numbers stored
  in 32 bits and summed in 64". Its "Counts add in any order and are undone exactly by subtraction"
  (THESIS §12.1).
- **The exact decode.** "a bank's vector times the bank's rows is 512 times each row's count" (THESIS
  §12.1).
- **One comparison.** The comparison is "one cosine over every row of every bank the question names ... and
  both sides speak in". A bank either side leaves silent "is out of the dot product and both norms", and
  the cosine is "never a cosine per bank, averaged". A level a/b is reached when b²·dot² ≥ a²·‖u‖²·‖v‖²,
  computed in whole numbers. The answer is "reaches", "short" or "silent" (THESIS §12.2).
- **Versions.** The carrier and the layout are versioned, and "profiles of different layouts are never
  compared" (THESIS §12.1). Each compiled body has an exactly agreeing reference twin (THESIS §12.5).

The silence rule lets different inventories meet. A study without a TE contrast cannot write the T2 bank,
so T2 drops out of that comparison, and two studies are compared over what both read.

**Departure** from THEORY II.4's mechanics, not its idea. THEORY composes scales "by **bind**
(role⊗filler), **bundle** (⊕), **permute** (ρ)" in "near-orthogonal" partitions. Here, banks are exactly
orthogonal, and addressing subsumes binding. The elementwise product of Sylvester-Hadamard rows i and k is
row i XOR k. So with role and value in disjoint bit-fields of the index, the bound row is the row the
address (zone, value) names.

#### 3.5.3 Ruling 5 inside the ledger

> "at some point I use the codebook itself, and typed shifts in its encoding across dimensions to take data
> encoded as floats and quantize it to shit, until the encoding itself is only in balanced ternary, with the
> codebook serving as a lossy compression of scalar intensity, the strict orthogonality serving for
> directionality encoding, and the balanced ternary used to encode presence, absence, or orthogonality to
> the measure being encoded in that dimension." (founder, 2026-10-02)

*Table 3.6. The ruling's elements, placed (DESIGNED).*

| The founder's element | In the ledger | Grounding |
|---|---|---|
| "the codebook serving as a lossy compression of scalar intensity" | a bank's rows are a quantizer's levels; a value lights its level's row. A zone's count table is its quantized histogram: lossy in the ladder, exact after it. The value is kept beside | THESIS §6.1, §6.2, §12.4 |
| "typed shifts in its encoding across dimensions" | each quantity has its own ladder of rows, with a level index moving along it. Edges sit at quantiles of the teaching residual, so all levels are equally likely. One level either side of the middle is THESIS's digit; finer levels only where the precision ladder licenses them | HDCSUB A.2 (discretize-then-roll); THESIS §6.2 |
| "the strict orthogonality serving for directionality encoding" | directions are exact orthogonal rows: θ to B0, binned; a tear's plane (horizontal, vertical, radial); the ACL's course against the roof; the direction to a center, one of eight | THESIS §6.1 (the dome link); BRIEF §5, layer 4; Part 2 lenses 4, 11 |
| "the balanced ternary used to encode presence, absence, or orthogonality" | each question bank holds a call: a present row (+1), an excluded row (−1), and *orthogonal*: read, but neither row lit | THESIS §7.3; HDCSUB A.3; Part 1 §1.7 |

**Three zeros, kept apart.**
1. **The middle** (THESIS §6.2): "At the middle" is a written row, and it counts in every comparison.
2. **The informational zero** (THESIS §6.3): a silent bank means no reading, and it counts in none.
3. **Orthogonal** (founder; THESIS §7.3, "something else entirely"; HDCSUB A.3, "look elsewhere"): the
   place was read, and the reading bears neither for nor against the question. It lights neither question
   row, so it enters no dot product. But it is not silence: the coverage bank records the read, so the
   orthogonal count is exact (read, minus present, minus excluded).

The thesis draws the same line: "A call's 0 is silence, like a bank nothing read, not a reading at its
static middle: the notation is shared, the meaning is not" (THESIS §7.3). The built code merges the first
two (§3.5.1, item 4).

**Where balanced ternary lives.** GenomeVault accumulates and then keeps only signs (HDCSUB A.1), while the
ledger keeps counts. **Departure** from A.1, for §3.5.1's item 3. The founder's quantization stays where it
is safe:
- in every reading, which is a level row;
- in every bundle's packed signs, two bit planes per bank (128 bytes). These store, ship and order scans
  (THESIS §12.1, §12.4; HDCSUB F.3's packed Hamming), and never decide.

**Departure: adjacent levels do not overlap.** A rolled basis (HDCSUB A.2) and LAA's "smeared codebook"
(LAA §2, §6) make neighboring bins similar on purpose. In exact rows they are orthogonal. Nearness between
levels lives in the row index, which the decode reads, not in the cosine. A profile is a histogram over
many voxels, so a slight shift moves only part of its mass across an edge, and the cosine falls in
proportion. Where a question needs nearness in the cosine, a cumulative writing gives graded overlap with
exact rows: level L lights rows 1 to L. Whether any question needs it is measured on H2's bridge (OPEN).

**The re-encoding experiment, handed to layer 5 (Part 4 §4.3).** Ruling 5's "small perturbation and random
shift to re-encode the codebook on the same data" tests a random code. With exact rows, re-seeding the row
order changes no count and no cosine, so it tests nothing. What bites here is a typed shift of the quantizer's
edges, a fraction of a level on every edge of a ladder. A reading that changes level under that shift lay near
an edge. Layer 5 perturbs the edges together with the registration.

#### 3.5.4 The layout

*Table 3.7. Layout v1 (DESIGNED; versioned).*

| Facet | Banks | Rows | Written where | Layer |
|---|---|---|---|---|
| Tissue | per parameter (PD, T1, T2, FF), per scale | the level ladder (three rows at the digit) | where identified; silent elsewhere, cause kept beside | 1 |
| Deviation | per parameter | licensed; bright 1..m; dark 1..m | where the parameter's reference speaks | 2 |
| Signature | one | fluid, fat, fibrous, edema, intermediate, unsuppressed fat, unnamed, void | where two or more contrasts cover the place | Part 2 lens 3 |
| Law | per series family | the digit of r/σ; Table 3.4's types | where the series covers the place | 1 |
| Questions | per question (fluid? edema? tear? line? …) | present; excluded | where the question's lens reads | 3 |
| Orientation | fiber to B0; structure frame; direction to a lesion's center | θ bins; tear planes; ACL course (parallel, flatter, steeper); eight directions | fibrous zones; residual components | 1, 3, 6 |
| Coverage | one | per series family, measured or imputed; read, per question; scale | every place | 0, 1 |
| Context | zone; regime; the zone word's pairs | words | every place (cheap) | 0 |

**Profiles.** A zone's profile is the count table of its voxels' rows, with its footprint kept beside: each
voxel's place, values and digits (THESIS §6.5). A study's profile keeps each zone's table under the zone's
address, plus a whole-knee table, since "a bundle of bundles is a bundle" (THESIS §6.5).

**Banks per question.** The banks a question reads are named before the run, and "No bank carries a
weight" (THESIS §6.6). Adding a bank is not free: GenomeVault's third bank "*reduces* accuracy" when
composed into the primary decision (HDCSUB A.3). So each question's banks are measured on H2's bridge
(§3.5.6).

**Full, sparse, cheap** (THESIS §6.4). Residual places write every facet. Black places write the sparse
vector: tissue digits, the licensed row, the signature and coverage. A series on the degraded path writes
the cheap vector, its raw deviation and signature. Like is compared only with like.

#### 3.5.5 Capacity, size, and the precision ladder

Rows never collide, so the writes-per-dimension law does not apply: "Any number of writings superpose and
read back exactly" (THESIS §12.1). The layout has under 200 rows per zone. At 30 zones, a study's tables
come to about 25 KB and its packed signs to about 150 KB, and the corpus's tables to about 100 MB. The
vector itself is never stored: "For one comparison, then, the vector adds nothing a count table lacks"
(THESIS §12.1).

*Table 3.8. The precision ladder in physics space. This amends Part 2 §2.7, whose normalized-float rung
survives only on the degraded path.*

| Rung | Holds | Read by | Measured by |
|---|---|---|---|
| DICOM stored values, with rescale | the scanner's numbers | layer 1 | — |
| Tissue parameters, with σ | PD-ish, T1-ish, T2-ish, FF-ish | layer 2; lenses | leave-one-series-out; phantoms |
| z | deviation from the population | the black; the residual | make-or-break; false survival |
| Level row | the quantized reading (the digit at m = 1) | ledger; cosine; recall | H2's bridge; m raised only to keep a distinction the digit loses |
| Packed signs | a bundle's signs | ordering; shipping | never drops a case |

"A decision drawn more finely than its data is less correct, not more" (THESIS §12.4). The task is coarse:
"The project here...is meant to resolve "is knee" or "sad knee". MUCH more forgiving." (founder,
2026-10-02). So the ladder starts coarse and earns each finer rung. Density is measured, never inherited.
GenomeVault's ~21% was "born of the specific form I built in my GenomeVault project, to encode nucleotide
data. Not really a law of nature" (founder, quoted in HDCSUB F.3).

#### 3.5.6 Cases, and how layer 4 fails

**Cases, not prototypes.** Layer 8 (Part 5 §5.5) keeps cases one by one and never sums them (THESIS §7.1, §7.4).
`tools/lens_eval2.py`'s prototypes remain a data-layer instrument, never the decision (RECIPE §8). What
layer 8 needs from this layer is the exact decode, which names a near miss's one difference: "this bank,
this metric, so many more places below the middle" (THESIS §6.6). That gives the difference detection
Minsky "only sketched" (THESIS §7.6).

**How it fails, and how that is measured.**
- *A lost distinction,* the third falsifier (THESIS §13.3), failing H2's bridge (THESIS §1.4). It is
  measured on RECIPE §7's hard pairs: meniscal tear vs. intrasubstance degeneration; contusion vs.
  fracture; effusion vs. synovitis; MCL sprain vs. a normal MCL. Their profiles must differ beyond chance
  on named banks, and the decode must name where. Part 6 §6.2.1 runs the measurement on nine pairs
  (Table 6.2).
- *Silence miswritten.* Tests pin the three zeros. A licensed place writes the licensed row, an unread
  place writes nothing, and an orthogonal place writes only its read row.
- *A rung too fine or too coarse.* A change of rung is a new layout version, "measured before use", never
  "a silent change of type" (THESIS §12.4).
- *Drift.* Profiles of different layouts are never compared, and the comparison refuses.

### 3.6 What this Part hands on, the build order, and what stays open

**Handed on.**
- *To layer 3 (Part 4 §4.1–§4.2):* the hardness map's raw material (ε maps, magic-angle windows, noise-floor
  silences, partial-volume edge marks, ghost bands) and the question banks.
- *To layer 5 (Part 4 §4.3):* its two handles, the quantizer's edges and the study's transform.
- *To layer 6 (Part 4 §4.4):* the residual in physics space, and the tissue words that set a lesion-object's
  halo, such as an effusion's partial-volume rim.
- *To layer 7 (Part 4 §4.5):* x(λ) = (1 − λ)x + λμ over tissue parameters, and the trajectory byte's slot.
- *To layer 8 (Part 5):* the profiles, the regime cases, and the series as committee members, with imputed
  series marked and never a voice.
- *To layer 9 (Part 6 §6.1):* the law's σ, and never the header.

**Build order (DESIGNED).** Each step is measured before the next; the steps fall in Part 6 §6.6.3's
Phases 1, 2, 4 and 5.
1. Read the corpus's tags and inventories, without pixels: tag survival, inventory distribution,
   identifiable sets.
2. Rebuild the front end: stored values with rescale; one kept transform per study, carried to every series
   around a shared center.
3. Build the gain and decay specialists, on studies with a TE contrast, and run leave-one-series-out.
4. Run physics-space KneeDiff on T2-ish against raw KneeDiff on the fixed instrument, re-sweeping the detrend
   in both.
5. Build the ledger, which replaces `hdc_encoder.py` for every new consumer.
6. Build the zone word, and measure the skip-miss rate, and the work it saves in counts per study (§3.2.6),
   before any route is used.
7. Add the recovery and fat specialists, the region scale and imputation.

**OPEN.**
- Which tags survive anonymization, and which magnets are vertical-field.
- The corpus's inventories, and how often each term is identifiable.
- The size of the fast-spin-echo and suppression coefficients per regime.
- Whether the detrend survives in physics space.
- Each quantity's m, and whether any question needs cumulative writing.
- The header's percentile levels, and whether its routing saves work here, counted per study (§3.2.6).
- Whether the carrier's implementation is shared with the cell project. Ruling 6 bars only GenomeVault
  code.

## Part 4 — Seeing: exclusion, the hardness map, perturbation anchors, the loop, and the λ-trajectory (layers 3, 5, 6 and 7)

This Part specifies four layers of the design (BRIEF §5): exclusion lenses and the hardness map (layer 3),
perturbation re-encoding as the knee's anchors (layer 5), the loop on the residual (layer 6) and the
λ-trajectory (layer 7). Together they are how the knee is seen. They take the residual KneeDiff leaves (layer
2; Part 3 §3.4), the readings of the lenses one per law term (Part 2, Tables 2.8a–b), written in the exact
ledger (layer 4; Part 3 §3.5), and hand the society (layer 8; Part 5) a kept record of typed readings,
committed lesion-objects and structure trajectories. They narrow, encode and propose; none of them decides a
finding (THEORY Part IV, Law 4).

One stance runs through all four layers:

> "Knowing where something is NOT is extremely useful for knowing where something is!" (founder, 2026-10-02)

Each layer turns what would be called a failure into a typed reading. An exclusion is a positive reading of
something else. A silence in health is a mark on the hardness map. A reading that flips under a small step
names the axis it depends on. A structure whose confidence falls as its prior is applied raises a question
of placement before it raises one of pathology. Nothing is discarded unexplained (THESIS §4.2).

### 4.1 Exclusion: how a lens says "not here"

The thesis's warrant: "a reading that is poor at finding a signal can be reliable at saying where the
signal is not. What something is not tells what another thing is, so what the lenses set aside is defined
away, not lost" (THESIS §3.6). The idea began as a background found by exclusion in the puzzle work
(THESIS §13.4), and GenomeVault's banks carry it in their alphabet: "+1 = match, −1 = anti-match, 0 = "look
elsewhere"", with each bank measurement read as a door opened on the hypothesis space (HDCSUB A.3).

**The exclusion mark.** An **exclusion mark** is a −1 written on one finding's question at one place, by a
lens entitled to write it. Four conditions make it a mark:
1. *A positive reading.* The lens saw something, such as bright fatty marrow. A missing positive is never
   an exclusion: "The negative is a fact of its own, given or confirmed by the expert, never inferred
   because a positive match is missing" (THESIS §7.3), and a refusal "says the question was not resolved
   there, never that nothing is there" (THESIS §10.3).
2. *A law names the incompatibility.* The signature law (L2) or a pathology law (L4) says the thing seen
   cannot coexist with the finding at that place.
3. *The lens can read there in health.* A lens the hardness map marks blind at a place cannot exclude at it
   (§4.2).
4. *No law-given censor has removed the evidence.* The magic-angle and fat-suppression censors come
   first (Part 2, lenses 4 and 5).

**Seniority** (THESIS §4.2). Excluders act in order of authority. The senior is "narrow and knowably
correct: it does not fire wherever light is faint, but where it fires it is right, and it decides alone".
T1-bright marrow is the senior excluder of edema, because the T1 pathway separates fat from edema without
relying on fat suppression. This is SYNTH's complementary sparsity, "Use AT pathway for high-confidence
rejection" (SYNTH Part III), moved to bone. FS-dark marrow is a junior excluder: a susceptibility void can
also make marrow dark. It refines only where the senior keeps the place.

*Table 4.1. The brief's four exclusions (BRIEF §5, layer 3), as rows of Part 2's lens tables.*

| Finding excluded | Excluder (Part 2 lens) | Law | Not entitled where |
|---|---|---|---|
| Contusion (edema) | T1-bright marrow (3, 14) | L2: fat is T1-bright, edema T1-dark | red marrow; no T1 series; T1-bright blood products |
| Ligament tear | a continuous dark band along the centerline (10), fibrous by the ligament's own population reference | L2: fibrous tissue is dark on every sequence, but the normal ACL is striated, with intermediate signal on PD and T1 near its tibial insertion, and less dark than the PCL; so brightness beyond the ligament's own reference needs a cause | the ACL's femoral attachment on sagittal (partial volume with the condyle) |
| Meniscal tear | a dark meniscus with no deviant signal touching a surface (7) | L4: the two-slice-touch rule | fewer than 2 covering slices; the meniscus–capsule junction; pseudotear sites; the magic-angle window |
| Effusion | every recess empty (12) | L4: joint fluid pools in the recesses | a recess cut off by the field (Coverage, lens 6) |

Whether intrasubstance meniscal signal without contact excludes the Meniscus findings depends on the label
definition (Q3): if degeneration counts as positive, row 3 excludes only "tear" (Part 2, Table 2.8b row 7).

**The partition.** For each finding F and zone Z, every place falls in exactly one of three parts:
**excluded** (at least one entitled excluder fired), **blind** (no lens entitled to speak for or against F
can read there), and the **remainder** (readable and not excluded). Findings are sought only in the
remainder. A body lying in F's excluded part is censored for F, absolutely, as a law-given censor is
(THESIS §7.5). It stays in the residual for every other finding, since an exclusion deletes nothing
(THESIS §4.2).

**The Monty Hall move, kept as context, never as numbers.** A lawful removal changes what the rest means
(THESIS §4.6). When most of a zone is excluded for F, a deviation in the remainder means something different
from the same deviation in a zone nobody examined. The thesis is exact about how much of the game carries
over: "The residual inherits the principle, never the numbers" (THESIS §4.6). So no formula raises a
probability because doors closed. Each candidate instead carries its **exclusion context** as a facet of how
it came out (THESIS §5.6): which excluders fired around it, and the excluded and blind shares of its zone for
each finding. Recall then compares candidates only with cases from like contexts (layer 8; Part 5 §5.5).
**Departure:** SYNTH Layer 0 calls its bank-agreement check a "Genomic Monty Hall" and turns agreement counts
directly into confidence levels (SYNTH Part IV, Layer 0). The knee keeps the context and lets confirmed cases
say what it means.

**The mechanism (DESIGNED).**
- *Reads:* every lens's reading at every place (Part 2, Table 2.8a), the hardness map's status there
  (§4.2), and the censors.
- *Computes:* for each finding and zone, the three-way partition and its shares.
- *Emits:* exclusion marks, written in the ledger as −1 on the finding's question (layer 4; Part 3 §3.5.3); a
  remainder mask per finding; and the exclusion context of every candidate.
- *Licensed by:* L2 and L4 (each excluder names its law); THESIS §3.6, §7.3, §7.5; founder ruling 3.
- *Fails:*
  - by an excluder wrong in a way its law did not foresee: subacute blood is T1-bright, so it would
    "exclude" a hemorrhagic contusion;
  - by excluding where the lens is in fact blind (a wrong hardness map);
  - by a misregistered zone boundary that lets one tissue's excluder speak in another.

  In BUILT code an exclusion cannot yet be written: `ternary_cell` in `src/RSNA_Knee/hdc_encoder.py` writes
  the licensed voxel as 0 and `encode_zones` drops every 0, so "excluded", "at the middle" and "never read"
  share one symbol (Part 2 §2.8, rule 3; Part 3 §3.5.1, item 4). Layer 4 writes them apart (Part 3
  §3.5.3).
- *Measured by:* lesions planted in true normals with their full signature. Where a lesion is planted, its
  excluders must stop firing; a planted lesion that ends up excluded names a wrong excluder. On gold, a
  positive finding whose lesion lies in its own excluded part is a near miss, kept with its named difference
  (THESIS §7.6).

### 4.2 The hardness map: where the views go blind in health

**The founder's reframe.** The clinical committee's four encoders failed together at 2 positions where
independence predicted 0.00006, a ratio of 36,210 (COMMITTEE §4.2). The committee's authors read the
cluster as a defect turned to use: errors "cluster at inherently difficult positions. However, this is
actually beneficial: these positions can be detected and flagged" (COMMITTEE §4.2). Their flagged
positions share a structural type: N bases, GC content of 70–78%, homopolymers and repeats (COMMITTEE §6.2,
§11.2). The founder reads it further:

> "It's *information*--"hey, I now have an EXTREMELY divergent signal that differentiates parts of the
> genome in a structurally-relevant way, and can be used to provide information about how that bit of DNA
> actually behaves!"" (founder, 2026-10-02)

TIERED supplies the second half. At margin 0, errors (about 81%) are predictable from the vector's own
features: Cohen's d is 1.95 for its total magnitude, 1.45 for local GC. At margin 2, errors (about 25%) are
not: they spread uniformly across GC content, base type and magnitude, with d below 0.3 (TIERED §3.1.1).
The first kind of failure tells about structure. The second is entropy, for that set of lenses.

**Definition.** The **hardness map** is a template-space record, built once from true normals, of where
each view goes blank, misleads, or fails together with other views in health. It reads no study. It is a
structural lens: it says where each view's silence or false reading is to be expected. Its expected
features in the knee are known to radiology: the meniscus–capsule junction, partial-volume edges and
fibrous tissue near the magic angle (BRIEF §5, layer 3), and the pseudotear sites (Part 2 §2.10).

**Construction (DESIGNED; how to build it was OPEN, BRIEF §7).**
1. *The population.* Held-out true normals, per regime key and series type (Part 2 §2.9). Never the
   studies squashed into the reference, whose own residuals are biased low (the caveat recorded in
   `tools/lens_eval2.py`). Today there are 30 held-out true normals, and 799 all-negative candidates
   harvested by the report parser, 80 of them fetched (LADDER). The population is split into a building
   half and a checking half.
2. *The readings.* Every lens runs on every series of every normal (Part 2, Table 2.8a), and so do layer 5's
   cheap perturbations (§4.3). Part 3 adds the law's typed residual: ghost bands, partial-volume edge marks,
   noise-floor silences, the suppression map and the magic-angle windows (Part 3, Table 3.4). Zones are
   constant index masks in template space (ZONES, item 2), so every reading lands on a template coordinate
   and counts accumulate per place with no bookkeeping.
3. *The counts,* in whole numbers (THESIS §12.2), per place, lens, series type and regime:
   - readings made, and silences by cause;
   - "for" readings, per finding the lens can count for;
   - exclusions;
   - flips under perturbation;
   - for each set of independent series, joint "for" readings.
4. *The rates,* each with a bound computed from its count, as THESIS §11.4 bounds its measured means:
   - the blank rate;
   - the false-for rate (any "for" reading on a true normal is false by construction);
   - the disagreement rate between series;
   - the flip rate;
   - the **joint-failure ratio** κ: the joint false-for rate across independent series, divided by the
     product of their marginal rates. κ is the knee's 36,210×.

   Where a count cannot bound a rate, the entry reads "insufficient", never zero (THESIS §4.8, decide or
   abstain).
5. *The admission test.* This is TIERED §3.1.1 made a rule. A failure enters the map only with a
   **law-named predictor** that separates the normals that failed from the rest, reported with its effect
   size as TIERED reports d. The candidate predictors are:
   - the fiber's angle to B0, computed per study (the magic angle, L2);
   - distance in slices to the zone boundary (partial volume, L3);
   - the type of the law's residual at the place (Part 3, Table 3.4);
   - the atlas vote fraction (ZONES, Rank 4);
   - the flexion word;
   - the regime word.

   A predictable failure is structural information: it goes on the map with its cause. A failure that
   concentrates at a place with no law-named predictor does not go on the map. It is either a lesion the
   "normals" carry but their reports missed (the parser that harvested them scores 77.7% against gold;
   LADDER), or a law the design lacks. It goes to the founder's eye and to gold (Q5). Failure that is
   uniform and unpredicted, like TIERED's margin 2, is entropy for these lenses. Law 5 then says to look for
   the missing information, a new lens or view, never for capacity (THEORY Part IV).
6. *The output,* per lens, series type and regime: a status volume and a table of expected rates,
   versioned with the template and the registration. The map lives in template space and dies with it, as
   every v1–v4 number died with its substrate (LADDER, substrate reset).

*Table 4.2. What the map says of a place, for one lens.*

| Status | Meaning | How a reading there is typed | Expected examples |
|---|---|---|---|
| **readable** | the lens speaks reliably in health | as written | femoral marrow on T1 |
| **blind** | the lens falls silent in health, for a named cause | its silence is the informational zero, neither for nor against (THESIS §6.3) | the meniscus–capsule junction on sagittal; a band thinner than the slice |
| **misleading** | the lens reads "for" in health at a rate a named cause predicts | its "for" counts only with concurrence from a series not misled there | the magic-angle window on short-TE series; the transverse-ligament pseudotear |
| **hard** | independent series fail together (κ well above 1) | the question is kept open there, as hardness information | junctions every plane cuts obliquely |

**How the society uses it.**
- *Typing silence.* A silence on the map is "blind here". A silence off the map is a deviation in its own
  right, a **hardness deviation**: the coil, motion or hardware made a readable place unreadable. It goes
  to the constraint reference (Part 1 §1.8), never to a finding.
- *Gating exclusion.* An exclusion counts only where its lens is readable (§4.1).
- *Dissenters, per place.* COMMITTEE found that two encoders were never the lone dissenter, and it breaks
  2–2 ties by trusting that pair, right 95.1% of the time (COMMITTEE §5.2–§5.3, §8.2). The map measures
  that reliability per place, in health. At a misleading place, a "for" reading needs a series the map
  says is not misled there.
- *Tiers* (TIERED §1.2; set out in full in Part 5 §5.4):
  - Tier 0: a zone whose header is quiet and whose map is readable is skipped, once Part 3's skip-miss rate
    allows it (Part 3 §3.2.6);
  - Tier 1: the series committee reads it;
  - Tier 2: where every series is blind or hard, the question stays open.

  COMMITTEE sends such positions to review, "UNCERTAIN - recommend re-sequencing" (COMMITTEE §6.3,
  §11.3). A test study has no reviewer, so the knee abstains there and records why (THEORY Part IV, Law 7).
- *Bounds and phantoms.* Readability enters each zone's λ-bounds (§4.5). Recovery of planted phantoms is
  always reported separately on and off the map.

**Departure.** COMMITTEE flags hard positions at run time and routes them to a person or to the
sequencer. The knee builds the map once, in health, and uses it as a lens on every study.

**The mechanism (DESIGNED).**
- *Reads:* true normals only, at teaching time.
- *Computes:* counts, rates with bounds, κ, and the admission test.
- *Emits:* the status volumes and expected rates of Table 4.2.
- *Licensed by:* founder ruling 3; THESIS §3.6, §6.3, §10.3; COMMITTEE §4.2, §6; TIERED §3.1.1.
- *Fails:*
  - with too few normals in a regime, it marks as blind places that are only unseen. A spread from few
    references has t-tails: n = 20 inflates P(|z| > 3) about 2.8 times (VERDICT). The regime key falls
    back to its parent when a cell is thin (Part 2 §2.9);
  - "normals" with unreported lesions mark common lesion sites as misleading. The admission test is the
    guard;
  - misregistered normals smear hardness along boundaries. Layer 5's flips separate frame-bound failures
    from tissue-bound ones;
  - κ needs at least two independent series, and the build reads one (BRIEF §4), so κ is **OPEN** until
    the series arrive.
- *Measured by:*
  - replication on the checking half, within the bounds;
  - the position of κ's peaks: they should fall on the known pitfalls (pseudotear sites, magic-angle
    orientations). A peak anywhere else names a registration fault or new structure, and is examined;
  - phantoms: recovery off the map should be high, and failure on blind places should match the map's
    prediction;
  - gold: how many lesions at mapped places were recovered, with the concurrence the map required.

### 4.3 Perturbation anchors: a truth that survives a small step either way

**Where the anchors come from.** The cell thesis resolves three anchor time points in full and tests each
from both sides: "Time on both sides tests an anchor. A truth that survives a small step either way is
real. A false cell, one whose cause does not last, is unlikely to survive the steps around it, and less
likely with each further step" (THESIS §3.4; §1.5). A static knee has no time. It has a **frame**, the
registration, and an **encoding**, the quantizer, and the design steps it either way in both. "Real lesions
persist; edges and misregistration flip" (BRIEF §5, layer 5). The founder's source for the move:

> "I also do some WEIRD shit as experiments, like doing a small perturbation and random shift to re-encode
> the codebook on the same data with mild perturbation" (founder, 2026-10-02)

*Table 4.3. What is perturbed: the frame families R1–R5 and the quantizer families QZ1–QZ4.*

| Family | What moves | Magnitude rule | Cost | Source |
|---|---|---|---|---|
| R1 in-plane shift | the study against the reference and zones, A-P and S-I | ±δ and ±2δ, δ from the measured landmark error: 2.05 ± 1.30 mm propagated, about 1.5–2.5 mm after NCC refinement (ZONES), i.e. 2–4 voxels at 0.67 mm; set per zone, with 2δ capped below the zone's minimum lesion extent (rule 4 and its precedence, below) | cheap | Law 3; ZONES |
| R2 through-plane phase | the sampling phase along the 3.4 mm medial–lateral axis | fractions of a slice | cheap | L3 (partial volume) |
| R3 rotation | about the zone's center | the angle the landmark error subtends over the zone's length | cheap | ZONES |
| R4 registration seed | rerun `register_full` with a new metric-sampling seed | the optimizer's own scatter | expensive | BUILT parameter: `SetMetricSamplingPercentage(0.2, seed=1729)` (affine) and `(0.15, seed=1729)` (B-spline), `tools/register_and_export.py` |
| R5 template | register to another atlas | the template's bias | expensive | ZONES, Ranks 4–5 (not built) |
| QZ1 middle edges | the static middle's low and high edges | a fraction of a tercile | cheap | THESIS §6.2 |
| QZ2 deviation threshold | the z threshold | a fraction of the step between its sane values {2.5, 3, 3.5} | cheap | Part 2, Table 2.8a, lens 1 |
| QZ3 detrend scale | the detrend σ | within the v5 plateau, σ from 16 to 32 (AUC 0.67, 0.68, 0.66) | cheap | LADDER, v5 |
| QZ4 codebook seed | which exact rows carry which values | none: it must change nothing | cheap | THESIS §6.1 |

**Departure, and where the founder's codebook shift goes.** In GenomeVault a re-seeded codebook changed
which dimensions collided. Encoders on different seeds therefore failed at different positions: overlap
fell from 1,728 of 1,728 errors to 3 of 1,869, and joint errors fell 373-fold (COMMITTEE §1.2, Appendix
B.1). The exact ledger has no collisions: any two different rows "cancel exactly" (THESIS §6.1). So a
re-seeded ledger writes the same counts and the same cosines, and QZ4 survives only as a check: a seed
change that moves any reading is a fault in the ledger. Under exactness, the founder's shift moves to the
quantizer, the codebook "serving as a lossy compression of scalar intensity" (founder, 2026-10-02), where
a shift moves the edges at which intensity is cut (QZ1–QZ3). A quantizer shift is not vibe collapse (TIERED
§2.3), which its own results refute (HDCSUB F.4 #1). It cuts the same values at nearby edges. It does not
decode at a lower resolution.

**Rules for the magnitudes (DESIGNED; the values are OPEN, BRIEF §7).**
1. *Two-sided,* symmetric about the registered position. The anchor sits in the middle, never at a border.
   A one-sided step is the static form of an anchor at the movie's first or last time point, which "would
   assert a base truth that nothing could warrant" (THESIS §3.4).
2. *Two magnitudes,* δ and 2δ: the thesis's two spans (THESIS §3.4).
3. *Set by measured uncertainty,* never chosen to separate gold (Part 2 §2.8, rule 2). The frame is
   stepped by the registration's own landmark error, the quantizer by a fraction of its plateau.
4. *Below lesion scale in the plane.* A step that can carry a lesion out of its zone tests the zone, not the
   lesion. The coarse B-spline mesh keeps the same principle (LADDER, standing findings).

*Precedence.* Rules 3 and 4 can collide. δ from the measured landmark error, about 1.5–2.5 mm after NCC
refinement (ZONES), puts 2δ at about 3–5 mm: the lesion laws' own minimum extents (Part 2 Table 2.8a, lenses
14 and 15: {3, 5} mm), and the scale of thin structures such as the MCL band and the menisci. Rule 4 governs.
δ is set per zone, and 2δ is capped below the zone's minimum lesion extent in the plane, and below one slice
through-plane. Where the zone's measured registration error exceeds that cap, the frame test cannot step by
the error without testing the zone: that zone's frame test is reported as zone-bound, and s there is read only
against phantoms of the same size and zone.

**What it computes.**
- The **stability fraction** s: the share of the K perturbations under which a reading keeps its word.
  For a candidate, the word is "still a body with the same signature"; for a digit, the same digit; for a
  trajectory, the same word with λ* within its bound. s is reported overall and per family. It is a graded
  score in [0, 1].
- The **flip-axis profile**: the share of flips in each family (Table 4.4). The axis along which a reading
  flips says what it depends on.
- The **two-span ratio** of a continuous reading r: |r(+2δ) − r(−2δ)| divided by |r(+δ) − r(−δ)|. In time,
  "over the longer span a steady drift doubles, while a random wander grows by only about √2" (THESIS
  §3.4). Here a ratio near 2 marks a gradient across an edge: a systematic, frame-bound reading. A change
  that does not grow with the step is the reading's own noise, or a stable interior. The two are told apart
  by the size of the change against the reading's own uncertainty (LAA §10). The ratio a random field
  gives depends on its correlation length, which is measured on true normals.
- The **sandwich status** (THESIS §11.5): "a quantity held between two that agree must agree with them".
  - *Held between:* present at −δ and +δ, absent at the registered position. This is an inconsistency, and
    it is answered only when an answer is shown: a quantizer edge (the continuous value falls just short),
    a slice-phase dropout (shown by R2), or an outlying registration (shown by R4). With none shown, the
    step abstains and the inconsistency is recorded, as the thesis never infers "it died" by ruling out the
    others.
  - *Isolated:* present at the registered position only. The reading is bound to one alignment. It stays a
    candidate with s near 1/K and is never committed on its own.

  RECIPE §6 keeps a second sandwich across planes: "two views in place of two anchors". That one is
  concurrence of independent evidence, and belongs to the committee (layer 8; Part 5 §5.3).

*Table 4.4. What a flip's axis says.*

| Flips under | Stable under | Reading |
|---|---|---|
| R2 only | R1, R4, QZ | partial volume at a slice boundary (L3). Read against phantoms of the same thickness; on the hardness map if it recurs on normals |
| R1 or R3 | R2, QZ | an in-plane edge: the reading depends on where a boundary falls (cartilage and fluid, ligament and fat) |
| R4 or R5 | the cheap families | the registration itself is unstable here: a constraint-reference reading, escalated |
| QZ1–QZ3 only | every frame family | a weak deviation on a digit edge. Magnitude, not place, is in question; the continuous value is kept beside the digit (THESIS §6.2) |
| nothing | everything | persistent: a property of the tissue, or a confident joint error |
| everything | nothing | nothing a law holds there |

**Independence.** Perturbations of one series are not committee members. Encodings of the same data fail
together: one codebook gave about 100% correlated errors (COMMITTEE §1.2), independence is a gate to be
measured (HDCSUB F.4 #4), and "Independence must come from different evidence, not different encodings"
(RECIPE §7). So s measures robustness. It is never counted as votes. A confident joint error, every series
and every jitter agreeing and wrong, passes this layer as it passes layer 1 (BRIEF §5). Its defenses are
gold read as near misses, and the censors (layer 8; Part 5 §5.6; Part 6 §6.5).

**Cost.** Work is spent in proportion to change (THESIS §12.6). The cheap families run only inside candidate
boxes and structure zones, padded by 2δ: a resample, a requantization and a re-read. The expensive families
(R4, R5) run only on escalation:
- a λ-trajectory alarm (§4.5);
- a committed object that flips under R1 or R2;
- a zone the hardness map calls hard.

**The mechanism (DESIGNED).**
- *Reads:* the readings of candidates and structures; the registration's parameters; the quantizer's edges.
- *Computes:* s, the flip-axis profile, the two-span ratio and the sandwich status.
- *Emits,* per reading, all four, to:
  - the commit (layer 6; §4.4);
  - emission, where s is one of the keys that order a register (layer 9; Part 6 §6.1.4);
  - the hardness map (flips on normals);
  - the constraint reference (flips under R4 and R5).
- *Licensed by:* THESIS §3.4, §11.5; Law 3, under which the bounded utility's uncertainty is measured; L3;
  founder ruling 5.
- *Fails:*
  - steps too small make everything stable, and no test was run; steps too large make small real lesions
    flip;
  - a thin real lesion, such as a meniscal tear one slice thick, flips through-plane by its nature. Its s is
    read against phantoms of the same size and zone, never as an absolute. The two-slice-touch rule is that
    object's own persistence test (L4);
  - a perturbation tangled with the lesion: a large effusion moves the registration metric's landscape, so
    reruns differ in its presence, and s is inverted;
  - quantizer flips that only track |z|, so that s restates magnitude.
- *Measured by:*
  - true normals: a stable "for" reading on a true normal is a confident false positive, and goes to the
    hardness map;
  - phantoms planted at known size, zone and amplitude: s should rise with size and amplitude, an amplitude
    response curve as VERDICT requires of the make-or-break instrument;
  - normals deliberately misregistered by known amounts beyond δ: flips should follow the shift's axis, and
    the registration alarm should fire (§4.5);
  - the information test: s enters emission only if it adds to the rank already given by |z| (H2's bridge,
    measured, never assumed; THESIS §13.1, step 7).

### 4.4 The loop on the residual: commit, take out with the halo, read again

H1's third move is elimination under law: "each \<object> found is taken out of the data whole, together
with the signal it spreads around it. What is left is not noise but the same structured problem with added
context, read again until nothing \<object>-shaped remains" (THESIS §1.4). In the knee the loop's \<objects>
are **lesion-objects**, present or absent and living in the residual: fluid collections, marrow edema,
fracture lines, signal inside a tear (RECIPE §1; Part 1 §1.5). Structures, always present and placed by the
atlas, are read by the λ-trajectory (§4.5), and are never taken.

**Outside precedent** (BRIEF §4). Crowded-field photometry fits each star with the point-spread function,
subtracts it, and searches the subtracted frame for the stars the bright ones hid (DAOPHOT; Stetson 1987).
Radio astronomy's CLEAN subtracts the instrument's beam at the brightest peak of the residual, round after
round (Högbom 1974). Both are this loop with a known spread function, and both fail the same way: an
imperfect spread function leaves rings and holes. THESIS §4.5's post-take check is the guard against
exactly that.

*Table 4.5. The round, from cells to knees.*

| Stage (THESIS) | Cells | Knee (DESIGNED) |
|---|---|---|
| 0, the pictures (§4.1) | four focus lenses, each at its own depth; the composite; the cheap readings | each series' residual and lens readings (Part 2); the composite, with the reading series kept as a number (Part 2 §2.7); the headers and field priors (layer 0; Part 2 §2.9; Part 3 §3.2) |
| 1, the black (§4.2) | the camera's dark, then the local haze, by seniority | the population's license (KneeDiff, layer 2; Part 3 §3.4.3) as the senior; the low-frequency trend as the junior (`detrended_residual_map`, BUILT); per finding, the exclusions of §4.1 |
| 2, the bodies (§4.3) | contiguous regions; specks narrower than 2 µm cleared; no parting | contiguous same-sign deviant regions per zone; specks below the lesion law's minimum extent cleared (Part 2, lens 14: {3, 5} mm); no parting before the take |
| 3, the lenses speak (§4.4) | lenses at one depth correct each other's borders; each cell counted once by its column | two contrasts in one plane read it two ways (the signature, L2); two planes are the knee in three dimensions; each object counted once in patient space (L1; RECIPE §6) |
| 4, commit and pull-out (§4.5) | concurrence of lenses; the take with its halo | concurrence of independent series; the take with the halo its own law gives |
| the residual, read again (§4.6) | the site search; reaching down | the site search, where the composite points; reaching inside a taken object |
| the last look (§4.7) | one word for each object left | one word for each object left, with one word added for the knee's censors |

**Commit by concurrence** (THESIS §4.5). Each series that can speak at a body, by the Coverage lens and the
hardness map, is read apart, "never pooling them into one score". Where the series concur, the object is
taken and the concurring readings recorded. Where they disagree or abstain, it stays for the next round,
which reads it from scratch. A narrow reading counts one way only: the Line lens counts only for. Agreement
counts only between voices whose independence has been measured (THESIS §6.2; RECIPE §7). **Today** the
build reads one series per study, so every concurrence has a single voice (BRIEF §4). The loop's mechanics
can be built and tested on phantoms with one series, but its takes carry the word "single voice", and
commit by concurrence waits for the series committee (layer 8; Part 5 §5.3).

**The take removes the object's own signal.** In the thesis, the take subtracts "the light the
inverse-square law says the cell spreads", so that "what remains is the slice's haze, or another cell's own
light. So a cell stacked beneath survives" (THESIS §5.5). The knee's take removes what the object's law
says the object contributes. It leaves the population's expected value, the knee's equivalent of the
slice's haze, "so that no false edge appears" (THESIS §4.5), or another object's own signal.

*Table 4.6. Lesion-objects, their halos, and what their removal reveals.*

| Lesion-object | Its own signal (law) | Its halo (law) | What the take reveals |
|---|---|---|---|
| Effusion | fluid signature, FS-bright and T1-dark, filling a recess (L2, L4) | partial volume at the recess wall: about one slice through-plane, about a voxel in-plane (L3) | the border of Hoffa's pad free of the fluid's partial volume (the fat-pad surrogate for synovitis); intermediate-signal tissue lining the recess that the fluid model does not explain; a lobe posteromedially, the Baker's neck |
| Marrow edema (contusion) | a smooth, geographic field of edema signature in bone (L4) | its feathered margin into normal marrow | the fracture line: a thin, dark, linear component inside it, reaching cortex (L4), read by the Line lens (Part 2, lens 15) |
| Baker's cyst | a rounded collection between the medial gastrocnemius and semimembranosus (L4) | partial volume at its wall | its neck to the joint (Neck lens, 13), or fluid tracking beyond it |

Without contrast, synovitis is read through surrogates: the fat-pad signal and MOAKS's effusion-synovitis,
in which fluid and thickened lining share one score (RECIPE §2, L4). The take separates the two only as far
as their signatures differ (L2), and how far that is gets measured on gold Synovitis.

**The post-take check.** "Once a cell is out, its place should look like its surroundings. A ring means too
little came out, a hole too much, and a lobe a second cell; a patch darker than the camera reads with no
light is impossible" (THESIS §4.5). In the knee, a place emptied by a take should read as licensed against
the population. The check needs no label.
- A **ring** is a same-sign deviation hugging the take's border. The halo was too narrow. After an effusion
  a ring is the confound synovitis must not inherit: a false rim.
- A **hole** is an opposite-sign deviation inside the footprint. Too much came out. After an effusion it
  erases the lining; after an edema it erases the line.
- A **lobe** is a same-sign residual with its own center, joined to the take. It is a second object: the
  Baker's neck, a second contusion, a loculated collection.
- An **impossible patch** is a value the signal equation cannot produce, such as an implied proton density
  below zero (Part 3 §3.3.2). The take's model is wrong.

A ring or hole sends the object back with its halo recomputed from its law: the slice geometry in the
headers sets the partial-volume rim, and no knob is tuned. A ring that survives the lawful halo is tissue,
not residue, and is kept as a candidate. There is no noise.

**Reading again.** The next round recomputes only the lenses whose zones a take touched (THESIS §12.6). By
the Wayfinder thesis the residual is "the same kind of problem with added context" (THESIS §4.6).
- *The site search* (THESIS §4.6). Wherever the residual's composite still shows a bounded deviation that no
  lens claims, wider than the lesion law's minimum, there is a site. The lenses that can speak there are
  asked, in a small block across all series. Where none speaks, nothing is taken, and the site is kept as
  "unexplained" (Part 1 §1.7). In teaching, the every-finding agency (Part 5 §5.2) sends the search back to
  look again: "the report says this knee has a Baker's cyst" means keep looking (RECIPE §5). It adds and never
  trims.
- *Reaching inside* (THESIS §4.6, reaching down). Within each taken object's footprint, what remains is read
  for an object of another kind nested in it: above all, "reaching inside committed edema for a fracture
  line" (RECIPE §4). The order is the law's: the smooth container first, then what it held, as the thesis's
  second hump stands out only once the first is out with its halo.
- *The last look* (THESIS §4.7). Each object still standing is read once and takes one word:
  1. part of a taken object (its rim or blur);
  2. smaller than any lesion law allows;
  3. no sane shape for a lesion of its zone, such as a thin sheet along a zone boundary: a frame edge;
  4. no deviation of its own: the trend's residue;
  5. explained by a law-given censor (the magic angle, failed suppression). The knee adds this word because
     its instrument has known artifacts;
  6. a lesion-object of its own, taken as a candidate.
- *The emptied box.* "The loop ends when a round takes nothing; a guard on the number of rounds is a
  reported safety, never the stopping rule" (THESIS §4.7). The emptied box is a law check. It supports and
  never establishes (THESIS §4.8; RECIPE §6).

**The cells result, as evidence for H1.** The founder's report of results not yet in the thesis text (BRIEF
§3, item 7; Part 1 §1.3) is that 100% of annotated nuclei were captured cleanly; that the loop ran 14–16
rounds to empty the box, with every annotated cell out in rounds 1–3; that cleanly resolved positions lay
under 2 µm from the annotation; and that the full pipeline is not yet complete. The result supports H1's claim
that a structure built from the laws resolves most of a picture cheaply: the plain objects come out first, and
the later rounds empty what is left. It does not yet show precision, since the clean-up and the agencies are
unfinished. For the knee, the analogous figures are measured, never assumed: rounds to empty each study, the
round in which each gold lesion comes out, and what the rounds after the third take.

**The mechanism (DESIGNED).**
- *Reads:* each series' residual; the lens readings; the exclusion marks and hardness map (§4.1–§4.2); the
  stability fractions (§4.3).
- *Computes:* bodies, commits, takes with halos, post-take checks and re-reads, to the emptied box.
- *Emits* the kept record of findings (THESIS §4.8):
  - every taken object, with its footprint per series, signature digits, halo model, round, concurring
    readings, exclusion context, stability fraction and post-take result;
  - its **route**: the first pass, the site search, reaching inside or the last look. The route is a
    physical fact (THESIS §5.6): a collection taken in round 1 and one found by the site search after an
    effusion's take are different objects;
  - every candidate, and every decision with what was known before it;
  - the residual.
- *Licensed by:* H1; THESIS §4.1–§4.8, §5.5; L1–L4.
- *Fails:*
  - a wrong halo leaves rings or holes (above);
  - a container's take could swallow what it holds. The halo's law bounds it (no wider than the slice
    profile through-plane), so it cannot erase tissue wider than that bound;
  - single-voice commits (today);
  - a loop that does not end; the guard reports it;
  - the Monty Hall move used as numbers (§4.1).
- *Measured by:*
  - phantoms: effusions with and without planted synovial thickening, and edemas with and without planted
    lines, which are LENS Phase 4's edge cases moved to the knee. The measures are ring, hole and lobe rates,
    and recovery of what each take should reveal;
  - true normals: any take is false, and is mapped by zone onto the hardness map;
  - gold: every gold-positive finding should be explained by a committed object (the every-finding agency,
    layer 8; Part 5 §5.2);
  - the round counts above.

### 4.5 The λ-trajectory: an explicit peak, and what it reduces to

> "We just need to build the right set of laws and lenses in this domain, and "KneeDiff" […] and the
> λ-trajectory are just the first and most elegant of them" (founder, 2026-10-02)

The genomic detector sweeps λ, how hard a lens's prior is applied (0 = raw data only, 1 = full
consensus), and reads the shape of the confidence curve (LENS Phase 5; SYNTH Part III). HDCSUB B.3 records
it as "the unifying signal" of GenomeVault's intelligence layer, with its three-way distinction between an
encoding error, a real variant and an input error. THEORY gives the knee's reading. A monotonic
increase "matches the normal consensus → nothing there". A peak-then-drop means "the region IS structurally
this thing AND deviates from its normal consensus → the finding present … the intermediate-λ peak is
exactly "structurally ACL, but abnormal." Peak height = confidence". A monotonic decrease is the "wrong
lens" (THEORY II.5).

**The mechanism gap.** These findings were verified this session (BRIEF §4), and the code was read
first-hand in the GenomeVault public tree.
1. *The overlay is additive.* The public decoder applies the lens as `chunk + lens_alpha*lens`, with a
   fixed `lens_alpha = 0.3` (`decoders/lens_aware_decoder_CORRECTED_3TERNARY.py:244`, `:299–305`), and
   decodes by dot products (`:337–339`). Each bank's similarity is therefore affine in λ:
   s(λ) = s(0) + λ·⟨lens, q⟩/D. An affine function on [0, 1] peaks at an end, never inside.
2. *Any interior peak comes from a later nonlinearity.* The public code has four: the norm-ratio weights
   (`:343–351`), the clip on the hinge term (`:354–359`), the argmax (`:369`) and the normalizer
   (`:370–371`). None was designed as the peak.
3. *The normalizer is degenerate.* Line 371 reads `confidence = scores[best_nuc] / total_score if
   total_score > 0 else 0.25`.
   - With magnitude weighting, A + T = 2·min(s_hinge, 0) and G + C = 2·max(s_hinge, 0), so the total is
     exactly 2·s_hinge. The confidence is 0.25 whenever s_hinge ≤ 0, and grows without bound as s_hinge
     approaches 0 from above.
   - Without weighting, the ± pairs cancel and the confidence is always 0.25.

   Both identities were checked numerically on random ternary banks this session.
4. *A second engine uses a second confidence.* The SIMD engine takes the maximum minus the median of the
   same four scores (`query/lens_aware_simd_query_engine.py:1068–1118`). It finds λ by a ternary search
   (`:1120–1164`), which presumes the curve has one peak: the shape the trajectory is meant to measure.
5. *SYNTH's decoder labels without measuring.* It sweeps only when its first pass, at λ_max, has confidence
   below 0.7. Otherwise it returns MONOTONIC_INCREASE unmeasured (SYNTH Part V,
   `LensAwareTrajectoryDecoder`).
6. *The classifier's thresholds are hand-set.* A half's mean gradient must exceed +0.02 or fall below −0.02,
   and a peak must drop by more than 0.1, over an 11-point sweep from λ_min to λ_max (SYNTH Part IV, Layer 3,
   `analyze_trajectory`). SYNTH expected about 95% MONOTONIC_INCREASE, 4% PEAK_THEN_DROP and 1%
   MONOTONIC_DECREASE (SYNTH Layer 3; Part VIII). E10 measured 62.0% AMBIGUOUS, 31.5% PEAK_DROP, 5.1% MONO_UP
   and 1.3% MONO_DOWN (HDCSUB F.2).

Read with "there is no noise", E10's 62% AMBIGUOUS is information about the instrument, not the genome: a
classifier whose classes were drawn before the trajectories were measured did not carve them. So the knee
measures its shapes before it names any (BRIEF §4), and builds its peak by construction. RECIPE asked which
nonlinearity GenomeVault uses (RECIPE §11, Q2). The public tree's answer is that none was designed, and the
founder's ruling frees the design to make its own: "don't worry about trying to actually use the code from
GenomeVault. The ideas are elegant, the encoding is genuinely primitive." (founder, 2026-10-02)

**The construction (DESIGNED).** Take an always-present structure S, read over its own tight zone in the
plane that holds it (L3; Part 2 §2.10's tubes, bands and horns).
- z_v is the KneeDiff residual at voxel v of S: BUILT as `residual_z` (`src/RSNA_Knee/kneediff.py`) and
  `detrended_residual_map` (`src/RSNA_Knee/platonic_reference.py`), in physics space once layer 2 is built.
  In residual units, the blend x(λ) = (1 − λ)x + λμ is z(λ) = (1 − λ)z.
- p̂_S is the mean of ‖z‖² = Σ_v z_v² over S, taken on held-out true normals. It is the structure's normal
  scatter energy, measured once as a static middle is (THESIS §6.2), never fitted. It absorbs the voxels'
  correlation and the reference's t-tails (VERDICT).
- **identity(λ) = exp(−½ (1 − λ)² p̂_S).** It measures how much of the reading's normal scatter the prior
  has replaced, so that the blended reading becomes S as normal knees have it. It rises to 1 at λ = 1, the
  same for every study: it is what the prior offers.
- **fidelity(λ) = exp(−½ λ² B)**, with B = ‖z‖² − p̂_S. It measures how much of this study's excess
  deviation survives the blend. It falls from 1, faster the more the study deviates: it is what the data
  allows.
- **confidence(λ) = identity(λ) × fidelity(λ) = exp(−½ [(1 − λ)² p̂_S + λ² B]).**

**The closed form.** The exponent is Stein's unbiased estimate of the risk of shrinking the residual toward
the reference (Stein 1981), with the measured p̂_S in the place of the voxel count. So the log of the
trajectory is a parabola fixed by one number per structure, ‖z‖²:
- the peak lies at **λ\* = p̂_S / ‖z‖²**, clipped to [0, 1]. This is the James–Stein factor (James and Stein
  1961), up to its p − 2. A sweep of the formula over a fine grid finds its maximum at λ*, as expected;
- the drop from the peak to λ = 1 is ½ B² / ‖z‖² when B > 0. Its scale under health stays bounded as the
  zone grows. With independent Gaussian voxels, ‖z‖² is χ² with one degree of freedom per voxel, and the
  drop's 95th percentile is about 2.3 to 2.6 log units for 50 to 1,000 voxels, growing slowly toward
  1.645² ≈ 2.71 as the zone grows (from the χ² quantiles, checked by simulation). The knee's own null is
  measured on true normals;
- the words become regions of that one number:
  - **MONO_UP** when the drop lies within its null range, measured on held-out normals. The deviation is no
    larger than normal scatter, and the prior can only help; every ‖z‖² ≤ p̂_S (where λ* = 1) reads so. The
    structure is normal as read, and nearly every true normal should read MONO_UP (Part 3 §3.2.6);
  - **PEAK_DROP** when the drop exceeds its null quantile and λ* is at or above the grid's first step: an
    explicit interior peak at λ*;
  - **MONO_DOWN** when the drop exceeds its null quantile and λ* falls below the grid's first step, 0.2,
    that is, when ‖z‖² exceeds five times p̂_S: the prior can only overwrite. The 0.2 boundary is the
    grid's resolution and separates words only; emission reads the continuous drop;
  - **AMBIGUOUS** when the instrument disagrees with itself: the closed form and the pipeline's sweep give
    different words (below), or a window's count cannot bound its statistic. Like E10's, it is information
    about the instrument. It is kept, and never counted as a vote.

The sweep over the grid {0, 0.2, …, 1} (LENS Phase 5; Part 2, Table 2.8a, lens 2) is kept beside the
closed form, in the spirit of THESIS §12.5's reference twin. It is run through the pipeline itself: blend
the zone, threshold again, read again. It tests whether the closed form describes what the pipeline does.
Where the two disagree beyond the grid's resolution, the digits are breaking the parabola, at a threshold
edge or in a saturated zone, and the disagreement is kept as a finding about the residual.

**What the closed form says, plainly.** One reference gives one number. PEAK_DROP and MONO_DOWN are
magnitudes of one statistic, not kinds of structure. λ*, the drop and the peak height are all monotone in
‖z‖², so a structure's trajectory ranks studies as ‖z‖² over its zone does: exactly above p̂_S, with ties
below it. Macro-AUC reads order only, so for the metric the single-reference trajectory adds no rank
information beyond its zone's sum of squared residuals. Its value lies in three other places:
- it names what kind of reading a structure gave, as a header word and λ* (layer 0; Part 3 §3.2.3–§3.2.4);
- it is computed per window, which a zone sum is not (below);
- with a second reference, it separates misplacement from deviation, which no single statistic can.

**Departure** from THEORY II.5 and BRIEF §5, layers 7 and 9 (Part 1 Table 1.3). They read PEAK_DROP as
"structurally ACL, but abnormal", MONO_DOWN as a misplaced zone, and the peak's height as confidence ("Peak
height = confidence", THEORY II.5). In the closed form identity(λ) is the same for every study, so the words
are bands of one magnitude, ‖z‖²/p̂_S, and "structurally S" is carried by the placement margin m (below). The
peak's own height falls as the deviation grows: the height above the right end, the drop, grows with the
deviation, while the height above the left end shrinks with it. **The drop is the reading emission uses**
(layer 9). Emission reads it through the windowed ratio Q = ‖z‖²/p̂_S, which keeps the drop's order and still
orders the studies where the drop ties at zero (Part 6 §6.1.3).

**The trap in the one language.** The natural first build would use the thesis's one comparison (THESIS
§6.6): identity(λ) = cos(x(λ), μ) and fidelity(λ) = cos(x(λ), x). This always gives a hump. With φ the
angle between x(λ) and x, and θ the angle between x and μ, the product is ½[cos θ + cos(2φ − θ)]. It peaks
where x(λ) bisects x and μ, at λ = ‖x‖/(‖x‖ + ‖μ‖). Its height there is (1 + c)/2, and its value at both ends
is c = cos(x, μ). This was derived and checked numerically this session. The prominence, (1 − c)/2, is
largest where c is smallest, so a misplaced zone would read as the strongest PEAK_DROP of all. The two
factors must be read against different references with different spreads: the prior's offer in the
population's units, the data's consent in its own. **Departure:** identity is never read against a bundled
prototype of positive cases, as `tools/lens_eval2.py` reads its findings today. THESIS §7.1 forbids the
sum: "a sum would lose which readings occurred together in each case".

**What one reference cannot say: placement.** MONO_DOWN says only that the deviation is too large for the
prior to help. Part 1 §1.8 names its causes: a misplaced zone, an input error, or an absent structure, as
after a complete tear. A second reference, the **reference displaced**, separates them.
- For each displacement Δ in the registration's failure set (layer 5's frame steps, extended to twice the
  measured landmark error), the same statistic is computed against the reference read at the displaced
  place: Q(Δ) = ‖z(Δ)‖² / p̂_S. The **placement margin** is m = min over Δ ≠ 0 of Q(Δ) − Q(0).
- m above its null range: S is best explained at its own place, and identity holds. A MONO_DOWN with
  identity holding and the constraint reference holding is a population-axis reading, a candidate absent or
  grossly abnormal structure, handed to the agency that reads S (layer 8; for a ligament or meniscus, the
  fibrous-structures agency, Part 5 §5.2), which alone decides (Law 4). The constraint reference holds when
  the NCC landmark check passes (ZONES, Rank 2) and the neighboring structures read MONO_UP.
- m below zero, so that some displaced reference explains S better, raises the **registration alarm**.
  - If the neighbors prefer the same Δ, the offset is coherent and the frame is off by Δ. This is LAA §9's
    test: where neighbors lock to one rhythm, the shared surface is trusted. The series is re-registered by
    layer 5's expensive families.
  - If only S prefers a displacement, the offset is local, or the lesion resembles displaced anatomy (fluid
    where cartilage would be). The reading is kept as a disagreement and settled by the NCC check at the
    nearest landmarks.
- An alarm that survives re-registration makes the zone unverifiable (Part 1 §1.8: constraints broken). It
  reads nothing there, and is never a finding.

Along λ the margin also has a closed form. It is read at λ = 0, on the data, because at λ = 1 the prior
supplies its own identity. **Departure:** SYNTH Layer 2 reads a large residual "in constrained position" as
an error and one "in variable position" as a real variant (SYNTH Part IV, Layer 2), the "sharp test" of
HDCSUB B.3. The knee reads a large deviation where the population is tight as pathology, and keeps input
error on this second reference (RECIPE §0; Part 1 §1.8).

**Windows.** A global fraction dilutes a localized lesion, where the peak local density does not (VERDICT).
The same holds here: a lesion of 15 voxels at z = 3 in a zone of 2,000 gives λ* ≈ 0.92, close to normal
(simulated this session). So the closed form runs per window inside each structure, as
`max_masked_window_density` does (`src/RSNA_Knee/platonic_reference.py`, BUILT). The structure's reading is
its most deviant window, and the null of that maximum is measured on true normals.

**λ-bounds per zone** (SYNTH Layer 1). GenomeVault bounds λ per family by silhouette: distinctive families
wide (F5_VERY_HIGH, +0.530: (0.3, 0.9)), overlapping ones narrow (F3_HIGH, −0.174: (0.0, 0.4)) (SYNTH Part
III). Layer 1 routes each chunk to its family's bounds, and planned to calibrate them by grid search (E03). As
printed, the table is assigned by hand: F1_VERY_LOW, at +0.382, shares (0.3, 0.9). A Bank3-variance gate, also
hand-set, widens or narrows the bounds at variances 1.0 and 3.0 (SYNTH Part III, Part V). **Departure:** the
knee keeps the idea and measures the bound. A zone's distinctiveness is how well its statistic separates
held-out true normals from phantoms planted in it, with its readability taken from the hardness map (§4.2).
Distinctive zones get wide bounds; variable or hard zones get narrow ones. Bounds clip the word only, never
the continuous reading sent to emission, since clipping would tie ranks.

**Statistical relatives.** λ* is the James–Stein factor, and the exponent is Stein's unbiased risk estimate.
The drop is a monotone function of ‖z‖²/p̂_S, the classical statistic for prior–data conflict (Box 1980;
Evans and Moshonov 2006). The closest Bayesian relative is the power prior (Ibrahim and Chen 2000; BRIEF
§4). Its weight on historical data plays λ's role, and when that weight is chosen to suit the current data
it falls as conflict grows, as λ* does. Nothing here is fitted: p̂_S is a measured mean over normals, and the
reference is the platonic squash (BUILT: `build_reference`).

**The word as a header.** E10 carried the pattern in two bits and λ_optimal in six (HDCSUB F.2; SYNTH Part
VIII). The knee writes the word and λ* as a header on the structure's vector (layer 0; Part 3 Table 3.1):
metadata, never a verdict. "The header is "metadata", not a verdict on meaning" (HDCSUB F.0), and "The headers
are cheap signals, not defining elements." (founder, 2026-10-02). SYNTH Part VIII made the trajectory "the
unifying signal", consumed everywhere. E10's routing speed-up was not delivered: 1.11× against an expected
1.55× (HDCSUB F.2). Any saving here is measured, in work counted per study (Part 3 §3.2.6).

**The mechanism (DESIGNED).**
- *Reads:*
  - each structure's z over its zone and windows, in its plane;
  - p̂_S and the null of the drop, from held-out normals;
  - the displaced references, the NCC check and the neighbors' words.
- *Computes:* λ*, the drop, the word, the placement margin m, the preferred displacement Δ and its coherence
  across neighbors. Each costs one pass over z per displacement; the sweep is a check.
- *Emits,* per structure, the readings above with the alarm, to:
  - the header (layer 0; Part 3 §3.2);
  - layer 5's expensive families, on an alarm;
  - emission, as the windowed drop (layer 9; Part 6 §6.1.3);
  - the constraint reference.
- *Licensed by:* L1 for the population reference; Law 3 and ZONES for the constraint reference; LENS Phase
  5; SYNTH Part III; THEORY II.5.
- *Fails:*
  - by dilution, which the windows answer;
  - by t-tails and correlated voxels, which p̂_S absorbs;
  - by reference members' residuals being biased low; p̂_S is taken on held-out normals only;
  - by the one-reference ambiguity, which the placement margin answers;
  - by a residual that does not follow the parabola, which the twin shows;
  - by counting one number twice. The windowed drop is emitted apart from the zone deviation count, so that
    layer 9 does not count one statistic twice. Its contribution beyond them is measured (H2's bridge;
    THESIS §13.1, step 7).
- *Measured by:*
  - held-out true normals: nearly all MONO_UP, with PEAK_DROP at the rate the null quantile predicts, and
    AMBIGUOUS rare;
  - phantoms: PEAK_DROP, with λ* falling as amplitude rises, an amplitude response curve (VERDICT);
  - deliberately misregistered normals: m below zero, a coherent Δ and the alarm, with no PEAK_DROP read as
    pathology;
  - gold: complete ACL tears should read MONO_DOWN with m above its null range.

### 4.6 What the four layers hand on

*Table 4.7. Outputs and consumers.*

| Layer | Emits | Consumed by |
|---|---|---|
| 3, exclusion | exclusion marks per finding; the remainder; each candidate's exclusion context | the loop (where to seek); the ledger (layer 4; Part 3 §3.5); recall (layer 8; Part 5 §5.5) |
| 3, hardness map | statuses and expected rates, per place, lens, series type and regime | the typing of every reading; the tiers; the dissenter rule per place; λ-bounds |
| 5, perturbation | the stability fraction; the flip-axis profile; the two-span ratio; the sandwich status | the commit (layer 6); emission (layer 9; Part 6 §6.1); the hardness map; the constraint reference |
| 6, the loop | the kept record: objects with their routes, candidates, decisions, the residual | the agencies, the every-finding agency among them (layer 8; Part 5 §5.2) |
| 7, λ-trajectory | λ*, the drop, the word, the placement margin, the alarm | the header (layer 0; Part 3 §3.2); layer 5's escalation; emission (layer 9; Part 6 §6.1.3); the constraint reference |

**The order within one study.**
1. The residual.
2. The lens readings, typed by the hardness map, with their exclusion marks.
3. The λ-trajectory of each structure, in closed form, with its placement margin.
4. The cheap perturbations of structures and candidates, escalated where an alarm fires.
5. The loop, to the emptied box.
6. The kept record, handed to the society.

**The caveat that remains.** A confident joint error, every series and every perturbation agreeing and
wrong, passes layers 3, 5, 6 and 7 as it passes layer 1 (BRIEF §5). Its defenses are gold read as near
misses and the censors (Part 5 §5.6); its shared causes, and the test that decides whether it can be
routed, are set out in Part 6 §6.5.

**OPEN (BRIEF §7 and this Part).**
- *The perturbation magnitudes.* Rules are given in §4.3; the values are measured.
- *The hardness map's grain:* normals per regime, the resolution of a place, and κ, which waits for more
  than one series.
- *The phantom library.* Phantoms consistent across contrasts need the signal equation (Part 3 §3.3.10;
  Part 5 §5.8).
- *The closed form.* Whether it describes the pipeline is shown by the twin's agreement.
- *Added information.* Whether the stability fraction and the windowed drop add rank information beyond the
  zone deviation (H2's bridge).
- *Q2* is answered here by proposal and awaits the founder.
- *Q3* sets which near miss is a negative for the meniscus.
- *Q4* sets how layer 9 orders the readings (Part 6 §6.1.4).

*External references:* Box GEP (1980), Sampling and Bayes' inference in scientific modelling and
robustness, JRSS A; Evans M, Moshonov H (2006), Checking for prior-data conflict, Bayesian Analysis;
Högbom JA (1974), Aperture synthesis with a non-regular distribution of interferometer baselines, A&AS;
Ibrahim JG, Chen M-H (2000), Power prior distributions for regression models, Statistical Science; James W,
Stein C (1961), Estimation with quadratic loss, Proc. Fourth Berkeley Symposium; Stein CM (1981),
Estimation of the mean of a multivariate normal distribution, Annals of Statistics; Stetson PB (1987),
DAOPHOT: a computer program for crowded-field stellar photometry, PASP.

## Part 5 — The society: agencies, the series committee, tiers, memory, censors, and teaching (layer 8)

This Part specifies layer 8 (BRIEF §5): the society that takes up what layers 0–7 leave, and decides each
finding or abstains. Layers 0–7 narrow, encode and propose. Layer 8 is the first layer entitled to decide a
finding, and layer 9 ranks what it decides (Part 1 §1.9; THEORY Part IV, Law 4). Its thesis is the cell
thesis's fourth hypothesis: "A society learns only the residue" (THESIS §1.4, §10).

The society reads the kept record Part 4 hands on (Part 4 Table 4.7). From Part 3 it takes the profiles in
the exact ledger, the regime cases, and "the series as committee members, with imputed series marked and
never a voice" (Part 3 §3.6). It hands Part 6 one word per finding per study, with the readings behind it
(§5.10).

This layer is also where a fitted model would most easily be smuggled in (Part 1 §1.11). The guard is
structural, and it is restated wherever it bites:
- every store holds individual cases with their sources, never weights;
- every level is "a ratio of two whole numbers written down before the run it judges" (THESIS §12.2);
- every answer is assigned by concurrence and refused on disagreement;
- nothing is tuned to agree with a teacher (THESIS §8.2).

The one sanctioned bounded utility remains registration (THEORY Part IV, Law 3). Nothing in this Part learns
in the fitting sense.

Today the build reads one series per study (BRIEF §4). So the committee has one voice, and much of
what follows waits for the series (Q6).

### 5.1 The society, and the rules every agency keeps

**The residue, typed.** H1's bridge says that what the structure leaves is "a typed **residue**, not noise:
the questions it leaves open, each typed by how it arose" (THESIS §1.4). In the knee the residue has six
types, each raised by a named layer:
1. a body the series do not concur on (the commit, layer 6, Part 4 §4.4; §5.3);
2. a structure whose word is PEAK_DROP, MONO_DOWN or AMBIGUOUS (Part 4 §4.5);
3. a committed object whose cause is not yet typed as lesion, instrument, normal variant or input error
   (§5.9);
4. a question every series is blind to (Tier 2; §5.4);
5. a site the loop left "unexplained" (Part 4 §4.4);
6. in teaching, a reported finding that no committed object explains (the every-finding agency, §5.2).

**The agency.** "An **agency** is such a learner, with its own question, oracle, cases and measure", and "An
agency is bounded by its check: one check against one clean signal makes one agency" (THESIS §10.1). Its
**oracle** is the signal it is taught against. The oracle must not depend on what the agency learns: "one
that did would teach it its own errors" (THESIS §10.1). Clean means independent, not free of error (Part 1
§1.4, clause 4). The knee's main teacher, the reports, is independent and noisy (§5.7).

*Table 5.1. The rules every agency keeps.*

| Rule | Source | What it forbids in the knee |
|---|---|---|
| Decide or abstain | THESIS §4.8 | a guessed score; a negative inferred because a positive is missing (THESIS §7.3) |
| Truth by concurrence, refused on disagreement | THESIS §4.4, §10.2 | a vote, an average or the strongest voice settling a disagreement |
| Law checks support; an oracle establishes, for its own question | THESIS §10.5; RECIPE §6 | a finding established by a law check, by an L5 pattern, or by another agency's oracle |
| No confidence-coupling where findings are decided | THEORY Part III; Law 4 | a finding decided because a margin or a probability crossed a cut |
| Cases, never prototypes | THESIS §7.1 | a bundle per answer used as a decision, such as `tools/lens_eval2.py`'s prototypes (§5.5) |
| Nothing tuned to agree | THESIS §8.2, §12.2 | a level, radius or lens setting chosen to separate gold, or to match reports study by study |
| No bank carries a weight | THESIS §6.6 | a weighted bank; a bank chosen because it separates confirmed cases |
| The memory never confirms itself | THESIS §8.4, §10.3 | a case confirmed by the memory's own routing; a study judged by a case made from it |
| A refusal teaches nothing | THESIS §10.3, §7.5 | a censor written from an abstention, a Tier 2 silence or an unresolved object |

The agencies meet "only in the one language and the kept record of findings" (THESIS §10.2). Every case,
censor and record is written in the same ledger (Part 3 §3.5), so one object's profile is readable by every
agency, each over the banks its own question names. "No agency is the pipeline, and no one score grades the
society" (THESIS §10.2).

**Where the society acts in a study.** Part 4's order within one study ends with "The kept record, handed to
the society" (Part 4 §4.6). The society also acts earlier, inside the loop: each commit asks the committee
(§5.3), at the tier the header and the hardness map assign (§5.4). Once the box is empty:
- the split types each object (§5.9);
- the agencies recall in curriculum order (§5.2, §5.5), under the censors (§5.6);
- a recalled procedure may send work back into the loop, under the loop's guard on rounds (THESIS §4.7).

### 5.2 The five agencies

RECIPE §5 names five agencies by their questions. Four divide the twelve findings by the tissue law that
reads them: fluid, marrow and fibrous tissue have their own signatures (L2), and OA is a compartment's
assembly of signs (L4). The fifth is the analog of the thesis's every-cell agency. Table 5.2 gives each its
oracle, stores, check and measure, in the form of THESIS §10.1's table.

*Table 5.2. The agencies.*

| Agency, and its question | Its oracle (teaching only) | Its stores | Its check (supports only) | Its measure |
|---|---|---|---|---|
| **Fluid.** Is there excess fluid, where, and which collection is it? With the fluid out, are the lining and the fat pad abnormal? | localized report calls on effusion, Baker's cyst and synovitis, with recess, size and "trace" words; gold | each recess's state; collections with and without a neck; fat-pad states with and without an effusion; censors from trace fluid, parameniscal cysts and pad clefts | fluid lies only in recesses and bursae; a Baker's cyst is posteromedial, with its neck (RECIPE §5); a take leaves no ring or hole, and a lobe is a second object (Part 4 §4.4) | per finding on held-out gold: identified, abstained and wrong, never summed; recovery of planted collections, and of lining planted behind an effusion; false takes per recess on true normals |
| **Marrow.** Is there edema in bone, of which kind, and is there a line in it? | report calls of bruise, contusion, marrow edema and fracture, with bone and side; gold | edema-objects by site, depth and pattern membership; lines with their reach to cortex; censors from OA marrow lesions, red marrow and physeal scars | edema lies inside bone; a fracture line lies inside edema and reaches cortex (RECIPE §5); every contusion belongs to a mechanism pattern or to OA's compartment, or is flagged unexplained (Part 2 §2.6) | as above; planted edemas with and without lines; planted lines without edema, every one censored |
| **Fibrous structures.** Is this ligament or meniscus injured? | localized calls of tear, sprain and degeneration, with horn, body, root or segment, and tear plane; gold | per structure and subregion: tear, sprain, degeneration and normal cases, with their contact, continuity, course, tear-plane and trajectory readings; censors from intrasubstance signal (Q3), pseudotear sites and bursal fluid | a meniscal tear touches a surface on two or more slices; a ligament tear breaks continuity or course (RECIPE §5); one lesion lands in one place on every plane that covers it (RECIPE §6) | as above; planted tears by slice count, plane and orientation; planted gaps; false contacts per subregion on true normals |
| **Compartments.** Is this compartment degenerated? | report OA and chondral calls with a compartment (the parser's compartment rule, BUILT); gold | compartment states, each an assembly of co-located signs: cartilage loss, gap, marginal outgrowth, subchondral lesion, extrusion; censors from one sign alone | OA's signs co-locate in one compartment (RECIPE §5) | as above, with each finding's report–gold softness beside it (§5.7) |
| **Every finding,** the count's analog. Was any finding missed? | the report's list of findings, "which ones, never where" (RECIPE §5); gold's list | combinations at half-seen places; combinations accepted as finding-bearing; censors from calls of "nothing there" | every reported finding is explained by a committed object (RECIPE §5); the emptied box (RECIPE §6) | the share of reported findings, and of gold findings, explained by a committed object |

*Table 5.3. The agencies in the study's order.*

| Agency | Findings | Consumes | Acts | Taught |
|---|---|---|---|---|
| Fluid | Effusion, Baker's, Synovitis | the residual; recess zones; the Recess volume, Neck and Fat pad lenses (Part 2 lenses 12, 13, 16) | at the first commits, since an effusion is taken first; then on what its take reveals | first |
| Marrow | Contusion, Fracture | bone subregions; the Marrow and Line lenses (14, 15); the T1 pathway | after fluid; inside each committed edema; at L5 partner sites | second, with fibrous |
| Fibrous structures | ACL, MCL, Medial Meniscus, Lateral Meniscus | structure words (Part 4 §4.5); lenses 7–11; the magic-angle censor | after fluid, whose take outlines the surfaces | second, with marrow |
| Compartments | Medial OA, Lateral OA, PF OA | the marrow and fibrous agencies' answers; lenses 9 and 17–19 | after marrow and fibrous | third |
| Every finding | all twelve | the kept record and every answer | last | fourth |

**Fluid.** A collection changes how its neighbors read, so this agency acts first. Once an effusion is taken
with its partial-volume rim, Hoffa's pad and the posteromedial recess are read for what the fluid hid (Part 4
Table 4.6). Its first two questions are asked together: "effusion, as gold counts it" and "fluid present".
Trace fluid answers them differently, so it is one call with a digit on each (§5.5). Synovitis is read without
contrast, through surrogates (MOAKS; Part 2 §2.5). Because effusion-synovitis shares one score, the agency
answers Synovitis only after its own Effusion decision.

**Marrow.** Its excluder is senior: T1-bright marrow excludes edema (Part 4 §4.1). It reaches inside each
committed edema for a line (Part 4 §4.4). It types each edema-object by site. A contusion at an L5 site is
read with its pattern partner. A subchondral one, under cartilage loss in a narrowed compartment, goes to the
compartments agency as an OA marrow lesion (Part 2 §2.6).

**Fibrous structures.** Its objects are structures, always present, read against their own prior (Part 4
§4.5) and by the lenses their law names. It asks per structure and subregion (horn, body, root; a ligament's
segments), because the localized calls do (§5.7). The magic-angle censor runs before it reads (§5.6).

**Compartments.** OA is an assembly, so this agency consumes the others' answers. Its findings are graded
processes the labels binarize (Part 1 §1.4, clause 2), so it is the agency most exposed to the reports'
softness (§5.7).

**Every finding.** The thesis's every-cell agency is taught by the count, which "establishes how many, never
which" (THESIS §10.1). The knee's analog is taught by the report's list of findings, "which ones, never
where" (RECIPE §5).
- *In teaching,* a reported finding that no committed object explains means keep looking. The site search
  runs again where the finding's law places it; reaching inside runs on that zone's committed objects; the L5
  partner sites are searched (Part 4 §4.4).
- *Its candidates* are written as **combinations**, one digit per lens and series at a half-seen place: +1
  where the lens saw the finding's signature, −1 where an entitled excluder fired, and 0 where it half-saw,
  "a reading at its middle and not silence" (THESIS §10.1).
- *Its one order by resemblance.* Candidates that pass are ordered by recall against confirmed combinations
  and accepted while the report still asks. Each keeps "accepted by the report" as its kind, where the
  thesis's candidates keep "accepted by the count". That is "the one order by resemblance the design allows,
  and only in teaching" (THESIS §10.1).
- *It adds and never trims:* "nothing committed is removed to match a report" (RECIPE §5). A site it leaves
  untaken is unconfirmed, never "no finding".
- *In a run,* a test study has no report. Remembered combinations, their censors and the site search choose
  where to try, and what passes goes back to the finding's own agency: "resemblance chooses where to try,
  never what a cell is" (THESIS §10.1).

**When two agencies meet one object.** Truth among agencies is assigned by concurrence (THESIS §10.2). Two
cases arise.
- *Two claims.* A posteromedial collection is a Baker's cyst to the fluid agency and a parameniscal cyst to
  the fibrous agency. A subchondral edema is a contusion to the marrow agency and an OA marrow lesion to the
  compartments agency. L1 allows one owner (§5.6), so the claim is settled as THESIS §9.5 settles a shared
  region: to the owner a call names; else to the side whose named difference holds (the neck; co-located OA
  signs); else to no one. Unowned material is kept and shown, "never made noise" (THESIS §9.5).
- *Corroboration.* An ACL reading PEAK_DROP and contusions at the pivot-shift sites corroborate each other.
  "Each is still established only by its own oracle" (RECIPE §5). Corroboration enters the record and the
  emission, never a decision (§5.6, the pattern rule).

**A sixth question: placement (OPEN).** Whether a zone lies where the atlas puts it has a clean oracle
(deliberate misregistrations of true normals, known by construction; the NCC check, ZONES Rank 2) and a check
of its own (the placement margin, Part 4 §4.5). By THESIS §10.1's rule that makes it an agency: the knee's
counterpart of the cell thesis's position agency, which keeps "Records of the jiggle and of carried places'
errors" (THESIS §10.1). The brief names five (BRIEF §5). Whether the constraint reference should learn where
registration errs, or only measure it, is for the founder.

**The modules (Q7, OPEN).** The society is new code. Eight text-extraction template stubs sit in
`src/RSNA_Knee/` (BRIEF §4). Two of them, read first-hand, carry contracts this design forbids:
- `pipeline.py` lists a "Neural residual (Pattern 13) — LLM for irreducible ambiguity", against Law 1;
- `bank_evaluator.py` says "Thresholds and weights MUST be calibrated from training data", against "No bank
  carries a weight" (THESIS §6.6).

Repurposing them by name would import those contracts. Part 6 §6.6.2 reads all eight and recommends
deleting them.

**The mechanism (DESIGNED).**
- *Reads:* the kept record (Part 4 §4.6); profiles and regime cases (Part 3 §3.6); its own stores.
- *Computes,* per question: the committee's outcome (§5.3), the object's class (§5.9), and recall (§5.5)
  under the censors (§5.6).
- *Emits,* per finding: PRESENT, ABSENT, DISAGREE or ABSTAIN, each with its cause and readings (§5.10).
  ABSENT is given only where entitled excluders or recalled "absent" cases cover the finding's zones, never
  because a positive is missing (THESIS §7.3).
- *Licensed by:* H4; THESIS §10.1–§10.5; RECIPE §5.
- *Fails:*
  - by an oracle that is not clean, as with a "true normal" whose report missed a lesion (Part 1 §1.4,
    clause 4);
  - by a question split wrongly between agencies, leaving an object no agency owns;
  - by a pooled curriculum: "One pooled set would blend contexts that answer differently, and every failure
    would differ in many respects, so no censor would form" (THESIS §10.3).
- *Measured by:* each agency's trajectory on held-out gold (§5.7); counts of unowned and unassigned objects;
  phantoms per agency.

### 5.3 The committee is the series

**The precedent.** GenomeVault's committee ran four encoders over 3,695,997 clinical positions (COMMITTEE,
Executive Summary). They were unanimous at 98.59% of positions, every one right; split 3–1 at 1.41%, 99.994%
right; and tied 2–2 at 0.004% (COMMITTEE §5.1). Two encoders were never the lone dissenter, and ties were
broken by trusting that pair, right 95.1% of the time (COMMITTEE §5.2–§5.3, §8.2). All three committee errors
fell where every encoder's margin was 0, so one rule catches them, `all(m == 0 for m in margins.values())`
(COMMITTEE §6.3; TIERED §4.1). And the four failed together at 2 positions where independence predicted
0.00006, a ratio of 36,210 (COMMITTEE §4.2). The founder reads that ratio as information, not failure (Part 1
§1.7), and the hardness map turns his reading into a lens (Part 4 §4.2).

**A codec's committee, and an inference's.** The precedent drew its independence from seeds. "Each seed
produces a **completely different codebook**" (COMMITTEE §2.2). Encoders that shared one codebook had "100%
error overlap", since "Same seed → Same dimension indices per position", and so "Same collisions → Same
errors" (COMMITTEE §1.2). Even four different decompositions of the four-letter alphabet (COMMITTEE §3)
failed together while they shared one codebook: OneHot and Trinucleotide overlapped on 1,728 of 1,728 errors.
A seed per encoder cut joint errors 373-fold (COMMITTEE, Appendix B.1). HDCSUB records independence as "a
GO/NO-GO GATE, not an assumption" (HDCSUB F.4 #4).

That committee corrected a **codec**. The genome was known, and each error was a decode error, caused by
collisions in a lossy code. The knee's ledger has no collisions: its rows are exact, "so nothing collides"
(BRIEF §4), and "Rows cancel exactly" (THESIS §12.1). A re-seeded ledger writes the same counts and the same
cosines (Part 3 §3.5.1, item 8; Part 4 §4.3).

What the knee must resolve is an **inference**: what the views of one knee saw. Its errors come from the
instrument and from geometry: partial volume, a plane cutting a structure along its length, failed
suppression, the magic angle, motion. "Independence must come from different evidence, not different
encodings" (RECIPE §7). The different evidence is the series: planes differ in geometry, contrasts in
physics. So the committee is the series (BRIEF §5, layer 8), and seeds play no part in it.

*Table 5.4. Causes of failure, and the series that share them (DESIGNED; each to be measured).*

| Cause | Law | Shared by | Separated by |
|---|---|---|---|
| partial volume; slice-phase dropout; a thin structure cut obliquely | L3 | the series of one plane, which cut the knee the same way | another plane |
| failed fat suppression | L2 | spectrally fat-suppressed series (STIR fails differently) | a series without suppression (T1) |
| the magic angle | L2 | short-TE series | a long-TE series |
| motion | constraint | one series (during it), or a pair (between them) | series acquired apart |
| the reference's t-tails (VERDICT) | L1 | series of one type in one regime | another series type |
| registration | Law 3 | every series of a study, which share one kept transform (Part 3 §3.6) | nothing: placement is never a committee question |

Independence is therefore per question. Two sagittal series fail together on surface contact. Two
fat-suppressed series fail together on edema where suppression fails. The thesis states the rule for cells:
"Readings of one light are not independent, so they count by these four families" (THESIS §8.1), and "The
limit is independence, not capacity, so the independence of views is measured before their agreement counts"
(THESIS §6.2). The knee counts by **independence classes**: for each question, series whose errors the gate
cannot separate count as one voice.

**The gate (DESIGNED, after HDCSUB F.4 #4).** For each question, and each pair of series families present
together in enough studies:
- *error indicators,* per place, on three measuring sets: phantoms, where truth is known by construction
  (misses and false "for" readings); held-out true normals, where any "for" is false; and gold, where a
  localized call fixes the place;
- *two statistics:* the φ coefficient of the pair's errors, and the joint-failure ratio κ, the joint error
  rate over the product of the marginal rates (Part 4 §4.2);
- *the rule:* the pair counts as two voices for the question when φ and κ fall below levels written before
  the run. GenomeVault's levels were "max φ < 0.25, scaled 4-way < 35, including the margin-0 worst case"
  (HDCSUB F.4 #4). They are adopted provisionally until the founder sets the knee's own bar (Part 6 §6.7,
  item 8), written before the run.

Two kinds of reading are never voices. An imputed series "is a function of the series that made it, so it
carries no independent evidence" (Part 3 §3.3.6). A perturbation measures robustness, and "It is never
counted as votes" (Part 4 §4.3).

**Who may speak.** For a question at a zone, a series is **entitled** when five conditions hold:
1. the Coverage lens gives it enough effective slices along the question's axis (Part 2 lens 6);
2. the hardness map marks its lens readable there, or misleading with a partner not misled there (Part 4
   Table 4.2);
3. no law-given censor has removed its evidence (§5.6);
4. it was measured, not imputed;
5. the entitlement table, written by dissenter analysis (below), does not set it aside for this question at
   this place.

A series that is not entitled is still read, and its word is recorded, but it is silent in the vote, with its
cause. Silence never counts against: "A reading that cannot read abstains, and never counts against" (THESIS
§8.1).

*Table 5.5. The committee's outcomes, over entitled independence classes.*

| Outcome | When | What follows | COMMITTEE's counterpart |
|---|---|---|---|
| **CONCUR** | two or more classes agree, and none dissents | the object is committed, or the exclusion stands; the concurring readings are recorded (THESIS §4.5) | unanimous; a majority whose dissenter is not entitled at that place |
| **SINGLE** | one class can speak | a take carrying "single voice" (Part 4 §4.4), only where the reading passes its own persistence test: the two-slice touch, or its stability fraction against phantoms of its size (Part 4 §4.3) | none: four encoders always spoke |
| **DISAGREE** | entitled classes stand on both sides | kept; the next round reads it from scratch (THESIS §4.5); at the last look it takes a word; it reaches emission as a disagreement | a majority with an entitled dissenter; a 2–2 tie |
| **ALL SILENT** | no class is entitled | Tier 2: the question stays open, with each voice's cause (§5.4) | all margins 0, sent to review |

**Departure** from BRIEF §5, layer 8, which specifies "dissenter analysis per finding and tie-break by the
most reliable pair (COMMITTEE §5)", and from COMMITTEE, which accepts a 3–1 majority and breaks a 2–2 tie by
its most reliable pair (COMMITTEE §5.1, §8.2). The thesis forbids both as rules of decision: truth is
"refused where they disagree, never by one tuned pipeline or one voice", and "Where two disagree, neither
overrules the other" (THESIS §4.4); a disagreement is "kept, and never broken by order, averaging or the
strongest voice" (THESIS §10.2). Where the brief conflicts with the canon, the canon governs (BRIEF,
preamble), so the brief's tie-break is dropped and its dissenter analysis kept. The knee keeps COMMITTEE's
measurement and changes its use. Reliability is measured per finding and place, by dissenter analysis, and
what it licenses is an **entitlement**, written before the run. Where a series' dissent is predicted by a
law-named cause, that series is not a voice for that question there. A majority stands only when its
dissenter is set aside so. A tie between entitled voices stays a disagreement. The most reliable pair (below)
keeps every role but the tie-break: the dissenter analysis that finds it writes the entitlement table, it is
the default cleaner pathway for the split's rejections (§5.9), and the hard sheets read it first (§5.7).

**Dissenter analysis, per finding (DESIGNED).** COMMITTEE learned which views to trust from who dissents:
"OneHot and Trinucleotide are NEVER the lone dissenter" (COMMITTEE §5.2). The knee aggregates its committee
records over finding, zone and regime. It computes:
- for each series family, its lone-dissent rate, and the margin word ("reaches" or "short"; THESIS §12.2) at
  which it dissents;
- for each dissent, the law-named predictors that might explain it, as the hardness map's admission test asks
  (Part 4 §4.2, step 5): the plane's angle to the structure (L3); θ to B0 (L2); distance in slices to a zone
  boundary (L3); suppression failure (L2); motion between series.

There are two outcomes.
- *A dissent a predictor separates,* with its effect size reported as TIERED reports d (TIERED §3.1.1),
  becomes an entry in the **entitlement table**. Expected entries include the sagittal series at the
  meniscal body, which it cuts along the circumference (L3), and the sagittal series at the ACL's femoral
  attachment, partial-volumed with the lateral condyle (Part 2 Table 2.8b, lens 10).
- *A dissent no predictor separates,* spread evenly, is entropy for this set of views: TIERED's margin 2
  (TIERED §3.1.1). Law 5 then says to look for the missing view or lens, never for capacity (THEORY Part IV).

The pair that passes the gate, and is never the lone dissenter at a place, is that place's **most reliable
pair**. The split's rejections and the hard sheets read it first (§5.9, §5.7).

**The knee's sandwich.** RECIPE §6's check, "two views in place of two anchors", belongs to the committee
(Part 4 §4.3). Readings concur only where they land one lesion in one patient-space place. A sagittal body
and a coronal body that both read "fluid", but lie apart beyond the correspondence radius (Part 2 lens 3), are
two candidates of one voice each.

**Structures, and why placement is not a committee question.** Each series that covers a structure gives its
own λ-trajectory word and drop (Part 4 §4.5), and the committee reads them as it reads lesion readings.
Placement is different. A study is registered once, and its one transform is carried to every series (Part 3
§3.6). A registration error is therefore common to every series, and their concurrence cannot clear it.
Placement is read on the constraint reference: the NCC check and the placement margin (Part 1 §1.8; Part 4
§4.5).

**The committee record.** TIERED stores "pre-computed votes + margins (NOT full vectors)", seven bytes a
position (TIERED §1.2, §3.4). The knee keeps, for each study, zone and question: each series' entitlement or
the cause of its silence; its word (+1, −1, orthogonal or silent: Part 3 §3.5.3's three zeros), margin word
and hardness status; the independence classes used; the outcome, the dissenter and its typed cause; and the
tier. It is a record of words, and dissenter analysis reads nothing else.

**Today.** With one series per study (BRIEF §4), every question has at most one class. Every outcome is
SINGLE or ALL SILENT, and the gate cannot run. The loop's takes carry "single voice" (Part 4 §4.4), and so
does every answer built on them. The committee waits on Q6.

**The mechanism (DESIGNED).**
- *Reads:* each series' readings per question and place; the hardness map; the Coverage lens; the censors.
- *Computes:* entitlement; independence classes, from the gate; the outcome; the committee record; the
  dissenter tables.
- *Emits:* commits and refusals to the loop (layer 6; Part 4 §4.4); outcomes and concurrence counts to the
  agencies and to emission; versioned entitlement tables; dissents with their predictors, to the hardness map.
- *Licensed by:* THESIS §4.4–§4.5, §6.2, §8.1; COMMITTEE §1–§6, §8; HDCSUB F.4 #4; RECIPE §6–§7; L2; L3.
- *Fails:*
  - by dependent voices the gate missed, through a cause absent from its measuring sets;
  - by entitlement tables built on too few studies, with the heavy tails VERDICT names;
  - by a confident joint error: every entitled class agreeing, and wrong, which no committee sees (BRIEF §5);
  - by inventories that never reach two classes for a question.
- *Measured by:*
  - φ and κ per pair and question, on phantoms, true normals and gold;
  - wrong commits per outcome on held-out gold, which should be fewest under CONCUR;
  - lone-dissent rates, replicated on a second half of the studies;
  - confident joint errors on gold, read as near misses (§5.6).

### 5.4 Tiers: where the work goes

TIERED's premise is that "**most of the genome is easy to encode**" (TIERED, Executive Summary). It runs three
tiers (TIERED §1.2):
Tier 0, a cheap baseline for about 93% of positions; Tier 1, a committee overlay for the low-margin 7%; and
Tier 2, about 170 positions (0.001%), for human review. The knee's form (BRIEF §5, layer 8): Tier 0, the
header skips quiet zones; Tier 1, the series committee; Tier 2, zones every view is blind to, kept as
hardness information.

*Table 5.6. The tiers, from the genome to the knee.*

| Tier | Genome (TIERED §1.2) | Knee (DESIGNED) | Kept |
|---|---|---|---|
| 0 | a cheap 2-bank decode, with vibe collapse | a quiet zone word (Part 3 Table 3.2) on a pair that is not mandatory: layers 3 and 5–7 skip the zone | the cheap profile, marked `skipped_by_header` |
| 1 | low margin: four encoders vote | the series committee, then recall | the committee record (§5.3) |
| 2 | every margin 0: human review or re-sequencing | ALL SILENT: the question stays open, with each voice's cause | the record; the hardness map, or the constraint reference |

**Departure.** TIERED's Tier 0 decodes by vibe collapse (TIERED §1.2, §2.3), which its own committed results
refute (HDCSUB F.4 #1). The knee's Tier 0 is the header of HDCSUB F.1, read off the ledger (Part 3 §3.2).

**Coverage, after TIERED §3.1.** TIERED covers some positions with "No exceptions" (every clinical variant),
some conditionally, and skips those of margin 4 or more. The knee sets its lists by measurement.
- *Mandatory,* never skipped:
  1. every (zone, finding) pair whose skip-miss rate on gold and phantoms is not near zero (Part 3 §3.2.6).
     Thin structures, where a tear is a few voxels, are expected here;
  2. the L5 partner sites of every committed object (Part 2 §2.6);
  3. in teaching, every zone a localized call names, since every call must find its successor (§5.7).
- *Skipped:* a quiet zone word (DEVIATION low, MISFIT low, FLUID and WATER-IN-FAT not high; Part 3 Table 3.2)
  on a pair that is not mandatory. A skip is not an exclusion, and "No header bit enters a decision or a
  score" (Part 3 §3.2.5): the headers "are cheap signals, not defining elements" (founder, 2026-10-02).
- *Conditional:* the rest go to Tier 1.

**Tier 2, an abstention that is information.** COMMITTEE's flagged positions shared a structural type: N
bases, GC content of 70–78%, homopolymers, repeats (COMMITTEE §11.1–§11.2). TIERED found errors at margin 0
predictable and errors at margin 2 not (TIERED §3.1.1; read in full in Part 4 §4.2). For the founder, a lens
that never resolves the signal is "a *perfect* lens for where your signal is *not*" (founder, 2026-10-02;
Part 1 §1.7).

So Tier 2 is triggered by ALL SILENT, an outcome the hardness map predicts, and it is kept as a reading
about the place:
- *on the map,* at a blind or hard place (Part 4 Table 4.2), it is expected. The question is open there, with
  its cause;
- *off the map,* it is a **hardness deviation**: a readable place made unreadable, by motion, the coil or
  hardware. It goes to the constraint reference, never to a finding (Part 4 §4.2).

COMMITTEE's answer to an all-zero position was "UNCERTAIN - recommend re-sequencing" (COMMITTEE §11.3). The
knee cannot rescan, but it can read a series it set aside. Before abstaining, Tier 2 asks whether the
inventory holds a series the Coverage lens rejected only on its obliquity tolerance. If so, it reads that
series at the lens's wider sane value (Part 2 Table 2.8a, lens 6), marked as such. Whether such reads add
more than they mislead is measured on phantoms at known obliquity. What stays open on a test study, which has
no reviewer, is an abstention with its cause (THEORY Part IV, Law 7). A finding is never ABSENT because its
zones are blind; emission places a Tier 2 case at exactly 0.5, in the middle register's fixed part
(Part 6 §6.1.4).

**Predictable failure, and entropy.** The knee measures TIERED's distinction on its own records. Wrong answers
concentrated where every voice was weak are predictable, as COMMITTEE's three errors were, and belong on the
hardness map. Wrong answers spread evenly across the tiers are entropy for these views, and call for a new
view (Law 5).

**The mechanism (DESIGNED).**
- *Reads:* the zone word and inventory (Part 3 §3.2); the hardness map; the committee's outcome.
- *Computes:* the tier of each (zone, question).
- *Emits:* the tier, into the committee record; Tier 2 causes, to the map or the constraint reference;
  skipped zones' cheap profiles.
- *Licensed by:* TIERED §1.2, §3.1, §3.1.1; COMMITTEE §6, §11; HDCSUB F.0–F.1; founder rulings 3 and 5;
  Law 4.
- *Fails:* by a quiet header over a finding; by a Tier 2 share that hides a finding in a regime; by a saving
  that never arrives (E10's routing gave 1.11× where 1.55× was expected; HDCSUB F.2).
- *Measured by:* the skip-miss rate per pair; Tier 2's share per finding and regime, and the part of it on
  the map; the work per study with and without routing, in counts and never in seconds (zones skipped by
  Tier 0, invocations of layers 3 and 5–7, perturbations and sweep twins run; Part 3 §3.2.6); whether cost
  falls as the agencies learn (THESIS §13.3 #6; Part 6 §6.4, falsifier 6).

### 5.5 Memory: cases, recalled by concurrence within a trust radius

**What a case is.** "A **case** is one remembered example of a typed object in a context. It keeps its
bundle; the role confirmed for it, its call; what was expected of it and how that was off, where it was; and
its source, what confirmed it." (THESIS §7.1). In the knee:
- *its bundle* is the object's or structure's profile in the ledger: a count table over every bank it writes,
  with its footprint beside it (Part 3 §3.5.4);
- *its call* is one balanced-ternary digit on each question the call speaks to (THESIS §7.3);
- *what was expected* is the structure's proposed word, and the named difference where the call corrected it;
- *its context* is the regime key (Part 3 §3.2.4), the zone, the route out of the loop (THESIS §5.6), the
  exclusion context (Part 4 §4.1) and the tier;
- *its source* is the report sentence verbatim, with its language and the parser's version; or the gold row;
  or the founder's words. The study and the teaching step are kept with it.

Cases of one answer form a **bucket**, kept per agency, question, zone class and regime. "They are compared
one by one, never summed into one bundle per answer, since a sum would lose which readings occurred together
in each case" (THESIS §7.1).

**Calls in ternary.** "Calls must be ternary because evidence for (+1), evidence against (−1) and no evidence
(0) are three different things, and decide or abstain needs all three" (THESIS §7.3).

*Table 5.7. Calls in ternary, on two pairs of the knee's questions.*

| Call, as a report or the founder gives it | Digits |
|---|---|
| "tear of the posterior horn" | tear +1; degeneration 0 |
| "intrasubstance degeneration, no tear" | tear −1; degeneration +1 |
| "normal menisci" | tear −1; degeneration −1 |
| "no meniscal tear" | tear −1; degeneration 0 |
| "moderate joint effusion" | effusion +1; fluid present +1 |
| "trace joint fluid" | effusion −1; fluid present +1 |
| "no effusion" | effusion −1; fluid present 0 |
| "possible tear"; a report with no terms found | 0 on every question: an abstention, kept, never a case |

The third kind of call is "not A or B, but A, its inversion, or something else entirely" (THESIS §7.3).
Trace fluid is the knee's not-cell-not-noise: certainly fluid, and not an effusion as gold counts it, since
"gold excludes trace/minimal effusions" (`src/RSNA_Knee/report_parser.py`, SMALLNESS_WORDS). And "An
abstention is kept among the calls; it never becomes a case and teaches nothing" (THESIS §7.3).

**Recall.** "It computes one cosine, over only the banks the question reads, between a present bundle and
each case" (THESIS §7.4), in whole numbers, against a level (THESIS §12.2). A case speaks only within its
**trust radius**, which "lies where the resemblances chance alone produces end, and it is set on real data.
It says when a resemblance is not an accident, never what a cell is" (THESIS §7.4). The knee constructs it
per bucket:
1. *The chance population:* profiles at the same zone class and regime that cannot carry the bucket's answer,
   by construction. For a bucket of a finding, these are held-out true normals, never reference members. For
   a bucket of "absent", they are phantoms planted in true normals, and gold positives localized to the zone.
2. *The statistic:* each member's cosine with its *nearest* case in the bucket.
3. *The radius:* the least level no member reaches, written as a ratio of whole numbers before any run it
   judges. Where the population is too small to bound the chance rate, the bucket answers "insufficient"
   (THESIS §4.8).

**Departure.** The thesis gives each case its radius. A knee bucket can hold hundreds of report-sourced
cases, and each case is one more chance for an accidental resemblance. Taking the radius on the nearest-case
statistic charges the bucket for its size.

The voices are the cases within their radii, and a censor written from a near miss vetoes "its one answer
within its radius" (THESIS §10.2). Then:
1. "One answer standing is recalled;
2. Two or more are a disagreement, kept, and never broken by order, averaging or the strongest voice;
3. None is an abstention." (THESIS §10.2)

A disagreement or an abstention "returns the question to the structure's own path: the less ambiguous
viewpoint that the principle of noncompromise, first formulated by Papert, seeks instead of a compromise"
(THESIS §10.2). Here that means another plane, another lens family or another round. The voices' counts and
sources travel with the outcome in the kept record, and never settle it inside the society; emission reads
recall only through the agency's decision word (Part 6 §6.1.3).

Each question's banks are named before the run. "No bank carries a weight, and none is chosen because it
separates confirmed cases" (THESIS §6.6). Header words, such as the trajectory byte and λ*, are metadata.
They may order a scan, never enter the cosine, and "A scan may drop a case only where an exact bound proves
that it cannot reach the level" (THESIS §12.2; Part 3 §3.2.5, rule 1).

**What a recall brings back.** "At its center, a K-line remembers methods, not answers: what it brings back
is no old verdict but a route to the structure's own tools, with the interpretation that tells them what to
do" (THESIS §7.2).

*Table 5.8. What a recalled interpretation routes to (DESIGNED).*

| Recalled interpretation | The procedure it routes to | Law |
|---|---|---|
| a meniscal tear, by tear plane | surface contact read again on both planes, the cross-plane count kept apart (Part 2 §2.11) | L3; L4 |
| a tear with a parameniscal collection | the collection to the ownership rule, read by the Neck lens | L1; L4 |
| an ACL tear | a site search at the pivot-shift sites; the placement margin checked | L5; Part 4 §4.5 |
| an effusion | the take with its partial-volume halo; Hoffa's pad and the posteromedial neck read after it | Part 4 Table 4.6 |
| a contusion at an L5 site | reaching inside for a line (lens 15); a site search at the partner site | L4; L5 |
| an OA marrow lesion | the compartments agency: are the signs co-located? | L5, OA |
| magic-angle brightening | the magic-angle censor, with the long-TE series | L2 |
| an input error | layer 5's expensive families, R4 and R5 (Part 4 §4.3) | Law 3 |
| several objects in one candidate | the knee's Scissors: parting along a law-named boundary (a cortex, a neck, a recess wall) | L1; L4 |

The thesis's Scissors part a candidate "under a contract of N that is never a quota: it makes no part the
light will not give" (THESIS §7.2). The knee's Scissors part only where a law names the boundary.

**A clean-up, if the knee needs one (OPEN).** The thesis redraws each candidate's border by resemblance to
confirmed regions, and "in a drawing a censor weighs and never vetoes" (THESIS §9.4). A knee object can
hold material of another kind at its edge: an edema's footprint holding a red-marrow island, an effusion's
holding thickened lining. Whether the knee needs the same drawing is measured by the post-take check's ring
and hole rates (Part 4 §4.4).

**Kanerva, and the regime in the key.** LAA stores its thin unknowns "in a Kanerva sparse distributed memory
[7], keyed by a hypervector encoding of the instance's context — its geometry, its log character, its regime
— and recalled by *similarity*". There, "a context near several stored ones returns their blend; a context far
from all of them returns a weak, low-confidence prior the uncertainty layer respects" (LAA §6). The regime
comes first: "a coefficient means one thing within a regime and another across one, so the regime must be
part of the key before the law's unknowns are read off the memory" (LAA §8). The knee keeps three things:
- *content addressing* over the ledger, where the cue is the bundle, as LAA's K-line is "a stored pattern
  that completes a partial cue" (LAA §6);
- *an activation radius,* the trust radius;
- *graceful failure.* A context far from every case recalls nothing, and abstains: LAA's "clean-or-hole
  contract" (LAA §11), with the level set against chance rather than read off the memory's own confidence.

It departs in two:
- *No blend.* A call is never reconstructed as a weighted mean of neighbors (THESIS §7.1).
- *No learned gate.* Of LAA §8's three stratified-regression designs (all fitted: LAA §2), the knee keeps
  only the block-diagonal partition: known, sharp, header-given boundaries with strict no-contamination. It
  replaces the per-block regression with per-regime references (median, MAD) and medians over individual cases
  taken at read time (Part 3 §3.3.5). Clustered regression and a mixture-of-experts gate are dropped because
  they also learn the partition (Part 2 §2.9).

*Table 5.9. The knee's two stores.*

| Store | Holds | Recall | Source |
|---|---|---|---|
| Regime coefficients | the law's thin unknowns, one case per true normal | the median of the regime's cases at read time, their spread as σ; never stored | Part 3 §3.3.5 |
| Calls | the agencies' cases, with ternary calls | concurrence within trust radii; censors veto | THESIS §7, §10.2 |

Recall searches the study's own regime cell first. It falls back to the parent key (field, then vendor, then
sequence) only where a bucket in the cell is empty (Part 2 §2.9), and marks a voice from a parent key as
such. The stratification is measured: on held-out gold, voices from other regimes should agree with
in-regime voices as often as in-regime voices agree with each other. Where they do not, the key is split.

**Why this is not a fitted model.** A memory that answers by resemblance to labeled examples is where a
classifier would be smuggled in, so the differences are stated.
- Nothing is fitted. A case is stored as it was confirmed, with its source. No parameter, weight or boundary
  is optimized against labels.
- Levels are set against chance, on populations that cannot carry the answer, before the run. Agreement with
  a teacher is "a consistency check, never a score to raise" (THESIS §8.2).
- An answer is never a vote of neighbors. One answer standing is recalled; two are a disagreement, kept.
- A recalled answer brings a procedure, and a lesion-object is still committed only by the series'
  concurrence (§5.3).
- Every answer names the cases, censors and laws behind it (THEORY Part IV, Law 7).

This is Winston's reasoning by precedent and Minsky's K-lines, as THESIS §7 reads them, on an exact
substrate.

**Provenance.** "The memory never confirms itself" (THESIS §8.4).
- A study is never compared with a case made from itself, so a gold study's own report-case leaves the
  memory while that study is judged.
- An answer the memory routes keeps a source of its own, and becomes a case only at a teacher's word (THESIS
  §10.3).
- Reference members never stand as "absent" cases. Their "own residuals are biased low"
  (`tools/lens_eval2.py`).
- "Calls are never overwritten; where two differ, the later stands beside the earlier." (THESIS §8.4)

**What `tools/lens_eval2.py` does, and what must change.** **BUILT:** it majority-bundles each finding's
parser-labeled positives (`data/registered_positives`, labels from report_parser_v3) into one prototype with
`bundle_prototype` (`src/RSNA_Knee/hdc_encoder.py`), at study level and per zone, and the 50 reference true
normals into a negative prototype, after subsampling the positives to the negatives' number (seed 1729). A
study's score is its similarity to the positive prototype minus its similarity to the negative, the zone level
taking the maximum over zones. Evaluation is on gold only: 43 gold studies and 30 held-out true normals. Its
readings died with the pre-v5 substrate (LADDER, substrate reset). It stays the v1 instrument, "never as
the decision" (RECIPE §8; Part 3 §3.5.1). The instrument that replaces it (DESIGNED) changes seven things:
1. cases, one per study and zone or per committed object, in the ledger, each with its localized call and
   source, and no bundle across studies;
2. "absent" cases only from normals outside the reference;
3. no subsampling: a bucket's size enters through its radius;
4. recall by THESIS §10.2, with censors vetoing, in place of a difference of two similarities;
5. per finding, identified, abstained and wrong, never summed (THESIS §10.4), beside the AUC under Part 6
   §6.1.4's ordering;
6. leave-own-study-out;
7. every level written before the run.

The label-source split it already keeps, taught from parser labels and judged on gold, stays.

**The mechanism (DESIGNED).**
- *Reads:* profiles; calls with their sources (§5.7); chance populations of true normals and phantoms.
- *Computes:* trust radii per bucket; recall outcomes; routed procedures.
- *Emits:* answers standing, disagreements and abstentions per question, with the voices' counts and
  sources; routed procedures; new cases, only at a teacher's word.
- *Licensed by:* H3; THESIS §7.1–§7.4, §8.4, §10.2, §12.2; LAA §6, §8, §11.
- *Fails:*
  - by H3's bridge failing: "Similar situations that do not lead to similar results" (THESIS §13.3 #4);
  - by a radius too low, so that chance speaks, or too high, so that everything abstains. LAA reports the
    second plainly: "Coverage at that clean threshold is deliberately modest" (LAA §11). A "normal" with an
    unreported lesion raises a radius; such members show as the population's outliers and go to the founder's
    sheet;
  - by report noise making disagreement the usual outcome;
  - by regimes aliased under one key.
- *Measured by:*
  - on held-out gold, how often the nearest confirmed case's interpretation holds, per finding, against
    chance;
  - the chance-voice rate on a second half of each chance population;
  - abstention and disagreement rates per finding over the trajectory, and whether wrong answers fall faster
    than abstentions rise (THESIS §13.3 #5).

### 5.6 Censors: law-given, and written from near misses

"A **censor** is a memory or a law that prevents an interpretation" (THESIS §7.5). It is negative expertise:
"Much of what an expert knows is what not to do, and knowing it can shape a search before it starts, more
cheaply than generating and testing" (THESIS §7.5). LAA gives the stance for near misses: "the right response
is not to score them down but to forbid them" (LAA §7). There are two kinds.
- A **law-given censor** "is a law that forbids outright, and it is absolute" (THESIS §7.5).
- A **remembered censor** rests on a call, or on a failure its agency's oracle confirmed. Remembered censors
  "act in two operations, kept apart. In a drawing, a remembered censor is a repulsor, weighed against the
  nearest attractor: never an absolute veto. In recall that assigns an answer, a censor written from a near
  miss vetoes its one answer within its trust radius, and nothing else." (THESIS §7.5)

LAA's two censors fall on either side. Its motion-evidence censor "is pure law", as the knee's law-given
censors are. Its envelope censor is a boundary "read directly off the field's solved cases", made "a hard
veto" (LAA §7). **Departure:** the knee makes no bound read off cases absolute. What is read off cases is a
remembered censor, which vetoes within its radius. Only a law forbids everywhere.

*Table 5.10. Law-given censors (DESIGNED).*

| Censor | Law | Forbids | Needs | Routes the reading to | Fails by · measured by |
|---|---|---|---|---|---|
| Magic angle | L2 | a tear or signal reading in fibrous tissue at θ within the window about 54.7°, bright on short TE only | the fiber's direction; B0; a long-TE series | the instrument; with no long-TE series, the hardness map's "misleading" (Part 4 Table 4.2) | a wrong B0 or θ; flexion · the θ-binned rate on true normals; gold tears inside the window (Part 2 lens 4) |
| Failed suppression | L2 | edema or Hoffa-synovitis where the FS-bright tissue is T1-bright fat | a T1 series | the instrument | real edema masked inside a failed region · the map of unsuppressed fat on true normals (Part 2 lens 5) |
| Edema lies in bone | L2 | Contusion for an edema signature outside bone | bone zones (8–10) | soft-tissue edema: the MCL shell, or unexplained | misregistered bone margins · phantoms at the margins |
| Fluid in cortex | L1, L2 | any lesion-object, and any tissue reading except a line, inside the cortical shell | a cortical shell zone, derived from the bone masks (to add) | a line inside edema, to the Line lens; otherwise the constraint reference, as a misplaced boundary | a cortex thinner than a voxel along the 3.4 mm axis; erosions · deliberately misregistered normals; gold |
| A fracture lies within edema | L4 | Fracture for a line outside committed edema | committed edema | the physeal scar or a vessel (variant), or unexplained | old fractures, if gold counts them · every line on true normals censored; each gold Fracture with no committed edema, read as a near miss of the censor itself |
| Fluid only in recesses and bursae | L4 | Effusion for fluid outside the recesses | recess zones (zone 4, BUILT; posterior recesses to add) | Baker's, a parameniscal cyst, a bursa, or unexplained | a recess the atlas misses · gold Effusion |
| One structure, one place | L1 | two owners of one voxel | — | the ownership rule (THESIS §9.5) | misregistered zones · counts of unassigned material |
| The pattern rule | L5; RECIPE §5 | a finding decided by its pattern | — | support, and a site search where a member is missing | a pattern used as a vote · an audit of every decision's provenance |

**What L5 may forbid.** It is tempting to list the mechanism patterns among the law-given censors. They
cannot be. RECIPE makes them "concurrence between independent questions", each finding "still established
only by its own oracle" (RECIPE §5), and Part 2 reads L5 as supporting and never trimming (Part 2 §2.6). A
real injury can lack its pattern, and a pattern can occur with one member intact, so an absolute law built on
a pattern would erase real findings. L5 therefore enters the society in four roles, none of them a veto:
- a law check that supports (RECIPE §6);
- a site search where a member is missing (Part 2 §2.6);
- a context word for recall: the pattern an object belongs to;
- one prohibition, the **pattern rule**: no finding is decided by its pattern.

The rule is THESIS §10.5 applied: "Law checks support a judgment; an oracle establishes it, and only for its
own question."

**Near misses, and the difference named.** "A **near miss** is a confirmed failure that differs from a right
answer in one significant, nameable way" (THESIS §7.6). The knee's mechanism, after the thesis:
1. *The failure.* An agency's answer is contradicted by its own oracle: a localized report call, gold, or the
   founder's word. "A near miss comes from an agency's own failure, confirmed by a signal independent of the
   memory" (THESIS §7.6). A refusal is never a failure.
2. *Its K-line.* The failure's profile is read beside the cases that recalled the wrong answer.
3. *The difference, named* by the exact decode: "this bank, this metric, so many more places below the
   middle" (THESIS §6.6). "A failure that differs in several respects teaches nothing until failures like it
   share one consistent difference" (THESIS §7.6).
4. *Decided against chance,* in one of three forms (THESIS §7.6): a censor of the failed answer, keyed by the
   failure's bundle; a **split K-line**, claiming only what the K-line's successes share; or nothing, and the
   failures wait.

"A code whose banks interfere, even slightly, says how far apart two cases are, never exactly in what
respect" (THESIS §7.6). The ledger is what lets the knee name the respect (Part 3 §3.5.6).

*Table 5.11. The knee's near misses, and their named differences (from Part 2 §2.5).*

| Finding | Near miss | The difference, and its bank | Writes | Its form in text (`src/RSNA_Knee/report_parser.py`) |
|---|---|---|---|---|
| Medial, Lateral Meniscus | intrasubstance degeneration | surface contact: slices on which deviant signal touches a surface (lens 7) | a censor of "tear" if the labels mean tear only; a split K-line if degeneration counts (Q3) | CONJUNCTIONS: a tear word must share the sentence |
| ACL | mucoid degeneration | continuity and course: the band unbroken, its angle to the roof unchanged (lenses 10, 11) | a censor | CONJUNCTIONS |
| MCL | bursal fluid | fluid beside the band, not around it (lens 12, in the MCL shell) | a censor | TEAR_WORDS counts "sprain" as injury |
| Effusion | physiological or trace fluid | recess volume within the normal spread (lens 12) | a censor | SMALLNESS_WORDS: "gold excludes trace/minimal effusions" |
| Baker's | a parameniscal cyst or ganglion | no neck (lens 13) | a censor; the cyst goes to the fibrous agency | — |
| Synovitis | the pad's clefts and vessels | shape and site: thin, tubular, at known places (the footprint beside lens 16's share) | a censor | — |
| Contusion | an OA marrow lesion | subchondral, under cartilage loss in a narrowed compartment (lenses 14, 17, 18) | a censor of Contusion; a case for the compartments agency | REACTIVE_EDEMA_CONTEXT: "reactive/subchondral edema is not a bruise" |
| Contusion | red marrow | T1 brighter than muscle (the T1 tissue level; lens 3's signature) | a censor (a variant) | — |
| Medial, Lateral, PF OA | one sign alone | co-location: the number of OA signs in one compartment | a censor | COMPARTMENT_OA: a compartment word and a degeneration word |

**Q3 sets the role of the textbook case.** "The surface-contact digit separating a tear from intrasubstance
signal is the textbook case" (RECIPE §8). If the meniscus labels mean tear only, it writes a censor of "tear"
for intrasubstance signal that makes no contact. If they mean tear or degeneration, "the two-slice-touch
difference separates two positives, not a positive from a negative, and the censor flips role" (RECIPE §11,
Q3): it writes a split K-line, both sides positive. The built parser carries evidence. Its conjunction rule
records: "gold gate 2026-08-29: mere mention or degeneration of a ligament/meniscus is 0; the label asserts
an INJURY — tear/rupture words in the same sentence" (`src/RSNA_Knee/report_parser.py`). On gold, then,
degeneration alone reads negative, as the tear-only reading predicts. The competition's own definition is
unverified, so Q3 stays **OPEN**, and the design holds either way. The MCL's scope, sprain or tear only, is
the same question for the ligaments (Part 2 §2.11).

**The parser already learned near misses, in words.** Each of its rules names the one difference that
separates a finding from its near miss: a tear word, a smallness word, a reactive context. Two record that
gold drew them: the conjunction rule's "gold gate 2026-08-29", and the smallness rule's "gold excludes
trace/minimal effusions". The image side must carry the same boundary in some bank. If the two sides'
profiles differ on no bank, the substrate has lost a distinction a question needs. That is the third
falsifier (THESIS §13.3 #3), measured on RECIPE §7's hard pairs (Part 3 §3.5.6).

**A noisy oracle writes censors slowly.** The thesis's calls came from an expert. The knee's come mostly from
reports, which the parser reads at 77.7% against gold (LADDER). One wrong report that wrote a censor would
veto real findings within its radius. So:
- a censor written from report-confirmed failures needs its difference to mark several such failures beyond
  chance, and not the K-line's report-confirmed successes;
- on a finding the softness table marks soft (§5.7), only gold or the founder can confirm one;
- a refusal, a Tier 2 silence or an unresolved object never writes one (THESIS §10.3).

**The confident joint error.** Every entitled series and every perturbation agreeing, and wrong, passes
layers 1 and 5 (BRIEF §5), and the committee too. Its defense is here: "the gold studies read as near misses,
and censors" (BRIEF §5); Part 6 §6.5 sets out its shared causes and the test that decides its routing.
Each such error on gold's teaching fold is read against the K-line that answered. A
named difference writes a censor; an unnamed one waits, and is counted. Their count on the judging fold
should fall as wrong answers turn into abstentions (THESIS §10.4).

**The mechanism (DESIGNED).**
- *Reads:* objects and structure words, with their contexts; the failures each oracle confirms; the exact
  decode.
- *Computes:* law-given vetoes; named differences; one of the three outcomes, against chance.
- *Emits:* vetoes, with the law named; censors and split K-lines, with their keys and named differences;
  routed readings, to the instrument, the variant buckets and the constraint reference.
- *Licensed by:* L1, L2, L4; THESIS §7.5–§7.6, §10.3; LAA §7; RECIPE §8.
- *Fails:*
  - by a law-given censor applied where its needs are absent, such as no long-TE series or no fiber
    direction;
  - by a remembered censor that vetoes real findings, written from a wrong report or from a difference that is
    the finding's own variation;
  - by a near miss whose difference no bank carries.
- *Measured by:*
  - phantoms planted inside each censor's key region: a vetoed phantom names a censor too wide;
  - gold positives vetoed, per censor, and each censor's veto count over the trajectory;
  - every line on true normals censored; gold tears inside the magic-angle window (Part 2 Table 2.8b).

### 5.7 Teaching: reports teach, gold establishes, the founder's eye takes the hard sheets

*Table 5.12. The teachers.*

| Teacher | Clean for | Its noise | Its role | How many |
|---|---|---|---|---|
| Reports, through the parser | every agency, being independent of every pixel computation | the parser reads them at 77.7% against gold (LADDER); a report is one original read, and even a perfect reader is capped near 0.88–0.92 against gold (BRIEF §2) | teach: calls become cases, with their sources | the 4,349 training studies without gold (the parser's docstring), in about a dozen languages |
| Gold | every agency | small; every gold study carries at least one positive (LADDER), so its negatives are negatives in abnormal knees | establishes; its teaching fold writes near misses | 58 (43 registered for evaluation in `tools/lens_eval2.py`) |
| True normals | "absent" cases, the hardness map, the chance populations | chosen by the parser from text alone | establish "absent" only as far as their reports do | 799 harvested, 80 fetched; 50 in the reference, 30 held out (LADDER) |
| Phantoms | lens families; the wiring of the split, the censors and the tiers | synthetic: they validate "WIRING and response only" (VERDICT) | establish response and specificity, never real-lesion validity | the library (OPEN; §5.8) |
| The founder's eye | the hard sheets | few hours (Q5) | calls on what the pictures show, never overwritten | a few dozen sheets |

**The parser, BUILT** (`src/RSNA_Knee/report_parser.py`; THEORY II.7). It is deterministic. It detects the
language by script and marker words, matches per-finding multilingual term lists with laterality in the terms,
and negates by sentence-scoped windows, 60 characters before a term and 90 after (Turkish negates after the
noun). Its conjunctions ask for a tear word with a ligament or meniscus, and a compartment word with a
degeneration word for OA. Its smallness rule follows gold, and its reactive-edema rule sets subchondral edema
apart from a bruise. It returns twelve labels, the language, the asserted sentences ("hits") and coverage.
Studies with "no_terms_found" "are reported, not folded into negatives blindly — the caller decides".
`tools/parser_validate.py` scores it on the 58 gold studies, reporting "every disagreement with language +
evidence snippet so lexicon growth is error-driven, never speculative". Its 77.7% gold gate survives the
substrate reset (LADDER). THEORY has the parser "keying/calibrating the reference and the lens/SDM recall"
(THEORY II.7). Here its labels harvest true normals and write cases. They calibrate no level or radius
(THESIS §8.2); in aggregate, as prevalence bands, they score lens-family configurations (§5.8).

**The extension, DESIGNED: from labels to localized calls** (RECIPE §5).
1. *Three states.* `sentence_asserts` already returns "asserted", "negated" or "absent" for each sentence, and
   `parse_report` collapses them to 1 or 0. A call keeps all three: +1, −1 and silence. "No effusion" is
   evidence against; an unmentioned effusion is no evidence (THESIS §7.3). A report with no terms found is
   an abstention on all twelve.
2. *Hedges.* "Possible", "cannot exclude" and "suspicious for" write an abstention, not +1. The parser reads
   "rule out" and "r/o" as negators today; a hedge is neither.
3. *Locations,* scoped to the sentence as negation is: horn, body or root; medial or lateral (already
   MEDIAL_WORDS and LATERAL_WORDS); condyle, plateau, patella or trochlea; the recesses; a ligament's segment.
   Each maps to an atlas zone where one exists (Part 2 §2.10), and to the coarser BUILT zone until then, such
   as zone 6 (`medial_compartment`, `src/RSNA_Knee/anatomy.py`) for a medial meniscal horn.
4. *Morphology and size.* Tear planes (horizontal, vertical, radial, complex) go to the orientation rows (Part
   3 §3.5.3). Size words (trace, small, moderate, large) go to a size question.
5. *The output,* per sentence: a call on a (zone, finding) pair, its ternary digits, the sentence verbatim,
   its language and the parser's version. "A report sentence then becomes a call on a (zone, finding) pair:
   the knee's version of an expert's call on a candidate." (RECIPE §5)

The lexicon grows only from gold's disagreements, as `parser_validate.py` requires. The parser stays
train-only; nothing at test depends on it (THEORY II.7).

**A call follows its object by place** (THESIS §8.3). A call names a zone, not a candidate. Its
**successor** is the committed object, or the structure reading, that holds most of the zone's deviant
voxels once the box is empty. The call goes to it, and the case's bundle is written over what the successor
holds. Three calls carry by rules of their own, after the thesis's three:
1. a call naming several sites ("both horns") carries per site;
2. a call with no clear successor, because the zone holds no deviant mass or two objects hold it equally,
   goes to the founder's sheet. For the every-finding agency it means keep looking;
3. a call naming a part the atlas does not yet draw, such as a root, waits for the zone.

**Report–gold disagreement is information.** On the 58 gold studies, each finding has a report call and a
gold label. A disagreement is one of two things, told apart by reading the hit sentence:
- a **parser miss**: the report says it, and the parser did not read it. The lexicon grows;
- a **report–gold disagreement**: the radiologist's original read and the expert's re-read differ.

Only the second measures how **soft** a finding is. The **softness table** gives, per finding:
- the rate of report–gold disagreement, with a bound from its count;
- its direction: gold positive with the report silent, as when a report omits a small effusion; or the report
  positive with gold negative, as with graded findings near the labeler's threshold.

Gold holds no all-normal study (LADDER), and the table says so. It is used five ways:
1. report-sourced cases of a soft finding carry the mark, and recall reports their share among the voices;
2. a censor on a soft finding needs gold or the founder (§5.6);
3. every bucket's first cases come from findings and phrasings where report and gold agree, since "The first
   cases are chosen for certainty rather than coverage" (THESIS §8.2);
4. hard sheets are drawn first from soft findings;
5. it is reported with each finding's expected score (Part 6 §6.6.3, Phase 9). Being one value per
   finding, it cannot move a rank within a finding's column (Part 6 §6.1.1).

Even a perfect report reader is capped near 0.88–0.92 against gold (BRIEF §2). The image side is not bound by
that cap if the test labels are re-reads like gold, since it reads the images as the re-reader does. That is
SYNTH's claim of a system "*more accurate than the input BAM file*" (SYNTH, Executive Summary), with the
report as the noisy input. Whether the test labels are re-reads is **OPEN**; the competition's data
description settles it.

**Sheets, and the founder's eye** (THESIS §8.1–§8.2). "For each candidate the structure proposes a word, and
the expert's call confirms it or corrects it" (THESIS §8.1). For each agency's question, the structure
proposes from its readings and from recall, and the localized call answers.
- *Where they agree,* the case enters at a glance: "Resemblance takes the easy half at the cost of a glance"
  (THESIS §8.2).
- *Where they disagree,* the case is hard. "The hardest calls are worth the most" (THESIS §8.2), but here the
  noisy call may be the error, so the case goes to a **hard sheet**. Each tile shows the zone in every
  entitled series, the residual over it, the report sentence verbatim, the proposed word, the nearest cases
  on both sides, the exclusion context and the hardness status.

The founder answers in a few words per agency: tear, degeneration or normal; effusion, trace, Baker's with
its neck, or another collection; contusion, OA lesion, red marrow, line or scar. "Artifact", "misplaced" and
an abstention are open to every agency. His call stands beside the report's, never over it (THESIS §8.4).
Sheets are drawn in this order:
1. soft findings;
2. recall disagreements;
3. objects on true normals that the split cannot type (§5.9): lesions the reports missed, or laws the design
   lacks;
4. Tier 2 places off the map;
5. near misses whose difference no bank names.

> "The project here...is meant to resolve "is knee" or "sad knee". MUCH more forgiving." (founder,
> 2026-10-02)

The questions are coarse, so the founder's hours go to the hard sheets, not to coverage. Whether reports,
gold and his eye are split rightly is Q5 (**OPEN**).

**Curriculum** (THESIS §10.3; RECIPE §8). "*Each agency is taught from its own oracle,* in a **curriculum**
of its own", and "The order of teaching follows what each agency consumes" (THESIS §10.3):
1. fluid first, since "an effusion changes how everything else looks" (RECIPE §8);
2. marrow and fibrous structures, which consume the fluid's takes and not each other's, in either order.
   RECIPE §8 lists marrow first, but nothing either consumes from the other fixes the order;
3. compartments, which consume marrow lesions, extrusion and degeneration;
4. every finding, last, which consumes every answer.

Within each, the certain cases come first, then the hard sheets.

**Judged by the course of its learning** (THESIS §10.4). After each step, each agency is read on gold it was
not taught on: "what it identified, abstained on and got wrong, per kind of answer and never summed".
"Turning a wrong answer into an abstention is progress." With 58 gold studies, the knee teaches on one fold
(near misses, censors, the founder's checks) and judges on the other, rotating. No study is judged by a case
or censor its own fold wrote (THESIS §8.4). Counts are small: LADDER records 7 MCL positives among the gold it
evaluated. So every rate carries its bound, and reads "insufficient" where the count cannot bound it (THESIS
§4.8). A plateau calls for a decision with the founder: "accept, teach further, or build the missing
structure" (THESIS §10.4). "No agency is admitted by beating the run without it; that run is kept to show
what the structure does alone." (THESIS §10.4) Macro-AUC on gold is reported end to end (RECIPE §8), never as
the number an agency's teaching steers by. Nothing is submitted without the founder's go (Law 8).

**The mechanism (DESIGNED).**
- *Reads:* reports, through the parser; gold labels; true normals; phantoms; the founder's calls.
- *Computes:* localized ternary calls; successors; the softness table; sheets; curricula; trajectories.
- *Emits:* cases with sources; near-miss failures (§5.6); the softness table; a trajectory per agency.
- *Licensed by:* THESIS §8, §10.3–§10.4; THEORY II.7; RECIPE §5, §8.
- *Fails:*
  - by an agency without a clean signal (THESIS §13.3 #2);
  - by learning that does not settle (THESIS §13.3 #5);
  - by a call attached to the wrong successor;
  - by parser misses counted as softness.
- *Measured by:* `parser_validate.py` per finding; successor ambiguity rates; trajectories on the judging
  fold; each memory's change "read bank by bank", until it settles (THESIS §10.4).

### 5.8 Lens families: discovered by grid, checked on planted lesions

The founder's charge, quoted at the head of Part 2, calls the document he uploaded "a rich vein to mine for
even more!" (founder, 2026-10-02). LENS is one way to mine it. Its premise: "a single "optimal" lens
configuration is insufficient. Different genomic motifs require different detection parameters" (LENS, Problem
Statement). In the knee, a tear's plane, a contusion's mechanism and an effusion's size are such sub-types.
HDCSUB reads LENS as "Law 8 ("earn the closed family") as an algorithm" (HDCSUB B.3), and Part 2 left the
families to the society (Part 2 §2.8, rule 2).

A **lens family** is a configuration of one finding's law lenses that behaves as one detector: one sane value
for each open quantity, and a route through the series. It is discovered as a local minimum, and kept as one
of the procedures its agency's K-lines route to (§5.5). It is a separate frozen configuration, not a lens's
default value: Part 2 §2.8, rule 2, fixes each default on true normals and phantoms, while a family is chosen
by aggregate prevalence matching, the count's analog (THESIS §10.1), and then validated on phantoms and gold.

*Table 5.13. LENS's phases, moved to the knee.*

| Phase | Genome (LENS) | Knee (DESIGNED) |
|---|---|---|
| 1, the grid | 12,500 threshold configurations in six dimensions, each scored by how far its detection frequencies lie from surveyed targets | per finding, the product of its lenses' sane values (Part 2 Table 2.8a) and the series routes; each scored by its firing rate per regime against the reports' prevalence band |
| 2, local minima | lower error than every neighbor within radius 0.15, separated by at least 0.005; 50–100 modes | lower error than every configuration one step away on the grid |
| 3, families | Ward linkage in parameter space; about 8 families; the lowest-error member represents each | Ward linkage over what the minima fire on; the lowest-error member represents each; the founder names it |
| 4, edge cases | 11 synthetic sequences; precision and specificity; a "motif specialization" | phantoms planted in true normals: lesions, near misses, artifacts, misregistrations; specificity and amplitude response |
| 5, the trajectory | λ profiles per family and motif | Part 4 §4.5 |
| validation | UCSC annotations | localized calls, as a consistency check; gold, which establishes |

**The prevalence is the knee's count.** LENS scores a configuration by "how far its detection **frequencies**
are from **surveyed target statistics**" (HDCSUB B.3). The knee's survey is the reports: per regime, the
share of studies whose report asserts each finding and, once calls are localized, each finding at each place.
It plays the part of the cell thesis's count, which "establishes how many, never which" and "is used only in
teaching" (THESIS §10.1). The parser's sensitivity and specificity per finding on gold
(`tools/parser_validate.py`) turn each observed share into a band, by Rogan and Gladen's closed-form
correction (1978). Nothing is fitted. Case mix differs by site, and a report's language is a rough mark of
its site, so the band is kept per regime and language group.

**Necessary, not sufficient.** A configuration whose firing rate lies far outside the band cannot be the
finding's detector. One inside it may still fire on the wrong studies. A detector that fires at random, at
the right rate, matches perfectly and carries nothing. One that fires on every study with failed suppression
may match the effusion rate by accident. So matching only proposes, and three checks follow:
1. *phantoms* (Phase 4): specificity against planted near misses and artifacts, and an amplitude response;
2. *consistency with localized calls,* per study: agreement beyond what chance gives at that prevalence, "a
   consistency check, never a score to raise" (THESIS §8.2);
3. *gold,* which establishes, on the judging fold only.

Every family's values are frozen before the runs that judge it (THESIS §8.2).

**The phantom library (DESIGNED; its contents OPEN).** LENS's edge cases were eleven synthetic sequences,
each expected to trigger a family or not to (LENS Phase 4). The knee plants its edge cases in held-out true
normals. Each is built through the signal equation, so that it is consistent across every series of its host
(Part 3 §3.3.10):
- *lesions:* effusions by volume; collections with and without a neck; geographic edemas at named marrow
  sites, with and without a line; tears by plane, slice count and orientation; ligament gaps;
- *near misses:* intrasubstance signal without contact; a line without edema; trace fluid; fluid beside the
  MCL band; a fat-pad cleft;
- *artifacts:* short-TE brightening at the magic angle; failed suppression; a ghost band;
- *input errors:* hosts misregistered by known amounts beyond the perturbation step (Part 4 §4.3).

Each kind is swept over amplitude, giving VERDICT's response curve: AUC must rise with amplitude, and the
no-lesion control must sit at chance (VERDICT, Decision 3). Two limits stay in view.
- "The synthetic world cannot answer the anatomical question ... It validates WIRING and response only"
  (VERDICT, Rationale). Phantoms never show that a family finds real lesions.
- Hosts are report-normal. A host with an unreported lesion makes its own site look like a false "for". So
  phantoms are planted where the host's own readings are quiet, and each host's deviations are recorded
  (Part 4 §4.2).

**Departure in Phase 3.** LENS clusters minima by their distance in parameter space. In the knee, two
configurations far apart in their sane values can fire on the same studies, and then they are one detector.
So minima are clustered by what they fire on, their firing sets over the corpus, with LENS's Ward linkage.
Each family's representative is its lowest-error member (LENS Phase 3). The founder names what each family
detects, since naming meaning is his (HDCSUB F.0), and the phantoms' specificity is the evidence he names it
from. The pipeline is rebuilt from LENS's specification, not its code: "I'll be rebuilding it completely
from scratch." (founder, 2026-10-02; Part 1 §1.2).

**The mechanism (DESIGNED).**
- *Reads:* lens readings over the training corpus, per regime; the prevalences and the parser's gold
  confusion; phantom responses; localized calls.
- *Computes:* firing rates per configuration; local minima; families; specificity and response;
  consistency.
- *Emits:* named, frozen families, each a procedure of its agency, with its λ-bounds read in Part 4 §4.5.
- *Licensed by:* LENS Phases 1–4; HDCSUB B.3, F.0; THESIS §8.2, §10.1; VERDICT.
- *Fails:* by a rate matched on the wrong studies; by one detector found twice; by phantoms unlike real
  lesions; by a prevalence biased by one site's case mix.
- *Measured by:* phantom specificity and amplitude response per family; consistency with localized calls;
  held-out gold per family; the overlap of the families' firing sets.

### 5.9 The three-way split, made four by two references

SYNTH splits its remaining gap three ways: "Some are TRUE encoding errors (need correction)";
"Some are TRUE biological variants (should NOT be "corrected")"; "Some are BAM errors that we're CORRECTLY
fixing". And "**The key challenge:** Distinguish these three cases automatically." (SYNTH Part II). Its tools
are three:
- Layer 0, cross-bank consistency: "Genomic Monty Hall: Each bank "opens a door"" (SYNTH Part IV, Layer 0);
- Layer 2, the template residual: "Large residuals in structurally constrained positions → errors", and
  "Large residuals in variable positions → real variants (keep!)" (SYNTH Part IV, Layer 2);
- complementary sparsity, which uses the sparser of two anti-correlated banks (ρ = −0.77) "for
  high-confidence rejection" (SYNTH Part III).

**The knee's correction.** Layer 2's reading of tightness cannot be ported to the population (RECIPE §0). A
large deviation where normal knees agree is the pathology signal, not an error (Part 1 §1.8). The reading is
kept where it belongs, on the law's residual: where the law is tight, a large typed residual is input error
(Part 3 §3.3.8). And the knee adds the cause the genome's split did not name, pathology. The split has four
classes (the accounting check, Part 2 §2.6), each read on its own reference. The scanner encodes tissue as
intensity, so its artifacts are the knee's encoding errors. The pipeline's input is the image placed by
registration, so misplacement and motion are its input errors.

*Table 5.14. The split's four classes.*

| Class | SYNTH Part II | Read by | Law | Taught by | Goes to |
|---|---|---|---|---|---|
| **Input error** | BAM errors | the registration alarm and placement margin (Part 4 §4.5); the NCC check; MISFIT high; a motion dipole (Part 3 Table 3.4); flips under R4 or R5 (Part 4 §4.3) | Law 3; L3 | normals misregistered by known amounts; the founder | the constraint reference: re-register, perturb or set aside, "never a finding" (Part 1 §1.8) |
| **Instrument** | encoding errors | a signature no tissue gives; the law's typed residual (Part 3 Table 3.4); the law-given censors | L2 | artifact phantoms; reports' artifact words; the founder | the hardness map and the censors |
| **Normal variant** | biological variants, preserved | a lawful signature, constraints holding, and a variant law's check holding | L1; Part 2 §2.5's near misses | objects surviving on true normals; reports' variant words; the founder | the variant buckets |
| **Pathology** | — | a lawful signature, constraints holding, a deviation where the population is tight, and no variant law explaining it | L4 | reports; gold | its agency's recall |

**The order (DESIGNED).** Each committed object, and each structure whose word is not MONO_UP, is typed
before any agency recalls it. As at the thesis's stage 1, the narrow and knowably correct reading acts first
(THESIS §4.2):
1. *Constraint.* If the constraint reference is broken at the object, it is input error.
2. *Consistency,* SYNTH's Layer 0 made a law. SYNTH asks whether "All banks point to same nucleotide". The
   knee asks whether one set of tissue parameters explains every series, and by how much it does not (Part 3
   §3.3.8). A signature no tissue gives, or a typed residual, is the instrument, and the law-given censors
   apply (§5.6).
3. *Variant.* With constraints holding and a lawful signature, the named variant laws are tested: red
   marrow, the physeal scar, physiological fluid, the pad's clefts, the pseudotear sites (Part 2 §2.5,
   §2.10). One that holds types the object a normal variant.
4. *Pathology.* What remains goes to its agency.

**Departure.** SYNTH's Layer 0 turns agreement counts straight into confidence levels: HIGH, MEDIUM and LOW
(SYNTH Part IV, Layer 0). The knee types the object, and lets confirmed cases say what a type means (Part 4
§4.1). SYNTH's Layer 2 corrects toward its template; the knee corrects nothing, but routes and records (Part
3 §3.3.8).

**Complementary sparsity: the cleaner pathway rejects.** Each step rejects a competing explanation, and it
reads the pathway in which that competitor is silent.

*Table 5.15. The cleaner pathway, per rejection (DESIGNED).*

| Rejecting | The competitor | The cleaner pathway | Why |
|---|---|---|---|
| edema in marrow | fat; failed suppression | T1 | fat is bright and edema dark (L2); the senior excluder (Part 4 §4.1) |
| fluid in a recess | unsuppressed fat | T1 | fluid is dark and fat bright (L2) |
| a tear in fibrous tissue | the magic angle | a long-TE series | the artifact vanishes at long TE (L2) |
| contact on a meniscal horn | partial volume at the surface | the plane at the largest angle to the surface | partial volume lies along the thick axis (L3) |
| a gap in the ACL | partial volume with the condyle | coronal | Part 2 Table 2.8b, lens 10 |

**Departure.** SYNTH picks its pathway per chunk, by counting zeros. The knee picks per place, question and
regime, by the hardness map's false-for rates in health, written before the run (Part 4 §4.2), with the
place's most reliable pair as the default (§5.3).

**Variants and artifacts are censors of pathology.** Every object that survives on a held-out true normal is,
by its report, not pathology. Typed by steps 1–3, it becomes a case of input error, instrument or variant,
with the report as its source, under the noisy-oracle rule (§5.6). The thesis: "A dense library of cells is
a dense library of censors against noise" (THESIS §9.6). Here, a dense library of confirmed variants and
artifacts is a dense library of remembered censors against "pathology" at those places. They are repulsors in
any drawing, and vetoes within their radius where written from a near miss. An object on a true normal that
no step types goes to the founder's sheet, as a lesion the report missed or a law the design lacks (Part 4
§4.2, the admission test).

**The mechanism (DESIGNED).**
- *Reads:* the constraint readings; signature digits and the law's typed residual; the variant laws; the
  hardness map.
- *Computes:* each object's class, in order, with the pathway each rejection read.
- *Emits:* input errors to the constraint reference; the instrument to the hardness map and the censors;
  variants to their buckets; pathology to recall. Only pathology bears on a finding.
- *Licensed by:* SYNTH Parts II–IV; Part 1 §1.8; Part 3 §3.3.8; L1–L4; Law 3.
- *Fails:*
  - by a variant law that swallows a real lesion: red marrow over a contusion, or a "physeal scar" that is a
    fracture with little edema;
  - by an artifact typed as a lesion, such as the magic angle where no long-TE series exists;
  - by misplacement typed as pathology where the constraint checks are weak.
- *Measured by:* the split's confusion matrix on phantoms of all four kinds; every surviving object on true
  normals typed as not pathology, with the untyped share reported; gold positives' objects typed as
  pathology.

### 5.10 What the society hands on, the build order, and what stays open

*Table 5.16. What the society hands to emission (layer 9; Part 6).*

| Reading | From | Per |
|---|---|---|
| the agency's word: PRESENT, ABSENT, DISAGREE or ABSTAIN, with its cause | §5.2 | study and finding |
| the concurrence count, in independence classes, with "single voice" marked | §5.3 | object or structure |
| the committee's outcome and the tier | §5.3, §5.4 | zone and question |
| recall: the answers standing, the voices' counts by source, the nearest cases' comparisons in whole numbers | §5.5 | object and question |
| the censors applied, with their named differences | §5.6 | object |
| the finding's softness | §5.7 | finding |
| the object's class | §5.9 | object |
| the stability fraction, the windowed drop and the law's σ, passed through, never recombined here | Parts 3–4 | object or structure |

How emission orders these readings is Q4 (Part 6 §6.1.4). Emission reads from this table the agency's
word, with ABSTAIN separated by its cause into a plain abstention, Tier 2 or unverifiable; the concurrence
count; the stability fraction; the windowed drop; and the law's σ (Part 6 §6.1.3). The rest stays in the
kept record as each score's provenance (THEORY Part IV, Law 7). Nothing in the table is a probability, and
no reading in it is combined with another inside the society.

**Build order (DESIGNED).** Each step is measured before the next. Part 6 §6.6.3 places these steps among
its phases; step 2 can run as soon as the ledger exists (Phase 5), ahead of the full society of Phase 8.
1. *Text, without pixels:* the parser's three states, hedges, locations, morphology and sizes; the
   report–gold table on gold, with parser misses split from disagreements; the softness table; L5's
   co-occurrences in text (Part 2 §2.6).
2. *Cases in place of prototypes:* the replacement for `tools/lens_eval2.py`, with trust radii from held-out
   normals and phantoms, on the current one-series substrate, once the ledger exists (Part 3 §3.6, step 5).
3. *The law-given censors,* with their lenses and zones (Part 2 lenses 4 and 5; §2.10).
4. *The agencies,* in curriculum order, each judged by its trajectory.
5. *The committee,* the gate and dissenter analysis, when the series arrive (Q6).
6. *The phantom library and the lens families.*
7. *The tiers,* switched on when the skip-miss rate allows (Part 3 §3.2.6).

**OPEN.**
- **Q3, extended.** Tear only, or tear and degeneration, for the menisci, with gold's evidence for tear only
  (§5.6); sprain or tear only for the MCL; whether OA marrow lesions count as Contusion; Baker's from what
  size (Part 2 §2.11).
- **Q4.** How emission ranks the readings of Table 5.16 (Part 6 §6.1.4).
- **Q5.** The split between reports, gold and the founder's eye, and the hours his sheets need.
- **Q6.** Which series are fetched. The committee, the gate and κ wait on it.
- **Q7.** The template stubs, two of which carry contracts this design forbids (§5.2).
- **Placement as a sixth agency** (§5.2).
- **The levels:** the gate's levels for φ and κ; the trust radii's chance populations per regime, and
  whether they are large enough to bound.
- **The phantom library's contents,** and the prevalence bands per regime and language group.
- **The test labels:** expert re-reads like gold, or derived from reports. This decides whether report–gold
  disagreement is a ceiling or a correction (§5.7).

*External reference:* Rogan WJ, Gladen B (1978), Estimating prevalence from the results of a screening test,
American Journal of Epidemiology.

## Part 6 — Emission, measurement, falsifiers, and the build plan (layer 9; recipe steps 7 and 9)

This Part closes the design. It turns the society's kept record into the twelve numbers the competition
scores (layer 9). It states what must be measured before anything is taught (recipe step 7) and how each
agency is judged afterwards (recipe step 9). It instantiates for the knee the findings that would show the
design wrong (THESIS §13.3; LAA §12), names the one failure no layer catches, and lays out the build from
the code that exists. It ends with the founder's open decisions, gathered in one list.

Throughout, a failure or a silence is kept as information, never discarded as noise: "Knowing where
something is NOT is extremely useful for knowing where something is!" (founder, 2026-10-02). **OPEN** here
marks a founder decision or a measurement not yet made. Nothing in this Part fits a model.
The emission is a fixed order over law-licensed readings, every bar is "written down before the run it
judges" (THESIS §8.2), and registration remains the one bounded utility (THEORY Part IV, Law 3).

### 6.1 Layer 9 — Emission: a rank read off the kept record

#### 6.1.1 What the metric rewards

**BUILT:** `src/RSNA_Knee/scoring.py` computes the competition's metric as pure functions. `roc_auc` is the
Mann–Whitney U statistic over tie-averaged ranks (`average_ranks`), and `macro_auc` takes the unweighted
mean over findings. `auc_status` classifies an undefined column with a named code (`no_positives`,
`no_negatives`, `empty`), never a bare boolean. Sixteen intent tests cover it (`tests/test_scoring.py`), with
Detective pins on `auc_status` and `macro_auc`. Four consequences fix the emission's form.
1. *Only order counts,* within one finding's column across studies. Any strictly monotone map of the scores
   leaves the AUC unchanged, so an emitted value carries nothing beyond its rank.
2. *A tie between classes earns half a pair* (`test_auc_tie_across_classes_counts_half`). A pile of ties is
   chance on its own pairs.
3. *Every finding weighs the same.* **Departure** from THEORY II.6, which stratifies strictness "by clinical
   importance" (E16). The metric knows no importance, so each finding's strictness is set by its agency's
   proof rule (Part 5 §5.2), never by a tier of importance.
4. *Small columns swing.* With n₊ positives, one positive moving past every negative moves the finding's AUC
   by 1/n₊. LADDER's evaluation set held 7 MCL positives. That is a label count, which the substrate reset
   leaves standing, so a single MCL study can move the MCL column by about 0.14.

#### 6.1.2 The tension, and its resolution

Three canon statements meet at layer 9:
- "No single number means anything here" (THESIS §6.7);
- "where the evidence is open, abstain (→ 0.5) rather than fabricate a confident score" (THEORY Part IV,
  Law 7);
- the system "reports where its answer is well-determined and abstains, with a graded score, where the
  propagated error is wide" (LAA §2, the Honesty Consequence).

RECIPE §9 proposed the reconciliation this Part adopts: "**emit a rank, not a verdict.**" The emitted value is
neither a meaning nor a probability. It is the contest's projection of the kept record, computed by a pure
function, with its contract (THESIS §12.5), from each study's decision and the readings behind it to a place
in an order. Emission decides nothing. Deciding or abstaining (THESIS §4.8) belongs to the society (layer 8;
Part 5), and no finding is decided by confidence coupling (Law 4).

#### 6.1.3 What emission reads, and what it never reads

For each study and finding F, emission reads five things (**DESIGNED**, as the interface layer 8 must
supply):

- **The decision word.** *Present* or *absent* when decided, with the proof rule that decided it. *Absent*
  is decided only on exclusion marks, or on recalled cases whose call is −1 (Part 5 §5.2, §5.5), never on a
  missing positive: "The negative is a fact of its own" (THESIS §7.3). Otherwise *open*, of one of four
  kinds:
  - a disagreement, kept (THESIS §10.2);
  - an abstention;
  - Tier 2, where every series is blind or hard (Part 4 §4.2);
  - *unverifiable,* where the constraint reference is broken (Part 1 §1.8).

  In Part 5's words (Part 5 §5.10, Table 5.16), PRESENT and ABSENT are the decided words, DISAGREE is the
  disagreement, and ABSTAIN is an abstention, a Tier 2 case or an unverifiable one, by its recorded cause.
- **The voices.** For each acquired series that read F's host zone, the voice is *for*, *against* or
  *silent*. An against-voice is an exclusion mark, and it counts only where its lens is readable (Part 4
  §4.1–4.2). Three things are never voices:
  - an imputed series, which is "never a voice in concurrence" (Part 3 §3.3.6);
  - a perturbation, since stability "is never counted as votes" (Part 4 §4.3);
  - a second lens on the same series, since two lenses on one series are one voice (Part 2 §2.4, item 7).
- **The stability fraction** s of the deciding reading (layer 5; Part 4 §4.3).
- **The host deviation** H. For the always-present structure that hosts F (Part 2 §2.10), H is Part 4's
  windowed ratio Q = ‖z‖²/p̂_S over the structure's most deviant window. The drop "is the reading emission
  uses" (Part 4 §4.5). Above p̂_S the drop equals (Q − 1)²·p̂_S/(2Q), which rises with Q. Below p̂_S the drop
  is zero, so every study there ties. Q therefore keeps the drop's order where the drop exists, and still
  orders the studies where it ties.

  **Departure** from BRIEF §5, layer 9, which names "the λ-peak height" among emission's readings, after
  THEORY II.5's "Peak height = confidence". In the closed form the peak's height falls as the deviation grows
  (Part 4 §4.5), so emission reads H, which keeps the drop's order, in its place (Part 1 Table 1.3).

  **DESIGNED here:** H is read on the residual of the round that committed F's object. A fracture's H is
  then the line left once its edema has gone out with its halo, and synovitis's H is the fat pad once the
  effusion has gone. This is the lawful removal changing what the remainder means (BRIEF §5, layer 6; Part 4
  §4.4).
- **The law's uncertainty** σ on the deciding readings, with the places where the law fell silent and the
  cause of each silence (Part 3 §3.3.7, §3.3.9).

**Never read: the header.** Layer 9 receives "the law's σ, and never the header" (Part 3 §3.6). A header is
"metadata", not a verdict on meaning (HDCSUB F.0), and "The headers are cheap signals, not defining
elements." (founder, 2026-10-02). No header word is an input of the emission rule (contract-tested, §6.1.6).
The regime key acts only upstream, choosing which reference, coefficients and cases a study is read against,
never as a key or weight in the order.

**Not read either: the recall margin**, which RECIPE §9 listed. Recall acts through the decision word. Its
cosine reads the banks that the voices and H already summarize, and a reading is not counted twice (Part 4
§4.5).

#### 6.1.4 The rule

**DESIGNED.** The rule has three registers, the middle one with a fixed part. Within each register, a fixed
sequence of keys orders the studies, and each key is compared only with itself across studies.

*Table 6.1. The emission rule.*

| Register | Members | Order within, first key to last | Emitted values |
|---|---|---|---|
| Upper | decided present, passing the σ guard | c₊; s-digit; H. Higher ranks higher | (0.55, 1) |
| Middle | open (disagreement, abstention); decided cases the σ guard demotes | *Literal* (Law 7): none, all at 0.5. *Ordered* (Q4): lean digit; L5 digit; ties stand | 0.5, or (0.45, 0.55) |
| Middle, fixed | unverifiable; Tier 2 | none in either variant: nothing on the population axis can be read there | exactly 0.5 |
| Lower | decided absent | c₋; s-digit; H. More exclusion, more stability or a smaller H ranks lower | (0, 0.45) |

The keys:
- **c₊** is the size of the largest set of acquired series that concur for F at the committed object and are
  pairwise independent by the gate of §6.2.2. **c₋** is the same count for exclusion marks over F's host
  zones. A pair of series that fails the gate counts as one voice.
- **The s-digit** reads s against a static middle (THESIS §6.2), set once at the terciles of s over the
  teaching studies' committed readings of F. s becomes a key only once it passes the information test Part 4
  sets for it (Part 4 §4.3). The test is run here without labels: where the keys above s tie, s must order
  planted phantoms above true normals. Until then the sequence skips it.
- **The lean digit** of an open case is +1 with more independent voices for than against, −1 with fewer, and
  0 with equal numbers, silence included.
- **The L5 digit** is +1 when a committed object of another finding completes a mechanism pattern with F:
  pivot shift, valgus, patellar dislocation or dashboard, and hyperextension if the founder accepts that
  addition (Part 2 §2.6; Q1). Otherwise it is 0. It is never −1: a
  pattern's members need not all appear, so a missing partner contradicts nothing, and "The negative is a
  fact of its own" (THESIS §7.3). Mechanism laws let findings "corroborate each other", yet "Each is still
  established only by its own oracle" (RECIPE §5). So the L5 digit orders only inside the middle register and
  never moves a study across registers.
- **The σ guard** applies to decided cases. Some proof rules rest on a reading taken where the law fell
  silent with a cause, or left the parameter unidentified (Part 3 §3.3.7, §3.3.9). A case decided that way
  is emitted in the middle register, flagged *under-determined*. This is LAA §10: where the evidence
  under-determines, "the architecture does not emit a confident number in the register it uses for a
  well-pinned one".

  The law's σ thus acts in two roles, and never twice in one role. Inside H it acts through z's denominator,
  so "a deviation measured with a wide bar counts less" (Part 3 §3.3.7). On the register it acts through the
  guard. If layer 8 never decides on such readings, the guard never fires, and every firing is a finding
  about layer 8.

**Why this order.** The keys run from the evidence least likely to be jointly wrong to the most likely:
- independent series are different evidence (RECIPE §7);
- stability is the same evidence surviving a step either way (THESIS §3.4);
- H is one statistic of one reading.

Every key except the last is a digit or a small count. In a lexicographic order a key has a say only where
the keys above it tie, so a continuous key ends the order wherever it stands. H, the magnitude, comes last
and breaks what the categorical evidence leaves tied. In the middle register, by default, only categorical
partial evidence orders, and ties stand: a magnitude that could not prove a decision does not order what was
left open. Whether H may also order there is part of Q4.

**Why no sum.** A weighted sum sets one reading's units against another's, and the one language has "no
rule for setting one lens's units against another's" (THESIS §6.6). The commit "reads apart each
independent reading … never pooling them into one score" (THESIS §4.5). And weights chosen to
raise gold AUC would put a fitted model inside the emission. Here "no weight is adjusted until outputs match
examples" (THESIS §1.3; Law 1).

**Details.**
- *Several objects for one finding.* Where a study has several objects for F, such as two contusions, F
  takes the key tuple of its strongest object. "Any" is read as the maximum, never as an average.
- *The emitted value.* Within a register of n members, a study with average rank r gets
  lo + (hi − lo)·r/(n + 1), and exact ties stay ties.
- *The ordered middle.* In the ordered variant, open cases whose lean and L5 digits are both 0 sit at
  exactly 0.5, beside the fixed cases. The groups ranked above them spread over (0.5, 0.55), and the groups
  below over (0.45, 0.5).
- *The register edges.* The edges 0.45 and 0.55 make no difference to the AUC. They are chosen so the file
  can be read: a value above 0.55 or below 0.45 is a decision, and one between them is not.

**Departures,** each argued where the society makes it.
- *From BRIEF §5, layer 8, and COMMITTEE §5.3 and §8.2* (Part 5 §5.3). The brief specifies "tie-break by the
  most reliable pair (COMMITTEE §5)", and in COMMITTEE a 2–2 tie is resolved by trusting the most reliable
  pair, then by margin-weighted voting. Here a disagreement stays open, "never broken by order, averaging or
  the strongest voice" (THESIS §10.2), since "Where two disagree, neither overrules the other" (THESIS §4.4),
  and the canon governs over the brief (BRIEF, preamble). Reliability per place acts upstream instead, as
  entitlement (Part 5 §5.3) and as the hardness map's rule that at a misleading place a "for" needs a series
  that place does not mislead (Part 4 §4.2). The most reliable pair remains the default cleaner pathway (Part
  5 §5.9), and the hard sheets read it first (Part 5 §5.7).
- *From COMMITTEE §6.3 and §11.3* (Part 5 §5.4). There all-zero-margin positions go to human review,
  "UNCERTAIN - recommend re-sequencing". A test study has no reviewer, so Tier 2 is emitted at exactly 0.5
  with its reason (Part 4 §4.2).

#### 6.1.5 What the rule does to the metric, exactly

Take one finding with n₊ positives and n₋ negatives, of which o₊ and o₋ sit in the middle register. Three
facts follow from the Mann–Whitney definition. Each is checkable with `roc_auc` on a toy column.
1. *The cost of the middle.* If every decision is right, then under Law 7 literal,
   AUC = 1 − ½ · (o₊/n₊) · (o₋/n₋). The middle register's whole cost is the product of the shares left
   open.
2. *The stake of Q4.* Ordering the middle register changes the AUC by (o₊·o₋)/(n₊·n₋) · (A_mid − ½), where
   A_mid is the AUC within the middle register. The bend pays only if partial evidence orders open studies
   better than chance, and its stake is set by how many of each class stay open.
3. *Abstention after a wrong decision never costs, in either variant.*
   - A positive wrongly decided absent earns nothing against open negatives, and at most a full pair against
     absent ones. Moved into the middle, it earns at least as much against open negatives and a full pair
     against every absent one.
   - The mirror holds for a negative wrongly decided present.

So "Turning a wrong answer into an abstention is progress" (THESIS §10.4) is exact for this metric under this
rule. Abstaining on a right decision does cost: under Law 7 literal, among other pairs, half a pair against
each open member of the other class. Abstention is honest, never free.

#### 6.1.6 The mechanism, and how it fails

- *Reads:* the decision word, the voices, s, H and σ (§6.1.3); the gate's table (§6.2.2); the static middles.
- *Computes:* registers, key tuples, average ranks, and the map from ranks to values.
- *Emits:* the twelve values per study. Beside them, per study and finding, the register, the keys and any
  guard firing are kept as findings with their consumer (THESIS §12.7).
- *Licensed by:* THEORY Part IV, Laws 4 and 7; LAA §2 and §10; THESIS §4.8, §6.7 and §10.2; RECIPE §9.
- *Fails:*
  - by confident errors in the outer registers (§6.5);
  - by a middle register that swallows a finding, whose AUC then sits near ½ by fact 1;
  - by a key that inverts order. s does so for thin real lesions, which flip through-plane by their nature
    (Part 4 §4.3);
  - by column names bound wrongly;
  - by a header leaking into the order.
- *Measured by:*
  - per finding, on the evaluation panel (§6.2.5), the 3 × 2 table of register against gold label, never
    summed;
  - the AUC with its swing 1/n₊, read twice. On gold alone, the negatives are other findings' positives,
    the confound LADDER's terminal finding names. On gold together with held-out true normals, the
    negatives include clean knees;
  - per key, the share of positive–negative pairs it decides, and the share it decides wrongly;
  - both middle-register variants side by side, with A_mid and its bound (fact 2);
  - the guard's firings, with their gold labels;
  - a contract test that no header field is among the emission's inputs (THESIS §12.5).

  The wrong-binding failure is Phase 0's gate (§6.6.3).
- *No noise:* a finding swallowed by the middle register is not a weak score to tune. It names an agency
  that lacks evidence, and Law 5 says where to look: for missing information, never for capacity.

### 6.2 Recipe step 7 — Measure the substrate before anything is taught

The step, as the thesis writes it: "*Measure the substrate* on the domain's own data before anything is
taught: whether the profiles keep the distinctions each question needs, which is H2's bridge, and whether the
views' errors are independent. An exact code does not make an observation lossless." (THESIS §13.1, step 7).
The views' independence is "measured the same way" as the bridge (THESIS §6.7). The knee adds two
instruments of its own. The fixed make-or-break is built; the λ-trajectory's shapes in health are designed
(Part 4 §4.5).

**Today only the fixed instrument can run.** The other three cannot, for three reasons:
- the build reads one series per study, so every concurrence has one voice (BRIEF §4);
- the encoder cannot name a difference (§6.2.1);
- the trajectory's closed form is not built.

#### 6.2.1 H2's bridge: do the profiles keep what each question needs?

The hard pairs come from RECIPE §7, whose four Part 3 §3.5.6 names, and from the near misses of Part 2
§2.5.

*Table 6.2. The hard pairs, and where the decode must find each difference.*

| Pair | The difference the law names | Where the decode must find it |
|---|---|---|
| Meniscal tear / intrasubstance degeneration | surface contact on ≥ 2 slices (De Smet and Tuite 2006) | the surface-contact bank. Q3 decides whether this separates a positive from a negative, or two positives |
| ACL tear / mucoid degeneration | a break, or a course flatter than the roof line | the continuity and course banks |
| MCL sprain / normal MCL; MCL / bursal fluid | fluid around the band, not beside it | the periligamentous-shell bank |
| Effusion / physiological fluid | recess volume beyond the normal spread | the recess-volume bank |
| Effusion / synovitis | the FS-bright share of Hoffa's pad, read after the effusion is out | the fat-pad bank, on the residual |
| Baker's cyst / parameniscal cyst or ganglion | the neck between the medial gastrocnemius and semimembranosus tendons | the neck bank, axial |
| Contusion / red marrow | T1 brighter than muscle | the T1 signature bank |
| Contusion / fracture | a line inside the edema reaching cortex | the line bank, after the edema's pull-out |
| Fracture / physeal scar | the line without edema | the line and edema banks together |

The mechanism (**DESIGNED**):
- *Reads:* the ledger profiles (layer 4; Part 3 §3.5) of objects whose side of a pair is called by a
  localized report call (RECIPE §5) or by gold. Only the question's banks are read, named in the layout
  before the run (THESIS §6.6).
- *Computes:*
  - for each object, whether its nearest case by the one cosine lies on its own side. Cases from the
    object's own study are excluded (THESIS §8.4). The same share is computed with the sides shuffled, and
    each share carries a bound from its count;
  - for each nearest cross-side pair, the exact decode of the difference, tallied by bank.
- *Emits:* one of three words per pair:
  - **kept:** the sides separate, and the decode names the law's difference;
  - **kept by a confound:** the sides separate, but in a bank the law does not name, such as a regime
    signature. That term then belongs in the key (LAA §8; Part 2 §2.9);
  - **lost:** no separation beyond chance.
- *Licensed by:* THESIS §1.4 (H2's bridge), §6.6, §7.6 and §13.3, finding 3.
- *Fails:*
  - when the oracle cannot say which side an object is on: unlocalized reports, or Q3 making both sides
    positive;
  - when too few cases on a side leave the share unbounded;
  - by leakage, which the rules of §6.2.5 exclude.
- *Measured by* a positive control. Phantoms that carry the law's difference by construction, for example a
  planted signal that touches the surface or stops short of it (Part 3 §3.3.10), must come out **kept**. If
  they do not, the instrument is broken, not the substrate.
- *No noise:* **lost** is not a failure of the knee. It names a missing bank (Law 5), or a label scope that
  merges two things (Q3).

**Why today's encoder cannot run it.** **BUILT:** `src/RSNA_Knee/hdc_encoder.py` writes each surviving voxel
into K = 4 random dimensions of a zone accumulator with D = 4,096 dimensions. A zone with N surviving voxels
therefore writes 4N/4,096 times per dimension. TIERED's rule is "Accuracy collapses when
`writes_per_dim > 1.5`" (TIERED §2.2), and this encoder crosses it at N = 1,536. Superposition also loses
the naming: "A code whose banks interfere, even slightly, says how far apart two cases are, never exactly in
what respect" (THESIS §7.6). The exact ledger, with one Sylvester–Hadamard row per value and whole-number
counts (THESIS §6.1), is this measurement's precondition. Part 3 §3.5.1 reads the built encoder line by
line, and notes that TIERED's collapse line is itself documented-only (HDCSUB F.4 #5).

#### 6.2.2 View independence: the gate before agreement counts

"Codebook independence is a GO/NO-GO GATE, not an assumption": in GenomeVault, a committee sharing one
codebook "gave ~100 % CORRELATED errors and bought zero error correction" (HDCSUB F.4 #4). In the knee the
committee is the series, and "Independence must come from different evidence, not different encodings"
(RECIPE §7).

The mechanism (**DESIGNED**):
- *Reads:* per series type and finding, each series' reading of F's host zone (for, against or silent), on
  studies that have an oracle.
- *Computes,* per pair of series types:
  - error indicators against the oracle. A silence is not an error: it is the informational zero (THESIS
    §6.3);
  - the φ coefficient between the two indicators, over the studies where both series spoke;
  - the joint-failure ratio κ: observed joint errors over the product of the marginal rates. "κ is the
    knee's 36,210×" (Part 4 §4.2; COMMITTEE §4.2).

  Each carries its count and bound.
- *Emits:*
  - the gate table, which says which pairs count as two voices for c₊ and c₋ (§6.1.4);
  - the κ map, handed to the hardness map as its **hard** places (Part 4 §4.2).
- *Licensed by:* HDCSUB F.4 #4; THESIS §6.2 and §6.7; RECIPE §7.
- *The bar.* GenomeVault's gate passed at "max φ < 0.25, scaled 4-way < 35, including the margin-0 worst
  case" (HDCSUB F.4 #4). It is adopted provisionally until the founder sets the knee's own bar (§6.7, item
  8), written before the run, as VERDICT's bars are "provisional until calibrated" (Part 5 §5.3 says the
  same).
- *Fails,* through its oracles, which bias it in opposite directions.
  - *Against reports* the panel is large, but the parser scores 77.7% against gold (LADDER). A report error
    makes every right series "fail" at once, so κ against reports is an upper bound on joint view error,
    inflated by the report error rate.
  - *Against gold* κ is free of report error, but it rests on 58 studies.

  A study where every series agrees and the report disagrees is kept as a *candidate soft label*:
  information about which findings the reports read softly (BRIEF §5, layer 8). It never fails the gate by
  itself.
- *Measured by:* the gap between κ against reports and κ against gold, per finding; and κ's peaks, which
  should fall on the known pitfalls (Part 4 §4.2).
- *No noise:* a failed pair is not discarded. Its correlated places are where the views are blind together,
  and that map is a lens: founder ruling 3 applied to COMMITTEE §4.2 (Part 1 §1.7).

#### 6.2.3 The fixed instrument, rerun

**BUILT:** `tools/make_or_break.py`, with the decision in `make_or_break_verdict`
(`src/RSNA_Knee/kneediff.py`).
- *Its statistic:* "the max fraction of cells whose KneeDiff residual exceeds threshold within any 9×9
  window" (VERDICT).
- *Its rule:* rank-based AUC of abnormal against held-out normal studies, with named codes:
  `insufficient_data`; `reference_absorbs` at 0.90 or above; `partial_signal` at 0.65 or above; otherwise
  `no_separation`. The bars are "provisional until calibrated" (VERDICT).
- *Its validation:* an amplitude response curve, with AUC [0.34, 0.65, 0.66, 0.91, 0.97] and a no-lesion
  control at 0.36 (VERDICT).

It never moves: "the verdict codes and the AUC statistic do not move between iterations (changing the test to
fit the rung would invalidate the ladder)" (LADDER, Consequences).

**Its standing reading** is LADDER's first compliant v5 reading on Effusion, given in full in Part 3
§3.4.1: `partial_signal` on the σ ∈ [16, 32] plateau (0.67, 0.68, 0.66; 0.68 at its center, σ = 24), against
0.58 (`no_separation`) without detrend and at σ = 8, with "several held-out TRUE normals still peg density
1.0" (LADDER, v5 first readings). Every v1–v4 number died with its substrate (LADDER, substrate reset).

**The rerun (DESIGNED):**
- *Reads:* each series type against its own reference; then the T2-ish residual of the physics substrate
  beside the raw residual (Part 3 §3.6, step 4).
- *Computes:* the unchanged statistic and verdict, with the detrend re-swept at σ ∈ {0, 8, 16, 24, 32} on
  both substrates.
- *Emits:* one row per series type and substrate, never pooled.
- *Licensed by:* VERDICT; LADDER; THEORY Part III's first question.
- *Predicts:* if layer 2 absorbs the protocol residue that detrend removes today (BRIEF §5, layer 2), the
  sweep flattens on the physics substrate, and the AUC without detrend approaches the plateau. If it does not
  flatten, the law is not absorbing that residue. The finding then concerns layer 1.
- *Fails:* by changing the instrument to fit the rung. A zone-conditioned twin is therefore a second
  instrument, with its own ladder, and never replaces the fixed one.
- *Measured by* explaining each saturating normal on one axis (Part 1 §1.8), with its tag header beside it as
  the "Cmd-F":
  - if the saturating normals cluster by regime, the cause is protocol;
  - if they cluster with the registration readings, the cause is input error;
  - if neither, they may carry what their reports missed, and go to the founder's eye.

#### 6.2.4 The trajectory's shapes, measured in health

E10 measured 62.0% AMBIGUOUS and 31.5% PEAK_DROP (HDCSUB F.2), where SYNTH had expected about 95%
MONOTONIC_INCREASE, its name for MONO_UP, under thresholds set by hand: a half's mean gradient past ±0.02
and a drop above 0.1 (SYNTH Part IV, Layer 3, `analyze_trajectory`; read in Part 4 §4.5, items 5–6, and
Part 3 §3.2.3). The knee therefore measures its shapes before naming any (BRIEF §4).

- *Reads:* held-out true normals, per structure and window.
- *Computes:* the null of the windowed drop, the rate of each word, and the agreement of the closed form with
  its sweep twin (Part 4 §4.5).
- *Emits:* each structure's null quantile, and its words' rates in health.
- *Licensed by:* THESIS §6.2, where middles are set on the teaching data and never chosen to separate cases;
  LENS Phase 5.
- *Predicts:* nearly every true normal reads MONO_UP; PEAK_DROP appears at the null quantile's own rate; and
  AMBIGUOUS is rare.
- *Fails* when AMBIGUOUS dominates in health. The instrument then does not carve the knee, and that is a
  finding about the instrument, as E10's 62% was (Part 4 §4.5).
- *Measured by:* the closed form's agreement with its sweep twin, and by phantoms, which must read PEAK_DROP
  with λ\* falling as amplitude rises (Part 4 §4.5).

#### 6.2.5 The panels, and the rules that keep measurement honest

*Table 6.3. The measuring panels.*

| Panel | What it is | Its use | Its bias |
|---|---|---|---|
| G | the 58 gold studies, an expert re-reading the images | establishes | small; every one carries at least one finding (LADDER), so a finding's negatives are other findings' positives |
| N | held-out true normals: parser all-negatives, 80 fetched of 799 harvested, 30 held out today (LADDER) | negatives; the hardness map; nulls | report-derived: an unreported lesion makes a "normal" false |
| R | report-labeled studies held out of every store | a large, noisy second oracle | the parser's 77.7% against gold |
| P | lesions planted in true normals' tissue parameters (Part 3 §3.3.10; LENS Phase 4) | label-free tests; response curves | as real as the law that makes them |

The first make-or-break runs split the gold set as 15 reference, 8 held-out negatives and 35 positives
(LADDER). Once the reference is built only from true normals, those 15 can return to G.

Five rules (**DESIGNED**), each enforced through the provenance every case keeps (THESIS §8.4):
1. *One role per study per measurement:* reference member, case source or evaluation, never two. A
   reference's members are never its evaluation negatives, whose "own residuals are biased low"
   (`tools/lens_eval2.py`).
2. *No self-comparison.* "a candidate is never compared with a case made from itself" (THESIS §8.4). Here it
   is never compared with any case from its own study.
3. *No case from gold under measurement.* Gold is never a case source while it is measured. Where gold
   teaches near misses (§6.5), it teaches in rotation: censors written from study g are withheld when g is
   read, and every number states its rotation.
4. *Every rate with its count and bound.* A count that cannot bound a rate reads "insufficient", never zero
   (Part 4 §4.2; THESIS §4.8).
5. *Bars before runs.* "Every value a reading is tested against is written down before the run it judges"
   (THESIS §8.2).

### 6.3 Recipe step 9 — Judge each agency by its trajectory

"An agency is judged by its **trajectory**, the course of its learning, never by one final number." After
each step of teaching, on data it was not taught on, "we read what it identified, abstained on and got
wrong, per kind of answer and never summed. Turning a wrong answer into an abstention is progress." (THESIS
§10.4; THESIS §13.1, step 9).

The protocol (**DESIGNED**):
- *A step of teaching* is one batch of localized report calls entered as cases, or one teaching sheet the
  founder has called (RECIPE §8). It belongs to one agency's curriculum, in the order the agencies consume:
  fluid, marrow, fibrous structures, compartments, every finding (RECIPE §8).
- *After each step* the agency's findings are read on G (in rotation) and N, with R as a second panel. Per
  finding, the triple identified, abstained and wrong is read with its bounds and never summed. By §6.1.5 the
  triple fixes much of the finding's AUC, and a move from wrong to abstained never lowers it.
- *The memory's change, bank by bank* (THESIS §10.4), is tallied by the banks in which each new case's named
  difference, and each new censor, fall.
  - Learning **settles** when new near misses name differences already named.
  - It does not settle while each new failure names a new difference: "a sign of an agency storing instances
    rather than forming rules, and the answer is more structure, not more memory" (THESIS §10.4).
- *The structure-alone run* is kept beside every step: layers 0–7 and the law checks, with no cases and no
  censors, emitted by the same rule. "No agency is admitted by beating the run without it; that run is kept to
  show what the structure does alone" (THESIS §10.4).
- *A plateau* goes to the founder: "accept, teach further, or build the missing structure" (THESIS §10.4).
- *One end-to-end number,* macro-AUC on G (RECIPE §8), is recorded at every step and chooses nothing: "A
  moving number never chooses the next change by itself" (THESIS §10.4).

The mechanism:
- *Reads:* each step's additions with their sources; the agency's decisions on G, N and R.
- *Computes:* the triples with bounds; the bank tally of new named differences; the structure-alone triple.
- *Emits:* each agency's trajectory table, and a word per step: *settling*, *not settling* or *plateau*.
- *Licensed by:* THESIS §10.3, §10.4 and §13.1, step 9.
- *Fails:* by bounds too wide on 58 gold studies to read a direction; by leakage; by a number choosing the
  next change.
- *Measured by:* the direction of each triple, replicated on R; leakage is excluded by §6.2.5's rules.

### 6.4 What would show the design wrong: nine falsifiers, measured on the knee

THESIS names six findings, "each measured on the domain", that would falsify the thesis there (THESIS
§13.3). LAA names three seams "where the account could break" (LAA §12). The founder's comparison sets their
weight. The cell domain was chosen as the harder one, and the knee "is meant to resolve "is knee" or "sad
knee". MUCH more forgiving." (founder, 2026-10-02). A falsifier that fires on the easier domain is therefore
strong evidence.

1. **Lenses that cannot resolve most of the problem** (THESIS §13.3, finding 1; H1).
   - *Measured:*
     - the black's share on N and G, per series type and in physics space. LADDER's "≥96%" died with its
       substrate and must be measured again;
     - the rounds needed to empty each study, and the round in which each gold lesion is taken;
     - on N, the emptied box: no lesion-shaped deviation left after the last look (THESIS §4.7);
     - on G, every positive finding explained by a committed object or a structure reading, the
       every-finding agency's check (RECIPE §5);
     - the structure-alone triple.

     The cell instance gives the expectation's form, not its numbers: the loop ran 14–16 rounds to empty the
     box, and every annotated cell came out in rounds 1–3 (BRIEF §3, item 7). The knee measures its own
     (Part 4 §4.4).
   - *Fires when:* the box does not empty on true normals, or the structure leaves most gold positives
     unexplained.
   - *Teaches:* either the reference does not absorb normal variation, which is THEORY Part III's first
     question, or a law and its lens are missing (Law 5).

2. **No clean signal for an agency** (finding 2; H4's bridge).
   - *Measured:* per finding, the number of localized report calls, the parser's agreement with gold
     (`tools/parser_validate.py` reports accuracy, sensitivity and specificity per finding), and the gold
     positives. An audit also checks that no case's source is the memory's own routing (THESIS §8.4).
   - *Fires when:* a finding has too few clean calls to teach from, or any case confirms itself.
   - *Teaches:* that finding's agency stays at the structure alone, and its column is emitted from the
     structure.

3. **A substrate that loses what a question needs** (finding 3; H2).
   - *Measured:* §6.2.1, on every hard pair.
   - *Fires when:* a pair is **lost**, or **kept by a confound**.
   - *Teaches:* a bank to add (Law 5), or a label scope to settle (Q3).

4. **Similar situations that do not lead to similar results** (finding 4; H3's bridge).
   - *Measured:* on G in rotation, the share of objects within some case's trust radius whose recalled call
     matches gold, against shuffled calls, within and across regimes. The trust radius itself lies "where the
     resemblances chance alone produces end", set on real data (THESIS §7.4).
   - *Fires when:* recall matches gold no better than shuffled calls.
   - *Teaches:* the context key lacks a term, such as regime, plane or zone (LAA §8), or the precondition
     fails for that finding.

5. **Learning that does not settle** (finding 5; H4).
   - *Measured:* §6.3's trajectory.
   - *Fires when:* wrong answers fall only as abstentions rise one for one, or new failures keep naming new
     differences.
   - *Teaches:* build structure, not memory. Where no structure settles it, H4 fails for that agency.

6. **Cost that does not fall** (finding 6).
   - *Measured* in counts per study, never in seconds, across teaching steps:
     - zones read at Tier 1;
     - escalations to the expensive perturbation families (Part 4 §4.3);
     - loop rounds;
     - sweep twins run.
   - *Fires when:* studies need more full analysis as teaching proceeds, so that the system is right only by
     being expensive.
   - *Teaches:* the claim that understanding is cheap fails for the knee.
   - *Scope:* this measures a direction, not a budget. The founder ruled budgets and deadlines out of scope:
     "This is about planning, theory, and ideation." (founder, 2026-10-02; BRIEF §2). E10's routing delivered
     1.11× against an expected 1.55× (HDCSUB F.2), so no saving is assumed.

7. **Specialists that lose their physical meaning** (LAA §12: decomposition "*preserves the coefficients'
   physical meaning*").
   - *Measured* (Part 3 §3.3.10):
     - a regime's coefficients, measured on two disjoint halves of its normals, agree within their spread;
     - reference tissues (joint fluid, fatty marrow, muscle) cluster by tissue, not by regime;
     - LAA's own contrast is run: "an over-flexible variant, one specialist allowed to absorb its neighbors,
       should degrade both interpretability and transfer". In the knee that variant is a gain left free per
       voxel, absorbing decay.
   - *Fires when:* coefficients cluster by regime, or the flexible variant transfers as well as the composed
     one.
   - *Teaches:* the terms do not mean what the law says. The series falls back to the BUILT raw path (Part 3
     §3.3.9).

8. **A replicate that conditions nothing** (LAA §12: without the information, "the refinement would be
   inert").
   - *Measured:* leave-one-series-out on N. The law's imputation of the withheld series is set against the
     population reference's mean for that series type, at the study's own level (Part 3 §3.3.6).
   - *Fires when:* the law predicts the withheld series no better than the population mean.
   - *Teaches:* imputation is inert. Any lens that needs an absent series stays silent, with that cause.

9. **An uncertainty that is not calibrated** (LAA §12: "error rises precisely where the propagated bar
   widens and where the neighbor field desynchronizes").
   - *Measured:*
     - e(v) is standard normal where the law holds (Part 3 §3.3.6);
     - binned by σ̂, error rises with it;
     - emitted errors concentrate where σ was wide;
     - error rises where the coherence gate falls, the knee's form of LAA's order parameter (Part 3 §3.3.6;
       LAA §9).
   - *Fires when:* error is flat across σ̂.
   - *Teaches:* σ loses its license in emission. It no longer weights H, nor grounds the guard's test of
     identifiability. Both revert: H to the population spread, the guard to silences with a stated cause.

### 6.5 The caveat that remains: confident joint errors

A **confident joint error** is a decision in which every independent view concurs, every perturbation keeps
the word, the law explains every series, and the decision is wrong. It passes layers 1 and 5 (BRIEF §5).
Part 4's table of flip axes keeps a row for it: stable under everything is "persistent: a property of the
tissue, or a confident joint error" (Part 4 §4.3, Table 4.4). The thesis states the limit: a small distance
between two carries "never shows that it holds, since two carries can agree on the same wrong neighbor. Their
agreement is a law check, which supports (§2.6); only a full measurement establishes" (THESIS §11.5). No
reading at run time catches such an error by its own agreement. The defenses attack its causes and measure
what remains.

Its causes are shared upstream. Each is something every view inherits, as one codebook gave every
GenomeVault encoder the same collisions (COMMITTEE §1.2).

*Table 6.4. The shared sources of a confident joint error.*

| Shared source | How it makes the error joint | Defense | Measured by |
|---|---|---|---|
| The study's one transform (Part 3 §3.1; Part 2 §2.4, item 5) | a misplaced frame moves every series' zone together | the placement margin and its alarm (Part 4 §4.5; DESIGNED); the NCC landmark check (ZONES Rank 2; decided, not built); the check registration below (DESIGNED here) | normals misregistered by known amounts beyond δ: the alarm must fire (Part 4 §4.3) |
| The one population reference | a normal variant the true normals lack deviates in every series | the split of Part 5 §5.9 (SYNTH Part II's three cases, made four: input error, instrument, normal variant, pathology); normal variants as L1 terms (Part 2 §2.2, item 6); enough normals per regime, since n = 20 inflates P(\|z\| > 3) about 2.8 times (VERDICT) | false-for rates on N per regime; gold near misses whose named difference is a variant: red marrow, the physeal scar, a pseudotear |
| The instrument's physics | the magic angle brightens every short-TE series; a failed suppression brightens every series from one coil | law-given censors, absolute and never votes (THESIS §7.5; Part 2 §2.3.1) | false-for inside the magic-angle window and the suppression map on N: the hardness map's **misleading** status (Part 4 §4.2) |
| The teacher | a blind spot in the reports is inherited by every case taught from them | gold read as near misses, in rotation; the founder's eye on hard sheets (Q5); the report–gold disagreement kept per finding | the per-finding report–gold confusion (`tools/parser_validate.py`); the gap between κ against reports and κ against gold (§6.2.2) |
| The atlas | a template's bias misplaces a zone for every series | the unbiased template and multi-atlas fusion (ZONES Ranks 4–5); zone agreement across planes (Part 2 §2.10) | the vote fraction at the error's place |

**The check registration (DESIGNED here).**
- *Reads:* a series from a second plane, registered independently to its own plane's template, and never
  used to read.
- *Computes:* the distance, in millimeters at the landmarks (ZONES), between the check transform and the
  study's transform.
- *Emits:* a constraint-reference reading (Part 1 §1.8), per study and per zone by its nearest landmark:
  agree, or disagree beyond one slice spacing.
- *Licensed by:* Law 3, the bounded utility run twice; THESIS §11.5's two carries.
- *Fails:* two registrations can agree on the same wrong answer, so a small distance proves nothing. And a
  study with only one plane has no check: a silence, with that cause.
- *Measured by:* deliberate misregistration beyond δ, which the check must catch, and the disagreement rate
  on true normals, which sets its null.

**The decisive test is TIERED's.** In GenomeVault, errors at margin 0 were predictable from the vector's own
features (d = 1.95), while errors at margin 2 were "uniformly distributed" (TIERED §3.1.1). Collect the
gold-confirmed confident joint errors, in rotation. Test them against the law-named predictors of Part 4's
admission test: the fiber's angle to B0, the distance in slices to a zone boundary, the law's residual type,
the atlas vote fraction, the flexion word and the regime word (Part 4 §4.2).
- **If predictable,** the context is routed to the middle register at run time, flagged. This is the knee's
  form of COMMITTEE's zero-error rule, where one flag "catches 100% of committee errors" (COMMITTEE §6.3).
  By §6.1.5, each wrong decision so moved can only raise the AUC, and each right one moved costs half a pair
  against each open member of the other class. The routing pays where errors dominate the context, as they
  did at margin 0, with an error rate near 81% (TIERED §3.1.1). The predictor's effect size and the
  context's measured error rate decide whether to route; both are written down before the run.
- **If unpredictable,** as at margin 2, the errors are this design's floor. They are counted per finding,
  each one named, and reported with the expected score. Law 5 then asks for missing information (a new law,
  lens or view), never for capacity.

Every confirmed confident joint error is also a near miss, read against the K-line it recalled (THESIS
§7.6):
- where its one named difference marks the failures beyond chance, it writes a censor;
- where the K-line's successes are the side that varies, it writes a split K-line;
- where neither holds, nothing is written, and the failures wait.

A refusal writes nothing (THESIS §10.3).

### 6.6 The build plan, from the code that exists

#### 6.6.1 What exists

*Table 6.5. The code that exists, and its fate.*

| Code | What it does | Status | Fate |
|---|---|---|---|
| `src/RSNA_Knee/scoring.py` | macro-AUC, tie-averaged, with named skip codes | BUILT | kept; scores every dry run |
| `src/RSNA_Knee/kneediff.py` | the per-cell residual, survival, window scorability, the verdict | BUILT, pure and pinned | kept |
| `src/RSNA_Knee/platonic_reference.py` | the squash (mean, spread; weighted), residual maps, mask-aware detrend, window densities | BUILT | kept; per series type, then in physics space (Part 3 §3.4) |
| `src/RSNA_Knee/anatomy.py`; `tools/build_atlas.py` | bone masks, landmarks, the twelve-label zone volume, eye-check renders | BUILT; awaiting the eye-check | kept; grows (Phase 3) |
| `src/RSNA_Knee/report_parser.py` | twelve labels from multilingual reports; negation, Turkish postposed included; 77.7% against gold | BUILT | kept; gains locations (Phase 1) |
| `tools/register_and_export.py` | assembly, N4, mask, normalization, histogram match, affine then B-spline; mm-true, 32 × 224 × 224 over 110 × 150 × 150 mm; chirality-canonical | BUILT, one series per study | rebuilt for stored values and one kept transform per study (Phase 2; Part 3 §3.1) |
| `tools/register_normals.py` | registers the true-normal pool into the ladder's template space with the same front end (`preprocess_canonical`, `histogram_match`, `register_full`) | BUILT | rebuilt with the Phase 2 front end, as `register_and_export.py` is |
| `tools/build_true_layout.py` | assembles `data/registered_true/` for the make-or-break instrument as symlinks: 50 true-normal references, 30 held out, 35 Effusion positives | BUILT | kept |
| `tools/fetch_labeled_studies.py` (`pick_series`) | one series per study: sagittal fluid-sensitive fat-suppressed, else any fluid-sensitive | BUILT | replaced by a multi-series fetch |
| `tools/make_or_break.py` | the fixed instrument | BUILT | kept unchanged |
| `src/RSNA_Knee/hdc_encoder.py` | random sparse superposition, D = 4,096, K = 4; majority-bundled prototypes | BUILT | replaced by the ledger (Phase 5) |
| `tools/lens_eval.py` | the v1 prototype lens read: leave-one-out majority-bundled prototypes per finding, read at study and zone level | BUILT | as `lens_eval2.py`: an instrument of the data layer only, never a decision |
| `tools/lens_eval2.py` | label-source split; one majority-bundled prototype per finding | BUILT | an instrument of the data layer only, never a decision (RECIPE §8; THESIS §7.1) |
| `tools/parser_validate.py`; `tools/select_normal_pool.py`; `tools/select_positive_pool.py` | the parser's gold gate; the true-normal and positive pools | BUILT | kept |
| `tests/` | 45 test functions; Detective pins on seven pure functions | BUILT; 45 pass (BRIEF §4) | kept; every new decision pinned |
| Eight template modules | text-extraction scaffold | unfilled | Q7 (§6.6.2) |

#### 6.6.2 The template stubs (Q7)

The eight modules `pipeline`, `evidence`, `domain_classifier`, `bank_evaluator`, `emission_policy`,
`coherence`, `healing` and `lexicon` are an unfilled text-extraction scaffold (BRIEF §4). Read first-hand,
several carry contracts the canon forbids.
- `pipeline.py` lists "Scale 4: Neural residual (Pattern 13) — LLM for irreducible ambiguity". `CONTEXT.md`'s
  checklist has a "Phase 7: Neural Residual" that says to "Implement LLM integration". Both break Laws 1
  and 3.
- `evidence.py`'s `compute_interference` pools bank scores into one `final_score`, adding a hand-set bonus of
  1.5 per support once there are three or more. THESIS §4.5 forbids the pooling, and the bonus is
  hand-tuned.
- `healing.py` promotes candidates into a ranked top-K list, and `emission_policy.py` sets confidence
  thresholds per schema family. These are the shapes of an extraction task, not of twelve ranked columns.
- `coherence.py`'s trajectory is a set overlap across expansion depths, with hand-set layer weights. It is not
  the λ-trajectory.

**Recommendation** (DESIGNED; the decision is the founder's, Q7):
- delete all eight;
- strike the LLM phase from `CONTEXT.md`, and the gold-string boilerplate from `.claude/CLAUDE.md`, keeping
  its column-binding gate;
- create modules named for what they do: the agencies and the emission.

A module's name and docstring are a contract later agents read (THESIS §12.5), and repurposing would keep
contracts the design contradicts. One rule from the scaffold's house rules is worth keeping: each concept
lives in one canonical module. The twelve finding names are defined today in six places:
`src/RSNA_Knee/report_parser.py`, `tools/lens_eval.py`, `tools/lens_eval2.py`, `tools/fetch_labeled_studies.py`
and both pool selectors (`tools/select_normal_pool.py`, `tools/select_positive_pool.py`). Only
`tools/parser_validate.py` already imports the parser's list.

#### 6.6.3 The phases

The phases follow two disciplines:
- *Each phase is measured before the next begins,* as each LADDER rung "was diagnosed from evidence before the
  next was built" (LADDER), and as Part 3 orders its own steps (Part 3 §3.6).
- *A go/no-go is a measurement written down before the run.* The form follows TIERED's table of targets and
  no-go thresholds (TIERED §8.2), with one difference: no phase has a target score. A no-go names a disease,
  and Law 5 says where to look.

The build runs on the founder's Mac (M1 Max, 64 GB). No GenomeVault code enters: "I'll be rebuilding it
completely from scratch." (founder, 2026-10-02).

**Phase 0 — The floor.**
- *Changes:*
  - bind the twelve column spellings from `sample_submission.csv`, the gate `.claude/CLAUDE.md` records as
    "NOT YET BOUND", and keep one canonical finding list;
  - decide Q7;
  - keep the registration transform, which is discarded today (ZONES, Consequences);
  - write the emission rule (§6.1.4) as a pure function with intent tests and Detective pins, as
    `scoring.py` was written.
- *Go/no-go:*
  - `make_or_break.py` reproduces the v5 Effusion reading (0.68 at σ = 24) on the unchanged layout, so the
    instrument is intact;
  - a dry-run file for G scores through `macro_auc` with no finding skipped, and with names matching the
    sample file.

**Phase 1 — The corpus without pixels.**
- *Changes:*
  - tag survival, series inventories, regime keys and identifiable sets (Part 3 §3.6, step 1; Part 2 §2.9);
  - parser locations: posterior horn, body, anterior horn; medial or lateral; condyle, plateau, patella;
    recess names. A report sentence then becomes a call on a (zone, finding) pair (RECIPE §5).
- *Go/no-go:*
  - falsifier 2's first reading: calls per finding, and the parser's agreement with gold per finding;
  - localized calls checked against G;
  - Q6 decided on the inventory counts.

**Phase 2 — Every series, with one transform per study.**
- *Changes:*
  - fetch every series of each study (the `train_series.csv` flags), and more of the 799 harvested true
    normals;
  - read stored values with their rescale; give a study's series one shared box center; keep one transform
    per study, carried through the shared frame (Part 3 §3.1; Part 2 §2.4, items 4–5);
  - give each plane its own canonical grid over the same 110 × 150 × 150 mm box, the sagittal grid kept;
  - build one platonic reference per series type, and per regime where counts allow;
  - add the check registration (§6.5).
- *Go/no-go:*
  - cross-series landmark agreement within one slice spacing (Part 2 §2.4);
  - chirality re-verified per plane against the 97.8% tag agreement found so far (LADDER);
  - the fixed instrument run per series type (§6.2.3);
  - κ becomes computable.

**Phase 3 — An atlas for every host structure.**
- *Changes:*
  - the zones of Part 2 §2.10: meniscal horns and bodies; ACL and PCL tubes with the roof line; the MCL band
    and shell; the LCL band; Hoffa's pad; cartilage plates; marrow subregions with the L5 sites; posterior
    recesses; the Baker's region and its tendons; the pseudotear sites;
  - coronal and axial atlases;
  - NCC refinement and its gate (ZONES Rank 2), then multi-atlas fusion and the unbiased template (ZONES
    Ranks 4–5).
- *Go/no-go:*
  - the founder's eye-check of each new zone, the one human artifact (ZONES);
  - zone agreement across planes (Part 2 §2.10);
  - NCC thresholds set on held-out annotated landmarks (PRIORART, Recipe B, step 4).

**Phase 4 — The law (layers 1–2).**
- *Changes:* the gain and decay specialists on studies with a TE contrast; then recovery and fat, the region
  scale and imputation (Part 3 §3.6, steps 3, 4 and 7); physics-space KneeDiff, T2-ish first.
- *Go/no-go:* falsifiers 7–9; the fixed instrument on the physics substrate against the raw one, with the
  detrend re-swept in both (§6.2.3).
- *A no-go* does not stop the build. The series falls back to the BUILT raw path (Part 3 §3.3.9), and L2
  enters only through the Signature lens's digits per contrast bank (RECIPE §3).

**Phase 5 — The ledger (layer 4).**
- *Changes:* the exact ledger replaces `hdc_encoder.py` for every new consumer; the zone word, with its
  skip-miss rate, and the work it saves in counts per study, never in seconds (falsifier 6), measured before
  any route is used (Part 3 §3.6, steps 5–6).
- *Go/no-go:*
  - an exact decode, and a reference twin that agrees exactly (THESIS §12.5);
  - a re-seeded codebook changes nothing (Part 4, Table 4.3, QZ4);
  - H2's bridge on every hard pair (§6.2.1; falsifier 3).

**Phase 6 — The lenses speak (layers 3, 5, 7).**
- *Changes:*
  - the lenses of Part 2 §2.8, with their exclusion marks;
  - the hardness map, built from held-out normals in building and checking halves (Part 4 §4.2);
  - the perturbation families, cheap ones first (Part 4 §4.3);
  - the λ-trajectory's closed form, its sweep twin and the placement margin (Part 4 §4.5);
  - the phantom library.
- *Go/no-go:*
  - the independence gate (§6.2.2);
  - the shapes in health (§6.2.4);
  - a response curve rising with phantom amplitude for each lens, as VERDICT requires of the instrument;
  - the hardness map replicating on its checking half;
  - s's information test.

**Phase 7 — The loop (layer 6).**
- *Changes:* commit by gated concurrence; take out with the lawful halo; the post-take check; read again; the
  last look; the emptied box (Part 4 §4.4).
- *Go/no-go:* falsifier 1; ring, hole and lobe rates on phantoms; the structure-alone triple on G, kept as
  §6.3's baseline.

**Phase 8 — The society (layer 8; Part 5).**
- *Changes:*
  - the agencies;
  - the memory of individual cases, recalled within trust radii set against chance, replacing
    `lens_eval2.py`'s prototypes as the reading of each finding;
  - censors, law-given and from near misses, with gold in rotation;
  - the curricula in order, and teaching sheets for the founder.
- *Go/no-go:* falsifiers 2, 4 and 5; a source audit with no violations; §6.3's trajectory; §6.5's
  predictability test.

**Phase 9 — Emission and the dry run (layer 9).**
- *Changes:* the rule of §6.1 wired to the record; both middle-register variants computed (Q4); the kernel
  dry run, with the internet off.
- *Go/no-go:*
  - §6.1.6's measurements;
  - falsifier 6, across the teaching steps;
  - the expected score surfaced to the founder with its bounds, with the structure-alone score beside it and
    §6.5's floor named.

Law 8 closes the build: "Build + CV-validate + dry-run the kernel; surface the expected score honestly;
submit only on the founder's explicit go" (THEORY Part IV, Law 8). Nothing is submitted without that go.

### 6.7 Open questions for the founder

**Rulings needed.**
1. **The laws (Q1).** What is missing or wrong in L1–L5? This includes Part 2's additions: the instrument
   terms, cartilage loss, extrusion, the bow tie, the axial neck, the physeal scar and hyperextension (Part 2
   §2.11).
2. **The λ peak (Q2).** Part 4 proposes confidence = identity × fidelity, in closed form. The peak is the
   James–Stein factor, and the order is that of ‖z‖²/p̂_S (Part 4 §4.5). Accepting it means that, for the
   metric, the trajectory adds no rank beyond the windowed ‖z‖²; that its "identity" role, BRIEF §5 layer
   7's "structurally ACL but abnormal", moves to the placement margin m; and that emission reads H in place of
   BRIEF §5 layer 9's λ-peak height (Part 1 Table 1.3; Part 6 §6.1.3). Accept?
3. **Label scope (Q3, extended).** Each answer fixes which near miss is a negative (Part 2 §2.5); all four
   are to be checked against the competition's label definitions.
   - Meniscus: tear only, or tear and degeneration?
   - MCL: sprain, or tear only?
   - Contusion: do OA marrow lesions count?
   - Baker's: from what size?
4. **Emission (Q4).**
   - (a) The middle register: all at exactly 0.5 (Law 7 literal), or ordered by partial evidence, at the
     stake fact 2 of §6.1.5 measures?
   - (b) The key order c, then s, then H, with σ acting only inside H and through the guard?
   - (c) Which keys may order the middle register? The proposal is the lean digit and the L5 digit; H is the
     candidate left out.
5. **The expert split (Q5).** Reports teach as localized calls, gold establishes, and the founder's eye takes
   the hard sheets: is that the right split? And may gold teach near misses in rotation (§6.2.5, rule 3)?
6. **Series scope (Q6).** A reference for every plane × contrast, or sagittal FS, coronal FS and one T1 first
   (RECIPE §11)?
7. **The template stubs (Q7).** Delete and re-create, as recommended (§6.6.2), or repurpose?
8. **The independence bar.** GenomeVault's max φ < 0.25 (scaled 4-way < 35) is adopted provisionally until
   the founder sets the knee's own bar, written before the run (§6.2.2; Part 5 §5.3). Keep it, or set the
   knee's own?
9. **The committee's tie-break.** Confirm the departure from BRIEF §5 layer 8 (and COMMITTEE §5.3, §8.2): a
   disagreement stays open and is never resolved by trusting the most reliable pair, which keeps its other
   roles (§6.1.4; Part 5 §5.3).
10. **The check registration.** Approve a second, independent registration per study as a constraint reading
    under Law 3 (§6.5).
11. **The test labels.** Are they gold-type re-reads or report-derived? Even a perfect report reader is capped
    around 0.88–0.92 against gold (BRIEF §2). The answer fixes which oracle the dry run's expected score is
    read against.
12. **The true normals.** They are report-derived, and they serve as reference, nulls and negatives at once.
    Should the founder's eye confirm a sample before they set the hardness map?
13. **Two slices across planes.** Do a sagittal and a coronal image of one place count as two slices for the
    two-slice-touch rule (Part 2 §2.11)?
14. **The four new questions of BRIEF §7.** Each now has a proposed rule, with its values left to measurement.
    Approve the rules?
    - The signal equation's feasibility: ratios, regime coefficients and silence with its cause (Part 3
      §3.3.9).
    - The jitter magnitudes: two-sided, at δ and 2δ, set per zone by the registration's measured error, with
      2δ capped below the zone's minimum lesion extent (Part 4 §4.3).
    - The hardness map: built from held-out true normals, behind a law-named admission test (Part 4 §4.2).
    - The phantom library: lesions planted in tissue parameters and forward-modeled through every series
      (Part 3 §3.3.10).
15. **Placement as a sixth agency** (Part 5 §5.2). Whether a zone lies where the atlas puts it has a clean
    oracle, normals misregistered by construction, and a check of its own, the placement margin. Should the
    constraint reference learn where registration errs, as an agency would, or only measure it?
16. **The carrier's implementation** (Part 3 §3.6). Ruling 6 bars only GenomeVault code: is the exact ledger
    shared with the cell project's, or built anew for the knee?

**Answered by measurement; reported to the founder, no ruling needed** (Part 2 §2.11; Part 3 §3.6; Part 4
§4.6; Part 5 §5.10):
- which tags survive anonymization, and which magnets are vertical-field;
- the corpus's inventories and identifiable sets;
- the fast-spin-echo and suppression coefficients per regime;
- whether the detrend survives in physics space;
- the header's percentile levels, and whether its routing saves work, counted per study;
- whether s and H add rank information beyond the voices;
- whether the closed form agrees with its twin;
- the sane values of Part 2's lens table, and the normal bursal volume the Neck lens needs (Part 2
  Table 2.8b);
- the route to coronal and axial atlases (Part 2 §2.10);
- each quantity's number of levels m, and whether any question needs cumulative writing (Part 3 §3.5.3);
- the hardness map's grain: normals per regime, the resolution of a place, and κ once the series arrive
  (Part 4 §4.6);
- the trust radii's chance populations per regime, and whether they are large enough to bound (Part 5 §5.5);
- the prevalence bands per regime and language group (Part 5 §5.8).

## Appendix A — Concordance

Each layer and mechanism, where this document designs it, the source sections it rests on, the code that
exists today, and its build status. The status words are the front matter's: **BUILT** names a code path,
**DESIGNED** a mechanism specified here, **OPEN** a decision or measurement still to come.

*Table A.1. Layers and mechanisms, with their sources and status.*

| Layer or mechanism | Designed in | Source sections | Code today | Status |
|---|---|---|---|---|
| Registration: the front end, one kept transform per study (Law 3) | Part 3 §3.1; Part 2 §2.4, items 4–5 | THEORY II.1; LADDER v5; ZONES; NOML | `tools/register_and_export.py` (`load_canonical_volume`, `derive_side`, `register_full`) | BUILT for one series per study: mm-true, chirality-canonical, N4, mask, affine then B-spline. DESIGNED: stored values with rescale; one transform kept and carried through the shared frame; a shared box center; a grid per plane |
| The landmark check by NCC, with its QC gate | Part 1 §1.8; Part 2 §2.4, §2.10 | ZONES Rank 2; PRIORART Recipe B | `tools/build_atlas.py` saves the mean template only | DESIGNED: decided in ZONES, not built |
| The check registration | Part 6 §6.5 | Law 3; THESIS §11.5 | — | DESIGNED; approval OPEN (Part 6 §6.7, item 10) |
| The two references, never merged | Part 1 §1.8 | RECIPE §0; SYNTH Part IV, Layer 2; BRIEF §4 | the chirality decision (`derive_side`) | DESIGNED; one constraint reading, chirality, BUILT |
| The domain laws L1–L5, each with its check (recipe steps 1 and 5) | Part 2 §2.1–§2.6 | RECIPE §2, §6; BRIEF §6; THESIS §2, §13.1 | — | Stated; Part 2's additions OPEN (Q1) |
| The collapse, the squint and the precision ladder | Part 2 §2.7; Part 3 §3.5.5 | THESIS §3, §12.4; HDCSUB F.3 | `n4_correct`, `normalize_intensity` (the degraded path) | DESIGNED |
| Lens 1, Deviation | Part 2 Table 2.8a; Part 3 §3.4 | THEORY II.2–II.3 | `kneediff.residual_z`, `classify_cell`; `platonic_reference.detrended_residual_map` | BUILT on raw intensity; DESIGNED in physics space |
| Lenses 2–19 (recipe step 2) | Part 2 §2.8, Tables 2.8a–b | RECIPE §3; THESIS §3.2, §13.1 | `pick_series` (plane routing, lens 6); `anatomy.joint_line` (one median midpoint, lens 18) | DESIGNED; their sane values OPEN, to be measured |
| The law-given censors: magic angle, failed suppression, edema in bone, fluid in cortex, a fracture within edema, fluid in the recesses, one structure per place, the pattern rule | Part 2 §2.3, §2.3.1; Part 3 §3.3.2; Part 5 §5.6, Table 5.10 | THESIS §7.5; LAA §7; L1, L2, L4, L5 | — (the transform the magic-angle lens needs is discarded today) | DESIGNED |
| The priors and the regime key (recipe step 3) | Part 2 §2.9; Part 3 §3.2.4 | THESIS §4.1, §13.1; LAA §8 | the Anatomical_Plane, Fluid_Sensitive and Fat_Suppression flags; `derive_side` | Flags BUILT; the DICOM tags unread; tag survival OPEN |
| The zones | Part 2 §2.10, Tables 2.10a–b | ZONES items 2–3, Ranks 4–5; RECIPE §10; PRIORART §3 | `anatomy.build_zone_labels` (twelve labels from one template study); `tools/build_atlas.py` | BUILT, awaiting the founder's eye-check; additions DESIGNED; the route to coronal and axial atlases OPEN |
| Layer 0: the tag header, the zone word, the study word, Cmd-F | Part 3 §3.2 | HDCSUB F.0–F.2; SYNTH Parts VII–VIII (E10); THESIS §4.1, §12.6; founder ruling 5 | — | DESIGNED; percentile levels and the routing saving OPEN |
| Layer 1: the MR signal equation as the network | Part 3 §3.3 | LAA §1–§2, §4–§10, §12; THESIS §13.2 | — (no code reads TR, TE or TI) | DESIGNED; feasibility OPEN |
| Layer 2: KneeDiff in physics space, the black, middles on the residual | Part 3 §3.4 | THEORY II.2–II.3; THESIS §4.2, §6.2; RECIPE §4; LADDER; VERDICT | `platonic_reference.py`, `kneediff.py` | BUILT on raw intensity; DESIGNED over tissue parameters |
| Layer 3: exclusion lenses and the partition | Part 4 §4.1 | THESIS §3.6, §4.2, §4.6, §7.3, §7.5; SYNTH Part III; founder ruling 3 | — (an exclusion cannot be written today) | DESIGNED |
| Layer 3: the hardness map | Part 4 §4.2 | COMMITTEE §4.2, §5–§6, §11; TIERED §3.1.1; THESIS §6.3, §10.3; founder ruling 3 | — | DESIGNED; its grain OPEN; κ waits on the series (Q6) |
| Layer 4: the exact ledger, the three zeros, the layout | Part 3 §3.5 | THESIS §6, §7.3, §12; HDCSUB A.1–A.3, F.3; founder ruling 5 | `hdc_encoder.py` (v1, frozen as an instrument) | DESIGNED, replacing v1 |
| Layer 5: perturbation anchors | Part 4 §4.3 | THESIS §3.4, §11.5; ZONES; LADDER; founder ruling 5 | the metric-sampling seeds of `register_full` (R4) | DESIGNED; magnitudes OPEN |
| Layer 6: the loop on the residual | Part 4 §4.4 | THESIS §1.4, §4.1–§4.8, §5.5; DAOPHOT; CLEAN | — | DESIGNED |
| Layer 7: the λ-trajectory in closed form, the placement margin, λ-bounds | Part 4 §4.5 | LENS Phase 5; SYNTH Parts III–IV, VIII; HDCSUB B.3, F.2; THEORY II.5 | `kneediff.residual_z`, `platonic_reference.max_masked_window_density` (its inputs) | DESIGNED; Q2 OPEN |
| Layer 8: the society and its five agencies (recipe steps 4 and 6) | Part 5 §5.1–§5.2 | THESIS §10; RECIPE §5 | — | DESIGNED; placement as a sixth agency OPEN |
| The series committee, the independence gate, dissenter analysis | Part 5 §5.3; Part 6 §6.2.2 | COMMITTEE §1–§6, §8; HDCSUB F.4 #4; RECIPE §6–§7; THESIS §4.4, §8.1 | — | DESIGNED; waits on the series (Q6) |
| Tiers | Part 5 §5.4; Part 3 §3.2.5 | TIERED §1.2, §3.1, §3.1.1; COMMITTEE §6, §11 | — | DESIGNED; Tier 0 waits on the skip-miss rate |
| Memory: cases, trust radii, recall | Part 5 §5.5 | THESIS §7.1–§7.4, §8.4, §10.2, §12.2; LAA §6, §8, §11 | `tools/lens_eval2.py` (majority-bundled prototypes, an instrument only) | DESIGNED |
| Near misses and remembered censors | Part 5 §5.6 | THESIS §7.5–§7.6, §10.3; LAA §7; RECIPE §8 | the parser's rules carry them in text (CONJUNCTIONS, SMALLNESS_WORDS, REACTIVE_EDEMA_CONTEXT, COMPARTMENT_OA) | DESIGNED; Q3 OPEN |
| Teaching: localized calls, the softness table, sheets, curricula (recipe step 8) | Part 5 §5.7 | THESIS §8, §10.3–§10.4; THEORY II.7; RECIPE §5, §8 | `report_parser.py` (77.7% against gold), `tools/parser_validate.py` | The parser BUILT; localized calls DESIGNED; Q5 OPEN |
| Lens families and the phantom library | Part 5 §5.8; Part 3 §3.3.10 | LENS Phases 1–4; HDCSUB B.3; VERDICT | — | DESIGNED; the library's contents OPEN |
| The split: input error, instrument, normal variant, pathology | Part 5 §5.9; Part 2 §2.6 | SYNTH Parts II–IV | — | DESIGNED |
| Layer 9: emission in three registers | Part 6 §6.1 | THEORY Part IV, Laws 4 and 7; LAA §2, §10; THESIS §4.8, §6.7, §10.2; RECIPE §9 | `scoring.py` (the metric) | DESIGNED; Q4 OPEN |
| Measuring the substrate (recipe step 7) | Part 6 §6.2 | THESIS §6.7, §13.1; HDCSUB F.4 #4; VERDICT; LADDER | `tools/make_or_break.py`, `kneediff.make_or_break_verdict` | The fixed instrument BUILT; the rest DESIGNED |
| Judging each agency by its trajectory (recipe step 9) | Part 6 §6.3 | THESIS §10.4, §13.1 | — | DESIGNED |
| The nine falsifiers | Part 6 §6.4 | THESIS §13.3; LAA §12 | — | DESIGNED |
| The confident joint error | Part 6 §6.5; Part 5 §5.6 | THESIS §11.5; TIERED §3.1.1; COMMITTEE §1.2, §6.3 | — | The remaining caveat; its defenses DESIGNED |
| The build, Phases 0–9 | Part 6 §6.6 | LADDER; TIERED §8.2; THEORY Part IV, Law 8 | Part 6 Table 6.5 | DESIGNED |
| The template stubs | Part 6 §6.6.2; Part 5 §5.2 | BRIEF §4 | eight unfilled modules in `src/RSNA_Knee/` | OPEN (Q7); deletion recommended |

## Appendix B — Glossary

Terms as this document uses them, with the place each is defined.

- **Agency.** A learner with its own question, oracle, cases and measure; "one check against one clean
  signal makes one agency" (THESIS §10.1). The knee's five are fluid, marrow, fibrous structures,
  compartments and every finding (Part 5 §5.2).
- **ALL SILENT, CONCUR, DISAGREE, SINGLE.** The committee's outcomes over entitled independence classes
  (Part 5 Table 5.5).
- **AMBIGUOUS.** The trajectory word for an instrument that disagrees with itself (the closed form and its
  sweep twin give different words) or a window whose count cannot bound its statistic; kept, never a vote
  (Part 4 §4.5).
- **Black, the.** The places the population reference licenses, resolved away as a decision kept as a
  record, never a discard; cleared by a senior and a junior filter (Part 1 §1.5; Part 3 §3.4.3).
- **Bucket.** The cases of one answer, kept per agency, question, zone class and regime (Part 5 §5.5).
- **c₊, c₋.** The size of the largest set of pairwise-independent acquired series that concur for a finding
  (c₊) or write exclusion marks against it (c₋); emission's first key (Part 6 §6.1.4).
- **Case.** One remembered example of a typed object in a context: its bundle, its call, what was expected
  of it, its context and its source (THESIS §7.1; Part 5 §5.5).
- **Censor.** A memory or a law that prevents an interpretation. A *law-given* censor forbids absolutely; a
  *remembered* censor is a repulsor in a drawing and a veto within its trust radius in recall (THESIS §7.5;
  Part 5 §5.6).
- **Check registration.** A second, independent registration of a series from another plane, used only as a
  constraint reading (Part 6 §6.5).
- **Cmd-F.** The header's bitwise query with a declared expected share; it finds and orders, never decides
  (Part 3 §3.2.5).
- **Coherence gate.** The share of covering series whose law residual lies within 2σ at a place; the law
  imputes only where they cohere (Part 3 §3.3.6).
- **Committee.** The study's acquired series, counted by independence class, as the voices of concurrence
  (Part 5 §5.3).
- **Concurrence.** Agreement among independent voices: the only way a lesion-object is committed or an
  answer assigned; refused on disagreement (THESIS §4.4–§4.5; Part 5 §5.3).
- **Confident joint error.** A decision in which every independent view concurs, every perturbation keeps
  the word, the law explains every series, and the decision is wrong (Part 6 §6.5).
- **Constraint reference.** The input-error axis: the readings that say whether the comparison is valid
  (chirality, the landmark check, the law's misfit, stability under perturbation, the placement margin)
  (Part 1 §1.8).
- **Coverage lens.** Lens 6: the effective slices a series has through a structure's zone along the
  question's axis (Part 2 Table 2.8a).
- **Decision word.** The society's word per study and finding: PRESENT, ABSENT, DISAGREE or ABSTAIN, with
  its cause (Part 5 §5.2); emission's *decided* and *open* registers (Part 6 §6.1.3).
- **Departure.** A marked place where the knee leaves a source, with the reason.
- **Drop.** The fall of the trajectory's log confidence from its peak to λ = 1; ½B²/‖z‖² when B > 0
  (Part 4 §4.5).
- **Entitlement.** A series' standing to speak for a question at a place: coverage, readability on the
  hardness map, no censor, measured rather than imputed, and not set aside by the entitlement table that
  dissenter analysis writes (Part 5 §5.3).
- **Every-finding agency.** The analog of the thesis's count, taught by the report's list of findings,
  "which ones, never where"; it adds and never trims (Part 5 §5.2).
- **Exclusion context.** The excluders that fired around a candidate, and its zone's excluded and blind
  shares for each finding, kept as a facet of how it came out (Part 4 §4.1).
- **Exclusion mark.** A −1 on one finding's question at one place, written by an entitled lens from a
  positive reading of something a law makes incompatible with the finding (Part 4 §4.1).
- **Finding.** One of the twelve scored labels, read as a zone together with a change of signature
  (Part 1 §1.5).
- **Flip-axis profile.** The share of a reading's flips in each perturbation family (Part 4 §4.3,
  Table 4.4).
- **Footprint.** Each voxel's place, values and digits, kept beside a profile (THESIS §6.5; Part 3 §3.5.4).
- **Gold.** The 58 training studies labeled by an expert re-reading the images; none is an all-negative
  knee (Part 1 §1.1). Gold establishes. It never sets a static middle (Part 3 §3.4.4), and it teaches near
  misses only in rotation (Part 6 §6.2.5).
- **H (host deviation).** The windowed ratio Q = ‖z‖²/p̂_S over the host structure's most deviant window,
  read on the residual of the committing round; emission's last key (Part 6 §6.1.3).
- **Halo.** The signal a lesion-object's law says it spreads, taken out with it: an effusion's
  partial-volume rim, an edema's feathered margin (Part 4 §4.4, Table 4.6).
- **Hardness deviation.** A silence off the hardness map, a readable place made unreadable; it goes to the
  constraint reference, never to a finding (Part 4 §4.2).
- **Hardness map.** A template-space record, built once from held-out true normals, of where each view goes
  blank, misleads or fails together in health, admitted only with a law-named predictor. Its statuses are
  readable, blind, misleading and hard (Part 4 §4.2, Table 4.2).
- **Identifiable set.** The law terms a study's series inventory can identify, per plane group and across
  planes (Part 3 §3.2.4, §3.3.3).
- **identity(λ), fidelity(λ).** The trajectory's two factors: what the prior offers, and what the data
  allows (Part 4 §4.5).
- **Imputed series.** A series run forward from the solved tissue parameters under an absent series'
  timing; marked in every reading it feeds, and never a voice (Part 3 §3.3.6).
- **Independence class.** For one question, the series whose errors the gate cannot separate; they count
  as one voice (Part 5 §5.3).
- **κ (joint-failure ratio).** The joint false rate across independent series over the product of their
  marginal rates: the knee's 36,210× (Part 4 §4.2; Part 6 §6.2.2).
- **λ\*.** The trajectory's peak, p̂_S/‖z‖² clipped to [0, 1], the James–Stein factor; written in the
  trajectory byte where E10 wrote λ_opt (Part 4 §4.5; Part 3 Table 3.1).
- **Law-named predictor.** A cause a law names (the fiber's angle to B0, distance in slices to a zone
  boundary, the law residual's type, the atlas vote fraction, the flexion word, the regime word) that
  separates failures from successes; the admission test of the hardness map and of dissents (Part 4 §4.2;
  Part 5 §5.3).
- **Ledger, the exact.** The one language: banks of Sylvester-Hadamard rows, each reading a row lit,
  bundles kept as whole-number count tables, one cosine and an exact decode (THESIS §6, §12; Part 3 §3.5).
- **Lens.** "a cheap, deliberately lossy view that measures one thing and knows no question" (THESIS
  §3.2); the knee's nineteen are in Part 2 Table 2.8a.
- **Lens family.** A configuration of one finding's law lenses that behaves as one detector, found as a
  local minimum and clustered by what it fires on (Part 5 §5.8).
- **Lesion-object.** Present or absent, and living in the residual: a fluid collection, a marrow edema, a
  fracture line, the fluid signal inside a tear (Part 1 §1.5).
- **MONO_DOWN.** The drop exceeds its null quantile and λ* falls below the grid's first step (‖z‖² above
  five times p̂_S): the prior can only overwrite. A registration alarm or an absent structure, which the
  placement margin tells apart (Part 4 §4.5).
- **MONO_UP.** The drop lies within its null range: the structure is normal as read (Part 4 §4.5).
- **Near miss.** "a confirmed failure that differs from a right answer in one significant, nameable way"
  (THESIS §7.6); the knee's are in Part 2 Table 2.5 and Part 5 Table 5.11.
- **Oracle.** The clean signal an agency is taught against, independent of what the agency learns
  (THESIS §10.1; Part 5 §5.1).
- **Orthogonal.** The third zero: the place was read, and the reading bears neither for nor against the
  question; it lights no question row, and the coverage bank counts it (Part 3 §3.5.3).
- **p̂_S.** The mean of ‖z‖² over structure S on held-out true normals: its normal scatter energy
  (Part 4 §4.5).
- **Partition.** For each finding and zone, every place is excluded, blind or in the remainder; findings
  are sought only in the remainder (Part 4 §4.1).
- **PEAK_DROP.** The drop exceeds its null quantile with an interior peak at λ* (Part 4 §4.5).
- **Phantom.** A lesion planted in a true normal's tissue parameters and forward-modeled through every
  series of its host, so that it is consistent across contrasts (Part 3 §3.3.10; Part 5 §5.8).
- **Placement margin (m).** The minimum over displacements Δ ≠ 0 of Q(Δ) − Q(0). Above its null range the
  structure is best explained at its own place; below zero it raises the registration alarm (Part 4 §4.5).
- **Population reference.** The pathology axis: the per-voxel distribution of true normals, per series
  type and regime (Part 1 §1.8; Part 3 §3.4).
- **Precision ladder.** The rungs at which a value is held, each earned by measurement before use
  (Part 2 §2.7; Part 3 Table 3.8).
- **Register.** One of emission's three bands: upper (decided present), middle (open, or demoted by the σ
  guard; a fixed part for Tier 2 and unverifiable cases), lower (decided absent) (Part 6 §6.1.4).
- **Regime key.** The header words a case is kept under; it stratifies the reference block-diagonally and
  falls back to its parent key where a cell is thin (Part 2 §2.9; Part 3 §3.2.4).
- **Registration alarm.** Raised when a displaced reference explains a structure better than its own place
  (Part 4 §4.5).
- **Residual.** What survives the black; in it a lesion is a large share (Part 3 §3.4.4).
- **s (stability fraction).** The share of the perturbations under which a reading keeps its word
  (Part 4 §4.3).
- **Sandwich status.** *Held between* or *isolated*: the static form of THESIS §11.5's two-sided check
  (Part 4 §4.3).
- **σ guard.** Demotes a decided case to the middle register when its proof rests on readings where the law
  fell silent or left a parameter unidentified (Part 6 §6.1.4).
- **Signature.** The pattern of contrast digits a tissue writes across a study's series (Part 2
  Table 2.3a).
- **Skip-miss rate.** The share of gold finding-bearing zones, and of zones holding a planted phantom, that
  Tier 0 would skip (Part 3 §3.2.6).
- **Softness table.** Per finding, the rate and direction of report–gold disagreement, parser misses set
  apart (Part 5 §5.7).
- **Specialists.** The law's terms, one each: gain, decay, recovery, fat and density, judged only at the
  composite (Part 3 §3.3.3).
- **Split K-line.** A K-line narrowed to what its successes share, written from a near miss (THESIS §7.6;
  Part 5 §5.6).
- **Static middle.** A digit's middle, set once over the residual cells of the teaching studies; never
  moved per regime, never chosen to separate cases (THESIS §6.2; Part 3 §3.4.4).
- **Structure.** Always present, one of each, placed by the atlas; read for abnormality against its own
  prior, and never taken out (Part 1 §1.5).
- **Successor.** The committed object, or the structure reading, that holds most of a call's zone's
  deviant voxels once the box is empty; the call follows it (Part 5 §5.7).
- **Three zeros.** The middle (a written row), the informational zero (a silent bank) and orthogonal (read,
  bearing neither way), kept apart (Part 3 §3.5.3).
- **Tier 0, Tier 1, Tier 2.** The header's skip of quiet zones; the series committee; questions every
  series is blind to, kept open as hardness information (Part 5 §5.4).
- **True normals.** Studies whose reports assert no finding, harvested by the parser; reference members
  and held-out normals are never mixed (Part 1 §1.1; Part 6 §6.2.5).
- **Trust radius.** Where the resemblances chance alone produces end, set per bucket on the nearest-case
  statistic (THESIS §7.4; Part 5 §5.5).
- **Two-span ratio.** |r(+2δ) − r(−2δ)| / |r(+δ) − r(−δ)|; near 2 it marks a frame-bound gradient
  (Part 4 §4.3).
- **Typed residual.** The law's unexplained part, typed by the term that explains it: motion, ghosting,
  magic angle, suppression failure, partial volume, noise floor, susceptibility, regime signature, or
  unexplained (Part 3 Table 3.4).
- **Unverifiable.** A reading where the constraints are broken; kept, and never read as normal or as a
  finding (Part 1 §1.8).
- **Zone word, study word.** The 32-bit header of a zone, or of the whole knee: paired bits read off the
  count table, with the trajectory byte inside (Part 3 §3.2.4, Table 3.1).
