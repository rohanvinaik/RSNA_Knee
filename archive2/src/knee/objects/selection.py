"""The selection: which territories are the objects, by structural facts, never by a name.

**Why it exists, against the thesis.** An `<object>` is "a resolvable sub-set of the visual field"
and recognition "SHOULD actually be something we can do mechanically ... we should be able to
isolate the components of the knee with NO recognition, pure math" (the founder, 2026-10-11 and
2026-10-12). The settled record: anatomy lives in the design, never in the record; what selects
an object for a rule is a structural fact an earlier stage computed. The founder on the knee: "two
GIANT fucking objects that almost precisely split the picture right in the middle. It's always in
roughly the same place, and almost looks the exact same"; on the views (2026-10-13): "the other
views shouldn't speak to the axial view ... Different photo with different rules/roles/objects."
So each kind of view has its own rule, nothing is carried between views, and every territory is
kept, selected or not.

**The facts, per territory** (`TerritoryFacts`, measurements from the dome's labels and the
stack's tile centres in the scanner's LPS millimetres: +x is the patient's left, +y posterior,
+z superior, so anterior is -y): the tile count; the centre; the centre's superior, anterior and
left-right coordinates; the superior extent (lowest and highest tile centre); the anterior face
(the most anterior tile centre); whether the territory touches a tile the first lens cleared or
left undecided (the leg's border); whether it is ringed (every four-neighbour of its tiles outside
it is an obstacle tile).

**The decisions, one per kind of view** (the kind is `SeriesRow.anatomical_plane`, told). On a
coronal or sagittal plane the two largest territories by tile count are the big pair: the one
whose centre is more superior is `superior_big`, the other `inferior_big`; a tie in count is
broken by superior position and said. On the sagittal, a territory smaller than `superior_big`,
with its centre anterior of `superior_big`'s centre and its superior coordinate between
`inferior_big`'s superior face and `superior_big`'s centre, is `anterior_small`. On the coronal, a
territory smaller than `inferior_big`, ringed, with its centre below `inferior_big`'s superior
face and beside it, is `lateral_small_ringed`, the witness whose side gives the laterality sign
(`knee.objects.laterality`). On the axial the largest territory is `central_big` and the largest
territory smaller than it with its centre anterior of its centre is `anterior_small`. Every other
territory is `unselected` and kept. The design glosses (femur, tibia, patella, fibula) stay in the
design.

This is the funnel's operation 5b (`openspec/changes/the-funnel/design.md` R5b, tasks 5b.1 to
5b.5). The pure decisions are `big_pair_code`, `anterior_small_code`, `lateral_witness_code` and
`axial_code`; `territory_facts` is the measurement; `read_selection` is orchestration.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import NamedTuple

import numpy as np

from knee.collapse.first_lens import TILE_CODES, FirstLens
from knee.collapse.squint_stack import SquintStack
from knee.compute.contracts import handed_on
from knee.objects.laterality import lateral_sign_code
from knee.objects.tile_dome import TileDome
from knee.telemetry import ledger

#: The role an object record carries: structural words, never anatomy.
ROLE_CODES: tuple[str, ...] = (
    "superior_big",
    "inferior_big",
    "anterior_small",
    "lateral_small_ringed",
    "central_big",
    "unselected",
)

#: What the big-pair decision can say of a slice's territories.
PAIR_CODES: tuple[str, ...] = (
    "selected",
    "one_big_only",
    "tie",
    "none",
    "invalid_measurement",
)

#: What the candidate decisions can say of one territory.
ANTERIOR_CODES: tuple[str, ...] = (
    "anterior_small",
    "not_small",
    "not_anterior",
    "not_near_the_end",
    "invalid_measurement",
)
WITNESS_CODES: tuple[str, ...] = (
    "lateral_small_ringed",
    "not_small",
    "not_ringed",
    "not_below_the_face",
    "not_beside",
    "invalid_measurement",
)

#: What a slice's selection reports as a whole.
SELECTION_CODES: tuple[str, ...] = ("present", "no_territory", "predecessor_absent")

#: The kinds of view the selection knows, as the series table spells them.
PLANE_KINDS: tuple[str, ...] = ("Coronal", "Sagittal", "Axial")

#: The default floor on a territory's tile count for the selection's decisions. The lead's,
#: 2026-10-13: four tiles at 8 mm is 32 mm across, below any big object and above a speck; the
#: founder changes it by eye. The route passes it as an argument; nothing here reads it.
MINIMUM_TILES: int = 4

#: The stored indices of the two first-lens codes that mark the leg's border: the tiles the lens
#: cleared, and the undecided buffer it kept in play (`knee.collapse.first_lens.TILE_CODES`).
_BACKGROUND: int = TILE_CODES.index("background")
_UNDECIDED: int = TILE_CODES.index("undecided")

#: The role of a territory no rule named.
_UNSELECTED: str = "unselected"


def _finite(*values: float) -> bool:
    return all(
        not isinstance(v, bool) and isinstance(v, (int, float)) and math.isfinite(v)
        for v in values
    )


def _count(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value >= 0


def big_pair_code(
    areas: tuple[int, ...], superior_mm: tuple[float, ...], minimum_tiles: int
) -> tuple[int | None, int | None, str]:
    """The two largest territories, the more superior named first (pure -- pinned).

    `areas` is each territory's tile count and `superior_mm` its centre's superior coordinate,
    in territory order; `minimum_tiles` is the bar a territory must reach to be a candidate (an
    argument; the founder changes it). Lengths that differ, a count that is not a non-negative
    int, a coordinate that is not a finite number, or a bar that is not a non-negative int, is
    (None, None, "invalid_measurement"). No candidate is (None, None, "none"); one is (index,
    None, "one_big_only"). Else the two largest by count: of equal counts the more superior
    comes first, and the word is "tie" instead of "selected"; the two are returned as
    (superior index, inferior index), the more superior centre first; two centres equally
    superior are also "tie", the lower index first. Exact comparisons, no tolerance.

    post: __return__[2] in PAIR_CODES
    post: (__return__[0] is None) == (__return__[2] in ("none", "invalid_measurement"))
    """
    if (
        not isinstance(areas, (tuple, list))
        or not isinstance(superior_mm, (tuple, list))
        or len(areas) != len(superior_mm)
        or not _count(minimum_tiles)
        or not all(_count(a) for a in areas)
        or not all(_finite(s) for s in superior_mm)
    ):
        return None, None, "invalid_measurement"
    candidates = [i for i, a in enumerate(areas) if a >= minimum_tiles]
    if not candidates:
        return None, None, "none"
    if len(candidates) == 1:
        return candidates[0], None, "one_big_only"
    ordered = sorted(candidates, key=lambda i: (-areas[i], -superior_mm[i], i))
    first, second = ordered[0], ordered[1]
    tied = areas[first] == areas[second] or (
        len(ordered) > 2 and areas[second] == areas[ordered[2]]
    )
    if superior_mm[first] == superior_mm[second]:
        sup, inf = (first, second) if first < second else (second, first)
        return sup, inf, "tie"
    if superior_mm[first] > superior_mm[second]:
        sup, inf = first, second
    else:
        sup, inf = second, first
    return sup, inf, "tie" if tied else "selected"


def anterior_small_code(
    area: int,
    big_area: int,
    anterior_mm: float,
    big_anterior_mm: float,
    superior_mm: float,
    inferior_face_mm: float,
    big_centre_superior_mm: float,
) -> str:
    """Whether one territory is the small object in front of the superior big one (pure -- pinned).

    `area`, `anterior_mm`, `superior_mm` are the candidate's; `big_area`, `big_anterior_mm`,
    `big_centre_superior_mm` the superior big object's; `inferior_face_mm` the inferior big
    object's superior face (its most superior tile centre). Non-numbers are
    "invalid_measurement". A candidate at least as large as the big one is "not_small"; one whose
    centre is not anterior of the big one's centre is "not_anterior"; one whose superior
    coordinate does not lie between the inferior object's superior face and the superior
    object's centre is "not_near_the_end"; else "anterior_small". Strict comparisons.

    post: __return__ in ANTERIOR_CODES
    """
    if not (
        _count(area)
        and _count(big_area)
        and _finite(
            anterior_mm,
            big_anterior_mm,
            superior_mm,
            inferior_face_mm,
            big_centre_superior_mm,
        )
    ):
        return "invalid_measurement"
    if area >= big_area:
        return "not_small"
    if anterior_mm <= big_anterior_mm:
        return "not_anterior"
    low, high = sorted((inferior_face_mm, big_centre_superior_mm))
    if not low < superior_mm < high:
        return "not_near_the_end"
    return "anterior_small"


def lateral_witness_code(
    area: int,
    big_area: int,
    ringed: bool,
    superior_mm: float,
    big_superior_face_mm: float,
    left_right_offset_mm: float,
) -> str:
    """Whether one territory is the small ringed object beside the inferior big one (pure -- pinned).

    `area`, `ringed`, `superior_mm` are the candidate's; `big_area` and `big_superior_face_mm`
    the inferior big object's tile count and superior face; `left_right_offset_mm` the
    candidate's centre minus the big one's along the patient's left-right axis. Non-numbers, or a
    `ringed` that is not a bool, are "invalid_measurement". At least as large as the big one is
    "not_small"; not ringed is "not_ringed"; a centre not below the big one's superior face is
    "not_below_the_face"; an offset of exactly zero is "not_beside"; else "lateral_small_ringed".

    post: __return__ in WITNESS_CODES
    """
    if not (
        _count(area)
        and _count(big_area)
        and isinstance(ringed, bool)
        and _finite(superior_mm, big_superior_face_mm, left_right_offset_mm)
    ):
        return "invalid_measurement"
    if area >= big_area:
        return "not_small"
    if not ringed:
        return "not_ringed"
    if superior_mm >= big_superior_face_mm:
        return "not_below_the_face"
    if left_right_offset_mm == 0.0:
        return "not_beside"
    return "lateral_small_ringed"


def axial_code(
    areas: tuple[int, ...], anterior_mm: tuple[float, ...], minimum_tiles: int
) -> tuple[int | None, int | None, str]:
    """The axial view's own rule: the largest territory and the one in front of it (pure -- pinned).

    `areas` and `anterior_mm` per territory, `minimum_tiles` the candidate bar, as for
    `big_pair_code`, with the same refusals. No candidate is (None, None, "none"). The largest
    candidate is the central object (ties by lower index, and the word is "tie"); the largest
    other candidate whose centre is anterior of the central one's centre is the anterior object,
    (central, anterior, "selected"); none anterior is (central, None, "one_big_only").

    post: __return__[2] in PAIR_CODES
    post: (__return__[0] is None) == (__return__[2] in ("none", "invalid_measurement"))
    """
    if (
        not isinstance(areas, (tuple, list))
        or not isinstance(anterior_mm, (tuple, list))
        or len(areas) != len(anterior_mm)
        or not _count(minimum_tiles)
        or not all(_count(a) for a in areas)
        or not all(_finite(a) for a in anterior_mm)
    ):
        return None, None, "invalid_measurement"
    candidates = sorted(
        (i for i, a in enumerate(areas) if a >= minimum_tiles),
        key=lambda i: (-areas[i], i),
    )
    if not candidates:
        return None, None, "none"
    central = candidates[0]
    tied = len(candidates) > 1 and areas[candidates[1]] == areas[central]
    front = [i for i in candidates[1:] if anterior_mm[i] > anterior_mm[central]]
    if not front:
        return central, None, "tie" if tied else "one_big_only"
    return central, front[0], "tie" if tied else "selected"


@dataclass(frozen=True, slots=True)
class TerritoryFacts:
    """One territory's structural facts, every one a number or a bool with its unit and frame.

    `index`: the label in the dome's `labels`. `tiles`: its tile count. `centre_lps`: float64
    (3,) mm, the mean of its tiles' centres. `superior_mm`, `anterior_mm`, `left_right_mm`: that
    centre's +z, -y and +x in LPS. `superior_extent_mm`: (lowest, highest) tile-centre z.
    `anterior_face_mm`: the most anterior tile-centre -y. `touches_leg_border`: a tile of it is
    four-adjacent to a tile the first lens cleared or left undecided. `ringed`: every tile
    four-adjacent to it and outside it is an obstacle of the dome.
    """

    index: int
    tiles: int
    centre_lps: np.ndarray
    superior_mm: float
    anterior_mm: float
    left_right_mm: float
    superior_extent_mm: tuple[float, float]
    anterior_face_mm: float
    touches_leg_border: bool
    ringed: bool


@dataclass(frozen=True, slots=True)
class ObjectRecord:
    """One territory with its role: `(index, role_code, facts, tiles)`; no anatomical word."""

    index: int
    role_code: str
    facts: TerritoryFacts
    tiles: int


@dataclass(frozen=True, slots=True)
class Selection:
    """One chosen slice's objects by role, every territory kept.

    `plane_kind`: the told plane word the rule was chosen by. `objects`: one `ObjectRecord` per
    territory of the dome, in label order, `unselected` where no rule named it. `pair_code`: the
    big-pair or axial decision's word; `candidate_codes`: per territory, the anterior or witness
    decision's word on it (empty on a kind with no such decision). `code` from
    `SELECTION_CODES`: `present` when the dome held territories, `no_territory` when it held none,
    `predecessor_absent` when the dome was not present. `border`: the dome's border word
    (`knee.objects.tile_dome.BORDER_CODES`) this selection was read from.
    """

    series_uid: str
    slice_index: int
    plane_kind: str
    code: str
    why: str
    pair_code: str
    objects: tuple[ObjectRecord, ...]
    candidate_codes: tuple[str, ...]
    border: str


@dataclass(frozen=True, slots=True)
class SelectionWithSign:
    """One slice's `Selection` together with the laterality sign its witness gives.

    `selection`: the `Selection`, as `read_selection` made it. `lateral_sign`: a word from
    `knee.objects.laterality.SIGN_CODES`, `lateral_sign_code` applied to the Coronal witness's
    offset along the patient's left-right axis (the witness's `left_right_mm` minus the inferior
    big object's); `side_abstained` wherever no witness was selected: on every Sagittal and Axial
    slice, which have no witness rule, and on a Coronal slice with no `lateral_small_ringed`
    territory. Kept beside the `Selection` and not in it, because the `Selection`'s fields are the
    lead's; every side-dependent code downstream takes this word and abstains with it.
    """

    selection: Selection
    lateral_sign: str


def territory_facts(
    labels: np.ndarray,
    obstacle: np.ndarray,
    first_codes: np.ndarray,
    centres_lps: np.ndarray,
) -> tuple[TerritoryFacts, ...]:
    """Every territory's facts from the dome's labels and the stack's tile centres (measurement).

    `labels` int32 (TR, TC) and `obstacle` bool (TR, TC) from the dome of one slice;
    `first_codes` uint8 (TR, TC) the first lens's codes at that slice; `centres_lps` float64
    (TR, TC, 3) that slice's tile centres in LPS mm. One `TerritoryFacts` per label 1..P in
    label order, as the class docstring defines each field; a territory with no tile (a label
    skipped by the watershed) is absent from the result. Shapes that disagree are refused by
    name, `selection_inputs_disagree`. No input is written.
    """
    grid = np.asarray(labels)
    blocked = np.asarray(obstacle)
    codes = np.asarray(first_codes)
    centres = np.asarray(centres_lps)
    # The four inputs describe one grid or none of them is read. A representation that is not the
    # one the docstring declares (integer labels and codes, a bool obstacle, float centres) is the
    # same disagreement: a coerced float label would turn a missing reading into a territory.
    if (
        grid.ndim != 2
        or blocked.shape != grid.shape
        or codes.shape != grid.shape
        or centres.shape != (*grid.shape, 3)
        or grid.dtype.kind not in "iu"
        or blocked.dtype != np.bool_
        or codes.dtype.kind not in "iu"
        or centres.dtype.kind != "f"
    ):
        raise ValueError("selection_inputs_disagree")
    centres = centres.astype(np.float64, copy=False)
    # The leg's border: the tiles the first lens cleared or left undecided. A territory touches it
    # where one of its tiles is four-adjacent to such a tile, whether or not that tile is the
    # territory's own (the dome keeps the undecided buffer in play, so a territory can hold it).
    beside_border = _beside(np.isin(codes, (_BACKGROUND, _UNDECIDED)))
    facts: list[TerritoryFacts] = []
    for label in np.unique(grid[grid > 0]):
        mask = grid == label
        here = centres[mask]
        centre = here.mean(axis=0)
        ring = _beside(mask) & ~mask
        facts.append(
            TerritoryFacts(
                index=int(label),
                tiles=int(np.count_nonzero(mask)),
                centre_lps=handed_on(centre),
                superior_mm=float(centre[2]),
                # Anterior is -y in LPS; `0.0 - y` keeps a centre at y = 0 from reading -0.0.
                anterior_mm=float(0.0 - centre[1]),
                left_right_mm=float(centre[0]),
                superior_extent_mm=(float(here[:, 2].min()), float(here[:, 2].max())),
                anterior_face_mm=float((0.0 - here[:, 1]).max()),
                touches_leg_border=bool(beside_border[mask].any()),
                # Tiles only: a position off the grid is no tile, so it neither encloses nor opens.
                ringed=bool(blocked[ring].all()),
            )
        )
    return tuple(facts)


def _beside(grid: np.ndarray) -> np.ndarray:
    """Which tiles have a four-adjacent tile that is true in `grid` (a tile never counts itself).

    `grid` bool (TR, TC); returns bool (TR, TC), a new array.
    """
    beside = np.zeros(grid.shape, dtype=bool)
    beside[1:, :] |= grid[:-1, :]
    beside[:-1, :] |= grid[1:, :]
    beside[:, 1:] |= grid[:, :-1]
    beside[:, :-1] |= grid[:, 1:]
    return beside


def read_selection(
    dome: TileDome,
    first: FirstLens,
    stack: SquintStack,
    plane_kind: str,
    minimum_tiles: int,
) -> SelectionWithSign:
    """Name each territory's role on one chosen slice by the view's own rule (orchestration).

    `plane_kind` not in `PLANE_KINDS`, or `minimum_tiles` not a non-negative int, is refused by
    name (`invalid_plane_kind`, `invalid_minimum_tiles`) before any ledger event. Records
    `tile_dome.consumed_by.selection` (dome: 1 when `present`) at the point of reading, and the
    first lens's and the stack's consumption likewise. A dome not `present` gives
    `predecessor_absent` (no objects); a dome with no territory gives `no_territory`. Else the
    facts, then: Coronal or Sagittal: `big_pair_code` over the counts and superior coordinates;
    the named pair take `superior_big` and `inferior_big`; on the Sagittal every other territory
    is put to `anterior_small_code` against the pair's facts and the largest "anterior_small"
    takes that role; on the Coronal every other territory is put to `lateral_witness_code`
    against `inferior_big`'s facts (the offset is the candidate's `left_right_mm` minus
    `inferior_big`'s) and the largest "lateral_small_ringed" takes that role. Axial: `axial_code`
    over the counts and anterior coordinates; the central and anterior objects take their roles.
    Every other territory is `unselected`. Then records `selection.produced` (objects: how many
    carry a role other than unselected). Decides nothing beyond applying the four decisions.
    """
    if not isinstance(plane_kind, str) or plane_kind not in PLANE_KINDS:
        raise ValueError("invalid_plane_kind")
    if not _count(minimum_tiles):
        raise ValueError("invalid_minimum_tiles")
    # The consumer records what it read at the point of reading (`specs/route-composition`): the
    # dome, the lens and the stack are always handed over, and each count says whether it held a
    # reading. Nothing is recorded before the two refusals above.
    ledger.record(
        "tile_dome.consumed_by.selection", dome=1 if dome.code == "present" else 0
    )
    ledger.record(
        "first_lens.consumed_by.selection",
        lens=0 if first.code == "predecessor_absent" else 1,
    )
    ledger.record(
        "squint_stack.consumed_by.selection",
        stack=1 if stack.code == "present" else 0,
    )
    result = _read_selection(dome, first, stack, plane_kind, minimum_tiles)
    ledger.record(
        "selection.produced",
        objects=sum(
            1 for item in result.selection.objects if item.role_code != _UNSELECTED
        ),
    )
    return result


class _Reading(NamedTuple):
    """What a view's rule said of one slice's territories, in the order of the facts.

    `roles`: one role code per territory. `pair_code`: the big-pair or axial decision's word.
    `candidate_codes`: the candidate decision's word per territory, "" for a territory it was not
    put to, empty on a view with no such decision. `witness_offset_mm`: the Coronal witness's
    offset along the left-right axis, None where no witness was selected. `notes`: words for the
    selection's `why`.
    """

    roles: tuple[str, ...]
    pair_code: str
    candidate_codes: tuple[str, ...]
    witness_offset_mm: float | None
    notes: tuple[str, ...]


def _read_selection(
    dome: TileDome,
    first: FirstLens,
    stack: SquintStack,
    plane_kind: str,
    minimum_tiles: int,
) -> SelectionWithSign:
    """The selection itself: the two silences first, then the facts and the view's own rule."""
    if dome.code != "present":
        return _silent(
            dome,
            plane_kind,
            minimum_tiles,
            "predecessor_absent",
            f"the tile dome is {dome.code} ({dome.why}), so no territory was put to a rule",
        )
    facts = _slice_facts(dome, first, stack)
    if not facts:
        return _silent(
            dome,
            plane_kind,
            minimum_tiles,
            "no_territory",
            f"the tile dome at slice {dome.slice_index} holds no territory (every label is 0), "
            "so none was put to a rule",
        )
    reading = (
        _axial_roles(facts, minimum_tiles)
        if plane_kind == "Axial"
        else _paired_roles(plane_kind, facts, minimum_tiles)
    )
    sign = lateral_sign_code(reading.witness_offset_mm)
    taken = [
        f"{role} is label {item.index}"
        for item, role in zip(facts, reading.roles, strict=True)
        if role != _UNSELECTED
    ]
    why = (
        f"{plane_kind} slice {dome.slice_index}: {len(facts)} territories; the pair rule says "
        f"{reading.pair_code}; "
        + (", ".join(taken) if taken else "no territory took a role")
        + "".join(f"; {note}" for note in reading.notes)
        + f"; lateral sign {sign}"
    )
    selection = Selection(
        series_uid=dome.series_uid,
        slice_index=int(dome.slice_index),
        plane_kind=plane_kind,
        code="present",
        why=why,
        pair_code=reading.pair_code,
        objects=tuple(
            ObjectRecord(index=item.index, role_code=role, facts=item, tiles=item.tiles)
            for item, role in zip(facts, reading.roles, strict=True)
        ),
        candidate_codes=reading.candidate_codes,
        border=dome.border,
    )
    return SelectionWithSign(selection=selection, lateral_sign=sign)


def _silent(
    dome: TileDome, plane_kind: str, minimum_tiles: int, code: str, why: str
) -> SelectionWithSign:
    """A selection that named no territory: its silence, with the view's pair rule put to nothing."""
    decide = axial_code if plane_kind == "Axial" else big_pair_code
    selection = Selection(
        series_uid=dome.series_uid,
        slice_index=int(dome.slice_index),
        plane_kind=plane_kind,
        code=code,
        why=why,
        pair_code=decide((), (), minimum_tiles)[2],
        objects=(),
        candidate_codes=(),
        border=dome.border,
    )
    return SelectionWithSign(selection=selection, lateral_sign=lateral_sign_code(None))


def _slice_facts(
    dome: TileDome, first: FirstLens, stack: SquintStack
) -> tuple[TerritoryFacts, ...]:
    """The facts of the dome's slice, from the lens's codes and the stack's centres at its index.

    A slice index that is not a whole number inside both the lens and the stack, or a lens or a
    stack that is not shaped like a series' record, is the same disagreement as a grid that does
    not fit: `selection_inputs_disagree`, never an `IndexError`.
    """
    index = dome.slice_index
    codes = np.asarray(first.codes)
    centres = np.asarray(stack.centres_lps)
    if (
        isinstance(index, (bool, np.bool_))
        or not isinstance(index, (int, np.integer))
        or codes.ndim != 3
        or centres.ndim != 4
        or not 0 <= index < min(codes.shape[0], centres.shape[0])
    ):
        raise ValueError("selection_inputs_disagree")
    return territory_facts(dome.labels, dome.obstacle, codes[index], centres[index])


def _paired_roles(
    plane_kind: str, facts: tuple[TerritoryFacts, ...], minimum_tiles: int
) -> _Reading:
    """The Coronal's and the Sagittal's rule: the big pair, then the one candidate role of the view.

    The pair rule names positions in `facts`. Roles go only to a named pair, so a single big
    territory (`one_big_only`) keeps no big role: it is not known to be the superior or the
    inferior one. Every other territory is put to the view's candidate decision against the pair's
    facts; the largest to answer with the view's word takes the role, equal sizes going to the
    lower position, which is said.
    """
    count = len(facts)
    high, low, pair_word = big_pair_code(
        tuple(item.tiles for item in facts),
        tuple(item.superior_mm for item in facts),
        minimum_tiles,
    )
    roles = [_UNSELECTED] * count
    candidates = [""] * count
    notes: list[str] = []
    offset: float | None = None
    if high is not None and low is not None:
        roles[high], roles[low] = "superior_big", "inferior_big"
        big, under = facts[high], facts[low]
        wanted = (
            "anterior_small" if plane_kind == "Sagittal" else "lateral_small_ringed"
        )
        for position, item in enumerate(facts):
            if position in (high, low):
                continue
            if plane_kind == "Sagittal":
                candidates[position] = anterior_small_code(
                    item.tiles,
                    big.tiles,
                    item.anterior_mm,
                    big.anterior_mm,
                    item.superior_mm,
                    under.superior_extent_mm[1],
                    big.superior_mm,
                )
            else:
                candidates[position] = lateral_witness_code(
                    item.tiles,
                    under.tiles,
                    item.ringed,
                    item.superior_mm,
                    under.superior_extent_mm[1],
                    item.left_right_mm - under.left_right_mm,
                )
        answering = [p for p, word in enumerate(candidates) if word == wanted]
        if answering:
            taker = max(answering, key=lambda p: (facts[p].tiles, -p))
            roles[taker] = wanted
            equal = [p for p in answering if facts[p].tiles == facts[taker].tiles]
            if len(equal) > 1:
                notes.append(
                    f"{len(equal)} equally large {wanted} territories, the lowest label took it"
                )
            if plane_kind == "Coronal":
                # The sign is never a guess: equally large witnesses on both sides of the
                # inferior big object leave the side unknown, so the sign abstains (the lead's
                # ruling of 2026-10-13, on the checker's finding).
                sides = {
                    math.copysign(1.0, facts[p].left_right_mm - under.left_right_mm)
                    for p in equal
                }
                if len(sides) > 1:
                    notes.append(
                        "the equally large witnesses lie on both sides of the inferior big "
                        "object, so the sign abstains"
                    )
                else:
                    offset = facts[taker].left_right_mm - under.left_right_mm
    return _Reading(
        roles=tuple(roles),
        pair_code=pair_word,
        candidate_codes=tuple(candidates),
        witness_offset_mm=offset,
        notes=tuple(notes),
    )


def _axial_roles(facts: tuple[TerritoryFacts, ...], minimum_tiles: int) -> _Reading:
    """The Axial's own rule: the central territory and the one in front of it; no candidate decision."""
    central, front, pair_word = axial_code(
        tuple(item.tiles for item in facts),
        tuple(item.anterior_mm for item in facts),
        minimum_tiles,
    )
    roles = [_UNSELECTED] * len(facts)
    if central is not None:
        roles[central] = "central_big"
    if front is not None:
        roles[front] = "anterior_small"
    return _Reading(
        roles=tuple(roles),
        pair_code=pair_word,
        candidate_codes=(),
        witness_offset_mm=None,
        notes=(),
    )


__all__ = [
    "ANTERIOR_CODES",
    "MINIMUM_TILES",
    "PAIR_CODES",
    "PLANE_KINDS",
    "ROLE_CODES",
    "SELECTION_CODES",
    "WITNESS_CODES",
    "ObjectRecord",
    "Selection",
    "SelectionWithSign",
    "TerritoryFacts",
    "anterior_small_code",
    "axial_code",
    "big_pair_code",
    "lateral_witness_code",
    "read_selection",
    "territory_facts",
]
