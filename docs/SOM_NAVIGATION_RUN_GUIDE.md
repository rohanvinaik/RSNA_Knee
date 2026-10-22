# Three-stage navigation over the fixed knee representation

Rohan's controlling decision is recorded verbatim in
[the navigation conversation](conversations/2026-10-22-three-stage-navigation-training.md):
use the paper's three-stage learned navigation layer over HDC signals. This extends the
existing society; it does not replace the lenses, exact HDC representation, anatomical
definitions, signed K-lines or their scoped evidence.

## State at the 2026-10-22 wind-down

Work stopped at Rohan's request. Training revision 2 completed; its fresh 58-study MRI
check did **not** complete. Commands below document supported operations for a later
authorized session; no training, inference, packaging or submission is queued.
[The current packet](work/current/README.md) owns current state.

| Artifact | Retained state | Evidence boundary |
|---|---|---|
| Signed memory | `data/readings/grounded-teaching-20261022/growth-batch-20/next-wave-run-r1/category-review-r3/published-learning-child-r1/memory` | 1,061 cases; manifest SHA-256 `ccd01612d36eae5a25a73c03a6937fc44ad9317e8390a71d13beac5c55d23da8`. |
| Dataset | `data/readings/som-navigation-20261022/dataset-r2` | 106 training studies, including the 58 official teaching studies, and 12 validation studies; 63,502 features. The 58 are training material, not held-out validation. |
| Learned artifact | `data/readings/som-navigation-20261022/train-r2` | 16 specialists, 10,566,320 parameters; all three training stages completed. |
| Current-source MRI check | `data/readings/som-navigation-20261022/gold58-current-check-r2` | Interrupted at user request, exit 130: four complete retained study records, each with 12 questions; no completed cohort receipt or 58-study result. |

The [training receipt](../data/readings/som-navigation-20261022/train-r2/training-receipt.json)
pins artifact SHA-256 `ea487781d8b0653b3045f17ec7218137d0e9da699bc56e0a89e93e257353b39b`
and dataset SHA-256 `8bb3b45eaf0ef0d3dc505e3432b2c24cbc385034feb0bbb3af321fb9b347b1d4`.
NumPy/Torch maximum probability and gate differences were approximately 1.19e-7 and
5.96e-8. This verifies export parity, not diagnostic accuracy.

The [interruption receipt](../data/readings/som-navigation-20261022/gold58-current-check-r2/root-interruption-receipt.json)
pins the four retained records and reports no changed source files during the run;
the launch pinned 134 source files. The preceding `gold58-current-check-r1` attempt
refused an existing output directory before reading a study. Preserve both attempts.
Neither establishes full-cohort diagnostic capacity.

## Data flow and authority

1. The ordinary squint pipeline produces typed object banks, both sides of contextual
   recall, applicable censors and observed anatomical checks. Missing readings retain
   availability; they do not become measured neutral readings or clinical negatives.
2. `som_features.features_for_record` is the same writer for training and runtime.
   Training-only vocabulary and normalization are frozen with the artifact. Raw exact
   bank counts are retained beside the numerical training inputs. Study IDs, reports,
   independent answers and final ranking values are not predictor features.
3. Subject-domain specialists learn study-condition opinions from independently scoped
   labels. A study-level fracture label is not a localized lesion on every bone.
   Clinical-contract tissue roles determine each specialist's applicable questions.
4. Specialists train first; frozen-specialist opinions then train the orchestrator;
   joint refinement follows at one tenth the learning rate. Unknown targets have no
   loss. All views of one study stay in one split.
5. The NumPy-only runtime loads once in `run_squint_cli`. Within `infer_study`, the
   orchestrator orders existing observation requests, with mandatory requests first.
   It adds no request-skipping rule. After inference, `apply_navigation_record` emits
   twelve output values: warranted assigned findings serialize as 1, warranted defeated
   findings as 0, and only open findings use a graded numerical opinion. Original
   symbolic questions/values and raw model probabilities remain retained. Numerical
   opinions do not rename an anatomical object or overrule a warranted finding.

This first trainer uses masked binary cross entropy, AdamW, OneCycle scheduling and
trajectory/epoch stopping. These are numerical learning operations for the expressly
authorized layer, not fitted replacements for a thermometer-like lens or an anatomical law.
The current full-feature input makes training revision 2 contain 10,566,320 parameters despite narrow
hidden layers; do not describe it as a tiny parameter model without measuring it.

### Shared state and diagnostic scope

The conditions consume one evolving object state. When a bounded observation or
identity refresh changes a subject's profile, eligibility or identity context,
`infer_study` refreshes already-computed conditions whose declared objects or clinical
contract consume that subject. It recalls, combines and serializes those dependent
answers again. Unrelated answers and no-op readings keep their cached work; later
questions read the current state. A formerly assigned answer can become open after
its support is withheld. `condition_propagation` retains the changed subjects,
revisions and affected consumers. Newly open questions keep their requests; this
refresh does not itself launch another MRI pass.

Configuration authority requires actual defining tissue in the query comparison as
well as appropriately scoped precedent evidence. Supporting context alone cannot
decide the condition. A single unlocalized bone-positive presentation cannot become
a localized finding or a decisive whole-condition configuration. Independently
warranted whole-normal configuration recall retains its authorized ability to decide
absence. Numerical output supplies no new anatomical or clinical warrant.

## Compatibility after the quality pass

The immutable `train-r2` and `dataset-r2` paths above identify the original training
experiment. Ruff changed only the feature writer’s formatting, which changes its
byte fingerprint. Current runtime uses `navigation-r2-quality-r1`; future training
with the identical measured arrays uses `dataset-r2-quality-r1`, both under
`data/readings/som-navigation-20261022/`. The new metadata records old/new writer
identities and unchanged AST/weights. All118 predictions and routing arrays are
bit-identical; no training was rerun. Do not edit historical artifacts or disable
the writer-pin guard to load them. [Quality record](work/reviews/QUALITY_PASS_20261022.md).

The commands below select these compatible artifacts. Original optimizer checkpoints
remain source-bound; the checkpoint loader now refuses unsafe pickle state. A changed
trainer is not an authorized resume of an old pinned training run.

## Train on an already prepared, pinned dataset

Install the optional training dependencies with `uv sync --extra som-training` when
needed. PyTorch is a training dependency, not an offline inference dependency.

The completed current dataset is `data/readings/som-navigation-20261022/dataset-r2`.
To reproduce its training into a **new** directory:

```sh
PYTHONPATH=src .venv/bin/python scripts/train_som_navigation.py \
  --dataset data/readings/som-navigation-20261022/dataset-r2-quality-r1 \
  --output /tmp/knee-navigation-reproduction-r2 \
  --hidden 32 --context 8 --gate 16 --batch-size 16 \
  --epochs1 20 --epochs2 20 --epochs3 10 \
  --lr1 0.001 --lr2 0.001 --weight-decay 0.01 \
  --seed 20261022 --threads 4 --device cpu
```

Use `--resume` only on that trainer's matching checkpoint; changed data, schema or
configuration must not silently reuse it. The script's `--help` names the supported
settings. Do not overwrite completed experiments. The current run completed 20, 20
and 10 epochs. Stage 2 froze specialists; stage 3 changed specialists and gates at
maximum learning rate 0.0001. Default trajectory settings were `--pab-window 20`,
`--pab-patience 5`, `--max-no-improve 40` and `--pab-thresholds 0.015 0.01 0.008`.

For further data, `scripts/prepare_som_navigation.py` consumes saved real study
records and separately supplied teaching, pins their generating parents and fits the
feature vocabulary only on the training partition. Read its complete CLI contract
and the selected dataset's receipt before exporting another cohort. Old saved
inference does not become a run of newly edited
source, and a model's training studies are not made held out by excluding their
K-lines at inference time.

## Run the trained layer through the real entry point

The completed current artifact is `data/readings/som-navigation-20261022/train-r2`.
This is a supported command for a fresh local output directory, not a claim that the
current artifact has completed this check:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONPATH=src \
.venv/bin/python scripts/run_interiors.py \
  --split test --root data/raw --workers 4 \
  --diagnostic-mode infer \
  --diagnostic-memory data/readings/grounded-teaching-20261022/growth-batch-20/next-wave-run-r1/category-review-r3/published-learning-child-r1/memory \
  --diagnostic-navigation data/readings/som-navigation-20261022/navigation-r2-quality-r1 \
  --diagnostic-submission-template data/raw/sample_submission.csv \
  --diagnostic-output /tmp/knee-navigation-public-check-r2 \
  --squint-time-limit 300
```

The entry point refuses an existing output directory. Preserve the interrupted
58-study output: it is not a completed resumable cohort. A later current-source check
requires a fresh output and authorization to resume work. Read its final receipt and
actual coverage before calling it complete.
Without `--diagnostic-navigation`, the existing symbolic path remains selected.
The learned adapter currently refuses capacity/teaching modes rather than making
an unsupported whole-study-exclusion claim about trained weights.

## Runtime artifact and verification

Only `navigation.json`, `schema.json` and `weights.npz` belong in the offline runtime.
`training-checkpoint.pt`, optimizer state, dataset, labels and reports do not.
The runtime verifies artifact content, feature-writer identity, dimensions and
official label order. Invalid artifacts fail by named contract; a valid forward
operation's numerical failure retains original symbolic output with its named cause.
An unread, budget-stopped study never masquerades as a negative finding.

Focused checks:

```sh
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_som_features.py tests/test_som_navigation.py \
  tests/test_som_training.py tests/test_som_runtime.py \
  tests/test_squint_conditional_propagation.py
```

The experimental notebook records actual learning and per-condition validation.
The current 106/12 split is development evidence: validation selects retained epochs
and is not an untouched final test. No new hard diagnostic cutoff or competitive
performance claim follows from successful training, focused tests or a valid CSV.
There is no completed current full-CI or 58-study MRI result asserted here.

## Historical evidence and held packages

`dataset-r1` / `train-r1` used 48 training and 12 validation studies, 62,294 features
and 10,353,712 parameters. The three-public-study MRI smoke in `gemini-smoke-r1`
completed, but used the earlier incorrect readout that overwrote categorical findings
with numerical opinions. Preserve it as historical wiring/runtime evidence.

`categorical-readout-replay-r2` and `categorical-readout-replay-r3` replayed those three
saved observations with the corrected output boundary: 7 assigned values became
exact 1, 6 defeated values exact 0, and 23 open values retained their grades. These
are retained-observation replays, not fresh MRI runs or validation of `train-r2`.

Navigation packages r1/r2/r3 and their wrapper pins predate the latest source and
`train-r2`; they are stale and held. Historical verified bundle identities do not
authorize release of current source. No fresh package or remote run is queued.

## Formal submission boundary

Rohan explicitly forbids formal competition submission without fresh permission;
two shots remain. Earlier authorization for private notebook tests or dataset uploads
does not authorize formal submission. Writing `submission.csv`, saving a notebook
version or obtaining successful outputs does not grant that permission. This
wind-down launches none of those operations.

## Categorical output authority — corrected after the first smoke

`serialize_condition_value` is the shared final boundary for ordinary and learned
production, tagged `knee.warranted-endpoints-open-grade/v1` in study records, run
receipts and submission provenance. It maps existing `assigned`/`defeated` findings
to exact 1/0 and preserves an open graded reading. It does not decide a diagnosis
from a 0.5 threshold. If an open numerical reading saturates at 0 or 1, serialization
uses the adjacent interior floating-point number; the original reading is retained. This is a representation
boundary, not a medical cutoff or new warrant. Malformed findings and invalid numbers
refuse by named contract. First-smoke success proved wiring under the earlier wrong
readout and does not certify this correction; its verification is recorded separately.

Legacy `ranking.value` remains internal evidence. Navigation's `numerical_values`
retains raw model opinions; `readout_values` and `readout_sources` retain emitted
values and their authority. The model never supplies missing categorical warrant.
