"""The patella question is measured inside its scope before any heavy reading, shares that
measurement with the bones, and keeps both attempts when the local one misses."""

from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest
from scipy import ndimage as ndi

from knee.collapse.physical import PlaneFrame
from knee.objects import assignments as A
from knee.objects.interiors import InteriorRegions
from knee.telemetry import computing, recording
from scripts import run_interiors as run

SHAPE = (48, 40)
FRAME = PlaneFrame(
    np.array([10.0, 20.0, 30.0]),
    np.array(
        [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]]
    ),  # row -> toward the back, column -> up
    (1.0, 1.0),
)
LOCAL = (2, 40, 6, 24)
MISSED = (18, 45, 6, 24)
FIELD_CODES = {"air": "abstain_no_leg", "skin": "abstain_no_air"}


def _feet():
    femur, tibia = np.zeros(SHAPE, bool), np.zeros(SHAPE, bool)
    femur[18:32, 8:22] = True
    tibia[34:40, 8:22] = True
    return {"f": femur, "t": tibia}


@pytest.fixture
def rig(monkeypatch):
    plane = np.full(SHAPE, 5.0)
    plane[20:31, 10:21] = 100.0  # the femur's marrow
    plane[5:12, 11:18] = 100.0  # the patella, in front of it
    volume = np.stack([plane] * 3)
    finite = np.isfinite(volume)
    seen: dict[str, list] = {"lens": [], "field": [], "margin": []}
    asked: list[int] = []
    feet = _feet()

    def lens(raw, spacing, split, prominence, *, available):
        seen["lens"].append(raw.shape)
        mask = raw > 50
        labels, _ = ndi.label(mask)
        return InteriorRegions(
            "measured",
            ~mask,
            available.copy(),
            ndi.distance_transform_edt(mask),
            np.zeros(raw.shape, np.int32),
            labels.astype(np.int32),
        )

    def field(raw, reading, basis, outside=None):
        seen["field"].append(raw.shape)
        return A.Field(
            reading.labels > 0,
            np.zeros(raw.shape, np.int8),
            dict(FIELD_CODES),
            A.territory_peaks(reading.labels, reading.distance_mm, basis),
            (False, True, True),
        )

    def margin(raw):
        seen["margin"].append(raw.shape)
        return np.zeros(raw.shape, bool)

    monkeypatch.setattr(run, "reads", lambda *a, **k: None)
    monkeypatch.setattr(run, "handed", lambda *a, **k: None)
    monkeypatch.setattr(run, "plane_frame", lambda s, z: FRAME)
    monkeypatch.setattr(run, "finite_of", lambda s: asked.append(1) or finite)
    monkeypatch.setattr(run, "bone_footprint", lambda s, z, f, shape, p, key: feet[key])
    monkeypatch.setattr(run, "interior_regions", lens)
    monkeypatch.setattr(run, "read_field", field)
    monkeypatch.setattr(run, "margin", margin)
    row = SimpleNamespace(series_uid="scope", fluid_sensitive="0", fat_suppression="1")
    own = SimpleNamespace(
        series=SimpleNamespace(row=row, volume=volume),
        record={"background_split": 1.0},
        arrays={"acquired_plane": plane},
        frame=FRAME,
    )
    return SimpleNamespace(
        own=own, seen=seen, volume=volume, asked=asked, finite=finite
    )


def ask(own, window, body=None, **kw):
    return run.patella_plane(
        cast(Any, own),
        1,
        np.zeros((1, 3)),
        np.zeros((1, 3)),
        ("f", "t"),
        body,
        profile_window=window,
        **kw,
    )


def test_bounds_are_whole_numbers_never_truncated():
    assert run.integer_bounds(np.array([0, 8, 1, 2], dtype=np.int32)) == (0, 8, 1, 2)
    assert run.integer_bounds((np.int64(1), 5, 2, 9)) == (1, 5, 2, 9)
    assert run.integer_bounds((0.0, 8.0, 1.0, 2.0)) == (0, 8, 1, 2)
    for bad in (
        (2.5, 10, 0, 3), (np.nan, 1, 2, 3), (True, 8, 0, 9), "abcd", None, 7,
        (1, 2, 3), np.zeros((2, 4)), (1, 2, 3, None),
    ):  # fmt: skip
        assert run.integer_bounds(bad) is None, bad
    got = run.patella_scope(SHAPE, (2.5, 30, 0, 20), None, [])
    assert got.window_rc is None and "profile_window_invalid" in got.reason


def test_boxes_normalise_without_raising():
    assert run.map_boxes_of(None) is None
    assert run.map_boxes_of(5) == []
    bad = run.map_boxes_of([(np.nan, 0, 1, 1), "x", (1, 1, -1, 1), 3, (3, 4, 1, 1)])
    assert bad == [(3.0, 4.0, 1.0, 1.0)]
    assert (
        run.map_boxes_of([(1, 2, 3)]) == []
        and run.map_boxes_of([(True, 1, 1, 1)]) == []
    )


def test_scope_union_is_half_open_clamped_and_includes_footprints():
    feet = _feet()
    got = run.patella_scope(
        SHAPE, (2, 36, 6, 24), [(40.0, 30.0, 10.0, 12.0)], [feet["f"], feet["t"]]
    )
    assert got.code == "scope_union" and got.window_rc == (2, 48, 6, 40)
    assert "profile_window" in got.reason and "femur_footprint" in got.reason
    box = run.patella_scope(SHAPE, None, [(10.0, 20.0, 2.0, 3.0)], [])
    assert box.window_rc == (
        8,
        13,
        17,
        24,
    )  # |p - centre| <= half, as the peak filter reads it
    clipped = run.patella_scope(SHAPE, (-5, 10, 30, 99), None, [])
    assert clipped.window_rc == (0, 10, 30, 40)
    assert "profile_window_clamped" in clipped.reason


def test_full_sized_union_missing_and_invalid_scopes_are_named_not_crashes():
    full = run.patella_scope(SHAPE, (0, 48, 0, 40), None, [])
    assert full.window_rc is None and full.code == "scope_union_is_full_frame"
    for window in ((-1, -1, -1, -1), None, "abc", (np.nan, 1, 2, 3), [1, 2]):
        got = run.patella_scope(SHAPE, window, None, [_feet()["f"]])
        assert got.window_rc is None
        assert got.code == "full_frame_no_profile_or_map_domain"


def test_local_frame_moves_the_origin_to_the_crop_first_pixel():
    local = run.local_frame(FRAME, LOCAL)
    np.testing.assert_allclose(
        local.origin_lps, FRAME.to_patient(np.array([[2.0, 6.0]]))[0]
    )
    np.testing.assert_allclose(
        local.to_patient(np.array([[3.0, 4.0]])),
        FRAME.to_patient(np.array([[5.0, 10.0]])),
    )


def test_crop_happens_before_the_heavy_lens_and_native_addresses_are_restored(
    rig, monkeypatch
):
    monkeypatch.setattr(
        run, "lens_of", lambda *a, **k: pytest.fail("whole-frame lens on a local hit")
    )
    body = np.zeros(SHAPE, bool)
    body[6:10, 12:16] = True
    with computing(), recording() as led:
        got = ask(rig.own, (2, 36, 6, 24), body)
        again = run.patella_scope_of(
            rig.own.series, 1, rig.volume[1], FRAME, 1.0, LOCAL, "patella"
        )
        names = {e.name for e in led.events()}
    assert rig.seen["lens"] == rig.seen["field"] == rig.seen["margin"] == [(38, 18)]
    assert got.code == "identified" and got.scope_code == "scope_union"
    assert got.window_rc == LOCAL and got.peak == (8, 14) and got.body_held == 16
    assert got.objects[8, 14] == A.OBJECT_CODES["patella"]
    assert got.labels.shape == got.available.shape == got.objects.shape == SHAPE
    assert got.available[2:40, 6:24].all()
    assert not got.available[0, 0] and not got.available[45, 30]
    assert (
        not got.labels[0, 0] and got.objects[0, 0] == 0
    )  # outside: unavailable, not air
    np.testing.assert_array_equal(got.labels[2:40, 6:24], got.attempts[0].labels)
    assert (6, 8) in [pk.peak_rc for pk in again.field.peaks]  # crop-local peak
    assert again.measures.key == ("scope", 1, LOCAL)
    np.testing.assert_array_equal(
        again.frame.origin_lps, run.local_frame(FRAME, LOCAL).origin_lps
    )
    assert len(rig.seen["lens"]) == 1  # the repeat request was handed the same context
    assert "patella_scope.made" in names and "patella_scope.handed_on" in names
    assert not {"lens.made", "field.made", "margin.made"} & names


def test_bone_and_patella_share_one_scoped_interior_and_finite_support(rig):
    own, volume = rig.own, rig.volume
    bone_scope = run.BonePlaneScope(LOCAL, "profile_window_union", "bone_only_reason")
    with computing(), recording() as led:
        lens = run.bone_local_lens_of(
            own.series, 1, volume[1], FRAME, 1.0, bone_scope, "bones"
        )
        got = ask(own, (2, 36, 6, 24))
        shared = run.scoped_interior_of(
            own.series, 1, volume[1], FRAME.spacing_rc, 1.0, LOCAL
        )
        names = {e.name for e in led.events()}
        assert rig.seen["lens"] == [(38, 18)]  # the same scope was measured once
        assert len(rig.asked) == 1 and np.shares_memory(shared.finite, rig.finite[1])
        assert lens.raw_crop is shared.raw and "scoped_interior.handed_on" in names
        assert got.attempts[0].raw is shared.raw
        assert got.attempts[0].labels is shared.reading.labels
        # the bone's reason stays the bone's; the patella's record names its own scope
        assert lens.scope_reason == "bone_only_reason"
        assert "bone_only_reason" not in got.attempts[0].scope_reason
        assert "bone_only_reason" not in got.scope_reason
        # a different window, or split, is a different measurement
        run.scoped_interior_of(
            own.series, 1, volume[1], FRAME.spacing_rc, 1.0, (0, 10, 0, 10)
        )
        run.scoped_interior_of(own.series, 1, volume[1], FRAME.spacing_rc, 2.0, LOCAL)
    assert rig.seen["lens"] == [(38, 18), (10, 10), (38, 18)]


def test_a_local_miss_keeps_every_reading_and_broadens_to_the_full_frame(rig):
    with computing(), recording() as led:
        got = ask(rig.own, (30, 45, 6, 24))
        names = {e.name for e in led.events()}
    assert rig.seen["lens"] == [(27, 18), (48, 40)]
    assert got.code == "identified" and got.peak == (8, 14) and got.window_rc is None
    assert got.scope_code == "broadened_full_frame_local_scope_missed"
    assert "abstain_no_peak_in_front_of_the_femur" in got.scope_reason
    assert got.available.all() and got.labels.shape == SHAPE  # full-frame, not the crop
    (attempt,) = got.attempts
    assert attempt.window_rc == MISSED and attempt.scope_code == "scope_union"
    assert attempt.code == "abstain_no_peak_in_front_of_the_femur"
    assert attempt.femur == run.IDENTIFIED and attempt.light == pytest.approx(100.0)
    assert attempt.field_codes == FIELD_CODES and attempt.axes_in_plane == (
        False,
        True,
        True,
    )
    assert set(attempt.codes) == {
        "patella", "joint_fluid", "hoffa_fat_pad", "suprapatellar_fat",
    }  # fmt: skip
    np.testing.assert_array_equal(attempt.raw, rig.volume[1][18:45, 6:24])
    for name in (
        "finite", "dark", "distance_mm", "markers", "labels",
        "available", "outside", "leg", "field_objects", "objects",
    ):  # fmt: skip
        assert getattr(attempt, name).shape == (27, 18), name
    np.testing.assert_array_equal(
        attempt.frame_origin_lps, run.local_frame(FRAME, MISSED).origin_lps
    )
    np.testing.assert_array_equal(attempt.frame_basis_lps, FRAME.basis_lps)
    assert {"patella_scope.made", "lens.made", "field.made", "margin.made"} <= names


def test_old_callers_and_positional_construction_still_read_the_whole_frame(rig):
    with computing(), recording():
        got = ask(rig.own, None)
    assert rig.seen["lens"] == [SHAPE] and rig.seen["field"] == [SHAPE]
    assert (
        got.scope_code == "full_frame_no_profile_or_map_domain" and got.attempts == ()
    )
    assert "profile_window_not_given" in got.scope_reason
    old = run.PatellaPlane(
        1, False, "identified", {}, "", "", None, None, None, None, None, None
    )
    assert (
        old.attempts == ()
        and old.window_rc is None
        and old.in_plane == "unguided_in_plane"
    )


def test_persistence_keeps_ragged_offsets_and_every_reading_and_metadata(rig):
    with computing(), recording():
        missed = ask(rig.own, (30, 45, 6, 24))
    arrays = run.patella_arrays(cast(Any, rig.own), [missed], [None])
    attempt, size = missed.attempts[0], 27 * 18
    assert arrays["a3_patella_local_slices"].tolist() == [1]
    assert arrays["a3_patella_local_window_rc"].tolist() == [list(MISSED)]
    assert arrays["a3_patella_local_crop_shapes"].tolist() == [[27, 18]]
    assert arrays["a3_patella_local_crop_offsets"].tolist() == [0, size]
    assert arrays["a3_patella_local_peak_offsets"].tolist() == [0, 1]
    assert arrays["a3_patella_local_peaks"].shape == (1, 5)
    assert arrays["a3_patella_local_peak_columns"].tolist() == [
        "territory",
        "depth_mm",
        "native_row",
        "native_col",
        "local_superior_mm",
    ]
    peak = arrays["a3_patella_local_peaks"][0]
    local_rc = peak[2:4] - np.asarray(MISSED[::2], dtype=np.float64)
    expected_superior = float(FRAME.basis_lps[2] @ local_rc)
    assert peak[4] == pytest.approx(expected_superior)
    assert peak[4] == pytest.approx(9.0)
    for name in (
        "raw", "finite", "dark", "distance_mm", "markers", "labels",
        "available", "outside", "leg", "field_objects", "objects",
    ):  # fmt: skip
        assert arrays[f"a3_patella_local_{name}"].shape == (size,), name
    np.testing.assert_array_equal(
        arrays["a3_patella_local_labels"].reshape(27, 18), attempt.labels
    )
    assert arrays["a3_patella_local_scope_reason"].tolist() == [attempt.scope_reason]
    assert arrays["a3_patella_local_part_code_keys"].tolist() == [
        "hoffa_fat_pad", "joint_fluid", "patella", "suprapatellar_fat",
    ]  # fmt: skip
    assert arrays["a3_patella_local_part_code_offsets"].tolist() == [0, 4]
    assert arrays["a3_patella_local_field_code_keys"].tolist() == ["air", "skin"]
    assert arrays["a3_patella_local_field_code_values"].tolist() == [
        FIELD_CODES["air"], FIELD_CODES["skin"],
    ]  # fmt: skip
    assert arrays["a3_patella_local_in_plane"].tolist() == [[False, True, True]]
    assert arrays["a3_patella_local_in_plane_axes"].tolist() == [
        "side_to_side", "front_to_back", "along_the_leg",
    ]  # fmt: skip
    assert arrays["a3_patella_local_light"][0] == pytest.approx(attempt.light)
    assert arrays["a3_patella_local_body_held"].tolist() == [-1]
    assert arrays["a3_patella_local_frame_basis_lps"].shape == (1, 3, 2)
    np.testing.assert_array_equal(
        arrays["a3_patella_local_frame_origin_lps"][0],
        run.local_frame(FRAME, MISSED).origin_lps,
    )
    codes = dict(
        zip(
            arrays["a3_patella_local_object_code_names"].tolist(),
            arrays["a3_patella_local_object_code_values"].tolist(),
            strict=True,
        )
    )
    assert codes == dict(A.OBJECT_CODES)
    # the plane keeps its full-frame reading beside the crop's, and says it was broadened
    assert arrays["a3_patella_plane_scope_code"].tolist() == [missed.scope_code]
    assert arrays["a3_patella_plane_scope_reason"].tolist() == [missed.scope_reason]
    assert arrays["a3_patella_plane_window_rc"].tolist() == [[-1, -1, -1, -1]]
    assert arrays["a3_patella_plane_labels"].shape == (1, *SHAPE)
    empty = run.patella_arrays(cast(Any, rig.own), [], [])
    assert empty["a3_patella_local_crop_offsets"].tolist() == [0]
    assert empty["a3_patella_local_crop_shapes"].shape == (0, 2)
    assert empty["a3_patella_local_frame_basis_lps"].shape == (0, 3, 2)
