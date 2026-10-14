"""The depth collapse: four cheap readings per slice, and each lens standing at the slice where its reading peaks.

**Why it exists, against the thesis.** The collapse in depth (§4): a stack is reduced to the
few slices worth reading in full, by cheap readings made once per slice. "Each is made once, in
milliseconds, where its input first exists, and is kept for any stage to consult. These readings
point, and never decide alone" (§5.1). Two of the four are the thesis's own lenses, Dark Share and
Split Quality (Figure H2a2, panel C). The founder, 2026-10-13, asked whether the squint and the
object picking run on every slice: "Not every slice, not even CLOSE. You might want to poke in on
the <object> thesis, and how it was able to turn a 4D cell microscopy MOVIE into a 2D still. This
is a WAAAAAAAAY easier problem than that to solve." He then confirmed the lead's restatement of the
thesis's mechanism ("Yup! ... This is the right general plan, enough to build off"): each lens is
one cheap number per slice and stands at the one slice where its number peaks; only that slice is
read in full; the other slices keep their cheap readings; a finding that needs another slice is
another lens standing at its own slice, not a walk through the stack. And the same day, with
"Good.": "The cheap number on every slice is how the thesis finds the one slice to read; the cell
build measured simple things on every depth to pick one ... Your 'not every slice' is about the
expensive work, which runs only where each lens stands."

**The four readings, per slice, each float64 (Z,) with NaN for silence**, all from the squint
stack, the first lens and the conjunction, in one pass, no pixel read:
- `kept_share`: the tiles the first lens did not clear (`not_background`, `undecided`) over the
  tiles holding a finite pixel; NaN when a slice holds none.
- `dark_share`: among the kept tiles, those whose median lies at or below the series' split, over
  the kept tiles (the thesis's Dark Share); NaN when the split is not finite or no tile is kept.
- `split_quality`: Otsu's between-class share over the kept tiles' medians (the thesis's Split
  Quality): the largest between-class variance over every two-way cut of the sorted medians,
  divided by their variance; NaN with fewer than two medians or no variance.
- `above_below_share`: the tiles whose conjunction is `above_below` over the tiles whose
  conjunction is one of the nine read pairs (`knee.lenses.conjunction.READ_CONJUNCTIONS`); NaN
  where no conjunction was handed over (a solitary series, or the partner of a pair) or no tile
  read a pair.
Each is a number about the slice and asserts nothing about what the slice holds.

**The decision.** `chosen_slice` stands a lens at the slice where its reading is largest, when
at least `minimum_valid` slices carry a finite reading (design §3: eight, the lead's, his to
change). The chosen slices of the four lenses, deduped, are the series' flat pictures: everything
below operation 4 in the funnel reads those slices in full and no other.

This is the funnel's operation 4 (`openspec/changes/the-funnel/design.md` R4, tasks 4.1 to
4.5). The pure decision is `chosen_slice`; `slice_readings` and `otsu_share` are the measurements
(the former carries the contract); `read_depth` is orchestration. Task 4.4's trace of the cell
build's own slice rule is the lead's and is recorded in the chapter's readings before the unit is
admitted.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from knee.collapse.first_lens import TILE_CODES, FirstLens
from knee.collapse.squint_stack import SquintStack
from knee.compute.contracts import ComputeContract, contracted, handed_on
from knee.lenses.conjunction import CONJUNCTION_CODES, READ_CONJUNCTIONS, Conjunction
from knee.telemetry import ledger

#: The four lenses, in the order their readings and choices are recorded.
LENSES: tuple[str, ...] = (
    "kept_share",
    "dark_share",
    "split_quality",
    "above_below_share",
)

#: What `chosen_slice` can say. `chosen` and `tie_middle` carry an index; the rest carry None.
CHOICE_CODES: tuple[str, ...] = (
    "chosen",
    "tie_middle",
    "all_silent",
    "too_few_valid",
    "invalid_measurement",
)

#: The codes a series' depth collapse reports as a whole.
DEPTH_CODES: tuple[str, ...] = ("present", "predecessor_absent")

#: How many slices must carry a finite reading before a lens may stand anywhere: design §3
#: (`minimum_valid`, "a lens needs eight slices with a reading to stand anywhere; the lead's");
#: the founder changes it. The route hands the request's value when one names it and this when
#: none does.
DEFAULT_MINIMUM_VALID: int = 8


def chosen_slice(
    readings: tuple[float, ...], minimum_valid: int
) -> tuple[int | None, str]:
    """The slice a lens stands at: where its cheap reading peaks (pure -- pinned).

    `readings` is one number per slice in stack order, NaN where the lens was silent;
    `minimum_valid` is the bar, how many slices must carry a finite reading before the lens may
    stand anywhere. A bar that is a bool, not an int, or negative, or `readings` that is not a
    tuple or list of numbers (a bool is not a number), is (None, "invalid_measurement"), the
    refusal, which outranks every silence. No finite reading at all, including no reading, is
    (None, "all_silent"). Fewer finite readings than the bar is (None, "too_few_valid"). Else the
    index of the largest finite reading, (index, "chosen"); when that largest value is attained
    at more than one slice, exactly and with no tolerance, the middle of those slices in stack
    order (the lower of the two middles when their count is even), (index, "tie_middle"). It
    never breaks a tie by any other reading, and it never stands a lens on a silent slice.

    post: __return__[1] in CHOICE_CODES
    post: (__return__[0] is None) == (__return__[1] not in ("chosen", "tie_middle"))
    """
    if isinstance(minimum_valid, bool) or not isinstance(minimum_valid, int):
        return None, "invalid_measurement"
    if minimum_valid < 0 or not isinstance(readings, (tuple, list)):
        return None, "invalid_measurement"
    values: list[float] = []
    for reading in readings:
        if isinstance(reading, bool) or not isinstance(
            reading, (int, float, np.number)
        ):
            return None, "invalid_measurement"
        values.append(float(reading))
    finite = [index for index, value in enumerate(values) if np.isfinite(value)]
    if not finite:
        return None, "all_silent"
    if len(finite) < minimum_valid:
        return None, "too_few_valid"
    largest = max(values[index] for index in finite)
    tied = [index for index in finite if values[index] == largest]
    if len(tied) == 1:
        return tied[0], "chosen"
    return tied[(len(tied) - 1) // 2], "tie_middle"


CONTRACT = ComputeContract(
    kind="measurement",
    language="NumPy over the tile grids, one pass per slice; the Otsu cut by cumulative sums over "
    "the sorted medians; no twin",
    reads="median float64 (Z, TR, TC), finite bool (Z, TR, TC), kept bool (Z, TR, TC), split "
    "float, readable bool (Z, TR, TC) or None, above_below bool (Z, TR, TC) or None",
    writes="four float64 (Z,) readings, NaN for silence",
    allocation="four (Z,) float64 outputs and one sorted copy of a slice's kept medians at a time",
    work="per slice: three counts over TR * TC tiles and one sort of the kept medians with a "
    "cumulative-sum scan",
    parallel_unit="slice",
    reference="slice_readings",
    proof_gate="tests/knee/collapse/test_depth.py: a slice whose kept tiles all lie above the "
    "split has dark_share 0 and one whose kept tiles all lie at or below it has 1; two "
    "well-separated clusters of medians give split_quality above 0.9 and one flat value gives "
    "NaN; a slice with no finite tile gives NaN in every reading; above_below_share is NaN "
    "where no conjunction was handed over and equals the above_below share where one was; no "
    "input is written",
)


def otsu_share(values: np.ndarray) -> float:
    """Otsu's between-class share of a set of values (measurement).

    Sort the finite values ascending, n of them. For every two-way cut k = 1 .. n - 1 the two
    classes are the first k and the rest, with weights k / n and (n - k) / n and their own means;
    the between-class variance at the cut is the product of the two weights times the squared
    difference of the two means. The share is the largest between-class variance over every cut,
    divided by the population variance of all n values. NaN when fewer than two finite values
    remain or their variance is zero. Exact over the sorted values, no histogram, no binning; the
    cut itself is not returned, because the reading is how well the medians split, not where.
    """
    flat = np.asarray(values, dtype=np.float64).ravel()
    ordered = np.sort(flat[np.isfinite(flat)])
    count = int(ordered.size)
    # Fewer than two values, or every value the same (the sorted ends agree, which is exact),
    # is no split to read: NaN, never a share of zero.
    if count < 2 or ordered[0] == ordered[-1]:
        return float("nan")
    total = float(ordered.sum())
    mean = total / count
    variance = float(np.mean((ordered - mean) ** 2))
    if not variance > 0.0:
        return float("nan")
    # Every two-way cut k = 1 .. n - 1 at once: the first k values' sum from one cumulative
    # sum, the rest from the total; the weights and the two means follow.
    below = np.cumsum(ordered)[:-1]
    k = np.arange(1, count, dtype=np.float64)
    weight_below = k / count
    weight_above = 1.0 - weight_below
    mean_below = below / k
    mean_above = (total - below) / (count - k)
    between = weight_below * weight_above * (mean_below - mean_above) ** 2
    return float(between.max() / variance)


@contracted
def slice_readings(
    median: np.ndarray,
    finite: np.ndarray,
    kept: np.ndarray,
    split: float,
    readable: np.ndarray | None,
    above_below: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """The four cheap readings of every slice, from the tile grids alone (measurement).

    `median` float64 (Z, TR, TC) from the squint stack; `finite` bool (Z, TR, TC), the tiles
    holding a finite pixel; `kept` bool (Z, TR, TC), the tiles the first lens did not clear;
    `split` the series' own valley, NaN when none; `readable` bool (Z, TR, TC), the tiles whose
    conjunction is one of the nine read pairs, and `above_below` bool (Z, TR, TC), the tiles
    whose conjunction is `above_below`, both None when no conjunction was handed over. Returns
    `(kept_share, dark_share, split_quality, above_below_share)`, each float64 (Z,), as the
    module docstring defines them, NaN for every silence, frozen. The shapes must agree
    (`invalid_readings_input` otherwise). No input is written.

    pre: median.ndim == 3
    pre: finite.shape == median.shape and kept.shape == median.shape
    post: all(reading.shape == (median.shape[0],) for reading in __return__)
    """
    medians = np.asarray(median, dtype=np.float64)
    held = np.asarray(finite, dtype=bool)
    counted = np.asarray(kept, dtype=bool)
    if (
        medians.ndim != 3
        or held.shape != medians.shape
        or counted.shape != medians.shape
    ):
        raise ValueError("invalid_readings_input")
    paired = readable is not None or above_below is not None
    if paired:
        if readable is None or above_below is None:
            raise ValueError("invalid_readings_input")
        pairs = np.asarray(readable, dtype=bool)
        above_below_tiles = np.asarray(above_below, dtype=bool)
        if pairs.shape != medians.shape or above_below_tiles.shape != medians.shape:
            raise ValueError("invalid_readings_input")
    valley = _split_value(split)
    slices = int(medians.shape[0])
    # Three counts per slice, over the tile grid, in one pass each: the finite tiles, the kept
    # tiles, and the kept tiles whose median lies at or below the split (a NaN median compares
    # false, so an empty tile is never dark).
    finite_count = np.count_nonzero(held, axis=(1, 2)).astype(np.float64)
    kept_count = np.count_nonzero(counted, axis=(1, 2)).astype(np.float64)
    dark_count = np.count_nonzero(counted & (medians <= valley), axis=(1, 2)).astype(
        np.float64
    )
    kept_share = np.full(slices, np.nan, dtype=np.float64)
    dark_share = np.full(slices, np.nan, dtype=np.float64)
    split_quality = np.full(slices, np.nan, dtype=np.float64)
    above_below_share = np.full(slices, np.nan, dtype=np.float64)
    some_finite = finite_count > 0.0
    kept_share[some_finite] = kept_count[some_finite] / finite_count[some_finite]
    some_kept = kept_count > 0.0
    if np.isfinite(valley):
        dark_share[some_kept] = dark_count[some_kept] / kept_count[some_kept]
    # The Otsu cut sorts one slice's kept medians at a time: one sorted copy at a time, as the
    # contract allocates; a slice with no kept tile has nothing to sort and stays NaN.
    for z in np.flatnonzero(some_kept):
        split_quality[z] = otsu_share(medians[z][counted[z]])
    if paired:
        read_count = np.count_nonzero(pairs, axis=(1, 2)).astype(np.float64)
        above_below_count = np.count_nonzero(above_below_tiles, axis=(1, 2)).astype(
            np.float64
        )
        some_read = read_count > 0.0
        above_below_share[some_read] = (
            above_below_count[some_read] / read_count[some_read]
        )
    return (
        handed_on(kept_share),
        handed_on(dark_share),
        handed_on(split_quality),
        handed_on(above_below_share),
    )


@dataclass(frozen=True, slots=True)
class DepthCollapse:
    """One series' depth collapse: the four readings over Z and where each lens stands.

    `kept_share`, `dark_share`, `split_quality`, `above_below_share`: float64 (Z,) in stack
    order, NaN for silence. `chosen_index`: one int per lens in `LENSES` order, the slice it
    stands at, -1 when it stands nowhere; `choice_codes`: that lens's word from `CHOICE_CODES`.
    `chosen_slices`: int64 (K,), the distinct chosen indices ascending, the series' flat
    pictures. `minimum_valid`: the bar the choices were made under. `code` from `DEPTH_CODES`:
    `present` when the stack and the first lens were there to read, whatever the readings said;
    `predecessor_absent` when either was not, with (0,) readings, every lens standing nowhere
    (`all_silent`), no chosen slice, and `why` naming which. A conjunction not handed over is
    `above_below_share` all NaN, never a reading of zero.
    """

    series_uid: str
    code: str
    why: str
    minimum_valid: int
    kept_share: np.ndarray
    dark_share: np.ndarray
    split_quality: np.ndarray
    above_below_share: np.ndarray
    chosen_index: tuple[int, int, int, int]
    choice_codes: tuple[str, str, str, str]
    chosen_slices: np.ndarray


def read_depth(
    stack: SquintStack,
    first: FirstLens,
    conjunction: Conjunction | None,
    split: float,
    minimum_valid: int,
) -> DepthCollapse:
    """Read the four cheap readings of every slice and stand each lens at its peak (orchestration).

    `minimum_valid` that is a bool, not an int, or negative is refused by name,
    `invalid_minimum_valid`, before any ledger event. `split` that is not a number is NaN. Records
    `squint_stack.consumed_by.depth` (stack: 1 when present, else 0), `first_lens.consumed_by.depth`
    (lens: 1 when the lens's code is not `predecessor_absent`, else 0), and, only when
    `conjunction` is not None (never for a None predecessor), `conjunction.consumed_by.depth`
    (conjunction: 1 when its code is `present`, else 0), each at the point of reading. When
    `stack.code` is not `present` or `first.code` is `predecessor_absent`, the collapse is
    `predecessor_absent`. Else `first.codes.shape` must equal `stack.median.shape`
    (`first_lens_does_not_match_stack` otherwise), and a conjunction whose `codes.shape` is not
    that shape is likewise refused (`conjunction_does_not_match_stack`). `finite =
    isfinite(stack.coverage) & (coverage > 0)`; `kept = isin(first.codes, (index of
    not_background, index of undecided))`; `readable = isin(conjunction.codes, the indices of
    READ_CONJUNCTIONS)` and `above_below = conjunction.codes == index of above_below` when a
    `present` conjunction was handed over, else both None; `slice_readings(...)` gives the four;
    for each lens in `LENSES` order `chosen_slice(tuple(reading), minimum_valid)` gives its
    index and word; `chosen_slices` is the sorted distinct set of the indices that are not None.
    Arrays frozen with `handed_on`. Then records `depth.produced` (chosen: how many distinct
    slices; standing: how many lenses stand somewhere). Decides nothing itself beyond applying
    `chosen_slice` per lens.
    """
    # Exactly a Python int: `type(...) is int` refuses a bool (an int to `isinstance`) and a
    # NumPy integer alike, by name, before any ledger event.
    if type(minimum_valid) is not int or minimum_valid < 0:
        raise ValueError("invalid_minimum_valid")
    bar = minimum_valid
    # The consumer records what it read at the point of reading (`specs/route-composition`):
    # the stack and the lens are always handed over, and each count says whether it held a
    # reading; the conjunction is recorded only when one was handed over, never for a None
    # predecessor, which is a solitary series or a partner and no silence of the conjunction's.
    ledger.record(
        "squint_stack.consumed_by.depth", stack=1 if stack.code == "present" else 0
    )
    ledger.record(
        "first_lens.consumed_by.depth",
        lens=1 if first.code != "predecessor_absent" else 0,
    )
    if conjunction is not None:
        ledger.record(
            "conjunction.consumed_by.depth",
            conjunction=1 if conjunction.code == "present" else 0,
        )
    collapse = _read_depth(stack, first, conjunction, _split_value(split), bar)
    ledger.record(
        "depth.produced",
        chosen=int(collapse.chosen_slices.shape[0]),
        standing=sum(1 for index in collapse.chosen_index if index >= 0),
    )
    return collapse


#: The stored indices the orchestration reads, so a code is one byte in the record.
_NOT_BACKGROUND: int = TILE_CODES.index("not_background")
_UNDECIDED: int = TILE_CODES.index("undecided")
_READ_PAIRS: tuple[int, ...] = tuple(
    CONJUNCTION_CODES.index(w) for w in READ_CONJUNCTIONS
)
_ABOVE_BELOW: int = CONJUNCTION_CODES.index("above_below")

#: Where a lens stands when it stands nowhere, and the word for it, in the record.
_NOWHERE: int = -1
_SILENT: str = "all_silent"


def _split_value(split: object) -> float:
    """The split as a float: a number that is not a bool, else NaN, which is no valley at all.

    The first lens reads its split the same way (`knee.collapse.first_lens._split_value`), so
    the two agree on what a split is.
    """
    if isinstance(split, bool) or not isinstance(split, (int, float, np.number)):
        return float("nan")
    return float(split)


def _absent(stack: SquintStack, bar: int, why: str) -> DepthCollapse:
    """The collapse of a series whose stack or first lens was not there to read: the named
    silence, (0,) readings, every lens standing nowhere, no chosen slice, every array frozen."""
    return DepthCollapse(
        series_uid=stack.series_uid,
        code="predecessor_absent",
        why=why,
        minimum_valid=bar,
        kept_share=handed_on(np.empty((0,), dtype=np.float64)),
        dark_share=handed_on(np.empty((0,), dtype=np.float64)),
        split_quality=handed_on(np.empty((0,), dtype=np.float64)),
        above_below_share=handed_on(np.empty((0,), dtype=np.float64)),
        chosen_index=(_NOWHERE, _NOWHERE, _NOWHERE, _NOWHERE),
        choice_codes=(_SILENT, _SILENT, _SILENT, _SILENT),
        chosen_slices=handed_on(np.empty((0,), dtype=np.int64)),
    )


def _read_depth(
    stack: SquintStack,
    first: FirstLens,
    conjunction: Conjunction | None,
    split: float,
    bar: int,
) -> DepthCollapse:
    """The collapse itself: the two silences first, the records' agreement, then the four
    readings and one choice per lens."""
    if stack.code != "present":
        return _absent(
            stack,
            bar,
            f"the squint stack is {stack.code}: {stack.why}; no slice was read",
        )
    if first.code == "predecessor_absent":
        return _absent(
            stack,
            bar,
            f"the first lens is {first.code}: {first.why}; no slice was read",
        )
    shape = tuple(stack.median.shape)
    if tuple(first.codes.shape) != shape:
        error = ValueError("first_lens_does_not_match_stack")
        error.add_note(
            f"first lens codes {tuple(first.codes.shape)}, squint stack median {shape}: "
            f"two records of series {stack.series_uid}"
        )
        raise error
    # A conjunction handed over and `present` is read; one handed over but not made (a
    # predecessor of its own was absent) reads as none, and `above_below_share` is NaN
    # throughout.
    pair = (
        conjunction
        if conjunction is not None and conjunction.code == "present"
        else None
    )
    if pair is not None and tuple(pair.codes.shape) != shape:
        error = ValueError("conjunction_does_not_match_stack")
        error.add_note(
            f"conjunction codes {tuple(pair.codes.shape)}, squint stack median {shape}: "
            f"two records of series {stack.series_uid}"
        )
        raise error
    coverage = np.asarray(stack.coverage, dtype=np.float64)
    finite = np.isfinite(coverage) & (coverage > 0.0)
    kept = np.isin(first.codes, (_NOT_BACKGROUND, _UNDECIDED))
    readable = None if pair is None else np.isin(pair.codes, _READ_PAIRS)
    above_below = None if pair is None else pair.codes == _ABOVE_BELOW
    readings = slice_readings(stack.median, finite, kept, split, readable, above_below)
    choices = [chosen_slice(tuple(reading.tolist()), bar) for reading in readings]
    chosen_index = tuple(
        _NOWHERE if index is None else int(index) for index, _ in choices
    )
    choice_codes = tuple(code for _, code in choices)
    chosen_slices = handed_on(
        np.array(
            sorted({index for index in chosen_index if index >= 0}), dtype=np.int64
        )
    )
    stood = ", ".join(
        f"{lens} at {index} ({code})" if index >= 0 else f"{lens} nowhere ({code})"
        for lens, index, code in zip(LENSES, chosen_index, choice_codes, strict=True)
    )
    return DepthCollapse(
        series_uid=stack.series_uid,
        code="present",
        why=(
            f"{shape[0]} slices of {shape[1]} x {shape[2]} tiles read under a bar of {bar}"
            f"{', no conjunction read' if pair is None else ''}: {stood}; "
            f"{int(chosen_slices.shape[0])} distinct slices chosen"
        ),
        minimum_valid=bar,
        kept_share=readings[0],
        dark_share=readings[1],
        split_quality=readings[2],
        above_below_share=readings[3],
        chosen_index=(
            chosen_index[0],
            chosen_index[1],
            chosen_index[2],
            chosen_index[3],
        ),
        choice_codes=(
            choice_codes[0],
            choice_codes[1],
            choice_codes[2],
            choice_codes[3],
        ),
        chosen_slices=chosen_slices,
    )


__all__ = [
    "CHOICE_CODES",
    "CONTRACT",
    "DEFAULT_MINIMUM_VALID",
    "DEPTH_CODES",
    "LENSES",
    "DepthCollapse",
    "chosen_slice",
    "otsu_share",
    "read_depth",
    "slice_readings",
]
