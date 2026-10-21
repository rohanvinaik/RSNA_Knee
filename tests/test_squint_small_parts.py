"""A compatible cheap reading decides at its own scope; a native outline is an explicit tool.

Superseded policy. SQUINT_TRAINING_BUILD §10 (last item), agreed on the lead's proposal on 2026-10-21,
had a small part read over its expected area grade within "open" until the bounded own-outline step had
read it, and no part's own-outline reading counted until validated. The lead's current assignment and
the newest human takeover withdrew that: production is squint-first, useful anatomical priors suffice,
and exact outlines are not a prerequisite to cheap recall. The native own-outline step remains an
available tool that runs only when a request names it (tests/test_squint_residual.py).

What an input itself states is still kept. A ``decision_scope`` of ``grade_only`` in a profile's source
or its merge lineage limits that reading to grading, no reading of the object is ``unavailable``, and
the territory origins a reading was placed from stay named in the evidence, never relabelled.
"""

from __future__ import annotations

import pytest

from knee.diagnosis import squint_locator
from knee.diagnosis.declarations import question_for
from knee.diagnosis.squint_contracts import combine_condition
from knee.diagnosis.squint_interfaces import (
    TERRITORY_ORIGINS,
    TERRITORY_PROCEDURE,
    territory_bank_name,
)
from knee.diagnosis.squint_pipeline import (
    _decision_scope,
    _profile_origins,
    _recall_question,
)
from knee.diagnosis.squint_profiles import merge_profiles

V1_PROCEDURE = "knee.squint-profile/scan-tercile-v1"
VIEW = {"orientation": "Coronal", "fluid_sensitive": "1", "fat_suppression": "1"}
BANK = territory_bank_name(VIEW, "object", "signal_median", "overview", 10.0)
SMALL = ["medial_meniscus", "mcl", "joint_fluid"]
LARGE = ["femur", "joint"]


def _record(outcome: str, **extra) -> dict:
    return {"outcome": outcome, "case_terms": [], "vetoed_answers": [], **extra}


def _reading(subject="medial_meniscus", origin=None, **source) -> dict:
    """One profile as the writer shapes it, with the origin its territory carried."""
    territory = {"territory": {"origin": origin}} if origin else {}
    return {
        "schema": "knee.squint-profile/v1",
        "subject": subject,
        "banks": {BANK: [1, 0, 0]},
        "source": {"procedure": TERRITORY_PROCEDURE, **territory, **source},
    }


def _merged(*profiles) -> dict:
    return merge_profiles(profiles, subject=profiles[0]["subject"])


@pytest.mark.parametrize("outcome", ["present", "absent"])
def test_an_explicit_grade_only_scope_reaches_the_contract_and_only_grades(outcome):
    decided = combine_condition(
        "Medial Meniscus", {"medial_meniscus": _record(outcome)}
    )
    graded = combine_condition(
        "Medial Meniscus",
        {"medial_meniscus": _record(outcome, decision_scope="grade_only")},
    )
    assert decided["outcome"] in ("assigned", "defeated")
    assert graded["outcome"] == "open"
    # The open question asks for a bounded look at the part, named by the contract.
    assert [
        (r["subject"], r["kind"], r["reason"]) for r in graded["observation_requests"]
    ] == [("medial_meniscus", "bounded_zoom", "query_decision_scope_grade_only")]


def test_the_same_record_still_decides_when_its_scope_is_decide():
    finding = combine_condition(
        "Medial Meniscus",
        {"medial_meniscus": _record("present", decision_scope="decide")},
    )
    assert finding["outcome"] == "assigned"


@pytest.mark.parametrize("subject", [*SMALL, *LARGE])
@pytest.mark.parametrize("origin", [*TERRITORY_ORIGINS, None])
def test_a_compatible_cheap_reading_decides_however_it_was_placed(subject, origin):
    # An anatomical relation, an anchor or a fallback location is a useful prior; none of
    # them is demoted for lacking a native outline, and neither is a reading with no origin.
    assert _decision_scope(subject, _reading(subject, origin)) == "decide"


def test_an_expected_area_reading_of_the_v1_writer_decides_too():
    profile = _reading(procedure=V1_PROCEDURE)
    assert _profile_origins(profile) == set()
    assert _decision_scope("medial_meniscus", profile) == "decide"


def test_mixed_origins_decide_and_each_origin_stays_named():
    mixed = _merged(
        _reading(origin="anatomical_relation"),
        _reading(origin="residual_native_support"),
    )
    assert _decision_scope("medial_meniscus", mixed) == "decide"
    assert _profile_origins(mixed) == {"anatomical_relation", "residual_native_support"}


@pytest.mark.parametrize("subject", ["medial_meniscus", "femur"])
def test_an_explicit_grade_only_scope_is_kept_through_the_merge_lineage(subject):
    limited = _reading(subject, "teacher_support", decision_scope="grade_only")
    assert _decision_scope(subject, limited) == "grade_only"
    mixed = _merged(_reading(subject, "anatomical_relation"), limited)
    assert _decision_scope(subject, mixed) == "grade_only"
    unlimited = _merged(
        _reading(subject, "anatomical_relation"), _reading(subject, "teacher_support")
    )
    assert _decision_scope(subject, unlimited) == "decide"


@pytest.mark.parametrize("subject", ["medial_meniscus", "femur"])
@pytest.mark.parametrize(
    "profile",
    [
        None,
        {},
        [],
        "profile",
        {"banks": {}, "source": {}},
        {**_reading("tibia")},
    ],
    ids=["none", "empty", "list", "text", "no-banks", "another-object"],
)
def test_no_reading_of_this_object_is_unavailable_never_decide(subject, profile):
    assert _decision_scope(subject, profile) == "unavailable"


def test_an_unwritten_profile_is_unavailable_not_a_measured_reading():
    silent = {**_reading(), "banks": {}}
    assert _decision_scope("medial_meniscus", silent) == "unavailable"


def test_origins_are_read_through_merge_lineage():
    nested = {
        "source": {
            "lineage": [
                {"territory": {"origin": "teacher_support"}},
                {"lineage": [{"territory": {"origin": "residual_native_support"}}]},
            ]
        }
    }
    assert _profile_origins(nested) == {"teacher_support", "residual_native_support"}
    assert _profile_origins(None) == set()
    assert _profile_origins({"source": "text"}) == set()


def _recalled(monkeypatch, outcome="proposal"):
    def recall(profile, memory, **kwargs):
        return _record(outcome)

    monkeypatch.setattr(squint_locator, "recall_object", recall)


def _located(**profiles) -> dict:
    return {
        subject: {"status": "proposal", "profile": profile, "regions": []}
        for subject, profile in profiles.items()
    }


def test_recall_evidence_keeps_the_scope_and_the_origin_each_reading_came_from(
    monkeypatch,
):
    _recalled(monkeypatch)
    question = question_for("Medial Meniscus")
    objects = _located(
        medial_meniscus=_reading("medial_meniscus", "anatomical_relation"),
        femur=_reading("femur", "anchor_structure"),
    )
    evidence = _recall_question(question, objects, {}, "query", False)
    meniscus = evidence["medial_meniscus"]
    assert meniscus["decision_scope"] == "decide"
    assert meniscus["query_origins"] == ["anatomical_relation"]  # not a teacher origin
    assert evidence["femur"]["query_origins"] == ["anchor_structure"]
    # An object the question names but nothing located has no reading, and says so.
    assert _decision_scope("joint", None) == "unavailable"
    assert "decision_scope" not in evidence["joint"]
    assert evidence["joint"]["location_status"] == "unavailable"
    assert evidence["joint"]["query_origins"] == []
    assert "decision_scope" not in evidence["diagnosis/Medial Meniscus"]


def test_missing_profile_stays_unknown_without_an_invalid_contract_scope(monkeypatch):
    _recalled(monkeypatch)
    question = question_for("Medial Meniscus")
    located = {
        "medial_meniscus": {
            "status": "unresolved_missing_reading",
            "profile": None,
            "regions": [],
        }
    }

    evidence = _recall_question(question, located, {}, "query", False)
    record = evidence["medial_meniscus"]

    assert _decision_scope("medial_meniscus", None) == "unavailable"
    assert "decision_scope" not in record
    assert record["location_status"] == "unresolved_missing_reading"
    finding = combine_condition("Medial Meniscus", {"medial_meniscus": record})
    assert finding["outcome"] == "open"
    assert finding["evidence"]["readings"]["medial_meniscus"]["state"] == "unknown"


def test_a_configuration_inherits_only_an_explicit_grade_only_of_a_defining_part(
    monkeypatch,
):
    _recalled(monkeypatch)
    question = question_for("Medial Meniscus")
    limited = _reading(
        "medial_meniscus", "teacher_support", decision_scope="grade_only"
    )
    objects = _located(
        medial_meniscus=limited, femur=_reading("femur", "anchor_structure")
    )
    evidence = _recall_question(question, objects, {}, "query", False)
    assert evidence["medial_meniscus"]["decision_scope"] == "grade_only"
    assert evidence["diagnosis/Medial Meniscus"]["decision_scope"] == "grade_only"
    # A supporting object's explicit scope limits that object, not the defining tissue.
    supporting = _located(
        medial_meniscus=_reading("medial_meniscus", "anatomical_relation"),
        femur=_reading("femur", "anchor_structure", decision_scope="grade_only"),
    )
    evidence = _recall_question(question, supporting, {}, "query", False)
    assert evidence["femur"]["decision_scope"] == "grade_only"
    assert evidence["medial_meniscus"]["decision_scope"] == "decide"
    assert "decision_scope" not in evidence["diagnosis/Medial Meniscus"]


@pytest.mark.parametrize(
    ("outcome", "decided"), [("present", "assigned"), ("absent", "defeated")]
)
def test_a_warranted_reading_over_an_anatomical_relation_decides_its_question(
    monkeypatch, outcome, decided
):
    _recalled(monkeypatch, outcome)
    question = question_for("Medial Meniscus")
    objects = _located(
        medial_meniscus=_reading("medial_meniscus", "anatomical_relation")
    )
    evidence = _recall_question(question, objects, {}, "query", False)
    finding = combine_condition(
        "Medial Meniscus", {"medial_meniscus": evidence["medial_meniscus"]}
    )
    assert finding["outcome"] == decided
    assert finding["observation_requests"] == []
    # The same reading with the scope an input stated only grades, and asks for a look.
    limited = _located(
        medial_meniscus=_reading(
            "medial_meniscus", "anatomical_relation", decision_scope="grade_only"
        )
    )
    evidence = _recall_question(question, limited, {}, "query", False)
    graded = combine_condition(
        "Medial Meniscus", {"medial_meniscus": evidence["medial_meniscus"]}
    )
    assert graded["outcome"] == "open"
    assert [r["subject"] for r in graded["observation_requests"]] == ["medial_meniscus"]
