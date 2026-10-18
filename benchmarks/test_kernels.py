"""Benchmarks of the run's costly kernels, each on the costliest call the production path made to it on
the proof study, rebuilt exactly from `benchmarks/recorded/`.

`benchmarks/record_calls.py` makes the recording from the real entry point, where the competition's
files are; the replays need none of them, so they run in the gate here and on GitHub, and under
CodSpeed (`.github/workflows/codspeed.yml`). Each call is rebuilt with every array's dtype, shape,
strides and read-only flag and checked against the digests its arrays had at the call
(`benchmarks/recording.py`). A replay runs once before it is measured, so compilation and first touch
are not measured, and it must leave its inputs as they were; both are done outside the measured call.
Rohan, 2026-10-18: «We shouldn't have hardcoded values, wire in the ones we compute in the production
path»; «Drop the requirements for study data».

What is replayed is one call per kernel, the costliest when the recording was made, from the commit
the manifest names: not a kernel's whole cost on the study, and not what the production path hands
the kernel today if that has changed since (refresh the recording then: FULL_BUILD_PLAN §9). The
kernels call one another (`dark_bands` runs `thick_parts`, `coarse_depth` runs `enclosed_darkness`),
so their figures overlap and do not add up. What a kernel costs is information, never a target
(FULL_BUILD_PLAN §14.3, M21).

With `--memray`, each replay's memory at its peak is measured; with `--fail-on-increase` as well, a
replay holding more at its peak than at its last successful run on this machine fails (pytest keeps
the runs in `.pytest_cache/`). memray compares a replay with a limit, and the limit given is this
machine's own memory, so it never fails a replay by itself.

    .venv/bin/python -m pytest benchmarks -rP
    .venv/bin/python -m pytest benchmarks -rP --memray --most-allocations=0 --fail-on-increase
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any

import pytest
from recording import KERNELS, Call, Recording, load, unchanged


@pytest.fixture(scope="session")
def recording() -> Recording:
    """Every kept call, rebuilt and checked against its digests."""
    return load()


@pytest.fixture
def call(recording: Recording, name: str) -> Iterator[Call]:
    """The kernel's kept call, replayed once before the test, and checked before and after it: the
    kernel must leave its inputs as they were."""
    kept = recording.calls[name]
    KERNELS[name](*kept.args, **kept.kwargs)
    assert unchanged(kept), f"{name} changed its inputs when replayed"
    yield kept
    assert unchanged(kept), f"{name} changed its inputs when replayed"


@pytest.fixture
def memory_limit(request: pytest.FixtureRequest) -> None:
    """With `--memray`, memray's limit for the replay: this machine's own memory, so that
    `--fail-on-increase` compares the replay with its last successful run."""
    if request.config.getoption("memray"):
        physical = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
        request.node.add_marker(pytest.mark.limit_memory(f"{physical} B"))


@pytest.mark.parametrize("name", list(KERNELS))
@pytest.mark.usefixtures("memory_limit")
def test_kernel_on_its_costliest_production_call(
    benchmark: Any, recording: Recording, call: Call, name: str
) -> None:
    """One kernel's costliest call from the production run on the proof study, replayed with the
    arguments production passed."""
    print(
        f"{name}: call {call.index + 1} of the {call.calls_in_the_run} the production run on the"
        f" proof study made, recorded from {recording.commit}"
        f"{' with uncommitted changes' if recording.uncommitted else ''}"
        f" on {recording.recorded_at}; it took {call.seconds:.4f} s of the kernel's"
        f" {call.all_calls_seconds:.4f} s on the study then"
    )
    benchmark(KERNELS[name], *call.args, **call.kwargs)
