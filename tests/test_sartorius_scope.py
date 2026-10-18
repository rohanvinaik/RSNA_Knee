"""Scoped contrast tests using the production grey-body selector and physical frame."""

from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest

from knee.collapse import anatomy_map
from knee.collapse.local_native import source_window
from knee.collapse.physical import PlaneFrame
from knee.objects import assignments
from knee.objects.assignments import (
    GRACILIS_REACH_MM,
    LOCAL_CONTRAST_MM,
    Measures,
    sartorius_on_slice,
    scoped_local_lightness,
    window_pixels,
)
from scripts import run_interiors as run

SHAPE = (200, 200)
FRAME = PlaneFrame(
    np.zeros(3), np.array([[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]]), (1.0, 1.0)
)
TARGET = np.zeros(SHAPE, dtype=bool)
TARGET[100:103, 100:103] = True
PLACES = FRAME.to_patient(np.argwhere(TARGET).astype(float)) + 20.0 * FRAME.normal()


def scope_for(target, frame=FRAME, shape=SHAPE):
    span = anatomy_map.target_span_mm("sartorius")
    assert span is not None
    full = (
        2.0 * (float(span[0]) + GRACILIS_REACH_MM),
        2.0 * (float(span[1]) + GRACILIS_REACH_MM),
        2.0 * (float(span[2]) + GRACILIS_REACH_MM),
    )
    return source_window(np.argwhere(target).astype(float), full, frame, shape)


def scene(bodies=()):
    plane = np.full(SHAPE, 100.0)
    for r0, r1, c0, c1 in bodies:
        plane[r0:r1, c0:c1] = 200.0
    return plane


def run_slice(plane, target=TARGET, scope=None, unseen=None, available=None):
    zeros = np.zeros(plane.shape, dtype=bool)
    return sartorius_on_slice(
        plane,
        zeros,
        zeros if unseen is None else unseen,
        PLACES,
        FRAME,
        "R",
        Measures(None, plane, FRAME.basis_lps),
        target,
        scope,
        available,
    )


def test_scope_validator_rejects_bad_shapes_and_fractional_boolean_or_nonfinite_bounds():
    bad = [
        {"status": "present", "window_rc_exclusive": [1, 20, 2]},
        {"status": "present", "window_rc_exclusive": [1, 20, 2, 30.5]},
        {"status": "present", "window_rc_exclusive": [True, 20, 2, 30]},
        {"status": "present", "window_rc_exclusive": [1, 20, 2, np.inf]},
        {"status": "present", "window_rc_exclusive": [1, 20, 2, 30]},
    ]
    assert [assignments.sartorius_scope_window(x, SHAPE) for x in bad] == [
        None,
        None,
        None,
        None,
        (1, 20, 2, 30),
    ]


def test_scoped_values_match_full_frame_inside_query_and_context_is_retained():
    rng = np.random.default_rng(3)
    plane = rng.uniform(50.0, 200.0, (160, 140))
    excluded = rng.random(plane.shape) < 0.1
    spacing = np.array([0.5, 2.0])
    window = (40, 100, 30, 90)
    full = assignments.local_lightness(plane, excluded, spacing)
    scoped = scoped_local_lightness(plane, excluded, spacing, window)
    r0, r1, c0, c1 = window
    for key, expected in zip(("lightness", "smooth", "surround"), full, strict=True):
        np.testing.assert_array_equal(scoped[key][r0:r1, c0:c1], expected[r0:r1, c0:c1])
        assert np.isnan(scoped[key][~scoped["query_window"]]).all()
    assert scoped["query_window"].sum() == (r1 - r0) * (c1 - c0)
    for key in (
        "context_raw",
        "context_excluded",
        "context_available",
        "context_not_low",
        "context_finite",
        "context_effective_available",
        "context_lightness",
        "context_smooth",
        "context_surround",
    ):
        assert scoped[key].shape == (102, 72)
    assert not scoped["context_effective_available"][scoped["context_excluded"]].any()


def test_context_halo_uses_anisotropic_pitch_and_clips_at_picture_edge():
    spacing = np.array([0.5, 2.0])
    rows, cols = window_pixels(spacing, LOCAL_CONTRAST_MM)
    plane = np.full((300, 200), 100.0)
    hidden = np.zeros(plane.shape, dtype=bool)
    inner = scoped_local_lightness(plane, hidden, spacing, (100, 150, 80, 120))
    assert tuple(inner["halo"]) == (rows // 2 + 1, cols // 2 + 1)
    corner = scoped_local_lightness(plane, hidden, spacing, (0, 50, 0, 50))
    assert corner["context"][0] == corner["context"][2] == 0


def test_scope_window_uses_authored_extent_plus_reach_in_physical_axes():
    frame = PlaneFrame(
        FRAME.origin_lps,
        np.array([[0.0, 2.0], [0.5, 0.0], [0.0, 0.0]]),
        (0.5, 2.0),
    )
    target = np.zeros((400, 400), dtype=bool)
    target[100:103, 100:103] = True
    scope = scope_for(target, frame, target.shape)
    span = anatomy_map.target_span_mm("sartorius")
    assert span is not None
    pad_r = int(np.ceil((span[1] + GRACILIS_REACH_MM) / 0.5))
    pad_c = int(np.ceil((span[0] + GRACILIS_REACH_MM) / 2.0))
    assert scope["window_rc_exclusive"] == [
        100 - pad_r,
        103 + pad_r,
        100 - pad_c,
        103 + pad_c,
    ]
    assert pad_r > pad_c


def test_real_selector_finds_body_inside_scope_and_retains_context_and_work_counts(
    monkeypatch,
):
    calls = []
    original = assignments.local_lightness

    def counted(plane, excluded, spacing):
        calls.append(tuple(np.shape(plane)))
        return original(plane, excluded, spacing)

    monkeypatch.setattr(assignments, "local_lightness", counted)
    body = (80, 100, 110, 116)
    plane = scene([body])
    scope = scope_for(TARGET)
    mask, readings, code = run_slice(plane, scope=scope)
    assert code == "identified"
    assert len(calls) == 1 and calls[0][0] * calls[0][1] < plane.size
    assert mask.shape == plane.shape and mask.dtype == bool
    assert mask[body[0] + 1 : body[1] - 1, body[2] + 1 : body[3] - 1].any()
    assert readings["contrast_context_raw"].size == calls[0][0] * calls[0][1]
    assert readings["contrast_query_window"].sum() == 93 * 97
    assert readings["contrast_effective_available"].sum() == 93 * 97
    assert readings["contrast_scope_window_rc"].tolist() == [55, 148, 53, 150]


def test_unavailable_pixels_are_not_reported_as_measured_empty():
    plane = scene([(70, 100, 110, 140)])
    available = np.ones(plane.shape, dtype=bool)
    available[80, 120] = False
    _, readings, code = run_slice(plane, scope=scope_for(TARGET), available=available)
    assert code == "identified"
    assert readings["contrast_query_window"][80, 120]
    assert not readings["contrast_effective_available"][80, 120]
    assert not readings["contrast_actual_available"][80, 120]
    assert readings["contrast_input_finite"][80, 120]
    assert np.isnan(readings["lightness"][80, 120])
    assert not readings["contrast_query_window"][10, 10]
    assert np.isnan(readings["lightness"][10, 10])


def test_tied_real_bodies_abstain_with_post_selector_counts():
    plane = scene([(87, 92, 102, 107), (94, 99, 102, 107)])
    mask, readings, code = run_slice(plane, scope=scope_for(TARGET))
    assert code == "abstain_tied_largest_bodies"
    assert not mask.any()
    assert readings["body_size_pixels"].size == 2
    assert readings["body_size_pixels"][0] == readings["body_size_pixels"][1]


def test_scope_refusal_happens_before_contrast_and_empty_target_is_not_read():
    calls = []
    real = assignments.local_lightness

    def counted(*args):
        calls.append(1)
        return real(*args)

    plane = scene([(70, 100, 110, 140)])
    empty_places = np.empty((0, 3))
    none = np.zeros(plane.shape, dtype=bool)
    mask, readings, code = sartorius_on_slice(
        plane, none, none, empty_places, FRAME, "R"
    )
    assert code == "abstain_no_gracilis_source" and not mask.any() and not readings
    monkeypatch_scope = {"status": "present", "window_rc_exclusive": [0, 250, 0, 30]}
    monkey = pytest.MonkeyPatch()
    monkey.setattr(assignments, "local_lightness", counted)
    try:
        _, _, code = run_slice(plane, target=TARGET, scope=monkeypatch_scope)
        assert code == "abstain_sartorius_scope_unavailable" and calls == []
    finally:
        monkey.undo()


def test_driver_projects_once_and_supplies_scope_before_contrast(monkeypatch):
    shape = (80, 80)
    frame = PlaneFrame(np.zeros(3), FRAME.basis_lps, (1.0, 1.0))
    plane = np.full(shape, 100.0)
    plane[25:55, 30:42] = 200.0
    cord = np.zeros(shape, dtype=bool)
    cord[50:56, 18:21] = True
    places = frame.to_patient(np.argwhere(cord).astype(float)) + 20 * frame.normal()
    own = cast(
        run.Measured,
        SimpleNamespace(
            series=SimpleNamespace(
                row=SimpleNamespace(
                    series_uid="ax", fat_suppression="1", fluid_sensitive="1"
                )
            ),
            record={
                "series_uid": "ax",
                "slice_index": 0,
                "assignments": {"knee": "R", "codes": {}},
            },
            arrays={
                "acquired_plane": plane,
                "b1_dark": np.zeros(shape, bool),
                "b1_available": np.ones(shape, bool),
            },
            frame=frame,
            assignment=SimpleNamespace(in_plane=(True, True, False)),
        ),
    )
    projection_calls = []
    original_projection = run.projected_places

    def project(*args):
        projection_calls.append(1)
        return original_projection(*args)

    monkeypatch.setattr(run, "projected_places", project)
    contrast_shapes = []
    original_lightness = assignments.local_lightness

    def contrast(plane, excluded, spacing):
        contrast_shapes.append(plane.shape)
        return original_lightness(plane, excluded, spacing)

    monkeypatch.setattr(assignments, "local_lightness", contrast)
    run.name_sartorius(own, places)
    assert len(projection_calls) == 1
    assert own.record["assignments"]["codes"]["sartorius"] == "identified"
    # exactly one contrast request, and on less than the whole plane
    assert len(contrast_shapes) == 1
    assert contrast_shapes[0][0] * contrast_shapes[0][1] < plane.size
    assert own.arrays["a2_sartorius_contrast_scope_window_rc"].shape == (4,)
    assert own.arrays["a2_sartorius_contrast_context_raw"].shape == contrast_shapes[0]
    assert own.arrays["a2_sartorius"].shape == shape
