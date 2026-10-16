"""Driver refusals and recording for the paired retinacula read."""

from types import SimpleNamespace

import numpy as np
import pytest

from scripts import run_interiors

MEDIAL = "medial_patellar_retinaculum"
LATERAL = "lateral_patellar_retinaculum"
GROUP = "patellar_retinacula"


def _own(*, in_plane=(True, True, False), knee="R", fat="1", fluid="1"):
    return SimpleNamespace(
        assignment=SimpleNamespace(in_plane=in_plane),
        record={"series_uid": "series-a", "assignments": {"knee": knee}},
        series=SimpleNamespace(
            row=SimpleNamespace(fat_suppression=fat, fluid_sensitive=fluid)
        ),
    )


def _leg(femur=None):
    if femur is None:
        femur = np.ones((1, 3), dtype=float)
    return SimpleNamespace(femur_lps=femur, patella_lps=np.ones((1, 3)))


@pytest.mark.parametrize(
    ("own", "leg", "centre", "expected"),
    [
        (
            _own(in_plane=(True, True, True)),
            _leg(),
            np.ones(3),
            "abstain_leg_runs_in_the_plane",
        ),
        (_own(knee="?"), _leg(), np.ones(3), "abstain_header_names_no_knee"),
        (
            _own(fluid="0"),
            _leg(),
            np.ones(3),
            "abstain_requires_fluid_sensitive_fat_suppression",
        ),
        (_own(), None, np.ones(3), "abstain_no_bone_carried"),
        (_own(), _leg(), None, "abstain_no_patella_carried"),
        (_own(), _leg(np.empty((0, 3))), np.ones(3), "abstain_no_femur_carried"),
    ],
)
def test_retinacula_slice_returns_named_prerequisite_refusals(
    own, leg, centre, expected
):
    assert run_interiors.retinacula_slice(own, leg, centre) == expected


def test_find_part_records_group_and_both_companion_silences_for_string_refusal():
    own = _own()
    own.record["assignments"]["codes"] = {}

    found, silences = run_interiors.find_part(
        [own], GROUP, lambda measured: "abstain_no_patella_carried", None
    )

    assert found == []
    assert silences == {
        "series-a:patellar_retinacula": "abstain_no_patella_carried",
        f"series-a:{MEDIAL}": "abstain_no_patella_carried",
        f"series-a:{LATERAL}": "abstain_no_patella_carried",
    }


def test_find_part_keeps_partial_identification_and_records_the_other_wall_silence():
    own = _own()
    record = {
        "series_uid": "series-a",
        "assignments": {
            "codes": {
                GROUP: "identified",
                MEDIAL: "identified",
                LATERAL: "abstain_no_outboard_wall_minimum",
            }
        },
        "main_slice": {"object": GROUP},
        "region": "present",
    }
    arrays = {"a1_objects": np.zeros((2, 2), dtype=np.int8)}
    frame = run_interiors.PlaneFrame(
        np.zeros(3), np.array([[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]]), (1.0, 1.0)
    )
    result = (record, arrays, frame)

    found, silences = run_interiors.find_part(
        [own], GROUP, lambda measured: result, None
    )

    assert found == [(record, arrays)]
    assert silences == {f"series-a:{LATERAL}": "abstain_no_outboard_wall_minimum"}
