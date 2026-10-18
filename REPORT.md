# Immediate map handoff candidate

This isolated candidate is based on the frozen patella-scope source snapshot. It changes only the copied `scripts/run_interiors.py` and adds `tests/test_immediate_map_handoff.py`; no live source, tests, docs, or measurement outputs were changed.

`offer_native_family` converts a completed family's returned observations once into named `family.map_rows` records. It publishes that actual product with `handed` and reads it at the existing `refine_map` call. For sagittal and axial meniscus results, it also declares consumption of the already-handed original observation product during conversion. The local wrapper retains the converted map rows for the final combined idempotent offer, so the observations are not converted a second time. Empty families produce no map-row product and do not call `refine_map`. The final combined offer contains only those saved pending rows; it does not add `main_records`. Original observation append points and order are unchanged.

Immediate offers follow completion of cartilage companions, recess, native fat support, coronal anterior recess, sagittal capsule, capsule and lining descriptions, axial recess fluid/anterior descriptions, axial joint compartment, axial extensor, coronal extensor, axial femoral cartilage, sagittal menisci, and axial menisci. The sagittal meniscus results continue to pass directly to the axial meniscus source collector.

The new tests exercise the real map handoff: native resolved support is admitted; partial readings, unresolved refusals, laid observations, and unknown object names are not promoted; duplicate evidence leaves map version and candidate count unchanged; an empty family does not invoke `refine_map`; and a later guide gains the patella anchor after the native plane advances the map version. They check actual guide placement values. No AST-only layout test remains.

This is a propagation change, not an equivalent-output or performance optimization. `StudyMap._guide` keeps alternative anchor placements and uses their inclusive depth union with the authored allowance; added usable evidence can broaden a later visited domain. No cost or speed claim is made. No real-study run was performed; the candidate remains for lead review.

## Validation

- Candidate tests: 32 passed across `test_immediate_map_handoff.py`, `test_patella_scope.py`, `test_reference.py`, and `test_bounded_bone_lens.py`.
- Ruff check and format check passed for the changed runner and new test.
- Python compilation passed for the changed runner.
- Global `ty` reported 45 diagnostics on both the unchanged pinned baseline and candidate, with no diagnostic fingerprint added or removed; the copied snapshot lacks neighboring drawing helper modules, which account for unresolved imports.
- The pinned 68-file patella snapshot does not contain `tests/test_study_map.py`; the new tests directly exercise `StudyMap` and `MapContext`.

See `baseline-hashes.json`, `candidate-hashes.json`, and `delta.json` for the pinned provenance and exact candidate delta. `VALIDATION_HISTORY.md` retains the corrected setup/test failures encountered while building this artifact.
