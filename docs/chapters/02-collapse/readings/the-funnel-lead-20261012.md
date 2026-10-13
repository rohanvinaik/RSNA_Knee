# The funnel — the lead's reading of what it has been missing, written before the consult

*2026-10-12. The lead's own reading, written BEFORE opening the Codex answer
(`the-funnel-codex-20261012.md`), as the working loop requires. Inference is labelled as the
lead's. The founder's words are verbatim. The thesis's own words were mined by cheap agents
(Haiku, whole sections, verbatim with line numbers) and are quoted in §3 with their locations.*

## 1. The founder's words, verbatim (2026-10-12)

The sheet he walked is `03-coronal-fs1-fat1.png` of `data/pictures/view-frames-20261012/…/study-views/`,
panels numbered 1 (top left) to 22 (bottom right), row by row. Its pair is `02-coronal-fs0-fat0.png`.

> "So, if you're actually following the epistemology I've been trying to express, the answer should
> be obvious. Also, why the build is currently NOT the "performance engineer, SICP-style, one compute
> operation per script, paralelizable compute, shared information, superposition of lenses resolving
> meaning" I specified that this should be."

> "First off, fat-dark vs fat-bright? These aren't independent views. These two are basically
> "lenses" that are given to us for free, by the competition itself."

> "The goal here is to try and resolve \<object>s that correspond to "bone", tibia and femur. On image
> 2, already, we can CLEANLY see most of the noise cleanly subtracted out (repeated on image 10?). I
> see the background CLEANLY resolved out. We need to actually fix this lens to work on all five
> images, but once it's good like this for all of them, we should NEVER spend a SECOND of compute on
> this ever again. Literally EVERY analysis that comes after this is wasting about 40-50% of its
> compute on places that should be comepltely removed and NEVER read for ANYTHING, EVER. So yeah,
> THAT'S what I've been trying to communicate. We're on the FIRST lens, and already the search space
> is halved, and the uncertainty of the resolution is exponentially smaller. That's not a vibe, I've
> proven this mathematically. We can also see that already both the tibia and femur are
> non-trivially resolved. If we had a script that needed to wildly guess SOMETHING at only this
> stage, we'd actually be able to hit the tibia and femur basically 100% of the time."

> "Also, this, and MANY of the other lenses, should have been computed off the lossy/squint view, the
> one that collapses that image into, I think, a 16x16 grid? We are doing two things--(1) high-level
> localization and targeting, and (2) fine-grained targeting and boundary-drawing. The "squint" view
> is WAAAAY cheaper. If the raw image is 256x256, then a 16x16 grid costs literally (n)^(1/2), for
> EVERYTHING. And when we've actually done that, wherever I've seen it, the squint view was MORE
> than enough to target analyses properly. Like, common-sense high-level reasoning, you only spend
> expensive compute to try and find the exact boundary of things in the places where they actually
> look like they might exist. Same sort of thing as the "black"/"air"/"background" removal thing I
> just outlined. Why try and draw boundaries where the bones aren't? I didn't do this quite so
> strictly in the cell tracking project because you can never actually predict where cells will be.
> But knee images? They almost ALWAYS look the same. Why compute vectors and shit where we know the
> knee isn't?"

> "No idea what's wrong with views 3/4, they just seem like pointless noise compared to 2. Pretty
> sure they're a mangling of what I actually wanted. Also 5/6. Not sure what they're supposed to be,
> I don't think that's what I asked for. Also, you missed some of the most CRITICAL lenses, the ones
> that were in [Image #1]."

> "Images 7/8 feel like another duplication, but they're HIGH-resolution lenses. When it comes to
> the high-level resolution of the boundaries of the bones, the expensive stuff, this is REFINED. I
> mean, LOOK at the boundary there. Is there any question what the tibia and femur look like?"

> "Image 9 isn't really anything"

> "Image 11 is partially what I was talking about, partially build, but WAAAAAAAAY more expensively
> than was needed."

> "the "interior peaks" one is VERY useful for specific selection of \<object>s that are potentially
> significant, treating them as physical objects that are grounded and connected as a singular
> whole, will be useful for diagnosing; i.e., what is "wrong" with the coherent object that is
> grounded to those interior peaks"

Image #1 is `data/pictures/codex-wiring-rereview-20261012/…/objects-interiors/series.png`: per
series, the acquired signal; measured low signal (red) and unavailable (magenta); **the distance
from surrounding constraints with the interior peaks (cyan +)**; all proposed interiors
(territories); the original native territory edges; the dark-band traces by outcome.

## 2. What the panels are, and what each cost (facts from the code and the saved run)

The sheet draws, on the acquired plane, every saved per-place reading of the route in route order.
What each panel's stage computes, where, and at what scale, from `src/knee` and the receipt of
`codex-closeout-review-jit-20261012` (the coronal fs1/fat1 series is 320 × 320 px at 0.5 mm, 36
slices; its squint is 54 × 54 tiles of 6 × 6 px):

| panel | reading | stage | computed over | scale |
|---|---|---|---|---|
| 1 | the acquired plane | study | — | native |
| 2 | places at or below the background split (the first valley of the whole-series histogram) | field (`collapse.noise.background_split`) | the whole volume's histogram; the mask over the whole plane | native |
| 3 | the air: low places connected to the frame's border | field (`collapse.structure`, 7.1) | the whole plane | native |
| 4 | the leg, closed: the complement of the air with holes filled | field (7.1) | the whole plane | native |
| 5 | two basins seeded by the header's axis and the profile's dip, and the seam between them | field (7.1) | the squint inside the leg | tiles |
| 6 | the darkest tiles and the largest bright bodies by rank | field (7.1) | the squint inside the leg | tiles |
| 7 | member `noise_law_cut`: one ternary digit per place against the noise law's tercile edges | lenses (`lenses.places`) | **the complete native volume**, every slice (3,686,400 places here) | native |
| 8 | member `background_split`: the same digit rule against the background population's tercile edges | lenses | the complete native volume | native |
| 9 | the standing between the two members per place (concur / dissent / one-only) | lenses (`lenses.members`) | the complete native volume | native |
| 10 | B1's measured low signal (the places at or below the split) and the unavailable places | objects (`objects.interiors`) | the whole plane | native |
| 11 | B1's territories: a marker-controlled watershed over the Euclidean distance transform of the available non-dark places, seeded at the prominent peaks (3 mm) | objects | the whole plane | native |
| 12 | B1's territory edges by what lies across them | objects | every edge pixel of every territory (5,176 here; 13,028 on the sagittal) | native |
| 13 | B1's profile traces across every edge, 13 samples each, by outcome | objects (`objects.profiles`) | every edge pixel | native |
| 14 | the conversation: the same-orientation partner's bounded dark bands transported into this plane | objects (`objects.conversation`, B2) | every bracketed edge of the partner (1,849 here) with a 13-sample profile each | native |
| 15 | the conversation's native outcomes and derived concurrent traces | objects (B2) | as 14 | native |
| 16–17 | the concurrent and conditional subdivisions of the territories by the transported barriers | objects (B2) | the whole plane | native |
| 18–20 | ownership members (solitary, concurrent, conditional): claimed and residual places | ownership | the whole plane, one partition per parse | native |
| 21 | the disagreement between the solitary and concurrent claims | ownership | the whole plane | native |
| 22 | the pairings: the flanking sample sites of every profile by outcome | relations (`relations.pairings`) | every edge profile (5,176 sites) | native |

Not per place, so not on the sheet: the bundles (`vectors`), which count every lens map and the
standing over every territory; the predicates and the output.

**What no stage does.** No stage reads the background mask of panel 2 (or the leg of panel 4) to
restrict where it computes. The lenses write a digit at every voxel of the volume, air included;
B1 transforms the whole plane; the traces, the pairings and the conversation cast a profile at
every edge pixel, the leg's rim against the air included; ownership partitions the whole plane.
Every stage is total over the whole field, and the only place the readings meet is the bundles,
after everything has been computed everywhere. The squint is computed (panel 5's substrate) and
nothing downstream targets by it.

## 3. The thesis's own words

The mined record, verbatim with line numbers, is `the-funnel-thesis-quotes-20261012.md` (§1.2,
§1.3, §1.5, §1.9, §1.11, §2.8, §3.5, §4, §5, §6, §7.3–7.7, §13.6–13.7, each read whole by a
miner). The sentences the lead's reading rests on:

- **The funnel is the thesis's own order.** "Stage 1 (§5.2) clears what any eye would call
  background before anything is drawn … **Each later step works only on what the earlier steps
  left**" (2280–2283). "A coarse view of the whole field is itself a squint … **It narrows where
  the expensive work runs**" (2325–2330). "Black is silence in the full analysis. Where a lens's
  stage 1/2 clears a place, **that lens spends no full analysis there**" (2984–2990). "Physics and
  abstention prune. … neither the look nor the search for missed cells computes anything at a place
  a cell already holds. A lens that cannot speak at a depth is not computed there" (4306–4308).
- **Cheap first, and why it is cleaner as well as cheaper.** "a reduced reading is cheaper and
  cleaner at once, and signal-to-noise rises as the work falls" (2247–2252); the mathematics:
  projecting onto the $k$ dimensions a question reads raises signal to variation by $N/k$, and
  pooling $n$ places raises it by $\sqrt{n}$ (299–313); a categorical question needs at most
  $\log_2$ of its answers in bits, one balanced-ternary digit for three (327–335).
- **Reading by exclusion, and the arithmetic of "exponentially smaller".** "a reading that is poor
  at finding a signal can be reliable at saying where the signal is not. What something is not
  tells what another thing is … so what the lenses set aside is defined away, not lost"
  (2291–2295). "A wide lens … What it does not hold can be cleared outright … A narrow lens speaks
  rarely, and is knowably correct where it speaks, so there it settles" (1177–1189). The count:
  $H_0(X) - H(X \mid S) = [H_0(X) - H(X)] + I(X;S)$, "what the laws remove by narrowing the
  admissible states" plus "what the rest of the problem says through them" (488–500); constraint
  propagation takes $4^n$ assignments, $2n$ bits, from "longer than the age of the universe" to
  seconds (514–523).
- **The residual is the same problem with added context, and the gain is large.** "remove the plain
  part of the problem, classified structurally, together with everything its laws say it caused.
  What remains is the same kind of problem with added context" (1050–1055); the weak source beside
  the strong carries 0.02 bits, after subtraction 1 bit, "nearly fifty times as much" (1067–1074).
- **The dome grounds the object, cheaply.** "A center's **dome** is the territory of places it
  holds … Nothing is cut on strength, so a bright nucleus never silences a dim one. … The dome link
  … is a cheap prior, drawn by distance alone, and it never decides alone: where it errs is
  information" (2699–2711); "Read as a relief of light, a nucleus is a peak. Its border is where the
  peak falls to its surroundings, and a valley is where one <object> ends and the next begins"
  (2650–2655).
- **Lenses are separate sources, and a family counts once.** "there are four, partly orthogonal …
  Their agreement and their disagreement are both information" (2134–2149); "Two lenses at about
  one depth read one plane two ways, and each corrects the other's borders" (2156–2160); "their
  errors must be independent enough for their agreement to be evidence" (3101–3105); "A family is
  the readings of one source. They are not independent of one another, so they count once, and no
  evidence is counted twice" (1242–1250).
- **The engineering shape.** "Compute once, keep, consult. A value is made once where it becomes
  known, and handed to every consumer" (4298–4302); "Functions are of three kinds, kept apart. A
  measurement … A decision … An orchestration only moves values between stages. Each function is
  small and pure, and does one thing a biologist could name" (4318–4321); "Each use is kept beside
  it with its consumer, so a finding never used shows itself" (4323–4326).
- **What the black keeps.** "Stage 1 deletes nothing … the voxels stay for every other lens and
  every later round … a removal is a decision by a reading entitled to make it, kept as a record,
  never a discard" (2353–2357); "What an earlier black silenced, no profile brings back, and that is
  why the readings behind each such decision are kept" (3101–3105).

### 3b. The engineering oracle, as its code map states it

Facts from `cell_tracking/docs/CODE_MAP.md` (read whole by a miner; the map's own lines, not a
symbolic trace of the source, which is still owed for any unit the knee borrows). The sibling's
shape is the funnel the thesis describes, in its own vocabulary:

- **The cheap whole-field pass first.** `instruments.background.embryo_background` ("the embryo's
  dark"), `instruments.acquisition.quiet_level` ("per voxel quiet + departure; per frame drift +
  step"), `record.frame.frame_state` ("one frame's projection + imaged-edge map"), and a **scale
  ladder**: `members.scalespace.scale_ladder`, `scale_space_counts` ("pixel · motif · cell ·
  neighbourhood"), `SPATIAL_SCALES`, `FINE_SMOOTH_UM` / `COARSE_SMOOTH_UM`, and a
  `squint_shape_verdict` (map lines 63–73, 612–658).
- **Candidates found cheaply, everywhere, as domes.** `instruments.detect.detect_candidates`:
  "every −LoG blob brighter than its ring, strength in flickers"; `nearest_brighter`,
  `brighter_neighbour_ratio` (lines 64, 343–352). One `ObjectRecord` **per candidate** per frame
  (line 354–357).
- **The expensive work only at a candidate, in a crop.** `instruments.localize.relocalize`,
  `crop_window`, `radius_vox_for_um` (lines 414–420), consumed by `record.record`,
  `substrate.encode.profile` and `members.scalespace`; `instruments.support.read_support`,
  `read_uncut_body`, `read_dips` ("the object over its own support; seams; dips", line 70), with
  the map's own cost note: "In the unoptimised reference path, most of this stage's time is the
  seam and dip geometry. That is where the EXEC-14 levers go, and where the pre-filter first
  applies" (364–365). The profile is per region: `substrate.encode.profile.region_profile_counts`,
  `profile_rows` ("the Layer-1.5 bank profile + exact decode", line 72).
- **Rounds, the pull-out, the final sweep.** `conclave.descent.descend → _Descent.run`: "rounds
  until nothing changes (max_rounds 20), then _final_sweep" (line 81); `_settle → pull_out →
  _commit (a FactCase)` (line 89).
- **Parallel by frame, computed once and kept.** `pmap(_record_frame_cached_task) per frame`
  (line 67); `record_cache_key`, `resume_decision`, `parallel_plan`, and "parallel maps that must
  return what the serial map returns" (lines 198–211).

The lead's inference from these facts: the sibling spends its whole-field compute on the cheap
readings and the candidate detection, and its expensive geometry only in a crop around each
candidate; the knee build spends its expensive geometry over the whole plane and its lenses over
the whole volume, with no candidate step between the field and the geometry.

## 4. The lead's reading of what it has been missing — labelled as the lead's inference

**(a) The pipeline is a funnel, not a row of total stages.** Each lens is cheap, lossy and certain
about what it *excludes*. Its output is a shared fact that every later computation consumes to
decide WHERE to look at all. The first lens, the background, removes the air with no false
exclusions, and from then on nothing reads the air: not the digits, not the distance transform,
not the traces, not the pairings. His arithmetic, which the lead takes as his: the search space
halves at the first lens and the uncertainty of every later resolution falls with the product of
the exclusions. The build instead made every stage total over the whole field, so each stage is
honest in isolation and none consumes another's exclusion; the readings meet only at the end, in
the bundles, after the compute has been spent everywhere. That is "functionalities in islands" by
another route: islands that run in sequence but do not narrow one another.

**(b) Two resolutions for two jobs.** The squint (the tile grid, the thesis's collapse) is for
localisation and targeting: at tile scale the two bones are already resolvable with near-certainty
("hit the tibia and femur basically 100% of the time"), at a cost two orders of magnitude below
native. Native resolution is for boundary drawing, spent only in the band around a localised
object where its boundary can be. The build runs the lenses, the distance transform, the
watershed, the traces, the conversation, the pairings and the bundles at native resolution over
the whole plane or volume, and never uses the squint to target any of them.

**(c) The acquisitions are the free lenses, and their superposition is the meaning.** The coronal
fat-bright (fs0/fat0) and fat-dark (fs1/fat1) series are two lossy measurements of one object,
handed over by the competition. Read per place in one frame, their conjunction names what neither
names alone: marrow is bright in one and dark in the other, so the femur's and tibia's interiors
are the (bright, dark) places; cortex, tendon and meniscus are dark in both; fluid is bright on the
fat-suppressed series; cartilage sits between. That is the thesis's bundle across lenses. The build
instead seats two members that are one measurement under two tercile rules (`noise_law_cut` at
80/120 and `background_split` at 79/119 on this series) and calls their agreement "concur" — which
is why panel 9 "isn't really anything": they are not independent, so their standing carries no
information. The real second lens, the other acquisition, is reached only through B2's boundary
exchange (profiles along normals, bands rasterised), which is a boundary-level and expensive way to
do what a per-place conjunction in a shared frame does cheaply.

**(d) The black is resolved once, then never read.** Panel 2's lens is the right first lens, and it
is to be made to work on all five views, then frozen; after that no script spends compute outside
the leg. Panels 3 and 4 are re-derivations of panel 2 (air by connectivity; the complement with
holes filled), and panels 5 and 6 are a tile-scale reinvention of the two-objects-and-a-gap idea
through a profile dip, which is not the mechanism he gave. What he gave, 2026-10-10, was the dome:
the distance fall-off from the surroundings that marks an object's border, whose interior peak
grounds the object. That is the column the sheet left out (image #1's third column), and the
territories of panel 11 are its product computed at the most expensive scale.

**(e) The interior peaks ground the objects.** Each prominent peak of the distance field is the
grounding of one physical object connected as a single whole; the two tallest at the squint scale
are the femur and the tibia; the lesser ones are the residual. The object grounded at a peak is the
unit a predicate is asked of: a fracture is a break in the coherence of the object grounded there,
a contusion a signal anomaly inside it. The selection of significant `<object>`s is the ranking of
peaks by prominence, which at tile scale is nearly free; the expensive boundary tracing then runs
only around the selected objects.

**(f) Panels 7 and 8 are the refined, expensive lens, in the right place at the wrong scope.** The
native digit maps DO draw the bones' boundaries crisply; that is where native-resolution compute
belongs — but only in the band the squint selects, not over the whole volume, every slice, air
included.

**(g) Why the build is not what he specified.** His specification was: one compute operation per
script, each a pure function of shared inputs, parallelisable across series, tiles and objects,
and the meaning assembled as the superposition of cheap lenses. The lead built nine stages that
each re-read the whole field at full resolution, each total over its predecessor, with the sharing
deferred to a final count. The SICP shape he named is the opposite order: background → leg mask;
squint per acquisition → tile digits inside the leg; conjunction across acquisitions in one frame →
tissue per tile; dome at tile scale → peaks → objects; the band around each object → native digits
in the band only → the boundary; each a layer whose output is the next layer's domain.

## 5. After the consult — where Codex agrees, where it corrects, what stands as the lead's

*Written after opening `the-funnel-codex-20261012.md`. Agreement reached independently is
evidence; a correction with a proof is taken; the rest is a question for the founder.*

**Agreement, independently reached (a, b, d, f, g in their core).** Codex supports, from the same
quoted lines, the criticism that is the heart of the reading: the build's stages are total over the
whole field and no exclusion has a downstream consumer, against "Each later step works only on
what the earlier steps left" (2280–2283) and "It narrows where the expensive work runs"
(2325–2330); the squint is computed and targets nothing; the acquisitions are lenses to be read
jointly (2156–2160); the first lens is to be resolved early and consulted; the distance field with
its peaks is missing from the sheet; panels 7 and 8 are the refined lens whose scope is wrong; and
the engineering rule is "Compute once, keep, consult" with functions that are measurements,
decisions or orchestrations (4296–4326).

**Corrections the lead takes, each with Codex's proof.**

1. *Measurement certainty is not decision authority.* "A tile's median is exactly that tile's
   median" makes no tile certainly air. An exclusion the rest of the route may rely on needs the
   standing of a **narrow** reading, "knowably correct where it speaks" (1177–1189): the senior
   filter's standing, not a wide lens's. Panel 2 today is a wide lens: it holds the air and extras
   (the dark tissue inside the leg). So "fix this lens to work on all five images" is, in the
   thesis's terms, making the first lens narrow: fire only where a place is knowably not knee, and
   there decide alone. The lead's (a) wrote "certain about what it excludes" as if the measurement
   gave that; the structure must.
2. *"Never read again" is about the full analysis, not the record.* "Stage 1 deletes nothing … the
   voxels stay for every other lens and every later round" (2353–2357); "Where a lens's stage 1/2
   clears a place, that lens spends no full analysis there … Yet a black place still writes
   something" (2984–2990). The lead reads the founder's "NEVER read for ANYTHING, EVER" as the
   thesis's rule on compute, not on the record: no expensive analysis is spent on a cleared place,
   the decision and its reasons are kept, and the cheap readings may still be written there. This
   is put to him as a question (§6, 2), not assumed.
3. *The "product of exclusions" was the lead's arithmetic and is withdrawn.* Overlapping exclusions
   do not multiply. The thesis's own count is $H_0(X) - H(X \mid S) = [H_0(X) - H(X)] + I(X;S)$
   (488–500).
4. *Panel 9 is not proven to carry nothing.* A family "counts once, and no evidence is counted
   twice" (1242–1250) forbids double counting; it does not make $I(X; Y_2 \mid Y_1)$ zero. On this
   series the two members' edges differ by one stored unit, so what the second adds is small; that
   is a measurement to report, not a verdict.
5. *Panels 3 and 4 are not the same measurement as panel 2.* Border connectivity and closure with
   holes filled are different conditions from "at or below the split". The founder said of them "No
   idea" and "Not sure", which is a question to answer in words, not an authorisation to retire
   them. The lead's (d) overstated.
6. *The orders of magnitude were wrong.* This run's squint is 54 × 54 tiles of 6 × 6 px on a
   320 × 320 plane: about 35 times fewer places, not a hundred. His 16 × 16 example on 256 × 256 is
   256 times fewer.
7. *"Tissue per tile" as a merged map is against the thesis.* Concurrence yields "a cleaner set of
   each lens's own bodies, never a merged picture" (2373–2383). The conjunction of the two
   acquisitions is read per place by a question over both lenses' kept digits; it is not a third,
   merged map. The lead's (g) sequence is its own architecture and is withdrawn as a sequence; the
   principle it was trying to state, each layer's output the next layer's domain, stands as a
   question for him.
8. *The dome's height field.* Codex notes that §6 reads "a relief of light" (2650–2655), and that
   the knee's distance-from-constraints field is an added interpretation. That interpretation is
   not the lead's own: it is the founder's ruling of 2026-10-11 ("Yes, deliberate homology", the
   distance transform as the dome's height field, `docs/OBJECT_MODEL.md`, Tier 1), so it stands on
   his words rather than the thesis's.
9. *What is the lead's addition, labelled so.* That the two tallest peaks are the bones; that
   prominence ranks significance; that fracture and contusion are predicates on the object grounded
   at a peak. The last of these is the founder's own table of 2026-10-11 (Fracture: "break in the
   structural coherence of its outline/interior"); the first two are the lead's and are questions.

**What Codex says the lead still misses, which the lead accepts.** The residual is what remains
after a *warranted* removal, with its added context (2434–2437), not "the lesser peaks"; the
candidate pool is generous by design (2812–2823). And the record must carry each decision with its
consumer, "so a finding never used shows itself" (4323–4326): the ledger already records
`consumed_by`, but a consumer that reads a value and does not let it narrow its domain is exactly
the shape the founder named.

**The mathematical claim, as the lead now reads it (the lead's inference, for his correction).**
In the thesis's terms the uncertainty of a field of $N$ places is $H_0 = \log_2 |\text{states}|$,
and the admissible states number $k^N$ for $k$ labels a place can take. A narrow first lens that
settles half the places as knowably not knee leaves $k^{N/2}$ admissible states: the bits halve and
the states fall exponentially, which is the §1.5 map-colouring picture ($4^n$ assignments, $2n$
bits, propagation to seconds). The lead takes "the uncertainty of the resolution is exponentially
smaller" to be this count of states, and asks whether that is the proof he means.

## 6. Where the lead is still uncertain — questions, not blockers

1. "Fix this lens to work on all five images": on the five sheets the background split marks the
   air on every view, with specks inside the leg on the fat-suppressed series. Is the fix about
   those specks (the leg's interior dark places read as background), about the fat-suppressed
   series where air and dark tissue are close in value, or about one rule that holds across all
   five acquisitions of a study?
2. The conjunction of the two acquisitions: in which frame? The squint's tiles in patient
   millimetres, resampled from each series' own grid, or native pixels after resampling one series
   onto the other's grid? And does the per-place conjunction replace B2's boundary exchange, or sit
   beneath it as the cheap pass that targets it?
3. The two members on one image: is `noise_law_cut` to be retired, leaving one member per
   acquisition, so that "the members" are the acquisitions?
4. The field's structural reading (panels 3–6): retired in favour of the dome, or kept as the
   leg mask alone (panel 4 is the mask every later script would take)?
5. The thesis-side question the lead cannot settle alone: in the cell build the loop's "reaching
   down" was per candidate site because cells can be anywhere; for the knee he says the targeting
   can be stricter because knees "almost ALWAYS look the same". Is the band around a localised
   object the right unit of native-resolution work, or the tiles the squint flags?
