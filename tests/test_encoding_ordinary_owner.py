from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from knee.array_archive import write_npz_xz
from knee.encoding.operation import encode_study
from knee.receipt import digest


def _case(tmp_path: Path, *, owner_changes: dict | None = None, copies: int = 1):
    run_dir = tmp_path / "interiors"
    run_dir.mkdir()
    study_uid = "study-a"
    target_artifact = "target-series.npz.xz"
    owner_artifact = "source-series-ACL.npz.xz"
    view = ("sagittal", "fluid", "fat-suppressed")
    mask = np.array([[True, False, True], [False, False, False]], dtype=np.bool_)
    arrays = {"a1_objects": mask}
    write_npz_xz(run_dir / owner_artifact, arrays)
    descriptor = {"a1_objects": {"digest": digest(mask)}}
    observation = {
        "object": "acl",
        "provenance": "laid",
        "kind": "resolved",
        "series_uid": "source-series",
        "view": list(view),
        "slices": [7],
        "code": "named",
        "count": 2,
        "support": "a1_objects",
        "artifact": owner_artifact,
        "row": None,
        "label": None,
    }
    target = {
        "study_uid": study_uid,
        "series_uid": "target-series",
        "view": view,
        "slice_index": 6,
        "artifact": target_artifact,
        "arrays": {},
        "observations": [observation],
    }
    owner = {
        "study_uid": study_uid,
        "series_uid": "source-series",
        "view": view,
        "slice_index": 7,
        "artifact": owner_artifact,
        "arrays": descriptor,
        "observations": [],
    }
    if owner_changes:
        owner.update(owner_changes)
    result = {
        "study_uid": study_uid,
        "records": [target],
        "main_records": [owner] * copies,
        "objects": {"acl": {}},
    }
    spec = {
        "version": "ordinary-owner-candidate-v1",
        "banks": [
            {
                "name": "context",
                "facet": "addressed source context",
                "metrics": [
                    {
                        "name": "orientation",
                        "kind": "words",
                        "words": ["sagittal"],
                    }
                ],
            }
        ],
        "profiles": [
            {
                "object": "acl",
                "provenance": "laid",
                "kind": "resolved",
                "support": "a1_objects",
                "view": list(view),
                "readings": [
                    {
                        "bank": "context",
                        "metric": "orientation",
                        "source": "record_context",
                        "path": ["view", 0],
                        "scope": "acquisition",
                    }
                ],
                "references": [],
            }
        ],
    }
    return run_dir, result, spec, target, owner


def _encode(tmp_path: Path, *, owner_changes: dict | None = None, copies: int = 1):
    run_dir, result, spec, target, owner = _case(
        tmp_path, owner_changes=owner_changes, copies=copies
    )
    status = encode_study(result, run_dir, run_dir, spec, tmp_path / "encoded.json")
    return status, target, owner


def test_ordinary_observation_retains_recipient_and_actual_source(tmp_path):
    status, target, owner = _encode(tmp_path)
    outcome = status["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "ok"
    assert outcome["artifact"] == owner["artifact"]
    # The recipient record and observed acquisition are different roles.
    assert outcome["record_series_uid"] == target["series_uid"]
    assert outcome["record_artifact"] == target["artifact"]
    assert outcome["target_artifact"] == owner["artifact"]
    assert outcome["target_series_uid"] == owner["series_uid"]
    assert outcome["target_artifact_root"] == "main"
    assert outcome["target_artifact_status"] == "retained_target_record_artifact"
    assert outcome["owner_series_uid"] == owner["series_uid"]
    assert outcome["record_view"] == target["view"]
    assert outcome["owner_view"] == owner["view"]
    assert outcome["record_slice_index"] == target["slice_index"]
    assert outcome["owner_slice_index"] == owner["slice_index"]
    assert status["work"]["opened_artifacts"] == 1
    assert status["work"]["verified_source_arrays"] == 1
    context = outcome["metadata"]["context_sources"][0]
    assert context["source_address"]["series_uid"] == owner["series_uid"]
    assert context["source_address"]["artifact"] == owner["artifact"]


@pytest.mark.parametrize(
    ("owner_changes", "expected"),
    [
        ({"series_uid": "wrong-series"}, "source_series_mismatch"),
        (
            {"view": ("coronal", "fluid", "fat-suppressed")},
            "context_acquisition_view_mismatch",
        ),
        ({"slice_index": 8}, "plane_address_required"),
    ],
)
def test_ordinary_owner_must_match_observation_source_address(
    tmp_path, owner_changes, expected
):
    status, _target, _owner = _encode(tmp_path, owner_changes=owner_changes)
    outcome = status["profiles"][0]["outcomes"][0]
    assert outcome["status"] == expected
    assert outcome["record_series_uid"] == "target-series"
    assert outcome["record_artifact"] == "target-series.npz.xz"
    assert outcome["target_series_uid"] == "source-series"
    if expected == "source_series_mismatch":
        assert outcome["target_artifact"] is None
        assert outcome["target_artifact_status"] == "target_record_artifact_unavailable"
    else:
        assert outcome["target_artifact"] == "source-series-ACL.npz.xz"
        assert outcome["target_artifact_status"] == "retained_target_record_artifact"


@pytest.mark.parametrize(
    ("owners", "expected"),
    [
        ([], "ordinary_source_owner_record_missing"),
        (["study-a", "study-a"], "ordinary_source_owner_record_ambiguous"),
        (["study-b"], "ordinary_source_owner_record_missing"),
    ],
)
def test_ordinary_owner_lookup_is_same_study_and_unique(tmp_path, owners, expected):
    run_dir, result, spec, _target, owner = _case(tmp_path, copies=0)
    result["main_records"] = [dict(owner, study_uid=uid) for uid in owners]
    status = encode_study(result, run_dir, run_dir, spec, tmp_path / "encoded.json")
    outcome = status["profiles"][0]["outcomes"][0]
    assert outcome["status"] == expected
    assert status["work"]["opened_artifacts"] == 0


def test_same_artifact_ordinary_observation_keeps_inline_owner_path(tmp_path):
    run_dir, result, spec, target, owner = _case(tmp_path)
    observation = dict(target["observations"][0], artifact=target["artifact"])
    observation["series_uid"] = target["series_uid"]
    target["slice_index"] = observation["slices"][0]
    target["observations"] = [observation]
    target["arrays"] = owner["arrays"]
    result["records"] = [dict(target, observations=[observation])]
    result["main_records"] = []
    write_npz_xz(
        run_dir / target["artifact"],
        {"a1_objects": np.array([[True, False, True], [False, False, False]])},
    )
    status = encode_study(result, run_dir, run_dir, spec, tmp_path / "encoded.json")
    outcome = status["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "ok"
    assert outcome["artifact"] == outcome["target_artifact"] == target["artifact"]
    assert status["work"]["opened_artifacts"] == 1


def test_projected_target_does_not_resolve_or_open_source_artifact(tmp_path):
    run_dir, result, spec, target, _owner = _case(tmp_path, copies=0)
    observation = dict(target["observations"][0], provenance="projected", kind="target")
    target["observations"] = [observation]
    spec["profiles"][0].update(provenance="projected", kind="target")
    result["records"] = [target]
    status = encode_study(result, run_dir, run_dir, spec, tmp_path / "encoded.json")
    outcome = status["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "target_only"
    assert status["work"]["opened_artifacts"] == 0
