"""Synthetic checks for B2 SAME proof structure and source standing."""

import importlib.util
import json
import sys
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS))
_SPEC = importlib.util.spec_from_file_location(
    "verify_conversation_same", SCRIPTS / "verify_conversation_same.py"
)
assert _SPEC is not None and _SPEC.loader is not None
verifier = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(verifier)


def _descriptor(array: np.ndarray) -> dict:
    return {
        "shape": list(array.shape),
        "dtype": array.dtype.str,
        "bytes": array.nbytes,
        "digest": sha256(
            array.dtype.str.encode() + str(array.shape).encode() + array.tobytes()
        ).hexdigest(),
    }


def test_array_descriptors_pin_shape_dtype_bytes_digest_and_exact_keys() -> None:
    array = np.arange(4, dtype=np.int16)
    verifier._check_array_descriptors({"b2_x": array}, {"b2_x": _descriptor(array)})
    with pytest.raises(ValueError, match="saved_array_key_set_mismatch"):
        verifier._check_array_descriptors(
            {"b2_x": array, "extra": array}, {"b2_x": _descriptor(array)}
        )
    descriptor = _descriptor(array)
    descriptor["bytes"] += 1
    with pytest.raises(ValueError, match="saved_array_descriptor_mismatch"):
        verifier._check_array_descriptors({"b2_x": array}, {"b2_x": descriptor})


def test_b2_array_set_and_saved_metadata_checks_reject_unrecorded_fields() -> None:
    array = np.array([1], dtype=np.uint8)
    with pytest.raises(AssertionError, match="same_b2_array_key_set_mismatch"):
        verifier._check_b2_array_sets(
            {"b2_x": array},
            {"b2_x": array},
            {"b2_x": array, "b2_extra": array},
            {"b2_x": array},
        )
    with pytest.raises(
        AssertionError, match="same_saved_conversation_metadata_mismatch"
    ):
        verifier._check_saved_metadata(
            {"requested_backend": "reference"}, {"requested_backend": "jit"}
        )


def test_current_status_requires_receipt_and_proof_source_digests(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(ROOT)
    writer_digest = sha256(
        (ROOT / "workbench/measure/object_analysis.py").read_bytes()
    ).hexdigest()
    serializer_digest = sha256(
        (ROOT / "workbench/measure/conversation_records.py").read_bytes()
    ).hexdigest()
    receipt = {
        "request": {"conversation": True},
        "kernel_sources": verifier.source_snapshot(),
        "source_snapshot_code": "unchanged",
        "environment": {},
        "writer_sha256": writer_digest,
        "conversation_serializer_sha256": serializer_digest,
        "failures": [],
        "studies": [{"code": "complete"}],
        "records": [{"conversation": {"exchanges": []}}],
        "series_count": 1,
        "study_count": 1,
    }
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(receipt))
    proof = {
        "code": "same",
        "series": 1,
        "exchanges": 0,
        "writer_sha256": "stale-proof-writer",
        "serializer_sha256": "stale-proof-serializer",
        "artifacts": {"saved.npz": "unused"},
        "kernel_sources": receipt["kernel_sources"],
    }
    (tmp_path / "same-proof-b2.json").write_text(json.dumps(proof))

    status = verifier.current_status(tmp_path)

    assert status["standing"] == "unverified_or_stale"
    assert status["checks"]["writer_current"] is False
    assert status["checks"]["serializer_current"] is False
    assert status["checks"]["proof_exchange_count_matches"] is True


def test_replay_refuses_stale_receipt_sources() -> None:
    with pytest.raises(ValueError, match="writer_snapshot_mismatch"):
        verifier._require_current_sources(
            {"writer_sha256": "stale", "conversation_serializer_sha256": "current"},
            "current",
            "current",
        )
