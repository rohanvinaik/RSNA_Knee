# The two objects — the lead's reading, written before consulting

2026-10-10. Written before opening Fable's or Codex's answer, per the loop.

## What the founder redirected to

The knee is **two objects that combine**. The field splits into the femur and the tibia. An injury
is a reasoned deviation in how they sit in one another. Resolve the femur, resolve the tibia,
resolve the joint space between them — structurally and deterministically — and diagnosis becomes
reasoning over the relation.

And the mechanism already exists: "the 'dome' shape, with a discrete fall-off in signal intensity
that marks the border between the edge of the cell membrane and the rest of the field... That could
resolve between HUNDREDS of cells in a single plate. Here? We just need to figure out the
difference between two GIANT fucking objects."

## The mechanism as built, traced

`instruments/support.py::read_dips` — the whole thing, in order:

1. **Local maxima** of the window become markers: `ndimage.label(local_maxima(v, connectivity=1))`
2. **Watershed on the NEGATED image** gives every peak its basin: `watershed(-v, markers=markers)`.
   A basin is the territory one bright centre holds — the dome as territory.
3. **The saddle** between two basins is read: `_saddle(v, basins, own_label, label)`.
4. **The dip's depth** is how far that saddle falls below the lower of the two peaks:

   `seam_depth_flickers(peak_a, peak_b, saddle) = min(peak_a, peak_b) - saddle`

   "PURE: how far the seam dips below the lower of two peaks, **in flickers**."

5. A `Dip` carries `direction_um`, `distance_um`, `peak_counts`, `depth_counts`, and
   **`depth_flickers`**.

**So the criterion for "two objects rather than one" is the depth of the seam between their peaks,
measured in units of the noise.** That is the discrete fall-off. Nothing about absolute brightness;
everything about how far the valley between two centres drops, in sigmas.

This is why the variance-stabilizing transform matters: a dip depth is only meaningful in noise
units, and the transform is what makes one unit mean one sigma at any intensity.

## The port, as the lead reads it

| cell tracking | the knee |
|---|---|
| hundreds of nuclei on a plate | **two** bones, plus the patella in some views |
| N unknown, discovered | **N is given by anatomy** — "the identity of the thing being imaged... has to be told to us" |
| a nucleus's peak | the marrow of the femur, the marrow of the tibia |
| the seam between two touching nuclei | **the joint line** — "the GIANT fucking gap between them" |
| the dip's depth in flickers decides | the same, and it should be enormous rather than marginal |

So the knee is the sibling's problem with N given and the seam made huge. The founder: "Compared to
cell tracking, it's child's play."

## Two things the lead got wrong, and why

**1. The gestalt prior is not applied.** Air is found by connectivity to the frame's border, which
works cleanly. But the black *enclosed* by the leg's boundary is not filled, so it is still counted
as leg. The thesis's own stage 2 "reasons from the gestalt of an <object>: **contiguous, closed**"
(§5.3), and §4.5 names "the gestalt, **the contiguous, closed whole**". Closure is the missing
step: fill the holes, then the leg is a body and not an outline.

**2. The direction was assumed, not read.** The lead's "darkest band down the centre" profile
failed, landing on image edges. One cause: it assumed image rows run superior-to-inferior, and the
rendered frames are visibly **rotated**. The direction is not in the pixels — the founder: "the
direction we're looking (down-->up or up-->down) **has to be told to us**."

It is in the header, and Chapter 1 already reads it: `SeriesGeometry.orientation` holds each
slice's row and column direction cosines, and `normal` the slice normal, all in DICOM LPS where
**superior is +Z**. So the in-plane axis with the largest Z cosine is the vertical, and its sign
says which end is up. In an axial series the superior-inferior axis is the stack normal, which is
why an axial view shows no joint line: it cuts across the relation rather than along it.

**The femur is superior, the tibia inferior.** That is an anatomical law, and once the axis is read
from the header it assigns the two basins their names without any measurement.

## What the lead believes the build is

1. **Close the leg.** Air by connectivity to the border, then fill the enclosed holes. The leg
   becomes a contiguous, closed body.
2. **Read the superior-inferior axis from the header**, never from the pixels.
3. **Find the two basins.** Watershed the negated squinted image inside the leg; take the two
   largest basins straddling the axis.
4. **Read the seam** between them: its depth in noise units, its position along the axis, its
   extent across the leg.
5. **Name them by the axis**: superior basin is the femur, inferior is the tibia.
6. The seam IS the joint line — the founder's normalization flag — and it is found as a
   *relation between two objects*, not as a dark band hunted by intensity.

## What the lead is uncertain about

- **The polarity flips between weightings.** On the anatomy sequence the marrow is bright and the
  seam is dark, so the watershed runs on the image as-is. On fluid-sensitive the marrow is mid and
  the joint space is *bright*, so the seam is a *ridge*, not a valley. Whether the dome on one
  weighting is the dip on the other is a thing to check, not assert.
- **The patella** is a third object in sagittal and axial views and must not be mistaken for one of
  the two.
- **"The lateral view is of the space between them"** — the founder's phrase is ambiguous to the
  lead, and if which view carries the joint space matters to the build it is a question for him
  rather than something to interpret.

## A claim the lead must withdraw

Earlier it was stated that "there is no background noise in this corpus to measure." **That came
from three series.** The 336-series run reported 18.8% `background_masked`, not 100%, and an
earlier 8-series probe found non-zero air in several (corner medians of 26, 224, 123). The correct
statement is that **the three series rendered had air that was nearly all zeros**, and the
corpus-wide air distribution has not been measured.
