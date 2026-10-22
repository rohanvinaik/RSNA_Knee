from __future__ import annotations

import copy
import json

import scripts.prepare_squint_training as cli
from knee.diagnosis.squint_identity import identity_condition_views, prepare_identity
from knee.study.tables import LABELS
from tests.test_squint_visual_teaching import additions, parent, rejection


def test_round_composition_keeps_a_visual_reject_out_of_positive_and_clinical_stores(
    tmp_path,
):
    original = parent()
    before = copy.deepcopy(original)
    a = rejection()
    source = tmp_path / "negative.json"
    source.write_text(json.dumps(a))

    child, summary = cli._compose_round_teaching(
        original,
        "a" * 64,
        labels={"calls": {"study-new": dict.fromkeys(LABELS, -1)}},
        labels_identity={"path": str(tmp_path / "train.csv"), "sha256": "b" * 64},
        visual_additions_path=source,
        round_name="signed-visual-round",
    )

    assert original == before
    assert child["cases"] == original["cases"]
    [negative] = child["object_identity_cases"]["cases"]
    assert negative["case_id"] == "new-acl"
    assert negative["condition_calls"] == {}
    assert "label_attribution" not in negative
    assert negative["direct_visual_teaching"]["call"]["call"] == "reject"
    assert child["object_identity_teaching"]["negative_case_ids"] == ["new-acl"]
    assert "new-acl" not in identity_condition_views(child)["views"]
    assert prepare_identity(child)["negative_case_count"] == 1
    assert summary == {
        "added_visual_case_ids": ["new-acl"],
        "carried_condition_case_ids": [],
        "rebuilt_configuration_case_ids": [],
        "rebuilt_study_uids": [],
    }


def test_round_composition_still_carries_a_confirmed_object_and_rebuilds_its_configuration(
    tmp_path,
):
    original = parent()
    a = additions()
    a["cases"][0]["condition_calls"] = {}
    a["cases"][0]["presentation_scope"] = {}
    source = tmp_path / "positive.json"
    source.write_text(json.dumps(a))
    labels = dict.fromkeys(LABELS, -1)
    labels["ACL"] = 1

    child, summary = cli._compose_round_teaching(
        original,
        "a" * 64,
        labels={"calls": {"study-new": labels}},
        labels_identity={"path": str(tmp_path / "train.csv"), "sha256": "b" * 64},
        visual_additions_path=source,
        round_name="signed-visual-round",
    )

    [confirmed] = [case for case in child["cases"] if case["case_id"] == "new-acl"]
    assert confirmed["condition_calls"]["ACL"] == 1
    assert confirmed["label_attribution"]["ACL"]["source_sha256"] == "b" * 64
    assert "new-acl" in identity_condition_views(child)["views"]
    assert summary["added_visual_case_ids"] == ["new-acl"]
    assert summary["carried_condition_case_ids"] == ["new-acl"]
    assert summary["rebuilt_study_uids"] == ["study-new"]
    assert summary["rebuilt_configuration_case_ids"]
    assert any(case["subject"] == "diagnosis/ACL" for case in child["cases"])
