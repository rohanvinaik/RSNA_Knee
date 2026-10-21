"""A territory with a runtime-only native mask waits for a named question like any other.

A bone located by its own anchor carries a native mask that its JSON record holds as an
address and digest alone. Production location (``refine_finalists=False``) makes no 2 mm
reading for it. The question that earns the reading is given the original territory the
location kept, by reference, on the runtime study, and reads over that very mask; a mask
the study does not hold, or holds as another territory, is named and never read in its
place. The default location (``True``) pairs at location as before.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import types

import numpy as np
import pytest

from knee.diagnosis import squint_anatomy_locator as anatomy
from knee.diagnosis import squint_configurations, squint_pipeline
from knee.diagnosis import squint_locator as locator
from knee.diagnosis import squint_profiles as writer
from knee.diagnosis.squint_interfaces import ROLE_CONTEXT, parse_territory_bank_name
from knee.diagnosis.squint_residual import held_readings
from tests import test_squint_dependent_territories as dependent
from tests.test_squint_v2_location import _anchor, _case, _native_bone, _v2_dependent

BONE_WINDOW = [0, 1, 3, 5, 3, 5]
#: the writer's own refinement, kept before any test replaces it with a watcher
REAL_REFINE_TERRITORY = writer.refine_territory
RETAINED = anatomy.NATIVE_SUPPORT_RETAINED


def _mask(block: slice) -> np.ndarray:
    """Two corner pixels and one block: the same box with another place, per block."""
    mask = np.zeros((1, 16, 16), dtype=bool)
    mask[0, 0, 0] = mask[0, -1, -1] = True
    mask[0, block, block] = True
    return mask


def _support(mask: np.ndarray, offset=(60, 60)) -> dict:
    """A native support as the anchor producer makes one: its offset a tuple."""
    return {"mask": mask, "offset_rc": offset, "slices": [0]}


def _native_femur(tmp_path, block: slice = slice(4, 8), offset=(60, 60)):
    """A femur whose own anchor territory carries a runtime-only native mask."""
    series, leg, territory = _native_bone(tmp_path)
    mask = _mask(block)
    territory["native_support"] = _support(mask, offset)
    coarse = writer.profile_territory(series, territory, leg, subject="femur")
    study = {
        "study_uid": territory["study_uid"],
        "series": [series],
        "leg_maps": {series["series_uid"]: leg},
        "anchors": {"femur": _anchor(series, territory)},
    }
    memory = {"cases": [_case(coarse, "femur")]}
    return study, memory, series, leg, territory, mask, coarse


def _forbid(*args, **kwargs):
    raise AssertionError("the v1 writer's refinement must never read a territory")


def _watch_refinement(monkeypatch) -> list:
    """Every ``refine_territory`` call from here on, made through to the real one."""
    calls: list = []

    def watched(*args, **kwargs):
        calls.append((args, kwargs))
        return REAL_REFINE_TERRITORY(*args, **kwargs)

    monkeypatch.setattr(writer, "refine_territory", watched)
    monkeypatch.setattr(writer, "refine_window", _forbid)
    return calls


def _scales(profile: dict) -> set[float]:
    fields = [parse_territory_bank_name(name) for name in profile["banks"]]
    assert all(field is not None for field in fields)
    return {field["scale_mm"] for field in fields if field is not None}


def _arrays_in(value, found=None) -> list:
    """Every numpy array or scalar reachable through plain dicts, lists and tuples."""
    found = [] if found is None else found
    if isinstance(value, (np.ndarray, np.generic)):
        found.append(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            _arrays_in(key, found)
            _arrays_in(item, found)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _arrays_in(item, found)
    return found


def _reachable(value, seen=None) -> set[int]:
    """The identity of every container and array reachable from a value."""
    seen = set() if seen is None else seen
    if id(value) in seen:
        return seen
    seen.add(id(value))
    if isinstance(value, dict):
        for key, item in value.items():
            _reachable(key, seen)
            _reachable(item, seen)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _reachable(item, seen)
    return seen


def _ask(study, objects, attempted=None, *, question="Fracture", deadline=None):
    return squint_pipeline._bounded_observation(
        {"object": "femur", "question": question},
        study,
        objects,
        set() if attempted is None else attempted,
        deadline,
    )


# ---------------------------------------------------------------------------
# production location: the native bone is read at 10 mm only
# ---------------------------------------------------------------------------


def test_production_location_reads_a_native_bone_at_10mm_and_makes_no_fine_call(
    tmp_path, monkeypatch
):
    study, memory, _series, _leg, territory, mask, coarse = _native_femur(tmp_path)
    calls = _watch_refinement(monkeypatch)

    located = locator.locate_objects(study, memory, refine_finalists=False)

    femur = located["objects"]["femur"]
    assert calls == []
    assert _scales(femur["profile"]) == {10.0}
    assert femur["profile"]["banks"] == coarse["banks"]
    assert [item["scale_mm"] for item in held_readings(femur["profile"])] == [10.0]
    evidence = femur["evidence"]
    assert evidence["profile_reading"] == "leg_tercile_territory_v2_10mm"
    assert evidence["fine_reading"] == {
        "policy": anatomy.FINE_READING_DEFERRED,
        "requested_at_location": 0,
        "deferred": 1,
    }
    assert located["evidence"]["fine_reading"] == anatomy.FINE_READING_DEFERRED
    # The record keeps the mask as an address and digest alone.
    record = femur["regions"][0]["territory"]
    assert femur["territories"] == [record]
    assert record["native_support"] is None
    assert record["native_support_address"]["mask_sha256"] == (
        hashlib.sha256(mask.tobytes()).hexdigest()
    )
    # The study keeps the original, by reference: the same mapping and the same mask.
    assert len(study[RETAINED]) == 1
    assert study[RETAINED][0] is territory
    assert study[RETAINED][0]["native_support"]["mask"] is mask
    original, why = anatomy.retained_native_territory(study, record)
    assert (original is territory, why) == (True, "retained")


@pytest.mark.parametrize(
    "options", [{}, {"refine_finalists": True}], ids=["default", "explicit_true"]
)
def test_the_default_and_explicit_true_locations_still_pair_at_location(
    tmp_path, monkeypatch, options
):
    study, memory, _series, _leg, territory, mask, _coarse = _native_femur(tmp_path)
    calls = _watch_refinement(monkeypatch)

    located = locator.locate_objects(study, memory, **options)

    femur = located["objects"]["femur"]
    assert len(calls) == 1
    assert calls[0][0][1] is territory
    assert calls[0][0][1]["native_support"]["mask"] is mask
    assert _scales(femur["profile"]) == {10.0, 2.0}
    assert {item["scale_mm"] for item in held_readings(femur["profile"])} == {10.0, 2.0}
    assert femur["evidence"]["profile_reading"] == (
        "leg_tercile_territory_v2_10mm_and_2mm"
    )
    assert "fine_reading" not in femur["evidence"]
    assert "fine_reading" not in located["evidence"]
    # Nothing is left to a question, so the study keeps nothing.
    assert RETAINED not in study
    # A question then finds the pair held and reads nothing more.
    held = _ask(study, located["objects"])
    assert (held["code"], held["reason"]) == (
        "already_measured",
        "paired_reading_already_held",
    )
    assert len(calls) == 1


def test_deferring_moves_no_candidate_territory_or_source_address(tmp_path):
    study, memory, *_ = _native_femur(tmp_path)

    paired = locator.locate_objects({**study}, memory)["objects"]["femur"]
    deferred = locator.locate_objects({**study}, memory, refine_finalists=False)[
        "objects"
    ]["femur"]

    for key in ("status", "regions", "territories"):
        assert deferred[key] == paired[key]
    assert [
        (item["series_uid"], item["window"], item["territory_origin"])
        for item in deferred["candidate_profiles"]
    ] == [
        (item["series_uid"], item["window"], item["territory_origin"])
        for item in paired["candidate_profiles"]
    ]
    for key in (
        "source",
        "location_route",
        "anchor",
        "resemblance_applied",
        "candidate_profiles_compared",
        "reading_territories",
        "duplicate_reading_territories",
        "reading_refusals",
        "other_anchor_territories",
        "spatial_constraints",
        "patient_coordinates_carried",
    ):
        assert deferred["evidence"][key] == paired["evidence"][key]
    # The 10 mm reading is the same one: same banks, same source address and mask digest.
    assert held_readings(deferred["profile"]) == [
        item for item in held_readings(paired["profile"]) if item["scale_mm"] == 10.0
    ]
    assert deferred["profile"]["banks"] == {
        name: counts
        for name, counts in paired["profile"]["banks"].items()
        if (parse_territory_bank_name(name) or {}).get("scale_mm") == 10.0
    }


def test_production_location_makes_no_2mm_call_for_any_object(monkeypatch):
    series, femur, _built, _profiles, memory = _v2_dependent()
    calls = _watch_refinement(monkeypatch)

    def study():
        return dependent._study(series, knee_side="left", anchors={"femur": femur})

    deferred = locator.locate_objects(study(), memory, refine_finalists=False)

    assert calls == []
    for name in ("femur", "medial_meniscus"):
        assert _scales(deferred["objects"][name]["profile"]) == {10.0}
    # The default location makes them: the native femur's, and the tied candidates'.
    locator.locate_objects(study(), memory)
    assert any(args[1].get("native_support") is not None for args, _ in calls)
    assert any(args[1].get("native_support") is None for args, _ in calls)


# ---------------------------------------------------------------------------
# the named question: one read, over the identical mask, then shared
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "offset", [(60, 60), [60, 60]], ids=["tuple_offset", "list_offset"]
)
def test_a_named_question_reads_the_native_territory_once_over_its_own_mask(
    tmp_path, monkeypatch, offset
):
    study, memory, series, leg, territory, mask, coarse = _native_femur(
        tmp_path, offset=offset
    )
    eager = locator.locate_objects({**study}, memory)["objects"]["femur"]["profile"]
    located = locator.locate_objects(study, memory, refine_finalists=False)
    objects = located["objects"]
    calls = _watch_refinement(monkeypatch)
    attempted: set = set()

    first = _ask(study, objects, attempted)

    assert first["code"] == "measured"
    assert (first["lens"], first["tile_mm"]) == ("physical_squint", 2.0)
    assert first["regions"] == [
        {"series_uid": series["series_uid"], "window": BONE_WINDOW}
    ]
    # One read, over the study's own series and leg map and the very mask of the location.
    assert len(calls) == 1
    (series_arg, territory_arg, leg_arg), kwargs = calls[0]
    assert series_arg is series
    assert leg_arg is leg
    assert territory_arg is territory
    assert territory_arg["native_support"]["mask"] is mask
    assert kwargs == {"subject": "femur", "tile_mm": 2.0}
    assert "femur" in attempted
    # What the eager pairing writes, bank for bank and reading for reading.
    profile = objects["femur"]["profile"]
    assert profile["banks"] == eager["banks"]
    assert held_readings(profile) == held_readings(eager)
    assert {item["scale_mm"] for item in held_readings(profile)} == {10.0, 2.0}
    # Over the mask, not over the territory's coarse object tiles it was rebuilt from.
    record = objects["femur"]["regions"][0]["territory"]
    direct = REAL_REFINE_TERRITORY(series, territory, leg, subject="femur")
    merged = writer.merge_profiles([coarse, direct], subject="femur")
    assert profile["banks"] == merged["banks"]
    occupancy = REAL_REFINE_TERRITORY(
        series, anatomy.territory_from_record(record), leg, subject="femur"
    )
    assert occupancy["banks"] != direct["banks"]
    json.dumps(first, allow_nan=False)

    # Shared: another question's request reads nothing more, and neither does a fresh
    # ask that remembers nothing, which finds the pair held by the same mask's identity.
    again = _ask(study, objects, attempted, question="Contusion")
    assert again == {"code": "shared_observation_already_available", "subject": "femur"}
    fresh = _ask(study, objects, question="Contusion")
    assert (fresh["code"], fresh["reason"]) == (
        "already_measured",
        "paired_reading_already_held",
    )
    assert len(calls) == 1
    assert profile["banks"] == eager["banks"]


def test_a_late_question_reads_nothing_and_leaves_the_mask_for_one_in_time(
    tmp_path, monkeypatch
):
    study, memory, *_ = _native_femur(tmp_path)
    objects = locator.locate_objects(study, memory, refine_finalists=False)["objects"]
    before = copy.deepcopy(objects["femur"]["profile"])
    calls = _watch_refinement(monkeypatch)
    attempted: set = set()

    late = _ask(study, objects, attempted, deadline=0.0)

    assert late["code"] == "deadline_before_zoom"
    assert calls == []
    assert attempted == set()
    assert objects["femur"]["profile"] == before
    assert len(study[RETAINED]) == 1
    assert _ask(study, objects, attempted)["code"] == "measured"
    assert len(calls) == 1


def test_a_later_location_replaces_what_an_earlier_one_kept(tmp_path):
    study, memory, *_ = _native_femur(tmp_path)

    locator.locate_objects(study, memory, refine_finalists=False)
    first = study[RETAINED]
    locator.locate_objects(study, memory, refine_finalists=False)
    # The same territory once, not twice: the study holds what the last location read.
    assert len(study[RETAINED]) == 1
    assert study[RETAINED] is not first
    # A location that pairs now leaves nothing to a question, and nothing from before.
    locator.locate_objects(study, memory)
    assert RETAINED not in study


def test_arrays_do_not_escape_the_located_object_or_the_saved_result(tmp_path):
    study, memory, _series, _leg, territory, mask, _coarse = _native_femur(tmp_path)
    located = locator.locate_objects(study, memory, refine_finalists=False)
    objects = located["objects"]
    observed = _ask(study, objects)

    assert observed["code"] == "measured"
    for saved in (located, objects, observed):
        json.dumps(saved, allow_nan=False)
        assert _arrays_in(saved) == []
        reach = _reachable(saved)
        for kept in (
            study[RETAINED],
            territory,
            territory["native_support"],
            territory["roles"],
            mask,
        ):
            assert id(kept) not in reach


# ---------------------------------------------------------------------------
# a support the study does not hold, or holds as another territory, is named
# ---------------------------------------------------------------------------


def _break(study, territory, how: str) -> str:
    """Spoil what the study kept; the reason the question must then name."""
    if how == "cache_removed":
        del study[RETAINED]
    elif how == "cache_empty":
        study[RETAINED] = []
    elif how == "cache_not_a_list":
        study[RETAINED] = {"femur": territory}
    elif how == "another_subject":
        study[RETAINED] = [{**territory, "subject": "tibia"}]
    elif how == "another_study":
        study[RETAINED] = [{**territory, "study_uid": "another-study"}]
    elif how == "another_series":
        study[RETAINED] = [{**territory, "series_uid": "another-series"}]
    elif how == "another_window":
        study[RETAINED] = [{**territory, "tile_window": [0, 1, 0, 5, 0, 5]}]
    elif how == "not_a_territory":
        study[RETAINED] = ["femur", None, 3]
    else:
        return _break_identity(study, territory, how)
    return "native_support_mask_not_retained"


def _break_identity(study, territory, how: str) -> str:
    """A territory at the record's address whose serialization is not the record's."""
    if how == "mask_changed_in_place":
        mask = territory["native_support"]["mask"]
        assert not mask[0, 1, 1]
        mask[0, 1, 1] = True
    elif how == "another_mask_at_the_same_address":
        study[RETAINED] = [
            {**territory, "native_support": _support(_mask(slice(8, 12)))}
        ]
    elif how == "same_mask_other_places":
        roles = territory["roles"].copy()
        roles[0, 3, 3] = ROLE_CONTEXT
        study[RETAINED] = [{**territory, "roles": roles}]
    elif how == "same_mask_other_shares":
        share = territory["object_share"].copy()
        share[0, 3, 3] = 0.125
        study[RETAINED] = [{**territory, "object_share": share}]
    elif how == "same_mask_other_provenance":
        study[RETAINED] = [{**territory, "provenance": {"another": True}}]
    elif how == "no_longer_a_valid_territory":
        study[RETAINED] = [{**territory, "roles": "not an array"}]
    else:
        raise AssertionError(how)
    return "native_support_mask_mismatch"


@pytest.mark.parametrize(
    "how",
    [
        "cache_removed",
        "cache_empty",
        "cache_not_a_list",
        "another_subject",
        "another_study",
        "another_series",
        "another_window",
        "not_a_territory",
        "mask_changed_in_place",
        "another_mask_at_the_same_address",
        "same_mask_other_places",
        "same_mask_other_shares",
        "same_mask_other_provenance",
        "no_longer_a_valid_territory",
    ],
)
def test_a_missing_or_mismatched_support_refuses_by_name_without_a_fine_read(
    tmp_path, monkeypatch, how
):
    study, memory, series, _leg, territory, _mask_kept, _coarse = _native_femur(
        tmp_path
    )
    objects = locator.locate_objects(study, memory, refine_finalists=False)["objects"]
    reason = _break(study, territory, how)
    before = copy.deepcopy(objects["femur"]["profile"])
    calls = _watch_refinement(monkeypatch)
    attempted: set = set()

    observed = _ask(study, objects, attempted)

    assert observed["code"] == "no_compatible_bounded_reading"
    assert observed["reason"] == "territory_unavailable"
    assert observed["unavailable_regions"] == [
        {"series_uid": series["series_uid"], "window": BONE_WINDOW, "reason": reason}
    ]
    assert calls == []
    assert objects["femur"]["profile"] == before
    assert attempted == set()
    json.dumps(observed, allow_nan=False)


def test_another_study_object_holds_no_support_for_the_located_record(
    tmp_path, monkeypatch
):
    study, memory, series, leg, *_ = _native_femur(tmp_path)
    objects = locator.locate_objects(study, memory, refine_finalists=False)["objects"]
    other = {
        "study_uid": study["study_uid"],
        "series": [series],
        "leg_maps": {series["series_uid"]: leg},
    }
    calls = _watch_refinement(monkeypatch)

    observed = _ask(other, objects)

    assert [item["reason"] for item in observed["unavailable_regions"]] == [
        "native_support_mask_not_retained"
    ]
    assert calls == []


def test_the_retained_territory_with_this_masks_identity_is_the_one_returned(
    tmp_path,
):
    _series, _leg, territory = _native_bone(tmp_path)
    first = {**territory, "native_support": _support(_mask(slice(4, 8)))}
    second = {**territory, "native_support": _support(_mask(slice(8, 12)))}
    study = {RETAINED: [first, second]}

    for wanted in (first, second):
        found, why = anatomy.retained_native_territory(
            study, anatomy.territory_record(wanted)
        )
        assert (found is wanted, why) == (True, "retained")
    # Same address as both, a mask neither holds: held at that address, but not this one.
    third = {**territory, "native_support": _support(_mask(slice(1, 3)))}
    unheld = anatomy.retained_native_territory(study, anatomy.territory_record(third))
    assert unheld == (None, "native_support_mask_mismatch")
    for not_a_study in (None, [], "study", {}):
        absent = anatomy.retained_native_territory(
            not_a_study, anatomy.territory_record(first)
        )
        assert absent == (None, "native_support_mask_not_retained")


# ---------------------------------------------------------------------------
# the production entry: location defers, a named question reads once
# ---------------------------------------------------------------------------


def _stub_module(monkeypatch, name: str, **members) -> types.ModuleType:
    module = types.ModuleType(name)
    vars(module).update(members)
    monkeypatch.setitem(sys.modules, name, module)
    return module


def test_infer_study_defers_a_native_bone_and_reads_it_once_for_the_question_that_asks(
    tmp_path, monkeypatch
):
    study, memory, _series, _leg, territory, mask, _coarse = _native_femur(tmp_path)
    uid = study["study_uid"]
    questions = tuple(
        types.SimpleNamespace(
            question_id=name, subject=f"diagnosis/{name}", objects=("femur",)
        )
        for name in ("Fracture", "Contusion")
    )

    def question_for(question_id):
        return next(item for item in questions if item.question_id == question_id)

    calls = _watch_refinement(monkeypatch)
    monkeypatch.setattr(
        writer, "read_study_squints", lambda root, study_uid, *, io_workers: study
    )
    _stub_module(
        monkeypatch,
        "knee.diagnosis.declarations",
        QUESTIONS=questions,
        question_for=question_for,
    )
    monkeypatch.setattr(squint_configurations, "question_for", question_for)
    _stub_module(
        monkeypatch,
        "knee.diagnosis.squint_contracts",
        combine_condition=lambda question_id, evidence: {
            "outcome": "open",
            "observation_requests": [{"question": question_id, "object": "femur"}],
        },
        rank_condition=lambda finding: {"value": 0.5},
    )
    recalls: list = []

    def recall(profile, memory, *, question, exclude_study_uid):
        if profile.get("subject") == "femur":
            recalls.append((question, _scales(profile), len(calls)))
        return {"outcome": "proposal", "case_terms": [], "speaking_calls": []}

    monkeypatch.setattr(locator, "recall_object", recall)

    record = squint_pipeline.infer_study(tmp_path, uid, {**memory, "revision": "r1"})

    # Squint and recall first: the first question's first recall holds the 10 mm reading.
    assert recalls[0] == ("Fracture", {10.0}, 0)
    work = record["work"]
    assert work["location_fine_readings"] == 0
    assert work["paired_fine_readings"] == 1
    assert work["bounded_zoom_runs"] == 1
    assert [item["code"] for item in record["observations"]] == [
        "measured",
        "shared_observation_already_available",
    ]
    # Only the named question earned the finer reading: once, over the very mask.
    assert len(calls) == 1
    assert calls[0][0][1] is territory
    assert calls[0][0][1]["native_support"]["mask"] is mask
    assert _scales(record["objects"]["femur"]["profile"]) == {10.0, 2.0}
    assert all(scales == {10.0, 2.0} for _q, scales, made in recalls if made)
    # The saved result is plain JSON and holds no array and no kept territory.
    json.dumps(record, allow_nan=False)
    assert _arrays_in(record) == []
    reach = _reachable(record)
    for kept in (study[RETAINED], territory, territory["native_support"], mask):
        assert id(kept) not in reach
