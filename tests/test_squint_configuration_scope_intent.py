"""Configuration names cannot add tissue coverage or diagnostic authority."""

import pytest

from knee.diagnosis.squint_contracts import combine_condition


def _bank(subject: str, role: str = "object") -> str:
    return (
        f'object/{subject}/squint/v2/view=["Coronal","1","1"]/'
        f"role={role}/metric=signal_median/direction=overview/scale=10mm"
    )


def _case(call: int, subjects: tuple[str, ...], *, scope: str, role="object") -> dict:
    return {
        "case_id": "independently-taught-case",
        "call": call,
        "call_scope": scope,
        "terms": {"dot": 1, "left_norm_sq": 1, "right_norm_sq": 1},
        "reaches_trust": True,
        "trust": {"source": "retained-independent-opposition-envelope"},
        "common_speaking_banks": [_bank(subject, role) for subject in subjects],
    }


def _recall(row: dict) -> dict:
    return {
        "outcome": "present" if row["call"] == 1 else "absent",
        "case_terms": [row],
        "speaking_calls": [row["call"]],
    }


@pytest.mark.parametrize("question", ["Contusion", "Fracture"])
@pytest.mark.parametrize("bone", ["femur", "tibia", "patella"])
def test_one_unlocalized_bone_does_not_gain_authority_by_configuration_wrapping(
    question: str, bone: str
) -> None:
    row = _case(1, (bone,), scope="study_condition_configuration")
    result = combine_condition(question, {f"diagnosis/{question}": _recall(row)})

    assert result["outcome"] == "open"
    coverage = result["evidence"]["joint_configuration_coverage"]
    assert coverage["eligible_case_ids"]["positive"] == []
    assert coverage["excluded_cases"] == [
        {
            "case_id": row["case_id"],
            "call": 1,
            "reason": "unlocalized_single_bone_presentation",
            "covered_subjects": [bone],
            "case_coverage_disposition": "unlocalized_single_bone_presentation",
            "call_scope": "study_condition_configuration",
        }
    ]
    assert result["recall_evidence"][f"diagnosis/{question}"][0]["case_terms"]


@pytest.mark.parametrize("question", ["Contusion", "Fracture"])
def test_actual_joint_bone_comparison_keeps_configuration_authority(
    question: str,
) -> None:
    row = _case(1, ("femur", "tibia"), scope="study_condition_configuration")
    result = combine_condition(question, {f"diagnosis/{question}": _recall(row)})

    assert result["outcome"] == "assigned"
    assert result["evidence"]["joint_configuration_coverage"]["eligible_case_ids"][
        "positive"
    ] == [row["case_id"]]


@pytest.mark.parametrize("question", ["Contusion", "Fracture"])
def test_localized_positive_bone_scope_is_not_a_study_presentation(
    question: str,
) -> None:
    row = _case(1, ("femur",), scope="localized_finding")
    result = combine_condition(question, {f"diagnosis/{question}": _recall(row)})

    assert result["outcome"] == "assigned"


@pytest.mark.parametrize("question", ["Contusion", "Fracture"])
def test_whole_normal_configuration_keeps_authority_without_every_site(
    question: str,
) -> None:
    row = _case(-1, ("tibia",), scope="study_condition_configuration")
    result = combine_condition(question, {f"diagnosis/{question}": _recall(row)})

    assert result["outcome"] == "defeated"


@pytest.mark.parametrize("call", [-1, 1])
def test_surroundings_are_comparison_evidence_not_defining_tissue(call: int) -> None:
    row = _case(call, ("mcl",), scope="study_condition_configuration", role="context")
    result = combine_condition("MCL", {"diagnosis/MCL": _recall(row)})

    assert result["outcome"] == "open"
    coverage = result["evidence"]["joint_configuration_coverage"]
    assert coverage["eligible_case_ids"] == {"positive": [], "negative": []}
    assert coverage["excluded_cases"][0]["covered_subjects"] == []
    assert result["recall_evidence"]["diagnosis/MCL"][0]["case_terms"][0][
        "common_speaking_banks"
    ] == [_bank("mcl", "context")]


@pytest.mark.parametrize("call, expected", [(-1, "defeated"), (1, "assigned")])
def test_own_mcl_tissue_and_its_surroundings_keep_both_signed_voices(
    call: int, expected: str
) -> None:
    row = _case(call, ("mcl",), scope="study_condition_configuration")
    row["common_speaking_banks"].append(_bank("mcl", "context"))
    result = combine_condition("MCL", {"diagnosis/MCL": _recall(row)})

    assert result["outcome"] == expected
    assert (
        len(
            result["recall_evidence"]["diagnosis/MCL"][0]["case_terms"][0][
                "common_speaking_banks"
            ]
        )
        == 2
    )


def test_a_subject_prefix_without_tissue_role_does_not_certify_coverage() -> None:
    row = _case(1, ("acl",), scope="study_condition_configuration")
    row["common_speaking_banks"] = ["object/acl/measured-bank"]
    result = combine_condition("ACL", {"diagnosis/ACL": _recall(row)})

    assert result["outcome"] == "open"
    assert result["evidence"]["joint_configuration_coverage"]["eligible_case_ids"] == {
        "positive": [],
        "negative": [],
    }
