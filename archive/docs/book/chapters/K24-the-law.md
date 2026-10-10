# K24 — The quantitative law (optional, by identifiability)

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K24'`. **Optional:** skipped by the next-chapter rule unless selected in `docs/book/SELECTION.toml` |
| **Depends on** | K18 (first light, which its acceptance re-runs), K10 (deviation and identity), K05 (timings, identifiable sets), K11 (phantoms), K09 (γ_s and the N roles) |
| **Consumed by** | K10 (physics-space z where identified), K11 (law-forward phantoms), K14 (typed misfit enters the constraint axis) |
| **Commit label / tag** | `knee/K24` · `knee-K24` |

## 1. Purpose and authority

To invert the MR signal equation where, and only where, a study's acquisitions identify the quantity. The law's
misfit is typed as instrument or input-error information.
- **The founder** (SESSION_BRIEF §5, layer 1): "the MR signal equation as the network".
- **The accord** (change 1): "Make acquisition-qualified measurements the general substrate. Permit parameter
  inversion only where a declared forward operator has sufficient rank and conditioning"; "Name empirical offsets
  as offsets, not recovered physical coefficients."
- **Selection.** Include this chapter if K05's identifiable sets show a useful share of studies with a same-fat-state
  TE contrast (within a plane or at region scale across planes) or a fat pair. Record the selection with that
  measurement.

## 2. Dependencies and consumers

**Produced** (`knee.run.law`):
- **`identifiability(series_timings, gains, filters, places) -> rank, condition, code`:** per study and place, at
  the plane-group and region scales. The unknowns include each series' gain γ_s and any per-series intensity
  filter c, as nuisances (ARCH §3.3.9 Table 3.5, rows 1–2: "one γ per series, pinned on reference tissue"; "a
  vendor's normalization filter makes c differ between series"). A quantity is `identified` only if it stays
  identified with those nuisances free, or pinned by K09's γ_s with its σ carried.
- **Where identified,** a quantity with its delta-method σ: T2-ish from a TE contrast at the same fat state;
  f(1−ε)-type combinations from fat pairs, never f and ε separately without a stated model for ε; T1-ish only
  where a TR contrast exists.
- **Empirical offsets** per regime and tissue class: medians of the residual on normals, **named as offsets**.
- **The typed misfit:** a motion dipole, ghosting, a magic-angle signature, suppression failure, partial volume,
  the noise floor, susceptibility, `unexplained`. Each goes to the constraint axis or the hardness map, never to a
  finding.
- **The physics-space references:** K24 builds its own, per identified quantity, from N roles allocated to it in K03,
  never the raw path's members re-used silently (ARCH §3.4.2). With K24 unselected, K09's raw path (x̃) stands.
- **K11's forward-law phantoms** need no inversion and do not wait on this chapter.

**Consumers:** K10, K14.

## 3. Mechanism

- **The composed spin-echo law,** in logs, per series s at place v: gain, plus density, plus recovery (TR, TI),
  minus TE·R2, plus the fat term, plus the offset. Gradient-echo and DESS series need their own law, or stay on
  measured signatures. A single spin-echo law is never forced on them.
- **The rank and conditioning** of the Jacobian over the identified unknowns decide `identified`,
  `partially_identified:<combination>` or `not_identified`. Only identified quantities, or named combinations, are
  emitted.
- **Leave-one-series-out** runs only on withheld contrasts that **add** information. Withholding a near-repeat
  tests repeatability, and is reported as such.

## 4. Contracts

- Quantities are float32 with σ, per place and scale, plus their identifiability code. Offsets are per regime and
  tissue class, with their n.

## 5. Implementation choice

- **NumPy closed forms** where they exist. **Numba** for per-place iterative solves. Each has a reference and a
  SAME twin.
- **Prior art:** KNEE_ARCHITECTURE §3.3 and LAA §4–§10. **Decision:** adopted under change 1's restrictions;
  fresh code.

## 6. Verification

- **Detective:** the identifiability decision and the misfit-type decision are converged.
- **Hypothesis:** forward then inverse returns the identified quantities within their σ, on generated tissue
  values.
- **Calibration:** the normalized LOSO error is standard normal where the law holds; the error rises with σ̂.

## 7. Integration

Where selected: K10's z gains a physics-space variant per identified quantity, as its own versioned stage. Re-run
`just firstlight`. K27 validates the selection.

## 8. Acceptance (if selected)

Written first: `acceptance/K24.toml`.
- **Behavioural correctness:** the decisions are pinned; SAME holds; first light is re-run, and its diff is read
  against this chapter's behaviour-change record.
- **Representation fidelity:** the identified share per regime is reported. Nothing is emitted where not
  identified.
- **Domain validity:**
  - LOSO calibration;
  - the offsets are stable across disjoint halves of normals within a regime (falsifier 7, reworded);
  - σ is calibrated (falsifier 9).
- **Performance evidence:** places and solve iterations counted; seconds as information.
- **Evidence scope:** the identified studies only.
- **Invalidation:** a change to the timing classes, the forward law, or the regimes.

**If not selected:** K27 records its absence explicitly.

## 9. Open matters

- **Facts:** the identifiable share (K05), which decides the selection.

## 10. Provenance and status log

- **Sources:**
  - LAA;
  - KNEE_ARCHITECTURE §3.3;
  - the Codex review rounds (C1–C2) and design round 1;
  - THE_KNEE §2 (change 1).
- **2026-10-02:** specified in K00.
- **2026-10-02, revision 1:**
  - depends on K18 (F09);
  - gains and filters as nuisances in identifiability (F52; ARCH §3.3.9);
  - its own physics-space references and N roles (F22, F52);
  - forward-law phantoms moved to K11 (F44).
