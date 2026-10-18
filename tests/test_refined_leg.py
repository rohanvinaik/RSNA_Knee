"""The leg refined by the bones' later native sections (`refine_leg`) and the caches keyed by the leg
(`leg_on`, `native_femur_coarse_context`): a refined leg is never handed the early leg's projection,
one leg shares its projection, and only sections the bones resolved natively are published."""

from dataclasses import replace
from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest

from knee.collapse.bones import IDENTIFIED, NO_TERRITORY, OUTCOMES
from knee.collapse.physical import PlaneFrame
from knee.telemetry.once import computing
from scripts import run_interiors as run

SHAPE = (40, 40)
FRAME = PlaneFrame(
    np.zeros(3), np.array([[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]]), (1.0, 1.0)
)


def leg(femur, tibia=((0.0, 0.0, 99.0),)) -> run.Leg:
    early = run.Leg(
        np.asarray(femur, dtype=float),
        np.asarray(tibia, dtype=float),
        None,
        None,
        np.zeros((0, 3)),
    )
    return replace(early, identity=run.leg_identity(early))


def series(uid="s", fat="0", thickness=2.0):
    return cast(
        run.Series,
        SimpleNamespace(
            row=SimpleNamespace(series_uid=uid, fat_suppression=fat),
            slice_thickness_mm=[thickness] * 8,
        ),
    )


def test_the_identity_follows_the_places_and_nothing_else():
    assert leg([[5.0, 5.0, 0.0]]).identity == leg([[5.0, 5.0, 0.0]]).identity
    assert leg([[5.0, 5.0, 0.0]]).identity != leg([[6.0, 5.0, 0.0]]).identity


def test_a_refined_leg_is_never_handed_the_early_legs_projection():
    early = leg([[5.0, 5.0, 0.0]])
    refined = leg([[5.0, 5.0, 0.0], [20.0, 20.0, 0.0]])
    with computing():
        first, _ = run.leg_on(early, series(), 0, FRAME, SHAPE, 2.0)
        again, _ = run.leg_on(early, series(), 0, FRAME, SHAPE, 2.0)
        second, _ = run.leg_on(refined, series(), 0, FRAME, SHAPE, 2.0)
    assert again is first  # one leg, one projection per slice
    assert int(first.sum()) == 1 and int(second.sum()) == 2


def test_the_coarse_femur_context_reads_the_refined_legs_seeds_on_the_same_slice():
    raw = np.full(SHAPE, 50.0)
    raw[8:32, 8:32] = 400.0  # a bright marrow body inside a darker field
    own = cast(
        run.Measured, SimpleNamespace(series=series(), record={"series_uid": "s"})
    )
    early = leg([[0.0, 0.0, 99.0]])  # off the slice: no seed here
    refined = leg([[0.0, 0.0, 99.0], [20.0, 20.0, 0.0]])
    with computing():
        before = run.native_femur_coarse_context(own, 0, raw, FRAME, early)
        after = run.native_femur_coarse_context(own, 0, raw, FRAME, refined)
    assert before["status"] == "no_femur_seed_on_native_slice"
    assert not before["femur_seed"].any()
    assert after["femur_seed"][20, 20] and after["status"] != before["status"]


def measured(outcomes, regions, slices=(3, 4)):
    record: dict = {"series_uid": "s", "bones": {}}
    arrays = {
        "a3_femur_plane_slices": np.asarray(slices, dtype=np.int32),
        "a3_femur_plane_region": np.stack(regions),
        "a3_femur_plane_outcome": np.asarray(
            [OUTCOMES.index(code) for code in outcomes], dtype=np.int8
        ),
    }
    return cast(
        run.Measured, SimpleNamespace(series=series(), record=record, arrays=arrays)
    )


def mask(*places):
    out = np.zeros(SHAPE, dtype=bool)
    for r, c in places:
        out[r, c] = True
    return out


def test_only_the_sections_the_bones_resolved_are_published_and_recorded(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(run, "plane_frame", lambda series, z: FRAME)
    early = leg([[5.0, 5.0, 0.0]])
    own = measured(
        (IDENTIFIED, NO_TERRITORY), [mask((10, 11), (12, 13)), mask((30, 30))]
    )
    refined = run.refine_leg(early, [own])
    assert len(refined.femur_lps) == 3  # the early place and the resolved section's two
    assert {tuple(p) for p in refined.femur_lps[1:]} == {
        (11.0, 10.0, 0.0),
        (13.0, 12.0, 0.0),
    }
    assert np.array_equal(refined.tibia_lps, early.tibia_lps)
    assert refined.identity == run.leg_identity(refined) != early.identity
    assert own.record["bones"]["published_to_leg"] == {
        "femur": {"support": "a3_femur_plane_region", "slices": [3]}
    }


def test_a_legs_places_cannot_change_after_its_identity_is_made():
    source = np.array([[5.0, 5.0, 0.0]])
    made = leg(source)
    # the array it was built from changes; the leg's own copy does not
    source[0, 0] = 99.0
    assert made.femur_lps[0, 0] == 5.0
    assert made.identity == run.leg_identity(made)
    for array in (made.femur_lps, made.tibia_lps, made.patella_lps):
        with pytest.raises(ValueError):
            array[...] = 0.0


def test_with_no_resolved_section_the_early_leg_is_kept_as_it_is(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(run, "plane_frame", lambda series, z: FRAME)
    early = leg([[5.0, 5.0, 0.0]])
    own = measured((NO_TERRITORY,), [mask((10, 11))], slices=(3,))
    assert run.refine_leg(early, [own]) is early
    assert "published_to_leg" not in own.record["bones"]
