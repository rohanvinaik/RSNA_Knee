import sys
import types
from dataclasses import dataclass

import numpy as np
import pytest

try:
    from knee.encoding.scoped import ScopedEncoding
except ImportError:  # test-only stub; not a production file
    from knee.encoding.places import EncodingResult

    @dataclass(frozen=True, slots=True)
    class ScopedEncoding:
        status: str
        encoding: EncodingResult | None
        coordinates: np.ndarray | None
        address_kind: str
        metadata: dict

    _mod = types.ModuleType("knee.encoding.scoped")
    _mod.ScopedEncoding = ScopedEncoding
    sys.modules["knee.encoding.scoped"] = _mod

from knee.encoding.coarse_adapter import (
    CoarseBlockLayout,
    CoarseTargetEvidence,
    encode_coarse_observation,
)
from knee.encoding.coarse_blocks import (
    block_native_bounds,
    coarse_row_geometry,
    support_block_coordinates,
)
from knee.encoding.handoff import digest
from knee.encoding.places import (
    BankSpec,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    NumericReference,
    compile_layout,
)

ROW0 = (5, (0, 10, 0, 10), (4, 4), (2.0, 2.0), {(0, 0), (2, 2), (1, 1)})
ROW1 = (7, (2, 6, 3, 9), (2, 3), (2.0, 3.0), {(1, 1)})
VIEW = ["Axial", "1", "1"]


def make_layout():
    spec = LayoutSpec(
        "v1",
        "test-carrier",
        (
            BankSpec(
                "b",
                "f",
                (
                    MetricSpec("flag", MetricKind.WORDS, ("False", "True")),
                    MetricSpec("med", MetricKind.DIGIT),
                ),
            ),
        ),
    )
    return compile_layout(spec)


def refs(layout):
    return {
        ("b", "med"): NumericReference(
            layout.fingerprint, "b", "med", "r", "s", "u", 1.0, 5.0
        )
    }


def ceil_div(a, b):
    return -(-a // b)


def build(rows=(ROW0, ROW1), prefix="c", **over):
    shapes, windows, pxs, mms, sl, body = [], [], [], [], [], []
    sizes = []
    for s, win, px, mm, on in rows:
        g = (ceil_div(win[1] - win[0], px[0]), ceil_div(win[3] - win[2], px[1]))
        shapes.append(g)
        windows.append(win)
        pxs.append(px)
        mms.append(mm)
        sl.append(s)
        sizes.append(g[0] * g[1])
        grid = np.zeros(g, bool)
        for i, j in on:
            grid[i, j] = True
        body.append(grid.ravel())
    n = len(rows)
    total = sum(sizes)
    med = np.arange(total, dtype=np.float32) + 1.0
    if total > 4:
        med[4] = np.nan
    data = {
        "offsets": np.concatenate(([0], np.cumsum(sizes))).astype(np.int64),
        "shapes": np.array(shapes, np.int32).reshape(n, 2),
        "slices": np.array(sl, np.int32),
        "windows_rc": np.array(windows, np.int32).reshape(n, 4),
        "block_px": np.array(pxs, np.int32).reshape(n, 2),
        "block_mm": np.array(mms, np.float64).reshape(n, 2),
        "median": med,
        "body": np.concatenate(body) if body else np.empty(0, bool),
    }
    data.update(over)
    arrays = {f"{prefix}_{k}": v for k, v in data.items()}
    record = {
        "artifact": "S/A-fibula.npz.xz",
        "series_uid": "U",
        "view": list(VIEW),
        "arrays": {k: {"digest": digest(v)} for k, v in arrays.items()},
    }
    coarse = CoarseBlockLayout(
        f"{prefix}_offsets",
        f"{prefix}_shapes",
        f"{prefix}_slices",
        f"{prefix}_windows_rc",
        f"{prefix}_block_px",
        f"{prefix}_block_mm",
        (f"{prefix}_median", f"{prefix}_body"),
    )
    return record, arrays, coarse


def obs(row=0, slice_=5, prefix="c", **kw):
    o = {
        "object": "patella",
        "provenance": "native",
        "kind": "reading",
        "view": list(VIEW),
        "series_uid": "U",
        "slices": [slice_],
        "artifact": "S/A-fibula.npz.xz",
        "support": f"{prefix}_body",
        "row": row,
        "label": None,
        "count": None,
    }
    o.update(kw)
    return o


def bind(prefix="c", policy="finite_values"):
    return [
        {
            "bank": "b",
            "metric": "flag",
            "value": f"{prefix}_body",
            "availability_policy": "all_stored",
        },
        {
            "bank": "b",
            "metric": "med",
            "value": f"{prefix}_median",
            "availability_policy": policy,
        },
    ]


def run(record, arrays, coarse, observation=None, bindings=None, references=True, **kw):
    layout = make_layout()
    return encode_coarse_observation(
        record,
        observation or obs(),
        arrays,
        layout,
        bindings or bind(),
        refs(layout) if references else {},
        coarse,
        **kw,
    )


def test_exact_grid_and_clipped_bounds_without_expansion():
    record, arrays, coarse = build()
    r = run(record, arrays, coarse)
    assert isinstance(r, ScopedEncoding)
    assert r.address_kind == "coarse_grid_rc"
    assert r.coordinates.tolist() == [[0, 0], [1, 1], [2, 2]]
    assert r.metadata["native_bounds_rc"].tolist() == [
        [0, 4, 0, 4],
        [4, 8, 4, 8],
        [8, 10, 8, 10],
    ]
    assert r.metadata["scope_address"]["grid_shape"] == [3, 3]
    assert r.metadata["scope_address"]["window_rc"] == [0, 10, 0, 10]


def test_variable_shape_second_row_and_window_offset():
    record, arrays, coarse = build()
    r = run(record, arrays, coarse, obs(row=1, slice_=7))
    assert r.coordinates.tolist() == [[1, 1]]
    assert r.metadata["native_bounds_rc"].tolist() == [[4, 6, 6, 9]]
    assert r.metadata["scope_address"]["grid_shape"] == [2, 2]
    assert r.metadata["scope_address"]["block_px"] == [2, 3]


def test_availability_nan_and_policies():
    record, arrays, coarse = build()
    r = run(record, arrays, coarse)
    med = next(m for m in r.encoding.metrics if m.metric == "med")
    assert med.source_available.tolist() == [True, False, True]  # block (1,1) is NaN
    assert np.isnan(med.source_values[1])
    flag = next(m for m in r.encoding.metrics if m.metric == "flag")
    assert flag.source_available.all()
    bad = run(record, arrays, coarse, bindings=bind(policy="all_stored"))
    assert bad.status == "availability_policy_dtype_mismatch"
    bad2 = run(
        record,
        arrays,
        coarse,
        bindings=[
            {
                "bank": "b",
                "metric": "flag",
                "value": "c_median",
                "availability_policy": "finite_values",
            }
        ],
    )
    assert bad2.status == "invalid_input"


def test_named_bool_availability_array():
    n = 13
    avail = np.zeros(n, bool)
    avail[0] = True
    record, arrays, coarse = build(avail=avail)
    coarse = (
        CoarseBlockLayout(
            **{**coarse.__dict__, "packed_arrays": coarse.packed_arrays + ("c_avail",)}
        )
        if False
        else CoarseBlockLayout(
            coarse.offsets,
            coarse.shapes,
            coarse.slices,
            coarse.windows_rc,
            coarse.block_px,
            coarse.block_mm,
            coarse.packed_arrays + ("c_avail",),
        )
    )
    b = bind()
    b[1] = {"bank": "b", "metric": "med", "value": "c_median", "available": "c_avail"}
    r = run(record, arrays, coarse, bindings=b)
    med = next(m for m in r.encoding.metrics if m.metric == "med")
    assert med.source_available.tolist() == [True, False, False]


def test_missing_reference_preserved():
    record, arrays, coarse = build()
    r = run(record, arrays, coarse, references=False)
    assert r.status == "missing_reference"
    assert r.coordinates.shape == (3, 2)


def test_zero_support_and_empty_grid():
    rows = (
        (5, (0, 10, 0, 10), (4, 4), (2.0, 2.0), set()),
        (6, (0, 0, 0, 0), (4, 4), (2.0, 2.0), set()),
    )
    record, arrays, coarse = build(rows)
    r = run(record, arrays, coarse)
    assert r.coordinates.shape == (0, 2) and r.encoding is not None
    assert r.metadata["support_block_count"] == 0
    e = run(record, arrays, coarse, obs(row=1, slice_=6))
    assert e.coordinates.shape == (0, 2)
    assert e.metadata["scope_address"]["grid_shape"] == [0, 0]


@pytest.mark.parametrize(
    "name,value,code",
    [
        (
            "windows_rc",
            np.array([[0, 10, 0, 10], [-2, 6, 3, 9]], np.int32),
            "window_invalid",
        ),
        (
            "windows_rc",
            np.array([[0, 10, 0, 10], [7, 6, 3, 9]], np.int32),
            "window_invalid",
        ),
        ("windows_rc", np.array([[0.0, 10, 0, 10], [2, 6, 3, 9]]), "window_invalid"),
        ("block_px", np.array([[4, 4], [0, 3]], np.int32), "block_px_invalid"),
        ("block_px", np.array([[4, 4], [2, 3]], np.float64), "block_px_invalid"),
        ("block_mm", np.array([[2.0, 2.0], [np.nan, 3.0]]), "block_mm_invalid"),
        ("block_mm", np.array([[2, 2], [2, 3]], np.int32), "block_mm_invalid"),
        ("slices", np.array([5.0, 7.0]), "slices_invalid"),
        ("slices", np.array([5, -7], np.int32), "slices_invalid"),
        ("shapes", np.array([[3, 3], [-2, 2]], np.int32), "shapes_invalid"),
        ("shapes", np.array([[3, 3], [3, 2]], np.int32), "grid_window_mismatch"),
        ("offsets", np.array([0, 9, 14], np.int64), "packed_plane_unavailable"),
        ("offsets", np.array([0, 13, 9], np.int64), "packed_plane_unavailable"),
    ],
)
def test_malformed_tables(name, value, code):
    record, arrays, coarse = build(**{name: value})
    row = 1 if name == "shapes" and code == "grid_window_mismatch" else 0
    assert (
        run(record, arrays, coarse, obs(row=row, slice_=7 if row else 5)).status == code
    )


@pytest.mark.parametrize("row", [True, 1.0, 1.5, -1, 2, np.int64(0)])
def test_bad_rows(row):
    record, arrays, coarse = build()
    r = run(record, arrays, coarse, obs(row=row))
    assert r.encoding is None and r.status in ("invalid_packed_row", "row_out_of_range")


@pytest.mark.parametrize("sl", [True, 5.0, [5, 6], -1])
def test_bad_slice_address(sl):
    record, arrays, coarse = build()
    o = obs()
    o["slices"] = sl if isinstance(sl, list) else [sl]
    assert run(record, arrays, coarse, o).status == "plane_address_required"


def test_slice_mismatch():
    record, arrays, coarse = build()
    assert run(record, arrays, coarse, obs(slice_=6)).status == "packed_slice_mismatch"


def test_digest_mismatch_and_cache():
    record, arrays, coarse = build()
    good = dict(arrays)
    arrays["c_median"] = arrays["c_median"] + 1.0
    assert run(record, arrays, coarse).status == "digest_mismatch"
    cache = {}
    assert run(record, good, coarse, verified_arrays=cache).encoding is not None
    assert ("c_median", record["arrays"]["c_median"]["digest"]) in cache
    # cache hit: the established (array_name, digest) semantics skip re-hashing
    assert run(record, arrays, coarse, verified_arrays=cache).encoding is not None


def test_same_owner_identity_checks():
    record, arrays, coarse = build()
    assert (
        run(record, arrays, coarse, obs(artifact="other")).status
        == "source_artifact_mismatch"
    )
    assert (
        run(record, arrays, coarse, obs(series_uid="V")).status
        == "source_series_mismatch"
    )
    assert (
        run(record, arrays, coarse, obs(view=["Axial", "1", "0"])).status
        == "source_view_mismatch"
    )
    assert run(record, arrays, coarse, obs(view=None)).status == "source_view_mismatch"


def fibula(prefix="a4_fibula_coarse_T"):
    record, arrays, coarse = build(prefix=prefix)
    record["series_uid"] = "OWN"
    record["view"] = ["Sagittal", "0", "0"]
    record["fibula_key_planes"] = {
        "T": {"orientation": "axial", "arrays_prefix": prefix, "slices_read": [5, 7]}
    }
    ev = CoarseTargetEvidence("S/A-fibula.npz.xz", "OWN", "T", tuple(VIEW))
    coarse = CoarseBlockLayout(
        coarse.offsets,
        coarse.shapes,
        coarse.slices,
        coarse.windows_rc,
        coarse.block_px,
        coarse.block_mm,
        coarse.packed_arrays,
        count_meaning="coarse_blocks",
        target_evidence=ev,
    )
    o = obs(prefix=prefix, series_uid="T", count=3)
    return record, arrays, coarse, o, prefix


def test_fibula_target_holder_ok_and_checks():
    record, arrays, coarse, o, p = fibula()
    r = run(record, arrays, coarse, o, bind(p))
    assert (
        r.encoding is not None
        and r.metadata["scope_address"]["target_series_uid"] == "T"
    )
    assert r.metadata["lineage"]["owner_series_uid"] == "OWN"
    assert (
        run(record, arrays, coarse, {**o, "series_uid": "OWN"}, bind(p)).status
        == "target_series_mismatch"
    )
    assert (
        run(
            record, arrays, coarse, {**o, "view": ["Sagittal", "0", "0"]}, bind(p)
        ).status
        == "target_view_mismatch"
    )
    assert (
        run(record, arrays, coarse, {**o, "artifact": "x"}, bind(p)).status
        == "owner_artifact_mismatch"
    )
    bad = dict(record)
    bad["artifact"] = "x"
    assert run(bad, arrays, coarse, o, bind(p)).status == "owner_artifact_mismatch"
    bad = {
        **record,
        "fibula_key_planes": {
            "T": {"orientation": "axial", "arrays_prefix": "zzz", "slices_read": [5, 7]}
        },
    }
    assert run(bad, arrays, coarse, o, bind(p)).status == "arrays_prefix_mismatch"
    bad = {
        **record,
        "fibula_key_planes": {
            "T": {"orientation": "axial", "arrays_prefix": p, "slices_read": [5, 9]}
        },
    }
    assert (
        run(
            bad, arrays, coarse, {**o, "row": 1, "slices": [7], "count": 1}, bind(p)
        ).status
        == "target_slice_mismatch"
    )
    bad = {**record, "fibula_key_planes": {}}
    assert run(bad, arrays, coarse, o, bind(p)).status == "target_evidence_missing"
    bad = {**record, "series_uid": "OTHER"}
    assert run(bad, arrays, coarse, o, bind(p)).status == "invalid_owner_identity"


def test_frame_absent_or_incomplete_still_valid():
    record, arrays, coarse = build()
    assert (
        run(record, arrays, coarse).metadata["geometry_status"] == "frame_not_declared"
    )
    origin = np.zeros((2, 3))
    arrays["c_origin"] = origin
    record["arrays"]["c_origin"] = {"digest": digest(origin)}
    c2 = CoarseBlockLayout(
        coarse.offsets,
        coarse.shapes,
        coarse.slices,
        coarse.windows_rc,
        coarse.block_px,
        coarse.block_mm,
        coarse.packed_arrays,
        frame_arrays={"origin_lps": "c_origin", "basis_lps": "c_missing"},
    )
    r = run(record, arrays, c2)
    assert (
        r.encoding is not None and r.metadata["geometry_status"] == "frame_incomplete"
    )
    assert r.metadata["packed_frame"] == {"origin_lps": [0.0, 0.0, 0.0]}
    assert "basis_lps" in r.metadata["frame_problems"]


def test_count_interpreted_only_when_declared():
    record, arrays, coarse = build()

    def with_meaning(m):
        return CoarseBlockLayout(
            coarse.offsets,
            coarse.shapes,
            coarse.slices,
            coarse.windows_rc,
            coarse.block_px,
            coarse.block_mm,
            coarse.packed_arrays,
            count_meaning=m,
        )

    assert run(record, arrays, with_meaning("coarse_blocks"), obs(count=3)).metadata[
        "count_interpreted_as_blocks"
    ]
    assert (
        run(record, arrays, with_meaning("coarse_blocks"), obs(count=4)).status
        == "support_count_mismatch"
    )
    assert (
        run(record, arrays, with_meaning("coarse_blocks"), obs(count=True)).status
        == "invalid_support_count"
    )
    assert run(record, arrays, with_meaning(None), obs(count=999)).encoding is not None
    assert (
        run(record, arrays, with_meaning("native_pixels"), obs(count=999)).encoding
        is not None
    )
    assert (
        run(record, arrays, with_meaning("coarse_blocks"), obs(count=None)).encoding
        is not None
    )


def test_no_false_native_or_lps_addresses():
    record, arrays, coarse = build()
    r = run(record, arrays, coarse)
    assert r.address_kind == "coarse_grid_rc"
    assert not hasattr(r, "points_rc") and not hasattr(r, "points_lps")
    for forbidden in ("points_rc", "points_lps", "plane_frame", "native_shape_rc"):
        assert forbidden not in r.metadata
    assert "support_array" not in r.metadata["scope_address"]


def test_primitive_direct():
    _record, arrays, _coarse = build()
    g = coarse_row_geometry(
        arrays["c_shapes"],
        arrays["c_slices"],
        arrays["c_windows_rc"],
        arrays["c_block_px"],
        arrays["c_block_mm"],
        0,
    )
    assert g.grid_shape == (3, 3)
    _code, b = block_native_bounds(g, np.array([[2, 0]], np.int64))
    assert b.tolist() == [[8, 10, 0, 4]]
    assert block_native_bounds(g, np.array([[3, 0]]))[0] == "coordinate_outside_grid"
    assert block_native_bounds(g, np.array([[True, False]]))[0] == "coordinates_invalid"
    assert (
        block_native_bounds(g, np.array([[2**63, 0]], dtype=np.uint64))[0]
        == "coordinates_invalid"
    )
    assert support_block_coordinates(np.zeros((0, 0), bool))[1].shape == (0, 2)
    assert support_block_coordinates(np.zeros((2, 2), int))[0] == "mask_invalid"
