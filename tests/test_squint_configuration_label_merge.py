"""Independent clinical calls fill unknown ledger cells without erasing knowledge."""

from __future__ import annotations

import copy

import pytest

from knee.diagnosis.squint_configurations import (
    ConfigurationProfileError,
    _configuration_row,
    apply_rebuilt_configurations,
    rebuild_study_configurations,
)
from knee.study.tables import LABELS
from tests.test_squint_identity_growth import SAG, identity_memory

SOURCE = {"source": "independently_reviewed_report", "source_sha256": "a" * 64}


@pytest.mark.parametrize("value", [0, 1])
def test_an_independent_known_call_fills_unknown_and_keeps_its_real_source(value):
    kept = {"Effusion": None, "Synovitis": 0}
    given = {"Effusion": value}
    original = copy.deepcopy((kept, given))

    row, provenance = _configuration_row("study", given, kept, False, SOURCE)

    assert row == {"Effusion": value, "Synovitis": 0}
    assert provenance["filled_questions"] == ["Effusion"]
    assert provenance["prior_label_ledger"] == {
        "source": "label_ledger",
        "study_uid": "study",
        "row": kept,
    }
    assert provenance["question_sources"]["Effusion"] == {
        **SOURCE,
        "study_uid": "study",
    }
    assert provenance["question_sources"]["Synovitis"] == {
        "source": "label_ledger",
        "study_uid": "study",
    }
    assert (kept, given) == original


@pytest.mark.parametrize("known", [0, 1])
@pytest.mark.parametrize("given", [{}, {"Effusion": None}])
def test_missing_or_unknown_call_never_erases_a_known_ledger_call(known, given):
    row, provenance = _configuration_row(
        "study", given, {"Effusion": known}, True, SOURCE
    )
    assert row == {"Effusion": known}
    assert provenance["filled_questions"] == []
    assert provenance["question_sources"]["Effusion"]["source"] == "label_ledger"


@pytest.mark.parametrize("known", [0, 1])
def test_an_agreeing_known_call_is_retained_without_fabricating_a_new_fill(known):
    row, provenance = _configuration_row(
        "study", {"Effusion": known}, {"Effusion": known}, True, SOURCE
    )
    assert row == {"Effusion": known}
    assert provenance["filled_questions"] == []
    assert provenance["question_sources"]["Effusion"] == {
        **SOURCE,
        "study_uid": "study",
    }


@pytest.mark.parametrize("known, supplied", [(0, 1), (1, 0)])
def test_opposite_known_calls_still_refuse_as_a_label_ledger_conflict(known, supplied):
    with pytest.raises(ConfigurationProfileError, match="label_ledger_row_conflict"):
        _configuration_row(
            "study", {"Effusion": supplied}, {"Effusion": known}, False, SOURCE
        )


def test_rebuild_applies_new_normal_and_positive_calls_to_an_existing_unknown_ledger():
    memory = identity_memory((("fluid", "joint_fluid", "study", [(SAG, (2, 0, 1))]),))
    memory["label_ledger"] = {"study": dict.fromkeys(LABELS)}
    before = copy.deepcopy(memory)
    supplied = {"study": {"Effusion": 0, "Synovitis": 1}}

    rebuilt = rebuild_study_configurations(
        memory,
        ["study"],
        built_by={"kind": "independent_report_teaching"},
        labels=supplied,
        label_source=SOURCE,
    )
    child = apply_rebuilt_configurations(memory, rebuilt)

    assert memory == before
    assert rebuilt["label_ledger"]["study"]["Effusion"] == 0
    assert rebuilt["label_ledger"]["study"]["Synovitis"] == 1
    assert child["label_ledger"]["study"] == {
        **before["label_ledger"]["study"],
        "Effusion": 0,
        "Synovitis": 1,
    }
    configs = {case["subject"]: case for case in rebuilt["cases"]}
    assert configs["diagnosis/Effusion"]["condition_calls"] == {"Effusion": -1}
    assert configs["diagnosis/Synovitis"]["condition_calls"] == {"Synovitis": 1}
    assert configs["diagnosis/Effusion"]["configuration_teaching"]["labels"][
        "filled_questions"
    ] == ["Effusion", "Synovitis"]
    assert child["object_identity_teaching"] == before["object_identity_teaching"]

    # A later unknown supplies no new call and cannot remove either configuration.
    later = rebuild_study_configurations(
        child,
        ["study"],
        built_by={"kind": "later_partial_report"},
        labels={"study": {"Effusion": None}},
        label_source={"source": "later_report"},
    )
    assert later["label_ledger"] == {}
    assert {c["subject"]: c["condition_calls"] for c in later["cases"]} == {
        "diagnosis/Effusion": {"Effusion": -1},
        "diagnosis/Synovitis": {"Synovitis": 1},
    }
