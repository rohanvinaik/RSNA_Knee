## Context

See proposal.md for the integration problem. The detailed existing mechanism is
[CLASSICAL_AI_BUILD_DESIGN.md](../../../docs/CLASSICAL_AI_BUILD_DESIGN.md).
The current packet named by FULL_BUILD_PLAN section 13 owns source and worker state.

## Goals / Non-Goals

Complete the existing production joins with testable scope and admission semantics.
Do not replace the encoder, introduce a universal episode framework, require full
anatomy reconstruction, or convert this classical-AI design into ML.

## Decisions

- **Keep one memory and existing adapters.** Extend signed publication and its real
  consumers rather than create a second classifier. Adapt reject negative_views
  into the reject's views, preserving original calls and source fingerprints.
- **Separate answering from publication.** Missing anatomy is neutral in recall;
  a new automatic addition needs affirmative applicable support. A direct visual
  call is an independent teaching route and does not await complete geometry.
  Support names an observed anatomical fact, including applicable intrinsic
  structure or an established relation; a score or bare status supplies no new fact.
- **Anatomy is a law check.** A pass rules nothing in; it records that the candidate lies where
  the object can lie. Plausible but wrong tissue is stopped by negative cases in joint recall, not by
  requiring one check to recognize tissue. Map distances aim the search and are not admission limits.
  The first growth round's admissions are inspected before its child becomes the next parent;
  later rounds are spot-checked, not held for a picture check.
- **Use actual partial geometry.** Extend the sanity consumer of native planes;
  placement already accepts partial anchors. Do not infer occupied volume from
  key planes or overlapping search windows.
- **Preserve the signed store in growth.** Reuse the same parent preparation and
  source exclusion across all record kinds. Keep signed cases, full/cheap data,
  asserted scope and lineage in the portable child. Never teach from a new case
  during the round that proposes it.
- **Connect the existing orchestrator.** Identity must affect the object evidence
  used by condition recall and named bounded requests, rather than only the study
  JSON. Keep conflict distinct from clinical absence.
- **Learn through concrete consumers.** Carry cue, recalled expectation, action,
  independent outcome and named differences through existing case/censor/split
  and procedure mechanisms. A special veto is not inferred from a bank count.

## Risks / Trade-offs

- Unknown-only anatomy will defer automatic additions -> use available partial
  directions and independent visual teaching; do not force unknown to positive.
- Mixed-view teaching can be widened accidentally -> pin exact scopes at adapter,
  recall, growth and condition-consumer boundaries.
- A child can lose counterevidence -> test signed-table persistence and negative-only
  study exclusion through publication, reload and next-round recall.
- Passing local tests can hide an unused result -> trace callers and verify the
  actual entry point before claiming integration.

## Migration Plan

Integrate bounded candidates in the existing source tree. Publish a new immutable
signed memory; retain earlier source memories and calls. Verify the grown child
before selecting it for production. Rollback selects a prior frozen memory and
source revision; it does not rewrite teaching history. Gate the final integrated
tree, then perform the private offline Kaggle resource run.
