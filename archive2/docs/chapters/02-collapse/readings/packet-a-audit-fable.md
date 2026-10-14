# Historical approved source audit

This is Fable’s independent reading of the approved Packet A source snapshot before repairs. It is not current measured state or authority over the design. See `packet-a-audit-resolution.md` for the checked findings and current evidence paths. The exact approved prompt remains private under `data/audits/`; prompt digest and API usage are in `packet-a-audit-fable-metadata.json`.

# Packet A — external audit

Scope: only what the shown source proves. No anatomical content, no redesign.

## Defects, ranked by consequence

### 1. `measure_series` raises per-series `ValueError`s that abort the whole study (`run_study`, `object_analysis.main`)

`measure_series` raises `invalid_slice_index` when `request.slice_index` is outside *this* series' volume, and `PlaneFrame.from_dicom` raises `degenerate_orientation`/`invalid_*` on *this* series' tags. `run_study` does not catch; the exception escapes for the entire study. In `object_analysis.main` the study lands in `failures`, no `SeriesRun` records are kept, and the regime readings of every other series in that study are discarded too.

Reproducible: a study with two stackable series of 3 and 1 slices, `AnalysisRequest(..., slice_index=2)`. Series 1 is valid; series 2 raises; `run_study` returns nothing for either. Without `analysis`, `run_study` never raises for a series; attaching measurement therefore changes the production entry point's failure semantics from per-series codes (`no_stacked_volume`, `geometry_unreadable`, `axis_unavailable`) to whole-study abort for two further conditions that are equally per-series. `SeriesMeasurement.code` already exists for exactly this purpose.

### 2. `scripts/verify_profiles_same.py` writes `"code": "same"` on bare `assert`

`assert_same` guards shape and dtype with `assert`; `main` guards `support_code`/`support_codes` with `assert`. Under `python -O` these are compiled out and `same.json` is written unconditionally. Only the `np.testing.*` calls survive optimisation. The SAME standing, which the lead cites as the proof gate, is thus contingent on interpreter flags. Additionally `same.json` carries no digest of `receipt.json` or of the `.npz` files it checked (the lead's "verification linkage" point; acknowledged, not repeated).

### 3. `object_analysis.main`: `kernel_sources` depends on the working directory and can be silently empty

`Path("src/knee/collapse").glob("*.py")` is relative to cwd, not to the imported package (`knee.collapse.__file__`). Run from any other directory, the receipt's `kernel_sources` is `{}` with no error. Also `pipeline.py` and `study/series.py` are not hashed, although `stack_geometry` (ordering, hence which plane is "middle") and `run_study` determine what was measured. The lead's planned "selected source plane identity" partially covers this; the cwd fragility is a separate, provable defect.

### 4. `object_analysis.main`: partial records on mid-study failure

Inside the `try`, `records.append`, `codes[...] += 1` and `np.savez_compressed` happen per series. If a later series of the same study raises (`missing_measurement_record`, `read_bytes` on a vanished file, savez I/O error), the earlier series' records and `.npz` files remain, and the study is *also* listed in `failures`. `series_count` and `codes` then count series from a study marked failed; `study_count` and `series_count` cannot be reconciled from the receipt.

### 5. `object_analysis.main`: `--backend jit` without numba loses the receipt entirely

Each study fails with `required_backend_unavailable:jit` (caught, recorded). After the loop, `version("numba")` raises `PackageNotFoundError` outside any handler; `receipt.json` is never written and the collected `failures` are lost. The condition that caused every failure is the one that prevents it from being recorded.

### 6. Unvalidated request fields when the axis is unavailable (`measure_series`)

`request.backend` and `request.offsets_mm` are only validated inside `sample_profiles`, which is skipped on the `axis_unavailable` branch; `direction_lps` is validated only after `physical_squint` has run. The lead already states this must fail before the branch; acknowledged. One addition the reading does not mention: `AnalysisRequest.backend="numba"` (invalid) produces a *successful* `axis_unavailable` receipt record with no backend error anywhere, so a receipt can show a backend string that was never admitted.

### 7. `object_analysis.main`: `--samples 1` probes at `-span_mm`, not the centre

`np.linspace(-s, s, 1)` returns `[-s]`. The parser accepts `samples=1`, so a one-sample run records `offsets_mm=(-span,)`. It is recorded honestly in the receipt, but it is not what "span" suggests and nothing warns.

### 8. `physical_squint` allocation contract is understated

`ComputeContract.allocation="64 bytes per tile plus one tile's finite values"`. The loop also allocates `np.isfinite(block)` (one byte per source pixel per tile), the boolean-indexed `values` copy, and `np.median`'s internal partition copy. Since the contract is declared data meant to be audited against the function, the statement is provably incomplete. No correctness consequence.

### 9. `verify_profiles_same.py` / tests: the signed-zero check is vacuous for this kernel

In `profile_samples_reference`, `total` starts at `+0.0` and `+0.0 + (-0.0) == +0.0`; any exact cancellation yields `+0.0` under round-to-nearest. `np.diff` of equal samples gives `+0.0`, divided by a positive offset difference. Hence `samples` and `slopes` can never contain `-0.0`, and the signbit assertions in `assert_same` and `test_reference_and_jit_agree…` cannot fail. Not a defect in the kernel; a defect in what the proof gate claims to have exercised ("signed zero").

## Items the lead's reading already answers (acknowledged, not repeated)

- Support as a conjunction of geometric and finite-value support: implemented exactly as declared in `profile_samples_reference`; zero-weight neighbours are not read.
- Orthonormal-axis assumption in the mm→pixel step (`sample_profiles` divides by spacing per axis; `measure_series` builds `normals` from `axes.T @ direction`): the lead has flagged the metric statement and proposes an identity test. Source confirms the assumption; nothing further provable.
- `numeric_plane` admitting float16/extended floats that `jit_profile_kernel` may reject: acknowledged.
- Read-only outputs as cooperation, not protection: `handed_on` does only `setflags(write=False)`; acknowledged.
- "One pixel decode per series" vs. hashing rereads: `read_series` decodes once; `object_analysis` rereads bytes for `sources`; acknowledged.
- Graph exercising only the unavailable-axis branch (`test_hamilton_graph_…`): acknowledged; the measured branch is untested in the graph.
- SAME scope limited to this environment: acknowledged.

## Verified as consistent (no finding)

- `PlaneFrame.from_dicom` column ordering (column 0 = row direction = `orientation[3:]`), spacing broadcast, `to_patient`/`to_native` round trip; `measure_series` recovers unit directions via `basis_lps / spacing_rc` correctly.
- Edge handling in `profile_samples_reference`: at `row == R-1` the `ri=1` weight is exactly 0 and `plane[R, ·]` is never read; `floor` of a value in `[0, R-1]` never produces an index that, plus a positive-weight neighbour, exceeds `R-1`.
- Tile centre formula `(r0 + r1 - 1)/2` with half-open bounds; `ceil` tile and shape arithmetic; empty-plane behaviour.
- Slope semantics (`np.divide … where=both`) match the declared "adjacent valid pairs / offset difference".
- Middle index `len(volume)//2` in stack order with stable `argsort` on filename order.
- `work_counts` constants (4 reads, 9 bytes) agree between `object_measurements.py`, `object_analysis.py` and the kernel contract.

## Unresolved questions (not defects)

1. **Ordering of filename ties.** `sorted(directory.glob("*.dcm"))` is lexicographic (`slice-10.dcm` < `slice-2.dcm`). The declaration "stable ties from filenames" is satisfied, but is lexicographic order the intended tie-break for real corpus naming?
2. **FMA contraction.** Bit-equality between reference and Numba relies on LLVM not fusing `weight * value` into `total`. `fastmath=False` is set; whether contraction is additionally disabled in the installed Numba/LLVM is not provable from source. The existing SAME run is the only evidence and is environment-scoped, as declared.
3. **`.npz` naming by `series_uid` only.** If a series UID recurs across studies (train/test, or `--uid` omitted), `np.savez_compressed` overwrites silently. Does the corpus guarantee uniqueness?
4. **`from_dicom` 1e-4 orthonormality tolerance.** It is described as a format check. Is there corpus evidence that no stackable series fails it? If one does, item 1 applies.
5. **`orientation_spread`** is computed by `stack_geometry` but `measure_series` uses only the selected slice's orientation/spacing. Is per-slice geometry intended to be trusted independently of spread, or should the receipt record spread so a reader can see it?
