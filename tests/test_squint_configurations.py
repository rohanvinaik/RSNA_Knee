from __future__ import annotations

import copy
import json

import pytest

from knee.diagnosis.declarations import question_for
from knee.diagnosis.squint_configurations import (
    ConfigurationProfileError,
    configuration_profile,
    with_configuration_cases,
)
from knee.diagnosis.squint_memory import load_memory, save_memory
from knee.diagnosis.squint_profiles import cosine_evidence
from knee.study.tables import LABELS


def _object_case(study_uid: str, subject: str, value: int) -> dict:
    return {
        "case_id": f"object-case:{study_uid}:{subject}",
        "study_uid": study_uid,
        "subject": subject,
        "condition_calls": {},
        "profile": {
            "schema": "knee.squint-profile/v1",
            "subject": subject,
            "banks": {"view/signal_median/overview/10mm": [value, 2, 3]},
            "source": {
                "procedure": "knee.squint-profile/scan-tercile-v1",
                "lineage": [{"series_uid": f"series-{subject}", "window": [1, 2, 3]}],
            },
        },
        "full_profile": {
            "subject": subject,
            "count_layout_id": f"layout-{subject}",
        },
        "full_source": {
            "product_path": f"/products/{study_uid}.h5",
            "product_sha256": "a" * 64,
            "study_uid": study_uid,
        },
        "regions": [],
        "teaching_source": {"kind": "official_train_csv_label"},
    }


def _memory() -> dict:
    labels = {question: None for question in LABELS}
    labels.update({"ACL": 1, "MCL": 0})
    return {
        "schema": "knee.squint-memory/v1",
        "revision": "bootstrap-r1",
        "questions": list(LABELS),
        "label_ledger": {"study-a": labels},
        "source_identities": {},
        "cases": [
            _object_case("study-a", "acl", 7),
            _object_case("study-a", "femur", 11),
            _object_case("study-a", "tibia", 13),
            _object_case("study-a", "pcl", 17),
            _object_case("study-b", "acl", 19),
        ],
    }


def test_configuration_profile_qualifies_banks_and_preserves_role_sources() -> None:
    profiles = {
        "acl": _object_case("study-a", "acl", 7),
        "femur": _object_case("study-a", "femur", 11),
        "tibia": _object_case("study-a", "tibia", 13),
        "unrelated": _object_case("study-a", "unrelated", 99),
    }
    result = configuration_profile(profiles, "ACL")
    assert result["subject"] == "diagnosis/ACL"
    assert result["banks"] == {
        f"object/{subject}/view/signal_median/overview/10mm": [value, 2, 3]
        for subject, value in (("acl", 7), ("femur", 11), ("tibia", 13))
    }
    source = result["source"]
    assert source["object_order"] == list(question_for("ACL").objects)
    assert (
        source["roles"]["acl"]["profile_source"] == profiles["acl"]["profile"]["source"]
    )
    assert source["roles"]["acl"]["full_profile"] == profiles["acl"]["full_profile"]
    assert source["roles"]["acl"]["full_source"] == profiles["acl"]["full_source"]
    assert source["missing_roles"] == [
        {"subject": "pcl", "status": "missing_object_case"}
    ]
    assert "unrelated" not in source["roles"]


def test_configuration_profile_keeps_silent_role_and_zero_counts() -> None:
    profiles = {
        "acl": _object_case("study-a", "acl", 0),
        "femur": _object_case("study-a", "femur", 0),
        "tibia": {
            **_object_case("study-a", "tibia", 0),
            "profile": {
                "schema": "knee.squint-profile/v1",
                "subject": "tibia",
                "banks": {},
                "source": {
                    "procedure": "knee.squint-profile/scan-tercile-v1",
                    "status": "silent",
                },
            },
        },
    }
    result = configuration_profile(profiles, "ACL")
    assert result["source"]["roles"]["tibia"]["status"] == "present"
    assert result["source"]["roles"]["tibia"]["bank_count"] == 0
    assert all(counts == [0, 2, 3] for counts in result["banks"].values())


def test_configuration_profile_is_accepted_by_shared_writer_cosine() -> None:
    profiles = {
        "acl": _object_case("study-a", "acl", 7),
        "femur": _object_case("study-a", "femur", 11),
        "tibia": _object_case("study-a", "tibia", 13),
    }
    composite = configuration_profile(profiles, "ACL")
    assert composite["source"]["procedure"] == "knee.squint-profile/scan-tercile-v1"
    evidence = cosine_evidence(composite, composite)
    assert evidence["code"] == "ok"
    assert evidence["common_banks"] == sorted(composite["banks"])


def test_with_configuration_cases_uses_only_explicit_labels_and_is_immutable() -> None:
    memory = _memory()
    original = copy.deepcopy(memory)
    result = with_configuration_cases(memory)
    assert memory == original
    assert [case["case_id"] for case in result["cases"][: len(memory["cases"])]] == [
        case["case_id"] for case in memory["cases"]
    ]
    created = [
        case
        for case in result["cases"]
        if case["case_id"].startswith("squint-configuration:")
    ]
    assert len(created) == 2
    assert [case["condition_calls"] for case in created] == [{"ACL": 1}, {"MCL": -1}]
    assert [case["presentation_scope"] for case in created] == [
        {"ACL": "study_condition_configuration"},
        {"MCL": "study_condition_configuration"},
    ]
    acl_case = created[0]
    assert acl_case["profile"]["banks"][
        "object/acl/view/signal_median/overview/10mm"
    ] == [7, 2, 3]
    assert (
        acl_case["profile"]["source"]["roles"]["acl"]["full_source"]["product_path"]
        == "/products/study-a.h5"
    )
    serialized_profile = json.dumps(acl_case["profile"], sort_keys=True)
    assert "condition_calls" not in serialized_profile
    assert "label_ledger" not in serialized_profile
    assert "study_condition_configuration" not in serialized_profile
    assert not any(
        case["study_uid"] == "study-b" and case["subject"] == "diagnosis/ACL"
        for case in created
    )


def test_with_configuration_cases_is_deduplicated_and_preserves_case_order() -> None:
    memory = _memory()
    once = with_configuration_cases(memory)
    twice = with_configuration_cases(once)
    assert twice == once
    assert len(twice["cases"]) == len(once["cases"])
    assert twice["revision"] == once["revision"]
    assert json.dumps(twice, sort_keys=True) == json.dumps(once, sort_keys=True)


def test_configuration_memory_roundtrips_through_existing_store(tmp_path) -> None:
    configured = with_configuration_cases(_memory())
    path = tmp_path / "configured-memory"
    receipt = save_memory(configured, path)
    assert receipt["case_count"] == len(configured["cases"])
    assert load_memory(path) == configured


def test_label_change_changes_call_but_not_composed_profile() -> None:
    present = _memory()
    absent = copy.deepcopy(present)
    absent["label_ledger"]["study-a"]["ACL"] = 0
    present_case = next(
        case
        for case in with_configuration_cases(present)["cases"]
        if case["subject"] == "diagnosis/ACL"
    )
    absent_case = next(
        case
        for case in with_configuration_cases(absent)["cases"]
        if case["subject"] == "diagnosis/ACL"
    )
    assert present_case["condition_calls"] == {"ACL": 1}
    assert absent_case["condition_calls"] == {"ACL": -1}
    assert present_case["profile"] == absent_case["profile"]


@pytest.mark.parametrize(
    ("question", "code"),
    [("", "question_id_invalid"), ("No such condition", "question_id_unknown")],
)
def test_configuration_profile_refuses_invalid_question(
    question: str, code: str
) -> None:
    with pytest.raises(ConfigurationProfileError, match=code):
        configuration_profile({}, question)


def test_configuration_profile_refuses_malformed_profile_counts() -> None:
    bad = _object_case("study-a", "acl", 1)
    bad["profile"]["banks"]["bad"] = [1, True, 3]
    with pytest.raises(
        ConfigurationProfileError, match="object_profile_bank_counts_invalid"
    ):
        configuration_profile({"acl": bad}, "ACL")


def test_configuration_profile_refuses_wrong_procedure() -> None:
    bad = _object_case("study-a", "acl", 1)
    bad["profile"]["source"]["procedure"] = "different-procedure"
    with pytest.raises(
        ConfigurationProfileError, match="object_profile_procedure_mismatch"
    ):
        configuration_profile({"acl": bad}, "ACL")


def test_with_configuration_cases_refuses_duplicate_object_cases() -> None:
    memory = _memory()
    duplicate = _object_case("study-a", "acl", 23)
    duplicate["case_id"] = "object-case:study-a:acl-duplicate"
    memory["cases"].append(duplicate)
    with pytest.raises(ConfigurationProfileError, match="study_object_case_duplicate"):
        with_configuration_cases(memory)
