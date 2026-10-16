"""The real driver wiring of the sartorius: where the semimembranosus group is resolved, that the
gracilis's places are consumed before any middle slice is saved, that each earlier record is still
saved once with the same keys, and the named refusals of the middle-axial stage."""

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest

from knee.collapse.physical import PlaneFrame
from scripts import run_interiors as run

SHAPE = (80, 80)
FRAME = PlaneFrame(
    np.zeros(3), np.array([[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]]), (1.0, 1.0)
)
CORD = np.zeros(SHAPE, dtype=bool)
CORD[50:56, 18:21] = True


@dataclass(frozen=True)
class Series:
    row: SimpleNamespace
    slices: tuple = (None,)


def axial_plane():
    plane = np.full(SHAPE, 100.0)
    plane[30:50, 28:34] = 200.0
    return plane


def view(uid, plane="Axial", fat="1", fluid="1", in_plane=(True, True, False)):
    series = Series(
        SimpleNamespace(
            series_uid=uid,
            anatomical_plane=plane,
            fat_suppression=fat,
            fluid_sensitive=fluid,
        )
    )
    arrays = {
        "acquired_plane": axial_plane(),
        "a1_objects": np.full(SHAPE, 3, dtype=np.int8),
        "b1_dark": np.zeros(SHAPE, dtype=bool),
        "b1_available": np.ones(SHAPE, dtype=bool),
        "b1_labels": np.ones(SHAPE, dtype=np.int32),
    }
    return cast(
        run.Measured,
        SimpleNamespace(
            series=series,
            record={
                "series_uid": uid,
                "slice_index": 0,
                "view": [plane, fluid, fat],
                "assignments": {"knee": "R", "codes": {"sartorius": "placeholder"}},
            },
            arrays=arrays,
            frame=FRAME,
            assignment=SimpleNamespace(in_plane=in_plane),
            stack=None,
        ),
    )


def source_record(uid, gracilis="identified"):
    codes = dict.fromkeys(("semimembranosus", "semitendinosus"), "identified")
    codes["gracilis"] = gracilis
    return (
        {
            "series_uid": uid,
            "slice_index": 11,
            "assignments": {"codes": codes},
            "main_slice": {"object": "semimembranosus"},
        },
        {"a2_gracilis": CORD.copy(), "acquired_plane": np.ones(SHAPE)},
        FRAME,
    )


def places(mask=CORD):
    return FRAME.to_patient(np.argwhere(mask).astype(float)) + 20.0 * FRAME.normal()


# -- the middle-axial stage ------------------------------------------------------------------


def test_names_the_sheet_on_the_middle_axial_keeping_every_primary_name_and_reading():
    own = view("ax")
    before = own.arrays["a1_objects"].copy()
    run.name_sartorius(own, places())
    codes = own.record["assignments"]["codes"]
    assert codes["sartorius"] == "identified"
    assert own.arrays["a2_sartorius"].sum() > 100
    assert np.array_equal(own.arrays["a1_objects"], before)
    assert np.array_equal(own.arrays["a2_sartorius_gracilis_target"], CORD)
    for name in ("lightness", "smooth", "surround", "grey_bodies", "body_status"):
        assert f"a2_sartorius_{name}" in own.arrays
    assert all(a.dtype != object for a in own.arrays.values())


@pytest.mark.parametrize(
    ("own", "source", "expected"),
    [
        (
            view("s", "Sagittal", in_plane=(False, True, True)),
            places(),
            "abstain_leg_runs_in_the_plane",
        ),
        (
            view("f", fat="0"),
            places(),
            "abstain_requires_fluid_sensitive_fat_suppression",
        ),
        (
            view("f", fluid="0"),
            places(),
            "abstain_requires_fluid_sensitive_fat_suppression",
        ),
        (view("n"), "abstain_no_native_gracilis", "abstain_no_native_gracilis"),
        (
            view("g"),
            "abstain_gracilis_source_geometry_unreadable",
            "abstain_gracilis_source_geometry_unreadable",
        ),
    ],
)
def test_every_other_view_gets_a_named_refusal_and_an_empty_saved_mask(
    own, source, expected
):
    run.name_sartorius(own, source)
    assert own.record["assignments"]["codes"]["sartorius"] == expected
    assert (
        own.arrays["a2_sartorius"].shape == SHAPE
        and not own.arrays["a2_sartorius"].any()
    )
    assert not [k for k in own.arrays if k.startswith("a2_sartorius_")]


def test_a_header_with_no_knee_is_refused_by_the_rule_after_the_cheap_prerequisites():
    own = view("k")
    own.record["assignments"]["knee"] = ""
    run.name_sartorius(own, places())
    assert (
        own.record["assignments"]["codes"]["sartorius"]
        == "abstain_header_names_no_knee"
    )
    assert not own.arrays["a2_sartorius"].any()


def test_the_contrast_is_read_once_per_axial_and_never_for_a_refused_view(monkeypatch):
    calls = []
    real = run.sartorius_on_slice
    monkeypatch.setattr(
        run, "sartorius_on_slice", lambda *a: calls.append(1) or real(*a)
    )
    for own, source in (
        (view("s", "Sagittal", in_plane=(False, True, True)), places()),
        (view("f", fat="0"), places()),
        (view("n"), "abstain_no_native_gracilis"),
        (view("ok"), places()),
    ):
        run.name_sartorius(own, source)
    assert len(calls) == 1


# -- the gracilis's places ----------------------------------------------------------------------


def test_the_source_is_the_first_native_gracilis_in_the_scanners_millimetres(
    monkeypatch,
):
    seen = []
    monkeypatch.setattr(run, "plane_frame", lambda series, z: seen.append(z) or FRAME)
    measured = [view("a"), view("b")]
    laid = source_record("a", "laid_from_its_partner")
    native = source_record("b")
    found = [(laid[0], laid[1]), (native[0], native[1])]
    got = run.gracilis_source(measured, found)
    assert isinstance(got, np.ndarray) and got.shape == (int(CORD.sum()), 3)
    assert np.allclose(got, FRAME.to_patient(np.argwhere(CORD).astype(float)))
    assert seen == [11]  # the frame of the slice it was named on, read once


def test_no_native_gracilis_or_unreadable_geometry_is_a_named_refusal(monkeypatch):
    measured = [view("a")]
    assert run.gracilis_source(measured, []) == "abstain_no_native_gracilis"
    laid = source_record("a", "laid_from_its_partner")
    assert (
        run.gracilis_source(measured, [(laid[0], laid[1])])
        == "abstain_no_native_gracilis"
    )
    native = source_record("a")
    monkeypatch.setattr(run, "plane_frame", lambda series, z: "geometry_unreadable")
    assert (
        run.gracilis_source(measured, [(native[0], native[1])])
        == "abstain_gracilis_source_geometry_unreadable"
    )


# -- the study's order ---------------------------------------------------------------------------


@pytest.fixture
def study(monkeypatch, tmp_path: Path):
    """measure_study through its real wiring, with the heavy stages stood in for and every call
    recorded in order; the semimembranosus group, the sartorius and the saves are the real ones."""
    order: list[tuple] = []
    axial = view("ax")
    sagittal = view("sg", "Sagittal", "0", "0", (False, True, True))
    measured = [sagittal, axial]
    by_uid = {m.series.row.series_uid: m for m in measured}

    monkeypatch.setattr(
        run,
        "read_study",
        lambda corpus, uid: SimpleNamespace(series=[m.series for m in measured]),
    )
    monkeypatch.setattr(
        run, "measure", lambda series, drawn: by_uid[series.row.series_uid]
    )
    for name in (
        "name_the_extensor_tendons",
        "name_the_rest_of_the_field",
        "name_joint_boundaries",
        "name_suprapatellar_pads",
        "name_iliotibial_band",
    ):
        monkeypatch.setattr(run, name, lambda *args: None)
    monkeypatch.setattr(
        run, "leg_of", lambda m: SimpleNamespace(patella_lps=np.empty((0, 3)))
    )
    monkeypatch.setattr(run, "name_the_back_of_the_knee", lambda own, leg: {})
    monkeypatch.setattr(run, "plane_frame", lambda series, z: FRAME)

    def semimembranosus(own, leg):
        order.append(("semimembranosus", own.series.row.series_uid))
        if own is axial:
            return source_record("ax")
        return "abstain_leg_runs_in_the_plane"

    def fibula(*args):
        order.append(("fibula",))
        return "abstain_header_names_no_knee"

    monkeypatch.setattr(run, "semimembranosus_slice", semimembranosus)
    monkeypatch.setattr(run, "find_fibula", fibula)
    for name in ("acl_slice", "lcl_slice", "retinacula_slice", "biceps_femoris_slice"):
        monkeypatch.setattr(run, name, lambda *args, name=name: f"abstain_{name}")

    real_name, real_save = run.name_sartorius, run.save

    def sartorius(own, source):
        order.append(("sartorius", own.series.row.series_uid, type(source).__name__))
        real_name(own, source)

    def save(run_dir, uid, record, arrays):
        order.append(
            ("save", record["series_uid"], record.get("main_slice", {}).get("object"))
        )
        return real_save(run_dir, uid, record, arrays)

    monkeypatch.setattr(run, "name_sartorius", sartorius)
    monkeypatch.setattr(run, "save", save)
    result = run.measure_study(
        cast(run.Corpus, None), "study", tmp_path / "run", tmp_path / "main", False
    )
    return order, result


def test_the_group_is_resolved_once_and_its_places_are_consumed_before_any_middle_save(
    study,
):
    order, _ = study
    assert [e for e in order if e[0] == "semimembranosus"] == [
        ("semimembranosus", "sg"),
        ("semimembranosus", "ax"),
    ]  # one call per series, never a second pass
    first_middle_save = next(
        i for i, e in enumerate(order) if e[0] == "save" and e[2] is None
    )
    sartorius = [i for i, e in enumerate(order) if e[0] == "sartorius"]
    group_save = order.index(("save", "ax", "semimembranosus"))
    assert sartorius and max(sartorius) < first_middle_save
    assert group_save < min(sartorius)
    assert order.index(("fibula",)) > max(sartorius)
    assert all(e[2] == "ndarray" for e in order if e[0] == "sartorius")
    # every middle save still happens inside the fibula loop, as before: after the fibula's turn
    middle = [i for i, e in enumerate(order) if e[0] == "save" and e[2] is None]
    assert len(middle) == 2 and all(i > order.index(("fibula",)) for i in middle[1:])


def test_every_earlier_record_and_silence_is_kept_once_with_the_sartorius_beside_them(
    study,
):
    _, result = study
    mains = [
        r
        for r in result["main_records"]
        if r["main_slice"]["object"] == "semimembranosus"
    ]
    assert len(mains) == 1 and mains[0]["series_uid"] == "ax"
    assert {r["series_uid"] for r in result["records"]} == {"ax", "sg"}
    assert result["main_unread"] == {
        "sg:semimembranosus": "abstain_leg_runs_in_the_plane",
        "sg:semitendinosus": "abstain_leg_runs_in_the_plane",
        "sg:gracilis": "abstain_leg_runs_in_the_plane",
        "sg:acl": "abstain_acl_slice",
        "ax:acl": "abstain_acl_slice",
        "sg:lcl": "abstain_lcl_slice",
        "sg:popliteus_tendon": "abstain_lcl_slice",
        "ax:lcl": "abstain_lcl_slice",
        "ax:popliteus_tendon": "abstain_lcl_slice",
        **{
            f"{uid}:{name}": "abstain_retinacula_slice"
            for uid in ("sg", "ax")
            for name in (
                "patellar_retinacula",
                "medial_patellar_retinaculum",
                "lateral_patellar_retinaculum",
            )
        },
        "sg:biceps_femoris_tendon": "abstain_biceps_femoris_slice",
        "ax:biceps_femoris_tendon": "abstain_biceps_femoris_slice",
        "sg:fibula": "abstain_header_names_no_knee",
        "ax:fibula": "abstain_header_names_no_knee",
    }
    by_uid = {r["series_uid"]: r for r in result["records"]}
    assert by_uid["ax"]["assignments"]["codes"]["sartorius"] == "identified"
    assert "a2_sartorius" in by_uid["ax"]["arrays"]
    assert (
        by_uid["sg"]["assignments"]["codes"]["sartorius"]
        == "abstain_leg_runs_in_the_plane"
    )
    # the saved middle slice's own names are the digest of what the slice made alone
    assert result["named"]["sartorius"] == 1
