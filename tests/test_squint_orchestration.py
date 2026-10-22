from __future__ import annotations

import copy
import csv
import json
import sys
import types
from pathlib import Path

import numpy as np
import pytest
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

import knee.diagnosis as diagnosis_package
from knee.diagnosis import (
    squint_configurations,
    squint_pipeline,
    squint_profiles,
    squint_residual,
)
from knee.diagnosis.squint_contracts import serialize_condition_value
from knee.diagnosis.squint_interfaces import (
    ROLE_CONTEXT,
    ROLE_OBJECT,
    TERRITORY_PROCEDURE,
)
from knee.diagnosis.squint_profiles import (
    merge_profiles,
    profile_window,
    read_study_squints,
)
from knee.diagnosis.squint_residual import held_readings

LABELS = (
    "ACL",
    "MCL",
    "Medial Meniscus",
    "Lateral Meniscus",
    "Medial OA",
    "Lateral OA",
    "PF OA",
    "Effusion",
    "Synovitis",
    "Baker's",
    "Contusion",
    "Fracture",
)


def _write_dicom(path: Path, study_uid: str, series_uid: str) -> None:
    pixels = np.arange(256, dtype=np.uint16).reshape(16, 16)
    meta = FileMetaDataset()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    meta.MediaStorageSOPClassUID = generate_uid()
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.ImplementationClassUID = generate_uid()
    dataset = FileDataset(str(path), {}, file_meta=meta, preamble=b"\0" * 128)
    dataset.SOPClassUID = meta.MediaStorageSOPClassUID
    dataset.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    dataset.StudyInstanceUID = study_uid
    dataset.SeriesInstanceUID = series_uid
    dataset.Modality = "MR"
    dataset.Rows, dataset.Columns = pixels.shape
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = 16
    dataset.BitsStored = 16
    dataset.HighBit = 15
    dataset.PixelRepresentation = 0
    dataset.ImagePositionPatient = [0.0, 0.0, 0.0]
    dataset.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    dataset.PixelSpacing = [1.0, 1.0]
    dataset.PixelData = pixels.astype("<u2").tobytes()
    dataset.save_as(path, enforce_file_format=True, little_endian=True)


def _write_tables(root: Path, uid: str, series_uid: str) -> None:
    with (root / "train.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("StudyInstanceUID", "Report", *LABELS))
        writer.writerow((uid, "", *([""] * len(LABELS))))
    with (root / "train_series.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            (
                "StudyInstanceUID",
                "SeriesInstanceUID",
                "Fluid_Sensitive",
                "Fat_Suppression",
                "Anatomical_Plane",
            )
        )
        writer.writerow((uid, series_uid, "1", "1", "Sagittal"))
    with (root / "test.csv").open("w", newline="", encoding="utf-8") as stream:
        csv.writer(stream).writerow(("StudyInstanceUID",))
    with (root / "test_series.csv").open("w", newline="", encoding="utf-8") as stream:
        csv.writer(stream).writerow(
            (
                "StudyInstanceUID",
                "SeriesInstanceUID",
                "Fluid_Sensitive",
                "Fat_Suppression",
                "Anatomical_Plane",
            )
        )


def _study(tmp_path: Path) -> tuple[str, dict]:
    uid, series_uid = generate_uid(), generate_uid()
    series_dir = tmp_path / "train_series" / uid / series_uid
    series_dir.mkdir(parents=True)
    _write_dicom(series_dir / "one.dcm", uid, series_uid)
    _write_tables(tmp_path, uid, series_uid)
    return uid, read_study_squints(tmp_path, uid, tile_mm=10.0)


def _located(series: dict, profile: dict, subject: str = "femur") -> dict:
    return {
        subject: {
            "status": "proposal",
            "profile": profile,
            "regions": [
                {
                    "series_uid": series["series_uid"],
                    "window": (0, 1, 0, 1, 0, 1),
                }
            ],
        }
    }


def test_bounded_observation_refines_one_located_region_and_shares_result(
    monkeypatch, tmp_path
):
    uid, study = _study(tmp_path)
    series = study["series"][0]
    coarse = profile_window(series, (0, 1, 0, 1, 0, 1), subject="femur")
    objects = _located(series, coarse)
    real_refine = squint_profiles.refine_window
    calls = []

    def counted_refine(*args, **kwargs):
        calls.append((args[1], kwargs["subject"], kwargs["tile_mm"]))
        return real_refine(*args, **kwargs)

    monkeypatch.setattr(squint_profiles, "refine_window", counted_refine)
    attempted = set()

    measured = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, attempted, None
    )
    shared = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, attempted, None
    )

    assert measured["code"] == "measured"
    assert shared == {
        "code": "shared_observation_already_available",
        "subject": "femur",
    }
    assert calls == [((0, 1, 0, 1, 0, 1), "femur", 2.0)]
    banks = objects["femur"]["profile"]["banks"]
    assert any("scale=10mm" in bank for bank in banks)
    assert any("scale=2mm" in bank for bank in banks)
    assert objects["femur"]["profile"]["source"]["api"].endswith("merge_profiles/v1")
    assert measured["regions"] == [
        {"series_uid": series["series_uid"], "window": [0, 1, 0, 1, 0, 1]}
    ]
    assert study["study_uid"] == uid


@pytest.mark.parametrize(
    "coarse_window",
    [None, (0, 1, 1, 2, 1, 2)],
    ids=["no_profile", "different_window"],
)
def test_v1_generic_refinement_requires_the_exact_held_coarse_reading(
    monkeypatch, tmp_path, coarse_window
):
    _, study = _study(tmp_path)
    series = study["series"][0]
    coarse = (
        None
        if coarse_window is None
        else profile_window(series, coarse_window, subject="femur")
    )
    objects = _located(series, coarse)
    calls = []
    monkeypatch.setattr(
        squint_profiles,
        "refine_window",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    attempted = set()

    observed = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, attempted, None
    )

    assert observed["code"] == "no_compatible_bounded_reading"
    assert observed["unavailable_regions"] == [
        {
            "series_uid": series["series_uid"],
            "window": [0, 1, 0, 1, 0, 1],
            "reason": "coarse_reading_not_held",
        }
    ]
    assert calls == []
    assert objects["femur"]["profile"] is coarse
    assert attempted == set()


def test_bounded_observation_deadline_and_missing_region_do_not_read(
    monkeypatch, tmp_path
):
    _, study = _study(tmp_path)
    series = study["series"][0]
    coarse = profile_window(series, (0, 1, 0, 1, 0, 1), subject="femur")
    objects = _located(series, coarse)
    calls = []
    monkeypatch.setattr(
        squint_profiles,
        "refine_window",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    deadline = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, set(), 0.0
    )
    missing_subject = squint_pipeline._bounded_observation(
        {"object": "tibia"}, study, objects, set(), None
    )
    missing_region = squint_pipeline._bounded_observation(
        {"object": "femur"},
        study,
        {"femur": {"status": "unresolved_missing_reading", "regions": []}},
        set(),
        None,
    )

    assert deadline["code"] == "deadline_before_zoom"
    assert missing_subject["code"] == "object_region_unavailable"
    assert missing_region["code"] == "no_compatible_bounded_reading"
    assert calls == []


def test_failed_or_expired_zoom_does_not_claim_a_shared_measurement(tmp_path):
    _, study = _study(tmp_path)
    series = study["series"][0]
    coarse = profile_window(series, (0, 1, 0, 1, 0, 1), subject="femur")
    objects = _located(series, coarse)
    measured = set()
    expired = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, measured, 0.0
    )
    assert expired["code"] == "deadline_before_zoom"
    assert "femur" not in measured
    regions = objects["femur"]["regions"]
    objects["femur"]["regions"] = []
    unavailable = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, measured, None
    )
    assert unavailable["code"] == "no_compatible_bounded_reading"
    assert "femur" not in measured
    objects["femur"]["regions"] = regions
    recovered = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, measured, None
    )
    assert recovered["code"] == "measured"
    assert "femur" in measured


def test_infer_study_reuses_fine_profile_for_later_question_without_full_rebuild(
    monkeypatch, tmp_path
):
    uid, study = _study(tmp_path)
    series = study["series"][0]
    coarse = profile_window(series, (0, 1, 0, 1, 0, 1), subject="femur")
    objects = _located(series, coarse)
    read_calls = []
    recall_calls = []
    combine_calls = []

    monkeypatch.setattr(
        squint_profiles,
        "read_study_squints",
        lambda root, study_uid, *, io_workers: read_calls.append(study_uid) or study,
    )

    def recall(profile, memory, *, question, exclude_study_uid):
        recall_calls.append((question, set(profile["banks"])))
        return {"outcome": "proposal", "case_terms": [], "speaking_calls": []}

    # _recall_question is the production adapter around recall_object; exercise that
    # adapter by replacing its imported locator module with a spy implementation.
    locator = types.ModuleType("knee.diagnosis.squint_locator")
    locator.locate_objects = lambda current, memory, *, deadline: {"objects": objects}
    locator.recall_object = recall
    monkeypatch.setitem(sys.modules, locator.__name__, locator)
    monkeypatch.setattr(diagnosis_package, "squint_locator", locator)

    question_module = types.ModuleType("knee.diagnosis.declarations")
    question_module.QUESTIONS = (
        types.SimpleNamespace(
            question_id="Fracture",
            subject="diagnosis/Fracture",
            objects=("femur",),
        ),
        types.SimpleNamespace(
            question_id="Contusion",
            subject="diagnosis/Contusion",
            objects=("femur",),
        ),
    )
    question_module.question_for = lambda question_id: next(
        question
        for question in question_module.QUESTIONS
        if question.question_id == question_id
    )
    monkeypatch.setitem(sys.modules, question_module.__name__, question_module)
    monkeypatch.setattr(diagnosis_package, "declarations", question_module)
    monkeypatch.setattr(
        squint_configurations, "question_for", question_module.question_for
    )
    contracts = types.ModuleType("knee.diagnosis.squint_contracts")

    def combine(question_id, evidence):
        combine_calls.append((question_id, set(objects["femur"]["profile"]["banks"])))
        return {
            "outcome": "open",
            "observation_requests": [{"object": "femur"}],
        }

    contracts.combine_condition = combine
    contracts.rank_condition = lambda finding: {"value": 0.5}
    contracts.serialize_condition_value = serialize_condition_value
    monkeypatch.setitem(sys.modules, contracts.__name__, contracts)
    monkeypatch.setattr(diagnosis_package, "squint_contracts", contracts)

    record = squint_pipeline.infer_study(tmp_path, uid, {"revision": "r1"})

    assert read_calls == [uid]
    assert record["work"]["full_anatomy_runs"] == 0
    assert record["work"]["bounded_zoom_runs"] == 1
    assert [item["code"] for item in record["observations"]] == [
        "measured",
        "shared_observation_already_available",
    ]
    assert any("scale=10mm" in bank for bank in objects["femur"]["profile"]["banks"])
    assert any("scale=2mm" in bank for bank in objects["femur"]["profile"]["banks"])
    assert any(
        "scale=2mm" in bank for _question, banks in recall_calls for bank in banks
    )
    assert any(
        "scale=2mm" in bank for _question, banks in combine_calls for bank in banks
    )


# ---------------------------------------------------------------------------
# the dispatcher's vocabulary: null, empty, malformed and late requests are named
# ---------------------------------------------------------------------------


def _boom(*args, **kwargs):
    raise AssertionError("no reading may be made here")


def _no_reading(monkeypatch):
    for module, name in (
        (squint_profiles, "refine_window"),
        (squint_profiles, "refine_territory"),
        (squint_residual, "own_outline"),
        (squint_residual, "run_residual"),
    ):
        monkeypatch.setattr(module, name, _boom)


@pytest.mark.parametrize(
    ("request_value", "code", "reason"),
    [
        (None, "request_invalid", "request_not_a_mapping"),
        ([], "request_invalid", "request_not_a_mapping"),
        ("femur", "request_invalid", "request_not_a_mapping"),
        (7, "request_invalid", "request_not_a_mapping"),
        ({}, "object_region_unavailable", "request_names_no_object"),
        ({"object": None}, "object_region_unavailable", "request_names_no_object"),
        ({"object": 5}, "object_region_unavailable", "request_names_no_object"),
        (
            {"subject": ["femur"]},
            "object_region_unavailable",
            "request_names_no_object",
        ),
        ({"object": ""}, "object_region_unavailable", "object_not_located"),
        ({"object": "tibia"}, "object_region_unavailable", "object_not_located"),
        ({"object": "femur", "lens": 5}, "request_invalid", "lens_not_a_name"),
        ({"object": "femur", "lens": ""}, "request_invalid", "lens_not_a_name"),
        ({"object": "femur", "lens": None}, "request_invalid", "lens_not_a_name"),
    ],
)
def test_null_empty_and_malformed_requests_are_named_and_read_nothing(
    monkeypatch, tmp_path, request_value, code, reason
):
    _, study = _study(tmp_path)
    series = study["series"][0]
    objects = _located(
        series, profile_window(series, (0, 1, 0, 1, 0, 1), subject="femur")
    )
    _no_reading(monkeypatch)
    observed = squint_pipeline._bounded_observation(
        request_value, study, objects, set(), None
    )
    assert (observed["code"], observed["reason"]) == (code, reason)
    json.dumps(observed)


@pytest.mark.parametrize(
    ("objects", "reason"),
    [
        (None, "objects_not_a_mapping"),
        ([], "objects_not_a_mapping"),
        ({"femur": None}, "object_record_invalid"),
        ({"femur": "located"}, "object_record_invalid"),
    ],
)
def test_malformed_located_objects_are_named_and_read_nothing(
    monkeypatch, tmp_path, objects, reason
):
    _, study = _study(tmp_path)
    _no_reading(monkeypatch)
    observed = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, set(), None
    )
    assert (observed["code"], observed["reason"]) == (
        "object_region_unavailable",
        reason,
    )


@pytest.mark.parametrize("study", [None, [], "study"])
def test_a_missing_study_is_named_and_reads_nothing(monkeypatch, tmp_path, study):
    _, real = _study(tmp_path)
    series = real["series"][0]
    objects = _located(
        series, profile_window(series, (0, 1, 0, 1, 0, 1), subject="femur")
    )
    _no_reading(monkeypatch)
    observed = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, set(), None
    )
    assert (observed["code"], observed["reason"]) == (
        "object_region_unavailable",
        "study_not_a_mapping",
    )


def test_regions_the_dispatcher_cannot_read_are_named_not_skipped(tmp_path):
    _, study = _study(tmp_path)
    series = study["series"][0]
    window = (0, 1, 0, 1, 0, 1)
    coarse = profile_window(series, window, subject="femur")
    objects = {
        "femur": {
            "status": "proposal",
            "profile": coarse,
            "regions": [
                "not a region",
                {"series_uid": "another-series", "window": window},
                {"series_uid": series["series_uid"], "window": [0, 1, 0]},
                {"series_uid": series["series_uid"], "window": (0.0, 1, 0, 1, 0, 1)},
            ],
        }
    }
    observed = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, set(), None
    )
    assert observed["code"] == "no_compatible_bounded_reading"
    assert observed["reason"] == "region_unavailable"
    assert [item["reason"] for item in observed["unavailable_regions"]] == [
        "region_malformed",
        "series_not_in_study",
        "region_window_invalid",
        "region_window_invalid",
    ]
    assert objects["femur"]["profile"] is coarse
    assert observed["held_regions"] == []
    json.dumps(observed)


def test_a_refused_refinement_is_named_and_leaves_the_reading_as_it_was(tmp_path):
    _, study = _study(tmp_path)
    series = study["series"][0]
    window = (0, 1, 0, 1, 0, 1)
    coarse = profile_window(series, window, subject="femur")
    objects = _located(series, coarse)
    study["series"] = [{**series, "native_series": None}]
    observed = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, set(), None
    )
    assert observed["code"] == "no_compatible_bounded_reading"
    assert observed["unavailable_regions"] == [
        {
            "series_uid": series["series_uid"],
            "window": list(window),
            "reason": "refinement_refused:squint_refine_native_series_unavailable",
        }
    ]
    assert objects["femur"]["profile"] is coarse


def test_a_deadline_reached_between_regions_names_each_region_left_unread(
    monkeypatch, tmp_path
):
    _, study = _study(tmp_path)
    series = study["series"][0]
    first, second = (0, 1, 0, 1, 0, 1), (0, 1, 1, 2, 1, 2)
    coarse = merge_profiles(
        [
            profile_window(series, first, subject="femur"),
            profile_window(series, second, subject="femur"),
        ],
        subject="femur",
    )
    objects = {
        "femur": {
            "status": "proposal",
            "profile": coarse,
            "regions": [
                {"series_uid": series["series_uid"], "window": first},
                {"series_uid": series["series_uid"], "window": second},
            ],
        }
    }
    clock = {"now": 0.0}
    real_refine = squint_profiles.refine_window

    def refine_then_expire(*args, **kwargs):
        clock["now"] = 20.0
        return real_refine(*args, **kwargs)

    monkeypatch.setattr(squint_profiles, "refine_window", refine_then_expire)
    monkeypatch.setattr(squint_pipeline.time, "monotonic", lambda: clock["now"])
    attempted: set = set()
    observed = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, attempted, 10.0
    )
    assert observed["code"] == "measured"
    assert observed["regions"] == [
        {"series_uid": series["series_uid"], "window": list(first)}
    ]
    assert observed["unavailable_regions"] == [
        {
            "series_uid": series["series_uid"],
            "window": list(second),
            "reason": "deadline_before_zoom",
        }
    ]
    assert "femur" in attempted


def test_a_deadline_reached_after_admission_but_before_any_read_is_named(
    monkeypatch, tmp_path
):
    _, study = _study(tmp_path)
    series = study["series"][0]
    window = (0, 1, 0, 1, 0, 1)
    coarse = profile_window(series, window, subject="femur")
    objects = _located(series, coarse)
    _no_reading(monkeypatch)
    calls = {"n": 0}

    def clock():
        calls["n"] += 1
        return 0.0 if calls["n"] == 1 else 20.0  # admitted, then late for the read

    monkeypatch.setattr(squint_pipeline.time, "monotonic", clock)
    attempted: set = set()
    observed = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, attempted, 10.0
    )
    assert observed["code"] == "deadline_before_zoom"
    assert observed["unavailable_regions"] == [
        {
            "series_uid": series["series_uid"],
            "window": list(window),
            "reason": "deadline_before_zoom",
        }
    ]
    assert objects["femur"]["profile"] is coarse
    assert attempted == set()  # a late, unread zoom claims no shared measurement


# ---------------------------------------------------------------------------
# territory-v2 readings: the paired finer reading over the region's own territory
# ---------------------------------------------------------------------------


def _located_bone(tmp_path):
    """A femur located as S1 locates one: a territory-v2 pair and region territory records."""
    from knee.diagnosis import squint_locator
    from tests.test_squint_v2_location import _anchor, _case, _native_bone

    series, leg, territory = _native_bone(tmp_path)
    coarse = squint_profiles.profile_territory(series, territory, leg, subject="femur")
    study = {
        "study_uid": territory["study_uid"],
        "series": [series],
        "leg_maps": {series["series_uid"]: leg},
        "anchors": {"femur": _anchor(series, territory)},
    }
    located = squint_locator.locate_objects(study, {"cases": [_case(coarse, "femur")]})
    return study, series, leg, located["objects"]["femur"], coarse


def _watch_territory_refinement(monkeypatch):
    calls = []
    real = squint_profiles.refine_territory

    def watched(*args, **kwargs):
        calls.append((args, kwargs))
        return real(*args, **kwargs)

    monkeypatch.setattr(squint_profiles, "refine_territory", watched)
    # A territory reading is never extended with the v1 writer's renamed 2 mm reading.
    monkeypatch.setattr(squint_profiles, "refine_window", _boom)
    return calls


BONE_WINDOW = [0, 1, 3, 5, 3, 5]


def test_a_territory_reading_without_its_fine_pair_gets_it_over_its_own_territory(
    tmp_path, monkeypatch
):
    study, series, leg, located, coarse = _located_bone(tmp_path)
    pair = located["profile"]  # what S1 wrote: 10 mm and 2 mm over the territory
    assert any("scale=2mm" in name for name in pair["banks"])
    assert not any("scale=2mm" in name for name in coarse["banks"])
    calls = _watch_territory_refinement(monkeypatch)
    objects = {"femur": {**located, "profile": copy.deepcopy(coarse)}}
    attempted: set = set()
    observed = squint_pipeline._bounded_observation(
        {"object": "femur", "question": "Fracture"}, study, objects, attempted, None
    )
    assert observed["code"] == "measured"
    assert observed["procedure"] == TERRITORY_PROCEDURE
    assert (observed["lens"], observed["tile_mm"]) == ("physical_squint", 2.0)
    assert observed["regions"] == [
        {"series_uid": series["series_uid"], "window": BONE_WINDOW}
    ]
    # Exactly the pair S1 wrote: the 2 mm counts are added once, the 10 mm ones not again.
    profile = objects["femur"]["profile"]
    assert profile["banks"] == pair["banks"]
    assert profile["source"]["procedure"] == TERRITORY_PROCEDURE
    assert {item["scale_mm"] for item in held_readings(profile)} == {10.0, 2.0}
    # Over the supplied territory record, the study's own series and its one leg map.
    assert len(calls) == 1
    (series_arg, territory_arg, leg_arg), kwargs = calls[0]
    assert series_arg is series
    assert leg_arg is leg
    assert territory_arg["origin"] == "anchor_structure"
    assert (
        territory_arg["roles"].tolist() == located["regions"][0]["territory"]["roles"]
    )
    assert kwargs == {"subject": "femur", "tile_mm": 2.0}
    assert "femur" in attempted
    json.dumps(observed)
    # Shared once: another question's request reads nothing more.
    again = squint_pipeline._bounded_observation(
        {"object": "femur", "question": "Contusion"}, study, objects, attempted, None
    )
    assert again == {"code": "shared_observation_already_available", "subject": "femur"}
    assert len(calls) == 1
    assert objects["femur"]["profile"]["banks"] == pair["banks"]


def test_a_held_fine_territory_reading_is_neither_read_nor_added_again(
    tmp_path, monkeypatch
):
    study, series, _leg, located, _coarse = _located_bone(tmp_path)
    calls = _watch_territory_refinement(monkeypatch)
    objects = {"femur": located}
    before = copy.deepcopy(located["profile"])
    attempted: set = set()
    observed = squint_pipeline._bounded_observation(
        {"object": "femur", "question": "Fracture"}, study, objects, attempted, None
    )
    assert observed["code"] == "already_measured"
    assert observed["held_regions"] == [
        {"series_uid": series["series_uid"], "window": BONE_WINDOW}
    ]
    assert calls == []
    assert objects["femur"]["profile"] == before
    assert "femur" in attempted
    shared = squint_pipeline._bounded_observation(
        {"object": "femur", "question": "Contusion"}, study, objects, attempted, None
    )
    assert shared["code"] == "shared_observation_already_available"
    assert objects["femur"]["profile"] == before


def _tied(region: dict) -> dict:
    """A second candidate in the same series: the same window with one object place given up."""
    tied = copy.deepcopy(region)
    for plane in tied["territory"]["roles"]:
        for row in plane:
            for column, value in enumerate(row):
                if value == ROLE_OBJECT:
                    row[column] = ROLE_CONTEXT
                    return tied
    raise AssertionError("the territory has no object place")


def test_a_candidate_the_profile_does_not_hold_is_not_refined_into_it(
    tmp_path, monkeypatch
):
    study, series, _leg, located, coarse = _located_bone(tmp_path)
    pair = located["profile"]
    region = located["regions"][0]
    regions = [region, _tied(region)]
    named = {
        "series_uid": series["series_uid"],
        "window": BONE_WINDOW,
        "reason": "territory_not_held_by_the_profile",
    }
    calls = _watch_territory_refinement(monkeypatch)
    # Coarse reading held: only that territory is paired; the other candidate stays one.
    objects = {
        "femur": {**located, "regions": regions, "profile": copy.deepcopy(coarse)}
    }
    observed = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, set(), None
    )
    assert observed["code"] == "measured"
    assert len(calls) == 1
    assert calls[0][0][1]["roles"].tolist() == region["territory"]["roles"]
    assert objects["femur"]["profile"]["banks"] == pair["banks"]
    assert observed["unavailable_regions"] == [named]
    # The pair already held: nothing is read, and the unheld candidate is still named.
    objects = {"femur": {**located, "regions": regions}}
    held = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, set(), None
    )
    assert held["code"] == "already_measured"
    assert held["unavailable_regions"] == [named]
    assert len(calls) == 1
    assert objects["femur"]["profile"] == pair


@pytest.mark.parametrize(
    ("defect", "reason"),
    [
        ("no_record", "region_without_territory_record"),
        ("series_missing", "series_not_in_study"),
        ("record_invalid", "territory_record_refused:territory_record_invalid"),
        ("no_leg_map", "leg_map_unavailable"),
        ("no_series_scale", "territory_identity_unavailable"),
        (
            "no_native_pixels",
            "refinement_refused:squint_refine_native_series_unavailable",
        ),
    ],
)
def test_no_supplied_compatible_territory_is_a_named_unavailable_and_changes_nothing(
    tmp_path, monkeypatch, defect, reason
):
    study, series, _leg, located, coarse = _located_bone(tmp_path)
    region = copy.deepcopy(located["regions"][0])
    if defect == "no_record":
        del region["territory"]
    elif defect == "series_missing":
        region["series_uid"] = "another-series"
    elif defect == "record_invalid":
        region["territory"]["serialization"] = "another-serialization"
    elif defect == "no_leg_map":
        del series["leg_map"]
        study["leg_maps"] = {}
    elif defect == "no_series_scale":
        context = {k: v for k, v in series["source"].items() if k != "tile_mm"}
        study["series"] = [{**series, "source": context}]
    else:
        study["series"] = [{**series, "native_series": None}]
    _watch_territory_refinement(monkeypatch)
    objects = {
        "femur": {**located, "regions": [region], "profile": copy.deepcopy(coarse)}
    }
    before = copy.deepcopy(objects["femur"]["profile"])
    attempted: set = set()
    observed = squint_pipeline._bounded_observation(
        {"object": "femur", "question": "Fracture"}, study, objects, attempted, None
    )
    assert observed["code"] == "no_compatible_bounded_reading"
    assert observed["reason"] == "territory_unavailable"
    assert [item["reason"] for item in observed["unavailable_regions"]] == [reason]
    assert objects["femur"]["profile"] == before
    assert attempted == set()
    json.dumps(observed)


def test_a_territory_whose_native_mask_was_not_kept_is_not_refined_from_coarse_tiles(
    tmp_path, monkeypatch
):
    from knee.diagnosis.squint_anatomy_locator import territory_record
    from tests.test_squint_v2_location import _native_bone

    series, leg, territory = _native_bone(tmp_path)
    mask = np.zeros((1, 16, 16), dtype=bool)
    mask[0, 4:8, 4:8] = True
    territory["native_support"] = {"mask": mask, "offset_rc": [60, 60], "slices": [0]}
    coarse = squint_profiles.profile_territory(series, territory, leg, subject="femur")
    record = territory_record(territory)
    assert record["native_support_address"]["mask_sha256"]
    assert record["native_support"] is None  # the mask itself is runtime-only
    series["leg_map"] = leg
    study = {
        "study_uid": territory["study_uid"],
        "series": [series],
        "leg_maps": {series["series_uid"]: leg},
    }
    objects = {
        "femur": {
            "status": "proposal",
            "profile": coarse,
            "regions": [
                {
                    "series_uid": series["series_uid"],
                    "view": series["view"],
                    "window": tuple(BONE_WINDOW),
                    "territory": record,
                }
            ],
        }
    }
    calls = _watch_territory_refinement(monkeypatch)
    observed = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, set(), None
    )
    # The territory's coarse object tiles are a different support than its native mask.
    assert observed["code"] == "no_compatible_bounded_reading"
    assert [item["reason"] for item in observed["unavailable_regions"]] == [
        "native_support_mask_not_retained"
    ]
    assert calls == []
    assert objects["femur"]["profile"] is coarse


def test_an_unlocated_territory_object_with_no_held_reading_pairs_nothing(
    tmp_path, monkeypatch
):
    study, _series, _leg, located, _coarse = _located_bone(tmp_path)
    calls = _watch_territory_refinement(monkeypatch)
    objects = {"femur": {**located, "profile": None}}
    observed = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, set(), None
    )
    assert observed["code"] == "no_compatible_bounded_reading"
    assert [item["reason"] for item in observed["unavailable_regions"]] == [
        "territory_not_held_by_the_profile"
    ]
    assert calls == []
    assert objects["femur"]["profile"] is None


# ---------------------------------------------------------------------------
# an open question asks for the paired finer reading of any part, never an outline
# ---------------------------------------------------------------------------


def _stub_module(monkeypatch, name: str, **members) -> types.ModuleType:
    module = types.ModuleType(name)
    vars(module).update(members)
    monkeypatch.setitem(sys.modules, name, module)
    return module


def test_an_open_question_on_a_small_part_reads_the_paired_finer_lens_not_its_outline(
    monkeypatch, tmp_path
):
    uid, study = _study(tmp_path)
    series = study["series"][0]
    coarse = profile_window(series, (0, 1, 0, 1, 0, 1), subject="medial_meniscus")
    objects = _located(series, coarse, "medial_meniscus")
    monkeypatch.setattr(
        squint_profiles,
        "read_study_squints",
        lambda root, study_uid, *, io_workers: study,
    )
    question = types.SimpleNamespace(
        question_id="Medial Meniscus",
        subject="diagnosis/Medial Meniscus",
        objects=("medial_meniscus",),
    )
    _stub_module(
        monkeypatch,
        "knee.diagnosis.squint_locator",
        locate_objects=lambda current, memory, *, deadline: {"objects": objects},
        recall_object=lambda profile, memory, **kwargs: {
            "outcome": "proposal",
            "case_terms": [],
            "speaking_calls": [],
        },
    )
    _stub_module(
        monkeypatch,
        "knee.diagnosis.declarations",
        QUESTIONS=(question,),
        question_for=lambda question_id: question,
    )
    from knee.diagnosis import squint_configurations

    monkeypatch.setattr(squint_configurations, "question_for", lambda _id: question)
    _stub_module(
        monkeypatch,
        "knee.diagnosis.squint_contracts",
        combine_condition=lambda question_id, evidence: {
            "outcome": "open",
            "observation_requests": [
                {
                    "question": question_id,
                    "subject": "medial_meniscus",
                    "kind": "bounded_zoom",
                    "reason": "proposal_without_sourced_trust",
                }
            ],
        },
        rank_condition=lambda finding: {"value": 0.5},
        serialize_condition_value=serialize_condition_value,
    )
    monkeypatch.setattr(squint_residual, "own_outline", _boom)
    monkeypatch.setattr(squint_residual, "run_residual", _boom)

    record = squint_pipeline.infer_study(tmp_path, uid, {"revision": "r1"})

    assert [item["code"] for item in record["observations"]] == ["measured"]
    assert record["observations"][0]["lens"] == "physical_squint"
    assert record["work"]["bounded_zoom_runs"] == 1
    assert record["work"]["own_outline_parts_measured"] == 0
    assert record["work"]["own_outline_native_slices_read"] == 0
    assert any(
        "scale=2mm" in bank
        for bank in record["objects"]["medial_meniscus"]["profile"]["banks"]
    )
    assert "own_outline" not in record["objects"]["medial_meniscus"]


# ---------------------------------------------------------------------------
# squint first: production location holds the 10 mm reading, a question earns the 2 mm
# ---------------------------------------------------------------------------


def _squint_first_run(monkeypatch, tmp_path, study, memory, subject, *, locate=None):
    """infer_study over ``study``, whose two questions each ask for ``subject``.

    Only the question and contract layers are stubbed; location, pairing and merging are
    the real ones. ``events`` records, in order, each recall (with whether the profile it
    was given holds a 2 mm bank), each combination and each call to the 2 mm reader.
    """
    from knee.diagnosis import squint_locator

    events: list[tuple] = []
    monkeypatch.setattr(
        squint_profiles, "read_study_squints", lambda root, uid, *, io_workers: study
    )
    real_refine = squint_profiles.refine_territory

    def refine(series, territory, leg_map, **kwargs):
        events.append(("fine_read", territory["subject"]))
        return real_refine(series, territory, leg_map, **kwargs)

    monkeypatch.setattr(squint_profiles, "refine_territory", refine)

    def recall(profile, memory, *, question, exclude_study_uid):
        fine = any("scale=2mm" in bank for bank in profile["banks"])
        events.append(("recall", profile["subject"], question, fine))
        return {"outcome": "proposal", "case_terms": [], "speaking_calls": []}

    monkeypatch.setattr(squint_locator, "recall_object", recall)
    if locate is not None:
        monkeypatch.setattr(
            squint_locator, "locate_objects", locate(squint_locator.locate_objects)
        )
    question_ids = {
        "femur": ("Fracture", "Contusion"),
        "medial_meniscus": ("Medial Meniscus", "Medial OA"),
    }[subject]
    questions = tuple(
        types.SimpleNamespace(
            question_id=name, subject=f"diagnosis/{name}", objects=(subject,)
        )
        for name in question_ids
    )
    by_id = {question.question_id: question for question in questions}
    _stub_module(
        monkeypatch,
        "knee.diagnosis.declarations",
        QUESTIONS=questions,
        question_for=by_id.__getitem__,
    )
    monkeypatch.setattr(squint_configurations, "question_for", by_id.__getitem__)

    def combine(question_id, evidence):
        events.append(("combine", question_id))
        return {"outcome": "open", "observation_requests": [{"object": subject}]}

    _stub_module(
        monkeypatch,
        "knee.diagnosis.squint_contracts",
        combine_condition=combine,
        rank_condition=lambda finding: {"value": 0.5},
        serialize_condition_value=serialize_condition_value,
    )
    record = squint_pipeline.infer_study(tmp_path, study["study_uid"], memory)
    return record, events


def _bone_in_a_study(tmp_path):
    from tests.test_squint_v2_location import _anchor, _case, _native_bone

    series, leg, territory = _native_bone(tmp_path)
    coarse = squint_profiles.profile_territory(series, territory, leg, subject="femur")
    study = {
        "study_uid": territory["study_uid"],
        "series": [series],
        "leg_maps": {series["series_uid"]: leg},
        "anchors": {"femur": _anchor(series, territory)},
    }
    return study, {"revision": "r1", "cases": [_case(coarse, "femur")]}


def _recalls_of(events, subject):
    return [event for event in events if event[:2] == ("recall", subject)]


def test_production_locates_on_the_10mm_reading_and_a_question_earns_the_2mm_once(
    monkeypatch, tmp_path
):
    from knee.diagnosis import squint_locator

    study, memory = _bone_in_a_study(tmp_path)
    # What the legacy, paired location writes for this bone.
    paired = squint_locator.locate_objects(study, memory)["objects"]["femur"]["profile"]
    assert {item["scale_mm"] for item in held_readings(paired)} == {10.0, 2.0}

    record, events = _squint_first_run(monkeypatch, tmp_path, study, memory, "femur")

    # The 2 mm reader ran once, after the first question was recalled on the 10 mm
    # reading alone and before the recall that carries it.
    reads = [i for i, event in enumerate(events) if event[0] == "fine_read"]
    assert [events[i] for i in reads] == [("fine_read", "femur")]
    before = _recalls_of(events[: reads[0]], "femur")
    after = _recalls_of(events[reads[0] :], "femur")
    assert before and not any(event[3] for event in before)
    assert after and all(event[3] for event in after)
    assert before[0][2] == "Fracture"
    # The second question asks for the same bone: its reading is shared, not repeated.
    assert [item["code"] for item in record["observations"]] == [
        "measured",
        "shared_observation_already_available",
    ]
    assert record["observations"][0]["regions"] == [
        {
            "series_uid": study["series"][0]["series_uid"],
            "window": [0, 1, 3, 5, 3, 5],
        }
    ]
    assert _recalls_of(events[reads[0] :], "femur")[-1][2] == "Contusion"
    # Exactly the pair the legacy location wrote, with its 2 mm counts added once.
    profile = record["objects"]["femur"]["profile"]
    assert profile["banks"] == paired["banks"]
    assert held_readings(profile) == held_readings(paired)
    work = record["work"]
    assert (work["location_fine_readings"], work["paired_fine_readings"]) == (0, 1)
    assert (work["bounded_zoom_runs"], work["full_anatomy_runs"]) == (1, 0)
    json.dumps(record, allow_nan=False)


def test_a_paired_location_is_held_at_once_and_no_question_reads_it_again(
    monkeypatch, tmp_path
):
    from knee.diagnosis import squint_locator

    study, memory = _bone_in_a_study(tmp_path)

    def legacy(real):
        # What production did before the keyword: the paired location, whatever is asked.
        def locate(study, memory, deadline=None, *, refine_finalists=False):
            return real(study, memory, deadline, refine_finalists=True)

        return locate

    record, events = _squint_first_run(
        monkeypatch, tmp_path, study, memory, "femur", locate=legacy
    )

    reads = [i for i, event in enumerate(events) if event[0] == "fine_read"]
    assert [events[i] for i in reads] == [("fine_read", "femur")]
    assert reads[0] < events.index(_recalls_of(events, "femur")[0])
    assert all(event[3] for event in _recalls_of(events, "femur"))
    assert [item["code"] for item in record["observations"]] == [
        "already_measured",
        "shared_observation_already_available",
    ]
    work = record["work"]
    assert (work["location_fine_readings"], work["paired_fine_readings"]) == (1, 0)
    reference = squint_locator.locate_objects(study, memory)["objects"]["femur"]
    assert (
        record["objects"]["femur"]["profile"]["banks"] == reference["profile"]["banks"]
    )


def test_production_defers_a_dependents_reading_and_its_question_asks_for_it_by_name(
    monkeypatch, tmp_path
):
    from tests import test_squint_dependent_territories as dependent
    from tests.test_squint_v2_location import _v2_dependent

    series, femur, _built, _profiles, memory = _v2_dependent()
    study = dependent._study(series, knee_side="left", anchors={"femur": femur})
    record, events = _squint_first_run(
        monkeypatch, tmp_path, study, memory, "medial_meniscus"
    )

    # The femur's and dependent's 2 mm readings wait for their named questions.
    reads = [(i, event[1]) for i, event in enumerate(events) if event[0] == "fine_read"]
    first_recall = events.index(_recalls_of(events, "medial_meniscus")[0])
    femur_reads = [i for i, subject in reads if subject == "femur"]
    assert not femur_reads
    dependent_reads = [i for i, subject in reads if subject == "medial_meniscus"]
    assert dependent_reads and all(i > first_recall for i in dependent_reads)
    # This fixture has no native pixels, so the finer reading is refused by name: it is
    # not invented, and the object keeps the coarse reading it held. A refused read
    # claims nothing shared, so the second question asks again.
    assert [row["code"] for row in record["observations"]] == [
        "no_compatible_bounded_reading"
    ] * 2
    for row in record["observations"]:
        assert [item["reason"] for item in row["unavailable_regions"]] == [
            "refinement_refused:squint_refine_native_series_unavailable"
        ]
    profile = record["objects"]["medial_meniscus"]["profile"]
    assert {item["scale_mm"] for item in held_readings(profile)} == {10.0}
    assert record["work"]["paired_fine_readings"] == 0
