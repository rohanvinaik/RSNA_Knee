"""A MOVIE: the input to Figure 8 (§2.8). Chapter 1.

From the figure, verbatim:

    A MOVIE: 64 slices × 256 × 256 voxels (about 104 µm a side), at each of about 100
    time points

The knee's input is a study. The knee's version, from the founder, 2026-10-10:

    "We only need the 58 labeled studies. The advantage of a classical/symbolic approach--if it
    works on a handful of cases, scaling up doesn't really add in much utility for training. So
    the 58 are enough."

    "The next chapter is rather clever, you'll enjoy it. For that, we need ALL the data to be
    available for each series, but we will use dimensional collapse to throw away a solid
    majority per analysis step, yet stay lossless. It's rather clever. We use all the data and
    the stored full-fidelity information that we get--*I* decide what gets compressed.
    Otherwise, I agree with your ideas here, let's set things up!"

What he agreed the stage hands on (the lead's proposal of 2026-10-10, accepted in the words
above):
- per study: its series as the host typed them, Fluid_Sensitive and Fat_Suppression each kept
  as given;
- per series: every slice, stacked in order along the slice normal, the values as stored, the
  geometry, and the tags as stored; a missing tag stays missing;
- per training study: each of the 12 labels as "1", "0" or "not_given", and the report text
  (training data only).

Nothing here compresses, rescales, resamples or drops anything.
"""
