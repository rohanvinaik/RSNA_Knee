"""Synthetic DICOM for the input stage's tests. No competition data is written or read by these helpers."""

from __future__ import annotations

from pathlib import Path

import gdcm
import numpy as np
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import UID, ExplicitVRLittleEndian, MRImageStorage, generate_uid

# Rows along +x, columns along +y: the normal is +z.
AXIAL = ("1", "0", "0", "0", "1", "0")


def pattern(
    rows: int, columns: int, dtype: type[np.integer], seed: int = 0
) -> np.ndarray:
    """A deterministic synthetic image whose every pixel differs from its neighbours."""
    values = (np.arange(rows * columns, dtype=np.int64) * 37 + seed * 1009) % 4093
    if np.dtype(dtype) == np.dtype(np.int16):
        values = values - 2046
    return values.reshape(rows, columns).astype(dtype)


def write_slice(
    path: Path,
    pixels: np.ndarray,
    *,
    position: tuple[str, ...] | None = ("0", "0", "0"),
    orientation: tuple[str, ...] | None = AXIAL,
    spacing: tuple[str, ...] | None = ("0.5", "0.5"),
    instance: int = 1,
    syntax: UID = ExplicitVRLittleEndian,
) -> Path:
    """One uncompressed single-frame MR slice. A geometry tag given as None is left out; any other value is
    written as given, so a malformed tag can be written on purpose."""
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = MRImageStorage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = syntax
    ds = Dataset()
    ds.file_meta = meta
    ds.SOPClassUID = MRImageStorage
    ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    ds.Modality = "MR"
    ds.EchoTime = "12.5"
    ds.InstanceNumber = instance
    ds.Rows, ds.Columns = pixels.shape
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1 if pixels.dtype == np.int16 else 0
    if position is not None:
        ds.ImagePositionPatient = list(position)
    if orientation is not None:
        ds.ImageOrientationPatient = list(orientation)
    if spacing is not None:
        ds.PixelSpacing = list(spacing)
    ds.PixelData = pixels.tobytes()
    ds.save_as(path, enforce_file_format=True)
    return path


def transcode(source: Path, target: Path, syntax: str) -> Path:
    """Re-encode a slice with GDCM into the named gdcm.TransferSyntax (e.g. "JPEGLosslessProcess14_1")."""
    reader = gdcm.ImageReader()
    reader.SetFileName(str(source))
    if not reader.Read():
        raise RuntimeError(f"gdcm could not read {source}")
    change = gdcm.ImageChangeTransferSyntax()
    change.SetTransferSyntax(gdcm.TransferSyntax(getattr(gdcm.TransferSyntax, syntax)))
    change.SetInput(reader.GetImage())
    if not change.Change():
        raise RuntimeError(f"gdcm could not encode {source} as {syntax}")
    writer = gdcm.ImageWriter()
    writer.SetFileName(str(target))
    writer.SetFile(reader.GetFile())
    writer.SetImage(change.GetOutput())
    if not writer.Write():
        raise RuntimeError(f"gdcm could not write {target}")
    return target
