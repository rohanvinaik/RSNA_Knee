# tests/test_encoding_spatial_batch_intent.py
"""Intent tests: scalar and batch spatial readings describe the same retained points.

Expected geometry is derived here from small explicit frames and plain Python
arithmetic. The reference precision is a geometric resolution interval, never a
healthy-tissue threshold. The public API has no crop parameter, so a clipped
window is expressed only through the retained frame origin.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from knee.encoding.spatial import (
    batch_native_lps_readings,
    batch_native_rc_readings,
    coordinate_status_name,
    joint_status_name,
    native_lps_reading,
    native_rc_reading,
    prepare_spatial_context,
)

try:
    from hypothesis import HealthCheck, assume, given, settings
    from hypothesis import strategies as st
except ImportError:  # pragma: no cover - property tests are skipped without it
    given = None

REF = (10.0, 20.0, 30.0)
PRECISION = (0.5, 1.0, 2.0)

# Native (row, col) -> LPS is origin + row * column0 + col * column1.
# Column0 = (0, 2, 2) and column1 = (3, 0, 4): anisotropic and oblique, rank 2.
FRAME = {
    "origin_lps": [5.0, -5.0, 10.0],
    "basis_lps": [[0.0, 3.0], [2.0, 0.0], [2.0, 4.0]],
}
RC_POINTS = [(0.0, 0.0), (2.0, 1.0), (0.0, 5.0), (10.0, 0.0)]
# Hand-derived: 5+3c, -5+2r, 10+2r+4c.
LPS_POINTS = [
    (5.0, -5.0, 10.0),
    (8.0, -1.0, 18.0),
    (20.0, -5.0, 30.0),
    (5.0, 15.0, 30.0),
]
# Hand-derived joint codes for PRECISION against REF.
JOINT_R = [0, 0, 19, 1]
JOINT_L = [18, 18, 1, 19]

DIGIT = {"below": 0, "within": 1, "above": 2}


def _map(*, point=REF, precision=PRECISION, side="R", scale=8.0, status="complete"):
    return {
        "schema": "study_map/v1",
        "knee": side,
        "scale": {"mm": scale, "source": "measured-femur-span", "code": "given"},
        "objects": {
            "femur": {
                "status": status,
                "point_lps": point,
                "precision_mm": precision,
                "key_planes": {"coronal": {"outcome": "selected", "slice": 7}},
            }
        },
    }


def _ctx(**kw):
    return prepare_spatial_context(_map(**kw), "femur")


def _expect(point, ref, side, precision, scale):
    """Independent plain-Python derivation of one point's facets."""
    rel = tuple(p - r for p, r in zip(point, ref, strict=True))
    x = {"R": rel[0], "L": -rel[0]}.get(side)
    mps = (x, rel[1], rel[2])
    tolerances = precision if precision is not None else (None, None, None)
    digits = []
    for value, tol in zip(mps, tolerances, strict=True):
        if value is None or tol is None:
            digits.append(None)
        else:
            digits.append(0 if value < -tol else 2 if value > tol else 1)
    norm = tuple(None if (v is None or scale is None) else v / scale for v in mps)
    joint = None if None in digits else digits[0] * 9 + digits[1] * 3 + digits[2]
    return {
        "point": tuple(point),
        "rel": rel,
        "mps": mps,
        "digits": tuple(digits),
        "norm": norm,
        "joint": joint,
    }


def _digits_from_codes(codes):
    return tuple(DIGIT.get(c) for c in codes)


def _assert_scalar(reading, exp):
    assert reading.point_lps == exp["point"]
    assert reading.relative_lps_mm == exp["rel"]
    assert reading.relative_mps_mm == exp["mps"]
    assert reading.normalized_mps == exp["norm"]
    assert _digits_from_codes(reading.axis_codes) == exp["digits"]
    assert reading.joint_code == exp["joint"]


def _nan(values):
    return [[np.nan if v is None else v for v in row] for row in values]


def _assert_batch(batch, exps):
    np.testing.assert_array_equal(batch.point_lps, [e["point"] for e in exps])
    np.testing.assert_array_equal(batch.relative_lps_mm, [e["rel"] for e in exps])
    np.testing.assert_array_equal(batch.relative_mps_mm, _nan(e["mps"] for e in exps))
    np.testing.assert_array_equal(batch.normalized_mps, _nan(e["norm"] for e in exps))
    np.testing.assert_array_equal(
        batch.axis_digits,
        [[-1 if d is None else d for d in e["digits"]] for e in exps],
    )
    np.testing.assert_array_equal(
        batch.joint_code, [-1 if e["joint"] is None else e["joint"] for e in exps]
    )


# --------------------------------------------------------------------------
# Hand-derived oblique/anisotropic native frames
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("side", "expected_joint"), [("R", JOINT_R), ("L", JOINT_L)])
def test_hand_derived_oblique_frame_points_and_codes_in_scalar_and_batch(
    side, expected_joint
):
    ctx = _ctx(side=side)
    batch = batch_native_rc_readings(ctx, np.array(RC_POINTS), frame=FRAME)
    np.testing.assert_array_equal(batch.point_lps, LPS_POINTS)
    assert batch.joint_code.tolist() == expected_joint
    for i, rc in enumerate(RC_POINTS):
        scalar = native_rc_reading(ctx, rc, frame=FRAME, view="sagittal")
        assert scalar.point_lps == LPS_POINTS[i]
        assert scalar.joint_code == expected_joint[i]


@pytest.mark.parametrize("side", ["R", "L", None])
@pytest.mark.parametrize("precision", [PRECISION, None])
@pytest.mark.parametrize("scale", [8.0, None])
def test_scalar_and_batch_rc_agree_with_independent_derivation(side, precision, scale):
    ctx = _ctx(side=side, precision=precision, scale=scale)
    exps = [_expect(p, REF, side, precision, scale) for p in LPS_POINTS]
    batch = batch_native_rc_readings(ctx, np.array(RC_POINTS), frame=FRAME)
    _assert_batch(batch, exps)
    for rc, exp in zip(RC_POINTS, exps, strict=True):
        _assert_scalar(native_rc_reading(ctx, rc, frame=FRAME, view="axial"), exp)
    # Scalar and batch also describe LPS inputs for those same physical points.
    lps_batch = batch_native_lps_readings(ctx, np.array(LPS_POINTS))
    _assert_batch(lps_batch, exps)
    for p, exp in zip(LPS_POINTS, exps, strict=True):
        _assert_scalar(native_lps_reading(ctx, p, view="axial"), exp)


def test_shared_frame_batch_equals_the_same_frame_given_per_row():
    ctx = _ctx()
    coords = np.array(RC_POINTS)
    shared = batch_native_rc_readings(ctx, coords, frame=FRAME)
    origins = np.broadcast_to(np.array(FRAME["origin_lps"]), (4, 3)).copy()
    bases = np.broadcast_to(np.array(FRAME["basis_lps"]), (4, 3, 2)).copy()
    per_row = batch_native_rc_readings(
        ctx, coords, origins_lps=origins, bases_lps=bases
    )
    for name in (
        "point_lps",
        "relative_lps_mm",
        "relative_mps_mm",
        "normalized_mps",
        "axis_digits",
        "joint_code",
        "coordinate_codes",
        "joint_codes",
    ):
        np.testing.assert_array_equal(getattr(shared, name), getattr(per_row, name))


def test_cropped_window_offset_via_origin_names_the_same_physical_point():
    # Crop starts at native (3, 2): shifted origin = origin + 3*col0 + 2*col1
    # = (5,-5,10) + (6,6,14) = (11, 1, 24). Native (5, 4) is local (2, 2).
    cropped = {
        "origin_lps": [11.0, 1.0, 24.0],
        "basis_lps": FRAME["basis_lps"],
    }
    ctx = _ctx()
    full = native_rc_reading(ctx, [5.0, 4.0], frame=FRAME, view="axial")
    local = native_rc_reading(ctx, [2.0, 2.0], frame=cropped, view="axial")
    assert full.point_lps == local.point_lps == (17.0, 5.0, 36.0)
    assert full.joint_code == local.joint_code
    batch = batch_native_rc_readings(ctx, np.array([[5.0, 4.0]]), frame=FRAME)
    cropped_batch = batch_native_rc_readings(ctx, np.array([[2.0, 2.0]]), frame=cropped)
    np.testing.assert_array_equal(batch.point_lps, [[17.0, 5.0, 36.0]])
    np.testing.assert_array_equal(batch.point_lps, cropped_batch.point_lps)
    np.testing.assert_array_equal(batch.relative_mps_mm, cropped_batch.relative_mps_mm)


def test_native_rc_and_lps_inputs_for_one_physical_point_differ_only_in_provenance():
    ctx = _ctx(side="L")
    rc = native_rc_reading(ctx, [2.0, 1.0], frame=FRAME, view="sagittal")
    lps = native_lps_reading(ctx, [8.0, -1.0, 18.0], view="sagittal")
    assert rc.coordinate == (2.0, 1.0) and lps.coordinate == (8.0, -1.0, 18.0)
    assert rc.coordinate_kind == "native_rc" and lps.coordinate_kind == "native_lps"
    for name in (
        "point_lps",
        "relative_lps_mm",
        "relative_mps_mm",
        "normalized_mps",
        "axis_codes",
        "joint_code",
        "joint_code_status",
    ):
        assert getattr(rc, name) == getattr(lps, name)
    b_rc = batch_native_rc_readings(ctx, np.array([[2.0, 1.0]]), frame=FRAME)
    b_lps = batch_native_lps_readings(ctx, np.array([[8.0, -1.0, 18.0]]))
    assert b_rc.coordinate_kind == "native_rc" and b_lps.coordinate_kind == "native_lps"
    np.testing.assert_array_equal(b_rc.point_lps, b_lps.point_lps)
    np.testing.assert_array_equal(b_rc.axis_digits, b_lps.axis_digits)
    np.testing.assert_array_equal(b_rc.joint_code, b_lps.joint_code)


def test_bad_rows_are_named_and_do_not_disturb_neighbouring_points():
    ctx = _ctx()
    coords = np.array([[2.0, 1.0], [np.nan, 0.0], [0.0, 5.0]])
    batch = batch_native_rc_readings(ctx, coords, frame=FRAME)
    assert [coordinate_status_name(c) for c in batch.coordinate_codes] == [
        "ok",
        "nonfinite_coordinate",
        "ok",
    ]
    np.testing.assert_array_equal(batch.point_lps[0], LPS_POINTS[1])
    np.testing.assert_array_equal(batch.point_lps[2], LPS_POINTS[2])
    assert np.isnan(batch.point_lps[1]).all()
    assert np.isnan(batch.relative_lps_mm[1]).all()
    assert batch.joint_code[1] == -1
    scalar = native_rc_reading(ctx, coords[1], frame=FRAME, view="axial")
    assert scalar.coordinate_code == "nonfinite_coordinate"
    assert scalar.joint_code is None
    assert (
        batch.joint_code[0]
        == native_rc_reading(ctx, coords[0], frame=FRAME, view="axial").joint_code
    )


# --------------------------------------------------------------------------
# Missing versus measured reference centre
# --------------------------------------------------------------------------


def test_measured_zero_centre_is_a_real_reference_not_a_missing_one():
    ctx = _ctx(point=(0.0, 0.0, 0.0), precision=(1.0, 1.0, 1.0), scale=10.0)
    assert ctx.point_lps == (0.0, 0.0, 0.0)
    assert ctx.code == "ok"
    reading = native_lps_reading(ctx, [0.0, 0.0, 0.0], view="axial")
    assert reading.relative_lps_mm == (0.0, 0.0, 0.0)
    assert reading.normalized_mps == (0.0, 0.0, 0.0)
    assert reading.axis_codes == ("within",) * 3
    assert reading.joint_code == 13
    batch = batch_native_lps_readings(ctx, np.zeros((1, 3)))
    np.testing.assert_array_equal(batch.relative_lps_mm, np.zeros((1, 3)))
    np.testing.assert_array_equal(batch.normalized_mps, np.zeros((1, 3)))
    assert batch.joint_code[0] == 13


@pytest.mark.parametrize(
    "bad_point", [None, (float("nan"), 0.0, 0.0), (True, False, True), (0.0, 0.0)]
)
def test_missing_centre_stays_unavailable_and_never_becomes_zero(bad_point):
    ctx = _ctx(point=bad_point)
    assert ctx.point_lps is None
    assert ctx.code == "reference_unavailable"
    reading = native_lps_reading(ctx, [0.0, 0.0, 0.0], view="axial")
    assert reading.point_lps == (0.0, 0.0, 0.0)  # the measurement itself survives
    assert reading.relative_lps_mm is None
    assert reading.relative_mps_mm is None
    assert reading.normalized_mps is None
    assert reading.axis_codes == ("reference_unavailable",) * 3
    assert reading.joint_code is None
    assert reading.joint_code_status == "reference_unavailable"
    batch = batch_native_lps_readings(ctx, np.zeros((1, 3)))
    np.testing.assert_array_equal(batch.point_lps, np.zeros((1, 3)))
    assert np.isnan(batch.relative_lps_mm).all()
    assert np.isnan(batch.normalized_mps).all()
    assert (batch.axis_digits == -1).all()
    assert joint_status_name(batch.joint_codes[0]) == "reference_unavailable"


def test_incomplete_map_status_with_a_point_does_not_supply_a_reference_in_either_form():
    ctx = _ctx(status="partial")
    assert ctx.point_lps == REF  # retained as written
    assert ctx.code == "reference_unavailable"
    reading = native_lps_reading(ctx, [12.0, 24.0, 38.0], view="axial")
    assert reading.relative_lps_mm is None and reading.normalized_mps is None
    assert reading.joint_code_status == "reference_unavailable"
    batch = batch_native_lps_readings(ctx, np.array([[12.0, 24.0, 38.0]]))
    np.testing.assert_array_equal(batch.point_lps, [[12.0, 24.0, 38.0]])
    assert np.isnan(batch.relative_lps_mm).all()
    assert batch.map_status == "partial"
    assert batch.reference_status == "reference_unavailable"
    assert joint_status_name(batch.joint_codes[0]) == "reference_unavailable"


# --------------------------------------------------------------------------
# Per-axis unavailability: side, precision, scale are independent
# --------------------------------------------------------------------------


def test_unknown_side_removes_only_the_medial_axis_in_scalar_and_batch():
    ctx = _ctx(side=None, precision=(1.0, 2.0, 3.0), scale=4.0)
    point = [12.0, 24.0, 38.0]  # relative LPS (2, 4, 8)
    reading = native_lps_reading(ctx, point, view="coronal")
    assert reading.relative_lps_mm == (2.0, 4.0, 8.0)
    assert reading.relative_mps_mm == (None, 4.0, 8.0)
    assert reading.normalized_mps == (None, 1.0, 2.0)
    assert reading.axis_codes == ("side_unavailable", "above", "above")
    assert reading.joint_code is None
    assert reading.joint_code_status == "side_unavailable"
    batch = batch_native_lps_readings(ctx, np.array([point]))
    np.testing.assert_array_equal(batch.relative_lps_mm, [[2.0, 4.0, 8.0]])
    np.testing.assert_array_equal(batch.relative_mps_mm, [[np.nan, 4.0, 8.0]])
    np.testing.assert_array_equal(batch.normalized_mps, [[np.nan, 1.0, 2.0]])
    assert batch.axis_digits[0].tolist() == [-1, 2, 2]
    assert batch.joint_code[0] == -1
    assert joint_status_name(batch.joint_codes[0]) == "side_unavailable"
    assert batch.side is None


@pytest.mark.parametrize("side", ["X", ""])
def test_unrecognised_knee_side_is_unknown_not_defaulted_to_a_side(side):
    ctx = _ctx(side=side)
    assert ctx.side is None
    reading = native_lps_reading(ctx, [12.0, 24.0, 38.0], view="axial")
    assert reading.relative_mps_mm[0] is None
    assert reading.relative_mps_mm[1:] == (4.0, 8.0)


@pytest.mark.parametrize(
    "precision",
    [(1.0, 0.0, 1.0), (1.0, -1.0, 1.0), (1.0, float("nan"), 1.0), (True, True, True)],
)
def test_unusable_precision_is_unavailable_whole_and_not_replaced_by_a_tolerance(
    precision,
):
    ctx = _ctx(precision=precision)
    assert ctx.precision_mm is None
    reading = native_lps_reading(ctx, [12.0, 24.0, 38.0], view="axial")
    assert reading.relative_mps_mm == (2.0, 4.0, 8.0)
    assert reading.axis_codes == ("precision_unavailable",) * 3
    assert reading.joint_code is None
    assert reading.joint_code_status == "precision_unavailable"
    batch = batch_native_lps_readings(ctx, np.array([[12.0, 24.0, 38.0]]))
    np.testing.assert_array_equal(batch.relative_mps_mm, [[2.0, 4.0, 8.0]])
    assert (batch.axis_digits == -1).all()
    assert batch.precision_status == "precision_unavailable"
    assert joint_status_name(batch.joint_codes[0]) == "precision_unavailable"


def test_unknown_scale_leaves_directions_and_distances_intact():
    ctx = _ctx(scale=None)
    reading = native_lps_reading(ctx, [12.0, 24.0, 38.0], view="axial")
    assert reading.relative_mps_mm == (2.0, 4.0, 8.0)
    assert reading.axis_codes == ("above", "above", "above")
    assert reading.joint_code == 26
    assert reading.normalized_mps == (None, None, None)
    batch = batch_native_lps_readings(ctx, np.array([[12.0, 24.0, 38.0]]))
    assert batch.scale_mm is None
    assert np.isnan(batch.normalized_mps).all()
    assert batch.joint_code[0] == 26


# --------------------------------------------------------------------------
# Scale: measured, continuous, never a fabricated 1
# --------------------------------------------------------------------------


def test_a_measured_scale_of_one_is_different_from_an_unknown_scale():
    point = [12.0, 24.0, 38.0]
    measured = _ctx(scale=1.0)
    unknown = _ctx(scale=None)
    assert native_lps_reading(measured, point, view="axial").normalized_mps == (
        2.0,
        4.0,
        8.0,
    )
    assert native_lps_reading(unknown, point, view="axial").normalized_mps == (
        None,
        None,
        None,
    )
    assert batch_native_lps_readings(measured, np.array([point])).scale_mm == 1.0
    np.testing.assert_array_equal(
        batch_native_lps_readings(measured, np.array([point])).normalized_mps,
        [[2.0, 4.0, 8.0]],
    )
    assert np.isnan(
        batch_native_lps_readings(unknown, np.array([point])).normalized_mps
    ).all()


def test_normalization_is_continuous_and_unclipped():
    ctx = _ctx(scale=8.0)
    point = [-390.0, 23.0, 30.0]  # relative (-400, 3, 0)
    reading = native_lps_reading(ctx, point, view="axial")
    assert reading.normalized_mps == (-50.0, 0.375, 0.0)
    assert reading.axis_codes == ("below", "above", "within")
    batch = batch_native_lps_readings(ctx, np.array([point]))
    np.testing.assert_array_equal(batch.normalized_mps, [[-50.0, 0.375, 0.0]])
    assert batch.scale_source == "measured-femur-span"


@pytest.mark.parametrize("scale", [0, -3.0, float("inf"), float("nan"), True, None])
def test_unusable_scale_value_gives_no_normalized_number_in_either_form(scale):
    ctx = _ctx(scale=scale)
    assert ctx.scale_mm is None
    reading = native_lps_reading(ctx, [12.0, 24.0, 38.0], view="axial")
    assert reading.normalized_mps == (None, None, None)
    batch = batch_native_lps_readings(ctx, np.array([[12.0, 24.0, 38.0]]))
    assert batch.scale_mm is None
    assert np.isnan(batch.normalized_mps).all()


# --------------------------------------------------------------------------
# Precision is geometric resolution, not a healthy threshold
# --------------------------------------------------------------------------


def test_precision_changes_only_direction_states_and_scale_changes_only_normalization():
    point = [12.0, 24.0, 38.0]  # relative (2, 4, 8)
    tight = _ctx(precision=(0.1, 0.1, 0.1), scale=8.0)
    wide = _ctx(precision=(50.0, 50.0, 50.0), scale=8.0)
    half = _ctx(precision=(0.1, 0.1, 0.1), scale=16.0)
    a = native_lps_reading(tight, point, view="axial")
    b = native_lps_reading(wide, point, view="axial")
    c = native_lps_reading(half, point, view="axial")
    assert a.joint_code == 26 and b.joint_code == 13
    assert a.relative_mps_mm == b.relative_mps_mm == (2.0, 4.0, 8.0)
    assert a.normalized_mps == b.normalized_mps == (0.25, 0.5, 1.0)
    assert c.normalized_mps == (0.125, 0.25, 0.5)
    assert c.axis_codes == a.axis_codes
    batch_a = batch_native_lps_readings(tight, np.array([point]))
    batch_b = batch_native_lps_readings(wide, np.array([point]))
    np.testing.assert_array_equal(batch_a.normalized_mps, batch_b.normalized_mps)
    assert batch_a.joint_code[0] == 26 and batch_b.joint_code[0] == 13


def test_readings_carry_geometry_vocabulary_not_health_vocabulary():
    reading = native_lps_reading(_ctx(), [12.0, 24.0, 38.0], view="axial")
    batch = batch_native_lps_readings(_ctx(), np.array([[12.0, 24.0, 38.0]]))
    for obj in (reading, batch):
        names = " ".join(f.name for f in dataclasses.fields(obj)).lower()
        assert "health" not in names and "normal_" not in names
    assert set(reading.axis_codes) <= {"below", "within", "above"}


# --------------------------------------------------------------------------
# Bounded Hypothesis properties
# --------------------------------------------------------------------------

if given is not None:
    _ints30 = st.integers(-30, 30)
    _vec = st.tuples(_ints30, _ints30, _ints30)
    _row = st.tuples(st.integers(-4, 4), st.integers(-4, 4))
    _basis = st.tuples(_row, _row, _row)
    _rc = st.tuples(st.integers(-15, 15), st.integers(-15, 15))
    _precision = st.tuples(*[st.integers(1, 6)] * 3)
    _SETTINGS = settings(
        max_examples=60,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )

    def _full_rank(basis):
        c0 = (basis[0][0], basis[1][0], basis[2][0])
        c1 = (basis[0][1], basis[1][1], basis[2][1])
        cross = (
            c0[1] * c1[2] - c0[2] * c1[1],
            c0[2] * c1[0] - c0[0] * c1[2],
            c0[0] * c1[1] - c0[1] * c1[0],
        )
        return any(cross)

    @_SETTINGS
    @given(
        ref=_vec,
        origin=_vec,
        basis=_basis,
        rcs=st.lists(_rc, min_size=1, max_size=6),
        side=st.sampled_from(["R", "L", None]),
        precision=st.one_of(st.none(), _precision),
        scale=st.one_of(st.none(), st.integers(1, 50)),
    )
    def test_property_scalar_and_batch_rc_match_independent_geometry(
        ref, origin, basis, rcs, side, precision, scale
    ):
        assume(_full_rank(basis))
        prec = None if precision is None else tuple(float(p) for p in precision)
        scl = None if scale is None else float(scale)
        ref_f = tuple(float(v) for v in ref)
        ctx = _ctx(point=ref_f, precision=prec, side=side, scale=scl)
        frame = {
            "origin_lps": [float(v) for v in origin],
            "basis_lps": [[float(a), float(b)] for a, b in basis],
        }
        lps = [
            tuple(
                float(origin[i] + basis[i][0] * r + basis[i][1] * c) for i in range(3)
            )
            for r, c in rcs
        ]
        exps = [_expect(p, ref_f, side, prec, scl) for p in lps]
        coords = np.array(rcs, dtype=np.float64)
        _assert_batch(batch_native_rc_readings(ctx, coords, frame=frame), exps)
        origins = np.broadcast_to(np.array(frame["origin_lps"]), (len(rcs), 3)).copy()
        bases = np.broadcast_to(np.array(frame["basis_lps"]), (len(rcs), 3, 2)).copy()
        _assert_batch(
            batch_native_rc_readings(ctx, coords, origins_lps=origins, bases_lps=bases),
            exps,
        )
        for rc, exp in zip(rcs, exps, strict=True):
            _assert_scalar(
                native_rc_reading(
                    ctx, [float(rc[0]), float(rc[1])], frame=frame, view="axial"
                ),
                exp,
            )

    @_SETTINGS
    @given(
        ref=_vec,
        points=st.lists(_vec, min_size=1, max_size=6),
        precision=_precision,
        scale=st.integers(1, 50),
    )
    def test_property_knee_side_mirrors_only_the_medial_axis(
        ref, points, precision, scale
    ):
        prec = tuple(float(p) for p in precision)
        pts = np.array(points, dtype=np.float64)
        kw = {
            "point": tuple(float(v) for v in ref),
            "precision": prec,
            "scale": float(scale),
        }
        right = batch_native_lps_readings(_ctx(side="R", **kw), pts)
        left = batch_native_lps_readings(_ctx(side="L", **kw), pts)
        np.testing.assert_array_equal(right.relative_lps_mm, left.relative_lps_mm)
        np.testing.assert_array_equal(
            right.relative_mps_mm[:, 0], -left.relative_mps_mm[:, 0]
        )
        np.testing.assert_array_equal(
            right.relative_mps_mm[:, 1:], left.relative_mps_mm[:, 1:]
        )
        np.testing.assert_array_equal(
            right.axis_digits[:, 0], 2 - left.axis_digits[:, 0]
        )
        np.testing.assert_array_equal(right.axis_digits[:, 1:], left.axis_digits[:, 1:])

    @_SETTINGS
    @given(
        ref=_vec,
        points=st.lists(_vec, min_size=1, max_size=6),
        side=st.sampled_from(["R", "L"]),
        prec_a=_precision,
        prec_b=_precision,
        scale_a=st.integers(1, 50),
        scale_b=st.integers(1, 50),
    )
    def test_property_precision_and_scale_do_not_leak_into_each_other(
        ref, points, side, prec_a, prec_b, scale_a, scale_b
    ):
        pts = np.array(points, dtype=np.float64)
        base = {"point": tuple(float(v) for v in ref), "side": side}

        def run(prec, scale):
            return batch_native_lps_readings(
                _ctx(
                    precision=tuple(float(p) for p in prec),
                    scale=float(scale),
                    **base,
                ),
                pts,
            )

        first = run(prec_a, scale_a)
        other_precision = run(prec_b, scale_a)
        other_scale = run(prec_a, scale_b)
        np.testing.assert_array_equal(
            first.relative_mps_mm, other_precision.relative_mps_mm
        )
        np.testing.assert_array_equal(
            first.normalized_mps, other_precision.normalized_mps
        )
        np.testing.assert_array_equal(first.axis_digits, other_scale.axis_digits)
        np.testing.assert_array_equal(first.joint_code, other_scale.joint_code)

    @_SETTINGS
    @given(
        ref=_vec,
        shift=_vec,
        points=st.lists(_vec, min_size=1, max_size=6),
        side=st.sampled_from(["R", "L", None]),
        precision=_precision,
    )
    def test_property_relative_readings_are_invariant_to_common_translation(
        ref, shift, points, side, precision
    ):
        prec = tuple(float(p) for p in precision)
        pts = np.array(points, dtype=np.float64)
        t = np.array(shift, dtype=np.float64)
        a = batch_native_lps_readings(
            _ctx(point=tuple(float(v) for v in ref), precision=prec, side=side), pts
        )
        b = batch_native_lps_readings(
            _ctx(
                point=tuple(float(v) for v in (np.array(ref) + t)),
                precision=prec,
                side=side,
            ),
            pts + t,
        )
        np.testing.assert_array_equal(a.relative_lps_mm, b.relative_lps_mm)
        np.testing.assert_array_equal(a.axis_digits, b.axis_digits)
        np.testing.assert_array_equal(a.joint_code, b.joint_code)

else:  # pragma: no cover

    def test_hypothesis_properties_require_hypothesis():
        pytest.skip("hypothesis is not installed")
