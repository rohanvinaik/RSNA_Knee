"""Two receipts compared record by record (`scripts/compare_receipts.py`, a script beside the run,
loaded here from its path): the same records are the same; a decision that changed is found; border
readings one side kept and the other did not are set aside only when asked; border readings both
sides kept are compared even then."""

import importlib.util
from pathlib import Path

TOOL = Path(__file__).resolve().parent.parent / "scripts" / "compare_receipts.py"


def tool():
    spec = importlib.util.spec_from_file_location("compare_receipts", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record(code: str = "identified", borders: str | None = None) -> dict:
    arrays = {"b1_labels": {"digest": "a"}}
    interiors: dict = {"code": "measured", "territories": 2}
    if borders is not None:
        arrays["b1_edge_points_rc"] = {"digest": borders}
        interiors["edge_counts"] = {"frame": 1}
    return {
        "study_uid": "s",
        "series_uid": "x",
        "arrays": arrays,
        "interiors": interiors,
        "assignments": {"codes": {"femur": code}},
    }


def receipt(*records: dict) -> dict:
    return {"records": list(records), "request": {}, "unread": {}}


def test_the_same_receipts_are_the_same() -> None:
    found = tool().compare(receipt(record()), receipt(record()), False, frozenset())
    assert not (found["differing"] or found["only_before"] or found["only_after"])


def test_a_changed_decision_is_found() -> None:
    before, after = receipt(record()), receipt(record("abstain_no_leg"))
    found = tool().compare(before, after, True, frozenset())
    assert list(found["differing"].values()) == [["assignments"]]


def test_borders_one_side_kept_are_set_aside_only_when_asked() -> None:
    before, after = receipt(record(borders="e")), receipt(record())
    assert tool().compare(before, after, False, frozenset())["differing"]
    assert not tool().compare(before, after, True, frozenset())["differing"]


def test_borders_both_sides_kept_are_compared_even_when_set_aside() -> None:
    before, after = receipt(record(borders="e")), receipt(record(borders="f"))
    found = tool().compare(before, after, True, frozenset())
    assert not found["differing"] and len(found["borders_differing"]) == 1
