"""`axial_joint_fluid` says the patellofemoral recess fluid the retinacular rule already selected.

Direct production calls on the two source addresses (the pointed `a3_recess_plane_*` stacks and the
original retinacula main record), with real `StudyMap` offers and real `PlaneFrame` geometry. Nothing
here reads an image: every image-reading function is made to fail.
"""

from __future__ import annotations

import copy
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from knee.collapse.physical import PlaneFrame
from knee.collapse.study_map import StudyMap
from scripts import run_interiors as run

PROOF = "1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149"
UID = "axial-fs"
SHAPE = (12, 14)
MEDIAL, LATERAL = run.RETINACULA
NO_FLUID = "abstain_no_fluid_recess_at_the_patella"
NO_WALL = "abstain_no_outboard_wall_minimum"
EMPTY_UNION = "abstain_no_joint_fluid_in_patellofemoral_recesses"
UNITS = "a4_axial_joint_fluid"


def box(r0: int, r1: int, c0: int, c1: int) -> np.ndarray:
    mask = np.zeros(SHAPE, dtype=bool)
    mask[r0:r1, c0:c1] = True
    return mask


def oblique(z: float, spacing: tuple[float, float] = (1.0, 1.0)) -> PlaneFrame:
    """An axial slice tilted about the first image axis: its normal is not along the patient's z."""
    return PlaneFrame.from_dicom((0.0, 0.0, z), (1, 0, 0, 0, 0.8, 0.6), spacing)


def stub(
    slices: list[Any],
    view: str = "Axial",
    thick: list[Any] | None = None,
) -> Any:
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid=UID),
        slice_thickness_mm=thick if thick is not None else [3.0] * len(slices),
        slices=slices,
    )
    return SimpleNamespace(
        series=series,
        record={"series_uid": UID, "view": [view, "1", "1"], "observations": []},
        arrays={"acquired_plane": np.zeros(SHAPE)},
    )


@pytest.fixture(autouse=True)
def stub_frames_and_no_image_reads(monkeypatch):
    monkeypatch.setattr(run, "plane_frame", lambda series, z: series.slices[z])

    def forbidden(*_args, **_kwargs):
        raise AssertionError("an image was read")

    for name in (
        "read_part_slice",
        "retinacula_on",
        "retinacula_slice",
        "lens_of",
        "field_of",
        "seen_native",
        "read_recess",
        "recess_axial_plane",
        "interior_regions",
    ):
        monkeypatch.setattr(run, name, forbidden)


def pointed_rows(rows: list[dict]) -> tuple[dict, dict]:
    """The axial series' own record/arrays as `name_the_recess` leaves them: a middle plane first, then
    the retained rows. Each row: slice, code, codes, medial and lateral masks."""
    planes: list[dict] = [
        {"slice": 0, "middle": True, "code": "bootstrap", "codes": {}}
    ]
    for row in rows:
        planes.append(
            {
                "slice": row["slice"],
                "middle": False,
                "code": row.get("code", "read"),
                "codes": row.get("codes", {}),
            }
        )
    record = {
        "series_uid": UID,
        "view": ["Axial", "1", "1"],
        "observations": [],
        "recess": {"kind": "retinacula", "pointed_planes": planes},
    }
    arrays = {
        "acquired_plane": np.zeros(SHAPE),
        "a3_recess_plane_slices": np.asarray([r["slice"] for r in rows], np.int32),
        "a3_recess_plane_medial_recess": np.stack(
            [r.get("medial", np.zeros(SHAPE, bool)) for r in rows]
        ),
        "a3_recess_plane_lateral_recess": np.stack(
            [r.get("lateral", np.zeros(SHAPE, bool)) for r in rows]
        ),
        "a3_recess_plane_medial_wall": np.stack([box(0, 1, 0, 1)] * len(rows)),
    }
    return record, arrays


def main_record(
    z: int, codes: dict[str, str], medial: np.ndarray, lateral: np.ndarray
) -> tuple[dict, dict]:
    record = {
        "series_uid": UID,
        "view": ["Axial", "1", "1"],
        "slice_index": z,
        "assignments": {"codes": codes},
        "main_slice": {"object": "patellar_retinaculum"},
    }
    arrays = {
        "acquired_plane": np.zeros(SHAPE),
        "a2_retinacula_positive_inner_selected_recess": medial,
        "a2_retinacula_negative_inner_selected_recess": lateral,
        f"a2_{MEDIAL}": box(0, 1, 0, 1),
    }
    return record, arrays


def both(code: str, other: str | None = None) -> dict[str, str]:
    return {MEDIAL: code, LATERAL: other or code}


def test_pointed_rows_union_overlap_once_and_addresses_agree():
    own = stub([oblique(0.0), oblique(3.0), oblique(6.0)])
    medial, lateral = box(2, 6, 1, 6), box(4, 9, 4, 9)  # overlap rows 4-5, cols 4-5
    record, arrays = pointed_rows(
        [
            {
                "slice": 1,
                "codes": both("identified", NO_WALL),
                "medial": medial,
                "lateral": lateral,
            },
            {
                "slice": 2,
                "codes": both("identified"),
                "medial": box(0, 2, 0, 2),
                "lateral": box(0, 2, 5, 7),
            },
        ]
    )
    before_arrays = copy.deepcopy(arrays)
    before_record = copy.deepcopy(record)
    found, missing = run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        None,
        pointed=True,
    )
    assert missing == []
    union = arrays[UNITS]
    assert union.dtype == np.bool_
    assert union.shape == (2, *SHAPE)  # same rows as a3_recess_plane_slices
    assert np.array_equal(union[0], medial | lateral)
    overlap = int(np.count_nonzero(medial & lateral))
    assert overlap == 4
    assert int(union[0].sum()) == medial.sum() + lateral.sum() - overlap
    assert [o.row for o in found] == [0, 1]
    assert [o.slices for o in found] == [(1,), (2,)]
    assert [o.count for o in found] == [int(union[0].sum()), int(union[1].sum())]
    first = found[0]
    assert (first.object, first.provenance, first.kind, first.code) == (
        "joint_fluid",
        "native",
        "resolved",
        "identified",
    )
    assert first.series_uid == UID and first.view == ("Axial", "1", "1")
    assert first.support == UNITS and first.label is None
    assert first.off_plane_mm == 0.0
    assert first.artifact == str(run.artifact_of(PROOF, record))
    assert "union" in first.note and "overlap" in first.note and "volume" in first.note
    # nothing prior is touched; only the new support and the one diagnostic record key are added
    for key, value in before_arrays.items():
        assert np.array_equal(arrays[key], value)
    assert set(arrays) == set(before_arrays) | {UNITS}
    assert {k: v for k, v in record.items() if k != UNITS} == before_record
    assert record[UNITS]["path"] == "pointed"
    assert [r["status"] for r in record[UNITS]["rows"]] == ["fluid", "fluid"]
    assert record[UNITS]["rows"][0]["pixels"] == first.count
    assert record["observations"] == []  # the caller merges, not this function


def test_main_record_union_is_two_dimensional_and_has_no_row():
    own = stub([oblique(0.0), oblique(3.0)])
    medial, lateral = box(1, 5, 1, 5), box(3, 7, 3, 7)
    record, arrays = main_record(1, both("identified"), medial, lateral)
    found, missing = run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        None,
        pointed=False,
    )
    assert missing == []
    assert arrays[UNITS].shape == SHAPE and arrays[UNITS].dtype == np.bool_
    assert np.array_equal(arrays[UNITS], medial | lateral)
    (obs,) = found
    assert obs.row is None and obs.label is None and obs.slices == (1,)
    assert obs.support == UNITS
    assert obs.artifact == str(run.artifact_of(PROOF, record))
    assert obs.artifact.endswith("-patellar_retinaculum.npz")
    assert np.array_equal(
        arrays["a2_retinacula_positive_inner_selected_recess"], medial
    )
    assert np.array_equal(
        arrays["a2_retinacula_negative_inner_selected_recess"], lateral
    )
    assert record[UNITS]["path"] == "main"


def test_one_side_success_and_wall_minimum_failure_are_still_fluid():
    own = stub([oblique(0.0)])
    medial = box(2, 6, 2, 6)
    record, arrays = pointed_rows(
        [
            {
                "slice": 0,
                "codes": both("identified", NO_FLUID),
                "medial": medial,
            }
        ]
    )
    found, missing = run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        None,
        pointed=True,
    )
    assert missing == [] and len(found) == 1
    assert np.array_equal(arrays[UNITS][0], medial)
    assert found[0].kind == "resolved"
    # no wall at all on either side, yet both pockets were selected: fluid is not tied to the wall
    lateral = box(7, 10, 8, 12)
    record, arrays = pointed_rows(
        [
            {
                "slice": 0,
                "codes": both(NO_WALL),
                "medial": medial,
                "lateral": lateral,
            }
        ]
    )
    found, missing = run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        None,
        pointed=True,
    )
    assert missing == []
    assert found[0].code == "identified" and found[0].kind == "resolved"
    assert found[0].count == int(medial.sum() + lateral.sum())
    main, main_arrays = main_record(0, both(NO_WALL, NO_FLUID), medial, box(0, 0, 0, 0))
    found, missing = run.axial_joint_fluid(
        own,
        main,
        main_arrays,
        PROOF,
        None,
        pointed=False,
    )
    assert missing == [] and found[0].count == int(medial.sum())


def test_prerequisite_failure_measured_empty_and_unavailable_are_three_things():
    own = stub([oblique(0.0), oblique(3.0), oblique(6.0)])
    record, arrays = pointed_rows(
        [
            {"slice": 0, "codes": both("abstain_no_patella_carried")},
            {"slice": 1, "codes": both(NO_FLUID)},
            {"slice": 2, "code": "unreadable_geometry", "codes": {}},
        ]
    )
    found, missing = run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        None,
        pointed=True,
    )
    codes = [m.code for m in missing]
    assert codes == ["abstain_no_patella_carried", "unreadable_geometry"]
    assert all(m.object == "joint_fluid" and m.provenance == "native" for m in missing)
    # the one measured-empty row is a reading with a count of zero, not an unresolved reason
    (empty,) = found
    assert (empty.kind, empty.code, empty.count, empty.row, empty.slices) == (
        "reading",
        EMPTY_UNION,
        0,
        1,
        (1,),
    )
    assert [r["status"] for r in record[UNITS]["rows"]] == [
        "unavailable",
        "measured_empty",
        "not_read",
    ]
    assert not arrays[UNITS].any()
    # every reading missing the interval, the femur or the patella surfaces under its own name
    for prerequisite in (
        "abstain_no_femur_carried",
        "abstain_no_patellar_region",
        "abstain_no_femoral_peak",
        "abstain_no_posterior_interval",
    ):
        record, arrays = pointed_rows([{"slice": 0, "codes": both(prerequisite)}])
        found, missing = run.axial_joint_fluid(
            own,
            record,
            arrays,
            PROOF,
            None,
            pointed=True,
        )
        assert found == [] and [m.code for m in missing] == [prerequisite]
    main, main_arrays = main_record(
        0, both("abstain_no_patella_carried"), box(0, 0, 0, 0), box(0, 0, 0, 0)
    )
    found, missing = run.axial_joint_fluid(
        own,
        main,
        main_arrays,
        PROOF,
        None,
        pointed=False,
    )
    assert found == [] and [m.code for m in missing] == ["abstain_no_patella_carried"]


def test_record_level_refusals_propagate_without_crashing():
    own = stub([oblique(0.0)])
    record = {
        "series_uid": UID,
        "recess": {"code": "abstain_leg_runs_in_the_plane"},
    }
    arrays: dict[str, np.ndarray] = {"acquired_plane": np.zeros(SHAPE)}
    found, missing = run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        None,
        pointed=True,
    )
    assert found == [] and [m.code for m in missing] == [
        "abstain_leg_runs_in_the_plane"
    ]
    assert UNITS not in arrays and UNITS not in record
    found, missing = run.axial_joint_fluid(
        own,
        {"series_uid": UID},
        dict(arrays),
        PROOF,
        None,
        pointed=True,
    )
    assert [m.code for m in missing] == ["recess_not_read"]
    # nothing pointed is unknown, not empty
    record = {
        "series_uid": UID,
        "recess": {"kind": "retinacula", "pointed_planes": []},
    }
    found, missing = run.axial_joint_fluid(
        own,
        record,
        {**arrays, "a3_recess_plane_slices": np.zeros(0, np.int32)},
        PROOF,
        None,
        pointed=True,
    )
    assert found == [] and [m.code for m in missing] == [
        "no_axial_plane_pointed_to_read_it"
    ]
    found, missing = run.axial_joint_fluid(
        own,
        {"series_uid": UID},
        {},
        PROOF,
        None,
        pointed=True,
    )
    assert found == [] and [m.code for m in missing] == ["acquired_plane_unavailable"]
    found, missing = run.axial_joint_fluid(
        own,
        {"series_uid": UID},
        dict(arrays),
        PROOF,
        None,
        pointed=False,
    )
    assert [m.code for m in missing] == ["retinacula_record_unavailable"]


def test_missing_and_malformed_arrays_are_never_an_empty_or_nonempty_measurement():
    own = stub([oblique(0.0), oblique(3.0)])
    good = box(2, 5, 2, 5)
    for damage, reason in (
        ("missing", "selected_recess_mask_unavailable"),
        ("integer", "selected_recess_mask_unavailable"),
        ("shape", "selected_recess_mask_unavailable"),
        ("rows", "selected_recess_mask_unavailable"),
    ):
        record, arrays = pointed_rows(
            [
                {"slice": 0, "codes": both("identified", NO_FLUID), "medial": good},
                {"slice": 1, "codes": both("identified", NO_FLUID), "medial": good},
            ]
        )
        key = "a3_recess_plane_medial_recess"
        if damage == "missing":
            del arrays[key]
        elif damage == "integer":
            arrays[key] = arrays[key].astype(np.int8)
        elif damage == "shape":
            arrays[key] = arrays[key][:, :-1]
        else:
            arrays[key] = arrays[key][:1]
        found, missing = run.axial_joint_fluid(
            own,
            record,
            arrays,
            PROOF,
            None,
            pointed=True,
        )
        assert found == [], damage
        assert [m.code for m in missing] == [reason, reason], damage
        assert not arrays[UNITS].any()
        assert all(r["status"] == "unavailable" for r in record[UNITS]["rows"])
    # a readable side keeps its fluid when the other side's array is malformed (set union of readable)
    record, arrays = pointed_rows(
        [{"slice": 0, "codes": both("identified"), "medial": good, "lateral": good}]
    )
    arrays["a3_recess_plane_lateral_recess"] = arrays[
        "a3_recess_plane_lateral_recess"
    ].astype(np.int8)
    found, missing = run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        None,
        pointed=True,
    )
    assert [m.code for m in missing] == [f"{LATERAL}:selected_recess_mask_unavailable"]
    assert found[0].count == int(good.sum())
    assert record[UNITS]["rows"][0]["sides"][LATERAL] == "unavailable"


def test_code_and_mask_that_disagree_do_not_become_a_measurement():
    own = stub([oblique(0.0)])
    full = box(1, 4, 1, 4)
    # wall code says a recess was selected but the mask is empty
    record, arrays = pointed_rows([{"slice": 0, "codes": both(NO_WALL)}])
    found, missing = run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        None,
        pointed=True,
    )
    assert found == [] and missing[0].code == "wall_code_disagrees_with_selected_recess"
    # the rule said "no recess" yet a mask is nonempty: not accepted as fluid or as empty
    record, arrays = pointed_rows(
        [{"slice": 0, "codes": both(NO_FLUID), "medial": full, "lateral": full}]
    )
    found, missing = run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        None,
        pointed=True,
    )
    assert found == [] and missing[0].code == "wall_code_disagrees_with_selected_recess"
    assert not arrays[UNITS].any()
    # codes absent altogether
    record, arrays = pointed_rows([{"slice": 0, "codes": {}, "medial": full}])
    found, missing = run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        None,
        pointed=True,
    )
    assert found == [] and missing[0].code == "wall_code_unavailable"


def test_row_counts_must_agree_with_the_retained_planes():
    own = stub([oblique(0.0), oblique(3.0)])
    record, arrays = pointed_rows(
        [{"slice": 0, "codes": both(NO_FLUID)}, {"slice": 1, "codes": both(NO_FLUID)}]
    )
    arrays["a3_recess_plane_slices"] = np.asarray([0], np.int32)
    found, missing = run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        None,
        pointed=True,
    )
    assert found == [] and [m.code for m in missing] == ["recess_plane_rows_disagree"]
    assert UNITS not in arrays
    record, arrays = pointed_rows(
        [{"slice": 0, "codes": both(NO_FLUID)}, {"slice": 1, "codes": both(NO_FLUID)}]
    )
    arrays["a3_recess_plane_slices"] = np.asarray([1, 0], np.int32)
    found, missing = run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        None,
        pointed=True,
    )
    assert [m.code for m in missing] == ["recess_plane_rows_disagree"]


def test_nonaxial_series_say_nothing_and_are_untouched():
    for view in ("Sagittal", "Coronal"):
        own = stub([oblique(0.0)], view=view)
        record, arrays = pointed_rows([{"slice": 0, "codes": both(NO_FLUID)}])
        record["view"] = [view, "1", "1"]
        snapshot = copy.deepcopy((record, arrays))
        for pointed in (True, False):
            found, missing = run.axial_joint_fluid(
                own, record, arrays, PROOF, None, pointed=pointed
            )
            assert (found, missing) == ([], [])
        assert UNITS not in arrays and UNITS not in record
        assert record == snapshot[0]


def test_map_offers_actual_planes_with_distinct_pixel_scales_and_keeps_ties():
    # three slices of one series, each with its own oblique frame and its own pixel scale
    frames = [
        oblique(0.0, (0.5, 0.5)),
        oblique(3.0, (0.8, 1.2)),
        oblique(6.0, (1.0, 1.0)),
        oblique(9.0, (1.0, 1.0)),
    ]
    own = stub(frames, thick=[3.0, 3.0, 3.0, None])
    pocket = box(2, 5, 2, 5)  # 9 pixels
    record, arrays = pointed_rows(
        [
            {"slice": 0, "codes": both("identified", NO_FLUID), "medial": pocket},
            {"slice": 1, "codes": both("identified", NO_FLUID), "medial": pocket},
            {"slice": 2, "codes": both(NO_FLUID)},  # measured empty: no offer
            {"slice": 3, "codes": both("identified", NO_FLUID), "medial": pocket},
        ]
    )
    mapping = run.MapContext(StudyMap(knee="R"), None, None)
    found, missing = run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        mapping,
        pointed=True,
    )
    assert missing == [] and [o.slices for o in found] == [(0,), (1,), (2,), (3,)]
    smap = mapping.smap
    assert len(smap.refinements) == 1  # one batch for the whole call
    assert smap.refinements[0]["object"] == "joint_fluid"
    held = smap.candidates[("joint_fluid", "axial")]
    assert [c.plane.slice for c in held] == [
        0,
        1,
        3,
    ]  # every competent row, none for empty
    expected = [9 * 0.25, 9 * 0.8 * 1.2, 9 * 1.0]
    assert [c.support for c in held] == pytest.approx(expected)
    assert {c.source for c in held} == {f"native:{UID}"}
    for candidate, z in zip(held, (0, 1, 3), strict=True):
        assert candidate.plane.usable
        assert candidate.plane.series_uid == UID
        assert candidate.plane.provenance == "observations.native_resolved"
        assert np.allclose(
            candidate.plane.normal, frames[z].normal()
        )  # the oblique normal
        assert not np.allclose(candidate.plane.normal, (0, 0, 1))
    assert held[0].plane.precision_mm == 1.5 and np.isnan(held[2].plane.precision_mm)
    # the map's own selection of the strongest section is a pointer; equal support stays a tie
    chosen = smap.selected("joint_fluid", "axial")
    assert chosen.series_uid == UID and chosen.slice == 3 and chosen.usable


def test_equal_support_planes_are_a_tie_the_map_does_not_break():
    frames = [oblique(0.0), oblique(3.0)]
    own = stub(frames)
    pocket = box(2, 5, 2, 5)
    record, arrays = pointed_rows(
        [
            {"slice": 0, "codes": both("identified", NO_FLUID), "medial": pocket},
            {"slice": 1, "codes": both(NO_FLUID, "identified"), "lateral": pocket},
        ]
    )
    mapping = run.MapContext(StudyMap(knee="R"), None, None)
    run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        mapping,
        pointed=True,
    )
    chosen = mapping.smap.selected("joint_fluid", "axial")
    assert chosen.outcome == "tied"
    assert sorted(chosen.candidates) == [(UID, 0), (UID, 1)]
    assert len(mapping.smap.candidates[("joint_fluid", "axial")]) == 2


def test_unreadable_frame_is_a_named_plane_and_never_a_guessed_support():
    frames = [oblique(0.0), "frame_unavailable"]
    own = stub(frames)
    pocket = box(2, 5, 2, 5)
    record, arrays = pointed_rows(
        [
            {"slice": 0, "codes": both("identified", NO_FLUID), "medial": pocket},
            {"slice": 1, "codes": both("identified", NO_FLUID), "medial": pocket},
        ]
    )
    mapping = run.MapContext(StudyMap(knee="R"), None, None)
    found, missing = run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        mapping,
        pointed=True,
    )
    assert [o.slices for o in found] == [(0,), (1,)]  # the section was read either way
    held = mapping.smap.candidates[("joint_fluid", "axial")]
    assert [c.plane.slice for c in held] == [0, 1]
    assert held[0].support == 9.0 and held[0].plane.usable
    assert held[1].support is None
    assert held[1].plane.outcome == "invalid:frame_unavailable"
    # a thickness list that is too short gives an explicitly invalid map plane, not a guessed precision
    short = stub([oblique(0.0), oblique(3.0)], thick=[3.0])
    mapping = run.MapContext(StudyMap(knee="R"), None, None)
    record, arrays = pointed_rows(
        [{"slice": 1, "codes": both("identified", NO_FLUID), "medial": pocket}]
    )
    found, missing = run.axial_joint_fluid(
        short,
        record,
        arrays,
        PROOF,
        mapping,
        pointed=True,
    )
    assert len(found) == 1
    assert missing == []
    (candidate,) = mapping.smap.candidates[("joint_fluid", "axial")]
    assert candidate.plane.outcome == "invalid:precision_unreadable"
    assert candidate.plane.slice == 1 and candidate.support == 9.0


def test_invalid_and_missing_thickness_make_named_map_planes_without_losing_observation():
    own = stub([oblique(0.0), oblique(3.0)], thick=["bad"])
    bad = run.map_plane(
        own,
        "joint_fluid",
        0,
        "the native resolved section on this series",
        "observations.native_resolved",
    )
    assert bad.outcome == "invalid:precision_unreadable"
    assert bad.series_uid == UID and bad.slice == 0
    assert bad.provenance == "observations.native_resolved"

    short = stub([oblique(0.0), oblique(3.0)], thick=[3.0])
    missing_precision = run.map_plane(
        short,
        "joint_fluid",
        1,
        "the native resolved section on this series",
        "observations.native_resolved",
    )
    assert missing_precision.outcome.startswith("invalid:")
    assert missing_precision.outcome == "invalid:precision_unreadable"

    unknown = stub([oblique(0.0)], thick=[None])
    unknown_precision = run.map_plane(
        unknown,
        "joint_fluid",
        0,
        "the native resolved section on this series",
        "observations.native_resolved",
    )
    assert unknown_precision.outcome == "selected"
    assert np.isnan(unknown_precision.precision_mm)


def test_map_offer_matches_native_refinement_offer_and_is_reused():
    own = stub([oblique(0.0)], thick=[3.0])
    pocket = box(2, 5, 2, 5)
    record, arrays = main_record(
        0, both("identified", NO_FLUID), pocket, box(0, 0, 0, 0)
    )
    mapping = run.MapContext(StudyMap(knee="R"), None, None)
    found, missing = run.axial_joint_fluid(
        own, record, arrays, PROOF, mapping, pointed=False
    )
    assert missing == [] and len(found) == 1
    (candidate,) = mapping.smap.candidates[("joint_fluid", "axial")]
    assert candidate.plane.outcome == "selected"
    assert candidate.source == f"native:{UID}"
    assert candidate.plane.provenance == "observations.native_resolved"
    assert candidate.plane.reason == (
        "strongest native-resolved section of the object on this series (identified); "
        "a pointer, not a definition of where the anatomy is most obvious"
    )
    own.record["observations"].append(
        {
            "object": found[0].object,
            "provenance": found[0].provenance,
            "kind": found[0].kind,
            "series_uid": found[0].series_uid,
            "slices": found[0].slices,
            "count": found[0].count,
            "code": found[0].code,
        }
    )
    assert run.refine_map(mapping, [own]) == 0
    assert len(mapping.smap.candidates[("joint_fluid", "axial")]) == 1


def test_invalid_precision_offer_survives_native_refinement():
    for z, thickness in ((0, ["bad"]), (1, [3.0])):
        own = stub([oblique(0.0), oblique(3.0)], thick=thickness)
        pocket = box(2, 5, 2, 5)
        record, arrays = main_record(
            z, both("identified", NO_FLUID), pocket, box(0, 0, 0, 0)
        )
        mapping = run.MapContext(StudyMap(knee="R"), None, None)
        found, missing = run.axial_joint_fluid(
            own, record, arrays, PROOF, mapping, pointed=False
        )
        assert missing == [] and len(found) == 1
        own.record["observations"].append(
            {
                "object": found[0].object,
                "provenance": found[0].provenance,
                "kind": found[0].kind,
                "series_uid": found[0].series_uid,
                "slices": found[0].slices,
                "count": found[0].count,
                "code": found[0].code,
            }
        )
        assert run.refine_map(mapping, [own]) == 1
        assert all(
            candidate.plane.outcome == "invalid:precision_unreadable"
            for candidate in mapping.smap.candidates[("joint_fluid", "axial")]
        )


def test_source_slice_indices_are_integer_nonnegative_and_within_native_depth():
    own = stub([oblique(0.0)])
    cases = (
        (True, "source_slice_invalid", np.asarray([True], dtype=bool)),
        (0.5, "source_slice_invalid", np.asarray([0.5], dtype=float)),
        (np.nan, "source_slice_invalid", np.asarray([np.nan], dtype=float)),
        (np.inf, "source_slice_invalid", np.asarray([np.inf], dtype=float)),
        ("bad", "source_slice_invalid", np.asarray(["bad"], dtype=object)),
        (-1, "source_slice_out_of_range", np.asarray([-1], dtype=np.int32)),
        (1, "source_slice_out_of_range", np.asarray([1], dtype=np.int32)),
    )
    for value, expected, slice_array in cases:
        record, arrays = pointed_rows([{"slice": 0, "codes": both(NO_FLUID)}])
        record["recess"]["pointed_planes"][1]["slice"] = value
        arrays["a3_recess_plane_slices"] = slice_array
        found, missing = run.axial_joint_fluid(
            own,
            record,
            arrays,
            PROOF,
            None,
            pointed=True,
        )
        assert found == [] and [m.code for m in missing] == [expected], repr(value)

        main, main_arrays = main_record(
            0, both(NO_FLUID), box(0, 0, 0, 0), box(0, 0, 0, 0)
        )
        main["slice_index"] = value
        found, missing = run.axial_joint_fluid(
            own,
            main,
            main_arrays,
            PROOF,
            None,
            pointed=False,
        )
        assert found == [] and [m.code for m in missing] == [expected], repr(value)

    record, arrays = pointed_rows([{"slice": 0, "codes": both(NO_FLUID)}])
    del record["recess"]["pointed_planes"][1]["slice"]
    found, missing = run.axial_joint_fluid(
        own, record, arrays, PROOF, None, pointed=True
    )
    assert found == [] and [m.code for m in missing] == ["source_slice_unavailable"]

    record, arrays = pointed_rows([{"slice": 0, "codes": both(NO_FLUID)}])
    del arrays["a3_recess_plane_slices"]
    found, missing = run.axial_joint_fluid(
        own, record, arrays, PROOF, None, pointed=True
    )
    assert found == [] and [m.code for m in missing] == ["source_slice_unavailable"]

    main, main_arrays = main_record(0, both(NO_FLUID), box(0, 0, 0, 0), box(0, 0, 0, 0))
    del main["slice_index"]
    found, missing = run.axial_joint_fluid(
        own, main, main_arrays, PROOF, None, pointed=False
    )
    assert found == [] and [m.code for m in missing] == ["source_slice_unavailable"]

    own_without_slices = stub([oblique(0.0)])
    del own_without_slices.series.slices
    record, arrays = pointed_rows([{"slice": 0, "codes": both(NO_FLUID)}])
    found, missing = run.axial_joint_fluid(
        own_without_slices,
        record,
        arrays,
        PROOF,
        None,
        pointed=True,
    )
    assert found == [] and [m.code for m in missing] == ["source_depth_unavailable"]


def test_owner_and_source_record_uids_must_agree_on_both_paths():
    own = stub([oblique(0.0)])
    record, arrays = pointed_rows([{"slice": 0, "codes": both(NO_FLUID)}])
    record["series_uid"] = "different-series"
    found, missing = run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        None,
        pointed=True,
    )
    assert found == [] and [m.code for m in missing] == ["source_record_uid_mismatch"]
    assert UNITS not in arrays and UNITS not in record

    record, arrays = main_record(0, both(NO_FLUID), box(0, 0, 0, 0), box(0, 0, 0, 0))
    record["series_uid"] = "different-series"
    found, missing = run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        None,
        pointed=False,
    )
    assert found == [] and [m.code for m in missing] == ["source_record_uid_mismatch"]
    assert UNITS not in arrays and UNITS not in record


def test_partial_fluid_union_keeps_side_reason_and_exact_readable_mask():
    own = stub([oblique(0.0)])
    medial = box(1, 4, 1, 5)
    for lateral_code, lateral_mask, reason in (
        ("unrecognized_code", box(0, 0, 0, 0), "unrecognized_code"),
        (NO_FLUID, box(6, 9, 7, 11), "wall_code_disagrees_with_selected_recess"),
    ):
        record, arrays = pointed_rows(
            [
                {
                    "slice": 0,
                    "codes": both("identified", lateral_code),
                    "medial": medial,
                    "lateral": lateral_mask,
                }
            ]
        )
        before_medial = arrays["a3_recess_plane_medial_recess"].copy()
        before_lateral = arrays["a3_recess_plane_lateral_recess"].copy()
        found, missing = run.axial_joint_fluid(
            own,
            record,
            arrays,
            PROOF,
            None,
            pointed=True,
        )
        assert len(found) == 1 and found[0].kind == "resolved"
        assert found[0].count == int(medial.sum())
        assert [m.code for m in missing] == [f"{LATERAL}:{reason}"]
        assert np.array_equal(arrays[UNITS][0], medial)
        assert np.array_equal(arrays["a3_recess_plane_medial_recess"], before_medial)
        assert np.array_equal(arrays["a3_recess_plane_lateral_recess"], before_lateral)
        diagnostic = record[UNITS]["rows"][0]
        assert diagnostic["status"] == "fluid"
        assert diagnostic["side_reasons"] == {LATERAL: reason}


def test_main_path_offer_and_no_mapping_no_offer():
    own = stub([oblique(0.0, (0.7, 0.7)), oblique(3.0, (0.7, 0.7))])
    pocket = box(1, 4, 1, 4)
    record, arrays = main_record(
        1, both("identified", NO_FLUID), pocket, box(0, 0, 0, 0)
    )
    found, _ = run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        None,
        pointed=False,
    )
    assert len(found) == 1
    mapping = run.MapContext(StudyMap(knee="L"), None, None)
    record, arrays = main_record(
        1, both("identified", NO_FLUID), pocket, box(0, 0, 0, 0)
    )
    run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        mapping,
        pointed=False,
    )
    (held,) = mapping.smap.candidates[("joint_fluid", "axial")]
    assert held.plane.slice == 1 and held.support == pytest.approx(9 * 0.49)
    # a measured-empty main slice offers nothing
    mapping = run.MapContext(StudyMap(knee="L"), None, None)
    record, arrays = main_record(1, both(NO_FLUID), box(0, 0, 0, 0), box(0, 0, 0, 0))
    found, _ = run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        mapping,
        pointed=False,
    )
    assert found[0].kind == "reading"
    assert mapping.smap.refinements == []


def test_telemetry_declares_the_union_and_only_its_actual_consumers(monkeypatch):
    produced: list[tuple[str, tuple[str, ...]]] = []
    consumed: list[tuple[str, tuple[str, ...], str]] = []
    monkeypatch.setattr(run, "handed", lambda p, n: produced.append((p, tuple(n))))
    monkeypatch.setattr(run, "reads", lambda p, n, s: consumed.append((p, tuple(n), s)))
    own = stub([oblique(0.0)])
    pocket = box(2, 5, 2, 5)
    record, arrays = pointed_rows(
        [{"slice": 0, "codes": both("identified", NO_FLUID), "medial": pocket}]
    )
    run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        None,
        pointed=True,
    )
    assert produced == [("axial_joint_fluid", ("union",))]
    stages = {s for p, _, s in consumed if p == "axial_joint_fluid"}
    assert stages == {"joint_fluid_observation"}  # no map offered, no map read declared
    consumed.clear()
    produced.clear()
    record, arrays = pointed_rows(
        [{"slice": 0, "codes": both("identified", NO_FLUID), "medial": pocket}]
    )
    mapping = run.MapContext(StudyMap(knee="R"), None, None)
    run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        mapping,
        pointed=True,
    )
    stages = {s for p, _, s in consumed if p == "axial_joint_fluid"}
    assert stages == {"joint_fluid_observation", "study_map_offer"}
    # nothing was produced when nothing was found
    produced.clear()
    consumed.clear()
    record, arrays = pointed_rows([{"slice": 0, "codes": both(NO_FLUID)}])
    run.axial_joint_fluid(
        own,
        record,
        arrays,
        PROOF,
        mapping,
        pointed=True,
    )
    assert produced == []
    assert not [c for c in consumed if c[0] == "axial_joint_fluid"]


def test_the_wall_selection_and_confirmation_helpers_are_not_changed():
    # the helper reads the existing selection; it does not redefine which parts or what confirms them
    assert run.RECESS_PARTS["retinacula"] == (
        (MEDIAL, "medial_wall"),
        (run.RETINACULA[1], "lateral_wall"),
    )
    plane = run.recess_blank(1, "retinacula", "abstain_no_patella_carried", ())
    assert run.recess_says(plane, {}) == "rejected"
