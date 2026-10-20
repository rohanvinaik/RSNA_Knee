"""Independent command-boundary checks using serialized retained H5 products."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path

import pytest

from knee.diagnosis.models import Snapshot
from knee.diagnosis.store import write_store
from knee.encoding import h5_store
from knee.encoding.places import (
    BankSpec,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    compile_layout,
)
from knee.study.tables import LABELS, TRAIN_COLUMNS

LANE = Path(__file__).resolve().parents[1]
RUNNER = LANE / "scripts" / "run_interiors.py"


def _manifest(uid: str, *, silent: bool = False) -> dict:
    spec = LayoutSpec(
        "retained-v1",
        "carrier-retained-v1",
        (
            BankSpec(
                "signal", "signal facet", (MetricSpec("tone", MetricKind.DIGIT, ()),)
            ),
        ),
    )
    compiled = compile_layout(spec)
    assert compiled is not None
    reference = "reference:signal:v1"
    count_id = f"{compiled.version}:{compiled.fingerprint}:{reference}"
    sparse_counts = [] if silent else [["signal", 4, 2], ["signal", 9, 1]]
    return {
        "study_uid": uid,
        "encoded_arrays": {},
        "object_composition": {
            "schema": "knee_object_profiles/v1",
            "carrier_identity": compiled.carrier_id,
            "layout_fingerprint": compiled.fingerprint,
            "registry_fingerprint": "registry-digest",
            "layout": {
                "version": compiled.version,
                "carrier_id": compiled.carrier_id,
                "fingerprint": compiled.fingerprint,
                "banks": [
                    {
                        "name": "signal",
                        "facet": "signal facet",
                        "metrics": [{"name": "tone", "kind": "digit", "words": []}],
                    }
                ],
            },
            "registry": [],
            "objects": {
                "joint_fluid": {
                    "status": "silent" if silent else "partial",
                    "preparation_status": "ok",
                    "detail": "",
                    "reference_set_identity": reference,
                    "count_layout_id": count_id,
                    "sparse_counts": sparse_counts,
                    "assembly": {
                        "code": "silent" if silent else "partial",
                        "outcomes": ["silent"] if silent else ["partial", "silent"],
                        "batches": [
                            {
                                "bank": "signal",
                                "status": "silent" if silent else "partial",
                            }
                        ],
                        "conflicts": [],
                        "mismatches": [],
                        "malformed": [],
                    },
                    "batch_index_maps": [],
                    "spatial_context": None,
                }
            },
            "additions": [],
        },
    }


def _write_product(path: Path, uid: str, *, silent: bool = False) -> Path:
    pytest.importorskip("h5py")
    path.mkdir(parents=True, exist_ok=True)
    product = path / f"{uid}.h5"
    h5_store.write_h5(product, _manifest(uid, silent=silent), {})
    return product


def _write_questions(
    path: Path, *, role: str = "joint_fluid", bank: str = "signal"
) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema": "knee.diagnostic-questions/v1",
                "questions": [
                    {
                        "question_id": question,
                        "objects": [role],
                        "banks": [f"object/{role}/{bank}"],
                        "bank_prefixes": [],
                        "context_keys": [],
                    }
                    for question in LABELS
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _write_labels(path: Path, rows: dict[str, dict[str, str]]) -> Path:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(TRAIN_COLUMNS)
        for uid, calls in rows.items():
            writer.writerow(
                [
                    uid,
                    f"report-only provenance for {uid}",
                    *(calls[name] for name in LABELS),
                ]
            )
    return path


def _run(
    args: list[str], *, expect_ok: bool = True
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(LANE / "src")
    result = subprocess.run(
        [str(LANE / ".venv/bin/python"), str(RUNNER), *args],
        cwd=LANE,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if expect_ok:
        assert result.returncode == 0, result.stderr
    else:
        assert result.returncode != 0
    return result


def _json_result(result: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_h5_teach_infer_capacity_keeps_calls_separate_and_excludes_whole_source_study(
    tmp_path: Path,
) -> None:
    products = tmp_path / "products"
    _write_product(products, "study-A")
    _write_product(products, "study-B")
    questions = _write_questions(tmp_path / "questions.json")
    labels = _write_labels(
        tmp_path / "train.csv",
        {
            "study-A": {name: ("" if name == "Fracture" else "1") for name in LABELS},
            "study-B": {name: "1" for name in LABELS},
        },
    )
    memory = tmp_path / "memory.json"
    taught_dir = tmp_path / "teach-output"
    taught = _json_result(
        _run(
            [
                "--diagnostic-products",
                str(products),
                "--diagnostic-mode",
                "teach",
                "--diagnostic-memory",
                str(memory),
                "--diagnostic-labels",
                str(labels),
                "--diagnostic-output",
                str(taught_dir),
                "--diagnostic-revision",
                "intent-r1",
                "--diagnostic-questions",
                str(questions),
            ]
        )
    )
    assert taught["action"] == "teach"
    assert taught["studies"] == 2
    assert taught["cases"] == 23
    assert (taught_dir / "teaching-source.csv").read_bytes() == labels.read_bytes()
    ledger = json.loads((taught_dir / "teaching-ledger.json").read_text())
    coverage = ledger["coverage"]
    assert coverage["schema"] == "knee.diagnostic-coverage/v1"
    assert coverage["memory_revision"] == "intent-r1"
    assert len(coverage["objects"]) == 44
    assert len(coverage["question_subjects"]) == 12
    assert all(not row["direct_question_calls"] for row in coverage["objects"])
    assert (
        sum(len(row["positive_case_ids"]) for row in coverage["question_subjects"])
        == 23
    )
    assert taught["coverage"] == str((taught_dir / "teaching-ledger.json").resolve())

    inferred_dir = tmp_path / "infer-output"
    inferred = _json_result(
        _run(
            [
                "--diagnostic-products",
                str(products),
                "--diagnostic-mode",
                "infer",
                "--diagnostic-memory",
                str(memory),
                "--diagnostic-output",
                str(inferred_dir),
                "--diagnostic-questions",
                str(questions),
            ]
        )
    )
    assert inferred["action"] == "infer"
    assert inferred["studies"] == 2
    infer_a = json.loads((inferred_dir / "studies/study-A.json").read_text())
    assert set(infer_a["questions"]) == set(LABELS)
    assert infer_a["questions"]["ACL"]["outcome"] == "proposal"
    assert infer_a["questions"]["ACL"]["case_terms"]
    assert "Report" not in json.dumps(infer_a)
    assert "report-only provenance" not in json.dumps(infer_a)

    capacity_dir = tmp_path / "capacity-output"
    capacity = _json_result(
        _run(
            [
                "--diagnostic-products",
                str(products / "study-A.h5"),
                "--diagnostic-mode",
                "capacity",
                "--diagnostic-memory",
                str(memory),
                "--diagnostic-labels",
                str(labels),
                "--diagnostic-output",
                str(capacity_dir),
                "--diagnostic-questions",
                str(questions),
            ]
        )
    )
    assert capacity["action"] == "capacity"
    assert capacity["same_study_excluded"] is True
    row = json.loads((capacity_dir / "studies/study-A.json").read_text())
    for question in LABELS:
        evidence = row["questions"][question]
        if question == "Fracture":
            assert evidence["excluded_case_ids"] == []
        else:
            assert evidence["excluded_case_ids"]
        assert all(
            case_id not in evidence["speaking_case_ids"]
            for case_id in evidence["excluded_case_ids"]
        )
        assert {term["study_uid"] for term in evidence["case_terms"]} == {"study-B"}
        assert evidence["evaluation"]["same_study_excluded"] is True
    assert row["questions"]["Fracture"]["evaluation"]["expected"] is None
    assert row["questions"]["Fracture"]["evaluation"]["assessment"] == "unlabeled"


def test_real_command_cohort_selects_manifest_identity_instead_of_filename(
    tmp_path: Path,
) -> None:
    from knee.diagnosis.store import read_store

    products = tmp_path / "products"
    _write_product(products, "study-A").rename(products / "opaque-2.h5")
    _write_product(products, "study-B").rename(products / "opaque-1.h5")
    questions = _write_questions(tmp_path / "questions.json")
    labels = _write_labels(
        tmp_path / "train.csv",
        {
            "study-A": {name: "0" for name in LABELS},
            "study-B": {name: "1" for name in LABELS},
        },
    )
    cohort = tmp_path / "cohort.json"
    cohort.write_text(
        json.dumps(
            {
                "schema": "knee.diagnostic-cohort/v1",
                "partitions": {"first": ["study-B"], "other": ["study-A"]},
                "disjoint_partitions": [["first", "other"]],
            }
        )
    )
    memory = tmp_path / "memory.json"
    output = tmp_path / "teach-output"
    result = _json_result(
        _run(
            [
                "--diagnostic-products",
                str(products),
                "--diagnostic-mode",
                "teach",
                "--diagnostic-memory",
                str(memory),
                "--diagnostic-labels",
                str(labels),
                "--diagnostic-output",
                str(output),
                "--diagnostic-revision",
                "cohort-intent-r1",
                "--diagnostic-questions",
                str(questions),
                "--diagnostic-cohort",
                str(cohort),
                "--diagnostic-partition",
                "first",
            ]
        )
    )
    assert result["studies"] == 1
    assert result["cases"] == 12
    assert result["cohort"]["selected_uids"] == ["study-B"]
    snapshot = read_store(memory)
    assert {case.study_uid for case in snapshot.cases} == {"study-B"}
    assert all(call.digit == 1 for case in snapshot.cases for call in case.calls)
    assert not (output / "sources/study-A").exists()
    ledger = json.loads((output / "teaching-ledger.json").read_text())
    assert [row["study_uid"] for row in ledger["studies"]] == ["study-B"]
    assert all(
        row["study_uids"] == ["study-B"]
        for row in ledger["coverage"]["question_subjects"]
    )


def test_silent_labeled_product_does_not_create_a_negative_case(tmp_path: Path) -> None:
    products = tmp_path / "products"
    _write_product(products, "silent-study", silent=True)
    questions = _write_questions(tmp_path / "questions.json")
    labels = _write_labels(
        tmp_path / "train.csv",
        {
            "silent-study": {name: "0" for name in LABELS},
        },
    )
    output = tmp_path / "teach-output"
    memory = tmp_path / "memory.json"
    receipt = _json_result(
        _run(
            [
                "--diagnostic-products",
                str(products),
                "--diagnostic-mode",
                "teach",
                "--diagnostic-memory",
                str(memory),
                "--diagnostic-labels",
                str(labels),
                "--diagnostic-output",
                str(output),
                "--diagnostic-revision",
                "silent-r1",
                "--diagnostic-questions",
                str(questions),
            ]
        )
    )
    assert receipt["cases"] == 0
    ledger = json.loads((output / "teaching-ledger.json").read_text())
    entries = ledger["studies"][0]["teaching"]["ledger"]
    assert len(entries) == len(LABELS)
    assert all(
        row["reason"] == "silent_profile" and row["digit"] == 0 for row in entries
    )


def test_pipeline_rejects_unhashable_trust_identity_and_preexisting_output(
    tmp_path: Path,
) -> None:
    products = tmp_path / "products"
    _write_product(products, "study-A")
    questions = _write_questions(tmp_path / "questions.json")
    labels = _write_labels(
        tmp_path / "train.csv", {"study-A": {name: "1" for name in LABELS}}
    )
    memory = tmp_path / "memory.json"
    _run(
        [
            "--diagnostic-products",
            str(products),
            "--diagnostic-mode",
            "teach",
            "--diagnostic-memory",
            str(memory),
            "--diagnostic-labels",
            str(labels),
            "--diagnostic-output",
            str(tmp_path / "teach-output"),
            "--diagnostic-revision",
            "trust-r1",
            "--diagnostic-questions",
            str(questions),
        ]
    )
    trust = tmp_path / "trust.json"
    trust.write_text(
        json.dumps(
            {
                "schema": "knee.diagnostic-trust/v1",
                "levels": [
                    {
                        "case_id": ["unhashable"],
                        "question": "ACL",
                        "numerator": 0,
                        "denominator": 1,
                        "source": "malformed-test",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    failed = _run(
        [
            "--diagnostic-products",
            str(products),
            "--diagnostic-mode",
            "infer",
            "--diagnostic-memory",
            str(memory),
            "--diagnostic-output",
            str(tmp_path / "bad-trust-output"),
            "--diagnostic-questions",
            str(questions),
            "--diagnostic-trust",
            str(trust),
        ],
        expect_ok=False,
    )
    assert "diagnostic_trust_record_invalid" in failed.stderr

    existing = tmp_path / "already-there"
    existing.mkdir()
    marker = existing / "keep.txt"
    marker.write_text("preserved", encoding="utf-8")
    failed = _run(
        [
            "--diagnostic-products",
            str(products),
            "--diagnostic-mode",
            "infer",
            "--diagnostic-memory",
            str(memory),
            "--diagnostic-output",
            str(existing),
            "--diagnostic-questions",
            str(questions),
        ],
        expect_ok=False,
    )
    assert "FileExistsError" in failed.stderr
    assert marker.read_text(encoding="utf-8") == "preserved"


def test_empty_product_source_is_named_and_does_not_teach(tmp_path: Path) -> None:
    products = tmp_path / "empty-products"
    products.mkdir()
    questions = _write_questions(tmp_path / "questions.json")
    labels = _write_labels(tmp_path / "train.csv", {})
    failed = _run(
        [
            "--diagnostic-products",
            str(products),
            "--diagnostic-mode",
            "teach",
            "--diagnostic-memory",
            str(tmp_path / "memory.json"),
            "--diagnostic-labels",
            str(labels),
            "--diagnostic-output",
            str(tmp_path / "output"),
            "--diagnostic-revision",
            "empty-r1",
            "--diagnostic-questions",
            str(questions),
        ],
        expect_ok=False,
    )
    assert "diagnostic_products_empty" in failed.stderr


def test_actual_dicom_recipe_runs_through_cli_and_missing_reference_stays_unknown(
    tmp_path: Path,
) -> None:
    np = pytest.importorskip("numpy")
    pydicom = pytest.importorskip("pydicom")
    from pydicom.dataset import FileDataset, FileMetaDataset
    from pydicom.uid import (
        ExplicitVRLittleEndian,
        SecondaryCaptureImageStorage,
        generate_uid,
    )

    study_uid = "1.2.826.0.1.3680043.10.543.1"
    series_uid = "1.2.826.0.1.3680043.10.543.2"
    frame = tmp_path / "frame.dcm"
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    meta.ImplementationClassUID = generate_uid()
    pixels = np.array([[10, 11, 12], [13, 14, 15]], dtype=np.int16)
    dataset = FileDataset(str(frame), {}, file_meta=meta, preamble=b"\0" * 128)
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
    dataset.PixelRepresentation = 1
    dataset.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
    dataset.ImagePositionPatient = [10, 20, 30]
    dataset.PixelSpacing = [0.5, 0.75]
    dataset.PixelData = np.asarray(pixels, dtype="<i2").tobytes()
    dataset.save_as(frame, enforce_file_format=True)

    spec = {
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
                "references": [],
            }
        ],
    }
    recipe = {
        "schema": "knee.diagnostic-inputs/v1",
        "mode": "cheap/raw-plane-v1",
        "producer": "explicit integration fixture",
        "dependencies": ["DICOM stored pixels", "caller support coordinates"],
        "encoding_spec": spec,
        "studies": [
            {
                "study_uid": study_uid,
                "observations": [
                    {
                        "object": "femur",
                        "region": "caller-region",
                        "frame": {
                            "path": str(frame),
                            "series_uid": series_uid,
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
    recipe_path = tmp_path / "recipe.json"
    recipe_path.write_text(json.dumps(recipe), encoding="utf-8")
    questions = _write_questions(
        tmp_path / "questions.json", role="femur", bank="raw_signal"
    )
    memory = tmp_path / "empty-memory.json"
    write_store(memory, Snapshot("empty-memory"))
    output = tmp_path / "acquired-output"
    result = _json_result(
        _run(
            [
                "--diagnostic-inputs",
                str(recipe_path),
                "--diagnostic-mode",
                "infer",
                "--diagnostic-memory",
                str(memory),
                "--diagnostic-output",
                str(output),
                "--diagnostic-questions",
                str(questions),
            ]
        )
    )
    assert result["source_mode"] == "declared_cheap_acquired_route"
    record = json.loads((output / "studies" / f"{study_uid}.json").read_text())
    assert set(record["questions"]) == set(LABELS)
    assert {row["outcome"] for row in record["questions"].values()} == {
        "unresolved_no_precedent"
    }
    source = record["source"]
    assert Path(source["manifest"]).is_file()
    assert Path(source["manifest"]).with_name("arrays.npz").is_file()
    assert pydicom.dcmread(frame).StudyInstanceUID == study_uid
