"""Resume integrity is checked through its real command after proof inputs change."""

import json
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

import pytest

from knee import collapse


@pytest.mark.parametrize("changed", ["artifact", "receipt", "verifier", "source"])
def test_resume_status_refuses_changed_proof_links(
    tmp_path: Path, changed: str
) -> None:
    assert collapse.__file__ is not None
    package = Path(collapse.__file__).resolve().parent.parent
    project = Path(__file__).resolve().parents[2]
    artifact = tmp_path / "series.npz"
    # Opaque bytes suffice here: this command checks proof identity, not the SAME arithmetic.
    artifact.write_bytes(b"synthetic saved artifact")
    receipt = {
        "schema": "physical-measurements-v2",
        "scope": "synthetic proof-link fixture",
        "kernel_sources": {
            str(p.relative_to(package.parent)): sha256(p.read_bytes()).hexdigest()
            for p in sorted(package.rglob("*.py"))
        },
        "study_count": 1,
        "series_count": 1,
        "codes": {"measured": 1},
        "failures": [],
        "records": [{"series_uid": "series", "code": "measured"}],
    }
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(receipt))
    proof = {
        "code": "same",
        "receipt_sha256": sha256(receipt_path.read_bytes()).hexdigest(),
        "verifier_sha256": sha256(
            (project / "scripts/verify_profiles_same.py").read_bytes()
        ).hexdigest(),
        "artifacts": {"series.npz": sha256(artifact.read_bytes()).hexdigest()},
        "series_checked": 1,
        "samples_checked": 1,
    }
    proof_path = tmp_path / "same.json"
    proof_path.write_text(json.dumps(proof))

    def run_status() -> dict:
        subprocess.run(
            [sys.executable, str(project / "scripts/object_status.py"), str(tmp_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads((tmp_path / "status.json").read_text())

    assert run_status()["resume_status"] == "ready_for_next_packet"
    if changed == "artifact":
        artifact.write_bytes(b"changed saved artifact")
    elif changed == "receipt":
        receipt["scope"] = "changed scope"
        receipt_path.write_text(json.dumps(receipt))
    elif changed == "verifier":
        proof["verifier_sha256"] = "different verifier"
        proof_path.write_text(json.dumps(proof))
    else:
        receipt["kernel_sources"]["knee/pipeline.py"] = "different source"
        receipt_path.write_text(json.dumps(receipt))
        proof["receipt_sha256"] = sha256(receipt_path.read_bytes()).hexdigest()
        proof_path.write_text(json.dumps(proof))
    status = run_status()
    assert status["resume_status"] == "reverify_required"
    if changed == "source":
        assert status["code"] == "stale_sources"
    else:
        assert status["same_proof_current"] is False
