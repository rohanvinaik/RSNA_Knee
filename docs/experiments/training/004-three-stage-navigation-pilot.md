# Experiment004 — three-stage learned navigation pilot

Recorded after training, 2026-10-22. This is parameter learning over fixed HDC signals,
separate from experiments001–003's signed-memory growth. The author explicitly selected
this mechanism; his words are in
[the navigation conversation](../../conversations/2026-10-22-three-stage-navigation-training.md).

## Intervention and population

The pilot uses60 completed fresh-study records generated under their actual frozen
`c037…` and `ef68…` memories. All-source teacher-population checks passed for each
actual generating parent. No teacher-bypass flag was used. Forty-eight whole studies
train and twelve validate, chosen by the fixed SHA256 ordering saved with the input
plan; no view crosses the split. Independent report calls supply378 known training
and82 known validation targets. Unknown/unmentioned or conflicting truth is masked.
This is not the fully labelled58-study teaching readback and not a60-patient fully
labelled cohort.

There are62,294 numerical inputs,16 specialist domains and10,353,712 trainable
parameters. The inputs retain12,000 typed HDC banks plus1,147 recall/law feature pairs;
exact raw counts are stored separately. Actual positive AND negative cosine channels
are nonzero for every condition. Feature vocabulary and normalization use training
studies only. No final ranking, gold label, report text or patient UID is an input.

The HDC writer, definitions, anatomy laws and signed memory are fixed. Specialist
domains/questions follow existing clinical roles. Their targets are study-condition
opinions, not invented lesion localization. This pilot demonstrates the authorized
numerical learner, not a newly established universal healthy-reference catalogue.

## Actual optimization

The real CLI exited0 in12.493 seconds. CPU used four threads.

| Stage | Epochs | Optimizer updates | Specialists changed | Orchestrator changed |
|---|---:|---:|---|---|
| 1 | 20 | 60 | True | False |
| 2 | 20 | 60 | False | True |
| 3 | 10 | 30 | True | True |

Stage2's specialists were byte-identical while the gate changed. Stage3 used one
tenth the maximum learning rate. All stages stopped at their declared epoch caps;
this is not evidence of convergence. Checkpoints, per-epoch histories and the source-
and dataset-bound launch receipt are retained. NumPy/Torch maximum absolute
prediction discrepancy was5.96e−8; trust-weight discrepancy was2.98e−7.

## Development validation

# Held-out fixed-HDC navigation pilot

These values describe the 12 validation studies, held out of gradient updates but used for PAB and best-epoch retention. They are not an untouched final test. No categorical cutoff or clinical assignment is introduced.

| Condition | Positive | Negative | Unknown | AUC | Correct / wrong / tied pairs |
|---|---:|---:|---:|---:|---:|
| ACL | 1 | 8 | 3 | 0.2500 | 2 / 6 / 0 |
| MCL | 1 | 8 | 3 | 0.7500 | 6 / 2 / 0 |
| Medial Meniscus | 5 | 4 | 3 | 0.7500 | 15 / 5 / 0 |
| Lateral Meniscus | 0 | 7 | 5 | unavailable_no_positive_truth | 0 / 0 / 0 |
| Medial OA | 5 | 4 | 3 | 0.8000 | 16 / 4 / 0 |
| Lateral OA | 3 | 4 | 5 | 0.6667 | 8 / 4 / 0 |
| PF OA | 5 | 4 | 3 | 0.5500 | 11 / 9 / 0 |
| Effusion | 5 | 4 | 3 | 0.3000 | 6 / 14 / 0 |
| Synovitis | 1 | 0 | 11 | unavailable_no_negative_truth | 0 / 0 / 0 |
| Baker's | 2 | 5 | 5 | 1.0000 | 10 / 0 / 0 |
| Contusion | 0 | 4 | 8 | unavailable_no_positive_truth | 0 / 0 / 0 |
| Fracture | 0 | 2 | 10 | unavailable_no_positive_truth | 0 / 0 / 0 |

The validation patients did not receive gradient updates, but their outcomes control
PAB and best-epoch retention. This is a development estimate, not an untouched final
test. ACL and effusion have poor ordering in this split; several other conditions
have favorable ordering on very few patients. There is no aggregate success claim.
Four AUCs are unavailable because one truth class is absent. No fitted categorical
cutoff was introduced; original symbolic categorical findings remain a separate
channel. These probability outputs do not establish clinical calibration.

## Artifacts, provenance and consumers

All paths below are relative to the project root:

- `data/readings/som-navigation-20261022/inputs-plan-r1.json`: source runs, teaching and split.
- `data/readings/som-navigation-20261022/dataset-r1/`: numerical data, exact counts, schema and receipt.
- `data/readings/som-navigation-20261022/dataset-feature-audit-r1.json`: actual both-side coverage.
- `data/readings/som-navigation-20261022/train-r1-launch.json`: exact command, source pins and measured duration.
- `data/readings/som-navigation-20261022/train-r1/`: three-file runtime artifact, history, checkpoint and receipt.
- `data/readings/som-navigation-20261022/validation-r1/`: all144 validation values, trust weights and condition-specific measurements.

- Dataset SHA256: `db605c1cd46c9376250b69e61a0f945a7b602d020f08ad2c16b5a994f1bd05fd`.
- Feature schema SHA256: `ce4bb3b093af937145c39a1fd8d790e32edb4c3026bb97fa604d62db561a8d53`.
- Model manifest SHA256: `4944e89cbf024d62e7d5f83fa1a9eb90baf0cc4b2a0fc5ca88a3e12e55d6d6c6`.
- Weights SHA256: `e1680e122632a5a78e7037483611c948618c826415c33c02406672a1adb92f24`.

Actual runtime consumers have been read in full: `run_squint_cli` loads the model
once, passes it into `infer_study`, and applies its values before saving evidence
and writing the official CSV. `infer_study` uses currently available measurements
to order existing requests, with mandatory work first. Original symbolic findings,
opposition and original values remain retained. Routing is presently an application
of the learned specialist gate, not supervised proof that its next-look ordering is
optimal. Final saved records train the pilot, whereas routing uses partial pre-look
records; independent action-utility validation remains necessary.

The root reran feature/model/trainer/runtime tests. No full final-tree gate is
claimed. Detective's scoped diagnose found nine unpinned behaviors in the contract-
index helper; its prescribed converge is running, not a completed certificate.

Gemini owns the independent three-public-study real-entry smoke; the native runtime
worker owns optional offline model packaging. Those are pending integration evidence,
not results of the12.5-second optimization run. Package no optimizer/checkpoint,
training reports or targets. Further measurements belong in dated addenda here.

## Supported conclusion and next comparison

The code now performs the author's three-stage parameter learning and exports a
matching NumPy runtime. This establishes a working training mechanism with mixed,
limited development discrimination. Next verify actual live feature/model consumers
on raw public studies, then the offline package. Grow independent teaching and replay
compatible saved signals for subsequent training; do not relabel repeated development
validation as fresh transfer or silently change the source of an old inference run.

## Addendum — isolated NumPy inference and focused verification

Actual model load: 0.244s. One already-prepared feature row: median 2.793ms, p95 4.093ms. Twelve sequential one-row calls: median 35.635ms, p95 42.394ms. Five warmups and twenty measured iterations, one native thread.

OS process lifetime peak RSS: 191.625MiB. Scope includes interpreter, imports, model and saved features, not MRI decoding, feature extraction or full-pipeline memory. The clean-subprocess guard loaded the real runtime and predicted with Torch imports forbidden; zero Torch imports occurred, and an explicit negative control verified the blocker. Raw timings and pins are in `data/readings/som-navigation-20261022/numpy-runtime-benchmark-r1/`.

Root reran all four feature/model/training/runtime test files: **39 passed in3.99s**. A first invocation named one nonexistent extra test path and collected no tests; the corrected explicit four-file invocation is the successful check. This is not the full CI gate. Separately, the runtime worker reports347 runtime/pipeline/packager/pin tests passed; final offline bundle verification remains pending.

## Addendum — actual raw-public-study smoke receipt

Root read Gemini's complete run receipt and official-schema CSV. The real entry point examined3 public studies with the accepted `ccd016…` memory and `4944e89c…` navigation artifact. All three report `navigation_outcome=applied`, the model loaded once, 27 question-level request-ordering receipts were retained, and zero full-anatomy runs occurred. No study exhausted its budget. Measured wall time: 85.064s; OS process peak RSS: 6.256GiB. The actual run used the default30,000-second budget, not the run guide's300-second check budget.

Submission SHA256: `63d4604ae73ac49402b7230561eadbfc75ef898114c2ab896a1caaaa3fb12422`; receipt SHA256: `daa2f2576dcd431890e78bdb4780cb92db91892e50a8705a6371a3d03ed42205`. These three unlabelled public studies establish live integration and output shape, not diagnostic accuracy or hidden-cohort timing. A separate saved-record audit will check exact numerical reproduction and retained symbolic evidence; it has not yet returned.

## Correction — first smoke passed an incomplete output contract

Rohan identified a serious semantic defect: the adapter emitted model floats even
when symbolic inference had a warranted categorical answer. Retaining that answer
only in evidence is insufficient. Root read `combine_condition` and `rank_condition`
whole: their existing assigned/defeated/open outcomes provide the categorical input;
the legacy banded ranking must not override final1/0. A shared serialization repair
is in flight for both the default and learned production paths. Raw model outputs
remain retained; no threshold or new clinical rule is introduced.

The trained weights and measured validation probabilities remain unchanged evidence
of learning. Gemini's original smoke and exact-probability replay remain valid wiring
measurements, not proof of conformance to the author's categorical output requirement.
Package navigation-r1 is withdrawn from release. Root interrupted its unfinished
private dataset upload and launched no notebook or competition submission. Further
verification must name the repaired source and new bundle, not relabel this first run.

## Addendum — categorical correction replay, actual retained public observations

The corrected adapter was applied to the same three complete saved study records, without MRI decoding or remeasurement. All36 outputs were checked: 7 assigned findings now serialize as exact1, 6 defeated findings as exact0, and 23 open findings keep their original raw model grades. Raw model opinions and complete symbolic/object/identity fields remain unchanged; original run files are immutable.

Receipt SHA256: `74829a517cb484e03a1cee367aac85727c7867ae7f0564c36ddd10077fed1a2f`. Corrected CSV SHA256: `a644463a4cf7c1e896d8bdf62caa94ac2d0e90fcfed57adeae25558bccfba11c`. Full per-question before/after checks and source pins are in `data/readings/som-navigation-20261022/categorical-readout-replay-r2/`. This is a readout replay, not a second raw-image run, a new diagnosis adjudication or accuracy validation.

The experiment reporters were also found to assume CSV equals the retained legacy internal rank. Their compatibility repair is being versioned so new categorical outputs are checked without weakening or rewriting historical runs. A fresh repaired offline bundle and private notebook validation remain pending. Formal submission requires Rohan's explicit permission.

## Addendum — actual reasoning repair and official58 training, r2

The first parameter pilot omitted the fully labelled58 teaching studies. Dataset-r2
adds their696 official answers as explicitly marked teaching data, preserving the
original60-study records and the same12 validation studies. Actual training completed
with106 train rows,1,074 known training targets and82 validation targets; stages
20/20/10 ran140/140/70 updates. Parameter count10,566,320. Stage2 changed the gate
while specialist bytes stayed fixed; stages1/3 changed specialists. NumPy/Torch
prediction discrepancy1.19e-7, trust discrepancy5.96e-8. No categorical cutoff was
fitted. Model manifest `ea487781d8b0653b3045f17ec7218137d0e9da699bc56e0a89e93e257353b39b`;
dataset `8bb3b45eaf0ef0d3dc505e3432b2c24cbc385034feb0bbb3af321fb9b347b1d4`.

Consumer tracing found an actual dependency defect: a later finer observation could
withdraw a femur while an earlier Contusion finding still serialized1. The repaired
coordinator refreshes only prior dependent questions from current profiles, identity
and eligibility. Controlled-producer tests run the actual coordinator/identity refresh/
clinical combiner/serializer in both directions;67 focused tests passed. This proves
the wiring correction, not clinical improvement. A separate demonstrated scope loophole
promoted the same unlocalized tibia measurements by wrapping them as a configuration.
Its repair is in review. The raw58-study check is prepared, not yet a measured result.

The accepted memory contains signed condition records from54 unique gold studies,
not all58; per-case counts cannot stand in for unique teaching coverage. Complete
findings and source pins: `gold58-data-plan-r1/` and `reasoning-repair-r1/` under the
som-navigation reading directory. The latter reproduces all9 previous validation
errors through real condition consumers. No claim that parameter training alone
corrects wrong evidence scope or stale shared-state reasoning is made.

## Closeout — author-requested wind-down, 2026-10-22

All three train-r2 stages completed before the pause. Saved teacher and development
validation replay are retained separately:

- [58 teaching rows](../../../data/readings/som-navigation-20261022/teacher-readback-r2/SUMMARY.md):
  raw numerical AUC0.994–1.000 per condition on GRADIENT-TRAINING examples.
  Existing saved categorical errors reduce the final mixed readout, particularly
  Effusion, Synovitis and Baker’s. These saved symbolic states predate the repair.
- [12 development-validation rows](../../../data/readings/som-navigation-20261022/validation-r2/SUMMARY.md):
  mixed per-condition results, four conditions without both truth signs. These
  studies inform epoch retention/PAB, so they are not an untouched final test.

The actual source-scope repair is complete: context-role banks no longer certify
defining-tissue coverage; a single unlocalized positive bone presentation keeps
its scope inside a configuration. One reproduced Contusion false positive becomes
open; eight other errors remain unchanged in the consumer replay. Root reran36
scope, conditional-propagation and analysis tests together: PASS. Worker311-contract
and67-dependency results overlap; do not sum them as unique tests.

The actual repaired58-study inference was interrupted at Rohan’s request, exit130.
Four complete12-question records were decoded and their SHA256 identities retained.
No complete cohort receipt or final58-study result exists. All134 production-source
pins stayed unchanged. The first launch was refused before reading images because
root pre-created its output directory for pins. Both attempts and the interruption
are preserved; default real-entry inference requires a fresh output directory.
[Interruption receipt](../../../data/readings/som-navigation-20261022/gold58-current-check-r2/root-interruption-receipt.json).

Detective’s scoped convergence of `condition_indices_for_subject` completed11/12
mutant kills with one undistinguished candidate-equivalent and four crash-only value
gaps. That bounded result is not a certificate for the whole pipeline or clinical
reasoning. The final-tree gate/cleanup remains deferred; no new commit/push was made.
The old train-r1 release bundle is stale after source/model updates. No new private
notebook or formal competition submission was launched.

No comparative superiority, complete clinical discrimination, full-cohort performance
or hidden-scale runtime claim follows from these results. The author paused further
building/training/deployment. Current artifacts and unfinished checks are in the sole
packet, revision168. Historical measurements and errors remain unchanged.
