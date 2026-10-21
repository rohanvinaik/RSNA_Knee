"""Reviewed identity-seed publication from the provisional candidate memory.

Automatic memory stays a candidate catalogue. Each explicit visual call writes
signed identity teaching on exactly the views it reviewed. Confirm is a positive
case of the proposed identity (+1). Reject, or a confirm's ``negative_views``,
is an ordinary negative identity case of the proposed identity (-1): a real case
on that question's negative side, never a veto. ``also_positive`` records a
known alternative identity of the pictured support (+1 on that identity).
Unsure writes nothing. Negative and alternative-identity records are kept apart
from the cases diagnosis recall reads. Diagnosis fields of object cases are
never edited; the whole-condition configuration cases are rebuilt from the
confirmed object cases by the existing builder, each role on the views where
its object's identity holds (CLASSICAL_AI_BUILD_DESIGN §5.1).
"""

from __future__ import annotations

import copy
import re
from collections.abc import Collection, Mapping, Sequence
from pathlib import Path
from typing import Any

from knee.diagnosis.squint_configurations import (
    ConfigurationProfileError,
    with_configuration_cases,
)
from knee.diagnosis.squint_interfaces import parse_territory_bank_name
from knee.diagnosis.squint_memory import (
    MemorySnapshot,
    SquintMemoryError,
    _full_profile_from_validated_case,
    _json_sha256,
    _link_configuration_full_profiles,
    _validate_memory,
    full_profile_from_case,
    save_memory,
)

REVIEW_SCHEMA = "knee.object-bootstrap-review/v1"
CALLS_SCHEMA = "knee.object-identity-calls/v1"
TEACHING_SCHEMA = "knee.object-identity-teaching/v1"
IDENTITY_CASES_SCHEMA = "knee.object-identity-cases/v1"
CALL_VALUES = ("confirm", "reject", "unsure")
_SHA = re.compile(r"[0-9a-f]{64}")
_FULL_KEYS = ("payload_ref", "context_ref", "product_record_sha256")
_CALL_KEYS = frozenset({"candidate_id", "call", "notes"})
_OPTIONAL_CALL_KEYS = frozenset({"views", "negative_views", "also_positive", "reader"})
_VIEW_FIELDS = ("orientation", "fluid_sensitive", "fat_suppression")


class SquintBootstrapError(ValueError):
    """A named refusal of the identity-seed path; nothing is written."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _fail(code: str) -> SquintBootstrapError:
    return SquintBootstrapError(code)


def _is_sha(value: object) -> bool:
    return isinstance(value, str) and _SHA.fullmatch(value) is not None


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_configuration(case: Mapping[str, Any]) -> bool:
    return case["subject"].startswith("diagnosis/")


def _clean_memory(memory: object) -> dict[str, Any]:
    try:
        return _validate_memory(memory)
    except SquintMemoryError as error:
        raise _fail("invalid_snapshot_state") from error


def _profile_views(case: Mapping[str, Any]) -> list[list[str]]:
    profile = case.get("profile")
    banks = profile.get("banks") if isinstance(profile, Mapping) else None
    if not isinstance(banks, Mapping):
        raise _fail("profile_banks_invalid")
    views: set[tuple[str, str, str]] = set()
    for name in banks:
        parsed = parse_territory_bank_name(name)
        view = parsed.get("view") if parsed is not None else None
        if (
            isinstance(view, list)
            and len(view) == 3
            and all(isinstance(value, str) for value in view)
        ):
            views.add(tuple(view))
    return [list(view) for view in sorted(views)]


def _entry(case: Mapping[str, Any], memory: Mapping[str, Any]) -> dict[str, Any]:
    full = case.get("full_profile")
    source = case.get("full_source")
    if not isinstance(full, dict) or not all(
        _text(full.get(key)) for key in _FULL_KEYS
    ):
        raise _fail("full_profile_ref_missing")
    if not isinstance(source, dict) or not _text(source.get("product_sha256")):
        raise _fail("source_product_missing")
    identities = memory.get("source_identities")
    identity = (
        identities.get(case["study_uid"]) if isinstance(identities, dict) else None
    )
    if (
        isinstance(identity, dict)
        and identity.get("product_sha256") != source["product_sha256"]
    ):
        raise _fail("source_product_mismatch")
    return {
        "candidate_id": case["case_id"],
        "case_id": case["case_id"],
        "study_uid": case["study_uid"],
        "subject": case["subject"],
        "profile_sha256": _json_sha256(case["profile"]),
        "full_profile": copy.deepcopy(full),
        "source_product_sha256": source["product_sha256"],
        "profile_views": _profile_views(case),
    }


def build_review(
    memory: Any,
    source_manifest_sha256: str,
    case_ids: Sequence[str],
    *,
    sheets: Mapping[str, str] | None = None,
    sanity_report: Any = None,
) -> dict[str, Any]:
    """Pin the selected original object candidates for visual review."""
    if not _is_sha(source_manifest_sha256):
        raise _fail("source_manifest_sha256_invalid")
    clean = _clean_memory(memory)
    if (
        isinstance(case_ids, (str, bytes))
        or not isinstance(case_ids, Sequence)
        or len(case_ids) == 0
    ):
        raise _fail("case_ids_invalid")
    by_id = {case["case_id"]: case for case in clean["cases"]}
    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []
    for case_id in case_ids:
        if not _text(case_id):
            raise _fail("case_ids_invalid")
        if case_id in seen:
            raise _fail("duplicate_candidate")
        seen.add(case_id)
        case = by_id.get(case_id)
        if case is None:
            raise _fail("unknown_candidate")
        if _is_configuration(case):
            raise _fail("configuration_case_not_selectable")
        candidates.append(_entry(case, clean))
    if sheets is not None:
        if not isinstance(sheets, Mapping):
            raise _fail("sheets_invalid")
        for case_id, path in sheets.items():
            if case_id not in seen:
                raise _fail("sheet_candidate_unknown")
            if not _text(path):
                raise _fail("sheets_invalid")
        for entry in candidates:
            if entry["case_id"] in sheets:
                entry["sheet_path"] = sheets[entry["case_id"]]
    review: dict[str, Any] = {
        "schema": REVIEW_SCHEMA,
        "source_manifest_sha256": source_manifest_sha256,
        "candidates": candidates,
    }
    if sanity_report is not None:
        review["sanity_report"] = copy.deepcopy(sanity_report)
    return review


def _review_candidates(review: object) -> dict[str, dict[str, Any]]:
    if (
        not isinstance(review, dict)
        or review.get("schema") != REVIEW_SCHEMA
        or not _is_sha(review.get("source_manifest_sha256"))
    ):
        raise _fail("review_malformed")
    items = review.get("candidates")
    if not isinstance(items, list) or not items:
        raise _fail("review_malformed")
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            raise _fail("review_malformed")
        candidate_id = item.get("candidate_id")
        full = item.get("full_profile")
        profile_views = item.get("profile_views")
        if (
            not _text(candidate_id)
            or item.get("case_id") != candidate_id
            or not _text(item.get("study_uid"))
            or not _text(item.get("subject"))
            or not _is_sha(item.get("profile_sha256"))
            or not _text(item.get("source_product_sha256"))
            or not isinstance(full, dict)
            or not all(_text(full.get(key)) for key in _FULL_KEYS)
        ):
            raise _fail("review_malformed")
        if profile_views is not None and (
            not isinstance(profile_views, list)
            or any(
                not isinstance(view, list)
                or len(view) != 3
                or not all(isinstance(value, str) for value in view)
                for view in profile_views
            )
            or len({tuple(view) for view in profile_views}) != len(profile_views)
        ):
            raise _fail("review_malformed")
        if candidate_id in result:
            raise _fail("duplicate_candidate")
        result[candidate_id] = item
    return result


def _facets_valid(views: object) -> bool:
    """A nonempty list of unique exact (orientation, fluid, fat) string triples."""
    return (
        isinstance(views, list)
        and bool(views)
        and all(
            isinstance(view, list)
            and len(view) == 3
            and all(isinstance(value, str) for value in view)
            for view in views
        )
        and len({tuple(view) for view in views}) == len(views)
    )


def _drawn_views(candidate: Mapping[str, Any]) -> set[tuple[str, ...]]:
    """Views whose native image was read and whose recorded support was drawn."""
    evidence = candidate.get("evidence")
    panels = evidence.get("panels") if isinstance(evidence, Mapping) else None
    drawn: set[tuple[str, ...]] = set()
    if isinstance(panels, list):
        for panel in panels:
            if not isinstance(panel, Mapping):
                continue
            view = panel.get("view")
            if (
                panel.get("image_state") == "read"
                and panel.get("support_state") == "drawn"
                and isinstance(view, Mapping)
            ):
                key = tuple(view.get(name) for name in _VIEW_FIELDS)
                if all(isinstance(value, str) for value in key):
                    drawn.add(key)
    return drawn


def _check_facets(candidate: Mapping[str, Any], views: list) -> None:
    """Each called view exists in the source profile and in a drawn native panel."""
    available = candidate.get("profile_views")
    if not isinstance(available, list) or any(view not in available for view in views):
        raise _fail("view_not_available")
    drawn = _drawn_views(candidate)
    if any(tuple(view) not in drawn for view in views):
        raise _fail("view_not_drawn")


def _rejected_views(
    candidate: Mapping[str, Any], record: Mapping[str, Any]
) -> tuple[list[list[str]] | None, str | None]:
    """A reject's negative views: its ``views``, else every drawn profile view.

    Returns (views, None), or (None, reason) when no pictured support exists to
    reject; that call then writes no negative case and its reason is kept.
    """
    if "views" in record:
        return copy.deepcopy(record["views"]), None
    available = candidate.get("profile_views")
    if not isinstance(available, list):
        return None, "profile_views_unrecorded"
    drawn = _drawn_views(candidate)
    resolved = [list(view) for view in available if tuple(view) in drawn]
    if not resolved:
        return None, "no_drawn_profile_view"
    return resolved, None


def alternative_entry_id(case_id: str, identity: str) -> str:
    """The teaching id of one case's positive on a known alternative identity."""
    return f"{case_id}::also_positive::{identity}"


def _alternatives_shape_valid(value: object) -> bool:
    if not isinstance(value, list) or not value:
        return False
    identities: list[str] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"identity", "views"}:
            return False
        if not _text(item["identity"]):
            return False
        identities.append(item["identity"])
    return len(set(identities)) == len(identities)


def _check_alternatives(
    candidate: Mapping[str, Any],
    alternatives: list[dict[str, Any]],
    known_subjects: Collection[str] | None,
) -> None:
    for item in alternatives:
        identity = item["identity"]
        if identity.startswith("diagnosis/"):
            raise _fail("also_positive_identity_invalid")
        if identity == candidate.get("subject"):
            raise _fail("also_positive_identity_is_proposed")
        if known_subjects is not None and identity not in known_subjects:
            raise _fail("also_positive_identity_unknown")
        if not _facets_valid(item["views"]):
            raise _fail("call_views_invalid")
        _check_facets(candidate, item["views"])


def _check_one_identity_per_view(
    candidate: Mapping[str, Any], record: Mapping[str, Any]
) -> None:
    """A view carries one sign of the proposed identity and at most one identity.

    Omitting a confirm's ``views`` asserts the whole case, which holds every
    view, so a whole-case confirm leaves no view for a second claim.
    """
    proposed: set[tuple[str, ...]] = set()
    if record["call"] == "confirm":
        positive = record.get("views", candidate.get("profile_views"))
        if isinstance(positive, list):
            proposed = {tuple(view) for view in positive}
    negative = {tuple(view) for view in record.get("negative_views", ())}
    if proposed & negative:
        raise _fail("call_views_overlap")
    claimed = set(proposed)
    for item in record.get("also_positive", ()):
        views = {tuple(view) for view in item["views"]}
        if claimed & views:
            raise _fail("call_views_overlap")
        claimed |= views


def validate_calls(
    review: Any,
    calls: Any,
    review_sha256: str,
    *,
    known_subjects: Collection[str] | None = None,
) -> dict[str, Any]:
    """Validate recorded visual calls against a review and its byte pin.

    Confirm writes +1 on the proposed identity (its ``views``, else the whole
    case). Reject writes -1 on it (its ``views``, else every drawn profile
    view); a confirm's ``negative_views`` writes -1 on those views. Each
    ``also_positive`` entry writes +1 on another identity the memory names, on
    its own views. Unsure writes nothing on the proposed identity. Every called
    view must exist in the source profile and in a drawn native panel.
    ``known_subjects``, when given, are the object subjects the memory names.
    """
    if not _is_sha(review_sha256):
        raise _fail("review_sha256_invalid")
    candidates = _review_candidates(review)
    if (
        not isinstance(calls, dict)
        or calls.get("schema") != CALLS_SCHEMA
        or not _text(calls.get("reader"))
        or not isinstance(calls.get("calls"), list)
        or "review_sha256" not in calls
    ):
        raise _fail("calls_malformed")
    if calls["review_sha256"] != review_sha256:
        raise _fail("stale_review_pin")
    seen: set[str] = set()
    records: list[dict[str, Any]] = []
    negative_views: dict[str, list[list[str]]] = {}
    not_written: dict[str, str] = {}
    alternatives: dict[str, list[dict[str, Any]]] = {}
    for record in calls["calls"]:
        if not isinstance(record, dict) or not (
            _CALL_KEYS <= set(record) <= _CALL_KEYS | _OPTIONAL_CALL_KEYS
        ):
            raise _fail("calls_malformed")
        candidate_id = record["candidate_id"]
        if not _text(candidate_id):
            raise _fail("calls_malformed")
        if candidate_id not in candidates:
            raise _fail("unknown_candidate")
        call = record["call"]
        if call not in CALL_VALUES:
            raise _fail("call_value_invalid")
        if not isinstance(record["notes"], str):
            raise _fail("call_notes_invalid")
        # A call merged from another reviewer's file keeps that reviewer by name.
        if "reader" in record and not _text(record["reader"]):
            raise _fail("call_reader_invalid")
        candidate = candidates[candidate_id]
        if "views" in record:
            if not _facets_valid(record["views"]):
                raise _fail("call_views_invalid")
            if call in ("confirm", "reject"):
                _check_facets(candidate, record["views"])
        if "negative_views" in record:
            if call != "confirm":
                raise _fail("negative_views_require_confirm")
            if not _facets_valid(record["negative_views"]):
                raise _fail("call_negative_views_invalid")
            _check_facets(candidate, record["negative_views"])
        if "also_positive" in record:
            if not _alternatives_shape_valid(record["also_positive"]):
                raise _fail("call_also_positive_invalid")
            _check_alternatives(candidate, record["also_positive"], known_subjects)
        _check_one_identity_per_view(candidate, record)
        if candidate_id in seen:
            raise _fail("duplicate_call")
        seen.add(candidate_id)
        records.append(copy.deepcopy(record))
        if call == "reject":
            views, reason = _rejected_views(candidate, record)
            if views is None:
                not_written[candidate_id] = str(reason)
            else:
                negative_views[candidate_id] = views
        elif call == "confirm" and "negative_views" in record:
            negative_views[candidate_id] = copy.deepcopy(record["negative_views"])
        alternatives[candidate_id] = [
            {
                "entry_id": alternative_entry_id(candidate_id, item["identity"]),
                "case_id": candidate_id,
                "identity": item["identity"],
                "views": copy.deepcopy(item["views"]),
            }
            for item in record.get("also_positive", ())
        ]
    confirmed = {item["candidate_id"] for item in records if item["call"] == "confirm"}
    return {
        "outcome": "valid",
        "reader": calls["reader"],
        "confirmed_case_ids": [cid for cid in candidates if cid in confirmed],
        "negative_case_ids": [cid for cid in candidates if cid in negative_views],
        "negative_views": {
            cid: negative_views[cid] for cid in candidates if cid in negative_views
        },
        "negatives_not_written": [
            {"candidate_id": cid, "reason": not_written[cid]}
            for cid in candidates
            if cid in not_written
        ],
        "alternative_positives": [
            entry for cid in candidates for entry in alternatives.get(cid, ())
        ],
        "calls": records,
    }


def adapt_recorded_calls(
    sources: Sequence[tuple[str, str, Sequence[Mapping[str, Any]]]],
    review_sha256: str,
) -> dict[str, Any]:
    """Merge recorded visual-call sources into one calls document, scope unchanged.

    ``sources`` is a sequence of ``(origin, reader, records)``: where the records came
    from, who made them, and the recorded calls. Each call keeps its candidate, sign,
    notes, ``views``, a confirm's ``negative_views`` and ``also_positive`` exactly, and
    carries its own reader. A reject recorded with its negative scope in
    ``negative_views`` gets that scope as its own ``views``: dropping it would widen
    the reject to every drawn view, and a view left unasserted stays unasserted. A
    reject giving two different scopes is refused rather than guessed. Other recorded
    keys (a review sheet's ``number``) go to the returned mapping, never into the call.
    A candidate called in two sources is refused. The source records are not changed.
    """
    if not _is_sha(review_sha256):
        raise _fail("review_sha256_invalid")
    allowed = _CALL_KEYS | _OPTIONAL_CALL_KEYS
    calls: list[dict[str, Any]] = []
    mapping: dict[str, dict[str, Any]] = {}
    readers: list[str] = []
    for origin, reader, records in sources:
        if not _text(origin) or not _text(reader) or isinstance(records, (str, bytes)):
            raise _fail("adapt_source_invalid")
        if reader not in readers:
            readers.append(reader)
        for record in records:
            if not isinstance(record, Mapping) or not _CALL_KEYS <= set(record):
                raise _fail("adapt_record_malformed")
            candidate_id = record["candidate_id"]
            if not _text(candidate_id):
                raise _fail("adapt_record_malformed")
            if candidate_id in mapping:
                raise _fail("adapt_duplicate_candidate")
            call = {
                key: copy.deepcopy(record[key])
                for key in sorted(record)
                if key in allowed
            }
            if call["call"] == "reject" and "negative_views" in call:
                scope = call.pop("negative_views")
                if "views" in call and call["views"] != scope:
                    raise _fail("adapt_reject_scope_ambiguous")
                call["views"] = scope
            call.setdefault("reader", reader)
            calls.append(call)
            mapping[candidate_id] = {
                "origin": origin,
                "recorded": {
                    key: copy.deepcopy(record[key])
                    for key in sorted(record)
                    if key not in allowed
                },
            }
    return {
        "calls": {
            "schema": CALLS_SCHEMA,
            "review_sha256": review_sha256,
            "reader": "; ".join(readers) + " (each call names its own reader)",
            "calls": calls,
        },
        "mapping": mapping,
    }


def _verify_candidates(
    memory: Mapping[str, Any], candidates: Mapping[str, Any]
) -> None:
    by_id = {case["case_id"]: case for case in memory["cases"]}
    for entry in candidates.values():
        case = by_id.get(entry["case_id"])
        if case is None:
            raise _fail("unknown_candidate")
        if _is_configuration(case):
            raise _fail("configuration_case_not_selectable")
        if (
            case["study_uid"] != entry["study_uid"]
            or case["subject"] != entry["subject"]
        ):
            raise _fail("source_identity_mismatch")
        if _json_sha256(case["profile"]) != entry["profile_sha256"]:
            raise _fail("profile_digest_mismatch")
        current = _entry(case, memory)
        if (
            "profile_views" in entry
            and current["profile_views"] != entry["profile_views"]
        ):
            raise _fail("profile_views_mismatch")
        if current["full_profile"] != entry["full_profile"]:
            raise _fail("full_profile_ref_mismatch")
        if current["source_product_sha256"] != entry["source_product_sha256"]:
            raise _fail("source_product_mismatch")


def _check_output(output: object, snapshot: MemorySnapshot) -> Path:
    if not isinstance(output, Path) or not output.name or ".." in output.parts:
        raise _fail("output_path_unsafe")
    if output.is_symlink():
        raise _fail("output_path_unsafe")
    if output.parent.exists() and not output.parent.is_dir():
        raise _fail("output_path_unsafe")
    target = output.resolve()
    source_dir = snapshot.path.parent
    if (
        target == snapshot.path
        or target == source_dir
        or source_dir in target.parents
        or target in source_dir.parents
    ):
        raise _fail("output_path_unsafe")
    if output.exists():
        raise _fail("output_exists")
    return output


def _rebuilt_configurations(
    source: Mapping[str, Any], child: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any] | None, str]:
    """Whole-condition cases rebuilt from the child's confirmed object cases.

    The existing builder composes each labelled question of each confirmed
    study exactly as ``compile_bootstrap`` does, from the confirmed object
    cases alone, each role limited to the views where that object's identity
    holds: the one condition view preparation reads (``squint_locator``).
    Missing roles stay explicit, and the study label stays the configuration's
    own call with its own scope. Negative and alternative identity records live
    outside ``cases`` and never become roles. A source with no label ledger
    has no labels to rebuild from, so the child carries none, as before.
    Returns (configuration cases, the child's ledger rows or None, revision).
    """
    ledger = source.get("label_ledger")
    if ledger is None:
        return [], None, child["revision"]
    if not isinstance(ledger, dict):
        raise _fail("label_ledger_invalid")
    from knee.diagnosis.squint_identity import identity_condition_views
    from knee.diagnosis.squint_locator import _scoped_cases, _source

    cases = child["cases"]
    scope = identity_condition_views(child)
    if scope.get("outcome") != "scoped":
        raise _fail("child_identity_teaching_invalid")
    roles = list(_scoped_cases(cases, scope))
    for case, role in zip(cases, roles, strict=True):
        if case["profile"]["banks"] and not role["profile"]["banks"]:
            raise _fail("confirmed_views_hold_no_banks")
    procedures = {_source(case["profile"]).get("procedure") for case in cases}
    if len(procedures) > 1:
        raise _fail("configuration_procedure_mixed")
    rows = {
        uid: copy.deepcopy(ledger[uid])
        for uid in sorted({case["study_uid"] for case in cases})
        if uid in ledger
    }
    staged = {
        "schema": child["schema"],
        "revision": child["revision"],
        "cases": roles,
        "label_ledger": rows,
    }
    try:
        built = with_configuration_cases(
            staged, **({"procedure": procedures.pop()} if procedures else {})
        )
    except ConfigurationProfileError as error:
        raise _fail(f"configuration_rebuild_{error.code}") from error
    return copy.deepcopy(built["cases"][len(roles) :]), rows, built["revision"]


def publish_seed_memory(
    source_snapshot: MemorySnapshot,
    review: Any,
    calls: Any,
    review_sha256: str,
    output: Path,
) -> dict[str, Any]:
    """Publish a child memory holding the reviewed signed identity teaching.

    Confirmed object cases enter ``cases`` exactly as before. Ordinary negative
    identity cases and alternative-identity positives keep their whole source
    case records in ``object_identity_cases``, which only identity teaching
    reads: their condition calls belong to their own proposed subject and never
    reach diagnosis recall. The whole-condition configuration cases are rebuilt
    from the confirmed object cases and the source's label ledger rows for
    their studies, each role on the views where its object's identity holds
    (``_rebuilt_configurations``), so the published child keeps a diagnosis
    voice. Negative-only teaching publishes; a call file that writes no
    identity case of either sign is refused.
    """
    if (
        not isinstance(source_snapshot, MemorySnapshot)
        or source_snapshot.status != "squint"
        or not isinstance(source_snapshot.memory, dict)
        or not _is_sha(source_snapshot.sha256)
        or not isinstance(source_snapshot.path, Path)
    ):
        raise _fail("invalid_snapshot_state")
    memory = _clean_memory(source_snapshot.memory)
    candidates = _review_candidates(review)
    if review["source_manifest_sha256"] != source_snapshot.sha256:
        raise _fail("stale_source_pin")
    known_subjects = {
        case["subject"] for case in memory["cases"] if not _is_configuration(case)
    }
    validated = validate_calls(
        review, calls, review_sha256, known_subjects=known_subjects
    )
    confirmed = set(validated["confirmed_case_ids"])
    negatives = set(validated["negative_case_ids"])
    alternative_cases = {
        entry["case_id"] for entry in validated["alternative_positives"]
    }
    if not confirmed and not negatives and not alternative_cases:
        raise _fail("no_identity_cases_written")
    _verify_candidates(memory, candidates)
    destination = _check_output(output, source_snapshot)

    by_id = {case["case_id"]: case for case in memory["cases"]}
    cases = [copy.deepcopy(c) for c in memory["cases"] if c["case_id"] in confirmed]
    identity_cases = [
        copy.deepcopy(by_id[cid])
        for cid in candidates
        if cid in negatives or cid in alternative_cases
    ]
    contexts_table = memory.get("full_profile_contexts")
    payloads_table = memory.get("full_profile_payloads")
    if not isinstance(contexts_table, dict) or not isinstance(payloads_table, dict):
        raise _fail("full_tables_missing")
    all_contexts = contexts_table.get("contexts")
    all_payloads = payloads_table.get("payloads")
    if not isinstance(all_contexts, dict) or not isinstance(all_payloads, dict):
        raise _fail("full_tables_missing")
    payload_refs: set[str] = set()
    context_refs: set[str] = set()
    for case in cases + identity_cases:
        refs = [case["full_profile"]]
        extra = case.get("full_profile_refs")
        if isinstance(extra, dict):
            refs.extend(v for v in extra.values() if isinstance(v, dict))
        for ref in refs:
            payload_refs.add(ref["payload_ref"])
            context_refs.add(ref["context_ref"])
    payloads: dict[str, Any] = {}
    for ref in sorted(payload_refs):
        if ref not in all_payloads:
            raise _fail("full_ref_missing")
        payloads[ref] = copy.deepcopy(all_payloads[ref])
        context_refs.add(payloads[ref].get("context_ref"))
    contexts: dict[str, Any] = {}
    for ref in sorted(context_refs, key=str):
        if ref not in all_contexts:
            raise _fail("full_ref_missing")
        contexts[ref] = copy.deepcopy(all_contexts[ref])
    identities = memory.get("source_identities")
    if not isinstance(identities, dict):
        raise _fail("source_identity_missing")
    source_identities: dict[str, Any] = {}
    for uid in sorted({case["study_uid"] for case in cases + identity_cases}):
        if uid not in identities:
            raise _fail("source_identity_missing")
        source_identities[uid] = copy.deepcopy(identities[uid])

    child: dict[str, Any] = {
        "schema": memory["schema"],
        # The signed-teaching schema enters the digest: a child holding negative
        # and alternative-identity cases never shares a revision with the
        # positive-only child an earlier publisher made from the same inputs.
        "revision": "{}+object-identity-seed-{}".format(
            memory["revision"],
            _json_sha256(
                [source_snapshot.sha256, review_sha256, calls, IDENTITY_CASES_SCHEMA]
            )[:16],
        ),
        "questions": copy.deepcopy(memory["questions"]),
        "procedure": copy.deepcopy(memory.get("procedure")),
        "source_identities": source_identities,
        "cases": cases,
        "full_profile_contexts": {
            "schema": contexts_table["schema"],
            "contexts": contexts,
        },
        "full_profile_payloads": {
            "schema": payloads_table["schema"],
            "payloads": payloads,
        },
        "object_identity_cases": {
            "schema": IDENTITY_CASES_SCHEMA,
            "cases": identity_cases,
        },
        "object_identity_teaching": {
            "schema": TEACHING_SCHEMA,
            "reader": validated["reader"],
            "confirmed_case_ids": list(validated["confirmed_case_ids"]),
            "negative_case_ids": list(validated["negative_case_ids"]),
            "negative_views": copy.deepcopy(validated["negative_views"]),
            "negatives_not_written": copy.deepcopy(validated["negatives_not_written"]),
            "alternative_positives": copy.deepcopy(validated["alternative_positives"]),
            "calls": validated["calls"],
            "review_sha256": review_sha256,
            "source_manifest_sha256": source_snapshot.sha256,
            "source_revision": memory["revision"],
            "reviewed_candidate_ids": list(candidates),
            "full_profile_role": "retained_source_only",
            "identity_scope": "per_call_reviewed_views_or_whole_case",
            "negative_scope": (
                "reject_views_else_every_drawn_profile_view_or_confirm_negative_views"
            ),
        },
    }
    for key in ("source", "object_order"):
        if key in memory:
            child[key] = copy.deepcopy(memory[key])
    configurations, ledger, revision = _rebuilt_configurations(memory, child)
    if ledger is not None:
        child["label_ledger"] = ledger
        child["revision"] = revision
        child["cases"] = [*cases, *configurations]
        _link_configuration_full_profiles(child)
    try:
        _validate_memory(child)
        for case in cases:
            full_profile_from_case(child, case)
        for record in identity_cases:
            _full_profile_from_validated_case(
                child, record, record["full_profile"], record["subject"]
            )
    except SquintMemoryError as error:
        raise _fail("child_memory_invalid") from error
    from knee.diagnosis.squint_identity import prepare_identity

    if prepare_identity(child).get("outcome") != "prepared":
        raise _fail("child_identity_teaching_invalid")
    receipt = save_memory(child, destination)
    return {
        "outcome": "published",
        "manifest": receipt["manifest"],
        "sha256": receipt["sha256"],
        "case_count": receipt["case_count"],
        "object_case_count": len(cases),
        "configuration_case_count": len(configurations),
        "confirmed_case_ids": list(validated["confirmed_case_ids"]),
        "negative_case_ids": list(validated["negative_case_ids"]),
        "alternative_positive_ids": [
            entry["entry_id"] for entry in validated["alternative_positives"]
        ],
    }
