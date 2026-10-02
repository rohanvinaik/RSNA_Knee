# K10 — Deviation and signatures

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K10'` |
| **Depends on** | K09 (references), K07/K08 (plane volumes, status), K05 (series timings) |
| **Consumed by** | K11 (response measurement), K12 (quantizer data), K13/K20 (lens inputs), K15 (bodies), K19 (signal evidence), K21 (D), K18 (kernel) |
| **Commit label / tag** | `knee/K10` · `knee-K10` |

## 1. Purpose and authority

KneeDiff. Each place gets its deviation from the population, its licensed record, its residual and its windowed
densities, plus the cross-series sign pattern each tissue change writes.
- **The founder** (2026-08-18): "line it up … then literally subtract!"
- **THEORY II.3**, and THESIS §4.2 ("a removal is a decision … kept as a record, never a discard").
- **The accord:** "licensed" never means "excluded" (THE_KNEE §2, change 3); signatures carry the substrate where
  the law cannot (change 1).

## 2. Dependencies and consumers

**Produced** (`knee.core.deviation`, `knee.run.deviation`, `knee.core.signature`):
- **z per place,** per series: `z = (x − centre) / sqrt(σ²_bio + σ²_meas + centre_var)`.
- **The licensed record,** uint8 per place:
  - `licensed` (|z| < t, compatible with the reference);
  - `deviant_bright` and `deviant_dark`;
  - `silent:<cause>` for out of field, a reference cell that is silent, below the noise floor, or an absent
    series.
- **The residual:** the deviant places, with their z.
- **Windowed densities:** the share of deviant places in every window of declared size, per zone, by running sums.
- **`signature(place) -> code`**, from the deviation signs across the co-registered series (region scale) read
  against the signs each series' timing predicts per tissue. The codes: `fluid`, `fat`, `fibrous`, `edema_like`,
  `intermediate`, `unsuppressed_fat`, `unnamed`, `void`, `insufficient_contrasts`.

**Consumers:** K11–K13, K15, K19–K21, K18.

## 3. Mechanism

1. **z.** The threshold t is written before the run. The proposal is t = 3, with t ∈ {2.5, 3, 3.5} measured for
   false survival on `checking` normals. The **SAME routing rule:** a place within the twin's stated float error of
   ±t is decided by the reference.
2. **Licensed is not excluded.** The record states compatibility with the reference only. A small lesion inside a
   wide spread is licensed and not ruled out. Nothing downstream may read `licensed` as a negative (K14's
   contracts enforce this).
3. **Detrend.** Whether a low-frequency detrend is still needed is **measured**, not assumed. It was needed on v5
   raw intensities (LADDER: σ ∈ [16, 32]). It is re-swept here per series class on the fixed instrument. If needed,
   it is a declared, versioned stage with its own SAME.
4. **Signatures.**
   - Each series is classed by its timing (K05): short or long TR, short or long TE, fat state.
   - A pure table `expected_sign(tissue, tr_class, te_class, fat_state) -> {+, 0, −}` is derived from the
     spin-echo law's partial derivatives (KNEE_ARCHITECTURE §2.3.2: "the ternary shadow of the equation").
   - Where at least two contrasts cover a place, the observed sign vector is matched against the table. A tie
     reads `unnamed`.
   - Gradient-echo series have their own table, with a stated law and no spin-echo assumption.
5. **Windows** are computed with running sums over each zone mask: exact integer counts, never a float density
   until reported.

## 4. Contracts

- `z`: float32, per plane grid, beside the uint8 licensed record and the status.
- Densities: int32 counts plus the window sizes.
- Signature codes: uint8, with a vocabulary owned by `knee.core.vocab`.
- The reference arithmetic is float64. The twin's float error bound for z is stated before the run.

## 5. Implementation choice

- **A fused Numba pass**: reading x, centre, the variances and the status, and writing z, the record and the
  window running sums, in one traversal with a declared scratch size. Its twin is a plain Python reference with an
  explicit order.
- **The signature match** is a Numba pass over places with a pure Python decision table, the table pinned by
  Detective.
- **Prior art:** legacy `kneediff.residual_z`, `classify_cell` and `survival_fraction`, and
  `platonic_reference.detrended_residual_map` and `max_masked_window_density`. **Decision:** rewritten. The
  denominator and the record's semantics change. The make-or-break verdict stays with the historical instrument.
  Each unit gets a `MIGRATION.md` row.

## 6. Verification

- **Detective:** `expected_sign`, the record codes and the window-bound decisions are converged. The kernel cores
  are reached through captured arguments where rank 3 makes synthesis inapplicable.
- **Hypothesis:**
  - z is antisymmetric in x about the centre;
  - the windowed counts equal brute-force counts;
  - silent places never become deviant.
- **SAME:** the Numba z and record against the reference, with exact record codes and threshold-boundary routing
  exercised by generated cases.
- **Authored signature cases:** synthetic sign vectors for each tissue and contrast set.

## 7. Integration

`knee.run.deviation.read(study, references) -> DeviationReading` is the kernel's step after registration.

## 8. Acceptance

- **Behavioural correctness:** SAME, including boundary routing; pinned decisions; licensed is never consumed as
  excluded (a K14 contract test, added when K14 lands).
- **Representation fidelity:** every place has a record code; no NaN.
- **Domain validity:**
  - false-deviant rates on `checking` normals, per class and zone, with bounds;
  - the detrend measurement, stated as needed or not needed per class;
  - the signature distribution on normals.
- **Performance evidence:** places per second, reference against Numba, with bytes scanned. Scope: "one study, all
  series, the named node".
- **Evidence scope:** the reference version, the threshold, the classes.
- **Invalidation:** a change to the references (K09), the threshold, the detrend, or the expected-sign table.

## 9. Open matters

- **Facts:**
  - the detrend;
  - t (from false survival);
  - the signature ties per class.

## 10. Provenance and status log

- **Sources:**
  - THEORY II.2–II.3;
  - KNEE_ARCHITECTURE §2.3, §3.4.3–§3.4.4;
  - VERDICT;
  - LADDER;
  - THE_KNEE §2 (changes 1, 3).
- **2026-10-02:** specified in K00.
