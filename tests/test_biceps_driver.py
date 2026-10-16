"""The real biceps femoris driver: its refusals, its silences, and the transfer of its mask onto the
twin's slice of the same place with unseen places left out; the rule and the walk are tested in
`tests/test_biceps_femoris.py`."""

from types import SimpleNamespace
from typing import cast

import numpy as np

from knee.collapse.physical import PlaneFrame
from scripts import run_interiors as run

SHAPE = (2, 3)


def view(uid: str, suppressed: bool, plane: str = "Sagittal", volume=None):
    frame = PlaneFrame(
        np.zeros(3), np.asarray([[0.0, 1.0], [0.0, 0.0], [-1.0, 0.0]]), (1.0, 1.0)
    )
    return cast(
        run.Measured,
        SimpleNamespace(
            series=SimpleNamespace(
                row=SimpleNamespace(
                    series_uid=uid,
                    fat_suppression=str(int(suppressed)),
                    anatomical_plane=plane,
                ),
                volume=volume,
                geometry=None,
                slice_thickness_mm=[1.0],
            ),
            record={
                "series_uid": uid,
                "slice_index": 0,
                "background_split": 1.0,
                "assignments": {"knee": "R", "codes": {}},
            },
            arrays={},
            frame=frame,
        ),
    )


def part(uid: str, code: str, mask: np.ndarray | None = None):
    arrays = {
        "acquired_plane": np.ones(SHAPE),
        "a1_objects": np.full(SHAPE, 3, dtype=np.int8),
        "b1_available": np.ones(SHAPE, dtype=bool),
        "b1_labels": np.ones(SHAPE, dtype=np.int32),
        "a2_biceps_femoris_tendon": np.zeros(SHAPE, bool) if mask is None else mask,
    }
    record = {
        "series_uid": uid,
        "slice_index": 0,
        "assignments": {"codes": {run.BICEPS: code}},
        "main_slice": {"object": run.BICEPS},
    }
    frame = view(uid, False).frame
    return record, arrays, frame


def test_native_refusals_are_named_before_anything_is_read():
    native, twin = view("n", False), view("t", True)
    assert run.biceps_native(native, twin, None) == "abstain_no_fibula"
    places = np.zeros((1, 3))
    assert run.biceps_native(native, None, places) == "abstain_no_fat_suppressed_twin"
    assert run.biceps_native(native, twin, places) == "geometry_unreadable"


def test_every_view_gets_a_named_refusal_and_the_silence_is_kept(monkeypatch):
    measured = [view("n", False), view("t", True), view("a", True, "Axial")]
    monkeypatch.setattr(
        run, "biceps_native", lambda *args: "abstain_slices_do_not_run_side_to_side"
    )
    found, silences = run.find_part(
        measured,
        run.BICEPS,
        lambda own: run.biceps_femoris_slice(own, measured, None),
        run.BICEPS_LAID_WHEN,
    )
    assert found == []
    assert silences["n:" + run.BICEPS] == "abstain_slices_do_not_run_side_to_side"
    assert silences["t:" + run.BICEPS] == "abstain_slices_do_not_run_side_to_side"
    assert silences["a:" + run.BICEPS] == "abstain_no_fat_bright_native_view"
    assert run.BICEPS in run.MAIN_PARTS


def test_mask_is_laid_onto_the_twin_without_unseen_places(monkeypatch):
    measured = [view("n", False), view("t", True, volume=[np.ones(SHAPE)])]
    mask = np.asarray([[True, True, False], [True, False, True]])
    native = part("n", "identified", mask)
    twin = part("t", run.BICEPS_LAID_WHEN)
    monkeypatch.setattr(run, "biceps_native", lambda *args: (*native, "t", 0))
    monkeypatch.setattr(run, "read_part_slice", lambda *args: twin)
    monkeypatch.setattr(run, "plane_frame", lambda *args: twin[2])
    monkeypatch.setattr(
        run, "matched", lambda *args: np.asarray([[0, -1, 2], [3, 4, 5]])
    )
    found, silences = run.find_part(
        measured,
        run.BICEPS,
        lambda own: run.biceps_femoris_slice(own, measured, np.zeros((1, 3))),
        run.BICEPS_LAID_WHEN,
    )
    assert silences == {}
    assert twin[0]["assignments"]["codes"][run.BICEPS] == "laid_from_its_partner"
    assert np.array_equal(
        twin[1]["a2_biceps_femoris_tendon"],
        np.asarray([[True, False, False], [True, False, True]]),
    )
    # the lay writes no label: only the separate mask carries the part
    assert not twin[1]["a1_objects"].any()
    assert len(found) == 2


def test_a_twin_that_is_another_series_is_refused(monkeypatch):
    measured = [view("n", False), view("t", True)]
    monkeypatch.setattr(
        run, "biceps_native", lambda *args: (*part("n", "identified"), "other", 0)
    )
    result = run.biceps_femoris_slice(measured[1], measured, np.zeros((1, 3)))
    assert result == "abstain_the_native_view_has_another_twin"


def test_unseen_places_are_not_darkness():
    volume = np.asarray([[[0.0, 0.0, 0.0], [5.0, np.nan, 7.0]]])
    own = view("u", False, volume=volume)
    plane, unseen = run.seen_native(own.series, 0)
    assert unseen.tolist() == [[True, True, True], [False, True, False]]
    assert plane.dtype != object
