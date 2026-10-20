from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pytest

from knee.encoding.object_sources import ObjectSourceError, prepare_object_sources
from knee.receipt import digest


def _record(
    root: Path,
    study: str,
    series: str,
    artifact: str,
    arrays: dict[str, np.ndarray],
    observations: list[dict],
    unresolved: list[dict] | None = None,
) -> tuple[dict, Path, str, dict[str, np.ndarray]]:
    path = root / artifact
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    record = {
        "study_uid": study,
        "series_uid": series,
        "view": ["Sagittal", "0", "0"],
        "slice_index": 4,
        "artifact": artifact,
        "arrays": {name: {"digest": digest(value)} for name, value in arrays.items()},
        "observations": observations,
        "observations_unresolved": unresolved or [],
    }
    return record, root, "run", arrays


def _observation(object_name: Any, support: Any, **updates: Any) -> dict:
    row = {
        "object": object_name,
        "provenance": "native",
        "kind": "resolved",
        "series_uid": "series-1",
        "view": ["Sagittal", "0", "0"],
        "slices": [4],
        "code": "identified",
        "count": 2,
        "off_plane_mm": 0.0,
        "support": support,
        "artifact": "study/series-1.npz.xz",
        "row": 0,
        "label": 3,
        "address_frame": {"origin_lps": [1.0, 2.0, 3.0]},
    }
    row.update(updates)
    return row


def _materialize(plan, candidates, mappings, emitted):
    for record, root, _ in candidates:
        path = (root / record["artifact"]).resolve()
        if path in plan.artifacts:
            plan.retain_artifact(path, mappings[record["artifact"]], {}, emitted)
    return plan.finish()


def test_preserves_all_objects_and_exact_observation_support_with_final_reference(
    tmp_path,
):
    support = np.array([[False, True], [True, False]], dtype=np.bool_)
    observation = _observation("femur", "a1_objects")
    record, root, root_name, arrays = _record(
        tmp_path,
        "study-1",
        "series-1",
        "study/series-1.npz.xz",
        {"a1_objects": support},
        [observation, observation],
    )
    objects: dict[str, dict[str, Any]] = {
        f"object-{index}": {"unresolved": {"pipeline": {"no_observation_record": 1}}}
        for index in range(43)
    }
    objects["femur"] = {"outcomes": {"identified": 2}, "native_series": ["series-1"]}
    result = {"study_uid": "study-1", "objects": objects}
    candidates = [(record, root, root_name)]
    plan = prepare_object_sources(result, candidates, tmp_path / "final.h5")
    emitted: dict[str, np.ndarray] = {}
    metadata = _materialize(plan, candidates, {record["artifact"]: arrays}, emitted)

    assert len(metadata["objects"]) == 44
    femur = metadata["objects"]["femur"]
    assert femur["summary"] == objects["femur"]
    assert femur["status"] == "source_arrays_retained"
    assert len(femur["observations"]) == 2
    first, second = femur["observations"]
    assert first["observation"] == observation
    assert first["source_address"]["owner_series_uid"] == "series-1"
    assert first["source_address"]["label"] == 3
    assert first["support"]["active"]["archive"] == str(
        (tmp_path / "final.h5").resolve()
    )
    assert first["support"]["source"]["artifact"] == record["artifact"]
    assert first["support"]["active"]["dtype"] == np.dtype(np.bool_).str
    assert first["support"]["active"]["shape"] == [2, 2]
    assert first["support"]["active"]["name"] == second["support"]["active"]["name"]
    assert np.array_equal(emitted[first["support"]["active"]["name"]], support)


def test_target_only_and_unresolved_objects_remain_named_without_array_reads(tmp_path):
    target = _observation(
        "joint_fluid",
        "",
        provenance="projected",
        kind="target",
        artifact=None,
        code="on_the_slice",
        count=0,
    )
    unresolved = {
        "object": "acl",
        "provenance": "native",
        "code": "abstain_no_region",
        "note": "retained",
    }
    record, root, root_name, _arrays = _record(
        tmp_path,
        "study-1",
        "series-1",
        "study/series-1.npz.xz",
        {},
        [target],
        [unresolved],
    )
    result = {"study_uid": "study-1", "objects": {"joint_fluid": {}, "acl": {}}}
    candidates = [(record, root, root_name)]
    plan = prepare_object_sources(result, candidates, tmp_path / "final.h5")
    assert plan.artifacts == ()
    metadata = plan.finish()
    assert metadata["objects"]["joint_fluid"]["status"] == "target_only"
    assert metadata["objects"]["joint_fluid"]["observations"][0]["support"] is None
    assert metadata["objects"]["acl"]["status"] == "unresolved_only"
    assert metadata["objects"]["acl"]["unresolved"] == [unresolved]


def test_observation_carrier_and_exact_array_owner_remain_distinct(tmp_path):
    support = np.array([[True, False]], dtype=np.bool_)
    observation = _observation(
        "acl",
        "a1_objects",
        artifact="study/source.npz.xz",
        series_uid="source-series",
    )
    carrier, root, root_name, _ = _record(
        tmp_path,
        "study-1",
        "target-series",
        "study/target.npz.xz",
        {},
        [observation],
    )
    owner, owner_root, owner_name, owner_arrays = _record(
        tmp_path,
        "study-1",
        "source-series",
        "study/source.npz.xz",
        {"a1_objects": support},
        [],
    )
    candidates = [(carrier, root, root_name), (owner, owner_root, owner_name)]
    plan = prepare_object_sources(
        {"study_uid": "study-1", "objects": {"acl": {}}},
        candidates,
        tmp_path / "final.h5",
    )
    emitted: dict[str, np.ndarray] = {}
    metadata = _materialize(
        plan,
        candidates,
        {owner["artifact"]: owner_arrays},
        emitted,
    )
    row = metadata["objects"]["acl"]["observations"][0]
    assert row["carrying_record_address"]["owner_series_uid"] == "target-series"
    assert row["source_address"]["owner_series_uid"] == "source-series"
    assert row["support"]["source"]["artifact"] == owner["artifact"]
    assert row["support"]["active"]["name"] in emitted


def test_declared_companion_families_are_retained_as_whole_exact_members(tmp_path):
    arrays = {
        "a3_fibula_axial_region": np.array([1, 0, 1], dtype=np.uint8),
        "a3_fibula_axial_offsets": np.array([0, 3], dtype=np.int64),
        "a3_fibula_axial_shapes": np.array([[1, 3]], dtype=np.int32),
        "a3_fibula_axial_slices": np.array([8], dtype=np.int32),
        "a3_fibula_axial_target": np.array([1, 0, 0], dtype=np.bool_),
        "a3_fibula_axial_available": np.array([1, 1, 1], dtype=np.bool_),
        "a3_fibula_axial_origin_lps": np.array([[1.0, 2.0, 3.0]], dtype=np.float64),
        "a3_fibula_axial_basis_lps": np.eye(3, 2, dtype=np.float64)[None, ...],
        "a3_fibula_axial_normal_lps": np.array([[0.0, 0.0, 1.0]], dtype=np.float64),
        "a3_fibula_axial_thickness_mm": np.array([2.5], dtype=np.float64),
        "b1_unrelated_dark": np.ones((9, 9), dtype=np.bool_),
    }
    obs = _observation("fibula", "a3_fibula_axial_region", view=["Axial", "0", "0"])
    record, root, root_name, mapping = _record(
        tmp_path, "study-1", "series-1", "study/series-1.npz.xz", arrays, [obs]
    )
    candidates = [(record, root, root_name)]
    plan = prepare_object_sources(
        {"study_uid": "study-1", "objects": {"fibula": {}}},
        candidates,
        tmp_path / "final.h5",
    )
    emitted = {}
    metadata = _materialize(plan, candidates, {record["artifact"]: mapping}, emitted)
    row = metadata["objects"]["fibula"]["observations"][0]
    active = {row["support"]["source"]["member"]: row["support"]["active"]["name"]}
    active.update(
        {item["source"]["member"]: item["active"]["name"] for item in row["companions"]}
    )
    assert set(active) == set(arrays) - {"b1_unrelated_dark"}
    for member, output_key in active.items():
        assert emitted[output_key].dtype == arrays[member].dtype
        assert emitted[output_key].shape == arrays[member].shape
        assert digest(emitted[output_key]) == digest(arrays[member])
    assert "b1_unrelated_dark" not in active


def test_trace_profile_and_coarse_layouts_keep_their_declared_companions(tmp_path):
    trace_prefix = "a3_posterior_trace_acl"
    coarse_prefix = "a4_patella_coarse_"
    arrays = {
        f"{trace_prefix}_points_lps": np.array([[1.0, 2.0, 3.0]], dtype=np.float64),
        f"{trace_prefix}_offsets": np.array([0, 1], dtype=np.int32),
        f"{trace_prefix}_slices": np.array([5], dtype=np.int32),
        f"{trace_prefix}_starts": np.array([0], dtype=np.int32),
        f"{trace_prefix}_stops": np.array([2], dtype=np.int32),
        f"{trace_prefix}_light": np.array([3.0], dtype=np.float32),
        f"{trace_prefix}_flank": np.array([4.0], dtype=np.float32),
        f"{coarse_prefix}patella_body": np.array([1, 0], dtype=np.bool_),
        f"{coarse_prefix}patella_seeds": np.array([1, 0], dtype=np.bool_),
        f"{coarse_prefix}median": np.array([2.0, 3.0], dtype=np.float32),
        f"{coarse_prefix}depth": np.array([1.0, 0.0], dtype=np.float32),
        f"{coarse_prefix}offsets": np.array([0, 2], dtype=np.int32),
        f"{coarse_prefix}shapes": np.array([[1, 2]], dtype=np.int32),
        f"{coarse_prefix}slices": np.array([7], dtype=np.int32),
        f"{coarse_prefix}windows_rc": np.array([[2, 4, 3, 5]], dtype=np.int32),
        f"{coarse_prefix}block_px": np.array([4], dtype=np.int32),
        f"{coarse_prefix}block_mm": np.array([1.0], dtype=np.float32),
    }
    obs = [
        _observation("acl", f"{trace_prefix}_points_lps", view=["Sagittal", "0", "0"]),
        _observation(
            "patella", f"{coarse_prefix}patella_body", view=["Axial", "0", "0"]
        ),
    ]
    record, root, root_name, mapping = _record(
        tmp_path, "study-1", "series-1", "study/series-1.npz.xz", arrays, obs
    )
    candidates = [(record, root, root_name)]
    plan = prepare_object_sources(
        {"study_uid": "study-1", "objects": {"acl": {}, "patella": {}}},
        candidates,
        tmp_path / "final.h5",
    )
    emitted = {}
    metadata = _materialize(plan, candidates, {record["artifact"]: mapping}, emitted)
    assert {
        x["source"]["member"]
        for x in metadata["objects"]["acl"]["observations"][0]["companions"]
    } == set(arrays) & {
        f"{trace_prefix}_{suffix}"
        for suffix in ("offsets", "slices", "starts", "stops", "light", "flank")
    }
    patella = metadata["objects"]["patella"]["observations"][0]
    assert {x["source"]["member"] for x in patella["companions"]} == {
        f"{coarse_prefix}{suffix}"
        for suffix in (
            "offsets",
            "shapes",
            "slices",
            "windows_rc",
            "block_px",
            "block_mm",
            "median",
            "depth",
            "patella_body",
            "patella_seeds",
        )
    }


def test_profile_area_retains_its_named_status_member(tmp_path):
    value = np.array([1.25, 2.5], dtype=np.float64)
    status = np.array([1, 2], dtype=np.int8)
    arrays = {"a3_femur_profile_area_mm2": value, "a3_femur_profile_status": status}
    obs = _observation("femur", "a3_femur_profile_area_mm2")
    record, root, root_name, mapping = _record(
        tmp_path, "study-1", "series-1", "study/series-1.npz.xz", arrays, [obs]
    )
    candidates = [(record, root, root_name)]
    plan = prepare_object_sources(
        {"study_uid": "study-1", "objects": {"femur": {}}},
        candidates,
        tmp_path / "final.h5",
    )
    emitted = {}
    metadata = _materialize(plan, candidates, {record["artifact"]: mapping}, emitted)
    row = metadata["objects"]["femur"]["observations"][0]
    assert [(x["role"], x["source"]["member"]) for x in row["companions"]] == [
        ("native_slice_profile_status", "a3_femur_profile_status")
    ]


def test_exact_array_bytes_are_preserved_for_noncontiguous_float_members(tmp_path):
    words = np.array(
        [0x8000000000000000, 0x7FF8000000000011, 0x3FF0000000000000, 0],
        dtype=np.uint64,
    )
    strided = words.view(np.float64)[::2]
    assert not strided.flags.c_contiguous
    obs = _observation("femur", "a1_objects")
    record, root, root_name, mapping = _record(
        tmp_path,
        "study-1",
        "series-1",
        "study/series-1.npz.xz",
        {"a1_objects": strided},
        [obs],
    )
    candidates = [(record, root, root_name)]
    plan = prepare_object_sources(
        {"study_uid": "study-1", "objects": {"femur": {}}},
        candidates,
        tmp_path / "final.h5",
    )
    emitted: dict[str, np.ndarray] = {}
    metadata = _materialize(plan, candidates, {record["artifact"]: mapping}, emitted)
    active = metadata["objects"]["femur"]["observations"][0]["support"]["active"]
    output = emitted[active["name"]]
    assert output.dtype.str == strided.dtype.str
    assert output.shape == strided.shape
    assert output.tobytes(order="C") == strided.tobytes(order="C")
    assert active["digest"] == digest(strided)


def test_missing_owner_and_ambiguous_owner_are_distinct(tmp_path):
    obs = _observation("femur", "a1_objects", artifact="study/source.npz.xz")
    record, root, root_name, _arrays = _record(
        tmp_path, "study-1", "series-1", "study/target.npz.xz", {}, [obs]
    )
    with pytest.raises(ObjectSourceError, match="source_owner_record_missing"):
        prepare_object_sources(
            {"study_uid": "study-1", "objects": {"femur": {}}},
            [(record, root, root_name)],
            tmp_path / "final.h5",
        )
    source, source_root, source_name, _ = _record(
        tmp_path,
        "study-1",
        "series-2",
        "study/source.npz.xz",
        {"a1_objects": np.ones((1, 1), dtype=np.bool_)},
        [],
    )
    with pytest.raises(ObjectSourceError, match="source_owner_record_ambiguous"):
        prepare_object_sources(
            {"study_uid": "study-1", "objects": {"femur": {}}},
            [
                (record, root, root_name),
                (source, source_root, source_name),
                (dict(source), source_root, source_name),
            ],
            tmp_path / "final.h5",
        )


def test_digest_member_and_unopened_artifact_fail_before_finish(tmp_path):
    obs = _observation("femur", "a1_objects")
    source = np.array([1, 2], dtype=np.uint16)
    record, root, root_name, _mapping = _record(
        tmp_path,
        "study-1",
        "series-1",
        "study/series-1.npz.xz",
        {"a1_objects": source},
        [obs],
    )
    candidates = [(record, root, root_name)]
    result = {"study_uid": "study-1", "objects": {"femur": {}}}
    plan = prepare_object_sources(result, candidates, tmp_path / "final.h5")
    with pytest.raises(ObjectSourceError, match="planned_artifact_not_opened"):
        plan.finish()

    plan = prepare_object_sources(result, candidates, tmp_path / "final.h5")
    with pytest.raises(ObjectSourceError, match="source_member_digest_mismatch"):
        plan.retain_artifact(
            (root / record["artifact"]).resolve(),
            {"a1_objects": np.array([9, 9], dtype=np.uint16)},
            {},
            {},
        )
    plan = prepare_object_sources(result, candidates, tmp_path / "final.h5")
    with pytest.raises(ObjectSourceError, match="source_member_unavailable"):
        plan.retain_artifact((root / record["artifact"]).resolve(), {}, {}, {})


def test_associated_field_references_are_retained_separately(tmp_path):
    profile = np.array([1.0, 2.0], dtype=np.float32)
    support = np.array([[True]], dtype=np.bool_)
    arrays = {"a1_objects": support, "a3_femur_profile_x": profile}
    record, root, root_name, mapping = _record(
        tmp_path,
        "study-1",
        "series-1",
        "study/series-1.npz.xz",
        arrays,
        [_observation("femur", "a1_objects")],
    )
    summary = {
        "associated_fields": {
            "marrow": {
                "series": [
                    {
                        "profile_references": [
                            {
                                "artifact": record["artifact"],
                                "name": "a3_femur_profile_x",
                                "digest": digest(profile),
                            }
                        ]
                    }
                ]
            }
        }
    }
    candidates = [(record, root, root_name)]
    plan = prepare_object_sources(
        {"study_uid": "study-1", "objects": {"femur": summary}},
        candidates,
        tmp_path / "final.h5",
    )
    emitted = {}
    metadata = _materialize(plan, candidates, {record["artifact"]: mapping}, emitted)
    field = metadata["objects"]["femur"]["associated_field_references"][0]
    assert field["path"].endswith("profile_references[0]")
    assert field["source"]["member"] == "a3_femur_profile_x"
    assert field["active"]["archive"] == str((tmp_path / "final.h5").resolve())


def test_path_escape_and_object_dtype_are_refused(tmp_path):
    obs = _observation("femur", "a1_objects", artifact="../outside.npz")
    outside = tmp_path.parent / "outside.npz"
    outside.touch()
    record, root, root_name, _ = _record(
        tmp_path,
        "study-1",
        "series-1",
        "../outside.npz",
        {"a1_objects": np.ones((1, 1), dtype=np.bool_)},
        [obs],
    )
    with pytest.raises(ObjectSourceError, match="source_artifact_path_invalid"):
        prepare_object_sources(
            {"study_uid": "study-1", "objects": {"femur": {}}},
            [(record, root, root_name)],
            tmp_path / "final.h5",
        )

    obs = _observation("femur", "a1_objects")
    object_array = np.array([object()], dtype=object)
    record, root, root_name, mapping = _record(
        tmp_path,
        "study-1",
        "series-1",
        "study/series-1.npz.xz",
        {"a1_objects": object_array},
        [obs],
    )
    candidates = [(record, root, root_name)]
    plan = prepare_object_sources(
        {"study_uid": "study-1", "objects": {"femur": {}}},
        candidates,
        tmp_path / "final.h5",
    )
    with pytest.raises(ObjectSourceError, match="object_dtype_source_refused"):
        plan.retain_artifact((root / record["artifact"]).resolve(), mapping, {}, {})


def test_malformed_support_object_and_unresolved_names_are_named_refusals(tmp_path):
    base = np.ones((1, 1), dtype=np.bool_)
    cases = (
        (
            _observation("femur", {"member": "a1_objects"}),
            "observation_support_malformed",
        ),
        (_observation(["femur"], "a1_objects"), "observation_object_name_malformed"),
    )
    for observation, expected_code in cases:
        record, root, root_name, _ = _record(
            tmp_path,
            "study-1",
            "series-1",
            f"study/{expected_code}.npz.xz",
            {"a1_objects": base},
            [observation],
        )
        with pytest.raises(ObjectSourceError, match=expected_code):
            prepare_object_sources(
                {"study_uid": "study-1", "objects": {"femur": {}}},
                [(record, root, root_name)],
                tmp_path / "final.h5",
            )

    record, root, root_name, _ = _record(
        tmp_path,
        "study-1",
        "series-1",
        "study/unresolved.npz.xz",
        {},
        [],
        [{"object": "missing_object", "code": "abstain_not_found"}],
    )
    with pytest.raises(ObjectSourceError, match="unresolved_object_not_catalogued"):
        prepare_object_sources(
            {"study_uid": "study-1", "objects": {"femur": {}}},
            [(record, root, root_name)],
            tmp_path / "final.h5",
        )


def test_reference_like_associated_field_without_digest_is_not_dropped(tmp_path):
    record, root, root_name, _ = _record(
        tmp_path,
        "study-1",
        "series-1",
        "study/associated.npz.xz",
        {},
        [],
    )
    result = {
        "study_uid": "study-1",
        "objects": {
            "femur": {
                "associated_fields": {
                    "marrow": {
                        "reference": {
                            "artifact": record["artifact"],
                            "name": "a3_femur_profile",
                        }
                    }
                }
            }
        },
    }
    with pytest.raises(ObjectSourceError, match="associated_field_reference_malformed"):
        prepare_object_sources(
            result, [(record, root, root_name)], tmp_path / "final.h5"
        )


def test_unknown_coarse_family_refuses_and_source_address_scalars_are_json_native(
    tmp_path,
):
    obs = _observation(
        "femur",
        "a4_axial_coarse_unrecognized",
        artifact="study/coarse.npz.xz",
    )
    record, root, root_name, _ = _record(
        tmp_path,
        "study-1",
        "series-1",
        "study/coarse.npz.xz",
        {"a4_axial_coarse_unrecognized": np.ones((1,), dtype=np.bool_)},
        [obs],
    )
    with pytest.raises(ObjectSourceError, match="unsupported_coarse_support_layout"):
        prepare_object_sources(
            {"study_uid": "study-1", "objects": {"femur": {}}},
            [(record, root, root_name)],
            tmp_path / "final.h5",
        )

    obs = _observation(
        "femur",
        "a1_objects",
        row=np.int64(0),
        artifact="study/native-scalars.npz.xz",
    )
    record, root, root_name, _ = _record(
        tmp_path,
        "study-1",
        "series-1",
        "study/native-scalars.npz.xz",
        {"a1_objects": np.ones((1, 1), dtype=np.bool_)},
        [obs],
    )
    record["slice_index"] = np.int64(4)
    plan = prepare_object_sources(
        {"study_uid": "study-1", "objects": {"femur": {}}},
        [(record, root, root_name)],
        tmp_path / "final.h5",
    )
    address = plan._objects["femur"]["_pending_observations"][0]["source_address"]
    assert address["owner_slice_index"] == 4
    assert type(address["owner_slice_index"]) is int
    assert type(address["row"]) is int


def test_new_retained_source_enters_shared_verified_cache(tmp_path):
    support = np.array([[True, False], [False, True]], dtype=np.bool_)
    observation = _observation("femur", "a1_objects")
    record, root, root_name, arrays = _record(
        tmp_path,
        "study-1",
        "series-1",
        "study/series-1.npz.xz",
        {"a1_objects": support},
        [observation],
    )
    plan = prepare_object_sources(
        {"study_uid": "study-1", "objects": {"femur": {}}},
        [(record, root, root_name)],
        tmp_path / "final.h5",
    )
    verified = {}
    emitted = {}
    plan.retain_artifact(root / record["artifact"], arrays, verified, emitted)
    assert set(verified) == {("a1_objects", digest(support))}
    assert verified[("a1_objects", digest(support))] is support
    assert plan.finish()["array_count"] == 1
