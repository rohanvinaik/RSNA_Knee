#!/usr/bin/env python3
"""Stage a minimal, hash-pinned Linux runtime context from a source checkout."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

METADATA_PATHS = ("pyproject.toml", "uv.lock", ".python-version")
SOURCE_PATHS = ("scripts/run_interiors.py",)


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def shipped_paths(root: Path) -> tuple[str, ...]:
    paths = list(SOURCE_PATHS)
    package = root / "src/knee"
    paths.extend(
        path.relative_to(root).as_posix()
        for path in package.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )
    return tuple(sorted(paths))


@dataclass(frozen=True)
class InputSnapshot:
    source_root: Path
    source_bytes: dict[str, bytes]
    metadata_bytes: dict[str, bytes]
    dockerfile_bytes: bytes
    revision: str


def _revision(root: Path) -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def snapshot_inputs(root: Path, candidate: Path) -> InputSnapshot:
    """Read every shipped/config input before export or staging begins."""
    paths = shipped_paths(root)
    source_bytes = {relative: (root / relative).read_bytes() for relative in paths}
    metadata_bytes = {
        relative: (root / relative).read_bytes() for relative in METADATA_PATHS
    }
    dockerfile = (candidate / "Dockerfile").read_bytes()
    snapshot = InputSnapshot(
        root,
        source_bytes,
        metadata_bytes,
        dockerfile,
        _revision(root),
    )
    verify_source_unchanged(snapshot)
    return snapshot


def verify_source_unchanged(snapshot: InputSnapshot) -> None:
    """Reject changed, added, or removed inputs relative to the initial snapshot."""
    root = snapshot.source_root
    if shipped_paths(root) != tuple(snapshot.source_bytes):
        raise RuntimeError("stale_source_input: shipped source file set changed")
    for relative, expected in snapshot.source_bytes.items():
        try:
            actual = (root / relative).read_bytes()
        except OSError as exc:
            raise RuntimeError(f"stale_source_input: cannot reread {relative}") from exc
        if actual != expected:
            raise RuntimeError(
                f"stale_source_input: shipped source changed: {relative}"
            )
    for relative, expected in snapshot.metadata_bytes.items():
        try:
            actual = (root / relative).read_bytes()
        except OSError as exc:
            raise RuntimeError(f"stale_source_input: cannot reread {relative}") from exc
        if actual != expected:
            raise RuntimeError(
                f"stale_source_input: build metadata changed: {relative}"
            )


def _source_manifest(
    snapshot: InputSnapshot, requirement_bytes: bytes
) -> dict[str, object]:
    entries = []
    tree = hashlib.sha256()
    for relative, content in snapshot.source_bytes.items():
        file_hash = digest_bytes(content)
        entries.append({"path": relative, "sha256": file_hash, "bytes": len(content)})
        tree.update(relative.encode("utf-8"))
        tree.update(b"\0")
        tree.update(file_hash.encode("ascii"))
        tree.update(b"\n")
    project = tomllib.loads(snapshot.metadata_bytes["pyproject.toml"].decode("utf-8"))
    return {
        "schema": "offline-runtime-source/v1",
        "source_revision": snapshot.revision,
        "source_tree_sha256": tree.hexdigest(),
        "python_version_file": snapshot.metadata_bytes[".python-version"]
        .decode()
        .strip(),
        "requires_python": project["project"]["requires-python"],
        "project_metadata_sha256": digest_bytes(
            snapshot.metadata_bytes["pyproject.toml"]
        ),
        "runtime_dependency_lock_sha256": digest_bytes(
            snapshot.metadata_bytes["uv.lock"]
        ),
        "runtime_dependency_export_sha256": digest_bytes(requirement_bytes),
        "files": entries,
    }


def _export_requirements(root: Path, uv: str) -> bytes:
    with tempfile.TemporaryDirectory(prefix="rsna-runtime-uv-") as cache:
        env = os.environ.copy()
        env["UV_CACHE_DIR"] = cache
        exported = subprocess.run(
            [
                uv,
                "export",
                "--frozen",
                "--no-dev",
                "--no-default-groups",
                "--extra",
                "jit",
                "--extra",
                "hdc",
                "--no-emit-project",
                "--no-header",
                "--no-annotate",
                "--format",
                "requirements-txt",
            ],
            cwd=root,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
    return exported.stdout.encode("utf-8")


def stage_context(
    root: Path,
    candidate: Path,
    destination: Path,
    uv: str = "uv",
    exporter: Callable[[Path, str], bytes] = _export_requirements,
) -> dict[str, object]:
    """Stage exact snapshot bytes, export locked requirements, then validate source stability."""
    snapshot = snapshot_inputs(root, candidate)
    if destination.is_relative_to(root):
        raise RuntimeError("destination must be outside the source checkout")
    destination.mkdir(parents=True, exist_ok=False)
    try:
        for relative, content in snapshot.source_bytes.items():
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        (destination / "Dockerfile").write_bytes(snapshot.dockerfile_bytes)

        requirement_bytes = exporter(root, uv)
        (destination / "requirements-runtime.txt").write_bytes(requirement_bytes)
        verify_source_unchanged(snapshot)

        # Check the staged payload against the pre-export snapshot, not the live checkout.
        for relative, expected in snapshot.source_bytes.items():
            if (destination / relative).read_bytes() != expected:
                raise RuntimeError(f"staged_source_mismatch: {relative}")
        if (destination / "Dockerfile").read_bytes() != snapshot.dockerfile_bytes:
            raise RuntimeError("staged_source_mismatch: Dockerfile")
        verify_source_unchanged(snapshot)

        manifest = _source_manifest(snapshot, requirement_bytes)
        (destination / "source-manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )
        return manifest
    except Exception:
        shutil.rmtree(destination)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--uv", default="uv")
    args = parser.parse_args()
    root = args.source_root.resolve(strict=True)
    candidate = args.candidate_root.resolve(strict=True)
    destination = args.destination.resolve()
    required = (
        root / "pyproject.toml",
        root / "uv.lock",
        root / ".python-version",
        root / "scripts/run_interiors.py",
        root / "src/knee",
        candidate / "Dockerfile",
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        parser.error("source or candidate is incomplete: " + ", ".join(missing))
    if destination.exists():
        parser.error(f"destination already exists: {destination}")
    manifest = stage_context(root, candidate, destination, args.uv)
    print(
        json.dumps(
            {
                "context": str(destination),
                "source_revision": manifest["source_revision"],
                "source_tree_sha256": manifest["source_tree_sha256"],
                "runtime_export_sha256": manifest["runtime_dependency_export_sha256"],
                "context_file_count": len(manifest["files"]) + 3,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
