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

import copy
import csv
import hashlib
import io
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

__all__ = [
    "PROCEDURE_EXPERIENCES_SCHEMA",
    "SCHEMA",
    "alignments",
    "attribute_routed",
    "build_call_index",
    "condition_outcome",
    "contract_subjects",
    "execution_status",
    "experience_rows",
    "identity_outcome",
    "independent_agreement",
    "information_obtained",
    "parse_candidate_id",
    "read_label_table",
    "recall_procedure_experiences",
    "retain_procedure_experiences",
    "select_observation_requests",
    "split_observations",
    "tally",
]

SCHEMA = "knee.procedure-experience/v1"
PROCEDURE_EXPERIENCES_SCHEMA = "knee.procedure-experience-memory/v1"
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


def _cue_banks_from_profile(profile: object) -> dict[str, list[int]]:
    """Extract coarse 10 mm banks when present, else all valid 3-count banks."""
    if not isinstance(profile, Mapping):
        return {}
    raw = profile.get("banks")
    if not isinstance(raw, Mapping):
        return {}
    all_banks: dict[str, list[int]] = {}
    coarse_banks: dict[str, list[int]] = {}
    for name, counts in raw.items():
        if (
            not isinstance(name, str)
            or not name
            or not isinstance(counts, (list, tuple))
            or len(counts) != 3
            or any(type(v) is not int or v < 0 for v in counts)
        ):
            continue
        triple = [int(counts[0]), int(counts[1]), int(counts[2])]
        if not any(triple):
            continue
        all_banks[name] = triple
        if name.rsplit("/scale=", 1)[-1] == "10mm":
            coarse_banks[name] = triple
    return coarse_banks if coarse_banks else all_banks


def _observed_cue(
    record: Mapping[str, Any],
    subject: object,
    obs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Observed HDC cue before the procedure ran, or coarse 10 mm banks from the record."""
    before_cue = obs.get("before_cue") if isinstance(obs, Mapping) else None
    if isinstance(before_cue, Mapping):
        banks = _cue_banks_from_profile(before_cue)
        return {
            "banks": banks,
            "procedure": before_cue.get("procedure"),
            "provenance": "recorded_before_procedure",
        }
    obj = _mapping(_mapping(record.get("objects")).get(subject))
    profile = _mapping(obj.get("profile"))
    banks = _cue_banks_from_profile(profile)
    return {
        "banks": banks,
        "procedure": _mapping(profile.get("source")).get("procedure"),
        "provenance": "coarse_banks_from_record" if banks else "not_recorded",
    }


def subject_context(
    record: Mapping[str, Any],
    subject: object,
    obs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
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
        "observed_cue": _observed_cue(record, subject, obs=obs),
    }


# --------------------------------------------------------------------------- states


def _recall_entry(entry: object) -> dict[str, Any] | None:
    if not isinstance(entry, Mapping):
        return None
    negatives = entry.get("applicable_negative_case_ids")
    if isinstance(negatives, (list, tuple)):
        neg_count = len(negatives)
    elif "applicable_negative_cases" in entry and isinstance(
        entry["applicable_negative_cases"], int
    ):
        neg_count = entry["applicable_negative_cases"]
    else:
        neg_count = 0
    return {
        "scale": entry.get("scale"),
        "outcome": entry.get("outcome"),
        "identity_state": entry.get("identity_state"),
        "appearance": entry.get("appearance"),
        "reason": entry.get("reason"),
        "applicable_negative_cases": neg_count,
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


def identity_state(
    record: Mapping[str, Any],
    subject: object,
    obs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Identity at 10 mm, after the finer look, and as the condition consumer finally read it.

    ``before`` is ``identity_recall.objects`` (10 mm; the reading that opened the contest);
    ``after`` is ``identity_recall.resolved_scale.objects`` (the joint 10 mm + 2 mm recall);
    ``changed`` says only that the recall outcome category differs between the two.
    A directly recorded observation instead retains that action's own snapshots;
    the final aggregate is never attributed to an earlier identity look.
    """
    if (
        isinstance(obs, Mapping)
        and obs.get("attribution_scope") == "single_procedure"
        and isinstance(obs.get("before_state"), Mapping)
        and isinstance(obs.get("after_state"), Mapping)
        and isinstance(obs.get("after_identity_consumption"), Mapping)
    ):
        before = _recall_entry(obs["before_state"])
        after = _recall_entry(obs["after_state"])
        return {
            "scope": "identity",
            "attribution_scope": "single_procedure",
            "before": before,
            "after": after,
            "consumed": dict(obs["after_identity_consumption"]),
            "changed": None
            if before is None or after is None
            else before["outcome"] != after["outcome"],
        }
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
        "attribution_scope": "question_final_finding",
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


def _has_direct_attribution(row: Mapping[str, Any]) -> bool:
    question = row.get("question")
    return (
        isinstance(question, str)
        and bool(question)
        and ("before_state" in row or "request_id" in row)
    )


def condition_state(
    record: Mapping[str, Any],
    question: str | None,
    subject: object,
    obs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """The condition finding before and after the observation step.

    When the observation row carries ``before_state`` and ``after_state`` directly,
    both states come from that single procedure step with ``provenance: recorded`` so
    an earlier look that left the question open is never credited with a later look's
    decision. On older records without ``after_state``, ``before.outcome`` is ``open``
    by construction and ``after`` is the final finding recorded on the question.
    """
    after_raw = obs.get("after_state") if isinstance(obs, Mapping) else None
    after = None
    if isinstance(after_raw, Mapping):
        after = {
            "outcome": after_raw.get("outcome"),
            "provenance": "recorded",
            "reason": after_raw.get("reason"),
            "value": after_raw.get(
                "value", _mapping(record.get("values")).get(question)
            ),
            "tier": after_raw.get("tier"),
            "subject_reading": after_raw.get("subject_reading"),
            "requests_still_listed": [
                str(item) for item in _sequence(after_raw.get("requests_listed"))
            ],
        }
    else:
        body = _mapping(_mapping(record.get("questions")).get(question))
        finding = _mapping(body.get("finding"))
        if finding:
            after = {
                "outcome": finding.get("outcome"),
                "provenance": "recorded_after_the_look",
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
    before_raw = obs.get("before_state") if isinstance(obs, Mapping) else None
    if isinstance(before_raw, Mapping):
        before = {
            "outcome": before_raw.get("outcome", CONDITION_BEFORE),
            "provenance": "recorded",
            "reason": before_raw.get("reason"),
            "reason_provenance": (
                "recorded" if before_raw.get("reason") is not None else "not_recorded"
            ),
            "tier": before_raw.get("tier"),
            "subject_reading": before_raw.get("subject_reading"),
            "requests_listed": before_raw.get("requests_listed"),
        }
    else:
        before = dict(_BEFORE_OPEN)
    before_outcome = before.get("outcome", CONDITION_BEFORE)
    before_reading = before.get("subject_reading")
    after_reading = after.get("subject_reading") if isinstance(after, Mapping) else None
    reading_changed = (
        before_reading != after_reading
        if isinstance(before_reading, Mapping) and isinstance(after_reading, Mapping)
        else None
    )
    return {
        "scope": "condition",
        "attribution_scope": (
            "single_procedure"
            if isinstance(after_raw, Mapping)
            else "question_final_finding"
        ),
        "before": before,
        "after": after,
        "reading_changed": reading_changed,
        "changed": None if after is None else after["outcome"] != before_outcome,
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
    """Independent study-condition teaching for a request that actually ran.

    Report entries are already verified by ``import_report_calls`` at export.
    Silence/held calls cannot erase a numeric label; opposing independent calls
    remain an unchecked disagreement rather than silently choosing a source.
    """
    if status == NOT_RUN:
        return _unchecked("request_did_not_run")
    if question is None:
        return _unchecked("question_not_attributed")
    if uid not in labels.get("table_uids", ()):
        return _unchecked("study_not_in_the_label_table")
    call = _mapping(_mapping(labels.get("calls")).get(uid)).get(question)
    report_calls = [
        dict(entry)
        for entry in _sequence(
            _mapping(_mapping(labels.get("report_calls")).get(uid)).get(question)
        )
        if isinstance(entry, Mapping)
        and entry.get("status") in ("signed", "contradictory")
        and entry.get("scope") == "study_condition"
        and entry.get("digit") in (-1, 1)
    ]
    if report_calls:
        digits = {entry["digit"] for entry in report_calls}
        if call in (-1, 1):
            digits.add(call)
        provenance = {
            "report_calls": report_calls,
            "report_source": labels.get("source"),
        }
        if len(digits) != 1:
            return {
                **_unchecked("independent_call_conflict"),
                "scope": "study_condition",
                "official_label_call": call,
                "label_source": labels.get("source"),
                **provenance,
            }
        return {
            "status": "checked",
            "source": (
                "official_label_and_report" if call in (-1, 1) else "independent_report"
            ),
            "call": next(iter(digits)),
            "scope": "study_condition",
            "reader": "verified report calls",
            "label_source": labels.get("source") if call in (-1, 1) else None,
            **provenance,
        }
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
    kind = row.get("request_kind") or ZOOM_KIND
    reason = row.get("request_reason") or CONTEST_REASON
    scope = row.get("request_scope") or "object_window"
    request_id = row.get("request_id")
    return {
        "kind": kind,
        "procedure": PAIRED_PROCEDURE,
        "subject": subject,
        "question": row.get("question") or IDENTITY_QUESTION,
        "reason": reason,
        "scope": scope,
        "bounded": True,
        "requested_by": row.get("requested_by") or IDENTITY_REQUESTER,
        "listed_after_the_look": None,
        "request_id": request_id,
        "provenance": {
            "question": "recorded",
            "reason": "recorded"
            if "request_reason" in row
            else (
                "derived_from_code_path"
                if subject in contested
                else "derived_from_code_path_but_subject_not_in_the_contest_list"
            ),
            "kind": "recorded" if "request_kind" in row else "derived_from_code_path",
            "scope": "recorded" if "request_scope" in row else "derived_from_code_path",
        },
    }


def _attribution_block(
    attribution: Mapping[str, Any], row: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    if isinstance(row, Mapping) and _has_direct_attribution(row):
        return {
            "status": "recorded",
            "kind": "recorded",
            "basis": "recorded_on_observation_row",
            "candidates": None,
            "rests_on": "direct_observation_attribution",
        }
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
    if _has_direct_attribution(row):
        kind = (
            row.get("request_kind")
            or row.get("kind")
            or (listed.get("kind") if listed else ZOOM_KIND)
        )
        reason = (
            row.get("request_reason")
            if "request_reason" in row
            else (listed.get("reason") if listed else None)
        )
        scope = (
            row.get("request_scope")
            if "request_scope" in row
            else (listed.get("scope") if listed else None)
        )
        return {
            "kind": kind,
            "procedure": PAIRED_PROCEDURE
            if kind == ZOOM_KIND
            else row.get("procedure"),
            "subject": row.get("subject"),
            "question": row.get("question"),
            "reason": reason,
            "scope": scope,
            "bounded": listed.get("bounded", True) if listed else True,
            "full_study": listed.get("full_study", False) if listed else False,
            "discretionary": listed.get("discretionary", True) if listed else True,
            "request_id": row.get("request_id")
            or (listed.get("request_id") if listed else None),
            "requested_by": None,
            "listed_after_the_look": listed is not None,
            "provenance": {
                "question": "recorded",
                "reason": "recorded" if reason is not None else "not_recorded",
                "kind": "recorded",
                "scope": "recorded" if scope is not None else "not_recorded",
                "first_pass_reason": (
                    "recorded" if "request_reason" in row else "not_recorded"
                ),
            },
        }
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


def information_obtained(
    execution: Mapping[str, Any], state: Mapping[str, Any]
) -> dict[str, Any]:
    """What the observation procedure itself obtained, distinct from the final verdict."""
    new_reading = bool(execution.get("new_reading"))
    reading_available = bool(execution.get("reading_available"))
    if new_reading:
        status = "new_reading_obtained"
    elif reading_available:
        status = "reading_already_available"
    else:
        status = "no_new_reading_available"
    return {
        "status": status,
        "new_reading": new_reading,
        "reading_available": reading_available,
        "reading_changed": state.get("reading_changed"),
        "finding_changed": state.get("changed"),
        "attribution_scope": state.get("attribution_scope", "question_final_finding"),
    }


def independent_agreement(
    state: Mapping[str, Any], independent_outcome: Mapping[str, Any]
) -> dict[str, Any]:
    """Compare the post-action state against the independent call without conflating them."""
    if independent_outcome.get("status") != "checked":
        return {
            "status": "unchecked",
            "independent_call": None,
            "after_answer": None,
        }
    scope = state.get("scope")
    if scope == "condition":
        call = independent_outcome.get("call")
        after_outcome = _get(state, "after", "outcome")
        after_answer = (
            1
            if after_outcome == "assigned"
            else -1
            if after_outcome == "defeated"
            else 0
        )
        if call not in (-1, 1):
            status = "unchecked"
        elif after_answer == 0:
            status = "unresolved_after_action"
        elif after_answer == call:
            status = "matches_independent_call"
        else:
            status = "contradicts_independent_call"
        return {
            "status": status,
            "independent_call": call,
            "after_outcome": after_outcome,
            "after_answer": after_answer,
        }
    if scope == "identity":
        calls = {
            c.get("call")
            for c in _sequence(independent_outcome.get("evidence"))
            if isinstance(c, Mapping)
        }
        read_as = _get(state, "consumed", "region_read_as_subject")
        if state.get("attribution_scope") == "single_procedure" and _get(
            state, "consumed", "identity_effect"
        ) not in ("answers", "appearance_opposed"):
            # Withholding a disputed support from diagnosis does not assert
            # that its identity is false. Only a decided effect can be checked.
            read_as = None
        if "confirm" in calls and "reject" not in calls:
            status = (
                "matches_independent_call"
                if read_as is True
                else "contradicts_independent_call"
                if read_as is False
                else "unresolved_after_action"
            )
            ind_call: Any = "confirm"
        elif "reject" in calls and "confirm" not in calls:
            status = (
                "matches_independent_call"
                if read_as is False
                else "contradicts_independent_call"
                if read_as is True
                else "unresolved_after_action"
            )
            ind_call = "reject"
        else:
            status = "unresolved_after_action"
            ind_call = sorted(str(c) for c in calls)
        return {
            "status": status,
            "independent_call": ind_call,
            "after_answer": read_as,
        }
    return {"status": "unchecked", "independent_call": None, "after_answer": None}


def _row(
    source: Mapping[str, Any],
    uid: str,
    row_id: str,
    parts: Mapping[str, Any],
) -> dict[str, Any]:
    pins = {key: source[key] for key in REQUIRED_PINS}
    extras = {k: v for k, v in source.items() if k not in REQUIRED_PINS}
    execution = _mapping(parts.get("execution"))
    state = _mapping(parts.get("state"))
    outcome = _mapping(parts.get("independent_outcome"))
    return {
        "schema": SCHEMA,
        "row_id": row_id,
        "source": {**pins, "study_uid": uid, **extras},
        **parts,
        "information_obtained": information_obtained(execution, state),
        "independent_agreement": independent_agreement(state, outcome),
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
                        "subject": subject_context(record, subject, obs=obs),
                    },
                    "request": _identity_request(record, obs),
                    "question_attribution": (
                        _attribution_block({}, obs)
                        if _has_direct_attribution(obs)
                        else {
                            "status": "recorded",
                            "kind": "recorded",
                            "basis": "requested_by=identity_question",
                            "candidates": None,
                            "rests_on": ROUTING_BASIS,
                        }
                    ),
                    "execution": execution,
                    "state": _credited(identity_state(record, subject, obs), execution),
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
                        "subject": subject_context(record, subject, obs=obs),
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
    placed = {a["unresolved_index"] for a in attributions if a["kind"] == "aligned"}
    for position, (index, obs) in enumerate(routed):
        attribution = attributions[position]
        subject = obs.get("subject")
        execution = _execution(observations, index, obs)
        listed = (
            unresolved[attribution["unresolved_index"]]
            if attribution["kind"] == "aligned"
            else None
        )
        direct = _has_direct_attribution(obs)
        question = obs.get("question") if direct else attribution.get("question")
        if direct and listed is None:
            for j, req in enumerate(unresolved):
                if j in placed:
                    continue
                if (
                    req.get("question") == question
                    and req.get("subject") == subject
                    and (
                        obs.get("request_id") is None
                        or req.get("request_id") == obs.get("request_id")
                    )
                ):
                    listed = req
                    placed.add(j)
                    break
        rows.append(
            _row(
                source,
                uid,
                f"{source['run']}|{uid}|{index:03d}",
                {
                    "context": {
                        "study": study,
                        "subject": subject_context(record, subject, obs=obs),
                        "subject_identity_final": _identity_consumed_final(
                            record, subject
                        ),
                    },
                    "request": _condition_request(obs, attribution, listed),
                    "question_attribution": _attribution_block(attribution, obs),
                    "execution": execution,
                    "state": _credited(
                        condition_state(record, question, subject, obs=obs)
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


# --------------------------------------------------------------------------- memory retention and recall


_RUNTIME_MEMORY_KEYS = frozenset(
    {"prepared_recall", "view", "memory_manifest_sha256", "full_profile_retention"}
)


def retain_procedure_experiences(
    memory: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    *,
    revision: str | None = None,
) -> dict[str, Any]:
    """Retain checked procedure-experience rows in a child memory mapping.

    Only checked rows that ran (``independent_outcome.status == "checked"`` and
    ``execution.status != "not_run"``) with valid source pins enter memory. Each
    retained row keeps its ``source.study_uid`` so ``memory_view`` and
    ``recall_procedure_experiences`` exclude a study's own experiences when that
    study is held out.
    """
    if not isinstance(memory, Mapping) or not isinstance(memory.get("revision"), str):
        raise TypeError("memory_invalid")
    existing_table = _mapping(memory.get("procedure_experiences"))
    existing_rows = [
        copy.deepcopy(dict(row))
        for row in _sequence(existing_table.get("rows"))
        if isinstance(row, Mapping) and isinstance(row.get("row_id"), str)
    ]
    seen_ids = {row["row_id"] for row in existing_rows}
    added: list[dict[str, Any]] = []
    for raw in rows:
        if not isinstance(raw, Mapping) or raw.get("schema") != SCHEMA:
            continue
        row_id = raw.get("row_id")
        if not isinstance(row_id, str) or not row_id or row_id in seen_ids:
            continue
        source = _mapping(raw.get("source"))
        _require_pins(source)
        study_uid = source.get("study_uid") or raw.get("study_uid")
        if not isinstance(study_uid, str) or not study_uid:
            raise ValueError(f"procedure_experience_study_uid_missing: {row_id}")
        if _mapping(raw.get("execution")).get("status") == NOT_RUN:
            continue
        if _mapping(raw.get("independent_outcome")).get("status") != "checked":
            continue
        entry = copy.deepcopy(dict(raw))
        entry["study_uid"] = study_uid
        seen_ids.add(row_id)
        added.append(entry)
    added.sort(key=lambda item: item["row_id"])
    merged = existing_rows + added
    child = {
        key: value for key, value in memory.items() if key not in _RUNTIME_MEMORY_KEYS
    }
    child["procedure_experiences"] = {
        "schema": PROCEDURE_EXPERIENCES_SCHEMA,
        "rows": merged,
    }
    if revision is not None:
        child["revision"] = revision
    elif added:
        digest = hashlib.sha256(
            json.dumps(
                [item["row_id"] for item in added],
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        child["revision"] = f"{memory['revision']}+procedure-memory-{digest[:16]}"
    return child


def _is_context_compatible(
    reason1: object,
    loc_status1: object,
    reason2: object,
    loc_status2: object,
) -> bool:
    """True if two observation or query contexts are mutually compatible.

    Does not require mandatory presence of all metadata fields. Only when both
    contexts assert a non-empty string for the same field and differ does it mismatch.
    """
    if (
        isinstance(reason1, str)
        and reason1
        and isinstance(reason2, str)
        and reason2
        and reason1 != reason2
    ):
        return False
    return not (
        isinstance(loc_status1, str)
        and loc_status1
        and isinstance(loc_status2, str)
        and loc_status2
        and loc_status1 != loc_status2
    )


def _is_opposing_category(category: str, other_cat: str) -> bool:
    """True if other_cat asserts an actual contrary outcome to category.

    Open or unattributed outcomes are unresolved evidence, not established
    procedural opposition.
    """
    if category == "confirmed_resolution":
        return other_cat in ("contradicted_outcome", "no_reading_available")
    if category in ("contradicted_outcome", "no_reading_available"):
        return other_cat == "confirmed_resolution"
    return False


def _empirical_opposition_floor(
    raw: Mapping[str, Any],
    row_banks: Mapping[str, Sequence[int]],
    common_banks: Sequence[str],
    category: str,
    rows: Sequence[Any],
    memory: Mapping[str, Any] | None,
    question_envelopes: Mapping[str, Any],
    excluded: str | None,
    query_context: Mapping[str, Any] | None = None,
) -> tuple[int, int] | None:
    """Finite empirical opposition floor over ``common_banks`` using ``_exact_bank_terms``.

    Opposition is scoped to this procedure's applicability in context:
    other attributed experiences for the same ``(subject, kind)`` (and
    ``question`` when present) with an opposing outcome category and compatible
    request reason/location context. An open outcome or an inapplicable failure
    cannot define this precedent's opposition floor.
    """
    from knee.diagnosis.squint_locator import _exact_bank_terms

    _ = question_envelopes
    restricted_left = {b: list(row_banks[b]) for b in common_banks if b in row_banks}
    if not restricted_left:
        return None
    req = _mapping(raw.get("request"))
    subject = req.get("subject")
    question = req.get("question")
    req_kind = str(req.get("kind") or ZOOM_KIND)
    req_reason = req.get("reason")
    loc_status = _get(raw, "context", "subject", "location_status")
    query = _mapping(query_context)
    query_reason = query.get("request_reason", query.get("reason"))
    query_location = query.get("location_status")
    row_id = raw.get("row_id")
    opposing_ratios: list[tuple[int, int]] = []

    for other in rows:
        if not isinstance(other, Mapping) or other.get("row_id") == row_id:
            continue
        other_uid = other.get("study_uid") or _mapping(other.get("source")).get(
            "study_uid"
        )
        if excluded is not None and other_uid == excluded:
            continue
        if _mapping(other.get("independent_outcome")).get("status") != "checked":
            continue
        if _mapping(other.get("execution")).get("status") == NOT_RUN:
            continue
        other_req = _mapping(other.get("request"))
        other_subj = other_req.get("subject")
        if other_subj != subject:
            continue
        other_kind = str(other_req.get("kind") or ZOOM_KIND)
        if other_kind != req_kind:
            continue
        other_q = other_req.get("question")
        if other_q != question:
            continue
        other_reason = other_req.get("reason")
        other_loc_status = _get(other, "context", "subject", "location_status")
        if not _is_context_compatible(
            req_reason, loc_status, other_reason, other_loc_status
        ):
            continue
        if not _is_context_compatible(
            query_reason, query_location, other_reason, other_loc_status
        ):
            continue
        other_cat, _info, _agree = _row_category(other, other_kind)
        if not _is_opposing_category(category, other_cat):
            continue
        other_banks = _row_cue_banks(
            other,
            memory,
            str(other_uid) if isinstance(other_uid, str) else None,
            other_subj if isinstance(other_subj, str) else None,
        )
        if not other_banks:
            continue
        terms = _exact_bank_terms(restricted_left, other_banks)
        if terms.get("code") == "ok" and list(
            terms.get("common_speaking_banks", ())
        ) == list(common_banks):
            opposing_ratios.append(terms["cosine_squared"])

    return _max_ratio(opposing_ratios)


def _row_cue_banks(
    raw: Mapping[str, Any],
    memory: Mapping[str, Any] | None,
    row_uid: str | None,
    subject: str | None,
) -> dict[str, list[int]]:
    """Observed HDC cue banks from the experience row, or explicitly linked pre-action cue."""
    _ = (memory, row_uid, subject)
    cue = _mapping(_get(raw, "context", "subject", "observed_cue"))
    banks = _cue_banks_from_profile(cue)
    if banks and cue.get("provenance") == "recorded_before_procedure":
        return banks
    linked = _mapping(raw.get("pre_action_cue") or raw.get("linked_cue"))
    if linked:
        linked_banks = _cue_banks_from_profile(linked)
        if linked_banks:
            return linked_banks
    return {}


def _row_category(
    raw: Mapping[str, Any], req_kind: str
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    _ = req_kind
    execution = _mapping(raw.get("execution"))
    state = _mapping(raw.get("state"))
    outcome = _mapping(raw.get("independent_outcome"))
    info = (
        dict(raw["information_obtained"])
        if isinstance(raw.get("information_obtained"), Mapping)
        else information_obtained(execution, state)
    )
    agree = (
        dict(raw["independent_agreement"])
        if isinstance(raw.get("independent_agreement"), Mapping)
        else independent_agreement(state, outcome)
    )
    if state.get("attribution_scope") != "single_procedure":
        # The final answer can still teach diagnosis; it cannot credit or blame
        # an individual action without that action's recorded outcome.
        return "outcome_unattributed", info, agree
    if agree.get("status") == "contradicts_independent_call":
        return "contradicted_outcome", info, agree
    if (
        info.get("status") == "new_reading_obtained"
        and agree.get("status") == "matches_independent_call"
    ):
        return "confirmed_resolution", info, agree
    if info.get("status") in ("new_reading_obtained", "reading_already_available"):
        return "obtained_reading_open", info, agree
    return "no_reading_available", info, agree


def _max_ratio(ratios: Sequence[tuple[int, int]]) -> tuple[int, int] | None:
    best: tuple[int, int] | None = None
    for num, den in ratios:
        if best is None or num * best[1] > best[0] * den:
            best = (num, den)
    return best


def recall_procedure_experiences(
    memory: Mapping[str, Any] | None,
    *,
    question: str | None,
    subject: str | None,
    kind: str | None = None,
    query_profile: Mapping[str, Any] | None = None,
    query_context: Mapping[str, Any] | None = None,
    study_uid: str | None = None,
    exclude_same_study: bool = False,
) -> dict[str, Any]:
    """Contextual K-line recall of checked procedure experiences for ``(question, subject, kind)``.

    * Requires an observed visual/HDC cue on ``query_profile`` (or ``query_context``).
      Without a visual cue, returns ``status: "no_contextual_cue"`` and never matches or
      vetoes by name alone.
    * Compares shared speaking HDC banks via ``squint_locator._exact_bank_terms`` and
      observed request/location context, supporting partial views without requiring
      complete geometry.
    * Distinguishes ``information_obtained`` from ``independent_agreement``:
      a state change that contradicts the independent call is ``recalled_outcome_contradicted``
      (never prioritized), and a measurement that obtained a reading while leaving the
      question open is ``recalled_reading_obtained_open`` (never a veto).
    """
    from knee.diagnosis.squint_locator import _exact_bank_terms

    table = _mapping(_mapping(memory).get("procedure_experiences"))
    rows = _sequence(table.get("rows"))
    q_ctx = _mapping(query_context)
    query_banks = _cue_banks_from_profile(query_profile)
    if not query_banks and isinstance(q_ctx.get("profile"), Mapping):
        query_banks = _cue_banks_from_profile(q_ctx.get("profile"))
    if not query_banks and isinstance(q_ctx.get("observed_cue"), Mapping):
        query_banks = _cue_banks_from_profile(q_ctx.get("observed_cue"))
    if not query_banks:
        return {
            "question": question,
            "subject": subject,
            "kind": kind,
            "status": "no_contextual_cue",
            "reason": "query_visual_cue_required",
            "confirmed_resolution_row_ids": [],
            "obtained_reading_open_row_ids": [],
            "contradicted_outcome_row_ids": [],
            "no_reading_available_row_ids": [],
            "unattributed_outcome_row_ids": [],
            "context_mismatch_row_ids": [],
            "incompatible_cue_row_ids": [],
            "matched_cues": [],
            "compared_count": 0,
        }
    confirmed_ids: list[str] = []
    open_reading_ids: list[str] = []
    contradicted_ids: list[str] = []
    no_reading_ids: list[str] = []
    unattributed_ids: list[str] = []
    context_mismatch_ids: list[str] = []
    incompatible_cue_ids: list[str] = []
    matched_cues: list[dict[str, Any]] = []
    confirmed_ratios: list[tuple[int, int]] = []
    opposing_ratios: list[tuple[int, int]] = []
    excluded = study_uid if exclude_same_study and study_uid else None
    q_reason = q_ctx.get("request_reason", q_ctx.get("reason"))
    q_loc_status = q_ctx.get("location_status")
    question_envelopes = _mapping(
        _get(memory, "prepared_recall", "envelopes", str(subject), str(question))
    )
    for raw in rows:
        if not isinstance(raw, Mapping):
            continue
        row_uid = raw.get("study_uid") or _mapping(raw.get("source")).get("study_uid")
        if excluded is not None and row_uid == excluded:
            continue
        if _mapping(raw.get("independent_outcome")).get("status") != "checked":
            continue
        execution = _mapping(raw.get("execution"))
        if execution.get("status") == NOT_RUN:
            continue
        req = _mapping(raw.get("request"))
        if req.get("question") != question or req.get("subject") != subject:
            continue
        req_kind = str(req.get("kind") or ZOOM_KIND)
        if kind is not None and req_kind != kind:
            continue
        row_id = str(raw.get("row_id") or "")
        if not row_id:
            continue
        category, info, agree = _row_category(raw, req_kind)
        if category == "outcome_unattributed":
            unattributed_ids.append(row_id)
            continue
        r_reason = req.get("reason")
        r_loc_status = _get(raw, "context", "subject", "location_status")
        if not _is_context_compatible(q_reason, q_loc_status, r_reason, r_loc_status):
            context_mismatch_ids.append(row_id)
            continue
        row_banks = _row_cue_banks(
            raw,
            memory,
            str(row_uid) if isinstance(row_uid, str) else None,
            subject if isinstance(subject, str) else None,
        )
        if not row_banks:
            incompatible_cue_ids.append(row_id)
            continue
        evidence = _exact_bank_terms(query_banks, row_banks)
        if evidence.get("code") != "ok" or int(evidence.get("dot", 0)) <= 0:
            incompatible_cue_ids.append(row_id)
            continue
        common_banks = list(evidence["common_speaking_banks"])
        ratio = evidence["cosine_squared"]
        floor = _empirical_opposition_floor(
            raw,
            row_banks,
            common_banks,
            category,
            rows,
            memory,
            question_envelopes,
            excluded,
            q_ctx,
        )
        reaches_envelope = None
        if floor is not None:
            env_num, env_den = floor
            reaches_envelope = ratio[0] * env_den > env_num * ratio[1]
            if not reaches_envelope:
                incompatible_cue_ids.append(row_id)
                continue
        if category == "confirmed_resolution":
            confirmed_ids.append(row_id)
            confirmed_ratios.append(ratio)
        elif category == "contradicted_outcome":
            contradicted_ids.append(row_id)
            opposing_ratios.append(ratio)
        elif category == "obtained_reading_open":
            open_reading_ids.append(row_id)
        else:
            no_reading_ids.append(row_id)
            opposing_ratios.append(ratio)
        matched_cues.append(
            {
                "row_id": row_id,
                "study_uid": row_uid,
                "category": category,
                "common_speaking_banks": common_banks,
                "terms": {
                    k: evidence[k] for k in ("dot", "left_norm_sq", "right_norm_sq")
                },
                "squared_cosine": {
                    "numerator": str(ratio[0]),
                    "denominator": str(ratio[1]),
                },
                "reaches_empirical_envelope": reaches_envelope,
                "information_obtained": info["status"],
                "independent_agreement": agree["status"],
                "independent_call": agree.get("independent_call"),
            }
        )
    best_confirmed = _max_ratio(confirmed_ratios)
    best_opposing = _max_ratio(opposing_ratios)
    if (confirmed_ids and not contradicted_ids and not no_reading_ids) or (
        confirmed_ids
        and best_confirmed is not None
        and (
            best_opposing is None
            or best_confirmed[0] * best_opposing[1]
            > best_opposing[0] * best_confirmed[1]
        )
    ):
        status = "recalled_confirmed_resolution"
    elif contradicted_ids:
        status = "recalled_outcome_contradicted"
    elif open_reading_ids:
        status = "recalled_reading_obtained_open"
    elif no_reading_ids:
        status = "recalled_no_reading_in_context"
    elif incompatible_cue_ids or context_mismatch_ids:
        status = "no_context_compatible_experience"
    elif unattributed_ids:
        status = "no_attributed_experience"
    else:
        status = "no_precedent"
    info_counts = tally(matched_cues, lambda item: item["information_obtained"])
    agree_counts = tally(matched_cues, lambda item: item["independent_agreement"])
    return {
        "question": question,
        "subject": subject,
        "kind": kind,
        "status": status,
        "confirmed_resolution_row_ids": confirmed_ids,
        "obtained_reading_open_row_ids": open_reading_ids,
        "contradicted_outcome_row_ids": contradicted_ids,
        "no_reading_available_row_ids": no_reading_ids,
        "unattributed_outcome_row_ids": unattributed_ids,
        "context_mismatch_row_ids": context_mismatch_ids,
        "incompatible_cue_row_ids": incompatible_cue_ids,
        "information_obtained_counts": info_counts,
        "independent_agreement_counts": agree_counts,
        "matched_cues": matched_cues,
        "compared_count": len(matched_cues),
    }


def select_observation_requests(
    requests: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    memory: Mapping[str, Any] | None = None,
    *,
    objects: Mapping[str, Any] | None = None,
    finding: Mapping[str, Any] | None = None,
    study_uid: str = "",
    exclude_same_study: bool = False,
) -> list[dict[str, Any]]:
    """Order and annotate candidate observation requests from contextual procedure memory.

    * When memory holds no ``procedure_experiences`` rows, returns ``list(requests)``
      unchanged ("no record changes nothing").
    * Only a request with a compatible observed HDC cue and context whose checked
      precedents resolved in agreement with the independent call
      (``recalled_confirmed_resolution``) is promoted to tier 0.
    * A state change that contradicted the independent call
      (``recalled_outcome_contradicted``) or a look that obtained a reading while
      leaving the question open (``recalled_reading_obtained_open``) stays at
      neutral tier 1 and is never promoted or vetoed.
    * Only a request whose matching HDC-context precedents could obtain no reading
      at all (``recalled_no_reading_in_context``) is placed in tier 2.
    """
    if isinstance(requests, Mapping):
        if finding is None:
            finding = requests
        request_list = [
            r
            for r in _sequence(requests.get("observation_requests"))
            if isinstance(r, Mapping)
        ]
    else:
        request_list = [r for r in requests if isinstance(r, Mapping)]
    if not request_list:
        return []
    table = _mapping(_mapping(memory).get("procedure_experiences"))
    if not _sequence(table.get("rows")):
        return [dict(r) for r in request_list]
    obj_map = _mapping(objects)
    scored: list[tuple[int, int, dict[str, Any]]] = []
    for index, raw in enumerate(request_list):
        req = dict(raw)
        question = req.get("question")
        subject = req.get("object", req.get("subject"))
        kind = req.get("kind", ZOOM_KIND)
        located = _mapping(obj_map.get(subject)) if isinstance(subject, str) else {}
        query_profile = (
            req.get("query_profile")
            if isinstance(req.get("query_profile"), Mapping)
            else located.get("profile")
            if isinstance(located.get("profile"), Mapping)
            else located.get("squint_profile")
            if isinstance(located.get("squint_profile"), Mapping)
            else None
        )
        query_context = {
            "request_reason": req.get("reason"),
            "location_status": located.get("status"),
            "finding_reason": _mapping(finding).get("reason"),
        }
        recalled = recall_procedure_experiences(
            memory,
            question=question if isinstance(question, str) else None,
            subject=subject if isinstance(subject, str) else None,
            kind=kind if isinstance(kind, str) else None,
            query_profile=query_profile,
            query_context=query_context,
            study_uid=study_uid,
            exclude_same_study=exclude_same_study,
        )
        if recalled["status"] == "recalled_confirmed_resolution":
            tier = 0
            req["recalled_procedure"] = recalled
        elif recalled["status"] == "recalled_no_reading_in_context":
            tier = 2
            req["recalled_procedure"] = recalled
        else:
            tier = 1
            if recalled["status"] not in ("no_precedent", "no_contextual_cue"):
                req["recalled_procedure"] = recalled
        scored.append((tier, index, req))
    scored.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in scored]


# --------------------------------------------------------------------------- reporting helper


def tally(rows: Sequence[Mapping[str, Any]], key: Any) -> dict[str, int]:
    """Counts of ``key(row)`` over rows, for reporting only (no score is derived from them)."""
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[str(key(row))] += 1
    return dict(sorted(counts.items()))
