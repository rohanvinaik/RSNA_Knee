import hashlib
import os

import numpy as np
import pytest

pytest.importorskip("h5py")

from knee.encoding import h5_store
from knee.encoding.h5_store import (
    MalformedH5Error,
    ManifestError,
    ReaderClosedError,
    UnsupportedArrayDtypeError,
    open_h5,
    write_h5,
)


def dig(a):
    return hashlib.sha256(
        a.dtype.str.encode() + repr(a.shape).encode() + a.tobytes()
    ).hexdigest()


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
    strided_base = np.arange(24, dtype=np.int32).reshape(4, 6)
    strided = strided_base[:, ::2]
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
        "a/b with space": np.array([1, 2], np.int16),
        "zeta": np.array([1], np.int8),
        "alpha": np.array([2], np.int8),
    }


MANIFEST = {
    "layout_id": "L-1",
    "reference_ids": ["r1", "r2"],
    "counts": {"places": 12345678901234567890, "zero": 0},
    "source": {"artifact": "x.npz.xz", "digest": "ab" * 32, "ünï": "ç"},
    "flag": None,
    "ratio": 0.1,
}


def test_round_trip_and_identity(tmp_path):
    arrays = sample()
    dest = tmp_path / "s.h5"
    assert write_h5(dest, MANIFEST, arrays) == dest
    with open_h5(dest) as r:
        assert r.manifest == MANIFEST
        assert list(r.manifest["source"]) == list(MANIFEST["source"])
        assert type(r.manifest["counts"]["places"]) is int
        assert list(r.arrays) == list(arrays)  # source keys and order
        assert len(r.arrays) == len(arrays)
        for k, a in arrays.items():
            got = r.arrays[k]
            assert got.dtype == a.dtype and got.shape == a.shape
            assert got.tobytes() == a.tobytes()
            assert dig(got) == dig(a)
    assert [p.name for p in tmp_path.iterdir()] == ["s.h5"]


def test_endian_complex_float16_payload_and_strided_arrays_are_bit_exact(tmp_path):
    arrays = sample()
    dest = tmp_path / "bit-patterns.h5"
    write_h5(dest, {"purpose": "dtype-and-byte-preservation"}, arrays)

    with open_h5(dest) as reader:
        for name in (
            "be_c128_payload",
            "be_c128_scalar",
            "be_f4_scalar",
            "be_i4_scalar",
            "f16_nan_payload",
            "strided",
        ):
            source = arrays[name]
            loaded = reader.arrays[name]
            assert loaded.dtype == source.dtype
            assert loaded.shape == source.shape
            assert loaded.tobytes() == source.tobytes()
            assert dig(loaded) == dig(source)
        assert arrays["strided"].strides != reader.arrays["strided"].strides
        # The serialized values remain exact even though HDF5 materializes a
        # contiguous result when reading the strided source view.
        assert reader.arrays["strided"].flags.c_contiguous


def test_missing_key(tmp_path):
    write_h5(tmp_path / "s.h5", {}, {"a": np.zeros(2)})
    with open_h5(tmp_path / "s.h5") as r:
        assert "nope" not in r.arrays
        with pytest.raises(KeyError):
            r.arrays["nope"]


def test_lazy_one_array_does_not_materialize_others(tmp_path, monkeypatch):
    write_h5(tmp_path / "s.h5", {}, sample())
    calls = []
    orig = h5_store.H5Reader._read

    def spy(self, name):
        calls.append(name)
        return orig(self, name)

    monkeypatch.setattr(h5_store.H5Reader, "_read", spy)
    with open_h5(tmp_path / "s.h5") as r:
        assert calls == []  # opening loads no array
        keys = list(r.arrays)
        _ = r.arrays["zeta"]
        assert len(calls) == 1
        assert calls[0] == f"{keys.index('zeta'):08d}"
        _ = r.arrays["alpha"]
        assert len(calls) == 2 and calls[0] != calls[1]


def test_reader_closed(tmp_path):
    write_h5(tmp_path / "s.h5", {"a": 1}, {"x": np.ones(3)})
    with open_h5(tmp_path / "s.h5") as r:
        arrays = r.arrays
    with pytest.raises(ReaderClosedError):
        arrays["x"]
    with pytest.raises(ReaderClosedError):
        len(arrays)
    with pytest.raises(ReaderClosedError):
        _ = r.manifest
    r.close()  # idempotent


def test_invalid_and_malformed(tmp_path):
    bad = tmp_path / "bad.h5"
    bad.write_bytes(b"not hdf5 at all")
    with pytest.raises(MalformedH5Error), open_h5(bad):
        pass
    import h5py

    foreign = tmp_path / "foreign.h5"
    with h5py.File(foreign, "w") as f:
        f.create_dataset("other", data=[1])
    with pytest.raises(MalformedH5Error), open_h5(foreign):
        pass
    good = tmp_path / "g.h5"
    write_h5(good, {}, {"x": np.arange(1000)})
    trunc = tmp_path / "t.h5"
    trunc.write_bytes(good.read_bytes()[:100])
    with pytest.raises(MalformedH5Error), open_h5(trunc):
        pass
    with pytest.raises(FileNotFoundError), open_h5(tmp_path / "absent.h5"):
        pass


@pytest.mark.parametrize(
    "manifest_dtype,manifest_shape,manifest_text",
    [
        (np.float64, (8,), b"{}      "),
        (np.uint8, (2, 4), b'{"x":1} '),
        (np.uint8, (9,), b'{"x":NaN}'),
    ],
)
def test_malformed_manifest_encoding_is_named(
    tmp_path, manifest_dtype, manifest_shape, manifest_text
):
    import h5py

    path = tmp_path / "malformed-manifest.h5"
    manifest_values = np.frombuffer(manifest_text, dtype=np.uint8).astype(
        manifest_dtype
    )
    with h5py.File(path, "w") as f:
        f.create_dataset("manifest_json", data=manifest_values.reshape(manifest_shape))
        f.create_group("arrays")
    with pytest.raises(MalformedH5Error), open_h5(path):
        pass


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
def test_unsupported_dtype_leaves_nothing_and_keeps_previous(tmp_path, arr):
    dest = tmp_path / "s.h5"
    write_h5(dest, {"v": 1}, {"ok": np.arange(3)})
    before = dest.read_bytes()
    with pytest.raises(UnsupportedArrayDtypeError):
        write_h5(dest, {"v": 2}, {"ok": np.arange(3), "bad": arr})
    assert dest.read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["s.h5"]


def test_unsupported_dtype_new_destination(tmp_path):
    dest = tmp_path / "n.h5"
    with pytest.raises(UnsupportedArrayDtypeError):
        write_h5(dest, {}, {"bad": np.array(["x"])})
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "manifest",
    [
        {"s": {1, 2}},
        {"t": (1, 2)},
        {1: "x"},
        {"f": float("nan")},
        {"f": float("inf")},
        [1],
    ],
)
def test_manifest_serialization_failure_rolls_back(tmp_path, manifest):
    dest = tmp_path / "s.h5"
    write_h5(dest, {"v": 1}, {"a": np.arange(3)})
    before = dest.read_bytes()
    with pytest.raises(ManifestError):
        write_h5(dest, manifest, {"a": np.arange(5)})
    assert dest.read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["s.h5"]


def test_write_failure_midway_removes_part_and_keeps_destination(tmp_path, monkeypatch):
    dest = tmp_path / "s.h5"
    write_h5(dest, {"v": 1}, {"a": np.arange(3)})
    before = dest.read_bytes()
    orig = h5_store._write_dataset
    count = {"n": 0}

    def boom(group, index, key, arr):
        count["n"] += 1
        if count["n"] == 2:
            raise OSError("disk full")
        return orig(group, index, key, arr)

    monkeypatch.setattr(h5_store, "_write_dataset", boom)
    with pytest.raises(OSError, match="disk full"):
        write_h5(dest, {"v": 2}, {"a": np.arange(5), "b": np.arange(6)})
    assert dest.read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["s.h5"]


def test_replace_failure_removes_part_and_keeps_destination(tmp_path, monkeypatch):
    dest = tmp_path / "s.h5"
    write_h5(dest, {"v": 1}, {"a": np.arange(3)})
    before = dest.read_bytes()

    def bad_replace(src, dst):
        raise OSError("replace failed")

    monkeypatch.setattr(os, "replace", bad_replace)
    with pytest.raises(OSError, match="replace failed"):
        write_h5(dest, {"v": 2}, {"a": np.arange(9)})
    monkeypatch.undo()
    assert dest.read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["s.h5"]


def test_overwrite_success_replaces(tmp_path):
    dest = tmp_path / "s.h5"
    write_h5(dest, {"v": 1}, {"a": np.arange(3)})
    write_h5(dest, {"v": 2}, {"b": np.arange(4)})
    with open_h5(dest) as r:
        assert r.manifest == {"v": 2}
        assert list(r.arrays) == ["b"]
    assert [p.name for p in tmp_path.iterdir()] == ["s.h5"]


def test_non_ndarray_rejected_without_cast(tmp_path):
    with pytest.raises(UnsupportedArrayDtypeError):
        write_h5(tmp_path / "s.h5", {}, {"a": [1, 2, 3]})
    assert list(tmp_path.iterdir()) == []


def test_empty_store(tmp_path):
    write_h5(tmp_path / "e.h5", {}, {})
    with open_h5(tmp_path / "e.h5") as r:
        assert r.manifest == {} and len(r.arrays) == 0


def test_gzip_shuffle_is_lossless_and_skips_scalar_and_empty_arrays(tmp_path):
    import h5py

    arrays = sample()
    dest = tmp_path / "filtered.h5"
    write_h5(dest, MANIFEST, arrays)

    with h5py.File(dest, "r") as stored:
        group = stored["arrays"]
        for index, (key, source) in enumerate(arrays.items()):
            dataset = group[f"{index:08d}"]
            assert dataset.attrs["key"] == key
            assert dataset.attrs["dtype"] == source.dtype.str
            if source.ndim > 0 and source.size > 0:
                assert dataset.compression == "gzip"
                assert dataset.compression_opts == 4
                assert dataset.shuffle is True
            else:
                assert dataset.compression is None
                assert dataset.shuffle is False

    with open_h5(dest) as reader:
        assert reader.manifest == MANIFEST
        assert list(reader.arrays) == list(arrays)
        for key, source in arrays.items():
            restored = reader.arrays[key]
            assert restored.dtype == source.dtype
            assert restored.shape == source.shape
            assert restored.tobytes() == source.tobytes()
