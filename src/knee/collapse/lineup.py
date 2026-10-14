"""The line-up: for each tile of one acquisition, the tile of its partner at the same place on the knee.

**Why it exists, against the thesis.** Two lenses "read one plane two ways, and each corrects the
other's borders" (§4.2), and their conjunction, not either alone, carries the meaning (§1.3:
I(X; Y1, Y2) = I(X; Y1) + I(X; Y2 | Y1)). The founder, 2026-10-13, on how two coronal pictures with
different pixel counts lie over each other: one physical knee, lying still, in one scanner, in one
plane; the pixel count is a setting of the camera; "the squint is how you make it cheap, you just
kinda...line it up. That's all ... It's the same fucking image, just sorta scootch it a bit, and
you're good." So the match is by the tile centres' positions in the scanner's millimetres, never by
tile index; a shift of a millimetre or two vanishes inside a tile.

**What it reads.** Two `SquintStack`s of one plane (the pairing from `knee.study.pairs`), their
`centres_lps`, and each series' `SeriesGeometry` (`along_normal`, `normal`, the slice thickness).
It is geometry only: no population, no digit, so it runs before the first lens and the first lens
reads one squint per series (the Codex correction of 2026-10-13: the earlier order was a cycle).

This is the funnel's operation 3a (`openspec/changes/the-funnel/design.md` R3a, task 3a.1). The
pure decisions are `match_code` and `slab_code`; `line_up` is orchestration over one measurement,
the nearest-centre search, which carries the contract; `read_lineups` is the orchestration the
route calls once per study, over every `paired` plane of the pairs record, and it reads that
record itself.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from knee.collapse.squint_stack import SquintStack
from knee.compute.contracts import ComputeContract, contracted, handed_on
from knee.study.pairs import AcquisitionPairs
from knee.study.series import SeriesGeometry
from knee.telemetry import ledger

#: Per tile: whether the partner tile found is the same patch of knee.
MATCH_CODES: tuple[str, ...] = (
    "matched",
    "beyond_half_tile",
    "partner_unavailable",
    "invalid_measurement",
)

#: Per slice: whether the nearest partner slice lies within the recipient's own slab.
SLAB_CODES: tuple[str, ...] = (
    "in_slab",
    "nearest_only",
    "no_partner",
    "invalid_measurement",
)


def match_code(distance_mm: float, half_tile_mm: float, partner_exists: bool) -> str:
    """Whether the nearest partner tile covers the same patch of knee (pure -- pinned).

    `distance_mm` is the distance between the two tile centres in the scanner's millimetres;
    `half_tile_mm` is the bar, an argument: a centre nearer than half a tile lies inside this
    tile's own patch, so the two tiles read the same millimetres of knee and are "matched". Farther
    is "beyond_half_tile": the nearest partner tile is kept and named, but it is not the same patch.
    No partner at all is "partner_unavailable", a silence. A distance or bar that is not a finite
    non-negative number is "invalid_measurement".

    post: __return__ in MATCH_CODES
    """
    if not partner_exists:
        return "partner_unavailable"
    if (
        not math.isfinite(distance_mm)
        or distance_mm < 0.0
        or not math.isfinite(half_tile_mm)
        or half_tile_mm <= 0.0
    ):
        return "invalid_measurement"
    if distance_mm <= half_tile_mm:
        return "matched"
    return "beyond_half_tile"


def slab_code(offset_mm: float, half_thickness_mm: float, partner_exists: bool) -> str:
    """Whether the nearest partner slice lies within this slice's slab (pure -- pinned).

    `offset_mm` is the distance along this slice's normal between the two slices' positions;
    `half_thickness_mm` is half this slice's stored thickness, the bar. Within it the partner slice
    cuts the same slab of knee: "in_slab". Beyond it the nearest partner slice is still named, as
    "nearest_only", and the match codes of its tiles say what they say. No partner is
    "no_partner". A non-finite or negative offset, or a half thickness that is not finite and
    positive, is "invalid_measurement": a thickness the header did not give is not a slab of zero.

    post: __return__ in SLAB_CODES
    """
    if not partner_exists:
        return "no_partner"
    if (
        not math.isfinite(offset_mm)
        or offset_mm < 0.0
        or not math.isfinite(half_thickness_mm)
        or half_thickness_mm <= 0.0
    ):
        return "invalid_measurement"
    if offset_mm <= half_thickness_mm:
        return "in_slab"
    return "nearest_only"


CONTRACT = ComputeContract(
    kind="measurement",
    language="NumPy, with SciPy's cKDTree where it is library-shaped; no twin",
    reads="recipient centres (TR, TC, 3) and partner centres (TR', TC', 3) of one slice pair, mm",
    writes="partner_tile int64 (TR, TC, 2) and distance_mm float64 (TR, TC)",
    allocation="one (TR, TC, 2) int64 and one (TR, TC) float64 per recipient slice",
    work="TR * TC nearest-neighbour queries over TR' * TC' partner centres per slice pair",
    parallel_unit="slice",
    reference="nearest_tiles",
    proof_gate="tests/knee/collapse/test_lineup.py: a partner grid shifted by half a pixel maps "
    "every tile to itself with distance under half a tile; a partner grid at a different pixel "
    "size maps each tile to the partner tile whose native bounds overlap its millimetre footprint",
)


@contracted
def nearest_tiles(
    recipient_centres: np.ndarray, partner_centres: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """For each recipient tile centre, the partner tile whose centre is nearest in mm (measurement).

    Returns `partner_tile` int64 (TR, TC, 2), the partner's tile rc, and `distance_mm` float64
    (TR, TC). A recipient tile whose centre is NaN (an empty tile) gets (-1, -1) and NaN; partner
    tiles with NaN centres are never chosen. Ties take the first partner tile in scan order.

    pre: recipient_centres.ndim == 3 and recipient_centres.shape[2] == 3
    pre: partner_centres.ndim == 3 and partner_centres.shape[2] == 3
    post: __return__[0].shape == recipient_centres.shape[:2] + (2,)
    post: __return__[1].shape == recipient_centres.shape[:2]
    """
    recipient = np.asarray(recipient_centres, dtype=np.float64)
    partner = np.asarray(partner_centres, dtype=np.float64)
    if recipient.ndim != 3 or recipient.shape[2] != 3:
        raise ValueError("invalid_recipient_centres")
    if partner.ndim != 3 or partner.shape[2] != 3:
        raise ValueError("invalid_partner_centres")
    tiles_down, tiles_across = int(recipient.shape[0]), int(recipient.shape[1])
    partner_across = int(partner.shape[1])
    asked = recipient.reshape(-1, 3)
    offered = partner.reshape(-1, 3)
    partner_tile = np.full((asked.shape[0], 2), -1, dtype=np.int64)
    distance = np.full(asked.shape[0], np.nan, dtype=np.float64)
    # A tile with no centre asks nothing and is never offered: an empty recipient tile keeps
    # (-1, -1) and NaN, and an empty partner tile is left out of the candidates.
    asking = np.flatnonzero(np.isfinite(asked).all(axis=1))
    candidates = np.flatnonzero(np.isfinite(offered).all(axis=1))
    if asking.size and candidates.size:
        points = offered[candidates]
        # The search is the plain broadcast, not the KD-tree, because the tie rule is part of
        # the contract: `argmin` returns the FIRST minimum, and `candidates` ascends in scan
        # order, so an exact tie goes to the first partner tile in scan order. The scratch is
        # bounded by taking the recipient's tiles in runs of at most `_SCRATCH_PAIRS` pairs.
        run = max(1, _SCRATCH_PAIRS // int(candidates.size))
        for start in range(0, int(asking.size), run):
            rows = asking[start : start + run]
            gaps = asked[rows, None, :] - points[None, :, :]
            squared = np.einsum("ijk,ijk->ij", gaps, gaps)
            nearest = np.argmin(squared, axis=1)
            flat = candidates[nearest]
            partner_tile[rows, 0] = flat // partner_across
            partner_tile[rows, 1] = flat % partner_across
            distance[rows] = np.sqrt(squared[np.arange(rows.size), nearest])
    return (
        handed_on(partner_tile.reshape(tiles_down, tiles_across, 2)),
        handed_on(distance.reshape(tiles_down, tiles_across)),
    )


#: How many (recipient tile, partner tile) pairs one run of the broadcast holds at most: a bound
#: on scratch (three float64 per pair for the gaps, one for the squares), never a bar on the data.
_SCRATCH_PAIRS: int = 1 << 18


@dataclass(frozen=True, slots=True)
class LineUp:
    """One pair's line-up, from the recipient's tiles to the partner's.

    `partner_slice`: int64 (Z,), the partner slice nearest along the recipient's normal, -1 when
    none. `slab_codes`: uint8 (Z,) indexing `SLAB_CODES`. `normal_angle_deg`: the angle between
    the two series' normals, a measurement kept and never judged here. `partner_tile`: int64
    (Z, TR, TC, 2); `distance_mm`: float64 (Z, TR, TC); `match_codes`: uint8 (Z, TR, TC) indexing
    `MATCH_CODES`. `half_tile_mm` and `half_thickness_mm` are the bars used. `code` is `present`
    when both stacks were present, else the recipient's or partner's own code, with `why`.
    """

    recipient_uid: str
    partner_uid: str
    code: str
    why: str
    half_tile_mm: float
    half_thickness_mm: float
    normal_angle_deg: float
    partner_slice: np.ndarray
    slab_codes: np.ndarray
    partner_tile: np.ndarray
    distance_mm: np.ndarray
    match_codes: np.ndarray


def line_up(
    recipient: SquintStack,
    partner: SquintStack,
    recipient_geometry: SeriesGeometry | None,
    partner_geometry: SeriesGeometry | None,
    half_tile_mm: float,
    half_thickness_mm: float,
) -> LineUp:
    """Line the partner's squint up with the recipient's by place on the knee (orchestration).

    When either stack's code is not `present`, or either geometry is None, every slice is
    `no_partner` and every tile `partner_unavailable`, with `why` naming which. Else, per recipient
    slice z: its position projected on the recipient normal (`recipient_geometry.along_normal[z]`)
    against every partner slice's position projected on the SAME normal gives the nearest partner
    slice and the offset; `slab_code(offset, half_thickness_mm, True)`; `nearest_tiles(
    recipient.centres_lps[z], partner.centres_lps[partner_slice])` gives the tiles and distances;
    `match_code(distance, half_tile_mm, True)` per tile. `normal_angle_deg` is the angle between
    the two normals. Arrays are frozen with `handed_on`. Records `squint_stack.consumed_by.lineup`
    and `lineup.produced` (matched tiles, in-slab slices) on the ledger. Decides nothing itself.
    """
    # The consumer records what it read at the point of reading (`specs/route-composition`):
    # both stacks are always handed over, and the counts say which of them held a reading.
    ledger.record(
        "squint_stack.consumed_by.lineup",
        recipient=1 if recipient.code == "present" else 0,
        partner=1 if partner.code == "present" else 0,
    )
    reading = _line_up(
        recipient,
        partner,
        recipient_geometry,
        partner_geometry,
        float(half_tile_mm),
        float(half_thickness_mm),
    )
    ledger.record(
        "lineup.produced",
        matched=int(np.count_nonzero(reading.match_codes == _MATCHED)),
        in_slab=int(np.count_nonzero(reading.slab_codes == _IN_SLAB)),
    )
    return reading


#: The stored index of each code, so a tile's or a slice's code is one byte in the record.
_MATCHED: int = MATCH_CODES.index("matched")
_PARTNER_UNAVAILABLE: int = MATCH_CODES.index("partner_unavailable")
_IN_SLAB: int = SLAB_CODES.index("in_slab")
_NO_PARTNER: int = SLAB_CODES.index("no_partner")


def normal_angle_deg(
    recipient_geometry: SeriesGeometry | None, partner_geometry: SeriesGeometry | None
) -> float:
    """The angle between the two series' slice normals, in degrees (measurement).

    NaN when either geometry is None or either normal has no length. The angle is the plain
    one between the two unit vectors, so antiparallel normals (one stack ordered against the
    other) read 180 and not 0: it is kept as measured and never judged here.
    """
    if recipient_geometry is None or partner_geometry is None:
        return float("nan")
    first = np.asarray(recipient_geometry.normal, dtype=np.float64)
    second = np.asarray(partner_geometry.normal, dtype=np.float64)
    lengths = float(np.linalg.norm(first)) * float(np.linalg.norm(second))
    if first.shape != (3,) or second.shape != (3,) or not lengths > 0.0:
        return float("nan")
    cosine = float(first @ second) / lengths
    return float(np.degrees(np.arccos(min(1.0, max(-1.0, cosine)))))


def shared_half_thickness_mm(thicknesses: tuple[float | None, ...]) -> float:
    """Half the one slice thickness a series' slices share, in millimetres (measurement).

    The study stage reads each slice's SliceThickness as stored (`Series.slice_thickness_mm`,
    None where the header gave none); the slab bar is one number for the whole line-up. It is
    half the thickness when every slice that gives one gives the same value. NaN when no slice
    gives a finite positive thickness, and NaN when the given thicknesses disagree: either way
    the slab decision names it `invalid_measurement`, which is a refusal and never a slab of
    zero. Decides nothing itself.
    """
    given = [
        float(value)
        for value in thicknesses
        if value is not None
        and not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
        and float(value) > 0.0
    ]
    if not given or any(value != given[0] for value in given):
        return float("nan")
    return given[0] / 2.0


def _silence(
    recipient: SquintStack,
    partner: SquintStack,
    code: str,
    why: str,
    half_tile_mm: float,
    half_thickness_mm: float,
    angle: float,
) -> LineUp:
    """The line-up of a pair that could not be lined up: every slice `no_partner`, every tile
    `partner_unavailable`, over the recipient's own grid (empty when its stack is absent)."""
    slices, tiles_down, tiles_across = (int(size) for size in recipient.median.shape)
    return LineUp(
        recipient_uid=recipient.series_uid,
        partner_uid=partner.series_uid,
        code=code,
        why=why,
        half_tile_mm=half_tile_mm,
        half_thickness_mm=half_thickness_mm,
        normal_angle_deg=angle,
        partner_slice=handed_on(np.full((slices,), -1, dtype=np.int64)),
        slab_codes=handed_on(np.full((slices,), _NO_PARTNER, dtype=np.uint8)),
        partner_tile=handed_on(
            np.full((slices, tiles_down, tiles_across, 2), -1, dtype=np.int64)
        ),
        distance_mm=handed_on(
            np.full((slices, tiles_down, tiles_across), np.nan, dtype=np.float64)
        ),
        match_codes=handed_on(
            np.full(
                (slices, tiles_down, tiles_across), _PARTNER_UNAVAILABLE, dtype=np.uint8
            )
        ),
    )


def _line_up(
    recipient: SquintStack,
    partner: SquintStack,
    recipient_geometry: SeriesGeometry | None,
    partner_geometry: SeriesGeometry | None,
    half_tile_mm: float,
    half_thickness_mm: float,
) -> LineUp:
    """The line-up itself: the silences first, then one partner slice and one search per slice."""
    angle = normal_angle_deg(recipient_geometry, partner_geometry)
    if recipient.code != "present":
        return _silence(
            recipient,
            partner,
            recipient.code,
            f"the recipient's stack is {recipient.code}: {recipient.why}",
            half_tile_mm,
            half_thickness_mm,
            angle,
        )
    if partner.code != "present":
        return _silence(
            recipient,
            partner,
            partner.code,
            f"the partner's stack is {partner.code}: {partner.why}",
            half_tile_mm,
            half_thickness_mm,
            angle,
        )
    # Both stacks were present, so the code is `present` whatever follows; a geometry that is
    # None is named in `why`, and every slice and tile is the silence it is.
    if recipient_geometry is None:
        return _silence(
            recipient,
            partner,
            "present",
            "the recipient has no geometry, so no slice can be projected on its normal",
            half_tile_mm,
            half_thickness_mm,
            angle,
        )
    if partner_geometry is None:
        return _silence(
            recipient,
            partner,
            "present",
            "the partner has no geometry, so its slices cannot be placed along the normal",
            half_tile_mm,
            half_thickness_mm,
            angle,
        )
    slices, tiles_down, tiles_across = (int(size) for size in recipient.median.shape)
    recipient_along = np.asarray(recipient_geometry.along_normal, dtype=np.float64)
    normal = np.asarray(recipient_geometry.normal, dtype=np.float64)
    partner_positions = np.asarray(partner_geometry.position, dtype=np.float64)
    # A stack and its geometry are two records of one series; a slice count that disagrees is
    # a contradiction between them, refused by name rather than lined up.
    if recipient_along.shape != (slices,):
        raise ValueError("recipient_geometry_does_not_match_stack")
    if partner_positions.ndim != 2 or partner_positions.shape != (
        int(partner.median.shape[0]),
        3,
    ):
        raise ValueError("partner_geometry_does_not_match_stack")
    if partner_positions.shape[0] == 0:
        return _silence(
            recipient,
            partner,
            "present",
            "the partner's stack holds no slice",
            half_tile_mm,
            half_thickness_mm,
            angle,
        )
    # Every partner slice's position projected on the recipient's OWN normal, once.
    partner_along = partner_positions @ normal
    partner_slice = np.full((slices,), -1, dtype=np.int64)
    slab_codes = np.full((slices,), _NO_PARTNER, dtype=np.uint8)
    partner_tile = np.full((slices, tiles_down, tiles_across, 2), -1, dtype=np.int64)
    distance_mm = np.full((slices, tiles_down, tiles_across), np.nan, dtype=np.float64)
    match_codes = np.full(
        (slices, tiles_down, tiles_across), _PARTNER_UNAVAILABLE, dtype=np.uint8
    )
    for z in range(slices):
        offsets = np.abs(partner_along - recipient_along[z])
        # `argmin` takes the FIRST of an exact tie, so a tie goes to the lower partner slice.
        nearest = int(np.argmin(offsets))
        partner_slice[z] = nearest
        slab_codes[z] = SLAB_CODES.index(
            slab_code(float(offsets[nearest]), half_thickness_mm, True)
        )
        tiles, distances = nearest_tiles(
            recipient.centres_lps[z], partner.centres_lps[nearest]
        )
        partner_tile[z] = tiles
        distance_mm[z] = distances
        # The scalar decision at every tile, so the rule has one statement.
        match_codes[z] = np.fromiter(
            (
                MATCH_CODES.index(match_code(float(d), half_tile_mm, True))
                for d in distances.ravel()
            ),
            dtype=np.uint8,
            count=tiles_down * tiles_across,
        ).reshape(tiles_down, tiles_across)
    return LineUp(
        recipient_uid=recipient.series_uid,
        partner_uid=partner.series_uid,
        code="present",
        why=(
            f"{slices} recipient slices lined up with {int(partner.median.shape[0])} partner "
            f"slices along the recipient's normal; {tiles_down} x {tiles_across} tiles per "
            f"slice matched by centre within {half_tile_mm:g} mm"
        ),
        half_tile_mm=half_tile_mm,
        half_thickness_mm=half_thickness_mm,
        normal_angle_deg=angle,
        partner_slice=handed_on(partner_slice),
        slab_codes=handed_on(slab_codes),
        partner_tile=handed_on(partner_tile),
        distance_mm=handed_on(distance_mm),
        match_codes=handed_on(match_codes),
    )


def read_lineups(
    pairs: AcquisitionPairs,
    stack_of: dict[str, SquintStack],
    geometry_of: dict[str, SeriesGeometry | None],
    thickness_of: dict[str, tuple[float | None, ...]],
    half_tile_mm: float,
) -> dict[str, LineUp]:
    """Line up every `paired` plane of one study, keyed by the recipient's uid (orchestration).

    The route calls this once per study, after every series has its squint stack and before any
    lens is read. It records `pairs.consumed_by.lineup` (planes, paired) at the point it reads
    the pairs record; then, for each plane whose code is `paired`, it calls `line_up` with
    `dark_uids[0]` as the recipient and `bright_uids[0]` as the partner (`knee.study.pairs`: one
    of each, so the first of each list is the one), `half_tile_mm` as the match bar and
    `shared_half_thickness_mm(thickness_of[recipient])` as the slab bar. A plane that is
    solitary, surplus or none is lined up with nothing and no stack is read for it: that silence
    is the pairs record's own, and the series on such a plane carry no line-up. A `paired` plane
    that names a series with no stack in `stack_of`, or that lacks either flavour, is a
    contradiction between the two records, refused by name rather than lined up. A series with
    no entry in `geometry_of` has no geometry, and one with no entry in `thickness_of` gave no
    thickness: each is the silence or the refusal `line_up` already names. Decides nothing itself.
    """
    # The consumer records what it read at the point of reading (`specs/route-composition`): the
    # pairs record is always handed over, and the counts say what it carried.
    ledger.record(
        "pairs.consumed_by.lineup",
        planes=len(pairs.pairs),
        paired=sum(1 for pair in pairs.pairs if pair.code == "paired"),
    )
    lineups: dict[str, LineUp] = {}
    for pair in pairs.pairs:
        if pair.code != "paired":
            continue
        if not pair.dark_uids or not pair.bright_uids:
            raise ValueError("paired_plane_without_both_flavours")
        recipient, partner = pair.dark_uids[0], pair.bright_uids[0]
        if recipient not in stack_of or partner not in stack_of:
            raise ValueError("paired_series_without_a_stack")
        lineups[recipient] = line_up(
            stack_of[recipient],
            stack_of[partner],
            geometry_of.get(recipient),
            geometry_of.get(partner),
            half_tile_mm,
            shared_half_thickness_mm(thickness_of.get(recipient, ())),
        )
    return lineups
