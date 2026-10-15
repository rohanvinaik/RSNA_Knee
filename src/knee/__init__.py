"""The knee: one run that resolves the parts of the knee in any study it is given.

The names are the roles of Figure 8 of *What an <Object> Is* (§2.8, "Road Map"), the whole system
from a movie to its output, in ``cell_tracking/docs/pipeline_thesis/paper/what_an_object_is.md``.
The route a study takes, in its order:

    study       A MOVIE, the input: a study's files read whole, each series stacked along its slice
                normal, nothing compressed, rescaled, resampled or dropped.
    collapse    THE COLLAPSE: the cheap whole-series measures that point where the expensive work
                runs (the background split, and the squint over every slice), and each slice's
                frame in the scanner's millimetres.
    objects     THE OBJECTS: the lens, one slice's geometric interiors and the dark bands at their
                borders (`objects.interiors`), and each part of the knee named from it, an
                «<object>» (`objects.assignments`).

Beside the line, below every stage:

    compute     the contract every numeric kernel carries, and `handed_on`, which freezes a
                reading handed to another stage.
    telemetry   the ledger of counted work, the route check of what no stage read, and `once`:
                each value two stages need, made once and handed on.
    receipt     the run's receipt: every study's records kept, one study's replaced at a time.

The run is `scripts/run_interiors.py`. The thesis is `docs/THEORY_OF_THE_CASE.md`; how each part is
resolved, by which views, lenses and operations, is `docs/RESOLVING_THE_PARTS.md`; how it is built,
and every correction that taught it, is `docs/HOW_TO_BUILD.md`.
"""
