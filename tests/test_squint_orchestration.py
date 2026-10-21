from __future__ import annotations

import csv
import sys
import types
from pathlib import Path

import numpy as np
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

from knee.diagnosis import squint_pipeline, squint_profiles
from knee.diagnosis.squint_profiles import profile_window, read_study_squints

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


def _located(series: dict, profile: dict) -> dict:
    return {
        "femur": {
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

    question_module = types.ModuleType("knee.diagnosis.declarations")
    question_module.QUESTIONS = (
        types.SimpleNamespace(
            question_id="question-one",
            subject="diagnosis/question-one",
            objects=("femur",),
        ),
        types.SimpleNamespace(
            question_id="question-two",
            subject="diagnosis/question-two",
            objects=("femur",),
        ),
    )
    question_module.question_for = lambda question_id: next(
        question
        for question in question_module.QUESTIONS
        if question.question_id == question_id
    )
    monkeypatch.setitem(sys.modules, question_module.__name__, question_module)
    from knee.diagnosis import squint_configurations

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
    monkeypatch.setitem(sys.modules, contracts.__name__, contracts)

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
