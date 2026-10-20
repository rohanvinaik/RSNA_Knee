"""Independent study labels joined to individual question-composite image cases.

No recall result is accepted as a teacher here. Reports remain source provenance;
this module neither interprets them nor localizes study labels to tissues/pixels.
The returned receipt is a separate ledger, never evidence inferred by memory.

Sparse identity schema (unpublished IDs deliberately change): every fingerprint
is SHA256 of UTF-8 JSON, sorted object keys, separators (",", ":"), ensure_ascii
False. Versioned documents form the following exact chain:

* knee.diagnostic-count-layout/v1: schema_version, layout_id, carrier_id, banks
  (complete ordered [name, row_count] pairs, including silent banks).
* knee.diagnostic-count-row-sparse/v1: schema_version, row_count, nonzero_rows
  (ascending [zero-based row index, lowercase unprefixed hexadecimal count]
  pairs). Omitted rows are exactly zero; hexadecimal preserves arbitrary-size
  integers without Python's decimal JSON digit limit.
* knee.diagnostic-count-bundle-sparse/v1: schema_version, layout_fingerprint,
  speaking_banks (ascending [zero-based bank index, row fingerprint] pairs).
  Omitted banks are entirely zero under the complete declared layout.
* knee.diagnostic-profile-sparse/v1: schema_version, subject, bundle_fingerprint,
  mode, scope, source_id, context, bank_statuses, provenance. Metadata pairs are
  lexicographically sorted for identity only; original profiles stay unchanged.
* knee.diagnostic-case-sparse/v2: schema_version, revision, study_uid,
  profile_fingerprint, call (question, digit, source, words).

The receipt names the case schema, records every profile fingerprint and retains
each complete layout document once, keyed by its fingerprint. No diagnostic call
enters the profile fingerprint. All reuse is scoped to one teach_from_labels
invocation; immutable objects are held strongly so Python id reuse is impossible.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from knee.diagnosis.models import Call, Case, Profile, Snapshot
from knee.encoding.counts import CountBundle, CountLayout, _is_plain_int, _valid_layout
from knee.study.tables import LABELS, TRAIN_COLUMNS


def csv_label_status(value: str) -> str:
    """Classify exact CSV spelling; a blank supplies no diagnostic call."""
    if value == "1":
        return "positive"
    if value == "0":
        return "negative"
    if value == "":
        return "blank"
    return "invalid_label"


def binary_label_status(value: int | None) -> str:
    """Classify independent binary labels without bool/float coercion."""
    if value is None:
        return "blank"
    if type(value) is not int:
        return "invalid_type"
    if value == 1:
        return "positive"
    if value == 0:
        return "negative"
    return "invalid_label"


def labels_from_csv(path: Path) -> dict[str, dict[str, int | None]]:
    """Read the exact train.csv schema, preserving blanks and refusing bad input.

    Report is deliberately not a label. The caller retains the original CSV and
    reports as provenance; the contracted return contains only binary labels.
    """
    labels: dict[str, dict[str, int | None]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle, strict=True)
        try:
            if tuple(next(reader, ())) != TRAIN_COLUMNS:
                raise ValueError("invalid_train_columns")
            for row in reader:
                if len(row) != len(TRAIN_COLUMNS):
                    raise ValueError(f"invalid_row_width: line {reader.line_num}")
                uid = row[0]
                _require_text(uid, "study_uid")
                if uid in labels:
                    raise ValueError(f"duplicate_study_uid: {uid}")
                calls: dict[str, int | None] = {}
                for question, value in zip(LABELS, row[2:], strict=True):
                    status = csv_label_status(value)
                    if status == "invalid_label":
                        raise ValueError(f"invalid_label: {uid}/{question}: {value!r}")
                    calls[question] = None if status == "blank" else int(value)
                labels[uid] = calls
        except csv.Error as exc:
            raise ValueError(f"malformed_csv: line {reader.line_num}: {exc}") from exc
    return labels


def _require_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"invalid_{name}")


def _digest(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sparse_row(row: tuple[int, ...]) -> tuple[str, bool]:
    """Validate all counts once and fingerprint exact nonzero row positions."""
    nonzero = []
    for index, count in enumerate(row):
        if not _is_plain_int(count) or count < 0:
            raise ValueError("invalid_profile_counts")
        if count:
            nonzero.append([index, format(count, "x")])
    return _digest(
        {
            "schema_version": "knee.diagnostic-count-row-sparse/v1",
            "row_count": len(row),
            "nonzero_rows": nonzero,
        }
    ), bool(nonzero)


class _IdentityScope:
    """One run's exact immutable identity reuse; never hash dense tuples as keys."""

    def __init__(self) -> None:
        self.layouts: dict[str, dict] = {}
        self._layout_objects: dict[int, tuple[CountLayout, str]] = {}
        self._layout_values: dict[tuple, str] = {}
        self._rows: dict[int, tuple[tuple[int, ...], str, bool]] = {}
        self._bundles: dict[int, tuple[CountBundle, str, bool]] = {}
        self._profiles: dict[int, tuple[Profile, str, bool]] = {}

    def _layout(self, layout: CountLayout) -> str:
        cached = self._layout_objects.get(id(layout))
        if cached is not None:
            return cached[1]
        if not _valid_layout(layout):
            raise ValueError("invalid_profile_counts")
        banks = tuple((bank.name, bank.row_count) for bank in layout.banks)
        key = (layout.layout_id, layout.carrier_id, banks)
        fingerprint = self._layout_values.get(key)
        if fingerprint is None:
            document = {
                "schema_version": "knee.diagnostic-count-layout/v1",
                "layout_id": layout.layout_id,
                "carrier_id": layout.carrier_id,
                "banks": [list(bank) for bank in banks],
            }
            fingerprint = _digest(document)
            self.layouts[fingerprint] = document
            self._layout_values[key] = fingerprint
        self._layout_objects[id(layout)] = (layout, fingerprint)
        return fingerprint

    def _bundle(self, bundle: CountBundle) -> tuple[str, bool]:
        cached = self._bundles.get(id(bundle))
        if cached is not None:
            return cached[1], cached[2]
        if not isinstance(bundle, CountBundle):
            # Preserve the existing count validator's single invalid-input state.
            raise ValueError("invalid_profile_counts")  # noqa: TRY004
        layout_fingerprint = self._layout(bundle.layout)
        if not isinstance(bundle.counts, tuple) or len(bundle.counts) != len(
            bundle.layout.banks
        ):
            raise ValueError("invalid_profile_counts")
        speaking = []
        for index, (row, bank) in enumerate(
            zip(bundle.counts, bundle.layout.banks, strict=True)
        ):
            # Cardinality belongs to each occurrence, even for a shared row.
            if not isinstance(row, tuple) or len(row) != bank.row_count:
                raise ValueError("invalid_profile_counts")
            known = self._rows.get(id(row))
            if known is None:
                row_fingerprint, speaks = _sparse_row(row)
                self._rows[id(row)] = (row, row_fingerprint, speaks)
            else:
                _, row_fingerprint, speaks = known
            if speaks:
                speaking.append([index, row_fingerprint])
        fingerprint = _digest(
            {
                "schema_version": "knee.diagnostic-count-bundle-sparse/v1",
                "layout_fingerprint": layout_fingerprint,
                "speaking_banks": speaking,
            }
        )
        speaks = bool(speaking)
        self._bundles[id(bundle)] = (bundle, fingerprint, speaks)
        return fingerprint, speaks

    def profile(self, profile: Profile) -> tuple[str, bool]:
        cached = self._profiles.get(id(profile))
        if cached is not None:
            return cached[1], cached[2]
        bundle_fingerprint, speaks = self._bundle(profile.bundle)
        fingerprint = _digest(
            {
                "schema_version": "knee.diagnostic-profile-sparse/v1",
                "subject": profile.subject,
                "bundle_fingerprint": bundle_fingerprint,
                "mode": profile.mode,
                "scope": profile.scope,
                "source_id": profile.source_id,
                "context": sorted(profile.context),
                "bank_statuses": sorted(profile.bank_statuses),
                "provenance": sorted(profile.provenance),
            }
        )
        self._profiles[id(profile)] = (profile, fingerprint, speaks)
        return fingerprint, speaks


def _validated_labels(
    labels: Mapping[str, Mapping[str, int | None]],
) -> dict[str, dict[str, int | None]]:
    result: dict[str, dict[str, int | None]] = {}
    for uid, row in labels.items():
        _require_text(uid, "study_uid")
        if not isinstance(row, Mapping):
            raise TypeError(f"invalid_label_row: {uid}")
        clean: dict[str, int | None] = {}
        for question, value in row.items():
            if question not in LABELS:
                raise ValueError(f"unknown_question: {question!r}")
            status = binary_label_status(value)
            if status in ("invalid_type", "invalid_label"):
                raise ValueError(f"{status}: {uid}/{question}: {value!r}")
            clean[question] = value
        result[uid] = clean
    return result


def _profile_metadata(profile: Profile, study_uid: str) -> dict[str, str]:
    """Keep explicit split/group declarations; never infer patient linkage."""
    metadata: dict[str, str] = {}
    for pairs in (profile.context, profile.provenance):
        if not isinstance(pairs, tuple):
            raise TypeError("invalid_profile_metadata")
        seen: set[str] = set()
        for pair in pairs:
            if not isinstance(pair, tuple) or len(pair) != 2:
                raise ValueError("invalid_profile_metadata")
            key, value = pair
            _require_text(key, "metadata_key")
            if not isinstance(value, str) or key in seen:
                raise ValueError("invalid_profile_metadata")
            seen.add(key)
            if key not in ("study_uid", "split", "source_group"):
                continue
            if key in metadata and metadata[key] != value:
                raise ValueError(f"contradictory_{key}")
            metadata[key] = value
    if "study_uid" in metadata and metadata["study_uid"] != study_uid:
        raise ValueError("profile_study_mismatch")
    return metadata


def _profiles_for_study(
    profiles: Sequence[Profile], study_uid: str, identities: _IdentityScope
) -> tuple[dict[str, list[tuple[str, Profile, bool]]], dict[str, str]]:
    by_question: dict[str, list[tuple[str, Profile, bool]]] = {}
    metadata: dict[str, str] = {}
    seen: set[str] = set()
    for profile in profiles:
        if not isinstance(profile, Profile):
            raise TypeError("invalid_profile")
        _require_text(profile.subject, "profile_subject")
        question = profile.subject.removeprefix("diagnosis/")
        if profile.subject != f"diagnosis/{question}" or question not in LABELS:
            raise ValueError(f"not_question_composite: {profile.subject!r}")
        for name in ("scope", "mode", "source_id"):
            _require_text(getattr(profile, name), f"profile_{name}")
        for key, value in _profile_metadata(profile, study_uid).items():
            if key in metadata and metadata[key] != value:
                raise ValueError(f"contradictory_{key}")
            metadata[key] = value
        identity, speaks = identities.profile(profile)
        if identity in seen:
            raise ValueError(f"duplicate_profile: {study_uid}/{question}")
        seen.add(identity)
        by_question.setdefault(question, []).append((identity, profile, speaks))
    return by_question, metadata


def teach_from_labels(
    profiles_by_study: Mapping[str, Sequence[Profile]],
    labels: Mapping[str, Mapping[str, int | None]],
    *,
    revision: str,
) -> tuple[Snapshot, dict]:
    """Build a frozen revision of scoped, independently called individual cases.

    Input subjects must be ``diagnosis/<condition>`` composites. Each profile
    receives only its own condition's call: CSV 1 -> +1, CSV 0 -> -1. Missing
    labels and silent image profiles remain explicit zero entries in the ledger.
    No trust radius, localization, normal-object claim or censor is inferred.

    ``split`` and ``source_group`` metadata are retained when explicitly supplied
    in profile context/provenance. Whole-study exclusion always applies, including
    all full/cheap views. Unknown stronger group links stay unknown. Callers must
    exclude the recorded studies/groups from any held-out evaluation snapshot.
    """
    _require_text(revision, "revision")
    clean_labels = _validated_labels(labels)
    for uid in profiles_by_study:
        _require_text(uid, "study_uid")
    label_source = f"labels-sha256:{_digest(clean_labels)}"
    cases: list[Case] = []
    ledger: list[dict] = []
    studies: list[dict] = []
    identities = _IdentityScope()
    for uid in sorted(set(profiles_by_study) | set(clean_labels)):
        by_question, metadata = _profiles_for_study(
            profiles_by_study.get(uid, ()), uid, identities
        )
        row = clean_labels.get(uid, {})
        study = {
            "study_uid": uid,
            "split": metadata.get("split") or None,
            "source_group": metadata.get("source_group") or None,
            "all_blank": bool(row) and all(value is None for value in row.values()),
        }
        studies.append(study)
        for question in LABELS:
            value = row.get(question)
            status = binary_label_status(value)
            supplied = by_question.get(question, ())
            if question not in row:
                reason = "not_asked" if uid in clean_labels else "no_label_row"
            elif status == "blank":
                reason = "blank_label"
            elif not supplied:
                reason = "missing_profile"
            else:
                reason = "signed_label"
            profiles = sorted(supplied, key=lambda item: item[0])
            for fingerprint, profile, speaks in profiles or ((None, None, False),):
                entry = {
                    "study_uid": uid,
                    "question": question,
                    "label": value,
                    "source": label_source,
                    "call_scope": f"diagnosis/{question}",
                    "profile_source_id": profile.source_id if profile else None,
                    "profile_scope": profile.scope if profile else None,
                    "profile_mode": profile.mode if profile else None,
                    "profile_fingerprint": fingerprint,
                    "split": study["split"],
                    "source_group": study["source_group"],
                    "reason": reason,
                    "digit": 0,
                    "case_id": None,
                    "teaching_revision": revision,
                }
                if reason == "signed_label" and profile is not None:
                    if not speaks:
                        entry["reason"] = "silent_profile"
                    else:
                        digit = 1 if value == 1 else -1
                        words = json.dumps(
                            {
                                **study,
                                "question": question,
                                "label": value,
                                "call_scope": entry["call_scope"],
                                "profile_scope": profile.scope,
                            },
                            sort_keys=True,
                        )
                        call = Call(question, digit, label_source, words)
                        identity = {
                            "schema_version": "knee.diagnostic-case-sparse/v2",
                            "revision": revision,
                            "study_uid": uid,
                            "profile_fingerprint": fingerprint,
                            "call": {
                                "question": call.question,
                                "digit": call.digit,
                                "source": call.source,
                                "words": call.words,
                            },
                        }
                        case_id = f"case-sha256:{_digest(identity)}"
                        cases.append(Case(case_id, uid, profile, (call,), revision))
                        entry["case_id"] = case_id
                        entry["digit"] = digit
                ledger.append(entry)
    snapshot = Snapshot(revision, tuple(cases))
    receipt = {
        "schema_version": "knee.diagnostic-teaching/v1",
        "identity_schema_version": "knee.diagnostic-case-sparse/v2",
        "identity_layouts": dict(sorted(identities.layouts.items())),
        "revision": revision,
        "label_source": label_source,
        "source_kind": "independently_supplied_binary_labels",
        "studies": studies,
        "exclude_study_uids": sorted({case.study_uid for case in cases}),
        "exclude_source_groups": sorted(
            {
                entry["source_group"]
                for entry in ledger
                if entry["case_id"] is not None and entry["source_group"]
            }
        ),
        "case_count": len(cases),
        "ledger": ledger,
    }
    return snapshot, receipt
