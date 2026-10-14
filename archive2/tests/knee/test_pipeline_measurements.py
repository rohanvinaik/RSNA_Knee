"""Intent tests for optional physical measurements through the production study entry point."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, MRImageStorage, generate_uid

import knee.study.corpus as corpus_module
from knee import pipeline
from knee.absence import CODES as ABSENCE_CODES
from knee.lenses.places import STANDING_VALUES
from knee.objects.analysis import AnalysisRequest
from knee.study.tables import LABELS

STUDY_UID = "study-measurements"
STACKED_UID = "series-axial"
UNSTACKED_UID = "series-shape-varies"
AXIAL = ("1", "0", "0", "0", "1", "0")


def _write_slice(path: Path, pixels: np.ndarray, *, z: int, instance: int) -> None:
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = MRImageStorage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds = Dataset()
    ds.file_meta = meta
    ds.SOPClassUID = MRImageStorage
    ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    ds.Modality = "MR"
    ds.InstanceNumber = instance
    ds.Rows, ds.Columns = pixels.shape
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0
    ds.ImagePositionPatient = ["0", "0", str(z)]
    ds.ImageOrientationPatient = list(AXIAL)
    ds.PixelSpacing = ["0.5", "0.5"]
    ds.PixelData = pixels.astype(np.uint16, copy=False).tobytes()
    ds.save_as(path, enforce_file_format=True)


def _write_corpus(root: Path) -> None:
    (root / "train_series.csv").parent.mkdir(parents=True, exist_ok=True)
    with (root / "train.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("StudyInstanceUID", "Report", *LABELS))
        writer.writerow((STUDY_UID, "", *([""] * len(LABELS))))
    with (root / "test.csv").open("w", newline="", encoding="utf-8") as stream:
        csv.writer(stream).writerow(("StudyInstanceUID",))
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
        writer.writerow((STUDY_UID, STACKED_UID, "1", "0", "Axial"))
        writer.writerow((STUDY_UID, UNSTACKED_UID, "0", "0", "Axial"))
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

    stacked = root / "train_series" / STUDY_UID / STACKED_UID
    stacked.mkdir(parents=True)
    rows, columns = np.indices((16, 16))
    for z in range(3):
        # A deterministic, nonconstant image makes the regime and physical readings observable.
        pixels = 200 + 11 * rows + 7 * columns + 3 * z
        _write_slice(stacked / f"slice-{z}.dcm", pixels, z=z, instance=z + 1)

    unstacked = root / "train_series" / STUDY_UID / UNSTACKED_UID
    unstacked.mkdir(parents=True)
    for z, shape in enumerate(((8, 8), (9, 8))):
        pixels = np.arange(np.prod(shape), dtype=np.uint16).reshape(shape) + 50
        _write_slice(unstacked / f"slice-{z}.dcm", pixels, z=z, instance=z + 1)


def _request(direction_lps: tuple[float, float, float]) -> AnalysisRequest:
    return AnalysisRequest(
        tile_mm=2.0,
        offsets_mm=(-0.5, 0.0, 0.5),
        direction_lps=direction_lps,
        backend="reference",
    )


def _same_with_nan(left: Any, right: Any) -> bool:
    if isinstance(left, (float, np.floating)) and isinstance(
        right, (float, np.floating)
    ):
        return (math.isnan(left) and math.isnan(right)) or left == right
    if isinstance(left, tuple) and isinstance(right, tuple):
        return len(left) == len(right) and all(
            _same_with_nan(a, b) for a, b in zip(left, right, strict=True)
        )
    return left == right


def _count_series_reads(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    counts: dict[str, int] = {}
    real_read_series = corpus_module.read_series

    def counted(directory: Path, row: Any):
        counts[row.series_uid] = counts.get(row.series_uid, 0) + 1
        return real_read_series(directory, row)

    monkeypatch.setattr(corpus_module, "read_series", counted)
    return counts


def test_open_and_run_attaches_real_measurements_and_reads_each_series_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_corpus(tmp_path)
    reads = _count_series_reads(monkeypatch)
    calls: list[str] = []
    real_measure = pipeline.measure_series

    def observed_measure(series, request):
        calls.append(series.row.series_uid)
        return real_measure(series, request)

    monkeypatch.setattr(pipeline, "measure_series", observed_measure)
    result = pipeline.open_and_run(tmp_path, STUDY_UID, _request((1.0, 0.0, 0.0)))

    assert reads == {STACKED_UID: 1, UNSTACKED_UID: 1}
    assert calls == [STACKED_UID, UNSTACKED_UID]
    assert result.reached == "collapse"
    stacked, unstacked = result.series
    assert stacked.regime is not None
    assert stacked.measurements is not None
    measured = stacked.measurements
    assert measured.code == "measured"
    assert measured.slice_index == 1
    assert measured.frame is not None
    assert measured.squint is not None
    assert measured.profiles is not None
    assert measured.projection_norm == pytest.approx(1.0)
    assert measured.squint.median.shape == (4, 4)
    assert measured.profiles.samples.shape == (16, 3)
    assert measured.profiles.support_code == "complete_support"

    assert unstacked.regime is None
    assert unstacked.why == "no_stacked_volume"
    assert unstacked.measurements is not None
    assert unstacked.measurements.code == "no_stacked_volume"
    # The field's structural reading rides with the request (task 7.1): read at the same slice
    # the objects stage reads, total over a series without a volume.
    assert stacked.structure is not None
    assert stacked.structure.code in ABSENCE_CODES
    assert stacked.structure.axis == "normal"
    assert unstacked.structure is not None
    assert unstacked.structure.code == "predecessor_absent"


def test_axial_superior_inferior_parallel_to_slice_is_unavailable_without_row_fallback(
    tmp_path: Path,
) -> None:
    _write_corpus(tmp_path)
    result = pipeline.open_and_run(tmp_path, STUDY_UID, _request((0.0, 0.0, 1.0)))
    stacked, unstacked = result.series

    assert stacked.measurements is not None
    measurement = stacked.measurements
    assert measurement.code == "axis_unavailable"
    assert measurement.frame is not None
    assert measurement.squint is not None
    assert measurement.squint.median.size > 0
    assert measurement.profiles is None
    assert measurement.projection_norm == 0.0
    assert unstacked.measurements is not None
    assert unstacked.measurements.code == "no_stacked_volume"


def test_default_entry_point_preserves_regime_and_does_not_run_measurement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_corpus(tmp_path)
    reads = _count_series_reads(monkeypatch)
    calls: list[str] = []
    real_measure = pipeline.measure_series

    def observed_measure(series, request):
        calls.append(series.row.series_uid)
        return real_measure(series, request)

    monkeypatch.setattr(pipeline, "measure_series", observed_measure)
    default = pipeline.open_and_run(tmp_path, STUDY_UID)
    assert reads == {STACKED_UID: 1, UNSTACKED_UID: 1}
    assert calls == []
    assert all(row.measurements is None for row in default.series)
    assert all(row.structure is None for row in default.series)
    assert default.series[0].regime is not None

    explicit = pipeline.open_and_run(tmp_path, STUDY_UID, _request((1.0, 0.0, 0.0)))
    assert reads == {STACKED_UID: 2, UNSTACKED_UID: 2}
    assert calls == [STACKED_UID, UNSTACKED_UID]
    default_regime = default.series[0].regime
    explicit_regime = explicit.series[0].regime
    assert default_regime is not None and explicit_regime is not None
    for name in default_regime.__dataclass_fields__:
        assert _same_with_nan(
            getattr(explicit_regime, name), getattr(default_regime, name)
        ), name
    assert explicit.series[0].measurements is not None


@pytest.mark.parametrize(
    ("direction", "expected_code", "expected_samples"),
    [
        ((0.0, 0.0, 1.0), "axis_unavailable", 0),
        ((1.0, 0.0, 0.0), "complete_support", 48),
    ],
)
def test_hamilton_graph_returns_the_production_measurements_and_derived_work_counts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    direction,
    expected_code,
    expected_samples,
) -> None:
    _write_corpus(tmp_path)
    reads = _count_series_reads(monkeypatch)
    # Hamilton's driver reads this when imported, so disable telemetry first.
    monkeypatch.setenv("HAMILTON_TELEMETRY_ENABLED", "false")
    from hamilton import driver

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2]))
    from workbench.graph import object_measurements

    graph = driver.Builder().with_modules(object_measurements).build()
    outputs = graph.execute(
        ["study_run", "support_records", "work_counts"],
        inputs={
            "corpus_root": tmp_path,
            "study_uid": STUDY_UID,
            "analysis_request": _request(direction),
        },
    )

    assert reads == {STACKED_UID: 1, UNSTACKED_UID: 1}
    study_run = outputs["study_run"]
    assert [series.measurements.code for series in study_run.series] == [
        "axis_unavailable" if expected_samples == 0 else "measured",
        "no_stacked_volume",
    ]
    measurements = tuple(
        series.measurements
        for series in study_run.series
        if series.measurements is not None
    )
    expected_records = tuple(
        measurement.profiles.support_code
        if measurement.profiles is not None
        else measurement.code
        for measurement in measurements
    )
    expected_native_samples = sum(
        measurement.profiles.samples.size
        for measurement in measurements
        if measurement.profiles is not None
    )
    expected_squint_tiles = sum(
        measurement.squint.median.size
        for measurement in measurements
        if measurement.squint is not None
    )
    assert (
        outputs["support_records"]
        == expected_records
        == (
            expected_code,
            "no_stacked_volume",
        )
    )
    # Counted over SEATED MEMBERS and derived from the run, never written down: the intent is
    # that the development graph reports what production produced, and a hardcoded total stops
    # checking that the moment a member is seated or unseated.
    seated = tuple(
        member
        for series in study_run.series
        if series.lenses is not None
        for member in series.lenses.members
    )
    readings = tuple(
        series.lenses for series in study_run.series if series.lenses is not None
    )
    expected_lenses = {
        "lens_seated_members": len(seated),
        "lens_native_places": sum(member.codes.size for member in seated),
        "lens_output_bytes": sum(
            member.codes.nbytes + member.digits.nbytes for member in seated
        )
        + sum(reading.standings.nbytes for reading in readings),
        "lens_dissenting_places": sum(
            reading.standing_counts[STANDING_VALUES["dissent"]] for reading in readings
        ),
    }
    assert expected_lenses["lens_seated_members"] == 2 * len(study_run.series)
    assert outputs["work_counts"] == {
        "profile_coordinate_evaluations": expected_native_samples,
        "source_read_upper_bound": 4 * expected_native_samples,
        "profile_sample_output_bytes": 9 * expected_native_samples,
        "squint_tiles": expected_squint_tiles,
        **expected_lenses,
        "pairing_profiles": 0,
        "sample_supported_pairs": 0,
    }
    assert outputs["work_counts"] == {
        "profile_coordinate_evaluations": expected_samples,
        "source_read_upper_bound": 4 * expected_samples,
        "profile_sample_output_bytes": 9 * expected_samples,
        "squint_tiles": 16,
        **expected_lenses,
        "pairing_profiles": 0,
        "sample_supported_pairs": 0,
    }


def test_unavailable_plane_does_not_discard_the_study(tmp_path: Path) -> None:
    _write_corpus(tmp_path)
    request = AnalysisRequest(2.0, (0.0,), (1.0, 0.0, 0.0), "reference", 99)
    result = pipeline.open_and_run(tmp_path, STUDY_UID, request)
    measurements = [s.measurements for s in result.series]
    assert all(m is not None for m in measurements)
    assert [m.code for m in measurements if m is not None] == [
        "slice_unavailable",
        "no_stacked_volume",
    ]
    assert result.series[0].regime is not None
    first = measurements[0]
    assert first is not None
    assert first.validation_code == "invalid_slice_index"


def test_malformed_plane_geometry_is_a_series_reading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from dataclasses import replace

    _write_corpus(tmp_path)
    original = corpus_module.read_series

    def malformed(directory, row):
        series = original(directory, row)
        if series.geometry is not None:
            orientations = series.geometry.orientation.copy()
            orientations[:] = (1, 0, 0, 1, 0, 0)
            return replace(
                series, geometry=replace(series.geometry, orientation=orientations)
            )
        return series

    monkeypatch.setattr(corpus_module, "read_series", malformed)
    result = pipeline.open_and_run(tmp_path, STUDY_UID, _request((1.0, 0.0, 0.0)))
    measurements = [s.measurements for s in result.series]
    assert all(m is not None for m in measurements)
    assert [m.code for m in measurements if m is not None] == [
        "geometry_unreadable",
        "no_stacked_volume",
    ]
    first = measurements[0]
    assert first is not None
    assert first.validation_code == "degenerate_orientation"
    assert result.series[0].regime is not None


# This synthetic corpus has no calibrated noise population; annotation is the tested contract.
@pytest.mark.filterwarnings("ignore:Degrees of freedom <= 0 for slice.:RuntimeWarning")
@pytest.mark.parametrize("split", [220.0, float("nan")])
def test_saved_annotation_uses_the_production_background_reading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, split: float
) -> None:
    import json
    import sys

    from knee.collapse import regime as regime_module
    from workbench.measure import object_analysis

    root = tmp_path / "raw"
    out = tmp_path / "run"
    _write_corpus(root)
    reads = _count_series_reads(monkeypatch)
    # The regime reads its valley from the histogram it retains (task 7.1a), so the production
    # reading is injected where the valley is read, not where the histogram is built.
    monkeypatch.setattr(
        regime_module, "histogram_valley", lambda counts, edges, smooth=5: split
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "object_analysis",
            "--root",
            str(root),
            "--uid",
            STUDY_UID,
            "--tile-mm",
            "2",
            "--span-mm",
            "1",
            "--samples",
            "3",
            "--axis",
            "left",
            "--backend",
            "reference",
            "--out",
            str(out),
            # Both named because the one command now defaults to BOTH: the acquisitions converse,
            # and every stage is drawn. This test is about what the WRITER saves from a synthetic
            # corpus, so it asks for neither -- the same run it has always exercised, now stated
            # rather than inherited. No assertion below is relaxed.
            "--no-conversation",
            "--no-pictures",
        ],
    )
    object_analysis.main()
    assert reads == {STACKED_UID: 1, UNSTACKED_UID: 1}
    receipt = json.loads((out / "receipt.json").read_text())
    events = receipt["studies"][0]["ledger"]
    produced = [
        event["counts"]["places"]
        for event in events
        if event["name"] == "lenses.produced"
    ]
    assert produced == [3 * 16 * 16, 0]
    # Consumption is recorded by the CONSUMER since task 6.5: the bundles stage records that it
    # read the lens record, once per series. (Until 2026-10-12 the route wrote `lenses.consumed`
    # itself, right after production, which said nothing about any reader.)
    consumed = [
        event["counts"]["readings"]
        for event in events
        if event["name"] == "lenses.consumed_by.vectors"
    ]
    assert consumed == [1, 1]
    record = receipt["records"][0]
    assert record["ownership"]["code"] == "predecessor_absent"
    assert [m["parse"] for m in record["ownership"]["members"]] == ["solitary"]
    assert record["relations"]["code"] == "construction_absent"
    assert record["pairings"]["code"] == "predecessor_absent"
    assert "task 1.3a" in record["relations"]["why"]
    assert receipt["studies"][0]["output"]["code"] == "projection_undeclared"
    assert receipt["studies"][0]["output"]["submission_rows"] is None
    assert [s for s, _ in receipt["studies"][0]["attendance"]] == list(pipeline.STAGES)
    # EVERY seated member is saved, each naming its own population, and the standing between
    # them beside them. No key here holds "the" reading, because the pipeline keeps everything
    # it computes and resolution is the founder's.
    members = record["lenses"]["members"]
    assert [member["population"] for member in members] == [
        "noise_law_cut",
        "background_split",
    ]
    assert all(member["normalisation"] == "none" for member in members)
    assert "normalisation" not in record["lenses"]
    assert "counts" not in record["lenses"]
    assert record["lenses"]["saved_scope"] == "selected native plane (row,column)"
    assert all(sum(member["counts"]) == 3 * 16 * 16 for member in members)
    assert sum(record["lenses"]["standing_counts"]) == 3 * 16 * 16
    with np.load(out / record["artifact"], allow_pickle=False) as arrays:
        for member in members:
            assert arrays[member["codes_array"]].dtype == np.uint8
            assert arrays[member["digits_array"]].dtype == np.int8
            assert arrays[member["digits_array"]].shape == (16, 16)
        assert arrays["lens_standings"].dtype == np.uint8
        assert arrays["lens_standings"].shape == (16, 16)
        assert arrays["ownership_solitary_claims"].shape == (0, 0)
        assert arrays["ownership_solitary_residual"].shape == (0, 0)
        assert arrays["ownership_disagreement"].shape == (0, 0)
        if np.isfinite(split):
            assert record["background_split"] == split
            assert record["background_annotation_code"] == "measured"
            np.testing.assert_array_equal(
                arrays["background_mask"], arrays["acquired_plane"] <= split
            )
            assert arrays["background_mask"].any()
            assert not arrays["background_mask"].all()
        else:
            assert record["background_split"] is None
            assert record["background_annotation_code"] == "unavailable"
            assert "background_mask" not in arrays
