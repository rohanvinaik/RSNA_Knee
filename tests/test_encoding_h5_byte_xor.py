"""Exact round trips and corruption checks for opt-in schema-v4 payloads."""

import json
import sys
import zlib

import h5py
import numpy as np
import pytest

from knee.encoding.byte_xor import decode_array, encode_array
from knee.encoding.h5_store import (
    MalformedH5Error,
    open_h5,
    write_h5_byte_xor,
    write_h5_compact,
)
from knee.encoding.product import (
    DigestMismatchError,
    ProductMalformedError,
    open_product,
)
from knee.receipt import digest


def _same(left, right):
    assert left.dtype.str == right.dtype.str
    assert left.shape == right.shape
    assert left.tobytes(order="C") == right.tobytes(order="C")


def _arrays():
    f64 = np.array([0x7FF8000000000123, 0x8000000000000000, 1], np.uint64).view("<f8")
    be = np.array([0x7FF8000000000123, 0xFFF0000000000000], dtype=">u8").view(">f8")
    strided = np.arange(48, dtype=np.int32).reshape(6, 8)[::2, 1::2]
    return {
        "f64_payload": f64,
        "be_f64": be,
        "strided": strided,
        "bool": np.array([True, False, True]),
        "scalar": np.array(-0.0, dtype=">f4"),
        "empty": np.empty((2, 0, 3), dtype="<i8"),
        "repeat": f64.copy(),
        "random": np.random.default_rng(713).integers(
            0, 256, size=16384, dtype=np.uint8
        ),
    }


def _index(path):
    with h5py.File(path, "r") as file:
        return json.loads(bytes(file["array_index_json"][()].tobytes()).decode())


def _rewrite_index(path, mutation):
    table = _index(path)
    mutation(table)
    with h5py.File(path, "r+") as file:
        del file["array_index_json"]
        ds = file.create_dataset(
            "array_index_json",
            data=np.frombuffer(json.dumps(table).encode(), dtype=np.uint8),
            compression="gzip",
            compression_opts=4,
            shuffle=True,
        )
        ds.attrs["encoding"] = "gzip"


def _with_lzma2_dictionary_property(payload, property_byte):
    """Retain a genuine XZ stream while changing its LZMA2 dictionary header."""
    result = bytearray(payload)
    assert result[:6] == b"\xfd7zXZ\x00"
    block_start = 12
    block_header_length = (result[block_start] + 1) * 4
    crc_start = block_start + block_header_length - 4
    assert result[block_start + 1] == 0  # one-filter block flags
    assert result[block_start + 2 : block_start + 5] == b"\x21\x01\x16"
    result[block_start + 4] = property_byte
    result[crc_start : crc_start + 4] = zlib.crc32(
        result[block_start:crc_start]
    ).to_bytes(4, "little")
    return bytes(result)


def test_v4_exact_payloads_manifest_order_and_public_product(tmp_path):
    arrays = _arrays()
    manifest = {
        "purpose": "byte-preserving storage",
        "encoded_arrays": {
            key: {
                "digest": digest(value),
                "dtype": value.dtype.str,
                "shape": list(value.shape),
            }
            for key, value in arrays.items()
        },
    }
    path = tmp_path / "v4.h5"
    write_h5_byte_xor(path, manifest, arrays)
    with h5py.File(path, "r") as file:
        assert file.attrs["schema_version"] == 4
        assert "arrays" not in file and "arenas" not in file
        assert file["byte_payload"].dtype == np.dtype(np.uint8)
        assert file["byte_payload"].compression is None
    with open_product(path) as product:
        assert product.manifest == manifest
        assert list(product.arrays) == list(arrays)
        for key, source in arrays.items():
            _same(product.arrays[key], source)
        assert not product.arrays["f64_payload"].flags.writeable


def test_v4_exact_duplicate_alias_and_lazy_payload_spans(tmp_path, monkeypatch):
    arrays = {
        "a": np.arange(512, dtype=np.int32),
        "a-copy": np.arange(512, dtype=np.int32),
        "b": np.arange(64, dtype=np.uint8),
    }
    path = tmp_path / "lazy.h5"
    write_h5_byte_xor(path, {}, arrays)
    entries = _index(path)["arrays"]
    assert entries[1]["alias_of"] == 0
    assert (entries[1]["offset"], entries[1]["length"]) == (
        entries[0]["offset"],
        entries[0]["length"],
    )
    calls = []
    original = h5py.Dataset.__getitem__

    def spy(self, key, *args):
        if self.name == "/byte_payload" and isinstance(key, slice):
            calls.append((key.start, key.stop))
        return original(self, key, *args)

    monkeypatch.setattr(h5py.Dataset, "__getitem__", spy)
    with open_h5(path) as reader:
        assert calls == []
        assert list(reader.arrays) == list(arrays)
        assert calls == []
        _same(reader.arrays["b"], arrays["b"])
        assert len(calls) == 1
        _same(reader.arrays["a-copy"], arrays["a-copy"])
        assert len(calls) == 2


@pytest.mark.parametrize("schema", [999, 4.0, True])
def test_unknown_or_malformed_schema_is_rejected(tmp_path, schema):
    path = tmp_path / "bad-version.h5"
    write_h5_byte_xor(path, {}, {"a": np.arange(4)})
    with h5py.File(path, "r+") as file:
        file.attrs["schema_version"] = schema
    with (
        pytest.raises(MalformedH5Error, match="unsupported H5 schema version"),
        open_h5(path),
    ):
        pass


@pytest.mark.parametrize(
    "mutate",
    [
        lambda table: table.update(extra=True),
        lambda table: table.__setitem__("format", "wrong"),
        lambda table: table["arrays"][0].__setitem__("offset", True),
        lambda table: table["arrays"][0].__setitem__("codec", "invented"),
        lambda table: table["arrays"][0].__setitem__("raw_length", -1),
        lambda table: table["arrays"][0].__setitem__("shape", [True]),
        lambda table: table["arrays"][0].__setitem__("predictor_stride", True),
        lambda table: table["arrays"][0].__setitem__("predictor_stride", 2),
        lambda table: table["arrays"][1].__setitem__("alias_of", 1),
    ],
)
def test_malformed_v4_index_is_named(tmp_path, mutate):
    path = tmp_path / "malformed-index.h5"
    write_h5_byte_xor(
        path, {}, {"a": np.arange(4, dtype=np.int32), "b": np.arange(3, dtype=np.uint8)}
    )
    _rewrite_index(path, mutate)
    with pytest.raises(MalformedH5Error), open_h5(path):
        pass


def test_corrupt_xz_span_is_named_at_lazy_read(tmp_path):
    path = tmp_path / "corrupt.h5"
    array = np.zeros(4096, dtype=np.float64)
    manifest = {
        "encoded_arrays": {
            "a": {
                "digest": digest(array),
                "dtype": array.dtype.str,
                "shape": list(array.shape),
            }
        }
    }
    write_h5_byte_xor(path, manifest, {"a": array})
    with h5py.File(path, "r+") as file:
        index = _index(path)
        entry = index["arrays"][0]
        start = entry["offset"]
        file["byte_payload"][start] ^= np.uint8(0xFF)
    with open_h5(path) as reader, pytest.raises(MalformedH5Error):
        reader.arrays["a"]
    with (
        open_product(path) as product,
        pytest.raises(ProductMalformedError, match="array_storage_unreadable"),
    ):
        product.arrays["a"]


def test_corrupt_raw_payload_is_named_by_public_product_digest(tmp_path):
    array = np.random.default_rng(121).integers(0, 256, 4096, dtype=np.uint8)
    manifest = {
        "encoded_arrays": {
            "a": {
                "digest": digest(array),
                "dtype": array.dtype.str,
                "shape": list(array.shape),
            }
        }
    }
    path = tmp_path / "corrupt-raw.h5"
    write_h5_byte_xor(path, manifest, {"a": array})
    entry = _index(path)["arrays"][0]
    assert entry["codec"] == "raw"
    with h5py.File(path, "r+") as file:
        file["byte_payload"][entry["offset"]] ^= np.uint8(1)
    with (
        open_product(path) as product,
        pytest.raises(DigestMismatchError, match="digest_mismatch"),
    ):
        product.arrays["a"]


def test_oversized_xz_dictionary_is_refused_before_large_allocation(tmp_path):
    path = tmp_path / "oversized-dictionary.h5"
    write_h5_byte_xor(path, {}, {"a": np.zeros((32, 32), dtype=np.float64)})
    index = _index(path)
    entry = index["arrays"][0]
    assert entry["codec"] == "byte_xor_row_shuffle_xz"
    with h5py.File(path, "r+") as file:
        start = entry["offset"]
        stop = start + entry["length"]
        payload = bytes(file["byte_payload"][start:stop].tobytes())
        patched = _with_lzma2_dictionary_property(payload, 39)
        assert len(patched) == len(payload)
        file["byte_payload"][start:stop] = np.frombuffer(patched, dtype=np.uint8)
    with (
        open_h5(path) as reader,
        pytest.raises(MalformedH5Error, match="byte_xor_decoder_memory_limit_exceeded"),
    ):
        reader.arrays["a"]


def test_standard_max_preset_dictionary_fits_decoder_budget():
    array = np.zeros((32, 32), dtype=np.float64)
    encoded = encode_array(array)
    assert encoded.codec == "byte_xor_row_shuffle_xz"
    payload = _with_lzma2_dictionary_property(encoded.payload, 30)
    decoded = decode_array(
        payload,
        encoded.codec,
        array.dtype,
        array.shape,
        encoded.raw_length,
        encoded.predictor_stride,
    )
    _same(decoded, array)


def test_v4_index_rejects_numpy_impossible_dimension_with_zero_bytes(tmp_path):
    path = tmp_path / "impossible-empty-shape.h5"
    write_h5_byte_xor(path, {}, {"a": np.empty((0,), dtype=np.uint8)})

    def impossible_shape(table):
        entry = table["arrays"][0]
        entry.update(
            shape=[sys.maxsize + 1, 0],
            codec="raw",
            offset=0,
            length=0,
            raw_length=0,
            alias_of=None,
        )
        entry.pop("predictor_stride", None)

    _rewrite_index(path, impossible_shape)
    with (
        pytest.raises(MalformedH5Error, match="shape dimension.*exceeds NumPy limits"),
        open_h5(path),
    ):
        pass


def test_write_failure_keeps_previous_file_and_removes_part(tmp_path, monkeypatch):
    path = tmp_path / "atomic.h5"
    write_h5_byte_xor(path, {"v": 1}, {"old": np.arange(3)})
    previous = path.read_bytes()
    original = h5py.Dataset.__setitem__
    calls = {"n": 0}

    def fail_second_write(dataset, key, value):
        if dataset.name == "/byte_payload":
            calls["n"] += 1
            if calls["n"] == 2:
                raise OSError("simulated storage failure")
        return original(dataset, key, value)

    monkeypatch.setattr(h5py.Dataset, "__setitem__", fail_second_write)
    with pytest.raises(OSError, match="simulated storage failure"):
        write_h5_byte_xor(path, {"v": 2}, {"a": np.zeros(2048), "b": np.ones(2048)})
    assert path.read_bytes() == previous
    assert [item.name for item in tmp_path.iterdir()] == ["atomic.h5"]


@pytest.mark.parametrize("writer", [write_h5_byte_xor, write_h5_compact])
@pytest.mark.parametrize("shape", [[0] * 65, [0, sys.maxsize, 2]])
def test_index_rejects_unrepresentable_empty_shape_before_lazy_read(
    tmp_path, writer, shape
):
    path = tmp_path / "unrepresentable-shape.h5"
    writer(path, {}, {"a": np.empty((0,), dtype=np.uint8)})
    _rewrite_index(path, lambda table: table["arrays"][0].__setitem__("shape", shape))
    with pytest.raises(MalformedH5Error, match="shape"), open_h5(path):
        pass
