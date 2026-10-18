"""The integration corrections: a bone is its marrow, the joint is between identified bones, and the
study's objects are described, grouped and kept by one output."""

import copy
from types import SimpleNamespace
from typing import Any, cast

import numpy as np

from knee.collapse import bones as B
from knee.collapse.observations import describe_objects
from knee.receipt import merged_receipt
from scripts import run_interiors as run


def territories():
    """Two lens territories on a 10 x 10 plane: 1 the left half, 2 the right half."""
    labels = np.zeros((10, 10), dtype=int)
    labels[:, :5] = 1
    labels[:, 5:] = 2
    return labels


def test_a_territory_that_is_mostly_not_marrow_is_not_the_bone():
    labels = territories()
    places = np.zeros((10, 10), dtype=bool)
    places[:, :5] = True  # the carried outline covers the whole of territory 1
    available = np.ones((10, 10), dtype=bool)
    nothing = np.zeros((10, 10), dtype=bool)
    body = np.zeros((10, 10), dtype=bool)
    body[:3, :5] = True  # the marrow body is a corner of it: the rest is soft tissue
    leak = B.name_territory(labels, available, places, nothing, body)
    assert leak.code == B.NOT_MARROW and not leak.region.any()
    body[:, :5] = True  # the marrow fills the territory: identified
    assert (
        B.name_territory(labels, available, places, nothing, body).code == B.IDENTIFIED
    )
    # exactly half is not "most": the same majority rule as `carried_bone`
    body[:] = False
    body[:5, :5] = True
    assert (
        B.name_territory(labels, available, places, nothing, body).code == B.NOT_MARROW
    )
    # no marrow body measured: the old behaviour stays (the caller decides what it asks)
    assert B.name_territory(labels, available, places, nothing).code == B.IDENTIFIED
    assert B.NOT_MARROW in B.OUTCOMES


def stub(slice_index, planes):
    arrays: dict[str, Any] = {}
    for bone, (slices, outcomes) in planes.items():
        arrays[f"a3_{bone}_plane_slices"] = np.asarray(slices, dtype=np.int32)
        arrays[f"a3_{bone}_plane_outcome"] = np.asarray(
            [B.OUTCOMES.index(o) for o in outcomes], dtype=np.int8
        )
    return cast(
        Any,
        SimpleNamespace(record={"slice_index": slice_index}, arrays=arrays),
    )


def test_the_joint_is_asked_only_where_both_bones_were_identified_natively():
    own = stub(
        4,
        {
            "femur": ([1, 6, 9], [B.IDENTIFIED, B.NOT_MARROW, B.IDENTIFIED]),
            "tibia": ([1, 6, 8], [B.IDENTIFIED, B.IDENTIFIED, B.HOLDING_MOST]),
        },
    )
    # the middle slice is the bootstrap's naming; 6 and 8, 9 are named for one bone only
    assert run.bones_identified_at(own, None) == {1, 4}


def test_no_bone_profile_in_the_pair_is_unknown_not_unidentified():
    bare = cast(Any, SimpleNamespace(record={"slice_index": 2}, arrays={}))
    assert run.bones_identified_at(bare, None) is None
    assert run.bones_identified_at(bare, bare) is None


def row(obj, provenance, kind, support, code="identified", series="s1", slices=(3,)):
    return {
        "object": obj,
        "provenance": provenance,
        "kind": kind,
        "series_uid": series,
        "view": ["Sagittal", "0", "0"],
        "slices": list(slices),
        "code": code,
        "count": 7,
        "off_plane_mm": 0.0,
        "support": support,
        "note": "n",
        "artifact": "a.npz",
        "row": None,
        "label": None,
    }


def test_the_objects_are_grouped_by_object_provenance_kind_and_property():
    records = [
        {
            "observations": [
                row("femur", "native", "resolved", "a1_objects"),
                row(
                    "femur",
                    "native",
                    "reading",
                    "a3_bone_plane_labels",
                    "tie",
                    slices=(5,),
                ),
                row(
                    "femur", "projected", "target", "a1_objects", "target", series="s2"
                ),
                row("femur", "laid", "resolved", "a3_femur_laid_region", series="s3"),
            ],
            "observations_unresolved": [
                {"object": "femur", "provenance": "laid", "code": "no_partner"},
                {"object": "tibia", "provenance": "native", "code": "no_body"},
            ],
        },
        {},  # a record with no observations contributes nothing and does not fail
    ]
    got = describe_objects(records)
    assert list(got) == ["femur", "tibia"]
    femur = got["femur"]
    assert femur["native_series"] == [
        "s1"
    ]  # only a native resolved one names the series
    assert set(femur["observations"]) == {"native", "projected", "laid"}
    assert set(femur["observations"]["native"]) == {"resolved", "reading"}
    assert "target" in femur["observations"]["projected"]
    assert "resolved" not in femur["observations"]["projected"]  # never a boundary
    reading = femur["observations"]["native"]["reading"]["a3_bone_plane_labels"][0]
    assert reading["code"] == "tie" and reading["slices"] == [5]
    assert (
        reading["artifact"] == "a.npz"
    )  # addressable: a reference, not a copy of pixels
    assert femur["outcomes"]["tie"] == 1
    # what was not read is a named unresolved saying, never an absence and never a resolved one
    assert femur["unresolved"] == {"laid": {"no_partner": 1}}
    assert got["tibia"]["observations"] == {} and got["tibia"]["native_series"] == []
    assert got["tibia"]["unresolved"] == {"native": {"no_body": 1}}


def test_declared_anatomy_catalogue_keeps_unobserved_features_explicit():
    records = [{"observations": [row("femur", "native", "resolved", "a1_objects")]}]
    got = describe_objects(records, ("femur", "tibia", "patella"))
    assert set(got) == {"femur", "tibia", "patella"}
    assert got["femur"]["native_series"] == ["s1"]
    assert got["femur"]["unresolved"] == {}
    for name in ("tibia", "patella"):
        assert got[name]["observations"] == {}
        assert got[name]["native_series"] == []
        assert got[name]["outcomes"] == {}
        assert got[name]["unresolved"] == {"pipeline": {"no_observation_record": 1}}


def test_empty_study_still_accounts_for_each_declared_feature():
    got = describe_objects([], ("femur", "tibia"))
    assert set(got) == {"femur", "tibia"}
    assert all(
        v["unresolved"] == {"pipeline": {"no_observation_record": 1}}
        for v in got.values()
    )


def test_the_receipt_keeps_each_studys_objects_and_replaces_only_its_own():
    first = merged_receipt(None, {}, "A", ["s"], [], {}, None, {"femur": {}})
    second = merged_receipt(first, {}, "B", ["t"], [], {}, None, {"tibia": {}})
    assert set(second["objects"]) == {"A", "B"}
    again = merged_receipt(second, {}, "A", ["s"], [], {}, None, {"patella": {}})
    assert again["objects"] == {"A": {"patella": {}}, "B": {"tibia": {}}}
    # a receipt that carries none (the main one) has no such key
    assert "objects" not in merged_receipt(None, {}, "A", ["s"], [], {}, None)


def test_the_retinacula_slice_is_chosen_through_the_patellas_whole_observed_extent():
    first = np.array([1.0, 2.0, 3.0])
    feed = {"retinacula_feed": [{"centre_of_every_section_lps": [4.0, 5.0, 6.0]}]}
    named = cast(Any, SimpleNamespace(record={"patella": feed}))
    bare = cast(Any, SimpleNamespace(record={}))
    with_feed = run.retinacula_centre([bare, named], first)
    assert with_feed is not None and with_feed.tolist() == [4.0, 5.0, 6.0]
    # no section named: the first identification's centre, as before
    assert run.retinacula_centre([bare], first) is first
    assert run.retinacula_centre([bare], None) is None


def test_the_drivers_keep_writes_the_objects_into_the_interiors_receipt_only(tmp_path):
    import json

    result = {
        "study_uid": "S",
        "series_uids": ["s"],
        "records": [],
        "unread": {},
        "telemetry": {"events": {}},
        "objects": {"femur": {"observations": {}, "outcomes": {}}},
        "main_keys": ["s"],
        "main_records": [],
        "main_unread": {},
    }
    run_dir, main_dir = tmp_path / "run", tmp_path / "main"
    run_dir.mkdir()
    main_dir.mkdir()
    run.keep(result, run_dir, main_dir)
    kept = json.loads((run_dir / "receipt.json").read_text())
    assert list(kept["objects"]["S"]) == ["femur"]
    assert "objects" not in json.loads((main_dir / "receipt.json").read_text())


def test_missing_observation_uses_its_own_retained_definition_refusal_only():
    records = [
        {
            "series_uid": "s",
            "assignments": {
                "codes": {
                    "joint_capsule": "abstain_no_femur",
                    "patella": "identified",
                    "synovium": "not_named_on_this_slice",
                    "unrelated": "abstain_not_this_object",
                }
            },
        }
    ]
    got = describe_objects(records, ("joint_capsule", "patella", "synovium"))
    assert got["joint_capsule"]["unresolved"] == {"native": {"abstain_no_femur": 1}}
    assert got["joint_capsule"]["observations"] == {}
    for name in ("patella", "synovium"):
        assert got[name]["unresolved"] == {"pipeline": {"no_observation_record": 1}}


def test_own_slice_silences_are_retained_without_alias_guessing_or_duplicate_counts():
    records = [
        {"series_uid": "s", "assignments": {"codes": {"lcl": "abstain_no_fibula"}}}
    ]
    got = describe_objects(
        records,
        ("lcl", "acl", "medial_patellar_retinaculum"),
        {
            "s:lcl": "abstain_no_fibula",
            "other:lcl": "geometry_unreadable",
            "s:medial_patellar_retinaculum": "abstain_patella_off_the_slices",
            "unscoped": "not_an_addressed_part",
        },
    )
    assert got["lcl"]["unresolved"] == {
        "native": {"abstain_no_fibula": 1, "geometry_unreadable": 1}
    }
    assert got["medial_patellar_retinaculum"]["unresolved"] == {
        "native": {"abstain_patella_off_the_slices": 1}
    }
    assert got["acl"]["unresolved"] == {"pipeline": {"no_observation_record": 1}}
    assert got["lcl"]["outcomes"] == {} and got["lcl"]["native_series"] == []


def test_existing_observation_and_structured_refusal_are_preserved():
    records = [
        {
            "series_uid": "s",
            "observations": [row("femur", "native", "resolved", "a1_objects")],
            "observations_unresolved": [
                {"object": "tibia", "provenance": "native", "code": "no_body"}
            ],
        }
    ]
    before = describe_objects(records, ("femur", "tibia"))
    after = describe_objects(
        records,
        ("femur", "tibia"),
        {"s:femur": "abstain_old", "s:tibia": "abstain_old"},
    )
    assert {
        name: {key: value for key, value in item.items() if key != "search_refusals"}
        for name, item in after.items()
    } == {
        name: {key: value for key, value in item.items() if key != "search_refusals"}
        for name, item in before.items()
    }
    assert after["femur"]["search_refusals"] == [
        {"series_uid": "s", "code": "abstain_old"}
    ]
    assert after["tibia"]["search_refusals"] == [
        {"series_uid": "s", "code": "abstain_old"}
    ]


def test_definition_decisions_and_search_refusals_survive_observations():
    records = [
        {
            "series_uid": "s1",
            "view": ["Sagittal", "0", "0"],
            "slice_index": 4,
            "artifact": "s1.npz",
            "main_slice": {"object": "femur"},
            "assignments": {
                "codes": {
                    "joint_capsule": "abstain_no_femur",
                    "patella": "not_named_on_this_slice",
                }
            },
            "observations": [row("joint_capsule", "native", "reading", "a2_parts")],
            "observations_unresolved": [
                {
                    "object": "joint_capsule",
                    "provenance": "native",
                    "code": "edge_unreadable",
                }
            ],
        },
        {
            "series_uid": "s2",
            "view": ["Coronal", "0", "0"],
            "slice_index": 9,
            "artifact": "s2.npz",
            "main_slice": {"object": "tibia"},
            "assignments": {
                "codes": {
                    "joint_capsule": "abstain_no_femur",
                    "unrelated": "abstain_other",
                }
            },
        },
        {
            "series_uid": "s3",
            "assignments": {"codes": {"joint_capsule": "identified"}},
        },
    ]
    silences = {
        "s2:joint_capsule": "geometry_unreadable",
        "s1:joint_capsule": "no_own_slice_support",
        "s3:unrelated": "must_not_copy",
        "unscoped": "must_not_copy",
    }
    original_records = copy.deepcopy(records)
    original_silences = copy.deepcopy(silences)

    got = describe_objects(records, ("joint_capsule", "patella"), silences)

    assert (
        got["joint_capsule"]["observations"]["native"]["reading"]["a2_parts"][0]["code"]
        == "identified"
    )
    assert got["joint_capsule"]["unresolved"] == {"native": {"edge_unreadable": 1}}
    assert got["joint_capsule"]["definition_decisions"] == [
        {
            "series_uid": "s1",
            "view": ["Sagittal", "0", "0"],
            "slice_index": 4,
            "artifact": "s1.npz",
            "main_object": "femur",
            "code": "abstain_no_femur",
        },
        {
            "series_uid": "s2",
            "view": ["Coronal", "0", "0"],
            "slice_index": 9,
            "artifact": "s2.npz",
            "main_object": "tibia",
            "code": "abstain_no_femur",
        },
        {
            "series_uid": "s3",
            "view": None,
            "slice_index": None,
            "artifact": None,
            "main_object": None,
            "code": "identified",
        },
    ]
    assert got["joint_capsule"]["search_refusals"] == [
        {"series_uid": "s1", "code": "no_own_slice_support"},
        {"series_uid": "s2", "code": "geometry_unreadable"},
    ]
    assert got["patella"]["definition_decisions"] == [
        {
            "series_uid": "s1",
            "view": ["Sagittal", "0", "0"],
            "slice_index": 4,
            "artifact": "s1.npz",
            "main_object": "femur",
            "code": "not_named_on_this_slice",
        }
    ]
    assert got["patella"]["search_refusals"] == []
    assert records == original_records and silences == original_silences
