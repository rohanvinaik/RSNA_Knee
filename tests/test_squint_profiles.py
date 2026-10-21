from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

from knee.collapse.squint_stack import SquintStack
from knee.diagnosis.squint_profiles import (
    cosine_evidence,
    merge_profiles,
    profile_window,
    read_study_squints,
    refine_window,
)
from knee.encoding.counts import BankLayout, CountBundle, CountLayout, cosine_terms


def _series_record(
    *,
    codes: np.ndarray | None = None,
    subject_view: tuple[str, str, str] = ("Sagittal", "1", "1"),
) -> dict:
    values = np.asarray([[[0.0, 1.0], [2.0, 3.0]]], dtype=np.float64)
    if codes is None:
        codes = np.asarray([[[-1, 0], [0, 1]]], dtype=np.int8)
    bounds = np.asarray(
        [[[[0, 1, 0, 1], [0, 1, 1, 2]], [[1, 2, 0, 1], [1, 2, 1, 2]]]],
        dtype=np.int64,
    )[0]
    # A (1, 2, 2) squint stack with one slice and four tiles.
    median = values.copy()
    minimum = values.copy()
    maximum = values.copy()
    coverage = np.ones_like(values)
    centres = np.zeros((1, 2, 2, 3), dtype=np.float64)
    for row in range(2):
        for column in range(2):
            centres[0, row, column] = (column * 10.0, row * 10.0, 0.0)
    for array in (median, minimum, maximum, coverage, centres, bounds):
        array.flags.writeable = False
    stack = SquintStack(
        series_uid="series-1",
        code="present",
        why="fixture",
        tile_mm=10.0,
        tile_shape_rc=(1, 1),
        bounds_rc=bounds,
        median=median,
        minimum=minimum,
        maximum=maximum,
        coverage=coverage,
        centres_lps=centres,
    )
    metrics = {
        "signal_median": values,
        "signal_minimum": values,
        "signal_maximum": values,
        "local_range": np.zeros_like(values),
        "gradient_row": np.zeros_like(values),
        "gradient_column": np.zeros_like(values),
    }
    available = {name: np.ones_like(values, dtype=np.bool_) for name in metrics}
    if codes.shape != values.shape:
        raise ValueError("fixture code shape")
    code_map = {name: codes.copy() for name in metrics}
    calibration = {
        name: {
            "status": "measured",
            "available_count": 4,
            "quantile_method": "numpy_linear_terciles",
            "low": 1.0,
            "high": 2.0,
        }
        for name in metrics
    }
    for array in (*metrics.values(), *available.values(), *code_map.values()):
        array.flags.writeable = False
    return {
        "series_uid": "series-1",
        "view": {
            "orientation": subject_view[0],
            "fluid_sensitive": subject_view[1],
            "fat_suppression": subject_view[2],
        },
        "shape": (1, 2, 2),
        "geometry": None,
        "stack": stack,
        "metric_values": metrics,
        "metric_available": available,
        "metric_codes": code_map,
        "calibration": calibration,
        "source": {
            "api": "fixture",
            "study_uid": "study-1",
            "series_uid": "series-1",
            "tile_mm": 10.0,
            "procedure": "knee.squint-profile/scan-tercile-v1",
            "calibration": calibration,
        },
        "native_series": None,
    }


def _write_dicom(
    path: Path,
    study_uid: str,
    series_uid: str,
    pixels: np.ndarray,
    spacing_rc: tuple[float, float] = (10.0, 10.0),
) -> None:
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
    dataset.PixelSpacing = list(spacing_rc)
    dataset.PixelData = np.asarray(pixels, dtype="<u2").tobytes()
    dataset.save_as(path, enforce_file_format=True, little_endian=True)


def _write_tables(root: Path, uid: str, series_uid: str) -> None:
    labels = (
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
    with (root / "train.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("StudyInstanceUID", "Report", *labels))
        writer.writerow((uid, "", *("" for _ in labels)))
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
        writer = csv.writer(stream)
        writer.writerow(("StudyInstanceUID",))
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


def test_reader_uses_real_dicom_series_and_retains_runtime_source(tmp_path):
    uid, series_uid = generate_uid(), generate_uid()
    series_dir = tmp_path / "train_series" / uid / series_uid
    series_dir.mkdir(parents=True)
    _write_dicom(series_dir / "one.dcm", uid, series_uid, np.arange(16).reshape(4, 4))
    _write_tables(tmp_path, uid, series_uid)

    study = read_study_squints(tmp_path, uid, io_workers=2, tile_mm=10.0)

    assert study["study_uid"] == uid
    assert study["work"]["series_read"] == 1
    assert study["work"]["slices_read"] == 1
    series = study["series"][0]
    assert series["view"] == {
        "orientation": "Sagittal",
        "fluid_sensitive": "1",
        "fat_suppression": "1",
    }
    assert series["stack"].code == "present"
    assert series["native_series"].volume.shape == (1, 4, 4)
    profile = profile_window(series, (0, 1, 0, 1, 0, 1), subject="femur")
    assert profile["source"]["native_bounds_rc"] == [0, 1, 0, 1]
    assert profile["source"]["series_context"] is series["source"]


def test_profile_window_uses_fixed_ternary_codes_and_omits_unread_banks():
    series = _series_record()
    series["metric_codes"]["signal_maximum"] = np.full((1, 2, 2), -2, dtype=np.int8)
    profile = profile_window(series, (0, 1, 0, 2, 0, 2), subject="femur")
    median = next(
        counts
        for name, counts in profile["banks"].items()
        if "metric=signal_median/" in name
    )
    assert median == [1, 2, 1]
    assert not any("metric=signal_maximum/" in name for name in profile["banks"])
    assert (
        profile["source"]["series_context"]["calibration"]["signal_median"]["low"]
        == 1.0
    )
    assert any("patient_lps_left" in name for name in profile["banks"])
    assert any("patient_lps_posterior" in name for name in profile["banks"])
    assert any("stack_depth_first" in name for name in profile["banks"])


def test_profile_window_rejects_invalid_and_out_of_bounds_windows():
    series = _series_record()
    with pytest.raises(ValueError, match="six_integer_bounds"):
        profile_window(series, [0, 1, 0, 1, 0, 1], subject="femur")
    with pytest.raises(ValueError, match="out_of_bounds"):
        profile_window(series, (0, 2, 0, 1, 0, 1), subject="femur")


def test_merge_profiles_is_exact_order_independent_and_keeps_lineage():
    first = profile_window(_series_record(), (0, 1, 0, 1, 0, 1), subject="femur")
    second = profile_window(_series_record(), (0, 1, 1, 2, 1, 2), subject="femur")
    left = merge_profiles((first, second), subject="femur")
    right = merge_profiles((second, first), subject="femur")
    assert left["banks"] == right["banks"]
    assert left["source"]["lineage"] == right["source"]["lineage"]
    assert all(sum(counts) == 2 for counts in left["banks"].values())
    with pytest.raises(ValueError, match="subject_mismatch"):
        merge_profiles((first, second), subject="tibia")


def test_cosine_terms_match_existing_count_arithmetic_exactly():
    left = {
        "schema": "knee.squint-profile/v1",
        "subject": "femur",
        "banks": {"a": [2, 1, 3], "silent": [0, 0, 0]},
        "source": {"procedure": "knee.squint-profile/scan-tercile-v1"},
    }
    right = {
        "schema": "knee.squint-profile/v1",
        "subject": "femur",
        "banks": {"a": [1, 2, 1], "other": [0, 0, 5]},
        "source": {"procedure": "knee.squint-profile/scan-tercile-v1"},
    }
    layout = CountLayout(
        "squint-test-layout",
        "squint-test-carrier",
        (BankLayout("a", 3), BankLayout("silent", 3), BankLayout("other", 3)),
    )
    exact = cosine_terms(
        CountBundle(layout, ((2, 1, 3), (0, 0, 0), (0, 0, 0))),
        CountBundle(layout, ((1, 2, 1), (0, 0, 0), (0, 0, 5))),
        ("a", "silent", "other"),
    )
    evidence = cosine_evidence(left, right)
    assert evidence["code"] == exact.code.value == "ok"
    assert evidence["dot"] == exact.terms.dot
    assert evidence["left_norm_sq"] == exact.terms.left_norm_sq
    assert evidence["right_norm_sq"] == exact.terms.right_norm_sq
    assert evidence["common_banks"] == list(exact.terms.included_banks) == ["a"]


def test_cosine_silence_is_not_a_measured_middle_vote():
    left = profile_window(
        _series_record(codes=np.full((1, 2, 2), -2)),
        (0, 1, 0, 2, 0, 2),
        subject="femur",
    )
    right = profile_window(_series_record(), (0, 1, 0, 2, 0, 2), subject="femur")
    assert left["banks"] == {}
    result = cosine_evidence(left, right)
    assert result["code"] == "silent"
    assert result["dot"] == result["left_norm_sq"] == result["right_norm_sq"] == 0
    assert result["common_banks"] == []


def test_refine_window_reads_only_native_support_and_preserves_crop_geometry(tmp_path):
    uid, series_uid = generate_uid(), generate_uid()
    series_dir = tmp_path / "train_series" / uid / series_uid
    series_dir.mkdir(parents=True)
    _write_dicom(
        series_dir / "one.dcm",
        uid,
        series_uid,
        np.arange(16).reshape(4, 4),
        spacing_rc=(1.0, 1.0),
    )
    _write_tables(tmp_path, uid, series_uid)
    study = read_study_squints(tmp_path, uid, tile_mm=10.0)
    series = study["series"][0]

    fine = refine_window(series, (0, 1, 0, 1, 0, 1), subject="femur", tile_mm=2.0)

    assert fine["schema"] == "knee.squint-profile/v1"
    assert fine["source"]["refinement"] is True
    assert fine["source"]["native_crop_rc"] == [0, 4, 0, 4]
    assert fine["source"]["native_slice_range"] == [0, 1]
    assert any("scale=2mm" in name for name in fine["banks"])
    fine_median = next(
        counts
        for name, counts in fine["banks"].items()
        if "metric=signal_median/" in name and "direction=overview" in name
    )
    assert sum(fine_median) == 4
