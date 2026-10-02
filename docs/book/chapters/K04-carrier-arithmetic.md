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
- `CarrierSpec`: banks, rows per bank (512), the declared limits R, C, |a| and |b|.
- `row_sign(bank_row, j)`: the Sylvester–Hadamard entry `(-1)**popcount(i & j)` by index arithmetic. The matrix
  is never materialized.
- `bundle(rows)` → count table; `unbundle` by subtraction.
- `level(u_counts, v_counts, mask, a, b)` → `reaches | short | silent`.
- `decode_difference(u, v, layout)` → named rows with count deltas.
- `pack_signs(counts)` → two uint64 bit-planes per bank, plus `hamming_order(...)` (ordering only).

**Consumers:** K12, K25 and K26 (near misses' named differences).

## 3. Mechanism

- **Profiles are count tables**, int32, one row per coordinate. Because the rows are exactly orthogonal, the
  vector's cosine **equals** the count table's cosine. The vector is therefore never built: "For one comparison,
  then, the vector adds nothing a count table lacks" (THESIS §12.1).
- **The level test.** For a question's mask M (the coordinates of the banks both sides speak in; the same mask
  for the dot product and both norms):
  - dot = Σ_M u·v, computed in binary64. This is exact, because the limits are checked first:
    C ≤ 2^20 per coordinate and R ≤ 2^9 coordinates give dot ≤ 2^49 < 2^53.
  - Then `reaches ⟺ b²·dot² ≥ a²·‖u‖²_M·‖v‖²_M`, evaluated in i128 or Python int (≤ 2^118 for
    |a|, |b| ≤ 2^10).
  - `silent` means either side has no coordinate in M.
- **The decode** is `v − u` per coordinate. A difference is named as (bank, row, Δcount). THESIS §6.6: "this bank,
  this metric, so many more places below the middle".
- **Packed signs order a scan's candidates.** A case is dropped only on a proved bound: sign agreement bounds
  nothing about the count cosine (THESIS §12.1's counterexample).

## 4. Contracts

- Counts are non-negative int32.
- A limit violation refuses with `limit_exceeded:<which>` **before** any float conversion.
- Masks are boolean over coordinates; the same mask feeds the dot product and both norms.
- Levels are ratios of whole numbers written before the run.
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
  - over-limit inputs refuse;
  - packed-sign ordering never drops a case.
- **Detective:** `level` and the limit and mask decisions are converged (literal and bounded-array inputs).
- **SAME** for every Numba twin: equal counts, equal codes.

## 7. Integration

`knee.core.ledger` is imported by K12's layout writer and by K25. No `run` code materializes vectors.

## 8. Acceptance

- **Behavioural correctness:** the laws hold; the refusals are named; standing is pinned for the decisions.
- **Representation fidelity:** cosine(count tables) equals the materialized-vector cosine, exactly, on
  generated cases. A test-only materialization serves as the twin.
- **Domain validity:** not applicable.
- **Performance evidence:**
  - comparisons per second for one profile against 10^5 cases, in both the reference and the Numba backend;
  - bytes scanned per comparison;
  - scope: "M1 Max, float64 BLAS, R = 512".
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
