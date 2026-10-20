"""Lossless, non-pickle persistence for one acquired diagnostic source."""

from __future__ import annotations

import dataclasses
import enum
import hashlib
import json
import lzma
import math
import os
import re
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from knee.encoding.counts import BankLayout, CountBundle, CountLayout
from knee.json_store import resolve_json_path

_SCHEMA = "knee.diagnostic-source-evidence/v1"
_SAFE_UID = re.compile(r"^[A-Za-z0-9._-]+$")


class SourceEvidenceError(ValueError):
    """A named malformed or unsupported source-evidence value."""


def _array_identity(array: np.ndarray) -> tuple[str, str]:
    if array.dtype.hasobject:
        raise SourceEvidenceError("object_dtype_array_unsupported")
    dtype_description = array.dtype.descr if array.dtype.fields else array.dtype.str
    dtype_json = json.dumps(
        dtype_description, ensure_ascii=False, separators=(",", ":")
    )
    digest = hashlib.sha256()
    digest.update(dtype_json.encode("utf-8"))
    digest.update(json.dumps(list(array.shape), separators=(",", ":")).encode("ascii"))
    digest.update(np.ascontiguousarray(array).tobytes(order="C"))
    return digest.hexdigest(), dtype_json


def _layout_record(layout: CountLayout) -> dict[str, Any]:
    if not isinstance(layout, CountLayout) or not isinstance(layout.banks, tuple):
        raise SourceEvidenceError("count_layout_invalid")
    if not layout.layout_id or not layout.carrier_id or not layout.banks:
        raise SourceEvidenceError("count_layout_identity_invalid")
    banks = []
    names: set[str] = set()
    for bank in layout.banks:
        if not isinstance(bank, BankLayout) or not bank.name or bank.name in names:
            raise SourceEvidenceError("count_layout_bank_invalid")
        if type(bank.row_count) is not int or bank.row_count <= 0:
            raise SourceEvidenceError("count_layout_row_count_invalid")
        names.add(bank.name)
        banks.append({"name": bank.name, "row_count": bank.row_count})
    return {
        "layout_id": layout.layout_id,
        "carrier_id": layout.carrier_id,
        "banks": banks,
    }


def _count_bundle_record(
    bundle: CountBundle, layouts: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    if not isinstance(bundle, CountBundle):
        raise SourceEvidenceError("count_bundle_invalid")
    layout = _layout_record(bundle.layout)
    layout_key = hashlib.sha256(_canonical(layout)).hexdigest()
    existing = layouts.setdefault(layout_key, layout)
    if existing != layout:
        raise SourceEvidenceError("count_layout_digest_collision")
    if not isinstance(bundle.counts, tuple) or len(bundle.counts) != len(
        bundle.layout.banks
    ):
        raise SourceEvidenceError("count_bundle_bank_shape_invalid")
    rows: list[list[str | int]] = []
    for bank_index, (counts, bank) in enumerate(
        zip(bundle.counts, bundle.layout.banks, strict=True)
    ):
        if not isinstance(counts, tuple) or len(counts) != bank.row_count:
            raise SourceEvidenceError(f"count_bundle_row_shape_invalid:{bank.name}")
        for row_index, value in enumerate(counts):
            if type(value) is not int or value < 0:
                raise SourceEvidenceError(
                    f"count_bundle_count_invalid:{bank.name}:{row_index}"
                )
            if value:
                rows.append([bank_index, row_index, str(value)])
    return {
        "$record_type": "knee.encoding.counts.CountBundle",
        "layout_ref": layout_key,
        "bank_count": len(bundle.layout.banks),
        "sparse_rows": rows,
    }


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _matches_profile_counts(source: dict[str, Any]) -> bool:
    profiles = source.get("profiles")
    profile_counts = source.get("profile_counts")
    if profiles is None or profile_counts is None:
        return False
    if not isinstance(profiles, (tuple, list)) or not isinstance(
        profile_counts, (tuple, list)
    ):
        raise SourceEvidenceError("profile_counts_shape_invalid")
    if len(profiles) != len(profile_counts):
        raise SourceEvidenceError("profile_counts_profile_length_mismatch")
    for index, (profile, counts) in enumerate(
        zip(profiles, profile_counts, strict=True)
    ):
        bundle = getattr(profile, "bundle", None)
        if not isinstance(bundle, CountBundle) or counts != bundle.counts:
            raise SourceEvidenceError(f"profile_counts_mismatch:{index}")
    return True


def _encode(
    value: Any, arrays: dict[str, np.ndarray], layouts: dict[str, dict[str, Any]]
) -> Any:
    if isinstance(value, Path):
        return {"$path": str(value)}
    if isinstance(value, np.ndarray):
        digest, dtype_json = _array_identity(value)
        name = "a_" + digest
        prior = arrays.setdefault(name, np.ascontiguousarray(value).copy())
        prior_digest, prior_dtype = _array_identity(prior)
        if (
            prior_digest != digest
            or prior_dtype != dtype_json
            or prior.shape != value.shape
        ):
            raise SourceEvidenceError("array_digest_collision")
        return {"$array": name, "dtype": dtype_json, "shape": list(value.shape)}
    if isinstance(value, CountBundle):
        return _count_bundle_record(value, layouts)
    if isinstance(value, enum.Enum):
        return {
            "$enum_type": f"{type(value).__module__}.{type(value).__qualname__}",
            "value": _encode(value.value, arrays, layouts),
        }
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        fields = {
            field.name: _encode(getattr(value, field.name), arrays, layouts)
            for field in dataclasses.fields(value)
        }
        return {
            "$record_type": f"{type(value).__module__}.{type(value).__qualname__}",
            "fields": fields,
        }
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            return {
                "$mapping": [
                    [_encode(key, arrays, layouts), _encode(item, arrays, layouts)]
                    for key, item in value.items()
                ]
            }
        return {key: _encode(item, arrays, layouts) for key, item in value.items()}
    if isinstance(value, tuple):
        return {"$tuple": [_encode(item, arrays, layouts) for item in value]}
    if isinstance(value, list):
        return [_encode(item, arrays, layouts) for item in value]
    if value is None or isinstance(value, (str, bool)) or type(value) is int:
        return value
    if type(value) is float:
        if math.isfinite(value):
            return value
        return {
            "$float": "nan" if math.isnan(value) else ("+inf" if value > 0 else "-inf")
        }
    raise SourceEvidenceError(
        f"unsupported_source_value:{type(value).__module__}.{type(value).__qualname__}"
    )


def _decode(value: Any, arrays: dict[str, np.ndarray], layouts: dict[str, Any]) -> Any:
    if isinstance(value, list):
        return [_decode(item, arrays, layouts) for item in value]
    if not isinstance(value, dict):
        return value
    if "$array" in value:
        name = value["$array"]
        array = arrays.get(name)
        if array is None or list(array.shape) != value.get("shape"):
            raise SourceEvidenceError(f"array_reference_invalid:{name}")
        digest, dtype_json = _array_identity(array)
        if name != "a_" + digest or dtype_json != value.get("dtype"):
            raise SourceEvidenceError(f"array_reference_digest_mismatch:{name}")
        return array
    if "$path" in value:
        return Path(value["$path"])
    if "$record_type" in value:
        if value["$record_type"] == "knee.encoding.counts.CountBundle":
            layout_key = value.get("layout_ref")
            if layout_key not in layouts:
                raise SourceEvidenceError("count_layout_reference_missing")
            return {
                "$record_type": value["$record_type"],
                "layout": layouts[layout_key],
                "bank_count": value["bank_count"],
                "sparse_rows": value["sparse_rows"],
            }
        return {
            "$record_type": value["$record_type"],
            "fields": _decode(value.get("fields", {}), arrays, layouts),
        }
    if "$enum_type" in value:
        return {
            "$enum_type": value["$enum_type"],
            "value": _decode(value.get("value"), arrays, layouts),
        }
    if "$tuple" in value:
        return tuple(_decode(item, arrays, layouts) for item in value["$tuple"])
    if "$mapping" in value:
        return {
            _decode(key, arrays, layouts): _decode(item, arrays, layouts)
            for key, item in value["$mapping"]
        }
    if "$float" in value:
        return {"nan": float("nan"), "+inf": float("inf"), "-inf": float("-inf")}[
            value["$float"]
        ]
    return {key: _decode(item, arrays, layouts) for key, item in value.items()}


def retain_source(output: Path, study_uid: str, source: dict) -> dict:
    """Atomically retain a source as typed XZ-compressed JSON plus exact arrays."""
    if not isinstance(output, Path):
        raise SourceEvidenceError("output_path_required")
    if (
        not isinstance(study_uid, str)
        or not _SAFE_UID.fullmatch(study_uid)
        or study_uid in (".", "..")
    ):
        raise SourceEvidenceError("unsafe_study_uid")
    if not isinstance(source, dict):
        raise SourceEvidenceError("source_dict_required")
    if source.get("study_uid", study_uid) != study_uid:
        raise SourceEvidenceError("source_study_uid_mismatch")
    output = output.resolve()
    layouts: dict[str, dict[str, Any]] = {}
    arrays: dict[str, np.ndarray] = {}
    source_copy = dict(source)
    duplicate_counts = _matches_profile_counts(source_copy)
    if duplicate_counts:
        source_copy.pop("profile_counts")
        source_copy["profile_counts"] = {"$duplicate_of": "profiles[*].bundle.counts"}
    encoded_source = _encode(source_copy, arrays, layouts)
    manifest = {
        "schema": _SCHEMA,
        "study_uid": study_uid,
        "source": encoded_source,
        "layouts": layouts,
        "arrays": {
            name: {"shape": list(array.shape), "dtype": _array_identity(array)[1]}
            for name, array in sorted(arrays.items())
        },
        "archive": "arrays.npz",
    }
    root = output / "sources"
    root.mkdir(parents=True, exist_ok=True)
    destination = root / study_uid
    if destination.exists():
        raise SourceEvidenceError(f"source_evidence_already_exists:{destination}")
    temporary = Path(tempfile.mkdtemp(prefix=f".{study_uid}.", dir=root))
    try:
        archive_path = temporary / "arrays.npz"
        np.savez(archive_path, **arrays)
        with archive_path.open("rb") as stream:
            os.fsync(stream.fileno())
        archive_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        manifest["archive_sha256"] = archive_hash
        manifest_bytes = _canonical(manifest)
        stored_manifest_bytes = lzma.compress(manifest_bytes, preset=6)
        manifest_path = temporary / "manifest.json.xz"
        with manifest_path.open("xb") as stream:
            stream.write(stored_manifest_bytes)
            stream.flush()
            os.fsync(stream.fileno())
        directory_fd = os.open(temporary, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        if destination.exists():
            raise SourceEvidenceError(f"source_evidence_already_exists:{destination}")
        os.replace(temporary, destination)
        parent_fd = os.open(root, os.O_RDONLY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    except Exception:
        if temporary.exists():
            import shutil

            shutil.rmtree(temporary)
        raise
    return {
        "manifest": str(destination / "manifest.json.xz"),
        "sha256": hashlib.sha256(stored_manifest_bytes).hexdigest(),
        "archive_sha256": archive_hash,
        "study_uid": study_uid,
    }


def load_source(path: Path) -> dict:
    """Load and verify one retained source; records remain explicitly typed maps."""
    requested = Path(path)
    manifest_path = requested / "manifest.json" if requested.is_dir() else requested
    manifest_path = resolve_json_path(manifest_path)
    if not manifest_path.is_file():
        raise SourceEvidenceError("source_manifest_missing")
    try:
        stored_manifest_bytes = manifest_path.read_bytes()
        if manifest_path.name.endswith(".json.xz"):
            manifest_bytes = lzma.decompress(stored_manifest_bytes)
        else:
            manifest_bytes = stored_manifest_bytes
        manifest = json.loads(manifest_bytes)
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        lzma.LZMAError,
        EOFError,
    ) as error:
        raise SourceEvidenceError("source_manifest_invalid") from error
    if manifest.get("schema") != _SCHEMA:
        raise SourceEvidenceError("source_manifest_schema_invalid")
    study_uid = manifest.get("study_uid")
    if (
        not isinstance(study_uid, str)
        or not _SAFE_UID.fullmatch(study_uid)
        or study_uid in (".", "..")
    ):
        raise SourceEvidenceError("source_manifest_study_uid_invalid")
    if manifest.get("archive") != "arrays.npz":
        raise SourceEvidenceError("source_archive_name_invalid")
    archive_path = manifest_path.parent / "arrays.npz"
    try:
        archive_bytes = archive_path.read_bytes()
    except OSError as error:
        raise SourceEvidenceError("source_archive_missing") from error
    if hashlib.sha256(archive_bytes).hexdigest() != manifest.get("archive_sha256"):
        raise SourceEvidenceError("source_archive_digest_mismatch")
    try:
        with np.load(archive_path, allow_pickle=False) as archive:
            arrays = {name: archive[name].copy() for name in archive.files}
    except (OSError, ValueError) as error:
        raise SourceEvidenceError("source_archive_invalid") from error
    for name, item in manifest.get("arrays", {}).items():
        if (
            name not in arrays
            or list(arrays[name].shape) != item.get("shape")
            or _array_identity(arrays[name])[1] != item.get("dtype")
        ):
            raise SourceEvidenceError(f"source_array_metadata_mismatch:{name}")
    source = _decode(manifest.get("source"), arrays, manifest.get("layouts", {}))
    if isinstance(source, dict) and source.get("profile_counts") == {
        "$duplicate_of": "profiles[*].bundle.counts"
    }:
        profiles = source.get("profiles", ())
        restored = []
        for profile in profiles:
            bundle = profile["fields"]["bundle"]
            layout = bundle["layout"]
            banks = [[0] * bank["row_count"] for bank in layout["banks"]]
            for bank_index, row_index, count in bundle["sparse_rows"]:
                banks[bank_index][row_index] = int(count)
            restored.append(tuple(tuple(bank) for bank in banks))
        source["profile_counts"] = tuple(restored)
    return {
        "schema": _SCHEMA,
        "study_uid": manifest["study_uid"],
        "source": source,
        "manifest_sha256": hashlib.sha256(stored_manifest_bytes).hexdigest(),
        "archive_sha256": manifest["archive_sha256"],
    }
