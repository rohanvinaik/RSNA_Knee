"""Version-pin behavior for the private production wrapper."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "kaggle" / "squint-production" / "run_squint.py"


def load_wrapper(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    spec = importlib.util.spec_from_file_location("runtime_pin_wrapper_test", WRAPPER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module


def manifest(
    directory: Path, memory_bytes: bytes, source_bytes: bytes
) -> tuple[Path, dict]:
    (directory / "memory").mkdir(parents=True)
    (directory / "source").mkdir()
    memory_path = directory / "memory" / "manifest.json"
    source_path = directory / "source" / "run.py"
    memory_path.write_bytes(memory_bytes)
    source_path.write_bytes(source_bytes)
    entries = [
        {
            "path": "memory/manifest.json",
            "sha256": hashlib.sha256(memory_bytes).hexdigest(),
            "bytes": len(memory_bytes),
        },
        {
            "path": "source/run.py",
            "sha256": hashlib.sha256(source_bytes).hexdigest(),
            "bytes": len(source_bytes),
        },
    ]
    document = {
        "schema": "knee.squint-runtime-manifest/v1",
        "bundle_id": hashlib.sha256(
            b"".join(
                entry["path"].encode() + b"\0" + entry["sha256"].encode() + b"\n"
                for entry in sorted(entries, key=lambda item: item["path"])
            )
        ).hexdigest(),
        "files": entries,
        "memory": {"schema": "knee.squint-memory/v1", "entry": "memory"},
        "source": {},
        "pythonpath": ["source"],
        "entrypoint": "source/run.py",
    }
    path = directory / "RUNTIME_MANIFEST.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path, document


def test_new_expected_runtime_wins_over_old_self_consistent_mount(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    wrapper = load_wrapper(monkeypatch)
    old_path, _old = manifest(tmp_path / "old", b"old-memory", b"old-runtime")
    new_path, new = manifest(tmp_path / "new", b"new-memory", b"new-runtime")
    expected_memory = hashlib.sha256(b"new-memory").hexdigest()

    result = wrapper.select_runtime_manifest(
        [old_path, new_path],
        hint="",
        expected_bundle_id=new["bundle_id"],
        expected_memory_manifest_sha256=expected_memory,
    )

    assert result["manifest_path"] == new_path
    assert result["manifest"]["bundle_id"] == new["bundle_id"]
    selection_pin = result["selection"]["source_pin"]
    assert selection_pin["expected_bundle_id"] == new["bundle_id"]
    assert selection_pin["expected_memory_manifest_sha256"] == expected_memory
    observed = {entry["path"]: entry for entry in selection_pin["observed_candidates"]}
    assert observed[str(old_path)] == {
        "path": str(old_path),
        "bundle_id": wrapper.load_candidate(old_path)["bundle_id"],
        "memory_manifest_sha256": hashlib.sha256(b"old-memory").hexdigest(),
        "tar_record": False,
    }
    assert observed[str(new_path)] == {
        "path": str(new_path),
        "bundle_id": new["bundle_id"],
        "memory_manifest_sha256": expected_memory,
        "tar_record": False,
    }
    assert [entry["path"] for entry in selection_pin["excluded_candidates"]] == [
        str(old_path)
    ]


@pytest.mark.parametrize(
    ("bundle_pin", "memory_pin", "expected_message"),
    [
        (None, "a" * 64, "runtime bundle pin is not configured"),
        ("a" * 64, None, "memory manifest pin is not configured"),
        ("0" * 64, "1" * 64, "runtime pin mismatch"),
    ],
)
def test_unset_or_wrong_pin_refuses_before_selection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    bundle_pin: str | None,
    memory_pin: str | None,
    expected_message: str,
) -> None:
    wrapper = load_wrapper(monkeypatch)
    path, _document = manifest(tmp_path / "candidate", b"actual-memory", b"runtime")
    if bundle_pin is None or memory_pin is None:
        monkeypatch.setattr(wrapper, "EXPECTED_RUNTIME_BUNDLE_ID", None)
        monkeypatch.setattr(wrapper, "EXPECTED_MEMORY_MANIFEST_SHA256", None)

    with pytest.raises(wrapper.SetupError, match=expected_message):
        wrapper.select_runtime_manifest(
            [path],
            hint="",
            expected_bundle_id=bundle_pin,
            expected_memory_manifest_sha256=memory_pin,
        )


def test_module_defaults_are_fail_closed_until_release_pins_are_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    wrapper = load_wrapper(monkeypatch)
    path, _document = manifest(tmp_path / "candidate", b"memory", b"runtime")
    monkeypatch.setattr(wrapper, "EXPECTED_RUNTIME_BUNDLE_ID", None)
    monkeypatch.setattr(wrapper, "EXPECTED_MEMORY_MANIFEST_SHA256", None)

    with pytest.raises(
        wrapper.SetupError, match="runtime bundle pin is not configured"
    ):
        wrapper.select_runtime_manifest([path], hint="")


def test_release_module_defaults_bind_to_matching_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    wrapper = load_wrapper(monkeypatch)
    path, document = manifest(tmp_path / "candidate", b"memory", b"runtime")
    monkeypatch.setattr(wrapper, "EXPECTED_RUNTIME_BUNDLE_ID", document["bundle_id"])
    monkeypatch.setattr(
        wrapper,
        "EXPECTED_MEMORY_MANIFEST_SHA256",
        wrapper.memory_manifest_sha256(document),
    )

    selected = wrapper.select_runtime_manifest([path], hint="")

    assert selected["manifest_path"] == path
    assert (
        selected["selection"]["source_pin"]["expected_bundle_id"]
        == document["bundle_id"]
    )


def test_wrong_memory_pin_refuses_even_when_bundle_id_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    wrapper = load_wrapper(monkeypatch)
    path, document = manifest(tmp_path / "candidate", b"memory", b"runtime")

    with pytest.raises(wrapper.SetupError, match="runtime pin mismatch"):
        wrapper.select_runtime_manifest(
            [path],
            hint="",
            expected_bundle_id=document["bundle_id"],
            expected_memory_manifest_sha256="0" * 64,
        )
    recorded = wrapper.REPORT["inputs"]["runtime_source_pin"]
    assert recorded["expected_bundle_id"] == document["bundle_id"]
    assert recorded["expected_memory_manifest_sha256"] == "0" * 64
    assert (
        recorded["observed_candidates"][0]["memory_manifest_sha256"]
        == hashlib.sha256(b"memory").hexdigest()
    )
