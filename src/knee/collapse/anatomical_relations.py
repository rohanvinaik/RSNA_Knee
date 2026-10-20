"""Authored anatomical relationships from the objects document, not study measurements."""

from __future__ import annotations

from collections.abc import Iterable

Relation = tuple[str, str, tuple[str, ...], str, str]
SOURCE = "docs/OBJECTS_AND_CONDITIONS.md §4"
BASIS = "anatomical_definition"

# subject, predicate, targets, qualifier, source
RELATIONSHIPS: tuple[Relation, ...] = (
    ("joint", "between", ("femur", "tibia"), "", SOURCE),
    ("meniscus", "between", ("femur", "tibia"), "generic compartment", SOURCE),
    ("medial_meniscus", "between", ("femur", "tibia"), "medial compartment", SOURCE),
    ("lateral_meniscus", "between", ("femur", "tibia"), "lateral compartment", SOURCE),
    ("femoral_cartilage", "covers", ("femur",), "articular surface", SOURCE),
    ("tibial_cartilage", "covers", ("tibia",), "articular surface", SOURCE),
    (
        "patellar_cartilage",
        "covers",
        ("patella",),
        "posterior articular surface",
        SOURCE,
    ),
    (
        "trochlear_cartilage",
        "covers",
        ("femur",),
        "facing trochlear articular surface",
        SOURCE,
    ),
    (
        "acl",
        "attaches_to",
        ("femur", "tibia"),
        "lateral femoral condyle; tibial intercondylar area",
        SOURCE,
    ),
    (
        "pcl",
        "attaches_to",
        ("femur", "tibia"),
        "medial femoral condyle; posterior tibia",
        SOURCE,
    ),
    (
        "mcl",
        "attaches_to",
        ("femur", "tibia"),
        "medial epicondyle; proximal tibia",
        SOURCE,
    ),
    ("mcl", "attaches_to", ("medial_meniscus",), "deep layer", SOURCE),
    (
        "lcl",
        "attaches_to",
        ("femur", "fibula"),
        "lateral femoral condyle; fibular head",
        SOURCE,
    ),
    (
        "patellar_tendon",
        "attaches_to",
        ("patella", "tibia"),
        "patellar apex; tibial tuberosity",
        SOURCE,
    ),
    ("quadriceps_tendon", "attaches_to", ("patella",), "superior pole", SOURCE),
    (
        "medial_patellar_retinaculum",
        "attaches_to",
        ("patella", "femur"),
        "medial side; medial femoral condyle",
        SOURCE,
    ),
    (
        "lateral_patellar_retinaculum",
        "attaches_to",
        ("patella", "femur"),
        "lateral side; lateral femoral condyle",
        SOURCE,
    ),
    ("hoffa_fat_pad", "posterior_to", ("patellar_tendon",), "", SOURCE),
    (
        "suprapatellar_fat",
        "between",
        ("quadriceps_tendon", "femur"),
        "suprapatellar region",
        SOURCE,
    ),
    ("quadriceps_fat_pad", "anterior_to", ("recess",), "suprapatellar portion", SOURCE),
    (
        "prefemoral_fat_pad",
        "posterior_to",
        ("recess",),
        "suprapatellar portion",
        SOURCE,
    ),
    (
        "anterior_synovial_recess",
        "between",
        ("patella", "femur"),
        "posterior patellar face; anterior femoral face",
        SOURCE,
    ),
    ("synovium", "lines", ("joint_capsule",), "", SOURCE),
    ("synovium", "bounds", ("joint_fluid",), "", SOURCE),
    ("joint_capsule", "encloses", ("joint",), "", SOURCE),
    (
        "gastrocnemius_semimembranosus_bursa",
        "between",
        ("medial_gastrocnemius", "semimembranosus"),
        "",
        SOURCE,
    ),
    (
        "semimembranosus",
        "attaches_to",
        ("tibia",),
        "direct arm; posteromedial proximal tibia",
        SOURCE,
    ),
    ("semitendinosus", "attaches_to", ("tibia",), "distal pes anserinus", SOURCE),
    ("gracilis", "attaches_to", ("tibia",), "distal pes anserinus", SOURCE),
    ("sartorius", "attaches_to", ("tibia",), "distal pes anserinus", SOURCE),
    (
        "medial_gastrocnemius",
        "posterior_to",
        ("femur",),
        "medial femoral condyle",
        SOURCE,
    ),
    (
        "lateral_gastrocnemius",
        "posterior_to",
        ("femur",),
        "lateral femoral condyle",
        SOURCE,
    ),
    ("popliteal_artery", "anterior_to", ("popliteal_vein",), "", SOURCE),
    ("popliteus_tendon", "medial_to", ("lcl",), "at the femoral sulcus", SOURCE),
    ("biceps_femoris_tendon", "attaches_to", ("fibula",), "fibular head", SOURCE),
    ("iliotibial_band", "deep_to", ("subcutaneous_fat",), "lateral knee", SOURCE),
)


def relationships_for(names: Iterable[str]) -> dict[str, list[dict[str, object]]]:
    """Return authored relations whose subject and every target are in ``names``.

    The returned dictionaries and target lists are newly allocated on every call.
    They describe definitions only; they do not report a measured or satisfied
    relation.
    """
    requested = dict.fromkeys(names)
    present = set(requested)
    result: dict[str, list[dict[str, object]]] = {name: [] for name in requested}
    for subject, predicate, targets, qualifier, source in RELATIONSHIPS:
        if subject not in present or not set(targets).issubset(present):
            continue
        result.setdefault(subject, []).append(
            {
                "subject": subject,
                "predicate": predicate,
                "targets": list(targets),
                "qualifier": qualifier,
                "source": source,
                "basis": BASIS,
            }
        )
    return result
