# Anatomy definition checkpoint — 2026-10-15, plan updated 2026-10-16

Paused at Rohan's request: «Can you find a clean pause point? Resolve whatever is in flight cleanly,
then tell me what's left before we can say we can resolve all the elements of knee anatomy reasonably».
On 2026-10-16 he asked for the plan to be kept here: «Save this out properly, so a new session knows
exactly what to do to continue/complete this».

## Where the code stands

The last part of the anatomy resolved is `c1b8bdb`, the popliteal artery and vein lumens. The commits
after it changed no decision, silence or saved array over the 58 labelled studies and the test split:
`fc4ca86` (each read declared where it happens; each part its own colour; the vessel rule's
candidates found in one pass) and `8901990` (the lens's border readings read only with `--draw`;
how to run and test, in `AGENTS.md`, "Running and testing"). The work on the parts below produced
evidence, previews and proposals only. None of it is in the production tree; do not count it as done.

The stopping criterion is Rohan's (2026-10-15): «We're resolving the elements of knee anatomy right
now. Exact specification and precise measurement is for the AI parts, which I have yet to specify. We
have to get the pipeline to produce a binary response--CAN we establish a rule for the lumens? And
CAN we measure them? That is sufficient». For each part below: a rule from anatomy and the parts
already found, and a region the run names and saves, shown competently once on the pictures. The full
dimensional collapse and the later AI work are not prerequisites; they come after.

## Plan to complete, in this order

Each step is one part, or one group, taken through the loop of `docs/HOW_TO_BUILD.md` §7: look at it
on the pictures at its own pixels; write the plain reading as a few descriptions on the lenses, each
one check with its named abstain code, its numbers from anatomy, a source or the picture (labelled);
draw it on the proof before it touches the run; then wire it in, test, run, look, gate, commit,
refresh `data/`, and show Rohan the picture. The readings marked "Claude's reading" are provisional:
the pictures decide. Mark a step done here, with its commit, when it is.

1. **Semitendinosus tendon.** Inspected preview and code proposal ready. The separate whole dark
   body behind the established semimembranosus tendon, on the inner side of the inner condyle, the
   one nearest that tendon among the bodies that satisfy those relations, on the semimembranosus
   tendon's own axial slice (`semimembranosus_slice`). Read first, whole:
   `data/readings/definitions-20261015/hamstrings-local-prep/semitendinosus_code_proposal.md`; then
   look at `data/pictures/definitions-20261015/semitendinosus-candidate-provisional.png`. Make the
   dark-body labels once on that slice, in `semimembranosus_slice`, and hand them to both selectors,
   with no fallback: the proposal's optional `candidate_labels=None`, which builds them again when
   they are not handed in, would be a second path that only a test reaches (`semimembranosus_on_slice`
   has one caller in the run, `semimembranosus_slice`, and one test, which then hands them in as the
   run does; `docs/HOW_TO_BUILD.md` §5, one path). Keep the semimembranosus selector's behaviour.

2. **The two fat pads above the patella, parted.** Inspected preview and a small code proposal ready:
   the suprapatellar fat split along the collapsed recess between the pads, the quadriceps pad in
   front and the prefemoral pad behind, on the sagittal middle slices. Read first, whole:
   `data/readings/definitions-20261015/fat-pads-local-prep/suprapatellar_pads_code_proposal.md` and
   `measurements.json`; look at
   `data/pictures/definitions-20261015/suprapatellar-ridge-preview-provisional.png`. Claude's reading
   (2026-10-16): the preview finds the seam from the brightest place in each row of the
   fat-suppressed slice, and some rows stray; the seam shows in both scans of the same place, a
   faint white film with fat suppressed and a thin dark curve without, so take it where the two
   agree, through the pair's one match of places (never one lens alone). Keep the helper small (the
   cross-sections need not be walked in superior order), reuse the shared patient-position
   measurements, and use the patient's axes, never proof coordinates.

3. **Medial and lateral patellar retinacula.** Slice chosen, pictures inspected, no rule yet. On the
   axial slice through the sagittal patella's centre (`slice_through`; slice 22 on the proof) both
   bright recesses beside the patella show, and outside each a dark band runs back toward the
   condyle: the retinaculum, the outer wall of the recess away from the femur, between the patella
   and the condyle (the capsule's rule, `capsule_at_side_recesses`, at these recesses). Claude's
   reading of why the last attempt stalled: the patella carried from one sagittal slice lands on the
   axial as a thin line (`data/pictures/definitions-20261015/retinacula-current-evidence.png`). A
   line is enough as a target, never as a mask: the patella on the axial is the lens's region holding
   that line, as the gastrocnemius rule finds the condyle by the carried bones. The knee's inner and
   outer sides come from the header's word for the knee. Evidence:
   `data/readings/definitions-20261015/retinacula-local-prep/metadata.json` and
   `retinacula-local-build/` (`metadata.json`, `preview.py`); its stored empty candidates are
   unresolved, not anatomical absence.

4. **The lateral complex beyond the LCL: popliteus tendon, biceps femoris tendon, iliotibial band.**
   Nothing built. Read first: the lateral-complex section of the Chien article in
   `data/readings/definitions-20261015/anatomy-sources/` (read whole on 2026-10-15, with its
   figures), and look at the prepared views (`lateral-complex-local-prep/`; pictures
   `lateral-complex-*.png` in `data/pictures/definitions-20261015/`). Claude's readings, to check on
   the pictures:
   - the popliteus tendon: the dark oval in the notch of the femur's outer condyle, on the LCL's own
     coronal slice. Today the LCL's band takes it in, a recorded over-reach: name it as its own
     region and leave the LCL as it is;
   - the biceps femoris tendon: the dark band reaching the fibula's head, behind and outside the LCL;
   - the iliotibial band: the thin dark band down the front of the outer side to the tibia's
     front-outer edge, likely on a slice in front of the LCL's, chosen by place from parts already
     found.

   Each is the MCL's and LCL's kind of rule: a dark band joining two parts already found. The saved
   mean fibula support includes the shaft: do not call that point its head.

5. **Gracilis and sartorius.** After the semitendinosus, by their order along the knee's inner side.
   Claude's reading, to confirm with the medial-knee source (LaPrade 2007, `[LP-MED]` in
   `docs/OBJECTS_AND_CONDITIONS.md`), the pes source recorded in
   `data/readings/definitions-20261015/remaining-anatomy-reading.md` (Zhong et al. 2018, §3.1–3.2
   only: the sartorius, the gracilis and the semitendinosus front to back where they attach, the
   semitendinosus behind and outside the other two at the back-inner knee) and the pictures, before
   writing anything: at the joint line, along the inner side from back to front, the semitendinosus
   (behind the semimembranosus tendon, step 1), the gracilis as a small dark oval, and the
   sartorius, mostly muscle there.

When all five are done, the anatomy definition pass is complete. Next comes the dimensional collapse
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

The local helpers stopped at saved artifact checkpoints. No new recognition code, dependency
changes or partial integration is left in the production tree. Resume from the original thesis
conversation and current source, then use this file to locate the evidence; inspect each preview
before integrating it. Run the real proof entry point, inspect its pictures and run the gate
before marking any of the remaining features complete.
