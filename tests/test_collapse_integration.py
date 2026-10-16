"""The integration corrections: a bone is its marrow, the joint is between identified bones, and the
study's objects are described, grouped and kept by one output."""

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
