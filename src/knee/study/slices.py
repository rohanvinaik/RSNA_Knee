"""One DICOM file, read whole: its header as stored and its pixels at stored fidelity."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pydicom


@dataclass(frozen=True, slots=True)
class Slice:
    """One file of a series.

    path: the file. header: every element as stored, with the file meta, except Pixel Data, whose content is
    `pixels`. pixels: pydicom's `pixel_array`, the stored values in the stored dtype with no rescale, windowing or
    conversion; (rows, columns) for a single frame.
    """

    path: Path
    header: pydicom.Dataset
    pixels: np.ndarray


def read_slice(path: Path) -> Slice:
    header = pydicom.dcmread(path)
    pixels = header.pixel_array
    del header.PixelData
    return Slice(path=path, header=header, pixels=pixels)
