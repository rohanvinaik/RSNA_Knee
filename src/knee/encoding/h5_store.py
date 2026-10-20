# path: src/knee/encoding/h5_store.py
"""Isolated, optional-dependency HDF5 storage adapter for retained arrays.

Schema v1 retains raw ``manifest_json`` and individually named array datasets.
Schema v2 shares exact duplicate array datasets through hard links and retains
every public name in an ordered key table. Its JSON datasets use declared gzip
compression. Schema v3 (written only by :func:`write_h5_compact`) stores the
same gzip manifest bytes, a gzip ordered JSON index and a small number of
gzip+shuffle arenas, one or more per original ``dtype.str``. Each public key
keeps its dtype, shape, exact byte offset/length and canonical alias identity
in the index; arrays are read lazily by span. Schema v4 adds opt-in per-array
byte-XOR/XZ payloads. Opt-in schema v5 chooses the shortest raw, v4 row-XOR, or
modular-row/XZ payload for each unique array. All versions preserve the input
manifest and decoded array bytes; the reader also accepts historical v1 files
without an explicit version.
Only bool / signed / unsigned / float / complex arrays are stored; no casting,
quantization, pickle or object representation is ever used.

Requires (imports): json, os, tempfile, collections.abc.Mapping, contextlib,
pathlib.Path, numpy; ``h5py`` is imported lazily and is optional.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from math import isfinite, prod
from pathlib import Path
from typing import Any, NamedTuple, Self

import numpy as np

__all__ = [
    "H5Reader",
    "H5StoreError",
    "MalformedH5Error",
    "ManifestError",
    "OptionalDependencyError",
    "ReaderClosedError",
    "UnsupportedArrayDtypeError",
    "open_h5",
    "write_h5",
    "write_h5_byte_xor",
    "write_h5_compact",
    "write_h5_modular",
]

_MANIFEST = "manifest_json"
_ARRAYS = "arrays"
_ARRAY_KEYS = "array_keys_json"
_ARRAY_INDEX = "array_index_json"
_ARENAS = "arenas"
_BYTE_PAYLOAD = "byte_payload"
_SCHEMA_VERSION = "schema_version"
_SCHEMA_V1 = 1
_SCHEMA_V2 = 2
_SCHEMA_V3 = 3
_SCHEMA_V4 = 4
_SCHEMA_V5 = 5
_MANIFEST_ENCODING = "encoding"
_ARENA_FORMAT = "knee-h5-arena/v3"
_BYTE_FORMAT = "knee-h5-byte-payload/v4"
_MODULAR_FORMAT = "knee-h5-byte-payload/modular-v5"
# An arena is split once adding another unique array would exceed this many bytes.
_MAX_ARENA_BYTES = 1 << 28
# Chunk span (bytes) of an arena; a one-array read decompresses only touched chunks.
_ARENA_CHUNK_BYTES = 1 << 18


class H5StoreError(Exception):
    """Base of all named failures of this adapter."""


class OptionalDependencyError(H5StoreError, ImportError):
    """h5py is not installed."""


class UnsupportedArrayDtypeError(H5StoreError, TypeError):
    """Object / unicode / bytes-string / structured / datetime or other non-numeric type."""


class ManifestError(H5StoreError, ValueError):
    """Manifest cannot be represented exactly as UTF-8 JSON."""


class MalformedH5Error(H5StoreError, ValueError):
    """File is not a readable HDF5 file written by this adapter."""


class ReaderClosedError(H5StoreError, ValueError):
    """Access to a reader after it was closed."""


def _h5py():
    try:
        import h5py
    except ImportError as e:  # pragma: no cover - depends on environment
        raise OptionalDependencyError(
            "optional dependency 'h5py' is not installed"
        ) from e
    return h5py


def _check_dtype(dtype: np.dtype, name: object) -> None:
    if dtype.hasobject or dtype.fields is not None or dtype.kind not in "biufc":
        raise UnsupportedArrayDtypeError(
            f"unsupported dtype {dtype!r} for array {name!r}"
        )


def _check_json(value: Any, where: str = "manifest") -> None:
    if value is None or isinstance(value, (bool, str, int)):
        return
    if isinstance(value, float):
        if not isfinite(value):
            raise ManifestError(f"nonfinite float at {where}")
        return
    if isinstance(value, list):
        for i, v in enumerate(value):
            _check_json(v, f"{where}[{i}]")
        return
    if isinstance(value, dict):
        for k, v in value.items():
            if not isinstance(k, str):
                raise ManifestError(f"non-string key {k!r} at {where}")
            _check_json(v, f"{where}.{k}")
        return
    raise ManifestError(f"unsupported type {type(value).__name__} at {where}")


def _serialize_manifest(manifest: object) -> bytes:
    if not isinstance(manifest, dict):
        raise ManifestError("manifest must be a dict")
    _check_json(manifest)
    try:
        return json.dumps(manifest, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as e:
        raise ManifestError(f"manifest not serializable: {e}") from e


def _write_dataset(group, index: int, key: str, arr: np.ndarray) -> None:
    filters = (
        {"compression": "gzip", "compression_opts": 4, "shuffle": True}
        if arr.ndim > 0 and arr.size > 0
        else {}
    )
    ds = group.create_dataset(f"{index:08d}", data=arr, **filters)
    ds.attrs["key"] = key
    ds.attrs["dtype"] = arr.dtype.str


def write_h5(path, manifest: dict, arrays: Mapping[str, np.ndarray]) -> Path:
    """Atomically write manifest + arrays; return the destination Path.

    Everything is validated before any file is created. Data goes to a unique sibling
    ``.part`` file that replaces the destination only after a complete close; on any
    failure the part file is removed and a previous destination is untouched.
    """
    dest = Path(path)
    payload = _serialize_manifest(manifest)
    items: list[tuple[str, np.ndarray]] = []
    for key, arr in arrays.items():
        if not isinstance(key, str):
            raise ManifestError(f"array key must be str: {key!r}")
        try:
            key.encode("utf-8")
        except UnicodeEncodeError as e:
            raise ManifestError(f"array key not UTF-8 encodable: {key!r}") from e
        if not isinstance(arr, np.ndarray):
            raise UnsupportedArrayDtypeError(f"array {key!r} must be a numpy ndarray")
        _check_dtype(arr.dtype, key)
        items.append((key, arr))
    aliases: list[str | None] = []
    by_digest: dict[tuple[str, tuple[int, ...], str], list[tuple[np.ndarray, str]]] = {}
    for key, arr in items:
        content = arr.tobytes(order="C")
        digest = hashlib.sha256(
            arr.dtype.str.encode("ascii") + repr(arr.shape).encode("ascii") + content
        ).hexdigest()
        identity = (arr.dtype.str, arr.shape, digest)
        canonical = None
        for previous, previous_name in by_digest.get(identity, ()):
            if previous.tobytes(order="C") == content:
                canonical = previous_name
                break
        aliases.append(canonical)
        if canonical is None:
            by_digest.setdefault(identity, []).append((arr, key))
    h5py = _h5py()
    uses_aliases = any(canonical is not None for canonical in aliases)

    fd, tmp_name = tempfile.mkstemp(
        dir=dest.parent, prefix=dest.name + ".", suffix=".part"
    )
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with h5py.File(tmp, "w") as f:
            f.attrs[_SCHEMA_VERSION] = _SCHEMA_V2 if uses_aliases else _SCHEMA_V1
            manifest_options = (
                {"compression": "gzip", "compression_opts": 4, "shuffle": True}
                if uses_aliases and payload
                else {}
            )
            manifest_ds = f.create_dataset(
                _MANIFEST,
                data=np.frombuffer(payload, dtype=np.uint8),
                **manifest_options,
            )
            if uses_aliases:
                manifest_ds.attrs[_MANIFEST_ENCODING] = "gzip"
            group = f.create_group(_ARRAYS)
            canonical_indices: dict[str, int] = {}
            for i, (key, arr) in enumerate(items):
                canonical = aliases[i]
                if canonical is None:
                    _write_dataset(group, i, key, arr)
                    canonical_indices[key] = i
                else:
                    canonical_index = canonical_indices[canonical]
                    group[f"{i:08d}"] = group[f"{canonical_index:08d}"]
            if uses_aliases:
                keys_payload = json.dumps(
                    [key for key, _ in items], ensure_ascii=False
                ).encode("utf-8")
                key_table = f.create_dataset(
                    _ARRAY_KEYS,
                    data=np.frombuffer(keys_payload, dtype=np.uint8),
                    compression="gzip",
                    compression_opts=4,
                    shuffle=True,
                )
                key_table.attrs[_MANIFEST_ENCODING] = "gzip"
        with open(tmp, "rb") as fh:
            os.fsync(fh.fileno())
        os.replace(tmp, dest)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return dest


# --------------------------------------------------------------------------
# Schema v3: compact arena writer
# --------------------------------------------------------------------------


def _byte_view(arr: np.ndarray) -> np.ndarray:
    """Flat uint8 view of the array's C-order bytes (copies only if strided)."""
    return np.ascontiguousarray(arr).reshape(-1).view(np.uint8)


def _content_digest(view: np.ndarray) -> bytes:
    return hashlib.sha256(view).digest()


def _write_arena_slice(dataset, start: int, stop: int, flat: np.ndarray) -> None:
    dataset[start:stop] = flat


def _plan_compact(items: list[tuple[str, np.ndarray]]) -> dict[str, Any]:
    """Fixed arena sizes, per-key offsets and exact-alias identities, before writing."""
    entries: list[dict[str, Any]] = []
    arenas: list[dict[str, Any]] = []
    open_arena: dict[str, int] = {}
    seen: dict[tuple[str, tuple[int, ...], bytes], list[int]] = {}
    for i, (key, arr) in enumerate(items):
        dtype_str = arr.dtype.str
        shape = [int(n) for n in arr.shape]
        nbytes = int(arr.size) * arr.dtype.itemsize
        entry: dict[str, Any] = {
            "key": key,
            "dtype": dtype_str,
            "shape": shape,
            "arena": None,
            "offset": 0,
            "length": 0,
            "alias_of": None,
        }
        if nbytes == 0:
            entries.append(entry)
            continue
        identity = (dtype_str, tuple(shape), _content_digest(_byte_view(arr)))
        alias = None
        for j in seen.get(identity, ()):
            # Hash is never sufficient: confirm exact C-order byte equality.
            if np.array_equal(_byte_view(items[j][1]), _byte_view(arr)):
                alias = j
                break
        if alias is not None:
            target = entries[alias]
            entry.update(
                arena=target["arena"],
                offset=target["offset"],
                length=target["length"],
                alias_of=alias,
            )
            entries.append(entry)
            continue
        a = open_arena.get(dtype_str)
        if (
            a is None
            or arenas[a]["bytes"] + nbytes > _MAX_ARENA_BYTES
            and arenas[a]["bytes"] > 0
        ):
            a = len(arenas)
            arenas.append({"name": f"{a:08d}", "dtype": dtype_str, "bytes": 0})
            open_arena[dtype_str] = a
        entry.update(arena=a, offset=arenas[a]["bytes"], length=nbytes)
        arenas[a]["bytes"] += nbytes
        entries.append(entry)
        seen.setdefault(identity, []).append(i)
    return {"format": _ARENA_FORMAT, "arenas": arenas, "arrays": entries}


def write_h5_compact(path, manifest: dict, arrays: Mapping[str, np.ndarray]) -> Path:
    """Atomically write an explicit schema-v3 arena store; return the destination.

    Same validation, atomic-replace and previous-file-on-error semantics as
    :func:`write_h5`. Unique arrays are packed (original dtype, original byte order,
    C order) into gzip+shuffle arenas bucketed by ``dtype.str``; exact duplicates
    share one span. No concatenated copy of all data is ever made.
    """
    dest = Path(path)
    payload = _serialize_manifest(manifest)
    items: list[tuple[str, np.ndarray]] = []
    for key, arr in arrays.items():
        if not isinstance(key, str):
            raise ManifestError(f"array key must be str: {key!r}")
        try:
            key.encode("utf-8")
        except UnicodeEncodeError as e:
            raise ManifestError(f"array key not UTF-8 encodable: {key!r}") from e
        if not isinstance(arr, np.ndarray):
            raise UnsupportedArrayDtypeError(f"array {key!r} must be a numpy ndarray")
        _check_dtype(arr.dtype, key)
        items.append((key, arr))
    plan = _plan_compact(items)
    try:
        index_payload = json.dumps(plan, ensure_ascii=False, allow_nan=False).encode(
            "utf-8"
        )
    except (TypeError, ValueError, UnicodeEncodeError) as e:  # pragma: no cover
        raise ManifestError(f"array index not serializable: {e}") from e
    h5py = _h5py()

    fd, tmp_name = tempfile.mkstemp(
        dir=dest.parent, prefix=dest.name + ".", suffix=".part"
    )
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with h5py.File(tmp, "w") as f:
            f.attrs[_SCHEMA_VERSION] = _SCHEMA_V3
            manifest_ds = f.create_dataset(
                _MANIFEST,
                data=np.frombuffer(payload, dtype=np.uint8),
                compression="gzip",
                compression_opts=4,
                shuffle=True,
            )
            manifest_ds.attrs[_MANIFEST_ENCODING] = "gzip"
            index_ds = f.create_dataset(
                _ARRAY_INDEX,
                data=np.frombuffer(index_payload, dtype=np.uint8),
                compression="gzip",
                compression_opts=4,
                shuffle=True,
            )
            index_ds.attrs[_MANIFEST_ENCODING] = "gzip"
            group = f.create_group(_ARENAS)
            datasets = []
            for meta in plan["arenas"]:
                dtype = np.dtype(meta["dtype"])
                count = meta["bytes"] // dtype.itemsize
                chunk = max(1, min(count, _ARENA_CHUNK_BYTES // dtype.itemsize))
                ds = group.create_dataset(
                    meta["name"],
                    shape=(count,),
                    dtype=dtype,
                    chunks=(chunk,),
                    compression="gzip",
                    compression_opts=4,
                    shuffle=True,
                )
                ds.attrs[_MANIFEST_ENCODING] = "gzip"
                datasets.append(ds)
            for (_key, arr), entry in zip(items, plan["arrays"], strict=True):
                if entry["alias_of"] is not None or entry["length"] == 0:
                    continue
                itemsize = arr.dtype.itemsize
                start = entry["offset"] // itemsize
                flat = np.ascontiguousarray(arr).reshape(-1)
                _write_arena_slice(
                    datasets[entry["arena"]], start, start + flat.size, flat
                )
        with open(tmp, "rb") as fh:
            os.fsync(fh.fileno())
        os.replace(tmp, dest)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return dest


def write_h5_byte_xor(path, manifest: dict, arrays: Mapping[str, np.ndarray]) -> Path:
    """Atomically write opt-in schema v4 with exact per-array byte-XOR/XZ payloads.

    Public names, dtype, shape, manifest, aliases and reader semantics match the
    other schemas. The payload dataset is an uncompressed uint8 stream; each
    array span declares either raw bytes or one independent complete XZ stream.
    """
    from knee.encoding.byte_xor import encode_array

    dest = Path(path)
    manifest_payload = _serialize_manifest(manifest)
    items: list[tuple[str, np.ndarray]] = []
    for key, array in arrays.items():
        if not isinstance(key, str):
            raise ManifestError(f"array key must be str: {key!r}")
        try:
            key.encode("utf-8")
        except UnicodeEncodeError as error:
            raise ManifestError(f"array key not UTF-8 encodable: {key!r}") from error
        if not isinstance(array, np.ndarray):
            raise UnsupportedArrayDtypeError(f"array {key!r} must be a numpy ndarray")
        _check_dtype(array.dtype, key)
        items.append((key, array))

    dedup = _plan_compact(items)
    entries: list[dict[str, Any]] = []
    canonical: dict[int, dict[str, Any]] = {}
    h5py = _h5py()
    fd, tmp_name = tempfile.mkstemp(
        dir=dest.parent, prefix=dest.name + ".", suffix=".part"
    )
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with h5py.File(tmp, "w") as file:
            file.attrs[_SCHEMA_VERSION] = _SCHEMA_V4
            manifest_ds = file.create_dataset(
                _MANIFEST,
                data=np.frombuffer(manifest_payload, dtype=np.uint8),
                compression="gzip",
                compression_opts=4,
                shuffle=True,
            )
            manifest_ds.attrs[_MANIFEST_ENCODING] = "gzip"
            payload_ds = file.create_dataset(
                _BYTE_PAYLOAD,
                shape=(0,),
                maxshape=(None,),
                chunks=(_ARENA_CHUNK_BYTES,),
                dtype=np.uint8,
            )
            payload_ds.attrs[_MANIFEST_ENCODING] = "per-array-codec"
            cursor = 0
            for index, ((key, array), prior) in enumerate(
                zip(items, dedup["arrays"], strict=True)
            ):
                base: dict[str, Any] = {
                    "key": key,
                    "dtype": array.dtype.str,
                    "shape": [int(size) for size in array.shape],
                    "codec": "raw",
                    "offset": 0,
                    "length": 0,
                    "raw_length": int(array.size) * array.dtype.itemsize,
                    "predictor_stride": None,
                    "alias_of": None,
                }
                alias_of = prior["alias_of"]
                if alias_of is not None:
                    target = canonical[alias_of]
                    base.update(
                        codec=target["codec"],
                        offset=target["offset"],
                        length=target["length"],
                        raw_length=target["raw_length"],
                        predictor_stride=target["predictor_stride"],
                        alias_of=alias_of,
                    )
                elif base["raw_length"]:
                    encoded = encode_array(array, preset=6)
                    blob = np.frombuffer(encoded.payload, dtype=np.uint8)
                    base.update(
                        codec=encoded.codec,
                        offset=cursor,
                        length=int(blob.size),
                        raw_length=encoded.raw_length,
                        predictor_stride=encoded.predictor_stride,
                    )
                    payload_ds.resize((cursor + blob.size,))
                    payload_ds[cursor : cursor + blob.size] = blob
                    cursor += int(blob.size)
                entries.append(base)
                if alias_of is None:
                    canonical[index] = base

            index_payload = json.dumps(
                {"format": _BYTE_FORMAT, "arrays": entries},
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
            index_ds = file.create_dataset(
                _ARRAY_INDEX,
                data=np.frombuffer(index_payload, dtype=np.uint8),
                compression="gzip",
                compression_opts=4,
                shuffle=True,
            )
            index_ds.attrs[_MANIFEST_ENCODING] = "gzip"
        with open(tmp, "rb") as stream:
            os.fsync(stream.fileno())
        os.replace(tmp, dest)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return dest


def write_h5_modular(
    path, manifest: dict, arrays: Mapping[str, np.ndarray], *, preset: int = 0
) -> Path:
    """Atomically write opt-in schema v5 with shortest exact per-array payloads.

    The transport XZ preset defaults to 0 for lower writer cost. V5 preserves
    all public keys, order, dtype, shape, manifest and aliases. Each unique
    nonempty array stores the shortest of raw bytes, v4 row-XOR/XZ, or
    modular-row/XZ bytes. V1-v4 remain separate formats and are unchanged.
    """
    from knee.encoding.byte_xor import encode_array_hybrid

    dest = Path(path)
    manifest_payload = _serialize_manifest(manifest)
    items: list[tuple[str, np.ndarray]] = []
    for key, array in arrays.items():
        if not isinstance(key, str):
            raise ManifestError(f"array key must be str: {key!r}")
        try:
            key.encode("utf-8")
        except UnicodeEncodeError as error:
            raise ManifestError(f"array key not UTF-8 encodable: {key!r}") from error
        if not isinstance(array, np.ndarray):
            raise UnsupportedArrayDtypeError(f"array {key!r} must be a numpy ndarray")
        _check_dtype(array.dtype, key)
        items.append((key, array))

    dedup = _plan_compact(items)
    entries: list[dict[str, Any]] = []
    canonical: dict[int, dict[str, Any]] = {}
    h5py = _h5py()
    fd, tmp_name = tempfile.mkstemp(
        dir=dest.parent, prefix=dest.name + ".", suffix=".part"
    )
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with h5py.File(tmp, "w") as file:
            file.attrs[_SCHEMA_VERSION] = _SCHEMA_V5
            manifest_ds = file.create_dataset(
                _MANIFEST,
                data=np.frombuffer(manifest_payload, dtype=np.uint8),
                compression="gzip",
                compression_opts=4,
                shuffle=True,
            )
            manifest_ds.attrs[_MANIFEST_ENCODING] = "gzip"
            payload_ds = file.create_dataset(
                _BYTE_PAYLOAD,
                shape=(0,),
                maxshape=(None,),
                chunks=(_ARENA_CHUNK_BYTES,),
                dtype=np.uint8,
            )
            payload_ds.attrs[_MANIFEST_ENCODING] = "per-array-codec"
            cursor = 0
            for index, ((key, array), prior) in enumerate(
                zip(items, dedup["arrays"], strict=True)
            ):
                base: dict[str, Any] = {
                    "key": key,
                    "dtype": array.dtype.str,
                    "shape": [int(size) for size in array.shape],
                    "codec": "raw",
                    "offset": 0,
                    "length": 0,
                    "raw_length": int(array.size) * array.dtype.itemsize,
                    "predictor_stride": None,
                    "alias_of": None,
                }
                alias_of = prior["alias_of"]
                if alias_of is not None:
                    target = canonical[alias_of]
                    base.update(
                        codec=target["codec"],
                        offset=target["offset"],
                        length=target["length"],
                        raw_length=target["raw_length"],
                        predictor_stride=target["predictor_stride"],
                        alias_of=alias_of,
                    )
                elif base["raw_length"]:
                    encoded = encode_array_hybrid(array, preset=preset)
                    blob = np.frombuffer(encoded.payload, dtype=np.uint8)
                    base.update(
                        codec=encoded.codec,
                        offset=cursor,
                        length=int(blob.size),
                        raw_length=encoded.raw_length,
                        predictor_stride=encoded.predictor_stride,
                    )
                    payload_ds.resize((cursor + blob.size,))
                    payload_ds[cursor : cursor + blob.size] = blob
                    cursor += int(blob.size)
                entries.append(base)
                if alias_of is None:
                    canonical[index] = base

            index_payload = json.dumps(
                {"format": _MODULAR_FORMAT, "arrays": entries},
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
            index_ds = file.create_dataset(
                _ARRAY_INDEX,
                data=np.frombuffer(index_payload, dtype=np.uint8),
                compression="gzip",
                compression_opts=4,
                shuffle=True,
            )
            index_ds.attrs[_MANIFEST_ENCODING] = "gzip"
        with open(tmp, "rb") as stream:
            os.fsync(stream.fileno())
        os.replace(tmp, dest)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return dest


class _CompactEntry(NamedTuple):
    dtype: np.dtype
    shape: tuple[int, ...]
    arena: str | None
    offset: int
    length: int


class _ByteEntry(NamedTuple):
    dtype: np.dtype
    shape: tuple[int, ...]
    codec: str
    offset: int
    length: int
    raw_length: int
    predictor_stride: int | None
    alias_of: int | None


class _LazyArrays(Mapping):
    def __init__(self, reader: H5Reader):
        self._reader = reader

    def __getitem__(self, key):
        self._reader._require_open()
        try:
            index = self._reader._index[key]
        except (KeyError, TypeError):
            raise KeyError(key) from None
        return self._reader._read(index)

    def __iter__(self) -> Iterator[str]:
        self._reader._require_open()
        return iter(list(self._reader._index))

    def __len__(self) -> int:
        self._reader._require_open()
        return len(self._reader._index)

    def __contains__(self, key) -> bool:
        self._reader._require_open()
        return key in self._reader._index


class H5Reader:
    """Open store: ``.manifest`` dict and lazy ``.arrays`` Mapping (one load per access)."""

    def __init__(self, file, manifest: dict, index: dict[str, Any]):
        self._file = file
        self._manifest = manifest
        self._index = index
        self.arrays: Mapping[str, np.ndarray] = _LazyArrays(self)

    @property
    def manifest(self) -> dict:
        self._require_open()
        return self._manifest

    @property
    def closed(self) -> bool:
        return self._file is None

    def _require_open(self) -> None:
        if self._file is None:
            raise ReaderClosedError("H5 reader is closed")

    def _read(self, name) -> np.ndarray:
        """Load exactly one dataset (v1/v2 internal name) or array span (v3 entry)."""
        if isinstance(name, _CompactEntry):
            return self._read_compact(name)
        if isinstance(name, _ByteEntry):
            return self._read_byte(name)
        file = self._file
        if file is None:
            raise ReaderClosedError("H5 reader is closed")
        try:
            ds = file[_ARRAYS][name]
            expected = np.dtype(ds.attrs["dtype"])
            value = ds[()]
            # h5py returns scalar datasets as NumPy scalars in native byte order.
            # Reapply the declared dtype so scalar arrays retain the file dtype.
            arr = (
                np.asarray(value, dtype=expected)
                if ds.shape == ()
                else np.asarray(value)
            )
        except (OSError, KeyError, ValueError, TypeError) as e:
            raise MalformedH5Error(f"unreadable array dataset {name!r}: {e}") from e
        if arr.dtype != expected or arr.shape != tuple(ds.shape):
            raise MalformedH5Error(f"dtype/shape mismatch in dataset {name!r}")
        return arr

    def _read_compact(self, entry: _CompactEntry) -> np.ndarray:
        """Read only the entry's byte span from its arena; reconstruct dtype + shape."""
        file = self._file
        if file is None:
            raise ReaderClosedError("H5 reader is closed")
        dtype = entry.dtype
        if entry.length == 0:
            return np.empty(entry.shape, dtype=dtype)
        itemsize = dtype.itemsize
        start = entry.offset // itemsize
        stop = start + entry.length // itemsize
        try:
            ds = file[_ARENAS][entry.arena]
            value = ds[start:stop]
        except (OSError, KeyError, ValueError, TypeError) as e:
            raise MalformedH5Error(f"unreadable arena span {entry.arena!r}: {e}") from e
        if (
            not isinstance(value, np.ndarray)
            or value.dtype.str != dtype.str
            or value.shape != (stop - start,)
        ):
            raise MalformedH5Error(f"dtype/shape mismatch in arena {entry.arena!r}")
        return np.ascontiguousarray(value).reshape(entry.shape)

    def _read_byte(self, entry: _ByteEntry) -> np.ndarray:
        """Read and decode one v4/v5 payload span without loading neighboring arrays."""
        file = self._file
        if file is None:
            raise ReaderClosedError("H5 reader is closed")
        if entry.length == 0:
            return np.empty(entry.shape, dtype=entry.dtype)
        try:
            dataset = file[_BYTE_PAYLOAD]
            payload_array = dataset[entry.offset : entry.offset + entry.length]
        except (OSError, KeyError, ValueError, TypeError) as error:
            raise MalformedH5Error(f"unreadable byte payload span: {error}") from error
        if payload_array.dtype != np.dtype(np.uint8) or payload_array.shape != (
            entry.length,
        ):
            raise MalformedH5Error("byte payload span has invalid dtype or length")
        from knee.encoding.byte_xor import decode_array

        try:
            return decode_array(
                payload_array.tobytes(),
                entry.codec,
                entry.dtype,
                entry.shape,
                entry.raw_length,
                entry.predictor_stride,
            )
        except (TypeError, ValueError, OverflowError) as error:
            raise MalformedH5Error(f"invalid byte payload: {error}") from error

    def close(self) -> None:
        f, self._file = self._file, None
        if f is not None:
            f.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def _reject_nonstandard_constant(value: str):
    raise ValueError(f"non-standard JSON constant {value}")


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _parse_dtype(text: object, where: str) -> np.dtype:
    if not isinstance(text, str):
        raise MalformedH5Error(f"dtype of {where} must be a string")
    try:
        dtype = np.dtype(text)
    except (TypeError, ValueError, SyntaxError) as e:
        raise MalformedH5Error(f"bad dtype {text!r} for {where}") from e
    if (
        dtype.hasobject
        or dtype.fields is not None
        or dtype.kind not in "biufc"
        or dtype.str != text
        or dtype.itemsize <= 0
    ):
        raise MalformedH5Error(f"unsupported dtype {text!r} for {where}")
    return dtype


def _legacy_index(f, h5py, schema_version: int) -> dict[str, str]:
    group = f[_ARRAYS]
    index: dict[str, str] = {}
    names = sorted(group)
    has_key_table = _ARRAY_KEYS in f
    if (schema_version == _SCHEMA_V2) != has_key_table:
        raise MalformedH5Error("schema version and array key table disagree")
    if schema_version == _SCHEMA_V2:
        keys_ds = f[_ARRAY_KEYS]
        if (
            not isinstance(keys_ds, h5py.Dataset)
            or keys_ds.dtype != np.dtype(np.uint8)
            or keys_ds.ndim != 1
        ):
            raise MalformedH5Error(
                "array_keys_json must be a one-dimensional uint8 dataset"
            )
        if (
            keys_ds.attrs.get(_MANIFEST_ENCODING) != "gzip"
            or keys_ds.compression != "gzip"
        ):
            raise MalformedH5Error("v2 array key table encoding is unsupported")
        keys = json.loads(bytes(keys_ds[()].tobytes()).decode("utf-8"))
        expected_names = (
            [f"{i:08d}" for i in range(len(keys))] if isinstance(keys, list) else []
        )
        if (
            not isinstance(keys, list)
            or len(keys) != len(names)
            or names != expected_names
            or any(not isinstance(key, str) for key in keys)
            or len(set(keys)) != len(keys)
        ):
            raise MalformedH5Error("array key index is malformed")
        for name, key in zip(names, keys, strict=True):
            ds = group[name]
            if not isinstance(ds, h5py.Dataset):
                raise MalformedH5Error(f"non-dataset member {name!r}")
            _check_dtype(ds.dtype, name)
            stored_key = ds.attrs["key"]
            if not isinstance(stored_key, str) or stored_key not in keys:
                raise MalformedH5Error(f"bad canonical key on {name!r}")
            index[key] = name
    else:
        for name in names:
            ds = group[name]
            if not isinstance(ds, h5py.Dataset):
                raise MalformedH5Error(f"non-dataset member {name!r}")
            _check_dtype(ds.dtype, name)
            key = ds.attrs["key"]
            if not isinstance(key, str) or key in index:
                raise MalformedH5Error(f"bad or duplicate key on {name!r}")
            index[key] = name
    return index


_ENTRY_FIELDS = {"key", "dtype", "shape", "arena", "offset", "length", "alias_of"}


def _compact_index(f, h5py) -> dict[str, _CompactEntry]:
    """Validate the v3 index against the arenas and return key -> span entries."""
    if _ARRAYS in f or _ARRAY_KEYS in f:
        raise MalformedH5Error("v3 store must not contain legacy array members")
    table_ds = f[_ARRAY_INDEX]
    if (
        not isinstance(table_ds, h5py.Dataset)
        or table_ds.dtype != np.dtype(np.uint8)
        or table_ds.ndim != 1
    ):
        raise MalformedH5Error(
            "array_index_json must be a one-dimensional uint8 dataset"
        )
    if (
        table_ds.attrs.get(_MANIFEST_ENCODING) != "gzip"
        or table_ds.compression != "gzip"
    ):
        raise MalformedH5Error("v3 array index encoding is unsupported")
    table = json.loads(
        bytes(table_ds[()].tobytes()).decode("utf-8"),
        parse_constant=_reject_nonstandard_constant,
    )
    if (
        not isinstance(table, dict)
        or set(table) != {"format", "arenas", "arrays"}
        or table["format"] != _ARENA_FORMAT
        or not isinstance(table["arenas"], list)
        or not isinstance(table["arrays"], list)
    ):
        raise MalformedH5Error("v3 array index is malformed")
    arena_meta = table["arenas"]
    arena_group = f[_ARENAS]
    if not isinstance(arena_group, h5py.Group):
        raise MalformedH5Error("arenas must be a group")
    if sorted(arena_group) != [f"{i:08d}" for i in range(len(arena_meta))]:
        raise MalformedH5Error("arena set disagrees with index")
    arenas: list[tuple[str, np.dtype, int]] = []
    for i, meta in enumerate(arena_meta):
        name = f"{i:08d}"
        if (
            not isinstance(meta, dict)
            or set(meta) != {"name", "dtype", "bytes"}
            or meta["name"] != name
        ):
            raise MalformedH5Error(f"arena {name} metadata is malformed")
        dtype = _parse_dtype(meta["dtype"], f"arena {name}")
        nbytes = meta["bytes"]
        if not _is_int(nbytes) or nbytes <= 0 or nbytes % dtype.itemsize:
            raise MalformedH5Error(f"arena {name} byte size is invalid")
        ds = arena_group[name]
        if (
            not isinstance(ds, h5py.Dataset)
            or ds.dtype.str != dtype.str
            or ds.shape != (nbytes // dtype.itemsize,)
        ):
            raise MalformedH5Error(f"arena {name} disagrees with its declaration")
        if ds.attrs.get(_MANIFEST_ENCODING) != "gzip" or ds.compression != "gzip":
            raise MalformedH5Error("v3 arena encoding is unsupported")
        arenas.append((name, dtype, nbytes))

    entries: list[_CompactEntry] = []
    alias_flags: list[bool] = []
    result: dict[str, _CompactEntry] = {}
    spans: list[list[tuple[int, int]]] = [[] for _ in arenas]
    for i, meta in enumerate(table["arrays"]):
        if not isinstance(meta, dict) or set(meta) != _ENTRY_FIELDS:
            raise MalformedH5Error(f"array entry {i} is malformed")
        key = meta["key"]
        if not isinstance(key, str) or key in result:
            raise MalformedH5Error(f"bad or duplicate array key at entry {i}")
        dtype = _parse_dtype(meta["dtype"], f"entry {i}")
        shape_raw = meta["shape"]
        if not isinstance(shape_raw, list) or any(
            not _is_int(n) or n < 0 for n in shape_raw
        ):
            raise MalformedH5Error(f"shape of entry {i} is invalid")
        from knee.encoding.byte_xor import _validate_numpy_shape

        try:
            count = _validate_numpy_shape(tuple(shape_raw), dtype.itemsize)
        except ValueError as error:
            raise MalformedH5Error(
                f"shape of entry {i} exceeds NumPy limits: {error}"
            ) from error
        arena, offset, length, alias_of = (
            meta["arena"],
            meta["offset"],
            meta["length"],
            meta["alias_of"],
        )
        if not _is_int(offset) or not _is_int(length) or offset < 0 or length < 0:
            raise MalformedH5Error(f"offset/length of entry {i} is invalid")
        if length != count * dtype.itemsize:
            raise MalformedH5Error(
                f"length of entry {i} disagrees with dtype and shape"
            )
        if length == 0:
            if arena is not None or offset != 0 or alias_of is not None:
                raise MalformedH5Error(f"empty entry {i} must not reference storage")
            arena_name = None
        else:
            if not _is_int(arena) or not 0 <= arena < len(arenas):
                raise MalformedH5Error(f"arena of entry {i} is invalid")
            arena_name, arena_dtype, arena_bytes = arenas[arena]
            if arena_dtype.str != dtype.str:
                raise MalformedH5Error(f"entry {i} dtype disagrees with its arena")
            if offset % dtype.itemsize or offset + length > arena_bytes:
                raise MalformedH5Error(
                    f"entry {i} span is misaligned or overruns arena"
                )
        entry = _CompactEntry(dtype, tuple(shape_raw), arena_name, offset, length)
        if alias_of is not None:
            if not _is_int(alias_of) or not 0 <= alias_of < i or alias_flags[alias_of]:
                raise MalformedH5Error(f"alias target of entry {i} is invalid")
            if entries[alias_of] != entry:
                raise MalformedH5Error(f"alias entry {i} disagrees with its target")
            alias_flags.append(True)
        else:
            alias_flags.append(False)
            if length:
                spans[arena].append((offset, offset + length))
        entries.append(entry)
        result[key] = entry
    for (name, _dtype, nbytes), arena_spans in zip(arenas, spans, strict=True):
        cursor = 0
        for start, end in sorted(arena_spans):
            if start != cursor:
                raise MalformedH5Error(
                    f"arena {name} has unreferenced or overlapping bytes"
                )
            cursor = end
        if cursor != nbytes:
            raise MalformedH5Error(
                f"arena {name} has unreferenced or overlapping bytes"
            )
    return result


def _byte_index(file, h5py, schema_version: int = _SCHEMA_V4) -> dict[str, _ByteEntry]:
    """Validate v4/v5 descriptors and exact contiguous payload coverage."""
    if _ARRAYS in file or _ARRAY_KEYS in file or _ARENAS in file:
        raise MalformedH5Error("v4 store contains members from another array schema")
    if _ARRAY_INDEX not in file or _BYTE_PAYLOAD not in file:
        raise MalformedH5Error("v4 index or payload is missing")
    table_ds = file[_ARRAY_INDEX]
    if (
        not isinstance(table_ds, h5py.Dataset)
        or table_ds.dtype != np.dtype(np.uint8)
        or table_ds.ndim != 1
        or table_ds.attrs.get(_MANIFEST_ENCODING) != "gzip"
        or table_ds.compression != "gzip"
    ):
        raise MalformedH5Error("v4 array index encoding is unsupported")
    payload_ds = file[_BYTE_PAYLOAD]
    if (
        not isinstance(payload_ds, h5py.Dataset)
        or payload_ds.dtype != np.dtype(np.uint8)
        or payload_ds.ndim != 1
        or payload_ds.attrs.get(_MANIFEST_ENCODING) != "per-array-codec"
        or payload_ds.compression is not None
    ):
        raise MalformedH5Error("v4 byte payload encoding is unsupported")
    try:
        table = json.loads(
            bytes(table_ds[()].tobytes()).decode("utf-8"),
            parse_constant=_reject_nonstandard_constant,
        )
    except (ValueError, UnicodeDecodeError) as error:
        raise MalformedH5Error(f"v4 array index is malformed: {error}") from error
    if (
        not isinstance(table, dict)
        or set(table) != {"format", "arrays"}
        or table["format"]
        != (_MODULAR_FORMAT if schema_version == _SCHEMA_V5 else _BYTE_FORMAT)
        or not isinstance(table["arrays"], list)
    ):
        raise MalformedH5Error("v4 array index format is malformed")

    legacy_fields = {
        "key",
        "dtype",
        "shape",
        "codec",
        "offset",
        "length",
        "raw_length",
        "alias_of",
    }
    fields = legacy_fields | {"predictor_stride"}
    result: dict[str, _ByteEntry] = {}
    entries: list[_ByteEntry] = []
    aliases: list[bool] = []
    spans: list[tuple[int, int]] = []
    from knee.encoding.byte_xor import (
        BYTE_MODULAR_ROW_SHUFFLE,
        BYTE_XOR_ROW_SHUFFLE,
        BYTE_XOR_SHUFFLE,
        RAW,
    )

    for index, meta in enumerate(table["arrays"]):
        if not isinstance(meta, dict) or set(meta) not in (legacy_fields, fields):
            raise MalformedH5Error(f"v4 array entry {index} is malformed")
        key = meta["key"]
        if not isinstance(key, str) or key in result:
            raise MalformedH5Error(f"bad or duplicate v4 key at entry {index}")
        dtype = _parse_dtype(meta["dtype"], f"v4 entry {index}")
        shape_raw = meta["shape"]
        if not isinstance(shape_raw, list) or any(
            not _is_int(size) or size < 0 for size in shape_raw
        ):
            raise MalformedH5Error(f"shape of v4 entry {index} is invalid")
        from knee.encoding.byte_xor import _validate_numpy_shape

        try:
            count = _validate_numpy_shape(tuple(shape_raw), dtype.itemsize)
        except ValueError as error:
            raise MalformedH5Error(
                f"shape dimension or byte size of v4 entry {index} exceeds NumPy limits: {error}"
            ) from error
        raw_length = meta["raw_length"]
        offset = meta["offset"]
        length = meta["length"]
        alias_of = meta["alias_of"]
        codec = meta["codec"]
        predictor_stride = meta.get("predictor_stride")
        expected_stride = max(1, prod(shape_raw[1:])) if len(shape_raw) > 1 else 1
        if predictor_stride is not None and (
            not _is_int(predictor_stride) or predictor_stride != expected_stride
        ):
            raise MalformedH5Error(f"predictor stride of v4 entry {index} is invalid")
        if not _is_int(raw_length) or raw_length != count * dtype.itemsize:
            raise MalformedH5Error(f"raw length of v4 entry {index} is invalid")
        if not _is_int(offset) or not _is_int(length) or offset < 0 or length < 0:
            raise MalformedH5Error(f"offset/length of v4 entry {index} is invalid")
        allowed_codecs = (RAW, BYTE_XOR_SHUFFLE, BYTE_XOR_ROW_SHUFFLE)
        if schema_version == _SCHEMA_V5:
            allowed_codecs = (*allowed_codecs, BYTE_MODULAR_ROW_SHUFFLE)
        if codec not in allowed_codecs:
            raise MalformedH5Error(
                f"codec of v{schema_version} entry {index} is invalid"
            )
        if codec in (BYTE_XOR_ROW_SHUFFLE, BYTE_MODULAR_ROW_SHUFFLE) and (
            predictor_stride != expected_stride
        ):
            raise MalformedH5Error(
                f"row predictor stride of v{schema_version} entry {index} is missing"
            )
        if codec == BYTE_XOR_SHUFFLE and predictor_stride is not None:
            raise MalformedH5Error(
                f"legacy predictor stride of v4 entry {index} is invalid"
            )
        if raw_length == 0:
            if offset != 0 or length != 0 or codec != RAW or alias_of is not None:
                raise MalformedH5Error(
                    f"empty v4 entry {index} must not reference storage"
                )
        else:
            if length == 0 or offset + length > payload_ds.shape[0]:
                raise MalformedH5Error(f"payload span of v4 entry {index} is invalid")
            if codec == RAW and length != raw_length:
                raise MalformedH5Error(
                    f"raw payload length of v4 entry {index} is invalid"
                )
        entry = _ByteEntry(
            dtype,
            tuple(shape_raw),
            codec,
            offset,
            length,
            raw_length,
            predictor_stride,
            alias_of,
        )
        if alias_of is not None:
            if not _is_int(alias_of) or not 0 <= alias_of < index or aliases[alias_of]:
                raise MalformedH5Error(f"alias target of v4 entry {index} is invalid")
            target = entries[alias_of]
            if (
                entry.dtype.str,
                entry.shape,
                entry.codec,
                entry.offset,
                entry.length,
                entry.raw_length,
                entry.predictor_stride,
            ) != (
                target.dtype.str,
                target.shape,
                target.codec,
                target.offset,
                target.length,
                target.raw_length,
                target.predictor_stride,
            ):
                raise MalformedH5Error(f"alias entry {index} disagrees with its target")
            aliases.append(True)
        else:
            aliases.append(False)
            if length:
                spans.append((offset, offset + length))
        entries.append(entry)
        result[key] = entry
    cursor = 0
    for start, stop in sorted(spans):
        if start != cursor:
            raise MalformedH5Error("v4 payload has unreferenced or overlapping bytes")
        cursor = stop
    if cursor != payload_ds.shape[0]:
        raise MalformedH5Error("v4 payload has unreferenced or overlapping bytes")
    return result


@contextmanager
def open_h5(path):
    """Context manager yielding an :class:`H5Reader`; closed on exit."""
    p = Path(path)
    h5py = _h5py()
    if not p.exists():
        raise FileNotFoundError(str(p))
    try:
        f = h5py.File(p, "r")
    except (OSError, ValueError) as e:
        raise MalformedH5Error(f"not a readable HDF5 file: {e}") from e
    try:
        try:
            schema_version = f.attrs.get(_SCHEMA_VERSION, _SCHEMA_V1)
            if (
                not isinstance(schema_version, (int, np.integer))
                or isinstance(schema_version, (bool, np.bool_))
                or int(schema_version)
                not in (_SCHEMA_V1, _SCHEMA_V2, _SCHEMA_V3, _SCHEMA_V4, _SCHEMA_V5)
            ):
                raise MalformedH5Error(
                    f"unsupported H5 schema version: {schema_version!r}"
                )
            schema_version = int(schema_version)
            manifest_ds = f[_MANIFEST]
            if (
                not isinstance(manifest_ds, h5py.Dataset)
                or manifest_ds.dtype != np.dtype(np.uint8)
                or manifest_ds.ndim != 1
            ):
                raise MalformedH5Error(
                    "manifest_json must be a one-dimensional uint8 dataset"
                )
            manifest_encoding = manifest_ds.attrs.get(_MANIFEST_ENCODING)
            if schema_version in (_SCHEMA_V2, _SCHEMA_V3, _SCHEMA_V4, _SCHEMA_V5):
                if manifest_encoding != "gzip" or manifest_ds.compression != "gzip":
                    raise MalformedH5Error(
                        f"v{schema_version} manifest encoding is unsupported"
                    )
            elif manifest_encoding is not None or manifest_ds.compression is not None:
                raise MalformedH5Error("v1 manifest must use the legacy raw encoding")
            raw = bytes(manifest_ds[()].tobytes())

            manifest = json.loads(
                raw.decode("utf-8"), parse_constant=_reject_nonstandard_constant
            )
            if schema_version == _SCHEMA_V3:
                index = _compact_index(f, h5py)
            elif schema_version in (_SCHEMA_V4, _SCHEMA_V5):
                index = _byte_index(f, h5py, schema_version)
            else:
                index = _legacy_index(f, h5py, schema_version)
        except H5StoreError:
            raise
        except (OSError, KeyError, ValueError, TypeError, UnicodeDecodeError) as e:
            raise MalformedH5Error(f"malformed store: {e}") from e
        if not isinstance(manifest, dict):
            raise MalformedH5Error("manifest is not a JSON object")
        reader = H5Reader(f, manifest, index)
    except BaseException:
        f.close()
        raise
    try:
        yield reader
    finally:
        reader.close()
