"""Clinical teaching uses an existing measured identity; it never creates one."""

import copy

import pytest

from knee.diagnosis.squint_configurations import (
    ConfigurationProfileError,
    _role_links,
    apply_rebuilt_configurations,
    rebuild_study_configurations,
)
from knee.diagnosis.squint_identity import (
    identity_condition_views,
    measured_identity_support_code,
    prepare_identity,
)
from knee.diagnosis.squint_interfaces import TERRITORY_PROCEDURE, territory_bank_name
from knee.diagnosis.squint_locator import _scoped_cases, prepare_recall, recall_object
from knee.diagnosis.squint_memory_view import memory_view
from knee.diagnosis.squint_reports import admit_report_cases, report_sha256

UID = "1.2.826.0001"
SAG, COR = ["Sagittal", "0", "0"], ["Coronal", "0", "0"]
REPORT = "There is no fracture."


def bank(view):
    return territory_bank_name(
        dict(
            zip(
                ("orientation", "fluid_sensitive", "fat_suppression"), view, strict=True
            )
        ),
        "object",
        "signal_median",
        "overview",
        10.0,
    )


SAG_BANK, COR_BANK = bank(SAG), bank(COR)


def inputs():
    regions = [
        {"series_uid": "sag-series", "window": [2, 3, 4, 8, 5, 10]},
        {"series_uid": "cor-series", "window": [3, 4, 5, 9, 6, 11]},
    ]
    profile = {
        "schema": "knee.squint-profile/v1",
        "subject": "femur",
        "banks": {SAG_BANK: [3, 0, 0], COR_BANK: [0, 0, 3]},
        "source": {
            "study_uid": UID,
            "mode": "cheap",
            "procedure": TERRITORY_PROCEDURE,
            "regions": copy.deepcopy(regions),
        },
    }
    seed = {
        "case_id": "confirmed-femur",
        "study_uid": UID,
        "subject": "femur",
        "profile": profile,
        "regions": regions,
        "condition_calls": {},
    }
    memory = {
        "schema": "knee.squint-memory/v1",
        "revision": "parent",
        "cases": [seed],
        "object_identity_teaching": {
            "schema": "knee.object-identity-teaching/v1",
            "reader": "visual-reviewer",
            "confirmed_case_ids": [seed["case_id"]],
            "calls": [
                {
                    "candidate_id": seed["case_id"],
                    "call": "confirm",
                    "views": [COR],
                    "negative_views": [SAG],
                }
            ],
        },
    }
    finding = {
        "study_uid": UID,
        "subject": "femur",
        "status": "located",
        "profile": copy.deepcopy(profile),
        "regions": [
            {**copy.deepcopy(r), "view_annotation": "retained"} for r in regions
        ],
    }
    call = {
        "study_uid": UID,
        "subject": "femur",
        "question": "Fracture",
        "digit": -1,
        "assertion": "absent",
        "sentence": REPORT,
        "scope": "study_condition",
        "source": "report:fixture.csv",
        "reader": "clinical-reader",
        "report_sha": report_sha256(REPORT),
    }
    return memory, finding, call


def test_exact_measured_support_binds_condition_to_existing_identity_only():
    memory, finding, call = inputs()
    before = copy.deepcopy(memory)
    child = admit_report_cases(
        memory, [finding], [call], "child", reports={UID: REPORT}
    )
    clinical = child["cases"][-1]
    assert clinical["identity_source_case_id"] == "confirmed-femur"
    assert clinical["condition_calls"] == {"Fracture": -1}
    assert clinical["teaching"]["pixel_localization_confirmed"] is False
    assert memory == before
    assert child["object_identity_teaching"] == before["object_identity_teaching"]
    assert (
        prepare_identity(child)["seed_count"]
        == prepare_identity(memory)["seed_count"]
        == 1
    )


def test_clinical_case_speaks_only_through_precursors_valid_views_in_preparation():
    memory, finding, call = inputs()
    opposing = copy.deepcopy(memory["cases"][0])
    opposing.update(case_id="opposing-femur", study_uid="1.2.826.0002")
    opposing["condition_calls"] = {"Fracture": 1}
    opposing["profile"]["banks"] = {SAG_BANK: [1, 2, 0], COR_BANK: [1, 2, 0]}
    opposing["profile"]["source"]["study_uid"] = "1.2.826.0002"
    memory["cases"].append(opposing)
    memory["object_identity_teaching"]["confirmed_case_ids"].append("opposing-femur")
    memory["object_identity_teaching"]["calls"].append(
        {"candidate_id": "opposing-femur", "call": "confirm"}
    )
    child = admit_report_cases(
        memory, [finding], [call], "child", reports={UID: REPORT}
    )
    clinical = child["cases"][-1]
    scope = identity_condition_views(child)
    assert scope["views"][clinical["case_id"]] == frozenset({tuple(COR)})
    cases = _scoped_cases(child["cases"], scope)
    assert set(cases[-1]["profile"]["banks"]) == {COR_BANK}
    prepared = prepare_recall(child)
    assert prepared["outcome"] == "prepared"
    assert (
        clinical["case_id"]
        not in child["object_identity_teaching"]["confirmed_case_ids"]
    )
    query_uid = "1.2.826.0003"
    query = copy.deepcopy(finding["profile"])
    query["source"]["study_uid"] = query_uid
    query["banks"] = {COR_BANK: [0, 0, 3]}
    view = memory_view(
        {**child, "prepared_recall": prepared},
        exclude_study_uids=[query_uid],
        selection_version=prepared.get("selection_version", "none"),
    )
    recalled = recall_object(query, view, "Fracture")
    assert query_uid != clinical["study_uid"]
    assert recalled["outcome"] == "absent"
    assert clinical["case_id"] in recalled["speaking_case_ids"]


@pytest.mark.parametrize(
    "difference", ["region", "profile_source", "series", "no_regions"]
)
def test_same_study_and_object_cannot_lend_identity_to_different_support(difference):
    memory, finding, call = inputs()
    if difference == "region":
        finding["regions"][0]["window"][0:2] = [10, 11]
    elif difference == "profile_source":
        finding["profile"]["source"]["procedure"] = "different-reader"
    elif difference == "series":
        finding["regions"][0]["series_uid"] = "another-series"
    else:
        finding["regions"] = []
    child = admit_report_cases(
        memory, [finding], [call], "child", reports={UID: REPORT}
    )
    clinical = child["cases"][-1]
    assert "identity_source_case_id" not in clinical
    assert clinical["case_id"] not in identity_condition_views(child)["views"]


def test_report_without_preexisting_identity_creates_no_identity_evidence():
    memory, finding, call = inputs()
    memory["object_identity_teaching"]["confirmed_case_ids"] = []
    child = admit_report_cases(
        memory, [finding], [call], "child", reports={UID: REPORT}
    )
    clinical = child["cases"][-1]
    assert "identity_source_case_id" not in clinical
    assert identity_condition_views(child)["views"] == {}
    assert prepare_identity(child)["seed_count"] == 0


def test_consumer_rechecks_link_after_support_changed_or_identity_corrected():
    memory, finding, call = inputs()
    child = admit_report_cases(
        memory, [finding], [call], "child", reports={UID: REPORT}
    )
    clinical = child["cases"][-1]
    clinical["regions"][0]["window"][0:2] = [10, 11]
    assert clinical["case_id"] not in identity_condition_views(child)["views"]
    clinical["regions"] = copy.deepcopy(finding["regions"])
    child["object_identity_teaching"]["confirmed_case_ids"] = []
    assert clinical["case_id"] not in identity_condition_views(child)["views"]


def test_ambiguous_precursors_do_not_create_an_implicit_identity_join():
    memory, finding, call = inputs()
    second = copy.deepcopy(memory["cases"][0])
    second["case_id"] = "second-confirmed-femur"
    memory["cases"].append(second)
    memory["object_identity_teaching"]["confirmed_case_ids"].append(second["case_id"])
    memory["object_identity_teaching"]["calls"].append(
        {"candidate_id": second["case_id"], "call": "confirm", "views": [SAG]}
    )
    child = admit_report_cases(
        memory, [finding], [call], "child", reports={UID: REPORT}
    )
    assert "identity_source_case_id" not in child["cases"][-1]


def test_support_comparison_names_match_difference_and_unavailable():
    memory, finding, _ = inputs()
    source = memory["cases"][0]
    assert measured_identity_support_code(source, finding) == "same_measured_support"
    assert measured_identity_support_code(source, None) == "support_unavailable"
    finding["subject"] = "tibia"
    assert measured_identity_support_code(source, finding) == "different_support"


def test_verified_clinical_alias_preserves_configuration_and_rebuilds_one_role():
    memory, finding, call = inputs()
    memory["label_ledger"] = {UID: {"Fracture": 0}}
    built = rebuild_study_configurations(memory, [UID], built_by={"kind": "fixture"})
    memory = apply_rebuilt_configurations(memory, built)
    child = admit_report_cases(
        memory, [finding], [call], "child", reports={UID: REPORT}
    )
    clinical = child["cases"][-1]
    scope = identity_condition_views(child)
    before_config = next(
        c for c in memory["cases"] if c["subject"] == "diagnosis/Fracture"
    )
    scoped_config = next(
        c
        for c in _scoped_cases(child["cases"], scope)
        if c["subject"] == "diagnosis/Fracture"
    )
    assert scoped_config["profile"]["banks"] == before_config["profile"]["banks"]
    rebuilt = rebuild_study_configurations(child, [UID], built_by={"kind": "fixture"})
    assert len(rebuilt["cases"]) == 1
    role = rebuilt["cases"][0]["configuration_teaching"]["roles"]["femur"]
    assert role["case_id"] == "confirmed-femur"
    assert role["identity_views"] == [COR]
    updated = apply_rebuilt_configurations(child, rebuilt)
    assert clinical in updated["cases"]
    assert clinical["condition_calls"] == {"Fracture": -1}
    # Direct role-link reading also uses the original identity call, not a
    # nonexistent clinical identity row or the report reader as identity teacher.
    links = _role_links({**child, "cases": [child["cases"][0], clinical]})
    assert links["femur"]["case_id"] == "confirmed-femur"
    assert links["femur"]["identity"]["reader"] == "visual-reviewer"


def test_unbound_clinical_duplicate_cannot_replace_an_explicit_configuration_source():
    memory, finding, call = inputs()
    memory["label_ledger"] = {UID: {"Fracture": 0}}
    built = rebuild_study_configurations(memory, [UID], built_by={"kind": "fixture"})
    memory = apply_rebuilt_configurations(memory, built)
    finding["regions"][0]["window"][0:2] = [10, 11]
    child = admit_report_cases(
        memory, [finding], [call], "child", reports={UID: REPORT}
    )
    assert "identity_source_case_id" not in child["cases"][-1]
    scope = identity_condition_views(child)
    config = next(
        c
        for c in _scoped_cases(child["cases"], scope)
        if c["subject"] == "diagnosis/Fracture"
    )
    # The existing configuration explicitly names the original measured
    # identity. An unrelated, unbound report presentation cannot silence it.
    # Rebuilding without a unique new role remains ambiguous below.
    assert set(config["profile"]["banks"]) == {"object/femur/" + COR_BANK}
    with pytest.raises(ConfigurationProfileError):
        rebuild_study_configurations(child, [UID], built_by={"kind": "fixture"})
