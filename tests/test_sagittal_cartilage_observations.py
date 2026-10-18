from __future__ import annotations

from copy import deepcopy
from typing import Any

from knee.collapse.cartilage import sagittal_cartilage_observations
from knee.collapse.observations import Observation
from knee.objects.assignments import OBJECT_CODES

SERIES_UID = "sagittal-series"
ARTIFACT = "study/sagittal.npz"
VIEW = ["Sagittal", "1", "1"]


def candidate(
    object_name: str, *, row: int = 0, slice_index: int = 15
) -> dict[str, Any]:
    return {
        "object": object_name,
        "provenance": "native",
        "kind": "reading",
        "series_uid": SERIES_UID,
        "view": VIEW.copy(),
        "slices": [slice_index],
        "code": "cartilage_candidates",
        "count": 7,
        "off_plane_mm": 0.0,
        "support": "a3_joint_plane_reading",
        "note": "existing candidate reading",
        "artifact": ARTIFACT,
        "row": row,
        "label": OBJECT_CODES[object_name],
    }


def record_with(*rows: dict[str, Any]) -> dict[str, Any]:
    return {
        "series_uid": SERIES_UID,
        "view": VIEW.copy(),
        "artifact": ARTIFACT,
        "observations": list(rows),
    }


def test_serialized_sagittal_cartilage_rows_make_companions_only() -> None:
    rows = [
        candidate("femoral_cartilage", row=2, slice_index=22),
        candidate("tibial_cartilage", row=0, slice_index=15),
    ]
    record = record_with(*rows)
    before = deepcopy(record)

    result = sagittal_cartilage_observations(record)

    assert record == before
    assert len(result) == 2
    for source, companion in zip(rows, result, strict=True):
        assert isinstance(companion, Observation)
        assert companion.object == source["object"]
        assert companion.provenance == "native"
        assert companion.kind == "resolved"
        assert companion.code == "identified"
        assert companion.series_uid == source["series_uid"]
        assert companion.view == tuple(source["view"])
        assert companion.slices == tuple(source["slices"])
        assert companion.count == source["count"]
        assert companion.off_plane_mm == source["off_plane_mm"]
        assert companion.support == source["support"]
        assert companion.artifact == source["artifact"]
        assert companion.row == source["row"]
        assert companion.label == source["label"]
        assert "same existing bone-facing cartilage rule" in companion.note
        assert "not a projection" in companion.note
        assert "full-surface precision" in companion.note


def test_only_complete_matching_native_sagittal_candidate_rows_promote() -> None:
    valid = candidate("femoral_cartilage")
    rows: list[Any] = [
        valid,
        {**valid, "code": "abstain_nothing_bright_against_the_bones"},
        {**valid, "provenance": "projected", "kind": "target", "code": "target"},
        {**valid, "provenance": "laid"},
        {**valid, "view": ["Coronal", "1", "1"]},
        {**valid, "view": ["Sagittal", "1", "0"]},
        {**valid, "count": 0},
        {**valid, "label": OBJECT_CODES["tibial_cartilage"]},
        {**valid, "artifact": ""},
        {**valid, "row": True},
        {**valid, "row": -1},
        {**valid, "slices": [True]},
        {**valid, "slices": [-1]},
        {**valid, "count": True},
        {**valid, "series_uid": "different-series"},
        {**valid, "artifact": "different-artifact.npz"},
        {**valid, "view": "Sagittal"},
        {**valid, "slices": "15"},
        {**valid, "off_plane_mm": float("nan")},
        None,
    ]

    result = sagittal_cartilage_observations(record_with(*rows))

    assert len(result) == 1
    assert result[0].object == "femoral_cartilage"
    assert result[0].kind == "resolved"


def test_bad_record_context_and_empty_rows_add_nothing() -> None:
    valid = candidate("femoral_cartilage")
    assert sagittal_cartilage_observations({"observations": []}) == []
    assert sagittal_cartilage_observations({}) == []
    assert sagittal_cartilage_observations(record_with()) == []
    assert (
        sagittal_cartilage_observations(
            {**record_with(valid), "view": ["Coronal", "1", "1"]}
        )
        == []
    )
    assert (
        sagittal_cartilage_observations({**record_with(valid), "series_uid": "other"})
        == []
    )
    assert (
        sagittal_cartilage_observations({**record_with(valid), "artifact": "other.npz"})
        == []
    )
    assert (
        sagittal_cartilage_observations({**record_with(valid), "observations": None})
        == []
    )
