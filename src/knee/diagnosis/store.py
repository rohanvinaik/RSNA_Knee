"""Immutable, exact persistence for individual diagnostic cases.

The JSON manifest carries source and decision metadata.  Count rows live in a
non-pickle NPZ archive as canonical decimal strings so Python integers are not
rounded or narrowed by a fixed-width numeric dtype.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

from knee.diagnosis.models import Call, Case, Censor, Profile, Snapshot, Trust
from knee.encoding.counts import BankLayout, CountBundle, CountLayout

_STORE_SCHEMA = "knee.diagnostic-store/v1"
_ARCHIVE_SCHEMA = "knee.diagnostic-counts/v2-sparse"
_ENCODING = {
    "archive_format": "npz-npy-v1",
    "count_format": "sparse-addressed-canonical-base10-decimal-strings-v1",
    "layout_format": "distinct-complete-layout-table-v1",
    "integer_format": "arbitrary-precision-nonnegative-python-int",
    "pickle": False,
    "row_width": "layout-defined",
}
_ARCHIVE_FILE = "profiles.npz"


class StoreError(ValueError):
    """A store is invalid, malformed, corrupted, or already immutable."""


def _plain_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _pair_sequence(value: object) -> bool:
    if not isinstance(value, tuple):
        return False
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, tuple) or len(item) != 2:
            return False
        key, text = item
        if not _nonempty_text(key) or not isinstance(text, str) or key in seen:
            return False
        seen.add(key)
    return True


def _validated_sparse_row(values: object) -> tuple[tuple[int, int], ...] | None:
    """Check the entire immutable row before offering its nonzero entries."""
    if not isinstance(values, tuple):
        return None
    entries: list[tuple[int, int]] = []
    for index, value in enumerate(values):
        if not _plain_int(value) or value < 0:
            return None
        if value:
            entries.append((index, value))
    return tuple(entries)


def _count_decimal(value: int) -> str:
    """Canonical decimal without changing Python's process-wide digit limit."""
    try:
        return str(value)
    except ValueError:
        chunks: list[str] = []
        base = 10**512
        while value >= base:
            value, remainder = divmod(value, base)
            chunks.append(str(remainder).zfill(512))
        return str(value) + "".join(reversed(chunks))


def _parse_count_decimal(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        # Syntax is checked by the caller; chunks stay below the interpreter's
        # smallest configurable digit limit without modifying global settings.
        result = 0
        for start in range(0, len(value), 512):
            chunk = value[start : start + 512]
            result = result * 10 ** len(chunk) + int(chunk)
        return result


def _valid_layout(layout: object) -> bool:
    if not isinstance(layout, CountLayout):
        return False
    if not _nonempty_text(layout.layout_id) or not _nonempty_text(layout.carrier_id):
        return False
    if not isinstance(layout.banks, tuple) or not layout.banks:
        return False
    names: set[str] = set()
    for bank in layout.banks:
        if not isinstance(bank, BankLayout):
            return False
        if not _nonempty_text(bank.name) or bank.name in names:
            return False
        if not _plain_int(bank.row_count) or bank.row_count <= 0:
            return False
        names.add(bank.name)
    return True


def _zero_row(width: int) -> tuple[int, ...]:
    return (0,) * width


class _StoreReuse:
    """Held-reference identity reuse, owned by exactly one public operation.

    Row keys never hash their contents. A cache hit requires the original object
    still held here, and rows enter only after every value has been checked.
    Layout and bundle entries refer to the frozen exchange records.
    """

    def __init__(self) -> None:
        self.rows: dict[int, tuple[tuple[int, ...], tuple[tuple[int, int], ...]]] = {}
        self.serialized_rows: dict[
            int, tuple[tuple[int, ...], tuple[tuple[int, str], ...]]
        ] = {}
        self.layouts: dict[int, CountLayout] = {}
        self.bundles: dict[int, CountBundle] = {}
        self.zero_rows: dict[int, tuple[int, ...]] = {}
        self.templates: dict[int, tuple[CountLayout, tuple[tuple[int, ...], ...]]] = {}

    def sparse_row(self, values: object) -> tuple[tuple[int, int], ...] | None:
        if not isinstance(values, tuple):
            return None
        cached = self.rows.get(id(values))
        if cached is not None and cached[0] is values:
            return cached[1]
        entries = _validated_sparse_row(values)
        if entries is not None:
            self.rows[id(values)] = (values, entries)
        return entries

    def serialized_row(self, values: tuple[int, ...]) -> tuple[tuple[int, str], ...]:
        cached = self.serialized_rows.get(id(values))
        if cached is not None and cached[0] is values:
            return cached[1]
        entries = self.sparse_row(values)
        if entries is None:
            raise StoreError("invalid_profile_bundle")
        serialized = tuple((index, _count_decimal(value)) for index, value in entries)
        self.serialized_rows[id(values)] = (values, serialized)
        return serialized

    def empty_counts(self, layout: CountLayout) -> tuple[tuple[int, ...], ...]:
        cached = self.templates.get(id(layout))
        if cached is not None and cached[0] is layout:
            return cached[1]
        counts = []
        for bank in layout.banks:
            row = self.zero_rows.get(bank.row_count)
            if row is None:
                row = _zero_row(bank.row_count)
                self.zero_rows[bank.row_count] = row
            counts.append(row)
        template = tuple(counts)
        self.templates[id(layout)] = (layout, template)
        return template


def _valid_bundle(bundle: object, reuse: _StoreReuse | None = None) -> bool:
    if not isinstance(bundle, CountBundle):
        return False
    if reuse is None:
        reuse = _StoreReuse()
    if reuse.bundles.get(id(bundle)) is bundle:
        return True
    layout = bundle.layout
    if not isinstance(layout, CountLayout):
        return False
    if reuse.layouts.get(id(layout)) is not layout:
        if not _valid_layout(layout):
            return False
        reuse.layouts[id(layout)] = layout
    if not isinstance(bundle.counts, tuple) or len(bundle.counts) != len(layout.banks):
        return False
    for values, bank in zip(bundle.counts, layout.banks, strict=True):
        # Width belongs to the declared bank, even when this row was checked for
        # another bank. Sharing counts never establishes layout compatibility.
        if not isinstance(values, tuple) or len(values) != bank.row_count:
            return False
        if reuse.sparse_row(values) is None:
            return False
    reuse.bundles[id(bundle)] = bundle
    return True


def _valid_profile(profile: object, reuse: _StoreReuse | None = None) -> str | None:
    if not isinstance(profile, Profile):
        return "invalid_profile_type"
    for name in ("subject", "mode", "scope", "source_id"):
        if not _nonempty_text(getattr(profile, name, None)):
            return "invalid_profile_identity"
    if not _valid_bundle(profile.bundle, reuse):
        return "invalid_profile_bundle"
    if not _pair_sequence(profile.context):
        return "invalid_profile_context"
    if not _pair_sequence(profile.bank_statuses):
        return "invalid_profile_bank_statuses"
    if not _pair_sequence(profile.provenance):
        return "invalid_profile_provenance"
    return None


def validate_case(case: Case) -> str:
    """Return ``valid`` or a stable, named reason for an invalid case.

    A zero digit is retained as an explicit abstention.  It is not rewritten
    to a negative call, and an all-zero case remains a ledger case only.
    """
    return _validate_case(case, _StoreReuse())


def _validate_case(case: Case, reuse: _StoreReuse) -> str:
    if not isinstance(case, Case):
        return "invalid_case_type"
    if not _nonempty_text(case.case_id):
        return "invalid_case_id"
    if not _nonempty_text(case.study_uid):
        return "invalid_study_uid"
    profile_error = _valid_profile(case.profile, reuse)
    if profile_error is not None:
        return profile_error
    if not isinstance(case.calls, tuple):
        return "invalid_calls_container"
    if not _nonempty_text(case.teaching_revision):
        return "invalid_teaching_revision"
    questions: set[str] = set()
    for call in case.calls:
        if not isinstance(call, Call):
            return "invalid_call_type"
        if not _nonempty_text(call.question):
            return "invalid_call_question"
        if call.question in questions:
            return "duplicate_call_question"
        questions.add(call.question)
        if not _plain_int(call.digit) or call.digit not in (-1, 0, 1):
            return "invalid_call_digit"
        if not _nonempty_text(call.source):
            return "invalid_call_source"
        if not isinstance(call.words, str):
            return "invalid_call_words"
    return "valid"


def _validate_snapshot(snapshot: object, reuse: _StoreReuse | None = None) -> None:
    if reuse is None:
        reuse = _StoreReuse()
    if not isinstance(snapshot, Snapshot):
        raise StoreError("invalid_snapshot_type")
    if not _nonempty_text(snapshot.revision):
        raise StoreError("invalid_snapshot_revision")
    if not _nonempty_text(snapshot.schema_version):
        raise StoreError("invalid_snapshot_schema_version")
    if not isinstance(snapshot.cases, tuple):
        raise StoreError("invalid_cases_container")
    case_ids: set[str] = set()
    for case in snapshot.cases:
        reason = _validate_case(case, reuse)
        if reason != "valid":
            raise StoreError(reason)
        if case.case_id in case_ids:
            raise StoreError("duplicate_case_id")
        case_ids.add(case.case_id)
    if not isinstance(snapshot.trust, tuple):
        raise StoreError("invalid_trust_container")
    trust_keys: set[tuple[str, str]] = set()
    for item in snapshot.trust:
        if not isinstance(item, Trust):
            raise StoreError("invalid_trust_record")
        if not _nonempty_text(item.case_id) or item.case_id not in case_ids:
            raise StoreError("unknown_trust_case")
        if not _nonempty_text(item.question) or not _nonempty_text(item.source):
            raise StoreError("invalid_trust_identity")
        key = (item.case_id, item.question)
        if key in trust_keys:
            raise StoreError("duplicate_trust_record")
        trust_keys.add(key)
        if (
            not _plain_int(item.numerator)
            or not _plain_int(item.denominator)
            or item.denominator <= 0
            or item.numerator < 0
            or item.numerator > item.denominator
        ):
            raise StoreError("invalid_trust_fraction")
    if not isinstance(snapshot.censors, tuple):
        raise StoreError("invalid_censors_container")
    censor_ids: set[str] = set()
    for item in snapshot.censors:
        if not isinstance(item, Censor):
            raise StoreError("invalid_censor_record")
        if not _nonempty_text(item.censor_id) or item.censor_id in censor_ids:
            raise StoreError("duplicate_or_invalid_censor_id")
        censor_ids.add(item.censor_id)
        if not _nonempty_text(item.question) or not _nonempty_text(item.source):
            raise StoreError("invalid_censor_identity")
        if not _plain_int(item.answer) or item.answer not in (-1, 1):
            raise StoreError("invalid_censor_answer")
        if _valid_profile(item.profile, reuse) is not None:
            raise StoreError("invalid_censor_profile")
        if (
            not _plain_int(item.numerator)
            or not _plain_int(item.denominator)
            or item.denominator <= 0
            or item.numerator < 0
            or item.numerator > item.denominator
        ):
            raise StoreError("invalid_censor_fraction")


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class _MetadataStringTable:
    """One-operation interner for exact strings and ordered string pairs."""

    schema = "knee.diagnostic-metadata-string-table/v1"

    def __init__(self) -> None:
        self.ids: dict[str, int] = {}
        self.values: list[str] = []
        self.pair_ids: dict[tuple[int, int], int] = {}
        self.pair_values: list[tuple[int, int]] = []

    def reference(self, value: str) -> int:
        index = self.ids.get(value)
        if index is not None:
            return index
        index = len(self.values)
        self.ids[value] = index
        self.values.append(value)
        return index

    def pair_reference(self, key: str, value: str) -> int:
        pair = (self.reference(key), self.reference(value))
        index = self.pair_ids.get(pair)
        if index is not None:
            return index
        index = len(self.pair_values)
        self.pair_ids[pair] = index
        self.pair_values.append(pair)
        return index


def _metadata_strings(
    manifest: dict[str, Any],
) -> tuple[list[str], list[tuple[int, int]]] | None:
    if "metadata_encoding" not in manifest:
        return None
    encoded = manifest.get("metadata_encoding")
    _require(isinstance(encoded, dict), "invalid_metadata_string_table")
    _require(
        encoded.get("schema") == _MetadataStringTable.schema,
        "unsupported_metadata_string_table",
    )
    values = encoded.get("strings")
    _require(
        isinstance(values, list) and all(isinstance(item, str) for item in values),
        "invalid_metadata_string_table",
    )
    _require(len(set(values)) == len(values), "duplicate_metadata_string")
    raw_pairs = encoded.get("pairs")
    _require(isinstance(raw_pairs, list), "invalid_metadata_pair_table")
    pairs: list[tuple[int, int]] = []
    for pair in raw_pairs:
        _require(
            isinstance(pair, list)
            and len(pair) == 2
            and all(type(index) is int and 0 <= index < len(values) for index in pair),
            "invalid_metadata_pair_table",
        )
        pairs.append((pair[0], pair[1]))
    _require(len(set(pairs)) == len(pairs), "duplicate_metadata_pair")
    return values, pairs


def _metadata_text(value: object, strings: list[str] | None, reason: str) -> str:
    if strings is None:
        _require(isinstance(value, str), reason)
        return value
    _require(
        type(value) is int and 0 <= value < len(strings),
        "invalid_metadata_string_reference",
    )
    return strings[value]


def _layout_manifest(
    layout: CountLayout, strings: _MetadataStringTable
) -> dict[str, Any]:
    return {
        "layout_id": strings.reference(layout.layout_id),
        "carrier_id": strings.reference(layout.carrier_id),
        "banks": [
            {"name": strings.reference(bank.name), "row_count": bank.row_count}
            for bank in layout.banks
        ],
    }


def _profile_manifest(
    profile: Profile, layout_index: int, strings: _MetadataStringTable
) -> dict[str, Any]:
    return {
        "subject": strings.reference(profile.subject),
        "mode": strings.reference(profile.mode),
        "scope": strings.reference(profile.scope),
        "source_id": strings.reference(profile.source_id),
        "context": [
            strings.pair_reference(key, value) for key, value in profile.context
        ],
        "bank_statuses": [
            strings.pair_reference(key, value) for key, value in profile.bank_statuses
        ],
        "provenance": [
            strings.pair_reference(key, value) for key, value in profile.provenance
        ],
        "layout_index": layout_index,
    }


def _collect_profiles(
    snapshot: Snapshot, reuse: _StoreReuse, strings: _MetadataStringTable
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[int],
    list[int],
    list[int],
    list[str],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    layouts: list[CountLayout] = []
    layout_indices: dict[CountLayout, int] = {}
    layout_identities: dict[int, tuple[CountLayout, int]] = {}
    profiles: list[dict[str, Any]] = []
    offsets = [0]
    bank_indices: list[int] = []
    row_indices: list[int] = []
    values: list[str] = []

    def append(profile: Profile) -> int:
        index = len(profiles)
        layout = profile.bundle.layout
        cached = layout_identities.get(id(layout))
        if cached is not None and cached[0] is layout:
            layout_index = cached[1]
        else:
            layout_index = layout_indices.get(layout)
            if layout_index is None:
                layout_index = len(layouts)
                layout_indices[layout] = layout_index
                layouts.append(layout)
            layout_identities[id(layout)] = (layout, layout_index)
        profiles.append(_profile_manifest(profile, layout_index, strings))
        for bank_index, bank in enumerate(profile.bundle.counts):
            for row_index, value in reuse.serialized_row(bank):
                bank_indices.append(bank_index)
                row_indices.append(row_index)
                values.append(value)
        offsets.append(len(values))
        return index

    case_profiles = [append(case.profile) for case in snapshot.cases]
    censor_profiles = [append(censor.profile) for censor in snapshot.censors]
    refs = [
        {"case_id": case.case_id, "profile_index": case_profiles[i]}
        for i, case in enumerate(snapshot.cases)
    ]
    censor_refs = [
        {"censor_id": censor.censor_id, "profile_index": censor_profiles[i]}
        for i, censor in enumerate(snapshot.censors)
    ]
    return (
        [_layout_manifest(layout, strings) for layout in layouts],
        profiles,
        offsets,
        bank_indices,
        row_indices,
        values,
        refs,
        censor_refs,
    )


def _snapshot_manifest(
    snapshot: Snapshot, reuse: _StoreReuse
) -> tuple[dict[str, Any], list[int], list[int], list[int], list[str]]:
    strings = _MetadataStringTable()
    (
        layouts,
        profiles,
        offsets,
        bank_indices,
        row_indices,
        values,
        case_profiles,
        censor_profiles,
    ) = _collect_profiles(snapshot, reuse, strings)
    manifest = {
        "schema": _STORE_SCHEMA,
        "snapshot_schema_version": snapshot.schema_version,
        "revision": snapshot.revision,
        "encoding": dict(_ENCODING),
        "archive": {"file": _ARCHIVE_FILE, "profile_count": len(profiles)},
        "layouts": layouts,
        "profiles": profiles,
        "cases": [
            {
                "case_id": strings.reference(case.case_id),
                "study_uid": strings.reference(case.study_uid),
                "profile_index": case_profiles[i]["profile_index"],
                "calls": [
                    {
                        "question": strings.reference(call.question),
                        "digit": call.digit,
                        "source": strings.reference(call.source),
                        "words": strings.reference(call.words),
                    }
                    for call in case.calls
                ],
                "teaching_revision": strings.reference(case.teaching_revision),
            }
            for i, case in enumerate(snapshot.cases)
        ],
        "trust": [
            {
                "case_id": strings.reference(item.case_id),
                "question": strings.reference(item.question),
                "numerator": item.numerator,
                "denominator": item.denominator,
                "source": strings.reference(item.source),
            }
            for item in snapshot.trust
        ],
        "censors": [
            {
                "censor_id": strings.reference(item.censor_id),
                "question": strings.reference(item.question),
                "answer": item.answer,
                "profile_index": censor_profiles[i]["profile_index"],
                "numerator": item.numerator,
                "denominator": item.denominator,
                "source": strings.reference(item.source),
            }
            for i, item in enumerate(snapshot.censors)
        ],
        "case_count": len(snapshot.cases),
        "trust_count": len(snapshot.trust),
        "censor_count": len(snapshot.censors),
        "metadata_encoding": {
            "schema": _MetadataStringTable.schema,
            "strings": strings.values,
            "pairs": [list(pair) for pair in strings.pair_values],
        },
    }
    return manifest, offsets, bank_indices, row_indices, values


def _npz_bytes(
    offsets: list[int],
    bank_indices: list[int],
    row_indices: list[int],
    values: list[str],
    profile_count: int,
) -> bytes:
    max_digits = max((len(value) for value in values), default=1)
    with tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024) as stream:
        np.savez_compressed(
            stream,
            archive_schema=np.asarray(_ARCHIVE_SCHEMA),
            profile_count=np.asarray(profile_count, dtype=np.int64),
            profile_offsets=np.asarray(offsets, dtype=np.uint64),
            bank_indices=np.asarray(bank_indices, dtype=np.uint64),
            row_indices=np.asarray(row_indices, dtype=np.uint64),
            counts_decimal=np.asarray(values, dtype=f"<U{max_digits}"),
        )
        stream.seek(0)
        return stream.read()


def write_store(path: Path, snapshot: Snapshot) -> dict[str, Any]:
    """Atomically publish one immutable snapshot at a new directory path."""
    if not isinstance(path, Path):
        raise StoreError("invalid_store_path")
    reuse = _StoreReuse()
    _validate_snapshot(snapshot, reuse)
    parent = path.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise StoreError("store_parent_unavailable") from error
    if path.exists():
        raise StoreError("store_already_exists")

    lock_path = path.with_name(path.name + ".publish-lock")
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise StoreError("store_publish_in_progress") from error
    temp_dir: Path | None = None
    try:
        if path.exists():
            raise StoreError("store_already_exists")
        temp_dir = Path(tempfile.mkdtemp(prefix=f".{path.name}.tmp-", dir=parent))
        manifest, offsets, bank_indices, row_indices, values = _snapshot_manifest(
            snapshot, reuse
        )
        profiles = manifest["profiles"]
        archive_data = _npz_bytes(
            offsets, bank_indices, row_indices, values, len(profiles)
        )
        archive_path = temp_dir / _ARCHIVE_FILE
        with archive_path.open("xb") as stream:
            stream.write(archive_data)
            stream.flush()
            os.fsync(stream.fileno())
        manifest["archive"]["sha256"] = _sha256(archive_data)
        manifest["archive"]["nonzero_count"] = len(values)
        manifest["manifest_sha256"] = _sha256(_canonical_json(manifest))
        manifest_data = _canonical_json(manifest) + b"\n"
        manifest_path = temp_dir / "manifest.json"
        with manifest_path.open("xb") as stream:
            stream.write(manifest_data)
            stream.flush()
            os.fsync(stream.fileno())
        dir_fd = os.open(temp_dir, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
        try:
            os.rename(temp_dir, path)
        except FileExistsError as error:
            raise StoreError("store_already_exists") from error
        parent_fd = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
        return {
            "schema": _STORE_SCHEMA,
            "revision": snapshot.revision,
            "case_count": len(snapshot.cases),
            "trust_count": len(snapshot.trust),
            "censor_count": len(snapshot.censors),
            "profile_count": len(profiles),
            "archive_sha256": manifest["archive"]["sha256"],
            "manifest_sha256": manifest["manifest_sha256"],
        }
    except StoreError:
        raise
    except (OSError, TypeError, ValueError, OverflowError) as error:
        raise StoreError("store_write_failed") from error
    finally:
        if temp_dir is not None and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        os.close(lock_fd)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise StoreError(reason)


def _read_manifest(path: Path) -> tuple[dict[str, Any], bytes, Path]:
    if not path.exists():
        raise StoreError("store_missing")
    if not path.is_dir():
        raise StoreError("store_not_directory")
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        raise StoreError("manifest_missing")
    try:
        manifest_data = manifest_path.read_bytes()
        manifest = json.loads(manifest_data)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise StoreError("malformed_manifest") from error
    _require(isinstance(manifest, dict), "malformed_manifest")
    _require(manifest.get("schema") == _STORE_SCHEMA, "unsupported_store_schema")
    _require(manifest.get("encoding") == _ENCODING, "invalid_encoding_metadata")
    _require(_nonempty_text(manifest.get("revision")), "invalid_snapshot_revision")
    _require(
        _nonempty_text(manifest.get("snapshot_schema_version")),
        "invalid_snapshot_schema_version",
    )
    expected_manifest_digest = manifest.get("manifest_sha256")
    _require(
        isinstance(expected_manifest_digest, str)
        and len(expected_manifest_digest) == 64
        and all(ch in "0123456789abcdef" for ch in expected_manifest_digest),
        "manifest_digest_missing_or_invalid",
    )
    digest_manifest = dict(manifest)
    digest_manifest.pop("manifest_sha256")
    _require(
        _sha256(_canonical_json(digest_manifest)) == expected_manifest_digest,
        "manifest_digest_mismatch",
    )
    archive_info = manifest.get("archive")
    _require(isinstance(archive_info, dict), "invalid_archive_metadata")
    archive_name = archive_info.get("file")
    _require(archive_name == _ARCHIVE_FILE, "invalid_archive_path")
    archive_path = path / _ARCHIVE_FILE
    _require(archive_path.is_file(), "archive_missing")
    try:
        archive_data = archive_path.read_bytes()
    except OSError as error:
        raise StoreError("archive_unreadable") from error
    archive_digest = archive_info.get("sha256")
    _require(
        isinstance(archive_digest, str)
        and len(archive_digest) == 64
        and _sha256(archive_data) == archive_digest,
        "archive_digest_mismatch",
    )
    return manifest, archive_data, archive_path


def _layout_from_metadata(
    layout_data: object, strings: list[str] | None = None
) -> CountLayout:
    _require(isinstance(layout_data, dict), "invalid_profile_layout")
    bank_data = layout_data.get("banks")
    _require(isinstance(bank_data, list) and bool(bank_data), "invalid_profile_layout")
    banks: list[BankLayout] = []
    names: set[str] = set()
    for bank in bank_data:
        _require(isinstance(bank, dict), "invalid_profile_layout")
        name = _metadata_text(bank.get("name"), strings, "invalid_profile_layout")
        row_count = bank.get("row_count")
        _require(
            _nonempty_text(name) and _plain_int(row_count) and row_count > 0,
            "invalid_profile_layout",
        )
        _require(name not in names, "invalid_profile_layout")
        names.add(name)
        banks.append(BankLayout(name, row_count))
    layout_id = _metadata_text(
        layout_data.get("layout_id"), strings, "invalid_profile_layout"
    )
    carrier_id = _metadata_text(
        layout_data.get("carrier_id"), strings, "invalid_profile_layout"
    )
    _require(
        _nonempty_text(layout_id) and _nonempty_text(carrier_id),
        "invalid_profile_layout",
    )
    return CountLayout(layout_id, carrier_id, tuple(banks))


def _profile_from_metadata(
    meta: object,
    layouts: list[CountLayout],
    profile_index: int,
    offsets: np.ndarray,
    bank_indices: np.ndarray,
    row_indices: np.ndarray,
    flat_values: list[str],
    reuse: _StoreReuse,
    strings: list[str] | None = None,
    pair_table: list[tuple[int, int]] | None = None,
) -> Profile:
    _require(isinstance(meta, dict), "invalid_profile_metadata")
    layout_index = meta.get("layout_index")
    _require(
        _plain_int(layout_index) and 0 <= layout_index < len(layouts),
        "invalid_profile_layout_index",
    )
    layout = layouts[layout_index]
    start, stop = int(offsets[profile_index]), int(offsets[profile_index + 1])
    rows_by_bank: dict[int, dict[int, int]] = {}
    previous_address: tuple[int, int] | None = None
    for entry_index in range(start, stop):
        bank_index = int(bank_indices[entry_index])
        row_index = int(row_indices[entry_index])
        address = (bank_index, row_index)
        _require(bank_index < len(layout.banks), "sparse_bank_index_out_of_range")
        _require(
            row_index < layout.banks[bank_index].row_count,
            "sparse_row_index_out_of_range",
        )
        _require(
            previous_address is None or address > previous_address,
            "sparse_addresses_not_canonical",
        )
        previous_address = address
        item = flat_values[entry_index]
        _require(
            isinstance(item, str) and item.isascii() and item.isdigit() and item != "0",
            "invalid_count_encoding",
        )
        parsed = _parse_count_decimal(item)
        _require(_count_decimal(parsed) == item, "noncanonical_count_encoding")
        rows_by_bank.setdefault(bank_index, {})[row_index] = parsed

    counts = list(reuse.empty_counts(layout))
    for bank_index, nonzero_rows in rows_by_bank.items():
        row_values = [0] * layout.banks[bank_index].row_count
        for row_index, value in nonzero_rows.items():
            row_values[row_index] = value
        counts[bank_index] = tuple(row_values)
    bundle = CountBundle(layout, tuple(counts))
    context = _decode_pairs(
        meta.get("context"), "invalid_profile_context", strings, pair_table
    )
    statuses = _decode_pairs(
        meta.get("bank_statuses"), "invalid_profile_bank_statuses", strings, pair_table
    )
    provenance = _decode_pairs(
        meta.get("provenance"), "invalid_profile_provenance", strings, pair_table
    )
    profile = Profile(
        _metadata_text(meta.get("subject"), strings, "invalid_profile_metadata"),
        bundle,
        _metadata_text(meta.get("mode"), strings, "invalid_profile_metadata"),
        _metadata_text(meta.get("scope"), strings, "invalid_profile_metadata"),
        _metadata_text(meta.get("source_id"), strings, "invalid_profile_metadata"),
        context,
        statuses,
        provenance,
    )
    reason = _valid_profile(profile, reuse)
    _require(reason is None, reason or "invalid_profile")
    return profile


def _decode_pairs(
    value: object,
    reason: str,
    strings: list[str] | None = None,
    pair_table: list[tuple[int, int]] | None = None,
) -> tuple[tuple[str, str], ...]:
    _require(isinstance(value, list), reason)
    rows: list[tuple[str, str]] = []
    if strings is None:
        for row in value:
            _require(isinstance(row, list) and len(row) == 2, reason)
            rows.append(
                (
                    _metadata_text(row[0], None, reason),
                    _metadata_text(row[1], None, reason),
                )
            )
    else:
        _require(pair_table is not None, "invalid_metadata_pair_table")
        for pair_index in value:
            _require(
                type(pair_index) is int and 0 <= pair_index < len(pair_table),
                "invalid_metadata_pair_reference",
            )
            key_index, value_index = pair_table[pair_index]
            rows.append((strings[key_index], strings[value_index]))
    result = tuple(rows)
    _require(_pair_sequence(result), reason)
    return result


def _load_archive(
    data: bytes, profile_count: int, nonzero_count: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    # np.load accepts a file-like object, avoiding a second persistent artifact.
    from io import BytesIO

    try:
        with np.load(BytesIO(data), allow_pickle=False) as archive:
            _require(
                set(archive.files)
                == {
                    "archive_schema",
                    "profile_count",
                    "profile_offsets",
                    "bank_indices",
                    "row_indices",
                    "counts_decimal",
                },
                "invalid_archive_fields",
            )
            schema = archive["archive_schema"]
            stored_profile_count = archive["profile_count"]
            offsets = archive["profile_offsets"]
            bank_indices = archive["bank_indices"]
            row_indices = archive["row_indices"]
            values = archive["counts_decimal"]
            _require(
                schema.shape == () and str(schema.item()) == _ARCHIVE_SCHEMA,
                "unsupported_archive_schema",
            )
            _require(
                stored_profile_count.shape == ()
                and stored_profile_count.dtype.kind in "iu"
                and int(stored_profile_count.item()) == profile_count,
                "archive_profile_count_mismatch",
            )
            _require(
                offsets.dtype.kind == "u" and offsets.shape == (profile_count + 1,),
                "invalid_profile_offsets",
            )
            _require(
                bank_indices.dtype.kind == "u"
                and bank_indices.shape == (nonzero_count,),
                "invalid_sparse_bank_indices",
            )
            _require(
                row_indices.dtype.kind == "u" and row_indices.shape == (nonzero_count,),
                "invalid_sparse_row_indices",
            )
            _require(
                values.dtype.kind == "U" and values.shape == (nonzero_count,),
                "invalid_count_array",
            )
            offset_values = np.asarray(offsets, dtype=np.int64)
            _require(
                int(offset_values[0]) == 0 and int(offset_values[-1]) == nonzero_count,
                "invalid_profile_offsets",
            )
            _require(
                bool(np.all(offset_values[1:] >= offset_values[:-1])),
                "invalid_profile_offsets",
            )
            return (
                offset_values,
                np.asarray(bank_indices, dtype=np.uint64),
                np.asarray(row_indices, dtype=np.uint64),
                [str(value) for value in values.tolist()],
            )
    except StoreError:
        raise
    except Exception as error:
        raise StoreError("malformed_archive") from error


def read_store(path: Path) -> Snapshot:
    """Read one complete snapshot, refusing missing or corrupted content."""
    if not isinstance(path, Path):
        raise StoreError("invalid_store_path")
    manifest, archive_data, _ = _read_manifest(path)
    metadata_tables = _metadata_strings(manifest)
    strings, pair_table = (
        metadata_tables if metadata_tables is not None else (None, None)
    )
    layout_data = manifest.get("layouts")
    profile_metas = manifest.get("profiles")
    case_data = manifest.get("cases")
    trust_data = manifest.get("trust")
    censor_data = manifest.get("censors")
    archive_info = manifest["archive"]
    _require(isinstance(layout_data, list), "invalid_layouts_metadata")
    _require(isinstance(profile_metas, list), "invalid_profiles_metadata")
    _require(isinstance(case_data, list), "invalid_cases_metadata")
    _require(isinstance(trust_data, list), "invalid_trust_metadata")
    _require(isinstance(censor_data, list), "invalid_censors_metadata")
    _require(
        archive_info.get("profile_count") == len(profile_metas),
        "archive_profile_count_mismatch",
    )
    _require(manifest.get("case_count") == len(case_data), "case_count_mismatch")
    _require(manifest.get("trust_count") == len(trust_data), "trust_count_mismatch")
    _require(manifest.get("censor_count") == len(censor_data), "censor_count_mismatch")
    nonzero_count = archive_info.get("nonzero_count")
    _require(_plain_int(nonzero_count) and nonzero_count >= 0, "invalid_nonzero_count")
    offsets, bank_indices, row_indices, values = _load_archive(
        archive_data, len(profile_metas), nonzero_count
    )
    layouts = [_layout_from_metadata(meta, strings) for meta in layout_data]
    _require(len(set(layouts)) == len(layouts), "duplicate_layout_metadata")
    reuse = _StoreReuse()
    profiles = [
        _profile_from_metadata(
            meta,
            layouts,
            index,
            offsets,
            bank_indices,
            row_indices,
            values,
            reuse,
            strings,
            pair_table,
        )
        for index, meta in enumerate(profile_metas)
    ]

    cases: list[Case] = []
    for item in case_data:
        _require(isinstance(item, dict), "invalid_case_metadata")
        profile_index = item.get("profile_index")
        _require(
            _plain_int(profile_index) and 0 <= profile_index < len(profiles),
            "invalid_case_profile_index",
        )
        call_data = item.get("calls")
        _require(isinstance(call_data, list), "invalid_calls_metadata")
        calls: list[Call] = []
        for call in call_data:
            _require(isinstance(call, dict), "invalid_call_metadata")
            calls.append(
                Call(
                    _metadata_text(
                        call.get("question"), strings, "invalid_call_metadata"
                    ),
                    call.get("digit"),
                    _metadata_text(
                        call.get("source"), strings, "invalid_call_metadata"
                    ),
                    _metadata_text(call.get("words"), strings, "invalid_call_metadata"),
                )
            )
        cases.append(
            Case(
                _metadata_text(item.get("case_id"), strings, "invalid_case_metadata"),
                _metadata_text(item.get("study_uid"), strings, "invalid_case_metadata"),
                profiles[profile_index],
                tuple(calls),
                _metadata_text(
                    item.get("teaching_revision"), strings, "invalid_case_metadata"
                ),
            )
        )

    trust: list[Trust] = []
    for item in trust_data:
        _require(isinstance(item, dict), "invalid_trust_record")
        trust.append(
            Trust(
                _metadata_text(item.get("case_id"), strings, "invalid_trust_record"),
                _metadata_text(item.get("question"), strings, "invalid_trust_record"),
                item.get("numerator"),
                item.get("denominator"),
                _metadata_text(item.get("source"), strings, "invalid_trust_record"),
            )
        )

    censors: list[Censor] = []
    for item in censor_data:
        _require(isinstance(item, dict), "invalid_censor_record")
        profile_index = item.get("profile_index")
        _require(
            _plain_int(profile_index) and 0 <= profile_index < len(profiles),
            "invalid_censor_profile_index",
        )
        censors.append(
            Censor(
                _metadata_text(item.get("censor_id"), strings, "invalid_censor_record"),
                _metadata_text(item.get("question"), strings, "invalid_censor_record"),
                item.get("answer"),
                profiles[profile_index],
                item.get("numerator"),
                item.get("denominator"),
                _metadata_text(item.get("source"), strings, "invalid_censor_record"),
            )
        )
    snapshot = Snapshot(
        manifest["revision"],
        tuple(cases),
        tuple(trust),
        tuple(censors),
        manifest["snapshot_schema_version"],
    )
    _validate_snapshot(snapshot, reuse)
    _require(len(snapshot.cases) == manifest["case_count"], "case_count_mismatch")
    return snapshot


__all__ = ["StoreError", "read_store", "validate_case", "write_store"]
