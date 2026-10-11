**Role note:** I read only your text. Where I say "provable," I mean it follows from the stated rules alone.

---

## (1) Internal consistency, and what is missing

**Mostly consistent, with one definitional gap that currently makes the subdivision not well-defined, and two derived values that are presented more strongly than the rules allow.**

**The gap: "supported transported boundary segments" is undefined, and the two candidate definitions give different subdivisions.**
Your increment produces three classes of transported segment: concurrent (recipient re-read also dark, intervals intersect), donor-only (recipient fully available, no dark run), and disputed/disjoint (recipient dark but not intersecting). The raster step says "supported" segments become barriers. Either:

- (a) supported = concurrent only — then donor-only constraints never partition the recipient's interior, and the subdivision measures only what both readings agree on; or
- (b) supported = any transported segment whose re-read was fully available — then a donor-only segment cuts the recipient's interior where the recipient itself read *no* border.

Under your founder's own premise ("confident resolution of background is itself informational"), the recipient's "fully available, no dark run" is a reading, not an absence. So (b) is not "conditioning on donor evidence"; it is cutting one measurement's territory along a line that measurement actively contradicts. That is a dissent, and your theory says dissent is retained, not acted on silently. (b) is only consistent if every piece carries, per bounding barrier, the label "cut by donor-only barrier over recipient non-dark reading," and if you also run (a) and keep both labelings. Without choosing, the subdivision is undefined. **This is the missing premise.** My reading is that your stated intent ("connectivity under stated donor constraints, not ownership") is (b) with full provenance, but it must be written down, and it should be acknowledged that under (b) the pieces are a function of the barrier set, so piece identities are not comparable across different barrier sets without recording the set.

**Provable error 1: the midpoint of an intersection is not a refined measurement.**
Intersecting two runs gives a narrower interval, legitimately. But its midpoint has no scope of its own: it is not the midpoint of either original, it shifts with the wider interval's endpoint, and if the two runs merely touch, the intersection is a single sample and the "refined trace" acquires spurious exactness. The rules only license: intersection interval, intersection width, and the two originals. A midpoint may be recorded as a derived convenience, but it must not be re-read, re-transported, or used as a barrier centreline with precision tighter than the intersection width. (Also, "no recursively borrowed evidence" is violated if a concurrent intersection from pair A→B is later transported into C as if it were B's own reading.)

**Provable error 2: a raster subdivision with undeclared connectivity is not a single result.**
A thin segment rasterized into a grid partitions the interior differently under 4- versus 8-connected labeling, and under thin (Bresenham-style) versus supercover barrier rasterization; diagonal leaks are a known consequence of mismatched choices. Two transported segments that cross can also close an accidental cell that no single measurement bounds. Since your subdivision is explicitly a measurement, the connectivity rule, barrier rasterization rule, and whether a barrier is rendered as the whole band or its centreline are part of the measurement definition and must be fixed and recorded.

**Unstated assumption:** "same scan of the same knee" gives a shared patient coordinate frame; it does not give coincident physical sampling. Inter-sequence motion and per-sequence geometric distortion (including chemical shift along readout) are real and sequence-specific. The increment is consistent only as a *test* of that assumption, with disjoint bands being its expected failure signature — not as something that presupposes it.

---

## (2) Plane correspondence without a depth-nearness identity test

Do not ask "are these the same plane?" Ask, per transported sample point, "does the recipient's own acquisition cover this point?" — a coverage question answered from the recipient's geometry, with no tunable similarity threshold.

Record for every transported sample: signed off-plane distance **d** to the nearest recipient sampled plane, the recipient's slab half-thickness **h**, slice spacing **s**, and the angle between donor and recipient normals. Then:

- **|d| ≤ ε_round**: coincident up to header rounding. ε_round is *derived* (half a unit in the last stated decimal of the header origin/spacing, propagated), not chosen. Still record d; do not zero it.
- **ε_round < |d| ≤ h**: inside the recipient's slab. The recipient voxel already integrates over this thickness, so the re-read is a genuine recipient measurement whose off-plane precision is h. This is not identity; it is the recipient's own resolution.
- **|d| > h**: between slabs (or outside coverage). The recipient has no sample there; any value would be interpolation. Mark "not available," which is distinct from "available, non-dark."

The **interface-only precision condition** before rasterizing: a transported segment may become a barrier in the recipient raster only along the portion whose samples satisfy |d| ≤ h, and the barrier record carries the max |d| and the normal angle along that portion. Portions with |d| > h are kept as off-plane records and are never rasterized. Projection onto the raster is then a placement for inspection, with d retained, and the claim it makes is only "the recipient measured a volume containing this point," which is true by construction.

This differs from the cell depth-nearness test in kind: the cell test judges object sameness by a proximity score; this judges sample coverage by the recipient's acquisition parameters, with no score. The founder's "same, not near" is preserved exactly: same frame, separately sampled.

---

## (3) What the sampling/raster contract must say about bracketed dark intervals

Each interval must carry, as inseparable fields: the source sampler (step along the normal, interpolation kernel, in-plane vs oblique path), the darkness predicate and its threshold, and the sample indices of first and last satisfying sample. The contract then states:

1. **Semantics:** [a, b] is the extent of a run of consecutive samples satisfying a predicate. Endpoints are quantized to the step; the true transition lies within one step (plus kernel support) of each endpoint. That is the only localization statement available.
2. **Width is not thickness.** The run includes partial-volume, slab averaging, and threshold effects, and depends on the sequence's contrast. Widths are never compared across sequences as physical dimensions and never reported as cortex.
3. **No calibration claimed.** Resolution of the run is stated in samples; no uncertainty in physical units is asserted beyond step size.
4. **Intersections inherit the coarser step.** Intersection of two runs is a run at resolution max(step₁, step₂); it does not tighten localization below the coarser sampler.
5. **Re-reads are the recipient's runs.** The recipient re-read along the transported normal uses the recipient's own step and predicate; "no dark interval" means the recipient predicate was evaluated and returned no run, with the recipient values stored so the absence is inspectable.
6. **Barriers are bands, not lines.** Rasterize the full transported interval's footprint; if a centreline is also drawn, it is labeled derived (per 1 above) and never narrower than the band.
7. **Predicate non-transferability.** The donor's threshold is not applied to recipient values and vice versa; a donor-only barrier is therefore a donor-predicate claim, never a recipient-predicate fact.

With the "supported" definition fixed, the connectivity rule declared, the midpoint demoted to derived, and these seven clauses attached to every interval, the increment is internally consistent as a bounded connectivity measurement under stated constraints.
