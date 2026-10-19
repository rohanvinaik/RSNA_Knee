from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import numpy as np

from knee.collapse.observations import Observation, Unresolved
from knee.collapse.physical import PlaneFrame
from knee.collapse.study_map import StudyMap
from knee.telemetry import recording
from scripts import run_interiors as run

FRAME = PlaneFrame(
    np.zeros(3), np.array([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]), (1.0, 1.0)
)
VIEW = ("Axial", "1", "1")
FAMILY = "unfamiliar_family_said"


def _own():
    return SimpleNamespace(
        series=SimpleNamespace(
            row=SimpleNamespace(series_uid="axial"), slice_thickness_mm=[1.0, 1.0]
        ),
        record={"view": list(VIEW), "observations": []},
    )


def _context():
    return run.MapContext(StudyMap(knee="R"), None, None)


def _native() -> Observation:
    return Observation(
        "patella",
        "native",
        "resolved",
        "axial",
        VIEW,
        (1,),
        "identified",
        8,
        0.0,
        "native_support",
        "a native resolved section",
    )


def _refusal() -> Unresolved:
    return Unresolved("joint_capsule", "native", "axial", VIEW, "not_read")


def _lineage(events, family):
    return [
        e.name
        for e in events
        if e.name.startswith(family) or e.name.startswith("study_map")
    ]


def _assert_no_support_bitmap(events):
    assert not any("support" in e.name for e in events)
    assert not any("bitmap" in e.name for e in events)


def test_unfamiliar_family_records_metadata_read_and_map_rows_handoff(monkeypatch):
    monkeypatch.setattr(run, "plane_frame", lambda _series, _z: FRAME)
    context = _context()
    own = _own()
    with recording() as led:
        product, rows, added = run.offer_native_family(
            context, [cast(run.Measured, own)], FAMILY, [([_native()], [_refusal()])]
        )
        events = led.events()
    assert product == f"{FAMILY}.map_rows"
    assert len(rows) == 1 and added == 1
    assert rows[0]["observations"][0]["support"] == "native_support"
    selected = context.smap.selected("patella", "axial")
    assert selected.outcome == "selected" and selected.slice == 1
    names = [e.name for e in events if e.name.startswith(FAMILY)]
    assert names == [
        f"{FAMILY}.observations.consumed_by.map_rows",
        f"{FAMILY}.map_rows.observations.produced",
        f"{FAMILY}.map_rows.observations.consumed_by.refine_map",
    ]
    _assert_no_support_bitmap(events)


def test_empty_family_emits_no_observation_lineage():
    context = _context()
    with recording() as led:
        result = run.offer_native_family(
            context, [cast(run.Measured, _own())], FAMILY, [([], [])]
        )
        events = led.events()
    assert result == (f"{FAMILY}.map_rows", [], 0)
    assert _lineage(events, FAMILY) == []
    _assert_no_support_bitmap(events)


def test_refusal_only_family_emits_no_observation_lineage():
    context = _context()
    with recording() as led:
        result = run.offer_native_family(
            context,
            [cast(run.Measured, _own())],
            FAMILY,
            [([], [_refusal()])],
        )
        events = led.events()
    assert result == (f"{FAMILY}.map_rows", [], 0)
    assert _lineage(events, FAMILY) == []
    _assert_no_support_bitmap(events)
