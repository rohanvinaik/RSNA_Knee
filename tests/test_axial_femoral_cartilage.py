from __future__ import annotations

import numpy as np

from knee.collapse.cartilage import femoral_cartilage_on_plane


def _case() -> tuple[np.ndarray, ...]:
    raw = np.full((32, 32), 5.0)
    raw[9:11, 12:19] = 20.0
    raw[20:22, 12:19] = 20.0
    available = np.ones(raw.shape, dtype=bool)
    core = np.zeros(raw.shape, dtype=bool)
    core[15, 12] = True
    enclosure = np.zeros(raw.shape, dtype=bool)
    enclosure[12:20, 12] = True
    enclosure[12:20, 19] = True
    enclosure[12, 12:20] = True
    enclosure[19, 12:20] = True
    sagittal = np.zeros(raw.shape, dtype=bool)
    sagittal[10, 12] = True
    coronal = np.zeros(raw.shape, dtype=bool)
    coronal[10, 18] = True
    return raw, available, core, enclosure, sagittal, coronal


def _measure(values: tuple[np.ndarray, ...], marrow: float = 10.0) -> dict:
    raw, available, core, enclosure, sagittal, coronal = values
    return femoral_cartilage_on_plane(
        raw,
        available,
        core,
        enclosure,
        sagittal,
        coronal,
        marrow,
        (1.0, 1.0),
    )


def test_whole_candidate_component_must_contact_both_source_views() -> None:
    result = _measure(_case())

    assert result["status"] == "selected_native_component"
    assert result["candidate"].any()
    assert result["selected"].any()
    assert np.all(result["selected"] <= result["candidate"])
    assert len(result["contact_labels"]) == 1
    assert int(result["selected"].sum()) == int(result["contact_sizes"][0])
    assert int(result["candidate"].sum()) > int(result["selected"].sum())
    assert result["filled_enclosure"].sum() > result["selected_enclosure"].sum()
    assert np.array_equal(
        result["fill_difference"],
        result["filled_enclosure"] & ~result["selected_enclosure"],
    )


def test_tied_largest_enclosures_are_not_selected() -> None:
    raw, available, core, enclosure, sagittal, coronal = _case()
    enclosure[:] = False
    enclosure[8:12, 8] = True
    enclosure[8:12, 11] = True
    enclosure[8, 8:12] = True
    enclosure[11, 8:12] = True
    enclosure[20:24, 20] = True
    enclosure[20:24, 23] = True
    enclosure[20, 20:24] = True
    enclosure[23, 20:24] = True
    core[:] = False
    core[9, 8] = True
    core[21, 20] = True

    result = _measure((raw, available, core, enclosure, sagittal, coronal))

    assert result["status"] == "tied_largest_touched_enclosures"
    assert not result["selected_enclosure"].any()
    assert len(result["touched_labels"]) == 2


def test_unknown_neighbour_of_enclosure_prevents_a_complete_claim() -> None:
    raw, available, core, enclosure, sagittal, coronal = _case()
    available[11, 15] = False

    result = _measure((raw, available, core, enclosure, sagittal, coronal))

    assert result["status"] == "enclosure_neighbors_unavailable"
    assert not result["selected"].any()


def test_values_outside_available_support_do_not_change_selected_mask() -> None:
    values = list(_case())
    raw, available, *_ = values
    available[0, 0] = False
    first = _measure(tuple(values))
    changed = raw.copy()
    changed[0, 0] = 1e12
    values[0] = changed
    second = _measure(tuple(values))

    assert first["status"] == second["status"]
    assert np.array_equal(first["candidate"], second["candidate"])
    assert np.array_equal(first["selected"], second["selected"])


def test_existing_brightness_and_fluid_boundaries_are_respected() -> None:
    raw, available, core, enclosure, sagittal, coronal = _case()
    raw[9, 12] = 15.0
    raw[10, 12] = 40.0

    result = _measure((raw, available, core, enclosure, sagittal, coronal))

    assert not result["candidate"][9, 12]
    assert result["candidate"][10, 12]


def test_missing_view_target_is_named_unknown() -> None:
    raw, available, core, enclosure, sagittal, coronal = _case()
    coronal[:] = False

    result = _measure((raw, available, core, enclosure, sagittal, coronal))

    assert result["status"] == "source_target_unavailable"
    assert not result["selected"].any()


def test_empty_brightness_band_is_distinct_from_an_unknown() -> None:
    raw, available, core, enclosure, sagittal, coronal = _case()
    raw[:] = 5.0

    result = _measure((raw, available, core, enclosure, sagittal, coronal))

    assert result["status"] == "measured_empty_brightness_band"
    assert not result["candidate"].any()
    assert not result["selected"].any()


def test_empty_core_and_untouched_enclosure_are_named_separately() -> None:
    values = list(_case())
    values[2][:] = False
    empty_core = _measure(tuple(values))
    assert empty_core["status"] == "femur_core_empty"

    values = list(_case())
    values[3][:] = False
    untouched = _measure(tuple(values))
    assert untouched["status"] == "no_positive_enclosure_touched_by_core"


def test_equal_largest_contacting_candidate_components_remain_unresolved() -> None:
    raw, available, core, enclosure, sagittal, coronal = _case()
    raw[:] = 5.0
    raw[10, 12:15] = 20.0
    raw[10, 16:19] = 20.0
    sagittal[:] = False
    coronal[:] = False
    sagittal[10, 15] = True
    coronal[10, 15] = True

    result = _measure((raw, available, core, enclosure, sagittal, coronal))

    assert result["status"] == "tied_largest_components_contacting_both_sources"
    assert len(result["contact_labels"]) == 2
    assert np.array_equal(result["contact_sizes"], np.asarray([3, 3]))
    assert not result["selected"].any()


def test_malformed_context_and_nonfinite_available_values_are_unknown() -> None:
    values = list(_case())
    values[1] = values[1][:-1]
    malformed = _measure(tuple(values))
    assert malformed["status"] == "native_context_shape_unavailable"

    values = list(_case())
    values[0][0, 0] = np.nan
    nonfinite = _measure(tuple(values))
    assert nonfinite["status"] == "native_values_unavailable"


def test_nonpositive_or_nonfinite_marrow_level_is_unknown() -> None:
    values = _case()
    for level in (0.0, float("nan"), float("inf")):
        result = _measure(values, level)
        assert result["status"] == "native_measurement_unavailable"
