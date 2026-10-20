# Diagnostic runs: setup, teaching, inference, readout and submission

This runbook describes the `knee.diagnosis` interfaces and their integration through
`scripts/run_interiors.py`. The mechanism is individual anatomical case memory: attributed
signed calls are joined to exact image descriptions; compatible cases can then speak on a
question. Cases are never averaged into a class prototype. Supplying the official submission
template enables the built-in symbolic/HDC readout; an explicit caller plugin can override it.
Without a template, inference retains evidence without producing a submission.
The governing design is [AI_DIAGNOSTIC_DESIGN.md](AI_DIAGNOSTIC_DESIGN.md), together
with the contracts in [FULL_BUILD_PLAN.md](FULL_BUILD_PLAN.md).
The master plan's current packet owns build status and acceptance results. This guide carries
operating contracts, not another live status ledger.

The diagnostic flags are registered on the existing runner. Confirm the flags on the exact
checkout with `.venv/bin/python scripts/run_interiors.py --help`.

## 1. Environment and inputs

Start each run by confirming the checkout, locked interpreter, competition root, source route, and fresh output paths. Then run the relevant teaching or inference command and inspect `receipt.json` before interpreting any result. The main outputs are: immutable case memory (`--diagnostic-memory` during teaching), `teaching-ledger.json` and `teaching-source.csv` for teaching, `sources/<uid>/` retained source evidence, `studies/<uid>.json` for question evidence and built-in readout details, `bank-sets.json` for referenced bank names, and `receipt.json` for run counts/work. Supplying `--diagnostic-submission-template` during infer/capacity also enables the built-in symbolic/HDC readout and creates `submission.csv` plus `submission-receipt.json`; adding `--diagnostic-readout module:callable` selects a caller plugin instead. With neither readout selection nor template, the run remains evidence-only.

Run from the repository root using its provisioned, locked Python environment. In an isolated
worker copy, the shared `.venv` supplies the interpreter only; imports must resolve to this
copy's `src`. Do not install this copy over another checkout's editable installation.

```sh
export PYTHONPATH="$PWD/src"
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMBA_NUM_THREADS=1
.venv/bin/python -c 'import knee.diagnosis.pipeline as p; print(p.__file__)'
.venv/bin/python scripts/run_interiors.py --help
export COMPETITION_ROOT="$PWD/data/raw"
export DIAGNOSTIC_RUN="$PWD/data/readings/diagnostic-seed-r1"
export DIAGNOSTIC_LABELS="$COMPETITION_ROOT/train.csv"
mkdir -p "$DIAGNOSTIC_RUN"
```

The printed module must be this checkout's `src/knee/diagnosis/pipeline.py`. Help must expose
the diagnostic flags. Use `--workers 1` for the reference recipes. The diagnostic loop
processes recipe studies serially; the anatomy runner's worker option does not parallelize
diagnostic recall.
Drawing is separate development work: omit `--draw` from every diagnostic command.

Three source routes exist at the diagnostic boundary:

| Route | Selection | Work and meaning |
|---|---|---|
| Retained reference products | `--diagnostic-products PATH` | Read already generated full object descriptions. Useful for teaching, reference recall and capacity inspection. It performs no fresh anatomy generation. |
| Acquired cheap observations | `--diagnostic-inputs PATH` | Read the study entries and explicit DICOM frame addresses in a `knee.diagnostic-inputs/v1` recipe; see §4. |
| Generated reference studies | `--study-uid`, `--labeled` or `--split`, with diagnostic mode and no products/inputs option | Generate full measurement and product encoding from the competition corpus; see Direct generated-reference source. |

Choose exactly one selection route. The parser's required mutually exclusive group enforces this. A retained-product directory is read at its top level: sorted
`*.h5` files take precedence; otherwise sorted `*.json.xz` files are used, excluding
`receipt.json.xz`. There is no recursive discovery or mixing of both formats. A single file
path is also accepted. Use dedicated directories containing only intended source products;
duplicate study identities are errors. The reference reader fixes `mode='full'`.

The diagnostic source options share the runner's required mutually exclusive selection
group with `--study-uid`, `--labeled` and `--split`. When using `--diagnostic-products` or
`--diagnostic-inputs`, do not also pass one of those study selectors. The acquired recipe
contains its own study UIDs and frame paths. `--root` supplies the competition corpus to the
anatomy runner; diagnostic dispatch happens before that corpus is opened, so it is not
needed by the acquired route.

If full reference products need generating, the existing anatomy path remains separate:

```sh
export COMPETITION_ROOT="$PWD/data/raw"
export REFERENCE_RUN="$PWD/data/readings/diagnostic-reference-r1"
.venv/bin/python scripts/run_interiors.py \
  --study-uid ACTUAL_TEACHING_STUDY_UID_1 ACTUAL_TEACHING_STUDY_UID_2 \
  --root "$COMPETITION_ROOT" --workers 1 --competition-output \
  --run "$REFERENCE_RUN/interiors" \
  --main-run "$REFERENCE_RUN/main-slices" \
  --encoding-run "$REFERENCE_RUN/products"
```

Replace the uppercase study placeholders with actual selected source study UIDs. Set
`COMPETITION_ROOT` to the actual competition mount if it is elsewhere; the ordinary corpus
loader expects the competition study/series CSVs and the corresponding series files there.
`--labeled` selects all fully labeled studies on disk; `--split test` selects the supplied
test split. Neither option is a requirement to run a cohort for the first seed test.
The three competition output roots must be fresh, disjoint and outside the input root.
`--competition-output` uses built-in encoding and retained self-contained H5 products;
it disallows drawing and an explicit `--encoding-spec`.

### Direct generated-reference source

With the runner integration that exposes diagnostic dispatch, omit both
`--diagnostic-products` and `--diagnostic-inputs` to ask the coordinator to generate one
full H5 product at a time from the ordinary competition corpus. Select studies with the
normal mutually exclusive `--study-uid`, `--labeled` or `--split` option and supply
`--root`. This route runs full anatomy measurement and exact product encoding; it is a
reference route, not the acquired cheap route.

For one explicitly selected study during teaching, the command shape is:

```sh
.venv/bin/python scripts/run_interiors.py \
  --study-uid ACTUAL_TEACHING_UID \
  --root "$COMPETITION_ROOT" --workers 1 \
  --diagnostic-mode teach \
  --diagnostic-labels "$DIAGNOSTIC_LABELS" \
  --diagnostic-memory "$DIAGNOSTIC_RUN/memory-generated-r1" \
  --diagnostic-revision generated-r1 \
  --diagnostic-output "$DIAGNOSTIC_RUN/teach-generated-r1"
```

The labels are used only for teaching; generated image profiles are the case evidence.
For competition inference the selector is typically `--split test`; `--root` points at the
mounted corpus. Generated studies run serially. The producer creates a per-study H5 inside a fresh scratch subdirectory, verifies its
complete retained arrays, and moves it to `<diagnostic-output>/objects/<uid>.h5`.
It then reads detached profiles and removes only the consumed reconstruction subdirectory
when iteration advances or closes. The diagnostic coordinator retains profile source
evidence before advancing. Keep the final H5, source evidence, encoder declaration/version
and receipts: count profiles alone cannot replace the complete pixel/value output. An optional
`--diagnostic-scratch` must name an existing directory. Without it, a fresh
`.generated-scratch` directory is created inside the new diagnostic output and removed
after the generated iteration closes.

The teaching CLI retains the exact supplied CSV bytes as
`<diagnostic-output>/teaching-source.csv`. Its `teaching-ledger.json` records the original
path, retained path and CSV byte hash. Calls use a separate `labels-sha256:...` identity
computed from the normalized label mapping; keep both identities in any external audit.
The CSV's exact columns, in order, are:

```text
StudyInstanceUID,Report,ACL,MCL,Medial Meniscus,Lateral Meniscus,Medial OA,Lateral OA,PF OA,Effusion,Synovitis,Baker's,Contusion,Fracture
```

`labels_from_csv` accepts only literal `1`, `0` or an empty cell for each condition. `1`
teaches +1; `0` teaches −1 on that condition; blank means no call. Duplicate UIDs, reordered
columns, invalid cells and malformed rows fail. `Report` is retained in the original source,
not interpreted by this reader and not returned in its label mapping. The teaching receipt's
`labels-sha256:...` hashes the normalized supplied label mapping, **not** the original CSV
bytes or report text. Retain both identities. The CLI teaches each study separately, so its
label-source hash covers the mapping supplied to that particular teaching call.

A study-level negative is condition-negative at `diagnosis/<condition>` scope, not a claim
that its whole object is healthy. A family-level fracture label is not a localized call on
every bone. Additional report/visual teaching requires a separately attributed independent
call at its actual scope; this CLI provides no report NLP or report-call import flag.
Inference consumes images/descriptions and fixed memory, never reports or evaluation labels.

### Explicit cohort selection

Optionally add both `--diagnostic-cohort PATH` and `--diagnostic-partition NAME` to
any diagnostic operation. The cohort is a caller-authored JSON declaration:

```json
{
  "schema": "knee.diagnostic-cohort/v1",
  "partitions": {
    "teaching": ["ACTUAL_TEACHING_UID"],
    "evaluation": ["ACTUAL_EVALUATION_UID"]
  },
  "disjoint_partitions": [["teaching", "evaluation"]],
  "source_groups": {}
}
```

Replace the placeholders with actual study UIDs. Partition names are opaque; the
command chooses no split, ratio, randomization or teaching policy. A partition is
nonempty and contains exact, unique UIDs. Only explicitly declared disjoint pairs
are checked for shared studies and known source groups. Supply `source_groups`
only for independent linkage actually known; an omitted group remains unknown.
A literal group named `unknown` is an ordinary identity, not missing metadata.

The selected studies run in declaration order. Missing or ambiguous requested UIDs
fail before profile construction or frame decoding. The retained-product route
reads structured identity metadata; filenames are not study identities. This
preflight opens product containers and their metadata, so it is not a claim of
zero I/O for excluded products. The acquired route selects recipe entries before
`read_slice`. Without these options, the existing source route is unchanged.

For example, append `--diagnostic-cohort "$DIAGNOSTIC_COHORT" --diagnostic-partition
teaching` to the teaching command below, after setting that variable to the actual
file. Supplying just one flag is an error. The receipt records the declaration's
resolved path, exact-byte SHA-256, chosen partition and selected UIDs. Explicit
source groups enter profile provenance and the existing capacity exclusion;
partition names and groups do not become image features or inferred split labels.

## 2. Retained-product teaching

Choose a new revision and new output paths for each published memory. For example, after
reference generation above:

```sh
export DIAGNOSTIC_RUN="$PWD/data/readings/diagnostic-seed-r1"
export DIAGNOSTIC_PRODUCTS="$REFERENCE_RUN/products"
export DIAGNOSTIC_LABELS="$COMPETITION_ROOT/train.csv"
mkdir -p "$DIAGNOSTIC_RUN"
```

Teach directly from the original CSV; the CLI retains its bytes before writing the ledger:

```sh
.venv/bin/python scripts/run_interiors.py \
  --diagnostic-mode teach \
  --diagnostic-products "$DIAGNOSTIC_PRODUCTS" \
  --diagnostic-labels "$DIAGNOSTIC_LABELS" \
  --diagnostic-memory "$DIAGNOSTIC_RUN/memory-r1" \
  --diagnostic-revision seed-r1 \
  --diagnostic-output "$DIAGNOSTIC_RUN/teach-r1" \
  --workers 1
```

Do not precreate `memory-r1` or `teach-r1`. Teaching requires source, labels, memory output,
a nonempty revision and a fresh diagnostic output directory. `--diagnostic-revision`
defaults to the empty string and therefore is not an implicit teaching revision.
The twelve question declarations are applied to each study's canonical object profiles;
composition preserves source roles as `object/<canonical-name>/<original-bank>`.
This combines objects within one case, never independent confirmed cases.

Inspect `teach-r1/teaching-ledger.json` and `teach-r1/receipt.json`, then validate the memory:

```sh
.venv/bin/python - <<'PY'
import os
from pathlib import Path
from knee.diagnosis.store import read_store
memory = read_store(Path(os.environ['DIAGNOSTIC_RUN']) / 'memory-r1')
print(memory.revision, len(memory.cases), len(memory.trust), len(memory.censors))
for case in memory.cases:
    print(case.case_id, case.study_uid, case.profile.subject,
          [(call.question, call.digit, call.source) for call in case.calls])
PY
```

The ledger's `coverage` field is `knee.diagnostic-coverage/v1`. It inventories
question cases by their actual profile subject and includes every canonical object.
`direct_question_calls` refers only to that object's own subject; the separate
`declared_role_case_ids` list is a question-role reference, not measured presence
or a taught healthy/diseased state. An empty bucket remains a gap. The run receipt's
`coverage` path points to this ledger; the index does not duplicate profile arrays.

The ledger distinguishes `signed_label`, `blank_label`, `not_asked`, `no_label_row`,
`missing_profile` and `silent_profile`. A blank or silent profile supplies no signed
precedent. Its zero ledger entry remains visible. Reports and recalled answers never
silently become teaching calls. The mechanical CLI does not verify that the seed set
contains a positive and negative usable image case for every question: inspect actual
coverage and missing banks before claiming that stage complete.

Memory publication is immutable. `write_store` publishes a new directory atomically and
refuses an existing target. A correction is a new revision beside the previous one;
teaching does not merge a prior directory automatically. The CLI creates a snapshot from
the current teaching inputs. Preserve earlier snapshots and ledgers, and explicitly
assemble the intended inputs for any replacement snapshot. Recall never writes memory.

### Explicit attributed case calls

`--diagnostic-cases PATH` is an optional teaching input for calls that have already been
independently authored and attributed to an exact profile. It does not infer calls from
labels, reports, or images; it does not create trust or censor records. Each row names the
exact study UID, exact `Profile.subject`, and one or more explicit question calls:

```json
{
  "schema": "knee.diagnostic-case-inputs/v1",
  "cases": [{
    "study_uid": "ACTUAL_TEACHING_UID",
    "subject": "acl",
    "calls": [{
      "question": "ACL",
      "digit": 1,
      "source": "retained independent adjudication record ID",
      "words": "optional attributed explanation"
    }]
  }]
}
```

`digit` is exactly `-1`, `0`, or `1`; signed calls require a speaking profile. Zero is an
explicit abstention and does not create a signed precedent. `source` must be nonempty, but
syntax validation does not prove that the source is independent or medically warranted.
The profile subject must resolve to exactly one canonical source profile or already composed
question profile for that study. An explicit `diagnosis/ACL` subject addresses that question's
composition; it does not silently substitute for a canonical object's subject. Duplicate
subject matches fail. Check the retained source and declarations for the exact subject. The declaration is retained byte-for-byte with its digest in `teaching-case-source.json`; the case receipt
records canonical case identities. Imported cases are combined into the teaching snapshot
alongside any label-derived question cases. Preserve the source record and evaluate its
authority separately. The CLI does not merge or reconcile contradictory authoring sources.

Example: add `--diagnostic-cases "$DIAGNOSTIC_CASES"` to a `teach` command above. With a
cohort declaration, every case study UID must belong to a declared partition; case rows
outside the selected partition are not silently treated as teaching examples.

## 3. Reference inference and same-study-excluded capacity

For reference inference on different retained full products:

```sh
export QUERY_PRODUCTS="$PWD/data/readings/diagnostic-query-reference-r1/products"
.venv/bin/python scripts/run_interiors.py \
  --diagnostic-mode infer \
  --diagnostic-products "$QUERY_PRODUCTS" \
  --diagnostic-memory "$DIAGNOSTIC_RUN/memory-r1" \
  --diagnostic-output "$DIAGNOSTIC_RUN/infer-reference-r1" \
  --workers 1
```

This is a full-description reference lookup. It is not a measurement of cheap acquired
inference. `infer` does **not** automatically exclude same-study cases. Use genuinely
separate query products; a stored case recalling itself is only a wiring demonstration.
Omit `--diagnostic-labels` in inference; the operation does not load it for `infer`.

Capacity mode uses independent labels only after recall, to assess each question:

```sh
.venv/bin/python scripts/run_interiors.py \
  --diagnostic-mode capacity \
  --diagnostic-products "$QUERY_PRODUCTS" \
  --diagnostic-memory "$DIAGNOSTIC_RUN/memory-r1" \
  --diagnostic-labels "$DIAGNOSTIC_LABELS" \
  --diagnostic-output "$DIAGNOSTIC_RUN/capacity-reference-r1" \
  --workers 1
```

For each query UID this calls `recall(..., exclude_study_uid=uid)`, excluding all matching
memory cases regardless of view or mode. The result records `same_study_excluded: true`
and the excluded case IDs. Where the query explicitly declares a `source_group`, capacity
also excludes cases with that same declared group, including different study UIDs. The
evidence names `excluded_source_group` and `source_group_excluded_case_ids`. No group is
inferred from a patient name, UID similarity or absent metadata. Retain declared
`split`/`source_group` metadata during teaching, and keep any additional known linkage
together when constructing evaluation inputs. Censors have no study UID field; any evaluation censors must also
be independently held out by their provenance before constructing the snapshot.

`receipt.json` contains `per_question` for the exact twelve condition IDs. For each labeled
query, `evaluation.assessment` is one of:

| Assessment | Meaning |
|---|---|
| `identified` | A warranted `present`/`absent` answer agrees with the independent binary label. |
| `wrong` | A warranted `present`/`absent` answer disagrees with it. |
| `proposed` | Nearest-case evidence is a proposal; it is not counted as identified. |
| `abstained` | Another named outcome leaves the condition unresolved. |
| `unlabeled` | The label is blank/missing; correctness was not assessed. |

Keep identified, abstained and wrong **per class**, with proposed and unlabeled shown
separately. The same counters also contain raw outcome counts, such as `present` and
`proposal`; do not add those to the assessment counts or studies will be counted twice.
Unwritten counter keys mean zero in that run. A successful command exit means the
operation completed, not that it identified any condition correctly.

## 4. Acquired cheap route

`--diagnostic-inputs` names a JSON recipe with schema `knee.diagnostic-inputs/v1`. The
recipe supplies its studies; its `encoding_spec` is either an embedded JSON declaration or
a path to one relative to the recipe file. `acquired_studies(args)` validates that spec
once, yields one `(study_uid, profiles, source_metadata)` tuple per declared study, and
decodes an explicitly addressed DICOM frame once per resolved path within that study.
The frame must be a readable 2D DICOM whose study and series UIDs match the declaration
and whose orientation, position and pixel spacing provide geometry.

Each observation names a canonical `object`, caller-authored nonempty `region`, frame
`path`, `series_uid`, nonnegative `slice_index`, and three-string `view`; `support_rc` is a
nonempty list of unique native `[row, column]` coordinates inside the frame. The adapter
uses that support as supplied and does not resolve an object boundary. The recipe root
also supplies an explicit `cheap/<version>` `mode`, a `producer` identity and ordered,
unique `dependencies`. No diagnosis label or report is an input to this route.

Every metric in the matching encoding-spec profile gets one observation binding. An
`acquired_signal` binding sends the stored DICOM pixel values and finite-value availability
through the existing exact encoder. An `unavailable` binding requires a caller reason and
uses the encoder's unread path; it stores no numeric placeholder and makes no normality
claim. Numeric references remain only in the supplied encoding spec. Missing references
retain `missing_reference` while measured values and availability remain in source
evidence.

When one object has multiple observations, the compiled count-layout identities must be
equal, each view must be unique, and each bank must name exactly one eligible view in
`view_distinguished_banks`. For each bank, the eligible view binds its metrics to
`acquired_signal`; every other view binds them to `unavailable` with a reason. This keeps
view contributions in distinct banks. Counts are added by the existing `add_counts`
operation. The adapter sorts observations canonically, namespaces provenance by
observation, and forms a region scope from the exact declared region scopes. It does not
combine same-named readings from multiple views into an unqualified marginal.

Acquisition-semantic identity binds the producer, mode, ordered dependencies, declared
bank/view/metric-source map and any complete region declaration, in addition to the
original reference-bound count layout.
With `view_distinguished_banks`, that map describes all declared views, including absent
ones; omitted views stay silent. Even a singleton observation must obey the declared
bank/view bindings. Changing study paths or pixel values does not change the measurement
contract; moving a reading to a different view does. Source evidence retains both the
measurement-contract ID and original count-layout ID.

For a procedure that permits partial views, supply optional recipe `region_scopes`, for
example `{"acl":["acl-sagittal-region","acl-coronal-region"]}`. It names the complete
logical scope of that procedure independently of which views are currently available.
Each observed object's region must occur in its nonempty, unique declared list. The
composed profile uses that complete scope; source evidence retains the actual observed
regions and addresses, and missing-view banks remain silent. Thus a two-view precedent
and one-view query can compare their common speaking banks without relabeling different
procedures as compatible. Without this field, scope follows observed regions and a
changed observed set can intentionally remain incompatible. Changing the complete
declaration changes encoding identity.

Here is a complete two-view recipe shape for one ACL object. Replace the uppercase
placeholders with actual DICOM paths, UIDs, and support coordinates before running it.
The empty reference lists deliberately do not provide a numeric MRI reference:

```json
{
  "schema": "knee.diagnostic-inputs/v1",
  "mode": "cheap/raw-plane-v1",
  "producer": "<actual procedure and version>",
  "dependencies": ["DICOM stored pixels", "explicit support coordinates"],
  "encoding_spec": {
    "version": "acl-raw-plane-v1",
    "storage": "npz_xz",
    "banks": [
      {"name": "sagittal_raw_signal", "facet": "acquired sagittal signal", "metrics": [{"name": "signal", "kind": "digit"}]},
      {"name": "coronal_raw_signal", "facet": "acquired coronal signal", "metrics": [{"name": "signal", "kind": "digit"}]}
    ],
    "profiles": [
      {"object": "acl", "provenance": "native", "kind": "reading", "support": "declared_region", "view": ["Sagittal", "0", "0"], "readings": [
        {"bank": "sagittal_raw_signal", "metric": "signal", "value": "acquired_plane", "available": "finite_pixels"},
        {"bank": "coronal_raw_signal", "metric": "signal", "value": "acquired_plane", "available": "finite_pixels"}
      ], "references": []},
      {"object": "acl", "provenance": "native", "kind": "reading", "support": "declared_region", "view": ["Coronal", "0", "0"], "readings": [
        {"bank": "sagittal_raw_signal", "metric": "signal", "value": "acquired_plane", "available": "finite_pixels"},
        {"bank": "coronal_raw_signal", "metric": "signal", "value": "acquired_plane", "available": "finite_pixels"}
      ], "references": []}
    ]
  },
  "view_distinguished_banks": {
    "sagittal_raw_signal": [["Sagittal", "0", "0"]],
    "coronal_raw_signal": [["Coronal", "0", "0"]]
  },
  "region_scopes": {"acl": ["acl-sagittal-region", "acl-coronal-region"]},
  "studies": [{
    "study_uid": "<actual StudyInstanceUID>",
    "observations": [
      {"object": "acl", "region": "acl-sagittal-region", "frame": {"path": "<sagittal-frame.dcm>", "series_uid": "<sagittal SeriesInstanceUID>", "slice_index": 0, "view": ["Sagittal", "0", "0"]}, "support_rc": [[10, 20], [10, 21]], "binding": [
        {"bank": "sagittal_raw_signal", "metric": "signal", "source": "acquired_signal"},
        {"bank": "coronal_raw_signal", "metric": "signal", "source": "unavailable", "reason": "coronal bank is not bound to this declared view"}
      ]},
      {"object": "acl", "region": "acl-coronal-region", "frame": {"path": "<coronal-frame.dcm>", "series_uid": "<coronal SeriesInstanceUID>", "slice_index": 0, "view": ["Coronal", "0", "0"]}, "support_rc": [[10, 20], [10, 21]], "binding": [
        {"bank": "sagittal_raw_signal", "metric": "signal", "source": "unavailable", "reason": "sagittal bank is not bound to this declared view"},
        {"bank": "coronal_raw_signal", "metric": "signal", "source": "acquired_signal"}
      ]}
    ]
  }]
}
```

The built-in MRI spec does not provide a numeric healthy reference for these raw signal
values. With `references: []`, the example preserves measured values but reports
`missing_reference`; it does not create diagnostic count rows from those values. A
question bank selector can name the resulting raw banks, but that alone does not make
them speak.

Question declarations are JSON overrides with schema `knee.diagnostic-questions/v1` and a
`questions` list. Each listed record supplies `question_id`, `objects`, and either exact
`banks` or `bank_prefixes`; `context_keys` is optional. The accepted condition IDs and
default canonical roles are:

| Question ID | Canonical object roles |
|---|---|
| `ACL` | `acl`, `femur`, `tibia`, `pcl` |
| `MCL` | `mcl`, `medial_meniscus`, `femur`, `tibia` |
| `Medial Meniscus` | `medial_meniscus`, `femur`, `tibia`, `joint` |
| `Lateral Meniscus` | `lateral_meniscus`, `femur`, `tibia`, `joint` |
| `Medial OA` | `femur`, `tibia`, `femoral_cartilage`, `tibial_cartilage`, `medial_meniscus`, `joint` |
| `Lateral OA` | `femur`, `tibia`, `femoral_cartilage`, `tibial_cartilage`, `lateral_meniscus`, `joint` |
| `PF OA` | `patella`, `femur`, `patellar_cartilage`, `trochlear_cartilage` |
| `Effusion` | `joint`, `joint_fluid`, `anterior_synovial_recess`, `joint_capsule`, `quadriceps_fat_pad`, `prefemoral_fat_pad` |
| `Synovitis` | `synovium`, `joint_fluid`, `joint`, `anterior_synovial_recess`, `joint_capsule` |
| `Baker's` | `gastrocnemius_semimembranosus_bursa`, `medial_gastrocnemius`, `semimembranosus`, `joint_capsule`, `joint` |
| `Contusion` | `femur`, `tibia`, `patella` |
| `Fracture` | `femur`, `tibia`, `patella`, `fibula` |

An ACL-only override for the two exact banks in the recipe is:

```json
{
  "schema": "knee.diagnostic-questions/v1",
  "questions": [{
    "question_id": "ACL",
    "objects": ["acl"],
    "banks": ["object/acl/sagittal_raw_signal", "object/acl/coronal_raw_signal"],
    "context_keys": []
  }]
}
```

The question file is a partial override: omitted IDs retain their default declarations.
Because this example recipe supplies only an `acl` object profile, the other eleven
questions have no matching source roles and are saved as `unresolved_missing_reading`.
That result comes from this example's source coverage, not from omitting those IDs in the
override. If the recipe supplies their roles, their outcomes depend on the compatible
memory and actual measured banks.

Run the acquired recipe without `--study-uid`, `--labeled`, `--split` or `--root`:

```sh
export DIAGNOSTIC_INPUTS="$DIAGNOSTIC_RUN/acl-raw-inputs.json"
export DIAGNOSTIC_QUESTIONS="$DIAGNOSTIC_RUN/acl-raw-question.json"
.venv/bin/python scripts/run_interiors.py \
  --diagnostic-mode infer \
  --diagnostic-inputs "$DIAGNOSTIC_INPUTS" \
  --diagnostic-questions "$DIAGNOSTIC_QUESTIONS" \
  --diagnostic-memory "$DIAGNOSTIC_RUN/compatible-acl-memory" \
  --diagnostic-output "$DIAGNOSTIC_RUN/infer-acquired-acl-r1" \
  --workers 1
```

Use `--diagnostic-mode teach` with independent `--diagnostic-labels`, a new memory path
and a nonempty `--diagnostic-revision` to teach from the recipe. Use `capacity` with an
independent evaluation CSV to exclude the query study UID. A query and its precedent must
share mode, scope, count layout, carrier, references and declared context keys; use the
same actual producer/spec/scopes for compatible cheap cases. `infer` does not exclude
same-study cases automatically.

For acquired **teaching** only, `--diagnostic-pair-products "$DIAGNOSTIC_PRODUCTS"` may
associate each cheap canonical object with its retained full description from the same
study. The coordinator prepares the product UID index once per run, then reads only the
matching study's full profiles. The retained source record contains `full_cheap_pairs`:
mode, scope, source identity, shared/missing banks, statuses and sparse exact counts for
both descriptions. Missing full objects are named. A pair records no diagnostic call
and performs no cross-mode cosine comparison. This flag is refused for inference,
capacity or retained-product teaching; full products are not a cheap-query dependency.

The acquired source record retains canonical object profiles and exact counts, per-view
addresses, geometry, support coordinates, source-file digests, measurement statuses,
decoded row names, measured values, availability and row codes. The diagnostic writer
publishes it before question composition at
`<diagnostic-output>/sources/<study_uid>/manifest.json.xz` and `arrays.npz`. The manifest is
standard lossless XZ around the same canonical JSON; the receipt names its actual file and hashes
its stored bytes. `load_source` also accepts earlier plain `manifest.json` files, a source directory,
or the logical `.json` path when the compressed sibling exists. The archive is
self-contained for those retained cue values; it does not include the entire DICOM frame
or serialize each later question-composite profile. `load_source` verifies the manifest,
archive and array digests, then returns dictionaries tagged with `$record_type`, not Python
dataclass instances. Keep the recipe and encoding spec with the result to reproduce the
same question composition. A later reference/layout can re-encode retained measured
values without repeating recognition, subject to the original producer actually having
retained those values.

## 5. Trust input and the boundary between proposal and decision

There is no default recall radius. Without sourced trust, comparable cases can yield
`proposal`; no nearest-case shortcut turns that into `present` or `absent`.
The optional `--diagnostic-trust PATH` reads this JSON envelope:

```json
{"schema":"knee.diagnostic-trust/v1","levels":[]}
```

An empty list installs no additional levels. Each populated `levels` object has:

| Field | Required meaning/type |
|---|---|
| `case_id` | Exact existing case ID from the published memory/teaching ledger. |
| `question` | Exact question ID for a call on that case. |
| `numerator` | Plain JSON integer; nonnegative and no greater than denominator. Boolean is invalid. |
| `denominator` | Plain JSON integer, strictly positive. Boolean is invalid. |
| `source` | Nonempty string identifying the retained independent justification. |

`numerator / denominator` is a cosine level, not a probability, vote weight or squared
cosine. The exact inclusive test is `denominator² × dot² >= numerator² × left_norm_sq ×
right_norm_sq`. Duplicate case/question entries, including an entry already stored in
the snapshot, fail; an overlay does not replace an existing level. The CLI requires an
existing case/call pair. The input's nonempty source string is syntactically validated;
it does not establish that its cited experiment warrants a medical decision.

The source must identify the independent justification, relevant condition,
comparison-bank/availability scope, compatible encoding, and teaching/reference provenance.
The current API is a sourced per-case cosine-level seam, not a requirement to perform a
new MRI null-distribution experiment before continuing the human's AI design. Clinical
definitions and independently labeled or adjudicated examples remain grounding inputs.
Chance resemblance to unrelated anatomy alone does not establish normal-versus-disease
discrimination within the same object.
Do not invent a universal level, copy a synthetic test fixture or adjust trust to remove
contradictory labels. The concrete MRI construction remains a separately accepted input.

Add `--diagnostic-trust "$DIAGNOSTIC_TRUST"` to a recipe only after setting that variable
to a file carrying the independently justified records. Teaching persists the levels in
the new snapshot; infer/capacity attach them in memory for that run without modifying the
published directory. Retain the overlay bytes and hash with the run for repeatability.
A changed overlay changes decision authority even when `memory_revision` stays equal.

Every eligible trusted reaching case speaks. A farther opposing case is not silenced
by a nearer supporting case. Opposite signs conflict unless an independently confirmed
near-miss censor vetoes its addressed interpretation. An ordinary condition-negative
case supplies negative evidence; it is not automatically a near-miss veto. The CLI has
no censor-teaching/import option; the frozen `Censor`/`Snapshot` Python API carries those
records with their separate independent source and rational level.

## 6. Records, retained values and readers

| Record/product | Writer → reader | Meaning and retention |
|---|---|---|
| `Profile` | Product adapter or cheap encoder; question composer → teaching/recall | Observed counts plus subject, mode, scope, source ID, context, bank statuses and provenance. Calls are separate. |
| `Question` / `QUESTIONS` | `declarations.py` → composer and bank selector/recall | Twelve exact condition IDs, `diagnosis/<ID>` subject, canonical object roles and selected measured-content facets. Acquisition/status/ID words are not injury evidence. |
| `Call`, `Case` | Independent teaching → store/recall | Signed question-specific digit, source and words; case ID, study UID, individual profile and teaching revision. A blank label produces no signed case; an explicit zero call is an abstention. |
| `Trust`, `Censor`, `Snapshot` | Explicit sourced construction / teaching → store/recall | Per-case/question authority; separate near-miss answer vetoes; fixed revision of individual cases. |
| `memory-r1/manifest.json` | `store.write_store` → `store.read_store` | `knee.diagnostic-store/v1`; memory schema `knee.diagnostic-memory/v1`, distinct count-layout declarations (bank names and row counts), profile metadata, cases/calls, trust/censors and digests. |
| `memory-r1/profiles.npz` | Store → store | `knee.diagnostic-counts/v2-sparse`; exact nonzero addressed counts as canonical decimal strings, profile offsets and bank/row indices. One complete layout table is shared by profiles naming the same layout. `allow_pickle=False`; no float approximation. |
| `teaching-ledger.json` | Teaching CLI → teaching review | Per-study source and independent-label ledger, including zero entries and reasons. It is not a report archive. |
| `teaching-source.csv` | Teaching/capacity CLI → provenance review | Exact supplied CSV/report bytes retained automatically; `teaching-ledger.json.label_source` records source path, retained path and byte hash. Each `Call.source` uses the separate normalized `labels-sha256:` identity. |
| `sources/<study_uid>/manifest.json` and `arrays.npz` | Diagnostic CLI → `evidence.load_source` | `knee.diagnostic-source-evidence/v1`; typed-map metadata, source arrays, profile counts and layout declarations, protected by manifest/archive/array digest checks. Acquired inputs retain measurements and addresses; product inputs retain a path/mode pointer, so keep the original product available. |
| `studies/<study_uid>.json` | Infer/capacity CLI → evidence review/readout caller | `knee.diagnostic-study/v1`; source receipt, memory revision, all question evidence and optional evaluation. Teaching instead writes `teaching-ledger.json`. `competition_readout` is `not_declared`, the built-in policy ID, or `caller_supplied`; built-in per-question `readout` details preserve support, missing-support flags, exact grade and source case IDs. |
| `bank-sets.json` | Infer/capacity CLI → evidence reader | Digest → complete ordered bank-name list. Expand `selected_banks` and `common_speaking_banks` references before interpreting comparisons. |
| `receipt.json` | Diagnostic CLI → run/capacity review | `knee.diagnostic-run/v1`; action, source route, study/case counts or per-question counters, and measured work. |

New stores use `metadata_encoding.schema: knee.diagnostic-metadata-string-table/v1`:
each exact metadata string and ordered key/value pair is written once per manifest,
with validated integer references from its consumers. The public reader restores the
original strings and shares repeated immutable values within that read; no global
cache is used. It also accepts the preceding direct-string manifest format. This
changes metadata storage, not snapshot meanings, count rows or teaching identities.
Use the public reader rather than treating an interned integer as a literal source ID.

`profiles_from_product(path, mode='full')` uses `open_product`, reconstructs immutable
counts from `object_composition`, and closes the source product before returning. One
canonical object's views/facets remain one object profile. Its
`object:<name>;composition:<fingerprint>` scope is accepted only when its provenance and
layout identity agree; explicit `region:<...>` input scopes are also accepted. Composition
retains each role's scope and status under that role's qualified banks. Object-specific
status/context is not forced to agree across roles; shared study/source identity and
question-declared context keys are checked across a composite.

The diagnostic store preserves exact counts and profile metadata, not original MRI arrays
or every raw reading. Its count layouts do not themselves contain the compiled mapping
from row addresses to metric/word names. Exact named decoding therefore also needs the
original compiled product/spec declaration and reference identity; a layout fingerprint
alone cannot reconstruct those names. Acquired source snapshots retain their actual measured values,
availability, row codes, addresses and source digests; full-product snapshots point to the
original product. Keep those source records and original H5/legacy products available
beside the memory. The acquired query source is written before question composition, so it
contains canonical object profiles and the inputs needed to reconstruct each composite,
not a serialized per-question composite profile. Retained values support re-encoding under
a new reference/layout when the producer saved the needed values.

Missing numeric MRI references remain `missing_reference`; the built-in declaration
does not supply a healthy quantitative atlas. Structural/qualitative banks can speak
where actually encoded. Neither a missing bank, an all-zero count bank nor an object
rule's refusal is a measured normal finding. A measured ternary-middle digit occupies a
real code row and must remain distinct from silence. Exact integer dot/norm triples use
only the common speaking selected banks; omitted banks contribute to neither norm.
Counts are exact under their retained carrier/layout, not evidence of a correct diagnosis.
Uniformly scaling all counts leaves cosine unchanged; pixel duplication does not encode
an extent distinction for recall.

Use `read_store` to validate the manifest/archive digests and complete layout rather
than reading only a plausible JSON header. Read integer evidence with an exact-integer
consumer such as Python's `json`; a JavaScript floating-point number may round large
integers. `manifest_sha256` is the canonical manifest hash with its own digest field
omitted, not the byte hash of the final manifest file. Record file-byte hashes separately.

`teach_from_labels` stamps case identities with `knee.diagnostic-case-sparse/v2` and its
teaching receipt with `knee.diagnostic-teaching/v1`. `prepare_snapshot(snapshot)` validates
the immutable cases once and retains their nonzero-bank activity facts in a run-local
prepared value; the CLI creates it once per infer/capacity operation and reuses it for all
queries. It is not a persisted or global cache. Exact counts remain attached to individual
profiles; case profiles are not summed into class rows.

Each question keeps `case_terms` and `censor_terms`, exact `dot`/`left_norm_sq`/
`right_norm_sq`, common speaking banks, trust/reaches flags, speaking/excluded/incompatible/
silent case IDs, nearest positive/negative IDs and coverage. Exact nearest ties retain
all tied IDs; a singular nearest-ID field is null when there is a tie. Nearest IDs are
proposals, not authority. The study JSON records this comparison evidence but
not a serialized per-question composite count bundle. Keep the retained query source and
the question/encoding declarations needed to reconstruct that bundle. For acquired input,
the source snapshot contains the exact per-object profiles and measured-value evidence;
for product input, the source record points to the original product and mode.

| `outcome` | `call` | Meaning |
|---|---:|---|
| `present` | +1 | Positive answer survives trusted concurrence/censors. |
| `absent` | −1 | Independently taught negative answer survives it. |
| `proposal` | 0 | Comparable precedent exists, but no surviving trusted answer speaks. |
| `unresolved_no_precedent` | 0 | No eligible signed precedent supplies the question. |
| `unresolved_conflict` | 0 | Opposing answers still speak. |
| `unresolved_missing_reading` | 0 | Compatible signed cases lack jointly speaking readings. |
| `incompatible_encoding` | 0 | Required subject/mode/scope/layout/reference/bank contract is incompatible. |
| `unresolved_censored` | 0 | A reaching near-miss veto prevents an answer. |
| `invalid_input` | 0 | Named input/record validation failure in recall. |

Without `--diagnostic-submission-template`, no probability readout or submission is
produced and `competition_readout` is `not_declared`. A template alone selects the built-in
symbolic/HDC policy in §7; an optional `--diagnostic-readout module:callable` overrides that
policy and must be paired with the template. The built-in graded values are a declared MVP
HDC confidence readout, not calibrated clinical risk. Silence, missing measurements, and
an unresolved symbolic decision remain distinct in the retained evidence. Do not interpret
a neutral grade as normal. A functioning case store is not by itself a demonstrated
diagnostic capacity result.

## 7. Probability readout and official template

The query path has three explicit modes:

| Arguments | Behavior |
|---|---|
| Neither `--diagnostic-submission-template` nor `--diagnostic-readout` | Evidence-only. Per-study decisions/evidence are retained; no probabilities or submission are emitted. |
| `--diagnostic-submission-template PATH` only | Use the built-in symbolic/HDC readout, then validate and write a submission against the template. |
| `--diagnostic-readout module:callable` plus `--diagnostic-submission-template PATH` | Use the caller-supplied readout plugin instead of the built-in policy, then write against the template. |

The template-only policy is `knee.diagnostic-readout/hdc-max-signed-squared-cosine-v1`.
These readout options are query-only: teaching rejects a submission template, and a plugin
cannot run without its template. The readout does not change symbolic recall decisions or trust. An already resolved
`present` call becomes exactly `1`; an already resolved `absent` call becomes exactly `0`.
For an uncertain outcome it examines compatible eligible signed `case_terms`, separately
for `call = +1` and `call = -1`. For each sign it takes the greatest exact squared cosine
from the eligible comparable case terms:

```text
u+ = max(dot² / (query_norm_sq * case_norm_sq)) over eligible positive case terms
u- = max(dot² / (query_norm_sq * case_norm_sq)) over eligible negative case terms
grade_exact = (1 + u+ - u-) / 2
```

The implementation compares and retains these rational values exactly with `Fraction`;
`grade_exact` is stored as a numerator and denominator string. A final float is used for
CSV serialization. If both signs have no eligible support, both support values are zero
and the grade is exactly `0.5`, meaning neutral because no signed support was available—not
normal. One-sided exact endpoints are moved to the nearest representable value strictly
inside `(0, 1)` with `nextafter`, so a graded uncertainty remains distinct from categorical
`present=1` and `absent=0`.

The per-sign `available` flag records whether eligible signed support actually exists; a
numeric zero used for an unavailable side is not evidence against that side. Recall reasons,
vetoed answers and censor IDs are retained. A vetoed sign contributes no support. A tie
at the maximum preserves all tied supporting case IDs but adds no votes; duplicate case
IDs in the evidence are rejected. Excluded, incompatible or silent case IDs cannot also
appear as terms. The readout accepts these uncertain symbolic outcomes: `unresolved_conflict`,
`unresolved_censored`, `proposal`, `unresolved_missing_reading`, `incompatible_encoding`,
and `unresolved_no_precedent`. `invalid_input` is rejected as malformed recall evidence.

For every question, the built-in policy stores its `policy_id`, symbolic outcome, readout
kind and reason under `studies/<uid>.json` → `readout`. Graded records also retain
positive/negative support numerator and denominator, per-sign availability, exact grade,
tied supporting case IDs, vetoed answers, censor IDs and recall reason. Symbolic records
retain their exact endpoint and do not fabricate graded support. The run receipt and submission receipt also identify the
policy. This is a declared MVP HDC confidence computed from the available symbolic evidence;
it is not a calibrated clinical posterior or patient risk. Do not map silence or missing
measurements to healthy, and do not call `0.5` normal.

A caller may override the built-in policy with an importable Python function specified as
`module:callable`. It receives the mapping from question ID to the full recall evidence
record, before evaluation-only fields are attached. It must return a mapping with exactly
the twelve condition names and finite numeric values in `[0, 1]`. Booleans, missing or extra
conditions, missing or extra study IDs, and nonfinite or out-of-range values fail. A plugin
requires the official template argument. Its source, calibration, and authority remain the
caller's responsibility; the run records the callable name but does not copy or hash the
module. Keep its exact source and hash with the outputs when repeatability matters. The
built-in policy is used whenever the template is supplied without a plugin.

The writer checks exact template study UID coverage and order, exact condition columns,
finite range-bounded probabilities, writes `submission.csv` atomically, then validates the
file again. `submission-receipt.json` records the template and output hashes, column list,
study count, readout source and memory revision. The per-study built-in readout details are
saved; the plugin's returned values are not copied into per-study question records. Readout
probability rows are accumulated until submission writing completes, so include that memory
in capacity accounting.

A competition run using the built-in policy needs only the official sample template:

```sh
export DIAGNOSTIC_RUN=/kaggle/working/diagnostics-r1
export SUBMISSION_TEMPLATE="$COMPETITION_ROOT/sample_submission.csv"
.venv/bin/python scripts/run_interiors.py \
  --split test --root "$COMPETITION_ROOT" --workers 1 \
  --diagnostic-mode infer \
  --diagnostic-memory "$DIAGNOSTIC_RUN/memory-r1" \
  --diagnostic-submission-template "$SUBMISSION_TEMPLATE" \
  --diagnostic-output "$DIAGNOSTIC_RUN/infer-test-r1"
cp "$DIAGNOSTIC_RUN/infer-test-r1/submission.csv" /kaggle/working/submission.csv
```

This generated-source example includes full anatomy measurement and encoding; it is not
the acquired cheap route. A raw acquired recipe can use the same template-only policy, but
the recipe UIDs must match all UIDs in the template. If running a subset, use a matching
subset template. The current test set and sample template are supplied at runtime; derive
the expected rows from those files instead of hard-coding the preview count. The official
sample template supplies columns and study IDs, not diagnostic evidence.

To use a reviewed plugin, add `--diagnostic-readout reviewed_readout:probabilities_for_study`
alongside the template argument. The competition run must use the mounted data source,
disable internet, stay within the competition-specific 9-hour CPU/GPU limit, and place the
final `submission.csv` at `/kaggle/working/submission.csv`. Current notebook documentation
records 4 CPU cores/30 GB RAM and 20 GB autosaved output at time of writing; session-only
scratch has no stated numeric quota. Treat the roughly 1,300 test-study figure as an estimate,
not a fixed row count. The binding source-backed limits and acceptance contract are in
[FULL_BUILD_PLAN §16.9](FULL_BUILD_PLAN.md#169-competition-resource-envelope-w8b-storage-closure-and-w10-verification).
See the official [code requirements](https://www.kaggle.com/competitions/rsna-knee-abnormality-detection/overview/code-requirements)
and [evaluation](https://www.kaggle.com/competitions/rsna-knee-abnormality-detection/overview/evaluation).

## 8. Compute, stage release and repeatability

For a retained reference run, `work.elapsed_seconds` covers diagnostic work after output
directory creation through preparation of the work receipt: reading products/labels or
memory, composition, teaching/recall and per-study publication. It excludes startup and
the final receipt write. `work.fresh_product_construction` is false on the retained route;
`work.previously_generated_product_read` is true. This excludes prior full anatomy generation. Add that earlier cost when reporting the full
reference workflow; never claim its avoided reconstruction cost as measured cheap speed.

`peak_rss_bytes` is the current process's lifetime high-water RSS, converted by platform;
it is not an incremental stage allocation measurement or a total of worker processes.
For retained-product and acquired-input routes, `full_anatomy_runs` is zero within this
operation. The generated-reference route measures and encodes one full study per yielded
item and reports those runs and producer time; include that work when comparing routes.
Memory is loaded once for infer/capacity. The diagnostic module has no targeted
measurement/fallback executor; unresolved questions remain unresolved. Any future explicit
full fallback must record its entire work and count it as fallback, not as cheap inference.

At study boundaries, the diagnostic loop releases its profile/composite/record references;
product readers close their file handles. Memory remains fixed for the run. Teaching
retains accumulated cases/ledgers until immutable publication; inference retains the
shared bank-set registry while publishing each study. Releasing Python references does
not guarantee immediate RSS reduction. Keep the complete chosen-route object outputs,
raw readings and required provenance; release only consumed intermediates whose retained
products have been verified. Do not run otherwise unnecessary anatomy to populate absent
full-output fields. Root must verify acquired-route decoding/release and any fallback
through the actual integrated runner.

For a repeat, keep identical source files, original CSV/report bytes, split/group choices,
procedure/spec and references, memory/overlay, revision, question declarations and source
hashes; choose another fresh diagnostic output directory, such as `capacity-reference-r1-repeat`.
Compare exact decisions, case IDs/terms, expanded bank sets, exclusions and assessments.
Elapsed time, RSS and path provenance can differ; compare those separately. Never overwrite
an earlier result to obtain a repeat. Teach again only to a new memory path. A failed run
can leave a diagnostic directory or even an already published memory before a later output
fails; retain that evidence and inspect it before choosing a fresh retry destination.

Assess the complete acquired operation against the master plan's source-backed offline
CPU/RAM/output/scratch limits and notebook cap. Include decoding, memory load, all fallback
work and output, and report the measured study count and actual coverage. Isolated cosine
benchmarks and previously completed anatomy cohorts establish neither integrated capacity
nor a hidden-test-scale guarantee. No 58-study diagnostic capacity is asserted by this guide.

## 9. Failures and release checks

At the Python boundary, `DiagnosticRunError`, `StoreError`, `ProductProfileError` and
`CompositionError` preserve named reasons. A diagnostic unresolved outcome is a saved
record, not a process failure. The CLI does not assign a separate numeric exit code to
each reason. Argparse normally returns 2 on invalid CLI syntax; an uncaught runtime error
normally returns 1. No custom exit-code map is defined.

| Reason or exception | Operator action |
|---|---|
| `diagnostic_missing_source`, `diagnostic_ambiguous_source`, `diagnostic_missing_memory`, `diagnostic_missing_labels` | Supply the required explicit inputs for the selected operation. |
| `diagnostic_output_required`, `diagnostic_teaching_revision_required` | Supply fresh output and a teaching revision where required. |
| `FileExistsError` for diagnostic output; `store_already_exists` | Keep prior outputs; use a new destination. |
| `diagnostic_product_source_missing`, `diagnostic_products_empty` | Point to the intended existing file or dedicated product directory. |
| `diagnostic_product_study_identity_missing_or_mixed`, `diagnostic_product_duplicate_study`, `diagnostic_duplicate_study` | Repair source selection/identity, retaining the failed evidence. |
| `diagnostic_drawing_is_separate_development_work` | Run the diagnostic command without `--draw`. |
| `invalid_train_columns`, `duplicate_study_uid`, `invalid_label`, `invalid_row_width`, `malformed_csv` | Check the original independent CSV and exact parser contract; do not coerce blanks. Some messages append line/UID details. |
| `diagnostic_trust_schema_unsupported`, `diagnostic_trust_levels_required`, `diagnostic_trust_record_invalid`, `diagnostic_trust_duplicate_case_question` | Repair the declaration against the actual case/call IDs and sourced rational contract. |
| `store_missing`, `manifest_missing`, `manifest_digest_mismatch`, `archive_missing`, `archive_digest_mismatch`, `invalid_encoding_metadata` | Restore/validate the complete immutable product. Never substitute an empty memory for corruption. |
| `layout_fingerprint_mismatch`, `count_layout_identity_mismatch:<object>`, `product_mode_mismatch:<source>:<requested>` | Use truly compatible source declarations/products; do not relabel identities. |
| `incompatible_scope_identity:<object>`, `incompatible_context:<key>`, `composition_layout_mismatch:<object>` | Use the matching source layouts and declared scopes/context; do not rewrite their identities. |
| `unresolved_missing_reading` in a question record | Inspect that question's declared roles and available measured banks. The result is saved evidence, not a normal call. |
| `diagnostic_case_document_invalid`, `diagnostic_case_record_shape_invalid`, `diagnostic_case_study_uid_not_in_cohort`, `diagnostic_case_study_uid_not_supplied` | Check the case JSON schema, exact profile subject and cohort/source UID coverage; preserve the authored source. |
| `diagnostic_readout_malformed`, `diagnostic_readout_import_failed`, `diagnostic_readout_callable_missing`, `diagnostic_readout_not_callable` | Make the `module:callable` importable in the locked interpreter and point to a callable attribute. |
| `diagnostic_readout_and_template_must_be_paired`, `diagnostic_readout_requires_query_mode`, `diagnostic_probability_readout_failed`, `diagnostic_probability_readout_invalid`, `diagnostic_probability_readout_details_invalid`, `diagnostic_probability_readout_unavailable` | Pair a plugin with an official template, use infer/capacity, and inspect the plugin result or built-in detail record. An unavailable callback names an internal wiring failure. |
| `template_columns_invalid`, `template_row_width_invalid`, `template_study_uid_duplicate`, `probability_type_invalid`, `probability_nonfinite`, `probability_out_of_range`, `probability_study_uid_missing`, `probability_condition_missing`, `probability_condition_extra`, `submission_study_uid_order_mismatch` | Use the current official template and provide one complete twelve-condition probability row for each exact template UID, with finite values from 0 through 1. |

The command contracts here do not declare a healthy quantitative MRI atlas, construct
independent trust declarations, or execute targeted full measurement fallback. The built-in
readout is an explicit MVP HDC confidence policy over recalled symbolic case evidence; it is
not calibrated clinical risk and does not turn missingness into normality. A caller plugin
can replace that policy but does not change the evidence contract. Mass training is a
separate operation over the declared case-store format; it does not change the per-case
sparse evidence contract.

## 10. Build the offline Kaggle bundle

`scripts/package_kaggle.py` ships the current `src/knee` Python files, the same
`scripts/run_interiors.py`, and the supplied immutable memory. It writes a dataset directory
and an offline notebook directory, with a content hash and every shipped file's digest.
It excludes study data, development files and credentials. The destination must be fresh and
outside the source, memory and optional wheelhouse trees.

For a working built-in readout run with the current memory:

```sh
.venv/bin/python scripts/package_kaggle.py build \
  --source-root "$PWD" \
  --memory-dir "$DIAGNOSTIC_RUN/memory-r1" \
  --output-dir /private/tmp/rsna-knee-kaggle-r1 \
  --dataset-id rohanvinaik/rsna-knee-mvp-bundle \
  --kernel-id rohanvinaik/rsna-knee-mvp-offline \
  --competition-source rsna-knee-abnormality-detection \
  --run-argv-json '["--split","test","--root","{input}/competitions/rsna-knee-abnormality-detection","--workers","1","--diagnostic-mode","infer","--diagnostic-memory","{memory}","--diagnostic-submission-template","{input}/competitions/rsna-knee-abnormality-detection/sample_submission.csv","--diagnostic-output","{working}/diagnostics-r1"]'
.venv/bin/python scripts/package_kaggle.py verify /private/tmp/rsna-knee-kaggle-r1
```

Change the owner/slug values to the intended Kaggle artifacts and confirm the actual competition
mount in the selected notebook. This example uses the built-in symbolic/HDC readout because it
supplies the official template and therefore produces a validated competition CSV. To use a
reviewed plugin instead, include its source in the production package or pass
`--runtime-script scripts/reviewed_readout.py` for an existing module, then add
`--diagnostic-readout reviewed_readout:probabilities_for_study` to the JSON argument list; keep
the template argument. The notebook copies the runner's validated CSV to
`/kaggle/working/submission.csv` only after successful execution. It never manufactures a fallback
CSV.

For a self-contained dependency closure, supply `--wheelhouse <Linux-wheel-directory>` and
`--requirements <frozen-requirements-file>`. Requirements must refer to that supplied closure;
installation uses `--no-index` and never downloads during the run. The existing
[offline runtime guide](../scripts/offline_runtime/README.md) describes the frozen production
`jit`/`hdc` dependency export and constrained Linux verification. Without a wheelhouse the package
explicitly reports that notebook-image dependencies have not been verified. Packaging checks the
memory's store envelope and copies it byte-for-byte; the public `read_store` reader must validate
its internal digests and exact payload before use. No Kaggle upload or execution is performed by
the package builder; `dataset/` and `kernel/` are the artifacts to inspect and upload separately.
