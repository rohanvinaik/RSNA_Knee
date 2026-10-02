# K13a — The hardness map and the independence gate, for the zone questions

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K13a'` |
| **Depends on** | K13 (per-acquisition zone-lens readings), K10 (per-series deviation and tissue level), K09 (normals by role), K11 (phantoms), K03 (panels, oracle kinds, the recognition table) |
| **Consumed by** | K14 (`committee_outcome` receives independence classes and entitlement), K15 (confirmation becomes possible), K16, K17 (c₊ and c₋), K18 (first light), K23 (extends both to the structure questions) |
| **Commit label / tag** | `knee/K13a` · `knee-K13a` |

## 1. Purpose and authority

To measure, before any agreement counts, where each view goes blind or reads falsely in health, and which
acquisitions fail together. This covers every question the zone lenses can speak to.

- **ARCH §6.2, recipe step 7:** "*Measure the substrate* on the domain's own data before anything is taught: … and
  whether the views' errors are independent" (THESIS §13.1, step 7). THESIS §6.2: "the independence of views is
  measured before their agreement counts".
- **ARCH §6.6.3.** Phase 6's go/no-go begins with "the independence gate (§6.2.2)". Only then does Phase 7 start,
  "commit by gated concurrence". Each phase "is measured before the next begins".
- **Why it is lettered here.** The fresh read found that the book deferred dependence to K23, after first light.
  That left the loop's confirmations impossible and made its K15/K16/K20 ↔ K23 bootstraps circular
  (`provenance/build/revision_1.md`, §ORDER and §F06). The commit consumes entitlement (ARCH §5.3: coverage, the
  hardness map, censors, measured series, the entitlement table) and independence classes, so both come first
  for every question whose lenses exist.
- **The accord** (THE_KNEE §2 change 7): dependence is a graph of shared causes, with no imported bar, and
  "insufficient" where independence is not established.
- **The founder:** "a lens that is NEVER able to resolve the signal you want...well, isn't that a *perfect* lens
  for where your signal is *not*?? That IS information!"
- **Non-goals:**
  - the structure questions, whose lenses arrive in K20 (K23 extends this chapter to them);
  - multiway dependence beyond pairs (K23).

## 2. Dependencies and consumers

**Produced** (`knee.build.hardness`, `knee.build.gate`; loaders in `knee.core`):
- **The hardness map v1** (ARCH §4.2), from per-acquisition readings on normals split into a building half and a
  checking half. Per place, lens, sane value, series class and regime it holds:
  - the blank rate;
  - the healthy false-reading rate;
  - the disagreement rate between series.

  Each carries its count and bound, or reads `insufficient`.
- **Admission to the map:** a failure pattern enters only with a **law-named predictor** and its effect size
  (ARCH §4.2 step 5). The status per place is `readable | blind | misleading | hard`.
- **The gate table v1** (ARCH §5.3, §6.2.2): per (zone question, pair of series families, regime cell), the φ of
  the pair's error indicators and the joint-failure ratio κ, each with its count over studies where both spoke,
  and its bound. It is read on three measuring sets, kept apart:
  - P, with truth by construction (misses and false readings);
  - N, where any "for" is false as far as its reports attest;
  - report-localized calls, read as an upper bound ("κ against reports is an upper bound on joint view error,
    inflated by the report error rate", ARCH §6.2.2).

  Gold, at 58 study-level labels, is read where a study-level reading suffices, with its count stated.
- **The pair status:**
  - `independent_measured`, where the founder's bar is met;
  - `dependent_measured`;
  - `insufficient`, where the counts cannot bound;
  - `bar_unset`, where φ and κ are measured but no bar has been written.

  Only `independent_measured` makes two voices.
- **The entitlement table v1:** per question, place and series class, whether the series is a voice. A series is
  set aside only by a measured, law-named limitation, never because its dissent is inconvenient (ARCH §5.3).
- **The κ map,** handed to the hardness map as its `hard` places (ARCH §6.2.2).

**Consumers:** K14, K15, K16, K17, K18, K23.

## 3. Mechanism

- **What normals can establish.** They carry no target, so any "for" reading on them is false by construction,
  but only as far as their reports and the founder's sample attest (K09's impurity).
  - Normals establish *healthy* false readings and shared failure causes.
  - Sensitivity and lesion-related dependence need P, with its stated assumptions (K11).
  - The two evidence domains are reported separately.
- **Error indicators are per acquisition** (§F03). A reading computed jointly from several series is one
  dependent voice whose sources are all of them, and it is never paired with its own sources.
- **A silence is not an error.** It is the informational zero (ARCH §6.2.2; THESIS §6.3).
- **An unpredicted, unadmitted failure** concentrated at a place goes to the founder's sheet, as a lesion the
  reports missed or a law the design lacks. It never goes onto the map.
- **κ peaks** should fall on the known pitfalls (ARCH §4.2). A peak anywhere else is examined.

## 4. Contracts

- **Map:** per-place status volumes (uint8) and rate tables with counts and bounds, versioned with the template
  and layout.
- **Gate and entitlement:** JSON tables keyed by (question, zone class, series-class pair, regime cell), each entry
  carrying `{phi, kappa, n_both_spoke, bounds, status, bar_version}`.
- **Where they live.** They are derived records: the tables may enter git (AGENTS override 7). The bulk
  volumes live in `data/hardness/` and in a private dataset for the kernel.

## 5. Implementation choice

- **Numba scatter-add** into per-place integer count volumes, with a plain reference and a SAME twin. **Python**
  for rates, bounds, the gate and admission.
- **Built on the Mac Pro** by normal shards, after the node is identified (K01). The merge is an exact integer
  sum. Shards are merged only after a cross-node check on sample shards.
- **Prior art:** ARCH §4.2, §5.3 and §6.2.2; COMMITTEE §4.2; TIERED §3.1.1.
  - **Decision:** adopt the map's admission discipline and the pairwise gate, with the bar left to the founder.
    GenomeVault's φ < 0.25 is not imported (the accord).
- **Typist eligibility:** the scatter-add twin.

## 6. Verification

- **Detective:** admission, status, entitlement and the gate-status decisions are converged.
- **Hypothesis:**
  - rates lie in [0, 1];
  - every bound contains its rate, and no bound is claimed to shrink monotonically (§F15);
  - the merge is order-invariant;
  - a pair of a joint reading with its own source is never formed.
- **Replication:** the building half against the checking half, within bounds.

## 7. Integration

- K14's `committee_outcome` receives independence classes and entitlement, so `CONCUR` becomes possible
  wherever a pair is `independent_measured`.
- K18 runs with them. Until the founder writes the bar, every pair reads `bar_unset`, no answer is assigned by
  concurrence, and first light records that as its finding.

## 8. Acceptance

Written first: `acceptance/K13a.toml`.
- **Behavioural correctness:** the decisions are pinned, the merge is exact, and SAME holds for the scatter-add
  twin.
- **Representation fidelity:** every gate entry carries its counts, bounds and evidence domain, and the map
  replicates on the checking half.
- **Domain validity (discovery):**
  - κ's peaks against the named pitfalls;
  - the two evidence domains, reported apart;
  - the share of pairs `insufficient`, per question;
  - per question, which acquisitions can ever be two voices.

  A miss opens a problem in §9 (R1).
- **Performance evidence:** places and normals counted per shard, with bytes scanned.
- **Evidence scope:** the normals at their roles with their measured impurity; the phantoms of K11 with their
  stated assumptions.
- **Invalidation:** a change to the readers (K10, K13), the normals, the template, the layout, or the bar.

## 9. Open matters

- **Policy (founder; ARCH §6.7 item 8):** the knee's independence bar, meaning what φ and κ count as two
  voices. It is written before the gate's run. ARCH adopted GenomeVault's levels "provisionally until the
  founder sets the knee's own bar"; the accord dropped the imported bar. Until it is written, pairs read
  `bar_unset`.
- **Facts:**
  - which acquisition pairs are independent, per zone question and regime;
  - the gap between κ against reports and κ against P.

## 10. Provenance and status log

- **Sources:**
  - ARCH §4.2, §5.3, §6.2, §6.2.2, §6.6.3, §6.7 (item 8);
  - THESIS §6.2, §13.1 (step 7);
  - COMMITTEE §4.2;
  - TIERED §3.1.1;
  - THE_KNEE §2 (change 7).
- **2026-10-02:** specified in revision 1 (`provenance/build/revision_1.md`, F06, F07, F51), split from K23 and
  placed before the loop as ARCH orders it.
