import numpy as np
import pytest

from knee.objects.assignments import white_body_at_location


def test_location_selects_the_whole_largest_eligible_body_not_the_target_region():
    white = np.zeros((10, 14), dtype=bool)
    white[1:3, 1:3] = True
    white[5:9, 5:12] = True
    target = np.zeros_like(white)
    target[1, 1] = True
    original_white = white.copy()
    original_target = target.copy()

    selected, code, readings = white_body_at_location(white, target)

    assert code == "selected"
    assert np.array_equal(
        selected, white & np.pad(np.ones((2, 2), bool), ((1, 7), (1, 11)))
    )
    assert int(selected.sum()) == 4
    assert readings["sizes"].tolist() == [4, 28]
    assert readings["eligible_ids"].tolist() == [1]
    assert readings["winner_ids"].tolist() == [1]
    assert np.array_equal(white, original_white)
    assert np.array_equal(target, original_target)


def test_missing_and_zero_dimension_inputs_are_empty_readings():
    selected, code, readings = white_body_at_location(None, np.ones((2, 4), dtype=bool))
    assert code == "no_body_at_target"
    assert selected.shape == (2, 4) and not selected.any()
    assert readings["labels"].shape == (2, 4)
    assert readings["sizes"].size == 0
    assert readings["eligible_ids"].size == 0
    assert readings["winner_ids"].size == 0

    empty = np.zeros((0, 3), dtype=bool)
    selected, code, readings = white_body_at_location(empty, empty.copy())
    assert code == "no_target"
    assert selected.shape == (0, 3)
    assert readings["labels"].shape == (0, 3)
    assert readings["sizes"].size == 0

    selected, code, readings = white_body_at_location(None, None)
    assert code == "no_target"
    assert selected.shape == readings["labels"].shape == (0, 0)


def test_equal_largest_eligible_bodies_abstain_and_retain_both_winners():
    white = np.zeros((6, 8), dtype=bool)
    white[1, 1:4] = True
    white[4, 4:7] = True
    target = np.zeros_like(white)
    target[1, 1] = True
    target[4, 6] = True

    selected, code, readings = white_body_at_location(white, target)

    assert code == "tied_largest_bodies"
    assert not selected.any()
    assert readings["sizes"].tolist() == [3, 3]
    assert readings["eligible_ids"].tolist() == [1, 2]
    assert readings["winner_ids"].tolist() == [1, 2]


def test_diagonal_white_pixels_form_one_eight_connected_body():
    white = np.zeros((5, 5), dtype=bool)
    white[1, 1] = True
    white[2, 2] = True
    white[3, 3] = True
    target = np.zeros_like(white)
    target[2, 2] = True

    selected, code, readings = white_body_at_location(white, target)

    assert code == "selected"
    assert np.array_equal(selected, white)
    assert readings["sizes"].tolist() == [3]
    assert readings["eligible_ids"].tolist() == [1]
    assert readings["winner_ids"].tolist() == [1]


def test_location_and_selection_commute_with_transpose_and_reflection():
    white = np.zeros((8, 11), dtype=bool)
    white[1:3, 1:4] = True
    white[5:7, 7:10] = True
    target = np.zeros_like(white)
    target[1, 2] = True
    expected, expected_code, _ = white_body_at_location(white, target)
    transforms = (lambda a: a.T, np.fliplr, np.flipud, lambda a: np.rot90(a, 2))

    for transform in transforms:
        transformed, code, readings = white_body_at_location(
            transform(white), transform(target)
        )
        assert code == expected_code == "selected"
        assert np.array_equal(transformed, transform(expected))
        assert int(readings["sizes"][readings["winner_ids"][0] - 1]) == int(
            expected.sum()
        )


@pytest.mark.parametrize(
    ("white", "target"),
    [
        (np.zeros((2, 3), dtype=bool), np.zeros((3, 2), dtype=bool)),
        (np.zeros(3, dtype=bool), np.zeros(3, dtype=bool)),
        (np.zeros((2, 2), dtype=np.uint8), np.zeros((2, 2), dtype=bool)),
    ],
)
def test_malformed_masks_are_rejected(white, target):
    with pytest.raises(ValueError):
        white_body_at_location(white, target)
