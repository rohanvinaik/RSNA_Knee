"""Prerequisite refusals for the native cross-view retinacula reader."""

from types import SimpleNamespace

import numpy as np
import pytest

from scripts import run_interiors


def _own(view="sagittal", *, knee="R", fluid="1", fat="1", level=(352.0,)):
    record = {
        "series_uid": "series-a",
        "view": (view, "FS"),
        "assignments": {"knee": knee},
        "recess": {"level": level},
    }
    series = SimpleNamespace(
        row=SimpleNamespace(
            series_uid="series-a", fluid_sensitive=fluid, fat_suppression=fat
        ),
        volume=np.zeros((1, 12, 14), dtype=float),
        slice_thickness_mm=[1.0],
    )
    return SimpleNamespace(record=record, series=series, arrays={})


def _refusal_codes(result):
    _, unresolved = result
    return [item.code for item in unresolved]


def test_coronal_reader_refuses_unknown_knee_laterality():
    result = run_interiors.cross_view_retinacula(
        _own("coronal", knee="?"), {}, "study-a", None
    )

    assert _refusal_codes(result) == [
        "coronal_retinacular_outer_bands:knee_laterality_unavailable",
        "coronal_retinacular_outer_bands:knee_laterality_unavailable",
    ]


@pytest.mark.parametrize("level", [[], np.array(np.nan)])
def test_reader_names_empty_or_scalar_unavailable_fluid_level(level):
    result = run_interiors.cross_view_retinacula(_own(level=level), {}, "study-a", None)

    assert _refusal_codes(result) == [
        "sagittal_retinacular_outer_bands:same_series_recess_level_unavailable",
        "sagittal_retinacular_outer_bands:same_series_recess_level_unavailable",
    ]


@pytest.mark.parametrize("flags", [{"fluid": "0"}, {"fat": "0"}])
def test_reader_requires_a_fluid_sensitive_fat_suppressed_sequence(flags):
    result = run_interiors.cross_view_retinacula(_own(**flags), {}, "study-a", None)

    assert _refusal_codes(result) == [
        "sagittal_retinacular_outer_bands:fluid_not_bright_on_this_sequence",
        "sagittal_retinacular_outer_bands:fluid_not_bright_on_this_sequence",
    ]


def test_missing_axial_source_is_named_without_a_native_candidate_read(monkeypatch):
    monkeypatch.setattr(
        run_interiors, "finite_of", lambda _series: np.ones((1, 12, 14), dtype=bool)
    )
    monkeypatch.setattr(run_interiors, "handed", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(run_interiors, "reads", lambda *_args, **_kwargs: None)
    result = run_interiors.cross_view_retinacula(_own(), {}, "study-a", None)

    assert _refusal_codes(result) == [
        "sagittal_retinacular_outer_bands:no_native_axial_source",
        "sagittal_retinacular_outer_bands:no_native_axial_source",
    ]


def _profile_reader_inputs(counts):
    depth = len(counts)
    own = _own()
    own.record["view"] = ("Sagittal", "1", "1")
    own.record["background_split"] = 0.5
    own.series.volume = np.zeros((depth, 12, 14), dtype=float)
    own.series.slice_thickness_mm = [1.0] * depth
    side = run_interiors.RETINACULA[0]
    source = {
        side: {
            "status": "selected",
            "points": np.asarray(
                [[1.0, 1.0, float(z)] for z in range(max(counts) + 1)]
            ),
            "metadata": {"support": "axial-source"},
        }
    }
    sample_rows = np.asarray(
        [[1 + index // 4, 1 + index % 4] for index in range(max(counts))],
        dtype=np.int32,
    )
    guide = SimpleNamespace(
        status="guided",
        slices=(depth - 2,),
        anchors=("joint_fluid",),
        placements=({"status": "ok", "point_lps": [1.0, 1.0, 0.0]},),
        half_px=(20.0, 20.0),
    )
    calls = {"native_z": [], "map_rows": []}

    class Frame:
        spacing_rc = (1.0, 1.0)
        basis_lps = np.asarray([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])

        def __init__(self, z):
            self.z = z

        def to_native(self, points):
            return np.asarray(points, dtype=float)[:, :2]

    def project(_points, frame, _thickness, _shape):
        count = counts[frame.z]
        samples = sample_rows[:count]
        return samples.copy(), samples.copy(), count, True, None

    def native_context(name, *args):
        if name == "lens_of":
            calls["native_z"].append(args[1])
            return None, SimpleNamespace(available=np.ones((12, 14), dtype=bool)), None
        return None

    def white_components(*_args):
        return np.ones((12, 14), dtype=np.int32), []

    def closest(*_args, **_kwargs):
        body = np.zeros((12, 14), dtype=bool)
        body[4:7, 4:7] = True
        return (
            body,
            body.copy(),
            {
                "status": "selected_nearest_native_white_body",
                "components": [],
                "nearest_source_distance_mm": 1.0,
            },
        )

    def wall(*_args, **_kwargs):
        band = np.zeros((12, 14), dtype=bool)
        band[4, 4] = True
        return {
            "strip": band.copy(),
            "minimum_band": band,
            "status": np.zeros(12, dtype=np.int8),
            "body_outer_edge_mm": np.zeros(12, dtype=float),
            "row_minimum": np.zeros(12, dtype=float),
            "adjacent_median": np.ones(12, dtype=float),
        }

    mapping = SimpleNamespace(
        guide=lambda *_args: guide,
        smap=SimpleNamespace(
            note_use=lambda *args, **kwargs: calls["map_rows"].append((args, kwargs))
        ),
    )
    return (
        own,
        source,
        mapping,
        counts,
        sample_rows,
        calls,
        Frame,
        project,
        native_context,
        white_components,
        closest,
        wall,
    )


def _run_profile_reader(monkeypatch, counts):
    (
        own,
        sources,
        mapping,
        counts,
        _sample_rows,
        calls,
        Frame,
        project,
        native_context,
        white_components,
        closest,
        wall,
    ) = _profile_reader_inputs(counts)
    monkeypatch.setattr(
        run_interiors,
        "finite_of",
        lambda _series: np.ones(own.series.volume.shape, dtype=bool),
    )
    monkeypatch.setattr(run_interiors, "plane_frame", lambda _series, z: Frame(z))
    monkeypatch.setattr(run_interiors, "_extensor_source_projection", project)
    monkeypatch.setattr(
        run_interiors, "lens_of", lambda *args: native_context("lens_of", *args)
    )
    monkeypatch.setattr(
        run_interiors,
        "field_of",
        lambda *_args: SimpleNamespace(leg=np.ones((12, 14), dtype=bool)),
    )
    monkeypatch.setattr(
        run_interiors, "margin_of", lambda *_args: np.zeros((12, 14), dtype=bool)
    )
    monkeypatch.setattr(run_interiors, "white_components", white_components)
    monkeypatch.setattr(run_interiors, "closest_white_body", closest)
    monkeypatch.setattr(run_interiors, "relative_outer_wall", wall)
    monkeypatch.setattr(
        run_interiors,
        "measures_of",
        lambda *_args: SimpleNamespace(along=lambda _axis: np.asarray([0.0, 1.0, 0.0])),
    )
    monkeypatch.setattr(run_interiors, "handed", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(run_interiors, "reads", lambda *_args, **_kwargs: None)

    run_interiors.cross_view_retinacula(own, sources, "study-a", mapping)
    return own, calls


def test_guided_hit_checks_stronger_source_profile_peak(monkeypatch):
    own, calls = _run_profile_reader(monkeypatch, [2, 0, 1, 0])

    side = run_interiors.RETINACULA[0]
    detail = own.record["sagittal_retinacular_outer_bands"]["sides"][side]
    review = detail["source_profile_review"]
    assert calls["native_z"] == [2, 0]
    assert review == {
        "guided_resolved_profile_count_max": 1,
        "stronger_source_peaks_checked": [{"slice": 0, "profile_count": 2}],
        "source_peaks_skipped_not_stronger": [],
    }
    assert calls["map_rows"][0][0][2] == "guided_hit_source_profile_stronger_checked"
    assert calls["map_rows"][0][1]["source_profile_review"] == review
    assert own.arrays[f"a4_sagittal_{side}_slices"].tolist() == [2, 0]


def test_guided_hit_skips_equal_or_weaker_source_profile_peak(monkeypatch):
    own, calls = _run_profile_reader(monkeypatch, [1, 0, 2, 0])

    side = run_interiors.RETINACULA[0]
    detail = own.record["sagittal_retinacular_outer_bands"]["sides"][side]
    review = detail["source_profile_review"]
    assert calls["native_z"] == [2]
    assert review == {
        "guided_resolved_profile_count_max": 2,
        "stronger_source_peaks_checked": [],
        "source_peaks_skipped_not_stronger": [{"slice": 0, "profile_count": 1}],
    }
    assert calls["map_rows"][0][0][2] == "guided_hit"
    assert own.arrays[f"a4_sagittal_{side}_slices"].tolist() == [2]
