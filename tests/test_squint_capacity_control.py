"""Two-sign evidence for changing query location and nothing downstream."""

from __future__ import annotations

import argparse
import copy
import csv
import json
from pathlib import Path

import numpy as np
import pytest
from pydicom.uid import generate_uid
from squint_upgrade_fixtures import SERIES_UID, STUDY_UID, study_record
from test_squint_profiles import _write_dicom, _write_tables

from knee.diagnosis import squint_locator
from knee.diagnosis.squint_capacity_control import (
    CONTROL,
    CapacityControlError,
    locate_teacher_objects,
    run_teacher_capacity,
    teacher_addresses,
)
from knee.diagnosis.squint_configurations import configuration_profile
from knee.diagnosis.squint_locator import prepare_recall, recall_object
from knee.diagnosis.squint_memory import save_memory
from knee.diagnosis.squint_profiles import (
    merge_profiles,
    profile_window,
    read_study_squints,
    refine_window,
)
from knee.json_store import load_json
from knee.study.tables import LABELS, TRAIN_COLUMNS
from scripts.evaluate_squint_capacity import evaluate_capacity, main


def _native_study(root: Path):
    uid, series_uid = str(generate_uid()), str(generate_uid())
    path = root / "train_series" / uid / series_uid
    path.mkdir(parents=True)
    pixels = np.arange(64 * 64).reshape(64, 64)
    _write_dicom(path / "one.dcm", uid, series_uid, pixels, spacing_rc=(1.0, 1.0))
    _write_tables(root, uid, series_uid)
    return read_study_squints(root, uid)


def _region(series_uid=SERIES_UID, window=(1, 2, 3, 5, 3, 5)):
    return {
        "series_uid": series_uid,
        "source_slice": window[0],
        "source_window": list(window),
        "extent_source": "retained_object_support",
    }


def _case(uid, subject, profile, regions, sign=1):
    return {
        "case_id": f"case:{uid}:{subject}",
        "study_uid": uid,
        "subject": subject,
        "condition_calls": {"ACL": sign},
        "profile": profile,
        "regions": regions,
    }


def test_teacher_reads_exact_bootstrap_writer_and_merges_regions(tmp_path):
    study = _native_study(tmp_path)
    uid = study["study_uid"]
    series = study["series"][0]
    windows = [(0, 1, 1, 3, 1, 3), (0, 1, 4, 6, 4, 6)]
    regions = [_region(series["series_uid"], w) for w in windows]
    result = locate_teacher_objects(study, {uid: {"acl": regions}})
    expected = merge_profiles(
        [
            merge_profiles(
                (
                    profile_window(series, w, subject="acl"),
                    refine_window(series, w, subject="acl", tile_mm=2.0),
                ),
                subject="acl",
            )
            for w in windows
        ],
        subject="acl",
    )
    assert result["objects"]["acl"]["profile"] == expected
    assert result["objects"]["acl"]["regions"] == regions
    assert any(name.endswith("scale=2mm") for name in expected["banks"])
    assert any(name.endswith("scale=10mm") for name in expected["banks"])


def test_moving_teacher_address_changes_query_but_labels_and_stored_counts_do_not(
    tmp_path,
):
    study = _native_study(tmp_path)
    uid = study["study_uid"]
    series_uid = study["series"][0]["series_uid"]
    memory = {
        "cases": [
            _case(
                uid,
                "acl",
                {"banks": {"poison": [99, 0, 0]}},
                [_region(series_uid, (0, 1, 1, 3, 1, 3))],
            )
        ]
    }
    addresses = teacher_addresses(memory)
    original = locate_teacher_objects(study, addresses)["objects"]["acl"]["profile"]
    memory["cases"][0]["condition_calls"] = {"ACL": -1}
    memory["cases"][0]["profile"]["banks"] = {"another_poison": [0, 99, 0]}
    same = locate_teacher_objects(study, teacher_addresses(memory))["objects"]["acl"][
        "profile"
    ]
    assert same == original
    memory["cases"][0]["regions"] = [_region(series_uid, (0, 1, 4, 6, 4, 6))]
    moved = locate_teacher_objects(study, teacher_addresses(memory))["objects"]["acl"][
        "profile"
    ]
    assert moved["banks"] != original["banks"]
    # Address book is a copy; changing teacher memory cannot move an existing query.
    assert (
        locate_teacher_objects(study, addresses)["objects"]["acl"]["profile"]
        == original
    )


def test_unretained_series_is_unavailable_never_a_guessed_window(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("writer ran on a guessed series/window")

    monkeypatch.setattr(
        "knee.diagnosis.squint_capacity_control.profile_window", forbidden
    )
    result = locate_teacher_objects(
        study_record(), {STUDY_UID: {"acl": [_region("absent")]}}
    )
    acl = result["objects"]["acl"]
    assert acl["status"] == "unavailable"
    assert acl["reason"] == "teacher_series_unavailable"
    assert acl["profile"] is None
    assert acl["regions"] == []
    assert acl["evidence"]["region_readings"] == [
        {"code": "teacher_series_unavailable", "region": _region("absent")}
    ]
    assert result["objects"]["mcl"]["reason"] == "teacher_regions_unavailable"


@pytest.mark.parametrize(
    "region,reason",
    [
        (None, "teacher_region_invalid"),
        ({"series_uid": SERIES_UID}, "teacher_window_invalid"),
        (_region(window=(1, 1, 3, 5, 3, 5)), "teacher_window_out_of_bounds_or_empty"),
        (_region(window=(1, 4, 3, 5, 3, 5)), "teacher_window_out_of_bounds_or_empty"),
        ({**_region(), "source_slice": 0}, "teacher_key_slice_window_mismatch"),
        ({**_region(), "source_slice": None}, "teacher_key_slice_unavailable"),
        (
            {**_region(), "source_window": [True, 2, 3, 5, 3, 5]},
            "teacher_window_invalid",
        ),
    ],
)
def test_invalid_or_empty_teacher_addresses_have_named_refusals(region, reason):
    result = locate_teacher_objects(study_record(), {STUDY_UID: {"acl": [region]}})
    assert result["objects"]["acl"]["reason"] == reason
    assert result["objects"]["acl"]["profile"] is None


def test_missing_teacher_or_expired_deadline_never_becomes_a_normal_reading():
    missing = locate_teacher_objects(study_record(), {})
    assert all(item["profile"] is None for item in missing["objects"].values())
    expired = locate_teacher_objects(
        study_record(), {STUDY_UID: {"acl": [_region()]}}, deadline=0.0
    )
    assert expired["objects"]["acl"]["reason"] == "teacher_deadline_before_read"
    assert expired["objects"]["acl"]["profile"] is None
    with pytest.raises(CapacityControlError, match="teacher_study_identity_invalid"):
        locate_teacher_objects(None, {})


def test_missing_native_refinement_retains_coarse_reading_but_not_a_paired_query():
    result = locate_teacher_objects(study_record(), {STUDY_UID: {"acl": [_region()]}})
    acl = result["objects"]["acl"]
    assert acl["status"] == "unavailable"
    assert acl["profile"] is None
    reading = acl["evidence"]["region_readings"][0]
    assert reading["code"] == "teacher_refinement_unavailable"
    assert reading["coarse_profile"]["banks"]


def _run_fixture(root):
    study = _native_study(root)
    uid = study["study_uid"]
    series = study["series"][0]
    region = _region(series["series_uid"], (0, 1, 1, 3, 1, 3))
    profile = locate_teacher_objects(study, {uid: {"acl": [region]}})["objects"]["acl"][
        "profile"
    ]
    cases = []
    for case_uid, sign in ((uid, 1), ("peer-positive", 1), ("peer-negative", -1)):
        p = copy.deepcopy(profile)
        if sign < 0:
            p["banks"] = {name: counts[::-1] for name, counts in p["banks"].items()}
        cases.append(_case(case_uid, "acl", p, [region], sign))
        config = configuration_profile({"acl": p}, "ACL")
        cases.append(_case(case_uid, "diagnosis/ACL", config, [region], sign))
    memory = {
        "schema": "knee.squint-memory/v1",
        "revision": "control-fixture",
        "questions": list(LABELS),
        "cases": cases,
        "censors": [
            {
                "censor_id": "own-censor",
                "question": "ACL",
                "answer": 1,
                "source": {"study_uid": uid},
                "profile": profile,
                "radius_numerator": 0,
                "radius_denominator": 1,
            }
        ],
    }
    prepared = prepare_recall(memory)
    save_memory(memory, root / "memory", prepared_recall=prepared)
    template = root / "template.csv"
    with template.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("StudyInstanceUID", *LABELS))
        writer.writerow((uid, *("" for _ in LABELS)))
    args = argparse.Namespace(
        diagnostic_mode="capacity",
        diagnostic_memory=root / "memory",
        diagnostic_output=root / "diagnostics",
        diagnostic_submission_template=template,
        root=root,
        study_uid=[uid],
        workers=2,
        squint_time_limit=120.0,
    )
    return uid, memory, profile, prepared, args


def _term_ids(value):
    ids = set()
    if isinstance(value, dict):
        for name, child in value.items():
            if name in ("case_id", "censor_id"):
                ids.add(child)
            elif name in (
                "case_ids",
                "population_case_ids",
                "speaking_case_ids",
                "nearest_positive_case_ids",
                "nearest_negative_case_ids",
            ):
                ids.update(child)
            else:
                ids.update(_term_ids(child))
    elif isinstance(value, list):
        for child in value:
            ids.update(_term_ids(child))
    return ids


def test_real_coordinator_excludes_own_object_configuration_censor_and_preparation(
    tmp_path,
):
    uid, memory, profile, prepared, args = _run_fixture(tmp_path)
    unexcluded = recall_object(profile, {**memory, "prepared_recall": prepared}, "ACL")
    assert f"case:{uid}:acl" in _term_ids(unexcluded)
    assert "own-censor" in _term_ids(unexcluded)
    locator_before = squint_locator.locate_objects
    result = run_teacher_capacity(args)
    assert squint_locator.locate_objects is locator_before
    record = load_json(
        args.diagnostic_output / result["work"]["studies"][0]["evidence_path"]
    )
    ids = _term_ids(record["questions"])
    assert f"case:{uid}:acl" not in ids
    assert f"case:{uid}:diagnosis/ACL" not in ids
    assert "own-censor" not in ids
    assert "case:peer-positive:acl" in ids
    assert "case:peer-negative:diagnosis/ACL" in ids
    assert record["capacity_exclusion"]["excluded_case_count"] == 2
    assert record["capacity_exclusion"]["excluded_censor_count"] == 1
    assert (
        result["capacity_control"]["exclusion_checks"][uid]["code"] == "study_excluded"
    )
    assert record["work"]["full_anatomy_runs"] == 0
    report = evaluate_capacity(args.diagnostic_output, tmp_path / "train.csv")
    assert report["capacity_control"]["location_mode"] == CONTROL
    assert report["per_object"]["mcl"]["location_reasons"] == {
        "teacher_regions_unavailable": 1
    }


def test_script_teacher_mode_reaches_real_capacity_runner(tmp_path):
    uid, _, _, _, args = _run_fixture(tmp_path)
    # The truth source is used only after inference and may contain any calls.
    labels = tmp_path / "truth.csv"
    with labels.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(TRAIN_COLUMNS)
        writer.writerow((uid, "independent truth", *("1" for _ in LABELS)))
    output, markdown = tmp_path / "report.json", tmp_path / "report.md"
    assert (
        main(
            [
                "--teacher-location",
                "--root",
                str(tmp_path),
                "--memory",
                str(args.diagnostic_memory),
                "--template",
                str(args.diagnostic_submission_template),
                "--run",
                str(args.diagnostic_output),
                "--labels",
                str(labels),
                "--output",
                str(output),
                "--markdown",
                str(markdown),
                "--workers",
                "2",
                "--study-uid",
                uid,
            ]
        )
        == 0
    )
    report = json.loads(output.read_text())
    assert report["run"]["study_uids"] == [uid]
    assert report["capacity_control"]["location_mode"] == CONTROL
    assert "Per-object abstention causes" in markdown.read_text()


def test_control_rejects_inference_and_restores_locator_after_failure(
    tmp_path, monkeypatch
):
    _, _, _, _, args = _run_fixture(tmp_path)
    args.diagnostic_mode = "infer"
    with pytest.raises(
        CapacityControlError, match="teacher_location_requires_capacity"
    ):
        run_teacher_capacity(args)
    args.diagnostic_mode = "capacity"
    before = squint_locator.locate_objects

    def fail(*a, **kw):
        assert squint_locator.locate_objects is not before
        raise RuntimeError("coordinator failure")

    monkeypatch.setattr("knee.diagnosis.squint_pipeline.run_squint_cli", fail)
    with pytest.raises(RuntimeError, match="coordinator failure"):
        run_teacher_capacity(args)
    assert squint_locator.locate_objects is before
