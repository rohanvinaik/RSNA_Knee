from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest

from knee.collapse.observations import Observation
from knee.collapse.physical import PlaneFrame
from scripts import run_interiors as run

STUDY = "study-1"
UID = "sagittal-capsule-series"
SOURCE_UID = "coronal-capsule-series"
SOURCE_ARTIFACT = f"{STUDY}/{SOURCE_UID}.npz"
SOURCE_SUPPORT = "a4_capsule_source_lps"
SUPPORT = "a4_sagittal_capsule_outer_wall"


@pytest.fixture
def production_stubs(monkeypatch: pytest.MonkeyPatch) -> None:
    def frame_for(_series: Any, z: int) -> PlaneFrame:
        return PlaneFrame(
            np.asarray([float(z), 0.0, 0.0]),
            np.asarray([[0.0, 0.0], [0.0, 1.0], [1.0, 0.0]]),
            (1.0, 1.0),
        )

    monkeypatch.setattr(run, "plane_frame", frame_for)
    monkeypatch.setattr(
        run, "finite_of", lambda series: np.isfinite(np.asarray(series.volume))
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
        run,
        "measures_of",
        lambda _uid, _z, plane, _frame: SimpleNamespace(
            along=lambda _axis: (
                -np.broadcast_to(
                    np.arange(np.shape(plane)[1], dtype=np.float64), np.shape(plane)
                )
            )
        ),
    )
    monkeypatch.setattr(
        run, "ledger", SimpleNamespace(record=lambda *_args, **_kwargs: None)
    )


def measured(
    volume: np.ndarray,
    *,
    view: tuple[str, str, str] = ("Sagittal", "1", "1"),
    fat_suppression: int = 1,
    fluid_sensitive: int = 1,
    level: tuple[float | None, float | None] | None = (10.0, 20.0),
) -> run.Measured:
    series = SimpleNamespace(
        row=SimpleNamespace(
            series_uid=UID,
            fat_suppression=fat_suppression,
            fluid_sensitive=fluid_sensitive,
        ),
        volume=volume,
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


def source(*, area: float = 1.0, status: str = "native") -> dict[str, Any]:
    return {
        "artifact": SOURCE_ARTIFACT,
        "support": SOURCE_SUPPORT,
        "row": 0,
        "area_mm2": area,
        "status": status,
        "provenance": "native",
    }


def target(z: int, *, code: str = "on_the_slice") -> Observation:
    return Observation(
        "joint_capsule",
        "projected",
        "target",
        UID,
        ("Sagittal", "1", "1"),
        (z,),
        code,
        1,
        0.0,
        SOURCE_SUPPORT,
        "projected source location only",
        SOURCE_ARTIFACT,
        0,
    )


def points(*rc: tuple[int, int], z: int) -> np.ndarray:
    return np.asarray([[float(z), float(c), float(r)] for r, c in rc])


def guide(
    z: int,
    point_lps: tuple[float, float, float],
    *,
    half_px: tuple[float, float] = (0.0, 0.0),
    status: str = "guided",
) -> SimpleNamespace:
    return SimpleNamespace(
        status=status,
        slices=(z,),
        placements=[{"status": "ok", "point_lps": point_lps}],
        anchors=["anterior_synovial_recess"],
        half_px=half_px,
    )


def mapping_for(
    z: int, point_lps: tuple[float, float, float], *, half_px=(0.0, 0.0)
) -> run.MapContext:
    return cast(
        run.MapContext,
        SimpleNamespace(
            guide=lambda _name, _own: guide(z, point_lps, half_px=half_px),
            smap=SimpleNamespace(note_use=lambda *_args, **_kwargs: None),
        ),
    )


def native_scene(depth: int = 5, *, z: int = 2, wall: bool = True) -> np.ndarray:
    volume = np.zeros((depth, 12, 12), dtype=np.float32)
    volume[z, 3:6, 3:6] = 20.0
    if wall:
        volume[z, 3:6, 6] = 2.0
        volume[z, 3:6, 7] = 4.0
    else:
        volume[z, 3:6, 6:8] = 15.0
    return volume


def test_native_band_is_full_saved_support_not_projected_source_shape(
    production_stubs: None,
) -> None:
    own = measured(native_scene())
    source_points = points((4, 4), (4, 5), z=2)

    observations, missing = run.sagittal_capsule(
        own, source_points, source(), [target(2)], STUDY, None
    )

    assert not missing
    assert len(observations) == 1
    observation = observations[0]
    assert observation.object == "joint_capsule"
    assert observation.kind == "resolved"
    assert observation.provenance == "native"
    assert observation.slices == (2,)
    assert observation.count == 3
    assert observation.artifact == f"{STUDY}/{UID}.npz"
    assert observation.support == SUPPORT
    assert observation.row == 0
    assert observation.count > len(source_points)
    support = own.arrays[SUPPORT]
    assert support.dtype == np.bool_
    assert support.shape == (1, 12, 12)
    expected = np.zeros((12, 12), dtype=bool)
    expected[3:6, 6] = True
    np.testing.assert_array_equal(support[0], expected)
    body = own.arrays["a4_sagittal_capsule_body"]
    expected_body = np.zeros((12, 12), dtype=bool)
    expected_body[3:6, 3:6] = True
    assert body.shape == (1, 12, 12)
    np.testing.assert_array_equal(body[0], expected_body)
    assert own.arrays["a4_sagittal_capsule_slices"].tolist() == [2]
    assert own.record["sagittal_capsule"]["calibration"] == "existing_recess_profile"


def test_native_candidate_is_found_on_neighbor_after_source_plane_misses(
    production_stubs: None,
) -> None:
    volume = native_scene(depth=5, z=3)
    own = measured(volume)

    observations, missing = run.sagittal_capsule(
        own, points((4, 4), (4, 5), z=2), source(), [target(2)], STUDY, None
    )

    assert not missing
    assert [observation.slices for observation in observations] == [(3,)]
    assert observations[0].count == 3
    detail = own.record["sagittal_capsule"]
    assert detail["search"] == "broadened_native_search"
    assert 2 in detail["visited_slices"]
    assert 3 in detail["visited_slices"]
    assert own.arrays["a4_sagittal_capsule_slices"].tolist() == [3]
    assert np.count_nonzero(own.arrays["a4_sagittal_capsule_body"][0]) == 9


def test_map_guide_places_are_used_and_off_map_source_still_resolves(
    production_stubs: None,
) -> None:
    volume = native_scene()
    own = measured(volume)
    mapping = mapping_for(2, (2.0, 4.0, 4.0), half_px=(0.5, 0.5))

    observations, missing = run.sagittal_capsule(
        own, points((4, 4), (4, 5), z=2), source(), [target(2)], STUDY, mapping
    )

    assert not missing
    assert observations[0].count == 3
    assert own.arrays["a4_sagittal_capsule_profile_map_count"][2] > 0
    assert own.record["sagittal_capsule"]["search"] == "guided_hit"

    off_map = measured(native_scene())
    off_map_mapping = mapping_for(2, (2.0, 9.0, 9.0))
    observations, missing = run.sagittal_capsule(
        off_map,
        points((4, 4), (4, 5), z=2),
        source(),
        [target(2)],
        STUDY,
        off_map_mapping,
    )

    assert not missing
    assert observations[0].count == 3
    assert off_map.arrays["a4_sagittal_capsule_profile_count"][2] > 0
    assert off_map.arrays["a4_sagittal_capsule_profile_map_count"][2] == 0
    assert off_map.record["sagittal_capsule"]["search"] == "source_location_hit"


def test_equal_largest_white_bodies_are_tied_not_collapsed(
    production_stubs: None,
) -> None:
    volume = np.zeros((5, 12, 12), dtype=np.float32)
    volume[2, 2:4, 2:4] = 20.0
    volume[2, 7:9, 8:10] = 20.0
    own = measured(volume)
    source_points = points((2, 2), (3, 3), (7, 8), (8, 9), z=2)

    observations, missing = run.sagittal_capsule(
        own, source_points, source(), [target(2)], STUDY, None
    )

    assert len(observations) == 1
    assert observations[0].kind == "reading"
    assert observations[0].count == 0
    assert observations[0].code == "abstain_tied_largest_bodies"
    assert len(missing) == 1
    assert missing[0].code == "sagittal_capsule:tied_largest_native_white_bodies"
    assert not own.arrays[SUPPORT].any()
    assert own.arrays["a4_sagittal_capsule_sizes_2"].tolist() == [4, 4]


@pytest.mark.parametrize(
    ("source_points", "source_record", "expected"),
    [
        (None, source(), "no_native_coronal_capsule_source"),
        (points((4, 4), z=2), None, "no_native_coronal_capsule_source"),
        (None, source(status="tied"), "tied_native_coronal_capsule_sources"),
        (np.asarray([1.0, 2.0, 3.0]), source(), "invalid_native_source_points"),
        (np.asarray([[1.0, 2.0, np.nan]]), source(), "invalid_native_source_points"),
    ],
)
def test_absent_tied_or_malformed_source_is_unknown(
    production_stubs: None,
    source_points: np.ndarray | None,
    source_record: dict[str, Any] | None,
    expected: str,
) -> None:
    own = measured(np.zeros((5, 12, 12), dtype=np.float32))

    observations, missing = run.sagittal_capsule(
        own, source_points, source_record, [target(2)], STUDY, None
    )

    assert observations == []
    assert [item.code for item in missing] == [f"sagittal_capsule:{expected}"]


def test_wrong_sequence_refuses_and_nonsagittal_record_is_skipped(
    production_stubs: None,
) -> None:
    wrong_sequence = measured(native_scene(), fluid_sensitive=0)
    observations, missing = run.sagittal_capsule(
        wrong_sequence, points((4, 4), z=2), source(), [target(2)], STUDY, None
    )
    assert observations == []
    assert [item.code for item in missing] == [
        "sagittal_capsule:fluid_not_bright_on_this_sequence"
    ]

    non_sagittal = measured(native_scene(), view=("Coronal", "1", "1"))
    observations, missing = run.sagittal_capsule(
        non_sagittal, points((4, 4), z=2), source(), [target(2)], STUDY, None
    )
    assert observations == missing == []
    assert "sagittal_capsule" not in non_sagittal.record


def test_finite_source_without_native_white_sample_is_unknown(
    monkeypatch: pytest.MonkeyPatch,
    production_stubs: None,
) -> None:
    own = measured(native_scene())
    monkeypatch.setattr(
        run,
        "finite_of",
        lambda series: np.zeros(np.shape(series.volume), dtype=bool),
    )

    observations, missing = run.sagittal_capsule(
        own, points((4, 4), (4, 5), z=2), source(), [target(2)], STUDY, None
    )

    assert observations == []
    assert [item.code for item in missing] == [
        "sagittal_capsule:unavailable_native_source_samples"
    ]
    assert np.isnan(own.arrays["a4_sagittal_capsule_profile_count"]).all()


def test_native_body_without_darker_outer_band_is_measured_empty(
    monkeypatch: pytest.MonkeyPatch,
    production_stubs: None,
) -> None:
    own = measured(native_scene())

    def margin_with_outer_strip(_uid: str, _z: int, plane: np.ndarray) -> np.ndarray:
        margin = np.zeros(np.shape(plane), dtype=bool)
        margin[3:6, 6:8] = True
        return margin

    monkeypatch.setattr(run, "margin_of", margin_with_outer_strip)

    observations, missing = run.sagittal_capsule(
        own, points((4, 4), (4, 5), z=2), source(), [target(2)], STUDY, None
    )

    assert not missing
    assert len(observations) == 1
    assert observations[0].kind == "reading"
    assert observations[0].count == 0
    assert observations[0].code == "abstain_no_outer_band_in_shell"
    assert own.record["sagittal_capsule"]["code"] == "measured_empty_outer_band"
    assert not own.arrays[SUPPORT].any()


def test_existing_fluid_level_is_reused_without_marrow_read(
    monkeypatch: pytest.MonkeyPatch,
    production_stubs: None,
) -> None:
    own = measured(native_scene())

    def physical_only(*_args, **_kwargs):
        return SimpleNamespace(
            along=lambda _axis: (
                -np.broadcast_to(np.arange(12, dtype=np.float64), (12, 12))
            ),
            light=lambda _mask: pytest.fail("shared marrow light recomputed"),
        )

    monkeypatch.setattr(run, "measures_of", physical_only)
    observations, missing = run.sagittal_capsule(
        own, points((4, 4), (4, 5), z=2), source(), [target(2)], STUDY, None
    )

    assert not missing
    assert observations[0].count == 3
    assert own.record["sagittal_capsule"]["level"] == 10.0
    assert own.record["sagittal_capsule"]["calibration"] == "existing_recess_profile"


def test_wrapper_selects_unique_largest_native_coronal_source_and_ties_abstain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chosen: list[tuple[np.ndarray | None, dict[str, Any] | None]] = []

    def capture(_own, source_points, source_record, _targets, _study, _mapping):
        chosen.append((source_points, source_record))
        return [], []

    monkeypatch.setattr(run, "sagittal_capsule", capture)
    p_small, p_large = points((1, 1), z=0), points((2, 2), z=0)
    first = measured(np.zeros((3, 4, 4), dtype=np.float32), view=("Coronal", "1", "1"))
    first.arrays[SOURCE_SUPPORT] = p_small
    first.record["capsule_source"] = source(area=2.0)
    second = measured(np.zeros((3, 4, 4), dtype=np.float32), view=("Coronal", "1", "1"))
    second.arrays[SOURCE_SUPPORT] = p_large
    second.record["capsule_source"] = source(area=5.0)
    sagittal = measured(np.zeros((3, 4, 4), dtype=np.float32))
    measured_rows = [first, second, sagittal]
    said: list[tuple[list[Observation], list[run.Unresolved]]] = [
        ([], []),
        ([], []),
        ([], []),
    ]

    result = run.name_sagittal_capsule(measured_rows, said, STUDY, None)

    assert len(result) == 3
    assert len(chosen) == len(measured_rows)
    for selected_points, selected_source in chosen:
        np.testing.assert_array_equal(selected_points, p_large)
        assert selected_source == source(area=5.0)

    chosen.clear()
    first.record["capsule_source"] = source(area=5.0)
    second.record["capsule_source"] = source(area=5.0)
    run.name_sagittal_capsule(measured_rows, said, STUDY, None)
    assert len(chosen) == len(measured_rows)
    for selected_points, selected_source in chosen:
        assert selected_points is None
        assert selected_source is not None
        assert selected_source["status"] == "tied"
        assert len(selected_source["candidates"]) == 2
