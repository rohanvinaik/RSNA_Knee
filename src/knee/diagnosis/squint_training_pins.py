"""Content pins for bounded, resumable local training work.

Expected files come from a trusted extraction/download inventory, never from the
subset currently present on disk. Cached file digests avoid rereading unchanged
studies; a changed size/mtime/ctime forces a fresh content check. This is an input
identity, not an anatomical, identity or diagnosis decision.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import tempfile
import zipfile
import zlib
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from pathlib import Path, PurePosixPath
from typing import Any

from knee.study.tables import read_series_rows

SOURCE_SCHEMA = "knee.squint-training-source/v1"
STUDY_SCHEMA = "knee.squint-training-study-input/v1"
CACHE_SCHEMA = "knee.squint-training-study-digest-cache/v1"
_RUNTIME_PACKAGES = (
    "numpy",
    "scipy",
    "scikit-image",
    "pydicom",
    "pylibjpeg",
    "python-gdcm",
    "numba",
    "h5py",
)
_RUNNER_NAMES = (
    "prepare_squint_training.py",
    "squint_training_round.py",
    "squint_round_composition.py",
    "evaluate_squint_capacity.py",
    "squint_object_bootstrap.py",
    "publish_visual_cases.py",
)


class TrainingPinError(ValueError):
    """A named input-identity or readiness refusal."""


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _runtime_identity() -> dict[str, Any]:
    versions = {}
    for name in _RUNTIME_PACKAGES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "machine": platform.machine(),
        "system": platform.system(),
        "packages": versions,
    }


def training_source_identity(
    repository: Path,
    *,
    reference_files: Mapping[str, Path] | None = None,
    environment: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Pin the existing broad producer scope, runners, lock and runtime.

    The source collection extends the report-round producer scope to the whole
    knee package so profile, anchor, decoding and object-writer changes cannot be
    omitted by an imported-module shortlist. Only source/config files are read.
    Explicit external writer/reference files can be added by their stable names.
    """
    repository = repository.resolve()
    package = repository / "src" / "knee"
    if not package.is_dir():
        raise TrainingPinError("training_source_missing:knee")
    paths = {
        str(path.relative_to(repository)): path
        for path in package.rglob("*.py")
        if not any(part.startswith(".") for part in path.relative_to(package).parts)
        and "__pycache__" not in path.parts
    }
    for name in _RUNNER_NAMES:
        path = repository / "scripts" / name
        if path.is_file():
            paths[str(path.relative_to(repository))] = path
    for name in ("pyproject.toml", "uv.lock"):
        path = repository / name
        if not path.is_file():
            raise TrainingPinError("training_source_missing:" + name)
        paths[name] = path
    for name, path in (reference_files or {}).items():
        if not isinstance(name, str) or not name:
            raise TrainingPinError("training_reference_name_invalid")
        paths["references/" + name] = path
    try:
        files = {name: _file_digest(path) for name, path in sorted(paths.items())}
    except OSError as error:
        raise TrainingPinError("training_source_unreadable") from error
    result = {
        "schema": SOURCE_SCHEMA,
        "files": files,
        "environment": dict(environment)
        if environment is not None
        else _runtime_identity(),
    }
    return {**result, "sha256": _digest(result)}


def archive_study_inventory(
    archive: Path, study_uids: Sequence[str], *, split: str = "train"
) -> dict[str, dict[str, dict[str, int]]]:
    """Read expected selected-study paths/sizes/CRCs from the ZIP directory only.

    This does not extract files or read the archived image bytes. The source ZIP
    must be the trusted competition download/extraction source for these studies.
    """
    if split not in ("train", "test"):
        raise TrainingPinError("study_split_invalid")
    requested = set(study_uids)
    if not requested or any(not _uid_valid(uid) for uid in requested):
        raise TrainingPinError("study_uid_invalid")
    inventories: dict[str, dict[str, dict[str, int]]] = {uid: {} for uid in requested}
    try:
        with zipfile.ZipFile(archive) as source:
            for item in source.infolist():
                parts = PurePosixPath(item.filename).parts
                if (
                    item.is_dir()
                    or len(parts) < 4
                    or parts[-4] != split + "_series"
                    or parts[-3] not in requested
                    or not parts[-1].endswith(".dcm")
                ):
                    continue
                uid = parts[-3]
                relative = "/".join(parts[-2:])
                if relative in inventories[uid]:
                    raise TrainingPinError("study_inventory_duplicate:" + uid)
                inventories[uid][relative] = {
                    "size": item.file_size,
                    "crc32": item.CRC,
                }
    except (OSError, zipfile.BadZipFile) as error:
        raise TrainingPinError("study_inventory_unreadable") from error
    for uid, files in inventories.items():
        if not files:
            raise TrainingPinError("study_readiness_unknown:" + uid)
    return inventories


def _uid_valid(uid: Any) -> bool:
    return (
        isinstance(uid, str)
        and bool(uid)
        and uid not in (".", "..")
        and Path(uid).name == uid
    )


def _expected_files(expected: Any, uid: str) -> dict[str, dict[str, Any]]:
    if expected is None:
        raise TrainingPinError("study_readiness_unknown:" + uid)
    if not isinstance(expected, Mapping) or not expected:
        raise TrainingPinError("study_inventory_invalid:" + uid)
    result = {}
    for name, metadata in expected.items():
        parts = PurePosixPath(name).parts if isinstance(name, str) else ()
        if (
            len(parts) != 2
            or any(part in (".", "..", "/") for part in parts)
            or not parts[-1].endswith(".dcm")
            or not isinstance(metadata, Mapping)
            or type(metadata.get("size")) is not int
            or metadata["size"] <= 0
        ):
            raise TrainingPinError("study_inventory_invalid:" + uid)
        crc = metadata.get("crc32")
        sha = metadata.get("sha256")
        if crc is not None and (type(crc) is not int or not 0 <= crc <= 0xFFFFFFFF):
            raise TrainingPinError("study_inventory_invalid:" + uid)
        if sha is not None and not _sha_valid(sha):
            raise TrainingPinError("study_inventory_invalid:" + uid)
        result[name] = dict(metadata)
    return result


def _fingerprint(path: Path) -> dict[str, int]:
    stat = path.stat()
    return {
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "ctime_ns": stat.st_ctime_ns,
    }


def _read_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise TrainingPinError("study_cache_invalid") from error
    if (
        not isinstance(value, dict)
        or value.get("schema") != CACHE_SCHEMA
        or not isinstance(value.get("files"), dict)
        or value.get("sha256")
        != _digest({k: v for k, v in value.items() if k != "sha256"})
    ):
        raise TrainingPinError("study_cache_invalid")
    return value["files"]


def _write_cache(path: Path, files: Mapping[str, Any]) -> None:
    value = {"schema": CACHE_SCHEMA, "files": dict(files)}
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump({**value, "sha256": _digest(value)}, stream, sort_keys=True)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _read_digest(path: Path) -> dict[str, Any]:
    sha = hashlib.sha256()
    crc = 0
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            sha.update(block)
            crc = zlib.crc32(block, crc)
    return {"sha256": sha.hexdigest(), "crc32": crc & 0xFFFFFFFF}


def _series_metadata(root: Path, study_uid: str, split: str) -> list[dict[str, Any]]:
    try:
        rows = read_series_rows(root / (split + "_series.csv"))
    except (OSError, ValueError, KeyError) as error:
        raise TrainingPinError("study_series_metadata_invalid:" + study_uid) from error
    selected = [asdict(row) for row in rows if row.study_uid == study_uid]
    if not selected:
        raise TrainingPinError("study_series_metadata_missing:" + study_uid)
    return selected


def verified_study_input(
    root: Path,
    study_uid: str,
    *,
    expected_files: Mapping[str, Mapping[str, Any]] | None,
    cache_directory: Path,
    split: str = "train",
) -> dict[str, Any]:
    """Pin one complete selected study, reusing unchanged verified file digests.

    Completion is relative to ``expected_files`` supplied by the extraction or
    download source. A current directory listing cannot substitute for it.
    """
    if not _uid_valid(study_uid):
        raise TrainingPinError("study_uid_invalid")
    if split not in ("train", "test"):
        raise TrainingPinError("study_split_invalid")
    expected = _expected_files(expected_files, study_uid)
    study = root / (split + "_series") / study_uid
    if study.is_symlink():
        raise TrainingPinError("study_file_invalid:" + study_uid)
    series_metadata = _series_metadata(root, study_uid, split)
    present = {
        str(path.relative_to(study)): path
        for path in study.glob("*/*.dcm")
        if not path.name.startswith("._")
    }
    if set(expected) - set(present):
        raise TrainingPinError("study_incomplete:" + study_uid)
    if set(present) - set(expected):
        raise TrainingPinError("study_inventory_mismatch:" + study_uid)
    cache_path = cache_directory / f"{split}-{study_uid}.json"
    cached = _read_cache(cache_path)
    updated = {}
    files = {}
    for name, specification in sorted(expected.items()):
        path = present[name]
        if path.is_symlink() or path.parent.is_symlink() or not path.is_file():
            raise TrainingPinError("study_file_invalid:" + study_uid)
        before = _fingerprint(path)
        if before["size"] != specification["size"]:
            raise TrainingPinError("study_incomplete:" + study_uid)
        previous = cached.get(name, {})
        if isinstance(previous, Mapping) and previous.get("fingerprint") == before:
            measured = previous.get("content", {})
            if not isinstance(measured, Mapping) or not _sha_valid(
                measured.get("sha256")
            ):
                raise TrainingPinError("study_cache_invalid")
            measured = dict(measured)
        else:
            measured = _read_digest(path)
        if _fingerprint(path) != before:
            raise TrainingPinError("study_changed_during_read:" + study_uid)
        for key in ("crc32", "sha256"):
            if key in specification and measured.get(key) != specification[key]:
                raise TrainingPinError("study_content_mismatch:" + study_uid)
        content = {"size": before["size"], **measured}
        files[name] = content
        updated[name] = {"fingerprint": before, "content": measured}
    final_files = {
        str(path.relative_to(study))
        for path in study.glob("*/*.dcm")
        if not path.name.startswith("._")
    }
    if final_files != set(present):
        raise TrainingPinError("study_changed_during_read:" + study_uid)
    if _series_metadata(root, study_uid, split) != series_metadata:
        raise TrainingPinError("study_changed_during_read:" + study_uid)
    _write_cache(cache_path, updated)
    value = {
        "schema": STUDY_SCHEMA,
        "study_uid": study_uid,
        "split": split,
        "series_metadata": series_metadata,
        "files": files,
    }
    return {**value, "sha256": _digest(value)}


def _sha_valid(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(c in "0123456789abcdef" for c in value)
    )


def checkpoint_identity_code(expected: dict, actual: dict) -> str:
    """Classify checkpoint pins without collapsing distinct repair actions.

    Source changes require a fresh code-epoch output root. Changed study bytes
    require new observation work. Other changed context includes parent, scope
    and record digest. An unread/malformed pin never authorizes reuse.
    """
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        return "checkpoint_pin_invalid"
    for pin in (expected, actual):
        if (
            not isinstance(pin.get("code"), dict)
            or not _sha_valid(pin["code"].get("sha256"))
            or not isinstance(pin.get("study_input"), dict)
            or not _sha_valid(pin["study_input"].get("sha256"))
        ):
            return "checkpoint_pin_invalid"
    if expected["code"] != actual["code"]:
        return "checkpoint_source_changed"
    if expected["study_input"] != actual["study_input"]:
        return "checkpoint_study_changed"
    if expected != actual:
        return "checkpoint_context_changed"
    return "checkpoint_pin_identical"
