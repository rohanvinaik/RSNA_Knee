# K09 — Population references

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K09'` |
| **Depends on** | K08 (refined registration, places), K06 (report-negative candidates) |
| **Consumed by** | K10 (z), K11 (hosts), K21 (p̂_S and nulls), K23 (normals for the hardness map), K18 (kernel artifacts) |
| **Commit label / tag** | `knee/K09` · `knee-K09` |

## 1. Purpose and authority

To build the platonic knee as a distribution: for every series class × regime × place, a robust centre, a spread
and a count. The pool is report-negative candidates, split by role.
- **THEORY II.2:** "The cell's entropy IS its per-cell tolerance."
- **The accord:** per-series-class references carry the substrate (THE_KNEE §2, change 1); "true normals" are
  report-negative candidates; the variance decomposition is coherent and includes the centre's uncertainty
  (change 10).
- **The founder's sample check (Q12):** "Should the founder's eye confirm a sample before they set the hardness
  map?" Yes; this chapter makes that sheet.

## 2. Dependencies and consumers

**Produced** (`knee.build.reference`; `knee.core.reference` for the loader):
- **`gain(series, reference_tissue_zones, regime_value) -> γ_s | gain_unpinned | gain_disagree`.** This is ARCH
  §3.3.3's gain specialist, lifted out of the law and run on every series: "a reference tissue read in the
  series, against its recalled regime value: muscle everywhere, marrow fat where unsuppressed". The two tissues
  are compared. A series with no normal reference tissue in the field is silent on the population axis (ARCH
  l.1853: "no normal reference tissue in the field").
- **The comparison representation:** x̃ = stored ÷ (N4 field × γ_s), which is invariant to a global gain and to a
  smooth multiplicative field (THEORY II.1; ARCH §3.3.9 Table 3.5, row 1). There is no p2–p98 scaling and no
  histogram matching (ARCH §3.4.1). The stored values stay untouched for K24.
- **References** per (series class, regime key, place), in that representation: `centre` (median), `spread`
  (1.4826·MAD), `n`, and `centre_var` (the centre's variance).
- **The regime fallback map:** which cells fell back to which parent key.
- **The pool's role assignment**, applied from K03.
- **The founder's sample sheet** and his recorded calls.
- **The historical make-or-break reading** per series class.

**Consumers:** K10, K11, K21, K23, K18.

## 3. Mechanism

1. **Pool.** K06's `negative` studies are registered (K08) and assigned roles (K03): `reference` builds the
   references; `null`, `chance`, `host` and `checking` are held out of them.
2. **The founder's sample.** A stratified sample of reference candidates, by regime and vendor, rendered as sheets:
   the zones in every series, the report sentence, the residual against a leave-one-out reference. The founder
   calls each normal, not normal, or abstain. His calls are recorded and never overwritten. A "not normal" leaves
   the reference roles, and the rate is reported as the pool's measured impurity.
3. **Per cell:**
   - centre = the median over reference members;
   - spread = 1.4826·MAD;
   - n = the members that cover the place, in field and not out of field.
4. **Fallback.** A cell with n below the declared minimum (n_min, written before the run) falls back along
   field → vendor → sequence family. Cells whose per-place distributions are measured indistinguishable are merged.
5. **Variance decomposition**, stated exactly. This is ARCH §3.4.2's estimator, with THE_KNEE §2 change 10's
   centre uncertainty added:
   - **σ²_meas** is estimated per study and series from homogeneous reference tissue (muscle) and background,
     under a stated noise model, in the same units as x̃. Magnitude images are Rician, and below the noise floor
     a place is silent with `below_noise_floor` (ARCH §3.3.7).
   - **σ²_bio(v) = max((1.4826·MAD(v))² − median over members of σ²_meas, 0).** This is ARCH's "max(s_p² − mean
     σ²_meas, floor²)" with the floor at zero: a negative estimate means measurement noise explains the
     spread.
   - **var(μ̂)(v) = (π/2)·(σ²_bio(v) + mean σ²_meas)/n**, the median's variance under the Gaussian
     decomposition. It is bootstrapped where the model is doubted.
   - All three enter K10's denominator. A cell with n < n_min is silent, or falls back to its parent key.
6. **The historical make-or-break.** The fixed instrument (`tools/make_or_break.py`, unchanged) is run per series
   class on the v-current layout for comparison with LADDER's v5 readings. It is a historical diagnostic, not the
   authority.

## 4. Contracts

- **Reference arrays:** float32 `centre`, `spread`, `centre_var`, and int16 `n`, per plane grid, per cell. Missing
  cells read `status=fallback:<key>` or `status=silent:<cause>`. Never NaN.
- **All artifacts are competition-derived:** `data/reference/v<k>/` and a private Kaggle dataset.

## 5. Implementation choice

- **The per-voxel median and MAD over N members** are memory-bound selection.
  - The reference is NumPy's `median` along the member axis, in slabs. "A plain Python or NumPy function behind
    the same contract" (THESIS §12.5).
  - The twin is a **Numba** kernel doing selection over voxel-major blocks. It is exact (order statistics), so
    SAME requires bitwise equality.
  - Block size is recorded with its rationale (bytes per block against cache), and so are the bytes scanned.
- **Runs on the Mac Pro** by slab shards, with merging governed by a cross-node SAME on sample slabs. The results
  are order statistics of the same inputs, so exact equality is expected.
- **Prior art:** legacy `RSNA_Knee/platonic_reference.py` (`build_reference` mean and std, detrend, window
  densities). **Decision:** rewritten. The statistic changes (median and MAD, the decomposition, fallback), and the
  window densities move to K10. Each unit gets a `MIGRATION.md` row.

## 6. Verification

- **Detective:** the fallback decision, the cell-status codes and n_min handling are converged.
- **Hypothesis:**
  - the median and MAD are invariant under member permutation;
  - z is invariant, within its stated tolerance, under a synthetic global gain and a smooth multiplicative field
    applied to a series and to its reference tissue together;
  - `gain` reads `gain_unpinned` when the reference tissue is absent, and `gain_disagree` when the two tissues
    disagree beyond the stated tolerance;
  - the spread is non-negative;
  - a fallback is never chosen while n ≥ n_min.
- **SAME:** the Numba median and MAD equal the NumPy reference bit for bit.
- **Leave-one-normal-out:** survival on `checking` members at the declared threshold.

## 7. Integration

- `just reference` builds the references.
- The kernel loads them per study regime and class (K18).

## 8. Acceptance

Written first: `acceptance/K09.toml`.
- **Behavioural correctness:** SAME is exact; the decisions are pinned; the fallback map is complete.
- **Representation fidelity:**
  - no NaN, and every cell has a status;
  - gain and bias invariance holds on synthetic inputs and on P.
- **Domain validity (discovery):**
  - γ_s's distribution per regime, and the two tissues' agreement, by regime and age band where known (muscle
    can carry fat in older knees);
  - the false-survival rate on `checking` members at the declared z threshold is within its stated bound, per
    class and regime;
  - the founder's sample is called, and the impurity is reported;
  - the historical make-or-break readings are recorded beside LADDER's.
- **Performance evidence:** slabs, members and bytes scanned, counted per node; seconds as information. Scope:
  "Numba median over N members".
- **Evidence scope:** the pool at its version, by regime.
- **Invalidation:** a change to the pool (K06), the roles (K03), registration or the atlas (K07, K08), n_min, or
  the noise model.

## 9. Open matters

- **Facts:**
  - the impurity of the report-negative pool (the founder's sample);
  - which regimes are thin;
  - whether the detrend survives (it was needed on v5, LADDER). Re-measured in K10.
- **Policy:** n_min and the false-survival bar, written before the run. Proposed: n_min = 30, with the bar stated
  per class.

## 10. Provenance and status log

- **Sources:**
  - THEORY II.2–II.3;
  - KNEE_ARCHITECTURE §3.4;
  - VERDICT;
  - LADDER;
  - THE_KNEE §2 (changes 1, 8, 10).
- **2026-10-02:** specified in K00.
- **2026-10-02, revision 1:**
  - γ_s on reference tissue for every series, references in x̃, and invariance as a fidelity check (F01; ARCH
    §3.3.3, §3.3.9; THEORY II.1);
  - the variance estimator stated (F43; ARCH §3.4.2);
  - NumPy accepted as the reference (F31; THESIS §12.5);
  - work counted (F39).
