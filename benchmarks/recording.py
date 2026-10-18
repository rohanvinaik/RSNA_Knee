"""The benchmarked kernels and the one call of each that the benchmarks replay: how a call the
production path makes is stored in `benchmarks/recorded/`, and how it is rebuilt exactly.

`benchmarks/record_calls.py` writes the recording, from the production run on the proof study, where
the competition's files are; `benchmarks/test_kernels.py` replays it and needs none of them. A call is
stored as it was passed: each array under its digest (`knee.receipt.digest`: its dtype, shape and
bytes) with its strides and read-only flag, since numba compiles a separate version of a kernel for
each layout and flag; a tuple, list, dict or dataclass by its items; a number, a string, None or a
numpy scalar as itself. Anything else stops the recording by its type. An array is rebuilt from its
stored values with the strides and flag it had and checked against the digest it had at the call, so
a replay is handed what production handed the kernel, value for value and layout for layout. An array
held by several arguments (a slice's plane, handed to a kernel and kept in its `Measures`) is rebuilt
once and handed to each.
"""

from __future__ import annotations

import dataclasses
import importlib
import json
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from knee.collapse.coarse_section import coarse_depth
from knee.collapse.noise import background_split
from knee.collapse.physical import physical_squint
from knee.collapse.profile import block_medians
from knee.objects.assignments import (
    dark_bands,
    enclosed_darkness,
    local_lightness,
    thick_parts,
)
from knee.objects.interiors import interior_regions
from knee.receipt import digest

RECORDED = Path(__file__).resolve().parent / "recorded"
MANIFEST = RECORDED / "manifest.json"
ARRAYS = RECORDED / "arrays.npz"
# The project's proof study (FULL_BUILD_PLAN §0, grounding step 3).
PROOF = "1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149"
KERNELS: dict[str, Callable[..., Any]] = {
    "interior_regions": interior_regions,
    "physical_squint": physical_squint,
    "block_medians": block_medians,
    "coarse_depth": coarse_depth,
    "enclosed_darkness": enclosed_darkness,
    "dark_bands": dark_bands,
    "local_lightness": local_lightness,
    "thick_parts": thick_parts,
    "background_split": background_split,
}
Arguments = tuple[tuple[Any, ...], dict[str, Any]]
# An array's identity when rebuilt: its digest, dtype, shape, strides and read-only flag.
Layout = tuple[str, str, tuple[int, ...], tuple[int, ...], bool]


@dataclass(frozen=True)
class Call:
    """A kept call, rebuilt: its arguments, the digests its arrays had at the call (in `arrays_in`'s
    order), and what the recording says of it: which of the run's calls it was, and how long it and
    all of the kernel's calls took when it was recorded."""

    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    digests: tuple[str, ...]
    index: int
    calls_in_the_run: int
    seconds: float
    all_calls_seconds: float


@dataclass(frozen=True)
class Recording:
    """Where the recording came from (the commit, and the working tree's uncommitted changes as
    `git status --porcelain` listed them) and each kernel's kept call."""

    commit: str
    uncommitted: tuple[str, ...]
    recorded_at: str
    calls: dict[str, Call]


def arrays_in(value: Any) -> Iterator[np.ndarray]:
    """The arrays among a call's arguments, in order, those a dataclass holds included."""
    if isinstance(value, np.ndarray):
        yield value
    elif isinstance(value, (tuple, list)):
        for item in value:
            yield from arrays_in(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from arrays_in(item)
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        for field in dataclasses.fields(value):
            yield from arrays_in(getattr(value, field.name))


def encoded(value: Any, arrays: dict[str, np.ndarray]) -> Any:
    """An argument as the manifest holds it, each array kept in `arrays` under its digest."""
    if isinstance(value, np.ndarray):
        if any(step < 0 for step in value.strides) or (
            value.itemsize and any(step % value.itemsize for step in value.strides)
        ):
            raise ValueError(
                f"an array with strides {value.strides} cannot be rebuilt from its values"
            )
        key = digest(value)
        arrays.setdefault(key, value)
        return {
            "array": key,
            "dtype": value.dtype.str,
            "shape": list(value.shape),
            "strides": list(value.strides),
            "writeable": bool(value.flags.writeable),
        }
    if isinstance(value, np.generic):
        return {"scalar": value.dtype.str, "value": value.item()}
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, tuple):
        return {"tuple": [encoded(item, arrays) for item in value]}
    if isinstance(value, list):
        return {"list": [encoded(item, arrays) for item in value]}
    if isinstance(value, dict):
        return {
            "dict": [
                [encoded(key, arrays), encoded(item, arrays)]
                for key, item in value.items()
            ]
        }
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        kind = type(value)
        fields = dataclasses.fields(value)
        if not all(field.init for field in fields):
            raise TypeError(
                f"a {kind.__name__} has fields its constructor does not take, so it cannot be"
                " rebuilt from its fields"
            )
        return {
            "dataclass": f"{kind.__module__}:{kind.__qualname__}",
            "fields": {
                field.name: encoded(getattr(value, field.name), arrays)
                for field in fields
            },
        }
    raise TypeError(f"a {type(value).__name__} argument cannot be recorded")


def array_of(
    entry: dict[str, Any],
    stored: Mapping[str, np.ndarray],
    made: dict[Layout, np.ndarray],
    keys: list[str],
) -> np.ndarray:
    """An array rebuilt from its stored values with its recorded dtype, shape, strides and read-only
    flag, and checked against its digest at the call. Its digest is added to `keys`."""
    key = entry["array"]
    keys.append(key)
    dtype = np.dtype(entry["dtype"])
    shape = tuple(entry["shape"])
    strides = tuple(entry["strides"])
    layout: Layout = (key, dtype.str, shape, strides, bool(entry["writeable"]))
    if layout in made:
        return made[layout]
    span = (
        1
        + sum(
            (size - 1) * step // dtype.itemsize
            for size, step in zip(shape, strides, strict=True)
        )
        if all(shape)
        else 0
    )
    array = np.ndarray(
        shape, dtype=dtype, buffer=np.zeros(span, dtype=dtype), strides=strides
    )
    array[...] = stored[key]
    if not entry["writeable"]:
        array.flags.writeable = False
    if digest(array) != key:
        raise ValueError(f"the array rebuilt for {key} is not the one recorded")
    made[layout] = array
    return array


def rebuilt(
    value: Any,
    stored: Mapping[str, np.ndarray],
    made: dict[Layout, np.ndarray],
    keys: list[str],
) -> Any:
    """An argument rebuilt from the manifest's form of it and the stored arrays, each array's digest
    added to `keys` in `arrays_in`'s order."""
    if not isinstance(value, dict):
        return value
    if "array" in value:
        return array_of(value, stored, made, keys)
    if "scalar" in value:
        return np.dtype(value["scalar"]).type(value["value"])
    if "tuple" in value:
        return tuple(rebuilt(item, stored, made, keys) for item in value["tuple"])
    if "list" in value:
        return [rebuilt(item, stored, made, keys) for item in value["list"]]
    if "dict" in value:
        return {
            rebuilt(key, stored, made, keys): rebuilt(item, stored, made, keys)
            for key, item in value["dict"]
        }
    if "dataclass" in value:
        module, _, qualname = value["dataclass"].partition(":")
        kind: Any = importlib.import_module(module)
        for part in qualname.split("."):
            kind = getattr(kind, part)
        return kind(
            **{
                name: rebuilt(item, stored, made, keys)
                for name, item in value["fields"].items()
            }
        )
    raise ValueError(
        f"the manifest holds an argument of no known kind: {sorted(value)}"
    )


def load() -> Recording:
    """The recording, each kept call rebuilt and checked. It must hold exactly the benchmarked
    kernels."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    recorded, benchmarked = set(manifest["kernels"]), set(KERNELS)
    if recorded != benchmarked:
        raise ValueError(
            f"the recording holds {sorted(recorded - benchmarked)}, which are not benchmarked,"
            f" and lacks {sorted(benchmarked - recorded)}: run benchmarks/record_calls.py where"
            " the competition's files are"
        )
    made: dict[Layout, np.ndarray] = {}
    calls: dict[str, Call] = {}
    with np.load(ARRAYS) as stored:
        for name, entry in manifest["kernels"].items():
            keys: list[str] = []
            args = rebuilt(entry["args"], stored, made, keys)
            kwargs = rebuilt(entry["kwargs"], stored, made, keys)
            calls[name] = Call(
                args=args,
                kwargs=kwargs,
                digests=tuple(keys),
                index=entry["kept_call"],
                calls_in_the_run=entry["calls_in_the_run"],
                seconds=entry["kept_call_seconds"],
                all_calls_seconds=entry["all_calls_seconds"],
            )
    return Recording(
        commit=manifest["commit"],
        uncommitted=tuple(manifest["uncommitted"]),
        recorded_at=manifest["recorded_at"],
        calls=calls,
    )


def unchanged(call: Call) -> bool:
    """Whether every array the call holds still has the digest it had at the call."""
    return (
        tuple(digest(array) for array in arrays_in((call.args, call.kwargs)))
        == call.digests
    )
