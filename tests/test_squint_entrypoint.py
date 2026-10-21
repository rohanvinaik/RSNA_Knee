from __future__ import annotations

import csv
import hashlib
import json
import runpy
import sys
from pathlib import Path

import numpy as np
import pytest
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

from knee.diagnosis.squint_profiles import profile_window, read_study_squints
from knee.json_store import load_json
from knee.study.tables import LABELS

RUNNER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_interiors.py"
OFFICIAL_COLUMNS = (
    "StudyInstanceUID",
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
    pixels = np.arange(32 * 32, dtype=np.uint16).reshape(32, 32)
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
    dataset.Rows = dataset.Columns = 32
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = dataset.BitsStored = 16
    dataset.HighBit = 15
    dataset.PixelRepresentation = 0
    dataset.ImagePositionPatient = [0.0, 0.0, 0.0]
    dataset.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    dataset.PixelSpacing = [1.0, 1.0]
    dataset.PixelData = pixels.astype("<u2").tobytes()
    dataset.save_as(path, enforce_file_format=True, little_endian=True)


def _write_corpus(root: Path, case_uid: str, query_uid: str) -> tuple[str, str]:
    case_series, query_series = str(generate_uid()), str(generate_uid())
    with (root / "train.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("StudyInstanceUID", "Report", *LABELS))
        writer.writerow((case_uid, "independent source case", *(["1"] + ["0"] * 11)))
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
        writer.writerow((case_uid, case_series, "1", "1", "Sagittal"))
    with (root / "test.csv").open("w", newline="", encoding="utf-8") as stream:
        csv.writer(stream).writerows((("StudyInstanceUID",), (query_uid,)))
    with (root / "test_series.csv").open("w", newline="", encoding="utf-8") as stream:
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
        writer.writerow((query_uid, query_series, "1", "1", "Sagittal"))
    for uid, series_uid, split in (
        (case_uid, case_series, "train_series"),
        (query_uid, query_series, "test_series"),
    ):
        directory = root / split / uid / series_uid
        directory.mkdir(parents=True)
        _write_dicom(directory / "one.dcm", uid, series_uid)
    return case_series, query_series


def _save_case_memory(root: Path, case_uid: str, series_uid: str, path: Path) -> None:
    """Write a valid immutable memory from public writer output and public memory API."""
    from knee.diagnosis.squint_memory import save_memory

    study = read_study_squints(root, case_uid)
    series = next(row for row in study["series"] if row["series_uid"] == series_uid)
    profile = profile_window(
        series,
        (
            0,
            series["stack"].median.shape[0],
            0,
            series["stack"].median.shape[1],
            0,
            series["stack"].median.shape[2],
        ),
        subject="femur",
    )
    memory = {
        "schema": "knee.squint-memory/v1",
        "revision": "entrypoint-fixture-r1",
        "questions": list(OFFICIAL_COLUMNS[1:]),
        "procedure": "knee.squint-profile/scan-tercile-v1",
        "source_identities": [{"study_uid": case_uid, "series_uid": series_uid}],
        "cases": [
            {
                "case_id": "fixture-case-acl-positive",
                "study_uid": case_uid,
                "subject": "femur",
                "condition_calls": {"ACL": 1},
                "profile": profile,
                "regions": [],
                "full_profile": None,
                "full_source": {"study_uid": case_uid, "series_uid": series_uid},
                "teaching_source": {"kind": "fixture-independent-call"},
            }
        ],
    }
    save_memory(memory, path)


def _run_main(monkeypatch, argv: list[str]) -> None:
    namespace = runpy.run_path(str(RUNNER_PATH), run_name="squint_entrypoint_test")
    main = namespace["main"]
    globals_ = main.__globals__

    def forbidden(*args, **kwargs):
        raise AssertionError("full-anatomy reference path was called")

    monkeypatch.setitem(globals_, "measure_study", forbidden)
    monkeypatch.setitem(globals_, "_generated_study_source_factory", forbidden)
    monkeypatch.setattr(sys, "argv", [str(RUNNER_PATH), *argv])
    main()


def test_real_entrypoint_uses_squint_memory_and_emits_official_rows(
    tmp_path, monkeypatch
):
    case_uid, query_uid = str(generate_uid()), str(generate_uid())
    root = tmp_path / "raw"
    root.mkdir()
    case_series, _ = _write_corpus(root, case_uid, query_uid)
    memory = tmp_path / "memory"
    _save_case_memory(root, case_uid, case_series, memory)
    manifest_path = memory / "manifest.json"
    original_manifest_bytes = manifest_path.read_bytes()
    read_count = 0
    parse_count = 0
    original_read_bytes = Path.read_bytes
    original_json_loads = json.loads

    def counted_read_bytes(path: Path) -> bytes:
        nonlocal read_count
        value = original_read_bytes(path)
        if path.resolve() == manifest_path.resolve():
            read_count += 1
        return value

    def counted_json_loads(value, *args, **kwargs):
        nonlocal parse_count
        if value == original_manifest_bytes:
            parse_count += 1
        return original_json_loads(value, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", counted_read_bytes)
    monkeypatch.setattr(json, "loads", counted_json_loads)
    template = tmp_path / "official-template.csv"
    with template.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(OFFICIAL_COLUMNS)
        writer.writerow((query_uid, *([0.0] * 12)))
    output = tmp_path / "output"

    _run_main(
        monkeypatch,
        [
            "--study-uid",
            query_uid,
            "--root",
            str(root),
            "--diagnostic-mode",
            "infer",
            "--diagnostic-memory",
            str(memory),
            "--diagnostic-output",
            str(output),
            "--diagnostic-submission-template",
            str(template),
            "--workers",
            "1",
        ],
    )

    manifest = original_json_loads(original_manifest_bytes)
    study = load_json(output / "studies" / f"{query_uid}.json")
    receipt = json.loads((output / "receipt.json").read_text())
    with (output / "submission.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.reader(stream))
    assert manifest["cases"][0]["study_uid"] == case_uid
    assert study["study_uid"] == query_uid
    assert study["memory_revision"] == "entrypoint-fixture-r1"
    assert set(study["questions"]) == set(LABELS)
    assert rows[0] == list(OFFICIAL_COLUMNS)
    assert rows[1][0] == query_uid
    assert len(rows[1]) == 13
    assert receipt["work"]["full_anatomy_runs"] == 0
    assert receipt["source_mode"] == "raw_squint_case_recall"
    assert (
        receipt["memory_manifest_sha256"]
        == hashlib.sha256(original_manifest_bytes).hexdigest()
    )
    assert read_count == 1
    assert parse_count == 1


def test_real_entrypoint_rejects_unknown_uid_without_full_reconstruction(
    tmp_path, monkeypatch
):
    case_uid, known_query_uid, unknown_uid = (
        str(generate_uid()),
        str(generate_uid()),
        str(generate_uid()),
    )
    root = tmp_path / "raw"
    root.mkdir()
    case_series, _ = _write_corpus(root, case_uid, known_query_uid)
    memory = tmp_path / "memory"
    _save_case_memory(root, case_uid, case_series, memory)

    with pytest.raises(ValueError, match="squint_study_uid_missing"):
        _run_main(
            monkeypatch,
            [
                "--study-uid",
                unknown_uid,
                "--root",
                str(root),
                "--diagnostic-mode",
                "infer",
                "--diagnostic-memory",
                str(memory),
                "--diagnostic-output",
                str(tmp_path / "unknown-output"),
                "--workers",
                "1",
            ],
        )
