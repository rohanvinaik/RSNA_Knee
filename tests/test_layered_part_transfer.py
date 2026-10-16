"""The partner's layered masks transfer independently of primary object labels."""

from types import SimpleNamespace
from typing import cast

import numpy as np

from knee.collapse.physical import PlaneFrame
from knee.objects.assignments import OBJECT_CODES
from scripts import run_interiors


def _own_with_matching_stubbed():
    # matched is replaced in these tests; lay_parts reads only own.series. This deliberate
    # partial fixture does not exercise study loading or claim to supply a complete Measured.
    return cast(run_interiors.Measured, SimpleNamespace(series=object()))


def _read(objects, *, available=None):
    shape = objects.shape
    if available is None:
        available = np.ones(shape, dtype=bool)
    return (
        {"series_uid": "target", "slice_index": 0},
        {
            "acquired_plane": np.zeros(shape),
            "a1_objects": objects.copy(),
            "b1_labels": np.ones(shape, dtype=np.int32),
            "b1_available": available.copy(),
        },
        PlaneFrame(np.zeros(3), np.eye(3)[:, :2], (1.0, 1.0)),
    )


def _partner(objects, **layered):
    arrays = {"acquired_plane": np.zeros(objects.shape), "a1_objects": objects}
    arrays.update({f"a2_{name}": mask for name, mask in layered.items()})
    return (
        {"series_uid": "source", "slice_index": 0},
        arrays,
        PlaneFrame(np.zeros(3), np.eye(3)[:, :2], (1.0, 1.0)),
    )


def test_primary_label_and_layered_mask_transfer_use_only_available_mapped_places(
    monkeypatch,
):
    target_objects = np.zeros((2, 3), dtype=np.int8)
    available = np.ones((2, 3), dtype=bool)
    available[0, 2] = False
    read = _read(target_objects, available=available)
    source_objects = np.zeros((2, 3), dtype=np.int8)
    source_objects.ravel()[[0, 1, 3]] = OBJECT_CODES["lcl"]
    source_popliteus = np.array([[False, True, True], [True, True, False]], dtype=bool)
    partner = _partner(source_objects, popliteus_tendon=source_popliteus)
    mapping = np.array([[0, 1, 2], [3, -1, 5]])
    monkeypatch.setattr(run_interiors, "matched", lambda *args: mapping)

    codes = run_interiors.lay_parts(
        _own_with_matching_stubbed(),
        read,
        partner,
        ("lcl", "popliteus_tendon"),
        product="lcl",
    )

    assert codes == {
        "lcl": "laid_from_its_partner",
        "popliteus_tendon": "laid_from_its_partner",
    }
    assert np.array_equal(
        read[1]["a1_objects"] == OBJECT_CODES["lcl"],
        np.array([[True, True, False], [True, False, False]]),
    )
    assert np.array_equal(
        read[1]["a2_popliteus_tendon"],
        np.array([[False, True, False], [True, False, False]]),
    )


def test_empty_layered_and_primary_sources_report_no_transfer(monkeypatch):
    read = _read(np.zeros((2, 2), dtype=np.int8))
    partner = _partner(
        np.zeros((2, 2), dtype=np.int8),
        popliteus_tendon=np.zeros((2, 2), dtype=bool),
    )
    monkeypatch.setattr(
        run_interiors, "matched", lambda *args: np.arange(4).reshape(2, 2)
    )

    codes = run_interiors.lay_parts(
        _own_with_matching_stubbed(),
        read,
        partner,
        ("lcl", "popliteus_tendon"),
        product="lcl",
    )

    assert codes == {"lcl": None, "popliteus_tendon": None}
    assert not read[1]["a1_objects"].any()
    assert not read[1]["a2_popliteus_tendon"].any()
