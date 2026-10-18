"""Record, for each benchmarked kernel, the costliest call the production path makes to it on the
proof study, for `benchmarks/test_kernels.py` to replay without the competition's files
(`benchmarks/recorded/`; how a call is stored and rebuilt: `benchmarks/recording.py`).

The recording needs those files. It runs the real entry point (`scripts/run_interiors.py`'s `main`, in
this process, one worker, drawing off, its records and printed report written to a temporary folder)
with each kernel wrapped wherever production holds its name; a run so wrapped makes the same records
as a plain run (`scripts/compare_receipts.py`, 2026-10-18). Each call keeps its arguments as passed and
as copied at the call, and a call whose arrays the run changed afterwards is kept as copied, as it was
at the call. Every call is then replayed once to warm up and once timed, and the one that took longest
is kept: where a change in the kernel's speed costs most. A kernel the run no longer calls stops the
recording by name. The manifest names the commit and the uncommitted changes the recording was made
from, and for each kernel which call it kept, how long that call took, how many calls the kernel had
in the run and how long all of them took.

An array whose values are whole numbers that uint16 holds, and that comes back from uint16 with the
same digest, is stored as uint16 (a series' voxels, handed to `background_split` as float64); every
other array is stored as passed. Rohan, 2026-10-18: «We shouldn't have hardcoded values, wire in the
ones we compute in the production path»; «Drop the requirements for study data»; «Obviously, GitHub
is for code, not for GB's of data».

Refresh it when the production path changes what it hands a kernel (FULL_BUILD_PLAN §9):

    .venv/bin/python benchmarks/record_calls.py
"""

from __future__ import annotations

import contextlib
import copy
import json
import platform
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pytest
from recording import (
    ARRAYS,
    KERNELS,
    MANIFEST,
    PROOF,
    RECORDED,
    Arguments,
    arrays_in,
    encoded,
)

from knee.receipt import digest

ROOT = Path(__file__).resolve().parents[1]
# One call as recorded: its arguments as passed, their copies at the call, and the digests of the
# passed arrays at the call.
Recorded = tuple[Arguments, Arguments, list[str]]


def as_passed(value: Any) -> Any:
    """An argument as it was at the call: an array as the very object passed, a tuple, list or dict
    rebuilt around its items, anything else copied whole."""
    if isinstance(value, np.ndarray):
        return value
    if isinstance(value, tuple):
        return tuple(as_passed(item) for item in value)
    if isinstance(value, list):
        return [as_passed(item) for item in value]
    if isinstance(value, dict):
        return {key: as_passed(item) for key, item in value.items()}
    return copy.deepcopy(value)


def at_the_call(value: Any) -> Any:
    """An argument copied at the call: an array with its dtype, memory order and read-only flag, a
    tuple, list or dict rebuilt around its items, anything else copied whole."""
    if isinstance(value, np.ndarray):
        copied = value.copy(order="K")
        copied.flags.writeable = value.flags.writeable
        return copied
    if isinstance(value, tuple):
        return tuple(at_the_call(item) for item in value)
    if isinstance(value, list):
        return [at_the_call(item) for item in value]
    if isinstance(value, dict):
        return {key: at_the_call(item) for key, item in value.items()}
    return copy.deepcopy(value)


def recorder(function: Callable[..., Any], kept: list[Recorded]) -> Callable[..., Any]:
    """`function`, keeping each call's arguments as passed and as copied at the call."""

    def recording(*args: Any, **kwargs: Any) -> Any:
        passed = (as_passed(args), as_passed(kwargs))
        digests = [digest(array) for array in arrays_in(passed)]
        kept.append((passed, (at_the_call(args), at_the_call(kwargs)), digests))
        return function(*args, **kwargs)

    return recording


def holders() -> list[ModuleType]:
    """The modules production looks the kernels up in: the run's own and every module of `knee`."""
    return [
        module
        for name, module in list(sys.modules.items())
        if isinstance(module, ModuleType)
        and (
            name == "scripts.run_interiors"
            or name == "knee"
            or name.startswith("knee.")
        )
    ]


def production_calls(out: Path) -> dict[str, list[Recorded]]:
    """Every call the production run on the proof study makes to each kernel."""
    sys.path.insert(0, str(ROOT))
    from scripts import run_interiors as run

    if not (run.KAGGLE_ROOT.is_dir() or (run.ROOT / run.LOCAL_ROOT).is_dir()):
        raise SystemExit(
            "the recording needs the competition's files, and they are not on this machine"
        )
    kept: dict[str, list[Recorded]] = {name: [] for name in KERNELS}
    with pytest.MonkeyPatch.context() as patch:
        for name, function in KERNELS.items():
            wrapper = recorder(function, kept[name])
            for module in holders():
                for attribute, value in list(vars(module).items()):
                    if value is function:
                        patch.setattr(module, attribute, wrapper)
        patch.setattr(
            sys,
            "argv",
            [
                "run_interiors.py",
                "--study-uid",
                PROOF,
                "--workers",
                "1",
                "--run",
                str(out / "interiors"),
                "--main-run",
                str(out / "main"),
                "--out",
                str(out / "pictures" / "interiors"),
                "--assignments-out",
                str(out / "pictures" / "assignments"),
                "--main-out",
                str(out / "pictures" / "main"),
            ],
        )
        with (
            (out / "run-report.txt").open("w", encoding="utf-8") as report,
            contextlib.redirect_stdout(report),
        ):
            run.main()
    return kept


def as_replayed(recorded: list[Recorded]) -> list[Arguments]:
    """Each call as passed when the run left its arrays as they were, else as copied at the call."""
    return [
        passed if [digest(array) for array in arrays_in(passed)] == digests else copied
        for passed, copied, digests in recorded
    ]


def costliest(
    kernel: Callable[..., Any], calls: list[Arguments]
) -> tuple[int, float, float]:
    """Which call took longest, replayed once to warm up and once timed; how long it took; and how
    long all of them took."""
    for args, kwargs in calls:
        kernel(*args, **kwargs)
    seconds: list[float] = []
    for args, kwargs in calls:
        start = time.perf_counter()
        kernel(*args, **kwargs)
        seconds.append(time.perf_counter() - start)
    index = max(range(len(seconds)), key=seconds.__getitem__)
    return index, seconds[index], sum(seconds)


def stored_form(key: str, array: np.ndarray) -> np.ndarray:
    """An array's values as `arrays.npz` keeps them: as uint16 when they are whole numbers uint16
    holds and come back from it with the array's digest, `key`; else as passed, contiguous."""
    if (
        array.dtype.kind == "f"
        and array.size
        and bool(np.isfinite(array).all())
        and array.min() >= 0
        and array.max() <= np.iinfo(np.uint16).max
    ):
        narrow = array.astype(np.uint16)
        if digest(narrow.astype(array.dtype)) == key:
            return narrow
    return np.ascontiguousarray(array)


def git(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout


def main() -> None:
    commit = git("rev-parse", "HEAD").strip()
    uncommitted = [line for line in git("status", "--porcelain").splitlines() if line]
    with tempfile.TemporaryDirectory() as folder:
        kept = production_calls(Path(folder))
    uncalled = [name for name, calls in kept.items() if not calls]
    if uncalled:
        raise SystemExit(
            f"the production run on the proof study made no call to {', '.join(uncalled)}"
        )
    arrays: dict[str, np.ndarray] = {}
    kernels: dict[str, dict[str, Any]] = {}
    for name, recorded in kept.items():
        calls = as_replayed(recorded)
        index, seconds, total = costliest(KERNELS[name], calls)
        args, kwargs = calls[index]
        kernels[name] = {
            "calls_in_the_run": len(calls),
            "kept_call": index,
            "kept_call_seconds": seconds,
            "all_calls_seconds": total,
            "args": encoded(args, arrays),
            "kwargs": encoded(kwargs, arrays),
        }
    stored = {key: stored_form(key, array) for key, array in arrays.items()}
    RECORDED.mkdir(exist_ok=True)
    np.savez_compressed(ARRAYS, allow_pickle=False, **stored)
    manifest = {
        "study": PROOF,
        "commit": commit,
        "uncommitted": uncommitted,
        "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": platform.platform(),
        "kernels": kernels,
        "arrays": {
            key: {
                "passed_dtype": array.dtype.str,
                "stored_dtype": stored[key].dtype.str,
                "bytes_passed": array.nbytes,
            }
            for key, array in arrays.items()
        },
    }
    MANIFEST.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    for name, entry in kernels.items():
        print(
            f"{name}: kept call {entry['kept_call'] + 1} of {entry['calls_in_the_run']},"
            f" {entry['kept_call_seconds']:.4f} s of the kernel's"
            f" {entry['all_calls_seconds']:.4f} s on the study"
        )
    print(
        f"recorded from {commit} ({len(uncommitted)} uncommitted changes listed);"
        f" {len(arrays)} arrays, {ARRAYS.stat().st_size / 2**20:.2f} MiB stored"
    )


if __name__ == "__main__":
    main()
