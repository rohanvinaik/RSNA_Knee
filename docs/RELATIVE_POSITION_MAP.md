# The knee's relative position map

**Status:** recorded 2026-10-17 from Rohan's words, at his request: «Record this understanding so it's
unambiguous, then build this.» **§0 is the understanding, as it stood after his corrections of that day: read it
first and build from it.** §1 to §8 keep his words in order and the history of getting there (the designs he
rejected and why). His words are quoted «» or as block quotes, verbatim with his typos; everything else is Claude's
wording. Where this document and his words differ, his words govern.

## 0. The understanding (authoritative; read this first)

Stated after three independent readings of all his words of the day (Codex, §8.5 to §8.7), and recorded at his
order: «Make REALLY fucking sure the correct understanding is recorded in the documentation everywhere, so this
understanding is compact/new session-stable. THEN we can get to building».

1. **One 3D map of the whole knee.** «The knee is a coherent object every part of the knee sits in a fixed position
   RELATIVE to every other» · «EVERY object in the study--every bone, every tendon, every artery--is built as a map of
   RELATIVE positioning». It is a 3D object, not a flat map: «Obects are resolved in 3D with vector distances in
   magnitude and direction, which is what enables ONE map to then be translated to expected position across each of
   the three views». For every object against every other object, the 3D vector between them in the leg's physical
   space: its direction and its magnitude, the magnitude kept both in millimetres and as a proportion of the knee's
   own size («Both»).
2. **The zero.** «the bones' key slices are the established "zero" point». The bones are objects in the same web,
   with their own vectors to every other object: «Bones don't get treated like some magical reference that is never
   wrong».
3. **Key slice.** For each object, in each of the three views (sagittal, coronal, axial), the one slice where it is
   most obvious, the «best resolution of the object's full physical representation». A study's fat-bright and
   fat-dark series are different images, each taking its own slices from the one map by its own geometry; there is
   no fat-bright or fat-dark map («do NOT build it that way»). The cheap look only finds positions: «The "cheap look"
   isn't a statement of truth or knowability, it's just a cheap way to *find* these positions».
   **The three key planes construct the object's position together.** The sagittal key plane supplies its
   across-leg position, the coronal key plane its front-to-back position, and the axial key plane its along-leg
   position. Their intersection in the leg's physical space is the object's reference point for the map, including
   for the bones. Use actual acquisition geometry; never substitute one section's centroid, average centroids,
   or copy raw slice indices between images. A missing plane remains a partial position with its known constraints.
   The point localizes the object; its other observations retain shape and extent. See §8.8.
4. **The ideal, from anatomy and physiology.** «a platonic ideal representation of the relative position of
   anatomical objects across all three angles of resolution»: the vectors of a sane knee, which anatomy and
   physiology document richly («surely the problem is TOO much data, not finding sane grounding numbers»). The
   builder grounds and justifies the numbers from that knowledge, no single textbook the authority; they are never
   taken from the studies.
5. **The ONE statistical contribution.** «a range/variance in the actual data built as the ONE statistical
   contribution, to establish the variance of the accuracy of the relative measure--EVERY object's position vs EVERY
   other object, across ALL 58 studies»: for every pair, the range and standard deviation of the actual 3D vector as
   our lenses find it. It checks the ideal and never makes it: «We USE statistics, we don't fucking base everything
   off it» · «If you are building this according to 58 RANDOM fucking studies, you will build overfitted and shitty
   nonsense».
6. **A map is a guide.** «A map is a guide. An expectation, a way to establish a cheap first/obvious measure, and only
   move off it if that well-established prior is not correct.» In a study the cheap view finds the obvious objects;
   the map's vectors from them give every other object's expected 3D position; carried into each image by its own
   geometry, that says where the search for the object's key slice begins and where in the slice to look; the search
   moves off only where the study shows the expectation wrong there. The map never bends what is seen («You don't
   mis-draw a map, see you've placed Toledo 5 miles to the West, then nuke the city and re-build it to fit your
   hand-drawn map»). With every object mapped, «key slice idenitification off the squint/lossy view becomes a
   *refined* prior for looking for the exact best resolution for every element of the knee's anatomy».
7. **What it is not.** Not statistics as the base: no cohort windows, and no ranges from the 58 studies standing in
   for the ideal. Not a flat map per view or per axis. Not a privileged reference that is never wrong. Not a relation
   that "places" a part. Not perfection: «the point is a correct and discriminative set of rules that align with each
   object at least once»; accuracy and border drawing belong to the later AI parts, «which I have yet to even
   describe». Labels carry no truth: «Names can't be "wrong" because they're never "right"».
8. **Why it is the thesis.** «This is EMINENTLY aligned with the thesis. There's a whole chapter about "dimensional
   collapse" and how "one slice" is a clear and correct lossy representation of the truth» (§5).
9. **How to work on it.** Understand before recording, record before building, explain before building: «How can you
   "Fix" what you don't yourself understand correctly?». The builder drafts the anatomy from the literature: «I think
   you draft. This is basic domain knowledge. look it up» (2026-10-14).
10. **The prior is useful before it is perfect (2026-10-18).** The squint, rough leg/background bounds
    and already resolved anatomy make each dependent object's location a strongly constrained question.
    Attachments, containment, intervening space and physiological relations narrow the places worth
    reading, so the same physical structure improves discrimination and reduces expensive compute.
    «This is about establishing priors, not being perfectly correct». Fine positional and boundary
    analysis refines that useful starting region. This is foundational to the entire operation, not
    an optional speed pass. Read `docs/TARGETED_ANATOMICAL_COMPUTE.md` and his complete messages in
    `docs/conversations/2026-10-18-anatomical-priors-and-targeted-compute.md`.

## 1. His words

What the anatomical reference work is for (2026-10-17), correcting Claude, who had built and reviewed it as
statistics of one link (one bone's key slice, a cohort window for the patella):

> It's a reasoning and symbolic  approach, not statistical. Speed is one element, but relative positioning is
> another. The knee is a coherent object every part of the knee sits in a fixed position RELATIVE to every other.
> If you know where the tibia/femur have their key flice, you can roughly guess the key slice of the patella. If
> you know the position of the patella AND the tibia and femur's key slices, then muscles become way more
> certain. If you know ALL of these, then the relative position of the rest of the anatomy's key slices becomes
> ABSURDLY well-resolved. That's the point here. Not "bone then patella". It's to look at the key slice of the
> most obvious parts of the anatomy, then from there to build a relative position map for where the key slice of
> every other object sits. When we have ALL of them mapped out, then key slice idenitification off the
> squint/lossy view becomes a *refined* prior for looking for the exact best resolution for every element of the
> knee's anatomy. This is EMINENTLY aligned with the thesis. There's a whole chapter about "dimensional collapse"
> and how "one slice" is a clear and correct lossy representation of the truth

Claude's two questions, then his answers:

- Q1 (Claude): Where do the relative positions come from? Anatomy (medicine's own placements, like LaPrade's
  measurements for the LCL); or measurement (the key slices our rules find on the labelled studies, used as
  relations between parts rather than as windows); or both?
- Q2 (Claude): What is a part's key slice, and where is the map kept? Is the key slice the slice where the
  part's own definition shows it most clearly, as the bones' biggest marrow body? Is the map kept in the leg's
  physical space, so that one map serves all five views?

> 1. Relative position comes from anatomy, and the exact representation for OUR pipeline (whatever anatomy says,
>    the lenses in this project are completely novel constructions, they should be validated over the study data
>    we have
> 2. Yes, key slice is best resolution of the object's full physical representation, and keps in the leg's
>    physical space, then translated to how that maps to the five (three, really) views provided in each study

The direction this refines, 2026-10-16: «Knee anatomy is physically linked. Get the one that is cheapest to
resolve with the squint system (I imagine the tibia/femur?), Get its "key slice", use that as a normalizer, get
the statistical slice range and position estimation *relative* to the obvious elements, to make the hard compute,
the expensive process, sanely targeted where they likely are».

## 2. The first restatement (accepted at the time; superseded by §0 where they differ)

- The knee is one coherent object, so its parts' key slices sit in fixed positions relative to each other.
- Start from the parts the squint shows most plainly: the femur's and the tibia's key slices.
- From those, the patella's key slice can be roughly placed.
- Each part placed adds another constraint. With the bones and the patella known, the muscles are far more
  certain, and once everything is known the rest are pinned.
- The finished map, every part's key slice relative to every other part's, then becomes a refined prior. The
  squint's cheap guess at a key slice is sharpened against the map, and each part's exact best-resolution slice is
  sought there.

## 3. The terms, from his answers

- **Key slice:** the best resolution of the object's full physical representation. The bones' key slice as the
  reference already reads it is one instance: the slice of the bone's largest supported marrow body, named as
  that bone by the lens (`select_reference`).
- **Where the map is kept:** in the leg's physical space (the scanner's millimetres of the one leg every series
  of a study shows), then translated to the views each study provides: three orientations (sagittal, coronal,
  axial) across its five series.
- **Where relative positions come from:** anatomy. The lenses of this project are novel constructions, so each
  relation's exact representation in our pipeline is validated over the study data we have.

## 4. What it is not (Claude's wording of his correction)

- Not statistics of one link. «Not "bone then patella".» The first build took the cohort's quartiles of the
  patella's offset from one bone's key slice (`PATELLA_FROM_REFERENCE_MM`); the joint pass looked for cohort
  windows of the joint's pointers against the same reference and found none (`JOINT_FROM_REFERENCE_MM`, empty).
  That framing is recorded in `docs/ANCHOR_RELATIVE_SEARCH.md`. The patella's loose window and the joint's empty
  range are what a single statistical link gives; they say nothing against the map, which was never built.
- Not a range taken from our own outputs alone: which part sits where relative to which is anatomy's; the study
  data validates how that relation reads through our lenses.

## 5. Why it is the thesis (Claude's reading, which he called eminently aligned)

- **The collapse.** A flat picture at a well-chosen depth holds an object whole, so one slice is a correct, lossy
  representation of a part. *What an <Object> Is* §4.2: «Lenses at different depths are the three-dimensional
  structure itself»; here, the parts' key slices at their own depths are the knee's structure.
- **Lossy lenses, applied to place.** Each part already placed is a lossy lens on where the next one is: alone it
  says "roughly here", together they resolve it. «the "truth" being recapitulated from addative and subtractive
  superposition of the lossy lenses to resolve the higher-dimensional truth». And his corpus line: «If a domain
  space is defined and constrained, information reveal in one axis/dimension is *implicitly* information reveal
  about the whole rest of the domain».
- **Reasoning over objects**, the part he said is easy once recognition is done: objects are «heavily constrained
  by physics», two cannot occupy the same space, and the knee's parts keep their relations.

## 6. What already exists that it builds on (Claude, from the source)

- The anchors' first key slice: `select_reference` (`src/knee/collapse/reference.py`) finds the femur's or the
  tibia's key slice on one series without fat suppression and keeps its plane and the bone's places in the
  scanner's millimetres.
- Physical coordinates: every slice's frame in millimetres; `reference_position` separates a plane's depth from an
  in-plane landmark; offsets are signed by physical direction, never by slice index.
- Links made one at a time by hand, each from one parent: the fibula from the tibia; the LCL's slice from the
  fibula's attachment (LaPrade 2003); the semimembranosus group at the tibia's top (LaPrade 2007); the retinacula
  through the patella's centre; the biceps from the fibular head.
- Each object's observations by series and slice, native, laid and projected (`objects[study_uid]`).

## 7. What the build must deliver (his words)

- The key slices of the most obvious parts first; from them, a relative position map for where the key slice of
  every other object sits; with all of them mapped, key-slice identification off the squint becomes a refined
  prior for the exact best resolution of every element.
- «Full compute for building and diagnosis is fine, but the production path should be computationally minimal».
- «We need the capacity to recognize, accuracy and completeness is for AI».

## 8. The build

Written as it is designed and built, each decision with its grounding in his words, the anatomy and the pictures.
Claude's design, 2026-10-17, as corrected by him the same day (§8.0).

### 8.0 His corrections to the first design (2026-10-17, verbatim)

To Claude's first design, which counted a section's depth only where a cheap look had chosen its slice, and which
proposed setting aside key points whose "name" was wrong:

> 1. The "key slice" is just the one slice, seperately for each of the 3 different views (as a standard
>    "normalizer", is the same for fat-bright vs fat-dark--they're looking at the same angle of the knee) where the
>    anatomy is most obvious. The "cheap look" isn't a statement of truth or knowability, it's just a cheap way to
>    *find* these positions, a common-sense grounding of position. You can see it yourself--the "cheap look"
>    works, common-sense reasoning allows you to resolve knee anatomy as high-level features trivially
> 2. Explain. What do you mean "names can be wrong"? Names can't be "wrong" because they're never "right". Object
>    recognition is a visual processing/reasoning pipeline. Switching the labels to German doesn't inform the
>    correctness of the visual reasoning process

To Claude's restatement, which said one slice is shared by the fat-bright and fat-dark series:

> 1. No you misunderstood. Fat bright and fat dark are DIFFERENT images in each specific study. But globally, when
>    we're establishing this mapping of knee anatomy, there isn't a special "fat bright" vs "fat dark" knee anatomy
>    relative positioning map. What you are describing is FUNDAMENTALLY invalid and would destroy everything, do NOT
>    build it that way
> 2. Oh good GOD not this again. Why are you so obsessed with statistics? I've told you so MANY times, the point is a
>    correct and discriminative set of rules that align with each object at least once. When it comes to accuracy,
>    border-drawing parsimony, etc, that's the job of the AI parts, which I have yet to even describe. Why are you
>    trying to solve this without AI? Obviously, if cheap and deterministic systems could solve problems like this,
>    we would have done it. Why even waste the compute required for ML? I have a classical AI solution, and I will
>    share it with you, but trying to make it perfect right now is doomed to fail. Just build it, then I will come

What they fix (Claude's wording of his words):
- **One map.** The map of the knee's anatomy is one, in the leg's physical space. There is no fat-bright or
  fat-dark map. In a study the fat-bright and fat-dark series are different images, each with its own slices; each
  image gets its own key slice for an object by carrying the map's position into that image's slices. No slice is
  shared between two images.
- **The key slice** of an object, in each of the three views, is where the object is most obvious. The cheap look
  is a cheap way to find that position, a common-sense grounding of position, never a judge of whether a section
  counts: every section the run resolved counts, however its slice was found.
- **No outlier handling.** The point is a correct, discriminative set of rules that align with each object at least
  once; accuracy and border-drawing parsimony are the AI parts' job. A label is a handle and carries no truth.

### 8.1 The pieces, each with what it rests on

1. **Key slice.** For each object, in each of the three views, the slice where it is most obvious («best resolution
   of the object's full physical representation»), kept in the leg's physical space and translated into each image
   of a study. *Rests on:* his answers of §1 and §8.0. Claude's working reading, not his words: "most obvious" found
   by the object's existing anatomical definition and the pictures, through a cheap reading that exposes it.
   Largest supported section may be a useful pointer where justified; it is not a universal definition of
   obviousness. The object's position is constructed from its sagittal, coronal and axial key planes together,
   using their physical intersection. Each plane's source, reason and outcome remain addressable. This also
   applies to the bones that establish the initial zero. The single-section-centroid reading is withdrawn (§8.8).
2. **The map: ONE map of the knee in 3D, every object against every other object.** «This is a 3D object, not a 2D
   flat map, so it has magnitude AND direction [...] Obects are resolved in 3D with vector distances in magnitude and
   direction, which is what enables ONE map to then be translated to expected position across each of the three
   views.» For every pair of objects («EVERY object in the study--every bone, every tendon, every artery»), the 3D
   vector from one to the other in the leg's physical space: its direction and its magnitude, the magnitude kept both
   in millimetres and as a proportion of the knee's own size («Both»). The bones' key slices are «the established
   "zero" point»; the bones are objects in the same web, with their own vectors to every other object: «Bones don't get
   treated like some magical reference that is never wrong». *Rests on:* his words in §8.6 and §8.7.
3. **The ideal, from anatomy and physiology.** «a platonic ideal representation of the relative position of
   anatomical objects across all three angles of resolution»: each object's vector to each other object in a sane
   knee, which anatomy and physiology document richly («surely the problem is TOO much data, not finding sane
   grounding numbers»). Claude assembles and justifies the ideal from that knowledge, no single textbook the authority
   («If you're asking if I have one favorite textbook, I do not»); never from the studies' observed offsets. *Rests
   on:* «Relative position comes from anatomy» · «I told you to base this on knee anatomy, NOT on statistics».
4. **The ONE statistical contribution.** «a range/variance in the actual data built as the ONE statistical
   contribution, to establish the variance of the accuracy of the relative measure--EVERY object's position vs EVERY
   other object, across ALL 58 studies»: across all 58 labelled studies, for every pair of objects, the range and
   standard deviation of the actual 3D vector as our lenses find it (how the direction's variation is summarized is
   Claude's to choose and justify). It checks the anatomical ideal («confirmed statistically»), whose agreement is
   measured, never assumed; it never supplies the ideal and never decides which relations exist. *Rests on:* «We USE
   statistics, we don't fucking base everything off it» · «If you are building this according to 58 RANDOM fucking
   studies, you will build overfitted and shitty nonsense».
5. **Translation to the images.** From the objects found and the one map's vectors, each other object's expected
   position in 3D; carried into each image by that image's own geometry (sagittal, coronal and axial, fat-bright and
   fat-dark alike), it says where the search for the object's key slice begins, and where within the slice to look. It
   guides the search: the key slice, where the object is shown most fully, is still what the search finds. *Rests on:*
   his answer 2 of §1, correction 1 of §8.0, and §8.7.
6. **Use: a map is a guide.** «A map is a guide. An expectation, a way to establish a cheap first/obvious measure,
   and only move off it if that well-established prior is not correct.» In a study the cheap view gives the first,
   obvious positions; the map says where each object's key slice is expected, given the others; the search for its
   exact best resolution starts there, and moves off only where the study shows that expectation is not correct
   there. The map never changes what is observed: «You don't mis-draw a map, see you've placed Toledo 5 miles to the
   West, then nuke the city and re-build it to fit your hand-drawn map.» He states no threshold for "not correct";
   Claude's reading for the build: where the object is not found at its expected slice, the search broadens, as the
   existing searches do. *Rests on:* his words in §8.6; «a *refined* prior for looking for the exact best resolution
   for every element»; «the production path should be computationally minimal».
7. **Building versus production.** The studies that validate the map's expression are read with a run that searches
   fully (every pointed plane read, no window), as development work; production runs with the map's narrowing.
   *Rests on:* «Full compute for building and diagnosis is fine, but the production path should be computationally
   minimal».

### 8.2 What the study data holds for checking

Native resolutions over the 58 labelled studies in the full-search baseline
(`data/readings/collapse-20261016/search-priors/cohort-run-final`), counted 2026-10-17: the joint 57 studies, the
tibia 46, the patella and the suprapatellar fat 40, the femur and Hoffa's fat pad 39, the PCL 36, the two fat pads
above the patella 34, the tibial cartilage 28, the joint fluid 24, the femoral cartilage 22, the menisci 14 to 21;
then 9 to 11 (the gastrocnemius heads, the iliotibial band, the MCL, the anterior recess and its lining, the
semimembranosus, the fibula), 3 to 6 (the extensor tendons, the bursa, the retinacula, the capsule, the ACL, the
semitendinosus) and 1 to 2 (the popliteal vessels, the sartorius, the gracilis, the LCL, the popliteus, the biceps).
These counts say how many studies can check each relation's expression; they say nothing of what the relations
are, which is anatomy's.

### 8.3 Order of work

1. The map's pieces as one small module (each object's key slices, the anatomical ideal as 3D vectors between every
   object and every other, each vector's range and variance over the studies, the translation into each image), with
   tests.
2. The key slices of every object in every labelled study, from the full-search baseline; drawn for the proof and a
   few other studies, and looked at.
3. The ideal from anatomy and physiology, as 3D vectors between every object and every other; then each vector's
   range and standard deviation over all 58 studies, as the one statistical contribution; looked at.
4. Production: the families that search read first where the map predicts, in order, measured against the baseline
   for work and for what is resolved.

### 8.4 Historical single-section point experiment — withdrawn by §8.8

**The construction below is historical evidence, not the map's current position definition.** Its pictures and
tables show that experiment's outputs. They do not demonstrate the required three-key-plane construction.
The prohibition below on combining views and the single-section centroid are withdrawn. Preserve the artifacts;
replace the implementation rather than relabelling its points.

Tool: `scripts/key_points.py` (development only: it reads a run's receipts and saved arrays, and each slice's frame
from the study's headers). Table over the 58 labelled studies, from the full-search baseline:
`data/readings/collapse-20261016/relative-map/key-points-cohort.json`. Pictures of the proof, one per part (its
key section with its key point, and the point carried onto every other series' nearest slice):
`data/pictures/collapse-20261016/relative-map/key-points/94649149/`.

- **Which sections count.** (First built counting a depth only where a cheap look had chosen the slice; he
  corrected it, §8.0.) Every section the run resolved counts; the key point is the centroid of the object's most
  obvious section, the largest, however its slice was found.
- **One section, never coordinates mixed across series.** On the proof the joint's fluid had its coronal key
  section in the lateral gutter and its sagittal one in the front recess; taking x from one and y from the other
  put the point inside the femur. A part that is not one compact body (the joint's fluid taken whole, the joint
  space, the field's tissues, the unsided meniscus) gets no key point; its bodies that are named on their own (the
  front recess) do.
- **Looked at.** On the proof every compact part's key point, carried onto every other series' nearest slice, lands
  on the part wherever that series reaches it (the medial gastrocnemius head lies 4.5 mm behind the coronal stacks'
  last slice).
- **What the data holds.** 2,050 sections (one without a readable frame), 841 key points. Across the leg (x), a depth
  chosen through the stack for the PCL in 35 studies, the patella in 25, the tibia in 24 and the femur in 14 (the
  fat pads named on the patella's planes share its slices, so they are not independent of it); front to back (y)
  for the femur in 25, the tibia in 22, the cartilages in 17 to 19, the menisci in 13 to 14, the MCL and the fibula
  in 9; along the leg (z) for no part, since no profile reads the axial stacks, though the key section's in-plane
  height is known for nearly every part. The back of the knee (the heads, the tendons, the vessels) has in-plane
  positions only.
- **The anchors.** The bones' cheap profiles already hold the femur's own anatomy through the depth
  (`data/pictures/collapse-20261016/relative-map/bone-profiles/94649149.png`): on the proof's sagittal stack two
  humps, the condyles, with the notch's dip between them at the middle slice; on its coronal stack the front, the
  full width at the condyles (the key slice, 4,800 mm²) and the back of the condyles. The tibia is one hump. A
  bone's centroid along the leg depends on how much shaft the scan holds, so along the leg the anchors are the
  femur's lower end and the tibia's top, which the bones' family records (the joint line); across the leg, the
  condyles' humps and the notch's dip; front to back, the femur's humps and the bones' key slices. (These are
  observations of the bones' cheap profiles, not a definition of the zero: the zero is the bones' key slices, and the
  bones are objects in the same web, §0.)
- **No outlier handling.** (Claude had proposed setting aside key points whose "name" was wrong; he corrected it,
  §8.0: a label carries no truth, and accuracy is the AI parts' job.)

### 8.5 Withdrawn: relations measured from the studies (2026-10-17)

Claude first wrote §8.1 as: every pair of parts is a relation along each axis, its range the smallest to the
largest offset between the two parts' key points over the 58 labelled studies, and a part's place the intersection
of those ranges, the relations seen in the most studies first; it labelled that as resting on his words, and coded
it (`measure_relations` in `src/knee/collapse/relative.py`, uncommitted, used by nothing). Anatomy had shrunk to the
single premise that positions are fixed. The fault was the studies as the source of each relation, with no anatomical
ideal behind it; every object against every other object is what he asks for (§8.6). His words:

> I told you to base this on knee anatomy, NOT on statistics

> We are well over halfway through this session, you have not ONCE built what I fucking told you to build. [...] Why
> the FUCK are you building statistical slop. This is NOT fucking "machine learning". If you are building this
> according to 58 RANDOM fucking studies, you will build overfitted and shitty nonsense, and destroy EVERYTHING. Why
> the hell don't you get this. I LITERALLY told you "this is not statistics", so you built...statistics? We USE
> statistics, we don't fucking base everything off it. Fix the record you've made, use the codex consult to correct
> your understanding first. THEN we can build, but only after you explain what you understand, and don't fuck this
> up. It's EXTREMELY simple, I don't get why you are unable to understand this

> No, i said consult FIRST, THEN change the record. How can you "Fix" what you don't yourself understand correctly?

The Codex consultation (one independent voice, GPT-6.1 Sol, model-only; prompt, Claude's prior reading and its
answer in `data/readings/collapse-20261016/relative-map/codex-consult-20261017/`) agreed with Claude's corrected
reading on the foundation: «construct the localization relationships from anatomy, express them through the
project's lenses, and validate that expression on studies». It flagged as Claude's own, not his: the centroid of the
largest section as the key point; every pair, range intersection and ordering by study counts; the femur and tibia
as a fixed starting pair (his words: «I imagine the tibia/femur?»); and the anatomical examples Claude listed, which
need their anatomical sources.

What he answered next, and what stays open: §8.6.

### 8.6 Every object against every other; the one statistical contribution; a map is a guide (2026-10-17)

Claude's explanation after the first consultation had said the relations are "not every pair of parts", treated the
bones as the reference the others are placed from, and asked how far "a relation places a part". His answer,
verbatim:

> 1. Yes, the bones' key slices are the established "zero" point, and relative positioning of every anatomical element
> is relative to EVERY OTHER ANATOMICAL OBJECT. I still don't think you're doing this right, I want to make sure you're
> not about to fuck this up. EVERY object in the study--every bone, every tendon, every artery--is built as a map of
> RELATIVE positioning, with a RELATIVE map in the three views. Bones don't get treated like some magical reference
> that is never wrong--THEY also get a full map of relative positioning informed from anatomy and confirmed
> statistically (to establish variance and standard deviation). I need you to go back to codex again, the way you're
> writing makes me think you STILL don't get it. We are building a platonic ideal representation of the relative
> position of anatomical objects across all three angles of resolution, with a range/variance in the actual data built
> as the ONE statistical contribution, to establish the variance of the accuracy of the relative measure--EVERY
> object's position vs EVERY other object, across ALL 58 studies.
> 2/3. Huh? A relation "place a part"? A relation doesn't "place a part". A relation is a...map? You don't mis-draw a
> map, see you've placed Toledo 5 miles to the West, then nuke the city and re-build it to fit your hand-drawn map. A
> map is a guide. An expectation, a way to establish a cheap first/obvious measure, and only move off it if that
> well-established prior is not correct. But across ALL the objects we have, EVERY object relative to EVERY other
> object, the map should be pretty fucking correct. Knees are sane objects. Across EVERY object, in every "cheap view"
> resolution, this should be *obvious*. Go back to codex, take ALL my words about this in this session to that same
> conversation with codex, make DAMN sure you get this right and come back to me

The second consultation (the same Codex thread, given all his words of the session verbatim; files in
`data/readings/collapse-20261016/relative-map/codex-consult-20261017/`, the `-2` set) found Claude's updated reading
substantially matched his words, with these held to: "confirmed statistically" is a check whose result is measured,
not assumed; the variance belongs to each pair's relative position, not to each object alone; "the map should be
largely correct" and "each object found narrows the rest" are expectations to be checked, not guarantees; the list of
objects is Claude's, his is «EVERY object in the study»; and «the largest remaining problem» was Claude's suggestion
that the studies might supply the ideal's central values, which his words do not authorize.

Open, for him (asked 2026-10-17): (1) the ideal map's numbers, the relative positions of a sane knee: from what
anatomical reference or construction, the 58 studies supplying only the observed range and variation; (2) whether the
relative positions and their variation are kept in millimetres, as proportions of the individual knee's size, or
both. Answered: §8.7.

### 8.7 One 3D map of vectors; the ideal from anatomy and physiology (2026-10-17)

His answer, verbatim:

> 1. ...anatomy and physiology? If you're asking if I have one favorite textbook, I do not. But, like, is this
> actually a hard problem? It's 2026. surely the problem is TOO much data, not finding sane grounding numbers?
> 2. Both, and your question is problematic. Position is inherently both? Like, you DO realize that I said "map", but
> that was colloquial. This is a 3D object, not a 2D flat map, so it has magnitude AND direction, not just a flat mm
> map? Do you still not get this? Obects are resolved in 3D with vector distances in magnitude and direction, which is
> what enables ONE map to then be translated to expected position across each of the three views. Take my words, my
> exact words, AGAIN to the same codex chat, make sure you get what I'm talking about

What Claude had kept wrong: "in each of the three views" read as a separate relative map per view, and positions as
flat per-axis offsets. The third consultation (the same thread; the `-3` files) found the central structure now
right: «one anatomical knee in 3D, with every object related to every other by magnitude and direction, translated
into the study's views»; «Both» answers millimetres AND proportions of the knee's own size, with direction an added
requirement; the grounding numbers are Claude's to assemble and justify from anatomy and physiology; the bones' key
slices are the zero, and no new definition (a centroid) may be slipped in under that word without respecting what the
key slices are; translating the map into a view guides where to look, and the key slice is still what the search
finds; how directional variation is recorded is Claude's to choose and justify. It found no question left that only
he can settle.

### 8.8 Three key planes make the 3D position — correction, 2026-10-17

Rohan's words, already recorded in §8.0:

> The "key slice" is just the one slice, seperately for each of the 3 different views
> [...] where the anatomy is most obvious.

And §8.7:

> Obects are resolved in 3D with vector distances in magnitude and direction, which is what
> enables ONE map to then be translated to expected position across each of the three views.

The side note Rohan relayed identified the deviation: the point was made from the centre of one biggest
cross-section instead of the object's key slices in all three views. Inspection of scripts/key_points.py
confirmed the substitution. Femoral centroid drift with shaft coverage was a symptom of that substitute.

The corrected operation, approved by «Fix the documentation, then build please»:

1. Find each object's key plane independently in sagittal, coronal and axial views. A sequence changes the reading,
   not the anatomical map. Keep acquisition geometry and the selected planes' provenance.
2. Each plane supplies one physical depth constraint. Together they define the object's reference position.
   In aligned views these are the three coordinates; for oblique acquisitions solve the plane equations
   in physical space. Keep missing, tied or geometrically indeterminate constraints explicit.
3. Construct every object-to-object displacement vector from those positions. Bones remain objects in the same
   map; their key planes establish the initial reference. Keep millimetres, anatomical proportions and direction.
4. Ground the ideal in anatomy and physiology. Across all 58 studies measure actual pair-vector range and
   variation. These measurements validate the pipeline's expression and never author the ideal.
5. Translate expected 3D positions into each acquisition's own slice and in-plane search location. Use the map as
   a guide and follow observed anatomy when the expectation differs.

The invariant through the real entry point is **key planes → physical 3D position → all-pairs vectors →
expected slice AND in-plane location**. A three-coordinate centroid, disconnected per-view maps, cohort windows,
or unused geometry code does not implement it. Perfect boundaries, exhaustive recovery and later AI are not
prerequisites for demonstrating this operation.

### 8.9 First anatomical reference and corrected geometry, 2026-10-17

The source and author choices are recorded in `docs/ANATOMICAL_MAP_REFERENCE.md`. The reference uses the
external SPL knee atlas and explicit constructions between the sourced anatomical neighbours; no competition
study supplies its numerical centres. `src/knee/collapse/anatomy_map.py` exposes one catalogue with 43 semantic
object slots, 39 defined sites and four named diffuse-field reference gaps. Each ordered-pair query uses those
same sites, bones included. Scaling uses an explicitly known knee breadth or retains reference millimetres.

`src/knee/collapse/relative.py` now implements the three-plane physical solve, actual pair vectors and native
slice/in-plane placement. `scripts/key_points.py` requires explicit selected planes rather than using its
diagnostic section centroids. Without those planes it reports partial positions. The old single-section
artifact remains historical. Tests and a development CLI demonstration establish the geometry component;
the demonstration's by-eye axial choices are labelled as such and do not establish automatic selection.

Automatic bone key-plane selection and guided search are now connected through `scripts/run_interiors.py`;
the source-matched verification checkpoint is §8.11. The reference catalogue and geometry alone do not
complete recognition, and a geometrically complete position is not anatomical validation. Missing independently
selected planes remain explicit. The 58-study measurement is recorded at that checkpoint when completed.

### 8.10 The production operation, 2026-10-17

Rohan's clarification while this build resumed:

> this is meant to be a PRODUCTION pipeline, that does a thing and works for a competition.
> Take in studies with knee anatomy images, spit out objects as coherent recognition output for every anatomical feature

And:

> That's also why the CI tools exist. Vulture finds dead code. Telemetry tracks heavy and/or repetitious compute. ETC

The deliverable is the existing `scripts/run_interiors.py` operation, from study input through the
saved per-study `objects` output. Geometry helpers, catalogue entries, passing unit tests, and pictures
alone do not complete it. The same operation computes shared readings, resolves the anatomical parts,
records their native/laid observations and projected targets separately, refines the one physical map,
and persists addressable evidence.

The production caller supplies the complete anatomy catalogue to `describe_objects`. A feature without
an observation or recorded refusal has the explicit `no_observation_record` saying, never an absence
claim. Existing observations and their actual refusals remain intact. Every ordered map pair is kept
as a complete vector or an explicit unresolved pair. The whole map is saved once in the study's
`study_map.json`; its receipt summary points to that file.

Integration is checked through that entry point and its actual pictures. Vulture findings identify
consumers still owed; the telemetry ledger and runtime instruments check whether shared readings
really run once and reach their consumers. An advisory check's findings remain obligations to inspect,
even when the blocking gate passes. A helper is not complete merely because it is imported and tested.


### 8.11 Connected search and CI checkpoint, 2026-10-17

The production entry point now passes the one `MapContext` into the patella, joint, recess and fibula
searches. Each consumes expected native slices and in-plane locations. Existing image definitions decide;
the anatomical map never paints a boundary or converts a failed observation into absence. The bone and
patella coarse scouts share cached block medians and enclosed-section readings. Native, laid, reading,
projected-target and unresolved observations remain distinct in the saved output.

For fibula and recesses, a usable map supplies the initial cheap profile window. A maximum at the edge of
what was read walks into adjacent unread slices until its run's peak is established. Physical in-plane
boxes select relevant supported runs; every tied maximum and applicable end confirmation of those runs
is retained. If native recognition does not answer there, only the unvisited remainder is profiled before
trying the remaining pointers. Expected points are projected using every candidate slice's own frame,
including allowed slices other than the point's nearest slice. Production selection within that justified
neighbourhood is intentional narrowing, not a certificate of a global maximum over unread anatomy.

The old `select_reference` calculation had no reader after the production map replaced the single-bone
cohort path: the actual ledger listed all its fields unread. The call and then its now-test-only function
were retired, with source and dedicated tests retained under
`data/readings/collapse-20261017/three-plane-map/retired-single-reference/`. Two geometry helpers with no
production caller, `plane_distance` and `compose`, were likewise retired under `retired-unused-geometry/`.
No anatomical definition was withdrawn. Development reference readers remain historical tools.

Verification: the full gate in `resume-map-consumers/gate-final.log` passed with 720 tests. Ruff,
Import Linter, deptry and `ty check src tests` passed. Vulture still lists atlas metadata, contract
fields and the image-placement diagnostic field, plus unused locals in older tests; those advisory
findings were not hidden by an allowlist. A separate check of `scripts/run_interiors.py` retains older
advisory type findings; do not describe the entire script as type-clean. The newly added coarse scouts'
optional-volume and frame narrowings were corrected without changing their anatomical selectors.

The real entry point ran the proof and bursa studies with drawing. Actual proof sagittal/coronal fibula,
sagittal/side/axial recess and retinacular pictures were inspected. Both studies keep all 43 semantic
feature slots, each with observations or an explicit unresolved saying. Their observation counts by
feature/provenance/kind are unchanged from `resume-integrated` despite the narrower recess search; this
is bookkeeping evidence, not a claim that every saved array or every study is unchanged.

The inspected proof map has three geometrically complete positions (femur, tibia, patella) and 40 partial
positions. The patella's sagittal and axial localization is clear; its coronal coarse section overreaches.
On the bursa study the original sagittal patella support is a small femoral fragment and propagates into
femoral coarse sections. Its geometrically complete result is not a validated patella. This is retained
as an explicit observed limitation, not a reason to withdraw the competent definition or tune it to this
study. More independently selected orientations are still owed for the other objects; catalogue coverage
is not complete 3D recognition. Whole-object encoding, volume, precision and diagnosis remain downstream.

Source hashes, fresh proof/bursa receipts, the labelled run, pair-variation outputs and runtime evidence
belong in `data/readings/collapse-20261017/three-plane-map/resume-map-consumers/`. Canonical measurements
remain untouched; development drawing refreshed the standard picture directories. Statistics report
actual observed vectors and missing ends only; no measured centre becomes an anatomical ideal.


Final verification for this checkpoint: `resume-map-consumers/gate-complete.log` passed with **723 tests**.
A fresh no-drawing proof/bursa run is in `final/`. The 58 labelled studies completed with 336 series records,
no unread studies, all 43 feature slots, and 58 saved study maps. The retained image outputs were then
fed through the actual `describe_objects` consumer again to propagate existing definition/own-slice
refusals into otherwise generic missing-observation entries: 388 slots across the 58 studies. No image
measurements were repeated or changed; the original receipt is retained as
`cohort/interiors/receipt-before-refusal-propagation.json`. Fresh proof/bursa objects and every saved-array
digest match their refreshed cohort records (`final-vs-cohort.json`). Source versions and the bounded
post-cohort output-only change are pinned in `source-hashes-complete.json` and `source-change-after-cohort.json`.

The pair-variation measurement is now executed, not just implemented: `pair-variation.json` and `.csv`,
with `cohort-map-summary.json`. Geometrically complete positions: femur in 34 studies, tibia in 29,
patella in 36; the other 40 slots have none yet. Of 1,806 ordered pairs, femur↔tibia has 24 measured
studies, femur↔patella 23, tibia↔patella 21; the other 1,800 pairs retain zero coverage and explicit
missing ends. Direction needs a known knee side and proportions need a known scale, so their metric
sample counts can be smaller. These are observations of the current lenses, not validation of every
anatomical assignment and never new ideal positions or hand-tuned cutoffs.

The Sonnet API address audit of the preceding `resume-integrated` two-study checkpoint checked 466
observation references and 1,950 saved-array digests with zero address/digest failures. Its explicit
unsupported checks include target-count reconstruction, some axial depth bounds and medical correctness.
It found specific refusals hidden by generic `no_observation_record` placeholders; the output correction
above resolves that finding. Artifact references still require the caller's interiors/main run roots,
and a native reading can live in its source artifact even when it describes another series. The audit
is source-version-scoped, not a verdict on the entire build. Prompt, script, negative controls, report,
metadata and **$2.5135639** recorded cost are in
`data/readings/collapse-20261016/api-build-and-search-priors/child-output-address-audit/`.

The actual no-drawing CLI also ran under cProfile (`proof-production.pstats`,
`production-profile-summary.json`): 35 lens calls, 17 saves, the axial coarse bone scout once and the
patella cross-orientation scout once; no retired single-reference call. Its timings overlapped the
end of the cohort run, so this is a call/work diagnostic, not a paired wall-clock speed-up claim. The
receipt's once-cache counts retain actual handoffs. The remaining task is the other objects' independently
selected key orientations and their guided native consumers; the pipeline's 43 slots do not imply that
those missing measurements have been made.

### 8.12 Fibula: its missing axial key plane, 2026-10-17

`fibula_key_planes` is connected to `measure_study`, after the existing sagittal/coronal fibula
recognition and before its main records are written. It adds the missing independent axial reading;
it changes no anatomical definition, lens constant or reference-atlas site.

Each native fibula main section supplies its physical pixel places, frame and slice thickness.
Those places are location seeds only. Their actual voxel extents identify the axial slabs to read,
using each target slice's own frame and thickness. On those slices, the existing shared 2 mm block
median and enclosed-section readings measure the axial image. The whole enclosed body holding the
fibula seeds is eligible; a body also holding the carried tibia's seeds is refused, never cut apart.
The largest competent section supplies the axial key plane, with all exact largest ties retained.
No section centroid or predicted slice supplies this plane.

All sources feed one scout per target axial series. The same `coarse_axial_blocks` and
`coarse_axial_depth` cache entries used by bones and patella are handed on. Actual slices, block grids,
seed pixels, tibia seeds, section masks, areas, statuses and physical frames are saved under
`a4_fibula_coarse_<full target series uid>_*` in the first native fibula's main artifact. Its
`fibula_key_planes` record identifies each target series and its refusals. Observations address that
artifact and packed boolean row while naming the target axial series, and remain native **readings**,
not full fibula boundaries. The later native/laid/axial observations are merged with them, never
overwritten. Missing volume, empty volume, unavailable geometry/thickness, absent sources and shared
sections remain distinct named reasons. The physical fibula value has a matching telemetry producer
and consumer.

The actual no-drawing proof run selects sagittal 30, coronal 22 and axial 1. Their physical plane
equations jointly give the fibula's position; the saved map now has four complete positions and twelve
complete ordered pairs, with the other ends explicit. The acquired images and all ten axial scout
readings were inspected. Slice 1 shows the separate fibular head beside the tibia; its coarse outline
is irregular and contains a hole. Small fragments on higher slices remain readings, not new anatomy
claims. This meets the competent demonstration criterion without a boundary-perfection campaign.
The scout only examines slabs reached by the source sections; it claims no global maximum over
unread slices and no full volume.

Evidence is in `data/readings/collapse-20261017/three-plane-map/fibula-key-planes/`, including
`production-three-planes.png`, `production-all-axial-readings.png`, the actual `production/` receipts,
`production/preservation.json` and `production/profile-summary.json`. Across the proof and bursa runs,
all 1,902 earlier saved arrays match by digest, all earlier assignments, main selections, observations
and refusals remain, and other objects' grouped outputs match. The proof retains 35 lens computations
and 44 coarse block/depth computations; the scout reuses ten coarse readings (handoffs rise from 13 to
23), adding no native lens or coarse image computation. The measured scout call takes about 0.20 s
over the two-study profiled run; that is a work diagnostic, not a paired speed-up claim. The final
gate passes 745 tests. Import and dependency checks and `ty check src tests` pass; Vulture retains the
existing advisory declarations plus the new `autouse` test fixture, whose pytest consumer was checked.
The standalone script type scan retains older findings; the new function has none in that scan.

Sonnet implemented the bounded scout and tests over the authorized API path; the lead supplied its
mechanism, wired it, checked the actual images, corrected missing/empty-volume reasons and the
telemetry producer, and verified preservation. Runner metadata records **$2.6667196** in
`data/readings/collapse-20261016/api-build-and-search-priors/child-fibula-key-plane/`.
The worker's own report says it incurred no API cost and had not wired the function: those statements
describe neither the parent runner's billing nor the final integrated state. Preserve that report as
worker provenance; use the runner metadata and lead's measured checkpoint for current status.

The fixed-source labelled refresh is complete in `fibula-key-planes/cohort/`: 58 studies, 336 series,
58 maps and no unread studies. Every study retains all 43 declared catalogue slots. The earlier
unsided `cartilage` observation also remains in the same 19 studies; those receipts have 44 keys,
as before. No output key was removed to enforce a catalogue-size cap.

`cohort-verification.json` compares 41,816 earlier middle-record arrays and 1,466 earlier main-record
arrays by saved digest: all 43,282 match. All earlier assignments, main selections, observations and
refusals remain; other objects' grouped outputs match. All 185 new scout rows reconstruct from their
saved boolean supports with matching counts, slice/series addresses and no integer labels. The
source hashes remained unchanged throughout the cohort. `production-vs-cohort.json` also checks the
two profiled studies against the final cohort, including every newly added array and the fibula's
selected planes; all saved-array metadata and objects match. The profiled run preceded only the
missing/empty-volume diagnostic distinction and telemetry-producer correction, which change no
image measurement on these valid inputs.

The refreshed `pair-variation.json`/`.csv` contain all 1,806 ordered pairs. Geometrically complete
positions are femur 34 studies, tibia 29, patella 36 and fibula one; the other 39 catalogue slots have
no complete position yet. Twelve ordered pairs have measured coverage: the six previous pairs among
femur/tibia/patella, plus fibula in both directions against those three, each in one study. For the
fibula pairs the measured vector is retained and sample standard deviation is unknown (`null`),
never zero from a single sample. No observed vector authors the anatomical ideal. The compact facts
and catalogue comparison are in `cohort-summary.json`; its earlier diagnostic finding is marked
resolved by the lead's correction note. The remaining build work is the other objects' missing
independently selected orientations and their native consumers, with no new perfection requirement.

### 8.13 Axial joint fluid and the full build plan, 2026-10-17

The requested full build plan is `docs/FULL_BUILD_PLAN.md`. The lead recorded its reading and draft,
then consulted Fable through the direct Anthropic API before implementation. The complete prompt,
verbatim answer, source packet, usage metadata and source-grounded comparison are retained in
`data/readings/collapse-20261017/full-build/`. The consultation completed normally: 107,447 input
tokens and 13,001 output tokens, including 8,174 thinking tokens; no monetary amount was returned.
The lead adopted its address, refusal and map-refresh checks. Its proposed withdrawal of general
joint fluid, single-axial-slice premise and slice-1 stack-boundary premise were not adopted; the
comparison explains each against the human contract and actual source.

The first bounded increment exposes the patellofemoral fluid pockets already selected by the
retinacular rule. `axial_joint_fluid` runs on the existing pointed axial records and the original
retinacula main record. It retains both side masks, stores their exact boolean union in
`a4_axial_joint_fluid`, and emits source-addressed native fluid observations. It reads no new image
or lens. A failed outboard-wall minimum does not discard a measured fluid body. Measured-empty,
missing prerequisites, unreadable support and partial side observations remain distinct. Boolean
supports have no integer label; pointed rows and native slice bounds are checked explicitly.

`measure_study` offers the actual pointed planes before later fibula searches, merges existing
pending recess observations at the family boundary, and appends the new observations at the
existing merge/save points. Main-record evidence is added before its one save. The existing
definitions, numerical cutoffs, reference-atlas sites and search-confirmation semantics are unchanged.

The source-matched two-study run is `full-build/production-verified/`. Its proof selects fluid planes
sagittal 22, coronal 15 and axial 22, with the separately measured pointed axial slice 21 also retained.
The actual saved supports and acquired images were inspected in `full-build/verified-images/`.
The axial outlines follow the bright pockets beside the patella. The three-plane intersection lies
inside the femur because fluid occupies several surrounding pockets. It is the map's localization
reference, never a fluid voxel, connected body, boundary or full-volume assertion. Native masks,
separate pockets and physical geometry remain the recognition evidence; overlapping views must not
be added as disjoint volume. This observed limit neither withdraws fluid nor restores a centroid.

`fluid-verification-verified.json` reconstructs both added axial supports/counts and selected plane
geometry, and verifies that the later sagittal/coronal fibula main records actually list joint fluid
among their map anchors. All earlier decisions, selections, observations and refusals remain. Of
1,944 prior saved arrays in these two studies, 1,925 retain their digests; the 19 changes are the proof's
cheap coronal fibula profile/fine/support readings as the new guide broadens its profile by four slices.
No changed detailed anatomy support or new native lens computation is claimed. No speed-up is claimed.

Rohan's current preference is small Codex subagents first. They performed bounded evidence, inventory
and adversarial audits; the lead retained meaning, integration and image acceptance. The completed
Sonnet implementation worker's runner metadata records $1.1264589. The workers' reports are scoped
provenance; final source, real-entry evidence and the lead checkpoint govern integrated status.

The remaining Packet A measurements are the joint's axial view, the anterior recess/lining's coronal
and axial views, and the capsule's sagittal and axial views. Their existing definitions remain done;
projected targets do not supply native key planes. Then follow the other anatomical families, output
and compute closure, and the thesis's full encoding/volume stage in `FULL_BUILD_PLAN.md`. The later AI
and diagnosis mechanics still require the human's deliberately deferred specification.

The full-build labelled refresh is complete in `full-build/cohort/`: 58 studies, 336 series, 58 maps
and no unread study inputs. All 40 production-source digests stayed fixed through completion.
`fluid-verification-cohort.json` preserves all earlier assignments, selections, observations and
refusals, all 41,816 earlier middle-record array digests, and 1,720 of 1,739 earlier main-record
digests. The only 19 changes are the already inspected cheap fibula profile/support readings above.
All 11 added fluid rows reconstruct correctly: seven nonempty observations and four measured-empty
readings. Every study retains the 43 declared slots, with the earlier extra `cartilage` key still
present in the same 19 studies. `cohort-summary.json` records these computed facts.

The pair refresh retains all 1,806 ordered pairs: 20 have measured coverage and 1,786 have none.
Complete three-plane positions occur for femur in 34 studies, tibia 29, patella 36, fibula one and
joint fluid one; the other 38 catalogue slots have no complete position in this run. Fourteen pairs
have one sample, with sample standard deviation `null`. The actual vector ranges/SD are development
measurements, never fitted selector thresholds or new anatomical reference positions.

After the frozen cohort, two type-expression fixes in the new helper preserve its exact operation:
an identity typing cast on a validated slice index, and direct boolean OR/copy for its at-most-two
same-shaped selected masks. `source-change-after-cohort.json` records the equivalence and separate
source pins. A fresh real-entry proof/bursa run in `production-complete/` matches all 1,946 saved
array keys/metadata/digests, both complete study maps and all object/decision/refusal outputs of
those studies in the cohort (`production-vs-cohort.json`, `final-array-sets-and-maps.json`).
The final full gate is `gate-complete.log`: 766 tests, Ruff, Import Linter, deptry and `ty check src
tests` pass. The standalone script scan retains 41 older findings, none in the new helper. Vulture
still lists atlas/contract/diagnostic fields and older unused test locals; its two autouse fixtures
are consumed by pytest. A green gate is not a claim that these advisory lists are empty.

The public test split also ran through the real entry point, drawing off, in `test-verified/` on
the frozen-cohort source: three studies and 15 series, with no unread study inputs. Main output keeps
one record and 164 named own-slice refusals; those are not diagnoses of absent anatomy. The final
type-expression changes are justified and checked separately above, rather than silently relabeling
that earlier test run's source. The initial incorrect synthetic `Series.frames` guard was caught by
the real-entry test and fixed to `Series.slices` before the accepted cohort. The rejected incomplete
run remains in the explicitly named rejected directories; it is not part of this checkpoint.

The lead also inspected the five added nonempty rows outside the proof in
`cohort-images/outside-proof-fluid-supports.png`. The `118514…` slice-24 and `549775…` slice-21/22
supports follow anterior bright pockets, with incomplete extents retained. Both `416004…` slice-27
rows instead outline a posterior condylar rim, not the intended patellofemoral pocket. Its tissue
identity is not settled here. These two nominal `identified` rows are an observed localization error
in the existing retinacular recess selection, faithfully exposed by the bridge, not anatomical
validation. Their arrays and refusals remain; no per-study exception or new cutoff was fitted.
Seven nonempty rows therefore means seven measured supports, not seven correct anatomical results.
The competent proof demonstration remains the criterion; later accuracy/completeness work is deferred.

### 8.14 Axial capsule from the existing recess walls, 2026-10-17

The next bounded Packet A bridge is connected through `scripts/run_interiors.py`. The existing
retinacular rule already resolves the native dark outer bands beside the patellofemoral fluid
pockets. `axial_capsule_observations` gives those same bands an additional relational description:
local capsule outside that recess. It preserves each original retinaculum observation and its
exact artifact, boolean support, packed row, slice and count. No new mask, intensity cutoff,
image lens, capsule envelope, membrane thickness or full course is introduced. Projected targets,
laid masks and reading-only rows do not become native capsule evidence. Malformed addresses and
views return named unresolved results; the original rule's eligible failures retain their reasons.

`measure_study` offers the pointed capsule observations at the recess-family map boundary, before
later searches. `recess_existing` observes each original main-slice wall once and returns its capsule
description for the final append. New descriptions follow the earlier observations; original rows
stay in their exact order. A main-slice mask is addressed from its main artifact even though the
observation belongs to its axial series' middle record, as the existing retinaculum observations do.

The real no-drawing proof/bursa run is `full-build/capsule-production/`. The proof keeps four new
native axial capsule observations: medial/lateral 65/71 pixels on pointed slice 21 and 70/65 on
original main slice 22. These counts are observations, not selector constants. The existing
coronal slice-15 support is retained. The common map selects axial 21 and coronal 15; sagittal
remains `not_supplied`, with no fabricated complete position. The receipt-backed native overlays
were inspected at `full-build/capsule-bridge/capsule-proof-native-supports.png` and its two larger
axial source figures in `collapse-20261017/joint-axial/`. The lines follow the outer boundaries of
the bright recesses; the bands remain a local wall description, not an isolated histological layer.

`capsule-bridge/capsule-bridge-audit.json` compares all 24 prior proof/bursa records: all 1,946 saved
arrays and digests remain identical, no arrays are added, earlier decision keys and observation/
unresolved prefixes remain unchanged, and every new address/count reconstructs from its boolean
mask with no integer label. Each new observation matches exactly one earlier native wall source.
Image-measurement telemetry is unchanged. The proof adds 12 cached-frame handoffs for map-plane
bookkeeping and one map refinement; no image-compute speed-up is claimed. The bursa study adds no
capsule observation and its telemetry is unchanged. The entry-point description was also corrected
to describe the actual three-plane anatomical map instead of the withdrawn single-bone/cohort path.

The 58-study statistics at §8.13 predate this bridge. The next full cohort refresh follows the
accepted family wave, rather than relabelling that older measurement as current. Packet A still
needs the joint's axial view, anterior recess/lining coronal and axial views, and capsule sagittal.
The axial lining work begins as a development preview only; it is not counted as implemented here.

The stable-source full gate is `full-build/capsule-gate-final.log`: 774 tests pass, formatting and
Ruff pass, the production import contract is kept, dependency analysis and `ty check src tests`
are clear. Vulture still reports the earlier atlas/contract/diagnostic fields and older test
locals/fixtures; the advisory lists are not empty. An initial gate ran during the integration
test's edits and failed formatting plus an assertion; it is retained as `capsule-gate.log`, not
counted as the accepted verification. The stable rerun passes the actual entry-point assertion.

`full-build/capsule-test/` is the fresh no-drawing public test run: three studies, 15 series, no
unread study inputs, one main record and 164 named own-slice refusals. `capsule-bridge/
test-preservation.json` checks every earlier decision/selection and observation/refusal prefix
and all 1,855 earlier test array entries against `test-verified/`; none differ. Source pins and
checks are beside that audit. The only source change after the proof/bursa run was the module's
description of the already implemented map, before the stable gate and public test verification.

The separate standalone-script type scan (`full-build/capsule-script-types-final.log`) retains
41 earlier findings outside this increment; no new helper or test finding remains. The gate's
clean `ty check src tests` result is not a claim that all standalone scripts are type-clean.

### 8.15 Axial lining as a cavity-side object description, 2026-10-17

Rohan reaffirmed the scope: this is the computer-vision ground layer before the later AI parts;
first resolve what an <object> is. The original thesis conversation and the primary object's
thesis §§1.1–1.3 were reread. Each lens measures its stated property, and independent descriptions
recover the object together. This step extends the existing lining description to axial views;
it does not restart the definition pass or impose a precision/completeness acceptance gate.

The existing `retinacular_walls` section loop already measures the selected fluid body's outboard
edge and the dark wall minimum beside it. On a section whose wall relation holds (contiguous
minimum, darker than adjacent fluid), it now retains the fluid pixels at that outboard edge in
`retinacula_positive_inner_lining` / `retinacula_negative_inner_lining`. The same patient axes,
selected recess, accepted section and edge value are reused, with no new numerical cutoff,
full-image analysis or lens. The native mask initialized for each side is filled through its
section view, avoiding a second temporary mask. Existing wall masks, statuses and codes are unchanged.

This is the cavity-facing surface location beside the wall, described separately from the dark
wall and fluid area. It asserts neither membrane signal/thickness nor a complete surface/course.
The actual native image supplies the evidence; a projected target does not name a lining.
`recess_axial_plane` retains the pointed masks as `a3_recess_plane_medial_lining` and
`a3_recess_plane_lateral_lining`. The original main record retains the two `a2_retinacula_*_lining`
masks. `axial_lining_observations` reads their actual counts using the validated native wall's
series/slice/row address; it does not reuse the wall's count or mask as lining. Missing or malformed
support returns a named unresolved result, whereas an actually saved empty edge is a `reading`
with count zero and `observed_empty_cavity_facing_edge`, never an absent-synovium assertion.

Both production paths reach the grouped object output and the one physical map. Pointed lining
observations enter at the recess-family boundary before later searches. Original main-slice lining
observations refer to their main artifacts, as the wall/capsule observations already do. The new
lining rows append after every earlier capsule row, keeping the earlier observation prefix intact.

The actual no-drawing proof/bursa run is `full-build/lining-production/`. Four new native proof
observations are retained: pointed axial21 medial/lateral64/69 pixels, original main22 67/65.
These counts are observations, never selector constants. `lining-bridge/audit-report.json`
reconstructs all four bool masks, packed slice addresses and counts with no integer mask label;
each lining lies inside its selected same-side fluid pocket and outside the wall. Earlier arrays,
record addresses, decisions and observation/unresolved prefixes are preserved; only the four
expected lining arrays are added. The bursa study adds no native lining. The proof map retains
its sagittal plane and gains axial21; coronal remains `not_supplied` and position stays partial.

Production source and acquired images are pinned independently of the earlier DEVELOPMENT preview.
The renderer uses production-ordered `volume[21]` for the pointed rows and verifies main22's
saved acquired frame against `volume[22]`. It does not use the owner artifact's middle16 image
behind pointed21 masks. The larger native-support pictures and exact render manifest are in
`lining-bridge/rendered/`. The previous preview's misregistered frame and sparse global-nearest
attempt remain explicitly rejected development artifacts, not production outputs.

The audit retains raw telemetry: no extra lens/interiors reading or other image-measurement work;
new `axial_lining` produce/consume events describe the inline edge masks and their actual observation
consumer. Cached-frame handoffs and map bookkeeping are retained separately. No timing speed-up
is claimed. The 58-study statistics still predate these family bridges and are not restated as
measurements of this source. The next Packet A work includes lining coronal, anterior recess
coronal/axial, joint axial and capsule sagittal; the other families follow the full build plan.

The final stable-source gate is `full-build/lining-gate-final.log`: 779 tests pass, Ruff/format
pass, the production import contract is kept, dependency analysis and `ty check src tests` pass.
The standalone runner scan retains 41 earlier findings outside this change (`lining-script-types-
concise.log`); this is not a standalone-script type-clean claim. Vulture retains the older
atlas/contract/diagnostic fields and test entries; its advisory lists are not empty. The first
gate's 779 tests passed but Ruff found a late-bound row in the new test's nested support reader;
passing the row explicitly fixed that finding before the accepted full rerun.

The lead inspected `lining-bridge/rendered/analytical-production-lining.png`: yellow samples
follow the cavity edge beside the orange dark wall and cyan fluid boundary on both native slices.
`lining-bridge/objects-preservation.json` verifies identical object-key sets, unchanged other
objects, and retained earlier synovium observations/refusals. The actual public test run is
`full-build/lining-test/`: three studies, fifteen series, no unread study inputs, one main record
and 164 named own-slice refusals. All 1,855 earlier test array entries, decisions and observation/
refusal prefixes match `capsule-test/` (`lining-bridge/test-preservation.json`). Forty source
hashes stayed fixed through production, public test and final gate; pins/checks are beside the
audit. Canonical measurements and the 58-study statistics were not refreshed for this substep.

### 8.16 Coronal cavity-facing lining, 2026-10-17

Rohan asked: «Excellent, onto coronal». This continues the lining description in the deterministic
ground layer, before the human-specified AI parts. The original thesis conversation, theory,
anatomical definitions and actual source images ground this increment; the existing definitions
remain competent demonstrations, not a new precision/perfection campaign.

The existing `capsule_at_side_recesses` selects the same largest eligible white body outboard of
each meniscus beside the femur and the same dark outer wall. It now returns those shared readings
instead of discarding the side context. The original capsule union is unchanged. On each native
section nearest patient superior/inferior, keep the selected fluid's outermost pixels only if every
same-side accepted wall pixel lies strictly farther outboard. A section without selected fluid,
without a wall, or with a wall not wholly outboard retains its own `no_fluid`, `no_wall` or
`ambiguous_wall` status. Other sections are `selected`. No new signal cutoff, contact distance,
image lens, slice search or proof coordinate is introduced. Negative/positive side names refer to
LPS-x, not an assumed medial/lateral header.

The two real callers consume the same returned readings: `name_joint_boundaries` saves
`a4_coronal_lining` and its per-side recess/wall/lining masks, section axis and statuses;
`recess_side_plane` retains the equivalent `side_lining` and context for generic pointed-plane
packing. The former `axial_lining_observations` is now `cavity_lining_observations`, shared by both
orientations, preserving the axial addresses and outputs. Coronal supports are `a4_coronal_lining`
(middle) and `a3_recess_plane_side_lining` (pointed). Each observation counts its own boolean
support using the native wall's source address. Missing/malformed support is unknown; saved-empty
support is a measured reading. Coronal failures retain `coronal_cavity_face:` reasons. The old
`a2_synovium`, its codes and every prior observation remain intact. No new search question is added.

The actual no-drawing proof/bursa run is `full-build/coronal-lining-production/`. The new proof
native coronal observation is slice15, 29 pixels, with no integer label and a separate source support.
Its negative-LPS recess/wall/lining counts are 317/41/29; the positive side is 105/0/0. These are
observations, not constants. The lead inspected both the development preview and production
`coronal-lining-bridge/rendered/coronal-native-lining.png`: the yellow samples follow the bright
pocket's cavity edge facing the orange wall. The opposite pocket has no accepted wall and contributes
no lining. This describes local surface position, not membrane signal, thickness or full course.

The production map selects sagittal 18, coronal15 and axial21 for synovium; the sagittal/axial choices
are unchanged from the preceding run. Their independently measured physical planes jointly solve
the reference position. The lead inspected `rendered/synovium-selected-three-planes.png` and the
whole saved synovium map record: the intersection lies inside the femur, not on a lining pixel.
As with distributed joint fluid, retain this as a localization reference, never a membrane voxel,
boundary or volume. The native masks/geometry remain the evidence. The proof now has six complete
references and thirty complete ordered pairs; this is not complete anatomical coverage. Existing
strongest-native-support plane selection is unchanged, not a new universal best-slice definition.

`coronal-lining-bridge/audit-report.json`, `summary.json` and the lead's independent
`lead-array-check.json` preserve all 24 prior records, 1,950 prior arrays byte-for-byte, old decision
keys and complete observation/refusal prefixes. Ten expected coronal arrays and one native observation
are added. The new anchor enters the map before fibula search: its guide now includes synovium;
its actual selected slices/supports and saved arrays are unchanged. Guide metadata and map predictions
change accordingly, not anatomy masks. The bursa study adds no native lining.

Raw telemetry records the inline coronal edge producer/observation consumer, four extra cached-frame
handoffs on the proof and the expected map changes. No new lens, field, acquired-light or other image
reading is added. Retained context arrays remain explicitly unread by later stages; saving is not
a read. No timing speed-up is claimed. The actual public test run `coronal-lining-test/` completes
three studies/fifteen series with no unread study inputs, one main record and 164 named own-slice
refusals. Its entire receipts, arrays and maps match `lining-test/`; the comparison is in
`coronal-lining-bridge/public-test/`.

The stable gate `full-build/coronal-lining-gate.log` passes 785 tests, Ruff/format, production import
contract, dependency checks and `ty check src tests`. Vulture retains its advisory atlas/contract/
diagnostic fields and older test entries. The separate runner scan retains 41 findings outside the
new producer/helper (`coronal-lining-script-types.log`), not a standalone-script type-clean claim.
Forty production source hashes remain fixed through both real runs and the gate. Tests cover the
new section rule, preserved walls, missing/ambiguous sections, physical-axis transpose/reflection,
independent support counts, empty versus malformed supports, pointed slice addresses and actual
three-plane entry-point behavior. A pointed coronal lining row is wired and tested synthetically;
the proof/bursa run has no such non-middle row, so it is not claimed demonstrated there.

Canonical measurements and the 58-study statistics are unchanged for this substep; the broader
refresh follows the accepted family wave. Remaining Packet A: joint axial, anterior recess
coronal/axial and capsule sagittal. Then follow `FULL_BUILD_PLAN.md`. No new API call/cost, commit,
push or submission in this increment; small Codex workers handled the bounded producer/tests and
factual audits, with the lead owning integration and image acceptance.

### 8.17 Axial anterior recess and coherent categorical output, 2026-10-17

Rohan's full three-view production request is recorded in THREE_VIEW_PRODUCTION_EXECUTION.md.
This bounded A1 addition reuses the already validated native axial patellofemoral fluid pockets:
they lie behind the patella and in front of the femur, reach both holder regions, and describe
fluid-filled anterior recesses. `anterior_recess_from_axial_pockets` adds that cavity description
to the same saved boolean support, retaining the fluid identity, source geometry, count, packed
row and named decision. It reads no image and makes no mask. Empty support stays a reading;
unknown source stays unknown. It claims neither the whole cavity envelope nor suprapatellar extent.
Both pointed and original retinacular main paths are connected; the pending family observations
enter the existing map boundary before later searches, and append after the prior observation prefix.

The real no-drawing proof/bursa run is `full-build/axial-anterior-recess-production-final/`.
Its native proof rows are axial21, packed row0, 1862 pixels, and axial 22, no packed row, 1896 pixels,
both addressing `a4_axial_joint_fluid`. Reconstructed supports exactly equal the original side unions.
The lead inspected `axial-anterior-recess-bridge/axial-anterior-recess-native-supports.png` against
the actual acquired images. Their selected pockets visibly describe anterior patellofemoral cavity
sections; the original fluid, lining, capsule and retinacular descriptions remain. The shared map
selects sagittal 18 and axial 22 for anterior recess, with coronal not supplied and no complete point.
Other proof references remain as at §8.16. The map's expected bookkeeping changes are recorded,
not presented as changed anatomy or a speed-up.

The public comparison exposed an aggregation issue: when a first structured observation arrived,
the older fallback-only object summary stopped including original definition abstentions, although
the per-record codes remained. `describe_objects` now always retains `definition_decisions` and
`search_refusals` independently of native/laid/projected observations. Sources are collected once
per record and once per own-slice silence, with exact object matching, no alias guesses or fabricated
provenance. Existing summary/fallback semantics and original rows remain. The final versus the
pre-single-pass collection run is output-identical; the collection change adds no image work.

`axial-anterior-recess-bridge/audit-final.json` reconstructs the final supports and preserves all
24 preceding proof/bursa records, all 1960 saved arrays byte-for-byte and all old observation/refusal
prefixes. Two axial cavity rows are appended. `public-test/final-public-output-audit.md` records
15 middle and one main public record: all 1855 arrays and three maps are unchanged; four native
anterior-recess unknown rows are appended with the existing source reasons. Original fallback
codes are retained in the new categorical fields. Forty source hashes match `source-hashes-final.json`
through the final real runs and whole gate. `full-build/axial-anterior-recess-gate-final.log` passes
791 tests, Ruff/format, production import contract, dependency and src/tests type checks. Vulture's
atlas/contract/diagnostic and older test advisories remain visible, not declared clean.

No new image reading, cutoff, slice search, duplicated fluid union, API call, commit or push is
part of this increment. Canonical measurements and the earlier 58-study snapshot remain unchanged;
the full refresh follows the accepted family wave. Remaining Packet A: anterior recess coronal,
joint axial and capsule sagittal, then the other families in FULL_BUILD_PLAN. The inspected coronal
preview is development only: native white body on a neighboring plane, physical source location
only a guide. No hard-coded example indices are authorized as production selection rules.


### 8.18 Coronal anterior recess from native acquired signal, 2026-10-17

This completes Packet A1 of THREE_VIEW_PRODUCTION_EXECUTION. The existing native sagittal
anterior recess supplies a physical location, not a coronal boundary. Its already computed LPS
points are retained once in `a4_anterior_recess_source_lps`, with exact source artifact, support,
row, slice and physical area. The unique strongest native source is shared across target series;
a source tie stays a named uncertainty.

`coronal_anterior_recess` starts with the existing physical target and the map's expected depth
and in-plane boxes. Cheap native-light samples at projected source coordinates point to a slice;
a positive peak at a visited edge extends, and a miss broadens the unvisited sample readings once.
Only candidate maxima label the native white bodies. `white_body_at_location` keeps the unique
largest connected white body intersecting the location target. It measures no anatomical name.
The native coronal signal uses the existing combined-marrow fluid level, without a new cutoff,
proof index, lens or field read. Every source/sample/status/component/native-support reading is
retained; unread context remains declared unread. Missing/unavailable and measured-empty readings
remain distinct. The new observations enter the existing family map boundary before fibula search,
then append after earlier observation/refusal prefixes and use the existing single persistence path.

The no-drawing actual run is `full-build/coronal-anterior-recess-production-final/{interiors,main}`.
The proof's native coronal slice7 has 178 pixels in boolean support `a4_coronal_anterior_recess`,
row0, label null. The source is sagittal 18, 75 points; the projected location has 21 unique pixels.
The existing coronal fluid level is 308. Seven slices were sampled and one native body was read.
These are observations, never constants. The lead inspected the actual frame7 raw/support figure
in `coronal-anterior-recess-bridge/public-test/proof-coronal-slice-7-address-check.png`, whose
loader/DICOM equality is recorded, and the selected-three-plane figure. The native pocket supplies
this local cavity description; it does not claim the whole recess envelope or its full extent.

Anterior recess now selects sagittal 18/coronal 7/axial 22. The physical plane intersection is
[-104.01913067885982,-97.29369248033808,46.22860950899794] mm: a reference for this distributed
cavity, not a guaranteed cavity voxel, boundary or volume. The proof has seven complete references
and 42 complete ordered pairs (43 slots / 1806 total pairs); remaining pairs retain unresolved ends.
Its new anchor is consumed in later fibula guides, with the actual fibula slices/supports unchanged.

`coronal-anterior-recess-bridge/audit-final.{json,md}` preserves all 24 prior proof/bursa records,
1,960 prior arrays, assignments and complete old observation/refusal prefixes. There are 22 new
arrays (21 coronal readings and one sagittal source), one new native proof observation and three
new coronal refusals. Runtime evidence records seven added margin readings, no added lens/field
readings, and one component-body read; timings are observations, not a speed claim.

The public final run `coronal-anterior-recess-test-final/` preserves all 1,855 prior arrays and
original categorical/observation/refusal information, adding 25 arrays, two native observations
and three refusals. The new public-target study 100628… native coronal rows 23/24 hold 2,893/4,225
pixels. The lead inspected both actual-frame figures; no universal anatomical-validation claim
is made. The public audit and exact DICOM/frame manifests are under the bridge's `public-test/`.
The pre-type-cleanup and final actual runs are output-identical, including records, arrays,
objects, unread inputs and telemetry (`accepted-source-equivalence.json`).

The complete gate `coronal-anterior-recess-gate-final.log` passes 817 tests, Ruff/format, the
production import contract, deptry and `ty check src tests`. Vulture's advisory atlas/contract/
diagnostic and test-fixture findings remain. All 40 accepted production source files are retained
byte-exact under `coronal-anterior-recess-bridge/accepted-source/`, matching
`source-hashes-accepted.json`. Subsequent capsule work is a later source increment, not a claim
that the working tree still equals that historical snapshot. The separate runner type scan still
has41 earlier findings; standalone-runner type cleanliness is not claimed.

Canonical/cohort outputs are not refreshed for this bounded step; the 58-study pair range/sample-SD
refresh follows the accepted family wave. Remaining Packet A2: joint axial and capsule sagittal.
The inspected capsule preview is now reproducible in
`production-build-planning/sagittal-capsule/relative-band-actual-frame/`; it is development only.
Its preceding ambiguous provenance led to an overclaimed wrong-frame diagnosis, corrected in the
older preview's WITHDRAWN.md. Existing definitions remain, with no precision/perfection gate,
API call, commit, push or submission in this increment.


### 8.19 Native sagittal capsule external band, 2026-10-17

This completes the capsule part of Packet A2, not the remaining axial joint description. The
coronal capsule wall's physical points, already computed in `name_the_recess` for cross-view
location, are retained once with their exact native source address. `name_sagittal_capsule`
shares the unique largest physical-area native coronal source across sagittal questions; a tie
or missing source remains explicit. The source points locate a native question, never its wall.

`sagittal_capsule` consumes the map's expected slice window and in-plane boxes, plus the existing
physical source target. Cheap acquired samples cover the existing 2 mm in-plane allowance around
projected source points. This is a location allowance, not slice thickness or a new depth gate.
Supported peaks at a visited edge extend; on a guided miss the already visited source window is
asked before unvisited depth is broadened. Only native candidate maxima label whole connected
white bodies. Use the existing recess fluid level or the same shared combined-marrow reading;
there is no new signal cutoff, image lens or field read. The target stays distinct from the body.

The new anatomy-independent `relative_outer_wall` reads native sections nearest patient superior.
Outward is patient anterior: outside the white body, in the existing 2 mm allowance, retain the
whole contiguous exact acquired-signal minimum only when darker than that section's white-body
median. Separated ties and unreadable/nondarker sections retain statuses and readings. Invalid,
unavailable and nonfinite body samples cannot move its edge, median or band. This relative lens
locates the visible fibrous outer band where the background split lens alone reads none; it does
not fit a new grey level. The two existing retinacular paths and their masks remain unchanged.

The final real no-drawing run is `full-build/sagittal-capsule-production-final/{interiors,main}`.
Proof native sagittal 3 / row 0 has 24 wall pixels around a 202-pixel body; sagittal 32 / row 1 has 159 around
a 4970-pixel body. Both use boolean `a4_sagittal_capsule_outer_wall`, label null. The coronal source
is slice 15, 41 points; the sagittal fluid level is 352. These are measured observations, not constants.
The lead inspected both actual-frame figures and the selected three-plane figure under
`sagittal-capsule-bridge/production-first/`. The longer native band follows the anterior dark
boundary of the bright cavity. The smaller section can include adjacent fibrous/surface tissue.
This is a competent local sleeve description, not full course, exact fibre separation or thickness.

The capsule selects sagittal32/coronal15/axial21. Their plane equations jointly give reference
[-146.82124852422498,-71.02607166628661,46.51896144828606] mm; it is a localization reference,
not a guaranteed membrane voxel or volume. The guide remains broad (34 of 36 sagittal slices
sampled here), with retained prediction disagreement; no tighter-prior or speed-up claim is made.
Only two full native body/wall questions run. The proof has 8 complete references and 56 complete
ordered pairs, up from 7/42; 35 slots remain partial. The capsule anchor is consumed by later fibula
guidance, with the fibula's observed point, key planes and earlier arrays unchanged.

`production-first/audit.{json,md}` reconstructs actual native support and preserves all 10 interior / 
14 main proof+bursa record identities, assignments and old observation/refusal prefixes. All 1982
prior arrays remain byte-exact; 39 interior arrays are added, none to main. Source-point/profile/
sample/component/strip/minimum/edge/status contexts are retained; context with no downstream
consumer remains declared unread. The proof adds one sequence refusal and the bursa adds two
(sequence/source); those are not absence. Runtime profiles retain 63 `interior_regions` and 47
`field_of` calls across the two studies; proof ledger lens/field production remains 35/27. There
are 5 new margin readings and 2 new position readings, with other handoffs recorded in the audit.
These are work observations, not a timing improvement.

The unprofiled normal parallel run and the final source-formatted production run exactly match
the first run's records, metadata, unread lists and all 2021 arrays (`repeat-run-comparison.json`).
The profiler's initial parallel-launch failure is retained in the first log: stdlib cProfile
could not pickle the entry point's worker under its `__main__` wrapper. Profiling used the existing
`--workers 1` option; the ordinary parallel CLI was verified separately. No production workaround
or alternative entry point was introduced. Formatting changed only syntax layout, with equal ASTs
recorded in `format-only-comparison.json`; both source 40-file snapshots are retained.

The matching public final run preserves all 15 interior / 1 main records' earlier assignments and
observation/refusal prefixes, unread lists, and all 1880 arrays. It adds 7 named unresolved capsule
rows across 3 studies and no native capsule support or arrays. The exact source/sequence reasons
remain in `production-first/public-output-audit.{json,md}`. The complete final gate
`sagittal-capsule-gate-final.log` passes 862 tests, Ruff/format, production import contract, deptry
and `ty check src tests`; Vulture's advisory fields/fixtures remain visible. The source 40-file
`source-hashes-final.json` matches the saved `source-final/` snapshot. The separate runner type
scan retains 41 older findings, with none in the new functions; it is not claimed clean.

Canonical/cohort outputs remain the preceding snapshot; the 58-study pair range/sample-SD refresh
follows the accepted family wave. The remaining A2 axial joint has an inspected development
candidate: the same 78-pixel intercondylar body contacts both independent sagittal and coronal
joint-location targets. Its intended native description is a fluid-filled portion of the known
tibiofemoral/intercondylar compartment, not a patellofemoral alias or whole envelope. Its build
has begun and is not yet accepted. B–F, including explicit typed anatomical-relationship output,
remain. No new API call, commit, push or submission in this increment.
### 8.20 Native axial joint and explicit anatomical links — 2026-10-17

Packet A2 is connected through the existing production entry point. The original sagittal and
coronal joint definitions remain intact. Their independently selected native FS sections supply
physical locations inside each actual axial half-thickness. At positive profile maxima, the
native fluid-level connected bodies must touch both source targets; the unique largest eligible
body supplies a local fluid-filled description of the tibiofemoral/intercondylar joint. This is
neither the whole joint envelope nor a renaming of the patellofemoral fluid pockets.

Map depth and in-plane placement guide the first search. Native source-depth support and boundary
extension remain available; a miss broadens. Geometry and source membership are calculated once,
with sparse readings retained. Full component measurements run only at candidate planes. Missing
sources, invalid geometry/calibration, ties, unavailable samples and complete empty readings remain
distinct. Sparse empty observations address profile slices and offsets, never fabricated full-image
availability or labels. Source points are made only for the selected source sections.

The actual proof resolves axial14, boolean `a4_joint_axial_compartment` row1, 78 pixels. Slice11
records separate bodies that do not satisfy both locations; slices17/18 retain empty sparse profile
readings. The selected joint planes are sagittal18/coronal15/axial14. Their physical constraints give
the ninth complete proof reference and 72 complete ordered pairs of 1806. The actual three native
frame figures were inspected. The bursa example refuses because its native coronal joint source
is unavailable; this is not anatomical absence.

All 24 prior proof/bursa records retain their identities, assignments and observation/refusal
prefixes; all 2021 prior arrays are unchanged, with 51 additions. The ordinary two-worker run and
single-worker profiled run have identical records, arrays, maps, object output and telemetry.
The public run preserves 15 interiors/1 main records and prior arrays; it adds five source arrays
and four named joint refusals, with no new joint observation. All 42 pinned source files match.
The whole gate passes 887 tests, Ruff, import/dependency/type checks; Vulture advisories remain.
The axial helper adds two full native component measurements on the proof, reusing the existing
fluid level and shared frames/margins, with no extra lens or field. No speed-up is claimed.

The same object-output builder now exposes 34 sourced typed anatomical definition links over
32 subjects: between, attaches_to, covers, lines, bounds, encloses and directional relations.
Every relation targets entries in that same object table and explicitly carries
`basis=anatomical_definition`; it does not claim the study measured every attachment or enclosure.
Actual observations and refusals remain separate. This closes that bounded F requirement, not
the rest of F or the three-view build.

Evidence, exact source copy, renderer, DICOM/frame/support hashes and audits:
`data/readings/collapse-20261017/full-build/axial-joint-bridge/`.
Packet A's source-fixed labelled refresh completed through the same CLI: 58 studies, 336 middle
records, 43 main records, no unread series. The existing analyzer reports 1806 ordered pair
entries with actual vector ranges and sample SD (unknown for n<2), and no inconsistent declared
positions. There are 107 complete object-study references; the other 2387 retain partial status
and explicit missing constraints. Partial status does not assert that an object is localized.
All 67 new axial-joint observation addresses and counts pass reconstruction, including 59 sparse
profile rows and eight full-plane rows. This verifies output/geometry, not anatomy on every study.
The complete reports are under `axial-joint-bridge/cohort-final/`. No previous cohort equivalence
is claimed. B–F remain as specified in THREE_VIEW_PRODUCTION_EXECUTION, with axial extensor
cross-sections completed in §8.21.

### 8.21 Native axial extensor tendons — 2026-10-17

Packet B begins with independent axial descriptions of the patellar and quadriceps tendons.
The uniquely strongest identified native non-FS sagittal middle section supplies each tendon’s
physical source locations; tied sources remain unresolved. Actual axial half-SliceThickness
membership gives sparse location profiles. The map’s depth and in-plane windows guide the first
candidate maxima; source-profile maxima are read only after a guided miss. These profiles point,
never supply the anatomical mask.

At a candidate, the existing enclosed-darkness reading, its positive support and the existing
2 mm dark-body operation supply whole native components. The unique largest component touching
the actual source locations describes that tendon cross-section. No fluid/marrow calibration,
new grey threshold, proof coordinate or component ID enters the rule. Same-slice depth, field,
free mask, body labels and component sizes are shared by both selectors. Native positions are
retained as unread diagnostic values; saving is not consumption. The generic enclosed-depth cache
also serves the existing vessel caller with its identical raw input, and retains the original
uncached behavior when no series identity is supplied.

The proof resolves patellar tendon axial13 (587 pixels) and quadriceps tendon axial30 (1786),
with boolean `a4_axial_<name>_body` rows addressed by `a4_axial_<name>_slices`. Actual acquired
frames, source locations, depth and complete component outlines were inspected and shown. The
quadriceps component retains lateral extension; these are competent local descriptions, not full
course or exact boundaries. Both enter the same family map handoff and grouped object output.
Their prior sagittal constraints remain; coronal remains missing, so both references remain partial.

Missing/tied/malformed source, unavailable geometry, clipped projection, tied bodies and complete
measured-empty bodies retain distinct outcomes. A positive body may be identified from the
in-frame part of a clipped source, while an empty clipped result remains unresolved. Empty native
readings address measured false body rows, never a projected location mask. Eight direct tests
exercise these distinctions, shared work and guided fallback.

The final real CLI preserves all 10 interiors/14 main proof-and-bursa records and earlier arrays,
assignments, observations and refusals; 41 arrays and two native proof observations are added.
The bursa example has no native sagittal tendon sources and says so. Final ordinary parallel and
first profiled outputs agree. Public inputs preserve 15 interiors/1 main records and all prior
arrays, add eight source-unavailable refusals across four axial series in three studies, and add
no native tendon observations. The full gate passes 895 tests, with import/dependency/type checks
kept and Vulture advisories retained. Standalone runner typing still has 41 older findings, none
in this helper. The profile records two new native body reads; no speed-up is claimed.

Evidence is `data/readings/collapse-20261017/full-build/axial-extensor-bridge/`: final audits,
actual-frame renderer/figure and address hashes, plus copies/hashes of 42 production files and the
focused test. That copy was captured after the final run; no pre-launch snapshot of the first
profile is claimed. The source-fixed 58-study checkpoint remains Packet A, not this later code.
Remaining B: coronal extensor tendons, fat pads in coronal/axial, retinacula in sagittal/coronal;
C–F and later encoding/AI/competition dependencies remain in the execution plan.

### 8.22 Native coronal extensor tendons — 2026-10-17

The coronal descriptions combine two independently native locations: the retained sagittal
source and the actual resolved axial tendon body. Each source contributes physical points inside
the actual coronal half-SliceThickness slab. Their separate cheap depth profiles point to candidate
maxima; map depth and in-plane guidance run first, broadening after a native miss. The native
enclosed-darkness body must contact BOTH location sets. A unique largest common component supplies
the section; separated source contacts and tied components remain unresolved. Physical-point counts
drive these coronal source profiles and map windows consistently; unique native RC targets are
retained separately. B1's unique-RC profiles and output schema remain unchanged.

The source projection, native context and context packing are shared with the axial reader through
`_extensor_source_projection`, `_extensor_native_context` and `_pack_extensor_native_context`.
Same-frame depth, available field, dark bodies and component sizes are computed once for both names.
Selected source LPS points are reused, including their actual source addresses. The existing family
map handoff receives the new observations before dependent searches and the single save. No new
threshold, image lens, copied slice coordinate or second anatomical compute path was introduced.

The real proof resolves patellar tendon coronal4 and quadriceps tendon coronal5 in BOTH sequences:
non-FS UID124515… has 3246 and 479 pixels; FS UID214978… has 2023 and 369. Patellar candidate6 is
measured empty in both, with actual false boolean support rows. The actual acquired frames, both
location sets, native depth and complete addressed bodies were inspected, including four native-pixel
crops. The dark fan below the patella and the band above it are competent local descriptions; full
course and exact boundaries are not asserted. An initial renderer message inverted FS/non-FS names;
receipt flags were checked and figure/manifest labels corrected before acceptance.

The selected physical constraints are patellar tendon sagittal21/coronal4/axial13 and quadriceps
tendon sagittal18/coronal5/axial30. Both references are now complete on the proof: 11 complete/32
partial references, 110 complete/1696 unresolved ordered pairs of 1806. These are localization
references; native masks supply tissue evidence. The bursa example's four coronal source refusals
remain explicit. No native tendon is claimed there.

The 44-file source snapshot was captured BEFORE the CLI at
`data/readings/collapse-20261017/full-build/coronal-extensor-bridge/source-first/`, with
`source-hashes-first.json`; all hashes still match. The first profiled and ordinary parallel runs
are exact across 10 interiors/14 main records, arrays, observations, maps and telemetry. Against B1,
all earlier arrays and categorical prefixes remain; 112 arrays, six observations (four resolved,
two empty) and four refusals are added. Two fibula main-slice summaries add only tendon guide
anchors/placements; selected slices and all native findings are unchanged. Public inputs retain
all old arrays/observations/refusals and add eight named coronal source refusals across four series,
with no new arrays or native claims. Reproducible audits and actual-frame renderer are in that
evidence directory.

The whole gate passes 901 tests, keeping import/dependency/type checks and reporting Vulture's
advisories. Runtime/static callers agree: two naming calls, four coronal reader calls, eight native
context calls across both orientations (two axial/six coronal), and three shared pack calls. No
speed-up is claimed. The 58-study snapshot remains the older source-fixed Packet A measurement.
Next B work: native coronal/axial fat pads, then sagittal/coronal retinacula; C–F remain.

### 8.23 Native sagittal and coronal patellar retinacula — 2026-10-17

The existing axial retinacular sections now have native sagittal and coronal companions. The
proof map selects medial sagittal12/coronal5/axial22 and lateral sagittal32/coronal12/axial21.
Their native boolean supports contain, respectively, medial 73/58/70 pixels and lateral
159/82/71 pixels in sagittal/coronal/axial order. These counts describe the addressed sections;
they do not measure wall thickness or the full courses.

The medial sagittal map-guided candidate at slice5 remains in the observations with 11 wall pixels.
The stronger sagittal source-profile candidate at slice12 was checked and resolved with 73 wall
pixels; slice12 becomes the selected sagittal key plane. The map evidence records support 2.75 at
slice5 and 18.25 at slice12. This retains the guided observation while allowing the checked native
source-profile result to supply the selected plane. Medial coronal slice5 remains selected with 58
pixels. The lateral sagittal support can include adjacent capsule/course tissue; that overreach is
recorded and does not turn the section into a thickness or full-course measure.

For each side, `retinacular_sources` chooses the unique largest physical-area native axial wall
and converts its addressed pixels to LPS points once. The proof sources are medial original-main
axial22/70 and lateral pointed-axial21/71. The sagittal and coronal reader projects those points
through each target's actual half-slice-thickness slab. Map depth and in-plane guidance order the
candidate questions first; the native source profile is the measured fallback, with stronger
maxima checked after a guided candidate. At a candidate, same-series recess calibration supplies
the bright-body level. The reader labels whole connected native white bodies, keeps the unique
nearest body with the existing 2 mm core to the source target, and applies the coronal inward-order
check. `relative_outer_wall` then reads the acquired-signal minimum in the existing 2 mm strip
outside the selected body, section by section; only a contiguous tied minimum darker than that
section's body median is retained. The axial locations guide these readings, not a projected
boundary or footprint. No new signal cutoff is introduced.

The frozen proof/bursa audit recomputed receipt digests and all five cross-view outer-wall array
addresses. All prior proof/bursa assignments, arrays, observations and unresolved prefixes are
preserved; first and ordinary parallel runs match. The public baseline and test receipts also
match exactly. The map remains at 13 complete references and 30 partial references; its refinement
count is 46 and version is 117. The complete gate for this frozen source scope passes 952 tests.
Evidence and inspected addressed figures: `data/readings/collapse-20261017/full-build/retinacula-cartilage-checkpoint/`
and `data/readings/collapse-20261017/full-build/retinacula-cross-view-bridge/stronger-profile-final-images/`.
The source-frozen checkpoint is separate from later live fat-pad work; no claim is made here about
that work.

### 8.24 Sagittal cartilage companion observations — 2026-10-17

Three already saved sagittal joint-plane readings now also carry the femoral and tibial cartilage
observations. At slice15 the saved labels contain 215 femoral and 259 tibial pixels; at slice17,
307 and 297; at slice22, 236 and 250. Each added row was checked against its actual saved row,
slice address, label and pixel count. The observations append after their prior matching-address
rows, and all existing candidates remain in order.

This was a zero-image-pass companion: the six observations use the existing `a3_joint_plane_reading`
arrays at their recorded rows. No saved arrays were added or changed, and no new image measurement
was made. This records sagittal support in those saved sections; it does not claim a new axial
cartilage description, a complete three-plane cartilage reference, or a perfect surface. The
observed tibial overreach is retained. The same frozen receipt/source/gate audit cited in §8.23
records the six validated rows and exact preservation checks.

### 8.25 Native fat-pad descriptions — 2026-10-17

The native coronal and axial descriptions use a new shared physical-gradient measurement in the
production operation. It measures acquired-image gradients from valid neighboring samples at their
actual pixel spacing, then uses SciPy's native image-filtered-gradient/IFT operation with linear
uint16 quantization. This is a measurement lens, not an anatomical threshold; the earlier proof
lenses remain unchanged. Actual half-slice-thickness source profiles and map locations guide
candidate questions, not tissue boundaries. The unique largest original H native territory touched
by its selected physical source supplies Hoffa candidate geometry. Q and P candidate basins come
from the native gradient competition among their source locations, native peaks, margin and the
coarse femoral-core marker. H/Q/P sources are independently selected identified sagittal-FS
sections by physical area; their source pixels are converted to LPS once. The composite Q/P source
is retained as context, never as a fourth gradient seed.

The opposite fat-bright acquisition is sampled at native candidate coordinates using that series'
own femoral-marrow calibration, actual planes, dimensions, thickness, bounds and margin. Positive,
negative, disagreement and unknown compatibility remain distinct; unqueried coordinates stay
unknown. The established fat-under-skin comparison is inclusive at its three-quarter-marrow
relation; the same-series white-fluid mask remains strictly above its existing fluid level. The
coarse femoral core is a competing geometric marker and exclusion where measured, not an exact
bone boundary. The two-millimetre operation here is existing coarse-block context, not a fat-body
opening. No signal cutoff was added.

Hoffa, quadriceps and prefemoral supports are separate. The suprapatellar description is the union
of quadriceps and prefemoral supports at the same native slice; it is resolved only where both
component supports are usable, and otherwise remains a partial reading. Same-series white fluid and
the measured femoral core are excluded where their actual supports are available. Named unknown,
incompatible, partial and measured-empty outcomes stay distinct; source locations are not painted
as tissue boundaries.

On the proof, the selected references are Hoffa sagittal18/coronal8/axial16, quadriceps
sagittal18/coronal6/axial27, prefemoral sagittal18/coronal8/axial29, and suprapatellar fat
sagittal18/coronal8/axial27. Addressed native boolean counts include Hoffa coronal8 7,735 and
axial16 2,504; quadriceps coronal6 2,107 and axial27 76; prefemoral coronal8 989 and axial27 164;
and composite coronal8 1,193 and axial27 240. The other measured sections remain in the receipt,
including composite readings at coronal6/9 and axial29. These are local supports, not full courses
or exact boundaries.

The lead inspected every addressed frame. The accepted descriptions retain visible limits: Hoffa
axial16 support is patchy; its coronal8 field is broad and includes adjacent/subcutaneous tissue,
and the posterior coronal22 candidate is marrow at that frame. Quadriceps coronal6 includes
neighboring muscle/fat; the coronal8 quadriceps and prefemoral supports are separate limited
sections. Axial27 quadriceps/prefemoral supports are small compatible portions of larger retained
candidates, and the prefemoral axial29 support is a strip. These observations remain recorded; no
per-study correction or perfection requirement is added.

The proof map now has 17 complete and 26 partial references, version129 and 50 refinements, up from
13 complete/30 partial, version117 and 46 refinements. The fixed-source production audit preserves
all prior proof/bursa records, observations and unresolved prefixes, and all 1,829 prior interiors
array digests; it adds 534 interiors arrays and leaves all 496 main arrays unchanged. The matching
serial and parallel outputs agree. The public comparison also preserves its prior outputs. The
complete gate for this source scope passes 963 tests. Evidence, source hashes and
actual-frame figures are under
`data/readings/collapse-20261017/full-build/native-fat-pads-checkpoint/`.

Packet B’s source-pinned cohort now completes: 58 maps, 336 interiors records, 43 main records, and 0 unread study inputs. Across the 2,494 study/object map entries there are 116 complete and 2,378 partial entries; these are coverage counts, not accuracy claims. The pair report contains 1,806 ordered pairs. For each reported metric, 1,534 pairs have n=0, 252 have n=1 and 20 have n≥2; sample SD is null below n=2. The declared `construction_consistent` field has zero inconsistencies, which is a position-construction check, not anatomical proof. All 80 native fat boolean support addresses validate against saved rows, slices, counts and actual frames. The corrected cohort audit counts native rows from both receipts, separates readings from resolved supports and cross-checks 5,879 native rows against the production combined object summary. At the Packet B audit, all 56 source hashes matched its source snapshot and live tree. Receipts are under `data/readings/collapse-20261017/full-build/packet-b-cohort/interiors/` and `data/readings/collapse-20261017/full-build/packet-b-cohort/main/`; pair report files `cohort-pair-variation.json` and `cohort-pair-variation.csv`, the source pin, detailed audit and summary are under `data/readings/collapse-20261017/full-build/native-fat-pads-checkpoint/`. This is Packet B’s source epoch. Packet C remains under construction; its live edits are outside this snapshot, and no C axial production result is accepted here.

### 8.26 Native axial femoral cartilage — 2026-10-18

The proof femoral-cartilage description now has an axial native observation in addition to its
existing sagittal and coronal readings. The selected planes are sagittal17, coronal15 and axial14.
The accepted native row is axial slice14, support
`a4_axial_femoral_cartilage_support`, packed row0, boolean shape (1,320,320), count994. It uses the
existing native femoral enclosure, marrow calibration and cartilage reach, and must touch both
independent sagittal and coronal source locations. The support is a local section description, not
a full-surface boundary; the inspected section retains adjacent cortex/tissue overreach. Existing
sagittal rows and the coronal source remain intact.

The first attempted run used the wrong collector key and emitted no resolved native cartilage row;
that output and its hashes remain preserved as a failed historical attempt. The corrected
source-fixed serial and parallel production receipts match, all earlier observation and refusal
prefixes remain, and canonical saved-array digests verify. Six existing retinacular profile arrays
changed in the proof interiors archive as map guidance was refreshed; exact per-key values are in
`data/readings/collapse-20261017/full-build/axial-femoral-cartilage-checkpoint/audit_axial_femoral_cartilage.json`.
The public run preserved all prior prefixes and maps, added four coronal source-context arrays and
four named unresolved femoral-cartilage rows, and added no resolved public native cartilage row.
The corrected 58-file source pin has no snapshot or live mismatches. Formatting-only normalization
after that pin was AST-equivalent and is documented in the checkpoint audit.

The corrected full CI gate passes 982 tests; Ruff, formatting/import/dependency checks, and source
and test typing pass. Vulture advisories remain. The audit, failed-first record, source pins and
figures are under `data/readings/collapse-20261017/full-build/axial-femoral-cartilage-checkpoint/`.
Corrected run receipts are in sibling directories `axial-femoral-cartilage-source-fixed/`,
`axial-femoral-cartilage-source-fixed-parallel/` and `axial-femoral-cartilage-source-fixed-test/`,
each with `interiors/` and `main/` receipts.
This is a proof-study result, not a refreshed Packet B cohort count. Packet B's 58-study coverage
figures above remain tied to its older source epoch. Native axial tibial cartilage, sided menisci,
ACL and PCL remain pending; development-only previews are not production descriptions. The direct
Fable efficiency consultation is complete; its advice remains advisory. Rohan's useful-priors
criterion is recorded in `docs/TARGETED_ANATOMICAL_COMPUTE.md`.


### 8.27 Native sagittal menisci in useful local windows — 2026-10-18

The existing native coronal FS medial/lateral wedges now guide independent sagittal FS readings
through `scripts/run_interiors.py`. Actual half-slab source profiles and the shared map choose
candidate slices. Heavy enclosure/body analysis reads only an anatomy-derived local crop. The
source points locate a part of the object; they are not its centre. An arbitrary in-object point
can be a full object extent from another point, so the existing full-span `source_window` helper
receives twice the authored extent (its projection uses half a full span). The earlier half-extent
crop cut off the enclosure. This correction requires no new signal threshold or additional lens.

Inside the useful crop, the original enclosed-darkness measurement gives positive depressions;
the existing 2 mm meniscus-body opening and four-connected labels separate substantial bodies.
Select the unique largest whole component reaching the native coronal source location through
the existing 2 mm contact allowance. Contact pixels are not substituted for the whole component.
Exact ties, unavailable targets, complete measured-empty and partial readings remain distinct.
Excluded stored values cannot influence the reading. Every crop, offset, source address, intermediate
measurement, selected support and explicit slice address remains saved. Only the final support is
scattered into full-frame coordinates for the existing observation/map contract.

The lead inspected the actual DICOM-addressed production figures: medial sagittal5 is a 588-pixel
body between the joint surfaces; lateral sagittal28 is a 200-pixel anterior horn; the retained
source-profile tie at sagittal29 gives a 553-pixel connected body. The lateral posterior horn on
slice28 is measured separately but not named by this source-contact selection. These are competent
local descriptions, not exact boundaries or full courses. All slice indices/counts are observations,
never production constants. The common map now selects medial sagittal5/coronal15 and lateral
sagittal29/coronal15; both still explicitly lack an axial plane, so neither gains a fabricated 3D point.

Reproducible evidence under `data/readings/collapse-20261017/full-build/targeted-compute-20261018/`:

- `meniscus-local-production-addressed/{interiors,main}` is the source-frozen profiled run;
  `meniscus-local-production-parallel/` matches its complete receipts and maps exactly.
- `meniscus-local-production-test/` preserves every earlier public array/map and categorical prefix;
  it adds named unresolved rows, with no resolved sagittal meniscus claim.
- `meniscus-local-checkpoint/source-hashes.json` pins 63 files, independently checked with zero
  mismatches. The first run without explicit support-slice arrays remains in `meniscus-local-production/`
  with its separate earlier source pin; it is not the final addressed receipt.
- `meniscus-local-checkpoint/audit_meniscus.{json,md}` reconstructs all five native sided-meniscus
  addresses, preserves all earlier observation/refusal/definition prefixes and all 3,005 earlier
  arrays (2,509 interiors + 496 main), with 73 added arrays and none removed or changed. Only the two
  meniscus entries and map bookkeeping change in the proof map. No other anatomical result is withdrawn.
- `meniscus-local-checkpoint/production-figures/` contains the inspected actual-frame sheets;
  its retained generator checks DICOM crop equality, full-frame scatter, counts and explicit z addresses.
- The whole gate passes 997 tests. Ruff, formatting, import/dependency checks and source/test typing
  pass; Vulture advisories remain. A separate broader runner typing probe retains 41 diagnostics
  outside the new adapter; it is not reported clean.

Three heavy local reads visit 20,520 + 17,346 + 17,346 = 55,212 pixels, respectively 20.039%,
16.939% and 16.939% of the 102,400-pixel frames. There are three distinct exact cache keys and no
repeated identical local reading. This is spatial targeting, not a measured whole-pipeline speedup.
`compute-audit.{json,md}` records the actual profile and ledger; the new driver has 0.136813 seconds
cumulative time in that profiled run, not a paired benchmark. It also exposes declaration gaps:
source points/metadata are consumed in code without ledger reads, and profile reads lack their
producer declaration. Correct those at the next family edit; do not invent consumers for diagnostic
arrays or count persistence as consumption. Older full-frame consumers and their retained unread
measurements remain work under the coherent roadmap.

The unchosen directional/closing-span/gradient variants remain development evidence. The directional
helper and its tests have been removed from production; exact copies and reproducible dev imports
are in `retired-directional-lens/`. The direct local-meniscus Fable consultation is retained in
`fable-local-meniscus/`; the lead's geometric correction, rather than its suggested extra selector,
resolved this increment. Next: the native axial meniscus question using the complementary native
coronal/sagittal descriptions, then the rest of roadmap R2. The 58-study cohort is still the older
Packet B epoch and is not refreshed by these two-study runs.


### 8.28 Native axial menisci and their shared-map handoff — 2026-10-18

The same production family now reads native axial medial/lateral meniscus bodies from both independent
coronal and sagittal native locations. Actual half-slab profiles and map guidance choose the candidate;
useful anatomy-derived windows precede heavy local enclosure/body work. A source location is not
an object centre. Inside the crop, reuse original positive enclosed darkness, the existing 2 mm
meniscus opening and four-connected components. Select the unique largest whole component reaching
each independent source through the existing 2 mm contact allowance. Intersect component IDs, not
contact pixels. No new signal cutoff or alternative recognition pipeline is added.

The lead inspected actual DICOM-addressed axial12 outputs: medial 1403 pixels, lateral
1437 pixels, curved bodies at the corresponding joint margins, with adjacent cortex/tissue
overreach retained. These are competent local descriptions, not precise borders or full courses.
Both selected supports are on available samples and neither touches its crop edge. Window
completeness is independent of the body decision: each window retains `partial_reading`, with
4 / 2504 unavailable samples respectively, while `selection_status=identified` supplies the native
resolved observation. Unavailable, tied or partial-empty questions are not promoted to resolution
or complete measured-empty outcomes. Useful bounds need not be complete; missing background
elsewhere in a broad window must not withdraw a measured positive body. All availability and local
measurements remain saved.

The common map now selects medial sagittal5/coronal15/axial12 and lateral
sagittal29/coronal15/axial12. Their reference positions are jointly solved from the three native
physical planes, never a section centroid. The lead independently checked the plane equations
and pair vector. The proof has 20 complete references and 380 complete ordered pairs; those are
coverage counts, not accuracy or full-anatomy completion.

Evidence under `data/readings/collapse-20261017/full-build/targeted-compute-20261018/`:

- `axial-menisci-local-production-final/`, its `-parallel` companion and `-test` public run are
  the final production epoch. Serial/parallel complete receipts, arrays and maps agree.
- `axial-menisci-local-checkpoint-final/` retains the 64-file run source snapshot, source pin,
  gate/profile/compute audit, actual-DICOM figure generator and selected three-plane figures,
  support-address audit and `lead-acceptance.json`. All seven native meniscus support addresses
  reconstruct. The original full gate passes 1,013 tests; Ruff, format, import and dependency
  checks pass. Vulture advisories remain. Its one test-fixture typing finding was subsequently
  corrected without production edits: the separate verification source manifest pins that change;
  source/test typing and 25 focused tests then pass. Do not rewrite the run's original pin.
- The first axial source epoch rejected sources by comparing string acquisition flags against
  integer 1. It is retained as failed history. The `-fixed` epoch corrects that and early volume
  access, but still downgraded positive bodies for incomplete windows. Its outputs are retained;
  final separates the local measurement scope from the positive component decision.

The regression audit intentionally retains `prefix_address_failure`: the new meniscus planes
improve the downstream retinacular guide, so its existing candidate policy no longer visits the
weak medial sagittal5 proposal (11 pixels). The selected sagittal12 support (73 pixels) is
bitwise identical, and the retinaculum's selected 12/5/22 planes remain. The lead read the whole
consumer and independently verified the 20 changed old retinacular/context arrays. Of 3,078
common arrays, 3,058 are unchanged; 90 arrays are added and none removed. All main arrays,
prior definition decision lists and unresolved prefixes remain. This is explicitly a changed
visited domain from new anatomical guidance, not an equivalent-output optimization or a claim
that every earlier observation is an exact prefix. The earlier run retains its original evidence.
Public prior outputs/maps remain, with no resolved new meniscus claim.

The final profile/ledger records five distinct heavy crop readings: three sagittal plus two axial,
159,242 pixels total. Axial windows are 59640 and 44390 pixels, respectively
58.242% and 43.350% of a frame. No whole-pipeline runtime speedup is claimed.
Source/profile producer and actual consumer declarations are connected; retained diagnostics
remain honestly unread, and saving is not a consumer. Earlier whole-frame consumers and rough
leg prepass remain roadmap work. Next: native axial tibial cartilage, PCL/ACL coronal/axial,
then attachment/posterior/catalogue families and production cohort acceptance.


### 8.29 Shared local enclosed-body producer — 2026-10-18

The accepted meniscus selector now delegates to `local_native.enclosed_body_at_sources`, with
its existing 2 mm thickness supplied explicitly. This is an actual shared production producer,
not an alternate pipeline. The generic operation validates finite positive thickness; the
meniscus wrapper and its public signature retain their behavior. This prepares reuse of the
same measurement for the ligament's already authored 3 mm body scale without copying it.

The source-frozen real CLI profile, ordinary parallel and public runs complete. The audit
preserves every prior observation, refusal, definition decision, map and saved array exactly:
2672 common interiors arrays and496 main arrays, zero additions/removals/changes; all7 native
meniscus addresses validate. All64 snapshot/live hashes match. The profile records5 real wrapper
calls and5 generic calls from that wrapper. No runtime speedup is asserted. The complete CI
gate passes1015 tests, source/test typing, Ruff/format, import contract and dependency checks;
Vulture advisories remain. Evidence is under targeted-compute-20261018/shared-local-body-checkpoint/
and shared-local-body-production with its parallel/test companions. Anatomical acceptance remains
§8.28, whose inspected images are unchanged. Tibial cartilage/PCL previews remain development.

### 8.30 Bounded execution is foundational, not a whole-frame equivalence requirement

The human supplied an external efficiency analysis for correction of the build. His original
useful-priors statements govern: a lens's property and its visited domain are separate. Run the
existing measurement inside useful anatomical bounds before heavy work; local edge changes are
expected and retained. Do not require a crop to reproduce the whole-slice output, perfect exclusion
or a separate replacement lens before using it. The native description must be anatomically useful,
with explicit scope, offsets, availability and uncertainty. Exact preservation is for claimed
equivalent code changes, not a gate against intentionally targeted questions. Earlier full-frame
readers are immediate efficiency work alongside the remaining anatomy, not deferred wholesale
to R5. Retention remains unchanged; no computed information is dropped. The external report and
lead reading are retained at targeted-compute-20261018/efficiency-review-20261018/.

### 8.31 Bounded bone fine readings — 2026-10-18

Existing bone profiles now supply useful per-slice windows before the original expensive
`interior_regions` measurement. Femur and tibia share their window union where both exist; a
single useful window is sufficient, with a named full-frame fallback only where neither exists.
The middle bootstrap is unchanged. The local cache includes acquisition, slice and window and
does not masquerade as a full-frame cache entry. Native raw, availability, darkness, distances,
markers, labels, offsets and scope reasons are retained; unvisited places remain unavailable.
The actual fine-profile consumer is now declared at `read_bone`.

Evidence is in `targeted-compute-20261018/efficiency-review-20261018/bounded-bone-checkpoint/`;
the real CLI runs are its sibling `bounded-bone-production` and parallel/test companions.
The run has a65-file source pin. The later66-file verification pin adds one corrected test spy
for the changed lens call site, with production unchanged. The complete corrected gate passes
1019 tests, Ruff/format/import/dependency and source/test typing checks; Vulture advisories remain.
The earlier failed gate is retained rather than overwritten.

Both the worker and lead independently reopened all20 source DICOM frames:4,859,040 saved crop
pixels match exactly, including dtype/shape, source identity, actual frame geometry and crop
windows. The lead checked all95 artifact hashes. The audit reconstructs13 resolved native bone
sections. The sole changed resolved support is the bursa study's non-FS coronal femur at slice9,
94001→94035 pixels (+34, none lost), not the proof study. The actual acquired/old/new figure was
inspected. This inherited region is broad, includes adjacent proximal tissue and omits part of
the distal condylar section; it is not an exact femur boundary. This increment accepts bounded
execution of the existing description, not improved anatomical accuracy or perfect segmentation.

The10 interiors records add 52 array instances and change16, with none removed. Maps and main
outputs remain identical. Serial/parallel receipts agree. Public interiors change four records
(52 added arrays,11 changed, none removed); public main is identical. This is an intentional
scope change, not universal output equivalence. The first intermediate audit miscounted changed
reading metadata as changed resolved masks; its withdrawn figures remain marked as history.

For this family only, the20 windows visit4,859,040 rather than5,717,504 pixels. Some are still
broad. The instrumented whole operation has88 region calls versus84 before: later families
can still request full-frame context after a bounded bone read. No whole-pipeline speedup is
asserted. Continue propagating structural information into those actual consumers before heavy
work; the first map-aware full-frame fine consumer identified by the source trace is
`patella_plane`. The trace and source pin are in `efficiency-review-20261018/structural-consumers/`.

### 8.32 Equivalent batched squint kernel — 2026-10-18

The `physical_squint` implementation now batches complete tiles while retaining the original
per-tile behavior for partial, ragged and fallback inputs. The accepted source comparison found
the same native-dtype mathematical outputs. This is supporting equivalence work: it does not add
an anatomical description or finish the structural propagation required for every object.

Rohan's current emphasis is that this phase is heavy on the efficiency/accuracy/efficacy link
grounded by Significance Weighting and the information-theoretic `<object>` thesis. For every
object, anatomy-derived constraints should jointly reduce identity alternatives and the native
measurement domains that need work. A faster kernel supports that operation; by itself it does
not implement or complete it. §8.28 remains the latest accepted new-anatomy description, and no
patella description is accepted by this checkpoint.

The frozen `squint-batch-checkpoint/` source epoch has 67 files with no live/snapshot mismatch at
acceptance. Its gate passes 1,026 tests. The labeled cohort has 58 studies; all 112,104 saved-array
digests across baseline and batch epochs match their receipts. Receipt records, maps and object
entries compare equal, and no speedup is claimed. The source pin, lead acceptance, small-run audit
and isolated labeled-cohort audit are under
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/squint-batch-checkpoint/`.
This acceptance is pinned to that source snapshot; later live source changes must not be described
as the same 67-file epoch without a fresh comparison.

### 8.33 Scoped patella execution — 2026-10-18

The original patella-plane lens now consumes the shared femur/tibia profile window before its
expensive local measurement. The existing definition and native resolved patella supports are
unchanged. Four saved local attempts are retained: sagittal-FS slice21 identifies the same
2,676-pixel native support; slices1, 5 and27 miss locally and then broaden to the existing full
scope. The local misses remain distinct from their full-scope follow-ups. This is a scoped
execution change, not a new patella definition or a claim that all anatomy is bounded.

The lead inspected all 12 figures and independently reopened the four addressed DICOM frames,
checking crop bytes, dtype, shape, offsets, frame geometry and availability over 1,717,665 pixels.
The 68-file source pin has zero live/snapshot mismatches and its gate passes 1,036 tests. Relative
to the squint-batch baseline, proof/bursa interiors add 88 arrays, change 5 and remove 0; observations
and maps are unchanged. Main outputs are unchanged. Serial and parallel outputs agree. Public
interiors add 132 arrays, change 2 and remove 0, with no observation or map changes; public main is
unchanged. The five changed existing arrays retain the altered tibial context and scoped
availability/labels. The four already-resolved patella support masks are unchanged.

The three local misses add empty-attempt work before broader reads, and the windows remain broad
with inherited tibial context. This run therefore establishes scoped execution and its retained
readings, not a whole-pipeline efficiency gain or an accuracy improvement. Full source, outputs,
figures, hashes and audit are in
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/patella-scope-checkpoint/`.
The [every-object structural matrix](../data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/every-object-structural-chain/README.md)
is a static 43-concept source trace, not whole-anatomy completion; marrow is explicitly recorded
as interior tissue within bone (R5), not as a fabricated unique map reference.


### 8.34 Immediate common-map handoff — 2026-10-18

Completed native-family outputs now enter the existing common map immediately, before later
dependent family guide requests. The 15 offered families are `cartilage_companions`,
`recess_said`, `native_fat_said`, `coronal_anterior_said`, `sagittal_capsule_said`,
`capsule_said`, `lining_said`, `recess_fluid_said`, `anterior_axial_said`,
`axial_joint_said`, `axial_extensor_said`, `coronal_extensor_said`,
`axial_femoral_cartilage_said`, `sagittal_menisci_said` and `axial_menisci_said`.
The map-facing rows are converted once, offered immediately and reused in the later idempotent
closure. The existing map filters, duplicate handling and original append/save order remain.
This changes when existing evidence becomes available to a
later guide. It does not add a map, rule engine, anatomy definition or threshold.

A source-frozen 69-file epoch is pinned at
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/immediate-map-handoff-production/source-hashes.json`
(SHA-256 `8165914de13f19a697ef96e15d13d8b9067db7b021b58cb7db4ebc9005a2c798`; runner SHA-256
`0bd86d213c7c92d5d2d125907396d2eef6a9175729b197eb0f9b6b4c1e9ce4ec`). The complete gate
passes 1,038 tests. The proof runtime trace has 172 events and zero hook errors. It records the
axial-extensor offer at map version 92 before later tendon guides, and the sagittal-meniscus offer
at version 100 before later meniscus guides; the latter guides see the newly offered sagittal
sources. The trace wrapper, raw events and interpretation are retained in
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/immediate-map-handoff-production/guidance-trace/`; the lead acceptance, independent check
and receipt audit are in `data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/immediate-map-handoff-checkpoint/` under the same readings tree.

The proof/bursa run changes visit domains. Compared with the patella-scope epoch, the audit
records 27 changed arrays and five arrays not produced in the new run. The prior axial-joint z11
empty reading is not revisited; the old run retains it. At z14 the resolved joint support remains
78 pixels and pixel-identical, while its receipt row changes from 1 to 0 because the earlier z11 row
is absent. This is not evidence of absence at z11 and does not support a blanket prefix or
equivalence claim. Some refreshed guide domains broaden. Serial and parallel receipts match; the
public run has one additional map refinement and unchanged main outputs.

This is an accepted structural-information handoff, not an anatomy acceptance, accuracy claim,
paired runtime-speedup claim or whole-pipeline efficiency closure. The lead's acceptance is
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/immediate-map-handoff-checkpoint/lead-acceptance.json`. At this execution checkpoint §8.28 remains the latest new-anatomy acceptance. Other E24 semantic consumers and E02 remain partial; the 43-concept every-object matrix remains a static trace, and marrow R5 remains pending.

### 8.35 Native axial PCL body — accepted once demonstrated, 2026-10-18

The existing production path now supplies a competent local native axial PCL body description
through `scripts/run_interiors.py`. This is the once-demonstrated anatomical increment; it does
not claim whole-course or volume completeness, general accuracy, a full three-plane PCL
reference, or whole-pipeline efficiency. The lead's source-pinned acceptance and independent
checks are recorded in
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/pcl-axial-checkpoint/lead-acceptance.json`.

The adapter validates the identified native non-fat-suppressed sagittal a1 PCL support and its
address before accessing the source volume. It selects the unique largest source by physical
area; ties remain named, and the inspected wrong-source cases remain in the evidence. Actual
half-slab axial fat-suppressed profiles and the current common-map point provide candidate
maxima. The crop uses the full authored anatomical extent around the source point as a point
within the object, not as its centre. Within that crop, the existing positive enclosed-darkness
reading, existing 3 mm PCL-body opening, four-connected whole components and existing 2 mm
source contact are applied; a unique largest contacting body is selected. Exact ties, measured
empty support and unavailable readings remain distinct. The selected native axial support comes
from the native body measurement, independently of projected target cardinality. Window
completeness remains separate from body identification. Source/profile readings are shared
through `native_meniscus_profiles` and `enclosed_body_at_sources`; new observations enter the
existing common map before dependent requests and the converted rows are reused at final closure.
No new threshold was introduced.

The accepted proof observation is the axial slice15 support of 295 pixels in series
`1.2.826.0.1.3680043.8.498.67495435033389756963800730529101229430`: a compact posterior-notch
body with corners trimmed. The local crop and its unknown exterior remain explicit. Across the
inspected proof, bursa and public observations, the lead judged one demonstration competent,
four identifications wrong, and three local readings measured-empty. The bursa slice2 support
follows distal posterior tibial cortex from its inherited sagittal source. Public100470 slices2
and4 follow posterior vessel-like bodies after a calf-muscle source label outranks the smaller
actual PCL source. Public100628 slice22 follows a posterior/subcutaneous body from posterior
image-edge source specks. The empty readings are bursa slice0 and public100628 slices14/23; they
are local measurements, not anatomical absence. Keep all named rows and refusals; no per-study
patches or withdrawal of the competent proof description follows from these errors.

The accepted source epoch pins 70 files at
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/pcl-axial-production-fixed/verification-source-70/source-hashes.json`
(SHA-256 `a8a5bd7cd1eb1f36e9b4f7bc3e48a25e0a191147e4c33dac1ea05c64163ad2a7`); runner SHA-256
is `e3733ff02804d742ad4e9befe00d9aa8d0bd0bccda60be13de9831769441d27c`. The full gate passes
1,071 tests. Profiled, parallel and public runs exit 0; serial and parallel agree. Zero prior arrays or observations were changed or removed. Proof/bursa add 68 arrays, 3 observations and 1
unresolved row; public adds 97 arrays, 5 observations and 4 unresolved rows. Main receipts are
unchanged. The lead independently reopened 8 actual DICOM frames and checked 521,942 crop pixels,
viewed 13 figures, and recomputed 162 digest flags with the production algorithm: zero actual
digest failures. The audit initially labeled all 162 as checker mismatches because it reshaped
scalar arrays `()` to `(1,)`; the later adjudication confirms 162/162 receipt values match the
project digest. The original flags remain in the full audit; the corrected interpretation is
documented in `pcl-axial-checkpoint/receipt-digest-adjudication.md`.

The structural residual remains shared: source eligibility and selection need already resolved
joint/bone context and the physical notch relation, rather than largest prior label alone. This
is an R5 propagation issue, not a per-study repair. PCL coronal remains pending, so no complete
three-plane PCL reference is claimed. ACL axial/coronal, tibial axial cartilage and other roadmap
families also remain. The retained packet distinguishes local empty from unavailable and
identified readings; its images and full audit are in
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/pcl-axial-checkpoint/`.

### 8.36 Native coronal PCL body and proof three-plane reference — accepted once demonstrated, 2026-10-18

The existing production path now supplies a competent local native coronal PCL body description
and one proof three-plane PCL reference. The lead accepted proof coronal slice22, 322 pixels: a
compact dark body in the posterior notch, consistent with the PCL on sagittal and axial views.
The selected proof planes are SAG18/COR22/AX15. Independent DICOM plane construction yields
LPS position `[-110.95654820639552, -42.08987813891625, 23.75791539106383]`. This is one local
three-plane proof reference, not a complete PCL course or volume, an accuracy claim across studies,
or whole-pipeline efficiency closure.

The coronal reader reuses the existing generic `name_native_pcl_sections` operation. It validates
the addressed native sagittal and axial PCL source rows, considers the actual axial source rows and
their physical areas (preserving ties), and uses actual sagittal and axial half-slab profiles with
the current map to form candidate coronal maxima. The union of source bounds plus the full authored
anatomical extent around the in-object points bounds the native crop before the existing enclosed-
body measurement. The existing 3 mm body opening and four-connected whole components are retained;
a unique largest body contacting both source targets within the existing 2 mm reach supplies the
native coronal support. Ties, partial/empty readings and sources outside the slab remain named.
Support is derived from the native body, not projected target cardinality. The coronal PCL addition
uses no new threshold and adds no per-study patch.

Other inspected coronal contexts remain explicit: bursa slices16/17 are partial, measured-empty
local readings; public100470 slice27 is `other_source_not_in_slab` with no heavy crop, and slice29
is measured-empty locally. These do not imply anatomical absence. The four wrong axial
identifications from §8.35 remain recorded, and the shared R5 source-eligibility residual still
requires resolved joint/bone context and physical notch relation, rather than largest prior label
alone.

The accepted source epoch pins 70 files. The file-byte manifest SHA-256 is
`11e2f799a46e31d58e1763780eb6a3dbb58d32e7f1594290e4c067767e119d12`; the canonical path-hash map
SHA-256 is `d0a2b6d54c2a0cda2d696c9dc57db79b4bb81f45a09bb5d7f21aabe76b9d65bc` (canonical serialization digest, distinct from manifest file bytes); runner SHA-256 is
`a2f9f22323707d8a16253844a3eb98ec14bc0e6c27ed05c49db8a5ccbbe6842d`. The full gate passes 1,087
tests; Vulture advisories remain. Parallel and public runs exited 0. A recorded serial rerun exited
0 and has receipt bytes identical to the original serial and parallel outputs; the original serial
exit status was not retained, and its original run-status record remains preserved. Relative to the
accepted axial epoch, proof/bursa adds 100 arrays and public adds 69; no prior arrays are changed or
removed, and prior observations and unresolved rows are exact prefixes. Main arrays are unchanged.
Two proof fibula main records gain only PCL map-guidance anchors and placements, so main-receipt
identity is not claimed.

The lead reopened 11 actual DICOM frames, checked 279,615 crop pixels and six figures, with zero
failed checks. The completed proof reference adds 40 complete PCL pair vectors; 44 other PCL pairs
remain partial at their other endpoint. It adds 38 prediction rows, 20 residual readings and PCL
anchors in four later retinacular guide uses. These map changes are expected propagation of the new
complete reference; the two raw full-map comparison flags remain preserved alongside the accepted
map-change adjudication. All older complete pairs and non-PCL native geometry remain unchanged.
The proof map contains 21 complete object references and 420 complete ordered pairs; these are
construction counts, not an accuracy measure. Source, receipts, actual-DICOM checks, all figures,
full-map snapshots and adjudications are retained in
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/efficiency-review-20261018/pcl-coronal-checkpoint/`.

The lead's acceptance is `pcl-coronal-checkpoint/lead-acceptance.json`. It completes one competent
coronal description and the proof three-plane reference; it does not finish all PCL pairs or the
whole build. R2 still includes ACL axial/coronal and tibial axial cartilage (its sagittal/coronal
descriptions remain accepted); R3–R6 remain in the roadmap.

### 8.37 Scoped sartorius contrast — 2026-10-18

FULL_BUILD_PLAN P1: the sartorius contrast runs on the gracilis-target window plus its exact surround
halo; the map, every other record and the 188-pixel sheet are unchanged. Evidence:
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/p1-sartorius-scope-20261018/`.
