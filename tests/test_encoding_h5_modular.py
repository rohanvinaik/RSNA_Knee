"""Exactness and resource-refusal tests for opt-in H5 schema v5."""

import json
import sys
import zlib

import h5py
import numpy as np
import pytest

from knee.encoding.byte_xor import (
    BYTE_MODULAR_ROW_SHUFFLE,
    RAW,
    XZ_DECODE_MEMORY_LIMIT_BYTES,
    decode_array,
    encode_array_hybrid,
)
from knee.encoding.h5_store import (
    MalformedH5Error,
    open_h5,
    write_h5_modular,
)
from knee.encoding.product import ProductMalformedError, open_product
from knee.receipt import digest


def _same(left, right):
    assert left.dtype.str == right.dtype.str
    assert left.shape == right.shape
    assert left.tobytes(order="C") == right.tobytes(order="C")


def _arrays():
    f64 = np.array([0x7FF8000000000123, 0x8000000000000000, 1], dtype=np.uint64).view(
        "<f8"
    )
    big = np.array([0x7FF8000000000123, 0xFFF0000000000000], dtype=">u8").view(">f8")
    return {
        "f64_nan_and_zero": f64,
        "big_endian": big,
        "strided": np.arange(96, dtype=np.int32).reshape(8, 12)[::2, 1::3],
        "float16": np.arange(64, dtype=np.float16).reshape(8, 8),
        "bool": np.array([False, True, True], dtype=np.bool_),
        "scalar": np.array(-0.0, dtype=">f4"),
        "empty": np.empty((3, 0, 2), dtype="<i8"),
        "repeated": f64.copy(),
        "random": np.random.default_rng(804).integers(
            0, 256, size=8192, dtype=np.uint8
        ),
    }


def _manifest(arrays):
    return {
        "version": 1,
        "encoded_arrays": {
            key: {
                "digest": digest(value),
                "dtype": value.dtype.str,
                "shape": list(value.shape),
            }
            for key, value in arrays.items()
        },
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
    result = bytearray(payload)
    assert result[:6] == b"\xfd7zXZ\x00"
    block_start = 12
    block_header_length = (result[block_start] + 1) * 4
    crc_start = block_start + block_header_length - 4
    assert result[block_start + 1] == 0
    assert result[block_start + 2 : block_start + 4] == b"\x21\x01"
    result[block_start + 4] = property_byte
    result[crc_start : crc_start + 4] = zlib.crc32(
        result[block_start:crc_start]
    ).to_bytes(4, "little")
    return bytes(result)


def test_modular_codec_roundtrips_all_supported_raw_word_shapes():
    arrays = _arrays()
    arrays.update(
        {
            "float32_grid": np.linspace(-1, 1, 4096, dtype=np.float32).reshape(64, 64),
            "int16_big": np.arange(4096, dtype=">i2").reshape(64, 64),
            "uint64": np.arange(2048, dtype=np.uint64).reshape(32, 64),
        }
    )
    modular = 0
    for source in arrays.values():
        encoded = encode_array_hybrid(source)
        restored = decode_array(
            encoded.payload,
            encoded.codec,
            source.dtype,
            source.shape,
            encoded.raw_length,
            encoded.predictor_stride,
        )
        _same(restored, source)
        modular += encoded.codec == BYTE_MODULAR_ROW_SHUFFLE
    assert modular >= 1


def test_masked_ndarray_uses_existing_underlying_numeric_byte_contract(tmp_path):
    source = np.ma.array(
        np.arange(8192, dtype=np.float64).reshape(128, 64),
        mask=True,
        fill_value=0.0,
    )
    expected = np.ascontiguousarray(source)
    encoded = encode_array_hybrid(source)
    assert encoded.codec == BYTE_MODULAR_ROW_SHUFFLE
    decoded = decode_array(
        encoded.payload,
        encoded.codec,
        source.dtype,
        source.shape,
        encoded.raw_length,
        encoded.predictor_stride,
    )
    _same(decoded, expected)
    arrays = {"masked": source}
    path = tmp_path / "masked.h5"
    # The manifest describes the same underlying numeric bytes as legacy writers.
    write_h5_modular(path, _manifest({"masked": expected}), arrays)
    with open_product(path) as product:
        _same(product.arrays["masked"], expected)


def test_hybrid_uses_raw_fallback_when_compression_is_not_smaller():
    source = np.random.default_rng(95).integers(0, 256, size=4096, dtype=np.uint8)
    encoded = encode_array_hybrid(source)
    assert encoded.codec == RAW
    _same(
        decode_array(
            encoded.payload, encoded.codec, source.dtype, source.shape, source.nbytes
        ),
        source,
    )


def test_v5_public_product_preserves_every_name_order_manifest_and_payload(tmp_path):
    arrays = _arrays()
    manifest = _manifest(arrays)
    path = tmp_path / "v5.h5"
    write_h5_modular(path, manifest, arrays)
    with h5py.File(path, "r") as file:
        assert file.attrs["schema_version"] == 5
        table = json.loads(bytes(file["array_index_json"][()].tobytes()).decode())
        assert table["format"] == "knee-h5-byte-payload/modular-v5"
        assert table["arrays"][7]["alias_of"] == 0
    with open_product(path) as product:
        assert product.manifest == manifest
        assert list(product.arrays) == list(arrays)
        for key, source in arrays.items():
            _same(product.arrays[key], source)
            assert (
                digest(product.arrays[key]) == manifest["encoded_arrays"][key]["digest"]
            )


def test_v5_reader_is_lazy_and_alias_reads_one_span(tmp_path, monkeypatch):
    arrays = {
        "a": np.arange(8192, dtype=np.float64).reshape(128, 64),
        "a-copy": np.arange(8192, dtype=np.float64).reshape(128, 64),
        "b": np.zeros((64, 64), dtype=np.float32),
    }
    path = tmp_path / "lazy.h5"
    write_h5_modular(path, _manifest(arrays), arrays)
    assert _index(path)["arrays"][1]["alias_of"] == 0
    calls = []
    original = h5py.Dataset.__getitem__

    def spy(dataset, key, *args):
        if dataset.name == "/byte_payload" and isinstance(key, slice):
            calls.append((key.start, key.stop))
        return original(dataset, key, *args)

    monkeypatch.setattr(h5py.Dataset, "__getitem__", spy)
    with open_h5(path) as reader:
        assert list(reader.arrays) == list(arrays)
        assert calls == []
        _same(reader.arrays["a-copy"], arrays["a-copy"])
        assert len(calls) == 1


@pytest.mark.parametrize("schema", [999, 4.0, True])
def test_v5_unknown_or_malformed_schema_is_named(tmp_path, schema):
    path = tmp_path / "bad-version.h5"
    write_h5_modular(path, {}, {"a": np.arange(4)})
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
        lambda table: table["arrays"][0].__setitem__("codec", "invented"),
        lambda table: table["arrays"][0].__setitem__("offset", True),
        lambda table: table["arrays"][0].__setitem__("predictor_stride", True),
        lambda table: table["arrays"][0].__setitem__("predictor_stride", 2),
    ],
)
def test_malformed_v5_index_is_named(tmp_path, mutate):
    path = tmp_path / "bad-index.h5"
    write_h5_modular(path, {}, {"a": np.arange(128, dtype=np.float64).reshape(16, 8)})
    _rewrite_index(path, mutate)
    with pytest.raises(MalformedH5Error), open_h5(path):
        pass


def test_v5_keeps_empty_arrays_as_named_zero_length_entries(tmp_path):
    arrays = {
        "empty-a": np.empty((0, 4), dtype=np.float32),
        "empty-b": np.empty((0, 4), dtype=np.float32),
    }
    path = tmp_path / "empty-aliases.h5"
    write_h5_modular(path, _manifest(arrays), arrays)
    entries = _index(path)["arrays"]
    assert [entry["key"] for entry in entries] == list(arrays)
    assert [entry["alias_of"] for entry in entries] == [None, None]
    with open_product(path) as product:
        for key, source in arrays.items():
            _same(product.arrays[key], source)


def test_v5_alias_must_match_its_exact_prior_entry(tmp_path):
    source = np.arange(1024, dtype=np.float32).reshape(32, 32)
    path = tmp_path / "bad-alias.h5"
    write_h5_modular(
        path,
        {},
        {"original": source, "copy": source.copy()},
    )

    def alter_alias(table):
        assert table["arrays"][1]["alias_of"] == 0
        table["arrays"][1]["dtype"] = ">f4"

    _rewrite_index(path, alter_alias)
    with pytest.raises(MalformedH5Error, match="alias entry"), open_h5(path):
        pass


def test_v5_modular_xz_dictionary_is_bounded_by_public_reader(tmp_path):
    source = np.linspace(0, 1, 4096, dtype=np.float32).reshape(64, 64)
    encoded = encode_array_hybrid(source)
    assert encoded.codec == BYTE_MODULAR_ROW_SHUFFLE
    arrays = {"a": source}
    path = tmp_path / "oversized-dictionary.h5"
    write_h5_modular(path, _manifest(arrays), arrays)
    entry = _index(path)["arrays"][0]
    assert entry["codec"] == BYTE_MODULAR_ROW_SHUFFLE
    with h5py.File(path, "r+") as file:
        start = entry["offset"]
        stop = start + entry["length"]
        payload = bytes(file["byte_payload"][start:stop].tobytes())
        patched = _with_lzma2_dictionary_property(payload, 39)
        file["byte_payload"][start:stop] = np.frombuffer(patched, dtype=np.uint8)
    with (
        pytest.raises(MalformedH5Error, match="byte_xor_decoder_memory_limit_exceeded"),
        open_h5(path) as reader,
    ):
        reader.arrays["a"]
    with (
        pytest.raises(ProductMalformedError, match="array_storage_unreadable"),
        open_product(path) as product,
    ):
        product.arrays["a"]


def test_v5_writer_failure_preserves_previous_destination(tmp_path, monkeypatch):
    path = tmp_path / "atomic.h5"
    write_h5_modular(path, {"generation": 1}, {"old": np.arange(4)})
    previous = path.read_bytes()
    original = h5py.Dataset.__setitem__
    calls = {"n": 0}

    def fail_second_payload_write(dataset, key, value):
        if dataset.name == "/byte_payload":
            calls["n"] += 1
            if calls["n"] == 1:
                raise OSError("injected v5 write failure")
        return original(dataset, key, value)

    monkeypatch.setattr(h5py.Dataset, "__setitem__", fail_second_payload_write)
    with pytest.raises(OSError, match="injected v5 write failure"):
        write_h5_modular(
            path,
            {"generation": 2},
            {
                "a": np.linspace(0, 1, 4096, dtype=np.float32).reshape(64, 64),
                "b": np.linspace(1, 0, 4096, dtype=np.float32).reshape(64, 64),
            },
        )
    assert path.read_bytes() == previous
    assert [item.name for item in tmp_path.iterdir()] == ["atomic.h5"]


def test_v5_index_rejects_numpy_impossible_empty_shape(tmp_path):
    path = tmp_path / "impossible-empty-shape.h5"
    write_h5_modular(path, {}, {"a": np.empty((0,), dtype=np.uint8)})

    def mutate(table):
        table["arrays"][0]["shape"] = [sys.maxsize + 1, 0]

    _rewrite_index(path, mutate)
    with (
        pytest.raises(MalformedH5Error, match="shape dimension.*exceeds NumPy limits"),
        open_h5(path),
    ):
        pass


def test_v5_index_cannot_expand_a_payload_beyond_declared_output(tmp_path):
    source = np.linspace(0, 1, 4096, dtype=np.float32).reshape(64, 64)
    arrays = {"a": source}
    path = tmp_path / "bounded-output.h5"
    write_h5_modular(path, _manifest(arrays), arrays)
    entry = _index(path)["arrays"][0]
    assert entry["codec"] == BYTE_MODULAR_ROW_SHUFFLE

    def shrink_declaration(table):
        table["arrays"][0]["shape"] = [1]
        table["arrays"][0]["raw_length"] = source.dtype.itemsize
        table["arrays"][0]["predictor_stride"] = 1

    _rewrite_index(path, shrink_declaration)
    with (
        open_h5(path) as reader,
        pytest.raises(MalformedH5Error, match="byte_xor_compressed_stream_invalid"),
    ):
        reader.arrays["a"]


def _lzma2_dictionary_bytes(payload):
    block_start = 12
    assert payload[block_start + 1] == 0
    assert payload[block_start + 2 : block_start + 4] == b"\x21\x01"
    property_byte = payload[block_start + 4]
    assert 0 <= property_byte < 40
    return (2 | (property_byte & 1)) << (property_byte // 2 + 11)


def test_v5_default_preset0_is_bounded_and_preset6_remains_readable(tmp_path):
    source = np.linspace(0, 1, 4096, dtype=np.float32).reshape(64, 64)
    arrays = {"a": source}
    manifest = _manifest(arrays)
    low_path = tmp_path / "preset0.h5"
    prior_path = tmp_path / "preset6.h5"
    write_h5_modular(low_path, manifest, arrays)
    write_h5_modular(prior_path, manifest, arrays, preset=6)

    low_entry = _index(low_path)["arrays"][0]
    prior_entry = _index(prior_path)["arrays"][0]
    assert low_entry["codec"] == BYTE_MODULAR_ROW_SHUFFLE
    assert prior_entry["codec"] == BYTE_MODULAR_ROW_SHUFFLE
    with h5py.File(low_path, "r") as file:
        low_payload = bytes(
            file["byte_payload"][
                low_entry["offset"] : low_entry["offset"] + low_entry["length"]
            ].tobytes()
        )
    with h5py.File(prior_path, "r") as file:
        prior_payload = bytes(
            file["byte_payload"][
                prior_entry["offset"] : prior_entry["offset"] + prior_entry["length"]
            ].tobytes()
        )
    low_dictionary = _lzma2_dictionary_bytes(low_payload)
    prior_dictionary = _lzma2_dictionary_bytes(prior_payload)
    assert low_dictionary <= XZ_DECODE_MEMORY_LIMIT_BYTES
    assert prior_dictionary <= XZ_DECODE_MEMORY_LIMIT_BYTES
    assert low_dictionary < prior_dictionary

    for path in (low_path, prior_path):
        with open_product(path) as product:
            _same(product.arrays["a"], source)
            assert (
                digest(product.arrays["a"]) == manifest["encoded_arrays"]["a"]["digest"]
            )
