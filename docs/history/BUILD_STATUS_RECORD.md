# Build status record: dated paragraphs moved from HOW_TO_BUILD.md, 2026-10-18

At Rohan's request («CLean up the post-compact setup process to focus only on the parts that are relevant
and useful and won't make you fuck up like you have been»), the purely dated status paragraphs of
`docs/HOW_TO_BUILD.md` were moved here unchanged: where the build stood on each date, what was resolved,
counts, run epochs and gates, and each checkpoint's "next". They are history, evidence for a part, never the
current state or the next step; the current state and the next task are `docs/FULL_BUILD_PLAN.md` §13.

The rules, corrections, standing permissions, owed work and limits still in force that sat in the same
sections stayed in HOW_TO_BUILD under their headings. Each block below names the section it came from and
its lines before the move. The unit-by-unit classification, written by the lead after reading the whole
file and checked by a Codex reading, is appended at the end; for each moved paragraph it names where any
principle stated in passing still lives in the files every session loads. Its evidence (the Codex prompts
and answers, the pre-move copy of HOW_TO_BUILD, the move script with its line guards, and the check that
every kept line survived) is in
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/grounding-cleanup-20261018/`. Some of
the moved paragraphs name work still owed at their date; the plan carries the open work in its task
order (§§4–8: the remaining ACL and tibial-cartilage views, the older consumers' scopes, the E02/E24
consumers, marrow), and its §13 records the items carried by name (HOW_TO_BUILD's "Still owed" list and
the sagittal-menisci adapter's ledger declarations).

## From "Where it stands, 2026-10-14" (HOW_TO_BUILD lines 243-317 before the move)

- Resolved on the proof study (commit `1d86cfc`), on the middle slices: air, skin, femur, tibia,
  bone marrow (the inside of each bone named), the joint, the patella, both menisci (sided by the
  header), the articular cartilage, the PCL, the MCL, the joint's fluid (the white in the joint's
  recesses with fat suppressed, laid onto the T1 and the T2), Hoffa's fat pad (the rest of the
  patella's territory below the patella) and the suprapatellar fat (the rest of it above the
  patella: the two fat pads above the patella, named together); the fibula on its main slice (the T2
  sagittal's slice 30); the ACL on its own slice, the middle slice's neighbour on the knee's outer
  side (named on the fat-suppressed sagittal's slice 19 and laid onto the T2's); and the LCL on its
  own slice, the coronal slice through where it attaches on the fibula's head, 8.2 mm behind the
  head's front edge (LaPrade 2003; named on the T1 coronal's slice 21 and laid onto the
  fat-suppressed one). The patella, the menisci, the cartilage, the PCL, the ACL, the MCL, the
  LCL, the joint's fluid, Hoffa's fat pad and the suprapatellar fat are each found on one sequence
  and laid onto the other sequence's slice of the same place. The medial gastrocnemius head (commit
  `6d19567`) is named on the fat-suppressed axial's middle slice, whose lens every run already
  reads: the deepest region behind the femur's inner condyle, on the knee's inner side of the
  notch, the femur and tibia carried onto the axial by place from the sagittal and coronal middle
  slices; over the 58 labelled studies it is named on 12 axial series of 11 studies, and of the
  other axials 46 abstain because the header names no knee. The semimembranosus tendon (commit
  `001d47a`) is named on an axial slice of its own, the top of the tibia: the axial slice nearest
  the femur that holds the tibia's carried places and none of the femur's (slice 11 on the proof).
  Its direct arm ends on the back-inner top of the tibia (LaPrade 2007), and there it is the front
  thick piece of low signal inside and behind the inner condyle's peak, at the tibia's back-inner
  corner; followed back onto the sagittals, that piece lies on the cord just behind the joint
  line's back end. Over the 58 labelled studies it is named on 10 axial series of 10 studies; of
  the other axials 46 abstain because the header names no knee, 16 find no tendon at the back-inner
  corner, 5 no inner condyle and 4 no tibia below the femur. The study's leg (its femur and tibia,
  and the notch) is made once and carried onto both parts' slices. The patellar and quadriceps
  tendons (commit `bd6bf6c`) are named on the T2 middle sagittal, where their band is plain: of
  the slice's thick, uniformly dark bands, which the PCL is read from and which are now made once
  and kept, the one joining the patella (laid on from the fat-suppressed slice) and the tibia,
  split at the patella along the leg; then laid back onto the fat-suppressed slice, the border
  between that slice's regions included, since with fat suppression the thinner band is the
  border its lens draws between two regions. Over the 58 labelled studies each is named only on
  the proof: they wait on the patella reaching the T2, which it does on 7 series (on 31 the two
  slices disagree about it), and on 6 of those the band does not join the patella and the tibia.
  With them the PCL reads the black margin as the margin, not every stored zero: on the proof it
  keeps its piece and gains its zero-light holes, its foot toward the back of the tibia and a thin
  strip of the femur's shell; over the 58 it is now named on 48 T2 sagittals, from 44, in 39
  studies, from 36. The fat under the skin (commit `a3ce594`) is named where fat is not
  suppressed, by its light: the places outside every part named at least three quarters of the
  marrow's light, in the pieces reaching within 2 mm of the skin; on the proof's T1 coronal the two
  bright bands down the knee's sides, stopping at the fascia; and laid onto the fat-suppressed slice
  of the same place, where it is grey, as dark as muscle. For it, air and skin are now laid from
  one sequence onto the other where a slice names none of its own, as on the proof's T1 coronal,
  whose lens draws the air into its territories. Over the 58 labelled studies the fat is named in
  56 (106 series by their own light, 72 laid on), air and skin are laid on 9 series, and every
  other part keeps its counts. Muscle (commits `0b1a328` and `80f255b`) is named where fat is not
  suppressed: the leg's places outside every part named, darker than fat, the bodies of them at
  least a centimetre across, then outside the white its fat-suppressed, fluid-sensitive twin sees
  as fluid, since on T1 fluid, a Baker's cyst among it, is as dark as muscle; and laid onto the
  twin. Over the 58 labelled studies it is named in 50, on 155 series. Every one of them is
  written in the module note as an «<object>» (§4), its descriptions checked against its code.
- What the run puts out (2026-10-15): for any study it is given, labelled or not, a decision on
  each of the 23 parts on every series it reads, named (and how) or abstained (and why): over the
  58 labelled studies, 336 series and none missing a decision; the 3 studies on disk that are
  not labelled are the test split's, the competition's public sample, and `--split test` runs
  them as a kernel would: 15 series, none missing a decision. `--root` is where the competition's
  files are, the kernel's mount (`KAGGLE_ROOT`) when it exists. The bone marrow (named with its
  bone) and the synovium (not named) have no decision of their own in the output.
- Not yet resolved, each with a provisional entry in `docs/RESOLVING_THE_PARTS.md` §6: the
  synovium, the gastrocnemius–semimembranosus bursa (Baker's), the lateral gastrocnemius head, the
  popliteal vessels, the patellar retinacula, the lateral complex beyond the LCL, and the other
  hamstring tendons. Claude had written that the synovium is "not named, because the pictures do not
  hold it"; Rohan, 2026-10-15: «It's literally a form of interstitial fluid. Interstitial. Between the
  tibia and femur. We have the tibia, we have the femur. It's...obviously in there? That's a
  demonstration of your failure to understand the basis of the thesis».
- Next: (1) the dimensional collapse. Rohan, 2026-10-15: «I think that you missed the point of this
  part of the thesis, and we need to get to fixing the implementation in another session»; and, of
  the middle slice the run reads for most parts: «The "middle" is a fine standard first slice to
  select. For other elements that are not obvious in that one slice, etc, that is a fine standard.
  There are five different views (different angles and fat-bright vs fat-dark), and each has
  multiple z-slices. That is where the thing being mined is relevant--discovery of ALL elements of
  the anatomy at their best slices and resolution across the 5 images/3 orientations». The thesis's
  own text on the collapse, and what the run does now, are in `docs/RESOLVING_THE_PARTS.md` §8. (2)
  Define each part not yet resolved once, from its provisional entry. Diagnosis only when he says.

## From "Definition pass, 2026-10-15" (HOW_TO_BUILD lines 470-475 before the move)

The anterior synovial recess and its fat-facing lining surface now have separate masks and decisions
through the real entry point (`docs/RESOLVING_THE_PARTS.md` §9). This supersedes "synovium not named"
in the earlier status record. The lining output localizes the cavity boundary against fat; it does
not report membrane thickness. Its rule uses the existing fluid measurement and anatomical order,
with no new numerical cutoff, and retains both masks without taking pixels away from existing parts.

## From "Definition pass, 2026-10-15" (HOW_TO_BUILD lines 476-481 before the move)

The capsule's dark outer wall at the side recesses is also demonstrated on the proof's coronal
slice, with a separate mask and decision (`RESOLVING_THE_PARTS.md` §9).
The bursa's fluid-filled body is demonstrated on study `…13335129881737731410081002627729200903`,
using the semimembranosus tendon's existing slice and measurements. It has a separate mask and
decision; its neck and wall across slices are not asserted by that mask (§9).

## From "Definition pass, 2026-10-15" (HOW_TO_BUILD lines 486-503 before the move)

The lateral gastrocnemius head is now named on the same fat-suppressed axial middle slice as the
medial head, by the medial head's own definition with the physical inner axis negated: the
bone-holding territory with the deepest peak on the outer side of the notch is the outer condyle,
and the deepest non-bone territory with its peak on that side and behind the condyle's peak is the
head (`docs/RESOLVING_THE_PARTS.md` §9). This element needed no new lens: the carried bones, the
notch, the territories and the ordered peaks are shared by both heads in one pass, there is no new
cutoff, and already named pixels are preserved. Its two side-specific refusals are
`abstain_no_outer_condyle` and `abstain_no_body_behind_the_outer_condyle`; the common
prerequisites keep their common codes. On the proof's axial slice 16 both heads are `identified`:
the bright green fills the belly behind the outer condyle up to the fascia and the midline
territory edge, reaches a little into the fat round the popliteal bundle, and the strip under the
skin along the back stays with the medial head's territory. Over the 58 labelled studies it is
named on 9 axial series of 9 studies (46 other axials abstain because the header names no knee, 8
because fat is not suppressed, 15 find no body behind the outer condyle, 3 no outer condyle).
This supersedes "the lateral gastrocnemius head" in the "Not
yet resolved" list above; the test split's 3 studies keep their earlier records, without this
decision, until `--split test` is run again.

## From "Definition pass, 2026-10-15" (HOW_TO_BUILD lines 519-533 before the move)

The popliteal artery and vein lumens now meet that criterion on the proof's axial slice 16.
Enclosed darkness measures the dark bodies within brighter enclosures; their place between the
two gastrocnemius heads and behind the condyles selects the pair, ordered artery in front of vein.
Both return `identified`, both have saved nonempty masks, and the actual output picture was
inspected (`RESOLVING_THE_PARTS.md` §9). This supersedes the vessels' earlier unresolved status.
The next unresolved element in §6's order is the patellar retinacula.

At Rohan's next pause request, the remaining work was closed at saved preview/proposal checkpoints,
with no further production recognition changes. The retinacula and lateral complex remain
unimplemented; the semitendinosus and separated suprapatellar fat pads have inspected candidate
previews and code proposals, but still need integration and real-pipeline verification. Gracilis
and sartorius remain to be discriminated individually. The exact status, artifact paths and API
closeout are in `docs/ANATOMY_DEFINITION_CHECKPOINT.md`; do not count those previews as completed
objects. The verified code checkpoint remains `c1b8bdb`.

## From "The island check and the colours, 2026-10-16" (HOW_TO_BUILD lines 553-556 before the move)

- The vessel rule no longer gathers every closed lumen's places on the slice only to set aside those
  outside the corridor: one pass finds which lie wholly in it. Over the 58 labelled studies and the
  test split every record (each decision, silence and saved array) is the same as before; only the
  telemetry changed.

## From "the 2026-10-16 definition sections" (HOW_TO_BUILD lines 586-688 before the move)

## Semitendinosus definition, 2026-10-16

The semitendinosus is now resolved (`ee5480b`) on the semimembranosus tendon's own axial slice:
the separate whole dark body behind that tendon, inside the inner condyle's peak, nearest the
tendon among the bodies satisfying those relations. Both selectors receive the same dark-body
labels and mean physical positions, computed once, with no fallback and no second lens or
slice search. Its separate mask and named decision are saved and drawn SILVER beside the BROWN
semimembranosus. The proof's actual output was inspected at its own pixels; all earlier proof
decisions and arrays are unchanged. The full gate passed with 211 tests. Details and limitations:
`docs/RESOLVING_THE_PARTS.md` §9; picture:
`data/pictures/definitions-20261016/semitendinosus-proof.png`. This supersedes semitendinosus's
preview-only status above. Continue at step 2 of `docs/ANATOMY_DEFINITION_CHECKPOINT.md`.

## Separate suprapatellar fat pads, 2026-10-16

The quadriceps and prefemoral fat pads are now resolved (`096f667`): in the already named
suprapatellar-fat field, the opposed light of the two physically matched sagittal acquisitions
locates their internal seam; fat in front is the quadriceps pad, behind is the prefemoral pad.
The rule adds no numerical cutoff, keeps ambiguous sections unresolved and does not smooth
between them. The native masks and seam are laid onto the twin by the existing match; the
aligned light and ratio are kept too. Both production pictures and their enlarged view were
inspected. Earlier proof decisions and arrays are unchanged; the full gate passed with 216 tests.
Limits and picture: `docs/RESOLVING_THE_PARTS.md` §9,
`data/pictures/definitions-20261016/suprapatellar-pads-proof.png`. This supersedes the earlier
preview-only status. Continue at step 3 of `docs/ANATOMY_DEFINITION_CHECKPOINT.md`.

## Patellar retinacula, 2026-10-16

Both are now resolved in `be52965`: the dark outer bands beside the two bright patellar recesses,
on the one axial slice selected by the native named patella's physical centre. Both walls share
the lens, carried bone targets and measurements. The rule combines anatomical order, the existing
fluid reading and contact allowance, and exact acquired-signal minima outside each recess;
separated tied minima abstain locally. There is no new signal cutoff or proof coordinate.
The real proof run identifies both, with separate masks and decisions; the actual enlarged output
was inspected and shown (`data/pictures/definitions-20261016/retinacula-proof.png`). Earlier proof
outputs are unchanged. The gate passed with 229 tests; Vulture still lists 13 advisory contract
declarations and fields. The masks locate the bands, not thickness or full course. Details:
`docs/RESOLVING_THE_PARTS.md` §9. Continue at step 4 of the checkpoint: the lateral complex.

## Popliteus tendon, 2026-10-16

The popliteus is separately resolved in `8fa091d`: the largest part of the existing LCL region
occupying the femur's lateral contour concavity, measured by its convex envelope. It reuses the
LCL's selected non-FS coronal slice, lens and carried femur; the target is retained. Its independent
mask is laid onto the FS twin through the shared match without altering earlier labels.
The real proof run and both output pictures were inspected, including the enlarged SAGE mask in
`data/pictures/definitions-20261016/popliteus-proof.png`. The full gate passed with 246 tests;
Vulture's 13 advisory contract declarations and fields remain. The localization can retain a
cortex rim and leaves the outer portion; full course and precision are deferred. Details and the
recorded independent Fable reading: `docs/RESOLVING_THE_PARTS.md` §9. Next in step 4: biceps femoris,
then iliotibial band; step 5 is still gracilis and sartorius.

## Last four anatomical definitions, 2026-10-16

In `4a126fc`, biceps femoris, iliotibial band, gracilis and sartorius now each have an independent
mask and named decision through the real entry point. This completes the outstanding anatomical list in
`ANATOMY_DEFINITION_CHECKPOINT.md`, at Rohan's criterion of a justified rule and a measurable,
competent demonstration once. It supersedes the earlier remaining-object lists, not the recorded
limitations. Full course, exact boundaries, generalization and diagnosis are not claimed.

- ITB: the acquired-signal dip directly deep to lateral subcutaneous fat, passing femur and
  reaching proximal tibia; existing middle non-FS coronal, carried onto the FS twin.
- Biceps femoris: the substantial dark body below the posterior thigh muscle toward the fibular
  head, using a lateral peripheral sagittal selected from the named head and its marrow support;
  both acquisitions distinguish tendon from muscle and fat.
- Gracilis: the separate thin dark body medial to the two already named posteromedial tendons,
  anterior to semitendinosus; a native-pixel body lens on their existing axial slice.
- Sartorius: the largest nearby grey muscle body medial and anterior to the projected gracilis
  location target, on the existing middle FS axial. The new local-lightness lens measures seen
  samples against their seen surround; its explicit visual baseline constants were not searched
  or tuned. The projection is a location reference, not a tendon boundary on that other slice.

The source definitions, constants, named refusals, actual observations and limits are recorded
in `RESOLVING_THE_PARTS.md` §9. All four actual output pictures were inspected at native pixels.
The semimembranosus group now runs once before middle-slice persistence, so gracilis is available
to sartorius; every prior group record and upstream silence remains, and the middle save point
is intact. Cheap prerequisites avoid a local-contrast reading on inappropriate views.

The full gate passed with 357 tests, with the production import contract kept and no type or
dependency findings. Vulture lists 12 advisory contract declarations/fields; it is not claimed
clean. The ledger still reports retained readings with no later consumer: the squint's pending
collapse readings, vessel components, and sartorius source points/window/separation/body statuses;
without drawing it also lists masks used only by development pictures. Saving is not a read.

Independent checks caught and fixed the API worker's initial median filter: excluded samples
could influence neighbouring ratios before masking. Two adversarial checks now pin that excluded
stored values cannot change any contrast reading and nonfinite samples have no light or ratio.
The anatomical selector and its constants were unchanged; the final proof mask is 188 pixels.

Nine Sonnet prototype/implementation workers completed at a recorded total of $17.4480384;
separate Fable readings returned token usage without monetary amounts. Payloads were authorized
by Rohan, credentials were not exported in packets, and all prompts/results/usage remain in
`data/readings/definitions-20261016/`. Worker claims were checked by the lead against source,
the real run and its actual pictures. Next: the dimensional collapse in §8, with Rohan's full
object thesis; the definition pass is no longer waiting on another anatomical element.

The labelled and test splits have been refreshed with that code. The comparison against the
saved pre-change receipts preserves all 351 previous middle-slice records and 48 previous
main-slice records, including earlier decisions, silences and array digests, with only the four
additions and optional border readings set aside. The final canonical proof drawn afterwards
also preserves the previous borders. Its arrays and decisions exactly match the inspected final
alternate run. Evidence: `data/readings/definitions-20261016/remaining-production/`.

## From "The relative position map, 2026-10-17" (HOW_TO_BUILD lines 713-778 before the move)

### Connected production checkpoint, later 2026-10-17

The relative map's current implementation and measured limits are `RELATIVE_POSITION_MAP.md` §8.11,
which supersedes the withdrawn-code description above. The real entry point now consumes the map in
patella, joint, recess and fibula search. The unused single-reference calculation and test-only helpers
were retired. The final gate passed 723 tests; all 58 labelled studies and 336 series completed. The
output keeps specific already-recorded refusals instead of generic placeholders where possible. The
cohort's three-plane coverage remains limited to femur, tibia and patella; other objects' missing
orientations remain the next build work, with no new perfection/generalization requirement. Read the
source-pinned artifacts at that checkpoint before restating any count as current.

The next completed collapse step is the fibula's missing axial key plane (`RELATIVE_POSITION_MAP.md`
§8.12). Its existing sagittal and coronal sections point to axial slabs; the axial image's shared coarse
bone enclosure supplies the independent plane. The main-record observation update now merges those
readings before its single save. The actual proof has sagittal 30, coronal 22 and axial 1 jointly
constructing its fibula position, with the three-plane picture inspected. The final gate passes 745 tests;
no new anatomical definition or cutoff was added. Continue with the remaining objects' missing key
orientations, not a perfection pass over the fibula. The full evidence and measured limits are at §8.12.

The next completed bridge, axial joint fluid, is recorded in `RELATIVE_POSITION_MAP.md` §8.13.
It exposes the retinacular rule's already measured side pockets on both existing native paths,
with exact saved boolean supports, distinct refusal reasons and an immediate map handoff to later
searches. No new image lens or cutoff is added. The actual axial and three-plane figures were
inspected; the fluid's plane intersection is a localization reference inside the femur, never a fluid
voxel or a boundary. The native pockets remain the anatomical evidence. The requested full plan,
reviewed through the direct Fable API before building, is `FULL_BUILD_PLAN.md`; its family order
and later encoding/AI/competition dependencies are explicit. Small Codex subagents are now the
preferred workers, with the lead retaining meaning, integration and visual acceptance. Read §8.13
and its source-matched evidence for this checkpoint rather than reusing the older counts above.

The following bounded bridge is the capsule's native axial outer-wall description
(`RELATIVE_POSITION_MAP.md` §8.14). Existing retinacular wall masks beside the recess are shared,
with their full source addresses and original observations preserved; no new image reading is
needed. Both pointed and original main-slice paths reach the shared map and grouped object output.
The proof has coronal and axial capsule planes and still lacks sagittal. The source-matched
proof/bursa comparison preserves all 1,946 earlier arrays and decision/observation prefixes.
The remaining joint-family views are still work; a development preview is not a production result.

The axial lining companion is now connected (`RELATIVE_POSITION_MAP.md` §8.15): retain the
cavity-side fluid edge already measured in the retinacular wall loop, independently of the wall
mask and count, and expose it through both native paths. Earlier fluid/wall/capsule outputs remain.
This is an object description in the deterministic ground layer, as Rohan reaffirmed, before
later AI representational work; it is not a thickness or full-course precision requirement.
Missing support and measured-empty support stay distinct, and every pointed picture uses the
actual addressed source frame rather than its owner artifact's middle image.

The coronal lining companion is connected at `RELATIVE_POSITION_MAP.md` §8.16. Reuse the
existing selected side recess and outer wall, retain the fluid-side edge where every wall pixel
on that native section lies farther outboard, and preserve named unresolved sections. Both real
coronal callers consume the same returned context, with separate support/counts for lining and
no new image lens or slice search. The shared helper is now `cavity_lining_observations`.
The proof selects sagittal 18/coronal15/axial21; their intersection is a localization reference
inside the femur, not a lining pixel. Actual surface masks remain the evidence. The production
figures were inspected, all 1,950 earlier arrays are unchanged, public test outputs match exactly,
and the stable gate passes 785 tests. Remaining Packet A: joint axial, anterior recess
coronal/axial, capsule sagittal. Canonical outputs and the 58-study snapshot are unchanged.

The axial anterior-recess description is connected at `RELATIVE_POSITION_MAP.md` §8.17.
It reuses the exact native fluid-pocket support on both production paths, with no new image pass.
The shared output now always retains original definition decisions and own-slice refusals alongside
new observations; adding evidence must not obscure earlier categorical information. Final real
proof/bursa and public runs preserve every earlier saved array; the full gate passes 791 tests.
Remaining Packet A: anterior recess coronal, joint axial, capsule sagittal. The complete production
execution order and shared-value/tool contracts are `THREE_VIEW_PRODUCTION_EXECUTION.md`.

## From "The relative position map, 2026-10-17, and the dated sections after it" (HOW_TO_BUILD lines 784-958 before the move)

### Sagittal capsule, 2026-10-17

RELATIVE_POSITION_MAP §8.19 records the native sagittal capsule outer-band description. Coronal wall points locate the question; native white-body selection and an acquired-signal minimum darker than adjacent fluid supply the independent anterior wall, with no new cutoff. Both actual sagittal outputs and the selected three-plane figure were inspected. Capsule 32/15/21 now jointly constrain its reference; the proof has 8 complete references / 56 complete ordered pairs. All earlier arrays and categorical information remain; the full gate passes 862 tests. The public split adds named source/sequence refusals, no native capsule claim. Packet A2 joint axial is being built; the rest of THREE_VIEW_PRODUCTION_EXECUTION remains.


### Axial joint and typed anatomical links, 2026-10-17

RELATIVE_POSITION_MAP §8.20 completes Packet A2 through the single CLI. Sagittal/coronal joint locations meet a native axial fluid body; joint 18/15/14 establishes the ninth proof reference. Actual source/support pictures were inspected, prior arrays and categorical prefixes are preserved, and parallel/profile outputs agree. The gate passes 887 tests; advisory Vulture findings remain. Object descriptions now include typed anatomical definition links, explicitly separate from measured evidence. The Packet A 58-study refresh completed (58 studies; source-pinned reports at §8.20); B–F remain, with only the typed-link portion of F connected. Continue the execution plan, not a perfection pass over the joint.


### Native axial extensor descriptions, 2026-10-17

RELATIVE_POSITION_MAP §8.21 records the accepted axial patellar/quadriceps descriptions. Physical sagittal source locations and map guidance point; native enclosed darkness and the existing 2 mm body operation supply the tissue support. Both selectors share same-slice measurements, retain exact boolean row addresses, and enter the existing family map/output path. The actual proof axial13/30 bodies were inspected and shown. All earlier proof/bursa/public evidence remains; the full gate passes 895 tests. Coronal tendon views and the remaining B–F work are still required. No new threshold, separate pipeline or perfection criterion was introduced.


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

### One final middle-artifact write, 2026-10-17

The middle records now stay live until all existing families finish, then each artifact is saved once.
This lets later native descriptions reuse original main-slice results without repeating their searches
or rewriting middle arrays. Existing main-artifact save points are unchanged. The actual CLI's profiled
and ordinary two-worker proof/bursa outputs exactly match accepted B2: all records, observations,
arrays, digests, physical maps, grouped objects, refusals and telemetry. The public split also matches
exactly; every persisted array digest was recomputed. Evidence is
`data/readings/collapse-20261017/full-build/final-persistence-bridge/`. The whole gate at its first
source checkpoint passed 920 tests; it is not a claim about subsequent edits. No speed claim is made.

At the final-persistence checkpoint, retinacular sagittal/coronal and fat-pad bridges were in flight;
the records below supersede that status for retinacula. Fat-pad production and native-sampler
connection remain unaccepted; standalone tests and development figures are not production acceptance.

### Retinacular planes and sagittal cartilage companions, 2026-10-17

The retinacula now have selected native planes in all three orientations on the proof: medial
12/5/22 and lateral 32/12/21 (sagittal/coronal/axial), with addressed supports of 73/58/70 and
159/82/71 pixels. The medial sagittal guided candidate at slice5 remains recorded with 11 wall pixels; the stronger
source-profile candidate at sagittal slice12 was checked and becomes the selected plane with 73
wall pixels. Medial coronal slice5 remains selected with 58 pixels. A source-profile maximum is a
location reading until its native result is checked; it is not itself the key-plane decision.
The supports describe local sections, not thickness or full course, and the lateral sagittal
support retains its recorded adjacent capsule/course overreach.

Six sagittal cartilage observations were appended from three already saved `a3_joint_plane_reading`
rows: slices15,17,22 with femoral/tibial counts 215/259, 307/297 and 236/250. No image pass or
array change was involved; previous candidate observations remain as an exact prefix. The tibial
overreach remains visible in the record. Neither addition creates a precision criterion or
changes the single three-dimensional map contract.

The source-frozen audit confirms all prior proof/bursa outputs and public outputs are preserved;
the first and ordinary parallel runs match, and the complete gate for that checkpoint passes 952
tests. See `RELATIVE_POSITION_MAP.md` §§8.23–8.24 and the audit at
`data/readings/collapse-20261017/full-build/retinacula-cartilage-checkpoint/`. Later live fat-pad
work is not covered by that snapshot. The Fable API consultation for this increment is complete
and adjudicated by the lead; its answer and comparison are retained in
`data/readings/collapse-20261017/full-build/fable-native-geometry/`.

## Native fat-pad descriptions, 2026-10-17

RELATIVE_POSITION_MAP §8.25 records the accepted native coronal and axial fat-pad descriptions.
Map locations and source points guide candidate questions; the native image supplies support.
Hoffa, quadriceps and prefemoral supports remain separate, and the suprapatellar support is their
same-slice quadriceps/prefemoral union. It is resolved only when both component supports are usable.
The non-fat-suppressed comparison uses each series' own marrow calibration at candidate coordinates
sampled on its actual planes, with its actual dimensions, thickness, bounds and margin. Its
positive, negative, disagreement and unknown classes remain separate. Same-series white fluid is
excluded only above its existing fluid level. A new shared physical-gradient measurement supplies
the Q/P native candidate basins from valid neighbors at actual pixel spacing through SciPy's
image-filtered-gradient/IFT operation and linear uint16 quantization; this adds a measurement lens,
not an anatomical cutoff, and leaves earlier proof lenses unchanged. Hoffa uses the unique largest
original native territory touched by its selected physical source. The coarse femoral core is a
competing marker and exclusion where measured, not an exact boundary; the two-millimetre operation
is coarse-block context, not fat-body opening. H/Q/P sources are selected identified sagittal-FS
sections by physical area and converted to LPS once; the composite Q/P source is not a fourth seed.

On the proof, the four selected references are Hoffa18/8/16, quadriceps18/6/27,
prefemoral18/8/29 and suprapatellar fat18/8/27 (sagittal/coronal/axial). The lead inspected the
actual addressed frames and supports. Visible limits remain in the record: broad/patchy Hoffa
sections, a posterior Hoffa candidate that is marrow, neighboring tissue in quadriceps coronal6,
limited coronal8 quadriceps/prefemoral sections, small compatible quadriceps/prefemoral portions
on axial27 and a prefemoral strip on axial29. These are local descriptions, not full courses or
exact boundaries; no further per-study corrections are being made.

The source-pinned proof/bursa serial and parallel runs match, prior records and array digests are
preserved, public prior outputs are preserved, and the completed gate passes 963 tests. Exact
counts, addresses, source hashes and figures are in
`data/readings/collapse-20261017/full-build/native-fat-pads-checkpoint/`.

Packet B’s source-pinned cohort now completes: 58 maps, 336 interiors records, 43 main records, and 0 unread study inputs. Across the 2,494 study/object map entries there are 116 complete and 2,378 partial entries; these are coverage counts, not accuracy claims. The pair report contains 1,806 ordered pairs. For each reported metric, 1,534 pairs have n=0, 252 have n=1 and 20 have n≥2; sample SD is null below n=2. The declared `construction_consistent` field has zero inconsistencies, which is a position-construction check, not anatomical proof. All 80 native fat boolean support addresses validate against saved rows, slices, counts and actual frames. The corrected cohort audit counts native rows from both receipts, separates readings from resolved supports and cross-checks 5,879 native rows against the production combined object summary. At the Packet B audit, all 56 source hashes matched its source snapshot and live tree. Receipts are under `data/readings/collapse-20261017/full-build/packet-b-cohort/interiors/` and `data/readings/collapse-20261017/full-build/packet-b-cohort/main/`; pair report files `cohort-pair-variation.json` and `cohort-pair-variation.csv`, the source pin, detailed audit and summary are under `data/readings/collapse-20261017/full-build/native-fat-pads-checkpoint/`. This is Packet B’s source epoch. Packet C remains under construction; its live edits are outside this snapshot, and no C axial production result is accepted here.

## Native axial femoral-cartilage description, 2026-10-18

The accepted proof increment adds one native axial femoral-cartilage reading at slice14, with a
994-pixel boolean support at row0 of `a4_axial_femoral_cartilage_support`. The reader reuses the
existing femoral enclosure, marrow calibration, cartilage reach and sagittal/coronal source
locations. The lead inspected and accepted the local description with adjacent cortex/tissue
overreach retained. Prior observation/refusal prefixes and main arrays remain; six proof
retinacular profile arrays changed with refreshed map guidance. The public run preserved old
prefixes/maps and added four source-context arrays plus four named unresolved rows, with no
resolved public cartilage row.

The first attempt's wrong collector key produced no resolved native row; its run and source pin are
preserved as failed history. The corrected 58-file source-fixed audit has no snapshot/live
mismatches; later formatting-only normalization was AST-equivalent. The complete gate passes 982
tests; Ruff, formatting/import/dependency checks and source/test typing pass, while Vulture
advisories remain. Audit and run records are in
`data/readings/collapse-20261017/full-build/axial-femoral-cartilage-checkpoint/`. This proof result
does not refresh Packet B's older cohort counts. Axial tibial cartilage, sided menisci, ACL and PCL
remain pending. Development-only native-body previews are not production results. The current
human steering and efficiency-first record is indexed at
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/`; the Fable consultation is
complete and its recommendations remain advisory, not an accepted optimization. Follow
`docs/TARGETED_ANATOMICAL_COMPUTE.md` for the authoritative useful-priors criterion.


## Native sagittal menisci, 2026-10-18

RELATIVE_POSITION_MAP §8.27 records the accepted local sagittal companion. Native coronal wedges
and map/source profiles point to useful crops; original enclosed darkness, the existing 2 mm body
operation and whole-component source contact resolve the native sagittal tissue. The bound uses a
full anatomical extent around an in-object source point, never assumes that point is the object
centre. The lead inspected medial5 (588 pixels), lateral28 (200, anterior horn) and lateral29
(553, connected body) on actual addressed DICOM frames. Both objects still lack their axial plane.
All 3,005 earlier arrays and categorical prefixes remain; source-frozen serial/parallel receipts
and maps match, public prior outputs remain, and the full gate passes 997 tests with Vulture
advisories retained. Three crop readings visit 55,212 pixels total, each 16.939–20.039% of its frame;
no whole-pipeline speedup is asserted. Producer/consumer ledger declarations in the new adapter
still need correction during the next family edit, as its compute audit explicitly records.
Evidence is under `full-build/targeted-compute-20261018/meniscus-local-checkpoint/` in the readings
tree. Continue axial menisci and the remaining coherent roadmap; do not perfect these local borders.


## Native axial menisci, 2026-10-18

RELATIVE_POSITION_MAP §8.28 records both native axial meniscus descriptions. Independent coronal
and sagittal locations guide useful crops; original local enclosure, existing 2 mm bodies and
whole-component contact with both sources supply axial12 supports of 1403 / 1437 pixels.
Window completeness remains a separate retained reading; unavailable background elsewhere does
not withdraw an identified component. The lead inspected actual axial and three-plane images.
The proof's selected medial [5, 15, 12] and lateral [29, 15, 12] planes now construct complete
references. Five distinct heavy windows total 159,242 pixels; no runtime speedup is claimed.
Serial/parallel outputs/maps agree and the full gate passes 1,013 tests, with Vulture advisories.
Its one fixture typing finding is corrected in a separately pinned verification-only change;
source/test typing and 25 focused tests pass afterward, with production source unchanged.

The new anatomical guide skips a prior weak medial retinaculum sagittal5 proposal; selected
sagittal12/73px and key planes remain identical. The generic prefix audit's failure is retained
and adjudicated explicitly, not called exact preservation. Earlier definition decisions, main
arrays and public prior outputs remain. The three source epochs, final evidence and limits are
under `targeted-compute-20261018/axial-menisci-local-checkpoint-final/` in the readings tree.
Next remains tibial axial cartilage and cruciates. The new cartilage/PCL packets are development
evidence until their own native outputs are accepted through the same CLI.

## Bounded bone execution, 2026-10-18

RELATIVE_POSITION_MAP §8.31 accepts the original bone lens running inside existing shared profile
windows before heavy measurement. Full local readings, scope, offsets and unknown places are
retained. All20 actual DICOM crops were independently verified; one bursa-study femoral section
gains34 pixels, with its inherited broad boundary limitation recorded. Common maps and main outputs
remain identical, serial/parallel agree, and the corrected gate passes1019 tests. This is a first
bounded family retrofit, not whole-pipeline efficiency closure. Later full-frame consumers remain;
the structural source trace identifies `patella_plane` as the first map-aware fine reader whose
in-plane guide currently acts only after its full-frame lens. The next work must move useful
structural guidance before that computation, while preserving the existing anatomical definitions.

## From "Supporting-kernel equivalence, 2026-10-18" (HOW_TO_BUILD lines 961-975 before the move)

The batched `physical_squint` implementation is accepted as an equivalent supporting change.
Complete tiles are batched; partial, ragged and fallback inputs retain the original per-tile
semantics and native-dtype outputs. The real production caller remains the existing squint stack.
This kernel supports the coherent build but does not resolve an anatomical object or complete the
information flow required across objects.

The accepted frozen source snapshot has 67 files and no snapshot/live hash mismatches at that
acceptance point. Its complete gate passes 1,026 tests. The labeled cohort run selected all 58
available labeled studies. Baseline and batch receipts, maps and object entries compare equal; all
112,104 saved-array digests across both epochs match. No speedup is claimed. The source snapshot,
acceptance record, comparison report and full run logs are under
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/squint-batch-checkpoint/`.
This is a pinned source epoch. If live code advances, verify a fresh source pin before describing
it as the same 67-file snapshot.

## From "the patella-scope and common-map sections" (HOW_TO_BUILD lines 983-1031 before the move)

## Historical scoped patella execution, 2026-10-18

RELATIVE_POSITION_MAP §8.33 records the existing patella-plane lens using the shared femur/tibia
profile window before its expensive local measurement. This changes execution scope only; the
existing patella definition and its resolved native support masks are unchanged. Of four local
attempts, the slice21 reading identifies the same 2,676-pixel support, while slices1, 5 and27 miss
locally and proceed to the retained broader reads. Those misses are not object absence.

The source-frozen packet has 68 files, zero live/snapshot hash mismatches and a gate of 1,036 tests.
The lead inspected all 12 figures and independently verified the four DICOM crops and their
geometry/availability across 1,717,665 pixels. Proof/bursa interiors add 88 arrays, change 5 and
remove 0; prior observations, maps and main outputs are unchanged, and serial/parallel outputs
agree. Public interiors add 132 arrays and change 2 with none removed; its observations, maps and
main outputs are unchanged. Three local misses add work before broadening; the windows are broad
and retain inherited tibial context. No whole-pipeline speed or accuracy claim follows. The
complete source pin and audit are under
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/patella-scope-checkpoint/`.

The static [every-object matrix](../data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/every-object-structural-chain/README.md) covers 43 emitted concepts and distinguishes actual selector inputs
from catalog relations; it is not a declaration that all anatomy is complete. Marrow remains
interior to bone and is explicitly tracked under R5. At the time of this patella checkpoint, the
immediate map handoff was still an artifact candidate; it has since been accepted as execution
behavior at MAP §8.34. E02 remains partial, and other E24 semantic consumers remain pending. The
rebased PCL API candidate uses the existing authored atlas extent, but no PCL production assignment
is accepted until its actual native outputs are audited. Keep the handoff scoped to this execution
change; do not make a general efficiency or accuracy claim.


## Shared common-map handoff, 2026-10-18

MAP §8.34 records the accepted execution update. Fifteen completed native families convert their rows once, offer them immediately to the
existing common map before later dependent guide requests, and reuse the converted rows at the
final idempotent closure. Existing
filters and duplicate handling remain, as does original observation append/save order. This is not
a new anatomy definition. Some guide domains broaden. The proof/bursa comparison records 27 changed
arrays and five not produced in the new run; the prior axial-joint z11 empty reading is not
revisited, while the z14 78-pixel support is pixel-identical. No blanket prefix/equivalence claim,
paired runtime gain or accuracy gain is made.

The source-frozen epoch pins 69 files (manifest SHA-256
`8165914de13f19a697ef96e15d13d8b9067db7b021b58cb7db4ebc9005a2c798`; runner SHA-256
`0bd86d213c7c92d5d2d125907396d2eef6a9175729b197eb0f9b6b4c1e9ce4ec`) and passes 1,038 gate
tests. Runtime trace, source snapshot, runs and receipt audit are retained under
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/immediate-map-handoff-production/`; acceptance and independent checks are under
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/immediate-map-handoff-checkpoint/`. At this execution checkpoint §8.28 remains the latest accepted anatomy. Other E24
semantic consumers and E02 remain partial; the 43-concept matrix is static and marrow R5 is
pending. §8.35 below records the later accepted axial PCL demonstration.

## From "Native axial PCL body, 2026-10-18" (HOW_TO_BUILD lines 1034-1040 before the move)

MAP §8.35 records the accepted native axial PCL body description through the existing production
path. The lead judged proof slice15 (295 pixels, series
`1.2.826.0.1.3680043.8.498.67495435033389756963800730529101229430`) a competent compact
posterior-notch body demonstration. This meets the agreed once-demonstrated criterion. It does not
establish a complete PCL course, volume, three-plane reference, general accuracy or whole-pipeline
efficiency.

## From "Native axial PCL body, 2026-10-18" (HOW_TO_BUILD lines 1051-1058 before the move)

The accepted 70-file source pin, runner hash, 1,071-test gate, serial/parallel/public runs and
independent DICOM/image checks are recorded in
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/pcl-axial-checkpoint/`.
The raw digest flags remain preserved; a separate adjudication recomputed all 162 and found zero
project-digest failures. PCL coronal, ACL axial/coronal, tibial axial cartilage and other roadmap
families remain pending. The current PCL evidence is local axial evidence only.

## From "Native coronal PCL body, 2026-10-18" (HOW_TO_BUILD lines 1061-1067 before the move)

MAP §8.36 records the accepted native coronal PCL body and the proof study's first accepted
three-plane PCL reference. The lead inspected the actual candidate and selected-plane figures, and
independently checked the DICOM frames and map propagation. Proof coronal slice22 has a 322-pixel
compact dark body in the posterior notch. Together with sagittal18 and axial15, its physical
intersection is LPS `[-110.95654820639552, -42.08987813891625, 23.75791539106383]`. This is one
competent proof description and reference, not a complete course/volume or whole-build claim.

## From "Native coronal PCL body and the complete remaining-work handoff, 2026-10-18" (HOW_TO_BUILD lines 1083-1106 before the move)

The accepted source, run comparisons, 11-frame/279,615-pixel independent check, five candidate
figures and the selected three-plane figure, proof plane check, map adjudication and 1,087-test gate are retained in
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/pcl-coronal-checkpoint/`.
The 70-file pin has no live/snapshot mismatches. Proof/bursa add 100 arrays and public adds 69; no
prior arrays are changed or removed. Prior observations and unresolved rows are exact prefixes.
Two proof fibula main records gain PCL guidance anchors/placements, so main-receipt identity is not
claimed. The map gains 40 complete PCL pair vectors, with 44 other pairs still partial at their
other endpoint, 38 predictions, 20 residuals and four later retinacular guide uses. This accepted
propagation is not a general accuracy, speed or whole-pipeline efficiency result. ACL axial/coronal,
tibial axial cartilage and the remaining roadmap families are still ahead.


## Complete remaining-work handoff, 2026-10-18

Rohan requested a full plan from the supplied build audit. `docs/FULL_BUILD_PLAN.md` now holds
the complete P0–P13 dependency order; NEXT_SESSION_PROMPT is its short entry card. Shared early
domains and later native bone context precede further dependent readers; the current scoped
sartorius candidate remains unintegrated. This documentation handoff adds no anatomical acceptance
or production change. Preserve the accepted MAP §8.36 source epoch and every original reading.
The plan distinguishes useful scope changes from equivalent kernel/refactor changes, observation
metadata consumers from support-pixel consumers, and completed recognition from the later
human-specified representation/AI/diagnostic dependencies. Earlier dated plans remain history.

## The classification

# HOW_TO_BUILD.md, unit by unit: what each paragraph governs (the lead's reading, 2026-10-18)

Written by the lead (Claude) after reading `docs/HOW_TO_BUILD.md` whole (1,161 lines), at Rohan's
correction of the first cleanup («Pause. You're fucking this up» and «No, you can continue with the
cleanup. I wanted you to pause to do thus closer reading»). The first cleanup sorted sections by a
heading keep-list and moved everything else to a history file headed "not the current state"; it is
retired. This table replaces it.

Classes:
- **R**: a rule, correction, definition, standing permission, owed work or limit still in force. Stays.
- **S**: purely dated status (counts, run epochs, "accepted at", a checkpoint's "next"). Moves verbatim
  to `docs/history/BUILD_STATUS_RECORD.md`.
- **U**: unclear. Stays.

A unit marked S may contain a principle stated in passing; the column "operative content lives in"
names where that principle is already in a file `CLAUDE.md` loads, so nothing operative leaves the
loaded set. Line numbers are of the file as read (before the edits described at the end).

| unit | lines | content | class | operative content lives in / reason |
|---|---|---|---|---|
| U01 | 1–15 | title, his 10-14 request, reading instruction | R | stays; reading instruction gains a pointer to FULL_BUILD_PLAN §0 (list kept) |
| U02 | 17–34 | §1 Listen | R | stays |
| U03 | 35–47 | §2 bullets: look with the conversation in mind; never from a summary; archives | R | stays |
| U04 | 48–65 | §2 after-compaction steps 1–5 | R | stays as a short pointer to FULL_BUILD_PLAN §0, which carries steps 1–4 whole; step 5's still-valid sentences stay here; its stale pointer (ANATOMY_DEFINITION_CHECKPOINT "plan", "Where it stands" as the record) is replaced by §4/§13 of the plan |
| U05 | 67–95 | §3 keep it simple | R | stays |
| U06 | 97–151 | §4 naming the parts | R | stays; step 3 "show him before the next object" gains "(P4–P6: at the end of each family wave, FULL_BUILD_PLAN §7)" |
| U07 | 153–205 | §5 one coherent operation | R | stays; last bullet gains: an equivalent speed-up keeps the same answers; a deliberate scope change is judged by its native output (§4 last bullet; plan §1) |
| U08 | 207–212 | §6 report what is true | R | stays |
| U09 | 214–238 | §7 the loop that works | R | stays; step 5 "show him the picture" gains the same family-wave qualification |
| U10 | 240–242 | "Where it stands" heading and intro | U | stays (with a note that its status bullets moved and where) |
| U11 | 243–294 | resolved on the proof by 2026-10-15, counts over 58 studies | S | definitions: RESOLVING_THE_PARTS and the module note of `assignments.py` (the bullet says so) |
| U12 | 295–301 | what the run put out, 2026-10-15 | S | `--root`, `--split test`: AGENTS "Running and testing" |
| U13 | 302–308 | not yet resolved, 2026-10-15 | S | all since resolved (definition pass); his synovium words: §4 and the 10-14 table |
| U14 | 309–317 | "Next: (1) the dimensional collapse" | S | his middle-slice/collapse words: AGENTS step 1 (whole quote) and the 10-14 table |
| U15 | 318–347 | "Still owed" | R | stays verbatim: owed work whose status is not re-checked; a note marks the two items shown done (fat pads parted `096f667`; border readings settled 2026-10-16) |
| U16 | 348–379 | over-reaches stated in the module note, not chased | R | stays: limits in force and the principle "not chased" |
| U17 | 380 | "Nothing is pushed; ask before pushing." | R | stays |
| U18 | 382–461 | the record of 2026-10-14 and its side notes | R | stays |
| U19 | 463–468 | his order: definitions first, then the collapse; robustness for the later AI | R | stays |
| U20 | 470–474 | anterior recess and lining demonstrated | S | limits: RESOLVING §9, plan F19 |
| U21 | 476–480 | capsule and bursa demonstrated | S | limits: RESOLVING §9, plan F25 |
| U22 | 482–484 | «Remember also, we can add lenses as needed» | R | stays |
| U23 | 486–502 | lateral gastrocnemius head resolved | S | definition: RESOLVING §9 |
| U24 | 504–509 | his authorization of the Anthropic API worker, «Do use that Anthropic API connection…» | U | stays (a standing permission whose scope "for this work" is not settled) |
| U25 | 511–517 | his vessel stopping criterion | R | stays |
| U26 | 519–524 | vessels resolved; "next … retinacula" | S | definition: RESOLVING §9 |
| U27 | 526–532 | the pause closeout of 2026-10-15 | S | stale; all named parts resolved 2026-10-16 |
| U28 | 534–538 | island check heading and his words | R | stays |
| U29 | 540–552 | saving is not reading; declare reads where they happen | R | stays whole (its status examples with it) |
| U30 | 553–556 | the vessel rule's one pass | S | status only |
| U31 | 557–571 | one colour table, its test, colours checked on the pictures | R | stays whole |
| U32 | 572–584 | drawing only with `--draw`, his words | R | stays whole |
| U33 | 586–597 | semitendinosus resolved; "continue at step 2" | S | definition: RESOLVING §9 |
| U34 | 599–610 | quadriceps/prefemoral pads resolved | S | definition: RESOLVING §9 |
| U35 | 612–623 | retinacula resolved | S | definition: RESOLVING §9 |
| U36 | 625–636 | popliteus resolved | S | definition: RESOLVING §9 |
| U37 | 638–687 | last four definitions; gate; worker costs; refresh | S | definitions: RESOLVING §9; excluded samples never change a reading: plan M01; saving is not a read: U29 |
| U38 | 689–706 | the one-3D-map construction contract (three key planes, no centroid, no map per sequence) | R | stays whole; its tail on `relative.py` gains the plan §3 item 8 clarification (the module still supplies production `IdealVector`) |
| U39 | 708–710 | the 2026-10-17 correction table | R | stays |
| U40 | 713–722 | connected production checkpoint | S | counts are an epoch's (plan §2: recompute state) |
| U41 | 724–730 | fibula's axial key plane | S | MAP §8.12 |
| U42 | 732–741 | axial joint fluid; "small Codex subagents preferred" | S | reference-not-voxel: plan §1, F18; worker route: plan §10 supersedes |
| U43 | 743–749 | axial capsule | S | "a preview is not production": plan P0 |
| U44 | 751–757 | axial lining | S | missing vs measured-empty: plan §14.1; addressed frames: plan §9 step 3 |
| U45 | 759–768 | coronal lining | S | MAP §8.16 |
| U46 | 770–776 | axial anterior recess | S | keep categorical information: plan §1 |
| U47 | 779–781 | coronal anterior cavity; "Use the exact acquired frame for every preview, with a retained generator and raw hash" | R (after the Codex check) | stays: the plan does not carry keeping each preview's generator and raw hash |
| U48 | 784–786 | sagittal capsule | S | MAP §8.19 |
| U49 | 789–791 | axial joint, typed links | S | MAP §8.20 |
| U50 | 794–796 | axial extensor | S | MAP §8.21 |
| U51 | 799–809 | coronal extensor | S | MAP §8.22 |
| U52 | 811–824 | one final middle write; in-flight note | S | MAP; "development figures are not acceptance": plan P0 |
| U53 | 826–849 | retinacular planes, cartilage companions | S | profile maxima are not recognition: plan M10 |
| U54 | 851–882 | native fat pads; Packet B cohort | S | coarse core is a marker, not a boundary: plan M09/M16; limits: MAP §8.25 |
| U55 | 884–906 | axial femoral cartilage | S | MAP §8.26 |
| U56 | 909–923 | sagittal menisci | S, with one owed item | full extent around an in-object point: plan M11; the owed item ("Producer/consumer ledger declarations in the new adapter still need correction during the next family edit") is carried into plan §13 as open, status not re-checked |
| U57 | 926–945 | axial menisci | S | partial scope does not withdraw a component: plan M12 |
| U58 | 947–957 | bounded bone execution; patella guidance owed | S | the owed move of guidance before `patella_plane`'s lens: plan P3 |
| U59 | 959–974 | batched squint kernel | S | equivalent changes keep answers: plan §1 |
| U60 | 976–981 | "Rohan's current instruction": efficiency/accuracy/efficacy connection explicit | R | stays (under its heading), with a dated note on its last sentence ("§8.28 remains the latest accepted new-anatomy description"): the PCL was accepted later, MAP §§8.35–8.36 |
| U61 | 983–1008 | scoped patella execution | S | a local miss is not absence: plan M11; marrow: plan P8 |
| U62 | 1011–1029 | shared common-map handoff | S | E02/E24/R5: plan P7/P8 |
| U63a | 1032–1039 | axial PCL accepted | S | MAP §8.35 |
| U63b | 1041–1049 | the axial PCL's wrong and empty readings; source eligibility; no per-study patches | R | stays: the failure modes the next task (P4) works from |
| U63c | 1051–1056 | axial PCL source pin, gate | S | MAP §8.35 |
| U64a | 1061–1066 | coronal PCL accepted, its reference | S | MAP §8.36 (the section heading at 1059 stays above U64b) |
| U64b | 1068–1081 | the coronal PCL reader's definition ("Native support is independent of projected-target cardinality"; ties, partial scope, measured-empty and outside-slab outcomes named) and the other coronal contexts, with the R5 residual | R (after the Codex check) | stays: the plan does not carry that invariant; the failure modes serve P4, like U63b |
| U64c | 1083–1092 | coronal PCL source pin, comparisons, gate | S | MAP §8.36 |
| U65 | 1095–1104 | complete remaining-work handoff | S | the plan's role: the new preamble pointer and plan §13 |
| U66 | 1107–1135 | the leg-bound conclusion | R | stays |
| U67 | 1138–1160 | the seed-purification substitution | R | stays |

Edits besides the moves: a pointer section to the history file; a note on U15; the U38 clarification;
the U04, U06, U07 and U09 changes above; and a new correction section for 2026-10-18's two further
corrections (this heading-sorted cleanup, and leaving the mis-framed P2a packet running).

The check after applying: every unit marked R or U is present word for word in `docs/HOW_TO_BUILD.md`
(save the stated additions), and every unit marked S is present word for word in
`docs/history/BUILD_STATUS_RECORD.md`.

## The Codex check (GPT-6.1 Sol, high, model-only; `codex-answer-2.md`) and what changed

A first attempt could not read files (the model-only home has no file tool; `codex-answer-1-no-file-access.md`)
and established nothing. The second carried every document whole in its prompt (`codex-prompt-full.md`).
Its points, each adopted:

- U47 and U64b carry obligations the plan does not (a preview's retained generator and raw hash; native
  support independent of projected-target cardinality): both stay, as marked above.
- "Lives in" claims that point to RESOLVING §9 or MAP §8 were not shown to Codex. The lead's basis: the
  moved paragraphs themselves name RESOLVING §9 as the home of their details and limits, and its outline
  has one subsection per part (lateral gastrocnemius head, semitendinosus, the two fat pads, retinacula,
  popliteus, ITB, biceps, gracilis, sartorius, the native fat-pad descriptions); RESOLVING is read whole
  in the grounding sequence. The moved text itself is kept verbatim in the history file.
- U60's last sentence and U38's tail on uncommitted and withdrawn code get dated notes.
- §0 keeps "RELATIVE_POSITION_MAP whole, its §0 first" rather than narrowing it, and calls only dated
  scheduling and status history, not the definitions and limits MAP §8 and RESOLVING §9 record.
- The lens line keeps the qualification that a bounded run may change local readings near its edge and
  must keep its scope and offsets.
- The memory's "what remains" sentence is rewritten, not appended to; its run command gains `--draw`; its
  "plan grows past the next object" becomes the plan's current task.
- AGENTS' confirm-before-proposing gate gains the authorized-plan qualification; the plan's P1 "not
  accepted", the plan's and NEXT's "HEAD a118db8" and NEXT's "leg_on keys only series/slice" get dated
  notes.
