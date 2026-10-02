# Decision: The make-or-break verdict keys on rank AUC of local survivor density

**Date:** 2026-08-28
**Status:** accepted
**Context:** First build session. The make-or-break test (THEORY Part III closing
note) needed a concrete statistic and decision rule. Two earlier candidates failed
on the synthetic machinery smoke for principled reasons, recorded here so they are
not re-tried.

## Decision

1. **Statistic:** peak local survivor density — the max fraction of cells whose
   KneeDiff residual exceeds threshold within any 9×9 window (integral-image
   sliding window; `platonic_reference.max_window_density`). The theory's claim is
   that pathology is a LOCALIZED cluster of unlicensed deviation; a global survival
   fraction dilutes a lesion over the study by construction. The local statistic is
   also what the per-finding lens (II.5) will consume.
2. **Decision rule:** the ROC-AUC of that statistic ranking abnormal studies above
   held-out normals (`kneediff.make_or_break_verdict`), with named codes:
   insufficient_data / reference_absorbs (AUC ≥ 0.90) / partial_signal (≥ 0.65) /
   no_separation. Bars are provisional until calibrated (Pattern 19).
3. **Machinery validation is an amplitude response curve**, not one number: the
   synthetic smoke sweeps lesion amplitude and requires AUC to rise with amplitude,
   the decisive lesion to yield reference_absorbs, and the no-lesion control to sit
   at chance. Validated 2026-08-28: AUC [0.34, 0.65, 0.66, 0.91, 0.97], control 0.36.

## Rationale

- Rank-based AUC is the competition's own metric, threshold-free at decision level.
- Absolute-level rules (survival fraction + margin — the first attempt) are
  calibration-fragile: per-cell sigma estimated from N references has t-tails
  (n=20 inflates P(|z|>3) ~2.8×) and smooth anatomical fields cluster the
  estimation error, shifting absolute levels while barely moving ranks.
- The synthetic world cannot answer the anatomical question (its "normal
  variation" and "lesion" are the same object at different amplitudes, so
  separation there is amplitude-driven by construction). It validates WIRING and
  response only; the real verdict comes from `--data-dir` on registered studies.

## Alternatives Considered

- **Global survival fraction + margin** — rejected: dilutes localized lesions;
  margin knob has no principled setting.
- **Local density + absolute margin** — rejected: same fragility via sigma
  estimation noise; normals' max-window statistic is heavy-tailed over smooth
  fields (extremes of Gaussian fields).

## Consequences

- `tools/make_or_break.py --data-dir data/registered` is the REAL test; it needs
  registered .npy studies in reference/ normal/ abnormal/ — the registration
  front-end (II.1) is the prerequisite build.
- Design lesson for the real reference: per-cell sigma from few references is
  noisy; use enough reference studies, and expect sigma SHRINKAGE (the pixel
  analogue of ConsensusBase.confidence) if N stays small.
- The genomics consecutive-disagreement decay and IUPAC ambiguity machinery are
  explicitly NOT ported (wrong physics for pixels) — recorded in
  `platonic_reference.py` docstring.
