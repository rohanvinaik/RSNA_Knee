"""The bone lens shares its existing profile scope and keeps the crop's native address."""

from types import SimpleNamespace
from typing import Any, cast

import numpy as np

from knee.objects.interiors import InteriorRegions
from knee.telemetry import computing, recording
from scripts import run_interiors as run


def _profile(windows: Any, depth: int = 2) -> Any:
    return SimpleNamespace(
        window_rc=np.asarray(windows, dtype=np.int32).reshape(depth, 4), fine=()
    )


def _plane_frame():
    return run.PlaneFrame(
        np.zeros(3),
        np.asarray([[1.0, 0.0], [0.0, 2.0], [0.0, 0.0]]),
        (1.0, 2.0),
    )


def _quiet(monkeypatch):
    monkeypatch.setattr(run, "reads", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(run, "handed", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(run, "plane_frame", lambda *_args: _plane_frame())
    monkeypatch.setattr(
        run,
        "lens_scopes_of",
        lambda series, _split: tuple(
            run.full_frame_scope(series.volume[z].shape, reason="test fixture")
            for z in range(len(series.volume))
        ),
    )


def _own():
    volume = np.arange(2 * 8 * 9, dtype=np.float32).reshape(2, 8, 9)
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid="bounded-bones", fat_suppression="0"),
        volume=volume,
        geometry=SimpleNamespace(position=[np.zeros(3), np.array([0.0, 0.0, 3.0])]),
        slice_thickness_mm=(3.0, 3.0),
    )
    return SimpleNamespace(
        series=series,
        record={
            "series_uid": "bounded-bones",
            "slice_index": 0,
            "background_split": 1.0,
            "assignments": {"femur": 1, "tibia": 2},
            "view": ["Coronal", "1", "1"],
        },
        arrays={
            "acquired_plane": volume[0],
            "a1_objects": np.zeros((8, 9), dtype=np.int8),
        },
        frame=_plane_frame(),
        stack=SimpleNamespace(code="present"),
    )


def _windows():
    femur = _profile([[0, 8, 0, 9], [1, 5, 2, 6]])
    tibia = _profile([[0, 8, 0, 9], [3, 7, 0, 4]])
    return {"femur": femur, "tibia": tibia}


def test_native_window_union_is_half_open_clamped_and_falls_back_explicitly():
    profiles = _windows()
    got = run.bone_plane_window_map(profiles, [(8, 9), (8, 9)])
    assert got[1].window_rc == (1, 7, 0, 6)
    assert got[1].code == "profile_window_union"

    clipped = {
        "femur": _profile([[0, 8, 0, 9], [2, 10, 4, 15]]),
        "tibia": _profile([[0, 8, 0, 9], [3, 7, 1, 6]]),
    }
    clipped_scope = run.bone_plane_window_map(clipped, [(8, 9), (8, 9)])[1]
    assert clipped_scope.window_rc == (2, 8, 1, 9)
    assert "femur_profile_window_clamped" in clipped_scope.reason

    missing = {
        "femur": _profile([[0, 8, 0, 9], [-1, -1, -1, -1]]),
        "tibia": _profile([[0, 8, 0, 9], [-1, -1, -1, -1]]),
    }
    fallback = run.bone_plane_window_map(missing, [(8, 9), (8, 9)])[1]
    assert fallback.window_rc == (0, 8, 0, 9)
    assert fallback.code == "full_frame_fallback_missing_profile_window"
    assert "profile_no_fine_window" in fallback.reason

    one_useful = {
        "femur": _profile([[0, 8, 0, 9], [2, 6, 3, 7]]),
        "tibia": _profile([[0, 8, 0, 9], [-1, -1, -1, -1]]),
    }
    single = run.bone_plane_window_map(one_useful, [(8, 9), (8, 9)])[1]
    assert single.window_rc == (2, 6, 3, 7)
    assert single.code == "profile_window_single"
    assert "femur_present" in single.reason
    assert "missing_tibia_profile_no_fine_window" in single.reason


def test_both_bones_share_one_crop_scatter_for_naming_and_keep_local_arrays(
    monkeypatch,
):
    _quiet(monkeypatch)
    own = _own()
    available = np.ones(own.series.volume.shape, dtype=bool)
    available[1, 4, 3] = False
    monkeypatch.setattr(run, "finite_of", lambda _series: available)
    crop_shapes = []

    def interior_reader(raw, spacing, split, prominence, *, available, scope=None):
        crop_shapes.append(raw.shape)
        assert spacing == (1.0, 2.0) and split == 1.0
        assert prominence == run.PROMINENCE_MM
        labels = np.zeros(raw.shape, dtype=np.int32)
        labels[2:4, 2:4] = 7
        return InteriorRegions(
            "measured",
            raw < 20,
            available.copy(),
            np.arange(raw.size, dtype=np.float64).reshape(raw.shape),
            np.ones(raw.shape, dtype=np.int32),
            labels,
        )

    monkeypatch.setattr(run, "interior_regions", interior_reader)
    monkeypatch.setattr(
        run,
        "bone_footprint",
        lambda _series, _z, _frame, shape, _places, _key: np.zeros(shape, dtype=bool),
    )
    profiles = _windows()
    scopes = run.bone_plane_window_map(profiles, [(8, 9), (8, 9)])
    femur_places = np.asarray([[1.0, 0.0, 0.0]])
    tibia_places = np.asarray([[2.0, 0.0, 0.0]])

    with computing(), recording():
        femur = run.bone_plane_read(
            cast(Any, own),
            "femur",
            1,
            femur_places,
            tibia_places,
            cast(Any, profiles["femur"]),
            plane_windows=scopes,
        )
        tibia = run.bone_plane_read(
            cast(Any, own),
            "tibia",
            1,
            tibia_places,
            femur_places,
            cast(Any, profiles["tibia"]),
            plane_windows=scopes,
        )
        assert femur.local_lens is tibia.local_lens
        assert femur.labels is tibia.labels
        assert femur.available is tibia.available

        femur_read = run.BoneRead(
            "femur", profiles["femur"], (femur,), "unresolved", {}, {}, ()
        )
        tibia_read = run.BoneRead(
            "tibia", profiles["tibia"], (tibia,), "unresolved", {}, {}, ()
        )
        run.keep_bone_planes(cast(Any, own), {"femur": femur_read, "tibia": tibia_read})
        _, full_reading, _ = run.lens_of(
            own.series,
            1,
            own.series.volume[1],
            _plane_frame(),
            1.0,
        )

    assert crop_shapes == [(6, 6), (8, 9)]
    assert full_reading.labels.shape == (8, 9)
    assert femur.local_lens is not None
    local = femur.local_lens
    assert local.window_rc == (1, 7, 0, 6)
    assert local.scope_code == "profile_window_union"
    assert local.raw_crop.shape == (6, 6)
    assert not local.available_crop[3, 3]
    assert not local.available_full[0, 0]
    assert not local.labels_full[0, 0]
    np.testing.assert_array_equal(local.labels_full[1:7, 0:6], local.labels_crop)
    assert own.arrays["a3_bone_lens_slices"].tolist() == [1]
    assert own.arrays["a3_bone_lens_windows_rc"].tolist() == [[1, 7, 0, 6]]
    assert own.arrays["a3_bone_lens_crop_shapes"].tolist() == [[6, 6]]
    assert own.arrays["a3_bone_lens_crop_offsets"].tolist() == [0, 36]
    assert own.arrays["a3_bone_lens_crop_raw"].shape == (36,)
    assert own.arrays["a3_bone_lens_crop_available"].sum() == 35


def test_missing_profile_window_uses_an_explicit_full_frame_lens(monkeypatch):
    _quiet(monkeypatch)
    own = _own()
    available = np.ones(own.series.volume.shape, dtype=bool)
    monkeypatch.setattr(run, "finite_of", lambda _series: available)
    seen_shapes = []

    def interior_reader(raw, spacing, split, prominence, *, available, scope=None):
        seen_shapes.append(raw.shape)
        return InteriorRegions(
            "measured",
            np.zeros(raw.shape, dtype=bool),
            available.copy(),
            np.zeros(raw.shape),
            np.zeros(raw.shape, dtype=np.int32),
            np.zeros(raw.shape, dtype=np.int32),
        )

    monkeypatch.setattr(run, "interior_regions", interior_reader)
    monkeypatch.setattr(
        run,
        "bone_footprint",
        lambda _series, _z, _frame, shape, _places, _key: np.zeros(shape, dtype=bool),
    )
    missing = {
        "femur": _profile([[0, 8, 0, 9], [-1, -1, -1, -1]]),
        "tibia": _profile([[0, 8, 0, 9], [-1, -1, -1, -1]]),
    }
    scopes = run.bone_plane_window_map(missing, [(8, 9), (8, 9)])
    with computing(), recording():
        plane = run.bone_plane_read(
            cast(Any, own),
            "femur",
            1,
            np.asarray([[1.0, 0.0, 0.0]]),
            np.asarray([[2.0, 0.0, 0.0]]),
            missing["femur"],
            plane_windows=scopes,
        )
    assert seen_shapes == [(8, 9)]
    assert plane.local_lens is not None
    assert plane.local_lens.scope_code == "full_frame_fallback_missing_profile_window"
    assert plane.local_lens.scope_reason.endswith("profile_no_fine_window")
    assert plane.local_lens.raw_crop.shape == own.arrays["acquired_plane"].shape


def test_name_the_bones_precomputes_both_profiles_before_first_read(monkeypatch):
    _quiet(monkeypatch)
    own = _own()
    carried = SimpleNamespace(
        femur_lps=np.asarray([[1.0, 0.0, 0.0]]),
        tibia_lps=np.asarray([[2.0, 0.0, 0.0]]),
    )
    events = []
    profiles = {
        "femur": _profile([[0, 8, 0, 9], [1, 5, 2, 6]]),
        "tibia": _profile([[0, 8, 0, 9], [3, 7, 0, 4]]),
    }
    monkeypatch.setattr(
        run, "bone_reading_basis", lambda _own, bone, _places: (np.ones((1, 3)), 100.0)
    )

    def profile_of(_own, bone, *_args):
        events.append(f"profile:{bone}")
        return profiles[bone]

    read_windows = []

    def read_bone(_own, bone, *_args, plane_windows=None, **_kwargs):
        assert events.count("profile:femur") == 1
        assert events.count("profile:tibia") == 1
        events.append(f"read:{bone}")
        read_windows.append(plane_windows)
        return "synthetic_unread"

    monkeypatch.setattr(run, "bone_profile_of", profile_of)
    monkeypatch.setattr(run, "read_bone", read_bone)
    monkeypatch.setattr(run, "artifact_of", lambda *_args: "artifact")

    run.name_the_bones([own], [None], cast(Any, carried), "study")

    assert events[:2] == ["profile:femur", "profile:tibia"]
    assert events[2:] == ["read:femur", "read:tibia"]
    assert read_windows[0] is read_windows[1]
    assert read_windows[0][1].window_rc == (1, 7, 0, 6)
    assert read_windows[0][1].code == "profile_window_union"
