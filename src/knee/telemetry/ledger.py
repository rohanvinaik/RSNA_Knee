"""The run's ledger: named events carrying counted work. Stdlib only, off by default."""

from __future__ import annotations

from collections.abc import Generator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field

from knee.compute.contracts import ComputeContract, contracted

CONTRACT = ComputeContract(
    kind="run_ledger_of_counted_work",
    language="pure Python stdlib; no profiler, no structlog, no OpenTelemetry on this path",
    reads="names and integer counts supplied by a stage; nothing of the study",
    writes="an append-only list of immutable Events held in memory",
    allocation="O(events); a disabled ledger allocates nothing at all",
    work="one list append per recorded event; no formatting until a reader asks",
    parallel_unit="one ledger per run, not shared across threads",
    reference="Ledger.record and Ledger.events are themselves the reference",
    proof_gate="tests/test_telemetry.py: disabled records nothing; counts must be whole",
)


@dataclass(frozen=True, slots=True)
class Event:
    """One thing a stage did, with the work it counted doing it.

    `counts` is deterministic counted work -- samples taken, places visited, cells written -- and is
    evidence.
    """

    name: str
    counts: Mapping[str, int]


@dataclass(slots=True)
class Ledger:
    """Collects events for one run. Disabled by default, and silent when disabled."""

    enabled: bool = False
    _events: list[Event] = field(default_factory=list)

    @contracted
    def record(self, name: str, /, **counts: int) -> None:
        """Record one event. Returns immediately and allocates nothing when disabled.

        Counts are whole, non-negative work. A bool is refused explicitly: `True` is an `int` in
        Python, and a flag silently summed as 1 would corrupt a budget.
        """
        if not self.enabled:
            return
        if not name:
            raise ValueError("event_name_required")
        for key, value in counts.items():
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"counted work must be a whole number: {key}={value!r}")
            if value < 0:
                raise ValueError(f"counted work must not be negative: {key}={value}")
        self._events.append(Event(name, dict(counts)))

    def events(self) -> tuple[Event, ...]:
        """Everything recorded, in order. A reader formats; the ledger never does."""
        return tuple(self._events)

    def totals(self) -> dict[str, int]:
        """Counted work summed across every event, by count name."""
        summed: dict[str, int] = {}
        for event in self._events:
            for key, value in event.counts.items():
                summed[key] = summed.get(key, 0) + value
        return summed

    def clear(self) -> None:
        self._events.clear()


ledger = Ledger()
"""The process-wide ledger. A stage records to this; a caller enables it."""


@contextmanager
def recording() -> Generator[Ledger]:
    """Enable the process-wide ledger for a block, then restore what it was.

    The ledger is cleared on entry so a block's events are its own, and the previous standing is
    restored on exit, so turning telemetry on in one place cannot leak into another.
    """
    was_enabled = ledger.enabled
    ledger.clear()
    ledger.enabled = True
    try:
        yield ledger
    finally:
        ledger.enabled = was_enabled
