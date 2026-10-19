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


def test_mcl_sources_require_exact_native_address_and_keep_invalid_context_named(
    monkeypatch,
):
    _quiet(monkeypatch)
    monkeypatch.setattr(run, "artifact_of", lambda *_args: "native-artifact")
    monkeypatch.setattr(run, "plane_frame", _frame)
    own = _own(pixels=np.zeros((16, 16), dtype=np.uint8))
    own.arrays["a1_objects"][2, 3] = run.OBJECT_CODES["mcl"]
    own.record["observations"] = [_row(own, object_name="mcl")]
    options = {
        "orientation": "coronal",
        "names": ("mcl",),
        "object_codes": {"mcl": run.OBJECT_CODES["mcl"]},
        "sources_product": "native_coronal_mcl_sources",
        "record_key": "a4_native_coronal_mcl_sources",
        "strict_native_address": True,
    }

    accepted = run.native_meniscus_sources([own], "study", **options)["mcl"]

    assert accepted["status"] == "selected"
    assert accepted["selected"]["metadata"]["support"] == "a1_objects"
    fractional = _own(pixels=np.zeros((16, 16), dtype=np.uint8))
    fractional.arrays["a1_objects"][2, 3] = run.OBJECT_CODES["mcl"]
    fractional.record["observations"] = [
        {**_row(fractional, object_name="mcl"), "slices": (1.0,)}
    ]
    rejected = run.native_meniscus_sources([fractional], "study", **options)["mcl"]
    assert rejected["status"] == "invalid_source_context"
    assert rejected["invalid_sources"] == [{"status": "invalid_slice_address"}]
    laid = _own(pixels=np.zeros((16, 16), dtype=np.uint8))
    laid.record["observations"] = [
        {**_row(laid, object_name="mcl"), "provenance": "laid"}
    ]
    laid_source = run.native_meniscus_sources([laid], "study", **options)["mcl"]
    assert laid_source["status"] == "unavailable"


@pytest.mark.parametrize(
    "defect", ["actual_acquisition", "float_label", "scalar_slice"]
)
def test_mcl_source_checks_the_actual_acquisition_and_typed_address(
    monkeypatch, defect
):
    _quiet(monkeypatch)
    monkeypatch.setattr(run, "artifact_of", lambda *_args: "native-artifact")
    monkeypatch.setattr(run, "plane_frame", _frame)
    own = _own(pixels=np.zeros((16, 16), dtype=np.uint8))
    own.arrays["a1_objects"][2, 3] = run.OBJECT_CODES["mcl"]
    row = _row(own, object_name="mcl")
    own.record["observations"] = [row]
    if defect == "actual_acquisition":
        own.record["series_uid"] = "tampered"
        row["series_uid"] = "tampered"
    elif defect == "float_label":
        row["label"] = float(run.OBJECT_CODES["mcl"])
    else:
        row["slices"] = 1
    result = run.native_meniscus_sources(
        [own],
        "study",
        names=("mcl",),
        object_codes={"mcl": run.OBJECT_CODES["mcl"]},
        sources_product="native_coronal_mcl_sources",
        strict_native_address=True,
    )["mcl"]
    assert result["status"] == "invalid_source_context"
    assert result["selected"] is None


def test_native_bone_supports_require_same_series_slice_and_exact_array_address(
    monkeypatch,
):
    _quiet(monkeypatch)
    monkeypatch.setattr(run, "artifact_of", lambda *_args: "native-artifact")
    own = _own(view=("Axial", "1", "1"), z=1)
    own.arrays["a1_objects"][2, 3] = run.OBJECT_CODES["femur"]
    own.record["observations"] = [
        {
            **_row(own, object_name="femur"),
            "count": 1,
            "artifact": "native-artifact",
        }
    ]
    a1 = run.native_axial_bone_supports(own, "study", 1, (1, 5, 1, 5))
    assert a1["femur"]["status"] == "resolved_native_support"
    assert a1["femur"]["mask"].sum() == 1
    assert a1["femur"]["metadata"]["addresses"][0]["slice"] == 1
    assert a1["tibia"]["status"] == "unknown_native_support_unavailable"

    own.record["observations"] = [
        {
            "object": "tibia",
            "provenance": "native",
            "kind": "resolved",
            "code": "identified",
            "series_uid": own.record["series_uid"],
            "view": tuple(own.record["view"]),
            "slices": (2,),
            "support": "a3_tibia_plane_region",
            "row": 0,
            "label": None,
            "count": 2,
            "artifact": "native-artifact",
        }
    ]
    regions = np.zeros((1, 16, 16), dtype=bool)
    regions[0, 3, 3:5] = True
    own.arrays["a3_tibia_plane_region"] = regions
    own.arrays["a3_tibia_plane_slices"] = np.asarray([2], dtype=np.int32)
    a3 = run.native_axial_bone_supports(own, "study", 2, (1, 5, 1, 5))
    assert a3["tibia"]["status"] == "resolved_native_support"
    assert a3["tibia"]["mask"].sum() == 2
    own.record["observations"][0]["row"] = 0.0
    malformed = run.native_axial_bone_supports(own, "study", 2, (1, 5, 1, 5))
    assert malformed["tibia"]["status"] == "unknown_invalid_native_support_context"


def test_native_bone_supports_or_independent_addresses_and_retain_malformed_rows(
    monkeypatch,
):
    _quiet(monkeypatch)
    monkeypatch.setattr(run, "artifact_of", lambda *_args: "native-artifact")
    own = _own(view=("Axial", "1", "1"), z=1)
    own.arrays["a1_objects"][2, 3] = run.OBJECT_CODES["femur"]
    valid_a1 = {
        **_row(own, object_name="femur"),
        "count": 1,
        "artifact": "native-artifact",
    }
    malformed = {**valid_a1, "slices": (1.5,)}
    own.record["observations"] = [valid_a1, malformed]
    own.arrays["a3_femur_plane_region"] = np.zeros((1, 16, 16), dtype=bool)
    own.arrays["a3_femur_plane_region"][0, 3, 4] = True
    own.arrays["a3_femur_plane_slices"] = np.asarray([1], dtype=np.int32)
    own.record["observations"].append(
        {
            **valid_a1,
            "support": "a3_femur_plane_region",
            "row": 0,
            "label": None,
        }
    )
    combined = run.native_axial_bone_supports(own, "study", 1, (1, 5, 1, 5))
    assert combined["femur"]["status"] == "resolved_native_support"
    assert combined["femur"]["mask"].sum() == 2
    metadata = combined["femur"]["metadata"]
    assert [address["support"] for address in metadata["addresses"]] == [
        "a1_objects",
        "a3_femur_plane_region",
    ]
    assert metadata["malformed_reasons"] == ["invalid_slice_type"]


def test_native_bone_supports_validate_actual_series_uid_and_strict_label(
    monkeypatch,
):
    _quiet(monkeypatch)
    monkeypatch.setattr(run, "artifact_of", lambda *_args: "native-artifact")
    own = _own(view=("Axial", "1", "1"), z=1)
    own.arrays["a1_objects"][2, 3] = run.OBJECT_CODES["femur"]
    row = {
        **_row(own, object_name="femur"),
        "count": 1,
        "artifact": "native-artifact",
    }
    own.record["observations"] = [row]
    own.record["series_uid"] = "tampered-record-uid"
    mismatched = run.native_axial_bone_supports(own, "study", 1, (1, 5, 1, 5))
    assert mismatched["femur"]["status"] == "unknown_invalid_acquisition_or_slice"

    own.record["series_uid"] = own.series.row.series_uid
    row["series_uid"] = own.series.row.series_uid
    row["label"] = float(run.OBJECT_CODES["femur"])
    invalid_label = run.native_axial_bone_supports(own, "study", 1, (1, 5, 1, 5))
    assert invalid_label["femur"]["status"] == "unknown_invalid_native_support_context"


@pytest.mark.parametrize(
    ("bone_overlap", "expected_status", "expected_observation_kind"),
    [
        (False, "identified", "resolved"),
        (True, "candidate_merged_with_resolved_bone", None),
    ],
)
def test_shared_ligament_adapter_runs_axial_mcl_measurement_and_conflict_branch(
    monkeypatch, bone_overlap, expected_status, expected_observation_kind
):
    _quiet(monkeypatch)
    own = _own(view=("Axial", "1", "1"), volume=np.ones((4, 16, 16)))
    own.record["series_uid"] = f"axial-mcl-{bone_overlap}"
    source = {
        "status": "selected",
        "selected": {
            "points_lps": np.asarray([[0.0, 0.0, 0.0]]),
            "metadata": {"series_uid": "coronal-mcl", "slice": 5},
        },
    }
    profile = {
        "status": "measured",
        "counts": np.asarray([0.0, 0.0, 2.0, 0.0]),
        "unique_counts": np.asarray([0.0, 0.0, 2.0, 0.0]),
        "map_counts": np.zeros(4),
        "statuses": np.asarray([0, 0, 4, 0], dtype=np.int8),
        "per_slice": {
            2: {
                "unique_rc": np.asarray([[4.0, 4.0], [4.0, 5.0]]),
                "sample_rc": np.asarray([[4.0, 4.0], [4.0, 5.0]]),
                "in_map": np.zeros(2, dtype=bool),
            }
        },
        "guide": None,
        "product": "native_axial_mcl_profiles",
        "source_product": "native_coronal_mcl_sources",
    }
    monkeypatch.setattr(
        run, "native_meniscus_profiles", lambda *_a, **_k: {"mcl": profile}
    )
    monkeypatch.setattr(run, "plane_frame", _frame)
    monkeypatch.setattr(
        run, "finite_of", lambda _series: np.ones((4, 16, 16), dtype=bool)
    )
    monkeypatch.setattr(run, "margin_of", lambda *_args: np.zeros((16, 16), dtype=bool))
    monkeypatch.setattr(
        run.anatomy_map, "target_span_mm", lambda *_args: (4.0, 4.0, 4.0)
    )
    monkeypatch.setattr(run, "_peak_slices", lambda _values: [2])
    monkeypatch.setattr(run, "once", lambda _name, _key, make: make())

    def bone_supports(_own, _study, _z, window):
        r0, r1, c0, c1 = window
        mask = np.zeros((r1 - r0, c1 - c0), dtype=bool)
        if bone_overlap:
            mask[3, 3] = True
        return {
            "femur": {
                "status": "resolved_native_support",
                "mask": mask,
                "metadata": {"support": "a3_femur_plane_region", "slice": 2},
            },
            "tibia": {"status": "unknown_native_support_unavailable"},
        }

    monkeypatch.setattr(run, "native_axial_bone_supports", bone_supports)
    calls = []

    def components(raw, available, target, frame):
        calls.append((raw.shape, target.copy()))
        labels = np.zeros(raw.shape, dtype=np.int32)
        labels[3, 3:5] = 1
        return {
            "status": "complete",
            "partial_reading": False,
            "labels": labels,
            "distance_to_target_mm": np.zeros(raw.shape),
            "target_pixels": int(target.sum()),
            "available_target_pixels": int(target.sum()),
            "components": [
                {
                    "label": 1,
                    "pixels": 2,
                    "minimum_target_distance_mm": 0.0,
                    "within_existing_contact_shell": True,
                    "crop_edge_pixels": 0,
                    "touches_crop_edge": False,
                    "touches_unavailable_boundary": False,
                }
            ],
            "positive_enclosure": labels.astype(bool),
            "enclosed_depth": labels.astype(float),
        }

    monkeypatch.setattr(run, "enclosed_components_at_source", components)
    monkeypatch.setattr(run, "artifact_of", lambda *_args: "axial-artifact")

    rows = run.name_native_ligament_sections(
        [own], {"mcl": source}, "study", None, orientation="axial", ligament="mcl"
    )

    assert len(calls) == 1
    if expected_observation_kind:
        assert rows[0][0][0].kind == expected_observation_kind
        assert rows[0][0][0].code == "identified"
    else:
        assert not rows[0][0]
    candidate = own.record["a4_axial_native_mcl_candidates"][0]
    assert candidate["status"] == expected_status
    assert "a4_axial_mcl_z2_raw_crop" in own.arrays
    assert "a4_axial_mcl_z2_positive_enclosure" in own.arrays
    if not expected_observation_kind:
        assert any(
            reason.code == "local_body_unavailable:candidate_merged_with_resolved_bone"
            for reason in rows[0][1]
        )


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
