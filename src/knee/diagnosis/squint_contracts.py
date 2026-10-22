"""Typed condition contracts for squint-first production.

Twelve plain declarations (one per train.csv column) say which located objects
speak for a condition and in what role; twelve plain functions combine the
object-level recall evidence of one study into ``assigned`` / ``defeated`` /
``open``; ``rank_condition`` serializes that finding as a continuous value.

What this module is, and is not (Rohan, 2026-10-21 and the squint contract):

* Roles are distinct. ``necessary`` objects: a warranted normal reading of one
  defeats the condition. ``sufficient`` configurations: when every member is a
  warranted positive reading the condition is assigned. ``alternatives``: any
  one branch may carry the condition, so one normal branch cannot rule out the
  condition elsewhere; every alternative must be observed negative to defeat.
  ``supporting`` objects are context: they are reported, never decisive. A
  positive condition presentation is not a claim that every context tissue is
  injured, and a normal context tissue is not a missing required finding.
* All necessary predicates holding is not treated as sufficiency. Literal
  clinical branches remain distinct from independently diagnosed whole-case
  configurations. Rohan explicitly authorizes warranted configuration recall
  to decide for either sign when its comparison includes defining tissue and
  no applicable anatomical finding contradicts it. Whole-normal configuration
  recall does not require a separate negative finding at every possible site.
* Unknown is not negative. Missing, silent, unregistered, malformed, censored
  or proposal-only evidence is unknown; only a warranted ``absent`` recall
  outcome is a negative reading. Strong Kleene logic carries readings through
  alternatives; conflicting trusted assignments stay a visible conflict and are
  never averaged away. Cases speaking without sourced trust are only proposals.
* Nothing here is a clinical threshold, a class prototype, a fitted band or a
  claim of calibrated probability. ``rank_condition`` is a fixed, uncalibrated
  serialization: ``p = (3*r + 1 + e) / 9`` with ``r`` = 0/1/2 for
  defeated/open/assigned and ``e = (1 + s_plus - s_minus) / 2``, where
  ``s_plus``/``s_minus`` are the best eligible exact squared cosines of
  positive/negative whole cases (one maximum per sign, never a sum or a mean
  of weak voices). ``e`` lies in [0, 1], so every tier is an open interval
  inside (0, 1): defeated [1/9, 2/9], open [4/9, 5/9], assigned [7/9, 8/9].
  Neither 0 nor 1 is ever produced and tiers never overlap.

Every function is pure: inputs are never mutated and results contain only
JSON-compatible values (plain ints stay exact, however large).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

__all__ = [
    "CONTRACTS",
    "FINDING_SCHEMA",
    "JOINT_PREFIX",
    "POLICY_ID",
    "QUESTION_IDS",
    "SOURCES",
    "ConditionContract",
    "ContractError",
    "combine_condition",
    "contract_for",
    "rank_condition",
]

POLICY_ID = "knee.squint-contracts/tiered-signed-squared-cosine-v1"
FINDING_SCHEMA = "knee.squint-condition-finding/v1"
# A whole-question (joint) recall voice is keyed "diagnosis/<question>". It
# can grade a finding and can decide only through trusted cases whose common
# speaking banks cover the condition's declared own-tissue roles.
JOINT_PREFIX = "diagnosis/"

QUESTION_IDS = (
    "ACL",
    "MCL",
    "Medial Meniscus",
    "Lateral Meniscus",
    "Medial OA",
    "Lateral OA",
    "PF OA",
    "Effusion",
    "Synovitis",
    "Baker's",
    "Contusion",
    "Fracture",
)

_ASSIGNED = "assigned"
_DEFEATED = "defeated"
_OPEN = "open"
_TIER = {_DEFEATED: 0, _OPEN: 1, _ASSIGNED: 2}

_POSITIVE = "positive"
_NEGATIVE = "negative"
_UNKNOWN = "unknown"
_CONFLICT = "conflict"

_SIGNS = (-1, 1)
_DECISION_SCOPES = frozenset({"decide", "grade_only"})
_UNSUPPORTED_REASON = "unsupported_combination:sufficient_configuration_not_sourced"

# ---------------------------------------------------------------------------
# literal anatomical sources (docs/OBJECTS_AND_CONDITIONS.md, "Sources")
# ---------------------------------------------------------------------------

SOURCES: dict[str, str] = {
    "K": (
        "Kaggle, RSNA Knee Abnormalities Detection "
        "(rsna-knee-abnormality-detection), Data page."
    ),
    "C": (
        "Chien A, Weaver JS, Kinne E, Omar I. Magnetic resonance imaging of the "
        "knee. Pol J Radiol. 2020;85:e509–e531. doi:10.5114/pjr.2020.99415 "
        "(PMC7571514; CC BY-NC-ND 4.0)."
    ),
    "Kh": (
        "Khanna AJ, Cosgarea AJ, Mont MA, Andres BM, Domb BG, Evans PJ, "
        "Bluemke DA, Frassica FJ. Magnetic resonance imaging of the knee: "
        "current techniques and spectrum of disease. J Bone Joint Surg Am. "
        "2001;83-A Suppl 2 Pt 2."
    ),
    "AUR": (
        "McClure KE, Trunz LM (Jefferson). How to approach a Knee MRI. "
        "Association of University Radiologists, ACER educator resource (PDF)."
    ),
    "R-KNEE": "Radiopaedia, Knee joint, rID 31365.",
    "R-ACL": "Radiopaedia, Anterior cruciate ligament, rID 23201.",
    "R-ACLT": "Radiopaedia, Anterior cruciate ligament tear, rID 12490.",
    "R-MCLI": (
        "Radiopaedia, Medial collateral ligament injury of the knee, rID 79899."
    ),
    "R-MEN": "Radiopaedia, Knee menisci, rID 26810.",
    "R-MT": "Radiopaedia, Meniscal tear, rID 32943.",
    "R-OA": "Radiopaedia, Osteoarthritis of the knee, rID 37587.",
    "R-EFF": "Radiopaedia, Joint effusion, rID 10594.",
    "R-SYN": "Radiopaedia, Synovitis, rID 67379.",
    "R-BAKER": "Radiopaedia, Baker cyst, rID 21117.",
    "R-BB": "Radiopaedia, Bone bruise, rID 32984.",
}


# ---------------------------------------------------------------------------
# declarations
# ---------------------------------------------------------------------------


class ContractError(ValueError):
    """A named misuse of the contract API (never a data-quality finding)."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.code = code
        self.detail = detail


@dataclass(frozen=True, slots=True)
class ConditionContract:
    """One condition's typed declaration; data only, no behaviour of its own.

    ``statements`` are literal source words, each with the keys of the sources
    in ``SOURCES`` that carry them. ``necessary``, ``alternatives`` and
    ``supporting`` name disjoint canonical object subjects. ``sufficient`` lists
    configurations (tuples of subjects that must all be warranted positive); it
    is empty exactly when the sources give no combination rule.
    """

    question: str
    contract_id: str
    kind: str
    statements: tuple[tuple[tuple[str, ...], str], ...]
    necessary: tuple[str, ...]
    sufficient: tuple[tuple[str, ...], ...]
    alternatives: tuple[str, ...]
    supporting: tuple[str, ...]
    unmeasured_source_predicates: tuple[str, ...] = ()
    limits: tuple[str, ...] = ()

    @property
    def subjects(self) -> tuple[str, ...]:
        return (*self.necessary, *self.alternatives, *self.supporting)

    @property
    def source_keys(self) -> tuple[str, ...]:
        keys: list[str] = []
        for source_keys, _ in self.statements:
            for key in source_keys:
                if key not in keys:
                    keys.append(key)
        return tuple(keys)

    @property
    def sufficiency_sourced(self) -> bool:
        return bool(self.sufficient)

    def source_declaration(self) -> list[dict[str, Any]]:
        """Literal statements with their source keys and citations."""
        return [
            {
                "keys": list(keys),
                "statement": statement,
                "citations": [SOURCES[key] for key in keys],
            }
            for keys, statement in self.statements
        ]


_OA_WORDS = (
    "knee osteoarthritis: joint-space narrowing, subchondral sclerosis, "
    "marginal osteophytes, subchondral cysts, altered shape of the condyles and "
    "plateau; the medial compartment is affected more often and more severely "
    "than the lateral"
)
_OA_LIMIT = (
    "the sources list the findings of osteoarthritis but give no rule saying "
    "how many or which combination suffice, so no sufficient configuration is "
    "declared for an isolated branch; warranted whole-configuration recall may decide"
)
_BONE_LIMIT = (
    "marrow is not an independently encoded object: a bone's reading speaks "
    "for that bone only, and one normal bone cannot rule out injury elsewhere"
)

_ACL = ConditionContract(
    question="ACL",
    contract_id="knee.squint-contract/acl/v1",
    kind="single_tissue",
    statements=(
        (("K",), "ACL: «anterior cruciate ligament injury»"),
        (
            ("R-ACLT",),
            "injury of the ACL; its tears are the most common knee ligament injury",
        ),
        (
            ("R-ACL",),
            (
                "ACL; its attachments on the lateral femoral condyle and the tibial "
                "intercondylar area"
            ),
        ),
    ),
    necessary=("acl",),
    sufficient=(("acl",),),
    alternatives=(),
    supporting=("femur", "tibia", "pcl"),
    limits=(
        (
            "femur and tibia are the ACL's attachment context and the PCL is its "
            "neighbour in the notch; a positive ACL presentation does not claim "
            "they are injured"
        ),
    ),
)

_MCL = ConditionContract(
    question="MCL",
    contract_id="knee.squint-contract/mcl/v1",
    kind="single_tissue",
    statements=(
        (("K",), "MCL: «medial collateral ligament injury»"),
        (
            ("R-MCLI",),
            "sprains, partial and complete tears of the superficial and/or deep MCL",
        ),
        (
            ("R-KNEE", "C"),
            "MCL; medial meniscus (attached); medial femoral epicondyle; medial tibia",
        ),
    ),
    necessary=("mcl",),
    sufficient=(("mcl",),),
    alternatives=(),
    supporting=("medial_meniscus", "femur", "tibia"),
    limits=(
        (
            "the deep layer attaches the periphery of the medial meniscus [C]; the "
            "meniscus, femur and tibia are attachment context, not proof of an MCL "
            "injury and not required to be injured"
        ),
    ),
)

_MEDIAL_MENISCUS = ConditionContract(
    question="Medial Meniscus",
    contract_id="knee.squint-contract/medial-meniscus/v1",
    kind="single_tissue",
    statements=(
        (("K",), "Medial Meniscus: «medial meniscus tear»"),
        (("R-MT",), "failure of the fibrocartilaginous meniscus"),
        (
            ("R-MEN",),
            "medial meniscus; the condyle and plateau it sits between",
        ),
    ),
    necessary=("medial_meniscus",),
    sufficient=(("medial_meniscus",),),
    alternatives=(),
    supporting=("femur", "tibia", "joint"),
    limits=(
        (
            "the condyle, plateau and joint space are the meniscus's neighbours "
            "[R-MEN]; they are context, not required findings"
        ),
    ),
)

_LATERAL_MENISCUS = ConditionContract(
    question="Lateral Meniscus",
    contract_id="knee.squint-contract/lateral-meniscus/v1",
    kind="single_tissue",
    statements=(
        (("K",), "Lateral Meniscus: «lateral meniscus tear»"),
        (("R-MT",), "failure of the fibrocartilaginous meniscus"),
        (
            ("R-MEN",),
            "lateral meniscus; the condyle and plateau it sits between",
        ),
    ),
    necessary=("lateral_meniscus",),
    sufficient=(("lateral_meniscus",),),
    alternatives=(),
    supporting=("femur", "tibia", "joint"),
    limits=(
        (
            "the condyle, plateau and joint space are the meniscus's neighbours "
            "[R-MEN]; they are context, not required findings"
        ),
    ),
)

_MEDIAL_OA = ConditionContract(
    question="Medial OA",
    contract_id="knee.squint-contract/medial-oa/v1",
    kind="alternative_branches",
    statements=(
        (
            ("K",),
            "Medial OA: «osteoarthritis of the medial tibiofemoral compartment»",
        ),
        (("R-OA",), _OA_WORDS),
        (
            ("R-KNEE", "R-MEN"),
            "medial femoral condyle, medial tibial facet, their cartilage, medial meniscus",
        ),
    ),
    necessary=(),
    sufficient=(),
    alternatives=(
        "femur",
        "tibia",
        "femoral_cartilage",
        "tibial_cartilage",
        "medial_meniscus",
    ),
    supporting=("joint",),
    limits=(
        _OA_LIMIT,
        (
            "a whole bone is not a medial subdivision; a branch reading is only "
            "the recalled presentation of that object for this question"
        ),
    ),
)

_LATERAL_OA = ConditionContract(
    question="Lateral OA",
    contract_id="knee.squint-contract/lateral-oa/v1",
    kind="alternative_branches",
    statements=(
        (
            ("K",),
            "Lateral OA: «osteoarthritis of the lateral tibiofemoral compartment»",
        ),
        (("R-OA",), _OA_WORDS),
        (
            ("R-KNEE", "R-MEN"),
            (
                "the same on the lateral side: lateral femoral condyle, lateral "
                "tibial facet, their cartilage, lateral meniscus"
            ),
        ),
    ),
    necessary=(),
    sufficient=(),
    alternatives=(
        "femur",
        "tibia",
        "femoral_cartilage",
        "tibial_cartilage",
        "lateral_meniscus",
    ),
    supporting=("joint",),
    limits=(
        _OA_LIMIT,
        (
            "a whole bone is not a lateral subdivision; a branch reading is only "
            "the recalled presentation of that object for this question"
        ),
    ),
)

_PF_OA = ConditionContract(
    question="PF OA",
    contract_id="knee.squint-contract/pf-oa/v1",
    kind="alternative_branches",
    statements=(
        (("K",), "PF OA: «patellofemoral osteoarthritis»"),
        (("R-OA",), "as above, in the patellofemoral joint: " + _OA_WORDS),
        (
            ("R-KNEE",),
            (
                "the patella's posterior facets, the femoral condyles they meet, "
                "their cartilage"
            ),
        ),
    ),
    necessary=(),
    sufficient=(),
    alternatives=("patella", "femur", "patellar_cartilage", "trochlear_cartilage"),
    supporting=(),
    limits=(_OA_LIMIT,),
)

_EFFUSION = ConditionContract(
    question="Effusion",
    contract_id="knee.squint-contract/effusion/v1",
    kind="alternative_branches",
    statements=(
        (("K",), "Effusion: «joint effusion / excess fluid»"),
        (
            ("R-EFF",),
            (
                "an increased amount of fluid within the synovial compartment, "
                "where normally there is only a little"
            ),
        ),
        (
            ("C", "R-KNEE"),
            "joint cavity and its recesses; suprapatellar bursa",
        ),
        (
            ("C", "Kh"),
            (
                "fluid signal in the joint's own recesses: low on T1W, high on T2W, "
                "very high on fat-suppressed T2W"
            ),
        ),
    ),
    necessary=(),
    sufficient=(("joint_fluid",), ("anterior_synovial_recess",)),
    alternatives=("joint_fluid", "anterior_synovial_recess"),
    supporting=("joint", "joint_capsule", "quadriceps_fat_pad", "prefemoral_fat_pad"),
    limits=(
        (
            "the suprapatellar bursa is part of the synovial compartment and "
            "usually communicates with the joint [C], so excess fluid in the "
            "recess is an effusion on its own; the fat pads only border the "
            "recess [R-EFF] and are context"
        ),
    ),
)

_SYNOVITIS = ConditionContract(
    question="Synovitis",
    contract_id="knee.squint-contract/synovitis/v1",
    kind="single_tissue",
    statements=(
        (("K",), "Synovitis: «inflammation of the joint lining»"),
        (("R-SYN",), "any inflammatory process of the synovium"),
        (("C", "R-KNEE"), "synovium; the joint fluid beside it"),
    ),
    necessary=("synovium",),
    sufficient=(("synovium",),),
    alternatives=(),
    supporting=("joint_fluid", "joint", "anterior_synovial_recess", "joint_capsule"),
    limits=(
        (
            "«contrast-enhanced imaging allows better differentiation between "
            "joint effusion and synovial disorders» [C] and no tag marks "
            "contrast [K]: fluid beside the synovium is context and never decides "
            "synovitis"
        ),
    ),
)

_BAKERS = ConditionContract(
    question="Baker's",
    contract_id="knee.squint-contract/bakers/v1",
    kind="single_tissue",
    statements=(
        (("K",), "Baker's: «Baker's cyst»"),
        (
            ("R-BAKER",),
            (
                "a fluid-filled, distended, synovial-lined lesion in the popliteal "
                "fossa between the medial gastrocnemius head and the semimembranosus "
                "tendon, communicating with the knee joint"
            ),
        ),
        (
            ("R-BAKER",),
            (
                "medial gastrocnemius head; semimembranosus tendon; posterior "
                "capsule; gastrocnemius–semimembranosus bursa"
            ),
        ),
        (
            ("R-BAKER", "AUR"),
            (
                "Fluid outside the joint at the back, between the medial "
                "gastrocnemius head and the semimembranosus tendon and joined to "
                "the joint by a neck, is a Baker's cyst"
            ),
        ),
    ),
    necessary=("gastrocnemius_semimembranosus_bursa",),
    sufficient=(("gastrocnemius_semimembranosus_bursa",),),
    alternatives=(),
    supporting=("medial_gastrocnemius", "semimembranosus", "joint_capsule", "joint"),
    unmeasured_source_predicates=("communicates_with_knee_joint",),
    limits=(
        (
            "the lesion is the distended bursa between the two named structures; "
            "those structures, the capsule and the joint are context and a normal "
            "reading of any of them is not a missing required finding"
        ),
        (
            "communication with the joint [R-BAKER] has no measured object, so an "
            "assigned finding does not verify it"
        ),
    ),
)

_CONTUSION = ConditionContract(
    question="Contusion",
    contract_id="knee.squint-contract/contusion/v1",
    kind="alternative_branches",
    statements=(
        (("K",), "Contusion: «bone contusion / bone bruise»"),
        (
            ("R-BB",),
            (
                "trabecular microfractures with haemorrhage, without a discrete "
                "fracture line or contour abnormality"
            ),
        ),
        (("K",), "the marrow of the femur, tibia and patella"),
    ),
    necessary=(),
    sufficient=(("femur",), ("tibia",), ("patella",)),
    alternatives=("femur", "tibia", "patella"),
    supporting=(),
    limits=(_BONE_LIMIT,),
)

_FRACTURE = ConditionContract(
    question="Fracture",
    contract_id="knee.squint-contract/fracture/v1",
    kind="alternative_branches",
    statements=(
        (("K",), "Fracture: «fracture»"),
        (
            ("C",),
            (
                "on MRI, a low-signal line on T1W, surrounded by oedema-like signal "
                "on fluid-sensitive sequences; a contusion has the oedema without "
                "the line"
            ),
        ),
        (("K",), "the femur, tibia, patella and fibula"),
    ),
    necessary=(),
    sufficient=(("femur",), ("tibia",), ("patella",), ("fibula",)),
    alternatives=("femur", "tibia", "patella", "fibula"),
    supporting=(),
    limits=(_BONE_LIMIT,),
)

CONTRACTS: tuple[ConditionContract, ...] = (
    _ACL,
    _MCL,
    _MEDIAL_MENISCUS,
    _LATERAL_MENISCUS,
    _MEDIAL_OA,
    _LATERAL_OA,
    _PF_OA,
    _EFFUSION,
    _SYNOVITIS,
    _BAKERS,
    _CONTUSION,
    _FRACTURE,
)


def contract_for(question: str) -> ConditionContract:
    """Return the declaration for an exact train.csv column name."""
    if not isinstance(question, str):
        raise ContractError("question_not_text")
    for contract in CONTRACTS:
        if contract.question == question:
            return contract
    raise ContractError("question_unknown", question)


# ---------------------------------------------------------------------------
# object-level readings from recall evidence
# ---------------------------------------------------------------------------

# recall outcome -> (reading state, named code). Only a warranted present or
# absent is a positive or negative reading; everything else is unknown or a
# visible conflict.
_RECALL_STATES: dict[str, tuple[str, str]] = {
    "present": (_POSITIVE, "warranted_positive"),
    "absent": (_NEGATIVE, "warranted_negative"),
    "unresolved_conflict": (_CONFLICT, "conflicting_trusted_cases"),
    "proposal": (_UNKNOWN, "proposal_without_sourced_trust"),
    "unresolved_missing_reading": (_UNKNOWN, "missing_reading"),
    "unresolved_censored": (_UNKNOWN, "censored_by_near_miss_veto"),
    "unresolved_no_precedent": (_UNKNOWN, "no_precedent"),
    "incompatible_encoding": (_UNKNOWN, "incompatible_encoding"),
    "invalid_input": (_UNKNOWN, "recall_rejected_input"),
}
_REQUIRED_SIGNS: dict[str, frozenset[int]] = {
    "present": frozenset({1}),
    "absent": frozenset({-1}),
    "unresolved_conflict": frozenset({1, -1}),
}
_ID_FIELDS = (
    "excluded_case_ids",
    "incompatible_case_ids",
    "silent_case_ids",
    "censor_ids",
    "speaking_case_ids",
)
_INELIGIBLE_FIELDS = (
    "excluded_case_ids",
    "incompatible_case_ids",
    "silent_case_ids",
)


def _id_list_ok(values: object) -> bool:
    return (
        isinstance(values, list)
        and all(isinstance(item, str) and item for item in values)
        and len(set(values)) == len(values)
    )


def _sign_list_ok(values: object, *, unique: bool) -> bool:
    if not isinstance(values, list):
        return False
    if any(type(item) is not int or item not in _SIGNS for item in values):
        return False
    return not unique or len(set(values)) == len(values)


def _banks_ok(banks: object) -> bool:
    """Jointly speaking banks: a nonempty list of names, or the pipeline's
    compact reference ``{"bank_set": <digest>, "count": <positive int>}``."""
    if isinstance(banks, Mapping):
        count = banks.get("count")
        digest = banks.get("bank_set")
        return (
            isinstance(digest, str)
            and bool(digest)
            and type(count) is int
            and count > 0
        )
    return (
        isinstance(banks, list)
        and bool(banks)
        and all(isinstance(bank, str) and bank for bank in banks)
        and len(set(banks)) == len(banks)
    )


def _check_row(
    row: object,
    aliases: tuple[str, ...] | None,
    seen: set[str],
    ineligible: set[str],
) -> tuple[dict[str, Any] | None, bool | None, str | None]:
    """Validate one signed whole-case row; return (row, trust flag, error code).

    The trust flag is None when the row carries no trust fields, else whether
    the case reached a sourced trust level. Impossible cosines (dot**2 greater
    than the product of the norms), negative or boolean counts, unsigned calls
    and duplicate or ineligible case ids are errors, never clipped.
    """
    if not isinstance(row, Mapping):
        return None, None, "case_term_not_object"
    case_id = row.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        return None, None, "case_id_invalid"
    if case_id in seen:
        return None, None, "duplicate_case_id"
    seen.add(case_id)
    if case_id in ineligible:
        return None, None, "ineligible_case_has_terms"
    call = row.get("call")
    if type(call) is not int or call not in _SIGNS:
        return None, None, "case_call_invalid"
    named = row.get("subject")
    if aliases is not None and named is not None and named not in aliases:
        return None, None, "case_subject_mismatch"
    terms = row.get("terms")
    if not isinstance(terms, Mapping):
        return None, None, "cosine_terms_missing"
    dot = terms.get("dot")
    left = terms.get("left_norm_sq")
    right = terms.get("right_norm_sq")
    if type(dot) is not int or dot < 0:
        return None, None, "cosine_dot_invalid"
    if type(left) is not int or left <= 0 or type(right) is not int or right <= 0:
        return None, None, "cosine_norm_invalid"
    if dot * dot > left * right:
        return None, None, "cosine_terms_impossible"
    banks = row.get("common_speaking_banks")
    if banks is not None and not _banks_ok(banks):
        return None, None, "common_speaking_banks_invalid"
    call_scope = row.get("call_scope")
    if call_scope is not None and (not isinstance(call_scope, str) or not call_scope):
        return None, None, "case_call_scope_invalid"
    trust_flag: bool | None = None
    if "trust" in row or "reaches_trust" in row:
        trust = row.get("trust")
        trust_flag = bool(
            row.get("reaches_trust") is True
            and isinstance(trust, Mapping)
            and isinstance(trust.get("source"), str)
            and trust.get("source")
        )
    normalized: dict[str, Any] = {
        "case_id": case_id,
        "call": call,
        "terms": {"dot": dot, "left_norm_sq": left, "right_norm_sq": right},
        "reaches_trust": trust_flag,
    }
    if "call_scope" in row:
        normalized["call_scope"] = call_scope
    trust = row.get("trust")
    if isinstance(trust, Mapping) and isinstance(trust.get("source"), str):
        normalized["trust"] = {"source": trust["source"]}
    if isinstance(banks, list):
        normalized["common_speaking_banks"] = list(banks)
    elif banks is not None:
        normalized["common_speaking_banks"] = dict(banks)
    return normalized, trust_flag, None


def _normalize_record(
    record: object, aliases: tuple[str, ...]
) -> tuple[dict[str, Any] | None, list[str]]:
    """Validate one recall record; return (normalized copy, problem codes)."""
    if not isinstance(record, Mapping):
        return None, ["record_not_object"]
    problems: list[str] = []
    outcome = record.get("outcome")
    if not isinstance(outcome, str) or outcome not in _RECALL_STATES:
        problems.append("outcome_invalid")
    named = record.get("subject")
    if named is not None and named not in aliases:
        problems.append("subject_mismatch")
    decision_scope = record.get("decision_scope")
    if "decision_scope" in record and (
        not isinstance(decision_scope, str) or decision_scope not in _DECISION_SCOPES
    ):
        problems.append("decision_scope_invalid")

    id_lists: dict[str, list[str]] = {}
    for field in _ID_FIELDS:
        values = record.get(field, [])
        if _id_list_ok(values):
            id_lists[field] = list(values)
        else:
            problems.append(f"{field}_invalid")
            id_lists[field] = []
    ineligible: set[str] = set()
    for field in _INELIGIBLE_FIELDS:
        ineligible.update(id_lists[field])

    vetoes_raw = record.get("vetoed_answers", [])
    vetoes: list[int] = []
    if _sign_list_ok(vetoes_raw, unique=True):
        vetoes = list(vetoes_raw)  # type: ignore[arg-type]
    else:
        problems.append("vetoed_answers_invalid")

    speaking: list[int] | None = None
    speaking_raw = record.get("speaking_calls")
    if speaking_raw is not None:
        if _sign_list_ok(speaking_raw, unique=False):
            speaking = list(speaking_raw)  # type: ignore[arg-type]
        else:
            problems.append("speaking_calls_invalid")

    rows: list[dict[str, Any]] = []
    trust_flags: list[tuple[int, bool | None]] = []
    rows_raw = record.get("case_terms", [])
    if isinstance(rows_raw, list):
        seen: set[str] = set()
        for index, row in enumerate(rows_raw):
            normalized_row, trust_flag, code = _check_row(
                row, aliases, seen, ineligible
            )
            if code is not None:
                problems.append(f"case_terms[{index}]:{code}")
            elif normalized_row is not None:
                rows.append(normalized_row)
                trust_flags.append((normalized_row["call"], trust_flag))
    else:
        problems.append("case_terms_not_list")

    if problems:
        return None, problems

    assert isinstance(outcome, str)
    state, code = _RECALL_STATES[outcome]
    trust_checked = False
    required = _REQUIRED_SIGNS.get(outcome)
    if required is not None:
        if required & set(vetoes):
            problems.append("outcome_sign_is_vetoed")
        if speaking is not None and set(speaking) - set(vetoes) != required:
            problems.append("speaking_calls_disagree_with_outcome")
        if problems:
            return None, problems
        flagged = [(call, flag) for call, flag in trust_flags if flag is not None]
        if flagged:
            trust_checked = True
            trusted_signs = {call for call, flag in flagged if flag}
            if not required <= trusted_signs:
                # The outcome claims a warrant its own cases do not carry.
                state, code = _UNKNOWN, "speaking_without_sourced_trust"

    normalized_record: dict[str, Any] = {
        "outcome": outcome,
        "subject": aliases[0],
        "state": state,
        "code": code,
        "case_terms": rows,
        "vetoed_answers": sorted(vetoes),
        "trust_checked": trust_checked,
    }
    if decision_scope is not None:
        normalized_record["decision_scope"] = decision_scope
    for field in _ID_FIELDS:
        normalized_record[field] = id_lists[field]
    reason = record.get("reason")
    if isinstance(reason, str):
        normalized_record["recall_reason"] = reason
    return normalized_record, []


def _reading(
    state: str,
    code: str,
    *,
    outcomes: list[str] | None = None,
    problems: list[str] | None = None,
    speaking: list[str] | None = None,
    trust_checked: bool = False,
) -> dict[str, Any]:
    return {
        "state": state,
        "code": code,
        "recall_outcomes": outcomes or [],
        "problems": problems or [],
        "speaking_case_ids": speaking or [],
        "trust_checked": trust_checked,
    }


def _read_subject(
    raw: object,
    aliases: tuple[str, ...],
    *,
    study_positive_is_context: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Reduce one subject's evidence to a reading and its normalized records.

    A subject may carry several records (e.g. separate recalls). A warranted
    positive and a warranted negative together are a conflict; an unknown
    record never cancels a warranted one; any malformed record makes the whole
    subject unknown, because evidence that cannot be verified cannot speak.
    """
    if raw is None:
        return _reading(_UNKNOWN, "not_observed"), []
    records = list(raw) if isinstance(raw, (list, tuple)) else [raw]
    if not records:
        return _reading(_UNKNOWN, "not_observed"), []
    kept: list[dict[str, Any]] = []
    problems: list[str] = []
    for index, record in enumerate(records):
        normalized, found = _normalize_record(record, aliases)
        if found:
            prefix = f"{index}:" if len(records) > 1 else ""
            problems.extend(prefix + item for item in found)
        elif normalized is not None:
            if study_positive_is_context and normalized["state"] == _POSITIVE:
                positive_rows = [
                    row
                    for row in normalized["case_terms"]
                    if row["call"] == 1 and row["reaches_trust"] is not False
                ]
                if positive_rows and all(
                    row.get("call_scope") == "positive_condition_presentation"
                    for row in positive_rows
                ):
                    # The study says some bone is affected, not which one.
                    # Keep every comparison for recall/ranking without
                    # manufacturing a localized positive bone predicate.
                    normalized["state"] = _UNKNOWN
                    normalized["code"] = "study_positive_presentation_not_localized"
            if (
                normalized.get("decision_scope") == "grade_only"
                and normalized["state"] != _UNKNOWN
            ):
                # The caller explicitly withheld decision authority. Keep its
                # terms for ranking while making its reading non-decisive.
                normalized["state"] = _UNKNOWN
                normalized["code"] = "query_decision_scope_grade_only"
            kept.append(normalized)
    if problems:
        return _reading(_UNKNOWN, "evidence_malformed", problems=problems), []
    states = [item["state"] for item in kept]
    speaking = sorted({case for item in kept for case in item["speaking_case_ids"]})
    outcomes = [item["outcome"] for item in kept]
    checked = any(item["trust_checked"] for item in kept)
    if _CONFLICT in states or (_POSITIVE in states and _NEGATIVE in states):
        state, code = _CONFLICT, "conflicting_trusted_cases"
    elif _POSITIVE in states:
        state, code = _POSITIVE, "warranted_positive"
    elif _NEGATIVE in states:
        state, code = _NEGATIVE, "warranted_negative"
    else:
        state, code = _UNKNOWN, kept[0]["code"]
    return (
        _reading(
            state,
            code,
            outcomes=outcomes,
            speaking=speaking,
            trust_checked=checked,
        ),
        kept,
    )


# ---------------------------------------------------------------------------
# strong Kleene propagation (conflict stays visible, never folded to a value)
# ---------------------------------------------------------------------------


def _kleene_or(states: list[str]) -> str:
    if not states:
        return _UNKNOWN
    if _POSITIVE in states:
        return _POSITIVE
    if _CONFLICT in states:
        return _CONFLICT
    if _UNKNOWN in states:
        return _UNKNOWN
    return _NEGATIVE


def _kleene_and(states: list[str]) -> str:
    if not states:
        return _UNKNOWN
    if _NEGATIVE in states:
        return _NEGATIVE
    if _CONFLICT in states:
        return _CONFLICT
    if _UNKNOWN in states:
        return _UNKNOWN
    return _POSITIVE


# ---------------------------------------------------------------------------
# the twelve combiners
# ---------------------------------------------------------------------------


def _decision(
    outcome: str,
    reason: str,
    *,
    decided_by: list[str] | None = None,
    unresolved: list[str] | None = None,
    unsupported: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "outcome": outcome,
        "reason": reason,
        "decided_by": decided_by or [],
        "unresolved": unresolved or [],
        "unsupported": unsupported or [],
    }


def _single_tissue(
    contract: ConditionContract, readings: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """The condition is its one defining tissue: that tissue's warranted
    reading speaks. A warranted negative defeats regardless of any positive
    context; a positive assigns without claiming context tissues are injured.
    """
    primary = contract.necessary[0]
    reading = readings[primary]
    state = reading["state"]
    if state == _POSITIVE:
        return _decision(
            _ASSIGNED, f"{primary}_warranted_positive", decided_by=[primary]
        )
    if state == _NEGATIVE:
        return _decision(
            _DEFEATED, f"{primary}_warranted_negative", decided_by=[primary]
        )
    if state == _CONFLICT:
        reason = f"{primary}_conflicting_assignments"
    else:
        reason = f"{primary}_unknown:{reading['code']}"
    return _decision(_OPEN, reason, unresolved=[primary])


def _alternative_branches(
    contract: ConditionContract, readings: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Any declared branch may carry the condition (strong Kleene OR).

    One normal branch cannot rule out the condition elsewhere: defeat needs
    every alternative observed negative. Assignment needs a declared sufficient
    configuration; a positive branch without one is an unsupported combination
    and stays open with a bounded request.
    """
    alternatives = list(contract.alternatives)
    states = {subject: readings[subject]["state"] for subject in alternatives}
    branch = _kleene_or([states[subject] for subject in alternatives])
    if branch == _NEGATIVE:
        return _decision(
            _DEFEATED,
            "all_alternatives_observed_negative",
            decided_by=alternatives,
        )
    satisfied = [
        configuration
        for configuration in contract.sufficient
        if _kleene_and([states.get(subject, _UNKNOWN) for subject in configuration])
        == _POSITIVE
    ]
    if satisfied:
        members = {subject for configuration in satisfied for subject in configuration}
        decided = [subject for subject in alternatives if subject in members]
        return _decision(
            _ASSIGNED,
            "alternative_positive:" + ",".join(decided),
            decided_by=decided,
        )
    positives = [s for s in alternatives if states[s] == _POSITIVE]
    unresolved = [s for s in alternatives if states[s] in (_UNKNOWN, _CONFLICT)]
    if positives:
        return _decision(
            _OPEN,
            _UNSUPPORTED_REASON,
            unresolved=unresolved,
            unsupported=positives,
        )
    conflicts = [s for s in alternatives if states[s] == _CONFLICT]
    if conflicts:
        reason = "conflicting_assignments:" + ",".join(conflicts)
        unknown = [s for s in unresolved if s not in conflicts]
        if unknown:
            reason += ";unresolved:" + ",".join(unknown)
    else:
        reason = "alternatives_unresolved:" + ",".join(unresolved)
    return _decision(_OPEN, reason, unresolved=unresolved)


def _combine_acl(readings: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return _single_tissue(_ACL, readings)


def _combine_mcl(readings: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return _single_tissue(_MCL, readings)


def _combine_medial_meniscus(readings: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return _single_tissue(_MEDIAL_MENISCUS, readings)


def _combine_lateral_meniscus(readings: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return _single_tissue(_LATERAL_MENISCUS, readings)


def _combine_medial_oa(readings: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return _alternative_branches(_MEDIAL_OA, readings)


def _combine_lateral_oa(readings: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return _alternative_branches(_LATERAL_OA, readings)


def _combine_pf_oa(readings: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return _alternative_branches(_PF_OA, readings)


def _combine_effusion(readings: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return _alternative_branches(_EFFUSION, readings)


def _combine_synovitis(readings: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return _single_tissue(_SYNOVITIS, readings)


def _combine_bakers(readings: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return _single_tissue(_BAKERS, readings)


def _combine_contusion(readings: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return _alternative_branches(_CONTUSION, readings)


def _combine_fracture(readings: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return _alternative_branches(_FRACTURE, readings)


_COMBINERS = {
    "ACL": _combine_acl,
    "MCL": _combine_mcl,
    "Medial Meniscus": _combine_medial_meniscus,
    "Lateral Meniscus": _combine_lateral_meniscus,
    "Medial OA": _combine_medial_oa,
    "Lateral OA": _combine_lateral_oa,
    "PF OA": _combine_pf_oa,
    "Effusion": _combine_effusion,
    "Synovitis": _combine_synovitis,
    "Baker's": _combine_bakers,
    "Contusion": _combine_contusion,
    "Fracture": _combine_fracture,
}

# ---------------------------------------------------------------------------
# bounded observation requests
# ---------------------------------------------------------------------------

# Each request asks for an existing measurement of one object's own region or
# window. None asks for a full-study reconstruction, and the pipeline may drop
# the discretionary ones (zoom) at a deadline without changing the open finding.
_REQUEST_KIND = {
    "warranted_positive": "bounded_zoom",
    "warranted_negative": "bounded_zoom",
    "not_observed": "locate_object_region",
    "missing_reading": "profile_object_window",
    "no_precedent": "profile_object_window",
    "incompatible_encoding": "profile_object_window",
    "proposal_without_sourced_trust": "bounded_zoom",
    "speaking_without_sourced_trust": "bounded_zoom",
    "censored_by_near_miss_veto": "bounded_zoom",
    "conflicting_trusted_cases": "bounded_zoom",
    "recall_rejected_input": "repeat_object_recall",
    "evidence_malformed": "repeat_object_recall",
    "query_decision_scope_grade_only": "bounded_zoom",
}


def _request(question: str, subject: str, kind: str, reason: str) -> dict[str, Any]:
    return {
        "request_id": f"{question}/{subject}/{kind}",
        "kind": kind,
        "question": question,
        "subject": subject,
        "reason": reason,
        "scope": "object_region" if kind == "locate_object_region" else "object_window",
        "bounded": True,
        "full_study": False,
        "uses_existing_measurements": True,
        "discretionary": kind == "bounded_zoom",
    }


def _requests(
    question: str,
    readings: dict[str, dict[str, Any]],
    decision: dict[str, Any],
) -> list[dict[str, Any]]:
    if decision["outcome"] != _OPEN:
        return []
    found: list[dict[str, Any]] = []
    for subject in decision["unresolved"]:
        code = readings[subject]["code"]
        if code == "study_positive_presentation_not_localized":
            # More pixels cannot localize the teaching label's source claim.
            # Keep the scope uncertainty visible without scheduling a zoom.
            continue
        found.append(_request(question, subject, _REQUEST_KIND[code], code))
    for subject in decision["unsupported"]:
        found.append(_request(question, subject, "bounded_zoom", _UNSUPPORTED_REASON))
    return found


def _configuration_case_disposition(
    call: int,
    covered_subjects: list[str],
    positive_branches: list[list[str]],
    required_negative: list[str],
) -> str:
    """Classify a whole-condition case by sign and compared defining tissue.

    This is not the rule for an isolated normal tissue finding. The negative
    case already carries an independently established whole-condition call;
    recall must compare relevant tissue but need not re-establish every site.
    Trust, provenance and contradictory findings are checked by the caller.
    """
    defining_subjects = set(required_negative)
    for branch in positive_branches:
        defining_subjects.update(branch)
    covered = set(covered_subjects) & defining_subjects
    if call == 1:
        if any(branch and set(branch) <= covered for branch in positive_branches):
            return "positive_configuration"
        return "positive_coverage_incomplete"
    if call == -1:
        if covered:
            return "negative_configuration"
        return "context_only"
    return "invalid_call"


# ---------------------------------------------------------------------------
# public combination
# ---------------------------------------------------------------------------


def _configuration_decision(
    contract: ConditionContract,
    decision: dict,
    readings: dict,
    joint: dict | None,
    joint_records: list[dict[str, Any]],
) -> tuple[dict, dict[str, Any]]:
    """Let covered, independently taught configuration cases speak.

    Each decisive sign needs case-level common-bank provenance for the
    condition's own declared roles. Warranted whole-normal recall may decide
    without separate normal findings at every alternative site (Rohan,
    2026-10-22). Opposing whole-condition calls remain a conflict even when
    their compared roles differ. A clean necessary negative remains decisive,
    and contradictions with anatomical readings stay visible.
    """
    coverage: dict[str, Any] = {
        "status": "not_present",
        "eligible_case_ids": {"positive": [], "negative": []},
        "excluded_cases": [],
        "competing_anatomical_counterevidence": [],
    }
    if joint is None:
        return decision, coverage
    if any(readings[name]["state"] == _NEGATIVE for name in contract.necessary):
        coverage["status"] = "necessary_negative_blocks_configuration"
        return decision, coverage
    diagnostic = [name for name in (*contract.necessary, *contract.alternatives)]
    eligible_signs: set[str] = set()
    eligible_ids: dict[str, set[str]] = {"positive": set(), "negative": set()}
    positive_covered_by_case: dict[str, set[str]] = {}
    grade_only_seen = False
    subjects = set(diagnostic)

    def covered_subjects(row: Mapping[str, Any]) -> set[str] | None:
        banks = row.get("common_speaking_banks")
        if not isinstance(banks, list) or any(
            not isinstance(bank, str) for bank in banks
        ):
            return None
        return {
            subject
            for subject in subjects
            if any(
                bank.startswith(f"object/{subject}/")
                and len(bank) > len(f"object/{subject}/")
                for bank in banks
            )
        }

    positive_branches = (
        [set(branch) for branch in contract.sufficient]
        if contract.sufficient
        else (
            [set(contract.necessary)]
            if contract.necessary
            else [{name} for name in contract.alternatives]
        )
    )
    negative_required = set(contract.alternatives or contract.necessary)
    if contract.necessary and contract.alternatives:
        negative_required.update(contract.necessary)

    for record in joint_records:
        if record.get("decision_scope") == "grade_only":
            grade_only_seen = True
            for row in record.get("case_terms", []):
                case_id = row.get("case_id") if isinstance(row, Mapping) else None
                call = row.get("call") if isinstance(row, Mapping) else None
                if isinstance(case_id, str) and call in _SIGNS:
                    coverage["excluded_cases"].append(
                        {
                            "case_id": case_id,
                            "call": call,
                            "reason": "query_decision_scope_grade_only",
                        }
                    )
            continue
        vetoed = set(record.get("vetoed_answers", []))
        for row in record.get("case_terms", []):
            call = row.get("call") if isinstance(row, Mapping) else None
            case_id = row.get("case_id") if isinstance(row, Mapping) else None
            if call not in (-1, 1) or call in vetoed:
                continue
            declared_signs = _REQUIRED_SIGNS.get(record.get("outcome"), frozenset())
            if call not in declared_signs:
                if isinstance(case_id, str):
                    coverage["excluded_cases"].append(
                        {
                            "case_id": case_id,
                            "call": call,
                            "reason": "record_does_not_declare_speaking_sign",
                        }
                    )
                continue
            if not isinstance(row, Mapping) or row.get("reaches_trust") is not True:
                if isinstance(case_id, str):
                    coverage["excluded_cases"].append(
                        {
                            "case_id": case_id,
                            "call": call,
                            "reason": "case_not_warranted",
                        }
                    )
                continue
            covered = covered_subjects(row)
            if covered is None:
                if isinstance(case_id, str):
                    coverage["excluded_cases"].append(
                        {
                            "case_id": case_id,
                            "call": call,
                            "reason": "common_bank_provenance_unavailable",
                        }
                    )
                continue
            disposition = _configuration_case_disposition(
                call,
                sorted(covered),
                [sorted(branch) for branch in positive_branches],
                sorted(negative_required),
            )
            if disposition in {"positive_configuration", "negative_configuration"}:
                label = (
                    "positive"
                    if disposition == "positive_configuration"
                    else "negative"
                )
                eligible_signs.add(label)
                if isinstance(case_id, str):
                    eligible_ids[label].add(case_id)
                    if call == 1:
                        positive_covered_by_case.setdefault(case_id, set()).update(
                            covered
                        )
            elif isinstance(case_id, str):
                excluded: dict[str, Any] = {
                    "case_id": case_id,
                    "call": call,
                    "reason": "defining_tissue_coverage_incomplete",
                    "covered_subjects": sorted(covered),
                    "case_coverage_disposition": disposition,
                }
                coverage["excluded_cases"].append(excluded)

    coverage["eligible_case_ids"] = {
        label: sorted(values) for label, values in eligible_ids.items()
    }
    positive_subjects = sorted(
        set().union(*positive_covered_by_case.values())
        if positive_covered_by_case
        else set()
    )
    normal_subjects = {
        name for name in diagnostic if readings[name]["state"] == _NEGATIVE
    }
    anatomical_overlap = sorted(set(positive_subjects) & normal_subjects)
    coverage["competing_anatomical_counterevidence"] = anatomical_overlap
    coverage["required_positive_branches"] = [
        sorted(branch) for branch in positive_branches
    ]
    coverage["negative_defining_subjects"] = sorted(negative_required)
    coverage["negative_coverage_rule"] = "warranted_configuration_with_defining_tissue"
    if not eligible_signs:
        coverage["status"] = (
            "query_grade_only"
            if grade_only_seen
            else "no_covered_warranted_configuration_cases"
        )
        if decision["outcome"] == _OPEN and joint["state"] in (_POSITIVE, _NEGATIVE):
            return (
                _decision(
                    _OPEN,
                    "configuration_defining_tissue_coverage_missing",
                    unresolved=diagnostic,
                ),
                coverage,
            )
        return decision, coverage
    state = (
        _CONFLICT
        if len(eligible_signs) > 1
        else _POSITIVE
        if "positive" in eligible_signs
        else _NEGATIVE
    )
    coverage["status"] = "covered_warranted_cases"
    coverage["state"] = state
    conflicted = any(readings[name]["state"] == _CONFLICT for name in diagnostic)
    opposing = (state == _POSITIVE and decision["outcome"] == _DEFEATED) or (
        state == _NEGATIVE
        and any(readings[name]["state"] == _POSITIVE for name in diagnostic)
    )
    if state == _CONFLICT or conflicted or opposing:
        return _decision(
            _OPEN, "configuration_anatomy_conflict", unresolved=diagnostic
        ), coverage
    if state == _POSITIVE and decision["outcome"] == _OPEN and anatomical_overlap:
        return _decision(
            _OPEN,
            "configuration_anatomy_counterevidence",
            unresolved=diagnostic,
        ), coverage
    if state == _POSITIVE and decision["outcome"] == _ASSIGNED:
        return decision, coverage
    return (
        _decision(
            _ASSIGNED if state == _POSITIVE else _DEFEATED,
            "warranted_condition_configuration",
            decided_by=[JOINT_PREFIX + contract.question],
        ),
        coverage,
    )


def combine_condition(question: str, object_evidence: dict) -> dict:
    """Combine per-object recall evidence for one condition.

    ``object_evidence`` maps canonical object subjects to ``recall_object``
    results (a mapping, or a list of mappings for several recalls of the same
    object). Absent subjects are unobserved, never normal. The result carries
    ``outcome`` (assigned/defeated/open), ``reason``, ``evidence``,
    ``observation_requests``, the validated ``recall_evidence`` that grades the
    finding, and its ``probability``/``rank`` from :func:`rank_condition`.
    """
    contract = contract_for(question)
    if not isinstance(object_evidence, Mapping):
        raise ContractError("object_evidence_not_object")
    joint_key = JOINT_PREFIX + contract.question

    readings: dict[str, dict[str, Any]] = {}
    graded: dict[str, list[dict[str, Any]]] = {}
    for role, subjects in (
        ("necessary", contract.necessary),
        ("alternative", contract.alternatives),
        ("supporting", contract.supporting),
    ):
        for subject in subjects:
            reading, kept = _read_subject(
                object_evidence.get(subject),
                (subject, f"object/{subject}"),
                study_positive_is_context=(
                    role == "alternative"
                    and contract.question in {"Fracture", "Contusion"}
                ),
            )
            reading["role"] = role
            readings[subject] = reading
            if kept and role != "supporting":
                graded[subject] = kept

    joint_voice: dict[str, Any] | None = None
    joint_records: list[dict[str, Any]] = []
    if joint_key in object_evidence:
        joint_voice, kept = _read_subject(object_evidence[joint_key], (joint_key,))
        joint_voice["role"] = "joint"
        joint_records = kept
        if kept:
            graded[joint_key] = kept

    declared = {*contract.subjects, joint_key}
    ignored = sorted(str(key) for key in object_evidence if key not in declared)
    decision = _COMBINERS[contract.question](readings)
    decision, configuration_coverage = _configuration_decision(
        contract, decision, readings, joint_voice, joint_records
    )
    requests = _requests(contract.question, readings, decision)

    supporting_summary: dict[str, list[str]] = {
        _POSITIVE: [],
        _NEGATIVE: [],
        _UNKNOWN: [],
        _CONFLICT: [],
    }
    for subject in contract.supporting:
        supporting_summary[readings[subject]["state"]].append(subject)

    finding: dict[str, Any] = {
        "schema": FINDING_SCHEMA,
        "question": contract.question,
        "contract_id": contract.contract_id,
        "policy_id": POLICY_ID,
        "outcome": decision["outcome"],
        "reason": decision["reason"],
        "evidence": {
            "contract_id": contract.contract_id,
            "kind": contract.kind,
            "sources": contract.source_declaration(),
            "necessary": list(contract.necessary),
            "sufficient": [list(config) for config in contract.sufficient],
            "sufficiency_sourced": contract.sufficiency_sourced,
            "alternatives": list(contract.alternatives),
            "supporting": list(contract.supporting),
            "readings": readings,
            "joint_voice": joint_voice,
            "joint_configuration_coverage": configuration_coverage,
            "decided_by": decision["decided_by"],
            "unresolved_subjects": decision["unresolved"],
            "unsupported_positive_subjects": decision["unsupported"],
            "supporting_context": supporting_summary,
            "ignored_subjects": ignored,
            "unmeasured_source_predicates": list(contract.unmeasured_source_predicates),
            "limits": list(contract.limits),
        },
        "observation_requests": requests,
        "recall_evidence": graded,
    }
    rank = rank_condition(finding)
    finding["rank"] = rank
    finding["probability"] = rank["value"]
    return finding


# ---------------------------------------------------------------------------
# continuous rank
# ---------------------------------------------------------------------------


def _fraction_record(value: Fraction) -> dict[str, str]:
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def _iter_records(raw: object, rejected: list[dict[str, Any]]):
    """Yield (subject hint, record) pairs from a list, a record or a mapping."""
    if raw is None:
        return []
    if isinstance(raw, Mapping):
        if "outcome" in raw or "case_terms" in raw:
            return [("", raw)]
        pairs: list[tuple[str, object]] = []
        for key, value in raw.items():
            hint = key if isinstance(key, str) else str(key)
            if isinstance(value, (list, tuple)):
                pairs.extend((hint, item) for item in value)
            else:
                pairs.append((hint, value))
        return pairs
    if isinstance(raw, (list, tuple)):
        return [("", item) for item in raw]
    rejected.append({"subject": "", "code": "recall_evidence_not_list_or_object"})
    return []


def _record_terms(
    hint: str,
    record: object,
    terms: list[tuple[str, str, int, Fraction]],
    vetoed_excluded: list[dict[str, str]],
    rejected: list[dict[str, Any]],
) -> None:
    """Append one record's eligible signed squared cosines (tolerant, recorded)."""
    named = record.get("subject") if isinstance(record, Mapping) else None
    subject = hint or (named if isinstance(named, str) else "")
    if not isinstance(record, Mapping):
        rejected.append({"subject": subject, "code": "record_not_object"})
        return
    vetoes = record.get("vetoed_answers", [])
    if not _sign_list_ok(vetoes, unique=True):
        rejected.append({"subject": subject, "code": "vetoed_answers_invalid"})
        return
    ineligible: set[str] = set()
    for field in _INELIGIBLE_FIELDS:
        values = record.get(field, [])
        if not _id_list_ok(values):
            rejected.append({"subject": subject, "code": f"{field}_invalid"})
            return
        ineligible.update(values)
    rows = record.get("case_terms", [])
    if not isinstance(rows, list):
        rejected.append({"subject": subject, "code": "case_terms_not_list"})
        return
    seen: set[str] = set()
    for index, row in enumerate(rows):
        normalized, _, code = _check_row(row, None, seen, ineligible)
        if code is not None or normalized is None:
            rejected.append({"subject": subject, "index": index, "code": code})
            continue
        if normalized["call"] in vetoes:
            vetoed_excluded.append(
                {"subject": subject, "case_id": normalized["case_id"]}
            )
            continue
        raw_terms = normalized["terms"]
        similarity = Fraction(
            raw_terms["dot"] * raw_terms["dot"],
            raw_terms["left_norm_sq"] * raw_terms["right_norm_sq"],
        )
        terms.append((subject, normalized["case_id"], normalized["call"], similarity))


def rank_condition(finding: dict) -> dict:
    """Serialize a finding as ``p = (3*r + 1 + e) / 9`` with exact retention.

    ``r`` is 0/1/2 for defeated/open/assigned. ``e = (1 + s_plus - s_minus)/2``
    uses the best eligible exact squared cosine per sign over every supplied
    recall record (a vetoed sign has no support; ties keep every case id;
    several weak voices are never added or averaged). No evidence gives
    ``e = 1/2``. The grade only orders findings inside their tier: a decisive
    negative cannot be lifted by partial positives, and no value is 0 or 1.
    Malformed case rows are excluded and reported in ``rejected_terms``.
    """
    if not isinstance(finding, Mapping):
        raise ContractError("finding_not_object")
    outcome = finding.get("outcome")
    if not isinstance(outcome, str) or outcome not in _TIER:
        raise ContractError("finding_outcome_invalid")
    tier = _TIER[outcome]

    rejected: list[dict[str, Any]] = []
    terms: list[tuple[str, str, int, Fraction]] = []
    vetoed_excluded: list[dict[str, str]] = []
    for hint, record in _iter_records(finding.get("recall_evidence"), rejected):
        _record_terms(hint, record, terms, vetoed_excluded, rejected)

    support: dict[int, tuple[Fraction, list[dict[str, str]], bool]] = {}
    for sign in _SIGNS:
        matching = [item for item in terms if item[2] == sign]
        if matching:
            best = max(item[3] for item in matching)
            sources = sorted(
                {(item[0], item[1]) for item in matching if item[3] == best}
            )
            support[sign] = (
                best,
                [{"subject": s, "case_id": c} for s, c in sources],
                True,
            )
        else:
            support[sign] = (Fraction(0), [], False)
    s_plus, plus_sources, plus_available = support[1]
    s_minus, minus_sources, minus_available = support[-1]
    grade = (Fraction(1) + s_plus - s_minus) / 2
    exact = (Fraction(3 * tier + 1) + grade) / 9

    if not plus_available and not minus_available:
        reason = "no_eligible_signed_support_neutral"
    elif plus_available and not minus_available:
        reason = "positive_support_only"
    elif minus_available and not plus_available:
        reason = "negative_support_only"
    else:
        reason = "both_signs_compared"

    return {
        "value": float(exact),
        "policy_id": POLICY_ID,
        "exact": _fraction_record(exact),
        "formula": "p=(3*r+1+e)/9",
        "tier": outcome,
        "r": tier,
        "e": _fraction_record(grade),
        "s_plus": {**_fraction_record(s_plus), "available": plus_available},
        "s_minus": {**_fraction_record(s_minus), "available": minus_available},
        "reason": reason,
        "positive_case_ids": sorted({item["case_id"] for item in plus_sources}),
        "negative_case_ids": sorted({item["case_id"] for item in minus_sources}),
        "positive_sources": plus_sources,
        "negative_sources": minus_sources,
        "eligible_term_count": len(terms),
        "vetoed_excluded": vetoed_excluded,
        "rejected_terms": rejected,
    }
