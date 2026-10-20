"""The production consumer freezes Question.banks over bank_prefixes for recall.

declarations.select_question_banks says explicit banks override prefixes. An
explicit exact bank absent from the query layout must therefore never fall back
to a broader prefix when run_diagnostic_cli hands the question to recall.
Only study acquisition is replaced; question JSON loading, selection, composition,
memory reading and recall are the production code.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from knee.diagnosis import pipeline, retrieval
from knee.diagnosis.composition import compose_question_profile
from knee.diagnosis.models import Call, Case, Profile, Question, Snapshot
from knee.diagnosis.store import write_store
from knee.encoding.counts import BankLayout, CountBundle, CountLayout
from knee.study.tables import LABELS, TRAIN_COLUMNS

SIGNAL = "object/femur/signal"
OTHER = "object/femur/other"
LAYOUT = CountLayout(
    "fixture-layout",
    "fixture-carrier",
    (BankLayout("signal", 3), BankLayout("other", 3)),
)


def _profile(uid: str, signal, other) -> Profile:
    return Profile(
        "femur",
        CountBundle(LAYOUT, (signal, other)),
        "cheap/fixture-v1",
        "region:bone-region",
        "source:" + uid,
        context=(("study_uid", uid), ("source_group", "group-" + uid)),
    )


def _memory(path: Path) -> Path:
    declared = Question(
        "ACL", "diagnosis/ACL", ("femur",), bank_prefixes=("object/femur/",)
    )

    def case(case_id, uid, digit, signal, other):
        return Case(
            case_id,
            uid,
            compose_question_profile((_profile(uid, signal, other),), declared),
            (Call("ACL", digit, "independent"),),
            "r1",
        )

    write_store(
        path,
        Snapshot(
            "handoff-r1",
            (
                case("positive", "train-pos", 1, (1, 0, 0), (0, 0, 1)),
                case("negative", "train-neg", -1, (0, 1, 0), (0, 1, 0)),
            ),
        ),
    )
    return path


def _questions(path: Path, *, banks: list[str], prefixes: list[str]) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema": "knee.diagnostic-questions/v1",
                "questions": [
                    {
                        "question_id": "ACL",
                        "objects": ["femur"],
                        "banks": banks,
                        "bank_prefixes": prefixes,
                    }
                ],
            }
        )
    )
    return path


def _run(tmp_path, monkeypatch, action, *, banks, prefixes):
    """Run the production CLI; return (ACL record, bank-set registry, recall calls)."""
    memory = _memory(tmp_path / "memory")
    questions = _questions(tmp_path / "questions.json", banks=banks, prefixes=prefixes)
    labels = tmp_path / "train.csv"
    with labels.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(TRAIN_COLUMNS)
        writer.writerow(["query", "report", *("0" for _ in LABELS)])
    monkeypatch.setattr(pipeline, "_product_paths", lambda _: (Path("fixture.h5"),))
    monkeypatch.setattr(
        pipeline,
        "_product_studies",
        lambda _: iter(
            (
                (
                    "query",
                    (_profile("query", (1, 0, 0), (0, 1, 0)),),
                    {"source": "fixture"},
                ),
            )
        ),
    )
    calls: list[str] = []
    real = retrieval.recall

    def counting(query, question, snapshot, **kwargs):
        calls.append(question.question_id)
        return real(query, question, snapshot, **kwargs)

    monkeypatch.setattr(retrieval, "recall", counting)
    out = tmp_path / ("out-" + action)
    pipeline.run_diagnostic_cli(
        SimpleNamespace(
            diagnostic_mode=action,
            diagnostic_products=tmp_path / "products",
            diagnostic_inputs=None,
            diagnostic_memory=memory,
            diagnostic_labels=labels,
            diagnostic_output=out,
            diagnostic_questions=questions,
            diagnostic_trust=None,
            diagnostic_pair_products=None,
            draw=False,
        )
    )
    record = json.loads((out / "studies/query.json").read_text())["questions"]["ACL"]
    registry = json.loads((out / "bank-sets.json").read_text())
    return record, registry, calls


@pytest.mark.parametrize("action", ["infer", "capacity"])
def test_missing_explicit_bank_never_falls_back_to_matching_prefix(
    tmp_path, monkeypatch, action
):
    record, registry, calls = _run(
        tmp_path,
        monkeypatch,
        action,
        banks=["object/femur/not-in-layout"],
        prefixes=["object/femur/"],  # would match both real cue banks
    )
    assert record["outcome"] == "incompatible_encoding"
    assert record["reason"] == "question_banks_not_present_in_query_layout"
    assert record["question_id"] == "ACL"
    assert registry[record["selected_banks"]["bank_set"]] == []
    assert record["call"] == 0
    assert "case_terms" not in record  # no broad-bank comparison happened
    assert calls == []


def test_nonempty_exact_selection_overrides_prefix_in_recall(tmp_path, monkeypatch):
    record, registry, calls = _run(
        tmp_path,
        monkeypatch,
        "infer",
        banks=[SIGNAL],
        prefixes=["object/femur/"],  # also matches OTHER; must not be compared
    )
    assert calls == ["ACL"]
    assert registry[record["selected_banks"]["bank_set"]] == [SIGNAL]
    assert record["outcome"] == "proposal"
    assert record["case_terms"]
    for term in record["case_terms"]:
        assert registry[term["common_speaking_banks"]["bank_set"]] == [SIGNAL]


def test_default_prefix_only_question_still_selects_prefix_banks(tmp_path, monkeypatch):
    record, registry, calls = _run(
        tmp_path, monkeypatch, "infer", banks=[], prefixes=["object/femur/"]
    )
    assert calls == ["ACL"]
    assert registry[record["selected_banks"]["bank_set"]] == [SIGNAL, OTHER]
    assert record["outcome"] == "proposal"
    for term in record["case_terms"]:
        assert registry[term["common_speaking_banks"]["bank_set"]] == [SIGNAL, OTHER]
