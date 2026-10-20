"""Lossless adapter for retained array archives: ordinary `.npz` and outer-XZ `.npz.xz`.

`open_arrays` returns an already-open NpzFile-like Mapping. A `.npz.xz` is decompressed once
into a SpooledTemporaryFile, rewound, and read by NumPy's normal NPZ reader. `write_npz_xz`
streams members into a ZIP_STORED NPZ whose byte stream is a single standard XZ stream.
A `.npz.xz` is not loadable by plain `np.load`; use `open_arrays`. Pickle is never loaded.
"""

from __future__ import annotations

import lzma
import os
import tempfile
import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Self

import numpy as np
from numpy.lib import format as npy_format

SUFFIX = ".npz.xz"
SPOOL_MAX_BYTES = 64 * 1024 * 1024
CHUNK_BYTES = 1 << 20
_FIXED_DATE = (1980, 1, 1, 0, 0, 0)

__all__ = ["ArrayArchive", "ArrayArchiveError", "open_arrays", "write_npz_xz"]


class ArrayArchiveError(ValueError):
    """Named failure of reading an archive (truncated, malformed outer/inner, not an NPZ)."""


class ArrayArchive(Mapping):
    """Open archive: ordered `.files`, lazy one-array-at-a-time indexing, close and context manager."""

    def __init__(self, npz, spool=None):
        self._npz = npz
        self._spool = spool
        self._names = list(npz.files)

    @property
    def files(self) -> list:
        return list(self._names)

    def __getitem__(self, name):
        if self._npz is None:
            raise ValueError("archive is closed")
        if name not in self._names:
            raise KeyError(name)
        try:
            return self._npz[name]
        except KeyError:
            raise
        except ArrayArchiveError:
            raise
        except ValueError:
            raise
        except (zipfile.BadZipFile, OSError, EOFError) as e:
            raise ArrayArchiveError(f"member_malformed: {name!r}: {e!r}") from e

    def __iter__(self):
        return iter(self._names)

    def __len__(self) -> int:
        return len(self._names)

    def __contains__(self, name) -> bool:
        return name in self._names

    def close(self) -> None:
        npz, spool = self._npz, self._spool
        self._npz = None
        self._spool = None
        try:
            if npz is not None:
                npz.close()
        finally:
            if spool is not None:
                spool.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def _require_npz(obj):
    if not isinstance(obj, np.lib.npyio.NpzFile):
        if hasattr(obj, "close"):
            obj.close()
        raise ArrayArchiveError(f"not_npz: {type(obj).__name__}")
    return obj


def _open_xz(path, spill_dir) -> ArrayArchive:
    spool = tempfile.SpooledTemporaryFile(  # noqa: SIM115 - caller closes through ArrayArchive
        max_size=SPOOL_MAX_BYTES,
        mode="w+b",
        dir=None if spill_dir is None else os.fspath(spill_dir),
    )
    try:
        total = 0
        try:
            with lzma.LZMAFile(path, "rb", format=lzma.FORMAT_XZ) as lz:
                while True:
                    block = lz.read(CHUNK_BYTES)
                    if not block:
                        break
                    spool.write(block)
                    total += len(block)
        except EOFError as e:
            raise ArrayArchiveError(f"truncated: {e}") from e
        except lzma.LZMAError as e:
            raise ArrayArchiveError(f"outer_malformed: {e}") from e
        if total == 0:
            raise ArrayArchiveError("truncated: empty decompressed stream")
        spool.flush()
        spool.seek(0)
        try:
            obj = np.load(spool, allow_pickle=False)
        except (zipfile.BadZipFile, ValueError, OSError, EOFError) as e:
            raise ArrayArchiveError(f"inner_malformed: {e!r}") from e
        return ArrayArchive(_require_npz(obj), spool)
    except BaseException:
        spool.close()
        raise


def open_arrays(path, *, allow_pickle=False, spill_dir=None) -> ArrayArchive:
    """Open a legacy `.npz` or an outer-XZ `.npz.xz`. Pickle loading is not permitted."""
    if allow_pickle:
        raise ValueError("allow_pickle=True is not supported")
    p = Path(path)
    if p.name.endswith(".xz"):
        return _open_xz(p, spill_dir)
    try:
        obj = np.load(p, allow_pickle=False)
    except (zipfile.BadZipFile, EOFError) as e:
        raise ArrayArchiveError(f"inner_malformed: {e!r}") from e
    return ArrayArchive(_require_npz(obj))


def _check_name(name, seen) -> None:
    if (
        not isinstance(name, str)
        or not name
        or "/" in name
        or "\\" in name
        or "\0" in name
        or name in seen
    ):
        raise ValueError(f"invalid_or_duplicate_member_name: {name!r}")
    seen.add(name)


def write_npz_xz(path, arrays, *, preset=6, filters=None) -> None:
    """Stream (name, ndarray) members, in order, into `path` (`*.npz.xz`) via a sibling temp file,
    replacing the destination atomically only after finalization. With `filters` (a standard
    lzma filter-chain list) the chain is used and `preset` is not passed (the lzma API forbids both)."""
    dest = Path(path)
    if not dest.name.endswith(SUFFIX):
        raise ValueError("path_must_end_with_.npz.xz")
    items = arrays.items() if isinstance(arrays, Mapping) else arrays
    fd, tmp_name = tempfile.mkstemp(
        dir=dest.parent, prefix=dest.name + ".", suffix=".part"
    )
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        kw: dict[str, Any] = (
            {"filters": filters} if filters is not None else {"preset": preset}
        )
        seen: set = set()
        with (
            lzma.LZMAFile(tmp, "wb", format=lzma.FORMAT_XZ, **kw) as lz,
            zipfile.ZipFile(lz, "w", zipfile.ZIP_STORED, allowZip64=True) as zf,
        ):
            for name, arr in items:
                _check_name(name, seen)
                arr = np.asarray(arr)
                if arr.dtype.hasobject:
                    raise ValueError(f"object_dtype_rejected: {name}")
                zi = zipfile.ZipInfo(name + ".npy", date_time=_FIXED_DATE)
                zi.compress_type = zipfile.ZIP_STORED
                zi.external_attr = 0o600 << 16
                with zf.open(zi, "w", force_zip64=True) as member:
                    npy_format.write_array(member, arr, allow_pickle=False)
        os.replace(tmp, dest)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
