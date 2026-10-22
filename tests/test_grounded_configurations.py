"""A configuration must read its actual measured roles, never a namesake."""

import copy

from knee.diagnosis.squint_configurations import configuration_reference
from knee.diagnosis.squint_identity import identity_condition_views
from knee.diagnosis.squint_interfaces import TERRITORY_PROCEDURE, territory_bank_name
from knee.diagnosis.squint_locator import _scoped_cases, recall_source_fingerprint


def memory():
    view = {"orientation": "Coronal", "fluid_sensitive": "1", "fat_suppression": "1"}
    bank = territory_bank_name(view, "object", "local_range", "overview", 2.0)
    reference = {
        "case_id": "grounded:medial-oa:diagnosed",
        "study_uid": "study-x",
        "subject": "femoral_cartilage",
        "condition_calls": {"Medial OA": 1},
        "profile": {
            "schema": "knee.squint-profile/v1",
            "subject": "femoral_cartilage",
            "banks": {bank: [2, 3, 4]},
            "source": {"procedure": TERRITORY_PROCEDURE},
        },
        "regions": [],
        "teaching_source": {"official_row": {"Medial OA": "1"}},
        "direct_visual_teaching": {"kind": "reviewed_question_reference"},
        "question_reference": {
            "schema": "knee.question-reference/v1",
            "question": "Medial OA",
        },
    }
    canonical = copy.deepcopy(reference)
    canonical["case_id"] = "canonical-cartilage"
    canonical["condition_calls"] = {}
    del canonical["question_reference"]
    configuration = configuration_reference(reference, [["Coronal", "1", "1"]])
    m = {
        "schema": "knee.squint-memory/v1",
        "revision": "test",
        "cases": [canonical, reference, configuration],
        "object_identity_teaching": {
            "schema": "knee.object-identity-teaching/v1",
            "confirmed_case_ids": [canonical["case_id"], reference["case_id"]],
            "calls": [
                {
                    "candidate_id": canonical["case_id"],
                    "call": "confirm",
                    "views": [["Sagittal", "1", "1"]],
                },
                {
                    "candidate_id": reference["case_id"],
                    "call": "confirm",
                    "views": [["Coronal", "1", "1"]],
                },
            ],
        },
    }
    return m, bank


def test_pictured_reference_not_a_namesakes_view_governs_configuration():
    m, bank = memory()
    scoped = _scoped_cases(m["cases"], identity_condition_views(m))
    assert scoped[0]["profile"]["banks"] == {}
    assert scoped[-1]["profile"]["banks"] == {
        "object/femoral_cartilage/" + bank: [2, 3, 4]
    }
    assert scoped[-1]["condition_calls"] == {"Medial OA": 1}


def test_reference_role_cannot_borrow_identity_from_another_study():
    m, _ = memory()
    m["cases"][1]["study_uid"] = "different-study"
    scoped = _scoped_cases(m["cases"], identity_condition_views(m))
    assert scoped[-1]["profile"]["banks"] == {}


def test_condition_labels_do_not_enter_configuration_measurements():
    m, _ = memory()
    ref = m["cases"][1]
    before = configuration_reference(ref, [["Coronal", "1", "1"]])
    ref["condition_calls"] = {"Medial OA": -1}
    after = configuration_reference(ref, [["Coronal", "1", "1"]])
    assert before["profile"] == after["profile"]
    assert before["condition_calls"] != after["condition_calls"]


def test_configuration_role_identity_changes_expire_preparation():
    m, _ = memory()
    before = recall_source_fingerprint(m)
    m["cases"][-1]["configuration_teaching"]["roles"]["femoral_cartilage"][
        "case_id"
    ] = "canonical-cartilage"
    assert recall_source_fingerprint(m) != before
    scoped = _scoped_cases(m["cases"], identity_condition_views(m))
    assert scoped[-1]["profile"]["banks"] == {}


def test_later_growth_rebuild_keeps_paired_configuration_precedents():
    from knee.diagnosis.squint_configurations import (
        apply_rebuilt_configurations,
        rebuild_study_configurations,
    )

    m, _ = memory()
    m["object_identity_teaching"]["calls"][0]["views"] = [["Coronal", "1", "1"]]
    m["label_ledger"] = {"study-x": {"Medial OA": 1}}
    reference_id = m["cases"][-1]["case_id"]
    rebuilt = rebuild_study_configurations(
        m, ["study-x"], built_by={"kind": "growth_fixture"}
    )
    child = apply_rebuilt_configurations(m, rebuilt)
    assert any(c["case_id"] == reference_id for c in child["cases"])
    assert len(rebuilt["cases"]) == 1
    assert (
        rebuilt["cases"][0]["configuration_teaching"]["roles"]["femoral_cartilage"][
            "case_id"
        ]
        == "canonical-cartilage"
    )
