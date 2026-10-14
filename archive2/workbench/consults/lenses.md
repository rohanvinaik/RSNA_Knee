# Consult: building `knee.lenses` — the tissue fingerprint as the thesis's bundle (2026-10-11)

READ-ONLY. Do not run any command and do not read any file. Answer from this text alone.

## The frame, which you must not reframe

Classical-AI, **no machine learning**: no CNN, no transformer, no fitted weight, no learned
embedding, no "small learned component". That is the thesis, not a constraint to optimise around.
RSNA Knee Abnormality Detection, 12 binary findings per knee MRI study, macro ROC-AUC.

Laws that bind any answer: **decide or abstain, and unknown is never false**; a missing reading is
**silence**, never a negative; truth is assigned by **concurrence** among independent measurements;
**no level is ever chosen to separate the gold labels**; and **a bar a decision reads is an argument,
never a constant inside it**.

## Where the build stands

Settled and built:
- studies read whole at stored fidelity; a per-series regime key of cheap whole-field readings.
- a **noise law**: background split by the histogram valley, channel count from a quartile ratio,
  dark and bright sigma; and a **Rician variance-stabilising transform** so one "flicker" unit is one
  sigma at any intensity (measured spread 0.886 / 0.995 / 1.063 / 1.002 / 0.999 at 0 / 1 / 2 / 5 /
  25 sigma).
- a physical frame in DICOM LPS patient coordinates; physical squints; native bilinear profiles with
  a reference and an exact Numba twin admitted only by a decision-preserving SAME harness.
- **objects (B1)**: territories per slice as `watershed(-EDT(interior), h_maxima(EDT, prominence))`.
  This is the thesis's "dome" re-derived: a cell is brightest at its centre because it emits, a bone
  is a solid bounded by dark cortex so it is **deepest** at its centre, and the distance transform
  replaces brightness as the dome's height field. Prominence, never a level, so "nothing is cut on
  strength".
- **conversation (B2)**: two series of the SAME orientation read the same knee, so one's bounded dark
  band is transported into the other's frame **by sampling along normals at points**, not by
  resampling volumes, and the recipient's own native plane is read at the same place. Eleven named
  outcomes; agreement bars, silence may bar conditionally, contradiction never bars.

Architecture settled with the founder: **a finding is a predicate violation on an object, or on a
relation between objects.** An interstice is *constructed* from facing objects, never detected.

## What `lenses` must be

From the thesis's figures (H2a2, H2b), which the founder supplied. A `<object>`'s **bundle** crosses
**scale** (the voxel · a 16×16 neighbourhood · the lens · the plate) with **lens** (Gradient ·
Contrast · Split Quality · Dark Share · Composite), plus relational banks (the dome link's eight
compass directions, the ring) and **provenance banks** (the lenses' conversation, *how its cell came
out*, its own voxels). Every row is one **balanced-ternary digit against a STATIC MIDDLE** — below /
at / above — shaded by how many of the object's places wrote it. A digit of 0 is "**a reading at its
middle, not silence**"; a row no place writes is a different thing entirely.

For the knee the **lens axis is the acquisitions**: T1, T2, PD, fat-suppressed and not, of the same
knee. A tissue class is a **conjunction of rows**, never a threshold on one image:

    fat        bright(non-FS) and dark(FS)
    fluid      bright(FS) and bright(T2 non-FS) and dark(T1)
    dark-on-everything    cortex, tendon, ligament, meniscus
    cartilage             intermediate: always below fluid, always above meniscus
    muscle                intermediate(T1), intermediate-dark(T2, FS)
    marrow edema          dark(T1) and bright(FS), inside a bone

This matters because **four intensity instruments already died on this corpus** — a quantile, Otsu,
the histogram valley, and the darkest-fifth-inside-the-leg. Each failed because an absolute level
cannot survive scanner scaling. A reading stated against witnesses in the same image can.

## My own design, written before asking you

1. **The middle is per series, never per corpus**, because intensity scaling differs between
   acquisitions and the whole point is comparability within one knee.

2. **The in-image references are found STRUCTURALLY, not by intensity** — otherwise it is circular
   (you need fat to calibrate, but finding fat needs calibration). My proposal: subcutaneous fat is a
   *position* — the band just inside the leg boundary, and the leg boundary is already resolved by
   air-connectivity-to-the-frame-border, which works cleanly on this corpus. Muscle is the bulk of
   non-bone soft tissue by volume. A distended recess, when present, is the fluid witness.

3. **The ternary band comes from the noise law, not from a tuned threshold.** A place reads "at the
   middle" when it is within its own measurement's noise of the middle — in flicker units, where one
   flicker is one sigma — so the band is `±k` flickers with `k` a recorded argument. Nothing is
   fitted; the width is the instrument's own resolution.

4. **No resampling of volumes.** I would follow B2's existing discipline: sample point-wise along the
   physical frame at the places a reading is wanted, rather than interpolating whole volumes into a
   common grid. Interpolating a volume to make a conjunction possible would mean deciding on
   interpolated values.

5. **A missing acquisition writes NO ROW**, rather than a 0 digit. The figure distinguishes "a row no
   place writes" from "at its middle", and collapsing them would turn an absent instrument into a
   measured middle.

6. **Measurements only.** `lenses` decides nothing: it owes one digit per row per place with its
   support, and silence where a place was not read.

## What I am asking you

Be concrete. A general caution is worth nothing here.

1. **Is point-wise sampling the right call, or does the conjunction genuinely need a common grid?**
   Two series of different orientation sample different physical planes; a "place" in one may fall
   between slices in another. What is the deterministic, non-interpolating way to state a conjunction
   across acquisitions — or is some interpolation unavoidable, and if so where should it be confined?
2. **Attack my structural bootstrap for the references.** Where does "subcutaneous fat is the band
   just inside the leg boundary" fail on a real knee MRI, and what is a better structural witness?
3. **The ternary band.** Is `±k` flickers around a per-series middle the right construction? What
   sets the middle itself — a median over what population of places?
4. **The row layout.** Which scales and which readings should the knee's banks actually carry? The
   sibling used Gradient, Contrast, Split Quality, Dark Share, Composite across voxel / neighbourhood
   / lens / plate. What is the knee's correct analogue, given that its lens axis is acquisitions?
5. **Where does this break?** Name the specific case where a conjunction across acquisitions gives a
   wrong tissue class with high confidence, and say why.
6. **Compute shape.** This runs over 58 studies now and a hidden test set inside a 9-hour Kaggle
   kernel with internet off. Which parts are NumPy-vectorizable, which want a Numba kernel, and which
   (if any) justify C or Rust? Where is the cache/memoisation boundary — what is worth computing once
   and reusing, and keyed on what?
7. **What am I not asking that I should be?**

Answer in prose with headed sections. Distinguish what you know from what you are inferring, and say
plainly where you are uncertain.
