"""Compute contracts are data; attaching one never wraps the measured function (§13.5)."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

import numpy as np

F = TypeVar("F", bound=Callable)


@dataclass(frozen=True, slots=True)
class ComputeContract:
    kind: str
    language: str
    reads: str
    writes: str
    allocation: str
    work: str
    parallel_unit: str
    reference: str
    proof_gate: str
    source: str = "What an <Object> Is §13.5; compute-build-codex.md"


def contracted(contract: ComputeContract) -> Callable[[F], F]:
    def attach(function: F) -> F:
        # Functions carry metadata without a wrapper, as required by §13.5.
        function.__dict__["__contract__"] = contract
        return function

    return attach


def handed_on(array: np.ndarray) -> np.ndarray:
    """Freeze newly owned output storage. Never call this on a caller's source array."""
    array.setflags(write=False)
    return array
