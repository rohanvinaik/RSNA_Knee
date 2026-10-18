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
complementary views can unlock constraints neither supplies alone. Derived consequences make
held information usable; they do not create fresh evidence. No other-domain scaling constants,
new significance-score engine or corpus-induction system is imported into this ground layer.

## 2. Source checkpoint and present state

The latest accepted anatomy is RELATIVE_POSITION_MAP §§8.35–8.36: native axial/coronal PCL,
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
The 70 source files were rechecked before this documentation handoff; later changes require a
fresh pin. HEAD is `a118db8`; the accepted build includes extensive uncommitted/untracked work.
A commit hash alone cannot reproduce it. Preserve the working tree and source snapshots.

Accepted recorded scope:

| Group | Current contract; do not rebuild completed definitions |
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

Read the five required primary documents in AGENTS order and inspect their proof pictures.
Then MAP §§0/8.8/8.36, TARGETED_ANATOMICAL_COMPUTE, the full anatomical-priors conversation,
this plan and NEXT_SESSION_PROMPT. Relevant primary text:
`../cell_tracking/docs/pipeline_thesis/paper/what_an_object_is.md` §§4, 7, 13 and
`/Users/rohanvinaik/Projects/rohan-vinaik.github.io/papers/Core Documents/SIGNIFICANCE_WEIGHTING.md`.
Read whole logical units, never text-search fragments; archives stay invisible.

Check git state and workers, verify the accepted source manifest, and inspect the preserved
run invocations before running anything. All three continuation helper tasks completed; no
pending worker result needs polling. No preview is accepted production. Read every candidate
unit before copying it. Generate a fresh object/view inventory from receipts and maps under the
actual source pin; separate resolved native, native reading, laid, projected, trace and refusal.

### P1 — finish the ready sartorius scope candidate

Packet: B + `sartorius-scope-max-20261018/attempt-3-text-only/`.
Read `candidate-verification.json`, `candidate-test-history.json`, complete
`candidate/review-units/` and `candidate/focused-tests-final.log`. The isolated corrected
candidate passed 39 focused tests and Ruff; it is **not lead-reviewed, integrated or accepted**.
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

### P2a — shared rough leg/domain producer

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
Inspect AX11/12/14 and affected cartilage/fat outputs through actual DICOM frames. More seeds
alone do not establish better anatomy. No repeated whole-study recognition/fixed-point loop.

### P3 — pass known bones into patella/recess questions

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
| MCL | SAG, AX | Medial band outside medial compartment, femur to proximal tibia, deep to pes structures; known medial meniscus and joint line. |
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

## 8. P7–P10: finish the whole-operation structural retrofit

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
  and checked across consumers. No array dropping or hidden retention policy change.

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

Each task packet contains:

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
It runs Ruff, format, pytest, Import Linter and advisory deptry/ty/two Vulture scans. Read all
advisories; a passing blocking gate does not clear them. Use Hypothesis for geometry/cache/lossless
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
6. Run the full gate after the integrated increment; inspect advisory lists. Update RESOLVING,
   MAP and NEXT with the mechanism, accepted image, source/run evidence and exact remaining work.
   Keep a clean checkpoint before the next packet. Do not commit/push without the requested scope.

## 10. Local Claude Max implementation route

Rohan explicitly authorized the source/measurement handoff and requested the **local CLI**:
«I am providing that approval, but more importantly I want you to use the local CLI path.»
Use subscription-authenticated Claude Max for bounded code generation and audits as much as
reasonable; small Codex helpers can reconstruct images, run isolated tests and check addresses.
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

## 12. P12–P13: representation and eventual competition completion

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

Then package the same no-draw runtime for Kaggle, with runtime-only dependencies, fixed references
and the provided mount. Match the actual sample/gold schema for one study's twelve probabilities;
never serialize internal observation rows as a substitute. Verify public inputs, empty/missing
inputs and the real competition budget using the current official contract at that stage.
Submission/publication is a later requested action. Recognition capacity is a concrete completed
milestone before that dependency; do not label the whole competition solution complete early.

## 13. Context-stable continuation and stop points

NEXT_SESSION_PROMPT is the short entry card; this file is the complete remaining-work order;
EFFICIENCY_RETROFIT_PLAN retains E01–E24 issue history; MAP holds dated accepted mechanisms and
pins; RESOLVING holds anatomical definitions. Do not create another competing master plan.
The previous full plan and next-session prompt are preserved under H.

At each handoff save: current source manifest and git state, accepted run roots, commands and
exit status, inspected images, result/unknown semantics, changed outputs adjudication, ledger/
profile/gate findings, worker attempts/status and the **next single task ID**. Update existing
records in place while preserving dated acceptance history. A clean pause has no ambiguous
in-flight mutation or worker completion being represented as production success.

**Progress, 2026-10-18:** P0 done (`B + p0-inventory-20261018/`; bulk commit `7b61b54`). P1 accepted
(`B + p1-sartorius-scope-20261018/`): sartorius contrast bounded to the gracilis-target window, the
188-pixel sheet unchanged. P2a measured, not built (`B + p2a-leg-domain-20261018/`): on these
knee-framed acquisitions a leg window would cover 90–100% of every middle frame, and the cheap
envelope's one non-trivial result (bursa fat-suppressed coronal) is wrong.

**Exact next action:** P2b. Dispatch factual P2 tracing/early-domain image
packets to subscription workers in parallel where independent. Publish shared native bone
context before further dependent ACL/tibial-cartilage work. Continue the table through P11;
P12/P13 keep their stated primary-contract/human-specification dependencies. No fresh thesis
redesign, repeated consultation, commit, push or submission is requested by this handoff.
