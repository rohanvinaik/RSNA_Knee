# The regime key, measured — and three design questions it settles

2026-10-10. Measured through Chapter 1's own reader (`knee.study.slices.read_slice`), one file per
series, all 336 series of the 58 labeled studies. Probe: `scratchpad/probe_regime_key.py`.

## 1. There are no unlabeled studies here. Artifact A rests on the 58.

| split | studies with at least one series on disk | studies with rows but no files |
|---|---|---|
| train | **58** | 4349 |
| test | **3** | 0 |

The 4410 figure counted *rows in the tables*. Only 61 studies have pixels on disk, and 58 of them
are the labeled ones; the 3 test studies are the public sample.

**This settles the founder's "maybe we can even throw in the others from the competition that
aren't labeled" — we cannot. They are not here.** The sqrt(n) pooling gain is therefore
sqrt(58) ~ 7.6x, and the 66x figure in an earlier note is withdrawn (already corrected there).

## 2. Laterality is absent from 54% of series, so it must be derived

| | series |
|---|---|
| no laterality tag of any kind | **181** |
| `Laterality` present | 155 (R 96, L 59) |

`ImageLaterality` and `FrameLaterality` appear nowhere.

**Consequence.** The mirror step cannot rest on the tag. Getting laterality wrong swaps medial for
lateral, which is fatal for exactly four of the 12 (Medial Meniscus, Lateral Meniscus, Medial OA,
Lateral OA), so this is not a place to guess.

Two things follow, and the second is a measurement still to make:
- Laterality is a property of the *study*, not the series. This probe read one file per series, so
  a study may carry the tag on some series and not others. **The per-study coverage is a separate
  count and has not been made yet.**
- Where no series carries it, laterality must be read from the image — the fibula's side relative
  to the tibia is the standard landmark. That reading is itself a lens, and it must concur with
  the tag wherever the tag exists. Disagreement is a named code, never an override.

## 3. The negative-valued series are signed-stored originals, not phase images

5 series of the 336 hold negative stored values. All five:
- `PixelRepresentation = 1` (signed two's complement storage), and
- `ImageType = ('ORIGINAL', 'PRIMARY', 'GDC')`.

They are **ORIGINAL/PRIMARY**, so they are not derived phase or real/imaginary images. `GDC` is a
vendor code, not a standard DICOM value. The earlier note's guess that this was a RescaleIntercept
is withdrawn: it is signed storage.

Related: **103 of 336 series declare `PixelRepresentation = 1`** while only 5 actually show
negative values. Signed storage is common here; negative values are rare. So a negative reading is
a property of the data, not of the declaration, and both must be carried.

The noise law must cope with negative stored values rather than assume a magnitude floor at zero.
This needs a named code; it is not grounds to exclude the series.

## 4. ImageType sorts the corpus into acquisition regimes

| ImageType (first four) | series |
|---|---|
| ORIGINAL, PRIMARY, M_SE, M | 112 |
| ORIGINAL, PRIMARY, OTHER | 91 |
| ORIGINAL, PRIMARY, M, NORM | 65 |
| ORIGINAL, PRIMARY, M, ND | 51 |
| ORIGINAL, PRIMARY, GDC | 12 |
| ORIGINAL, PRIMARY, M_IR, M | 4 |
| ORIGINAL, PRIMARY, M_FFE, M | 1 |

**`NORM` (65 series) is the vendor normalization flag** that Fable named as breaking the
stationary-noise assumption: a smooth gain field multiplies signal and noise together, so sigma_g
becomes sigma_g(x). `ND` (51 series) marks no distortion correction. These are read from the
header, not inferred, and they belong in the regime key.

## 5. The zero share confirms two acquisition regimes

Over 336 series: min 0.0001, median 0.0426, max 0.6042.

| zero share | series |
|---|---|
| < 0.1% | 9 |
| 0.1% - 1% | 56 |
| 1% - 5% | 121 |
| 5% - 20% | 88 |
| **> 20%** | **62** |

**62 series — nearly a fifth — are more than 20% zeros**, up to 60%. On those, an air-based
sigma estimator has no air to read and returns zero. This is the measured basis for requiring two
estimators that must concur, with `BACKGROUND_MASKED` as a named code when E_bg abstains.

## What this changes in the design

1. Artifact A is built from the 58. No unlabeled pool exists locally.
2. Laterality is a derived reading with a tag check, not a tag lookup.
3. Signed storage and negative values are carried as named codes, not exclusions.
4. `NORM` in ImageType is a regime flag with a known consequence for the noise law.
5. The two-estimator concurrence requirement is justified by measurement, not by caution.
