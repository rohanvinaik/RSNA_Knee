# K05 — The corpus and ingest

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K05'` |
| **Depends on** | K02 (store, environments), K03 (vocabulary) |
| **Consumed by** | K07 (volumes, geometry), K09 and K10 (series classes, regimes), K24 (identifiable sets), K18 (the kernel's ingest path) |
| **Commit label / tag** | `knee/K05` · `knee-K05` |

## 1. Purpose and authority

To turn the competition's files into typed facts: every series' header, its stored values, its geometry, and the
study's inventory, regime key and identifiable sets.
- **The founder:** "The questions should be resolved by building and observing". Q6 (series scope) and the
  identifiability of the law are facts measured here.
- **Non-goals:** registration; reading any deviation.

## 2. Dependencies and consumers

**Produced (`knee.core.ingest`, `knee.build.corpus`):**
- **The fetcher:** the Kaggle API for tables, with `KAGGLE_API_TOKEN` from `~/Projects/Kaggle_Killer/.env`; the
  DICOM bundle by ranged reads. Resumable, checksummed, shardable.
- **The header census**, for all 24,371 series (one file per series). Each series gets a `SeriesHeader` record,
  or a named failure code.
- **Decoders** chosen by transfer-syntax UID. Every observed UID is tested.
- **Stored values,** with bits stored, signedness and rescale preserved. Patient-space geometry.
- **Inventories** per study; a **sequence family** per series; a **regime key** per study.
- **Identifiable sets**, within a plane and across planes.

**Consumers:** K07, K09, K10, K18, K24.

## 3. Mechanism

1. **Census.** Read headers only (`stop_before_pixels`) for one slice per series. Record every allowlisted tag
   present, or `absent`: TR, TE, TI, ETL, flip angle, ScanningSequence, SequenceVariant, ScanOptions,
   MRAcquisitionType, field strength, Manufacturer and model, geometry, FrameOfReferenceUID, transfer syntax,
   rescale, bits stored, NumberOfFrames.
2. **Sequence family:** `sequence_family(scanning_sequence, sequence_variant, scan_options, tr, te, ti, etl,
   acq_type) -> code`, one of fast spin echo, spin echo, gradient echo (DESS included), inversion recovery, or
   `unknown`. It is cross-checked against `train_series.csv`'s Fluid_Sensitive and Fat_Suppression flags, and
   disagreements are kept as findings.
3. **Decoding.** `decoder_for(transfer_syntax_uid, available) -> code`. Stored values are kept as int16 or uint16
   per bits stored and signedness. Rescale is applied only where a consumer declares it.
4. **Geometry.** A patient-space affine per series from IPP, IOP and spacing. Slices are ordered along the normal.
   Enhanced multi-frame series are handled when present.
5. **Inventory and regime.**
   - The inventory is the set of (plane, family, suppression).
   - The regime key is (field, vendor, family per series), with a fallback chain (field → vendor → family)
     declared for K09.
6. **Identifiable sets.** `identifiable(inventory_timings) -> {within_plane: [...], cross_plane: [...]}` names
   which contrasts a study offers:
   - a TE contrast at the same fat state;
   - a TR contrast at the same fat state;
   - a fat pair at comparable TR and TE.

   It also answers whether "T1-like" (non-fluid, non-FS) series are ever PD without fat suppression (long TR).
7. **Sharding.** Studies are partitioned by `shard_of(study_digest, k)`. A shard runs on the M1 Max or on the Mac
   Pro via `squishos-compute run squishhub -- …`. Shards from different nodes merge only after a cross-node SAME
   on a sample (decoded values equal byte for byte).

## 4. Contracts

- **`SeriesHeader`:** typed fields; each absent tag reads `absent`; no guessing.
- **Stored-value arrays:** shape (slices, rows, cols), dtype per bits stored, C order, the patient-space affine
  beside it (float64, mm), slice order.
- **Records** are JSONL in `data/store/ingest/<version>/`. Competition-derived, so never in git.

## 5. Implementation choice

- **Python + pydicom,** with the native codec K01 found on Kaggle and locally (pylibjpeg's plugins, or gdcm,
  chosen per UID).
- **Process pool per series.** Per-worker residency is declared at ≤ 1 GB, and the concurrency is declared per
  node (the Mac Pro: ≤ 6 workers on 16 GB).
- **Prior art:**
  - legacy `tools/fetch_from_bundle.py`, `auto_resume_fetch.py` and `fetch_labeled_studies.py`: reuse decision
    per `MIGRATION.md`. The ranged-read logic is argued for reuse if it passes SAME and adversarial tests; the
    one-series `pick_series` is retired;
  - legacy `load_series_volume` and `derive_side` in `tools/register_and_export.py`: K07 decides.

## 6. Verification

- **Detective:** `sequence_family`, `decoder_for`, `identifiable` and `shard_of` are converged.
- **Intent tests** (authored synthetic headers): every family, missing tags, malformed values.
- **Hypothesis:** the geometry's slice order is invariant under shuffled input order.
- **SAME:** decoded values are equal across the M1 Max and the Mac Pro on a sample of each transfer syntax.

## 7. Integration

- `just census` runs the census, resumably.
- `knee.core.ingest.read_series(path) -> (SeriesHeader, StoredValues, Affine)` is the kernel's ingest entry
  (K18).

## 8. Acceptance

- **Behavioural correctness:**
  - every series has a header record or a named failure;
  - every observed transfer syntax decodes, or is named unsupported;
  - the pure decisions stand pinned.
- **Representation fidelity:** the inventory reproduces `train_series.csv`'s plane and flags, with disagreements
  listed.
- **Domain validity:** the identifiable-set distribution, within and across planes, is recorded (in `data/`);
  Q6 and the "T1-like means PD?" question are answered with counts.
- **Performance evidence:** series headers per second and slices decoded per second, per node, scoped as
  "headers only" or "decode only".
- **Evidence scope:** the training corpus at fetch time, and the nodes named.
- **Invalidation:** a change to a decoder or codec version, to the pydicom version, or to the competition data.

## 9. Open matters

- **Facts:**
  - the tag survival per class over all series;
  - the identifiable sets;
  - whether test series show syntaxes or families the training set lacks. Only the public sample is visible; K18
    re-checks.

## 10. Provenance and status log

- **Sources:**
  - the competition's data page (the 86-tag allowlist; transfer syntaxes);
  - `provenance/review/reading_claude.md` §3 (the 45-series tag probe; the inventory from flags);
  - THE_KNEE §3.5 and §4.
- **2026-10-02:** specified in K00.
