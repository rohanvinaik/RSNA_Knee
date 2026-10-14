"""Intent tests for the run's receipt: every study's records kept, one study's replaced at a time."""

import pytest

from knee.receipt import merged_receipt

REQUEST = {
    "prominence_mm": 3.0,
    "offsets_mm": [0.0],
    "slice_index": None,
    "backend": "reference",
}


def record(study: str, series: str) -> dict:
    return {"study_uid": study, "series_uid": series}


def test_a_first_study_starts_the_receipt():
    receipt = merged_receipt(
        None,
        REQUEST,
        "A",
        ["a1", "a2"],
        [record("A", "a1")],
        {"a2": "no_stacked_volume"},
        {"totals": {}},
    )
    assert receipt["records"] == [record("A", "a1")]
    assert receipt["unread"] == {"a2": "no_stacked_volume"}
    assert receipt["telemetry"] == {"A": {"totals": {}}}


def test_a_second_study_keeps_the_first():
    first = merged_receipt(
        None, REQUEST, "A", ["a1"], [record("A", "a1")], {}, {"totals": {"x": 1}}
    )
    both = merged_receipt(
        first,
        REQUEST,
        "B",
        ["b1", "b2"],
        [record("B", "b1")],
        {"b2": "slice_unavailable"},
        {"totals": {"x": 2}},
    )
    assert both["records"] == [record("A", "a1"), record("B", "b1")]
    assert both["unread"] == {"b2": "slice_unavailable"}
    assert set(both["telemetry"]) == {"A", "B"}


def test_a_study_run_again_replaces_only_its_own():
    first = merged_receipt(
        None,
        REQUEST,
        "A",
        ["a1", "a2"],
        [record("A", "a1")],
        {"a2": "no_stacked_volume"},
        {"run": 1},
    )
    both = merged_receipt(
        first, REQUEST, "B", ["b1"], [record("B", "b1")], {}, {"run": 1}
    )
    again = merged_receipt(
        both,
        REQUEST,
        "A",
        ["a1", "a2"],
        [record("A", "a1"), record("A", "a2")],
        {},
        {"run": 2},
    )
    assert again["records"] == [record("B", "b1"), record("A", "a1"), record("A", "a2")]
    # a2 was silent before and is read now: its old silence goes
    assert again["unread"] == {}
    assert again["telemetry"] == {"B": {"run": 1}, "A": {"run": 2}}


def test_a_receipt_that_does_not_carry_telemetry_holds_none_for_the_study():
    receipt = merged_receipt(None, REQUEST, "A", ["a1"], [record("A", "a1")], {}, None)
    assert receipt["telemetry"] == {}


def test_records_made_under_other_settings_are_never_mixed_in():
    first = merged_receipt(None, REQUEST, "A", ["a1"], [record("A", "a1")], {}, None)
    other = {**REQUEST, "prominence_mm": 2.0}
    with pytest.raises(ValueError, match="receipt_request_differs"):
        merged_receipt(first, other, "B", ["b1"], [record("B", "b1")], {}, None)
