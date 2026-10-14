# The remaining gaps, measured — 2026-10-12, the second half of the session

The record of `openspec/changes/every-stage-renders/tasks.md` §7, declared from the computed
inventory that morning under the founder's instruction and worked through the same day. Every
number here was computed by the command named beside it; nothing is recalled. The founder's go,
after the Codex re-review of the tree was read against the code: *"we have code, each of the
pieces of code is capable of doing useful things, I want this to be a coherent and functional
pipeline that works to perform the intended task as a single artifact (to the extent that it has
been built thus far)"*.

The first half of this work is the checkpoint commit `37c3934`; the second half is the commit this
record lands in. The chapter's earlier record of the day is `composition-repair-20261012.md`.

## 1. What the Codex re-review found, and what the code said

Four issues, each read against its enclosing unit whole before anything was declared
(`tasks.md` 7.12–7.14; the fourth was the known wiring gap of 7.1):

| issue | confirmed | repair |
|---|---|---|
| the slab lookup projected every place into the other acquisition's SELECTED slice frame while taking depth from the nearest slice, so one slice's in-plane origin stood for the stack | yes, in `bundles._slab_codes` | the in-plane test is made in the nearest slice's own frame (its stored origin, the shared basis); Chapter 1 measures `origin_spread_mm` beside `orientation_spread`; a must-not test with a displaced origin |
| the output reader accepted twelve rows of finding 0 as complete, and raised on a row without a reason or with a non-numeric index | yes, in `read_output` | a row reader that returns None for anything unreadable; complete is the twelve distinct indices; two must-not tests |
| ownership recorded `conversation.consumed_by.ownership` with the conversation off | yes, in `read_ownership_members` | the consumption rule in `specs/route-composition/spec.md`: a consumer records only for a record handed over; every consumer audited; a default-route composition test |
| the structural reader had only test callers | yes | wired into `run_study` at the one selected slice (`selected_slice`, now also the objects stage's rule), saved by the writer, drawn by the field drawer |

A fifth finding came from the gate after the slab twin landed: vulture listed the scalar
`slab_code` with no production caller, because the reference restated its arithmetic. The
reference now applies `slab_code` per place and the compiled twin is a second body pinned SAME to
it (7.15).

## 2. The instruments, before and after

Computed by the gate (`scripts/ci_local.sh`) and `just places` on the tree at each point.

| instrument | at the §7 declaration | at the checkpoint `37c3934` | at this record |
|---|---|---|---|
| tests | 760 passed | 871 passed, 4 skipped | 925 passed, 5 skipped |
| `just places`, unwired | 22 | 17 | 4 (the empty `beside` packages) |
| vulture, production scope | 24 lines | 10 | 4, the by-design four (§7, §9) |
| deptry | pandas, SimpleITK unused | the same | clean: both removed from the declared dependencies, `uv lock` removed SimpleITK from the lock (pandas stays as a transitive dependency of the development tools) |
| ty on `src` | 2 diagnostics | 0 | 0 (13 in tests, recorded) |
| LintGate | 8 blocking, 695 warnings | not run | 6 blocking, 919 warnings (§6), then 15 blocking, 894 warnings after the drawers packet (§7) |

## 3. Detective standings, per function, as the runs returned them

Every run's complete output is in `.detective/runs/` and its report in `.detective/reports/`; every
survivor was judged by the lead, and a flag carries its proof in the note. The call-form decorator
finding of the morning (`detective-call-form-decorator-20261012.md`) is confirmed: under the plain
`@contracted` the kernels converge.

| function | standing | survivors, judged |
|---|---|---|
| `count_by_extent` | Incomplete, 9/10 killed | the last is unresolved by the ENGINE: the authored `--input` run crashed in survivor classification (§4) |
| `footprint_labels_reference` | no certificate | the engine crashed in survivor classification on the first pass (§4) |
| `place_codes_reference` | COMPLETE 40/42, modulo 2 flagged, 6 crash-only | both flagged mutants rewrite a type annotation, which Python 3.14 evaluates lazily |
| `read_ownership` | COMPLETE 54/55 | the one unkilled is flagged (`np.unique(...).size` is a Python int); the rest were killable and are killed by two direct tests, one recording the ledger on both paths; six casts the first report offered as equivalent are load-bearing, because `np.count_nonzero` returns a NumPy integer (measured, numpy 2.5.3) |
| `slab_codes_reference` | COMPLETE 21/21, 4 crash-only | none |
| `stage_code` | COMPLETE 16/17 | the one flagged: a negative sentinel the absence vocabulary reads alike |
| `read_relations` | COMPLETE 37/45 on the new digest | eight flagged: six arguments `absence_code` never reads once construction is absent, two casts of values already Python ints; the dead `profiles` branch removed |
| `walk_indices` | COMPLETE 27/32, 7 crash-only | five flagged: an empty `linspace` at zero and the commutativity of `min` |
| `selected_slice` | COMPLETE 30/38, 3 crash-only | six flagged (two annotations, four range checks); a dropped int check was killable and is killed by a non-integer request; two STATE survivors print an EMPTY diff and are not judged (§4) |
| `report_code` | COMPLETE 13/13, 3 crash-only | none |
| `axis_code` | COMPLETE 26/26, 2 crash-only | none |
| `superior_code` | COMPLETE 23/24 | the one flagged: zero returns `unreadable` before the comparison; two moved edges were killable and are killed by small cosines |
| `structure_code` | COMPLETE 5/6 | the one flagged: a negative sentinel |
| `told_sign` | COMPLETE 9/10 | first 1/10, then 7/10 after a direct test, then 9/10 with the unhashable flag the test carries; the one left is listed, not judged equivalent |
| `histogram_valley`, `background_histogram` | no certificate | the engine crashed in survivor classification (§4) |
| `conversed_parses` | UNVERIFIED | the engine's own generated proof basis cannot be collected (§4), twice |
| `read_ownership_members`, `read_pairings`, `read_bundles`, `read_findings`, `read_output`, `submission_rows` | COMPLETE: 101/106, 12/12, 41/41, 63/67, 87/94, 25/25 | blocked twice by that generated file; run a third time with it removed, every survivor judged, 16 flagged with proofs, the rest killed by the ledger and must-not tests (§7) |
| `superior_end` | COMPLETE 27/29 | two annotation survivors flagged (§7) |

Standings recorded earlier today and unchanged: `absence_code`, `is_silence`, `ownership_code`,
`members_code`, `comparison_code`, `finding_code`, `output_code`, `pair_code`, `bank_status_code`
(`composition-repair-20261012.md`).

**An observation about the reports, to be reported to the Detective project.** On both
`read_ownership` and `read_relations` the FINAL kill count and the printed survivor list disagree:
`read_ownership` reports 54/55 killed and lists 16 candidate-equivalent survivors; `read_relations`
reports 37/45 and lists 14. The kill counts match the lead's judgement exactly (one and eight
provably equivalent), and the lists include mutants a routed test provably kills (`claims = True`
crashes `handed_on` on the real-field test; `ledger.record('', ...)` fails the ledger test). The
counts are taken as the measurement and the lists as stale classification. The same holds on the
six readers of the third batch after their re-convergence (§7): every listed survivor is one the
ledger tests kill by crash, while the counts rose by exactly what those tests target.

## 4. Engine defects, reported and never waived

Three distinct Detective defects, each with its run log in `.detective/runs/`:

1. **`classify_survivors` → `_captured_domain_variant_inputs` → `_domain_variants` calls
   `dataclasses.fields` on a captured input that is not a dataclass** (`engine.py:2701`,
   `TypeError: must be called with a dataclass type or instance`). Seen on
   `footprint_labels_reference`, `background_histogram`, and `count_by_extent` with an authored
   `--input`. These three therefore hold no certificate from today.
2. **`_guard_directed_inputs` uses a NumPy array as a set element** (`engine.py:2351`,
   `TypeError: cannot use 'tuple' as a set element (unhashable type: 'numpy.ndarray')`). Seen on
   `histogram_valley`.
3. **A generated test imports a private helper from a sibling test module by bare name**
   (`from test_ownership_claims import _Conversation` in
   `tests/detective/test_src_knee_ownership_claims_conversed_parses_*_synth.py`), which cannot
   import from the generated tests' folder. The file wrote zero tests, broke collection of the
   whole suite, and so made every later target of the batch UNGATEABLE (`collection_failed`).
   Removed twice; `conversed_parses` is left UNVERIFIED rather than converged against a broken
   proof basis.

Two further artefacts: two `selected_slice` survivors print an empty diff; and the survivor lists
of §3's observation.

## 5. CrossHair

`just crosshair` over the four modules with new contracts. Modules that import scikit-image trip
CrossHair's audit wall during type enumeration (`skimage.io` scans plugin files with `glob`); the
exact `--unblock` string it prints unblocks it, and `just crosshair <target> '--unblock=...'`
passes it through.

| contract | result |
|---|---|
| `selected_slice` post | Confirmed over all paths |
| `structure_code` posts, `superior_code` post | Confirmed over all paths |
| `output_code` posts | Confirmed over all paths |
| `submission_rows` post | **VIOLATED**: `OutputReading('written', '', (), Projection(0.0, '', ''), None)` came back as `('written', [])`. Repaired: a refusal is always a code of the stage, `invalid_count` for a code outside its vocabulary or a `present` reading without rows; a second post states it; the counterexample is a must-not test |
| `report_code`, `axis_code`, `told_sign`, `read_structure`, `read_output` posts | Not confirmed (neither a violation nor a pass) |
| `walk_indices` post | NO standing: its run stopped at pydicom's import-time audit wall (corrected in §7); `superior_end`, behind the same wall, passed it with the event-name unblock and is Not confirmed |

## 6. LintGate, second run

6 blocking (from 8), 919 warnings (from 695; the tree gained the structure unit, its tests, and
the generated Detective tests). The blockers:

- `StructurePanels` in `knee/pictures/collapse.py`: 24 attributes. It is the picture adapter's
  record of the structural reading, one field per saved value, and is recorded here as the
  design's record shape, as `RegimeKey` and `BoundaryExchange` were in the first run, not split
  for a style limit.
- `workbench/render/object_conversation.py::draw`: cyclomatic complexity 39. A renderer the
  drawers packet was editing when the run was taken; see §7.
- four `unresolved-import` findings on `matplotlib` in the same renderer: the stage contract
  supplies matplotlib per run (`uv run --with matplotlib`) and never installs it in the venv, so
  LintGate's resolver cannot see it. A deliberate conflict, recorded, not fixed.

The two complexity blockers of the first run are gone (`scripts/places.py::main` 32 → 3 and
`lenses/places.py::read_member` 31 → 7, behaviour unchanged, the receipt byte-identical), and the
writer's four `attr-defined` findings had one cause (one loop variable re-bound across two loops)
and are gone with the writer's decomposition.

## 7. The run, the composition, SAME, the drawers, and what the third batch returned

**The real run.** `just analyze-objects` on the demonstration study
(`1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149`; tile 3 mm, a 3 mm span at
13 samples along superior, prominence 3 mm, the conversation on), three times: on each backend
with pictures off, and on `jit` with pictures on
(`data/measurements/remaining-gaps-{reference,jit,drawn}-20261012`). Every time: five series
measured, no failures, the structural reading `present` on all five, and in the drawn run the
study record carries `origin_spread_mm` on all five, 0.0006 to 0.0008 mm. `just composition` on
each run: `composed`, no dangling producer, no phantom consumer, `conversation.produced` at ledger
index 47 before the first `ownership.produced` at 53; attendance `present` for study, collapse,
lenses, objects, ownership, vectors and predicates, `construction_absent` for relations and
`projection_undeclared` for output, the two declared absences. `objects.boundary_census` is listed
as a name in neither ledger vocabulary.

**SAME between the reference and the twin**, by `probe_same_through_plane.py` over the two
receipts: 204 through-plane banks compared and identical in status and rows; `slab_places`
identical per series (564,236; 519,312; 249,492; 360,856; 195,052 -- 1,888,948 in all, the
ledger's count of the kernel's evaluations); the structural codes and counts identical.

**The drawers.** The gallery index of the drawn run: 12 drawn, 0 not drawn, no route stage without
a drawer, and the corpus picture drawn once per run beside it (the writer's `draw_corpus`, which
records a drawer's returned refusal as `not_drawn` with its code). The four drawers the packet
touched were read whole by the lead before acceptance: `field_frames` (the structural row),
`study_frames` (the retained walk, the superior end), `bundle_frames` (the backend and the gap
fractions read, never defaulted), `object_conversation` (the unavailable plane listed with the
stage's saved code and the renderer's own refusal, `parted_more_by` from the picture adapter), and
the new `corpus_frames`. Each arranges saved values through `knee.pictures`, validates a saved
record against the stage's own vocabularies, names every silence, and computes nothing of its own
beyond display scaling and legend counts. Two adapters joined `knee.pictures`: `structure_panels`
and `SavedStructure` (the reading handed on unchanged, the saved form included) and
`superior_end`, a named code over `SUPERIOR_ENDS` from the two header codes, Detective-COMPLETE
27/29 modulo two annotation survivors flagged with their proof, CrossHair `Not confirmed`. The
lead's round-trip tests pin the drawers' readers: the writer's structural record comes back as
the stage returned it, present and silent alike, and a code the stage does not say, a dip outside
the profile or a tampered digest is refused by name; the corpus reader reconstitutes the stage's
own `CorpusShape` and refuses nine drifts by name.

What the pictures show, read by the lead on the drawn run. The field gallery, per series: the
squint's four maps placed by the saved bounds, the regime key reading by reading, the whole-series
histogram with the background split marked on it, the spread ratio beside the Gaussian line (two
series read one, three did not); then the structural row: the air in red, the leg closed with the
outside in blue, the squint inside the leg, its coverage, the profile along the header's axis with
its dip, the two basins and the seam, the darkest places and the ranked bodies, the air's own
histogram. On the axial series the profile, basins and seam panels name the stage's silence (the
axis runs along the stack normal), which is the drawing of an abstention and not a gap. The study
gallery marks the superior end on every plane. The corpus page, from the tables as the study stage
counted them when the corpus opened:

| count | value |
|---|---|
| training studies, series | 4,407; 24,371 |
| test studies, series | 3; 15 |
| labeled training studies; orphan series | 58; 0 |
| labeled studies carrying 4, 5, 6 distinct views | 16, 31, 11 |
| reports present, blank, not given | 4,407; 0; 0 (median 977 characters) |
| label codes per finding | the `1` and `0` counts per finding, 4,349 `not_given` on each |

**The third batch, judged and re-converged.** Every survivor was judged by the lead against the
whole function; the provable equivalents were flagged with their proof (18 flags, all accepted);
the rest were killed by two kinds of test the lead wrote: a ledger test per reader, which records
the exact event list under `recording()` -- the enabled ledger refuses an unnamed event, a count
that is not a whole number and a negative count, so the renamed, the tuple-valued, the negative
and the uncast NumPy counts all raise, and the None-handed paths show no consumption; and the
must-nots the survivors pointed at (a thirteenth row beside the twelve, a code outside the
predicates' vocabulary, a declared whole-number value written as a decimal, the why sentence of
the predicates, two members compared and the solitary member always first, a member holding no
places never compared, the disagreement mask read-only on the not-compared path).

| function | before | after | flagged, with the proof class |
|---|---|---|---|
| `told_sign` | 1/10 | 9/10 | none |
| `read_ownership_members` | 70/106 | 101/106 | 5: the shape clause implied by `readable_field` and `conversed_parses`; `compared` implies a second member; `comparison_code` symmetric in its sizes; two permutations equal over the reachable triples |
| `read_pairings` | 12/12 | 12/12 | none |
| `read_bundles` | 31/41 | 41/41 | none |
| `read_findings` | 38/67 | 63/67 | 4: a commutative `max`; `item_count` unread once `predecessor_returned` is False (twice); the default unobservable while `_one_finding` passes `form_given=False`, a premise that expires when a form is given |
| `read_output` | 61/94 | 87/94 | 7: an annotation under lazy evaluation; the `unmapped` clause implied by the index check (twice); `present` implies a projection by `output_code`'s post; `tuple` of a tuple; a negative sentinel the absence vocabulary reads alike (twice) |
| `submission_rows` | 25/25 | 25/25 | none |
| `superior_end` | -- | 27/29 | 2: annotations under lazy evaluation |

Every report still prints a survivor list, and on all six readers every listed entry is one the
new tests kill by crash or by value; the lists are stale against the final counts, which is the
observation of §3 now seen on six functions. None of those was flagged, because none is
equivalent. The reports also propose removing the lead's intent tests as redundant for kills and
lines; a generated suite is a characterization and the intent tests stay.

**CrossHair.** `superior_end`'s post is `Not confirmed` (neither a violation nor a pass). The
audit wall at pydicom's import-time scan of its example files (`pathlib.Path.rglob`) stops every
module behind `knee.study.series`; the exact `--unblock` string CrossHair prints stops at the next
file, and the event-name prefix `--unblock=pathlib.Path.rglob` is what passes it. A correction to
§5: `walk_indices` has NO CrossHair standing -- its run of 17:12 stopped at that same wall, read
whole this evening, so the `Not confirmed` recorded for it there was never measured.

**The instruments at this record**, computed by the gate (`gate-pre-3.log`): 925 tests passed, 5
skipped (the matplotlib-supplied ones and one platform float); ruff and the format check clean
over 352 files; the import contract kept; `just places` 97 declared, 83 wired, 4 unwired (the
empty `beside` packages `agencies`, `expert`, `memory`, `record`); the graph valid; deptry clean;
ty 13 diagnostics, every one in tests and every one a hand-built malformed argument the checker
rightly refuses; vulture's production scope 4 lines -- `signal_squared`, `READ_STANDINGS`,
`was_measured`, `KAGGLE_ROOT`, the four kept visible by design (§9) -- after `zero_share`,
`foreground_share` and `along_normal` joined the allowlist with their dynamic consumers named,
`SUPERIOR_ENDS` got its production consumer (the study drawer checks its words table against it
before drawing) and `pictures_dir` was removed with its reason (every drawer takes its output
from the joined pass and checks it against `PROJECT`). LintGate's third run: 15 blocking, 894
warnings -- `StructurePanels` at 24 attributes (the record's shape, as before),
`workbench/render/field_frames.py` at 1,236 lines with `saved_structure` at complexity 50,
`object_conversation.draw` at 41, and ten `matplotlib` imports its resolver cannot see (the
deliberate conflict of §6, now in four renderers). The decomposition of the two renderers is owed
under 7.7, with the round-trip tests as its behaviour pin.

## 8. What the builders reported that the lead did not do

- The bundles builder measured the slab twin on synthetic volumes of 898,880 places: the reference
  kernel 0.213 s, the compiled twin 0.0007 s, the old per-distinct scalar method 0.021 s where
  offsets repeat and 0.251 s where they do not; and it inferred, from 0.29 µs per unprofiled scalar
  call, that task 7.10's 2.75 s figure was inflated by cProfile. The twin's first call compiles in
  0.243 s into an empty Numba cache and loads in 0.079 s from a populated one; on a Kaggle kernel
  the cache directory must be writable or `njit(cache=True)` raises at the first call, and the
  stage would report that as a refused backend.
- The writer builder proved the decomposed writer's receipt byte-identical to the committed one on
  frozen sources, and found `--detective-report` raising `FileNotFoundError` on any use (it hashed
  a file commit `e0edfb1` deleted).
- Rule slips, reported by the builders themselves and recorded because the law is the founder's:
  the bundles builder ran `wc -l` once on its own two files; the writer builder ran `head -n 0`
  and `tail -n 0` once each as no-ops and piped one `git status` through `cat`; in its second
  packet it piped one full-suite run through `cat` and its lint command reformatted the
  conversation drawer while the drawers builder held it (formatting only, by the builder's own
  modification-time check).
- The second writer packet: the `--detective-report` flag reaches the moved module through its
  import and hashes its file; the receipt carries `root` and `split` beside the request (never
  inside it, since a reader rebuilds the request from that entry); the source digests key under
  the shared split-to-folder map. Its item 4 arranged the input that crashed the conversation
  drawer -- a saved slice index of None from a series with no stacked volume -- instead of
  refusing it: the saved silence sorts first and is listed with the stage's saved code and the
  renderer's own refusal `acquired_plane_unavailable`. The lead accepts that as arrangement, and
  the name stays. Its report, requested as a file after the post-compaction lock refused its
  messages, is `builder-writer-2-report.md` in the session scratchpad.
- The drawers builder's report arrived after the second half was committed (`25a2581`): it went
  idle under the same lock, and its files had been read whole instead (§7). Its own evidence: the
  render tests and the whole suite passing, `just imports` kept, and a 180-check adversarial
  probe of every new reader and refusal in the scratchpad. It left two defects, on the lead's
  instruction to change nothing further, both repaired after the commit: `saved_gap` in the bundle
  drawer lost its type narrowing to a ruff rewrite (three ty findings), now a `saved_number`
  reader that narrows; and the corpus label text joined a code and its count without a colon. Its
  third observation stands as the data: the test split's 3 studies and 15 series are invisible
  bars beside the training split's. It kept the existing readers raising on a tampered array or a
  word outside a stage's vocabulary, because the tests pin that, and made every new absence a
  named silence; the lead keeps both. It added no `DRAWINGS` entry for the corpus drawer, which
  takes a receipt and not a study, and asked which of two wirings was wanted; the writer call was
  the lead's answer. Its slips, self-reported: one inline interpreter call (to print a picture's
  pixel size), three line-window reads of files it had already read whole, and one shared scratch
  file of an earlier builder overwritten (`crop.py`). It names `tile_placement` and `saved_gap`
  as pure decisions it left unpinned; `superior_end` and `saved_shape` have the lead's tests and
  `superior_end` its certificate (§7).
- The writer's `origin_spread_mm` line was the lead's, once the series run carried the field,
  which the writer builder had correctly refused to add in `src`.

## 9. Open, after this record

- 7.1a: the per-view tabulations of the regime and geometry records are a corpus summary still
  owed when the one command runs without `--uid`; the table-only shape is saved and drawn.
- 7.2: `signal_squared`, `READ_STANDINGS` and `was_measured` stay visible in the gate by design
  (their consumer is the conjunction bank, which waits on the normalisation that is the
  founder's); `KAGGLE_ROOT` waits on DEPLOY. Those four are vulture's whole production scope.
- 7.5 (6.3a): the edge-to-piece translation is declared and not built.
- 7.6: the three engine crashes and the unverified parser `conversed_parses`; seven of the eight
  readers are COMPLETE.
- 7.7: the two renderers' decomposition (`field_frames.saved_structure`, complexity 50, in a
  1,236-line file; `object_conversation.draw`, 41) and the 894 warnings not yet triaged into this
  list or an allowlist.
- 7.8: thirteen ty diagnostics in tests remain, each a hand-built malformed argument the type
  checker rightly refuses; recorded, not silenced.
- 7.12: the prevalence of in-plane origin displacement over the 58 is measured by the corpus run,
  not yet taken; on the one study it is under a thousandth of a millimetre on every series.
- The ledger name `objects.boundary_census` is in neither composition vocabulary: a producer
  whose consumer the check cannot classify, to be named or declared.
- For the Detective project: the three engine defects of §4, the stale survivor lists of §3 and
  §7, and CrossHair's audit wall at pydicom's import, with the unblock that passes it.
- Codex's boundary statement stands: complete interstice extents, pairings under the conversed
  parses and the cross-acquisition conjunction remain unavailable, each declared.
