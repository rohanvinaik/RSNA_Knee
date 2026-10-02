# RSNA Knee Abnormality Detection — `RSNA_Knee`

> A classical-AI data-geometry entry for the RSNA Knee Abnormality Detection
> competition. **No machine learning in the architecture** — the pixels are collapsed
> deterministically ("KneeDiff") and read by a classical multi-scale/lens system.
> The design and its theory are recorded the way `ARC_AGI_3/` records theirs.

## Read in this order

1. **`AGENTS.md`** — arriving-fresh onboarding + the anti-solipsism protocol. Read
   before proposing anything; this project has an ML-substitution failure mode.
2. **`docs/THEORY_OF_THE_CASE.md`** — the canonical derived design: the Case, the
   **data layer in full** (Part II), the **intelligence layer sketch** (Part III,
   to-be-designed), the 8 Laws (Part IV), the pathology record (Part V).
3. **`docs/FOUNDING_RECORD.md`** — the verbatim founder canon (2026-08-18) the design
   derives from.
4. **`docs/REFERENCE_MANIFEST.yaml`** — the external corpus (papers + GenomeVault/GSE
   code), machine-checkable with sha256.
5. **`decisions/`** — the dated decision log (ADR-style), including the founding decisions.

## The one-line design

`register → platonic-subtract (KneeDiff) → threshold → multi-scale HDC encode →`
`per-finding lens λ-trajectory → margin/tier confidence → 12 macro-AUC scores`

…and on top of that substrate, a classical intelligence layer (law-as-architecture:
Society of finding-specialists, censors, regime stratification, recollective SDM) —
**still to be designed** (THEORY Part III).

## Status (2026-08-18)

- **Data layer:** designed and recorded in full (THEORY Part II). Nothing built yet.
- **Intelligence layer:** shape captured, derivation deferred (THEORY Part III).
- **First thing to build/test:** the make-or-break bet — does the entropy-weighted
  superposition reference absorb normal anatomical variation and leave only pathology
  in the residual? (THEORY II.2, Part III closing note.)
- **Competition:** $77K, macro-AUC over 12 findings, kernels-only ≤9h, Efficiency
  Track. Entry deadline 2026-10-15; final 2026-10-22. Data NOT yet downloaded; the
  competition scaffold (`bootstrap_competition.sh`) has NOT been run.

## Provenance

This folder records the design from the founding conversation of 2026-08-18. The
corrected cross-session memory lives at
`~/.claude/projects/-Users-rohanvinaik-Projects-Kaggle-Killer/memory/`
(`project-kneediff-genomevault-port`, `feedback-architecture-is-AI-not-ML`).
