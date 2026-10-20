import io
import lzma
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest
from numpy.lib import format as npy_format

from knee import array_archive as aa


def nan_payload():
    bits = np.array(
        [0x7FF8000000000001, 0xFFF8000000000ABC, 0x7FF0000000000123], dtype=np.uint64
    )
    return bits.view(np.float64)


def edge_arrays():
    base = np.arange(24, dtype=np.int16).reshape(4, 6)
    ro = np.arange(5.0)
    ro.setflags(write=False)
    return {
        "zz_first": np.arange(10, dtype=np.uint8),
        "empty": np.empty((0, 3), np.float32),
        "empty_u": np.array([], dtype="<U4"),
        "scalar": np.array(3.5),
        "scalar_u": np.array("héllo"),
        "unicode": np.array(["a", "bé", "日本"]),
        "readonly": ro,
        "fortran": np.asfortranarray(base),
        "strided": np.arange(60, dtype=np.int32).reshape(6, 10)[::2, ::3],
        "transposed": base.T,
        "nan_payload": nan_payload(),
        "neg_zero": np.array([-0.0, 0.0, -0.0], dtype=np.float32),
        "bool": np.array([True, False, True]),
        "big_endian": np.arange(3, dtype=">i8"),
        "aa_last": np.arange(3, dtype="<f4"),
    }


def same(a, b):
    assert a.dtype.str == b.dtype.str
    assert a.shape == b.shape
    assert a.tobytes() == b.tobytes()


def no_residue(directory):
    return sorted(p.name for p in directory.iterdir())


@pytest.fixture
def spools(monkeypatch):
    made = []
    real = tempfile.SpooledTemporaryFile

    def spy(*a, **k):
        s = real(*a, **k)
        made.append((s, k))
        return s

    monkeypatch.setattr(aa.tempfile, "SpooledTemporaryFile", spy)
    return made


def test_default_spool_bound():
    assert aa.SPOOL_MAX_BYTES == 64 * 1024 * 1024


def test_legacy_npz_read(tmp_path):
    arrays = edge_arrays()
    p = tmp_path / "legacy.npz"
    np.savez_compressed(p, **arrays)
    with aa.open_arrays(p) as z:
        assert z.files == list(arrays)
        assert list(z) == list(arrays)
        assert len(z) == len(arrays)
        for n, a in arrays.items():
            same(z[n], a)
        assert "scalar" in z and "nope" not in z
        with pytest.raises(KeyError):
            z["nope"]


def test_xz_roundtrip_and_structure(tmp_path):
    arrays = edge_arrays()
    dest = tmp_path / "a.npz.xz"
    aa.write_npz_xz(dest, arrays)
    raw = lzma.decompress(dest.read_bytes(), format=lzma.FORMAT_XZ)
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        assert [i.filename for i in zf.infolist()] == [n + ".npy" for n in arrays]
        assert all(i.compress_type == zipfile.ZIP_STORED for i in zf.infolist())
    with aa.open_arrays(dest) as z:
        assert z.files == list(arrays)
        for n, a in arrays.items():
            same(z[n], a)
    assert no_residue(tmp_path) == ["a.npz.xz"]


def test_iterable_input_and_unicode_member_name(tmp_path):
    dest = tmp_path / "i.npz.xz"
    pairs = [("zeta", np.arange(3)), ("naïve", np.ones((2, 2))), ("alpha", np.zeros(1))]
    aa.write_npz_xz(dest, (p for p in pairs))
    with aa.open_arrays(dest) as z:
        assert z.files == ["zeta", "naïve", "alpha"]
        assert dict(z.items()).keys() == {"zeta", "naïve", "alpha"}
        for n, a in pairs:
            same(z[n], a)


def test_array_valid_after_close(tmp_path):
    arrays = edge_arrays()
    xz = tmp_path / "c.npz.xz"
    aa.write_npz_xz(xz, arrays)
    leg = tmp_path / "c.npz"
    np.savez(leg, **arrays)
    for p in (xz, leg):
        z = aa.open_arrays(p)
        got = {n: z[n] for n in ("fortran", "strided", "nan_payload")}
        z.close()
        z.close()
        for n, value in got.items():
            same(value, arrays[n])
        got["strided"][0, 0] = 99  # caller-owned and writable
        with pytest.raises(ValueError):
            z["fortran"]
        assert z.files == list(arrays)


def test_no_pickle(tmp_path):
    with pytest.raises(ValueError):
        aa.open_arrays(tmp_path / "x.npz", allow_pickle=True)
    leg = tmp_path / "obj.npz"
    np.savez(leg, o=np.array([{"a": 1}], dtype=object), ok=np.arange(2))
    with aa.open_arrays(leg) as z:
        same(z["ok"], np.arange(2))
        with pytest.raises(ValueError):
            z["o"]
    dest = tmp_path / "o.npz.xz"
    with pytest.raises(ValueError, match="object_dtype"):
        aa.write_npz_xz(
            dest, [("ok", np.arange(3)), ("bad", np.array([{}], dtype=object))]
        )
    struct = np.zeros(2, dtype=[("a", "i4"), ("o", "O")])
    with pytest.raises(ValueError, match="object_dtype"):
        aa.write_npz_xz(dest, {"s": struct})
    assert not dest.exists()
    assert no_residue(tmp_path) == ["obj.npz"]


def test_plain_np_load_cannot_read_xz(tmp_path):
    dest = tmp_path / "s.npz.xz"
    aa.write_npz_xz(dest, {"a": np.arange(5)})
    assert not zipfile.is_zipfile(dest)
    with pytest.raises(ValueError):
        np.load(dest, allow_pickle=False)


def test_spool_threshold_and_spill_dir(tmp_path, monkeypatch, spools):
    dest = tmp_path / "s.npz.xz"
    aa.write_npz_xz(dest, edge_arrays())
    total = len(lzma.decompress(dest.read_bytes()))
    assert total > 100
    spill = tmp_path / "spill"
    spill.mkdir()
    with aa.open_arrays(dest) as z:
        assert spools[-1][0]._rolled is False
        assert spools[-1][1]["max_size"] == aa.SPOOL_MAX_BYTES
        assert spools[-1][1]["dir"] is None
        same(z["fortran"], edge_arrays()["fortran"])
    monkeypatch.setattr(aa, "SPOOL_MAX_BYTES", total)
    with aa.open_arrays(dest, spill_dir=spill):
        assert spools[-1][0]._rolled is False
    monkeypatch.setattr(aa, "SPOOL_MAX_BYTES", total - 1)
    with aa.open_arrays(dest, spill_dir=spill) as z:
        spool, kw = spools[-1]
        assert spool._rolled is True
        assert kw["dir"] == str(spill) and kw["max_size"] == total - 1
        same(z["strided"], edge_arrays()["strided"])
    assert spool.closed
    assert no_residue(spill) == []


def _valid(tmp_path):
    rng = np.random.default_rng(0)
    dest = tmp_path / "r.npz.xz"
    aa.write_npz_xz(dest, {"r": rng.integers(0, 256, 20000, dtype=np.uint8)})
    return dest


def _fail_clean(path, spools, spill, exc=aa.ArrayArchiveError):
    n = len(spools)
    with pytest.raises(exc):
        aa.open_arrays(path, spill_dir=spill)
    assert all(s.closed for s, _ in spools[n:])
    assert no_residue(spill) == []


def test_malformed_inputs_clean_up(tmp_path, spools):
    spill = tmp_path / "spill"
    spill.mkdir()
    src = tmp_path / "in"
    src.mkdir()
    data = _valid(tmp_path).read_bytes()

    cut = src / "cut.npz.xz"
    cut.write_bytes(data[: len(data) // 2])
    _fail_clean(cut, spools, spill)

    garbage = src / "g.npz.xz"
    garbage.write_bytes(b"not xz at all" * 10)
    _fail_clean(garbage, spools, spill)

    flipped = bytearray(data)
    flipped[len(flipped) // 2] ^= 0xFF
    bad = src / "f.npz.xz"
    bad.write_bytes(bytes(flipped))
    _fail_clean(bad, spools, spill)

    empty = src / "e.npz.xz"
    empty.write_bytes(b"")
    _fail_clean(empty, spools, spill)

    _fail_clean(src / "missing.npz.xz", spools, spill, FileNotFoundError)

    text = src / "text.npz.xz"
    text.write_bytes(lzma.compress(b"hello world" * 100, format=lzma.FORMAT_XZ))
    _fail_clean(text, spools, spill)

    buf = io.BytesIO()
    npy_format.write_array(buf, np.arange(4))
    npy = src / "npy.npz.xz"
    npy.write_bytes(lzma.compress(buf.getvalue(), format=lzma.FORMAT_XZ))
    _fail_clean(npy, spools, spill)

    zbad = src / "zip_bad.npz.xz"
    zbad.write_bytes(lzma.compress(b"PK\x03\x04" + b"\x00" * 50, format=lzma.FORMAT_XZ))
    _fail_clean(zbad, spools, spill)

    assert no_residue(src) == sorted(
        [
            "cut.npz.xz",
            "g.npz.xz",
            "f.npz.xz",
            "e.npz.xz",
            "text.npz.xz",
            "npy.npz.xz",
            "zip_bad.npz.xz",
        ]
    )


def test_legacy_non_npz_and_missing(tmp_path):
    p = tmp_path / "plain.npz"
    np.save(tmp_path / "plain.npy", np.arange(3))
    (tmp_path / "plain.npy").rename(p)
    with pytest.raises(aa.ArrayArchiveError):
        aa.open_arrays(p)
    with pytest.raises(FileNotFoundError):
        aa.open_arrays(tmp_path / "missing.npz")


def test_invalid_and_duplicate_names(tmp_path):
    dest = tmp_path / "n.npz.xz"
    bad_lists = [
        [("", np.arange(1))],
        [("a/b", np.arange(1))],
        [("a\\b", np.arange(1))],
        [("a\0b", np.arange(1))],
        [(1, np.arange(1))],
        [("a", np.arange(1)), ("a", np.arange(2))],
    ]
    for items in bad_lists:
        with pytest.raises(ValueError):
            aa.write_npz_xz(dest, items)
        assert no_residue(tmp_path) == []
    with pytest.raises(ValueError):
        aa.write_npz_xz(tmp_path / "wrong.npz", {"a": np.arange(1)})
    assert no_residue(tmp_path) == []


def test_atomic_overwrite_and_failure_preserves_destination(tmp_path):
    dest = tmp_path / "d.npz.xz"
    aa.write_npz_xz(dest, {"old": np.arange(4)})
    before = dest.read_bytes()

    def boom():
        yield "new", np.arange(10)
        raise RuntimeError("mid-stream")

    with pytest.raises(RuntimeError):
        aa.write_npz_xz(dest, boom())
    assert dest.read_bytes() == before
    with pytest.raises(ValueError):
        aa.write_npz_xz(
            dest, [("a", np.arange(2)), ("b", np.array([{}], dtype=object))]
        )
    assert dest.read_bytes() == before
    assert no_residue(tmp_path) == ["d.npz.xz"]

    aa.write_npz_xz(dest, {"new": np.arange(7)})
    with aa.open_arrays(dest) as z:
        assert z.files == ["new"]
        same(z["new"], np.arange(7))
    assert no_residue(tmp_path) == ["d.npz.xz"]


def test_explicit_filter_chain(tmp_path):
    arrays = edge_arrays()
    dest = tmp_path / "f.npz.xz"
    chain = [
        {"id": lzma.FILTER_DELTA, "dist": 1},
        {"id": lzma.FILTER_LZMA2, "preset": 1},
    ]
    aa.write_npz_xz(dest, arrays, filters=chain)
    with aa.open_arrays(dest) as z:
        assert z.files == list(arrays)
        for n, a in arrays.items():
            same(z[n], a)
    assert len(lzma.decompress(dest.read_bytes())) > 0
    assert no_residue(tmp_path) == ["f.npz.xz"]


def test_invalid_filter_chain_cleans_up_and_preserves(tmp_path):
    dest = tmp_path / "bf.npz.xz"
    with pytest.raises((lzma.LZMAError, ValueError)):
        aa.write_npz_xz(dest, {"a": np.arange(3)}, filters=[{"id": 999}])
    assert no_residue(tmp_path) == []
    aa.write_npz_xz(dest, {"a": np.arange(3)})
    before = dest.read_bytes()
    with pytest.raises((lzma.LZMAError, ValueError)):
        aa.write_npz_xz(dest, {"a": np.arange(9)}, filters=[{"id": 999}])
    assert dest.read_bytes() == before
    assert no_residue(tmp_path) == ["bf.npz.xz"]


def test_simultaneous_independent_readers(tmp_path, spools):
    arrays = edge_arrays()
    p1, p2 = tmp_path / "one.npz.xz", tmp_path / "two.npz.xz"
    aa.write_npz_xz(p1, arrays)
    aa.write_npz_xz(p2, {"x": np.arange(100.0), "y": np.arange(5)})
    a, b, c = aa.open_arrays(p1), aa.open_arrays(p2), aa.open_arrays(p1)
    assert len({id(s) for s, _ in spools}) == 3
    same(a["fortran"], arrays["fortran"])
    same(b["x"], np.arange(100.0))
    same(c["unicode"], arrays["unicode"])
    a.close()
    same(c["strided"], arrays["strided"])
    same(b["y"], np.arange(5))
    b.close()
    same(c["neg_zero"], arrays["neg_zero"])
    c.close()

    def read(_):
        with aa.open_arrays(p1) as z:
            return {n: z[n].tobytes() for n in z}

    with ThreadPoolExecutor(4) as ex:
        results = list(ex.map(read, range(8)))
    want = {n: np.asarray(v).tobytes() for n, v in arrays.items()}
    assert all(r == want for r in results)
