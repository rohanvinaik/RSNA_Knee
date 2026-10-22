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


def test_a_teaching_spec_digest_is_accepted() -> None:
    checks = tool()
    digest = sha1("source_memory")
    recording = frozenset({sha1(digest)})
    assert (
        checks.finding_verdict(
            "docs/teaching/seed_categories.json", checks.HEX, sha1(digest), recording
        )
        == "teaching_spec_digest"
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


def test_addition_records_preserve_source_addresses() -> None:
    diff = (
        "diff --git a/wrapper.py b/wrapper.py\n"
        "--- a/wrapper.py\n"
        "+++ b/wrapper.py\n"
        "@@ -10,3 +10,4 @@ a function heading\n"
        " context\n"
        "-old\n"
        "+new\n"
        "+second\n"
        " context\n"
        "\\ No newline at end of file\n"
        "@@ -30 +31 @@\n"
        "-old\n"
        "+last\n"
    )
    assert tool().addition_records(diff) == [(11, "new"), (12, "second"), (31, "last")]


def test_addition_records_keep_merge_result_addresses() -> None:
    diff = (
        "diff --cc wrapper.py\n"
        "@@@ -4,3 -5,3 +8,4 @@@ a function heading\n"
        "- old from first\n"
        " -old from second\n"
        "+ from second parent\n"
        " +from first parent\n"
        "  context\n"
        "++new to both\n"
    )
    assert tool().addition_records(diff) == [(11, "new to both")]


@pytest.mark.parametrize(
    "name", ["EXPECTED_RUNTIME_BUNDLE_ID", "EXPECTED_MEMORY_MANIFEST_SHA256"]
)
@pytest.mark.parametrize("uppercase", [False, True])
def test_public_pin_recognition_reads_the_commit_binding_even_when_only_value_changes(
    name: str, uppercase: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    checks = tool()
    value = hashlib.sha256(name.encode()).hexdigest()
    if uppercase:
        value = value.upper()
    source = f'# public release\n{name}: str | None = (\n    "{value}"\n)\n'
    diff = f'@@ -3 +3 @@\n-    "old"\n+    "{value}"\n'
    calls = []

    def mock_git(*arguments: str) -> str:
        calls.append(arguments)
        return (
            source if arguments == ("show", f"revision:{checks.RELEASE_PINS}") else diff
        )

    monkeypatch.setattr(checks, "git", mock_git)
    assert checks.release_pin_hashes("revision") == {1: frozenset({sha1(value)})}
    assert calls == [
        ("show", f"revision:{checks.RELEASE_PINS}"),
        (
            "show",
            "--format=",
            "--unified=0",
            "--no-color",
            "--no-ext-diff",
            "--cc",
            "revision",
            "--",
            checks.RELEASE_PINS,
        ),
    ]
    assert (
        checks.finding_verdict(
            checks.RELEASE_PINS, checks.HEX, sha1(value), frozenset({sha1(value)})
        )
        == "public_digest_pin"
    )


@pytest.mark.parametrize(
    "assignment",
    [
        'PAYLOAD = "{value}"',
        'OTHER_SHA256 = "{value}"',
        'EXPECTED_MEMORY_MANIFEST_SHA256 = "{value}0"',
        'EXPECTED_MEMORY_MANIFEST_SHA256 = "{bad}"',
        'EXPECTED_MEMORY_MANIFEST_SHA256 = "{short}"',
        "EXPECTED_MEMORY_MANIFEST_SHA256 = None",
        "EXPECTED_MEMORY_MANIFEST_SHA256 = 123",
        'EXPECTED_MEMORY_MANIFEST_SHA256 = str("{value}")',
        'EXPECTED_MEMORY_MANIFEST_SHA256 = TOKEN = "{value}"',
        'def nested():\n    EXPECTED_MEMORY_MANIFEST_SHA256 = "{value}"',
        'EXPECTED_MEMORY_MANIFEST_SHA256 = "{value}"; TOKEN = "{value}"',
    ],
)
def test_public_pin_recognition_refuses_untyped_malformed_or_ambiguous_bindings(
    assignment: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    checks = tool()
    value = hashlib.sha256(b"not a public pin").hexdigest()
    source = (
        assignment.format(value=value, short=value[:-1], bad=value[:-1] + "g") + "\n"
    )
    diff = "@@ -0,0 +1,2 @@\n" + "".join(f"+{line}\n" for line in source.splitlines())
    monkeypatch.setattr(checks, "git", lambda *args: source if len(args) == 2 else diff)
    assert checks.release_pin_hashes("revision") == {}


def test_public_pin_verdict_does_not_explain_tokens_passwords_or_other_paths() -> None:
    checks = tool()
    known = sha1(hashlib.sha256(b"public pin").hexdigest())
    recognized = frozenset({known})
    for kind in ("Secret Keyword", "GitHub Token", "Base64 High Entropy String"):
        assert checks.finding_verdict(checks.RELEASE_PINS, kind, known, recognized) == (
            "unexplained"
        )
    assert checks.finding_verdict("src/other.py", checks.HEX, known, recognized) == (
        "unexplained"
    )
    assert checks.finding_verdict(
        checks.RELEASE_PINS, checks.HEX, sha1("other"), recognized
    ) == ("unexplained")


def test_unreadable_public_pin_syntax_cannot_become_an_exemption(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checks = tool()
    monkeypatch.setattr(checks, "git", lambda *_: "not valid python !")
    with pytest.raises(checks.Unchecked, match="release pin source cannot be parsed"):
        checks.release_pin_hashes("revision")


def test_scan_accepts_only_pin_occurrences_and_still_refuses_secrets_in_the_wrapper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checks = tool()
    value = hashlib.sha256(b"public release pin").hexdigest()
    memory = hashlib.sha256(b"public memory pin").hexdigest()
    lines = [
        "EXPECTED_RUNTIME_BUNDLE_ID: str | None = (",
        f'    "{value}"',
        ")",
        f'EXPECTED_MEMORY_MANIFEST_SHA256 = "{memory}"',
        f'PAYLOAD = "{value}"',
        f'PASSWORD = "{memory}"',
        'TOKEN = "synthetic token"',
    ]
    source = "\n".join(lines) + "\n"
    # The added-line addresses differ from source addresses. The binding itself
    # need not change for a literal pin update to be recognized.
    added = [lines[i] for i in (1, 3, 4, 5, 6)]
    diff = (
        f'@@ -2 +2 @@\n-    "old"\n+{lines[1]}\n'
        + "@@ -4,4 +4,4 @@\n"
        + "".join(f"+{line}\n" for line in lines[3:])
    )
    monkeypatch.setattr(checks, "git", lambda *args: source if len(args) == 2 else diff)
    monkeypatch.setattr(
        checks, "commit_additions", lambda _: {checks.RELEASE_PINS: added}
    )
    findings = [
        {"type": kind, "hashed_secret": sha1(text), "line_number": number}
        for number, kind, text in (
            (1, checks.HEX, value),
            (2, checks.HEX, memory),
            (3, checks.HEX, value),
            (4, "Secret Keyword", memory),
            (5, "GitHub Token", "synthetic token"),
        )
    ]

    def mock_run(command, cwd=None):
        assert command == ["uvx", checks.DETECT_SECRETS, "scan", "--all-files", "."]
        assert (Path(cwd) / "revision" / checks.RELEASE_PINS).read_text() == (
            "\n".join(added) + "\n"
        )
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps({"results": {f"revision/{checks.RELEASE_PINS}": findings}}),
            "",
        )

    monkeypatch.setattr(checks, "run", mock_run)
    assert checks.scan(["revision"]) == [
        f"a possible secret in revisio {checks.RELEASE_PINS}, added line {number}: {kind}"
        for number, kind in (
            (3, checks.HEX),
            (4, "Secret Keyword"),
            (5, "GitHub Token"),
        )
    ]


def fixture_value() -> str:
    return hashlib.sha256(b"public fixture manifest").hexdigest()


def fixture_git(source: str, diff: str):
    return lambda *args: source if len(args) == 2 else diff


def test_public_fixture_digest_is_accepted_at_its_exact_binding_and_line(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checks = tool()
    value = fixture_value()
    source = f'"""doc"""\nV1_MANIFEST_SHA256 = "{value}"\n'
    diff = f'@@ -0,0 +2 @@\n+V1_MANIFEST_SHA256 = "{value}"\n'
    monkeypatch.setattr(checks, "git", fixture_git(source, diff))
    assert checks.fixture_digest_hashes("revision") == {1: frozenset({sha1(value)})}
    assert (
        checks.finding_verdict(
            checks.FIXTURE_DIGEST, checks.HEX, sha1(value), frozenset({sha1(value)})
        )
        == "public_fixture_digest"
    )


def test_public_fixture_digest_is_refused_elsewhere(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checks = tool()
    value = fixture_value()
    known = frozenset({sha1(value)})
    assert checks.finding_verdict("tests/other.py", checks.HEX, sha1(value), known) == (
        "unexplained"
    )
    for kind in ("Secret Keyword", "GitHub Token"):
        assert checks.finding_verdict(
            checks.FIXTURE_DIGEST, kind, sha1(value), known
        ) == ("unexplained")
    # wrong added line: the finding's line is not the bound literal's
    monkeypatch.setattr(
        checks,
        "git",
        fixture_git(
            f'V1_MANIFEST_SHA256 = "{value}"\n',
            f'@@ -0,0 +1,2 @@\n+V1_MANIFEST_SHA256 = "{value}"\n+OTHER = "{value}"\n',
        ),
    )
    assert checks.fixture_digest_hashes("revision").get(2) is None
    for assignment in (
        'OTHER = "{value}"',
        'V1_MANIFEST_SHA256 = "{value}0"',
        'V1_MANIFEST_SHA256 = "{short}"',
        'V1_MANIFEST_SHA256 = str("{value}")',
        'V1_MANIFEST_SHA256 = ALIAS = "{value}"',
        'def nested():\n    V1_MANIFEST_SHA256 = "{value}"',
        'V1_MANIFEST_SHA256 = "{value}"; TOKEN = "{value}"',
    ):
        source = assignment.format(value=value, short=value[:-1]) + "\n"
        diff = "@@ -0,0 +1,2 @@\n" + "".join(
            f"+{line}\n" for line in source.splitlines()
        )
        monkeypatch.setattr(checks, "git", fixture_git(source, diff))
        assert checks.fixture_digest_hashes("revision") == {}


def test_scan_accepts_the_fixture_hex_finding_but_refuses_a_keyword_with_its_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checks = tool()
    value = fixture_value()
    lines = [f'V1_MANIFEST_SHA256 = "{value}"', f'PASSWORD = "{value}"']
    source = "\n".join(lines) + "\n"
    diff = "@@ -0,0 +1,2 @@\n" + "".join(f"+{line}\n" for line in lines)
    monkeypatch.setattr(checks, "git", fixture_git(source, diff))
    monkeypatch.setattr(
        checks, "commit_additions", lambda _: {checks.FIXTURE_DIGEST: lines}
    )
    findings = [
        {"type": kind, "hashed_secret": sha1(value), "line_number": number}
        for number, kind in ((1, checks.HEX), (2, "Secret Keyword"), (2, checks.HEX))
    ]

    def mock_run(command, cwd=None):
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps({"results": {f"revision/{checks.FIXTURE_DIGEST}": findings}}),
            "",
        )

    monkeypatch.setattr(checks, "run", mock_run)
    assert checks.scan(["revision"]) == [
        f"a possible secret in revisio {checks.FIXTURE_DIGEST}, added line 2: {kind}"
        for kind in ("Secret Keyword", checks.HEX)
    ]
