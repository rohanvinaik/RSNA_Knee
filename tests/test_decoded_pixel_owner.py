from __future__ import annotations

import base64
from pathlib import Path

import numpy as np
import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.encaps import encapsulate
from pydicom.pixels import pixel_array
from pydicom.pixels.encoders.base import get_encoder
from pydicom.uid import (
    ExplicitVRLittleEndian,
    JPEG2000Lossless,
    RLELossless,
    generate_uid,
)

from knee.study import series as series_module
from knee.study.series import read_series
from knee.study.slices import Slice, read_slice
from knee.study.tables import SeriesRow


def _write_dicom(path: Path, pixels: np.ndarray, position_z: float) -> None:
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = generate_uid()
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    dataset = FileDataset(str(path), {}, file_meta=meta, preamble=b"\0" * 128)
    dataset.SOPClassUID = meta.MediaStorageSOPClassUID
    dataset.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    dataset.Rows, dataset.Columns = pixels.shape
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = pixels.dtype.itemsize * 8
    dataset.BitsStored = pixels.dtype.itemsize * 8
    dataset.HighBit = dataset.BitsStored - 1
    dataset.PixelRepresentation = int(pixels.dtype.kind == "i")
    dataset.PixelSpacing = [0.7, 0.8]
    dataset.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
    dataset.ImagePositionPatient = [0, 0, position_z]
    dataset.SliceThickness = 1.2
    dataset.PixelData = pixels.tobytes()
    pydicom.dcmwrite(path, dataset, enforce_file_format=True)


def _row() -> SeriesRow:
    return SeriesRow("study", "series", "0", "0", "Sagittal")


def test_public_decoder_matches_dataset_pixel_array_without_dataset_cache(
    tmp_path: Path,
) -> None:
    expected = (np.arange(35, dtype=np.uint16).reshape(5, 7) * 13).astype(np.uint16)
    path = tmp_path / "one.dcm"
    _write_dicom(path, expected, 2.0)
    dataset = pydicom.dcmread(path)
    old_api = dataset.pixel_array.copy()
    assert "_pixel_array" in dataset.__dict__
    dataset = pydicom.dcmread(path)
    public_api = pixel_array(dataset)
    np.testing.assert_array_equal(public_api, old_api)
    assert public_api.dtype == old_api.dtype
    assert dataset.__dict__.get("_pixel_array") is None


def test_read_slice_uses_public_decoder_and_preserves_header_without_pixel_data(
    tmp_path: Path,
) -> None:
    values = np.arange(24, dtype=np.int16).reshape(4, 6)
    path = tmp_path / "single.dcm"
    _write_dicom(path, values, 1.0)
    prior = pydicom.dcmread(path)
    expected = prior.pixel_array.copy()
    result = read_slice(path)
    np.testing.assert_array_equal(result.pixels, expected)
    assert result.pixels.dtype == expected.dtype
    assert result.path == path
    assert "PixelData" not in result.header
    assert result.header.ImagePositionPatient == prior.ImagePositionPatient
    assert result.header.__dict__.get("_pixel_array") is None


def test_stackable_series_slices_are_views_of_one_ordered_owner(
    tmp_path: Path, monkeypatch
) -> None:
    values_by_name = {
        "a.dcm": np.full((4, 5), 10, dtype=np.uint16),
        "b.dcm": np.full((4, 5), 20, dtype=np.uint16),
        "c.dcm": np.full((4, 5), 30, dtype=np.uint16),
    }
    for name in values_by_name:
        (tmp_path / name).touch()
    slices_by_name = {}
    for index, (name, pixels) in enumerate(values_by_name.items()):
        header = pydicom.Dataset()
        header.SliceThickness = 1.2
        header.InstanceNumber = index
        slices_by_name[name] = Slice(tmp_path / name, header, pixels.copy())

    orientation = np.array([1, 0, 0, 0, 1, 0], dtype=np.float64)
    spacing = np.array([0.7, 0.8], dtype=np.float64)
    positions = {"a.dcm": 3.0, "b.dcm": 1.0, "c.dcm": 2.0}

    def reader_for(tag):
        if tag == "orientation":
            return lambda _header: ("present", orientation)
        if tag == "position":
            return lambda header: (
                "present",
                np.array(
                    [
                        0.0,
                        0.0,
                        positions[
                            next(
                                name
                                for name, candidate in slices_by_name.items()
                                if candidate.header is header
                            )
                        ],
                    ],
                    dtype=np.float64,
                ),
            )
        return lambda _header: ("present", spacing)

    monkeypatch.setattr(
        series_module,
        "GEOMETRY_TAGS",
        tuple((tag, reader_for(tag)) for tag in ("position", "orientation", "spacing")),
    )
    monkeypatch.setattr(
        series_module, "read_slice", lambda path: slices_by_name[path.name]
    )
    result = read_series(tmp_path, _row())
    assert result.stack == ("stackable",)
    assert result.geometry is not None
    assert result.volume is not None
    assert result.volume[:, 0, 0].tolist() == [20, 30, 10]
    assert [slice_.header.InstanceNumber for slice_ in result.slices] == [1, 2, 0]
    for index, slice_ in enumerate(result.slices):
        assert np.shares_memory(slice_.pixels, result.volume)
        assert np.shares_memory(slice_.pixels, result.volume[index])
        assert slice_.pixels.base is result.volume or np.shares_memory(
            slice_.pixels, result.volume
        )
        np.testing.assert_array_equal(slice_.pixels, result.volume[index])
        assert not slice_.pixels.flags.writeable
    assert not result.volume.flags.writeable
    assert result.volume.nbytes == sum(slice_.pixels.nbytes for slice_ in result.slices)


def test_nonstackable_shape_or_dtype_paths_keep_independent_slice_arrays(
    tmp_path: Path, monkeypatch
) -> None:
    for name in ("a.dcm", "b.dcm"):
        (tmp_path / name).touch()
    slices_by_name = {
        "a.dcm": Slice(
            tmp_path / "a.dcm", pydicom.Dataset(), np.ones((3, 4), dtype=np.uint16)
        ),
        "b.dcm": Slice(
            tmp_path / "b.dcm", pydicom.Dataset(), np.ones((4, 4), dtype=np.uint16)
        ),
    }
    monkeypatch.setattr(
        series_module,
        "GEOMETRY_TAGS",
        tuple(
            (tag, lambda _header: ("absent", None))
            for tag in ("position", "orientation", "spacing")
        ),
    )
    monkeypatch.setattr(
        series_module, "read_slice", lambda path: slices_by_name[path.name]
    )
    shape_result = read_series(tmp_path, _row())
    assert "shape_varies" in shape_result.stack
    assert shape_result.volume is None
    assert shape_result.slices[0].pixels is slices_by_name["a.dcm"].pixels
    assert shape_result.slices[1].pixels is slices_by_name["b.dcm"].pixels


def test_nonstackable_dtype_paths_keep_independent_slice_arrays(
    tmp_path: Path, monkeypatch
) -> None:
    for name in ("a.dcm", "b.dcm"):
        (tmp_path / name).touch()
    slices_by_name = {
        "a.dcm": Slice(
            tmp_path / "a.dcm", pydicom.Dataset(), np.ones((3, 4), dtype=np.uint16)
        ),
        "b.dcm": Slice(
            tmp_path / "b.dcm", pydicom.Dataset(), np.ones((3, 4), dtype=np.int16)
        ),
    }
    monkeypatch.setattr(
        series_module,
        "GEOMETRY_TAGS",
        tuple(
            (tag, lambda _header: ("absent", None))
            for tag in ("position", "orientation", "spacing")
        ),
    )
    monkeypatch.setattr(
        series_module, "read_slice", lambda path: slices_by_name[path.name]
    )
    result = read_series(tmp_path, _row())
    assert "dtype_varies" in result.stack
    assert result.volume is None
    assert result.slices[0].pixels is slices_by_name["a.dcm"].pixels
    assert result.slices[1].pixels is slices_by_name["b.dcm"].pixels


# Deterministic OpenJPEG image fixture for the pixel-decoder equivalence test.
_JPEG2000_LOSSLESS_FRAME = base64.b64decode(
    "/0//UQApAAAAAAAgAAAAIAAAAAAAAAAAAAAAIAAAACAAAAAAAAAAAAABDwEB/1IADAAAAAEAAgQEAAH/XAAKQICIiJCIiJD/ZAAlAAFDcmVhdGVkIGJ5IE9wZW5KUEVHIHZlcnNpb24gMi41LjT/kAAKAAAAAAEkAAH/k9/4k7gSLEKnnPZywFH9Gqc/v4uSsRIh311zCNA6eu9lTE/bmRqeJ1ElnIdVjcPQHJiRG9MTZZfixm7HcatolZrtMDJNC5AaQySqEmbtHZ52LTfBFBWX6Uj5HhuZiJSfQXo2I9gH3Uz1zKy9cSzndfNqqeSk3MxAcQnZ/cf+GDE/8SJIf+GBAEQuNXMzldQ8OI4DP+aLg4RF6HhSWJE0vznR2vMhIQQjm5T1vaT8SmgO45UDY+F8EWKnIi0qckQdRfpuT0XmOkybP+gfx/4YMz/xIgh/4YDAkQVXp/9/GgJA8kte5K/L8gAAGwcdIMRxA4zAtSaR/xlqmpPV4sBqoSDfGoAAGECdysuQwcYUJf9/kFZjCn/X/9k="  # pragma: allowlist secret
)


def _jpeg2000_expected() -> np.ndarray:
    return ((np.arange(32 * 32, dtype=np.uint32).reshape(32, 32) * 101) % 65536).astype(
        np.uint16
    )


def _write_compressed_dicom(
    path: Path, pixels: np.ndarray, transfer_syntax, position_z: float
) -> None:
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = generate_uid()
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = transfer_syntax
    dataset = FileDataset(str(path), {}, file_meta=meta, preamble=b"\0" * 128)
    dataset.SOPClassUID = meta.MediaStorageSOPClassUID
    dataset.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    dataset.Rows, dataset.Columns = pixels.shape
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = pixels.dtype.itemsize * 8
    dataset.BitsStored = pixels.dtype.itemsize * 8
    dataset.HighBit = dataset.BitsStored - 1
    dataset.PixelRepresentation = int(pixels.dtype.kind == "i")
    dataset.PixelSpacing = [0.7, 0.8]
    dataset.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
    dataset.ImagePositionPatient = [0, 0, position_z]
    dataset.SliceThickness = 1.2
    if transfer_syntax == JPEG2000Lossless:
        if pixels.shape != (32, 32) or pixels.dtype != np.dtype(np.uint16):
            raise ValueError("embedded_jpeg2000_fixture_shape_or_dtype")
        frame = _JPEG2000_LOSSLESS_FRAME
    else:
        encoder = get_encoder(transfer_syntax)
        frame = encoder.encode(
            pixels,
            rows=pixels.shape[0],
            columns=pixels.shape[1],
            number_of_frames=1,
            samples_per_pixel=1,
            bits_allocated=pixels.dtype.itemsize * 8,
            bits_stored=pixels.dtype.itemsize * 8,
            pixel_representation=int(pixels.dtype.kind == "i"),
            photometric_interpretation="MONOCHROME2",
            encoding_plugin="pydicom" if transfer_syntax == RLELossless else "",
        )
    dataset.PixelData = encapsulate([frame])
    pydicom.dcmwrite(path, dataset, enforce_file_format=True)


def test_compressed_dataset_pixel_array_matches_public_pixel_array(
    tmp_path: Path,
) -> None:
    fixtures = (
        ("j2k-lossless.dcm", JPEG2000Lossless, _jpeg2000_expected()),
        (
            "rle-lossless.dcm",
            RLELossless,
            ((np.arange(32 * 32, dtype=np.uint32).reshape(32, 32) * 7) % 251).astype(
                np.uint8
            ),
        ),
    )
    for name, transfer_syntax, expected in fixtures:
        path = tmp_path / name
        _write_compressed_dicom(path, expected, transfer_syntax, 1.0)
        original = pydicom.dcmread(path)
        old_pixels = original.pixel_array.copy()
        assert original.file_meta.TransferSyntaxUID == transfer_syntax
        current = pydicom.dcmread(path)
        new_pixels = pixel_array(current)
        np.testing.assert_array_equal(new_pixels, old_pixels)
        assert new_pixels.shape == old_pixels.shape == expected.shape
        assert new_pixels.dtype == old_pixels.dtype == expected.dtype
        assert current.__dict__.get("_pixel_array") is None
        np.testing.assert_array_equal(new_pixels, expected)


def test_rle_series_slices_share_the_read_only_volume_owner(tmp_path: Path) -> None:
    expected = []
    for index in range(3):
        values = (
            (np.arange(32 * 32, dtype=np.uint32).reshape(32, 32) + index * 19) % 251
        ).astype(np.uint8)
        expected.append(values)
        _write_compressed_dicom(
            tmp_path / f"{index:02}.dcm", values, RLELossless, float(2 - index)
        )
    result = read_series(tmp_path, _row())
    assert result.stack == ("stackable",)
    assert result.volume is not None
    assert result.geometry is not None
    np.testing.assert_array_equal(result.volume, np.stack(expected[::-1]))
    assert result.volume.dtype == np.uint8
    assert result.volume.nbytes == sum(slice_.pixels.nbytes for slice_ in result.slices)
    assert not result.volume.flags.writeable
    for index, slice_ in enumerate(result.slices):
        assert np.shares_memory(slice_.pixels, result.volume[index])
        assert np.shares_memory(slice_.pixels, result.volume)
        assert not slice_.pixels.flags.writeable
        np.testing.assert_array_equal(slice_.pixels, expected[::-1][index])
