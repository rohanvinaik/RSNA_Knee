"""Procedure-experience rows: what a bounded observation did in a real run, and what checks it.

Lane C of docs/SOCIETY_OF_MIND_TRAINING.md (section 5, row C), retention only. These are pure
functions over the retained ``knee.squint-study/v1`` inference records (and the independent
evidence beside them). Nothing here scores, thresholds, learns or proposes a request, and
nothing writes a "success", "failure", "settled" or "useful" field: a row keeps the request, the
context, whether and how it ran, the question's state before and after as far as the record keeps
it, and the independent call that bears on the question (or ``unchecked``).

What the record does and does not keep (read from ``knee.diagnosis.squint_pipeline.infer_study``,
source sha256 4f08b234...; the batch-r2 run's frozen source snapshot has the identical file):

* Identity looks are written by ``_resolve_identity_contests`` (line 1543) with
  ``requested_by: identity_question``, before any condition question is asked. The question is
  recorded (it is the identity question); the request's reason is the constant the coordinator
  passes (``contested_at_squint_scale``) and is derived here from the contest list.
* Condition-question requests are routed in the condition loop (lines 1763-1792) in QUESTIONS
  order, each question only while its finding is ``open`` (lines 1768-1772). The observation row
  that comes back from ``_bounded_observation`` carries the subject and the code and nothing
  else: no question, no reason, no request id. So the question of a routed row is RECONSTRUCTED
  here, never read.
* ``unresolved_observation_requests`` (lines 1884-1888) is the list of requests still asked by the
  final findings, after the looks and the identity refresh. They are second-pass requests: they
  did not run as listed. They are matched to the routed rows by subject, in order.

Every reconstruction is marked as such on the row. Where more than one answer fits, the row says
``ambiguous`` and lists the candidates; it never picks one.

Provenance codes used on rows (the legend is repeated in summary.md):

* ``recorded`` the record states it; ``recorded_after_the_look`` the final finding states it;
* ``reconstructed_by_order_and_subject`` / ``reconstructed_by_position_and_contract`` see above;
* ``derived_from_code_path`` follows from which function writes the row;
* ``not_recorded`` the record does not keep it.
"""

from __future__ import annotations

import csv
import io
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

__all__ = [
    "SCHEMA",
    "alignments",
    "attribute_routed",
    "build_call_index",
    "condition_outcome",
    "contract_subjects",
    "execution_status",
    "experience_rows",
    "identity_outcome",
    "parse_candidate_id",
    "read_label_table",
    "split_observations",
    "tally",
]

SCHEMA = "knee.procedure-experience/v1"
IDENTITY_QUESTION = "identity"
IDENTITY_REQUESTER = "identity_question"
CONTEST_REASON = "contested_at_squint_scale"
ZOOM_KIND = "bounded_zoom"
PAIRED_PROCEDURE = "paired_finer_reading"
BONES = ("femur", "tibia", "patella", "fibula")
CONDITION_BEFORE = "open"

MEASURED = "measured"
RAN_NEW = "ran_new_reading"
READING_AVAILABLE = "reading_already_available"
NOT_RUN = "not_run"
#: Codes that mean a reading of the subject exists and the request consumed it without making it.
_AVAILABLE_CODES = frozenset(
    {"shared_observation_already_available", "already_measured", "reading_unchanged"}
)
#: Codes that mean this observation made a new reading.
_NEW_CODES = frozenset({MEASURED, "profiled", "located"})

#: The pins every row must carry (a pinless row is refused, never written).
REQUIRED_PINS = (
    "run",
    "record_file",
    "record_sha256",
    "memory_sha256",
    "memory_revision",
)

#: Where each reconstruction rests, for the row's own attribution block.
ROUTING_BASIS = (
    "squint_pipeline.py sha256 4f08b234: L1543 identity looks; L1763-1792 condition requests "
    "routed per open question in QUESTIONS order; L1884-1888 final requests"
)

_ATTRIBUTION_STATUS = {
    "aligned": "reconstructed_unique",
    "dropped": "reconstructed_unique",
    "dropped_ambiguous": "ambiguous",
    "dropped_no_question_fits": "not_reconstructed",
    "ambiguous": "ambiguous",
    "unaligned": "not_reconstructed",
}


# --------------------------------------------------------------------------- small helpers


def _get(value: object, *path: str, default: Any = None) -> Any:
    for key in path:
        if isinstance(value, Mapping) and key in value:
            value = value[key]
        else:
            return default
    return value


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def execution_status(code: object) -> str:
    """``ran_new_reading``, ``reading_already_available`` or ``not_run``, from the row's code.

    A code that is neither a known new-reading code nor a known "already there" code is
    ``not_run``: nothing is credited to a request whose code does not say a reading exists.
    """
    if code in _NEW_CODES:
        return RAN_NEW
    if code in _AVAILABLE_CODES:
        return READING_AVAILABLE
    return NOT_RUN


def _view_triple(view: object) -> list[str] | None:
    if isinstance(view, Mapping):
        parts = [
            view.get("orientation"),
            view.get("fluid_sensitive"),
            view.get("fat_suppression"),
        ]
        if all(isinstance(part, str) for part in parts):
            return [str(part) for part in parts]
    if (
        isinstance(view, Sequence)
        and not isinstance(view, (str, bytes))
        and len(view) == 3
        and all(isinstance(part, str) for part in view)
    ):
        return [str(part) for part in view]
    return None


# --------------------------------------------------------------------------- observations


Observation = tuple[int, Mapping[str, Any]]


def split_observations(
    observations: object,
) -> tuple[list[Observation], list[Observation], list[Observation]]:
    """Identity-question looks, routed condition-question rows, and rows of any other requester.

    Each entry keeps the row's index in the record's ``observations`` list.
    """
    identity: list[Observation] = []
    routed: list[Observation] = []
    other: list[Observation] = []
    for index, row in enumerate(_sequence(observations)):
        if not isinstance(row, Mapping):
            continue
        requester = row.get("requested_by")
        if requester is None:
            routed.append((index, row))
        elif requester == IDENTITY_REQUESTER:
            identity.append((index, row))
        else:
            other.append((index, row))
    return identity, routed, other


def _supplier(
    observations: Sequence[Any], index: int, subject: object
) -> dict[str, Any] | None:
    """The earliest observation of ``subject`` that made a new reading, at or before ``index``."""
    for position, row in enumerate(observations):
        if position > index:
            break
        if (
            isinstance(row, Mapping)
            and row.get("subject") == subject
            and execution_status(row.get("code")) == RAN_NEW
        ):
            return {
                "observation_index": position,
                "code": row.get("code"),
                "requested_by": row.get("requested_by") or "condition_request",
            }
    return None


def _regions(rows: object) -> list[dict[str, Any]]:
    found = []
    for item in _sequence(rows):
        if isinstance(item, Mapping):
            found.append(
                {
                    key: item[key]
                    for key in ("series_uid", "window", "reason")
                    if key in item
                }
            )
    return found


def _execution(
    observations: Sequence[Any], index: int, row: Mapping[str, Any]
) -> dict[str, Any]:
    code = row.get("code")
    status = execution_status(code)
    execution: dict[str, Any] = {
        "observation_index": index,
        "status": status,
        "reading_available": status != NOT_RUN,
        "new_reading": status == RAN_NEW,
        "code": code,
        "reason": row.get("reason"),
        "lens": row.get("lens"),
        "tile_mm": row.get("tile_mm"),
        "writer_procedure": row.get("procedure"),
        "regions_read": _regions(row.get("regions")),
        "held_regions": _regions(row.get("held_regions")),
        "unavailable_regions": _regions(row.get("unavailable_regions")),
    }
    if status == RAN_NEW:
        execution["reading_supplied_by"] = {
            "observation_index": index,
            "code": code,
            "requested_by": row.get("requested_by") or "condition_request",
        }
    elif status == READING_AVAILABLE:
        execution["reading_supplied_by"] = _supplier(
            observations, index, row.get("subject")
        )
    else:
        execution["reading_supplied_by"] = None
    return execution


# --------------------------------------------------------------------------- alignment


def alignments(
    routed_subjects: Sequence[str],
    unresolved_subjects: Sequence[str],
    *,
    cap: int = 1000,
) -> list[tuple[int, ...]] | None:
    """Every order-preserving way to match each unresolved request to a distinct routed row.

    Each way is the tuple of routed indices, one per unresolved request, with equal subjects.
    ``[]`` means the unresolved list is not a subsequence of the routed rows; ``None`` means
    more than ``cap`` ways exist (too ambiguous to enumerate).
    """
    n, m = len(routed_subjects), len(unresolved_subjects)
    ways = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        ways[i][m] = 1
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            ways[i][j] = ways[i + 1][j]
            if routed_subjects[i] == unresolved_subjects[j]:
                ways[i][j] += ways[i + 1][j + 1]
    if ways[0][0] > cap:
        return None
    found: list[tuple[int, ...]] = []
    chosen: list[int] = []

    def walk(start: int, j: int) -> None:
        if j == m:
            found.append(tuple(chosen))
            return
        for k in range(start, n):
            if routed_subjects[k] == unresolved_subjects[j] and ways[k + 1][j + 1]:
                chosen.append(k)
                walk(k + 1, j + 1)
                chosen.pop()

    if ways[0][0]:
        walk(0, 0)
    return found


def contract_subjects(record: Mapping[str, Any]) -> dict[str, set[str]]:
    """Each question's contract subjects, as the final finding's evidence names them."""
    found: dict[str, set[str]] = {}
    for question, body in _mapping(record.get("questions")).items():
        evidence = _mapping(_get(body, "finding", "evidence"))
        names: set[str] = set(_mapping(evidence.get("readings")))
        for key in ("necessary", "alternatives", "supporting"):
            names.update(s for s in _sequence(evidence.get(key)) if isinstance(s, str))
        found[question] = names
    return found


def _dropped_candidates(
    index: int,
    embedding: Sequence[int],
    unresolved: Sequence[Mapping[str, Any]],
    question_order: Sequence[str],
    contracts: Mapping[str, set[str]],
    subject: str,
) -> tuple[str, ...]:
    """The questions a routed row that matched no final request could have served.

    The rows of one question are contiguous and the questions run in QUESTIONS order, so a row
    belongs to a question between its neighbours' questions (inclusive; one question when both
    neighbours belong to the same) whose contract names the subject. A question whose contract
    is not known stays a candidate (it cannot be excluded).
    """
    before = [j for j, k in enumerate(embedding) if k < index]
    after = [j for j, k in enumerate(embedding) if k > index]
    previous = unresolved[before[-1]]["question"] if before else None
    following = unresolved[after[0]]["question"] if after else None
    low = question_order.index(previous) if previous in question_order else 0
    high = (
        question_order.index(following)
        if following in question_order
        else len(question_order) - 1
    )
    window = question_order[low : high + 1]
    return tuple(
        question
        for question in window
        if question not in contracts or subject in contracts[question]
    )


def _unattributed(kind: str, basis: str, count: int) -> list[dict[str, Any]]:
    return [
        {
            "kind": kind,
            "question": None,
            "unresolved_index": None,
            "candidates": None,
            "basis": basis,
        }
        for _ in range(count)
    ]


def _resolved_attribution(
    choices: set[tuple[Any, ...]],
    unresolved: Sequence[Mapping[str, Any]],
    question_order: Sequence[str],
) -> dict[str, Any]:
    if len(choices) == 1:
        tag, detail = next(iter(choices))
        if tag == "aligned":
            return {
                "kind": "aligned",
                "question": unresolved[detail]["question"],
                "unresolved_index": detail,
                "candidates": None,
                "basis": "single_order_preserving_alignment_by_subject",
            }
        kind, basis = {
            0: ("dropped_no_question_fits", "no_question_fits_position_and_contract"),
            1: ("dropped", "position_between_neighbours_and_contract_membership"),
        }.get(
            len(detail),
            ("dropped_ambiguous", "more_than_one_question_fits_position_and_contract"),
        )
        return {
            "kind": kind,
            "question": detail[0] if len(detail) == 1 else None,
            "unresolved_index": None,
            "candidates": list(detail),
            "basis": basis,
        }
    names: set[str] = set()
    for tag, detail in choices:
        if tag == "aligned":
            names.add(unresolved[detail]["question"])
        else:
            names.update(detail)
    ordered = [q for q in question_order if q in names] + sorted(
        names - set(question_order)
    )
    return {
        "kind": "ambiguous",
        "question": None,
        "unresolved_index": None,
        "candidates": ordered,
        "basis": "several_alignments_disagree_about_this_row",
    }


def attribute_routed(
    routed_subjects: Sequence[str],
    unresolved: Sequence[Mapping[str, Any]],
    question_order: Sequence[str],
    contracts: Mapping[str, set[str]],
    *,
    cap: int = 1000,
) -> tuple[list[dict[str, Any]], list[list[int]]]:
    """Which question each routed row served, by reconstruction, and each request's row(s).

    Returns one attribution per routed row and, per unresolved request, the routed indices it
    could match. An attribution is one of:

    * ``aligned``: the row is the first-pass row of a still-listed request (one alignment fits);
    * ``dropped``: the row matched no final request; its question is the single question that
      position and contract allow, or ``dropped_ambiguous`` with the candidates;
    * ``ambiguous``: several alignments fit and they disagree about this row;
    * ``unaligned``: the final requests are not a subsequence of the routed rows.
    """
    subjects = [str(u.get("subject")) for u in unresolved]
    found = alignments(routed_subjects, subjects, cap=cap)
    n = len(routed_subjects)
    empty: list[list[int]] = [[] for _ in unresolved]
    if found is None:
        return _unattributed("ambiguous", "more_alignments_than_the_cap", n), empty
    if not found:
        return (
            _unattributed("unaligned", "final_requests_not_a_subsequence_of_routed", n),
            empty,
        )
    options: list[set[tuple[Any, ...]]] = [set() for _ in range(n)]
    matches: list[set[int]] = [set() for _ in unresolved]
    for embedding in found:
        placed = {k: j for j, k in enumerate(embedding)}
        for j, k in enumerate(embedding):
            matches[j].add(k)
        for i in range(n):
            if i in placed:
                options[i].add(("aligned", placed[i]))
            else:
                options[i].add(
                    (
                        "dropped",
                        _dropped_candidates(
                            i,
                            embedding,
                            unresolved,
                            question_order,
                            contracts,
                            routed_subjects[i],
                        ),
                    )
                )
    attributions = [
        _resolved_attribution(choices, unresolved, question_order)
        for choices in options
    ]
    return attributions, [sorted(m) for m in matches]


# --------------------------------------------------------------------------- context


def _knee_side(record: Mapping[str, Any]) -> dict[str, Any]:
    seen: dict[tuple[str, str], int] = defaultdict(int)
    for obj in _mapping(record.get("objects")).values():
        for territory in _sequence(_mapping(obj).get("territories")):
            relation = _mapping(_mapping(territory).get("relation"))
            side = relation.get("knee_side")
            if isinstance(side, str):
                seen[(side, str(relation.get("knee_side_status")))] += 1
    if not seen:
        return {"value": None, "status": "not_recorded"}
    values = {side for side, _status in seen}
    if len(values) > 1:
        return {
            "value": None,
            "status": "conflicting",
            "seen": {f"{s}/{t}": n for (s, t), n in sorted(seen.items())},
        }
    return {
        "value": next(iter(values)),
        "status": "/".join(sorted({status for (_s, status) in seen})),
        "territories_naming_it": sum(seen.values()),
    }


def _planes(key_planes: object) -> dict[str, Any]:
    return {
        name: _get(plane, "outcome")
        for name, plane in _mapping(key_planes).items()
        if isinstance(plane, Mapping)
    }


def _anchor_summary(obj: Mapping[str, Any]) -> dict[str, Any]:
    evidence = _mapping(obj.get("evidence"))
    anchor = _mapping(evidence.get("anchor") or evidence.get("unanchored_bone"))
    return {
        "location_route": evidence.get("location_route"),
        "anchored": evidence.get("location_route") == "structural_anchor",
        "anchor_status": anchor.get("status"),
        "anchor_code": anchor.get("code"),
        "view_resolution": _get(anchor, "view_resolution", "code"),
        "key_planes": _planes(anchor.get("key_planes")),
    }


def _locator_views(record: Mapping[str, Any]) -> list[list[str]]:
    views: set[tuple[str, ...]] = set()
    for raw in _mapping(record.get("objects")).values():
        obj = _mapping(raw)
        costs = _mapping(_mapping(obj.get("evidence")).get("candidate_costs_by_view"))
        for key in costs:
            try:
                triple = _view_triple(json.loads(key))
            except (TypeError, ValueError):
                triple = None
            if triple:
                views.add(tuple(triple))
        for region in _sequence(obj.get("regions")):
            triple = _view_triple(_mapping(region).get("view"))
            if triple:
                views.add(tuple(triple))
    return [list(v) for v in sorted(views)]


def study_context(record: Mapping[str, Any]) -> dict[str, Any]:
    """Study-level context: knee side, the four bones' anchors and status, views the locator read."""
    objects = _mapping(record.get("objects"))
    return {
        "knee_side": _knee_side(record),
        "bone_anchors": {
            bone: _anchor_summary(_mapping(objects[bone]))
            for bone in BONES
            if bone in objects
        },
        "views_with_locator_candidates": _locator_views(record),
        "series_read": _get(record, "work", "series_read"),
        "leg_map_status": _get(record, "work", "leg_map_status"),
    }


def _placing_anchors(obj: Mapping[str, Any]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for territory in _sequence(obj.get("territories")):
        for anchor in _sequence(_mapping(territory).get("anchors")):
            fields = _mapping(anchor)
            item = {
                key: fields[key]
                for key in ("anchor", "kind", "anchor_observation_status", "prior_only")
                if key in fields
            }
            if item and item not in found:
                found.append(item)
    return found


def subject_context(record: Mapping[str, Any], subject: object) -> dict[str, Any]:
    """What placed the object, its structural anchors and the identity context it was heard in."""
    obj = _mapping(_mapping(record.get("objects")).get(subject))
    evidence = _mapping(obj.get("evidence"))
    consumption = _mapping(
        _mapping(_get(record, "identity_consumption", "objects")).get(subject)
    )
    context = _mapping(consumption.get("identity_context"))
    origins = {
        str(_mapping(t).get("origin"))
        for t in _sequence(obj.get("territories"))
        if _mapping(t).get("origin") is not None
    }
    return {
        "location_status": obj.get("status"),
        "location_route": evidence.get("location_route"),
        "location_source": evidence.get("source"),
        "placing_anchors": _placing_anchors(obj),
        "territory_origins": sorted(origins),
        "identity_basis": context.get("basis"),
        "identity_conditioning": context.get("conditioning"),
        "identity_support": context.get("support"),
        "open_alternatives": list(_sequence(context.get("open_alternatives"))),
        "removed_by_structure": list(_sequence(context.get("removed_by_structure"))),
        "contradictions": len(_sequence(context.get("contradictions"))),
        "sanity_status": _get(obj, "sanity", "status"),
    }


# --------------------------------------------------------------------------- states


def _recall_entry(entry: object) -> dict[str, Any] | None:
    if not isinstance(entry, Mapping):
        return None
    return {
        "scale": entry.get("scale"),
        "outcome": entry.get("outcome"),
        "identity_state": entry.get("identity_state"),
        "appearance": entry.get("appearance"),
        "reason": entry.get("reason"),
        "applicable_negative_cases": len(
            _sequence(entry.get("applicable_negative_case_ids"))
        ),
    }


def _open_question(question: object) -> dict[str, Any] | None:
    """What the identity consumer still names after the look: named, never issued by these runs."""
    fields = _mapping(question)
    if not fields:
        return None
    return {
        "status": fields.get("status"),
        "why": fields.get("why"),
        "named_next_observations": [
            {
                "procedure": _mapping(item).get("procedure"),
                "lens": _get(item, "request", "lens"),
            }
            for item in _sequence(fields.get("next_observations"))
        ],
        "run": fields.get("run"),
    }


def identity_state(record: Mapping[str, Any], subject: object) -> dict[str, Any]:
    """Identity at 10 mm, after the finer look, and as the condition consumer finally read it.

    ``before`` is ``identity_recall.objects`` (10 mm; the reading that opened the contest);
    ``after`` is ``identity_recall.resolved_scale.objects`` (the joint 10 mm + 2 mm recall);
    ``changed`` says only that the recall outcome category differs between the two.
    """
    recall = _mapping(record.get("identity_recall"))
    before = _recall_entry(_mapping(recall.get("objects")).get(subject))
    joint = _mapping(recall.get("resolved_scale"))
    after = _recall_entry(_mapping(joint.get("objects")).get(subject))
    consumption = _mapping(
        _mapping(_get(record, "identity_consumption", "objects")).get(subject)
    )
    contest = _mapping(consumption.get("squint_scale_contest"))
    return {
        "scope": "identity",
        "before": before,
        "after": after,
        "consumed": {
            "identity_effect": consumption.get("identity_effect"),
            "region_read_as_subject": consumption.get("region_read_as_subject"),
            "identity_state": consumption.get("identity_state"),
            "identity_scale": consumption.get("identity_scale"),
            "contest_status": contest.get("status"),
            "contest_finer_look": contest.get("finer_look"),
            "contest_finding": contest.get("finding"),
            "open_question_after": _open_question(
                consumption.get("identity_open_question")
            ),
        },
        "changed": None
        if before is None or after is None
        else before["outcome"] != after["outcome"],
    }


def _subject_reading(reading: object) -> dict[str, Any] | None:
    if not isinstance(reading, Mapping):
        return None
    return {
        "role": reading.get("role"),
        "state": reading.get("state"),
        "code": reading.get("code"),
        "recall_outcomes": list(_sequence(reading.get("recall_outcomes"))),
        "trust_checked": reading.get("trust_checked"),
        "speaking_cases": len(_sequence(reading.get("speaking_case_ids"))),
    }


_BEFORE_OPEN = {
    "outcome": CONDITION_BEFORE,
    "provenance": "derived_from_code_path",
    "reason": None,
    "reason_provenance": "not_recorded",
}


def condition_state(
    record: Mapping[str, Any], question: str | None, subject: object
) -> dict[str, Any]:
    """The condition finding as the record keeps it (after the look); before is open by code.

    A request is routed only while its question's finding is open (infer_study lines 1768-1772),
    so ``before.outcome`` is ``open`` by construction; why it was open is not recorded.
    ``after`` is the final finding, after the look and the identity refresh. ``changed`` says only
    that the final finding is no longer open; it is not credited to the look.
    """
    body = _mapping(_mapping(record.get("questions")).get(question))
    finding = _mapping(body.get("finding"))
    after = None
    if finding:
        after = {
            "outcome": finding.get("outcome"),
            "reason": finding.get("reason"),
            "value": _mapping(record.get("values")).get(question),
            "tier": _get(finding, "rank", "tier"),
            "subject_reading": _subject_reading(
                _mapping(_get(finding, "evidence", "readings")).get(subject)
            ),
            "requests_still_listed": [
                f"{r.get('subject')}:{r.get('reason')}"
                for r in _sequence(finding.get("observation_requests"))
                if isinstance(r, Mapping)
            ],
        }
    return {
        "scope": "condition",
        "before": dict(_BEFORE_OPEN),
        "after": after,
        "changed": None if after is None else after["outcome"] != CONDITION_BEFORE,
    }


def _identity_consumed_final(
    record: Mapping[str, Any], subject: object
) -> dict[str, Any]:
    """The subject's identity as the condition questions finally read it (context for a row).

    ``recall_outcome_10mm_as_recorded`` is the final recorded 10 mm entry: it was recomputed after
    a routed look for an object that was not contested, so it is not a pre-look value there.
    """
    consumption = _mapping(
        _mapping(_get(record, "identity_consumption", "objects")).get(subject)
    )
    recall = _mapping(_mapping(_get(record, "identity_recall", "objects")).get(subject))
    contested = _get(
        record, "identity_recall", "resolved_scale", "contested_at_squint_scale"
    )
    return {
        "identity_effect": consumption.get("identity_effect"),
        "region_read_as_subject": consumption.get("region_read_as_subject"),
        "identity_state": consumption.get("identity_state"),
        "recall_outcome_10mm_as_recorded": recall.get("outcome"),
        "was_contested_at_squint_scale": subject in _sequence(contested),
    }


# --------------------------------------------------------------------------- independent evidence


def read_label_table(text: str) -> dict[str, Any]:
    """Official labels from the competition table's text: ``1`` is +1, ``0`` is -1, blank is no call.

    Returns ``calls`` (study -> question -> +1/-1, only where a call exists) and ``table_uids``
    (every study the table lists, with or without a call). A blank cell is not a negative.
    """
    reader = csv.DictReader(io.StringIO(text))
    columns = [
        c for c in (reader.fieldnames or []) if c not in ("StudyInstanceUID", "Report")
    ]
    calls: dict[str, dict[str, int]] = {}
    uids: set[str] = set()
    for row in reader:
        uid = row.get("StudyInstanceUID") or ""
        if not uid:
            continue
        uids.add(uid)
        for column in columns:
            cell = (row.get(column) or "").strip()
            if cell == "1":
                calls.setdefault(uid, {})[column] = 1
            elif cell == "0":
                calls.setdefault(uid, {})[column] = -1
    return {"calls": calls, "table_uids": uids}


def _unchecked(reason: str, **extra: Any) -> dict[str, Any]:
    return {"status": "unchecked", "reason": reason, **extra}


def condition_outcome(
    labels: Mapping[str, Any],
    uid: str,
    question: str | None,
    status: str,
) -> dict[str, Any]:
    """The official label at study scope, only for a request that ran and a known question."""
    if status == NOT_RUN:
        return _unchecked("request_did_not_run")
    if question is None:
        return _unchecked("question_not_attributed")
    if uid not in labels.get("table_uids", ()):
        return _unchecked("study_not_in_the_label_table")
    call = _mapping(_mapping(labels.get("calls")).get(uid)).get(question)
    if call is None:
        return _unchecked("label_blank_no_call")
    return {
        "status": "checked",
        "source": "official_label",
        "call": call,
        "scope": "study_condition",
        "reader": "official label table",
        "label_source": labels.get("source"),
    }


def parse_candidate_id(candidate_id: object) -> tuple[str, str, str, str] | None:
    """``kind:study:subject[:tail]`` -> (kind, study, subject, tail), else None."""
    if not isinstance(candidate_id, str):
        return None
    parts = candidate_id.split(":", 3)
    if len(parts) < 3 or not all(parts[:3]):
        return None
    return parts[0], parts[1], parts[2], parts[3] if len(parts) > 3 else ""


def _call_item(
    call: Mapping[str, Any], kind: str, concerns: str, **extra: Any
) -> dict[str, Any]:
    return {
        "call": call.get("call"),
        "views": call.get("views"),
        "negative_views": call.get("negative_views"),
        "also_positive": call.get("also_positive"),
        "reader": call.get("reader"),
        "notes": call.get("notes"),
        "candidate_id": call.get("candidate_id"),
        "source_kind": kind,
        "concerns": concerns,
        **extra,
    }


_CONCERNS = {"squint-case": "catalogue_case", "direct-visual": "direct_visual_case"}


def build_call_index(memory: Mapping[str, Any]) -> dict[str, Any]:
    """The memory's visual calls, keyed by (study, subject), with their provenance.

    Reviewer calls only. A call that carries ``identity_growth`` is the recognition-derived
    admission itself ("not an independent visual or clinical call") and is listed apart, never
    as an outcome. A reviewer's confirm of a located admission is tied to the inference record it
    came from through the located case's ``identity_growth.source.record_sha256`` (file bytes).
    """
    teaching = _mapping(memory.get("object_identity_teaching"))
    located_cases = {
        c["case_id"]: c
        for c in _sequence(memory.get("cases"))
        if isinstance(c, Mapping)
        and isinstance(c.get("case_id"), str)
        and c["case_id"].startswith("located:")
    }
    reviewer: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    excluded: list[str] = []
    seen: set[tuple[Any, ...]] = set()

    def add(item: dict[str, Any]) -> None:
        parsed = parse_candidate_id(item["candidate_id"])
        key = (
            item["candidate_id"],
            item["call"],
            json.dumps(item["views"], default=str),
        )
        if parsed is None or key in seen:
            return
        seen.add(key)
        reviewer[(parsed[1], parsed[2])].append(item)

    for raw in _sequence(teaching.get("calls")):
        call = _mapping(raw)
        parsed = parse_candidate_id(call.get("candidate_id"))
        if parsed is None:
            continue
        if "identity_growth" in call:
            excluded.append(str(call.get("candidate_id")))
            continue
        concerns = _CONCERNS.get(parsed[0], "other_candidate")
        add(_call_item(call, "identity_teaching_calls", concerns))
    for review_raw in _sequence(teaching.get("admission_reviews")):
        review = _mapping(review_raw)
        for raw in _sequence(review.get("calls")):
            call = _mapping(raw)
            parsed = parse_candidate_id(call.get("candidate_id"))
            if parsed is None:
                continue
            case = _mapping(located_cases.get(call.get("candidate_id")))
            source = _mapping(_get(case, "identity_growth", "source"))
            add(
                _call_item(
                    call,
                    "admission_review",
                    "located_candidate",
                    record_sha256=source.get("record_sha256"),
                    candidate_revision=parsed[3],
                    review_sha256=review.get("review_sha256"),
                )
            )
    for batch in _sequence(memory.get("direct_visual_teaching")):
        for raw in _sequence(_mapping(batch).get("calls")):
            call = _mapping(raw)
            if parse_candidate_id(call.get("candidate_id")):
                add(_call_item(call, "direct_visual_teaching", "direct_visual_case"))
    return {
        "reviewer_calls": dict(reviewer),
        "recognition_derived_excluded": sorted(excluded),
    }


_CALL_FIELDS = ("call", "views", "negative_views", "reader", "notes", "candidate_id")


def identity_outcome(
    call_index: Mapping[str, Any],
    uid: str,
    subject: object,
    source: Mapping[str, Any],
    status: str,
) -> dict[str, Any]:
    """A reviewer's call on this run's own located candidate, else ``unchecked`` with the reason.

    A call counts only if it concerns the located candidate that THIS record produced (the
    located case's recorded record sha equals this record's file sha, and the candidate's
    revision is the run's). Calls on another candidate are listed as related, not joined.
    """
    if status == NOT_RUN:
        return _unchecked("request_did_not_run")
    calls = _mapping(call_index.get("reviewer_calls")).get((uid, subject), [])
    if not calls:
        return _unchecked("no_visual_review_call_for_this_study_and_object")
    matching = [
        c
        for c in calls
        if c["concerns"] == "located_candidate"
        and c.get("record_sha256") == source.get("record_sha256")
        and c.get("candidate_revision") == source.get("memory_revision")
    ]
    if not matching:
        return _unchecked(
            "visual_call_concerns_another_candidate",
            related_calls=[
                {
                    k: c.get(k)
                    for k in ("call", "views", "reader", "candidate_id", "concerns")
                }
                for c in calls
            ],
        )
    return {
        "status": "checked",
        "source": "visual_review_of_this_runs_located_candidate",
        "scope": "reviewed_views",
        "evidence": [
            {
                **{k: c.get(k) for k in _CALL_FIELDS},
                "review_sha256": c.get("review_sha256"),
            }
            for c in matching
        ],
    }


# --------------------------------------------------------------------------- rows


def _require_pins(source: Mapping[str, Any]) -> None:
    missing = [key for key in REQUIRED_PINS if not source.get(key)]
    if missing:
        raise ValueError("source pins missing: " + ", ".join(missing))


def _identity_request(
    record: Mapping[str, Any], row: Mapping[str, Any]
) -> dict[str, Any]:
    subject = row.get("subject")
    contested = _sequence(
        _get(record, "identity_recall", "resolved_scale", "contested_at_squint_scale")
    )
    return {
        "kind": ZOOM_KIND,
        "procedure": PAIRED_PROCEDURE,
        "subject": subject,
        "question": IDENTITY_QUESTION,
        "reason": CONTEST_REASON,
        "scope": "object_window",
        "bounded": True,
        "requested_by": row.get("requested_by"),
        "listed_after_the_look": None,
        "provenance": {
            "question": "recorded",
            "reason": "derived_from_code_path"
            if subject in contested
            else "derived_from_code_path_but_subject_not_in_the_contest_list",
            "kind": "derived_from_code_path",
            "scope": "derived_from_code_path",
        },
    }


def _attribution_block(attribution: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": _ATTRIBUTION_STATUS[attribution["kind"]],
        "kind": attribution["kind"],
        "basis": attribution["basis"],
        "candidates": attribution.get("candidates"),
        "rests_on": ROUTING_BASIS,
    }


def _condition_request(
    row: Mapping[str, Any],
    attribution: Mapping[str, Any],
    listed: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if listed is not None:
        return {
            "kind": listed.get("kind"),
            "procedure": PAIRED_PROCEDURE if listed.get("kind") == ZOOM_KIND else None,
            "subject": listed.get("subject"),
            "question": listed.get("question"),
            "reason": listed.get("reason"),
            "scope": listed.get("scope"),
            "bounded": listed.get("bounded"),
            "full_study": listed.get("full_study"),
            "discretionary": listed.get("discretionary"),
            "request_id": listed.get("request_id"),
            "requested_by": None,
            "listed_after_the_look": True,
            "provenance": {
                "question": "reconstructed_by_order_and_subject",
                "reason": "recorded_after_the_look",
                "kind": "recorded_after_the_look",
                "scope": "recorded_after_the_look",
                "first_pass_reason": "not_recorded",
            },
        }
    return {
        "kind": ZOOM_KIND,
        "procedure": PAIRED_PROCEDURE,
        "subject": row.get("subject"),
        "question": attribution.get("question"),
        "reason": None,
        "scope": None,
        "bounded": None,
        "requested_by": None,
        "listed_after_the_look": False,
        "provenance": {
            "question": "reconstructed_by_position_and_contract"
            if attribution.get("question")
            else "not_attributed",
            "reason": "not_recorded",
            "kind": "derived_from_code_path",
            "scope": "not_recorded",
        },
    }


def _row(
    source: Mapping[str, Any],
    uid: str,
    row_id: str,
    parts: Mapping[str, Any],
) -> dict[str, Any]:
    pins = {key: source[key] for key in REQUIRED_PINS}
    extras = {k: v for k, v in source.items() if k not in REQUIRED_PINS}
    return {
        "schema": SCHEMA,
        "row_id": row_id,
        "source": {**pins, "study_uid": uid, **extras},
        **parts,
    }


def _credited(state: dict[str, Any], execution: Mapping[str, Any]) -> dict[str, Any]:
    """A request that did not run is not an outcome: its row reports no state change."""
    if execution["status"] == NOT_RUN:
        return {**state, "changed": None}
    return state


def _identity_rows(
    record: Mapping[str, Any],
    source: Mapping[str, Any],
    uid: str,
    study: dict[str, Any],
    call_index: Mapping[str, Any],
) -> list[dict[str, Any]]:
    observations = _sequence(record.get("observations"))
    identity, _routed, other = split_observations(observations)
    rows = []
    for index, obs in identity:
        subject = obs.get("subject")
        execution = _execution(observations, index, obs)
        rows.append(
            _row(
                source,
                uid,
                f"{source['run']}|{uid}|{index:03d}",
                {
                    "context": {
                        "study": study,
                        "subject": subject_context(record, subject),
                    },
                    "request": _identity_request(record, obs),
                    "question_attribution": {
                        "status": "recorded",
                        "kind": "recorded",
                        "basis": "requested_by=identity_question",
                        "candidates": None,
                        "rests_on": ROUTING_BASIS,
                    },
                    "execution": execution,
                    "state": _credited(identity_state(record, subject), execution),
                    "independent_outcome": identity_outcome(
                        call_index, uid, subject, source, execution["status"]
                    ),
                },
            )
        )
    for index, obs in other:
        subject = obs.get("subject")
        rows.append(
            _row(
                source,
                uid,
                f"{source['run']}|{uid}|{index:03d}",
                {
                    "context": {
                        "study": study,
                        "subject": subject_context(record, subject),
                    },
                    "request": {
                        "kind": None,
                        "subject": subject,
                        "question": None,
                        "requested_by": obs.get("requested_by"),
                        "reason": None,
                        "provenance": {"question": "not_recorded"},
                    },
                    "question_attribution": {
                        "status": "not_reconstructed",
                        "kind": "other_requester",
                        "basis": "requester_not_understood",
                        "candidates": None,
                        "rests_on": ROUTING_BASIS,
                    },
                    "execution": _execution(observations, index, obs),
                    "state": {
                        "scope": "unknown",
                        "before": None,
                        "after": None,
                        "changed": None,
                    },
                    "independent_outcome": _unchecked("question_not_attributed"),
                },
            )
        )
    return rows


def _empty_condition_state() -> dict[str, Any]:
    return {
        "scope": "condition",
        "before": dict(_BEFORE_OPEN),
        "after": None,
        "changed": None,
    }


def _routed_rows(
    record: Mapping[str, Any],
    source: Mapping[str, Any],
    uid: str,
    study: dict[str, Any],
    labels: Mapping[str, Any],
    cap: int,
) -> list[dict[str, Any]]:
    observations = _sequence(record.get("observations"))
    _identity, routed, _other = split_observations(observations)
    unresolved = [
        u
        for u in _sequence(record.get("unresolved_observation_requests"))
        if isinstance(u, Mapping)
    ]
    attributions, request_matches = attribute_routed(
        [str(obs.get("subject")) for _i, obs in routed],
        unresolved,
        list(_mapping(record.get("questions"))),
        contract_subjects(record),
        cap=cap,
    )
    rows = []
    for position, (index, obs) in enumerate(routed):
        attribution = attributions[position]
        subject = obs.get("subject")
        execution = _execution(observations, index, obs)
        listed = (
            unresolved[attribution["unresolved_index"]]
            if attribution["kind"] == "aligned"
            else None
        )
        question = attribution.get("question")
        rows.append(
            _row(
                source,
                uid,
                f"{source['run']}|{uid}|{index:03d}",
                {
                    "context": {
                        "study": study,
                        "subject": subject_context(record, subject),
                        "subject_identity_final": _identity_consumed_final(
                            record, subject
                        ),
                    },
                    "request": _condition_request(obs, attribution, listed),
                    "question_attribution": _attribution_block(attribution),
                    "execution": execution,
                    "state": _credited(
                        condition_state(record, question, subject)
                        if question
                        else _empty_condition_state(),
                        execution,
                    ),
                    "independent_outcome": condition_outcome(
                        labels, uid, question, execution["status"]
                    ),
                },
            )
        )
    placed = {a["unresolved_index"] for a in attributions if a["kind"] == "aligned"}
    for j, request in enumerate(unresolved):
        if j in placed:
            continue
        subject, question = request.get("subject"), request.get("question")
        candidates = request_matches[j] if j < len(request_matches) else []
        rows.append(
            _row(
                source,
                uid,
                f"{source['run']}|{uid}|u{j:03d}",
                {
                    "context": {
                        "study": study,
                        "subject": subject_context(record, subject),
                        "subject_identity_final": _identity_consumed_final(
                            record, subject
                        ),
                    },
                    "request": {
                        **{
                            k: request.get(k)
                            for k in (
                                "kind",
                                "subject",
                                "question",
                                "reason",
                                "scope",
                                "bounded",
                                "full_study",
                                "discretionary",
                                "request_id",
                            )
                        },
                        "procedure": None,
                        "requested_by": None,
                        "listed_after_the_look": True,
                        "provenance": {
                            "question": "recorded",
                            "reason": "recorded_after_the_look",
                        },
                    },
                    "question_attribution": {
                        "status": "recorded",
                        "kind": "final_request_without_a_unique_routed_row",
                        "basis": "unresolved_observation_requests",
                        "candidates": None,
                        "rests_on": ROUTING_BASIS,
                    },
                    "execution": {
                        "observation_index": None,
                        "status": NOT_RUN,
                        "reading_available": False,
                        "new_reading": False,
                        "code": None,
                        "reason": "second_pass_request_not_routed_as_listed",
                        "candidate_first_pass_observations": [
                            routed[c][0] for c in candidates
                        ],
                        "reading_supplied_by": None,
                    },
                    "state": {
                        **condition_state(record, question, subject),
                        "changed": None,
                    },
                    "independent_outcome": condition_outcome(
                        labels, uid, question, NOT_RUN
                    ),
                },
            )
        )
    return rows


def experience_rows(
    record: Mapping[str, Any],
    source: Mapping[str, Any],
    *,
    labels: Mapping[str, Any],
    call_index: Mapping[str, Any],
    cap: int = 1000,
) -> list[dict[str, Any]]:
    """One row per request that had any: identity looks, routed condition rows, unmatched finals.

    ``source`` must carry every pin in ``REQUIRED_PINS`` (a record without them is refused).
    """
    _require_pins(source)
    if record.get("schema") != "knee.squint-study/v1":
        raise ValueError("not a knee.squint-study/v1 record")
    uid = str(record.get("study_uid"))
    study = study_context(record)
    return _identity_rows(record, source, uid, study, call_index) + _routed_rows(
        record, source, uid, study, labels, cap
    )


# --------------------------------------------------------------------------- reporting helper


def tally(rows: Sequence[Mapping[str, Any]], key: Any) -> dict[str, int]:
    """Counts of ``key(row)`` over rows, for reporting only (no score is derived from them)."""
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[str(key(row))] += 1
    return dict(sorted(counts.items()))
