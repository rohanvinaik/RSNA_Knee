#!/usr/bin/env python3
"""Replay saved squint evidence through the current condition contracts, without re-recognition.

A completed squint run keeps, for every study and condition, the object evidence its
finding was combined from: each located object's recall record with its exact case
terms, and the whole-condition configuration voice. This tool reruns the *current*
``combine_condition`` and ``rank_condition`` over exactly that saved evidence and lays
the replayed finding beside the saved one, so a change to the contracts can be read on
retained records. No image is decoded, no object is located, no case is recalled and no
memory is opened; the saved case terms and ``decision_scope`` marks are replayed as
they were saved, never recomputed. A record saved before a field existed (a run from
before ``decision_scope``, say) is replayed without it, and the report counts that.

Labels are never read as features. The replay is finished before the labels file is
opened; only then does the optional evaluation read the official labels, to count per
condition how many saved and replayed findings were identified (decisive and correct),
abstained (open) or wrong (decisive and incorrect), and to lay out the transitions from
the saved outcomes. A blank or unrecognized label is unavailable truth, never negative.
A dataset whose receipt does not account for every study, or that holds a study that was
not examined, is reported as partial and tallied apart from the complete studies; the
two are never pooled.

Every fraction is exact, as a numerator and denominator string. Nothing here is a
cutoff, a weight or a readout: the value of a finding is whatever ``rank_condition``
serializes, and the report only compares it with the saved one.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import lzma
import math
import platform
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from knee.diagnosis import squint_contracts
from knee.diagnosis.squint_contracts import (
    ContractError,
    combine_condition,
    rank_condition,
)
from knee.study.codes import label_code
from knee.study.tables import LABELS, TRAIN_COLUMNS

REPLAY_SCHEMA = "knee.squint-replay/v1"
STUDY_SCHEMA = "knee.squint-study/v1"
OUTCOMES = ("assigned", "defeated", "open")
UNAVAILABLE = "unavailable"
JOINT_PREFIX = "diagnosis/"

#: Named codes that describe a file or a record without making a study partial.
INFORMATIONAL = frozenset(
    {"question_unknown", "unlisted_evidence_file", "evidence_duplicate_format"}
)

#: What the replay does not rerun: these are read from the saved evidence as saved.
NOT_RERUN = (
    "object location",
    "recall_object and its case terms",
    "decision_scope assignment",
    "configuration_profile composition",
    "memory loading and recall preparation",
    "image decoding and squinting",
)

# What a saved finding and a replayed finding are compared on, field by field.
_COMPARED = (
    "outcome",
    "reason",
    "decided_by",
    "unresolved_subjects",
    "unsupported_positive_subjects",
    "observation_request_ids",
    "configuration",
    "rank_exact",
    "positive_case_ids",
    "negative_case_ids",
)

Problem = tuple[str, str]

# What a regression in the contracts can raise. Each is reported by name, never
# swallowed; MemoryError, KeyboardInterrupt and the like are not the contracts' to explain.
_CONTRACT_FAILURES = (
    TypeError,
    ValueError,
    KeyError,
    IndexError,
    AttributeError,
    ArithmeticError,
    RecursionError,
    AssertionError,
)


class ReplayError(ValueError):
    """A named refusal to replay or evaluate an unreadable or mismatched input."""


@dataclass(frozen=True)
class _Study:
    """One study the run lists: its identity and the file its record is read from."""

    uid: str
    path: Path | None
    evidence_path: str | None


def _issue(
    code: str,
    detail: str = "",
    *,
    uid: str | None = None,
    question: str | None = None,
) -> dict[str, Any]:
    """A named finding about the dataset, one study or one condition."""
    scope = "question" if question is not None else "study" if uid else "dataset"
    return {
        "scope": scope,
        "study_uid": uid,
        "question": question,
        "code": code,
        "detail": detail,
    }


# ---------------------------------------------------------------------------
# bytes, digests and exact fractions
# ---------------------------------------------------------------------------


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_sha256(value: object) -> str | None:
    """SHA-256 of the canonical JSON of ``value``; None when it cannot be encoded."""
    try:
        text = json.dumps(value, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError, OverflowError, RecursionError):
        return None
    return _sha256(text.encode("ascii"))


def _decode_json(name: str, raw: bytes, prefix: str) -> tuple[object, str | None]:
    """Decode plain or XZ-compressed UTF-8 JSON; the named code says what failed."""
    data = raw
    if name.endswith(".xz"):
        try:
            data = lzma.decompress(raw, format=lzma.FORMAT_XZ)
        except (lzma.LZMAError, EOFError):
            return None, f"{prefix}_not_xz"
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None, f"{prefix}_not_utf8"
    try:
        return json.loads(text), None
    except (ValueError, RecursionError):
        return None, f"{prefix}_not_json"


def _read_json_file(
    path: Path, prefix: str
) -> tuple[object, dict[str, Any], str | None]:
    """Read one file once: its decoded JSON, the identity of its bytes, a named code."""
    identity: dict[str, Any] = {"sha256": None, "bytes": None}
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return None, identity, f"{prefix}_file_missing"
    except OSError:
        return None, identity, f"{prefix}_unreadable"
    identity = {"sha256": _sha256(raw), "bytes": len(raw)}
    value, code = _decode_json(path.name, raw, prefix)
    return value, identity, code


def _fraction_record(value: Fraction) -> dict[str, str]:
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def _parse_fraction(record: object) -> Fraction | None:
    """An exact fraction from its numerator/denominator strings, else None."""
    if not isinstance(record, Mapping):
        return None
    numerator, denominator = record.get("numerator"), record.get("denominator")
    if type(numerator) is not str or type(denominator) is not str:
        return None
    try:
        return Fraction(int(numerator), int(denominator))
    except (ValueError, ZeroDivisionError):
        return None


# ---------------------------------------------------------------------------
# the epoch: which code replayed
# ---------------------------------------------------------------------------


def _function_digests(source: str) -> dict[str, str]:
    """SHA-256 of every top-level function and class of a module's source."""
    digests: dict[str, str] = {}
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            segment = ast.get_source_segment(source, node)
            if segment is not None:
                digests[node.name] = _sha256(segment.encode("utf-8"))
    return dict(sorted(digests.items()))


def _file_epoch(path_text: str | None) -> dict[str, Any]:
    """The path and SHA-256 of a source file, or the named reason it is unavailable."""
    if not path_text:
        return {"status": "source_unavailable", "path": None, "sha256": None}
    path = Path(path_text)
    try:
        raw = path.read_bytes()
    except OSError:
        return {"status": "source_unavailable", "path": str(path), "sha256": None}
    return {
        "status": "read",
        "path": str(path.resolve()),
        "sha256": _sha256(raw),
        "bytes": len(raw),
    }


def current_epoch() -> dict[str, Any]:
    """The code this replay runs: file, per-function digests, policy and contract ids."""
    contracts = _file_epoch(getattr(squint_contracts, "__file__", None))
    functions: dict[str, str] = {}
    if contracts["status"] == "read":
        try:
            source = Path(contracts["path"]).read_text(encoding="utf-8")
            functions = _function_digests(source)
        except (OSError, SyntaxError, UnicodeDecodeError):
            contracts = {**contracts, "status": "functions_unreadable"}
    return {
        "python": platform.python_version(),
        "replayed_code": {
            "module": squint_contracts.__name__,
            **contracts,
            "entry_points": ["combine_condition", "rank_condition"],
            "policy_id": squint_contracts.POLICY_ID,
            "finding_schema": squint_contracts.FINDING_SCHEMA,
            "contract_ids": {
                contract.question: contract.contract_id
                for contract in squint_contracts.CONTRACTS
            },
            "functions": functions,
        },
        "script": _file_epoch(__file__),
        "not_rerun": list(NOT_RERUN),
    }


# ---------------------------------------------------------------------------
# what a finding and its ranking retain
# ---------------------------------------------------------------------------


def _names(value: object) -> list[str] | None:
    if not isinstance(value, list):
        return None
    return [item for item in value if isinstance(item, str)]


def _support(value: object) -> dict[str, Any] | None:
    fraction = _parse_fraction(value)
    if fraction is None or not isinstance(value, Mapping):
        return None
    return {"exact": _fraction_record(fraction), "available": value.get("available")}


def _rank_summary(ranking: object) -> tuple[dict[str, Any] | None, list[str]]:
    """The retained facts of one ranking with exact fractions, and what is wrong."""
    if not isinstance(ranking, Mapping):
        return None, ["rank_missing"]
    problems: list[str] = []
    exact = _parse_fraction(ranking.get("exact"))
    value = ranking.get("value")
    if exact is None:
        problems.append("rank_exact_invalid")
    elif not 0 < exact < 1:
        problems.append("rank_exact_out_of_range")
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        problems.append("rank_value_invalid")
        value = None
    elif exact is not None and 0 < exact < 1 and float(exact) != value:
        problems.append("rank_exact_value_mismatch")
    grade = _parse_fraction(ranking.get("e"))
    rejected = ranking.get("rejected_terms")
    eligible = ranking.get("eligible_term_count")
    return {
        "exact": None if exact is None else _fraction_record(exact),
        "value": value,
        "tier": ranking.get("tier"),
        "e": None if grade is None else _fraction_record(grade),
        "s_plus": _support(ranking.get("s_plus")),
        "s_minus": _support(ranking.get("s_minus")),
        "reason": ranking.get("reason"),
        "positive_case_ids": _names(ranking.get("positive_case_ids")) or [],
        "negative_case_ids": _names(ranking.get("negative_case_ids")) or [],
        "eligible_term_count": eligible if type(eligible) is int else None,
        "rejected_term_count": len(rejected) if isinstance(rejected, list) else None,
    }, problems


def _coverage(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    eligible = value.get("eligible_case_ids")
    eligible = eligible if isinstance(eligible, Mapping) else {}
    coverage = {
        "status": value.get("status"),
        "state": value.get("state"),
        "eligible_case_ids": {
            "positive": _names(eligible.get("positive")) or [],
            "negative": _names(eligible.get("negative")) or [],
        },
    }
    counterevidence = value.get("counterevidence_case_ids")
    if isinstance(counterevidence, list):
        coverage["counterevidence_case_ids"] = _names(counterevidence) or []
    competing = value.get("competing_partial_counterevidence")
    if isinstance(competing, Mapping):
        coverage["competing_partial_counterevidence"] = {
            str(case_id): _names(subjects) or []
            for case_id, subjects in competing.items()
        }
    anatomical = value.get("competing_anatomical_counterevidence")
    if isinstance(anatomical, list):
        coverage["competing_anatomical_counterevidence"] = _names(anatomical) or []
    return coverage


def _request_ids(value: object) -> list[str] | None:
    if not isinstance(value, list):
        return None
    return [
        item["request_id"]
        for item in value
        if isinstance(item, Mapping) and isinstance(item.get("request_id"), str)
    ]


def _projection(finding: Mapping[str, Any], ranking: object) -> dict[str, Any]:
    """What one side of the comparison keeps of a finding (saved or replayed)."""
    evidence = finding.get("evidence")
    evidence = evidence if isinstance(evidence, Mapping) else {}
    rank, problems = _rank_summary(ranking)
    return {
        "outcome": finding.get("outcome"),
        "reason": finding.get("reason"),
        "policy_id": finding.get("policy_id"),
        "contract_id": finding.get("contract_id"),
        "decided_by": _names(evidence.get("decided_by")),
        "unresolved_subjects": _names(evidence.get("unresolved_subjects")),
        "unsupported_positive_subjects": _names(
            evidence.get("unsupported_positive_subjects")
        ),
        "observation_request_ids": _request_ids(finding.get("observation_requests")),
        "configuration": _coverage(evidence.get("joint_configuration_coverage")),
        "rank": rank,
        "rank_problems": problems,
    }


def _comparable(projection: Mapping[str, Any]) -> dict[str, Any]:
    """The projection flattened to exactly the fields ``_COMPARED`` names."""
    rank = projection["rank"] or {}
    flat = {
        **projection,
        "rank_exact": rank.get("exact"),
        "positive_case_ids": rank.get("positive_case_ids"),
        "negative_case_ids": rank.get("negative_case_ids"),
    }
    return {key: flat[key] for key in _COMPARED}


def _delta(saved: Mapping[str, Any], current: Mapping[str, Any]) -> dict | None:
    """Replayed minus saved exact value, or None when either side has none."""
    left = _parse_fraction((saved["rank"] or {}).get("exact"))
    right = _parse_fraction((current["rank"] or {}).get("exact"))
    if left is None or right is None:
        return None
    return _fraction_record(right - left)


# ---------------------------------------------------------------------------
# one condition of one study
# ---------------------------------------------------------------------------


def _input_summary(objects: Mapping[str, Any]) -> dict[str, Any]:
    """Each subject's saved recall outcome, term count and decision scope."""

    def one(record: object) -> dict[str, Any]:
        if not isinstance(record, Mapping):
            return {"shape": type(record).__name__}
        rows = record.get("case_terms")
        return {
            "outcome": record.get("outcome"),
            "case_terms": len(rows) if isinstance(rows, list) else None,
            "decision_scope": record.get("decision_scope"),
        }

    summary: dict[str, Any] = {}
    for key in sorted(objects, key=str):
        raw = objects[key]
        summary[str(key)] = (
            [one(item) for item in raw] if isinstance(raw, list) else one(raw)
        )
    return summary


def _new_features() -> dict[str, Counter]:
    return {
        "decision_scope": Counter(),
        "call_scope": Counter(),
        "configuration_voice": Counter(),
    }


def _mark(counter: Counter, record: Mapping[str, Any], name: str) -> None:
    """Count one saved mark: its value when it is a named string, else why not."""
    value = record.get(name)
    if name not in record:
        counter["absent"] += 1
    elif isinstance(value, str) and value:
        counter[value] += 1
    else:
        counter["other"] += 1


def _count_features(objects: Mapping[str, Any], features: dict[str, Counter]) -> None:
    """Count the saved marks the contracts read, so absent ones are visible."""
    for key, raw in objects.items():
        if str(key).startswith(JOINT_PREFIX):
            features["configuration_voice"]["present"] += 1
        for record in raw if isinstance(raw, list) else [raw]:
            if not isinstance(record, Mapping):
                continue
            _mark(features["decision_scope"], record, "decision_scope")
            rows = record.get("case_terms")
            for row in rows if isinstance(rows, list) else []:
                if isinstance(row, Mapping):
                    _mark(features["call_scope"], row, "call_scope")


def _saved_side(
    entry: Mapping[str, Any], problems: list[Problem]
) -> dict[str, Any] | None:
    """The saved finding of one condition, or None with the reason it is unusable."""
    finding = entry.get("finding")
    if finding is None:
        problems.append(("saved_finding_missing", ""))
        return None
    if not isinstance(finding, Mapping):
        problems.append(("saved_finding_not_object", ""))
        return None
    if finding.get("outcome") not in OUTCOMES:
        problems.append(("saved_outcome_invalid", repr(finding.get("outcome"))[:80]))
        return None
    ranking = entry.get("ranking")
    projection = _projection(
        finding, ranking if isinstance(ranking, Mapping) else finding.get("rank")
    )
    if projection["rank_problems"]:
        problems.append(("saved_rank_invalid", ",".join(projection["rank_problems"])))
    return projection


def _replayed_side(
    question: str, objects: Mapping[str, Any], problems: list[Problem]
) -> tuple[dict[str, Any] | None, Mapping[str, Any] | None, bool | None]:
    """Run the current contracts: (projection, finding, embedded rank == standalone)."""
    try:
        finding = combine_condition(question, objects)
    except ContractError as error:
        problems.append((f"combine_condition_refused:{error.code}", error.detail))
        return None, None, None
    except _CONTRACT_FAILURES as error:
        problems.append(
            (f"combine_condition_raised:{type(error).__name__}", str(error)[:200])
        )
        return None, None, None
    if not isinstance(finding, Mapping) or finding.get("outcome") not in OUTCOMES:
        problems.append(("current_finding_invalid", ""))
        return None, None, None
    try:
        standalone = rank_condition(finding)
    except ContractError as error:
        problems.append((f"rank_condition_refused:{error.code}", error.detail))
        return None, finding, None
    except _CONTRACT_FAILURES as error:
        problems.append(
            (f"rank_condition_raised:{type(error).__name__}", str(error)[:200])
        )
        return None, finding, None
    embedded = finding.get("rank")
    ranking = embedded if isinstance(embedded, Mapping) else standalone
    projection = _projection(finding, ranking)
    found = list(projection["rank_problems"])
    if isinstance(ranking, Mapping) and ranking.get("tier") != finding.get("outcome"):
        found.append("rank_tier_mismatch")
    if found:
        problems.append(("current_rank_invalid", ",".join(found)))
        return None, finding, None
    agrees = embedded == standalone if isinstance(embedded, Mapping) else None
    return projection, finding, agrees


def _empty_row(question: str) -> dict[str, Any]:
    return {
        "question": question,
        "disposition": "not_replayed",
        "issues": [],
        "input_sha256": None,
        "input": None,
        "saved": None,
        "current": None,
        "changed": None,
        "identical_finding": None,
        "rank_delta": None,
        "rank_embedded_equals_standalone": None,
    }


def _replay_question(
    question: str, entry: object, features: dict[str, Counter]
) -> tuple[dict[str, Any], list[Problem]]:
    """One condition: the saved finding beside the current combination of its evidence."""
    problems: list[Problem] = []
    row = _empty_row(question)
    if not isinstance(entry, Mapping):
        problems.append(("question_entry_not_object", ""))
        row["issues"] = [code for code, _ in problems]
        return row, problems
    saved = _saved_side(entry, problems)
    row["saved"] = saved
    objects = entry.get("objects")
    if not isinstance(objects, Mapping):
        missing = objects is None
        problems.append(
            ("question_objects_missing" if missing else "question_objects_invalid", "")
        )
        row["issues"] = [code for code, _ in problems]
        return row, problems
    # Everything read from the saved evidence is read before the contracts run.
    row["input_sha256"] = _canonical_sha256(objects)
    if row["input_sha256"] is None:
        problems.append(("input_digest_unavailable", ""))
    row["input"] = _input_summary(objects)
    _count_features(objects, features)
    current, finding, agrees = _replayed_side(question, objects, problems)
    row["current"] = current
    row["rank_embedded_equals_standalone"] = agrees
    if current is not None:
        row["disposition"] = "replayed"
        if saved is not None:
            before, after = _comparable(saved), _comparable(current)
            row["changed"] = [key for key in _COMPARED if before[key] != after[key]]
            row["identical_finding"] = entry.get("finding") == finding
            row["rank_delta"] = _delta(saved, current)
    row["issues"] = [code for code, _ in problems]
    return row, problems


# ---------------------------------------------------------------------------
# one study record
# ---------------------------------------------------------------------------


def _unread(uid: str, code: str, detail: str = "") -> dict[str, Any]:
    """The result for a study whose record could not be used at all."""
    return {
        "study_uid": uid,
        "disposition": "not_replayed",
        "study_status": None,
        "memory_revision": None,
        "rows": [],
        "issues": [_issue(code, detail, uid=uid)],
        "saved_policy_ids": [],
    }


def _unusable_record(uid: str, record: object) -> tuple[str, str] | None:
    """The code and detail that make a decoded record impossible to replay, if any."""
    if not isinstance(record, Mapping):
        return "evidence_not_object", ""
    if record.get("schema") != STUDY_SCHEMA:
        return "evidence_schema_mismatch", repr(record.get("schema"))[:80]
    if record.get("study_uid") != uid:
        return "study_uid_mismatch", repr(record.get("study_uid"))[:100]
    if not isinstance(record.get("questions"), Mapping):
        return "questions_missing", ""
    return None


def replay_study(
    uid: str, record: object, features: dict[str, Counter] | None = None
) -> dict[str, Any]:
    """Replay one saved study record: its rows and the issues found in it (no file read)."""
    features = features if features is not None else _new_features()
    unusable = _unusable_record(uid, record)
    if unusable is not None:
        return _unread(uid, *unusable)
    assert isinstance(record, Mapping)
    questions = record["questions"]
    issues: list[dict[str, Any]] = []
    status = record.get("study_status")
    if status is None:
        issues.append(_issue("study_status_missing", uid=uid))
    elif status == "not_examined_budget":
        issues.append(_issue("study_not_examined_budget", uid=uid))
    elif status != "examined":
        issues.append(_issue("study_status_invalid", repr(status)[:80], uid=uid))
    issues.extend(
        _issue("question_unknown", name, uid=uid)
        for name in sorted(str(key) for key in questions if key not in LABELS)
    )
    rows: list[dict[str, Any]] = []
    for question in LABELS:
        if question not in questions:
            issues.append(_issue("question_missing", uid=uid, question=question))
            row = _empty_row(question)
            row["issues"] = ["question_missing"]
            rows.append(row)
            continue
        row, problems = _replay_question(question, questions[question], features)
        issues.extend(
            _issue(code, detail, uid=uid, question=question)
            for code, detail in problems
        )
        rows.append(row)
    blocking = any(issue["code"] not in INFORMATIONAL for issue in issues)
    return {
        "study_uid": uid,
        "disposition": "partial" if blocking else "complete",
        "study_status": status,
        "memory_revision": record.get("memory_revision"),
        "rows": rows,
        "issues": issues,
        "saved_policy_ids": sorted(
            {
                row["saved"]["policy_id"]
                for row in rows
                if row["saved"] and isinstance(row["saved"].get("policy_id"), str)
            }
        ),
    }


# ---------------------------------------------------------------------------
# the run: which studies it lists, and where their records are
# ---------------------------------------------------------------------------


def _studies_root(run: Path) -> Path:
    """The directory holding ``studies/``: the run itself or its ``diagnostics``."""
    for candidate in (run, run / "diagnostics"):
        if (candidate / "studies").is_dir():
            return candidate
    raise ReplayError("run_studies_directory_missing")


def _safe_path(root: Path, relative: object) -> Path | None:
    if type(relative) is not str or not relative:
        return None
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return None
    return path


def _scan_directory(root: Path, issues: list[dict[str, Any]]) -> dict[str, Path]:
    """Every record on disk by file stem; the compressed form wins over a plain twin."""
    found: dict[str, Path] = {}
    for path in sorted((root / "studies").iterdir()):
        for suffix in (".json.xz", ".json"):
            if path.name.endswith(suffix) and path.is_file():
                stem = path.name[: -len(suffix)]
                if stem in found:
                    issues.append(_issue("evidence_duplicate_format", stem))
                    if suffix == ".json.xz":
                        found[stem] = path
                else:
                    found[stem] = path
                break
    return found


def _read_receipt(
    root: Path, issues: list[dict[str, Any]]
) -> tuple[Mapping[str, Any] | None, dict[str, Any] | None]:
    """The run's receipt and the identity of its bytes; a named issue when unusable."""
    for name in ("receipt.json", "receipt.json.xz"):
        path = root / name
        if not path.is_file():
            continue
        receipt, identity, code = _read_json_file(path, "receipt")
        identity = {"path": name, **identity}
        if code is not None:
            issues.append(_issue(code))
            return None, identity
        if not isinstance(receipt, Mapping):
            issues.append(_issue("receipt_not_object"))
            return None, identity
        return receipt, identity
    issues.append(_issue("receipt_missing"))
    return None, None


def _receipt_studies(
    root: Path, receipt: Mapping[str, Any], issues: list[dict[str, Any]]
) -> list[_Study] | None:
    """The studies a receipt lists, or None when the receipt cannot index the run."""
    work = receipt.get("work")
    listed = work.get("studies") if isinstance(work, Mapping) else None
    if not isinstance(listed, list):
        issues.append(_issue("receipt_studies_missing"))
        return None
    studies: list[_Study] = []
    seen: set[str] = set()
    for index, item in enumerate(listed):
        uid = item.get("study_uid") if isinstance(item, Mapping) else None
        if type(uid) is not str or not uid:
            issues.append(_issue("receipt_study_row_invalid", str(index)))
            continue
        if uid in seen:
            issues.append(_issue("receipt_study_uid_duplicate", uid))
            continue
        seen.add(uid)
        relative = item.get("evidence_path")
        path = _safe_path(root, relative)
        if path is None:
            outside = type(relative) is str and bool(relative)
            code = (
                "receipt_evidence_path_outside_run"
                if outside
                else "receipt_evidence_path_invalid"
            )
            issues.append(_issue(code, uid))
        studies.append(_Study(uid, path, relative if path is not None else None))
    count = receipt.get("studies")
    if type(count) is not int or count != len(listed):
        issues.append(
            _issue("receipt_study_count_mismatch", f"{count!r}:{len(listed)}")
        )
    return studies


def _index_run(
    root: Path, issues: list[dict[str, Any]]
) -> tuple[list[_Study], str, dict[str, Any] | None]:
    """The run's own study list: its receipt when valid, else its records on disk."""
    on_disk = _scan_directory(root, issues)
    receipt, identity = _read_receipt(root, issues)
    if receipt is not None and identity is not None:
        studies = _receipt_studies(root, receipt, issues)
        if studies is not None:
            identity.update(
                {
                    key: receipt.get(key)
                    for key in (
                        "schema",
                        "action",
                        "source_mode",
                        "memory_revision",
                        "memory_manifest_sha256",
                        "studies",
                    )
                }
            )
            listed = {study.uid for study in studies}
            issues.extend(
                _issue("unlisted_evidence_file", stem)
                for stem in sorted(set(on_disk) - listed)
            )
            return studies, "receipt", identity
    listing = [
        _Study(stem, path, f"studies/{path.name}") for stem, path in on_disk.items()
    ]
    return listing, "directory_listing", identity


def read_expected_uids(path: Path) -> tuple[list[str], dict[str, Any]]:
    """The study UIDs a run was meant to cover: one per line, blank lines ignored."""
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise ReplayError("expected_uids_unreadable") from error
    try:
        lines = raw.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError as error:
        raise ReplayError("expected_uids_not_utf8") from error
    uids = [line.strip() for line in lines if line.strip()]
    if not uids:
        raise ReplayError("expected_uids_empty")
    repeated = sorted(uid for uid, count in Counter(uids).items() if count > 1)
    if repeated:
        raise ReplayError("expected_uids_duplicate:" + repeated[0])
    identity = {
        "path": str(path.resolve()),
        "sha256": _sha256(raw),
        "bytes": len(raw),
        "count": len(uids),
    }
    return uids, identity


def _run_studies(
    listed: list[_Study],
    index_kind: str,
    expected: Sequence[str] | None,
    issues: list[dict[str, Any]],
) -> tuple[list[_Study], str]:
    """The studies to replay, and where the expectation of their number comes from."""
    if expected is None:
        return listed, index_kind
    by_uid = {study.uid: study for study in listed}
    wanted = set(expected)
    issues.extend(
        _issue("expected_study_not_in_run", uid)
        for uid in expected
        if uid not in by_uid
    )
    issues.extend(
        _issue("study_not_in_expected", study.uid)
        for study in listed
        if study.uid not in wanted
    )
    studies = [by_uid.get(uid, _Study(uid, None, None)) for uid in expected]
    return studies, "expected_uids"


def _replay_listed(
    study: _Study, features: dict[str, Counter], inputs: list[dict[str, Any]]
) -> dict[str, Any]:
    """Read one listed study's record once, retain its identity, and replay it."""
    if study.path is None:
        return _unread(study.uid, "evidence_file_missing")
    record, identity, code = _read_json_file(study.path, "evidence")
    inputs.append({"study_uid": study.uid, "path": study.evidence_path, **identity})
    if code is not None:
        return _unread(study.uid, code)
    return replay_study(study.uid, record, features)


# ---------------------------------------------------------------------------
# the whole replay (no labels anywhere in this function's reach)
# ---------------------------------------------------------------------------


def _saved_outcome(row: Mapping[str, Any]) -> str:
    saved = row["saved"]
    return saved["outcome"] if saved else UNAVAILABLE


def _replayed_outcome(row: Mapping[str, Any]) -> str:
    current = row["current"]
    return current["outcome"] if current else UNAVAILABLE


def _transitions(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, int]]:
    """Saved outcome (row) by replayed outcome (column); the unavailable ones apart."""
    names = (*OUTCOMES, UNAVAILABLE)
    matrix = {saved: dict.fromkeys(names, 0) for saved in names}
    for row in rows:
        matrix[_saved_outcome(row)][_replayed_outcome(row)] += 1
    return matrix


def _bin_summary(studies: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Label-free counts and per-condition transitions for one bin of studies."""
    rows = [row for study in studies for row in study["rows"]]
    replayed = [row for row in rows if row["disposition"] == "replayed"]
    return {
        "study_count": len(studies),
        "conditions": len(rows),
        "replayed": len(replayed),
        "not_replayed": len(rows) - len(replayed),
        "identical_to_saved": sum(row["identical_finding"] is True for row in replayed),
        "outcome_changed": sum("outcome" in (row["changed"] or ()) for row in replayed),
        "any_field_changed": sum(bool(row["changed"]) for row in replayed),
        "per_condition": {
            question: {
                "transitions": _transitions(
                    [row for row in rows if row["question"] == question]
                )
            }
            for question in LABELS
        },
    }


def replay_run(
    run: Path,
    *,
    expected_uids: Sequence[str] | None = None,
    expected_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Replay every study a run lists through the current contracts. Takes no labels."""
    root = _studies_root(Path(run))
    issues: list[dict[str, Any]] = []
    listed, index_kind, receipt_identity = _index_run(root, issues)
    studies, expected_source = _run_studies(listed, index_kind, expected_uids, issues)

    features = _new_features()
    evidence_inputs: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    saved_revisions: Counter = Counter()
    saved_policies: Counter = Counter()
    for study in studies:
        result = _replay_listed(study, features, evidence_inputs)
        issues.extend(result["issues"])
        if result["disposition"] != "not_replayed":
            saved_revisions[str(result["memory_revision"])] += 1
            saved_policies.update(result["saved_policy_ids"])
        results.append(result)

    by_disposition = Counter(result["disposition"] for result in results)
    blocking = Counter(
        issue["code"] for issue in issues if issue["code"] not in INFORMATIONAL
    )
    if expected_source == "expected_uids":
        blocking.pop("receipt_missing", None)  # the supplied UIDs fix the universe
    if not studies:
        blocking["no_studies_listed"] += 1
    verifiable = expected_source != "directory_listing"
    return {
        "schema": REPLAY_SCHEMA,
        "scope": {
            "replayed": "combine_condition and rank_condition over each saved "
            "question's object evidence, as saved",
            "not_rerun": list(NOT_RERUN),
            "labels_read": False,
        },
        "epoch": current_epoch(),
        "run": {
            "path": str(root.resolve()),
            "study_index": index_kind,
            "receipt": receipt_identity,
        },
        "inputs": {
            "receipt": receipt_identity,
            "expected_uids": None
            if expected_identity is None
            else dict(expected_identity),
            "evidence": evidence_inputs,
        },
        "saved_epoch": {
            "memory_revisions": dict(sorted(saved_revisions.items())),
            "finding_policy_ids": dict(sorted(saved_policies.items())),
            "marks_in_saved_evidence": {
                name: dict(sorted(counter.items()))
                for name, counter in sorted(features.items())
            },
        },
        "dataset": {
            "status": "complete" if verifiable and not blocking else "partial",
            "expected": {
                "source": expected_source,
                "verifiable": verifiable,
                "count": len(studies) if verifiable else None,
            },
            "studies": {
                "listed": len(studies),
                "complete": by_disposition["complete"],
                "partial": by_disposition["partial"],
                "not_replayed": by_disposition["not_replayed"],
            },
            "partial_because": dict(sorted(blocking.items())),
        },
        "bins": {
            "complete_studies": _bin_summary(
                [r for r in results if r["disposition"] == "complete"]
            ),
            "partial_studies": _bin_summary(
                [r for r in results if r["disposition"] == "partial"]
            ),
        },
        "studies": [
            {
                "study_uid": result["study_uid"],
                "disposition": result["disposition"],
                "study_status": result["study_status"],
                "memory_revision": result["memory_revision"],
                "issue_codes": sorted({issue["code"] for issue in result["issues"]}),
            }
            for result in results
        ],
        "rows": [
            {"study_uid": result["study_uid"], **row}
            for result in results
            for row in result["rows"]
        ],
        "issues": issues,
        "evaluation": {"status": "not_requested", "labels_read": False},
    }


# ---------------------------------------------------------------------------
# labels, read only after the replay is finished
# ---------------------------------------------------------------------------


def read_labels(path: Path) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    """Official labels as literal codes ("1", "0", "not_given", "unrecognized")."""
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise ReplayError("labels_unreadable") from error
    try:
        text = raw.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text, newline=""), strict=True))
    except (UnicodeDecodeError, csv.Error) as error:
        raise ReplayError("labels_csv_malformed") from error
    if not rows:
        raise ReplayError("labels_empty")
    header, *body = rows
    if tuple(header) != TRAIN_COLUMNS:
        raise ReplayError("labels_columns_invalid")
    if not body:
        raise ReplayError("labels_empty")
    labels: dict[str, dict[str, str]] = {}
    for number, cells in enumerate(body, start=2):
        if len(cells) != len(TRAIN_COLUMNS):
            raise ReplayError(f"labels_row_width_invalid:{number}")
        row = dict(zip(TRAIN_COLUMNS, cells, strict=True))
        uid = row["StudyInstanceUID"]
        if not uid.strip():
            raise ReplayError("labels_study_uid_invalid")
        if uid in labels:
            raise ReplayError("labels_study_uid_duplicate:" + uid)
        labels[uid] = {name: label_code(row[name]) for name in LABELS}
    identity = {
        "path": str(path.resolve()),
        "sha256": _sha256(raw),
        "bytes": len(raw),
        "study_count": len(labels),
    }
    return labels, identity


def _identification(outcome: str, truth: str) -> str:
    """Decisive and correct, decisive and wrong, or open; unavailable stays apart."""
    if outcome == "open":
        return "abstained"
    if outcome in ("assigned", "defeated"):
        correct = (outcome == "assigned") == (truth == "positive")
        return "identified" if correct else "wrong"
    return UNAVAILABLE


def _new_tally() -> dict[str, int]:
    return {"identified": 0, "abstained": 0, "wrong": 0, UNAVAILABLE: 0, "count": 0}


def _evaluate_bin(
    studies: Sequence[Mapping[str, Any]],
    rows: Mapping[str, Mapping[str, Mapping[str, Any]]],
    labels: Mapping[str, Mapping[str, str]],
) -> dict[str, Any]:
    """Per condition: unavailable truth, saved and replayed tallies, transitions."""
    per_condition: dict[str, Any] = {}
    for question in LABELS:
        tallies = {
            side: {truth: _new_tally() for truth in ("positive", "negative")}
            for side in ("saved", "replayed")
        }
        unavailable_truth: Counter = Counter()
        by_truth: dict[str, list[Mapping[str, Any]]] = {"positive": [], "negative": []}
        for study in studies:
            uid = study["study_uid"]
            row = rows[uid].get(question)
            if row is None:
                continue
            code = (
                labels[uid][question] if uid in labels else "study_not_in_label_source"
            )
            if code not in ("1", "0"):
                unavailable_truth[code] += 1
                continue
            truth = "positive" if code == "1" else "negative"
            by_truth[truth].append(row)
            for side, outcome in (
                ("saved", _saved_outcome(row)),
                ("replayed", _replayed_outcome(row)),
            ):
                tally = tallies[side][truth]
                tally[_identification(outcome, truth)] += 1
                tally["count"] += 1
        per_condition[question] = {
            "unavailable_truth": dict(sorted(unavailable_truth.items())),
            **tallies,
            "transitions_by_truth": {
                truth: _transitions(chosen) for truth, chosen in by_truth.items()
            },
        }
    return {"study_count": len(studies), "per_condition": per_condition}


def evaluate_replay(
    replay: Mapping[str, Any],
    labels: Mapping[str, Mapping[str, str]],
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    """Count identified / abstained / wrong per condition, and the transitions by truth.

    The replay is already complete here. Complete and partial studies are tallied in
    separate bins and never pooled. Only literal ``1`` and ``0`` labels are truth.
    """
    rows: dict[str, dict[str, Mapping[str, Any]]] = {}
    for row in replay["rows"]:
        rows.setdefault(row["study_uid"], {})[row["question"]] = row
    studies = [s for s in replay["studies"] if s["disposition"] != "not_replayed"]
    completeness: Counter = Counter()
    for study in studies:
        uid = study["study_uid"]
        if uid not in labels:
            completeness["study_not_in_label_source"] += 1
        elif all(labels[uid][question] in ("1", "0") for question in LABELS):
            completeness["complete"] += 1
        else:
            completeness["partial"] += 1
    return {
        "status": "evaluated",
        "labels_read": True,
        "labels_read_after_replay": True,
        "labels": dict(identity),
        "meaning": {
            "identified": "decisive and correct (assigned for a positive label, "
            "defeated for a negative one)",
            "wrong": "decisive and incorrect",
            "abstained": "open",
            "unavailable": "no usable outcome on that side (not replayed or not saved)",
            "truth": "only the literal labels 1 and 0; a blank or unrecognized label "
            "is unavailable truth, never negative",
        },
        "label_completeness": dict(sorted(completeness.items())),
        "bins": {
            name: _evaluate_bin(
                [s for s in studies if s["disposition"] == disposition], rows, labels
            )
            for name, disposition in (
                ("complete_studies", "complete"),
                ("partial_studies", "partial"),
            )
        },
    }


def build_report(
    run: Path,
    *,
    labels_path: Path | None = None,
    expected_uids_path: Path | None = None,
) -> dict[str, Any]:
    """Replay a run, then (only then) read the labels and evaluate."""
    expected: list[str] | None = None
    expected_identity: dict[str, Any] | None = None
    if expected_uids_path is not None:
        expected, expected_identity = read_expected_uids(expected_uids_path)
    report = replay_run(
        run, expected_uids=expected, expected_identity=expected_identity
    )
    if labels_path is not None:
        labels, identity = read_labels(labels_path)
        report["evaluation"] = evaluate_replay(report, labels, identity)
        report["scope"] = {**report["scope"], "labels_read": True}
        report["inputs"] = {**report["inputs"], "labels": identity}
    return report


# ---------------------------------------------------------------------------
# the Markdown reading of a report, and the command
# ---------------------------------------------------------------------------


def _transition_cells(matrix: Mapping[str, Mapping[str, int]]) -> str:
    kept = sum(row[name] for name, row in matrix.items())
    moved = [
        f"{saved}→{replayed} {count}"
        for saved, row in matrix.items()
        for replayed, count in row.items()
        if count and saved != replayed
    ]
    return "; ".join([f"{kept} unchanged", *moved])


def _tally_cell(tally: Mapping[str, int]) -> str:
    cell = f"{tally['identified']} / {tally['abstained']} / {tally['wrong']}"
    if tally[UNAVAILABLE]:
        cell += f" (+{tally[UNAVAILABLE]} unavailable)"
    return cell


def _markdown_header(report: Mapping[str, Any]) -> list[str]:
    code = report["epoch"]["replayed_code"]
    dataset = report["dataset"]
    counts = dataset["studies"]
    lines = [
        "# Squint findings replayed through the current contracts",
        "",
        f"Run: `{report['run']['path']}` (study index: {report['run']['study_index']})  ",
        f"Replayed code: `{code['module']}` at `{code['path']}`  ",
        f"Its SHA-256: `{code['sha256']}`; policy `{code['policy_id']}`  ",
        f"Not rerun: {', '.join(report['scope']['not_rerun'])}.  ",
        (
            f"Dataset: **{dataset['status']}**: {counts['complete']} complete, "
            f"{counts['partial']} partial, {counts['not_replayed']} not replayed "
            f"of {counts['listed']} listed."
        ),
    ]
    if dataset["partial_because"]:
        why = ", ".join(f"{n} {name}" for name, n in dataset["partial_because"].items())
        lines.append(f"Partial because: {why}.")
    marks = json.dumps(report["saved_epoch"]["marks_in_saved_evidence"], sort_keys=True)
    return [*lines, "", f"Marks present in the saved evidence: `{marks}`", ""]


def _markdown_transitions(report: Mapping[str, Any]) -> list[str]:
    lines: list[str] = []
    for name, bin_ in report["bins"].items():
        if not bin_["study_count"]:
            continue
        title = name.replace("_", " ")
        lines += [
            f"## Transitions from the saved outcomes: {title} ({bin_['study_count']})",
            "",
            (
                f"{bin_['replayed']} of {bin_['conditions']} conditions replayed; "
                f"{bin_['identical_to_saved']} identical to the saved finding; "
                f"{bin_['outcome_changed']} changed outcome."
            ),
            "",
            "| Condition | Saved to replayed |",
            "|---|---|",
        ]
        lines += [
            f"| {question} | {_transition_cells(entry['transitions'])} |"
            for question, entry in bin_["per_condition"].items()
        ]
        lines.append("")
    return lines


def _markdown_evaluation(evaluation: Mapping[str, Any]) -> list[str]:
    if evaluation["status"] != "evaluated":
        return []
    lines = [
        "## Identified / abstained / wrong against the official labels",
        "",
        (
            "Identified is decisive and correct; abstained is open; wrong is decisive "
            "and incorrect. Blank or unrecognized labels are unavailable truth, not "
            "negative. No combined score is reported."
        ),
        "",
    ]
    for name, bin_ in evaluation["bins"].items():
        if not bin_["study_count"]:
            continue
        lines += [
            f"### {name.replace('_', ' ')} ({bin_['study_count']})",
            "",
            (
                "| Condition | Saved: positive | Saved: negative "
                "| Replayed: positive | Replayed: negative |"
            ),
            "|---|---:|---:|---:|---:|",
        ]
        for question, entry in bin_["per_condition"].items():
            cells = (
                _tally_cell(entry[side][truth])
                for side in ("saved", "replayed")
                for truth in ("positive", "negative")
            )
            lines.append(f"| {question} | " + " | ".join(cells) + " |")
        lines.append("")
    return lines


def _markdown_changes(report: Mapping[str, Any]) -> list[str]:
    lines: list[str] = []
    changed = [row for row in report["rows"] if row["changed"]]
    if changed:
        lines += ["## Changed findings", ""]
        lines += [
            (
                f"- `{row['study_uid']}` {row['question']}: "
                f"{row['saved']['outcome']} to {row['current']['outcome']} "
                f"({row['saved']['reason']} to {row['current']['reason']}); "
                f"changed: {', '.join(row['changed'])}"
            )
            for row in changed
        ]
        lines.append("")
    if report["issues"]:
        by_code = Counter(issue["code"] for issue in report["issues"])
        lines += ["## Named issues", ""]
        lines += [f"- `{name}`: {n}" for name, n in sorted(by_code.items())]
        lines.append("")
    return lines


def _markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            *_markdown_header(report),
            *_markdown_transitions(report),
            *_markdown_evaluation(report["evaluation"]),
            *_markdown_changes(report),
        ]
    )


def _write_new(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run",
        type=Path,
        required=True,
        help="run directory holding studies/ (or its parent holding diagnostics/)",
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="new JSON report path"
    )
    parser.add_argument(
        "--markdown", type=Path, help="optional new Markdown report path"
    )
    parser.add_argument(
        "--labels",
        type=Path,
        help="official train.csv, read only after the replay, to evaluate it",
    )
    parser.add_argument(
        "--expected-uids",
        type=Path,
        help="text file, one study UID per line, that the run was meant to cover",
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="exit 1 (after writing) when the dataset is partial",
    )
    args = parser.parse_args(argv)
    try:
        if (
            args.markdown is not None
            and args.markdown.resolve() == args.output.resolve()
        ):
            raise ReplayError("output_paths_must_be_distinct")
        for output in (args.output, args.markdown):
            if output is not None and output.exists():
                raise ReplayError("output_already_exists:" + str(output))
        report = build_report(
            args.run, labels_path=args.labels, expected_uids_path=args.expected_uids
        )
        _write_new(
            args.output,
            json.dumps(report, sort_keys=True, indent=1, allow_nan=False) + "\n",
        )
        if args.markdown is not None:
            _write_new(args.markdown, _markdown(report))
    except (ReplayError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(f"wrote {args.output}")
    if args.markdown is not None:
        print(f"wrote {args.markdown}")
    if args.require_complete and report["dataset"]["status"] != "complete":
        print("dataset is partial", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
