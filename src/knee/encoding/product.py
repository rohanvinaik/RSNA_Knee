"""Uniform read access to a retained encoding product: legacy NPZ+JSON or a single H5.

`open_product(path)` yields a `Product` with `.manifest` and lazy, verified `.arrays`.
Legacy: `path` is the manifest (`.json` / `.json.xz`); its `archive` field is resolved and
opened with `open_arrays`. H5: `path` is the `.h5` product itself. Each array is checked
against manifest `encoded_arrays` (dtype, shape, digest) on first access. Nothing is
silently absent: every failure is a named error below.
"""

from __future__ import annotations

import lzma
import zipfile
from collections.abc import Iterator, Mapping
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Any

import numpy as np

from knee.array_archive import open_arrays
from knee.encoding import h5_store
from knee.json_store import load_json, resolve_json_path
from knee.receipt import digest

__all__ = [
    "ArchiveReferenceError",
    "ArrayMismatchError",
    "DigestMismatchError",
    "DtypeMismatchError",
    "MissingArrayError",
    "Product",
    "ProductClosedError",
    "ProductError",
    "ProductMalformedError",
    "ProductNotFoundError",
    "ShapeMismatchError",
    "UnsupportedArrayError",
    "VerifiedArrays",
    "open_product",
]


class ProductError(Exception):
    """Base of all named failures of this module."""


class ProductNotFoundError(ProductError, FileNotFoundError):
    """Manifest (legacy) or product (H5) file does not exist."""


class ProductMalformedError(ProductError, ValueError):
    """Manifest/product metadata unreadable or structurally invalid."""


class ArchiveReferenceError(ProductError, ValueError):
    """Legacy manifest `archive` is unsafe, not a string, or does not exist."""


class ProductClosedError(ProductError, ValueError):
    """Access after the product was closed."""


class MissingArrayError(ProductError, KeyError):
    """Requested array (or a manifest-listed array) is absent from the archive."""


class UnsupportedArrayError(ProductError, TypeError):
    """Array is not described by the manifest, or is not a plain numeric ndarray."""


class ArrayMismatchError(ProductError, ValueError):
    """Array disagrees with its manifest entry."""


class DigestMismatchError(ArrayMismatchError):
    pass


class ShapeMismatchError(ArrayMismatchError):
    pass


class DtypeMismatchError(ArrayMismatchError):
    pass


def _expected_arrays(manifest: Any) -> dict[str, tuple[str, tuple[int, ...], str]]:
    if not isinstance(manifest, dict):
        raise ProductMalformedError("manifest_not_an_object")
    encoded = manifest.get("encoded_arrays")
    if not isinstance(encoded, dict):
        raise ProductMalformedError("manifest_encoded_arrays_required")
    out: dict[str, tuple[str, tuple[int, ...], str]] = {}
    for name, entry in encoded.items():
        if not isinstance(name, str) or not isinstance(entry, dict):
            raise ProductMalformedError(f"manifest_array_entry_invalid:{name!r}")
        dg, shape, dtype = entry.get("digest"), entry.get("shape"), entry.get("dtype")
        if (
            not isinstance(dg, str)
            or not isinstance(dtype, str)
            or not isinstance(shape, list)
            or any(
                not isinstance(n, int) or isinstance(n, bool) or n < 0 for n in shape
            )
        ):
            raise ProductMalformedError(f"manifest_array_entry_invalid:{name!r}")
        out[name] = (dg, tuple(shape), dtype)
    return out


def _immutable_snapshot(array: np.ndarray) -> np.ndarray:
    """Return an exact C-order snapshot backed by immutable Python bytes."""
    payload = array.tobytes(order="C")
    return np.frombuffer(payload, dtype=array.dtype).reshape(array.shape)


class VerifiedArrays(Mapping):
    """Lazy mapping over the archive's arrays; verifies each on first access."""

    def __init__(self, product: Product, source: Mapping, expected: dict):
        self._product = product
        self._source = source
        self._expected = expected
        self._cache: dict[str, np.ndarray] = {}

    @property
    def files(self) -> list[str]:
        return list(self)

    def __getitem__(self, name):
        self._product._require_open()
        if name in self._cache:
            return self._cache[name]
        if name not in self._source:
            raise MissingArrayError(f"missing_array:{name!r}")
        expected = self._expected.get(name)
        if expected is None:
            raise UnsupportedArrayError(f"array_not_in_manifest:{name!r}")
        try:
            array = self._source[name]
        except h5_store.H5StoreError as error:
            raise ProductMalformedError(
                f"array_storage_unreadable:{name!r}:{error}"
            ) from error
        self._verify(name, array, expected)
        immutable = _immutable_snapshot(array)
        self._cache[name] = immutable
        return immutable

    def close(self) -> None:
        self._cache.clear()

    @staticmethod
    def _verify(name, array, expected) -> None:
        want_digest, want_shape, want_dtype = expected
        if (
            not isinstance(array, np.ndarray)
            or array.dtype.hasobject
            or array.dtype.kind not in "biufc"
        ):
            raise UnsupportedArrayError(f"unsupported_array:{name!r}")
        if array.dtype.str != want_dtype:
            raise DtypeMismatchError(
                f"dtype_mismatch:{name!r}:{array.dtype.str}!={want_dtype}"
            )
        if tuple(array.shape) != want_shape:
            raise ShapeMismatchError(
                f"shape_mismatch:{name!r}:{tuple(array.shape)}!={want_shape}"
            )
        if digest(array) != want_digest:
            raise DigestMismatchError(f"digest_mismatch:{name!r}")

    def get(self, name, default=None):
        self._product._require_open()
        # A manifest-listed array missing from the archive must raise, not read as absent.
        if name in self._source or name in self._expected:
            return self[name]
        return default

    def __iter__(self) -> Iterator[str]:
        self._product._require_open()
        return iter(list(self._source))

    def __len__(self) -> int:
        self._product._require_open()
        return len(self._source)

    def __contains__(self, name) -> bool:
        self._product._require_open()
        return name in self._source


class Product:
    """Open product: `.manifest`, lazy verified `.arrays`, `.storage` ('npz_xz' | 'h5')."""

    def __init__(self, storage: str, manifest: dict, source: Mapping):
        self.storage = storage
        self._manifest = manifest
        self._closed = False
        self.arrays = VerifiedArrays(self, source, _expected_arrays(manifest))

    @property
    def manifest(self) -> dict:
        self._require_open()
        return self._manifest

    @property
    def closed(self) -> bool:
        return self._closed

    def _require_open(self) -> None:
        if self._closed:
            raise ProductClosedError("product_closed")

    def close(self) -> None:
        self.arrays.close()
        self._closed = True


def _resolve_archive(manifest_file: Path, ref: object) -> Path:
    if not isinstance(ref, str) or not ref or "\0" in ref:
        raise ArchiveReferenceError(f"archive_reference_unsafe:{ref!r}")
    path = Path(ref)
    if ".." in path.parts:
        raise ArchiveReferenceError(f"archive_reference_unsafe:{ref!r}")
    candidate = path if path.is_absolute() else manifest_file.parent / path
    if candidate.is_file():
        return candidate
    raise ArchiveReferenceError(f"archive_reference_missing:{ref!r}")


def _open_legacy(path: Path, stack: ExitStack) -> Product:
    actual = resolve_json_path(path)
    if not actual.is_file():
        raise ProductNotFoundError(f"manifest_not_found:{path}")
    try:
        manifest = load_json(actual)
    except (OSError, ValueError, EOFError, lzma.LZMAError) as error:
        raise ProductMalformedError(f"manifest_unreadable:{error!r}") from error
    _expected_arrays(manifest)  # structural validation before touching the archive
    archive_path = _resolve_archive(actual, manifest.get("archive"))
    try:
        archive = open_arrays(archive_path)
    except (OSError, ValueError, EOFError, lzma.LZMAError, zipfile.BadZipFile) as error:
        raise ProductMalformedError(f"archive_unreadable:{error!r}") from error
    stack.callback(archive.close)
    return Product("npz_xz", manifest, archive)


def _open_h5(path: Path, stack: ExitStack) -> Product:
    if not path.is_file():
        raise ProductNotFoundError(f"product_not_found:{path}")
    try:
        reader = stack.enter_context(h5_store.open_h5(path))
    except h5_store.MalformedH5Error as error:
        raise ProductMalformedError(f"product_unreadable:{error}") from error
    return Product("h5", reader.manifest, reader.arrays)


@contextmanager
def open_product(path):
    """Open a legacy manifest path or an `.h5` product path; close everything on exit."""
    p = Path(path)
    with ExitStack() as stack:
        product = (
            _open_h5(p, stack) if p.name.endswith(".h5") else _open_legacy(p, stack)
        )
        stack.callback(product.close)  # registered last, so it runs first
        yield product
