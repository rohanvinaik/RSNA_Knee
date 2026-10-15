"""Computed once: a value made the first time a stage asks for it, then handed to every stage that
asks after it, for one study; each making and each handing-on counted on the ledger.

The founder, 2026-10-15: «Repeated work is a scourge, it's an artifact of you being myopic about the
codebase» and «ALL repetitious operations need to be centralized and deduplicated across the whole
codebase. That's why I have a "Telemetry" folder for centralized compute tracking». A value two
stages need -- a slice's frame, its black margin, the match of one slice's places onto its twin's,
the leg's bones on an axial slice, the lens read on a slice -- is asked of `once` by its kind and
the key that names its inputs: the first asker's `make` runs and the value is kept; every later
asker is handed that same value, and nothing is made twice.

The scope is one study (`computing`), entered where the study is measured, so a worker that measures
many studies keeps nothing from one to the next. Outside a scope every ask makes its value and keeps
nothing, so a test or a single call sees no state. A value kept is handed on as it is: a stage that
needs to change one changes a copy, as every stage here already does with the names a slice made.

The ledger records `<kind>.made` for each value made and `<kind>.handed_on` for each later ask a kept
one answered, so the receipt says, kind by kind, what was computed and how often it was shared.
"""

from __future__ import annotations

from collections.abc import Callable, Generator, Hashable
from contextlib import contextmanager
from typing import TypeVar, cast

from knee.compute.contracts import ComputeContract, contracted
from knee.telemetry.ledger import ledger

CONTRACT = ComputeContract(
    kind="computed_once_store",
    language="pure Python stdlib; no cache library on this path",
    reads="a kind, a hashable key naming the value's inputs, and the stage's own maker",
    writes="one dict entry per value made inside a study's scope; nothing outside one",
    allocation="O(values kept) for one study; released when the study's scope ends",
    work="one dict lookup per ask; the maker runs once per kind and key within a scope",
    parallel_unit="one store per process, one study at a time",
    reference="once",
    proof_gate="tests/test_telemetry.py: inside a scope a key's maker runs once and every later "
    "ask is handed that value; outside one nothing is kept; each scope starts empty",
)

T = TypeVar("T")

# The values kept for the study being measured, by (kind, key); None outside a study's scope.
_kept: dict[tuple[str, Hashable], object] | None = None


@contracted
def once(kind: str, key: Hashable, make: Callable[[], T]) -> T:
    """The value of `kind` for `key`: made by `make` the first time it is asked for within the
    study's scope and kept, then handed to every later asker; made and not kept outside a scope.
    The ledger records `<kind>.made` or `<kind>.handed_on`."""
    if _kept is None:
        ledger.record(f"{kind}.made")
        return make()
    whole = (kind, key)
    if whole in _kept:
        ledger.record(f"{kind}.handed_on")
        return cast(T, _kept[whole])
    value = make()
    _kept[whole] = value
    ledger.record(f"{kind}.made")
    return value


@contextmanager
def computing() -> Generator[None]:
    """One study's scope: values made inside it are kept for it, and released when it ends; the
    scope that was open before is restored, so scopes never leak into each other."""
    global _kept
    was = _kept
    _kept = {}
    try:
        yield
    finally:
        _kept = was
