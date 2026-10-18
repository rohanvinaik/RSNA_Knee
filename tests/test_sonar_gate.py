"""The Sonar step's blocking decision (`scripts/sonar_local.py`, a script beside the run, loaded here
from its path). Only bare correctness blocks (Rohan, 2026-10-18: «only bare correctness issues should be
blocking»): open bugs or vulnerabilities, counted by the search's own total; a search the server did not
answer, so an unread count is never a pass; a failed scan or analysis. A clean analysis passes."""

import importlib.util
from pathlib import Path

TOOL = Path(__file__).resolve().parent.parent / "scripts" / "sonar_local.py"


def tool():
    spec = importlib.util.spec_from_file_location("sonar_local", TOOL)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def answer(http: int, body: dict) -> dict:
    return {"http": http, "body": body}


def issues(total: int, listed: int) -> dict:
    issue = {
        "type": "BUG",
        "rule": "python:S1764",
        "component": "RSNA_Knee:tests/x.py",
        "line": 1,
    }
    paging = {"pageIndex": 1, "pageSize": 500, "total": total}
    return answer(200, {"issues": [issue] * listed, "paging": paging})


def test_a_clean_analysis_passes() -> None:
    assert tool().blocking_failures(0, "SUCCESS", issues(0, 0)) == []


def test_open_bugs_block() -> None:
    assert tool().blocking_failures(0, "SUCCESS", issues(3, 3)) == [
        "3 open bugs or vulnerabilities"
    ]


def test_the_count_is_the_search_total_not_one_page() -> None:
    assert tool().issue_total(issues(501, 500)) == 501


def test_a_refused_search_blocks() -> None:
    refused = answer(400, {"errors": [{"msg": "refused"}]})
    assert tool().blocking_failures(0, "SUCCESS", refused) == [
        "the open bugs and vulnerabilities were not read (HTTP 400)"
    ]


def test_an_answer_without_an_issue_list_is_unread() -> None:
    assert tool().issue_total(answer(200, {"text": "<html>"})) is None


def test_an_answer_without_an_issue_list_blocks() -> None:
    assert tool().blocking_failures(0, "SUCCESS", answer(200, {"text": "<html>"})) == [
        "the open bugs and vulnerabilities were not read (HTTP 200)"
    ]


def test_a_failed_scan_blocks() -> None:
    assert tool().blocking_failures(1, "no task", issues(0, 0)) == [
        "the scanner failed",
        "the analysis task: no task",
    ]


def test_an_analysis_that_did_not_succeed_blocks() -> None:
    assert tool().blocking_failures(0, "FAILED", issues(0, 0)) == [
        "the analysis task: FAILED"
    ]
