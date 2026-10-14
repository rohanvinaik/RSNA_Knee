**Provable defects (within the stated contract)**

1. **The guard set contaminates the distance semantics.** If EDT is computed to low ∪ unavailable ∪ outside, the value at a pixel is min(d_low, d_unavail, d_frame), not "distance to low signal." Near a large unavailable region this is a lower bound only, and h‑maxima computed on it have prominence relative to the wrong field: seeds can be suppressed, split, or shifted purely because of where unavailable happens to lie. That is functionally treating unavailable as a boundary — the same effect as treating it as false — at the seed stage, even though edges are later tagged honestly. Coherent repair without redesign: tag each seed with which guard class determined its maximum (and the margin to the next class), so "guard‑limited" seeds are distinguishable from low‑signal‑bounded ones.

2. **Tie‑breaking is unspecified, so the partition is not deterministic.** Watershed of −EDT has plateaus and exactly‑equidistant ridges; h‑maxima has plateaus and dynamics exactly equal to h. Without a declared rule (ordering, plateau handling, strict vs. non‑strict h), two correct implementations produce different territories and edge sets. "Classical deterministic" requires the rule to be part of the contract.

3. **Rounding error is not scale‑free.** If anisotropic spacing is rounded, absolute distance error grows linearly with distance (≈ relative spacing error × d). The h‑maxima criterion compares an absolute prominence h against values whose error depends on territory size. Seed existence is therefore not reproducible across rounding choices unless you state the condition error(d_max) < h, or tag seeds whose dynamic is within the bound as prominence‑marginal. Note an exact orthogonal‑grid physical EDT exists, so rounding is a choice that needs a stated reason.

4. **Normal direction on a pixel‑edge boundary is axis‑aligned.** Raw directed boundary edges have only four orientations. A profile along that "normal" crosses an obliquely oriented band at angle θ, so measured width ≥ true width by 1/cos θ, and the midpoint is on the band but not at the orthogonal projection of the edge. Either declare the normal‑estimation scheme (and its support length) or record the width as an upper bound.

5. **Profile codes are window‑dependent.** "Exactly one below‑level interval" vs. "multiple" vs. "unbounded" changes as the profile length changes; the code is not a property of the image but of (image, window). The physical profile extent must be part of the recorded datum.

6. **"Below‑level" is ambiguous relative to the consumed predicate.** Either it is the given low‑signal predicate sampled along the line (then no new level is introduced, and bracketing endpoints are automatically above‑predicate on the interior side), or it is a new level on original values (then a threshold has been introduced, contradicting "consume an existing predicate"). State which.

**Concrete unresolved questions**

- Does a profile continue across the peer territory on the far side, using original values regardless of label? (It must, for the far bracket to be meaningful, but the text doesn't say.)
- For peer edges, both directed copies (A→B, B→A) sample the same geometric line; are the two measurements required to be identical, and is disagreement a recorded code?
- "Unseeded" edges can only arise against above‑predicate components containing no seed (flooding fills any seeded component). Is that the intended meaning, or is there also a notion of unlabeled pixels inside a seeded component?
- Is the 2D procedure run per slice with a per‑slice label namespace? If so, "territory" across sagittal/coronal in the root test are unrelated objects, and any cross‑slice comparison belongs entirely to the later continuity lens.
- What is the minimum h relative to pixel spacing, since h‑maxima on a discrete EDT cannot resolve prominence below one spacing step?

**What is sound as stated**

Classifying edges by what bounds them, retaining non‑measurement codes rather than collapsing them, keeping territory as candidate rather than ownership, and treating unsupported divides as information all hold up. The defects above are all about making the stated measurements actually reproducible and semantically what they claim; none requires changing the step's scope.
