# How hard is the alignment? Per-view geometry, measured

2026-10-10. DICOM headers only (`stop_before_pixels`), first and last file of each series.
Probe: `scratchpad/probe_geometry_spread.py`. 58 labeled studies, 336 series.

## Per view

| view | series | slices (min/med/max) | mm per pixel | field of view mm | thickness mm | extent mm |
|---|---|---|---|---|---|---|
| Sagittal (0,0) | 72 | 11 / 29 / 136 | 0.2 / 0.4 / 0.8 | 150 / 170 / 240 | 1.6 / 3.0 / 5.0 | 2.3 / 27.0 / 99.4 |
| Coronal (1,1) | 65 | 15 / 30 / 42 | 0.1 / 0.3 / 0.7 | 130 / 160 / 240 | 2.0 / 3.0 / 5.0 | 3.3 / 24.0 / 102.3 |
| Sagittal (1,1) | 64 | 15 / 28.5 / 320 | 0.1 / 0.3 / 0.8 | 130 / 170 / 240 | 0.8 / 3.0 / 5.0 | 3.3 / 36.0 / 96.0 |
| Axial (1,1) | 63 | 12 / 30 / 160 | 0.1 / 0.3 / 0.7 | 81 / 160 / 240 | 0.6 / 3.5 / 5.0 | 3.3 / 27.3 / 105.6 |
| Coronal (0,0) | 54 | 16 / 30 / 42 | 0.1 / 0.3 / 0.7 | 120 / 160 / 240 | 2.0 / 3.0 / 4.5 | 3.5 / 30.9 / 89.1 |
| Axial (0,0) | 18 | 27 / 33 / 40 | 0.2 / 0.2 / 0.4 | 150 / 161 / 180 | 3.0 / 3.0 / 3.5 | 3.3 / 41.2 / 92.4 |

Matrix sizes observed: 320, 384, 400, 432, 512, 640, 704, 832, 960.

## What this says

**The physical extent is consistent; the pixel grid is not.** Median field of view is 160-170 mm
in every view, and the bulk sits in a narrow band around it. But in-plane sampling spans 0.1 to
0.8 mm per pixel — an eightfold range — and matrix size ranges from 320 to 960. The knees really
are "roughly the same size" in millimetres, as the founder said; they are simply sampled at very
different pixel densities.

**Two consequences for the collapse.**

1. The common frame must be **physical (millimetres), never pixel**. Chapter 1 already extracts
   what this needs: slice normal, direction cosines, ImagePositionPatient, PixelSpacing, and the
   ordering along the normal.

2. **The squint's tile is a physical size, and the acquisition heterogeneity sets a floor on it.**
   A tile cannot be finer than the coarsest acquisition can fill (0.8 mm per pixel in plane,
   5.0 mm slice thickness). So the squint is not only an S/N device here: it is what makes
   heterogeneous acquisitions commensurable at all. The floor is measured, not picked. What sets
   the ceiling (the smallest feature that must survive) is a domain question, and is the founder's.

**Outliers to handle, not to average over**: a few series carry 136, 160 and 320 slices, against a
median near 30. Those are a different acquisition kind (thin-slice or multi-echo), and stack extent
runs from about 3 mm to about 105 mm. Slice thickness reaching 0.6-0.8 mm in some series against
5.0 mm in others means the through-plane sampling differs by nearly an order of magnitude.
