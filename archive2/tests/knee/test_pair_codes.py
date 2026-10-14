"""Direct two-sign intent for categorical pairing; labels are never averaged."""

import pytest

from knee.relations.pair_codes import pair_code


@pytest.mark.parametrize(
    ("source", "trace", "near", "far", "expected"),
    [
        (1, 1, [1], [3], "paired"),
        (3, 1, [3, 3, -1, -1], [1, 1], "paired"),
        (1, 1, [1], [1], "same_object"),
        (1, 1, [1], [1, 3], "far_ambiguous"),
        (1, 1, [1, 3], [2], "source_ambiguous"),
        (1, 1, [3], [2], "source_mismatch"),
        (1, 1, [0, 1], [2], "source_unassigned"),
        (1, 1, [1], [0, 2], "far_unassigned"),
        (0, 1, [1], [2], "source_unassigned"),
        (1, 1, [-2, 1], [2], "item_unread"),
        (1, 1, [1], [-2, 2], "item_unread"),
        (1, 1, [], [2], "item_unread"),
        (1, 1, [1], [-1], "item_unread"),
        (1, 4, [1], [2], "profile_unbracketed"),
        (1, 0, [1], [2], "item_unread"),
        (-1, 1, [1], [2], "invalid_measurement"),
        (1, 8, [1], [2], "invalid_measurement"),
        (1, 1, [-3], [2], "invalid_measurement"),
        (1, 1, [1], [-3], "invalid_measurement"),
    ],
)
def test_pairing_requires_both_supported_sides(source, trace, near, far, expected):
    assert pair_code(source, trace, near, far) == expected
