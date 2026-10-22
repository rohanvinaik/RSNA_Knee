# Quality/publication pass — 2026-10-22

Rohan authorized the full CI gate, correction of issues found, commit and push.
Application development/training remains paused; this pass does not authorize a
Kaggle run or formal competition submission. His additional remote-cleanup request
is included below. Live publication state remains only in FULL_BUILD_PLAN §13’s
packet; this is a dated change/evidence record.

## Corrections applied

- Updated Pillow12.3.0 to13.0.0 in the lockfile. The all-extras/all-groups audit
  initially reported35 vulnerabilities in Pillow; the repeated audit reported
  `no_known_flaws`. No dependency scope was narrowed to obtain that result.
- Checkpoint loading uses `torch.load(weights_only=True)` with explicit unsafe/
  malformed refusals and no unsafe fallback. Interrupted-resume tests preserve
  identical final weights and predictions.
- The serializer validates a finite closed range before testing its endpoints.
  Exact endpoint tests now use ordered boundary comparisons within that validated
  range, preserving the same outputs without ineffective Sonar annotations.
  No tolerance, threshold or output policy was changed.
- Blank/ragged CSV rows now receive named refusals before indexing in BOTH Kaggle
  wrappers. Recorder null/list/empty mappings receive named CLI refusals too.
- Metadata-only replay no longer imports NumPy through the bank-name parser.
  Array validators import it when needed; validator behavior is unchanged.
- Hosted CI installs and explicitly imports the training extra, so trainer tests
  cannot silently skip. Its locked Linux closure includes about3.01GB compressed
  wheels; no-cache install avoids retaining that second copy. Hosted installed
  capacity remains a measurement, not a claim from this size calculation.
- Deptry now correctly identifies the two existing sibling-script modules as
  first-party imports. Whole-tree Ruff lint/format failures were repaired.
- Obsolete synthetic bank fixtures now declare actual object roles. Two older
  assertions expecting one unlocalized bone to gain configuration authority were
  corrected to the already-approved scoped refusal, with localized controls kept.
  Generic orchestration fixtures use real clinical declarations and retain the
  actual serializer. Current endpoint/dependency metadata is pinned explicitly.
- The demonstration document no longer claims zero parameter fitting, held-out
  validation from teaching readback, guaranteed abstention or comparative success
  unsupported by the recorded experiments.

## Artifact compatibility, without retraining

Ruff changed the feature writer’s bytes but not its normalized Python AST. Original
training artifacts remain immutable. A new compatibility artifact and dataset
metadata copy preserve the numeric arrays and historical training provenance:

```text
data/readings/som-navigation-20261022/navigation-r2-quality-r1
data/readings/som-navigation-20261022/dataset-r2-quality-r1
```

- Current writer SHA256: `c49cfed30c311d62dcecc85f46fe671d55c662f148dff48089cc118309990ac7`.
- Before/after normalized AST SHA256: `28b871a9e7ce53806ec64a1892283083901a9a2f0232e01aa6a38d6da73c7064`.
- Compatible navigation manifest: `13991b30579c61ffc6c7a3bb11aa89c13d108c883a886f511314f1ded49ff017`.
- Compatible schema: `f83b8256f6bed551a3143d12d74e0c4228830ed6c9da09d4383c4f3292cb882c`.
- Weight bytes unchanged: `a5c9c4cef5ef0511c275f67730af8e0e13f900df0c030e4dfba908f9b6121be7`.

All118 prediction and routing-weight arrays are bit-identical under old/new
artifacts. Current runtime pin validation and application to an actual retained
study record passed. No MRI was remeasured and no new clinical judgment or
parameter training occurred. The old train-r2 model/checkpoint remains historical;
source-pinned resume must not silently accept a changed trainer.

Full receipt: `data/readings/grounded-teaching-20261022/quality-pass-r1/navigation-compatibility-export-r1.json`.

## Verification protocol and remaining advisory information

The exploratory full gate found43 test failures, lint/format failures and three
Sonar correctness findings. Those results were retained, not relabelled green.
Focused tests and the corrections above precede the final gate. The publication
requires `scripts/ci_local.sh` passing on exactly the tree committed and the normal
pre-push hook’s secret/dependency checks. The authoritative final result is the
matching tree stamp under `.git/gate-passed/` and GitHub’s gate for the pushed
revision, rather than a manually predicted result in this document.

Existing advisory findings are not all defects. The reviewed type output was
predominantly unchanged-source/NumPy-stub issues; the new SoM source is type-clean.
Vulture’s lists include dynamic interfaces and test/reference tools and were not
used to delete the author’s design. PERF/FURB suggestions are leads, not targets.

Three recorded-kernel memray peaks exceeded this machine’s prior cache baseline:
physical squint229.4→283.5KiB, coarse depth741.6→741.7KiB and enclosed
darkness6.4→16.2MiB. The kernel functions are AST-identical to the recording and
HEAD; no output/mutation assertion failed. The prior environment provenance is
unavailable, so the larger peak remains a performance lead, not a proved leak or
whole-run RSS claim. The baseline was not reset and no limit was relaxed.
The advisory inventory and raw coherent reports are retained in `quality-pass-r1/`.

A clean software gate is not clinical validation, completion of the interrupted
58-study check, proof of learned transfer or verification of hidden-scale runtime.
Those earlier experimental limitations remain in the notebook and current packet.

## Remote shutdown verified

At22:58:42UTC on2026-10-22, full process inventories on SSH aliases `squishhub`
and `sanjay` showed no remaining project inference, training, extraction, download
or worker jobs. SquishHub had no caffeinate. Sanjay’s confirmed
`/usr/bin/caffeinate -dims` PID75258 was stopped with SIGTERM after PID, command
and UID revalidation; the follow-up inventory showed no caffeinate on either host.
No unrelated application or service was stopped. No new remote work was launched.
Evidence: `quality-pass-r1/remote-cleanup-r1/receipt.json`.

## Secret preflight

The scanner flagged a historical parent-manifest SHA256. Its value was checked
against the actual saved manifest bytes, then annotated on that single line with
the scanner’s standard allowlist comment. The unannotated history is preserved
locally as `quality-pass-r1/history167-original.md`; the published copy declares
the annotation. No scanner rule or hook was weakened.
