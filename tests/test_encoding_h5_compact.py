# path: tests/test_encoding_h5_compact.py
"""Authored expected behavior of the schema-v3 compact arena writer/reader."""

import json
import os
from typing import Any, cast

import numpy as np
import pytest

h5py = pytest.importorskip("h5py")

from knee.encoding import h5_store
from knee.encoding.h5_store import (
    MalformedH5Error,
    ManifestError,
    ReaderClosedError,
    UnsupportedArrayDtypeError,
    open_h5,
    write_h5,
    write_h5_compact,
)
from knee.encoding.product import (
    DigestMismatchError,
    DtypeMismatchError,
    ProductClosedError,
    open_product,
)
from knee.receipt import digest

MANIFEST = {
    "layout_id": "L-1",
    "counts": {"places": 12345678901234567890, "zero": 0},
    "source": {"artifact": "x.npz.xz", "ünï": "ç"},
    "flag": None,
    "ratio": 0.1,
}


def sample():
    f32 = np.array(
        [0x7FC00001, 0x7F800001, 0xFFC12345, 0x7F800000, 0x80000000], np.uint32
    ).view(np.float32)
    f64 = np.array([0x7FF8000000000123, 0xFFF0000000000000, 1], np.uint64).view(
        np.float64
    )
    f16 = np.array([0x7E01, 0xFE55, 0x8000, 0x7C00], np.uint16).view(np.float16)
    be_c128 = np.array(
        [
            0x7FF8000000000123,
            0x8000000000000000,
            0xFFF0000000000000,
            0x7FF0000000000042,
        ],
        dtype=">u8",
    ).view(">c16")
    strided = np.arange(24, dtype=np.int32).reshape(4, 6)[:, ::2]
    assert not strided.flags.c_contiguous
    return {
        "b": np.array([True, False, True]),
        "i8": np.array([-128, 0, 127], np.int8),
        "i64": np.array([-(2**63), 2**63 - 1], np.int64),
        "u16": np.arange(6, dtype=np.uint16).reshape(2, 3),
        "f32_nan": f32,
        "f64_nan": f64,
        "c128": np.array([1 + 2j, complex(np.nan, -np.inf)], np.complex128),
        "scalar": np.array(7.5, np.float64),
        "scalar_b": np.array(True),
        "empty": np.zeros((0,), np.int32),
        "empty2": np.zeros((3, 0), np.float32),
        "be_i4": np.array([1, -2, 3], ">i4"),
        "be_i4_scalar": np.array(1234, ">i4"),
        "le_u2": np.array([1, 2], "<u2"),
        "be_f4": np.array([1.5, np.nan], ">f4"),
        "be_f4_scalar": np.array(-0.0, ">f4"),
        "be_f8": np.array([2.5, -0.0], ">f8"),
        "f16_nan_payload": f16,
        "be_c128_payload": be_c128,
        "be_c128_scalar": be_c128[:1].reshape(()),
        "strided": strided,
        "fortran": np.asfortranarray(np.arange(6, dtype=np.int16).reshape(2, 3)),
        "a/b with space": np.array([1, 2], np.int16),
        "zeta": np.array([1], np.int8),
        "alpha": np.array([2], np.int8),
    }


def same(left, right):
    assert left.dtype.str == right.dtype.str
    assert left.shape == right.shape
    assert left.tobytes() == right.tobytes()


def stored_index(path):
    with h5py.File(path, "r") as f:
        return json.loads(bytes(f["array_index_json"][()].tobytes()).decode("utf-8"))


def rewrite_index(path, mutate):
    table = stored_index(path)
    mutate(table)
    with h5py.File(path, "r+") as f:
        del f["array_index_json"]
        ds = f.create_dataset(
            "array_index_json",
            data=np.frombuffer(json.dumps(table).encode(), np.uint8),
            compression="gzip",
            compression_opts=4,
            shuffle=True,
        )
        ds.attrs["encoding"] = "gzip"


# ---------------------------------------------------------------- positive


def test_round_trip_is_exact_and_schema_v3_layout(tmp_path):
    arrays = sample()
    dest = tmp_path / "c.h5"
    assert write_h5_compact(dest, MANIFEST, arrays) == dest
    with h5py.File(dest, "r") as f:
        assert f.attrs["schema_version"] == 3
        assert "arrays" not in f and "array_keys_json" not in f
        assert f["manifest_json"].compression == "gzip"
        assert f["manifest_json"].attrs["encoding"] == "gzip"
        assert bytes(f["manifest_json"][()].tobytes()) == h5_store._serialize_manifest(
            MANIFEST
        )
        assert f["array_index_json"].compression == "gzip"
        assert f["array_index_json"].attrs["encoding"] == "gzip"
        for name in f["arenas"]:
            assert f["arenas"][name].compression == "gzip"
            assert f["arenas"][name].shuffle is True
    index = stored_index(dest)
    nonempty_dtypes = {a.dtype.str for a in arrays.values() if a.size}
    assert {m["dtype"] for m in index["arenas"]} == nonempty_dtypes
    assert len(index["arenas"]) == len(nonempty_dtypes)  # one arena per bucket here
    with open_h5(dest) as r:
        assert r.manifest == MANIFEST
        assert type(r.manifest["counts"]["places"]) is int
        assert list(r.arrays) == list(arrays)
        assert len(r.arrays) == len(arrays)
        for key, source in arrays.items():
            got = r.arrays[key]
            same(got, source)
            assert got.flags.c_contiguous and got.flags.writeable
    assert [p.name for p in tmp_path.iterdir()] == ["c.h5"]


def test_empty_store_and_all_empty_arrays(tmp_path):
    write_h5_compact(tmp_path / "e.h5", {}, {})
    write_h5_compact(
        tmp_path / "z.h5", {"k": 1}, {"z": np.zeros((0, 2), ">f8"), "y": np.zeros(0)}
    )
    with open_h5(tmp_path / "e.h5") as r:
        assert r.manifest == {} and len(r.arrays) == 0
    with open_h5(tmp_path / "z.h5") as r:
        assert list(r.arrays) == ["z", "y"]
        same(r.arrays["z"], np.zeros((0, 2), ">f8"))
        same(r.arrays["y"], np.zeros(0))
    assert stored_index(tmp_path / "z.h5")["arenas"] == []


def test_exact_duplicates_share_span_but_keep_all_names_in_order(tmp_path):
    base = np.array([1, -2, 3], dtype=">i4")
    arrays = {
        "orig/key": base,
        "alias with spaces": base.copy(),
        "different": np.array([2, -1, 4], dtype=">i4"),
        "emptyA": np.zeros(0, "<i4"),
        "emptyB": np.zeros(0, "<i4"),
    }
    dest = tmp_path / "a.h5"
    write_h5_compact(dest, {}, arrays)
    index = stored_index(dest)
    e = index["arrays"]
    assert [x["key"] for x in e] == list(arrays)
    assert e[1]["alias_of"] == 0 and e[0]["alias_of"] is None
    assert (e[1]["arena"], e[1]["offset"], e[1]["length"]) == (
        e[0]["arena"],
        e[0]["offset"],
        e[0]["length"],
    )
    assert e[2]["alias_of"] is None and e[2]["offset"] == 12
    assert index["arenas"][0]["bytes"] == 24
    assert e[3]["arena"] is None and e[3]["alias_of"] is None
    with open_h5(dest) as r:
        assert list(r.arrays) == list(arrays)
        for key, source in arrays.items():
            same(r.arrays[key], source)
        # aliases decode to independent arrays
        a, b = r.arrays["orig/key"], r.arrays["alias with spaces"]
        a[0] = 99
        assert b[0] == 1


def test_nan_payload_and_signed_zero_alias_only_on_exact_bytes(tmp_path):
    nan_a = np.array([0x7FF8000000000001], np.uint64).view(np.float64)
    nan_b = np.array([0x7FF8000000000002], np.uint64).view(np.float64)
    arrays = {
        "nan-a": nan_a,
        "nan-a-copy": nan_a.copy(),
        "nan-b": nan_b,
        "negzero": np.array([-0.0]),
        "negzero-copy": np.array([-0.0]),
        "poszero": np.array([0.0]),
    }
    dest = tmp_path / "f.h5"
    write_h5_compact(dest, {}, arrays)
    alias = [x["alias_of"] for x in stored_index(dest)["arrays"]]
    assert alias == [None, 0, None, None, 3, None]
    with open_h5(dest) as r:
        for key, source in arrays.items():
            same(r.arrays[key], source)


def test_dtype_shape_bytes_and_stale_manifest_never_alias(tmp_path):
    base = np.array([1, 2], dtype="<i2")
    arrays = {
        "base": base,
        "same-bytes-other-dtype": base.view("<u2"),
        "same-bytes-other-shape": base.reshape((1, 2)),
        "other-bytes": np.array([1, 3], "<i2"),
        "other-endian": base.astype(">i2"),
    }
    manifest = {
        "encoded_arrays": {
            k: {"digest": "stale-shared", "dtype": "<i2", "shape": [2]} for k in arrays
        }
    }
    dest = tmp_path / "n.h5"
    write_h5_compact(dest, manifest, arrays)
    assert all(x["alias_of"] is None for x in stored_index(dest)["arrays"])
    with open_h5(dest) as r:
        for key, source in arrays.items():
            same(r.arrays[key], source)


def test_equal_hash_still_requires_exact_comparison(tmp_path, monkeypatch):
    monkeypatch.setattr(h5_store, "_content_digest", lambda view: b"collision")
    arrays = {
        "a": np.array([1, 2], np.int16),
        "b": np.array([1, 2], np.int16),
        "c": np.array([1, 3], np.int16),
    }
    dest = tmp_path / "h.h5"
    write_h5_compact(dest, {}, arrays)
    assert [x["alias_of"] for x in stored_index(dest)["arrays"]] == [None, 0, None]
    with open_h5(dest) as r:
        for key, source in arrays.items():
            same(r.arrays[key], source)


def test_arena_splitting_with_fixed_offsets(tmp_path, monkeypatch):
    monkeypatch.setattr(h5_store, "_MAX_ARENA_BYTES", 16)
    arrays = {f"k{i}": np.full(4, i, np.int32) for i in range(5)}
    arrays["big"] = np.arange(100, dtype=np.int32)  # larger than the cap: own arena
    dest = tmp_path / "s.h5"
    write_h5_compact(dest, {}, arrays)
    index = stored_index(dest)
    assert len(index["arenas"]) > 1
    assert sum(m["bytes"] for m in index["arenas"]) == sum(
        a.nbytes for a in arrays.values()
    )
    with open_h5(dest) as r:
        for key, source in arrays.items():
            same(r.arrays[key], source)


def test_v1_and_v2_writer_and_reader_unchanged(tmp_path):
    unique = {"a": np.arange(3), "b": np.arange(4)}
    dup = {"a": np.arange(3), "b": np.arange(3)}
    write_h5(tmp_path / "v1.h5", {"m": 1}, unique)
    write_h5(tmp_path / "v2.h5", {"m": 1}, dup)
    with h5py.File(tmp_path / "v1.h5", "r") as f:
        assert f.attrs["schema_version"] == 1
    with h5py.File(tmp_path / "v2.h5", "r") as f:
        assert f.attrs["schema_version"] == 2
    for name, arrs in (("v1.h5", unique), ("v2.h5", dup)):
        with open_h5(tmp_path / name) as r:
            assert list(r.arrays) == list(arrs)
            for k, a in arrs.items():
                same(r.arrays[k], a)


# ---------------------------------------------------------------- lazy / closed


def test_lazy_read_touches_only_requested_span(tmp_path, monkeypatch):
    arrays = {
        "filler": np.arange(100000).astype(np.int8),
        "zeta": np.array([1], np.int8),
        "alpha": np.array([2], np.int8),
    }
    dest = tmp_path / "l.h5"
    write_h5_compact(dest, {}, arrays)
    slices = []
    original = h5py.Dataset.__getitem__

    def spy(self, *a, **k):
        if a and isinstance(a[0], slice):
            slices.append((a[0].start, a[0].stop))
        return original(self, *a, **k)

    monkeypatch.setattr(h5py.Dataset, "__getitem__", spy)
    reads = []
    original_read = h5_store.H5Reader._read_compact

    def spy_read(self, entry):
        reads.append(entry)
        return original_read(self, entry)

    monkeypatch.setattr(h5_store.H5Reader, "_read_compact", spy_read)
    with open_h5(dest) as r:
        assert reads == [] and slices == []
        keys = list(r.arrays)
        assert keys == list(arrays) and reads == []
        got = r.arrays["zeta"]
        assert got.tolist() == [1]
        assert len(reads) == 1
        assert slices == [(100000, 100001)]
        same(r.arrays["alpha"], arrays["alpha"])
        assert slices[-1] == (100001, 100002)


def test_reader_closed_semantics(tmp_path):
    write_h5_compact(tmp_path / "s.h5", {"a": 1}, {"x": np.ones(3)})
    with open_h5(tmp_path / "s.h5") as r:
        arrays = r.arrays
        assert not r.closed
    assert r.closed
    with pytest.raises(ReaderClosedError):
        arrays["x"]
    with pytest.raises(ReaderClosedError):
        len(arrays)
    with pytest.raises(ReaderClosedError):
        _ = r.manifest
    r.close()  # idempotent


def test_missing_key(tmp_path):
    write_h5_compact(tmp_path / "s.h5", {}, {"a": np.zeros(2)})
    with open_h5(tmp_path / "s.h5") as r:
        assert "nope" not in r.arrays
        with pytest.raises(KeyError):
            r.arrays["nope"]


# ---------------------------------------------------------------- open_product


def _product_fixture(tmp_path, mutate=None):
    arrays = {
        "zeta": np.arange(6, dtype=np.int32).reshape(2, 3),
        "alpha": np.array([True, False, True]),
        "mid": np.linspace(0, 1, 4),
        "dup": np.arange(6, dtype=np.int32).reshape(2, 3),
        "scalar": np.array(2.5),
        "empty": np.zeros((0, 3), np.float32),
    }
    path = tmp_path / "p.h5"
    manifest = {
        "archive": str(path),
        "encoded_arrays": {
            k: {"digest": digest(a), "shape": list(a.shape), "dtype": a.dtype.str}
            for k, a in arrays.items()
        },
    }
    if mutate:
        mutate(manifest)
    write_h5_compact(path, manifest, arrays)
    return path, manifest, arrays


def test_open_product_reads_compact_h5_with_digest_verification(tmp_path, monkeypatch):
    path, manifest, arrays = _product_fixture(tmp_path)
    calls = []
    original = h5_store.H5Reader._read_compact

    def spy(self, entry):
        calls.append(entry)
        return original(self, entry)

    monkeypatch.setattr(h5_store.H5Reader, "_read_compact", spy)
    with open_product(path) as p:
        assert p.storage == "h5"
        assert p.manifest == manifest
        assert calls == []
        assert list(p.arrays) == list(arrays)
        got = p.arrays["dup"]
        assert len(calls) == 1
        assert not got.flags.writeable
        assert p.arrays["dup"] is got and len(calls) == 1
        for k, a in arrays.items():
            v = p.arrays[k]
            assert digest(v) == manifest["encoded_arrays"][k]["digest"]
            same(v, a)
        held = p.arrays
    assert p.closed
    with pytest.raises(ProductClosedError):
        held["zeta"]
    with pytest.raises(ProductClosedError):
        _ = p.manifest


def test_open_product_still_performs_original_digest_and_dtype_checks(tmp_path):
    def bad_digest(m):
        m["encoded_arrays"]["zeta"]["digest"] = "0" * 64

    path, _, _ = _product_fixture(tmp_path, bad_digest)
    with open_product(path) as p:
        _ = p.arrays["alpha"]
        with pytest.raises(DigestMismatchError):
            p.arrays["zeta"]

    def bad_dtype(m):
        m["encoded_arrays"]["zeta"]["dtype"] = "<i8"

    path, _, _ = _product_fixture(tmp_path, bad_dtype)
    with open_product(path) as p, pytest.raises(DtypeMismatchError):
        p.arrays["zeta"]


# ---------------------------------------------------------------- writer negatives


@pytest.mark.parametrize(
    "arr",
    [
        np.array([object()], dtype=object),
        np.array(["ab"]),
        np.array([b"ab"]),
        np.array(["2020-01-01"], dtype="datetime64[D]"),
        np.zeros(2, dtype=[("a", "<i4")]),
    ],
)
def test_unsupported_dtype_keeps_previous_and_leaves_no_part(tmp_path, arr):
    dest = tmp_path / "s.h5"
    write_h5_compact(dest, {"v": 1}, {"ok": np.arange(3)})
    before = dest.read_bytes()
    with pytest.raises(UnsupportedArrayDtypeError):
        write_h5_compact(dest, {"v": 2}, {"ok": np.arange(3), "bad": arr})
    assert dest.read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["s.h5"]


def test_non_ndarray_and_non_str_key_rejected(tmp_path):
    with pytest.raises(UnsupportedArrayDtypeError):
        write_h5_compact(tmp_path / "s.h5", {}, cast(Any, {"a": [1, 2, 3]}))
    with pytest.raises(ManifestError):
        write_h5_compact(tmp_path / "s.h5", {}, cast(Any, {1: np.zeros(2)}))
    with pytest.raises(ManifestError):
        write_h5_compact(tmp_path / "s.h5", {}, {"\ud800": np.zeros(2)})
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "manifest",
    [{"s": {1, 2}}, {"t": (1, 2)}, {1: "x"}, {"f": float("nan")}, [1]],
)
def test_manifest_failure_rolls_back(tmp_path, manifest):
    dest = tmp_path / "s.h5"
    write_h5_compact(dest, {"v": 1}, {"a": np.arange(3)})
    before = dest.read_bytes()
    with pytest.raises(ManifestError):
        write_h5_compact(dest, manifest, {"a": np.arange(5)})
    assert dest.read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["s.h5"]


def test_midway_write_failure_removes_part_and_keeps_destination(tmp_path, monkeypatch):
    dest = tmp_path / "s.h5"
    write_h5_compact(dest, {"v": 1}, {"a": np.arange(3)})
    before = dest.read_bytes()
    original = h5_store._write_arena_slice
    count = {"n": 0}

    def boom(dataset, start, stop, flat):
        count["n"] += 1
        if count["n"] == 2:
            raise OSError("disk full")
        return original(dataset, start, stop, flat)

    monkeypatch.setattr(h5_store, "_write_arena_slice", boom)
    d = np.arange(5)
    with pytest.raises(OSError, match="disk full"):
        write_h5_compact(
            dest,
            {"v": 2},
            {"a": d, "alias": d.copy(), "b": np.arange(6.0), "c": np.arange(2.0)},
        )
    assert dest.read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["s.h5"]


def test_replace_failure_removes_part_and_keeps_destination(tmp_path, monkeypatch):
    dest = tmp_path / "s.h5"
    write_h5_compact(dest, {"v": 1}, {"a": np.arange(3)})
    before = dest.read_bytes()

    def bad_replace(src, dst):
        raise OSError("replace failed")

    monkeypatch.setattr(os, "replace", bad_replace)
    with pytest.raises(OSError, match="replace failed"):
        write_h5_compact(dest, {"v": 2}, {"a": np.arange(9)})
    monkeypatch.undo()
    assert dest.read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["s.h5"]


def test_overwrite_success_replaces(tmp_path):
    dest = tmp_path / "s.h5"
    write_h5_compact(dest, {"v": 1}, {"a": np.arange(3)})
    write_h5_compact(dest, {"v": 2}, {"b": np.arange(4)})
    with open_h5(dest) as r:
        assert r.manifest == {"v": 2} and list(r.arrays) == ["b"]
    assert [p.name for p in tmp_path.iterdir()] == ["s.h5"]


def test_missing_optional_dependency_is_named_and_creates_nothing(
    tmp_path, monkeypatch
):
    def missing():
        raise h5_store.OptionalDependencyError("optional dependency 'h5py' missing")

    monkeypatch.setattr(h5_store, "_h5py", missing)
    with pytest.raises(h5_store.OptionalDependencyError):
        write_h5_compact(tmp_path / "s.h5", {}, {"a": np.zeros(2)})
    assert list(tmp_path.iterdir()) == []


# ---------------------------------------------------------------- reader negatives


def _fixture_arrays():
    a = np.arange(4, dtype=np.int16)
    return {
        "a": a,
        "b": a.copy(),
        "c": np.array([1.0, 2.0], np.float32),
        "d": np.array([9, 8], np.int16),
    }


def _fixture(tmp_path):
    path = tmp_path / "v3.h5"
    write_h5_compact(path, {"m": 1}, _fixture_arrays())
    index = stored_index(path)
    # sanity of the layout the mutations below rely on
    assert [e["alias_of"] for e in index["arrays"]] == [None, 0, None, None]
    assert [m["dtype"] for m in index["arenas"]] == ["<i2", "<f4"]
    assert [e["offset"] for e in index["arrays"]] == [0, 0, 0, 8]
    return path


def _set(i, field, value):
    def mutate(table):
        table["arrays"][i][field] = value

    return mutate


def _delete_entry(table):
    del table["arrays"][3]


def _delete_field(table):
    del table["arrays"][0]["length"]


def _arena_dtype(table):
    table["arenas"][0]["dtype"] = "<i4"


def _arena_bytes(table):
    table["arenas"][0]["bytes"] = 16


def _extra_key(table):
    table["extra"] = 1


def _format(table):
    table["format"] = "other"


MUTATIONS = {
    "unknown-format": _format,
    "extra-top-level-key": _extra_key,
    "bad-dtype-string": _set(0, "dtype", "not-a-dtype"),
    "object-dtype": _set(0, "dtype", "|O"),
    "non-canonical-dtype": _set(0, "dtype", "int16"),
    "length-mismatch": _set(0, "length", 6),
    "offset-overrun": _set(3, "offset", 10),
    "offset-misaligned": _set(3, "offset", 7),
    "offset-bool": _set(0, "offset", True),
    "offset-float": _set(0, "offset", 0.0),
    "length-bool": _set(0, "length", True),
    "shape-float": _set(0, "shape", [4.0]),
    "shape-negative": _set(0, "shape", [-4]),
    "shape-bool": _set(0, "shape", [True]),
    "arena-out-of-range": _set(2, "arena", 5),
    "arena-bool": _set(2, "arena", False),
    "arena-wrong-dtype": _set(2, "arena", 0),
    "alias-self": _set(1, "alias_of", 1),
    "alias-forward": _set(1, "alias_of", 3),
    "alias-mismatch": _set(1, "alias_of", 2),
    "alias-bool": _set(1, "alias_of", True),
    "alias-negative": _set(1, "alias_of", -1),
    "duplicate-key": _set(1, "key", "a"),
    "non-string-key": _set(1, "key", 3),
    "unreferenced-bytes": _delete_entry,
    "overlapping-span": _set(3, "offset", 4),
    "missing-field": _delete_field,
    "arena-dtype-disagrees-with-dataset": _arena_dtype,
    "arena-size-disagrees-with-dataset": _arena_bytes,
}


@pytest.mark.parametrize("name", list(MUTATIONS))
def test_malformed_index_is_named(tmp_path, name):
    path = _fixture(tmp_path)
    rewrite_index(path, MUTATIONS[name])
    with pytest.raises(MalformedH5Error), open_h5(path):
        pass


def test_unknown_schema_version_refused(tmp_path):
    path = _fixture(tmp_path)
    with h5py.File(path, "r+") as f:
        f.attrs["schema_version"] = 999
    with (
        pytest.raises(MalformedH5Error, match="unsupported H5 schema version"),
        open_h5(path),
    ):
        pass


def test_manifest_index_and_arena_encodings_must_be_declared_gzip(tmp_path):
    for target, message in (
        ("manifest_json", "v3 manifest encoding is unsupported"),
        ("array_index_json", "v3 array index encoding is unsupported"),
        ("arenas/00000000", "v3 arena encoding is unsupported"),
    ):
        path = _fixture(tmp_path)
        with h5py.File(path, "r+") as f:
            f[target].attrs["encoding"] = "raw"
        with pytest.raises(MalformedH5Error, match=message), open_h5(path):
            pass


def test_uncompressed_arena_is_refused(tmp_path):
    path = _fixture(tmp_path)
    with h5py.File(path, "r+") as f:
        data = f["arenas/00000000"][()]
        del f["arenas/00000000"]
        ds = f.create_dataset("arenas/00000000", data=data)
        ds.attrs["encoding"] = "gzip"
    with pytest.raises(MalformedH5Error, match="arena encoding"), open_h5(path):
        pass


def test_missing_or_extra_arena_and_legacy_members_are_refused(tmp_path):
    path = _fixture(tmp_path)
    with h5py.File(path, "r+") as f:
        del f["arenas/00000001"]
    with pytest.raises(MalformedH5Error), open_h5(path):
        pass
    path = _fixture(tmp_path)
    with h5py.File(path, "r+") as f:
        f.create_dataset("arenas/00000009", data=np.zeros(2, np.int8))
    with pytest.raises(MalformedH5Error), open_h5(path):
        pass
    path = _fixture(tmp_path)
    with h5py.File(path, "r+") as f:
        f.create_group("arrays")
    with pytest.raises(MalformedH5Error), open_h5(path):
        pass


def test_index_missing_or_not_json_is_named(tmp_path):
    path = _fixture(tmp_path)
    with h5py.File(path, "r+") as f:
        del f["array_index_json"]
    with pytest.raises(MalformedH5Error), open_h5(path):
        pass
    path = _fixture(tmp_path)
    with h5py.File(path, "r+") as f:
        del f["array_index_json"]
        ds = f.create_dataset(
            "array_index_json",
            data=np.frombuffer(b"not json", np.uint8),
            compression="gzip",
            compression_opts=4,
            shuffle=True,
        )
        ds.attrs["encoding"] = "gzip"
    with pytest.raises(MalformedH5Error), open_h5(path):
        pass


def test_truncated_file_is_named(tmp_path):
    path = _fixture(tmp_path)
    trunc = tmp_path / "t.h5"
    trunc.write_bytes(path.read_bytes()[:100])
    with pytest.raises(MalformedH5Error), open_h5(trunc):
        pass
