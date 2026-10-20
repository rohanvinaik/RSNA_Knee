from __future__ import annotations

import copy

import numpy as np
from test_encoding_operation import _spec, _study

from knee.array_archive import write_npz_xz
from knee.encoding import operation
from knee.encoding.mri_spec import make_mri_spec
from knee.encoding.product import open_product
from knee.json_store import load_json
from knee.receipt import digest


def test_encode_study_same_acquisition_records_target_artifact(tmp_path):
    run_dir, main_run, result, _ = _study(tmp_path)
    links = operation.encode_study(
        result,
        run_dir,
        main_run,
        _spec(view=["coronal", "fluid", "fat-suppressed"]),
        tmp_path / "ordinary.json.xz",
    )
    outcome = load_json(links["manifest"])["profiles"][0]["outcomes"][0]
    assert outcome["target_series_uid"] == "series-a"
    assert outcome["target_artifact"] == "study-1/series-a.npz.xz"
    assert outcome["target_artifact_status"] == "retained_target_record_artifact"
    assert outcome["record_artifact"] == "study-1/series-a.npz.xz"
    assert outcome["record_series_uid"] == "series-a"
    assert outcome["target_artifact_root"] == "run"
    group = load_json(links["manifest"])["support_ownership"]["femur"][
        "addressed_supports"
    ][0]
    assert group["source_address"]["record_artifact"] == "study-1/series-a.npz.xz"
    assert (
        group["source_address"]["target_artifact_status"]
        == "retained_target_record_artifact"
    )


def test_encode_study_target_only_uses_same_named_provenance_contract(tmp_path):
    run_dir, main_run, result, record = _study(tmp_path)
    observation = dict(record["observations"][0])
    observation.update(
        provenance="projected",
        kind="target",
        code="pointed",
        count=None,
        off_plane_mm=None,
    )
    record["observations"] = [observation]
    links = operation.encode_study(
        result,
        run_dir,
        main_run,
        _spec(provenance="projected", kind="target"),
        tmp_path / "target-only.json.xz",
    )
    outcome = load_json(links["manifest"])["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "target_only"
    assert outcome["target_series_uid"] == "series-a"
    assert outcome["target_artifact"] == "study-1/series-a.npz.xz"
    assert outcome["target_artifact_status"] == "retained_target_record_artifact"
    assert "points_rc" not in outcome


def test_missing_observation_target_does_not_borrow_the_holder_identity(tmp_path):
    run_dir, main_run, result, record = _study(tmp_path)
    record["observations"][0].pop("series_uid")
    links = operation.encode_study(
        result,
        run_dir,
        main_run,
        _spec(),
        tmp_path / "unknown-target.json.xz",
    )
    outcome = load_json(links["manifest"])["profiles"][0]["outcomes"][0]
    assert outcome["owner_series_uid"] == "series-a"
    assert outcome["target_series_uid"] is None
    assert outcome["target_artifact"] is None
    assert outcome["target_artifact_status"] == "target_identity_unavailable"
    assert "points_rc" not in outcome


def _carried_fibula_study(tmp_path):
    owner_uid = "holder-sagittal-series"
    target_uid = "separate-axial-series"
    study_uid = "study-carried-fibula"
    prefix = "fibula_target"
    artifact = f"{study_uid}/{owner_uid}-fibula.npz.xz"
    arrays = {
        f"{prefix}_offsets": np.array([0, 4], dtype=np.int64),
        f"{prefix}_shapes": np.array([[2, 2]], dtype=np.int32),
        f"{prefix}_slices": np.array([0], dtype=np.int32),
        f"{prefix}_windows_rc": np.array([[0, 8, 0, 8]], dtype=np.int32),
        f"{prefix}_block_px": np.array([[4, 4]], dtype=np.int32),
        f"{prefix}_block_mm": np.array([[2.0, 2.0]], dtype=np.float64),
        f"{prefix}_median": np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32),
        f"{prefix}_depth": np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32),
        f"{prefix}_fibula_body": np.array([True, False, True, False], dtype=bool),
        f"{prefix}_fibula_seeds": np.array([True, False, False, False], dtype=bool),
    }
    run_dir, main_run = tmp_path / "interiors", tmp_path / "main"
    artifact_path = run_dir / artifact
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    write_npz_xz(artifact_path, arrays)
    profile = next(
        copy.deepcopy(item)
        for item in make_mri_spec(include_coarse=True)["profiles"]
        if item.get("object") == "fibula"
        and item.get("support") == "{arrays_prefix}_fibula_body"
    )
    # Keep every declared metric binding, but make each reading intentionally unread.
    factory = make_mri_spec(include_coarse=True)
    metrics_by_bank = {
        bank["name"]: [metric["name"] for metric in bank["metrics"]]
        for bank in factory["banks"]
    }
    profile["readings"] = [
        {
            "bank": bank,
            "metric": metric,
            "source": "unread",
            "reason": "fixture measures only the retained coarse support address",
        }
        for bank, metrics in metrics_by_bank.items()
        for metric in metrics
    ]
    profile["references"] = []
    observation = {
        "object": "fibula",
        "provenance": "native",
        "kind": "reading",
        "series_uid": target_uid,
        "view": ["Axial", "1", "1"],
        "slices": [0],
        "code": "section",
        "count": 2,
        "off_plane_mm": 0.0,
        "support": f"{prefix}_fibula_body",
        "artifact": artifact,
        "row": 0,
        "label": None,
    }
    record = {
        "study_uid": study_uid,
        "series_uid": owner_uid,
        "view": ["Sagittal", "0", "0"],
        "slice_index": 30,
        "artifact": artifact,
        "arrays": {name: {"digest": digest(value)} for name, value in arrays.items()},
        "fibula_key_planes": {
            target_uid: {
                "orientation": "axial",
                "arrays_prefix": prefix,
                "slices_read": [0],
            }
        },
        "observations": [observation],
    }
    result = {
        "study_uid": study_uid,
        "records": [record],
        "main_records": [],
        "objects": {"fibula": {}},
    }
    spec = factory
    spec["profiles"] = [profile]
    return run_dir, main_run, result, spec, owner_uid, target_uid, artifact


def test_encode_study_carried_fibula_keeps_holder_and_target_distinct(tmp_path):
    run_dir, main_run, result, spec, owner_uid, target_uid, artifact = (
        _carried_fibula_study(tmp_path)
    )
    links = operation.encode_study(
        result, run_dir, main_run, spec, tmp_path / "carried.json.xz"
    )
    with open_product(links["archive"]) as product:
        outcome = product.manifest["profiles"][0]["outcomes"][0]
    assert outcome["owner_series_uid"] == owner_uid
    assert outcome["target_series_uid"] == target_uid
    assert outcome["artifact"] == artifact
    assert outcome["record_artifact"] == artifact
    assert outcome["target_artifact"] is None
    assert outcome["target_artifact_status"] == "target_record_artifact_unavailable"
    assert outcome["target_series_uid"] == target_uid
    with open_product(links["archive"]) as product:
        owned = product.manifest["support_ownership"]["fibula"]["addressed_supports"][0]
    assert owned["source_address"]["record_artifact"] == artifact
    assert owned["source_address"]["target_artifact"] is None
    assert owned["source_address"]["record_series_uid"] == owner_uid
    assert owned["source_address"]["target_artifact_root"] is None
    assert (
        owned["source_address"]["target_artifact_status"]
        == "target_record_artifact_unavailable"
    )
    assert outcome["metadata"]["scope_address"]["target_series_uid"] == target_uid
    assert outcome["metadata"]["scope_address"]["slice_index"] == 0
