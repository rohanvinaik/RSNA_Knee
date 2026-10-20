from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pytest
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import (
    ExplicitVRLittleEndian,
    SecondaryCaptureImageStorage,
    generate_uid,
)

from knee.diagnosis.composition import compose_question_profile
from knee.diagnosis.inputs import DiagnosticInputError, acquired_studies
from knee.diagnosis.models import Call, Case, Question, Snapshot
from knee.diagnosis.retrieval import recall
from knee.encoding.counts import CountCode, cosine_terms

STUDY_UID = "1.2.826.0.1.3680043.10.543.1"
SERIES_UID = "1.2.826.0.1.3680043.10.543.2"
OTHER_SERIES_UID = "1.2.826.0.1.3680043.10.543.3"
AXIAL_SERIES_UID = "1.2.826.0.1.3680043.10.543.4"


def _write_dicom(
    path: Path,
    pixels: np.ndarray,
    *,
    series_uid: str = SERIES_UID,
    study_uid: str = STUDY_UID,
) -> None:
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    meta.ImplementationClassUID = generate_uid()
    ds = FileDataset(str(path), {}, file_meta=meta, preamble=b"\0" * 128)
    ds.SOPClassUID = meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    ds.PatientName = "Fixture^Patient"
    ds.PatientID = "fixture"
    ds.StudyInstanceUID = study_uid
    ds.SeriesInstanceUID = series_uid
    ds.Modality = "MR"
    ds.Rows, ds.Columns = pixels.shape
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1
    ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
    ds.ImagePositionPatient = [10, 20, 30]
    ds.PixelSpacing = [0.5, 0.75]
    ds.PixelData = np.asarray(pixels, dtype="<i2").tobytes()
    ds.save_as(path, enforce_file_format=True)


def _spec(*, references: list[dict] | None = None) -> dict:
    return {
        "version": "fixture-v1",
        "storage": "npz_xz",
        "banks": [
            {
                "name": "raw_signal",
                "facet": "acquired signal",
                "metrics": [{"name": "signal", "kind": "digit"}],
            }
        ],
        "profiles": [
            {
                "object": "femur",
                "provenance": "native",
                "kind": "reading",
                "support": "declared_region",
                "view": ["Sagittal", "0", "0"],
                "readings": [
                    {
                        "bank": "raw_signal",
                        "metric": "signal",
                        "value": "acquired_plane",
                        "available": "finite_pixels",
                    }
                ],
                "references": references or [],
            }
        ],
    }


def _recipe(frame: Path, spec: dict, observations: list[dict] | None = None) -> dict:
    return {
        "schema": "knee.diagnostic-inputs/v1",
        "mode": "cheap/raw-plane-v1",
        "producer": "fixture raw plane reader",
        "dependencies": ["DICOM stored pixels", "declared support coordinates"],
        "encoding_spec": spec,
        "studies": [
            {
                "study_uid": STUDY_UID,
                "observations": observations
                or [
                    {
                        "object": "femur",
                        "region": "caller-region",
                        "frame": {
                            "path": str(frame),
                            "series_uid": SERIES_UID,
                            "slice_index": 7,
                            "view": ["Sagittal", "0", "0"],
                        },
                        "support_rc": [[0, 1], [1, 2]],
                        "binding": [
                            {
                                "bank": "raw_signal",
                                "metric": "signal",
                                "source": "acquired_signal",
                            }
                        ],
                    }
                ],
            }
        ],
    }


def _two_view_spec() -> dict:
    def profile(view: list[str], eligible_bank: str, unavailable_bank: str) -> dict:
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
                for bank in (eligible_bank, unavailable_bank)
            ],
            "references": [
                {
                    "bank": bank,
                    "metric": "signal",
                    "reference_id": f"{bank}-reference-v1",
                    "source": "explicit fixture reference",
                    "units": "stored-value-unit",
                    "low": 12,
                    "high": 14,
                }
                for bank in ("sagittal_signal", "coronal_signal")
            ],
        }

    return {
        "version": "two-view-fixture-v1",
        "banks": [
            {
                "name": bank,
                "facet": f"{bank} acquired signal",
                "metrics": [{"name": "signal", "kind": "digit"}],
            }
            for bank in ("sagittal_signal", "coronal_signal")
        ],
        "profiles": [
            profile(["Sagittal", "0", "0"], "sagittal_signal", "coronal_signal"),
            profile(["Coronal", "0", "0"], "coronal_signal", "sagittal_signal"),
        ],
    }


def _two_view_observation(
    frame: Path,
    *,
    series_uid: str,
    view: list[str],
    eligible_bank: str,
    unavailable_bank: str,
) -> dict:
    return {
        "object": "femur",
        "region": f"{view[0].lower()}-region",
        "frame": {
            "path": str(frame),
            "series_uid": series_uid,
            "slice_index": 0,
            "view": view,
        },
        "support_rc": [[0, 1], [1, 2]],
        "binding": [
            {
                "bank": eligible_bank,
                "metric": "signal",
                "source": "acquired_signal",
            },
            {
                "bank": unavailable_bank,
                "metric": "signal",
                "source": "unavailable",
                "reason": f"{unavailable_bank} is not bound to this declared view",
            },
        ],
    }


def _three_view_spec(views: dict[str, list[str]]) -> dict:
    banks = tuple(views)
    return {
        "version": "three-view-fixture-v1",
        "banks": [
            {
                "name": bank,
                "facet": f"{bank} acquired signal",
                "metrics": [{"name": "signal", "kind": "digit"}],
            }
            for bank in banks
        ],
        "profiles": [
            {
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
                    for bank in banks
                ],
                "references": [
                    {
                        "bank": bank,
                        "metric": "signal",
                        "reference_id": f"{bank}-reference-v1",
                        "source": "explicit fixture reference",
                        "units": "stored-value-unit",
                        "low": 12,
                        "high": 14,
                    }
                    for bank in banks
                ],
            }
            for view in views.values()
        ],
    }


def _three_view_observation(
    frame: Path,
    *,
    series_uid: str,
    view: list[str],
    eligible_bank: str,
    banks: tuple[str, ...],
) -> dict:
    return {
        "object": "femur",
        "region": f"{view[0].lower()}-region",
        "frame": {
            "path": str(frame),
            "series_uid": series_uid,
            "slice_index": 0,
            "view": view,
        },
        "support_rc": [[0, 1], [1, 2]],
        "binding": [
            {
                "bank": bank,
                "metric": "signal",
                "source": (
                    "acquired_signal" if bank == eligible_bank else "unavailable"
                ),
                **(
                    {}
                    if bank == eligible_bank
                    else {"reason": f"{bank} is not bound to this declared view"}
                ),
            }
            for bank in banks
        ],
    }


def test_real_dicom_pixels_support_and_missing_reference_are_retained(
    tmp_path: Path,
) -> None:
    frame = tmp_path / "frame.dcm"
    source = np.array([[10, 11, 12], [13, 14, 15]], dtype=np.int16)
    _write_dicom(frame, source)
    recipe = _recipe(frame, _spec())

    study_uid, profiles, metadata = next(acquired_studies({"recipe_data": recipe}))

    assert study_uid == STUDY_UID
    assert len(profiles) == 1
    profile = profiles[0]
    assert profile.scope == 'region:["region:caller-region"]'
    assert profile.bundle.counts[0][0] == 0
    evidence = metadata["observations"][0]
    assert evidence["description_status"] == "missing_reference"
    measurement = evidence["measurements"][0]
    assert measurement["status"] == "missing_reference"
    value_digest = measurement["source_values_digest"]
    available_digest = measurement["source_available_digest"]
    np.testing.assert_array_equal(
        metadata["shared_measurement_arrays"][value_digest], [11, 15]
    )
    np.testing.assert_array_equal(
        metadata["shared_measurement_arrays"][available_digest], [True, True]
    )
    np.testing.assert_array_equal(evidence["support_rc"], [[0, 1], [1, 2]])
    np.testing.assert_array_equal(
        evidence["frame"]["geometry"]["origin_lps"], [10.0, 20.0, 30.0]
    )
    assert evidence["frame"]["geometry"]["basis_lps"] == [
        [0.0, 0.75],
        [0.5, 0.0],
        [0.0, 0.0],
    ]


def test_declared_reference_encodes_exact_low_and_high_rows(tmp_path: Path) -> None:
    frame = tmp_path / "frame.dcm"
    _write_dicom(frame, np.array([[10, 11, 12], [13, 14, 15]], dtype=np.int16))
    spec = _spec(
        references=[
            {
                "bank": "raw_signal",
                "metric": "signal",
                "reference_id": "caller-reference-v1",
                "source": "caller-declared source",
                "units": "stored-value-unit",
                "low": 12,
                "high": 14,
            }
        ]
    )

    _, profiles, metadata = next(
        acquired_studies({"recipe_data": _recipe(frame, spec)})
    )

    measurement = metadata["observations"][0]["measurements"][0]
    assert metadata["observations"][0]["description_status"] == "ok"
    assert measurement["status"] == "ok"
    np.testing.assert_array_equal(
        metadata["shared_measurement_arrays"][measurement["source_values_digest"]],
        [11, 15],
    )
    np.testing.assert_array_equal(
        metadata["shared_measurement_arrays"][measurement["row_codes_digest"]],
        [0, 2],
    )
    assert profiles[0].bundle.counts[0][0] == 1
    assert profiles[0].bundle.counts[0][2] == 1


def test_same_frame_is_decoded_once_for_multiple_regions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    frame = tmp_path / "frame.dcm"
    _write_dicom(frame, np.arange(6, dtype=np.int16).reshape(2, 3))
    first = _recipe(frame, _spec())["studies"][0]["observations"][0]
    second = dict(first, object="tibia", region="second-region", support_rc=[[0, 0]])
    calls = 0
    from knee.diagnosis import inputs

    actual = inputs.read_slice

    def counted(path: Path):
        nonlocal calls
        calls += 1
        return actual(path)

    monkeypatch.setattr(inputs, "read_slice", counted)
    spec = _spec()
    spec["profiles"].append(dict(spec["profiles"][0], object="tibia"))
    recipe = _recipe(frame, spec, [first, second])

    _, profiles, metadata = next(acquired_studies({"recipe_data": recipe}))

    assert calls == 1
    assert len(profiles) == 2
    assert metadata["decoded_frame_count"] == 1
    assert profiles[0].scope == 'region:["region:caller-region"]'


def test_malformed_support_is_named_before_encoding(tmp_path: Path) -> None:
    frame = tmp_path / "frame.dcm"
    _write_dicom(frame, np.arange(6, dtype=np.int16).reshape(2, 3))
    recipe = _recipe(frame, _spec())
    recipe["studies"][0]["observations"][0]["support_rc"] = [[2, 0]]

    with pytest.raises(DiagnosticInputError, match="support_rc_out_of_frame"):
        next(acquired_studies({"recipe_data": recipe}))


def test_cli_argument_recipe_and_separate_spec_paths(tmp_path: Path) -> None:
    frame = tmp_path / "frame.dcm"
    _write_dicom(frame, np.arange(6, dtype=np.int16).reshape(2, 3))
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(_spec()), encoding="utf-8")
    recipe = _recipe(frame, _spec())
    recipe["encoding_spec"] = "spec.json"
    recipe_path = tmp_path / "recipe.json"
    recipe_path.write_text(json.dumps(recipe), encoding="utf-8")

    study_uid, _, _ = next(
        acquired_studies(
            argparse.Namespace(
                diagnostic_inputs=recipe_path,
                diagnostic_output=tmp_path / "separate-output.json",
            )
        )
    )

    assert study_uid == STUDY_UID


def test_duplicate_support_coordinate_is_named(tmp_path: Path) -> None:
    frame = tmp_path / "frame.dcm"
    _write_dicom(frame, np.arange(6, dtype=np.int16).reshape(2, 3))
    recipe = _recipe(frame, _spec())
    recipe["studies"][0]["observations"][0]["support_rc"] = [[0, 1], [0, 1]]

    with pytest.raises(DiagnosticInputError, match="support_rc_duplicate_coordinate"):
        next(acquired_studies({"recipe_data": recipe}))


def test_two_view_composition_keeps_bank_roles_and_is_order_independent(
    tmp_path: Path,
) -> None:
    sagittal = tmp_path / "sagittal.dcm"
    coronal = tmp_path / "coronal.dcm"
    _write_dicom(sagittal, np.array([[10, 11, 12], [13, 14, 15]], dtype=np.int16))
    _write_dicom(
        coronal,
        np.array([[20, 21, 22], [23, 24, 25]], dtype=np.int16),
        series_uid=OTHER_SERIES_UID,
    )
    sag_view = ["Sagittal", "0", "0"]
    cor_view = ["Coronal", "0", "0"]
    sag = _two_view_observation(
        sagittal,
        series_uid=SERIES_UID,
        view=sag_view,
        eligible_bank="sagittal_signal",
        unavailable_bank="coronal_signal",
    )
    cor = _two_view_observation(
        coronal,
        series_uid=OTHER_SERIES_UID,
        view=cor_view,
        eligible_bank="coronal_signal",
        unavailable_bank="sagittal_signal",
    )
    recipe = _recipe(sagittal, _two_view_spec(), [sag, cor])
    recipe["view_distinguished_banks"] = {
        "sagittal_signal": [sag_view],
        "coronal_signal": [cor_view],
    }

    _, profiles_forward, metadata_forward = next(
        acquired_studies({"recipe_data": recipe})
    )
    recipe["studies"][0]["observations"].reverse()
    _, profiles_reverse, metadata_reverse = next(
        acquired_studies({"recipe_data": recipe})
    )

    profile = profiles_forward[0]
    assert profile == profiles_reverse[0]
    assert profile.scope == 'region:["region:coronal-region","region:sagittal-region"]'
    assert len(dict(profile.provenance)) == len(profile.provenance)
    bank_counts = dict(
        zip(
            (bank.name for bank in profile.bundle.layout.banks),
            profile.bundle.counts,
            strict=True,
        )
    )
    assert sum(bank_counts["sagittal_signal"]) == 2
    assert sum(bank_counts["coronal_signal"]) == 2
    by_view = {
        tuple(row["frame"]["view"]): row for row in metadata_forward["observations"]
    }
    assert {
        (row["bank"], row["source_state"])
        for row in by_view[tuple(sag_view)]["measurements"]
    } == {("sagittal_signal", "measured"), ("coronal_signal", "unavailable")}
    assert {
        (row["bank"], row["source_state"])
        for row in by_view[tuple(cor_view)]["measurements"]
    } == {("sagittal_signal", "unavailable"), ("coronal_signal", "measured")}
    assert all(
        "source_values_digest" not in row
        for rows in (
            by_view[tuple(sag_view)]["measurements"],
            by_view[tuple(cor_view)]["measurements"],
        )
        for row in rows
        if row["source_state"] == "unavailable"
    )
    assert profiles_forward == profiles_reverse
    assert metadata_forward["profiles"][0] == metadata_reverse["profiles"][0]


def test_multi_view_composition_refuses_unqualified_bank_marginals(
    tmp_path: Path,
) -> None:
    sagittal = tmp_path / "sagittal.dcm"
    coronal = tmp_path / "coronal.dcm"
    _write_dicom(sagittal, np.arange(6, dtype=np.int16).reshape(2, 3))
    _write_dicom(
        coronal,
        np.arange(6, dtype=np.int16).reshape(2, 3),
        series_uid=OTHER_SERIES_UID,
    )
    sag_view = ["Sagittal", "0", "0"]
    cor_view = ["Coronal", "0", "0"]
    sag = _two_view_observation(
        sagittal,
        series_uid=SERIES_UID,
        view=sag_view,
        eligible_bank="sagittal_signal",
        unavailable_bank="coronal_signal",
    )
    cor = _two_view_observation(
        coronal,
        series_uid=OTHER_SERIES_UID,
        view=cor_view,
        eligible_bank="coronal_signal",
        unavailable_bank="sagittal_signal",
    )
    recipe = _recipe(sagittal, _two_view_spec(), [sag, cor])

    with pytest.raises(
        DiagnosticInputError, match="composition_bank_view_not_exclusive"
    ):
        next(acquired_studies({"recipe_data": recipe}))


@pytest.mark.parametrize(
    ("field", "value"),
    [("series_uid", OTHER_SERIES_UID), ("slice_index", 8)],
)
def test_repeated_frame_rejects_contradictory_address_declaration(
    tmp_path: Path, field: str, value: object
) -> None:
    frame = tmp_path / "frame.dcm"
    _write_dicom(frame, np.arange(6, dtype=np.int16).reshape(2, 3))
    first = _recipe(frame, _spec())["studies"][0]["observations"][0]
    second = dict(first, region="second", frame=dict(first["frame"], **{field: value}))

    with pytest.raises(DiagnosticInputError, match="repeated_frame_address_mismatch"):
        next(
            acquired_studies({"recipe_data": _recipe(frame, _spec(), [first, second])})
        )


def test_single_view_semantic_layout_identity_binds_the_declared_view(
    tmp_path: Path,
) -> None:
    frame = tmp_path / "frame.dcm"
    _write_dicom(frame, np.arange(6, dtype=np.int16).reshape(2, 3))
    sagittal_recipe = _recipe(frame, _spec())
    coronal_recipe = _recipe(frame, _spec())
    coronal_recipe["encoding_spec"]["profiles"][0]["view"] = [
        "Coronal",
        "0",
        "0",
    ]
    coronal_recipe["studies"][0]["observations"][0]["frame"]["view"] = [
        "Coronal",
        "0",
        "0",
    ]

    _, sagittal_profiles, _ = next(acquired_studies({"recipe_data": sagittal_recipe}))
    _, coronal_profiles, _ = next(acquired_studies({"recipe_data": coronal_recipe}))

    assert sagittal_profiles[0].bundle.layout.layout_id != (
        coronal_profiles[0].bundle.layout.layout_id
    )
    assert sagittal_profiles[0].bundle.layout.banks == (
        coronal_profiles[0].bundle.layout.banks
    )
    assert (
        cosine_terms(
            sagittal_profiles[0].bundle,
            coronal_profiles[0].bundle,
            ("raw_signal",),
        ).code
        is CountCode.IDENTITY_MISMATCH
    )


def test_multiview_bank_binding_identity_changes_when_bank_view_assignment_changes(
    tmp_path: Path,
) -> None:
    sagittal = tmp_path / "sagittal.dcm"
    coronal = tmp_path / "coronal.dcm"
    _write_dicom(sagittal, np.arange(6, dtype=np.int16).reshape(2, 3))
    _write_dicom(
        coronal,
        np.arange(6, dtype=np.int16).reshape(2, 3),
        series_uid=OTHER_SERIES_UID,
    )
    sag_view = ["Sagittal", "0", "0"]
    cor_view = ["Coronal", "0", "0"]

    def make_recipe(sagittal_bank: str, coronal_bank: str) -> dict:
        sagittal_observation = _two_view_observation(
            sagittal,
            series_uid=SERIES_UID,
            view=sag_view,
            eligible_bank=sagittal_bank,
            unavailable_bank=(
                "coronal_signal"
                if sagittal_bank == "sagittal_signal"
                else "sagittal_signal"
            ),
        )
        coronal_observation = _two_view_observation(
            coronal,
            series_uid=OTHER_SERIES_UID,
            view=cor_view,
            eligible_bank=coronal_bank,
            unavailable_bank=(
                "sagittal_signal"
                if coronal_bank == "coronal_signal"
                else "coronal_signal"
            ),
        )
        recipe = _recipe(
            sagittal,
            _two_view_spec(),
            [sagittal_observation, coronal_observation],
        )
        recipe["view_distinguished_banks"] = {
            sagittal_bank: [sag_view],
            coronal_bank: [cor_view],
        }
        return recipe

    original = make_recipe("sagittal_signal", "coronal_signal")
    reassigned = make_recipe("coronal_signal", "sagittal_signal")
    _, original_profiles, _ = next(acquired_studies({"recipe_data": original}))
    _, reassigned_profiles, _ = next(acquired_studies({"recipe_data": reassigned}))

    assert original_profiles[0].bundle.layout.layout_id != (
        reassigned_profiles[0].bundle.layout.layout_id
    )
    assert (
        cosine_terms(
            original_profiles[0].bundle,
            reassigned_profiles[0].bundle,
            ("sagittal_signal", "coronal_signal"),
        ).code
        is CountCode.IDENTITY_MISMATCH
    )


def test_measurement_identity_excludes_study_file_values_and_reference_availability(
    tmp_path: Path,
) -> None:
    first_frame = tmp_path / "first.dcm"
    second_frame = tmp_path / "second.dcm"
    _write_dicom(first_frame, np.array([[10, 11, 12], [13, 14, 15]], dtype=np.int16))
    other_study_uid = "1.2.826.0.1.3680043.10.543.99"
    _write_dicom(
        second_frame,
        np.array([[90, 91, 92], [93, 94, 95]], dtype=np.int16),
        study_uid=other_study_uid,
    )
    first_recipe = _recipe(first_frame, _spec())
    second_recipe = _recipe(second_frame, _spec())
    second_recipe["studies"][0]["study_uid"] = other_study_uid
    second_recipe["studies"][0]["observations"][0]["region"] = "different-region"
    second_recipe["studies"][0]["observations"][0]["label"] = "changed label"
    references = [
        {
            "bank": "raw_signal",
            "metric": "signal",
            "reference_id": "fixture-reference-v1",
            "source": "fixture source",
            "units": "stored-value-unit",
            "low": 12,
            "high": 14,
        }
    ]
    referenced_recipe = _recipe(first_frame, _spec(references=references))

    _, first_profiles, first_metadata = next(
        acquired_studies({"recipe_data": first_recipe})
    )
    _, second_profiles, second_metadata = next(
        acquired_studies({"recipe_data": second_recipe})
    )
    _, referenced_profiles, referenced_metadata = next(
        acquired_studies({"recipe_data": referenced_recipe})
    )

    first_layout_id = first_profiles[0].bundle.layout.layout_id
    assert second_profiles[0].bundle.layout.layout_id == first_layout_id
    # The original reference-set identity remains part of CountLayout; the
    # added measurement-contract digest itself is independent of that status.
    assert referenced_profiles[0].bundle.layout.layout_id != first_layout_id
    assert (
        first_metadata["measurement_contract_ids"]["femur"]
        == second_metadata["measurement_contract_ids"]["femur"]
        == referenced_metadata["measurement_contract_ids"]["femur"]
    )
    assert (
        first_metadata["observations"][0]["source_count_layout_id"]
        != (referenced_metadata["observations"][0]["source_count_layout_id"])
    )
    assert (
        first_metadata["observations"][0]["description_status"] == "missing_reference"
    )
    assert referenced_metadata["observations"][0]["description_status"] == "ok"


@pytest.mark.parametrize(
    ("field", "changed_value"),
    [
        ("producer", "different producer"),
        ("mode", "cheap/another-mode"),
        ("dependencies", ["different declared input"]),
    ],
)
def test_measurement_identity_binds_producer_mode_and_dependencies(
    tmp_path: Path, field: str, changed_value: object
) -> None:
    frame = tmp_path / "frame.dcm"
    _write_dicom(frame, np.arange(6, dtype=np.int16).reshape(2, 3))
    original = _recipe(frame, _spec())
    changed = _recipe(frame, _spec())
    changed[field] = changed_value

    _, original_profiles, _ = next(acquired_studies({"recipe_data": original}))
    _, changed_profiles, _ = next(acquired_studies({"recipe_data": changed}))

    assert original_profiles[0].bundle.layout.layout_id != (
        changed_profiles[0].bundle.layout.layout_id
    )


def test_single_view_contract_identity_does_not_depend_on_observation_listing_order(
    tmp_path: Path,
) -> None:
    frame = tmp_path / "frame.dcm"
    _write_dicom(frame, np.arange(6, dtype=np.int16).reshape(2, 3))
    first = _recipe(frame, _spec())["studies"][0]["observations"][0]
    second = dict(first, object="tibia", region="second-region", support_rc=[[0, 0]])
    spec = _spec()
    spec["profiles"].append(dict(spec["profiles"][0], object="tibia"))
    recipe = _recipe(frame, spec, [first, second])

    _, forward, forward_metadata = next(acquired_studies({"recipe_data": recipe}))
    recipe["studies"][0]["observations"].reverse()
    _, reverse, reverse_metadata = next(acquired_studies({"recipe_data": recipe}))

    assert forward == reverse
    assert (
        forward_metadata["measurement_contract_ids"]
        == reverse_metadata["measurement_contract_ids"]
    )
    single_object_recipe = _recipe(frame, _spec())
    _, single_object_profiles, _ = next(
        acquired_studies({"recipe_data": single_object_recipe})
    )
    assert forward[0].bundle.layout.layout_id == (
        single_object_profiles[0].bundle.layout.layout_id
    )


def test_explicit_three_view_identity_is_complete_when_a_declared_view_is_missing(
    tmp_path: Path,
) -> None:
    views = {
        "sagittal_signal": ["Sagittal", "0", "0"],
        "coronal_signal": ["Coronal", "0", "0"],
        "axial_signal": ["Axial", "0", "0"],
    }
    frames = {
        "sagittal_signal": (tmp_path / "sagittal.dcm", SERIES_UID),
        "coronal_signal": (tmp_path / "coronal.dcm", OTHER_SERIES_UID),
        "axial_signal": (tmp_path / "axial.dcm", AXIAL_SERIES_UID),
    }
    for index, (path, series_uid) in enumerate(frames.values()):
        _write_dicom(
            path,
            np.arange(6, dtype=np.int16).reshape(2, 3) + index * 20,
            series_uid=series_uid,
        )
    banks = tuple(views)
    vdb = {bank: [view] for bank, view in views.items()}
    spec = _three_view_spec(views)
    observations = [
        _three_view_observation(
            frames[bank][0],
            series_uid=frames[bank][1],
            view=views[bank],
            eligible_bank=bank,
            banks=banks,
        )
        for bank in ("sagittal_signal", "coronal_signal")
    ]
    two_view_recipe = _recipe(frames["sagittal_signal"][0], spec, observations)
    two_view_recipe["view_distinguished_banks"] = vdb
    one_view_recipe = _recipe(frames["sagittal_signal"][0], spec, [observations[0]])
    one_view_recipe["view_distinguished_banks"] = dict(reversed(list(vdb.items())))

    _, two_view_profiles, two_view_metadata = next(
        acquired_studies({"recipe_data": two_view_recipe})
    )
    _, one_view_profiles, one_view_metadata = next(
        acquired_studies({"recipe_data": one_view_recipe})
    )

    two_view = two_view_profiles[0]
    one_view = one_view_profiles[0]
    assert two_view.bundle.layout.layout_id == one_view.bundle.layout.layout_id
    assert two_view.bundle.layout == one_view.bundle.layout
    assert (
        two_view_metadata["measurement_contract_ids"]
        == one_view_metadata["measurement_contract_ids"]
    )
    contract_id = one_view_metadata["measurement_contract_ids"]["femur"]
    assert contract_id
    assert one_view_metadata["profile_measurement_contract_ids"] == {
        "femur": contract_id
    }
    assert two_view_metadata["profile_measurement_contract_ids"] == {
        "femur": contract_id
    }
    assert dict(one_view.bank_statuses)["axial_signal"] == "signal=silent"
    counts = dict(zip(banks, one_view.bundle.counts, strict=True))
    assert sum(counts["sagittal_signal"]) == 2
    assert not any(counts["coronal_signal"])
    assert not any(counts["axial_signal"])
    one_view_provenance = dict(one_view.provenance)
    assert (
        contract_id in one_view_provenance["observation_0000.measurement_contract_id"]
    )


def test_explicit_single_view_refuses_acquisition_from_another_banks_view(
    tmp_path: Path,
) -> None:
    views = {
        "sagittal_signal": ["Sagittal", "0", "0"],
        "coronal_signal": ["Coronal", "0", "0"],
        "axial_signal": ["Axial", "0", "0"],
    }
    coronal = tmp_path / "coronal.dcm"
    _write_dicom(coronal, np.arange(6, dtype=np.int16).reshape(2, 3))
    banks = tuple(views)
    observation = _three_view_observation(
        coronal,
        series_uid=SERIES_UID,
        view=views["coronal_signal"],
        eligible_bank="sagittal_signal",
        banks=banks,
    )
    recipe = _recipe(coronal, _three_view_spec(views), [observation])
    recipe["view_distinguished_banks"] = {bank: [view] for bank, view in views.items()}

    with pytest.raises(
        DiagnosticInputError,
        match="composition_view_binding_mismatch:femur:sagittal_signal",
    ):
        next(acquired_studies({"recipe_data": recipe}))


def test_declared_region_scopes_enable_partial_view_question_recall(
    tmp_path: Path,
) -> None:
    views = {
        "sagittal_signal": ["Sagittal", "0", "0"],
        "coronal_signal": ["Coronal", "0", "0"],
        "axial_signal": ["Axial", "0", "0"],
    }
    frames = {
        "sagittal_signal": (tmp_path / "train-sagittal.dcm", SERIES_UID),
        "coronal_signal": (tmp_path / "train-coronal.dcm", OTHER_SERIES_UID),
        "query-sagittal": (tmp_path / "query-sagittal.dcm", SERIES_UID),
    }
    train_uid = STUDY_UID
    query_uid = "1.2.826.0.1.3680043.10.543.5"
    for index, (name, (path, series_uid)) in enumerate(frames.items()):
        _write_dicom(
            path,
            np.arange(6, dtype=np.int16).reshape(2, 3) + index * 20,
            series_uid=series_uid,
            study_uid=query_uid if name.startswith("query-") else train_uid,
        )
    banks = tuple(views)
    vdb = {bank: [view] for bank, view in views.items()}
    region_scopes = {"femur": ["sagittal-region", "coronal-region", "axial-region"]}
    spec = _three_view_spec(views)
    train_observations = [
        _three_view_observation(
            frames[bank][0],
            series_uid=frames[bank][1],
            view=views[bank],
            eligible_bank=bank,
            banks=banks,
        )
        for bank in ("sagittal_signal", "coronal_signal")
    ]
    query_observation = _three_view_observation(
        frames["query-sagittal"][0],
        series_uid=frames["query-sagittal"][1],
        view=views["sagittal_signal"],
        eligible_bank="sagittal_signal",
        banks=banks,
    )
    train_recipe = _recipe(frames["sagittal_signal"][0], spec, train_observations)
    train_recipe["view_distinguished_banks"] = vdb
    train_recipe["region_scopes"] = region_scopes
    query_recipe = _recipe(frames["query-sagittal"][0], spec, [query_observation])
    query_recipe["studies"][0]["study_uid"] = query_uid
    query_recipe["view_distinguished_banks"] = dict(reversed(list(vdb.items())))
    query_recipe["region_scopes"] = region_scopes

    _, train_profiles, train_metadata = next(
        acquired_studies({"recipe_data": train_recipe})
    )
    _, query_profiles, query_metadata = next(
        acquired_studies({"recipe_data": query_recipe})
    )
    question = Question(
        "femur-condition",
        "diagnosis/femur-condition",
        ("femur",),
        banks=tuple(f"object/femur/{bank}" for bank in banks),
    )
    train_question_profile = compose_question_profile(train_profiles, question)
    query_question_profile = compose_question_profile(query_profiles, question)
    snapshot = Snapshot(
        "fixture-revision",
        cases=(
            Case(
                "train-case",
                train_uid,
                train_question_profile,
                (Call(question.question_id, 1, "fixture-label"),),
                "fixture-revision",
            ),
        ),
    )

    result = recall(query_question_profile, question, snapshot)

    assert result["outcome"] == "proposal"
    assert result["case_terms"][0]["common_speaking_banks"] == [
        "object/femur/sagittal_signal"
    ]
    train_scope = dict(train_metadata["profiles"][0].provenance)[
        "declared_region_scopes"
    ]
    query_scope = dict(query_metadata["profiles"][0].provenance)[
        "declared_region_scopes"
    ]
    assert train_scope == query_scope
    assert train_profiles[0].scope == query_profiles[0].scope
    assert train_profiles[0].bundle.layout.layout_id == (
        query_profiles[0].bundle.layout.layout_id
    )
    assert train_metadata["observations"][0]["region"] == "sagittal-region"
    assert query_metadata["observations"][0]["region"] == "sagittal-region"
    assert query_metadata["observations"][0]["scope"] == "region:sagittal-region"
    assert query_metadata["observations"][0]["declared_region_scopes"] == [
        "axial-region",
        "coronal-region",
        "sagittal-region",
    ]
    query_counts = dict(zip(banks, query_profiles[0].bundle.counts, strict=True))
    assert sum(query_counts["sagittal_signal"]) == 2
    assert not any(query_counts["coronal_signal"])
    assert not any(query_counts["axial_signal"])

    changed_region_recipe = dict(query_recipe)
    changed_region_recipe["region_scopes"] = {
        "femur": ["sagittal-region", "coronal-region", "other-axial-region"]
    }
    _, changed_profiles, _ = next(
        acquired_studies({"recipe_data": changed_region_recipe})
    )
    changed_question_profile = compose_question_profile(changed_profiles, question)
    assert changed_question_profile.bundle.layout.layout_id != (
        query_question_profile.bundle.layout.layout_id
    )
    assert recall(changed_question_profile, question, snapshot)["outcome"] == (
        "incompatible_encoding"
    )

    undeclared_recipe = dict(query_recipe)
    undeclared_observation = dict(query_observation)
    undeclared_observation["region"] = "unlisted-region"
    undeclared_recipe["studies"] = [
        dict(query_recipe["studies"][0], observations=[undeclared_observation])
    ]
    with pytest.raises(
        DiagnosticInputError,
        match="region_not_declared_for_object:femur:unlisted-region",
    ):
        next(acquired_studies({"recipe_data": undeclared_recipe}))


@pytest.mark.parametrize(
    ("orientation", "spacing", "coordinate_rc", "expected"),
    [
        (
            [1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            [2.0, 3.0],
            (4, 5),
            (25.0, 28.0, 30.0),
        ),
        (
            [
                0.7071067811865476,
                0.7071067811865476,
                0.0,
                -0.5,
                0.5,
                0.7071067811865476,
            ],
            [2.0, 3.0],
            (4, 5),
            (16.6066017178, 34.6066017178, 35.6568542495),
        ),
    ],
)
def test_acquired_geometry_maps_native_rc_to_dicom_lps(
    tmp_path: Path,
    orientation: list[float],
    spacing: list[float],
    coordinate_rc: tuple[int, int],
    expected: tuple[float, float, float],
) -> None:
    import pydicom

    from knee.encoding.spatial import SpatialContext, native_rc_reading

    frame_path = tmp_path / "anisotropic-oblique.dcm"
    _write_dicom(frame_path, np.arange(72, dtype=np.int16).reshape(8, 9))
    dataset = pydicom.dcmread(frame_path)
    dataset.ImageOrientationPatient = orientation
    dataset.PixelSpacing = spacing
    dataset.save_as(frame_path, enforce_file_format=True)

    observation = {
        "object": "femur",
        "region": "caller-region",
        "frame": {
            "path": str(frame_path),
            "series_uid": SERIES_UID,
            "slice_index": 7,
            "view": ["Sagittal", "0", "0"],
        },
        "support_rc": [list(coordinate_rc)],
        "binding": [
            {
                "bank": "raw_signal",
                "metric": "signal",
                "source": "acquired_signal",
            }
        ],
    }
    _, _, metadata = next(
        acquired_studies({"recipe_data": _recipe(frame_path, _spec(), [observation])})
    )
    frame = metadata["observations"][0]["frame"]["geometry"]

    context = SpatialContext(
        "femur",
        "complete",
        expected,
        (1.0, 1.0, 1.0),
        {},
        "R",
        1.0,
        "fixture",
        "fixture",
        "ok",
    )
    reading = native_rc_reading(
        context,
        coordinate_rc,
        frame=frame,
        view="Sagittal",
        slice_index=7,
        address={"series_uid": SERIES_UID},
    )

    assert reading.coordinate_code == "ok"
    np.testing.assert_allclose(reading.point_lps, expected, rtol=0.0, atol=1e-9)
