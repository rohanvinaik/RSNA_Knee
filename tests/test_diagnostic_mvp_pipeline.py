"""Focused production-entry tests for generated case sources and readout wiring."""

from __future__ import annotations

import csv
import json
from argparse import ArgumentParser, Namespace
from pathlib import Path

import pytest

from knee.diagnosis.models import Profile, Snapshot
from knee.diagnosis.pipeline import (
    DiagnosticRunError,
    add_arguments,
    run_diagnostic_cli,
)
from knee.diagnosis.store import read_store, write_store
from knee.encoding.counts import BankLayout, CountBundle, CountLayout
from knee.study.tables import LABELS, TRAIN_COLUMNS


def _profile(uid: str, subject: str = "acl") -> Profile:
    layout = CountLayout("layout-v1", "carrier-v1", (BankLayout("signal", 3),))
    return Profile(
        subject,
        CountBundle(layout, ((0, 2, 0),)),
        "full",
        "object:" + subject,
        uid,
        context=(("study_uid", uid),),
    )


def _args(
    tmp_path: Path,
    *,
    mode: str = "teach",
    cases: Path | None = None,
    labels: Path | None = None,
    cohort: Path | None = None,
    partition: str | None = None,
    template: Path | None = None,
    inputs: Path | None = None,
    products: Path | None = None,
    memory: Path | None = None,
) -> Namespace:
    return Namespace(
        diagnostic_mode=mode,
        diagnostic_products=products,
        diagnostic_inputs=inputs,
        diagnostic_memory=memory or tmp_path / "memory.json",
        diagnostic_labels=labels,
        diagnostic_cases=cases,
        diagnostic_output=tmp_path / "output",
        diagnostic_revision="mvp-r1",
        diagnostic_pair_products=None,
        diagnostic_questions=None,
        diagnostic_trust=None,
        diagnostic_cohort=cohort,
        diagnostic_partition=partition,
        diagnostic_submission_template=template,
        draw=False,
    )


def _case_file(path: Path, cases: list[dict]) -> Path:
    path.write_text(
        json.dumps({"schema": "knee.diagnostic-case-inputs/v1", "cases": cases}),
        encoding="utf-8",
    )
    return path


def _case(uid: str, subject: str = "acl", digit: int = 1) -> dict:
    return {
        "study_uid": uid,
        "subject": subject,
        "calls": [
            {
                "question": "ACL",
                "digit": digit,
                "source": "explicit-human-attribution",
                "words": "individually attributed case call",
            }
        ],
    }


def _generated(uid: str, profile: Profile, scratch: Path):
    scratch.mkdir()
    (scratch / "temporary.bin").write_bytes(b"producer-only")

    def factory(selected_uids):
        yield (
            uid,
            (profile,),
            {
                "scratch_path": scratch,
                "producer": "test-generated-reference/v1",
                "full_anatomy_runs": 1,
                "producer_seconds": 0.375,
            },
        )

    return factory


def test_generated_case_teaching_retains_profiles_after_scratch_is_removed(
    tmp_path: Path,
) -> None:
    uid = "study-generated"
    profile = _profile(uid)
    cases = _case_file(tmp_path / "cases.json", [_case(uid)])
    scratch = tmp_path / "scratch"
    args = _args(tmp_path, cases=cases)
    args.diagnostic_output = tmp_path / "teach-output"

    result = run_diagnostic_cli(
        args,
        study_source=_generated(uid, profile, scratch),
    )

    assert result["source_mode"] == "generated_full_reference"
    assert result["cases"] == 1
    assert result["explicit_cases"] == 1
    snapshot = read_store(args.diagnostic_memory)
    assert len(snapshot.cases) == 1
    assert snapshot.cases[0].profile == profile
    assert snapshot.cases[0].calls[0].digit == 1
    from knee.json_store import load_json

    source_record = load_json(
        args.diagnostic_output / "sources" / uid / "manifest.json"
    )
    assert source_record["source"]["source_api"] == "generated"
    assert source_record["source"]["profiles"]["$tuple"][0]["$record_type"] == (
        "knee.diagnosis.models.Profile"
    )
    (scratch / "temporary.bin").unlink()
    scratch.rmdir()
    from knee.diagnosis.evidence import load_source

    restored = load_source(args.diagnostic_output / "sources" / uid)["source"]
    assert restored["study_uid"] == uid
    assert restored["profiles"][0]["fields"]["subject"] == "acl"
    assert restored["profiles"][0]["fields"]["bundle"]["sparse_rows"] == [[0, 1, "2"]]
    assert result["work"]["full_anatomy_runs"] == 1
    assert result["work"]["producer_seconds"] == 0.375
    assert len(result["work"]["studies"]) == 1
    assert result["work"]["studies"][0]["producer_seconds"] == 0.375
    assert result["work"]["fresh_product_construction"] is True
    assert result["work"]["previously_generated_product_read"] is False
    teaching_ledger = json.loads(
        (args.diagnostic_output / "teaching-ledger.json").read_text()
    )
    assert teaching_ledger["label_source"] is None
    assert teaching_ledger["case_declaration"]["case_count"] == 1
    retained = Path(teaching_ledger["case_declaration"]["retained"])
    assert retained.read_bytes() == cases.read_bytes()
    assert (
        teaching_ledger["case_declaration"]["sha256"]
        == result["case_declaration"]["sha256"]
    )


def test_factory_receives_partition_after_selection_and_records_excluded_cases(
    tmp_path: Path,
) -> None:
    cohort_path = tmp_path / "cohort.json"
    cohort_path.write_text(
        json.dumps(
            {
                "schema": "knee.diagnostic-cohort/v1",
                "partitions": {"chosen": ["selected"], "other": ["excluded"]},
                "disjoint_partitions": [["chosen", "other"]],
            }
        ),
        encoding="utf-8",
    )
    cases = _case_file(
        tmp_path / "cases.json", [_case("selected"), _case("excluded", digit=-1)]
    )
    args = _args(
        tmp_path,
        cases=cases,
        cohort=cohort_path,
        partition="chosen",
    )
    args.diagnostic_output = tmp_path / "cohort-output"
    seen_selection = []

    def factory(selected_uids):
        seen_selection.append(selected_uids)
        yield (
            "selected",
            (_profile("selected"),),
            {
                "full_anatomy_runs": 1,
                "producer_seconds": 0.25,
            },
        )

    result = run_diagnostic_cli(args, study_source=factory)

    assert seen_selection == [("selected",)]
    assert result["cohort"]["selected_uids"] == ["selected"]
    assert {case.study_uid for case in read_store(args.diagnostic_memory).cases} == {
        "selected"
    }
    ledger = json.loads((args.diagnostic_output / "teaching-ledger.json").read_text())
    assert ledger["case_declaration"]["excluded_cohort_uids"] == ["excluded"]


def test_unknown_case_uid_in_cohort_fails_before_source_factory(tmp_path: Path) -> None:
    cohort_path = tmp_path / "cohort.json"
    cohort_path.write_text(
        json.dumps(
            {
                "schema": "knee.diagnostic-cohort/v1",
                "partitions": {"chosen": ["selected"]},
                "disjoint_partitions": [],
            }
        ),
        encoding="utf-8",
    )
    cases = _case_file(tmp_path / "cases.json", [_case("not-declared")])
    args = _args(
        tmp_path,
        cases=cases,
        cohort=cohort_path,
        partition="chosen",
    )
    called = False

    def factory(selected_uids):
        nonlocal called
        called = True
        return iter(())

    with pytest.raises(DiagnosticRunError, match="case_study_uid_not_in_cohort"):
        run_diagnostic_cli(args, study_source=factory)
    assert called is False
    assert not args.diagnostic_output.exists()


def test_malformed_case_call_fails_before_source_factory(tmp_path: Path) -> None:
    cases = _case_file(tmp_path / "cases.json", [_case("study", digit=True)])
    args = _args(tmp_path, cases=cases)
    called = False

    def factory(selected_uids):
        nonlocal called
        called = True
        return iter(())

    with pytest.raises(DiagnosticRunError, match="case_digit_invalid"):
        run_diagnostic_cli(args, study_source=factory)
    assert called is False
    assert not args.diagnostic_output.exists()


def test_unmatched_case_uid_without_cohort_is_not_silently_dropped(
    tmp_path: Path,
) -> None:
    uid = "observed-study"
    cases = _case_file(tmp_path / "cases.json", [_case("missing-study")])
    args = _args(tmp_path, cases=cases)
    args.diagnostic_output = tmp_path / "unmatched-output"

    with pytest.raises(DiagnosticRunError, match="case_study_uid_not_supplied"):
        run_diagnostic_cli(
            args,
            study_source=lambda selected: iter(
                [
                    (
                        uid,
                        (_profile(uid),),
                        {"full_anatomy_runs": 1, "producer_seconds": 0.1},
                    )
                ]
            ),
        )
    assert not args.diagnostic_memory.exists()


def test_generated_source_requires_real_work_counters_and_factory_is_exclusive(
    tmp_path: Path,
) -> None:
    cases = _case_file(tmp_path / "cases.json", [_case("study")])
    args = _args(tmp_path, cases=cases)
    args.diagnostic_output = tmp_path / "bad-source"
    with pytest.raises(
        DiagnosticRunError, match="generated_full_anatomy_runs_required"
    ):
        run_diagnostic_cli(
            args,
            study_source=lambda selected: iter(
                [("study", (_profile("study"),), {"producer_seconds": 0.1})]
            ),
        )

    ambiguous = _args(tmp_path, inputs=tmp_path / "recipe.json")
    with pytest.raises(DiagnosticRunError, match="ambiguous_source"):
        run_diagnostic_cli(
            ambiguous,
            study_source=lambda selected: iter(()),
        )


def test_readout_callback_receives_evidence_without_capacity_labels_and_writes_template(
    tmp_path: Path,
) -> None:
    uid = "query-study"
    memory = tmp_path / "memory.json"
    write_store(memory, Snapshot("memory-r7"))
    labels = tmp_path / "train.csv"
    with labels.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(TRAIN_COLUMNS)
        writer.writerow([uid, "source report is provenance", *(["1"] * len(LABELS))])
    template = tmp_path / "template.csv"
    with template.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("StudyInstanceUID", *LABELS))
        writer.writerow((uid, *([""] * len(LABELS))))
    args = _args(
        tmp_path,
        mode="capacity",
        labels=labels,
        template=template,
        memory=memory,
    )
    args.diagnostic_output = tmp_path / "readout-output"
    received = []

    def callback(evidence):
        received.append(evidence)
        assert set(evidence) == set(LABELS)
        assert all("evaluation" not in row for row in evidence.values())
        return {condition: 0.375 for condition in LABELS}

    result = run_diagnostic_cli(
        args,
        study_source=lambda selected: iter(
            [(uid, (), {"full_anatomy_runs": 1, "producer_seconds": 0.5})]
        ),
        probability_readout=callback,
    )

    assert len(received) == 1
    assert result["competition_readout"] == "caller_supplied"
    submission = args.diagnostic_output / "submission.csv"
    assert submission.is_file()
    with submission.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.reader(stream))
    assert tuple(rows[0]) == ("StudyInstanceUID", *LABELS)
    assert rows[1] == [uid, *("0.375" for _ in LABELS)]
    assert result["submission"]["source_provenance"]["memory_revision"] == "memory-r7"


@pytest.mark.parametrize(
    ("template", "callback", "mode", "error"),
    [
        (None, lambda evidence: {}, "infer", "readout_and_template_must_be_paired"),
        (
            Path("template.csv"),
            lambda evidence: {},
            "teach",
            "readout_requires_query_mode",
        ),
    ],
)
def test_readout_requires_complete_flags_and_query_mode(
    tmp_path: Path, template: Path | None, callback, mode: str, error: str
) -> None:
    args = _args(tmp_path, mode=mode, template=template)
    with pytest.raises(DiagnosticRunError, match=error):
        run_diagnostic_cli(args, probability_readout=callback)


def test_cli_arguments_expose_case_input_and_template_without_new_source_route() -> (
    None
):
    parser = ArgumentParser()
    selection = parser.add_mutually_exclusive_group()
    add_arguments(parser, selection)
    args = parser.parse_args(
        [
            "--diagnostic-products",
            "products",
            "--diagnostic-cases",
            "calls.json",
            "--diagnostic-submission-template",
            "template.csv",
        ]
    )
    assert args.diagnostic_cases == Path("calls.json")
    assert args.diagnostic_submission_template == Path("template.csv")


def test_explicit_case_can_reference_composed_diagnosis_profile(tmp_path: Path) -> None:
    uid = "composed-case-study"
    roles = ("acl", "femur", "tibia", "pcl")
    profiles = tuple(_profile(uid, subject) for subject in roles)
    cases = _case_file(
        tmp_path / "composed-cases.json",
        [_case(uid, subject="diagnosis/ACL")],
    )
    args = _args(tmp_path, cases=cases)
    args.diagnostic_output = tmp_path / "composed-output"

    run_diagnostic_cli(
        args,
        study_source=lambda selected: iter(
            [(uid, profiles, {"full_anatomy_runs": 1, "producer_seconds": 0.2})]
        ),
    )

    snapshot = read_store(args.diagnostic_memory)
    assert len(snapshot.cases) == 1
    assert snapshot.cases[0].profile.subject == "diagnosis/ACL"
    assert snapshot.cases[0].profile.source_id == uid


def test_explicit_case_subject_collision_is_named(tmp_path: Path) -> None:
    uid = "composed-collision-study"
    roles = ("acl", "femur", "tibia", "pcl")
    profiles = (
        *(_profile(uid, subject) for subject in roles),
        _profile(uid, "diagnosis/ACL"),
    )
    cases = _case_file(
        tmp_path / "collision-cases.json",
        [_case(uid, subject="diagnosis/ACL")],
    )
    args = _args(tmp_path, cases=cases)
    args.diagnostic_output = tmp_path / "collision-output"

    with pytest.raises(
        DiagnosticRunError, match="diagnostic_case_profile_subject_ambiguous"
    ):
        run_diagnostic_cli(
            args,
            study_source=lambda selected: iter(
                [(uid, profiles, {"full_anatomy_runs": 1, "producer_seconds": 0.2})]
            ),
        )


def test_source_iterator_closes_when_consumer_fails(tmp_path: Path) -> None:
    uid = "cleanup-study"
    closed = []

    def studies(selected):
        try:
            yield uid, (_profile(uid),), {"producer_seconds": 0.2}
            pytest.fail("consumer should stop after invalid work metadata")
        finally:
            closed.append(True)

    args = _args(tmp_path, cases=_case_file(tmp_path / "cleanup.json", [_case(uid)]))
    args.diagnostic_output = tmp_path / "cleanup-output"
    with pytest.raises(
        DiagnosticRunError, match="diagnostic_generated_full_anatomy_runs_required"
    ):
        run_diagnostic_cli(args, study_source=studies)
    assert closed == [True]
