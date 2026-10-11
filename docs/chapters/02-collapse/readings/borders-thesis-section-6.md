# §6, the borders, as the thesis states them — and the two things it does not

Mined 2026-10-11 from `paper/v7_parts/05_borders.md` (§6, 197 lines, read whole) by a reading agent
under the standing authorization: verbatim quotations with their locations, no judgement. Line
numbers are that file's. Read for OpenSpec task 3.8, the supported-contour-chains contract.

## 1. The movement allowance is the LEEWAY. "Band" means depth.

> L30-32: "Each border point gets a **leeway**: how far the flicker could have displaced it. The
> leeway is the flicker at the light there divided by how steeply the light falls across the border,
> held between half a place and half a speck (1 µm)."

> L12-13: "The **band** is a nucleus's depth, one space is physics, and the camera's flicker sets how
> finely any border is known."

> L100: "A nucleus is several slices deep, and down its column its light rises and falls once, in one
> hump: its band (§5.5)."

The miner states it plainly: *"The file does not state that a band limits how far a point moves."*

**This is a name collision we have imported and must not keep.** The sibling's *code* calls the
movement allowance `border_band`, and this project has followed the code rather than the thesis — in
the consult brief, in the lead's own reading, and in the capability spec's requirement text. Meanwhile
the knee build already uses "band" for a third thing: B2's *transported donor bands*
(`data/pictures/object-toolkit/conversation-b2/series.png`, column 2). Three meanings, one word, in
one pipeline.

Correction, admissible under `AGENTS.md` law 9 as an internal contradiction shown by quoting both
passages: the contract says **leeway** for how far a point may move, and reserves **band** for extent
through depth. The sibling's symbol names stay as they are; our prose and our contract do not follow
them.

## 2. The three constraints of the pull, verbatim

> L24: "Three constraints meet in the pull."
> L24-25: "Of all loops enclosing one area, the circle's is the shortest, so shortening the trace at a
> fixed area rounds the shape as far as the data allow."
> L25-26: "The knowledge that a nucleus is roundish is thus applied as a pull, never imposed."
> L26-27: "No border is known more finely than the flicker, so none is moved farther than its flicker."
> L27-28: "And topology is kept: a dumbbell whose waist is deeper than the flicker keeps its waist and
> its two centers, and reaches the Scissors whole."

The three pulls themselves, L34-39: halfway onto the chord between neighbours; halfway toward an oval
round two centres **that the loop's own area and second moments set on its long axis**; the loop eased
along its normal to hold the area it was traced with, each point held within its leeway **of where it
was traced**.

> L53-54: "What a body drew outside its outline is kept as a finding, never discarded."

## 3. The dome link, in §6's own words

> L59-60: "A center's dome is the territory of places it holds, and a place's dome link is its
> direction to that center."
> L61-62: "Nothing is cut on strength, so a bright nucleus never silences a dim one. Each place goes
> to its **nearest center in the plane**."
> L64-65: "The dome link says which places belong together. It is a **cheap prior, drawn by distance
> alone**, and it **never decides alone**: where it errs is information (§1.2)."
> L68-69: "**Two centers alone do not make two cells, nor does one center make one cell.** Where the
> dome link and a call disagree, the disagreement is evidence, kept beside the call."

Figure 21's caption, verbatim: *"(C) A body that holds two centers, its places tinted by the territory
each lies in, with an arrow at every second place toward its own center; the expert called it two
cells. (D) Another body, drawn the same way at its own slice, also holds two centers; the expert
called it one cell."*

## 4. THE DECISIVE ABSENCE: the thesis has no gap-completion rule, because it never has a gap

The miner, having read the whole section: *"Bridging, completing or filling a gap: the section has no
such sentence."* The only "fill" in §6 is figure 20's caption describing shading — *"the dim fill is
the places the pull shed"*. And the one sentence nearest to joining is a **prohibition**:

> L52-53: "Each body is pulled taut on its own as the lenses begin to read each other, so **neighbors
> never join across the lane between them**."

**Why the thesis needs no such rule.** Its outline is traced round a *filled contiguous mask* — the
sibling's `borders_of` runs marching squares at 0.5 on the mask padded by one empty place, so **every
loop closes by construction**. A body is contiguous and closed by its gestalt (L9-10). The question
"what do I do about a gap in the trace?" cannot arise there.

**Why the knee's situation is not the same, and this is the heart of task 3.8.** A knee territory's
loop is *also* closed by construction — it is the boundary of a watershed region. What is dotted is
not the loop but its **support**: each place of the loop is typed by what lies across it, and the
typing can be *measured dark*, *a peer territory* (a constructed divide, a decision rather than a
reading), or unread — the production codes already include `native_open` (252 places on the saved B2
run), `native_missing` (49) and `native_multiple` (20).

So the knee's "gap" is **a run of places on a closed loop whose profile returned no bracketed dark
interval**, not a hole in a curve. The operation 3.8 has to contract is therefore not "bridge a gap"
but: *may the loop's POSITION in an unsupported run be set from its supported flanks, or must it stay
where the watershed put it and be reported as unsupported?*

That reframing matters because it rules out the analogy the lead was about to lean on. The sibling's
pinned behaviour *"a hole narrower than its band closes"* is **not** the knee's completion rule: that
is a hole in a filled mask closing under the pull, not a position being inferred across an unsupported
run. The knee needs something the sibling does not have, which means it must be derived here and
cannot be ported.

## 5. The sanity test, for the record

> L50-51: "A shape is sane when its outline is one closed loop and its width, the diameter of a circle
> of its area, lies between 4 µm, the narrowest nucleus, and 15 µm, the ceiling the structure keeps
> for one cell."
> L51-52: "A wider shape is taken whole, and parted after the take (§5.3)."

A size bound of this kind is biology's, per L10-12, and the knee's own values are the founder's to
give — they are not ported.

## What the miner did not look at

Only `05_borders.md` was read, whole, in one call. Not opened: the four figure PNGs (captions are the
file's own text); every section §6 cites (§1.2, §1.8, §1.9, §3.3, §5.3, §5.5, §7.1, §8–§10, §10.4,
§10.5); the other `v7_parts` files; the canonical copy; the cell-tracking code. No commands and no
text search; the absence claims come from reading the whole file.
