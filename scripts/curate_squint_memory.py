"""Curate one published squint memory: retire named whole object cases, nothing inferred.

Some teaching cases are known to be wrongly named and should not poison recall.
This command withdraws exactly the cases a person names, publishes the result as a
new memory beside the old one, and changes nothing else. It never looks at an
image, a label, a mask, a cosine or any other measurement to choose a case: every
decision comes from the decision file, authored independently, with its evidence,
reason and reviewer. The parent is only read.

Two commands:

  fingerprints   print each object case's id, study, subject and profile fingerprint
                 (identity only: no labels, sizes or scores), so a decision can pin the
                 exact reading its author inspected.
  curate         publish the curated child memory.

Exact commands, from the repository root with the project interpreter:

  PYTHONPATH=src .venv/bin/python scripts/curate_squint_memory.py fingerprints --memory PARENT --expected-manifest-sha256 SHA [--case-id ID ...]
  PYTHONPATH=src .venv/bin/python scripts/curate_squint_memory.py curate --memory PARENT --expected-manifest-sha256 SHA --decisions decisions.json --output-memory NEWDIR

PARENT is a memory directory (or its manifest.json). SHA is the SHA-256 of that
manifest.json (shasum -a 256 PARENT/manifest.json). NEWDIR must not exist and must
lie outside PARENT. A receipt is printed as one JSON line; a refusal prints one JSON
line with its code on stderr and exits 2, with nothing published and PARENT untouched.

Decision file (knee.squint-memory-curation-decisions/v1). An empty list is valid and
keeps every case. Any other key, a missing key, a repeated case or a repeated JSON key
is refused:

  {"schema": "knee.squint-memory-curation-decisions/v1",
   "decisions": [{"case_id": "squint-case:STUDY:SUBJECT",
                  "expected_profile_fingerprint": "64 hex digits from fingerprints",
                  "disposition": "retire_whole_case",
                  "evidence": "what the source inspection showed",
                  "reason": "pending-view-adjudication",
                  "reviewer": "who inspected"}]}

What it does, in order. It reads PARENT once and refuses unless its manifest digest is
SHA and it is a knee.squint-memory/v1 that has not been curated. Each decision must name
an existing object case whose profile fingerprint is the pinned one. The retired cases
leave the case list; each is kept whole, with its decision, in the child manifest under
curation. Study-level configuration cases that name a retired object as a role are
rebuilt by the library's own with_configuration_cases from the remaining object cases
and the unchanged label ledger, in the parent's own profile writer; every other case is
carried over untouched. The child gets a versioned revision, its own fresh recall
preparation (the parent's is never read), and is saved with save_memory into a hidden
staging directory next to NEWDIR. It is read back through load_memory_snapshot (manifest
digest, revision, case list, curation record, source fingerprint and acceptance of its
preparation by prepare_recall) and only then renamed to NEWDIR.

Limitations.
  * It decides nothing. It cannot tell a wrongly named case from a right one; a wrong
    decision is carried out as written. To change a decision, run again from the
    original PARENT with a corrected file: a curated memory is refused as a parent, so
    curations never stack silently.
  * Retirement is whole-case. Every region and view of the case leaves recall together,
    and nothing is asserted about any other view of that object; per-view or per-facet
    retirement does not exist.
  * Only object cases can be retired. Configuration cases are derived and are refused as
    targets. The portable full-profile tables are carried whole, so a retired case's
    payload stays in them, referenced by no active case; curation.counts says how many.
  * The parent's compile records (procedure, territory_writer, source_identities) and any
    censors describe the parent and are carried unchanged. The child's own counts are in
    curation.counts.
  * A noncanonical configuration that does not name a retired object's role is carried
    over and listed if the canonical rebuild would write it differently. A configuration
    that still contains a retired object's role banks cannot be rebuilt from its identity
    and is refused by the verifier; no noncanonical configuration is retired or rewritten
    by inference.
  * The recall preparation is computed afresh and costs as much as the compile's.
  * It runs no held-out evaluation. A result measured on the parent says nothing about
    the child.
  * It uses four private helpers of knee.diagnosis.squint_memory (_json_sha256, _canonical,
    _link_configuration_full_profiles, _full_profile_retention_receipt).
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import knee
from knee.diagnosis.declarations import question_for
from knee.diagnosis.squint_configurations import (
    ConfigurationProfileError,
    with_configuration_cases,
)
from knee.diagnosis.squint_locator import prepare_recall, recall_source_fingerprint
from knee.diagnosis.squint_memory import (
    MemorySnapshot,
    _canonical,
    _full_profile_retention_receipt,
    _json_sha256,
    _link_configuration_full_profiles,
    load_memory_snapshot,
    save_memory,
)
from knee.json_store import load_json, resolve_json_path

CURATION_SCHEMA = "knee.squint-memory-curation/v1"
DECISIONS_SCHEMA = "knee.squint-memory-curation-decisions/v1"
RECEIPT_SCHEMA = "knee.squint-memory-curation-receipt/v1"
FINGERPRINTS_SCHEMA = "knee.squint-memory-curation-fingerprints/v1"
CURATION_REVISION = "squint-memory-curation-v1"
RETIRE_WHOLE_CASE = "retire_whole_case"
DISPOSITIONS = (RETIRE_WHOLE_CASE,)

_CONFIGURATION_PREFIX = "squint-configuration:"
_QUESTION_SUBJECT_PREFIX = "diagnosis/"
_DECISION_KEYS = frozenset(
    {
        "case_id",
        "expected_profile_fingerprint",
        "disposition",
        "evidence",
        "reason",
        "reviewer",
    }
)
#: What a rebuilt configuration case must still say, as the parent said it.
_CONFIGURATION_IDENTITY = (
    "case_id",
    "study_uid",
    "subject",
    "condition_calls",
    "presentation_scope",
    "label_attribution",
    "teaching_source",
    "regions",
)
_SEMANTICS = {
    "retired_case_scope": "whole_case",
    "other_view_facets_asserted_false": False,
    "note": (
        "A retired case is withdrawn from recall as a whole. Nothing is asserted "
        "about any other view or facet of that object."
    ),
}
_SHA256 = re.compile(r"[0-9a-f]{64}")


class CurationError(ValueError):
    """A named refusal: nothing was published and the parent was not touched."""

    def __init__(self, code: str, detail: Any = None):
        self.code = code
        self.detail = detail
        super().__init__(code)


def _same(left: object, right: object) -> bool:
    """Equal as the memory's own canonical JSON sees them (key order is not content)."""
    return _canonical({"value": left}) == _canonical({"value": right})


# --------------------------------------------------------------- the decision file


def case_profile_fingerprint(case: Mapping[str, Any]) -> str:
    """SHA-256 of the case's squint profile (banks and source), as the memory hashes JSON."""
    return _json_sha256(case["profile"])


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "\0" not in value


def _unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CurationError("decisions_json_duplicate_key", key)
        result[key] = value
    return result


def _decision_record(entry: object) -> dict[str, str]:
    if not isinstance(entry, dict):
        raise CurationError("decision_invalid")
    if set(entry) != _DECISION_KEYS:
        raise CurationError("decision_keys_invalid", sorted(map(str, entry)))
    if not _text(entry["case_id"]):
        raise CurationError("decision_case_id_invalid")
    fingerprint = entry["expected_profile_fingerprint"]
    if not isinstance(fingerprint, str) or not _SHA256.fullmatch(fingerprint):
        raise CurationError("decision_fingerprint_invalid", entry["case_id"])
    if entry["disposition"] not in DISPOSITIONS:
        raise CurationError("decision_disposition_unknown", entry["case_id"])
    for field in ("evidence", "reason", "reviewer"):
        if not _text(entry[field]):
            raise CurationError(f"decision_{field}_invalid", entry["case_id"])
    return dict(entry)


def parse_decisions(raw: bytes) -> dict[str, Any]:
    """Validate the decision file's bytes; refuse anything not exactly as specified."""
    try:
        document = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CurationError("decisions_json_invalid") from error
    if not isinstance(document, dict) or set(document) != {"schema", "decisions"}:
        raise CurationError("decisions_document_invalid")
    if document["schema"] != DECISIONS_SCHEMA:
        raise CurationError("decisions_schema_invalid")
    if not isinstance(document["decisions"], list):
        raise CurationError("decisions_list_invalid")
    records = [_decision_record(entry) for entry in document["decisions"]]
    ids = [record["case_id"] for record in records]
    repeated = sorted({case_id for case_id in ids if ids.count(case_id) > 1})
    if repeated:
        raise CurationError("decision_case_duplicate", repeated)
    records.sort(key=lambda record: record["case_id"])
    return {
        "records": records,
        "set_sha256": _json_sha256(records),
        "file_sha256": hashlib.sha256(raw).hexdigest(),
    }


# ------------------------------------------------------------------- the parent


def _is_configuration(case: Mapping[str, Any]) -> bool:
    return str(case["case_id"]).startswith(_CONFIGURATION_PREFIX)


def _memory_of(snapshot: MemorySnapshot) -> dict[str, Any]:
    if snapshot.status != "squint" or snapshot.memory is None:
        raise CurationError(snapshot.error_code or "parent_not_a_squint_memory")
    return snapshot.memory


def _parent_memory(snapshot: MemorySnapshot, expected_manifest_sha256: str) -> dict:
    """The parent's memory, only if it is the pinned bytes and not yet curated."""
    if not isinstance(expected_manifest_sha256, str) or not _SHA256.fullmatch(
        expected_manifest_sha256
    ):
        raise CurationError("expected_manifest_sha256_invalid")
    memory = _memory_of(snapshot)
    if snapshot.sha256 != expected_manifest_sha256:
        raise CurationError(
            "parent_manifest_sha256_mismatch",
            {"expected": expected_manifest_sha256, "actual": snapshot.sha256},
        )
    if "curation" in memory:
        raise CurationError("parent_already_curated")
    if "prepared_recall" in memory:
        raise CurationError("parent_embeds_recall_preparation")
    return memory


def _require_object_cases(
    case_ids: Sequence[str], by_id: Mapping[str, Mapping[str, Any]], prefix: str
) -> None:
    """Refuse, by name and with every offender, ids that are not existing object cases."""
    unknown = [case_id for case_id in case_ids if case_id not in by_id]
    if unknown:
        raise CurationError(f"{prefix}_case_unknown", unknown)
    derived = [case_id for case_id in case_ids if _is_configuration(by_id[case_id])]
    if derived:
        raise CurationError(f"{prefix}_case_is_derived_configuration", derived)


def _resolve(
    records: Sequence[dict[str, str]], by_id: Mapping[str, dict[str, Any]]
) -> list[tuple[dict[str, str], dict[str, Any]]]:
    """Each decision with the object case it names, only if its pin still holds."""
    _require_object_cases([record["case_id"] for record in records], by_id, "decision")
    stale = [
        record["case_id"]
        for record in records
        if case_profile_fingerprint(by_id[record["case_id"]])
        != record["expected_profile_fingerprint"]
    ]
    if stale:
        raise CurationError("decision_profile_fingerprint_mismatch", stale)
    return [(record, by_id[record["case_id"]]) for record in records]


# ------------------------------------------------------- the configuration rebuild


def _question_objects(case: Mapping[str, Any]) -> frozenset[str]:
    subject = case.get("subject")
    if isinstance(subject, str) and subject.startswith(_QUESTION_SUBJECT_PREFIX):
        try:
            question = question_for(subject.removeprefix(_QUESTION_SUBJECT_PREFIX))
        except KeyError:
            return frozenset()
        return frozenset(question.objects)
    return frozenset()


def _single_procedure(cases: Sequence[Mapping[str, Any]]) -> str | None:
    """The one profile writer every object case was read with, or a refusal."""
    found: set[str | None] = set()
    for case in cases:
        source = case["profile"].get("source")
        found.add(source.get("procedure") if isinstance(source, dict) else None)
    if len(found) > 1:
        raise CurationError(
            "parent_profile_procedure_not_single", sorted(map(str, found))
        )
    return next(iter(found), None)


def _rebuild_configurations(
    parent: Mapping[str, Any],
    objects: Sequence[dict[str, Any]],
    active: list[dict[str, Any]],
    configurations: Sequence[dict[str, Any]],
    retired_subjects: Mapping[str, set[str]],
) -> tuple[dict[str, dict[str, Any]], list[str], str | None]:
    """Rebuild only the configuration cases that name a retired object as a role.

    The library's own ``with_configuration_cases`` writes them from the remaining
    object cases and the parent's unchanged label ledger, in the parent's own
    profile writer. Every other configuration case is left as the parent has it.
    Returns the rebuilt cases by id, the carried-over cases the canonical rebuild
    would now write differently, and the writer's procedure.
    """
    affected = {
        case["case_id"]
        for case in configurations
        if retired_subjects.get(case["study_uid"], set()) & _question_objects(case)
    }
    if not affected:
        return {}, [], None
    procedure = _single_procedure(objects)
    try:
        rebuilt = with_configuration_cases(
            {**parent, "cases": active},
            **({} if procedure is None else {"procedure": procedure}),
        )
    except ConfigurationProfileError as error:
        raise CurationError(f"configuration_rebuild_refused:{error.code}") from error
    _link_configuration_full_profiles(rebuilt)
    canonical = {case["case_id"]: case for case in rebuilt["cases"][len(active) :]}
    missing = sorted(affected - canonical.keys())
    if missing:
        raise CurationError("affected_configuration_not_rebuilt", missing)
    drift = [
        case["case_id"]
        for case in configurations
        if case["case_id"] not in affected
        and (
            case["case_id"] not in canonical
            or not _same(case, canonical[case["case_id"]])
        )
    ]
    return (
        {case_id: canonical[case_id] for case_id in sorted(affected)},
        drift,
        procedure,
    )


# ------------------------------------------------------------- building the child


def _record(
    snapshot: MemorySnapshot,
    parent: Mapping[str, Any],
    child: Mapping[str, Any],
    decisions: Mapping[str, Any],
    retired: Sequence[tuple[dict[str, str], dict[str, Any]]],
    rebuilt: Mapping[str, Any],
    drift: Sequence[str],
    procedure: str | None,
) -> dict[str, Any]:
    objects = [case for case in parent["cases"] if not _is_configuration(case)]
    configurations = len(parent["cases"]) - len(objects)
    parent_links = _full_profile_retention_receipt(dict(parent))
    child_links = _full_profile_retention_receipt(dict(child))
    return {
        "schema": CURATION_SCHEMA,
        "operation": "retire_whole_cases",
        "semantics": dict(_SEMANTICS),
        "parent": {
            "manifest": str(snapshot.path),
            "manifest_sha256": snapshot.sha256,
            "revision": parent["revision"],
            "recall_source_fingerprint": recall_source_fingerprint(parent),
        },
        "decisions": {
            "schema": DECISIONS_SCHEMA,
            "file_sha256": decisions["file_sha256"],
            "set_sha256": decisions["set_sha256"],
            "count": len(retired),
        },
        "retired_cases": [
            {"decision": dict(record), "case": copy.deepcopy(case)}
            for record, case in retired
        ],
        "configuration_cases": {
            "rebuilt_with": "knee.diagnosis.squint_configurations.with_configuration_cases",
            "profile_procedure": procedure,
            "rebuilt_case_ids": sorted(rebuilt),
            "carried_over_differs_from_canonical_rebuild": list(drift),
        },
        "label_ledger_sha256": _json_sha256(parent.get("label_ledger")),
        "child_recall_source_fingerprint": recall_source_fingerprint(child),
        "counts": {
            "parent": {
                "cases": len(parent["cases"]),
                "object_cases": len(objects),
                "configuration_cases": configurations,
            },
            "retired_object_cases": len(retired),
            "child": {
                "cases": len(child["cases"]),
                "object_cases": len(objects) - len(retired),
                "configuration_cases": configurations,
            },
            "configuration_cases_rebuilt": len(rebuilt),
            "configuration_cases_carried_over": configurations - len(rebuilt),
            "full_profile_payloads": {
                "in_tables": parent_links["payload_count"],
                "case_links_parent": parent_links["case_payload_links"],
                "case_links_child": child_links["case_payload_links"],
            },
        },
    }


def curate_memory(
    snapshot: MemorySnapshot,
    decisions: Mapping[str, Any],
    *,
    expected_manifest_sha256: str,
) -> dict[str, Any]:
    """The child memory, unpublished. Pure: the snapshot and its memory are not changed."""
    parent = _parent_memory(snapshot, expected_manifest_sha256)
    cases = parent["cases"]
    retired = _resolve(decisions["records"], {case["case_id"]: case for case in cases})
    retired_ids = {record["case_id"] for record, _ in retired}
    retired_subjects: dict[str, set[str]] = {}
    for _, case in retired:
        retired_subjects.setdefault(case["study_uid"], set()).add(case["subject"])
    objects = [case for case in cases if not _is_configuration(case)]
    configurations = [case for case in cases if _is_configuration(case)]
    active = [case for case in objects if case["case_id"] not in retired_ids]
    rebuilt, drift, procedure = _rebuild_configurations(
        parent, objects, active, configurations, retired_subjects
    )
    child = dict(parent)
    child["cases"] = [
        rebuilt.get(case["case_id"], case)
        for case in cases
        if case["case_id"] not in retired_ids
    ]
    child["revision"] = (
        f"{parent['revision']}+{CURATION_REVISION}-{decisions['set_sha256'][:12]}"
    )
    if "full_profile_retention" in parent:
        child["full_profile_retention"] = _full_profile_retention_receipt(child)
    child["curation"] = _record(
        snapshot, parent, child, decisions, retired, rebuilt, drift, procedure
    )
    verify_curation(parent, child)
    return child


def verify_curation(parent: Mapping[str, Any], child: Mapping[str, Any]) -> None:
    """Check the child against the parent, independently of how it was built.

    Nothing was dropped or altered but the retired cases; each retired case is kept
    verbatim; every object case is unchanged; no configuration case keeps a retired
    object's banks; and a rebuilt configuration case differs from the parent's only by
    those banks.
    """
    shared = {"cases", "revision", "curation", "full_profile_retention"}
    if not _same(
        {k: v for k, v in parent.items() if k not in shared},
        {k: v for k, v in child.items() if k not in shared},
    ):
        raise CurationError("child_fields_changed")
    record = child["curation"]
    by_id = {case["case_id"]: case for case in parent["cases"]}
    retired_ids = {item["decision"]["case_id"] for item in record["retired_cases"]}
    if [case["case_id"] for case in child["cases"]] != [
        case["case_id"]
        for case in parent["cases"]
        if case["case_id"] not in retired_ids
    ]:
        raise CurationError("child_case_set_differs")
    retired_subjects: dict[str, set[str]] = {}
    for item in record["retired_cases"]:
        original = by_id.get(item["decision"]["case_id"])
        if original is None or not _same(item["case"], original):
            raise CurationError(
                "retired_case_not_verbatim", item["decision"]["case_id"]
            )
        retired_subjects.setdefault(original["study_uid"], set()).add(
            original["subject"]
        )
    for case in child["cases"]:
        original = by_id[case["case_id"]]
        if not _is_configuration(case):
            if not _same(case, original):
                raise CurationError("child_object_case_changed", case["case_id"])
            continue
        gone = retired_subjects.get(case["study_uid"], set())
        prefixes = tuple(f"object/{subject}/" for subject in gone)
        profile = case["profile"]
        if any(bank.startswith(prefixes) for bank in profile["banks"]) or gone & set(
            profile["source"].get("roles", {})
        ):
            raise CurationError("retired_object_banks_remain", case["case_id"])
        if _same(case, original):
            continue
        kept = {
            bank: counts
            for bank, counts in original["profile"]["banks"].items()
            if not bank.startswith(prefixes)
        }
        if profile["banks"] != kept or any(
            not _same(case.get(key), original.get(key))
            for key in _CONFIGURATION_IDENTITY
        ):
            raise CurationError("rebuilt_configuration_differs", case["case_id"])


# --------------------------------------------------------------------- publishing


def _check_destination(destination: Path, parent: MemorySnapshot) -> None:
    if os.path.lexists(destination):
        raise CurationError("output_already_exists", str(destination))
    home = parent.path.parent.resolve()
    target = destination.resolve()
    if target == home or home in target.parents:
        raise CurationError("output_overlaps_parent", str(destination))


def _sync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _read_back(
    staged: Path, child: Mapping[str, Any], published: Mapping[str, Any]
) -> dict[str, Any]:
    """Read the staged child through the public loader and check what it must say."""
    snapshot = load_memory_snapshot(staged)
    memory = _memory_of(snapshot)

    def check(ok: bool, name: str) -> None:
        if not ok:
            raise CurationError("publication_readback_mismatch", name)

    check(snapshot.sha256 == published["sha256"], "manifest_sha256")
    check(memory["revision"] == child["revision"], "revision")
    check(
        [case["case_id"] for case in memory["cases"]]
        == [case["case_id"] for case in child["cases"]],
        "case_ids",
    )
    check(_same(memory["curation"], child["curation"]), "curation")
    cache_path = resolve_json_path(staged / "recall-preparation.json")
    cache = load_json(cache_path)
    check(
        isinstance(cache, dict)
        and cache.get("memory_manifest_sha256") == snapshot.sha256
        and cache.get("memory_revision") == memory["revision"],
        "recall_cache_identity",
    )
    fingerprint = recall_source_fingerprint(memory)
    check(
        fingerprint == child["curation"]["child_recall_source_fingerprint"]
        and cache.get("source_fingerprint") == fingerprint,
        "source_fingerprint",
    )
    # The same acceptance test production applies to a sidecar before reusing it.
    restored = prepare_recall(memory, cached=cache)
    check(restored.get("runtime_indexes_rebuilt") is True, "recall_cache")
    return {
        "checks": [
            "manifest_sha256",
            "revision",
            "case_ids",
            "curation",
            "recall_cache_identity",
            "source_fingerprint",
            "recall_cache",
        ],
        "manifest_sha256": snapshot.sha256,
        "source_fingerprint": fingerprint,
        "recall_preparation_file": cache_path.name,
    }


def publish_curated_memory(
    child: dict[str, Any], destination: Path, *, parent: MemorySnapshot
) -> dict[str, Any]:
    """Prepare, save and read back the child; publish it only if every check holds.

    The child is saved by ``save_memory`` into a hidden staging directory beside the
    destination, read back there, and renamed into place last. Any failure removes
    the staging directory and leaves nothing at the destination.
    """
    destination = Path(destination)
    _check_destination(destination, parent)
    verify_curation(_memory_of(parent), child)
    record = child["curation"]
    prepared = prepare_recall(child)
    if prepared.get("outcome") != "prepared":
        raise CurationError("recall_preparation_failed", prepared.get("reason"))
    if prepared.get("source_fingerprint") != record["child_recall_source_fingerprint"]:
        raise CurationError("recall_preparation_failed", "source_fingerprint")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.curation-", dir=destination.parent
        )
    )
    try:
        staged = staging / "memory"
        published = save_memory(child, staged, prepared_recall=prepared)
        readback = _read_back(staged, child, published)
        if os.path.lexists(destination):
            raise CurationError("output_already_exists", str(destination))
        os.rename(staged, destination)
        _sync_directory(destination.parent)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    shutil.rmtree(staging, ignore_errors=True)
    final = destination.resolve()
    sidecar = published["recall_preparation_cache"]
    return {
        "schema": RECEIPT_SCHEMA,
        "outcome": "published",
        "tool": {
            "script": Path(__file__).name,
            "knee_package": str(Path(knee.__file__).resolve().parent),
        },
        "parent": {
            "manifest": str(parent.path),
            "manifest_sha256": parent.sha256,
            "revision": record["parent"]["revision"],
            "recall_source_fingerprint": record["parent"]["recall_source_fingerprint"],
        },
        "decisions": {
            key: record["decisions"][key]
            for key in ("file_sha256", "set_sha256", "count")
        },
        "child": {
            "manifest": str(final / "manifest.json"),
            "manifest_sha256": published["sha256"],
            "revision": child["revision"],
            "recall_source_fingerprint": readback["source_fingerprint"],
            "recall_preparation": {
                "path": str(final / readback["recall_preparation_file"]),
                "sha256": sidecar["sha256"],
                "bytes": sidecar["bytes"],
            },
        },
        "counts": record["counts"],
        "retired_case_ids": [
            item["decision"]["case_id"] for item in record["retired_cases"]
        ],
        "rebuilt_configuration_case_ids": record["configuration_cases"][
            "rebuilt_case_ids"
        ],
        "readback": {
            "checks": readback["checks"],
            "manifest_sha256": readback["manifest_sha256"],
        },
    }


# ------------------------------------------------------------------ the commands


def list_fingerprints(
    snapshot: MemorySnapshot,
    *,
    expected_manifest_sha256: str,
    case_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Identity and profile fingerprint of object cases (the named ones, else all)."""
    parent = _parent_memory(snapshot, expected_manifest_sha256)
    if case_ids is None:
        selected = [case for case in parent["cases"] if not _is_configuration(case)]
    else:
        by_id = {case["case_id"]: case for case in parent["cases"]}
        _require_object_cases(case_ids, by_id, "fingerprint")
        selected = [by_id[case_id] for case_id in case_ids]
    return {
        "schema": FINGERPRINTS_SCHEMA,
        "manifest_sha256": snapshot.sha256,
        "revision": parent["revision"],
        "cases": [
            {
                "case_id": case["case_id"],
                "study_uid": case["study_uid"],
                "subject": case["subject"],
                "profile_fingerprint": case_profile_fingerprint(case),
            }
            for case in selected
        ],
    }


def _curate_command(args: argparse.Namespace) -> dict[str, Any]:
    try:
        raw = args.decisions.read_bytes()
    except OSError as error:
        raise CurationError("decisions_unreadable") from error
    decisions = parse_decisions(raw)
    snapshot = load_memory_snapshot(args.memory)
    child = curate_memory(
        snapshot, decisions, expected_manifest_sha256=args.expected_manifest_sha256
    )
    return publish_curated_memory(child, args.output_memory, parent=snapshot)


def _fingerprints_command(args: argparse.Namespace) -> dict[str, Any]:
    return list_fingerprints(
        load_memory_snapshot(args.memory),
        expected_manifest_sha256=args.expected_manifest_sha256,
        case_ids=args.case_id,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    actions = parser.add_subparsers(dest="action", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--memory",
        type=Path,
        required=True,
        help="parent memory directory, or its manifest.json (only read)",
    )
    common.add_argument(
        "--expected-manifest-sha256",
        required=True,
        help="SHA-256 of the parent's manifest.json; any other bytes are refused",
    )
    listing = actions.add_parser(
        "fingerprints",
        parents=[common],
        help="print each object case's id, study, subject and profile fingerprint",
    )
    listing.add_argument(
        "--case-id", nargs="+", help="only these object cases (default: all of them)"
    )
    curate = actions.add_parser(
        "curate",
        parents=[common],
        help="publish the curated child memory",
    )
    curate.add_argument(
        "--decisions",
        type=Path,
        required=True,
        help="independently authored decision JSON (see the module description)",
    )
    curate.add_argument(
        "--output-memory",
        type=Path,
        required=True,
        help="fresh directory to publish into; must not exist, outside the parent",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = (
            _fingerprints_command(args)
            if args.action == "fingerprints"
            else _curate_command(args)
        )
    except (ValueError, OSError) as error:
        refusal = {
            "outcome": "refused",
            "code": getattr(error, "code", None) or f"{type(error).__name__}:{error}",
            "detail": getattr(error, "detail", None),
        }
        print(json.dumps(refusal, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
