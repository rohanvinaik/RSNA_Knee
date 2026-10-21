from __future__ import annotations

from knee.diagnosis.squint_locator import prepare_recall, recall_object


def _profile() -> dict:
    return {
        "schema": "knee.squint-profile/v1",
        "subject": "femur",
        "banks": {"axial/light/whole": [4, 0, 0]},
        "source": {"procedure": "knee.squint-profile/scan-tercile-v1"},
    }


def _case(case_id: str, call: int, scope: object = ...) -> dict:
    case = {
        "case_id": case_id,
        "study_uid": f"study-{case_id}",
        "subject": "femur",
        "condition_calls": {"ACL": call},
        "profile": _profile(),
        "teaching_source": {"kind": "official_train_csv_label"},
    }
    if scope is not ...:
        case["presentation_scope"] = scope
    return case


def test_recall_case_terms_preserve_only_valid_per_question_call_scope() -> None:
    memory = {
        "cases": [
            _case("positive", 1, {"ACL": "positive_condition_presentation"}),
            _case(
                "negative",
                -1,
                {"ACL": "condition_negative_with_other_positive_presentation"},
            ),
            _case("scope-absent", 1),
            _case("scope-malformed", 1, {"ACL": 1}),
        ]
    }
    memory["prepared_recall"] = prepare_recall(memory)

    result = recall_object(_profile(), memory, "ACL")

    terms = {row["case_id"]: row for row in result["case_terms"]}
    assert terms["positive"]["call_scope"] == "positive_condition_presentation"
    assert terms["negative"]["call_scope"] == (
        "condition_negative_with_other_positive_presentation"
    )
    assert terms["scope-absent"]["call_scope"] is None
    assert terms["scope-malformed"]["call_scope"] is None
