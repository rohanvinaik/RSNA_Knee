from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import pytest

SUPERVISOR_PATH = (
    Path(__file__).parents[1] / "scripts/offline_runtime/supervise_offline.py"
)
SPEC = importlib.util.spec_from_file_location(
    "offline_runtime_supervisor", SUPERVISOR_PATH
)
assert SPEC is not None and SPEC.loader is not None
SUPERVISOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUPERVISOR)


def test_main_fails_budget_overrun_even_when_cli_exited_zero(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
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
        ],
    )
    monkeypatch.setattr(
        SUPERVISOR,
        "run_case",
        lambda *_args, **_kwargs: {"exit_code": 0, "status": "output_budget_exceeded"},
    )
    assert SUPERVISOR.main() == 1


def test_main_forwards_encoding_flag_to_run_case(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
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
            "--encode-objects",
        ],
    )
    captured = {}

    def fake_run_case(*_args, **kwargs):
        captured.update(kwargs)
        return {"exit_code": 0, "status": "completed"}

    monkeypatch.setattr(SUPERVISOR, "run_case", fake_run_case)
    assert SUPERVISOR.main() == 0
    assert captured["encode_objects"] is True


def test_case_arguments_use_requested_worker_count() -> None:
    proof = SUPERVISOR.case_arguments("proof-bursa-parallel")
    assert proof[-2:] == ["--workers", "4"]
    assert SUPERVISOR.case_arguments("proof-bursa-parallel", 1)[-2:] == [
        "--workers",
        "1",
    ]
    assert SUPERVISOR.case_arguments("public-test") == [
        "--split",
        "test",
        "--workers",
        "4",
    ]
    assert SUPERVISOR.case_arguments("labeled-cohort") == [
        "--labeled",
        "--workers",
        "4",
    ]
    assert "TMPDIR=/tmp" in SUPERVISOR.THREAD_ENV
    assert not any(entry.startswith("HOME=") for entry in SUPERVISOR.THREAD_ENV)


def test_case_arguments_enable_encoding_only_when_requested() -> None:
    ordinary = SUPERVISOR.case_arguments("public-test")
    assert "--encode-objects" not in ordinary
    assert "--encoding-run" not in ordinary

    encoded = SUPERVISOR.case_arguments("public-test", encode_objects=True)
    assert encoded[-3:] == ["--encode-objects", "--encoding-run", "/out/encoding"]
    with pytest.raises(TypeError, match="encode_objects_must_be_bool"):
        SUPERVISOR.case_arguments("public-test", encode_objects=1)


def pinned_inputs() -> tuple[dict, dict, dict]:
    manifest = {
        "source_revision": "revision-a",
        "source_tree_sha256": "tree-a",
    }
    build = {
        "base_image": "python:3.14-slim@sha256:base-a",
        "source_revision": "revision-a",
        "source_tree_sha256": "tree-a",
    }
    image = {
        "image_id": "sha256:image-a",
        "os": "linux",
        "architecture": "amd64",
        "labels": {
            "org.opencontainers.image.revision": "revision-a",
            "org.rsna-knee.source-tree-sha256": "tree-a",
        },
    }
    return manifest, build, image


def test_validate_pins_accepts_matching_source_image_and_base() -> None:
    manifest, build, image = pinned_inputs()
    assert (
        SUPERVISOR.validate_pins(manifest, build, image, "sha256:image-a") == "base-a"
    )


def test_validate_pins_rejects_image_id_mismatch() -> None:
    manifest, build, image = pinned_inputs()
    with pytest.raises(RuntimeError, match="image id mismatch"):
        SUPERVISOR.validate_pins(manifest, build, image, "sha256:image-other")


def test_validate_pins_rejects_source_tree_and_revision_mismatch() -> None:
    manifest, build, image = pinned_inputs()
    image["labels"]["org.rsna-knee.source-tree-sha256"] = "tree-other"
    with pytest.raises(RuntimeError, match="tree hash mismatch"):
        SUPERVISOR.validate_pins(manifest, build, image, "sha256:image-a")

    manifest, build, image = pinned_inputs()
    image["labels"]["org.opencontainers.image.revision"] = "revision-other"
    with pytest.raises(RuntimeError, match="revision mismatch"):
        SUPERVISOR.validate_pins(manifest, build, image, "sha256:image-a")

    manifest, build, image = pinned_inputs()
    build["source_tree_sha256"] = "tree-other"
    with pytest.raises(RuntimeError, match="build metadata/source manifest tree"):
        SUPERVISOR.validate_pins(manifest, build, image, "sha256:image-a")


def test_run_case_refuses_existing_root_before_image_inspection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_root = tmp_path / "data"
    data_root.mkdir()
    output_root = tmp_path / "output"
    output_root.mkdir()

    def unexpected_image_inspection(_image_ref: str) -> dict:
        pytest.fail("existing output must be refused before Docker inspection")

    monkeypatch.setattr(SUPERVISOR, "inspect_image", unexpected_image_inspection)
    with pytest.raises(RuntimeError, match="refusing non-fresh roots"):
        SUPERVISOR.run_case(
            "public-test",
            data_root=data_root,
            output_root=output_root,
            scratch_root=tmp_path / "scratch",
            context=tmp_path / "context",
            build_metadata_path=tmp_path / "build.json",
            image_ref="candidate-image",
            expected_image_id="sha256:expected",
            workers=4,
            interval=1.0,
            timeout_seconds=30.0,
        )


def test_resource_limit_defaults_and_validation() -> None:
    assert SUPERVISOR.DEFAULT_MEMORY_BYTES == 24_000_000_000
    assert SUPERVISOR.DEFAULT_OUTPUT_BUDGET_BYTES == 20_000_000_000
    assert SUPERVISOR.positive_integer("24000000000") == 24_000_000_000
    assert SUPERVISOR.positive_integer("20000000000") == 20_000_000_000
    for value in ("0", "-1", "1.5", "nope"):
        with pytest.raises(argparse.ArgumentTypeError):
            SUPERVISOR.positive_integer(value)

    SUPERVISOR.validate_resource_limits(24_000_000_000, 20_000_000_000, 1.0, 30.0)
    for args in (
        (0, 20, 1.0, 30.0),
        (24, 0, 1.0, 30.0),
        (24, 20, 0.0, 30.0),
        (24, 20, float("nan"), 30.0),
        (24, 20, 1.0, float("inf")),
    ):
        with pytest.raises(ValueError):
            SUPERVISOR.validate_resource_limits(*args)


def test_output_budget_boundary_and_capacity_fact(tmp_path: Path) -> None:
    assert not SUPERVISOR.output_budget_exceeded(99, 100)
    assert not SUPERVISOR.output_budget_exceeded(100, 100)
    assert SUPERVISOR.output_budget_exceeded(101, 100)
    capacity = SUPERVISOR.filesystem_capacity(tmp_path)
    assert capacity["path"] == str(tmp_path)
    assert capacity["total_bytes"] >= capacity["available_bytes"] >= 0
    assert capacity["free_bytes"] >= capacity["available_bytes"]
    (tmp_path / "partial.npz.xz.part").write_bytes(b"partial")
    assert SUPERVISOR.folder_size(tmp_path) == (7, 1)


def test_run_case_stops_with_named_output_budget_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
    _manifest, _build, image = pinned_inputs()
    monkeypatch.setattr(SUPERVISOR, "inspect_image", lambda _ref: image)

    class Process:
        returncode: int | None = None

        def __init__(self, command, **_kwargs):
            self.command = command

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            if self.returncode is None:
                self.returncode = 137
            return self.returncode

    process_holder = {}

    def popen(command, **kwargs):
        process = Process(command, **kwargs)
        process_holder["process"] = process
        return process

    monkeypatch.setattr(SUPERVISOR.subprocess, "Popen", popen)
    calls = []

    def fake_run(command, *, timeout=15.0):
        calls.append(command)
        if command[:3] == ["docker", "info", "--format"]:
            if command[-1] == "{{.MemTotal}}":
                return SUPERVISOR.subprocess.CompletedProcess(
                    command, 0, "34359738368\n", ""
                )
            return SUPERVISOR.subprocess.CompletedProcess(
                command, 0, "linux/aarch64\n", ""
            )
        if command[:2] == ["docker", "stats"]:
            return SUPERVISOR.subprocess.CompletedProcess(
                command, 0, "0%|1MiB / 24GiB|2|0B / 0B\n", ""
            )
        if command[:3] == ["docker", "stop", "--time"]:
            process_holder["process"].returncode = 137
            return SUPERVISOR.subprocess.CompletedProcess(command, 0, "stopped", "")
        if command[:2] == ["docker", "inspect"]:
            return SUPERVISOR.subprocess.CompletedProcess(command, 1, "", "not found")
        if command[:2] == ["docker", "rm"]:
            return SUPERVISOR.subprocess.CompletedProcess(command, 0, "removed", "")
        return SUPERVISOR.subprocess.CompletedProcess(command, 1, "", "unexpected")

    monkeypatch.setattr(SUPERVISOR, "run", fake_run)
    monkeypatch.setattr(
        SUPERVISOR,
        "folder_size",
        lambda path: (101, 1) if path.name == "output" else (0, 0),
    )
    monkeypatch.setattr(SUPERVISOR.time, "sleep", lambda _seconds: None)
    result = SUPERVISOR.run_case(
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
        memory_bytes=24_000_000_000,
        output_budget_bytes=100,
        encode_objects=True,
    )

    assert result["status"] == "output_budget_exceeded"
    assert result["stop_reason"] == "output_budget_exceeded"
    assert result["output_budget_exceeded"] is True
    assert result["container_limits"]["memory_bytes"] == 24_000_000_000
    assert result["container_limits"]["memory_swap_bytes"] == 24_000_000_000
    assert result["object_encoding_enabled"] is True
    assert result["encoding_run_in_container"] == "/out/encoding"
    assert "--encode-objects" in result["argv_in_container"]
    assert (
        result["argv_in_container"][
            result["argv_in_container"].index("--encoding-run") + 1
        ]
        == "/out/encoding"
    )
    assert result["docker_vm_memory_total_bytes"] == 34_359_738_368
    assert "--memory" in result["docker_argv"]
    assert result["docker_argv"][result["docker_argv"].index("--memory") + 1] == str(
        24_000_000_000
    )
    assert result["filesystem_capacity_start"]["hard_quota"] == (
        "unknown_not_enforced_by_supervisor"
    )
    assert any(call[:3] == ["docker", "stop", "--time"] for call in calls)
