"""Teacher support stays distinct from its bounding box and its context."""

from __future__ import annotations

import io
import lzma
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from squint_upgrade_fixtures import STUDY_UID, series_record

from knee.diagnosis.squint_interfaces import (
    LEG_INSIDE,
    LEG_MAP_SCHEMA,
    LEG_MIXED,
    LEG_OUTSIDE,
    LEG_UNKNOWN,
    ROLE_CONTEXT,
    ROLE_OBJECT,
    ROLE_OUTSIDE_LEG,
    territory_code,
)
from knee.diagnosis.squint_memory import SquintMemoryError, _support_bbox
from knee.diagnosis.squint_support import support_mask, teacher_territory


def _series() -> dict:
    return {
        "series_uid": "series",
        "shape": (1, 8, 8),
        "view": {"orientation": "Coronal"},
        "stack": SimpleNamespace(
            median=np.zeros((1, 2, 2)),
            bounds_rc=np.array(
                [[[0, 4, 0, 4], [0, 4, 4, 8]], [[4, 8, 0, 4], [4, 8, 4, 8]]]
            ),
            tile_mm=10.0,
        ),
    }


def _address(series_uid: str = "series", slice_index: int = 0) -> dict:
    return {
        "target_series_uid": series_uid,
        "observation_slices": [slice_index],
        "observation_view": ["Coronal", "1", "1"],
        "observation_support": "body",
        "native_shape_rc": [8, 8],
        "address_kind": "native_rc",
        "geometry_status": "available",
    }


def _info(mask: np.ndarray, series_uid: str = "series", slice_index: int = 0) -> dict:
    rows, cols = np.nonzero(mask)
    return {
        "code": "resolved",
        "mask": mask,
        "bbox": (
            int(rows.min()),
            int(rows.max()) + 1,
            int(cols.min()),
            int(cols.max()) + 1,
        ),
        "source_address": _address(series_uid, slice_index),
        "provenance": {"fixture": True},
    }


def _public_entry(points: np.ndarray) -> dict:
    return {
        "source_address": _address(),
        "links": [
            {
                "coordinate_field": "points_rc",
                "coordinate_member": "points",
                "profile_object": "femur",
                "place_count": len(points),
                "metadata": {
                    "observation": {
                        "series_uid": "series",
                        "slices": [0],
                        "support": "body",
                        "view": ["Coronal", "1", "1"],
                    }
                },
            }
        ],
    }


def _artifact(tmp_path: Path, arrays: dict, address: dict) -> tuple[dict, dict]:
    buffer = io.BytesIO()
    np.savez_compressed(buffer, **arrays)
    path = tmp_path / "support.npz.xz"
    path.write_bytes(lzma.compress(buffer.getvalue()))
    address.update(observation_artifact=path.name, source_root="run")
    return {"femur": {"addressed_supports": [{"source_address": address}]}}, {
        "run": str(tmp_path)
    }


def test_two_of_four_tiles_are_object_with_native_pixel_shares() -> None:
    mask = np.zeros((8, 8), dtype=np.bool_)
    mask[1:3, 1:3] = True
    mask[1:3, 4:8] = True
    info = _info(mask)
    result = teacher_territory("study", _series(), "femur", info, 0)
    assert result["code"] == "resolved"
    assert territory_code(result, grid_shape=(1, 2, 2)) == "valid"
    assert result["origin"] == "teacher_support"
    assert result["tile_window"] == [0, 1, 0, 2, 0, 2]
    np.testing.assert_array_equal(
        result["roles"], [[[ROLE_OBJECT, ROLE_OBJECT], [ROLE_CONTEXT, ROLE_CONTEXT]]]
    )
    np.testing.assert_array_equal(result["object_share"], [[[0.25, 0.5], [0.0, 0.0]]])
    native = result["native_support"]
    assert native["slices"] == [0]
    assert native["offset_rc"] == [1, 1]
    np.testing.assert_array_equal(native["mask"], mask[None, 1:3, 1:8])
    assert result["provenance"]["source_address"] == info["source_address"]


def test_same_box_different_footprints_have_different_roles_and_shares() -> None:
    sparse = np.zeros((8, 8), dtype=np.bool_)
    sparse[0, 0] = sparse[7, 7] = True
    full = np.ones((8, 8), dtype=np.bool_)
    left = teacher_territory("study", _series(), "femur", _info(sparse), 0)
    right = teacher_territory("study", _series(), "femur", _info(full), 0)
    assert left["tile_window"] == right["tile_window"]
    assert (
        left["provenance"]["native_bounds_rc"]
        == right["provenance"]["native_bounds_rc"]
    )
    np.testing.assert_array_equal(
        left["roles"], [[[ROLE_OBJECT, ROLE_CONTEXT], [ROLE_CONTEXT, ROLE_OBJECT]]]
    )
    np.testing.assert_array_equal(left["object_share"], [[[1 / 16, 0], [0, 1 / 16]]])
    assert np.all(right["roles"] == ROLE_OBJECT)
    assert np.all(right["object_share"] == 1)


def test_shared_fixture_gets_exactly_one_spatial_context_ring() -> None:
    series = series_record()
    mask = np.zeros(series["shape"][1:], dtype=np.bool_)
    mask[61:64, 62:68] = True
    result = teacher_territory(
        STUDY_UID, series, "medial_meniscus", _info(mask, series["series_uid"], 1), 1
    )
    assert territory_code(result, grid_shape=(3, 8, 8)) == "valid"
    assert result["tile_window"] == [1, 2, 2, 5, 2, 5]
    assert np.count_nonzero(result["roles"] == ROLE_OBJECT) == 1
    assert np.count_nonzero(result["roles"] == ROLE_CONTEXT) == 8
    assert result["object_share"][0, 1, 1] == 18 / 400
    assert result["native_support"]["offset_rc"] == [61, 62]


def test_partial_edge_tile_uses_its_actual_native_area() -> None:
    series = _series()
    series["shape"] = (1, 7, 6)
    series["stack"].bounds_rc = np.array(
        [[[0, 4, 0, 4], [0, 4, 4, 6]], [[4, 7, 0, 4], [4, 7, 4, 6]]]
    )
    mask = np.zeros((7, 6), dtype=np.bool_)
    mask[6, 5] = True
    result = teacher_territory("study", series, "femur", _info(mask), 0)
    assert result["code"] == "resolved"
    assert result["object_share"][0, 1, 1] == 1 / 6
    assert result["native_support"]["offset_rc"] == [6, 5]


def _leg(codes: np.ndarray) -> dict:
    share = np.full(codes.shape, np.nan)
    share[codes == LEG_INSIDE] = 1
    share[codes == LEG_OUTSIDE] = 0
    share[codes == LEG_MIXED] = 0.5
    return {
        "schema": LEG_MAP_SCHEMA,
        "study_uid": "study",
        "series_uid": "series",
        "tile_mm": 10.0,
        "rule": "fixture",
        "codes": codes,
        "leg_share": share,
        "provenance": {},
    }


def test_only_explicit_outside_leg_overrides_object_or_context() -> None:
    mask = np.ones((8, 8), dtype=np.bool_)
    codes = np.array(
        [[[LEG_OUTSIDE, LEG_MIXED], [LEG_UNKNOWN, LEG_INSIDE]]], dtype=np.int8
    )
    result = teacher_territory("study", _series(), "femur", _info(mask), 0, _leg(codes))
    np.testing.assert_array_equal(
        result["roles"], [[[ROLE_OUTSIDE_LEG, ROLE_OBJECT], [ROLE_OBJECT, ROLE_OBJECT]]]
    )
    # The contradictory support measurement is retained, not silently erased.
    assert np.all(result["object_share"] == 1)
    np.testing.assert_array_equal(result["native_support"]["mask"], mask[None])


def test_outside_context_adds_no_object_and_unknown_is_not_outside() -> None:
    mask = np.zeros((8, 8), dtype=np.bool_)
    mask[0, 0] = True
    codes = np.array(
        [[[LEG_UNKNOWN, LEG_OUTSIDE], [LEG_MIXED, LEG_INSIDE]]], dtype=np.int8
    )
    result = teacher_territory("study", _series(), "femur", _info(mask), 0, _leg(codes))
    np.testing.assert_array_equal(
        result["roles"],
        [[[ROLE_OBJECT, ROLE_OUTSIDE_LEG], [ROLE_CONTEXT, ROLE_CONTEXT]]],
    )


def test_entire_support_outside_leg_is_named_and_preserved() -> None:
    info = _info(np.ones((8, 8), dtype=np.bool_))
    result = teacher_territory(
        "study", _series(), "femur", info, 0, _leg(np.zeros((1, 2, 2), dtype=np.int8))
    )
    assert result["code"] == "support_outside_leg"
    assert result["support"] is info
    assert "tile_window" not in result


def test_unavailable_support_never_becomes_a_location_box() -> None:
    info = support_mask("femur", "series", 0, {}, {}, {})
    assert info["code"] == "support_unavailable"
    assert info["mask"] is info["bbox"] is None
    result = teacher_territory("study", _series(), "femur", info, 0)
    assert result["code"] == "support_unavailable"
    assert "tile_window" not in result
    assert _support_bbox("femur", "series", 0, {}, {}, {}) is None


@pytest.mark.parametrize(
    "defect,expected",
    [
        ("empty", "support_empty"),
        ("dtype", "support_mask_invalid"),
        ("shape", "support_mask_invalid"),
        ("bbox", "support_bounds_invalid"),
        ("padded", "support_bounds_mismatch"),
        ("address", "support_address_mismatch"),
        ("slice_list", "support_address_mismatch"),
        ("grid", "support_grid_unavailable"),
        ("tile", "support_tile_bounds_invalid"),
        ("slice", "support_slice_outside_series"),
    ],
)
def test_malformed_inputs_have_named_refusals(defect: str, expected: str) -> None:
    mask = np.zeros((8, 8), dtype=np.bool_)
    mask[1:3, 1:3] = True
    info = _info(mask)
    series = _series()
    slice_index = 0
    if defect == "empty":
        info["mask"][:] = False
    elif defect == "dtype":
        info["mask"] = mask.astype(np.uint8)
    elif defect == "shape":
        info["mask"] = mask[:4]
    elif defect == "bbox":
        info["bbox"] = (-1, 3, 1, 3)
    elif defect == "padded":
        info["bbox"] = (0, 4, 0, 4)
    elif defect == "address":
        info["source_address"]["target_series_uid"] = "another"
    elif defect == "slice_list":
        info["source_address"]["observation_slices"] = None
    elif defect == "grid":
        series["stack"] = None
    elif defect == "tile":
        series["stack"].bounds_rc[0, 0, 0] = -1
    elif defect == "slice":
        slice_index = 1
    assert (
        teacher_territory("study", series, "femur", info, slice_index)["code"]
        == expected
    )


def test_leg_map_from_another_series_is_refused() -> None:
    leg = _leg(np.ones((1, 2, 2), dtype=np.int8))
    leg["series_uid"] = "other"
    result = teacher_territory(
        "study", _series(), "femur", _info(np.ones((8, 8), dtype=np.bool_)), 0, leg
    )
    assert result["code"] == "support_leg_map_identity_mismatch"


def test_public_coordinate_support_preserves_holes_and_address() -> None:
    points = np.array([[1, 1], [6, 6], [1, 1]], dtype=np.int32)
    entry = _public_entry(points)
    ownership = {"femur": {"addressed_supports": [entry]}}
    result = support_mask("femur", "series", 0, ownership, {}, {}, {"points": points})
    assert result["code"] == "resolved"
    assert result["bbox"] == (1, 7, 1, 7)
    assert result["source_address"] == entry["source_address"]
    assert result["provenance"]["coordinate_member"] == "points"
    assert np.count_nonzero(result["mask"]) == 2
    assert not result["mask"][3, 3]
    assert (
        _support_bbox("femur", "series", 0, ownership, {}, {}, {"points": points})
        == result["bbox"]
    )
    assert (
        support_mask("femur", "series", 1, ownership, {}, {}, {"points": points})[
            "code"
        ]
        == "support_unavailable"
    )


def test_empty_public_support_cannot_fall_back_to_nonempty_artifact(
    tmp_path: Path,
) -> None:
    points = np.zeros((0, 2), dtype=np.int32)
    entry = _public_entry(points)
    ownership, roots = _artifact(
        tmp_path, {"body": np.ones((8, 8))}, entry["source_address"]
    )
    ownership["femur"]["addressed_supports"][0] = entry
    result = support_mask(
        "femur", "series", 0, ownership, roots, {}, {"points": points}
    )
    assert result["code"] == "support_unavailable"


def test_invalid_public_coordinate_keeps_existing_named_exception() -> None:
    points = np.array([[8, 1]], dtype=np.int32)
    entry = _public_entry(points)
    with pytest.raises(SquintMemoryError, match="support_coordinate_out_of_bounds"):
        support_mask(
            "femur",
            "series",
            0,
            {"femur": {"addressed_supports": [entry]}},
            {},
            {},
            {"points": points},
        )


def test_artifact_label_mask_excludes_neighbors_and_reuses_cache(
    tmp_path: Path,
) -> None:
    labels = np.zeros((8, 8), dtype=np.int16)
    labels[1, 1] = labels[6, 6] = 3
    labels[2:6, 2:6] = 7
    address = _address()
    address["observation_label"] = 3
    ownership, roots = _artifact(tmp_path, {"body": labels}, address)
    cache = {}
    result = support_mask("femur", "series", 0, ownership, roots, cache)
    assert result["bbox"] == (1, 7, 1, 7)
    np.testing.assert_array_equal(result["mask"], labels == 3)
    assert len(cache) == 1
    again = support_mask("femur", "series", 0, ownership, roots, cache)
    np.testing.assert_array_equal(again["mask"], result["mask"])
    assert (
        _support_bbox("femur", "series", 0, ownership, roots, cache) == result["bbox"]
    )


def test_artifact_companion_row_is_checked_against_observation_slice(
    tmp_path: Path,
) -> None:
    masks = np.zeros((2, 8, 8), dtype=np.bool_)
    masks[1, 2:4, 3:7] = True
    address = _address(slice_index=4)
    address.update(
        observation_row=1,
        observation_support="a3_femur_plane_region",
        record_slice_index=0,
    )
    ownership, roots = _artifact(
        tmp_path,
        {"a3_femur_plane_region": masks, "a3_femur_plane_slices": np.array([0, 4])},
        address,
    )
    result = support_mask("femur", "series", 4, ownership, roots, {})
    assert result["bbox"] == (2, 4, 3, 7)
    np.testing.assert_array_equal(result["mask"], masks[1])
    address["observation_row"] = 0
    assert (
        support_mask("femur", "series", 4, ownership, roots, {})["code"]
        == "support_unavailable"
    )


def test_empty_or_missing_artifact_has_no_guessed_bounds(tmp_path: Path) -> None:
    ownership, roots = _artifact(tmp_path, {"body": np.zeros((8, 8))}, _address())
    assert (
        support_mask("femur", "series", 0, ownership, roots, {})["code"]
        == "support_unavailable"
    )
    (tmp_path / "support.npz.xz").unlink()
    assert (
        support_mask("femur", "series", 0, ownership, roots, {})["code"]
        == "support_unavailable"
    )


def test_artifact_path_cannot_escape_its_source_root(tmp_path: Path) -> None:
    ownership, roots = _artifact(tmp_path, {"body": np.ones((8, 8))}, _address())
    nested = tmp_path / "nested"
    nested.mkdir()
    roots["run"] = str(nested)
    ownership["femur"]["addressed_supports"][0]["source_address"][
        "observation_artifact"
    ] = "../support.npz.xz"
    assert (
        support_mask("femur", "series", 0, ownership, roots, {})["code"]
        == "support_unavailable"
    )
