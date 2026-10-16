# Anatomy definition checkpoint — 2026-10-15

Paused at Rohan's request: «Can you find a clean pause point? Resolve whatever is in flight cleanly,
then tell me what's left before we can say we can resolve all the elements of knee anatomy reasonably».

The verified production checkpoint is `c1b8bdb`, the popliteal artery and vein lumens. That code
passed the full local gate with 192 tests, was run on the proof with its images inspected, and
the stored measurements were refreshed for the 58 labelled and three sample test studies.
The subsequent work below produced evidence, previews and proposals only. None of these additional
features has been integrated or verified through the real pipeline. Do not count them as completed.

The stopping criterion remains Rohan's: establish an anatomical rule and a measurable object,
competently at least once. Exact specification, precise measurement, full dimensional collapse
and the later AI work are not additional prerequisites for this definition pass.

## What remains

1. **Medial and lateral patellar retinacula.** The already named sagittal patella's centre selects
   axial slice 22 on the proof through `slice_through`, using scanner geometry and actual slice
   thickness. The acquired image was inspected: both bright patellofemoral recesses and their
   outer wall bands are visible. The proposed relation is the outer recess wall, away from the
   femur, between patella and condyle, analogous to the existing coronal capsular-wall rule.
   No defensible returned masks have yet been produced. The local checkpoint explicitly stores
   empty, unresolved candidates; those arrays do not mean anatomical absence.
2. **Lateral complex beyond the LCL:** popliteus tendon, biceps femoris tendon and iliotibial band.
   Existing LCL coronal views and fibula-guided axial views are prepared. Root read the complete
   Chien lateral-complex section and its figures. The API worker's exploration is saved; it did
   not finish a feature prototype or source patch before being stopped for the pause.
3. **Remaining medial tendons/pes anserinus:** semitendinosus, gracilis and sartorius.
   The semitendinosus has a preview inspected by root: the separate whole dark body behind the
   established semimembranosus, on the inner side of the condyle, nearest to that tendon among
   bodies satisfying those relations. It reuses the existing dark-body construction and selected
   slice. A code proposal is ready; production integration and verification remain.
   Gracilis and sartorius still need individual image-grounded discrimination and implementation.
4. **Separate quadriceps and prefemoral fat pads.** Root inspected a provisional split of the
   existing combined suprapatellar-fat mask around the bright recess on the fat-suppressed
   sagittal, with the non-suppressed twin alongside. The main anterior triangle and posterior strip
   separate; several cross-sections show noisy maxima. A small code proposal is ready.
   This is a competent candidate for the definition pass, not a completed pipeline output.

After these are demonstrated through the real entry point, the listed anatomy definition pass
can be called reasonably complete at the agreed standard. Choosing ideal slices and recovering
each complete object across all views remains the later dimensional-collapse work.

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
