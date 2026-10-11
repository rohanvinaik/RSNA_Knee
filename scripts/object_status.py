"""Compute saved Packet A standing from receipts and current source, never a prose checkpoint."""

import argparse
import json
from hashlib import sha256
from pathlib import Path

import knee
from knee import objects


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    receipt_path = args.run / "receipt.json"
    if not receipt_path.exists():
        print(json.dumps({"code": "receipt_not_written", "run": str(args.run)}))
        return
    receipt = json.loads(receipt_path.read_text())
    if knee.__file__ is None or objects.__file__ is None:
        raise RuntimeError("package_source_unavailable")
    # The package root, named directly rather than reached through one stage's location, so moving
    # a module between stages cannot silently change what this status covers (2026-10-11).
    package = Path(knee.__file__).resolve().parent
    actual = {
        str(p.relative_to(package.parent)): sha256(p.read_bytes()).hexdigest()
        for p in sorted(package.rglob("*.py"))
    }
    current = actual == receipt["kernel_sources"]
    same_path = args.run / "same.json"
    same = json.loads(same_path.read_text()) if same_path.exists() else None
    same_matches = (
        same is not None
        and same.get("receipt_sha256") == sha256(receipt_path.read_bytes()).hexdigest()
    )
    artifact_changes = []
    expected_artifacts = {
        record.get("artifact", f"{record['series_uid']}.npz")
        for record in receipt["records"]
        if record["code"] == "measured"
    }
    proven_artifacts = same.get("artifacts", {}) if same else {}
    for name in sorted(expected_artifacts):
        path = args.run / name
        if (
            name not in proven_artifacts
            or not path.is_file()
            or sha256(path.read_bytes()).hexdigest() != proven_artifacts[name]
        ):
            artifact_changes.append(name)
    verifier = Path(__file__).with_name("verify_profiles_same.py")
    verifier_current = (
        same is not None
        and same.get("verifier_sha256") == sha256(verifier.read_bytes()).hexdigest()
    )
    proof_current = (
        same_matches
        and verifier_current
        and not artifact_changes
        and same is not None
        and same.get("code") == "same"
        and same.get("series_checked") == len(expected_artifacts)
    )
    status = {
        "code": "current_sources" if current else "stale_sources",
        "resume_status": (
            "ready_for_next_packet"
            if current and proof_current and not receipt["failures"]
            else "reverify_required"
        ),
        "run": str(args.run),
        "schema": receipt["schema"],
        "scope": receipt["scope"],
        "study_count": receipt["study_count"],
        "series_count": receipt["series_count"],
        "codes": receipt["codes"],
        "failures": receipt["failures"],
        "same_receipt_matches": same_matches,
        "same_verifier_current": verifier_current,
        "same_artifacts_changed": artifact_changes,
        "same_proof_current": proof_current,
        "same_series_checked": same.get("series_checked") if same else None,
        "same_samples_checked": same.get("samples_checked") if same else None,
        "detective": {
            "target": receipt.get("detective", {}).get("snapshot", {}).get("function"),
            "specification": receipt.get("detective", {})
            .get("snapshot", {})
            .get("specification"),
            "profile_source_current": receipt.get("detective", {}).get(
                "profile_codes_source_sha256"
            )
            == sha256(
                Path(objects.__file__).parent.joinpath("profile_codes.py").read_bytes()
            ).hexdigest(),
        },
    }
    (args.run / "status.json").write_text(json.dumps(status, indent=2) + "\n")
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
