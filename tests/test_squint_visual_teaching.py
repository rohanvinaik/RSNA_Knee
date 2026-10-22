from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from knee.diagnosis.squint_identity import identity_condition_views, prepare_identity
from knee.diagnosis.squint_memory import load_memory_snapshot, save_memory
from knee.diagnosis.squint_visual_teaching import (
    SCHEMA,
    VisualTeachingError,
    publish_visual_cases,
    validate_additions,
)
from knee.study.tables import LABELS

pytest_plugins = ["tests.test_squint_identity_growth"]

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "publish_visual_cases.py"
SAG = ["Sagittal", "1", "1"]
COR = ["Coronal", "1", "1"]
PROCEDURE = "knee.squint-profile/scan-tercile-v1"


def case(case_id="new-acl", study_uid="study-new", subject="acl"):
    return {
        "case_id": case_id,
        "study_uid": study_uid,
        "subject": subject,
        "condition_calls": {"ACL": 1},
        "presentation_scope": {"ACL": "positive_condition_presentation"},
        "profile": {
            "schema": "knee.squint-profile/v1",
            "subject": subject,
            "banks": {
                f"squint/v2/view={json.dumps(SAG, separators=(',', ':'))}/role=object/metric=signal/direction=d/scale=10mm": [
                    2,
                    0,
                    1,
                ]
            },
            "source": {"procedure": PROCEDURE},
        },
        "regions": [],
        "source": {"kind": "native-picture-fixture", "mask_sha256": "a" * 64},
    }


def parent():
    old = case("old", "study-old", "mcl")
    return {
        "schema": "knee.squint-memory/v1",
        "revision": "parent-r1",
        "questions": list(LABELS),
        "cases": [old],
        "object_identity_teaching": {
            "schema": "knee.object-identity-teaching/v1",
            "reader": "earlier reviewer",
            "confirmed_case_ids": ["old"],
            "calls": [
                {
                    "candidate_id": "old",
                    "call": "confirm",
                    "notes": "earlier visual call",
                    "views": [SAG],
                }
            ],
        },
    }


def additions():
    return {
        "schema": SCHEMA,
        "reader": "actual fixture visual reviewer",
        "cases": [case()],
        "calls": [
            {
                "candidate_id": "new-acl",
                "call": "confirm",
                "notes": "Seen in its attachment context",
                "views": [SAG],
            }
        ],
    }


def test_identity_only_case_with_empty_condition_calls_is_confirmed_without_clinical_claims():
    p, a = parent(), additions()
    a["cases"][0]["condition_calls"] = {}
    a["cases"][0]["presentation_scope"] = {}
    before = copy.deepcopy((p, a))

    cases, calls = validate_additions(p, a)

    assert cases[0]["condition_calls"] == {}
    assert cases[0]["presentation_scope"] == {}
    assert calls[0]["views"] == [SAG]
    assert calls[0]["reader"] == a["reader"]
    assert (p, a) == before


def test_identity_only_child_publishes_with_its_view_and_no_invented_full_profile(
    tmp_path,
):
    saved = save_memory(parent(), tmp_path / "parent")
    source = tmp_path / "additions.json"
    a = additions()
    a["cases"][0]["condition_calls"] = {}
    a["cases"][0]["presentation_scope"] = {}
    source.write_text(json.dumps(a))

    result = publish_visual_cases(
        tmp_path / "parent", saved["sha256"], source, tmp_path / "child"
    )

    child = load_memory_snapshot(tmp_path / "child").memory
    added = child["cases"][-1]
    assert result["outcome"] == "visual_child_published"
    assert added["condition_calls"] == {}
    assert "full_profile" not in added and "full_profile_refs" not in added
    assert identity_condition_views(child)["views"][added["case_id"]] == frozenset(
        {tuple(SAG)}
    )
    assert prepare_identity(child)["outcome"] == "prepared"


@pytest.mark.parametrize(
    "change, code",
    [
        (lambda a: a["cases"][0].update(case_id="old"), "visual_case_id_duplicate"),
        (
            lambda a: a["cases"][0].update(study_uid="study-old", subject="mcl"),
            "visual_study_subject_duplicate",
        ),
        (lambda a: a["calls"][0].pop("views"), "visual_call_explicit_views_required"),
        (lambda a: a["calls"][0].update(views=[COR]), "visual_call_view_not_observed"),
        (
            lambda a: a["cases"][0].update(full_profile={"payload_ref": "invented"}),
            "visual_case_full_evidence_not_supplied_by_this_route",
        ),
        (
            lambda a: a["cases"][0].update(full_profile_refs={"acl": {}}),
            "visual_case_full_evidence_not_supplied_by_this_route",
        ),
    ],
)
def test_validator_refuses_duplicate_unasserted_or_full_evidence(change, code):
    a = additions()
    change(a)
    with pytest.raises(VisualTeachingError) as err:
        validate_additions(parent(), a)
    assert err.value.code == code


def test_validator_rejects_duplicate_case_and_study_subject_within_additions():
    for duplicate_id, code in (
        (True, "visual_case_id_duplicate"),
        (False, "visual_study_subject_duplicate"),
    ):
        a = additions()
        second = copy.deepcopy(a["cases"][0])
        if duplicate_id:
            second["study_uid"] = "study-second"
        else:
            second["case_id"] = "second-case"
            second["study_uid"] = a["cases"][0]["study_uid"]
        a["cases"].append(second)
        a["calls"].append({**a["calls"][0], "candidate_id": second["case_id"]})
        with pytest.raises(VisualTeachingError) as err:
            validate_additions(parent(), a)
        assert err.value.code == code


def test_stale_parent_pin_refuses_without_output(tmp_path):
    saved = save_memory(parent(), tmp_path / "parent")
    source = tmp_path / "additions.json"
    source.write_text(json.dumps(additions()))
    output = tmp_path / "child"

    with pytest.raises(VisualTeachingError) as err:
        publish_visual_cases(tmp_path / "parent", "0" * 64, source, output)

    assert err.value.code == "parent_pin_stale"
    assert not output.exists()
    assert (
        hashlib.sha256((tmp_path / "parent/manifest.json").read_bytes()).hexdigest()
        == saved["sha256"]
    )


def test_publication_preserves_signed_parent_cases_and_full_payloads(tmp_path, signed):
    before = signed.parent.path.read_bytes()
    source = tmp_path / "additions.json"
    source.write_text(json.dumps(additions()))

    result = publish_visual_cases(
        signed.parent.path.parent,
        signed.parent.sha256,
        source,
        tmp_path / "visual-child",
    )

    child = load_memory_snapshot(tmp_path / "visual-child").memory
    old = signed.parent.memory
    assert result["outcome"] == "visual_child_published"
    assert child["cases"][:-1] == old["cases"]
    assert child["object_identity_cases"] == old["object_identity_cases"]
    for key in ("full_profile_contexts", "full_profile_payloads"):
        assert child[key] == old[key]
    assert (
        child["object_identity_teaching"]["calls"][:-1]
        == old["object_identity_teaching"]["calls"]
    )
    for key in ("negative_case_ids", "negative_views", "alternative_positives"):
        assert (
            child["object_identity_teaching"][key]
            == old["object_identity_teaching"][key]
        )
    assert signed.parent.path.read_bytes() == before
    assert child["cases"][-1]["direct_visual_teaching"]["call"]["views"] == [SAG]
    assert "full_profile" not in child["cases"][-1]
    assert prepare_identity(child)["outcome"] == "prepared"


def test_cli_help_keeps_the_existing_public_flags():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    for flag in (
        "--parent",
        "--parent-sha256",
        "--additions",
        "--output",
        "--prepare-recall",
    ):
        assert flag in result.stdout
