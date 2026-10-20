"""Exact addressed readings whose places are scopes rather than native points.

A coarse-grid coordinate identifies one retained block, and a series-slice
coordinate identifies a measurement of that slice. Neither asserts a point in
patient space. Original scope geometry and source evidence remain in metadata.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from knee.encoding.places import EncodingResult


@dataclass(frozen=True, slots=True)
class ScopedEncoding:
    status: str
    encoding: EncodingResult | None
    coordinates: np.ndarray | None
    address_kind: str
    metadata: dict
