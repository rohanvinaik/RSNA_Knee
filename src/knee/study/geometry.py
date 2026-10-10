"""Slice geometry in the patient's frame (DICOM LPS, millimetres), from a header's tags as stored.

A pixel at (row r, column c) of a slice lies at position + c * spacing[1] * row_direction + r * spacing[0] *
column_direction, where orientation = (row_direction, column_direction) and spacing = (between rows, between
columns): DICOM PS3.3 C.7.6.2.1.1.

Each reader returns a named status with its values: "present" with the values, or None with the kind of zero it
found: "absent" (no such element), "empty" (the element is there with no value), "malformed" (not the expected
count of finite decimals), or, for an orientation, "degenerate" (row x column is the zero vector). The stored text
stays in the header.
"""

from __future__ import annotations

import numpy as np
import pydicom
from pydicom.multival import MultiValue

Reading = tuple[str, np.ndarray | None]


def decimals(header: pydicom.Dataset, keyword: str, count: int) -> Reading:
    """A decimal tag's status, and its values as float64 (count,) when "present"."""
    if keyword not in header:
        return "absent", None
    value = header.get(keyword)
    many = isinstance(value, (MultiValue, list, tuple))
    if value is None or value == "" or (many and len(value) == 0):
        return "empty", None
    values = list(value) if many else [value]
    if len(values) != count:
        return "malformed", None
    try:
        out = np.array([float(v) for v in values], dtype=np.float64)
    except (TypeError, ValueError):
        return "malformed", None
    if not bool(np.isfinite(out).all()):
        return "malformed", None
    return "present", out


def orientation_of(header: pydicom.Dataset) -> Reading:
    """ImageOrientationPatient (6,): the row then the column direction cosines."""
    status, orientation = decimals(header, "ImageOrientationPatient", 6)
    if orientation is None:
        return status, None
    if not np.any(np.cross(orientation[:3], orientation[3:])):
        return "degenerate", None
    return "present", orientation


def position_of(header: pydicom.Dataset) -> Reading:
    """ImagePositionPatient (3,), mm: the centre of the slice's first pixel."""
    return decimals(header, "ImagePositionPatient", 3)


def spacing_of(header: pydicom.Dataset) -> Reading:
    """PixelSpacing (2,), mm: between rows, then between columns."""
    return decimals(header, "PixelSpacing", 2)


def slice_normal(orientation: np.ndarray) -> np.ndarray:
    """The unit normal (3,) of a slice with this orientation (6,): row direction x column direction."""
    normal = np.cross(orientation[:3], orientation[3:])
    return normal / np.linalg.norm(normal)


def along(positions: np.ndarray, normal: np.ndarray) -> np.ndarray:
    """Each position (n, 3), mm, projected on the unit normal (3,): mm along the stack axis, (n,)."""
    return positions @ normal
