"""Add independently pictured cheap cases without replacing signed parent memory.

This packet utility deliberately does not build configuration extensions. C2 owns
that integration. Existing configurations and all signed parent records remain.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

from knee.diagnosis.squint_identity import (
    IDENTITY_CASES_SCHEMA,
    _view_set,
    confirm_call_views,
    identity_condition_views,
    prepare_identity,
)
from knee.diagnosis.squint_locator import _bank_view, prepare_recall
from knee.diagnosis.squint_memory import (
    SquintMemoryError,
    _validate_memory,
    load_memory_snapshot,
    save_memory,
)

SCHEMA = "knee.direct-visual-teaching/v1"
RUNTIME_KEYS = {
    "full_profile_retention",
    "view",
    "prepared_recall",
    "memory_manifest_sha256",
}


class VisualTeachingError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def validate_additions(parent: dict, additions: object) -> tuple[list, list]:
    """Require one explicitly scoped confirm or reject per measured object case."""
    if not isinstance(additions, dict) or additions.get("schema") != SCHEMA:
        raise VisualTeachingError("additions_schema_invalid")
    reader = additions.get("reader")
    if not isinstance(reader, str) or not reader.strip():
        raise VisualTeachingError("visual_reader_required")
    cases, calls = additions.get("cases"), additions.get("calls")
    if not isinstance(cases, list) or not cases or not isinstance(calls, list):
        raise VisualTeachingError("visual_cases_and_calls_required")
    ids = {c["case_id"] for c in parent["cases"]}
    table = parent.get("object_identity_cases") or {}
    ids.update(c["case_id"] for c in table.get("cases", []))
    pairs = {(c["study_uid"], c["subject"]) for c in parent["cases"]}
    procedures = {
        c["profile"].get("source", {}).get("procedure")
        for c in parent["cases"]
        if not c["subject"].startswith("diagnosis/")
    }
    by_id: dict = {}
    for case in cases:
        if not isinstance(case, dict):
            raise VisualTeachingError("visual_case_invalid")
        cid, uid, subject = (case.get(k) for k in ("case_id", "study_uid", "subject"))
        if not all(isinstance(x, str) and x.strip() for x in (cid, uid, subject)):
            raise VisualTeachingError("visual_case_identity_invalid")
        if cid in ids or cid in by_id:
            raise VisualTeachingError("visual_case_id_duplicate")
        if subject.startswith("diagnosis/"):
            raise VisualTeachingError("visual_case_must_be_object")
        if case.get("full_profile") is not None or "full_profile_refs" in case:
            raise VisualTeachingError(
                "visual_case_full_evidence_not_supplied_by_this_route"
            )
        if not isinstance(case.get("source"), dict) or not case["source"]:
            raise VisualTeachingError("visual_source_required")
        try:
            _validate_memory(
                {
                    "schema": parent["schema"],
                    "revision": "visual-input-check",
                    "questions": parent["questions"],
                    "cases": [case],
                }
            )
        except SquintMemoryError as error:
            raise VisualTeachingError(f"visual_case_invalid:{error.code}") from error
        by_id[cid] = case
    rows: dict = {}
    for row in calls:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("candidate_id"), str)
            or row["candidate_id"] not in by_id
        ):
            raise VisualTeachingError("visual_call_candidate_invalid")
        cid = row["candidate_id"]
        if cid in rows:
            raise VisualTeachingError("visual_call_duplicate")
        if row.get("call") not in ("confirm", "reject"):
            raise VisualTeachingError("visual_call_must_confirm_or_reject")
        if row.get("negative_views") or row.get("also_positive"):
            raise VisualTeachingError("visual_call_must_assert_one_identity")
        if not isinstance(row.get("notes"), str) or not row["notes"].strip():
            raise VisualTeachingError("visual_call_reason_required")
        actual_reader = row.get("reader", reader)
        if not isinstance(actual_reader, str) or not actual_reader.strip():
            raise VisualTeachingError("visual_reader_required")
        case = by_id[cid]
        if row["call"] == "confirm":
            pair = (case["study_uid"], case["subject"])
            if pair in pairs:
                raise VisualTeachingError("visual_study_subject_duplicate")
            pairs.add(pair)
            result = confirm_call_views(row)
            selected = result.get("views") if result["outcome"] == "views" else None
        else:
            if case.get("condition_calls"):
                raise VisualTeachingError("visual_reject_cannot_assert_conditions")
            selected = _view_set(row.get("views"))
        if not selected:
            raise VisualTeachingError("visual_call_explicit_views_required")
        profile = by_id[cid].get("profile")
        banks = profile.get("banks") if isinstance(profile, dict) else None
        if not isinstance(banks, dict):
            raise VisualTeachingError("visual_profile_invalid")
        if profile.get("subject") != by_id[cid]["subject"]:
            raise VisualTeachingError("visual_profile_subject_mismatch")
        profile_source = profile.get("source")
        if not isinstance(profile_source, dict):
            raise VisualTeachingError("visual_profile_source_invalid")
        if profile_source.get("procedure") not in procedures:
            raise VisualTeachingError("visual_profile_procedure_mismatch")
        available = {
            _bank_view(name)
            for name, counts in banks.items()
            if isinstance(name, str) and sum(counts) > 0
        }
        if not selected.issubset(available):
            raise VisualTeachingError("visual_call_view_not_observed")
        rows[cid] = {**row, "reader": actual_reader}
    if set(rows) != set(by_id):
        raise VisualTeachingError("visual_case_without_call")
    return copy.deepcopy(cases), [copy.deepcopy(rows[c["case_id"]]) for c in cases]


def apply_validated_additions(
    parent: dict, cases: list, calls: list, provenance: dict
) -> dict:
    """Apply ``validate_additions``' signed rows without publishing or relabelling.

    Confirmed measured cases enter the existing positive store. Rejected support
    enters the existing signed identity table, carrying its actual call scope;
    it supplies no condition feature. Every parent store is retained. The caller
    owns revision, configuration refresh and immutable publication.
    """
    confirmed, rejected = [], []
    for source_case, call in zip(cases, calls, strict=True):
        case = copy.deepcopy(source_case)
        case["direct_visual_teaching"] = {**provenance, "call": copy.deepcopy(call)}
        if call["call"] == "confirm":
            confirmed.append(case)
        elif call["call"] == "reject":
            rejected.append(case)
        else:
            raise VisualTeachingError("visual_call_must_confirm_or_reject")
    child = {key: value for key, value in parent.items() if key not in RUNTIME_KEYS}
    child["cases"] = [*parent["cases"], *confirmed]
    teaching = copy.deepcopy(parent["object_identity_teaching"])
    teaching["confirmed_case_ids"].extend(case["case_id"] for case in confirmed)
    teaching["calls"].extend(copy.deepcopy(calls))
    if rejected:
        teaching["negative_case_ids"] = [
            *teaching.get("negative_case_ids", []),
            *(case["case_id"] for case in rejected),
        ]
        teaching["negative_views"] = {
            **teaching.get("negative_views", {}),
            **{
                call["candidate_id"]: copy.deepcopy(call["views"])
                for call in calls
                if call["call"] == "reject"
            },
        }
        table = parent.get("object_identity_cases") or {
            "schema": IDENTITY_CASES_SCHEMA,
            "cases": [],
        }
        child["object_identity_cases"] = {
            **table,
            "cases": [*table["cases"], *rejected],
        }
    child["object_identity_teaching"] = teaching
    child["direct_visual_teaching"] = [
        *parent.get("direct_visual_teaching", []),
        copy.deepcopy(provenance),
    ]
    return child


def publish_visual_cases(
    parent_path: Path,
    parent_sha256: str,
    additions_path: Path,
    output_path: Path,
    *,
    build_recall_cache: bool = False,
) -> dict:
    """Publish a new immutable child; this is visual teaching, not a growth round."""
    if output_path.exists():
        raise VisualTeachingError("output_already_exists")
    source_dir = parent_path if parent_path.is_dir() else parent_path.parent
    if output_path.resolve().is_relative_to(source_dir.resolve()):
        raise VisualTeachingError("output_inside_parent")
    snapshot = load_memory_snapshot(parent_path)
    if snapshot.status != "squint" or not isinstance(snapshot.memory, dict):
        raise VisualTeachingError("parent_memory_invalid")
    if snapshot.sha256 != parent_sha256:
        raise VisualTeachingError("parent_pin_stale")
    parent = snapshot.memory
    if prepare_identity(parent).get("outcome") != "prepared":
        raise VisualTeachingError("parent_identity_teaching_invalid")
    source_paths = {Path(__file__).resolve()}
    for function in (prepare_identity, prepare_recall, _validate_memory):
        module_path = sys.modules[function.__module__].__file__
        if not isinstance(module_path, str):
            raise VisualTeachingError("builder_source_file_unavailable")
        source_paths.add(Path(module_path).resolve())
    source_pins = {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in source_paths
    }
    addition_bytes = additions_path.read_bytes()
    additions = json.loads(addition_bytes)
    cases, calls = validate_additions(parent, additions)
    digest = hashlib.sha256(addition_bytes).hexdigest()
    provenance = {
        "schema": SCHEMA,
        "kind": "independent_direct_visual_teaching",
        "reader": additions["reader"],
        "parent_revision": parent["revision"],
        "parent_manifest_sha256": parent_sha256,
        "additions_sha256": digest,
        "additions_source": str(additions_path.resolve()),
        "builder_source_sha256": source_pins,
        "case_ids": [c["case_id"] for c in cases],
        "calls": calls,
        "configuration_extension": "pending_C2",
    }
    child = apply_validated_additions(parent, cases, calls, provenance)
    child["revision"] = f"{parent['revision']}+direct-visual-{digest[:16]}"
    child["parent_revision"] = parent["revision"]
    child["parent_manifest_sha256"] = parent_sha256
    try:
        _validate_memory(child)
    except SquintMemoryError as error:
        raise VisualTeachingError(f"child_memory_invalid:{error.code}") from error
    if prepare_identity(child).get("outcome") != "prepared":
        raise VisualTeachingError("child_identity_preparation_failed")
    scope = identity_condition_views(child)
    if scope.get("outcome") != "scoped" or any(
        (call["candidate_id"] in scope["views"]) != (call["call"] == "confirm")
        for call in calls
    ):
        raise VisualTeachingError("child_diagnosis_scope_failed")
    prepared = prepare_recall(child) if build_recall_cache else None
    if prepared is not None and prepared.get("outcome") != "prepared":
        raise VisualTeachingError("child_recall_preparation_failed")
    if hashlib.sha256(snapshot.path.read_bytes()).hexdigest() != parent_sha256:
        raise VisualTeachingError("parent_changed_before_publication")
    if any(
        hashlib.sha256(Path(path).read_bytes()).hexdigest() != pin
        for path, pin in source_pins.items()
    ):
        raise VisualTeachingError("builder_source_changed_before_publication")
    publication = save_memory(child, output_path, prepared_recall=prepared)
    readback = load_memory_snapshot(output_path)
    restored = readback.memory
    if not isinstance(restored, dict) or restored["cases"] != child["cases"]:
        raise VisualTeachingError("child_cases_readback_failed")
    for key in (
        "parent_revision",
        "parent_manifest_sha256",
        "object_identity_teaching",
        "object_identity_cases",
        "full_profile_contexts",
        "full_profile_payloads",
        "procedure_experiences",
    ):
        if restored.get(key) != child.get(key):
            raise VisualTeachingError(f"child_preservation_failed:{key}")
    if prepare_identity(restored).get("outcome") != "prepared":
        raise VisualTeachingError("child_identity_readback_failed")
    if identity_condition_views(restored).get("views") != scope["views"]:
        raise VisualTeachingError("child_diagnosis_scope_readback_failed")
    if hashlib.sha256(snapshot.path.read_bytes()).hexdigest() != parent_sha256:
        raise VisualTeachingError("parent_changed_during_publication")
    return {
        **publication,
        "outcome": "visual_child_published",
        "case_ids": provenance["case_ids"],
        "confirmed_case_ids": [
            call["candidate_id"] for call in calls if call["call"] == "confirm"
        ],
        "negative_case_ids": [
            call["candidate_id"] for call in calls if call["call"] == "reject"
        ],
        "configuration_extension": "pending_C2",
        "parent_integrity": "unchanged_verified",
        "parent_records": "retained_verified",
        "builder_source_sha256": source_pins,
    }
