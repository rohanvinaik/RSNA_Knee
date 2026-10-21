#!/usr/bin/env python3
"""Teach one immutable memory revision from independent calls, then evaluate it.

A teaching round consumes three immutable inputs and pins each by SHA-256:

* a published parent memory (``knee.squint-memory/v1``);
* one completed squint run (``receipt.json`` and ``studies/<uid>.json[.xz]``)
  whose per-study records hold the located object observations;
* call documents in the existing ``knee.squint-report-calls/v1`` schema, bound to
  the report text of train.csv (only its Report column is read here).

Admission is the existing ``admit_report_cases``; it alone decides what an
independent call may teach. This command hands it findings read off the run's
records: a called object as ``scripts/squint_report_teaching.py`` reads it, and
a called question composite as the same ``configuration_profile`` composition
the inference recalled. A record's verdicts, values and recall evidence are
never read as calls, and train.csv labels are never calls here.

The child is published with ``save_memory`` into a fresh round root together
with its recall preparation (the parent's sidecar is reused when the recall
inputs are unchanged), read back through the ordinary loader and the production
preparation consumer, and only then marked published. An optional held-out
evaluation runs the production capacity route on the child (each study left out
of its own memory), checks each study's population against ``memory_view`` and
reports identified, abstained and wrong per condition with ``evaluate_capacity``.

The parent is never written. A child is never published over an existing path,
and nothing proceeds from an unverified publication. Running the same command
on the same round root again resumes from its pinned inputs.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.util
import itertools
import json
import lzma
import math
import os
import sys
import tempfile
import time
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from knee.diagnosis.squint_interfaces import TEACHING_ROUND_SCHEMA, teaching_round_code
from knee.diagnosis.squint_memory import (
    MemorySnapshot,
    SquintMemoryError,
    load_memory_snapshot,
    save_memory,
)
from knee.diagnosis.squint_reports import (
    ReportCallError,
    admit_report_cases,
    import_report_calls,
    read_reports,
    revision_code,
)
from knee.json_store import load_json, resolve_json_path
from knee.study.tables import LABELS

INPUTS_SCHEMA = "knee.squint-teaching-round-inputs/v1"
LINEAGE_SCHEMA = "knee.squint-teaching-round-lineage/v1"
EVALUATION_SCHEMA = "knee.squint-teaching-round-evaluation/v1"
#: The located statuses scripts/squint_report_teaching.py admits.
LOCATED_STATUSES = ("proposal", "located")
#: Verified call statuses whose study and subject are looked up in the run.
REFERENCED_STATUSES = (
    "signed",
    "abstention",
    "needs_review",
    "contradictory",
    "duplicate",
)
USES = {
    "teaching": "A revision taught by independent calls.",
    "mechanical_loop_test": (
        "Mechanical test of the teaching loop only. Never use this memory for "
        "inference, further teaching or any capacity claim."
    ),
}
ROUND_FILE = "round.json"
INPUTS_FILE = "round-inputs.json"
CHILD_DIR = "memory"
EVALUATION_DIR = "evaluation"
SCRIPT_DIR = Path(__file__).resolve().parent
CAPACITY_ROUTE = (
    "knee.diagnosis.squint_pipeline.run_squint_cli(diagnostic_mode=capacity)"
)

CapacityRunner = Callable[..., Any]


class RoundError(ValueError):
    """A named refusal; ``status`` is the round state the refusal leaves."""

    def __init__(self, code: str, status: str = "refused") -> None:
        self.code = code
        self.status = status
        super().__init__(code)


# ---------------------------------------------------------------------------
# Identity and files.
# ---------------------------------------------------------------------------


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "\0" not in value


def _uid_ok(value: object) -> bool:
    return _text(value) and Path(str(value)).name == value


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _finite_json(value: object) -> bool:
    """Whether ``save_memory`` can publish the value (it refuses NaN/inf)."""
    try:
        _canonical(value)
    except (TypeError, ValueError):
        return False
    return True


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _stable(path: Path, read: Callable[[Path], Any], code: str) -> tuple[Any, str]:
    """Read ``path`` between two digests of its bytes; refuse if it changed."""
    try:
        before = _file_sha256(path)
        value = read(path)
        after = _file_sha256(path)
    except ReportCallError as error:
        raise RoundError(f"{code}_{error.reason}") from error
    except (OSError, UnicodeError, ValueError, EOFError, lzma.LZMAError) as error:
        raise RoundError(f"{code}_unreadable") from error
    if before != after:
        raise RoundError(f"{code}_changed_during_read")
    return value, before


def _write_json(path: Path, value: object, *, exclusive: bool = False) -> str:
    """Write JSON atomically; ``exclusive`` refuses an existing path."""
    data = (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    descriptor, name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if exclusive:
            os.link(temporary, path)
        else:
            os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return hashlib.sha256(data).hexdigest()


def _source_identity() -> dict[str, Any]:
    """Digests of the code this round and its evaluation run on."""
    import knee

    package = Path(knee.__file__).resolve().parent
    repository = SCRIPT_DIR.parent
    paths = [
        *sorted((package / "diagnosis").glob("*.py")),
        *sorted((package / "collapse").glob("*.py")),
        *sorted((package / "study").glob("*.py")),
        package / "json_store.py",
        SCRIPT_DIR / "squint_training_round.py",
        SCRIPT_DIR / "evaluate_squint_capacity.py",
    ]
    files: dict[str, str] = {}
    for path in paths:
        if not path.is_file():
            continue
        try:
            name = str(path.relative_to(repository))
        except ValueError:
            name = str(path)
        files[name] = _file_sha256(path)
    return {"files": files, "sha256": _digest(files)}


# ---------------------------------------------------------------------------
# Inputs: parent, reports, calls and the observation run.
# ---------------------------------------------------------------------------


def _parent_round(directory: Path, sha: str) -> tuple[dict[str, Any], dict | None]:
    """A parent published by a round must come from a completed teaching one."""
    manifest_path = directory.parent / ROUND_FILE
    if directory.name != CHILD_DIR or not manifest_path.is_file():
        return {"status": "not_a_round_child"}, None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RoundError("parent_round_manifest_unreadable") from error
    if teaching_round_code(manifest) != "valid" or manifest.get("status") not in (
        "published",
        "evaluated",
    ):
        raise RoundError("parent_publication_incomplete")
    if manifest["child"].get("manifest_sha256") != sha:
        raise RoundError("parent_round_child_mismatch")
    use = manifest.get("use")
    if not isinstance(use, Mapping) or use.get("kind") != "teaching":
        raise RoundError("parent_marked_not_for_use")
    evaluation = manifest.get("evaluation")
    previous = (
        evaluation
        if isinstance(evaluation, Mapping) and evaluation.get("status") == "evaluated"
        else None
    )
    info = {
        "status": "round_child",
        "path": str(manifest_path),
        "sha256": _file_sha256(manifest_path),
    }
    return info, previous


def _parent(
    path: Path, expected: str | None
) -> tuple[MemorySnapshot, dict[str, Any], dict | None]:
    try:
        snapshot = load_memory_snapshot(path)
    except SquintMemoryError as error:
        raise RoundError("parent_" + error.code) from error
    if snapshot.memory is None or not snapshot.sha256:
        raise RoundError("parent_memory_snapshot_invalid")
    memory = snapshot.memory
    manifest_sha256 = snapshot.sha256
    if expected is not None and snapshot.sha256 != expected:
        raise RoundError("parent_manifest_sha256_mismatch")
    rounds = memory.get("teaching_rounds", [])
    if not isinstance(rounds, list):
        raise RoundError("parent_teaching_rounds_invalid")
    directory = snapshot.path.parent
    parent_round, previous = _parent_round(directory, manifest_sha256)
    return (
        snapshot,
        {
            "path": str(directory),
            "manifest_sha256": manifest_sha256,
            "revision": memory["revision"],
            "case_count": len(memory["cases"]),
            "round": parent_round,
        },
        previous,
    )


def _parent_preparation(
    directory: Path, snapshot: MemorySnapshot
) -> tuple[dict | None, dict[str, Any]]:
    """The parent's sidecar, usable only if it is bound to these manifest bytes."""
    memory = snapshot.memory
    path = resolve_json_path(directory / "recall-preparation.json")
    if not path.is_file():
        return None, {"status": "missing"}
    try:
        cache, sha = _stable(path, load_json, "parent_recall_preparation")
    except RoundError as error:
        return None, {"status": error.code, "path": str(path)}
    bound = (
        isinstance(cache, dict)
        and memory is not None
        and cache.get("memory_manifest_sha256") == snapshot.sha256
        and cache.get("memory_revision") == memory["revision"]
    )
    return (cache if bound else None), {
        "status": "bound_to_parent" if bound else "not_bound_to_parent",
        "path": str(path),
        "sha256": sha,
    }


def _call_uid(result: Mapping[str, Any]) -> object:
    uid = result.get("study_uid")
    record = result.get("record")
    if uid is None and isinstance(record, Mapping):
        uid = record.get("study_uid")
    return uid


def _calls(
    paths: Sequence[Path], reports: dict[str, str], scope: set[str] | None
) -> tuple[list[dict], list[dict[str, Any]]]:
    """Validate each call document with the existing importer; keep the scope."""
    resolved = [path.resolve() for path in paths]
    if len(set(resolved)) != len(resolved):
        raise RoundError("call_source_repeated")
    calls: list[dict] = []
    sources: list[dict[str, Any]] = []
    for path in resolved:
        results, sha = _stable(
            path, lambda item: import_report_calls(item, reports), "call_source"
        )
        # A record naming no study stays in scope and keeps its named refusal.
        kept = [
            result
            for result in results
            if scope is None
            or not isinstance(_call_uid(result), str)
            or _call_uid(result) in scope
        ]
        calls.extend(kept)
        sources.append(
            {
                "source": str(path),
                "sha256": sha,
                "kind": "report_calls",
                "records": len(results),
                "in_scope": len(kept),
                "validated_statuses": dict(
                    sorted(Counter(str(row.get("status")) for row in kept).items())
                ),
            }
        )
    return calls, sources


def _references(calls: Iterable[Mapping[str, Any]]) -> dict[str, set[str]]:
    """Which study and subject each verified call names."""
    refs: dict[str, set[str]] = {}
    for call in calls:
        if call.get("status") not in REFERENCED_STATUSES:
            continue
        uid, subject = call.get("study_uid"), call.get("subject")
        if not _text(uid) or not _text(subject):
            continue
        if not _uid_ok(uid):
            raise RoundError("study_uid_invalid_for_record_path")
        refs.setdefault(str(uid), set()).add(str(subject))
    return refs


def _observations(
    run_root: Path, uids: Iterable[str]
) -> tuple[dict[str, Any], dict[str, Mapping[str, Any]]]:
    """Pin the run's receipt and the records of the called studies."""
    run = run_root.resolve()
    receipt_path = run / "receipt.json"
    if not receipt_path.is_file():
        raise RoundError("observation_receipt_missing")
    receipt, receipt_sha = _stable(receipt_path, load_json, "observation_receipt")
    work = receipt.get("work") if isinstance(receipt, Mapping) else None
    if (
        not isinstance(receipt, Mapping)
        or receipt.get("schema") != "knee.squint-run/v1"
        or receipt.get("action") not in ("infer", "capacity")
        or receipt.get("source_mode") != "raw_squint_case_recall"
        or not isinstance(work, Mapping)
        or not isinstance(work.get("studies"), list)
    ):
        raise RoundError("observation_receipt_invalid")
    revision = receipt.get("memory_revision")
    memory_sha = receipt.get("memory_manifest_sha256")
    if not _text(revision) or not _text(memory_sha):
        raise RoundError("observation_memory_identity_missing")
    listed: dict[str, str] = {}
    for row in work["studies"]:
        uid = row.get("study_uid") if isinstance(row, Mapping) else None
        evidence = row.get("evidence_path") if isinstance(row, Mapping) else None
        if not _uid_ok(uid) or uid in listed or not _text(evidence):
            raise RoundError("observation_receipt_study_invalid")
        listed[str(uid)] = str(evidence)
    records: dict[str, Mapping[str, Any]] = {}
    identities: dict[str, dict[str, Any]] = {}
    for uid in sorted(uids):
        if uid not in listed:
            identities[uid] = {"status": "not_in_run"}
            continue
        path = (run / listed[uid]).resolve()
        try:
            path.relative_to(run)
        except ValueError as error:
            raise RoundError(f"observation_evidence_outside_run:{uid}") from error
        try:
            record, sha = _stable(path, load_json, "observation_record")
        except RoundError as error:
            raise RoundError(f"{error.code}:{uid}") from error
        if (
            not isinstance(record, Mapping)
            or record.get("schema") != "knee.squint-study/v1"
            or record.get("study_uid") != uid
        ):
            raise RoundError(f"observation_record_identity_mismatch:{uid}")
        if record.get("memory_revision") != revision:
            raise RoundError(f"observation_record_memory_mismatch:{uid}")
        exclusion = record.get("capacity_exclusion")
        records[uid] = record
        identities[uid] = {
            "status": str(record.get("study_status", "unstated")),
            "path": str(path),
            "sha256": sha,
            "capacity_exclusion": (
                exclusion.get("exclusion_status")
                if isinstance(exclusion, Mapping)
                else None
            ),
        }
    return {
        "run_root": str(run),
        "receipt_sha256": receipt_sha,
        "action": receipt["action"],
        "memory_revision": revision,
        "memory_manifest_sha256": memory_sha,
        "listed_study_count": len(listed),
        "records": identities,
    }, records


# ---------------------------------------------------------------------------
# Findings read off the run's records.
# ---------------------------------------------------------------------------


def _region_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, Mapping) for item in value)


def object_finding(
    objects: Mapping[str, Any], uid: str, subject: str, located: Sequence[str]
) -> tuple[dict | None, str]:
    """One called object, read by the rule of scripts/squint_report_teaching.py.

    That rule is a located status and the object's own profile. Regions that are
    not a list of mappings, and readings ``save_memory`` cannot publish (NaN or
    infinity), are refused here by name instead of failing the publication.
    """
    item = objects.get(subject)
    if not isinstance(item, Mapping):
        return None, "object_not_in_record"
    if item.get("status") not in located:
        return None, "object_not_located"
    profile = item.get("profile")
    if not isinstance(profile, Mapping) or profile.get("subject") != subject:
        return None, "object_profile_unavailable"
    regions = item.get("regions", [])
    if not _region_list(regions):
        return None, "object_regions_invalid"
    if not _finite_json(profile) or not _finite_json(regions):
        return None, "object_reading_not_finite_json"
    return {
        "study_uid": uid,
        "subject": subject,
        "status": item["status"],
        "mode": "cheap",
        "profile": profile,
        "regions": regions,
    }, "object_finding"


def composite_finding(
    objects: Mapping[str, Any], uid: str, subject: str, located: Sequence[str]
) -> tuple[dict | None, str]:
    """One called question composite, composed exactly as the inference does.

    ``squint_pipeline._recall_question`` composes every declared object whose
    retained profile is not None, in the one writer (procedure) those profiles
    share, and composes nothing when they mix writers. The composite is taught
    only when each composed role was located; it is a proposal unless all of
    them are located.
    """
    from knee.diagnosis.declarations import question_for
    from knee.diagnosis.squint_configurations import (
        ConfigurationProfileError,
        configuration_profile,
    )

    try:
        declaration = question_for(subject.removeprefix("diagnosis/"))
    except KeyError:
        return None, "composite_question_unknown"
    if declaration.subject != subject:
        return None, "composite_question_unknown"
    roles: dict[str, dict[str, Any]] = {}
    statuses: dict[str, str] = {}
    regions: list[dict[str, Any]] = []
    for role in declaration.objects:
        item = objects.get(role)
        if not isinstance(item, Mapping) or item.get("profile") is None:
            continue
        if item.get("status") not in located:
            return None, "composite_role_not_located"
        role_regions = item.get("regions", [])
        if not _region_list(role_regions):
            return None, "composite_role_regions_invalid"
        roles[role] = dict(item["profile"])
        statuses[role] = str(item["status"])
        regions.extend({**region, "subject": role} for region in role_regions)
    procedures = {
        (profile.get("source") or {}).get("procedure")
        if isinstance(profile, Mapping)
        else None
        for profile in roles.values()
    }
    if len(procedures) > 1:
        return None, "composite_mixed_procedures"
    procedure = next(iter(procedures)) if procedures else None
    if procedure is not None and not isinstance(procedure, str):
        return None, "composite_procedure_unavailable"
    try:
        profile = (
            configuration_profile(roles, declaration.question_id, procedure=procedure)
            if procedure is not None
            else configuration_profile(roles, declaration.question_id)
        )
    except ConfigurationProfileError as error:
        return None, "composite_" + error.code
    if not profile["banks"]:
        return None, "composite_silent"
    if not _finite_json(profile) or not _finite_json(regions):
        return None, "composite_reading_not_finite_json"
    status = (
        "located"
        if all(value == "located" for value in statuses.values())
        else "proposal"
    )
    return {
        "study_uid": uid,
        "subject": declaration.subject,
        "status": status,
        "mode": "cheap",
        "profile": profile,
        "regions": regions,
    }, "composite_finding"


def _findings(
    records: Mapping[str, Mapping[str, Any]], refs: Mapping[str, set[str]]
) -> tuple[list[dict], dict[str, int]]:
    findings: list[dict] = []
    codes: Counter = Counter()
    for uid in sorted(refs):
        record = records.get(uid)
        objects = record.get("objects") if isinstance(record, Mapping) else None
        if not isinstance(objects, Mapping):
            codes[
                "record_unavailable" if record is None else "record_objects_missing"
            ] += len(refs[uid])
            continue
        for subject in sorted(refs[uid]):
            read = (
                composite_finding
                if subject.startswith("diagnosis/")
                else object_finding
            )
            finding, code = read(objects, uid, subject, LOCATED_STATUSES)
            codes[code] += 1
            if finding is not None:
                findings.append(finding)
    return findings, dict(sorted(codes.items()))


def _admission_summary(
    receipt: Mapping[str, Any], built: Mapping[str, int], offered: int
) -> dict[str, Any]:
    retained = receipt.get("retained_calls", {})

    def count(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
        return dict(sorted(Counter(str(row.get(key)) for row in rows).items()))

    return {
        "schema": receipt.get("schema"),
        "receipt_sha256": _digest(receipt),
        "added_case_count": receipt["added_case_count"],
        "admitted": [
            {
                key: row[key]
                for key in (
                    "case_id",
                    "study_uid",
                    "subject",
                    "condition_calls",
                    "call_ids",
                )
            }
            for row in receipt["admitted"]
        ],
        "rejected_by_reason": count(retained.get("rejected", ()), "status"),
        "needs_review": len(retained.get("needs_review", ())),
        "needs_review_call_ids": sorted(
            str(row.get("call_id")) for row in retained.get("needs_review", ())
        ),
        "abstentions": len(retained.get("abstentions", ())),
        "duplicates": len(retained.get("duplicates", ())),
        "contradictory": len(retained.get("contradictory", ())),
        "held_calls_by_code": count(receipt.get("held_calls", ()), "code"),
        "unmatched_calls_by_code": count(receipt.get("unmatched_calls", ()), "code"),
        "skipped_findings_by_code": count(receipt.get("skipped_findings", ()), "code"),
        "findings_without_calls": receipt.get("findings_without_calls"),
        "prior_opposition": len(receipt.get("prior_opposition", ())),
        "findings_offered": offered,
        "findings_read_by_code": dict(built),
        "trust_added": receipt.get("trust_added"),
        "censors_added": receipt.get("censors_added"),
    }


# ---------------------------------------------------------------------------
# Publication and readback.
# ---------------------------------------------------------------------------


def _pin_inputs(root: Path, inputs: Mapping[str, Any]) -> bool:
    """Own a fresh round root for these inputs, or resume one pinned to them."""
    path = root / INPUTS_FILE
    if path.is_file():
        try:
            pinned = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise RoundError("round_root_inputs_unreadable") from error
        if _digest(pinned) != _digest(inputs):
            raise RoundError("round_root_inputs_mismatch")
        return True
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise RoundError("round_root_not_fresh")
    root.mkdir(parents=True, exist_ok=True)
    try:
        _write_json(path, inputs, exclusive=True)
    except FileExistsError as error:
        raise RoundError("round_root_not_fresh") from error
    return False


def _publish(
    child: dict, destination: Path, cache: dict | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    from knee.diagnosis.squint_locator import prepare_recall

    started = time.perf_counter()
    prepared = (
        prepare_recall(child, cached=cache)
        if cache is not None
        else prepare_recall(child)
    )
    seconds = time.perf_counter() - started
    if not isinstance(prepared, dict) or prepared.get("outcome") != "prepared":
        raise RoundError("child_recall_preparation_failed", "incomplete")
    source = (
        "parent_preparation_reused"
        if prepared.get("runtime_indexes_rebuilt") is True
        else "computed"
    )
    started = time.perf_counter()
    try:
        publication = save_memory(child, destination, prepared_recall=prepared)
    except SquintMemoryError as error:
        raise RoundError(
            "child_publication_failed:" + error.code, "incomplete"
        ) from error
    except (OSError, ValueError) as error:
        raise RoundError(
            "child_publication_failed:" + type(error).__name__, "incomplete"
        ) from error
    return publication, {
        "source": source,
        "preparation_seconds": seconds,
        "publication_seconds": time.perf_counter() - started,
    }


def _verify_child(
    destination: Path, planned: Mapping[str, Any]
) -> tuple[MemorySnapshot, dict[str, Any], dict[str, Any]]:
    """Read the child back exactly as the next run will, or name what is wrong.

    Returns the snapshot, the preparation restored from its sidecar by the
    production consumer, and the readback record.
    """
    from knee.diagnosis.squint_locator import prepare_recall

    try:
        snapshot = load_memory_snapshot(destination)
    except SquintMemoryError as error:
        raise RoundError("child_" + error.code, "incomplete") from error
    memory = snapshot.memory
    if memory is None or not snapshot.sha256:
        raise RoundError("child_memory_snapshot_invalid", "incomplete")
    admissions = memory.get("report_admissions") or [None]
    lineage = memory.get("teaching_rounds") or [None]
    checks = (
        ("revision", memory.get("revision") == planned["revision"]),
        (
            "parent_revision",
            memory.get("parent_revision") == planned["parent_revision"],
        ),
        ("admission_receipt", _digest(admissions[-1]) == planned["receipt_sha256"]),
        ("lineage", _digest(lineage[-1]) == _digest(planned["lineage"])),
        (
            "case_ids",
            [case.get("case_id") for case in memory["cases"]] == planned["case_ids"],
        ),
    )
    for name, passed in checks:
        if not passed:
            raise RoundError("child_publication_mismatch:" + name, "incomplete")
    cache_path = resolve_json_path(destination / "recall-preparation.json")
    if not cache_path.is_file():
        raise RoundError("child_recall_preparation_missing", "incomplete")
    try:
        cache, cache_sha = _stable(cache_path, load_json, "child_recall_preparation")
    except RoundError as error:
        raise RoundError(error.code, "incomplete") from error
    if (
        not isinstance(cache, dict)
        or cache.get("memory_manifest_sha256") != snapshot.sha256
        or cache.get("memory_revision") != memory.get("revision")
    ):
        raise RoundError("child_recall_preparation_not_bound", "incomplete")
    restored = prepare_recall(memory, cached=cache)
    if restored.get("runtime_indexes_rebuilt") is not True:
        raise RoundError("child_recall_preparation_not_reusable", "incomplete")
    return (
        snapshot,
        restored,
        {
            "loader": "knee.diagnosis.squint_memory.load_memory_snapshot",
            "status": snapshot.status,
            "checks": [name for name, _ in checks],
            "recall_preparation": {
                "path": str(cache_path),
                "sha256": cache_sha,
                "consumer": "knee.diagnosis.squint_locator.prepare_recall(cached=...)",
                "runtime_indexes_rebuilt": True,
            },
            "full_profile_retention": memory.get("full_profile_retention"),
        },
    )


# ---------------------------------------------------------------------------
# Held-out evaluation.
# ---------------------------------------------------------------------------


def _capacity_evaluator() -> Callable[[Path, Path], dict]:
    name = "_squint_training_round_capacity_report"
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(
            name, SCRIPT_DIR / "evaluate_squint_capacity.py"
        )
        if spec is None or spec.loader is None:
            raise RoundError("evaluation_reporter_unavailable")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return module.evaluate_capacity


def _production_capacity(namespace: argparse.Namespace, **kwargs: Any) -> Any:
    from knee.diagnosis.squint_pipeline import run_squint_cli

    return run_squint_cli(namespace, **kwargs)


def _write_template(path: Path, uids: Sequence[str]) -> None:
    from knee.diagnosis.submission import SUBMISSION_COLUMNS

    lines = [",".join(SUBMISSION_COLUMNS)]
    lines.extend(uid + "," * len(LABELS) for uid in uids)
    with path.open("x", encoding="utf-8", newline="") as stream:
        stream.write("\n".join(lines) + "\n")


def exclusion_checks(
    memory: dict,
    prepared: Mapping[str, Any],
    manifest_sha: str,
    run: Path,
    uids: Sequence[str],
) -> dict[str, Any]:
    """Compare each evaluated study's population with the one memory view.

    The view is built from the child and the same published preparation the
    capacity route reads, so its projected preparation is the population that
    study's recall should have consumed.
    """
    from knee.diagnosis.squint_memory_view import MemoryViewError, memory_view

    source = {
        **memory,
        "prepared_recall": prepared,
        "memory_manifest_sha256": manifest_sha,
    }
    rows: dict[str, dict[str, Any]] = {}
    for uid in uids:
        try:
            record = load_json(run / "studies" / f"{uid}.json")
        except (OSError, ValueError, EOFError, lzma.LZMAError):
            rows[uid] = {"agree": False, "code": "evaluation_record_unreadable"}
            continue
        exclusion = (
            record.get("capacity_exclusion") if isinstance(record, dict) else None
        )
        exclusion = exclusion if isinstance(exclusion, Mapping) else {}
        try:
            view = memory_view(source, exclude_study_uids=(uid,))
        except MemoryViewError as error:
            rows[uid] = {"agree": False, "code": error.code}
            continue
        projected = view.get("prepared_recall")
        reachable = sum(
            1
            for case in view["cases"]
            if isinstance(case, Mapping) and case.get("study_uid") == uid
        )
        row = {
            "view_preparation_code": view["view"]["preparation_code"],
            "view_projected_fingerprint": (
                projected.get("source_fingerprint")
                if isinstance(projected, Mapping)
                else None
            ),
            "run_consumed_fingerprint": exclusion.get("consumed_case_fingerprint"),
            "view_case_count": len(view["cases"]),
            "run_filtered_case_count": exclusion.get("filtered_case_count"),
            "excluded_case_count": len(memory["cases"]) - len(view["cases"]),
            "excluded_cases_reachable": reachable,
            "run_exclusion_status": exclusion.get("exclusion_status"),
        }
        row["agree"] = (
            row["view_preparation_code"] == "prepared"
            and row["view_projected_fingerprint"] == row["run_consumed_fingerprint"]
            and row["view_case_count"] == row["run_filtered_case_count"]
            and row["run_exclusion_status"] == "applied"
            and reachable == 0
        )
        rows[uid] = row
        del view, projected
    return {
        "view_api": "knee.diagnosis.squint_memory_view.memory_view",
        "studies": rows,
        "agree": bool(rows) and all(row["agree"] for row in rows.values()),
    }


def _trajectory(
    previous: Mapping[str, Any] | None,
    summary: Mapping[str, Any],
    point: Mapping[str, Any],
) -> dict[str, Any]:
    """The course of learning: comparable evaluations side by side, never summed."""
    points: list[Mapping[str, Any]] = []
    state = {"status": "unavailable", "reason": "parent_has_no_round_evaluation"}
    if previous is not None:
        comparable = (
            previous.get("request", {}).get("study_uids")
            == summary["request"]["study_uids"]
            and previous.get("labels", {}).get("sha256") == summary["labels"]["sha256"]
            and previous.get("source_identity_sha256")
            == summary["source_identity_sha256"]
        )
        if comparable and isinstance(previous.get("point"), Mapping):
            points.append(previous["point"])
            state = {"status": "comparable"}
        else:
            state = {
                "status": "not_comparable",
                "reason": "study_set_labels_or_source_differ",
            }
    points.append(point)
    return {"previous": state, "points": points}


def _evaluate(
    root: Path,
    child: MemorySnapshot,
    prepared: Mapping[str, Any],
    request: Mapping[str, Any],
    runner: CapacityRunner,
    previous: Mapping[str, Any] | None,
) -> dict[str, Any]:
    request_sha = _digest(request)
    base = root / EVALUATION_DIR / request_sha[:16]
    attempt = base / "attempt-1"
    for number in itertools.count(1):
        attempt = base / f"attempt-{number}"
        if not attempt.exists():
            break
        done = attempt / "evaluation.json"
        if done.is_file():
            try:
                kept = json.loads(done.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                continue
            if (
                kept.get("request_sha256") == request_sha
                and kept.get("child_manifest_sha256") == child.sha256
            ):
                return {**kept, "resumed": True}
        # An incomplete or failed attempt stays where it is, as evidence.
    attempt.mkdir(parents=True)
    _write_json(attempt / "request.json", request, exclusive=True)
    uids = list(request["study_uids"])
    template = attempt / "template.csv"
    _write_template(template, uids)
    run = attempt / "run"
    namespace = argparse.Namespace(
        diagnostic_mode="capacity",
        diagnostic_memory=child.path.parent,
        diagnostic_output=run,
        diagnostic_submission_template=template,
        root=Path(request["root"]),
        study_uid=uids,
        workers=request["workers"],
        squint_time_limit=request["time_limit_seconds"],
        draw=False,
    )
    failure: dict[str, Any] = {
        "schema": EVALUATION_SCHEMA,
        "status": "failed",
        "attempt": str(attempt),
        "request_sha256": request_sha,
        "child_manifest_sha256": child.sha256,
    }
    started = time.perf_counter()
    try:
        runner(namespace, prepared_memory_snapshot=child)
    # Any failure of the evaluation run leaves the verified child published and
    # is kept by name beside the attempt; it never becomes an evaluation.
    except Exception as error:  # noqa: BLE001
        failure["code"] = f"evaluation_run_failed:{type(error).__name__}:{error}"[:300]
        _write_json(attempt / "failure.json", failure, exclusive=True)
        return failure
    run_seconds = time.perf_counter() - started
    try:
        receipt = load_json(run / "receipt.json")
    except (OSError, ValueError, EOFError, lzma.LZMAError):
        receipt = None
    if (
        not isinstance(receipt, Mapping)
        or not child.sha256
        or receipt.get("memory_manifest_sha256") != child.sha256
        or child.memory is None
        or receipt.get("memory_revision") != child.memory.get("revision")
    ):
        failure["code"] = "evaluation_memory_mismatch"
        _write_json(attempt / "failure.json", failure, exclusive=True)
        return failure
    labels = Path(request["labels"]["path"])
    try:
        report = _capacity_evaluator()(run, labels)
    except (ValueError, OSError) as error:
        failure["code"] = "evaluation_report_refused:" + str(error)[:200]
        _write_json(attempt / "failure.json", failure, exclusive=True)
        return failure
    if report["labels"]["sha256"] != request["labels"]["sha256"]:
        failure["code"] = "evaluation_labels_changed"
        _write_json(attempt / "failure.json", failure, exclusive=True)
        return failure
    report_sha = _write_json(attempt / "report.json", report, exclusive=True)
    if child.memory is None or child.sha256 is None:
        failure["code"] = "evaluation_memory_mismatch"
        _write_json(attempt / "failure.json", failure, exclusive=True)
        return failure
    checks = exclusion_checks(child.memory, prepared, child.sha256, run, uids)
    point = {
        "revision": child.memory.get("revision"),
        "manifest_sha256": child.sha256,
        "per_condition": report["per_condition"],
    }
    summary: dict[str, Any] = {
        "schema": EVALUATION_SCHEMA,
        "status": "evaluated" if checks["agree"] else "exclusion_mismatch",
        "attempt": str(attempt),
        "request": dict(request),
        "request_sha256": request_sha,
        "child_manifest_sha256": child.sha256,
        "source_identity_sha256": request["source_identity_sha256"],
        "run": {
            "path": str(run),
            "route": CAPACITY_ROUTE,
            "receipt_sha256": report["run"]["receipt_sha256"],
            "study_uids": report["run"]["study_uids"],
            "seconds": run_seconds,
        },
        "labels": report["labels"],
        "report": {"path": str(attempt / "report.json"), "sha256": report_sha},
        "exclusion": checks,
        "per_condition": report["per_condition"],
        "point": point,
    }
    summary["trajectory"] = _trajectory(previous, summary, point)
    _write_json(attempt / "evaluation.json", summary, exclusive=True)
    return summary


def _completed_evaluations(root: Path, child_sha: str) -> list[dict[str, Any]]:
    """Every completed evaluation of this child kept under the round root."""
    kept = []
    for path in sorted((root / EVALUATION_DIR).glob("*/attempt-*/evaluation.json")):
        try:
            summary = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if (
            isinstance(summary, dict)
            and summary.get("child_manifest_sha256") == child_sha
            and summary.get("status") in ("evaluated", "exclusion_mismatch")
        ):
            kept.append(summary)
    return kept


# ---------------------------------------------------------------------------
# The round.
# ---------------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--parent-memory", type=Path, required=True)
    parser.add_argument("--expect-parent-sha256", help="pin the parent manifest bytes")
    parser.add_argument(
        "--observations",
        type=Path,
        required=True,
        help="completed squint run root: receipt.json and studies/",
    )
    parser.add_argument(
        "--reports",
        type=Path,
        required=True,
        help="train.csv; only the Report column is read, to verify each call",
    )
    parser.add_argument("--calls", type=Path, action="append", required=True)
    parser.add_argument("--revision", required=True, help="the child revision name")
    parser.add_argument("--out", type=Path, required=True, help="the round root")
    parser.add_argument(
        "--study-uid", action="append", help="limit a small round to these studies"
    )
    parser.add_argument("--use", choices=tuple(USES), default="teaching")
    parser.add_argument("--note", default="")
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--root", type=Path, help="raw competition root (evaluation)")
    parser.add_argument("--labels", type=Path, help="official train.csv (evaluation)")
    parser.add_argument("--evaluate-study-uid", action="append")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--time-limit", type=float, default=1800.0)
    return parser


def parse_options(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return _parser().parse_args(argv)


def _uids(values: Sequence[str] | None, code: str) -> list[str] | None:
    if not values:
        return None
    if len(set(values)) != len(values) or not all(_uid_ok(uid) for uid in values):
        raise RoundError(code)
    return list(values)


def _evaluation_request(
    options: argparse.Namespace, scope: list[str] | None, source_sha: str
) -> dict[str, Any] | None:
    if not options.evaluate:
        return None
    uids = _uids(options.evaluate_study_uid, "evaluation_study_uids_invalid") or scope
    if not uids:
        raise RoundError("evaluation_study_uids_required")
    if options.root is None or options.labels is None:
        raise RoundError("evaluation_root_and_labels_required")
    if type(options.workers) is not int or not 1 <= options.workers <= 3:
        raise RoundError("evaluation_workers_must_be_1_to_3")
    if not math.isfinite(options.time_limit) or options.time_limit <= 0:
        raise RoundError("evaluation_time_limit_invalid")
    labels = options.labels.resolve()
    try:
        labels_sha = _file_sha256(labels)
    except OSError as error:
        raise RoundError("evaluation_labels_unreadable") from error
    return {
        "schema": EVALUATION_SCHEMA,
        "route": CAPACITY_ROUTE,
        "root": str(options.root.resolve()),
        "labels": {"path": str(labels), "sha256": labels_sha},
        "study_uids": uids,
        "workers": options.workers,
        "time_limit_seconds": float(options.time_limit),
        "source_identity_sha256": source_sha,
    }


def _overlaps(first: Path, second: Path) -> bool:
    return first == second or first in second.parents or second in first.parents


def run_round(
    options: argparse.Namespace, *, capacity_runner: CapacityRunner | None = None
) -> dict[str, Any]:
    """Run one teaching round and return its teaching-round manifest."""
    started = time.perf_counter()
    root = Path(options.out).resolve()
    source = _source_identity()
    manifest: dict[str, Any] = {
        "schema": TEACHING_ROUND_SCHEMA,
        "status": "refused",
        "round_root": str(root),
        "use": {
            "kind": options.use,
            "statement": USES[options.use],
            "note": options.note,
        },
        "parent": {"revision": "unavailable", "manifest_sha256": "unavailable"},
        "calls": [],
        "admission": {},
        "child": None,
        "evaluation": {"status": "not_requested"},
        "source_identity": source,
        "seconds": {},
    }
    owned = False
    try:
        if not _text(options.revision):
            raise RoundError("revision_invalid")
        scope_list = _uids(options.study_uid, "study_uids_invalid")
        scope = set(scope_list) if scope_list is not None else None
        manifest["study_scope"] = sorted(scope) if scope is not None else None
        request = _evaluation_request(options, scope_list, source["sha256"])

        parent_snapshot, parent, previous = _parent(
            Path(options.parent_memory), options.expect_parent_sha256
        )
        manifest["parent"] = parent
        if revision_code(options.revision, parent["revision"]) != "new":
            raise RoundError("revision_not_new")
        if _overlaps(root, Path(parent["path"])):
            raise RoundError("round_root_overlaps_parent")
        reports_path = Path(options.reports).resolve()
        reports, reports_sha = _stable(reports_path, read_reports, "reports")
        calls, sources = _calls([Path(path) for path in options.calls], reports, scope)
        manifest["calls"] = sources
        manifest["reports"] = {"path": str(reports_path), "sha256": reports_sha}
        refs = _references(calls)
        observations, records = _observations(Path(options.observations), refs)
        manifest["observations"] = observations
        inputs = {
            "schema": INPUTS_SCHEMA,
            "parent": {
                key: parent[key] for key in ("path", "manifest_sha256", "revision")
            },
            "child_revision": options.revision,
            "use": options.use,
            "reports": manifest["reports"],
            "calls": [
                {"source": row["source"], "sha256": row["sha256"]} for row in sources
            ],
            "observations": {
                "run_root": observations["run_root"],
                "receipt_sha256": observations["receipt_sha256"],
                "records": {
                    uid: row.get("sha256", row["status"])
                    for uid, row in observations["records"].items()
                },
            },
            "study_scope": sorted(scope) if scope is not None else None,
            "located_statuses": list(LOCATED_STATUSES),
        }
        inputs_sha = _digest(inputs)
        manifest["inputs_sha256"] = inputs_sha
        resumed = _pin_inputs(root, inputs)
        owned = True
        manifest["resumed"] = resumed
        manifest["seconds"]["inputs"] = time.perf_counter() - started

        findings, built = _findings(records, refs)
        del records
        parent_memory = parent_snapshot.memory
        if parent_memory is None:
            raise RoundError("parent_memory_snapshot_invalid")
        try:
            child = admit_report_cases(
                parent_memory,
                findings,
                calls,
                options.revision,
                reports=reports,
                located_statuses=LOCATED_STATUSES,
            )
        except ReportCallError as error:
            raise RoundError("admission_" + error.reason) from error
        receipt = child["report_admissions"][-1]
        lineage = {
            "schema": LINEAGE_SCHEMA,
            "revision": options.revision,
            "parent_revision": parent["revision"],
            "parent_manifest_sha256": parent["manifest_sha256"],
            "inputs_sha256": inputs_sha,
            "use": options.use,
            "admission_receipt_sha256": _digest(receipt),
        }
        child["teaching_rounds"] = [*parent_memory.get("teaching_rounds", []), lineage]
        planned = {
            "revision": options.revision,
            "parent_revision": parent["revision"],
            "receipt_sha256": _digest(receipt),
            "lineage": lineage,
            "case_ids": [case.get("case_id") for case in child["cases"]],
        }
        manifest["admission"] = _admission_summary(receipt, built, len(findings))
        del findings, calls, reports
        destination = root / CHILD_DIR
        manifest["seconds"]["admission"] = time.perf_counter() - started

        if destination.exists():
            # Resume: the existing child is verified below before anything else.
            publication: dict[str, Any] = {"publication": "resumed_existing"}
        else:
            # Beside the child before it exists, so that no later round can take
            # it as a parent until its readback here has succeeded.
            manifest["status"] = "incomplete"
            manifest["child"] = {
                "revision": options.revision,
                "path": str(destination),
                "state": "publication_pending",
            }
            _write_round(root, manifest)
            cache, preparation = _parent_preparation(
                Path(parent["path"]), parent_snapshot
            )
            receipt_out, timing = _publish(child, destination, cache)
            publication = {
                "publication": "published_now",
                "parent_recall_preparation": preparation,
                "recall_preparation_source": timing["source"],
                "seconds": timing,
                "save_receipt_sha256": receipt_out["sha256"],
            }
            del cache
        added = receipt["added_case_count"]
        del child, receipt, parent_memory, parent_snapshot
        gc.collect()
        child_snapshot, restored, readback = _verify_child(destination, planned)
        if child_snapshot.memory is None or child_snapshot.sha256 is None:
            raise RoundError("child_memory_snapshot_invalid", "incomplete")
        if request is None:
            del restored
        if publication.get("save_receipt_sha256") not in (None, child_snapshot.sha256):
            raise RoundError("child_publication_mismatch:manifest_sha256", "incomplete")
        manifest["child"] = {
            "revision": options.revision,
            "parent_revision": parent["revision"],
            "path": str(destination),
            "manifest_sha256": child_snapshot.sha256,
            "case_count": len(child_snapshot.memory["cases"]),
            "added_case_count": added,
            "lineage": lineage,
            **publication,
            "readback": readback,
        }
        manifest["status"] = "published"
        manifest["seconds"]["published"] = time.perf_counter() - started
        if request is not None:
            _write_round(root, manifest)
            runner = capacity_runner or _production_capacity
            evaluation = _evaluate(
                root, child_snapshot, restored, request, runner, previous
            )
            del restored
            manifest["evaluation"] = evaluation
            manifest["seconds"]["evaluated"] = time.perf_counter() - started
        completed = _completed_evaluations(root, child_snapshot.sha256)
        manifest["evaluations"] = [
            {key: row.get(key) for key in ("status", "attempt", "request_sha256")}
            for row in completed
        ]
        if request is None and completed:
            manifest["evaluation"] = {**completed[-1], "resumed": True}
        if manifest["evaluation"].get("status") == "evaluated":
            manifest["status"] = "evaluated"
        _write_round(root, manifest)
    except RoundError as error:
        manifest["status"] = error.status
        manifest["failure"] = {"code": error.code}
        if owned:
            _write_round(root, manifest)
    return manifest


def _write_round(root: Path, manifest: Mapping[str, Any]) -> None:
    code = teaching_round_code(manifest)
    if code != "valid":
        raise RoundError("round_manifest_invalid:" + code, "incomplete")
    _write_json(root / ROUND_FILE, manifest)


def _brief(manifest: Mapping[str, Any]) -> dict[str, Any]:
    admission = manifest.get("admission") or {}
    child = manifest.get("child") or {}
    evaluation = manifest.get("evaluation") or {}
    return {
        "status": manifest.get("status"),
        "failure": manifest.get("failure"),
        "round": str(Path(manifest["round_root"]) / ROUND_FILE),
        "use": manifest.get("use", {}).get("kind"),
        "parent": {
            key: manifest.get("parent", {}).get(key)
            for key in ("revision", "manifest_sha256")
        },
        "child": {key: child.get(key) for key in ("revision", "manifest_sha256")},
        "added_case_count": admission.get("added_case_count"),
        "rejected_by_reason": admission.get("rejected_by_reason"),
        "needs_review": admission.get("needs_review"),
        "held_calls_by_code": admission.get("held_calls_by_code"),
        "evaluation": evaluation.get("status"),
    }


def main(argv: Sequence[str] | None = None) -> int:
    options = parse_options(argv)
    manifest = run_round(options)
    print(json.dumps(_brief(manifest), sort_keys=True))
    expected = "evaluated" if options.evaluate else "published"
    return 0 if manifest["status"] == expected else 2


if __name__ == "__main__":
    raise SystemExit(main())
