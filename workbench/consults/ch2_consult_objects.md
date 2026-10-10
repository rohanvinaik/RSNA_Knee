READ-ONLY. Do not run any command or read any file. Answer from this text alone.

# Standing context

A **classical-AI, no-machine-learning** system for RSNA Knee Abnormality Detection: 12 binary
findings per knee MRI study. No model, no fitted weight, no learned embedding, no segmentation
network. If your answer contains one it is wrong. The founder has built working systems this way in
a harder domain.

The lead spent a long stretch tuning histogram statistics to separate "background" from "tissue",
tried four intensity instruments, and failed with all four:

1. a **quantile** (lowest fifth by value) — truncates the population, so its moments stop being the
   noise's;
2. **Otsu** — maximises between-class variance, which sits at the valley only when the two modes
   carry comparable mass; a knee's background is a narrow spike against broad tissue, so it lands
   far above the valley;
3. the **histogram valley** (first local minimum after the first peak) — exact on synthetic bimodal
   data, erratic on real knees whose histograms carry several tissue modes;
4. the **darkest fifth inside the leg**, meant to find cortical bone — found the leg's left and
   right edges instead.

The founder then redirected, and the redirect is the whole point of this consult.

# The founder's words, verbatim

> "structure isn't something you can blindly apply. It has to be re-derived for each problem space.
> For here, you're missing a BIG one: **Knees are two objects that combine.** The problem space is
> to split the visual field into "<object>"s--the tibia and the femur"

> "Knee injuries aren't some arbitrary thing, they are reasoned deviations from the norm of how
> knees are supposed to work. A tibia and a femur sit into one another, with [synovial] fluid
> between them. An injury is a breakage, an issue in the way they sit in one another. **What we
> need to do is resolve what is the tibia, resolve what is the femur, resolve what is the
> interstitial space, and have it be a structural and deterministic resolution. Then, diagnosis is
> a matter of reasoning over the dynamics between them and how these objects sit relative to each
> other**"

> "The answer here, what makes these two objects, is, again, SUPER obvious. The lateral view is of
> the space between them, where synovial fluid sits. **The identity of the thing being imaged, the
> direction we're looking (down-->up or up-->down) has to be told to us.** But for any images that
> are vertical, it's laughably simple"

> "The difference between tibia and femur? **It's the GIANT fucking gap between them.** Look into
> the cell tracking project for the way we resolved cells, the **"dome" shape, with a discrete
> fall-off in signal intensity that marks the border** between the edge of the cell membrane and
> the rest of the field. THat was WAAAAAY harder. That could resolve between HUNDREDS of cells in a
> single plate. Here? We just need to figure out the difference between **two GIANT fucking objects
> that almost precisely split the picture right in the middle. It's always in roughly the same
> place, and almost looks the exact same.** Compared to cell tracking, it's child's play."

> "the "background" resolution here is REALLY good... VERY clean. In the images, we can see that
> some of the views are able to draw the boundary around the black, but **we're not using the
> obvious gestalt priors that "fill in" the middle** and resolve that as background as well."

> "The objects are hard to reason over with numbers. But **computer vision is about reasoning over
> *objects*.**"

# The sibling mechanism, traced from its code

`instruments/support.py::read_dips`, in order:

1. **Local maxima** become markers: `ndimage.label(local_maxima(v, connectivity=1))`
2. **Watershed on the NEGATED image**: `watershed(-v, markers=markers)`. A basin is the territory
   one bright centre holds.
3. **The saddle** between two basins: `_saddle(v, basins, own_label, other_label)`
4. **The dip's depth**:
   `seam_depth_flickers(peak_a, peak_b, saddle) = min(peak_a, peak_b) - saddle`,
   documented as "how far the seam dips below the lower of two peaks, **in flickers**"
5. A `Dip` carries direction, distance, the other peak's counts, depth in counts, and **depth in
   flickers**.

So the criterion for "two objects rather than one" is **the depth of the seam between their peaks,
measured in units of the noise**. Not absolute brightness. The thesis also states that stage 2
"reasons from the gestalt of an <object>: **contiguous, closed**".

# What the rendered images show

- **Air by connectivity to the frame's border** works cleanly, about 10-11% of the frame, tracing
  the leg's contour. The enclosed black inside the leg is NOT yet filled.
- **The squint keeps the knee legible** at 8x8 tile medians — femur, tibia, patella and the joint
  space all readable.
- **The polarity flips between weightings.** On the anatomy sequence (not fluid-sensitive) the
  marrow is BRIGHT and the joint line is a DARK band. On the fluid-sensitive sequence the marrow is
  mid-grey and the joint space is BRIGHT. Same structure, opposite sign.
- The frames are **visibly rotated** — image rows are not guaranteed to run superior-to-inferior.
- Chapter 1 already reads DICOM geometry: per-slice row and column direction cosines, and the slice
  normal, in LPS where **superior is +Z**.

# The lead's reading, for you to check

1. **Close the leg**: air by connectivity to the border, then fill enclosed holes, so the leg is a
   contiguous closed body rather than an outline.
2. **Read the superior-inferior axis from the header**, never from the pixels.
3. **Find two basins**: watershed the negated squinted image inside the leg, take the two largest
   straddling that axis.
4. **Read the seam** between them — depth in noise units, position along the axis, extent across
   the leg.
5. **Name them by the axis**: superior basin is the femur, inferior is the tibia.
6. The seam IS the joint line, found as a *relation between two objects* rather than as a dark band
   hunted by intensity.

# The questions

At most 1000 words. Concrete, inside this epistemology. No learned component anywhere.

1. **Is the lead's reading right?** Correct it where it is wrong. In particular: is watershed on
   the negated image the right port, or is the knee's case different enough that the basin is the
   wrong object?

2. **The polarity flip.** On the anatomy weighting the bones are bright and the seam is a dark
   valley, so a watershed on the negated image finds them. On the fluid-sensitive weighting the
   joint space is BRIGHT — so the seam is a *ridge*, not a valley. Does the same machinery run with
   the sign flipped, or does the fluid-sensitive weighting need a different reading entirely? State
   plainly which, and what decides.

3. **N = 2 is given.** The sibling discovers how many objects there are; here anatomy supplies it,
   plus the patella in sagittal and axial views. What does knowing N in advance let the method do
   that it could not otherwise, and what must it still abstain on?

4. **The gestalt closure.** "Fill in the middle" — what exactly is the operation, and what is the
   rule for which enclosed dark is background and which is a real dark structure inside the leg
   (cortical bone is signal-void on every sequence, so the bone's own outline is dark too)? This
   must not swallow real anatomy.

5. **What reading makes the seam a MEASUREMENT rather than a threshold?** The seam's depth in noise
   units is one. What else about the relation between two bones is directly measurable and
   label-free — things that would later let a deviation be read? Think about what the relation
   itself has: separation, parallelism, congruence of the two facing surfaces, where along the axis
   the seam sits, whether it is one seam or several.

6. **What breaks it.** Name the failure modes specific to this port: a knee in flexion, a frame
   rotated, the patella, a severe effusion filling the joint space, a bone with a fracture through
   it, an axial view that cuts across the relation rather than along it.
