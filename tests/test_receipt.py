"""Intent tests for the run's receipt: every study's records kept, one study's replaced at a time."""

from hashlib import sha256

import numpy as np
import pytest

import knee.receipt as receipt_module
from knee.receipt import digest, merged_receipt

REQUEST = {
    "prominence_mm": 3.0,
    "offsets_mm": [0.0],
    "slice_index": None,
    "backend": "reference",
}


def record(study: str, series: str) -> dict:
    return {"study_uid": study, "series_uid": series}


def test_a_first_study_starts_the_receipt():
    receipt = merged_receipt(
        None,
        REQUEST,
        "A",
        ["a1", "a2"],
        [record("A", "a1")],
        {"a2": "no_stacked_volume"},
        {"totals": {}},
    )
    assert receipt["records"] == [record("A", "a1")]
    assert receipt["unread"] == {"a2": "no_stacked_volume"}
    assert receipt["telemetry"] == {"A": {"totals": {}}}


def test_a_second_study_keeps_the_first():
    first = merged_receipt(
        None, REQUEST, "A", ["a1"], [record("A", "a1")], {}, {"totals": {"x": 1}}
    )
    both = merged_receipt(
        first,
        REQUEST,
        "B",
        ["b1", "b2"],
        [record("B", "b1")],
        {"b2": "slice_unavailable"},
        {"totals": {"x": 2}},
    )
    assert both["records"] == [record("A", "a1"), record("B", "b1")]
    assert both["unread"] == {"b2": "slice_unavailable"}
    assert set(both["telemetry"]) == {"A", "B"}


def test_a_study_run_again_replaces_only_its_own():
    first = merged_receipt(
        None,
        REQUEST,
        "A",
        ["a1", "a2"],
        [record("A", "a1")],
        {"a2": "no_stacked_volume"},
        {"run": 1},
    )
    both = merged_receipt(
        first, REQUEST, "B", ["b1"], [record("B", "b1")], {}, {"run": 1}
    )
    again = merged_receipt(
        both,
        REQUEST,
        "A",
        ["a1", "a2"],
        [record("A", "a1"), record("A", "a2")],
        {},
        {"run": 2},
    )
    assert again["records"] == [record("B", "b1"), record("A", "a1"), record("A", "a2")]
    # a2 was silent before and is read now: its old silence goes
    assert again["unread"] == {}
    assert again["telemetry"] == {"B": {"run": 1}, "A": {"run": 2}}


def test_a_receipt_that_does_not_carry_telemetry_holds_none_for_the_study():
    receipt = merged_receipt(None, REQUEST, "A", ["a1"], [record("A", "a1")], {}, None)
    assert receipt["telemetry"] == {}


def test_records_made_under_other_settings_are_never_mixed_in():
    first = merged_receipt(None, REQUEST, "A", ["a1"], [record("A", "a1")], {}, None)
    other = {**REQUEST, "prominence_mm": 2.0}
    with pytest.raises(ValueError, match="receipt_request_differs"):
        merged_receipt(first, other, "B", ["b1"], [record("B", "b1")], {}, None)


# --- digest: streaming must equal the old whole-bytes expression exactly ---


def reference_digest(array: np.ndarray) -> str:
    """The old expression, retained verbatim as the reference."""
    return sha256(
        array.dtype.str.encode() + str(array.shape).encode() + array.tobytes()
    ).hexdigest()


def nan_payloads() -> np.ndarray:
    bits = np.array(
        [0x7FC00000, 0x7FC00001, 0xFFC00000, 0x7F800001, 0x7FBFFFFF, 0x7FC12345],
        dtype=np.uint32,
    )
    return bits.view(np.float32)


def signed_zeros() -> np.ndarray:
    return np.array([0.0, -0.0, 0.0, -0.0], dtype=np.float64)


def cases() -> dict:
    base = np.arange(5 * 6 * 7, dtype=np.int32).reshape(5, 6, 7)
    wide = np.arange(40, dtype=np.float64).reshape(4, 10)
    return {
        "c_contiguous": base,
        "f_contiguous": np.asfortranarray(base),
        "step_slice": base[::2, 1::3, ::-2][:, :, ::1],
        "step_slice_2d": wide[::2, ::3],
        "negative_strides": base[::-1, ::-1, ::-1],
        "negative_1d": np.arange(50, dtype=np.int16)[::-1],
        "transposed": base.transpose(2, 0, 1),
        "scalar_array": np.array(3.5),
        "numpy_scalar": np.float32(2.0),
        "empty_1d": np.empty(0, dtype=np.float32),
        "empty_2d": np.empty((0, 4), dtype=np.uint8),
        "empty_inner": np.empty((3, 0, 2), dtype=np.int64),
        "big_endian": np.arange(30, dtype=">i4").reshape(5, 6),
        "little_endian": np.arange(30, dtype="<i4").reshape(5, 6),
        "big_endian_float": np.linspace(0, 1, 33).astype(">f8"),
        "signed_zero": signed_zeros(),
        "signed_zero_strided": np.tile(signed_zeros(), 6)[::3],
        "nan_payloads": nan_payloads(),
        "nan_payloads_reversed": nan_payloads()[::-1],
        "bool": np.array([[True, False], [False, True]]),
        "complex": (np.arange(12) * (1 + 2j)).reshape(3, 4),
        "datetime": np.arange(10).astype("datetime64[s]"),
        "structured": np.zeros(7, dtype=[("a", "<i2"), ("b", ">f4")]),
        "strings": np.array([["ab", "c"], ["def", ""]]),
        "object": np.array([1, "a", None, 2.5], dtype=object),
        "readonly": np.frombuffer(bytes(range(60)), dtype=np.uint8).reshape(6, 10),
    }


@pytest.mark.parametrize("name", list(cases()))
def test_digest_equals_the_old_expression(name):
    array = cases()[name]
    assert digest(array) == reference_digest(array)


@pytest.mark.parametrize("chunk", [1, 3, 7, 64, 1000])
@pytest.mark.parametrize("name", list(cases()))
def test_digest_equals_the_old_expression_across_many_chunks(name, chunk, monkeypatch):
    # tiny chunk bounds force every chunked path (including rows larger than a chunk)
    monkeypatch.setattr(receipt_module, "_CHUNK", chunk)
    array = cases()[name]
    assert digest(array) == reference_digest(array)


def test_digest_keeps_nan_payload_and_signed_zero_distinct():
    a, b = nan_payloads(), nan_payloads()[::-1].copy()[::-1]
    assert digest(a) == digest(b)
    quiet = np.array([0x7FC00000], dtype=np.uint32).view(np.float32)
    other = np.array([0x7FC00001], dtype=np.uint32).view(np.float32)
    assert digest(quiet) != digest(other)
    assert digest(np.array([0.0])) != digest(np.array([-0.0]))


def test_digest_changes_with_content_dtype_shape_and_byte_order(monkeypatch):
    monkeypatch.setattr(receipt_module, "_CHUNK", 5)
    a = np.arange(24, dtype=np.int32).reshape(4, 6)
    base = digest(a)
    changed = a.copy()
    changed[3, 5] += 1
    assert digest(changed) != base
    assert digest(a.reshape(6, 4)) != base
    assert digest(a.view(np.float32)) != base
    assert digest(a.astype(">i4")) != base
    # a view with the same values in another layout has the same digest
    assert digest(np.asfortranarray(a)) == base


class NoTobytesArray(np.ndarray):
    def tobytes(self, *args, **kwargs):
        raise AssertionError("contiguous digest materialized the full array")


def test_digest_contiguous_path_does_not_call_tobytes(monkeypatch):
    monkeypatch.setattr(receipt_module, "_CHUNK", 13)
    base = np.arange(33, dtype=np.uint8)
    array = base.view(NoTobytesArray)
    assert digest(array) == reference_digest(np.asarray(array))

    large_void_scalar = np.zeros((), dtype="V257").view(NoTobytesArray)
    assert digest(large_void_scalar) == reference_digest(np.asarray(large_void_scalar))


def test_digest_noncontiguous_payload_updates_stay_within_chunk(monkeypatch):
    monkeypatch.setattr(receipt_module, "_CHUNK", 32)
    original_sha256 = receipt_module.sha256
    payload_update_lengths = []

    class RecordingHash:
        def __init__(self):
            self._hash = original_sha256()

        def update(self, value):
            payload_update_lengths.append(memoryview(value).nbytes)
            self._hash.update(value)

        def hexdigest(self):
            return self._hash.hexdigest()

    monkeypatch.setattr(receipt_module, "sha256", RecordingHash)
    array = np.arange(512, dtype=np.int16)[::-2]
    assert digest(array) == reference_digest(array)
    assert max(payload_update_lengths) <= 32
