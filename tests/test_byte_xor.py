import sys

import numpy as np
import pytest

from knee.encoding.byte_xor import (
    BYTE_XOR_ROW_SHUFFLE,
    RAW,
    byte_xor_row_shuffle,
    decode_array,
    encode_array,
    inverse_byte_xor_row_shuffle,
)


@pytest.mark.parametrize(
    "array",
    [
        np.asarray(0, dtype=np.int16),
        np.asarray(-0.0, dtype=np.float64),
        np.asarray([], dtype=np.uint32),
        np.arange(15, dtype=np.uint8).reshape(3, 5),
        np.arange(60, dtype=np.int32).reshape(5, 12)[:, ::3],
        np.arange(20, dtype=np.float64).reshape(4, 5)[::-1, ::-2],
        np.asarray([True, False, True, True], dtype=np.bool_),
        np.asarray([1, -2, 3], dtype="<i4"),
        np.asarray([1, -2, 3], dtype=">i4"),
        np.asarray([1 + 2j, -3 + 0j], dtype="<c16"),
    ],
)
def test_row_transform_codec_restores_exact_c_bytes(array):
    array = np.asarray(array)
    raw = np.ascontiguousarray(array).tobytes(order="C")
    transformed, stride = byte_xor_row_shuffle(array)
    assert len(transformed) == len(raw)
    assert (
        inverse_byte_xor_row_shuffle(transformed, array.dtype, array.shape, stride)
        == raw
    )
    encoded = encode_array(array)
    decoded = decode_array(
        encoded.payload,
        encoded.codec,
        array.dtype,
        array.shape,
        encoded.raw_length,
        encoded.predictor_stride,
    )
    assert decoded.dtype.str == array.dtype.str
    assert decoded.shape == array.shape
    assert decoded.tobytes(order="C") == raw
    assert encoded.predictor_stride == stride


def test_float_nan_payloads_and_signed_zero_restore_exact_bits():
    bits = np.asarray(
        [0x7FF8000000000001, 0x7FF8000000001234, 0x8000000000000000, 0],
        dtype=np.uint64,
    )
    values = bits.view(np.float64)
    encoded = encode_array(values)
    decoded = decode_array(
        encoded.payload,
        encoded.codec,
        values.dtype,
        values.shape,
        encoded.raw_length,
        encoded.predictor_stride,
    )
    assert decoded.view(np.uint64).tobytes() == bits.tobytes()


def test_compressed_stream_rejects_truncation_trailing_data_and_wrong_length():
    array = np.tile(np.arange(256, dtype=np.uint64), 256).reshape(256, 256)
    encoded = encode_array(array)
    assert encoded.codec == BYTE_XOR_ROW_SHUFFLE
    with pytest.raises(
        ValueError, match="compressed_stream_invalid|compressed_payload_malformed"
    ):
        decode_array(
            encoded.payload[:-1],
            encoded.codec,
            array.dtype,
            array.shape,
            encoded.raw_length,
            encoded.predictor_stride,
        )
    with pytest.raises(ValueError, match="compressed_stream_invalid"):
        decode_array(
            encoded.payload + b"trailing",
            encoded.codec,
            array.dtype,
            array.shape,
            encoded.raw_length,
            encoded.predictor_stride,
        )
    with pytest.raises(ValueError, match="raw_length_mismatch"):
        decode_array(
            encoded.payload,
            encoded.codec,
            array.dtype,
            array.shape,
            encoded.raw_length + 1,
            encoded.predictor_stride,
        )


def test_raw_fallback_empty_payload_and_unknown_codec_are_named():
    noisy = np.random.default_rng(121).integers(0, 256, 2048, dtype=np.uint8)
    encoded = encode_array(noisy)
    assert encoded.codec == RAW
    assert encoded.payload == noisy.tobytes()
    empty = encode_array(np.empty((0, 3), dtype=np.float32))
    assert empty.codec == RAW and empty.payload == b"" and empty.raw_length == 0
    assert empty.predictor_stride == 3
    with pytest.raises(ValueError, match="codec_unknown"):
        decode_array(b"", "future_codec", noisy.dtype, noisy.shape, noisy.nbytes)


def test_decode_rejects_numpy_impossible_dimension_even_when_array_is_empty():
    with pytest.raises(ValueError, match="shape_dimension_exceeds_numpy_limit"):
        decode_array(b"", RAW, np.dtype("u1"), (sys.maxsize + 1, 0), 0)


@pytest.mark.parametrize("shape", [(0,) * 65, (0, sys.maxsize, 2)])
def test_empty_shape_still_requires_representable_rank_and_strides(shape):
    with pytest.raises(ValueError, match="byte_xor_shape"):
        decode_array(b"", RAW, np.dtype("u1"), shape, 0)


def test_inverse_rejects_wrong_buffer_stride_and_unsupported_object_arrays():
    with pytest.raises(ValueError, match="payload_length_mismatch"):
        inverse_byte_xor_row_shuffle(b"\x00", np.dtype("<i4"), (2,), 1)
    with pytest.raises(ValueError, match="unsupported_byte_xor_array"):
        byte_xor_row_shuffle(np.asarray([object()], dtype=object))
    with pytest.raises(ValueError, match="unsupported_byte_xor_dtype"):
        decode_array(b"", RAW, np.dtype(object), (0,), 0)
    a = np.arange(12, dtype=np.int32).reshape(3, 4)
    transformed, stride = byte_xor_row_shuffle(a)
    with pytest.raises(ValueError, match="stride_mismatch"):
        inverse_byte_xor_row_shuffle(transformed, a.dtype, a.shape, stride + 1)


def _reference_row_transform(array):
    """Small deliberately scalar implementation used as an independent oracle."""
    raw = np.ascontiguousarray(array).tobytes(order="C")
    itemsize = array.dtype.itemsize
    stride = max(1, int(np.prod(array.shape[1:]))) if array.ndim > 1 else 1
    nitems = array.size
    deltas = bytearray(len(raw))
    for item in range(nitems):
        row, column = divmod(item, stride)
        for byte in range(itemsize):
            source_offset = item * itemsize + byte
            if row == 0:
                deltas[source_offset] = raw[source_offset]
            else:
                previous_offset = ((row - 1) * stride + column) * itemsize + byte
                deltas[source_offset] = raw[source_offset] ^ raw[previous_offset]
    shuffled = bytes(
        deltas[index * itemsize + byte]
        for byte in range(itemsize)
        for index in range(nitems)
    )
    return shuffled, stride


@pytest.mark.parametrize(
    "array",
    [
        np.arange(12, dtype=np.uint32).reshape(3, 4),
        np.arange(24, dtype=np.float64).reshape(2, 3, 4)[:, ::2, ::-1],
        np.asarray(1234, dtype=">i4"),
        np.arange(9, dtype=np.uint8),
        np.empty((2, 0, 3), dtype="<f8"),
        np.array([0x7FF8000000000123, 0x8000000000000000], dtype=np.uint64)
        .view("<f8")
        .reshape(1, 2),
    ],
)
def test_row_stride_transform_matches_frozen_reference(array):
    array = np.asarray(array)
    expected, stride = _reference_row_transform(array)
    transformed, actual_stride = byte_xor_row_shuffle(array)
    assert actual_stride == stride
    assert transformed == expected
    raw = np.ascontiguousarray(array).tobytes(order="C")
    assert (
        inverse_byte_xor_row_shuffle(transformed, array.dtype, array.shape, stride)
        == raw
    )
