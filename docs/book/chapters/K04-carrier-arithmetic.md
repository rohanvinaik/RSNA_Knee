# K04 — Carrier arithmetic: the exact ledger's algebra

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K04'` |
| **Depends on** | K02 |
| **Consumed by** | K12 (layout), K25 (memory and recall), every profile comparison and named difference |
| **Commit label / tag** | `knee/K04` · `knee-K04` |

## 1. Purpose and authority

To build the one language's arithmetic: domain-independent, exact, and fast.
- **THESIS §6 and §12:** a profile is a whole-number count table; there is one cosine; the exact decode names a
  difference.
- **The founder:** "for hypervectors, cache/memory operations can really speed stuff up, and JIT is basically a
  requirment".
- **The accord:** exactness is proved from declared limits (THE_KNEE §3.4).
- **Non-goals:** the domain layout (which banks, which rows) is K12's.

## 2. Dependencies and consumers

**Produced (`knee.core.ledger`):**
- `CarrierSpec`: banks, rows per bank (512), and the declared limits: C (the largest count per coordinate), R
  (every allocated coordinate of every bank a question names), and |a|, |b|.
- `row_sign(bank_row, j)`: the Sylvester–Hadamard entry `(-1)**popcount(i & j)` by index arithmetic. The matrix
  is never materialized.
- `bundle(rows)` → count table; `unbundle` by subtraction.
- `level(u_counts, v_counts, read_banks_u, read_banks_v, question_banks, a, b)` → `reaches | short | silent`, or a
  refusal (`limit_exceeded:<which>`, `level_out_of_domain`).
- `decode_difference(u, v, layout)` → named rows with count deltas.
- `pack_signs(counts)` → two uint64 bit-planes per bank, plus `hamming_order(...)` (ordering only).

**Consumers:** K12, K25 and K26 (near misses' named differences).

## 3. Mechanism

- **Profiles are count tables**, int32, one row per coordinate.
  - The rows are exactly orthogonal (H Hᵀ = 512 I), so the materialized vectors' dot product and squared norms
    are exactly 512 times the tables' whole-number ones.
  - The cosines are therefore equal *algebraically*. A float cosine, through square roots, is never compared
    bitwise and never decides.
  - The vector is never built: "For one comparison, then, the vector adds nothing a count table lacks" (THESIS
    §12.1).
- **Silence is a bank, read off the coverage record** (THESIS §6.3: "The informational zero is a silent bank").
  The question's mask M is every coordinate of the banks the question names that *both* sides read (ARCH §3.5.2).
  It is never inferred from zero counts. The same M feeds the dot product and both norms.
- **The level test** (THESIS §12.2: "Counts are never negative, so a cosine reaches the level a/b exactly when
  b² · dot² ≥ a² · ‖u‖² · ‖v‖²"):
  - **The level's domain:** integers 0 ≤ a ≤ b, b ≥ 1, written before the run. Anything else refuses
    (`level_out_of_domain`). Counts are non-negative, so dot ≥ 0 and squaring loses no sign.
  - **dot = Σ_M u·v** is computed in whole numbers. The limits are checked on the integer inputs first.
    Binary64 BLAS is admitted for a batch only when R·C² < 2^53, where R counts every allocated coordinate of
    every named bank; with C ≤ 2^20, that allows R ≤ 2^12, eight banks. Beyond that, int64 carries the dot (exact
    while R·C² < 2^63), and Python int beyond that.
  - **The decision:** `reaches ⟺ b²·dot² ≥ a²·‖u‖²_M·‖v‖²_M`, in i128 or Python int.
  - **`silent`** when M is empty, *or* when either side's norm over M is zero (every read row unlit: ARCH
    §3.5.3's *orthogonal*). "A pair with nothing to compare abstains" (THESIS §12.2). It never reaches, which
    the squared test would otherwise give at 0 ≥ 0.
- **The decode** is `v − u` per coordinate. A difference is named as (bank, row, Δcount). THESIS §6.6: "this bank,
  this metric, so many more places below the middle".
- **Packed signs order a scan's candidates.** A case is dropped only on a proved bound: sign agreement bounds
  nothing about the count cosine (THESIS §12.1's counterexample).

## 4. Contracts

- Counts are non-negative int32.
- A limit violation refuses with `limit_exceeded:<which>` **before** any float conversion.
- A side's read banks come from its coverage record. The mask is their intersection over the question's banks,
  and the same mask feeds the dot product and both norms.
- Levels are ratios of whole numbers in [0, 1], written before the run.
- The layout version travels with every table. Comparing tables of different layouts refuses with
  `layout_mismatch`.

## 5. Implementation choice

- **Python references with an explicit operation order,** then **Numba twins** for scatter-add (row indices →
  counts), sign packing and popcount. The founder's "JIT is basically a requirment".
- **The dot product** through BLAS (NumPy float64 matmul) for batched comparisons, after the limit check. The
  borderline level test runs in exact integers.
- **Memory:**
  - tables are contiguous, row-major, int32;
  - norms are cached as int64 per table;
  - sign planes are uint64 arrays;
  - the bytes scanned per comparison are recorded.
- **Prior art.** Cell-tracking's `hdc/banks.py` (16 banks × 512 rows, per-bank seeded permutations, an exact
  decode by matrix product). Q16 asks whether to share it. **Decision: fresh.**
  - The knee needs a count-table-first API, with no vector materialization, plus declared limits and an exact
    level test. `banks.py` materializes rows and decodes by float matmul.
  - The arithmetic laws it embodies are reused as acceptance properties.
  - The decision is recorded in `MIGRATION.md`, under "external prior art".

## 6. Verification

- **Hypothesis laws:**
  - unbundle(bundle(x) + y) = x;
  - the decode is exact;
  - re-seeding the row order changes no count and no cosine (QZ4: a seed change that moves anything is a fault);
  - rows are orthogonal, checked by index arithmetic on sampled pairs;
  - the level test agrees with exact rational arithmetic on every generated case, boundary cases included;
  - a zero norm over M answers `silent`, never `reaches`;
  - a bank read on one side only is out of M on both;
  - a level outside its domain refuses;
  - over-limit inputs refuse, and the backend choice (BLAS, int64, Python int) follows R·C²;
  - packed-sign ordering never drops a case.
- **Detective:** `level` and the limit and mask decisions are converged (literal and bounded-array inputs).
- **SAME** for every Numba twin: equal counts, equal codes.

## 7. Integration

`knee.core.ledger` is imported by K12's layout writer and by K25. No `run` code materializes vectors.

## 8. Acceptance

Written first: `acceptance/K04.toml`.
- **Behavioural correctness:** the laws hold; the refusals are named; standing is pinned for the decisions.
- **Representation fidelity:** on generated cases, the tables' whole-number dot and norms equal 1/512 of the
  materialized vectors', exactly, and the level decision agrees. A test-only materialization serves as the twin.
  The float cosines are reported within a stated tolerance, and they decide nothing.
- **Domain validity:** not applicable.
- **Performance evidence** (work counted; ARCH §3.2.6):
  - comparisons, coordinates and bytes scanned per comparison, for one profile against 10^5 cases, in each
    backend;
  - seconds as information;
  - scope: "M1 Max, the backend the R·C² rule chose".
- **Evidence scope:** the generated inputs within the declared limits.
- **Invalidation:** a change to the limits, the mask semantics, the level arithmetic, or the BLAS or backend
  semantics.

## 9. Open matters

- **Facts:**
  - whether batched recall at the memory's real size needs a native scan (K25 measures);
  - Q16 is settled here as "fresh", by argument.

## 10. Provenance and status log

- **Sources:**
  - THESIS §6.1, §6.6, §12.1–§12.2;
  - THE_KNEE §3.4;
  - Codex design round 2 (A5);
  - cell-tracking `hdc/banks.py` (prior art).
- **2026-10-02:** specified in K00.
- **2026-10-02, revision 1** (F16): silence read from coverage; the level's domain; a zero norm is silent; R over
  every named bank, with the backend chosen from R·C²; algebraic, not bitwise, equality of cosines (THESIS §6.3,
  §12.2; ARCH §3.5.2–§3.5.3).
