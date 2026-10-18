from typing import cast

from knee.collapse.anatomical_relations import relationships_for
from knee.collapse.anatomy_map import MAP_OBJECTS
from knee.collapse.observations import describe_objects

SOURCE = "docs/OBJECTS_AND_CONDITIONS.md §4"
BASIS = "anatomical_definition"


def test_catalogue_matches_object_slots_and_keeps_definition_contract():
    got = relationships_for(MAP_OBJECTS)
    assert set(got) == set(MAP_OBJECTS)
    rows = [row for subject_rows in got.values() for row in subject_rows]
    assert len(rows) == len(
        {
            (
                row["subject"],
                row["predicate"],
                tuple(cast(list[str], row["targets"])),
                row["qualifier"],
            )
            for row in rows
        }
    )
    assert all(row["source"] == SOURCE for row in rows)
    assert all(row["basis"] == BASIS for row in rows)
    assert all(
        set(row) == {"subject", "predicate", "targets", "qualifier", "source", "basis"}
        and row["subject"] in MAP_OBJECTS
        and set(cast(list[str], row["targets"])).issubset(MAP_OBJECTS)
        for row in rows
    )

    by_subject = {subject: rows for subject, rows in got.items() if rows}
    joint = by_subject["joint"][0]
    assert (joint["predicate"], joint["targets"]) == ("between", ["femur", "tibia"])
    assert all(row["predicate"] != "attaches_to" for row in by_subject["joint"])
    assert any(
        row["predicate"] == "attaches_to"
        and row["targets"] == ["medial_meniscus"]
        and row["qualifier"] == "deep layer"
        for row in by_subject["mcl"]
    )
    assert any(
        row["predicate"] == "anterior_to" and row["targets"] == ["popliteal_vein"]
        for row in by_subject["popliteal_artery"]
    )
    assert all("measured" not in row and "status" not in row for row in rows)


def test_a_missing_subject_or_any_target_suppresses_only_that_relation():
    got = relationships_for({"mcl", "femur", "tibia"})
    assert [(row["subject"], row["targets"]) for row in got["mcl"]] == [
        ("mcl", ["femur", "tibia"])
    ]
    assert got["femur"] == [] and got["tibia"] == []
    assert relationships_for({"femur", "tibia"}) == {"femur": [], "tibia": []}
    assert relationships_for({"joint", "femur"}) == {"joint": [], "femur": []}


def test_empty_or_unrelated_names_keep_only_requested_empty_slots():
    assert relationships_for(()) == {}
    assert relationships_for({"unassigned", "not_an_object"}) == {
        "unassigned": [],
        "not_an_object": [],
    }


def test_each_call_returns_fresh_json_safe_mutable_records():
    first = relationships_for({"joint", "femur", "tibia"})
    cast(list[str], first["joint"][0]["targets"]).append("invented")
    first["joint"].append({"subject": "invented"})
    second = relationships_for({"joint", "femur", "tibia"})
    assert second["joint"][0]["targets"] == ["femur", "tibia"]
    assert second["joint"][0]["basis"] == BASIS
    assert second["femur"] == [] and second["tibia"] == []


def test_object_description_adds_definition_links_without_replacing_evidence():
    address = {
        "series_uid": "s1",
        "view": ["Coronal", "1", "1"],
        "slices": [3],
        "code": "identified",
        "count": 4,
        "off_plane_mm": 0.0,
        "support": "a1_objects",
        "artifact": "study/s1.npz",
        "row": None,
        "label": None,
    }
    records = [
        {
            "series_uid": "s1",
            "view": ["Coronal", "1", "1"],
            "slice_index": 3,
            "artifact": "study/s1.npz",
            "observations": [
                {
                    **address,
                    "object": "joint",
                    "provenance": "native",
                    "kind": "resolved",
                }
            ],
            "observations_unresolved": [
                {"object": "femur", "provenance": "native", "code": "abstain_example"}
            ],
            "assignments": {
                "codes": {"joint": "identified", "femur": "abstain_example"}
            },
        }
    ]
    names = ("joint", "femur", "tibia", "air", "medial_meniscus")
    got = describe_objects(records, names, {"s2:air": "abstain_not_on_view"})
    assert set(got) == set(names)
    assert got["joint"]["observations"]["native"]["resolved"]["a1_objects"] == [address]
    assert got["femur"]["unresolved"] == {"native": {"abstain_example": 1}}
    assert got["air"]["search_refusals"] == [
        {"series_uid": "s2", "code": "abstain_not_on_view"}
    ]
    assert got["tibia"]["unresolved"] == {"pipeline": {"no_observation_record": 1}}
    assert got["air"]["anatomical_relations"] == []
    assert got["femur"]["anatomical_relations"] == []
    joint_relation = got["joint"]["anatomical_relations"]
    assert joint_relation[0]["targets"] == ["femur", "tibia"]
    assert joint_relation[0]["basis"] == BASIS
    assert "measured" not in joint_relation[0] and "status" not in joint_relation[0]


def test_empty_descriptions_keep_catalogue_slots_and_attach_definition_links():
    names = ("joint", "femur", "tibia", "air")
    got = describe_objects([], names)
    assert set(got) == set(names)
    assert got["joint"]["anatomical_relations"][0]["targets"] == ["femur", "tibia"]
    assert got["joint"]["anatomical_relations"][0]["basis"] == BASIS
    assert all(
        got[name]["anatomical_relations"] == [] for name in ("femur", "tibia", "air")
    )
    assert all(
        got[name]["unresolved"] == {"pipeline": {"no_observation_record": 1}}
        for name in names
    )
