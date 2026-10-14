"""COMPUTE: the project-wide compute discipline, below every stage.

Not a stage of the route. This is the layer the stages stand on, and nothing here knows what a knee
is. It was pulled out of `knee.collapse` on 2026-10-11 at the founder's word -- "The ComputeContract,
again, is much the same, got thrown into that junk pile instead of being organized properly."

What lives here:

    contracts.py   ComputeContract, the declaration every numeric kernel carries (SS12.5, SS13.5);
                   `contracted`, which attaches it as DATA, records the kernel in the registry
                   `declared_contracts` reads (task 7.3: the receipt carries every contract beside
                   the ledger's counted work), and returns the function unwrapped so nothing sits
                   on the hot path; and `handed_on`, which freezes newly owned output storage so a
                   consumer cannot write through a reading it was handed.

A contract states kind, language, reads, writes, allocation, work, parallel_unit, reference and
proof_gate. `language` is the computation shape's chosen language, decided at design time
(AGENTS.md override 3): Python orchestrates; NumPy for vectorizable maps; Numba for custom repeated
loops on the kernel path; C for cache-hostile build-time kernels; Rust for the case-memory scan.
`reference` names the plain implementation an accelerated twin must answer to under SAME, and
`proof_gate` names what would falsify the contract.

The standard is docs/STAGE_CONTRACT.md. `tests/knee/test_compute_contracts.py` fails the gate on a
stub, because a contract that names no reference and no proof gate licenses nothing while reading as
a guarantee.
"""

from knee.compute.contracts import (
    ComputeContract,
    contracted,
    declared_contracts,
    handed_on,
)

__all__ = ["ComputeContract", "contracted", "declared_contracts", "handed_on"]
