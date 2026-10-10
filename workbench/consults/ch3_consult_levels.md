READ-ONLY. Do not run any command or read any file. Answer from this text alone.

# Standing context

A **classical-AI, no-machine-learning** system for RSNA Knee Abnormality Detection: 12 binary
findings per knee MRI study, macro-averaged ROC-AUC. No model, no fitted weight, no learned
embedding. If your answer contains one it is wrong.

Already built and committed:
- **Stage 1, the noise law.** Per series, `(sigma_g, coils)`, read two independent ways that must
  concur — a dark estimator over the quiet population taken wherever it lies (never a designated
  corner), and a bright estimator from pseudo-residuals that never touches the background.
  Disagreement is a named code, never a refit. Justified by measurement: 62 of this corpus's 336
  series are over 20% zeros, where an air-based estimator has no air.
- **Stage 2, the variance-stabilizing transform.** The integral of dv/sigma(v) for the Rician /
  noncentral-chi family, tabulated per series. Measured quality: within 0.5% above 5 sigma, within
  7% through the transition, and **11% low at pure noise** (the delta method's limit).

# The problem stage 3 was supposed to solve

Flicker units cancel **gain** but not **SNR**. Coil, field strength, bandwidth, averages and voxel
size all change tissue contrast without changing the noise scale, so two series of one knee can be
noise-commensurable and sit at different levels. Uncorrected, that is a whole-field sheet in the
residual.

The obvious fix is intensity standardization by histogram landmarks (Nyúl-Udupa): map percentiles
of each series' foreground onto a common scale. **It has a fatal problem here.** The foreground
histogram moves when there is pathology. A knee with a large effusion has more bright fluid, so its
upper percentiles shift, so the map partly normalizes away the thing being detected. And it is
worst exactly where it hurts: **on a fluid-sensitive sequence the brightest tissue IS fluid**,
which is effusion, Baker's cyst and oedema — three of the twelve.

The founder's response was that this cannot be a blocker, because the sibling project solved the
homologous problem: a **confluent** microscopy plate has far more total fluorescent signal than a
**sparse** one, which is the same global scale-up.

# What the sibling build actually does — read from its code, verbatim

**1. A place's value is read above a measured level, in noise units.**
`cassette/instrument.py::light_above(brightness, level, curve)`:

> "Each place's light above a level, **in noise units**: its brightness in noise units less the
> level's (`noise_units` on each, the level read as 0 where it is NaN).
>
> `level` is one number (the dark) or a field of the brightness's shape (a slice's haze); `curve`
> the camera's (a, b, floor). **Graded, never cut: a place below the level reads a negative
> number.** A place never imaged (an exact 0) reads NaN, as does a place whose level was not read
> (NaN) and every place under a curve not measured."

**2. The value is then reduced to a balanced-ternary digit against a reference band.**
`cassette/layout.py::digit_of(value, middle)`:

> "PURE: ``value``'s balanced-ternary digit against its ``middle`` (low, high): **-1 below low, 0
> from low to high (both edges at the middle), +1 above high**; None for a value not read (None or
> NaN)."

The bands are held in a versioned table (`Middles`: "a name saying what they were read from", and
"for each (bank name, metric name), its (low, high) edges"). A provisional test table builds each
middle as that metric's **terciles**, the 1/3 and 2/3 quantiles.

**3. Density is kept as an exact token, not divided out.**
`substrate/compose/facets.py::regime_facet(regime)`:

> "The `regime` bank facet: an **exact token for the embryo density regime** (`sparse` / `dense`).
> Unknown regime -> `KeyError`."

And the thesis's §5.1, on readings taken once for the whole movie:

> "The readings of the whole field, taken once for the movie, are the **priors**: its **density**,
> its distribution (even, spiky or one-sided), its profile down the depth, and whether and how the
> plate drifts. Their words form the **regime key** under which a case from this field is kept."

**4. No bright anchor appears anywhere.** Nothing in the chain anchors on the brightest signal or
on a high percentile. The scale is anchored only on the dark/quiet end.

**5. The regime key is built from CHEAP GLOBAL readings of the whole field.** The thesis, §5.1,
calls these "the natural philosopher's toolkit":

> "Beside them stand cheap readings... Each is made once, in milliseconds, where its input first
> exists, and is kept for any stage to consult. **These readings point, and never decide alone.** A
> coarse view of the whole field is itself a squint: **it settles whether a plate is dense or
> sparse**, still or moving, more cleanly and more cheaply than a fine one. It narrows where the
> expensive work runs...
>
> The readings of the whole field, taken once for the movie, are the **priors**: its **density**,
> its **distribution** (even, spiky or one-sided), its **profile down the depth**, and whether and
> how the plate **drifts**. Their words form the **regime key** under which a case from this field
> is kept."

The founder's steer, which is why this section is quoted here: the global level and composition
are handled by exactly these **cheap, whole-field metrics** — measured once, named, and used to
condition which cases are comparable. They are not divided out of the signal.

**Still open, being read now:** whether the middles' (low, high) edges are read **per movie** or
from a **corpus reference**. Per-movie edges cancel a global gain change; corpus edges do not.
Answer for both branches where it matters.

# The distinction that matters

A consultant reading of this flagged, correctly, that **gain and composition are different**:

- A **gain** change scales every value together. If the middle is read from the same series, the
  middle scales with it, so the digit is invariant.
- A **composition** change alters the mix of what is in the field — more cells, or a large effusion
  — which moves a quantile even with gain fixed.

The sibling carries a density regime token, which suggests the digit did NOT absorb confluence and
the regime is the composition mechanism.

# The questions

At most 1000 words, concrete, inside this epistemology.

1. **Port the chain.** State the knee's version of "raw value -> above a measured level, in noise
   units -> ternary digit against a middle". What is the knee's analogue of the dark, and of the
   haze (the local level field)? Note stage 1 already measures a per-series quiet level and
   sigma_g, label-free, which an effusion does not touch.

2. **Does this actually dispose of the level problem, and exactly which part?** Separate the three:
   (a) scanner/coil **gain**; (b) **SNR** differences between acquisitions; (c) **compositional**
   change from a large effusion. Say for each whether the chain handles it, and by which step. Be
   precise about what is NOT handled.

3. **The knee's regime key.** If composition is handled by a regime token rather than by
   normalization, what are the knee's regimes, and what is read to assign one? They must be
   **label-free** and measurable per series. What would a knee's "sparse / dense" be?

4. **Terciles versus tail.** Is a mid-quantile band (1/3, 2/3) materially more robust to a local
   bright finding than Nyúl-Udupa's upper landmarks, or is that wishful? Quantify roughly: for a
   finding occupying a given fraction of the foreground at a given brightness, how far does a
   tercile move versus a 95th percentile? State the condition under which the tercile band is safe.

5. **Is stage 3 the wrong frame entirely?** If the chain above is right, there may be no "level
   map" in this design at all — the level is dealt with by reading above a measured dark in noise
   units and then quantizing against a per-series band. Say plainly whether stage 3 should be
   reframed, and if so, into what.

6. **What breaks it.** Name the specific failure modes of this chain in MRI that do not arise in
   microscopy, and say for each whether it is an engineering problem or a conceptual one.
