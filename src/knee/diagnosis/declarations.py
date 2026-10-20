"""Anatomical questions over observed, role-qualified MRI content.

The twelve IDs are the train.csv columns (OBJECTS_AND_CONDITIONS §§4–6).
The source names and facets come from OBJECT_CODES, make_mri_spec and its
secondary/coarse declarations. These declarations supply neither diagnoses nor
numeric MRI references. In particular, a bone role is not a localized fracture
call, and its marrow is not an independently encoded object.

Composition must prepend ``object/<canonical-name>/`` to each original bank.
The default prefixes match the JSON facet addresses produced by expand_facets,
including each view, scale and direction, without selecting acquisition/status
words, projected-target membership or authored definitions. Measured context
objects remain available alongside the primary tissue. No sum is claimed to be
a measured interaction or a medial/lateral subdivision of a whole bone.

Consumers validate profile mode, source, scope, layout/reference compatibility
and availability. Selection reads bank names only: a selected but silent bank
stays silent. Composition, teaching, query encoding and recall share this API;
no selector has an unnamed all-bank fallback.
"""

from __future__ import annotations

from knee.diagnosis.models import Question
from knee.encoding.counts import BankLayout, CountBundle, CountLayout

__all__ = ["QUESTIONS", "question_for", "select_question_banks"]

# Only actual measured-content families. The mixed numeric/word banks retain
# the encoder's missing-reference states; this module never supplies a middle.
_PLACE_BANKS = ("lens_boolean", "lens_raw_signal", "lens_distance")
_ADDITIONAL_BANKS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("native_profile_area", ("femur", "tibia", "fibula", "joint_fluid")),
    ("coarse_unfiltered", ("femur", "tibia", "patella", "fibula")),
    ("coarse_scale_filtered", ("femur", "tibia")),
    ("axial_joint_samples", ("joint",)),
    ("posterior_trace_values", ("semimembranosus",)),
)


def _question(question_id: str, objects: tuple[str, ...]) -> Question:
    """Bind source roles to exact base-bank prefixes of expanded facets."""
    prefixes = tuple(
        f'object/{name}/facet:["{bank}",'
        for name in objects
        for bank in (
            *_PLACE_BANKS,
            *(bank for bank, sources in _ADDITIONAL_BANKS if name in sources),
        )
    )
    return Question(
        question_id=question_id,
        subject=f"diagnosis/{question_id}",
        objects=objects,
        bank_prefixes=prefixes,
    )


QUESTIONS: tuple[Question, ...] = (
    _question("ACL", ("acl", "femur", "tibia", "pcl")),
    _question("MCL", ("mcl", "medial_meniscus", "femur", "tibia")),
    _question("Medial Meniscus", ("medial_meniscus", "femur", "tibia", "joint")),
    _question("Lateral Meniscus", ("lateral_meniscus", "femur", "tibia", "joint")),
    _question(
        "Medial OA",
        (
            "femur",
            "tibia",
            "femoral_cartilage",
            "tibial_cartilage",
            "medial_meniscus",
            "joint",
        ),
    ),
    _question(
        "Lateral OA",
        (
            "femur",
            "tibia",
            "femoral_cartilage",
            "tibial_cartilage",
            "lateral_meniscus",
            "joint",
        ),
    ),
    _question(
        "PF OA",
        ("patella", "femur", "patellar_cartilage", "trochlear_cartilage"),
    ),
    _question(
        "Effusion",
        (
            "joint",
            "joint_fluid",
            "anterior_synovial_recess",
            "joint_capsule",
            "quadriceps_fat_pad",
            "prefemoral_fat_pad",
        ),
    ),
    _question(
        "Synovitis",
        (
            "synovium",
            "joint_fluid",
            "joint",
            "anterior_synovial_recess",
            "joint_capsule",
        ),
    ),
    _question(
        "Baker's",
        (
            "gastrocnemius_semimembranosus_bursa",
            "medial_gastrocnemius",
            "semimembranosus",
            "joint_capsule",
            "joint",
        ),
    ),
    _question("Contusion", ("femur", "tibia", "patella")),
    _question("Fracture", ("femur", "tibia", "patella", "fibula")),
)


def question_for(question_id: str) -> Question:
    """Return the frozen declaration for an exact train.csv ID; else KeyError."""
    for question in QUESTIONS:
        if question.question_id == question_id:
            return question
    raise KeyError(question_id)


def _bank_selection(
    bank: str, explicit: tuple[str, ...], prefixes: tuple[str, ...]
) -> str:
    """Pure selection decision; explicit names take precedence over prefixes."""
    if explicit:
        return "selected_explicit" if bank in explicit else "outside_explicit"
    if prefixes:
        return "selected_prefix" if bank.startswith(prefixes) else "outside_prefix"
    return "undeclared"


def select_question_banks(question: Question, bundle: CountBundle) -> tuple[str, ...]:
    """Select declared names present in the layout, in layout order.

    Explicit ``banks`` override ``bank_prefixes``. Missing names are omitted;
    an unmatched or undeclared selection returns (). Empty/malformed selectors
    are refused, so an empty prefix cannot silently mean every bank. Custom
    questions may explicitly name measured context/interaction banks. Callers
    remain responsible for their semantics and for count/status validation.
    """
    if not isinstance(question, Question):
        raise TypeError("question_required")
    for selectors in (question.banks, question.bank_prefixes):
        if (
            not isinstance(selectors, tuple)
            or any(not isinstance(name, str) or not name for name in selectors)
            or len(set(selectors)) != len(selectors)
        ):
            raise ValueError("invalid_question_bank_selectors")
    if not isinstance(bundle, CountBundle) or not isinstance(
        bundle.layout, CountLayout
    ):
        raise TypeError("count_bundle_required")
    banks = bundle.layout.banks
    if not isinstance(banks, tuple) or any(
        not isinstance(bank, BankLayout)
        or not isinstance(bank.name, str)
        or not bank.name
        for bank in banks
    ):
        raise ValueError("invalid_bank_layout")
    names = tuple(bank.name for bank in banks)
    if len(set(names)) != len(names):
        raise ValueError("duplicate_bank_names")
    return tuple(
        name
        for name in names
        if _bank_selection(name, question.banks, question.bank_prefixes)
        in ("selected_explicit", "selected_prefix")
    )
