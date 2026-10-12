"""The composition of the route, through the real study entry point (`specs/route-composition`).

Every claim here is read off the LEDGER of one run over the synthetic corpus, never off the
artifact: design.md's correction two, "a disconnected predicates stage that always returns twelve
abstentions produces the same final file".
"""

import importlib.util
from pathlib import Path

from knee import pipeline
from knee.objects.analysis import AnalysisRequest
from knee.telemetry import recording

_fixture_path = Path(__file__).with_name("test_pipeline_measurements.py")
_fixture_spec = importlib.util.spec_from_file_location(
    "pipeline_measurement_fixture", _fixture_path
)
assert _fixture_spec is not None and _fixture_spec.loader is not None
_fixture_module = importlib.util.module_from_spec(_fixture_spec)
_fixture_spec.loader.exec_module(_fixture_module)
STUDY_UID = _fixture_module.STUDY_UID
_write_corpus = _fixture_module._write_corpus


def _conversing_request() -> AnalysisRequest:
    return AnalysisRequest(
        tile_mm=2.0,
        offsets_mm=(-1.0, 0.0, 1.0),
        direction_lps=(1.0, 0.0, 0.0),
        backend="reference",
        prominence_mm=1.0,
        conversation=True,
    )


def _events(
    tmp_path: Path, request: AnalysisRequest | None
) -> tuple[list[str], pipeline.StudyRun]:
    _write_corpus(tmp_path)
    with recording() as run_ledger:
        result = pipeline.open_and_run(tmp_path, STUDY_UID, request)
    return [event.name for event in run_ledger.events()], result


def _unread_and_phantom(names: list[str]) -> tuple[list[str], list[str]]:
    """The producers no stage read, and the consumptions of a record no stage produced."""
    # A producer is the STAGE that produced -- `ownership.member.produced` is ownership's own
    # sub-unit, and `pairings.produced` is the relations stage's unit read by the relations stage.
    produced = {name.split(".")[0] for name in names if name.endswith(".produced")}
    consumed = {
        name.split(".consumed_by.")[0] for name in names if ".consumed_by." in name
    }
    # The output stage is the route's last reader; the output file is its consumer and is written
    # by the impure edge, outside the ledger. Every other producer must be read by a stage.
    return sorted(produced - consumed - {"output"}), sorted(consumed - produced)


def test_every_produced_record_has_a_consumer(tmp_path: Path) -> None:
    names, _ = _events(tmp_path, _conversing_request())
    unread, phantom = _unread_and_phantom(names)
    assert not unread, f"produced and read by no stage: {unread}"
    # And the reverse: nothing claims to have consumed a record no stage produced.
    assert not phantom, f"consumed but produced by no stage: {phantom}"


def test_a_producer_that_did_not_run_has_no_consumer_in_the_ledger(
    tmp_path: Path,
) -> None:
    # MUST NOT: record the consumption of a record no stage produced. With no analysis request
    # the objects stage never measures and the conversation never runs, and until task 7.14
    # ownership, relations and the bundles recorded having read both (Codex re-review
    # 2026-10-12: "Ownership unconditionally records `conversation.consumed_by.ownership`").
    names, _ = _events(tmp_path, None)
    assert "objects.produced" not in names
    assert "conversation.produced" not in names
    unread, phantom = _unread_and_phantom(names)
    assert not phantom, f"consumed but produced by no stage: {phantom}"
    assert not unread, f"produced and read by no stage: {unread}"


def test_the_conversation_precedes_the_stages_that_read_the_parse(
    tmp_path: Path,
) -> None:
    names, result = _events(tmp_path, _conversing_request())
    assert "conversation.produced" in names
    assert names.index("conversation.produced") < names.index("ownership.produced")
    assert names.index("conversation.produced") < names.index("relations.produced")
    assert "conversation.consumed_by.ownership" in names
    assert all(run.conversation is not None for run in result.series)


def test_no_consumed_event_is_recorded_by_the_route_after_production(
    tmp_path: Path,
) -> None:
    # MUST NOT: the old route-recorded `<stage>.consumed` events said a value was read when
    # nothing had read it. Every consumption now names its consumer.
    names, _ = _events(tmp_path, _conversing_request())
    assert not [name for name in names if name.endswith(".consumed")]


def test_the_attendance_roster_names_every_stage_with_its_own_code(
    tmp_path: Path,
) -> None:
    _, result = _events(tmp_path, _conversing_request())
    assert [stage for stage, _ in result.attendance] == list(pipeline.STAGES)
    codes = dict(result.attendance)
    assert codes["study"] == "present"
    assert codes["relations"] == "construction_absent"
    # The bundles body landed with task 6.7: on a field that resolved extents it writes profiles.
    assert codes["vectors"] == "present"
    assert codes["output"] == "projection_undeclared"
    assert codes["predicates"] == "present"


def test_without_a_conversation_ownership_seats_the_solitary_parse_only(
    tmp_path: Path,
) -> None:
    names, result = _events(
        tmp_path,
        AnalysisRequest(
            2.0, (-1.0, 0.0, 1.0), (1.0, 0.0, 0.0), "reference", prominence_mm=1.0
        ),
    )
    assert "conversation.produced" not in names
    # Nothing claims to have read a conversation that never ran (task 7.14): the ledger keeps a
    # producer that did not run apart from one that ran and handed over nothing.
    assert not [name for name in names if name.startswith("conversation.consumed_by.")]
    for run in result.series:
        assert run.conversation is None
        assert run.ownership is not None
        assert [member.parse for member in run.ownership.members] == ["solitary"]


def test_the_relations_record_carries_the_pairings(tmp_path: Path) -> None:
    _, result = _events(tmp_path, _conversing_request())
    for run in result.series:
        assert run.relations is not None
        assert run.relations.pairings is not None
        assert run.relations.code == "construction_absent"


def test_the_output_refuses_rows_and_keeps_the_companion(tmp_path: Path) -> None:
    _, result = _events(tmp_path, _conversing_request())
    assert result.output is not None
    assert result.output.code == "projection_undeclared"
    assert result.output.rows is None
    assert len(result.output.companion) == 12
