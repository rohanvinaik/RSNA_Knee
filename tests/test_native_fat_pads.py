import numpy as np
import pytest

from knee.collapse.fat_pads import native_fat_support


def classes(shape: tuple[int, int], *, positive: bool, known: bool = True):
    candidate = np.ones(shape, dtype=bool)
    return {
        "positive_without_known_negative": candidate.copy()
        if positive
        else np.zeros(shape, dtype=bool),
        "known": candidate.copy() if known else np.zeros(shape, dtype=bool),
        "unknown": np.zeros(shape, dtype=bool) if known else candidate.copy(),
        "disagreement": np.zeros(shape, dtype=bool),
    }


def test_native_fat_support_intersects_measured_geometry_and_exclusions():
    candidate = np.ones((3, 4), dtype=bool)
    available = np.ones_like(candidate)
    white = np.zeros_like(candidate)
    white[0, 0] = True
    core = np.zeros_like(candidate)
    core[2, 3] = True

    result = native_fat_support(
        candidate, available, white, classes(candidate.shape, positive=True), core
    )

    expected = candidate & ~white & ~core
    assert result.status == "native_support_selected"
    assert result.complete
    assert result.mask.dtype == np.bool_
    np.testing.assert_array_equal(result.mask, expected)
    assert result.support_count == int(expected.sum())


def test_native_fat_support_reports_complete_measured_empty():
    candidate = np.ones((2, 3), dtype=bool)
    result = native_fat_support(
        candidate,
        np.ones_like(candidate),
        np.zeros_like(candidate),
        classes(candidate.shape, positive=False),
    )

    assert result.status == "measured_empty_native_support"
    assert result.complete
    assert result.support_count == 0
    assert not result.mask.any()


def test_native_fat_support_keeps_unknown_distinct_from_empty():
    candidate = np.ones((2, 2), dtype=bool)
    result = native_fat_support(
        candidate,
        np.ones_like(candidate),
        np.zeros_like(candidate),
        classes(candidate.shape, positive=False, known=False),
    )

    assert result.status == "native_compatibility_incomplete"
    assert not result.complete
    assert result.unknown_count == int(candidate.sum())
    assert not result.mask.any()


def test_native_fat_support_does_not_claim_empty_without_same_series_fluid_reading():
    candidate = np.ones((2, 2), dtype=bool)
    result = native_fat_support(
        candidate,
        np.ones_like(candidate),
        None,
        classes(candidate.shape, positive=True),
    )

    assert result.status == "same_series_fluid_level_unavailable"
    assert not result.complete
    assert result.unknown_count == int(candidate.sum())
    assert not result.mask.any()


@pytest.mark.parametrize(
    ("candidate", "available", "white", "expected"),
    [
        (
            np.ones((2, 2), dtype=np.uint8),
            np.ones((2, 2), dtype=bool),
            None,
            "candidate",
        ),
        (np.ones((2, 2), dtype=bool), np.ones((2, 3), dtype=bool), None, "available"),
        (
            np.ones((2, 2), dtype=bool),
            np.ones((2, 2), dtype=bool),
            np.ones((2, 3), dtype=bool),
            "white_fluid",
        ),
    ],
)
def test_native_fat_support_rejects_malformed_masks(
    candidate, available, white, expected
):
    with pytest.raises(ValueError, match=expected):
        native_fat_support(
            candidate,
            available,
            white,
            classes((2, 2), positive=True),
        )
