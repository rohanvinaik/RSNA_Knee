"""The anchors: the femur, tibia, patella and fibula found by their structure (lane W9).

A small synthetic knee is built in memory as real `Series` with real squints: a tapered elliptic
femur above a tapered elliptic tibia, each a bright marrow inside a dark cortex, a patella in front
of the femur's lower end, and a fibula behind the tibia on the knee's outer side, inside a grey leg
in black air. Its sagittal and coronal series (one fat-suppressed sagittal for the patella) and an
axial series are read by `find_anchors` exactly as a study from `read_study_squints` is.

Two signs: a bone that moves moves its anchor (territory and reference follow the structure, not a
stored window), and a bone the structure does not show stays unavailable, never a guess. The
transcribed orchestrations are pinned against the runner's own functions on the same inputs.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import scripts.run_interiors as runner
from knee.collapse.squint_stack import read_squint_stack
from knee.diagnosis import squint_anchors as anchors_module
from knee.diagnosis.squint_anchors import BONES, find_anchors
from knee.diagnosis.squint_interfaces import (
    ROLE_CONTEXT,
    ROLE_OBJECT,
    anchor_code,
    territory_code,
)
from knee.objects.assignments import (
    OBJECT_CODES,
    Measures,
    assign_plane,
    margin,
    read_field,
)
from knee.study.series import Series, SeriesGeometry
from knee.study.tables import SeriesRow

STUDY = "1.2.826.0.1.3680043.8.498.anchors.synthetic"
AIR, CORTEX, SOFT, MARROW = 0.0, 0.0, 300.0, 1000.0
SAGITTAL = (0.0, 1.0, 0.0, 0.0, 0.0, -1.0)  # columns posterior, rows inferior
CORONAL = (1.0, 0.0, 0.0, 0.0, 0.0, -1.0)  # columns toward the left, rows inferior
AXIAL = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0)  # columns toward the left, rows posterior


def _knee(
    points: np.ndarray, shift: tuple[float, float, float], bones: bool
) -> np.ndarray:
    """The synthetic right knee's stored value at LPS places (millimetres)."""
    x, y, z = (points[..., axis] - shift[axis] for axis in range(3))
    value = np.where(x**2 + (y - 4.0) ** 2 <= 50.0**2, SOFT, AIR)
    if not bones:
        return value

    def solid(outer: np.ndarray, inner: np.ndarray) -> None:
        nonlocal value
        value = np.where(outer, CORTEX, value)
        value = np.where(inner, MARROW, value)

    for low, high, sign in ((6.0, 76.0, 1.0), (-76.0, -6.0, -1.0)):
        # the femur above, the tibia below: an elliptic section narrowing away from the joint
        reach = np.clip(sign * z - 6.0, 0.0, None)
        scale = 1.0 - reach / 160.0
        inside = (z >= low) & (z <= high)
        outer = inside & ((x / (28 * scale)) ** 2 + (y / (22 * scale)) ** 2 <= 1.0)
        core = (
            (z >= low + 2)
            & (z <= high - 2)
            & ((x / (28 * scale - 2)) ** 2 + (y / (22 * scale - 2)) ** 2 <= 1.0)
        )
        solid(outer, core)
    # the patella in front of the femur's lower end
    patella = (x / 12) ** 2 + ((y + 29.0) / 6.5) ** 2 + ((z - 24) / 16) ** 2
    solid(
        patella <= 1.0,
        (x / 10) ** 2 + ((y + 29.0) / 4.5) ** 2 + ((z - 24) / 14) ** 2 <= 1.0,
    )
    # the fibula behind the tibia on the outer side (a right knee's outer side is the patient's right)
    radius = 9.0 - np.clip(-40.0 - z, 0.0, None) * (2.0 / 38.0)
    along = (z >= -78.0) & (z <= -38.0)
    spoke = (x + 18.0) ** 2 + (y - 34.0) ** 2
    solid(
        along & (spoke <= radius**2),
        along & (z <= -40) & (z >= -76) & (spoke <= (radius - 1.5) ** 2),
    )
    return value


def _plane_places(origin, orientation, shape) -> np.ndarray:
    rows, cols = np.indices(shape)
    row_step = np.asarray(orientation[3:])
    col_step = np.asarray(orientation[:3])
    return np.asarray(origin) + rows[..., None] * row_step + cols[..., None] * col_step


def _series(
    uid: str,
    plane: str,
    tags: str,
    orientation,
    origins,
    shape,
    thickness: float,
    shift,
    bones: bool,
    knee: str,
) -> Series:
    volume = np.stack(
        [_knee(_plane_places(o, orientation, shape), shift, bones) for o in origins]
    ).astype(np.uint16)
    volume.setflags(write=False)
    count = len(origins)
    geometry = SeriesGeometry(
        np.tile(np.asarray(orientation, dtype=float), (count, 1)),
        np.asarray(origins, dtype=float),
        np.ones((count, 2)),
    )
    slices = tuple(
        SimpleNamespace(
            path=Path(f"{uid}-{k}.dcm"),
            header=SimpleNamespace(Laterality=knee),
            pixels=volume[k],
        )
        for k in range(count)
    )
    return Series(
        SeriesRow(STUDY, uid, tags, tags, plane),
        slices,
        ("stackable",),
        volume,
        geometry,
        (thickness,) * count,
    )


def _record(series: Series) -> dict:
    return {
        "series_uid": series.row.series_uid,
        "view": {
            "orientation": series.row.anatomical_plane,
            "fluid_sensitive": series.row.fluid_sensitive,
            "fat_suppression": series.row.fat_suppression,
        },
        "shape": tuple(series.volume.shape),
        "stack": read_squint_stack(series, 10.0),
        "native_series": series,
    }


@cache
def _study(
    shift: tuple[float, float, float] = (0.0, 0.0, 0.0),
    bones: bool = True,
    views: tuple[str, ...] = ("sag", "sagfs", "cor", "ax"),
    knee: str = "R",
) -> dict:
    """The synthetic study as `read_study_squints` returns one (cached: tests only read it)."""
    made = {
        "sag": lambda: _series(
            "1.2.826.0.1.3680043.8.498.anchors.sag",
            "Sagittal",
            "0",
            SAGITTAL,
            [(-27.0 + 3 * k, -55.0, 80.0) for k in range(19)],
            (160, 115),
            3.0,
            shift,
            bones,
            knee,
        ),
        "sagfs": lambda: _series(
            "1.2.826.0.1.3680043.8.498.anchors.sagfs",
            "Sagittal",
            "1",
            SAGITTAL,
            [(-27.0 + 3 * k, -55.0, 80.0) for k in range(19)],
            (160, 115),
            3.0,
            shift,
            bones,
            knee,
        ),
        "cor": lambda: _series(
            "1.2.826.0.1.3680043.8.498.anchors.cor",
            "Coronal",
            "0",
            CORONAL,
            [(-55.0, -36.0 + 3 * k, 80.0) for k in range(25)],
            (160, 110),
            3.0,
            shift,
            bones,
            knee,
        ),
        "ax": lambda: _series(
            "1.2.826.0.1.3680043.8.498.anchors.ax",
            "Axial",
            "0",
            AXIAL,
            [(-55.0, -55.0, -76.0 + 4 * k) for k in range(39)],
            (115, 110),
            4.0,
            shift,
            bones,
            knee,
        ),
    }
    return {
        "schema": "knee.squint-study/v1",
        "study_uid": STUDY,
        "series": [_record(made[name]()) for name in views],
    }


@cache
def _anchors(**kwargs) -> dict:
    return find_anchors(_study(**kwargs))


def _grid(study: dict, series_uid: str) -> tuple[int, ...]:
    record = next(r for r in study["series"] if r["series_uid"] == series_uid)
    return tuple(int(v) for v in record["stack"].median.shape)


def _support(territory: dict, shape: tuple[int, int]) -> np.ndarray:
    mask = np.zeros(shape, dtype=bool)
    r0, c0 = territory["native_support"]["offset_rc"]
    crop = territory["native_support"]["mask"][0]
    mask[r0 : r0 + crop.shape[0], c0 : c0 + crop.shape[1]] = crop
    return mask


# -- the frozen shapes and what each anchor says ---------------------------------------------------
def test_every_anchor_and_territory_is_a_valid_frozen_shape():
    study, found = _study(), _anchors()
    assert set(found) == set(BONES)
    for bone, anchor in found.items():
        assert anchor_code(anchor) == "valid", bone
        assert anchor["producer"] == anchors_module.PRODUCER
        assert anchor["cost"]["seconds"] > 0
        for territory in anchor["territories"]:
            grid = _grid(study, territory["series_uid"])
            assert territory_code(territory, grid_shape=grid) == "valid"
            assert territory["origin"] == "anchor_structure"
            roles = territory["roles"]
            # a box is an address: only the support's own tiles are object, one tile round them
            # context; this producer calls no tile outside the leg
            assert set(np.unique(roles)) <= {ROLE_OBJECT, ROLE_CONTEXT}
            share = territory["object_share"]
            assert np.all(share[roles == ROLE_OBJECT] > 0)


def test_the_femur_and_tibia_are_found_whole_on_their_own_bones():
    found = _anchors()
    for bone, (z_low, z_high) in (("femur", (6, 76)), ("tibia", (-76, -6))):
        anchor = found[bone]
        assert anchor["status"] == "complete", anchor["conflicts"]
        x, y, z = anchor["reference_lps"]
        # the three key planes are where each bone is broadest: the middle sagittal and coronal
        # slices through its axis, and the axial slice beside the joint
        assert abs(x) <= 1.5 and abs(y) <= 1.5
        assert z_low <= z <= z_high
        assert abs(z - (8.0 if bone == "femur" else -8.0)) <= 0.5
        planes = anchor["key_planes"]
        assert all(
            planes[o]["outcome"] == "selected" for o in ("sagittal", "coronal", "axial")
        )
        for territory in anchor["territories"]:
            assert territory["provenance"].get("cross_view") in (None, "views_agree")
    # the femur's breadth is measured from its attributed axial sections (its marrow is about
    # 51 mm across at its broadest section, read on 2 mm blocks), with its source; no other bone
    # has one
    breadth = found["femur"]["breadth_mm"]
    assert 48.0 <= breadth <= 58.0
    assert "measured_femur_ml_breadth" in found["femur"]["breadth_source"]
    assert all(found[b]["breadth_mm"] is None for b in ("tibia", "patella", "fibula"))


def test_the_patella_and_the_fibula_are_named_by_their_own_rules():
    found = _anchors()
    patella, fibula = found["patella"], found["fibula"]
    sagittal = patella["key_planes"]["sagittal"]
    assert sagittal["outcome"] == "selected"
    assert sagittal["series_uid"].endswith(
        "sagfs"
    )  # named by its light with fat suppression
    native = [t for t in patella["territories"] if t["provenance"]["scale"] == "native"]
    assert (
        native
        and native[0]["provenance"]["femur_it_was_named_against"] == "views_agree"
    )
    fibula_native = [
        t
        for t in fibula["territories"]
        if t["provenance"]["derivation"]
        == "fibula_main_slice_named_by_the_established_rule"
    ]
    assert fibula_native
    for territory in fibula_native:
        assert territory["native_support"]["mask"].any()
    # the fibula lies behind the tibia on the outer side: its sagittal key plane is lateral
    plane = fibula["key_planes"]["sagittal"]
    assert plane["outcome"] == "selected"
    assert plane["offset_mm"] is not None
    # the sagittal normal runs toward the patient's left (+x): the outer side is negative
    assert -27.0 <= plane["offset_mm"] <= -9.0


# -- the two signs ------------------------------------------------------------------------------
def test_a_bone_that_moves_moves_its_anchor():
    """The territory and the reference follow the bone: a knee placed 16 mm lower in the same
    pictures gives anchors 16 mm lower, and its middle-slice support 16 rows lower (read at each
    bone's edge at the joint: the tibia's far end runs off the picture once the knee is lower)."""
    before, after = _anchors(), _anchors(shift=(0.0, 0.0, -16.0))
    for bone in ("femur", "tibia"):
        a, b = before[bone]["reference_lps"], after[bone]["reference_lps"]
        assert after[bone]["status"] == "complete"
        assert abs((b[2] - a[2]) + 16.0) <= 0.5
        assert abs(b[0] - a[0]) <= 0.5 and abs(b[1] - a[1]) <= 0.5
        for derivation in ("middle_slice_named_by_the_established_rule",):
            one = next(
                t
                for t in before[bone]["territories"]
                if t["provenance"]["derivation"] == derivation
                and t["series_uid"].endswith(".sag")
            )
            two = next(
                t
                for t in after[bone]["territories"]
                if t["provenance"]["derivation"] == derivation
                and t["series_uid"].endswith(".sag")
            )
            shape = (160, 115)
            edge = np.max if bone == "femur" else np.min
            row_one = edge(np.argwhere(_support(one, shape))[:, 0])
            row_two = edge(np.argwhere(_support(two, shape))[:, 0])
            assert row_two - row_one == 16  # rows run inferior, 1 mm each
            assert one["tile_window"] != two["tile_window"]
            assert (
                one["native_support"]["mask"].sum()
                == two["native_support"]["mask"].sum()
                or bone == "tibia"
            )


def test_what_the_structure_does_not_show_stays_unavailable_never_a_guess():
    # a leg with no bone in it: the rule abstains on every slice and nothing is placed
    empty = _anchors(bones=False)
    for bone in BONES:
        anchor = empty[bone]
        assert anchor["status"] == "unavailable", bone
        assert anchor["territories"] == [] and anchor["reference_lps"] is None
        assert all(p["outcome"] != "selected" for p in anchor["key_planes"].values())
    codes = {row["code"] for row in empty["femur"]["outcomes"]}
    assert codes & {
        "abstain_fewer_than_two_territories",
        "abstain_nothing_above_or_below_the_deepest",
    }
    # an axial series alone: the rule names no bone where the leg runs through the plane
    axial_only = _anchors(views=("ax",))
    for bone in BONES:
        assert axial_only[bone]["status"] == "unavailable"
        assert axial_only[bone]["reference_lps"] is None
    assert {row["code"] for row in axial_only["femur"]["outcomes"]} == {
        "not_read_leg_runs_through_the_plane"
    }
    assert axial_only["femur"]["cost"]["native_lens_planes"] == 0


def test_a_missing_view_leaves_the_reference_partial_never_a_centroid():
    found = _anchors(views=("sag", "sagfs", "cor"))
    femur = found["femur"]
    assert femur["status"] == "partial"
    assert femur["reference_lps"] is None
    assert femur["key_planes"]["axial"]["outcome"] == "not_supplied"
    assert femur["reference"]["problems"] == {"axial": "not_supplied"}
    assert femur["reference"]["line_direction"] is not None  # two planes leave a line
    assert femur["breadth_mm"] is None and femur["breadth_source"] is None


# -- the cross-view check (one leg, one set of objects) -------------------------------------------
def _readings(study: dict):
    cost = anchors_module._Cost()
    readings = [anchors_module._Series(r, cost) for r in study["series"]]
    call = anchors_module._Call(
        STUDY,
        cost,
        anchors_module.StudyMap(knee="R", names=BONES),
        {bone: [] for bone in BONES},
    )
    named, _codes = anchors_module._identity(readings, call)
    return readings, named, call


def test_a_section_the_other_view_contradicts_is_named_a_conflict():
    _readings_all, named, _call = _readings(_study(views=("sag", "cor")))
    sag, cor = named
    sag_labels = sag.lens(sag.index, "test").labels
    cor_labels = cor.lens(cor.index, "test").labels
    true_sag = sag.objects == OBJECT_CODES["femur"]
    true_cor = cor.objects == OBJECT_CODES["femur"]
    agree = [
        anchors_module._Section("femur", sag, sag.index, true_sag, sag_labels),
        anchors_module._Section("femur", cor, cor.index, true_cor, cor_labels),
    ]
    anchors_module._cross_view(agree)
    assert not any(s.contradicted for s in agree)
    assert all(c["outcome"] == "consistent" for s in agree for c in s.checks)
    # the sagittal "femur" put on another territory of that slice (here the one the tibia holds;
    # on the real studies it was the soft tissue behind the thigh): the coronal femur's own places,
    # carried onto that slice, lie in another territory than the one named
    other = sag.objects == OBJECT_CODES["tibia"]
    assert other.any() and not (other & true_sag).any()
    wrong = [
        anchors_module._Section("femur", sag, sag.index, other, sag_labels),
        anchors_module._Section("femur", cor, cor.index, true_cor, cor_labels),
    ]
    anchors_module._cross_view(wrong)
    assert wrong[0].contradicted
    assert wrong[0].checks[0]["outcome"] == anchors_module.CROSS_VIEW_CONFLICT


def test_a_patella_named_against_a_femur_in_conflict_carries_the_conflict():
    readings, named, call = _readings(_study())
    fs = next(
        own for own in named if own.fat_suppressed and own.orientation == "sagittal"
    )
    assert fs.codes["patella"] == "identified"
    labels = fs.lens(fs.index, "test").labels
    femur = anchors_module._Section(
        "femur", fs, fs.index, fs.objects == OBJECT_CODES["femur"], labels
    )
    call.sections.append(femur)
    femur.checks.append({"outcome": "consistent"})
    anchors_module._patella(named, readings, call)
    assert call.conflicts["patella"] == []
    # the same patella, read against the same femur once its views disagree
    readings, named, call = _readings(_study())
    fs = next(
        own for own in named if own.fat_suppressed and own.orientation == "sagittal"
    )
    femur = anchors_module._Section(
        "femur", fs, fs.index, fs.objects == OBJECT_CODES["femur"], labels
    )
    femur.checks.append({"outcome": anchors_module.CROSS_VIEW_CONFLICT})
    call.sections.append(femur)
    anchors_module._patella(named, readings, call)
    assert [row["code"] for row in call.conflicts["patella"]] == [
        "named_in_front_of_a_femur_whose_views_disagree"
    ]


# -- the transcriptions, pinned against what they transcribe --------------------------------------
def test_the_bone_naming_is_assign_plane_s_own_bones():
    for view in ("sag", "sagfs", "cor"):
        record = next(
            r for r in _study()["series"] if r["series_uid"].endswith(f".{view}")
        )
        own = anchors_module._Series(record, anchors_module._Cost())
        frame = own.frame(own.index)
        plane = own.plane(own.index)
        reading = own.lens(own.index, "test")
        outside = margin(plane)
        field = read_field(plane, reading, frame.basis_lps, outside)
        full = assign_plane(
            plane,
            reading,
            frame.basis_lps,
            own.knee,
            own.fat_suppressed,
            own.fluid_sensitive,
            outside,
            field,
            Measures(None, plane, frame.basis_lps),
        )
        mine = anchors_module._name_bones(
            plane, reading, frame.basis_lps, own.fat_suppressed, outside, field
        )
        for name in ("femur", "tibia", "patella"):
            code = OBJECT_CODES[name]
            assert np.array_equal(full.objects == code, mine.objects == code), name
            assert full.codes[name] == mine.codes[name]
        assert (full.femur, full.tibia, full.patella) == (
            mine.femur,
            mine.tibia,
            mine.patella,
        )
        if view == "sagfs":
            assert mine.codes["patella"] == "identified"


def test_thinned_places_are_the_runners():
    rng = np.random.default_rng(7)
    points = rng.normal(0.0, 30.0, size=(500, 3))
    points[5] = np.nan
    assert np.array_equal(anchors_module._thinned(points), runner.thinned(points))
    assert anchors_module._thinned(np.empty((0, 3))).shape == (0, 3)


def test_the_bone_profile_is_the_runners_bone_profile():
    _all, named, _call = _readings(_study(views=("sag", "cor")))
    leg = anchors_module._leg_of(named)
    for own in named:
        mask = own.objects == OBJECT_CODES["femur"]
        light = float(np.median(np.asarray(own.plane(own.index))[mask]))
        places = anchors_module._thinned(leg.femur)
        others = anchors_module._thinned(leg.tibia)
        mine = anchors_module._bone_profile(own, places, others, light)
        theirs = runner.bone_profile(
            own.series, own.stack, places, others, light, "bones"
        )
        assert np.array_equal(mine.status, theirs.status)
        assert np.array_equal(mine.area_mm2, theirs.area_mm2, equal_nan=True)
        assert np.array_equal(mine.window_rc, theirs.window_rc)
        assert sorted(mine.fine) == [f.index for f in theirs.fine]


def test_the_axial_sections_are_the_runners():
    readings, named, _call = _readings(_study())
    leg = anchors_module._leg_of(named)
    axial = next(own for own in readings if own.orientation == "axial")
    mine = anchors_module._axial_sections(axial, leg.femur, leg.tibia)
    own = SimpleNamespace(
        series=axial.series,
        record={"series_uid": axial.uid, "view": axial.view},
        arrays={"acquired_plane": np.asarray(axial.plane(axial.index))},
    )
    smap = anchors_module.StudyMap(knee="R")
    said = runner.axial_bone_planes(
        smap,
        own,
        runner.Leg(leg.femur, leg.tibia, None, None, leg.patella),
    )
    for bone in ("femur", "tibia"):
        assert np.array_equal(
            mine.areas[bone],
            own.arrays[f"a4_axial_{bone}_section_area_mm2"],
            equal_nan=True,
        )
        assert (
            list(anchors_module.key_slices(mine.areas[bone]))
            == said[bone]["key_slices"]
        )
    low, high = own.arrays["a4_axial_femur_scale_bounds_lps_mm"]
    found = _anchors()["femur"]["breadth_mm"]
    assert found == pytest.approx(high - low)


def test_the_fibula_is_found_as_the_runner_finds_it():
    study = _study(views=("sag",))
    record = study["series"][0]
    series = record["native_series"]
    measured = runner.measure(series, False)
    assert not isinstance(measured, str)
    theirs = runner.find_fibula(
        series, measured.record, measured.arrays, measured.stack, None
    )
    _all, named, call = _readings(study)
    mine = anchors_module._find_fibula(named[0], call.outcomes["fibula"])
    assert not isinstance(theirs, str) and mine is not None
    assert mine.slice == theirs.slice_index
    assert np.array_equal(
        mine.region, theirs.arrays["a1_objects"] == OBJECT_CODES["fibula"]
    )
    assert [z for z, _ in mine.planes] == [z for z, _a, _n in theirs.resolved]


def test_the_cost_names_every_native_plane_the_lens_read():
    found = _anchors()
    cost = found["femur"]["cost"]
    assert cost["native_lens_planes"] == len(cost["lens_reads"])
    purposes = [row["purpose"] for row in cost["lens_reads"]]
    # one bounded middle slice per series the leg runs in; none on the axial
    assert purposes.count("middle_slice_naming") == 3
    assert all(
        row["series_uid"] != "1.2.826.0.1.3680043.8.498.anchors.ax"
        for row in cost["lens_reads"]
    )
    assert cost["block_readings"] >= cost["block_reading_planes"] > 0
    assert set(cost["stages_seconds"]) >= {"middle_naming_and_partner", "cross_view"}
    # the same call's cost is handed to each anchor, each its own copy
    assert found["tibia"]["cost"] == cost and found["tibia"]["cost"] is not cost
