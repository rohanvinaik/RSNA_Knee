"""The pixel decoders the competition's files need, checked before any file is read.

The data description: "Series come in a mix of transfer syntaxes (uncompressed Explicit VR Little Endian, JPEG
Lossless, JPEG 2000, Implicit VR Little Endian)." Both JPEG Lossless syntaxes and both JPEG 2000 syntaxes are
required. A missing decoder is refused by name; nothing falls back.
"""

from __future__ import annotations

from pydicom.pixels.decoders.base import get_decoder
from pydicom.uid import (
    JPEG2000,
    UID,
    ExplicitVRLittleEndian,
    ImplicitVRLittleEndian,
    JPEG2000Lossless,
    JPEGLossless,
    JPEGLosslessSV1,
)

REQUIRED: tuple[UID, ...] = (
    ExplicitVRLittleEndian,
    ImplicitVRLittleEndian,
    JPEGLossless,
    JPEGLosslessSV1,
    JPEG2000Lossless,
    JPEG2000,
)


def decoder_plugins() -> dict[str, tuple[str, ...]]:
    """Each required transfer syntax's name -> the decoder plugins available for it here (empty: none needed for
    the uncompressed syntaxes, which pydicom reads natively, or none installed)."""
    return {
        uid.name: tuple(sorted(get_decoder(uid).available_plugins)) for uid in REQUIRED
    }


def decoder_codes() -> dict[str, str]:
    """Each required transfer syntax's name -> "available" or "unavailable", in this environment."""
    return {
        uid.name: "available" if get_decoder(uid).is_available else "unavailable"
        for uid in REQUIRED
    }


def require_decoders() -> None:
    """Refuse, naming each one, when a decoder the competition's files need is unavailable."""
    missing = [name for name, code in decoder_codes().items() if code == "unavailable"]
    if missing:
        raise RuntimeError(f"no pixel decoder for: {', '.join(missing)}")
