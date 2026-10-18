from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from knee.study.tables import SeriesRow

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location(
    "rsna_run_interiors_for_native_pcl_tests", ROOT / "scripts" / "run_interiors.py"
)
assert SPEC is not None and SPEC.loader is not None
run = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = run
SPEC.loader.exec_module(run)

LABEL = run.OBJECT_CODES["pcl"]
SAG = ("Sagittal", "1", "0")
AX = ("Axial", "1", "1")
COR = ("Coronal", "1", "1")


def _own(uid, view=SAG, *, count=4, z=1, fluid="1", fat="0", depth=4):
    pixels = np.zeros((16, 16), dtype=np.uint8)
    pixels.flat[:count] = LABEL
    series = SimpleNamespace(
        row=SeriesRow(
            study_uid="study",
            series_uid=uid,
            fluid_sensitive=fluid,
            fat_suppression=fat,
            anatomical_plane=view[0],
        ),
        volume=np.ones((depth, 16, 16)),
        slice_thickness_mm=(3.0,) * depth,
    )
    own = SimpleNamespace(
        record={
            "series_uid": uid,
            "view": list(view),
            "slice_index": z,
            "observations": [],
        },
        arrays={"a1_objects": pixels},
        series=series,
    )
    own.record["observations"] = [_row(own, count)]
    return own


def _row(own, count):
    return {
        "object": "pcl",
        "provenance": "native",
        "kind": "resolved",
        "code": "identified",
        "series_uid": own.record["series_uid"],
        "view": tuple(own.record["view"]),
        "slices": (own.record["slice_index"],),
        "support": "a1_objects",
        "row": None,
        "label": LABEL,
        "count": count,
        "artifact": "art",
    }


def _sag_frames(spacings):
    def frame(series, _z):
        s = spacings[series.row.series_uid]
        basis = np.asarray([[0.0, s], [s, 0.0], [0.0, 0.0]])
        return run.PlaneFrame(np.zeros(3), basis, (s, s))

    return frame


def _axial_frame(_series, z):
    # row direction y at 2 mm, column direction x at 1 mm, slices 3 mm apart along z
    basis = np.asarray([[0.0, 1.0], [2.0, 0.0], [0.0, 0.0]])
    return run.PlaneFrame(np.asarray([0.0, 0.0, 3.0 * z]), basis, (2.0, 1.0))


@pytest.fixture(autouse=True)
def _quiet(monkeypatch):
    monkeypatch.setattr(run, "reads", lambda *a, **k: None)
    monkeypatch.setattr(run, "handed", lambda *a, **k: None)
    monkeypatch.setattr(run, "artifact_of", lambda *_a: "art")
    monkeypatch.setattr(run, "finite_of", lambda s: np.ones(np.shape(s.volume), bool))
    monkeypatch.setattr(run, "margin_of", lambda *_a: np.zeros((16, 16), bool))
    monkeypatch.setattr(run.anatomy_map, "target_span_mm", lambda *_a: (1.0, 1.0, 1.0))


def test_body_thickness_is_the_existing_three_mm():
    assert run.LIGAMENT_THICK_MM == 3.0


def test_unique_largest_physical_area_wins_not_count(monkeypatch):
    a, b = _own("a", count=4), _own("b", count=3)
    monkeypatch.setattr(run, "plane_frame", _sag_frames({"a": 1.0, "b": 2.0}))
    got = run.native_pcl_sources([a, b], "study")["pcl"]
    assert got["status"] == "selected"
    assert got["selected"]["owner"] is b  # 3 px * 4 mm2 > 4 px * 1 mm2
    assert got["largest_physical_area_mm2"] == 12.0
    assert b.arrays["a4_pcl_source_lps"].shape == (3, 3)


def test_equal_area_stays_tied_and_none_is_unavailable(monkeypatch):
    a, b = _own("a", count=3), _own("b", count=3)
    monkeypatch.setattr(run, "plane_frame", _sag_frames({"a": 2.0, "b": 2.0}))
    tied = run.native_pcl_sources([a, b], "study")["pcl"]
    assert tied["status"] == "tied" and tied["selected"] is None
    assert len(tied["entries"]) == 2
    assert run.native_pcl_sources([], "study")["pcl"]["status"] == "unavailable"


@pytest.mark.parametrize(
    "change",
    [
        {"provenance": "laid"},
        {"kind": "reading"},
        {"code": "laid_from_its_partner"},
        {"count": 5},
        {"label": 999},
        {"support": "a3_joint_plane_objects"},
        {"row": 0},
        {"slices": (2,)},
        {"slices": (1, 2)},
        {"series_uid": "other"},
        {"view": ("Sagittal", "1", "1")},
    ],
)
def test_source_rejects_unqualified_observation(monkeypatch, change):
    own = _own("a")
    own.record["observations"] = [{**own.record["observations"][0], **change}]
    monkeypatch.setattr(run, "plane_frame", _sag_frames({"a": 1.0}))
    assert run.native_pcl_sources([own], "study")["pcl"]["status"] == "unavailable"
    assert "a4_pcl_source_lps" not in own.arrays


@pytest.mark.parametrize(
    "kwargs", [{"view": ("Sagittal", "1", "1"), "fat": "1"}, {"view": AX}]
)
def test_fat_suppressed_or_non_sagittal_series_is_never_a_source(monkeypatch, kwargs):
    monkeypatch.setattr(run, "plane_frame", _sag_frames({"a": 1.0}))
    own = _own("a", **kwargs)
    assert run.native_pcl_sources([own], "study")["pcl"]["status"] == "unavailable"


def test_mask_count_must_match_saved_count(monkeypatch):
    own = _own("a")
    own.arrays["a1_objects"][0, 0] = 0
    monkeypatch.setattr(run, "plane_frame", _sag_frames({"a": 1.0}))
    assert run.native_pcl_sources([own], "study")["pcl"]["status"] == "unavailable"


@pytest.mark.parametrize(
    ("support", "row_change"),
    [("empty", None), ("missing", None), ("present", {"provenance": "laid"})],
)
def test_ineligible_primary_source_avoids_series_volume(support, row_change):
    own = _own(f"no-volume-{support}", count=0 if support == "empty" else 4)

    class VolumeMustNotBeRead:
        def __init__(self, row):
            self.row = row

        @property
        def volume(self):
            raise AssertionError("volume is unnecessary without native PCL support")

    own.series = VolumeMustNotBeRead(own.series.row)
    if support == "missing":
        own.arrays.pop("a1_objects")
    if row_change is not None:
        own.record["observations"] = [{**own.record["observations"][0], **row_change}]
    assert run.native_pcl_sources([own], "study")["pcl"]["status"] == "unavailable"


def _selected(points):
    return {
        "pcl": {
            "status": "selected",
            "selected": {
                "points_lps": np.asarray(points, float),
                "metadata": {"series_uid": "src"},
            },
        }
    }


def _fake_body(calls, status="identified", selection="identified", select=True):
    def body(raw, available, target, frame, *, thickness_mm, other_target=None):
        calls.append(
            {
                "shape": raw.shape,
                "thickness": thickness_mm,
                "target": target.copy(),
                "other_target": None if other_target is None else other_target.copy(),
            }
        )
        selected = np.zeros(raw.shape, bool)
        if select:
            selected[0, 0] = True
        return {
            "status": status,
            "selection_status": selection,
            "selected": selected,
            "availability": available.copy(),
        }

    return body


def _guide_map(slices):
    guide = SimpleNamespace(
        status="guided",
        slices=set(slices),
        half_px=(1.0, 1.0),
        placements=[{"status": "ok", "point_lps": np.asarray([4.0, 8.0, 6.0])}],
    )
    return SimpleNamespace(
        smap=SimpleNamespace(scale=SimpleNamespace(mm=1.0)),
        guide=lambda _name, _own: guide,
    )


def test_half_slab_profile_and_candidate_order(monkeypatch):
    monkeypatch.setattr(run, "plane_frame", _axial_frame)
    calls = []
    monkeypatch.setattr(run, "enclosed_body_at_sources", _fake_body(calls))
    own = _own("ax-order", AX)
    points = [[4, 8, 0], [5, 8, 0], [6, 8, 0], [4, 8, 6]]
    rows = run.name_native_pcl_sections(
        [own], _selected(points), "study", _guide_map({2})
    )
    arrays = own.arrays
    assert arrays["a4_axial_pcl_source_profile_count"].tolist() == [3, 0, 1, 0]
    assert arrays["a4_axial_pcl_source_profile_slab_count"].tolist() == [3, 0, 1, 0]
    assert arrays["a4_axial_pcl_source_profile_status"].tolist() == [4, 3, 4, 3]
    assert arrays["a4_axial_pcl_source_profile_map_count"][2] == 1
    assert own.record["a4_axial_pcl_profile"]["map_guided_first"] == [2]
    assert [c["slice"] for c in own.record["a4_axial_native_pcl_candidates"]] == [2, 0]
    assert [r.slices for r in rows[0][0]] == [(2,), (0,)]
    assert all(c["thickness"] == run.LIGAMENT_THICK_MM for c in calls)


def test_full_radius_window_reaches_the_far_corner(monkeypatch):
    monkeypatch.setattr(run, "plane_frame", _axial_frame)
    monkeypatch.setattr(run.anatomy_map, "target_span_mm", lambda *_a: (4.0, 4.0, 4.0))
    spans, calls = [], []
    real = run.source_window

    def capture(points, span, frame, shape):
        spans.append(tuple(span))
        return real(points, span, frame, shape)

    monkeypatch.setattr(run, "source_window", capture)
    monkeypatch.setattr(run, "enclosed_body_at_sources", _fake_body(calls))
    own = _own("ax-window", AX)
    run.name_native_pcl_sections([own], _selected([[4, 8, 0]]), "study", None)
    assert set(spans) == {
        (8.0, 8.0, 8.0)
    }  # twice the full anatomical extent passed as source_window's full-span argument
    window = own.record["a4_axial_native_pcl_candidates"][0]["window"]
    assert window["window_rc_exclusive"] == [2, 7, 0, 9]
    assert calls[0]["shape"] == (5, 9) and calls[0]["target"].sum() == 1
    assert own.arrays["a4_axial_pcl_z0_raw_crop"].shape == (5, 9)


@pytest.mark.parametrize(
    ("status", "selection", "select", "resolved"),
    [
        ("partial_reading", "identified", True, True),
        ("partial_reading", "measured_empty", False, False),
        ("tied_largest_components", "tied_largest_components", False, False),
        ("identified", "identified", True, True),
    ],
)
def test_partial_window_does_not_withdraw_an_identified_component(
    monkeypatch, status, selection, select, resolved
):
    monkeypatch.setattr(run, "plane_frame", _axial_frame)
    monkeypatch.setattr(
        run, "enclosed_body_at_sources", _fake_body([], status, selection, select)
    )
    own = _own(f"ax-{status}-{selection}", AX)
    here, missing = run.name_native_pcl_sections(
        [own], _selected([[4, 8, 0]]), "study", None
    )[0]
    assert any(r.kind == "resolved" for r in here) is resolved
    assert ("a4_axial_pcl_z0_support" in own.arrays) is select
    assert bool(missing) is (not resolved)


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ({"status": "tied"}, "source_tied"),
        ({"status": "unavailable"}, "source_unavailable"),
    ],
)
def test_unselected_source_is_a_named_refusal(source, code):
    own = _own("ax-refuse", AX)
    rows = run.name_native_pcl_sections([own], {"pcl": source}, "study", None)
    assert rows[0][0] == [] and [r.code for r in rows[0][1]] == [code]


def test_wrong_sequence_volume_and_extent_are_refused(monkeypatch):
    monkeypatch.setattr(run, "plane_frame", _axial_frame)
    monkeypatch.setattr(
        run,
        "native_meniscus_profiles",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("profile must be skipped")
        ),
    )
    sources = _selected([[4, 8, 0]])
    non_fs = _own("ax-nonfs", ("Axial", "1", "0"))
    assert [
        r.code for r in run.name_native_pcl_sections([non_fs], sources, "s", None)[0][1]
    ] == ["unsupported_target_sequence"]
    novol = _own("ax-novol", AX)
    novol.series.volume = None
    assert [
        r.code for r in run.name_native_pcl_sections([novol], sources, "s", None)[0][1]
    ] == ["native_volume_unavailable"]
    # non-axial series are not questioned at all
    sag = _own("sag-skip", SAG)
    assert run.name_native_pcl_sections([sag], sources, "s", None)[0] == ([], [])


def test_live_pcl_reference_span_and_valid_bootstrap_reach_axial_measurement(
    monkeypatch,
):
    monkeypatch.undo()
    monkeypatch.setattr(run, "reads", lambda *a, **k: None)
    monkeypatch.setattr(run, "handed", lambda *a, **k: None)
    monkeypatch.setattr(run, "artifact_of", lambda *_a: "art")
    monkeypatch.setattr(run, "finite_of", lambda s: np.ones(np.shape(s.volume), bool))
    monkeypatch.setattr(run, "margin_of", lambda *_a: np.zeros((16, 16), bool))

    sagittal = _sag_frames({"sag-bootstrap": 1.0})

    def frame(series, z):
        return (
            sagittal(series, z)
            if series.row.anatomical_plane == "Sagittal"
            else _axial_frame(series, z)
        )

    monkeypatch.setattr(run, "plane_frame", frame)
    calls = []
    monkeypatch.setattr(run, "enclosed_body_at_sources", _fake_body(calls))

    span = run.anatomy_map.target_span_mm("pcl", 92.69343800000001)
    assert span == pytest.approx(
        (27.429690846826812, 37.83405632908264, 42.06206256856812)
    )

    bootstrap = _own("sag-bootstrap", SAG)
    sources = run.native_pcl_sources([bootstrap], "study")
    assert sources["pcl"]["status"] == "selected"
    assert sources["pcl"]["selected"]["metadata"]["support"] == "a1_objects"
    assert sources["pcl"]["selected"]["metadata"]["kind"] == "resolved"

    def profiles(*_args, **_kwargs):
        return {
            "pcl": {
                "status": "measured",
                "counts": np.asarray([1.0]),
                "unique_counts": np.asarray([1.0]),
                "map_counts": np.asarray([0.0]),
                "statuses": np.asarray([4]),
                "guide": None,
                "per_slice": {0: {"unique_rc": np.asarray([[4.0, 8.0]])}},
            }
        }

    monkeypatch.setattr(run, "native_meniscus_profiles", profiles)
    own = _own("ax-live-reference", AX, z=0)
    mapping = _guide_map(set())
    mapping.smap.scale.mm = 92.69343800000001
    here, missing = run.name_native_pcl_sections([own], sources, "study", mapping)[0]
    assert here and not any(
        "anatomical_extent_unavailable" in row.code for row in missing
    )
    assert calls and calls[0]["thickness"] == run.LIGAMENT_THICK_MM
    assert own.record["a4_axial_native_pcl_candidates"][0]["status"] == "identified"


def test_missing_authored_extent_keeps_the_candidate_refusal(monkeypatch):
    monkeypatch.undo()
    monkeypatch.setattr(run, "reads", lambda *a, **k: None)
    monkeypatch.setattr(run, "handed", lambda *a, **k: None)
    monkeypatch.setattr(run, "artifact_of", lambda *_a: "art")
    monkeypatch.setattr(run, "plane_frame", _axial_frame)
    monkeypatch.setattr(run.anatomy_map, "target_span_mm", lambda *_a: None)
    own = _own("ax-noextent", AX)
    _, missing = run.name_native_pcl_sections([own], _selected([[4, 8, 0]]), "s", None)[
        0
    ]
    assert (
        missing[0].code == "candidate_readings_unresolved:anatomical_extent_unavailable"
    )


def test_native_row_reaches_the_same_map_as_an_axial_plane(monkeypatch):
    monkeypatch.setattr(run, "plane_frame", _axial_frame)
    monkeypatch.setattr(run, "enclosed_body_at_sources", _fake_body([]))
    own = _own("ax-map", AX)
    here, _ = run.name_native_pcl_sections(
        [own], _selected([[4, 8, 0]]), "study", None
    )[0]
    read_events = []
    monkeypatch.setattr(run, "reads", lambda *args: read_events.append(args))
    monkeypatch.setattr(
        run,
        "map_plane",
        lambda *_a: run.rel.KeyPlane(
            "pcl", "axial", "selected", "ax-map", 0, (0.0, 0.0, 1.0), 0.0, 1.0
        ),
    )
    context = run.MapContext(run.StudyMap(names=("pcl",)), None, None)
    product, rows, added = run.offer_native_family(
        context, [own], "axial_pcl_said", [(here, [])]
    )
    assert product == "axial_pcl_said.map_rows"
    assert rows and added == 1
    selected = context.smap.selected("pcl", "axial")
    assert selected.outcome == "selected" and selected.series_uid == "ax-map"
    assert ("axial_pcl_said", ("observations",), "map_rows") in read_events
    assert (
        "axial_pcl_said.map_rows",
        ("observations",),
        "refine_map",
    ) in read_events


def test_partial_pcl_reading_does_not_become_a_map_plane(monkeypatch):
    monkeypatch.setattr(run, "plane_frame", _axial_frame)
    monkeypatch.setattr(
        run,
        "enclosed_body_at_sources",
        _fake_body([], "partial_reading", "tied_largest_components", True),
    )
    own = _own("ax-partial-map", AX)
    own.record["observations"] = []
    here, missing = run.name_native_pcl_sections(
        [own], _selected([[4, 8, 0]]), "study", None
    )[0]
    assert here and all(row.kind == "reading" for row in here) and missing
    context = run.MapContext(run.StudyMap(names=("pcl",)), None, None)
    product, rows, added = run.offer_native_family(
        context, [own], "axial_pcl_said", [(here, missing)]
    )
    assert product == "axial_pcl_said.map_rows" and rows and added == 0
    assert context.smap.selected("pcl", "axial").outcome != "selected"


def _axial_source_row(own, z, pixels, *, kind="resolved", code="identified"):
    support_name = f"a4_axial_pcl_z{z}_support"
    support = np.zeros((16, 16), dtype=bool)
    for row, col in pixels:
        support[row, col] = True
    own.arrays[support_name] = support
    own.arrays[f"{support_name}_slices"] = np.asarray([z], dtype=np.int32)
    return {
        "object": "pcl",
        "provenance": "native",
        "kind": kind,
        "code": code,
        "series_uid": own.record["series_uid"],
        "view": tuple(own.record["view"]),
        "slices": (z,),
        "support": support_name,
        "row": None,
        "label": None,
        "count": int(support.sum()),
        "artifact": "art",
    }


def test_axial_source_uses_addressed_resolved_support_and_physical_area(monkeypatch):
    a, b = _own("ax-source-a", AX, fat="1"), _own("ax-source-b", AX, fat="1")
    rows_a = [_axial_source_row(a, 1, [(4, 5), (4, 6), (5, 5), (5, 6)])]
    rows_b = [_axial_source_row(b, 1, [(4, 5), (4, 6)])]

    def frame(series, z):
        spacing = 1.0 if series.row.series_uid == "ax-source-a" else 3.0
        basis = np.asarray([[0.0, spacing], [spacing, 0.0], [0.0, 0.0]])
        return run.PlaneFrame(
            np.asarray([0.0, 0.0, 3.0 * z]), basis, (spacing, spacing)
        )

    monkeypatch.setattr(run, "plane_frame", frame)
    selected = run.native_pcl_sources(
        [a, b],
        "study",
        orientation="axial",
        pending=[(rows_a, []), (rows_b, [])],
    )["pcl"]
    assert selected["status"] == "selected"
    assert selected["selected"]["owner"] is b
    assert len(selected["entries"]) == 2
    assert "a4_axial_pcl_z1_source_lps" in a.arrays
    assert "a4_axial_pcl_z1_source_lps" in b.arrays
    assert len(b.record["a4_axial_pcl_sources"]) == 1
    assert b.record["a4_axial_pcl_sources"][0]["support"] == "a4_axial_pcl_z1_support"


def test_axial_source_skips_volume_for_reading_rows():
    own = _own("ax-source-reading", AX, fat="1")

    class VolumeMustNotBeRead:
        def __init__(self, row):
            self.row = row

        @property
        def volume(self):
            raise AssertionError("a reading is not an eligible PCL source")

    own.series = VolumeMustNotBeRead(own.series.row)
    reading = _axial_source_row(
        own, 1, [(4, 5)], kind="reading", code="partial_reading"
    )
    result = run.native_pcl_sources(
        [own], "study", orientation="axial", pending=[([reading], [])]
    )["pcl"]
    assert result["status"] == "unavailable"
    assert result["entries"] == []


def test_axial_source_ranks_all_identified_supports_within_one_owner(monkeypatch):
    own = _own("ax-source-multiple", AX, fat="1", depth=4)
    first = _axial_source_row(own, 1, [(4, 5), (4, 6)])
    second = _axial_source_row(own, 2, [(4, 5), (4, 6), (5, 5), (5, 6)])
    monkeypatch.setattr(run, "plane_frame", _axial_frame)
    selected = run.native_pcl_sources(
        [own],
        "study",
        orientation="axial",
        pending=[([first, second], [])],
    )["pcl"]
    assert selected["status"] == "selected"
    assert selected["selected"]["metadata"]["slice"] == 2
    assert [entry["slice"] for entry in selected["entries"]] == [1, 2]
    assert len(own.record["a4_axial_pcl_sources"]) == 2


def test_axial_source_equal_largest_supports_stay_tied_within_one_owner(monkeypatch):
    own = _own("ax-source-tie", AX, fat="1", depth=4)
    first = _axial_source_row(own, 1, [(4, 5), (4, 6)])
    second = _axial_source_row(own, 2, [(4, 5), (4, 6)])
    monkeypatch.setattr(run, "plane_frame", _axial_frame)
    selected = run.native_pcl_sources(
        [own],
        "study",
        orientation="axial",
        pending=[([first, second], [])],
    )["pcl"]
    assert selected["status"] == "tied"
    assert selected["selected"] is None
    assert len(selected["entries"]) == 2


def test_axial_source_rejects_boolean_label_field(monkeypatch):
    own = _own("ax-source-bool-label", AX, fat="1")
    row = _axial_source_row(own, 1, [(4, 5), (4, 6)])
    row["label"] = LABEL
    monkeypatch.setattr(run, "plane_frame", _axial_frame)
    selected = run.native_pcl_sources(
        [own], "study", orientation="axial", pending=[([row], [])]
    )["pcl"]
    assert selected["status"] == "unavailable"
    assert selected["entries"] == []


def test_axial_source_skips_volume_when_series_row_is_not_fs(monkeypatch):
    own = _own("ax-source-wrong-row-tags", AX, fluid="0", fat="1")
    observation = _axial_source_row(own, 1, [(4, 5), (4, 6)])

    class VolumeMustNotBeRead:
        def __init__(self, row):
            self.row = row

        @property
        def volume(self):
            raise AssertionError("inconsistent source tags are not eligible")

    own.series = VolumeMustNotBeRead(own.series.row)
    monkeypatch.setattr(run, "plane_frame", _axial_frame)
    selected = run.native_pcl_sources(
        [own], "study", orientation="axial", pending=[([observation], [])]
    )["pcl"]
    assert selected["status"] == "unavailable"
    assert selected["entries"] == []


@pytest.mark.parametrize(
    ("primary_status", "secondary_status", "expected"),
    [
        ("tied", "selected", "source_tied"),
        ("selected", "tied", "other_source_tied"),
        ("selected", "unavailable", "other_source_unavailable"),
    ],
)
def test_coronal_sources_are_required_before_target_volume(
    primary_status, secondary_status, expected
):
    own = _own("cor-source-prerequisite", COR)

    class VolumeMustNotBeRead:
        @property
        def volume(self):
            raise AssertionError("coronal target cannot be read without both sources")

    own.series = VolumeMustNotBeRead()
    primary = {"pcl": {"status": primary_status}}
    secondary = {"pcl": {"status": secondary_status}}
    rows = run.name_native_pcl_sections(
        [own], primary, "study", None, orientation="coronal", other_sources=secondary
    )
    assert rows[0][0] == []
    assert [row.code for row in rows[0][1]] == [expected]


def _source_profile(counts, unique_counts, map_counts, per_slice, guide=None):
    return {
        "status": "measured",
        "counts": np.asarray(counts, dtype=float),
        "unique_counts": np.asarray(unique_counts, dtype=float),
        "map_counts": np.asarray(map_counts, dtype=float),
        "statuses": np.full(len(counts), 4, dtype=np.int8),
        "guide": guide,
        "per_slice": per_slice,
    }


def test_coronal_profiles_keep_sagittal_and_axial_namespaces(monkeypatch):
    own = _own("cor-profile-prefix", COR)
    monkeypatch.setattr(run, "plane_frame", _axial_frame)
    source = _selected([[4, 8, 0]])
    run.native_meniscus_profiles(
        own,
        source,
        None,
        orientation="coronal",
        source_tag="sagittal",
        names=("pcl",),
        sources_product="native_pcl_sources",
    )
    run.native_meniscus_profiles(
        own,
        source,
        None,
        orientation="coronal",
        source_tag="axial",
        names=("pcl",),
        sources_product="native_axial_pcl_sources",
    )
    assert "a4_coronal_pcl_sagittal_source_profile_unique_rc" in own.arrays
    assert "a4_coronal_pcl_axial_source_profile_unique_rc" in own.arrays
    assert "a4_axial_pcl_sagittal_source_profile_unique_rc" not in own.arrays


def test_coronal_uses_both_profiles_and_keeps_each_candidate_failure(monkeypatch):
    monkeypatch.setattr(run, "plane_frame", _axial_frame)
    calls = []
    monkeypatch.setattr(run, "enclosed_body_at_sources", _fake_body(calls))
    own = _own("cor-both-profiles", COR)
    guided = _guide_map({2}).guide("pcl", own)
    rc = np.asarray([[4.0, 8.0]])
    other_rc = np.asarray([[6.0, 8.0]])
    primary = _source_profile(
        [0, 5, 0, 0],
        [0, 2, 0, 0],
        [0, 0, 9, 0],
        {1: {"unique_rc": rc}, 2: {"unique_rc": rc}, 3: {"unique_rc": rc}},
        guided,
    )
    secondary = _source_profile(
        [0, 0, 0, 7],
        [0, 0, 0, 3],
        [0, 0, 0, 0],
        {1: {"unique_rc": other_rc}, 3: {"unique_rc": other_rc}},
    )

    def profiles(_own, _sources, _mapping, **kwargs):
        return {"pcl": secondary if kwargs["source_tag"] == "axial" else primary}

    monkeypatch.setattr(run, "native_meniscus_profiles", profiles)
    primary_sources = _selected([[4, 8, 0]])
    secondary_sources = _selected([[6, 8, 0]])
    rows = run.name_native_pcl_sections(
        [own],
        primary_sources,
        "study",
        _guide_map({2}),
        orientation="coronal",
        other_sources=secondary_sources,
    )
    here, missing = rows[0]
    candidates = own.record["a4_coronal_native_pcl_candidates"]
    assert [item["slice"] for item in candidates] == [2, 1, 3]
    assert candidates[0]["status"] == "other_source_not_in_slab"
    assert [item.slices for item in here] == [(1,), (3,)]
    assert len(missing) == 1 and "other_source_not_in_slab" in missing[0].code
    assert len(calls) == 2
    assert all(call["other_target"] is not None for call in calls)
    assert all(
        call["target"].sum() > 0 and call["other_target"].sum() > 0 for call in calls
    )
    assert "a4_coronal_pcl_z1_other_target_crop" in own.arrays
    assert "a4_coronal_pcl_z3_other_target_crop" in own.arrays
    assert "a4_coronal_pcl_z2_raw_crop" not in own.arrays


@pytest.mark.parametrize(
    ("mode", "status", "selection"),
    [
        ("one", "identified", "identified"),
        ("two", "tied_largest_components", "tied_largest_components"),
        ("empty", "measured_empty", "measured_empty"),
        ("partial", "partial_reading", "identified"),
    ],
)
def test_shared_selector_requires_both_targets_and_preserves_window_status(
    mode, status, selection
):
    own = _own(f"cor-selector-{mode}", COR)
    raw = np.full((21, 31), 100.0)
    if mode == "two":
        raw[3:18, 3:12] = 20.0
        raw[3:18, 14:23] = 20.0
        raw[5:12, 4:11] = 0.0
        raw[5:12, 15:22] = 0.0
        target_rc = (8, 12)
    else:
        raw[3:18, 3:28] = 20.0
        raw[5:12, 4:27] = 0.0
        target_rc = (8, 7) if mode != "empty" else (1, 1)
    target = np.zeros(raw.shape, dtype=bool)
    other_target = np.zeros(raw.shape, dtype=bool)
    target[target_rc] = True
    other_target[target_rc] = True
    if mode == "two":
        target[8, 13] = True
        other_target[8, 13] = True
    available = np.ones(raw.shape, dtype=bool)
    if mode == "partial":
        available[0, 0] = False
    frame = (
        run.PlaneFrame(
            np.zeros(3),
            np.asarray([[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]]),
            (1.0, 1.0),
        )
        if mode == "two"
        else _axial_frame(own.series, 0)
    )
    result = run.enclosed_body_at_sources(
        raw,
        available,
        target,
        frame,
        thickness_mm=run.LIGAMENT_THICK_MM,
        other_target=other_target,
    )
    assert result["status"] == status
    assert result["selection_status"] == selection
    assert result["target_contacted_component_count"] is not None
    assert result["other_contacted_component_count"] is not None
    assert (
        result["both_contacted_component_count"] == result["contacted_component_count"]
    )


def test_coronal_native_observation_reaches_the_common_map(monkeypatch):
    monkeypatch.setattr(run, "plane_frame", _axial_frame)
    monkeypatch.setattr(run, "enclosed_body_at_sources", _fake_body([]))
    own = _own("cor-map", COR)
    rc = np.asarray([[4.0, 8.0]])
    profile = _source_profile([1], [1], [0], {0: {"unique_rc": rc}}, None)
    monkeypatch.setattr(
        run,
        "native_meniscus_profiles",
        lambda *_a, **kwargs: {"pcl": profile},
    )
    sources = _selected([[4, 8, 0]])
    here, _ = run.name_native_pcl_sections(
        [own],
        sources,
        "study",
        None,
        orientation="coronal",
        other_sources=sources,
    )[0]
    assert here and here[0].kind == "resolved"
    monkeypatch.setattr(
        run,
        "map_plane",
        lambda *_a: run.rel.KeyPlane(
            "pcl", "coronal", "selected", "cor-map", 0, (0.0, 0.0, 1.0), 0.0, 1.0
        ),
    )
    context = run.MapContext(run.StudyMap(names=("pcl",)), None, None)
    product, rows, added = run.offer_native_family(
        context, [own], "coronal_pcl_said", [(here, [])]
    )
    assert product == "coronal_pcl_said.map_rows"
    assert rows and added == 1
    assert context.smap.selected("pcl", "coronal").outcome == "selected"
