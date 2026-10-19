"""The run's receipt: every study's records kept, one study's replaced at a time.

A run writes the receipt its renderers read. A study run again replaces only its own records,
silences and telemetry; every other study's stay as they were, since the input stage drops nothing
and neither does the run's record of it (the founder, 2026-10-10: «*I* decide what gets
compressed»). Records made under other settings are never mixed in: the receipt refuses. Two
processes writing one receipt would still lose each other's records, so a run folder takes one
process at a time.
"""

from hashlib import sha256

import numpy as np

_CHUNK = 1 << 24  # bytes handed to the hash (or copied) at a time


def _feed(hasher, a: np.ndarray) -> None:
    """Feed C-order bytes in chunks, with at most one oversized element copied at a time."""
    nbytes = a.size * a.itemsize
    if nbytes <= _CHUNK or a.ndim == 0:
        hasher.update(a.tobytes())
        return
    n = a.shape[0]
    step = max(1, _CHUNK // (nbytes // n))
    if step > 1 or a.ndim == 1:
        for i in range(0, n, step):
            hasher.update(a[i : i + step].tobytes())
    else:  # one row alone exceeds the bound: descend into it
        for i in range(n):
            _feed(hasher, a[i])


def digest(array: np.ndarray) -> str:
    """A saved array's digest: its dtype, shape and bytes. The one statement of it: the run notes
    each saved array's on its record, and every renderer checks the array it loads against it.

    Equal to sha256(dtype.str + str(shape) + C-order bytes), but the bytes are fed in bounded
    chunks rather than materialized whole."""
    hasher = sha256()
    hasher.update(array.dtype.str.encode())
    hasher.update(str(array.shape).encode())
    if array.size and array.itemsize and array.flags.c_contiguous:
        try:
            flat = array.reshape(-1).view(np.uint8)  # a view: no copy
        except (TypeError, ValueError):  # e.g. object dtype: use the generic path
            flat = None
        if flat is not None:
            for i in range(0, flat.size, _CHUNK):
                hasher.update(flat[i : i + _CHUNK])
            return hasher.hexdigest()
    _feed(hasher, array)
    return hasher.hexdigest()


def merged_receipt(
    old: dict | None,
    request: dict,
    study_uid: str,
    series_uids: list[str],
    records: list[dict],
    unread: dict[str, str],
    telemetry: dict | None,
    objects: dict | None = None,
) -> dict:
    """The receipt with this study's records, silences and telemetry in place of what it held for
    the study before, and every other study's kept as it was.

    `old` is the receipt already in the run folder, None when there is none; `request` the
    settings this run reads under; `series_uids` every series of the study, read or not, so a
    series silent before and read now loses its old silence. `telemetry` is the study's ledger
    reading, or None when this receipt does not carry it. `objects` is the study's anatomical
    objects (`knee.collapse.observations.describe_objects`), kept per study like its telemetry,
    or None when this receipt does not carry them. Raises `ValueError`
    ("receipt_request_differs") when `old` holds records made under other settings, since this
    receipt's request would misdescribe them.
    """
    old = old or {}
    if old.get("records") and old.get("request") != request:
        raise ValueError("receipt_request_differs")
    mine = set(series_uids)
    kept = [
        record for record in old.get("records", []) if record["study_uid"] != study_uid
    ]
    silences = {
        uid: code for uid, code in old.get("unread", {}).items() if uid not in mine
    }
    silences.update(unread)
    telemetries = {
        uid: reading
        for uid, reading in old.get("telemetry", {}).items()
        if uid != study_uid
    }
    if telemetry is not None:
        telemetries[study_uid] = telemetry
    described = {
        uid: reading
        for uid, reading in old.get("objects", {}).items()
        if uid != study_uid
    }
    if objects is not None:
        described[study_uid] = objects
    receipt = {
        "request": request,
        "records": kept + list(records),
        "unread": silences,
        "telemetry": telemetries,
    }
    if described:
        receipt["objects"] = described
    return receipt
