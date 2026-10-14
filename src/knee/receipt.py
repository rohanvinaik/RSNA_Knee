"""The run's receipt: every study's records kept, one study's replaced at a time.

A run writes the receipt its renderers read. A study run again replaces only its own records,
silences and telemetry; every other study's stay as they were, since the input stage drops nothing
and neither does the run's record of it (the founder, 2026-10-10: «*I* decide what gets
compressed»). Records made under other settings are never mixed in: the receipt refuses. Two
processes writing one receipt would still lose each other's records, so a run folder takes one
process at a time.
"""


def merged_receipt(
    old: dict | None,
    request: dict,
    study_uid: str,
    series_uids: list[str],
    records: list[dict],
    unread: dict[str, str],
    telemetry: dict | None,
) -> dict:
    """The receipt with this study's records, silences and telemetry in place of what it held for
    the study before, and every other study's kept as it was.

    `old` is the receipt already in the run folder, None when there is none; `request` the
    settings this run reads under; `series_uids` every series of the study, read or not, so a
    series silent before and read now loses its old silence. `telemetry` is the study's ledger
    reading, or None when this receipt does not carry it. Raises `ValueError`
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
    return {
        "request": request,
        "records": kept + list(records),
        "unread": silences,
        "telemetry": telemetries,
    }
