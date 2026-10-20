from __future__ import annotations

import hashlib
import json
import lzma
from pathlib import Path

import numpy as np
import pytest

from knee.diagnosis.evidence import SourceEvidenceError, load_source, retain_source


def _source() -> dict:
    return {
        "study_uid": "study-1",
        "mode": "full",
        "metadata": {"ordered": ["first", "second"], "count": 3},
        "array": np.arange(12, dtype=np.int16).reshape(3, 4),
    }


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def test_writer_compresses_exact_canonical_manifest_and_hashes_stored_bytes(
    tmp_path: Path,
) -> None:
    source = _source()
    receipt = retain_source(tmp_path, "study-1", source)
    manifest_path = Path(receipt["manifest"])
    stored = manifest_path.read_bytes()

    assert manifest_path.name == "manifest.json.xz"
    assert stored.startswith(b"\xfd7zXZ\x00")
    decoded = lzma.decompress(stored)
    manifest = json.loads(decoded)
    assert decoded == _canonical(manifest)
    assert receipt["sha256"] == hashlib.sha256(stored).hexdigest()
    assert receipt["archive_sha256"] == manifest["archive_sha256"]
    restored = load_source(manifest_path)
    assert restored["manifest_sha256"] == hashlib.sha256(stored).hexdigest()
    np.testing.assert_array_equal(restored["source"]["array"], source["array"])
    assert restored["source"]["metadata"] == source["metadata"]


def test_compressed_source_resolves_from_logical_json_path_and_directory(
    tmp_path: Path,
) -> None:
    receipt = retain_source(tmp_path, "study-1", _source())
    manifest_path = Path(receipt["manifest"])
    directory = manifest_path.parent

    from_logical_path = load_source(directory / "manifest.json")
    from_directory = load_source(directory)
    from_actual_path = load_source(manifest_path)

    assert (
        from_logical_path["source"]["metadata"]
        == from_actual_path["source"]["metadata"]
    )
    assert from_directory["manifest_sha256"] == from_actual_path["manifest_sha256"]
    np.testing.assert_array_equal(
        from_logical_path["source"]["array"], from_actual_path["source"]["array"]
    )


def test_legacy_plain_manifest_remains_readable_from_file_and_directory(
    tmp_path: Path,
) -> None:
    receipt = retain_source(tmp_path / "compressed", "study-1", _source())
    compressed_path = Path(receipt["manifest"])
    legacy = tmp_path / "legacy" / "study-1"
    legacy.mkdir(parents=True)
    plain_bytes = lzma.decompress(compressed_path.read_bytes())
    (legacy / "manifest.json").write_bytes(plain_bytes)
    (legacy / "arrays.npz").write_bytes(
        (compressed_path.parent / "arrays.npz").read_bytes()
    )

    by_file = load_source(legacy / "manifest.json")
    by_directory = load_source(legacy)

    assert by_file["manifest_sha256"] == hashlib.sha256(plain_bytes).hexdigest()
    assert by_directory["manifest_sha256"] == by_file["manifest_sha256"]
    assert by_file["source"]["metadata"] == _source()["metadata"]
    np.testing.assert_array_equal(by_directory["source"]["array"], _source()["array"])


def test_malformed_xz_and_invalid_decompressed_json_are_named(tmp_path: Path) -> None:
    directory = tmp_path / "sources" / "broken"
    directory.mkdir(parents=True)
    (directory / "manifest.json.xz").write_bytes(b"not an XZ stream")
    with pytest.raises(SourceEvidenceError, match="source_manifest_invalid"):
        load_source(directory)

    (directory / "manifest.json.xz").write_bytes(lzma.compress(b"not JSON", preset=6))
    with pytest.raises(SourceEvidenceError, match="source_manifest_invalid"):
        load_source(directory / "manifest.json.xz")


def test_publication_is_immutable_and_keeps_the_first_compressed_bytes(
    tmp_path: Path,
) -> None:
    first = retain_source(tmp_path, "study-1", _source())
    manifest_path = Path(first["manifest"])
    original = manifest_path.read_bytes()

    with pytest.raises(SourceEvidenceError, match="already_exists"):
        retain_source(tmp_path, "study-1", {"study_uid": "study-1", "other": True})

    assert manifest_path.read_bytes() == original
    assert sorted(path.name for path in manifest_path.parent.iterdir()) == [
        "arrays.npz",
        "manifest.json.xz",
    ]
