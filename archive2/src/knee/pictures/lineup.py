"""What the line-up resolved, drawn: the recipient's tiles and the partner's tile centres on one plane.

The funnel's operation 3a (`openspec/changes/the-funnel/design.md` R3a, task 3a.2):
`knee.collapse.lineup.line_up` names, per recipient slice, the partner slice nearest along the
recipient's normal and, per recipient tile, the partner tile whose centre is nearest in the
scanner's millimetres, each with its named code. Its picture is the one the founder described on
2026-10-13: two pictures of one plane laid over the same knee, "just sorta scootch it a bit" --
the recipient's tile grid over its own acquired plane, each tile tinted by its match code, and the
partner's tile centres at the nearest partner slice placed on that same plane.

Every value here is one the stage computed and the writer saved. Selecting one slice of the saved
line-up is ARRANGING: it chooses which stored values to show and alters none of them. The
recipient's tile centres are read off its saved native bounds (the midpoint of each tile's
half-open bounds, the same point `tile_centres_lps` placed in millimetres); the partner's saved
centres, in millimetres, are placed in the recipient's native frame through the recipient's own
saved plane frame (`PlaneFrame.to_native`), the one affine placement a picture of two grids on
one plane needs. Nothing here measures, thresholds, searches or recomputes a distance; a line-up
that was not saved, one the stage did not make, a slice the line-up does not hold, a partner
slice the stage did not name, a partner stack this run did not save, or a partner slice the
partner's stack does not hold, is a named silence in words, never an empty picture. The one
decision, `slice_standing`, is pure and total and names what the picture at one slice can be.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from knee.collapse.lineup import SLAB_CODES
from knee.collapse.physical import PlaneFrame
from knee.collapse.squint_stack import STACK_CODES
from knee.compute.contracts import handed_on

#: What the picture at one recipient slice can be. `lined_up` is a reading drawn; the rest are the
#: silences, each with its own remedy: this run's writer saved no line-up for the series; the
#: saved code is a word the stage does not say; the stage made no line-up (its own code says
#: why); the slice lies outside the line-up; the stage named no partner slice there; this run
#: holds no saved stack for the partner; the named partner slice lies outside the partner's stack.
SLICE_STANDINGS: tuple[str, ...] = (
    "lined_up",
    "lineup_not_saved",
    "lineup_code_unknown",
    "lineup_absent",
    "slice_outside_lineup",
    "partner_slice_absent",
    "partner_stack_not_saved",
    "partner_slice_outside_stack",
)


def slice_standing(
    code: object,
    index: object,
    slices: int,
    partner_slice: object,
    partner_slices: object,
) -> str:
    """Name what the picture at one recipient slice can show, from the two saved records.

    `code` is the line-up's saved code (`STACK_CODES`: `present` when both stacks were present,
    else the absent stack's own code), or None when the writer saved no line-up for the series;
    `index` the recipient slice to draw; `slices` how many slices the saved line-up holds;
    `partner_slice` the saved partner slice at `index`, -1 where the stage named none;
    `partner_slices` how many slices the partner's saved stack holds, or None when this run holds
    no saved stack for the partner. Total: no saved line-up is `lineup_not_saved`; a code the
    stage does not say, or one that is not text, is `lineup_code_unknown`, named and never drawn;
    a line-up the stage did not make is `lineup_absent`; an index that is not a whole number
    inside the line-up is `slice_outside_lineup`; a partner slice that is not a whole number at or
    above zero is `partner_slice_absent`, the stage's own silence; a partner slice count that is
    not a whole number is `partner_stack_not_saved`; a partner slice at or beyond that count is
    `partner_slice_outside_stack`, a contradiction between the two saved records; else the slice
    is `lined_up`. It selects nothing and counts nothing.

    post: __return__ in SLICE_STANDINGS
    """
    if code is None:
        return "lineup_not_saved"
    if not isinstance(code, str) or code not in STACK_CODES:
        return "lineup_code_unknown"
    if code != "present":
        return "lineup_absent"
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < slices:
        return "slice_outside_lineup"
    if (
        isinstance(partner_slice, bool)
        or not isinstance(partner_slice, int)
        or partner_slice < 0
    ):
        return "partner_slice_absent"
    if isinstance(partner_slices, bool) or not isinstance(partner_slices, int):
        return "partner_stack_not_saved"
    if partner_slice >= partner_slices:
        return "partner_slice_outside_stack"
    return "lined_up"


@dataclass(frozen=True, slots=True)
class LinedUpSlice:
    """One recipient slice of the picture: its standing, and the saved values at that slice.

    index: the recipient slice drawn, as given. standing: from `SLICE_STANDINGS`. partner_index:
    the saved partner slice at `index`, None unless `standing` is `lined_up`. slab_code: the name
    of the saved slab code at `index`, None where `index` lies outside the line-up or the saved
    value is not in the vocabulary. recipient_centres_rc: float64 (TR, TC, 2), each recipient
    tile's centre in its own native (row, column), read off the saved bounds; None when no bounds
    were handed on. partner_centres_rc: float64 (TR', TC', 2), the partner's tile centres at
    `partner_index` in the recipient's native (row, column), placed through the recipient's saved
    frame, NaN where the partner's saved centre is NaN; None unless `standing` is `lined_up` and
    both the partner's centres and the recipient's frame were handed on. partner_tile: int64
    (TR, TC, 2); distance_mm: float64 (TR, TC); match_codes: uint8 (TR, TC): the saved values at
    `index`, None where `index` lies outside the line-up. Nothing is derived.
    """

    index: object
    standing: str
    partner_index: int | None
    slab_code: str | None
    recipient_centres_rc: np.ndarray | None
    partner_centres_rc: np.ndarray | None
    partner_tile: np.ndarray | None
    distance_mm: np.ndarray | None
    match_codes: np.ndarray | None


@dataclass(frozen=True, slots=True)
class LineUpPanels:
    """One recipient's saved line-up, AS THE WRITER SAVED IT, at one slice, ready to be drawn.

    code, why: the line-up's standing as saved, or None when the record carries no line-up at
    all. recipient_uid, partner_uid: the two series as saved. half_tile_mm, half_thickness_mm:
    the bars used, None where the writer saved none (a bar the stage could not read is saved as
    None). normal_angle_deg: the measured angle between the two normals, None where unsaved or
    unread. slices: how many recipient slices the saved line-up holds (0 when none).
    partner_slice: int64 (Z,) and slab_codes: uint8 (Z,), over every recipient slice as saved;
    None when none was saved. at: the one slice drawn. An absent value stays absent, never a
    zero.
    """

    code: str | None
    why: str | None
    recipient_uid: str | None
    partner_uid: str | None
    half_tile_mm: float | None
    half_thickness_mm: float | None
    normal_angle_deg: float | None
    slices: int
    partner_slice: np.ndarray | None
    slab_codes: np.ndarray | None
    at: LinedUpSlice


def tile_centres_rc(bounds_rc: np.ndarray) -> np.ndarray:
    """Each tile's centre in native (row, column), read off its saved half-open bounds.

    The midpoint of the pixels a tile holds, (r0 + r1 - 1) / 2 and (c0 + c1 - 1) / 2: the same
    point `knee.collapse.squint_stack.tile_centres_lps` placed in millimetres. Returns float64
    (TR, TC, 2), newly owned and frozen with `handed_on`; the saved bounds are never written.
    No pixel is read.
    """
    bounds = np.asarray(bounds_rc, dtype=np.float64)
    return handed_on(
        np.stack(
            (
                (bounds[..., 0] + bounds[..., 1] - 1.0) / 2.0,
                (bounds[..., 2] + bounds[..., 3] - 1.0) / 2.0,
            ),
            axis=-1,
        )
    )


def placed_centres_rc(frame: PlaneFrame, centres_lps: np.ndarray) -> np.ndarray:
    """The partner's tile centres of one slice, (TR', TC', 3) mm, in the recipient's native frame.

    Through `frame.to_native`, which projects on the recipient's plane and drops the off-plane
    part; a centre that is NaN stays NaN and is never handed to the frame, which refuses a
    non-finite point. Returns float64 (TR', TC', 2), newly owned and frozen with `handed_on`;
    the saved centres are never written.
    """
    centres = np.asarray(centres_lps, dtype=np.float64)
    flat = centres.reshape(-1, 3)
    placed = np.full((flat.shape[0], 2), np.nan, dtype=np.float64)
    finite = np.isfinite(flat).all(axis=1)
    if finite.any():
        placed[finite] = frame.to_native(flat[finite])
    return handed_on(placed.reshape(*centres.shape[:2], 2))


def lineup_panels(
    code: str | None,
    why: str | None,
    recipient_uid: str | None,
    partner_uid: str | None,
    half_tile_mm: float | None,
    half_thickness_mm: float | None,
    normal_angle_deg: float | None,
    partner_slice: np.ndarray | None,
    slab_codes: np.ndarray | None,
    partner_tile: np.ndarray | None,
    distance_mm: np.ndarray | None,
    match_codes: np.ndarray | None,
    bounds_rc: np.ndarray | None,
    partner_centres_lps: np.ndarray | None,
    frame: PlaneFrame | None,
    index: object,
) -> LineUpPanels:
    """Hand on one recipient's saved line-up at one slice, reading nothing of the study.

    Every argument is a value a stage computed and the writer saved: the line-up's code, bars and
    angle, its five arrays over every recipient slice, the recipient's saved `bounds_rc`
    (TR, TC, 4), the partner's saved `centres_lps` (Z', TR', TC', 3) in millimetres (None when
    this run holds no saved stack for the partner), the recipient's saved plane frame (None when
    the writer saved none), and `index`, the recipient slice to draw. `slice_standing` names what
    the slice can show. The saved values at `index` (its partner tiles, distances and match
    codes) are selected whenever `index` lies inside the line-up, whatever the standing, as
    `LinedUpSlice` says; the recipient's tile centres are read off the bounds whenever bounds
    were handed on; and only where the slice is `lined_up` are the partner's centres at the
    named partner slice placed in the recipient's native frame through `frame.to_native`, a
    finite centre at a time. The arrays are handed on in their saved dtypes; nothing is
    measured, resampled or derived, and an absent value stays absent.
    """
    named = None if partner_slice is None else np.asarray(partner_slice, dtype=np.int64)
    slabs = None if slab_codes is None else np.asarray(slab_codes, dtype=np.uint8)
    slices = 0 if named is None else int(named.shape[0])
    inside = (
        isinstance(index, int) and not isinstance(index, bool) and 0 <= index < slices
    )
    at_partner = int(named[index]) if inside and named is not None else -1
    partner_slices = (
        None
        if partner_centres_lps is None
        else int(np.asarray(partner_centres_lps).shape[0])
    )
    standing = slice_standing(code, index, slices, at_partner, partner_slices)
    slab_name = None
    if inside and slabs is not None and int(slabs[index]) < len(SLAB_CODES):
        slab_name = SLAB_CODES[int(slabs[index])]
    placed = None
    if standing == "lined_up" and partner_centres_lps is not None and frame is not None:
        placed = placed_centres_rc(
            frame, np.asarray(partner_centres_lps, dtype=np.float64)[at_partner]
        )
    return LineUpPanels(
        code=code,
        why=why,
        recipient_uid=recipient_uid,
        partner_uid=partner_uid,
        half_tile_mm=None if half_tile_mm is None else float(half_tile_mm),
        half_thickness_mm=None
        if half_thickness_mm is None
        else float(half_thickness_mm),
        normal_angle_deg=None if normal_angle_deg is None else float(normal_angle_deg),
        slices=slices,
        partner_slice=named,
        slab_codes=slabs,
        at=LinedUpSlice(
            index=index,
            standing=standing,
            partner_index=at_partner if standing == "lined_up" else None,
            slab_code=slab_name,
            recipient_centres_rc=None
            if bounds_rc is None
            else tile_centres_rc(bounds_rc),
            partner_centres_rc=placed,
            partner_tile=None
            if not inside or partner_tile is None
            else np.asarray(partner_tile, dtype=np.int64)[index],
            distance_mm=None
            if not inside or distance_mm is None
            else np.asarray(distance_mm, dtype=np.float64)[index],
            match_codes=None
            if not inside or match_codes is None
            else np.asarray(match_codes, dtype=np.uint8)[index],
        ),
    )
