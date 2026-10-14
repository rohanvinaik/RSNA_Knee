# Physical geometry for the proposed object toolkit

2026-10-10. Measured in this Codex session through Chapter 1's `open_corpus → read_study →
read_series`, including actual pixels. All 58 labeled studies and 336 series opened; every series
had stacked pixels and geometry; no study-read exception was returned. This is a geometry/input
measurement, not an object-resolution accuracy measurement.

The initial probe ran in the project's `.venv/bin/python`. The rerunnable equivalent is
`workbench/measure/object_toolkit_geometry.py`; its complete geometry receipt is
`data/measurements/object-toolkit-geometry.json`. The first run's receipt was
`/private/tmp/rsna-object-toolkit-geometry.json`. No image or bulk pixel array is written by the probe.

## What was computed

- Native in-plane spacing, over every slice's DICOM PixelSpacing.
- Width of the demonstrated 8-place tile: eight times native spacing, in mm.
- Length of the superior vector's projection into the first slice plane:
  `hypot(row_direction_Z, column_direction_Z)`. This is a geometric projection, not an anatomy
  assignment. Rounded DICOM directions can produce a value minutely above 1.
- True stack extent: `max(along_normal) - min(along_normal)` after Chapter 1's physical ordering.
  This is not the displacement between first and last filenames.
- Orientation spread supplied by Chapter 1, retained as measured, not a verdict on alignment.

## Results

Ranges below are minimum–maximum; columns name their units. View flags are fluid-sensitive,
fat-suppression, exactly as the series table gives them.

| view | series | native spacing, mm | 8-place tile width, mm | superior projection into plane | ordered stack extent, mm |
|---|---:|---:|---:|---:|---:|
| Axial (0,0) | 18 | 0.1562–0.3516 | 1.2496–2.8128 | 0.0426–0.1686 | 102.30–136.00 |
| Axial (1,1) | 63 | 0.1465–0.703125 | 1.172–5.625 | 0–0.4980 | 39.60–163.80 |
| Coronal (0,0) | 54 | 0.1465–0.703125 | 1.172–5.625 | 0.8099–1 | 33.00–142.68 |
| Coronal (1,1) | 65 | 0.1465–0.7422 | 1.172–5.9376 | 0.7872–1 | 33.00–142.68 |
| Sagittal (0,0) | 72 | 0.1563–0.781254 | 1.2504–6.250032 | 0.9756–1 | 22.50–149.16 |
| Sagittal (1,1) | 64 | 0.1465–0.7813 | 1.172–6.2504 | 0.9835–1 | 70.00–149.16 |

The largest within-series orientation spread was approximately 1e-5 in a direction cosine. It
does not establish inter-series registration or justify treating different acquisitions as the
same samples.

## Codex's inference for the plan

The squint is a useful location map, but an eight-place tile has different physical reach across
acquisitions. Plan coarse routing in physical distance and return to each acquisition's native
samples for fine boundaries. This measurement establishes no particular physical tile size or
minimum clinically relevant feature size.

The axial in-plane superior projection includes zero and is usually small; a vertical-view split
cannot simply be reused there. Some axial planes are substantially oblique. Use the full geometry
and stack relation rather than choosing a row axis from the plane's name.

The older `geometry-spread.md` explicitly used first/last filenames for its extent probe. Its
extent numbers and these ordered-stack spans measure different operands and must not be used
interchangeably. This record leaves that historical measurement intact and gives the new plan the
actual Chapter 1 stack geometry.
