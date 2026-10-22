# Bounded train-ready repairs and the integration handoff

This is a dated implementation record, not a second current queue. The sole live packet is
`docs/work/current/README.md`. Rohan explicitly asked this session to implement the small gaps
found in review while the other agent continues the larger build. All pre-existing edits were
preserved; this session did not publish a memory or start a competing training round.

## Changes to retain

1. **Action attribution governs procedure credit.** In `squint_procedure_memory._row_category`,
   a question's final answer without single-action attribution is `outcome_unattributed`.
   Its measured information, independent clinical answer and original record remain intact.
   It cannot promote or veto an individual procedure, or become that procedure's counterexample.
   Recall reports the retained row IDs explicitly instead of silently assigning success/failure.
2. **Pre-action cues retain temporal meaning.** `_row_cue_banks` accepts the recorded before-action
   cue or an explicitly linked pre-action cue. A profile marked `coarse_banks_from_record` remains
   available in the experience but cannot silently stand in for what was observed before the action.
3. **Round children carry their actual lineage.** `run_round` writes `parent_revision` and
   `parent_manifest_sha256` on the child. Recovery after child publication can reuse that child
   without rerunning studies or replacing its manifest.
4. **Partial recovery compares content, not just IDs.** `_memory_content_sha256` compares the complete
   serialized semantic memory, excluding the existing runtime/publication-derived fields. Same case
   IDs with changed clinical calls, signed teaching, profiles or procedure rows do not pass recovery.
5. **Training-export checkpoints verify inputs and outputs.** `_training_export` reuses the ordinary
   `prepare` operation; its checks include source run/record pins, code, labels, memory and output
   file digests. The existing inference receipt is preserved on recovery instead of being rewritten
   with a different executed/resumed count that invalidates its own provenance.
6. **The new child's corpus is exported after publication.** A round's `training/` remains the
   parent/pre-action material. Its `child-training/` contains a separate normal/condition corpus and
   experience export pinned to the published child, including new reviewed visual teaching.
   `round-receipt.json` and the CLI return name `child_training` explicitly. Consume that export for
   post-round corpus work; do not relabel the old parent export as the new corpus.

Primary source changes: `scripts/prepare_squint_training.py` and
`src/knee/diagnosis/squint_procedure_memory.py`. New both-sign tests:
`tests/test_train_ready_repairs_intent.py`. These synthetic tests establish wiring, signed meaning,
durability and CLI behavior; they are not evidence of diagnostic transfer to a different patient.

## What the other agent should do next

- **Integrate these exact changes into the shared source.** Preserve the signed-label repair and
  direct per-action recording already present. Do not restore diagnosis/identity cases as generic
  procedure failures, or a final study finding as evidence that each earlier look helped.
- **Run new attributed episodes now.** Old material remains useful; its independent labels still
  teach diagnosis. Historical action usefulness remains unknown unless the original observations
  establish a unique reconstruction. Do not manufacture attribution or discard the material.
  Identity-procedure retention currently records a before/after recall and final consumption;
  extend its producer with an actual action-specific outcome/cue before claiming those rows teach
  individual procedural success. Ordinary signed identity teaching continues independently.
- **Show one actual learning-to-action example.** Frozen parent → real observation and appropriately
  checked outcome → one published child → a changed action/identity/consumer on another fully excluded
  study, plus a different-context control → next round reading the child. Reuse existing real evidence
  where it has the necessary provenance. The temporary synthetic tests do not complete this milestone.
- **Continue direct visual teaching in parallel.** Refresh addressed readback on the newest memory;
  classify remaining rows as missing teaching, unused existing teaching, scope/measurement mismatch,
  genuine contradiction or ambiguity. Fill actual missing examples from pictures and official labels.
  Unimplicated correctly identified objects are valid normal examples. Do not resume an automatic
  all-58 recognition campaign or make its perfection a condition of training.
- **Complete the remaining round input/source pins.** The current source list covers twelve modules,
  not the full decoding/profile/anatomical producer closure. Reuse the existing whole-source identity
  mechanism; verify ready-study input identities. Do not silently resume an older round after a code
  change. Use a fresh output root for the new code epoch and the newest parent on the one memory chain.
- **Check resource failure applicability.** A remembered failure to obtain a reading must not veto a
  currently available action merely because the image resembles that past situation. Preserve the
  failure's actual cause/preconditions; do not invent a global exclusion or a numeric cutoff.
- **Use the existing actual batch and publication routes.** `--run-round` now retains procedure
  experiences, composes supplied visual teaching/clinical calls and publishes their child. It does not
  itself call identity-growth admission. Compose the existing warranted growth/review/correction route
  explicitly when doing corpus expansion; do not advertise this command alone as the whole SoM learner.

Before making an anatomical judgment, read the relevant whole units in DIAGNOSTIC_PAIR_PACKET,
AI_DIAGNOSTIC_DESIGN, RELATIVE_POSITION_MAP and RESOLVING_THE_PARTS. For representation and learning,
use the cell project's HDC_DESIGN, K_LINES and relevant whole prompts in
CLASSICAL_LAYERS_FOUNDER_WORDS, under the knee author's latest conversations. Each agency learns
from evidence on its own question; a K-line remains one case, not a pooled class prototype.

The thin operational training pilot and complete 58-study addressed teaching readback remain
different deliverables. Keep all signed cases, clinical/view scopes, immutable lineage and whole-study
exclusion. No model/capacity sweep, fitted healthy band, new generic learner or Kaggle run is this task.

## Verification

The final verification record and any Detective limitations are linked from the sole current packet.
Do not infer a complete integrated CI/Sonar pass or a real-patient learning demonstration from the
focused tests above. No actual memory publication is claimed by this repair record.
