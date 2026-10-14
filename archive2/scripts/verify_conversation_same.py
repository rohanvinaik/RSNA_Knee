"""Verify saved B2 conversations against original B1 inputs and both backends."""

import argparse
import json
import platform
from hashlib import sha256
from pathlib import Path

import numpy as np
from verify_profiles_same import assert_same

from knee.collapse.physical import PlaneFrame
from knee.objects.analysis import SeriesMeasurement
from knee.objects.conversation import ConversationInput, converse
from knee.objects.interiors import InteriorReading
from knee.objects.profile_codes import profile_support_code
from knee.objects.profiles import ProfileReading
from workbench.measure.conversation_records import conversation_record
from workbench.measure.object_analysis import (
    array_digest,
    package_version,
    source_snapshot,
)


def environment_current(environment: dict) -> bool:
    values = {
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
    return all(environment.get(key) == value for key, value in values.items())


def _b1_profile(arrays: dict, record: dict) -> ProfileReading | None:
    if "b1_samples" not in arrays:
        return None
    return ProfileReading(
        arrays["b1_samples"],
        arrays["b1_valid"],
        arrays["b1_slopes"],
        arrays["b1_distances_mm"],
        profile_support_code(
            int(arrays["b1_valid"].size), int(arrays["b1_valid"].sum())
        ),
        tuple(
            profile_support_code(arrays["b1_valid"].shape[1], int(row.sum()))
            for row in arrays["b1_valid"]
        ),
        record["interiors"]["requested_backend"],
        record["interiors"]["effective_backend"],
    )


def _measurement(record: dict, arrays: dict) -> SeriesMeasurement:
    frame = None
    if "origin_lps" in arrays and "basis_lps" in arrays:
        frame = PlaneFrame(
            arrays["origin_lps"],
            arrays["basis_lps"],
            tuple(record["spacing_rc_mm"]),
        )
    interior = None
    if "interiors" in record:
        info = record["interiors"]
        profile = _b1_profile(arrays, record)
        interior = InteriorReading(
            info["code"],
            arrays["b1_dark"],
            arrays["b1_available"],
            arrays["b1_distance_mm"],
            arrays["b1_markers"],
            arrays["b1_labels"],
            arrays["b1_edge_points_rc"],
            arrays["b1_edge_normals_rc"],
            arrays["b1_edge_regions"],
            arrays["b1_edge_kinds"],
            profile,
            arrays["b1_band_low_mm"],
            arrays["b1_band_high_mm"],
            arrays["b1_trace_points_rc"],
            arrays["b1_trace_codes"],
            info["distance_error_bound_mm"],
            arrays["b1_distance_guard"],
        )
    return SeriesMeasurement(
        record["code"],
        frame=frame,
        acquired_plane=arrays.get("acquired_plane"),
        interiors=interior,
        slice_thickness_mm=record.get("slice_thickness_mm"),
    )


def _normalized(metadata: dict) -> dict:
    value = json.loads(json.dumps(metadata))
    value["requested_backend"] = "<backend>"
    value["effective_backends"] = ["<backend>"] if value["effective_backends"] else []
    for exchange in value["exchanges"]:
        if exchange["profile"] is not None:
            exchange["profile"]["requested_backend"] = "<backend>"
            exchange["profile"]["effective_backend"] = "<backend>"
    return value


def _check_metadata(actual: dict, expected: dict) -> None:
    if _normalized(actual) != _normalized(expected):
        raise AssertionError("same_conversation_metadata_mismatch")


def _check_saved_metadata(actual: dict, expected: dict) -> None:
    if actual != expected:
        raise AssertionError("same_saved_conversation_metadata_mismatch")


def _check_array_descriptors(arrays: dict, descriptors: dict) -> None:
    if set(arrays) != set(descriptors):
        raise ValueError("saved_array_key_set_mismatch")
    for name, descriptor in descriptors.items():
        array = arrays[name]
        if (
            list(array.shape) != descriptor["shape"]
            or array.dtype.str != descriptor["dtype"]
            or array.nbytes != descriptor["bytes"]
            or array_digest(array) != descriptor["digest"]
        ):
            raise ValueError("saved_array_descriptor_mismatch")


def _check_b2_array_sets(
    reference: dict, twin: dict, saved: dict, requested: dict
) -> None:
    expected = set(reference)
    if set(twin) != expected or set(saved) != expected or set(requested) != expected:
        raise AssertionError("same_b2_array_key_set_mismatch")
    for name in expected:
        assert_same(reference[name], twin[name])
        assert_same(reference[name], saved[name])
        assert_same(requested[name], saved[name])


def _require_current_sources(
    receipt: dict, writer_digest: str, serializer_digest: str
) -> None:
    if receipt.get("writer_sha256") != writer_digest:
        raise ValueError("writer_snapshot_mismatch")
    if receipt.get("conversation_serializer_sha256") != serializer_digest:
        raise ValueError("conversation_serializer_snapshot_mismatch")


def current_status(run: Path) -> dict:
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    proof_path = run / "same-proof-b2.json"
    proof = json.loads(proof_path.read_text()) if proof_path.exists() else {}
    writer = Path("workbench/measure/object_analysis.py")
    serializer = Path("workbench/measure/conversation_records.py")
    writer_digest = sha256(writer.read_bytes()).hexdigest()
    serializer_digest = sha256(serializer.read_bytes()).hexdigest()
    expected_exchanges = sum(
        len(record.get("conversation", {}).get("exchanges", []))
        for record in receipt.get("records", [])
    )
    checks = {
        "conversation_requested": receipt.get("request", {}).get("conversation")
        is True,
        "sources_current": receipt.get("kernel_sources") == source_snapshot(),
        "receipt_sources_unchanged": receipt.get("source_snapshot_code") == "unchanged",
        "writer_current": receipt.get("writer_sha256") == writer_digest
        and proof.get("writer_sha256") == writer_digest,
        "serializer_current": receipt.get("conversation_serializer_sha256")
        == serializer_digest
        and proof.get("serializer_sha256") == serializer_digest,
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
        "no_failed_studies": not receipt.get("failures")
        and all(study["code"] == "complete" for study in receipt["studies"]),
        "all_records_conversed": all(
            "conversation" in record for record in receipt["records"]
        ),
        "proof_passed": proof.get("code") == "same" and proof.get("series", 0) > 0,
        "proof_sources_current": proof.get("kernel_sources") == source_snapshot(),
        "proof_series_count_matches": proof.get("series")
        == receipt.get("series_count")
        == len(receipt.get("records", [])),
        "proof_exchange_count_matches": proof.get("exchanges") == expected_exchanges,
    }
    result = {
        "standing": "current" if all(checks.values()) else "unverified_or_stale",
        "checks": checks,
        "studies": receipt.get("study_count"),
        "series": receipt.get("series_count"),
        "conversations": proof.get("series"),
        "exchanges": proof.get("exchanges"),
        "sample_evaluations": proof.get("sample_evaluations"),
        "raster_visits": proof.get("raster_visits"),
    }
    (run / "same-status-b2.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
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
    if request.get("conversation") is not True:
        raise ValueError("conversation_not_requested")
    writer = Path("workbench/measure/object_analysis.py")
    serializer = Path("workbench/measure/conversation_records.py")
    writer_digest = sha256(writer.read_bytes()).hexdigest()
    serializer_digest = sha256(serializer.read_bytes()).hexdigest()
    _require_current_sources(receipt, writer_digest, serializer_digest)
    if not environment_current(receipt["environment"]):
        raise ValueError("same_environment_mismatch")
    if (
        receipt["kernel_sources"] != source_snapshot()
        or receipt["source_snapshot_code"] != "unchanged"
    ):
        raise ValueError("production_source_snapshot_not_current")

    grouped: dict[str, list[ConversationInput]] = {}
    saved: dict[str, dict[str, tuple[dict, dict]]] = {}
    artifacts: dict[str, str] = {}
    for record in receipt["records"]:
        artifact_name = record["artifact"]
        artifact = args.run / artifact_name
        with np.load(artifact, allow_pickle=False) as loaded:
            arrays = dict(loaded)
        _check_array_descriptors(arrays, record["arrays"])
        artifacts[artifact_name] = sha256(artifact.read_bytes()).hexdigest()
        if "conversation" not in record:
            raise ValueError("missing_saved_conversation")
        b2_arrays = {
            key: value for key, value in arrays.items() if key.startswith("b2_")
        }
        saved.setdefault(record["study_uid"], {})[record["series_uid"]] = (
            record["conversation"],
            b2_arrays,
        )
        if record.get("orientation") is not None:
            orientation = record["orientation"]
        else:
            orientation = record["view"][0]
        grouped.setdefault(record["study_uid"], []).append(
            ConversationInput(
                record["series_uid"],
                orientation,
                _measurement(record, arrays),
                float("nan")
                if record["background_split"] is None
                else record["background_split"],
            )
        )

    series_count = exchange_count = sample_evaluations = 0
    raster_visits = [0, 0]
    for study_uid, inputs in grouped.items():
        per_backend = {}
        for backend in ("reference", "jit"):
            readings = converse(
                tuple(inputs), np.asarray(request["offsets_mm"]), backend
            )
            per_backend[backend] = {
                reading.series_uid: conversation_record(reading, backend)
                for reading in readings
            }
        for input_item in inputs:
            uid = input_item.series_uid
            ref_meta, ref_arrays = per_backend["reference"][uid]
            jit_meta, jit_arrays = per_backend["jit"][uid]
            saved_metadata, saved_arrays = saved[study_uid][uid]
            requested_backend = request["backend"]
            if requested_backend not in per_backend:
                raise ValueError("invalid_requested_backend")
            _check_metadata(ref_meta, jit_meta)
            _check_saved_metadata(
                saved_metadata, per_backend[requested_backend][uid][0]
            )
            if saved_metadata["requested_backend"] != requested_backend:
                raise AssertionError("saved_requested_backend_mismatch")
            _check_b2_array_sets(
                ref_arrays,
                jit_arrays,
                saved_arrays,
                per_backend[requested_backend][uid][1],
            )
            series_count += 1
            exchange_count += len(ref_meta["exchanges"])
            sample_evaluations += ref_meta["sample_evaluations"]
            raster_visits = [
                a + b
                for a, b in zip(raster_visits, ref_meta["raster_visits"], strict=True)
            ]
            print(
                f"SAME B2 {series_count}: {study_uid} / {uid} / {len(ref_meta['exchanges'])} exchanges",
                flush=True,
            )
    if source_snapshot() != receipt["kernel_sources"]:
        raise ValueError("source_changed_during_same")
    if series_count == 0:
        raise ValueError("no_conversation_records")
    proof = {
        "code": "same",
        "scope": "all original-input B2 arrays and metadata; reference/JIT/saved within the receipt environment",
        "series": series_count,
        "exchanges": exchange_count,
        "sample_evaluations": sample_evaluations,
        "raster_visits": raster_visits,
        "artifacts": artifacts,
        "receipt_sha256": sha256(receipt_path.read_bytes()).hexdigest(),
        "writer_sha256": writer_digest,
        "serializer_sha256": serializer_digest,
        "verifier_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "same_array_checker_sha256": sha256(
            Path(__file__).with_name("verify_profiles_same.py").read_bytes()
        ).hexdigest(),
        "kernel_sources": receipt["kernel_sources"],
        "environment": receipt["environment"],
    }
    (args.run / "same-proof-b2.json").write_text(json.dumps(proof, indent=2) + "\n")
    status = current_status(args.run)
    print(json.dumps(status, indent=2))
    if status["standing"] != "current":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
