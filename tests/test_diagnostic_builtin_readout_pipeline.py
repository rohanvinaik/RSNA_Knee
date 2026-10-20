"""Production-entry tests for the built-in functional competition readout.

These drive ``run_diagnostic_cli`` and the public submission writer with a
synthetic source.  The built-in policy is never re-implemented here: the
evidence the pipeline hands a caller-supplied readout is captured, the public
``probabilities_for_study`` is applied to that same evidence, and the
pipeline's own built-in output must agree with it.
"""

from __future__ import annotations

import csv
import json
from argparse import Namespace
from pathlib import Path

import pytest

from knee.diagnosis.models import Profile, Snapshot
from knee.diagnosis.pipeline import DiagnosticRunError, run_diagnostic_cli
from knee.diagnosis.readout import POLICY_ID, probabilities_for_study
from knee.diagnosis.store import write_store
from knee.diagnosis.submission import SUBMISSION_COLUMNS, validate_submission
from knee.encoding.counts import BankLayout, CountBundle, CountLayout
from knee.study.tables import LABELS, TRAIN_COLUMNS

QUERY_UID = "query-study"
SOURCE_WORK = {"full_anatomy_runs": 1, "producer_seconds": 0.5}


# ---------------------------------------------------------------------------
# synthetic inputs
# ---------------------------------------------------------------------------


def _profile(uid: str, subject: str = "acl") -> Profile:
    layout = CountLayout("layout-v1", "carrier-v1", (BankLayout("signal", 3),))
    return Profile(
        subject,
        CountBundle(layout, ((0, 2, 0),)),
        "full",
        "object:" + subject,
        uid,
        context=(),
    )


def _args(tmp_path: Path, **overrides) -> Namespace:
    values = {
        "diagnostic_mode": "capacity",
        "diagnostic_products": None,
        "diagnostic_inputs": None,
        "diagnostic_memory": tmp_path / "memory.json",
        "diagnostic_labels": None,
        "diagnostic_cases": None,
        "diagnostic_output": tmp_path / "output",
        "diagnostic_revision": "mvp-r1",
        "diagnostic_pair_products": None,
        "diagnostic_questions": None,
        "diagnostic_trust": None,
        "diagnostic_cohort": None,
        "diagnostic_partition": None,
        "diagnostic_submission_template": None,
        "draw": False,
    }
    values.update(overrides)
    return Namespace(**values)


def _labels_file(path: Path, uid: str, digit: str) -> Path:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(TRAIN_COLUMNS)
        writer.writerow([uid, "source report is provenance", *([digit] * len(LABELS))])
    return path


def _template_file(path: Path, uid: str = QUERY_UID) -> Path:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("StudyInstanceUID", *LABELS))
        writer.writerow((uid, *([""] * len(LABELS))))
    return path


def _source(uid: str = QUERY_UID, profiles: tuple = ()):
    return lambda selected: iter([(uid, profiles, dict(SOURCE_WORK))])


def _capacity_args(
    tmp_path: Path,
    name: str,
    *,
    digit: str = "1",
    template: bool = True,
    memory: Path | None = None,
) -> Namespace:
    """Arguments for one capacity run in its own folder under ``tmp_path``."""
    folder = tmp_path / name
    folder.mkdir()
    store = memory or folder / "memory.json"
    if memory is None:
        write_store(store, Snapshot("memory-r7"))
    return _args(
        folder,
        diagnostic_memory=store,
        diagnostic_labels=_labels_file(folder / "train.csv", QUERY_UID, digit),
        diagnostic_submission_template=(
            _template_file(folder / "template.csv") if template else None
        ),
    )


def _capture_evidence(tmp_path: Path, name: str, profiles: tuple = ()):
    """Run through the existing caller-supplied route, keeping the evidence."""
    args = _capacity_args(tmp_path, name)
    seen: list[dict] = []

    def callback(evidence):
        seen.append(evidence)
        return {label: 0.25 for label in LABELS}

    result = run_diagnostic_cli(
        args, study_source=_source(profiles=profiles), probability_readout=callback
    )
    assert len(seen) == 1
    return args, result, seen[0]


def _submission_values(args: Namespace) -> list[float]:
    with (args.diagnostic_output / "submission.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        rows = list(csv.reader(stream))
    assert tuple(rows[0]) == ("StudyInstanceUID", *LABELS)
    assert len(rows) == 2 and rows[1][0] == QUERY_UID
    return [float(cell) for cell in rows[1][1:]]


def _strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _strings(key)
            yield from _strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings(item)


def _studies_with_readout(output: Path) -> list[tuple[Path, dict]]:
    found = []
    for path in sorted(output.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if isinstance(data, dict) and "readout" in data:
            found.append((path, data))
    return found


# ---------------------------------------------------------------------------
# template alone selects the built-in readout
# ---------------------------------------------------------------------------


def test_template_without_callback_runs_the_builtin_policy_on_the_same_evidence(
    tmp_path: Path,
) -> None:
    _, _, evidence = _capture_evidence(tmp_path, "reference")
    expected = probabilities_for_study(evidence)
    assert set(expected) == set(LABELS)

    args = _capacity_args(tmp_path, "builtin")
    result = run_diagnostic_cli(args, study_source=_source())

    assert result["competition_readout"] == POLICY_ID
    assert _submission_values(args) == [expected[label] for label in LABELS]
    assert result["submission"]["source_provenance"]["memory_revision"] == "memory-r7"


def test_builtin_submission_is_written_by_the_official_writer_for_the_template(
    tmp_path: Path,
) -> None:
    args = _capacity_args(tmp_path, "builtin")
    run_diagnostic_cli(args, study_source=_source())

    submission = args.diagnostic_output / "submission.csv"
    template = args.diagnostic_submission_template
    with submission.open(newline="", encoding="utf-8") as stream:
        header = next(csv.reader(stream))
    assert tuple(header) == SUBMISSION_COLUMNS == ("StudyInstanceUID", *LABELS)
    receipt = validate_submission(template, submission)
    assert receipt["study_count"] == 1
    for value in _submission_values(args):
        assert 0.0 <= value <= 1.0


def test_builtin_details_are_stored_at_the_study_json_readout_key(
    tmp_path: Path,
) -> None:
    args = _capacity_args(tmp_path, "builtin")
    result = run_diagnostic_cli(args, study_source=_source())

    studies = _studies_with_readout(args.diagnostic_output)
    assert studies, "no study JSON carries a 'readout' key"
    for _, data in studies:
        readout = data["readout"]
        assert readout, "readout key is empty"
        text = set(_strings(readout))
        assert POLICY_ID in text
        assert set(LABELS) <= text  # details are reported for every official label
    assert result["competition_readout"] == POLICY_ID


def test_builtin_readout_json_is_stable_across_identical_runs(tmp_path: Path) -> None:
    first = _capacity_args(tmp_path, "first")
    second = _capacity_args(tmp_path, "second")
    run_diagnostic_cli(first, study_source=_source())
    run_diagnostic_cli(second, study_source=_source())

    assert _submission_values(first) == _submission_values(second)
    read_first = [
        d["readout"] for _, d in _studies_with_readout(first.diagnostic_output)
    ]
    read_second = [
        d["readout"] for _, d in _studies_with_readout(second.diagnostic_output)
    ]
    assert read_first and read_first == read_second


# ---------------------------------------------------------------------------
# capacity labels never reach the readout
# ---------------------------------------------------------------------------


def test_capacity_labels_never_reach_the_builtin_readout(tmp_path: Path) -> None:
    all_positive = _capacity_args(tmp_path, "labels-one", digit="1")
    all_negative = _capacity_args(tmp_path, "labels-zero", digit="0")
    run_diagnostic_cli(all_positive, study_source=_source())
    run_diagnostic_cli(all_negative, study_source=_source())

    assert _submission_values(all_positive) == _submission_values(all_negative)
    assert [
        d["readout"] for _, d in _studies_with_readout(all_positive.diagnostic_output)
    ] == [
        d["readout"] for _, d in _studies_with_readout(all_negative.diagnostic_output)
    ]


def test_evidence_handed_to_any_readout_carries_no_capacity_label(
    tmp_path: Path,
) -> None:
    _, _, evidence = _capture_evidence(tmp_path, "reference")
    assert set(evidence) == set(LABELS)
    assert all("evaluation" not in row for row in evidence.values())


# ---------------------------------------------------------------------------
# an explicit callback with a template is unchanged
# ---------------------------------------------------------------------------


def test_explicit_callback_with_template_still_wins_and_is_still_caller_supplied(
    tmp_path: Path,
) -> None:
    args = _capacity_args(tmp_path, "explicit")

    def callback(evidence):
        assert set(evidence) == set(LABELS)
        return {label: 0.375 for label in LABELS}

    result = run_diagnostic_cli(
        args, study_source=_source(), probability_readout=callback
    )

    assert result["competition_readout"] == "caller_supplied"
    assert _submission_values(args) == [0.375] * len(LABELS)
    assert POLICY_ID not in repr(result)
    for _, data in _studies_with_readout(args.diagnostic_output):
        assert POLICY_ID not in repr(data["readout"])


# ---------------------------------------------------------------------------
# argument pairing errors
# ---------------------------------------------------------------------------


def test_callback_without_template_is_an_error_before_any_source_work(
    tmp_path: Path,
) -> None:
    args = _capacity_args(tmp_path, "unpaired", template=False)
    touched = []

    def source(selected):
        touched.append(selected)
        return iter(())

    with pytest.raises(DiagnosticRunError, match="readout_and_template_must_be_paired"):
        run_diagnostic_cli(
            args,
            study_source=source,
            probability_readout=lambda evidence: {label: 0.5 for label in LABELS},
        )
    assert touched == []
    assert not (args.diagnostic_output / "submission.csv").exists()


@pytest.mark.parametrize("with_callback", [False, True])
def test_any_readout_or_template_in_teach_mode_is_an_error(
    tmp_path: Path, with_callback: bool
) -> None:
    folder = tmp_path / ("callback" if with_callback else "template-only")
    folder.mkdir()
    args = _args(
        folder,
        diagnostic_mode="teach",
        diagnostic_submission_template=_template_file(folder / "template.csv"),
    )
    touched = []

    def source(selected):
        touched.append(selected)
        return iter(())

    callback = (lambda evidence: {}) if with_callback else None
    with pytest.raises(
        DiagnosticRunError,
        match="readout_requires_query_mode|readout_and_template_must_be_paired",
    ):
        run_diagnostic_cli(args, study_source=source, probability_readout=callback)
    assert touched == []


def test_callback_alone_in_teach_mode_is_also_an_error(tmp_path: Path) -> None:
    args = _args(tmp_path, diagnostic_mode="teach")
    with pytest.raises(
        DiagnosticRunError,
        match="readout_requires_query_mode|readout_and_template_must_be_paired",
    ):
        run_diagnostic_cli(args, probability_readout=lambda evidence: {})


# ---------------------------------------------------------------------------
# neither supplied is evidence-only
# ---------------------------------------------------------------------------


def test_neither_template_nor_callback_is_evidence_only(tmp_path: Path) -> None:
    args = _capacity_args(tmp_path, "evidence-only", template=False)

    result = run_diagnostic_cli(args, study_source=_source())

    assert not (args.diagnostic_output / "submission.csv").exists()
    assert not list(args.diagnostic_output.rglob("submission*.csv"))
    assert result.get("competition_readout") not in (POLICY_ID, "caller_supplied")
    for _, data in _studies_with_readout(args.diagnostic_output):
        assert POLICY_ID not in repr(data["readout"])


# ---------------------------------------------------------------------------
# a taught memory: the built-in output still equals the policy on the evidence
# ---------------------------------------------------------------------------


def _taught_memory(tmp_path: Path) -> Path:
    folder = tmp_path / "teach"
    folder.mkdir()
    taught_uid = "taught-study"
    cases = folder / "cases.json"
    cases.write_text(
        json.dumps(
            {
                "schema": "knee.diagnostic-case-inputs/v1",
                "cases": [
                    {
                        "study_uid": taught_uid,
                        "subject": "acl",
                        "calls": [
                            {
                                "question": "ACL",
                                "digit": 1,
                                "source": "explicit-human-attribution",
                                "words": "individually attributed case call",
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    args = _args(
        folder,
        diagnostic_mode="teach",
        diagnostic_cases=cases,
        diagnostic_memory=folder / "memory.json",
    )
    run_diagnostic_cli(
        args,
        study_source=lambda selected: iter(
            [(taught_uid, (_profile(taught_uid),), dict(SOURCE_WORK))]
        ),
    )
    return args.diagnostic_memory


def test_builtin_agrees_with_the_policy_when_memory_actually_holds_cases(
    tmp_path: Path,
) -> None:
    memory = _taught_memory(tmp_path)
    profiles = (_profile(QUERY_UID),)

    reference = _capacity_args(tmp_path, "reference", memory=memory)
    seen: list[dict] = []

    def callback(evidence):
        seen.append(evidence)
        return {label: 0.25 for label in LABELS}

    run_diagnostic_cli(
        reference,
        study_source=_source(profiles=profiles),
        probability_readout=callback,
    )
    expected = probabilities_for_study(seen[0])

    builtin = _capacity_args(tmp_path, "builtin", memory=memory)
    result = run_diagnostic_cli(builtin, study_source=_source(profiles=profiles))

    assert result["competition_readout"] == POLICY_ID
    assert _submission_values(builtin) == pytest.approx(
        [expected[label] for label in LABELS], abs=1e-12
    )
    for value in expected.values():
        assert 0.0 <= value <= 1.0
