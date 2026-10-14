"""Saved representation is verified, never silently repaired by drawing."""

from hashlib import sha256

import numpy as np
import pytest

from workbench.render.pair_frames import saved_array


def descriptor(array):
    return {
        "shape": array.shape,
        "dtype": array.dtype.str,
        "digest": sha256(
            array.dtype.str.encode() + str(array.shape).encode() + array.tobytes()
        ).hexdigest(),
    }


def test_saved_array_uses_the_production_digest_key_and_returns_exact_array():
    array = np.array([1, 3], dtype=np.int32)
    assert (
        saved_array({"a": array}, {"a": descriptor(array)}, "a", np.int32, 1) is array
    )


@pytest.mark.parametrize(
    "cause", ["missing_array", "missing_descriptor", "dtype", "shape", "digest", "rank"]
)
def test_corrupt_saved_representation_is_refused(cause):
    array = np.array([1, 3], dtype=np.int32)
    arrays, descriptors = {"a": array}, {"a": descriptor(array)}
    rank = 1
    if cause == "missing_array":
        arrays = {}
    elif cause == "missing_descriptor":
        descriptors = {}
    elif cause == "dtype":
        descriptors["a"]["dtype"] = "<i8"
    elif cause == "shape":
        descriptors["a"]["shape"] = [1]
    elif cause == "digest":
        descriptors["a"]["digest"] = "changed"
    else:
        rank = 2
    with pytest.raises(ValueError):
        saved_array(arrays, descriptors, "a", np.int32, rank)
