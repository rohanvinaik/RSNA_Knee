# K10 — Deviation and signatures

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K10'` |
| **Depends on** | K09 (references), K07/K08 (plane volumes, status), K05 (series timings) |
| **Consumed by** | K11 (response measurement), K12 (quantizer data), K13/K20 (lens inputs), K15 (bodies), K19 (signal evidence), K21 (D), K18 (kernel) |
| **Commit label / tag** | `knee/K10` · `knee-K10` |

## 1. Purpose and authority

KneeDiff. Each place gets three readings, never merged:
- its deviation from the population, with its licensed record, residual and windowed densities;
- its tissue identity, read within the study;
- its change of tissue word against its zone's normal word.
- **The founder** (2026-08-18): "line it up … then literally subtract!"
- **THEORY II.3**, and THESIS §4.2 ("a removal is a decision … kept as a record, never a discard").
- **The accord:** "licensed" never means "excluded" (THE_KNEE §2, change 3); signatures carry the substrate where
  the law cannot (change 1).

## 2. Dependencies and consumers

**Produced** (`knee.core.deviation`, `knee.run.deviation`, `knee.core.signature`):
- **z per place,** per series, on the comparison representation x̃ (K09): `z = (x̃ − centre) / sqrt(σ²_bio +
  σ²_meas + centre_var)`. A series K09 marks `gain_unpinned` is silent here.
- **The licensed record,** uint8 per place:
  - `licensed` (|z| < t, compatible with the reference);
  - `deviant_bright` and `deviant_dark`;
  - `silent:<cause>` for out of field, a reference cell that is silent, below the noise floor, or an absent
    series.
- **The residual:** the deviant places, with their z.
- **Windowed densities:** the share of deviant places in every window of declared size, per zone, by running sums.
- **`tissue_level(place, series) -> + | 0 | − | silent:<cause>`**, per acquisition. It is the place's signal in
  that series against the series' *own* reference tissue (muscle): "T1 brighter than muscle (the T1 tissue
  level; lens 3's signature)" (ARCH l.3866). It needs no gain, as ARCH §2.3.2 says of the Signature lens ("does
  not need g"). Its middle is set once (THESIS §6.2).
- **`tissue_word(place) -> code`**, the *identity* reading. The per-series tissue levels are matched against
  Table 2.3a's expected signs for each series' timing class. The codes: `fluid`, `fat`, `fibrous`, `edema_like`,
  `intermediate`, `unsuppressed_fat`, `unnamed`, `void`, `insufficient_contrasts`. It is one joint reading,
  whose sources are all the series it used. It is a law check, "Cross-contrast consistency is a check" (ARCH
  §2.3 consequence 3). It supports and never votes.
- **`change(place) -> word_normal | word_changed:<from>→<to> | silent`**, the tissue word against the zone's
  normal word, which is measured on N's `reference` role. ARCH §3.4.3: "A place is black when every identified
  parameter lies within the licence … and its signature word is its zone's normal one." §2.3 consequence 1: "A
  meniscus turning + on FS holds fluid."
- **`suppression_map(series, fat_zone)`** (lens 5): the share of fat places left FS-bright and T1-bright (ARCH
  Table 2.8a row 5). It feeds the failed-suppression censor (Table 5.10) and K14's split.
- **Every reading carries its source set** (series ids). A joint reading is one dependent reading of all its
  sources (§F03).

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
4. **Identity, then change.** The book once merged these, and a healthy ligament never read `fibrous`
   (`provenance/build/revision_1.md`, §F02).
   - Each series is classed by its timing (K05): short or long TR, short or long TE, fat state.
   - A pure table `expected_sign(tissue, tr_class, te_class, fat_state) -> {+, 0, −}` gives each tissue's *level*
     against muscle, derived from the spin-echo law (KNEE_ARCHITECTURE §2.3, Table 2.3a; §2.3.2: "the ternary
     shadow of the equation").
   - Where at least two contrasts cover a place, the observed vector of per-series tissue levels is matched
     against the table, and the match is the tissue word. A tie reads `unnamed`.
   - Gradient-echo series have their own table, with a stated law and no spin-echo assumption.
   - The change reading compares the word with its zone's normal word. The deviation z stays a separate,
     per-series reading.
5. **Windows** are computed with running sums over each zone mask: exact integer counts, never a float density
   until reported.

## 4. Contracts

- `z`: float32, per plane grid, beside the uint8 licensed record and the status.
- Densities: int32 counts plus the window sizes.
- Tissue levels: uint8 per series. Tissue words and change codes: uint8, each with a uint32 source bitmask over
  the study's series. The vocabulary is owned by `knee.core.vocab`.
- The suppression map: float32 shares with int32 counts, per series and fat zone.
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
- **Authored identity and change cases:**
  - a healthy ligament (every series darker than muscle) reads `fibrous`, with its change `word_normal`;
  - a meniscus that turns FS-bright reads `word_changed:fibrous→fluid`;
  - fat on T1 with failed suppression reads `unsuppressed_fat`, and the suppression map rises.
- **A joint reading is never paired with its own sources** (a property test).

## 7. Integration

`knee.run.deviation.read(study, references) -> DeviationReading` is the kernel's step after registration.

## 8. Acceptance

Written first: `acceptance/K10.toml`.
- **Behavioural correctness:** SAME, including boundary routing; pinned decisions; licensed is never consumed as
  excluded (a K14 contract test, added when K14 lands).
- **Representation fidelity:** every place has a record code; no NaN.
- **Domain validity:**
  - false-deviant rates on `checking` normals, per class and zone, with bounds;
  - the detrend measurement, stated as needed or not needed per class;
  - each zone's normal tissue word, measured on N's `reference` role, and its change rates on `checking` normals;
  - the suppression map's distribution on normals, by regime.
- **Performance evidence:** places and bytes scanned, counted for the reference and for Numba; seconds as
  information. Scope: "one study, all series, the named node".
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
- **2026-10-02, revision 1:**
  - identity read within the series against muscle, and change kept apart from deviation (F02; ARCH Table 2.3a,
    §2.3.2, §3.4.3, l.3866);
  - source sets on every reading (F03);
  - the suppression map, lens 5 (F21);
  - z in x̃ (F01).
