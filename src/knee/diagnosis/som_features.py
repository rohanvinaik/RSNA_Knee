"""Typed numerical navigation inputs from already measured HDC banks.

Labels, reports, UIDs, candidate names asserted by recall, and diagnostic
decisions are never feature values. A bank's three signed counts remain
recoverable in ``raw_counts``; float32 fractions are the learner's view.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from knee.diagnosis.squint_contracts import contract_for
from knee.diagnosis.squint_interfaces import parse_territory_bank_name
from knee.study.tables import LABELS

SCHEMA = "knee.som-navigation-features/v1"
CHANNELS = (
    "negative_fraction",
    "neutral_fraction",
    "positive_fraction",
    "count",
    "available",
)


class NavigationFeatureError(ValueError):
    """A named input-contract refusal."""


def measured_banks(record: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Read each subject's actual bank once, preserving its typed address."""
    objects = record.get("objects")
    if not isinstance(objects, Mapping):
        raise NavigationFeatureError("objects_required")
    result: dict[str, dict[str, Any]] = {}
    for obj in objects.values():
        if not isinstance(obj, Mapping):
            raise NavigationFeatureError("object_invalid")
        profile = obj.get("profile")
        if profile is None:
            continue
        if not isinstance(profile, Mapping):
            raise NavigationFeatureError("profile_invalid")
        subject, banks = profile.get("subject"), profile.get("banks")
        if (
            not isinstance(subject, str)
            or not subject
            or not isinstance(banks, Mapping)
        ):
            raise NavigationFeatureError("profile_subject_or_banks_invalid")
        for bank, raw in banks.items():
            address = parse_territory_bank_name(bank)
            if address is None or not all(isinstance(v, str) for v in address["view"]):
                raise NavigationFeatureError("bank_address_invalid")
            if not math.isfinite(address["scale_mm"]) or address["scale_mm"] <= 0:
                raise NavigationFeatureError("bank_scale_invalid")
            if (
                not isinstance(raw, (tuple, list))
                or len(raw) != 3
                or any(type(v) is not int or v < 0 for v in raw)
                or any(v > np.iinfo(np.int64).max for v in raw)
                or sum(raw) > np.iinfo(np.int64).max
            ):
                raise NavigationFeatureError("bank_counts_invalid")
            name = json.dumps(
                [subject, bank], ensure_ascii=False, separators=(",", ":")
            )
            item = {
                "name": name,
                "subject": subject,
                "bank": bank,
                "view": list(address["view"]),
                "role": address["role"],
                "metric": address["metric"],
                "direction": address["direction"],
                "scale_mm": address["scale_mm"],
                "counts": tuple(raw),
            }
            if name in result and result[name]["counts"] != item["counts"]:
                raise NavigationFeatureError("duplicate_subject_bank_conflict")
            result[name] = item
    return result


def condition_indices_for_subject(subject: str) -> list[int]:
    """Existing defining roles only; these are study-condition opinion targets.

    A fracture-positive study is not a localized positive label on each bone.
    Supporting objects remain available in full context, not specialist gold.
    """
    result = []
    for index, question in enumerate(LABELS):
        contract = contract_for(question)
        defining = set(contract.necessary) | set(contract.alternatives)
        defining.update(role for branch in contract.sufficient for role in branch)
        if subject in defining:
            result.append(index)
    return result


def _cosine(row: Mapping[str, Any]) -> float | None:
    terms = row.get("terms", row)
    if not isinstance(terms, Mapping):
        return None
    values = [terms.get(key) for key in ("dot", "left_norm_sq", "right_norm_sq")]
    if any(type(v) is not int for v in values) or values[1] <= 0 or values[2] <= 0:
        return None
    dot, left, right = values
    if dot * dot > left * right:
        raise NavigationFeatureError("recall_terms_invalid")
    return dot / math.sqrt(left * right)


def recall_evidence_features(record: Mapping[str, Any]) -> dict[str, tuple[str, float]]:
    """Numerical BOTH-side memory/law readings, never the final readout or truth.

    The returned subject groups are domains, not asserted identities. Actual
    applicable negatives remain separate from positive resemblance; other-object
    names are never automatically recoded as countercases.
    """
    result: dict[str, tuple[str, float]] = {}

    def put(subject: str, axis: str, metric: str, value: float) -> None:
        name = json.dumps(
            [subject, axis, metric], ensure_ascii=False, separators=(",", ":")
        )
        result[name] = (subject, float(value))

    def comparisons(
        subject: str, axis: str, positive: list, negative: list, censors: list | None
    ) -> None:
        put(subject, axis, "comparison_record_available", 1)
        for sign, rows in (("positive", positive), ("negative", negative)):
            comparable = [
                (row, _cosine(row)) for row in rows if isinstance(row, Mapping)
            ]
            values = [value for _, value in comparable if value is not None]
            if values:
                put(subject, axis, sign + "/best_cosine", max(values))
            put(subject, axis, sign + "/available", bool(values))
            put(subject, axis, sign + "/comparison_count", len(values))
            put(
                subject,
                axis,
                sign + "/speaking_count",
                sum(
                    row.get("reaches_trust", row.get("speaks")) is True
                    for row, value in comparable
                    if value is not None
                ),
            )
        if censors is not None:
            put(subject, axis, "censor/compared_count", len(censors))
            put(
                subject,
                axis,
                "censor/active_count",
                sum(
                    isinstance(row, Mapping) and row.get("reaches_trust") is True
                    for row in censors
                ),
            )

    questions = record.get("questions", {})
    if isinstance(questions, Mapping):
        for question in LABELS:
            entry = questions.get(question, {})
            if not isinstance(entry, Mapping):
                continue
            finding = entry.get("finding", {})
            evidence = entry.get("recall_evidence")
            if not isinstance(evidence, Mapping) and isinstance(finding, Mapping):
                evidence = finding.get("recall_evidence")
            if not isinstance(evidence, Mapping):
                evidence = entry.get("objects", {})
            if not isinstance(evidence, Mapping):
                continue
            for subject, value in evidence.items():
                rows = value if isinstance(value, list) else [value]
                rows = [row for row in rows if isinstance(row, Mapping)]
                if not isinstance(subject, str) or not rows:
                    continue
                terms = [
                    term
                    for row in rows
                    if isinstance(row.get("case_terms"), list)
                    for term in row["case_terms"]
                ]
                censor_rows = [
                    row for row in rows if isinstance(row.get("censor_terms"), list)
                ]
                censors = (
                    [term for row in censor_rows for term in row["censor_terms"]]
                    if censor_rows
                    else None
                )
                comparisons(
                    subject,
                    "condition/" + question,
                    [r for r in terms if isinstance(r, Mapping) and r.get("call") == 1],
                    [
                        r
                        for r in terms
                        if isinstance(r, Mapping) and r.get("call") == -1
                    ],
                    censors,
                )
                for field in ("censor_ids", "vetoed_answers"):
                    observed = [
                        row[field] for row in rows if isinstance(row.get(field), list)
                    ]
                    if observed:
                        put(
                            subject,
                            "condition/" + question,
                            field + "/count",
                            len(
                                {
                                    v
                                    for values in observed
                                    for v in values
                                    if isinstance(v, (str, int))
                                }
                            ),
                        )
    identity = record.get("identity_recall", {})
    if isinstance(identity, Mapping):
        for stage, table in (
            ("squint", identity),
            ("resolved", identity.get("resolved_scale", {})),
        ):
            if not isinstance(table, Mapping) or not isinstance(
                table.get("objects"), Mapping
            ):
                continue
            for subject, row in table["objects"].items():
                if not isinstance(row, Mapping) or not isinstance(subject, str):
                    continue
                positives = row.get("cases", [])
                negatives = [
                    r.get("over_the_asserted_region", {})
                    for r in row.get("negative_cases", [])
                    if isinstance(r, Mapping) and r.get("applies") is True
                ]
                comparisons(
                    subject,
                    "identity/" + stage,
                    positives if isinstance(positives, list) else [],
                    negatives,
                    [],
                )
    objects = record.get("objects", {})
    if isinstance(objects, Mapping):
        for subject, obj in objects.items():
            if not isinstance(obj, Mapping) or not isinstance(subject, str):
                continue
            sanity = obj.get("sanity", {})
            if not isinstance(sanity, Mapping):
                continue
            states: dict[tuple[str, str], int] = {}
            for window in sanity.get("windows", []):
                if not isinstance(window, Mapping):
                    continue
                for check in window.get("checks", []):
                    if not isinstance(check, Mapping) or not isinstance(
                        check.get("result"), str
                    ):
                        continue
                    # Named authored law, actual tested role/axis and result;
                    # no pixel coordinates, source UID, or proposed-name gold.
                    axis = json.dumps(
                        [
                            check.get("rule_id"),
                            check.get("candidate_role"),
                            check.get("axis"),
                        ],
                        separators=(",", ":"),
                    )
                    key = (axis, check["result"])
                    states[key] = states.get(key, 0) + 1
            for (axis, state), count in states.items():
                put(subject, "law/" + axis, state + "/observed_count", count)
    return result


def fit_feature_schema(training_records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Fit the address vocabulary using training records only, never targets."""
    if not training_records:
        raise NavigationFeatureError("training_records_required")
    vocabulary: dict[str, dict[str, Any]] = {}
    for record in training_records:
        for name, item in measured_banks(record).items():
            vocabulary[name] = {
                key: value for key, value in item.items() if key != "counts"
            }
    if not vocabulary:
        raise NavigationFeatureError("training_banks_missing")
    banks = [vocabulary[name] for name in sorted(vocabulary)]
    feature_names = [
        f"{bank['name']}/{channel}" for bank in banks for channel in CHANNELS
    ]
    by_subject: dict[str, list[int]] = {}
    for index, bank in enumerate(banks):
        by_subject.setdefault(bank["subject"], []).extend(
            range(index * len(CHANNELS), (index + 1) * len(CHANNELS))
        )
    evidence: dict[str, str] = {}
    for record in training_records:
        evidence.update(
            {
                name: subject
                for name, (subject, _) in recall_evidence_features(record).items()
            }
        )
    evidence_features = [
        {"name": name, "subject": evidence[name]} for name in sorted(evidence)
    ]
    for entry in evidence_features:
        index = len(feature_names)
        feature_names.extend((entry["name"] + "/value", entry["name"] + "/available"))
        by_subject.setdefault(entry["subject"], []).extend((index, index + 1))
    groups, context_only = [], []
    for subject, indices in sorted(by_subject.items()):
        conditions = condition_indices_for_subject(subject)
        if conditions:
            groups.append(
                {
                    "name": subject,
                    "feature_indices": indices,
                    "condition_indices": conditions,
                }
            )
        else:
            context_only.append(subject)
    return {
        "schema": SCHEMA,
        "labels": list(LABELS),
        "channels": list(CHANNELS),
        "banks": banks,
        "evidence_features": evidence_features,
        "feature_names": feature_names,
        "specialist_groups": groups,
        "context_only_subjects": context_only,
        "target_scope": "study_condition_opinion_not_localized_lesion",
        "missing_bank": "zero_count_and_unavailable; measured_neutral_has_positive_count",
        "raw_count_storage": "raw_counts int64[N,B,3], negative/neutral/positive order",
        "learner_view": "float32 fractions,count,availability; exact counts retained separately",
    }


def counts_for_record(
    schema: Mapping[str, Any], record: Mapping[str, Any]
) -> np.ndarray:
    """Project one study into the training vocabulary; unseen banks stay unused."""
    if schema.get("schema") != SCHEMA or not isinstance(schema.get("banks"), list):
        raise NavigationFeatureError("feature_schema_invalid")
    banks = schema["banks"]
    measured = measured_banks(record)
    result = np.zeros((len(banks), 3), dtype=np.int64)
    for index, bank in enumerate(banks):
        if not isinstance(bank, Mapping) or not isinstance(bank.get("name"), str):
            raise NavigationFeatureError("feature_schema_bank_invalid")
        item = measured.get(bank["name"])
        if item is not None:
            result[index] = item["counts"]
    return result


def features_for_record(
    schema: Mapping[str, Any], record: Mapping[str, Any]
) -> np.ndarray:
    """Production adapter: measured banks -> one float32 vector, without labels."""
    counts = counts_for_record(schema, record)
    totals = counts.sum(axis=1)
    result = np.zeros((len(counts), len(CHANNELS)), dtype=np.float32)
    nonzero = totals > 0
    result[nonzero, :3] = counts[nonzero] / totals[nonzero, None]
    result[:, 3] = totals
    result[:, 4] = nonzero
    evidence = recall_evidence_features(record)
    extras = np.zeros(2 * len(schema.get("evidence_features", [])), dtype=np.float32)
    for index, entry in enumerate(schema.get("evidence_features", [])):
        value = evidence.get(entry["name"])
        if value is not None:
            extras[2 * index], extras[2 * index + 1] = value[1], 1
    return np.concatenate((result.reshape(-1), extras))


def population_study_uids(memory: Mapping[str, Any]) -> frozenset[str]:
    """All speaking stores, including nested configuration/procedure lineage.

    The ordinary memory view checks row and source UIDs. Freshness proof here is
    deliberately stronger: a nested source-study mention prevents an unsupported
    claim that the generating memory never saw that study.
    """
    stores = [memory.get("cases", ()), memory.get("censors", ())]
    for name, key in (
        ("object_identity_cases", "cases"),
        ("procedure_experiences", "rows"),
    ):
        block = memory.get(name)
        if block is not None:
            if not isinstance(block, Mapping):
                raise NavigationFeatureError("population_table_invalid")
            stores.append(block.get(key, ()))
    uids = set()

    def visit(value: object) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if key in ("study_uid", "source_study_uid") and child is not None:
                    if not isinstance(child, str) or not child:
                        raise NavigationFeatureError("population_uid_invalid")
                    uids.add(child)
                elif key in ("study_uids", "source_study_uids"):
                    if not isinstance(child, (list, tuple)) or any(
                        not isinstance(uid, str) or not uid for uid in child
                    ):
                        raise NavigationFeatureError("population_uid_invalid")
                    uids.update(child)
                if isinstance(child, (Mapping, list, tuple)):
                    visit(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                if isinstance(child, (Mapping, list, tuple)):
                    visit(child)

    for rows in stores:
        if not isinstance(rows, (list, tuple)):
            raise NavigationFeatureError("population_rows_invalid")
        for row in rows:
            if not isinstance(row, Mapping):
                raise NavigationFeatureError("population_row_invalid")
            visit(row)
    return frozenset(uids)


def validate_feature_population(
    record: Mapping[str, Any],
    memory_sha256: str,
    *,
    population_uids: frozenset[str] | None = None,
    training: bool = False,
    allow_teacher_readback: bool = False,
) -> str:
    """Prove exclusion/freshness, or explicitly name TRAIN-only teacher input."""
    uid = record.get("study_uid")
    if not isinstance(uid, str) or not uid:
        raise NavigationFeatureError("study_uid_invalid")
    exclusion = record.get("capacity_exclusion")
    if (
        isinstance(exclusion, Mapping)
        and exclusion.get("exclusion_status") == "applied"
    ):
        if exclusion.get("excluded_study_uid") != uid:
            raise NavigationFeatureError("exclusion_uid_mismatch")
        for kind in ("case", "censor"):
            keys = [
                f"{prefix}_{kind}_count"
                for prefix in ("original", "filtered", "excluded")
            ]
            values = [exclusion.get(key) for key in keys]
            if (
                any(type(v) is not int or v < 0 for v in values)
                or values[0] != values[1] + values[2]
            ):
                raise NavigationFeatureError("exclusion_counts_invalid")
        identity = exclusion.get("prepared_population_identity")
        fingerprint = exclusion.get("consumed_case_fingerprint")
        if (
            exclusion.get("preparation_schema") != "knee.squint-recall-preparation/v1"
            or exclusion.get("preparation_outcome") != "prepared"
            or exclusion.get("consumed_fingerprint_scope")
            != "source_cases_calls_profiles_and_censors_v1"
            or not isinstance(fingerprint, str)
            or not fingerprint
            or not isinstance(identity, Mapping)
            or identity.get("status") != "prepared"
            or identity.get("source_fingerprint") != fingerprint
            or identity.get("memory_manifest_sha256") != memory_sha256
        ):
            raise NavigationFeatureError("exclusion_population_identity_invalid")
        return "whole_study_excluded"
    if population_uids is not None and uid not in population_uids:
        return "fresh_to_verified_generating_memory"
    if training and allow_teacher_readback:
        return "teacher_readback_training_only"
    raise NavigationFeatureError(
        "generating_memory_population_not_excluded_or_verified_fresh"
    )
