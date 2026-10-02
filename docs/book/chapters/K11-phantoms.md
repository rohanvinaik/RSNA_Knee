# K11 — Phantoms: truth specified independently of the readers

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K11'` |
| **Depends on** | K10 (hosts read and quiet places known), K08 (zones for placement) |
| **Consumed by** | K13, K15, K19–K23, K25 (response and specificity), K07 (misregistration phantoms), K24 (upgrade when the law holds) |
| **Commit label / tag** | `knee/K11` · `knee-K11` |

## 1. Purpose and authority

To manufacture labelled cases whose truth is known by construction. They measure the response, the specificity
and the wiring of every reader.
- **VERDICT:** the synthetic world "validates WIRING and response only".
- **Codex** (design round 2, D3): "Define phantom truth and generation rules independently of K10's measured
  outputs. A generator may run before the reader; acceptance compares them."
- **Non-goals:** phantoms never establish that a reader finds *real* lesions.

## 2. Dependencies and consumers

**Produced** (`knee.build.phantoms`):
- **Generators**, each a pure specification plus a deterministic planting function:
  - **geometry and misregistration:** a host shifted, rotated or slice-phase-shifted by known amounts;
  - **acquisition:**
    - a failed fat-suppression field (smooth, peripheral);
    - a ghost band along the phase-encoding axis;
    - magic-angle brightening on short-TE series only, in fibrous zones at θ ≈ 54.7°;
  - **lesions:**
    - effusions by volume in recesses;
    - collections with and without a neck;
    - geographic marrow edema at named subregions, with and without a line;
    - meniscal signal touching a surface on k slices;
    - ligament gaps;
    - lining thickening behind an effusion;
  - **near misses:**
    - intrasubstance meniscal signal without contact;
    - a line without edema;
    - trace fluid;
    - fluid beside, not around, the MCL band;
    - a fat-pad cleft.
- **Truth records** per phantom: the generator, its parameters, its seed, the planted region, and the expected
  readings stated as **generator facts** (where signal was placed, in which series, at what amplitude), never as
  reader outputs.

**Consumers:** K13 and K15–K25.

## 3. Mechanism

- **Hosts** come from the `host` role (K03), the report-negative candidates held out of the references.
- **Planting** happens only where the host's own readings (K10) are quiet. Each host's pre-existing deviations are
  recorded.
- **Consistency across series without the law.** A lesion is planted through **per-series signature templates**:
  the tissue's expected sign and a declared amplitude per series class, scaled by each series' measured local
  intensity statistics. So the phantom is consistent across contrasts by construction, without inverting the
  signal equation. K24 may later upgrade selected generators to forward-model through the law, where the law
  holds.
- **Partial volume** at the phantom's border follows each series' slice profile, from the header geometry.
- **Amplitude sweeps** give each reader its response curve: the response must rise with amplitude, and the
  no-lesion control must sit at chance (VERDICT, Decision 3).

## 4. Contracts

- **Phantom volumes** are written as **derived copies** of host plane volumes, with manifests linking each to its
  host, generator and truth record. They are competition-derived, so they stay in `data/phantoms/`.
- **Generator specifications** and their authored synthetic unit fixtures are independent of competition data,
  and go in git.

## 5. Implementation choice

- **Python specifications;** the per-voxel planting runs as a Numba twin under SAME.
- **Prior art:** the synthetic smoke of `tools/make_or_break.py` (VERDICT's amplitude curve). **Decision:** its
  amplitude-response discipline is reused as a requirement; its generator is rewritten, because it has no
  cross-series consistency and no named sites.

## 6. Verification

- **Detective:** the generator parameter decisions (placement admissibility, quiet-host check) are converged.
- **Hypothesis:**
  - planting is deterministic per seed;
  - outside the planted region the volume is byte-identical to the host;
  - the planted amplitude is as specified per series.
- **SAME** for the Numba planter.

## 7. Integration

`just phantoms` builds the library, versioned. Each reader chapter's acceptance names the phantom IDs it is
judged on.

## 8. Acceptance

- **Behavioural correctness:** the generator's laws hold; SAME; the decisions are pinned.
- **Representation fidelity:** the truth records match the planted volumes exactly.
- **Domain validity:** reported, not gated. K10's response on each lesion generator over amplitude: it rises,
  with controls at chance. Signature consistency is **not** a claim of clinical realism.
- **Performance evidence:** phantoms per second, informational.
- **Evidence scope:** the generators at this version.
- **Invalidation:** a change to a generator, to the host roles, or to the series classes.

## 9. Open matters

- **Facts:** whether signature-template phantoms are realistic enough for the readers' acceptance. Measured where
  gold allows, never assumed.

## 10. Provenance and status log

- **Sources:**
  - LENS Phase 4;
  - VERDICT;
  - KNEE_ARCHITECTURE §3.3.10 and §5.8;
  - Codex design round 2 (D3);
  - THE_KNEE §5.
- **2026-10-02:** specified in K00.
