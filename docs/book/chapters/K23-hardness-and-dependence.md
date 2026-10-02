# K23 — The hardness map and dependence

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K23'` |
| **Depends on** | K22 (flips), K09 (normals by role), K11 (phantoms), K13/K20/K21 (raw readings) |
| **Consumed by** | K14's contracts (entitlement and dependence data plug in), K16 (concurrence becomes possible), K26 (soft places), K17 |
| **Commit label / tag** | `knee/K23` · `knee-K23` |

## 1. Purpose and authority

To learn, from observation, where each view goes blind or reads falsely in health, and which acquisitions fail
together.
- **The founder:** "a lens that is NEVER able to resolve the signal you want...well, isn't that a *perfect* lens
  for where your signal is *not*?? That IS information!"
- **The accord** (change 7): dependence is a graph of shared causes; no imported bar; "insufficient" where
  independence is not established.
- **Codex** (design round 2): normal observations establish *healthy false readings and shared failure causes*.
  Positive sensitivity and lesion-related dependence need phantoms or independently supported positives. The two
  evidence domains are stated separately.

## 2. Dependencies and consumers

**Produced** (`knee.build.hardness`; `knee.core.hardness` for the loader):
- **The hardness map,** from **observed raw readings** on normals, split into building and checking halves. Per
  place, lens, sane value, series class and regime:
  - the blank rate;
  - the healthy false-reading rate (a reading beyond its healthy interval on a normal);
  - the disagreement rate between series;
  - the flip rate (K22).

  Each carries its count and bound, or reads `insufficient`.
- **Admission:** a failure pattern enters the map only with a **law-named predictor** that separates it (fiber
  angle to B0; distance in slices to a boundary; residual type; atlas vote fraction; flexion; regime), with an
  effect size. Status per place: `readable | blind | misleading | hard`.
- **Dependence**, between series pairs and multiway, per question and place: φ and κ of joint false readings on
  normals, with shared causes named. And, separately, joint misses and false readings on phantoms (the sensitivity
  domain). The status per pair and set is `independent_measured | dependent_measured | insufficient`. No genomic
  bar is used: the levels are written before the run (policy, below).
- **Entitlement tables:** for each question, place and series class, whether the series is a voice. A series is
  set aside only by a measured, law-named limitation, never because its dissent is inconvenient.

**Consumers:** K14, K16, K17, K26.

## 3. Mechanism

- **Normals carry no target,** so any "for" reading on them is false by construction, but only *as far as their
  reports and the founder's sample attest* (K09's impurity).
- **An unpredicted, unadmitted failure** concentrated at a place goes to the founder's sheet as a lesion the
  reports missed or a law the design lacks. It never goes onto the map.
- **κ peaks** should fall on the known pitfalls: pseudotear sites, the magic-angle window, the meniscus–capsule
  junction. A peak anywhere else is examined.

## 4. Contracts

- **Map:** per-place status volumes (uint8) plus rate tables with counts and bounds, versioned with the template
  and layout.
- **Dependence and entitlement:** JSON tables keyed by (question, zone class, series class pair or set).
- **All competition-derived:** `data/hardness/`, and a private dataset for the kernel.

## 5. Implementation choice

- **Numba scatter-add** into per-place integer count volumes, with a reference and a SAME twin. **Python** for
  rates, bounds and admission.
- **Built on the Mac Pro** by normal shards. The merge is an exact integer sum, with cross-node SAME on sample
  shards.
- **Prior art:** KNEE_ARCHITECTURE §4.2 and §5.3; COMMITTEE §4.2; TIERED §3.1.1. **Decision:** adopt the map's
  admission discipline. Replace the pairwise gate with the graph plus multiway checks. Drop GenomeVault's φ < 0.25
  bar.

## 6. Verification

- **Detective:** admission, status, entitlement and the dependence-status decisions are converged.
- **Hypothesis:**
  - rates lie in [0, 1];
  - bounds shrink with n;
  - the merge is order-invariant.
- **Replication:** the building half against the checking half, within bounds.

## 7. Integration

- K14's `committee_outcome` now receives measured dependence, so `CONCUR` becomes possible.
- K16 is re-run.
- `just firstlight` is re-run; the change in decisions is recorded as this chapter's effect.

## 8. Acceptance

- **Behavioural correctness:** the decisions are pinned; the merge is exact; first light is re-run and its changes
  explained.
- **Representation fidelity:** the map replicates on the checking half.
- **Domain validity:** κ peaks at named pitfalls; the evidence domains (healthy against lesion) are reported
  separately; `insufficient` is used where counts cannot bound.
- **Performance evidence:** normals per hour per node.
- **Evidence scope:** the normals at their roles and their measured impurity; the phantoms of K11.
- **Invalidation:** a change to the readers, the normals, the template or the layout.

## 9. Open matters

- **Policy:** the dependence levels (what φ, κ and multiway statistics count as independent), written before the
  run by the founder or by an argued default recorded here. The genomic numbers are not inherited (Codex design
  round 2, Q8).

## 10. Provenance and status log

- **Sources:**
  - founder ruling 3 (SESSION_BRIEF §3);
  - KNEE_ARCHITECTURE §4.2, §5.3, §6.2.2;
  - COMMITTEE;
  - TIERED;
  - THE_KNEE §2 (change 7).
- **2026-10-02:** specified in K00.
