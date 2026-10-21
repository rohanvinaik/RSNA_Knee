# Complete the knee-recognition pipeline — execution and handoff plan

**Recorded 2026-10-18 at Rohan's request after his supplied build audit.** This is the canonical
remaining-work order. It supersedes the scheduling in COHERENT_BUILD_ROADMAP and
THREE_VIEW_PRODUCTION_EXECUTION; their dated acceptance records remain history. Human words,
THEORY_OF_THE_CASE and the primary thesis govern this plan. This is the lead's engineering
application, not a new recognition theory or a declaration that the build is finished.

The deliverable is **one production operation taking a knee MRI study to coherent anatomical
objects**, their independently native descriptions in available orientations, one physical relative
map, retained evidence and named uncertainty. Correctness and compute efficiency come from the
same anatomical structure. Finish that ground layer before the human-specified later AI/diagnosis.

**Mechanical implementation contract:** use §§14–15 before assigning or accepting any remaining
work. They define 22 measurement products, their existing/required consumers and permitted
interpretations, 26 anatomical-family contracts, and concrete P2b wiring. A packet must name its
input/output contract IDs and actual consumer. REUSE/WIRE work is mechanical; a missing native
selector marked DEFINE NATIVE RULE must be supplied by the lead from the actual images and
§7's rule-review procedure before a worker implements it. No proxy score or preferred
intermediate output fills that semantic gap.

## 0. Grounding: every session start and every compaction

Rohan, 2026-10-18: «CLean up the post-compact setup process to focus only on the parts that are
relevant and useful and won't make you fuck up like you have been. The build/handoff plan is a good
central place, only add in anything that is addatively useful for you to ground in the project
epistemology and working contract.» This section is that sequence. AGENTS.md, HOW_TO_BUILD §2,
NEXT_SESSION_PROMPT and the project memory point here.

**Loaded into every session by `CLAUDE.md`:** AGENTS.md, THEORY_OF_THE_CASE.md, HOW_TO_BUILD.md (the
rules and every correction), this plan, the original thesis and anatomical-priors conversations,
the exact-HDC and classical-AI conversations of 2026-10-19 and 2026-10-20, the latest
squint/bootstrap conversation, AI_DIAGNOSTIC_DESIGN, SQUINT_PRODUCTION_CONTRACT and
CLASSICAL_AI_BUILD_DESIGN. Imports establish availability, not proof of comprehension.

**Straight after a compaction, and at every session start, in this order, before anything else:**

1. Read the pre-compact snapshot the start-up hook names: his messages, word for word; his last one
   is the task. A compaction summary is never a source, and neither are your own notes. What his last
   «Yes» approved is your own message just before it in the session transcript: read that exchange
   whole. Pasted or relayed agent text keeps its author: a fact to check, never his instruction, never
   quoted as his words (`docs/conversations/2026-10-18-build-session-corrections.md` shows how the two
   are told apart).
2. Read whole, where not already loaded: the thesis conversation, THEORY_OF_THE_CASE,
   OBJECTS_AND_CONDITIONS, HOW_TO_BUILD and RESOLVING_THE_PARTS; for the current collapse work,
   RELATIVE_POSITION_MAP, its §0 first (§8.8 and its latest accepted §8 record carry the current
   construction); TARGETED_ANATOMICAL_COMPUTE and his complete messages in
   `docs/conversations/2026-10-18-anatomical-priors-and-targeted-compute.md`; this plan, its §§1–1.2
   and §§14–15 before any task; NEXT_SESSION_PROMPT. When a task needs them, the primary units this
   plan names: `../cell_tracking/docs/pipeline_thesis/paper/what_an_object_is.md` §§4, 7, 13 and
   `SIGNIFICANCE_WEIGHTING.md` §§4–5, 13–16.
   For P12, also read the complete author clarification in
   `docs/conversations/2026-10-19-structural-information-and-exact-hdc.md` and the
   interface contract `docs/HDC_ENCODING.md`. His later clarification governs the knee-specific
   healthy reference; do not substitute the cell experiment's provisional terciles.
   For bootstrap, case admission, memory, agency learning or diagnostic-AI work, also read the
   complete AI conversation (`2026-10-20-classical-ai-diagnostic-control.md`), the latest
   squint/bootstrap conversation (`2026-10-21-ternary-buckets-and-squint-orchestration.md`) and
   [CLASSICAL_AI_BUILD_DESIGN.md](CLASSICAL_AI_BUILD_DESIGN.md) whole. K-lines enable corpus
   construction and remain active classical memory; corpus population is not the whole learning
   process. Confirmed negative examples must reach the actual memory consumer.
   Before changing bootstrap/learning integration, read the pending acceptance contract at
   `openspec/changes/complete-signed-bootstrap-loop/` (proposal, design, capability spec and tasks).
   It declares unfinished behavior; artifact validation does not certify runtime completion.
3. Look at the proof study's pictures with the conversation in mind: see the parts of the knee the
   lenses already pull out («you can already see parts of it peeking out from that image»), not an
   audit of your own code. The lens pictures, `data/pictures/interiors/<proof uid>/series.png` and its
   per-series panels, are the current stage's output; the named pictures,
   `data/pictures/assignments/<proof uid>/series.png` and its panels, show the parts resolved on the
   middle slices; `data/pictures/main-slices/<proof uid>/series.png` shows the parts named on slices of
   their own (the fibula, the ACL, the LCL and the semimembranosus tendon). The proof uid is
   `1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149`. With them, the two figures
   he showed as proof of the thesis, the cells and the knee (`data/pictures/thesis-2026-10-13/F14-cells.png`,
   `data/pictures/thesis-2026-10-13/knee-series.png`; THEORY_OF_THE_CASE, canonical references).
4. `git log --oneline -15` and `git status`; then §13's active-task index and the packet it names.
   That packet alone holds detailed live state, jobs and the next single action. Verify its actual
   source pins and job handles before stating anything as current.
5. Read `docs/GROUNDING_AND_WORKER_GUIDE.md` whole before dispatching or integrating any worker.
   Then do what his last message asks. Build work follows §4's order, each task's contract in §§14–15
   and §15.3's acceptance record; anatomy rules follow §7's process. Do not ask him to confirm again
   what is recorded («YES. I have said that MANY TIMES»), and do not re-measure finished parts on other
   slices or studies.

Always: the archives (`archive/`, `archive2/`) are invisible unless he says to look; read whole units,
never text-search. Dated scheduling and status (HOW_TO_BUILD's dated sections, `docs/history/`, the
status lines of the MAP's §8 and RESOLVING's §9 entries, earlier plans) are history and evidence for a
part, never the next step; the definitions and limits those entries record stay in force until a later
accepted record supersedes them.

The worker guide required in step 5 adds launch, dependency, invalidation and integration
procedures. Its §10 distinguishes proposed enforcement from available checks. It does not replace
this sequence, the work order or §7's chosen anatomy-rule review. §13 names the active packet;
all populated live state and jobs are recorded only there.

## 1. Mechanism and non-negotiable distinctions

Read the original conversation with its pictures: simple, complementary, lossy measurements
already separate real structures. The remaining work is to say plainly why a structure looks like
itself, encode that general anatomical distinction, and connect its result to the rest of the knee.
A lens measures a property; its combination with other measurements and anatomy resolves identity.
No lens has to identify a whole object alone. Add a simple objective lens when needed; Rohan
explicitly authorized this. Preserve each measurement's meaning and provenance.

The construction is:

> cheap whole-study readings → useful leg/region priors → obvious native anatomical anchors →
> shared physical context and map → a small residual native question → complementary local
> readings → an object description → information available to subsequent questions.

This applies to every existing and new family, not an optional optimization after recognition.
Containment, attachment, sidedness, intervening space and physiological course constrain both
**what it could be** and **where to compute**. Use these consequences before expensive work.
A relation in a catalogue without a decision consumer has not implemented that mechanism.

- Build per concept, never per study. No proof coordinates, selected component IDs, threshold
  sweeps, cohort-fitted anatomy, or a new rule for each failed image.
- Useful priors suffice. Do not demand perfect masks, perfect exclusion, or whole-frame equality
  before restricting a question. Dark tissue within a leg remains anatomy. Missing evidence is
  not evidence of absence. Retain the scope and unknown exterior of every bounded reading.
- A deliberate scope change may change local measurements. A cache/refactor/compiled twin
  claiming equivalent answers must preserve them. Do not confuse these acceptance tests.
- A projected source, trace or expected map position locates a question. It is not a native
  boundary, a resolved native plane, or independent confirmation of its own prediction.
- Three independently selected sagittal/coronal/axial **key planes** jointly constrain an object's
  physical reference. Never substitute a single section's centroid, average centroids, copy slice
  indices between acquisitions, or create separate anatomy maps for fat-bright/fat-dark images.
  A three-plane reference need not lie in a tissue voxel, especially for distributed fluid/surfaces.
- Competent once is the recognition criterion. Requested three-view capacity means a competent
  native description in each orientation where that object is supplied, not perfect recovery on
  every study. Preserve unresolved outcomes and known overreach; later AI handles variation.
- Keep all computed readings and categorical information. Saving is not a consumer. There is no
  permission here to drop intermediate arrays or add a default-off retention flag.

The information-theoretic grounding is What an <Object> Is §§4, 7, 13 and
SIGNIFICANCE_WEIGHTING §§4–5, 13–16. One useful fact constrains a cluster of dependent questions;
complementary views can unlock constraints neither supplies alone. Preserve the structural
channel itself: Rohan's later Monty Hall clarification explains why a bounded relational
derivation can add conditional information to a local representation that omitted that channel.
Do not replace that mechanism with a blanket statement that derivation adds no information.
Reusing a consequence is still not another independent acquisition or observation. No other-domain scaling constants,
new significance-score engine or corpus-induction system is imported into this ground layer.

### 1.1 Required epistemology: a failed construction does not retire the capability

**Human correction, 2026-10-18.** Rohan objected to the P2a dismissal and asked that the build/
handoff prevent its recurrence. The concrete error: a script measured padded bounding rectangles,
then the record asserted that an unimplemented tile-level region would fail too. That assertion
had no measurement behind it. The earlier Codex review was too generous in treating the decision
as a reasonable reprioritization. This correction governs every stage, not just P2a.

1. **State the question before choosing its proxy.** A useful leg/background domain is a spatial
   region, potentially irregular, tiled or composed from complementary views and known anatomy.
   The smallest enclosing rectangle is one possible execution envelope, not the region itself.
   A rectangle covering most of the image says nothing by itself about how much irrelevant
   background an actual region can exclude or which dependent questions it can constrain.
2. **Report exactly the operation performed.** Name the construction, inputs, views, scope,
   measurement and consumer. An unbuilt tile mask has no measured outcome. A test of one padded
   rectangle is not a test of every spatial representation. Label an inference as an inference;
   never promote it to a measured result or copy it into the next handoff as established fact.
3. **Diagnose the residual within the thesis.** If edge-connected darkness enters dark marrow,
   that construction confounds exterior with tissue. Use the other available distinctions—
   enclosure, geometry, neighbouring slices/views and resolved anatomy—to make the question
   useful. No individual lens must solve it alone. Do not turn that failure into abandonment,
   hand-tuned instance metrics, a weighted verdict, or a default ML replacement.
4. **A prior's value includes its consequences.** Its own rectangular crop may save little while
   its region, containment or anatomical exclusions narrow many later identities and scopes.
   Trace those actual consumers. One local area ratio or timing share is not authority to remove
   a foundational information handoff. Share an existing equivalent producer rather than add
   duplicate work simply to tick a task box.
5. **Keep the capability open until demonstrated and connected.** Useful once is enough; perfect
   segmentation and universal success are not required. Mark an unsuccessful construction as
   such and retain its evidence. Do not mark the capability complete, unnecessary, disproved or
   permanently skipped. Other independent work may continue without silently deleting it.
6. **Keep authorship and authority exact.** Agent analysis remains agent analysis even if a human
   relays it. Do not attribute a Codex paragraph to Rohan or manufacture approval from it. A
   repeated claim in a README, plan, prompt and commit is still one claim, not corroboration.

Before closing a structural task, record its actual region/measurement, at least one useful
native demonstration, which expensive decision consumes it before running, and which downstream
questions it narrows. If these are not supplied, record the remaining work; do not invent a
negative conclusion. Native anatomy remains the criterion, not the proxy an agent found easiest.

### 1.2 Required epistemology: representation fidelity before intermediate-mask optimization

**Human correction, 2026-10-18.** Rohan supplied an agent report that called an AX14 calibration
change (74.5→71) and loss of 63 bright-rim pixels "hurt accuracy", then proposed carrying only
section interiors inside a 2 mm shell. Those are the agent's reported observations/proposal,
not an independently established accuracy result or an accepted remedy. Rohan clarified:
«It should be REASONABLY accurate, but alignment with the theory of the project as a computer
vision pipeline is WAAAAY more important». This applies across the entire ground-layer build.
The distinctions below restate an agent's review that he pasted under his words «You are
FUCKING this up AGAIN:»: agent text he endorsed, not his words (verbatim record:
`docs/conversations/2026-10-18-build-session-corrections.md`, 16:37 and 16:42).

The task is to implement a correct, useful anatomical description and its information flow.
Reasonable native competence is required. Cleaner intermediate masks, fewer ambiguous pixels,
a preferred calibration value, larger support, or agreement with an old result are not substitute
objectives. Do not optimize an intermediate proxy until it becomes the task being solved.

- **A changed reading is a changed reading.** Report the actual calibration/count and inspect
  what the image says it represents. Neither its numerical direction nor its difference from
  an old result proves accuracy improved or declined. If a region visibly names another
  structure, identify that specific anatomical/semantic error; do not dismiss it, but fix the
  definition or information handoff rather than fit the proxy numbers.
- **Keep what each representation means.** A projected location prior, a source section with
  its own scope/uncertainty, a native bone observation, a coarse enclosure, and samples used
  for marrow calibration answer different questions. Carry that distinction through existing
  records and consumers. An uncertain edge does not become certain native bone or marrow by
  projection or union. Conversely, uncertainty does not make the whole useful source unusable.
- **Repair a conflation where it occurs.** If a consumer treats a broad bone-location support
  as definitive native marrow, diagnose that producer–consumer mismatch. Preserve the source
  reading and use native signal plus complementary geometry/anatomical relations to answer the
  marrow question. Do not erase source evidence to make the misinterpreted mask look cleaner.
- **An anatomical law is not an arbitrary morphology instruction.** "Marrow is within bone"
  constrains marrow's anatomical identity. It does not by itself specify eroding every source
  section by 2 mm. A shell/interior operation may be useful only with an independently stated
  measurement role and native evidence. Reusing an existing number does not establish that
  role. Do not choose a width or seed variant because it restores 74.5, recovers 63 pixels, or
  looks closer to a preferred intermediate output.
- **Complementarity is allowed to be messy.** The descriptions are lossy by construction. Use
  their conjunctions, exclusions, context and retained disagreements to constrain the residual
  question. Do not require each input lens or seed cloud to be a clean full object before it
  may contribute. "More seeds do not guarantee better anatomy" prohibits an unsupported success
  claim; it does not instruct the agent to purify seeds until local metrics improve.
- **Experiments serve a stated question.** Comparing early, pooled and interior seed variants
  is development work, not inherently a mistake. Before accepting one, state what property it
  measures, why that property answers the anatomical question, and which downstream decision
  uses it. Choose by that explanation and reasonable native competence, not a ranking of proxy
  outputs on selected study slices. Preserve the variants/readings; no per-study tuning.

Before a semantic/seed-filtering change, write three short statements in its task packet:
(1) the intended meaning of the producer and consumer; (2) the specific mismatch observed, if
any, with native image evidence separated from numerical change; (3) why the proposed general
operation repairs that mismatch under the thesis. Then implement the smallest repair through
all actual consumers. This is a clarification of the existing data contract, not a new rule
engine, exhaustive accuracy campaign, perfect-boundary requirement or request for repeated
human approval. Once the faithful description is reasonably competent, continue the build.

### 1.3 Governing production principle: structure buys correctness and efficiency together

Rohan's specification for the whole build: «a well-built productionized version of the "what an
<object> is" thesis, like a competent performance engineer would produce, with logical consolidation
of compute with and across studies». The following engineering contracts are this Codex session's
implementation of that request in the existing plan, grounded in the cited primary sections; the
Fable consultation is a second reading, not new authority. This governs P0–P13 and every family packet,
not only P10 or §16's measured kernel leads. The thesis's §§4.5–4.6, 5.1, 7.3–7.5 and 13.3–13.7 supply the mechanism:
cheap context makes a smaller question; readings are made once and handed on; expensive work follows
the remaining uncertainty; exact retained information supports later questions without repeating it.
Its cell-specific temporal invariances and numerical savings are not MRI assumptions.

**Build the anatomical information flow before accelerating its arithmetic.** The leg domain bounds
where a knee question is useful; bones constrain marrow, joint spaces and attachments; resolved
muscles and bones constrain tendons and vascular courses. These are useful priors with provenance,
not perfect masks or additional observations. Each family consumes what is already known before
choosing its native slices, query region and necessary surrounding context. The cheap squint and
physical map locate the question; its complementary native readings resolve it. An expensive full
frame followed by a mask has not implemented this reduction. Where a prerequisite genuinely needs a
broader read, name it and retain that read for its other consumers. Unknown exterior remains unknown;
no useful dark tissue is classified as exterior merely because its signal is dark.

**One operation, many consumers.** Keep measurement, anatomical decision and orchestration separate.
A named value has a producer, dependency identity, scope, owner, lifetime, retained address and actual
readers. Two families needing the same value receive it, rather than each making a private copy of the
analysis. Distinct acquisition, context, halo or calibration can require different readings; sharing
must preserve that distinction. A saved array with no decision consumer is retained evidence, not
proof that the recognition graph uses its information. Derived map/context consequences guide the
next measurement; their repeated reuse is not independent corroboration.

**Consolidate at the lifetime where the fact is true.** Across studies share authored anatomical laws
and relation templates, approved descriptive search priors, executable definitions, compiled code and
preparation whose inputs are actually invariant. Within a study share its decoded sources, cheap
readings, geometry, map, scoped contexts and already-resolved object information with all eligible readers. Each patient's native
observations, calibration and placements retain their own identity; unrelated studies are not adjacent
frames of the thesis's cell movie. Equal slice numbers, dimensions or object names do not establish
reuse. A cross-study search prior remains an expectation guiding a new native question, not an
observed placement in that knee. Neither a ban on all cross-study sharing nor a cache of one patient's
answer for the next is this contract. §16.6 specifies the actual reuse and invalidation account.

**Compile the bounded work that remains.** Consolidate producers, narrow queries and avoid redundant
materialization first. Use the production trace and allocation evidence to decide where JIT, Rust or
C++ can fuse loops, reuse scratch and reduce language crossings. NumPy/SciPy calls may already run
native code; changing the wrapper's language is not itself a saving. Preserve a plain reference twin,
measurement semantics, precision and named decisions. No fastmath, silent quantization, approximate
replacement or dropped reading follows from an efficiency request. The later MRI representation is
still P12's human-specified work; the thesis's exact bundling explains the intended reuse, not permission
to invent its layout now.

**The unit of success is the whole production operation.** Account for fresh-process startup and JIT,
decoding, recognition, retained state, serialization and cohort execution through the one CLI. Amortize
input-independent setup across studies in bounded workers; do not retain an ever-growing patient cache.
Keep complete required object information reconstructible under the retention contract in §16.6 while managing residency and intermediate-file lifetimes.
Actual compute, memory and output limits constrain scheduling and storage, never anatomical identity.
Use the existing gate, real callers, ledger and full-run instruments (§§9, 16); kernel replays alone do
not establish whole-run efficiency. Large savings are the intended consequence of this construction;
no unmeasured speed-up factor or preferred benchmark number is its acceptance criterion.

Actual competition limits are production requirements throughout the build; §16.9 makes W8b storage
closure and W10 verification of the complete compute envelope mandatory. They do not define anatomy.

**Optimize for the consumer of the representation and the actual competition operation.** Rohan
reaffirmed this on 2026-10-20 (the exact words follow the retention exchange in
`docs/conversations/2026-10-20-competition-object-retention.md`). The intended operation reads a study,
resolves anatomical objects, writes each object's unified view/lens/direction/scale representation,
hands it to the later human-specified AI and produces the competition's twelve diagnostic
probabilities. At the current pre-AI milestone, retain complete object pixel/HDC bundles as requested.
Judge storage choices by complete encode/access/inference/output cost and the useful retained
information, including the later consumer's access patterns, rather than compressed bytes alone.

The thesis §§7.1/7.4–7.6 and 13.1–13.7 give the existing engineering mechanism: encode readings
already computed, keep values beside their digits, use exact sparse counts where they are the
carrier's equivalent form, and pay only for a question's relevant spoken banks. Reuse compatible
per-object bundles and invariant preparation; retain cross-view/source/refinement provenance and
explicit silence. Avoid requiring the next stage to repeat recognition, recompute a bundle already
held, materialize dense pixel vectors for a count-only operation, or write/read H5 merely to hand
live data between stages. H5 remains a durable handoff and offline teaching product. Preserve a
clear in-memory consumer boundary where exact arrays/composed profiles are alive; its AI mechanism
and query/teaching policy are not to be invented. Cell-movie temporal assumptions and precision
rungs are not automatically MRI rules. W10 includes actual configured encoding/write/readback work
and reports the future consumer cost as unspecified until supplied, never zero.

Every packet applies this principle using §16.7's short work account and its existing M/F contract.
This is ordinary construction of the approved pipeline, not a new framework, tuning objective,
repeated approval gate, or an optimization phase postponed until all anatomical families are built.


## 2. Historical source checkpoint and accepted scope

At this historical handoff, the accepted anatomy was RELATIVE_POSITION_MAP §§8.35–8.36: native axial/coronal PCL,
with proof SAG18/COR22/AX15 jointly constructing LPS
`[-110.95654820639552, -42.08987813891625, 23.75791539106383]`. This is a competent local
reference, not full course or volume. Four wrong axial identifications and three local empty
readings remain recorded; their shared source-eligibility issue is work below.

Use these paths relative to the project root:

- **B:** `data/readings/collapse-20261017/full-build/targeted-compute-20261018/`
- **E:** B + `efficiency-review-20261018/`
- **H:** B + `full-plan-handoff-20261018/`

These are shorthand in this document, not literal shell environment variables.

The accepted manifest is E +
`pcl-coronal-production/source-freeze-coronal-pcl-70/source-hashes.json`.
Its file SHA-256 is `11e2f799a46e31d58e1763780eb6a3dbb58d32e7f1594290e4c067767e119d12`;
runner SHA-256 is `a2f9f22323707d8a16253844a3eb98ec14bc0e6c27ed05c49db8a5ccbbe6842d`.
The accepted epoch's gate passed 1,087 tests. Recorded serial, parallel and public runs exited 0.
The 70 source files were rechecked at that handoff. Its HEAD was `a118db8` plus extensive
uncommitted/untracked work; `7b61b54` subsequently committed that work and later increments
followed. That hash alone does not reproduce the historical epoch. Preserve its source snapshots;
use §13's active packet and verify live source before making a current-state claim.

Accepted recorded scope:

| Group | Accepted scope at this handoff; definitions and limits remain in force |
|---|---|
| Original anatomical definition pass | Every outstanding part in ANATOMY_DEFINITION_CHECKPOINT was demonstrated once by 2026-10-16. Full course/precision/generalization was never required. |
| Bones and joint/anterior families | Native bone references, fibula, joint/fluid/recess/lining/capsule, extensor tendons, retinacula and fat-pad bridges have accepted records in MAP §§8.12–8.25. Their limitations remain. |
| Compartment additions | Femoral axial cartilage §8.26; sagittal and axial sided menisci §§8.27–8.28; PCL §§8.35–8.36. |
| Structural execution | Local body sharing, bounded bones, equivalent batched squint, scoped patella and immediate native-family map handoff have separate accepted epochs §§8.29–8.34. These do not close whole-pipeline efficiency. |
| Remaining native orientations | ACL AX/COR; tibial cartilage AX; attachment family and posterior/medial family below. |
| Catalogue/whole operation | Marrow's explicit coherent-output address, diffuse/general-specific semantics, upstream shared priors, remaining consumer adoption, persistence/compute closure and final cohort refresh. |

The older Packet B 58-study cohort is a **different source epoch**. The 43-concept matrix is a
static trace of emitted concepts, not completion or accuracy. Recompute state when reporting it.

## 3. Take on the supplied audit

The audit's strongest point is correct: the newest local readers have the desired shape, while
older high-cost readers often rediscover anatomy over whole slices. Targeting after the expensive
measurement does not buy the structural efficiency being requested. Broad bounds and repeated
fallbacks are visible unfinished work, not evidence against the thesis.

Preserved verbatim at H + `user-supplied-audit-verbatim.txt`, SHA-256
`ce228948a3bee59f88b76111cc9d8d6b546967c600cfa7a61aea5f806ff1e139`.
Its reported 43.4-second profile and cost shares belong to that frozen run; they are not new
paired speed measurements. Items overlap and must not be summed as independent costs.

Qualifications and source findings checked by the lead:

1. A low tile maximum is not proof that no anatomical part occupies it. Cortex/tendon can be
   dark. Build a useful exterior/leg envelope with context and preserve enclosed dark tissue.
2. Proof 21/43 versus bursa 2/43 complete references measures coverage, not an accuracy difference.
   Trace the earliest common missing prerequisite; do not tune the bursa study toward the proof count.
3. `refine_map` consumes observation metadata/counts/native geometry, not support-mask pixels.
   Correct missing observation read declarations without inventing mask consumers. Retained
   working arrays can honestly remain unread.
4. `offer_native_family` declares observation reads for only four hardcoded families. Make the
   declaration follow the actual conversion/offer for every family, while preserving real lineage.
5. Later native bone sections currently do **not** refresh the original carried `Leg` or coarse
   seeds. `leg_on` caches by `(series_uid, slice)` only. Publishing later bone context requires
   context-aware caching, not merely calling the old cache with a new Leg.
6. Similar profile builders and coordinate calculations are candidates for sharing, not proof
   that their inputs/semantics are identical. Establish actual runtime identities first.
7. Production `interior_regions` does not use the drawing layer's compiled border reader. The
   old blanket statement that the production lens runs on its JIT twin is inaccurate.
8. Vulture names are leads. Contracts, retained diagnostics and actually dead helpers require
   different remedies. `relative.py` still supplies production `IdealVector`; its historical
   withdrawn algorithm does not make the whole module safe to delete.

The attachment's global Claude settings/hook claims are outside this project plan and were not
independently verified here. No global settings change or environment repair is required by this plan.

## 4. Execution order and ownership

The following task order supersedes postponing all structural propagation until old R5. Apply
useful targeting throughout; do not wait for a perfect background stage before building anatomy.
Each task ends at a small, source-pinned, real-CLI checkpoint. One lead owns production integration.

**Parallel construction is a foundational build requirement, not an optional optimization.**
Rohan, 2026-10-19: «If I had 5-10 engineers, each of them would obviously have something useful
they could work on independently. This should be equally applicable to AI coding agents».
His complete correction is `docs/conversations/2026-10-19-parallel-construction.md`.
The lead must organize this designed pipeline as a team would build it:

- Decompose the actual dependency graph into independent implementation packets. Native families
  with settled rules, shared-context wiring, persistence/readers, runtime packaging and invariant
  tests can be written concurrently against the existing substrate. Never make a single ordered
  list of object names the code-writing schedule.
- Keep available workers doing useful implementation when such work exists. Delegating only
  searches, repeated audits or verification while the lead writes everything serially does not
  satisfy this requirement. The lead retains meaning, anatomical decisions, visual acceptance
  and integration; it does not need to type every mechanically determined implementation.
- Use inexpensive in-session helpers and the **local Claude Max terminal CLI**, under the existing
  authorization and §10 route. A client’s in-session concurrency limit is not a reason to leave
  independent CLI work unlaunched. Do not use browser automation to operate the subscription.
  Keep actual process handles, input pins, full returns and measured usage in the active packet;
  a prepared prompt or a completed old call is not a running worker.
- Give each worker the chosen mechanism and whole governing/source units, exact inputs/outputs,
  allowed files or named functions, consumer and checks. Work in isolated copies/worktrees.
  Shared-file work may proceed in disjoint named units and be merged by the sole integrator;
  it need not wait merely because both units live in the large runner. Never overwrite an
  intervening accepted change. Reject genuinely stale inputs or explicitly rebase and verify.
- Distinguish **code-writing dependencies from integration dependencies**. A frozen production
  cohort or final gate freezes that checked tree, not independent candidate construction.
  A worker with a ready candidate can proceed to its next independent approved packet while
  the lead integrates. Wait only for a concrete unavailable prerequisite, necessary native
  decision, ownership conflict, external capacity or explicit resource constraint.
- Integrate ready packets continuously at controlled boundaries, then verify one coherent wave
  through the real entry point and required gate. Do not run a whole cohort/gate after every
  private worker or tentative object rule. Preserve focused worker checks, changed-native image
  review, source/retention contracts and the final exact-tree gate; parallelism waives none.
- Bound simultaneous **local compute** by actual CPU/RAM ownership; remote CLI inference and
  private code writing are different from several full-volume production runs. Share tooling,
  avoid MCP/server fleets and orphaned children, and clean up idle build services. Resource
  control must not become an excuse for serializing low-footprint code writing.
- Preserve the fixed finish line: useful general anatomical definitions and addressed pixel
  bundles, not perfect intermediate masks. Completion is the integrated working operation,
  not tokens spent or worker counts. Record a factual critical path and remaining work in §13’s
  sole active packet, with ETA assumptions and uncertainty; do not promise a deadline from
  uninspected scope. A missed ETA requires changing execution, not merely issuing another one.

**Pre-AI completion-wave binding, reaffirmed by Rohan 2026-10-20.** Execute this approved plan as
parallel implementation lanes: (a) native measurement/address adapters; (b) sourced healthy and
relational-bank bindings; (c) unified full/sparse/cheap object composition and physical support/depth
ownership; (d) lossless persistence through every reader; (e) bounded study lifetime and offline/native
runtime; (f) independent contract/entry-point verification. These are responsibilities, not a claim
that each is currently running or accepted. The active packet alone records live assignments.
Use the native session helpers and actual Claude Max subscription terminal CLI for independent
mechanical construction. Root retains meaning, direct positive/negative intent tests, native-image
acceptance and sole integration. Drive Detective's printed procedure on suitable pure decisions;
characterization never substitutes for intended meaning. Keep unknown/equivalence/refusal outcomes
honest. Integrate continuously at real dependency boundaries; freeze one coherent batch for coordinated
independent verification and its full CLI/gate checkpoint while unrelated private construction continues.
The finish line includes every required source family, sourced applicable references/structural banks,
one exact object representation across views/lenses/scales, reconstructible support ownership, W8b
storage and W10 resource verification. Original readings and named uncertainty remain. The later AI
and diagnostic mechanism is still the author's explicit dependency; no worker fills it in. This binds
§§9,12,14–16 to the existing completion workflow and creates neither another master plan nor a second
current-state record. Stop faithful, competent anatomical construction without a perfection campaign.

Before leaving a worker idle or making work serial, the lead must be able to name the genuine
blocking dependency and show why another approved independent implementation packet cannot use
that capacity. Rohan’s urgency and later-AI dependency make this a delivery obligation throughout
the remaining build, including after compaction.

| ID | Work | Prerequisite | Retrofit/old packet correspondence |
|---|---|---|---|
| P0 | Verify handoff and inventory actual object/view evidence | Primary grounding | R0; no production edits |
| P1 | Review and integrate the existing scoped-sartorius candidate | P0 | E05; bounded ready work |
| P2 | Shared early leg/domain prior and native bone-context handoff | P0; integrate as separate small increments | E03/E24; high fan-out prerequisites |
| P3 | Reuse bone/patella context in patella and recess readers | P2's applicable context | E01/E02/E16; avoid bone rediscovery |
| P4 | Correct source eligibility and complete ACL/tibial cartilage | P2; available P3 context | R2; structural PCL residual |
| P5 | Complete missing attachment-family native views | P2/P4 available evidence, not all studies perfect | R3 |
| P6 | Complete missing posterior/medial native views | Shared bone/joint context and source sections | R4 |
| P7 | Carry useful domains through every remaining older reader | Incrementally alongside P3–P6 | E02/E04/E06/E24 |
| P8 | Catalogue, marrow, diffuse/general-specific output closure | All family implementations inventoried | R5 |
| P9 | Shared geometry/profiles, lineage, digests and persistence | Incrementally with affected tasks | E08–E16/E21–E23 plus audit corrections |
| P10 | Optimize residual measured hot kernels | Useful scopes/producer sharing established | E17–E20; no speculative rewrite |
| P11 | Frozen whole-operation, cohort and competition-runtime recognition verification | P1–P10 accounted for | R6 |
| P12 | Exact encoding/extent contract and implementation | Recognition capacity; MRI contract grounded in primary thesis | Later representation milestone |
| P13 | Human-specified AI/diagnosis, then competition output/package | Explicit later specification | Deferred dependency, not invented here |

P9 lineage fixes accompany the next adapter edit, not the end of the project. P7 and P9 are
whole-operation checklists, not reasons to restart accepted families. Do not make a fixed sequence
of object names the architecture: order follows actual dependencies and cheap useful evidence.

## 5. P0–P3: make anatomical information available before paying again

### P0 — start from the actual state

Ground by §0, which carries the reading this task listed: the five required primary documents
in AGENTS order with their proof pictures; the MAP from §0 (§§0/8.8 and its latest accepted
record); TARGETED_ANATOMICAL_COMPUTE; the full anatomical-priors conversation; this plan and
NEXT_SESSION_PROMPT; and the primary text
`../cell_tracking/docs/pipeline_thesis/paper/what_an_object_is.md` §§4, 7, 13 and
`/Users/rohanvinaik/Projects/rohan-vinaik.github.io/papers/Core Documents/SIGNIFICANCE_WEIGHTING.md`.
Read whole logical units, never text-search fragments; archives stay invisible.

Check git state and workers, verify the accepted source manifest, and inspect the preserved
run invocations before running anything. All three continuation helper tasks completed; no
pending worker result needed polling at that historical checkpoint. For live jobs use only the
active packet's job table and verify the actual handles. No preview is accepted production. Read every candidate
unit before copying it. Generate a fresh object/view inventory from receipts and maps under the
actual source pin; separate resolved native, native reading, laid, projected, trace and refusal.

### P1 — finish the ready sartorius scope candidate

Packet: B + `sartorius-scope-max-20261018/attempt-3-text-only/`.
Read `candidate-verification.json`, `candidate-test-history.json`, complete
`candidate/review-units/` and `candidate/focused-tests-final.log`. The isolated corrected
candidate passed 39 focused tests and Ruff at that isolated development checkpoint. The subsequent
P1 production acceptance is recorded in commit `19967cd` and B + `p1-sartorius-scope-20261018/`.
The procedure below explains that increment's mechanism and checks; it is not an open-task
instruction to repeat it. Use §13's active packet for the current task.
Use the corrected candidate, not the original answer.md as an automatic patch.

Chosen mechanism: project gracilis once; `source_window` bounds the search around the actual
in-object target using full window span `2 * (target_span_mm("sartorius") + GRACILIS_REACH_MM)`
with the existing 10 mm reach.
The source is not the body's centre. The existing 20 mm surround and native 3×3 smoothing add
context. Compute local contrast there before the old grey-body selector, preserving its rule,
thresholds and ties. Keep every computed context output, query mask, availability/finite masks,
window/offset and local status. Unqueried exterior is unknown.

Production edit boundary: `name_sartorius` in the runner; `sartorius_on_slice` and scoped helpers
in assignments; meaningful driver/unseen/scope tests. Check callers first; avoid a new objects-to-
collapse top-level import cycle. Declare retained fields and actual read/visit counts. One
projection and one scoped contrast request through the real caller are required. The saved
driver test asserts one projection but only a nonempty contrast-call list; strengthen it to
assert exactly one contrast request during integration (the direct selector test already does).

Run proof/bursa and public no-draw, inspect the real proof output, reconstruct context/support
addresses, run the gate. This changes scope; no whole-frame equality requirement. Keep the old
188-pixel competent sheet visible or explain a changed competent description from the image.
A smaller visited area alone is not a runtime speed claim.

### P2a — shared rough leg/domain producer — OPEN, required

Rohan's correction during the overnight build: a useful prior is sufficient, not an exact skin
boundary. Do not turn this required efficiency step into a perfect-envelope prerequisite or stall
the full build on a mask-quality target. Demonstrate useful exclusion through the actual consumer,
retain uncertainty, and continue. This applies throughout the pipeline, not only to P2a.

The existing `p2a-leg-domain-20261018/` experiment tested only a 10 mm-padded bounding rectangle
around two candidate envelopes. It did not implement or evaluate tile-level execution, measure
work over an irregular leg region, or exercise such a region through a production consumer.
The broad rectangles and the leaking flood are observations about those constructions only.
The assertion that a tile version would have the same failure is withdrawn as unsupported.
Commit `398b856` records the earlier overbroad dismissal; its message is historical error, not
permission to skip P2a. The packet README now states this correction explicitly.

Next bounded P2a packet: keep the actual candidate region or tile occupancy separate from its
padded enclosing box; inspect it against the acquired anatomy; retain unknown and enclosed dark
tissue; combine available complementary context where the first construction fails. Count the
actual query places/tiles and operation-specific context needed by a chosen real consumer.
Demonstrate useful exclusion or a useful downstream anatomical constraint, then connect that
producer before the expensive work. Count real visited work, not only the box. If a consumer
requires a broad envelope, record that consumer's scope without ruling out other consumers or
representations. This specifies the work, not a new threshold or a perfect-mask prerequisite.
P2b/P3 may proceed independently; P2a remains on the required build list until this is done.

Reuse already computed finite/margin/background/squint data before the middle-slice expensive
lens. Produce a useful per-slice or per-tile leg envelope and available scope, not a perfect leg
segmentation. Surrounding exterior connectivity, filled envelopes, nearby slices and known bone
context can keep dark internal tissue eligible. The precise simple construction must be checked
on raw proof/bursa pictures before implementation; this plan does not declare one thresholded
tile mask an anatomical truth.

Put the producer in the existing input/collapse path. Pass its scope into the expensive callers;
masking a full-frame result afterward does not complete this task. Preserve the measured tiles,
finite/unknown/clipped states and actual visited window. A broad/full-frame result on one scan
is allowed and honestly counted. No fabricated consumer for an unused tile statistic.

Test dark tissue enclosed by brighter leg tissue, clipped scans, no/partial signal, nonfinite
values, anisotropic/ragged tiles and malformed geometry. Inspect the native crop with tendon,
cortex and subcutaneous tissue visible. Do not spend another full anatomical lens just to obtain
the bound intended to precede that lens.

### P2b — later native bones feed dependent native questions

**Read §1.2 and the concrete producer–consumer contract in §14.4 before changing seed selection
or calibration.** P2b publishes what the later native
sections actually supply and makes it usable by downstream questions. It is not a campaign to
improve AX14's coarse-core mask or restore an earlier calibration/rim count. The reported
74.5→71 and 63-pixel difference do not by themselves establish an accuracy regression.
If projected support is being mistaken for native marrow, repair that semantic distinction at
the real producer/consumer. "Marrow within bone" alone does not justify a universal 2 mm erosion.
Any `prototype_interior_seeds.py` or comparison of variants remains development evidence until
its measurement meaning, general anatomical justification and real consumer are established.
No source/seed variant is accepted merely for producing preferred intermediate numbers.

Read E + `later-bone-context-trace-20261018/README.md` and the actual complete units:
`Leg`, `leg_of`, `leg_on`, `name_the_bones`, `keep_bone_planes`, `bone_target`,
`native_femur_coarse_context`, `coarse_section`. Lead traces references before changes.

The packet verifies early AX14 seeds of 170 femur/0 tibia and a separate comparison-only
projection from later native regions of 415/39. The latter is not current runtime behavior or
proof of exact anatomy. Publish validated, addressed native bone physical supports once when
known. Retain their acquisition, plane, scope and interpretation; do not silently union broad
bone territories into a perfect surface. Share that new context with coarse/native readers and
calibration. Preserve early bootstrap context for consumers that run before this producer.

Give updated support context an immutable identity/version; include it in `leg_on` and every
coarse/profile cache that depends on it, or explicitly invalidate those entries. Previously
cached early projections must not survive under a new bone context. Verify same frame + different
context misses, same complete context reuses, and ordering reaches the intended later readers.
Inspect AX11/12/14 and affected cartilage/fat outputs through actual DICOM frames for reasonable
anatomical competence and faithful representation. Neither more seeds nor a cleaner core alone
establishes a better implementation; retain scope and uncertainty instead of optimizing a mask
in isolation. No repeated whole-study recognition/fixed-point loop.

### P3 — pass known bones into patella/recess questions

Increment 1's location handoff and explicit recess reference-sample provenance are recorded in
MAP §8.41 and its B1 evidence record. The work below still includes native calibration sharing
and bounded patella/cavity execution; passing refined locations alone does not complete P3.

Read `patella_plane`, `patella_scope`, `recess_anterior_plane`, `lens_of` and their real callers.
Currently the patella reader includes both bones' footprints and names them again to obtain
context/calibration. The recess calls the patella reader with no bounded window. Replace
rediscovery with supplied usable native/shared bone context and sequence-specific marrow light.
Then bound the patella corridor and the cavity between its posterior face and anterior femur
before expensive measurements. Shared supplied context must retain its provenance and uncertainty.

Share a same-slice reading when inputs and scopes really agree. Do not compute different
contexts under one cache key or pretend one crop is an exact subset of another's watershed.
Keep local miss, missing context, incompatible context and broadening distinct. Broaden for the
specific unresolved prerequisite; do not unconditionally run the full-frame path after a local
success. Check every patella/recess route, not only one direct caller. Inspect resulting native
support and later guide use; count added fallback work as well as saved work.

## 6. P4: finish the compartment residual from actual anatomy

First apply general source eligibility to source-consuming families: native/addressed usable
support, appropriate acquisition, and the anatomical region/attachments that make it that object.
Largest area may choose among eligible sources; it is not identity. PCL's notch relation must
exclude calf, distal cortex and image-edge sources without UID-specific rules. Uncertain context
gets a named unresolved outcome, not fabricated correctness. Preserve previous wrong-run history.

| Missing capacity | Anatomical question and shared context | Existing development checkpoint; next lead decision |
|---|---|---|
| ACL axial, then coronal | Heterogeneous ligament in the notch, between its tibial intercondylar and lateral femoral attachment regions; distinguish PCL/cortex/fluid by course and neighbours. | B + `acl-native-preview-20261018/`. Actual source is native SAG-FS z19 in main-layer output, not laid non-FS or a refused middle row. Individual frames and original enclosure/body previews exist at AX14/COR18. Largest body is often PCL/cortex; neither source contact alone nor PCL's uniform-dark rule resolves ACL. Readable pictures plus improved native bone/notch context must settle the few lens relations before a builder implements them. |
| Tibial axial cartilage | Articular layer on the plateau facing the femur, distinguished from cortical shaft/spine, meniscus and free fluid by its surface relation. | E + `tibial-axial-current-preview-20261018/`. Keep accepted SAG/COR descriptions and their visible overreach. The trial most-superior strip follows the tibial spine; the unique coronal-contact AX11 component is not accepted competent cartilage. Improve native plateau/bone context; do not promote uniqueness or a selected index into identity. |

Use existing local measurements or add one objective complementary measurement if the pictured
anatomical distinction needs it. Do not perform threshold/lens sweeps until a desired contour
appears. Capture the lead's plain rule and provenance before mechanical implementation.

The ACL source is produced late in `measure_study`; an adapter cannot consume it before it exists.
Reuse the in-memory main result at the real producer boundary, offer new native observations
before their later consumers, and preserve the existing single persistence path. Map/profile
expectations and actual slab support remain distinct. Off-plane PCL projections locate course
context; they do not claim native PCL pixels in that ACL slab.

Stop each object/orientation when a competent generic native description is demonstrated once,
with named uncertainty and real production output. Do not perfect the accepted menisci/PCL.

## 7. P5–P6: remaining native families, one anatomy decision at a time

P5 evidence is ready at B + `attachment-native-frames-20261018/`: five validated sources,
16 candidate native frames, 21 figures, no final tissue selector. Its observed indices are
inspection addresses only. They must never become production constants.

| Family/object | Missing native views | Structural starting question; share these values |
|---|---|---|
| MCL | SAG (AX local band: MAP §8.44) | Medial band outside medial compartment, femur to proximal tibia, deep to pes structures; known medial meniscus and joint line. |
| LCL | SAG, AX | Lateral cord femur to fibular head; separate from medial popliteus and posterior biceps; use existing head/attachment context. |
| Popliteus tendon | SAG, AX | Tissue in lateral femoral sulcus, medial to LCL, following its course; reuse measured concavity and native bone relation. |
| Iliotibial band | SAG, AX | Superficial lateral fascial band deep to subcutaneous fat, passing femur toward proximal tibia; reuse fat/skin/relative-minimum context. |
| Biceps femoris tendon | COR, AX | Posterior-lateral tendon from muscle toward fibular head, beside the LCL; preserve overlap limitations at conjoint insertion. |
| Both gastrocnemius heads | SAG, COR | Muscle bellies posterior to their own femoral condyles, separated by fascia; distinguish heads using physical sidedness and notch. |
| Semimembranosus | SAG, COR | Posteromedial tibial attachment and substantial tendon body; axial source and trace locate a longitudinal native question. |
| Semitendinosus | SAG, COR | Separate cord posterior to semimembranosus, continuing toward pes region; reuse their joint local dark-body readings. |
| Gracilis | SAG, COR | Thin medial/anterior neighbour of the posterior tendons at the relevant level; use its actual source, not distal insertion order at every height. |
| Sartorius | SAG, COR | Medial/anterior grey muscle sheet relative to gracilis; share bounded lightness/muscle context and anatomical level. |
| Popliteal artery, vein | SAG, COR | Lumens in posterior inter-head corridor, artery anterior to vein; native contrast/flanks and course distinguish them from tendon/fascia. |
| Gastrocnemius–semimembranosus bursa | SAG, COR | Fluid pocket between its named neighbours; use the known visible bursa study. Neck/wall/full course are not this local-body prerequisite. |

For each row:

1. Read its complete RESOLVING definition and source paragraph. Validate the native source address.
2. Reuse cheap physical profiles, map guide and available neighbours to choose candidate planes
   and useful native windows. Use each acquisition's own slab thickness/spacing/frame.
3. Inspect acquired images and separate complementary measurements at native pixels. State the
   smallest general rule explaining the pictured anatomy. A trace remains a pointer until native
   evidence settles the body. A longitudinal description need not mimic an axial cross-section.
4. Give that exact rule and named refusals to a bounded builder. Reuse existing geometry,
   enclosed-body, minima, field and contrast producers; avoid a copied 500-line family adapter.
5. Retain native observations plus original laid/projected/read/refused rows. Update the common
   map before dependent searches; persist through the existing writer. Validate actual pictures
   and addresses, run appropriate tests and the gate, record acceptance, then take the next row.

The lead's anatomical/image decision remains necessary where no rule is chosen yet. The build
around it is mechanizable. A new agent must not invent an unapproved rule and call that mechanical
execution, nor ask Rohan to repeat the established thesis as a substitute for looking.

**How each rule is decided (Rohan's choices, 2026-10-18).** The lead put the question to him as
options; his choices and words are recorded verbatim in
`docs/conversations/2026-10-18-build-session-corrections.md`. At 16:57 UTC he chose the option
"Codex check only"; at 17:15 UTC, after a side note that a model-only Codex cannot see the
pictures, he chose "Codex + Fable", having written «Yes, change that, Codex is the main consult
interface». For the P4–P6 pictures he chose "Each family wave" (11:25 UTC). For every row of P4–P6:

1. The lead drafts the rule from the native pictures with §1.2's three statements (what the
   producer and consumer mean; the anatomical fact seen in the native images, separated from any
   number; why the operation follows from that anatomy).
2. Codex, the main consult interface (model-only, `codex-consultation.md`), checks it against the
   thesis. Every prompt carries the complete proposed rule, its governing theory/correction/contract
   units and the actual evidence being discussed as text; file paths alone are not inputs. This
   review route must not depend on file or image access. Record the exact rendered prompt and
   response. An answer that could not read its required inputs counts as no review; repair the
   payload and obtain the substantive reading before treating this step as complete.
3. The Fable consult, the only route that takes a picture
   (`~/Projects/SquishOS/ops/agents/bin/anthropic-consult --prompt <file> --image <png> --out <md>`,
   `anthropic-consultation.md`; it spends API credits), is shown the rule's picture sheet and asked
   whether the pictured anatomy supports the rule.
4. A rule both readers agree with is built without waiting for Rohan; any disagreement goes to him
   before building.
5. The lead inspects every view and records its reading; Rohan sees each family wave's pictures
   together at the end of that wave.

A row's evidence keeps the draft, the Codex prompt and answer, the Fable prompt, picture sheet and
answer, and the picture packet the rule rests on. Each reader is one voice, never a verdict.

## 8. P7–P10: finish the whole-operation structural retrofit

The whole-operation efficiency packets in §16 make this work concrete from the full-run probe.
They refine P7/P9/P10 and their verification, preserving this order and the anatomical contracts.

### P7 — apply domains to all older consumers

Trace every expensive operation in the no-draw runtime. In addition to P1–P3, cover fat-pad
candidate reads, own-slice ACL/LCL/biceps/retinacula, joint/tendon planes, native axial territory,
posterior lumen/corridor work, full-frame muscle opening and the three `dark_bands` callers
(`assign_plane`, `twin_reading`, `joint_plane`). Shared context and filter halos must precede work.

E04 facts at B + `structural-retrofit-next-20261018/` show why one proposed shortcut is wrong:
the initial non-FS call has no laid patella yet. A padded bone-only box clips the accepted
extensor chain. Bone plus later patella would contain it but is unavailable at that caller.
The filled leg box covers the whole proof frame. Use a legitimately available course/corridor
or retain the broad bootstrap; do not claim a reduction by changing the accepted question.

Each expensive caller must have an explicit consumed anatomical scope or a specific recorded
reason it legitimately needs broader work. Audit downstream callers too: a smaller first read
followed by a redundant broad one can lose the whole-pipeline benefit. Distinct scope can be a
useful new reading; it is not automatically a cache duplicate.

### P8 — every concept, contained tissue and output semantics

Regenerate the catalogue from production definitions and receipts; join it with the anatomy
source document. Account for all 43 existing concepts plus explicit bone-associated marrow,
without treating a target count as completion. Keep generic meniscus/cartilage/general recess
slots distinct from sided/surface-specific observations. Audit the articular-surface coverage
requested by the domain document, including patellar-facing anatomy; record any unrepresented
requested description rather than silently claiming the current two cartilage names cover it.

Expose marrow as the retained inside support associated with each named bone, with an actual
source address and the existing calibration relation. It does not need an independent invented
reference point. Air, skin, subcutaneous fat and general muscle remain diffuse fields, with
native masks and named map limitations. The semantic `recess` slot does not imply a newly
measured structure. Local walls/lining do not claim histology, membrane thickness or full envelope.
Every requested object/view has either a native competent demonstration or an explicit remaining
slot; a per-study refusal is always emitted when its prerequisites are unavailable.

### P9 — shared values, honest lineage and retained persistence

- Make observation conversion/offer lineage generic over the real family call, replacing the
  four-family hardcoded declaration. Do not mark support bitmaps read when only metadata is used.
- Record actual consumers where a value influences identity, slice, scope, source eligibility,
  calibration or later map use. Retained diagnostic values stay honestly unread. Separate them
  from accidental waste rather than deleting them to make the ledger green.
- Reuse source-to-slab profile construction where mathematical semantics match; translate
  family status codes explicitly so old saved numeric codes keep their meanings. Invalid
  thickness, unavailable projection and measured-empty are different outcomes.
- Centralize genuinely identical profile merges, frame scalar-axis coordinates, margins and
  tile reductions. Respect the different 10 mm squint and 2 mm coarse-block questions.
- Cache keys include full acquisition/slice, native scope, source/context identity, geometry,
  parameters and measurement meaning. Compute immutable support digests once at their producer;
  do not rehash identical bones for each plane. Verify mutation/context invalidation boundaries.
- Inspect `gradient_magnitude`, `gradient_facts`, `PatellaAttempt.field_objects`, atlas fields,
  contracts and `relative.unusable_frames` against actual references. Do not delete retained
  computed information or a module with live production consumers. Retire proven redundant
  uncalled code only after reference and contract checks.
- Separate persistence cost from recognition. Reuse already computed digests and avoid repeated
  materialization/serialization; any codec/storage improvement must be lossless, reconstructible
  and checked across consumers. No array dropping or hidden retention policy change. W8b must resolve
  actual competition storage capacity under §16.9 before closing; a known overflow is not an advisory
  that can be left to packaging. Lossless layout/placement changes update all real readers and addresses.

### P10 — remaining hot kernels

Reprofile the real operation after structural changes. Optimize only residual material work:
peak finding/sorting, band medians, physical-disc morphology, histogram or native fat sampling.
A library operation is already native code; replacing it with JIT is not inherently faster.
Use project tooling and a reference twin. Pin finite/unavailable behavior, border/reflection,
anisotropy, discrete radius, dtype, shape, tie and categorical semantics. Preserve partial/ragged
tile behavior already accepted in the squint. No fastmath that changes decisions.

Measure cold compilation separately from warm production, record total visited pixels/windows,
requests/misses/handoffs, fallback work, retained bytes and time/memory. Equivalent optimizations
need same-output comparisons and paired measurements; scoped builds need explicit change
adjudication plus competent images. Do not infer speed from area reduction or compare isolated
profile seconds under different machine load.

## 9. Mechanical packet, tools and acceptance contract

Before each edit the lead uses Serena references and whole functions to find producers, every
caller and sibling route. Check fresh indexed bodies against actual files. Aider is read-only;
the installed unrestricted mapper can expose archives, so use an archive-excluding invocation
or active-source AST inventories instead. Helpers do not start separate Serena fleets.

Each task packet contains the concrete M/F/task contract references from §§14–15, not only
a generic request to improve the result. Its completion record supplies the six statements in
§15.3. Each task packet contains:

| Field | Required content |
|---|---|
| Intent | Human specification, chosen plain anatomical rule, primary references; worker may not reinterpret it. |
| Inputs | Full source units, source hashes, native data addresses/geometry and relevant image packet. |
| Ownership | Exact allowed files/functions; runner belongs to one integrator. Independent candidates use isolated copies. |
| Contract | Named inputs/outputs, actual next consumer, scope/cache identity, unavailable/tie/refusal meanings, retention. |
| Work | One bounded implementation or factual audit, no generic framework, threshold search or archive access. |
| Verification | Focused adversarial tests, exact real-CLI integration point, picture/address checks, expected output changes. |
| Return | Complete code units or patch, imports, tests/logs, hashes, remaining uncertainty and model usage. |
| Stop | Specific completed packet; no self-assigned next mechanism or unsupported anatomical verdict. |

Use the existing ledger/once/Measures and source-owned graph. Hamilton can inspect a graph
where already applicable; no new orchestration engine or Kedro migration is needed to satisfy
this plan. Static references plus actual runtime calls establish whether values are shared.

Read `scripts/ci_local.sh` and its current configuration rather than copying a remembered gate.
It runs, from the locked environment, Ruff, format, the tests under coverage, zizmor on the workflows,
Import Linter, advisory deptry/ty, Ruff's PERF and stable FURB rules, two Vulture scans and the kernel
costs (`benchmarks/`: each costly kernel's costliest call from the production run on the proof study,
recorded in `benchmarks/recorded/` by `benchmarks/record_calls.py` and replayed exactly without the
study data, with memray's memory at the peak and a failure when a replay holds more than at its last
run on this machine), and a Sonar check that blocks only on an open bug or vulnerability and prints its
quality gate, smells, coverage and duplication as information (`scripts/sonar_local.py gate`; Rohan,
2026-10-18: «don't over-fit to targets, only bare correctness issues should be blocking»); the same gate
runs on GitHub on every push (`.github/workflows/gate.yml`; Rohan, 2026-10-18: «Sonar should be part of
the CI gate for this project, and a full CI gate should also run upon push to github»), and the kernel
benchmarks run there under CodSpeed's CPU simulation and memory instruments too
(`.github/workflows/codspeed.yml`), compared commit to commit as information. Read all advisories; a
passing blocking gate does not clear them. Use Hypothesis for geometry/cache/lossless
properties, Detective and CrossHair for suitable pure decisions/contracts, not to certify anatomy
from test counts. CrossHair must actually report checkable contracts; silence is not proof.
Use project-interpreter cProfile/VizTracer or another available instrument against the real entry
point. Account for trace sampling/worker blind spots. No tool installation spree is required.

For every production increment:

1. Freeze relevant source before the run; retain source hashes, exact argv, environment/backend,
   input identity, completion status and untruncated logs. Keep failed/corrected epochs separate.
2. Run proof and visible-bursa studies with drawing off into **new output directories**, then
   public test through the same CLI. Compare ordinary/serial/parallel behavior where affected.
3. Reconstruct each new native support from its addressed artifact/array/row/offset/shape/slice;
   verify count, dtype, label semantics, frame and actual DICOM pixels. Inspect all changed native
   frames and source supports. Owner artifact's middle image may not be the addressed slice.
4. Compare receipts/digests, observations, categorical prefixes, maps and guides against the prior
   epoch. Equivalent changes must match. Scoped or semantic propagation changes get a complete
   named adjudication of changed/unvisited rows and downstream effects, not a false prefix pass.
5. Exercise empty/malformed/nonfinite/boundary input, missing knee side/source/geometry,
   different sequence dimensions, oblique slabs, ties, map disagreement, clipped contexts and
   measured-empty versus unavailable. Check all real sibling routes and the single save point.
6. Write everything the checkpoint commits before its final gate, and change nothing tracked after it.
   When the increment changes a benchmarked kernel or what the production path hands it (its caller,
   scope or arguments), refresh the kernel benchmarks' recording from the integrated source first
   (`.venv/bin/python benchmarks/record_calls.py`, one more run of the proof study), so `benchmarks/`
   replays the current calls: the gate replays the stored recording and never refreshes it, so a
   recording refreshed after the gate would be committed without being replayed. The first gate after a
   refresh compares a different call, so its advisory memory figure is information, not a regression.
   Record the mechanism, accepted image and source/run evidence in the dated RESOLVING/MAP acceptance
   record; update detailed remaining work only in §13's active packet, which points to the final gate's
   log under `data/` instead of carrying its numbers. NEXT stays a pointer card. Then run the full gate
   on exactly that tree and read its whole output and advisory lists; an earlier gate run during
   integration is diagnostic only. Commit exactly that tree with explicit paths: the gate stamps the tree
   it passed on, and after a later edit, or with a file left out of the commit, the pre-push hook runs the
   gate again on a clean checkout or refuses a checkout that is not clean. Push the checkpoint before the
   next production integration wave; independent private implementation continues meanwhile (§4). Git runs the pre-push hook (`scripts/push_checks.py`: the gate unless it passed on that
   tree, the secret scan, and the advisory lockfile audit); read its whole output, then the GitHub gate
   run on the commit, whose results go into the next revision (Rohan, 2026-10-18: «just freaking commit
   to git»; «Set it as an automatic hook»; HOW_TO_BUILD, "Commit and push, 2026-10-18").

## 10. Local Claude Max implementation route

Rohan explicitly authorized the source/measurement handoff and requested the **local CLI**:
«I am providing that approval, but more importantly I want you to use the local CLI path.»
Use one explicit route per job: tool-enabled in-session helpers reconstruct images, trace source,
run isolated tests and check addresses; workflow agents (Sonnet, xhigh effort), each in an isolated
git worktree, return bounded implementation candidates under `docs/work/current/BUILD_WORKFLOWS.md`
(Rohan, 2026-10-19: «Good. I approve, continue setting this up»), and the text-only
subscription-authenticated Claude Max route below stays recorded for a text-only candidate;
model-only Codex provides independent text review; Fable over the Anthropic API reads picture sheets. The Codex consultation route receives no
implementation work and is not an evidence/test runner. Tool-enabled session helpers are a
different capability, not a promise that a model-only consultation can open files or images.
Lead retains meaning, rule selection, production integration and visual acceptance.

A working recipe is preserved in B +
`sartorius-scope-max-20261018/attempt-3-text-only/{launch.py,invocation.json,system_prompt.txt,empty-mcp.json}`.
Read those whole and create a **new task directory/invocation**, never overwrite that attempt.
The local executable is `/Users/rohanvinaik/.local/bin/claude`. Verify current authentication with
its local auth status: `claude.ai`, `firstParty`, `max`; never print tokens or export credentials.
Keychain isolation can make a sandboxed launch falsely report not logged in. The successful
launch used the normal permission-reviewed host access; do not bypass an approval rejection.

The successful text-only route replaces the default CLI system prompt, supplies all needed
whole code units in stdin, disables tools/MCP and saves complete result/stderr/usage/completion.
Its flags include `--safe-mode --strict-mcp-config --mcp-config <empty-config>` with
`{"mcpServers":{}}`, `--setting-sources "" --tools "" --disable-slash-commands --no-chrome
--no-session-persistence --permission-mode dontAsk --model sonnet --effort medium
--output-format json --print`. `--system-prompt` contains the literal text-only worker contract,
not a filename. Read the recorded argv rather than reconstructing shell quoting by guess.

The child environment removes API-key/base-URL overrides and CLAUDECODE. No API fallback.
Without the replacement system prompt, attempt 2 emitted unavailable Bash/Glob tool markup and
no implementation despite exit 0. Such text is failed output, never an executable instruction.
Attempt 1 sent zero tokens because keychain auth was unavailable; attempt 3 returned code.
Validate result substance as well as exit status. Record subscription token usage; a CLI list
cost estimate is not evidence of an API charge. Do not keep retrying the same stalled prompt:
inspect completion/logs, distinguish authentication, capacity, malformed output and actual work,
correct the specific cause and preserve each attempt.

For a genuine conceptual question, save the lead's independent reading first and ask a narrow
second reader with the human's words and complete relevant units. Prior Fable consultations are
already retained; do not repeat one to obtain endorsement. An advisor never changes the thesis.

## 11. P11: verify the completed recognition operation

Use the same production entry point. These commands use fresh directories; choose a new name
if they exist. The root below is the local data mount, replaced by the kernel mount in production.

```bash
.venv/bin/python scripts/run_interiors.py --study-uid 1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149 1.2.826.0.1.3680043.8.498.13335129881737731410081002627729200903 --root data/raw --workers 1 --run data/measurements/recognition-final-serial/interiors --main-run data/measurements/recognition-final-serial/main
.venv/bin/python scripts/run_interiors.py --split test --root data/raw --workers 1 --run data/measurements/recognition-final-public/interiors --main-run data/measurements/recognition-final-public/main
.venv/bin/python scripts/run_interiors.py --labeled --root data/raw --workers 2 --run data/measurements/recognition-final-cohort/interiors --main-run data/measurements/recognition-final-cohort/main
bash scripts/ci_local.sh
```

For development images add `--draw` to a separate specified-study run. Production has it off;
no drawing-only imports/borders/consultation/cohort-calibration work belong on that path. Replay
the saved serial argv with workers 2 and distinct destinations to check parallel output. Copy
baseline receipts aside before changes; use `scripts/compare_receipts.py` for their actual
contract, with `--borders-aside` only when comparing drawn versus undrawn output.

Compute the current labelled study count; historically it is 58, not an assumed constant. Run
all supplied studies once per accepted family wave or final checkpoint, not once per tentative
rule. Use the existing pair-vector reports for observed range and sample SD; n<2 keeps SD
unknown. No statistics create the anatomy map or fit selectors. Empty/partial pairs remain in
the report. Profile and ordinary runs must give corresponding output under the same source pin.

Recognition completion requires:

- Each requested concept and native orientation is accounted for, with a general description
  competently demonstrated once and linked to actual inspected evidence; diffuse/contained
  concepts retain their appropriate representation. No universal study success requirement.
- Per-study output preserves native/laid/projected/read/refused distinctions, original decisions,
  source geometry and support addresses; every object has a result or its specific uncertainty.
- Key-plane constraints construct the reference; all ordered pair vectors have resolved or named
  partial endpoints. The same map points each acquisition to its own expected slice and region.
- Available anatomical facts actually constrain later source eligibility, identity and compute
  scopes. No expensive independent whole-image rediscovery where useful context already exists.
- Every measured value has a real consumer or an explicit retained-evidence purpose. Caches share
  identical contexts, source pins reproduce outputs, serial/parallel agree, and advisories are
  adjudicated. Whole-pipeline costs/fallbacks are measured honestly.

Report identified / abstained / wrong **per object and orientation**, with uninspected cases
explicit. Coverage and position-construction checks are not clinical accuracy. A green gate,
complete pair count or many worker tokens cannot replace native-image acceptance.

The efficiency completion record is §16.5: compare equivalent outputs, account for the whole
operation and its retained evidence, and report ordinary RSS separately from tracked allocations.
A kernel replay alone does not complete this part of P11. W10 also satisfies §16.9: integrated offline
recognition under the selected CPU/RAM/storage limits, complete startup-to-output costs, measured
workload and explicitly projected hidden-scale capacity, W8b storage closure rechecked, and recorded
headroom for later supplied stages. A known overflow or required missing capacity check prevents
completion; a green correctness gate does not waive these deployment requirements.


## 12. P12–P13: representation and eventual competition completion

The author's exact-HDC and structural-information clarification is preserved verbatim in
`docs/conversations/2026-10-19-structural-information-and-exact-hdc.md`. Read it before P12:
the bounded relational anatomy constitutes the objects, and representing that structure removes
proxy inference/uncertainty/compute. Efficiency is inherent, not an optional optimization after
the representation is built. Healthy anatomical zero and the intended healthy profile have the
same reference here; missing/unread information is distinct. The MRI adapter, reference-source
contract and parallel construction order are in `docs/HDC_ENCODING.md`, subordinate to this plan.
Rohan authorized sourcing missing healthy-profile facts from open medical reference texts. That
does not authorize replacing their quantities with scan percentiles or invented raw-intensity
limits. The current task packet owns implementation status; the interface note is not a queue.

P12 follows the author's exact idiom, not textbook approximate HDC. What an <Object> Is §7 and
§13 specify independent banks, seeded exact Sylvester–Hadamard rows, whole-number row counts,
exact additive/subtractive bundles, versioned layout/carrier and explicit silence. A profile is
a bundle of places; a bundle of bundles is a bundle. Original values, footprints, positions,
depth and geometry remain beside the encoding. Write from retained measurements; do not recompute
recognition for encoding. Packed signs may order a scan, not discard cases without an exact bound.

First record the MRI-specific place/depth/bank layout, physical support ownership and overlap
contract from those primary sections. Distinguish full/sparse/cheap readings and zero-versus-
silence. A measured 3D support/volume must follow the retained full encoding/extent mechanism;
three key planes or an extruded representative footprint are not a volume measurement. Do not
sum overlapping views of the same tissue as independent volume or substitute an arbitrary mesh/
area-times-spacing rule. If the MRI-specific step is not specified by the primary contract,
bring that concrete gap to Rohan after preparing the input/output contract; do not invent it or
make it block recognition completion. Test exact bundle/decode/subtraction, order invariance,
layout compatibility, silent banks and physical support ownership before integration.

P13 is an explicit human-specification dependency: Rohan has deliberately not yet specified the
later AI accuracy/completeness and diagnostic mechanics. Record the ready typed object interface
and the twelve anatomical condition relationships already documented. Implement his supplied
mechanism when given; do not fill the gap with a model, weighted score, generic classifier or
new diagnosis heuristic.

Rohan clarified on 2026-10-19 that the endpoint is a verdict/diagnosis, and that the current
stand-in may report pixel bundles for each object's identity. The complete direct exchange is
`docs/conversations/2026-10-19-completed-study-lifetime.md`. Finish recognition by publishing each
object's identity and actual addressed pixel supports, preserving native readings, uncertainty and
unavailable states. This stand-in is the current per-study output boundary; diagnosis replaces it
when he supplies that layer. It does not require inventing the MRI-specific HDC layout, diagnostic
rules or competition probabilities. Release completed-study working data after the configured
output consumer has finished (§16.6). His following clarification makes the handoff natural:
diagnoses concern unnatural or damaged states of these identified objects. Their pixel bundles
are therefore the direct starting input for the later diagnostic layer, alongside their retained
identity, geometry and anatomical relations. Recognition need not be repeated to begin diagnosis.

Then package the same no-draw runtime for Kaggle, with runtime-only dependencies, fixed references
and the provided mount. Match the actual sample/gold schema for one study's twelve probabilities;
never serialize internal observation rows as a substitute. Verify public inputs, empty/missing
inputs and recheck the real competition budget using the current official contract at that stage.
W8b storage closure and W10 compute-envelope verification already happen under §16.9; adding the
actual P12/P13 work triggers a new whole-notebook check, not the first capacity assessment.
Submission/publication is a later requested action. Recognition capacity is a concrete completed
milestone before that dependency; do not label the whole competition solution complete early.

## 13. Context-stable continuation and stop points

**Active task ID:** `THIN-OBJECT-BOOTSTRAP-20261021`.
**Active packet:** [docs/work/current/README.md](work/current/README.md).

This section is the only active-task index. The named packet is the only populated current-state
record: request, source basis, accepted checkpoint, next action, open work and the job table all
live there. NEXT_SESSION_PROMPT and the guide point here; they do not copy its state. Worker
attempt directories retain immutable inputs/results/logs and do not constitute a competing live
queue. Update this task ID and packet pointer together when the lead changes the active task.
A historical packet's completion never dispatches a new task by itself.

This file remains the complete remaining-work order; EFFICIENCY_RETROFIT_PLAN retains issue
history; MAP holds dated accepted mechanisms and source pins; RESOLVING holds anatomical
definitions. Do not create another master plan. The former populated checkpoint and NEXT are
preserved verbatim in `docs/history/CONTINUATION_STATE_2026-10-18.md`. They are history, not
current instructions. In particular, superseded non-acceptance or early-cache descriptions must
not restart completed work. Continuing corrections and contracts elsewhere in this plan remain.

### The single handoff template

Populate this template only in the active packet. The guide's grounding, job supervision and
pause procedures use these same fields. References to full evidence may be used instead of
copying logs or primary documents. Distinguish inherited acceptance records from new checks.

```text
TASK ID / PACKET REVISION / STATE:
CURRENT REQUEST / AUTHORITATIVE EXCHANGES / ACTUAL AUTHORS:
SOURCE HEAD / DIRTY UNITS / MANIFEST / INPUT IDENTITIES:
OWNER / PERMITTED WRITES / WORKER ROUTES:
CONTRACTS / INPUT AND OUTPUT MEANINGS / REAL CONSUMER:
NEXT SINGLE ACTION / PROPOSED OPERATION / JUSTIFICATION:
OPEN SEMANTIC CHOICE / PREREQUISITES / OTHER OPEN BUILD ITEMS:
ACCEPTED CHECKPOINT / RUN ROOTS / EXACT COMMANDS / EXIT STATUS:
INSPECTED IMAGE ADDRESSES / RESULT AND UNKNOWN SEMANTICS:
CHANGED OUTPUT ADJUDICATION / LEDGER / PROFILE / GATE ADVISORIES:
WORKERS: <task/attempt, route, owner, handle, dependencies, output root, verified state>
UNREVIEWED / WITHDRAWN / STALE RESULTS:
VERIFICATION STILL OWED / RECHECK BASIS:
HANDOFF TIME / EVIDENCE LINKS:
```

A clean pause has no ambiguous in-flight mutation or worker completion represented as production
acceptance. Check actual job handles and source identities before resuming; an unverified external
job stays unverified. Preserve existing source epochs and all readings. Follow the current human
request; consult the packet for the next build task without treating it as permission to change
the current activity. P12/P13 retain their primary-contract/human-specification dependencies.


## 14. Measurement and consumer contracts

**Added at Rohan's explicit request, 2026-10-18.** These are the meanings and permitted uses of
the existing measurements, followed by the remaining task contracts in §15. They are instructions
for work in the existing plain functions and records, not a request to build a contract engine,
another pipeline, or a new set of scores. §§1.1–1.2 govern every contract.

### 14.1 How a mechanical builder must use these contracts

A task packet names its input and output contract IDs below, exact source units/files, and its
production consumer. The worker implements that transformation. It may not replace the anatomical
question with an easier measurable objective. If a specified input is unavailable, preserve the
named unavailable/partial result; do not invent support or silently substitute another product.
A useful approximate description remains usable with its stated scope and uncertainty.

Three work states are distinct:

- **REUSE:** the measurement/operation already exists. Use it with its current documented meaning;
  do not introduce another implementation or tune its constants to a new example.
- **WIRE:** the required handoff is specified. A worker can implement addresses, projection,
  caching, ordering, persistence, consumer arguments and appropriate invariant tests mechanically.
- **DEFINE NATIVE RULE:** the location and anatomical distinction are specified, but the final
  combination selecting tissue in a missing view has not been accepted. The lead must inspect
  the existing images, write the short rule from anatomy and the lenses, and put it into the
  packet. Helpers can prepare the native readings meanwhile. Do not treat this as permission to
  optimize variants, nor as a reason to ask Rohan to explain the thesis again. No new approval
  ritual is required for ordinary grounded rule construction within the authorized build.

Every spatial product retains its actual acquisition/frame/slice, scope/offset, available and
unqueried places, and source address or derivation. Geometry may be referenced once rather than
copied everywhere. A derived product retains links to its inputs; original readings are kept.
Existing masks/arrays/observation records are sufficient carriers: add only the missing fields
needed by a real consumer. Missing, unknown, measured-empty, tied, partial and resolved remain
named and distinct. A full-frame-shaped boolean array is not automatically a full-frame measurement.

In the tables, **existing consumers** name established code paths, not a claim that every pending
change is accepted. **Required consumers** name the intended remaining wiring. A producer must
not claim that a required consumer is already connected. Source evidence for the inspected units
is B + `measurement-contracts-20261018/source-evidence.json`; the worktree can advance, so check
its actual current units. The plan's contracts do not certify those live edits.

### 14.2 Input, spatial and geometric measurements

| ID / product | Meaning and producer | Existing / required consumer and permitted decision | Anatomical or physical justification | Forbidden substitution / required check |
|---|---|---|---|---|
| M01 — acquired signal and availability | The recorded intensity at an actual voxel, with finite/reconstruction availability. `measure`, `finite_of`, `margin_of` and the acquisition/frame readers own these inputs once. | Every native measurement reads available acquired values; geometry-dependent readers use M02. P2a may use availability as context. | MRI sequence determines tissue contrast. A stored value outside reconstructed/available support says nothing about tissue. | Zero intensity is not globally air. Unavailable samples cannot become dark tissue, background evidence or a negative anatomical vote. Changing excluded stored values must not alter a reading that excludes them. |
| M02 — native frame, spacing and slab | `PlaneFrame`, `plane_frame`, native image shape and actual thickness map voxel coordinates to patient millimetres. `places_on_slice` reads actual slab membership; `projected_places` is a location projection. | `leg_on`, source profiles, native target creation, physical distances, source windows and key-plane geometry. | All series observe one knee in a common physical frame, with different sampling and obliquity. | A projected point is not proof that tissue occupies that native pixel/slab. Do not copy indices between sequences, replace thickness with index proximity, or silently use a different frame. Test oblique/anisotropic, off-slab, missing and clipped geometry. |
| M03 — background split and low-signal class | `background_split` measures the series' own histogram valley; a low map states intensity at/below that split. It is a signal measurement, not an anatomical label. | `lens_of`/`interior_regions`, low-signal band/body readers; required P2a context combined with other readings. | Tissue classes have different contrast, and cortex, tendons and ligaments may all be dark. | Never equate low signal with not-leg. No fitted per-study cutoff to repair an object. Preserve histogram/split scope; a signal-class failure does not retire the anatomical question. |
| M04 — squint stack | `read_squint_stack`/`physical_squint`: each 10 mm tile's exact median/minimum/maximum/coverage, bounds and physical centre per slice. No tile statistic names tissue. | Existing profiles consume relevant grid/geometry; P2a and future cheap search may consume the actual intensity/coverage values. Declare the particular field read. | Cheap large-scale structure can locate plausible anatomical regions before finer questions. | Do not invent a median consumer or assert an unbuilt tile rule failed. Do not require one statistic to recognize an object. Preserve partial/ragged tile semantics; batch reuse changes computation, not values. |
| M05 — useful leg/domain region | Required P2a product from cheap existing readings plus justified complementary context. Its region/tiles, enclosing box and operation-specific halo are distinct values. Construction remains OPEN. | Required input to chosen expensive native reader(s) before measurement; later narrower anatomical domains can refine it. | Relevant anatomy is in the leg; the exterior does not require object recognition. Dark internal tissue is still eligible. | Box area is not region area. An irregular mask applied only after full-frame computation is not a compute-saving handoff. Inspect the actual region, count queried places/context and trace a real consumer. Imperfect but useful is sufficient. |
| M06 — native interiors, distance and territories | `interior_regions` measures distance from low-signal constraints and peak-grown territories inside its declared scope; `Measures` shares named geometric summaries. A territory is a geometric reading. | `assign_plane`, `name_the_bones`, patella/joint/field and other existing selectors combine these readings with anatomy. | Enclosed tissue bodies and their relative positions separate large knee structures. | Largest/deepest is not universal identity. No territory becomes bone merely because a generic function returned it. Preserve local boundary conditions, offsets and scope; drawing-only borders are separate and off in production. |
| M07 — addressed native anatomical source | A source is a named native observation with the exact support array/row, acquisition, slice and its definition's limits. Source-to-LPS conversion records measured source places, not a full reconstructed volume. `native_*_sources`, `keep_bone_planes` and source collectors own it. | Source eligibility, M09 profiles, M10 targets/windows, `refine_leg`, other anatomy-dependent selectors. | One object's observed location constrains that same object and its neighbours in other views. | Laid/projected/read-only rows cannot be silently promoted to independently native evidence. Source choice first respects the object's anatomical region/course; area can distinguish eligible sources, not create their identity. Keep broad-support uncertainty. |
| M08 — projected support / shared bone-location context | `leg_of` and `refine_leg` publish source-derived patient-space places; `leg_on` projects/intersects them into native targets. Later sections add locational information with links to M07. | Existing back-of-knee readers use early context. Required later context reaches `native_femur_coarse_context` and compatible later bone/attachment readers; P3 supplies the relevant context to patella/recess. | Bone positions constrain articular surfaces, contained marrow and attachments. | This is a location prior, not definitive native bone or marrow. Preserve provenance/role, early versus later context and their cache identities. No default erosion, source withdrawal or seed ranking to restore an old calibration. |
| M09 — coarse bone enclosure | `block_medians` → `coarse_depth` → `coarse_section` over native blocks. Depth measures enclosed contrast; seeds locate touched native coarse bodies. Current selection level is derived from held positive depths; competing bone seeds can yield `SHARED`. `native_core` expands that coarse result to the native grid. | `axial_bone_planes`, `fibula_key_planes`, `patella_key_planes`; shared `native_femur_coarse_context` feeds `native_fat_coarse_femur_context` and `native_femoral_cartilage_candidates`. | Bone compartments are enclosed structures whose known physical places point into native bone-related contrast. | An expanded block is not a precise boundary or automatically a marrow sample. `SHARED` is unresolved attribution, not absent bone. The median level/area is a reading, not a value to optimize. Do not tune seeds for core cleanliness. |
| M10 — source-to-slab profiles and candidate order | `native_meniscus_profiles` and the existing cartilage/fat profile builders count/address source overlap through actual slabs and combine it with map proposals. They point to candidate questions. | Native meniscus/PCL/cartilage/fat readers choose which frames to inspect; their independent native support, not the profile count alone, supplies a key-plane observation. | Anatomy is contiguous and physically shared across views, so a known section narrows relevant slices elsewhere. | Profile maxima are not automatic recognition. Retain ties/off-slab/unknown and old status-code meanings. Share geometry only where semantics match; do not merge different status dictionaries by numeric coincidence. |
| M11 — query window and context halo | `source_window` bounds actual source locations using an authored physical extent; filter halo adds samples needed for the specified operation. A source point need not be an object centre. | Local meniscus/PCL/body readers and scoped sartorius; required analogous P3/P5/P6 consumers. | A localized object has a constrained extent/reach; its neighbourhood supplies context. | Do not halve extent by assuming an in-object point is central. Keep query/context/availability distinct. A local miss describes its question, not global absence. A broad window does not invalidate other region representations. |

### 14.3 Local tissue measurements and object-support decisions

| ID / product | Meaning and producer | Existing / required consumer and permitted decision | Anatomical or physical justification | Forbidden substitution / required check |
|---|---|---|---|---|
| M12 — enclosed darkness / native components | `enclosed_darkness` measures darkness below surrounding enclosure on acquired signal. `enclosed_body_at_sources` adds a caller-specified existing body operation, connected labels and source-contact readings within M11. | Vessel/lumen and tendon/body selectors; existing native meniscus/PCL adapters; a future family only after its rule names these measurements. | Dark bodies surrounded by brighter tissue can distinguish tendons, ligaments, lumens or other structures when their anatomical relations agree. | Enclosure alone is not identity. Retain depth, positive class, opened result, labels and selected component as separate readings. A selected body can coexist with partial scope; do not make every unavailable pixel negate it. |
| M13 — physical distance, contact, thickness/body operation | `Measures.distance`, native distance maps, `thick_parts` and named body operations measure reach/scale in their own roles. Existing 2 mm contact/body and 3 mm PCL operations retain their documented meanings. | Menisci between bones; ligament/extensor contacts; lumen/tendon body eligibility; bone/cartilage proximity. | Attachment, adjacency and distinct bodies impose different geometric questions. | A contact allowance is not anatomical thickness or an erosion instruction. Reusing a number does not transfer its meaning. Do not add a shell to purify source seeds without a separate justified measurement role. Preserve anisotropy and exact tie/border semantics. |
| M14 — marrow reference light | `Measures.light` measures median acquired light over the caller's explicit bone-derived native sample support. Retain sample address/meaning, sequence and returned value. The attribution to marrow is the anatomical inference of the calling definition. | Existing dark-band, fat/white-fluid and cartilage relations; `femoral_cartilage_on_plane` receives the callback and declares which native support it reads. P3 passes usable sequence-specific calibration instead of re-naming both bones. | Marrow lies within bone and supplies an in-study tissue reference; sequence changes its appearance. | Neither M08 projected target nor M09 coarse expansion is automatically the native sample. Do not target a particular median or impose a purity/perfection campaign. A declared approximate bone-based reference can be competent; its scope remains explicit. Changes such as 74.5→71 are readings, not accuracy verdicts. |
| M15 — relative tissue contrast / opposed acquisition | Existing cartilage-to-marrow, fluid-to-marrow, fat-to-marrow and physically paired acquired-signal readings, including `relative_signal` and native opposed-fat samples. Retain positive/negative/disagreement/unknown separately. | Cartilage/white-fluid/field selectors; suprapatellar-pad seam; `native_fat_opposed_samples` and fat-pad observers. | Different sequences give complementary contrasts of the same tissues; their physical locations identify what is being compared. | No single ratio decides identity. Keep established relations/constants and their provenance; do not fit them to a desired mask. Unseen/zero-denominator is not negative compatibility. Do not compare unmatched positions or use one sequence's intensity as another's marrow reference. |
| M16 — native fat candidate basins | Shared native physical gradient/IFT candidate measurements and markers in `native_fat_pad_candidates`; source locations, native peaks and coarse bone context have distinct roles. | Native Q/P fat-pad selectors; Hoffa's original territory selector retains its distinct definition. Actual opposed-signal compatibility supplies further information. | Fat pads lie between extensor structures, recess and femur; competing context helps distinguish neighbouring fat. | A gradient basin or coarse marker is not tissue truth. Do not equate smaller/more compact basins with better anatomy. Reuse actual gradient work; retain diagnostics honestly if no later consumer reads them. |
| M17 — local soft-tissue contrast | `local_lightness`/`scoped_local_lightness` read seen native light against seen surround; `muscle_grey_bodies` measures the established grey-body class. `name_sartorius` supplies one gracilis projection and a scoped query. | `sartorius_on_slice` combines body, medial/anterior ordering and existing reach; required future sartorius views must preserve that semantic distinction at their anatomical level. | Sartorius is a muscle sheet relative to the thin gracilis, not another dark tendon cross-section. | Keep raw/context/query/finite/available readings and existing constants. Do not pick a contrast threshold by recovering 188 pixels. The accepted count is evidence of one demonstration, never a target for subsequent studies. |
| M18 — native extrema, walls, seams and course pointers | Acquired-signal minima versus flanks, fluid boundaries, matched relative-signal seam, convex-envelope concavity and `trace_tube` each measure their stated local property. Their products are not interchangeable. | Retinacula/capsule/lining; ITB deep-fat dip; Q/P separation; popliteus sulcus; posterior traces locate missing-view questions. | A wall lies on the appropriate side of a cavity, fascia deep to fat, tendon in a sulcus, and a course continues beside relevant neighbours. | A trace is not a full native body or volume. A lining edge is not membrane thickness. Keep separated ties and local stops; no smoothing/interpolation solely to complete a preferred contour. An axial cross-section and longitudinal trace answer different descriptions. |
| M19 — resolved native object support / observation | A family decision applies its stated anatomical relations to complementary measurements and returns a native support or named uncertainty. `Observation` retains support addresses/counts/frame/view and provenance; existing adapters and `describe_objects` own aggregation. | `offer_native_family`/`offer_map_rows`/`refine_map`, subsequent source collectors, grouped object output and intended later representation. | An object is the joint description of its physically constrained evidence, not its label or one metric. | Preserve original native/laid/projected/read/refused descriptions. No promotion of projected mask to independent evidence. At the inspected map path, metadata/counts/geometry are consumed; do not claim support pixels were read there. Reasonable competent identity once is the criterion. |
| M20 — key-plane constraints, common reference and guide | `KeyPlane`, `StudyMap`/`MapContext`, physical plane construction and authored anatomical relations supply per-object partial/full reference constraints, pair vectors and expected native locations. | `mapping.guide` consumers in bone/patella/joint/recess/fibula/native-family searches; object output retains constraints and named partial endpoints. | One knee has one physical set of objects with relative positions. Three key orientations jointly constrain the reference; known neighbours narrow later questions. | A point is not a tissue voxel/boundary; area may distinguish existing candidate sections but is not universal obviousness. Never use a centroid as the reference, force a prior onto observation, or count a derived guide as new confirmation. Refresh before dependent calls without repeatedly re-running recognition. |
| M21 — work, persistence and cohort reports | Ledger/once, digests, receipts, actual query/context counts, profiling and pair-variation reports measure execution/preservation/coverage. | Integrator verifies real paths, reuse, retained information and performance; cohort variation supplements the authored map. | Shared useful information should reduce repeated work and constrain several questions; output must preserve what was observed. | None of these reports defines anatomy. No pixel/count/calibration objective, fake consumer, SD for n<2, imported speed multiplier, or claim of accuracy from map coverage. Equivalent refactors preserve answers; intended semantic/scope changes receive an explicit adjudication. |
| M22 — exact later encoding | Versioned banks and integer row-count bundles encode the retained named measurements under the author's exact carrier/layout. MRI place/depth/support layout is a later explicit contract. | P12 representation, then the human-specified P13 consumers. | Bundling provides one exact additive/subtractive language for complementary descriptions and their contexts. | No generic HDC classifier, weighted vote, invented volume from key planes or default ML tail. No recomputation of recognition to write already held measurements. Unspecified MRI/diagnostic choices stay explicit; they do not block ground-layer completion. |

### 14.4 P2b's concrete producer–consumer contract

This is the mechanical next-stage contract behind the recent confusion:

1. `keep_bone_planes`/`name_the_bones` retain native identified section supports (M07), their
   actual frames, row/slice addresses and outcomes. Preserve their inherited overreach. They do
   not emit a promise of pure marrow or an exact full 3D bone surface.
2. `refine_leg` publishes their usable physical locations once as later shared context (M08),
   linked to those original sections. Existing arrays/records may provide the linkage. Keep early
   context available to earlier consumers. Do not default to eroding every source section.
3. `leg_on` uses context identity plus acquisition/slice geometry to supply location/slab targets;
   updated context cannot hit an early-context cache entry. `native_femur_coarse_context` shares
   the same raw block/depth readings while recalculating the context-dependent section (M09).
4. `native_fat_coarse_femur_context` consumes that coarse result as competing-marker/enclosure
   context for fat candidates. It does not certify every marked native pixel as bone/marrow.
5. `native_femoral_cartilage_candidates` consumes the coarse result to locate a native bone-related
   question. Native enclosure/component selection (M12/M19) and the explicitly addressed sample
   used by `Measures.light` (M14) are separate from the coarse target. Their status and support
   remain visible. The cartilage relation then reads the native signal band and proximity to its
   bone/surface, with the independently native sagittal/coronal source locations (M13/M15).
6. The resulting native cartilage observation enters M19/M20 before dependent guide requests.
   Its count and calibration are reported but never used to choose which seed representation
   should be preferred. Inspect whether it reasonably describes the intended anatomy.

At the source inspection for these contracts, the cartilage path passes `selected_enclosure`
to the marrow callback instead of directly calibrating on the coarse expansion. The builder's
subsequent P2b increment-1 acceptance and repair runs are recorded in §13 and
`p2b-bone-context-20261018/README.md`; this contract edit preserves that record and does not
independently re-perform its acceptance audit. The native component's attribution is still an
anatomical inference with its documented limits. Source evidence is retained under
`measurement-contracts-20261018/`. Do not justify the repair by its calibration or pixel counts.
The earlier seed-shell direction is withdrawn development evidence, not a competing accepted
objective. P2b's remaining axial-anchor/fibula consumers keep their own task boundary.

**P2b's tests pin meanings and wiring:** only eligible native sections contribute; source masks
and outcomes remain retained; source-frame projection round-trips; changed context misses the
old projection/coarse cache; identical context reuses; the fat and cartilage readers actually
receive the later context; calibration's sample address is distinguishable from the coarse target;
unknown is not empty. Do not assert that adding seeds must always increase/decrease the median,
make the core smaller, recover the old rim count, or improve an accuracy score.

## 15. Remaining task and anatomical-family contracts

### 15.1 Work packets with a fixed objective

| Task | Inputs → output meaning | Required real consumer / wiring | What the worker can build mechanically | Completion and explicit non-objective |
|---|---|---|---|---|
| P2a — OPEN | M01–M04 plus justified complementary context → M05 useful actual region/tiles, with box/halo separate. | Chosen expensive middle/native reader before it computes; later anatomical scope may refine the same product. | Produce native-region/tile evidence packet and actual operation work counts; after the lead chooses the simple region rule, wire its scope/unknown handling into that consumer. | Useful native region or downstream constraint demonstrated and consumed. Not “minimum rectangle fraction”, perfect background segmentation, or rejection of all domains after one flood fails. |
| P2b | Retained M07 sections → M08 updated context → shared M09 native coarse question. | `leg_on`, `native_femur_coarse_context`, fat and cartilage consumers in §14.4. | Publication, provenance links, context identity/cache changes, explicit arguments and invariant tests; retain early context. | New information reaches actual dependent questions with reasonable native competence. Not calibration stability or purified seed masks. |
| P3 | M07–M09 usable bone context, M14 sequence-specific calibration, patella/map location → local patella or recess native question. | `patella_plane`, `patella_scope`, `recess_anterior_plane` and every sibling caller. | Pass shared usable context; bound before the heavy reader; share identical requests; retain named missing/fallback outcomes. | Avoid rediscovering supplied bones and use the actual patella/cavity relation. Not a smaller box at any cost, whole-frame equality, or a second whole-frame read after successful local resolution. |
| P4–P6 | Eligible existing native sources, M02/M10/M11 location and native complementary readings → M19 body/surface in each missing orientation. | Family source collectors, `offer_native_family`, common map and grouped output. | Once its F-contract below has a chosen native rule: one adapter, shared primitives, native addresses/statuses, tests and immediate offer. Prepare evidence for DEFINE NATIVE RULE rows meanwhile. | General rule and competent native demonstration once per requested orientation. Not universal correctness, source count, arbitrary largest component or a variant leaderboard. |
| P7/P9 | Existing products and actual caller dependencies → useful scopes/shared calculations with unchanged meanings and honest lineage. | All expensive readers and their actual next decision, not only drawing/save. | Deduplicate identical inputs; key real context; wire scopes and read declarations; preserve family status interpretation and retained arrays. | Concrete dependency used before work; same answer for equivalent refactors, explicit changes for new scopes. Not a clean Vulture/ledger count obtained by deleting evidence or inventing reads. |
| P8 | M19 catalogue/fields plus native bone-associated support → complete accounted-for concepts and contained marrow descriptions. | Coherent object output and later representation. | Address retained supports, preserve generic/specific/diffuse semantics, emit named missing outcomes. | Every requested concept accounted for without fake points or an invented extra object. Not a target catalogue count or reconstructed full anatomy from labels. |
| P10/P11 | M21 measurements and frozen production evidence → equivalent kernels where justified and verified coherent runtime. | The existing no-draw CLI, serial/parallel/public/cohort paths. | Appropriate kernel twins, real entry-point runs, source/receipt/address audits and actual work/profile reports. | Preserved meanings and demonstrated production behavior. No optimization substitutes for missing object capacity; no speed/accuracy claim from isolated counters. |
| P12/P13 | Retained measurements → exact specified encoding → later human-specified inference/output. | Existing pipeline's declared downstream interface; competition serializer after diagnostic contract. | Implement supplied layout/carrier and later inference contract, with exact arithmetic/schema tests. | No invented AI/diagnosis mechanism or dense-volume formula. Ground-layer completion is an independent deliverable. |

### 15.2 Fixed anatomical questions and output consumers

These are the anatomical decision contracts. Facts and accepted operations are in
OBJECTS_AND_CONDITIONS and RESOLVING_THE_PARTS; those full units govern the exact existing
constants and limits. Each row feeds **M19 → M20 → dependent source/guide consumers and grouped
object output**. That shared destination is required for every row and is not a claim that an
unfinished native-view adapter exists. The row also names the concrete next anatomical question
its result supports. Reuse existing measurements; choose no new numerical criterion by trying
values until a desired output appears.

| ID / object output | Anatomical invariant that determines identity | Measurements and existing owner(s) to reuse | Next anatomical consumer / why useful | Build boundary |
|---|---|---|---|---|
| F01 — femur, tibia | Superior/inferior bones forming the tibiofemoral articulation, with their native enclosed bodies and cortex/marrow context. | M06–M09; `assign_plane`, `name_the_bones`, `keep_bone_planes`, shared coarse section. | Joint between them, cartilage on articular faces, cruciates/collaterals at attachments, posterior condyle context. | Retain accepted native rules; WIRE later context under §14.4. Do not replace key-plane reference by a shaft-dependent centroid. |
| F02 — patella | Anterior bone at distal femur, between quadriceps and patellar tendon context. | M06–M11/M14; `patella_plane`, existing patella search and key planes. | Extensor chain, retinacula, anterior cavity and fat pads. | REUSE accepted identity; P3 WIRE bone/calibration context before its reader. No mandatory bone rediscovery. |
| F03 — fibula | Separate lateral/posterior proximal bone below tibial joint level. | Existing `find_fibula`, profile/head and native key-plane support; M02/M09/M10. | LCL and biceps fibular attachment; lateral sidedness context where available. | REUSE accepted sections and native axial bridge. No brightness-only identification or bone treated as an infallible global reference. |
| F04 — bone-associated marrow | Interior tissue associated with a particular native bone support and its acquisition's contrast. | M07/M14; existing bone masks/native section/calibration records, retaining approximate-support limits. | Same-sequence tissue contrasts and later contusion/fracture/OA representation under future specification. | WIRE explicit output address without an invented independent point. Neither full coarse enclosure nor eroded seeds automatically constitutes marrow. |
| F05 — joint / generic recess | Joint lies between native femur/tibia surfaces; general recess is an interstitial relation with specific cavity descriptions, not a fabricated extra body. | `between_along_the_leg`, `name_the_joint`, native joint adapter, recess corridors; M06/M13/M19. | Menisci/cartilage/cruciates in their compartments and joint-fluid/capsule context. | REUSE accepted bridges; preserve generic/specific semantics in P8. Not every bright pixel is joint, and a semantic slot needs no invented independent mask. |
| F06 — medial/lateral menisci; generic meniscus | Sided dark fibrocartilage wedges between condyle and plateau; horns and body are descriptions of the same sided object. | Existing coronal definition, `name_native_menisci`, M10–M13 and sided bone/joint context. | Corresponding cartilage/compartment; medial meniscus also constrains MCL context. | REUSE accepted three-view capacity; no perfection pass or source redefinition from one fragmented lens. |
| F07 — femoral cartilage | Articular surface on the femur, distinguished from bone interior, free fluid and unrelated cortex by surface/context and native contrast. | `femoral_cartilage_on_plane`, `native_femoral_cartilage_candidates`; M09 locates, M12/M14/M15/M13 measure native question. | Compartment and patellofemoral surface descriptions; later OA inference only when specified. | REUSE accepted competence; any P2b-induced semantic repair follows §14.4. Not a target bright-rim count or marrow median. |
| F08 — tibial cartilage | Layer on the tibial articular plateau facing femur, distinguished from spine/shaft cortex and intervening meniscus/fluid. | Existing SAG/COR native descriptions, M07–M15, actual plateau/bone context. | Tibiofemoral compartment and its interstitial structures. | AX is DEFINE NATIVE RULE from the retained packet; the superior-most/spine strip and unique contact component are not accepted selectors. Do not copy femoral code without its tibial surface relation. |
| F09 — ACL | Heterogeneous ligament in the notch between tibial intercondylar and lateral femoral attachment regions, with its course distinguished from PCL/cortex/fluid. | Existing native SAG own-slice source, M07/M10/M11 plus bone/notch/PCL context and complementary native signal. | Notch/attachment context for the other cruciate and later requested ACL inference. | AX/COR are DEFINE NATIVE RULE. Not PCL uniform-darkness, largest body alone, or projected source contact as complete identity. Use actual late source producer before adapter. |
| F10 — PCL | Posterior-notch ligament between medial femoral and posterior tibial attachment regions, distinct from calf/cortex/subcutaneous bodies. | `native_pcl_sources`, `name_native_pcl_sections`, M10–M13; accepted source/body/opening/contact contract. | ACL/notch context and later guided anatomy. | REUSE competent three-plane description. WIRE general anatomical source eligibility; do not select an anatomically ineligible larger label or tune to the four recorded errors. |
| F11 — MCL | Medial band connecting femoral epicondylar region to proximal tibia outside medial compartment and deep to pes context. | Existing coronal definition, native sources, medial meniscus/joint/bone context, M03/M12/M13/M18 as its chosen rule requires. | Medial compartment and medial tendon ordering. | SAG remains DEFINE NATIVE RULE; native AX local-band construction is MAP §8.44. Endpoint/course/sidedness is the question; no unique grey threshold distinguishes every ligament. |
| F12 — LCL | Lateral cord from femoral condyle to fibular head, separate by course from popliteus and biceps. | `lcl_on_slice`, fibula/head selection, existing source reach/body readings. | Popliteus sulcus and biceps attachment distinction. | SAG/AX are DEFINE NATIVE RULE; REUSE existing coronal definition and attachment-guided slice. Do not require exact separation of every fibre. |
| F13 — popliteus tendon | Tendon in the lateral femoral sulcus, medial to LCL at that level. | `popliteus_in_notch`, existing femoral convex envelope and LCL native support, M18. | Lateral-complex identity exclusions and attachment/course context. | SAG/AX are DEFINE NATIVE RULE. A source sulcus mask points, not a projected native boundary in every view. |
| F14 — iliotibial band | Lateral fascia deep to subcutaneous fat, passing femur toward proximal tibia. | `iliotibial_band_on_slice`, fat/bone axes and native relative-minimum versus flanks. | Superficial/deep ordering of lateral structures. | SAG/AX are DEFINE NATIVE RULE; retain the existing coronal trace and its limits. Not any lateral dark line or an interpolated perfect band. |
| F15 — biceps femoris tendon | Posterolateral tendon continuing from muscle toward fibular head beside the LCL. | `biceps_native`/`biceps_femoris_slice`, fibular head, posterior muscle, matched sequence contrasts. | Fibular attachment/lateral-complex context. | COR/AX are DEFINE NATIVE RULE; reuse selected native SAG source. Keep known conjoint-insertion overlap, not a fibre-perfect separation prerequisite. |
| F16 — patellar and quadriceps tendons | Extensor chain: patella–tibia below and tendon above patella toward quadriceps. | `name_the_extensor_tendons`, shared `dark_bands`, existing native axial/coronal section adapters. | Anterior fat pads and cavity bounds. | REUSE accepted three-view descriptions. Bound shared band work only with context actually available at that caller; do not clip the extensor chain with a bone-only box. |
| F17 — Hoffa, Q/P and combined suprapatellar fat | Hoffa behind patellar tendon; quadriceps and prefemoral pads on opposed sides of the suprapatellar recess. Combined Q/P is their same-slice union with both usable. | Existing pad definitions, `native_fat_pad_candidates`, opposed signal and seam, M14–M18. | Anterior cavity/lining and extensor surface relations. | REUSE competent descriptions, share supplied coarse context and scope. Preserve component roles and unknown compatibility; do not maximize basin compactness or force a union when one component is unresolved. |
| F18 — joint fluid / anterior synovial recess | Fluid in the anatomically bounded joint/recess space; cavity support is distinct from solid tissue and its lining. | Existing white-fluid relation, native pockets, `name_the_recess`, `name_coronal_anterior_recess`, `axial_joint_fluid`. | Lining/capsule walls, fat-pad separation and local retinacular context. | REUSE accepted native bridges; P3 WIRE bounded cavity context. Do not call every bright body fluid or require a three-plane reference to be a fluid voxel. |
| F19 — synovial lining / capsule | Cavity-facing lining and exterior capsular band are different sides/relations of the native cavity, with separate observations. | Existing `cavity_lining_observations`, wall/extrema readings and capsule bridges, M18. | Recess/retinacular boundaries and future requested conditions. | REUSE accepted local descriptions. No membrane thickness, complete envelope or dense segmentation prerequisite. |
| F20 — medial/lateral patellar retinacula | Bands beside patellofemoral recesses connecting the corresponding patellar/femoral sides. | `retinacula_slice`, native wall readings and `name_cross_view_retinacula`; patella/femur/fluid context. | Companion fluid/capsule/lining and anterior anatomy. | REUSE accepted three-view capacity; scope at the real caller before expensive work. Keep capsule overlap limits and local ties. |
| F21 — both gastrocnemius heads | Native muscle bellies posterior to their respective femoral condyles, separated by fascia and physical sidedness. | `name_the_back_of_the_knee`, shared condyle/head territories and early/native bone context. | Inter-head vessel corridor; medial head with semimembranosus bounds bursa. | SAG/COR are DEFINE NATIVE RULE. Reuse AX source; a belly needs muscle/compartment evidence, not a projected oval or full longitudinal trace assumed from it. |
| F22 — semimembranosus / semitendinosus | Posteromedial tibial-related tendon and separate posterior neighbour at the appropriate level. | Existing `semimembranosus_slice`, `dark_tendon_bodies`, `semitendinosus_on_slice`; native source and course pointers. | Bursa seam, gracilis distinction and medial tendon context. | SAG/COR are DEFINE NATIVE RULE. Native trace is a location reading until the body's rule is chosen; exact full tendon course is not required. |
| F23 — gracilis / sartorius | Thin medial/anterior tendon relative to posterior tendons; nearby sartorius is a distinct muscle sheet, with level-specific relations. | `gracilis_on_slice`, shared source group, M17 and physical position/reach; P1 scoped contrast retained. | Each localizes the other medial soft-tissue question; tibial attachment context helps constrain course. | SAG/COR are DEFINE NATIVE RULE. Do not apply distal insertion order blindly at patellofemoral level, or purify the projected gracilis mask to manufacture sartorius identity. |
| F24 — popliteal artery / vein | Distinct lumens in the posterior inter-head corridor, artery anterior to vein at the established source level. | `popliteal_lumens`, shared enclosed darkness/body/corridor, axial sources and `trace_tube` pointers. | Posterior anatomy and exclusion from tendon/bursal fluid questions. | SAG/COR are DEFINE NATIVE RULE. Retain distinct lumen/course readings; exact calipers and full vessel reconstruction are not required. |
| F25 — gastrocnemius–semimembranosus bursa | Fluid body between the named medial head and tendon; distinguish adjacent joint fluid and vessels by that relation. | `bursa_on_slice`, native source on the known visible bursa study, fluid contrast and neighbour context. | Posterior interstitial space and future human-specified Baker's inference. | SAG/COR are DEFINE NATIVE RULE. Use the visible example; a refusal on proof is not absence. Neck/wall/full course are deferred limits, not new perfection requirements. |
| F26 — air, skin, subcutaneous fat, general muscle | Exterior field, leg edge, superficial fat and remaining muscle field with their physical/tissue relations. | `read_field`, `name_the_rest_of_the_field`, actual paired signal/availability, M01–M06/M14/M15. | Useful leg domain, ITB superficial context, muscle/attachment and posterior compartments. | REUSE existing diffuse masks and WIRE useful earlier M05 guidance. No invented unique reference points, generic muscle substituted for a named head, or identification of every dark place as air. |

The future anatomical-rule packet for a DEFINE NATIVE RULE row must resolve the **specific**
missing selector, not repeat the whole project plan. It names the relevant F-row, native source,
candidate frame/scope, complementary M-readings, ordered anatomical conditions, exact tie/refusal
handling, and one inspected competent example. This is the only unfinished semantic choice a
mechanical implementation worker receives; it must be filled by the lead before that worker
implements the selector. Apply §7's existing rule-review procedure (the recorded Codex and Fable
checks and disagreement route); this adds no further approval step. All independent evidence/wiring
tasks can proceed meanwhile.

### 15.3 Acceptance record that prevents objective substitution

For each completed packet record these six statements in its existing README/status record:

1. **Question:** the F-contract or structural task being implemented, in anatomical/plain words.
2. **Reads:** the M-contracts with actual source addresses, acquisition/scope and meaning.
3. **Produces:** the stated measurement versus anatomical inference, retained separately where needed.
4. **Consumed by:** the real function/decision that uses each result, before its measurement if targeting.
5. **Why valid:** the physical/anatomical relation and the actual native competent demonstration.
6. **Verified:** the appropriate invariant and real-CLI/address/image checks, including retained uncertainty.

Calibration shifts, pixel counts, box area, source counts, profile maxima, test totals and runtime
remain reported observations. They cannot replace any of those six statements, become acceptance
targets, or silently redefine the task. An explicit unresolved selector is better than a mechanically
implemented proxy pretending to be the specified anatomical operation.


## 16. Full-operation efficiency: measured leads carried into P7–P11

Rohan's request after the full-run probe: «Can you work on how we can make this part of the full
build plan/workflow that we can launch?» This section turns that evidence into bounded work inside
the existing plan. It adds no recognition objective, arbitrary numerical target, new pipeline or profiling
framework. The sequence is still anatomical constraints before residual kernel work (§1). The governing
production contract is §1.3; §§16.6–16.8 apply it throughout P0–P13, within studies and across the
cohort, rather than confining efficiency to the measured kernel leads below.

### 16.1 Evidence and what it does not establish

The dated probe is B + full-run-efficiency-20261019T011718Z/ (B is §2's readings root).
Read its README.md, SUMMARY.json, source-before.json, source-after.json and commands.json as a
complete evidence packet. Detailed allocation and CPU reports are there too. Its production source
pin was afc6f032a4a0d95a5e0492ba961ee018c4b65ddc; profiled source hashes were unchanged across runs.
The proof study, no drawing and one worker, covered the currently implemented operation. Ordinary,
Memray and cProfile receipts matched. The packet is evidence of that source, not today's cost, a
leak diagnosis, an anatomical acceptance record or a multi-worker memory bound.

The measured leads are native-light float64 copies retained in the shared store; decoded slices
beside a stacked volume; compression and digest copies; repeated frame inverse construction; and
per-pixel scratch allocation in local lightness. Counts and timings locate work; they neither
prove every allocation redundant nor prescribe deleting a reading. Useful sharing can increase
residency while preventing recomputation. Trace consumers, source ownership and lifetime together.

### 16.2 The bounded packets and their production consumers

Each row uses M21, plus the anatomical contracts its reader already serves. The lead settles any
scope/meaning decision with §§1.1–1.2 and §7 before workers implement it. Workers return facts or an
equivalent candidate, never choose the anatomy from a memory/timing leaderboard.

| Packet | Existing task / workflow | Operation, inputs and actual consumer | Required evidence / boundary |
|---|---|---|---|
| EP0 — freeze whole-operation evidence | W2's existing P7 facts; P7/P9/P10 checkpoints | Read the probe, verify its source hashes against the relevant current modules, and trace every measured producer to its real readers. The lead uses the account to prepare EP1–EP4 packets. Reuse the probe when its inputs/source are applicable; otherwise make a fresh source-pinned baseline. | Name input loading, recognition, shared-store residency, hashing, compression and receipt output separately. Do not call an old source's numbers current or add nested cumulative costs. |
| EP1 — anatomy scopes and source-owned representations | P2/P3 and P7; W3–W7 | The lead's anatomical regions precede heavy native reads. Include seen_native, its real fibula/head/biceps readers, and any whole-frame float/context materialization those readers demand. Trace decoded Slice.pixels and Series.volume to all callers before considering common backing storage. | Useful context, halos, unknown exterior and all retained readings survive. Share identical contexts; distinct queries remain distinct. Keep broad bootstrap work where a named prerequisite requires it. A storage-only change is equivalent; a scope change gets the anatomical change account. Do not remove a useful cache, cast dtype, drop arrays or gate retention to make RSS smaller. |
| EP2 — frame transforms made once | P9; W8a's existing geometry work | PlaneFrame.to_native currently constructs the basis pseudoinverse at every call. Establish the full frame/basis identity and mutation rules; reuse that exact transform across callers when those rules allow it. Projection results still consume their own source points. | Check every caller/sibling conversion, oblique/anisotropic geometry and invalid input. A frozen dataclass does not by itself make its ndarray fields immutable. Never key by a slice index alone or reuse a stale inverse. If a different numerical operation changes answers, it is not this equivalent task. |
| EP3a — digest without repeated byte copies | P9; W8b | The existing digest defines SHA-256 over dtype, shape and C-order array bytes. Feed exactly that stream incrementally and reuse a digest only at an established immutable producer. Consumers are save/receipt verification and the existing source/cache identities. | Preserve every existing digest, dtype/shape distinction, byte order, signed zero and NaN bytes. Exercise contiguous, strided, empty and scalar arrays. A non-contiguous array may still need materialization. Keep mutation invalidation explicit; never memoize by object id alone. |
| EP3b — lossless persistence with its real readers | P9; W8b after EP3a is integrated | Trace save and all NPZ/receipt/address readers. Reduce repeated serialization/compression setup within the reconstruction contract, preferring the established format and applying §16.9 when capacity requires a versioned lossless repair. Keep this separate from recognition time and report the storage/time tradeoff. | Every named array, diagnostic reading, key, dtype, shape, address and digest remains reconstructible. Archive compressed bytes need not be identical; decoded arrays and receipt semantics must be. Section 16.9 now requires W8b to resolve actual capacity, allowing the minimum lossless versioned layout/placement repair with all readers/addresses updated if the existing format is insufficient. No retention switch, dropped reading or unrequested asynchronous writer is authorized. A known overflow cannot be closed as an advisory. |
| EP4 — local-lightness scratch and other residual kernels | P10; W9 | Reprofile after EP1–EP3. If local_lightness remains material, replace per-pixel allocation/partition scratch with scoped reusable workspace under the same median operation. Existing scoped_local_lightness and its anatomical consumer receive the same outputs. Other residual kernels use their own bounded packets. | Keep a reference twin before editing. Same float64 values, finite/unavailable handling, even/odd medians, borders, context/halo and all three output arrays; no fastmath or selector changes. Workspace is per call/worker or has proved safe lifetime, never shared mutable scratch across concurrent calls. A kernel disappearing after structural work needs no speculative rewrite. |

The row is accounted for by an integrated verified implementation, or by a specific measured/code-
grounded reason the existing operation is already shared or still required. An open item stays
open. Rejecting one candidate retires that candidate, not the useful-domain capability or anatomical
information handoff. P2a remains required under §1.1. These dispositions do not replace workflow
outcomes or the six statements in §15.3.

### 16.3 One repeatable whole-run measurement contract

Use installed instruments through the project interpreter, not a bespoke profiler or production
import. Invoke scripts/run_interiors.py with explicit input and fresh run/main-run destinations,
one worker first, drawing off. The probe's commands.json gives the successful local command shape.
The lead owns these runs; candidates and verifiers retain their own output roots as usual.

- Freeze source hashes, environment/backend, input identity, exact argv, exit status and complete
  logs. A changed HEAD caused only by documents is not proof that production changed; inspect the
  relevant source hashes. Unplanned source changes require a fresh pin; an intentionally changed
  candidate is compared with its preserved pre-change baseline, not mistaken for stale input.
- Keep an ordinary run for elapsed/user/system time and OS peak RSS; cProfile and Memray are
  separate diagnostic runs. Use macOS time -l here, an equivalent OS instrument on another host.
  If OS statistics are refused, record unavailable and use the normal permission route; do not
  call the pipeline failed solely because the timing wrapper could not report them.
- Record RSS, tracked live-allocation peak, cumulative allocated bytes and allocation count as
  different quantities. Name tracking settings and missing native symbols. Startup, imports and
  JIT loading are included in a fresh-process run; measure cold compilation separately if needed.
  Nested kernel costs and overlapping cache/array views are not additive ownership totals.
- Read per-event ledger counts, not cross-stage totals as if every count meant the same thing.
  Report cheap/expensive slice reads, actual context/query work, cache creations/reuses, broader
  fallback and retained/persisted bytes. An enclosing box is not a measured irregular domain.
- Compare ordinary and diagnostic receipts using compare_receipts.py for both output families.
  For an equivalent candidate compare baseline and candidate too, preserving its source epochs.
  For a scoped/semantic change use §9's complete change account and inspected native images.
- Before claiming a speed-up, run ordinary baseline/candidate measurements sequentially under
  matched input, worker, draw and backend conditions, repeat in alternating order when scheduling
  noise obscures the result, and keep all observations. If still unclear, report the benefit as
  undetermined. RSS variation or a larger cumulative allocation total alone proves no leak.

Full diagnostic captures are shared checkpoint evidence, not repeated by every object worker:
reuse this probe where applicable; refresh after the W7 structural scope work, after W8b's
representation/persistence work and after W9's kept residual changes. W10 uses those records
when its frozen source matches, measuring the final ordinary serial and actual parallel paths.
Reuse existing proof/bursa/public/cohort runs for ordinary observations where the settings match;
no per-object cohort profiling or duplicate diagnostic suite is added. The run is still one CLI.

### 16.4 Worker verification and benchmark continuity

In addition to their task-specific checks, EP workers/verifiers use these stable check names in
their prompt, return schema and script's required-check list (never a count of arbitrary checks):
source_basis, production_consumers, scope_and_context, retained_information, equivalent_outputs,
real_cli_runs, measurement_semantics, whole_operation_account. The source-basis check follows the
existing required-file manifests. A worker's whole_operation_account checks baseline applicability,
its own real-CLI counts/cost observations and affected downstream work; it links the matching-source
lead checkpoint where one exists. It does not require a post-integration profile that the lead
cannot make until this candidate is verified. Full shared Memray/cProfile captures remain the lead's
checkpoint duty; a worker does not invent them or run Sonar. A scoped change replaces the
equivalent_outputs check with anatomical_change_account and keeps §7's rule/image process.
A required check that cannot be made stays not_checkable and the chain stays INCOMPLETE. EP4 adds
reference_twin and concurrent_workspace; EP2 adds geometry_and_mutation; EP3a adds exact_digest_stream;
EP3b adds reconstruct_all_arrays and competition_storage_envelope (§16.9). These are contents of the existing workflow contract, not a
second outcome engine.

Keep a fixed set of recorded arguments to compare equivalent kernel implementations. A production
scope/argument change can justify refreshing benchmarks/recorded, but that changes the benchmark
question; label it explicitly and keep the prior recording as evidence rather than interpreting
the difference as the same-call regression. A change to call frequency/targeting/sharing may leave
an isolated replay unchanged: the ledger and whole run establish that benefit. GitHub keeps the
existing data-free recorded replays, not an invented tiny-study replacement for this evidence.
All recordings, profile records, acceptance records and active-packet updates precede the final
gate on exactly the tree committed (§9). The correctness gate stays the existing one; profiler and
benchmark figures stay advisory. Actual deployment limits and §16.9 stage acceptance are mandatory.

### 16.5 Completion at P11

The recognition-completion record links the frozen-source ordinary and diagnostic evidence,
serial/parallel results, same-output or anatomical change account, and EP0–EP4 dispositions with
real consumers. Explain useful prior propagation and remaining broad work, retained representations,
serialization and residual kernels separately. If an item is open, say so; a smaller kernel number
or green CodSpeed run is not whole-operation completion. There is no invented minimum speed-up, RSS
ceiling, mask-purity target or all-studies perfection requirement; the actual deployment envelope
in §16.9 is mandatory and includes W8b storage and W10 integrated capacity/headroom verification. Later MRI encoding and diagnostic
specification gaps remain P12/P13's and do not block competent recognition.

### 16.6 Reuse, ownership and lifetime within and across studies

Apply §1.3 before implementing a family as well as during EP0–EP4. Record the following in the
existing packet/producer contract, using the existing source-owned graph and ledger rather than
introducing a universal cache manager:

| Lifetime | What can be consolidated | Identity and consumer obligation |
|---|---|---|
| Installed code / process | Authored definitions, anatomical relations and approved descriptive search priors; compiled kernels; immutable tables and preparations independent of the current image. | Pin definition/layout/backend versions and real preparation inputs. A code cache is not an observation cache. Report compile/load/setup separately from warm use. |
| Cohort / worker | Input discovery/indexing and invariant setup used by multiple studies; immutable shared backing where the runtime supports it. | Carry the actual input manifest and configuration; share only the invariant portion. Each worker's private copy, IPC/pickling and thread pools count in the cohort account. Do not reload/rebuild the same invariant setup inside each family or study without a reason. |
| Study / acquisition | Decoded source ownership, squint readings, observed anchors, physical map and calibration/context whose dependencies belong here. | Preserve patient/study/series identity and source revision, sequence/geometry and dependencies. Fat-bright and fat-dark native readings remain distinct even though one physical knee map relates them. No patient-derived value is silently reused for another patient. |
| Native plane / query / context | Frame transforms, measurements, scoped representations and reusable scratch. | Name the source plane, full physical basis, query/context/halo, offsets, calibration, producer/encoding versions (and layout/carrier versions when applicable), and dependency mutation state relevant to this value. Reuse the actual same computation, not a superficially matching object label or array shape. Scratch is private to its proven concurrency/lifetime boundary. |
| Persisted record | Every retained reading, decision, provenance and array address; lossless common backing or exact digest reuse where warranted. | Reconstruction preserves dtype, shape, values, scope, unknowns and source identity. Shared storage does not erase separate provenance. Existing readers and receipts consume it; saved information need not stay resident in every worker. |

A reuse key covers the dependencies that can change that value, not an indiscriminate hash of the whole
project on every call. Establish identities at source/producer boundaries and hand them on. Where an
array may mutate, freeze ownership or version/invalidate it; object identity or a frozen container is
insufficient. Include backend/environment where it affects the reference contract. Reuse between two
inputs is legitimate only if the computation's actual dependencies are invariant or demonstrably
identical; never infer this from similar anatomy. Count constructions/reuses/invalidations and name
why a broader/new reading was needed. Record releases/drops with their causes and retained addresses,
distinguishing invalidation, completed lifetime and scratch disposal from loss of information. Reusing
a consequence does not create another independent vote.

Retention and residency are different. Persist and verify the required information, then release
study-scoped working references at a safe completed-study boundary, after all current consumers have
finished and the complete kept record is verified reconstructible by its existing readers and digests.
If a later reader needs the value, pass its retained address or retain its live owner as appropriate.
Never evict its only copy, leave dangling views, or hide repeated decoding/analysis behind a small RSS number. A reusable worker
must start its next study with new study-scoped mutable state; an exception must not leave stale
state eligible. Readers of a common buffer must not mutate it behind another reader's identity.
Rohan explicitly reaffirmed the competition lifetime on 2026-10-19: finish a study completely,
record the needed result, and release that completed study before starting another; parallel
processing keeps only the bounded set of active studies. His complete words are in
`docs/conversations/2026-10-19-completed-study-lifetime.md`. Apply this to the complete configured
per-study operation: currently report each object's identity and pixel/HDC bundle; later include
the human-specified AI/diagnostic consumer before study completion. Do not retain completed
image volumes or caches for the whole cohort. The parent owns the aggregate receipt and final
cleanup after publication. Unique per-study recognition/encoding products may be written by their
bounded study worker: those are synchronous stages of the same study, not an additional asynchronous
writer queue. In competition mode, encoding and public-reader verification belong inside that worker
so independent studies use available cores through the complete operation. Prepare invariant encoding
configuration once per worker; return compact metadata and verified identities, with no image/count
array payload sent through IPC. The parent validates the return's study/configuration/product identity,
stages its compact receipt and then releases consumed intermediate files. Do not re-encode or repeat
the complete readback in the parent. Serial and development behavior retain their existing contracts.
Completed results awaiting the parent and submitted work are bounded along with active studies. Preserve
input-order receipt semantics, failure cleanup and the reusable invariant worker setup. A worker
count alone does not bound an eager all-cohort future/result queue. Verify actual ownership and
release after the last consumer on serial and reusable-worker paths; a high-water RSS value alone
neither proves retention nor proves release. Persisted records may be addressed without keeping
their decoded working arrays live. Required durable output and the separate storage quota still
follow the retention contract and §16.9.

EP3b now closes storage under §16.9. If measured cohort output requires a different container or
placement, the lead settles the minimum versioned lossless repair and all consumers before building;
no known overflow is deferred beyond W8b. Rohan explicitly changed competition retention on
2026-10-20: «Retain complete object outputs; release consumed intermediate files». The exact exchange
is in `docs/conversations/2026-10-20-competition-object-retention.md`. Competition mode retains complete
object pixel/HDC bundles, measured values and necessary provenance in independently readable final
products. Active support/value links resolve there; original source paths remain historical provenance.
After the final consumer and verified publication/readback, release only that run's owned intermediate
files. A missing dependency, publication failure or failed verification prevents cleanup. Development
retains diagnostic intermediates. This supersedes blanket permanent-intermediate retention for
competition mode; it authorizes neither precision loss, incomplete final objects nor deletion of old runs.

### 16.7 The short work account required of every construction packet

Extend the existing §9 Contract and Verification fields; do not maintain a second task list. For each
family, retrofit and performance candidate, the lead supplies the anatomical meaning and the worker
returns facts against it:

1. **Known information and next question.** What prior/anchor/object is already available, what physical
   relation narrows this question, and which real consumer uses it before costly work? Explain broader
   bootstrap or fallback work and distinguish expected position from native evidence.
2. **Actual work domain.** Identify the cheap discovery step, selected native plane(s), irregular/tiled
   query where used, necessary context/halo and unavailable exterior. Count actual expensive reads and
   queried/context pixels or tiles under the existing ledger's meanings. An envelope area alone does
   not measure the irregular region; overlapping regions and nested times are not additive totals.
3. **Shared value and lifetime.** Identify its producer and all readers, the preparation it replaces,
   reuse/invalidation basis from §16.6, source ownership and retained output. Explain any remaining
   duplicate computation or independent read that is necessary rather than calling it optimized.
4. **Residual execution.** State what still pays after structural reduction. Name existing native code,
   Python coordination, allocations and data movement separately. Name encodings read/written,
   allocation/retention and the safe parallel unit in the existing callable/packet contract. Only material
   remaining work gets a compiled/fused candidate; no per-object interpreter/native boundary or whole-volume temporary is
   introduced merely to wrap a small operation. If allocation evidence warrants private scratch, test
   its empty, boundary and concurrent uses against the reference twin.
5. **Whole-operation consequence.** Trace changed calls, reuse and downstream work through the real CLI.
   An equivalent implementation uses exact receipt/array checks; changed anatomical scope uses §7's
   native review and complete change account. Link existing matching-source checkpoint measurements;
   workers do not wait for the lead's later full profile or duplicate a profiler suite per family.

These are explanations with code/run evidence, not numerical optimization targets or demands for
perfect scope. EP0 includes this account across the graph, identifying same-value preparations both
within and between studies. The lead resolves a semantic gap before asking a mechanical worker to
implement it; a poor construction does not retire its useful capability (§1.1).

### 16.8 Native execution and cohort verification

Use the existing EP packets and production entry point; no parallel runner or new orchestration
framework. EP1–EP3 establish useful scopes, ownership and sharing; EP4 tackles remaining kernels.
P12 uses the same production principles once its MRI representation is specified.

- Keep a simple reference twin and pin actual inputs before changing arithmetic or storage. Test
  strict order/precision, nonfinite/unavailable handling, empty and clipped scopes, ties and offsets.
  Rust/C++/JIT candidates preserve outputs and named decisions; changed floating reductions are not
  silently treated as equivalent. A fused kernel's reference is the plain composition of the prior
  references, not a replacement tailored to its output. Exact agreement is checked within each frozen
  supported environment; no cross-platform floating bitwise identity is asserted. Record relevant
  BLAS/OpenMP/Numba thread settings with the environment. Count conversion, copying and dispatch costs
  as part of the call. Compile/fuse at a useful batch/context boundary when warranted, rather than crossing the language
  boundary for each pixel. Keep development/profiling dependencies out of the production import path.
- Reuse long-lived worker initialization where useful, with source/version-correct compiled caches
  and immutable setup. Verify first process start, available warm-cache start and subsequent studies;
  cold compilation is a separate reported condition; compare warm with warm and cold with cold. Use
  the existing bounded worker route, not a new daemon or service. Offline production cannot depend on
  downloading a compiler, model or package mid-run. Maintain the existing supported reference route where needed.
- The lead measures the actual serial and parallel cohort routes after integration. Choose worker
  count and native-thread counts together from measured per-study residency and the execution host's
  CPU/memory limits; do not multiply process pools by unconstrained native threads. Bound in-flight
  studies, results and serialization queues. Include decode, transfer/IPC, hashing, compression and
  output costs, and retain the existing single receipt/output ownership unless explicitly repaired.
- Reuse the existing labelled/public/proof runs for a small multi-study account where possible.
  Verify different dimensions, sequence/geometry/calibration dependencies, identical slice indices in
  unrelated acquisitions, and repeat processing in one worker. Enumerate mutable module/lazy state
  and check A then B, B then A and B alone for two existing studies where warm reuse is changed;
  compare their individual receipts, ignoring only existing non-semantic telemetry. Include an existing
  missing/failed-input case where available to check cleanup; do not create a new anatomical accuracy campaign. Confirm
  study-scoped state resets, invariant preparation is reused, and serial/parallel answers agree.
  A rising process high-water RSS alone is not retained growth: inspect live ownership/allocations
  over completed studies before diagnosing a leak. Count shared backing once per ownership account.
- Capture final ordinary elapsed time, peak residency, persisted bytes and actual work/reuse counts
  with source/environment/input identities. Diagnostic runs remain separate (§16.3). Compare the same
  cohort and settings; isolated kernel gains do not imply proportional competition gains. Account for
  startup once, per-study work across inputs and shared setup at its actual lifetime. Record remaining
  broad work, recomputation and storage-contract gaps explicitly; do not invent linear scaling or a
  hardware-independent speed-up from one proof study.

The existing required check whole_operation_account includes the five statements in §16.7.
For packets changing cross-study lifecycle/sharing, add reuse_lifetime_isolation; for compiled/native
implementation changes, add reference_twin and native_execution_boundary. These names appear in the
prompt, schema and script's required-check list when applicable. The lead's final cohort account is
part of §16.5, not a prerequisite that cycles back into a pre-integration worker check. Unmeasurable
claims remain unmeasured; worker outcomes and the correctness gate stay as already specified.

Grounding and second-reader record for §§1.3, 16.6–16.8: B +
production-thesis-contract-20261019T014732Z/ holds the user request, own reading written before the
consultation, inlined whole thesis/plan units, the local Claude Max CLI's Fable response and the
Codex adjudication. The source of the engineering contracts remains the user's request and thesis.
That dated evidence is not a second current-state record or a production performance measurement.

### 16.9 Competition resource envelope: W8b storage closure and W10 verification

Rohan explicitly requested: «Make those competition constraints explicit in the build plan and
workflow—W8b must resolve storage, W10 must verify the full compute envelope.» This is a production
requirement throughout construction, not a numerical objective for anatomical definitions. Useful
priors, measurement fidelity and native competence still follow §§1, 7 and 14–15. The existing ban on
arbitrary timing/RSS targets does not waive actual execution limits.

#### Source-backed deployment constraints

Verified 2026-10-19 UTC against the official competition Code Requirements, Dataset Description and
Efficiency Prize Evaluation pages, and Kaggle's notebook Technical Specifications. Save/recheck the
current source and actual selected environment at W8b/W10 and final packaging; the competition's
nine-hour limit overrides the general notebook documentation's longer editing-session allowance.

| Constraint | Published envelope / production obligation |
|---|---|
| Notebook elapsed time | CPU and GPU submissions: at most 9 hours (32,400 seconds). Account for the whole offline notebook: environment preparation, imports/JIT, discovery, decoding, recognition, later supplied stages, serialization and final output. A kernel-only timing is insufficient. |
| CPU route | 4 CPU cores, advertised 30 GB RAM. Submission CPUs are Intel Skylake under the current notebook documentation. Record actual CPU, available memory, process/thread settings and image; local Apple timings are not target-hardware measurements. |
| GPU route, if deliberately selected | The documented P100 and dual-T4 notebook routes have 4 CPU cores and advertised 29 GB host RAM, plus their GPU resources. GPU use is permitted, not required. Account for host and device memory separately; selecting a GPU does not remove the notebook elapsed-time limit. |
| Saved output | Advertised 20 GB in /kaggle/working for all saved files combined, not per study or per output family. Include retained arrays, receipts, logs, packages/compiled caches placed there, temporary write peaks and eventual submission.csv. |
| Scratch | Additional space outside /kaggle/working is session-local. Measure the actual available quota and peak use; it is neither unlimited nor durable. Do not silently turn required retained evidence into disposable scratch. |
| Network / executable environment | Internet disabled. Bundle runtime dependencies and target-compatible compiled artifacts, or compile from already available dependencies offline. No runtime consult, download or development/profiling dependency is part of recognition. |
| Workload | Host describes about 1,300 hidden test studies, not an exact constant. The supplied example is a small replacement set. Enumerate the studies actually mounted at runtime; use the host estimate only in labelled capacity planning. Sequence counts, dimensions and transfer syntax vary, with a long slice-count tail. |
| Final output / later stage | One submission.csv with the competition's study identifier and twelve probabilities, after the human-specified diagnostic mechanism exists. Efficient recognition is a prior milestone, not a substitute for that output or its inference specification. |

Sources: [competition overview/code requirements and efficiency evaluation](https://www.kaggle.com/competitions/rsna-knee-abnormality-detection/overview),
[data description](https://www.kaggle.com/competitions/rsna-knee-abnormality-detection/data),
[notebook technical specifications](https://www.kaggle.com/docs/notebooks).
The efficiency prize uses both predictive performance and RuntimeSeconds / 32,400; runtime savings
alone establish neither eligibility nor a winning score. This does not introduce AUC as a ground-layer
anatomical acceptance target. GB is the platform's advertised unit: record actual byte quotas and
measurements rather than silently treating GB as GiB.

#### W8b must resolve storage before its gate can close

EP3b includes the minimum concrete lossless storage/layout/placement repair needed to meet this
envelope, through the existing production entry point and every real writer/reader. Prefer compatible
existing-format changes. If a format/address schema must change, version it, update every consumer and
verify reconstruction; do not leave a known storage overflow merely as an advisory or defer it to P13.
The explicit 2026-10-20 competition retention decision in §16.6 applies: retain complete object
outputs and necessary measured information/provenance, and release consumed intermediates after
verified publication. No additional dropped object information, precision change or unrequested
asynchronous writer follows.

- Inventory ownership and on-disk sizes for both output families, receipts, retained evidence and
  supporting runtime files. Distinguish physical bytes from logical reconstructed arrays and shared
  backing. Measure live write/replace peaks and concurrent writers, not only the final archive size.
- Use the current source's available cohort, with per-study variation, to demonstrate the solution
  and plan storage for the host-described scale. The old proof probe saved 28,877,034 bytes; repeating
  that size over an illustrative 1,300 studies is about 37.5 GB. This is a dated extrapolation exposing
  the issue, not the current cohort's measured size or a new bytes-per-study target.
- Specify durable output versus session-local working storage, their actual mounts/quotas, lifetimes
  and all downstream readers. Reduce duplication/materialization and use lossless representation or
  placement consistent with retained-information contracts. Scratch may hold genuine transient work;
  moving required final object evidence there and losing it when the notebook ends is not a solution.
  Consumed intermediate lens files are genuine transient work under the explicit retention decision.
  Verify final object support/value addresses remain readable after those intermediates are removed.
- Reconstruct all retained arrays and decisions through the actual readers/addresses and compare
  values/dtypes/shapes/digests as appropriate. Verify same output in serial/parallel operation, bounded
  pending results and temporary-file peaks, and named behavior for unavailable or exhausted storage.
- The W8b acceptance record supplies the implemented solution, source/configuration, measured bytes
  and peaks, workload-scale account, retained-information proof and remaining uncertainty. A known
  quota overflow fails acceptance; an unmeasured/unresolved capacity claim stays INCOMPLETE under the
  existing workflow outcomes. W8b cannot close by saying that a future storage task will resolve it.

#### W10 must verify the full recognition compute envelope before its gate can close

Run the integrated no-draw production operation with its actual storage solution, on the selected
Kaggle route or a documented offline Linux environment reproducing its CPU/RAM/storage restrictions.
Use target-compatible native/JIT artifacts; a macOS binary/cache or an isolated benchmark does not
verify the submission environment. Record any difference from real submission hardware explicitly.

- Measure fresh-process startup including relevant compilation/cache preparation, decode, recognition,
  retained state, IPC, hashing/compression/write time and final receipt output. Include the parent and
  all workers in memory accounting; record peak host/device memory separately where relevant. Verify
  actual worker/native-thread limits, bounded queues and completed-study state isolation (§16.8).
- Exercise serial/parallel, proof/bursa, public input and the available labelled cohort using explicit
  run roots and source/environment pins. Include available larger series, dimensions and supported
  transfer syntaxes. Compare reference/candidate and serial/parallel receipts; inspect intended
  anatomical changes under §7. Reuse these runs for capacity evidence rather than profiling per object.
- Report the measured workload/counts, input range, elapsed time, RAM and disk peaks separately from
  the planned hidden-workload capacity account. Use the host's approximate study count and measured
  variation/overheads to account for target-scale runtime/storage; state assumptions, uncertainty and
  remaining headroom. A public-example run or one local proof study is not a full-scale validation.
  Inaccessible hidden data is not required at W10: label projections as projections, never as measured
  hidden-test performance. Do not call unavailable target-environment evidence a supported check.
- Compare the complete recognition capacity account with 32,400 seconds and actual RAM/disk limits.
  Record remaining time/memory/storage for the not-yet-specified encoding/diagnosis and final output.
  Do not assign those stages zero cost or consume the full allowance and call the future notebook fit
  established. A reserve is justified by the current work account and uncertainty, not an invented
  fixed percentage; unspecified later costs remain explicit and are measured when supplied.
- Exercise the explicit competition-output lifecycle as well as the development route: fresh owned
  output roots, complete per-study final products verified before cleanup, compact object receipts,
  no active references to deleted intermediates, and no cleanup on publication failure. Include final
  product bytes, intermediate/write peaks and bounded concurrent-study scratch in the account.
- Recheck W8b's storage closure on W10's completed source and actual concurrency. Known overflow,
  stale source, missing consumers or unresolved required capacity evidence cannot pass by a green
  test suite/CodSpeed replay. Use the existing VERIFICATION_FAILED / INCOMPLETE / STALE_INPUT meanings;
  no second outcome engine or new generic performance framework is introduced.

Applicable W8b worker prompts, return schemas and required-check lists add
competition_storage_envelope alongside reconstruct_all_arrays. Applicable W10 packets add
competition_compute_envelope, competition_storage_envelope, offline_production_route and
downstream_headroom_account. Their reports carry the evidence above, with measured/projected/unknown
clearly separated. Worker-local checks do not await a future lead profile: the lead owns final
integrated target-environment and workload-scale verification. P11 recognition completion includes
this account; P12/P13 must recheck it after their actual work is added. Final notebook execution and
submission schema verification remain P13, not permission to postpone recognition-stage capacity work.

## 17. Approved squint-first production build — 2026-10-21

Rohan: «Good. Save this in the build plan and agent context, then launch the build wide with native agents and Claude Max. Get the squint-first production pipeline working and run the private Kaggle dry run.» This supersedes the old P13 waiting state, cohort healthy-reference prerequisite and full-reconstruction inference default. High-resolution products of the 58 labeled studies bootstrap individual object/state buckets. Production reads input-available squints, locates objects using current-study anatomy, recalls normal/condition presentations, combines condition evidence under sourced necessary/sufficient/supporting contracts, and performs only question-directed bounded zoom. Numeric output is continuous and preserves defeated < open < assigned ordering; categorical findings remain separate.

Authoritative design: docs/AI_DIAGNOSTIC_DESIGN.md. Frozen engineering interfaces and ownership: docs/SQUINT_PRODUCTION_CONTRACT.md. Wide lanes: shared squint writer; bootstrap compiler; anatomy-constrained locator and recall; domain contracts and ranking; report teaching/admission; root production integration; Kaggle packaging/verification. Native and authenticated local Claude Max builders implement independent units concurrently. Root integrates and owns the actual runner; no serial whole-project gate per candidate. Two-sign intent tests and Detective pin pure decisions; real-command and private-Kaggle runs verify actual integration and resources. The existing gate remains intact. No competition submission is authorized by the dry run. Live state and worker handles reside only in §13's current packet.

§17 execution clarification from Rohan: “Let warranted configuration recall decide.” The whole-condition case remains individually sourced and role-qualified. It may assign or defeat when warranted and uncontradicted by necessary anatomy; no numeric cutoff or clinical lesion-count rule is invented. A clean necessary negative remains decisive; opposing warranted descriptions stay visible.

§17 full/cheap coexistence binding: the same individual case retains its raw-scan cheap profile and the exact full sparse object record, with shared fingerprinted interpretation context and original source identities. Configuration roles link to the canonical object payload. Publication reads every available full payload through the existing canonical adapter; the production loader does not expand full CountBundles. Full readback works offline without source H5 access. This is the storage implementation of Rohan's supplied cell figure, not a change to diagnostic meaning or permission to merge incompatible layouts. SQUINT_PRODUCTION_CONTRACT and SQUINT_RUN_GUIDE give the schemas and public readers; §13's packet alone records measured verification.


### Production execution correction, 2026-10-21

Rohan identified the checkpoint's exhaustive locator and context-only configuration decisions as defects to fix before other work. The binding correction is SQUINT_PRODUCTION_CONTRACT.md §Required production correction: anatomy before enumeration; his literal audit is in the latest conversation. Required order: preserve the tested checkpoint; replace full-leg sliding with anatomy-first finite physical windows; enforce defining-tissue coverage for configuration authority; give each study its own budget and ship invariant recall preparation; run the 58-study held-out entrypoint evaluation with complete source exclusion; then time the corrected private Kaggle run and scale. Record per-condition identified/abstained/wrong and value ordering. Storage/portability and further Detective work can wait. Live implementation/worker state remains solely in the §13 packet.

### Squint-to-training execution detail, 2026-10-21

Rohan: «Use the fable consult over the Claude max subscription, then plan out a wide build to meaningfully upgrade this codebase so that we can FINALLY get to AI training properly». [SQUINT_TRAINING_BUILD.md](SQUINT_TRAINING_BUILD.md) is this section's execution appendix, not another master plan. Read it before dispatching or integrating upgrade workers. It records the independently checked Max consultation, existing versus missing joins, frozen meanings, seven disjoint worker lanes plus root integration, dependency waves, two-sign checks and the engineering/visual training-readiness distinction. §13's packet alone owns current jobs and results.

The upgrade connects current-study structural bone evidence to the locator, addressed object/support/context territories to paired cheap/full profiles, predeclared question banks to exact recall and preparation, one excluded memory view to every consumer, and existing independent admission to an executable teaching/publication/evaluation round. Preserve the tested arithmetic, case scopes, warranted-configuration authority and readout. No perfect skin/contour prerequisite, transplanted patient stencil, substituted window-width bone measurement, arbitrary cross-view centre threshold, new healthy reference or full-anatomy production prefix is introduced. Changed observational meanings require explicit compatible writer/corpus identities. Whole-project gates run per integrated batch, not per worker; the competition envelope and verified private runtime pins remain requirements.

## 18. Thin object bootstrap — Rohan's execution order, 2026-10-21

The complete human clarification and admission answers are in
`docs/conversations/2026-10-21-ternary-buckets-and-squint-orchestration.md`.
This is the next application of the existing representation, not another anatomy-definition campaign.

The complete bootstrap -> corpus construction -> agency learning -> runtime-memory binding is
[CLASSICAL_AI_BUILD_DESIGN.md](CLASSICAL_AI_BUILD_DESIGN.md), this plan's design appendix, not a
second master plan or live queue. Read it whole before implementing these stages. Rohan explicitly
clarified that K-lines BOTH build the basic recognition corpus needed to construct the training
dataset AND remain part of the classical Minsky-style AI stack. Filling buckets is an enabling
operation, not the entire agency-learning algorithm. The earlier “equivalent of training” analogy
must not erase this distinction.

1. Consume the authored relative map and anatomical relations as cheap sanity checks while resolving
   candidates. An observed anatomical contradiction prevents that interpretation. A missing neighbour,
   overlapping coarse bounds or unavailable view is unknown, not a negative finding. The numerical
   scatter of unreviewed outputs from the 58 studies is not a tolerance. Record each checked relation,
   its source and the observation that supported or contradicted it; a plausible location never proves identity.
2. Build the starting fill from actual native pictures of candidates in the existing 58 teaching
   products, with stable source addresses and the paired cheap/full bundles. Rohan's correction:
   «We fill everything we can with ALL correct candidates.» Start with clear examples, then admit
   every additional visually warranted example; do not impose an arbitrary small final seed count.
   A reviewer may make the common-sense visual call; record the actual reviewer, never attribute an
   agent's call to Rohan. Messy borders do not prevent a correct object call. If particular views are
   mistaken, retain correct view evidence at its explicit scope rather than discarding the object or
   teaching the wrong facet. Genuine ambiguity remains unresolved. The automatically compiled memory
   is a source of proposals, not a trusted fill before review.
   Retain confirmed negative calls as usable negative cases at their actual question/view/region
   scope, not only rejection notes. An incorrect proposed name can teach against that interpretation
   without supplying another identity or a clinical diagnosis. Missing matches and unresolved calls
   do not teach negatives. Ordinary negative memories and specialized near-miss censors are distinct.
3. Expand by HDC recognition against that fill. Rohan explicitly authorizes a high-confidence identity
   match, with common-sense anatomical checks, to enter its object bucket. Preserve the recalled seed
   lineage and what was asserted. This does not invent a clinical label or turn a routed identity into an
   independent radiology observation. Unresolved or conflicting candidates stay available for review.

**Answering versus automated admission.** Unknown anatomy remains neutral when answering an identity
question. It cannot by itself warrant a new automatic memory addition. Require confident joint recall,
affirmative applicable anatomical support for the claimed scope, and no known contradiction. Unknown-only
anatomy leaves a proposal, not a rejection. This does not demand every relation or all three planes;
use directions available native geometry actually constrains. A direct warranted visual call teaches
independently and does not wait for the automated filter to be complete. This is the engineering binding
of the subsequent review exchange, not an additional verbatim quotation attributed to Rohan.
An anatomical pass is a law check that records location, not tissue (thesis §11.5). Plausible but
wrong tissue is stopped by negative cases in joint recall, never by requiring the check to recognize
tissue alone; the map's distances aim the search and are not admission limits. The first growth round's
admissions are inspected before its child becomes the next parent; later rounds are spot-checked, not
held for a picture check (CLASSICAL_AI_BUILD_DESIGN §7.1 and §13).

The completion contract is [the OpenSpec change](../openspec/changes/complete-signed-bootstrap-loop/).
Integrate signed publication and exact call adaptation, partial anatomical checking, signed frozen-parent
growth and active identity consumers in parallel where independent. Children must preserve the negative
and alternative store; whole-study exclusion covers all record kinds. No changed round may silently
drop negatives or rebrand already-confirmed teachers as newly learned examples. The worked example's
second round is withdrawn as evidence of growth. New tests pin existing boundaries; unmet integration
scenarios remain explicit OpenSpec tasks. Root owns actual entry-point and final-tree acceptance.

The growing corpus supplies task-specific experiences: observations, signed calls, expectations,
procedures and appropriately sourced outcomes. Agencies use those episodes to learn contextual
interpretations, significant differences, censors/splits and useful routes through the existing tools.
Their K-lines remain active in production recall and reasoning. Preserve independent clinical calls
and recognition-derived identity lineage as different sources; this distinction does not prohibit
the identity-growth operation Rohan authorized. No evaluation of a tiny unfilled memory replaces the
immediate work of supplying its positive and negative teaching examples.

Rohan's scope clarification: «This is a PURE categorization task, which is WAAAAAAAAY easier. Thus
warranting some cheap deviations from the full "thesis"». Neither exact borders, all three complete
outlines, nor perfect positional recovery is a prerequisite for a recognizable seed. Preserve the one
object across the views available and the distinction between its coarse and full descriptions. No
mandatory high-resolution production prefix follows. Use the already implemented compiler, readers,
publication and production entry point; parallelize bounded mechanical work through native helpers
and the local Claude Max CLI. Root owns meaning, visual inspection and integration. §13's packet
alone holds the active jobs, source pins and measured outcomes.
