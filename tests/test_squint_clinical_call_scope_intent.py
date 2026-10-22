"""Clinical source scope survives HDC recall into the actual condition consumer."""

import copy

import pytest

from knee.diagnosis.squint_contracts import combine_condition
from knee.diagnosis.squint_locator import (
    _case_call_scope,
    prepare_recall,
    recall_object,
)
from knee.diagnosis.squint_memory import (
    LOCALIZED_PRESENTATION_SCOPE,
    carry_condition_calls,
)
from knee.diagnosis.squint_memory_view import memory_view
from knee.diagnosis.squint_reports import (
    admit_report_cases,
    report_sha256,
    validate_report_calls,
)
from tests import test_report_identity_support_intent as fixture

QUERY_UID = "1.2.826.0003"


def setup_case(sign):
    memory, finding, base = fixture.inputs()
    other = copy.deepcopy(memory["cases"][0])
    other.update(case_id="opposing-bone", study_uid="1.2.826.0002")
    other["condition_calls"] = {"Fracture": -sign, "Contusion": -sign}
    other["profile"]["source"]["study_uid"] = other["study_uid"]
    other["profile"]["banks"] = {
        fixture.SAG_BANK: [1, 2, 0],
        fixture.COR_BANK: [1, 2, 0],
    }
    memory["cases"].append(other)
    memory["object_identity_teaching"]["confirmed_case_ids"].append(other["case_id"])
    memory["object_identity_teaching"]["calls"].append(
        {"candidate_id": other["case_id"], "call": "confirm"}
    )
    report = (
        "There is fracture and contusion."
        if sign == 1
        else "There is no fracture or contusion."
    )
    calls = [
        {
            **base,
            "question": question,
            "digit": sign,
            "assertion": "present" if sign == 1 else "absent",
            "sentence": report,
            "report_sha": report_sha256(report),
        }
        for question in ("Fracture", "Contusion")
    ]
    child = admit_report_cases(
        memory, [finding], calls, "clinical", reports={fixture.UID: report}
    )
    query = copy.deepcopy(finding["profile"])
    query["source"]["study_uid"] = QUERY_UID
    query["banks"] = {fixture.COR_BANK: [0, 0, 3]}
    return (child, query, calls, report)


@pytest.mark.parametrize("question", ["Fracture", "Contusion"])
def test_study_positive_keeps_hdc_terms_but_cannot_claim_this_bone_is_affected(
    question,
):
    memory, query, _, _ = setup_case(1)
    clinical = memory["cases"][-1]
    before = copy.deepcopy(clinical)
    assert _case_call_scope(clinical, question) == "positive_condition_presentation"
    prepared = prepare_recall(memory)
    view = memory_view(
        {**memory, "prepared_recall": prepared},
        exclude_study_uids=[QUERY_UID],
        selection_version=prepared.get("selection_version", "none"),
    )
    recalled = recall_object(query, view, question)
    assert QUERY_UID != clinical["study_uid"]
    assert recalled["outcome"] == "present"
    assert clinical["case_id"] in recalled["speaking_case_ids"]
    row = next(
        row for row in recalled["case_terms"] if row["case_id"] == clinical["case_id"]
    )
    assert row["call_scope"] == "positive_condition_presentation"
    assert row["terms"]["dot"] > 0
    decision = combine_condition(question, {"femur": recalled})
    assert decision["outcome"] == "open"
    assert (
        decision["evidence"]["readings"]["femur"]["code"]
        == "study_positive_presentation_not_localized"
    )
    assert decision["recall_evidence"]["femur"][0]["case_terms"]
    assert clinical == before
    assert clinical["condition_scopes"][question] == "study_condition"


@pytest.mark.parametrize("question", ["Fracture", "Contusion"])
def test_explicit_study_absence_remains_negative_evidence_not_silence(question):
    memory, query, _, _ = setup_case(-1)
    clinical = memory["cases"][-1]
    assert _case_call_scope(clinical, question) == "study_condition"
    prepared = prepare_recall(memory)
    view = memory_view(
        {**memory, "prepared_recall": prepared},
        exclude_study_uids=[QUERY_UID],
        selection_version=prepared.get("selection_version", "none"),
    )
    recalled = recall_object(query, view, question)
    assert recalled["outcome"] == "absent"
    assert clinical["case_id"] in recalled["speaking_case_ids"]
    decision = combine_condition(question, {"femur": recalled})
    assert decision["evidence"]["readings"]["femur"]["state"] == "negative"
    assert clinical["condition_calls"][question] == -1


@pytest.mark.parametrize("question", ["Fracture", "Contusion"])
def test_existing_independently_localized_finding_can_still_decide(question):
    memory, query, _, _ = setup_case(1)
    seed = memory["cases"][0]
    call = memory["object_identity_teaching"]["calls"][0]
    carry = carry_condition_calls(
        seed,
        call,
        {question: 1},
        localized_calls=[
            {
                "study_uid": seed["study_uid"],
                "subject": "femur",
                "question": question,
                "digit": 1,
                "source": {
                    "kind": "independent_visual_finding",
                    "finding": "this bone",
                },
            }
        ],
    )
    seed["condition_calls"] = carry["condition_calls"]
    seed["presentation_scope"] = carry["presentation_scope"]
    memory["cases"] = memory["cases"][:-1]
    assert _case_call_scope(seed, question) == LOCALIZED_PRESENTATION_SCOPE
    prepared = prepare_recall(memory)
    view = memory_view(
        {**memory, "prepared_recall": prepared},
        exclude_study_uids=[QUERY_UID],
        selection_version=prepared.get("selection_version", "none"),
    )
    recalled = recall_object(query, view, question)
    assert combine_condition(question, {"femur": recalled})["outcome"] == "assigned"


def test_report_validator_does_not_assert_localization_from_named_subject():
    _, _, calls, report = setup_case(1)
    records = validate_report_calls(
        [{**calls[0], "scope": LOCALIZED_PRESENTATION_SCOPE}], {fixture.UID: report}
    )
    assert records[0]["status"] == "scope_not_study_condition"


def test_unlocalized_clinical_source_cannot_be_widened_by_presentation_annotation():
    memory, _, _, _ = setup_case(1)
    clinical = memory["cases"][-1]
    clinical["presentation_scope"] = {"Fracture": LOCALIZED_PRESENTATION_SCOPE}
    assert _case_call_scope(clinical, "Fracture") == "positive_condition_presentation"


def test_whole_configuration_source_is_not_reclassified_as_one_bone():
    case = {
        "subject": "diagnosis/Fracture",
        "condition_calls": {"Fracture": 1},
        "condition_scopes": {"Fracture": "study_condition"},
    }
    assert _case_call_scope(case, "Fracture") == "study_condition"
