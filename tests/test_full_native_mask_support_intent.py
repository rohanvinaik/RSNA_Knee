"""Positive and negative intent for native-mask address eligibility."""

from scripts.run_interiors import _ordinary_full_native_mask_support


def test_direct_positive_full_plane_boolean_and_label_supports() -> None:
    assert _ordinary_full_native_mask_support(
        "a2_femur", ((64, 80), "b"), (64, 80), None
    )
    assert _ordinary_full_native_mask_support(
        "a1_objects", ((64, 80), "i"), (64, 80), None
    )


def test_direct_positive_bounded_full_plane_row() -> None:
    assert _ordinary_full_native_mask_support(
        "a3_femur_plane_region", ((3, 64, 80), "u"), (64, 80), 2
    )


def test_direct_negative_address_families_and_crop_shapes() -> None:
    for name in (
        "a3_coarse_femur",
        "a3_packed_values",
        "a3_posterior_trace_points_lps",
        "a3_femur_profile_area",
        "a4_sample_context",
        "a2_crop_femur",
    ):
        assert not _ordinary_full_native_mask_support(
            name, ((64, 80), "b"), (64, 80), None
        )
    assert not _ordinary_full_native_mask_support(
        "a2_femur", ((32, 40), "b"), (64, 80), None
    )


def test_direct_negative_dtype_shape_and_missing_row() -> None:
    assert not _ordinary_full_native_mask_support(
        "a2_measurement", ((64, 80), "f"), (64, 80), None
    )
    assert not _ordinary_full_native_mask_support(
        "a2_measurement", ((64, 80), "b"), (64, 80), 0
    )
    assert not _ordinary_full_native_mask_support(
        "a2_measurement", ((3, 64, 80), "b"), (64, 80), None
    )
    assert not _ordinary_full_native_mask_support(
        "a2_measurement", ((63, 80), "b"), (64, 80), None
    )
