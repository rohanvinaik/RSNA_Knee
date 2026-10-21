"""Direct-call intent tests for the squint-first condition contracts.

Rohan's words behind these tests (2026-10-21): the squint decides from
located anatomy and individual cases; unknown is not normal ("orthogonal
signal, lacking in significance" is its own state, never a silent healthy
default); a cleanly negative part of a multi-part diagnosis suppresses the
label whatever ambiguous partial signal surrounds it; ambiguity is carried as
a directionally valid cosine grade, not as a hidden decision.

Every test calls ``combine_condition`` / ``rank_condition`` directly on
hand-built evidence in the public ``recall`` row convention (``case_terms`` rows
with ``case_id``, ``call``, ``terms = {dot, left_norm_sq, right_norm_sq}``).
Both signs of every decision are pinned: the reading that assigns and the
reading that defeats, the unknown that does neither, and the conflict that
stays a conflict. Expected grades are recomputed here from exact fractions.
"""

from __future__ import annotations

import copy
import itertools
from fractions import Fraction

import pytest

from knee.diagnosis import squint_contracts
from knee.diagnosis.declarations import QUESTIONS
from knee.diagnosis.squint_contracts import (
    CONTRACTS,
    POLICY_ID,
    QUESTION_IDS,
    SOURCES,
    ContractError,
    combine_condition,
    contract_for,
    rank_condition,
)
from knee.study.tables import LABELS

TIER = {"defeated": 0, "open": 1, "assigned": 2}
INTERVAL = {
    "defeated": (Fraction(1, 9), Fraction(2, 9)),
    "open": (Fraction(4, 9), Fraction(5, 9)),
    "assigned": (Fraction(7, 9), Fraction(8, 9)),
}
REQUEST_KINDS = {
    "locate_object_region",
    "profile_object_window",
    "bounded_zoom",
    "repeat_object_recall",
}


# ---------------------------------------------------------------------------
# builders
# ---------------------------------------------------------------------------


def _term_row(
    case_id: str,
    call: int,
    dot: int,
    left: int,
    right: int | None = None,
    *,
    trust: str = "unchecked",
) -> dict:
    row = {
        "case_id": case_id,
        "call": call,
        "terms": {
            "dot": dot,
            "left_norm_sq": left,
            "right_norm_sq": left if right is None else right,
        },
        "common_speaking_banks": ["bank"],
    }
    if trust == "trusted":
        row["trust"] = {"numerator": 1, "denominator": 2, "source": "sourced-file"}
        row["reaches_trust"] = True
    elif trust == "untrusted":
        row["trust"] = None
        row["reaches_trust"] = None
    return row


def _ratio(case_id: str, call: int, k: int, m: int, **kwargs: str) -> dict:
    """A row whose squared cosine is exactly (k/m)**2."""
    return _term_row(case_id, call, k, m, m, **kwargs)


def _sq(k: int, m: int) -> Fraction:
    return Fraction(k * k, m * m)


def _rec(outcome: str, rows=(), *, vetoed=(), **extra) -> dict:
    record = {
        "outcome": outcome,
        "case_terms": [copy.deepcopy(row) for row in rows],
        "vetoed_answers": list(vetoed),
    }
    record.update(extra)
    return record


def _present(rows=()) -> dict:
    return _rec("present", rows)


def _absent(rows=()) -> dict:
    return _rec("absent", rows)


def _missing(rows=()) -> dict:
    return _rec("unresolved_missing_reading", rows)


def _conflict(rows=()) -> dict:
    return _rec("unresolved_conflict", rows)


def _proposal(rows=()) -> dict:
    return _rec("proposal", rows)


FACTORIES = {
    "present": _present,
    "absent": _absent,
    "missing": _missing,
    "conflict": _conflict,
}


def _fraction(record: dict) -> Fraction:
    return Fraction(int(record["numerator"]), int(record["denominator"]))


def _record(value: Fraction) -> dict:
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def _tier_value(tier: str, grade: Fraction) -> Fraction:
    return (Fraction(3 * TIER[tier] + 1) + grade) / 9


SINGLE_TISSUE = [
    ("ACL", "acl", ("femur", "tibia", "pcl")),
    ("MCL", "mcl", ("medial_meniscus", "femur", "tibia")),
    ("Medial Meniscus", "medial_meniscus", ("femur", "tibia", "joint")),
    ("Lateral Meniscus", "lateral_meniscus", ("femur", "tibia", "joint")),
    (
        "Synovitis",
        "synovium",
        ("joint_fluid", "joint", "anterior_synovial_recess", "joint_capsule"),
    ),
    (
        "Baker's",
        "gastrocnemius_semimembranosus_bursa",
        ("medial_gastrocnemius", "semimembranosus", "joint_capsule", "joint"),
    ),
]
SOURCED_ALTERNATIVES = [
    ("Fracture", ("femur", "tibia", "patella", "fibula")),
    ("Contusion", ("femur", "tibia", "patella")),
    ("Effusion", ("joint_fluid", "anterior_synovial_recess")),
]
OSTEOARTHRITIS = [
    (
        "Medial OA",
        ("femur", "tibia", "femoral_cartilage", "tibial_cartilage", "medial_meniscus"),
        ("joint",),
        "lateral_meniscus",
    ),
    (
        "Lateral OA",
        ("femur", "tibia", "femoral_cartilage", "tibial_cartilage", "lateral_meniscus"),
        ("joint",),
        "medial_meniscus",
    ),
    (
        "PF OA",
        ("patella", "femur", "patellar_cartilage", "trochlear_cartilage"),
        (),
        "tibia",
    ),
]


# ---------------------------------------------------------------------------
# declarations: twelve plain contracts with distinct roles and literal sources
# ---------------------------------------------------------------------------


def test_twelve_contracts_cover_exactly_the_official_questions() -> None:
    assert len(QUESTION_IDS) == len(CONTRACTS) == 12
    assert set(QUESTION_IDS) == set(LABELS)
    assert tuple(contract.question for contract in CONTRACTS) == QUESTION_IDS
    assert tuple(question.question_id for question in QUESTIONS) == QUESTION_IDS
    for contract in CONTRACTS:
        assert contract_for(contract.question) is contract


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.question)
def test_roles_are_distinct_and_inside_the_declared_question_objects(
    contract,
) -> None:
    flat = [
        subject
        for role in (contract.necessary, contract.alternatives, contract.supporting)
        for subject in role
    ]
    assert len(flat) == len(set(flat))  # no object plays two roles
    declared = next(
        question for question in QUESTIONS if question.question_id == contract.question
    )
    assert set(flat) <= set(declared.objects)
    for configuration in contract.sufficient:
        assert configuration
        assert set(configuration) <= set(contract.necessary) | set(
            contract.alternatives
        )
    if contract.kind == "single_tissue":
        assert len(contract.necessary) == 1
        assert not contract.alternatives
        assert contract.sufficient == ((contract.necessary[0],),)
    else:
        assert contract.kind == "alternative_branches"
        assert not contract.necessary
        assert contract.alternatives


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.question)
def test_every_contract_declares_literal_sources(contract) -> None:
    assert contract.statements
    assert contract.source_keys
    for key in contract.source_keys:
        assert SOURCES[key].strip()
    for entry in contract.source_declaration():
        assert entry["statement"].strip()
        assert entry["citations"]
    assert contract.contract_id.startswith("knee.squint-contract/")


def test_declared_roles_match_the_anatomical_contracts() -> None:
    for question, primary, context in SINGLE_TISSUE:
        contract = contract_for(question)
        assert contract.necessary == (primary,)
        assert contract.supporting == context
    for question, branches in SOURCED_ALTERNATIVES:
        contract = contract_for(question)
        assert contract.alternatives == branches
        assert contract.sufficient == tuple((branch,) for branch in branches)
    for question, branches, context, _ in OSTEOARTHRITIS:
        contract = contract_for(question)
        assert contract.alternatives == branches
        assert contract.supporting == context


def test_only_the_three_oa_contracts_lack_a_sourced_sufficient_configuration() -> None:
    unsourced = {c.question for c in CONTRACTS if not c.sufficiency_sourced}
    assert unsourced == {"Medial OA", "Lateral OA", "PF OA"}


def test_bakers_discloses_the_unmeasured_communication_predicate() -> None:
    contract = contract_for("Baker's")
    assert contract.unmeasured_source_predicates == ("communicates_with_knee_joint",)
    finding = combine_condition(
        "Baker's", {"gastrocnemius_semimembranosus_bursa": _present()}
    )
    assert finding["outcome"] == "assigned"
    assert finding["evidence"]["unmeasured_source_predicates"] == [
        "communicates_with_knee_joint"
    ]


def test_unknown_question_and_misuse_raise_named_errors() -> None:
    for bad in ("Torn ACL", "acl", "", "Medial  OA"):
        with pytest.raises(ContractError) as caught:
            combine_condition(bad, {})
        assert caught.value.code == "question_unknown"
        with pytest.raises(ContractError):
            contract_for(bad)
    for bad in (None, 7, ["ACL"]):
        with pytest.raises(ContractError) as caught:
            combine_condition(bad, {})  # type: ignore[arg-type]
        assert caught.value.code == "question_not_text"
    for bad in (None, [], "acl", 7):
        with pytest.raises(ContractError) as caught:
            combine_condition("ACL", bad)  # type: ignore[arg-type]
        assert caught.value.code == "object_evidence_not_object"
    for bad in (None, "finding", 7, []):
        with pytest.raises(ContractError) as caught:
            rank_condition(bad)  # type: ignore[arg-type]
        assert caught.value.code == "finding_not_object"
    for bad in ({}, {"outcome": "maybe"}, {"outcome": None}, {"outcome": 1}):
        with pytest.raises(ContractError) as caught:
            rank_condition(bad)
        assert caught.value.code == "finding_outcome_invalid"


def test_public_surface_is_declared() -> None:
    for name in (
        "combine_condition",
        "rank_condition",
        "CONTRACTS",
        "POLICY_ID",
        "SOURCES",
    ):
        assert name in squint_contracts.__all__
    assert isinstance(POLICY_ID, str) and POLICY_ID.strip()


# ---------------------------------------------------------------------------
# single-tissue conditions: the warranted reading of its own tissue speaks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("question", "primary", "context"), SINGLE_TISSUE)
def test_single_tissue_reading_speaks_for_its_condition_both_signs(
    question: str, primary: str, context: tuple
) -> None:
    assigned = combine_condition(question, {primary: _present()})
    defeated = combine_condition(question, {primary: _absent()})

    assert assigned["outcome"] == "assigned"
    assert assigned["reason"] == f"{primary}_warranted_positive"
    assert assigned["evidence"]["decided_by"] == [primary]
    assert defeated["outcome"] == "defeated"
    assert defeated["reason"] == f"{primary}_warranted_negative"
    assert defeated["evidence"]["decided_by"] == [primary]
    assert assigned["observation_requests"] == []
    assert defeated["observation_requests"] == []


@pytest.mark.parametrize(("question", "primary", "context"), SINGLE_TISSUE)
def test_context_tissue_is_not_a_required_finding_and_never_decides(
    question: str, primary: str, context: tuple
) -> None:
    normal_context = {name: _absent() for name in context}
    positive_context = {name: _present() for name in context}

    # a positive presentation does not claim every context tissue is injured
    assert (
        combine_condition(question, {primary: _present(), **normal_context})["outcome"]
        == "assigned"
    )
    # a decisive negative stands regardless of any partial positive
    defeated = combine_condition(question, {primary: _absent(), **positive_context})
    assert defeated["outcome"] == "defeated"
    assert defeated["rank"]["value"] <= float(INTERVAL["defeated"][1])
    # context alone neither assigns nor defeats
    for context_state in (normal_context, positive_context, {}):
        result = combine_condition(question, dict(context_state))
        assert result["outcome"] == "open"
        assert result["evidence"]["readings"][primary]["code"] == "not_observed"
    for unresolved in (_missing(), _conflict(), _proposal()):
        for context_state in (normal_context, positive_context):
            result = combine_condition(
                question, {primary: copy.deepcopy(unresolved), **context_state}
            )
            assert result["outcome"] == "open"


@pytest.mark.parametrize(("question", "primary", "context"), SINGLE_TISSUE)
def test_single_tissue_truth_table(question: str, primary: str, context: tuple) -> None:
    expected = {"present": "assigned", "absent": "defeated"}
    for primary_state, primary_factory in FACTORIES.items():
        for context_states in itertools.product(FACTORIES, repeat=len(context)):
            evidence = {primary: primary_factory()}
            for name, state in zip(context, context_states, strict=True):
                evidence[name] = FACTORIES[state]()
            result = combine_condition(question, evidence)
            assert result["outcome"] == expected.get(primary_state, "open")


@pytest.mark.parametrize(("question", "primary", "context"), SINGLE_TISSUE)
def test_conflicting_assignments_remain_a_conflict(
    question: str, primary: str, context: tuple
) -> None:
    result = combine_condition(question, {primary: _conflict()})
    assert result["outcome"] == "open"
    assert result["evidence"]["readings"][primary]["state"] == "conflict"
    assert "conflict" in result["reason"]
    assert [item["kind"] for item in result["observation_requests"]] == ["bounded_zoom"]
    # opposing recalls of one object are a conflict, not an average
    both = combine_condition(question, {primary: [_present(), _absent()]})
    assert both["outcome"] == "open"
    assert both["evidence"]["readings"][primary]["state"] == "conflict"
    # an unknown record never cancels a warranted one, in either direction
    assert (
        combine_condition(question, {primary: [_present(), _missing()]})["outcome"]
        == "assigned"
    )
    assert (
        combine_condition(question, {primary: [_absent(), _missing()]})["outcome"]
        == "defeated"
    )


# ---------------------------------------------------------------------------
# unknown is not negative
# ---------------------------------------------------------------------------

UNKNOWN_RECORDS = [
    (lambda: _missing(), "missing_reading", "profile_object_window", False),
    (
        lambda: _rec("unresolved_no_precedent"),
        "no_precedent",
        "profile_object_window",
        False,
    ),
    (
        lambda: _rec("incompatible_encoding"),
        "incompatible_encoding",
        "profile_object_window",
        False,
    ),
    (
        lambda: _rec("unresolved_censored"),
        "censored_by_near_miss_veto",
        "bounded_zoom",
        True,
    ),
    (lambda: _proposal(), "proposal_without_sourced_trust", "bounded_zoom", True),
    (
        lambda: _rec("invalid_input", reason="rejected"),
        "recall_rejected_input",
        "repeat_object_recall",
        False,
    ),
]


@pytest.mark.parametrize(
    ("make", "code", "kind", "discretionary"),
    UNKNOWN_RECORDS,
    ids=[item[1] for item in UNKNOWN_RECORDS],
)
def test_unknown_readings_are_open_never_negative(
    make, code: str, kind: str, discretionary: bool
) -> None:
    unknown = combine_condition("ACL", {"acl": make()})
    negative = combine_condition("ACL", {"acl": _absent()})

    assert unknown["outcome"] == "open"
    assert negative["outcome"] == "defeated"
    assert unknown["evidence"]["readings"]["acl"]["state"] == "unknown"
    assert unknown["evidence"]["readings"]["acl"]["code"] == code
    assert negative["evidence"]["readings"]["acl"]["state"] == "negative"
    assert unknown["reason"] == f"acl_unknown:{code}"
    (request,) = unknown["observation_requests"]
    assert request["kind"] == kind
    assert request["discretionary"] is discretionary
    # unknown stays strictly above the defeated tier and below the assigned tier
    assert negative["rank"]["value"] < unknown["rank"]["value"]
    assigned = combine_condition("ACL", {"acl": _present()})
    assert unknown["rank"]["value"] < assigned["rank"]["value"]


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.question)
def test_no_evidence_is_open_with_a_bounded_request_per_deciding_object(
    contract,
) -> None:
    result = combine_condition(contract.question, {})
    assert result["outcome"] == "open"
    deciding = [*contract.necessary, *contract.alternatives]
    assert [item["subject"] for item in result["observation_requests"]] == deciding
    assert {item["kind"] for item in result["observation_requests"]} == {
        "locate_object_region"
    }
    assert result["rank"]["reason"] == "no_eligible_signed_support_neutral"
    assert result["probability"] == 0.5  # open tier with e = 1/2
    for subject in contract.supporting:
        assert result["evidence"]["readings"][subject]["code"] == "not_observed"


def test_a_none_value_is_unobserved_not_normal() -> None:
    result = combine_condition("ACL", {"acl": None, "femur": _absent()})
    assert result["outcome"] == "open"
    assert result["evidence"]["readings"]["acl"]["code"] == "not_observed"
    assert combine_condition("ACL", {"acl": []})["outcome"] == "open"


# ---------------------------------------------------------------------------
# proposals and unsourced warrants
# ---------------------------------------------------------------------------


def test_cases_speaking_without_sourced_trust_are_only_proposals() -> None:
    perfect = [_ratio("positive", 1, 1, 1)]
    proposal = combine_condition("ACL", {"acl": _proposal(perfect)})

    assert proposal["outcome"] == "open"
    assert proposal["evidence"]["readings"]["acl"]["code"] == (
        "proposal_without_sourced_trust"
    )
    # the perfect cosine can only grade within the open tier, up to its ceiling
    assert proposal["rank"]["exact"] == _record(Fraction(5, 9))
    assert proposal["rank"]["tier"] == "open"


def test_an_outcome_whose_cases_carry_no_sourced_trust_is_not_a_warrant() -> None:
    untrusted = combine_condition(
        "ACL", {"acl": _present([_ratio("p", 1, 1, 2, trust="untrusted")])}
    )
    trusted = combine_condition(
        "ACL", {"acl": _present([_ratio("p", 1, 1, 2, trust="trusted")])}
    )
    assert untrusted["outcome"] == "open"
    reading = untrusted["evidence"]["readings"]["acl"]
    assert reading["code"] == "speaking_without_sourced_trust"
    assert reading["trust_checked"] is True
    assert trusted["outcome"] == "assigned"
    assert trusted["evidence"]["readings"]["acl"]["trust_checked"] is True

    # the warrant must be for the sign the outcome claims
    wrong_sign = combine_condition(
        "ACL", {"acl": _absent([_ratio("p", 1, 1, 2, trust="trusted")])}
    )
    assert wrong_sign["outcome"] == "open"
    right_sign = combine_condition(
        "ACL", {"acl": _absent([_ratio("n", -1, 1, 2, trust="trusted")])}
    )
    assert right_sign["outcome"] == "defeated"

    # a conflict needs a sourced warrant on both signs
    one_sided = combine_condition(
        "ACL",
        {
            "acl": _conflict(
                [
                    _ratio("p", 1, 1, 2, trust="trusted"),
                    _ratio("n", -1, 1, 2, trust="untrusted"),
                ]
            )
        },
    )
    two_sided = combine_condition(
        "ACL",
        {
            "acl": _conflict(
                [
                    _ratio("p", 1, 1, 2, trust="trusted"),
                    _ratio("n", -1, 1, 2, trust="trusted"),
                ]
            )
        },
    )
    assert one_sided["evidence"]["readings"]["acl"]["state"] == "unknown"
    assert two_sided["evidence"]["readings"]["acl"]["state"] == "conflict"
    assert one_sided["outcome"] == two_sided["outcome"] == "open"


def test_object_subject_aliases_are_accepted_and_foreign_subjects_refused() -> None:
    for named in ("acl", "object/acl"):
        result = combine_condition("ACL", {"acl": {**_present(), "subject": named}})
        assert result["outcome"] == "assigned"
    foreign = combine_condition("ACL", {"acl": {**_present(), "subject": "femur"}})
    assert foreign["outcome"] == "open"
    assert foreign["evidence"]["readings"]["acl"]["code"] == "evidence_malformed"


# ---------------------------------------------------------------------------
# alternative branches: bones, fluid compartments, OA surfaces
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("question", "branches"), SOURCED_ALTERNATIVES)
def test_any_positive_alternative_assigns_whatever_the_others_say(
    question: str, branches: tuple
) -> None:
    for rest in (_absent, _missing, _conflict, _proposal):
        for positive in branches:
            evidence = {name: rest() for name in branches}
            evidence[positive] = _present()
            result = combine_condition(question, evidence)
            assert result["outcome"] == "assigned"
            assert result["evidence"]["decided_by"] == [positive]
            assert result["observation_requests"] == []


@pytest.mark.parametrize(("question", "branches"), SOURCED_ALTERNATIVES)
def test_one_normal_alternative_cannot_rule_out_the_condition_elsewhere(
    question: str, branches: tuple
) -> None:
    for normal in branches:
        result = combine_condition(question, {normal: _absent()})
        assert result["outcome"] == "open"
    for unresolved in (_missing(), _conflict(), _proposal(), None):
        evidence = {name: _absent() for name in branches[:-1]}
        if unresolved is not None:
            evidence[branches[-1]] = unresolved
        result = combine_condition(question, evidence)
        assert result["outcome"] == "open"
        assert [r["subject"] for r in result["observation_requests"]] == [branches[-1]]

    all_normal = combine_condition(question, {name: _absent() for name in branches})
    assert all_normal["outcome"] == "defeated"
    assert all_normal["reason"] == "all_alternatives_observed_negative"
    assert all_normal["evidence"]["decided_by"] == list(branches)
    assert all_normal["observation_requests"] == []


@pytest.mark.parametrize(("question", "branches"), SOURCED_ALTERNATIVES)
def test_alternative_truth_table(question: str, branches: tuple) -> None:
    for states in itertools.product(FACTORIES, repeat=len(branches)):
        evidence = {
            name: FACTORIES[state]()
            for name, state in zip(branches, states, strict=True)
        }
        if "present" in states:
            expected = "assigned"
        elif all(state == "absent" for state in states):
            expected = "defeated"
        else:
            expected = "open"
        assert combine_condition(question, evidence)["outcome"] == expected


def test_contusion_does_not_use_the_fibula_but_fracture_must_observe_it() -> None:
    three = {name: _absent() for name in ("femur", "tibia", "patella")}

    contusion = combine_condition("Contusion", {**three, "fibula": _present()})
    assert contusion["outcome"] == "defeated"
    assert "fibula" in contusion["evidence"]["ignored_subjects"]

    fracture = combine_condition("Fracture", three)
    assert fracture["outcome"] == "open"
    (request,) = fracture["observation_requests"]
    assert request["subject"] == "fibula"
    assert request["kind"] == "locate_object_region"
    assert combine_condition("Fracture", {**three, "fibula": _absent()})["outcome"] == (
        "defeated"
    )
    assert combine_condition("Fracture", {**three, "fibula": _present()})[
        "outcome"
    ] == ("assigned")


def test_alternative_findings_propagate_strong_kleene_logic() -> None:
    normal = {"femur": _absent(), "tibia": _absent(), "patella": _absent()}

    unknown = combine_condition("Fracture", {**normal, "fibula": _missing()})
    assert unknown["reason"] == "alternatives_unresolved:fibula"

    conflict = combine_condition("Fracture", {**normal, "fibula": _conflict()})
    assert conflict["reason"] == "conflicting_assignments:fibula"

    mixed = combine_condition(
        "Fracture",
        {
            "femur": _absent(),
            "tibia": _missing(),
            "patella": _conflict(),
            "fibula": _absent(),
        },
    )
    # conflict outranks unknown in the reason; neither is read as a value
    assert mixed["reason"] == "conflicting_assignments:patella;unresolved:tibia"
    for result in (unknown, conflict, mixed):
        assert result["outcome"] == "open"

    within_one_object = combine_condition(
        "Fracture", {**normal, "fibula": [_present(), _absent()]}
    )
    assert within_one_object["outcome"] == "open"
    assert "conflict" in within_one_object["reason"]

    # positive absorbs every other state
    absorbed = combine_condition(
        "Fracture",
        {**normal, "fibula": [_present(), _missing()], "tibia": _conflict()},
    )
    assert absorbed["outcome"] == "assigned"


def test_effusion_branches_and_supporting_context() -> None:
    assert (
        combine_condition("Effusion", {"joint_fluid": _present()})["outcome"]
        == "assigned"
    )
    recess = combine_condition(
        "Effusion", {"joint_fluid": _absent(), "anterior_synovial_recess": _present()}
    )
    assert recess["outcome"] == "assigned"
    assert recess["evidence"]["decided_by"] == ["anterior_synovial_recess"]
    assert (
        combine_condition("Effusion", {"joint_fluid": _absent()})["outcome"] == "open"
    )
    both_normal = {"joint_fluid": _absent(), "anterior_synovial_recess": _absent()}
    assert combine_condition("Effusion", both_normal)["outcome"] == "defeated"

    context = ("joint", "joint_capsule", "quadriceps_fat_pad", "prefemoral_fat_pad")
    positive_context = {name: _present() for name in context}
    normal_context = {name: _absent() for name in context}
    assert combine_condition("Effusion", positive_context)["outcome"] == "open"
    assert combine_condition("Effusion", normal_context)["outcome"] == "open"
    assert (
        combine_condition("Effusion", {**normal_context, "joint_fluid": _present()})[
            "outcome"
        ]
        == "assigned"
    )
    assert (
        combine_condition("Effusion", {**positive_context, **both_normal})["outcome"]
        == "defeated"
    )


@pytest.mark.parametrize(
    ("question", "branches", "context", "other_compartment"), OSTEOARTHRITIS
)
def test_oa_defeats_only_when_every_surface_branch_is_negative(
    question: str, branches: tuple, context: tuple, other_compartment: str
) -> None:
    normal = {name: _absent() for name in branches}
    defeated = combine_condition(question, normal)
    assert defeated["outcome"] == "defeated"
    assert defeated["evidence"]["decided_by"] == list(branches)

    for name in branches:
        one_unresolved = {**normal, name: _missing()}
        result = combine_condition(question, one_unresolved)
        assert result["outcome"] == "open"
        assert [r["subject"] for r in result["observation_requests"]] == [name]
    # context and the other compartment's tissue are never required findings
    for name in context:
        assert combine_condition(question, {**normal, name: _present()})["outcome"] == (
            "defeated"
        )
    result = combine_condition(question, {**normal, other_compartment: _present()})
    assert result["outcome"] == "defeated"
    assert other_compartment in result["evidence"]["ignored_subjects"]


@pytest.mark.parametrize(
    ("question", "branches", "context", "other_compartment"), OSTEOARTHRITIS
)
def test_oa_positive_branches_stay_open_without_a_sourced_combination(
    question: str, branches: tuple, context: tuple, other_compartment: str
) -> None:
    # "all necessary predicates hold" is not "sufficient": nothing is invented
    for positives in range(1, len(branches) + 1):
        for chosen in itertools.combinations(branches, positives):
            evidence = {
                name: _present() if name in chosen else _absent() for name in branches
            }
            result = combine_condition(question, evidence)
            assert result["outcome"] == "open"
            assert result["reason"] == (
                "unsupported_combination:sufficient_configuration_not_sourced"
            )
            assert result["evidence"]["unsupported_positive_subjects"] == list(chosen)
            assert result["evidence"]["decided_by"] == []
            requests = result["observation_requests"]
            assert [r["subject"] for r in requests] == list(chosen)
            assert {r["kind"] for r in requests} == {"bounded_zoom"}
            assert {r["reason"] for r in requests} == {
                "unsupported_combination:sufficient_configuration_not_sourced"
            }
            assert result["evidence"]["sufficiency_sourced"] is False
    # positives plus unresolved branches ask for both kinds of bounded work
    evidence = {name: _missing() for name in branches}
    evidence[branches[0]] = _present()
    result = combine_condition(question, evidence)
    kinds = {r["subject"]: r["kind"] for r in result["observation_requests"]}
    assert kinds[branches[0]] == "bounded_zoom"
    assert {k for k in kinds if k != branches[0]} == set(branches[1:])
    assert all(kinds[name] == "profile_object_window" for name in branches[1:])


@pytest.mark.parametrize(
    ("question", "branches", "context", "other_compartment"), OSTEOARTHRITIS
)
def test_oa_truth_table_never_assigns(
    question: str, branches: tuple, context: tuple, other_compartment: str
) -> None:
    for states in itertools.product(FACTORIES, repeat=len(branches)):
        evidence = {
            name: FACTORIES[state]()
            for name, state in zip(branches, states, strict=True)
        }
        expected = "defeated" if all(s == "absent" for s in states) else "open"
        assert combine_condition(question, evidence)["outcome"] == expected


def test_medial_and_lateral_oa_use_their_own_meniscus() -> None:
    surfaces = ("femur", "tibia", "femoral_cartilage", "tibial_cartilage")
    normal = {name: _absent() for name in surfaces}
    medial = combine_condition("Medial OA", {**normal, "medial_meniscus": _missing()})
    lateral = combine_condition(
        "Lateral OA", {**normal, "lateral_meniscus": _missing()}
    )
    assert medial["outcome"] == lateral["outcome"] == "open"
    assert [r["subject"] for r in medial["observation_requests"]] == ["medial_meniscus"]
    assert [r["subject"] for r in lateral["observation_requests"]] == [
        "lateral_meniscus"
    ]
    cross = combine_condition("Medial OA", {**normal, "lateral_meniscus": _missing()})
    assert [r["subject"] for r in cross["observation_requests"]] == ["medial_meniscus"]


# ---------------------------------------------------------------------------
# malformed and out-of-range evidence never decides
# ---------------------------------------------------------------------------


def _bad_terms(**overrides) -> dict:
    row = _ratio("bad", 1, 1, 2)
    row["terms"].update(overrides)
    return row


BAD_RECORDS = {
    "record_is_text": "present",
    "record_is_number": 7,
    "empty_record": {},
    "outcome_unknown": {"outcome": "bogus"},
    "outcome_bool": {"outcome": True},
    "case_terms_not_list": {"outcome": "proposal", "case_terms": {"a": 1}},
    "dot_beyond_cauchy": _proposal([_term_row("bad", 1, 3, 1, 1)]),
    "dot_beyond_cauchy_by_one": _proposal(
        [_term_row("bad", 1, 10**400 + 1, 10**400, 10**400)]
    ),
    "negative_dot": _proposal([_bad_terms(dot=-1)]),
    "bool_dot": _proposal([_bad_terms(dot=True)]),
    "fractional_dot": _proposal([_bad_terms(dot=0.5)]),
    "zero_left_norm": _proposal([_bad_terms(dot=0, left_norm_sq=0)]),
    "negative_right_norm": _proposal([_bad_terms(right_norm_sq=-4)]),
    "string_norm": _proposal([_bad_terms(left_norm_sq="2")]),
    "terms_missing": _proposal([{"case_id": "bad", "call": 1}]),
    "call_zero": _proposal([_term_row("bad", 0, 1, 2)]),
    "call_two": _proposal([_term_row("bad", 2, 1, 2)]),
    "call_bool": _proposal([_term_row("bad", True, 1, 2)]),
    "case_id_missing": _proposal(
        [{"call": 1, "terms": {"dot": 1, "left_norm_sq": 2, "right_norm_sq": 2}}]
    ),
    "duplicate_case_id": _proposal([_ratio("same", 1, 1, 2), _ratio("same", -1, 1, 3)]),
    "row_not_object": _proposal(["not-a-row"]),
    "empty_bank_list": _proposal(
        [{**_ratio("bad", 1, 1, 2), "common_speaking_banks": []}]
    ),
    "vetoed_out_of_range": _rec("proposal", vetoed=[2]),
    "vetoed_duplicate": _rec("proposal", vetoed=[1, 1]),
    "vetoed_bool": _rec("proposal", vetoed=[True]),
    "ineligible_case_has_terms": {
        "outcome": "proposal",
        "excluded_case_ids": ["x"],
        "case_terms": [_ratio("x", 1, 1, 2)],
    },
    "id_list_not_a_list": {"outcome": "present", "silent_case_ids": "x"},
    "record_for_another_object": {"outcome": "present", "subject": "femur"},
    "row_for_another_object": _proposal([{**_ratio("r", 1, 1, 2), "subject": "femur"}]),
    "speaking_calls_out_of_range": {"outcome": "present", "speaking_calls": [2]},
    "speaking_calls_disagree": {"outcome": "present", "speaking_calls": [-1]},
    "outcome_sign_is_vetoed": {"outcome": "present", "vetoed_answers": [1]},
}


@pytest.mark.parametrize("name", sorted(BAD_RECORDS))
def test_malformed_evidence_is_unknown_and_asks_for_a_new_recall(name: str) -> None:
    result = combine_condition("ACL", {"acl": copy.deepcopy(BAD_RECORDS[name])})

    assert result["outcome"] == "open"
    reading = result["evidence"]["readings"]["acl"]
    assert reading["state"] == "unknown"
    assert reading["code"] == "evidence_malformed"
    assert reading["problems"]
    (request,) = result["observation_requests"]
    assert request["kind"] == "repeat_object_recall"
    # unverifiable evidence grades nothing and is not retained as recall evidence
    assert result["recall_evidence"] == {}
    assert result["rank"]["eligible_term_count"] == 0
    assert result["rank"]["exact"] == _record(Fraction(1, 2))


def test_malformed_evidence_cannot_defeat_or_assign_an_alternative() -> None:
    normal = {name: _absent() for name in ("femur", "tibia", "patella")}
    broken = combine_condition("Fracture", {**normal, "fibula": {"outcome": "bogus"}})
    assert (
        broken["outcome"] == "open"
    )  # not defeated: the fibula is not observed negative
    assert broken["evidence"]["readings"]["fibula"]["code"] == "evidence_malformed"

    still_assigned = combine_condition(
        "Fracture", {**normal, "femur": _present(), "fibula": {"outcome": "bogus"}}
    )
    assert still_assigned["outcome"] == "assigned"  # a warranted positive absorbs
    assert still_assigned["evidence"]["readings"]["fibula"]["problems"]


def test_one_malformed_record_voids_a_subject_even_beside_a_warranted_one() -> None:
    result = combine_condition("ACL", {"acl": [_present(), {"outcome": "bogus"}]})
    assert result["outcome"] == "open"
    assert result["evidence"]["readings"]["acl"]["problems"] == ["1:outcome_invalid"]


def test_every_recall_outcome_family_is_a_named_reading() -> None:
    outcomes = {
        "present": "positive",
        "absent": "negative",
        "unresolved_conflict": "conflict",
        "proposal": "unknown",
        "unresolved_missing_reading": "unknown",
        "unresolved_censored": "unknown",
        "unresolved_no_precedent": "unknown",
        "incompatible_encoding": "unknown",
        "invalid_input": "unknown",
    }
    for outcome, state in outcomes.items():
        result = combine_condition("ACL", {"acl": _rec(outcome)})
        assert result["evidence"]["readings"]["acl"]["state"] == state
        for request in result["observation_requests"]:
            assert request["kind"] in REQUEST_KINDS


# ---------------------------------------------------------------------------
# observation requests are bounded, named and only for open findings
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.question)
def test_requests_are_bounded_existing_measurements_never_a_full_study(
    contract,
) -> None:
    results = [combine_condition(contract.question, {})]
    for state in ("missing", "conflict"):
        evidence = {
            name: FACTORIES[state]()
            for name in (*contract.necessary, *contract.alternatives)
        }
        results.append(combine_condition(contract.question, evidence))
    for result in results:
        requests = result["observation_requests"]
        assert requests
        assert len({r["request_id"] for r in requests}) == len(requests)
        for request in requests:
            assert request["kind"] in REQUEST_KINDS
            assert request["bounded"] is True
            assert request["full_study"] is False
            assert request["uses_existing_measurements"] is True
            assert request["scope"] in {"object_region", "object_window"}
            assert request["question"] == contract.question
            assert request["subject"] in contract.subjects
            assert request["request_id"].startswith(contract.question + "/")
            assert request["reason"]
            assert request["discretionary"] is (request["kind"] == "bounded_zoom")


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.question)
def test_decided_findings_carry_no_requests_and_supporting_never_asks(contract) -> None:
    for state in ("present", "absent"):
        evidence = {
            name: FACTORIES[state]()
            for name in (*contract.necessary, *contract.alternatives)
        }
        result = combine_condition(contract.question, evidence)
        if result["outcome"] != "open":
            assert result["observation_requests"] == []
    # supporting objects are never asked for, however silent they are
    result = combine_condition(contract.question, {})
    asked = {r["subject"] for r in result["observation_requests"]}
    assert asked.isdisjoint(contract.supporting)


# ---------------------------------------------------------------------------
# purity and retained provenance
# ---------------------------------------------------------------------------


def test_combination_is_pure_deterministic_and_order_independent() -> None:
    evidence = {
        "femur": _proposal([_ratio("f-pos", 1, 1, 2), _ratio("f-neg", -1, 1, 3)]),
        "tibia": _absent([_ratio("t-neg", -1, 1, 2, trust="trusted")]),
        "patella": _conflict(),
        "fibula": None,
        "unrelated": _present(),
    }
    before = copy.deepcopy(evidence)

    first = combine_condition("Fracture", evidence)
    assert evidence == before
    assert combine_condition("Fracture", evidence) == first
    reordered = dict(reversed(list(evidence.items())))
    assert combine_condition("Fracture", reordered) == first

    first["recall_evidence"]["femur"][0]["case_terms"].clear()
    first["evidence"]["readings"]["femur"]["problems"].append("scribble")
    assert evidence == before
    assert combine_condition("Fracture", evidence)["recall_evidence"]["femur"][0][
        "case_terms"
    ]


def test_findings_hold_only_json_values_and_name_policy_and_contract() -> None:
    def check(value: object) -> None:
        if isinstance(value, dict):
            assert all(isinstance(key, str) for key in value)
            for item in value.values():
                check(item)
        elif isinstance(value, list):
            for item in value:
                check(item)
        else:
            assert value is None or type(value) in (bool, int, float, str)

    for contract in CONTRACTS:
        evidence = {
            name: _present([_ratio("p", 1, 1, 2)]) for name in contract.subjects
        }
        finding = combine_condition(contract.question, evidence)
        check(finding)
        assert finding["policy_id"] == POLICY_ID
        assert finding["contract_id"] == contract.contract_id
        assert finding["question"] == contract.question
        assert finding["schema"] == "knee.squint-condition-finding/v1"


def test_ignored_subjects_are_reported_not_used() -> None:
    result = combine_condition(
        "ACL", {"acl": _present(), "banana": _present(), 7: _present()}
    )
    assert result["outcome"] == "assigned"
    assert result["evidence"]["ignored_subjects"] == ["7", "banana"]


def test_source_case_ids_are_retained_with_the_deciding_evidence() -> None:
    result = combine_condition(
        "ACL",
        {
            "acl": _present(
                [
                    _ratio("case-a", 1, 1, 2, trust="trusted"),
                    _ratio("case-b", -1, 1, 3),
                ]
            )
        },
    )
    kept = result["recall_evidence"]["acl"][0]
    assert [row["case_id"] for row in kept["case_terms"]] == ["case-a", "case-b"]
    assert result["rank"]["positive_sources"] == [
        {"subject": "acl", "case_id": "case-a"}
    ]
    assert result["rank"]["negative_sources"] == [
        {"subject": "acl", "case_id": "case-b"}
    ]


# ---------------------------------------------------------------------------
# rank: p = (3*r + 1 + e) / 9
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("tier", "expected"),
    [
        ("defeated", Fraction(1, 6)),
        ("open", Fraction(1, 2)),
        ("assigned", Fraction(5, 6)),
    ],
)
def test_no_evidence_is_the_neutral_grade_inside_each_tier(
    tier: str, expected: Fraction
) -> None:
    for finding in (
        {"outcome": tier},
        {"outcome": tier, "recall_evidence": None},
        {"outcome": tier, "recall_evidence": []},
        {"outcome": tier, "recall_evidence": {}},
        {"outcome": tier, "recall_evidence": {"acl": []}},
        {"outcome": tier, "recall_evidence": [_rec("unresolved_missing_reading")]},
    ):
        result = rank_condition(finding)
        assert type(result["value"]) is float
        assert result["value"] == float(expected)
        assert result["exact"] == _record(expected)
        assert result["e"] == _record(Fraction(1, 2))
        assert result["policy_id"] == POLICY_ID
        assert result["reason"] == "no_eligible_signed_support_neutral"
        assert result["positive_case_ids"] == result["negative_case_ids"] == []
        assert result["s_plus"]["available"] is False
        assert result["s_minus"]["available"] is False


@pytest.mark.parametrize("tier", ["defeated", "open", "assigned"])
@pytest.mark.parametrize(
    ("positive", "negative"),
    [
        ([(1, 2)], []),
        ([], [(1, 2)]),
        ([(1, 2)], [(1, 3)]),
        ([(3, 4)], [(1, 4)]),
        ([(1, 1)], [(1, 1)]),
        ([(0, 5)], [(0, 5)]),
        ([(2, 3)], [(1, 5)]),
    ],
)
def test_rank_is_the_fixed_serialization_of_tier_and_exact_cosine_grade(
    tier: str, positive: list, negative: list
) -> None:
    rows = [_ratio(f"p{i}", 1, k, m) for i, (k, m) in enumerate(positive)] + [
        _ratio(f"n{i}", -1, k, m) for i, (k, m) in enumerate(negative)
    ]
    s_plus = max((_sq(k, m) for k, m in positive), default=Fraction(0))
    s_minus = max((_sq(k, m) for k, m in negative), default=Fraction(0))
    grade = (1 + s_plus - s_minus) / 2
    expected = _tier_value(tier, grade)

    result = rank_condition({"outcome": tier, "recall_evidence": [_proposal(rows)]})

    assert result["value"] == float(expected)
    assert result["exact"] == _record(expected)
    assert result["e"] == _record(grade)
    assert _fraction(result["s_plus"]) == s_plus
    assert _fraction(result["s_minus"]) == s_minus
    assert result["s_plus"]["available"] is bool(positive)
    assert result["s_minus"]["available"] is bool(negative)
    assert result["tier"] == tier
    assert result["r"] == TIER[tier]
    assert 0.0 < result["value"] < 1.0
    low, high = INTERVAL[tier]
    assert low <= _fraction(result["exact"]) <= high


def test_squared_cosine_uses_dot_and_both_norms() -> None:
    # dot=2, |l|^2=8, |r|^2=2 -> 4/16 = 1/4, not dot**2/left or dot/right
    result = rank_condition(
        {
            "outcome": "open",
            "recall_evidence": [_proposal([_term_row("p", 1, 2, 8, 2)])],
        }
    )
    assert _fraction(result["s_plus"]) == Fraction(1, 4)
    assert result["exact"] == _record(_tier_value("open", Fraction(5, 8)))


def test_tiers_never_overlap_and_never_reach_zero_or_one() -> None:
    lowest = [_ratio("n", -1, 1, 1)]  # e = 0
    highest = [_ratio("p", 1, 1, 1)]  # e = 1
    values: dict[str, tuple[Fraction, Fraction]] = {}
    for tier in TIER:
        low = rank_condition({"outcome": tier, "recall_evidence": [_proposal(lowest)]})
        high = rank_condition(
            {"outcome": tier, "recall_evidence": [_proposal(highest)]}
        )
        assert _fraction(low["e"]) == 0
        assert _fraction(high["e"]) == 1
        assert _fraction(low["exact"]) == INTERVAL[tier][0]
        assert _fraction(high["exact"]) == INTERVAL[tier][1]
        assert 0.0 < low["value"] < high["value"] < 1.0
        values[tier] = (_fraction(low["exact"]), _fraction(high["exact"]))
    assert values["defeated"][1] < values["open"][0]
    assert values["open"][1] < values["assigned"][0]
    assert Fraction(1, 9) == values["defeated"][0]
    assert Fraction(8, 9) == values["assigned"][1]


def test_a_decisive_negative_ranks_below_every_open_and_assigned_finding() -> None:
    strongest_partial_positive = {
        "synovium": _absent([_ratio("n", -1, 1, 2)]),
        "joint_fluid": _present([_ratio("p", 1, 1, 1)]),
        "joint": _present([_ratio("p2", 1, 1, 1)]),
    }
    defeated = combine_condition("Synovitis", strongest_partial_positive)
    assert defeated["outcome"] == "defeated"
    weakest_open = combine_condition(
        "Synovitis", {"synovium": _proposal([_ratio("n", -1, 1, 1)])}
    )
    weakest_assigned = combine_condition(
        "Synovitis", {"synovium": _present([_ratio("n", -1, 1, 1)])}
    )
    assert defeated["probability"] <= float(INTERVAL["defeated"][1])
    assert defeated["probability"] < weakest_open["probability"]
    assert weakest_open["probability"] < weakest_assigned["probability"]
    # context positives and strong cosines never lift it out of its tier
    assert defeated["rank"]["tier"] == "defeated"


def test_tier_decides_before_grade_across_the_real_combination() -> None:
    defeated_best = combine_condition("ACL", {"acl": _absent([_ratio("p", 1, 1, 1)])})
    open_worst = combine_condition("ACL", {"acl": _proposal([_ratio("n", -1, 1, 1)])})
    open_best = combine_condition("ACL", {"acl": _proposal([_ratio("p", 1, 1, 1)])})
    assigned_worst = combine_condition(
        "ACL", {"acl": _present([_ratio("n", -1, 1, 1)])}
    )
    chain = [defeated_best, open_worst, open_best, assigned_worst]
    assert [item["outcome"] for item in chain] == [
        "defeated",
        "open",
        "open",
        "assigned",
    ]
    values = [item["probability"] for item in chain]
    assert values == sorted(values)
    assert len(set(values)) == 4
    assert all(0.0 < value < 1.0 for value in values)


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.question)
def test_every_contract_stays_inside_its_tier_interval(contract) -> None:
    extremes = (
        [_ratio("n", -1, 1, 1)],
        [_ratio("p", 1, 1, 1)],
        [_ratio("p", 1, 1, 1), _ratio("n", -1, 1, 1)],
        [],
    )
    for factory in FACTORIES.values():
        for rows in extremes:
            evidence = {name: factory(rows) for name in contract.subjects}
            finding = combine_condition(contract.question, evidence)
            low, high = INTERVAL[finding["outcome"]]
            exact = _fraction(finding["rank"]["exact"])
            assert low <= exact <= high
            assert 0.0 < finding["probability"] < 1.0
            assert finding["probability"] == float(exact)


def test_identical_evidence_ties_and_keeps_every_source() -> None:
    record = _proposal([_ratio("p", 1, 1, 2), _ratio("n", -1, 1, 3)])
    single = rank_condition({"outcome": "open", "recall_evidence": {"acl": record}})
    twin = rank_condition(
        {"outcome": "open", "recall_evidence": {"acl": record, "mcl": record}}
    )
    assert twin["value"] == single["value"]
    assert twin["exact"] == single["exact"]
    assert twin["positive_sources"] == [
        {"subject": "acl", "case_id": "p"},
        {"subject": "mcl", "case_id": "p"},
    ]
    assert twin["positive_case_ids"] == ["p"]
    assert single["positive_sources"] == [{"subject": "acl", "case_id": "p"}]


def test_support_is_the_best_per_sign_never_a_sum_or_mean_of_weak_voices() -> None:
    single = rank_condition(
        {"outcome": "open", "recall_evidence": [_proposal([_ratio("only", 1, 1, 2)])]}
    )
    voices = rank_condition(
        {
            "outcome": "open",
            "recall_evidence": [
                _proposal(
                    [
                        _ratio("z-case", 1, 1, 2),
                        # the same squared cosine from different integers: a tie
                        _term_row("a-case", 1, 2, 8, 2),
                        _term_row("m-case", 1, 3, 12, 3),
                        _ratio("weaker", 1, 1, 3),
                        _ratio("weakest", 1, 1, 4),
                    ]
                ),
                _proposal([_ratio("other-object", 1, 1, 3)]),
            ],
        }
    )
    assert voices["value"] == single["value"]
    assert _fraction(voices["s_plus"]) == Fraction(1, 4)
    assert voices["positive_case_ids"] == ["a-case", "m-case", "z-case"]
    assert voices["eligible_term_count"] == 6


def test_a_vetoed_sign_has_no_support_and_cannot_be_replaced_by_a_lesser_case() -> None:
    rows = [
        _ratio("best-positive", 1, 1, 1),
        _ratio("lesser-positive", 1, 1, 2),
        _ratio("negative", -1, 1, 2),
    ]
    open_result = rank_condition(
        {"outcome": "open", "recall_evidence": [_rec("unresolved_censored", rows)]}
    )
    vetoed = rank_condition(
        {
            "outcome": "open",
            "recall_evidence": [_rec("unresolved_censored", rows, vetoed=[1])],
        }
    )
    assert _fraction(open_result["s_plus"]) == 1
    assert vetoed["s_plus"]["available"] is False
    assert _fraction(vetoed["s_minus"]) == Fraction(1, 4)
    assert vetoed["e"] == _record(Fraction(3, 8))  # (1 + 0 - 1/4) / 2
    assert [item["case_id"] for item in vetoed["vetoed_excluded"]] == [
        "best-positive",
        "lesser-positive",
    ]


def test_ineligible_cases_do_not_grade_and_are_reported() -> None:
    record = _proposal([_ratio("silent", 1, 1, 1), _ratio("fine", -1, 1, 2)])
    record["silent_case_ids"] = ["silent"]
    result = rank_condition({"outcome": "open", "recall_evidence": [record]})
    assert result["s_plus"]["available"] is False
    assert _fraction(result["s_minus"]) == Fraction(1, 4)
    assert result["rejected_terms"] == [
        {"subject": "", "index": 0, "code": "ineligible_case_has_terms"}
    ]


def test_malformed_rows_are_excluded_and_named_not_silently_used() -> None:
    good = _ratio("good", 1, 1, 2)
    clean = rank_condition({"outcome": "open", "recall_evidence": [_proposal([good])]})
    messy = rank_condition(
        {
            "outcome": "open",
            "recall_evidence": [
                _proposal(
                    [
                        _term_row("impossible", 1, 3, 1, 1),
                        good,
                        _bad_terms(dot=-1),
                        "junk",
                    ]
                )
            ],
        }
    )
    assert messy["value"] == clean["value"]
    assert messy["exact"] == clean["exact"]
    assert [item["code"] for item in messy["rejected_terms"]] == [
        "cosine_terms_impossible",
        "cosine_dot_invalid",
        "case_term_not_object",
    ]
    assert [item["index"] for item in messy["rejected_terms"]] == [0, 2, 3]
    assert clean["rejected_terms"] == []


@pytest.mark.parametrize(
    "bad",
    [
        "junk",
        7,
        True,
        [7],
        [None],
        {"acl": 7},
        [_rec("proposal", [_ratio("p", 1, 1, 1)], vetoed=[2])],
        [{"outcome": "proposal", "case_terms": "rows"}],
        [{"outcome": "proposal", "silent_case_ids": [1]}],
    ],
)
def test_unusable_recall_evidence_grades_nothing_and_is_reported(bad: object) -> None:
    result = rank_condition({"outcome": "open", "recall_evidence": bad})
    assert result["exact"] == _record(Fraction(1, 2))
    assert result["e"] == _record(Fraction(1, 2))
    assert result["rejected_terms"]
    assert result["eligible_term_count"] == 0


def test_list_mapping_and_single_record_evidence_are_equivalent() -> None:
    record = _proposal([_ratio("p", 1, 1, 2), _ratio("n", -1, 1, 3)])
    shapes = [
        record,
        [record],
        {"acl": record},
        {"acl": [record]},
        (record,),
    ]
    values = {
        rank_condition({"outcome": "open", "recall_evidence": shape})["exact"][
            "numerator"
        ]
        for shape in shapes
    }
    assert len(values) == 1
    expected = _tier_value("open", (1 + _sq(1, 2) - _sq(1, 3)) / 2)
    assert Fraction(int(values.pop()), 648) == expected  # 329/648


def test_opposing_evidence_is_monotone_inside_a_tier() -> None:
    previous = -1.0
    for k in range(8):  # the best positive grows, the negative stays at 1/9
        value = rank_condition(
            {
                "outcome": "open",
                "recall_evidence": [
                    _proposal([_ratio("p", 1, k, 8), _ratio("n", -1, 1, 3)])
                ],
            }
        )["value"]
        assert value > previous
        previous = value
    previous = 2.0
    for k in range(8):  # the best negative grows, the positive stays at 1/9
        value = rank_condition(
            {
                "outcome": "open",
                "recall_evidence": [
                    _proposal([_ratio("p", 1, 1, 3), _ratio("n", -1, k, 8)])
                ],
            }
        )["value"]
        assert value < previous
        previous = value


def test_swapping_signs_reflects_the_open_tier_about_one_half() -> None:
    for left, right in [((1, 2), (1, 4)), ((3, 4), (1, 2)), ((1, 8), (7, 8))]:
        forward = rank_condition(
            {
                "outcome": "open",
                "recall_evidence": [
                    _proposal([_ratio("p", 1, *left), _ratio("n", -1, *right)])
                ],
            }
        )
        mirror = rank_condition(
            {
                "outcome": "open",
                "recall_evidence": [
                    _proposal([_ratio("p", 1, *right), _ratio("n", -1, *left)])
                ],
            }
        )
        assert _fraction(forward["exact"]) + _fraction(mirror["exact"]) == 1


def test_integers_far_beyond_float_range_are_exact() -> None:
    big = 10**600
    rows = [
        _term_row("big-positive", 1, big, 2 * big, 2 * big),  # exactly 1/4
        _term_row("big-negative", -1, big, 4 * big, 4 * big),  # exactly 1/16
    ]
    grade = (1 + Fraction(1, 4) - Fraction(1, 16)) / 2
    result = rank_condition(
        {"outcome": "assigned", "recall_evidence": [_proposal(rows)]}
    )
    assert _fraction(result["s_plus"]) == Fraction(1, 4)
    assert _fraction(result["s_minus"]) == Fraction(1, 16)
    assert result["exact"] == _record(_tier_value("assigned", grade))

    n = 10**400
    near_one = rank_condition(
        {
            "outcome": "assigned",
            "recall_evidence": [_proposal([_term_row("almost", 1, n - 1, n, n)])],
        }
    )
    support = Fraction((n - 1) ** 2, n * n)
    assert support != 1
    assert _fraction(near_one["s_plus"]) == support
    assert 0.0 < near_one["value"] < 1.0


def test_the_cosine_boundary_one_is_allowed_and_stays_below_the_ceiling() -> None:
    n = 10**500 + 7
    result = rank_condition(
        {
            "outcome": "assigned",
            "recall_evidence": [_proposal([_term_row("same", 1, n, n, n)])],
        }
    )
    assert _fraction(result["s_plus"]) == 1
    assert result["exact"] == _record(Fraction(8, 9))
    assert result["value"] < 1.0


def test_rank_is_pure_and_the_finding_embeds_exactly_its_rank() -> None:
    finding = combine_condition(
        "Fracture",
        {
            "femur": _present([_ratio("f", 1, 1, 2)]),
            "tibia": _proposal([_ratio("t", -1, 1, 3)]),
        },
    )
    before = copy.deepcopy(finding)
    again = rank_condition(finding)
    assert finding == before
    assert again == finding["rank"]
    assert finding["probability"] == finding["rank"]["value"]
    assert finding["rank"]["tier"] == finding["outcome"] == "assigned"
    assert finding["rank"]["policy_id"] == POLICY_ID
    # the grade uses every decision-bearing voice: best positive 1/4, best negative 1/9
    grade = (1 + Fraction(1, 4) - Fraction(1, 9)) / 2
    assert finding["rank"]["exact"] == _record(_tier_value("assigned", grade))


def test_supporting_context_never_grades_but_a_joint_whole_case_voice_does() -> None:
    decisive = {"acl": _proposal([_ratio("a-neg", -1, 1, 2)])}
    context = {
        "femur": _proposal([_ratio("f-pos", 1, 1, 1)]),
        "tibia": _proposal([_ratio("t-pos", 1, 1, 1)]),
        "pcl": _proposal([_ratio("c-pos", 1, 1, 1)]),
    }
    without = combine_condition("ACL", decisive)
    with_context = combine_condition("ACL", {**decisive, **context})
    assert with_context["outcome"] == without["outcome"] == "open"
    assert with_context["rank"] == without["rank"]
    assert with_context["rank"]["e"] == _record(Fraction(3, 8))  # (1 + 0 - 1/4) / 2
    assert sorted(with_context["recall_evidence"]) == ["acl"]

    joint = {"diagnosis/ACL": _proposal([_ratio("j-pos", 1, 1, 1)])}
    graded = combine_condition("ACL", {**decisive, **joint})
    assert (
        graded["outcome"] == "open"
    )  # proposal-only configuration evidence grades but cannot decide
    assert graded["rank"]["e"] == _record(Fraction(7, 8))  # (1 + 1 - 1/4) / 2
    assert graded["rank"]["positive_sources"] == [
        {"subject": "diagnosis/ACL", "case_id": "j-pos"}
    ]
    assert graded["evidence"]["joint_voice"]["role"] == "joint"
    # Rohan explicitly authorizes warranted whole-configuration recall.
    assert (
        combine_condition("ACL", {"diagnosis/ACL": _present()})["outcome"] == "assigned"
    )
    assert (
        combine_condition("ACL", {"diagnosis/ACL": _absent()})["outcome"] == "defeated"
    )


def test_a_malformed_joint_voice_is_reported_and_does_not_grade() -> None:
    result = combine_condition(
        "ACL",
        {
            "acl": _proposal([_ratio("a-neg", -1, 1, 2)]),
            "diagnosis/ACL": {"outcome": "bogus"},
        },
    )
    assert result["outcome"] == "open"
    assert result["evidence"]["joint_voice"]["code"] == "evidence_malformed"
    assert result["rank"]["e"] == _record(Fraction(3, 8))


def test_compact_bank_set_references_are_accepted_and_hollow_ones_refused() -> None:
    compact = _ratio("p", 1, 1, 2)
    compact["common_speaking_banks"] = {"bank_set": "abc123", "count": 3}
    accepted = combine_condition("ACL", {"acl": _present([compact])})
    assert accepted["outcome"] == "assigned"
    assert accepted["recall_evidence"]["acl"][0]["case_terms"][0][
        "common_speaking_banks"
    ] == {"bank_set": "abc123", "count": 3}

    hollow = (
        {"bank_set": "abc", "count": 0},
        {"bank_set": "", "count": 2},
        {"count": 2},
        {"bank_set": "abc", "count": True},
        [],
        "bank",
    )
    for bad in hollow:
        row = _ratio("p", 1, 1, 2)
        row["common_speaking_banks"] = bad
        result = combine_condition("ACL", {"acl": _present([row])})
        assert result["outcome"] == "open"
        assert result["evidence"]["readings"]["acl"]["code"] == "evidence_malformed"


def test_a_full_recall_object_record_is_read_as_supplied() -> None:
    record = {
        "question_id": "ACL",
        "subject": "acl",
        "selected_banks": ["bank-a", "bank-b"],
        "case_terms": [
            {
                "case_id": "case-1",
                "study_uid": "study-1",
                "call": 1,
                "terms": {"dot": 3, "left_norm_sq": 4, "right_norm_sq": 4},
                "common_speaking_banks": ["bank-a"],
                "trust": {"numerator": 3, "denominator": 4, "source": "teaching/c1"},
                "reaches_trust": True,
            },
            {
                "case_id": "case-2",
                "study_uid": "study-2",
                "call": -1,
                "terms": {"dot": 1, "left_norm_sq": 2, "right_norm_sq": 2},
                "common_speaking_banks": ["bank-a", "bank-b"],
                "trust": None,
                "reaches_trust": None,
            },
        ],
        "censor_terms": [],
        "speaking_case_ids": ["case-1"],
        "speaking_calls": [1],
        "excluded_case_ids": [],
        "source_group_excluded_case_ids": [],
        "excluded_source_group": "",
        "incompatible_case_ids": [],
        "silent_case_ids": [],
        "nearest_positive_case_ids": ["case-1"],
        "nearest_negative_case_ids": ["case-2"],
        "nearest_positive_case_id": "case-1",
        "nearest_negative_case_id": "case-2",
        "censor_ids": [],
        "vetoed_answers": [],
        "outcome": "present",
        "coverage": {"compatible_signed_cases": 2},
    }
    before = copy.deepcopy(record)
    result = combine_condition("ACL", {"acl": record})

    assert record == before
    assert result["outcome"] == "assigned"
    reading = result["evidence"]["readings"]["acl"]
    assert reading["trust_checked"] is True
    assert reading["speaking_case_ids"] == ["case-1"]
    # the untrusted negative case is a proposal: it grades, it never decides
    grade = (1 + Fraction(9, 16) - Fraction(1, 4)) / 2
    assert result["rank"]["exact"] == _record(_tier_value("assigned", grade))
    assert result["rank"]["positive_case_ids"] == ["case-1"]
    assert result["rank"]["negative_case_ids"] == ["case-2"]

    # the same record with the near-miss veto reaching the positive sign is a
    # contradiction, not a silently trusted warrant
    contradicted = copy.deepcopy(record)
    contradicted["vetoed_answers"] = [1]
    contradicted["censor_ids"] = ["censor-1"]
    assert combine_condition("ACL", {"acl": contradicted})["outcome"] == "open"


def test_warranted_configuration_decides_without_overriding_necessary_negative():
    assert (
        combine_condition("Medial OA", {"diagnosis/Medial OA": _present()})["outcome"]
        == "assigned"
    )
    assert (
        combine_condition("Medial OA", {"diagnosis/Medial OA": _absent()})["outcome"]
        == "defeated"
    )
    assert (
        combine_condition("ACL", {"acl": _absent(), "diagnosis/ACL": _present()})[
            "outcome"
        ]
        == "defeated"
    )
    assert (
        combine_condition("ACL", {"acl": _present(), "diagnosis/ACL": _absent()})[
            "outcome"
        ]
        == "open"
    )
    assert combine_condition("ACL", {"diagnosis/ACL": _conflict()})["outcome"] == "open"


def test_alternative_reasoning_intent_has_both_signs_and_unknowns():
    from knee.diagnosis.squint_contracts import _kleene_or

    assert _kleene_or(["negative", "negative"]) == "negative"
    assert _kleene_or(["negative", "positive"]) == "positive"
    assert _kleene_or(["negative", "unknown"]) == "unknown"
    assert _kleene_or(["negative", "conflict"]) == "conflict"
    assert _kleene_or(["conflict", "positive"]) == "positive"
    assert _kleene_or([]) == "unknown"
