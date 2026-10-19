"""Provenance for the recess fluid-profile calibration support."""

from types import SimpleNamespace
from typing import cast

import numpy as np

from scripts import run_interiors as run


def test_retinacula_profile_keeps_the_exact_projected_light_support(monkeypatch):
    uid = "retinacula-series"
    frame = run.PlaneFrame(
        np.zeros(3),
        np.asarray([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]),
        (1.0, 1.0),
    )
    projected_femur = np.asarray(
        [[True, True, False], [False, True, False], [False, False, False]], dtype=bool
    )
    available = np.asarray(
        [[True, False, True], [False, True, True], [False, False, False]], dtype=bool
    )
    measured_supports = []

    class Measures:
        @staticmethod
        def light(mask):
            measured_supports.append(mask)
            return float(np.count_nonzero(mask) * 10)

    volume = np.ones((3, 3, 3), dtype=float)
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid=uid, fat_suppression="1", fluid_sensitive="1"),
        volume=volume,
        geometry=SimpleNamespace(
            position=[np.asarray([0.0, 0.0, float(z)]) for z in range(3)]
        ),
        slice_thickness_mm=[1.0, 1.0, 1.0],
    )
    objects = np.zeros((3, 3), dtype=np.int8)
    own = SimpleNamespace(
        series=series,
        record={
            "series_uid": uid,
            "slice_index": 1,
            "background_split": 50.0,
            "assignments": {"knee": "R", "femur": 1, "tibia": 2, "codes": {}},
        },
        arrays={
            "a1_objects": objects,
            "acquired_plane": volume[1],
            "b1_available": available,
        },
        stack=SimpleNamespace(code="present"),
        assignment=SimpleNamespace(in_plane=(False, False, False)),
        frame=frame,
    )
    leg = run.Leg(
        np.asarray([[1.0, 1.0, 1.0]]),
        np.asarray([[0.0, 0.0, -5.0]]),
        None,
        None,
        np.asarray([[1.0, 2.0, 3.0]]),
        identity="refined-context-1",
    )
    status = np.full(3, run.JOINT_NOT_READ, dtype=np.int8)
    profile = run.JointProfile(
        names=(run.FLUID,),
        status={run.FLUID: status},
        area_mm2={run.FLUID: np.zeros(3, dtype=float)},
        seen_blocks=np.zeros((3, 1), dtype=np.int32),
        unseen_blocks=np.zeros((3, 1), dtype=np.int32),
        corridor_px=np.zeros(3, dtype=np.int32),
        corridor=np.zeros((3, 1, 1), dtype=bool),
        could={run.FLUID: np.zeros((3, 1, 1), dtype=bool)},
        window_rc=np.zeros((3, 4), dtype=np.int32),
        cell_mm=np.ones((3, 2), dtype=float),
        block_px=np.ones((3, 2), dtype=np.int32),
        fine=(),
        level={run.FLUID: (10.0, 20.0)},
    )
    monkeypatch.setattr(run, "slab_thicknesses", lambda _: ([1.0] * 3, None))
    monkeypatch.setattr(
        run, "leg_on", lambda *args: (projected_femur, np.zeros_like(projected_femur))
    )
    monkeypatch.setattr(run, "measures_of", lambda *args: Measures())
    monkeypatch.setattr(run, "levels", lambda *args: {run.FLUID: (10.0, 20.0)})
    monkeypatch.setattr(
        run,
        "recess_corridor",
        lambda *args: (
            lambda z, plane, shape: np.ones(shape, dtype=bool),
            {"frame": "test"},
        ),
    )
    monkeypatch.setattr(run, "retinacula_z", lambda *args: (1, [1.0] * 3, "R"))
    monkeypatch.setattr(run, "joint_profile", lambda *args, **kwargs: profile)

    with run.recording(), run.computing():
        # The namespace supplies this isolated reader's Measured fields; dependencies are stubbed above.
        result = run.read_recess(
            cast(run.Measured, own), None, leg, np.asarray([1.0, 2.0, 3.0]), {}
        )

    assert isinstance(result, run.RecessRead)
    expected = projected_femur & available
    assert len(measured_supports) == 1
    assert result.arrays["a3_recess_reference_light_support"] is measured_supports[0]
    assert np.array_equal(result.arrays["a3_recess_reference_light_support"], expected)
    assert not result.arrays["a3_recess_reference_light_support"].flags.writeable
    calibration = result.record["profile_calibration"]
    assert calibration == {
        "method": "acquired_light_over_projected_bone_locations",
        "source_series_uid": uid,
        "native_middle_slice": 1,
        "femur_support_address": "a3_recess_reference_light_support",
        "femur_support_codes": None,
        "bones_support_address": "a3_recess_reference_light_support",
        "bones_support_codes": None,
        "femur_light": 20.0,
        "bones_light": 20.0,
        "role": "fluid_profile_reference_prior_not_native_marrow_identity",
        "location_context_identity": "refined-context-1",
        "location_support_digest": run.digest(expected),
    }
