from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path

import pytest

from knee.diagnosis.cheap import pair_descriptions
from knee.diagnosis.evidence import load_source
from knee.diagnosis.models import Profile
from knee.diagnosis.pairing import (
    DiagnosticPairingError,
    pair_with_products,
    prepare_products,
)
from knee.diagnosis.product_cases import profiles_from_product
from knee.encoding import h5_store
from knee.encoding.counts import BankLayout, CountBundle, CountLayout
from knee.encoding.places import (
    BankSpec,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    compile_layout,
)
from knee.study.tables import LABELS, TRAIN_COLUMNS


def _full_manifest(uid: str, subject: str = "joint_fluid") -> dict:
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
    return {
        "study_uid": uid,
        "encoded_arrays": {},
        "object_composition": {
            "schema": "knee_object_profiles/v1",
            "carrier_identity": compiled.carrier_id,
            "layout_fingerprint": compiled.fingerprint,
            "registry_fingerprint": "fixture-registry",
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
                subject: {
                    "status": "partial",
                    "preparation_status": "ok",
                    "detail": "",
                    "reference_set_identity": reference,
                    "count_layout_id": count_id,
                    "sparse_counts": [["signal", 4, 2], ["signal", 9, 1]],
                    "assembly": {
                        "code": "partial",
                        "batches": [{"bank": "signal", "status": "partial"}],
                    },
                }
            },
            "additions": [],
        },
    }


def _write_full(path: Path, uid: str, subject: str = "joint_fluid") -> Path:
    pytest.importorskip("h5py")
    path.parent.mkdir(parents=True, exist_ok=True)
    h5_store.write_h5(path, _full_manifest(uid, subject), {})
    return path


def _cheap_profile(
    subject: str = "joint_fluid",
    *,
    study_uid: str = "study-001",
    producer: str = "declared-cheap-producer-v1",
    mode: str = "cheap/raw-plane-v1",
    scope: str = "region:joint-fluid-search",
    banks: tuple[BankLayout, ...] | None = None,
    counts: tuple[tuple[int, ...], ...] | None = None,
) -> Profile:
    if banks is None:
        banks = (BankLayout("signal", 512), BankLayout("cheap_context", 512))
    layout = CountLayout("cheap-layout-v1", "cheap-carrier-v1", banks)
    if counts is None:
        zero = (0,) * 512
        signal = list(zero)
        signal[9] = 7
        counts = (tuple(signal), zero)
    return Profile(
        subject,
        CountBundle(layout, counts),
        mode,
        scope,
        f"cheap:{study_uid}:{subject}",
        (("view", "Sagittal"),),
        tuple(
            (bank.name, "measured" if any(row) else "silent")
            for bank, row in zip(banks, counts, strict=True)
        ),
        (
            ("study_uid", study_uid),
            ("producer", producer),
            ("source_address", "fixture:series/slice/region"),
        ),
    )


def test_h5_product_pairs_typed_cheap_profile_by_subject_and_uid_without_cosine(
    tmp_path, monkeypatch
):
    product_dir = tmp_path / "full-products"
    product = _write_full(product_dir / "study-001.h5", "study-001")
    cheap = _cheap_profile()

    def forbidden(*args, **kwargs):
        raise AssertionError("pairing must not calculate cosine")

    import knee.encoding.counts as counts_module

    monkeypatch.setattr(counts_module, "cosine_terms", forbidden)
    result = pair_with_products((cheap,), "study-001", product_dir)

    assert result["schema"] == "knee.diagnostic-pairs/v1"
    assert result["study_uid"] == "study-001"
    assert result["producer"] == "declared-cheap-producer-v1"
    assert result["full_product"] == {
        "path": str(product.resolve()),
        "study_uid": "study-001",
        "storage": "h5",
    }
    assert result["comparison_performed"] is False
    assert result["diagnostic_call"] is None
    assert len(result["objects"]) == 1
    pair = result["objects"][0]
    assert pair["subject"] == "joint_fluid" and pair["status"] == "paired"
    assert pair["pair"]["full"]["mode"] == "full"
    assert pair["pair"]["cheap"]["mode"] == "cheap/raw-plane-v1"
    assert pair["pair"]["full"]["scope"].startswith("object:joint_fluid;")
    assert pair["pair"]["cheap"]["scope"] == "region:joint-fluid-search"
    assert pair["pair"]["comparison_performed"] is False
    signal = next(row for row in pair["pair"]["banks"] if row["bank"] == "signal")
    assert signal["full_counts"]["nonzero_rows"] == [[4, "2"], [9, "1"]]
    assert signal["cheap_counts"]["nonzero_rows"] == [[9, "7"]]
    assert pair["pair"]["bank_name_sets"] == {
        "common": ["signal"],
        "full_only": [],
        "cheap_only": ["cheap_context"],
        "common_speaking": ["signal"],
        "differing_availability": [],
    }


def test_missing_full_object_is_named_and_keeps_cheap_identity(tmp_path):
    product = _write_full(tmp_path / "study-001.h5", "study-001")
    result = pair_with_products((_cheap_profile("tibia"),), "study-001", product)
    object_record = result["objects"][0]
    assert object_record["status"] == "missing_full_object"
    assert object_record["full"] is None and object_record["pair"] is None
    assert object_record["cheap"]["scope"] == "region:joint-fluid-search"
    assert result["full_product"]["path"] == str(product.resolve())


def test_dense_pair_descriptions_remains_backward_compatible_and_matches_sparse_rows(
    tmp_path,
):
    product = _write_full(tmp_path / "study-001.h5", "study-001")
    full = profiles_from_product(product, mode="full")[0]
    cheap = _cheap_profile()
    dense = pair_descriptions(full, cheap)
    sparse = pair_descriptions(full, cheap, counts_mode="sparse")

    assert "layout_banks" not in dense["full"]
    assert isinstance(
        next(row for row in dense["banks"] if row["bank"] == "signal")["full_counts"],
        list,
    )
    assert "layout_banks" in sparse["full"]
    for bank in dense["banks"]:
        compact = next(row for row in sparse["banks"] if row["bank"] == bank["bank"])
        for side in ("full_counts", "cheap_counts"):
            if bank[side] is None:
                assert compact[side] is None
                continue
            expanded = [0] * compact[side]["row_count"]
            for index, value in compact[side]["nonzero_rows"]:
                expanded[index] = int(value)
            assert expanded == bank[side]


def test_pairing_rejects_source_uid_mismatch_missing_product_and_mixed_producers(
    tmp_path,
):
    wrong_uid = _write_full(tmp_path / "wrong.h5", "different-study")
    with pytest.raises(DiagnosticPairingError, match="pair_full_study_uid_mismatch"):
        pair_with_products((_cheap_profile(),), "study-001", wrong_uid)
    with pytest.raises(DiagnosticPairingError, match="pair_full_product_missing"):
        pair_with_products((_cheap_profile(),), "study-001", tmp_path / "absent")
    product = _write_full(tmp_path / "right.h5", "study-001")
    mixed = _cheap_profile("tibia", producer="another-producer")
    with pytest.raises(
        DiagnosticPairingError, match="pair_cheap_producer_missing_or_mixed"
    ):
        pair_with_products((_cheap_profile(), mixed), "study-001", product)


def test_pairing_rejects_cheap_uid_and_mode_incompatibility(tmp_path):
    product = _write_full(tmp_path / "study-001.h5", "study-001")
    wrong_uid = _cheap_profile(study_uid="other-study")
    with pytest.raises(DiagnosticPairingError, match="pair_cheap_study_uid_mismatch"):
        pair_with_products((wrong_uid,), "study-001", product)
    wrong_mode = _cheap_profile(mode="full")
    with pytest.raises(DiagnosticPairingError, match="pair_cheap_mode_invalid"):
        pair_with_products((wrong_mode,), "study-001", product)


def test_prepared_product_index_reads_each_header_once_for_repeated_queries(
    tmp_path, monkeypatch
):
    first = _write_full(tmp_path / "first.h5", "study-001")
    second = _write_full(tmp_path / "second.h5", "study-002")
    import knee.diagnosis.pairing as pairing_module

    header_reads = []
    original_uid = pairing_module._product_uid

    def counted_uid(path):
        header_reads.append(path)
        return original_uid(path)

    profile_reads = []
    original_profiles = pairing_module.profiles_from_product

    def counted_profiles(path, mode="full"):
        profile_reads.append((path, mode))
        return original_profiles(path, mode)

    monkeypatch.setattr(pairing_module, "_product_uid", counted_uid)
    monkeypatch.setattr(pairing_module, "profiles_from_product", counted_profiles)
    prepared = prepare_products(tmp_path)
    assert len(header_reads) == 2
    with pytest.raises(TypeError):
        prepared.paths_by_uid["study-003"] = ()

    pair_with_products((_cheap_profile(study_uid="study-001"),), "study-001", prepared)
    pair_with_products((_cheap_profile(study_uid="study-002"),), "study-002", prepared)
    assert len(header_reads) == 2
    assert profile_reads == [(first.resolve(), "full"), (second.resolve(), "full")]


def test_prepared_product_index_refuses_duplicate_declared_uid_at_query(tmp_path):
    _write_full(tmp_path / "first.h5", "study-001")
    _write_full(tmp_path / "second.h5", "study-001")
    prepared = prepare_products(tmp_path)
    with pytest.raises(DiagnosticPairingError, match="pair_full_study_uid_ambiguous"):
        pair_with_products((_cheap_profile(),), "study-001", prepared)


def test_sparse_summary_scans_shared_builtin_rows_once_and_checks_each_bank_cardinality(
    tmp_path, monkeypatch
):
    product = _write_full(tmp_path / "study-001.h5", "study-001")
    full = profiles_from_product(product, mode="full")[0]
    zero = (0,) * 512
    banks = tuple(BankLayout(f"silent/{index}", 512) for index in range(3))
    cheap = _cheap_profile("joint_fluid", banks=banks, counts=(zero, zero, zero))
    import knee.diagnosis.cheap as cheap_module

    calls = []
    original_summary = cheap_module._summarize_sparse_row

    def counted_summary(row, cardinality):
        calls.append((id(row), cardinality))
        return original_summary(row, cardinality)

    monkeypatch.setattr(cheap_module, "_summarize_sparse_row", counted_summary)
    pair_descriptions(full, cheap, counts_mode="sparse")
    assert calls == [
        (id(full.bundle.counts[0]), full.bundle.layout.banks[0].row_count),
        (id(zero), 512),
    ]

    malformed = _cheap_profile(
        "joint_fluid", banks=(BankLayout("short", 511),), counts=((0,) * 512,)
    )
    with pytest.raises(ValueError, match="pair_count_row_cardinality_mismatch"):
        pair_descriptions(full, malformed, counts_mode="sparse")
    shared_wrong_cardinality = _cheap_profile(
        "joint_fluid",
        banks=(BankLayout("first", 512), BankLayout("second", 511)),
        counts=(zero, zero),
    )
    with pytest.raises(ValueError, match="pair_count_row_cardinality_mismatch"):
        pair_descriptions(full, shared_wrong_cardinality, counts_mode="sparse")


def test_sparse_pair_output_keeps_full_layout_and_exact_large_counts(tmp_path):
    product = _write_full(tmp_path / "study-001.h5", "study-001")
    bank_count = 3696
    zero = (0,) * 512
    rows = [zero] * bank_count
    rows[0] = (10**100,) + (0,) * 511
    banks = tuple(BankLayout(f"bank/{index:04d}", 512) for index in range(bank_count))
    large = _cheap_profile("joint_fluid", banks=banks, counts=tuple(rows))
    # The product has only `signal`; this profile's complete sparse layout still
    # appears in its identity and per-bank records, including silent banks.
    result = pair_with_products((large,), "study-001", product)
    pair = result["objects"][0]["pair"]
    cheap_identity = pair["cheap"]
    assert len(cheap_identity["layout_banks"]) == bank_count
    assert len(pair["banks"]) == bank_count + 1
    first = next(item for item in pair["banks"] if item["bank"] == "bank/0000")
    assert first["cheap_counts"] == {
        "row_count": 512,
        "nonzero_rows": [[0, str(10**100)]],
    }
    silent = next(item for item in pair["banks"] if item["bank"] == "bank/0001")
    assert silent["cheap_counts"] == {"row_count": 512, "nonzero_rows": []}
    assert all(
        item["cheap_counts"] is not None
        for item in pair["banks"]
        if item["bank"].startswith("bank/")
    )
    assert "counts" not in silent["cheap_counts"]


def test_real_teaching_cli_publishes_pairing_inside_verified_source_evidence(tmp_path):
    np = pytest.importorskip("numpy")
    pydicom = pytest.importorskip("pydicom")
    from pydicom.dataset import FileDataset, FileMetaDataset
    from pydicom.uid import (
        ExplicitVRLittleEndian,
        SecondaryCaptureImageStorage,
        generate_uid,
    )

    from knee.diagnosis.store import read_store

    study_uid = "1.2.826.0.1.3680043.10.543.101"
    series_uid = "1.2.826.0.1.3680043.10.543.102"
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

    reference = {
        "bank": "raw_signal",
        "metric": "signal",
        "reference_id": "fixture-reference-v1",
        "source": "test fixture only",
        "units": "stored-value-unit",
        "low": 12,
        "high": 14,
    }
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
                "references": [reference],
            }
        ],
    }
    recipe = {
        "schema": "knee.diagnostic-inputs/v1",
        "mode": "cheap/raw-plane-v1",
        "producer": "integration raw-plane producer",
        "dependencies": ["DICOM stored pixels", "explicit support coordinates"],
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
    questions = tmp_path / "questions.json"
    questions.write_text(
        json.dumps(
            {
                "schema": "knee.diagnostic-questions/v1",
                "questions": [
                    {
                        "question_id": question,
                        "objects": ["femur"],
                        "banks": ["object/femur/raw_signal"],
                        "bank_prefixes": [],
                        "context_keys": [],
                    }
                    for question in LABELS
                ],
            }
        ),
        encoding="utf-8",
    )
    labels = tmp_path / "train.csv"
    with labels.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(TRAIN_COLUMNS)
        writer.writerow(
            [
                study_uid,
                "report text is teaching provenance only",
                *(["1"] * len(LABELS)),
            ]
        )
    full_product = _write_full(tmp_path / "full-study.h5", study_uid, "femur")
    memory = tmp_path / "memory.json"
    output = tmp_path / "teaching-output"
    runner = Path(__file__).resolve().parents[1] / "scripts/run_interiors.py"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    completed = subprocess.run(
        [
            str(Path(__file__).resolve().parents[1] / ".venv/bin/python"),
            str(runner),
            "--diagnostic-inputs",
            str(recipe_path),
            "--diagnostic-pair-products",
            str(full_product),
            "--diagnostic-mode",
            "teach",
            "--diagnostic-memory",
            str(memory),
            "--diagnostic-labels",
            str(labels),
            "--diagnostic-output",
            str(output),
            "--diagnostic-revision",
            "pairing-cli-r1",
            "--diagnostic-questions",
            str(questions),
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    receipt = json.loads(completed.stdout.strip().splitlines()[-1])
    assert receipt["action"] == "teach" and receipt["studies"] == 1
    ledger = json.loads((output / "teaching-ledger.json").read_text())
    source_receipt = ledger["studies"][0]["source"]
    retained = load_source(Path(source_receipt["manifest"]))["source"]
    paired = retained["full_cheap_pairs"]
    assert paired["schema"] == "knee.diagnostic-pairs/v1"
    assert paired["study_uid"] == study_uid
    assert paired["producer"] == "integration raw-plane producer"
    assert paired["comparison_performed"] is False
    assert paired["diagnostic_call"] is None
    assert paired["objects"][0]["status"] == "paired"
    assert paired["objects"][0]["pair"]["full"]["scope"].startswith("object:femur;")
    assert paired["objects"][0]["pair"]["cheap"]["scope"].startswith("region:")
    snapshot = read_store(memory)
    assert snapshot.cases
    assert pydicom.dcmread(frame).StudyInstanceUID == study_uid
