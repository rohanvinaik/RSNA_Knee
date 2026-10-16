"""The posterior family's output through the driver: what each view says of a part, and the tube's
continuation (`scripts.run_interiors.index_posterior`)."""

from types import SimpleNamespace
from typing import Any, cast

import numpy as np

from knee.collapse.physical import PlaneFrame
from knee.collapse.posterior import START_NAMES, STOP_NAMES
from scripts import run_interiors as run

STUDY = "S"
AXIAL = ([1.0, 0.0, 0.0], [0.0, 1.0, 0.0])  # columns along x, rows along y
SAGITTAL = ([0.0, 1.0, 0.0], [0.0, 0.0, -1.0])  # columns along y, rows toward the feet


def series_stub(uid, planes, positions, orientation, fat=0, fluid=0):
    geometry = SimpleNamespace(
        position=[np.asarray(p, dtype=float) for p in positions],
        orientation=[[*orientation[0], *orientation[1]] for _ in positions],
        spacing=[(1.0, 1.0) for _ in positions],
    )
    return SimpleNamespace(
        row=SimpleNamespace(
            series_uid=uid, fat_suppression=str(fat), fluid_sensitive=str(fluid)
        ),
        volume=np.asarray(planes, dtype=float),
        geometry=geometry,
        slice_thickness_mm=[5.0 for _ in positions],
    )


def measured_stub(series, index, codes, arrays, view):
    frame = PlaneFrame.from_dicom(
        series.geometry.position[index],
        series.geometry.orientation[index],
        series.geometry.spacing[index],
    )
    record = {
        "series_uid": series.row.series_uid,
        "view": view,
        "slice_index": index,
        "assignments": {"codes": codes},
    }
    return cast(
        Any, SimpleNamespace(series=series, record=record, arrays=arrays, frame=frame)
    )


def axial(uid="ax", codes=None, mask_name="a2_popliteal_artery"):
    """An axial slice at z = 50 mm holding a 3 x 3 mm place at x 20 to 22, y 10 to 12."""
    mask = np.zeros((40, 40), dtype=bool)
    mask[10:13, 20:23] = True
    series = series_stub(uid, [np.zeros((40, 40))], [[0, 0, 50]], AXIAL, 1, 1)
    return measured_stub(
        series,
        0,
        codes or {"popliteal_artery": "identified"},
        {mask_name: mask, "a1_objects": np.zeros((40, 40), dtype=np.int8)},
        ["Axial", "1", "1"],
    )


def sagittal(uid="sag", xs=(0, 5, 10, 15, 20, 25), fat=0, fluid=0, dark=True):
    """A stack of sagittal slices at the given x (in the given order); the tube lies in the slice
    at x = 20, along the leg (rows) at column 11, from the 20th to the 80th row."""
    planes = []
    for x in xs:
        plane = np.full((120, 40), 100.0) if dark else np.full((120, 40), 10.0)
        if x == 20:
            plane[20:80, 11] = 0.0 if dark else 200.0
        planes.append(plane)
    series = series_stub(uid, planes, [[x, 0, 100] for x in xs], SAGITTAL, fat, fluid)
    mid = len(xs) // 2
    return measured_stub(series, mid, {}, {}, ["Sagittal", str(fluid), str(fat)])


def rows_of(own, kind=None):
    rows = own.record.get("observations", [])
    return [r for r in rows if kind is None or (r["provenance"], r["kind"]) == kind]


def test_a_tube_is_said_natively_projected_and_followed_along_the_leg():
    ax, sag = axial(), sagittal()
    run.index_posterior([ax, sag], run.EARLY_MIDDLE_PARTS, [], STUDY, None, True)
    native = rows_of(ax, ("native", "resolved"))
    assert [(r["object"], r["count"], r["label"]) for r in native] == [
        ("popliteal_artery", 9, None)  # a boolean mask: no label selects in it
    ]
    assert native[0]["artifact"] == "S/ax.npz" and native[0]["off_plane_mm"] == 0.0
    (target,) = rows_of(sag, ("projected", "target"))
    assert target["code"] == "on_the_slice" and target["slices"] == (4,)
    assert (
        target["support"] == "a2_popliteal_artery" and target["artifact"] == "S/ax.npz"
    )
    (tube,) = rows_of(sag, ("native", "reading"))
    assert tube["code"] == "tube_followed" and tube["slices"] == (4,)
    assert tube["count"] == 60 and tube["row"] == 0
    assert (
        tube["artifact"] == "S/ax.npz"
    )  # the places are kept in the cross-section's record
    arrays = ax.arrays
    offsets = arrays["a3_posterior_trace_popliteal_artery_offsets"]
    points = arrays["a3_posterior_trace_popliteal_artery_points_lps"]
    assert offsets.tolist() == [0, 60] and points.shape == (60, 3)
    assert set(np.round(points[:, 0])) == {20.0}  # the slice's own x
    assert points[:, 2].min() == 100 - 79 and points[:, 2].max() == 100 - 20
    # feet to head, and each end's stop is named, never silent
    assert arrays["a3_posterior_trace_popliteal_artery_starts"].tolist() == [
        START_NAMES.index("followed")
    ]
    stops = arrays["a3_posterior_trace_popliteal_artery_stops"][0]
    assert [STOP_NAMES[i] for i in stops] == [
        "stopped_not_set_apart_from_the_flanks"
    ] * 2
    # no leg was given, so the joint line's context is unknown, not zero
    assert np.isnan(arrays["a3_posterior_context_up_mm"]).all()


def test_the_followed_places_do_not_depend_on_the_order_of_the_stack():
    first, second = axial("a"), axial("b")
    run.index_posterior(
        [first, sagittal()], run.EARLY_MIDDLE_PARTS, [], STUDY, None, True
    )
    run.index_posterior(
        [second, sagittal(xs=(25, 20, 15, 10, 5, 0))],
        run.EARLY_MIDDLE_PARTS,
        [],
        STUDY,
        None,
        True,
    )
    a = first.arrays["a3_posterior_trace_popliteal_artery_points_lps"]
    b = second.arrays["a3_posterior_trace_popliteal_artery_points_lps"]
    assert np.array_equal(a, b)


def test_a_part_the_rule_refused_is_unresolved_and_one_never_asked_is_silent():
    ax = axial(
        codes={
            "popliteal_artery": "abstain_requires_both_gastrocnemius_heads",
            "popliteal_vein": "not_named_on_this_slice",
        }
    )
    run.index_posterior([ax], run.EARLY_MIDDLE_PARTS, [], STUDY, None, True)
    missing = ax.record["observations_unresolved"]
    assert [(m["object"], m["code"]) for m in missing] == [
        ("popliteal_artery", "abstain_requires_both_gastrocnemius_heads")
    ]
    assert not rows_of(ax)  # nothing is invented for it, nor for the part never asked


def test_a_part_laid_onto_a_series_is_laid_there_and_not_projected_onto_it():
    ax = axial()
    twin = axial("twin", {"popliteal_artery": "laid_from_its_partner"})
    run.index_posterior([ax, twin], run.EARLY_MIDDLE_PARTS, [], STUDY, None, True)
    (laid,) = rows_of(twin, ("laid", "resolved"))
    assert laid["code"] == "laid_from_its_partner" and laid["off_plane_mm"] is None
    assert not rows_of(twin, ("projected", "target"))
    # an axial series is not asked for the continuation: the leg does not run in its plane
    assert not rows_of(twin, ("native", "reading"))


def test_fluid_is_followed_as_bright_only_where_it_is_bright():
    codes = {"gastrocnemius_semimembranosus_bursa": "identified"}
    name = "a2_gastrocnemius_semimembranosus_bursa"
    record = {"series_uid": "ax", "main_slice": {"object": "semimembranosus"}}
    for sag, expected in (
        (sagittal(fat=1, fluid=1, dark=False), "tube_followed"),
        (sagittal(fat=0, fluid=0, dark=False), None),
    ):
        ax = axial(codes=codes, mask_name=name)
        mine: dict[str, Any] = {
            **ax.record,
            **record,
            "assignments": {"codes": codes},
        }
        run.index_posterior(
            [ax, sag],
            (),
            [(mine, ax.arrays)],
            STUDY,
            None,
            True,
        )
        got = rows_of(sag, ("native", "reading"))
        if expected is None:
            assert not got
            assert [m["code"] for m in sag.record["observations_unresolved"]] == [
                "fluid_is_not_bright_in_this_sequence"
            ]
        else:
            assert [r["code"] for r in got] == [expected] and got[0]["count"] == 60
        # the main record's artifact is named for its part
        (native,) = [r for r in mine["observations"] if r["kind"] == "resolved"]
        assert native["artifact"] == "S/ax-semimembranosus.npz"


def test_a_place_beyond_the_scan_is_unknown_for_the_continuation():
    ax, far = axial(), sagittal(xs=(100, 105, 110))
    run.index_posterior([ax, far], run.EARLY_MIDDLE_PARTS, [], STUDY, None, True)
    (target,) = rows_of(far, ("projected", "target"))
    assert target["code"] == "beyond_the_scan"
    assert [m["code"] for m in far.record["observations_unresolved"]] == [
        "target_beyond_the_scan"
    ]
    assert not rows_of(far, ("native", "reading"))
    assert "a3_posterior_trace_popliteal_artery_points_lps" not in ax.arrays


def test_the_refusals_find_part_kept_are_said_on_the_series_that_gave_them():
    ax = axial()
    run.posterior_silences(
        [ax],
        {
            "ax:semitendinosus": "abstain_no_body_meets_both_spatial_relations",
            "ax:fibula": "abstain_no_fibula",  # not a posterior part: not said here
            "elsewhere:gracilis": "abstain_no_native_gracilis",  # a series the study lacks
        },
    )
    assert [(m["object"], m["code"]) for m in ax.record["observations_unresolved"]] == [
        ("semitendinosus", "abstain_no_body_meets_both_spatial_relations")
    ]


def test_a_label_selects_only_in_a_coded_array():
    assert run.coded_label("patella", "a1_objects") == run.OBJECT_CODES["patella"]
    assert run.coded_label("patella", "a3_patella_plane_objects") == 6
    # the twin's tendon masks are boolean: the old label (22) selected nothing in them
    assert run.coded_label("patellar_tendon", "a3_patella_twin_patellar_tendon") is None
    assert (
        run.coded_label("patellar_tendon", "a3_patella_twin_ab12cd34_pad_anterior")
        is None
    )


def test_a_twin_laid_onto_from_several_series_keeps_every_sources_arrays():
    twin: dict[str, Any] = {}
    uid_a, uid_b = (
        "1.2.3.111.12345678",
        "1.2.3.222.12345678",
    )  # the same last eight digits
    first = run.source_prefix("a3_femur_laid", twin, uid_a)
    twin[f"{first}_slices"] = np.asarray([1])
    second = run.source_prefix("a3_femur_laid", twin, uid_b)
    twin[f"{second}_slices"] = np.asarray([2])
    third = run.source_prefix("a3_femur_laid", twin, uid_a)
    assert first == "a3_femur_laid"
    assert second == f"a3_femur_laid_{uid_b}" and second != first
    # the exact identity separates sources an abbreviation of it would run together
    assert uid_a[-8:] == uid_b[-8:] and third != second
    assert twin["a3_femur_laid_slices"].tolist() == [
        1
    ]  # the first is never overwritten


def test_the_context_the_middle_slice_names_is_indexed_without_projection_or_a_best_slice():
    ax = axial(
        codes={
            "joint": "identified",
            "muscle": "laid_from_its_partner",
            "air": "abstain_no_air_in_the_field",
            "skin": "not_named_on_this_slice",
        }
    )
    ax.arrays["a1_objects"][5:9, 5:9] = run.OBJECT_CODES["joint"]
    ax.arrays["a1_objects"][20:25, 20:25] = run.OBJECT_CODES["muscle"]
    sag = sagittal()
    run.index_posterior([ax, sag], run.CONTEXT_MIDDLE_PARTS, [], STUDY, None, False)
    got = {(r["object"], r["provenance"]): r for r in rows_of(ax)}
    assert got[("joint", "native")]["count"] == 16
    assert got[("joint", "native")]["label"] == run.OBJECT_CODES["joint"]
    assert "no claim that this slice is its best" in got[("joint", "native")]["note"]
    assert got[("muscle", "laid")]["count"] == 25
    assert [(m["object"], m["code"]) for m in ax.record["observations_unresolved"]] == [
        ("air", "abstain_no_air_in_the_field")
    ]
    assert not rows_of(
        sag
    )  # context is not projected onto other series, and nothing is followed
