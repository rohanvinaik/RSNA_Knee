"""Named observation actions; the study coordinator owns interpretation.

Bounded zoom uses the existing paired reader. Location and profiling use the
delivered bounded consumers without a separate identity or diagnosis comparison.
Repeated recall validates its input and returns it to the coordinator's common
question pass. The coordinator refreshes identity in its actual anatomical context
after an action changes observations, sharing prepared memory and finer readings.
An identity dispute never blocks the additional observation that could settle it.
Each non-zoom action is shared once per subject and kind in a study.
"""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from knee.diagnosis.squint_interfaces import TERRITORY_PROCEDURE
from knee.diagnosis.squint_procedure_memory import (
    recall_procedure_experiences,
    select_observation_requests,
)

__all__ = [
    "BOUNDED_ZOOM",
    "LOCATE_OBJECT_REGION",
    "PROFILE_OBJECT_WINDOW",
    "REPEAT_OBJECT_RECALL",
    "SEARCH_NOT_RUN",
    "route_observation_request",
    "select_observation_requests",
]

BOUNDED_ZOOM = "bounded_zoom"
LOCATE_OBJECT_REGION = "locate_object_region"
PROFILE_OBJECT_WINDOW = "profile_object_window"
REPEAT_OBJECT_RECALL = "repeat_object_recall"
#: The v1 writer's procedure (``squint_profiles.profile_window``).
V1_PROCEDURE = "knee.squint-profile/scan-tercile-v1"
#: The locator's record of a search it never ran: the one reason a second search can change.
SEARCH_NOT_RUN = "deadline_before_search"
#: Why a location the locator completed cannot change, by the reason it recorded.
_LOCATION_COMPLETE = {
    "no_compatible_current_study_candidates": "precedent_gap",
    "no_current_study_candidate_profiles": "no_current_study_candidates",
    "no_anatomical_windows_available": "no_series_to_search",
    "no_compatible_anatomical_candidates": "search_completed_without_a_candidate",
    "coarse_ties_exceed_refinement_budget": "candidate_tie_exceeds_refinement_budget",
    "structural_anchor_without_readable_territory": "anchor_territories_unreadable",
}
_ANCHORED_SOURCE = "current_study_structural_anchor"
#: First element of the marker tuple a consumer leaves in the study's ``attempted`` set.
_MARKER = "observation_procedure"


@dataclass(slots=True)
class _Call:
    """One admitted request and the study state its consumer reads and updates."""

    request: Mapping[str, Any]
    kind: str
    subject: str
    question: str | None
    study: dict[str, Any]
    objects: dict[str, Any]
    memory: Mapping[str, Any]
    deadline: float | None
    excluded_uid: str | None
    withheld: dict[str, Any] | None
    identity_readings: dict[str, Any] | None
    identity_consumption: dict[str, Any] | None
    location_evidence: Mapping[str, Any] | None


def route_observation_request(
    request: object,
    study: object,
    objects: object,
    attempted: set,
    deadline: float | None,
    *,
    withheld: dict[str, Any] | None = None,
    memory: Mapping[str, Any] | None = None,
    study_uid: str = "",
    exclude_same_study: bool = False,
    identity_readings: dict[str, Any] | None = None,
    identity_consumption: dict[str, Any] | None = None,
    location_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Send one observation request to its kind's consumer and return that consumer's row.

    ``attempted`` is the study's set of the bounded reader; ``withheld``, ``identity_readings``
    and ``identity_consumption`` are the study's identity state, updated in place when a
    consumer makes a new reading that identity recall must hear; ``location_evidence`` is the
    location's study-level evidence (the knee side and the anchors it read).
    """
    kind = (
        request.get("kind", BOUNDED_ZOOM)
        if isinstance(request, Mapping)
        else BOUNDED_ZOOM
    )
    recalled: Mapping[str, Any] | None = None
    if isinstance(request, Mapping) and isinstance(memory, Mapping):
        attached = request.get("recalled_procedure")
        if isinstance(attached, Mapping):
            recalled = attached
        elif "procedure_experiences" in memory:
            subj = request.get("object", request.get("subject"))
            quest = request.get("question")
            if (
                isinstance(subj, str)
                and isinstance(quest, str)
                and isinstance(kind, str)
            ):
                located_obj = (
                    objects.get(subj) if isinstance(objects, Mapping) else None
                )
                query_profile = (
                    request.get("query_profile")
                    if isinstance(request.get("query_profile"), Mapping)
                    else located_obj.get("profile")
                    if isinstance(located_obj, Mapping)
                    and isinstance(located_obj.get("profile"), Mapping)
                    else located_obj.get("squint_profile")
                    if isinstance(located_obj, Mapping)
                    and isinstance(located_obj.get("squint_profile"), Mapping)
                    else None
                )
                query_context = {
                    "request_reason": request.get("reason"),
                    "location_status": (
                        located_obj.get("status")
                        if isinstance(located_obj, Mapping)
                        else None
                    ),
                }
                looked = recall_procedure_experiences(
                    memory,
                    question=quest,
                    subject=subj,
                    kind=kind,
                    query_profile=query_profile,
                    query_context=query_context,
                    study_uid=study_uid,
                    exclude_same_study=exclude_same_study,
                )
                if looked.get("status") not in ("no_precedent", "no_contextual_cue"):
                    recalled = looked
        if (
            recalled is not None
            and recalled.get("status") == "recalled_no_reading_in_context"
            and request.get("discretionary", True) is not False
        ):
            return {
                "kind": kind if isinstance(kind, str) else repr(kind),
                "subject": request.get("object", request.get("subject")),
                "question": request.get("question"),
                "code": "skipped_by_recalled_procedure",
                "reason": "recalled_procedure_had_no_available_reading_in_context",
                "recalled_procedure": dict(recalled),
            }
    if kind == BOUNDED_ZOOM:
        from knee.diagnosis import squint_pipeline

        zoom_obs = squint_pipeline._bounded_observation(
            request, study, objects, attempted, deadline
        )
        if recalled is not None:
            zoom_obs = {**zoom_obs, "recalled_procedure": dict(recalled)}
        return zoom_obs
    assert isinstance(request, Mapping)  # a request that is no mapping names no kind
    subject = request.get("object", request.get("subject"))
    question = request.get("question")
    row: dict[str, Any] = {
        "kind": kind if isinstance(kind, str) else repr(kind),
        "subject": subject if isinstance(subject, str) else None,
        "question": question if isinstance(question, str) else None,
    }
    if recalled is not None:
        row["recalled_procedure"] = dict(recalled)
    consumer = _CONSUMERS.get(kind) if isinstance(kind, str) else None
    if consumer is None:
        return {
            **row,
            "code": "request_kind_has_no_consumer",
            "reason": "no_acting_consumer_is_named_for_this_kind",
        }
    if not isinstance(subject, str) or not subject:
        return {**row, "code": "request_invalid", "reason": "request_names_no_object"}
    if not isinstance(objects, dict):
        return {
            **row,
            "code": "object_region_unavailable",
            "reason": "objects_not_a_mapping",
        }
    if not isinstance(study, dict):
        return {
            **row,
            "code": "object_region_unavailable",
            "reason": "study_not_a_mapping",
        }
    if not isinstance(memory, Mapping):
        return {**row, "code": "memory_unavailable", "reason": "memory_not_a_mapping"}
    if not isinstance(attempted, set):
        # A caller without the study's set keeps no answer between its calls.
        attempted = set()
    first = next(
        (
            item
            for item in attempted
            if isinstance(item, tuple)
            and len(item) == 4
            and item[:3] == (_MARKER, kind, subject)
        ),
        None,
    )
    if first is not None:
        return {
            **row,
            "code": "procedure_already_answered",
            "reason": "one_answer_per_object_and_kind_in_a_study",
            "first_code": first[3],
            "repeat": True,
        }
    call = _Call(
        request=request,
        kind=kind,
        subject=subject,
        question=row["question"],
        study=study,
        objects=objects,
        memory=memory,
        deadline=deadline,
        excluded_uid=study_uid if exclude_same_study else None,
        withheld=withheld,
        identity_readings=identity_readings,
        identity_consumption=identity_consumption,
        location_evidence=location_evidence,
    )
    answer = {**row, **consumer(call)}
    attempted.add((_MARKER, kind, subject, answer["code"]))
    return answer


def _past(deadline: float | None) -> bool:
    return deadline is not None and time.monotonic() >= deadline


# ---------------------------------------------------------------------------
# repeat_object_recall: once, on the validated current reading
# ---------------------------------------------------------------------------


def _profile_problem(profile: object, subject: str) -> str | None:
    """Why a reading cannot be recalled for ``subject``, or None when it is well formed."""
    if not isinstance(profile, Mapping):
        return "profile_not_a_mapping"
    if profile.get("subject") != subject:
        return "profile_names_another_object"
    banks = profile.get("banks")
    if not isinstance(banks, Mapping):
        return "profile_banks_not_a_mapping"
    for name, counts in banks.items():
        if (
            not isinstance(name, str)
            or not name
            or not isinstance(counts, (list, tuple))
            or len(counts) != 3
            or any(type(value) is not int or value < 0 for value in counts)
        ):
            return "profile_bank_invalid"
    return None


def _repeat_object_recall(call: _Call) -> dict[str, Any]:
    """Validate a repeated recall request; the coordinator owns its actual comparison."""
    if call.question is None:
        return {"code": "request_invalid", "reason": "request_names_no_question"}
    from knee.diagnosis.squint_pipeline import _empty_profile

    located = call.objects.get(call.subject)
    located = located if isinstance(located, Mapping) else {}
    profile = located.get("profile") or _empty_profile(call.subject)
    problem = _profile_problem(profile, call.subject)
    if problem is not None:
        return {"code": "current_profile_invalid", "reason": problem}
    if _past(call.deadline):
        return {"code": "deadline_before_recall", "reason": "study_deadline_reached"}
    return {
        "code": "recall_ready",
        "reason": "validated_reading_returned_to_the_question_coordinator",
    }


# ---------------------------------------------------------------------------
# shared: the memory's writer, and identity recall of a new reading
# ---------------------------------------------------------------------------


def _case_rows(memory: Mapping[str, Any]) -> list[Any]:
    cases = memory.get("cases", ())
    return (
        list(cases)
        if isinstance(cases, Sequence) and not isinstance(cases, (str, bytes))
        else []
    )


def _memory_writer(memory: Mapping[str, Any]) -> str:
    """The writer the locator chooses for this memory (``locate_anatomy_first``'s rule)."""
    from knee.diagnosis.squint_locator import _source

    territory = memory.get("procedure") == TERRITORY_PROCEDURE or any(
        isinstance(row, Mapping)
        and _source(row.get("profile")).get("procedure") == TERRITORY_PROCEDURE
        for row in _case_rows(memory)
    )
    return TERRITORY_PROCEDURE if territory else V1_PROCEDURE


# ---------------------------------------------------------------------------
# profile_object_window: the located regions, read with the memory's writer
# ---------------------------------------------------------------------------


def _read_region(
    call: _Call, region: Mapping[str, Any], writer: str, by_uid: Mapping[str, Any]
) -> tuple[dict[str, Any] | None, str | None]:
    """One located region's reading by ``writer``, as location reads it, or why not."""
    from knee.diagnosis.squint_pipeline import _region_window
    from knee.diagnosis.squint_profiles import (
        leg_calibration,
        profile_territory,
        profile_window,
    )

    series = by_uid.get(region.get("series_uid"))
    if series is None:
        return None, "series_not_in_study"
    if writer == V1_PROCEDURE:
        window = _region_window(dict(region))
        if window is None:
            return None, "region_window_invalid"
        try:
            return profile_window(dict(series), window, subject=call.subject), None
        except (TypeError, ValueError) as error:
            return None, f"writer_refused:{error}"
    from knee.diagnosis.squint_anatomy_locator import (
        retained_native_territory,
        territory_from_record,
    )

    record = region.get("territory")
    if not isinstance(record, Mapping):
        return None, "region_without_territory_record"
    try:
        territory = territory_from_record(record)
    except (TypeError, ValueError) as error:
        return None, f"territory_record_refused:{error}"
    if record.get("native_support_address") is not None:
        # The record holds its native mask as an address alone: the retained original is
        # the territory location read, or the reason is named (``_territory_pairing``).
        retained, why = retained_native_territory(call.study, record)
        if retained is None:
            return None, why
        territory = retained
    leg_map = series.get("leg_map")
    if leg_map is None and isinstance(call.study.get("leg_maps"), Mapping):
        leg_map = call.study["leg_maps"].get(region.get("series_uid"))
    if not isinstance(leg_map, dict):
        return None, "leg_map_unavailable"
    try:
        calibration = leg_calibration(series, leg_map)
        return (
            profile_territory(
                series,
                dict(territory),
                leg_map,
                subject=call.subject,
                calibration=calibration,
            ),
            None,
        )
    except (TypeError, ValueError) as error:
        return None, f"writer_refused:{error}"


def _merged(profiles: list[dict[str, Any]], subject: str) -> dict[str, Any] | None:
    """Location's merge: one profile stands alone, several are added, a refusal is none."""
    from knee.diagnosis.squint_profiles import merge_profiles

    if not profiles:
        return None
    try:
        return merge_profiles(profiles, subject=subject)
    except ValueError:
        return profiles[0] if len(profiles) == 1 else None


def _profile_object_window(call: _Call) -> dict[str, Any]:
    if call.request.get("reason") == "no_precedent":
        return {
            "code": "precedent_gap",
            "reason": "no_reading_supplies_a_missing_precedent",
        }
    located = call.objects.get(call.subject)
    if not isinstance(located, dict):
        return {"code": "object_region_unavailable", "reason": "object_not_located"}
    regions = located.get("regions")
    regions = (
        [item for item in regions if isinstance(item, Mapping)]
        if isinstance(regions, list)
        else []
    )
    if not regions:
        return {"code": "object_region_unavailable", "reason": "no_located_region"}
    from knee.diagnosis.squint_locator import _source, _view_key
    from knee.diagnosis.squint_pipeline import _region_address

    writer = _memory_writer(call.memory)
    previous = located.get("profile")
    if previous is not None and _source(previous).get("procedure") == writer:
        # The same writer over the same regions writes the same counts again.
        return {
            "code": "reading_unchanged",
            "reason": "reading_already_by_the_memory_writer",
            "procedure": writer,
        }
    if _past(call.deadline):
        return {"code": "deadline_before_profile", "reason": "study_deadline_reached"}
    by_uid = {
        row["series_uid"]: row
        for row in call.study.get("series", ())
        if isinstance(row, dict) and isinstance(row.get("series_uid"), str)
    }
    evidence = located.get("evidence")
    anchored = (
        isinstance(evidence, Mapping) and evidence.get("source") == _ANCHORED_SOURCE
    )
    if anchored:
        # An anchored bone merges every territory it read (``_anchored_object``).
        groups = [regions]
    else:
        # Any other object takes the one region of each view; a tie stays a tie.
        by_view: dict[Any, list[Mapping[str, Any]]] = {}
        for region in regions:
            by_view.setdefault(_view_key(region.get("view")), []).append(region)
        groups = list(by_view.values())
    profiles: list[dict[str, Any]] = []
    read: list[dict[str, Any]] = []
    unavailable: list[dict[str, Any]] = []
    tied: list[list[dict[str, Any]]] = []
    for group in groups:
        if not anchored and len(group) != 1:
            tied.append([_region_address(region) for region in group])
            continue
        for region in group:
            profile, why = _read_region(call, region, writer, by_uid)
            if profile is None:
                unavailable.append({**_region_address(region), "reason": why})
            elif not profile.get("banks"):
                unavailable.append(
                    {**_region_address(region), "reason": "writer_wrote_no_bank"}
                )
            else:
                profiles.append(profile)
                read.append(_region_address(region))
    outcome = {
        "procedure": writer,
        "regions": read,
        "unavailable_regions": unavailable,
        "tied_views": tied,
    }
    if not profiles:
        if tied and not unavailable:
            return {
                "code": "located_candidates_tied",
                "reason": "no_view_holds_a_single_located_region",
                **outcome,
            }
        return {
            "code": "no_compatible_reading",
            "reason": "no_located_region_read_by_the_memory_writer",
            **outcome,
        }
    merged = _merged(profiles, call.subject)
    if merged is None or not merged.get("banks"):
        return {
            "code": "no_compatible_reading",
            "reason": "memory_writer_readings_do_not_merge",
            **outcome,
        }
    if previous is not None:
        located["incompatible_writer_profile"] = previous
    located["profile"] = merged
    return {
        "code": "profiled",
        "reason": "located_regions_read_by_the_memory_writer",
        **outcome,
    }


# ---------------------------------------------------------------------------
# locate_object_region: the locator's per-object steps, for one object
# ---------------------------------------------------------------------------


def _locate_object_region(call: _Call) -> dict[str, Any]:
    """Extend the shared locator for one previously unsearched subject."""
    located = call.objects.get(call.subject)
    if not isinstance(located, Mapping):
        return {
            "code": "location_unchanged",
            "reason": "precedent_gap",
            "location_reason": "object_not_in_the_location_result",
        }
    if located.get("status") == "proposal":
        return {"code": "location_unchanged", "reason": "object_already_located"}
    evidence = located.get("evidence")
    evidence = evidence if isinstance(evidence, Mapping) else {}
    recorded = evidence.get("reason")
    if recorded != SEARCH_NOT_RUN:
        return {
            "code": "location_unchanged",
            "reason": _LOCATION_COMPLETE.get(recorded, "location_search_completed"),
            "location_reason": recorded,
        }
    if _past(call.deadline):
        return {
            "code": "deadline_before_location",
            "reason": "study_deadline_reached",
            "location_reason": recorded,
        }
    from knee.diagnosis.squint_anatomy_locator import locate_anatomy_first

    if _memory_writer(call.memory) != TERRITORY_PROCEDURE:
        return {
            "code": "location_unchanged",
            "reason": "bounded_location_reads_territory_memories_only",
            "location_reason": recorded,
        }
    result = locate_anatomy_first(
        call.study,
        call.memory,
        call.deadline,
        refine_finalists=False,
        subjects=(call.subject,),
    )
    record = result.get("objects", {}).get(call.subject)
    if not isinstance(record, dict):
        return {
            "code": "location_unchanged",
            "reason": result.get("reason", result.get("outcome", "location_refused")),
            "location_reason": recorded,
        }
    record["evidence"]["bounded_location"] = {
        "procedure": "squint_procedures.locate_object_region/v1",
        "question": call.question,
        "request_reason": call.request.get("reason"),
        "shared_locator": "knee.diagnosis.squint_anatomy_locator.locate_anatomy_first",
        "prior_location": dict(located),
    }
    call.objects[call.subject] = record
    if record["status"] != "proposal":
        reason = record["evidence"]["reason"]
        return {
            "code": "location_unchanged",
            "reason": _LOCATION_COMPLETE.get(reason, "location_search_completed"),
            "location_reason": reason,
            "location_status": record["status"],
        }
    from knee.diagnosis.squint_pipeline import _region_address

    return {
        "code": "located",
        "reason": "bounded_single_object_location",
        "location_status": record["status"],
        "location_reason_before": recorded,
        "regions": [_region_address(region) for region in record["regions"]],
    }


_CONSUMERS = {
    LOCATE_OBJECT_REGION: _locate_object_region,
    PROFILE_OBJECT_WINDOW: _profile_object_window,
    REPEAT_OBJECT_RECALL: _repeat_object_recall,
}
