import numpy as np

from knee.encoding.spatial import (
    batch_native_lps_readings,
    batch_native_rc_readings,
    coordinate_status_name,
    joint_status_name,
    native_lps_reading,
    native_rc_reading,
    prepare_spatial_context,
)


def study_map(
    *,
    point=(10.0, 20.0, 30.0),
    precision=(0.5, 1.0, 2.0),
    side="R",
    scale=100.0,
    status="complete",
):
    return {
        "schema": "study_map/v1",
        "knee": side,
        "scale": {"mm": scale, "source": "measured-femur-span", "code": "given"},
        "objects": {
            "femur": {
                "status": status,
                "point_lps": point,
                "precision_mm": precision,
                "key_planes": {"sagittal": {"outcome": "selected", "slice": 4}},
            }
        },
    }


def test_oblique_native_frame_converts_rc_and_retains_address():
    ctx = prepare_spatial_context(study_map(), "femur")
    # The row basis is tilted into superior LPS; the column basis points in -x.
    frame = {
        "origin_lps": [10.0, 20.0, 30.0],
        "basis_lps": [[0.0, -2.0], [3.0, 0.0], [4.0, 0.0]],
    }
    reading = native_rc_reading(
        ctx,
        [2.0, 1.0],
        frame=frame,
        view="sagittal",
        slice_index=4,
        row=1,
        address={"series_uid": "series-a", "support": "packed-row-1"},
        provenance={"source": "native-measurement"},
    )
    assert reading.point_lps == (8.0, 26.0, 38.0)
    assert reading.relative_lps_mm == (-2.0, 6.0, 8.0)
    assert reading.relative_mps_mm == (-2.0, 6.0, 8.0)
    assert reading.axis_codes == ("below", "above", "above")
    assert reading.joint_code == 0 * 9 + 2 * 3 + 2
    assert reading.normalized_mps == (-0.02, 0.06, 0.08)
    assert reading.address["series_uid"] == "series-a"
    assert reading.provenance["source"] == "native-measurement"
    assert reading.provenance["keyplanes"]["sagittal"]["slice"] == 4


def test_lps_trace_uses_canonical_side_sign_and_exact_precision_boundaries():
    right = prepare_spatial_context(study_map(side="R"), "femur")
    left = prepare_spatial_context(study_map(side="L"), "femur")
    point = [10.5, 19.0, 32.0]
    rr = native_lps_reading(
        right, point, view="axial", slice_index=8, provenance={"frame": "patient-LPS"}
    )
    lr = native_lps_reading(
        left, point, view="axial", slice_index=8, provenance={"frame": "patient-LPS"}
    )
    assert rr.coordinate == tuple(point)
    assert rr.point_lps == tuple(point)
    assert rr.relative_mps_mm == (0.5, -1.0, 2.0)
    assert lr.relative_mps_mm == (-0.5, -1.0, 2.0)
    assert rr.axis_codes == ("within", "within", "within")
    assert rr.joint_code == 13
    assert rr.provenance["frame"] == "patient-LPS"


def test_missing_map_fields_silence_facets_without_dropping_point():
    missing_side = prepare_spatial_context(study_map(side=None), "femur")
    reading = native_lps_reading(missing_side, [11.0, 22.0, 33.0], view="coronal")
    assert reading.point_lps == (11.0, 22.0, 33.0)
    assert reading.relative_lps_mm == (1.0, 2.0, 3.0)
    assert reading.relative_mps_mm == (None, 2.0, 3.0)
    assert reading.axis_codes == ("side_unavailable", "above", "above")
    assert reading.joint_code is None
    assert reading.joint_code_status == "side_unavailable"

    unknown_scale = prepare_spatial_context(study_map(scale=None), "femur")
    reading = native_lps_reading(unknown_scale, [11.0, 22.0, 33.0], view="coronal")
    assert reading.relative_mps_mm == (1.0, 2.0, 3.0)
    assert reading.normalized_mps == (None, None, None)
    assert reading.provenance["scale_code"] == "scale_unavailable"
    assert reading.provenance["scale_record_code"] == "given"


def test_unknown_precision_still_retains_coordinates_and_normalized_delta():
    ctx = prepare_spatial_context(study_map(precision=None, scale=50.0), "femur")
    reading = native_lps_reading(ctx, [12.0, 23.0, 34.0], view="coronal")
    assert reading.point_lps == (12.0, 23.0, 34.0)
    assert reading.relative_lps_mm == (2.0, 3.0, 4.0)
    assert reading.relative_mps_mm == (2.0, 3.0, 4.0)
    assert reading.normalized_mps == (0.04, 0.06, 0.08)
    assert reading.axis_codes == ("precision_unavailable",) * 3
    assert reading.joint_code is None
    assert reading.joint_code_status == "precision_unavailable"


def test_native_rc_without_or_with_malformed_frame_is_named_unknown():
    ctx = prepare_spatial_context(study_map(), "femur")
    missing = native_rc_reading(ctx, [1.0, 2.0], frame=None, view="axial")
    malformed = native_rc_reading(
        ctx,
        [1.0, 2.0],
        frame={"origin_lps": [0, 0, 0], "basis_lps": np.eye(3)},
        view="axial",
    )
    assert missing.coordinate_code == "frame_unavailable"
    assert missing.point_lps is None and missing.joint_code is None
    assert malformed.coordinate_code == "malformed_frame"
    assert malformed.point_lps is None


def test_incomplete_reference_or_bad_scale_never_fabricates_one():
    partial = prepare_spatial_context(study_map(status="partial", point=None), "femur")
    reading = native_lps_reading(partial, [1, 2, 3], view="sagittal")
    assert reading.point_lps == (1.0, 2.0, 3.0)
    assert reading.relative_lps_mm is None
    assert reading.joint_code_status == "reference_unavailable"

    for scale in (0, -1, float("inf"), float("nan")):
        ctx = prepare_spatial_context(study_map(scale=scale), "femur")
        out = native_lps_reading(ctx, [10, 20, 30], view="axial")
        assert out.normalized_mps == (None, None, None)


def test_invalid_point_is_retained_as_raw_when_finite_but_refused_when_not():
    ctx = prepare_spatial_context(study_map(), "femur")
    bad = native_lps_reading(ctx, [1, 2], view="axial", address={"id": 7})
    assert bad.coordinate == (1.0, 2.0)
    assert bad.coordinate_code == "invalid_lps_shape"
    assert bad.point_lps is None
    assert bad.address == {"id": 7}
    nonfinite = native_lps_reading(ctx, [1, float("nan"), 3], view="axial")
    assert nonfinite.coordinate is None
    assert nonfinite.coordinate_code == "nonfinite_coordinate"


def test_all_joint_direction_codes_are_unique_base3_combinations():
    ctx = prepare_spatial_context(
        study_map(point=(0, 0, 0), precision=(1, 1, 1), scale=1), "femur"
    )
    seen = set()
    for x in (-2, 0, 2):
        for y in (-2, 0, 2):
            for z in (-2, 0, 2):
                reading = native_lps_reading(ctx, [x, y, z], view="axial")
                expected_digits = tuple((n + 2) // 2 for n in (x, y, z))
                expected_code = (
                    expected_digits[0] * 9 + expected_digits[1] * 3 + expected_digits[2]
                )
                assert reading.joint_code == expected_code
                seen.add(reading.joint_code)
    assert seen == set(range(27))


def test_malformed_or_missing_map_object_stays_named_and_point_survives():
    for record, expected in (
        ({"schema": "other"}, "invalid_map"),
        ({"schema": "study_map/v1", "objects": {}}, "object_not_in_map"),
        (
            {"schema": "study_map/v1", "objects": {"femur": None}},
            "malformed_object_record",
        ),
    ):
        ctx = prepare_spatial_context(record, "femur")
        reading = native_lps_reading(ctx, [4, 5, 6], view="coronal")
        assert reading.point_lps == (4.0, 5.0, 6.0)
        assert reading.relative_lps_mm is None
        assert reading.joint_code is None
        assert reading.joint_code_status == expected


def test_batch_lps_matches_scalar_codes_and_values():
    ctx = prepare_spatial_context(study_map(), "femur")
    coords = np.array(
        [[10.5, 19.0, 28.0], [9.0, 21.0, 32.1], [np.nan, 0.0, 0.0]],
        dtype=np.float64,
    )
    batch = batch_native_lps_readings(ctx, coords)
    scalar = [native_lps_reading(ctx, row, view="axial") for row in coords]
    assert batch.input_code == "ok"
    for i, reading in enumerate(scalar):
        if reading.point_lps is None:
            assert (
                coordinate_status_name(batch.coordinate_codes[i])
                == reading.coordinate_code
            )
            assert np.isnan(batch.point_lps[i]).all()
            assert batch.joint_code[i] == -1
        else:
            np.testing.assert_allclose(batch.point_lps[i], reading.point_lps)
            np.testing.assert_allclose(
                batch.relative_lps_mm[i], reading.relative_lps_mm
            )
            np.testing.assert_allclose(
                batch.relative_mps_mm[i], reading.relative_mps_mm
            )
            np.testing.assert_allclose(batch.normalized_mps[i], reading.normalized_mps)
            assert tuple(batch.axis_digits[i]) == tuple(
                {"below": 0, "within": 1, "above": 2}[code]
                for code in reading.axis_codes
            )
            assert batch.joint_code[i] == reading.joint_code


def test_batch_rc_uses_distinct_per_row_oblique_frames_and_names_bad_rows():
    ctx = prepare_spatial_context(study_map(), "femur")
    coords = np.array([[1.0, 2.0], [1.0, 2.0], [1.0, 2.0]])
    origins = np.array([[10.0, 20.0, 30.0], [2.0, 3.0, 4.0], [0.0, 0.0, 0.0]])
    bases = np.array(
        [
            [[0.0, -2.0], [3.0, 0.0], [4.0, 0.0]],
            [[1.0, 0.0], [0.0, 1.0], [0.0, 1.0]],
            [[1.0, 0.0], [2.0, 0.0], [3.0, 0.0]],
        ]
    )
    batch = batch_native_rc_readings(ctx, coords, origins_lps=origins, bases_lps=bases)
    assert [coordinate_status_name(c) for c in batch.coordinate_codes] == [
        "ok",
        "ok",
        "malformed_frame",
    ]
    np.testing.assert_allclose(batch.point_lps[0], [6.0, 23.0, 34.0])
    np.testing.assert_allclose(batch.point_lps[1], [3.0, 5.0, 6.0])
    assert np.isnan(batch.point_lps[2]).all()
    scalar = native_rc_reading(
        ctx,
        coords[0],
        frame={"origin_lps": origins[0], "basis_lps": bases[0]},
        view="sagittal",
    )
    np.testing.assert_allclose(batch.point_lps[0], scalar.point_lps)
    assert batch.joint_code[0] == scalar.joint_code


def test_batch_unknown_side_and_precision_silence_only_affected_facets():
    no_side = prepare_spatial_context(study_map(side=None), "femur")
    batch = batch_native_lps_readings(no_side, np.array([[11, 22, 33]], dtype=np.int16))
    assert np.isnan(batch.relative_mps_mm[0, 0])
    np.testing.assert_allclose(batch.relative_mps_mm[0, 1:], [2, 3])
    assert tuple(batch.axis_digits[0]) == (-1, 2, 2)
    assert batch.joint_code[0] == -1
    assert joint_status_name(batch.joint_codes[0]) == "side_unavailable"

    no_precision = prepare_spatial_context(study_map(precision=None), "femur")
    batch = batch_native_lps_readings(
        no_precision, np.array([[11, 22, 33]], dtype=np.int16)
    )
    np.testing.assert_allclose(batch.relative_mps_mm[0], [1, 2, 3])
    assert tuple(batch.axis_digits[0]) == (-1, -1, -1)
    assert joint_status_name(batch.joint_codes[0]) == "precision_unavailable"


def test_boolean_coordinates_and_scale_are_not_measurements():
    ctx = prepare_spatial_context(study_map(), "femur")
    assert (
        native_lps_reading(ctx, [True, False, True], view="axial").coordinate_code
        == "boolean_coordinate"
    )
    assert (
        native_rc_reading(ctx, [True, False], frame=None, view="axial").coordinate_code
        == "boolean_coordinate"
    )
    batch = batch_native_lps_readings(ctx, np.array([[True, False, True]]))
    assert batch.input_code == "invalid_coordinate_dtype"
    bad_scale = prepare_spatial_context(study_map(scale=True), "femur")
    reading = native_lps_reading(bad_scale, [11, 22, 33], view="axial")
    assert reading.normalized_mps == (None, None, None)


def test_batch_status_arrays_are_compact_and_read_only():
    ctx = prepare_spatial_context(study_map(), "femur")
    result = batch_native_lps_readings(ctx, np.array([[10, 20, 30]], dtype=np.int16))
    assert result.coordinate_codes.dtype == np.uint8
    assert result.joint_codes.dtype == np.uint8
    assert not result.point_lps.flags.writeable
    assert not result.axis_digits.flags.writeable
    assert coordinate_status_name(result.coordinate_codes[0]) == "ok"
    assert joint_status_name(result.joint_codes[0]) == "ok"
