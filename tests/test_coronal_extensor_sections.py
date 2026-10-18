from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from scripts import run_interiors as run
from tests.test_extensor_cross_sections import (
    STUDY,
    UID,
    dark_patch,
    enclosed_bodies,
    lps_points,
    mapping_for,
    measured,
)


@pytest.fixture
def production_stubs(monkeypatch: pytest.MonkeyPatch) -> None:
    def frame_for(_series: Any, z: int) -> run.PlaneFrame:
        return run.PlaneFrame(
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
    monkeypatch.setattr(run, "lens_of", lambda *_args: (None, 1.0, None))
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


def source_group(points: np.ndarray) -> dict[str, Any]:
    return {
        "points": points,
        "metadata": {"series_uid": "identified-source", "support": "a1_objects"},
    }


@pytest.fixture
def coronal_stubs(monkeypatch: pytest.MonkeyPatch, production_stubs: None) -> None:
    monkeypatch.setattr(
        run,
        "field_of",
        lambda _series, _z, plane, _frame, _reading: SimpleNamespace(
            objects=np.zeros(np.shape(plane), dtype=np.int16)
        ),
    )


def source_observation(
    own: run.Measured, mask: np.ndarray, name: str, row: int = 0
) -> run.Observation:
    support = f"a4_axial_{name}_body"
    return run.Observation(
        object=name,
        provenance="native",
        kind="resolved",
        series_uid=own.record["series_uid"],
        view=tuple(own.record["view"]),
        slices=(2,),
        code="identified",
        count=int(mask.sum()),
        off_plane_mm=0.0,
        support=support,
        note="native body",
        artifact=f"{STUDY}/{UID}.npz",
        row=row,
        label=None,
    )


def coronal_sources(
    sagittal: np.ndarray | None,
    axial: np.ndarray | None,
) -> dict[str, dict[str, Any]]:
    if sagittal is None or axial is None:
        return {
            name: {"status": "unavailable"}
            for name in ("patellar_tendon", "quadriceps_tendon")
        }
    selected = {
        "status": "selected",
        "groups": {
            "sagittal": source_group(sagittal),
            "axial": source_group(axial),
        },
        "detail": {"status": "selected"},
    }
    return {
        name: {
            **selected,
            "groups": {
                group: source_group(points)
                for group, points in (
                    ("sagittal", sagittal),
                    ("axial", axial),
                )
            },
        }
        for name in ("patellar_tendon", "quadriceps_tendon")
    }


def test_common_native_body_is_not_the_two_projected_source_targets(
    monkeypatch: pytest.MonkeyPatch,
    coronal_stubs: None,
) -> None:
    volume = enclosed_bodies()
    dark_patch(volume, 2, (6, 6), size=5)
    dark_patch(volume, 2, (20, 20), size=9)
    own = measured(volume, view=("Coronal", "1", "1"))
    sources = coronal_sources(
        lps_points((6.1, 6.1, 2.0), (6.2, 6.2, 2.0)),
        lps_points((6.0, 6.0, 2.0)),
    )
    body_calls = 0
    real_bodies = run.dark_tendon_bodies

    def count_bodies(dark, free, spacing_rc, back_mm, inner_mm):
        nonlocal body_calls
        body_calls += 1
        return real_bodies(dark, free, spacing_rc, back_mm, inner_mm)

    monkeypatch.setattr(run, "dark_tendon_bodies", count_bodies)

    with run.computing():
        observations, missing = run.coronal_extensor_sections(own, sources, STUDY, None)

    assert missing == []
    assert body_calls == 1
    observed = next(row for row in observations if row.object == "patellar_tendon")
    assert observed.kind == "resolved"
    assert observed.provenance == "native"
    assert observed.label is None
    assert observed.slices == (2,)
    assert observed.support == "a4_coronal_patellar_tendon_body"
    body = own.arrays[observed.support]
    assert body.dtype == np.bool_
    assert body.shape == (1, *volume.shape[1:])
    assert int(body[observed.row].sum()) == observed.count
    assert own.arrays["a4_coronal_patellar_tendon_slices"][observed.row] == 2
    expected = np.zeros(volume.shape[1:], dtype=bool)
    expected[4:9, 4:9] = True
    expected[4, 4] = expected[4, 8] = expected[8, 4] = expected[8, 8] = False
    np.testing.assert_array_equal(body[observed.row], expected)

    sagittal_count = own.arrays["a4_coronal_patellar_tendon_profile_sagittal_count"]
    sagittal_rc = own.arrays["a4_coronal_patellar_tendon_profile_sagittal_rc"]
    sagittal_offsets = own.arrays["a4_coronal_patellar_tendon_profile_sagittal_offsets"]
    assert sagittal_count[2] == 2
    assert sagittal_offsets[2:4].tolist() == [0, 1]
    assert sagittal_rc.tolist() == [[6, 6]]


def test_separate_source_bodies_are_measured_empty_not_concurrent(
    coronal_stubs: None,
) -> None:
    volume = enclosed_bodies()
    dark_patch(volume, 2, (6, 6), size=5)
    dark_patch(volume, 2, (17, 17), size=5)
    own = measured(volume, view=("Coronal", "1", "1"))

    observations, missing = run.coronal_extensor_sections(
        own,
        coronal_sources(lps_points((6, 6, 2)), lps_points((17, 17, 2))),
        STUDY,
        None,
    )

    assert missing == []
    observed = next(row for row in observations if row.object == "patellar_tendon")
    assert observed.kind == "reading"
    assert observed.code == "abstain_no_common_dark_body_at_both_source_locations"
    assert observed.count == 0
    assert observed.label is None
    assert observed.support == "a4_coronal_patellar_tendon_body"
    assert not own.arrays[observed.support][observed.row].any()
    assert int(own.arrays["a4_coronal_patellar_tendon_target_sagittal"][0].sum()) == 1
    assert int(own.arrays["a4_coronal_patellar_tendon_target_axial"][0].sum()) == 1


def test_equal_common_bodies_abstain_with_a_named_tie(
    coronal_stubs: None,
) -> None:
    volume = enclosed_bodies()
    for center in ((6, 6), (20, 20)):
        dark_patch(volume, 2, center, size=5)
    own = measured(volume, view=("Coronal", "1", "1"))
    points = lps_points((6, 6, 2), (20, 20, 2))

    observations, missing = run.coronal_extensor_sections(
        own, coronal_sources(points, points.copy()), STUDY, None
    )

    assert not any(row.object == "patellar_tendon" for row in observations)
    assert any(
        row.object == "patellar_tendon"
        and row.code
        == "coronal_extensor_sections:tied_largest_common_bodies_at_slice_2"
        for row in missing
    )


def test_map_guide_is_tried_before_profile_fallback_and_skips_fallback_on_hit(
    coronal_stubs: None,
) -> None:
    volume = enclosed_bodies()
    dark_patch(volume, 2, (6, 6), size=5)
    dark_patch(volume, 3, (6, 6), size=5)
    own = measured(volume, view=("Coronal", "1", "1"))
    points = lps_points((6, 6, 2), (6, 6, 3))

    observations, missing = run.coronal_extensor_sections(
        own,
        coronal_sources(points, points.copy()),
        STUDY,
        mapping_for(point_lps=(6, 6, 2)),
    )

    assert not missing
    assert (
        next(row for row in observations if row.object == "patellar_tendon").kind
        == "resolved"
    )
    detail = own.record["coronal_extensor_sections"]["tendons"]["patellar_tendon"]
    assert detail["candidate_order"] == {
        "map_guided_first": [2],
        "source_profile_fallback": [3],
    }
    assert detail["candidate_slices"] == [2]
    assert detail["broadened_after_guided_miss"] is False
    assert "joint" not in own.record


def test_sources_on_different_slices_and_bad_projection_remain_unknown(
    monkeypatch: pytest.MonkeyPatch,
    coronal_stubs: None,
) -> None:
    volume = enclosed_bodies()
    dark_patch(volume, 2, (6, 6), size=5)
    dark_patch(volume, 3, (17, 17), size=5)
    unavailable = measured(volume, view=("Coronal", "1", "1"))
    unavailable_observations, unavailable_missing = run.coronal_extensor_sections(
        unavailable, coronal_sources(None, None), STUDY, None
    )
    assert not unavailable_observations
    assert any(
        row.object == "patellar_tendon"
        and row.code
        == "coronal_extensor_sections:required_patellar_tendon_source_unavailable"
        for row in unavailable_missing
    )

    separated = measured(volume, view=("Coronal", "1", "1"))
    observations, missing = run.coronal_extensor_sections(
        separated,
        coronal_sources(lps_points((6, 6, 2)), lps_points((17, 17, 3))),
        STUDY,
        None,
    )
    assert not observations
    assert any(
        "both_source_locations_not_on_slice_at_slice_2" in row.code for row in missing
    )
    assert any(
        "both_source_locations_not_on_slice_at_slice_3" in row.code for row in missing
    )

    malformed = measured(volume.copy(), view=("Coronal", "1", "1"))
    monkeypatch.setattr(
        run,
        "plane_frame",
        lambda _series, z: SimpleNamespace(
            origin_lps=np.asarray([0.0, 0.0, float(z)]),
            normal=lambda: np.asarray([0.0, 0.0, 1.0]),
            spacing_rc=(1.0, 1.0),
            to_native=lambda points: np.full((len(points), 2), np.nan),
        ),
    )
    malformed_observations, malformed_missing = run.coronal_extensor_sections(
        malformed,
        coronal_sources(lps_points((6, 6, 2)), lps_points((6, 6, 2))),
        STUDY,
        None,
    )
    assert not malformed_observations
    assert any(
        row.object == "patellar_tendon"
        and row.code
        == "coronal_extensor_sections:sagittal_source_projection_unavailable_at_slice_2"
        for row in malformed_missing
    )


def test_wrapper_reuses_sagittal_points_and_only_converts_selected_axial_source(
    monkeypatch: pytest.MonkeyPatch,
    production_stubs: None,
) -> None:
    captured: list[tuple[Any, ...]] = []

    def capture(own, sources, study_uid, mapping, orientation="axial"):
        captured.append((own, sources, study_uid, mapping, orientation))
        return [], []

    monkeypatch.setattr(run, "extensor_sections", capture)
    sagittal = measured(
        np.zeros((3, 28, 28), dtype=np.float32), view=("Sagittal", "0", "0")
    )
    sagittal.record["assignments"]["codes"]["patellar_tendon"] = "identified"
    sagittal_points = lps_points((6, 6, 2), (7, 6, 2))
    sagittal_metadata = {
        "code": "identified",
        "provenance": "native",
        "support": "a1_objects",
        "label": run.OBJECT_CODES["patellar_tendon"],
        "row": None,
    }
    sagittal.record["a4_axial_patellar_tendon_source"] = sagittal_metadata
    sagittal.arrays["a4_axial_patellar_tendon_source_lps"] = sagittal_points

    axial_records = []
    axial_said = []
    for uid, pixels in (("axial-small", 4), ("axial-large", 9)):
        own = measured(enclosed_bodies())
        own.record["series_uid"] = uid
        object.__setattr__(own.series.row, "series_uid", uid)
        mask = np.zeros((28, 28), dtype=bool)
        mask.flat[:pixels] = True
        own.arrays["a4_axial_patellar_tendon_body"] = mask[None, ...]
        own.arrays["a4_axial_patellar_tendon_slices"] = np.asarray([2], dtype=np.int32)
        axial_records.append(own)
        axial_said.append(([source_observation(own, mask, "patellar_tendon")], []))

    converted: list[str] = []

    def frame_for(series, _z):
        uid = series.row.series_uid

        def to_patient(rc):
            converted.append(uid)
            return np.column_stack((rc[:, 0], rc[:, 1], np.full(len(rc), 2.0)))

        return SimpleNamespace(spacing_rc=(1.0, 1.0), to_patient=to_patient)

    monkeypatch.setattr(run, "plane_frame", frame_for)
    coronal = measured(enclosed_bodies(), view=("Coronal", "1", "1"))
    outputs = run.name_coronal_extensor_sections(
        [sagittal, *axial_records, coronal],
        [([], []), *axial_said, ([], [])],
        STUDY,
        None,
    )

    assert len(outputs) == 4
    own, sources, study_uid, mapping, orientation = captured[0]
    assert own is coronal
    assert study_uid == STUDY
    assert mapping is None
    assert orientation == "coronal"
    selected = sources["patellar_tendon"]
    assert selected["groups"]["sagittal"]["points"] is sagittal_points
    assert selected["groups"]["sagittal"]["metadata"] is sagittal_metadata
    assert converted == ["axial-large"]
