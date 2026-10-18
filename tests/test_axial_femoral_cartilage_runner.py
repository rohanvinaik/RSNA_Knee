from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location(
    "rsna_run_interiors_for_cartilage_tests", ROOT / "scripts" / "run_interiors.py"
)
assert SPEC is not None and SPEC.loader is not None
run = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = run
SPEC.loader.exec_module(run)


def _profiles(depth: int, *, guided: list[int], peaks: list[int]) -> dict:
    per_slice = {
        z: {
            "unique_rc": np.asarray([[2, 2]], dtype=np.int32),
            "sample_rc": np.asarray([[2, 2]], dtype=np.int32),
            "in_map": np.asarray([True]),
        }
        for z in range(depth)
    }
    groups = {
        name: {
            "per_slice": per_slice,
            "complete": np.ones(depth, dtype=bool),
        }
        for name in ("sagittal", "coronal")
    }
    return {
        "groups": groups,
        "guided": guided,
        "source_peaks": peaks,
        "counts": np.ones(depth, dtype=float),
        "map_counts": np.ones(depth, dtype=float),
        "unique_counts": np.ones(depth, dtype=float),
    }


def _own(*, sequence: tuple[int, int] = (1, 1), volume=None, thickness=()):
    return SimpleNamespace(
        record={
            "series_uid": "series",
            "view": ["Axial", "1", "1"],
            "observations": [],
        },
        series=SimpleNamespace(
            row=SimpleNamespace(
                fluid_sensitive=sequence[0], fat_suppression=sequence[1]
            ),
            volume=volume,
            slice_thickness_mm=thickness,
        ),
        arrays={},
    )


def _sources() -> dict:
    return {
        name: {"status": "selected", "points": np.ones((1, 3)), "point_count": 1}
        for name in ("sagittal", "coronal")
    }


def _silence_telemetry(monkeypatch) -> None:
    monkeypatch.setattr(run, "reads", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(run, "handed", lambda *_args, **_kwargs: None)


def test_non_fs_refusal_precedes_any_volume_access(monkeypatch) -> None:
    _silence_telemetry(monkeypatch)

    class NoVolumeSeries:
        row = SimpleNamespace(fluid_sensitive=0, fat_suppression=0)

        @property
        def volume(self):
            raise AssertionError("unsupported sequences must be refused first")

    own = _own(sequence=(0, 0))
    own.series = NoVolumeSeries()
    rows = run.name_femoral_cartilage([own], _sources(), "study", None, None)

    assert rows[0][0] == []
    assert len(rows[0][1]) == 1
    assert rows[0][1][0].code == "unsupported_sequence"


def test_sources_skip_patient_conversion_without_axial_fs_fluid_target(
    monkeypatch,
) -> None:
    _silence_telemetry(monkeypatch)
    sagittal = SimpleNamespace(
        record={
            "series_uid": "sagittal",
            "view": ["Sagittal", "1", "1"],
            "slice_index": 2,
            "assignments": {"codes": {"femoral_cartilage": "identified"}},
        },
        arrays={
            "a3_joint_plane_reading": np.asarray([[[0, 4], [0, 0]]], dtype=np.uint8),
            "a3_joint_plane_slices": np.asarray([2], dtype=np.int32),
        },
        series=SimpleNamespace(
            row=SimpleNamespace(fat_suppression=0, fluid_sensitive=0)
        ),
    )
    observation = run.Observation(
        "femoral_cartilage",
        "native",
        "resolved",
        "sagittal",
        ("Sagittal", "1", "1"),
        (2,),
        "identified",
        1,
        0.0,
        "a3_joint_plane_reading",
        "test source",
        "artifact",
        0,
        4,
    )
    axial = _own(sequence=(0, 0))
    monkeypatch.setattr(
        run,
        "plane_frame",
        lambda *_args: (_ for _ in ()).throw(
            AssertionError("source conversion has no axial target consumer")
        ),
    )

    sources = run.native_femoral_cartilage_sources(
        [sagittal, axial], [([observation], []), ([], [])], "study"
    )

    assert sources["sagittal"]["status"] == "no_axial_fs_fluid_sensitive_target"
    assert sources["coronal"]["status"] == "no_axial_fs_fluid_sensitive_target"
    assert sources["sagittal"]["point_count"] == 0
    assert sources["coronal"]["point_count"] == 0


def test_coronal_native_cartilage_group_code_supplies_labelled_source(
    monkeypatch,
) -> None:
    _silence_telemetry(monkeypatch)
    coronal = SimpleNamespace(
        record={
            "series_uid": "coronal-native",
            "view": ["Coronal", "1", "1"],
            "slice_index": 15,
            "assignments": {"codes": {"cartilage": "identified"}},
        },
        arrays=np.zeros((0,)),
        series=SimpleNamespace(
            row=SimpleNamespace(fat_suppression=1, fluid_sensitive=1)
        ),
    )
    coronal.arrays = {"a1_objects": np.asarray([[11, 0, 0], [0, 11, 0]])}
    laid = SimpleNamespace(
        record={
            "series_uid": "coronal-laid",
            "view": ["Coronal", "1", "1"],
            "slice_index": 15,
            "assignments": {"codes": {"cartilage": "laid_from_its_partner"}},
        },
        arrays={"a1_objects": np.full((2, 3), 11, dtype=np.uint8)},
        series=SimpleNamespace(
            row=SimpleNamespace(fat_suppression=1, fluid_sensitive=1)
        ),
    )
    axial = _own(sequence=(1, 1))
    axial.record["series_uid"] = "axial-target"
    monkeypatch.setattr(
        run, "artifact_of", lambda _study, record: record["series_uid"] + ".npz"
    )
    monkeypatch.setattr(
        run,
        "plane_frame",
        lambda *_args: SimpleNamespace(
            to_patient=lambda rc: np.column_stack(
                (np.asarray(rc, dtype=float), np.zeros(len(rc)))
            )
        ),
    )

    sources = run.native_femoral_cartilage_sources(
        [coronal, laid, axial], [([], []), ([], []), ([], [])], "study"
    )

    assert sources["coronal"]["status"] == "selected"
    assert sources["coronal"]["point_count"] == 2
    assert np.array_equal(
        sources["coronal"]["points"],
        np.asarray([[0.0, 0.0, 0.0], [1.0, 1.0, 0.0]]),
    )
    metadata = sources["coronal"]["entries"]
    assert len(metadata) == 1
    assert metadata[0] == {
        "series_uid": "coronal-native",
        "view": ["Coronal", "1", "1"],
        "slice": 15,
        "support": "a1_objects",
        "row": None,
        "label": run.OBJECT_CODES["femoral_cartilage"],
        "count": 2,
        "artifact": "coronal-native.npz",
        "provenance": "native",
        "code": "identified",
    }
    assert "a4_femoral_cartilage_sources" not in laid.record


def test_missing_volume_is_preserved_as_named_unresolved(monkeypatch) -> None:
    _silence_telemetry(monkeypatch)
    own = _own(volume=None)
    monkeypatch.setattr(
        run,
        "native_femoral_cartilage_profiles",
        lambda *_args: _profiles(1, guided=[], peaks=[]),
    )

    rows = run.name_femoral_cartilage([own], _sources(), "study", None, None)

    assert rows[0][0] == []
    assert len(rows[0][1]) == 1
    assert rows[0][1][0].code == "native_volume_unavailable"


def test_invalid_slice_thickness_is_not_collapsed_to_empty(monkeypatch) -> None:
    _silence_telemetry(monkeypatch)
    own = _own(volume=np.ones((1, 8, 8)), thickness=(0.0,))
    monkeypatch.setattr(
        run,
        "native_femoral_cartilage_profiles",
        lambda *_args: _profiles(1, guided=[0], peaks=[0]),
    )
    monkeypatch.setattr(run, "plane_frame", lambda *_args: SimpleNamespace())

    rows = run.name_femoral_cartilage([own], _sources(), "study", None, None)

    assert rows[0][0] == []
    assert len(rows[0][1]) == 1
    assert rows[0][1][0].code == "native_slice_0:slice_thickness_unavailable"


def test_no_candidate_slices_is_a_named_unresolved(monkeypatch) -> None:
    _silence_telemetry(monkeypatch)
    own = _own(volume=np.ones((1, 8, 8)), thickness=(1.0,))
    monkeypatch.setattr(
        run,
        "native_femoral_cartilage_profiles",
        lambda *_args: _profiles(1, guided=[], peaks=[]),
    )

    rows = run.name_femoral_cartilage([own], _sources(), "study", None, None)

    assert rows[0][0] == []
    assert len(rows[0][1]) == 1
    assert rows[0][1][0].code == "native_no_candidate_slices"


def test_missing_native_marrow_is_named_unknown_not_an_exception(monkeypatch) -> None:
    _silence_telemetry(monkeypatch)
    own = _own(volume=np.ones((1, 8, 8)), thickness=(1.0,))
    monkeypatch.setattr(
        run,
        "native_femoral_cartilage_profiles",
        lambda *_args: _profiles(1, guided=[0], peaks=[0]),
    )
    monkeypatch.setattr(
        run,
        "plane_frame",
        lambda *_args: SimpleNamespace(spacing_rc=(1.0, 1.0)),
    )
    monkeypatch.setattr(
        run, "finite_of", lambda _series: np.ones((1, 8, 8), dtype=bool)
    )
    monkeypatch.setattr(run, "margin_of", lambda *_args: np.zeros((8, 8), dtype=bool))
    monkeypatch.setattr(
        run,
        "native_femur_coarse_context",
        lambda *_args: {
            "status": "section",
            "block_reading": SimpleNamespace(
                median=np.ones((2, 2)),
                block_px=(2, 2),
                block_mm=(2.0, 2.0),
                window_rc=(0, 8, 0, 8),
            ),
            "native_core": np.eye(8, dtype=bool),
            "section": SimpleNamespace(
                status="section",
                area_mm2=4.0,
                level=1.0,
                body=np.ones((2, 2), dtype=bool),
            ),
            "depth": np.ones((2, 2)),
        },
    )
    monkeypatch.setattr(
        run,
        "enclosed_depth_of",
        lambda *_args: np.ones((8, 8), dtype=float),
    )
    monkeypatch.setattr(
        run,
        "measures_of",
        lambda *_args: SimpleNamespace(light=lambda _mask: None, distance=None),
    )
    rows = run.name_femoral_cartilage([own], _sources(), "study", None, None)

    assert rows[0][0] == []
    assert len(rows[0][1]) == 1
    assert rows[0][1][0].code == "native_slice_0:native_marrow_level_unavailable"


def test_unavailable_outer_border_is_open_and_its_stored_values_are_ignored(
    monkeypatch,
) -> None:
    _silence_telemetry(monkeypatch)
    raw = np.full((12, 12), 5.0)
    raw[4:8, 4] = 20.0
    raw[4:8, 7] = 20.0
    raw[4, 4:8] = 20.0
    raw[7, 4:8] = 20.0
    raw[5:7, 5:7] = 1.0
    margin = np.zeros(raw.shape, dtype=bool)
    margin[[0, -1], :] = True
    margin[:, [0, -1]] = True
    raw[margin] = 900.0
    own = _own(volume=raw[np.newaxis, ...], thickness=(1.0,))
    monkeypatch.setattr(
        run,
        "native_femoral_cartilage_profiles",
        lambda *_args: _profiles(1, guided=[0], peaks=[0]),
    )
    monkeypatch.setattr(
        run,
        "plane_frame",
        lambda *_args: SimpleNamespace(spacing_rc=(1.0, 1.0)),
    )
    monkeypatch.setattr(
        run, "finite_of", lambda _series: np.ones((1, 12, 12), dtype=bool)
    )
    monkeypatch.setattr(run, "margin_of", lambda *_args: margin)
    monkeypatch.setattr(
        run,
        "native_femur_coarse_context",
        lambda *_args: {
            "status": "section",
            "block_reading": SimpleNamespace(
                median=np.ones((2, 2)),
                block_px=(2, 2),
                block_mm=(2.0, 2.0),
                window_rc=(0, 12, 0, 12),
            ),
            "native_core": raw == 20.0,
            "section": SimpleNamespace(
                status="section",
                area_mm2=4.0,
                level=1.0,
                body=np.ones((2, 2), dtype=bool),
            ),
            "depth": np.ones((2, 2)),
        },
    )
    monkeypatch.setattr(
        run,
        "measures_of",
        lambda *_args: SimpleNamespace(light=lambda _mask: None, distance=None),
    )
    depth_inputs = []
    depth_outputs = []
    enclosed_darkness = run.enclosed_darkness

    def read_depth(plane, *_args):
        measured = enclosed_darkness(plane)
        depth_inputs.append(np.asarray(plane).copy())
        depth_outputs.append(measured)
        return measured

    monkeypatch.setattr(run, "enclosed_depth_of", read_depth)

    rows = run.name_femoral_cartilage([own], _sources(), "study", None, None)

    # The band's calibration follows the native component the core selects; this core (the
    # bright ring) touches no positive enclosed component, so the selection is what refuses.
    assert rows[0][1][0].code == "native_slice_0:no_positive_enclosure_touched_by_core"
    prefix = "a4_axial_femoral_cartilage_context_depth_input"
    values = own.arrays[f"{prefix}_values"]
    offsets = own.arrays[f"{prefix}_offsets"]
    shape = tuple(own.arrays[f"{prefix}_shapes"][0])
    depth_input = values[offsets[0] : offsets[1]].reshape(shape)
    assert np.all(depth_input[margin] == 1.0)
    assert (
        own.record["a4_axial_femoral_cartilage_candidates"][0]["depth_boundary_policy"]
        == "minimum_of_available_at_unavailable_pixels"
    )
    measured_depth = own.arrays[
        "a4_axial_femoral_cartilage_context_enclosed_depth_values"
    ]
    assert np.isfinite(measured_depth).all()
    changed_raw = raw.copy()
    changed_raw[margin] = -1e9
    changed = _own(volume=changed_raw[np.newaxis, ...], thickness=(1.0,))
    run.name_femoral_cartilage([changed], _sources(), "study", None, None)
    assert len(depth_inputs) == len(depth_outputs) == 2
    assert np.array_equal(depth_inputs[0], depth_inputs[1])
    assert np.array_equal(depth_outputs[0], depth_outputs[1])
    assert depth_outputs[0][5, 5] > 0.0
