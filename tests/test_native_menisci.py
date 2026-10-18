import numpy as np

from knee.collapse.menisci import meniscus_local_body
from knee.collapse.physical import PlaneFrame


def _frame(spacing_rc=(1.0, 1.0)):
    return PlaneFrame.from_dicom(
        np.zeros(3), np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0]), spacing_rc
    )


def _body_scene():
    raw = np.full((32, 40), 10.0)
    raw[10:22, 14:27] = 2.0
    available = np.ones(raw.shape, dtype=bool)
    target = np.zeros(raw.shape, dtype=bool)
    target[16, 12] = True
    return raw, available, target


def test_local_body_selects_whole_opened_component_reached_by_source():
    raw, available, target = _body_scene()
    result = meniscus_local_body(raw, available, target, _frame())
    assert result["status"] == "identified"
    assert result["selection_status"] == "identified"
    assert result["selected_pixels"] > 1
    assert np.all(result["selected"] <= result["opened"])
    assert np.any(result["selected"] & ~target)
    assert np.any(result["selected"][:, 20:])
    assert result["selected_pixels"] == result["largest_contacted_pixels"]
    assert result["selected_touches_crop_edge"] is False


def test_local_body_keeps_equal_largest_contacted_components_unselected():
    raw = np.full((30, 40), 10.0)
    raw[8:20, 5:14] = 2.0
    raw[8:20, 18:27] = 2.0
    available = np.ones(raw.shape, dtype=bool)
    target = np.zeros(raw.shape, dtype=bool)
    target[13, 15:17] = True
    result = meniscus_local_body(raw, available, target, _frame())
    assert result["status"] == "tied_largest_components"
    assert result["selection_status"] == "tied_largest_components"
    assert len(result["largest_component_labels"]) == 2
    assert result["contacted_component_count"] == 2
    assert result["selected_pixels"] == 0
    assert not result["selected"].any()


def test_local_body_distinguishes_missing_source_from_measured_empty():
    raw = np.full((16, 20), 10.0)
    available = np.ones(raw.shape, dtype=bool)
    no_target = np.zeros(raw.shape, dtype=bool)
    missing = meniscus_local_body(raw, available, no_target, _frame())
    assert missing["status"] == "target_missing"

    target = no_target.copy()
    target[8, 10] = True
    empty = meniscus_local_body(raw, available, target, _frame())
    assert empty["status"] == "measured_empty"
    assert empty["selection_status"] == "measured_empty"
    assert empty["selected_pixels"] == 0
    assert empty["available_pixels"] == raw.size

    unavailable = available.copy()
    unavailable[target] = False
    refused = meniscus_local_body(raw, unavailable, target, _frame())
    assert refused["status"] == "target_unavailable"
    assert refused["available_target_pixels"] == 0


def test_local_body_unavailable_values_cannot_affect_partial_reading():
    raw, available, target = _body_scene()
    available[0, 0] = False
    changed = raw.copy()
    changed[0, 0] = -1e12
    first = meniscus_local_body(raw, available, target, _frame())
    second = meniscus_local_body(changed, available, target, _frame())
    assert first["status"] == second["status"] == "partial_reading"
    assert first["selection_status"] == second["selection_status"] == "identified"
    for key in (
        "depth_input",
        "enclosed_depth",
        "positive_enclosure",
        "opened",
        "labels",
        "distance_to_target",
        "contacted_components",
        "selected",
    ):
        np.testing.assert_array_equal(first[key], second[key])
    assert first["selected_pixels"] > 0
    assert first["selected_touches_crop_edge"] is False


def test_local_body_transpose_respects_physical_pixel_spacing():
    raw, available, target = _body_scene()
    target[:] = False
    target[16, 13] = True
    first = meniscus_local_body(raw, available, target, _frame((1.0, 2.0)))
    second = meniscus_local_body(raw.T, available.T, target.T, _frame((2.0, 1.0)))
    assert first["status"] == second["status"] == "identified"
    for key in (
        "depth_input",
        "enclosed_depth",
        "positive_enclosure",
        "opened",
        "labels",
        "distance_to_target",
        "contacted_components",
        "selected",
    ):
        np.testing.assert_allclose(first[key], second[key].T, equal_nan=True)
    assert first["selected_pixels"] == second["selected_pixels"]


def test_local_body_names_malformed_input_and_spacing():
    raw, available, target = _body_scene()
    assert (
        meniscus_local_body(raw[0], available, target, _frame())["status"]
        == "malformed_raw_shape"
    )
    assert (
        meniscus_local_body(raw, available.astype(np.uint8), target, _frame())["status"]
        == "malformed_availability_dtype"
    )
    assert (
        meniscus_local_body(raw, available, target.astype(np.uint8), _frame())["status"]
        == "malformed_target_dtype"
    )
    bad_spacing = PlaneFrame(np.zeros(3), np.eye(3)[:, :2], (0.0, 1.0))
    assert (
        meniscus_local_body(raw, available, target, bad_spacing)["status"]
        == "invalid_spacing"
    )


def test_local_body_single_target_results_are_unchanged_without_second_source():
    raw, available, target = _body_scene()
    original = meniscus_local_body(raw, available, target, _frame())
    explicit_none = meniscus_local_body(
        raw, available, target, _frame(), other_target=None
    )
    assert original.keys() == explicit_none.keys()
    for key, value in original.items():
        if isinstance(value, np.ndarray):
            np.testing.assert_array_equal(value, explicit_none[key])
        else:
            assert value == explicit_none[key]
    for key in (
        "distance_to_other_target",
        "other_contacted_components",
        "both_contacted_components",
        "other_target_pixels",
        "available_other_target_pixels",
        "other_contacted_component_count",
        "target_contacted_component_count",
        "both_contacted_component_count",
        "target_contacted_component_labels",
        "other_target_contacted_component_labels",
        "both_contacted_component_labels",
    ):
        assert original[key] is None


def test_local_body_requires_one_component_to_reach_both_sources():
    raw, available, target = _body_scene()
    other = np.zeros(raw.shape, dtype=bool)
    other[16, 29] = True
    single_source = meniscus_local_body(raw, available, target, _frame())
    both_sources = meniscus_local_body(
        raw, available, target, _frame(), other_target=other
    )
    assert single_source["selection_status"] == "identified"
    assert both_sources["status"] == "measured_empty"
    assert both_sources["selection_status"] == "measured_empty"
    assert both_sources["target_contacted_component_count"] == 1
    assert both_sources["other_contacted_component_count"] == 0
    assert both_sources["both_contacted_component_count"] == 0
    assert not both_sources["selected"].any()
    assert both_sources["distance_to_other_target"].shape == raw.shape


def test_local_body_does_not_join_distinct_components_contacted_by_each_source():
    raw = np.full((30, 40), 10.0)
    raw[8:20, 5:14] = 2.0
    raw[8:20, 22:31] = 2.0
    available = np.ones(raw.shape, dtype=bool)
    target = np.zeros(raw.shape, dtype=bool)
    other = np.zeros(raw.shape, dtype=bool)
    target[13, 14] = True
    other[13, 21] = True

    result = meniscus_local_body(raw, available, target, _frame(), other_target=other)

    assert result["target_contacted_component_labels"]
    assert result["other_target_contacted_component_labels"]
    assert result["both_contacted_component_labels"] == []
    assert result["contacted_component_count"] == 0
    assert result["selected_pixels"] == 0
    assert result["selection_status"] == "measured_empty"


def test_local_body_preserves_exact_tie_among_components_reached_by_both():
    raw = np.full((30, 40), 10.0)
    raw[8:20, 5:14] = 2.0
    raw[8:20, 17:26] = 2.0
    available = np.ones(raw.shape, dtype=bool)
    target = np.zeros(raw.shape, dtype=bool)
    other = np.zeros(raw.shape, dtype=bool)
    target[12, 15] = True
    other[13, 15] = True

    result = meniscus_local_body(raw, available, target, _frame(), other_target=other)

    assert result["status"] == "tied_largest_components"
    assert result["selection_status"] == "tied_largest_components"
    assert (
        result["target_contacted_component_labels"]
        == result["other_target_contacted_component_labels"]
    )
    assert result["both_contacted_component_count"] == 2
    assert len(result["largest_component_labels"]) == 2
    assert result["selected_pixels"] == 0


def test_local_body_reports_unavailable_second_source_as_unmeasured():
    raw, available, target = _body_scene()
    other = np.zeros(raw.shape, dtype=bool)
    other[16, 20] = True
    available[other] = False

    result = meniscus_local_body(raw, available, target, _frame(), other_target=other)

    assert result["status"] == "other_target_unavailable"
    assert result["selection_status"] == "unmeasured"
    assert result["other_target_pixels"] == 1
    assert result["available_other_target_pixels"] == 0
    assert result["selected"] is None


def test_local_body_transposes_both_source_distances_with_physical_spacing():
    raw, available, target = _body_scene()
    target[:] = False
    target[16, 13] = True
    other = np.zeros(raw.shape, dtype=bool)
    other[16, 20] = True
    first = meniscus_local_body(
        raw, available, target, _frame((1.0, 2.0)), other_target=other
    )
    second = meniscus_local_body(
        raw.T,
        available.T,
        target.T,
        _frame((2.0, 1.0)),
        other_target=other.T,
    )
    assert first["status"] == second["status"] == "identified"
    for key in (
        "distance_to_target",
        "contacted_components",
        "selected",
        "distance_to_other_target",
        "other_contacted_components",
        "both_contacted_components",
    ):
        np.testing.assert_allclose(first[key], second[key].T, equal_nan=True)
    assert first["selected_pixels"] == second["selected_pixels"]


def test_local_body_names_malformed_second_source():
    raw, available, target = _body_scene()
    assert (
        meniscus_local_body(
            raw, available, target, _frame(), other_target=np.zeros((2, 2), bool)
        )["status"]
        == "malformed_other_target_shape"
    )
    assert (
        meniscus_local_body(
            raw,
            available,
            target,
            _frame(),
            other_target=np.zeros(raw.shape, dtype=np.uint8),
        )["status"]
        == "malformed_other_target_dtype"
    )
    assert (
        meniscus_local_body(
            raw,
            available,
            target,
            _frame(),
            other_target=np.zeros(raw.shape, dtype=bool),
        )["status"]
        == "other_target_missing"
    )
