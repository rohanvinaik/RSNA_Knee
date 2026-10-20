"""Exact reversible row-predicted byte transforms for HDF payloads."""

from __future__ import annotations

import lzma
import sys
from dataclasses import dataclass
from math import prod
from typing import Literal

import numpy as np

BYTE_XOR_SHUFFLE = "byte_xor_shuffle_xz"  # prior scalar-neighbor candidate format
BYTE_XOR_ROW_SHUFFLE = "byte_xor_row_shuffle_xz"
BYTE_MODULAR_ROW_SHUFFLE = "byte_modular_row_shuffle_xz"
RAW = "raw"
# All standard XZ presets 0-9 fit below this decoder working-memory ceiling.
# The payload output is separately bounded by the declared raw length.
XZ_DECODE_MEMORY_LIMIT_BYTES = 256 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class EncodedBytes:
    codec: Literal[
        "raw",
        "byte_xor_shuffle_xz",
        "byte_xor_row_shuffle_xz",
        "byte_modular_row_shuffle_xz",
    ]
    payload: bytes
    raw_length: int
    predictor_stride: int | None = None


def _row_stride(shape: tuple[int, ...]) -> int:
    """Number of items in a C-order row; scalar/1D/empty use stride one."""
    return max(1, prod(shape[1:])) if len(shape) > 1 else 1


def _validate_numpy_shape(shape: tuple[int, ...], itemsize: int) -> int:
    if not isinstance(shape, tuple) or any(
        not isinstance(n, int) or isinstance(n, bool) or n < 0 for n in shape
    ):
        raise ValueError("invalid_byte_xor_shape")
    limit = sys.maxsize
    if any(n > limit for n in shape):
        raise ValueError("byte_xor_shape_dimension_exceeds_numpy_limit")
    try:
        # Zero extents validate the installed NumPy rank limit without payload allocation.
        np.empty((0,) * len(shape), dtype=np.uint8)
    except ValueError as error:
        raise ValueError("byte_xor_shape_rank_exceeds_numpy_limit") from error
    nitems = prod(shape) if shape else 1
    addressed_items = prod(max(1, n) for n in shape)
    if nitems > (limit - 1) // itemsize or addressed_items > limit // itemsize:
        raise ValueError("byte_xor_shape_byte_size_exceeds_numpy_limit")
    return nitems


def byte_xor_shuffle(array: np.ndarray) -> bytes:
    """Legacy scalar-neighbor transform retained to read the first private v4."""
    if not isinstance(array, np.ndarray) or array.dtype.hasobject:
        raise ValueError("unsupported_byte_xor_array")
    itemsize = int(array.dtype.itemsize)
    if itemsize < 1:
        raise ValueError("invalid_byte_xor_itemsize")
    nitems = int(array.size)
    if nitems == 0:
        return b""
    values = np.ascontiguousarray(array).view(np.uint8).reshape(nitems, itemsize)
    delta = np.empty_like(values)
    delta[0] = values[0]
    if nitems > 1:
        np.bitwise_xor(values[1:], values[:-1], out=delta[1:])
    return delta.T.copy().tobytes(order="C")


def inverse_byte_xor_shuffle(
    payload: bytes, dtype: np.dtype, shape: tuple[int, ...]
) -> bytes:
    """Inverse of the legacy scalar-neighbor byte shuffle."""
    dtype = np.dtype(dtype)
    if dtype.hasobject or dtype.itemsize < 1:
        raise ValueError("unsupported_byte_xor_dtype")
    if not isinstance(payload, bytes):
        raise TypeError("byte_xor_payload_must_be_bytes")
    nitems = _validate_numpy_shape(shape, dtype.itemsize)
    expected = nitems * dtype.itemsize
    if len(payload) != expected:
        raise ValueError("byte_xor_payload_length_mismatch")
    if nitems == 0:
        return b""
    shuffled = np.frombuffer(payload, dtype=np.uint8).reshape(dtype.itemsize, nitems)
    delta = shuffled.T.copy()
    np.bitwise_xor.accumulate(delta, axis=0, out=delta)
    return delta.tobytes(order="C")


def byte_xor_row_shuffle(array: np.ndarray) -> tuple[bytes, int]:
    """Predict each C-order row from the preceding row at the same item position.

    The first row is unchanged. Elements within a row are not predictors for the
    next row; byte-plane shuffling follows the row-wise XOR operation.
    """
    if not isinstance(array, np.ndarray) or array.dtype.hasobject:
        raise ValueError("unsupported_byte_xor_array")
    itemsize = int(array.dtype.itemsize)
    if itemsize < 1:
        raise ValueError("invalid_byte_xor_itemsize")
    shape = array.shape
    stride = _row_stride(shape)
    nitems = int(array.size)
    if nitems == 0:
        return b"", stride
    values = np.ascontiguousarray(array).view(np.uint8).reshape(nitems, itemsize)
    rows = values.reshape(nitems // stride, stride, itemsize)
    delta = np.empty_like(rows)
    delta[0] = rows[0]
    if rows.shape[0] > 1:
        np.bitwise_xor(rows[1:], rows[:-1], out=delta[1:])
    return delta.reshape(nitems, itemsize).T.copy().tobytes(order="C"), stride


def inverse_byte_xor_row_shuffle(
    payload: bytes, dtype: np.dtype, shape: tuple[int, ...], predictor_stride: int
) -> bytes:
    """Restore C-order bytes from a row-predicted byte-plane payload."""
    dtype = np.dtype(dtype)
    if dtype.hasobject or dtype.itemsize < 1:
        raise ValueError("unsupported_byte_xor_dtype")
    if not isinstance(payload, bytes):
        raise TypeError("byte_xor_payload_must_be_bytes")
    nitems = _validate_numpy_shape(shape, dtype.itemsize)
    expected_stride = _row_stride(shape)
    if (
        not isinstance(predictor_stride, int)
        or isinstance(predictor_stride, bool)
        or predictor_stride != expected_stride
    ):
        raise ValueError("byte_xor_predictor_stride_mismatch")
    expected = nitems * dtype.itemsize
    if len(payload) != expected:
        raise ValueError("byte_xor_payload_length_mismatch")
    if nitems == 0:
        return b""
    rows_count = nitems // predictor_stride
    shuffled = np.frombuffer(payload, dtype=np.uint8).reshape(dtype.itemsize, nitems)
    delta = shuffled.T.copy().reshape(rows_count, predictor_stride, dtype.itemsize)
    np.bitwise_xor.accumulate(delta, axis=0, out=delta)
    return delta.reshape(nitems, dtype.itemsize).tobytes(order="C")


def _modular_word_dtype(itemsize: int) -> np.dtype:
    if itemsize not in (1, 2, 4, 8):
        raise ValueError("unsupported_modular_word_size")
    return np.dtype(f"<u{itemsize}")


def modular_row_shuffle(array: np.ndarray) -> tuple[bytes, int]:
    """Modulo-delta little-endian raw words between corresponding C-order rows."""
    if not isinstance(array, np.ndarray) or array.dtype.hasobject:
        raise ValueError("unsupported_modular_array")
    dtype = _modular_word_dtype(int(array.dtype.itemsize))
    stride = _row_stride(array.shape)
    if array.size == 0:
        return b"", stride
    values = np.frombuffer(np.ascontiguousarray(array).tobytes(order="C"), dtype=dtype)
    rows = values.reshape(array.size // stride, stride)
    delta = np.empty_like(rows)
    delta[0] = rows[0]
    if rows.shape[0] > 1:
        np.subtract(rows[1:], rows[:-1], out=delta[1:])
    planes = delta.view(np.uint8).reshape(array.size, array.dtype.itemsize)
    return planes.T.copy(order="C").tobytes(), stride


def inverse_modular_row_shuffle(
    payload: bytes, dtype: np.dtype, shape: tuple[int, ...], predictor_stride: int
) -> bytes:
    """Restore raw C bytes by unsigned cumulative sum modulo each word width."""
    dtype = np.dtype(dtype)
    word_dtype = _modular_word_dtype(int(dtype.itemsize))
    count = _validate_numpy_shape(shape, dtype.itemsize)
    expected_stride = _row_stride(shape)
    if (
        not isinstance(predictor_stride, int)
        or isinstance(predictor_stride, bool)
        or predictor_stride != expected_stride
    ):
        raise ValueError("modular_predictor_stride_mismatch")
    expected = count * dtype.itemsize
    if not isinstance(payload, bytes) or len(payload) != expected:
        raise ValueError("modular_payload_length_mismatch")
    if count == 0:
        return b""
    deltas_bytes = (
        np.frombuffer(payload, dtype=np.uint8).reshape(dtype.itemsize, count).T.copy()
    )
    deltas = (
        deltas_bytes.reshape(-1)
        .view(word_dtype)
        .reshape(count // predictor_stride, predictor_stride)
    )
    restored = np.add.accumulate(deltas, axis=0, dtype=word_dtype)
    return restored.tobytes(order="C")


def encode_array_hybrid(array: np.ndarray, *, preset: int = 6) -> EncodedBytes:
    """Choose the shortest lossless raw, row-XOR, or modular-row XZ payload."""
    current = encode_array(array, preset=preset)
    if array.size == 0:
        return current
    try:
        transformed, stride = modular_row_shuffle(array)
    except ValueError as error:
        if str(error) == "unsupported_modular_word_size":
            return current
        raise
    payload = lzma.compress(transformed, format=lzma.FORMAT_XZ, preset=preset)
    if len(payload) < len(current.payload):
        return EncodedBytes(
            BYTE_MODULAR_ROW_SHUFFLE, payload, current.raw_length, stride
        )
    return current


def encode_array(array: np.ndarray, *, preset: int = 6) -> EncodedBytes:
    """Encode one array with its explicit C-row stride; raw fallback stays exact."""
    if not isinstance(array, np.ndarray) or array.dtype.hasobject:
        raise ValueError("unsupported_byte_xor_array")
    raw = np.ascontiguousarray(array).tobytes(order="C")
    transformed, stride = byte_xor_row_shuffle(array)
    if not raw:
        return EncodedBytes(RAW, raw, 0, stride)
    compressed = lzma.compress(transformed, format=lzma.FORMAT_XZ, preset=preset)
    if len(compressed) >= len(raw):
        return EncodedBytes(RAW, raw, len(raw), stride)
    return EncodedBytes(BYTE_XOR_ROW_SHUFFLE, compressed, len(raw), stride)


def decode_array(
    payload: bytes,
    codec: str,
    dtype: np.dtype,
    shape: tuple[int, ...],
    raw_length: int,
    predictor_stride: int | None = None,
) -> np.ndarray:
    """Decode one payload; XZ streams must be complete and exactly sized."""
    dtype = np.dtype(dtype)
    if dtype.hasobject or dtype.itemsize < 1:
        raise ValueError("unsupported_byte_xor_dtype")
    nitems = _validate_numpy_shape(shape, dtype.itemsize)
    expected = nitems * dtype.itemsize
    if (
        not isinstance(raw_length, int)
        or isinstance(raw_length, bool)
        or raw_length != expected
    ):
        raise ValueError("byte_xor_raw_length_mismatch")
    if codec == RAW:
        raw = payload
    elif codec in (BYTE_XOR_SHUFFLE, BYTE_XOR_ROW_SHUFFLE, BYTE_MODULAR_ROW_SHUFFLE):
        try:
            decoder = lzma.LZMADecompressor(
                format=lzma.FORMAT_XZ,
                memlimit=XZ_DECODE_MEMORY_LIMIT_BYTES,
            )
            transformed = decoder.decompress(payload, max_length=expected + 1)
        except lzma.LZMAError as error:
            if "memory usage limit exceeded" in str(error).casefold():
                raise ValueError("byte_xor_decoder_memory_limit_exceeded") from error
            raise ValueError("byte_xor_compressed_payload_malformed") from error
        except MemoryError as error:
            raise ValueError("byte_xor_decoder_memory_limit_exceeded") from error
        if not decoder.eof or decoder.unused_data:
            raise ValueError("byte_xor_compressed_stream_invalid")
        if len(transformed) != expected:
            raise ValueError("byte_xor_decoded_length_mismatch")
        if codec == BYTE_XOR_SHUFFLE:
            raw = inverse_byte_xor_shuffle(transformed, dtype, shape)
        elif codec == BYTE_XOR_ROW_SHUFFLE:
            if predictor_stride is None:
                raise ValueError("byte_xor_predictor_stride_required")
            raw = inverse_byte_xor_row_shuffle(
                transformed, dtype, shape, predictor_stride
            )
        else:
            if predictor_stride is None:
                raise ValueError("modular_predictor_stride_required")
            raw = inverse_modular_row_shuffle(
                transformed, dtype, shape, predictor_stride
            )
    else:
        raise ValueError("byte_xor_codec_unknown")
    if len(raw) != expected:
        raise ValueError("byte_xor_payload_length_mismatch")
    if codec in (BYTE_XOR_ROW_SHUFFLE, BYTE_MODULAR_ROW_SHUFFLE) and (
        predictor_stride != _row_stride(shape)
    ):
        raise ValueError("byte_xor_predictor_stride_mismatch")
    return np.frombuffer(raw, dtype=dtype).reshape(shape).copy()
