"""Intent tests for the input stage's pure decisions (knee.study.codes), written from the founder's agreed contract:
a label is "1", "0" or not given; a series is handed on whole, and stacked only when its files form one stack; and
every zero says which zero it is."""

from knee.study.codes import label_code, stack_codes, tag_reasons


def test_the_hosts_values_are_kept_as_given() -> None:
    assert label_code("1") == "1"
    assert label_code("0") == "0"


def test_a_blank_is_not_given_never_a_zero() -> None:
    assert label_code("") == "not_given"


def test_any_other_value_is_carried_as_unrecognized() -> None:
    for raw in (" ", "1.0", "nan", "NaN", "yes", "-1", "2"):
        assert label_code(raw) == "unrecognized", raw


def test_each_kind_of_zero_in_a_tag_is_its_own_reason() -> None:
    assert tag_reasons("position", 0, 0, 0, 0) == []
    assert tag_reasons("position", 2, 0, 0, 0) == ["position_absent"]
    assert tag_reasons("spacing", 0, 1, 0, 0) == ["spacing_empty"]
    assert tag_reasons("orientation", 0, 0, 3, 0) == ["orientation_malformed"]
    assert tag_reasons("orientation", 0, 0, 0, 1) == ["orientation_degenerate"]


def test_every_kind_found_is_reported_in_a_fixed_order() -> None:
    assert tag_reasons("orientation", 1, 1, 1, 1) == [
        "orientation_absent",
        "orientation_empty",
        "orientation_malformed",
        "orientation_degenerate",
    ]


def test_a_complete_series_is_stackable() -> None:
    assert stack_codes(True, 4, 0, [], 1, 1, 4, 4) == ("stackable",)


def test_a_missing_directory_and_an_empty_one_are_different_zeros() -> None:
    assert stack_codes(False, 0, 0, [], 0, 0, 0, 0) == ("directory_missing",)
    assert stack_codes(True, 0, 0, [], 0, 0, 0, 0) == ("no_slices",)


def test_each_reason_is_named() -> None:
    assert stack_codes(True, 4, 1, [], 1, 1, 4, 4) == ("multiframe_file",)
    assert stack_codes(True, 4, 0, ["spacing_malformed"], 1, 1, 4, 4) == (
        "spacing_malformed",
    )
    assert stack_codes(True, 4, 0, [], 2, 1, 4, 4) == ("shape_varies",)
    assert stack_codes(True, 4, 0, [], 1, 2, 4, 4) == ("dtype_varies",)
    assert stack_codes(True, 4, 0, [], 1, 1, 4, 3) == ("positions_repeat",)


def test_every_reason_that_holds_is_reported_in_a_fixed_order() -> None:
    reasons = ["position_absent", "orientation_degenerate"]
    assert stack_codes(True, 4, 1, reasons, 3, 2, 2, 1) == (
        "multiframe_file",
        "position_absent",
        "orientation_degenerate",
        "shape_varies",
        "dtype_varies",
    )


def test_repeats_are_judged_only_when_every_file_has_a_position() -> None:
    assert stack_codes(True, 4, 0, ["position_absent"], 1, 1, 3, 2) == (
        "position_absent",
    )
    assert stack_codes(True, 4, 0, [], 1, 1, 4, 2) == ("positions_repeat",)
