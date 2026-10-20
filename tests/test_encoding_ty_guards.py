from __future__ import annotations

import numpy as np
import pytest

from knee.encoding.coarse_blocks import (
    GRID_WINDOW_MISMATCH,
    CoarseRowGeometry,
    block_native_bounds,
)
from knee.encoding.mri_spec import make_mri_spec
from knee.encoding.operation import _coarse_inputs, _retained_ordinary_profiles


def test_block_bounds_refuse_success_code_without_required_geometry() -> None:
    geometry = CoarseRowGeometry(code="ok", row=0, grid_shape=(1, 1))
    status, bounds = block_native_bounds(geometry, np.asarray([[0, 0]], dtype=np.int64))
    assert status == GRID_WINDOW_MISMATCH
    assert bounds is None


def test_coarse_target_without_owner_artifact_has_named_refusal() -> None:
    spec = make_mri_spec(include_coarse=True)
    profile = next(
        item
        for item in spec["profiles"]
        if item.get("support_layout", {}).get("family") == "native_coarse_blocks"
        and item["object"] == "fibula"
        and item["support"].endswith("_fibula_body")
    )
    target_uid = "target-series"
    prefix = "a4_fibula_coarse_target-series"
    record = {
        "artifact": None,
        "series_uid": "owner-series",
        "fibula_key_planes": {
            target_uid: {
                "orientation": "axial",
                "arrays_prefix": prefix,
                "slices_read": [5],
            }
        },
    }
    observation = {
        "support": f"{prefix}_fibula_body",
        "series_uid": target_uid,
        "view": ["Axial", "1", "1"],
        "slices": [5],
        "row": 0,
    }
    layout, bindings, problem = _coarse_inputs(profile, record, observation)
    assert layout is None
    assert bindings is None
    assert problem == "target_identity_invalid"


def test_retained_ordinary_rejects_malformed_bank_declaration() -> None:
    observation = {
        "object": "femur",
        "provenance": "native",
        "kind": "resolved",
        "support": "a2_anterior_synovial_recess",
        "artifact": "study/series.npz.xz",
        "series_uid": "series",
        "view": ["Sagittal", "0", "0"],
        "slices": [4],
        "row": None,
    }
    record = {
        "artifact": observation["artifact"],
        "series_uid": observation["series_uid"],
        "slice_index": 4,
        "observations": [observation],
    }
    with pytest.raises(TypeError, match="ordinary_expansion_bank_declaration_invalid"):
        _retained_ordinary_profiles([record], [], [{"name": "bad", "metrics": None}])
