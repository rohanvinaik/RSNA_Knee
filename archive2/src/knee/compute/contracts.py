"""Compute contracts are data; attaching one never wraps the measured function (§13.5).

THE ONE FORM (task 0.3, the founder: "I guess only one? … the bigger risk is you forgetting that
there are two formats"; respelled under task 7.11): a module declares its contract once, at module
level, as `CONTRACT = ComputeContract(...)`, and applies it to the reference kernel its `reference`
field names with the PLAIN decorator, `@contracted`. The decorator reads the module's `CONTRACT`
itself. Why plain and not `@contracted(CONTRACT)`: measured 2026-10-12
(`docs/chapters/02-collapse/measurements/detective-call-form-decorator-20261012.md`), a decorator
applied in call form makes Detective add mutants it cannot build and return UNGATEABLE for ANY
function under it, so every kernel's standing was the decorator's and not the kernel's. Every site
migrated on 2026-10-12; the call form is retired and refused by name, and `scripts/places.py`
reports any site that still spells it.

`contracted` also records each kernel it decorates in a registry keyed by the kernel's dotted path,
`<module>.<qualname>`, so a tool can read every declared contract from one place instead of
importing the kernels and asking each what it carries (task 7.3). Recording is bookkeeping beside
the function: the function is returned as it was given, and calling it costs nothing more.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import FunctionType, MappingProxyType
from typing import TypeVar

import numpy as np

# A function or a method defined in a class body: the two things a contract is attached to, which
# have a dotted path to be keyed by and a `__dict__` to carry the contract.
F = TypeVar("F", bound=FunctionType)


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


# Every kernel `contracted` has decorated, by `<module>.<qualname>`. Only `contracted` writes it,
# and readers get a read-only view from `declared_contracts`.
_DECLARED: dict[str, ComputeContract] = {}


def _attach(function: F, contract: ComputeContract) -> F:
    """Attach `contract` to `function` as data, record it, and return the function unwrapped."""
    key = f"{function.__module__}.{function.__qualname__}"
    if key in _DECLARED and _DECLARED[key] != contract:
        # One key is one kernel: two kernels that share a path, or one kernel declared under
        # two contracts, would leave a contract that describes the wrong one. Refused before
        # anything is attached. The SAME contract under the same key is not that: a module
        # reloaded, or a decorated definition executed again in one interpreter (a test body,
        # a mutation run), re-declares what was declared, and that is idempotent.
        error = ValueError("duplicate_contract_key")
        error.add_note(f"key: {key}")
        raise error
    # Functions carry metadata without a wrapper, as required by §13.5.
    function.__dict__["__contract__"] = contract
    _DECLARED[key] = contract
    return function


def contracted(target: F) -> F:
    """The one form: `@contracted` on the reference kernel reads the module's `CONTRACT`.

    It takes the function and finds `CONTRACT` in the function's own module globals; a module
    that declares none, or declares something that is not a `ComputeContract`, is refused by name
    (`contract_undeclared`), because a kernel without a declared contract is exactly what this
    decorator exists to make impossible. The call form, `@contracted(CONTRACT)`, is retired (task
    7.11, every site migrated 2026-10-12) and refused by name, `contracted_call_form_retired`, so
    the spelling that made Detective return UNGATEABLE cannot come back unnoticed.
    """
    if isinstance(target, ComputeContract):
        error = TypeError("contracted_call_form_retired")
        error.add_note(
            "apply the plain `@contracted` and declare `CONTRACT` at module level (task 7.11)"
        )
        raise error
    if not isinstance(target, FunctionType):
        raise TypeError("contracted_expects_a_function")
    contract = target.__globals__.get("CONTRACT")
    if not isinstance(contract, ComputeContract):
        error = ValueError("contract_undeclared")
        error.add_note(f"module: {target.__module__}; kernel: {target.__qualname__}")
        raise error
    return _attach(target, contract)


def declared_contracts() -> Mapping[str, ComputeContract]:
    """Every contract attached so far, by the kernel's dotted path, in the order they were declared.

    A read-only view of the registry, not a copy: a kernel declared after the call appears in it.
    A module that has not been imported has declared nothing, so what this holds is what the
    running process has imported.
    """
    return MappingProxyType(_DECLARED)


def handed_on(array: np.ndarray) -> np.ndarray:
    """Freeze newly owned output storage. Never call this on a caller's source array."""
    array.setflags(write=False)
    return array
