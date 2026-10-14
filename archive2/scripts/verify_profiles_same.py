"""SAME on the exact acquired planes and probes saved by the production run."""

import argparse
import json
from hashlib import sha256
from pathlib import Path

import numpy as np

from knee.objects.profiles import sample_profiles


def assert_same(left: np.ndarray, right: np.ndarray) -> None:
    if left.shape != right.shape or left.dtype != right.dtype:
        raise AssertionError("same_shape_or_dtype_mismatch")
    if left.dtype.kind == "f":
        missing = np.isnan(left)
        np.testing.assert_array_equal(missing, np.isnan(right))
        np.testing.assert_array_equal(left[~missing], right[~missing])
        np.testing.assert_array_equal(
            np.signbit(left[~missing]), np.signbit(right[~missing])
        )
    else:
        np.testing.assert_array_equal(left, right)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    receipt = json.loads((args.run / "receipt.json").read_text())
    checked, samples = 0, 0
    artifacts = {}
    for record in receipt["records"]:
        if record["code"] != "measured":
            continue
        artifact = args.run / record.get("artifact", f"{record['series_uid']}.npz")
        artifacts[str(artifact.relative_to(args.run))] = sha256(
            artifact.read_bytes()
        ).hexdigest()
        with np.load(artifact, allow_pickle=False) as arrays:
            for name, descriptor in record["arrays"].items():
                array = arrays[name]
                digest = sha256(
                    array.dtype.str.encode()
                    + str(array.shape).encode()
                    + array.tobytes()
                ).hexdigest()
                if digest != descriptor["digest"]:
                    raise AssertionError("saved_array_digest_mismatch")
            axes = arrays["basis_lps"] / tuple(record["spacing_rc_mm"])
            metric = (
                axes.T @ axes
                if receipt["schema"] == "physical-measurements-v2"
                else None
            )
            readings = [
                sample_profiles(
                    arrays["acquired_plane"],
                    arrays["points_rc"],
                    arrays["normals_rc"],
                    arrays["distances_mm"],
                    tuple(record["spacing_rc_mm"]),
                    backend,
                    metric_rc=metric,
                )
                for backend in ("reference", "jit")
            ]
            for name in ("samples", "valid", "slopes", "distances_mm"):
                assert_same(getattr(readings[0], name), getattr(readings[1], name))
                assert_same(arrays[name], getattr(readings[1], name))
            if not (
                readings[0].support_code
                == readings[1].support_code
                == record["support_code"]
            ):
                raise AssertionError("same_support_code_mismatch")
            if not (
                readings[0].support_codes
                == readings[1].support_codes
                == tuple(record["support_codes"])
            ):
                raise AssertionError("same_per_profile_code_mismatch")
            checked += 1
            samples += readings[0].samples.size
    standing = {
        "code": "same",
        "receipt_sha256": sha256((args.run / "receipt.json").read_bytes()).hexdigest(),
        "artifacts": artifacts,
        "verifier_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "series_checked": checked,
        "samples_checked": samples,
        "scope": "saved acquired planes/probes; exact within this environment; missing-axis records not sampled",
    }
    (args.run / "same.json").write_text(json.dumps(standing, indent=2) + "\n")
    print(json.dumps({k: v for k, v in standing.items() if k != "artifacts"}, indent=2))


if __name__ == "__main__":
    main()
