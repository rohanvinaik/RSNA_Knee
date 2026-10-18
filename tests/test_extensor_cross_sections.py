from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest

from knee.collapse.physical import PlaneFrame
from scripts import run_interiors as run

STUDY = "extensor-cross-section-study"
UID = "extensor-cross-section-axial"
TENDONS = ("patellar_tendon", "quadriceps_tendon")


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
    monkeypatch.setattr(
        run,
        "lens_of",
        lambda *_args: (None, 1.0, None),
    )
    monkeypatch.setattr(
        run,
        "field_of",
        lambda _series, _z, plane, _frame, _reading: SimpleNamespace(
            objects=np.full(np.shape(plane), run.OBJECT_CODES["femur"])
        ),
    )
    monkeypatch.setattr(
        run,
        "measures_of",
        lambda *_args: SimpleNamespace(
            along=lambda _axis: 1.0, light=lambda _mask: 1.0
        ),
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
    slice_index: int | None = None,
    thickness: tuple[Any, ...] | None = None,
) -> run.Measured:
    if thickness is None:
        thickness = (0.8,) * len(volume)
    series = SimpleNamespace(
        row=SimpleNamespace(
            series_uid=UID,
            fat_suppression=0 if view[0].casefold() == "sagittal" else 1,
            fluid_sensitive=1,
        ),
        volume=volume,
        slices=tuple(range(len(volume))),
        slice_thickness_mm=thickness,
        geometry=object(),
    )
    if slice_index is None:
        slice_index = len(volume) // 2
    record: dict[str, Any] = {
        "series_uid": UID,
        "view": view,
        "slice_index": slice_index,
        "background_split": 10.0,
        "assignments": {"codes": {}},
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


def lps_points(*rcz: tuple[float, float, float]) -> np.ndarray:
    return np.asarray([[r, c, z] for r, c, z in rcz], dtype=float)


def source(points: np.ndarray | None, tendon: str) -> dict[str, Any]:
    if points is None:
        return {"status": "unavailable", "detail": {"status": "unavailable"}}
    return {
        "status": "selected",
        "points": points,
        "metadata": {
            "series_uid": f"{tendon}-native-sagittal",
            "slice": 12,
            "code": "identified",
            "count": len(points),
            "area_mm2": float(len(points)),
            "artifact": f"{STUDY}/{tendon}-native-sagittal.npz",
            "support": "a1_objects",
            "label": int(run.OBJECT_CODES[tendon]),
            "provenance": "native",
            "row": None,
        },
        "detail": {"status": "selected"},
    }


def sources_for(
    patellar: np.ndarray | None = None,
    quadriceps: np.ndarray | None = None,
) -> dict[str, dict[str, Any]]:
    if patellar is None:
        patellar = lps_points((6.0, 6.0, 2.0))
    if quadriceps is None:
        quadriceps = lps_points((17.0, 17.0, 2.0))
    return {
        "patellar_tendon": source(patellar, "patellar_tendon"),
        "quadriceps_tendon": source(quadriceps, "quadriceps_tendon"),
    }


def enclosed_bodies(
    *, depth: int = 5, shape: tuple[int, int] = (28, 28), z: int = 2
) -> np.ndarray:
    volume = np.full((depth, *shape), 20.0, dtype=np.float32)
    return volume


def dark_patch(
    volume: np.ndarray,
    z: int,
    center: tuple[int, int],
    size: int = 5,
) -> None:
    half = size // 2
    row, col = center
    volume[z, row - half : row + half + 1, col - half : col + half + 1] = 2.0


def mapping_for(
    *,
    slices: tuple[int, ...] = (2,),
    point_lps: tuple[float, float, float] = (6.0, 6.0, 2.0),
    half_px: tuple[float, float] = (0.0, 0.0),
) -> run.MapContext:
    guide = SimpleNamespace(
        status="guided",
        slices=slices,
        placements=[{"status": "ok", "point_lps": point_lps}],
        anchors=["patella", "tibia"],
        half_px=half_px,
    )
    return cast(
        run.MapContext,
        SimpleNamespace(
            guide=lambda _name, _own: guide,
            smap=SimpleNamespace(note_use=lambda *_args, **_kwargs: None),
        ),
    )


def observation_for(observations: list[run.Observation], name: str) -> run.Observation:
    return next(item for item in observations if item.object == name)


def test_selected_body_is_native_and_not_a_projected_source_line(
    production_stubs: None,
) -> None:
    volume = enclosed_bodies()
    dark_patch(volume, 2, (6, 6), size=5)
    dark_patch(volume, 2, (20, 20), size=9)
    own = measured(volume)
    assert "recess" not in own.record
    assert "a1_objects" not in own.arrays

    observations, missing = run.extensor_sections(
        own,
        sources_for(patellar=lps_points((6.4, 6.4, 2.0))),
        STUDY,
        None,
    )

    assert missing == []
    observed = observation_for(observations, "patellar_tendon")
    assert observed.kind == "resolved", own.record["axial_extensor_sections"]
    assert observed.provenance == "native"
    assert observed.code == "identified"
    assert observed.slices == (2,)
    assert observed.label is None
    assert observed.support == "a4_axial_patellar_tendon_body"
    support = own.arrays[observed.support]
    assert support.dtype == np.bool_
    assert support.shape[1:] == volume.shape[1:]
    assert int(support[observed.row].sum()) == observed.count
    expected = np.zeros(volume.shape[1:], dtype=bool)
    expected[4:9, 4:9] = True
    expected[4, 4] = False
    expected[4, 8] = False
    expected[8, 4] = False
    expected[8, 8] = False
    np.testing.assert_array_equal(support[observed.row], expected)
    assert own.arrays["a4_axial_patellar_tendon_slices"][observed.row] == 2
    profile_rc = own.arrays["a4_axial_patellar_tendon_profile_rc"]
    profile_offsets = own.arrays["a4_axial_patellar_tendon_profile_offsets"]
    assert profile_rc[profile_offsets[2] : profile_offsets[3]].tolist() == [[6, 6]]


def test_two_tendons_read_separate_native_bodies_and_share_one_depth_measurement(
    monkeypatch: pytest.MonkeyPatch,
    production_stubs: None,
) -> None:
    volume = enclosed_bodies()
    dark_patch(volume, 2, (6, 6), size=5)
    dark_patch(volume, 2, (17, 17), size=5)
    own = measured(volume)
    calls: list[tuple[str | None, int | None, str, tuple[int, ...]]] = []
    body_calls: list[tuple[tuple[int, ...], int]] = []
    real_depth = run.enclosed_darkness
    real_bodies = run.dark_tendon_bodies

    def count_depth(plane: np.ndarray) -> np.ndarray:
        calls.append((None, None, plane.dtype.str, plane.shape))
        return real_depth(plane)

    def count_bodies(dark, free, spacing_rc, back_mm, inner_mm):
        body_calls.append((dark.shape, int(dark.sum())))
        return real_bodies(dark, free, spacing_rc, back_mm, inner_mm)

    monkeypatch.setattr(run, "enclosed_darkness", count_depth)
    monkeypatch.setattr(run, "dark_tendon_bodies", count_bodies)
    with run.computing():
        observations, missing = run.extensor_sections(own, sources_for(), STUDY, None)

    assert missing == []
    for name in TENDONS:
        observed = observation_for(observations, name)
        assert observed.kind == "resolved"
        assert own.arrays[observed.support].dtype == np.bool_
        assert int(own.arrays[observed.support][observed.row].sum()) == observed.count
    assert calls.count((None, None, volume.dtype.str, volume.shape[1:])) == 1
    assert len(body_calls) == 1


def test_measured_empty_is_native_false_mask_and_unsampled_source_is_unknown(
    production_stubs: None,
) -> None:
    empty_volume = np.zeros((5, 28, 28), dtype=np.float32)
    empty = measured(empty_volume)
    empty_observations, empty_missing = run.extensor_sections(
        empty,
        sources_for(),
        STUDY,
        None,
    )
    assert empty_missing == []
    observed = observation_for(empty_observations, "patellar_tendon")
    assert observed.kind == "reading"
    assert observed.count == 0
    assert observed.support == "a4_axial_patellar_tendon_body"
    profile_slices = empty.arrays["a4_axial_patellar_tendon_profile_slices"]
    offsets = empty.arrays["a4_axial_patellar_tendon_profile_offsets"]
    rc = empty.arrays["a4_axial_patellar_tendon_profile_rc"]
    target = empty.arrays["a4_axial_patellar_tendon_profile_target"]
    body = empty.arrays[observed.support]
    profile_row = int(np.flatnonzero(profile_slices == observed.slices[0])[0])
    assert body.dtype == np.bool_
    assert body.shape == (1, *empty_volume.shape[1:])
    assert empty.arrays["a4_axial_patellar_tendon_slices"][observed.row] == 2
    assert profile_slices[profile_row] == observed.slices[0]
    assert offsets[profile_row : profile_row + 2].tolist() == [0, 1]
    assert rc[offsets[profile_row] : offsets[profile_row + 1]].tolist() == [[6, 6]]
    assert target[profile_row].tolist() == [True]
    assert not body[observed.row].any()
    assert "recess" not in empty.record
    assert "a1_objects" not in empty.arrays

    outside = measured(enclosed_bodies())
    outside_sources = sources_for(patellar=lps_points((6.0, 6.0, 20.0)))
    outside_observations, outside_missing = run.extensor_sections(
        outside, outside_sources, STUDY, None
    )
    assert not any(item.kind == "resolved" for item in outside_observations)
    assert any(
        item.object == "patellar_tendon"
        and item.code == "axial_extensor_sections:no_source_supported_axial_slice"
        for item in outside_missing
    )

    off_frame = measured(enclosed_bodies())
    _, off_frame_missing = run.extensor_sections(
        off_frame,
        sources_for(patellar=lps_points((60.0, 60.0, 2.0))),
        STUDY,
        None,
    )
    assert any(
        item.object == "patellar_tendon"
        and item.code
        == "axial_extensor_sections:source_projection_outside_frame_at_slice_2"
        for item in off_frame_missing
    )

    malformed = measured(enclosed_bodies(), thickness=(0.8, 0.8, "bad", 0.8, 0.8))
    malformed_observations, malformed_missing = run.extensor_sections(
        malformed, sources_for(), STUDY, None
    )
    assert not any(item.kind == "resolved" for item in malformed_observations)
    assert any(
        item.object == "patellar_tendon"
        and item.code == "axial_extensor_sections:actual_slice_thickness_unavailable"
        for item in malformed_missing
    )


def test_tied_bodies_and_nonfinite_source_projection_do_not_select_a_body(
    monkeypatch: pytest.MonkeyPatch,
    production_stubs: None,
) -> None:
    tied_volume = enclosed_bodies()
    dark_patch(tied_volume, 2, (6, 6), size=5)
    dark_patch(tied_volume, 2, (20, 20), size=5)
    tied = measured(tied_volume)
    tied_sources = sources_for(patellar=lps_points((6.0, 6.0, 2.0), (20.0, 20.0, 2.0)))
    tied_observations, tied_missing = run.extensor_sections(
        tied, tied_sources, STUDY, None
    )
    assert not any(
        item.kind == "resolved" and item.object == "patellar_tendon"
        for item in tied_observations
    )
    assert any(item.object == "patellar_tendon" for item in tied_missing)

    projected = measured(tied_volume)
    monkeypatch.setattr(
        run,
        "plane_frame",
        lambda _series, z: SimpleNamespace(
            origin_lps=np.asarray([0.0, 0.0, float(z)]),
            normal=lambda: np.asarray([0.0, 0.0, 1.0]),
            to_native=lambda _points: np.full((1, 2), np.nan),
        ),
    )
    projected_observations, projected_missing = run.extensor_sections(
        projected, sources_for(), STUDY, None
    )
    assert not any(
        item.kind == "resolved" and item.object == "patellar_tendon"
        for item in projected_observations
    )
    assert any(
        item.object == "patellar_tendon"
        and item.code
        == "axial_extensor_sections:source_projection_unavailable_at_slice_2"
        for item in projected_missing
    )

    malformed_projection = measured(tied_volume)
    monkeypatch.setattr(
        run,
        "plane_frame",
        lambda _series, z: SimpleNamespace(
            origin_lps=np.asarray([0.0, 0.0, float(z)]),
            normal=lambda: np.asarray([0.0, 0.0, 1.0]),
            to_native=lambda _points: np.empty((0, 2)),
        ),
    )
    _, malformed_projection_missing = run.extensor_sections(
        malformed_projection, sources_for(), STUDY, None
    )
    assert any(
        item.object == "patellar_tendon"
        and item.code
        == "axial_extensor_sections:source_projection_unavailable_at_slice_2"
        for item in malformed_projection_missing
    )


def test_guide_uses_depth_and_inplane_and_falls_back_after_miss(
    production_stubs: None,
) -> None:
    volume = enclosed_bodies()
    dark_patch(volume, 2, (6, 6), size=5)
    dark_patch(volume, 3, (6, 6), size=5)
    own = measured(volume)
    patellar_points = lps_points((6.0, 6.0, 2.0), (6.0, 6.0, 3.0))
    guided_observations, _ = run.extensor_sections(
        own,
        sources_for(patellar=patellar_points),
        STUDY,
        mapping_for(point_lps=(6.0, 6.0, 2.0)),
    )
    assert observation_for(guided_observations, "patellar_tendon").kind == "resolved"
    guide_detail = own.record["axial_extensor_sections"]["tendons"]["patellar_tendon"]
    assert guide_detail["profile"][2]["map_count"] == 1
    assert guide_detail["candidate_order"] == {
        "map_guided_first": [2],
        "source_profile_fallback": [3],
    }
    assert guide_detail["candidate_slices"] == [2]
    assert guide_detail["broadened_after_guided_miss"] is False

    missed = measured(volume.copy())
    missed_observations, missed_missing = run.extensor_sections(
        missed,
        sources_for(patellar=patellar_points),
        STUDY,
        mapping_for(point_lps=(26.0, 26.0, 2.0)),
    )
    assert observation_for(missed_observations, "patellar_tendon").kind == "resolved"
    assert not any(item.object == "patellar_tendon" for item in missed_missing)
    missed_detail = missed.record["axial_extensor_sections"]["tendons"][
        "patellar_tendon"
    ]
    assert missed_detail["profile"][2]["map_count"] == 0
    assert missed_detail["candidate_order"]["source_profile_fallback"] == [2, 3]
    assert missed_detail["candidate_slices"] == [2, 3]
    assert missed_detail["broadened_after_guided_miss"] is True


def test_valid_partial_source_is_retained_and_malformed_source_is_unknown(
    production_stubs: None,
) -> None:
    volume = enclosed_bodies()
    dark_patch(volume, 2, (6, 6), size=5)
    own = measured(volume)
    source_data = sources_for(patellar=lps_points((6.0, 6.0, 2.0), (60.0, 60.0, 2.0)))
    source_data["quadriceps_tendon"] = {
        "status": "unavailable",
        "detail": {"status": "unavailable"},
    }

    observations, missing = run.extensor_sections(own, source_data, STUDY, None)

    observed = observation_for(observations, "patellar_tendon")
    assert observed.kind == "resolved"
    assert observed.count is not None and observed.count > 0
    assert not own.arrays["a4_axial_patellar_tendon_projection_complete"][2]
    assert any(
        item.object == "quadriceps_tendon"
        and item.code
        == "axial_extensor_sections:no_native_sagittal_quadriceps_tendon_source"
        for item in missing
    )

    malformed_source = measured(volume.copy())
    bad_source = sources_for(patellar=lps_points((float("nan"), 6.0, 2.0)))
    bad_source_observations, bad_source_missing = run.extensor_sections(
        malformed_source, bad_source, STUDY, None
    )
    assert not any(item.object == "patellar_tendon" for item in bad_source_observations)
    assert any(
        item.object == "patellar_tendon"
        and item.code
        == "axial_extensor_sections:unreadable_native_sagittal_patellar_tendon_source"
        for item in bad_source_missing
    )


def test_wrapper_selects_only_unique_largest_native_sagittal_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[tuple[Any, dict[str, dict], str, Any]] = []

    def capture(own, sources, study_uid, mapping):
        captured.append((own, sources, study_uid, mapping))
        return [], []

    monkeypatch.setattr(run, "extensor_sections", capture)
    conversions: list[str] = []

    def source_record(uid: str, tendon: str, count: int) -> run.Measured:
        own = measured(
            np.zeros((3, 28, 28), dtype=np.float32),
            view=("Sagittal", "0", "0"),
        )
        own.record["series_uid"] = uid
        own.record["assignments"]["codes"][tendon] = "identified"
        mask = np.zeros((28, 28), dtype=np.int16)
        mask.flat[:count] = run.OBJECT_CODES[tendon]
        own.arrays["a1_objects"] = mask

        def to_patient(rc: np.ndarray) -> np.ndarray:
            conversions.append(uid)
            return np.column_stack((rc[:, 0], rc[:, 1], np.full(len(rc), 2.0)))

        object.__setattr__(
            own,
            "frame",
            SimpleNamespace(spacing_rc=(1.0, 1.0), to_patient=to_patient),
        )
        return own

    small = source_record("small-source", "patellar_tendon", 3)
    large = source_record("large-source", "patellar_tendon", 7)
    quad = source_record("quad-source", "quadriceps_tendon", 4)
    axial = measured(enclosed_bodies())
    result = run.name_axial_extensor_sections([small, large, quad, axial], STUDY, None)

    assert len(result) == 4
    assert len(captured) == 1
    assert captured[0][0] is axial
    chosen = captured[0][1]
    assert chosen["patellar_tendon"]["status"] == "selected"
    assert chosen["quadriceps_tendon"]["status"] == "selected"
    assert conversions.count("large-source") == 1
    assert conversions.count("quad-source") == 1
    assert "small-source" not in conversions
    np.testing.assert_array_equal(
        large.arrays["a4_axial_patellar_tendon_source_lps"],
        chosen["patellar_tendon"]["points"],
    )

    tied = source_record("tied-source", "patellar_tendon", 7)
    conversions.clear()
    run.name_axial_extensor_sections([large, tied, quad, axial], STUDY, None)
    tied_sources = captured[-1][1]
    assert tied_sources["patellar_tendon"]["status"] == "tied"
    assert "large-source" not in conversions
    assert "tied-source" not in conversions


def test_enclosed_depth_cache_reuses_only_identical_plane_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, tuple[int, ...]]] = []

    def count_depth(plane: np.ndarray) -> np.ndarray:
        calls.append((plane.dtype.str, plane.shape))
        return np.zeros(plane.shape, dtype=float)

    monkeypatch.setattr(run, "enclosed_darkness", count_depth)
    plane = np.arange(12, dtype=np.float32).reshape(3, 4)
    with run.computing():
        run.enclosed_depth_of(plane, UID, 2)
        run.enclosed_depth_of(plane.copy(), UID, 2)
        changed_value = plane.copy()
        changed_value[0, 0] = -1.0
        run.enclosed_depth_of(changed_value, UID, 2)
        run.enclosed_depth_of(plane.astype(np.float64), UID, 2)
        run.enclosed_depth_of(plane.reshape(2, 6), UID, 2)

    assert calls == [
        (plane.dtype.str, plane.shape),
        (plane.dtype.str, plane.shape),
        (np.dtype(np.float64).str, plane.shape),
        (plane.dtype.str, (2, 6)),
    ]
