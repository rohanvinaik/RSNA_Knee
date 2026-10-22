# One society: grounding, completion contracts and scale-training execution

Written at Rohan's request on 2026-10-22, incorporating his complete mid-turn corrections.
This is the execution appendix to [CLASSICAL_AI_BUILD_DESIGN](CLASSICAL_AI_BUILD_DESIGN.md)
and [FULL_BUILD_PLAN §18](FULL_BUILD_PLAN.md#18-thin-object-bootstrap--rohans-execution-order-2026-10-21).
It is not another master plan or current-state queue. FULL_BUILD_PLAN §13 names the sole live packet.
The contracts here specify required behavior; a contract is not a claim that the behavior is built.

## 1. Read the actual request before doing anything

The latest literal requests and corrections are in the final sections of
[the squint/bootstrap conversation](conversations/2026-10-21-ternary-buckets-and-squint-orchestration.md).
They control this appendix. In particular:

> Well, these aren't different *societies*, they're different agencies/sets of "agencies" in the single model. Assignment of object pixels and assignment of role ID is inherently connected to diagnosis of conditions. Read the "anatomy map" document plus the one about structural diagnosis one(s) for some context

> Note also that anatomy--the physical location of objects--and physiology--how their physical presentation and anatomy inform function--are related but different. Hand-built "scan-calibrated" measurements are fine for a cheap estimation of literal physical relation, but objectivity and definitional correctness matter for purposivistic assignment of function

> Note also the whole POINT of all this--the Kaggle competition. We want to be able to diagnose scans from among the 12 options, with some degree of acceptable uncertainty if we can't confidently make an assignment.

**The objective is one functioning diagnostic system.** It takes a knee study, uses its observations,
anatomical organization and learned contextual experience to answer the twelve competition questions,
and retains uncertainty where a confident assignment is unwarranted. The twelve questions are not an
exclusive choice of one winning diagnosis; a study can have several conditions.

The question names are `ACL`, `MCL`, `Medial Meniscus`, `Lateral Meniscus`, `Medial OA`,
`Lateral OA`, `PF OA`, `Effusion`, `Synovitis`, `Baker's`, `Contusion` and `Fracture`.
Use `knee.study.tables.LABELS` and the official template at serialization; internal object/role
names do not replace those external fields.

Local bootstrap and training build that diagnostic capacity and its efficient orchestration. They are
not an unrelated corpus-management project. Equally, packaging a notebook is not evidence that the
society has learned. Earlier local-only instructions prevent deployment work from displacing training;
they do not remove the competition endpoint. Use the existing deployment contract when the trained
system is ready for that stage. This documentation task launches no remote run or submission.

## 2. Grounding route and source authority

Follow FULL_BUILD_PLAN §0. Read coherent units, and preserve actual authorship. The required units for
this work, in addition to the foundational conversation and theory, are:

1. The complete [exact-HDC conversation](conversations/2026-10-19-structural-information-and-exact-hdc.md),
   [AI conversation](conversations/2026-10-20-classical-ai-diagnostic-control.md) and latest
   [squint/bootstrap conversation](conversations/2026-10-21-ternary-buckets-and-squint-orchestration.md).
2. [CLASSICAL_AI_BUILD_DESIGN](CLASSICAL_AI_BUILD_DESIGN.md), especially §§4–11, and this appendix.
3. [RELATIVE_POSITION_MAP §0](RELATIVE_POSITION_MAP.md#0-the-understanding-authoritative-read-this-first),
   [ANATOMICAL_MAP_REFERENCE](ANATOMICAL_MAP_REFERENCE.md),
   [OBJECTS_AND_CONDITIONS](OBJECTS_AND_CONDITIONS.md),
   [DIAGNOSTIC_PAIR_PACKET](DIAGNOSTIC_PAIR_PACKET.md) and
   [AI_DIAGNOSTIC_DESIGN](AI_DIAGNOSTIC_DESIGN.md). Before changing an anatomical rule, also read the
   relevant complete definition in [RESOLVING_THE_PARTS](RESOLVING_THE_PARTS.md). Follow the existing
   anatomy-rule review, rather than inventing a selector from a score.
4. [HDC_ENCODING](HDC_ENCODING.md), [GROUNDED_RECOGNITION](GROUNDED_RECOGNITION.md) and
   [TRAIN_READY_COMPLETION](TRAIN_READY_COMPLETION.md). The earlier dated lane tables are evidence,
   not a command to restart their work.
5. The cell thesis, *What an \<Object> Is*: §§1.7, 1.12, 1.14–1.15, 7–9, 11 and14.1;
   `../cell_tracking/docs/K_LINES.md`; and the applicable complete sections of that project's
   `HDC_DESIGN.md` and `CLASSICAL_LAYERS_FOUNDER_WORDS.md`.
6. Rohan's `SIGNIFICANCE_WEIGHTING.md` and `law_as_architecture.md`, plus the related
   `SOM_TRAINING_ANALYSIS copy.md`, at the paths recorded in CLASSICAL_AI_BUILD_DESIGN §16 and the
   conversation. These inform the mechanism; they do not override the later knee specification.

The source papers have different running implementations. Law-as-architecture includes continuous
coefficient recall in geosteering; the older chess/legal notes include differentiable specialists,
losses and optimizers. Transport the justified principles: domain-shaped composition, contextual
memory, specialist responsibilities, staged teaching, saved-signal replay and residual-directed work.
Do not import their coefficients, network sizes, loss weights, gates or update equations into the knee.
The knee's currently specified learned records are individual cases, signed corrections, warranted
censors/splits and contextual procedure memories. Any additional custom trainable quantity needs its
named meaning and actual update operation, not an invented generic optimizer.

## 3. One society, one evolving account of this knee

The society shares one representation of the observed knee and its candidate objects. Its agencies
may propose support, assign anatomical roles, interpret functional state, discriminate diagnoses or
choose further observations. These are responsibilities within one model, not two societies, separate
encoders or independent classifiers whose scores are averaged at the end.

The shared object account retains:

- actual observed places and their uncertainty, including mixed coarse support;
- proposed and established identities/roles, with the evidence for each;
- current-study anatomical relations and their sources;
- available lenses, acquisition views, directions, scales and full/cheap profile links;
- signed interpretations of properties and conditions, with the meanings of their references;
- recalled precedents, counterevidence, unresolved alternatives and useful next questions.

These are information requirements for existing records, not a new universal object/episode format.
One object spans its available views. A missing view does not invalidate a useful observed one, and
three key planes do not become an invented filled volume.

The activities are coupled. Relationships help select support and assign a role; the object's
presentation helps interpret its state; a condition interpretation can explain a departure from the
expected presentation and direct a new look at the support or role. The coordinator must reconsider
affected questions when new observations change their premises. It must not require complete,
permanently frozen anatomical identification before allowing any diagnostic reasoning.

For example, femur and tibia may correctly resemble each other as bone. Their observed arrangement
assigns their roles. A damaged bone does not cease to be bone because its appearance departs from a
normal precedent. Preserve that identity evidence while interpreting the departure. A coarse territory
or proposed role still does not certify every sampled pixel as that tissue.

## 4. Anatomy, physiology and the meaning of a deviation

Anatomy supplies physical organization: location, course, attachment, containment, facing surfaces and
relative position. Physiology concerns what those structures do and how their organization and
presentation support that function. The two inform each other but are not interchangeable.

The map is a useful anatomical expectation carried into this study's actual geometry. It narrows the
next observation. The image supplies what is actually there. Map allowances are not admission limits,
and a normal expectation does not unconditionally reject an abnormal object.

Cheap scan-calibrated measurements remain valid tools for spatial and appearance estimation. Their
functional interpretation must be grounded in the object definition and anatomy/physiology, rather than
selected because a cohort score improved. A raw MRI middle is not a definition of health. Conversely,
the presence of a calibration in a cheap writer is not a reason to discard that writer or rebuild every
lens. Keep the measurement's role and the interpretation's warrant explicit.

Rohan's diagnostic examples state the intended directional meaning: a broken bone is deficient in
structural integrity relative to the normal object; inflammation is an object with excess in the
relevant presentation. These illustrate typed departures, not universal one-measurement diagnostic
rules. The actual combination that discriminates each condition is taught and read in its anatomical
and physiological context.

## 5. Balanced ternary: the question determines what the sign means

| Channel | −1 | 0 | +1 | Consumer |
|---|---|---|---|---|
| Named measured quantity | Below its declared reference | At/neutral to that reference | Above its declared reference | Compatible measurement/profile reader |
| Named structural or physiological departure | Deficit, diminished integrity, less of the named property | No significant departure/orthogonal on that axis | Excess, enlargement, more of the named property | Object-state and diagnostic reasoning |
| Signed call on an identity or condition question | Evidence against that proposition | Nothing asserted on that proposition | Evidence for that proposition | The corresponding scoped case memory |

An unread bank is represented by availability/silence, not by fabricating a measured zero. A missing
reference, uncertain identity and known normal property remain distinguishable. The same digit in two
typed channels need not assert the same fact. Reduced integrity can support a fracture interpretation;
it does not mean a negative call on the fracture question.

A normal object has a rich HDC description, not an all-zero vector. Raw signal polarity and healthy
functional reference have separate meanings. A structural/physiological interpretation may be supplied
by a grounded qualitative relation or recalled normal/altered pattern; it does not require an invented
universal numeric MRI threshold. Preserve reference identity, source, scope and available evidence.

Bundle only through the existing exact representation. Keep orthogonal bank meanings, compact counts,
view/scale compatibility and exact named differences. Opposite departures do not cancel into normality.
Keep individual cases; a class-average vector loses which observations co-occurred in each example.

## 6. What the agencies learn and what may teach them

| Responsibility | Question | Appropriate teaching | Learned effect that must reach a real consumer |
|---|---|---|---|
| Candidate/support/role resolution | Where could the object be, which support belongs to it, and what role does it occupy? | Reviewed images, actual current-study relationships, signed identity precedents; recognized additions retain derived lineage | Better contextual proposals/assignments and useful routes, with corrections opposing the appropriate interpretation |
| Object state and functional interpretation | How does this object depart from its normal organization or presentation? | Grounded normal/altered examples, appropriate observations and independently scoped clinical/visual interpretation | Contextual signed distinctions, with named evidence rather than unexplained similarity alone |
| Condition/configuration reasoning | Which of the twelve diagnoses do these objects and relations support? | Official labels, report statements and warranted reviewed findings at their real scope | Normal/condition precedents and role-qualified configurations acting through the clinical contracts |
| Observation/orchestration | Which available action can answer what remains open? | A recorded pre-action cue, the action's own result and the question's appropriate independent check | Contextual recruitment/ordering of useful work; justified avoidance only at its actual applicability |

This table does not require one class, network or process for every row. The agencies share findings
and HDC descriptions, and the relations determine composition. There is no global good/bad teaching
signal that can replace the individual questions' evidence boundaries.

K-lines have both roles: they make corpus construction possible and remain active memories of
interpretations and useful activity. Populating buckets is an enabling operation, not the whole
learning algorithm. Corrected negative cases teach immediately. A specialized censor/split needs the
thesis's significant named difference against the recalled K-line's successes. When the distinction
is not established, retain the ordinary correction without manufacturing a generalized veto.

## 7. Establish the teaching basis without demanding an already trained system

The 58 independently labelled studies supply the initial clinical distinctions. Use actual images
and retained products to isolate recognizable examples. Hand-selection is valid when the automatic
tool misses an object. Useful rough/partial supports suffice. Admit all warranted examples, not an
arbitrary quota, and retain exact positive, negative, alternative and unknown view scopes.

Correctly identified objects unimplicated by positive study conditions supply normal examples under
Rohan's rule. An unrelated injury does not invalidate them. Missing labels are not normal calls. A
study-level fracture/contusion positive does not localize injury to every bone. A localized diagnosis
can carry to other views of the same identity-established object; it cannot carry through a facet
known to be other tissue or still unasserted.

Normal and diagnosed configurations both speak under the same applicable evidence rules. Rohan
authorized warranted whole-condition recall and warranted whole-normal configuration recall to
decide. Their actual comparisons must include defining tissue; supporting context cannot impersonate
it. A local normal finding retains its proper force without becoming an all-sites negative. Hear both
sides and retain genuine disagreement.

Keep two checks distinct:

- Addressed teaching readback asks whether the hand-defined examples and clinical meanings reach the
  intended consumers. A failure is classified as missing teaching, unused teaching, incompatible
  scope/measurement, genuine contradiction or ambiguity. Repair that actual cause.
- Whole-study-excluded replay asks about transfer. It removes every relevant source and preparation
  from that study; its clinical target is joined only after image inference.

Do not force either check to agree by copying labels into features, weakening trust, dropping negatives
or tuning a scalar score. Do not make perfect automatic discovery on all 58 a prerequisite for useful
agency training. Continue filling genuine teaching gaps while the operational loop runs.

## 8. Remaining implementation contracts from the source review

These are acceptance tasks, not populated live jobs. The sole current packet assigns ownership and
records completion. The dated source basis is `33ff9c763ab7d55ec940bf3f6c74b758f1fc42a0`.
Recheck changed whole functions and their callers if that source moves.

### R1. Procedure opposition must share applicability and assert an actual contrary outcome

Producer/consumer: `squint_procedure_memory._empirical_opposition_floor` ->
`recall_procedure_experiences` -> `select_observation_requests` and
`squint_procedures.route_observation_request` -> `squint_pipeline.infer_study`.

At the reviewed source, the main recall loop checks request reason/location context, but the
opposition-floor calculation compares a wider set. It also treats a different outcome category as
opposition, including an attributed reading that leaves the question open.

The read-only synthetic reproduction used the existing `experience(direct=True)` fixture from
`tests/test_train_ready_repairs_intent.py`, the same compatible banks and an excluded second UID:

| Added experience | Actual reviewed behavior | Required intent |
|---|---|---|
| Successful attributed experience alone | `recalled_confirmed_resolution` | Keep working |
| Otherwise identical attributed experience ending open | `no_context_compatible_experience` | Open is not confirmed opposition to usefulness |
| Otherwise identical failed experience with a different request reason | `no_context_compatible_experience` | An inapplicable failure cannot define this precedent's opposition floor |

Apply the same observed applicability contract before building opposition. Preserve relevant actual
failures, clinical outcomes and unresolved records; do not introduce a score cutoff. Both-sign tests
must retain warranted success with neutral/inapplicable additions and prevent promotion when a truly
applicable contrary result leaves the usefulness unresolved. Unknown context does not automatically
establish either compatibility or contradiction; retain its actual scope. This does not make every
metadata field mandatory: partial observed context can suffice under the existing mechanism.

### R2. Attribute identity looks before learning their procedural usefulness

Producer: identity contest/refinement observations in `squint_pipeline` ->
`squint_procedure_memory._identity_rows` / `identity_state` -> procedure recall.

The reviewed condition-action path records a before cue and action-specific before/after state. The
identity-state path retains the coarse/joint result and final consumption but no `single_procedure`
attribution. `_row_category` therefore correctly treats its utility as unattributed.

Extend the actual producer/adapter with the action's own pre-action cue and result. Do not add a
certificate by setting an attribution string on a final aggregate result. A scoped visual identity
call still teaches identity independently of whether a procedure can be credited. Test an attributed
identity look against the appropriate independent identity call, an unresolved outcome, multiple
looks whose credit cannot be separated, and same-study exclusion. Demonstrate the actual consumer.

### R3. Replace the synthetic selector trace with a real next-study action trace

`scripts/record_learning_to_action_trace.py::generate_trace` at the reviewed source copies the
teacher's `confirmed_banks`, supplies another study UID and invokes recall/selection directly.
Its `other_tissue` request is a synthetic control. Preserve that result as selector wiring evidence,
but do not describe it as another patient's observed cue or executed `infer_study` transfer.

Required trace: a real teaching experience -> verified child -> another study's own pre-action
observations -> actual recalled IDs/context -> executed or justified avoided action through
`infer_study` -> resulting findings. Hold source, inputs and exclusions fixed between parent/child
comparisons. Include an incompatible-context control and self-study exclusion. If no stored episode
applies to the chosen study, report that and choose a justified demonstration; do not inject the
teacher's profile or loosen matching to manufacture transfer.

### R4. Finish source/input pinning before unattended scale rounds

`prepare_squint_training._code_identity` lists twelve files at the reviewed source. It omits actual
profile/anchor/collapse/decoding producers. `_study_pin_payload` does not identify raw study content;
the round pins a root path and UID list. An extraction can add files at that same path.

Reuse the existing broader source identity in `scripts/squint_training_round.py` and the actual
ready-study/extraction identities. Identify the participating producer closure, including retained
writer/reference identities and relevant environment identity. Do not rehash the whole SSD every
round: use verified per-study/source manifests. Refuse stale source, changed input, incomplete study,
modified record or changed signed child content with named codes. Identical completed inputs resume
without re-execution. A new code epoch uses a fresh output root.

### R5. Compose the existing operations into one executable training-round path

The existing commands have distinct responsibilities (§9). `prepare_squint_training --run-round`
does not call identity growth and currently iterates study inference serially. Running that publishing
command independently on three machines would create competing children, not one shared round.

Use one integrator and immutable worker observation outputs. The coordinator must reuse those outputs
for identity admission/review/correction, independent clinical teaching, configuration refresh and
procedure retention, then publish the complete child on the one accepted chain. Preserve the actual
generating parent of every observation. Reuse the existing functions and formats; add only the missing
adapter/coordinator glue, not another generic learner or distributed framework.

The integrator may compose changes before one publication or use existing publishers in explicit
successive immutable links. In the latter case, retain each observation's original generating parent,
do not rerun images merely to attach an experience, and promote only the complete reviewed tip to
the next inference round. Do not present sibling children as successive links.

Before claiming one coherent round, show that newly recognized examples and learned procedure
experiences both survive into the same loaded child and that the next round consumes them. A
documented manual recipe is honest interim operation; an export alone or a publishing flag that
omits growth is not the complete round. Resolve API/schema mismatches before dispatching large shards.

An automatic identity admission must retain recognition-derived lineage. Never pass it through a
direct-visual-teaching adapter and relabel it independent merely to make formats fit. An actual
reviewed visual correction has its own genuine reviewer and source.

### R6. Make physiological interpretation and the competition consumer visible

Do not rewrite the cheap polarity writer merely because its calibration is not a healthy reference.
Trace the actual object-state/condition consumer: what observations it reads, what normal/altered
precedents or sourced relations give those observations meaning, which named departures matter, and
how the result reaches the twelve findings. Measured scan-neutral, healthy neutral and unread must
stay distinguishable. Reuse existing representations and grounded teaching; no complete numerical
reference catalogue or perfect-boundary campaign is a new prerequisite.

Acceptance examples use actual normal/diagnosed pairs and the existing anatomical/clinical contracts.
Show object-qualified differences, the evidence linking them to a functional interpretation and its
diagnosis, and the uncertainty left open. Do not call an intensity-bin difference a physiological
deficit without that link, or claim a function from the proposed label's authored-definition bank.

### R7. Reconcile lineage and finish ordinary verification

The reviewed packet described a chain through `demo-round-r1-child`, but the fresh child directly
names the earlier 909-case parent. Preserve both immutable artifacts. Explicitly reconcile unique
teaching, designate the accepted tip and record the actual parent links; do not rewrite an old
manifest to invent a linear history or blindly duplicate the same experience under new run IDs.

The independent focused review reran 146 tests successfully at the reviewed source. That does not
certify all learning semantics or a full final-tree CI/Sonar gate. Pin the repaired pure decisions
with Detective's both-sign intent workflow, run appropriate integration tests and the normal final
gate after meaningful changes. Do not claim certification from a mutation-stage progress log.

## 9. Existing command boundaries

These names/flags were checked against the source CLI help during the review. Consult their complete
current definitions/run guides before use, and use the active packet's actual paths and digests.

| Existing route | Actual responsibility | Important boundary |
|---|---|---|
| `scripts/run_interiors.py --diagnostic-mode infer` | Actual study inference and its saved observation records | Shared squint/identity/condition consumer; raw query has no label input as features |
| `scripts/squint_object_bootstrap.py grow` | Warranted frozen-parent identity-growth decisions and optional child publication | `--parent`, `--inference`, `--output`, optional `--decisions-only`, `--labels`, `--held-out` |
| `scripts/squint_object_bootstrap.py export-admissions`, `admit`, `sheets` | Inspection and scoped correction of the admission decisions | Preserve actual signed view/question scope; use the command's current help |
| `scripts/publish_visual_cases.py` / `squint_visual_teaching` | Independently reviewed measured visual additions | Actual visual call and reviewer required; not a relabelling route for automatic admissions |
| `scripts/squint_training_round.py` | Teach source-backed report calls from saved observations, publish and optionally evaluate | This is a report-teaching operation, not every agency's learner |
| `scripts/prepare_squint_training.py --run …` | Export object buckets and experiences from saved runs without image inference | Repeated `--run` accepts separate completed run roots; keep generating-memory/source pins |
| `scripts/prepare_squint_training.py --run-round` | Local pinned inference, staged identity growth, reviewed continuation, clinical/configuration carry, procedure retention and child export | First admissions require actual review; this is not a parallel fleet coordinator |
| `scripts/check_squint_learning_transfer.py` | Real parent/child/action comparison, with a declared procedure-only child ablation and pinned raw study cues | A neutral recall annotation is not a changed action or demonstrated clinical benefit |
| `scripts/near_miss_report.py` | Retain actual corrections/expectations and named differences | No fabricated expectation, automatic censor or new chance rule |
| `scripts/replay_squint_findings.py` and existing recall APIs | Reconsider saved evidence under declared semantics | State exactly whether replay recombines findings or recomputes recall; neither silently relocates pixels |

`scripts/run_squint_admission.py` does not exist at the reviewed source. Do not copy the previous
packet's reference to it into another run guide.

A verified local round invocation, after choosing actual inputs, is:

```sh
PYTHONPATH=src .venv/bin/python scripts/prepare_squint_training.py \
  --run-round \
  --memory path/to/accepted-parent/memory \
  --memory-sha256 <actual-parent-manifest-sha256> \
  --root path/to/verified-ready-study-root \
  --source-archive path/to/competition-source.zip \
  --study-uids-file path/to/frozen-study-uids.txt \
  --labels data/raw/train.csv \
  --child-revision <new-revision> \
  --output path/to/fresh-round-root
```

The source ZIP's central directory supplies the selected studies' expected images; a partially
extracted directory does not certify itself complete. Only selected image bytes are checked, with
cached digests for unchanged files. Known AppleDouble sidecars are not image inputs. The ZIP defaults
to the root's sibling `.zip` when `--source-archive` is omitted. Source or study changes refuse stale
checkpoint reuse with named reasons.

When new identity admissions are staged, the command stops with
`identity_growth_admission_review_required`. The proposal memory is at
`<round-root>/growth/identity-growth/memory`. Use the existing `export-admissions` and `admit`
commands to inspect and call its candidates, then resume the SAME original frozen-parent command
with `--reviewed-growth-memory <reviewed-child>/memory`. Actual calls must cover the first round's
admissions; selecting candidates for a sheet is not a review. The final child extends that reviewed
continuation, while observations retain the parent that generated them. A zero-admission round can
still retain checked procedure experience and clinical teaching.

The default `--growth-review-mode first-round` requires that complete first inspection. After it,
use `--growth-review-mode spot-check` on subsequent rounds. Later rounds need not wait for a call on
every admission; supplied partial reviewed corrections still apply at their signed scopes. This
mode is an explicit operational choice retained in the round inputs and receipt, not an automatic
confidence threshold or a claim that unreviewed cases received independent confirmation.

This command's scope is the table above. Optional `--visual-additions` accepts its validated reviewed
format. It does not relabel recognition-derived candidates as independent calls or synthesize censors.
The command's `training/` is parent material; `child-training/` is exported against the published
child. Keep each receipt's true identity. Resume only with identical pinned inputs.

## 10. The training round, mechanically

1. **Choose the round's learning questions.** Use actual teaching gaps and observed residuals. The
   objective remains the twelve-condition diagnostic task. Select useful missing distinctions, not
   an arbitrary target number of cases, files or parameters.
2. **Freeze inputs.** Select the accepted parent, source/writer/reference identities, complete local
   studies, independent teaching sources and any fully excluded check studies. Give every worker the
   same parent identity and the applicable complete definitions.
3. **Shard independent observation work.** Each machine gets a disjoint set of study IDs and a bounded
   amount of ready data. Workers infer/read; they do not independently publish their own next parents.
   Check returned source, parent, study and record identities before integration.
4. **Resolve this knee jointly.** Read cheap shared information once, generate useful candidates,
   carry established relationships forward, hear signed cases and interpret object states/conditions.
   New evidence revises affected assignments. A settled question does not schedule needless work;
   an open question can request the available bounded observation that bears on it.
5. **Record experiences at the actual action.** Keep the pre-action cue and premises, the request,
   procedure, obtained information and action-specific result. Reusing a previous observation is
   different from obtaining a new one. Preserve failure causes and availability; do not turn an
   infrastructure failure into an anatomical or clinical negative.
6. **Join teaching afterward at its scope.** Reviewed identity calls, official condition rows and
   report statements teach their own questions. Preserve report negation, uncertainty, localization
   and source sentence. An unmentioned condition in a report is not an asserted absence. Recognized
   identity growth is authorized but retains its lineage rather than becoming an independent oracle.
7. **Admit/correct objects.** Automatic admission needs confident joint recognition, affirmative
   applicable anatomical support and no unresolved applicable contradiction. Partial useful geometry
   suffices; unknown-only anatomy leaves a proposal. Direct warranted visual teaching is independent.
   Inspect first-round admissions before promotion; later rounds use the agreed spot checks.
8. **Learn the actual distinctions.** Add warranted individual cases and scoped negatives. Read a
   confirmed failure against the precedent it recalled. Use a significant named difference for a
   justified censor/split; otherwise retain the correction without inventing a rule. Learn procedure
   usefulness only from attributed, applicable evidence checked against the appropriate outcome.
9. **Refresh dependencies.** Rebuild configurations for changed objects/views/clinical calls. Update
   compatible recall preparation. A corrected identity must change clinical evidence eligibility;
   a new memory entry that no decision consumes is unfinished.
10. **Publish the complete continuation.** One integrator owns publication, preserving every signed
    store, full/cheap link and source lineage. If existing publishers require intermediate children,
    keep their actual successive parent links and promote only the complete tip. Verify ordinary
    readback and export that child's own training material. New cases do not affect the inference
    round that produced them.
11. **Read the next step of learning.** Compare parent/child consequences on actual independent
    studies, with whole-study exclusions and stable source semantics. Report identified, abstained
    and wrong per question/context, the evidence that spoke, actions taken/avoided and useful work.
    Keep addressed teacher readback as a separate inventory.
12. **Continue from the accepted child.** Carry forward useful experience. Investigate recurring
    residuals with pictures and named differences; teach missing distinctions or refine the justified
    structure. A plateau calls for a concrete decision, not an automatic model-size sweep or a new
    threshold. Do not require the entire SSD corpus to be processed before the system is useful.

Each round directory must identify whether it is proposed, running, incomplete, stale, failed
verification or accepted. A source/input mismatch is not a negative training example. A completed
checkpoint remains reusable without silently treating changed raw inputs as the old study.

## 11. What scale changes, and what it does not

The same learning operation runs on more studies; scale does not change what counts as evidence.
Use the actual available machines and paths recorded in the current packet/SquishOS, not historical
host assumptions. Transfer ready shards with source identities, bound concurrent decoders/native
threads and pending work, and release each study's working arrays when its consumers finish.

Share invariant case preparation at the appropriate process scope. Replay saved bundles/observations
where they answer the question instead of rereading MRI volumes. Rich payloads can remain lazy, while
compact exact counts serve compatible comparisons. Retain complete required object outputs, values
and provenance; release consumed intermediates under the existing retention contract.

Parallelize independent studies, independent clinical reading and bounded disjoint mechanical source
repairs. Native workers and authenticated Claude Max CLI workers are available under the established
worker guide. The integrator supplies meaning, pinned inputs, allowed files and consumer contracts;
workers return facts/patches. Do not let a worker's framing silently replace the author's mechanism.

Efficiency follows from conditional structure: a resolved fact reduces the useful alternatives and
changes which other questions need reading. Significance weighting motivates propagation and useful
residual selection, not multiplication of dependent observations as independent probabilities.
Do not promise that arbitrary memory expansion is free or that a borrowed asymptotic constant measures
this implementation. Measure actual useful work and runtime without turning them into anatomy targets.

## 12. Completion checks and the competition endpoint

Keep three claims separate:

| Claim | Required evidence |
|---|---|
| Software is integrated | Real producer/consumer traces, adversarial intent checks, immutable publication/readback, resume and normal gate evidence |
| Teaching reference is represented | Addressed images, correct identity/clinical scopes, actual compatible bundles and per-question readback/residual reasons |
| The society learns and diagnoses | An appropriately checked experience changes subsequent applicable interpretation/action, preserved uncertainty, and per-condition diagnostic trajectories on independent studies |

Begin useful training with a thin competent basis; continue genuine missing teaching alongside it.
Do not claim all 58 are resolved because a command exported records. Do not delay training until an
untrained automatic locator perfectly resolves all 58. These are different errors.

The final trained system consumes a frozen memory and emits the official twelve values per study
through the existing submission adapter/schema. It may support several conditions, decline a
confident categorical assignment or retain disagreement. Keep the categorical finding and evidence
beside the graded output. Property-deviation digits are not submission probabilities. Preserve the
currently approved readout; this handoff supplies no replacement probability formula or covert
score-tuning policy.

Use the official template and current source-backed deployment constraints in FULL_BUILD_PLAN §16.9
when validating the integrated competition run: offline operation, actual selected hardware, complete
time/memory/storage/output accounting and capacity for bounded residual work. Bootstrap's costly
teaching tools need not run for every competition study. A valid CSV alone proves neither diagnosis
nor the compute envelope. Submission remains subject to Rohan's instruction.

## 13. Dispatch text for the implementing agent

> Build the existing knee design as ONE society with ONE shared object account. Support, anatomical
> role, physiological state and diagnosis condition one another; do not create separate generative
> and diagnostic models or freeze identity before diagnostic reasoning can act. Anatomy supplies
> spatial relationships; physiology supplies functional meaning. Cheap calibrated readings are
> valid observations but their numerical middle does not define healthy function. Preserve typed
> balanced-ternary departures, signed teaching and unread states. The endpoint is the twelve Kaggle
> condition questions with warranted assignments and honest uncertainty. Use the hand-grounded 58
> and correctly identified unimplicated normal objects to teach; do not demand perfect pre-AI
> recognition. Implement R1–R7 here against whole current functions and real consumers, respecting
> the current packet's ownership. In particular, fix applicable procedural opposition, finish
> action attribution for identity looks, replace the borrowed-teacher-cue demonstration with real
> next-study action evidence, pin actual source/study inputs and compose the existing growth and
> experience paths into one frozen-parent round. Preserve every signed store and one publication
> chain. Parallel workers produce disjoint observations/patches; one integrator publishes. Show a
> real learned consequence, then repeat the same operation locally at scale. Do not substitute a
> fitted cutoff, prototype average, generic optimizer, perfect-boundary campaign or Kaggle
> packaging exercise. Return a genuinely unspecified update as one concrete operation with its
> actual inputs and missing transformation while continuing the specified work.

## 14. Literal request and mid-turn corrections

Copied as complete recording units from the conversation. These author messages govern the
engineering binding above. This copy keeps the new handoff self-contained even where local
conversation records are not tracked by Git. Recording metadata remains visibly separate.

### Rohan — review completion and articulate scale training, 2026-10-22

Recording metadata: the following is his repeated pre-compaction request, preserved once here. The
other agent's completion report is agent evidence to check, not an additional founder specification.

Take a look at the changes in the code. They've all landed...and I think we're done?

Anything we need to send to the agent? Any last-mile changes/fixes? And after that,  can you clarify/articulate the full design of how the society-of-agencies/"law as architecture" theory paper/etc inspired classical AI pipeline should be trained at scale? Unambiguous and idiot-proof. Make sure you read all the documentation in this project that would be relevant, that might clarify/enhance your understanding here

### Rohan — generative assignments and signed diagnostic discrimination, 2026-10-22

We want to be able to call each anatomical object as well as we can with the society-of-agencies design. Then, GIVEN a set of anatomical objects, the society-of-agencies has agencies that link the anatomical objects to diagnoses discrimination. The first is "generative", in that it is meant to add/resolve candidates for anatomical objects and make those assignments with the "significance weighting)-style conditional logic aspects, the second is pure balanced ternary discrimination--0/normal/orthogonal, -1/sub-(whatever)/less, and +1/super-/extra/whatever. A broken bone is a bone that is "less" because it's a normal bone with sub-ideal structural integrity. Inflammation is a tissue that is the ideal tissue "plus" more. Etc. makes sense?

### Rohan — one society; connected support, role and condition assignments, 2026-10-22

Recording metadata: Codex had incorrectly called these two societies. This is his correction, not
approval of that split. The generative and discriminative activities belong to the same model.

Well, these aren't different *societies*, they're different agencies/sets of "agencies" in the single model. Assignment of object pixels and assignment of role ID is inherently connected to diagnosis of conditions. Read the "anatomy map" document plus the one about structural diagnosis one(s) for some context

### Rohan — anatomy, physiology and objective functional meaning, 2026-10-22

Note also that anatomy--the physical location of objects--and physiology--how their physical presentation and anatomy inform function--are related but different. Hand-built "scan-calibrated" measurements are fine for a cheap estimation of literal physical relation, but objectivity and definitional correctness matter for purposivistic assignment of function

### Rohan — twelve-condition competition endpoint and the complete handoff, 2026-10-22

Note also the whole POINT of all this--the Kaggle competition. We want to be able to diagnose scans from among the 12 options, with some degree of acceptable uncertainty if we can't confidently make an assignment.

Please take in my prompt and all my mid-turn adjustments, write up a FULL contextual grounding and implementation writeup for that other agent to work on
