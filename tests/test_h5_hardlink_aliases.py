from __future__ import annotations

import h5py
import numpy as np
import pytest

from knee.encoding import h5_store
from knee.encoding.h5_store import MalformedH5Error, open_h5, write_h5


def _same(left: np.ndarray, right: np.ndarray) -> None:
    assert left.dtype.str == right.dtype.str
    assert left.shape == right.shape
    assert left.tobytes() == right.tobytes()


def _object_address(dataset: h5py.Dataset) -> int:
    return int(h5py.h5o.get_info(dataset.id).addr)


def test_exact_duplicate_arrays_share_dataset_but_keep_every_public_name(tmp_path):
    base = np.array([1, -2, 3], dtype=">i4")
    alias = base.copy()
    arrays = {"original/key": base, "alias with spaces": alias, "different": base + 1}
    destination = tmp_path / "shared.h5"

    write_h5(destination, {"array_names": list(arrays)}, arrays)

    with h5py.File(destination, "r") as stored:
        assert stored.attrs["schema_version"] == 2
        assert "array_keys_json" in stored
        assert stored["manifest_json"].compression == "gzip"
        assert stored["manifest_json"].attrs["encoding"] == "gzip"
        assert stored["array_keys_json"].compression == "gzip"
        assert stored["array_keys_json"].attrs["encoding"] == "gzip"
        group = stored["arrays"]
        assert _object_address(group["00000000"]) == _object_address(group["00000001"])
        assert _object_address(group["00000000"]) != _object_address(group["00000002"])
        # The shared dataset attribute remains the canonical first-name fact;
        # the explicit key table retains the alias's distinct public name.
        assert group["00000000"].attrs["key"] == "original/key"
        assert group["00000001"].attrs["key"] == "original/key"

    with open_h5(destination) as reader:
        assert reader.manifest == {"array_names": list(arrays)}
        assert list(reader.arrays) == list(arrays)
        for key, source in arrays.items():
            _same(reader.arrays[key], source)


def test_nan_payload_and_signed_zero_alias_only_when_exact_bytes_match(tmp_path):
    first_nan = np.array([0x7FF8000000000001], dtype=np.uint64).view(np.float64)
    same_nan = first_nan.copy()
    other_nan = np.array([0x7FF8000000000002], dtype=np.uint64).view(np.float64)
    negative_zero = np.array([-0.0], dtype=np.float64)
    same_negative_zero = negative_zero.copy()
    positive_zero = np.array([0.0], dtype=np.float64)
    arrays = {
        "nan-a": first_nan,
        "nan-a-copy": same_nan,
        "nan-b": other_nan,
        "negative-zero": negative_zero,
        "negative-zero-copy": same_negative_zero,
        "positive-zero": positive_zero,
    }
    path = tmp_path / "float-bits.h5"
    write_h5(path, {}, arrays)
    with h5py.File(path, "r") as stored:
        group = stored["arrays"]
        addresses = {
            key: _object_address(group[f"{index:08d}"])
            for index, key in enumerate(arrays)
        }
        assert addresses["nan-a"] == addresses["nan-a-copy"]
        assert addresses["nan-a"] != addresses["nan-b"]
        assert addresses["negative-zero"] == addresses["negative-zero-copy"]
        assert addresses["negative-zero"] != addresses["positive-zero"]
    with open_h5(path) as reader:
        for key, source in arrays.items():
            _same(reader.arrays[key], source)


def test_dtype_shape_bytes_and_stale_manifest_never_cause_aliasing(tmp_path):
    base = np.array([1, 2], dtype=np.int16)
    arrays = {
        "base": base,
        "same-bytes-different-dtype": base.astype(np.int32),
        "same-values-different-shape": base.reshape((1, 2)),
        "different-bytes": np.array([1, 3], dtype=np.int16),
    }
    # Caller metadata deliberately claims all arrays share one digest. The
    # writer must derive identity from the actual arrays, not these claims.
    manifest = {
        "arrays": {
            key: {"digest": "stale-shared-digest", "dtype": "<i2", "shape": [2]}
            for key in arrays
        }
    }
    destination = tmp_path / "not-shared.h5"

    write_h5(destination, manifest, arrays)

    with h5py.File(destination, "r") as stored:
        assert stored.attrs["schema_version"] == 1
        assert stored["manifest_json"].compression is None
        assert "array_keys_json" not in stored
        group = stored["arrays"]
        addresses = [_object_address(group[f"{index:08d}"]) for index in range(4)]
        assert len(set(addresses)) == len(addresses)
    with open_h5(destination) as reader:
        assert list(reader.arrays) == list(arrays)
        for key, source in arrays.items():
            _same(reader.arrays[key], source)


def test_alias_created_before_write_failure_is_removed_and_previous_file_survives(
    tmp_path, monkeypatch
):
    destination = tmp_path / "atomic.h5"
    write_h5(destination, {"version": 1}, {"old": np.arange(4)})
    original = destination.read_bytes()
    real_write = h5_store._write_dataset

    def fail_on_later_unique(group, index, key, array):
        if key == "failure":
            raise OSError("simulated write failure")
        return real_write(group, index, key, array)

    monkeypatch.setattr(h5_store, "_write_dataset", fail_on_later_unique)
    duplicate = np.arange(8, dtype=np.int32)
    with pytest.raises(OSError, match="simulated write failure"):
        write_h5(
            destination,
            {"version": 2},
            {"first": duplicate, "alias": duplicate.copy(), "failure": np.arange(2)},
        )
    monkeypatch.undo()
    assert destination.read_bytes() == original
    assert sorted(path.name for path in tmp_path.iterdir()) == ["atomic.h5"]


def test_key_table_malformed_is_named(tmp_path):
    path = tmp_path / "bad-index.h5"
    with h5py.File(path, "w") as stored:
        manifest = stored.create_dataset(
            "manifest_json",
            data=np.frombuffer(b"{}", dtype=np.uint8),
            compression="gzip",
            compression_opts=4,
            shuffle=True,
        )
        manifest.attrs["encoding"] = "gzip"
        stored.attrs["schema_version"] = 2
        group = stored.create_group("arrays")
        dataset = group.create_dataset("00000000", data=np.arange(2, dtype=np.int16))
        dataset.attrs["key"] = "a"
        dataset.attrs["dtype"] = np.dtype(np.int16).str
        key_table = stored.create_dataset(
            "array_keys_json",
            data=np.frombuffer(b'["a", "a"]', dtype=np.uint8),
            compression="gzip",
            compression_opts=4,
            shuffle=True,
        )
        key_table.attrs["encoding"] = "gzip"
    with (
        pytest.raises(MalformedH5Error, match="array key index is malformed"),
        open_h5(path),
    ):
        pass


def test_old_writer_product_without_version_is_read_as_v1(tmp_path):
    path = tmp_path / "old-v1.h5"
    source = {"first": np.arange(4, dtype=np.int16), "second": np.array([1.5])}
    # Independent legacy-format fixture: no current writer or private file.
    with h5py.File(path, "w") as stored:
        stored.create_dataset(
            "manifest_json",
            data=np.frombuffer(b'{"origin": "old writer"}', dtype=np.uint8),
        )
        group = stored.create_group("arrays")
        for index, (key, value) in enumerate(source.items()):
            dataset = group.create_dataset(f"{index:08d}", data=value)
            dataset.attrs["key"] = key
            dataset.attrs["dtype"] = value.dtype.str
    with h5py.File(path, "r") as stored:
        assert "schema_version" not in stored.attrs
        assert "array_keys_json" not in stored
    with open_h5(path) as reader:
        assert list(reader.arrays) == list(source)
        for key, value in source.items():
            _same(reader.arrays[key], value)


def test_unknown_schema_version_and_v2_without_key_table_are_refused(tmp_path):
    aliases = {"a": np.arange(3), "b": np.arange(3)}
    path = tmp_path / "versioned.h5"
    write_h5(path, {}, aliases)
    with h5py.File(path, "r+") as stored:
        stored.attrs["schema_version"] = 77
    with (
        pytest.raises(MalformedH5Error, match="unsupported H5 schema version"),
        open_h5(path),
    ):
        pass
    write_h5(path, {}, aliases)
    with h5py.File(path, "r+") as stored:
        del stored["array_keys_json"]
    with (
        pytest.raises(
            MalformedH5Error, match="schema version and array key table disagree"
        ),
        open_h5(path),
    ):
        pass


def test_v2_manifest_must_declare_compressed_json_encoding(tmp_path):
    path = tmp_path / "bad-manifest-encoding.h5"
    write_h5(path, {}, {"a": np.arange(3), "b": np.arange(3)})
    with h5py.File(path, "r+") as stored:
        stored["manifest_json"].attrs["encoding"] = "raw"
    with (
        pytest.raises(MalformedH5Error, match="v2 manifest encoding is unsupported"),
        open_h5(path),
    ):
        pass


def test_v2_key_table_must_declare_compressed_json_encoding(tmp_path):
    path = tmp_path / "bad-key-encoding.h5"
    write_h5(path, {}, {"a": np.arange(3), "b": np.arange(3)})
    with h5py.File(path, "r+") as stored:
        stored["array_keys_json"].attrs["encoding"] = "raw"
    with (
        pytest.raises(
            MalformedH5Error, match="v2 array key table encoding is unsupported"
        ),
        open_h5(path),
    ):
        pass
