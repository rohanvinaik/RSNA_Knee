from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from scripts import run_interiors as RUNNER


def _fixture(monkeypatch):
    uid = "series-1"
    view = ("Sagittal", "1", "1")
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid=uid),
        volume=np.zeros((4, 8, 9), dtype=np.int16),
    )
    measured = SimpleNamespace(series=series, record={"series_uid": uid, "view": view})
    frame = RUNNER.PlaneFrame(
        origin_lps=np.asarray([10.0, 20.0, 30.0]),
        basis_lps=np.asarray([[0.8, -0.4], [0.6, 0.7], [0.0, 0.5]]),
        spacing_rc=(1.0, 1.0),
    )
    calls = []

    def get_frame(actual_series, z):
        calls.append((actual_series, z))
        return frame if z == 2 else "geometry_unreadable"

    monkeypatch.setattr(RUNNER, "plane_frame", get_frame)
    observation = {
        "series_uid": uid,
        "view": list(view),
        "slices": [2],
        "provenance": "native",
        "kind": "resolved",
        "support": "a2_femur",
        "artifact": "study/series-1.npz.xz",
        "row": None,
        "address_frame": None,
    }
    record = {"observations": [observation]}
    descriptors = {observation["artifact"]: {"a2_femur": ((8, 9), "b")}}
    return uid, measured, frame, calls, observation, record, descriptors


def test_attaches_oblique_frame_for_off_record_slice_without_mutating_support(
    monkeypatch,
):
    uid, measured, frame, calls, observation, record, descriptors = _fixture(
        monkeypatch
    )
    observation["slices"] = [2]  # distinct from the measured middle slice at index 0

    RUNNER.attach_full_native_mask_address_frames(
        [record], {uid: measured}, descriptors
    )

    assert observation["address_frame"] == {
        "origin_lps": [10.0, 20.0, 30.0],
        "basis_lps": frame.basis_lps.tolist(),
    }
    assert calls == [(measured.series, 2)]
    assert observation["support"] == "a2_femur"
    assert observation["slices"] == [2]


def test_cached_frame_is_computed_once_for_repeated_same_slice_observations(
    monkeypatch,
):
    uid, measured, _, calls, observation, record, descriptors = _fixture(monkeypatch)
    record["observations"].append({**observation, "support": "a2_tibia"})
    descriptors[observation["artifact"]]["a2_tibia"] = ((8, 9), "i")

    RUNNER.attach_full_native_mask_address_frames(
        [record], {uid: measured}, descriptors
    )

    assert len(calls) == 1
    assert all(row["address_frame"] is not None for row in record["observations"])


def test_accepts_bounded_row_of_full_native_mask_stack(monkeypatch):
    uid, measured, _, calls, observation, record, descriptors = _fixture(monkeypatch)
    observation["row"] = 1
    descriptors[observation["artifact"]]["a2_femur"] = ((3, 8, 9), "u")

    RUNNER.attach_full_native_mask_address_frames(
        [record], {uid: measured}, descriptors
    )

    assert observation["address_frame"] is not None
    assert calls[0][1] == 2


def test_accepts_laid_full_native_boolean_support(monkeypatch):
    uid, measured, _, _, observation, record, descriptors = _fixture(monkeypatch)
    observation["provenance"] = "laid"
    observation["support"] = "a2_laid_part"
    descriptors[observation["artifact"]] = {"a2_laid_part": ((8, 9), "b")}
    monkeypatch.setattr(
        RUNNER,
        "plane_frame",
        lambda _series, _z: RUNNER.PlaneFrame(
            np.zeros(3), np.asarray([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]), (1.0, 1.0)
        ),
    )

    RUNNER.attach_full_native_mask_address_frames(
        [record], {uid: measured}, descriptors
    )

    assert observation["address_frame"] is not None


def test_refuses_bad_address_families_shapes_rows_and_series(monkeypatch):
    uid, measured, _, calls, observation, _record, descriptors = _fixture(monkeypatch)
    original = dict(observation)
    cases = [
        ({"support": "a3_packed_femur", "row": 0}, ((72,), "b")),
        ({"support": "a3_posterior_trace_artery_points_lps"}, ((8, 3), "f")),
        ({"support": "a4_sample_context"}, ((8, 9), "b")),
        ({"support": "a2_float_measurement"}, ((8, 9), "f")),
        ({"support": "a2_crop_femur"}, ((4, 5), "b")),
        ({}, ((8, 10), "b")),
        ({"slices": [1, 2]}, ((8, 9), "b")),
        ({"row": True}, ((2, 8, 9), "b")),
        ({"row": 2}, ((2, 8, 9), "b")),
        ({"series_uid": "unknown"}, ((8, 9), "b")),
    ]
    for overrides, descriptor in cases:
        row = {**original, **overrides, "address_frame": None}
        one_record = {"observations": [row]}
        descriptors[original["artifact"]][row["support"]] = descriptor
        RUNNER.attach_full_native_mask_address_frames(
            [one_record], {uid: measured}, descriptors
        )
        assert row["address_frame"] is None, overrides
    assert calls == []


def test_leaves_invalid_geometry_and_existing_frame_untouched(monkeypatch):
    uid, measured, _, calls, observation, record, descriptors = _fixture(monkeypatch)
    observation["slices"] = [1]
    RUNNER.attach_full_native_mask_address_frames(
        [record], {uid: measured}, descriptors
    )
    assert observation["address_frame"] is None
    assert calls == [(measured.series, 1)]

    observation["address_frame"] = {
        "origin_lps": [1, 2, 3],
        "basis_lps": [[1, 0], [0, 1], [0, 0]],
    }
    RUNNER.attach_full_native_mask_address_frames(
        [record], {uid: measured}, descriptors
    )
    assert observation["address_frame"]["origin_lps"] == [1, 2, 3]
    assert len(calls) == 1
