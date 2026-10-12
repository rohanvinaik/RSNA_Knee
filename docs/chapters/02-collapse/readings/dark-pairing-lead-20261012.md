# Task 1.3a: the literal support of a dark-bounded pair

Lead reading written before implementation. The founder's `<object>` definition and task 1.3a
license indexed extents, never anatomical identity. This construction records which extent a
bracketed profile actually reaches, not a conjectured far-side label in the boundary census.

`profile_samples_reference` reads each positive-weight bilinear contributor. Its output is an
intensity average; that arithmetic is not portable to categorical labels. Counterexample:
contributors labelled 1 and 3 at equal weights average to 2, which need not occur anywhere there.
Therefore label interpolation cannot support the construction.

`dark_bands` already locates a single fully read bounded sampled dark run and records its low/high
offsets. The two immediately flanking sample positions are therefore in the existing profile
grid, not a newly chosen radius. Reconstruct their original native coordinates from that grid's
recorded points, normals, offsets and spacing. Read every positive-weight native contributor's
label at each of those positions, retaining the complete footprint. No nearest-label choice,
label average, new intensity threshold or tissue identity enters.

A pair is supported only when the near footprint's contributors all belong to the recorded
source extent, and the far footprint's contributors all belong to one different positive extent.
This is an exact statement about the partition's ownership at those sample positions. It does
not assert an unsampled continuous gap, a closed border, a three-dimensional interstice, or its
meaning. Mixed, unassigned, unread, same-object and source-mismatch outcomes remain distinct.
The existing bracket's sampling limit remains visible. Every profile is retained, including
those whose trace was not bracketed. The input stage's absence is named separately.

The knee's existing sampler is the engineering source for the positive-weight footprint rule.
Its coordinate formula is read literally in `src/knee/objects/profiles.py`; `dark_bands` and the
production caller are read whole in `interiors.py` and `analysis.py`. No sibling instance's shape
prior is reused. This is the source contract for the lead-owned unit, not a domain ruling.
