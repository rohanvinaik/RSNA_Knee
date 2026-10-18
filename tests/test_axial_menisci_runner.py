from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

from knee.study.tables import SeriesRow

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location(
    "rsna_run_interiors_for_axial_menisci_tests", ROOT / "scripts" / "run_interiors.py"
)
assert SPEC is not None and SPEC.loader is not None
run = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = run
SPEC.loader.exec_module(run)


def _own(
    view=("Axial", "1", "1"),
    *,
    z=0,
    pixels=None,
    volume=None,
    fluid_sensitive="1",
    fat_suppression="1",
):
    if pixels is None:
        pixels = np.asarray(
            [[0, run.OBJECT_CODES["medial_meniscus"], 0]], dtype=np.uint8
        )
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


def _selected_source(name, points, *, owner=None, metadata=None):
    return {
        "status": "selected",
        "selected": {
            "owner": owner,
            "points_lps": np.asarray(points, dtype=np.float64),
            "metadata": metadata or {"series_uid": "source-series", "slice": 2},
        },
        "entries": [],
        "point_count": len(points),
    }


def _unavailable():
    return {"status": "unavailable", "selected": None, "entries": [], "point_count": 0}


def _quiet(monkeypatch):
    monkeypatch.setattr(run, "reads", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(run, "handed", lambda *_args, **_kwargs: None)


def _frame(*_args):
    return run.PlaneFrame(
        np.asarray([0.0, 0.0, 0.0]),
        np.asarray([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]),
        (1.0, 1.0),
    )


def test_sagittal_source_collector_consumes_pending_native_support_and_keeps_address(
    monkeypatch,
):
    _quiet(monkeypatch)
    own = _own(view=("Sagittal", "1", "1"), z=3)
    support = np.zeros((16, 16), dtype=bool)
    support[1, 2:5] = True
    own.arrays = {
        "a4_medial_meniscus_z3_support": support,
        "a4_medial_meniscus_z3_support_slices": np.asarray([3], dtype=np.int32),
    }
    observation = run.observe(
        "medial_meniscus",
        "native",
        "resolved",
        own,
        (3,),
        "identified",
        3,
        0.0,
        "a4_medial_meniscus_z3_support",
        "native sagittal support",
        "native-artifact",
    )
    monkeypatch.setattr(run, "artifact_of", lambda *_args: "native-artifact")
    monkeypatch.setattr(run, "plane_frame", _frame)

    sources = run.native_meniscus_sources(
        [own], "study", orientation="sagittal", pending=[([observation], [])]
    )

    selected = sources["medial_meniscus"]
    assert selected["status"] == "selected"
    assert selected["point_count"] == 3
    assert selected["selected"]["owner"] is own
    assert selected["selected"]["metadata"]["slice"] == 3
    assert (
        selected["selected"]["metadata"]["support"] == "a4_medial_meniscus_z3_support"
    )
    assert selected["selected"]["metadata"]["count"] == 3
    assert selected["selected"]["metadata"]["view"] == ["Sagittal", "1", "1"]


def test_sagittal_source_collector_rejects_non_native_or_misaddressed_rows(monkeypatch):
    _quiet(monkeypatch)
    cases = []
    for changes in (
        {"provenance": "laid"},
        {"kind": "reading"},
        {"count": 4},
        {"support_slices": [2]},
        {"fluid_sensitive": "0"},
    ):
        own = _own(
            view=("Sagittal", "1", "1"),
            z=3,
            fluid_sensitive=changes.get("fluid_sensitive", "1"),
        )
        mask = np.zeros((16, 16), dtype=bool)
        mask[1, 2:5] = True
        support_key = "a4_medial_meniscus_z3_support"
        own.arrays = {
            support_key: mask,
            f"{support_key}_slices": np.asarray([3], dtype=np.int32),
        }
        values = {
            "object": "medial_meniscus",
            "provenance": "native",
            "kind": "resolved",
            "code": "identified",
            "series_uid": own.record["series_uid"],
            "view": ("Sagittal", "1", "1"),
            "slices": (3,),
            "support": support_key,
            "row": None,
            "label": None,
            "count": 3,
            "artifact": "native-artifact",
        }
        values.update(
            {
                k: v
                for k, v in changes.items()
                if k != "support_slices" and k != "fluid_sensitive"
            }
        )
        if "support_slices" in changes:
            own.arrays[f"{support_key}_slices"] = np.asarray(
                changes["support_slices"], dtype=np.int32
            )
        cases.append((own, SimpleNamespace(**values)))

    monkeypatch.setattr(run, "artifact_of", lambda *_args: "native-artifact")
    monkeypatch.setattr(run, "plane_frame", _frame)
    sources = run.native_meniscus_sources(
        [own for own, _ in cases],
        "study",
        orientation="sagittal",
        pending=[([observation], []) for _, observation in cases],
    )

    assert sources["medial_meniscus"]["status"] == "unavailable"
    assert sources["medial_meniscus"]["entries"] == []
    assert all(
        "a4_sagittal_medial_meniscus_source_lps" not in own.arrays for own, _ in cases
    )


def test_axial_missing_secondary_source_skips_profiles_and_local_body(monkeypatch):
    _quiet(monkeypatch)
    own = _own(view=("Axial", "1", "1"))

    class NoVolume:
        row = SeriesRow(
            study_uid="study-native",
            series_uid="series-native",
            fluid_sensitive="1",
            fat_suppression="1",
            anatomical_plane="Axial",
        )

        @property
        def volume(self):
            raise AssertionError(
                "unpaired axial source must be rejected before volume access"
            )

    own.series = NoVolume()
    sources = {
        "medial_meniscus": _selected_source("medial_meniscus", [[0.0, 0.0, 0.0]]),
        "lateral_meniscus": _unavailable(),
    }
    monkeypatch.setattr(run, "plane_frame", _frame)
    monkeypatch.setattr(
        run,
        "native_meniscus_profiles",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("missing paired source must skip profile computation")
        ),
    )
    monkeypatch.setattr(
        run,
        "meniscus_local_body",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("missing secondary source must skip the local reader")
        ),
    )

    rows = run.name_native_menisci(
        [own],
        sources,
        "study",
        None,
        orientation="axial",
        other_sources={
            "medial_meniscus": _unavailable(),
            "lateral_meniscus": _unavailable(),
        },
    )

    assert rows[0][0] == []
    assert any(row.code == "other_source_unavailable" for row in rows[0][1])
    assert "a4_native_meniscus_candidates" not in own.record


def test_axial_primary_and_secondary_targets_are_distinct_and_cache_key_includes_both(
    monkeypatch,
):
    _quiet(monkeypatch)
    own = _own(view=("Axial", "1", "1"), volume=np.ones((1, 16, 16)))
    own.record["series_uid"] = "axial-target"
    primary = _selected_source("medial_meniscus", [[0.0, 0.0, 0.0]])
    secondary_a = _selected_source("medial_meniscus", [[4.0, 0.0, 0.0]])
    secondary_b = _selected_source("medial_meniscus", [[6.0, 0.0, 0.0]])
    source_groups = [
        (
            {"medial_meniscus": primary, "lateral_meniscus": _unavailable()},
            {"medial_meniscus": secondary_a, "lateral_meniscus": _unavailable()},
        ),
        (
            {"medial_meniscus": primary, "lateral_meniscus": _unavailable()},
            {"medial_meniscus": secondary_b, "lateral_meniscus": _unavailable()},
        ),
    ]
    monkeypatch.setattr(run, "plane_frame", _frame)

    def project_source(points, _frame, _thickness, _shape):
        rc = np.asarray([[round(points[0, 0]) + 4, 4]], dtype=np.int32)
        return rc, rc.copy(), 1, True, None

    monkeypatch.setattr(run, "_extensor_source_projection", project_source)
    monkeypatch.setattr(
        run, "finite_of", lambda _series: np.ones((1, 16, 16), dtype=bool)
    )
    monkeypatch.setattr(run, "margin_of", lambda *_args: np.zeros((16, 16), dtype=bool))
    monkeypatch.setattr(
        run.anatomy_map, "target_span_mm", lambda *_args: (4.0, 4.0, 4.0)
    )
    monkeypatch.setattr(run, "artifact_of", lambda *_args: "native-artifact")
    monkeypatch.setattr(
        run,
        "source_window",
        lambda *_args: {"status": "present", "window_rc_exclusive": (0, 12, 0, 12)},
    )
    monkeypatch.setattr(
        run, "once", lambda _name, key, select: (cache_keys.append(key), select())[1]
    )
    cache_keys = []
    helper_calls = []

    def local_body(raw, available, target, frame, *, other_target=None):
        helper_calls.append(
            (target.copy(), other_target.copy() if other_target is not None else None)
        )
        return {
            "status": "identified",
            "selection_status": "identified",
            "selected": np.ones(raw.shape, dtype=bool),
            "availability": available,
            "depth_input": raw,
            "enclosed_depth": np.zeros(raw.shape),
            "positive_enclosure": np.zeros(raw.shape, bool),
            "opened": np.zeros(raw.shape, bool),
            "labels": np.zeros(raw.shape, np.int32),
            "distance_to_target": np.zeros(raw.shape),
            "contacted_components": np.zeros(raw.shape, bool),
        }

    monkeypatch.setattr(run, "meniscus_local_body", local_body)
    for sources, other_sources in source_groups:
        rows = run.name_native_menisci(
            [own],
            sources,
            "study",
            None,
            orientation="axial",
            other_sources=other_sources,
        )
    resolved = [
        row
        for row in rows[0][0]
        if row.kind == "resolved" and row.object == "medial_meniscus"
    ]
    assert len(resolved) == 1
    assert resolved[0].support == "a4_axial_medial_meniscus_z0_support"
    assert resolved[0].slices == (0,)
    assert resolved[0].count == 144

    assert len(helper_calls) == 2
    assert all(call[1] is not None and call[1].any() for call in helper_calls)
    assert not np.array_equal(helper_calls[0][1], helper_calls[1][1])
    assert len(cache_keys) == 2 and cache_keys[0] != cache_keys[1]
    assert [call[0].sum() for call in helper_calls] == [1, 1]
    assert all(call[0].sum() == 1 and call[1].sum() == 1 for call in helper_calls)
    assert "a4_axial_medial_meniscus_z0_support" in own.arrays
    assert own.arrays["a4_axial_medial_meniscus_z0_support"].dtype == np.bool_
    assert (
        int(own.arrays["a4_axial_medial_meniscus_z0_support"].sum())
        == resolved[0].count
    )
    assert own.arrays["a4_axial_medial_meniscus_z0_support_slices"].tolist() == [0]
    assert "a4_axial_medial_meniscus_z0_other_target_crop" in own.arrays
    assert np.array_equal(
        own.arrays["a4_axial_medial_meniscus_z0_target_crop"], helper_calls[1][0]
    )
    assert np.array_equal(
        own.arrays["a4_axial_medial_meniscus_z0_other_target_crop"], helper_calls[1][1]
    )
    assert "a4_axial_lateral_meniscus_z0_support" not in own.arrays


def test_axial_native_profile_uses_distinct_tag_without_changing_sagittal_prefix(
    monkeypatch,
):
    _quiet(monkeypatch)
    own = _own(view=("Axial", "1", "1"), volume=np.ones((2, 16, 16)))
    source = _selected_source("medial_meniscus", [[0.0, 0.0, 0.0]])
    monkeypatch.setattr(run, "plane_frame", _frame)
    monkeypatch.setattr(
        run,
        "_extensor_source_projection",
        lambda *_args: (np.asarray([[1, 2]]), np.asarray([[1, 2]]), 1, True, None),
    )

    profile = run.native_meniscus_profiles(
        own,
        {"medial_meniscus": source},
        None,
        orientation="axial",
        source_tag="sagittal",
    )

    assert profile["medial_meniscus"]["status"] == "measured"
    assert "a4_axial_medial_meniscus_sagittal_source_profile_count" in own.arrays
    assert "a4_sagittal_medial_meniscus_source_profile_count" not in own.arrays
