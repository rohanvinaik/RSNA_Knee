"""Every transfer syntax the competition names decodes here (knee.study.decoders, knee.study.slices).

The lossless syntaxes are checked by an exact round trip: a synthetic image is written uncompressed, re-encoded by
GDCM, and read back through the input stage's own reader.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from conftest import pattern, transcode, write_slice
from pydicom.uid import ImplicitVRLittleEndian

from knee.study import decoders
from knee.study.slices import read_slice

LOSSLESS = {
    "JPEGLosslessProcess14_1": "1.2.840.10008.1.2.4.70",
    "JPEGLosslessProcess14": "1.2.840.10008.1.2.4.57",
    "JPEG2000Lossless": "1.2.840.10008.1.2.4.90",
}


def test_every_required_decoder_is_available() -> None:
    assert set(decoders.decoder_codes().values()) == {"available"}
    decoders.require_decoders()


@pytest.mark.parametrize("dtype", [np.uint16, np.int16])
@pytest.mark.parametrize("syntax", sorted(LOSSLESS))
def test_lossless_files_decode_exactly(
    tmp_path: Path, syntax: str, dtype: type[np.integer]
) -> None:
    pixels = pattern(16, 24, dtype)
    source = write_slice(tmp_path / "plain.dcm", pixels)
    target = transcode(source, tmp_path / "coded.dcm", syntax)
    decoded = read_slice(target)
    assert str(decoded.header.file_meta.TransferSyntaxUID) == LOSSLESS[syntax]
    assert decoded.pixels.dtype == np.dtype(dtype)
    assert np.array_equal(decoded.pixels, pixels)


def test_implicit_vr_little_endian_decodes_exactly(tmp_path: Path) -> None:
    pixels = pattern(16, 24, np.uint16)
    decoded = read_slice(
        write_slice(tmp_path / "implicit.dcm", pixels, syntax=ImplicitVRLittleEndian)
    )
    assert str(decoded.header.file_meta.TransferSyntaxUID) == "1.2.840.10008.1.2"
    assert np.array_equal(decoded.pixels, pixels)


def test_jpeg_2000_decodes_to_the_stored_shape_and_dtype(tmp_path: Path) -> None:
    pixels = pattern(16, 24, np.uint16)
    target = transcode(
        write_slice(tmp_path / "plain.dcm", pixels), tmp_path / "j2k.dcm", "JPEG2000"
    )
    decoded = read_slice(target)
    assert str(decoded.header.file_meta.TransferSyntaxUID) == "1.2.840.10008.1.2.4.91"
    assert decoded.pixels.shape == pixels.shape and decoded.pixels.dtype == pixels.dtype


def test_a_missing_decoder_is_refused_by_name(monkeypatch: pytest.MonkeyPatch) -> None:
    def codes() -> dict[str, str]:
        return {
            "JPEG Lossless": "unavailable",
            "Explicit VR Little Endian": "available",
        }

    monkeypatch.setattr(decoders, "decoder_codes", codes)
    with pytest.raises(RuntimeError, match="JPEG Lossless"):
        decoders.require_decoders()
