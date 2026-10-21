"""Teacher-addressed queries for the current-writer capacity control only.

The teacher supplies addresses, never query counts or condition calls. The
ordinary production coordinator still owns study exclusion, preparation,
recall, bounded observations, condition combination, ranking and readout.
This is an oracle-location experiment, not a production locator.
"""

from __future__ import annotations

import copy
import json
import threading
import time
from pathlib import Path
from unittest.mock import patch

from knee.diagnosis.declarations import QUESTIONS
from knee.diagnosis.squint_profiles import (
    merge_profiles,
    profile_window,
    refine_window,
)

CONTROL = "teacher_bootstrap_regions/v1"
CONTROL_V2 = "teacher_bootstrap_profiles/territory-v2"
_TERRITORY_PROCEDURE = "knee.squint-profile/leg-tercile-territory-v2"
_CONTROL_LOCK = threading.Lock()


class CapacityControlError(ValueError):
    """A named refusal to run an invalid or non-excluded control."""


def teacher_addresses(memory: dict) -> dict[str, dict[str, list[dict]]]:
    """Copy only object addresses from bootstrap cases; discard profiles/calls.

    Configuration cases contain the same regions role by role and must not
    be counted a second time. Repeated identical object addresses are shared.
    """
    addresses: dict[str, dict[str, list[dict]]] = {}
    for case in memory.get("cases", ()):
        subject = case["subject"]
        if subject.startswith("diagnosis/"):
            continue
        regions = addresses.setdefault(case["study_uid"], {}).setdefault(subject, [])
        for region in case["regions"]:
            if region not in regions:
                regions.append(copy.deepcopy(region))
    return addresses


def teacher_profiles(memory: dict) -> dict[str, dict[str, dict]]:
    """Copy each study's own territory-v2 object case profiles and regions.

    For a territory memory the bootstrap already read every case region over
    the object's own saved outline with the territory writer and the study's
    leg-only cutoffs: exactly what a query read at the true location would
    be. Copied before the study is excluded, so recall never meets them as
    cases. Calls are not copied.
    """
    own: dict[str, dict[str, dict]] = {}
    for case in memory.get("cases", ()):
        subject = case["subject"]
        if subject.startswith("diagnosis/"):
            continue
        profile = case.get("profile")
        if not isinstance(profile, dict):
            continue
        own.setdefault(case["study_uid"], {})[subject] = {
            "profile": copy.deepcopy(profile),
            "regions": copy.deepcopy(case.get("regions", [])),
        }
    return own


def locate_teacher_profiles(study: object, own: dict[str, dict[str, dict]]) -> dict:
    """Located objects for one study from its own territory-v2 case profiles."""
    if (
        not isinstance(study, dict)
        or not isinstance(study.get("study_uid"), str)
        or not study["study_uid"]
    ):
        raise CapacityControlError("teacher_study_identity_invalid")
    uid = study["study_uid"]
    rows = own.get(uid, {})
    subjects = sorted(
        {s for question in QUESTIONS for s in question.objects} | set(rows)
    )
    objects = {}
    for subject in subjects:
        row = rows.get(subject)
        located = row is not None and bool(row["profile"].get("banks"))
        objects[subject] = {
            "status": "located" if located else "unavailable",
            "reason": "teacher_profile_copied"
            if located
            else "teacher_regions_unavailable",
            "profile": row["profile"] if located else None,
            "regions": row["regions"] if located else [],
            "evidence": {"location_mode": CONTROL_V2, "teacher_study_uid": uid},
        }
    return {"outcome": "teacher_locations_read", "objects": objects}


def _region_code(region: object, series: dict | None) -> str:
    if not isinstance(region, dict):
        return "teacher_region_invalid"
    if series is None:
        return "teacher_series_unavailable"
    if getattr(series.get("stack"), "code", None) != "present":
        return "teacher_squint_unavailable"
    window = region.get("source_window")
    if (
        not isinstance(window, (list, tuple))
        or len(window) != 6
        or any(type(value) is not int for value in window)
    ):
        return "teacher_window_invalid"
    z0, z1, r0, r1, c0, c1 = window
    depth, rows, cols = series["stack"].median.shape
    if not (0 <= z0 < z1 <= depth and 0 <= r0 < r1 <= rows and 0 <= c0 < c1 <= cols):
        return "teacher_window_out_of_bounds_or_empty"
    if type(region.get("source_slice")) is not int:
        return "teacher_key_slice_unavailable"
    if (z0, z1) != (region["source_slice"], region["source_slice"] + 1):
        return "teacher_key_slice_window_mismatch"
    return "available"


def locate_teacher_objects(
    study: object, addresses: dict[str, dict[str, list[dict]]], *, deadline=None
) -> dict:
    """Read this study's retained windows using the bootstrap's exact writer.

    Regions are retained verbatim beside named read outcomes. A missing series
    or address never falls back to another series, slice, or guessed window.
    This deliberately keeps v1 box-address semantics and coarse calibration;
    it does not claim that those addresses are measured v2 object territories.
    """
    if (
        not isinstance(study, dict)
        or not isinstance(study.get("study_uid"), str)
        or not study["study_uid"]
    ):
        raise CapacityControlError("teacher_study_identity_invalid")
    uid = study["study_uid"]
    own = addresses.get(uid, {})
    by_uid = {row["series_uid"]: row for row in study.get("series", [])}
    subjects = sorted(
        {s for question in QUESTIONS for s in question.objects} | set(own)
    )
    objects = {}
    for subject in subjects:
        profiles, readings, measured_regions = [], [], []
        regions = own.get(subject, [])
        for region in regions:
            series = (
                by_uid.get(region.get("series_uid"))
                if isinstance(region, dict)
                else None
            )
            code = _region_code(region, series)
            if deadline is not None and time.monotonic() >= deadline:
                code = "teacher_deadline_before_read"
            if code != "available":
                readings.append({"code": code, "region": copy.deepcopy(region)})
                continue
            assert isinstance(series, dict)
            assert isinstance(region, dict)
            window = tuple(region["source_window"])
            # Same two calls and merge nesting as squint_memory._profile_regions.
            coarse = profile_window(series, window, subject=subject)
            try:
                fine = refine_window(series, window, subject=subject, tile_mm=2.0)
            except ValueError as error:
                # Keep the coarse observation, but refuse a paired query when
                # its second writer could not run. Do not substitute a coarse
                # profile for the bootstrap's coarse-plus-fine profile.
                if str(error) != "squint_refine_native_series_unavailable":
                    raise
                readings.append(
                    {
                        "code": "teacher_refinement_unavailable",
                        "region": copy.deepcopy(region),
                        "coarse_profile": coarse,
                    }
                )
                continue
            else:
                combined = merge_profiles((coarse, fine), subject=subject)
                code = (
                    "teacher_profile_measured"
                    if combined["banks"]
                    else "teacher_profile_silent"
                )
            profiles.append(combined)
            measured_regions.append(copy.deepcopy(region))
            readings.append({"code": code, "region": copy.deepcopy(region)})
        profile = merge_profiles(profiles, subject=subject) if profiles else None
        located = profile is not None and bool(profile["banks"])
        reason = (
            "teacher_profile_measured"
            if located
            else readings[0]["code"]
            if readings
            else "teacher_regions_unavailable"
        )
        objects[subject] = {
            "status": "located" if located else "unavailable",
            "reason": reason,
            "profile": profile,
            "regions": measured_regions,
            "evidence": {
                "location_mode": CONTROL,
                "teacher_study_uid": uid,
                "region_readings": readings,
                "unavailable_reasons": sorted(
                    {
                        r["code"]
                        for r in readings
                        if r["code"] != "teacher_profile_measured"
                    }
                    | ({"teacher_regions_unavailable"} if not regions else set())
                ),
            },
        }
    return {"outcome": "teacher_locations_read", "objects": objects}


def run_teacher_capacity(args, *, prepared_memory_snapshot=None) -> dict:
    """Run the real capacity coordinator with only its locator substituted.

    The substitution spans all study threads and is restored on every exit.
    This standalone experiment must not share a process with an ordinary
    inference run. Concurrent/nested control invocations are refused.
    """
    from knee.diagnosis import squint_locator, squint_pipeline
    from knee.diagnosis.squint_memory import MemorySnapshot, load_memory_snapshot

    if getattr(args, "diagnostic_mode", None) != "capacity":
        raise CapacityControlError("teacher_location_requires_capacity")
    if not _CONTROL_LOCK.acquire(blocking=False):
        raise CapacityControlError("teacher_location_control_already_running")
    try:
        snapshot = prepared_memory_snapshot
        if snapshot is None:
            snapshot = load_memory_snapshot(Path(args.diagnostic_memory))
        if not isinstance(snapshot, MemorySnapshot) or snapshot.memory is None:
            raise CapacityControlError("teacher_memory_snapshot_invalid")
        territory = any(
            (case.get("profile") or {}).get("source", {}).get("procedure")
            == _TERRITORY_PROCEDURE
            for case in snapshot.memory.get("cases", ())
            if not case["subject"].startswith("diagnosis/")
        )
        addresses = {} if territory else teacher_addresses(snapshot.memory)
        own_profiles = teacher_profiles(snapshot.memory) if territory else {}
        mode = CONTROL_V2 if territory else CONTROL
        audits = {}

        def teacher_locator(study, memory, deadline=None):
            uid = study["study_uid"]
            if any(c.get("study_uid") == uid for c in memory.get("cases", ())):
                raise CapacityControlError("teacher_location_cases_not_excluded:" + uid)
            for censor in memory.get("censors", ()):
                source = censor.get("source")
                source_uid = (
                    source.get("study_uid") if isinstance(source, dict) else None
                )
                if (censor.get("study_uid") or source_uid) == uid:
                    raise CapacityControlError(
                        "teacher_location_censors_not_excluded:" + uid
                    )
            prepared = memory.get("prepared_recall", {})
            fingerprint = squint_locator.recall_source_fingerprint(memory)
            if prepared.get("source_fingerprint") != fingerprint:
                raise CapacityControlError(
                    "teacher_location_preparation_mismatch:" + uid
                )
            for questions in prepared.get("envelopes", {}).values():
                for buckets in questions.values():
                    for envelope in buckets.values():
                        if any(
                            uid in row["study_uids"]
                            for row in envelope.get("comparisons", ())
                        ):
                            raise CapacityControlError(
                                "teacher_location_prepared_study_leak:" + uid
                            )
            audits[uid] = {"code": "study_excluded", "source_fingerprint": fingerprint}
            if territory:
                return locate_teacher_profiles(study, own_profiles)
            return locate_teacher_objects(study, addresses, deadline=deadline)

        with patch.object(squint_locator, "locate_objects", teacher_locator):
            result = squint_pipeline.run_squint_cli(
                args, prepared_memory_snapshot=snapshot
            )
        result["capacity_control"] = {
            "location_mode": mode,
            "writer": (
                "own territory-v2 case profiles (profile_territory + refine_territory "
                "over each saved outline), copied before exclusion"
                if territory
                else "profile_window+refine_window(2mm), merged per subject"
            ),
            "address_source_manifest_sha256": snapshot.sha256,
            "exclusion_checks": audits,
        }
        receipt = Path(args.diagnostic_output) / "receipt.json"
        temporary = receipt.with_suffix(".tmp")
        temporary.write_text(json.dumps(result, sort_keys=True, allow_nan=False))
        temporary.replace(receipt)
        return result
    finally:
        _CONTROL_LOCK.release()


__all__ = [
    "CONTROL_V2",
    "CapacityControlError",
    "locate_teacher_objects",
    "locate_teacher_profiles",
    "run_teacher_capacity",
    "teacher_addresses",
    "teacher_profiles",
]
