from pathlib import Path

import numpy as np
import pytest

from knee.array_archive import ArrayArchive, write_npz_xz
from knee.encoding import h5_store, product
from knee.encoding.product import (
    ArchiveReferenceError,
    DigestMismatchError,
    DtypeMismatchError,
    MissingArrayError,
    ProductClosedError,
    ProductMalformedError,
    ProductNotFoundError,
    ShapeMismatchError,
    UnsupportedArrayError,
    open_product,
)
from knee.json_store import dump_json_atomic
from knee.receipt import digest


def arrays():
    return {
        "zeta": np.arange(6, dtype=np.int32).reshape(2, 3),
        "alpha": np.array([True, False, True]),
        "mid": np.linspace(0, 1, 4),
    }


def manifest_for(arrs, archive):
    return {
        "archive": archive,
        "encoded_arrays": {
            k: {"digest": digest(a), "shape": list(a.shape), "dtype": a.dtype.str}
            for k, a in arrs.items()
        },
    }


FORMATS = ["npz", "h5"]
_DEFAULT_ARCHIVE = object()


def build(fmt, tmp_path, arrs=None, mutate=None, archive_ref=_DEFAULT_ARCHIVE):
    arrs = arrays() if arrs is None else arrs
    if fmt == "npz":
        arch = tmp_path / "p.npz.xz"
        write_npz_xz(arch, arrs.items())
        m = manifest_for(
            arrs,
            str(arch) if archive_ref is _DEFAULT_ARCHIVE else archive_ref,
        )
        if mutate:
            mutate(m)
        mp = tmp_path / "p.json.xz"
        dump_json_atomic(mp, m)
        return mp, m
    pytest.importorskip("h5py")
    path = tmp_path / "p.h5"
    m = manifest_for(arrs, str(path))
    if mutate:
        mutate(m)
    h5_store.write_h5(path, m, arrs)
    return path, m


@pytest.mark.parametrize("fmt", FORMATS)
def test_round_trip_manifest_order_and_digests(fmt, tmp_path):
    path, m = build(fmt, tmp_path)
    src = arrays()
    with open_product(path) as p:
        assert p.manifest == m
        assert list(p.arrays) == list(src)
        assert p.arrays.files == list(src)
        for k, a in src.items():
            got = p.arrays[k]
            assert digest(got) == m["encoded_arrays"][k]["digest"]
            assert got.dtype == a.dtype and got.shape == a.shape


def test_legacy_relative_archive_resolved_against_manifest_parent(tmp_path):
    path, _ = build("npz", tmp_path, archive_ref="p.npz.xz")
    with open_product(path) as p:
        assert list(p.arrays) == list(arrays())


def test_legacy_plain_json_manifest_path_resolves_xz_sibling(tmp_path):
    _path, m = build("npz", tmp_path)
    with open_product(tmp_path / "p.json") as p:  # load_json resolves the .xz sibling
        assert p.manifest == m


def test_lazy_npz_reads_only_requested(tmp_path, monkeypatch):
    path, _ = build("npz", tmp_path)
    calls = []
    orig = ArrayArchive.__getitem__

    def spy(self, name):
        calls.append(name)
        return orig(self, name)

    monkeypatch.setattr(ArrayArchive, "__getitem__", spy)
    with open_product(path) as p:
        assert calls == []
        list(p.arrays)
        _ = p.arrays["alpha"]
        assert calls == ["alpha"]


def test_verified_array_is_loaded_once_cached_readonly_and_cleared_on_close(
    tmp_path, monkeypatch
):
    path, manifest = build("npz", tmp_path)
    expected = arrays()["zeta"]

    class ChangingArchive:
        def __init__(self):
            self.calls = {}
            self.closed = False

        def __contains__(self, name):
            return name == "zeta"

        def __getitem__(self, name):
            self.calls[name] = self.calls.get(name, 0) + 1
            value = expected.copy()
            if self.calls[name] > 1:
                value += 100
            return value

        def __iter__(self):
            return iter(("zeta",))

        def __len__(self):
            return 1

        def close(self):
            self.closed = True

    source = ChangingArchive()
    monkeypatch.setattr(product, "open_arrays", lambda _path: source)
    with open_product(path) as opened:
        values = opened.arrays
        first = values["zeta"]
        assert first.tobytes() == expected.tobytes()
        assert not first.flags.writeable
        with pytest.raises(ValueError):
            first.flags.writeable = True
        with pytest.raises(ValueError):
            first[0, 0] = -1
        second = values["zeta"]
        assert second is first
        assert source.calls == {"zeta": 1}
        assert opened.manifest == manifest
    assert source.closed
    assert values._cache == {}


@pytest.mark.parametrize("fmt", FORMATS)
def test_cached_verified_array_cannot_be_made_writeable(fmt, tmp_path):
    path, manifest = build(fmt, tmp_path)
    expected = arrays()["zeta"]
    with open_product(path) as opened:
        first = opened.arrays["zeta"]
        assert opened.arrays["zeta"] is first
        assert first.dtype == expected.dtype
        assert first.shape == expected.shape
        assert first.tobytes(order="C") == expected.tobytes(order="C")
        assert digest(first) == manifest["encoded_arrays"]["zeta"]["digest"]
        assert not first.flags.writeable
        with pytest.raises(ValueError):
            first.flags.writeable = True
        with pytest.raises(ValueError):
            first[0, 0] = -1
        assert first.tobytes(order="C") == expected.tobytes(order="C")


@pytest.mark.parametrize(
    "array",
    [
        np.array([0x7FF8000000000042, 0x8000000000000000], dtype=np.uint64).view(
            np.float64
        ),
        np.array([1.25, -0.0], dtype=">f8"),
        np.empty((2, 0, 3), dtype=np.int16),
        np.array(-0.0, dtype=">f8"),
    ],
)
def test_immutable_snapshot_preserves_dtype_shape_and_exact_bytes(array):
    frozen = product._immutable_snapshot(array)
    assert frozen.dtype.str == array.dtype.str
    assert frozen.shape == array.shape
    assert frozen.tobytes(order="C") == array.tobytes(order="C")
    assert not frozen.flags.writeable
    with pytest.raises(ValueError):
        frozen.flags.writeable = True


def test_lazy_h5_reads_only_requested(tmp_path, monkeypatch):
    path, _ = build("h5", tmp_path)
    calls = []
    orig = h5_store.H5Reader._read

    def spy(self, name):
        calls.append(name)
        return orig(self, name)

    monkeypatch.setattr(h5_store.H5Reader, "_read", spy)
    with open_product(path) as p:
        assert calls == []
        _ = p.arrays["zeta"]
        assert len(calls) == 1


def test_npz_closes_archive_and_blocks_access(tmp_path, monkeypatch):
    path, _ = build("npz", tmp_path)
    seen = []
    real = product.open_arrays

    def capture(*a, **k):
        archive = real(*a, **k)
        seen.append(archive)
        return archive

    monkeypatch.setattr(product, "open_arrays", capture)
    with open_product(path) as p:
        arrs = p.arrays
        _ = arrs["zeta"]
    assert seen[0]._npz is None
    assert p.closed
    with pytest.raises(ProductClosedError):
        arrs["zeta"]
    with pytest.raises(ProductClosedError):
        _ = p.manifest


def test_h5_closes_reader(tmp_path, monkeypatch):
    path, _ = build("h5", tmp_path)
    seen = []
    real = h5_store.open_h5

    from contextlib import contextmanager

    @contextmanager
    def capture(pth):
        with real(pth) as reader:
            seen.append(reader)
            yield reader

    monkeypatch.setattr(h5_store, "open_h5", capture)
    with open_product(path) as p:
        arrs = p.arrays
        _ = arrs["zeta"]
    assert seen[0].closed
    with pytest.raises(ProductClosedError):
        arrs["zeta"]


def test_h5_dependency_absent_is_named(tmp_path, monkeypatch):
    path = tmp_path / "p.h5"
    path.write_bytes(b"placeholder")

    def missing():
        raise h5_store.OptionalDependencyError(
            "optional dependency 'h5py' is not installed"
        )

    monkeypatch.setattr(h5_store, "_h5py", missing)
    with pytest.raises(h5_store.OptionalDependencyError), open_product(path):
        pass


@pytest.mark.parametrize("name", ["absent.json.xz", "absent.h5"])
def test_missing_manifest_or_product(tmp_path, name):
    with pytest.raises(ProductNotFoundError), open_product(tmp_path / name):
        pass


def test_malformed_legacy_manifests(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    with pytest.raises(ProductMalformedError), open_product(bad):
        pass
    for payload in ("[1]", "{}", '{"encoded_arrays": []}'):
        bad.write_text(payload)
        with pytest.raises(ProductMalformedError), open_product(bad):
            pass
    bad.write_text(
        '{"encoded_arrays": {"a": {"digest": 1, "shape": [], "dtype": "|b1"}}}'
    )
    with pytest.raises(ProductMalformedError), open_product(bad):
        pass
    xz = tmp_path / "trunc.json.xz"
    xz.write_bytes(b"\xfd7zXZ\x00garbage")
    with pytest.raises(ProductMalformedError), open_product(xz):
        pass


def test_malformed_legacy_archive_is_named(tmp_path):
    path, manifest = build("npz", tmp_path)
    Path(manifest["archive"]).write_bytes(b"not an NPZ or XZ archive")
    with (
        pytest.raises(ProductMalformedError, match="archive_unreadable"),
        open_product(path),
    ):
        pass


def test_malformed_h5_product(tmp_path):
    pytest.importorskip("h5py")
    bad = tmp_path / "bad.h5"
    bad.write_bytes(b"not hdf5")
    with pytest.raises(ProductMalformedError), open_product(bad):
        pass
    h5_store.write_h5(tmp_path / "nomanifest.h5", {"x": 1}, {})
    with pytest.raises(ProductMalformedError), open_product(tmp_path / "nomanifest.h5"):
        pass  # manifest lacks encoded_arrays


@pytest.mark.parametrize("ref", ["../p.npz.xz", "", "a/../../p.npz.xz", 5, None])
def test_unsafe_archive_reference(tmp_path, ref):
    path, _ = build("npz", tmp_path, archive_ref=ref)
    with pytest.raises(ArchiveReferenceError), open_product(path):
        pass


def test_relative_archive_does_not_fall_back_to_current_working_directory(
    tmp_path, monkeypatch
):
    manifest_dir = tmp_path / "manifests"
    working_dir = tmp_path / "cwd"
    manifest_dir.mkdir()
    working_dir.mkdir()
    path, _ = build("npz", manifest_dir, archive_ref="not-next-to-manifest.npz.xz")
    write_npz_xz(working_dir / "not-next-to-manifest.npz.xz", arrays().items())
    monkeypatch.chdir(working_dir)
    with pytest.raises(ArchiveReferenceError), open_product(path):
        pass


def test_missing_archive_reference(tmp_path):
    path, _ = build("npz", tmp_path, archive_ref="gone.npz.xz")
    with pytest.raises(ArchiveReferenceError), open_product(path):
        pass


@pytest.mark.parametrize("fmt", FORMATS)
def test_digest_mismatch(fmt, tmp_path):
    def mut(m):
        m["encoded_arrays"]["zeta"]["digest"] = "0" * 64

    path, _ = build(fmt, tmp_path, mutate=mut)
    with open_product(path) as p:
        _ = p.arrays["alpha"]  # untouched array still reads
        with pytest.raises(DigestMismatchError):
            p.arrays["zeta"]


@pytest.mark.parametrize("fmt", FORMATS)
def test_shape_mismatch(fmt, tmp_path):
    def mut(m):
        m["encoded_arrays"]["zeta"]["shape"] = [3, 2]

    path, _ = build(fmt, tmp_path, mutate=mut)
    with open_product(path) as p, pytest.raises(ShapeMismatchError):
        p.arrays["zeta"]


@pytest.mark.parametrize("fmt", FORMATS)
def test_dtype_mismatch(fmt, tmp_path):
    def mut(m):
        m["encoded_arrays"]["zeta"]["dtype"] = "<i8"

    path, _ = build(fmt, tmp_path, mutate=mut)
    with open_product(path) as p, pytest.raises(DtypeMismatchError):
        p.arrays["zeta"]


@pytest.mark.parametrize("fmt", FORMATS)
def test_missing_and_unsupported_array(fmt, tmp_path):
    def mut(m):
        m["encoded_arrays"]["ghost"] = dict(m["encoded_arrays"]["alpha"])

    path, _ = build(fmt, tmp_path, mutate=mut)
    with open_product(path) as p:
        with pytest.raises(MissingArrayError):
            p.arrays["ghost"]
        with pytest.raises(MissingArrayError):
            p.arrays.get("ghost")  # not silent absence
        with pytest.raises(MissingArrayError):
            p.arrays["never-listed"]
        assert p.arrays.get("never-listed") is None

    def drop(m):
        del m["encoded_arrays"]["alpha"]

    path2, _ = build(fmt, tmp_path / "x" if False else tmp_path, mutate=drop)
    with open_product(path2) as p, pytest.raises(UnsupportedArrayError):
        p.arrays["alpha"]  # in archive but not described by manifest


@pytest.mark.parametrize(
    "unsupported",
    [np.array(["word"], dtype="U4"), np.array([b"word"], dtype="S4")],
)
def test_text_array_dtypes_are_rejected_even_with_matching_manifest(
    tmp_path, unsupported
):
    path, _ = build("npz", tmp_path, arrs={"text": unsupported})
    with (
        open_product(path) as product,
        pytest.raises(UnsupportedArrayError, match="unsupported_array"),
    ):
        product.arrays["text"]


def test_closed_npz_get_unknown_is_not_silent_absence(tmp_path):
    path, _ = build("npz", tmp_path)
    with open_product(path) as opened:
        arrays = opened.arrays
    with pytest.raises(ProductClosedError):
        arrays.get("never-listed")
