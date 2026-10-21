"""An anatomy-authored first reference for the whole knee, independent of study outputs.

The numerical reference is the SPL MRI teaching atlas (Richolt, Jakab, Kikinis,
2015), plus explicitly named relational constructions from OBJECTS_AND_CONDITIONS.
It is one specimen and a first guide, not a population norm. Nothing is fitted to
the competition cohort. Native study positions are made elsewhere from three key
planes; these sites are expectations, never observations or segmentation masks.

Reference coordinates are (medial, posterior, superior), mm. The atlas is a left
knee by its fibula's lateral position; hence medial = minus atlas LPS-left.
Selected atlas planes and all tied alternatives are retained in _atlas_reference.
Largest sections are author-selected reference views for the structures listed
there, not a universal definition or a study key-plane selector. Muscle and vessel
cross-sections are selected at the condyles, and semitendinosus at proximal tibia,
so extra thigh/calf coverage does not define their knee-level reference.

Unlabelled structures get transparent geometric constructions between named
anatomical neighbours. Their midpoints are authored first expectations, not
published caliper measurements. Four diffuse field classes have no single site;
they remain named gaps rather than fabricated locations. All pairs still exist
as queries, including the bones. See docs/ANATOMICAL_MAP_REFERENCE.md.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from types import MappingProxyType

from knee.collapse._atlas_reference import (
    ANTERIOR_CONTACTS_LPS_MM,
    ATLAS_SITES,
    ATLAS_SOURCE,
)
from knee.collapse.relative import IdealVector
from knee.objects.assignments import OBJECT_CODES

Triple = tuple[float, float, float]
MAP_OBJECTS = tuple(sorted((set(OBJECT_CODES) - {"unassigned"}) | {"recess"}))
REFERENCE_BREADTH_MM = ATLAS_SITES["femur"]["span_mm"][0]
DOMAIN_SOURCE = "docs/OBJECTS_AND_CONDITIONS.md §4; sourced anatomical relations"


@dataclass(frozen=True)
class ReferenceSite:
    """One expected location and its construction; no actual study position."""

    object: str
    status: str
    point_mps_mm: Triple | None
    span_mm: Triple | None
    source: str
    reason: str
    construction: str
    key_planes: tuple[Mapping[str, object], ...] = ()


def _mid(a: Triple, b: Triple) -> Triple:
    return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2


def _construction(name: str, point: Triple, span: Triple, reason: str) -> ReferenceSite:
    """Expected planes derived from a stated relation, never claimed acquired."""
    planes = tuple(
        {
            "orientation": orientation,
            "coordinate_mps_mm": point[axis],
            "kind": "anatomical_construction",
            "reason": reason,
        }
        for axis, orientation in enumerate(("sagittal", "coronal", "axial"))
    )
    return ReferenceSite(
        name,
        "anatomical_reference",
        point,
        span,
        f"{DOMAIN_SOURCE}; {ATLAS_SOURCE}",
        reason,
        "between_anatomical_neighbours",
        planes,
    )


@cache
def reference_sites() -> Mapping[str, ReferenceSite]:
    """One immutable catalogue; reference numeric values never read study data."""
    sites = {
        name: ReferenceSite(
            name,
            "reference_not_defined",
            None,
            None,
            DOMAIN_SOURCE,
            "Diffuse field class; no unique anatomical key-plane reference is authored.",
            "explicit_gap",
        )
        for name in MAP_OBJECTS
    }
    for name, row in ATLAS_SITES.items():
        sites[name] = ReferenceSite(
            name,
            "anatomical_reference",
            tuple(row["point_mps_mm"]),
            tuple(row["span_mm"]),
            ATLAS_SOURCE,
            row["reason"],
            "selected_atlas_planes",
            tuple(row["key_planes"]),
        )

    # These are relations stated in the objects document, with simple reference
    # plane constructions. They are deliberately exposed, not disguised as labels
    # or reference measurements the atlas does not supply.
    def point(name: str) -> Triple:
        value = sites[name].point_mps_mm
        assert value is not None
        return value

    def span(name: str) -> Triple:
        value = sites[name].span_mm
        assert value is not None
        return value

    def put(name: str, p: Triple, s: Triple, reason: str):
        sites[name] = _construction(name, p, s, reason)

    joint = _mid(point("medial_meniscus"), point("lateral_meniscus"))
    joint_span = span("meniscus")
    put(
        "joint",
        joint,
        joint_span,
        "Between the condyles and plateau: the midway key planes of the two menisci.",
    )
    for name in ("joint_fluid", "synovium", "joint_capsule"):
        put(
            name,
            joint,
            joint_span,
            "Joint cavity, its lining and its sleeve surround the menisci between femur and tibia; "
            "the joint reference is the initial guide, not a membrane boundary.",
        )

    patella = point("patella")
    # Interstitial means BETWEEN the facing surfaces, not between bone reference
    # points inside marrow. The physical source cuts, including neighbours, are kept.
    femur_front = ANTERIOR_CONTACTS_LPS_MM["femur_at_patella"][1]
    patella_back = ANTERIOR_CONTACTS_LPS_MM["patella_back_at_patella"][1]
    front = (patella[0], (patella_back + femur_front) / 2, patella[2])
    front_span = (
        span("patella")[0],
        abs(patella_back - femur_front),
        span("patella")[2],
    )
    cartilage_search_reason = (
        "The cartilage is the articular layer on subarticular bone plate "
        "(OBJECTS_AND_CONDITIONS.md §4); this facing-surface coordinate and "
        "broad span are search guides from the retained anterior contact labels, "
        "not cartilage thickness, a measured boundary, or an extracted cartilage label."
    )
    put(
        "patellar_cartilage",
        (patella[0], patella_back, patella[2]),
        front_span,
        "Patellar cartilage covers the posterior patellar articular surface; "
        "use the retained patella-back contact coordinate as a search guide. "
        + cartilage_search_reason,
    )
    put(
        "trochlear_cartilage",
        (patella[0], femur_front, patella[2]),
        front_span,
        "Trochlear cartilage covers the facing femoral articular surface; "
        "use the retained femur-front contact coordinate at patellar level as a search guide. "
        + cartilage_search_reason,
    )
    for name in ("anterior_synovial_recess", "recess"):
        put(
            name,
            front,
            front_span,
            "The anterior recess lies between the patella's posterior face and femur's anterior face; "
            "the source label boundaries at i282/k80 give those facing surfaces. "
            "The intervening plane is an authored guide, not an atlas recess label.",
        )

    # The tendon attaches at the patella's superior edge. At that level the fat
    # pads lie between it and femur, on either side of the intervening recess.
    superior_patella = ATLAS_SITES["patella"]["bounds_mps_mm"][1][2]
    tendon = (patella[0], patella[1], superior_patella)
    put(
        "quadriceps_tendon",
        tendon,
        span("patella"),
        "Quadriceps tendon reaches the superior patellar pole; that attachment plane is the first guide.",
    )
    lower = ANTERIOR_CONTACTS_LPS_MM["femur_above_patella_lower"]
    upper = ANTERIOR_CONTACTS_LPS_MM["femur_above_patella_upper"]
    fraction = (superior_patella - lower[2]) / (upper[2] - lower[2])
    upper_femur_front = lower[1] + fraction * (upper[1] - lower[1])
    upper_front = (patella[0], (tendon[1] + upper_femur_front) / 2, superior_patella)
    upper_span = (front_span[0], abs(tendon[1] - upper_femur_front), front_span[2])
    put(
        "suprapatellar_fat",
        upper_front,
        upper_span,
        "The two suprapatellar pads lie above patella between quadriceps tendon and femur.",
    )
    for name, end in (
        ("quadriceps_fat_pad", tendon),
        ("prefemoral_fat_pad", (patella[0], upper_femur_front, superior_patella)),
    ):
        put(
            name,
            _mid(upper_front, end),
            upper_span,
            "Quadriceps fat is anterior and prefemoral fat posterior to the suprapatellar recess; "
            "take the intervening planes on its respective side. This is an authored guide.",
        )

    # Direct arm at the posteromedial proximal tibia (LaPrade 2007, LP-MED).
    mm_bounds = ATLAS_SITES["medial_meniscus"]["bounds_mps_mm"]
    sm = (mm_bounds[1][0], mm_bounds[1][1], mm_bounds[0][2])
    put(
        "semimembranosus",
        sm,
        span("medial_meniscus"),
        "The direct semimembranosus arm attaches at the posteromedial tibial top, just distal to joint line "
        "(LP-MED). Use the medial/posterior meniscal extent and its inferior plane as a first guide; "
        "the atlas's semimembranosus muscle is never substituted for this tendon.",
    )
    put(
        "gastrocnemius_semimembranosus_bursa",
        _mid(sm, point("medial_gastrocnemius")),
        span("medial_gastrocnemius"),
        "The bursa is between medial gastrocnemius and semimembranosus tendon (R-BAKER, LP-MED); "
        "its expected planes bisect those references. A collapsed bursa need not be visible.",
    )

    patella_bounds = ATLAS_SITES["patella"]["bounds_mps_mm"]
    femur_bounds = ATLAS_SITES["femur"]["bounds_mps_mm"]
    for name, side in (
        ("medial_patellar_retinaculum", 1),
        ("lateral_patellar_retinaculum", 0),
    ):
        medial = (patella_bounds[side][0] + femur_bounds[side][0]) / 2
        put(
            name,
            (medial, front[1], patella[2]),
            front_span,
            "A retinacular band joins the corresponding side of patella to its femoral condyle; "
            "use intervening planes between those sides at patellar level.",
        )
    return MappingProxyType(sites)


def _scale(knee_scale_mm: float | None) -> float:
    if knee_scale_mm is None:
        return 1.0
    if not math.isfinite(knee_scale_mm) or knee_scale_mm <= 0:
        raise ValueError(
            "knee scale must be finite and positive, or explicitly unknown"
        )
    return knee_scale_mm / REFERENCE_BREADTH_MM


def ideal_vector(
    origin: str, target: str, knee_scale_mm: float | None = None
) -> IdealVector | None:
    """Any ordered pair, bones included. Unknown reference never becomes zero."""
    sites = reference_sites()
    a, b = sites[origin], sites[target]
    if a.point_mps_mm is None or b.point_mps_mm is None:
        return None
    scale = _scale(knee_scale_mm)
    pa, pb = a.point_mps_mm, b.point_mps_mm
    displacement = (
        scale * (pb[0] - pa[0]),
        scale * (pb[1] - pa[1]),
        scale * (pb[2] - pa[2]),
    )
    return IdealVector(
        origin,
        target,
        displacement,
        f"{a.source}; {b.source}; {a.construction} -> {b.construction}",
    )


def target_span_mm(object: str, knee_scale_mm: float | None = None) -> Triple | None:
    """Full reference extent as a search allowance, never an observed boundary."""
    span = reference_sites()[object].span_mm
    if span is None:
        return None
    factor = _scale(knee_scale_mm)
    return factor * span[0], factor * span[1], factor * span[2]
