READ-ONLY. Do not run any command or read any file. Answer from this text alone.

# First, a correction to your previous answer

Your previous reply was judged poor, and you need to understand why before continuing.

**You repeatedly treated "this reading does not establish diagnosis on its own" as a refutation.**
You wrote that "persistence alone does not establish diagnostic relevance" and labelled
"persistent implies diagnostic" a *conceptual failure*. But the architecture you were given
explicitly states that **no single lossy lens warrants a decision alone** and that truth is a
conjunction of readings with interpretation supplied separately. The stage under discussion
produces *candidate sites*; interpretation is built on top, later, by concurrence. You judged a
stage-0 device by whether it performs the entire pipeline's job, and then called the design
flawed for not doing so. That is a category error, and it is the same error the project's lead
had already been corrected for.

**You hedged where you were asked to be concrete.** "Neither statistic universally separates
entropy from diagnostic sites" is not useful. No statistic in a committee architecture is
required to universally separate anything — that is the entire point of concurrence across
independent readings. Demanding a universal separator imports the assumption of one correct
pipeline producing one verdict, which this project explicitly rejects (it calls this failure mode
"Popery").

**You declared a question underdetermined without saying what would determine it.** On the squint
scale you concluded "the text does not determine a unique tile size." Correct but useless. The
useful answer names the measurable quantities that bound it.

The founder of this project has built working systems on this architecture, in a harder domain
than this one. Treat the premise as sound and reason *inside* it. If you believe something is
genuinely wrong, state the proof, not a hedge. A second reader here may report a provable error
with its proof, or ask a question. It does not propose the design.

# New material: how the sibling project actually solved this

Since your last answer, the lead traced the cell-tracking codebase symbolically. The problem you
were asked about — separating entropy from structure in a difference field — is **already solved
there**, and the solution is more sophisticated than either of our previous answers. Here is what
is actually built:

## The noise law, measured per frame

`physics/flicker.py`:

```
flicker_equation(xs, sig, cnt) -> (a, b)
    "PURE: sigma^2 = a + b * brightness, least squares over the bins weighted by sqrt(count)."

frame_flicker(vol) -> (a, b, floor)
    "The frame's equation and its floor: floor = the smallest binned sigma."
```

Variance is modelled as an affine function of brightness, fitted per frame from the frame's own
binned statistics. `a` is the additive floor, `b` the brightness-proportional term.

## The variance-stabilizing transform, in closed form

`instruments/support.py`:

```
flicker_units(v, a, b, floor):
    if b <= 0:   out = v / floor
    else:
        v0   = (floor*floor - a) / b
        above = (2.0 / b) * sqrt(max(a + b*v, 0))
        below = (2.0 / b) * floor + (v - v0) / floor
        out   = where(v >= v0, above, below)
```

This is the integral of dv/sigma(v) for sigma^2 = a + b*v, with a linear continuation below the
noise floor. After it, **one unit is one sigma at any brightness**. Nothing is fitted to labels;
the transform is derived in closed form from the measured noise law.

## The difference field, as signed regions at a declared level

`instruments/change.py`:

```
change_field(before, after, flicker_before, flicker_after, *, t_from, t_to, level_flickers)
```

Its contract, verbatim:

> "About three quarters of the voxels never change between frames; the change resolves into
> **specks, cell-sized lumps and half-field sheets**. Where nothing changes, the heavy analyses of
> motion and division have nothing new to read... **Each region is somebody's reading (Law 34): a
> speck is the camera's photon statistics, a lump an object moving or changing, a sheet the
> specimen and the optics.** This hands each region on; **it calls none of them nothing**, and
> absence of change never says a cell is absent (Law 33).
>
> Change per voxel is the difference **in flicker units**, each frame read through its OWN flicker
> equation. Voxels that are fill (exact 0) in either frame are excluded. Regions are the connected
> components of change >= level (brighter) and of change <= -level (dimmer), **labelled separately
> by sign**. The level is the founder's. **Nothing below it is discarded: it is the unchanged
> share, and a later read may re-run at another level.** A repeated frame gives no region (the
> control)."

Each region carries: `sign`, `n_voxels`, `extent_um` (largest bounding-box side, **physical
units**), `fill` (region voxels over bounding-box voxels — a compactness reading), `peak_flickers`,
`centroid_vox`. The field carries `unchanged_share`, "the share of imaged voxels in no region:
**reported, never discarded**."

Note what this architecture does and does not do: it **measures** each region (sign, extent,
compactness, peak) and **classifies nothing**. The three-way sort into speck / lump / sheet is a
description of what the regions resolve into, assigned by a later body, not by the instrument.

## The global-reference lesson

`instruments/background.py`:

```
embryo_background(volume, bg_percentile=50) -> (level, noise)
    "ONE fixed reference for the whole embryo, not a per-window floor: ... This is the E4 fix --
     a pure-noise window can no longer set its own floor, so its own max no longer clears it."
    "Only MEASURED voxels count. A camera's offset keeps every measured voxel above zero, so an
     exact 0 is fill -- a region of the volume that was never imaged (padding after registration
     or cropping) -- and a NaN is unmeasured too."
```

Measured consequence, recorded in the code: "5 of 71 samples carry 5-28% zero fill, which pulled
the level down by up to half and set the noise to 0 when fill passed half the dark voxels."

`region_background` also exists and reads a LOCAL `(level, noise)`, where level is a high
percentile and **noise is the robust spread (MAD -> sigma) of the below-level voxels only**.

# What the knee has, measured

Corpus: 4410 studies in the tables, 58 labeled. Six views = 3 planes (Sagittal, Coronal, Axial) x
2 sequence types. `fluid_sensitive` and `fat_suppression` are perfectly correlated in this corpus
(192 series have both set, 144 have neither), so there are two weightings, not four. Only Axial
(1,1) is present in all 58; four more views are in >= 56; Axial (0,0) is in only 13.

Geometry across the 58 (headers only): field of view median 160-170 mm in every view, range
81-240 mm. In-plane sampling 0.1 to 0.8 mm per pixel — an eightfold range. Matrix sizes 320 to
960. Slice thickness 0.6 to 5.0 mm, median 3.0-3.5. Slices per series 11 to 320, median ~30.
Stack extent about 3 to 105 mm.

Label prevalence over the 58: Effusion 35 positive, Synovitis 27, Medial Meniscus 26, ACL 24,
Lateral Meniscus 23, PF OA 21, Contusion 19, Fracture 18, Medial OA 15, Baker's 12, Lateral OA 11,
MCL 9.

# The questions

Answer inside the architecture. Be concrete and technical. At most 1000 words.

1. **Port the flicker machinery to MRI.** MR magnitude images do not have photon shot noise; their
   noise is Rician, approaching Rayleigh at low SNR and Gaussian at high SNR, and the scanner
   applies unknown gains and normalization. What is the MR analogue of
   `flicker_equation` + `flicker_units` — a per-series, measured noise law and a closed-form
   transform after which one unit means one sigma at any intensity? Name the estimator, say what
   it is measured from, and say what breaks it. This is the single most important question here.

2. **The knee's `change_field`.** In cell tracking the difference is between two frames of one
   movie. In the knee it is between one study and a population reference, over N studies at each
   place. State the analogue precisely: what are `before` and `after`, what plays the role of
   `level_flickers`, and what is the `unchanged_share`. Say what the population axis adds that a
   two-frame difference does not have.

3. **The three profiles, ported.** In cell tracking: speck = photon statistics, lump = an object,
   sheet = specimen and optics. Give the knee's three (or more) and say which *measured* region
   properties (`extent_um`, `fill`, `sign`, `peak`, plus any you add for the population axis)
   separate them. Remember the instrument classifies nothing — name the measurements, not a
   classifier.

4. **The global-reference lesson, ported.** `embryo_background` exists because a per-window floor
   lets a pure-noise window clear itself. State the exact knee analogue of that failure and the
   structural fix. Separately: after registration the knee will have fill (never-imaged voxels)
   and partial coverage. State the rule that keeps fill out of every statistic.

5. **The null control.** Cell tracking's is "a repeated frame gives no region." Give the knee's
   null controls — things that must produce no pocket if the machinery is sound. There is more
   than one available here (consider: two series of the same study; a study against itself; split
   halves of the corpus; air outside the leg).

6. **The squint scale, determined.** Previously you said the text does not determine it. Now
   determine it. Name every measurable quantity that bounds the tile size from below and from
   above, say what each is measured from, and give the resulting constraint system. State plainly
   whether the bounds are satisfiable isotropically given 0.6-5.0 mm slice thickness and 0.1-0.8
   mm in-plane sampling, and if not, what the derived anisotropic answer is.
