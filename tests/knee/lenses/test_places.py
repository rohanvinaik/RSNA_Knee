"""A native digit map is the scalar reading repeated, not a new classifier or a rescaling."""

from types import SimpleNamespace

import numpy as np
import pytest

from knee.lenses.digits import DIGIT_CODES, digit_code
from knee.lenses.places import CODE_VALUES, SILENT, place_codes_reference, read_lenses
from knee.telemetry import recording


@pytest.mark.parametrize(
    "edges,count,minimum",
    [
        ((2.0, 4.0), 8, 8),
        ((3.0, 3.0), 8, 8),
        ((4.0, 2.0), 8, 8),
        ((np.nan, 4.0), 8, 8),
        ((2.0, 4.0), 7, 8),
        ((2.0, 4.0), 0, 0),
    ],
)
def test_vector_reference_answers_to_every_scalar_including_silence(
    edges, count, minimum
) -> None:
    values = np.array([[[1.0, 2.0, 3.0, 4.0, 5.0, np.nan, np.inf, -np.inf]]])
    before = values.copy()
    actual = place_codes_reference(values, *edges, count, minimum)
    expected = np.array(
        [
            CODE_VALUES[digit_code(float(v), *edges, count, minimum)]
            for v in values.flat
        ],
        dtype=np.uint8,
    ).reshape(values.shape)
    np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(values, before)
    assert not actual.flags.writeable


def test_two_acquisitions_use_their_own_pair_without_rescaling() -> None:
    first = read_lenses(
        np.array([[[1.0, 2.0, 3.0, 4.0, 5.0, np.nan]]]),
        SimpleNamespace(
            terciles=(2.0, 4.0), foreground_count=8, tercile_minimum_population=8
        ),
    )
    second = read_lenses(
        np.array([[[10.0, 20.0, 30.0, 40.0, 50.0, np.nan]]]),
        SimpleNamespace(
            terciles=(20.0, 40.0), foreground_count=8, tercile_minimum_population=8
        ),
    )
    assert first.normalisation == second.normalisation == "none"
    assert (first.low_edge, first.high_edge) == (2.0, 4.0)
    assert (second.low_edge, second.high_edge) == (20.0, 40.0)
    np.testing.assert_array_equal(first.digits, second.digits)
    np.testing.assert_array_equal(first.digits, [[[-1, 0, 0, 0, 1, SILENT]]])
    assert first.counts == (1, 3, 1, 1, 0, 0, 0)
    assert not first.digits.flags.writeable


@pytest.mark.parametrize("dtype", [np.float16, np.float32, np.float64, np.uint16])
def test_scalar_edges_are_not_rounded_to_the_source_dtype(dtype) -> None:
    values = np.array([[[1, 2]]], dtype=dtype)
    low = np.nextafter(1.0, np.inf)
    high = np.nextafter(2.0, -np.inf)
    codes = place_codes_reference(values, low, high, 8, 8)
    assert codes[0, 0, 0] == CODE_VALUES[digit_code(1.0, low, high, 8, 8)]
    assert codes[0, 0, 1] == CODE_VALUES[digit_code(2.0, low, high, 8, 8)]
    assert codes[0, 0, 0] == CODE_VALUES["below"]
    assert codes[0, 0, 1] == CODE_VALUES["above"]


def test_missing_metadata_never_reconstructs_a_population_from_a_share() -> None:
    reading = read_lenses(
        np.ones((1, 2, 2)), SimpleNamespace(terciles=(1.0, 2.0), foreground_share=0.8)
    )
    assert reading.code == "item_unread"
    assert reading.population_count is None
    assert reading.low_edge is None
    assert (reading.digits == SILENT).all()


def test_small_population_writes_only_named_silence() -> None:
    reading = read_lenses(
        np.ones((1, 2, 2)),
        SimpleNamespace(
            terciles=(1.0, 2.0), foreground_count=7, tercile_minimum_population=8
        ),
    )
    assert reading.code == "population_too_small"
    assert (reading.digits == SILENT).all()
    assert reading.counts[CODE_VALUES["population_too_small"]] == 4


@pytest.mark.parametrize(
    "volume,key,code",
    [
        (None, None, "predecessor_absent"),
        ("malformed", object(), "item_unread"),
        (np.empty((0, 2, 2)), object(), "predecessor_empty"),
    ],
)
def test_missing_malformed_and_empty_predecessors_complete_with_named_codes(
    volume, key, code
) -> None:
    reading = read_lenses(volume, key)
    assert reading.code == code
    assert not reading.codes.flags.writeable


def test_map_counts_and_ledger_are_computed_from_codes_once() -> None:
    with recording() as ledger:
        reading = read_lenses(
            np.array([[[1.0, 3.0, 5.0, np.nan]]]),
            SimpleNamespace(
                terciles=(2.0, 4.0), foreground_count=8, tercile_minimum_population=8
            ),
        )
    assert sum(reading.counts) == reading.codes.size
    assert len(reading.counts) == len(DIGIT_CODES)
    assert ledger.totals() == {"places": 4, "output_bytes": 8}
