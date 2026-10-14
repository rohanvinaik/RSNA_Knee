# Anatomical lens workshop — Fable second reading

Conceptual model-only consultation. No source files, pixels, reports or patient identifiers were sent. The lead reading was saved before this response was opened. This is a second reading, never design authority.

**A. Residual positive-mask framing**

Your reading mostly escapes it, but two places still treat a warranted exclusion as something that *appears* rather than something that *acts*.

First, contour-chain construction "inside explicit measured movement bands." As written, the band is a geometric search region derived from measurement; nothing in it says the band itself is narrowed by a warranted exclusion. If a profile across a nominated contour portion, read in one view, warrants "this transition interval is not a bone boundary for the femur question" (e.g., it is accounted-for material belonging to a positively resolved neighbour), then the chain search for the femur contour must not be allowed to enter that interval, and the chain must be permitted to terminate there as a *known-stopped* end rather than a gap to be closed. Under premise 2, retaining the raw profile without that exclusion's lineage leaves the chain builder free to reuse support that has already been consumed. Concretely: the movement band must be computed from (measurement ∩ not-yet-consumed support for this question), not from measurement alone.

Second, the reread after known bodies. Your text says the reread "uses additional affirmative signal alongside absence from previous bodies to propose new sites." That is correct in intent, but it only becomes a computation if the previously accounted-for support is actually removed from the candidate pool for *this* question while remaining available for other questions (premise 3). A between-bones region positively bounded by femur and tibia contours has, for the "bone" question, reduced possibilities; for the "synovial fluid" question it stays open. If the reread consults one retained mask rather than per-question consumed support, the exclusion is cosmetic.

A third, smaller place: adjacent-section correspondence in axial. If a bone is warranted absent in section *k*, correspondence from *k−1* to *k+1* must not bridge through *k* as if it were merely unread. "No-read" and "warranted negative" must drive different bridging behaviour.

**B. Minimal typed record**

Per place (or per support unit: territory, contour portion, section), keep four separate fields, each per question rather than per verdict:

1. *Measurement availability*: acquired value / acquired zero / unavailable reading. This is about the sensor and sampler only and carries no question (premise 1, premise 3).
2. *Claim status*, keyed by named question: open (unanswered), warranted positive, warranted negative, peer-owned, unassigned, disagreement (alternatives retained). "Open" must be the default and must not collapse into negative when a measurement is missing.
3. *Geometry support*: which territory, contour chain, section and view this unit participates in, with notches, clipping and alternative edges listed as distinct entries rather than merged.
4. *Causation*: the operation that changed the claim status, its cause (which reading or which prior resolution), its scope (this question, this view, this section), and its trace back to the source provenance of the profile.

What keeps a lens from becoming a feature of one verdict is that fields 1 and 3 never mention a question, and field 2 can hold several questions' statuses for the same unit simultaneously. A unit can be "warranted negative for femur, open for fluid, unassigned for meniscus" with one measurement record.

**C. Dependence order: gaps and circularity**

The chain as stated runs: closed-leg support → two-marker watershed territories → profile readings along nominated contours → claims → contour chains → bone identities and facing relations → joint localization → smaller structures → axial identity via cross-view nominated evidence → reread of residual → new territories.

Circularities to make explicit:

- *Territories and exclusions*: the watershed partitions support before any reading. Its territories are hypotheses with a cause ("two-marker partition"), not claims. If an exclusion later consumes support inside a territory, the territory's extent must be recomputed or marked as superseded; otherwise exclusions and territories each assume the other is fixed.
- *Contours and identity*: you correctly say candidate geometry is not an identity call, but contour chains are "nominated" by territory, and territories are built from markers that are already placed by assumed bone positions. State whether marker placement is a measurement (from geometry metadata) or a hypothesis (from a prior look); if the latter, it must carry a trace.
- *Joint localization and the intervening region*: the between-bones region is defined by resolved bone contours, yet the bone contours' movement bands are bounded by the region. Pick one direction for the first increment and record the other as a later constraint.
- *Axial identity and cross-view alignment*: alignment from acquisition geometry is a measurement and can be used first; alignment refined through resolved bones is a consequence and cannot feed back into resolving the same bones without a trace. The text does not say which alignment the "nominated evidence from other views" uses.

A first inspectable increment under the theory: take cross-view alignment from acquisition metadata only; nominate contour portions from the exploratory territories while labelling them as hypotheses with cause; read raw values, physical derivatives and transition intervals as separate quantities; record claims only as "open" or "disagreement" plus any exclusions that follow purely from positively resolved surrounding material; display positives, warranted negatives, unassigned support and raw data together. Make no identity or joint call in this increment. This avoids inventing thresholds and does not assume every contrast extremum is bone — extrema are entries in field 1, not in field 2.

**D. Sorting the uncertainties**

*Acquiring a measurement*: coverage holes in coarse tiles, unavailable native readings, reference/strict-JIT disagreement in the sampler, axial sections changing substantially along the stack, low-signal samples occupying structures other than the one outlined. These stay as availability states.

*Computing a consequence*: whether consumed support reduces a movement band, whether a chain end is known-stopped or merely unread, whether a territory is superseded, whether section *k* bridges, whether a between-bones region is partially accounted for. These are deterministic once the claim statuses and causes are given.

*Obtaining an anatomical warrant*: which transition interval counts as the femur boundary, whether a facing relation is a joint, whether nested material is meniscus or fluid, whether visibility in one section licenses expectation in another. Per premise 5, numeric laws support identity warrants but do not make the call; these require the domain expert and should remain "open" in the record until supplied.

Keeping these apart means an unresolved place in category 1 or 3 is never written as a negative in category 2.
