"""The joint space's cheap readings and the relations a pointed plane is read by: measurements only,
no names (`docs/DIMENSIONAL_COLLAPSE_PLAN.md` Step 5, the sided menisci, the articular cartilage,
the cruciates and the collaterals).

**Why it exists.** The femur and the tibia are carried through the stacks (the bones' family). The
joint, in its existing definition, is what lies between them along the leg. This module asks that
of every slice cheaply, from the bones' carried places, before any lens is read: where on a slice
the joint can lie (`joint_reach`: the places between the two bones' carried places on each line along
the leg and what is within `SHELL_MM` of them, the reach the existing rules allow a part to its
bones), and then, in that corridor only, FOUR SEPARATE quantities, each the area of the 2 mm blocks
(the existing `LIGAMENT_SMOOTH_MM`) whose median lies at a level an existing rule reads:

- `dark`: at or under the series' background split, the low signal the menisci's rule reads;
- `ligament`: under `LIGAMENT_DARKER` of the femur's marrow, the PCL's uniformly dark band;
- `bright`: over `CARTILAGE_BRIGHTER` of the bones' marrow, the cartilage's layer;
- `fluid`: over `FLUID_BRIGHTER` of the bones' marrow, the white the ACL is walled off by.

They are never combined: each points at its own useful planes (`knee.collapse.profile` runs and
maxima, every tie kept). The corridor is an UPPER BOUND on where the joint can lie (the carried places
are the union over the planes the bones were named on), never a section, and a block's level is
support, never a name. Nothing unseen is absence: a block with any place never seen has no median, so
a measured absence needs every block of the corridor seen.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from knee.objects.assignments import (
    CARTILAGE_BRIGHTER,
    FLUID_BRIGHTER,
    FOUR_NEIGHBOURS,
    LIGAMENT_DARKER,
    MENISCUS_THICKNESS_MM,
    SHELL_MM,
    between_along_the_leg,
    distance_from,
    end_pieces,
    meniscus_side,
    thick_parts,
)

DARK = "dark"
LIGAMENT = "ligament"
BRIGHT = "bright"
FLUID = "fluid"
QUANTITIES = (DARK, LIGAMENT, BRIGHT, FLUID)
# What each quantity points at, in the family's words (the pointed planes name no object by it).
POINTS_AT = {
    DARK: "meniscus body (coronal), meniscal horns (sagittal), the MCL",
    LIGAMENT: "the PCL (sagittal, without fat suppression)",
    BRIGHT: "the articular cartilage (fat suppression)",
    FLUID: "the ACL (sagittal, fat suppression)",
}


def joint_reach(
    femur_foot: np.ndarray,
    tibia_foot: np.ndarray,
    basis_lps: np.ndarray,
    spacing_rc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Where the joint can lie on a slice, from the two bones' carried places projected onto it
    (`femur_foot`, `tibia_foot`, native pixels): the `corridor` (the places between the femur's and
    the tibia's on each line along the leg, `between_along_the_leg`, the joint's own definition) and
    its `reach` (the corridor and every place within `SHELL_MM` of it, the distance the existing
    rules allow a part to reach its bones by). Both empty where either bone has no place on the
    slice, or none lies between them."""
    femur = np.asarray(femur_foot, dtype=bool)
    tibia = np.asarray(tibia_foot, dtype=bool)
    none = np.zeros(femur.shape, dtype=bool)
    if not (femur.any() and tibia.any()):
        return none, none
    corridor = between_along_the_leg(femur, tibia, basis_lps) & ~femur & ~tibia
    if not corridor.any():
        return none, none
    return corridor, distance_from(corridor, spacing_rc) <= SHELL_MM


def levels(
    split: float, femur_light: float, bones_light: float
) -> dict[str, tuple[float, float] | None]:
    """The level each quantity reads, (low, high) in the acquired light, or None where its anchor is
    not usable: the background split must be finite, a marrow light finite and positive. A quantity
    with no usable anchor is unreadable and never excluded (a NaN anchor makes every comparison false,
    which would read as a measured absence)."""

    def usable(value: float) -> bool:
        return bool(np.isfinite(value) and value > 0)

    return {
        DARK: (-np.inf, float(split)) if np.isfinite(split) else None,
        LIGAMENT: (-np.inf, LIGAMENT_DARKER * float(femur_light))
        if usable(femur_light)
        else None,
        BRIGHT: (CARTILAGE_BRIGHTER * float(bones_light), np.inf)
        if usable(bones_light)
        else None,
        FLUID: (FLUID_BRIGHTER * float(bones_light), np.inf)
        if usable(bones_light)
        else None,
    }


def block_support(
    median: np.ndarray,
    held: np.ndarray,
    block_mm: tuple[float, float],
    wanted: dict[str, tuple[float, float]],
) -> tuple[dict[str, float], int, int]:
    """The area in square millimetres of the blocks of `held` (BR, BC; the blocks that hold a place of
    the corridor's reach) whose median reads each wanted quantity, by the comparison its rule makes
    (`dark`: at or under; `ligament`: under; `bright`, `fluid`: over), the blocks of `held` seen, and
    how many were not (NaN median: a place of the block was never seen, so it is no reading, not
    darkness and not light). The area counts the seen blocks only: with unseen blocks it is a lower
    bound, and a caller never reads zero as absence while any block is unseen."""
    values = np.asarray(median, dtype=np.float64)
    places = np.asarray(held, dtype=bool)
    seen = np.isfinite(values)
    area: dict[str, float] = {}
    with np.errstate(invalid="ignore"):
        for name, (low, high) in wanted.items():
            if name == DARK:
                hit = values <= high
            elif name == LIGAMENT:
                hit = values < high
            else:
                hit = values > low
            area[name] = float(
                np.count_nonzero(places & seen & hit) * block_mm[0] * block_mm[1]
            )
    return (
        area,
        int(np.count_nonzero(places & seen)),
        int(np.count_nonzero(places & ~seen)),
    )


def compartment(knee: str, toward_left_mm: float) -> str:
    """The compartment of a sagittal plane: "medial" or "lateral" by the header's own word for which
    knee it is (`meniscus_side`, the existing siding) and the plane's place toward the patient's left
    of the notch's plane; "meniscus" (no side) where the header names no knee or the plane IS the
    notch's, never a guess."""
    if not np.isfinite(toward_left_mm) or toward_left_mm == 0:
        return "meniscus"
    return meniscus_side(knee, bool(toward_left_mm > 0))


def horn_pieces(
    dark: np.ndarray,
    joint: np.ndarray,
    outside_picture: np.ndarray,
    spacing_rc: np.ndarray,
    back_mm: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """On a sagittal plane the meniscal horn candidates, by the menisci's existing description with
    the plane's own in-plane axis: the low signal with every piece thinner than
    `MENISCUS_THICKNESS_MM` rubbed away, the pieces touching the joint, the piece nearest each end
    of the joint (`end_pieces`), here along the leg's front to back (`back_mm`, each place's position
    toward the back). Returns (candidates, ends): `candidates` the pieces kept, `ends` int8 with 1 the
    piece at the front, 2 at the back, 0 elsewhere. Both empty with no joint or no such piece. A
    candidate is a reading, not a name: the existing rule is gated to the planes side to side runs in."""
    none = np.zeros(dark.shape, dtype=bool)
    ends = np.zeros(dark.shape, dtype=np.int8)
    if not np.asarray(joint, dtype=bool).any():
        return none, ends
    thick = thick_parts(
        np.asarray(dark, dtype=bool) & ~np.asarray(outside_picture, dtype=bool),
        spacing_rc,
        MENISCUS_THICKNESS_MM,
    )
    pieces, _ = ndi.label(thick)
    near = ndi.binary_dilation(joint, structure=FOUR_NEIGHBOURS)
    touching = np.unique(pieces[near & (pieces > 0)])
    pieces = np.where(np.isin(pieces, touching), pieces, 0)
    pieces, count = ndi.label(pieces > 0)
    middle = float(np.asarray(back_mm)[joint].mean())
    for piece, toward_back in end_pieces(pieces, count, back_mm, middle):
        ends[pieces == piece] = 2 if toward_back else 1
    return ends > 0, ends
