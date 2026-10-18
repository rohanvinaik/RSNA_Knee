from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest

from knee.collapse.observations import Observation
from knee.collapse.physical import PlaneFrame
from scripts import run_interiors as run

STUDY = "study-1"
UID = "coronal-series"
SOURCE_UID = "sagittal-series"
ARTIFACT = f"{STUDY}/{SOURCE_UID}.npz"
SUPPORT = "a2_anterior_synovial_recess"


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


def measured(
    volume: np.ndarray,
    *,
    view: tuple[str, str, str] = ("Coronal", "1", "1"),
    fluid_sensitive: int = 1,
) -> run.Measured:
    series = SimpleNamespace(
        row=SimpleNamespace(
            series_uid=UID,
            fat_suppression=1,
            fluid_sensitive=fluid_sensitive,
        ),
        volume=volume,
    )
    record = {
        "series_uid": UID,
        "view": view,
        "slice_index": len(volume) // 2,
        "recess": {"level": (10.0, 20.0)},
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


def source(*, area: float = 1.0, status: str = "identified") -> dict[str, Any]:
    return {
        "artifact": ARTIFACT,
        "support": SUPPORT,
        "row": 0,
        "area_mm2": area,
        "status": status,
    }


def target(z: int, *, code: str = "on_the_slice") -> Observation:
    return Observation(
        "anterior_synovial_recess",
        "projected",
        "target",
        UID,
        ("Coronal", "1", "1"),
        (z,),
        code,
        1,
        0.0,
        SUPPORT,
        "projected location only",
        ARTIFACT,
        0,
    )


def points(*rc: tuple[int, int], z: int) -> np.ndarray:
    return np.asarray([[float(r), float(c), float(z)] for r, c in rc])


def guide(
    z: int, point_lps: tuple[float, float, float], *, status: str = "guided"
) -> SimpleNamespace:
    return SimpleNamespace(
        status=status,
        slices=(z,),
        placements=[{"status": "ok", "point_lps": point_lps}],
        anchors=["anterior_synovial_recess"],
        half_px=(0.0, 0.0),
    )


def mapping_for(z: int, point_lps: tuple[float, float, float]) -> run.MapContext:
    return cast(
        run.MapContext,
        SimpleNamespace(
            guide=lambda _name, _own: guide(z, point_lps),
            smap=SimpleNamespace(note_use=lambda *_args, **_kwargs: None),
        ),
    )


def test_direct_coronal_read_uses_native_white_body_not_projection_as_boundary(
    production_stubs: None,
) -> None:
    volume = np.zeros((5, 10, 10), dtype=np.float32)
    volume[2, 2:5, 2:5] = 12.0
    own = measured(volume)

    observations, missing = run.coronal_anterior_recess(
        own, points((3, 3), z=2), source(), [target(2)], STUDY, None
    )

    assert not missing
    assert len(observations) == 1
    observation = observations[0]
    assert observation.kind == "resolved"
    assert observation.provenance == "native"
    assert observation.support == "a4_coronal_anterior_recess"
    assert observation.slices == (2,)
    assert observation.count == 9
    assert observation.artifact == f"{STUDY}/{UID}.npz"
    assert observation.row == 0
    assert own.arrays[observation.support].dtype == np.bool_
    assert own.arrays[observation.support].shape == (1, 10, 10)
    assert np.count_nonzero(own.arrays[observation.support][0]) == 9
    assert (
        own.record["coronal_anterior_recess"]["calibration"]
        == "existing_recess_profile"
    )


def test_map_guided_neighbor_peak_survives_an_initial_source_slice_miss(
    production_stubs: None,
) -> None:
    volume = np.zeros((4, 10, 10), dtype=np.float32)
    volume[2, 5:7, 5:7] = 12.0
    own = measured(volume)
    mapping = mapping_for(2, (5.0, 5.0, 2.0))

    observations, missing = run.coronal_anterior_recess(
        own, points((5, 5), z=1), source(), [target(1)], STUDY, mapping
    )

    assert not missing
    assert [o.slices for o in observations] == [(2,)]
    detail = own.record["coronal_anterior_recess"]
    assert detail["search"] == "guided_hit"
    assert detail["broadened"] is False
    assert detail["visited_slices"] == [1, 2, 3]
    np.testing.assert_array_equal(
        own.arrays["a4_coronal_anterior_profile_count"][1:3], [0.0, 1.0]
    )
    np.testing.assert_array_equal(
        own.arrays["a4_coronal_anterior_profile_map_count"][1:3], [0.0, 1.0]
    )
    assert observations[0].count == 4


def test_equal_slice_peaks_are_both_retained_after_broadening(
    production_stubs: None,
) -> None:
    volume = np.zeros((5, 10, 10), dtype=np.float32)
    volume[1, 3, 3:5] = 12.0
    volume[2, 3, 3] = 12.0
    volume[3, 3, 3:5] = 12.0
    own = measured(volume)

    observations, missing = run.coronal_anterior_recess(
        own, points((3, 3), (3, 4), z=2), source(), [target(2)], STUDY, None
    )

    assert not missing
    assert [o.slices for o in observations] == [(1,), (3,)]
    assert [o.count for o in observations] == [2, 2]
    assert own.record["coronal_anterior_recess"]["broadened"] is False


def test_tied_largest_native_bodies_remain_an_abstention(
    production_stubs: None,
) -> None:
    volume = np.zeros((3, 12, 12), dtype=np.float32)
    volume[1, 1, 1:3] = 12.0
    volume[1, 8, 8:10] = 12.0
    own = measured(volume)

    observations, missing = run.coronal_anterior_recess(
        own,
        points((1, 1), (8, 8), z=1),
        source(),
        [target(1)],
        STUDY,
        None,
    )

    assert len(observations) == 1
    assert observations[0].kind == "reading"
    assert observations[0].count == 0
    assert observations[0].code == "abstain_tied_largest_bodies"
    assert len(missing) == 1
    assert missing[0].code == "coronal_anterior_recess:native_body_not_resolved"
    assert not own.arrays["a4_coronal_anterior_recess"].any()


@pytest.mark.parametrize(
    ("source_points", "source_record", "expected"),
    [
        (None, source(status="tied"), "tied_native_sagittal_recess_sources"),
        (None, None, "no_native_sagittal_recess_source"),
        (np.asarray([1.0, 2.0, 3.0]), source(), "invalid_native_source_points"),
        (np.asarray([[1.0, 2.0, np.nan]]), source(), "invalid_native_source_points"),
    ],
)
def test_missing_or_invalid_sagittal_source_is_named_unknown(
    production_stubs: None,
    source_points: np.ndarray | None,
    source_record: dict[str, Any] | None,
    expected: str,
) -> None:
    own = measured(np.zeros((3, 8, 8), dtype=np.float32))

    observations, missing = run.coronal_anterior_recess(
        own, source_points, source_record, [target(1)], STUDY, None
    )

    assert observations == []
    assert [m.code for m in missing] == [f"coronal_anterior_recess:{expected}"]


def test_wrong_sequence_and_noncoronal_record_do_not_create_absence(
    production_stubs: None,
) -> None:
    own = measured(np.zeros((3, 8, 8), dtype=np.float32), fluid_sensitive=0)

    observations, missing = run.coronal_anterior_recess(
        own, points((3, 3), z=1), source(), [target(1)], STUDY, None
    )

    assert observations == []
    assert [m.code for m in missing] == [
        "coronal_anterior_recess:fluid_not_bright_on_this_sequence"
    ]
    untouched = measured(
        np.zeros((3, 8, 8), dtype=np.float32), view=("Axial", "1", "1")
    )
    observations, missing = run.coronal_anterior_recess(
        untouched, points((3, 3), z=1), source(), [target(1)], STUDY, None
    )
    assert observations == missing == []
    assert "coronal_anterior_recess" not in untouched.record


@pytest.mark.parametrize("unavailable", ["nonfinite", "margin"])
def test_unavailable_source_pixels_are_not_emitted_as_native_observations(
    monkeypatch: pytest.MonkeyPatch,
    production_stubs: None,
    unavailable: str,
) -> None:
    volume = np.zeros((3, 8, 8), dtype=np.float32)
    volume[1, 3, 3] = 12.0
    own = measured(volume)
    if unavailable == "nonfinite":
        finite = np.isfinite(volume)
        finite[:, 3, 3] = False
        monkeypatch.setattr(run, "finite_of", lambda _series: finite)
    else:
        margin = np.zeros((8, 8), dtype=bool)
        margin[3, 3] = True
        monkeypatch.setattr(run, "margin_of", lambda _uid, _z, _plane: margin)

    observations, missing = run.coronal_anterior_recess(
        own, points((3, 3), z=1), source(), [target(1)], STUDY, None
    )

    assert observations == []
    assert [m.code for m in missing] == [
        "coronal_anterior_recess:source_location_unreadable"
    ]
    assert own.record["coronal_anterior_recess"]["status_codes"]["unavailable"] == 3
    assert np.isnan(own.arrays["a4_coronal_anterior_profile_count"]).all()


@pytest.mark.parametrize(
    ("target_observations", "expected"),
    [
        ([], "native_source_not_located_in_acquired_stack"),
        ([target(12)], "no_usable_starting_plane"),
        (
            [target(2, code="beyond_the_scan")],
            "native_source_not_located_in_acquired_stack",
        ),
    ],
)
def test_target_outside_available_stack_is_named_unknown(
    production_stubs: None,
    target_observations: list[Observation],
    expected: str,
) -> None:
    own = measured(np.zeros((3, 8, 8), dtype=np.float32))

    observations, missing = run.coronal_anterior_recess(
        own, points((3, 3), z=1), source(), target_observations, STUDY, None
    )

    assert observations == []
    assert [m.code for m in missing] == [f"coronal_anterior_recess:{expected}"]


def test_existing_positive_recess_level_is_reused_without_marrow_recompute(
    monkeypatch: pytest.MonkeyPatch,
    production_stubs: None,
) -> None:
    volume = np.zeros((3, 8, 8), dtype=np.float32)
    volume[1, 3:5, 3:5] = 12.0
    own = measured(volume)
    monkeypatch.setattr(
        run,
        "measures_of",
        lambda *_args, **_kwargs: pytest.fail("marrow calibration recomputed"),
    )

    observations, missing = run.coronal_anterior_recess(
        own, points((3, 3), z=1), source(), [target(1)], STUDY, None
    )

    assert not missing
    assert observations[0].count == 4
    assert own.record["coronal_anterior_recess"]["level"] == 10.0
    assert (
        own.record["coronal_anterior_recess"]["calibration"]
        == "existing_recess_profile"
    )


def test_each_candidate_body_is_read_once(
    monkeypatch: pytest.MonkeyPatch,
    production_stubs: None,
) -> None:
    volume = np.zeros((3, 8, 8), dtype=np.float32)
    volume[1, 3:5, 3:5] = 12.0
    own = measured(volume)
    original = run.white_body_at_location
    calls: list[tuple[tuple[int, ...], tuple[int, ...]]] = []

    def counted(white: np.ndarray, target_mask: np.ndarray):
        calls.append((white.shape, target_mask.shape))
        return original(white, target_mask)

    monkeypatch.setattr(run, "white_body_at_location", counted)

    observations, missing = run.coronal_anterior_recess(
        own, points((3, 3), z=1), source(), [target(1)], STUDY, None
    )

    assert not missing
    assert len(observations) == 1
    assert calls == [((8, 8), (8, 8))]


def test_name_coronal_anterior_recess_uses_unique_largest_source_and_refuses_tie(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chosen: list[tuple[np.ndarray | None, dict[str, Any] | None]] = []

    def capture(_own, points_lps, source_record, _targets, _study, _mapping):
        chosen.append((points_lps, source_record))
        return [], []

    monkeypatch.setattr(run, "coronal_anterior_recess", capture)
    p_small, p_large = points((1, 1), z=0), points((2, 2), z=0)
    first = measured(np.zeros((2, 4, 4), dtype=np.float32))
    first.arrays["a4_anterior_recess_source_lps"] = p_small
    first.record["anterior_recess_source"] = source(area=2.0)
    second = measured(np.zeros((2, 4, 4), dtype=np.float32))
    second.arrays["a4_anterior_recess_source_lps"] = p_large
    second.record["anterior_recess_source"] = source(area=5.0)
    measured_rows = [first, second]
    said = [([], []), ([], [])]

    result = run.name_coronal_anterior_recess(measured_rows, said, STUDY, None)

    assert len(result) == 2
    assert len(chosen) == 2
    np.testing.assert_array_equal(chosen[0][0], p_large)
    np.testing.assert_array_equal(chosen[1][0], p_large)
    assert chosen[0][1] == chosen[1][1] == source(area=5.0)

    chosen.clear()
    tied_first = measured(np.zeros((2, 4, 4), dtype=np.float32))
    tied_first.arrays["a4_anterior_recess_source_lps"] = p_small
    tied_first.record["anterior_recess_source"] = source(area=5.0)
    tied_second = measured(np.zeros((2, 4, 4), dtype=np.float32))
    tied_second.arrays["a4_anterior_recess_source_lps"] = p_large
    tied_second.record["anterior_recess_source"] = source(area=5.0)
    run.name_coronal_anterior_recess([tied_first, tied_second], said, STUDY, None)
    assert len(chosen) == 2
    assert chosen[0][0] is None and chosen[1][0] is None
    assert chosen[0][1] == chosen[1][1]
    assert chosen[0][1]["status"] == "tied"
    assert len(chosen[0][1]["candidates"]) == 2


def test_name_coronal_anterior_recess_sends_tied_sources_to_unknown_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def refuse(own, points_lps, source_record, _targets, _study, _mapping):
        nonlocal calls
        calls += 1
        assert points_lps is None
        assert source_record["status"] == "tied"
        return [], [
            run.Unresolved(
                "anterior_synovial_recess",
                "native",
                own.series.row.series_uid,
                tuple(own.record["view"]),
                "coronal_anterior_recess:tied_native_sagittal_recess_sources",
            )
        ]

    monkeypatch.setattr(run, "coronal_anterior_recess", refuse)
    candidates = [measured(np.zeros((3, 8, 8), dtype=np.float32)) for _ in range(2)]
    for item, point in zip(
        candidates, (points((1, 1), z=0), points((2, 2), z=0)), strict=True
    ):
        item.arrays["a4_anterior_recess_source_lps"] = point
        item.record["anterior_recess_source"] = source(area=4.0)

    results = run.name_coronal_anterior_recess(
        candidates, [([], []), ([], [])], STUDY, None
    )

    assert calls == 2
    assert all(not observations for observations, _missing in results)
    assert all(
        missing[0].code == "coronal_anterior_recess:tied_native_sagittal_recess_sources"
        for _observations, missing in results
    )
