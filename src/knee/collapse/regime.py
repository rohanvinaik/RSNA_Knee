"""The regime key: the cheap readings of a whole series, taken once, that say what it is.

The thesis, SS5.1, calls these the natural philosopher's toolkit: "Each is made once, in
milliseconds, where its input first exists, and is kept for any stage to consult. These readings
POINT, AND NEVER DECIDE ALONE. A coarse view of the whole field is itself a squint: it settles
whether a plate is dense or sparse... The readings of the whole field, taken once for the movie,
are the priors: its density, its distribution (even, spiky or one-sided), its profile down the
depth, and whether and how the plate drifts. Their words form the REGIME KEY under which a case
from this field is kept."

So a global difference between fields is not divided out of the signal. It is measured once,
named, and carried as the condition under which two fields are comparable. The knee's version
drops drift, which needs a time axis it does not have, and keeps the rest.

This module is an ORCHESTRATION (SS13.7): it moves values between the measurements in `noise.py`
and the decisions in `codes.py`, and decides nothing itself. It consults no label.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from knee.collapse.codes import (
    coil_code,
    concurrence_code,
    normalization_code,
    quiet_code,
    storage_code,
)
from knee.collapse.noise import (
    background_histogram,
    bright_sigma,
    coil_count,
    coil_count_robust,
    dark_sigma,
    finite_values,
    histogram_valley,
    moment_ratio,
    quiet_population,
)
from knee.collapse.units import magnitude_moments, stabilizer, to_units
from knee.study.series import Series, selected_slice

# The Gaussian value of (p95 - p5) / (p75 - p25). A spread at this value is as even as a normal;
# above it the distribution carries more in its tails. Derived, not chosen.
GAUSSIAN_SPREAD_RATIO = 2.4387


@dataclass(frozen=True, slots=True)
class RegimeKey:
    """What one series is, read once and cheaply, before any expensive work runs.

    Identity: `view`, the (plane, fluid-sensitive, fat-suppressed) triple the series table gives.
    The noise law: `dark`, `bright` and `coils`, with the counts each was read from. The words:
    `quiet`, `coils_word`, `concurrence`, `storage` and `normalization`, each a named code. The
    cheap global readings: `zero_share` and `foreground_share` (the knee's density), the `terciles`
    of the above-dark values, `spread_ratio` and `skew` (the distribution's shape), and
    `depth_spread` (its profile along the stack). Every reading is in the series' own stored values
    unless named otherwise. `background_split` retains the whole-series histogram valley
    already used to read the quiet population, so downstream annotations use that same reading.

    The channel count is asked of the background twice, and both answers are kept. `coils` is the
    robust reading, from the quartile ratio, and `coils_word` and the dark sigma are read from it.
    `coils_moment` is a SECOND MEMBER of the same question, from the fourth-to-second moment ratio
    through the identity (L + 1) / L, kept beside the first and never a fallback for it: the
    founder, 2026-10-12, "we always keep information we compute ... the pipeline should keep
    everything, including where things conflict". The identity refuses a ratio outside (1, 2], as
    a contaminated fourth moment makes it, and then `coils_moment` is NaN while `coils` still
    reads; that disagreement is the record, not an error.

    `histogram_counts` and `histogram_edges` are the whole-series histogram the valley was read
    from: one count per bin and one more edge than there are bins, as plain tuples of numbers so
    the writer's enumeration of the fields saves them as it does every other reading. They are
    kept so the field's picture draws the valley on the histogram it came from and no probe
    recomputes one beside it. Both are empty where no histogram could be made, never a row of zero
    counts.

    A reading not made is NaN, never zero.
    """

    view: tuple[str, str, str]
    slices: int
    dark: float
    dark_count: int
    bright: float
    bright_count: int
    coils: float
    quiet: str
    coils_word: str
    concurrence: str
    storage: str
    normalization: str
    zero_share: float
    foreground_share: float
    terciles: tuple[float, float]
    spread_ratio: float
    skew: float
    depth_spread: float
    background_split: float = float("nan")
    foreground_count: int | None = None
    tercile_minimum_population: int = 8
    # THE SECOND SEATED MEMBER's population, and it is not a fallback for the first. `terciles`
    # above is read over the values that carry signal above the noise floor; these are read over the
    # values above the background split, which separates tissue from air. Different invariants, so
    # different populations, so two readings -- which is why both are carried and neither is
    # consulted only when the other is missing. Founder, 2026-10-12: "we always keep information we
    # compute ... the pipeline should keep everything, including where things conflict."
    # `every-stage-renders` task 2.2a.
    split_terciles: tuple[float, float] = (float("nan"), float("nan"))
    split_population_count: int | None = None
    coils_moment: float = float("nan")
    histogram_counts: tuple[int, ...] = ()
    histogram_edges: tuple[float, ...] = ()


def tercile_edges(
    values: np.ndarray, minimum_population: int
) -> tuple[float, float, int]:
    """The 1/3 and 2/3 quantiles of one population, and the population's count (measurement).

    THE ONE STATEMENT of the tercile rule (the-funnel task 3b.1): `_shape_readings` reads the
    regime's own terciles through it, and the tile digits (`knee.lenses.tiles`) read theirs over
    the tiles the first lens did not clear. `values` is the population, already selected by the
    caller, as a float array of any shape; `minimum_population` the bar it is read under, an
    argument and never a constant. Returns `(low, high, count)` with `count = values.size`. Both
    edges are NaN when `minimum_population` is negative (a bar that is no bar), when the count is
    0, or when the count is below the bar; else they are `np.quantile(values, (1/3, 2/3))`,
    exactly as the regime has always read them. A reading not made is NaN, never zero. Decides
    nothing.

    post: __return__[2] == values.size
    """
    count = int(values.size)
    if minimum_population < 0 or count == 0 or count < minimum_population:
        return float("nan"), float("nan"), count
    low, high = (float(q) for q in np.quantile(values, (1 / 3, 2 / 3)))
    return low, high, count


def _shape_readings(
    values: np.ndarray, minimum_population: int = 8
) -> tuple[tuple[float, float], float, float]:
    """The distribution's terciles, its spread ratio against the Gaussian, and its skew's sign.

    The terciles are the 1/3 and 2/3 quantiles: a MIDDLE band, which is what the sibling build
    writes its digits against; they are read through `tercile_edges`, the rule's one statement.
    The spread ratio is (p95 - p5) / (p75 - p25), which reads as 2.4387
    on a normal: above that the tails carry more than a normal's. The skew says which side they
    carry it on, one-sided or even. All three are "even, spiky or one-sided" in SS5.1's words,
    measured rather than named, and all three abstain together under the same bar.
    """
    low, high, count = tercile_edges(values, minimum_population)
    if minimum_population < 0 or count < minimum_population or not count:
        return (low, high), float("nan"), float("nan")
    p5, p25, p75, p95 = (
        float(q) for q in np.quantile(values, (0.05, 0.25, 0.75, 0.95))
    )
    inner = p75 - p25
    ratio = (p95 - p5) / inner if inner > 0 else float("nan")
    centre, spread = float(np.median(values)), inner
    skew = float(np.mean(values) - centre) / spread if spread > 0 else float("nan")
    return (low, high), ratio, skew


def read_regime(
    series: Series,
    min_quiet: int = 1000,
    lag: int = 2,
    single_tolerance: float = 0.25,
    tolerance_errors: float = 3.0,
    foreground_units: float = 3.0,
    block: int = 16,
    floor_quantile: float = 0.1,
    shape_minimum_population: int = 8,
    finite: np.ndarray | None = None,
) -> RegimeKey | None:
    """One series' regime key, read once from its own values and no label.

    The bars this reads -- how few quiet values are too few, the neighbour lag, how many standard
    errors count as concurrence, the block size and the floor's quantile -- are arguments, never
    constants inside a decision. Under Law 4 a level is written down before the run it judges.
    `finite` is which of the volume's values are finite, when the caller has read it once for the
    series; it is read here otherwise, and once.

    None when the series carries no stacked volume: a regime cannot be read from a series whose
    files do not form one stack, and Chapter 1 already says in named codes why they do not.
    """
    if series.volume is None or series.volume.size == 0:
        return None
    volume = np.asarray(series.volume, dtype=np.float64)
    finite = np.isfinite(volume) if finite is None else finite
    values = finite_values(volume, finite)
    if values.size == 0:
        return None

    # The background is cut at the histogram's valley, never at a quantile: a quantile truncates
    # the population and its moments stop being the noise's (see `background_split`). The
    # histogram is made ONCE and the valley read from it, and the same one is kept on the key, so
    # the valley is drawn on the histogram it came from.
    counts, edges = background_histogram(values)
    split = histogram_valley(counts, edges)
    quiet = quiet_population(values, split)
    n_zero = int(np.count_nonzero(quiet == 0.0))
    spread = float(np.std(quiet)) if quiet.size else float("nan")
    quiet_word = quiet_code(quiet.size, n_zero, spread, min_quiet)

    # The channel count comes from the background's QUARTILE ratio, not its moments: measurement
    # showed a handful of leaked tissue values sends the fourth moment to 7.19, outside the
    # identity's range, while quartiles barely move. `coil_code` is pinned against a moment ratio,
    # so the robust count is carried back to its equivalent ratio, (L + 1) / L, exactly.
    coils = coil_count_robust(quiet)
    ratio = (coils + 1.0) / coils if np.isfinite(coils) and coils > 0 else float("nan")
    coils_word = coil_code(ratio, single_tolerance)
    # A coil count the identity refuses is not a reading; one channel is what a magnitude is at
    # minimum, and the dark estimator says so by abstaining rather than by assuming.
    dark = dark_sigma(quiet, coils)

    # The SECOND MEMBER of the channel-count question: the moment-ratio reading of the same quiet
    # population, kept beside the robust one and never a fallback for it. The identity refuses a
    # ratio outside (1, 2] (`coil_count`), as a contaminated fourth moment makes it, and then this
    # member is NaN while the robust one still reads. The word and the dark sigma stay with the
    # robust member. Founder, 2026-10-12: "the pipeline should keep everything, including where
    # things conflict".
    coils_moment = coil_count(moment_ratio(quiet))

    # The bright estimator reads tissue, so its floor is the same valley: above it is tissue. Its
    # slice is the route's middle slice, by the one rule for it.
    middle = volume[selected_slice(int(volume.shape[0]), None) or 0]
    bright, bright_n = bright_sigma(middle, lag, split, block, floor_quantile)

    concurrence = concurrence_code(dark, bright, quiet.size, bright_n, tolerance_errors)

    header = series.slices[0].header if series.slices else None
    representation = int(getattr(header, "PixelRepresentation", -1)) if header else -1
    image_type = tuple(str(v) for v in getattr(header, "ImageType", ()) or ())

    # The level is anchored on the NOISE LAW, never on a quantile of the same distribution. A level
    # taken as a quantile makes the share above it that quantile's complement by construction,
    # which measures nothing: "share above this series' upper tercile is approximately one-third by
    # construction; it cannot measure density" (Codex, 2026-10-10, catching exactly that bug here).
    # So the level is the expected magnitude with NO signal -- a derived quantity -- and the share
    # above it is a real reading of how much of the field carries signal.
    table = stabilizer(dark, coils)
    if table is None:
        level, cut, above = float("nan"), float("nan"), np.empty(0)
    else:
        no_signal, _ = magnitude_moments(np.zeros(1), dark, coils)
        level = float(no_signal[0])
        at_level = float(to_units(np.array([level]), table)[0])
        # the magnitude at which the excess reaches the declared number of noise units
        cut = float(
            np.interp(at_level + foreground_units, table.units, table.magnitude)
        )
        above = values[values > cut]
    terciles, spread_ratio, skew = _shape_readings(above, shape_minimum_population)

    # The second member's population, read with the SAME tercile rule (`tercile_edges`) over a
    # different structural selection: everything above the background split rather than above the
    # noise-law cut. It is computed whether or not the first member resolved, because a seated
    # member does not wait on another's attendance -- measured 2026-10-12, the first places a pair
    # on 2 of 5 acquisitions of one study and this on 5 of 5, and where both read they agreed to
    # within one stored unit. That agreement is overlap, NOT interchangeability (both second
    # readers, independently). Only its terciles are kept, so only they are read: the spread and
    # skew `_shape_readings` reads beside them would be made and thrown away.
    above_split = values[values > split] if np.isfinite(split) else np.empty(0)
    split_low, split_high, _ = tercile_edges(above_split, shape_minimum_population)
    split_terciles = (split_low, split_high)

    # The profile along the stack: how much each slice's own foreground share departs from the
    # series', which is SS5.1's "profile down the depth" without a depth model.
    per_slice = np.array(
        [
            float(np.mean(s[f] > cut)) if np.isfinite(cut) else np.nan
            for s, f in zip(volume, finite, strict=True)
        ]
    )
    depth_spread = float(np.nanstd(per_slice)) if per_slice.size else float("nan")

    return RegimeKey(
        view=(
            series.row.anatomical_plane,
            series.row.fluid_sensitive,
            series.row.fat_suppression,
        ),
        slices=int(volume.shape[0]),
        dark=dark,
        dark_count=int(quiet.size),
        bright=bright,
        bright_count=int(bright_n),
        coils=coils,
        quiet=quiet_word,
        coils_word=coils_word,
        concurrence=concurrence,
        storage=storage_code(representation, int(np.count_nonzero(values < 0))),
        normalization=normalization_code(image_type),
        zero_share=float(np.count_nonzero(values == 0.0) / values.size),
        foreground_share=float(above.size / values.size),
        terciles=terciles,
        spread_ratio=spread_ratio,
        skew=skew,
        depth_spread=depth_spread,
        background_split=split,
        foreground_count=int(above.size),
        tercile_minimum_population=shape_minimum_population,
        split_terciles=split_terciles,
        split_population_count=int(above_split.size),
        coils_moment=coils_moment,
        histogram_counts=tuple(int(c) for c in counts),
        histogram_edges=tuple(float(e) for e in edges),
    )
