"""Intent tests for the telemetry: the ledger's own proof gate (its CONTRACT: disabled records
nothing; counted work is whole), the route, which names every product no stage read, and the
compute-once store, which makes a value once per study and hands it to every later asker."""

import pytest

from knee.telemetry import Ledger, computing, ledger, once, recording
from knee.telemetry.route import unread_products


def test_inside_a_study_a_value_is_made_once_and_handed_to_every_later_asker():
    made = []

    def make() -> list[int]:
        made.append(1)
        return [len(made)]

    with recording() as led, computing():
        first = once("frame", ("series", 3), make)
        again = once("frame", ("series", 3), make)
        other = once("frame", ("series", 4), make)
    assert first is again
    assert other == [2]
    assert len(made) == 2
    assert [event.name for event in led.events()] == [
        "frame.made",
        "frame.handed_on",
        "frame.made",
    ]


def test_outside_a_study_nothing_is_kept():
    made = []
    for _ in range(2):
        once("frame", "key", lambda: made.append(1))
    assert len(made) == 2


def test_each_study_starts_empty_and_the_scope_before_it_is_restored():
    made = []
    with computing():
        once("margin", "key", lambda: made.append("outer"))
        with computing():
            once("margin", "key", lambda: made.append("inner"))
        once("margin", "key", lambda: made.append("outer again"))
    assert made == ["outer", "inner"]


def test_a_disabled_ledger_records_nothing():
    quiet = Ledger()
    quiet.record("stage.produced", planes=1)
    with quiet.span("stage.work", planes=1):
        pass
    assert quiet.events() == ()


def test_counted_work_is_whole_and_never_negative():
    on = Ledger(enabled=True)
    with pytest.raises(TypeError):
        on.record("stage.work", planes=True)
    with pytest.raises(TypeError):
        on.record("stage.work", planes=1.5)  # ty: ignore[invalid-argument-type]
    with pytest.raises(ValueError):
        on.record("stage.work", planes=-1)
    on.record("stage.work", planes=2)
    on.record("stage.work", planes=3)
    assert on.totals() == {"planes": 5}


def test_recording_turns_the_ledger_on_for_a_block_then_restores_it():
    was = ledger.enabled
    with recording() as led:
        ledger.record("stage.work", planes=1)
        assert [event.name for event in led.events()] == ["stage.work"]
    assert ledger.enabled == was


def test_every_product_read_leaves_nothing_unread():
    names = ["series.volume.produced", "series.volume.consumed_by.regime"]
    assert unread_products(names) == ()


def test_a_product_no_stage_read_is_named():
    names = [
        "regime.background_split.produced",
        "regime.dark.produced",
        "regime.background_split.consumed_by.interiors",
    ]
    assert unread_products(names) == ("regime.dark",)


def test_reading_a_field_reads_its_product_but_not_the_fields_beside_it():
    names = [
        "squint_stack.produced",
        "squint_stack.median.produced",
        "squint_stack.centres_lps.produced",
        "squint_stack.centres_lps.consumed_by.fibula",
    ]
    assert unread_products(names) == ("squint_stack.median",)


def test_a_read_of_something_never_produced_is_no_island():
    assert unread_products(["study.consumed_by.squint_stack"]) == ()
