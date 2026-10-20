from __future__ import annotations

import argparse
import json
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import (
    ExplicitVRLittleEndian,
    SecondaryCaptureImageStorage,
    generate_uid,
)

from knee.diagnosis import pipeline
from knee.diagnosis.cohort import CohortError, load_cohort
from knee.diagnosis.composition import compose_question_profile
from knee.diagnosis.inputs import acquired_studies
from knee.diagnosis.models import Call, Case, Profile, Question, Snapshot
from knee.diagnosis.store import write_store
from knee.encoding.counts import BankLayout, CountBundle, CountLayout

_SCHEMA = "knee.diagnostic-cohort/v1"
_SERIES_UID = "1.2.826.0.1.3680043.10.543.2"
_SAGITTAL_VIEW = ["Sagittal", "0", "0"]


def _cohort(path: Path, partitions: dict, groups: dict | None = None) -> Path:
    value = {
        "schema": _SCHEMA,
        "partitions": partitions,
        "disjoint_partitions": [],
    }
    if groups is not None:
        value["source_groups"] = groups
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _profile(uid: str) -> Profile:
    layout = CountLayout(
        "cohort-fixture-layout",
        "cohort-fixture-carrier",
        (BankLayout("signal", 3),),
    )
    return Profile(
        subject="acl",
        bundle=CountBundle(layout, ((1, 0, 0),)),
        mode="full",
        scope="object:acl",
        source_id=uid,
        bank_statuses=(("signal", "observed"),),
    )


def _question(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema": "knee.diagnostic-questions/v1",
                "questions": [
                    {
                        "question_id": "ACL",
                        "objects": ["acl"],
                        "banks": ["object/acl/signal"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _args(
    *, products, memory, output, questions, cohort=None, partition=None, labels=None
):
    return argparse.Namespace(
        diagnostic_mode="capacity" if labels is not None else "infer",
        diagnostic_products=products,
        diagnostic_inputs=None,
        diagnostic_memory=memory,
        diagnostic_labels=labels,
        diagnostic_output=output,
        diagnostic_revision="",
        diagnostic_pair_products=None,
        diagnostic_questions=questions,
        diagnostic_trust=None,
        diagnostic_cohort=cohort,
        diagnostic_partition=partition,
        draw=False,
    )


class _ManifestProduct:
    def __init__(self, manifest: dict):
        self.manifest = manifest

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None


def _product_directory(tmp_path: Path, uids: tuple[str, ...], monkeypatch):
    import knee.encoding.product as product_module
    from knee.diagnosis import product_cases

    root = tmp_path / "products"
    root.mkdir(parents=True)
    paths = {}
    manifests = {}
    for index, uid in enumerate(uids):
        path = root / f"artifact-{index:02d}.h5"
        path.write_bytes(b"metadata-only fixture")
        paths[uid] = path
        manifests[path] = {"study_uid": uid}

    @contextmanager
    def fake_open_product(path):
        yield _ManifestProduct(manifests[Path(path)])

    profile_calls = []

    def fake_profiles(path, mode="full"):
        uid = next(uid for uid, product_path in paths.items() if product_path == path)
        profile_calls.append(uid)
        return (_profile(uid),)

    monkeypatch.setattr(product_module, "open_product", fake_open_product)
    monkeypatch.setattr(product_cases, "profiles_from_product", fake_profiles)
    return root, paths, profile_calls


def _memory_with_group_cases(path: Path, question: Question) -> None:
    cases = []
    for uid, group, sign in (
        ("related-case", "patient-A", 1),
        ("other-case", "patient-B", -1),
    ):
        source = pipeline._attach_source_group((_profile(uid),), group)
        composed = compose_question_profile(source, question)
        cases.append(
            Case(
                uid,
                uid,
                composed,
                (Call("ACL", sign, "fixture-label"),),
                "fixture-r1",
            )
        )
    write_store(path, Snapshot("fixture-r1", tuple(cases)))


def test_product_cohort_preflights_manifest_then_processes_selected_order_and_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    uid_a, uid_b, uid_excluded = "uid-a", "uid-b", "uid-excluded"
    products, paths, profile_calls = _product_directory(
        tmp_path, (uid_a, uid_b, uid_excluded), monkeypatch
    )
    cohort_path = _cohort(
        tmp_path / "cohort.json",
        {"selected": [uid_b, uid_a], "other": [uid_excluded]},
        {uid_a: "patient-A", uid_b: "patient-B", uid_excluded: "patient-C"},
    )
    questions = _question(tmp_path / "questions.json")
    question = next(q for q in pipeline._questions(questions) if q.question_id == "ACL")
    memory = tmp_path / "memory.json"
    _memory_with_group_cases(memory, question)
    labels = tmp_path / "labels.csv"
    labels.write_text("fixture labels are supplied by the adapter", encoding="utf-8")
    from knee.diagnosis import teaching

    monkeypatch.setattr(
        teaching,
        "labels_from_csv",
        lambda _path: {uid_b: {"ACL": 1}, uid_a: {"ACL": 1}},
    )
    output = tmp_path / "out"

    result = pipeline.run_diagnostic_cli(
        _args(
            products=products,
            memory=memory,
            output=output,
            questions=questions,
            cohort=cohort_path,
            partition="selected",
            labels=labels,
        )
    )

    assert profile_calls == [uid_b, uid_a]
    assert result["cohort"] == {
        "source": str(cohort_path.resolve()),
        "sha256": load_cohort(cohort_path).sha256,
        "partition": "selected",
        "selected_uids": [uid_b, uid_a],
    }
    assert result["studies"] == 2
    assert not (output / "studies" / f"{uid_excluded}.json").exists()
    query_record = json.loads((output / "studies" / f"{uid_a}.json").read_text())
    call = query_record["questions"]["ACL"]
    assert "related-case" in call["source_group_excluded_case_ids"]
    assert "other-case" in [row["case_id"] for row in call["case_terms"]]
    from knee.json_store import load_json

    source = load_json(output / "sources" / uid_a / "manifest.json")["source"]
    assert source["cohort"]["source_group"] == "patient-A"
    assert source["cohort"]["selected_uids"] == [uid_b, uid_a]
    assert paths[uid_excluded].exists()


def test_product_partition_missing_or_duplicate_uid_fails_before_profile_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from knee.diagnosis import product_cases

    products, _paths, _calls = _product_directory(
        tmp_path, ("uid-a", "uid-b"), monkeypatch
    )
    cohort_path = _cohort(tmp_path / "cohort.json", {"selected": ["uid-missing"]})
    questions = _question(tmp_path / "questions.json")
    memory = tmp_path / "memory.json"
    write_store(memory, Snapshot("fixture-r1", ()))
    calls = []
    monkeypatch.setattr(
        product_cases,
        "profiles_from_product",
        lambda *_args, **_kwargs: (
            calls.append("profile") or pytest.fail("profile read")
        ),
    )

    with pytest.raises(
        pipeline.DiagnosticRunError, match="cohort_requested_uid_missing"
    ):
        pipeline.run_diagnostic_cli(
            _args(
                products=products,
                memory=memory,
                output=tmp_path / "missing-out",
                questions=questions,
                cohort=cohort_path,
                partition="selected",
            )
        )
    assert calls == []

    ambiguous_products, _paths, _calls = _product_directory(
        tmp_path / "ambiguous", ("uid-a", "uid-a"), monkeypatch
    )
    ambiguous_path = _cohort(
        tmp_path / "ambiguous-cohort.json", {"selected": ["uid-a"]}
    )
    with pytest.raises(
        pipeline.DiagnosticRunError, match="cohort_available_uid_ambiguous"
    ):
        pipeline.run_diagnostic_cli(
            _args(
                products=ambiguous_products,
                memory=memory,
                output=tmp_path / "ambiguous-out",
                questions=questions,
                cohort=ambiguous_path,
                partition="selected",
            )
        )
    assert calls == []


def test_malformed_cohort_flag_pair_is_named_before_source_access(tmp_path: Path):
    questions = _question(tmp_path / "questions.json")
    with pytest.raises(
        pipeline.DiagnosticRunError,
        match="diagnostic_cohort_and_partition_must_be_paired",
    ):
        pipeline.run_diagnostic_cli(
            _args(
                products=tmp_path / "must-not-open",
                memory=tmp_path / "must-not-open-memory",
                output=tmp_path / "out",
                questions=questions,
                cohort=tmp_path / "cohort.json",
                partition=None,
            )
        )


def _write_dicom(path: Path, study_uid: str, pixels: np.ndarray) -> None:
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    meta.ImplementationClassUID = generate_uid()
    dataset = FileDataset(str(path), {}, file_meta=meta, preamble=b"\0" * 128)
    dataset.SOPClassUID = meta.MediaStorageSOPClassUID
    dataset.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    dataset.PatientName = "Cohort^Fixture"
    dataset.PatientID = "cohort-fixture"
    dataset.StudyInstanceUID = study_uid
    dataset.SeriesInstanceUID = _SERIES_UID
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
    dataset.PixelData = np.asarray(pixels, dtype="<i2").tobytes()
    dataset.save_as(path, enforce_file_format=True)


def _recipe_observation(path: Path) -> dict:
    return {
        "object": "femur",
        "region": "caller-region",
        "frame": {
            "path": str(path),
            "series_uid": _SERIES_UID,
            "slice_index": 0,
            "view": _SAGITTAL_VIEW,
        },
        "support_rc": [[0, 1], [1, 2]],
        "binding": [
            {"bank": "raw_signal", "metric": "signal", "source": "acquired_signal"}
        ],
    }


def _recipe_spec() -> dict:
    return {
        "version": "cohort-input-v1",
        "banks": [
            {
                "name": "raw_signal",
                "facet": "fixture acquired signal",
                "metrics": [{"name": "signal", "kind": "digit"}],
            }
        ],
        "profiles": [
            {
                "object": "femur",
                "provenance": "native",
                "kind": "reading",
                "support": "declared_region",
                "view": _SAGITTAL_VIEW,
                "readings": [
                    {
                        "bank": "raw_signal",
                        "metric": "signal",
                        "value": "acquired_plane",
                        "available": "finite_pixels",
                    }
                ],
                "references": [],
            }
        ],
    }


def _acquired_recipe(entries: list[tuple[str, Path]]) -> dict:
    return {
        "schema": "knee.diagnostic-inputs/v1",
        "mode": "cheap/cohort-fixture-v1",
        "producer": "caller-addressed fixture",
        "dependencies": ["stored pixels", "caller coordinates"],
        "encoding_spec": _recipe_spec(),
        "studies": [
            {
                "study_uid": uid,
                "observations": [_recipe_observation(path)],
            }
            for uid, path in entries
        ],
    }


def test_acquired_cohort_selects_order_before_decoding_and_excludes_other_frames(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    uids = (
        "1.2.826.0.1.3680043.10.543.11",
        "1.2.826.0.1.3680043.10.543.12",
        "1.2.826.0.1.3680043.10.543.13",
    )
    paths = tuple(tmp_path / f"opaque-name-{index}.dcm" for index in range(3))
    for index, (uid, path) in enumerate(zip(uids, paths, strict=True)):
        _write_dicom(path, uid, np.arange(6, dtype=np.int16).reshape(2, 3) + index)
    recipe = _acquired_recipe(list(zip(uids, paths, strict=True)))
    cohort_path = _cohort(
        tmp_path / "cohort.json",
        {"chosen": [uids[1], uids[0]], "excluded": [uids[2]]},
    )
    cohort = load_cohort(cohort_path)
    from knee.diagnosis import inputs

    actual = inputs.read_slice
    decoded = []

    def record_read(path):
        decoded.append(Path(path))
        return actual(path)

    monkeypatch.setattr(inputs, "read_slice", record_read)
    outputs = list(
        acquired_studies(
            {"recipe_data": recipe}, cohort=cohort, partition_name="chosen"
        )
    )
    assert [uid for uid, _, _ in outputs] == [uids[1], uids[0]]
    assert decoded == [paths[1], paths[0]]
    assert all(metadata["decoded_frame_count"] == 1 for _, _, metadata in outputs)


@pytest.mark.parametrize("available", [["uid-a"], ["uid-a", "uid-a"]])
def test_acquired_missing_or_ambiguous_selected_uid_fails_before_read_slice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, available: list[str]
) -> None:
    valid_uid = "1.2.826.0.1.3680043.10.543.22"
    available = [valid_uid] * len(available)
    path = tmp_path / "frame.dcm"
    _write_dicom(path, valid_uid, np.arange(6, dtype=np.int16).reshape(2, 3))
    entries = [(uid, path) for uid in available]
    recipe = _acquired_recipe(entries)
    requested = (
        [valid_uid, "1.2.826.0.1.3680043.10.543.23"]
        if len(available) == 1
        else [valid_uid]
    )
    cohort_path = _cohort(tmp_path / "cohort.json", {"chosen": requested})
    cohort = load_cohort(cohort_path)
    from knee.diagnosis import inputs

    calls = []
    monkeypatch.setattr(inputs, "read_slice", lambda *_: calls.append("read"))
    with pytest.raises(CohortError):
        list(
            acquired_studies(
                {"recipe_data": recipe}, cohort=cohort, partition_name="chosen"
            )
        )
    assert calls == []


def test_existing_no_cohort_route_has_no_cohort_record_or_source_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    products, _paths, profile_calls = _product_directory(
        tmp_path, ("uid-a",), monkeypatch
    )
    questions = _question(tmp_path / "questions.json")
    memory = tmp_path / "memory.json"
    write_store(memory, Snapshot("fixture-r1", ()))
    output = tmp_path / "out"

    result = pipeline.run_diagnostic_cli(
        _args(products=products, memory=memory, output=output, questions=questions)
    )

    assert profile_calls == ["uid-a"]
    assert "cohort" not in result
    assert (
        "cohort"
        not in json.loads((output / "studies" / "uid-a.json").read_text())["source"]
    )
