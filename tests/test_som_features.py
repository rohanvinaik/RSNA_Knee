"""Both-sign contracts for measured navigation inputs and independent targets."""

import copy
import csv
import json
from pathlib import Path

import numpy as np
import pytest

from knee.diagnosis.som_features import (
    NavigationFeatureError,
    condition_indices_for_subject,
    counts_for_record,
    features_for_record,
    fit_feature_schema,
    population_study_uids,
    validate_feature_population,
)
from knee.diagnosis.squint_interfaces import territory_bank_name
from knee.study.tables import LABELS, TRAIN_COLUMNS
from scripts.prepare_som_navigation import prepare_navigation

BANK = territory_bank_name(
    {"orientation": "Sagittal", "fluid_sensitive": "1", "fat_suppression": "1"},
    "object",
    "local_range",
    "overview",
    10,
)
MEMORY_SHA = "a" * 64


def study(uid="train", counts=(1, 2, 3)):
    return {
        "schema": "knee.squint-study/v1",
        "study_uid": uid,
        "memory_revision": "parent",
        "objects": {
            "acl": {"profile": {"subject": "acl", "banks": {BANK: list(counts)}}}
        },
        "questions": {},
        "capacity_exclusion": {"exclusion_status": "not_requested"},
    }


def excluded(record):
    record["capacity_exclusion"] = {
        "exclusion_status": "applied",
        "excluded_study_uid": record["study_uid"],
        "original_case_count": 5,
        "filtered_case_count": 4,
        "excluded_case_count": 1,
        "original_censor_count": 1,
        "filtered_censor_count": 1,
        "excluded_censor_count": 0,
        "consumed_case_fingerprint": "fingerprint",
        "preparation_schema": "knee.squint-recall-preparation/v1",
        "preparation_outcome": "prepared",
        "consumed_fingerprint_scope": "source_cases_calls_profiles_and_censors_v1",
        "prepared_population_identity": {
            "status": "prepared",
            "source_fingerprint": "fingerprint",
            "memory_manifest_sha256": MEMORY_SHA,
        },
    }
    return record


def test_counts_are_retained_and_measured_neutral_is_not_missing():
    record = study(counts=(0, 7, 0))
    schema = fit_feature_schema([record])
    vector = features_for_record(schema, record)
    assert vector.dtype == np.float32
    assert vector.tolist() == [0, 1, 0, 7, 1]
    assert counts_for_record(schema, record).tolist() == [[0, 7, 0]]
    missing = study()
    missing["objects"]["acl"]["profile"]["banks"] = {}
    assert features_for_record(schema, missing).tolist() == [0, 0, 0, 0, 0]


def test_validation_does_not_add_vocabulary_or_teacher_data_to_features():
    training = study()
    schema = fit_feature_schema([training])
    validation = study("validation")
    validation["objects"]["acl"]["profile"]["banks"][BANK.replace("10mm", "2mm")] = [
        8,
        1,
        1,
    ]
    validation.update({"values": {"ACL": 1}, "Report": "tear", "labels": {"ACL": 1}})
    assert len(schema["banks"]) == 1
    np.testing.assert_array_equal(
        features_for_record(schema, validation), features_for_record(schema, training)
    )
    assert "validation" not in json.dumps(schema)
    assert schema["specialist_groups"][0]["condition_indices"] == [LABELS.index("ACL")]
    assert LABELS.index("ACL") not in condition_indices_for_subject("femur")


def test_both_sides_and_observed_law_disagreement_remain_distinct():
    record = study()
    record["questions"] = {
        "ACL": {
            "objects": {
                "acl": {
                    "case_terms": [
                        {
                            "call": 1,
                            "terms": {"dot": 3, "left_norm_sq": 5, "right_norm_sq": 5},
                            "reaches_trust": True,
                        },
                        {
                            "call": -1,
                            "terms": {"dot": 4, "left_norm_sq": 5, "right_norm_sq": 5},
                            "reaches_trust": True,
                        },
                    ],
                    "censor_terms": [{"reaches_trust": True}],
                }
            }
        }
    }
    record["objects"]["acl"]["sanity"] = {
        "windows": [
            {
                "checks": [
                    {
                        "rule_id": "observed-relation",
                        "candidate_role": "subject",
                        "axis": "z",
                        "result": "unknown",
                    },
                    {
                        "rule_id": "observed-relation",
                        "candidate_role": "subject",
                        "axis": "z",
                        "result": "supported_between",
                    },
                ]
            }
        ]
    }
    schema = fit_feature_schema([record])
    vector = features_for_record(schema, record)
    lookup = dict(zip(schema["feature_names"], vector, strict=True))
    positives = [
        v
        for k, v in lookup.items()
        if "positive/best_cosine" in k and k.endswith("/value")
    ]
    negatives = [
        v
        for k, v in lookup.items()
        if "negative/best_cosine" in k and k.endswith("/value")
    ]
    assert positives == pytest.approx([0.6])
    assert negatives == pytest.approx([0.8])
    assert any("supported_between" in k and v == 1 for k, v in lookup.items())
    assert any("unknown" in k and v == 1 for k, v in lookup.items())
    changed = copy.deepcopy(record)
    changed["questions"]["ACL"]["finding"] = {"outcome": "defeated", "probability": 0}
    np.testing.assert_array_equal(features_for_record(schema, changed), vector)


def test_actual_subject_to_list_recall_evidence_is_consumed_and_silence_is_unavailable():
    record = study()
    record["questions"] = {
        "ACL": {
            "finding": {"outcome": "open"},
            "observation_requests": [],
            "recall_evidence": {
                "acl": [
                    {
                        "case_terms": [
                            {
                                "call": 1,
                                "terms": {
                                    "dot": 3,
                                    "left_norm_sq": 5,
                                    "right_norm_sq": 5,
                                },
                                "reaches_trust": True,
                            }
                        ]
                    },
                    {
                        "case_terms": [
                            {
                                "call": -1,
                                "terms": {
                                    "dot": 4,
                                    "left_norm_sq": 5,
                                    "right_norm_sq": 5,
                                },
                                "reaches_trust": True,
                            }
                        ],
                        "vetoed_answers": [-1],
                    },
                ]
            },
        }
    }
    schema = fit_feature_schema([record])
    vector = features_for_record(schema, record)
    lookup = dict(zip(schema["feature_names"], vector, strict=True))
    assert any(
        "positive/best_cosine" in key
        and key.endswith("/value")
        and value == pytest.approx(0.6)
        for key, value in lookup.items()
    )
    assert any(
        "negative/best_cosine" in key
        and key.endswith("/value")
        and value == pytest.approx(0.8)
        for key, value in lookup.items()
    )
    assert not any("censor/compared_count" in key for key in lookup)
    silent = copy.deepcopy(record)
    silent["questions"]["ACL"]["recall_evidence"]["acl"] = [{"case_terms": []}]
    silent_values = dict(
        zip(schema["feature_names"], features_for_record(schema, silent), strict=True)
    )
    assert all(
        value == 0 for key, value in silent_values.items() if "best_cosine" in key
    )


@pytest.mark.parametrize("counts", [[True, 0, 0], [-1, 2, 3], [0.1, 2, 3], [1, 2]])
def test_malformed_counts_never_become_features(counts):
    record = study()
    record["objects"]["acl"]["profile"]["banks"][BANK] = counts
    with pytest.raises(NavigationFeatureError, match="bank_counts_invalid"):
        fit_feature_schema([record])


def test_population_uses_each_generating_parent_and_all_signed_stores():
    parent = {
        "cases": [
            {
                "study_uid": "positive",
                "configuration_teaching": {
                    "roles": {"bone": {"source_study_uids": ["nested"]}}
                },
            }
        ],
        "censors": [{"source": {"study_uid": "censored"}}],
        "object_identity_cases": {"cases": [{"study_uid": "negative"}]},
        "procedure_experiences": {"rows": [{"source": {"study_uid": "procedural"}}]},
    }
    population = population_study_uids(parent)
    assert population == {"positive", "negative", "censored", "procedural", "nested"}
    assert (
        validate_feature_population(
            study("fresh"), MEMORY_SHA, population_uids=population
        )
        == "fresh_to_verified_generating_memory"
    )
    with pytest.raises(NavigationFeatureError):
        validate_feature_population(
            study("negative"), MEMORY_SHA, population_uids=population
        )
    assert (
        validate_feature_population(
            study("negative"),
            MEMORY_SHA,
            population_uids=population,
            training=True,
            allow_teacher_readback=True,
        )
        == "teacher_readback_training_only"
    )
    with pytest.raises(NavigationFeatureError):
        validate_feature_population(
            study("negative"),
            MEMORY_SHA,
            population_uids=population,
            allow_teacher_readback=True,
        )


def test_exclusion_must_match_the_actual_generating_memory():
    record = excluded(study())
    assert validate_feature_population(record, MEMORY_SHA) == "whole_study_excluded"
    with pytest.raises(
        NavigationFeatureError, match="exclusion_population_identity_invalid"
    ):
        validate_feature_population(record, "b" * 64)


def test_export_real_cli_contract_masks_unknown_and_preserves_whole_uid_split(
    tmp_path: Path,
):
    run = tmp_path / "run"
    run.mkdir()
    entries = []
    for uid in ["train", "validation"]:
        record = excluded(study(uid))
        path = run / (uid + ".json")
        path.write_text(json.dumps(record))
        entries.append(
            {
                "study_uid": uid,
                "evidence_path": path.name,
                "capacity_exclusion": record["capacity_exclusion"],
            }
        )
    (run / "receipt.json").write_text(
        json.dumps(
            {
                "action": "capacity",
                "source_mode": "raw_squint_case_recall",
                "memory_manifest_sha256": MEMORY_SHA,
                "memory_revision": "parent",
                "studies": 2,
                "work": {"studies": entries},
            }
        )
    )
    labels = tmp_path / "train.csv"
    with labels.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=TRAIN_COLUMNS)
        writer.writeheader()
        writer.writerow({"StudyInstanceUID": "train", "ACL": "1"})
        writer.writerow({"StudyInstanceUID": "validation", "ACL": "0"})
    output = tmp_path / "dataset"
    receipt = prepare_navigation(
        runs=[run],
        labels=labels,
        report_calls=[],
        train_uids=["train"],
        validation_uids=["validation"],
        output=output,
    )
    with np.load(output / "dataset.npz", allow_pickle=False) as dataset:
        assert dataset["study_uids"].tolist() == ["train", "validation"]
        assert dataset["y"][:, LABELS.index("ACL")].tolist() == [1, 0]
        assert dataset["label_mask"].sum() == 2
        assert dataset["train_mask"].tolist() == [True, False]
        assert dataset["validation_mask"].tolist() == [False, True]
        assert dataset["raw_counts"].dtype == np.int64
    assert receipt["training_studies"] == receipt["validation_studies"] == 1
    with pytest.raises(NavigationFeatureError, match="study_split_overlap"):
        prepare_navigation(
            runs=[run],
            labels=labels,
            report_calls=[],
            train_uids=["train"],
            validation_uids=["train"],
            output=tmp_path / "overlap",
        )
