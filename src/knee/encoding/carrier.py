"""Exact, bank-partitioned Sylvester-Hadamard count carrier.

Each row is a distinct nonnegative count coordinate. Signed semantic values are
represented by assigning them distinct rows; they are never superposed with
signed cancellation by this module.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from functools import cached_property, lru_cache

import numpy as np

ROW_WIDTH = 512
CARRIER_VERSION = 1
_INT32 = np.iinfo(np.int32)
_INT64 = np.iinfo(np.int64)


class CarrierError(ValueError):
    """Input violates the carrier's named shape, type, or exactness contract."""


class CarrierOverflow(OverflowError):
    """An exact value cannot be represented by the carrier's int32 vector."""


@lru_cache(maxsize=1)
def _basis() -> np.ndarray:
    """One shared 512 by 512 int8 Hadamard basis (exactly 256 KiB)."""
    index = np.arange(ROW_WIDTH, dtype=np.uint16)
    parity = np.bitwise_count(index[:, None] & index[None, :]) & np.uint16(1)
    matrix = np.where(parity == 0, np.int8(1), np.int8(-1))
    matrix.flags.writeable = False
    return matrix


def _fwht(values: np.ndarray) -> np.ndarray:
    """Apply the exact natural-order Sylvester transform in O(n log n) work.

    The carrier contracts bound every encode intermediate by its nonnegative
    row-count total and every decode intermediate by 512 times an int32 value,
    so the int64 path cannot overflow. Object arrays retain exact Python-int
    arithmetic for larger encode inputs.
    """
    source = np.asarray(values)
    if source.shape != (ROW_WIDTH,):
        raise CarrierError(
            f"Hadamard vector shape must be {(ROW_WIDTH,)}, got {source.shape}"
        )
    dtype = object if source.dtype.kind == "O" else np.int64
    transformed = np.array(source, dtype=dtype, copy=True)
    width = 1
    while width < ROW_WIDTH:
        blocks = transformed.reshape(-1, 2 * width)
        left = blocks[:, :width].copy()
        right = blocks[:, width:].copy()
        blocks[:, :width] = left + right
        blocks[:, width:] = left - right
        width *= 2
    return transformed


@lru_cache(maxsize=64)
def _permutation(seed: int) -> np.ndarray:
    """One bank's realized default_rng permutation; cache is bounded independently of layouts."""
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise CarrierError("bank seed must be a nonnegative integer")
    permutation = np.random.default_rng(seed).permutation(ROW_WIDTH).astype(np.int16)
    permutation.flags.writeable = False
    return permutation


def _name_tuple(names: Iterable[str]) -> tuple[str, ...]:
    if isinstance(names, (str, bytes)):
        raise CarrierError("banks must be an iterable of distinct nonempty names")
    try:
        result = tuple(names)
    except TypeError as error:
        raise CarrierError(
            "banks must be an iterable of distinct nonempty names"
        ) from error
    if any(not isinstance(name, str) or not name.strip() for name in result):
        raise CarrierError("each bank name must be a nonempty string")
    if len(set(result)) != len(result):
        raise CarrierError("bank names must be unique")
    return result


def _fingerprint(permutation: np.ndarray) -> str:
    # Explicit little-endian 16-bit serialization makes the digest byte-order stable.
    return hashlib.sha256(permutation.astype("<u2", copy=False).tobytes()).hexdigest()


@dataclass(frozen=True)
class HadamardCarrier:
    """A versioned ordered bank layout; bank index is its deterministic seed.

    The empty bank tuple is permitted and denotes the empty, silent carrier.
    Reordering or changing the names changes the carrier identity. Each identity
    embeds a digest of the actual per-bank permutation table as well as its seed.
    """

    banks: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "banks", _name_tuple(self.banks))

    @classmethod
    def from_banks(cls, banks: Iterable[str]) -> HadamardCarrier:
        return cls(_name_tuple(banks))

    @cached_property
    def identity(self) -> str:
        description = {
            "version": CARRIER_VERSION,
            "construction": "Sylvester-Hadamard count carrier",
            "row_width": ROW_WIDTH,
            "banks": [
                {
                    "name": name,
                    "seed": seed,
                    "permutation_sha256": _fingerprint(_permutation(seed)),
                }
                for seed, name in enumerate(self.banks)
            ],
        }
        encoded = json.dumps(description, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
        return (
            f"hadamard-counts-v{CARRIER_VERSION}:{hashlib.sha256(encoded).hexdigest()}"
        )

    def encode(self, counts: np.ndarray) -> np.ndarray:
        """Map nonnegative integer counts (banks,512) to exact int32 bank vectors.

        Each bank occupies its own 512-dimensional slice. Input is never cast
        from floats or booleans. Intermediate arithmetic uses int64; a per-bank
        count total above int64 capacity or any output coordinate outside int32
        is refused rather than wrapped.
        """
        table = _checked_counts(counts, len(self.banks))
        vectors = np.zeros((len(self.banks), ROW_WIDTH), dtype=np.int32)
        for seed in range(len(self.banks)):
            row_counts = table[seed]
            total = sum(int(value) for value in row_counts)
            arithmetic_dtype = np.int64 if total <= _INT64.max else object
            hadamard_counts = np.zeros(ROW_WIDTH, dtype=arithmetic_dtype)
            hadamard_counts[_permutation(seed)] = row_counts.astype(
                arithmetic_dtype, copy=False
            )
            encoded = _fwht(hadamard_counts)
            if (
                int(encoded.min(initial=0)) < _INT32.min
                or int(encoded.max(initial=0)) > _INT32.max
            ):
                raise CarrierOverflow(f"bank {self.banks[seed]!r} vector exceeds int32")
            vectors[seed] = encoded.astype(np.int32)
        vectors.flags.writeable = False
        return vectors

    def decode(self, vectors: np.ndarray) -> np.ndarray:
        """Recover exact nonnegative row counts from int32 vectors or refuse them.

        Every inverse Hadamard coefficient must be an integer count >=0. Since
        H is self-inverse up to 512, these checks reconstruct the input exactly.
        """
        encoded = _checked_vectors(vectors, len(self.banks))
        counts = np.zeros((len(self.banks), ROW_WIDTH), dtype=np.int64)
        for seed in range(len(self.banks)):
            projections = _fwht(encoded[seed].astype(np.int64, copy=False))
            remainder = projections % ROW_WIDTH
            if remainder.any():
                raise CarrierError(
                    f"bank {self.banks[seed]!r} vector is not an integral Hadamard bundle"
                )
            by_hadamard_row = projections // ROW_WIDTH
            recovered = by_hadamard_row[_permutation(seed)]
            if (recovered < 0).any():
                raise CarrierError(
                    f"bank {self.banks[seed]!r} decodes to a negative row count"
                )
            if int(recovered.max(initial=0)) > _INT32.max:
                raise CarrierOverflow(
                    f"bank {self.banks[seed]!r} row count exceeds int32 encoding"
                )
            counts[seed] = recovered
        counts.flags.writeable = False
        return counts


def _checked_counts(counts: np.ndarray, banks: int) -> np.ndarray:
    table = np.asarray(counts)
    if table.shape != (banks, ROW_WIDTH):
        raise CarrierError(
            f"count table shape must be {(banks, ROW_WIDTH)}, got {table.shape}"
        )
    if table.dtype.kind not in "iuO":
        raise CarrierError(
            "count table must have an integer dtype; booleans and floats are refused"
        )
    if table.dtype.kind == "O":
        for value in table.flat:
            if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
                raise CarrierError(
                    "object count tables may contain only non-boolean integers"
                )
            if int(value) < 0:
                raise CarrierError("row counts must be nonnegative")
    elif table.size and table.dtype.kind == "i" and (table < 0).any():
        raise CarrierError("row counts must be nonnegative")
    return table


def _checked_vectors(vectors: np.ndarray, banks: int) -> np.ndarray:
    value = np.asarray(vectors)
    if value.shape != (banks, ROW_WIDTH):
        raise CarrierError(
            f"vector shape must be {(banks, ROW_WIDTH)}, got {value.shape}"
        )
    if value.dtype != np.dtype(np.int32):
        raise CarrierError(f"vectors must have dtype int32, got {value.dtype}")
    return value
