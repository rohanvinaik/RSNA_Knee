from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from knee.study.tables import SeriesRow

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location(
    "rsna_run_interiors_for_native_menisci_tests", ROOT / "scripts" / "run_interiors.py"
)
assert SPEC is not None and SPEC.loader is not None
run = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = run
SPEC.loader.exec_module(run)


def _own(
    view=("Coronal", "1", "1"),
    *,
    z=1,
    pixels=None,
    volume=None,
    fluid_sensitive="1",
    fat_suppression="1",
):
    if pixels is None:
        pixels = np.zeros((16, 16), dtype=np.uint8)
        pixels[1, 2] = run.OBJECT_CODES["medial_meniscus"]
        pixels[1, 3] = run.OBJECT_CODES["lateral_meniscus"]
    if volume is None:
        volume = np.ones((4, 16, 16), dtype=np.float64)
    series = SimpleNamespace(
        row=SeriesRow(
            study_uid="study-native",
            series_uid="series-native",
            fluid_sensitive=fluid_sensitive,
            fat_suppression=fat_suppression,
            anatomical_plane=view[0],
        ),
        volume=volume,
        slice_thickness_mm=(1.0,) * len(volume),
    )
    arrays: dict[str, Any] = {"a1_objects": pixels}
    return SimpleNamespace(
        record={
            "series_uid": "series-native",
            "view": list(view),
            "slice_index": z,
            "observations": [],
        },
        arrays=arrays,
        series=series,
    )


def _row(own, *, object_name="medial_meniscus", count=1):
    label = run.OBJECT_CODES[object_name]
    return {
        "object": object_name,
        "provenance": "native",
        "kind": "resolved",
        "code": "identified",
        "series_uid": own.record["series_uid"],
        "view": tuple(own.record["view"]),
        "slices": (own.record["slice_index"],),
        "support": "a1_objects",
        "row": None,
        "label": label,
        "count": count,
        "artifact": "native-artifact",
    }


def _frame(*_args):
    # Oblique native row/column basis with anisotropic 2 mm and 1 mm spacing.
    root_two = np.sqrt(2.0)
    basis = np.asarray(
        [[0.0, 0.0], [root_two, -0.5 * root_two], [root_two, 0.5 * root_two]]
    )
    return run.PlaneFrame(np.asarray([10.0, 20.0, 30.0]), basis, (2.0, 1.0))


def _quiet(monkeypatch):
    monkeypatch.setattr(run, "reads", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(run, "handed", lambda *_args, **_kwargs: None)


def test_sources_require_native_coronal_label_count_and_address(monkeypatch):
    _quiet(monkeypatch)
    own = _own()
    own.record["observations"] = [
        _row(own),
        _row(own, object_name="lateral_meniscus"),
    ]
    laid = _own()
    laid.record["series_uid"] = "laid-series"
    laid.record["observations"] = [{**_row(laid), "provenance": "laid"}]
    wrong_count = _own()
    wrong_count.record["series_uid"] = "wrong-count-series"
    wrong_count.record["observations"] = [_row(wrong_count, count=2)]
    wrong_label = _own()
    wrong_label.record["series_uid"] = "wrong-label-series"
    wrong_label.record["observations"] = [{**_row(wrong_label), "label": 999}]
    wrong_view = _own(view=("Axial", "1", "1"))
    wrong_view.record["observations"] = [_row(wrong_view)]
    monkeypatch.setattr(run, "artifact_of", lambda _study, _record: "native-artifact")
    monkeypatch.setattr(run, "plane_frame", _frame)

    sources = run.native_meniscus_sources(
        [own, laid, wrong_count, wrong_label, wrong_view], "study"
    )

    selected = sources["medial_meniscus"]
    assert selected["status"] == "selected"
    assert selected["point_count"] == 1
    assert selected["selected"]["owner"] is own
    assert selected["entries"][0]["support"] == "a1_objects"
    assert "a4_medial_meniscus_source_lps" in own.arrays
    lateral = sources["lateral_meniscus"]
    assert lateral["status"] == "selected"
    assert lateral["point_count"] == 1
    assert (
        lateral["selected"]["metadata"]["label"] == run.OBJECT_CODES["lateral_meniscus"]
    )
    for rejected in (laid, wrong_count, wrong_label, wrong_view):
        assert "a4_meniscus_sources" not in rejected.record
        assert "a4_medial_meniscus_source_lps" not in rejected.arrays


def test_non_fs_sagittal_target_skips_profile_volume_and_local_reader(monkeypatch):
    _quiet(monkeypatch)

    class NoVolume:
        row = SeriesRow(
            study_uid="study-native",
            series_uid="series-native",
            fluid_sensitive="0",
            fat_suppression="1",
            anatomical_plane="Sagittal",
        )

        @property
        def volume(self):
            raise AssertionError("unsupported target sequence must be rejected first")

    own = _own(view=("Sagittal", "0", "1"))
    own.series = NoVolume()
    monkeypatch.setattr(
        run,
        "native_meniscus_profiles",
        lambda *_args: (_ for _ in ()).throw(AssertionError("profile must be skipped")),
    )
    monkeypatch.setattr(
        run,
        "meniscus_local_body",
        lambda *_args: (_ for _ in ()).throw(
            AssertionError("local read must be skipped")
        ),
    )
    sources = {
        name: {"status": "selected"} for name in ("medial_meniscus", "lateral_meniscus")
    }

    rows = run.name_native_menisci([own], sources, "study", None)

    assert rows[0][0] == []
    assert [row.code for row in rows[0][1]] == [
        "unsupported_target_sequence",
        "unsupported_target_sequence",
    ]


def test_missing_sources_skip_map_guide_and_window_body(monkeypatch):
    _quiet(monkeypatch)
    own = _own(view=("Sagittal", "1", "1"))
    monkeypatch.setattr(run, "plane_frame", _frame)
    monkeypatch.setattr(
        run,
        "meniscus_local_body",
        lambda *_args: (_ for _ in ()).throw(
            AssertionError("no source means no local read")
        ),
    )

    class NoGuide:
        def guide(self, *_args):
            raise AssertionError("no selected source means no map guide read")

    profiles = run.native_meniscus_profiles(
        own,
        {
            "medial_meniscus": {"status": "unavailable"},
            "lateral_meniscus": {"status": "tied"},
        },
        NoGuide(),
    )

    assert profiles["medial_meniscus"]["status"] == "unavailable"
    assert profiles["lateral_meniscus"]["status"] == "tied"
    rows = run.name_native_menisci(
        [own],
        {
            "medial_meniscus": {"status": "unavailable"},
            "lateral_meniscus": {"status": "tied"},
        },
        "study",
        None,
    )
    assert rows[0][0] == []
    assert [row.code for row in rows[0][1]] == ["source_unavailable", "source_tied"]


def test_source_point_uses_full_radius_window_and_candidate_readings_are_retained(
    monkeypatch,
):
    _quiet(monkeypatch)
    own = _own(view=("Sagittal", "1", "1"), volume=np.ones((4, 16, 16)))
    own.record["series_uid"] = "target-series"
    # A source point at the near corner of its object; the opposite corner is four mm away.
    unique_rc = np.asarray([[4.0, 4.0]])
    per_slice = {
        z: {
            "unique_rc": unique_rc.copy(),
            "sample_rc": unique_rc.copy(),
            "in_map": np.zeros(1, bool),
        }
        for z in range(4)
    }
    statuses = np.asarray([3, 5, 0, 4], dtype=np.int8)
    profile = {
        "status": "measured",
        "counts": np.asarray([8.0, 8.0, 8.0, 8.0]),
        "unique_counts": np.asarray([8.0, 8.0, 8.0, 8.0]),
        "map_counts": np.zeros(4),
        "statuses": statuses,
        "complete": np.asarray([True, False, False, True]),
        "per_slice": per_slice,
        "guide": None,
        "product": "native_sagittal_meniscus_profiles",
        "source_product": "native_meniscus_sources",
    }
    sources = {
        "medial_meniscus": {
            "status": "selected",
            "selected": {
                "points_lps": np.asarray([[0.0, 0.0, 0.0]]),
                "metadata": {"series_uid": "source-series"},
            },
        },
        "lateral_meniscus": {"status": "unavailable"},
    }
    monkeypatch.setattr(
        run,
        "native_meniscus_profiles",
        lambda *_args, **_kwargs: {
            "medial_meniscus": profile,
            "lateral_meniscus": {"status": "unavailable"},
        },
    )
    monkeypatch.setattr(run, "plane_frame", _frame)
    monkeypatch.setattr(
        run, "finite_of", lambda _series: np.ones((4, 16, 16), dtype=bool)
    )
    monkeypatch.setattr(run, "margin_of", lambda *_args: np.zeros((16, 16), dtype=bool))
    monkeypatch.setattr(
        run.anatomy_map, "target_span_mm", lambda *_args: (4.0, 4.0, 4.0)
    )
    actual_source_window = run.source_window
    spans = []

    def capture_window(points, span, frame, shape):
        spans.append(tuple(span))
        return actual_source_window(points, span, frame, shape)

    monkeypatch.setattr(run, "source_window", capture_window)
    body_calls = []

    def local_body(raw, available, target, frame):
        body_calls.append((raw.copy(), target.copy()))
        index = len(body_calls) - 1
        code = (
            "measured_empty",
            "partial_reading",
            "tied_largest_components",
            "identified",
        )[index]
        selection = (
            "measured_empty",
            "partial_reading",
            "tied_largest_components",
            "identified",
        )[index]
        selected = np.zeros(raw.shape, dtype=bool)
        if index:
            selected[0, 0] = True
        return {
            "status": code,
            "selection_status": selection,
            "selected": selected,
            "availability": available.copy(),
            "depth_input": raw.copy(),
            "enclosed_depth": np.zeros(raw.shape),
            "positive_enclosure": np.zeros(raw.shape, dtype=bool),
            "opened": np.zeros(raw.shape, dtype=bool),
            "labels": np.zeros(raw.shape, dtype=np.int32),
            "distance_to_target": np.zeros(raw.shape),
            "contacted_components": np.zeros(raw.shape, dtype=bool),
        }

    monkeypatch.setattr(run, "meniscus_local_body", local_body)

    rows = run.name_native_menisci([own], sources, "study", None)

    assert spans and set(spans) == {(8.0, 8.0, 8.0)}
    # A four-mm half-span reaches the opposite object corner at native (6, 8).
    crop = own.arrays["a4_medial_meniscus_z0_raw_crop"]
    window = own.record["a4_native_meniscus_candidate_status"]["medial_meniscus"][0][
        "window"
    ]
    r0, r1, c0, c1 = window["window_rc_exclusive"]
    assert r0 <= 6 < r1 and c0 <= 8 < c1
    assert crop.shape == (r1 - r0, c1 - c0)
    assert len(body_calls) == 4
    candidate_rows = own.record["a4_native_meniscus_candidate_status"][
        "medial_meniscus"
    ]
    assert [row["status"] for row in candidate_rows] == [
        "measured_empty",
        "partial_reading",
        "tied_largest_components",
        "identified",
    ]
    medial_observations, unresolved = rows[0]
    assert [row.kind for row in medial_observations] == [
        "reading",
        "reading",
        "resolved",
    ]
    assert [row.code for row in medial_observations] == [
        "measured_empty",
        "partial_reading",
        "identified",
    ]
    assert any(row.code == "local_body_tied_largest_components" for row in unresolved)
    assert any(row.code.startswith("local_body_partial_reading") for row in unresolved)
    assert "a4_medial_meniscus_z3_support" in own.arrays


@pytest.mark.parametrize(
    ("status", "selection_status", "has_selected", "resolved"),
    [
        ("partial_reading", "identified", True, True),
        ("partial_reading", "measured_empty", False, False),
        ("tied_largest_components", "tied_largest_components", False, False),
    ],
)
def test_partial_scope_resolves_only_an_identified_selected_component(
    monkeypatch, status, selection_status, has_selected, resolved
):
    _quiet(monkeypatch)
    own = _own(view=("Sagittal", "1", "1"), volume=np.ones((4, 16, 16)))
    own.record["series_uid"] = "partial-scope-series"
    selected_source = {
        "status": "selected",
        "selected": {
            "points_lps": np.asarray([[0.0, 0.0, 0.0]]),
            "metadata": {"series_uid": "source-series"},
        },
    }
    sources = {
        "medial_meniscus": selected_source,
        "lateral_meniscus": {"status": "unavailable"},
    }
    unique_rc = np.asarray([[4.0, 4.0]])
    per_slice = {
        z: {
            "unique_rc": unique_rc.copy() if z == 0 else np.empty((0, 2)),
            "sample_rc": unique_rc.copy() if z == 0 else np.empty((0, 2)),
            "in_map": np.zeros(1, dtype=bool),
        }
        for z in range(4)
    }
    profile = {
        "status": "measured",
        "counts": np.asarray([8.0, 0.0, 0.0, 0.0]),
        "unique_counts": np.asarray([8.0, 0.0, 0.0, 0.0]),
        "map_counts": np.zeros(4),
        "statuses": np.asarray([3, 0, 0, 0], dtype=np.int8),
        "per_slice": per_slice,
        "guide": None,
        "product": "native_sagittal_meniscus_profiles",
        "source_product": "native_meniscus_sources",
    }
    monkeypatch.setattr(
        run,
        "native_meniscus_profiles",
        lambda *_args, **_kwargs: {
            "medial_meniscus": profile,
            "lateral_meniscus": {"status": "unavailable"},
        },
    )
    monkeypatch.setattr(run, "plane_frame", _frame)
    monkeypatch.setattr(
        run, "finite_of", lambda _series: np.ones((4, 16, 16), dtype=bool)
    )
    monkeypatch.setattr(run, "margin_of", lambda *_args: np.zeros((16, 16), dtype=bool))
    monkeypatch.setattr(
        run.anatomy_map, "target_span_mm", lambda *_args: (4.0, 4.0, 4.0)
    )

    def local_body(raw, available, target, frame):
        selected = np.zeros(raw.shape, dtype=bool)
        if has_selected:
            selected[0, 0] = True
        return {
            "status": status,
            "selection_status": selection_status,
            "selected": selected,
            "availability": available.copy(),
            "depth_input": raw.copy(),
            "enclosed_depth": np.zeros(raw.shape),
            "positive_enclosure": np.zeros(raw.shape, dtype=bool),
            "opened": selected.copy(),
            "labels": selected.astype(np.int32),
            "distance_to_target": np.zeros(raw.shape),
            "contacted_components": selected.copy(),
        }

    monkeypatch.setattr(run, "meniscus_local_body", local_body)
    rows = run.name_native_menisci([own], sources, "study", None)

    observations, unresolved = rows[0]
    native_rows = [row for row in observations if row.object == "medial_meniscus"]
    assert (
        any(row.kind == "resolved" and row.code == "identified" for row in native_rows)
        is resolved
    )
    support = "a4_medial_meniscus_z0_support"
    if resolved:
        assert own.arrays[support].sum() == 1
        assert own.arrays[f"{support}_slices"].tolist() == [0]
    else:
        assert support not in own.arrays
        assert any(row.object == "medial_meniscus" for row in unresolved)


def test_unavailable_raw_values_do_not_change_local_body_measurement():
    raw = np.full((9, 9), 100.0)
    raw[2:7, 2:7] = 40.0
    available = np.ones(raw.shape, dtype=bool)
    available[4, 4] = False
    target = np.zeros(raw.shape, dtype=bool)
    target[4, 2] = True
    changed = raw.copy()
    changed[4, 4] = -1_000_000.0

    first = run.meniscus_local_body(raw, available, target, _frame())
    second = run.meniscus_local_body(changed, available, target, _frame())

    for key in (
        "status",
        "selection_status",
        "available_pixels",
        "unavailable_pixels",
        "component_count",
        "contacted_components_pixels",
        "selected_pixels",
    ):
        assert first[key] == second[key]
    for key in (
        "availability",
        "depth_input",
        "enclosed_depth",
        "positive_enclosure",
        "opened",
        "labels",
        "selected",
    ):
        np.testing.assert_array_equal(first[key], second[key])
