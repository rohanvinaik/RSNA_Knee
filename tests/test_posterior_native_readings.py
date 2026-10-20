import copy
import inspect
from dataclasses import replace
from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest

from knee.collapse.local_native import (
    enclosed_components_at_source,
    enclosed_context,
    enclosed_target_contacts,
)
from knee.collapse.observations import Unresolved
from knee.collapse.physical import PlaneFrame
from knee.objects import assignments as A
from knee.telemetry import computing, recording
from scripts import run_interiors as ri

STUDY = "STUDY"
AX = np.array([1.0, 0, 0, 0, 1.0, 0])  # (r, c) -> x = c, y = r
SAG = np.array([0.0, 1.0, 0.0, 0.0, 0.0, -1.0])  # (r, c) -> (x, c, 20 - r)


def _unit_frame(position=(0.0, 0.0, 0.0), orientation=AX, spacing=(1.0, 1.0)):
    return PlaneFrame.from_dicom(np.array(position), orientation, spacing)


def _same(a, b):
    assert a.keys() == b.keys()
    for key in a:
        if isinstance(a[key], np.ndarray):
            np.testing.assert_array_equal(a[key], b[key])
        else:
            assert a[key] == b[key], key


# ---------------------------------------------------------------- local_native
def _two_pocket_crop():
    raw = np.full((9, 12), 10.0)
    raw[4, 2] = 1.0
    raw[4, 8] = 1.0
    available = np.ones(raw.shape, dtype=bool)
    t1 = np.zeros(raw.shape, dtype=bool)
    t1[4, 3:6] = True  # contacts only the left pocket
    t2 = np.zeros(raw.shape, dtype=bool)
    t2[4, 6:8] = True  # contacts only the right pocket
    return raw, available, t1, t2


def test_shared_context_measures_enclosure_once_and_matches_one_shot(monkeypatch):
    frame = _unit_frame()
    raw, available, t1, t2 = _two_pocket_crop()
    calls = []
    real = A.enclosed_darkness

    def spy(plane):
        calls.append(plane.shape)
        return real(plane)

    monkeypatch.setattr(A, "enclosed_darkness", spy)
    context = enclosed_context(raw, available, frame)
    assert calls == []  # validation is cheap; nothing heavy yet
    r1 = enclosed_target_contacts(context, t1)
    r2 = enclosed_target_contacts(context, t2)
    assert calls == [raw.shape]
    assert r1["contacted_component_count"] == 1 and r2["contacted_component_count"] == 1
    assert r1["contacted_component_ids"] != r2["contacted_component_ids"]
    calls.clear()
    _same(r1, enclosed_components_at_source(raw, available, t1, frame))
    _same(r2, enclosed_components_at_source(raw, available, t2, frame))
    assert len(calls) == 2  # the one-shot API still measures per call


def test_early_outs_never_pay_for_the_enclosure(monkeypatch):
    frame = _unit_frame()
    raw, available, t1, _ = _two_pocket_crop()
    monkeypatch.setattr(
        A,
        "enclosed_darkness",
        lambda _p: (_ for _ in ()).throw(AssertionError("heavy")),
    )
    context = enclosed_context(raw, available, frame)
    assert (
        enclosed_target_contacts(context, np.zeros_like(t1))["status"]
        == "target_missing"
    )
    none = enclosed_context(raw, np.zeros_like(available), frame)
    assert enclosed_target_contacts(none, t1)["status"] == "no_available_pixels"
    hole = available.copy()
    hole[t1] = False
    assert (
        enclosed_target_contacts(enclosed_context(raw, hole, frame), t1)["status"]
        == "target_unavailable"
    )


def test_context_and_contacts_name_malformed_inputs():
    frame = _unit_frame()
    raw, available, t1, _ = _two_pocket_crop()
    assert (
        enclosed_context(np.ones(3), available, frame)["status"]
        == "malformed_raw_shape"
    )
    assert enclosed_context(raw, available.astype(np.uint8), frame)["status"] == (
        "malformed_availability_dtype"
    )
    assert (
        enclosed_context(raw, available, cast(Any, None))["status"] == "invalid_frame"
    )
    bad = enclosed_context(np.ones(3), available, frame)
    assert enclosed_target_contacts(bad, t1)["status"] == "malformed_raw_shape"
    context = enclosed_context(raw, available, frame)
    assert (
        enclosed_target_contacts(context, t1[:, :3])["status"]
        == "malformed_target_shape"
    )
    assert enclosed_target_contacts(context, t1.astype(np.uint8))["status"] == (
        "malformed_target_dtype"
    )
    assert enclosed_target_contacts(cast(Any, None), t1)["status"] == "invalid_context"


# ------------------------------------------------------------- run_interiors
def _series(uid, volume, thickness):
    return SimpleNamespace(
        row=SimpleNamespace(series_uid=uid),
        volume=volume,
        slice_thickness_mm=thickness,
        geometry=object(),
        slices=[] if volume is None else list(range(len(volume))),
    )


def _measured(uid, view, series):
    return SimpleNamespace(
        series=series,
        record={"series_uid": uid, "view": view, "slice_index": 0},
        arrays={},
        frame=None,
    )


@pytest.fixture
def world(monkeypatch):
    plane = np.full((40, 40), 10.0)
    plane[20, 9] = 1.0
    plane[20, 13] = 1.0
    frames = {
        "ax": [_unit_frame((0, 0, 0)), _unit_frame((0, 0, 1))],
        "sag": [_unit_frame((2.0 * i, 0, 20), SAG) for i in range(5)],
        "far": [_unit_frame((50.0 + 2.0 * i, 0, 20), SAG) for i in range(5)],
    }
    measured = [
        _measured(
            "ax", ("axial", "0", "0"), _series("ax", np.zeros((2, 40, 40)), [3.0, 3.0])
        ),
        _measured(
            "sag",
            ("sagittal", "1", "1"),
            _series("sag", np.stack([plane] * 5), [2.0] * 5),
        ),
        _measured(
            "far",
            ("sagittal", "0", "0"),
            _series("far", np.stack([plane] * 5), [2.0] * 5),
        ),
    ]
    exterior = {"mask": np.zeros((40, 40), dtype=bool)}
    monkeypatch.setattr(ri, "plane_frame", lambda s, z: frames[s.row.series_uid][z])
    monkeypatch.setattr(ri, "finite_of", lambda s: np.isfinite(np.asarray(s.volume)))
    monkeypatch.setattr(ri, "margin_of", lambda uid, z, p: exterior["mask"])
    monkeypatch.setattr(ri, "SQUINT_TILE_MM", 2.0, raising=False)

    def source(name, rows, cols, z=0):
        mask = np.zeros((40, 40), dtype=bool)
        mask[rows[0] : rows[1], cols[0] : cols[1]] = True
        code = ri.OBJECT_CODES[name]
        record = {
            "series_uid": "ax",
            "view": ("axial", "0", "0"),
            "slice_index": z,
            "assignments": {"codes": {name: "identified"}},
        }
        return ri.PosteriorSource(
            name,
            record,
            {"a1_objects": np.where(mask, code, 0).astype(np.int32)},
            frames["ax"][z],
            mask,
            "a1_objects",
            code,
            str(ri.artifact_of(STUDY, record)),
            int(mask.sum()),
        )

    return SimpleNamespace(
        measured=measured, source=source, frames=frames, exterior=exterior
    )


def _run(world, sources):
    with recording(), computing():
        return ri.posterior_readings_from_sources(world.measured, sources, STUDY)


def _pair(world):
    return [
        world.source("semimembranosus", (10, 13), (4, 7)),
        world.source("semitendinosus", (14, 16), (4, 7)),
    ]


def test_overlapping_queries_share_one_cropped_context_per_tied_plane(
    world, monkeypatch
):
    seen = []
    real = A.enclosed_darkness

    def spy(plane):
        seen.append(plane.copy())
        return real(plane)

    monkeypatch.setattr(A, "enclosed_darkness", spy)
    said = _run(world, _pair(world))
    # tied maximum planes 2 and 3: one heavy reading each, two objects each, cropped (5, 10)
    assert [p.shape for p in seen] == [(5, 10), (5, 10)]
    assert all(np.isfinite(p).all() for p in seen)
    here, missing = said[1]
    assert missing == []
    by = {(o.object, o.slices[0]): o for o in here}
    assert set(by) == {
        ("semimembranosus", 2),
        ("semimembranosus", 3),
        ("semitendinosus", 2),
        ("semitendinosus", 3),
    }
    arrays = world.measured[1].arrays
    stack = arrays[ri.READING_SUPPORT_KEY]
    a, b = by[("semimembranosus", 2)], by[("semitendinosus", 2)]
    # all-contacted ambiguous support: A touches both pockets, B only one
    assert {tuple(p) for p in np.argwhere(stack[a.row])} == {(20, 9), (20, 13)}
    assert {tuple(p) for p in np.argwhere(stack[b.row])} == {(20, 13)}
    assert a.count == int(stack[a.row].sum()) == 2 and b.count == 1
    assert (a.provenance, a.kind, a.label) == ("native", "reading", None)
    assert a.support == ri.READING_SUPPORT_KEY
    assert a.artifact == str(ri.artifact_of(STUDY, world.measured[1].record))
    assert a.view == ("sagittal", "1", "1") and a.series_uid == "sag"
    assert "tied" not in a.note  # distinct sources, not an area tie
    np.testing.assert_array_equal(
        arrays["a22_posterior_context0_window_rc_exclusive"], [18, 23, 8, 18]
    )
    assert arrays["a22_posterior_context0_raw"].shape == (5, 10)
    assert arrays["a22_posterior_context0_enclosed_depth"].shape == (5, 10)
    assert arrays["a22_posterior_context0_m0_semimembranosus_components"].shape == (
        2,
        6,
    )
    # axial control: no readings; far acquisition: named, not absent
    assert said[0] == ([], [])
    assert said[2][0] == []
    assert {(u.object, u.code) for u in said[2][1]} == {
        ("semimembranosus", "source_outside_target_slabs"),
        ("semitendinosus", "source_outside_target_slabs"),
    }
    assert all(
        u.provenance == "native" and u.view == ("sagittal", "0", "0")
        for u in said[2][1]
    )
    prof = arrays["a22_posterior_semimembranosus_s0_profile_in_frame_count"]
    assert prof.tolist() == [0, 0, 6, 6, 0]
    assert arrays["a22_posterior_semimembranosus_s0_profile_selected"].tolist() == [
        False,
        False,
        True,
        True,
        False,
    ]


def test_unseen_exterior_and_nonfinite_cannot_become_dark_support(world):
    ext = np.zeros((40, 40), dtype=bool)
    ext[:, 9] = True
    world.exterior["mask"] = ext
    here, _ = _run(world, _pair(world))[1]
    stack = world.measured[1].arrays[ri.READING_SUPPORT_KEY]
    by = {(o.object, o.slices[0]): o for o in here}
    assert {tuple(p) for p in np.argwhere(stack[by[("semimembranosus", 2)].row])} == {
        (20, 13)
    }
    assert not stack[:, 20, 9].any()


def test_nonfinite_pocket_leaves_named_unresolved_not_absence(world):
    world.measured[1].series.volume[:, 20, 13] = np.nan
    here, missing = _run(world, _pair(world))[1]
    assert {o.object for o in here} == {"semimembranosus"}
    assert [(u.object, u.code) for u in missing] == [
        ("semitendinosus", "enclosed_darkness_not_in_source_contact")
    ]


def test_nothing_enclosed_in_context_is_named_unresolved(world):
    for m in world.measured[1:]:
        m.series.volume[:] = 10.0
    here, missing = _run(world, _pair(world))[1]
    assert here == []
    assert {u.code for u in missing} == {"no_enclosed_darkness_in_query_context"}


def test_null_empty_malformed_and_axial_inputs_are_quiet(world):
    assert _run(world, []) == [([], []), ([], []), ([], [])]
    assert ri.posterior_readings_from_sources([], [], STUDY) == []
    weird = _measured("w", ("sagittal",), _series("w", np.zeros((1, 4, 4)), [1.0]))
    odd = _measured("o", (), _series("o", np.zeros((1, 4, 4)), [1.0]))
    with recording(), computing():
        said = ri.posterior_readings_from_sources([weird, odd], _pair(world), STUDY)
    assert said[0][0] == [] and said[1] == ([], [])
    assert {u.code for u in said[0][1]} == {"source_series_not_measured"}


def test_actual_thickness_and_oblique_normal_define_the_half_slab(monkeypatch):
    a = np.pi / 6
    orient = np.concatenate(([1.0, 0, 0], [0, np.cos(a), np.sin(a)]))
    base = PlaneFrame.from_dicom(np.array([5.0, 5.0, 5.0]), orient, (1.0, 1.0))
    n = base.normal()
    points = base.to_patient(np.array([[10.0, 10.0], [11.0, 12.0], [12.0, 14.0]]))
    points = points + np.array([0.05, 0.4, 1.1])[:, None] * n
    frames = [
        PlaneFrame(base.origin_lps + k * n, base.basis_lps, (1.0, 1.0))
        for k in range(3)
    ]
    monkeypatch.setattr(ri, "plane_frame", lambda s, z: frames[z])

    def planes(thickness):
        own = SimpleNamespace(
            series=_series("t", np.zeros((3, 40, 40)), [thickness] * 3)
        )
        return ri.posterior_source_planes(cast(ri.Measured, own), points)

    one, why = planes(1.0)
    assert why is None
    assert [p["slab_count"] for p in one] == [2, 1, 0]
    assert [p["z"] for p in ri.posterior_max_planes(one)[0]] == [0]
    assert one[0]["nearest_mm"] == pytest.approx(0.05)
    two, _ = planes(2.0)
    assert [p["slab_count"] for p in two] == [2, 3, 1]
    assert [p["z"] for p in ri.posterior_max_planes(two)[0]] == [1]


def test_unreadable_target_geometry_is_not_called_absence(monkeypatch):
    points = np.array([[1.0, 1.0, 1.0]])
    monkeypatch.setattr(ri, "plane_frame", lambda s, z: _unit_frame((0, 0, z)))
    own = SimpleNamespace(
        series=_series("t", np.zeros((2, 8, 8)), [None, float("nan")])
    )
    got, why = ri.posterior_source_planes(cast(ri.Measured, own), points)
    assert why is None and {p["status"] for p in got} == {
        "target_thickness_unavailable"
    }
    assert ri.posterior_max_planes(got) == ([], "target_slab_geometry_unavailable")
    assert ri.posterior_source_planes(
        cast(ri.Measured, SimpleNamespace(series=_series("t", None, []))), points
    ) == (
        [],
        "target_volume_unavailable",
    )
    assert ri.posterior_max_planes([]) == ([], "source_outside_target_slabs")


def test_source_on_slab_but_outside_frame_is_named(monkeypatch):
    monkeypatch.setattr(ri, "plane_frame", lambda s, z: _unit_frame((0, 0, 0)))
    own = SimpleNamespace(series=_series("t", np.zeros((1, 8, 8)), [2.0]))
    planes, _ = ri.posterior_source_planes(
        cast(ri.Measured, own), np.array([[100.0, 100.0, 0.0]])
    )
    assert ri.posterior_max_planes(planes) == (
        [],
        "source_on_target_slabs_outside_frame",
    )


@pytest.mark.parametrize(
    "change,fault",
    [
        (
            lambda s: replace(s, record={**s.record, "series_uid": "zzz"}),
            "source_series_not_measured",
        ),
        (lambda s: replace(s, name="femur"), "source_not_a_posterior_reading_object"),
        (
            lambda s: replace(
                s,
                record={
                    **s.record,
                    "assignments": {"codes": {s.name: "laid_from_its_partner"}},
                },
            ),
            "source_code_not_native_named",
        ),
        (
            lambda s: replace(s, record={**s.record, "view": ("coronal", "0", "0")}),
            "source_view_mismatch",
        ),
        (
            lambda s: replace(s, record={**s.record, "slice_index": 9}),
            "source_slice_out_of_range",
        ),
        (lambda s: replace(s, mask=s.mask[:, :5]), "source_mask_shape_mismatch"),
        (lambda s: replace(s, pixels=s.pixels + 1), "source_count_mismatch"),
        (lambda s: replace(s, label=s.label + 1), "source_label_mismatch"),
        (lambda s: replace(s, artifact="elsewhere"), "source_artifact_mismatch"),
        (lambda s: replace(s, frame=_unit_frame((0, 0, 7))), "source_frame_mismatch"),
        (None, None),
    ],
)
def test_source_identity_is_validated_against_real_arrays_and_geometry(
    world, change, fault
):
    good = world.source("gracilis", (10, 13), (4, 7))
    by_uid = {m.record["series_uid"]: m for m in world.measured}
    source = good if change is None else change(good)
    assert ri._posterior_source_fault(source, by_uid, STUDY) == fault


def test_mask_that_is_not_the_support_pixels_is_rejected(world):
    good = world.source("gracilis", (10, 13), (4, 7))
    mask = good.mask.copy()
    mask[30, 30] = True
    bad = replace(good, mask=mask, pixels=int(mask.sum()))
    by_uid = {m.record["series_uid"]: m for m in world.measured}
    assert (
        ri._posterior_source_fault(bad, by_uid, STUDY)
        == "source_mask_not_support_pixels"
    )


def test_source_guard_checks_actual_series_and_owning_slice(world):
    source = world.source("gracilis", (10, 13), (4, 7), z=0)
    by_uid = {m.record["series_uid"]: m for m in world.measured}
    original = world.measured[0]
    mismatched_owner = SimpleNamespace(
        series=_series("different-actual-series", original.series.volume, [3.0, 3.0]),
        record=original.record,
        arrays=original.arrays,
    )
    assert (
        ri._posterior_source_fault(
            source, {"ax": cast(ri.Measured, mismatched_owner)}, STUDY
        )
        == "source_series_uid_mismatch"
    )

    changed_slice = replace(source, record={**source.record, "slice_index": 1})
    assert (
        ri._posterior_source_fault(changed_slice, by_uid, STUDY)
        == "source_frame_mismatch"
    )


def test_unique_largest_selection_keeps_ties_and_invalid_sources(world):
    a = world.source("gracilis", (10, 13), (4, 7), z=0)  # 9 px
    b = world.source("gracilis", (20, 23), (4, 7), z=1)  # 9 px: exact tie
    c = world.source("gracilis", (30, 32), (4, 7), z=0)  # 4 px
    bigger_but_bad = replace(world.source("gracilis", (0, 8), (0, 8)), label=-5)
    selected, faults, candidates = ri.posterior_reading_selection(
        world.measured, [a, b, c, bigger_but_bad], STUDY
    )
    assert selected["gracilis"] == [a, b]
    assert faults == [(bigger_but_bad, "source_label_mismatch")]
    assert [row["selected"] for row in candidates["gracilis"]] == [
        True,
        True,
        False,
        False,
    ]
    assert [row["fault"] for row in candidates["gracilis"]][
        3
    ] == "source_label_mismatch"
    selected, _, _ = ri.posterior_reading_selection(world.measured, [a, c], STUDY)
    assert selected["gracilis"] == [a]


def test_tied_sources_retain_every_reading_and_name_the_tie(world):
    a = world.source("gracilis", (10, 13), (4, 7), z=0)
    b = world.source("gracilis", (10, 13), (4, 7), z=1)
    here, _ = _run(world, [a, b])[1]
    assert len(here) == 4 and all("exactly tied largest areas" in o.note for o in here)


def test_invalid_source_is_retained_as_named_unresolved(world):
    bad = replace(world.source("gracilis", (10, 13), (4, 7)), pixels=1)
    said = _run(world, [bad])
    assert said[0][1] == [
        Unresolved(
            "gracilis", "native", "ax", ("axial", "0", "0"), "source_count_mismatch"
        )
    ]
    assert said[1] == ([], [])


def test_merge_query_windows_overlap_touch_chain_and_disjoint():
    m = ri.merge_query_windows
    assert m([(0, 5, 0, 5), (3, 9, 4, 8)]) == [([0, 1], (0, 9, 0, 8))]
    assert m([(0, 5, 0, 5), (5, 9, 0, 5)]) == [([0], (0, 5, 0, 5)), ([1], (5, 9, 0, 5))]
    assert m([(0, 4, 0, 4), (20, 24, 0, 4)]) == [
        ([0], (0, 4, 0, 4)),
        ([1], (20, 24, 0, 4)),
    ]
    chain = m([(0, 4, 0, 4), (10, 14, 0, 4), (3, 11, 0, 4)])
    assert chain == [([0, 1, 2], (0, 14, 0, 4))]


def test_query_window_is_extent_plus_one_tile_in_native_spacing(monkeypatch):
    monkeypatch.setattr(ri, "SQUINT_TILE_MM", 3.0, raising=False)
    frame = _unit_frame(spacing=(1.0, 0.5))
    rc = np.array([[10, 10], [12, 11]], dtype=np.int32)
    assert ri.posterior_query_window(rc, frame, (40, 40)) == (7, 16, 4, 18)
    assert ri.posterior_query_window(rc[:1] * 0, frame, (40, 40)) == (
        0,
        4,
        0,
        7,
    )  # clipped
    bad = PlaneFrame(frame.origin_lps, frame.basis_lps, (np.nan, 1.0))
    assert ri.posterior_query_window(rc, bad, (40, 40)) is None


def test_driver_uses_posterior_sayings_sources_and_preserves_original_fields(
    world, monkeypatch
):
    a = world.source("semimembranosus", (10, 13), (4, 7))
    calls = []

    def fake(record, arrays, frame, parts, study_uid, by_silence):
        calls.append((tuple(p[0] for p in parts), by_silence))
        return [], [], ([a] if record["series_uid"] == "ax" else []), set()

    monkeypatch.setattr(ri, "posterior_sayings", fake)
    before = copy.deepcopy([m.record for m in world.measured])
    with recording(), computing():
        said = ri.posterior_readings_from_sources(
            world.measured,
            ri.posterior_reading_sources(world.measured, [], STUDY),
            STUDY,
        )
    assert [
        {k: v for k, v in m.record.items() if k != "a22_posterior_readings"}
        for m in world.measured
    ] == before
    retained = world.measured[1].record["a22_posterior_readings"]
    assert retained and retained[0]["reading"]["enclosure_status"] == "present"
    prefix = retained[0]["context_prefix"]
    assert all(
        f"{prefix}_{key}" in world.measured[1].arrays
        for key in (
            "depth_input",
            "enclosed_depth",
            "positive_enclosure",
            "labels",
            "unavailable_boundary",
        )
    )
    assert len(calls) == 3 and all(set(n) <= set(ri.READING_NAMES) for n, _ in calls)
    assert any(o.object == "semimembranosus" for o in said[1][0])


def test_readings_are_appended_once_through_keep_recess(world, monkeypatch):
    said = _run(world, _pair(world))
    kept = []
    monkeypatch.setattr(
        ri,
        "keep_on_record",
        lambda record, here, missing: kept.append((record, here, missing)),
    )
    ri.keep_recess(world.measured, said)
    assert [r["series_uid"] for r, _, _ in kept] == ["sag", "far"]  # axial had nothing
    assert kept[0][1] is said[1][0] and kept[1][2] is said[2][1]


def test_grouped_description_publishes_addressed_reading(world):
    """Depends on the real keep_on_record/describe_objects record shape (minimal record here)."""
    said = _run(world, _pair(world))
    ri.keep_recess(world.measured, said)
    described = ri.describe_objects(
        [m.record for m in world.measured], ri.MAP_NAMES, {}
    )
    text = repr(described)
    assert "source_contacted_enclosed_darkness" in text
    assert ri.READING_SUPPORT_KEY in text


def test_measure_study_wiring_is_one_late_shared_reading_pass():
    src = inspect.getsource(ri.measure_study)
    assert "posterior_native_readings(" not in src
    assert src.count("late_native_readings(") == 1
    first_index = src.index("index_posterior(measured, EARLY_MIDDLE_PARTS, group_found")
    joint = src.index("joint_existing(")
    late_index = src.index("(*LATE_MIDDLE_PARTS, *CONTEXT_MIDDLE_PARTS)")
    reading = src.index("late_native_readings(")
    appended = src.index("keep_recess(measured, posterior_reading_said)")
    group_save = src.index("save_study_record(main_run, part_record, part_arrays)")
    assert first_index < group_save < joint < late_index < reading < appended
    final_save = src.index("save_study_record(run_dir, own.record, own.arrays)")
    assert reading < final_save
    assert src.count("keep_recess(measured, posterior_reading_said)") == 1
    assert appended < final_save
    assert src.count("save_study_record(run_dir, own.record, own.arrays)") == 1
    assert "late_main_records" in src
    assert (
        'reads("posterior_readings", ("observations", "unresolved"), "keep_recess")'
        in src
    )
