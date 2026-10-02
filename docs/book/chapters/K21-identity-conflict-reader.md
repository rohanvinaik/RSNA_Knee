# K21 — The identity–conflict reader (the λ words, re-founded)

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K21'` |
| **Depends on** | K19 (identity evidence I), K10 (z), K11 (phantoms), K09 (normals for nulls) |
| **Consumed by** | K16 (structure words in agency rules), K22 (perturbed words), K23 (word rates in health), K12 (a context bank row for the word) |
| **Commit label / tag** | `knee/K21` · `knee-K21` |

## 1. Purpose and authority

To give each always-present structure the reading its λ-trajectory was meant to give: "structurally S, but
abnormal". The two observables are measured separately and honestly.
- **The founder:** "KneeDiff […] and the λ-trajectory are just the first and most elegant of them".
- **The accord** (change 5, with Codex review rounds 1–3): the closed form measures only reference conflict. A
  structural reading needs study-dependent identity, read on patient evidence only. The four words are legacy
  routing codes for cells of (I, D), and are named so.

## 2. Dependencies and consumers

**Produced** (`knee.run.reader`):
- **D, per structure window:** `Q = ‖z‖² / p̂_S` over the structure's most deviant window. p̂_S is the mean of ‖z‖²
  over `null`-role normals, and the null distribution of the window maximum is measured on the same normals.
- **The \|z\| survival profile:** `N(λ) = #{|z_v| > t/(1−λ)}` over the structure's places, for the declared λ
  grid. It is a monotone distributional reading in its own right: a few large deviations against many moderate
  ones. It contains no anatomical identity and no spatial arrangement.
- **Words,** as cells of (I, D):
  - `MONO_UP`: I = identified, D within its null;
  - `PEAK_DROP`: I = identified, D beyond its null. Read it as "identified S with population conflict", not as
    "pathology": variants and acquisition effects remain possible;
  - `MONO_DOWN`: I = not_found_adequate_visibility, and placement holds. Routed to the agency as a candidate absent
    or destroyed structure. Under broken placement it becomes `unverifiable`;
  - `AMBIGUOUS`: I is insufficient or inconsistent, or D's null cannot bound it.
- **The closed form, kept as a named analogy:**
  - λ* = min(1, p̂/E);
  - the log-drop is (E − p̂)²/(2E) for E > p̂;
  - the sampled first step falls only if E > 10p̂ on the 0.2 grid;
  - "fidelity" exceeds 1 when E < p̂;
  - the SURE remark holds only under its stated assumptions (zero-mean nuisance whose trace persists under
    pathology; fixed λ).

**Consumers:** K16, K22, K23, K12.

## 3. Mechanism

- **I comes from K19** and is never measured on blended data, so a prior cannot certify structure it inserted
  itself.
- **D is a deviation energy,** windowed so that a 15-voxel lesion is not diluted by a 2,000-voxel zone.
- **The words are routing codes,** never decisions and never emitted values. The agencies decide (K14 and K16).

## 4. Contracts

- `{structure, I_outcome, Q, window_id, null_quantile, survival_profile: [counts], word, placement_code}`.

## 5. Implementation choice

- **Numba** for windowed energies and survival counts, each with a reference and a SAME twin. **Pure Python** for
  the words.
- **Prior art:** KNEE_ARCHITECTURE §4.5 (the closed form; the placement margin), and GenomeVault's lens decoder
  (whose `:371` confidence is degenerate). **Decision:** the closed form is kept as an analogy and a twin. The
  placement margin becomes a constraint challenge only. Identity is re-founded on K19.

## 6. Verification

- **Detective:** the word decision and the null-quantile decision are converged.
- **Hypothesis:**
  - Q is invariant under voxel permutation within a window;
  - the survival profile is monotone in λ;
  - the closed-form identities hold (recomputed on generated E and p̂).
- **Phantoms:** lesions give `PEAK_DROP` with Q rising in amplitude; ligament gaps give `PEAK_DROP` (identified,
  damaged); complete absence with good placement gives `MONO_DOWN`; misregistration gives `unverifiable` or
  `AMBIGUOUS`, **never** `PEAK_DROP`.

## 7. Integration

Words and readings join the kept record and the context bank. Re-run `just firstlight`.

## 8. Acceptance

- **Behavioural correctness:** the decisions are pinned; the phantom words are as specified; first light is
  re-run.
- **Representation fidelity:** p̂_S and the nulls come only from `null`-role normals (a provenance test).
- **Domain validity:** the word rates on `checking` normals: `MONO_UP` dominant, `PEAK_DROP` at its null rate,
  `AMBIGUOUS` rare. E10's 62% AMBIGUOUS is the precedent this must not repeat unexamined.
- **Performance evidence:** milliseconds per structure.
- **Evidence scope:** the K19 identity outcomes and the null-role normals.
- **Invalidation:** a change to K19, the references, the windows, or the null roles.

## 9. Open matters

- **Policy (Q2's naming):** the founder confirms that the four words stay as names for (I, D) cells, or names
  the sweep observable he intended. The measurement here informs the choice.

## 10. Provenance and status log

- **Sources:**
  - THEORY II.5;
  - KNEE_ARCHITECTURE §4.5;
  - the Codex review rounds (C5–C6; round 3 acceptance);
  - THE_KNEE §2 (change 5).
- **2026-10-02:** specified in K00.
