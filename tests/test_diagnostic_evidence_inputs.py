from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import (
    ExplicitVRLittleEndian,
    SecondaryCaptureImageStorage,
    generate_uid,
)

from knee.diagnosis.evidence import load_source, retain_source
from knee.diagnosis.inputs import acquired_studies
from knee.receipt import digest

STUDY_UID = "1.2.826.0.1.3680043.10.543.1"
SAGITTAL_UID = "1.2.826.0.1.3680043.10.543.2"
CORONAL_UID = "1.2.826.0.1.3680043.10.543.3"
SAGITTAL_VIEW = ["Sagittal", "0", "0"]
CORONAL_VIEW = ["Coronal", "0", "0"]


def _write_frame(path: Path, series_uid: str, values: list[list[int]]) -> None:
    pixels = np.asarray(values, dtype="<i2")
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    meta.ImplementationClassUID = generate_uid()
    dataset = FileDataset(str(path), {}, file_meta=meta, preamble=b"\0" * 128)
    dataset.SOPClassUID = meta.MediaStorageSOPClassUID
    dataset.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    dataset.PatientName = "Evidence^Fixture"
    dataset.PatientID = "evidence-fixture"
    dataset.StudyInstanceUID = STUDY_UID
    dataset.SeriesInstanceUID = series_uid
    dataset.Modality = "MR"
    dataset.Rows, dataset.Columns = pixels.shape
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = 16
    dataset.BitsStored = 16
    dataset.HighBit = 15
    dataset.PixelRepresentation = 1
    dataset.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
    dataset.ImagePositionPatient = [10, 20, 30]
    dataset.PixelSpacing = [0.5, 0.75]
    dataset.PixelData = pixels.tobytes()
    dataset.save_as(path, enforce_file_format=True)


def _profile(view: list[str], read_bank: str, unavailable_bank: str) -> dict:
    return {
        "object": "femur",
        "provenance": "native",
        "kind": "reading",
        "support": "declared_region",
        "view": view,
        "readings": [
            {
                "bank": bank,
                "metric": "signal",
                "value": "acquired_plane",
                "available": "finite_pixels",
            }
            for bank in (read_bank, unavailable_bank)
        ],
        "references": [
            {
                "bank": "coronal_signal",
                "metric": "signal",
                "reference_id": "coronal-fixture-reference-v1",
                "source": "fixture explicit reference",
                "units": "stored-value-unit",
                "low": 12,
                "high": 14,
            }
        ],
    }


def _observation(
    path: Path,
    *,
    series_uid: str,
    view: list[str],
    read_bank: str,
    unavailable_bank: str,
) -> dict:
    return {
        "object": "femur",
        "region": f"{view[0].lower()}-region",
        "frame": {
            "path": str(path),
            "series_uid": series_uid,
            "slice_index": 4,
            "view": view,
        },
        "support_rc": [[0, 1], [1, 2]],
        "binding": [
            {"bank": read_bank, "metric": "signal", "source": "acquired_signal"},
            {
                "bank": unavailable_bank,
                "metric": "signal",
                "source": "unavailable",
                "reason": "this diagnostic bank is not declared for this view",
            },
        ],
    }


def _recipe(sagittal: Path, coronal: Path) -> dict:
    sagittal_bank = "sagittal_signal"
    coronal_bank = "coronal_signal"
    spec = {
        "version": "retained-evidence-fixture-v1",
        "banks": [
            {
                "name": name,
                "facet": f"{name} acquired signal",
                "metrics": [{"name": "signal", "kind": "digit"}],
            }
            for name in (sagittal_bank, coronal_bank)
        ],
        "profiles": [
            _profile(SAGITTAL_VIEW, sagittal_bank, coronal_bank),
            _profile(CORONAL_VIEW, coronal_bank, sagittal_bank),
        ],
    }
    return {
        "schema": "knee.diagnostic-inputs/v1",
        "mode": "cheap/retained-evidence-v1",
        "producer": "generated two-view DICOM fixture",
        "dependencies": ["DICOM stored pixels", "explicit support coordinates"],
        "encoding_spec": spec,
        "view_distinguished_banks": {
            sagittal_bank: [SAGITTAL_VIEW],
            coronal_bank: [CORONAL_VIEW],
        },
        "studies": [
            {
                "study_uid": STUDY_UID,
                "observations": [
                    _observation(
                        sagittal,
                        series_uid=SAGITTAL_UID,
                        view=SAGITTAL_VIEW,
                        read_bank=sagittal_bank,
                        unavailable_bank=coronal_bank,
                    ),
                    _observation(
                        coronal,
                        series_uid=CORONAL_UID,
                        view=CORONAL_VIEW,
                        read_bank=coronal_bank,
                        unavailable_bank=sagittal_bank,
                    ),
                ],
            }
        ],
    }


def _save_audit_sample(root: Path, receipt: dict, loaded: dict) -> None:
    sample_dir = root / "worker-output"
    sample_dir.mkdir(parents=True, exist_ok=True)
    retained_dir = sample_dir / "retained-source"
    if retained_dir.exists():
        shutil.rmtree(retained_dir)
    shutil.copytree(Path(receipt["manifest"]).parent, retained_dir)
    source = loaded["source"]
    arrays = source["shared_measurement_arrays"]
    measurements = []
    for observation in source["observations"]:
        measurements.append(
            {
                "view": observation["frame"]["view"],
                "description_status": observation["description_status"],
                "support_rc": observation["support_rc"].tolist(),
                "measurements": [
                    {
                        **{
                            key: value
                            for key, value in item.items()
                            if not key.endswith("_digest")
                        },
                        **{
                            key: arrays[value].tolist()
                            for key, value in item.items()
                            if key.endswith("_digest")
                        },
                    }
                    for item in observation["measurements"]
                ],
            }
        )
    (sample_dir / "retained-source-sample.json").write_text(
        json.dumps(
            {
                "retention_receipt": receipt,
                "loaded_manifest_sha256": loaded["manifest_sha256"],
                "loaded_archive_sha256": loaded["archive_sha256"],
                "profile_record_type": source["profiles"][0]["$record_type"],
                "profile_layout": source["profiles"][0]["fields"]["bundle"]["layout"],
                "sparse_count_rows": source["profiles"][0]["fields"]["bundle"][
                    "sparse_rows"
                ],
                "profile_counts": source["profile_counts"],
                "observations": measurements,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def test_two_view_source_is_lossless_after_dicom_source_is_removed(
    tmp_path: Path,
) -> None:
    sagittal_path = tmp_path / "sagittal.dcm"
    coronal_path = tmp_path / "coronal.dcm"
    _write_frame(sagittal_path, SAGITTAL_UID, [[10, 11, 12], [13, 14, 15]])
    _write_frame(coronal_path, CORONAL_UID, [[20, 21, 22], [23, 24, 25]])
    recipe = _recipe(sagittal_path, coronal_path)

    study_uid, profiles, metadata = next(acquired_studies({"recipe_data": recipe}))
    assert study_uid == STUDY_UID
    assert len(profiles) == 1
    assert metadata["decoded_frame_count"] == 2
    profile = profiles[0]
    assert profile.scope == 'region:["region:coronal-region","region:sagittal-region"]'
    assert len(dict(profile.provenance)) == len(profile.provenance)
    counts_by_bank = dict(
        zip(
            (bank.name for bank in profile.bundle.layout.banks),
            profile.bundle.counts,
            strict=True,
        )
    )
    assert sum(counts_by_bank["sagittal_signal"]) == 0
    assert sum(counts_by_bank["coronal_signal"]) == 2
    assert metadata["profile_counts"] == (profile.bundle.counts,)

    rows = {tuple(row["frame"]["view"]): row for row in metadata["observations"]}
    sagittal_measurement = {
        row["bank"]: row for row in rows[tuple(SAGITTAL_VIEW)]["measurements"]
    }
    coronal_measurement = {
        row["bank"]: row for row in rows[tuple(CORONAL_VIEW)]["measurements"]
    }
    assert sagittal_measurement["sagittal_signal"]["status"] == "missing_reference"
    assert sagittal_measurement["sagittal_signal"]["source_state"] == "measured"
    assert coronal_measurement["sagittal_signal"]["source_state"] == "unavailable"
    assert coronal_measurement["sagittal_signal"]["reason"]
    assert coronal_measurement["coronal_signal"]["status"] == "ok"
    assert sagittal_measurement["coronal_signal"]["source_state"] == "unavailable"

    shared = metadata["shared_measurement_arrays"]
    np.testing.assert_array_equal(
        shared[sagittal_measurement["sagittal_signal"]["source_values_digest"]],
        [11, 15],
    )
    np.testing.assert_array_equal(
        shared[sagittal_measurement["sagittal_signal"]["source_available_digest"]],
        [True, True],
    )
    np.testing.assert_array_equal(
        shared[coronal_measurement["coronal_signal"]["source_values_digest"]], [21, 25]
    )
    np.testing.assert_array_equal(
        rows[tuple(SAGITTAL_VIEW)]["support_rc"], [[0, 1], [1, 2]]
    )
    np.testing.assert_array_equal(
        rows[tuple(CORONAL_VIEW)]["support_rc"], [[0, 1], [1, 2]]
    )
    assert rows[tuple(SAGITTAL_VIEW)]["frame"]["geometry"]["origin_lps"] == [
        10.0,
        20.0,
        30.0,
    ]
    assert rows[tuple(CORONAL_VIEW)]["frame"]["geometry"]["basis_lps"] == [
        [0.0, 0.75],
        [0.5, 0.0],
        [0.0, 0.0],
    ]

    output = tmp_path / "published"
    receipt = retain_source(output, study_uid, metadata)
    source_paths = (sagittal_path, coronal_path)
    renamed_paths = tuple(path.with_suffix(".offline") for path in source_paths)
    try:
        for original, renamed in zip(source_paths, renamed_paths, strict=True):
            original.rename(renamed)
        loaded = load_source(Path(receipt["manifest"]))
    finally:
        for original, renamed in zip(source_paths, renamed_paths, strict=True):
            if renamed.exists():
                renamed.rename(original)

    restored = loaded["source"]
    assert loaded["study_uid"] == STUDY_UID
    assert loaded["manifest_sha256"] == receipt["sha256"]
    assert loaded["archive_sha256"] == receipt["archive_sha256"]
    assert restored["profile_counts"] == metadata["profile_counts"]
    assert (
        restored["observations"][0]["profile"]["$record_type"]
        == "knee.diagnosis.models.Profile"
    )
    assert restored["profiles"][0]["$record_type"] == "knee.diagnosis.models.Profile"
    assert restored["profiles"][0]["fields"]["scope"] == profile.scope
    assert len(restored["profiles"][0]["fields"]["provenance"]) == len(
        profile.provenance
    )
    restored_counts = restored["profiles"][0]["fields"]["bundle"]["sparse_rows"]
    assert restored_counts == [
        [1, row, str(value)]
        for row, value in enumerate(counts_by_bank["coronal_signal"])
        if value
    ]
    restored_arrays = restored["shared_measurement_arrays"]
    for digest_key, array in shared.items():
        np.testing.assert_array_equal(restored_arrays[digest_key], array)
        assert digest(array) == digest_key
    assert restored["observations"][0]["frame"]["path"] == str(sagittal_path)
    assert restored["observations"][1]["frame"]["path"] == str(coronal_path)
    _save_audit_sample(tmp_path / "audit-sample", receipt, loaded)
