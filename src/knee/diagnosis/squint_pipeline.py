"""Squint-first inference, bounded study lifetimes and official output.

The full reconstruction runner is a bootstrap/reference tool. This coordinator
never calls it. Each worker owns one study's decoded pixels and releases them
when its compact findings have been published. Case memory is loaded once.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import inspect
import json
import math
import os
import platform
import resource
import time
from collections import Counter
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from knee.diagnosis.squint_anatomy_locator import BONES as READER_BONES
from knee.diagnosis.squint_contracts import READOUT_POLICY_ID, contract_for
from knee.diagnosis.squint_identity import (
    CONDITIONING,
    CONTESTED_AFTER_FINER_READING,
    CONTESTED_AT_SQUINT_SCALE,
    CONTESTED_OUTCOMES,
    CONTEXT_SCHEMA,
    FINE_SCALE,
    IDENTITY_CONSUMPTION_SCHEMA,
    JOINT_SCALE,
    MAP_RELATION,
    PRIOR_ONLY,
    PROPOSED_PLACES,
    RECALL_CONTEXT_SCHEMA,
    RESOLVED_BY_FINER_READING,
    RESOLVED_SUPPORT,
    SIGNED_CONFLICT,
    SQUINT_SCALE,
    STRUCTURAL_READER,
    SUPPORT_UNRECORDED,
    holds_scale,
    squint_contest_resolution,
)
from knee.diagnosis.squint_interfaces import (
    MEASURED_ORIGINS,
    MEMORY_VIEW_SCHEMA,
    TERRITORY_PROCEDURE,
)
from knee.diagnosis.squint_locator import recall_source_fingerprint
from knee.diagnosis.squint_memory_view import memory_view
from knee.study.tables import LABELS

SCHEMA = "knee.squint-run/v1"
MEMORY_SCHEMA = "knee.squint-memory/v1"


class SquintRunError(ValueError):
    """A named source, output or invocation failure."""


def _manifest_path(path: Path) -> Path:
    return path / "manifest.json" if path.is_dir() else path


def is_squint_memory(path: Path | None) -> bool:
    """Select only an explicitly declared new memory; legacy stores keep their route."""
    if path is None:
        return False
    candidate = _manifest_path(Path(path))
    if not candidate.is_file():
        return False
    try:
        declaration = json.loads(candidate.read_text())
    except (OSError, ValueError, UnicodeError):
        return False
    return isinstance(declaration, dict) and declaration.get("schema") == MEMORY_SCHEMA


def _save(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    try:
        temporary.write_text(json.dumps(record, sort_keys=True, allow_nan=False))
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _table_uids(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "StudyInstanceUID" not in reader.fieldnames:
            raise SquintRunError("study_table_columns_invalid")
        rows = list(reader)
    uids = tuple(row["StudyInstanceUID"] for row in rows)
    if not uids or any(not uid or Path(uid).name != uid for uid in uids):
        raise SquintRunError("study_uid_invalid_or_empty")
    if len(set(uids)) != len(uids):
        raise SquintRunError("duplicate_study_uid")
    return uids


def _selected_uids(args) -> tuple[str, ...]:
    selected = getattr(args, "study_uid", None)
    if selected:
        uids = tuple(selected)
        if len(set(uids)) != len(uids) or any(
            not isinstance(uid, str) or not uid or Path(uid).name != uid for uid in uids
        ):
            raise SquintRunError("study_uid_invalid_or_duplicate")
        return uids
    root = Path(args.root)
    if getattr(args, "labeled", False):
        with (root / "train.csv").open(newline="", encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        uids = tuple(
            row["StudyInstanceUID"]
            for row in rows
            if all(row.get(label) in ("0", "1") for label in LABELS)
        )
        if not uids:
            raise SquintRunError("no_labeled_studies")
        return uids
    split = getattr(args, "split", None)
    if split not in ("train", "test"):
        raise SquintRunError("raw_study_selector_required")
    return _table_uids(root / (split + ".csv"))


def _empty_profile(subject: str) -> dict:
    return {
        "schema": "knee.squint-profile/v1",
        "subject": subject,
        "banks": {},
        "source": {
            "code": "object_not_located",
            "procedure": "knee.squint-profile/scan-tercile-v1",
        },
    }


#: The lens a generic bounded observation names: the paired finer reading of a reading
#: the object already holds (``refine_territory`` for a territory profile, otherwise
#: ``refine_window``). A request naming any other lens names a native procedure.
PAIRED_FINER_LENS = "physical_squint"


def _lineage_sources(profile: object):
    """Each writer call's source a profile was made from, through its merge lineage."""
    stack = [profile.get("source") if isinstance(profile, dict) else None]
    while stack:
        source = stack.pop()
        if not isinstance(source, dict):
            continue
        yield source
        lineage = source.get("lineage")
        if isinstance(lineage, list):
            stack.extend(lineage)


def _profile_origins(profile: object) -> set[str]:
    """Territory origins a profile was read from, through its merge lineage."""
    origins: set[str] = set()
    for source in _lineage_sources(profile):
        territory = source.get("territory")
        if isinstance(territory, dict) and isinstance(territory.get("origin"), str):
            origins.add(territory["origin"])
    return origins


def _decision_scope(subject: str, profile: object) -> str:
    """How far one object's reading may speak: ``decide``, ``grade_only`` or ``unavailable``.

    A compatible cheap reading decides at its own scope however it was placed: a useful
    anatomical prior is enough, and a native outline is an explicit tool, never a
    prerequisite (SQUINT_TRAINING_BUILD §10's gate on small parts is withdrawn). Only
    what an input states limits a reading: a ``decision_scope`` of ``grade_only`` in its
    source or merge lineage. An object with no reading (no profile, no banks, or another
    object's) is ``unavailable``. Where each reading was placed from stays named in the
    evidence (``query_origins``).
    """
    if (
        not isinstance(profile, dict)
        or profile.get("subject") != subject
        or not profile.get("banks")
    ):
        return "unavailable"
    if any(s.get("decision_scope") == "grade_only" for s in _lineage_sources(profile)):
        return "grade_only"
    return "decide"


def _recall_question(
    question,
    objects: dict,
    memory: dict,
    uid: str,
    excluded: bool,
    *,
    not_read_as: Mapping[str, Mapping] | None = None,
) -> dict:
    """Recall each of a question's objects and its whole configuration.

    Every located object answers as the object identified in context: its own reading
    is heard, and it composes the configuration. Resemblance to another object never
    changes that. ``not_read_as`` names the regions an applicable negative case speaks
    over (``_identity_consumption``): each reaches both voices exactly as an unlocated
    object does, so its questions stay open, never a normal reading and never a defeat,
    with its reason kept beside its evidence as ``region_not_read_as_subject``. Nothing
    renames it.
    """
    from knee.diagnosis.squint_locator import recall_object

    not_read = not_read_as if isinstance(not_read_as, Mapping) else {}
    if not_read:
        objects = {
            name: value for name, value in objects.items() if name not in not_read
        }
    try:
        from knee.diagnosis.squint_questions import question_selection

        selection = question_selection(question.question_id)
    except (ImportError, ValueError):
        selection = None
    # One declaration reaches both anatomical and role-qualified recalls.
    # A missing adapter is explicit invalid selection, never all-bank recall.
    memory = {**memory, "recall_selection": selection}
    evidence = {}
    for subject in question.objects:
        located = objects.get(subject, {})
        profile = located.get("profile") or _empty_profile(subject)
        record = {
            **recall_object(
                profile,
                memory,
                question=question.question_id,
                exclude_study_uid=uid if excluded else "",
            ),
            "location_status": located.get("status", "unavailable"),
            "regions": located.get("regions", []),
            "query_origins": sorted(_profile_origins(located.get("profile"))),
        }
        scope = _decision_scope(subject, located.get("profile"))
        if scope != "unavailable":
            record["decision_scope"] = scope
        if subject in not_read:
            record["region_not_read_as_subject"] = dict(not_read[subject])
        evidence[subject] = record
    from knee.diagnosis.squint_configurations import configuration_profile

    source_profiles = {
        subject: objects[subject]["profile"]
        for subject in question.objects
        if subject in objects and objects[subject].get("profile") is not None
    }
    # The configuration is composed in the one writer its located objects
    # share; objects written by different writers are never mixed.
    procedures = {
        (profile.get("source") or {}).get("procedure")
        for profile in source_profiles.values()
    }
    if len(procedures) > 1:
        evidence[f"diagnosis/{question.question_id}"] = {
            "outcome": "proposal",
            "reason": "configuration_mixed_procedures",
            "procedures": sorted(str(item) for item in procedures),
            "case_terms": [],
            "censor_terms": [],
            "speaking_calls": [],
        }
        return evidence
    combined = (
        configuration_profile(
            source_profiles, question.question_id, procedure=procedures.pop()
        )
        if procedures
        else configuration_profile(source_profiles, question.question_id)
    )
    if combined["banks"]:
        evidence[combined["subject"]] = recall_object(
            combined,
            memory,
            question=question.question_id,
            exclude_study_uid=uid if excluded else "",
        )
        # A configuration that reads a defining part its input limited to grading
        # may grade, never decide.
        roles = (selection or {}).get("subjects", {}) if selection else {}
        defining = [s for s, r in roles.items() if r in ("defining", "alternative")]
        if any(
            evidence.get(s, {}).get("decision_scope") == "grade_only" for s in defining
        ):
            evidence[combined["subject"]]["decision_scope"] = "grade_only"
    return evidence


def _budget_unexamined_study(
    uid: str, memory: dict, *, reason: str, elapsed_seconds: float = 0.0
) -> dict:
    """Represent a study skipped before pixels as neutral, open evidence."""
    from knee.diagnosis.declarations import QUESTIONS
    from knee.diagnosis.squint_contracts import combine_condition, rank_condition

    questions = {}
    values = {}
    for question in QUESTIONS:
        finding = combine_condition(question.question_id, {})
        ranking = finding.get("rank")
        if not isinstance(ranking, dict):
            ranking = rank_condition(finding)
        value = ranking.get("value")
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not 0.0 < value < 1.0
        ):
            raise SquintRunError(
                "budget_unexamined_ranking_invalid:" + question.question_id
            )
        values[question.question_id] = value
        questions[question.question_id] = {
            "finding": finding,
            "ranking": ranking,
            "objects": {},
        }
    return {
        "schema": "knee.squint-study/v1",
        "readout_policy_id": READOUT_POLICY_ID,
        "study_uid": uid,
        "memory_revision": memory.get("revision", ""),
        "study_status": "not_examined_budget",
        "not_examined_reason": reason,
        "questions": questions,
        "values": values,
        "objects": {},
        "observations": [],
        "work": {
            "elapsed_seconds": elapsed_seconds,
            "full_anatomy_runs": 0,
            "bounded_zoom_runs": 0,
            "squint_stacks": 0,
            "image_reads": 0,
            "source_mode": "raw_squint_case_recall",
        },
        "unresolved_observation_requests": [],
    }


def _region_window(region: dict) -> tuple[int, int, int, int, int, int] | None:
    """The six-integer tile window a located region is addressed by, else None."""
    window = region.get("window", region.get("source_window"))
    if (
        isinstance(window, (list, tuple))
        and len(window) == 6
        and all(type(value) is int for value in window)
    ):
        z0, z1, r0, r1, c0, c1 = window
        return z0, z1, r0, r1, c0, c1
    return None


def _region_address(region: object) -> dict:
    """Where a located region was addressed, as the evidence names it."""
    address = region if isinstance(region, dict) else {}
    window = _region_window(address)
    series_uid = address.get("series_uid")
    return {
        "series_uid": series_uid if isinstance(series_uid, str) else None,
        "window": list(window) if window is not None else None,
    }


def _window_pairing(subject: str, profile: object):
    """Settle a v1 region: its tile window's reading, held at 2 mm or to be refined."""
    from knee.diagnosis.squint_profiles import refine_window
    from knee.diagnosis.squint_residual import FINE_TILE_MM, holds_reading

    def pair(region: dict, by_uid: dict):
        window = _region_window(region)
        if window is None:
            return "unread", "region_window_invalid"
        series = by_uid.get(region.get("series_uid"))
        if series is None:
            return "unread", "series_not_in_study"
        coarse_mm = getattr(series.get("stack"), "tile_mm", None)
        if isinstance(coarse_mm, bool) or not isinstance(coarse_mm, (int, float)):
            return "unread", "series_scale_unavailable"
        if not holds_reading(
            profile,
            series_uid=region["series_uid"],
            window=window,
            scale_mm=float(coarse_mm),
        ):
            return "unread", "coarse_reading_not_held"
        if holds_reading(
            profile,
            series_uid=region["series_uid"],
            window=window,
            scale_mm=FINE_TILE_MM,
        ):
            return "held", None
        return "read", lambda: refine_window(
            series, window, subject=subject, tile_mm=FINE_TILE_MM
        )

    return pair


def _territory_pairing(subject: str, profile: object, study: dict):
    """Settle a territory-v2 region: the finer reading of the 10 mm territory it holds.

    The territory is the region's own record from the locator and the series and leg map
    are the study's. A record the profile holds no reading of is another candidate and is
    not read into it. A record that holds its native mask as an address alone is read
    over the original territory the study kept at location, and only when that
    territory's own serialization is the record (``retained_native_territory``); a mask
    the study does not hold, or holds as another territory, would be read over different
    pixels than its coarse reading. Each is named, never read in its place.
    """
    from knee.diagnosis.squint_anatomy_locator import (
        retained_native_territory,
        territory_from_record,
    )
    from knee.diagnosis.squint_profiles import refine_territory
    from knee.diagnosis.squint_residual import FINE_TILE_MM, held_readings

    held = held_readings(profile)
    leg_maps = study.get("leg_maps")

    def pair(region: dict, by_uid: dict):
        record = region.get("territory")
        if not isinstance(record, Mapping):
            return "unread", "region_without_territory_record"
        series_uid = region.get("series_uid")
        if not isinstance(series_uid, str) or series_uid not in by_uid:
            return "unread", "series_not_in_study"
        series = by_uid[series_uid]

        def identity(**scale) -> list[dict]:
            # The reading identity the territory writer's own call carries: held_readings
            # reads it from a source of that shape, so the lookup is the profile's own.
            source = {
                "procedure": TERRITORY_PROCEDURE,
                "series_context": series.get("source"),
                "territory": record,
                **scale,
            }
            return held_readings({"source": source})

        try:
            territory = territory_from_record(record)
            coarse = identity()
            fine = identity(refinement=True, fine_tile_mm=FINE_TILE_MM)
        except (TypeError, ValueError) as error:
            return "unread", f"territory_record_refused:{error}"
        if not coarse or not fine:
            return "unread", "territory_identity_unavailable"
        if coarse[0] not in held:
            return "unread", "territory_not_held_by_the_profile"
        if fine[0] in held:
            return "held", None
        to_read = territory
        if record.get("native_support_address") is not None:
            # The record holds the mask as an address alone: the original, kept by the
            # location that read it, is the territory to refine, or the reason is named.
            retained, why = retained_native_territory(study, record)
            if retained is None:
                return "unread", why
            to_read = retained
        leg_map = series.get("leg_map")
        if leg_map is None and isinstance(leg_maps, Mapping):
            leg_map = leg_maps.get(series_uid)
        if leg_map is None:
            return "unread", "leg_map_unavailable"
        return "read", lambda: refine_territory(
            series, to_read, leg_map, subject=subject, tile_mm=FINE_TILE_MM
        )

    return pair


def _refine_regions(located: dict, deadline: float | None, by_uid: dict, pair):
    """Make each located region's finer reading once and name every region's outcome.

    ``pair`` settles a region cheaply as ``held`` (already read), ``unread`` (with its
    reason) or ``read`` (a call making the reading). The deadline is checked only before
    a read, so a late study still reports which regions it held or could not read.
    """
    fines: list[dict] = []
    read: list[dict] = []
    held: list[dict] = []
    unavailable: list[dict] = []
    regions = located.get("regions")
    for region in regions if isinstance(regions, list) else ():
        address = _region_address(region)
        if not isinstance(region, dict):
            unavailable.append({**address, "reason": "region_malformed"})
            continue
        verdict, detail = pair(region, by_uid)
        if verdict == "held":
            held.append(address)
        elif verdict == "unread":
            unavailable.append({**address, "reason": detail})
        elif deadline is not None and time.monotonic() >= deadline:
            unavailable.append({**address, "reason": "deadline_before_zoom"})
        else:
            try:
                fine = detail()
            except (TypeError, ValueError) as error:
                reason = f"refinement_refused:{error}"
                unavailable.append({**address, "reason": reason})
                continue
            if isinstance(fine, dict) and fine.get("banks"):
                fines.append(fine)
                read.append(address)
            else:
                unavailable.append({**address, "reason": "refinement_wrote_no_bank"})
    return fines, read, held, unavailable


def _named_procedure(
    request: Mapping,
    lens: str,
    subject: str,
    study: dict,
    objects: dict,
    attempted: set,
    deadline: float | None,
) -> dict:
    """Run the object's own existing native procedure because the request named it.

    Only the object's producer in the residual table can be named. Another lens, or a part
    with no producer, is ``procedure_unavailable`` with its reason, never another reading
    in its place. The step runs once per object and study (``own_outline``) and replaces
    the expected-area reading, which it keeps beside it; its whole answer is the evidence.
    """
    from knee.diagnosis.squint_residual import (
        OWN_OUTLINE_REASON,
        UNAVAILABLE,
        own_outline,
        producer_for,
    )

    producer = producer_for(subject)
    if producer is None:
        reason = UNAVAILABLE.get(subject, "no_existing_bounded_native_producer_named")
        return {
            "code": "procedure_unavailable",
            "subject": subject,
            "lens": lens,
            "reason": reason,
        }
    if lens != producer.lens:
        return {
            "code": "procedure_unavailable",
            "subject": subject,
            "lens": lens,
            "reason": "request_lens_is_not_this_objects_producer",
        }
    if deadline is not None and time.monotonic() >= deadline:
        return {"code": "deadline_before_residual", "subject": subject, "lens": lens}
    record = own_outline(
        subject,
        study,
        objects,
        deadline=deadline,
        question_id=str(request.get("question") or OWN_OUTLINE_REASON),
    )
    if "measured" in (record["code"], record.get("first_code")):
        attempted.add(subject)
    return {
        "code": record["code"],
        "subject": subject,
        "lens": record["lens"],
        "own_outline": record,
    }


def _bounded_observation(
    request: dict,
    study: dict,
    objects: dict,
    attempted: set,
    deadline: float | None,
) -> dict:
    """Make the one bounded reading a request asks for, once per object and study.

    A request that names no procedure asks for the paired finer reading: a reading the
    object holds at 10 mm, read again at 2 mm over the same native region. A territory
    reading is refined over its region's own territory record (``refine_territory``), a
    v1 reading over its tile window (``refine_window``); the two are never mixed. A
    reading the object already holds is neither read nor added again, and every question
    that asks shares the one reading. A ``lens`` naming the object's own native procedure
    runs that existing procedure instead (``_named_procedure``); no part is sent there
    for what it is. Identity never blocks a bounded look. Whatever cannot be read
    returns a named code and reason.
    """
    if not isinstance(request, Mapping):
        return {"code": "request_invalid", "reason": "request_not_a_mapping"}
    subject = request.get("object", request.get("subject"))
    unlocated = {"code": "object_region_unavailable", "request": request}
    if not isinstance(objects, Mapping):
        return {**unlocated, "reason": "objects_not_a_mapping"}
    if not isinstance(study, Mapping):
        return {**unlocated, "reason": "study_not_a_mapping"}
    if not isinstance(subject, str):
        return {**unlocated, "reason": "request_names_no_object"}
    if subject not in objects:
        return {**unlocated, "reason": "object_not_located"}
    located = objects[subject]
    if not isinstance(located, dict):
        return {**unlocated, "reason": "object_record_invalid"}
    if "lens" in request:
        lens = request["lens"]
        if not isinstance(lens, str) or not lens.strip():
            return {
                "code": "request_invalid",
                "subject": subject,
                "reason": "lens_not_a_name",
            }
        if lens != PAIRED_FINER_LENS:
            return _named_procedure(
                request, lens, subject, study, objects, attempted, deadline
            )
    if subject in attempted:
        return {"code": "shared_observation_already_available", "subject": subject}
    if deadline is not None and time.monotonic() >= deadline:
        return {"code": "deadline_before_zoom", "subject": subject}
    own = located.get("own_outline")
    if isinstance(own, Mapping) and own.get("code") == "measured":
        # The part's own outline replaced its expected-area reading, so the regions it
        # was located at no longer describe what its profile holds.
        attempted.add(subject)
        return {
            "code": "already_measured",
            "subject": subject,
            "reason": "own_outline_replaced_the_expected_area_reading",
        }
    from knee.diagnosis.squint_profiles import merge_profiles
    from knee.diagnosis.squint_residual import FINE_TILE_MM

    previous = located.get("profile")
    regions = located.get("regions")
    source = previous.get("source") if isinstance(previous, dict) else None
    territory_reading = (
        isinstance(source, dict) and source.get("procedure") == TERRITORY_PROCEDURE
    ) or any(
        isinstance(region, dict) and isinstance(region.get("territory"), Mapping)
        for region in (regions if isinstance(regions, list) else ())
    )
    by_uid = {
        s["series_uid"]: s
        for s in study.get("series", ())
        if isinstance(s, dict) and "series_uid" in s
    }
    pair = (
        _territory_pairing(subject, previous, study)
        if territory_reading
        else _window_pairing(subject, previous)
    )
    fines, read, held, unavailable = _refine_regions(located, deadline, by_uid, pair)
    outcome = {
        "subject": subject,
        "held_regions": held,
        "unavailable_regions": unavailable,
    }
    if not fines:
        if held:
            attempted.add(subject)
            code, reason = "already_measured", "paired_reading_already_held"
        elif any(item["reason"] == "deadline_before_zoom" for item in unavailable):
            code, reason = "deadline_before_zoom", "deadline_reached_before_the_read"
        else:
            code = "no_compatible_bounded_reading"
            reason = (
                "no_located_region"
                if not unavailable
                else "territory_unavailable"
                if territory_reading
                else "region_unavailable"
            )
        return {"code": code, "reason": reason, **outcome}
    try:
        merged = merge_profiles(
            [previous, *fines] if previous is not None else fines, subject=subject
        )
    except (TypeError, ValueError) as error:
        reason = f"profile_merge_refused:{error}"
        return {"code": "no_compatible_bounded_reading", "reason": reason, **outcome}
    located["profile"] = merged
    attempted.add(subject)
    return {
        "code": "measured",
        "regions": read,
        "lens": PAIRED_FINER_LENS,
        "tile_mm": FINE_TILE_MM,
        "procedure": merged["source"]["procedure"],
        **outcome,
    }


def _squint_first_location(locate) -> dict:
    """The production locator's option: the 2 mm reading waits for a named question.

    Offered only to a locator that declares it. The teacher control substitutes a locator
    that reads its own pairs upfront, and its signature predates the keyword.
    """
    try:
        declared = "refine_finalists" in inspect.signature(locate).parameters
    except (TypeError, ValueError):
        declared = False
    return {"refine_finalists": False} if declared else {}


def _fine_readings_held(objects: object) -> int:
    """How many 2 mm readings the located objects' profiles hold."""
    from knee.diagnosis.squint_residual import FINE_TILE_MM, held_readings

    return sum(
        reading.get("scale_mm") == FINE_TILE_MM
        for located in (objects.values() if isinstance(objects, Mapping) else ())
        if isinstance(located, Mapping)
        for reading in held_readings(located.get("profile"))
    )


# The locator's own evidence vocabulary (``squint_anatomy_locator``): how it placed each
# object. A bone read from its structural anchor names both; a dependent placed by the
# anatomy map from the established anchors names the relation route, and each of its
# territories the origin that placed it.
_ANCHOR_SOURCE = "current_study_structural_anchor"
_ANCHOR_ROUTE = "structural_anchor"
_RELATION_ROUTE = "anatomical_relation_from_structural_anchors"
_EXISTING_ROUTE = "existing_finite_route"
_RELATION_ORIGIN = "anatomical_relation"
_FALLBACK_ORIGIN = "fallback_location"
_ANCHOR_CONFLICT = "anatomical_relation_conflict"
#: Territory origins (``squint_interfaces.TERRITORY_ORIGINS``) by what the region is: a
#: support the structure resolved, or places an expectation proposed and nothing measured.
_RESOLVED_ORIGINS = frozenset({"anchor_structure", *MEASURED_ORIGINS})
_PROPOSAL_ORIGINS = frozenset({_RELATION_ORIGIN, _FALLBACK_ORIGIN})
#: The reader's own record of the arrangement it named a bone by (``squint_anchors``: each
#: territory's provenance carries the established rule, its code and the views it was read
#: against).
_ARRANGEMENT_FIELDS = ("derivation", "rule", "middle_slice_code", "partner", "scale")


def _six_ints(value: object) -> tuple[int, int, int, int, int, int] | None:
    if (
        isinstance(value, (list, tuple))
        and len(value) == 6
        and all(type(item) is int for item in value)
    ):
        z0, z1, r0, r1, c0, c1 = value
        return z0, z1, r0, r1, c0, c1
    return None


def _boxes_overlap(left: tuple[int, ...], right: tuple[int, ...]) -> bool:
    """Whether two half-open tile windows of one series share a tile."""
    return all(
        left[2 * axis] < right[2 * axis + 1] and right[2 * axis] < left[2 * axis + 1]
        for axis in range(3)
    )


def _is_located(located: Mapping) -> bool:
    regions = located.get("regions")
    profile = located.get("profile")
    return (isinstance(regions, list) and bool(regions)) or (
        isinstance(profile, Mapping) and bool(profile.get("banks"))
    )


def _readings_of(located: Mapping) -> list[dict]:
    """Each located region's series, object window and the territory it was read over."""
    regions = located.get("regions")
    territories = located.get("territories")
    territories = territories if isinstance(territories, list) else []
    rows = []
    for index, region in enumerate(regions if isinstance(regions, list) else ()):
        if not isinstance(region, Mapping):
            continue
        window = _region_window(region)
        uid = region.get("series_uid")
        if window is None or not isinstance(uid, str) or not uid:
            continue
        territory = (
            territories[index] if index < len(territories) else region.get("territory")
        )
        rows.append(
            {
                "series_uid": uid,
                "window": list(window),
                "territory": territory if isinstance(territory, Mapping) else {},
            }
        )
    return rows


def _identity_basis(located: Mapping, readings: list[dict]) -> tuple[str, str]:
    """What placed one object, by the locator's own record, and why that basis.

    A located region placed by the anatomy map from the established anchors makes the
    object ``MAP_RELATION`` even when another of its regions came from the leg-frame seed
    alone; each region keeps its own origin in the supporting observations.
    """
    evidence = located.get("evidence")
    evidence = evidence if isinstance(evidence, Mapping) else {}
    route = evidence.get("location_route")
    if route == _ANCHOR_ROUTE and evidence.get("source") == _ANCHOR_SOURCE:
        return STRUCTURAL_READER, "located_by_its_structural_anchor"
    if route == _RELATION_ROUTE:
        origins = {row["territory"].get("origin") for row in readings}
        if _RELATION_ORIGIN in origins:
            return MAP_RELATION, "placed_from_established_structural_anchors"
        if _FALLBACK_ORIGIN in origins:
            return PRIOR_ONLY, "leg_frame_prior_only"
        return PRIOR_ONLY, "no_relation_territory_recorded"
    if route == _EXISTING_ROUTE:
        return PRIOR_ONLY, "no_usable_structural_anchor"
    return PRIOR_ONLY, "no_structural_placement_recorded"


def _reversed_checks(sanity: object, subject: str, scope: str) -> list[dict]:
    """Every recorded ``reversed_*`` law check of ``subject``, with its rule and intervals."""
    if not isinstance(sanity, Mapping):
        return []
    rows = []
    windows = sanity.get("windows")
    for window_row in windows if isinstance(windows, list) else ():
        if not isinstance(window_row, Mapping):
            continue
        checks = window_row.get("checks")
        for check in checks if isinstance(checks, list) else ():
            if (
                not isinstance(check, Mapping)
                or check.get("candidate_subject", subject) != subject
            ):
                continue
            result = check.get("result")
            if isinstance(result, str) and result.startswith("reversed_"):
                rows.append(
                    {
                        "scope": scope,
                        "rule_id": check.get("rule_id"),
                        "relation": check.get("relation"),
                        "axis": check.get("axis"),
                        "result": result,
                        "expected_relation": check.get("expected_relation"),
                        "candidate_interval": copy.deepcopy(
                            check.get("candidate_interval")
                        ),
                        "target_interval": copy.deepcopy(check.get("target_interval")),
                        "reference_subject": check.get("reference_subject"),
                        "series_uid": window_row.get("series_uid"),
                        "window": copy.deepcopy(window_row.get("window")),
                    }
                )
    return rows


def _contradictions(subject: str, located: Mapping) -> list[dict]:
    """Genuine contradictory observations about this object from its law checks.

    Its located windows' reversed checks and, for a bone whose own structural anchor was
    set aside for a reversed relation, that anchor's. Unknown and overlap are neither.
    """
    rows = _reversed_checks(located.get("sanity"), subject, "located_windows")
    evidence = located.get("evidence")
    unanchored = (
        evidence.get("unanchored_bone") if isinstance(evidence, Mapping) else None
    )
    if isinstance(unanchored, Mapping) and unanchored.get("code") == _ANCHOR_CONFLICT:
        rows.extend(
            _reversed_checks(
                unanchored.get("anatomical_sanity"),
                subject,
                "set_aside_structural_anchor",
            )
        )
    return rows


def _locator_proposals(objects: Mapping) -> dict[str, dict[str, list]]:
    """Each object's own candidate windows from this study's locator, by series.

    A window whose own law checks the locator recorded as contradicted is kept apart:
    known structure has already ruled that object out there.
    """
    proposals: dict[str, dict[str, list]] = {}
    for subject, located in objects.items():
        evidence = located.get("evidence") if isinstance(located, Mapping) else None
        territories = (
            evidence.get("candidate_territories")
            if isinstance(evidence, Mapping)
            else None
        )
        if not isinstance(subject, str) or not isinstance(territories, Mapping):
            continue
        ruled_out = set()
        checks = evidence.get("anatomical_sanity_checks")
        for row in checks if isinstance(checks, list) else ():
            if isinstance(row, Mapping) and row.get("status") == "contradicted":
                window = _six_ints(row.get("window"))
                if window is not None and isinstance(row.get("series_uid"), str):
                    ruled_out.add((row["series_uid"], window))
        found: dict[str, list] = {"eligible": [], "contradicted": []}
        for uid, row in territories.items():
            windows = (
                row.get("candidate_object_windows")
                if isinstance(row, Mapping)
                else None
            )
            for raw in windows if isinstance(windows, list) else ():
                window = _six_ints(raw)
                if window is not None:
                    key = (str(uid), window)
                    found["contradicted" if key in ruled_out else "eligible"].append(
                        key
                    )
        proposals[subject] = found
    return proposals


def _open_alternatives(
    subject: str,
    readings: list[dict],
    proposals: Mapping[str, Mapping[str, list]],
    established: set[str],
) -> dict:
    """What the established structure still leaves possible for the located region.

    The other objects whose own candidate windows from this study's locator overlap a
    located window in the same series. A bone the structural reader established is no
    alternative name for a window beside it; an object whose only overlapping windows its
    own law checks contradicted is ruled out by that structure, and named apart.
    """
    open_names: set[str] = set()
    law_names: set[str] = set()
    overlaps: list[dict] = []
    law_overlaps: list[dict] = []
    for reading in readings:
        uid, window = reading["series_uid"], tuple(reading["window"])
        for other in sorted(proposals):
            if other == subject or other in established:
                continue
            counts = {
                kind: sum(
                    1
                    for series_uid, candidate in proposals[other][kind]
                    if series_uid == uid and _boxes_overlap(window, candidate)
                )
                for kind in ("eligible", "contradicted")
            }
            address = {
                "subject": other,
                "series_uid": uid,
                "region_window": list(window),
            }
            if counts["eligible"]:
                open_names.add(other)
                overlaps.append(
                    {**address, "overlapping_candidate_windows": counts["eligible"]}
                )
            if counts["contradicted"]:
                law_names.add(other)
                law_overlaps.append(
                    {
                        **address,
                        "law_contradicted_candidate_windows": counts["contradicted"],
                    }
                )
    return {
        "open_alternatives": sorted(open_names),
        "alternative_overlaps": overlaps,
        "law_excluded_alternatives": sorted(law_names - open_names),
        "law_excluded_overlaps": law_overlaps,
    }


def _support_kind(readings: list[dict]) -> str:
    """What the located region is, by the origin of every territory it was read over."""
    origins = {row["territory"].get("origin") for row in readings}
    if readings and origins <= _RESOLVED_ORIGINS:
        return RESOLVED_SUPPORT
    if readings and origins <= _PROPOSAL_ORIGINS:
        return PROPOSED_PLACES
    return SUPPORT_UNRECORDED


def _arrangement(readings: list[dict]) -> list[dict]:
    """The structural reader's own record of how it named the bone, per territory read.

    The established rule (``assign_plane``: the upper and lower of the two deepest
    interiors along the leg; the patella in front of the femur's lower end; the fibula's
    own rule), its code, the partner sequence's agreement and the cross-view checks,
    exactly as the territory's provenance holds them. Nothing is recomputed.
    """
    rows = []
    for row in readings:
        territory = row["territory"]
        provenance = territory.get("provenance")
        provenance = provenance if isinstance(provenance, Mapping) else {}
        if territory.get("origin") != "anchor_structure" or not isinstance(
            provenance.get("derivation"), str
        ):
            continue
        checks = provenance.get("cross_view_checks")
        rows.append(
            {
                "establishes": "bone_identity_by_the_readers_observed_arrangement",
                "series_uid": row["series_uid"],
                "window": row["window"],
                "producer": provenance.get("producer"),
                **{
                    key: copy.deepcopy(provenance[key])
                    for key in _ARRANGEMENT_FIELDS
                    if key in provenance
                },
                "cross_view_checks": [
                    {
                        key: check.get(key)
                        for key in ("against_series_uid", "against_slice", "outcome")
                    }
                    for check in (checks if isinstance(checks, list) else ())
                    if isinstance(check, Mapping)
                ],
            }
        )
    return rows


def _placing_anchors(territory: Mapping) -> list[dict]:
    rows = territory.get("anchors")
    found: list[dict] = []
    for row in rows if isinstance(rows, list) else ():
        if not isinstance(row, Mapping):
            continue
        item = {
            key: row[key]
            for key in ("anchor", "kind", "anchor_observation_status", "prior_only")
            if key in row
        }
        if item and item not in found:
            found.append(item)
    return found


def _supporting_observations(
    subject: str, located: Mapping, basis: str, reason: str, readings: list[dict]
) -> dict:
    """References to the locator records the basis rests on, never a recomputation."""
    evidence = located.get("evidence")
    evidence = evidence if isinstance(evidence, Mapping) else {}
    sanity = located.get("sanity")
    observations = {
        "reason": reason,
        "location_status": located.get("status"),
        "location_route": evidence.get("location_route"),
        "sanity_status": sanity.get("status") if isinstance(sanity, Mapping) else None,
        "regions": [
            {
                "series_uid": row["series_uid"],
                "window": row["window"],
                "origin": row["territory"].get("origin"),
            }
            for row in readings
        ],
    }
    if basis == STRUCTURAL_READER:
        anchor = evidence.get("anchor")
        anchor = anchor if isinstance(anchor, Mapping) else {}
        resolution = anchor.get("view_resolution")
        observations.update(
            record=f"objects/{subject}/evidence/anchor",
            anchor={
                "status": anchor.get("status"),
                "code": anchor.get("code"),
                "producer": anchor.get("producer"),
                "key_planes": copy.deepcopy(anchor.get("key_planes")),
                "view_resolution": resolution.get("code")
                if isinstance(resolution, Mapping)
                else None,
            },
            reading_territories=evidence.get("reading_territories"),
            arrangement=_arrangement(readings),
        )
    elif basis == MAP_RELATION:
        observations.update(
            record=f"objects/{subject}/territories",
            placed_by=[
                {
                    "series_uid": row["series_uid"],
                    "window": row["window"],
                    "anchors": _placing_anchors(row["territory"]),
                    "relation": row["territory"]["relation"].get("kind")
                    if isinstance(row["territory"].get("relation"), Mapping)
                    else None,
                }
                for row in readings
            ],
        )
    else:
        observations["record"] = f"objects/{subject}/evidence"
    return observations


def _identity_contexts(objects: object) -> dict[str, dict]:
    """What the current study's own structure already established about each object.

    Read from the locator's records, by reference, once per located object: the basis
    (the structural reader, the anatomy map from the established anchors, or the prior
    alone); what the region is by its territories' origin (a resolved support or
    proposed places); which identities structure removed (for a bone the reader
    established, every other bone of its own set, which it tells apart by arrangement,
    found or not; for a placement, the bones it established here); what that leaves open;
    and any genuine contradictory law observation. Recognition is never repeated to make
    it. An object the locator did not locate has no context.
    """
    if not isinstance(objects, Mapping):
        return {}
    placed: dict[str, tuple[str, str, list[dict]]] = {}
    for subject, located in objects.items():
        if (
            isinstance(subject, str)
            and isinstance(located, Mapping)
            and _is_located(located)
        ):
            readings = _readings_of(located)
            placed[subject] = (*_identity_basis(located, readings), readings)
    established = {
        subject
        for subject, (basis, _r, _x) in placed.items()
        if basis == STRUCTURAL_READER
    }
    proposals = _locator_proposals(objects)
    contexts = {}
    for subject in sorted(placed):
        basis, reason, readings = placed[subject]
        if basis == STRUCTURAL_READER:
            removed = set(READER_BONES) - {subject}
        elif basis == MAP_RELATION:
            removed = established - {subject}
        else:
            removed = set()
        context = {
            "schema": CONTEXT_SCHEMA,
            "subject": subject,
            "basis": basis,
            "conditioning": CONDITIONING[basis],
            "support": _support_kind(readings),
            "open_alternatives": [],
            "removed_by_structure": sorted(removed),
            "contradictions": _contradictions(subject, objects[subject]),
            "supporting_observations": _supporting_observations(
                subject, objects[subject], basis, reason, readings
            ),
        }
        if basis == MAP_RELATION:
            context.update(
                _open_alternatives(subject, readings, proposals, established)
            )
        contexts[subject] = context
    return contexts


def _identity_readings(
    objects: dict,
    memory: dict,
    excluded_uid: str | None,
    *,
    prepared_identity: Mapping | None = None,
    contexts: Mapping[str, Mapping] | None = None,
) -> dict:
    """Hear called identity seeds once per study view, independently of diagnosis.

    An automatic catalogue is not identity teaching. Missing profiles remain unread;
    neither a proposed anatomical name nor a plausible location supplies a class. Each
    object's recall is conditioned on its ``contexts`` entry, what the structure already
    established about it; one with none is heard unconditioned. This operation returns
    evidence only: it never publishes a case or a diagnosis.
    """
    if "object_identity_teaching" not in memory:
        return {"outcome": "unreviewed_candidate_memory", "objects": {}}
    from knee.diagnosis.squint_identity import prepare_identity, recall_identity

    prepared = (
        prepared_identity
        if prepared_identity is not None
        else prepare_identity(memory, exclude_study_uid=excluded_uid)
    )
    if prepared.get("outcome") != "prepared":
        return {
            "outcome": "invalid_seed_teaching",
            "preparation": dict(prepared),
            "objects": {},
        }
    known = contexts if isinstance(contexts, Mapping) else {}
    readings = {}
    for subject, located in sorted(objects.items()):
        profile = located.get("profile")
        readings[subject] = (
            recall_identity(
                profile,
                memory,
                exclude_study_uid=excluded_uid,
                sanity=located.get("sanity"),
                prepared=prepared,
                context=known.get(subject),
            )
            if profile is not None
            else {"outcome": "unresolved_missing_reading", "identity": None}
        )
    return {
        "schema": "knee.study-object-identity/v1",
        "outcome": "examined",
        "preparation": dict(prepared),
        "objects": readings,
        "memory_published": False,
    }


def _identity_open_question(
    subject: str,
    context: Mapping | None,
    reading: Mapping | None,
    effect: str,
    contest: Mapping | None = None,
    holds_fine: bool = False,
) -> dict | None:
    """The bounded next observation that could settle an identity left open.

    Contested at its deciding scale (an applicable negative case speaks), a squint-scale
    contest the finer reading has not settled, or a placement or prior whose own cases
    do not support it: the existing residual paths that remain are named. The paired
    finer reading of the located regions (``refine_territory`` or ``refine_window`` at
    2 mm, ``_bounded_observation``'s default) is named only while no finer reading is
    held, so nothing is read twice; where the part has one, its own native producer
    (``squint_residual.own_outline``) is named too. Naming them runs nothing: the
    consumer decides within its budget. A squint-scale contest's finer look, which
    ``infer_study`` makes itself, is recorded as ``finer_look``. A bone the reader
    established, uncontested, asks none.
    """
    if context is None or reading is None:
        return None
    pending = contest is not None and contest["status"] not in (
        RESOLVED_BY_FINER_READING,
        CONTESTED_AFTER_FINER_READING,
    )
    unconfirmed = context["basis"] != STRUCTURAL_READER and reading.get(
        "appearance"
    ) in ("silent", "uncalibrated")
    if effect == "answers" and not pending and not unconfirmed:
        return None
    from knee.diagnosis.squint_residual import FINE_TILE_MM, producer_for

    if effect in CONTESTED_OUTCOMES:
        why = "contested"
    elif pending:
        why = CONTESTED_AT_SQUINT_SCALE
    else:
        why = "appearance_unconfirmed"
    observations = []
    if not holds_fine:
        observations.append(
            {
                "request": {"object": subject, "question": "identity", "reason": why},
                "procedure": "paired_finer_reading",
                "reads": f"the located regions at {FINE_TILE_MM:g} mm: refine_territory "
                "over a territory reading, refine_window over a tile window",
            }
        )
    producer = producer_for(subject)
    if producer is not None:
        observations.append(
            {
                "request": {
                    "object": subject,
                    "lens": producer.lens,
                    "question": "identity",
                    "reason": why,
                },
                "procedure": "residual_native_support",
                "reads": producer.definition,
            }
        )
    question = {
        "status": "open",
        "why": why,
        "support": context.get("support"),
        "next_observations": observations,
        "run": "left_to_the_consumer_within_budget",
    }
    if contest is not None:
        question["finer_look"] = copy.deepcopy(contest.get("finer_look"))
    return question


def _look_summary(look: object) -> dict | None:
    """The finer look a squint-scale contest earned: its code and what it read."""
    if not isinstance(look, Mapping):
        return None
    return {
        "code": look.get("code"),
        "reason": look.get("reason"),
        "lens": look.get("lens"),
        "regions_read": len(look.get("regions") or ()),
    }


def _object_consumption(
    subject: str,
    reading: object,
    examined: object,
    context: object,
    contest_state: Mapping | None = None,
    holds_fine: bool = False,
) -> dict:
    """How one object's identity in context reaches its condition questions.

    The object answers its own questions as the object identified in context unless an
    applicable negative case speaks over its asserted region in the comparison that
    decides: then the region is not read as that object (``appearance_opposed``, or a
    ``signed_conflict`` with its own cases), its questions stay open, and nothing renames
    it. A negative speaking at the squint scale opens the question and does not decide
    it: the joint recall after the finer look in ``contest_state`` does
    (``squint_contest_resolution``). Settled there, the object answers. Opposed there,
    the region is not read. When its own cases and a negative both still speak, the
    question returns to the structure's own word (thesis §11.2): a bone the structural
    reader named stands, the disagreement kept as a finding, and a placement or prior,
    with no concurring family, stays open. Not yet settled, a reader's bone stands, its
    question recorded, and a placement or prior is ``contested_at_squint_scale``, its
    questions left open. A contest is never broken by which side resembles more. A
    genuine contradictory law observation is a revisable ``identity_question``.
    """
    if examined != "examined":
        outcome = examined if isinstance(examined, str) and examined else None
        outcome = outcome or "identity_recall_unavailable"
    elif not isinstance(reading, Mapping):
        outcome = "identity_reading_missing"
    else:
        outcome = reading.get("outcome")
        outcome = (
            outcome
            if isinstance(outcome, str) and outcome
            else "identity_outcome_invalid"
        )
    context = context if isinstance(context, Mapping) else None
    heard = reading if examined == "examined" and isinstance(reading, Mapping) else None
    deciding, scale, effect, contest = heard, SQUINT_SCALE, "answers", None
    standing = False
    if heard is not None and outcome in CONTESTED_OUTCOMES:
        state = contest_state if isinstance(contest_state, Mapping) else {}
        resolution = state.get("resolution") or squint_contest_resolution(heard, None)
        resolved = state.get("resolved")
        structural = context is not None and context["basis"] == STRUCTURAL_READER
        finding = None
        if resolution["status"] == CONTESTED_AFTER_FINER_READING:
            deciding, scale = resolved, JOINT_SCALE
            if resolved["outcome"] == SIGNED_CONFLICT and structural:
                # Both voices still reach: the structure's own word stands.
                standing = True
                finding = "disagreement_kept_structural_identity_stands"
            else:
                effect = resolved["outcome"]
        elif resolution["status"] == RESOLVED_BY_FINER_READING:
            deciding, scale = resolved, JOINT_SCALE
        elif structural:
            standing = True
        else:
            effect = CONTESTED_AT_SQUINT_SCALE
        contest = {
            "finer_look": _look_summary(state.get("look")),
            **resolution,
            "finding": finding,
        }
    if effect in CONTESTED_OUTCOMES:
        applicable = list(deciding.get("applicable_negative_case_ids", ()))
    elif effect == CONTESTED_AT_SQUINT_SCALE:
        applicable = list(heard.get("applicable_negative_case_ids", ()))
    else:
        applicable = []
    contradictions = list(context["contradictions"]) if context is not None else []
    entry = {
        "answers_questions_as": subject if effect == "answers" else None,
        "region_read_as_subject": effect == "answers",
        "identity_effect": effect,
        "identity_basis": context["basis"] if context is not None else None,
        "identity_scale": scale if heard is not None else None,
        "identity_state": "established"
        if standing
        else deciding.get("identity_state")
        if deciding is not None
        else None,
        "support": context.get("support") if context is not None else None,
        "recall_outcome": outcome,
        "applicable_negative_case_ids": applicable,
        "squint_scale_contest": contest,
        "identity_context": copy.deepcopy(context),
        "identity_question": None,
        "identity_open_question": _identity_open_question(
            subject, context, deciding, effect, contest, holds_fine
        ),
    }
    if contradictions:
        entry["identity_question"] = {
            "status": "open",
            "kind": "reversed_anatomical_relation",
            "revisable": True,
            "evidence": copy.deepcopy(contradictions),
        }
    return entry


def _identity_consumption(
    objects: object,
    identity_readings: object,
    contexts: object = None,
    contests: object = None,
) -> dict:
    """Each located object's identity in context, as condition reasoning consumes it.

    Resemblance to another object never keeps a region from its own questions; an
    applicable negative case at the deciding scale does (``_object_consumption``), and
    ``contests`` holds the finer recall of each squint-scale contest
    (``_resolve_identity_contests``). ``not_read_as_subject`` names those regions;
    bounded looks are never refused for identity.
    """
    record: dict = {
        "schema": IDENTITY_CONSUMPTION_SCHEMA,
        "not_read_as_subject": [],
        "objects": {},
    }
    if not isinstance(objects, Mapping):
        return record
    examined = readings = None
    if isinstance(identity_readings, Mapping):
        examined = identity_readings.get("outcome")
        readings = identity_readings.get("objects")
    if not isinstance(readings, Mapping):
        readings = {}
    known = contexts if isinstance(contexts, Mapping) else {}
    states = contests if isinstance(contests, Mapping) else {}
    record["objects"] = {
        subject: _object_consumption(
            subject,
            readings.get(subject),
            examined,
            known.get(subject),
            states.get(subject),
            holds_scale(
                objects[subject].get("profile")
                if isinstance(objects[subject], Mapping)
                else None,
                FINE_SCALE,
            ),
        )
        for subject in sorted(objects)
    }
    record["not_read_as_subject"] = [
        subject
        for subject, entry in record["objects"].items()
        if not entry["region_read_as_subject"]
    ]
    return record


def _regions_not_read(consumption: Mapping) -> dict[str, dict]:
    """The regions not read as their object, each with the reason its evidence carries."""
    objects = consumption.get("objects") if isinstance(consumption, Mapping) else None
    return {
        subject: {
            "reason": entry["identity_effect"],
            "applicable_negative_case_ids": list(entry["applicable_negative_case_ids"]),
        }
        for subject, entry in (objects.items() if isinstance(objects, Mapping) else ())
        if not entry["region_read_as_subject"]
    }


def _resolve_identity_contests(
    objects: dict,
    study: dict,
    memory: dict,
    excluded_uid: str | None,
    identity_readings: dict,
    contexts: Mapping | None,
    attempted: set,
    observations: list,
    deadline: float | None,
    prepared_resolved: Mapping | None = None,
) -> dict[str, dict]:
    """Settle each squint-scale identity contest with the object's own finer reading.

    A located object whose squint-scale recall in context has an applicable negative
    case (``CONTESTED_OUTCOMES``) has an open identity question, not a decided one: at
    10 mm a support's object tiles still mix the object with its surroundings. It earns
    the existing bounded finer look of its own region (``_bounded_observation``'s paired
    finer reading at the same address), shared with every later question through
    ``attempted`` and ``observations``, so nothing is read twice. An object that then
    holds a finer reading of its own tiles is recalled again as one comparison over
    every bank both sides speak in at both scales (``JOINT_SCALE``), under the same
    context and rules, against a joint view prepared once (``prepared_resolved``, else
    from this ``memory`` and exclusion); how its contest stands is
    ``squint_contest_resolution``. Returns, per contested object, its look, its joint
    recall (None without a finer reading) and the resolution, and records the joint
    recalls in ``identity_readings["resolved_scale"]``. With no contest, nothing is read
    and nothing is recorded.
    """
    from knee.diagnosis.squint_identity import prepare_identity, recall_identity
    from knee.diagnosis.squint_procedure_memory import (
        _recall_entry,
        select_observation_requests,
    )

    if identity_readings.get("outcome") != "examined":
        return {}
    readings = identity_readings.get("objects")
    readings = readings if isinstance(readings, Mapping) else {}
    contested = sorted(
        subject
        for subject, reading in readings.items()
        if isinstance(reading, Mapping)
        and reading.get("schema") == RECALL_CONTEXT_SCHEMA
        and reading.get("outcome") in CONTESTED_OUTCOMES
        and isinstance(objects.get(subject), dict)
    )
    if not contested:
        return {}
    known = contexts if isinstance(contexts, Mapping) else {}
    prepared = prepared_resolved
    finer: dict[str, dict] = {}
    states: dict[str, dict] = {}
    requests = [
        {
            "object": subject,
            "question": "identity",
            "reason": CONTESTED_AT_SQUINT_SCALE,
            "kind": "bounded_zoom",
            "scope": "object_window",
            "request_id": f"identity:{subject}:{CONTESTED_AT_SQUINT_SCALE}",
        }
        for subject in contested
    ]
    requests = select_observation_requests(
        requests,
        memory,
        objects=objects,
        study_uid=excluded_uid or str(study.get("study_uid", "")),
        exclude_same_study=excluded_uid is not None,
    )
    for request in requests:
        subject = request["object"]
        located = objects[subject]
        before_state = _recall_entry(readings[subject])
        before_cue = _subject_cue_snapshot(located)
        look = _bounded_observation(request, study, objects, attempted, deadline)
        resolved = None
        if holds_scale(located.get("profile"), FINE_SCALE):
            if prepared is None:
                prepared = prepare_identity(
                    memory, exclude_study_uid=excluded_uid, scale=JOINT_SCALE
                )
            resolved = recall_identity(
                located["profile"],
                memory,
                exclude_study_uid=excluded_uid,
                sanity=located.get("sanity"),
                prepared=prepared,
                context=known.get(subject),
                scale=JOINT_SCALE,
                resolve_negatives=readings[subject].get(
                    "applicable_negative_case_ids", ()
                ),
            )
            finer[subject] = resolved
        states[subject] = {
            "look": look,
            "resolved": resolved,
            "resolution": squint_contest_resolution(readings[subject], resolved),
        }
        observation = {
            **look,
            "requested_by": "identity_question",
            "question": "identity",
            "request_id": request["request_id"],
            "request_kind": "bounded_zoom",
            "request_reason": CONTESTED_AT_SQUINT_SCALE,
            "request_scope": "object_window",
            "attribution_scope": "single_procedure",
            "before_state": before_state,
            "after_state": _recall_entry(resolved),
            "after_identity_consumption": _object_consumption(
                subject,
                readings[subject],
                "examined",
                known.get(subject),
                states[subject],
                holds_scale(located.get("profile"), FINE_SCALE),
            ),
        }
        if before_cue is not None:
            observation["before_cue"] = before_cue
        if "recalled_procedure" in request:
            observation["recalled_procedure"] = request["recalled_procedure"]
        observations.append(observation)
    identity_readings["resolved_scale"] = {
        "scale": JOINT_SCALE,
        "contested_at_squint_scale": contested,
        "preparation": dict(prepared) if isinstance(prepared, Mapping) else None,
        "objects": finer,
    }
    return states


def _refresh_identity_after_observations(
    objects: dict,
    study: dict,
    memory: dict,
    excluded_uid: str | None,
    previous_profiles: Mapping,
    contexts: dict,
    identity_readings: dict,
    contests: dict,
    attempted: set,
    observations: list,
    deadline: float | None,
    prepared_identity: Mapping | None,
    prepared_resolved: Mapping | None,
) -> Mapping | None:
    """Hear changed observations in their current anatomical context before diagnosis.

    The request consumer only locates or writes. This coordinator shares the same
    identity preparation and the same finer-look mechanism as the initial pass.
    Unchanged profiles in unchanged contexts are not compared again. Prior joint
    evidence for unaffected objects remains present in the final study record.
    """
    next_contexts = _identity_contexts(objects)
    changed = {
        subject: located
        for subject, located in objects.items()
        if isinstance(located, Mapping)
        and (
            previous_profiles.get(subject) is not located.get("profile")
            or contexts.get(subject) != next_contexts.get(subject)
        )
    }
    if not changed:
        return prepared_resolved
    heard = _identity_readings(
        changed,
        memory,
        excluded_uid,
        prepared_identity=prepared_identity,
        contexts=next_contexts,
    )
    if prepared_resolved is None and any(
        isinstance(row, Mapping) and row.get("outcome") in CONTESTED_OUTCOMES
        for row in heard.get("objects", {}).values()
    ):
        from knee.diagnosis.squint_identity import prepare_identity

        prepared_resolved = prepare_identity(
            memory, exclude_study_uid=excluded_uid, scale=JOINT_SCALE
        )
    updated_contests = _resolve_identity_contests(
        changed,
        study,
        memory,
        excluded_uid,
        heard,
        next_contexts,
        attempted,
        observations,
        deadline,
        prepared_resolved,
    )
    for subject in changed:
        contests.pop(subject, None)
    contests.update(updated_contests)
    contexts.clear()
    contexts.update(next_contexts)
    identity_readings.setdefault("objects", {}).update(heard.get("objects", {}))
    previous_joint = identity_readings.get("resolved_scale")
    previous_joint = previous_joint if isinstance(previous_joint, Mapping) else {}
    joint_objects = {
        subject: reading
        for subject, reading in previous_joint.get("objects", {}).items()
        if subject not in changed
    }
    next_joint = heard.get("resolved_scale")
    next_joint = next_joint if isinstance(next_joint, Mapping) else {}
    joint_objects.update(next_joint.get("objects", {}))
    if previous_joint or next_joint:
        identity_readings["resolved_scale"] = {
            **previous_joint,
            **next_joint,
            "objects": joint_objects,
            "contested_at_squint_scale": sorted(contests),
        }
    return prepared_resolved


def _condition_state_snapshot(
    finding: Mapping[str, Any], subject: object
) -> dict[str, Any]:
    """Snapshot a condition finding before or after an observation request runs."""
    evidence = finding.get("evidence")
    readings = evidence.get("readings") if isinstance(evidence, Mapping) else None
    reading = readings.get(subject) if isinstance(readings, Mapping) else None
    rank = finding.get("rank")
    subject_reading = None
    if isinstance(reading, Mapping):
        speaking = reading.get("speaking_case_ids")
        subject_reading = {
            "role": reading.get("role"),
            "state": reading.get("state"),
            "code": reading.get("code"),
            "recall_outcomes": list(reading.get("recall_outcomes") or ()),
            "trust_checked": reading.get("trust_checked"),
            "speaking_cases": len(speaking)
            if isinstance(speaking, (list, tuple))
            else 0,
        }
    return {
        "outcome": finding.get("outcome"),
        "reason": finding.get("reason"),
        "value": rank.get("value")
        if isinstance(rank, Mapping)
        else finding.get("probability"),
        "tier": rank.get("tier") if isinstance(rank, Mapping) else None,
        "subject_reading": subject_reading,
        "requests_listed": [
            f"{r.get('subject')}:{r.get('reason')}"
            for r in (finding.get("observation_requests") or ())
            if isinstance(r, Mapping)
        ],
    }


def _subject_cue_snapshot(located: object) -> dict[str, Any] | None:
    """Snapshot an object's coarse 10 mm HDC banks and location status before an action."""
    if not isinstance(located, Mapping):
        return None

    profile = located.get("profile")
    if not isinstance(profile, Mapping):
        banks = {}
        procedure = None
    else:
        raw_banks = profile.get("banks")
        banks = (
            {
                k: list(v)
                for k, v in raw_banks.items()
                if isinstance(k, str) and k.rsplit("/scale=", 1)[-1] == "10mm"
            }
            if isinstance(raw_banks, Mapping)
            else {}
        )
        if not banks and isinstance(raw_banks, Mapping):
            banks = {k: list(v) for k, v in raw_banks.items() if isinstance(k, str)}
        source = profile.get("source")
        procedure = source.get("procedure") if isinstance(source, Mapping) else None

    evidence = located.get("evidence")
    evidence = evidence if isinstance(evidence, Mapping) else {}
    return {
        "subject": located.get("subject")
        or (profile.get("subject") if isinstance(profile, Mapping) else None),
        "status": located.get("status"),
        "location_route": evidence.get("location_route"),
        "location_reason": evidence.get("reason"),
        "procedure": procedure,
        "banks": banks,
    }


def _serialize_condition_finding(question_id: str, finding: dict) -> tuple[dict, float]:
    """The shared final readout, retaining the existing exact internal rank."""
    from knee.diagnosis.squint_contracts import (
        rank_condition,
        serialize_condition_value,
    )

    ranking = finding.get("rank")
    if not isinstance(ranking, dict):
        ranking = rank_condition(finding)
    value = ranking.get("value")
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise SquintRunError("ranking_value_invalid:" + question_id)
    if not 0.0 < value < 1.0:
        raise SquintRunError("ranking_endpoint_or_out_of_range:" + question_id)
    return ranking, serialize_condition_value(finding, value)


def _condition_changed_subjects(
    before_profiles: Mapping,
    after_profiles: Mapping,
    before_contexts: Mapping,
    after_contexts: Mapping,
    before_not_read: Mapping,
    after_not_read: Mapping,
) -> dict[str, list[str]]:
    """Identify changed shared inputs; producers replace their plain measured profiles."""
    changed = {}
    subjects = set().union(
        before_profiles,
        after_profiles,
        before_contexts,
        after_contexts,
        before_not_read,
        after_not_read,
    )
    for subject in sorted(subjects):
        reasons = []
        before = before_profiles.get(subject)
        after = after_profiles.get(subject)
        if before is not after and before != after:
            reasons.append("profile_changed")
        if before_contexts.get(subject) != after_contexts.get(subject):
            reasons.append("identity_context_changed")
        if before_not_read.get(subject) != after_not_read.get(subject):
            reasons.append("condition_eligibility_changed")
        if reasons:
            changed[subject] = reasons
    return changed


def infer_study(
    root: Path,
    uid: str,
    memory: dict,
    *,
    deadline: float | None = None,
    io_workers: int = 8,
    exclude_same_study: bool = False,
    prepared_identity: Mapping | None = None,
    prepared_identity_resolved: Mapping | None = None,
    navigation_runtime: Any | None = None,
) -> dict:
    """Consume current-study cheap observations; never read teaching calls as features.

    Squint first: location keeps the 10 mm reading it holds, and only a question left open
    earns the bounded finer reading of the object it names (``_bounded_observation``).
    What the locator already established about each located object (its structural
    reader, the anatomy map from the established anchors, or the prior alone) is carried
    forward once as its identity context (``_identity_contexts``): identity recall is
    conditioned on it, and every located object answers its own questions as the object
    identified in context (``identity_consumption``). Resemblance to another object
    changes nothing. A negative case speaking at the squint scale opens the identity
    question, which earns the object's finer look and a finer recall before any
    condition question is asked (``_resolve_identity_contests``); one still applying
    there keeps its region from its object's questions, which stay open. A genuine
    contradictory law observation is a revisable question, and bounded looks are never
    refused for identity. ``prepared_identity`` and ``prepared_identity_resolved`` are
    the identity views at the squint and the finer scale, made from this ``memory``.
    """
    from knee.diagnosis.declarations import QUESTIONS
    from knee.diagnosis.squint_contracts import (
        combine_condition,
    )
    from knee.diagnosis.squint_identity import prepare_identity
    from knee.diagnosis.squint_locator import locate_objects
    from knee.diagnosis.squint_procedures import (
        route_observation_request,
        select_observation_requests,
    )
    from knee.diagnosis.squint_profiles import read_study_squints

    started = time.perf_counter()
    if deadline is not None and time.monotonic() >= deadline:
        return _budget_unexamined_study(
            uid,
            memory,
            reason="study_time_budget_exhausted_before_read",
            elapsed_seconds=time.perf_counter() - started,
        )
    view = memory.get("view")
    if exclude_same_study and not (
        isinstance(view, dict)
        and view.get("schema") == MEMORY_VIEW_SCHEMA
        and uid in view.get("excluded_study_uids", ())
        and view.get("source_fingerprint") == recall_source_fingerprint(memory)
    ):
        memory, _excluded = _study_excluded_memory(memory, uid)
    study = read_study_squints(root, uid, io_workers=io_workers)
    locations = locate_objects(
        study, memory, deadline=deadline, **_squint_first_location(locate_objects)
    )
    objects = locations.get("objects", {})
    excluded_uid = uid if exclude_same_study else None
    identity_contexts = _identity_contexts(objects)
    if prepared_identity is None and "object_identity_teaching" in memory:
        prepared_identity = prepare_identity(memory, exclude_study_uid=excluded_uid)
    identity_readings = _identity_readings(
        objects,
        memory,
        excluded_uid,
        prepared_identity=prepared_identity,
        contexts=identity_contexts,
    )
    # 2 mm readings held when location returned, before any look this study earns.
    fine_readings_at_location = _fine_readings_held(objects)
    observations: list = []
    attempted: set = set()
    # Identity is settled before any condition question reads a region, and the one
    # finer reading an identity question earns is the one every later question reuses.
    if prepared_identity_resolved is None and any(
        isinstance(row, Mapping) and row.get("outcome") in CONTESTED_OUTCOMES
        for row in identity_readings.get("objects", {}).values()
    ):
        prepared_identity_resolved = prepare_identity(
            memory, exclude_study_uid=excluded_uid, scale=JOINT_SCALE
        )
    contests = _resolve_identity_contests(
        objects,
        study,
        memory,
        excluded_uid,
        identity_readings,
        identity_contexts,
        attempted,
        observations,
        deadline,
        prepared_identity_resolved,
    )
    identity_consumption = _identity_consumption(
        objects, identity_readings, identity_contexts, contests
    )
    not_read = _regions_not_read(identity_consumption)
    questions: dict[str, dict[str, Any]] = {}
    values: dict[str, float] = {}
    question_declarations = {question.question_id: question for question in QUESTIONS}
    dependencies = {
        question.question_id: set(question.objects)
        | set(contract_for(question.question_id).subjects)
        for question in QUESTIONS
    }
    condition_revision = 0
    condition_updates = []
    condition_recall_calls = 0
    navigation_request_orderings = []
    for question in QUESTIONS:
        object_evidence = _recall_question(
            question, objects, memory, uid, exclude_same_study, not_read_as=not_read
        )
        condition_recall_calls += 1
        finding = combine_condition(question.question_id, object_evidence)
        finding_revision = condition_revision
        requests = (
            finding.get("observation_requests", [])
            if finding.get("outcome") == "open"
            else []
        )
        if requests:
            requests = select_observation_requests(
                requests,
                memory,
                objects=objects,
                finding=finding,
                study_uid=uid,
                exclude_same_study=exclude_same_study,
            )
            if navigation_runtime is not None:
                from knee.diagnosis.som_runtime import order_navigation_requests

                partial_record = {
                    "objects": objects,
                    "questions": {
                        **questions,
                        question.question_id: {
                            "finding": finding,
                            "objects": object_evidence,
                        },
                    },
                    "identity_recall": identity_readings,
                    "identity_consumption": identity_consumption,
                }
                requests, order_receipt = order_navigation_requests(
                    navigation_runtime, partial_record, question.question_id, requests
                )
                navigation_request_orderings.append(order_receipt)
            has_confirmed_recalled = any(
                isinstance(r, Mapping)
                and isinstance(r.get("recalled_procedure"), Mapping)
                and r["recalled_procedure"].get("status")
                == "recalled_confirmed_resolution"
                for r in requests
            )
            previous_profiles = {
                subject: row.get("profile")
                for subject, row in objects.items()
                if isinstance(row, Mapping)
            }
            for request in requests:
                if (
                    has_confirmed_recalled
                    and finding.get("outcome") != "open"
                    and isinstance(request, Mapping)
                    and request.get("discretionary", True) is not False
                ):
                    break
                before_finding = finding
                before_contexts = copy.deepcopy(identity_contexts)
                before_not_read = copy.deepcopy(not_read)
                subject_name = (
                    request.get("object", request.get("subject"))
                    if isinstance(request, Mapping)
                    else None
                )
                before_cue = _subject_cue_snapshot(
                    objects.get(subject_name) if isinstance(subject_name, str) else None
                )
                obs = route_observation_request(
                    request,
                    study,
                    objects,
                    attempted,
                    deadline,
                    memory=memory,
                    study_uid=uid,
                    exclude_same_study=exclude_same_study,
                    location_evidence=locations.get("evidence"),
                )
                if subject_name is None:
                    subject_name = obs.get("subject")
                obs["question"] = question.question_id
                obs["attribution_scope"] = "single_procedure"
                if before_cue is not None:
                    obs["before_cue"] = before_cue
                if isinstance(request, Mapping):
                    obs["request_id"] = request.get("request_id")
                    obs["request_kind"] = request.get("kind", "bounded_zoom")
                    obs["request_reason"] = request.get("reason")
                    obs["request_scope"] = request.get("scope")
                    if (
                        "recalled_procedure" in request
                        and "recalled_procedure" not in obs
                    ):
                        obs["recalled_procedure"] = request["recalled_procedure"]
                obs["before_state"] = _condition_state_snapshot(
                    before_finding, subject_name
                )
                observations.append(obs)
                first_observation_index = len(observations) - 1
                prepared_identity_resolved = _refresh_identity_after_observations(
                    objects,
                    study,
                    memory,
                    excluded_uid,
                    previous_profiles,
                    identity_contexts,
                    identity_readings,
                    contests,
                    attempted,
                    observations,
                    deadline,
                    prepared_identity,
                    prepared_identity_resolved,
                )
                identity_consumption = _identity_consumption(
                    objects, identity_readings, identity_contexts, contests
                )
                not_read = _regions_not_read(identity_consumption)
                next_profiles = {
                    subject: row.get("profile")
                    for subject, row in objects.items()
                    if isinstance(row, Mapping)
                }
                changed = _condition_changed_subjects(
                    previous_profiles,
                    next_profiles,
                    before_contexts,
                    identity_contexts,
                    before_not_read,
                    not_read,
                )
                previous_profiles = next_profiles
                refreshed = []
                if changed:
                    condition_revision += 1
                    for prior_id, cached in tuple(questions.items()):
                        affected = dependencies[prior_id].intersection(changed)
                        if not affected:
                            continue
                        evidence = _recall_question(
                            question_declarations[prior_id],
                            objects,
                            memory,
                            uid,
                            exclude_same_study,
                            not_read_as=not_read,
                        )
                        condition_recall_calls += 1
                        updated = combine_condition(prior_id, evidence)
                        updated_rank, updated_value = _serialize_condition_finding(
                            prior_id, updated
                        )
                        refreshed.append(
                            {
                                "question": prior_id,
                                "changed_dependencies": sorted(affected),
                                "previous_outcome": cached["finding"]["outcome"],
                                "current_outcome": updated["outcome"],
                                "previous_value": values[prior_id],
                                "current_value": updated_value,
                            }
                        )
                        questions[prior_id] = {
                            "finding": updated,
                            "ranking": updated_rank,
                            "objects": evidence,
                            "shared_state_revision": condition_revision,
                        }
                        values[prior_id] = updated_value
                current_changed = bool(
                    dependencies[question.question_id].intersection(changed)
                )
                current_recalled = current_changed or obs.get("code") == "recall_ready"
                if current_recalled:
                    object_evidence = _recall_question(
                        question,
                        objects,
                        memory,
                        uid,
                        exclude_same_study,
                        not_read_as=not_read,
                    )
                    condition_recall_calls += 1
                    finding = combine_condition(question.question_id, object_evidence)
                    finding_revision = condition_revision
                if changed:
                    condition_updates.append(
                        {
                            "revision": condition_revision,
                            "trigger_question": question.question_id,
                            "observation_indices": list(
                                range(first_observation_index, len(observations))
                            ),
                            "changed_subjects": changed,
                            "refreshed_questions": refreshed,
                            "current_question_recalled": current_recalled,
                            "consumer": "_recall_question -> combine_condition -> serialize_condition_value",
                        }
                    )
                obs["after_state"] = _condition_state_snapshot(finding, subject_name)
        ranking, value = _serialize_condition_finding(question.question_id, finding)
        values[question.question_id] = value
        questions[question.question_id] = {
            "finding": finding,
            "ranking": ranking,
            "objects": object_evidence,
            "shared_state_revision": finding_revision,
        }
    work = {
        **study.get("work", {}),
        "leg_map_status": study.get("leg_map_status", "unavailable"),
        "shared_leg_map_series": len(study.get("leg_maps") or {}),
        "elapsed_seconds": time.perf_counter() - started,
        "process_peak_rss_bytes_at_study_end": resource.getrusage(
            resource.RUSAGE_SELF
        ).ru_maxrss
        * (1 if platform.system() == "Darwin" else 1024),
        "full_anatomy_runs": 0,
        "bounded_zoom_runs": sum(row["code"] == "measured" for row in observations),
        # 2 mm readings held when location returned, against those a question earned.
        "location_fine_readings": fine_readings_at_location,
        "paired_fine_readings": sum(
            len(row.get("regions") or ())
            for row in observations
            if row["code"] == "measured" and row.get("lens") == PAIRED_FINER_LENS
        ),
        "own_outline_parts_measured": sum(
            (row.get("own_outline") or {}).get("code") == "measured"
            for row in observations
        ),
        "own_outline_native_slices_read": sum(
            ((row.get("own_outline") or {}).get("cost") or {}).get(
                "native_slices_read", 0
            )
            for row in observations
        ),
        "own_outline_seconds": sum(
            ((row.get("own_outline") or {}).get("cost") or {}).get("seconds", 0.0)
            for row in observations
        ),
        "source_mode": "raw_squint_case_recall",
        "condition_recall_calls": condition_recall_calls,
    }
    # Neither Series nor SquintStack escapes this operation. Retained profiles
    # and addresses suffice to inspect why recall reached each finding.
    result = {
        "schema": "knee.squint-study/v1",
        "readout_policy_id": READOUT_POLICY_ID,
        "study_uid": uid,
        "memory_revision": memory.get("revision", ""),
        "study_status": "examined",
        "questions": questions,
        "values": values,
        "objects": objects,
        "identity_recall": identity_readings,
        "identity_consumption": identity_consumption,
        "observations": observations,
        "condition_propagation": {
            "schema": "knee.condition-dependency-refresh/v1",
            "revision": condition_revision,
            "dependencies": {
                name: sorted(subjects) for name, subjects in dependencies.items()
            },
            "updates": condition_updates,
        },
        "work": work,
        "unresolved_observation_requests": [
            {"question": q, **request}
            for q, record in questions.items()
            for request in record["finding"].get("observation_requests", [])
        ],
    }
    if navigation_runtime is not None:
        result["navigation_request_orderings"] = navigation_request_orderings
    return result


def _study_excluded_memory(memory: dict, uid: str) -> tuple[dict, dict]:
    """Use the same population for capacity location, recall and preparation."""
    view = memory_view(memory, exclude_study_uids=(uid,))
    case_count = len(memory.get("cases", ()))
    censor_count = len(memory.get("censors", ()))
    return view, {
        "excluded_study_uid": uid,
        "original_case_count": case_count,
        "filtered_case_count": len(view["cases"]),
        "excluded_case_count": case_count - len(view["cases"]),
        "original_censor_count": censor_count,
        "filtered_censor_count": len(view.get("censors", ())),
        "excluded_censor_count": censor_count - len(view.get("censors", ())),
    }


def _study_budget_deadline(
    total_deadline: float,
    remaining_studies: int,
    worker_count: int,
    *,
    now: float | None = None,
) -> tuple[float, float]:
    """Allocate one bounded remaining-time share to an admitted study."""
    moment = time.monotonic() if now is None else now
    if type(remaining_studies) is not int or remaining_studies < 1:
        raise SquintRunError("remaining_studies_invalid")
    if type(worker_count) is not int or worker_count < 1:
        raise SquintRunError("worker_count_invalid")
    remaining = max(0.0, total_deadline - moment)
    active_workers = min(worker_count, remaining_studies)
    share = remaining * active_workers / remaining_studies
    return min(total_deadline, moment + share), share


def _capacity_exclusion_evidence(
    excluded: dict,
    prepared: dict | None,
    *,
    memory: dict,
    memory_digest: str,
    preparation_status: str,
) -> dict:
    prepared = prepared or {}
    excluded_count = (
        excluded["excluded_case_count"] or excluded["excluded_censor_count"]
    )
    population = {
        "status": (
            "prepared" if prepared.get("outcome") == "prepared" else preparation_status
        ),
        "source_fingerprint": prepared.get("source_fingerprint"),
        "source": prepared.get(
            "memory_source", memory.get("source", memory.get("metadata", {}))
        ),
        "memory_manifest_sha256": memory_digest,
        "case_profile_count": (
            len(prepared.get("case_profile_banks", {}))
            if isinstance(prepared.get("case_profile_banks"), dict)
            else None
        ),
    }
    return {
        **excluded,
        "exclusion_status": "applied" if excluded_count else "no_matching_attribution",
        "consumed_case_fingerprint": prepared.get("source_fingerprint"),
        "consumed_fingerprint_scope": "source_cases_calls_profiles_and_censors_v1",
        "preparation_schema": prepared.get("schema"),
        "preparation_outcome": prepared.get("outcome", preparation_status),
        "prepared_population_identity": population,
    }


def _publish_preparation_cache_bytes(
    output: Path, content: bytes, expected_sha256: str
) -> Path:
    """Atomically retain the exact validated compressed preparation sidecar."""
    destination = output / "recall-preparation.json.xz"
    temporary = output / f".{destination.name}.{os.getpid()}.tmp"
    try:
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        copied_sha256 = hashlib.sha256(temporary.read_bytes()).hexdigest()
        if copied_sha256 != expected_sha256:
            raise SquintRunError("squint_recall_cache_copy_digest_mismatch")
        os.replace(temporary, destination)
        directory_fd = os.open(output, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return destination
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def run_squint_cli(args, *, prepared_memory_snapshot=None) -> dict:
    """One production entry point, bounded concurrent studies and immutable memory."""
    from knee.diagnosis.squint_memory import (
        MemorySnapshot,
        compile_bootstrap,
        load_memory_snapshot,
    )
    from knee.diagnosis.submission import write_submission

    mode = getattr(args, "diagnostic_mode", None)
    navigation_path = getattr(args, "diagnostic_navigation", None)
    if navigation_path is not None and mode != "infer":
        raise SquintRunError("navigation_requires_infer")
    if getattr(args, "draw", False):
        raise SquintRunError("squint_production_disallows_draw")
    if args.diagnostic_memory is None or args.diagnostic_output is None:
        raise SquintRunError("squint_memory_and_output_required")
    if any(
        getattr(args, name, None) is not None
        for name in (
            "diagnostic_products",
            "diagnostic_inputs",
            "diagnostic_readout",
            "diagnostic_trust",
            "diagnostic_questions",
            "diagnostic_cases",
            "diagnostic_scratch",
        )
    ):
        raise SquintRunError("squint_conflicting_reference_options")
    output = Path(args.diagnostic_output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    bootstrap = getattr(args, "squint_bootstrap_products", None)
    if mode == "teach":
        if bootstrap is None:
            raise SquintRunError("squint_bootstrap_products_required")
        selected = tuple(args.study_uid) if getattr(args, "study_uid", None) else None
        compiled = compile_bootstrap(
            Path(args.root),
            Path(bootstrap),
            Path(args.diagnostic_memory),
            selected_uids=selected,
        )
        result = {
            "schema": SCHEMA,
            "action": "teach",
            "store": compiled,
            "memory": str(Path(args.diagnostic_memory).resolve()),
            "work": {
                "elapsed_seconds": time.perf_counter() - started,
                "full_anatomy_runs": 0,
            },
        }
        _save(output / "receipt.json", result)
        return result
    if mode not in ("infer", "capacity") or bootstrap is not None:
        raise SquintRunError("squint_operation_invalid")
    if getattr(args, "diagnostic_labels", None) is not None:
        raise SquintRunError("squint_inference_does_not_read_label_source")
    limit = float(getattr(args, "squint_time_limit", 30000.0))
    if not math.isfinite(limit) or limit <= 0:
        raise SquintRunError("squint_time_limit_invalid")
    total_deadline = time.monotonic() + limit
    snapshot = prepared_memory_snapshot
    if snapshot is None:
        snapshot = load_memory_snapshot(Path(args.diagnostic_memory))
    if not isinstance(snapshot, MemorySnapshot):
        raise SquintRunError("squint_memory_snapshot_invalid")
    expected_path = _manifest_path(Path(args.diagnostic_memory)).resolve()
    if snapshot.path != expected_path:
        raise SquintRunError("squint_memory_snapshot_path_mismatch")
    if snapshot.status != "squint" or snapshot.memory is None:
        raise SquintRunError(snapshot.error_code or "squint_memory_snapshot_invalid")
    if not isinstance(snapshot.sha256, str):
        raise SquintRunError("squint_memory_snapshot_digest_missing")
    memory_digest = snapshot.sha256
    memory = snapshot.memory
    navigation_runtime = None
    if navigation_path is not None:
        from knee.diagnosis.som_runtime import load_navigation_runtime

        navigation_runtime = load_navigation_runtime(navigation_path)
    if mode == "capacity":
        memory = {**memory, "memory_manifest_sha256": memory_digest}
    from knee.diagnosis.squint_locator import prepare_recall
    from knee.json_store import dump_json_atomic, load_json, resolve_json_path

    uids = _selected_uids(args)
    cohort_path = getattr(args, "diagnostic_cohort", None)
    partition = getattr(args, "diagnostic_partition", None)
    cohort_receipt = None
    if (cohort_path is None) != (partition is None):
        raise SquintRunError("squint_cohort_and_partition_must_be_paired")
    if cohort_path is not None:
        from knee.diagnosis.cohort import load_cohort, partition_uids

        if not isinstance(partition, str):
            raise SquintRunError("squint_cohort_partition_invalid")
        cohort = load_cohort(Path(cohort_path))
        uids = partition_uids(cohort, partition, uids)
        cohort_receipt = {
            "path": cohort.source,
            "sha256": cohort.sha256,
            "partition": partition,
        }
    worker_count = max(1, min(int(args.workers), len(uids), 4))
    preparation_path = None
    preparation_seconds = 0.0
    preparation_cache_path = resolve_json_path(
        snapshot.path.parent / "recall-preparation.json"
    )
    cache = None
    preparation_cache_status = (
        "study_excluded_per_study" if mode == "capacity" else "missing_recomputed"
    )
    preparation_cache_bytes = None
    preparation_cache_sha256 = None
    if preparation_cache_path.is_file():
        try:
            pinned_sha256 = hashlib.sha256(
                preparation_cache_path.read_bytes()
            ).hexdigest()
            candidate = load_json(preparation_cache_path)
            loaded_bytes = preparation_cache_path.read_bytes()
            if hashlib.sha256(loaded_bytes).hexdigest() != pinned_sha256:
                candidate = None
            elif preparation_cache_path.name.endswith(".json.xz"):
                preparation_cache_bytes = loaded_bytes
                preparation_cache_sha256 = pinned_sha256
        except (OSError, ValueError, UnicodeError):
            candidate = None
            preparation_cache_bytes = None
            preparation_cache_sha256 = None
        if (
            isinstance(candidate, dict)
            and candidate.get("memory_manifest_sha256") == memory_digest
            and candidate.get("memory_revision") == memory.get("revision", "")
        ):
            cache = candidate
            if mode != "capacity":
                preparation_cache_status = "cached_candidate"
        elif mode != "capacity":
            preparation_cache_status = "invalid_recomputed"
    identity_preparation_seconds = 0.0
    identity_resolved_preparation_seconds = 0.0
    # The shared preparation; capacity runs prepare each study's held-out view instead.
    prepared: dict | None = None
    if mode != "capacity":
        preparation_started = time.perf_counter()
        prepared = (
            prepare_recall(memory, cached=cache)
            if cache is not None
            else prepare_recall(memory)
        )
        preparation_seconds = time.perf_counter() - preparation_started
        if not isinstance(prepared, dict) or prepared.get("outcome") != "prepared":
            raise SquintRunError("squint_recall_preparation_invalid")
        if prepared.get("runtime_indexes_rebuilt") is True:
            preparation_cache_status = "persisted_reused"
        elif cache is not None:
            preparation_cache_status = "stale_recomputed"
        memory = {**memory, "prepared_recall": prepared}
        if (
            preparation_cache_status == "persisted_reused"
            and isinstance(cache, dict)
            and preparation_cache_bytes is not None
            and preparation_cache_sha256 is not None
        ):
            preparation_path = _publish_preparation_cache_bytes(
                output, preparation_cache_bytes, preparation_cache_sha256
            )
            preparation_artifact_schema = cache.get("schema")
            preparation_artifact_source = "persisted_cache_sidecar_bytes"
        else:
            preparation_path = dump_json_atomic(
                output / "recall-preparation.json",
                {
                    "schema": prepared.get("schema"),
                    "memory_manifest_sha256": memory_digest,
                    "memory_revision": memory.get("revision", ""),
                    "cache_status": preparation_cache_status,
                    **{
                        key: prepared[key]
                        for key in (
                            "outcome",
                            "source_fingerprint",
                            "memory_source",
                            "envelopes",
                            "case_indices",
                            "censor_indices",
                        )
                        if key in prepared
                    },
                },
            )
            preparation_artifact_schema = prepared.get("schema")
            preparation_artifact_source = "computed_preparation"
        preparation_identity = {
            "source_fingerprint": prepared.get("source_fingerprint"),
            "memory_manifest_sha256": memory_digest,
            "memory_revision": memory.get("revision", ""),
        }
        identity_prepared_shared = None
        identity_resolved_shared = None
        if "object_identity_teaching" in memory:
            from knee.diagnosis.squint_identity import prepare_identity

            identity_started = time.perf_counter()
            identity_prepared_shared = prepare_identity(memory)
            identity_preparation_seconds = time.perf_counter() - identity_started
            # Once per bank set (its own trust radii), from the very memory object
            # every study is given.
            identity_started = time.perf_counter()
            identity_resolved_shared = prepare_identity(memory, scale=JOINT_SCALE)
            identity_resolved_preparation_seconds = (
                time.perf_counter() - identity_started
            )
    else:
        identity_prepared_shared = None
        identity_resolved_shared = None
        preparation_artifact_schema = None
        preparation_artifact_source = "not_written"
        preparation_identity = None

    navigation_options: dict[str, Any] = (
        {"navigation_runtime": navigation_runtime}
        if navigation_runtime is not None
        else {}
    )

    def infer_admitted_study(uid: str, deadline: float, budget_seconds: float) -> dict:
        study_memory: dict = memory
        excluded = None
        study_preparation_seconds = 0.0
        study_identity_preparation_seconds = 0.0
        study_preparation_source = preparation_cache_status
        if mode == "capacity":
            study_memory, excluded = _study_excluded_memory(memory, uid)
        if time.monotonic() >= deadline:
            record = _budget_unexamined_study(
                uid,
                study_memory,
                reason="study_time_budget_exhausted_before_preparation",
            )
            record["work"].update(
                {
                    "study_time_budget_seconds": budget_seconds,
                    "study_budget_deadline_exhausted": True,
                    "recall_preparation_seconds": 0.0,
                    "recall_preparation_source": "not_run_budget_exhausted",
                }
            )
            if excluded is not None:
                record["capacity_exclusion"] = _capacity_exclusion_evidence(
                    excluded,
                    None,
                    memory=memory,
                    memory_digest=memory_digest,
                    preparation_status="not_run_budget_exhausted",
                )
            else:
                record["capacity_exclusion"] = {
                    "exclusion_status": "not_requested",
                    "excluded_study_uid": None,
                }
            return record
        identity_prepared = identity_prepared_shared
        if mode == "capacity":
            preparation_started = time.perf_counter()
            study_prepared = prepare_recall(memory, cached=cache, exclude_study_uid=uid)
            study_preparation_seconds = time.perf_counter() - preparation_started
            if (
                not isinstance(study_prepared, dict)
                or study_prepared.get("outcome") != "prepared"
            ):
                raise SquintRunError("squint_capacity_recall_preparation_invalid")
            study_memory = {
                **study_memory,
                "prepared_recall": study_prepared,
                "view": {**study_memory["view"], "preparation_code": "prepared"},
            }
            if "object_identity_teaching" in study_memory:
                from knee.diagnosis.squint_identity import prepare_identity

                identity_started = time.perf_counter()
                identity_prepared = prepare_identity(
                    study_memory, exclude_study_uid=uid
                )
                study_identity_preparation_seconds = (
                    time.perf_counter() - identity_started
                )
            study_preparation_source = (
                "study_excluded_projected"
                if study_prepared.get("runtime_indexes_rebuilt") is True
                else "study_excluded_recomputed"
            )
        record = infer_study(
            Path(args.root),
            uid,
            study_memory,
            deadline=deadline,
            exclude_same_study=mode == "capacity",
            prepared_identity=identity_prepared,
            # A capacity study's finer view is made from its own held-out memory,
            # only when one of its identity questions needs it.
            prepared_identity_resolved=(
                identity_resolved_shared if mode != "capacity" else None
            ),
            **navigation_options,
        )
        record["work"].update(
            {
                "study_time_budget_seconds": budget_seconds,
                "study_budget_deadline_exhausted": time.monotonic() >= deadline,
                "recall_preparation_seconds": study_preparation_seconds,
                "recall_preparation_source": study_preparation_source,
                "identity_preparation_seconds": study_identity_preparation_seconds,
                "identity_preparation_source": (
                    "study_excluded"
                    if mode == "capacity" and identity_prepared is not None
                    else "shared_once"
                    if identity_prepared is not None
                    else "not_requested"
                ),
            }
        )
        if excluded is not None:
            prepared = study_memory.get("prepared_recall", {})
            record["capacity_exclusion"] = _capacity_exclusion_evidence(
                excluded,
                prepared,
                memory=memory,
                memory_digest=memory_digest,
                preparation_status=study_preparation_source,
            )
        else:
            record["capacity_exclusion"] = {
                "exclusion_status": "not_requested",
                "excluded_study_uid": None,
            }
        return record

    def submit_study(pool, uid: str, remaining_studies: int):
        deadline, budget = _study_budget_deadline(
            total_deadline, remaining_studies, worker_count
        )
        return pool.submit(infer_admitted_study, uid, deadline, budget)

    rows = []
    studies = []
    tallies = {label: Counter() for label in LABELS}
    # Submit at most worker_count studies. Completed arrays are released before
    # another study is admitted, irrespective of hidden-test cohort size.
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        pending = {}
        cursor = iter(uids)
        for _ in range(worker_count):
            uid = next(cursor, None)
            if uid is not None:
                pending[uid] = submit_study(pool, uid, len(uids))
        for completed, uid in enumerate(uids, start=1):
            record = pending.pop(uid).result()
            if navigation_runtime is not None:
                from knee.diagnosis.som_runtime import apply_navigation_record

                record = apply_navigation_record(navigation_runtime, record)
            evidence_path = dump_json_atomic(
                output / "studies" / (uid + ".json"),
                record,
                compression_preset=0,
            )
            rows.append((uid, record["values"]))
            studies.append(
                {
                    "study_uid": uid,
                    **record["work"],
                    "capacity_exclusion": record["capacity_exclusion"],
                    "evidence_path": str(evidence_path.relative_to(output)),
                    "evidence_bytes": evidence_path.stat().st_size,
                }
            )
            if navigation_runtime is not None:
                studies[-1]["navigation_outcome"] = record["navigation"]["outcome"]
                studies[-1]["navigation_request_orderings"] = len(
                    record.get("navigation_request_orderings", [])
                )
            for label, evidence in record["questions"].items():
                tally = (
                    "not_examined_budget"
                    if record.get("study_status") == "not_examined_budget"
                    else evidence["finding"]["outcome"]
                )
                tallies[label][tally] += 1
            del record
            next_uid = next(cursor, None)
            if next_uid is not None:
                pending[next_uid] = submit_study(pool, next_uid, len(uids) - completed)
    submission = None
    template = getattr(args, "diagnostic_submission_template", None)
    if template is not None:
        submission_source = {
            "readout_policy_id": READOUT_POLICY_ID,
            "source_mode": "raw_squint_case_recall",
            "memory_revision": memory.get("revision", ""),
            "memory_manifest_sha256": memory_digest,
        }
        if navigation_runtime is not None:
            submission_source["navigation"] = {
                "scope": "study_condition_model_opinion_not_localized_tissue",
                "artifact_pins": dict(navigation_runtime.artifact_pins),
            }
        submission = write_submission(
            Path(template),
            output / "submission.csv",
            rows,
            source_provenance=submission_source,
        )
    result = {
        "schema": SCHEMA,
        "action": mode,
        "readout_policy_id": READOUT_POLICY_ID,
        "source_mode": "raw_squint_case_recall",
        "studies": len(studies),
        "memory_revision": memory.get("revision", ""),
        "memory_manifest_sha256": memory_digest,
        "recall_preparation": {
            "path": (
                str(preparation_path.relative_to(output))
                if preparation_path is not None
                else None
            ),
            "sha256": (
                hashlib.sha256(preparation_path.read_bytes()).hexdigest()
                if preparation_path is not None
                else None
            ),
            "bytes": preparation_path.stat().st_size
            if preparation_path is not None
            else 0,
            "cache_status": preparation_cache_status,
            "seconds": preparation_seconds,
            "schema": preparation_artifact_schema,
            "preparation_schema": (
                prepared.get("schema") if prepared is not None else None
            ),
            "artifact_source": preparation_artifact_source,
            "identity": preparation_identity,
            "source_cache_sha256": preparation_cache_sha256,
        },
        "per_question": {q: dict(c) for q, c in tallies.items()},
        "submission": submission,
        "cohort": cohort_receipt,
        "work": {
            "elapsed_seconds": time.perf_counter() - started,
            "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            * (1 if platform.system() == "Darwin" else 1024),
            "full_anatomy_runs": 0,
            "memory_loaded_once": True,
            "recall_preparation_seconds": preparation_seconds,
            "identity_preparation_seconds": identity_preparation_seconds,
            "identity_resolved_preparation_seconds": (
                identity_resolved_preparation_seconds
            ),
            "identity_preparations_shared": int(identity_prepared_shared is not None),
            "identity_resolved_preparations_shared": int(
                identity_resolved_shared is not None
            ),
            "workers": worker_count,
            "studies": studies,
        },
    }
    if navigation_runtime is not None:
        from knee.diagnosis.som_runtime import navigation_provenance

        result["navigation"] = {
            **navigation_provenance(navigation_runtime),
            "loaded_once": True,
            "study_outcomes": dict(
                Counter(row["navigation_outcome"] for row in studies)
            ),
        }
    _save(output / "receipt.json", result)
    return result
