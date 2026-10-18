from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest

from knee.collapse.physical import PlaneFrame
from scripts import run_interiors as run

STUDY = "axial-joint-study"
UID = "axial-joint-series"
SUPPORT = "a4_joint_axial_compartment"


@pytest.fixture
def production_stubs(monkeypatch: pytest.MonkeyPatch) -> None:
    def frame_for(_series: Any, z: int) -> PlaneFrame:
        return PlaneFrame(
            np.asarray([0.0, 0.0, float(z)]),
            np.asarray([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]),
            (1.0, 1.0),
        )

    monkeypatch.setattr(run, "plane_frame", frame_for)
    monkeypatch.setattr(
        run,
        "finite_of",
        lambda series: np.isfinite(np.asarray(series.volume)),
    )
    monkeypatch.setattr(
        run,
        "margin_of",
        lambda _uid, _z, plane: np.zeros(np.shape(plane), dtype=bool),
    )
    monkeypatch.setattr(run, "artifact_of", lambda study, _record: f"{study}/{UID}.npz")
    monkeypatch.setattr(run, "reads", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(run, "handed", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        run, "ledger", SimpleNamespace(record=lambda *_args, **_kwargs: None)
    )


def measured(
    volume: np.ndarray,
    *,
    view: tuple[str, str, str] = ("Axial", "1", "1"),
    level: tuple[float | None, float | None] | None = (10.0, 20.0),
    thickness: tuple[Any, ...] | None = None,
) -> run.Measured:
    if thickness is None:
        thickness = (0.8,) * len(volume)
    series = SimpleNamespace(
        row=SimpleNamespace(
            series_uid=UID,
            fat_suppression=1,
            fluid_sensitive=1,
        ),
        volume=volume,
        slice_thickness_mm=thickness,
        geometry=object(),
    )
    record: dict[str, Any] = {
        "series_uid": UID,
        "view": view,
        "slice_index": len(volume) // 2,
        "recess": {"level": level},
    }
    return cast(
        run.Measured,
        SimpleNamespace(
            series=series,
            record=record,
            arrays={"acquired_plane": np.zeros(volume.shape[1:], dtype=np.float32)},
            frame=None,
        ),
    )


def lps_points(*rcz: tuple[int, int, float]) -> np.ndarray:
    return np.asarray([[float(r), float(c), z] for r, c, z in rcz], dtype=float)


def selected_sources(
    sagittal: np.ndarray | None = None,
    coronal: np.ndarray | None = None,
) -> dict[str, dict[str, Any]]:
    if sagittal is None:
        sagittal = lps_points((3, 3, 2.0))
    if coronal is None:
        coronal = lps_points((3, 8, 2.0))
    return {
        "sagittal": {
            "status": "selected",
            "points": sagittal,
            "metadata": {
                "series_uid": "sagittal-native-source",
                "slice": 12,
                "code": "identified",
                "count": len(sagittal),
                "support": "a1_objects",
                "row": None,
                "artifact": f"{STUDY}/sagittal-native-source.npz",
            },
            "detail": {"status": "selected"},
        },
        "coronal": {
            "status": "selected",
            "points": coronal,
            "metadata": {
                "series_uid": "coronal-native-source",
                "slice": 9,
                "code": "identified",
                "count": len(coronal),
                "support": "a1_objects",
                "row": None,
                "artifact": f"{STUDY}/coronal-native-source.npz",
            },
            "detail": {"status": "selected"},
        },
    }


def connected_native_body(depth: int = 5) -> np.ndarray:
    volume = np.zeros((depth, 12, 12), dtype=np.float32)
    volume[2, 3, 3:9] = 20.0
    return volume


def mapping_for(
    *,
    slices: tuple[int, ...] = (2,),
    point_lps: tuple[float, float, float] = (3.0, 3.0, 2.0),
    half_px: tuple[float, float] = (0.0, 0.0),
    outcome_rows: list[dict[str, Any]] | None = None,
) -> run.MapContext:
    if outcome_rows is None:
        outcome_rows = []
    guide = SimpleNamespace(
        status="guided",
        slices=slices,
        placements=[{"status": "ok", "point_lps": point_lps}],
        anchors=["femur", "tibia"],
        half_px=half_px,
    )
    return cast(
        run.MapContext,
        SimpleNamespace(
            guide=lambda _name, _own: guide,
            smap=SimpleNamespace(
                note_use=lambda *args, **kwargs: outcome_rows.append(
                    {"args": args, "kwargs": kwargs}
                )
            ),
        ),
    )


def test_native_white_component_must_touch_both_sources_and_saves_exact_support(
    production_stubs: None,
) -> None:
    own = measured(connected_native_body())

    observations, missing = run.axial_joint_compartment(
        own, selected_sources(), STUDY, None
    )

    assert missing == []
    assert len(observations) == 1
    observation = observations[0]
    assert observation.object == "joint"
    assert observation.kind == "resolved"
    assert observation.provenance == "native"
    assert observation.slices == (2,)
    assert observation.code == "identified"
    assert observation.support == SUPPORT
    assert observation.artifact == f"{STUDY}/{UID}.npz"
    assert observation.row == 0
    native = own.arrays[SUPPORT]
    assert native.dtype == np.bool_
    assert native.shape == (1, 12, 12)
    assert int(native[observation.row].sum()) == observation.count == 6
    expected = np.zeros((12, 12), dtype=bool)
    expected[3, 3:9] = True
    np.testing.assert_array_equal(native[observation.row], expected)
    assert own.arrays["a4_joint_axial_slices"].tolist() == [2]


def test_two_separate_one_sided_components_do_not_satisfy_source_concurrence(
    production_stubs: None,
) -> None:
    volume = np.zeros((5, 12, 12), dtype=np.float32)
    volume[2, 3, 3] = 20.0
    volume[2, 3, 8] = 20.0
    own = measured(volume)

    observations, missing = run.axial_joint_compartment(
        own, selected_sources(), STUDY, None
    )

    assert len(observations) == 1
    assert observations[0].kind == "reading"
    assert observations[0].count == 0
    assert observations[0].code == "abstain_no_white_body_touches_both_sources"
    assert missing == []
    assert not own.arrays[SUPPORT].any()


def test_unique_largest_concurrent_body_is_selected_and_tied_largest_abstains(
    production_stubs: None,
) -> None:
    points = lps_points((2, 2, 2.0), (9, 9, 2.0))
    sources = selected_sources(points, points)
    volume = np.zeros((5, 12, 12), dtype=np.float32)
    volume[2, 2, 2:4] = 20.0
    volume[2, 9, 9:12] = 20.0
    own = measured(volume)

    observations, missing = run.axial_joint_compartment(own, sources, STUDY, None)

    assert missing == []
    assert observations[0].kind == "resolved"
    assert observations[0].count == 3
    assert own.arrays[SUPPORT][0, 9, 9:12].all()
    assert not own.arrays[SUPPORT][0, 2, 2:4].any()

    tied_volume = np.zeros((5, 12, 12), dtype=np.float32)
    tied_volume[2, 2, 2:4] = 20.0
    tied_volume[2, 9, 9:11] = 20.0
    tied = measured(tied_volume)
    tied_observations, tied_missing = run.axial_joint_compartment(
        tied, sources, STUDY, None
    )

    assert tied_observations == []
    assert len(tied_missing) == 1
    assert tied_missing[0].code.startswith(
        "axial_joint_compartment:tied_largest_native_white_bodies_at_slice_"
    )
    tied_detail = tied.record["axial_joint_compartment"]["pointed_planes"][0]
    assert tied_detail["code"] == "abstain_tied_largest_bodies"
    assert not tied.arrays[SUPPORT].any()
    assert tied.arrays["a4_joint_axial_sizes_2"].tolist() == [2, 2]


@pytest.mark.parametrize(
    "bad_points",
    [
        np.empty((0, 3), dtype=float),
        np.asarray([1.0, 2.0, 3.0]),
        np.asarray([[1.0, 2.0, np.nan]]),
    ],
)
def test_empty_or_malformed_native_source_is_named_unknown(
    production_stubs: None,
    bad_points: np.ndarray,
) -> None:
    sources = selected_sources()
    sources["sagittal"]["points"] = bad_points
    own = measured(connected_native_body())

    observations, missing = run.axial_joint_compartment(own, sources, STUDY, None)

    assert observations == []
    assert len(missing) == 1
    assert missing[0].code.startswith("axial_joint_compartment:")
    assert "sagittal" in missing[0].code
    assert "axial_joint_compartment" in own.record
    assert "identified" not in own.record["axial_joint_compartment"].get("code", "")


@pytest.mark.parametrize(
    "bad_thickness",
    [None, 0.0, -0.8, float("nan"), "unreadable"],
)
def test_missing_or_invalid_actual_slice_thickness_is_named_unknown(
    production_stubs: None,
    bad_thickness: Any,
) -> None:
    thickness = (0.8, 0.8, bad_thickness, 0.8, 0.8)
    own = measured(connected_native_body(), thickness=thickness)

    observations, missing = run.axial_joint_compartment(
        own, selected_sources(), STUDY, None
    )

    assert observations == []
    assert len(missing) == 1
    assert missing[0].code.startswith("axial_joint_compartment:")
    assert "thickness" in missing[0].code


def test_measured_empty_is_reading_but_unavailable_samples_are_unknown(
    monkeypatch: pytest.MonkeyPatch,
    production_stubs: None,
) -> None:
    empty = measured(np.zeros((5, 12, 12), dtype=np.float32))
    empty_observations, empty_missing = run.axial_joint_compartment(
        empty, selected_sources(), STUDY, None
    )

    assert empty_missing == []
    assert len(empty_observations) == 1
    assert empty_observations[0].kind == "reading"
    assert empty_observations[0].count == 0
    assert empty_observations[0].code == "abstain_no_white_sample_at_source_locations"
    empty_observation = empty_observations[0]
    assert empty_observation.support == "a4_joint_axial_profile_white"
    assert empty_observation.row is not None
    profile_row = empty_observation.row
    profile_slices = empty.arrays["a4_joint_axial_profile_slices"]
    offsets = empty.arrays["a4_joint_axial_profile_offsets"]
    assert int(profile_slices[profile_row]) == empty_observation.slices[0]
    start = int(offsets[profile_row])
    stop = int(offsets[profile_row + 1])
    sparse_white = empty.arrays["a4_joint_axial_profile_white"][start:stop]
    assert sparse_white.dtype == np.bool_
    assert int(np.count_nonzero(sparse_white)) == empty_observation.count == 0
    assert empty.arrays["a4_joint_axial_compartment"].shape == (0, 12, 12)

    unavailable = measured(connected_native_body())
    monkeypatch.setattr(
        run,
        "finite_of",
        lambda series: np.zeros(np.shape(series.volume), dtype=bool),
    )
    unknown_observations, unknown_missing = run.axial_joint_compartment(
        unavailable, selected_sources(), STUDY, None
    )

    assert unknown_observations == []
    assert unknown_missing
    assert all(
        item.code.startswith("axial_joint_compartment:") for item in unknown_missing
    )
    assert all(item.kind != "reading" for item in unknown_observations)


def test_excluded_partial_source_sample_is_invariant_to_stored_intensity(
    monkeypatch: pytest.MonkeyPatch,
    production_stubs: None,
) -> None:
    complete = measured(connected_native_body())
    complete_observations, _ = run.axial_joint_compartment(
        complete, selected_sources(), STUDY, None
    )
    assert complete_observations[0].kind == "resolved"

    partial = measured(connected_native_body())
    valid = np.ones_like(partial.series.volume, dtype=bool)
    valid[2, 3, 8] = False
    monkeypatch.setattr(run, "finite_of", lambda _series: valid)
    partial_observations, partial_missing = run.axial_joint_compartment(
        partial, selected_sources(), STUDY, None
    )

    assert len(partial_observations) == 1
    assert partial_observations[0].kind == "reading"
    assert partial_observations[0].code == "abstain_no_white_body_at_coronal_target"
    assert partial_missing == []
    assert partial.arrays["a4_joint_axial_profile_count"][2] == 1
    assert partial.arrays["a4_joint_axial_profile_status"][2] == 6
    assert partial.arrays["a4_joint_axial_profile_coronal_valid_count"][2] == 0
    assert partial.arrays["a4_joint_axial_profile_sagittal_white_count"][2] == 1

    changed_volume = connected_native_body()
    changed_volume[2, 3, 8] = 1_000_000.0
    changed = measured(changed_volume)
    changed_observations, changed_missing = run.axial_joint_compartment(
        changed, selected_sources(), STUDY, None
    )
    assert changed_missing == partial_missing
    assert changed_observations == partial_observations
    for key in (
        "a4_joint_axial_profile_count",
        "a4_joint_axial_profile_status",
        "a4_joint_axial_profile_white",
        "a4_joint_axial_compartment",
    ):
        np.testing.assert_array_equal(changed.arrays[key], partial.arrays[key])


def test_guide_depth_and_inplane_box_are_separate_and_miss_broadens(
    production_stubs: None,
) -> None:
    guided = measured(connected_native_body())
    guided_map = mapping_for(point_lps=(3.0, 3.0, 2.0))

    observations, missing = run.axial_joint_compartment(
        guided, selected_sources(), STUDY, guided_map
    )

    assert missing == []
    assert observations[0].kind == "resolved"
    assert guided.arrays["a4_joint_axial_profile_map_count"][2] > 0
    assert guided.record["axial_joint_compartment"]["search"] == "guided_hit"

    outside = measured(connected_native_body())
    uses: list[dict[str, Any]] = []
    outside_map = mapping_for(point_lps=(10.0, 10.0, 2.0), outcome_rows=uses)
    outside_observations, outside_missing = run.axial_joint_compartment(
        outside,
        selected_sources(
            lps_points((1, 1, 2.0)),
            lps_points((1, 10, 2.0)),
        ),
        STUDY,
        outside_map,
    )

    assert not any(item.kind == "resolved" for item in outside_observations)
    assert outside_missing or any(
        item.kind == "reading" for item in outside_observations
    )
    assert outside.arrays["a4_joint_axial_profile_map_count"][2] == 0
    detail = outside.record["axial_joint_compartment"]
    assert detail["broadened"] is True
    assert detail["search"] == "broadened_native_search"
    assert uses[-1]["args"][2] == "broadened_native_search"

    source_supported = measured(connected_native_body())
    source_observations, source_missing = run.axial_joint_compartment(
        source_supported, selected_sources(), STUDY, None
    )
    assert source_missing == []
    assert source_observations[0].kind == "resolved"
    source_detail = source_supported.record["axial_joint_compartment"]
    assert source_detail["search"] == "source_location_hit"
    assert source_detail["broadened"] is False
    assert source_detail["unvisited_slices"] == [0, 4]
    assert source_detail["visited_slices"] == [1, 2, 3]


def test_geometry_is_reused_and_component_sizes_cover_the_full_native_plane(
    monkeypatch: pytest.MonkeyPatch,
    production_stubs: None,
) -> None:
    volume = connected_native_body()
    volume[2, 1, 1] = 20.0
    own = measured(volume)
    frame_calls: list[int] = []
    label_calls: list[tuple[int, int]] = []
    real_label = run.ndi.label

    def frame_for(_series: Any, z: int) -> PlaneFrame:
        frame_calls.append(z)
        return PlaneFrame(
            np.asarray([0.0, 0.0, float(z)]),
            np.asarray([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]),
            (1.0, 1.0),
        )

    def label(image: np.ndarray, *, structure: np.ndarray):
        result = real_label(image, structure=structure)
        label_calls.append((int(result[1]), int(np.count_nonzero(image))))
        return result

    monkeypatch.setattr(run, "plane_frame", frame_for)
    monkeypatch.setattr(run.ndi, "label", label)

    observations, missing = run.axial_joint_compartment(
        own, selected_sources(), STUDY, None
    )

    assert missing == []
    assert observations[0].kind == "resolved"
    volume = own.series.volume
    assert volume is not None
    assert len(frame_calls) == len(set(frame_calls)) == len(volume)
    assert label_calls == [(2, 7)]
    assert own.arrays["a4_joint_axial_sizes_2"].tolist() == [1, 6]
    assert own.arrays["a4_joint_axial_white_plane"][0].sum() == 7


def test_unreadable_fluid_level_and_source_projection_are_named_unknown(
    monkeypatch: pytest.MonkeyPatch,
    production_stubs: None,
) -> None:
    bad_level = measured(connected_native_body(), level=cast(Any, ("unreadable", 20.0)))
    level_observations, level_missing = run.axial_joint_compartment(
        bad_level, selected_sources(), STUDY, None
    )

    assert level_observations == []
    assert len(level_missing) == 1
    assert level_missing[0].code.endswith(":unreadable_fluid_level")

    projected = measured(connected_native_body())

    monkeypatch.setattr(
        run,
        "plane_frame",
        lambda _series, z: SimpleNamespace(
            origin_lps=np.asarray([0.0, 0.0, float(z)]),
            normal=lambda: np.asarray([0.0, 0.0, 1.0]),
            to_native=lambda _points: np.full((1, 2), np.nan),
        ),
    )
    projection_observations, projection_missing = run.axial_joint_compartment(
        projected, selected_sources(), STUDY, None
    )

    assert projection_observations == []
    assert len(projection_missing) == 1
    assert projection_missing[0].code.endswith(":source_projection_unavailable")


def test_empty_off_frame_and_one_source_targets_remain_distinct(
    production_stubs: None,
) -> None:
    empty_sources = selected_sources(lps_points((3, 3, 20.0)), lps_points((3, 8, 20.0)))
    no_slab = measured(connected_native_body())
    no_slab_observations, no_slab_missing = run.axial_joint_compartment(
        no_slab, empty_sources, STUDY, None
    )
    assert no_slab_observations == []
    assert no_slab_missing[0].code.endswith(
        ":no_guided_or_source_supported_axial_slice"
    )

    off_frame_sources = selected_sources(
        lps_points((30, 30, 2.0)), lps_points((31, 31, 2.0))
    )
    off_frame = measured(connected_native_body())
    off_frame_observations, off_frame_missing = run.axial_joint_compartment(
        off_frame, off_frame_sources, STUDY, None
    )
    assert off_frame_observations == []
    assert off_frame_missing[0].code.endswith(":source_projection_unavailable")

    one_target = measured(connected_native_body())
    one_target_observations, one_target_missing = run.axial_joint_compartment(
        one_target,
        selected_sources(lps_points((3, 3, 2.0)), lps_points((31, 31, 2.0))),
        STUDY,
        None,
    )
    assert one_target_observations == []
    assert len(one_target_missing) == 1
    assert one_target_missing[0].code.endswith(":source_projection_unavailable")
    projected_rows = one_target.record["axial_joint_compartment"]["source_profile"]
    slice_two = next(row for row in projected_rows if row["slice"] == 2)
    assert slice_two["sagittal_target_pixels"] == 1
    assert slice_two["coronal_target_pixels"] == 0


def test_guided_hit_skips_other_native_peaks_and_keeps_larger_remote_body_unread(
    monkeypatch: pytest.MonkeyPatch,
    production_stubs: None,
) -> None:
    volume = np.zeros((5, 12, 12), dtype=np.float32)
    volume[1, 3, 3:10] = 20.0
    volume[2, 3, 3:6] = 20.0
    own = measured(volume)
    sources = selected_sources(
        lps_points((3, 3, 1.0), (3, 3, 2.0)),
        lps_points((3, 8, 1.0), (3, 5, 2.0)),
    )
    calls: list[int] = []
    real_label = run.ndi.label

    def label(image: np.ndarray, *, structure: np.ndarray):
        calls.append(int(np.count_nonzero(image)))
        return real_label(image, structure=structure)

    monkeypatch.setattr(run.ndi, "label", label)
    observations, missing = run.axial_joint_compartment(
        own, sources, STUDY, mapping_for(slices=(2,), point_lps=(3.0, 5.0, 2.0))
    )

    assert missing == []
    assert len(observations) == 1
    assert observations[0].kind == "resolved"
    assert observations[0].slices == (2,)
    assert calls == [3]
    assert own.arrays["a4_joint_axial_slices"].tolist() == [2]
    assert own.record["axial_joint_compartment"]["search"] == "guided_hit"


def test_wrapper_uses_the_unique_largest_source_and_abstains_on_ties(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Any, dict[str, Any], str, Any]] = []

    def capture(own, sources, study_uid, mapping):
        calls.append((own, sources, study_uid, mapping))
        return [], []

    monkeypatch.setattr(run, "axial_joint_compartment", capture)
    to_patient_calls: list[str] = []

    def source_record(name: str, count: int, view: tuple[str, str, str]):
        volume = np.zeros((3, 12, 12), dtype=np.float32)
        own = measured(volume, view=view)
        own.record["assignments"] = {"codes": {"joint": "identified"}}
        mask = np.zeros((12, 12), dtype=np.int16)
        mask.flat[:count] = run.OBJECT_CODES["joint"]
        own.arrays["a1_objects"] = mask

        def to_patient(rc: np.ndarray) -> np.ndarray:
            to_patient_calls.append(name)
            return np.column_stack((rc[:, 0], rc[:, 1], np.full(len(rc), 7.0)))

        object.__setattr__(
            own, "frame", SimpleNamespace(spacing_rc=(1.0, 1.0), to_patient=to_patient)
        )
        return own

    sagittal_small = source_record("sagittal_small", 2, ("Sagittal", "1", "1"))
    sagittal_large = source_record("sagittal_large", 5, ("Sagittal", "1", "1"))
    coronal = source_record("coronal", 3, ("Coronal", "1", "1"))
    axial = measured(connected_native_body())

    result = run.name_axial_joint_compartment(
        [sagittal_small, sagittal_large, coronal, axial], STUDY, None
    )

    assert len(result) == 4
    assert len(calls) == 1
    assert calls[0][0] is axial
    sources = calls[0][1]
    assert sources["sagittal"]["status"] == "selected"
    assert sources["coronal"]["status"] == "selected"
    assert to_patient_calls.count("sagittal_large") == 1
    assert to_patient_calls.count("coronal") == 1
    assert "sagittal_small" not in to_patient_calls
    np.testing.assert_array_equal(
        sagittal_large.arrays["a4_joint_axial_source_sagittal_lps"],
        sources["sagittal"]["points"],
    )
    assert (
        sagittal_large.record["a4_joint_axial_source_sagittal"]["support"]
        == "a1_objects"
    )
    assert sagittal_large.record["a4_joint_axial_source_sagittal"]["count"] == 5

    calls.clear()
    to_patient_calls.clear()
    tied_sagittal = source_record("sagittal_tied", 5, ("Sagittal", "1", "1"))
    run.name_axial_joint_compartment(
        [sagittal_large, tied_sagittal, coronal, axial], STUDY, None
    )
    tied_sources = calls[0][1]
    assert tied_sources["sagittal"]["status"] == "tied"
    assert "points" not in tied_sources["sagittal"]
    assert len(tied_sources["sagittal"]["detail"]["candidates"]) == 2
