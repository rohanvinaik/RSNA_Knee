"""The slab rule over arrays: a plain reference and a Numba twin that answers to the scalar rule.

WHY THIS EXISTS (task 7.10 of `every-stage-renders`). `knee.vectors.bundles` asks, for every claimed
place of the selected plane and for every OTHER acquisition, what that acquisition's slabs did about
the place. It used to ask the scalar `slab_code` one call at a time. Measured 2026-10-12 on the real
study, the through-plane bank called the scalar rule 1,888,948 times, from a generator, and those
calls cost 2.75 s of the 5.47 s `run_study` takes. The decision is cheap; the cost is the Python call.

The house rule (AGENTS.md, project override 2) is a reference first, then an accelerated twin that
answers to SAME. The founder, 2026-10-12, on this finding: "yeah, JIT/C++ for memory management".
The loop is a custom repeated loop on the kernel path, which override 3 gives to Numba; it is not
memory-bound, so C is not what it needs.

WHAT IS HERE. The scalar rule, `knee.lenses.slabs.slab_code`, stays the ONE decision and the oracle.
This module restates its arithmetic over arrays, in the same order and with the same comparisons,
and answers with indices into the oracle's own `SLAB_CODES`, so a code is named in one place and an
index can never mean something the rule does not. Nothing here is a second rule:
`tests/knee/lenses/test_slab_kernels.py` pins it to `slab_code` element by element, on every
boundary the rule names and in both in-plane states.

    slab_codes_reference   a plain Python loop: the contracted kernel, and the body the twin compiles
    jit_slab_kernel        that same body under Numba (`cache=True, nogil=True, fastmath=False`)
    slab_codes             the one entry: validates the arrays, selects the backend by name, and
                           hands back an owned, read-only uint8 array

The twin is the reference body compiled, not a second implementation, and `fastmath=False` keeps
every comparison IEEE, so a signed zero, the half-thickness, the half-pitch and a NaN offset fall on
the same side in both. A backend outside the registry is refused as `invalid_backend`, and one that
is in it but not installed as `required_backend_unavailable:jit`: the reference is never run in
place of a backend that was asked for.
"""

import math
from functools import lru_cache

import numpy as np

from knee.compute.contracts import ComputeContract, contracted, handed_on
from knee.lenses.slabs import SLAB_CODES

CONTRACT = ComputeContract(
    kind="slab_codes_per_place",
    language="Python reference / Numba strict twin (fastmath=False, nogil=True)",
    reads="offset_mm float64 (N,) signed offsets along the slice normal; thickness_mm and spacing_mm scalars in mm; in_plane bool (N,)",
    writes="owned read-only uint8 (N,) indices into SLAB_CODES; inputs unwritten",
    allocation="N bytes of output; constant scalar scratch",
    work="N evaluations of the slab rule's arithmetic, O(N), counted in the ledger as slab_places",
    parallel_unit="independent place; serial reference and twin",
    reference="slab_codes_reference",
    proof_gate="element-wise SAME against the scalar slab_code on every boundary it names, both in-plane flags, in tests/knee/lenses/test_slab_kernels.py; the twin is the reference body compiled",
)

# Where each code the scalar rule names sits in `SLAB_CODES`, read from the oracle's own vocabulary
# once, here. Numba freezes module-level integers as constants, which is why the kernel below names
# these and never indexes the tuple of strings.
_MEASURED = SLAB_CODES.index("measured")
_IN_GAP = SLAB_CODES.index("in_gap")
_NOT_THIS_SLICE = SLAB_CODES.index("not_this_slice")
_OUTSIDE_FRAME = SLAB_CODES.index("outside_frame")
_INVALID_GEOMETRY = SLAB_CODES.index("invalid_geometry")


@contracted
def slab_codes_reference(offset_mm, thickness_mm, spacing_mm, in_plane):
    """`slab_code` place by place, as indices into `SLAB_CODES`; the body the twin compiles.

    Self-contained on purpose: it calls neither `slab_code` nor `half_thickness`, because a plain
    Python callee does not compile. Beyond allocating its output it uses only `math.isfinite`,
    `abs`, comparisons and array indexing. The geometry is tested inside the loop, in `slab_code`'s
    own order, and not hoisted.
    """
    codes = np.zeros(len(offset_mm), dtype=np.uint8)
    for place in range(len(offset_mm)):
        offset = offset_mm[place]
        if (
            not math.isfinite(offset)
            or not math.isfinite(thickness_mm)
            or not math.isfinite(spacing_mm)
            or spacing_mm <= 0.0
            or thickness_mm / 2.0 <= 0.0
        ):
            codes[place] = _INVALID_GEOMETRY
        elif not in_plane[place]:
            codes[place] = _OUTSIDE_FRAME
        else:
            distance = abs(offset)
            if distance <= thickness_mm / 2.0:
                codes[place] = _MEASURED
            elif distance <= spacing_mm / 2.0:
                codes[place] = _IN_GAP
            else:
                codes[place] = _NOT_THIS_SLICE
    return codes


@lru_cache(maxsize=1)
def jit_slab_kernel():
    """The reference body compiled, or `RuntimeError("required_backend_unavailable:jit")`."""
    try:
        from numba import njit
    except ImportError as error:
        raise RuntimeError("required_backend_unavailable:jit") from error
    return njit(cache=True, nogil=True, fastmath=False)(slab_codes_reference)


def _as_array(value: object) -> np.ndarray | None:
    """`value` as an array, or None when it cannot be one (a ragged nest, for instance)."""
    try:
        return np.asarray(value)
    except (ValueError, TypeError):
        return None


def slab_codes(
    offset_mm: np.ndarray,
    thickness_mm: float,
    spacing_mm: float,
    in_plane: np.ndarray,
    backend: str = "reference",
) -> np.ndarray:
    """Name what one other acquisition's slabs did about every place at once.

    `offset_mm` is each place's signed distance from its slice's centre plane along the slice
    normal; `in_plane` says each place falls inside the slice's in-plane rectangle; `thickness_mm`
    and `spacing_mm` are the acquisition's own, as for `slab_code`. The answer is a read-only uint8
    array of indices into `SLAB_CODES`, one per place, and no input is written.

    Refused by name, never broadcast or coerced: `invalid_slab_arrays` unless `offset_mm` is a 1-D
    numeric array and `in_plane` a 1-D bool array of the same length (a flag broadcast over places
    would claim an in-plane fact nobody measured); `invalid_backend` for a backend outside
    ("reference", "jit"); `required_backend_unavailable:jit` when the twin was asked for and cannot
    be built.
    """
    offsets = _as_array(offset_mm)
    flags = _as_array(in_plane)
    if (
        offsets is None
        or flags is None
        or offsets.ndim != 1
        or offsets.dtype.kind not in "iuf"
        or flags.ndim != 1
        or flags.dtype != np.bool_
        or flags.shape != offsets.shape
    ):
        raise ValueError("invalid_slab_arrays")
    if backend not in ("reference", "jit"):
        raise ValueError("invalid_backend")
    kernel = slab_codes_reference if backend == "reference" else jit_slab_kernel()
    codes = kernel(
        offsets.astype(np.float64, copy=False),
        float(thickness_mm),
        float(spacing_mm),
        flags,
    )
    return handed_on(codes)
