"""THE COLLAPSE (the squint), Figure 8 (§2.8) of *What an <Object> Is*.

From the figure, verbatim:

    In depth:  Four lenses (Gradient, Contrast, Split Quality, Dark Share), each standing
               at its own sharpest depth, read the volume as flat stills; the composite,
               a fifth flat picture, keeps each place's depth as a number
    In time:   Three anchor time points (t/3, t/2, 2t/3), dividing the movie into a third,
               a sixth, a sixth and a third, are resolved in full; every other time point
               is followed

For the knee, Rohan, 2026-10-15: «The "middle" is a fine standard first slice to select. For other
elements that are not obvious in that one slice, etc, that is a fine standard. There are five
different views (different angles and fat-bright vs fat-dark), and each has multiple z-slices. That is
where the thing being mined is relevant--discovery of ALL elements of the anatomy at their best slices
and resolution across the 5 images/3 orientations»; and: «I think that you missed the point of this
part of the thesis, and we need to get to fixing the implementation in another session». His method
for a part's slice, 2026-10-14: «Is it not obvious which slice to use? The one that is able to show
the anatomical region needed for identification of each anatomical object, and then for diagnosis.»
The thesis's own text on the collapse is gathered in `docs/RESOLVING_THE_PARTS.md` §8. What the run
does now: it squints every slice of every series (`squint_stack`) and reads one background split per
series (`noise`), then reads the lens on each series' middle slice and on a few parts' own slices
(`scripts/run_interiors.py`).

The modules here, and what each is (SS13.7 keeps the kinds apart):

    noise.py         MEASUREMENTS. The background split per series: the valley after the
                     background's mode in the series' own histogram, the level the lens reads low
                     signal under.
    physical.py      MEASUREMENTS. A slice's plane frame in the scanner's millimetres (its places,
                     the inverse that carries a place onto it, its normal), and one slice's squint.
    squint_stack.py  ORCHESTRATION. The squint over every slice of a series, each tile's centre in
                     the scanner's millimetres: the cheap look at the whole series that points
                     where the expensive work runs.
"""
