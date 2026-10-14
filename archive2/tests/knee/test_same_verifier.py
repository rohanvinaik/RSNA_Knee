"""A false SAME claim must fail even when Python's ordinary asserts are disabled."""

import json
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

import numpy as np


def test_wrong_support_code_fails_the_real_verifier_under_optimization(
    tmp_path: Path,
) -> None:
    arrays = {
        "acquired_plane": np.zeros((2, 2)),
        "points_rc": np.array([[0.0, 0.0]]),
        "normals_rc": np.array([[1.0, 0.0]]),
        "distances_mm": np.array([0.0]),
        "basis_lps": np.array([[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]]),
        "samples": np.zeros((1, 1)),
        "valid": np.ones((1, 1), dtype=bool),
        "slopes": np.empty((1, 0)),
    }
    np.savez_compressed(tmp_path / "series.npz", allow_pickle=False, **arrays)
    descriptors = {
        name: {
            "digest": sha256(
                a.dtype.str.encode() + str(a.shape).encode() + a.tobytes()
            ).hexdigest()
        }
        for name, a in arrays.items()
    }
    receipt = {
        "schema": "physical-measurements-v1",
        "records": [
            {
                "series_uid": "series",
                "code": "measured",
                "spacing_rc_mm": [1.0, 1.0],
                "support_code": "partial_support",
                "support_codes": ["complete_support"],
                "arrays": descriptors,
            }
        ],
    }
    (tmp_path / "receipt.json").write_text(json.dumps(receipt))
    script = Path(__file__).resolve().parents[2] / "scripts/verify_profiles_same.py"
    result = subprocess.run(
        [sys.executable, "-O", str(script), str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "same_support_code_mismatch" in result.stderr
    assert not (tmp_path / "same.json").exists()
