# Decision: Classical-AI data-geometry entry; the data layer is a GenomeVault GDiff port

**Date:** 2026-08-18
**Status:** accepted
**Context:** Founding conversation for the RSNA Knee Abnormality Detection entry. The
agent twice re-derived an ML-shaped design and was corrected (see THEORY Part V). This
records the settled foundation so it is not re-litigated.

## Decision

1. **The architecture contains no machine learning.** AI is the genus; ML is one
   avoidable species. The entry is a classical-AI data-geometry system. The single
   sanctioned bounded-ML utility is image **registration/normalization** (front-end
   only), exactly as in the founder's brain-scan pipeline.
2. **The data layer is an instantiation of GenomeVault's GDiff machinery** ("KneeDiff"),
   recorded in full in THEORY Part II:
   - platonic reference by Byzantine consensus over squashed reference knees, ambiguous
     cells as statistical superposition (base→pixel generalization);
   - align + per-cell statistical residual (NOT the sparse set-diff `differences.py`),
     then threshold → sparse pathological residual;
   - multi-scale compositional HDC encode (voxel→region→structure→knee) via
     bind/bundle/permute in a shared OTP space;
   - per-finding lens + λ-trajectory detector (peak-then-drop = deviation);
   - E16 margin-as-signal + clinical tier stratification → the 12 macro-AUC scores;
   - deterministic multilingual report→12-label parser as the train-only label oracle.
3. **The intelligence layer on top is sketched, not designed** (THEORY Part III):
   law-as-architecture (Society of finding-specialists, near-miss censors, regime
   stratification, recollective SDM, delta-method confidence). Its derivation is the
   next design work.

## Rationale

The founder's track record falsifies the "need a learned backbone to win" prior
(TriageGeist ceiling at 99.8% deterministic; harmonizing won with <1% LLM; ARC-AGI
leaderboard-beating on a story engine). `law_as_architecture` §11 names medical
imaging from sparse views as a target for this exact architecture. The efficiency
metric rewards high-signal-AND-cheap, which this design is by construction. Porting DNA
machinery to pixels is another instantiation of the same hardware, not novel research.

## Alternatives Considered

- **CNN/transformer ensemble over raw pixels** — rejected. It is the monolithic fitting
  architecture the portfolio is built to beat, and adopting it demolishes the design
  rather than extending it (THEORY Part V, first death).
- **"Small ML downstream of a deterministic encoder" (SoM-style navigation net)** —
  rejected as a framing: it reduces AI to ML and mis-describes the thesis. A small model
  may appear only as a bounded utility, never as the architecture.
- **sparse-wiki as the collapse mechanism** — rejected; the founder clarified the
  collapse is GDiff. sparse-wiki is a separate tool (deterministic encoding of semantic
  messiness).

## Consequences

- Laws 1–8 (THEORY Part IV) are binding; Law 1 (no ML) and Law 4 (data layer narrows,
  never decides) are the load-bearing ones.
- The first thing to build/test is the make-or-break bet: does the entropy-weighted
  superposition reference absorb normal anatomical variation and leave only pathology
  in the residual?
- Still to read to fully close the data layer (founder-flagged): GenomeVault
  reconstruction / E2E comparison experiments, 3d-h5 metadata processing, dedicated
  oncogene predictor.
- No competition scaffold has been created and no data downloaded; `bootstrap_
  competition.sh` has not been run.
