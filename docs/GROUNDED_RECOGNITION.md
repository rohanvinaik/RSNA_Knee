# Hand-build the corpus that bootstraps classical AI

For the connected Society of Mind training operation and the twelve-condition diagnostic endpoint,
read [CLASSICAL_AI_TRAINING_EXECUTION](CLASSICAL_AI_TRAINING_EXECUTION.md). It incorporates Rohan's
latest distinction between anatomical organization and physiological meaning, and the fact that
support, role and diagnosis are activities of ONE society rather than separate models.

Rohan's current task is to hand-build the corpus from the 58 labeled teaching studies: isolate
recognizable anatomical examples on their actual images, establish identity and independently
sourced normal/diagnosed meanings, and retain their measured bundles as K-lines. The existing
recognition tools help isolate examples; they are not required to solve recognition automatically
before the AI can be bootstrapped and trained. Useful rough supports and partial views suffice.
This is local work. A held-out score, deployment run or softer output band is not a substitute for
defining the objects and states the AI will discriminate.

The authored starting categories and native-image examples are in
[GROUNDED_TEACHING](GROUNDED_TEACHING.md). The sole current packet is
[work/current/README](work/current/README.md); it names the current memory, run and review state.
The procedure below is reusable; measured status lives in that packet and its linked receipts.

For the exact remaining implementation, use [TRAIN_READY_COMPLETION](TRAIN_READY_COMPLETION.md):
signed-label/clinical carry, contextual procedure applicability, action attribution, safe resumable
publication, addressed teaching residuals and the real learning-to-action launch check. Its command
template reuses this project's local round interface; it is not a new generic training framework.

## One memory, distinct evidence scopes

`scripts/grounded_recognition.py publish` extends the workset's pinned signed parent with its
reviewed regional presentations. It preserves every previous case, signed negative and
alternative, retained full profile, original configuration, and scoped identity call. Publication
uses the existing immutable `save_memory` and `prepare_recall` functions.

A question reference remains an ordinary speaking case, with its own measured support and
confirmed views. `question_reference` explicitly marks it as a regional presentation rather than
a second canonical whole object in the same knee. The configuration builder and recall preparer
both preserve the original object's configuration role. Unmarked duplicate objects remain
ambiguous; no arbitrary last-record-wins rule chooses one. The recall fingerprint includes this
role distinction, so preparations made before the distinction expire.

Adding a cartilage reference does not silently replace that study's whole cartilage case. Adding
a normal bursal-site presentation does not assert that an enlarged bursa exists. Existing
configurations are retained, not declared re-reviewed by this publication. Further canonical
object corrections use the existing correction/configuration rebuilding path.

Publication is a pinned operation, not a command to rerun against an old parent. For each
new reviewed workset, name the newest parent explicitly in that workset, then publish into
a fresh directory:

```sh
PYTHONPATH=src .venv/bin/python scripts/grounded_recognition.py publish \
  --workset path/to/new-reviewed-reference-cases.json \
  --output data/readings/grounded-teaching-20261022/integrated-next/memory
```

The default input is `references-r3/reference_cases.json`. A different parent requires a
new explicitly pinned workset; do not silently graft the old workset onto an unrelated tip.
Do not republish that initial workset after its child has already been extended. Use the
newest memory named by the active packet.

For an incremental question/view pair, use a partial teaching specification with a unique
`case_namespace` and the newest parent pin, then build and publish it together with its explicitly
linked configuration precedents:

```sh
PYTHONPATH=src .venv/bin/python scripts/grounded_teaching.py \
  --spec path/to/reviewed-pair.json --partial --output path/to/fresh-workset

PYTHONPATH=src .venv/bin/python scripts/grounded_recognition.py publish \
  --workset path/to/fresh-workset/reference_cases.json \
  --output path/to/fresh-child/memory --with-configurations
```

Partial means a subset of named condition questions, not relaxed source or review requirements.
Each pair still needs inspected normal/diagnosed native supports and independent opposite calls.
The same production configuration builder serves this route and the standalone configuration CLI.

`scripts/grounded_configurations.py` builds a question's configuration from its reviewed
reference, using only the object roles and views actually measured. Each configuration links
to those source cases explicitly; it never substitutes another same-name object from the
same study. These regional precedents coexist with the canonical study configuration.

Rohan's 2026-10-22 decision, recorded in the latest conversation, lets warranted **whole-normal
configuration recall** decide absence without separately normal findings at every site. The
comparison must include defining tissue. Context-only or unwarranted matches cannot decide,
and applicable contradictory findings remain conflicts. A local normal finding on its own
still cannot establish that all other sites are normal.

## Check installed teaching examples

```sh
PYTHONPATH=src .venv/bin/python scripts/grounded_recognition.py replay \
  --memory data/readings/grounded-teaching-20261022/integrated-r2/memory \
  --output data/readings/grounded-teaching-20261022/integrated-r2/replay-next.json
```

This asks ordinary recall against the complete installed signed population. It is teaching
replay: a self-match checks installation, encoding and opposing-case handling, not automatic
object location, diagnosis of every teaching study or recognition in another patient.

To check the same pictured references through the **real object/configuration recall and
condition combiner**, rather than stopping at object recall:

```sh
PYTHONPATH=src .venv/bin/python scripts/grounded_recognition.py replay \
  --memory data/readings/grounded-teaching-20261022/integrated-r2/memory \
  --output data/readings/grounded-teaching-20261022/integrated-r2/condition-capacity-next.json \
  --through-conditions
```

The supplied support has independent visual teaching. The expected normal/diagnosed answer
checks the result after inference; it is not supplied to the query. This tests the reference
operation, including configuration authority, without claiming automatic discovery of that
region. A self-match establishes installation and consumption, not transfer to another study.

## Run the actual image-to-answer path

```sh
PYTHONPATH=src .venv/bin/python scripts/run_interiors.py \
  --labeled --root data/raw --workers 2 --diagnostic-mode infer \
  --diagnostic-memory data/readings/grounded-teaching-20261022/integrated-r2/memory \
  --diagnostic-output data/readings/grounded-teaching-20261022/recognition-next \
  --squint-time-limit 7200
```

The existing entry point reads raw images, proposes regions through current-study anatomy,
constructs profiles, settles identity questions, recalls object states/configurations and records
condition answers. Official query labels and reports are never passed to inference. This is
teaching/development competence, intentionally allowing established teachers to remain in memory.
It is not a leave-one-study-out test. Keep any later transfer experiment separately named.

## Attach independent answers and inspect what the run actually read

```sh
PYTHONPATH=src .venv/bin/python scripts/grounded_recognition.py audit \
  --memory data/readings/grounded-teaching-20261022/integrated-r2/memory \
  --run data/readings/grounded-teaching-20261022/recognition-next \
  --output data/readings/grounded-teaching-20261022/ledger-next

PYTHONPATH=src .venv/bin/python -m scripts.grounded_review \
  --run data/readings/grounded-teaching-20261022/recognition-next \
  --output data/readings/grounded-teaching-20261022/pictures-next
```

The ledger has one record per labeled study: the independent report/labels, scoped reviewed
object cases, actual queried regions and identity outcomes, and identified/unresolved/wrong per
condition. Large evidence stays in the original run; the ledger links it instead of copying every
matrix. Lack of a reviewed teacher for a particular study/object is not proof of a missing object
or a requirement to annotate every structure before progressing.

The picture tool draws the first actual selected region for each of the twelve starting
questions. Other queried views remain in the inference record. Orange boxes show sampled places,
not asserted tissue boundaries. These sheets are **unreviewed proposals**, not new identity or
clinical calls. Do not promote them by their captions. Official labels may conflict with report
text; retain both and investigate the discrepancy rather than tuning a numerical rule to hide it.

For corpus construction, inspect candidate images beside the appropriate reviewed normal and
diagnosed references. An open automatic answer is not a prerequisite repair queue. Select useful
examples directly on the native image when the automatic proposal misses them. If investigating
an automatic result helps that teaching operation, distinguish these findings:

1. Wrong tissue or wrong site: correct location/support reasoning, keeping the actual scoped
   negative expertise. Re-reading the same wrong window more finely does not relocate it.
2. A valid unfamiliar presentation: add an independently reviewed case at its actual scope.
3. A distinction visible in the image but absent from the encoded measurements: identify the
   missing measurement by its anatomical meaning before implementing it.
4. A measured distinction not consumed: fix the real caller and pin both signs of its intent.
5. Conflicting or insufficient independent teaching: preserve the conflict or unknown; neither is
   a negative, and neither warrants an invented diagnosis.

When an actual consumer is repaired, check its affected inputs. Do not make repeated full-cohort
automatic runs a gate on hand-teaching. Study identifiers address teaching records; they are not
diagnostic image features. Teaching polygons annotate the selected examples and are not
new-patient locators. Label addressed teaching replay as such.

## Reuse measurements to isolate the remaining fault

When only the condition consumer or configurations changed, `scripts/grounded_replay.py`
can reuse an existing run's readings. Its default retained-query mode first requires identical
non-configuration cases and signed identity teaching, so a changed identity decision is never
silently reused.

```sh
PYTHONPATH=src .venv/bin/python scripts/grounded_replay.py \
  --run data/readings/grounded-teaching-20261022/recognition-r2 \
  --source-memory data/readings/grounded-teaching-20261022/integrated-r1/memory \
  --memory data/readings/grounded-teaching-20261022/integrated-r2/memory \
  --output data/readings/grounded-teaching-20261022/retained-query-next \
  --workers 2
```

That is retained-query replay: location, identity, measurement and additional looks are not
rerun. Add `--teacher-supports` with a different output directory to evaluate the reviewed
native teaching supports instead. The latter reads only confirmed views, with the reviewed
question reference where one exists. It does not claim to locate or name objects unaided.
It uses the current independently reviewed teaching inputs, so adding teaching does not require
pretending that an older automatic identity decision remains valid.
Attach independent labels with the same `audit` command. Keep these two modes separately
named: correct addressed recognition and automatic discovery answer different engineering
questions. Neither mode requires rereading the MRI volumes.

## The handoff to Society of Mind training

The target is a meaningful, visually grounded corpus that the ordinary memory and agency
consumers can read, with remaining ambiguities explicitly recorded. Save its measured bundles,
scoped calls and sources. Subsequent classical
training learns parameters/procedure memories that select useful cheap observations, route
questions, apply significant near-miss distinctions and reuse contextual evidence to reach those
established answers efficiently. Filling case buckets supplies that process; it is not the whole
learning algorithm. Do not invent gradient weights, a cosine cutoff, a capacity sweep or an
alternative objective in place of Rohan's custom design.

## Export object buckets and retained experiences

The official twelve-label row supplies the normal set as well as the condition presentations.
Once identity is confirmed, an object that none of the study's positive conditions implicates
belongs in its normal bucket. An unrelated injury does not disqualify it. A positive condition
that does implicate it supplies a condition presentation at that label's actual scope; a
study-wide fracture does not by itself localize a fracture to that bone. Missing labels do not
become normal calls. No separate normality annotation is required for unimplicated objects.

Use the newest published memory and its manifest digest from the current packet:

```sh
PYTHONPATH=src .venv/bin/python scripts/prepare_squint_training.py \
  --memory path/to/newest-published/memory \
  --memory-sha256 <manifest-sha256> \
  --run path/to/completed-raw-squint-run \
  --labels data/raw/train.csv \
  --output path/to/fresh-training-material
```

`--run` may be repeated for distinct completed runs. This command reuses saved readings; it
does not infer images again or modify the memory. Its fresh output directory contains:

- `object-buckets.json`: confirmed cases grouped by object and normal/condition/unlabelled state,
  with a per-condition index, their measured profiles restricted to confirmed identity views,
  original clinical scopes/full-profile references, and the unchanged signed teaching tables.
  Keep the pinned backing memory with the export so its retained payload references resolve.
- `procedure-experiences.jsonl`: the actual requests, context, actions, observed changes and
  independent outcomes available from those saved runs. An unverified outcome stays unchecked.
  Completing a measurement or changing a status is not itself evidence that a procedure helped.
- `receipt.json`: code, label-file, teaching-memory and inference-memory pins, source-record
  digests and the measured output counts. Labels supply teaching outcomes, never image features.

Retain existing scoped corrections and any actual recalled expectation separately:

```sh
PYTHONPATH=src .venv/bin/python scripts/near_miss_report.py \
  --memory path/to/newest-published/memory \
  --inference-root path/to/completed-raw-squint-run \
  --out path/to/fresh-correction-material --skip-survey
```

`--inference-root` may also be repeated. A catalogue proposal without a recorded recalled
precedent remains explicitly expectation-unavailable; the tool does not manufacture a
near-miss distinction or censor. These exports provide corpus and experience material for
the specified classical learning operations, not a substitute learning algorithm.

For independently reviewed identity-only additions, the existing measured-additions format can
be published through the ordinary source-tree command:

```sh
PYTHONPATH=src .venv/bin/python scripts/publish_visual_cases.py \
  --parent path/to/newest-published/memory \
  --parent-sha256 <manifest-sha256> \
  --additions path/to/reviewed-measured-additions.json \
  --output path/to/fresh-child/memory --prepare-recall
```

The publisher preserves the parent and signed scopes; it does not invent a full profile or
clinical call. Use this child's actual pin for the next publication and training export.

## Local round outputs

`prepare_squint_training.py --run-round` uses the interface in
[TRAIN_READY_COMPLETION §8](TRAIN_READY_COMPLETION.md#8-existing-commands-and-verification-order).
A completed round distinguishes `training/`, prepared against its frozen parent, from
`child-training/`, exported after publication against its actual child. The latter includes newly
supplied reviewed visual cases and their scoped clinical teaching. Its receipt and the round's
`child_training` field name the child's manifest pin. Use `child-training/` for post-round corpus work.

Resume with identical frozen inputs. Published children are preserved; changed signed content or
tampered exported material is refused. A changed code epoch requires a fresh round output root.
The command consumes supplied visual additions and retains attributed procedure experiences; the
existing identity growth/review/correction route is a distinct operation, not implicitly run by this flag.

## What completes this corpus-building step

The earlier version of this section incorrectly made automatic recognition across all 58 studies
a prerequisite for training. Rohan corrected that interpretation explicitly: **we are hand-building
the corpus**. Recognition here isolates individual anatomical objects, normal and diseased, so
their bundles can be assigned as K-lines and bootstrap the AI. This does not require a perfect or
complete pre-AI solution to recognition.

- Establish the anatomical identities and normal/altered meanings from actual images, anatomy,
  independent labels and reports. Keep useful rough supports; perfect borders are not required.
- Retain every warranted example with its actual image address, available views/scales, measured
  bundle, positive/negative/unknown meaning and independent source. A disease label keeps its
  actual scope; it does not mark every tissue in that study diseased.
- Use the reviewed normal/diagnosed categories to organize further examples, preserving meaningful
  variation and signed corrections. Do not impose an arbitrary seed quota or require every study
  and object to be automatically resolved before proceeding.
- Verify that publication preserves the cases and that the ordinary loader, recall and relevant
  agency consumers can use them. Addressed replay checks that wiring; it need not prove automatic
  location or generalization before the corpus can teach.
- The corpus supplies the specified Society of Mind training. It is not the entire learning
  algorithm. Automatic recognition, contextual discrimination and efficient procedure selection
  are capabilities the AI develops using this material, not a solved-system admission test for it.
