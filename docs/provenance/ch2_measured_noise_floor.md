# Can we measure the noise law? Tested against the data

2026-10-10. Probe: `scratchpad/probe_noise_floor.py`. One mid-stack slice from each of 8 labeled
studies' Axial (1,1) series — the only view present in all 58. Pixels decoded locally with
pydicom (decoding works here; the Kaggle kernel's missing JPEG-Lossless decoder is a separate,
already-recorded problem).

## What was measured

| matrix | range | p50 | zeros | corner median | sigma (Rayleigh) | sigma (median est.) |
|---|---|---|---|---|---|---|
| 320x320 | 0-569 | 11 | 8.60% | 3.0 | 2.1 | 2.5 |
| 480x480 | 0-1050 | 108 | 15.69% | 0.0 | 1.7 | **0.0** |
| 640x640 | 0-2027 | 164 | 0.02% | 26.0 | **107.7** | **22.1** |
| 512x512 | 0-1877 | 245 | 4.86% | 224.0 | 148.0 | 190.2 |
| 640x640 | 0-1059 | 12 | 0.38% | 4.0 | 4.1 | 3.4 |
| 640x640 | 0-1093 | 3 | 43.36% | 0.0 | **0.0** | **0.0** |
| 640x640 | 0-1655 | 218 | 0.80% | 5.0 | 6.5 | 4.2 |
| 544x512 | **-721**-8920 | 248 | 0.12% | 123.0 | 104.9 | 104.5 |

## Three findings, each with a design consequence

**1. The air-based noise estimator does not port.** Codex proposed measuring sigma from imaged,
artifact-free air by the Rayleigh estimator. The zero fraction across these series runs from 0.02%
to 43.36%: some scanners (or reconstructions) background-suppress the air. Where they do, the air
sample is identically zero and **sigma is estimated as 0.0** — rows 2 and 6. A zero denominator
makes every place clear any level.

This is precisely the failure the sibling codebase already fixed. `embryo_background`'s recorded
measurement: "5 of 71 samples carry 5-28% zero fill, which pulled the level down by up to half and
**set the noise to 0 when fill passed half the dark voxels**." Same failure, different domain.

**The fix is already in the sibling code and is more robust than the textbook MR estimator.**
`region_background` reads `noise` as "the robust spread (MAD -> sigma) of the **below-level**
voxels" — it takes the quiet *population*, wherever that lives, and never needs a spatially
designated air region. `embryo_background` makes it one global reference per volume rather than
per window. Porting those two together gives a per-series noise reading that survives background
suppression, because it never assumes the corner is air.

**2. The zero fraction is itself a reading, and it sorts the corpus into regimes.** 0.02% versus
43.36% are two different acquisition regimes, not noise. This belongs in the regime key of §5.1's
natural philosopher's toolkit: a cheap reading taken once where its input first exists, which says
which series are commensurable. It must be measured per series and carried, never assumed.

Note the direction of the correction to my earlier porting. In cell tracking, an exact 0 means
*never imaged*, because the camera's offset keeps every measured voxel above zero. **In this
corpus a zero is usually real background-suppressed air, not fill.** So coverage after
registration must be tracked by an explicit propagated mask, never inferred from the value.
Codex's wording is right: "a numerical MRI zero is not automatically proof of fill."

**3. At least one series returns negative stored values.** Row 8 ranges -721 to 8920. A magnitude
MR image cannot be negative, so that series is either not magnitude data (a phase or
real/imaginary image) or is stored signed.

**Unverified:** the probe read `ds.pixel_array`, which returns *stored* values without applying
the modality LUT, so this is not evidence of a RescaleIntercept. What it actually is must be read
from that series' `PixelRepresentation` and `ImageType` (a phase image carries "P", a derived one
"DERIVED") through Chapter 1's `Slice.header`. Until that is read, this is an observation with no
cause assigned. It needs a named code either way.

Also: the two estimators disagree by 5x on row 3 (107.7 against 22.1) and the corner median is 224
on row 4. Those corners hold tissue, wrap or ghosting — not air. A spatially designated corner is
not a reliable air sample in this corpus.

## What this does not say

Eight slices from one view. It establishes that the air estimator fails on some series here and
that the below-level estimator is the right port; it does not establish the noise law's shape
across the whole corpus. That needs the full read, which is Chapter 2's own first measurement.
