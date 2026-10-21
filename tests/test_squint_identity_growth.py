"""Two-sign intent of signed identity growth from one frozen parent.

CLASSICAL_AI_BUILD_DESIGN §§7, 7.1-7.2 and the OpenSpec change
``complete-signed-bootstrap-loop``: answering and admitting are different
decisions; an anatomical pass is a location law check; a round scores against
its frozen parent alone; the child keeps every signed record; a candidate's
whole study leaves its comparison across every record kind; an admission asserts
only the views that spoke. Each test pins one meaning in both signs, through
direct calls to the growth API, the identity reader and the CLI.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from knee.diagnosis.squint_bootstrap import (
    CALLS_SCHEMA,
    build_review,
    publish_seed_memory,
)
from knee.diagnosis.squint_identity import (
    IDENTITY_CASES_SCHEMA,
    SANITY_SCHEMA,
    TEACHING_SCHEMA,
    prepare_identity,
    recall_identity,
)
from knee.diagnosis.squint_identity_growth import (
    CHILD_DIRECTORY,
    DECISIONS_FILE,
    DECISIONS_SCHEMA,
    GROWTH_SCHEMA,
    READER,
    RECOGNITION_KIND,
    IdentityGrowthError,
    admission_decision,
    admission_from_recall,
    admission_scope,
    candidates_from_memory,
    exclusion_studies,
    grow_identity_memory,
    harvest_candidates,
    location_support,
    read_inference_records,
    record_sha256,
    represented_objects,
)
from knee.diagnosis.squint_locator import prepare_recall
from knee.diagnosis.squint_memory import (
    SCHEMA,
    _full_profile_from_validated_case,
    _json_sha256,
    full_profile_from_case,
    hydrate_full_profiles,
    load_memory_snapshot,
    save_memory,
)
from knee.diagnosis.squint_memory_view import memory_view
from knee.json_store import dump_json_atomic
from knee.study.tables import LABELS
from tests.test_squint_bootstrap import _product

ROOT = Path(__file__).resolve().parents[1]
SAG = ["Sagittal", "0", "0"]
COR = ["Coronal", "0", "0"]
PROCEDURE = "knee.squint-profile/scan-tercile-v1"
WINDOW = [0, 1, 0, 2, 0, 2]
INFERENCE_REVISION = "inference-memory-r1"
DECISION_KEYS = sorted(
    [
        "candidate_id",
        "study_uid",
        "subject",
        "state",
        "reason",
        "recognized_identity",
        "views",
        "support",
        "regions",
        "source",
    ]
)


def bank(view: list[str]) -> str:
    return (
        "squint/v2/view="
        + json.dumps(view, separators=(",", ":"))
        + "/role=object/metric=signal/direction=d/scale=10mm"
    )


def profile(subject: str, by_view) -> dict:
    return {
        "schema": "knee.squint-profile/v1",
        "subject": subject,
        "banks": {bank(view): list(counts) for view, counts in by_view},
        "source": {"procedure": PROCEDURE},
    }


def sanity(subject: str, status: str, *results: str) -> dict:
    """A knee.object-anatomical-sanity/v1 record shaped as the locator writes it."""
    checks = [
        {
            "rule_id": f"authored:{subject}:superior_to:tibia",
            "source": "docs/OBJECTS_AND_CONDITIONS.md §4",
            "subject": subject,
            "target": "tibia",
            "candidate_role": "subject",
            "axis": "z",
            "relation": "superior_to",
            "expected_relation": "strictly_after",
            "candidate_interval": [40.0, 80.0],
            "target_interval": [0.0, 30.0],
            "result": result,
            "candidate_subject": subject,
            "reference_subject": "tibia",
        }
        for result in results
    ]
    return {
        "schema": SANITY_SCHEMA,
        "status": status,
        "identity_assertion": None,
        "windows": [
            {
                "index": 0,
                "window": list(WINDOW),
                "address": list(WINDOW),
                "status": status,
                "eligible": True,
                "checks": checks,
                "series_uid": "series-sag",
            }
        ],
    }


def plausible(subject: str) -> dict:
    return sanity(subject, "plausible", "supported_strictly_after")


def unknown(subject: str) -> dict:
    return sanity(subject, "unknown", "unknown")


def contradicted(subject: str) -> dict:
    return sanity(subject, "contradicted", "reversed_strictly_after")


def located(subject: str, by_view, anatomy) -> dict:
    return {
        "status": "proposal",
        "profile": profile(subject, by_view),
        "regions": [
            {
                "series_uid": "series-sag",
                "view": {
                    "orientation": "Sagittal",
                    "fluid_sensitive": "0",
                    "fat_suppression": "0",
                },
                "window": list(WINDOW),
            }
        ],
        "sanity": anatomy,
        "evidence": {"source": "fixture"},
    }


def study_record(uid: str, objects: dict, revision: str = INFERENCE_REVISION) -> dict:
    """A knee.squint-study/v1 record as infer_study writes it, abridged."""
    return {
        "schema": "knee.squint-study/v1",
        "study_uid": uid,
        "memory_revision": revision,
        "study_status": "examined",
        "objects": objects,
        "identity_recall": {"outcome": "examined", "objects": {}},
        "questions": {},
        "values": {},
    }


def candidate(uid: str, subject: str, by_view, anatomy) -> dict:
    [item] = harvest_candidates(
        [study_record(uid, {subject: located(subject, by_view, anatomy)})]
    )
    return item


def _record(case_id: str, subject: str, study_uid: str, by_view) -> dict:
    return {
        "case_id": case_id,
        "study_uid": study_uid,
        "subject": subject,
        "condition_calls": {},
        "profile": profile(subject, by_view),
        "regions": [],
    }


def identity_memory(seeds, negatives=(), revision: str = "parent-r1") -> dict:
    """A valid squint memory of confirmed seeds and scoped ordinary negative cases.

    ``seeds`` are (case_id, subject, study_uid, by_view); ``negatives`` add the
    views their reject asserted.
    """
    cases = [_record(*seed) for seed in seeds]
    calls = [
        {
            "candidate_id": case["case_id"],
            "call": "confirm",
            "notes": "n",
            "reader": "fixture reviewer",
        }
        for case in cases
    ]
    teaching = {
        "schema": TEACHING_SCHEMA,
        "reader": "fixture reviewer",
        "confirmed_case_ids": [case["case_id"] for case in cases],
        "calls": calls,
    }
    memory = {
        "schema": SCHEMA,
        "revision": revision,
        "questions": list(LABELS),
        "cases": cases,
        "object_identity_teaching": teaching,
    }
    if negatives:
        records = []
        teaching["negative_case_ids"] = []
        teaching["negative_views"] = {}
        for case_id, subject, study_uid, by_view, views in negatives:
            records.append(_record(case_id, subject, study_uid, by_view))
            teaching["negative_case_ids"].append(case_id)
            teaching["negative_views"][case_id] = [list(view) for view in views]
            calls.append(
                {
                    "candidate_id": case_id,
                    "call": "reject",
                    "notes": "n",
                    "reader": "fixture reviewer",
                    "views": [list(view) for view in views],
                }
            )
        memory["object_identity_cases"] = {
            "schema": IDENTITY_CASES_SCHEMA,
            "cases": records,
        }
    return memory


def saved(tmp_path: Path, name: str, memory: dict):
    save_memory(memory, tmp_path / name)
    return load_memory_snapshot(tmp_path / name)


def decide(item: dict, memory: dict) -> dict:
    return admission_decision(item, memory)["decision"]


# A femur and a tibia seed that resemble each other: each one's envelope is 4/5.
ROUND_SEEDS = (
    ("a1", "femur", "sa", [(SAG, (3, 0, 0))]),
    ("t1", "tibia", "st", [(SAG, (2, 1, 0))]),
)
# A femur and a patella seed that share nothing: both envelopes are 0.
TWO_SEEDS = (
    ("a1", "femur", "sa", [(SAG, (3, 0, 0))]),
    ("b1", "patella", "sb", [(SAG, (0, 0, 3))]),
)
# A reviewer rejected this sagittal support as femur; study "sn" holds nothing else.
NEGATIVE = ("n1", "femur", "sn", [(SAG, (1, 2, 0))], [SAG])


# ------------------------------------------------------------- the decision


def test_identified_with_location_support_is_admitted_at_the_views_that_spoke():
    memory = identity_memory(ROUND_SEEDS)
    item = candidate("sx", "femur", [(SAG, (4, 0, 1))], plausible("femur"))
    scored = admission_decision(item, memory)
    decision = scored["decision"]
    assert sorted(decision) == DECISION_KEYS
    assert (decision["state"], decision["reason"]) == (
        "admitted",
        "identified_with_location_support",
    )
    assert decision["recognized_identity"] == "femur"
    assert decision["views"] == [SAG]
    [support] = decision["support"]
    assert support["establishes"] == "location_only"
    assert (support["rule_id"], support["axis"], support["result"]) == (
        "authored:femur:superior_to:tibia",
        "z",
        "supported_strictly_after",
    )
    assert support["candidate_interval"] == [40.0, 80.0]
    assert support["target_interval"] == [0.0, 30.0]
    assert scored["recall"]["outcome"] == "identified"
    assert scored["excluded_study_uid"] is None


def test_unknown_only_anatomy_keeps_a_proposal_even_when_recall_identifies():
    memory = identity_memory(ROUND_SEEDS)
    for anatomy in (unknown("femur"), None):
        scored = admission_decision(
            candidate("sx", "femur", [(SAG, (4, 0, 1))], anatomy), memory
        )
        # The legacy recall field says admitted; it is not a publication warrant.
        assert scored["recall"]["outcome"] == "identified"
        assert scored["recall"]["admitted"] is True
        decision = scored["decision"]
        assert (decision["state"], decision["reason"]) == (
            "proposal",
            "anatomy_unknown",
        )
        assert decision["recognized_identity"] == "femur"
        assert decision["views"] == [] and decision["support"] == []
    # A bare plausible status that records no supporting check establishes nothing.
    bare = candidate("sx", "femur", [(SAG, (4, 0, 1))], sanity("femur", "plausible"))
    decision = decide(bare, memory)
    assert (decision["state"], decision["reason"]) == (
        "proposal",
        "anatomy_support_unrecorded",
    )


def test_a_known_contradiction_blocks_and_one_reversed_check_is_enough():
    memory = identity_memory(ROUND_SEEDS)
    decision = decide(
        candidate("sx", "femur", [(SAG, (4, 0, 1))], contradicted("femur")), memory
    )
    assert (decision["state"], decision["reason"]) == (
        "blocked",
        "anatomy_contradicted",
    )
    mixed = sanity(
        "femur", "plausible", "supported_strictly_after", "reversed_strictly_after"
    )
    decision = decide(candidate("sx", "femur", [(SAG, (4, 0, 1))], mixed), memory)
    assert (decision["state"], decision["reason"]) == (
        "blocked",
        "anatomy_contradicted",
    )
    # Its pass is still recorded, as location only.
    assert [row["result"] for row in decision["support"]] == [
        "supported_strictly_after"
    ]


def test_a_pass_is_location_support_for_its_own_subject_only():
    tibia_pass = plausible("tibia")
    assert location_support(tibia_pass, "femur")["support"] == []
    assert len(location_support(tibia_pass, "tibia")["support"]) == 1
    asserted = {**plausible("femur"), "identity_assertion": "femur"}
    assert location_support(asserted, "femur")["status"] is None
    decision = decide(
        candidate("sx", "femur", [(SAG, (4, 0, 1))], tibia_pass),
        identity_memory(ROUND_SEEDS),
    )
    assert (decision["state"], decision["reason"]) == (
        "proposal",
        "anatomy_support_unrecorded",
    )


def test_a_negative_case_speaking_against_an_otherwise_identified_candidate_blocks_it():
    item = candidate("sr", "femur", [(SAG, (1, 2, 0))], plausible("femur"))
    assert decide(item, identity_memory(TWO_SEEDS))["state"] == "admitted"
    decision = decide(item, identity_memory(TWO_SEEDS, [NEGATIVE]))
    assert (decision["state"], decision["reason"]) == (
        "conflict",
        "identity_spoken_for_and_against",
    )
    assert decision["views"] == [] and decision["recognized_identity"] is None
    # The location pass is kept, as location only (OpenSpec: a plausible location
    # that a negative case opposes).
    assert [row["establishes"] for row in decision["support"]] == ["location_only"]


def test_a_negative_case_speaking_alone_is_named_opposed():
    item = candidate("sq", "femur", [(SAG, (1, 2, 0))], plausible("femur"))
    alone = decide(item, identity_memory(ROUND_SEEDS))
    assert (alone["state"], alone["reason"]) == ("proposal", "no_case_above_envelope")
    decision = decide(item, identity_memory(ROUND_SEEDS, [NEGATIVE]))
    assert (decision["state"], decision["reason"]) == (
        "opposed",
        "negative_case_speaks_against_proposed_identity",
    )
    assert decision["recognized_identity"] is None
    assert decision["support"][0]["establishes"] == "location_only"


def test_recognition_as_another_identity_is_a_conflict_naming_that_identity():
    memory = identity_memory(TWO_SEEDS, [NEGATIVE])
    decision = decide(
        candidate("sp", "femur", [(SAG, (0, 0, 3))], plausible("femur")), memory
    )
    assert (decision["state"], decision["reason"]) == (
        "conflict",
        "recognized_as_other_identity",
    )
    assert decision["recognized_identity"] == "patella"
    own = decide(
        candidate("sp", "patella", [(SAG, (0, 0, 3))], plausible("patella")), memory
    )
    assert (own["state"], own["recognized_identity"]) == ("admitted", "patella")


def test_a_study_known_only_through_a_negative_record_is_excluded():
    memory = identity_memory(TWO_SEEDS, [NEGATIVE])
    # Reading studies from ``cases`` alone, as the prototype did, misses "sn".
    assert {case["study_uid"] for case in memory["cases"]} == {"sa", "sb"}
    assert exclusion_studies(memory) == {"sa", "sb", "sn"}
    item = candidate("sn", "tibia", [(SAG, (1, 2, 0))], plausible("tibia"))
    scored = admission_decision(item, memory)
    assert scored["excluded_study_uid"] == "sn"
    assert scored["recall"]["negative_cases"] == []
    decision = scored["decision"]
    assert (decision["state"], decision["reason"]) == (
        "conflict",
        "recognized_as_other_identity",
    )
    assert decision["recognized_identity"] == "femur"
    # Unexcluded, the study's own negative would speak in its candidate's comparison.
    leaked = recall_identity(item["profile"], memory, sanity=item["sanity"])
    assert leaked["reason"] == "identity_spoken_for_and_against"
    assert prepare_identity(memory, exclude_study_uid="sn")["negative_case_count"] == 0


def test_an_object_the_parent_already_holds_in_either_sign_is_a_duplicate():
    memory = identity_memory(TWO_SEEDS, [NEGATIVE])
    assert represented_objects(memory)["objects"] == {
        ("sa", "femur"),
        ("sb", "patella"),
        ("sn", "femur"),
    }
    for uid in ("sa", "sn"):
        decision = decide(
            candidate(uid, "femur", [(SAG, (3, 0, 0))], plausible("femur")), memory
        )
        assert (decision["state"], decision["reason"]) == (
            "duplicate",
            "object_already_in_parent",
        )
    other = decide(
        candidate("sa", "tibia", [(SAG, (0, 0, 3))], plausible("tibia")), memory
    )
    assert other["state"] != "duplicate"
    same_id = {
        **candidate("sz", "tibia", [(SAG, (0, 0, 3))], plausible("tibia")),
        "case_id": "a1",
    }
    decision = decide(same_id, memory)
    assert (decision["state"], decision["reason"]) == (
        "duplicate",
        "case_id_already_in_parent",
    )


def _row(identity: str, speaks: bool, *views: list[str]) -> dict:
    return {
        "identity": identity,
        "speaks": speaks,
        "common_speaking_banks": [bank(view) for view in views],
    }


def test_scope_is_the_views_that_spoke_minus_any_view_a_negative_speaks_through():
    axial = ["Axial", "0", "0"]
    rows = [
        _row("femur", True, SAG, COR),
        _row("patella", True, axial),
        _row("femur", False, axial),
    ]
    recall = {"cases": rows, "negative_cases": [_row("femur", True, SAG)]}
    assert admission_scope(recall, "femur") == {"views": [COR]}
    quiet = {
        "cases": rows,
        "negative_cases": [_row("femur", False, SAG), _row("patella", True, COR)],
    }
    assert admission_scope(quiet, "femur") == {"views": [COR, SAG]}
    assert admission_scope({"cases": rows}, "femur") == {"views": [COR, SAG]}


def test_unresolved_or_malformed_scope_is_a_named_refusal_never_a_whole_case_call():
    unparsed = [
        {"identity": "femur", "speaks": True, "common_speaking_banks": ["not-a-bank"]}
    ]
    for recall in (
        {
            "cases": [_row("femur", True, SAG)],
            "negative_cases": [_row("femur", True, SAG)],
        },
        {"cases": unparsed},
        {"cases": [{"identity": "femur", "speaks": True, "common_speaking_banks": []}]},
        {"cases": [_row("femur", False, SAG)]},
        {"cases": "rows"},
        {},
    ):
        assert (
            admission_scope(recall, "femur")["refusal"] == "admission_scope_unresolved"
        )
    item = candidate("sx", "femur", [(SAG, (4, 0, 1))], plausible("femur"))
    identified = {"outcome": "identified", "identity": "femur", "negative_cases": []}
    decision = admission_from_recall(item, {**identified, "cases": unparsed})
    assert (decision["state"], decision["reason"]) == (
        "refused",
        "admission_scope_unresolved",
    )
    assert decision["views"] == []
    scoped = admission_from_recall(
        item, {**identified, "cases": [_row("femur", True, SAG)]}
    )
    assert (scoped["state"], scoped["views"]) == ("admitted", [SAG])


# ------------------------------------------------------------- candidates


def test_harvest_takes_each_located_profile_with_its_recorded_sanity_and_source():
    anatomy = plausible("femur")
    record = study_record(
        "s1",
        {
            "femur": located("femur", [(SAG, (4, 0, 1))], anatomy),
            "tibia": {"status": "unresolved_missing_reading", "profile": None},
        },
    )
    record["work"] = {"elapsed_seconds": math.nan}  # records are written allowing NaN
    [item] = harvest_candidates([record])
    assert item["case_id"] == f"located:s1:femur:{INFERENCE_REVISION}"
    assert (item["study_uid"], item["subject"]) == ("s1", "femur")
    assert item["profile"] == record["objects"]["femur"]["profile"]
    assert item["sanity"] == anatomy
    assert item["regions"] == [{"series_uid": "series-sag", "window": WINDOW}]
    assert item["source"] == {
        "kind": "squint-inference",
        "record_sha256": record_sha256(record),
        "record_sha256_scope": "decoded_json",
        "memory_revision": INFERENCE_REVISION,
    }
    assert "full_profile" not in item
    [pinned] = harvest_candidates([record], record_sha256s=["c" * 64])
    assert pinned["source"]["record_sha256"] == "c" * 64
    assert pinned["source"]["record_sha256_scope"] == "file_bytes"


def test_harvest_refuses_a_repeated_study_and_malformed_records_by_name():
    record = study_record("s1", {"femur": located("femur", [(SAG, (4, 0, 1))], None)})
    bad_window = copy.deepcopy(record)
    bad_window["objects"]["femur"]["regions"][0]["window"] = [0, 0, 0, 2, 0, 2]
    no_regions = copy.deepcopy(record)
    no_regions["objects"]["femur"]["regions"] = []
    for records, code in (
        ([record, copy.deepcopy(record)], "duplicate_study_record"),
        ([bad_window], "study_record_region_invalid"),
        ([no_regions], "study_record_regions_missing"),
        ([{**record, "schema": "other"}], "study_record_invalid"),
        ([{**record, "memory_revision": ""}], "study_record_invalid"),
    ):
        with pytest.raises(IdentityGrowthError) as info:
            harvest_candidates(records)
        assert info.value.code == code
    with pytest.raises(IdentityGrowthError) as info:
        harvest_candidates([record], record_sha256s=["c" * 63])
    assert info.value.code == "record_sha256s_invalid"


# ---------------------------------------------------------- rounds and children


def test_admissions_never_speak_in_their_own_round_and_the_next_round_hears_them(
    tmp_path: Path,
):
    parent = saved(tmp_path, "parent", identity_memory(ROUND_SEEDS))
    x = candidate("sx", "femur", [(SAG, (4, 0, 1))], plausible("femur"))
    w = candidate("sw", "femur", [(SAG, (4, 0, 2))], plausible("femur"))
    receipt = grow_identity_memory(parent, [x, w], tmp_path / "round-1")
    assert receipt["outcome"] == "published"
    assert receipt["admitted_case_ids"] == [x["case_id"]]
    document = json.loads((tmp_path / "round-1" / DECISIONS_FILE).read_text())
    by_id = {row["candidate_id"]: row for row in document["decisions"]}
    # Each candidate was scored against the frozen parent alone.
    for item in (x, w):
        assert (
            by_id[item["case_id"]]
            == admission_decision(item, parent.memory)["decision"]
        )
    assert (by_id[w["case_id"]]["state"], by_id[w["case_id"]]["reason"]) == (
        "proposal",
        "no_case_above_envelope",
    )
    child = load_memory_snapshot(tmp_path / "round-1" / CHILD_DIRECTORY)
    assert prepare_identity(child.memory)["seed_count"] == 3
    heard = recall_identity(w["profile"], child.memory, sanity=w["sanity"])
    assert heard["identity"] == "femur"
    [row] = [row for row in heard["cases"] if row["case_id"] == x["case_id"]]
    assert row["speaks"] is True
    assert row["lineage"]["call"]["reader"] == READER
    second = grow_identity_memory(child, [w], tmp_path / "round-2")
    assert second["admitted_case_ids"] == [w["case_id"]]
    grandchild = load_memory_snapshot(tmp_path / "round-2" / CHILD_DIRECTORY).memory
    [admitted] = [c for c in grandchild["cases"] if c["case_id"] == w["case_id"]]
    assert admitted["identity_growth"]["speaking_case_ids"] == [x["case_id"]]
    assert admitted["identity_growth"]["parent_manifest_sha256"] == child.sha256
    rounds = grandchild["object_identity_growth"]["rounds"]
    assert [entry["parent_manifest_sha256"] for entry in rounds] == [
        parent.sha256,
        child.sha256,
    ]


def test_each_admission_is_recognition_derived_with_lineage_and_no_clinical_call(
    tmp_path: Path,
):
    parent = saved(tmp_path, "parent", identity_memory(ROUND_SEEDS))
    x = candidate("sx", "femur", [(SAG, (4, 0, 1))], plausible("femur"))
    receipt = grow_identity_memory(parent, [x], tmp_path / "grown")
    data = (tmp_path / "grown" / DECISIONS_FILE).read_bytes()
    assert receipt["decisions_sha256"] == hashlib.sha256(data).hexdigest()
    child = load_memory_snapshot(tmp_path / "grown" / CHILD_DIRECTORY).memory
    [case] = [case for case in child["cases"] if case["case_id"] == x["case_id"]]
    assert case["condition_calls"] == {}
    assert "full_profile" not in case and "presentation_scope" not in case
    assert (case["profile"], case["regions"]) == (x["profile"], x["regions"])
    assert case["teaching_source"] == {
        "kind": RECOGNITION_KIND,
        "parent_manifest_sha256": parent.sha256,
    }
    lineage = case["identity_growth"]
    assert lineage["independent_confirmation"] is False
    assert lineage["parent_manifest_sha256"] == parent.sha256
    assert lineage["speaking_case_ids"] == ["a1"]
    assert lineage["source"] == x["source"]
    assert lineage["decision"]["views"] == [SAG]
    assert lineage["decision"]["support"][0]["establishes"] == "location_only"
    teaching = child["object_identity_teaching"]
    [call] = [row for row in teaching["calls"] if row["candidate_id"] == x["case_id"]]
    assert (call["call"], call["views"], call["reader"]) == ("confirm", [SAG], READER)
    assert teaching["confirmed_case_ids"] == ["a1", "t1", x["case_id"]]
    assert child["object_identity_growth"]["schema"] == GROWTH_SCHEMA
    [entry] = child["object_identity_growth"]["rounds"]
    assert entry["decisions_sha256"] == receipt["decisions_sha256"]
    assert entry["admitted_case_ids"] == [x["case_id"]]
    assert child["revision"].startswith(parent.memory["revision"] + "+identity-growth-")
    # Condition recall and every population view still read the child.
    assert prepare_recall(child)["outcome"] == "prepared"
    view = memory_view(child, exclude_study_uids=("sx",))
    assert x["case_id"] not in [row["case_id"] for row in view["cases"]]


def test_a_round_without_admissions_writes_decisions_and_publishes_no_child(
    tmp_path: Path,
):
    parent = saved(tmp_path, "parent", identity_memory(ROUND_SEEDS))
    w = candidate("sw", "femur", [(SAG, (4, 0, 2))], plausible("femur"))
    receipt = grow_identity_memory(parent, [w], tmp_path / "quiet")
    assert (receipt["outcome"], receipt["child"]) == ("no_admissions", None)
    assert [path.name for path in (tmp_path / "quiet").iterdir()] == [DECISIONS_FILE]
    only = grow_identity_memory(
        parent,
        [candidate("sx", "femur", [(SAG, (4, 0, 1))], plausible("femur"))],
        tmp_path / "decisions",
        decisions_only=True,
    )
    assert only["outcome"] == "decisions_only" and only["admitted_case_ids"]
    assert [path.name for path in (tmp_path / "decisions").iterdir()] == [
        DECISIONS_FILE
    ]


def test_a_round_refuses_by_name_and_writes_nothing(tmp_path: Path):
    parent = saved(tmp_path, "parent", identity_memory(ROUND_SEEDS))
    x = candidate("sx", "femur", [(SAG, (4, 0, 1))], plausible("femur"))
    (tmp_path / "taken").mkdir()
    plain = identity_memory(ROUND_SEEDS)
    del plain["object_identity_teaching"]
    for arguments, code in (
        ((parent, [x, copy.deepcopy(x)], tmp_path / "twice"), "duplicate_candidate_id"),
        ((parent, [x], tmp_path / "taken"), "output_exists"),
        ((parent, [x], tmp_path / "parent" / "inside"), "output_path_unsafe"),
        ((parent.memory, [x], tmp_path / "raw"), "invalid_parent_snapshot"),
        (
            (saved(tmp_path, "plain", plain), [x], tmp_path / "untaught"),
            "parent_identity_teaching_missing",
        ),
    ):
        with pytest.raises(IdentityGrowthError) as info:
            grow_identity_memory(*arguments)
        assert info.value.code == code
        assert not arguments[2].exists() or arguments[2] == tmp_path / "taken"


# -------------------------------------- a signed parent with full payloads

SIGNED = (
    ("study-a", "femur", ((SAG, (3, 0, 0)), (COR, (3, 0, 0)))),
    ("study-b", "patella", ((SAG, (0, 0, 3)), (COR, (0, 0, 3)))),
    ("study-c", "femur", ((SAG, (1, 2, 0)), (COR, (3, 0, 0)))),
    ("study-d", "patella", ((SAG, (3, 0, 0)), (COR, (0, 0, 3)))),
    ("study-e", "femur", ((SAG, (3, 0, 0)), (COR, (3, 0, 0)))),
)
FA, PB, FC, PD, FE = (f"squint-case:{uid}:{subject}" for uid, subject, _ in SIGNED)
CONDITION = {"femur": "ACL", "patella": "PF OA"}


@pytest.fixture
def signed(tmp_path: Path) -> SimpleNamespace:
    """A five-study catalogue and its signed parent; every H5 product is deleted.

    The parent confirms FA and PB, rejects FC on the sagittal view (a femur
    negative), and rejects PD sagittally while calling that facet femur (an
    alternative positive). FE stays uncalled.
    """
    products = tmp_path / "products"
    products.mkdir()
    cases, sources = [], {}
    for uid, subject, by_view in SIGNED:
        product = products / f"{uid}.h5"
        manifest, record = _product(product, uid, (subject,))
        composition = manifest["object_composition"]
        digest = hashlib.sha256(product.read_bytes()).hexdigest()
        sources[uid] = {
            "product_path": str(product.resolve()),
            "product_sha256": digest,
            "layout_fingerprint": composition["layout_fingerprint"],
            "carrier_identity": composition["carrier_identity"],
            "source_roots": {},
            "full_profile_subjects": [subject],
        }
        banks = {f"coarse/{subject}/signal": [5, 0, 3]}
        banks.update({bank(view): list(counts) for view, counts in by_view})
        cases.append(
            {
                "case_id": f"squint-case:{uid}:{subject}",
                "study_uid": uid,
                "subject": subject,
                "condition_calls": {CONDITION[subject]: 1},
                "presentation_scope": {
                    CONDITION[subject]: "positive_condition_presentation"
                },
                "question_roles": {CONDITION[subject]: "implicated"},
                "label_attribution": {},
                "profile": {
                    "schema": "knee.squint-profile/v1",
                    "subject": subject,
                    "banks": banks,
                    "source": {"procedure": PROCEDURE},
                },
                "regions": [],
                "full_profile": {
                    "subject": subject,
                    "mode": "full",
                    "scope": f"object:{subject}",
                    "count_layout_id": record["count_layout_id"],
                    "reference_set_identity": record["reference_set_identity"],
                    "carrier_identity": composition["carrier_identity"],
                    "layout_fingerprint": composition["layout_fingerprint"],
                    "product_record_sha256": _json_sha256(record),
                },
                "full_source": {
                    "product_path": str(product.resolve()),
                    "product_sha256": digest,
                    "study_uid": uid,
                    "source_roots": {},
                },
                "teaching_source": {"kind": "official_train_csv_label"},
            }
        )
    catalogue = {
        "schema": SCHEMA,
        "revision": "growth-fixture-catalogue",
        "questions": list(LABELS),
        "procedure": {"id": "knee.squint-ternary/v1"},
        "source_identities": sources,
        "cases": cases,
    }
    save_memory(hydrate_full_profiles(catalogue, products), tmp_path / "catalogue")
    snapshot = load_memory_snapshot(tmp_path / "catalogue")
    review = build_review(snapshot.memory, snapshot.sha256, [FA, PB, FC, PD])
    for item in review["candidates"]:
        if item["candidate_id"] in (FC, PD):
            item["evidence"] = {
                "panels": [
                    {
                        "view": dict(
                            zip(
                                ("orientation", "fluid_sensitive", "fat_suppression"),
                                view,
                                strict=True,
                            )
                        ),
                        "image_state": "read",
                        "support_state": "drawn",
                    }
                    for view in (SAG, COR)
                ]
            }
    pin = hashlib.sha256(json.dumps(review, sort_keys=True).encode("utf-8")).hexdigest()
    calls = {
        "schema": CALLS_SCHEMA,
        "review_sha256": pin,
        "reader": "reader-one",
        "calls": [
            {"candidate_id": FA, "call": "confirm", "notes": "n"},
            {"candidate_id": PB, "call": "confirm", "notes": "n"},
            {"candidate_id": FC, "call": "reject", "notes": "n", "views": [SAG]},
            {
                "candidate_id": PD,
                "call": "reject",
                "notes": "n",
                "views": [SAG],
                "also_positive": [{"identity": "femur", "views": [SAG]}],
            },
        ],
    }
    publish_seed_memory(snapshot, review, calls, pin, tmp_path / "parent")
    parent = load_memory_snapshot(tmp_path / "parent")
    for product in products.glob("*.h5"):
        product.unlink()
    return SimpleNamespace(catalogue=snapshot, parent=parent, root=tmp_path)


def test_growth_keeps_every_signed_record_and_the_next_reader_hears_the_negatives(
    signed,
):
    parent = signed.parent
    before = copy.deepcopy(parent.memory)
    x = candidate(
        "study-x", "femur", [(SAG, (3, 0, 0)), (COR, (3, 0, 0))], plausible("femur")
    )
    y = candidate(
        "study-y", "femur", [(SAG, (1, 2, 0)), (COR, (3, 0, 0))], plausible("femur")
    )
    receipt = grow_identity_memory(parent, [x, y], signed.root / "grown")
    assert receipt["state_counts"] == {"admitted": 1, "conflict": 1}
    document = json.loads((signed.root / "grown" / DECISIONS_FILE).read_text())
    by_id = {row["candidate_id"]: row for row in document["decisions"]}
    assert by_id[x["case_id"]]["views"] == [COR, SAG]
    assert by_id[y["case_id"]]["reason"] == "identity_spoken_for_and_against"
    child = load_memory_snapshot(signed.root / "grown" / CHILD_DIRECTORY).memory
    # The frozen parent is untouched, in memory and on disk.
    assert parent.memory == before
    assert load_memory_snapshot(parent.path).sha256 == parent.sha256
    assert child["cases"][: len(before["cases"])] == before["cases"]
    assert child["object_identity_cases"] == before["object_identity_cases"]
    teaching, parent_teaching = (
        child["object_identity_teaching"],
        before["object_identity_teaching"],
    )
    for key in (
        "negative_case_ids",
        "negative_views",
        "negatives_not_written",
        "alternative_positives",
        "reader",
        "review_sha256",
        "reviewed_candidate_ids",
    ):
        assert teaching[key] == parent_teaching[key]
    assert (
        teaching["calls"][: len(parent_teaching["calls"])] == parent_teaching["calls"]
    )
    for table, key in (
        ("full_profile_payloads", "payloads"),
        ("full_profile_contexts", "contexts"),
    ):
        assert child[table][key] == before[table][key]
    assert child["source_identities"] == before["source_identities"]
    [case] = [case for case in child["cases"] if case["case_id"] == x["case_id"]]
    assert case["identity_growth"]["speaking_case_ids"] == sorted(
        [FA, f"{PD}::also_positive::femur"]
    )
    # Offline: no product is left, and every signed record still reads in full.
    for record in child["object_identity_cases"]["cases"]:
        full = _full_profile_from_validated_case(
            child, record, record["full_profile"], record["subject"]
        )
        assert full.source_id == record["study_uid"]
    prepared = prepare_identity(child)
    assert (
        prepared["seed_count"],
        prepared["negative_case_count"],
        prepared["alternative_positive_count"],
    ) == (4, 2, 1)
    # The next round's reader still meets the parent's -1 on its own view.
    heard = recall_identity(y["profile"], child, prepared=prepared)
    assert heard["outcome"] == "unresolved_conflict"
    assert FC in [row["case_id"] for row in heard["negative_cases"] if row["speaks"]]
    held_out = memory_view(child, exclude_study_uids=("study-c",))
    assert FC not in [
        row["case_id"] for row in held_out["object_identity_cases"]["cases"]
    ]
    assert (
        prepare_identity(child, exclude_study_uid="study-c")["negative_case_count"] == 1
    )
    assert prepare_recall(child)["outcome"] == "prepared"


def test_a_candidate_memory_case_enters_as_its_source_holds_it(signed):
    items = candidates_from_memory(
        signed.catalogue,
        candidate_ids=[FE, FA, FC],
        sanity_by_case_id={FE: plausible("femur")},
    )
    receipt = grow_identity_memory(signed.parent, items, signed.root / "from-memory")
    document = json.loads((signed.root / "from-memory" / DECISIONS_FILE).read_text())
    states = {
        row["candidate_id"]: (row["state"], row["reason"])
        for row in document["decisions"]
    }
    assert states == {
        FE: ("admitted", "identified_with_location_support"),
        FA: ("duplicate", "case_id_already_in_parent"),
        # A rejected support never returns as a positive of its own case.
        FC: ("duplicate", "case_id_already_in_parent"),
    }
    assert receipt["admitted_case_ids"] == [FE]
    child = load_memory_snapshot(signed.root / "from-memory" / CHILD_DIRECTORY).memory
    [case] = [case for case in child["cases"] if case["case_id"] == FE]
    original = next(c for c in signed.catalogue.memory["cases"] if c["case_id"] == FE)
    assert {key: value for key, value in case.items() if key != "identity_growth"} == (
        original
    )
    assert case["identity_growth"]["source"]["kind"] == "candidate-memory"
    assert (
        case["identity_growth"]["source"]["manifest_sha256"] == signed.catalogue.sha256
    )
    # Its paired full profile travelled with it and reads offline.
    assert full_profile_from_case(child, case).source_id == "study-e"
    assert (
        child["source_identities"]["study-e"]
        == (signed.catalogue.memory["source_identities"]["study-e"])
    )
    [plain] = candidates_from_memory(signed.catalogue, candidate_ids=[FE])
    assert admission_decision(plain, signed.parent.memory)["decision"]["reason"] == (
        "anatomy_unknown"
    )


# --------------------------------------------------------------------- CLI


def _cli():
    path = ROOT / "scripts" / "squint_object_bootstrap.py"
    spec = importlib.util.spec_from_file_location("squint_object_bootstrap_grow", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MOD = _cli()


def _inference(tmp_path: Path, name: str, records: list[dict]) -> Path:
    for record in records:
        dump_json_atomic(
            tmp_path / name / "studies" / (record["study_uid"] + ".json"),
            record,
            compression_preset=0,
        )
    return tmp_path / name


def test_cli_decisions_only_writes_the_frozen_schema_and_publishes_nothing(
    tmp_path: Path, capsys
):
    parent = saved(tmp_path, "parent", identity_memory(ROUND_SEEDS))
    record = study_record(
        "sx",
        {
            "femur": located("femur", [(SAG, (4, 0, 1))], plausible("femur")),
            "tibia": located("tibia", [(SAG, (0, 0, 3))], unknown("tibia")),
        },
    )
    record["work"] = {"elapsed_seconds": math.nan}
    directory = _inference(tmp_path, "inference", [record])
    [(read_back, digest)] = read_inference_records(directory)
    assert read_back["study_uid"] == "sx"
    output = tmp_path / "decisions"
    result = MOD.main(
        [
            "grow",
            "--parent",
            str(tmp_path / "parent"),
            "--inference",
            str(directory),
            "--output",
            str(output),
            "--decisions-only",
        ]
    )
    assert (result["action"], result["outcome"], result["child"]) == (
        "grow",
        "decisions_only",
        None,
    )
    assert [path.name for path in output.iterdir()] == [DECISIONS_FILE]
    data = (output / DECISIONS_FILE).read_bytes()
    document = json.loads(data)
    assert sorted(document) == ["decisions", "parent", "schema"]
    assert document["schema"] == DECISIONS_SCHEMA
    assert document["parent"] == {
        "manifest_sha256": parent.sha256,
        "revision": parent.memory["revision"],
    }
    assert all(sorted(row) == DECISION_KEYS for row in document["decisions"])
    by_subject = {row["subject"]: row for row in document["decisions"]}
    assert by_subject["femur"]["state"] == "admitted"
    assert by_subject["tibia"]["state"] == "proposal"
    file_sha256 = hashlib.sha256(
        (directory / "studies" / "sx.json.xz").read_bytes()
    ).hexdigest()
    assert digest == file_sha256
    assert by_subject["femur"]["source"] == {
        "kind": "squint-inference",
        "record_sha256": file_sha256,
        "record_sha256_scope": "file_bytes",
        "memory_revision": INFERENCE_REVISION,
    }
    assert by_subject["femur"]["regions"] == [
        {"series_uid": "series-sag", "window": WINDOW}
    ]
    printed = json.loads(capsys.readouterr().out)
    assert printed["decisions_sha256"] == hashlib.sha256(data).hexdigest()


def test_cli_publishes_the_child_beside_its_decisions_and_refuses_overwrite(
    tmp_path: Path,
):
    saved(tmp_path, "parent", identity_memory(ROUND_SEEDS))
    record = study_record(
        "sx", {"femur": located("femur", [(SAG, (4, 0, 1))], plausible("femur"))}
    )
    directory = _inference(tmp_path, "inference", [record])
    output = tmp_path / "grown"
    arguments = [
        "grow",
        "--parent",
        str(tmp_path / "parent"),
        "--inference",
        str(directory),
        "--output",
        str(output),
    ]
    result = MOD.main(arguments)
    assert result["outcome"] == "published"
    assert sorted(path.name for path in output.iterdir()) == [
        DECISIONS_FILE,
        CHILD_DIRECTORY,
    ]
    child = load_memory_snapshot(output / CHILD_DIRECTORY)
    assert child.sha256 == result["child"]["sha256"]
    assert result["child"]["identity_preparation"]["seed_count"] == 3
    with pytest.raises(SystemExit) as info:
        MOD.main(arguments)
    assert str(info.value) == "output_exists"
    assert load_memory_snapshot(output / CHILD_DIRECTORY).sha256 == child.sha256


def test_cli_refuses_a_parent_without_identity_teaching(tmp_path: Path):
    plain = identity_memory(ROUND_SEEDS)
    del plain["object_identity_teaching"]
    save_memory(plain, tmp_path / "plain")
    record = study_record(
        "sx", {"femur": located("femur", [(SAG, (4, 0, 1))], plausible("femur"))}
    )
    directory = _inference(tmp_path, "inference", [record])
    with pytest.raises(SystemExit) as info:
        MOD.main(
            [
                "grow",
                "--parent",
                str(tmp_path / "plain"),
                "--inference",
                str(directory),
                "--output",
                str(tmp_path / "out"),
            ]
        )
    assert str(info.value) == "parent_identity_teaching_missing"
    assert not (tmp_path / "out").exists()
