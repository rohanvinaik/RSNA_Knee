"""Explicit, caller-declared study cohorts for the diagnostic command.

A cohort file names partitions of studies, which pairs of partitions must not
share a study or a known independent source group, and optionally the source
group of some studies. Everything is declared by the caller: there is no default
partition, no random split, no stratification, no ratio, and no label is read.
Partition names are opaque. A missing source group is unknown and neutral; a
group string, including the literal ``unknown``, is only ever a genuine identity.

Study spellings are retained exactly (no case, whitespace or duplicate
normalization). The study-id safety rule is the same decision as
``knee.diagnosis.pipeline._safe_uid``; it is restated as a total decision here
because the pipeline will import this module and a pipeline import would cycle.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

__all__ = [
    "SCHEMA",
    "Cohort",
    "CohortError",
    "cohort_document_status",
    "load_cohort",
    "partition_uids",
    "source_group_for",
    "uid_status",
]

SCHEMA = "knee.diagnostic-cohort/v1"
_REQUIRED = ("schema", "partitions", "disjoint_partitions")
_ALLOWED = (*_REQUIRED, "source_groups")


class CohortError(ValueError):
    """A named failure at the explicit-cohort boundary.

    ``code`` is the stable name; ``detail`` locates it; ``uids`` carries every
    study involved when more than the first is useful (missing requests).
    """

    def __init__(self, code: str, detail: str = "", uids: tuple[str, ...] = ()):
        super().__init__(f"{code}:{detail}" if detail else code)
        self.code = code
        self.detail = detail
        self.uids = uids


@dataclass(frozen=True, slots=True)
class Cohort:
    """Immutable validated cohort declaration with its source identity.

    ``partitions`` keeps declared name and study order; ``disjoint_partitions``
    keeps each declared pair as written; ``source_groups`` keeps declared order.
    ``source`` is the resolved file path and ``sha256`` the digest of its exact
    bytes, so a later run can prove which declaration selected its studies.
    """

    schema: str
    partitions: tuple[tuple[str, tuple[str, ...]], ...]
    disjoint_partitions: tuple[tuple[str, str], ...]
    source_groups: tuple[tuple[str, str], ...]
    source: str
    sha256: str
    _group_index: Mapping[str, str] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _partition_index: Mapping[str, tuple[str, ...]] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "_group_index", MappingProxyType(dict(self.source_groups))
        )
        object.__setattr__(
            self, "_partition_index", MappingProxyType(dict(self.partitions))
        )


def uid_status(value: object) -> str:
    """Decide study-ID safety exactly as the pipeline's ``_safe_uid`` does.

    post: __return__ in ('ok', 'cohort_uid_not_string', 'cohort_uid_unsafe')
    """
    if type(value) is not str:
        return "cohort_uid_not_string"
    if (
        not value.strip()
        or value in (".", "..")
        or any(ord(character) in (0, 47, 92) for character in value)
    ):
        return "cohort_uid_unsafe"
    return "ok"


def _name_ok(value: object) -> bool:
    return type(value) is str and bool(value.strip())


def _group_ok(value: object) -> bool:
    # Same acceptance as composition's metadata text rule, so a declared group
    # can never be silently dropped by the consumer that excludes by group.
    return type(value) is str and bool(value.strip()) and "\0" not in value


def _partitions_status(partitions: object) -> str:
    if type(partitions) is not dict:
        return "cohort_partitions_invalid"
    if not partitions:
        return "cohort_partitions_empty"
    for name, uids in partitions.items():
        if not _name_ok(name):
            return "cohort_partition_name_invalid"
        if type(uids) is not list:
            return f"cohort_partition_not_list:{name}"
        if not uids:
            return f"cohort_partition_empty:{name}"
        seen: set[str] = set()
        for uid in uids:
            status = uid_status(uid)
            if status != "ok":
                return f"{status}:{name}"
            if uid in seen:
                return f"cohort_duplicate_uid:{name}:{uid}"
            seen.add(uid)
    return "ok"


def _pairs_status(pairs: object, names: dict) -> str:
    if type(pairs) is not list:
        return "cohort_disjoint_partitions_invalid"
    seen: set[frozenset[str]] = set()
    for pair in pairs:
        if (
            type(pair) is not list
            or len(pair) != 2
            or not all(type(name) is str for name in pair)
        ):
            return "cohort_disjoint_pair_malformed"
        first, second = pair
        if first == second:
            return f"cohort_disjoint_pair_same_partition:{first}"
        for name in pair:
            if name not in names:
                return f"cohort_disjoint_unknown_partition:{name}"
        key = frozenset(pair)
        if key in seen:
            return f"cohort_disjoint_duplicate_pair:{first}|{second}"
        seen.add(key)
    return "ok"


def _groups_status(groups: object, members: frozenset[str]) -> str:
    if type(groups) is not dict:
        return "cohort_source_groups_invalid"
    for uid, group in groups.items():
        if type(uid) is not str or uid not in members:
            return f"cohort_source_group_unknown_uid:{uid}"
        if not _group_ok(group):
            return f"cohort_source_group_invalid:{uid}"
    return "ok"


def _leakage_status(document: dict) -> str:
    """Refuse a declared disjoint pair that shares a study or a known group."""
    partitions = document["partitions"]
    groups = document.get("source_groups", {})
    for first, second in document["disjoint_partitions"]:
        second_uids = set(partitions[second])
        for uid in partitions[first]:
            if uid in second_uids:
                return f"cohort_disjoint_uid_overlap:{first}|{second}:{uid}"
        second_groups = {groups[u] for u in partitions[second] if u in groups}
        for uid in partitions[first]:
            if uid in groups and groups[uid] in second_groups:
                return f"cohort_disjoint_group_overlap:{first}|{second}:{groups[uid]}"
    return "ok"


def cohort_document_status(document: object) -> str:
    """Name the first defect of a parsed cohort document, or ``ok``.

    Defects are reported as ``code`` or ``code:detail``. This is the whole
    validation decision; nothing is inferred, defaulted or repaired.

    post: __return__ != ''
    """
    if type(document) is not dict:
        return "cohort_not_object"
    if not document:
        return "cohort_empty"
    for key in document:
        if key not in _ALLOWED:
            return f"cohort_unknown_key:{key}"
    for key in _REQUIRED:
        if key not in document:
            return f"cohort_missing_key:{key}"
    if document["schema"] != SCHEMA or type(document["schema"]) is not str:
        return "cohort_schema_unsupported"
    status = _partitions_status(document["partitions"])
    if status != "ok":
        return status
    partitions = document["partitions"]
    status = _pairs_status(document["disjoint_partitions"], partitions)
    if status != "ok":
        return status
    members = frozenset(uid for uids in partitions.values() for uid in uids)
    status = _groups_status(document.get("source_groups", {}), members)
    if status != "ok":
        return status
    return _leakage_status(document)


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise CohortError("cohort_duplicate_json_key", key)
        result[key] = value
    return result


def _raise_status(status: str) -> None:
    code, _, detail = status.partition(":")
    raise CohortError(code, detail)


def load_cohort(path: Path) -> Cohort:
    """Read one explicit cohort file; refuse anything malformed, empty or leaky."""
    if not isinstance(path, Path):
        raise CohortError("cohort_path_invalid")
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise CohortError("cohort_unreadable", str(path)) from error
    if not raw.strip():
        raise CohortError("cohort_empty")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CohortError("cohort_not_utf8") from error
    try:
        document = json.loads(text, object_pairs_hook=_no_duplicate_keys)
    except (json.JSONDecodeError, RecursionError) as error:
        raise CohortError("cohort_json_malformed") from error
    status = cohort_document_status(document)
    if status != "ok":
        _raise_status(status)
    return Cohort(
        schema=document["schema"],
        partitions=tuple(
            (name, tuple(uids)) for name, uids in document["partitions"].items()
        ),
        disjoint_partitions=tuple(
            (pair[0], pair[1]) for pair in document["disjoint_partitions"]
        ),
        source_groups=tuple(document.get("source_groups", {}).items()),
        source=str(path.resolve()),
        sha256=hashlib.sha256(raw).hexdigest(),
    )


def partition_uids(
    cohort: Cohort, name: str, available_uids: Sequence[str]
) -> tuple[str, ...]:
    """Return the named partition's studies in declared order.

    Every declared study must be present exactly once among ``available_uids``
    (extra available studies are simply not selected). Spellings are compared
    exactly. A missing or ambiguous request is refused, never skipped or merged.
    """
    if not isinstance(cohort, Cohort):
        raise CohortError("cohort_invalid")
    if type(name) is not str:
        raise CohortError("cohort_partition_name_invalid")
    declared = cohort._partition_index.get(name)
    if declared is None:
        raise CohortError("cohort_partition_unknown", name)
    if isinstance(available_uids, (str, bytes)) or not isinstance(
        available_uids, Sequence
    ):
        raise CohortError("cohort_available_invalid")
    counts: dict[str, int] = {}
    for uid in available_uids:
        if type(uid) is not str:
            raise CohortError("cohort_available_invalid")
        counts[uid] = counts.get(uid, 0) + 1
    missing = tuple(uid for uid in declared if uid not in counts)
    if missing:
        raise CohortError("cohort_requested_uid_missing", missing[0], missing)
    ambiguous = tuple(uid for uid in declared if counts[uid] > 1)
    if ambiguous:
        raise CohortError("cohort_available_uid_ambiguous", ambiguous[0], ambiguous)
    return declared


def source_group_for(cohort: Cohort, uid: str) -> str:
    """Return the explicit group of ``uid``, or ``""`` when none was declared."""
    if not isinstance(cohort, Cohort):
        raise CohortError("cohort_invalid")
    if type(uid) is not str:
        raise CohortError("cohort_uid_not_string")
    return cohort._group_index.get(uid, "")
