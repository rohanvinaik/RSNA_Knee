"""THE COLLAPSE (the squint), Figure 8 (§2.8).

From the figure, verbatim:

    In depth:  Four lenses (Gradient, Contrast, Split Quality, Dark Share), each standing
               at its own sharpest depth, read the volume as flat stills; the composite,
               a fifth flat picture, keeps each place's depth as a number
    In time:   Three anchor time points (t/3, t/2, 2t/3), dividing the movie into a third,
               a sixth, a sixth and a third, are resolved in full; every other time point
               is followed

The knee's version, being taught by the founder (2026-10-10; not complete):

    "The key thing here is that the vast majority of the problem space is actually extremely
    static, both in how thing align and how they differ. All images are of knees, which generally
    look VERY similar. The differences are in the injury, which is specific and definitionally
    measurable."

    "What we need to do is define two things--(1) how does a single study differ across the
    different views of the same knee? By definition, each of the views is of the same thing. ...
    The thing to resolve is how each instrument can serve as a "lens", and how each "lens" appears
    and what it says about each of the 12 categories of diagnoses/study images. Each of the 12 has
    a fairly definable profile, ways in which they are common in a single study and differ in the
    other 11. (2) how do the same views in each of the 12 different categories look different?
    ... the thing that matters here is to find where the data is actually *meaningful* and
    *discriminative*. Most of this is pretty worthless noise that can be washed away. Every knee
    looks, generally, like a knee. So what makes knees that can be categorized thus look
    *different*."

    "We JUST need to be able to say which of the 12 categories each study fits into. That's
    discernment of ANY difference, not exact prediction! Routing, not computation! ... we CAN have
    a categorical routing all-or-nothing approach to categorization, where warranted, and thanks to
    the whole "principled abstention" thing, it can be more measured and balanced of a confidence
    where appropriate!"

His answers to the lead's questions (2026-10-10, after the compaction):

    On the black: ""Black" isn't a color. It's the structural elements of the problem space that
    can be resolved out, because they never contain information or data that is itself
    informative for positive resolution of the categorization we care about. In the cell
    microscopy build, it was literally the "black" space of the microscopy movie. The literal
    pixel count was non-zero, but that space NEVER contained actual cells. That isn't the same as
    "junk", it's important to have positive assignment of what that space is. Rigorous
    characterization of the structural elements that are the equivalent of "black"--parts of the
    data that *aren't* what you care about-- inherently helps resolve the parts you *do* care
    about more cleanly. So in this project, "black" is the space of the data we are given that
    does not actually ever relate in any way to the 12 possible categories, and the context that
    is needed to resolve them. Note here that we actually have SUPER obvious resolution of the
    image. Unlike cells, knee images have a GINORMOUS normalization flag--the giant fucking
    black-ish line that is the connection point between the tibia and femur. It's why the
    "KneeDiff" idea spoke to ideas of aligning different images to a defined normalization, a
    "platonic" version of a knee. Cell microscopy is images of a whole bunch of small objects
    randomly thrown about a plate. Knee imaging is HIGHLY structured; doctors tell people to
    place their knee in the machine and DON'T MOVE while imaging; the images are VERY regular,
    and we should be taking advantage of that. It's about discovering structure and noting where
    we actually can have "surprise" vs where the image is simply uninteresting or common across
    knees, and not waste compute and analysis on the parts that medicine LITERALLY already tries
    to normalize for diagnosis"

    On the specks: ""Speck" refers to appropriate characterization of scale. Again, data is noisy
    and busy. What we need is appropriate characterization of scale. If an object is only
    resolvable as a multi-pixel profile over a certain span, then objects that are definitionally
    WAY below the minimum possible size (e.g. if a knee diagnosis can only appear within X cm
    from the tibia-femur conjunction site, then stuff that's too far from it, or too small to
    represent resolvable damage that is diagnosable, isn't what we need)."

    On the lens: "A lens is a single measurement that is a lossy representation of the problem
    space that allows reconstruction of the problem as a decomposed structure. ... I don't know
    what "focus" has to do with this."

    On the normal knee: "It's why I call it a "platonic ideal" image. It's not one image. But we
    DO have a full representation of "normal". Every element of the knee as an anatomical object
    has a "normal" representation as a superposition of all 58 movies. The "normal" knee is the
    "normal" parts of each of the 58 movies, which are all the parts not labeled or impacted by
    the category of issue they are labeled as having."

    On the labels: "Synovitis is...Synovitis? Is that not a categoy of label? Why are you trying
    to reject the competition labels??"

The knee's collapse (2026-10-10, the teaching pass). His words:

    "The knee's "collapse" is KneeDiff and the above. As for what fills the "lens" role, that's
    for us to reason over, with domain knowledge on knee physiology and medicine and some logic"

    On what the four/five lenses of stage 0 actually were, correcting the lead's reading that they
    measured "focus":

    "the lenses in cell tracking weren't measuring the same property at every place. In fact, none
    of them were trying to measure "focus". That's not a thing that has a measure. There isn't an
    objective measure of "in focus" for every posible interpretation of that word. What those four
    lenses did wasn't really meant as a "measure". The purpose of THOSE four/five lenses was
    different from the other lenses in that project. They are "lenses" in the sense of the project
    epistemology--singular lossy measures that are inherently correct because they simply measure a
    metric, a reading, which is inherently correct, and interpretation is explicitly disclaimed.
    But for these four/five, their "measurment" isn't really a point for interpretation. They
    measure simple metrics--variance in pixel intensity, black/white balance, intensity/coverage,
    etc--for the sake of finding a local minima state that can resolve a single view of cells that
    was analytically useful. That is all. Finding a single slice in each of the four to start the
    first loop of the pipeline."

    "There needs to be SOME grounding consistency. There doesn't need to be perfect identity. The
    lenses there didn't measure the same property at every place. They read one metric--NOT
    focus--at ONE place at a time, and after one loop finished and cells were pulled out each of
    the four pulled out anoter z-plane to resolve for the sake of presenting a clear image to
    process in the pipeline."

    Rejecting "deviation from normal" as a lens:

    "what is "deviation from normal"? What is an objective metric to measure "deviation" or
    "normal"? There isn't."

    What this chapter is:

    "The point of the knee project at THIS stage is to find an analysis frame that allows
    dimensional collapse. Essentially--what is the format of the data we are presented? What are we
    shown, and what about it is categorically something small and resolvable as largely static?
    Basically, the point is to establish the information-theoretic ground here. What is the way
    that we can do a pure, mathematical operation or search or what have you, to produce a single,
    resolvable starting ground that highlights what ACTUALLY matters?"

    KneeDiff, the mechanism:

    "In this project, my ideas was "KneeDiff". Basically, in order for knee scans to MEAN
    something, they all have to look reeeeeally similar. They're roughly the same size, roughly the
    same orientation, the boundary between the femur and tibia is this GIANT fucking dark line
    right in the middle, and most of the rest is just undifferentiated slop. Say you took 100
    different images of knees. There are plenty of tools that can do basic alignment, yes? If not,
    even in the cell tracking project there's a whole "squint" conncept with various
    implementations, which instantiates the idea of intentional lossy representation of data to
    better resolve S/N for significant elements and patterns, like how humans squint to allow
    gestalt priors to better help resole an ambiguous view. In the cell project, one such
    application was a split of the grid into 16x16 chunks of flat representation--an astronomical
    collapse of information fidelity. But just look at this picture: [the 16x16 tile-median
    reduction of a microscopy plane, in which the cells remain plainly visible]"

    "Yes, very lossy. But...you see the cells, right? It's pretty freaking obvious where you see
    "cell" vs the black background. Think about it simply and logically. Knee images are WILDLY
    similar. So just...take a cheap, lossy view, "squint" at a whole stack of them, then
    just...subtract. Even with just the 58 different knees we have annotated, or maybe we can even
    throw in the others from the competition that aren't labeled--we just want to get an average, a
    vibe-y representation of the sites that actually matter or are useful--line up each specific
    view that they provide, kinda shift them around a bit, line them up nicely, then produce a
    single "platonic" study set that has as each view, each image in the study, as an amalgamation
    of ALL the views lined up then subtracted. What would you expect? Well, personally, I'd expect
    most of the data to basically subtract out into near-noise. Low variance, largely drift, very
    obviously not something useful for diagnosis. And in the places that actually carry diagnostic
    information? Mostly I'd expect it to be kinda messy and blobby in those areas, no? Seems like a
    bad thing--it's NOT. This us where the "there is no noise" principle comes into play. Because
    what I described is NOT an undifferentiated mass of blah. What I described are two DIFFERENT
    profiles of "blah". One is spiky, small, and largley pure noise. The other is a definable
    region of clear and obvious uncertainty, places where the studies and images have GENUINE
    differences in what they show--whaich is obviously what we actually CARE about. It LITERALLY
    should produce an amalgamation that explicitly preserves exactly the sites of high variance as
    resolvable points of analysis, places that are diagnostically-significant."

    The discriminator, and the baseline:

    "And how does this relate to actual computer vision? Image data like this is messy. You see a
    knee with a fracture or whatever, most of the image is variable vs any other arbitrary image of
    a knee you might see, and certainly a superimposed combination of a whole bunch of them. But
    WHERE the variance is ACTUALLY diagnostic is definable as (1) a profile of discrete
    variance--where does this knee look NOTABLY different from other knees, with a clean and
    obvious profile (e.g. a giant-ass fracture that shows as a big freaking line that is an
    entropic abnormality that is unmistakable), and (2) variance that SPECIFICALLY shows up in
    places that have distinct pockets of discrete variance that is stubborn and unmistakable.
    Places that are parts of the knee and unimportant have a spiky profile of variance--some
    per-study variance, each image is taken by different people, of different people, at different
    times. But places that correspond EXPLICITLY to places where knee abnormalities show up and are
    diagnosable will have stubborn and persistent pockets of differential presentation that will
    NOT simply go away when you stack many of these study images on top of one another. The
    variance isn't in one random study at a few random spots, it's PERSISTENT and consistent and
    shows up repeatedly in the same general ways and in the same general places. The baseline isn't
    noisiness; it's *entropy*"

    On the task's nature:

    "this project is WAAAAAAAAY easier; the cell tracking project expected us to identify and track
    the exact position of every cell, a literal numerical value. The hard stuff for a classical vs
    neural approach. But here? We JUST need to be able to say which of the 12 categories each study
    fits into."

    "I have another project that's all about routing categorical assignment when the task is simply
    routing to a fixed category set, not a free-floating space of numerical assignment."

His rulings of 2026-10-10 on the lead's two open questions:

    On the finding-to-region map, which the lead had called domain knowledge for him to author:
    "that's actually an objective fact, not something I should be vibing in chat about. Find what
    the current standard approach assigns for them."

    On rare normal variants (discoid meniscus, bipartite patella), which the lead had asked whether
    to treat as abstentions: "the domain space is defined by the competition. If it's not one of
    the 12, then to me it doesn't exist. Log it, we'll come back to it when it comes to "noise
    correction" if needed, but for establishing the ground for this project, it's immaterial by
    definition"

    So: a region that is stubborn-minority but belongs to none of the 12 is not a category of this
    chapter. It is logged as an observation for a later noise-correction pass and is immaterial to
    establishing the ground. Chapter 2 does not model it, name it or abstain on it.

The three-legged stool (2026-10-10). His words:

    "Persist what we need for MOAKS, Hoffa's, AND baker's. In the thesis/cell tracking project we
    called it the "three-legged stool" principle, after the one in Anglicanism; when sources of
    truth are defined as correct but are incomplate but overlapping in their coverage, then the
    places in which they seem to disagree are not noise to wipe away, but are some of the MOST
    informative information we can have"

    This corpus has such a stool, and the competition's host built it deliberately. The 12 labels
    were made by two subspecialty radiologists reading the images independently, a third
    adjudicating; the report was written by one signing radiologist for clinical care; the images
    are what the scanner recorded. The host, asked whether image or report is authoritative where
    they differ: "Yes [the image]. Note that only a small sample of provided data contains both.
    It is intended to help participants surface this conclusion." And on why they differ at all:
    "clinical reports typically involve one signing radiologist who created it for clinical care,
    and the image-based labels uses multiple readers with stricter image-based thresholds."

    A participant's audit of 20 of the 58 measured the two written legs against each other at
    82.5% agreement. That residual is the stool speaking, not noise to clean.

On adding measures (2026-10-10). His words:

    "The addition of additional measures is very much encouraged. Each domain should have its own
    entire universe of lenses/meausres that carry useful or interesting bits of data. None of them
    are wrong. Anything above entropy is genuine information. The *actual* usefulness is something
    we will consider, weigh how to apply, drop if not helpful for interpretation or understanding,
    but the addition of measures and information are never a bad thing."

On the bars, which are empirical rather than declared (2026-10-10). His words:

    On the change level: "The change level is technically mine, but it should be pretty clear from
    the data. I'll provide more discrete ruling if necessary, for which I'll need to see the actual
    photos and how the work we're doing subtracts and produces a genuine "platonic" version, but
    see if it's not already obvious"

    On the coverage count: "Enough. Seems like a circular answer, but it's not something knowable
    in advance. I think the data we have should be enough"

    On the concurrence tolerance: "Another empirical result, the data should speak for us"

    On the unlabeled pool: "There is no unlabeled pool--there is in the competition itself. But
    that's a LOT of data, only worth adding in what we need, if it actually is helpful for the
    build"

THE KNEE IS TWO OBJECTS THAT COMBINE (2026-10-10). The chapter's real decomposition, after the
lead had spent a long stretch tuning histogram statistics without ever rendering an image.

    First, the redirect: "Can you show me? Show me what the literal images look like at this
    stage, and what structure needs to be built to resolve signals? It's about visual reasoning,
    not tuning metrics. "Knee" or sections of the knee that are significant aren't objective
    numbers, they're heuristics about the structure of the problem space that we use to reason
    over the problem space"

    Then the decomposition:

    "structure isn't something you can blindly apply. It has to be re-derived for each problem
    space. For here, you're missing a BIG one: Knees are two objects that combine. The problem
    space is to split the visual field into "<object>"s--the tibia and the femur"

    "Knee injuries aren't some arbitrary thing, they are reasoned deviations from the norm of how
    knees are supposed to work. A tibia and a femur sit into one another, with interstitial fluid
    (that's what they call it, right?) between them. An injury is a breakage, an issue in the way
    they sit in one another. What we need to do is resolve what is the tibia, resolve what is the
    femur, resolve what is the interstitial space, and have it be a structural and deterministic
    resolution. Then, diagnosis is a matter of reasoning over the dynamics between them and how
    these objects sit relative to each other"

    The lead's correction to the term, which he invited ("right?"): the fluid in a joint is
    SYNOVIAL fluid, in the JOINT SPACE (the articular cavity), lined by the SYNOVIUM. Interstitial
    fluid is a different thing, the fluid in tissue spaces generally. It matters because two of
    the twelve name that space: Effusion is excess synovial fluid in it, Synovitis is inflammation
    of its lining.

    What makes the two objects two, and where the mechanism already lives:

    "The answer here, what makes these two objects, is, again, SUPER obvious. The lateral view is
    of the space between them, where synovial fluid sits. The identity of the thing being imaged,
    the direction we're looking (down-->up or up-->down) has to be told to us. But for any images
    that are vertical, it's laughably simple"

    "The difference between tibia and femur? It's the GIANT fucking gap between them. Look into
    the cell tracking project for the way we resolved cells, the "dome" shape, with a discrete
    fall-off in signal intensity that marks the border between the edge of the cell membrane and
    the rest of the field. THat was WAAAAAY harder. That could resolve between HUNDREDS of cells
    in a single plate. Here? We just need to figure out the difference between two GIANT fucking
    objects that almost precisely split the picture right in the middle. It's always in roughly
    the same place, and almost looks the exact same. Compared to cell tracking, it's child's play."

    "Trust the thesis. I promise, the answer exists. I'll help you find it"

    On the background, which the lead HAD got right by connectivity rather than by threshold:
    "the "background" resolution here is REALLY good, just wanted to say that. VERY clean. In the
    images, we can see that some of the views are able to draw the boundary around the black, but
    we're not using the obvious gestalt priors that "fill in" the middle and resolve that as
    background as well."

    So: the leg's boundary is drawn, but the enclosed black is not yet filled. The gestalt prior
    is CLOSURE -- the thesis's own stage 2 "reasons from the gestalt of an <object>: contiguous,
    closed" (SS5.3), and SS4.5 names "the gestalt, the contiguous, closed whole".

WHAT THE IMAGES SHOWED, AND FOUR INSTRUMENTS THAT FAILED (2026-10-10)

    Rendered at last: the middle slice of one series per view, as recorded, squinted, with the
    background marked and the histogram beside it.

    - Air by CONNECTIVITY TO THE FRAME'S BORDER works, and cleanly: about 10-11% of the frame,
      tracing the leg's contour. The founder called it "VERY clean". It is a structural reading,
      so it holds whatever the values are.
    - The squint keeps the knee legible at 8x8 tile medians: femur, tibia, patella and the joint
      space all still readable at a sixty-fourfold loss of fidelity.
    - The joint line's SIGN FLIPS between weightings. On the anatomy sequence the marrow is bright
      and the joint line is the dark band -- the founder's "giant black-ish line". On the
      fluid-sensitive sequence the marrow is mid-grey and the joint space is BRIGHT. Same
      structure, opposite polarity, which is why a digit's meaning must be keyed by weighting.

    Four intensity instruments were tried for cutting background from tissue, and every one
    failed. They are listed so a later reader does not try a fifth:
      1. a QUANTILE (the lowest fifth by value) -- truncates the population, so its moments stop
         being the noise's;
      2. OTSU -- maximises between-class variance, which sits at the valley only when the modes
         carry comparable mass; a knee's background is a narrow spike against broad tissue, so it
         lands far above the valley;
      3. the HISTOGRAM VALLEY (first local minimum after the first peak) -- exact on synthetic
         bimodal data, erratic on real knees, whose histograms carry several tissue modes;
      4. the DARKEST FIFTH inside the leg, meant to find cortical bone -- found the leg's left and
         right edges instead, and "the three largest bodies above it" was one blob.

    The lesson the founder drew: these are objects, not intensity classes, and the reading must be
    structural. "The objects are hard to reason over with numbers. But computer vision is about
    reasoning over *objects*."

================================================================================
WHERE CHAPTER 2 STANDS. Read this first in a new session or after a compaction.
================================================================================

THE CHAPTER'S TASK, in one line: resolve the femur, resolve the tibia, resolve the joint space
between them, structurally and deterministically, so that diagnosis becomes reasoning over how the
two objects sit relative to each other.

BUILT, gated and committed:
  - `codes.py`   the stage's pure decisions, five of them, all Detective-converged COMPLETE.
  - `noise.py`   the noise law per series: a background population, a channel count from the
                 background's QUARTILE ratio (the fourth moment is not robust), a dark estimator,
                 and a bright estimator that reads the noise FLOOR among local blocks with its own
                 sampling bias derived and corrected.
  - `units.py`   the variance-stabilizing transform for the Rician/noncentral-chi family,
                 tabulated per series. Measured quality: within 0.5% above 5 sigma, within 7%
                 through the transition, 11% LOW at pure noise. A null taken in air must use the
                 measured dark-end spread rather than assume one.
  - `regime.py`  the regime key: the cheap whole-field readings taken once per series.

NOT WORKING, and the reason matters:
  Over all 336 series the two noise estimators concur on 4. The ratio between them flipped from
  5.5x to 0.2x across the rebuild, which means the instrument moved and the disagreement did not
  resolve. The founder's ruling on how to proceed is OUTSTANDING -- the three options put to him
  were: keep refining the background instrument; accept that the dark estimator works only where a
  clean background exists and let abstention carry the rest (so concurrence is a READING about
  comparability, not a target); or make the bright estimator primary and the dark its check.

  Do not resume by trying a fifth intensity instrument. Four are listed above with why each failed.

THE REDIRECT, which supersedes the order of work above:
  The founder stopped the noise work and redirected to OBJECTS. The chapter does not need a
  population variance map first; it needs the two bones resolved first, because a deviation has to
  be a deviation OF something. The mechanism is the sibling's dome and seam, already built:

    `instruments/support.py::read_dips` -- local maxima as markers, watershed on the NEGATED image
    so each peak holds a basin, then the saddle between two basins, and
    `seam_depth_flickers(peak_a, peak_b, saddle) = min(peak_a, peak_b) - saddle`, "how far the seam
    dips below the lower of two peaks, IN FLICKERS".

  So two peaks are two objects when the seam between them is deep in units of the noise. That is
  the "discrete fall-off". It is why the transform matters: a dip depth means nothing outside noise
  units.

  For the knee, N = 2 is GIVEN by anatomy rather than discovered, the seam is enormous rather than
  marginal, and the superior-inferior direction is read FROM THE HEADER (Chapter 1's
  `SeriesGeometry.orientation`, LPS, superior is +Z) because "the direction we're looking has to be
  told to us" and the frames are visibly rotated.

OPEN, and the founder's to rule:
  1. the noise law's three options above;
  2. valleys or terciles for a middle's edges, and values or digits into the stack (stage 3);
  3. whether the polarity flip between weightings is one machinery with a sign flip or two
     readings -- on the anatomy sequence the bones are bright and the seam is a dark valley, on
     the fluid-sensitive one the joint space is bright and the seam is a RIDGE;
  4. what "the lateral view is of the space between them" means for which view carries what.

A CLAIM WITHDRAWN: it was said that "there is no background noise in this corpus to measure." That
came from THREE rendered series whose air was nearly all zeros. The 336-series run reported 18.8%
background_masked, not 100%. The corpus-wide air distribution has not been measured.

THE READINGS AND MEASUREMENTS all live in `docs/provenance/`, one file per unit, written before
the next step so a compaction costs one unit rather than a session:
  ch2_design.md                     the chapter's design, with provenance per element
  ch2_the_collapse_resolved.md      the collapse as population, the disagreement geography
  ch2_thesis_math_and_code.md       SS1.3's pooling math, SS13.4's precision ladder, the sibling's code
  ch2_cell_tracking_trace.md        the symbolic trace of the sibling's stage 0
  ch2_competition_definitions.md    the host's own definitions of the 12, the tightest source
  ch2_label_collapse.md             the gold labels' ternary fold and what it reaches
  ch2_flicker_port_and_nulls.md     the Rician port, the profiles, the null suite
  ch2_measured_*.md                 corpus shape, geometry spread, noise floor, regime key
  ch2_stage1_fails_on_real_data.md  the 336-series run and the traced causes
  ch2_two_objects_my_reading.md     the dome and seam port, written before consulting
  ch3_the_level_problem.md          stage 3 reframed: there is no level map

THE WAY OF WORKING is `docs/SPINE.md`, "The working loop". The founder corrects the frame; an
apparent blocker is the signal that something has been misframed, and goes to him with the framing
laid bare and no verdict attached.
"""
