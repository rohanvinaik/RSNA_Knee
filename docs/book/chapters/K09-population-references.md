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
- **References** per (series class, regime key, place): `centre` (median), `spread` (1.4826·MAD), `n`, and
  `centre_var` (the centre's variance).
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
5. **Variance decomposition** (coherent, replacing KNEE_ARCHITECTURE §3.4.2's MAD² subtraction).
   - Measurement noise is estimated per study and series from homogeneous reference tissue (muscle) and
     background, under a stated noise model. Magnitude images are Rician, and below the noise floor a place is
     silent.
   - σ²_bio is estimated from the reference members' residuals under the stated model (Gaussian for the
     decomposition).
   - var(μ̂) for the median is (π/2)·σ²/n, or bootstrapped where the model is doubted.
   - All three enter K10's denominator.
6. **The historical make-or-break.** The fixed instrument (`tools/make_or_break.py`, unchanged) is run per series
   class on the v-current layout for comparison with LADDER's v5 readings. It is a historical diagnostic, not the
   authority.

## 4. Contracts

- **Reference arrays:** float32 `centre`, `spread`, `centre_var`, and int16 `n`, per plane grid, per cell. Missing
  cells read `status=fallback:<key>` or `status=silent:<cause>`. Never NaN.
- **All artifacts are competition-derived:** `data/reference/v<k>/` and a private Kaggle dataset.

## 5. Implementation choice

- **The per-voxel median and MAD over N members** are memory-bound selection.
  - The reference is NumPy's `median` along the member axis, in slabs.
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
  - the spread is non-negative;
  - a fallback is never chosen while n ≥ n_min.
- **SAME:** the Numba median and MAD equal the NumPy reference bit for bit.
- **Leave-one-normal-out:** survival on `checking` members at the declared threshold.

## 7. Integration

- `just reference` builds the references.
- The kernel loads them per study regime and class (K18).

## 8. Acceptance

- **Behavioural correctness:** SAME is exact; the decisions are pinned; the fallback map is complete.
- **Representation fidelity:** no NaN; every cell has a status.
- **Domain validity:**
  - the false-survival rate on `checking` members at the declared z threshold is within its stated bound, per
    class and regime;
  - the founder's sample is called, and the impurity is reported;
  - the historical make-or-break readings are recorded beside LADDER's.
- **Performance evidence:** seconds per slab per node; bytes scanned. Scope: "Numba median over N members".
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
