# Theory of the Case — RSNA Knee Abnormality Detection as a Deterministic Data-Geometry Problem

**Status:** Canonical derived design (2026-08-18). Records the DATA LAYER in full;
the classical-AI INTELLIGENCE LAYER on top is sketched only (Part III), explicitly
to-be-designed. Written to onboard a collaborator or agent into the theoretical
construct of the project the way `ARC_AGI_3/docs/THEORY_OF_THE_CASE.md` does.

**Supremacy clause.** This document is DERIVED. The canon it derives from is:
(1) the founder's statements in the founding conversation (2026-08-18) — the
founding record, excerpted verbatim below and in `docs/FOUNDING_RECORD.md`; and
(2) the external theory and implementations they name: `law_as_architecture.md`
(law-as-topology, Society-of-Mind specialists, recollective SDM memory, near-miss
censors, regime stratification, delta-method confidence), GenomeVault's GDiff /
Byzantine-consensus / superposition-reference machinery and its HDC experimentation
(OTP lenses, multi-modal lens library, the E16 margin-as-signal reframe), GSE's
multi-scale compositional semantics (`gse/docs/THEORY.md` + the OTP↔GenomeVault
synthesis), the SoM training analysis, the Balanced Sashimi ternary architecture,
and the founder's brain-scan neuroimaging registration pipeline. Where this
document is silent, ambiguous, or wrong, canon governs. The pathology record
(Part V) is a record of THIS conversation's failures, kept so they stay
recognizable — never a source.

**Canonical references (direct paths):** see `docs/REFERENCE_MANIFEST.yaml` for the
machine-checkable list (id · path · role · sha256). Key entries:

| Source | Location |
|---|---|
| law_as_architecture (the intelligence-layer blueprint) | `~/Projects/rohan-vinaik.github.io/papers/Core Documents/AI_architecture_papers/law_as_architecture.md` |
| GDiff rationale / template | `~/Projects/genomevault/docs/GDIFF_RATIONALE.md` · `.../GDIFF_TEMPLATE_ENCODING_ARCHITECTURE.md` |
| Byzantine consensus + superposition builders | `~/Projects/genomevault/genomevault/reference/{byzantine,superposition}_consensus_builder.py` |
| Differential encoding + HDV encoder | `~/Projects/genomevault/genomevault/differential_encoding/{differences.py,gdiff/schema.py,gdiff/selective_hdv_encoder.py}` |
| HDC conceptual architecture (OTP, adaptive-k, margin) | `~/Projects/genomevault/genomevault/hdv_validation/hdc_experimentation/HDC_CONCEPTUAL_ARCHITECTURE_V8.md` |
| Multi-modal lens + λ-trajectory (the detector) | `.../hdc_experimentation/docs/MULTI_MODAL_LENS_STRATEGY.md` |
| E16 margin-as-signal + tier stratification | `.../hdc_experimentation/experiments/E16_variant_analysis/output/E16_STRATEGIC_ANALYSIS.md` |
| GSE multi-scale theory + OTP synthesis | `~/Projects/gse/docs/THEORY.md` · `~/Projects/gse/gse_otp_genomevault_synthesis.md` |
| SoM training analysis (navigation-over-features) | `~/Projects/rohan-vinaik.github.io/papers/Core Documents/LLM_WORKFLOW/SOM_TRAINING_ANALYSIS copy.md` |
| Balanced Sashimi (ternary structural decoder) | `~/Projects/ShortcutForge/research/docs/BALANCED_SASHIMI_RESEARCH.md` |
| Brain-scan registration pipeline (the alignment front-end) | `~/MentalAtlas/biodata/neuroimaging/` |
| Competition (official) | https://www.kaggle.com/competitions/rsna-knee-abnormality-detection |

---

## Part I — The Case

**The claim.** RSNA Knee Abnormality Detection is winnable by a **classical-AI
data-geometry system with no machine learning in the architecture**, because the
signal-to-noise problem — twelve subtle findings hidden in ~570 GB of MRI pixels —
is collapsible *deterministically*. A "platonic knee" reference absorbs normal
anatomy and normal variation; subtracting it leaves only the pathological residual
(~99% of the pixels are meaningless to the task and zero out); the residual, encoded
into an HDC substrate, is read by a classical multi-scale/lens architecture. This
is the same bet, and the same machine, that already produced results on the
founder's other competitions.

**The founder's statement of the case, verbatim (2026-08-18):**

> "The architecture IS no ML. I bite my thumb at ML. Maybe I'll end up using some
> small model somewhere for some reason, but NO, the architecture is NOT NOT NOT ML."

> "We have our 'platonic' knee image that's a holographic projection of some standard
> reference ones, and we have the analysis image we need to process, we can just kind
> of line it up nicely so all the positions resolve cleanly … then literally subtract!
> … that should all just zero out. Then we have the diff, which is the actual signal
> we need to process!"

> "A full image has WAY too high a [noise] ratio, it's flooded with pixels that mean
> nothing to the analysis, but the KneeDiff format eliminates 99% of the noise, and
> the HDC architecture is like the JSON format for reasoning to bring it to a classical
> architecture in an AI-readable format."

**Why this beats fitting.** AI is the genus; ML is one narrow, avoidable species of
it (founding record). The dominant reflex — throw a CNN/transformer ensemble at raw
pixels — is precisely the monolithic fitting architecture the founder's portfolio is
built to beat. `law_as_architecture` §1–3: where the structure is known, the residue
that defeats corpus-fitting is resolved by *structure plus recollection*, not by
capacity; §11 names **medical imaging from sparse views** as a target domain for this
exact architecture. The track record is the existence proof — TriageGeist matched the
leaderboard ceiling with 99.8% deterministic decisions; the harmonizing competition
won money with <1% LLM (Gemini Flash-Lite) touching the cells; ARC-AGI is
leaderboard-beating on a deterministic story-understanding engine.

**The competition shape.** $77K total: $63K main leaderboard (top 10) + **$18K
Efficiency Track** (3 prizes). Metric: macro-averaged ROC-AUC over 12 binary findings
(ACL, MCL, Medial/Lateral Meniscus, Medial/Lateral/PF OA, Effusion, Synovitis,
Baker's, Contusion, Fracture). Kernels-only, internet off, ≤9h CPU or GPU.
~819,635 DICOM slices / 570 GB; ~1,300 test studies. Multimodal: each study paired
with a multilingual radiology **report — train-only** (not present at test). Only a
small subset of training studies carry per-condition labels; the rest are derived
from the reports. `train_series.csv` gives `Anatomical_Plane × Fluid_Sensitive ×
Fat_Suppression`. Entry deadline 2026-10-15; final submission 2026-10-22.
The efficiency metric `AUC/(Benchmark − maxAUC) + RuntimeSeconds/32400` rewards
being high-signal AND cheap *simultaneously* — which this architecture is by
construction, not by trade-off. Efficiency and main-LB are the same submission.

**The carve** (which prior work does which job here):
- **GenomeVault GDiff** → the probability-space collapse ("KneeDiff"): platonic
  reference, superposition of ambiguous cells, align + subtract → residual.
- **GenomeVault HDC / OTP** → the substrate encoding: the residual becomes an
  AI-readable hypervector ("the JSON format for reasoning").
- **GenomeVault multi-modal lens + λ-trajectory** → the finding-detector.
- **GenomeVault E16** → margin-as-signal + clinical tier stratification → the 12 AUC scores.
- **GSE multi-scale** → the "more than a bag of pixels" composition (voxel→region→structure→knee).
- **Brain-scan neuroimaging pipeline** → the alignment front-end (the one bounded ML utility: registration).
- **law_as_architecture / SoM / Balanced Sashimi** → the classical INTELLIGENCE layer on top (Part III, to-be-designed).

---

## Part II — The Data Layer (recorded in FULL — the substrate, not the intelligence)

This is the "active/perception" layer in ARC's sense: cheap, approximate,
deterministic machinery that turns a giant undifferentiated grid into a handful of
clean, AI-readable candidates. It NARROWS and ENCODES; it never DECIDES a finding
(that is Part III). Its warrant is cheapness + good-enough, never correctness.
Every stage is an instantiation of built, validated GenomeVault machinery — porting
from DNA to pixels is another instantiation of the same hardware, not novel work.

### II.1 Alignment front-end (register, so the subtract is clean)
Mirror of the founder's brain-scan pipeline (`~/MentalAtlas/biodata/neuroimaging/`):
- **N4 bias correction** (`t1_n4corrected` analogue) — remove scanner intensity
  inhomogeneity, the prerequisite for a clean subtract across the diverse
  international scanner/protocol mix.
- **Background mask** (skull-strip / `t1_brain_mask` analogue) — zero out
  everything that is not the knee (off-field, leg, air) BEFORE diffing.
- **Register to the canonical knee template** (MNI-registration analogue,
  `t1_mni_registered`) — put each study in a standard reference space so positions
  correspond cell-to-cell.
- **Landmark anchors** — deterministically flag key positions to drive/verify the
  fit: patella, femoral condyles, tibial plateau, intercondylar notch. (Founder's
  open question: "maybe we should find a way to deterministically flag key positions
  to help it line up right?")
- ML is confined HERE, to the registration/segmentation utility only, exactly as in
  the brain-scan work. This is the single sanctioned bounded-ML utility; it is not
  the architecture being ML.

### II.2 The platonic reference (squash + superposition)
Byzantine weighted-vote consensus over N reference knees, position-by-position
(`reference/byzantine_consensus_builder.py::build_consensus_chromosome`,
`compute_consensus_base`). Ambiguous cells become a **statistical superposition**,
not a single value (`ConsensusBase` = value · confidence · entropy · disagreement-set
· p-value; `SuperpositionNode`/`SuperpositionPath` = candidate values × freq/confidence/
provenance).

**The load-bearing generalization (base → pixel):** a reference cell becomes a
*distribution over intensity/opacity* across the squashed reference knees. Where the
references genuinely vary — normal anatomical variation — the cell is high-entropy /
wide-spread; where they agree, low-entropy / narrow. **The cell's entropy IS its
per-cell tolerance.** Normal variation is absorbed into the reference and zeros out;
only deviation the reference does not license survives. This is the S/N collapse, and
it falls straight out of the struct GenomeVault already built (the founder's point:
the superposition base-pair was "over-engineered for genomic data … but here that base
design is VERY useful").

### II.3 KneeDiff (align + subtract → residual = signal)
Align the analysis study to the reference (II.1), then compute a **per-cell statistical
residual** — the deviation of the analysis pixel from the reference cell's distribution,
normalized by that cell's spread (z-score / Mahalanobis using the `ConsensusBase`
confidence + entropy). Off-knee background and normal anatomy cancel to ~zero; the
residual is the pathology.

> **Precision (do not port the wrong sibling):** the built diff
> `differential_encoding/differences.py` is a SPARSE *set difference* over discrete
> variant keys (matches vanish by not being emitted) — correct for genomics, WRONG
> semantics for dense continuous pixels. The dense statistical-residual operator does
> not exist in the tree yet; it is the natural continuous generalization of what the
> superposition cell stores. After the dense subtract, **threshold** and the residual
> goes sparse again (only abnormal pixels remain non-zero) — so the "matches → zero →
> sparse" behavior returns, via a statistical threshold rather than exact match.

### II.4 Multi-scale compositional HDC encode ("JSON for reasoning")
The residual is encoded into the OTP hypervector substrate. What makes it an image and
not a bag of pixels is **multi-scale composition** (GSE `docs/THEORY.md` §6; the OTP↔
GenomeVault synthesis) — NOT adjacency-linking. Distinct scales, each with its own
primitive vocabulary, co-resident in ONE shared space via disjoint bank partitions
(near-orthogonal, so scales don't contaminate), composed by **bind** (role⊗filler),
**bundle** (⊕), **permute** (ρ). A higher scale IS a composition of the one below:

  voxel (multi-channel residual: intensity/opacity across sequence × plane)
    → local region → anatomical structure (ACL, meniscus, compartment) → whole study.

This is the same machine as GSE's word→sentence(→paragraph→text) and the genomic
scale ladder the founder named (nucleotide → operon → promoter → off-site
modification/ubiquitination), grounded there in DNA biophysics. The HDC primitives
(random ternary basis, roll-permutation binding, FFT circular-convolution binding,
additive bundling, L2-norm, schema-weighted features in
`gdiff/selective_hdv_encoder.py`) are domain-general; only the value encoder is
swapped (pixel multi-channel value replacing the base→symbol lookup), and the
position/role encoder is pointed at 2-D/3-D coordinates.

### II.5 The detector — multi-modal lens + λ-trajectory
(`hdc_experimentation/docs/MULTI_MODAL_LENS_STRATEGY.md`;
`query/multi_modal_lens_discovery.py`, `biological_lens_validation.py`.)
Each finding-type is a **lens** — a specialized detector, discovered as a local
minimum in the parameter landscape and validated against known exemplars. Apply a
lens to a residual region while sweeping λ (lens influence) and read the **confidence
trajectory**:
- **monotonic increase** → matches the normal consensus → nothing there;
- **peak-then-drop** → the region IS structurally this thing AND deviates from its
  normal consensus → **the finding present**. The lens supplies "this is the ACL"
  without forcing to consensus; the intermediate-λ peak is exactly "structurally ACL,
  but abnormal." Peak height = confidence;
- **monotonic decrease** → wrong lens.

The variant-preservation mechanism IS the pathology detector. "TATA box with a SNP" ≈
"ACL with a tear."

### II.6 Margin-as-signal + tier stratification → the 12 AUC scores
(`E16_variant_analysis/output/E16_STRATEGIC_ANALYSIS.md`.) E16's reframe: low-margin
cells are NOT decode failures — they are differential signals of real variation.
Preserve margin as queryable confidence; stratify confidence thresholds by clinical
importance (genomic Tier-1 = ClinVar/COSMIC/exon strict; Tier-3 = intergenic relaxed).
For the knee: the residual's low-margin cells ARE the pathology; per-finding /
per-region tiers set strictness; margin → the per-finding confidence that becomes the
macro-AUC output. "Treat low-margin as variant, not error" = "treat deviation-from-
normal as pathology, not scanner noise."

### II.7 Report parser = train-only label oracle
A deterministic multilingual radiology-report → 12-label extractor (negation +
laterality + multilingual MSK lexicon) generates clean pseudo-labels across the whole
training set, keying/calibrating the reference and the lens/SDM recall. The weak-
supervision problem closes symbolically (the swiss_legal "deterministic pipeline
generates the training data" pattern). The report is train-only; nothing at test time
depends on it.

**Data-layer pipeline (one line):**
`register → platonic-subtract (KneeDiff) → threshold → multi-scale HDC encode →
per-finding lens λ-trajectory → margin/tier confidence → 12 AUC scores.`

---

## Part III — The Intelligence Layer On Top (SKETCH — to be designed)

> This part is deliberately light. The founder's instruction (2026-08-18): "some
> light work as well to capture the shape of the classical AI architecture that will
> go on top of it. We need to finish designing that more directly and clearly."
> Recorded as intent, not as standing design. Do not build from this Part as if it
> were specified; it names the shape and the source, and defers the derivation.

The two-layer law (from ARC's Theory of the Case, §III.0): the data layer (Part II)
and the intelligence layer are **co-equal in execution** (nothing runs without the
substrate) but the intelligence layer alone has **authority over MEANING**. The
substrate proposes candidates with cheap confidence/gestalt priors; it may NARROW by
probability. The intelligence layer DECIDES the findings — and the same probabilistic
machinery is *forbidden* from deciding, because a finding decided by confidence-coupling
is the failure mode, not the method.

The intended source for the intelligence layer is `law_as_architecture.md`, whose
five-part architecture transposes here:
- **Law as topology** — the anatomical/radiological forward model (what a normal knee
  looks like across sequences/planes; how each abnormality manifests as signal changes
  in specific tissues) wired as the network, decomposed into a **Society of first-order
  finding-specialists** (ligament / meniscus / cartilage-OA / fluid / bone), each
  vibing its thin unknown, supervised only at the composite.
- **Recollective memory** — Kanerva SDM over balanced-ternary hypervectors, recalling
  finding-coefficients by *resemblance*, regime-keyed (scanner × plane × sequence ×
  patient), calibrated from the report-derived labels.
- **Near-miss censors** — anatomically impossible findings made unrepresentable, not
  penalized.
- **Regime stratification** — the diverse international scanner/protocol mix as the
  regime key.
- **Delta-method confidence** — uncertainty propagated through the law's own Jacobian,
  so the per-finding AUC confidence is intrinsic, and the system abstains (→ 0.5) where
  the evidence leaves the answer open.

The ternary structural decoder of Balanced Sashimi and the SoM navigation-over-
features pattern are candidate realizations of the specialists; which to use is part
of the deferred design. **The open question to resolve first** (the make-or-break of
the whole case): does the entropy-weighted superposition reference actually absorb
normal anatomical variation and leave ONLY pathology in the residual? Everything above
assumes it; it is the first thing to test.

---

## Part IV — The Laws

1. **The architecture is not ML.** AI is the genus; ML is one avoidable species. Never
   reduce the one to the other, never call the architecture "small ML," never frame a
   deterministic/vector-symbolic method as a diminished special case of ML.
2. **No smuggling.** "No algorithm beats its data's correctness" is garbage-in-garbage-
   out common sense, NOT a warrant to reintroduce ML. Any reach for a learned model
   must name itself as a bounded utility and justify its boundary.
3. **One sanctioned bounded-ML utility: registration/normalization** (II.1), exactly
   as in the brain-scan pipeline. Nothing else learns.
4. **The data layer narrows and encodes; it never decides a finding.** Confidence /
   gestalt / probability are legitimate in Part II (they only narrow) and FORBIDDEN in
   Part III (deciding a finding by confidence-coupling is the disease).
5. **Iterate the encoder, not the model.** The AUC ceiling is set by signal quality
   (the reference, the diff, the lenses), never by model capacity. When it plateaus,
   the first hypothesis is "the signal is missing information," never "add capacity."
6. **Margin / deviation is signal, not error** (E16). Low confidence against the
   reference is the pathology channel, not noise to suppress.
7. **Provenance and abstention.** Every finding traces to a derivation; where the
   evidence is open, abstain (→ 0.5) rather than fabricate a confident score.
8. **Never auto-submit.** Build + CV-validate + dry-run the kernel; surface the
   expected score honestly; submit only on the founder's explicit go (inherited from
   the Kaggle_Killer submission protocol).

---

## Part V — The Pathology Record (this conversation's failures, kept recognizable)

Recorded so the same drifts are recognizable next time. Both were the agent
substituting fluent ML-shaped defaults for the specified classical-AI mechanism.

**First death — ML substitution.** The agent asserted "the main leaderboard will be
won by heavy CNN/transformer ensembles" and framed the architecture as "ML, just
small and downstream, fed pre-computed features." Diagnosis: reducing AI (the genus)
to ML (the species); crowning the one architecture the portfolio is built to beat;
using the signal-quality-ceiling truism as a covert re-entry point for ML. The tell:
splitting the world into "your symbolic stuff (caps out)" vs "real ML (needed to
win)"; any sentence where a learned backbone is "necessary for a high score."

**Second death — token-matching the multi-scale concept.** Asked "does GenomeVault
link nucleotide *i* to *i+1*?", found only the 1-D hinge, and declared a "2-D
neighbor-binding gap" — genuine new research. Diagnosis: token-matching adjacency
instead of grasping the concept. The real mechanism is **multi-scale compositional
resolution** (Part II.4), built and validated for genomics; porting to 2-D/3-D is
instantiation, not research. Also over-weighted "not built" generally — treating "the
DNA code has no literal pixel path" as a gap when it is the obvious next instantiation
of the same hardware. The tell: calling an instantiation a "genuine build gap";
asking an adjacency question of a compositional system.

The recovery from both is this document and the corrected memory
(`~/.claude/projects/-Users-rohanvinaik-Projects-Kaggle-Killer/memory/`:
`feedback-architecture-is-AI-not-ML`, `project-kneediff-genomevault-port`).
