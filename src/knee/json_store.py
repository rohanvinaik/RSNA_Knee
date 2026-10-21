"""Lossless JSON metadata stored as plain UTF-8 or an outer-XZ `.json.xz` sidecar."""

from __future__ import annotations

import json
import lzma
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

JSON_XZ_SUFFIX = ".json.xz"
JSON_SUFFIX = ".json"


def compressed_path(path: str | os.PathLike[str]) -> Path:
    """Return the compressed sidecar path for a logical JSON path."""
    value = Path(path)
    if value.name.endswith(JSON_XZ_SUFFIX):
        return value
    if value.name.endswith(JSON_SUFFIX):
        return value.with_name(value.name + ".xz")
    raise ValueError("metadata_path_must_end_with_.json_or_.json.xz")


def _legacy_path(path: Path) -> Path:
    if path.name.endswith(JSON_XZ_SUFFIX):
        return path.with_name(path.name[: -len(".xz")])
    if path.name.endswith(JSON_SUFFIX):
        return path
    raise ValueError("metadata_path_must_end_with_.json_or_.json.xz")


def resolve_json_path(path: str | os.PathLike[str]) -> Path:
    """Use an existing requested path; otherwise use its existing other-format sibling."""
    requested = Path(path)
    if requested.exists():
        return requested
    if requested.name.endswith(JSON_XZ_SUFFIX):
        sibling = _legacy_path(requested)
    elif requested.name.endswith(JSON_SUFFIX):
        sibling = compressed_path(requested)
    else:
        return requested
    return sibling if sibling.exists() else requested


def load_json(path: str | os.PathLike[str]) -> Any:
    """Load JSON from a plain file or standard outer-XZ JSON sidecar."""
    actual = resolve_json_path(path)
    if actual.name.endswith(JSON_XZ_SUFFIX):
        with lzma.open(actual, "rt", encoding="utf-8", format=lzma.FORMAT_XZ) as stream:
            return json.load(stream)
    with actual.open("r", encoding="utf-8") as stream:
        return json.load(stream)


_JSON_WRITE_BUFFER_BYTES = 64 * 1024
# JSONEncoder emits ASCII text because ensure_ascii=True. The smaller character
# slice also bounds UTF-8 encoding memory if a future caller changes that option.
_JSON_TEXT_SLICE_CHARS = _JSON_WRITE_BUFFER_BYTES // 4


def _write_json_buffered(
    stream: lzma.LZMAFile, encoder: json.JSONEncoder, value: Any
) -> None:
    """Write an encoded JSON stream through a bounded coalescing byte buffer."""
    buffer = bytearray()

    def append_bytes(encoded: bytes) -> None:
        if not encoded:
            return
        if len(buffer) + len(encoded) > _JSON_WRITE_BUFFER_BYTES:
            if buffer:
                stream.write(buffer)
                buffer.clear()
            if len(encoded) == _JSON_WRITE_BUFFER_BYTES:
                stream.write(encoded)
                return
        buffer.extend(encoded)
        if len(buffer) == _JSON_WRITE_BUFFER_BYTES:
            stream.write(buffer)
            buffer.clear()

    for text in encoder.iterencode(value):
        if len(text) <= _JSON_TEXT_SLICE_CHARS:
            append_bytes(text.encode("utf-8"))
            continue
        for start in range(0, len(text), _JSON_TEXT_SLICE_CHARS):
            encoded = text[start : start + _JSON_TEXT_SLICE_CHARS].encode("utf-8")
            append_bytes(encoded)
    append_bytes(b"\n")
    if buffer:
        stream.write(buffer)


def dump_json_atomic(
    path: str | os.PathLike[str],
    value: Any,
    default: Callable[[Any], Any] | None = None,
    *,
    compression_preset: int = 6,
) -> Path:
    """Stream compact standard JSON to an XZ sidecar and atomically replace it.

    A logical `.json` input writes `.json.xz`; an explicit `.json.xz` input writes itself.
    Existing legacy JSON is removed only after the compressed replacement is committed, so a
    subsequent request using the legacy name resolves to the current sidecar rather than stale data.
    """
    if (
        isinstance(compression_preset, bool)
        or not isinstance(compression_preset, int)
        or not 0 <= compression_preset <= 9
    ):
        raise ValueError("compression_preset_invalid")
    requested = Path(path)
    dest = compressed_path(requested)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        dir=dest.parent, prefix=dest.name + ".", suffix=".part"
    )
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        encoder = json.JSONEncoder(
            default=default,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=True,
        )
        with lzma.LZMAFile(
            temporary,
            "wb",
            format=lzma.FORMAT_XZ,
            preset=compression_preset,
        ) as stream:
            _write_json_buffered(stream, encoder, value)
        os.replace(temporary, dest)
        legacy = _legacy_path(dest)
        if legacy.exists():
            try:
                legacy.unlink()
            except OSError as exc:
                raise OSError("legacy_json_remove_failed") from exc
        return dest
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
