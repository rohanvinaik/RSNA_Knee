from __future__ import annotations

import numpy as np
import pytest

from knee.collapse.anterior_fat import (
    NativeGradientTerritories,
    fat_compatibility_sets,
    native_gradient_territories,
)


def _region(shape: tuple[int, int], *points: tuple[int, int]) -> np.ndarray:
    mask = np.zeros(shape, dtype=bool)
    for row, column in points:
        mask[row, column] = True
    return mask


def _by_name(result: NativeGradientTerritories) -> dict[str, np.ndarray]:
    labels = result.labels
    return {
        name: labels == marker_id for name, marker_id in result.marker_codes.items()
    }


def test_physical_spacing_scales_gradient_and_single_marker_fills_valid_region() -> (
    None
):
    rows, columns = np.indices((8, 9), dtype=np.float64)
    raw = 4.0 * rows + 3.0 * columns
    available = np.ones(raw.shape, dtype=bool)
    result = native_gradient_territories(
        raw,
        available,
        (2.0, 1.0),
        {"source:hoffasupport": _region(raw.shape, (4, 4))},
    )

    assert result.gradient_valid.all()
    assert result.gradient_magnitude[2:-2, 2:-2] == pytest.approx(np.sqrt(13.0))
    assert np.unique(result.gradient_u16).tolist() == [0]
    assert (result.labels == result.marker_codes["source:hoffasupport"]).all()
    assert not result.unknown.any()
    assert result.gradient_facts["spacing_rc_mm"] == [2.0, 1.0]


def test_unavailable_stored_values_cannot_change_gradient_or_basin() -> None:
    rows, columns = np.indices((12, 13), dtype=np.float64)
    raw = 0.7 * rows**2 + 1.3 * columns**2 + rows * columns
    available = np.ones(raw.shape, dtype=bool)
    available[5, 6] = False
    available[6, 5] = False
    groups = {
        "source:first": _region(raw.shape, (2, 2)),
        "peak:separate": _region(raw.shape, (9, 10)),
    }
    first = native_gradient_territories(raw, available, (0.7, 0.9), groups)
    changed = raw.copy()
    changed[~available] = np.array([1e30, -1e30])
    second = native_gradient_territories(changed, available, (0.7, 0.9), groups)

    assert np.array_equal(first.gradient_valid, second.gradient_valid)
    assert np.array_equal(first.gradient_u16, second.gradient_u16)
    assert np.array_equal(
        first.gradient_magnitude[first.gradient_valid],
        second.gradient_magnitude[second.gradient_valid],
    )
    assert np.array_equal(first.labels, second.labels)
    assert np.array_equal(first.unknown, second.unknown)
    assert not first.gradient_valid[5, 6]
    assert first.unknown[5, 6]


def test_equal_priority_output_follows_scipy_ift_queue_policy() -> None:
    from scipy import ndimage as ndi

    shape = (9, 11)
    raw = np.zeros(shape, dtype=np.float32)
    available = np.ones(shape, dtype=bool)
    left = _region(shape, (4, 1))
    right = _region(shape, (4, 9))
    result = native_gradient_territories(
        raw, available, (1.0, 1.0), {"H": left, "Q": right}
    )
    expected = ndi.watershed_ift(
        result.gradient_u16,
        result.marker_ids,
        structure=ndi.generate_binary_structure(2, 1),
    )

    assert np.array_equal(result.labels, expected)
    assert result.gradient_facts["watershed"]["equal_priority_policy"].startswith(
        "native SciPy watershed_ift marker queue order"
    )


def test_disconnected_or_unseeded_valid_components_remain_unknown() -> None:
    shape = (9, 11)
    raw = np.arange(np.prod(shape), dtype=np.float64).reshape(shape)
    available = np.ones(shape, dtype=bool)
    available[:, 5] = False
    result = native_gradient_territories(
        raw,
        available,
        (1.0, 1.0),
        {"left_source": _region(shape, (4, 2))},
    )

    assert not result.unknown[4, 2]
    assert result.unknown[:, 5].all()
    assert result.unknown[:, 7:].all()
    assert not result.labels[:, 7:].any()
    assert result.gradient_facts["watershed"]["seeded_components"] == 1
    assert result.gradient_facts["watershed"]["unseeded_components_left_unknown"] == 1


def test_conflicting_source_and_peak_claims_are_withheld_not_prioritized() -> None:
    shape = (7, 8)
    raw = np.arange(np.prod(shape), dtype=np.float64).reshape(shape)
    available = np.ones(shape, dtype=bool)
    first = _region(shape, (2, 2), (2, 3))
    peak = _region(shape, (2, 2), (4, 5))
    result = native_gradient_territories(
        raw,
        available,
        (1.0, 1.0),
        {"source:H": first, "native_peak:territory_1": peak},
    )

    assert result.conflicts[2, 2]
    assert result.marker_ids[2, 2] == 0
    assert result.labels[2, 2] == 0
    assert result.unknown[2, 2]
    assert result.marker_codes == {"source:H": 1, "native_peak:territory_1": 2}


def test_conflicting_marker_strip_is_unknown_and_separates_unseeded_component() -> None:
    shape = (9, 11)
    raw = np.arange(np.prod(shape), dtype=np.float64).reshape(shape)
    strip = np.zeros(shape, dtype=bool)
    strip[:, 5] = True
    result = native_gradient_territories(
        raw,
        np.ones(shape, dtype=bool),
        (1.0, 1.0),
        {
            "left_source": _region(shape, (4, 2)),
            "first_conflict_claim": strip,
            "second_conflict_claim": strip,
        },
    )

    assert result.conflicts[:, 5].all()
    assert result.unknown[:, 5].all()
    assert result.unknown[:, 7:].all()
    assert not result.labels[:, 7:].any()
    assert result.gradient_facts["watershed"]["seeded_components"] == 1
    assert result.gradient_facts["watershed"]["unseeded_components_left_unknown"] == 1


def test_unavailable_compatibility_is_unknown_and_disagreement_is_retained() -> None:
    first_available = np.array([[True, True, False, False, True]])
    second_available = np.array([[True, True, True, False, True]])
    first_compatible = np.array([[True, False, True, True, False]])
    second_compatible = np.array([[True, True, False, True, True]])
    result = fat_compatibility_sets(
        [first_compatible, second_compatible],
        [first_available, second_available],
    )

    assert result["positive"].tolist() == [[True, True, False, False, True]]
    assert result["negative"].tolist() == [[False, True, True, False, True]]
    assert result["unknown"].tolist() == [[False, False, False, True, False]]
    assert result["disagreement"].tolist() == [[False, True, False, False, True]]
    assert result["positive_without_known_negative"].tolist() == [
        [True, False, False, False, False]
    ]
    assert result["negative_without_known_positive"].tolist() == [
        [False, False, True, False, False]
    ]


@pytest.mark.parametrize(
    ("raw", "available", "spacing", "markers", "message"),
    [
        (
            np.ones((3, 3), dtype=object),
            np.ones((3, 3), dtype=bool),
            (1.0, 1.0),
            {},
            "raw_must_be",
        ),
        (
            np.ones((3, 3)),
            np.ones((3, 2), dtype=bool),
            (1.0, 1.0),
            {},
            "available_must_be",
        ),
        (np.ones((3, 3)), np.ones((3, 3), dtype=bool), (1.0, 0.0), {}, "spacing_rc_mm"),
        (
            np.ones((3, 3)),
            np.ones((3, 3), dtype=bool),
            (1.0, 1.0),
            {"bad": np.ones((3, 3))},
            "marker_bad_must_be_boolean",
        ),
    ],
)
def test_native_gradient_rejects_malformed_measurement_inputs(
    raw: np.ndarray,
    available: np.ndarray,
    spacing: tuple[float, float],
    markers: dict[str, np.ndarray],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        native_gradient_territories(raw, available, spacing, markers)


def test_fat_sets_reject_unpaired_or_wrong_shaped_fields() -> None:
    field = np.ones((2, 2), dtype=bool)
    with pytest.raises(ValueError, match="nonempty_and_paired"):
        fat_compatibility_sets([field], [])
    with pytest.raises(ValueError, match="available_1_must_be_boolean"):
        fat_compatibility_sets([field, field], [field, np.ones((1, 2), dtype=bool)])
