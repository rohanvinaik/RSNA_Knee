"""The pre-push gate's decisions (`scripts/push_checks.py`, a script beside the run, loaded here from its
path): what a pushed ref needs from the gate, which secret-scan findings are the kernel-benchmark
recording's own digests, which lines a diff adds, and the lockfile audit's named result, which refuses no
push while the secret scan does. Rohan, 2026-10-18: «Set it as an automatic hook». The audit reports have
the shapes pip-audit 2.10.1 wrote on 2026-10-18: a clean package, flask 0.5 with a flaw it listed twice,
and a package that is not on PyPI. No commit, tree or digest is written out here: each is made when the
test runs, so the hook's own secret scan finds nothing in this file."""

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parent.parent / "scripts" / "push_checks.py"


def tool():
    spec = importlib.util.spec_from_file_location("push_checks", TOOL)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha1(text: str) -> str:
    return hashlib.sha1(text.encode(), usedforsecurity=False).hexdigest()


COMMIT, OTHER = sha1("commit"), sha1("another commit")
TREE, OTHER_TREE = sha1("tree"), sha1("another tree")


def test_a_deletion_needs_no_gate() -> None:
    checks = tool()
    assert checks.ref_check(checks.ZERO, "", frozenset(), COMMIT, False) == "deletion"


def test_a_tree_the_gate_passed_on_is_not_gated_again() -> None:
    checks = tool()
    passed = frozenset({TREE})
    assert (
        checks.ref_check(COMMIT, TREE, passed, COMMIT, True)
        == "gate_passed_on_this_tree"
    )
    assert (
        checks.ref_check(OTHER, TREE, passed, COMMIT, False)
        == "gate_passed_on_this_tree"
    )


def test_the_clean_checkout_is_gated_now() -> None:
    assert (
        tool().ref_check(COMMIT, TREE, frozenset({OTHER_TREE}), COMMIT, True)
        == "gate_runs_now"
    )


def test_a_changed_working_tree_cannot_stand_for_the_pushed_tree() -> None:
    assert (
        tool().ref_check(COMMIT, TREE, frozenset(), COMMIT, False)
        == "gate_not_run_on_this_tree"
    )


def test_a_commit_other_than_the_checkout_cannot_be_gated_here() -> None:
    assert (
        tool().ref_check(OTHER, TREE, frozenset(), COMMIT, True)
        == "gate_not_run_on_this_tree"
    )


def test_a_recording_digest_is_accepted() -> None:
    checks = tool()
    digest = sha1("array")
    recording = frozenset({sha1(digest)})
    assert (
        checks.finding_verdict(checks.RECORDING, checks.HEX, sha1(digest), recording)
        == "recording_digest"
    )


def test_the_same_string_elsewhere_is_unexplained() -> None:
    checks = tool()
    recording = frozenset({sha1("array")})
    assert (
        checks.finding_verdict("docs/notes.md", checks.HEX, sha1("array"), recording)
        == "unexplained"
    )


def test_another_kind_of_finding_in_the_recording_is_unexplained() -> None:
    checks = tool()
    recording = frozenset({sha1("array")})
    assert (
        checks.finding_verdict(
            checks.RECORDING, "Secret Keyword", sha1("array"), recording
        )
        == "unexplained"
    )


def test_a_string_the_recording_does_not_hold_is_unexplained() -> None:
    checks = tool()
    recording = frozenset({sha1("array")})
    assert (
        checks.finding_verdict(checks.RECORDING, checks.HEX, sha1("planted"), recording)
        == "unexplained"
    )


def test_the_lines_a_diff_adds_leave_its_headers_out() -> None:
    diff = (
        "diff --git a/notes.md b/notes.md\n"
        "index 1111111..2222222 100644\n"
        "--- a/notes.md\n"
        "+++ b/notes.md\n"
        "@@ -1,0 +2,2 @@\n"
        "+a new line\n"
        "+++ a line that begins with two plus signs\n"
        "-a removed line\n"
    )
    assert tool().added_lines(diff) == [
        "a new line",
        "++ a line that begins with two plus signs",
    ]


def test_a_binary_change_adds_no_lines() -> None:
    diff = (
        "diff --git a/arrays.npz b/arrays.npz\n"
        "index 1111111..2222222 100644\n"
        "Binary files a/arrays.npz and b/arrays.npz differ\n"
    )
    assert tool().added_lines(diff) == []


def test_a_merge_adds_only_the_lines_no_parent_has() -> None:
    diff = (
        "diff --cc notes.md\n"
        "index 1111111,2222222..3333333\n"
        "--- a/notes.md\n"
        "+++ b/notes.md\n"
        "@@@ -1,1 -1,1 +1,1 @@@\n"
        "- main\n"
        " -side\n"
        "+ a line from the second parent\n"
        " +a line from the first parent\n"
        "++resolved\n"
    )
    assert tool().added_lines(diff) == ["resolved"]


def git_in(repo: Path, *arguments: str, check: bool = True) -> None:
    subprocess.run(
        [
            "git",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "user.email=test@example.invalid",
            "-c",
            "user.name=test",
            *arguments,
        ],
        cwd=repo,
        capture_output=True,
        check=check,
    )


def test_a_commit_adds_its_lines_and_a_merge_only_what_it_resolves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checks = tool()
    notes = tmp_path / "notes.md"
    git_in(tmp_path, "init", "-q", "-b", "main")
    notes.write_text("base\n", encoding="utf-8")
    git_in(tmp_path, "add", "-A")
    git_in(tmp_path, "commit", "-q", "-m", "base")
    git_in(tmp_path, "checkout", "-q", "-b", "side")
    notes.write_text("side\n", encoding="utf-8")
    git_in(tmp_path, "commit", "-q", "-am", "side")
    git_in(tmp_path, "checkout", "-q", "main")
    notes.write_text("main\n", encoding="utf-8")
    git_in(tmp_path, "commit", "-q", "-am", "main")
    git_in(tmp_path, "merge", "-q", "side", check=False)
    notes.write_text("resolved\n", encoding="utf-8")
    git_in(tmp_path, "commit", "-q", "-am", "conflicted merge")
    git_in(tmp_path, "checkout", "-q", "-b", "other")
    (tmp_path / "other.md").write_text("other\n", encoding="utf-8")
    git_in(tmp_path, "add", "-A")
    git_in(tmp_path, "commit", "-q", "-m", "other")
    git_in(tmp_path, "checkout", "-q", "main")
    git_in(tmp_path, "merge", "-q", "--no-ff", "-m", "clean merge", "other")
    monkeypatch.setattr(checks, "ROOT", tmp_path)
    assert checks.commit_additions("side") == {"notes.md": ["side"]}
    assert checks.commit_additions("main~1") == {"notes.md": ["resolved"]}
    assert checks.commit_additions("other") == {"other.md": ["other"]}
    assert checks.commit_additions("main") == {}


def report(*entries: object) -> dict[str, object]:
    return {"dependencies": list(entries), "fixes": []}


CLEAN = {"name": "six", "version": "1.17.0", "vulns": []}
FLAW = {
    "id": "PYSEC-2018-66",
    "fix_versions": ["0.12.3"],
    "aliases": ["CVE-2018-1000656"],
    "description": "Improper input validation in flask before 0.12.3.",
}
FLAWED = {"name": "flask", "version": "0.5", "vulns": [FLAW, FLAW]}
SKIPPED = {
    "name": "rsna-knee-no-such-package-20261018",
    "skip_reason": "Dependency not found on PyPI and could not be audited:"
    " rsna-knee-no-such-package-20261018 (1.0)",
}
UNFIXED = {
    "name": "pillow",
    "version": "1.0",
    "vulns": [{"id": "PYSEC-0000-0", "fix_versions": [], "aliases": []}],
}


def test_a_known_flaw_is_flaws_found() -> None:
    assert tool().audit_result(report(CLEAN, FLAWED)) == "flaws_found"


def test_packages_audited_without_a_flaw_are_no_known_flaws() -> None:
    checks = tool()
    assert checks.audit_result(report(CLEAN)) == "no_known_flaws"
    assert checks.audit_result(report(CLEAN, SKIPPED)) == "no_known_flaws"


def test_no_report_is_never_a_clean_audit() -> None:
    checks = tool()
    for written in (
        None,
        {},
        [],
        "No known vulnerabilities found",
        {"dependencies": "six"},
    ):
        assert checks.audit_result(written) == "audit_did_not_run"


def test_a_report_that_audited_nothing_is_not_a_clean_audit() -> None:
    checks = tool()
    assert checks.audit_result(report()) == "audit_did_not_run"
    assert checks.audit_result(report(SKIPPED)) == "audit_did_not_run"


def test_an_entry_that_cannot_be_read_keeps_the_audit_from_being_clean() -> None:
    checks = tool()
    unreadable = {"name": "six", "version": "1.17.0", "vulns": None}
    assert checks.audit_result(report(CLEAN, "six 1.17.0")) == "audit_did_not_run"
    assert checks.audit_result(report(CLEAN, unreadable)) == "audit_did_not_run"
    assert checks.audit_result(report(FLAWED, "six 1.17.0")) == "flaws_found"


def test_each_flaw_is_printed_once_and_each_skipped_package_with_its_reason() -> None:
    assert tool().audit_lines(report(CLEAN, FLAWED, SKIPPED, UNFIXED)) == [
        "flask 0.5: PYSEC-2018-66 (also CVE-2018-1000656); fixed in 0.12.3",
        (
            "rsna-knee-no-such-package-20261018: not audited: Dependency not found on PyPI"
            " and could not be audited: rsna-knee-no-such-package-20261018 (1.0)"
        ),
        "pillow 1.0: PYSEC-0000-0; no fixed version yet",
    ]


def pip_audit_writing(text: str | None, messages: str):
    """A stand-in for `run`: `uv export` succeeds, and pip-audit writes `text` as its report (no report
    when None) and prints `messages`."""

    def run(command: list[str], cwd: object = None, env: object = None):
        if command[0] == "uvx" and text is not None:
            output = Path(command[command.index("--output") + 1])
            output.write_text(text, encoding="utf-8")
        printed = messages if command[0] == "uvx" else ""
        return subprocess.CompletedProcess(command, 0, "", printed)

    return run


def test_the_audit_names_the_flaws_in_the_report_pip_audit_writes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    checks = tool()
    written = json.dumps(report(CLEAN, FLAWED))
    messages = "Found 2 known vulnerabilities in 1 package\n"
    monkeypatch.setattr(checks, "run", pip_audit_writing(written, messages))
    assert checks.audit() == "flaws_found"
    printed = capsys.readouterr().out
    assert (
        "flask 0.5: PYSEC-2018-66 (also CVE-2018-1000656); fixed in 0.12.3" in printed
    )
    assert "Found 2 known vulnerabilities in 1 package" in printed


def test_an_audit_without_a_readable_report_did_not_run(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    checks = tool()
    messages = "ERROR:pip_audit._cli:invalid requirements input\n"
    monkeypatch.setattr(checks, "run", pip_audit_writing(None, messages))
    assert checks.audit() == "audit_did_not_run"
    assert "invalid requirements input" in capsys.readouterr().out
    monkeypatch.setattr(checks, "run", pip_audit_writing("not a report", ""))
    assert checks.audit() == "audit_did_not_run"
    assert "its report could not be read" in capsys.readouterr().out


def test_an_audit_whose_tools_cannot_start_did_not_run(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    checks = tool()

    def missing(command: list[str], cwd: object = None, env: object = None):
        raise checks.Unchecked(f"{command[0]} could not be run: not found")

    monkeypatch.setattr(checks, "run", missing)
    assert checks.audit() == "audit_did_not_run"
    assert "uv could not be run" in capsys.readouterr().out


def test_the_audit_refuses_no_push_and_the_secret_scan_does(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    checks = tool()
    answers = {
        ("rev-parse", "HEAD"): COMMIT,
        ("status", "--porcelain"): "",
        ("rev-parse", f"{COMMIT}^{{tree}}"): TREE,
    }
    monkeypatch.setattr(checks, "git", lambda *arguments: answers[arguments])
    monkeypatch.setattr(checks, "passed_trees", lambda: frozenset({TREE}))
    monkeypatch.setattr(checks, "pushed_commits", lambda *_: [COMMIT])
    pushed = [["refs/heads/main", COMMIT, "refs/heads/main", OTHER]]

    def push(result: str, refusals: list[str]) -> int:
        monkeypatch.setattr(checks, "audit", lambda: result)
        monkeypatch.setattr(checks, "scan", lambda _commits: refusals)
        return checks.hook("origin", pushed)

    assert push("flaws_found", []) == 0
    assert "the lockfile audit's result is flaws_found" in capsys.readouterr().out
    assert push("audit_did_not_run", []) == 0
    assert push("no_known_flaws", []) == 0
    assert push("no_known_flaws", ["a possible secret in a pushed line"]) == 1
    assert "REFUSED: a possible secret in a pushed line" in capsys.readouterr().out
