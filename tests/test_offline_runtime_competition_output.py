from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SUPERVISOR_PATH = (
    Path(__file__).parents[1] / "scripts/offline_runtime/supervise_offline.py"
)
SPEC = importlib.util.spec_from_file_location(
    "offline_runtime_supervisor_competition", SUPERVISOR_PATH
)
assert SPEC is not None and SPEC.loader is not None
SUPERVISOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUPERVISOR)

BASE_ARGV = [
    "supervisor",
    "public-test",
    "--data-root",
    "data",
    "--output-root",
    "out",
    "--scratch-root",
    "scratch",
    "--context",
    "context",
    "--build-metadata",
    "build.json",
    "--image",
    "image",
    "--image-id",
    "sha256:image",
]


def test_competition_case_arguments_imply_encoding_without_duplicate() -> None:
    args = SUPERVISOR.case_arguments("public-test", competition_output=True)
    assert args[-3:] == ["--competition-output", "--encoding-run", "/out/encoding"]
    assert "--encode-objects" not in args
    both = SUPERVISOR.case_arguments(
        "public-test", encode_objects=True, competition_output=True
    )
    assert both.count("--encoding-run") == 1
    assert "--encode-objects" not in both


def test_default_and_encode_objects_arguments_unchanged() -> None:
    assert SUPERVISOR.case_arguments("public-test") == [
        "--split",
        "test",
        "--workers",
        "4",
    ]
    encoded = SUPERVISOR.case_arguments("public-test", encode_objects=True)
    assert encoded[-3:] == ["--encode-objects", "--encoding-run", "/out/encoding"]
    assert "--competition-output" not in encoded


@pytest.mark.parametrize("bad", [1, 0, "yes", None])
def test_competition_flag_must_be_bool(bad) -> None:
    with pytest.raises(TypeError, match="competition_output_must_be_bool"):
        SUPERVISOR.case_arguments("public-test", competition_output=bad)


def test_run_case_rejects_nonbool_before_side_effects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def no_docker(*_a, **_k):
        pytest.fail("no Docker/filesystem side effects before validation")

    monkeypatch.setattr(SUPERVISOR, "inspect_image", no_docker)
    monkeypatch.setattr(SUPERVISOR, "run", no_docker)
    out = tmp_path / "output"
    scratch = tmp_path / "scratch"
    common = {
        "data_root": tmp_path / "data",
        "output_root": out,
        "scratch_root": scratch,
        "context": tmp_path / "context",
        "build_metadata_path": tmp_path / "build.json",
        "image_ref": "image",
        "expected_image_id": "sha256:x",
        "workers": 4,
        "interval": 1.0,
        "timeout_seconds": 30.0,
    }
    with pytest.raises(TypeError, match="competition_output_must_be_bool"):
        SUPERVISOR.run_case("public-test", competition_output=1, **common)
    with pytest.raises(TypeError, match="encode_objects_must_be_bool"):
        SUPERVISOR.run_case("public-test", encode_objects="yes", **common)
    assert not out.exists() and not scratch.exists()


def test_main_forwards_competition_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[dict] = []

    def fake_run_case(*_args, **kwargs):
        captured.append(kwargs)
        return {"exit_code": 0, "status": "completed"}

    monkeypatch.setattr(SUPERVISOR, "run_case", fake_run_case)
    monkeypatch.setattr(sys, "argv", BASE_ARGV + ["--competition-output"])
    assert SUPERVISOR.main() == 0
    assert captured[-1]["competition_output"] is True
    assert captured[-1]["encode_objects"] is False
    monkeypatch.setattr(sys, "argv", BASE_ARGV)
    assert SUPERVISOR.main() == 0
    assert captured[-1]["competition_output"] is False


def _run_fake_case(tmp_path: Path, monkeypatch, **flags) -> dict:
    data_root = tmp_path / "data"
    data_root.mkdir()
    context = tmp_path / "context"
    context.mkdir()
    (context / "source-manifest.json").write_text(
        '{"source_revision":"revision-a","source_tree_sha256":"tree-a",'
        '"runtime_dependency_lock_sha256":"lock-a",'
        '"runtime_dependency_export_sha256":"export-a",'
        '"files":[{"path":"scripts/run_interiors.py","sha256":"runner-a"}]}'
    )
    build_path = tmp_path / "build.json"
    build_path.write_text(
        '{"base_image":"python:3.14-slim@sha256:base-a",'
        '"source_revision":"revision-a","source_tree_sha256":"tree-a"}'
    )
    image = {
        "image_id": "sha256:image-a",
        "os": "linux",
        "architecture": "amd64",
        "labels": {
            "org.opencontainers.image.revision": "revision-a",
            "org.rsna-knee.source-tree-sha256": "tree-a",
        },
    }
    monkeypatch.setattr(SUPERVISOR, "inspect_image", lambda _ref: image)

    class Process:
        returncode = 0

        def __init__(self, command, **_kwargs):
            self.command = command

        def poll(self):
            return 0

        def wait(self, timeout=None):
            return 0

    monkeypatch.setattr(SUPERVISOR.subprocess, "Popen", Process)

    def fake_run(command, *, timeout=15.0):
        CP = SUPERVISOR.subprocess.CompletedProcess
        if command[:3] == ["docker", "info", "--format"]:
            text = (
                "34359738368\n" if command[-1] == "{{.MemTotal}}" else "linux/aarch64\n"
            )
            return CP(command, 0, text, "")
        if command[:2] == ["docker", "stats"]:
            return CP(command, 0, "0%|1MiB / 24GiB|2|0B / 0B\n", "")
        if command[:2] == ["docker", "rm"]:
            return CP(command, 0, "removed", "")
        return CP(command, 1, "", "not found")

    monkeypatch.setattr(SUPERVISOR, "run", fake_run)
    monkeypatch.setattr(SUPERVISOR, "folder_size", lambda _p: (0, 0))
    monkeypatch.setattr(SUPERVISOR.time, "sleep", lambda _s: None)
    return SUPERVISOR.run_case(
        "public-test",
        data_root=data_root,
        output_root=tmp_path / "output",
        scratch_root=tmp_path / "scratch",
        context=context,
        build_metadata_path=build_path,
        image_ref="image-ref",
        expected_image_id="sha256:image-a",
        workers=4,
        interval=0.01,
        timeout_seconds=30.0,
        **flags,
    )


def _value_after(argv: list[str], flag: str) -> str:
    return argv[argv.index(flag) + 1]


def test_run_case_competition_puts_intermediates_on_scratch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _run_fake_case(tmp_path, monkeypatch, competition_output=True)
    argv = result["argv_in_container"]
    assert "--competition-output" in argv
    assert "--encode-objects" not in argv
    assert _value_after(argv, "--run") == "/scratch/interiors"
    assert _value_after(argv, "--main-run") == "/scratch/main"
    assert _value_after(argv, "--encoding-run") == "/out/encoding"
    assert result["competition_output_enabled"] is True
    assert result["object_encoding_enabled"] is True
    assert result["encoding_run_in_container"] == "/out/encoding"
    roots = result["intermediate_roots"]
    assert roots["location"] == "scratch"
    assert roots["recognition_run_host"].startswith(result["scratch_root"])
    assert roots["main_run_host"].startswith(result["scratch_root"])
    assert "released" in roots["lifetime"]
    # Final retained encoding is still inside the output mount budget.
    assert not _value_after(argv, "--encoding-run").startswith("/scratch")
    # Memory/network/mount settings unchanged.
    docker = result["docker_argv"]
    assert _value_after(docker, "--network") == "none"
    assert _value_after(docker, "--memory") == str(SUPERVISOR.DEFAULT_MEMORY_BYTES)


def test_run_case_default_keeps_output_intermediates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _run_fake_case(tmp_path, monkeypatch)
    argv = result["argv_in_container"]
    assert _value_after(argv, "--run") == "/out/interiors"
    assert _value_after(argv, "--main-run") == "/out/main"
    assert "--competition-output" not in argv
    assert "--encoding-run" not in argv
    assert result["competition_output_enabled"] is False
    assert result["object_encoding_enabled"] is False
    assert result["encoding_run_in_container"] is None
    assert result["intermediate_roots"]["location"] == "output"


def test_run_case_encode_objects_only_keeps_output_intermediates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _run_fake_case(tmp_path, monkeypatch, encode_objects=True)
    argv = result["argv_in_container"]
    assert "--encode-objects" in argv
    assert "--competition-output" not in argv
    assert _value_after(argv, "--run") == "/out/interiors"
    assert result["competition_output_enabled"] is False
    assert result["object_encoding_enabled"] is True
    assert result["encoding_run_in_container"] == "/out/encoding"
