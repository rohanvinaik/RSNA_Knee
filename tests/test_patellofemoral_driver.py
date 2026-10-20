from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

REBASE = Path(__file__).parents[1]
sys.path.insert(0, str(REBASE / "src"))
RUNNER_PATH = REBASE / "scripts" / "run_interiors.py"
SPEC = importlib.util.spec_from_file_location("p8_current_rebase_runner", RUNNER_PATH)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def make_middle(*, fat_suppression: int = 1, fluid_sensitive: int = 1):
    shape = (18, 20)
    raw = np.full(shape, 10.0, dtype=np.float32)
    objects = np.zeros(shape, dtype=np.int8)
    objects[5:9, 5:9] = runner.OBJECT_CODES["patella"]
    objects[10:14, 9:14] = runner.OBJECT_CODES["femur"]
    available = np.zeros(shape, dtype=bool)
    available[4:15, 3:17] = True
    frame = runner.PlaneFrame(
        np.zeros(3, dtype=np.float64),
        np.array([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]),
        (1.0, 1.0),
    )
    uid = "series-pf-test"
    row = SimpleNamespace(
        series_uid=uid,
        fat_suppression=fat_suppression,
        fluid_sensitive=fluid_sensitive,
    )
    series = SimpleNamespace(row=row, volume=np.stack([raw] * 6))
    record = {
        "series_uid": uid,
        "view": ("Sagittal", "1", "1"),
        "slice_index": 3,
        "background_split": 4.0,
        "assignments": {"codes": {"patella": "identified", "femur": "identified"}},
    }
    own = SimpleNamespace(
        series=series,
        record=record,
        arrays={
            "a1_objects": objects,
            "acquired_plane": raw,
            "b1_available": available,
        },
        frame=frame,
    )
    return own, raw, objects


def test_middle_native_surface_readings_retain_operator_arrays_and_crop_address():
    own, _, _ = make_middle()
    runner.native_patellofemoral_surface_readings([own], "study-pf-test")

    assert own.arrays["a4_patellofemoral_slices"].tolist() == [3]
    assert own.arrays["a4_patellofemoral_window_rc"].tolist() == [[0, 18, 0, 20]]
    assert own.arrays["a4_patellofemoral_source_kind"].tolist() == ["a1_middle"]
    assert own.arrays["a4_patellofemoral_source_support"].tolist() == ["a1_objects"]
    assert own.arrays["a4_patellofemoral_raw_shapes"].tolist() == [[18, 20]]
    measured_available = own.arrays["a4_patellofemoral_available_flat"].reshape(18, 20)
    assert np.array_equal(measured_available, own.arrays["b1_available"])
    assert (
        own.record["patellofemoral_surface_readings"][0]["source_address"]["support"]
        == "a1_objects"
    )

    for name in (
        "bridge",
        "patella_filled",
        "femur_filled",
        "brightness_band",
        "to_patella_mm",
        "to_femur_mm",
        "patella_reach",
        "femur_reach",
        "patella_support",
        "trochlear_support",
        "ties",
        "available",
        "finite",
    ):
        prefix = f"a4_patellofemoral_{name}"
        assert f"{prefix}_flat" in own.arrays
        assert own.arrays[f"{prefix}_shapes"].tolist() == [[18, 20]]
        assert own.arrays[f"{prefix}_offsets"].tolist() == [0, 360]

    observations = own.record["observations"]
    assert [
        (row["object"], row["provenance"], row["kind"]) for row in observations
    ] == [
        ("patellar_cartilage", "native", "reading"),
        ("trochlear_cartilage", "native", "reading"),
    ]
    assert all(
        row["artifact"] == "study-pf-test/series-pf-test.npz.xz" for row in observations
    )
    assert all(row["row"] == 0 for row in observations)
    support = own.arrays["a4_patellofemoral_patellar_cartilage_support"]
    assert support.shape == (1, 18, 20)
    assert np.array_equal(
        support[0], own.arrays["a4_patellofemoral_patella_support_flat"].reshape(18, 20)
    )
    assert observations[0]["support"] == "a4_patellofemoral_patellar_cartilage_support"
    saved_available = own.arrays["a4_patellofemoral_measurement_available"]
    assert saved_available.shape == (1, 18, 20)
    assert np.array_equal(saved_available[0], own.arrays["b1_available"])


def test_missing_fs_fluid_context_is_named_unresolved_not_absence():
    own, _, _ = make_middle(fat_suppression=0, fluid_sensitive=1)
    runner.native_patellofemoral_surface_readings([own], "study-pf-test")

    assert own.record["patellofemoral_surface_readings"] == []
    assert "a4_patellofemoral_slices" not in own.arrays
    unresolved = own.record["observations_unresolved"]
    assert {(row["object"], row["code"]) for row in unresolved} == {
        ("patellar_cartilage", "requires_fat_suppressed_fluid_sensitive_acquisition"),
        ("trochlear_cartilage", "requires_fat_suppressed_fluid_sensitive_acquisition"),
    }


def test_middle_scope_exterior_stays_unavailable_in_saved_operator_array():
    own, _, _ = make_middle()
    runner.native_patellofemoral_surface_readings([own], "study-pf-test")
    available = own.arrays["a4_patellofemoral_available_flat"].reshape(18, 20)
    assert not available[0, 0]
    assert available[9, 9]
    assert own.arrays["a4_patellofemoral_available_offsets"].tolist() == [0, 360]


def test_observation_rows_reconstruct_native_support_across_different_crop_shapes(
    monkeypatch,
):
    shape = (7, 8)
    window = (1, 6, 2, 7)
    crop_shape = (5, 5)
    raw = np.full(shape, 10.0, dtype=np.float32)
    objects = np.zeros(shape, dtype=np.int8)
    objects[2:4, 3:5] = runner.OBJECT_CODES["patella"]
    objects[4:6, 4:7] = runner.OBJECT_CODES["femur"]
    local_objects = objects[window[0] : window[1], window[2] : window[3]].copy()
    frame = runner.PlaneFrame(
        np.zeros(3, dtype=np.float64),
        np.array([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]),
        (1.0, 1.0),
    )
    native_pointed_frame = runner.PlaneFrame(
        np.array([100.0, 200.0, 300.0], dtype=np.float64),
        frame.basis_lps.copy(),
        frame.spacing_rc,
    )
    crop_frame = runner.local_frame(native_pointed_frame, window)
    local_raw = raw[window[0] : window[1], window[2] : window[3]].copy()
    local_available = np.ones(crop_shape, dtype=bool)
    uid = "series-pf-pointed"
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid=uid, fat_suppression=1, fluid_sensitive=1),
        volume=np.stack([raw] * 6),
    )
    identified = runner.PATELLA_OUTCOMES.index("identified")
    record = {
        "series_uid": uid,
        "view": ("Sagittal", "1", "1"),
        "slice_index": 3,
        "background_split": 4.0,
        "assignments": {"codes": {"patella": "identified", "femur": "identified"}},
        "observations": [
            {
                "object": "patella",
                "provenance": "native",
                "kind": "resolved",
                "code": "identified",
                "slices": [5],
                "support": "a3_patella_plane_objects",
                "row": 0,
            }
        ],
    }
    own = SimpleNamespace(
        series=series,
        record=record,
        frame=frame,
        arrays={
            "a1_objects": objects,
            "acquired_plane": raw,
            "b1_available": np.ones(shape, dtype=bool),
            "a3_patella_plane_slices": np.asarray([5], dtype=np.int32),
            "a3_patella_plane_outcome": np.asarray([identified], dtype=np.int8),
            "a3_patella_plane_window_rc": np.asarray([window], dtype=np.int32),
            "a3_patella_plane_objects": objects[None, ...],
            "a3_patella_local_slices": np.asarray([5], dtype=np.int32),
            "a3_patella_local_window_rc": np.asarray([window], dtype=np.int32),
            "a3_patella_local_outcome": np.asarray([identified], dtype=np.int8),
            "a3_patella_local_outcome_names": np.asarray(runner.PATELLA_OUTCOMES),
            "a3_patella_local_femur": np.asarray(["identified"]),
            "a3_patella_local_crop_shapes": np.asarray([crop_shape], dtype=np.int32),
            "a3_patella_local_crop_offsets": np.asarray([0, 25], dtype=np.int64),
            "a3_patella_local_objects": local_objects.ravel(),
            "a3_patella_local_frame_origin_lps": crop_frame.origin_lps[None, ...],
            "a3_patella_local_frame_basis_lps": crop_frame.basis_lps[None, ...],
        },
    )
    measurements = runner.Measures((uid, 5, window), local_raw, crop_frame.basis_lps)
    context = SimpleNamespace(
        interior=SimpleNamespace(
            raw=local_raw,
            reading=SimpleNamespace(available=local_available),
        ),
        frame=crop_frame,
        measures=measurements,
    )
    monkeypatch.setattr(
        runner,
        "plane_frame",
        lambda _series, z: frame if z == 3 else native_pointed_frame,
    )
    monkeypatch.setattr(runner, "patella_scope_of", lambda *args: context)

    runner.native_patellofemoral_surface_readings([own], "study-pf-pointed")

    assert own.arrays["a4_patellofemoral_slices"].tolist() == [3, 5]
    assert own.arrays["a4_patellofemoral_window_rc"].tolist() == [
        [0, *shape[:1], 0, shape[1]],
        list(window),
    ]
    assert own.arrays["a4_patellofemoral_crop_shapes"].tolist() == [
        list(shape),
        list(crop_shape),
    ]
    assert own.arrays["a4_patellofemoral_source_kind"].tolist() == [
        "a1_middle",
        "a3_patella_local",
    ]
    assert own.arrays["a4_patellofemoral_source_row"].tolist() == [-1, 0]
    rows = own.record["patellofemoral_surface_readings"]
    assert [row["result_row"] for row in rows] == [0, 1]
    assert rows[1]["source_address"]["row"] == 0
    assert own.arrays["a4_patellofemoral_patella_support_shapes"].tolist() == [
        list(shape),
        list(crop_shape),
    ]
    assert own.arrays["a4_patellofemoral_patella_support_offsets"].tolist() == [
        0,
        int(np.prod(shape)),
        int(np.prod(shape)) + int(np.prod(crop_shape)),
    ]
    support_rows = own.arrays["a4_patellofemoral_patellar_cartilage_support"]
    assert support_rows.shape == (2, *shape)
    crop = support_rows[1, window[0] : window[1], window[2] : window[3]]
    flat = own.arrays["a4_patellofemoral_patella_support_flat"]
    start = int(own.arrays["a4_patellofemoral_patella_support_offsets"][1])
    stop = int(own.arrays["a4_patellofemoral_patella_support_offsets"][2])
    assert np.array_equal(crop, flat[start:stop].reshape(crop_shape))
    assert not support_rows[1, 0, 0]
    saved_available = own.arrays["a4_patellofemoral_measurement_available"]
    assert saved_available.shape == (2, *shape)
    assert np.all(saved_available[0])
    assert np.array_equal(
        saved_available[1, window[0] : window[1], window[2] : window[3]],
        local_available,
    )
    assert not saved_available[1, 0, 0]
    pointed_observation = next(
        row
        for row in own.record["observations"]
        if row["support"] == "a4_patellofemoral_patellar_cartilage_support"
        and row["slices"] == (5,)
    )
    assert pointed_observation["slices"] == (5,)
    assert pointed_observation["address_frame"]["origin_lps"] == [100.0, 200.0, 300.0]
    assert pointed_observation["address_frame"]["origin_lps"] != list(
        crop_frame.origin_lps
    )
    assert np.array_equal(
        own.arrays["a4_patellofemoral_raw_flat"][shape[0] * shape[1] :],
        local_raw.ravel(),
    )


def test_unmeasured_surface_count_is_unknown_but_measured_empty_is_zero():
    unmeasured, _, _ = make_middle()
    unmeasured.arrays["b1_available"][:] = False
    runner.native_patellofemoral_surface_readings([unmeasured], "study-pf-unmeasured")
    assert [row["count"] for row in unmeasured.record["observations"]] == [None, None]
    assert {row["code"] for row in unmeasured.record["observations"]} == {
        "unmeasured:no_available_finite_pixels"
    }

    empty, _, _ = make_middle()
    runner.native_patellofemoral_surface_readings([empty], "study-pf-empty")
    assert [row["count"] for row in empty.record["observations"]] == [0, 0]
    assert {row["code"] for row in empty.record["observations"]} == {
        "measured_empty:no_eligible_bridge_pixels"
    }


def test_eligible_but_missing_native_masks_remains_named_unresolved():
    own, _, _ = make_middle()
    own.record["assignments"]["codes"] = {}
    own.arrays.pop("a1_objects")
    own.arrays.pop("a3_patella_plane_slices", None)
    runner.native_patellofemoral_surface_readings([own], "study-pf-test")

    assert own.record["patellofemoral_surface_readings"] == []
    assert {row["object"] for row in own.record["observations_unresolved"]} == {
        "patellar_cartilage",
        "trochlear_cartilage",
    }
    assert {row["code"] for row in own.record["observations_unresolved"]} == {
        "no_selected_same_slice_native_patella_femur_context"
    }


def test_measure_study_calls_surface_reader_after_native_patella_producers(
    monkeypatch, tmp_path
):
    events = []
    uid = "series-caller-test"
    row = SimpleNamespace(series_uid=uid, fat_suppression=1, slices=[0])
    series = SimpleNamespace(row=row, slices=[0])
    own = SimpleNamespace(
        series=series,
        record={
            "series_uid": uid,
            "view": ("Sagittal", "1", "1"),
            "slice_index": 0,
            "assignments": {"codes": {}, "knee": "R"},
        },
        arrays={"a1_objects": np.zeros((2, 2), dtype=np.int8)},
        assignment=SimpleNamespace(in_plane=(True, True, True)),
        stack=object(),
    )
    leg = SimpleNamespace(patella_lps=np.empty((0, 3), dtype=np.float64))
    monkeypatch.setattr(
        runner, "read_study", lambda *_: SimpleNamespace(series=[series])
    )
    monkeypatch.setattr(runner, "measure", lambda *_: own)
    monkeypatch.setattr(runner, "partner_of", lambda *_: None)
    monkeypatch.setattr(runner, "field_names", lambda *_: ())

    def event(name, result=None):
        def call(*_args, **_kwargs):
            events.append(name)
            return result

        return call

    no_op_names = (
        "name_the_extensor_tendons",
        "name_the_rest_of_the_field",
        "name_joint_boundaries",
        "name_suprapatellar_pads",
        "name_iliotibial_band",
        "name_sartorius",
        "name_the_bones",
        "name_the_joint",
        "fibula_key_planes",
        "joint_existing",
        "keep_recess",
        "posterior_silences",
        "index_posterior",
        "native_fat_opposed_samples",
    )
    for name in no_op_names:
        monkeypatch.setattr(runner, name, lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runner, "leg_of", lambda *_: leg)
    monkeypatch.setattr(runner, "refine_leg", lambda *_: leg)
    monkeypatch.setattr(runner, "name_the_back_of_the_knee", lambda *_: {})
    monkeypatch.setattr(runner, "find_part", lambda *_: ([], {}))
    monkeypatch.setattr(runner, "gracilis_source", lambda *_: None)
    monkeypatch.setattr(runner, "anatomical_reference", lambda: object())
    monkeypatch.setattr(runner, "build_study_map", lambda *_: object())
    monkeypatch.setattr(runner, "name_the_patella", event("name_the_patella"))
    monkeypatch.setattr(runner, "patella_key_planes", event("patella_key_planes"))
    monkeypatch.setattr(runner, "refine_map", event("refine_map"))
    monkeypatch.setattr(
        runner, "native_patellofemoral_surface_readings", event("surface_reader")
    )
    monkeypatch.setattr(runner, "native_pcl_sources", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(runner, "native_meniscus_sources", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        runner, "name_native_ligament_sections", lambda *_args, **_kwargs: [([], [])]
    )
    monkeypatch.setattr(
        runner, "offer_native_family", lambda _m, _r, family, _s: (family, [], None)
    )
    monkeypatch.setattr(runner, "sagittal_cartilage_observations", lambda *_: [])
    monkeypatch.setattr(runner, "native_femoral_cartilage_sources", lambda *_: [])
    monkeypatch.setattr(runner, "name_the_recess", lambda *_: [([], [])])
    monkeypatch.setattr(runner, "native_fat_pad_sources", lambda *_: [])
    monkeypatch.setattr(runner, "native_fat_pad_candidates", lambda *_: {})
    monkeypatch.setattr(runner, "native_fat_pad_observations", lambda *_: ([], []))
    for name in (
        "name_coronal_anterior_recess",
        "name_sagittal_capsule",
        "name_axial_joint_compartment",
        "name_axial_extensor_sections",
        "name_coronal_extensor_sections",
        "name_femoral_cartilage",
        "name_native_menisci",
        "name_native_pcl_sections",
        "name_native_gastrocnemius_heads",
        "name_cross_view_retinacula",
        "native_tibial_cartilage_readings",
        "collect_bursa_native_readings",
    ):
        monkeypatch.setattr(runner, name, lambda *_args, **_kwargs: [([], [])])
    for name in (
        "axial_capsule_observations",
        "cavity_lining_observations",
        "axial_joint_fluid",
        "anterior_recess_from_axial_pockets",
    ):
        monkeypatch.setattr(runner, name, lambda *_args, **_kwargs: ([], []))
    monkeypatch.setattr(runner, "late_native_readings", lambda *_: [([], [])])
    monkeypatch.setattr(runner, "recess_existing", lambda *_: None)
    monkeypatch.setattr(runner, "find_fibula", lambda *_: "not-read-in-test")
    monkeypatch.setattr(runner, "finish_map", lambda *_: {"counts": {}})
    monkeypatch.setattr(runner, "named_parts", lambda *_: [])
    monkeypatch.setattr(runner, "describe_objects", lambda *_: {})
    monkeypatch.setattr(runner, "save", lambda *_args, **_kwargs: events.append("save"))

    result = runner.measure_study(
        object(), "study-caller-test", tmp_path / "run", tmp_path / "main", False
    )

    assert result["study_uid"] == "study-caller-test"
    assert events.index("name_the_patella") < events.index("patella_key_planes")
    assert events.index("patella_key_planes") < events.index("surface_reader")
    assert events.index("surface_reader") < events.index("save")
