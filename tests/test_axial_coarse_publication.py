"""The retained axial coarse products stay separate native readings."""

from __future__ import annotations

import numpy as np
import pytest

from knee.collapse.coarse_section import (
    EMPTY,
    NO_BONE_SCALE,
    NOT_READ,
    SECTION,
    SEEDS_UNSEEN,
    SHARED,
    STATUS_CODES,
)
from knee.encoding.mri_coarse_spec import COARSE_BANKS, make_mri_coarse_spec
from knee.encoding.mri_spec import BASE_SLICE_VIEWS, make_mri_spec
from scripts import run_interiors as run


def _packed_rows() -> dict[str, np.ndarray]:
    offsets = np.array([0, 4, 8, 12], dtype=np.int64)
    arrays: dict[str, np.ndarray] = {
        "a4_axial_coarse_slices": np.array([4, 7, 11], dtype=np.int32),
        "a4_axial_coarse_offsets": offsets,
        "a4_axial_coarse_shapes": np.tile(np.array([[2, 2]], dtype=np.int32), (3, 1)),
    }
    for bone in ("femur", "tibia"):
        for suffix in ("body", "seeds", "estimate_body"):
            arrays[f"a4_axial_coarse_{bone}_{suffix}"] = np.zeros(12, dtype=bool)
        arrays[f"a4_axial_coarse_{bone}_status"] = np.full(
            3, STATUS_CODES[NOT_READ], dtype=np.int8
        )
        arrays[f"a4_axial_coarse_{bone}_estimate_made"] = np.array(
            [True, True, False], dtype=bool
        )
        arrays[f"a4_axial_coarse_{bone}_estimate_status"] = np.array(
            [STATUS_CODES[NOT_READ], STATUS_CODES[NOT_READ], STATUS_CODES[NOT_READ]],
            dtype=np.int8,
        )
    arrays["a4_axial_coarse_femur_status"] = np.array(
        [STATUS_CODES[SECTION], STATUS_CODES[EMPTY], STATUS_CODES[NOT_READ]],
        dtype=np.int8,
    )
    arrays["a4_axial_coarse_femur_body"][:4] = [True, True, False, False]
    arrays["a4_axial_coarse_femur_seeds"][4] = True
    arrays["a4_axial_coarse_femur_estimate_status"] = np.array(
        [STATUS_CODES[NO_BONE_SCALE], STATUS_CODES[EMPTY], STATUS_CODES[NOT_READ]],
        dtype=np.int8,
    )
    arrays["a4_axial_coarse_tibia_status"] = np.array(
        [STATUS_CODES[SHARED], STATUS_CODES[SEEDS_UNSEEN], STATUS_CODES[NOT_READ]],
        dtype=np.int8,
    )
    arrays["a4_axial_coarse_tibia_seeds"][:4] = [True, True, False, False]
    arrays["a4_axial_coarse_tibia_seeds"][4] = True
    arrays["a4_axial_coarse_tibia_estimate_status"] = np.array(
        [STATUS_CODES[SHARED], STATUS_CODES[SEEDS_UNSEEN], STATUS_CODES[NOT_READ]],
        dtype=np.int8,
    )
    return arrays


def test_axial_products_keep_distinct_supports_and_producer_statuses():
    arrays = _packed_rows()
    original_statuses = arrays["a4_axial_coarse_femur_status"].copy()
    record = {"series_uid": "axial-series", "view": ["Axial", "1", "1"]}
    rows = run._axial_coarse_observations(record, arrays, "study/axial-series.npz.xz")

    femur = [row for row in rows if row.object == "femur"]
    tibia = [row for row in rows if row.object == "tibia"]
    assert [(r.slices, r.code, r.support, r.count) for r in femur] == [
        ((4,), SECTION, "a4_axial_coarse_femur_body", 2),
        ((4,), NO_BONE_SCALE, "a4_axial_coarse_femur_estimate_body", 0),
        ((7,), EMPTY, "a4_axial_coarse_femur_seeds", 1),
        ((7,), EMPTY, "a4_axial_coarse_femur_estimate_body", 0),
    ]
    assert [(r.slices, r.code, r.support, r.count) for r in tibia] == [
        ((4,), SHARED, "a4_axial_coarse_tibia_seeds", 2),
        ((4,), SHARED, "a4_axial_coarse_tibia_estimate_body", 0),
        ((7,), SEEDS_UNSEEN, "a4_axial_coarse_tibia_seeds", 1),
        ((7,), SEEDS_UNSEEN, "a4_axial_coarse_tibia_estimate_body", 0),
    ]
    assert all(row.provenance == "native" and row.kind == "reading" for row in rows)
    assert all(
        row.off_plane_mm == 0.0 and row.artifact == "study/axial-series.npz.xz"
        for row in rows
    )
    assert all("coarse blocks, not native pixels" in row.note for row in rows)
    np.testing.assert_array_equal(
        arrays["a4_axial_coarse_femur_status"], original_statuses
    )


def test_not_read_and_inactive_estimates_do_not_create_empty_observations():
    arrays = _packed_rows()
    rows = run._axial_coarse_observations(
        {"series_uid": "axial-series", "view": ["Axial", "1", "1"]},
        arrays,
        "study/axial-series.npz.xz",
    )
    assert all(11 not in row.slices for row in rows)
    arrays["a4_axial_coarse_femur_estimate_made"][1] = False
    rows = run._axial_coarse_observations(
        {"series_uid": "axial-series", "view": ["Axial", "1", "1"]},
        arrays,
        "study/axial-series.npz.xz",
    )
    assert not any(
        row.support == "a4_axial_coarse_femur_estimate_body" and row.slices == (7,)
        for row in rows
    )


def test_malformed_packed_geometry_is_refused_by_name():
    arrays = _packed_rows()
    arrays["a4_axial_coarse_offsets"] = np.array([0, 4, 9, 12], dtype=np.int64)
    with pytest.raises(ValueError, match="invalid_axial_coarse_packed_geometry"):
        run._axial_coarse_observations(
            {"series_uid": "axial-series", "view": ["Axial", "1", "1"]},
            arrays,
            "study/axial-series.npz.xz",
        )


def test_coarse_spec_has_separate_product_banks_and_all_acquisition_roles():
    spec = make_mri_coarse_spec()
    base = make_mri_spec()
    banks = {bank["name"]: bank for bank in spec["banks"]}
    assert all(banks[bank["name"]] == bank for bank in base["banks"])
    assert all(banks[bank["name"]] == bank for bank in COARSE_BANKS)
    roles = tuple(tuple(role) for role in spec["object_composition"]["view_roles"])
    expected = {
        (orientation, fluid, fat)
        for orientation in ("Sagittal", "Coronal", "Axial")
        for fluid in ("0", "1")
        for fat in ("0", "1")
    }
    assert set(roles) == expected and len(roles) == 12
    assert set(map(tuple, BASE_SLICE_VIEWS)).issubset(set(roles))
    plans = {row["base_bank"]: row for row in spec["object_composition"]["bank_plans"]}
    assert (
        plans["coarse_unfiltered"]["scale_scope"] == "producer_unfiltered_coarse_grid"
    )
    assert (
        plans["coarse_scale_filtered"]["scale_scope"]
        == "producer_scale_filtered_coarse_grid"
    )
    coarse_profiles = [
        p
        for p in spec["profiles"]
        if p.get("support_layout", {}).get("family") == "native_coarse_blocks"
    ]
    assert {p["support"] for p in coarse_profiles} >= {
        "a4_axial_coarse_femur_body",
        "a4_axial_coarse_femur_seeds",
        "a4_axial_coarse_femur_estimate_body",
        "a4_axial_coarse_tibia_body",
        "a4_axial_coarse_tibia_seeds",
        "a4_axial_coarse_tibia_estimate_body",
        "a4_patella_coarse_patella_body",
        "a4_patella_coarse_patella_seeds",
        "{arrays_prefix}_fibula_body",
        "{arrays_prefix}_fibula_seeds",
    }
    for profile in coarse_profiles:
        assert profile["references"] == []
        assert profile["view"] is None
        assert profile["support_layout"]["count_meaning"] == "coarse_blocks"
        readings = {(r["bank"], r["metric"]): r for r in profile["readings"]}
        active = (
            "coarse_scale_filtered"
            if profile["support"].endswith("estimate_body")
            else "coarse_unfiltered"
        )
        assert readings[(active, "membership")]["value"] == profile["support"]
        assert readings[(active, "membership")]["availability_policy"] == "all_stored"
        assert readings[(active, "median")]["availability_policy"] == "finite_values"
        assert readings[(active, "depth")]["availability_policy"] == "finite_values"
        inactive = (
            "coarse_unfiltered"
            if active == "coarse_scale_filtered"
            else "coarse_scale_filtered"
        )
        assert all(
            readings[(inactive, metric)]["source"] == "unread"
            for metric in ("membership", "median", "depth")
        )
