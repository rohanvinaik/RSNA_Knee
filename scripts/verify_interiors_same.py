"""Compare saved production B1 arrays to reference/JIT and compute resume standing."""

import argparse
import json
import platform
from hashlib import sha256
from pathlib import Path

import numpy as np
from verify_profiles_same import assert_same

from knee.collapse.interiors import read_interiors
from workbench.measure.interior_records import interior_record
from workbench.measure.object_analysis import (
    array_digest,
    package_version,
    source_snapshot,
)


def environment_current(environment: dict) -> bool:
    current = {
        "python": platform.python_version(),
        "machine": platform.machine(),
        "platform": platform.platform(),
        **{
            name: package_version(package)
            for name, package in (
                ("numpy", "numpy"),
                ("numba", "numba"),
                ("llvmlite", "llvmlite"),
                ("scipy", "scipy"),
                ("scikit_image", "scikit-image"),
            )
        },
    }
    return all(environment.get(key) == value for key, value in current.items())


def current_status(run: Path) -> dict:
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    proof_path = run / "interiors-same.json"
    proof = json.loads(proof_path.read_text()) if proof_path.exists() else {}
    writer = Path("workbench/measure/object_analysis.py")
    serializer = writer.with_name("interior_records.py")
    checks = {
        "sources_current": receipt["kernel_sources"] == source_snapshot(),
        "receipt_sources_unchanged": receipt["source_snapshot_code"] == "unchanged",
        "writer_current": receipt["writer_sha256"]
        == sha256(writer.read_bytes()).hexdigest(),
        "serializer_current": receipt.get("interior_serializer_sha256")
        == sha256(serializer.read_bytes()).hexdigest(),
        "proof_passed": proof.get("code") == "same" and proof.get("readings", 0) > 0,
        "environment_current": environment_current(receipt["environment"]),
        "array_checker_current": proof.get("same_array_checker_sha256")
        == sha256(
            Path(__file__).with_name("verify_profiles_same.py").read_bytes()
        ).hexdigest(),
        "proof_receipt_current": proof.get("receipt_sha256")
        == sha256(receipt_path.read_bytes()).hexdigest(),
        "verifier_current": proof.get("verifier_sha256")
        == sha256(Path(__file__).read_bytes()).hexdigest(),
        "artifacts_current": bool(proof.get("artifacts"))
        and all(
            (run / name).exists()
            and sha256((run / name).read_bytes()).hexdigest() == digest
            for name, digest in proof.get("artifacts", {}).items()
        ),
        "no_failed_studies": not receipt["failures"]
        and all(s["code"] == "complete" for s in receipt["studies"]),
    }
    result = {
        "standing": "current" if all(checks.values()) else "unverified_or_stale",
        "checks": checks,
        "studies": receipt["study_count"],
        "series": receipt["series_count"],
        "geometric_readings": proof.get("readings"),
        "territories": sum(
            r.get("interiors", {}).get("territories", 0) for r in receipt["records"]
        ),
        "band_codes": {
            name: sum(
                r.get("interiors", {}).get("trace_counts", {}).get(name, 0)
                for r in receipt["records"]
            )
            for name in (
                "bracketed",
                "no_dark_bracket",
                "multiple_brackets",
                "missing_profile",
                "frame_clipped",
            )
        },
    }
    (run / "interiors-status.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--status-only", action="store_true")
    args = parser.parse_args()
    if args.status_only:
        status = current_status(args.run)
        print(json.dumps(status, indent=2))
        if status["standing"] != "current":
            raise SystemExit(1)
        return
    receipt_path = args.run / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    request = receipt["request"]
    if not environment_current(receipt["environment"]):
        raise ValueError("same_environment_mismatch")
    if (
        receipt["kernel_sources"] != source_snapshot()
        or receipt["source_snapshot_code"] != "unchanged"
    ):
        raise ValueError("production_source_snapshot_not_current")
    readings, samples = 0, 0
    artifacts = {}
    for metadata in receipt["records"]:
        artifact = args.run / metadata["artifact"]
        with np.load(artifact, allow_pickle=False) as loaded:
            arrays = dict(loaded)
        for name, descriptor in metadata["arrays"].items():
            if array_digest(arrays[name]) != descriptor["digest"]:
                raise ValueError("saved_array_digest_mismatch")
        artifacts[metadata["artifact"]] = sha256(artifact.read_bytes()).hexdigest()
        if "interiors" not in metadata:
            continue
        basis = arrays["basis_lps"] / metadata["spacing_rc_mm"]
        arguments = (
            arrays["acquired_plane"],
            tuple(metadata["spacing_rc_mm"]),
            metadata["background_split"]
            if metadata["background_split"] is not None
            else np.nan,
            request["prominence_mm"],
            np.asarray(request["offsets_mm"]),
        )
        reference = read_interiors(*arguments, "reference", metric_rc=basis.T @ basis)
        twin = read_interiors(*arguments, "jit", metric_rc=basis.T @ basis)
        ref_meta, ref_arrays = interior_record(reference)
        jit_meta, jit_arrays = interior_record(twin)
        for name in ref_arrays:
            assert_same(ref_arrays[name], jit_arrays[name])
            assert_same(ref_arrays[name], arrays[name])
        for key in (
            "code",
            "territories",
            "territory_pixels",
            "edge_counts",
            "trace_counts",
            "distance_error_bound_mm",
        ):
            if not (ref_meta[key] == jit_meta[key] == metadata["interiors"][key]):
                raise AssertionError("same_scalar_or_decision_mismatch")
        samples += ref_meta["coordinate_evaluations"]
        readings += 1
        print(
            f"SAME {readings}: {metadata['view'][0]} / {ref_meta['territories']} territories",
            flush=True,
        )
    if receipt["kernel_sources"] != source_snapshot():
        raise ValueError("source_changed_during_same")
    if readings == 0:
        raise ValueError("no_geometric_readings")
    proof = {
        "code": "same",
        "scope": "all B1 arrays, scalar quantities and named decisions; saved/reference/JIT within receipt environment",
        "readings": readings,
        "samples": samples,
        "artifacts": artifacts,
        "receipt_sha256": sha256(receipt_path.read_bytes()).hexdigest(),
        "verifier_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "same_array_checker_sha256": sha256(
            Path(__file__).with_name("verify_profiles_same.py").read_bytes()
        ).hexdigest(),
        "environment": receipt["environment"],
    }
    (args.run / "interiors-same.json").write_text(json.dumps(proof, indent=2) + "\n")
    status = current_status(args.run)
    print(json.dumps(status, indent=2))
    if status["standing"] != "current":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
