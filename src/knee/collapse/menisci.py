"""Native local meniscus descriptions using the existing enclosed-darkness lens."""

from __future__ import annotations

from typing import Any

import numpy as np

from knee.collapse.local_native import enclosed_body_at_sources
from knee.collapse.physical import PlaneFrame
from knee.objects import assignments


def meniscus_local_body(
    raw: np.ndarray,
    available: np.ndarray,
    target: np.ndarray,
    frame: PlaneFrame,
    *,
    other_target: np.ndarray | None = None,
) -> dict[str, Any]:
    """Measure whole opened meniscus components at the existing physical thickness."""
    return enclosed_body_at_sources(
        raw,
        available,
        target,
        frame,
        thickness_mm=assignments.MENISCUS_THICKNESS_MM,
        other_target=other_target,
    )
