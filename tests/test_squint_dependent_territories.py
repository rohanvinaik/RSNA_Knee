"""Dependents placed from structural bone anchors (lane W10).

Fixture: one coronal series, 9 slices x 24 x 24 tiles of 10 mm, with real DICOM
frames, a slice-shifted signal pattern inside the leg and two tiles of air round
it. Tile centres are x = -115 + 10c, y = -40 + 10z, z = 115 - 10r (LPS mm). The
series carries a W1-shape leg map (the air ring outside the leg), and direct
calls pass the matching foreground, so the leg prior is explicit in every test.
"""

from __future__ import annotations

import json
import sys
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest

import knee.diagnosis.squint_anatomy_locator as anatomy_locator
import knee.diagnosis.squint_locator as locator
from knee.collapse.anatomy_map import ideal_vector
from knee.collapse.physical import PlaneFrame
from knee.collapse.squint_stack import SquintStack, tile_centres_lps
from knee.diagnosis import squint_pipeline
from knee.diagnosis import squint_profiles as writer
from knee.diagnosis.squint_identity import PRIOR_ONLY
from knee.diagnosis.squint_interfaces import (
    ANCHOR_SCHEMA,
    LEG_INSIDE,
    LEG_MAP_SCHEMA,
    LEG_OUTSIDE,
    LEG_UNKNOWN,
    ROLE_CONTEXT,
    ROLE_OBJECT,
    ROLE_OUTSIDE_LEG,
    TERRITORY_SCHEMA,
    anchor_code,
    leg_map_code,
    territory_code,
)

STUDY = "1.2.826.0.1.3680043.8.498.w10.study"
CORONAL = "1.2.826.0.1.3680043.8.498.w10.coronal"
VIEW = {"orientation": "Coronal", "fluid_sensitive": "1", "fat_suppression": "1"}
DEPTH, ROWS, COLS = 9, 24, 24
TILE_PX, PIXEL_MM = 4, 2.5
AIR = 2
ORIENTATION = np.asarray([1.0, 0.0, 0.0, 0.0, 0.0, -1.0])


def _air() -> np.ndarray:
    rows, cols = np.indices((ROWS, COLS))
    ring = (rows < AIR) | (rows >= ROWS - AIR) | (cols < AIR) | (cols >= COLS - AIR)
    return np.broadcast_to(ring, (DEPTH, ROWS, COLS)).copy()


def _leg_map(codes: np.ndarray | None = None) -> dict:
    if codes is None:
        codes = np.where(_air(), LEG_OUTSIDE, LEG_INSIDE).astype(np.int8)
    share = np.ones(codes.shape, dtype=np.float32)
    share[codes == LEG_OUTSIDE] = 0.0
    share[(codes != LEG_OUTSIDE) & (codes != LEG_INSIDE)] = np.nan
    value = {
        "schema": LEG_MAP_SCHEMA,
        "study_uid": STUDY,
        "series_uid": CORONAL,
        "tile_mm": 10.0,
        "codes": codes,
        "leg_share": share,
        "rule": "fixture:air-ring-outside",
        "provenance": {"fixture": True},
    }
    assert leg_map_code(value, grid_shape=(DEPTH, ROWS, COLS)) == "valid"
    return value


def _series(*, slices_differ: bool = True) -> dict:
    positions = np.asarray(
        [[-118.75, -40.0 + 10.0 * z, 118.75] for z in range(DEPTH)], dtype=np.float64
    )
    spacing = np.asarray([[PIXEL_MM, PIXEL_MM]] * DEPTH, dtype=np.float64)
    bounds = np.zeros((ROWS, COLS, 4), dtype=np.int64)
    for r in range(ROWS):
        for c in range(COLS):
            bounds[r, c] = (
                r * TILE_PX,
                (r + 1) * TILE_PX,
                c * TILE_PX,
                (c + 1) * TILE_PX,
            )
    centres = np.stack(
        [
            tile_centres_lps(
                PlaneFrame.from_dicom(positions[z], ORIENTATION, spacing[z]), bounds
            )
            for z in range(DEPTH)
        ]
    )
    rows, cols = np.indices((ROWS, COLS))
    # Each slice's pattern is shifted, so no two slices read alike, unless asked.
    shift = 1.0 if slices_differ else 0.0
    median = np.stack(
        [
            120.0
            + 40.0 * np.sin((rows + 0.9 * shift * z) / 2.7)
            + 25.0 * np.cos((cols - 0.7 * shift * z) / 3.1)
            for z in range(DEPTH)
        ]
    )
    minimum = median - 40.0
    maximum = median + 60.0
    air = _air()
    median[air] = 0.5
    minimum[air] = 0.0
    maximum[air] = 3.0
    coverage = np.ones_like(median)
    for array in (median, minimum, maximum, coverage, bounds, centres):
        array.flags.writeable = False
    stack = SquintStack(
        series_uid=CORONAL,
        code="present",
        why="fixture",
        tile_mm=10.0,
        tile_shape_rc=(TILE_PX, TILE_PX),
        bounds_rc=bounds,
        median=median,
        minimum=minimum,
        maximum=maximum,
        coverage=coverage,
        centres_lps=centres,
    )
    values = writer._metrics(stack)
    available = writer._metric_availability(stack, values)
    calibration, codes = writer._calibrate(values, available)
    return {
        "series_uid": CORONAL,
        "view": dict(VIEW),
        "shape": (DEPTH, ROWS * TILE_PX, COLS * TILE_PX),
        "geometry": {
            "orientation": np.asarray([ORIENTATION] * DEPTH),
            "position": positions,
            "spacing": spacing,
        },
        "stack": stack,
        "metric_values": values,
        "metric_available": available,
        "metric_codes": codes,
        "calibration": calibration,
        "source": {
            "api": "fixture",
            "study_uid": STUDY,
            "series_uid": CORONAL,
            "tile_mm": 10.0,
            "procedure": writer._PROCEDURE,
            "geometry_status": "available",
            "calibration": calibration,
            "native_slice_paths": (),
        },
        "native_series": None,
        "leg_map": _leg_map(),
    }


def _foreground(series: dict) -> np.ndarray:
    """The leg eligibility a locator reads from the series' leg map."""
    return np.asarray(series["leg_map"]["codes"]) != LEG_OUTSIDE


def _leg_bounds(series: dict):
    return locator._current_leg_frame_prior([series], {id(series): _foreground(series)})


def _study(series: dict, **extra) -> dict:
    return {
        "study_uid": STUDY,
        "series": [series],
        "leg_maps": {CORONAL: series["leg_map"]},
        **extra,
    }


def _plane(orientation: str, normal, offset: float, *, series_uid: str, slice_index):
    return {
        "orientation": orientation,
        "outcome": "selected",
        "series_uid": series_uid,
        "slice": slice_index,
        "normal": [float(value) for value in normal],
        "offset_mm": float(offset),
        "precision_mm": 1.25,
        "reason": "fixture key plane",
        "provenance": "fixture",
        "candidates": [],
    }


def _anchor_territory(bone: str, box: tuple[int, ...], *, selected: bool = True):
    """An anchor_structure territory over a tile box with one tile of context."""
    z0, _z1, r0, r1, c0, c1 = box
    t0, t1 = max(0, r0 - 1), min(ROWS, r1 + 1)
    u0, u1 = max(0, c0 - 1), min(COLS, c1 + 1)
    roles = np.full((1, t1 - t0, u1 - u0), ROLE_CONTEXT, dtype=np.int8)
    roles[0, r0 - t0 : r1 - t0, c0 - u0 : c1 - u0] = ROLE_OBJECT
    share = np.full(roles.shape, np.nan, dtype=np.float32)
    share[roles == ROLE_OBJECT] = 1.0
    return {
        "schema": TERRITORY_SCHEMA,
        "study_uid": STUDY,
        "series_uid": CORONAL,
        "subject": bone,
        "origin": "anchor_structure",
        "tile_window": [z0, z0 + 1, t0, t1, u0, u1],
        "roles": roles,
        "object_share": share,
        "native_support": {
            "mask": np.ones((1, 4, 4), dtype=np.bool_),
            "slices": [z0],
            "offset_rc": (r0 * TILE_PX, c0 * TILE_PX),
        },
        "anchors": [],
        "relation": None,
        "key_planes": {
            "coronal": {
                "series_uid": CORONAL,
                "slice": z0,
                "outcome": "selected" if selected else "not_the_selected_key_plane",
            }
        },
        "provenance": {"fixture": True},
    }


def _complete_anchor(bone: str, point, territories=()):
    p = [float(value) for value in point]
    return {
        "schema": ANCHOR_SCHEMA,
        "study_uid": STUDY,
        "subject": bone,
        "status": "complete",
        "territories": list(territories),
        "key_planes": {
            "sagittal": _plane(
                "sagittal",
                (1, 0, 0),
                p[0],
                series_uid="fixture-sagittal",
                slice_index=0,
            ),
            "coronal": _plane(
                "coronal", (0, 1, 0), p[1], series_uid=CORONAL, slice_index=2
            ),
            "axial": _plane(
                "axial", (0, 0, 1), p[2], series_uid="fixture-axial", slice_index=0
            ),
        },
        "reference_lps": p,
        "breadth_mm": None,
        "producer": "fixture-anchor-producer",
        "cost": {"seconds": 0.0},
    }


def _unavailable_anchor(bone: str, status: str = "unavailable"):
    return {
        "schema": ANCHOR_SCHEMA,
        "study_uid": STUDY,
        "subject": bone,
        "status": status,
        "territories": [],
        "key_planes": {},
        "reference_lps": None,
        "breadth_mm": None,
        "producer": "fixture-anchor-producer",
        "cost": {},
    }


def _lps(subject: str, origin: str = "femur") -> np.ndarray:
    """The authored map vector origin -> subject for a left knee, in LPS mm."""
    vector = ideal_vector(origin, subject)
    assert vector is not None
    medial, posterior, superior = vector.anatomical_mm
    return np.asarray((-medial, posterior, superior), dtype=np.float64)


def _femur_point(series: dict, tile=(4, 11, 12), subject="medial_meniscus"):
    """A femur reference whose map vector puts ``subject`` on a tile centre."""
    return series["stack"].centres_lps[tile] - _lps(subject)


def _case(case_id: str, subject: str, series: dict, window: tuple[int, ...]):
    return {
        "case_id": case_id,
        "study_uid": "other-study",
        "subject": subject,
        "condition_calls": {},
        "profile": writer.profile_window(dict(series), window, subject=subject),
        "regions": [
            {
                "view": dict(VIEW),
                "extent_source": "retained_object_support",
                "series_uid": CORONAL,
                "source_window": list(window),
            }
        ],
    }


def _memory(series: dict, windows: dict[str, tuple[int, ...]]) -> dict:
    return {
        "objects": sorted(windows),
        "cases": [
            _case(f"case-{subject}", subject, series, window)
            for subject, window in windows.items()
        ],
    }


def _geometry(series: dict, anchor: dict) -> dict:
    state = anatomy_locator.study_anchors(
        {"study_uid": STUDY, "anchors": {anchor["subject"]: anchor}},
        {CORONAL: series},
    )
    return state["geometry"][anchor["subject"]]


def _propose(series: dict, subject: str, anchors: dict, **extra) -> dict:
    foreground = extra.pop("foreground", None)
    if foreground is None:
        foreground = _foreground(series)
    return anatomy_locator.dependent_territories(
        series,
        subject,
        study_uid=STUDY,
        anchors=anchors,
        leg_bounds_lps=locator._current_leg_frame_prior(
            [series], {id(series): foreground}
        ),
        foreground=foreground,
        knee_side=extra.pop("knee_side", "left"),
        **extra,
    )


def _signature(territory: dict) -> tuple:
    return (tuple(territory["tile_window"]), territory["roles"].tobytes())


def _shifted(territory: dict, rows: int) -> tuple:
    z0, z1, r0, r1, c0, c1 = territory["tile_window"]
    return ((z0, z1, r0 + rows, r1 + rows, c0, c1), territory["roles"].tobytes())


def _no_producer(monkeypatch):
    monkeypatch.setitem(sys.modules, "knee.diagnosis.squint_anchors", None)


def test_moved_bone_anchor_moves_dependent_territories_by_the_relation():
    series = _series()
    point = _femur_point(series)

    def propose(anchor_point):
        anchor = _complete_anchor("femur", anchor_point)
        return _propose(series, "medial_meniscus", {"femur": _geometry(series, anchor)})

    first = propose(point)
    moved = propose(point + np.asarray((0.0, 0.0, -20.0)))
    assert first["origin"] == moved["origin"] == "anatomical_relation"
    assert first["territories"]
    # Must change: 20 mm inferior is two tile rows down, for every candidate.
    assert {_signature(t) for t in moved["territories"]} == {
        _shifted(t, 2) for t in first["territories"]
    }
    for territory in first["territories"] + moved["territories"]:
        assert territory_code(territory, grid_shape=(DEPTH, ROWS, COLS)) == "valid"
        assert territory["origin"] == "anatomical_relation"
        assert np.isnan(territory["object_share"]).all()
        assert set(np.unique(territory["roles"])) <= {ROLE_OBJECT, ROLE_CONTEXT}
        assert [row["anchor"] for row in territory["anchors"]] == ["femur"]
        assert territory["relation"]["authored_relations"] == [
            {
                "predicate": "between",
                "targets": ["femur", "tibia"],
                "qualifier": "medial compartment",
                "source": "docs/OBJECTS_AND_CONDITIONS.md §4",
            }
        ]
    expected = np.asarray(first["territories"][0]["anchors"][0]["expected_point_lps"])
    moved_expected = np.asarray(
        moved["territories"][0]["anchors"][0]["expected_point_lps"]
    )
    np.testing.assert_allclose(moved_expected - expected, (0.0, 0.0, -20.0))
    np.testing.assert_allclose(
        expected, series["stack"].centres_lps[4, 11, 12], atol=1e-9
    )
    # Must not change: moving the anchor changes where, never what the candidate is.
    assert [t["roles"].shape for t in first["territories"]] == [
        t["roles"].shape for t in moved["territories"]
    ]
    assert first["territories"][0]["relation"] == moved["territories"][0]["relation"]


def test_resemblance_located_bone_never_moves_a_dependent(monkeypatch):
    _no_producer(monkeypatch)
    series = _series()
    femur = _complete_anchor(
        "femur",
        _femur_point(series),
        [_anchor_territory("femur", (2, 3, 6, 10, 13, 20))],
    )
    femur_geometry = {"femur": _geometry(series, femur)}
    windows = [
        anatomy_locator._object_window(t)
        for t in _propose(series, "tibia", femur_geometry)["territories"]
    ]
    # Two candidates on different slices: the tibia's located plane differs, so
    # a dependent placed from it would move.
    first_tibia, second_tibia = (0, 1, 10, 15, 13, 22), (6, 7, 10, 15, 13, 22)
    assert first_tibia in windows and second_tibia in windows

    def locate(tibia_window):
        study = _study(
            series,
            knee_side="left",
            anchors={"femur": femur, "tibia": _unavailable_anchor("tibia")},
        )
        memory = _memory(
            series,
            {
                "femur": (0, 1, 3, 6, 3, 6),
                "tibia": tibia_window,
                "medial_meniscus": (4, 5, 11, 12, 10, 15),
            },
        )
        return locator.locate_objects(study, memory)["objects"]

    first = locate(first_tibia)
    second = locate(second_tibia)
    # Must change: the tibia's own case moves which candidate resembles it.
    assert [r["window"] for r in first["tibia"]["regions"]] == [first_tibia]
    assert [r["window"] for r in second["tibia"]["regions"]] == [second_tibia]
    assert first["tibia"]["evidence"]["location_route"] == (
        "anatomical_relation_from_structural_anchors"
    )
    # Must not change: an unanchored bone anchors nothing, so the meniscus's
    # candidates and choice are the same wherever the tibia was located.
    meniscus = first["medial_meniscus"]
    assert meniscus["territories"] == second["medial_meniscus"]["territories"]
    assert (
        meniscus["evidence"]["candidate_territories"]
        == second["medial_meniscus"]["evidence"]["candidate_territories"]
    )
    assert meniscus["evidence"]["structural_anchors"] == {"femur": "complete"}
    from_femur_alone = _propose(series, "medial_meniscus", femur_geometry)
    assert meniscus["evidence"]["candidate_territories"][CORONAL][
        "candidate_object_windows"
    ] == [
        list(anatomy_locator._object_window(t)) for t in from_femur_alone["territories"]
    ]
    for territory in meniscus["territories"]:
        assert [row["anchor"] for row in territory["anchors"]] == ["femur"]


def test_anchored_bone_is_located_by_its_anchor_not_by_resemblance(monkeypatch):
    _no_producer(monkeypatch)
    series = _series()
    point = _femur_point(series)
    box = (2, 3, 6, 10, 13, 20)
    femur = _complete_anchor(
        "femur",
        point,
        [
            _anchor_territory("femur", box),
            _anchor_territory("femur", (5, 6, 6, 9, 13, 19), selected=False),
        ],
    )
    # The stored femur case resembles another place entirely.
    memory = _memory(series, {"femur": (7, 8, 14, 18, 3, 7)})
    located = locator.locate_objects(_study(series, anchors={"femur": femur}), memory)[
        "objects"
    ]["femur"]

    assert located["status"] == "proposal"
    assert [region["window"] for region in located["regions"]] == [box]
    assert located["evidence"]["location_route"] == "structural_anchor"
    assert located["evidence"]["resemblance_applied"] is False
    assert located["evidence"]["candidate_profiles_compared"] == 0
    assert located["evidence"]["reading_territories"] == (
        "territories_on_selected_key_planes"
    )
    assert len(located["evidence"]["other_anchor_territories"]) == 1
    expected = writer.profile_window(dict(series), box, subject="femur")
    assert located["profile"]["banks"] == expected["banks"]
    record = located["territories"][0]
    assert record["origin"] == "anchor_structure"
    assert record["native_support"] is None
    assert record["native_support_address"]["support_count"] == 16
    rebuilt = anatomy_locator.territory_from_record(record)
    np.testing.assert_array_equal(rebuilt["roles"], femur["territories"][0]["roles"])
    reference = located["evidence"]["spatial_constraints"]["reference"]
    assert reference["status"] == "complete"
    np.testing.assert_allclose(reference["point_lps"], point)


def test_an_anchor_support_given_twice_is_read_once(monkeypatch):
    _no_producer(monkeypatch)
    series = _series()
    point = _femur_point(series)
    box = (2, 3, 6, 10, 13, 20)
    once = _complete_anchor("femur", point, [_anchor_territory("femur", box)])
    twice = _complete_anchor(
        "femur",
        point,
        [_anchor_territory("femur", box), _anchor_territory("femur", box)],
    )
    memory = _memory(series, {"femur": box})

    def femur(anchor):
        study = _study(series, anchors={"femur": anchor})
        return locator.locate_objects(study, memory)["objects"]["femur"]

    single, double = femur(once), femur(twice)
    assert double["evidence"]["duplicate_reading_territories"] == 1
    assert single["evidence"]["duplicate_reading_territories"] == 0
    assert double["profile"]["banks"] == single["profile"]["banks"]
    assert [r["window"] for r in double["regions"]] == [box]
    assert len(double["evidence"]["other_anchor_territories"]) == 1


def test_partial_anchor_keeps_its_missing_plane_missing(monkeypatch):
    _no_producer(monkeypatch)
    series = _series()
    partial = {
        **_unavailable_anchor("femur", status="partial"),
        "key_planes": {
            # A selected plane given only by its address takes the acquisition frame.
            "coronal": {"series_uid": CORONAL, "slice": 4, "outcome": "selected"},
            "sagittal": {
                "orientation": "sagittal",
                "outcome": "tied",
                "candidates": [["a", 1], ["b", 2]],
            },
        },
    }
    assert anchor_code(partial) == "valid"
    state = anatomy_locator.study_anchors(
        {"study_uid": STUDY, "anchors": {"femur": partial}}, {CORONAL: series}
    )
    assert state["route"] == "structural_anchors"
    planes = state["geometry"]["femur"]["planes"]
    assert set(planes) == {"coronal", "sagittal"}
    assert planes["sagittal"]["outcome"] == "tied"
    coronal = planes["coronal"]
    assert coronal["outcome"] == "selected"
    assert coronal["geometry_source"] == "acquisition_frame_at_anchor_slice"
    normal = np.asarray(coronal["normal"])
    # Slice 4 lies at y = 0 mm.
    assert abs(abs(normal[1]) - 1.0) < 1e-12
    assert abs(coronal["offset_mm"]) < 1e-9
    assert state["geometry"]["femur"]["reference"]["point_lps"] is None

    built = _propose(series, "medial_meniscus", state["geometry"])
    assert built["territories"]
    hypothesis = built["proposal"]["provenance"]["hypotheses"][0]
    assert hypothesis["kind"] == "partial_native_planes_guided_prior"
    assert [plane["orientation"] for plane in hypothesis["selected_native_planes"]] == [
        "coronal"
    ]
    projected = np.asarray(hypothesis["projected_anchor_prior_lps"])
    assert abs(projected[1]) < 1e-9
    for territory in built["territories"]:
        assert territory["anchors"][0]["anchor_observation_status"] == "partial"
        assert territory["anchors"][0]["prior_only"] is True


def test_unavailable_anchors_keep_the_existing_route_by_name(monkeypatch):
    _no_producer(monkeypatch)
    series = _series()
    memory = _memory(
        series,
        {
            "femur": (2, 3, 6, 10, 13, 20),
            "tibia": (3, 4, 10, 15, 13, 21),
            "medial_meniscus": (4, 5, 11, 12, 10, 15),
        },
    )
    without = locator.locate_objects(_study(series, knee_side="left"), memory)
    supplied = locator.locate_objects(
        _study(
            series,
            knee_side="left",
            anchors={
                "femur": _unavailable_anchor("femur"),
                "tibia": _unavailable_anchor("tibia", status="conflict"),
            },
        ),
        memory,
    )
    assert without["evidence"]["anchors"]["source"]["status"] == (
        "anchor_producer_unavailable"
    )
    assert supplied["evidence"]["anchors"]["route"] == "existing_finite_route"
    assert supplied["evidence"]["anchors"]["source"] == {
        "status": "supplied_with_study",
        "route_reason": "no_usable_structural_anchor",
    }
    for result in (without, supplied):
        for located in result["objects"].values():
            assert "territories" not in located
            assert located["evidence"]["location_route"] == "existing_finite_route"
    # Today's path, by name: the dependent is placed from the bones as before.
    meniscus = supplied["objects"]["medial_meniscus"]
    assert meniscus["status"] == "proposal"
    hypotheses = meniscus["evidence"]["proposal_sources"][0]["provenance"]["hypotheses"]
    assert {row["anchor"] for row in hypotheses} <= {"femur", "tibia"}
    strip = ("anchors", "anchor_source", "location_route")

    def comparable(result):
        objects = {
            name: {
                **row,
                "evidence": {
                    k: v for k, v in row["evidence"].items() if k not in strip
                },
            }
            for name, row in result["objects"].items()
        }
        return json.dumps(objects, sort_keys=True, default=str)

    # Unavailable anchors change nothing on the existing route but its name.
    assert comparable(without) == comparable(supplied)


def test_conflicting_anchor_is_observed_as_a_hypothesis_but_never_anchors(monkeypatch):
    _no_producer(monkeypatch)
    series = _series()
    tibia_point = series["stack"].centres_lps[4, 11, 12] - _lps(
        "medial_meniscus", "tibia"
    )
    study = _study(
        series,
        knee_side="left",
        anchors={
            "femur": {
                **_unavailable_anchor("femur", status="conflict"),
                "territories": [_anchor_territory("femur", (2, 3, 6, 10, 13, 20))],
            },
            "tibia": _complete_anchor(
                "tibia",
                tibia_point,
                [_anchor_territory("tibia", (3, 4, 12, 16, 9, 17))],
            ),
        },
    )
    memory = _memory(
        series,
        {"femur": (2, 3, 6, 10, 13, 20), "medial_meniscus": (4, 5, 11, 12, 10, 15)},
    )
    state = anatomy_locator.study_anchors(study, {CORONAL: series})
    assert set(state["usable"]) == {"tibia"}
    assert set(state["geometry"]) == {"tibia"}
    assert state["hypotheses"]["femur"][0]["territory"] is (
        study["anchors"]["femur"]["territories"][0]
    )

    result = locator.locate_objects(study, memory)
    femur = result["objects"]["femur"]
    assert result["evidence"]["anchors"]["bones"]["femur"]["status"] == "conflict"
    assert femur["evidence"]["location_route"] == (
        "anatomical_relation_from_structural_anchors"
    )
    assert femur["evidence"]["structural_anchors"] == {"tibia": "complete"}
    assert femur["profile"] is not None
    [held] = femur["evidence"]["selected_withheld_support_hypotheses"]
    assert held["reason"] == "anchor_not_established"
    assert held["territory"] == anatomy_locator.territory_record(
        study["anchors"]["femur"]["territories"][0]
    )
    # Retaining the reader's original source does not establish its proposed identity.
    assert femur["territories"] == [held["territory"]]
    context = squint_pipeline._identity_contexts(result["objects"])["femur"]
    assert context["basis"] == PRIOR_ONLY
    assert context["removed_by_structure"] == []
    assert "arrangement" not in context["supporting_observations"]

    # The conflict's support is observable, but only the tibia places the meniscus.
    meniscus = result["objects"]["medial_meniscus"]
    assert meniscus["territories"]
    for territory in meniscus["territories"]:
        assert [row["anchor"] for row in territory["anchors"]] == ["tibia"]


def _assert_inside_the_leg(built: dict, outside: np.ndarray) -> int:
    reaching = 0
    for territory in built["territories"]:
        z0, _z1, r0, r1, c0, c1 = territory["tile_window"]
        roles = territory["roles"][0]
        out = outside[z0, r0:r1, c0:c1]
        assert np.all(roles[out] == ROLE_OUTSIDE_LEG)
        assert not np.any(out[(roles == ROLE_OBJECT) | (roles == ROLE_CONTEXT)])
        window = anatomy_locator._object_window(territory)
        assert not outside[
            window[0] : window[1], window[2] : window[3], window[4] : window[5]
        ].any()
        assert territory["provenance"]["outside_leg_tiles_in_object_box"] == 0
        reaching += int(np.any(out))
    return reaching


def test_a_dependent_never_takes_a_territory_outside_the_leg():
    series = _series()
    # Put the meniscus's expected place one tile inside the leg's left edge.
    point = _femur_point(series, tile=(4, 11, AIR + 1))
    anchors = {"femur": _geometry(series, _complete_anchor("femur", point))}
    from_map = _propose(series, "medial_meniscus", anchors)
    assert from_map["leg_prior"]["source"] == "leg_map"
    assert _assert_inside_the_leg(from_map, _air()), "the windows must reach the air"
    # The same rule without a leg map reads the locator's own foreground.
    unmapped = {k: v for k, v in series.items() if k != "leg_map"}
    from_foreground = _propose(unmapped, "medial_meniscus", anchors, foreground=~_air())
    assert from_foreground["leg_prior"]["source"] == "squint_foreground_proxy"
    assert _assert_inside_the_leg(from_foreground, _air())
    assert [_signature(t) for t in from_foreground["territories"]] == [
        _signature(t) for t in from_map["territories"]
    ]
    # Proposals reaching into the air are trimmed to their places in the leg.
    assert from_map["proposed_window_count"] >= len(from_map["territories"])


def test_leg_map_outside_refuses_and_unknown_stays_in_scope():
    series = _series()
    point = _femur_point(series)
    codes = np.asarray(series["leg_map"]["codes"]).copy()
    # Every slice-4 candidate lies wholly in this block; slice 6's reach unread tiles.
    codes[4, 9:14, 6:18] = LEG_OUTSIDE
    codes[6, 9:14, 9:16] = LEG_UNKNOWN
    series["leg_map"] = _leg_map(codes)
    built = _propose(
        series,
        "medial_meniscus",
        {"femur": _geometry(series, _complete_anchor("femur", point))},
        # A foreground that disagrees with the map, so windows land in its outside.
        foreground=np.ones((DEPTH, ROWS, COLS), dtype=np.bool_),
    )
    assert built["leg_prior"]["source"] == "leg_map"
    assert built["refusals"].get("relation_window_outside_leg", 0) > 0
    kept_unknown = 0
    for territory in built["territories"]:
        z0, _z1, r0, r1, c0, c1 = territory["tile_window"]
        roles = territory["roles"][0]
        leg = codes[z0, r0:r1, c0:c1]
        assert not np.any(roles[leg == LEG_OUTSIDE] != ROLE_OUTSIDE_LEG)
        kept_unknown += int(np.any(roles[leg == LEG_UNKNOWN] == ROLE_OBJECT))
    # Unknown is never outside: an unread tile keeps its expected role.
    assert kept_unknown


def test_anchor_checks_name_their_refusals(monkeypatch):
    _no_producer(monkeypatch)
    series = _series()
    point = _femur_point(series)
    stranger = {**_complete_anchor("tibia", point), "study_uid": "another-study"}
    stray = _anchor_territory("femur", (2, 3, 6, 10, 13, 20))
    stray["series_uid"] = "not-in-this-study"
    femur = _complete_anchor(
        "femur", point, [stray, _anchor_territory("femur", (2, 3, 6, 10, 13, 20))]
    )
    state = anatomy_locator.study_anchors(
        {
            "study_uid": STUDY,
            "anchors": {"femur": femur, "tibia": stranger, "joint": femur},
        },
        {CORONAL: series},
    )
    assert state["bones"]["tibia"]["code"] == "anchor_identity_mismatch"
    assert state["bones"]["tibia"]["status"] == "unavailable"
    assert state["bones"]["joint"]["code"] == "anchor_subject_not_a_bone"
    assert state["bones"]["patella"]["code"] == "anchor_not_returned"
    assert state["bones"]["femur"]["refused_territories"] == {
        "territory_series_not_in_study": 1
    }
    assert state["bones"]["femur"]["territory_count"] == 1
    assert set(state["usable"]) == {"femur"}


def test_producer_is_called_once_and_its_failure_is_named(monkeypatch):
    series = _series()
    point = _femur_point(series)
    calls = []
    producer = ModuleType("knee.diagnosis.squint_anchors")

    def find_anchors(study):
        calls.append(study["study_uid"])
        return {
            "femur": _complete_anchor(
                "femur", point, [_anchor_territory("femur", (2, 3, 6, 10, 13, 20))]
            )
        }

    producer.find_anchors = find_anchors
    monkeypatch.setitem(sys.modules, producer.__name__, producer)
    memory = _memory(
        series,
        {"femur": (2, 3, 6, 10, 13, 20), "medial_meniscus": (4, 5, 11, 12, 10, 15)},
    )
    study = _study(series, knee_side="left")
    result = locator.locate_objects(study, memory)
    assert calls == [STUDY]
    assert result["evidence"]["anchors"]["source"]["status"] == "produced"
    assert result["objects"]["medial_meniscus"]["status"] == "proposal"
    assert json.dumps(result["objects"], allow_nan=False, sort_keys=True)

    def broken(_study):
        raise ValueError("fixture failure")

    producer.find_anchors = broken
    failed = locator.locate_objects(study, memory)
    assert failed["evidence"]["anchors"]["route"] == "existing_finite_route"
    assert failed["evidence"]["anchors"]["source"]["status"] == (
        "anchor_producer_failed:ValueError"
    )
    producer.find_anchors = find_anchors
    calls.clear()
    late = locator.locate_objects(study, memory, deadline=0.0)
    assert calls == []
    assert late["evidence"]["anchors"]["source"]["status"] == (
        "deadline_before_anchor_search"
    )
    assert {row["evidence"]["reason"] for row in late["objects"].values()} == {
        "deadline_before_search"
    }


def test_supplied_anchors_past_the_deadline_keep_their_shape(monkeypatch):
    _no_producer(monkeypatch)
    series = _series()
    study = _study(
        series,
        anchors={
            "femur": _complete_anchor(
                "femur",
                _femur_point(series),
                [_anchor_territory("femur", (2, 3, 6, 10, 13, 20))],
            )
        },
    )
    memory = _memory(
        series,
        {"femur": (2, 3, 6, 10, 13, 20), "medial_meniscus": (4, 5, 11, 12, 10, 15)},
    )
    late = locator.locate_objects(study, memory, deadline=0.0)
    assert late["evidence"]["anchors"]["route"] == "structural_anchors"
    for located in late["objects"].values():
        assert located["evidence"]["reason"] == "deadline_before_search"
        assert located["territories"] == []
        assert located["regions"] == []


def test_located_territories_are_json_records_that_rebuild(monkeypatch):
    _no_producer(monkeypatch)
    series = _series()
    study = _study(
        series,
        knee_side="left",
        anchors={
            "femur": _complete_anchor(
                "femur",
                _femur_point(series),
                [_anchor_territory("femur", (2, 3, 6, 10, 13, 20))],
            )
        },
    )
    memory = _memory(
        series,
        {"femur": (2, 3, 6, 10, 13, 20), "medial_meniscus": (4, 5, 11, 12, 10, 15)},
    )
    result = locator.locate_objects(study, memory)
    text = json.dumps(result["objects"], allow_nan=False, sort_keys=True)
    meniscus = json.loads(text)["medial_meniscus"]
    assert meniscus["status"] == "proposal"
    assert len(meniscus["territories"]) == len(meniscus["regions"])
    for record, region in zip(
        meniscus["territories"], meniscus["regions"], strict=True
    ):
        territory = anatomy_locator.territory_from_record(record)
        assert territory["origin"] == "anatomical_relation"
        assert np.isnan(territory["object_share"]).all()
        assert anatomy_locator._object_window(territory) == tuple(region["window"])
        assert anatomy_locator.territory_record(territory) == {
            **record,
            "native_support": None,
        }
    for bad in ({}, {**meniscus["territories"][0], "roles": [[[9]]]}):
        try:
            anatomy_locator.territory_from_record(bad)
        except ValueError:
            continue
        raise AssertionError("a malformed record must be refused")


def test_explicit_ties_stay_ties_on_the_structural_route(monkeypatch):
    _no_producer(monkeypatch)
    # Every slice reads alike, so same-box candidates on other slices tie exactly.
    series = _series(slices_differ=False)
    femur = _complete_anchor(
        "femur",
        _femur_point(series),
        [_anchor_territory("femur", (2, 3, 6, 10, 13, 20))],
    )
    tied_box = (10, 15, 13, 22)
    candidates = [
        anatomy_locator._object_window(t)
        for t in _propose(series, "tibia", {"femur": _geometry(series, femur)})[
            "territories"
        ]
    ]
    tied = sorted(w for w in candidates if w[2:] == tied_box)
    assert len(tied) == 3
    memory = _memory(series, {"femur": (0, 1, 3, 6, 3, 6), "tibia": tied[1]})
    tibia = locator.locate_objects(
        _study(series, knee_side="left", anchors={"femur": femur}), memory
    )["objects"]["tibia"]
    # A tie is kept whole and named; no candidate is picked to break it.
    assert tibia["status"] == "proposal"
    assert sorted(r["window"] for r in tibia["regions"]) == tied
    assert len(tibia["territories"]) == 3
    assert tibia["evidence"]["selected_view_regions"] == 0
    assert tibia["profile"] is None


def test_reversed_bone_anchor_pair_is_quarantined_before_dependent_windows(
    monkeypatch,
):
    _no_producer(monkeypatch)
    series = _series()
    femur_point = np.asarray((0.0, 0.0, -100.0))
    tibia_point = np.asarray((0.0, 0.0, 100.0))
    femur = _complete_anchor(
        "femur", femur_point, [_anchor_territory("femur", (2, 3, 6, 10, 13, 20))]
    )
    tibia = _complete_anchor(
        "tibia", tibia_point, [_anchor_territory("tibia", (3, 4, 12, 16, 9, 17))]
    )
    for anchor, point in ((femur, femur_point), (tibia, tibia_point)):
        anchor["reference"] = {
            "status": "complete",
            "point_lps": point.tolist(),
            "precision_mm": [0.0, 0.0, 0.0],
        }

    from knee.diagnosis import squint_anatomical_priors as priors

    calls = []
    actual = priors.anatomical_windows

    def observe_windows(series_record, subject, **kwargs):
        calls.append({"subject": subject, "anchors": dict(kwargs["anchors"])})
        return actual(series_record, subject, **kwargs)

    monkeypatch.setattr(priors, "anatomical_windows", observe_windows)
    memory = _memory(series, {"medial_meniscus": (4, 5, 11, 12, 10, 15)})
    result = locator.locate_objects(
        _study(
            series,
            knee_side="left",
            anchors={"femur": femur, "tibia": tibia},
        ),
        memory,
    )

    anchor_evidence = result["evidence"]["anchors"]
    for name in ("femur", "tibia"):
        bone = anchor_evidence["bones"][name]
        assert bone["status"] == "conflict"
        assert bone["code"] == "anatomical_relation_conflict"
        assert bone["anatomical_sanity"]["status"] == "contradicted"
    assert anchor_evidence["source"]["route_reason"] == "anatomical_anchor_conflict"
    assert calls
    assert {call["subject"] for call in calls} == {"medial_meniscus"}
    assert all(not ({"femur", "tibia"} & set(call["anchors"])) for call in calls)


def _sided_anchors(tibia_knee, fibula_knee) -> dict:
    """A tibia, and a fibula at larger LPS x (the patient's left side of it).

    The tibia's territory spans x -90..-50 mm and its reference stands at x -70;
    the fibula's spans x 30..70 and its reference stands at x 50. Each anchor
    records the knee its series headers named (DICOM Laterality), as
    ``find_anchors`` writes it.
    """
    anchors = {}
    for bone, point, box, knee in (
        ("tibia", (-70.0, -10.0, -30.0), (3, 4, 12, 16, 3, 6), tibia_knee),
        ("fibula", (50.0, -10.0, -40.0), (3, 4, 14, 17, 15, 18), fibula_knee),
    ):
        anchor = _complete_anchor(bone, point, [_anchor_territory(bone, box)])
        anchor["reference"] = {
            "status": "complete",
            "point_lps": list(point),
            "precision_mm": [0.0, 0.0, 0.0],
        }
        anchor["knee"] = knee
        anchors[bone] = anchor
    return anchors


def test_the_headers_knee_reaches_the_anchor_checks_and_the_sided_proposals(
    monkeypatch,
):
    _no_producer(monkeypatch)
    series = _series()
    memory = _memory(series, {"medial_meniscus": (4, 5, 11, 12, 10, 15)})

    def locate(anchors, **extra):
        return locator.locate_objects(_study(series, anchors=anchors, **extra), memory)

    def proposal_statuses(result):
        rows = result["objects"]["medial_meniscus"]["evidence"]["proposal_sources"]
        return {row["status"] for row in rows}

    # The headers name a left knee: the fibula lies lateral of the tibia, as it
    # must, and the sided dependent is proposed on that knee's side alone.
    left = locate(_sided_anchors("L", "L"))
    assert left["evidence"]["knee_side"] == {
        "side": "left",
        "source": "series_header_laterality",
    }
    anchors = left["evidence"]["anchors"]
    assert {anchors["bones"][bone]["status"] for bone in ("tibia", "fibula")} == {
        "complete"
    }
    assert anchors["anatomical_sanity"]["fibula"]["status"] == "plausible"
    assert proposal_statuses(left) == {"proposed"}
    # The same pictures headed as a right knee reverse that relation: the pair is
    # quarantined and anchors nothing.
    right = locate(_sided_anchors("R", "R"))
    assert right["evidence"]["knee_side"] == {
        "side": "right",
        "source": "series_header_laterality",
    }
    for bone in ("tibia", "fibula"):
        record = right["evidence"]["anchors"]["bones"][bone]
        assert (record["status"], record["code"]) == (
            "conflict",
            "anatomical_relation_conflict",
        )
    # No knee named: the side relation stays unknown, the pair stays usable, and
    # the dependent keeps both mirrored hypotheses.
    unnamed = locate(_sided_anchors(None, None))
    assert unnamed["evidence"]["knee_side"] == {"side": None, "source": None}
    assert (
        unnamed["evidence"]["anchors"]["anatomical_sanity"]["fibula"]["status"]
        == "unknown"
    )
    assert proposal_statuses(unnamed) == {"proposed_unknown_side"}
    # Anchors naming different knees name no side, and say why.
    mixed = locate(_sided_anchors("L", "R"))
    assert mixed["evidence"]["knee_side"] == {"side": None, "source": None}
    assert mixed["evidence"]["anchors"]["source"]["knee_conflict"] == ["L", "R"]
    # A side the caller supplies is the study's own and comes first.
    supplied = locate(_sided_anchors("R", "R"), knee_side="left")
    assert supplied["evidence"]["knee_side"] == {"side": "left", "source": "study"}
    assert (
        supplied["evidence"]["anchors"]["anatomical_sanity"]["fibula"]["status"]
        == "plausible"
    )


def test_a_reversed_pair_sets_aside_only_the_member_no_other_view_confirms(
    monkeypatch,
):
    """A reversed relation is a disagreement about the pair. When exactly one member
    has support of its own (another view of the same bone agreed with its section),
    the other is set aside and the confirmed one anchors, keeping the overruled
    relation; when both or neither have it, both are set aside."""
    _no_producer(monkeypatch)
    series = _series()
    memory = _memory(series, {"medial_meniscus": (4, 5, 11, 12, 10, 15)})

    def locate(confirmed: set[str]):
        anchors = _sided_anchors("R", "R")
        for bone in confirmed:
            anchors[bone]["territories"][0]["provenance"] = {
                "fixture": True,
                "cross_view": "views_agree",
            }
        return locator.locate_objects(_study(series, anchors=anchors), memory)[
            "evidence"
        ]["anchors"]["bones"]

    # The tibia's section agreed with another view; the fibula's agreed with none.
    bones = locate({"tibia"})
    assert (bones["fibula"]["status"], bones["fibula"]["code"]) == (
        "conflict",
        "anatomical_relation_conflict",
    )
    assert bones["tibia"]["status"] == "complete"
    (overruled,) = bones["tibia"]["overruled_relation_conflicts"]
    assert overruled["set_aside"] == "fibula"
    assert overruled["kept_by"] == "cross_view_agreement"
    assert overruled["checks_when_set_aside"]["status"] in {
        "contradicted",
        "plausible",
        "unknown",
    }
    # The other sign: the fibula is the confirmed one, the tibia is set aside.
    bones = locate({"fibula"})
    assert bones["tibia"]["status"] == "conflict"
    assert bones["fibula"]["status"] == "complete"
    assert [
        row["set_aside"] for row in bones["fibula"]["overruled_relation_conflicts"]
    ] == ["tibia"]
    # Both confirmed, or neither: the checks cannot say which name was mistaken.
    for confirmed in ({"tibia", "fibula"}, set()):
        bones = locate(confirmed)
        assert {bones[bone]["status"] for bone in ("tibia", "fibula")} == {"conflict"}
        assert all(
            "overruled_relation_conflicts" not in bones[bone]
            for bone in ("tibia", "fibula")
        )


def _positioned(x_mm: float) -> dict:
    """A series record whose squint tiles all centre at patient x = ``x_mm``."""
    centres = np.zeros((1, 2, 2, 3))
    centres[..., 0] = x_mm
    return {"stack": SimpleNamespace(centres_lps=centres)}


def test_the_knees_position_names_a_side_only_off_the_bore_axis():
    side = anatomy_locator.knee_side_from_position
    right = side({"a": _positioned(-90.0), "b": _positioned(-80.0)})
    assert (right["side"], right["code"], right["centre_x_mm"]) == (
        "right",
        "named_by_position",
        -85.0,
    )
    assert side({"a": _positioned(85.0)})["side"] == "left"
    # Within the knee's half-breadth of the axis the knee straddles it: no side.
    near = side({"a": _positioned(-20.0)})
    assert (near["side"], near["code"]) == (None, "knee_straddles_the_bore_axis")
    assert side({})["code"] == "no_series_position"
    # The fixture's leg (its leg-map tiles) is centred on the axis.
    assert side({CORONAL: _series()})["side"] is None


def test_the_knees_position_names_the_side_the_headers_omit_and_never_overrules_them(
    monkeypatch,
):
    _no_producer(monkeypatch)
    series = _series()
    memory = _memory(series, {"medial_meniscus": (4, 5, 11, 12, 10, 15)})

    def locate(knee, position_side):
        monkeypatch.setattr(
            anatomy_locator,
            "knee_side_from_position",
            lambda _series: {
                "side": position_side,
                "code": "fixture",
                "centre_x_mm": None,
            },
        )
        return locator.locate_objects(
            _study(series, anchors=_sided_anchors(knee, knee)), memory
        )["evidence"]

    # No header side: the position names it, and the fibula's lateral check reads it.
    evidence = locate(None, "left")
    assert evidence["knee_side"] == {
        "side": "left",
        "source": "knee_position_in_patient_frame",
    }
    assert evidence["anchors"]["anatomical_sanity"]["fibula"]["status"] == "plausible"
    # Header and position agree: the header is the recorded source.
    assert locate("L", "left")["knee_side"] == {
        "side": "left",
        "source": "series_header_laterality",
    }
    # Header with no side by position: the header stands.
    assert locate("L", None)["knee_side"]["side"] == "left"
    # They name different knees: neither is chosen, and the conflict is kept.
    evidence = locate("R", "left")
    assert evidence["knee_side"] == {"side": None, "source": None}
    assert evidence["knee_position"]["conflict"] == {
        "header": "right",
        "position": "left",
    }
    assert evidence["anchors"]["anatomical_sanity"]["fibula"]["status"] == "unknown"


def _partial_axial_anchor(bone: str, box: tuple[int, ...], height_mm: float):
    """A partial anchor: one coronal territory and one exactly axial key plane."""
    return {
        **_unavailable_anchor(bone, status="partial"),
        "territories": [_anchor_territory(bone, box)],
        "key_planes": {
            "axial": _plane(
                "axial",
                (0, 0, 1),
                height_mm,
                series_uid="fixture-axial",
                slice_index=0,
            ),
            "sagittal": {
                "orientation": "sagittal",
                "outcome": "tied",
                "candidates": [["a", 1], ["b", 2]],
            },
        },
    }


def test_partial_anchor_pair_is_checked_on_the_axis_its_planes_determine(monkeypatch):
    _no_producer(monkeypatch)
    series = _series()
    # Tile rows 6-9 span z 20..60 mm, rows 12-15 z -40..0 mm; each axial key plane
    # lies inside its bone's own territory.
    high, low = (2, 3, 6, 10, 13, 20), (3, 4, 12, 16, 9, 17)

    def checked(femur_box, femur_z, tibia_box, tibia_z):
        state = anatomy_locator.study_anchors(
            {
                "study_uid": STUDY,
                "anchors": {
                    "femur": _partial_axial_anchor("femur", femur_box, femur_z),
                    "tibia": _partial_axial_anchor("tibia", tibia_box, tibia_z),
                },
            },
            {CORONAL: series},
        )
        assert set(state["usable"]) == {"femur", "tibia"}
        anatomy_locator._check_anchor_sanity(state, {CORONAL: series}, "left")
        return state

    ordered = checked(high, 40.0, low, -20.0)
    assert set(ordered["usable"]) == {"femur", "tibia"}
    assert ordered["route"] == "structural_anchors"
    for name in ("femur", "tibia"):
        assert ordered["sanity"][name]["status"] == "plausible"
        (row,) = ordered["sanity"][name]["windows"]
        (check,) = [
            c
            for c in row["checks"]
            if c["rule_id"] == "authored:femur:superior_to:tibia"
        ]
        assert check["reference_status"] == "partial"
        assert check["reference_construction"] == "partial_reference_selected_planes"
        assert [plane["orientation"] for plane in check["reference_planes"]] == [
            "axial"
        ]

    # The opposite sign: the bones' own axial planes put the femur below the tibia.
    reversed_pair = checked(low, -20.0, high, 40.0)
    assert reversed_pair["usable"] == {}
    assert reversed_pair["route"] == "existing_finite_route"
    assert reversed_pair["source"]["route_reason"] == "anatomical_anchor_conflict"
    for name in ("femur", "tibia"):
        bone = reversed_pair["bones"][name]
        assert bone["status"] == "conflict"
        assert bone["code"] == "anatomical_relation_conflict"
        assert bone["anatomical_sanity"]["status"] == "contradicted"


def _partial_unplaned_anchor(bone: str, box: tuple[int, ...]):
    """A partial anchor whose only key plane is tied: its territory alone places it."""
    return {
        **_unavailable_anchor(bone, status="partial"),
        "territories": [_anchor_territory(bone, box)],
        "key_planes": {
            "sagittal": {
                "orientation": "sagittal",
                "outcome": "tied",
                "candidates": [["a", 1], ["b", 2]],
            }
        },
    }


def test_anchor_geometry_carries_its_checked_territories_object_boxes(monkeypatch):
    _no_producer(monkeypatch)
    series = _series()
    box = (2, 3, 6, 10, 13, 20)
    stray = _anchor_territory("femur", (5, 6, 6, 9, 13, 19))
    stray["series_uid"] = "not-in-this-study"
    femur = {
        **_partial_unplaned_anchor("femur", box),
        "territories": [_anchor_territory("femur", box), stray],
    }
    regions = _geometry(series, femur)["regions"]
    # Only the territory that passed the anchor's checks, by its object-tile box:
    # never the territory's tile window, which holds its context ring too.
    assert regions == [
        {
            "series_uid": CORONAL,
            "window": list(box),
            "status": "anchor_territory_object_tiles",
            "origin": "anchor_structure",
        }
    ]
    assert femur["territories"][0]["tile_window"] != list(box)


def test_territory_windows_decide_where_no_plane_determines_the_axis(monkeypatch):
    _no_producer(monkeypatch)
    series = _series()
    # Tile rows 6-9 span z 20..60 mm, rows 12-15 z -40..0 mm.
    high, low = (2, 3, 6, 10, 13, 20), (3, 4, 12, 16, 9, 17)

    def checked(femur_box, tibia_box):
        state = anatomy_locator.study_anchors(
            {
                "study_uid": STUDY,
                "anchors": {
                    "femur": _partial_unplaned_anchor("femur", femur_box),
                    "tibia": _partial_unplaned_anchor("tibia", tibia_box),
                },
            },
            {CORONAL: series},
        )
        assert set(state["usable"]) == {"femur", "tibia"}
        # Production names no knee side; the z rule does not need one.
        anatomy_locator._check_anchor_sanity(state, {CORONAL: series}, None)
        return state

    def femur_rule(state, name):
        (row,) = state["sanity"][name]["windows"]
        (check,) = [
            c
            for c in row["checks"]
            if c["rule_id"] == "authored:femur:superior_to:tibia"
        ]
        return check

    ordered = checked(high, low)
    assert set(ordered["usable"]) == {"femur", "tibia"}
    for name, other_z in (("femur", [-40.0, 0.0]), ("tibia", [20.0, 60.0])):
        assert ordered["sanity"][name]["status"] == "plausible"
        check = femur_rule(ordered, name)
        assert check["target_interval"] == pytest.approx(other_z)
        assert check["reference_construction"] == "anchor_window_projection"
        assert check["reference_fallbacks"] == [
            "partial_reference_without_selected_planes"
        ]
        (window,) = check["reference_windows"]
        assert window["series_uid"] == CORONAL
        assert window["scope"] == "candidate_series"

    # The opposite sign: the territories put the femur below the tibia.
    reversed_pair = checked(low, high)
    assert reversed_pair["usable"] == {}
    assert reversed_pair["route"] == "existing_finite_route"
    assert reversed_pair["source"]["route_reason"] == "anatomical_anchor_conflict"
    for name in ("femur", "tibia"):
        bone = reversed_pair["bones"][name]
        assert bone["status"] == "conflict"
        assert bone["code"] == "anatomical_relation_conflict"
        assert bone["anatomical_sanity"]["status"] == "contradicted"
