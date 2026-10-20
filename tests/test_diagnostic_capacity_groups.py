"""A declared related source is excluded by the production capacity consumer."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from types import SimpleNamespace

from knee.diagnosis import pipeline
from knee.diagnosis.composition import compose_question_profile
from knee.diagnosis.models import Call, Case, Profile, Question, Snapshot
from knee.diagnosis.store import write_store
from knee.encoding.counts import BankLayout, CountBundle, CountLayout
from knee.study.tables import LABELS, TRAIN_COLUMNS


def test_capacity_excludes_known_related_studies_but_inference_keeps_fixed_memory(
    tmp_path, monkeypatch
):
    layout = CountLayout(
        "fixture-layout", "fixture-carrier", (BankLayout("signal", 3),)
    )
    question = Question("ACL", "diagnosis/ACL", ("femur",), ("object/femur/signal",))

    def profile(uid, group):
        return Profile(
            "femur",
            CountBundle(layout, ((1, 0, 0),)),
            "cheap/fixture-v1",
            "region:bone-region",
            "source:" + uid,
            context=(("study_uid", uid), ("source_group", group)),
        )

    same_group = compose_question_profile(
        (profile("train-related", "group-A"),), question
    )
    other_group = compose_question_profile(
        (profile("train-independent", "group-B"),), question
    )
    memory = tmp_path / "memory"
    write_store(
        memory,
        Snapshot(
            "group-test-r1",
            (
                Case(
                    "related",
                    "train-related",
                    same_group,
                    (Call("ACL", 1, "independent"),),
                    "r1",
                ),
                Case(
                    "independent",
                    "train-independent",
                    other_group,
                    (Call("ACL", -1, "independent"),),
                    "r1",
                ),
            ),
        ),
    )
    questions = tmp_path / "questions.json"
    questions.write_text(
        json.dumps(
            {
                "schema": "knee.diagnostic-questions/v1",
                "questions": [
                    {
                        "question_id": "ACL",
                        "objects": ["femur"],
                        "banks": ["object/femur/signal"],
                    }
                ],
            }
        )
    )
    labels = tmp_path / "train.csv"
    with labels.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(TRAIN_COLUMNS)
        writer.writerow(["query", "independent report", *("0" for _ in LABELS)])
    monkeypatch.setattr(pipeline, "_product_paths", lambda _: (Path("fixture.h5"),))
    monkeypatch.setattr(
        pipeline,
        "_product_studies",
        lambda _: iter(
            (("query", (profile("query", "group-A"),), {"source": "fixture"}),)
        ),
    )
    for action in ("capacity", "infer"):
        out = tmp_path / action
        args = SimpleNamespace(
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
        pipeline.run_diagnostic_cli(args)
        result = json.loads((out / "studies/query.json").read_text())["questions"][
            "ACL"
        ]
        assert result["outcome"] == "proposal"
        if action == "capacity":
            assert result["source_group_excluded_case_ids"] == ["related"]
            assert result["excluded_source_group"] == "group-A"
            assert result["excluded_case_ids"] == ["related"]
            assert [term["case_id"] for term in result["case_terms"]] == ["independent"]
        else:
            assert result["excluded_case_ids"] == []
            assert {term["case_id"] for term in result["case_terms"]} == {
                "related",
                "independent",
            }
            assert not (out / "teaching-source.csv").exists()
