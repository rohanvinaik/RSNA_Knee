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

import knee
from knee.compute.contracts import ComputeContract

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
