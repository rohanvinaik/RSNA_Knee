"""Native categorical support, exact bounds and the real interior/profile interface."""

from dataclasses import replace

import numpy as np
import pytest

from knee.objects.interiors import EDGE_KINDS, dark_bands, read_interiors
from knee.objects.profiles import sample_profiles
from knee.relations.pair_codes import CODES
from knee.relations.pairings import footprint_labels_reference, read_pairings


def test_categorical_footprint_never_invents_the_average_label():
    labels = np.array([[1, 3], [4, 5]], dtype=np.int32)
    original = labels.copy()
    result = footprint_labels_reference(
        labels, np.ones((2, 2), dtype=bool), np.array([[0, 0.5], [1, 1]])
    )
    assert result.tolist() == [[1, 3, -1, -1], [5, -1, -1, -1]]
    assert not result.flags.writeable
    np.testing.assert_array_equal(labels, original)
    assert labels.flags.writeable


def test_unread_coordinates_and_missing_positive_contributors_are_not_zero():
    labels = np.ones((2, 2), dtype=np.int32)
    available = np.array([[True, False], [True, True]])
    result = footprint_labels_reference(
        labels, available, np.array([[0, 0.5], [-0.1, 0], [np.nan, 0]])
    )
    assert result.tolist() == [[1, -2, -1, -1], [-2] * 4, [-2] * 4]


def test_empty_native_plane_is_unread_for_each_supplied_position():
    result = footprint_labels_reference(
        np.empty((0, 0), dtype=np.int32),
        np.empty((0, 0), dtype=bool),
        np.array([[0, 0]]),
    )
    assert result.tolist() == [[-2] * 4]


def bracket_fixture():
    plane = np.tile([8.0, 8.0, 0.0, 0.0, 8.0, 8.0, 8.0], (3, 1))
    offsets = np.arange(-3.0, 4.0)
    interior = read_interiors(plane, (1.0, 1.0), 1.0, 1.0, offsets)
    points, normals = np.array([[1.0, 3.0]]), np.array([[0.0, 1.0]])
    profiles = sample_profiles(plane, points, normals, offsets, (1.0, 1.0))
    low, high, trace, codes = dark_bands(
        profiles, 1.0, np.array([EDGE_KINDS["low_signal"]]), points, normals, (1, 1)
    )
    return replace(
        interior,
        edge_points_rc=points,
        edge_normals_rc=normals,
        edge_regions=np.array([1], dtype=np.int32),
        profiles=profiles,
        band_low_mm=low,
        band_high_mm=high,
        trace_points_rc=trace,
        trace_codes=codes,
    )


def test_pair_records_original_bracket_and_immediate_flanking_samples():
    interior = bracket_fixture()
    reading = read_pairings(interior, (1.0, 1.0))
    assert reading.code == "present"
    assert reading.counts["paired"] == 1
    assert CODES[int(reading.outcome_codes[0])] == "paired"
    assert reading.source_labels.tolist() == [1]
    assert reading.far_labels.tolist() == [2]
    assert reading.positions_rc.tolist() == [[[1, 1], [1, 4]]]
    assert reading.band_limits_mm.tolist() == [[-1, 0]]
    assert reading.contributor_labels.tolist() == [[[1, -1, -1, -1], [2, -1, -1, -1]]]
    assert sum(reading.counts.values()) == len(interior.trace_codes)
    assert not reading.positions_rc.flags.writeable


def test_unbracketed_and_malformed_brackets_keep_their_profile_rows():
    interior = bracket_fixture()
    no_bracket = replace(interior, trace_codes=np.array([2], dtype=np.uint8))
    assert read_pairings(no_bracket, (1, 1)).counts["profile_unbracketed"] == 1
    malformed = replace(interior, band_low_mm=np.array([-0.75]))
    reading = read_pairings(malformed, (1, 1))
    assert reading.counts["item_unread"] == 1
    assert reading.trace_codes.tolist() == [1]
    assert reading.far_labels.tolist() == [0]


def test_absent_empty_and_unread_predecessors_have_distinct_codes():
    assert read_pairings(None, None).code == "predecessor_absent"
    empty = read_interiors(np.zeros((3, 7)), (1, 1), 1, 1, np.arange(-3.0, 4.0))
    assert read_pairings(empty, (1, 1)).code == "predecessor_empty"
    reading = read_pairings(bracket_fixture(), None)
    assert reading.code == "item_unread"
    assert reading.counts["item_unread"] == 1


@pytest.mark.parametrize(
    "field,dtype",
    [
        ("edge_regions", np.int64),
        ("trace_codes", np.int32),
        ("band_low_mm", np.int32),
        ("available", np.uint8),
    ],
)
def test_malformed_predecessor_representation_is_refused(field, dtype):
    interior = bracket_fixture()
    malformed = replace(interior, **{field: getattr(interior, field).astype(dtype)})
    reading = read_pairings(malformed, (1, 1))
    assert reading.code == "item_unread"
    assert reading.counts["paired"] == 0
    assert reading.source_labels.dtype == np.int32
    assert reading.trace_codes.dtype == np.uint8
    assert reading.band_limits_mm.dtype == np.float64


def test_returned_counts_cannot_be_changed_by_a_consumer():
    reading = read_pairings(bracket_fixture(), (1, 1))
    with pytest.raises(TypeError):
        reading.counts["paired"] = 999


def test_tiny_fraction_uses_the_original_samplers_float64_weight_rule():
    # The existing intensity sampler omits the product that underflows to zero.
    plane = np.array([[1.0, 1.0], [1.0, np.nan]])
    points = np.array([[1e-200, 1e-200]])
    sampled = sample_profiles(
        plane, points, np.array([[0.0, 1.0]]), np.array([0.0]), (1, 1)
    )
    assert sampled.valid.tolist() == [[True]]
    labels = np.array([[1, 1], [1, 2]], dtype=np.int32)
    footprint = footprint_labels_reference(labels, np.isfinite(plane), points)
    assert footprint.tolist() == [[1, 1, 1, -1]]
