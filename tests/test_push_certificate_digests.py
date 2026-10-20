"""The pre-push scan recognizes only typed function digests from Detective certificates."""

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


def digest(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def finding_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8"), usedforsecurity=False).hexdigest()


def test_certificate_scan_loads_the_named_file_and_recognizes_only_valid_digests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checks = tool()
    valid_a = digest("certificate function a")
    valid_b = digest("certificate function b")
    payload = {
        "src/a.py::function_a": {"function_digest": valid_a, "standing": "complete"},
        "src/b.py::function_b": {"function_digest": valid_b},
        "src/list.py::not_record": [{"function_digest": digest("list item")}],
        "src/string.py::not_record": "not a certificate record",
        "src/missing.py::no_digest": {"standing": "complete"},
        "src/null.py::null_digest": {"function_digest": None},
        "src/number.py::number_digest": {"function_digest": 1234567890123456},
        "src/short.py::short_digest": {"function_digest": valid_a[:-1]},
        "src/long.py::long_digest": {"function_digest": valid_a + "0"},
        "src/upper.py::uppercase_digest": {"function_digest": valid_a.upper()},
        "src/nonhex.py::nonhex_digest": {"function_digest": "g" + valid_a[1:]},
    }
    calls = []

    def mock_git(*arguments: str) -> str:
        calls.append(arguments)
        return json.dumps(payload)

    monkeypatch.setattr(checks, "git", mock_git)
    recognized = checks.certificate_hashes("commit-under-test")

    assert calls == [("show", "commit-under-test:tests/detective/certificates.json")]
    assert recognized == frozenset({finding_hash(valid_a), finding_hash(valid_b)})
    assert (
        checks.finding_verdict(
            checks.CERTIFICATES,
            checks.HEX,
            finding_hash(valid_a),
            recognized,
        )
        == "function_digest"
    )
    assert (
        checks.finding_verdict(
            checks.CERTIFICATES,
            checks.HEX,
            finding_hash(valid_b),
            recognized,
        )
        == "function_digest"
    )


def test_certificate_digest_verdict_requires_the_expected_file_kind_and_hash() -> None:
    checks = tool()
    known = finding_hash(digest("known certificate function"))
    recognized = frozenset({known})

    assert checks.finding_verdict("src/other.py", checks.HEX, known, recognized) == (
        "unexplained"
    )
    assert (
        checks.finding_verdict(checks.CERTIFICATES, "Secret Keyword", known, recognized)
        == "unexplained"
    )
    assert (
        checks.finding_verdict(
            checks.CERTIFICATES,
            checks.HEX,
            finding_hash(digest("unknown certificate function")),
            recognized,
        )
        == "unexplained"
    )


def test_certificate_source_must_be_an_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checks = tool()
    monkeypatch.setattr(checks, "git", lambda *_arguments: json.dumps([]))

    with pytest.raises(checks.Unchecked, match="not an object"):
        checks.certificate_hashes("commit-under-test")


def test_recording_digest_verdict_remains_unchanged() -> None:
    checks = tool()
    known = finding_hash(digest("recording array"))
    assert (
        checks.finding_verdict(checks.RECORDING, checks.HEX, known, frozenset({known}))
        == "recording_digest"
    )


def test_scan_keeps_recording_and_certificate_hashes_scoped_to_their_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checks = tool()
    commit = "commit-under-test"
    recording_digest = digest("recorded array")
    certificate_digest = digest("certified function")
    unrelated_digest = digest("unrelated certificate field")
    certificate_source = {
        "src/module.py::function": {
            "function_digest": certificate_digest,
            "sha256": unrelated_digest,
        }
    }
    recording_source = {"arrays": [recording_digest], "commit": "recorded commit"}
    source_blobs = {
        f"{commit}:{checks.CERTIFICATES}": json.dumps(certificate_source),
        f"{commit}:{checks.RECORDING}": json.dumps(recording_source),
    }
    git_calls = []

    def mock_git(*arguments: str) -> str:
        git_calls.append(arguments)
        if len(arguments) == 2 and arguments[0] == "show":
            return source_blobs[arguments[1]]
        raise AssertionError(f"unexpected git call: {arguments}")

    monkeypatch.setattr(checks, "git", mock_git)
    monkeypatch.setattr(
        checks,
        "commit_additions",
        lambda _sha: {
            checks.RECORDING: ["recording file addition"],
            checks.CERTIFICATES: ["certificate file addition"],
        },
    )
    run_calls = []

    def mock_run(command: list[str], cwd: object = None):
        assert cwd is not None
        exported = {
            path.relative_to(Path(cwd)).as_posix(): path.read_text(encoding="utf-8")
            for path in Path(cwd).rglob("*")
            if path.is_file()
        }
        run_calls.append((command, exported))
        results = {
            f"./{commit}/{checks.RECORDING}": [
                {
                    "type": checks.HEX,
                    "hashed_secret": finding_hash(recording_digest),
                    "line_number": 1,
                }
            ],
            f"./{commit}/{checks.CERTIFICATES}": [
                {
                    "type": checks.HEX,
                    "hashed_secret": finding_hash(certificate_digest),
                    "line_number": 1,
                },
                {
                    "type": checks.HEX,
                    "hashed_secret": finding_hash(unrelated_digest),
                    "line_number": 1,
                },
            ],
        }
        return subprocess.CompletedProcess(
            command, 0, json.dumps({"results": results}), ""
        )

    monkeypatch.setattr(checks, "run", mock_run)
    refusals = checks.scan([commit])

    assert run_calls[0][0][0:3] == ["uvx", checks.DETECT_SECRETS, "scan"]
    assert run_calls[0][1] == {
        f"{commit}/{checks.RECORDING}": "recording file addition\n",
        f"{commit}/{checks.CERTIFICATES}": "certificate file addition\n",
    }
    assert git_calls == [
        ("show", f"{commit}:{checks.RECORDING}"),
        ("show", f"{commit}:{checks.CERTIFICATES}"),
    ]
    assert refusals == [
        f"a possible secret in {commit[:7]} {checks.CERTIFICATES}, added line 1: {checks.HEX}"
    ]
