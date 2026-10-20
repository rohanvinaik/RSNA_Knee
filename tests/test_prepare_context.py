from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[1] / "scripts/offline_runtime/prepare_context.py"
SPEC = importlib.util.spec_from_file_location("prepare_context", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
PREPARE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PREPARE
SPEC.loader.exec_module(PREPARE)


def make_inputs(root: Path, candidate: Path) -> None:
    (root / "scripts").mkdir(parents=True)
    (root / "src/knee").mkdir(parents=True)
    (candidate).mkdir(parents=True)
    (root / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.11"\n')
    (root / "uv.lock").write_text("version = 1\n")
    (root / ".python-version").write_text("3.14\n")
    (root / "scripts/run_interiors.py").write_text("print('production')\n")
    (root / "src/knee/__init__.py").write_text("VALUE = 1\n")
    (candidate / "Dockerfile").write_text("FROM python:3.14-slim\n")


def exporter(_root: Path, _uv: str) -> bytes:
    return b"locked-dependency==1.0 --hash=sha256:abc\n"


def test_locked_runtime_export_selects_jit_and_hdc_extras(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        return PREPARE.subprocess.CompletedProcess(argv, 0, "locked\n", "")

    monkeypatch.setattr(PREPARE.subprocess, "run", fake_run)
    assert PREPARE._export_requirements(tmp_path, "uv") == b"locked\n"
    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv[:2] == ["uv", "export"]
    assert "--frozen" in argv
    extras = [
        argv[index + 1] for index, value in enumerate(argv[:-1]) if value == "--extra"
    ]
    assert extras == ["jit", "hdc"]
    assert "--no-dev" in argv and "--no-default-groups" in argv
    assert kwargs["check"] is True


def test_stable_stage_manifest_hashes_exact_copied_bytes(tmp_path: Path) -> None:
    root, candidate, destination = (
        tmp_path / "source",
        tmp_path / "candidate",
        tmp_path / "context",
    )
    make_inputs(root, candidate)

    manifest = PREPARE.stage_context(root, candidate, destination, exporter=exporter)
    written = json.loads((destination / "source-manifest.json").read_text())

    assert written == manifest
    assert manifest["source_revision"] == "unavailable"
    assert (
        manifest["runtime_dependency_export_sha256"]
        == hashlib.sha256(exporter(root, "uv")).hexdigest()
    )
    for entry in manifest["files"]:
        copied = (destination / entry["path"]).read_bytes()
        assert len(copied) == entry["bytes"]
        assert hashlib.sha256(copied).hexdigest() == entry["sha256"]
    assert (destination / "Dockerfile").read_bytes() == (
        candidate / "Dockerfile"
    ).read_bytes()


@pytest.mark.parametrize("change", ["edit", "add", "remove", "metadata"])
def test_export_phase_source_change_refuses_and_removes_owned_context(
    tmp_path: Path, change: str
) -> None:
    root, candidate, destination = (
        tmp_path / "source",
        tmp_path / "candidate",
        tmp_path / "context",
    )
    make_inputs(root, candidate)

    def mutating_exporter(source_root: Path, _uv: str) -> bytes:
        if change == "edit":
            (source_root / "scripts/run_interiors.py").write_text("changed\n")
        elif change == "add":
            (source_root / "src/knee/added.py").write_text("ADDED = True\n")
        elif change == "remove":
            (source_root / "src/knee/__init__.py").unlink()
        else:
            (source_root / "uv.lock").write_text("version = 2\n")
        return exporter(source_root, "uv")

    with pytest.raises(RuntimeError, match="stale_source_input"):
        PREPARE.stage_context(root, candidate, destination, exporter=mutating_exporter)
    assert not destination.exists()
