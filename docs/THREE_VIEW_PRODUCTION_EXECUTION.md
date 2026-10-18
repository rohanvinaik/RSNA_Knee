# Three-view anatomical production build — execution contract

**Dated note, 2026-10-18:** `docs/FULL_BUILD_PLAN.md`, Rohan's plan approved for building, is now the
canonical remaining-work order. It supersedes the scheduling here and in COHERENT_BUILD_ROADMAP; where
this document's contracts differ from the plan's §§14–15, the plan governs. The execution record below
remains history; its definitions are in RESOLVING_THE_PARTS.

The active continuation roadmap, bounded worker contracts and session-resume order are
`docs/COHERENT_BUILD_ROADMAP.md`. This document retains the family contracts and execution record;
the roadmap incorporates the subsequent foundational useful-priors steering across every family.

Rohan, 2026-10-17: «We need to resolve every anatomical object in each of the three angles of view as a generic object, equally technically resolvable in any arbitrary input study, with a robust "platonic ideal" map of the knee as a series of anatomical objects with each having a relative position and causal relationship to each other». Then: «Plan it out, then make this the output of a single, coherent production pipeline, with sensible compute sharing and reuse where appropriate. Use the tooling outlined in global model context files, plus the ones in the CI gate, to plan out the build, then let's execute!»

This operationalizes FULL_BUILD_PLAN through the existing entry point. Its authority remains the original conversation, THEORY_OF_THE_CASE, OBJECTS_AND_CONDITIONS, HOW_TO_BUILD, RESOLVING_THE_PARTS and RELATIVE_POSITION_MAP §0/§8.8. At planning start the latest accepted increment is §8.16, not a finished three-view build. The current useful-priors criterion and targeted-compute guidance are in `docs/TARGETED_ANATOMICAL_COMPUTE.md`; later AI and diagnosis are still human-specified work.

## 1. One production operation and its output

**Foundational for every packet and existing stage:** anatomical relationships and useful approximate
priors determine where computation runs. They improve discrimination and efficiency together.
This is the `<object>` thesis applied to construction, not a separate optimization campaign.
THEORY_OF_THE_CASE Law 14 and `docs/TARGETED_ANATOMICAL_COMPUTE.md` govern the whole graph.
Rohan's full statement is `docs/conversations/2026-10-18-anatomical-priors-and-targeted-compute.md`.

The only production CLI remains scripts/run_interiors.py. A study enters once. Its sequence flags, actual frames, valid acquired samples and shared cheap stack readings feed native object-specific questions. The obvious bone/patella descriptions establish initial physical constraints; the anatomical ideal supplies expected native slices and in-plane locations. Useful rough bounds and relational priors focus later measurement; they need not be perfect segmentations, and later AI is not a prerequisite for using them. Each subsequent family reuses those values, reads the native image in the selected local region/slices, retains every description and refreshes the one map at its existing family boundary. Study workers compute independently; one parent writes receipts in request order. Drawing and diagnostic instruments remain development-only.

The coherent output for each object keeps native/laid/projected/read/unresolved provenance, source series and actual slice geometry, exact array/label/packed-row addresses, measured support and descriptive properties, independent view constraints and the resulting physical reference when defined. The same map keeps all ordered relative vectors and their unresolved endpoints. The descriptions remain available even when one view or a reference point is missing. A projected target guides recognition; its native evidence settles it.

Anatomical relationships belong to these descriptions and their actual consumers: attaches to, lies between, bounds, contains, lies superficial/deep to, and continues along a course. The relation is grounded in the objects document and primary anatomy. Each family records which measured neighbours constrain its question and uses those inputs directly. Relative vectors provide location; attachment/enclosure/course relations discriminate objects sharing a location or signal. Do not introduce a generic rule engine, a second anatomy pipeline or a new learned selector. Do not fabricate direct causality between anatomically unrelated pairs; all pairs still have relative positioning in the common web.

## 2. Build packets and dependency order

| packet | native descriptions to complete | shared inputs and relations | integrated result |
|---|---|---|---|
| A1 cavity descriptions | anterior recess axial, then coronal | already measured patellofemoral pockets, selected patella/femur sections, actual facing surfaces; cavity behind patella/in front of femur | new native cavity observations reuse existing pocket arrays; preserve fluid/wall/lining identities |
| A2 joint and capsule | joint axial, capsule sagittal | joint-line physical interval from sagittal/coronal bones; native transverse compartment; capsule external to cavity and its enclosed fat/tissue, distinct from inner lining | independent native section evidence, not a projected footprint or renamed cortex/fat boundary |
| B anterior/extensor | Hoffa and combined/separate upper pads: coronal/axial; both extensor tendons: coronal/axial; retinacula: sagittal/coronal (accepted with axial) | native patella, femur/tibia, extensor attachments, existing opposed sequence light, fat/recess seam and superficial/deep order | same objects described in longitudinal and transverse cuts; attachment and enclosure evidence retained |
| C compartments | sided menisci: sagittal/axial; femoral/tibial cartilage: sagittal/axial (sagittal companion rows and femoral axial native description accepted; tibial axial remains pending); ACL/PCL: coronal/axial | bones/joint/capsule; wedge and horn/body relations, bone-facing surface, ligament endpoints/course through notch | per-view descriptions of each existing concept, keeping original general-class outputs |
| D attachments | MCL/LCL/popliteus/ITB: sagittal/axial; biceps tendon: coronal/axial | completed fibula plus femur/tibia, sulcus, meniscal attachment and superficial band; existing biceps/LCL native searches | actual attachment/course constraints shared by neighbouring objects |
| E posterior/medial | both gastrocnemius heads, semimembranosus/semitendinosus/gracilis/sartorius, artery/vein/bursa: remaining sagittal/coronal | existing axial sources, patient axes, bone level, shared dark/grey/fluid bodies and traces that point; bursa's visible example study | native longitudinal descriptions, separate vessel/tendon identities and named unresolved alternatives |
| F catalogue closure | marrow, field classes, general meniscus/recess/cartilage entries and every emitted slot | existing bone interiors, diffuse tissue masks, relationships to specific objects | explicit output addresses and three-view field descriptions; missing unique point remains explicit rather than fabricating one |

Within a packet, do the smallest prerequisite-complete increment first. The table is a dependency order, not a reason to wait for exact boundaries, perfect exclusion or proof of a complete boundary, or to force a single shared slice on different objects. Useful priors should restrict where dependent measurements run; they are not annotations after an unnecessary whole-image pass. No object's native rule may use a coordinate, component number or grey level copied from a competition example. Inspect actual pictures before implementation; document the few anatomical/lens relations. Preserve competent earlier rules and their observations. Do not treat maximum area as a universal best-slice definition. Follow `docs/TARGETED_ANATOMICAL_COMPUTE.md` for the current human criterion.

## 3. Compute ownership and reuse

Existing runtime mechanisms are the starting point, not things to replace. The read-only tool inventory is data/readings/collapse-20261017/production-build-planning/existing-compute-lineage-inventory.md. The per-study computing scope keeps values under their actual keys; the ledger distinguishes made from handed-on and produced from consumed. Save is not a consumer.

| value | existing owner/cache | sharing requirement |
|---|---|---|
| volume/geometry/sequence metadata | study/series input and plane_frame | one read/context; physical coordinates, no equal-index assumption |
| valid samples/background/squint | finite_of, existing background/squint stages | one series reading; cheap pointers only, no repeated full anatomical analysis |
| native lens/field | lens_of and field_of, series UID plus slice | all objects using that slice share the same reading; borders only with --draw |
| axes/light/distances/sizes | Measures and existing once keys | reuse identical inputs; changed supports require their real context, never a stale result |
| matches/projections/coarse blocks | matched, carried bone footprints, coarse axial cache | reuse geometry/target digest/block context; retain actual native versus projected provenance |
| selected pocket/region/band and its surfaces | existing anatomical producer | retain useful byproducts; derive companion observations from validated support without making the same union/mask twice |
| map | existing MapContext/StudyMap family boundary | refresh after new native constraints and before dependent search, not a repeated full recognition loop |

A new measurement is justified by an anatomical distinction visible in the images. If multiple objects need it, give it one producer and explicit consumers; retain computed evidence. Do not mark a diagnostic output as consumed merely because it was saved. Remove duplicated work only after static/runtime trace identifies the same operation and a paired output comparison pins equivalence. JIT/native optimization follows measured hot work.

## 4. Tool-driven implementation and acceptance

1. Read whole anatomical definitions and actual source pictures; state the intended native relation. Serena reads complete symbols and references: find both production paths, the consumers and any duplicate producer before an edit. Subagents use whole-symbol AST/Aider maps within allowed nonarchive scope, and report facts only.
2. Implement within that producer/family and existing persistence points. Every decision has a named code; unavailable, unvisited, malformed, tied and measured-empty remain distinct. Tests call actual functions directly and exercise negative as well as positive cases. Type-check nontrivial changes.
3. Run the real CLI without drawing into separate scratch receipts, inspect exact addressed native supports and all affected views, reconstruct counts/rows/geometry, and verify earlier observations/refusals survive. A tuple of selected plane indices alone is not anatomical evidence. The two-study coronal-lining-production run is the starting preservation baseline.
4. Compare static references with actual runtime calls and ledger ownership. Use stdlib cProfile for an initial complete CLI caller/count baseline (available in this interpreter); installed development tools may refine a specific measured question. Hamilton is an installed development dependency, not the current production orchestrator. Its availability does not justify replacing the pipeline or fabricating a second hand-maintained graph. Optional profiling packages are currently absent from this interpreter; do not claim their measurements.
5. Run scripts/ci_local.sh whole: Ruff/format/tests/production import contract, dependency/type checks, both Vulture scans. Read advisory findings and runtime unread products; a passed blocking gate does not make them empty. Pure decision pinning/properties use Detective/CrossHair/Hypothesis when the claim calls for them; do not substitute an exhaustive specification campaign for the human's anatomical demonstration criterion.
6. After each accepted family wave, run specified studies, all 58 labelled studies and public test through that same path, with source hashes fixed. Measure actual pair-vector range/sample SD only; no study-fitted ideal, cutoff or search prior. Keep current coverage, known localization errors and genuine unknown SD explicit. Profile drawing-off production and preserve outputs for any efficiency change.

## 5. Finish line for this build

Every requested anatomical concept has a generic, justified native description in sagittal, coronal and axial views, connected to the single production path and demonstrated competently on an appropriate visible study. Those descriptions and the actual physical geometry establish one knee map with relative vectors and meaningful anatomical relationships. Each search uses resolved neighbours and native image evidence; shared work is computed once. The output retains evidence and uncertainty rather than papering over missing views. Field/diffuse concepts retain their actual three-view support without an invented unique point.

This milestone precedes the object's thesis's exact encoding/extent/volume layout (§§7/13), the later human-specified AI/diagnosis and competition submission schema. Those dependencies remain in FULL_BUILD_PLAN; they are not silently implemented as assumptions during view recognition.

## Execution record

- Planning baseline: accepted coronal lining (§8.16), six complete proof references; source hashes match the frozen run.
- Global composition/performance instructions, existing source/cache contracts and CI were read. Three local factual inventories assigned; lead retains anatomical meaning and build decisions.
- First implementation: A1 axial anterior recess, using existing native patellofemoral cavity evidence; no new image measurement or duplicate fluid union. Native image/provenance and prior-output preservation must be verified before completion is recorded.

- A1 axial anterior recess accepted at RELATIVE_POSITION_MAP §8.17: both native paths connected,
  exact support reuse, earlier arrays/observation prefixes preserved, final full gate 791 tests.
  Coherent output keeps definition_decisions/search_refusals independently of arriving observations;
  their categorical sources are collected once. Next: coronal anterior recess from native evidence.


### A1 coronal anterior recess accepted

RELATIVE_POSITION_MAP §8.18 closes A1: native connected coronal cavity body, map-guided cheap depth/in-plane sampling and original physical source reuse; earlier arrays/observation/refusal prefixes retained; full gate817. Exact accepted production source snapshot is retained under coronal-anterior-recess-bridge/accepted-source. A2 is in progress: sagittal capsule relative-band implementation after actual-frame visual acceptance; axial joint still a native-evidence preview. No A2 result is yet accepted. All B–F work remains as listed above.


### A2 sagittal capsule accepted

RELATIVE_POSITION_MAP §8.19 records the native external relative-minimum band, existing physical-source reuse and actual map depth/in-plane consumption. Full native reads occur only at two candidate slices; old arrays and prefixes remain, normal parallel/profile/final outputs match, and the final full gate passes 862 tests. Source40files are preserved separately for this accepted increment. A2 axial joint is in implementation from two-source joint-location concurrence and actual native signal. No claim that it or B–F is complete. The output inventory confirms typed anatomical relations are still a required F deliverable; current vectors and free-text reasons alone do not satisfy that part.


### A2 axial joint accepted; typed definition links connected

RELATIVE_POSITION_MAP §8.20 closes Packet A2: two independent native joint locations and actual axial fluid bodies supply the joint's missing axial description, preserving earlier compartment and pocket identities. Proof joint 18/15/14 now contributes the ninth complete reference; all prior arrays remain, and the ordinary parallel run matches the profiled run. Gate: 887 tests passed, with Vulture advisories retained. The same object builder also emits 34 sourced typed anatomical definition links over 32 subjects; these are definitions, not claims that every relation was measured. No second recognition path or image pass is added. Other F requirements remain. The source-fixed Packet A 58-study refresh is running; B starts with anterior/extensor native cross-view pictures.


### B1 axial extensor descriptions accepted

RELATIVE_POSITION_MAP §8.21 records native axial patellar/quadriceps bodies, generic exact-input depth reuse and shared native body context. Actual acquired frames were inspected; all previous proof/bursa and public evidence is preserved; final parallel and first profile outputs agree. The full gate passes 895 tests, with Vulture advisories retained. Their coronal planes remain missing. Packet A’s completed 58-study snapshot is frozen separately; it is not a measurement of this later code. Next: native coronal extensor descriptions, then the remaining B–F views, retaining the one production entry point and family handoff.


### Native coronal extensor descriptions, 2026-10-17

RELATIVE_POSITION_MAP §8.22 records the accepted coronal patellar/quadriceps bodies. Actual sagittal
and axial locations must meet the same native coronal dark body; projection/native context/persistence
operations are shared with the axial reader. Both sequences' actual coronal4/5 bodies and empty
patellar6 readings were inspected. Tendon key planes now complete two additional proof references
(11 total, 110 complete ordered pairs). All prior arrays and categorical information remain; first
profile/ordinary parallel runs match, public inputs add only named source refusals, and the whole
gate passes 901 tests with Vulture advisories retained. Source44files were pinned before the run.
Remaining B: native coronal/axial fat pads and sagittal/coronal retinacula, then C–F. The source-fixed
58-study checkpoint remains Packet A; it is not a measurement of this later code.

### Shared late-family persistence

Middle artifacts are now written once after the existing late families. This exposes the original
axial retinacular results to the next native cross-view reader without duplicating their search or
rewriting artifacts. Source-fixed proof/bursa and public comparisons preserve every B2 output,
including maps, objects and telemetry; the first gate passed 920 tests. Reproducible comparisons and
hashes are in `full-build/final-persistence-bridge/` under the 2026-10-17 readings tree. Retinacular
and fat-pad native bridges are being implemented; no later anatomical acceptance is asserted here.

### Retinacular planes and sagittal cartilage companions accepted

RELATIVE_POSITION_MAP §§8.23–8.24 record the accepted additions. The proof selects native
retinacular planes medial sagittal12/coronal5/axial22 and lateral sagittal32/coronal12/axial21;
their addressed supports contain 73/58/70 and 159/82/71 pixels. The medial sagittal guided
candidate at slice5 remains recorded with 11 wall pixels; the stronger source-profile candidate at
sagittal slice12 was checked and becomes the selected plane with 73 pixels. Medial coronal slice5
remains selected with 58 pixels. These sections do not assert thickness or full course; lateral
sagittal support retains its recorded adjacent capsule/course overreach.

Six sagittal cartilage observations at existing saved rows (slices15,17,22; femoral/tibial counts
215/259, 307/297, 236/250) were added without an image pass or array change. Existing candidate
rows remain in order, and the known tibial overreach remains. The frozen proof/bursa and public
comparisons preserve prior outputs, first and ordinary parallel runs match, and the full gate
passes 952 tests. Evidence is in
`data/readings/collapse-20261017/full-build/retinacula-cartilage-checkpoint/`; inspected native
retinacular figures and exact addresses are in
`data/readings/collapse-20261017/full-build/retinacula-cross-view-bridge/stronger-profile-final-images/`.
The later live fat-pad bridge and development-only axial cartilage work are outside this accepted
checkpoint. The direct Fable API consultation is complete; its lead comparison is retained at
`data/readings/collapse-20261017/full-build/fable-native-geometry/`.

### Native coronal and axial fat-pad descriptions accepted

RELATIVE_POSITION_MAP §8.25 records separate native descriptions for Hoffa, quadriceps and
prefemoral fat, plus the same-slice quadriceps/prefemoral suprapatellar union. Existing native
locations and map depth/in-plane guidance point to candidate questions; actual native support
decides. Hoffa uses the unique largest original native territory touched by its selected physical
source. Q/P candidate basins use a new shared physical-gradient measurement: valid neighboring
acquired samples at actual pixel spacing feed SciPy's image-filtered-gradient/IFT operation with
linear uint16 quantization. This is a new measurement lens, not an anatomical threshold; earlier
proof lenses remain unchanged. H/Q/P physical sources are selected identified sagittal-FS sections
by physical area and converted to LPS once; the composite Q/P source is retained as context, never
a fourth seed. Native peaks, margin and measured coarse femoral core compete with Q/P source
locations.

The counterpart fat-bright acquisition is sampled at candidate coordinates using its own
femoral-marrow calibration and actual planes, dimensions, thickness, bounds and margin. Positive,
negative, disagreement and unknown classes remain distinct. The established inclusive
fat-under-skin comparison and strict-above-fluid comparison remain unchanged. The coarse femoral
core is a geometric competitor/exclusion where measured, not an exact boundary; two millimetres
refers to coarse-block context, not fat-body opening. Composite support resolves only when both
same-slice component supports are usable.

The lead inspected all proof addressed frames and accepted the local descriptions with their
recorded limits: patchy/broad Hoffa support, including a posterior candidate that is marrow;
quadriceps coronal6 includes neighboring muscle/fat; coronal8 Q/P sections are limited; axial27
Q/P support retains only small compatible portions of larger candidates, and prefemoral axial29
is a strip. No per-study tuning follows these cases. The source-pinned proof/bursa serial and
parallel outputs match, prior arrays and categorical prefixes remain, public prior outputs remain,
and the gate passes 963 tests. Evidence and source hashes are under
`data/readings/collapse-20261017/full-build/native-fat-pads-checkpoint/`.

Packet B’s source-pinned cohort now completes: 58 maps, 336 interiors records, 43 main records, and 0 unread study inputs. Across the 2,494 study/object map entries there are 116 complete and 2,378 partial entries; these are coverage counts, not accuracy claims. The pair report contains 1,806 ordered pairs. For each reported metric, 1,534 pairs have n=0, 252 have n=1 and 20 have n≥2; sample SD is null below n=2. The declared `construction_consistent` field has zero inconsistencies, which is a position-construction check, not anatomical proof. All 80 native fat boolean support addresses validate against saved rows, slices, counts and actual frames. The corrected cohort audit counts native rows from both receipts, separates readings from resolved supports and cross-checks 5,879 native rows against the production combined object summary. At the Packet B audit, all 56 source hashes matched its source snapshot and live tree. Receipts are under `data/readings/collapse-20261017/full-build/packet-b-cohort/interiors/` and `data/readings/collapse-20261017/full-build/packet-b-cohort/main/`; pair report files `cohort-pair-variation.json` and `cohort-pair-variation.csv`, the source pin, detailed audit and summary are under `data/readings/collapse-20261017/full-build/native-fat-pads-checkpoint/`. This is Packet B’s source epoch. Packet C remains under construction; its live edits are outside this snapshot, and no C axial production result is accepted here.

### Native axial femoral cartilage accepted — 2026-10-18

RELATIVE_POSITION_MAP §8.26 records the new proof axial femoral-cartilage support at slice14
(994 pixels, bool row0 in `a4_axial_femoral_cartilage_support`); selected planes are sagittal17,
coronal15 and axial14. It is constrained by the existing
sagittal and coronal native source locations and existing enclosure/marrow/cartilage measurements.
The lead inspected the addressed frame and accepted it as a local native description with the
recorded cortex/adjacent-tissue overreach. Corrected serial and parallel receipts match. Prior
observation/refusal prefixes and all existing main arrays remain; six proof retinacular profile
arrays changed with refreshed map guidance. Public prefixes/maps remain exact; four named
unresolved rows and four source-context arrays were added, with no resolved public row. The
source-fixed audit, hashes and retained first failed run are under
`data/readings/collapse-20261017/full-build/axial-femoral-cartilage-checkpoint/`. Corrected serial,
parallel and public receipts are in sibling directories `axial-femoral-cartilage-source-fixed/`,
`axial-femoral-cartilage-source-fixed-parallel/` and `axial-femoral-cartilage-source-fixed-test/`,
each with `interiors/` and `main/`. Its source-fixed 58-file pin matched; subsequent formatting
normalization was AST-equivalent. The full gate passes
982 tests, with Ruff/format/import/dependency/type checks clear and Vulture advisories remaining.
This proof increment does not refresh Packet B's older 58-study cohort totals. C axial tibial
cartilage, sided menisci, ACL and PCL remain pending; development previews are not production
evidence. Human steering and the completed Fable consultation are recorded under
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/`; Fable's recommendations are
advisory, not an accepted optimization. The human's useful-priors criterion is authoritative in
`docs/TARGETED_ANATOMICAL_COMPUTE.md`.


### Shared common-map handoff accepted — 2026-10-18

RELATIVE_POSITION_MAP §8.34 records an execution-only change: converted observations from 15
completed families are offered once to the existing map before later dependent guide requests.
The converted rows are reused at final idempotent closure; original append/save order and existing
filtering/deduplication behavior remain. The 69-file
source pin, 1,038-test gate, raw 172-event proof trace, output comparisons and independent checks
are retained under
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/immediate-map-handoff-production/`
and the sibling `immediate-map-handoff-checkpoint/`. The proof/bursa outputs record changed visit
domains (27 changed arrays and five not produced); the prior z11 joint reading is not revisited,
while the z14 78-pixel support remains pixel-identical. Some guides broaden. No accuracy or
paired-runtime gain is claimed. No new anatomy was accepted: §8.28 remains the latest anatomical
acceptance, and PCL production remains pending.


### Native axial PCL body accepted once demonstrated — 2026-10-18

RELATIVE_POSITION_MAP §8.35 records a competent local native axial PCL body description through
the existing production CLI: proof slice15, 295 pixels, compact and in the posterior notch. This
meets the once-demonstrated criterion, without claiming complete PCL course/volume, a full
three-plane reference, general accuracy or whole-pipeline efficiency. The accepted 70-file source
pin and runner hash, 1,071-test gate, successful profiled/parallel/public runs, actual-DICOM audit,
figures and lead acceptance are retained under
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/pcl-axial-checkpoint/`.
Serial and parallel outputs agree; no prior arrays or observations were changed or removed, and
main receipts are unchanged. Proof/bursa add 68 arrays,3 observations and1 unresolved row;
public adds97 arrays,5 observations and4 unresolved rows.

Lead review judged four additional identifications wrong and three local readings measured-empty,
not absent. The shared source-selection residual is to use resolved joint/bone context and physical
notch relation, rather than largest prior label alone (R5). Keep the competent proof description;
no per-study patches follow. At this historical checkpoint coronal PCL was pending; MAP §8.36
later accepts its proof description and three-plane reference. Other R2 families remain pending.


### Native coronal PCL body and proof three-plane reference accepted — 2026-10-18

RELATIVE_POSITION_MAP §8.36 records the accepted proof coronal PCL body at slice22 (322 pixels),
with sagittal18 and axial15 forming a physical reference at LPS
`[-110.95654820639552, -42.08987813891625, 23.75791539106383]`. The existing reader validates
addressed sagittal/axial sources, uses actual half-slab profiles and common-map candidates, and
measures the local coronal crop using the existing enclosed-body rule, 3 mm opening, whole
four-connected bodies and existing 2 mm contact to both source targets. Full authored extent is
centered on source points within the object; ties, partial scope, empty and outside-slab outcomes
remain separate. No threshold or per-study patch was introduced.

The 70-file source pin has zero live/snapshot mismatches. The full gate passes 1,087 tests; the
recorded serial rerun, parallel and public runs exited 0. Independent checks covered 11 DICOM
frames and 279,615 crop pixels with zero failures. Proof/bursa added 100 arrays and public added
69; no prior arrays were changed or removed, and prior observations/unresolved rows are exact
prefixes. Two proof fibula main records gained PCL guidance anchors/placements, so main-receipt
identity is not claimed. Map adjudication accepts the propagated additions: 40 newly complete PCL
pair vectors, 44 other PCL pairs still partial at their other endpoint, 38 predictions, 20 residuals
and four later retinacular guide uses. Full maps and original raw audit flags remain retained. See
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/pcl-coronal-checkpoint/`.

This completes one competent coronal description and a proof reference only. The four wrong axial
identifications and three axial measured-empty readings in §8.35 remain evidence; bursa COR16/17
are partial/empty and public COR27 is outside-slab while COR29 is measured-empty. R5 still needs
general source eligibility from resolved joint/bone context and physical notch relation. ACL axial/
coronal and tibial axial cartilage remain R2 work.
