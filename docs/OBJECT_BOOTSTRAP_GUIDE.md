# Reviewed object bootstrap

The existing automatic catalogue supplies candidates. Visual review makes the starting identity
memory. Admit every correctly recognizable candidate: a rough border is acceptable for this
categorization task. A plausible location supports a call but never supplies an identity by itself.
The governing operation is [FULL_BUILD_PLAN §18](FULL_BUILD_PLAN.md#18-thin-object-bootstrap--rohans-execution-order-2026-10-21).
Live jobs and current results belong only to [the active packet](work/current/README.md).

The complete bootstrap, training and continuing classical-memory design is
[CLASSICAL_AI_BUILD_DESIGN.md](CLASSICAL_AI_BUILD_DESIGN.md). Read it before changing this path.
The commands below publish signed identity teaching: confirmed positive cases, ordinary negative
cases and alternative identities, each on exactly the views its call names. Corpus construction
enables learning and is not the whole agency-learning algorithm. K-lines remain active during runtime reasoning and procedure
selection. [The run guide](SQUINT_RUN_GUIDE.md#implementation-boundary-and-next-integration) names
the connected operation and remaining boundaries.

## Export actual images

From the repository's locked environment:

```sh
uv sync
.venv/bin/python scripts/squint_object_bootstrap.py export \
  --memory /absolute/existing/candidate-memory \
  --root /absolute/competition-root \
  --output /absolute/new/review-directory \
  --limit 12
```

Optional repeatable `--study-uid`, `--subject`, and `--case-id` filters select explicit candidates.
Selection uses stable IDs, not a score. `--limit` bounds a drawing batch; it is not a final seed quota.
Increase it to export the whole catalogue. No recognition pipeline is rerun.

The output contains `index.md`, one PNG sheet per object case, `review.json`, and `calls.json`.
Each sheet shows raw native images and the actual recorded teacher support with cropped context.
Magenta is the support; the yellow dashed box is a coarse tile window. The box never substitutes for
a support. Missing images, missing supports and their causes remain named. The product's recorded
digest is verified before its support is opened. One study is read at a time and its requested
slices/supports are shared across that study's sheets.

## Make real visual calls

Review the pictures and edit `calls.json`. Record the actual reviewer. An agent making the visual
call must identify itself; it must never attribute that call to Rohan. The generated file contains
an empty call list and the exact review-file digest:

```json
{
  "schema": "knee.object-identity-calls/v1",
  "review_sha256": "<exact digest supplied by export>",
  "reader": "<actual visual reviewer>",
  "calls": [
    {
      "candidate_id": "<exact candidate ID from index.md>",
      "call": "confirm",
      "notes": "<what in the pictured anatomy establishes this identity>"
    },
    {
      "candidate_id": "<candidate with a correct sagittal view and incorrect other views>",
      "call": "confirm",
      "notes": "<anatomical evidence in the selected view>",
      "views": [["Sagittal", "1", "1"]]
    },
    {
      "candidate_id": "<candidate whose pictured support is other tissue>",
      "call": "reject",
      "notes": "<what the support actually shows, e.g. posterior thigh soft tissue>"
    },
    {
      "candidate_id": "<candidate that is the object coronally and other tissue sagittally>",
      "call": "confirm",
      "notes": "<evidence for each view>",
      "views": [["Coronal", "0", "0"]],
      "negative_views": [["Sagittal", "1", "1"]]
    },
    {
      "candidate_id": "<a patella candidate whose sagittal support is plainly the femur>",
      "call": "reject",
      "notes": "<why the sagittal support is the femur>",
      "views": [["Sagittal", "1", "1"]],
      "also_positive": [{"identity": "femur", "views": [["Sagittal", "1", "1"]]}]
    }
  ]
}
```

Calls are `confirm`, `reject`, or `unsure`. Each call answers one question about the candidate,
"is the pictured support this proposed object?", on the views it names:

- `confirm` says yes (+1). The candidate becomes a positive case of its proposed object.
- `reject` says no (−1): the pictured support is other tissue. The candidate becomes an ordinary
  negative case of its proposed object: a real case on the "not this object" side, recalled like
  any other case. It is not a veto, and it says nothing about which other object the support is.
- `unsure` says nothing, and neither does leaving a candidate out. Neither is a negative.

A negative is the reviewer's own visual fact about this candidate. Never write one because a
confirmation is missing. Identity calls are not diagnostic calls: rejecting "femur" for a
candidate says nothing about a fracture.

Do not hold recognizable objects outside the seed because their outlines are imperfect. Make the
call view by view, and do not silently call an entire combined record when only some of its views
were found correct. Optional `views` lists exact triples in the order orientation, fluid
sensitivity and fat suppression, with the exact string values supplied by the review:

- On a confirm, `views` names the views that show the object. Omitting it asserts the whole case;
  it is not shorthand for whichever picture happened to look right.
- On a reject, `views` names the views whose support is other tissue. Omitting it rejects every
  view whose native support was drawn on the sheet.
- A confirm may also list `negative_views`: views of the same candidate whose support is other
  tissue. One candidate can be the object in one view and not the object in another.
- Any call may add `also_positive` when the support in some views is plainly another object the
  memory already names: a list of `{"identity": <that object>, "views": [...]}`. It writes a
  positive case of that other object on exactly those views, and nothing about any third object.
- Any call may name its own `reader` when it comes from a different reviewer than the file's.

Every listed triple must exist in the source profile and in a successfully drawn native-support
panel, and all pictured panels of that triple must support the call. A view carries one claim: it
cannot be both confirmed and rejected, nor two different objects. A confirm that lists
`negative_views` or `also_positive` must therefore list its confirmed `views` too.

### Adapting previously recorded signed calls

Calls recorded in an earlier format, or by several reviewers against the same review, are merged
into one calls file by `adapt`. It validates the merged file against the review before writing
`calls.json` and `adaptation.json` (each source file's digest and reader, and every recorded key that
is not part of a call, such as a montage number):

```sh
.venv/bin/python scripts/squint_object_bootstrap.py adapt \
  --review /absolute/existing/review-directory/review.json \
  --calls /absolute/existing/review-directory/calls-root.json \
  --jsonl /absolute/existing/recorded-calls.jsonl "<actual reviewer of those calls>" \
  --output /absolute/new/adapted-calls
```

It preserves the meaning of the original review:

- A reject's explicitly recorded `negative_views` becomes that reject's own `views`. It must not be
  dropped, because omission can widen the rejection to every drawn view.
- A confirm with negative facets retains its positive and negative scopes separately. An explicitly
  observed alternative identity is its own positive assertion, not a relabeling of the original full
  source record or a diagnosis.
- A view left unasserted stays unasserted. Recognizing one object jointly from available facets does
  not require each lossy view to recognize it independently, and does not certify unused facets.
- Retain the original calls, reader, notes, review/source pins and the adaptation provenance. Reject
  ambiguity rather than choosing a wider scope: a reject giving two different scopes, or a candidate
  called in two files, is refused by name. Each merged call names its own reader. The source files
  are only read.

## Publish an immutable seed

```sh
.venv/bin/python scripts/squint_object_bootstrap.py admit \
  --memory /absolute/existing/candidate-memory \
  --review /absolute/existing/review-directory/review.json \
  --calls /absolute/existing/review-directory/calls.json \
  --output /absolute/new/seed-memory
```

The wrapper hashes the exact final review bytes and checks the pictured sheet bytes. The shared
`knee.diagnosis.squint_bootstrap` API checks the source snapshot, candidate IDs, profile digests,
full-profile references and source-product identities. It refuses stale pins, malformed or duplicate
calls, an `also_positive` object the memory does not name, a view given two claims, unsafe paths
and overwrite, each by name. A call file that writes no identity case of either sign is refused as
`no_identity_cases_written`; negative-only teaching publishes.

Confirmed object cases enter the child memory's `cases`; diagnosis configuration cases do not.
Negative cases and `also_positive` cases are kept apart, in `object_identity_cases`, as whole source
case records. They never enter `cases`, so diagnosis recall never reads, for example, posterior thigh
tissue filed under "femur", and each record's condition calls stay with its own proposed object.
`object_identity_teaching` lists `confirmed_case_ids`, `negative_case_ids` with each one's
`negative_views`, and `alternative_positives`, beside every call kept verbatim. A reject whose sheet
drew no support view writes nothing and is listed in `negatives_not_written` with its reason.
Selected source cases remain intact, with cheap profiles and their portable full payloads and
interpretation contexts; positive and negative cases alike read back without the original H5. Scoped
calls restrict the seed banks allowed to teach identity; they do not rewrite or discard the original
record. An unreviewed view carries no identity assertion. Clinical labels and their scope are
preserved: confirming or rejecting an object's identity does not localize a study-level diagnosis to
it. The source catalogue is unchanged.

In identity recall, a positive case speaks for its object and a negative case against its object,
each only when a new profile resembles it more than it resembles the other side of the same
question. For a negative case that other side is the confirmed cases of its own object; until one
exists the negative stays silent, marked `no_compatible_opposing_case`. An object spoken for and
against is a conflict, not an answer. An object spoken against only is listed in
`opposed_identities` and cannot be identified. Held-out exclusion removes a study's negative and
`also_positive` cases exactly as it removes its positive ones.

## Read a new study through the production entry point

```sh
.venv/bin/python scripts/run_interiors.py --study-uid <UID> \
  --root /absolute/competition-root --workers 1 \
  --diagnostic-mode infer --diagnostic-memory /absolute/existing/seed-memory \
  --diagnostic-output /absolute/new/inference
```

The route is `run_interiors.py` → `run_squint_cli` → `infer_study`. Location uses current-study
anatomy. Anatomical contradictions are checked before candidate scoring, and conflicting structural
bones cannot silently place dependent objects. Unknown checks stay neutral when answering a question;
they do not establish anatomical support for automated new-case admission.

The study record's `identity_recall` compares observed cheap profiles with explicitly called seeds.
The proposed anatomical name does not choose its answer. All speaking identities are retained;
disagreement stays conflict. The exact existing count-space comparison is reused, and one preparation
is shared by ordinary studies and their object queries for the same immutable memory. A held-out
study has a separately prepared excluded view. A seed lacking the necessary opposing-case evidence remains
a proposal rather than acquiring invented confidence. The original full/cheap distinction remains.

Use the existing `--diagnostic-mode capacity` path for study-excluded evaluation, with the labels
required by that mode. The held-out study must leave both the scoring cases and opposing-case
comparisons. Neither inference nor this identity-evidence output automatically publishes another
memory. Recognition-based expansion publication remains a separate operation with preserved seed
lineage; do not confuse a recognition result with an already written case.

## Grow a recognition corpus, then train the active agencies

This is the approved operation to integrate, not a new runnable growth command:

1. Read candidates against one immutable parent with both positive and negative evidence present.
   Preserve whole-study exclusion and the actual jointly compared view scope.
2. Admit a new identity case only when identity is confidently established, applicable current-study
   anatomy affirmatively supports it and no known anatomical fact contradicts it. Unknown-only checks
   leave a proposal for later evidence. A partial bone plane can support the direction it actually
   constrains; missing directions do not invalidate that evidence or become invented constraints.
   An anatomical pass is a law check: it records where the candidate lies, never what tissue it is.
   Plausible but wrong tissue is the negative cases' job in joint recall, and the map's distances aim
   the search; they are not admission limits.
3. Publish a fresh child preserving signed cases, portable full/cheap evidence, source scope and
   lineage. The next round reads that complete child. No admission teaches another candidate in the
   same round.
4. Use independently established corrections at their actual scope immediately as ordinary teaching
   evidence. A wrong admission can additionally expose the memory's own near miss. A specialized
   censor requires a named significant difference tested against the recalled K-line's successes;
   neither counting changed banks nor finding two similar failures supplies that warrant by itself.

Visual inspection is useful for the first real growth demonstration and for independently correcting
failures: the first round's admissions are inspected before its child becomes the next parent, and
later rounds are spot-checked. It is not a permanent requirement that a person approve every future
recognition-derived case. Likewise, a rough useful support needs no contour-perfection exercise.

The corpus then supports classical learning through actual recognition, diagnostic and routing tasks.
Retain the cues, expectation, selected procedure, observations, sourced outcome and explanatory
difference needed by the relevant learning mechanism. Cases, scoped censors, K-line splits and useful
procedure links must be recalled by the decisions they serve. Do not stop at storing a name or call
this corpus-growth command the whole training algorithm. The precise mechanism and unresolved custom
policy belong in [CLASSICAL_AI_BUILD_DESIGN.md](CLASSICAL_AI_BUILD_DESIGN.md), not an invented
`train` command or a fitted similarity threshold in this guide.

## Verify the operation

Focused checks cover publication, offline full-profile readback, exact review/sheet pins, partial
calls, named anatomical states, exact recall and its real consumer. Run the normal integrated gate
before committing the final tree:

```sh
bash scripts/ci_local.sh
```

Passing software checks does not establish that an unseen teacher is correct. Inspect actual pictures;
admit the correct observations, including useful messy ones, and retain the scope of every call.
