"""Composition of already measured native fat-pad support."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class NativeFatSupport:
    mask: np.ndarray
    status: str
    candidate_count: int
    support_count: int
    known_count: int
    unknown_count: int
    disagreement_count: int
    complete: bool


def _boolean_plane(value: object, shape: tuple[int, int], name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.shape != shape or array.dtype.kind != "b":
        raise ValueError(f"{name}_must_be_boolean_with_candidate_shape")
    return array.astype(bool, copy=False)


def native_fat_support(
    candidate: np.ndarray,
    available: np.ndarray,
    white_fluid: np.ndarray | None,
    fat_classes: dict[str, np.ndarray],
    coarse_femur_core: np.ndarray | None = None,
) -> NativeFatSupport:
    """Keep measured compatible candidate pixels outside white fluid and the coarse femur core.

    The candidate is native geometry already selected by the caller. This function adds no
    image reading or threshold: it combines existing boolean measurements and preserves whether
    the candidate was completely classified or still contains unknown/unavailable places.
    """
    region = np.asarray(candidate)
    if region.ndim != 2 or region.dtype.kind != "b":
        raise ValueError("candidate_must_be_a_boolean_plane")
    shape = (int(region.shape[0]), int(region.shape[1]))
    region = region.astype(bool, copy=False)
    readable = _boolean_plane(available, shape, "available")
    if white_fluid is None:
        return NativeFatSupport(
            np.zeros(shape, dtype=bool),
            "same_series_fluid_level_unavailable",
            int(region.sum()),
            0,
            0,
            int(region.sum()),
            0,
            False,
        )
    white = _boolean_plane(white_fluid, shape, "white_fluid")
    if coarse_femur_core is None:
        core = np.zeros(shape, dtype=bool)
    else:
        core = _boolean_plane(coarse_femur_core, shape, "coarse_femur_core")
    positive = _boolean_plane(
        fat_classes.get("positive_without_known_negative"),
        shape,
        "positive_without_known_negative",
    )
    known = _boolean_plane(fat_classes.get("known"), shape, "known")
    unknown = _boolean_plane(fat_classes.get("unknown"), shape, "unknown")
    disagreement = _boolean_plane(
        fat_classes.get("disagreement"), shape, "disagreement"
    )
    candidate_available = region & readable
    support = candidate_available & positive & ~white & ~core
    complete = bool(np.all(~region | (readable & known & ~unknown & ~disagreement)))
    unknown_count = int(np.count_nonzero(region & (~readable | unknown)))
    if support.any():
        status = "native_support_selected"
    elif not candidate_available.any():
        status = "native_candidate_unavailable"
    elif complete:
        status = "measured_empty_native_support"
    else:
        status = "native_compatibility_incomplete"
    return NativeFatSupport(
        support,
        status,
        int(region.sum()),
        int(support.sum()),
        int(np.count_nonzero(region & readable & known)),
        unknown_count,
        int(np.count_nonzero(region & disagreement)),
        complete,
    )
