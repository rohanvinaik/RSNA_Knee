"""The slab rule's array kernel, both signs (task 7.10): a reference and a JIT twin that answer to SAME.

Written by the lead BEFORE the body. The oracle is the scalar `slab_code`, the one decision, and
since task 7.15 the reference RUNS it, place by place; the twin is a second body, the rule's
arithmetic over arrays compiled, admitted only by agreeing with the reference element by element on
every boundary the rule names (the half-thickness, the half-pitch, an underflowing thickness, a
non-finite offset or geometry) and on both in-plane flags. It is never a silent fallback: an
unavailable backend is refused by name.
"""

import math

import numpy as np
import pytest

from knee.compute.contracts import ComputeContract
from knee.lenses import slab_kernels
from knee.lenses.slab_kernels import CONTRACT, slab_codes, slab_codes_reference
from knee.lenses.slabs import SLAB_CODES, slab_code

GEOMETRIES = (
    (3.0, 4.0),  # a 1 mm gap
    (4.0, 4.0),  # slabs that touch: no gap to fall into
    (6.0, 5.0),  # overlapping slabs: `in_gap` unreachable
    (
        5e-324,
        4.0,
    ),  # a positive thickness whose half-extent underflows: invalid_geometry
    (3.0, 0.0),  # a non-positive pitch: invalid_geometry
    (3.0, -1.0),
    (3.0, math.nan),
    (math.nan, 4.0),
    (3.0, math.inf),
    (math.inf, 4.0),
)


def _offsets(thickness: float, spacing: float) -> np.ndarray:
    """Every boundary the scalar rule names, just inside and just outside it, and the non-finite."""
    half = thickness / 2.0 if math.isfinite(thickness) else 1.0
    pitch = spacing / 2.0 if math.isfinite(spacing) else 1.0
    around = []
    for edge in (half, pitch):
        around += [edge, -edge, np.nextafter(edge, np.inf), -np.nextafter(edge, np.inf)]
        around += [np.nextafter(edge, -np.inf), -np.nextafter(edge, -np.inf)]
    return np.array(
        [0.0, -0.0, *around, 1e6, -1e6, math.nan, math.inf, -math.inf], dtype=np.float64
    )


def _oracle(offsets, thickness, spacing, in_plane) -> list[int]:
    return [
        SLAB_CODES.index(slab_code(float(o), thickness, spacing, bool(f)))
        for o, f in zip(offsets, in_plane, strict=True)
    ]


# ---------------------------------------------------------------- positive


@pytest.mark.parametrize(("thickness", "spacing"), GEOMETRIES)
@pytest.mark.parametrize("flag", [True, False])
def test_the_reference_equals_the_scalar_rule_at_every_boundary(
    thickness, spacing, flag
) -> None:
    offsets = _offsets(thickness, spacing)
    in_plane = np.full(offsets.shape, flag, dtype=bool)
    codes = slab_codes_reference(offsets, thickness, spacing, in_plane)
    assert codes.dtype == np.uint8
    assert codes.shape == offsets.shape
    assert codes.tolist() == _oracle(offsets, thickness, spacing, in_plane)


def test_the_reference_answers_a_mixed_in_plane_array_place_by_place() -> None:
    offsets = np.linspace(-6.0, 6.0, 49)
    in_plane = (np.arange(49) % 3) != 0
    codes = slab_codes_reference(offsets, 3.0, 4.0, in_plane)
    assert codes.tolist() == _oracle(offsets, 3.0, 4.0, in_plane)


def test_an_empty_array_is_an_empty_answer() -> None:
    codes = slab_codes_reference(np.zeros(0), 3.0, 4.0, np.zeros(0, dtype=bool))
    assert codes.shape == (0,)
    assert codes.dtype == np.uint8


@pytest.mark.parametrize(("thickness", "spacing"), GEOMETRIES)
def test_the_jit_twin_is_the_same_as_the_reference(thickness, spacing) -> None:
    pytest.importorskip("numba")
    offsets = _offsets(thickness, spacing)
    in_plane = (np.arange(offsets.size) % 2) == 0
    reference = slab_codes(offsets, thickness, spacing, in_plane, backend="reference")
    twin = slab_codes(offsets, thickness, spacing, in_plane, backend="jit")
    np.testing.assert_array_equal(twin, reference)
    assert twin.dtype == reference.dtype == np.uint8


def test_the_dispatcher_hands_back_a_read_only_array() -> None:
    codes = slab_codes(np.array([0.0, 1.0]), 3.0, 4.0, np.array([True, True]))
    assert not codes.flags.writeable


def test_the_kernel_carries_its_contract_on_the_reference() -> None:
    assert isinstance(CONTRACT, ComputeContract)
    assert CONTRACT.reference == "slab_codes_reference"
    assert "slab_code" in CONTRACT.proof_gate


def test_the_reference_applies_the_scalar_rule_to_every_place(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Task 7.15: the rule has ONE statement and the reference runs it, so production on the
    reference backend calls `slab_code` once per place. A restatement left the scalar rule with
    no production caller and two bodies pinned to each other only by tests."""
    calls: list[tuple[float, float, float, bool]] = []

    def recording_rule(offset, thickness, spacing, in_plane):
        calls.append((offset, thickness, spacing, in_plane))
        return slab_code(offset, thickness, spacing, in_plane)

    monkeypatch.setattr(slab_kernels, "slab_code", recording_rule)
    offsets = np.linspace(-6.0, 6.0, 13)
    flags = (np.arange(13) % 2) == 0
    codes = slab_codes_reference(offsets, 3.0, 4.0, flags)
    assert len(calls) == 13
    assert [call[3] for call in calls] == flags.tolist()
    assert codes.tolist() == _oracle(offsets, 3.0, 4.0, flags)


def test_the_jit_twin_is_a_second_body_admitted_only_by_same() -> None:
    pytest.importorskip("numba")
    kernel = slab_kernels.jit_slab_kernel()
    assert kernel.py_func is slab_kernels._slab_body
    assert kernel.py_func is not slab_codes_reference


@pytest.mark.parametrize(("thickness", "spacing"), GEOMETRIES)
def test_the_twins_body_equals_the_reference_uncompiled_too(thickness, spacing) -> None:
    """SAME holds for the body itself, not only for what Numba made of it."""
    offsets = _offsets(thickness, spacing)
    in_plane = (np.arange(offsets.size) % 3) != 0
    body = slab_kernels._slab_body(offsets, thickness, spacing, in_plane)
    reference = slab_codes_reference(offsets, thickness, spacing, in_plane)
    assert body.tolist() == reference.tolist()


# ---------------------------------------------------------------- negative


def test_it_never_names_a_code_outside_the_slab_vocabulary() -> None:
    rng = np.random.default_rng(7)
    offsets = rng.normal(0.0, 10.0, 10_000)
    offsets[::97] = math.nan
    in_plane = rng.random(10_000) < 0.5
    for thickness, spacing in GEOMETRIES:
        codes = slab_codes_reference(offsets, thickness, spacing, in_plane)
        assert int(codes.max(initial=0)) < len(SLAB_CODES)


def test_a_backend_outside_the_registry_is_refused_by_name() -> None:
    with pytest.raises(ValueError, match="invalid_backend"):
        slab_codes(np.zeros(2), 3.0, 4.0, np.ones(2, dtype=bool), backend="gpu")


def test_mismatched_arrays_are_refused_rather_than_broadcast() -> None:
    """MUST NOT: broadcasting a flag over places would claim an in-plane fact nobody measured."""
    with pytest.raises(ValueError, match="invalid_slab_arrays"):
        slab_codes(np.zeros(3), 3.0, 4.0, np.ones(2, dtype=bool))
    with pytest.raises(ValueError, match="invalid_slab_arrays"):
        slab_codes(np.zeros((3, 1)), 3.0, 4.0, np.ones(3, dtype=bool))
    with pytest.raises(ValueError, match="invalid_slab_arrays"):
        slab_codes(np.zeros(3), 3.0, 4.0, np.ones(3, dtype=np.int64))


def test_a_non_finite_geometry_is_invalid_for_every_place_never_a_partial_answer() -> (
    None
):
    """MUST NOT: refuse the geometry for some places and measure with it at others."""
    offsets = np.array([0.0, 1.0, 2.0, 5.0])
    in_plane = np.array([True, True, False, True])
    for thickness, spacing in (
        (math.nan, 4.0),
        (3.0, math.inf),
        (0.0, 4.0),
        (3.0, 0.0),
    ):
        codes = slab_codes_reference(offsets, thickness, spacing, in_plane)
        assert codes.tolist() == [SLAB_CODES.index("invalid_geometry")] * 4


def test_the_in_plane_flag_is_never_overridden_by_the_offset() -> None:
    """MUST NOT: a place outside the frame is `outside_frame` however close its offset is."""
    offsets = np.array([0.0, 0.0, 0.0])
    codes = slab_codes_reference(offsets, 3.0, 4.0, np.array([False, False, False]))
    assert codes.tolist() == [SLAB_CODES.index("outside_frame")] * 3
