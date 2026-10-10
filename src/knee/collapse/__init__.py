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
"""
