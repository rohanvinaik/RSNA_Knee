"""The ledger's proof gate, named by knee.telemetry.ledger.CONTRACT.

Counted work is deterministic and is evidence; a duration is behaviour. These tests pin that
distinction, and pin that a disabled ledger is genuinely silent -- a production run must pay nothing
for the instrumentation being present.
"""

import pytest

from knee.telemetry import Ledger, ledger, recording


def test_a_disabled_ledger_records_nothing() -> None:
    quiet = Ledger()
    assert not quiet.enabled
    quiet.record("anything", places=10)
    with quiet.span("a block", samples=5) as extra:
        extra["samples"] = 99
    assert quiet.events() == ()
    assert quiet.totals() == {}


def test_a_disabled_ledger_refuses_nothing_and_validates_nothing() -> None:
    """Silence must be cheap: a disabled ledger does not even inspect its arguments."""
    quiet = Ledger()
    quiet.record("bad", flag=True)  # a bool would be refused when enabled
    assert quiet.events() == ()


def test_counted_work_must_be_whole_and_not_negative() -> None:
    loud = Ledger(enabled=True)
    with pytest.raises(TypeError):
        # Deliberately the wrong type: the point is that the RUNTIME refuses it. ty does not
        # honour mypy's bracket form, so its own suppression is used here.
        loud.record("event", places=1.5)  # ty: ignore[invalid-argument-type]
    with pytest.raises(ValueError):
        loud.record("event", places=-1)
    with pytest.raises(ValueError):
        loud.record("", places=1)
    assert loud.events() == ()


def test_a_bool_is_refused_because_true_is_an_int() -> None:
    """A flag silently summed as 1 would corrupt a budget, so it is refused explicitly."""
    loud = Ledger(enabled=True)
    with pytest.raises(TypeError):
        loud.record("event", converged=True)


def test_an_event_keeps_its_counts() -> None:
    loud = Ledger(enabled=True)
    loud.record("sampled", samples=12, places=4)
    (event,) = loud.events()
    assert event.name == "sampled"
    assert event.counts == {"samples": 12, "places": 4}
    assert event.elapsed_ns is None


def test_a_span_lets_the_block_replace_its_declared_counts() -> None:
    loud = Ledger(enabled=True)
    with loud.span("raster", cells=0) as counted:
        counted["cells"] = 37
        counted["clipped"] = 2
    (event,) = loud.events()
    assert event.counts == {"cells": 37, "clipped": 2}


def test_timing_is_taken_only_when_asked_for() -> None:
    untimed = Ledger(enabled=True, timed=False)
    with untimed.span("work", steps=1):
        pass
    assert untimed.events()[0].elapsed_ns is None

    timed = Ledger(enabled=True, timed=True)
    with timed.span("work", steps=1):
        pass
    elapsed = timed.events()[0].elapsed_ns
    assert elapsed is not None and elapsed >= 0
    assert timed.events()[0].counts == {"steps": 1}


def test_totals_sum_counted_work_by_name() -> None:
    loud = Ledger(enabled=True)
    loud.record("one", samples=3, places=1)
    loud.record("two", samples=4)
    assert loud.totals() == {"samples": 7, "places": 1}


def test_recording_restores_the_previous_standing() -> None:
    """Turning telemetry on in one place must not leak into another."""
    assert not ledger.enabled
    with recording(timed=True) as run:
        assert run is ledger
        assert ledger.enabled and ledger.timed
        ledger.record("inside", steps=1)
        assert len(ledger.events()) == 1
    assert not ledger.enabled
    assert not ledger.timed


def test_recording_clears_so_a_block_sees_only_its_own_events() -> None:
    with recording() as first:
        first.record("a", steps=1)
    with recording() as second:
        assert second.events() == ()
        second.record("b", steps=1)
        assert [event.name for event in second.events()] == ["b"]
