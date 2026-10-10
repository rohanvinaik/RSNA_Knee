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
  over `null`-role normals.
  - **The null matches the statistic.** It is the same *maximum-window* statistic, over the same window size and
    shape, zone and plane, on the same normals (ARCH §4.5 l.3080–3084: "the null of that maximum is measured on
    true normals").
  - **Degenerate cases,** following ARCH l.2998 and l.3007–3016:
    - E = ‖z‖² = 0 gives λ* = 1 through the clip, which reads `MONO_UP` ("every ‖z‖² ≤ p̂_S … reads so");
    - a p̂_S that cannot be measured, or measures 0, is `insufficient`, and the word is `AMBIGUOUS` with that
      cause ("a window's count cannot bound its statistic");
    - a window whose places are all silent is silent and takes no word.
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

- **The layout extension:** the word and λ* are written as the context bank's trajectory byte (ARCH Table 3.1, bits
  20–27; "metadata, never a verdict", l.3103–3105). This makes a new layout version, v2.1.

**Consumers:** K16, K22, K23, K12 (the layout version).

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
  - the closed-form identities hold (recomputed on generated E and p̂);
  - E = 0 reads `MONO_UP`; an unmeasurable p̂ reads `AMBIGUOUS:insufficient`; a silent window takes no word;
  - the null's window size, shape, zone and plane equal the study's.
- **Phantoms:** lesions give `PEAK_DROP` with Q rising in amplitude; ligament gaps give `PEAK_DROP` (identified,
  damaged); complete absence with good placement gives `MONO_DOWN`; misregistration gives `unverifiable` or
  `AMBIGUOUS`, **never** `PEAK_DROP`.

## 7. Integration

Words and readings join the kept record and the context bank. Re-run `just firstlight`.

## 8. Acceptance

Written first: `acceptance/K21.toml`.
- **Behavioural correctness:** the decisions are pinned; the phantom words are as specified; first light is re-run,
  and its decision diff is read against this chapter's behaviour-change record.
- **Representation fidelity:** p̂_S and the nulls come only from `null`-role normals (a provenance test).
- **Domain validity:** the word rates on `checking` normals: `MONO_UP` dominant, `PEAK_DROP` at its null rate,
  `AMBIGUOUS` rare. E10's 62% AMBIGUOUS is the precedent this must not repeat unexamined.
- **Performance evidence:** windows and places counted per structure; seconds as information.
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
- **2026-10-02, revision 1** (F50; ARCH §4.5): the null matched to the window statistic; the degenerate cases;
  the trajectory byte as layout v2.1.
