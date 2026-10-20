from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
MODULE_PATH = ROOT / "scripts" / "run_interiors.py"
spec = importlib.util.spec_from_file_location("p7_candidate_runner", MODULE_PATH)
assert spec is not None and spec.loader is not None
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)


def oblique_frame() -> runner.PlaneFrame:
    angle = np.deg2rad(23.0)
    row_axis = np.array([np.cos(angle), np.sin(angle), 0.0]) * 1.7
    col_axis = np.array([-np.sin(angle), np.cos(angle), 0.0]) * 0.55
    basis = np.column_stack((row_axis, col_axis))
    return runner.PlaneFrame(np.array([11.0, -5.0, 27.0]), basis, (1.7, 0.55))


def test_profile_windows_union_all_source_points_and_keep_physical_padding(monkeypatch):
    frame = oblique_frame()
    shape = (64, 80)
    spans = {
        "hoffa_fat_pad": (12.0, 8.0, 4.0),
        "quadriceps_fat_pad": (6.0, 5.0, 3.0),
    }
    monkeypatch.setattr(
        runner.anatomy_map, "target_span_mm", lambda name: spans.get(name)
    )
    profiles = {
        "hoffa_fat_pad": {
            "per_slice": {
                4: {"sample_rc": np.array([[25, 35], [26, 37]], dtype=np.int32)}
            }
        },
        "quadriceps_fat_pad": {
            "per_slice": {4: {"sample_rc": np.array([[42, 45]], dtype=np.int32)}}
        },
    }
    result = runner.native_fat_profile_window(profiles, 4, frame, shape)
    first = runner.source_window(
        profiles["hoffa_fat_pad"]["per_slice"][4]["sample_rc"],
        tuple(2 * v for v in spans["hoffa_fat_pad"]),
        frame,
        shape,
    )["window_rc_exclusive"]
    second = runner.source_window(
        profiles["quadriceps_fat_pad"]["per_slice"][4]["sample_rc"],
        tuple(2 * v for v in spans["quadriceps_fat_pad"]),
        frame,
        shape,
    )["window_rc_exclusive"]
    expected = (
        min(first[0], second[0]),
        max(first[1], second[1]),
        min(first[2], second[2]),
        max(first[3], second[3]),
    )
    assert result["window_rc"] == expected
    assert result["source_windows"]["hoffa_fat_pad"]["window"][
        "target_bbox_rc_exclusive"
    ] == [25, 27, 35, 38]
    assert result["status"] == "profile_window"
    assert result["full_frame"] is False


def test_profile_window_reports_clipping_and_full_frame_union(monkeypatch):
    frame = oblique_frame()
    monkeypatch.setattr(
        runner.anatomy_map, "target_span_mm", lambda _name: (100.0, 100.0, 100.0)
    )
    profiles = {
        "hoffa_fat_pad": {
            "per_slice": {1: {"sample_rc": np.array([[0, 0]], dtype=np.int32)}}
        }
    }
    result = runner.native_fat_profile_window(profiles, 1, frame, (20, 30))
    assert result["window_rc"] == (0, 20, 0, 30)
    assert result["status"] == "profile_window_full_frame"
    assert result["full_frame"] is True
    assert (
        result["source_windows"]["hoffa_fat_pad"]["status"] == "window_clipped_to_image"
    )


def test_native_context_runs_lens_on_union_crop_and_embeds_exterior_unknown(
    monkeypatch,
):
    frame = oblique_frame()
    raw = np.arange(64 * 80, dtype=np.uint16).reshape(1, 64, 80)
    series = SimpleNamespace(row=SimpleNamespace(series_uid="synthetic"), volume=raw)
    own = SimpleNamespace(
        series=series,
        record={
            "series_uid": "synthetic",
            "background_split": 100.0,
            "slice_index": -1,
        },
        arrays={},
    )
    profiles = {
        "hoffa_fat_pad": {
            "per_slice": {0: {"sample_rc": np.array([[30, 40]], dtype=np.int32)}}
        },
        "quadriceps_fat_pad": {
            "per_slice": {0: {"sample_rc": np.array([[32, 43]], dtype=np.int32)}}
        },
    }
    monkeypatch.setattr(runner, "plane_frame", lambda _series, _z: frame)
    monkeypatch.setattr(
        runner.anatomy_map, "target_span_mm", lambda _name: (8.0, 5.0, 3.0)
    )
    monkeypatch.setattr(
        runner, "finite_of", lambda _series: np.ones(raw.shape, dtype=bool)
    )
    monkeypatch.setattr(
        runner, "margin_of", lambda _uid, _z, plane: np.zeros(plane.shape, dtype=bool)
    )
    seen = {}

    def fake_interiors(crop, _spacing, _split, _prominence, *, available):
        seen["crop_shape"] = crop.shape
        seen["crop_values"] = crop.copy()
        markers = np.zeros(crop.shape, dtype=np.int32)
        markers[0, 0] = 1
        return SimpleNamespace(
            available=available,
            markers=markers,
            labels=np.zeros(crop.shape, dtype=np.int32),
        )

    def fake_gradient(signal, available, _spacing, groups):
        seen["gradient_shape"] = signal.shape
        seen["gradient_group_shapes"] = {
            name: mask.shape for name, mask in groups.items()
        }
        return SimpleNamespace(
            gradient_magnitude=np.ones(signal.shape, dtype=np.float64),
            gradient_u16=np.ones(signal.shape, dtype=np.uint16),
            gradient_valid=available.copy(),
            marker_ids=np.zeros(signal.shape, dtype=np.int32),
            conflicts=np.zeros(signal.shape, dtype=bool),
            labels=np.zeros(signal.shape, dtype=np.int32),
            unknown=~available,
            marker_codes={},
            marker_counts={name: int(mask.sum()) for name, mask in groups.items()},
            gradient_facts={},
        )

    monkeypatch.setattr(runner, "once", lambda _name, _key, read: read())
    monkeypatch.setattr(runner, "reads", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runner, "handed", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runner, "handed_on", lambda value: value)
    monkeypatch.setattr(runner, "field_names", lambda _value: ())
    monkeypatch.setattr(
        runner, "ledger", SimpleNamespace(record=lambda *_args, **_kwargs: None)
    )
    monkeypatch.setattr(
        runner, "margin", lambda plane: np.zeros(plane.shape, dtype=bool)
    )
    monkeypatch.setattr(runner, "interior_regions", fake_interiors)
    monkeypatch.setattr(
        runner,
        "read_field",
        lambda plane, _reading, _basis, _margin: SimpleNamespace(
            leg=np.ones(plane.shape, dtype=bool)
        ),
    )
    monkeypatch.setattr(
        runner,
        "native_fat_coarse_femur_context",
        lambda *_args: {
            "status": "measured",
            "native_core": np.zeros(raw[0].shape, dtype=bool),
        },
    )
    monkeypatch.setattr(runner, "native_gradient_territories", fake_gradient)
    result = runner.native_fat_plane_context(own, 0, profiles, None)
    expected = runner.native_fat_profile_window(profiles, 0, frame, raw[0].shape)[
        "window_rc"
    ]
    assert result["status"] == "measured"
    assert seen["crop_shape"] == (expected[1] - expected[0], expected[3] - expected[2])
    assert np.array_equal(result["scope_raw"], seen["crop_values"])
    assert result["lens_labels"].shape == raw[0].shape
    assert not result["lens_available"][: expected[0]].any()
    assert not result["available"][: expected[0]].any()
    assert result["scope"]["status"] == "profile_window"
    assert result["targets"]["hoffa_fat_pad"][30, 40]
    assert result["targets"]["quadriceps_fat_pad"][32, 43]
    assert seen["gradient_shape"] == result["scope_raw"].shape
    assert set(seen["gradient_group_shapes"]) >= {
        "hoffa_fat_pad",
        "quadriceps_fat_pad",
        "native_lens_peak_1",
        "frame_margin",
    }
    assert all(
        shape == result["scope_raw"].shape
        for shape in seen["gradient_group_shapes"].values()
    )
    peak = result["gradient_marker_groups"]["native_lens_peak_1"]
    assert peak.shape == raw[0].shape
    assert peak[expected[0], expected[2]]
    assert result["gradient"].unknown[: expected[0]].all()


def test_missing_profile_domain_uses_named_full_frame_fallback(monkeypatch):
    frame = oblique_frame()
    raw = np.arange(32 * 40, dtype=np.uint16).reshape(1, 32, 40)
    series = SimpleNamespace(row=SimpleNamespace(series_uid="fallback"), volume=raw)
    own = SimpleNamespace(
        series=series,
        record={"series_uid": "fallback", "background_split": 100.0, "slice_index": -1},
        arrays={},
    )
    monkeypatch.setattr(runner, "plane_frame", lambda _series, _z: frame)
    monkeypatch.setattr(
        runner, "finite_of", lambda _series: np.ones(raw.shape, dtype=bool)
    )
    monkeypatch.setattr(
        runner, "margin_of", lambda _uid, _z, plane: np.zeros(plane.shape, dtype=bool)
    )
    reading = SimpleNamespace(
        available=np.ones(raw[0].shape, dtype=bool),
        markers=np.zeros(raw[0].shape, dtype=np.int32),
        labels=np.zeros(raw[0].shape, dtype=np.int32),
    )
    field = SimpleNamespace(leg=np.ones(raw[0].shape, dtype=bool))
    monkeypatch.setattr(
        runner, "lens_of", lambda *_args, **_kwargs: (raw[0], reading, {})
    )
    monkeypatch.setattr(runner, "field_of", lambda *_args, **_kwargs: field)
    result = runner.native_fat_plane_context(own, 0, {}, None)
    assert result["status"] == "measured"
    assert result["scope"]["status"] == "profile_window_unavailable_full_frame"
    assert result["scope"]["full_frame"] is True
    assert result["scope_window_rc"] == (0, 32, 0, 40)
    assert result["available"].all()


def test_candidate_persistence_keeps_scope_offsets_raw_and_availability(monkeypatch):
    raw = np.arange(5 * 6, dtype=np.uint16).reshape(1, 5, 6)
    series = SimpleNamespace(
        row=SimpleNamespace(fluid_sensitive=1, fat_suppression=1, series_uid="persist"),
        volume=raw,
    )
    own = SimpleNamespace(
        series=series,
        record={
            "series_uid": "persist",
            "view": ("axial",),
            "recess": {},
            "a4_native_fat_profiles": {"hoffa_fat_pad": {"candidate_order": {}}},
        },
        arrays={},
    )
    profile = {
        "counts": np.array([1.0]),
        "map_counts": np.array([0.0]),
        "complete": np.array([True]),
        "guided": [],
        "source_peaks": [0],
        "guide": None,
    }
    monkeypatch.setattr(
        runner, "native_fat_source_profiles", lambda *_args: {"hoffa_fat_pad": profile}
    )
    window = (1, 3, 2, 5)
    scope_raw = raw[0, 1:3, 2:5].copy()
    scope_available = np.array([[True, False, True], [True, True, False]])
    full_available = np.zeros((5, 6), dtype=bool)
    full_available[1:3, 2:5] = scope_available
    targets = {
        name: np.zeros((5, 6), dtype=bool)
        for name in (
            "hoffa_fat_pad",
            "quadriceps_fat_pad",
            "prefemoral_fat_pad",
            "suprapatellar_fat",
        )
    }
    targets["hoffa_fat_pad"][1, 2] = True
    scope = {
        "status": "profile_window_partial_sources",
        "window_rc": window,
        "full_frame": False,
        "source_windows": {"hoffa_fat_pad": {"status": "present"}},
    }
    context = {
        "status": "measured",
        "z": 0,
        "raw": raw[0],
        "frame": oblique_frame(),
        "available": full_available,
        "lens_available": full_available,
        "margin": np.zeros((5, 6), dtype=bool),
        "lens_markers": np.zeros((5, 6), dtype=np.int32),
        "lens_labels": np.zeros((5, 6), dtype=np.int32),
        "targets": targets,
        "gradient": None,
        "coarse_femur": {"status": "not_needed_without_qp_gradient"},
        "scope": scope,
        "scope_raw": scope_raw,
        "scope_available": scope_available,
        "scope_window_rc": window,
    }
    monkeypatch.setattr(runner, "native_fat_plane_context", lambda *_args: context)
    candidate = np.zeros((5, 6), dtype=bool)
    candidate[1, 2] = True
    monkeypatch.setattr(
        runner,
        "native_fat_pad_candidate",
        lambda *_args: {
            "status": "selected_native_lens_territory",
            "candidate": candidate,
            "target": targets["hoffa_fat_pad"],
        },
    )
    monkeypatch.setattr(runner, "reads", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runner, "handed", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        runner, "ledger", SimpleNamespace(record=lambda *_args, **_kwargs: None)
    )
    result = runner.native_fat_pad_candidates(own, {}, None, None)
    prefix = "a4_axial_native_fat_context_scope"
    assert result["hoffa_fat_pad"][0]["slice"] == 0
    assert np.array_equal(
        own.arrays[f"{prefix}_windows_rc"], np.array([window], dtype=np.int32)
    )
    assert np.array_equal(own.arrays[f"{prefix}_raw_values"], scope_raw.ravel())
    assert np.array_equal(
        own.arrays[f"{prefix}_available_values"], scope_available.ravel()
    )
    assert np.array_equal(
        own.arrays[f"{prefix}_offsets"], np.array([0, scope_raw.size])
    )
    assert (
        own.record["a4_native_fat_candidate_context"]["scope_by_slice"][0]["status"]
        == scope["status"]
    )
