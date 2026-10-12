"""Performance engineering is a first-order requirement, enforced rather than remembered.

The founder, 2026-10-11: "telemetry, JIT/C++/Rust, overall performance engineering is also a
first-order requirment of the pipeline. The SICP-centric design rules should slot in nicely here,
the competition itself scores for efficiency, so that's a first-order consideration, alongside the
image output and clean modular production-spec design"

The project's law attaches a compute contract to every numeric KERNEL (AGENTS.md override 2 and 3;
THESIS SS12.5, SS13.5), not to every stage -- `knee.study` is the impure I/O edge and runs no kernel.
So what is enforced here is that every contract which exists is COMPLETE: a contract that does not
name its reference, its proof gate, its allocation and its counted work licenses nothing, and a stub
contract is worse than none because it reads as a guarantee.
"""

import importlib
import pkgutil
from collections.abc import Mapping

import knee
from knee.compute.contracts import ComputeContract, contracted

# Every field is load-bearing. `language` records the computation shape's chosen language, which is
# the decision AGENTS.md override 3 makes at design time; `reference` names the plain implementation
# an accelerated twin must answer to under SAME; `proof_gate` names what would falsify the contract.
REQUIRED = (
    "kind",
    "language",
    "reads",
    "writes",
    "allocation",
    "work",
    "parallel_unit",
    "reference",
    "proof_gate",
)


def _contracts() -> list[tuple[str, ComputeContract]]:
    found: list[tuple[str, ComputeContract]] = []
    for stage in (m.name for m in pkgutil.iter_modules(knee.__path__) if m.ispkg):
        package = importlib.import_module(f"knee.{stage}")
        for info in pkgutil.walk_packages(package.__path__, prefix=f"knee.{stage}."):
            module = importlib.import_module(info.name)
            for name, value in vars(module).items():
                if isinstance(value, ComputeContract):
                    found.append((f"{info.name}.{name}", value))
    return found


def _modules() -> list[tuple[str, object]]:
    """Every module under knee/, with its namespace, for the two structural checks below."""
    found: list[tuple[str, object]] = []
    for stage in (m.name for m in pkgutil.iter_modules(knee.__path__) if m.ispkg):
        package = importlib.import_module(f"knee.{stage}")
        for info in pkgutil.walk_packages(package.__path__, prefix=f"knee.{stage}."):
            found.append((info.name, importlib.import_module(info.name)))
    return found


def _carried(value: object) -> list[int]:
    """The contract this callable carries, by identity, or nothing."""
    attached = getattr(value, "__dict__", None)
    if not isinstance(attached, Mapping):
        return []
    contract = attached.get("__contract__")
    return [id(contract)] if isinstance(contract, ComputeContract) else []


def unattached_contracts(namespace: Mapping[str, object]) -> list[str]:
    """Contracts declared in a namespace that no callable in it carries.

    This is the check three contracts survived without. `interiors`, `ledger` and
    `conversation` each declared `CONTRACT = ComputeContract(...)` and never applied it,
    while `places.json` reported `contract: true` and `contract_disagrees: none` -- both
    true at MODULE scale, and both blind to the fact that no function carried it. SS13.5
    wants a contract to be data attached to the measured function; an unattached module
    constant is a comment.

    Classes are searched as well as functions, because `Ledger.record` is where the
    telemetry ledger's contract belongs.
    """
    attached: list[int] = []
    for value in namespace.values():
        attached.extend(_carried(value))
        if isinstance(value, type):
            for member in vars(value).values():
                attached.extend(_carried(member))
    return sorted(
        name
        for name, value in namespace.items()
        if isinstance(value, ComputeContract) and id(value) not in attached
    )


def reference_twin_without_a_contract(namespace: Mapping[str, object]) -> bool:
    """Whether this namespace holds a reference/twin pair and declares no contract.

    The pair is recognised by the house's naming -- a `*_reference` kernel beside a
    `jit_*` builder -- which is a CONVENTION and not a proof. A twin that breaks the
    convention is invisible to this check, and that limit is stated rather than implied.
    """
    references = [
        name
        for name, value in namespace.items()
        if name.endswith("_reference") and callable(value)
    ]
    twins = [
        name
        for name, value in namespace.items()
        if name.startswith("jit_") and callable(value)
    ]
    if not (references and twins):
        return False
    return not any(isinstance(value, ComputeContract) for value in namespace.values())


def _probe() -> ComputeContract:
    return ComputeContract(
        kind="probe",
        language="python reference",
        reads="one int",
        writes="one int",
        allocation="none",
        work="one addition",
        parallel_unit="none",
        reference="kernel itself",
        proof_gate="this test",
    )


def test_every_declared_contract_reaches_its_kernel() -> None:
    """A contract that is declared and never attached links to nothing it describes."""
    offenders = [
        f"{name}.{declared}"
        for name, module in _modules()
        for declared in unattached_contracts(vars(module))
    ]
    assert not offenders, (
        f"these contracts are declared and attached to no callable: {offenders}. "
        "Apply it with @contracted(CONTRACT) to the kernel its `reference` field names."
    )


def test_every_reference_twin_pair_declares_a_contract() -> None:
    """A twin is admitted only against a named reference, so the pair owes a contract."""
    offenders = [
        name
        for name, module in _modules()
        if reference_twin_without_a_contract(vars(module))
    ]
    assert not offenders, (
        f"these modules hold a reference/twin pair and declare no contract: {offenders}"
    )


def test_the_unattached_check_catches_a_contract_nothing_carries() -> None:
    """The check itself is checked: it must fail on the shape it exists to refuse."""
    contract = _probe()

    def kernel(value: int) -> int:
        return value + 1

    bare = {"CONTRACT": contract, "kernel": kernel}
    assert unattached_contracts(bare) == ["CONTRACT"]
    attached = contracted(contract)(kernel)
    assert unattached_contracts({"CONTRACT": contract, "kernel": attached}) == []


def test_the_unattached_check_sees_a_contract_carried_by_a_method() -> None:
    """`Ledger.record` carries its module's contract, so a class member must count."""
    contract = _probe()

    class Holder:
        @contracted(contract)
        def record(self) -> None: ...

    assert unattached_contracts({"CONTRACT": contract, "Holder": Holder}) == []


def test_the_pair_check_catches_a_twin_whose_contract_was_removed() -> None:
    """The second check is checked the same way, both signs."""

    def thing_reference(value: int) -> int:
        return value

    def jit_thing() -> None: ...

    without = {"thing_reference": thing_reference, "jit_thing": jit_thing}
    assert reference_twin_without_a_contract(without)
    assert not reference_twin_without_a_contract({**without, "CONTRACT": _probe()})
    assert not reference_twin_without_a_contract({"thing_reference": thing_reference})


def test_the_pipeline_declares_compute_contracts() -> None:
    """At least the built numeric stages carry one, so the requirement cannot silently lapse."""
    assert _contracts(), "no compute contract is declared anywhere in knee/"


def test_no_compute_contract_is_a_stub() -> None:
    for where, contract in _contracts():
        for field in REQUIRED:
            value = getattr(contract, field)
            assert isinstance(value, str) and value.strip(), (
                f"{where}: {field} is empty"
            )
            assert len(value.strip()) > 3, (
                f"{where}: {field} is too short to mean anything"
            )


def test_every_contract_names_a_reference_and_a_proof_gate() -> None:
    """A twin is admitted only by a decision-preserving SAME harness against a named reference."""
    for where, contract in _contracts():
        assert "reference" in contract.reference or contract.reference, where
        assert contract.proof_gate, where
        # The reference must name something, not merely assert that one exists.
        assert any(character.isalpha() for character in contract.reference), (
            f"{where}: reference names nothing"
        )


def _import_module(path, name: str):
    """Import a module from a file, as the kernels' modules are imported, for the plain-form tests."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


KERNEL_MODULE = """
from knee.compute.contracts import ComputeContract, contracted

CONTRACT = ComputeContract(
    kind="probe", language="python reference", reads="one int", writes="one int",
    allocation="none", work="one addition", parallel_unit="none",
    reference="kernel", proof_gate="the plain-form test",
)


@contracted
def kernel(value: int) -> int:
    return value + 1
"""


def test_the_plain_form_reads_the_modules_one_contract_and_registers_the_kernel(
    tmp_path,
) -> None:
    """Task 7.11: `@contracted` with no argument attaches the module's `CONTRACT` as data, returns
    the kernel unwrapped, and records it under its dotted path."""
    from knee.compute.contracts import declared_contracts

    path = tmp_path / "plain_form_probe.py"
    path.write_text(KERNEL_MODULE)
    module = _import_module(path, "plain_form_probe")
    assert module.kernel(1) == 2
    assert module.kernel.__dict__["__contract__"] is module.CONTRACT
    assert declared_contracts()["plain_form_probe.kernel"] is module.CONTRACT
    assert unattached_contracts(vars(module)) == []


def test_the_plain_form_refuses_a_module_that_declares_no_contract(tmp_path) -> None:
    """MUST NOT: attach nothing silently. A kernel under `@contracted` in a module with no
    `CONTRACT`, or with something else under that name, is refused by name at import."""
    import pytest

    bare = tmp_path / "no_contract_probe.py"
    bare.write_text(
        "from knee.compute.contracts import contracted\n\n"
        "@contracted\ndef kernel(value: int) -> int:\n    return value\n"
    )
    with pytest.raises(ValueError, match="contract_undeclared"):
        _import_module(bare, "no_contract_probe")
    wrong = tmp_path / "wrong_contract_probe.py"
    wrong.write_text(
        "from knee.compute.contracts import contracted\n\nCONTRACT = 'not a contract'\n\n"
        "@contracted\ndef kernel(value: int) -> int:\n    return value\n"
    )
    with pytest.raises(ValueError, match="contract_undeclared"):
        _import_module(wrong, "wrong_contract_probe")


def test_the_plain_form_takes_only_a_function() -> None:
    import pytest

    with pytest.raises(TypeError, match="contracted_expects_a_function"):
        contracted("kernel")  # type: ignore[call-overload]


def test_re_declaring_the_same_contract_is_idempotent_and_a_different_one_is_refused(
    tmp_path,
) -> None:
    """A module reloaded re-declares what it declared; a second contract under one key is refused."""
    import pytest

    path = tmp_path / "reload_probe.py"
    path.write_text(KERNEL_MODULE)
    first = _import_module(path, "reload_probe")
    second = _import_module(path, "reload_probe")
    assert second.kernel.__dict__["__contract__"] == first.CONTRACT
    different = _probe()
    with pytest.raises(ValueError, match="duplicate_contract_key"):
        contracted(different)(second.kernel)


def test_contracts_are_data_and_never_wrap_the_measured_function() -> None:
    """SS13.5: attaching a contract must not put a wrapper on the hot path."""
    from knee.compute.contracts import contracted

    def kernel(value: int) -> int:
        return value + 1

    contract = ComputeContract(
        kind="probe",
        language="python reference",
        reads="one int",
        writes="one int",
        allocation="none",
        work="one addition",
        parallel_unit="none",
        reference="kernel itself",
        proof_gate="this test",
    )
    decorated = contracted(contract)(kernel)
    assert decorated is kernel, (
        "contracted() returned a wrapper; it must attach metadata only"
    )
    assert decorated.__dict__["__contract__"] is contract
