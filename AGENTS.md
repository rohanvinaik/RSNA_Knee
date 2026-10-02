# For agents (and humans) arriving fresh — read this before proposing anything

This project will look wrong to trained instincts. It is a computer-vision medical-
imaging competition, and the design contains **no machine learning in the
architecture** — no CNN, no transformer, no learned backbone over pixels. That is not
an oversight to be corrected; it is the thesis, and it is load-bearing. This file is
the map from *that looks like it's missing the model* to *where it says why*.

## Step 0 — ground before acting (the anti-solipsism protocol)

This design has been re-derived from the founder twice in one conversation because the
agent substituted fluent ML-shaped defaults for the specified classical-AI mechanism
(see `docs/THEORY_OF_THE_CASE.md` Part V — the two deaths). The recovery discipline is
mechanical, and it applies to you:

1. Read, in order: `README.md` → this file → `docs/THEORY_OF_THE_CASE.md` (the design,
   its data layer in full, and its 8 Laws) → `docs/FOUNDING_RECORD.md` (the verbatim
   founder canon the design derives from) → `docs/REFERENCE_MANIFEST.yaml` (the
   external corpus, with hashes).
2. Before proposing or modifying any design-derived component: restate, in your own
   words, at MECHANISM level — what is the platonic reference, what does "subtract"
   compute numerically, what is a lens, what does the λ-trajectory decide — and have
   the founder confirm it. A correct-sounding paraphrase is not the test; the data-flow
   is. This is the check that caught every drift that mattered.
3. The two-step from the founder's global rules governs here: DIAGNOSE symbolically
   (Serena `find_symbol` / `find_referencing_symbols`, never grep Python source — a
   hook blocks it) before touching anything; PIN behavior after. Reference genomics
   code lives in `~/Projects/genomevault`; do not read Python as text.

## Stop — I can explain (the it-looks-like-it's-missing-the-model defense)

**"Where is the model?"** There isn't one, by design. AI is the genus; ML is one
narrow, avoidable species (Law 1). The founder's track record is the existence proof:
TriageGeist hit the leaderboard ceiling with 99.8% deterministic decisions; the
harmonizing competition won money with <1% LLM; ARC-AGI is leaderboard-beating on a
deterministic story engine. Proposing a CNN/transformer ensemble "to actually win" is
the FIRST death (Part V), and it demolishes the design rather than extending it.

**"Images need a learned encoder for the pixels."** No. The pixels are collapsed
deterministically: register to a "platonic knee" reference, subtract, and ~99% of the
pixels (background, normal anatomy) zero out (`KneeDiff`, THEORY Part II.2–II.3). The
residual — the pathology — is encoded into an HDC substrate ("the JSON format for
reasoning"). The only learned utility anywhere is **registration** (Law 3), exactly as
in the founder's brain-scan pipeline.

**"There's no cross-pixel / spatial model — it's just a bag of pixels."** The spatial
structure is handled by **multi-scale composition** (THEORY II.4), not adjacency-
linking. voxel → region → structure → whole-knee, composed by bind/bundle/permute in a
shared OTP space, scales kept orthogonal by bank partition — the same machine as GSE's
word→sentence→text. Asking "does pixel *i* link to *i+1*?" is the SECOND death (Part V).

**"HDC is a neural embedding."** No. HDC / VSA here is Kanerva SDM + balanced-ternary
hypervectors — deterministic, algebraic, auditable. Binding, bundling, permutation,
and similarity-decode; margin = confidence. No weights are trained.

**"The data layer decides the findings."** No. The data layer (Part II) NARROWS and
ENCODES; it may use confidence/gestalt priors because it only narrows. The intelligence
layer (Part III, to-be-designed) DECIDES, and probabilistic confidence-coupling is
FORBIDDEN there (Law 4). Co-equal in execution; never co-equal in authority over meaning.

## What this actually is

A classical-AI data-geometry system for RSNA Knee Abnormality Detection. A "platonic
knee" reference (squashed from public references, ambiguous cells as statistical
superposition) is registered to each study and subtracted, leaving a low-noise
residual; the residual is encoded multi-scale into an HDC substrate; per-finding lenses
read it via λ-trajectory (peak-then-drop = abnormal); margin + clinical tiers produce
the 12 macro-AUC confidences. On top of that substrate goes a classical intelligence
layer (law-as-architecture: Society of finding-specialists, near-miss censors, regime
stratification, recollective SDM, delta-method confidence) — sketched in Part III,
not yet designed. The data layer is recorded in full; the intelligence layer is the
next design work.

## The working method (probe symbolically, pin behaviorally, verify end-to-end)

- **Diagnose before designing** — never design against a signature you have not read;
  never trust a null before verifying the wiring that should have produced a non-null.
- **The make-or-break test first** — before building anything downstream, verify the
  core bet: does the entropy-weighted superposition reference actually absorb normal
  anatomical variation and leave ONLY pathology in the residual? Everything assumes it.
- **Iterate the encoder, not the model** (Law 5). When AUC plateaus, the signal is
  missing information; improve the reference / diff / lenses, never "add capacity."
- **Never auto-submit** (Law 8). Build + CV-validate + dry-run the kernel; surface the
  expected score honestly; submit only on the founder's explicit go.
