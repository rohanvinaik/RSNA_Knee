# K22 — Perturbation: a truth that survives a small step either way

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K22'` |
| **Depends on** | K20, K21 (readings to perturb), K07 (registration and its measured error), K12 (versioned quantizers) |
| **Consumed by** | K23 (flips on normals), K15/K16 (stability in the kept record), K17 (stability as an ordering key only after its information test) |
| **Commit label / tag** | `knee/K22` · `knee-K22` |

## 1. Purpose and authority

A static knee has no time. Its anchors are steps in frame and encoding instead.
- **THESIS §3.4:** "A truth that survives a small step either way is real."
- **The founder** (2026-10-02): "doing a small perturbation and random shift to re-encode the codebook on the
  same data with mild perturbation".
- **Codex** (design round 1): "If uncertainty exceeds lesion scale, report that limitation rather than shrinking
  the test until it passes."

## 2. Dependencies and consumers

**Produced** (`knee.run.perturb`):
- **Frame families:**
  - R1: in-plane shift;
  - R2: through-plane slice phase;
  - R3: rotation about the zone centre;
  - R4: a registration re-run with a new sampling seed (expensive);
  - R5: another checked template (expensive).
- **Quantizer families:**
  - QZ1: middle edges by a fraction of a level;
  - QZ2: the z threshold among its sane values;
  - QZ3: the detrend scale, if K10 kept one;
  - QZ4: codebook seed invariance. This is a check, not a perturbation: any change it moves is a fault.
- **Per reading:**
  - the stability fraction s (per family and overall);
  - the flip-axis profile;
  - the two-span ratio;
  - the sandwich status (held between, or isolated).
- **Stated limitation:** where a zone's measured registration error (K07/K08) exceeds the step allowed below
  lesion scale, the frame test there is reported as `zone_bound: uncertainty_exceeds_lesion_scale`. It is never
  run with a shrunken step that would read as stable.

**Consumers:** K23, K15/K16, K17.

## 3. Mechanism

- **Steps are two-sided,** at δ and 2δ.
  - δ comes per zone from the **measured** registration uncertainty: K07's landmark and check-registration
    disagreement.
  - The quantizer steps are fractions of a level.
- **Cheap families** (R1–R3, QZ1–QZ3) run inside candidate and structure crops. **Expensive families** (R4–R5) run
  on escalation only: a placement alarm, a committed object that flips under R1 or R2, or a hard zone (ARCH §4.3,
  l.2759–2764).
- **In DEPLOY** (internet off; the 9-hour budget), an escalation runs inside the kernel's own budget, or is skipped
  and recorded `escalation_unavailable`. The Mac Pro serves build time only, and no kernel path reaches it.
- **Perturbations are never votes.** s measures robustness; it is never a witness (K14).

## 4. Contracts

- `{reading_id, families: {R1: {steps: [...], kept: k, n: n}, ...}, s_overall, flip_axis, two_span_ratio,
  sandwich, limitation?}`.

## 5. Implementation choice

- **Python orchestration** re-uses the lens and reader kernels on perturbed crops.
- **Threads with `nogil`** across perturbations, with ownership declared against the Numba and ITK threads.
- **R4 and R5** on the Mac Pro as batch jobs where escalations accumulate at build time, the node identified first
  (K01).
- **Prior art:** KNEE_ARCHITECTURE §4.3. **Decision:** adopted, with the magnitude rule amended per Codex (a stated
  limitation instead of capping below uncertainty).

## 6. Verification

- **Detective:** the step-magnitude decision, the sandwich decision and the limitation decision are converged.
- **Hypothesis:**
  - QZ4 changes nothing;
  - s lies in [0, 1];
  - two-sided steps are symmetric.
- **Phantoms:** s rises with lesion size and amplitude. Misregistered normals flip along the shift's axis.

## 7. Integration

s and the flip axis join the kept record, and K17 places s as its second key on ARCH's structural argument
(l.4427–4430). s is read against phantoms of its size and zone (ARCH l.2779–2781).

Two measurements are **reported** and **never admit or bar s**:
- whether s orders P above `checking` normals where the keys above it tie;
- whether s is a function of |z| (ARCH l.2784: "quantizer flips that only track |z|, so that s restates
  magnitude").

ARCH §6.1.4's admission test is admission by discrimination on one query, which the No Popery law forbids. The
conflict is put to the founder (`provenance/build/revision_1.md`, §F24). Re-run `just firstlight`, and read its
diff against this chapter's behaviour-change record.

## 8. Acceptance

Written first: `acceptance/K22.toml`.
- **Behavioural correctness:** the decisions are pinned; QZ4 invariance holds; first light is re-run; no kernel path
  reaches a remote node.
- **Representation fidelity:** the limitation is recorded wherever uncertainty exceeds lesion scale. The count of
  such zones is reported.
- **Domain validity (discovery):**
  - stable false readings on `checking` normals, reported (K23's input);
  - the phantom response of s, per phantom family;
  - the two reported measurements of s above.
- **Performance evidence:** perturbations counted per study by family; escalations counted, and those skipped in
  DEPLOY; seconds as information.
- **Evidence scope:** the reading set of K13, K20 and K21, at the measured uncertainties.
- **Invalidation:** a change to registration uncertainty, to a reader, or to the quantizer edges.

## 9. Open matters

- **Facts:** whether s adds order beyond the magnitude readings. This is measured and reported, never gating.
- **Policy (founder):** the conflict between ARCH §6.1.4's admission test and the No Popery law (K17, §F24).

## 10. Provenance and status log

- **Sources:**
  - THESIS §3.4 and §11.5;
  - KNEE_ARCHITECTURE §4.3;
  - Codex design round 1 (item 7);
  - founder ruling 5 (SESSION_BRIEF §3).
- **2026-10-02:** specified in K00.
- **2026-10-02, revision 1:**
  - no admission of s by discrimination, its measurements reported only (F24);
  - escalations in DEPLOY stay inside the kernel or are skipped (F38; ARCH §4.3);
  - work counted (F39).
