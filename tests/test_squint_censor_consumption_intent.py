"""Two-sign intent tests for synthetic censor consumption in recall (Lane B)."""

from __future__ import annotations

from knee.diagnosis.models import Call, Case, Censor, Profile, Question, Snapshot, Trust
from knee.diagnosis.retrieval import prepare_question, prepare_snapshot, recall
from knee.diagnosis.squint_locator import prepare_recall, recall_object
from knee.encoding.counts import BankLayout, CountBundle, CountLayout


def _squint_profile(*counts: int) -> dict:
    return {
        "schema": "knee.squint-profile/v1",
        "subject": "femur",
        "banks": {"axial/light/whole": list(counts)},
        "source": {
            "study": "current",
            "procedure": "knee.squint-profile/scan-tercile-v1",
        },
    }


def _squint_case(
    case_id: str,
    study_uid: str,
    question: str,
    call: int,
    counts: tuple[int, int, int],
) -> dict:
    return {
        "case_id": case_id,
        "study_uid": study_uid,
        "subject": "femur",
        "condition_calls": {question: call},
        "profile": _squint_profile(*counts),
        "teaching_source": {"kind": "independent_report", "id": case_id},
    }


def _count_layout() -> CountLayout:
    return CountLayout(
        "layout:reference-a:v1",
        "carrier:v1",
        (BankLayout("content/signal", 3),),
    )


def _bundle_profile(source_id: str, signal: tuple[int, int, int]) -> Profile:
    return Profile(
        subject="diagnosis/acl",
        bundle=CountBundle(_count_layout(), (signal,)),
        mode="full",
        scope="object:acl",
        source_id=source_id,
        context=(("scanner", "scanner-a"),),
    )


def test_censor_vetoes_resembling_held_out_query_on_its_answer_and_leaves_unrelated_question_untouched() -> (
    None
):
    memory = {
        "cases": [
            _squint_case("pos-acl", "study-pos", "acl", 1, (0, 4, 0)),
            _squint_case("neg-acl", "study-neg", "acl", -1, (4, 0, 0)),
            _squint_case("pos-mcl", "study-mcl-pos", "mcl", 1, (0, 4, 0)),
            _squint_case("neg-mcl", "study-mcl-neg", "mcl", -1, (4, 0, 0)),
        ],
        "censors": [
            {
                "censor_id": "synthetic-censor-acl-pos",
                "question": "acl",
                "answer": 1,
                "profile": _squint_profile(0, 4, 0),
                "radius_numerator": 1,
                "radius_denominator": 1,
                "source": "synthetic-near-miss",
            }
        ],
    }
    memory["prepared_recall"] = prepare_recall(memory)

    measured_neutral_query = _squint_profile(0, 4, 0)
    silent_bank_query = _squint_profile(0, 0, 0)

    vetoed = recall_object(
        measured_neutral_query, memory, "acl", exclude_study_uid="held-out-query"
    )
    assert vetoed["outcome"] == "unresolved_censored"
    assert vetoed["vetoed_answers"] == [1]
    assert [row["censor_id"] for row in vetoed["censor_terms"]] == [
        "synthetic-censor-acl-pos"
    ]

    untouched = recall_object(
        measured_neutral_query, memory, "mcl", exclude_study_uid="held-out-query"
    )
    assert untouched["outcome"] == "present"
    assert untouched["vetoed_answers"] == []
    assert untouched["censor_terms"] == []

    silent_result = recall_object(
        silent_bank_query, memory, "acl", exclude_study_uid="held-out-query"
    )
    assert silent_result["outcome"] == "unresolved_no_precedent"
    assert silent_result["speaking_calls"] == []
    assert silent_result["vetoed_answers"] == []
    assert silent_result["censor_terms"] == []


def test_prepare_question_censor_distinguishes_measured_neutral_row_from_silent_bank() -> (
    None
):
    pos_case = Case(
        case_id="pos-acl",
        study_uid="study-pos",
        profile=_bundle_profile("source:pos-acl", (0, 4, 0)),
        calls=(Call("acl", 1, "independent-teacher", "call 1"),),
        teaching_revision="seed-v1",
    )
    censor = Censor(
        censor_id="synthetic-censor-acl-pos",
        question="acl",
        answer=1,
        profile=_bundle_profile("source:censor", (0, 4, 0)),
        numerator=1,
        denominator=1,
        source="synthetic-near-miss",
    )
    snapshot = Snapshot(
        revision="memory-v1",
        cases=(pos_case,),
        trust=(Trust(pos_case.case_id, "acl", 1, 1, "independent"),),
        censors=(censor,),
    )
    prepared_snapshot = prepare_snapshot(snapshot)
    acl_question = Question(
        question_id="acl",
        subject="diagnosis/acl",
        objects=("acl",),
        banks=("content/signal",),
        context_keys=("scanner",),
    )

    neutral_query = _bundle_profile("query:neutral", (0, 4, 0))
    neutral_plan = prepare_question(neutral_query, acl_question, prepared_snapshot)
    neutral_recalled = recall(
        neutral_query,
        acl_question,
        neutral_plan,
        exclude_study_uid="held-out-query",
    )
    assert neutral_recalled["outcome"] == "unresolved_censored"
    assert neutral_recalled["vetoed_answers"] == [1]
    assert neutral_recalled["censor_ids"] == ["synthetic-censor-acl-pos"]

    silent_query = _bundle_profile("query:silent", (0, 0, 0))
    silent_plan = prepare_question(silent_query, acl_question, prepared_snapshot)
    silent_recalled = recall(
        silent_query,
        acl_question,
        silent_plan,
        exclude_study_uid="held-out-query",
    )
    assert silent_recalled["outcome"] == "unresolved_missing_reading"
    assert silent_recalled.get("vetoed_answers", []) == []
    assert silent_recalled.get("censor_ids", []) == []
