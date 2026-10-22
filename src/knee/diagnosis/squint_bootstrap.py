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

A growth round's admissions are reviewed the same way, on their own review
(ADMISSION_REVIEW_SCHEMA; CLASSICAL_AI_BUILD_DESIGN §§7, 7.1, 13 step 5). An
admission holds a cheap profile, its regions and recognition-derived lineage, and
no full profile; none is required or made. Its sheet is the squint tile window the
recognition read on each native slice, so a view counts as drawn when its window
was drawn on a read slice. A call means what it means on a seed review, and is
applied only where it asserts. A reject's views (every drawn profile view when it
names none), or a confirm's ``negative_views``, become an ordinary negative
identity case of the proposed identity on exactly those views; ``also_positive``
gives its views to the named identity. Every admitted view not taken keeps
speaking for the proposed identity with its recognition-derived lineage and its
condition evidence: the case stays confirmed in ``cases`` and its round's confirm
row takes the seed's mixed form (``views`` the remaining views, beside
``negative_views`` and ``also_positive``). Only when every admitted view is taken
does the whole case move to ``object_identity_cases``, its row then the reviewer's
reject row with that reader. The corrected facets name the reviewer through the
case's identity record. Confirm otherwise leaves the admission as it is and records
the reader's confirmation: a recognition-derived case does not become an
independent confirmation (OpenSpec ``complete-signed-bootstrap-loop``). Unsure
changes nothing. The corrected memory is a new child of the reviewed one, keeping
every other record.
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
    load_memory,
    save_memory,
)

REVIEW_SCHEMA = "knee.object-bootstrap-review/v1"
ADMISSION_REVIEW_SCHEMA = "knee.object-admission-review/v1"
ADMISSION_RECORD_SCHEMA = "knee.object-admission-review-record/v1"
CORRECTION_SCHEMA = "knee.object-admission-correction/v1"
CORRECTION_KIND = "visual_correction_of_recognition_derived_admission"
CALLS_SCHEMA = "knee.object-identity-calls/v1"
TEACHING_SCHEMA = "knee.object-identity-teaching/v1"
IDENTITY_CASES_SCHEMA = "knee.object-identity-cases/v1"
# The growth module's lineage kind for its admissions (squint_identity_growth).
RECOGNITION_KIND = "recognition_derived_identity"
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
    _attach_sheets(candidates, seen, sheets)
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


def _attach_sheets(
    candidates: list[dict[str, Any]],
    selected: Collection[str],
    sheets: Mapping[str, str] | None,
) -> None:
    """Give each selected candidate its sheet path; an unselected or empty one refuses."""
    if sheets is None:
        return
    if not isinstance(sheets, Mapping):
        raise _fail("sheets_invalid")
    for case_id, path in sheets.items():
        if case_id not in selected:
            raise _fail("sheet_candidate_unknown")
        if not _text(path):
            raise _fail("sheets_invalid")
    for entry in candidates:
        if entry["case_id"] in sheets:
            entry["sheet_path"] = sheets[entry["case_id"]]


# ------------------------------------------------------ admission review
#
# A growth round's admissions are inspected on their pictures before its child
# becomes the next parent, and a wrong one returns as a scoped negative
# (CLASSICAL_AI_BUILD_DESIGN §§7.1, 13 step 5). Nothing here recognizes or
# scores: the review pins what the round admitted and what a reviewer saw.


def _teaching_rows(
    memory: Mapping[str, Any],
) -> tuple[dict[str, list[Mapping[str, Any]]], set[str]]:
    """Each candidate's teaching call rows and the confirmed case ids of a memory."""
    teaching = memory.get("object_identity_teaching")
    if not isinstance(teaching, Mapping) or teaching.get("schema") != TEACHING_SCHEMA:
        raise _fail("identity_teaching_missing")
    calls = teaching.get("calls")
    confirmed = teaching.get("confirmed_case_ids")
    if (
        not isinstance(calls, list)
        or not all(isinstance(row, Mapping) for row in calls)
        or not isinstance(confirmed, list)
        or not all(_text(item) for item in confirmed)
    ):
        raise _fail("identity_teaching_invalid")
    rows: dict[str, list[Mapping[str, Any]]] = {}
    for row in calls:
        if _text(row.get("candidate_id")):
            rows.setdefault(row["candidate_id"], []).append(row)
    return rows, set(confirmed)


def _standing_admission(
    case: Mapping[str, Any],
    rows_by_id: Mapping[str, list[Mapping[str, Any]]],
    confirmed: Collection[str],
) -> tuple[Mapping[str, Any] | None, str | None]:
    """The case's own recognition-derived confirm row, or why it is no standing admission.

    A standing admission is a growth case (``identity_growth`` of RECOGNITION_KIND)
    that is still confirmed by exactly one call row: the confirm its round wrote,
    marked with the same lineage kind and parent, naming views its profile holds.
    A row that already carries ``negative_views`` or ``also_positive`` was
    corrected in part by an earlier review: its remaining positive views keep
    speaking, and it is not reviewed again as an untouched admission.
    """
    lineage = case.get("identity_growth")
    if not isinstance(lineage, Mapping) or lineage.get("kind") != RECOGNITION_KIND:
        return None, "candidate_not_recognition_derived"
    rows = rows_by_id.get(case["case_id"], [])
    mark = rows[0].get("identity_growth") if len(rows) == 1 else None
    if (
        len(rows) != 1
        or rows[0].get("call") != "confirm"
        or not isinstance(mark, Mapping)
        or mark.get("kind") != RECOGNITION_KIND
        or mark.get("parent_manifest_sha256") != lineage.get("parent_manifest_sha256")
    ):
        return None, "admission_call_not_found"
    if "negative_views" in rows[0] or "also_positive" in rows[0]:
        return None, "admission_corrected_in_part"
    if case["case_id"] not in confirmed:
        return None, "admission_not_confirmed"
    views = rows[0].get("views")
    available = _profile_views(case)
    if not _facets_valid(views) or any(view not in available for view in views):
        return None, "admission_views_invalid"
    return rows[0], None


def round_admissions(memory: Any, *, round_index: int | None = None) -> dict[str, Any]:
    """One growth round's admissions (default: the latest), each standing or why not.

    A standing admission can be reviewed (``build_admission_review``). One that no
    longer stands keeps its reason: ``corrected_negative`` once a review returned
    the whole case as a negative, else the reason ``_standing_admission`` names
    (``admission_corrected_in_part`` once a review corrected some of its facets).
    """
    clean = _clean_memory(memory)
    growth = clean.get("object_identity_growth")
    rounds = growth.get("rounds") if isinstance(growth, Mapping) else None
    if not isinstance(rounds, list) or not rounds:
        raise _fail("memory_has_no_growth_round")
    index = len(rounds) - 1 if round_index is None else round_index
    if type(index) is not int or not 0 <= index < len(rounds):
        raise _fail("growth_round_unknown")
    entry = rounds[index]
    admitted = entry.get("admitted_case_ids") if isinstance(entry, Mapping) else None
    if not isinstance(admitted, list) or not all(_text(item) for item in admitted):
        raise _fail("growth_round_malformed")
    rows_by_id, confirmed = _teaching_rows(clean)
    negatives = clean["object_identity_teaching"].get("negative_case_ids")
    corrected = set(negatives) if isinstance(negatives, list) else set()
    by_id = {case["case_id"]: case for case in clean["cases"]}
    standing: list[str] = []
    not_standing: list[dict[str, str]] = []
    for case_id in admitted:
        case = by_id.get(case_id)
        if case is None:
            reason = (
                "corrected_negative" if case_id in corrected else "case_not_in_cases"
            )
        else:
            reason = _standing_admission(case, rows_by_id, confirmed)[1]
        if reason is None:
            standing.append(case_id)
        else:
            not_standing.append({"case_id": case_id, "reason": reason})
    return {
        "round_index": index,
        "round_count": len(rounds),
        "parent_manifest_sha256": entry.get("parent_manifest_sha256"),
        "decisions_sha256": entry.get("decisions_sha256"),
        "admitted_case_ids": list(admitted),
        "standing": standing,
        "not_standing": not_standing,
    }


def _admission_entry(case: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "candidate_id": case["case_id"],
        "case_id": case["case_id"],
        "study_uid": case["study_uid"],
        "subject": case["subject"],
        "case_sha256": _json_sha256(case),
        "admission_call_sha256": _json_sha256(row),
        "admission_call": copy.deepcopy(dict(row)),
        "admitted_views": copy.deepcopy(row["views"]),
        "profile_sha256": _json_sha256(case["profile"]),
        "profile": copy.deepcopy(case["profile"]),
        "profile_views": _profile_views(case),
        "regions": copy.deepcopy(case["regions"]),
        "identity_growth": copy.deepcopy(case["identity_growth"]),
    }
    if isinstance(case.get("full_profile"), dict):
        entry["full_profile"] = copy.deepcopy(case["full_profile"])
    return entry


def build_admission_review(
    memory: Any,
    source_manifest_sha256: str,
    case_ids: Sequence[str],
    *,
    sheets: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Pin the selected standing admissions of a growth child for visual review.

    Each candidate carries its cheap profile, regions, profile views, admitted
    views and recognition-derived lineage, pinned by the digests of its whole case
    record and of its admission's confirm row. It carries a full profile only when
    the case holds one; none is required or made.
    """
    if not _is_sha(source_manifest_sha256):
        raise _fail("source_manifest_sha256_invalid")
    clean = _clean_memory(memory)
    if (
        isinstance(case_ids, (str, bytes))
        or not isinstance(case_ids, Sequence)
        or len(case_ids) == 0
    ):
        raise _fail("case_ids_invalid")
    rows_by_id, confirmed = _teaching_rows(clean)
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
        row, reason = _standing_admission(case, rows_by_id, confirmed)
        if row is None:
            raise _fail(str(reason))
        candidates.append(_admission_entry(case, row))
    _attach_sheets(candidates, seen, sheets)
    return {
        "schema": ADMISSION_REVIEW_SCHEMA,
        "source_manifest_sha256": source_manifest_sha256,
        "source_revision": clean["revision"],
        "candidates": candidates,
    }


def _strict_sha256(value: object) -> str | None:
    """The canonical digest of a strict-JSON value, or None for any other value."""
    try:
        return _json_sha256(value)
    except (TypeError, ValueError):
        return None


def _admission_review_candidates(review: object) -> dict[str, dict[str, Any]]:
    if (
        not isinstance(review, dict)
        or review.get("schema") != ADMISSION_REVIEW_SCHEMA
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
        lineage = item.get("identity_growth")
        profile = item.get("profile")
        admitted = item.get("admitted_views")
        available = item.get("profile_views")
        if (
            not _text(candidate_id)
            or item.get("case_id") != candidate_id
            or not _text(item.get("study_uid"))
            or not _text(item.get("subject"))
            or not all(
                _is_sha(item.get(key))
                for key in ("case_sha256", "admission_call_sha256", "profile_sha256")
            )
            or not isinstance(profile, dict)
            or _strict_sha256(profile) != item["profile_sha256"]
            or not isinstance(item.get("regions"), list)
            or not isinstance(lineage, dict)
            or lineage.get("kind") != RECOGNITION_KIND
            or not _facets_valid(available)
            or not _facets_valid(admitted)
            or any(view not in available for view in admitted)
        ):
            raise _fail("review_malformed")
        if candidate_id in result:
            raise _fail("duplicate_candidate")
        result[candidate_id] = item
    return result


def _candidates_of(review: object) -> tuple[dict[str, dict[str, Any]], bool]:
    """The pinned candidates of a seed or an admission review, and which it is."""
    if isinstance(review, dict) and review.get("schema") == ADMISSION_REVIEW_SCHEMA:
        return _admission_review_candidates(review), True
    return _review_candidates(review), False


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


def _drawn_views(
    candidate: Mapping[str, Any], drawn_key: str = "support_state"
) -> set[tuple[str, ...]]:
    """Views whose native image was read and whose recorded evidence was drawn.

    On a seed review the evidence is the recorded teacher support
    (``support_state``); on an admission review it is the squint tile window the
    recognition read (``window_state``). Neither stands in for the other.
    """
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
                and panel.get(drawn_key) == "drawn"
                and isinstance(view, Mapping)
            ):
                key = tuple(view.get(name) for name in _VIEW_FIELDS)
                if all(isinstance(value, str) for value in key):
                    drawn.add(key)
    return drawn


def _check_facets(
    candidate: Mapping[str, Any], views: list, drawn_key: str = "support_state"
) -> None:
    """Each called view exists in the source profile and in a drawn native panel."""
    available = candidate.get("profile_views")
    if not isinstance(available, list) or any(view not in available for view in views):
        raise _fail("view_not_available")
    drawn = _drawn_views(candidate, drawn_key)
    if any(tuple(view) not in drawn for view in views):
        raise _fail("view_not_drawn")


def _rejected_views(
    candidate: Mapping[str, Any],
    record: Mapping[str, Any],
    drawn_key: str = "support_state",
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
    drawn = _drawn_views(candidate, drawn_key)
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
    drawn_key: str = "support_state",
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
        _check_facets(candidate, item["views"], drawn_key)


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


def _check_admission_claims(
    candidate: Mapping[str, Any],
    record: Mapping[str, Any],
    negative: Sequence[Sequence[str]],
) -> None:
    """A call on an admission keeps one claim per view beside the admission's own.

    The admission already asserts its admitted views. The call's negative views
    (a reject's views, or a confirm's ``negative_views``) take those views from
    it, and every other admitted view still speaks for the proposed identity. A
    confirm that would leave none is a reject in all but name and is refused; an
    ``also_positive`` view may not be one that still speaks for the proposed one.
    """
    taken = {tuple(view) for view in negative}
    remaining = {tuple(view) for view in candidate["admitted_views"]} - taken
    if record["call"] == "confirm" and not remaining:
        raise _fail("admission_confirm_leaves_no_admitted_view")
    for item in record.get("also_positive", ()):
        if remaining & {tuple(view) for view in item["views"]}:
            raise _fail("call_views_overlap")


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

    An admission review (ADMISSION_REVIEW_SCHEMA) is read the same way, with a
    view drawn when its squint tile window was drawn on a read native slice, and
    every call keeps its seed meaning: ``negative_views`` and ``also_positive``
    included. The admission itself already asserts its admitted views, so a view
    still carries one claim (``_check_admission_claims``). A reject that has no
    drawn view to name is refused rather than left to change nothing.
    """
    if not _is_sha(review_sha256):
        raise _fail("review_sha256_invalid")
    candidates, admissions = _candidates_of(review)
    drawn_key = "window_state" if admissions else "support_state"
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
                _check_facets(candidate, record["views"], drawn_key)
        if "negative_views" in record:
            if call != "confirm":
                raise _fail("negative_views_require_confirm")
            if not _facets_valid(record["negative_views"]):
                raise _fail("call_negative_views_invalid")
            _check_facets(candidate, record["negative_views"], drawn_key)
        if "also_positive" in record:
            if not _alternatives_shape_valid(record["also_positive"]):
                raise _fail("call_also_positive_invalid")
            _check_alternatives(
                candidate, record["also_positive"], known_subjects, drawn_key
            )
        _check_one_identity_per_view(candidate, record)
        if candidate_id in seen:
            raise _fail("duplicate_call")
        seen.add(candidate_id)
        records.append(copy.deepcopy(record))
        if call == "reject":
            views, reason = _rejected_views(candidate, record, drawn_key)
            if views is None and admissions:
                raise _fail("admission_reject_has_no_drawn_view")
            if views is None:
                not_written[candidate_id] = str(reason)
            else:
                negative_views[candidate_id] = views
        elif call == "confirm" and "negative_views" in record:
            negative_views[candidate_id] = copy.deepcopy(record["negative_views"])
        if admissions:
            _check_admission_claims(
                candidate, record, negative_views.get(candidate_id, [])
            )
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


def _snapshot_memory(snapshot: object) -> dict[str, Any]:
    """The validated memory of a loaded squint snapshot, or a named refusal."""
    if (
        not isinstance(snapshot, MemorySnapshot)
        or snapshot.status != "squint"
        or not isinstance(snapshot.memory, dict)
        or not _is_sha(snapshot.sha256)
        or not isinstance(snapshot.path, Path)
    ):
        raise _fail("invalid_snapshot_state")
    return _clean_memory(snapshot.memory)


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
    memory = _snapshot_memory(source_snapshot)
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


def _verify_admissions(
    memory: Mapping[str, Any],
    candidates: Mapping[str, Mapping[str, Any]],
    rows_by_id: Mapping[str, list[Mapping[str, Any]]],
    confirmed: Collection[str],
) -> dict[str, Mapping[str, Any]]:
    """Each reviewed admission still stands exactly as pinned; returns its confirm row."""
    by_id = {case["case_id"]: case for case in memory["cases"]}
    rows: dict[str, Mapping[str, Any]] = {}
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
        row, reason = _standing_admission(case, rows_by_id, confirmed)
        if row is None:
            raise _fail(str(reason))
        if _json_sha256(case) != entry["case_sha256"]:
            raise _fail("admission_case_digest_mismatch")
        if _json_sha256(row) != entry["admission_call_sha256"]:
            raise _fail("admission_call_digest_mismatch")
        if _json_sha256(case["profile"]) != entry["profile_sha256"]:
            raise _fail("profile_digest_mismatch")
        if _profile_views(case) != entry["profile_views"]:
            raise _fail("profile_views_mismatch")
        if row["views"] != entry["admitted_views"]:
            raise _fail("admission_views_mismatch")
        rows[entry["case_id"]] = row
    return rows


def _admission_effects(
    candidates: Mapping[str, Mapping[str, Any]], validated: Mapping[str, Any]
) -> dict[str, dict[str, Any]]:
    """What each call changes on its admission, in review order.

    A call's negative views (a reject's views, or a confirm's ``negative_views``)
    take those views from the admission, and its ``also_positive`` entries give
    their views to another identity; every other admitted view keeps speaking.
    When no admitted view remains the whole case moves (``whole_case``),
    otherwise only the named facets change (``facets``). A call naming neither
    (a plain confirm or unsure) changes nothing and has no entry.
    """
    calls = {record["candidate_id"]: record for record in validated["calls"]}
    alternatives: dict[str, list[dict[str, Any]]] = {}
    for entry in validated["alternative_positives"]:
        alternatives.setdefault(entry["case_id"], []).append(entry)
    effects: dict[str, dict[str, Any]] = {}
    for case_id, candidate in candidates.items():
        call = calls.get(case_id)
        negative = validated["negative_views"].get(case_id, [])
        others = alternatives.get(case_id, [])
        if call is None or (not negative and not others):
            continue
        remaining = [
            view for view in candidate["admitted_views"] if view not in negative
        ]
        effects[case_id] = {
            "effect": "facets" if remaining else "whole_case",
            "call": copy.deepcopy(call),
            "reader": call.get("reader", validated["reader"]),
            "positive_views": copy.deepcopy(remaining),
            "negative_views": copy.deepcopy(negative),
            "alternatives": copy.deepcopy(others),
        }
    return effects


def _corrected_row(
    admission_row: Mapping[str, Any], effect: Mapping[str, Any]
) -> dict[str, Any]:
    """The case's one call row after its correction, in a form the seed path writes.

    A whole-case correction is the reviewer's reject row, which names that reader:
    the teaching's own reader is the seed's reviewer. A facet correction is the
    round's own confirm row, its recognition-derived reader and lineage mark kept,
    with ``views`` the admitted views that still speak, ``negative_views`` the
    views taken from it and ``also_positive`` the views given to another identity,
    exactly as a seed confirm row carries them.
    """
    if effect["effect"] == "whole_case":
        return {**copy.deepcopy(effect["call"]), "reader": effect["reader"]}
    row = copy.deepcopy(dict(admission_row))
    row["views"] = copy.deepcopy(effect["positive_views"])
    if effect["negative_views"]:
        row["negative_views"] = copy.deepcopy(effect["negative_views"])
    if effect["alternatives"]:
        row["also_positive"] = copy.deepcopy(effect["call"]["also_positive"])
    return row


def _corrected_record(
    case: Mapping[str, Any],
    admission_row: Mapping[str, Any],
    effect: Mapping[str, Any],
    provenance: Mapping[str, Any],
) -> dict[str, Any]:
    """The identity record a correction adds: the case, and who called which facet.

    The record is the case exactly as its round admitted it. Its top-level
    ``reader`` and ``review_sha256`` are the record's provenance, which the
    identity reader gives to the negative and alternative entries it builds from
    the record, so those facets name the reviewer; ``identity_correction`` keeps
    the call, the facets it moved and the superseded confirm row verbatim.
    """
    record = copy.deepcopy(dict(case))
    record["reader"] = effect["reader"]
    record["review_sha256"] = provenance["review_sha256"]
    record["identity_correction"] = {
        "schema": CORRECTION_SCHEMA,
        "kind": CORRECTION_KIND,
        "corrected_by": effect["reader"],
        **copy.deepcopy(dict(provenance)),
        "effect": effect["effect"],
        "call": copy.deepcopy(effect["call"]),
        "positive_views_after": copy.deepcopy(effect["positive_views"]),
        "negative_views": copy.deepcopy(effect["negative_views"]),
        "alternative_positives": copy.deepcopy(effect["alternatives"]),
        "superseded_call": copy.deepcopy(dict(admission_row)),
    }
    return record


def _corrected_teaching(
    memory: Mapping[str, Any],
    effects: Mapping[str, Mapping[str, Any]],
    rows: Mapping[str, dict[str, Any]],
    review_record: dict[str, Any],
) -> dict[str, Any]:
    """The reviewed memory's teaching with its corrections applied, a fresh copy."""
    teaching = copy.deepcopy(dict(memory["object_identity_teaching"]))
    for key, kind in (
        ("negative_case_ids", list),
        ("negative_views", Mapping),
        ("alternative_positives", list),
        ("admission_reviews", list),
    ):
        if key in teaching and not isinstance(teaching[key], kind):
            raise _fail("identity_teaching_invalid")
    moved = {cid for cid, effect in effects.items() if effect["effect"] == "whole_case"}
    teaching["confirmed_case_ids"] = [
        case_id for case_id in teaching["confirmed_case_ids"] if case_id not in moved
    ]
    # Each corrected admission had exactly one row, its round's confirm.
    teaching["calls"] = [
        rows.get(row["candidate_id"], row)
        if isinstance(row.get("candidate_id"), str)
        else row
        for row in teaching["calls"]
    ]
    negatives = [cid for cid, effect in effects.items() if effect["negative_views"]]
    if negatives:
        teaching["negative_case_ids"] = [
            *teaching.get("negative_case_ids", []),
            *negatives,
        ]
        teaching["negative_views"] = {
            **teaching.get("negative_views", {}),
            **{
                case_id: copy.deepcopy(effects[case_id]["negative_views"])
                for case_id in negatives
            },
        }
    alternatives = [
        copy.deepcopy(entry)
        for effect in effects.values()
        for entry in effect["alternatives"]
    ]
    if alternatives:
        teaching["alternative_positives"] = [
            *teaching.get("alternative_positives", []),
            *alternatives,
        ]
    teaching["admission_reviews"] = [
        *teaching.get("admission_reviews", []),
        review_record,
    ]
    return teaching


def _corrections_summary(
    effects: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Per corrected admission: what moved, on which views, and who called it."""
    return {
        case_id: {
            "effect": effect["effect"],
            "reader": effect["reader"],
            "positive_views_after": copy.deepcopy(effect["positive_views"]),
            "negative_views": copy.deepcopy(effect["negative_views"]),
            "alternative_positive_ids": [
                entry["entry_id"] for entry in effect["alternatives"]
            ],
        }
        for case_id, effect in effects.items()
    }


def _corrected_child(
    memory: Mapping[str, Any],
    provenance: Mapping[str, Any],
    calls: Mapping[str, Any],
    validated: Mapping[str, Any],
    effects: Mapping[str, Mapping[str, Any]],
    admission_rows: Mapping[str, Mapping[str, Any]],
    reviewed_ids: Sequence[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """The child memory and the identity records it adds; the reviewed memory is not mutated.

    A whole-case correction moves the case out of ``cases``; a facet correction
    leaves it there, confirmed, and rewrites only its call row. Either adds the
    case's identity record, which the identity reader needs to build the
    negative and alternative entries of the corrected facets.
    """
    from knee.diagnosis.squint_identity_growth import _RUNTIME_KEYS

    table = memory.get("object_identity_cases")
    if table is None:
        table = {"schema": IDENTITY_CASES_SCHEMA, "cases": []}
    if (
        not isinstance(table, Mapping)
        or table.get("schema") != IDENTITY_CASES_SCHEMA
        or not isinstance(table.get("cases"), list)
    ):
        raise _fail("identity_cases_table_invalid")
    held = {row.get("case_id") for row in table["cases"] if isinstance(row, Mapping)}
    by_id = {case["case_id"]: case for case in memory["cases"]}
    rows: dict[str, dict[str, Any]] = {}
    records: list[dict[str, Any]] = []
    for case_id, effect in effects.items():
        if case_id in held:
            raise _fail("corrected_case_id_already_held")
        rows[case_id] = _corrected_row(admission_rows[case_id], effect)
        records.append(
            _corrected_record(
                by_id[case_id], admission_rows[case_id], effect, provenance
            )
        )
    review_record = {
        "schema": ADMISSION_RECORD_SCHEMA,
        "reader": validated["reader"],
        **copy.deepcopy(dict(provenance)),
        "reviewed_candidate_ids": list(reviewed_ids),
        "calls": copy.deepcopy(validated["calls"]),
        "confirmed_admission_ids": list(validated["confirmed_case_ids"]),
        "unsure_case_ids": [
            record["candidate_id"]
            for record in validated["calls"]
            if record["call"] == "unsure"
        ],
        "corrected_case_ids": list(effects),
        "corrections": _corrections_summary(effects),
        "superseded_calls": [
            copy.deepcopy(dict(admission_rows[case_id])) for case_id in effects
        ],
        "confirm_effect": "recorded_only_recognition_derived_lineage_kept",
    }
    moved = {cid for cid, effect in effects.items() if effect["effect"] == "whole_case"}
    child = {key: value for key, value in memory.items() if key not in _RUNTIME_KEYS}
    child["cases"] = [case for case in memory["cases"] if case["case_id"] not in moved]
    child["object_identity_teaching"] = _corrected_teaching(
        memory, effects, rows, review_record
    )
    if records:
        child["object_identity_cases"] = {**table, "cases": [*table["cases"], *records]}
    digest = _json_sha256(
        [
            provenance["reviewed_manifest_sha256"],
            provenance["review_sha256"],
            calls,
            ADMISSION_RECORD_SCHEMA,
        ]
    )
    child["revision"] = f"{memory['revision']}+admission-review-{digest[:16]}"
    return child, records


def _refresh_corrected_configurations(
    child: dict[str, Any],
    memory: Mapping[str, Any],
    effects: Mapping[str, Mapping[str, Any]],
    provenance: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Rebuild the whole-condition cases of every study a correction touched.

    A correction changes the views where an admitted object's identity holds, or
    takes the object out of ``cases``; a configuration built with that object as
    a role would otherwise keep speaking for it. The studies are rebuilt from the
    corrected child with the public pair
    (``squint_configurations.rebuild_study_configurations`` /
    ``apply_rebuilt_configurations``): every role on the views where its identity
    now holds, a whole-case correction no longer a role, the official label at
    study scope from the child's ledger row, and each replaced version kept whole
    as a record. A study without configurations or a ledger row is left as it is.
    The rebuild is recorded on the review record it follows from.
    """
    from knee.diagnosis.squint_configurations import (
        SUPERSEDED_CONFIGURATIONS_KEY,
        SUPERSEDED_CONFIGURATIONS_SCHEMA,
        ConfigurationProfileError,
        apply_rebuilt_configurations,
        rebuild_study_configurations,
    )

    by_id = {case["case_id"]: case for case in memory["cases"]}
    studies = sorted({by_id[case_id]["study_uid"] for case_id in effects})
    if not studies:
        return child, None
    built_by = {
        "kind": "admission_correction",
        "review_sha256": provenance["review_sha256"],
        "reviewed_manifest_sha256": provenance["reviewed_manifest_sha256"],
    }
    # A study left with no object case has no warranted role for any configuration:
    # its configurations are retired whole, as records, rather than rebuilt.
    with_objects = {
        case["study_uid"] for case in child["cases"] if not _is_configuration(case)
    }
    emptied = [study for study in studies if study not in with_objects]
    retired = [
        case
        for case in child["cases"]
        if _is_configuration(case) and case["study_uid"] in emptied
    ]
    if retired:
        table = child.get(SUPERSEDED_CONFIGURATIONS_KEY) or {
            "schema": SUPERSEDED_CONFIGURATIONS_SCHEMA,
            "cases": [],
        }
        child = {
            **child,
            "cases": [case for case in child["cases"] if case not in retired],
            SUPERSEDED_CONFIGURATIONS_KEY: {
                **table,
                "cases": [
                    *table["cases"],
                    *(
                        {
                            "case_sha256": _json_sha256(case),
                            "superseded_by": dict(built_by),
                            "retired": "no_object_case_remains_in_the_study",
                            "case": case,
                        }
                        for case in retired
                    ),
                ],
            },
        }
    try:
        rebuilt = rebuild_study_configurations(
            child,
            [study for study in studies if study in with_objects],
            built_by=built_by,
        )
        refreshed = apply_rebuilt_configurations(child, rebuilt)
    except ConfigurationProfileError as error:
        raise _fail(f"configuration_rebuild_refused:{error.code}") from error
    summary = {
        "built_by": built_by,
        "study_uids": list(rebuilt["study_uids"]),
        "rebuilt_case_ids": [case["case_id"] for case in rebuilt["cases"]],
        "new_case_ids": [case["case_id"] for case in rebuilt["new"]],
        "superseded_sha256": dict(rebuilt["superseded"]),
        "retired_case_ids": [case["case_id"] for case in retired],
    }
    refreshed["object_identity_teaching"]["admission_reviews"][-1][
        "configuration_rebuild"
    ] = summary
    return refreshed, summary


def _facet(
    banks: Mapping[str, tuple[int, ...]], identity: str, views: Sequence[Sequence[str]]
) -> tuple[str, frozenset]:
    """One identity-recall entry as the reader builds it: its identity and banks."""
    from knee.diagnosis.squint_identity import _signal_banks

    selected = {tuple(view) for view in views}
    return identity, frozenset(_signal_banks(banks, selected).items())


def _identity_facets(prepared: Any) -> dict[tuple[str, str], tuple[str, frozenset]]:
    """Every entry the identity reader prepared, by sign and id: identity and banks.

    Seeds, alternative-identity seeds among them, are ``+``; negative identity
    cases are ``-``. Nothing else speaks in identity recall.
    """
    facets: dict[tuple[str, str], tuple[str, frozenset]] = {}
    for sign, entries in (("+", prepared._seeds), ("-", prepared._negatives)):
        for entry in entries:
            facets[(sign, entry["case_id"])] = (
                entry["subject"],
                frozenset(dict(entry["banks"]).items()),
            )
    return facets


def _expected_facets(
    before: Mapping[tuple[str, str], tuple[str, frozenset]],
    effects: Mapping[str, Mapping[str, Any]],
    by_id: Mapping[str, Mapping[str, Any]],
) -> dict[tuple[str, str], tuple[str, frozenset]]:
    """The reviewed memory's entries with exactly the corrected facets moved."""
    from knee.diagnosis.squint_locator import _banks

    expected = dict(before)
    for case_id, effect in effects.items():
        case = by_id[case_id]
        banks = _banks(case["profile"]) or {}
        if effect["effect"] == "whole_case":
            expected.pop(("+", case_id), None)
        else:
            expected[("+", case_id)] = _facet(
                banks, case["subject"], effect["positive_views"]
            )
        if effect["negative_views"]:
            expected[("-", case_id)] = _facet(
                banks, case["subject"], effect["negative_views"]
            )
        for entry in effect["alternatives"]:
            expected[("+", entry["entry_id"])] = _facet(
                banks, entry["identity"], entry["views"]
            )
    return expected


def _expected_condition_views(
    before: Mapping[str, Any], effects: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    """Where each case's condition evidence speaks once the corrections apply."""
    expected = dict(before)
    for case_id, effect in effects.items():
        if effect["effect"] == "whole_case":
            expected.pop(case_id, None)
        else:
            expected[case_id] = frozenset(
                tuple(view) for view in effect["positive_views"]
            )
    return expected


def publish_admission_corrections(
    source_snapshot: MemorySnapshot,
    review: Any,
    calls: Any,
    review_sha256: str,
    output: Path,
) -> dict[str, Any]:
    """Publish a child of a reviewed growth child holding the reviewer's calls.

    ``source_snapshot`` is the memory the admission review was exported from.
    Each call applies only where it asserts (``_admission_effects``). A call's
    negative views become an ordinary negative identity case of the proposed
    identity on exactly those views, and its ``also_positive`` views a positive of
    the named identity on exactly theirs, read from the case's identity record,
    which names the reviewer. Every admitted view not taken keeps speaking for the
    proposed identity, with its recognition-derived lineage and its condition
    evidence: the case stays in ``cases``, confirmed, and its round's confirm row
    narrows its ``views`` and gains ``negative_views`` or ``also_positive`` as a
    seed confirm row carries them. Only when every admitted view is taken does the
    whole case move to ``object_identity_cases``, its row then the reviewer's
    reject row. Each superseded row is kept verbatim. A plain confirm or unsure
    changes no case and no row; the review record in
    ``object_identity_teaching["admission_reviews"]`` keeps every call, the reader
    and the confirmed admissions. The whole-condition configurations of every
    study a correction touched are rebuilt from the corrected child
    (``_refresh_corrected_configurations``), their replaced versions kept as
    records and the rebuild noted on the review record. Every other record (cases,
    the other studies' configurations, identity records, calls, full tables,
    source identities and growth rounds) is the reviewed memory's own. A call file
    applying nothing is refused. The child
    must prepare with exactly the corrected facets moved, in identity recall and in
    where condition evidence speaks, and nothing else changed.
    """
    memory = _snapshot_memory(source_snapshot)
    if not isinstance(review, dict) or review.get("schema") != ADMISSION_REVIEW_SCHEMA:
        raise _fail("review_malformed")
    candidates = _admission_review_candidates(review)
    if review["source_manifest_sha256"] != source_snapshot.sha256:
        raise _fail("stale_source_pin")
    known_subjects = {
        case["subject"] for case in memory["cases"] if not _is_configuration(case)
    }
    validated = validate_calls(
        review, calls, review_sha256, known_subjects=known_subjects
    )
    effects = _admission_effects(candidates, validated)
    if not validated["confirmed_case_ids"] and not effects:
        raise _fail("no_admission_calls_applied")
    rows_by_id, confirmed = _teaching_rows(memory)
    admission_rows = _verify_admissions(memory, candidates, rows_by_id, confirmed)
    destination = _check_output(output, source_snapshot)
    from knee.diagnosis.squint_identity import (
        identity_condition_views,
        prepare_identity,
    )

    before = prepare_identity(memory)
    before_scope = identity_condition_views(memory)
    if before.get("outcome") != "prepared" or before_scope.get("outcome") != "scoped":
        raise _fail("parent_identity_teaching_invalid")
    provenance = {
        "review_sha256": review_sha256,
        "reviewed_manifest_sha256": source_snapshot.sha256,
        "reviewed_revision": memory["revision"],
    }
    child, records = _corrected_child(
        memory,
        provenance,
        calls,
        validated,
        effects,
        admission_rows,
        list(candidates),
    )
    child, configuration_rebuild = _refresh_corrected_configurations(
        child, memory, effects, provenance
    )
    try:
        _validate_memory(child)
        for record in records:
            reference = record.get("full_profile")
            if (
                isinstance(reference, dict)
                and reference.get("availability") == "retained_sparse_counts"
            ):
                _full_profile_from_validated_case(
                    child, record, reference, record["subject"]
                )
    except SquintMemoryError as error:
        raise _fail("child_memory_invalid") from error
    prepared = prepare_identity(child)
    scope = identity_condition_views(child)
    if prepared.get("outcome") != "prepared" or scope.get("outcome") != "scoped":
        raise _fail("child_identity_teaching_invalid")
    # Exactly the corrected facets moved, in identity recall and in where condition
    # evidence speaks, and nothing else changed: a row the reader would skip, or a
    # positive facet a correction erased, shows up here, not as a silent change.
    by_id = {case["case_id"]: case for case in memory["cases"]}
    expected = _expected_facets(_identity_facets(before), effects, by_id)
    if _identity_facets(prepared) != expected or scope["views"] != (
        _expected_condition_views(before_scope["views"], effects)
    ):
        raise _fail("corrected_facets_not_prepared")
    receipt = save_memory(child, destination)
    readback = prepare_identity(load_memory(destination))
    if readback.get("outcome") != "prepared" or dict(readback) != dict(prepared):
        raise _fail("child_readback_invalid")
    return {
        "outcome": "published",
        "manifest": receipt["manifest"],
        "sha256": receipt["sha256"],
        "case_count": receipt["case_count"],
        "revision": child["revision"],
        "confirmed_admission_ids": list(validated["confirmed_case_ids"]),
        "corrected_case_ids": list(effects),
        "whole_case_ids": [
            case_id
            for case_id, effect in effects.items()
            if effect["effect"] == "whole_case"
        ],
        "corrections": _corrections_summary(effects),
        "negative_views": copy.deepcopy(validated["negative_views"]),
        "unsure_case_ids": [
            record["candidate_id"]
            for record in validated["calls"]
            if record["call"] == "unsure"
        ],
        "configuration_rebuild": configuration_rebuild,
        "identity_preparation": dict(readback),
    }
