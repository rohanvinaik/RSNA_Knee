# Anatomy definition checkpoint — definition pass completed 2026-10-16

Paused at Rohan's request: «Can you find a clean pause point? Resolve whatever is in flight cleanly,
then tell me what's left before we can say we can resolve all the elements of knee anatomy reasonably».
On 2026-10-16 he asked for the plan to be kept here: «Save this out properly, so a new session knows
exactly what to do to continue/complete this».

## Where the code stands

**Current implementation: `4a126fc`. All five plan steps below are complete.** The final four
parts were each run through the real entry point and their actual output pictures inspected.
The full gate passes with 357 tests. Labelled and test records have been refreshed: all 351
earlier middle-slice records and 48 earlier main-slice records preserve every earlier decision,
silence and saved-array digest, setting aside only the four new objects and optional borders.
The final drawn proof also preserves the earlier border readings. Canonical output now contains
351 middle records and 50 main records, the two additions being the biceps source and twin.
Evidence: `data/readings/definitions-20261016/remaining-production/`, particularly
`final-verification.json`, `final-canonical-drawn-comparison.json` and `final-gate.log`.


The separated suprapatellar fat pads are now resolved in `096f667` (2026-10-16), step 2 below.
The semitendinosus was resolved in `ee5480b`, step 1. Both steps use existing selected slices,
share their measurements, and retain separate masks and named decisions.
The previous anatomy checkpoint was `c1b8bdb`, the popliteal artery and vein lumens. The intervening
maintenance commits changed no decision, silence or saved array over the 58 labelled studies
and the test split:
`fc4ca86` (each read declared where it happens; each part its own colour; the vessel rule's
candidates found in one pass) and `8901990` (the lens's border readings read only with `--draw`;
how to run and test, in `AGENTS.md`, "Running and testing"). Step 3 is resolved in
`be52965`, with its shared-slice reporting preserved in `d948e0e`. Step 4's popliteus
is resolved in `8fa091d`. The remaining biceps femoris, iliotibial band,
gracilis and sartorius are now implemented and verified below; the anatomical definition list
is complete at Rohan's stated criterion. Full-dimensional resolution is the next phase.

The proposed next-phase implementation is written in `docs/DIMENSIONAL_COLLAPSE_PLAN.md`
(2026-10-16), with the independent Fable consultation and comparison in
`data/readings/collapse-20261016/`. Read that plan with `RESOLVING_THE_PARTS.md` §8 before building.
It is planning only; the collapse has not yet been implemented. The first complete case proposed
there is fibula selection, extent and cross-view observations feeding its lateral consumers.

The stopping criterion is Rohan's (2026-10-15): «We're resolving the elements of knee anatomy right
now. Exact specification and precise measurement is for the AI parts, which I have yet to specify. We
have to get the pipeline to produce a binary response--CAN we establish a rule for the lumens? And
CAN we measure them? That is sufficient». For each part below: a rule from anatomy and the parts
already found, and a region the run names and saves, shown competently once on the pictures. The full
dimensional collapse and the later AI work are not prerequisites; they come after.

## Completed plan, in order

Each step is one part, or one group, taken through the loop of `docs/HOW_TO_BUILD.md` §7: look at it
on the pictures at its own pixels; write the plain reading as a few descriptions on the lenses, each
one check with its named abstain code, its numbers from anatomy, a source or the picture (labelled);
draw it on the proof before it touches the run; then wire it in, test, run, look, gate, commit,
refresh `data/`, and show Rohan the picture. The readings marked "Claude's reading" are provisional:
the pictures decide. Mark a step done here, with its commit, when it is.

1. **Semitendinosus tendon — DONE, `ee5480b`, 2026-10-16.** The separate whole dark body behind
   the established semimembranosus tendon, inside the inner condyle's peak, nearest that tendon
   among bodies satisfying both relations. The rule uses the existing semimembranosus axial slice
   and adds no numerical cutoff. `dark_tendon_bodies` makes the crack-closed, thick-body labels
   and their mean patient positions once; both selectors receive this `TendonBodies` reading,
   with no fallback. Its mask is `a2_semitendinosus`, with its own decision. The proof's axial
   slice 11 names the separate 46-pixel body behind the unchanged 72-pixel semimembranosus;
   these counts are observations, never selection rules. The actual output, at its own pixels:
   `data/pictures/definitions-20261016/semitendinosus-proof.png` (BROWN semimembranosus, SILVER
   semitendinosus). The real entry point was run and inspected, and the full gate passed with
   211 tests. Next: step 2. The older proposal below is historical; its optional candidate-map
   fallback was deliberately not implemented. Across all 351 middle-slice and 44 main-slice
   records, every earlier decision, silence and saved array is unchanged (optional borders set
   aside). The labelled and test records have been refreshed.

2. **The two fat pads above the patella — DONE, `096f667`, 2026-10-16.** The existing
   suprapatellar-fat field is parted around the internal recess: quadriceps fat anterior,
   prefemoral fat posterior. `relative_signal` measures acquired FS signal relative to the
   aligned non-FS twin; the pair's existing physical match is reused. On each cross-section
   along the leg, the greatest internal relative signal locates the seam, with named fat on
   both sides; flat or separated tied maxima abstain locally, contiguous ties keep the band.
   No section is interpolated and no numerical cutoff is added. The source retains both pad
   masks, the seam, the aligned twin light and ratio; the masks and seam are laid onto the
   twin. The real proof run names both pads; its earlier decisions and arrays are unchanged.
   The actual picture, inspected at its own pixels:
   `data/pictures/definitions-20261016/suprapatellar-pads-proof.png` (COBALT quadriceps, COPPER
   prefemoral, BLACK seam). Deviations near the seam's ends and the inherited combined mask's
   overreach remain stated limitations, not a precision campaign. Gate: 216 tests passed.
   The independent Fable image reading and usage are retained in
   `data/readings/definitions-20261016/fat-pad-seam/`. Next: step 3.

3. **Medial and lateral patellar retinacula — DONE, `be52965`, 2026-10-16.** On the
   axial slice through the sagittal patella's centre (`slice_through`; slice 22 on the proof) both
   bright recesses beside the patella show, and outside each a dark band runs back toward the
   condyle: the retinaculum, the outer wall of the recess away from the femur, between the patella
   and the condyle. The production rule selects the largest bright recess on each side reaching
   the native patella- and femur-holding regions through the existing 2 mm contact allowance.
   Between the patella target's posterior middle and the femoral region's strongest peak, each
   native cross-section reads the exact minimum signal in the outer strip beside that recess.
   It keeps contiguous ties darker than the neighbouring fluid; separated ties abstain locally.
   Both walls share the selected slice, lens, carried landmarks and measurements. Their own masks
   and decisions are retained; the rule adds no grey-level cutoff or proof coordinates.
   The real proof run identifies medial 70 pixels and lateral 65 pixels (observations, not rules).
   The enlarged actual output was inspected and shown:
   `data/pictures/definitions-20261016/retinacula-proof.png` (AMBER medial, ROSE lateral).
   This locates each band, not thickness or the full course. The full gate passed with 229 tests;
   Vulture retains its 13 advisory contract declarations and fields. The labelled and test records
   were refreshed. All 351 earlier middle-slice and 44 earlier main-slice records, their masks,
   decisions and silences are preserved (new decisions and optional borders set aside).
   The shared-slice correction in `d948e0e` keeps the tendon reference's specific upstream
   abstention reason; the full gate then passed with 230 tests. Next: step 4.
   Claude's
   reading of why the last attempt stalled: the patella carried from one sagittal slice lands on the
   axial as a thin line (`data/pictures/definitions-20261015/retinacula-current-evidence.png`). A
   line is enough as a target, never as a mask: the patella on the axial is the lens's region holding
   that line, as the gastrocnemius rule finds the condyle by the carried bones. The knee's inner and
   outer sides come from the header's word for the knee. Evidence:
   `data/readings/definitions-20261015/retinacula-local-prep/metadata.json` and
   `retinacula-local-build/` (`metadata.json`, `preview.py`); its stored empty candidates are
   unresolved, not anatomical absence.

4. **The lateral complex beyond the LCL — DONE, `4a126fc`, 2026-10-16.**
   The popliteus is resolved in `8fa091d` (2026-10-16): the largest connected part of the existing
   LCL region occupying a concavity of the carried femur's convex envelope. The native T1 LCL
   slice supplies the definition, reusing its selected slice, lens and carried femur. Its own
   mask and named decision are saved beside the earlier LCL labels, and the pair's shared match
   lays the mask onto the fat-suppressed twin. No grey cutoff, new anatomical scale or proof
   coordinate is used. The convex envelope, vertices, equations and candidate readings are kept.
   Actual production output, inspected and shown:
   `data/pictures/definitions-20261016/popliteus-proof.png` (SAGE), T1 slice 21 identified with
   251 pixels, twin laid with 155 pixels (observations, not constants). This localizes the tendon
   in its sulcus; the contour can retain a cortex rim and leaves the outer portion of the
   cross-section. It does not assert the full course. The full gate passed with 246 tests;
   earlier proof results are unchanged. The independent anatomical reading and usage are kept in
   `data/readings/definitions-20261016/popliteus-reading/`; the lead checked the actual mask.
   The remaining lateral definitions are now resolved too:
   - Biceps femoris: the substantial dark body below posterior thigh muscle toward the fibular
     head, combining native and matched FS light. A lazy head-body reading selects a lateral
     peripheral sagittal from the named fibula, without a proof index. The real proof identifies
     2,276 native pixels and carries 1,463 onto the twin (slice 34, observations). Actual output:
     `data/pictures/definitions-20261016/biceps-proof.png` (KHAKI). The anterior arm may include
     distal LCL tissue; this is not a precise conjoint-insertion or full-course separation.
   - ITB: the local dark dip deep to lateral subcutaneous fat, passing the femur and reaching
     proximal tibia on the existing middle non-FS coronal, with no new signal cutoff. Actual
     output: `data/pictures/definitions-20261016/itb-proof.png` (AQUAMARINE): native 221 pixels,
     twin 139, slice 15 (observations). This is a fascial trace, not a thickness measurement.

5. **Gracilis and sartorius — DONE, `4a126fc`, 2026-10-16.** Gracilis is the thinner separate dark body
   medial to semimembranosus and semitendinosus, anterior to the latter, nearest their pair among
   eligible bodies. Its native-pixel sampling lens reuses the existing low signal and patient
   axes on their established axial slice. The real proof identifies 22 pixels, preserving
   semimembranosus 72 and semitendinosus 46. Actual inspected output:
   `data/pictures/definitions-20261016/gracilis-proof.png` (AZURE, BROWN, SILVER).

   Sartorius is a flattened grey muscle sheet medial and anterior to the projected gracilis
   location reference on the middle FS axial. The new objective local-lightness reading uses
   seen samples and their seen surround; the muscle-grey class and reach are explicit first
   visual baseline readings, not a parameter search. It keeps the largest whole eligible body,
   refusing exact ties. The source is a location target from another slice, not an asserted
   tendon boundary or intervening course. The semimembranosus group runs once earlier in the
   same production graph so its gracilis points are available before middle persistence.
   The real proof identifies 188 pixels on slice 16; actual inspected output:
   `data/pictures/definitions-20261016/sartorius-final-close.png` (ULTRAMARINE), with the whole
   knee in `sartorius-final-overview.png`. Small halo/lobe overreach remains documented.
   The full gate passes with 357 tests, including two independent checks that caught and fixed
   excluded samples influencing the worker's initial median. All constants and the anatomical
   selector stayed fixed. Retained provenance/status readings remain honestly listed as unread.

All five steps are done: the anatomy definition pass is complete at the stated once-per-object
criterion. Next comes the dimensional collapse
(`docs/RESOLVING_THE_PARTS.md` §8): every part at its best slices across the five views. The AI part
is Rohan's to describe; diagnosis only when he says.

## How each part is wired in and recorded

- Code. Its rule in `src/knee/objects/assignments.py`, with its paragraph in the module note (a
  numbered set of descriptions of how it appears in these scans, each one check with its named
  abstain code, and the category of the twelve it relates to; the ACL's paragraph is the worked
  example) and a test. Its own mask (`a2_<part>`) and decision code, as the joint boundaries, the
  bursa and the vessels have; an entry in `OBJECT_CODES`; a colour and word in `OBJECT_COLOURS`
  (`scripts/object_assignments.py`) that `tests/test_part_colours.py` accepts and the pictures show
  apart from its neighbours. Its mask handed on once it is named, each read declared where it
  happens (the drawing's in `measure_study`), and nothing a stage already made computed again.
- Run and test (`AGENTS.md`, "Running and testing"): the proof with `--draw` to look; the run without
  `--draw`, as the competition runs it; the gate; then the labelled studies, compared with the
  receipts from before (`scripts/compare_receipts.py`), so every part already named keeps its
  decisions.
- Record: a row or subsection in `docs/RESOLVING_THE_PARTS.md` (§5 or §9), a line in
  `docs/HOW_TO_BUILD.md`, and its step marked done here.

## Open, not blocking

- An independent reading of the pictures (`data/readings/colours-20261016/`) found the joint's
  magenta and the MCL's hot pink hard to tell apart where both are thin lines at the joint's inner
  edge, and the capsule's spring green near the lateral meniscus's lime. Neither was changed.
- The vessel rule's closed-lumen map is kept and read by no stage, by design
  (`docs/RESOLVING_THE_PARTS.md` §9); dropping a kept reading is Rohan's call.

## Saved evidence and proposals

All paths below are relative to the project and lie in the ignored data tree. Exact source UIDs
and geometry are in their metadata; do not transcribe guessed identifiers into prose.

- Retinacula: `data/readings/definitions-20261015/retinacula-local-prep/metadata.json`;
  `retinacula-local-build/metadata.json` and `preview.py` under that same readings parent.
  Pictures: `data/pictures/definitions-20261015/retinacula-patella-centre-axial.png` and
  `retinacula-current-evidence.png`. `retinacula-preview-outlined.png` asserts no retinacular mask.
- Fat pads: `data/readings/definitions-20261015/fat-pads-local-prep/`, particularly
  `suprapatellar_pads_code_proposal.md` and `measurements.json`.
  Picture: `data/pictures/definitions-20261015/suprapatellar-ridge-preview-provisional.png`.
  The draft helper is longer than necessary: independent cross-sections need axis selection and
  transposition, but do not need to be walked in superior order. Keep integration small and reuse
  shared patient-position measurements. The source must use physical axes, not proof coordinates.
- Semitendinosus: `data/readings/definitions-20261015/hamstrings-local-prep/`, particularly
  `semitendinosus_code_proposal.md`, `semitendinosus-candidate.json` and the retained NPZ maps.
  Picture: `data/pictures/definitions-20261015/semitendinosus-candidate-provisional.png`.
  Share the dark-body labels with the existing semimembranosus selector in its existing slice
  stage; do not compute the candidate construction twice. Keep the established selector's behavior.
- Lateral complex: `data/readings/definitions-20261015/lateral-complex-local-prep/` and
  `lateral-complex-worker/`; pictures prefixed `lateral-complex-` in
  `data/pictures/definitions-20261015/`. Mean saved fibula support includes shaft; do not call that
  point its head. The superior-edge axial selection is recorded separately.
- Anatomical sources: `data/readings/definitions-20261015/anatomy-sources/`. The official Chien
  PDF and complete rendered pages 14–17 are saved. Root read the complete lateral-complex and
  retinacula subsections. `remaining-anatomy-reading.md` records the separate pes source scope.

## Worker closeout

The retinacula API worker reached its run budget without a source implementation: **$12.08731475**,
terminal reason `budget_exhausted`. The independent lateral-complex API worker was stopped on
Rohan's pause request: **$6.0503875**, terminal reason `aborted_streaming`. Total for this pass:
**$18.13770225**. Prompts, events, terminal results and launch metadata are retained in
`retinacula-worker/` and `lateral-complex-worker/` under the readings parent. Neither is authority
for an anatomical name. Do not automatically retry the budget-exhausted consultation.

At the original pause the local helpers stopped at saved artifact checkpoints, with no partial
integration in the production tree. Step 1 above records the subsequent completed implementation.
The original pause proposals above remain historical evidence. They have been superseded by
the completed production definitions in steps 1–5 and `RESOLVING_THE_PARTS.md` §9. On resuming,
read the original thesis conversation and current source, then begin the dimensional-collapse
discussion; do not rebuild the already demonstrated anatomical definitions.

## Final worker closeout — 2026-10-16

The nine Sonnet prototype/implementation workers for these last four parts all terminated
successfully. Their recorded total is $17.4480384, computed from their launch metadata and saved
in `data/readings/definitions-20261016/remaining-production/worker-closeout.json`. The separate
Fable consultations returned token usage without monetary cost. No worker remains active.
The lead independently checked the source, the actual output and preservation; worker results
alone are not anatomical evidence. The older closeout above is the earlier paused pass.
