"""Squint-first inference, bounded study lifetimes and official output.

The full reconstruction runner is a bootstrap/reference tool. This coordinator
never calls it. Each worker owns one study's decoded pixels and releases them
when its compact findings have been published. Case memory is loaded once.
"""

from __future__ import annotations

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

from knee.diagnosis.squint_interfaces import MEMORY_VIEW_SCHEMA, TERRITORY_PROCEDURE
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
    withheld: Mapping[str, Mapping] | None = None,
) -> dict:
    """Recall each of a question's objects and its whole configuration.

    ``withheld`` names located objects whose identity recall withheld their tissue from
    their proposed subject (``_identity_consumption``). Each reaches both voices exactly as
    an unlocated object does: its own voice hears an empty reading, and no configuration
    composes it. Its named reason is kept beside its evidence as ``identity_withheld``;
    the condition contracts never read it, so the withheld object stays unknown, never a
    normal reading and never a defeat. It is not reassigned to the identity it resembles.
    """
    from knee.diagnosis.squint_locator import recall_object

    if withheld:
        objects = {
            name: value for name, value in objects.items() if name not in withheld
        }
    else:
        withheld = {}
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
        if subject in withheld:
            record["identity_withheld"] = dict(withheld[subject])
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
    *,
    withheld: Mapping[str, Mapping] | None = None,
) -> dict:
    """Make the one bounded reading a request asks for, once per object and study.

    A request that names no procedure asks for the paired finer reading: a reading the
    object holds at 10 mm, read again at 2 mm over the same native region. A territory
    reading is refined over its region's own territory record (``refine_territory``), a
    v1 reading over its tile window (``refine_window``); the two are never mixed. A
    reading the object already holds is neither read nor added again, and every question
    that asks shares the one reading. A ``lens`` naming the object's own native procedure
    runs that existing procedure instead (``_named_procedure``); no part is sent there
    for what it is. A located object its identity recall withheld (``withheld``) earns no
    read of either kind and its located record is left as it is. Whatever cannot be read
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
    if withheld and subject in withheld:
        # Tissue recognized as another object, or opposed by its own negative cases,
        # is no region of this object to read: the request is named, never read.
        return {**unlocated, "subject": subject, **withheld[subject]}
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


def _identity_readings(
    objects: dict,
    memory: dict,
    excluded_uid: str | None,
    *,
    prepared_identity: Mapping | None = None,
) -> dict:
    """Hear called identity seeds once per study view, independently of diagnosis.

    An automatic catalogue is not identity teaching. Missing profiles remain unread;
    neither a proposed anatomical name nor a plausible location supplies a class.
    This operation returns evidence only: it never publishes a case or a diagnosis.
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


def _names(value: object) -> frozenset[str]:
    """The identity names a recall lists, or none when the list is absent or malformed."""
    if not isinstance(value, (list, tuple)):
        return frozenset()
    return frozenset(item for item in value if isinstance(item, str))


def _identity_decision(subject: str, reading: object, examined: object) -> dict:
    """Whether one located object's tissue may answer its proposed subject's questions.

    ``subject`` is the object the structure placed, ``reading`` its identity recall and
    ``examined`` the study's identity outcome. Tissue recognized as a different object,
    or spoken against by negative cases of its own subject with no positive case for it,
    is ``withheld``: it answers none of that subject's condition questions and earns no
    bounded read, and it is never reassigned to the identity it resembles. Everything
    else is ``kept``, the structure's own placement standing, with the outcome that left
    it standing as its reason. Recognized as itself, conflicted, without precedent,
    unread, blocked by its anatomical check or heard against a memory with no identity
    teaching, its tissue still answers: an unresolved identity is no clinical absence.
    """
    if examined != "examined":
        reason = examined if isinstance(examined, str) and examined else None
        return {"decision": "kept", "reason": reason or "identity_recall_unavailable"}
    if not isinstance(reading, Mapping):
        return {"decision": "kept", "reason": "identity_reading_missing"}
    outcome = reading.get("outcome")
    identity = reading.get("identity")
    if outcome == "identified" and isinstance(identity, str) and identity:
        if identity != subject:
            return {
                "decision": "withheld",
                "reason": "identity_recognized_as_other",
                "recognized_as": identity,
            }
        return {"decision": "kept", "reason": "identified", "recognized_as": identity}
    opposed = _names(reading.get("opposed_identities"))
    if subject in opposed and subject not in _names(reading.get("speaking_identities")):
        return {"decision": "withheld", "reason": "identity_opposed_by_negative_cases"}
    return {
        "decision": "kept",
        "reason": outcome
        if isinstance(outcome, str) and outcome
        else "identity_outcome_invalid",
    }


def _identity_consumption(objects: object, identity_readings: object) -> dict:
    """Each located object's identity decision, as condition reasoning consumes it."""
    if not isinstance(objects, Mapping):
        return {}
    examined = readings = None
    if isinstance(identity_readings, Mapping):
        examined = identity_readings.get("outcome")
        readings = identity_readings.get("objects")
    if not isinstance(readings, Mapping):
        readings = {}
    return {
        subject: _identity_decision(subject, readings.get(subject), examined)
        for subject in sorted(objects)
    }


def _withheld_objects(consumption: Mapping) -> dict:
    """The withheld objects and the named reason each carries to its evidence."""
    return {
        subject: {key: value for key, value in decision.items() if key != "decision"}
        for subject, decision in consumption.items()
        if decision.get("decision") == "withheld"
    }


def infer_study(
    root: Path,
    uid: str,
    memory: dict,
    *,
    deadline: float | None = None,
    io_workers: int = 8,
    exclude_same_study: bool = False,
    prepared_identity: Mapping | None = None,
) -> dict:
    """Consume current-study cheap observations; never read teaching calls as features.

    Squint first: location keeps the 10 mm reading it holds, and only a question left open
    earns the bounded finer reading of the object it names (``_bounded_observation``).
    Identity recall decides, once per located object, whether its tissue may answer its
    proposed subject (``identity_consumption``); a withheld object reaches every condition
    question and bounded read as an unlocated one, and its located record is retained.
    """
    from knee.diagnosis.declarations import QUESTIONS
    from knee.diagnosis.squint_contracts import combine_condition, rank_condition
    from knee.diagnosis.squint_locator import locate_objects
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
    identity_readings = _identity_readings(
        objects,
        memory,
        uid if exclude_same_study else None,
        prepared_identity=prepared_identity,
    )
    identity_consumption = _identity_consumption(objects, identity_readings)
    withheld = _withheld_objects(identity_consumption)
    fine_readings_at_location = _fine_readings_held(objects)
    questions = {}
    values = {}
    observations = []
    attempted = set()
    for question in QUESTIONS:
        object_evidence = _recall_question(
            question, objects, memory, uid, exclude_same_study, withheld=withheld
        )
        finding = combine_condition(question.question_id, object_evidence)
        requests = (
            finding.get("observation_requests", [])
            if finding.get("outcome") == "open"
            else []
        )
        if requests:
            for request in requests:
                observations.append(
                    _bounded_observation(
                        request, study, objects, attempted, deadline, withheld=withheld
                    )
                )
            object_evidence = _recall_question(
                question, objects, memory, uid, exclude_same_study, withheld=withheld
            )
            finding = combine_condition(question.question_id, object_evidence)
        ranking = finding.get("rank")
        if not isinstance(ranking, dict):
            ranking = rank_condition(finding)
        value = ranking.get("value")
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise SquintRunError("ranking_value_invalid:" + question.question_id)
        if not 0.0 < value < 1.0:
            raise SquintRunError(
                "ranking_endpoint_or_out_of_range:" + question.question_id
            )
        values[question.question_id] = value
        questions[question.question_id] = {
            "finding": finding,
            "ranking": ranking,
            "objects": object_evidence,
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
    }
    # Neither Series nor SquintStack escapes this operation. Retained profiles
    # and addresses suffice to inspect why recall reached each finding.
    result = {
        "schema": "knee.squint-study/v1",
        "study_uid": uid,
        "memory_revision": memory.get("revision", ""),
        "study_status": "examined",
        "questions": questions,
        "values": values,
        "objects": objects,
        "identity_recall": identity_readings,
        "identity_consumption": identity_consumption,
        "observations": observations,
        "work": work,
        "unresolved_observation_requests": [
            {"question": q, **request}
            for q, record in questions.items()
            for request in record["finding"].get("observation_requests", [])
        ],
    }
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
        if "object_identity_teaching" in memory:
            from knee.diagnosis.squint_identity import prepare_identity

            identity_started = time.perf_counter()
            identity_prepared_shared = prepare_identity(memory)
            identity_preparation_seconds = time.perf_counter() - identity_started
    else:
        identity_prepared_shared = None
        preparation_artifact_schema = None
        preparation_artifact_source = "not_written"
        preparation_identity = None

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
        submission = write_submission(
            Path(template),
            output / "submission.csv",
            rows,
            source_provenance={
                "source_mode": "raw_squint_case_recall",
                "memory_revision": memory.get("revision", ""),
                "memory_manifest_sha256": memory_digest,
            },
        )
    result = {
        "schema": SCHEMA,
        "action": mode,
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
                prepared.get("schema") if mode != "capacity" else None
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
            "identity_preparations_shared": int(identity_prepared_shared is not None),
            "workers": worker_count,
            "studies": studies,
        },
    }
    _save(output / "receipt.json", result)
    return result
