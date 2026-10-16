"""The real middle-slice ITB stage preserves primary labels and transfers its own mask."""

from types import SimpleNamespace
from typing import cast

import numpy as np

from knee.collapse.physical import PlaneFrame
from scripts import run_interiors


def measured(suppressed: bool):
    shape = (2, 3)
    arrays = {
        "acquired_plane": np.ones(shape),
        "a1_objects": np.full(shape, 3, dtype=np.int8),
        "b1_available": np.ones(shape, dtype=bool),
        "b1_labels": np.ones(shape, dtype=np.int32),
    }
    return cast(
        run_interiors.Measured,
        SimpleNamespace(
            series=SimpleNamespace(
                row=SimpleNamespace(fat_suppression=str(int(suppressed)))
            ),
            record={
                "series_uid": str(suppressed),
                "slice_index": 0,
                "assignments": {"knee": "R", "codes": {}},
            },
            arrays=arrays,
            frame=PlaneFrame(
                np.zeros(3),
                np.asarray([[0.0, 1.0], [0.0, 0.0], [-1.0, 0.0]]),
                (1.0, 1.0),
            ),
        ),
    )


def test_native_itb_and_transferred_mask_preserve_primary_names(monkeypatch):
    source, target = measured(False), measured(True)
    native = np.asarray([[True, False, True], [False, True, False]])
    mapping = np.asarray([[0, -1, 2], [3, 4, 5]])
    target.arrays["b1_available"][0, 2] = False
    before = target.arrays["a1_objects"].copy()
    monkeypatch.setattr(run_interiors, "measures_of", lambda *args: None)
    monkeypatch.setattr(run_interiors, "matched", lambda *args: mapping)
    monkeypatch.setattr(
        run_interiors,
        "iliotibial_band_on_slice",
        lambda *args, **_kwargs: (native, {"candidate_lines": native}, "identified"),
    )
    run_interiors.name_iliotibial_band(source, target)
    assert source.record["assignments"]["codes"]["iliotibial_band"] == "identified"
    assert (
        target.record["assignments"]["codes"]["iliotibial_band"]
        == "laid_from_its_partner"
    )
    assert np.array_equal(source.arrays["a2_itb_candidate_lines"], native)
    assert np.array_equal(target.arrays["a1_objects"], before)
    assert np.array_equal(
        target.arrays["a2_iliotibial_band"],
        np.asarray([[True, False, False], [False, True, False]]),
    )


def test_native_refusal_is_saved_and_never_transferred(monkeypatch):
    source, target = measured(False), measured(True)
    monkeypatch.setattr(run_interiors, "measures_of", lambda *args: None)
    monkeypatch.setattr(
        run_interiors,
        "iliotibial_band_on_slice",
        lambda *args, **_kwargs: (
            np.zeros((2, 3), bool),
            {},
            "abstain_no_subcutaneous_fat",
        ),
    )

    def must_not_match(*args):
        raise AssertionError("A refused source cannot be transferred")

    monkeypatch.setattr(run_interiors, "matched", must_not_match)
    run_interiors.name_iliotibial_band(source, target)
    assert (
        source.record["assignments"]["codes"]["iliotibial_band"]
        == "abstain_no_subcutaneous_fat"
    )
    assert not source.arrays["a2_iliotibial_band"].any()
    assert "a2_iliotibial_band" not in target.arrays
