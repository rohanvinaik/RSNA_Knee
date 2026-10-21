# Reading an object’s saved pixel bundle

This note follows the receipt schema in `src/knee/collapse/observations.py` and the production storage APIs. An observation is a typed reference to retained arrays; it does not carry pixels itself. The study’s object table says what was observed, how it was placed, and what remains unresolved. It is the entry point for finding the corresponding per-series artifact.

These retained high-resolution products supply teaching evidence and full-profile readback. They
are not a required reconstruction prefix for every diagnostic study. The active squint/recall path,
its retained cheap descriptions and the distinction between proposed and called identities are in
[SQUINT_RUN_GUIDE.md](SQUINT_RUN_GUIDE.md) and
[CLASSICAL_AI_BUILD_DESIGN.md](CLASSICAL_AI_BUILD_DESIGN.md). A stored proposed name does not by
itself establish identity or a clinical finding.

## Distinguish the three provenances

`native` records what the slice’s own rule resolved (`kind=resolved`) or what a native reader measured (`kind=reading`). A reading such as `source_contacted_enclosed_darkness` is a native measurement pointer and code, not a resolved boundary claim.

`laid` records identity transferred from the corresponding physical places in a paired sequence. Its presence says which places were inherited through that transfer; it does not turn that sequence’s own abstention into a native identification.

`projected` records physical locations projected onto another plane. In the schema it is necessarily `kind=target`: a place to ask a native question, not a segmented boundary. Keep its `off_plane_mm` and originating artifact with it. Do not merge a projected target into the native support.

Each object entry also stores `unresolved` by provenance and named code. That is a record of a missing or refused saying, not evidence that the object is absent. `None` means unmeasured; do not convert it to zero. The generic `pipeline.no_observation_record` means no observation/refusal was retained for that object in that receipt, not a negative finding.

## Finding pixels in an artifact

A saved observation reference has `artifact`, `support`, and optional `row` or `label`, along with the series, view, slice list, code and count. Resolve `artifact` relative to the directory containing that receipt. Find the matching `records` entry by both `study_uid` and `artifact`; its `arrays` table carries each saved array’s digest. Use `knee.array_archive.open_arrays` for `.npz.xz` files and verify the loaded array with `knee.receipt.digest` before interpreting it.

The address fields are type-dependent, as documented in `observations.py`:

- A `label` selects pixels from an integer-coded array, for example `a1_objects == label`. A boolean support already contains the places and has no label.
- For a stack with one mask per observation row, `row` indexes its first axis. The example below validates one such actual support: the semitendinosus native coronal reading at slice 28, support `a22_posterior_reading_support`, row 1.
- For a profile, `slices` names first-axis entries. For packed unequal-sized planes or traces, `row` addresses `offsets[row]:offsets[row + 1]`; the accompanying shapes and `note` define any reshape or trace meaning. Those packed arrays require their matching offsets/shapes fields. Do not apply the stack example’s `array[row]` interpretation to them.

`count` is a useful consistency check for the observation’s stated support. The archive’s digest and dimensions are the check on the bytes and shape. When a support is packed or a labelled map, apply its documented addressing before comparing counts.

## Runnable, single-artifact example

The companion test loads the saved cohort receipt through `knee.json_store.load_json`, follows the exact semitendinosus `native/reading` reference, opens only its named compressed artifact with `knee.array_archive.open_arrays`, validates the declared digest, and selects the observed stack row. It does not load or decompress other cohort artifacts.

Run from the project root using the project interpreter (the example requires the retained local cohort artifact, so it is development evidence rather than a data-free CI test):

```sh
.venv/bin/python -m pytest -rP \
  data/readings/collapse-20261017/full-build/targeted-compute-20261018/b9b10-integrated-20261019/metadata-batch/consumer-example/test_saved_observation.py
```

The pinned example is from the completed 58-study cohort receipt under `data/readings/collapse-20261017/full-build/targeted-compute-20261018/b9b10-integrated-20261019/cohort/labeled-workers4-no-draw/interiors/receipt.json`. Its exact observation has code `source_contacted_enclosed_darkness`, count 101, view `Coronal/1/1`, slice 28, and support row 1. In the same object entry, projected targets use a separate projected artifact and remain `kind=target`; the native observation is not replaced by those pointers. The object’s unresolved native codes remain named separately.

## Source contracts read for this handoff

- `src/knee/collapse/observations.py`: `Observation`, `Unresolved`, `describe_objects`, and the module-level address/provenance contract.
- `src/knee/array_archive.py` and `src/knee/json_store.py`: `open_arrays` and `load_json` behavior, including compressed sidecars and close/context-manager behavior.
- `src/knee/receipt.py`: `digest` and the receipt’s saved-array reference convention.

This handoff documents storage and addressing only. It makes no anatomical acceptance claim.

## Per-study entry point and relations

The production operation writes `receipt.json.xz` in each requested output directory. `load_json(run_dir / "receipt.json")` accepts that file and legacy uncompressed receipts. The main recognition receipt's `objects[study_uid][object_name]` table groups references as `observations[provenance][kind][support]`; each value is a list of addresses. Original per-record observations keep their explanatory notes beside the support's other arrays. `definition_decisions`, `search_refusals`, and named unresolved outcomes remain available even when a different view supplies a reading.

`anatomical_relations` are sourced definition links to the other objects in that study. They express the authored anatomy; they do not claim the current images independently measured every attachment or enclosure. `native_series` counts only independently resolved native observations, so a valid complementary native reading need not appear there. Diffuse fields and bone-associated marrow retain their own field/support representation instead of invented reference points. Marrow appears under a named bone's `associated_fields`, with its source support and calibration relationship.

The per-study `study_map.json.xz` preserves physical geometry, selected key planes, partial endpoints and ordered pair relations. Three independently selected key planes constrain the object's reference in patient millimetres. Their intersection is a reference for search, not a measured tissue voxel or volume. Keep the saved original supports for actual pixels and the map for physical relations.

Coarse search readings remain available beside the fine supports. For example, axial femur/tibia section estimates are retained under `a4_axial_coarse_*`, and coronal/axial patella section readings under `a4_patella_coarse_*`. Their matching slice, block geometry, packed offsets and status arrays define their addresses; they are not full-resolution tissue boundaries. Fat-pad contexts also retain their consumed coarse bone readings under `a4_<view>_native_fat_context_coarse_*`, with native core/seed arrays where measured. Those location-seeded measurements do not become resolved native bone observations merely because a later reader consumes them.

A native reading may have `count=None` while still addressing retained measured arrays, as the patella coarse-section reader does. Inspect its code, support type and associated geometry. Counting only positive full-resolution pixel counts would omit such readings; counting every reading as a successfully identified body would also be incorrect.

This is the present boundary for the later author-specified encoding and diagnosis. Those stages can consume the retained object pixels, original signal, geometry and relations without repeating recognition. The output itself makes no diagnostic verdict and supplies no invented probability.
