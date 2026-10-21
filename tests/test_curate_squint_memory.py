"""Curating a published squint memory: whole-case retirement on exact, pinned input.

Each test builds a tiny memory the way ``compile_bootstrap`` does (object cases,
canonical configuration cases linked to the shared full-profile payloads, a fresh
recall preparation, ``save_memory``) and drives the command's own functions
directly. No real memory is read, prepared or decoded; nothing here retires a
case on a label, a mask size, a cosine or any other measurement. The decisions
are written by the test, as the root will write them.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import knee
from knee.diagnosis.squint_configurations import with_configuration_cases
from knee.diagnosis.squint_interfaces import TERRITORY_PROCEDURE, territory_bank_name
from knee.diagnosis.squint_locator import (
    prepare_recall,
    recall_object,
    recall_source_fingerprint,
)
from knee.diagnosis.squint_memory import (
    SCHEMA,
    SquintMemoryError,
    _canonical,
    _condition_calls,
    _full_profile_retention_receipt,
    _intern_full_context,
    _link_configuration_full_profiles,
    _portable_tables,
    _question_object_roles,
    _retain_full_record,
    _sparse_count_availability,
    full_profile_from_case,
    load_memory_snapshot,
    save_memory,
)
from knee.encoding.places import (
    BankSpec,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    compile_layout,
)
from knee.json_store import load_json
from knee.study.tables import LABELS
from scripts import curate_squint_memory as curation

SCRIPT = Path(__file__).parents[1] / "scripts" / "curate_squint_memory.py"
V1_PROCEDURE = "knee.squint-profile/scan-tercile-v1"
VIEW = {"orientation": "Coronal", "fluid_sensitive": "1", "fat_suppression": "1"}
METRICS = ("signal_median", "local_range")
STUDIES = {
    "study-a": {"ACL": 1, "MCL": 0},
    "study-b": {"ACL": 0, "MCL": 1},
    "study-c": {"ACL": 1, "MCL": 1},
}
SUBJECTS = ("acl", "femur", "tibia", "pcl", "mcl", "medial_meniscus")
FEMUR_A = "squint-case:study-a:femur"
ACL_A = "squint-case:study-a:acl"


# --------------------------------------------------------------------------- fixture


def _bank_names(writer: str) -> list[str]:
    if writer == "territory":
        return [
            territory_bank_name(VIEW, "object", metric, "overview", 10.0)
            for metric in METRICS
        ]
    return [
        f"squint/v1/view=coronal/metric={metric}/overview/10mm" for metric in METRICS
    ]


def _profile(
    study_index: int, subject_index: int, subject: str, writer: str
) -> dict[str, Any]:
    procedure = TERRITORY_PROCEDURE if writer == "territory" else V1_PROCEDURE
    return {
        "schema": "knee.squint-profile/v1",
        "subject": subject,
        "banks": {
            name: [
                study_index + 1,
                subject_index + 2,
                (study_index + subject_index + bank_index) % 4 + 1,
            ]
            for bank_index, name in enumerate(_bank_names(writer))
        },
        "source": {"procedure": procedure, "window": [0, 1, 0, 1, 0, 1]},
    }


def _build_memory(writer: str = "v1") -> dict[str, Any]:
    """A compile-shaped memory: 3 studies x 6 object cases, then their configurations."""
    procedure = TERRITORY_PROCEDURE if writer == "territory" else V1_PROCEDURE
    spec = LayoutSpec(
        "fixture-layout-v1",
        "fixture-carrier-v1",
        (
            BankSpec(
                "fixture/signal",
                "signal",
                (MetricSpec("level", MetricKind.WORDS, ("low", "mid", "high")),),
            ),
        ),
    )
    compiled = compile_layout(spec)
    assert compiled is not None
    layout = {
        "version": spec.version,
        "carrier_id": spec.carrier_id,
        "fingerprint": compiled.fingerprint,
        "banks": [
            {
                "name": bank.name,
                "facet": bank.facet,
                "metrics": [
                    {
                        "name": metric.name,
                        "kind": metric.kind.value,
                        "words": list(metric.words),
                    }
                    for metric in bank.metrics
                ],
            }
            for bank in spec.banks
        ],
    }
    reference_id = "reference-set-a"
    roles = _question_object_roles()
    contexts, payloads = _portable_tables()
    cases: list[dict[str, Any]] = []
    ledger: dict[str, dict[str, int | None]] = {}
    sources: dict[str, dict[str, Any]] = {}
    for study_index, (uid, given) in enumerate(STUDIES.items()):
        labels: dict[str, int | None] = {question: None for question in LABELS}
        labels.update(given)
        ledger[uid] = labels
        records = {
            subject: {
                "count_layout_id": f"{spec.version}:{compiled.fingerprint}:{reference_id}",
                "reference_set_identity": reference_id,
                "sparse_counts": [
                    ["fixture/signal", 0, 3 + index],
                    ["fixture/signal", 2, 1],
                ],
                "status": "valid",
                "preparation_status": "prepared",
                "assembly": {"code": "assembled", "batches": []},
            }
            for index, subject in enumerate(SUBJECTS)
        }
        manifest = {
            "study_uid": uid,
            "mode": "full",
            "product_storage": "h5",
            "spec": {"version": "fixture-spec-v1"},
            "spec_sha256": "a" * 64,
            "object_composition": {
                "schema": "knee_object_profiles/v1",
                "objects": records,
                "layout_fingerprint": compiled.fingerprint,
                "carrier_identity": spec.carrier_id,
                "registry_fingerprint": "registry-fingerprint-a",
                "layout": layout,
            },
        }
        context_ref, context = _intern_full_context(manifest, contexts["contexts"])
        composition = manifest["object_composition"]
        sources[uid] = {
            "product_path": f"/products/{uid}.h5",
            "product_sha256": "a" * 64,
            "layout_fingerprint": composition["layout_fingerprint"],
            "carrier_identity": composition["carrier_identity"],
            "source_roots": {},
            "full_profile_subjects": sorted(records),
        }
        for subject_index, subject in enumerate(SUBJECTS):
            record = records[subject]
            calls, scopes = _condition_calls(subject, labels)
            payload_ref, record_sha = _retain_full_record(
                context_ref, context, subject, record, payloads["payloads"]
            )
            case: dict[str, Any] = {
                "case_id": f"squint-case:{uid}:{subject}",
                "study_uid": uid,
                "subject": subject,
                "condition_calls": calls,
                "presentation_scope": scopes
                or {
                    "kind": "structural_context",
                    "label_scope": "condition_not_asked_or_unlabeled",
                },
                "question_roles": roles[subject],
                "label_attribution": {
                    question: {
                        "source": "train.csv",
                        "source_path": "/raw/train.csv",
                        "study_uid": uid,
                        "condition": question,
                    }
                    for question in calls
                },
                "profile": _profile(study_index, subject_index, subject, writer),
                "regions": [
                    {
                        "source_window": [0, 1, 0, 1, 0, 1],
                        "native_bounds_rc": [0, 1, 0, 1],
                        "orientation": "coronal",
                        "view": dict(VIEW),
                        "series_uid": f"series-{uid}",
                        "source_slice": 0,
                        "extent_source": "retained_object_support",
                    }
                ],
                "full_profile": {
                    "subject": subject,
                    "mode": "full",
                    "scope": f"object:{subject}",
                    "count_layout_id": record["count_layout_id"],
                    "reference_set_identity": reference_id,
                    "carrier_identity": composition["carrier_identity"],
                    "layout_fingerprint": composition["layout_fingerprint"],
                    "product_record_sha256": record_sha,
                    "availability": _sparse_count_availability(record),
                    "context_ref": context_ref,
                    "payload_ref": payload_ref,
                },
                "full_source": {
                    "product_path": sources[uid]["product_path"],
                    "product_sha256": sources[uid]["product_sha256"],
                    "study_uid": uid,
                    "source_roots": {},
                },
                "teaching_source": {
                    "kind": "official_train_csv_label",
                    "revision": "fixture-bootstrap",
                },
            }
            if writer == "territory":
                case["unprofiled_regions"] = []
            cases.append(case)
    memory: dict[str, Any] = {
        "schema": SCHEMA,
        "revision": "fixture-bootstrap+portable-full-profiles-v1",
        "procedure": {
            "id": "knee.squint-ternary/v1",
            "tile_mm": 10.0,
            "mode_pair": ["full", "squint"],
        },
        "questions": list(LABELS),
        "object_conditions": {},
        "object_question_roles": roles,
        "source_identities": sources,
        "full_profile_contexts": contexts,
        "full_profile_payloads": payloads,
        "label_ledger": ledger,
        "cases": cases,
    }
    if writer == "territory":
        memory["procedure"].update(
            writer="territory-v2", profile_procedure=TERRITORY_PROCEDURE
        )
        memory["territory_writer"] = {
            "schema": "knee.squint-territory-writer/v1",
            "counts": {"studies": len(STUDIES), "object_cases": len(cases)},
        }
    memory = with_configuration_cases(memory, procedure=procedure)
    _link_configuration_full_profiles(memory)
    memory["full_profile_retention"] = _full_profile_retention_receipt(memory)
    return memory


def _publish_parent(directory: Path, memory: dict[str, Any]) -> str:
    prepared = prepare_recall(memory)
    assert prepared["outcome"] == "prepared"
    return save_memory(memory, directory, prepared_recall=prepared)["sha256"]


@pytest.fixture(scope="module")
def parent(tmp_path_factory: pytest.TempPathFactory) -> SimpleNamespace:
    memory = _build_memory("v1")
    path = tmp_path_factory.mktemp("parent") / "memory"
    return SimpleNamespace(path=path, sha=_publish_parent(path, memory), memory=memory)


@pytest.fixture(scope="module")
def territory_parent(tmp_path_factory: pytest.TempPathFactory) -> SimpleNamespace:
    memory = _build_memory("territory")
    path = tmp_path_factory.mktemp("territory-parent") / "memory"
    return SimpleNamespace(path=path, sha=_publish_parent(path, memory), memory=memory)


def _variant_parent(tmp_path: Path, memory: dict[str, Any]) -> SimpleNamespace:
    """A deliberately odd parent, published without a preparation (curation ignores it)."""
    path = tmp_path / "variant-parent"
    return SimpleNamespace(
        path=path, sha=save_memory(memory, path)["sha256"], memory=memory
    )


# ------------------------------------------------------------------------ test helpers


def _fingerprint(case: dict[str, Any]) -> str:
    """The specified fingerprint, derived here and not through the command under test."""
    text = json.dumps(
        case["profile"], sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _case(memory: dict[str, Any], case_id: str) -> dict[str, Any]:
    return next(case for case in memory["cases"] if case["case_id"] == case_id)


def _ids(memory: dict[str, Any]) -> list[str]:
    return [case["case_id"] for case in memory["cases"]]


def _decision(memory: dict[str, Any], case_id: str, **overrides: Any) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "expected_profile_fingerprint": _fingerprint(_case(memory, case_id)),
        "disposition": "retire_whole_case",
        "evidence": f"fixture inspection of {case_id}",
        "reason": "pending-view-adjudication",
        "reviewer": "fixture-reviewer",
        **overrides,
    }


def _document(*decisions: dict[str, Any]) -> bytes:
    return json.dumps(
        {"schema": curation.DECISIONS_SCHEMA, "decisions": list(decisions)}
    ).encode("utf-8")


def _curate(
    parent: SimpleNamespace, *decisions: dict[str, Any], pin: str | None = None
):
    snapshot = load_memory_snapshot(parent.path)
    parsed = curation.parse_decisions(_document(*decisions))
    child = curation.curate_memory(
        snapshot, parsed, expected_manifest_sha256=pin or parent.sha
    )
    return snapshot, child


def _tree(path: Path) -> dict[str, bytes]:
    return {
        str(item.relative_to(path)): item.read_bytes()
        for item in sorted(path.rglob("*"))
        if item.is_file()
    }


def _published(path: Path) -> SimpleNamespace:
    """A published memory through the public loader: its dict and its manifest digest."""
    snapshot = load_memory_snapshot(path)
    assert snapshot.memory is not None
    return SimpleNamespace(memory=snapshot.memory, sha256=snapshot.sha256)


def _configurations(memory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        case["case_id"]: case
        for case in memory["cases"]
        if case["case_id"].startswith("squint-configuration:")
    }


def _main(capsys: pytest.CaptureFixture[str], *argv: object) -> tuple[int, str, str]:
    code = curation.main([str(item) for item in argv])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _curate_argv(
    parent: SimpleNamespace, decisions: Path, output: Path
) -> list[object]:
    return [
        "curate",
        "--memory",
        parent.path,
        "--expected-manifest-sha256",
        parent.sha,
        "--decisions",
        decisions,
        "--output-memory",
        output,
    ]


# ------------------------------------------------------------- the fingerprint and file


def test_fingerprint_is_the_digest_of_the_case_profile_alone(parent) -> None:
    case = copy.deepcopy(parent.memory["cases"][0])
    fingerprint = curation.case_profile_fingerprint(case)
    assert fingerprint == _fingerprint(case)
    elsewhere = copy.deepcopy(case)
    elsewhere["regions"] = []
    elsewhere["condition_calls"] = {}
    assert curation.case_profile_fingerprint(elsewhere) == fingerprint
    changed = copy.deepcopy(case)
    first = next(iter(changed["profile"]["banks"]))
    changed["profile"]["banks"][first][0] += 1
    assert curation.case_profile_fingerprint(changed) != fingerprint


def _valid(**overrides: Any) -> dict[str, Any]:
    return {
        "case_id": "squint-case:study-a:femur",
        "expected_profile_fingerprint": "0" * 64,
        "disposition": "retire_whole_case",
        "evidence": "looked at the sagittal and coronal pictures",
        "reason": "pending-view-adjudication",
        "reviewer": "root",
        **overrides,
    }


def test_a_well_formed_decision_file_parses_to_a_sorted_set_with_stable_digests() -> (
    None
):
    first = _valid(case_id="squint-case:study-b:tibia")
    second = _valid()
    raw = _document(first, second)
    parsed = curation.parse_decisions(raw)
    assert [row["case_id"] for row in parsed["records"]] == [
        "squint-case:study-a:femur",
        "squint-case:study-b:tibia",
    ]
    assert parsed["records"][0] == second
    assert parsed["file_sha256"] == hashlib.sha256(raw).hexdigest()
    canonical = json.dumps(
        parsed["records"], sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    assert parsed["set_sha256"] == hashlib.sha256(canonical.encode()).hexdigest()
    # The set is the decisions, not their order or layout in the file.
    reordered = curation.parse_decisions(_document(second, first))
    assert reordered["set_sha256"] == parsed["set_sha256"]
    assert reordered["file_sha256"] != parsed["file_sha256"]
    # "No decisions" is a valid, explicit input.
    assert curation.parse_decisions(_document())["records"] == []


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        (b"{", "decisions_json_invalid"),
        (b"\xff\xfe", "decisions_json_invalid"),
        (b"[]", "decisions_document_invalid"),
        (
            b'{"schema": "a", "schema": "b", "decisions": []}',
            "decisions_json_duplicate_key",
        ),
        (
            (
                b'{"schema": "knee.squint-memory-curation-decisions/v1", "decisions": '
                b'[{"case_id": "x", "case_id": "y"}]}'
            ),
            "decisions_json_duplicate_key",
        ),
    ],
)
def test_undecodable_or_ambiguous_decision_bytes_are_refused(
    raw: bytes, code: str
) -> None:
    with pytest.raises(curation.CurationError) as error:
        curation.parse_decisions(raw)
    assert error.value.code == code


@pytest.mark.parametrize(
    ("change", "code"),
    [
        (lambda d: d.update(schema="other/v1"), "decisions_schema_invalid"),
        (lambda d: d.pop("schema"), "decisions_document_invalid"),
        (lambda d: d.update(note="free text"), "decisions_document_invalid"),
        (lambda d: d.update(decisions={}), "decisions_list_invalid"),
        (lambda d: d["decisions"].append("femur"), "decision_invalid"),
        (lambda d: d["decisions"][0].pop("reviewer"), "decision_keys_invalid"),
        (lambda d: d["decisions"][0].update(prediction=1), "decision_keys_invalid"),
        (lambda d: d["decisions"][0].update(case_id=""), "decision_case_id_invalid"),
        (lambda d: d["decisions"][0].update(case_id=7), "decision_case_id_invalid"),
        (
            lambda d: d["decisions"][0].update(expected_profile_fingerprint="abc"),
            "decision_fingerprint_invalid",
        ),
        (
            lambda d: d["decisions"][0].update(expected_profile_fingerprint="A" * 64),
            "decision_fingerprint_invalid",
        ),
        (
            lambda d: d["decisions"][0].update(disposition="retire_view"),
            "decision_disposition_unknown",
        ),
        (lambda d: d["decisions"][0].update(evidence=""), "decision_evidence_invalid"),
        (lambda d: d["decisions"][0].update(reason="   "), "decision_reason_invalid"),
        (
            lambda d: d["decisions"][0].update(reviewer=None),
            "decision_reviewer_invalid",
        ),
        (
            lambda d: d["decisions"].append(copy.deepcopy(d["decisions"][0])),
            "decision_case_duplicate",
        ),
        (
            lambda d: d["decisions"].append({**d["decisions"][0], "reason": "other"}),
            "decision_case_duplicate",
        ),
    ],
)
def test_malformed_or_conflicting_decisions_are_refused_by_name(
    change, code: str
) -> None:
    document = {"schema": curation.DECISIONS_SCHEMA, "decisions": [_valid()]}
    change(document)
    with pytest.raises(curation.CurationError) as error:
        curation.parse_decisions(json.dumps(document).encode("utf-8"))
    assert error.value.code == code


# ------------------------------------------------------------ the default: no decisions


def test_no_decisions_keeps_every_case_and_field_but_takes_a_new_revision(
    parent,
) -> None:
    snapshot, child = _curate(parent)
    assert child["cases"] == snapshot.memory["cases"]
    for key, value in snapshot.memory.items():
        # save_memory alone fills the receipt's publication-time readback fields.
        if key not in ("revision", "cases", "full_profile_retention"):
            assert child[key] == value
    counts = ("context_count", "payload_count", "case_payload_links")
    assert {k: child["full_profile_retention"][k] for k in counts} == {
        k: snapshot.memory["full_profile_retention"][k] for k in counts
    }
    assert child["revision"] != snapshot.memory["revision"]
    assert child["revision"].startswith(snapshot.memory["revision"] + "+")
    record = child["curation"]
    assert record["schema"] == curation.CURATION_SCHEMA
    assert record["retired_cases"] == []
    assert record["counts"]["retired_object_cases"] == 0
    assert record["configuration_cases"]["rebuilt_case_ids"] == []


def test_no_decisions_publishes_a_fresh_identity_and_equal_decoded_profiles(
    parent, tmp_path: Path
) -> None:
    snapshot, child = _curate(parent)
    output = tmp_path / "child"
    receipt = curation.publish_curated_memory(child, output, parent=snapshot)
    published = _published(output)
    assert published.sha256 == receipt["child"]["manifest_sha256"] != parent.sha
    assert published.memory["revision"] == child["revision"]
    assert [c["case_id"] for c in published.memory["cases"]] == _ids(snapshot.memory)
    # Nothing retired: the published readback verified every payload the parent had.
    assert (
        published.memory["full_profile_retention"]
        == (snapshot.memory["full_profile_retention"])
    )
    decoded = 0
    for case in snapshot.memory["cases"]:
        if case["subject"].startswith("diagnosis/"):
            continue
        before = full_profile_from_case(snapshot.memory, case)
        after = full_profile_from_case(published.memory, case)
        assert after.bundle == before.bundle
        assert after.source_id == before.source_id
        decoded += 1
    assert decoded == len(STUDIES) * len(SUBJECTS)


# ----------------------------------------------------------------- retiring a case


def test_a_retired_case_leaves_recall_and_every_other_case_is_untouched(
    parent, tmp_path: Path
) -> None:
    snapshot, child = _curate(parent, _decision(parent.memory, FEMUR_A))
    retired = _case(snapshot.memory, FEMUR_A)
    assert FEMUR_A not in _ids(child)
    assert _ids(child) == [item for item in _ids(snapshot.memory) if item != FEMUR_A]
    assert all(
        case == _case(snapshot.memory, case["case_id"])
        for case in child["cases"]
        if not case["case_id"].startswith("squint-configuration:")
    )
    # The whole original case and its decision are kept, verbatim, in the child.
    (kept,) = child["curation"]["retired_cases"]
    assert kept["case"] == retired
    assert kept["decision"] == _decision(snapshot.memory, FEMUR_A)
    assert child["full_profile_payloads"] == snapshot.memory["full_profile_payloads"]
    assert child["full_profile_contexts"] == snapshot.memory["full_profile_contexts"]
    assert child["source_identities"] == snapshot.memory["source_identities"]
    assert child["label_ledger"] == snapshot.memory["label_ledger"]

    output = tmp_path / "child"
    curation.publish_curated_memory(child, output, parent=snapshot)
    published = _published(output)
    cache = load_json(output / "recall-preparation.json")
    query = copy.deepcopy(retired["profile"])
    before = recall_object(
        query,
        {**snapshot.memory, "prepared_recall": prepare_recall(snapshot.memory)},
        "ACL",
    )
    after = recall_object(
        query,
        {
            **published.memory,
            "prepared_recall": prepare_recall(published.memory, cached=cache),
        },
        "ACL",
    )
    before_ids = {row["case_id"] for row in before["case_terms"]}
    after_ids = {row["case_id"] for row in after["case_terms"]}
    assert FEMUR_A in before_ids
    assert FEMUR_A not in after_ids
    assert after_ids == before_ids - {FEMUR_A}


def test_a_study_with_every_object_case_retired_still_publishes(
    parent, tmp_path: Path
) -> None:
    decisions = [
        _decision(parent.memory, f"squint-case:study-a:{subject}")
        for subject in SUBJECTS
    ]
    snapshot, child = _curate(parent, *decisions)
    for case_id in (
        "squint-configuration:study-a:ACL",
        "squint-configuration:study-a:MCL",
    ):
        rebuilt = _configurations(child)[case_id]
        assert rebuilt["profile"]["banks"] == {}
        assert rebuilt["profile"]["source"]["roles"] == {}
        assert (
            rebuilt["condition_calls"]
            == _configurations(snapshot.memory)[case_id]["condition_calls"]
        )
    curation.publish_curated_memory(child, tmp_path / "child", parent=snapshot)
    assert len(_published(tmp_path / "child").memory["cases"]) == len(
        snapshot.memory["cases"]
    ) - len(SUBJECTS)


# ------------------------------------------------- configurations rebuilt, not copied


def test_configurations_naming_the_retired_role_are_rebuilt_without_its_banks(
    parent,
) -> None:
    snapshot, child = _curate(parent, _decision(parent.memory, FEMUR_A))
    before, after = _configurations(snapshot.memory), _configurations(child)
    assert set(after) == set(before)
    rebuilt = sorted(
        f"squint-configuration:study-a:{question}" for question in ("ACL", "MCL")
    )
    assert child["curation"]["configuration_cases"]["rebuilt_case_ids"] == rebuilt
    for case_id in rebuilt:
        old, new = before[case_id], after[case_id]
        assert any(bank.startswith("object/femur/") for bank in old["profile"]["banks"])
        assert new["profile"]["banks"] == {
            bank: counts
            for bank, counts in old["profile"]["banks"].items()
            if not bank.startswith("object/femur/")
        }
        assert "femur" not in new["profile"]["source"]["roles"]
        assert {"subject": "femur", "status": "missing_object_case"} in new["profile"][
            "source"
        ]["missing_roles"]
        assert "femur" not in new["full_profiles"]
        assert "femur" not in new.get("full_profile_refs", {})
        assert new["condition_calls"] == old["condition_calls"]
        assert new["label_attribution"] == old["label_attribution"]
        assert new["profile"]["source"]["procedure"] == V1_PROCEDURE
    for case_id, case in before.items():
        if case_id not in rebuilt:
            assert after[case_id] == case


def test_a_configuration_that_never_named_the_retired_role_is_carried_over_unchanged(
    parent,
) -> None:
    # The acl object is a role of the ACL configuration only, not of the MCL one.
    snapshot, child = _curate(parent, _decision(parent.memory, ACL_A))
    before, after = _configurations(snapshot.memory), _configurations(child)
    assert (
        after["squint-configuration:study-a:MCL"]
        == before["squint-configuration:study-a:MCL"]
    )
    assert (
        after["squint-configuration:study-a:ACL"]
        != before["squint-configuration:study-a:ACL"]
    )
    assert child["curation"]["configuration_cases"]["rebuilt_case_ids"] == [
        "squint-configuration:study-a:ACL"
    ]
    assert child["curation"]["counts"]["configuration_cases_rebuilt"] == 1
    assert child["curation"]["counts"]["configuration_cases_carried_over"] == 5


def test_a_carried_over_configuration_that_differs_from_the_canonical_rebuild_is_kept_and_named(
    tmp_path: Path,
) -> None:
    memory = _build_memory("v1")
    drifted = "squint-configuration:study-b:MCL"
    _case(memory, drifted)["presentation_scope"] = {"MCL": "altered_by_an_older_build"}
    variant = _variant_parent(tmp_path, memory)
    snapshot, child = _curate(variant, _decision(memory, FEMUR_A))
    assert _case(child, drifted) == _case(snapshot.memory, drifted)
    assert child["curation"]["configuration_cases"][
        "carried_over_differs_from_canonical_rebuild"
    ] == [drifted]


def test_an_affected_configuration_the_canonical_rebuild_cannot_write_is_refused(
    tmp_path: Path,
) -> None:
    memory = _build_memory("v1")
    memory["label_ledger"]["study-a"]["ACL"] = None
    variant = _variant_parent(tmp_path, memory)
    with pytest.raises(curation.CurationError) as error:
        _curate(variant, _decision(memory, ACL_A))
    assert error.value.code == "affected_configuration_not_rebuilt"
    assert error.value.detail == ["squint-configuration:study-a:ACL"]


def test_the_rebuild_keeps_the_parents_own_writer_and_never_relabels_it(
    territory_parent, tmp_path: Path
) -> None:
    snapshot, child = _curate(
        territory_parent, _decision(territory_parent.memory, FEMUR_A)
    )
    rebuilt = child["curation"]["configuration_cases"]["rebuilt_case_ids"]
    assert rebuilt
    assert (
        child["curation"]["configuration_cases"]["profile_procedure"]
        == TERRITORY_PROCEDURE
    )
    for case_id in rebuilt:
        assert (
            _case(child, case_id)["profile"]["source"]["procedure"]
            == TERRITORY_PROCEDURE
        )
    assert child["territory_writer"] == snapshot.memory["territory_writer"]
    assert child["procedure"] == snapshot.memory["procedure"]
    curation.publish_curated_memory(child, tmp_path / "child", parent=snapshot)
    assert _published(tmp_path / "child").memory["revision"] == child["revision"]


def test_object_profiles_from_two_writers_are_refused(tmp_path: Path) -> None:
    memory = _build_memory("v1")
    _case(memory, "squint-case:study-c:tibia")["profile"]["source"]["procedure"] = (
        TERRITORY_PROCEDURE
    )
    variant = _variant_parent(tmp_path, memory)
    with pytest.raises(curation.CurationError) as error:
        _curate(variant, _decision(memory, FEMUR_A))
    assert error.value.code == "parent_profile_procedure_not_single"


def test_a_noncanonical_configuration_with_retired_role_banks_is_refused_by_name(
    tmp_path: Path,
) -> None:
    memory = _build_memory("v1")
    odd = []
    for case_id, subject in (
        ("squint-configuration:study-a:Unlisted", "diagnosis/Unlisted"),
        ("squint-configuration:study-a:Odd", "odd"),
    ):
        extra = copy.deepcopy(_case(memory, "squint-configuration:study-a:ACL"))
        extra.update(case_id=case_id, subject=subject, condition_calls={})
        memory["cases"].append(extra)
        odd.append(case_id)
    variant = _variant_parent(tmp_path, memory)
    with pytest.raises(curation.CurationError) as error:
        _curate(variant, _decision(memory, FEMUR_A))
    assert error.value.code == "retired_object_banks_remain"
    assert error.value.detail in odd


def test_a_noncanonical_configuration_without_retired_roles_is_carried_over_and_named(
    tmp_path: Path,
) -> None:
    memory = _build_memory("v1")
    odd = []
    for case_id, subject in (
        ("squint-configuration:study-a:Unlisted", "diagnosis/Unlisted"),
        ("squint-configuration:study-a:Odd", "odd"),
    ):
        extra = copy.deepcopy(_case(memory, "squint-configuration:study-a:ACL"))
        extra.update(case_id=case_id, subject=subject, condition_calls={})
        profile = extra["profile"]
        profile["banks"] = {
            name: counts
            for name, counts in profile["banks"].items()
            if not name.startswith("object/femur/")
        }
        profile["source"]["roles"].pop("femur", None)
        memory["cases"].append(extra)
        odd.append(case_id)
    variant = _variant_parent(tmp_path, memory)
    snapshot, child = _curate(variant, _decision(memory, FEMUR_A))
    for case_id in odd:
        assert _case(child, case_id) == _case(snapshot.memory, case_id)
    drift = child["curation"]["configuration_cases"][
        "carried_over_differs_from_canonical_rebuild"
    ]
    assert sorted(drift) == sorted(odd)


def test_a_rebuild_the_library_itself_refuses_is_refused_by_name(
    tmp_path: Path,
) -> None:
    memory = _build_memory("v1")
    del memory["label_ledger"]
    variant = _variant_parent(tmp_path, memory)
    with pytest.raises(curation.CurationError) as error:
        _curate(variant, _decision(memory, FEMUR_A))
    assert (
        error.value.code
        == "configuration_rebuild_refused:memory_cases_or_label_ledger_invalid"
    )


def test_a_memory_with_no_portable_tables_and_its_own_case_ids_curates_and_publishes(
    tmp_path: Path,
) -> None:
    def case(uid: str, subject: str, value: int) -> dict[str, Any]:
        return {
            "case_id": f"object-case:{uid}:{subject}",
            "study_uid": uid,
            "subject": subject,
            "condition_calls": {},
            "regions": [],
            "profile": {
                "schema": "knee.squint-profile/v1",
                "subject": subject,
                "banks": {"view/signal_median/overview/10mm": [value, 2, 3]},
                "source": {"procedure": V1_PROCEDURE},
            },
        }

    labels: dict[str, int | None] = {question: None for question in LABELS}
    labels.update({"ACL": 1, "MCL": 0})
    memory = with_configuration_cases(
        {
            "schema": SCHEMA,
            "revision": "plain-r1",
            "questions": list(LABELS),
            "label_ledger": {"study-a": labels},
            "source_identities": {},
            "cases": [
                case("study-a", "acl", 7),
                case("study-a", "femur", 11),
                case("study-a", "tibia", 13),
                case("study-b", "femur", 19),
            ],
        }
    )
    variant = _variant_parent(tmp_path, memory)
    retired = "object-case:study-a:femur"
    snapshot, child = _curate(variant, _decision(memory, retired))
    assert retired not in _ids(child)
    assert "full_profile_retention" not in child
    assert child["curation"]["counts"]["full_profile_payloads"]["in_tables"] == 0
    rebuilt = _configurations(child)["squint-configuration:study-a:ACL"]
    assert "femur" not in rebuilt["profile"]["source"]["roles"]
    assert (
        "object/femur/view/signal_median/overview/10mm"
        not in rebuilt["profile"]["banks"]
    )
    curation.publish_curated_memory(child, tmp_path / "child", parent=snapshot)
    assert _published(tmp_path / "child").memory["revision"] == child["revision"]


# --------------------------------------------------------- the pinned, explicit input


@pytest.mark.parametrize(
    ("pin", "overrides", "code"),
    [
        ("stale", {}, "parent_manifest_sha256_mismatch"),
        ("malformed", {}, "expected_manifest_sha256_invalid"),
        ("good", {"case_id": "squint-case:study-z:femur"}, "decision_case_unknown"),
        (
            "good",
            {"expected_profile_fingerprint": "f" * 64},
            "decision_profile_fingerprint_mismatch",
        ),
        (
            "good",
            {"case_id": "squint-configuration:study-a:ACL"},
            "decision_case_is_derived_configuration",
        ),
    ],
)
def test_unpinned_or_unknown_input_publishes_nothing_and_leaves_the_parent_alone(
    parent, tmp_path: Path, capsys, pin: str, overrides: dict[str, Any], code: str
) -> None:
    base = (
        "squint-configuration:study-a:ACL"
        if overrides.get("case_id", "").startswith("squint-configuration:")
        else FEMUR_A
    )
    decisions = tmp_path / "decisions.json"
    decisions.write_bytes(_document({**_decision(parent.memory, base), **overrides}))
    work = tmp_path / "work"
    work.mkdir()
    before = _tree(parent.path)
    argv = _curate_argv(parent, decisions, work / "child")
    argv[argv.index("--expected-manifest-sha256") + 1] = {
        "stale": "0" * 64,
        "malformed": "not-a-digest",
        "good": parent.sha,
    }[pin]
    exit_code, out, err = _main(capsys, *argv)
    assert exit_code == 2
    assert out == ""
    assert json.loads(err)["code"] == code
    assert list(work.iterdir()) == []
    assert _tree(parent.path) == before


def test_a_matching_pin_and_fingerprint_are_what_let_a_retirement_through(
    parent, tmp_path: Path, capsys
) -> None:
    decisions = tmp_path / "decisions.json"
    decisions.write_bytes(_document(_decision(parent.memory, FEMUR_A)))
    output = tmp_path / "child"
    exit_code, out, err = _main(capsys, *_curate_argv(parent, decisions, output))
    assert (exit_code, err) == (0, "")
    assert json.loads(out)["outcome"] == "published"
    assert (output / "manifest.json").is_file()


def test_a_curated_memory_cannot_be_curated_again(parent, tmp_path: Path) -> None:
    snapshot, child = _curate(parent, _decision(parent.memory, FEMUR_A))
    first = tmp_path / "first"
    curation.publish_curated_memory(child, first, parent=snapshot)
    published = SimpleNamespace(
        path=first, sha=load_memory_snapshot(first).sha256, memory=child
    )
    with pytest.raises(curation.CurationError) as error:
        _curate(published)
    assert error.value.code == "parent_already_curated"


def test_a_parent_that_embeds_a_recall_preparation_is_refused(tmp_path: Path) -> None:
    memory = _build_memory("v1")
    memory["prepared_recall"] = {
        "schema": "knee.squint-recall-preparation/v1",
        "outcome": "prepared",
        "source_fingerprint": "a" * 64,
    }
    variant = _variant_parent(tmp_path, memory)
    with pytest.raises(curation.CurationError) as error:
        _curate(variant)
    assert error.value.code == "parent_embeds_recall_preparation"


def test_a_snapshot_that_is_not_a_squint_memory_is_refused_by_the_loaders_own_code(
    parent,
) -> None:
    broken = dataclasses.replace(
        load_memory_snapshot(parent.path),
        status="invalid",
        memory=None,
        error_code="memory_manifest_invalid",
    )
    parsed = curation.parse_decisions(_document())
    with pytest.raises(curation.CurationError) as error:
        curation.curate_memory(broken, parsed, expected_manifest_sha256=parent.sha)
    assert error.value.code == "memory_manifest_invalid"


def test_curation_is_a_pure_function_of_the_snapshot_and_decisions(parent) -> None:
    snapshot = load_memory_snapshot(parent.path)
    before = copy.deepcopy(snapshot.memory)
    parsed = curation.parse_decisions(_document(_decision(parent.memory, FEMUR_A)))
    first = curation.curate_memory(
        snapshot, parsed, expected_manifest_sha256=parent.sha
    )
    second = curation.curate_memory(
        snapshot, parsed, expected_manifest_sha256=parent.sha
    )
    assert snapshot.memory == before
    assert _canonical(first) == _canonical(second)


def test_a_decision_asserts_nothing_about_other_views_and_keeps_its_reason(
    parent,
) -> None:
    _, child = _curate(parent, _decision(parent.memory, FEMUR_A))
    record = child["curation"]
    assert record["semantics"]["retired_case_scope"] == "whole_case"
    assert record["semantics"]["other_view_facets_asserted_false"] is False
    assert (
        record["retired_cases"][0]["decision"]["reason"] == "pending-view-adjudication"
    )
    retired_regions = record["retired_cases"][0]["case"]["regions"]
    assert retired_regions == _case(parent.memory, FEMUR_A)["regions"]


# ------------------------------------------------------------ the independent check


def _doctor_child(parent, change) -> tuple[dict[str, Any], dict[str, Any]]:
    snapshot, child = _curate(parent, _decision(parent.memory, FEMUR_A))
    child = copy.deepcopy(child)
    change(child, snapshot.memory)
    return snapshot.memory, child


def _first_rebuilt(child: dict[str, Any]) -> dict[str, Any]:
    return _case(child, child["curation"]["configuration_cases"]["rebuilt_case_ids"][0])


@pytest.mark.parametrize(
    ("change", "code"),
    [
        (
            lambda child, parent: child["cases"].append(_case(parent, FEMUR_A)),
            "child_case_set_differs",
        ),
        (lambda child, parent: child["cases"].pop(0), "child_case_set_differs"),
        (
            lambda child, parent: child["cases"][0]["profile"]["banks"].clear(),
            "child_object_case_changed",
        ),
        (
            lambda child, parent: child["label_ledger"]["study-a"].update(ACL=None),
            "child_fields_changed",
        ),
        (
            lambda child, parent: child["full_profile_payloads"]["payloads"].clear(),
            "child_fields_changed",
        ),
        (
            lambda child, parent: child["curation"]["retired_cases"][0]["case"][
                "profile"
            ]["banks"].clear(),
            "retired_case_not_verbatim",
        ),
        (
            lambda child, parent: _first_rebuilt(child)["profile"]["banks"].update(
                {"object/femur/squint/v1/leftover": [1, 2, 3]}
            ),
            "retired_object_banks_remain",
        ),
        (
            lambda child, parent: _first_rebuilt(child)["profile"]["banks"].pop(
                next(iter(_first_rebuilt(child)["profile"]["banks"]))
            ),
            "rebuilt_configuration_differs",
        ),
        (
            lambda child, parent: _first_rebuilt(child).update(condition_calls={}),
            "rebuilt_configuration_differs",
        ),
    ],
)
def test_the_verifier_refuses_a_child_that_dropped_changed_or_kept_what_it_should_not(
    parent, change, code: str
) -> None:
    original, child = _doctor_child(parent, change)
    with pytest.raises(curation.CurationError) as error:
        curation.verify_curation(original, child)
    assert error.value.code == code


def test_the_verifier_accepts_the_child_the_builder_made(parent) -> None:
    original, child = _doctor_child(parent, lambda child, parent: None)
    curation.verify_curation(original, child)


# ---------------------------------------------- publication, readback and identity


def test_the_published_child_reads_back_publicly_with_its_own_preparation(
    parent, tmp_path: Path
) -> None:
    snapshot, child = _curate(parent, _decision(parent.memory, FEMUR_A))
    output = tmp_path / "child"
    receipt = curation.publish_curated_memory(child, output, parent=snapshot)
    published = _published(output)
    cache = load_json(output / "recall-preparation.json")
    assert receipt["schema"] == curation.RECEIPT_SCHEMA
    assert receipt["outcome"] == "published"
    assert receipt["child"]["manifest"] == str(output.resolve() / "manifest.json")
    assert receipt["child"]["manifest_sha256"] == published.sha256
    assert receipt["readback"]["manifest_sha256"] == published.sha256
    assert cache["memory_manifest_sha256"] == published.sha256
    assert cache["memory_revision"] == published.memory["revision"] == child["revision"]
    fingerprint = recall_source_fingerprint(published.memory)
    assert cache["source_fingerprint"] == fingerprint
    assert receipt["child"]["recall_source_fingerprint"] == fingerprint
    assert child["curation"]["child_recall_source_fingerprint"] == fingerprint
    assert fingerprint != recall_source_fingerprint(snapshot.memory)
    assert receipt["parent"]["manifest_sha256"] == parent.sha
    assert receipt["parent"]["recall_source_fingerprint"] == recall_source_fingerprint(
        snapshot.memory
    )
    # The sidecar is accepted by the public restore path production uses.
    assert (
        prepare_recall(published.memory, cached=cache)["runtime_indexes_rebuilt"]
        is True
    )
    # The parent's own preparation is not the child's: it is not accepted for it.
    parent_cache = load_json(parent.path / "recall-preparation.json")
    reused = prepare_recall(published.memory, cached=parent_cache)
    assert reused.get("runtime_indexes_rebuilt") is not True
    assert reused["cache_status"] == "rebuilt_incompatible_cache"
    assert sorted(path.name for path in output.iterdir()) == [
        "manifest.json",
        "recall-preparation.json.xz",
    ]


def test_an_unchanged_population_still_gets_a_new_preparation_identity(
    parent, tmp_path: Path
) -> None:
    snapshot, child = _curate(parent)
    output = tmp_path / "child"
    curation.publish_curated_memory(child, output, parent=snapshot)
    cache = load_json(output / "recall-preparation.json")
    parent_cache = load_json(parent.path / "recall-preparation.json")
    # The cases, calls and profiles are the same, so their fingerprint is too...
    assert cache["source_fingerprint"] == parent_cache["source_fingerprint"]
    # ...but the preparation belongs to the child's manifest and revision alone.
    assert cache["memory_manifest_sha256"] != parent_cache["memory_manifest_sha256"]
    assert cache["memory_revision"] != parent_cache["memory_revision"]
    assert (output / "recall-preparation.json.xz").read_bytes() != (
        parent.path / "recall-preparation.json.xz"
    ).read_bytes()


def test_publication_is_deterministic(parent, tmp_path: Path) -> None:
    decision = _decision(parent.memory, FEMUR_A)
    manifests = []
    for name in ("one", "two"):
        snapshot, child = _curate(parent, decision)
        curation.publish_curated_memory(child, tmp_path / name, parent=snapshot)
        manifests.append((tmp_path / name / "manifest.json").read_bytes())
    assert manifests[0] == manifests[1]


def test_the_territory_memory_publishes_and_is_accepted_by_its_selection_route(
    territory_parent, tmp_path: Path
) -> None:
    snapshot, child = _curate(
        territory_parent, _decision(territory_parent.memory, FEMUR_A)
    )
    output = tmp_path / "child"
    receipt = curation.publish_curated_memory(child, output, parent=snapshot)
    published = _published(output)
    cache = load_json(output / "recall-preparation.json")
    assert "selections" in cache["preparation"]
    assert (
        prepare_recall(published.memory, cached=cache)["runtime_indexes_rebuilt"]
        is True
    )
    assert receipt["child"]["recall_source_fingerprint"] == cache["source_fingerprint"]


def test_full_profile_tables_are_carried_whole_and_the_counts_say_what_is_kept_only_for_retirees(
    parent, tmp_path: Path
) -> None:
    snapshot, child = _curate(parent, _decision(parent.memory, FEMUR_A))
    counts = child["curation"]["counts"]
    assert counts["parent"] == {
        "cases": len(snapshot.memory["cases"]),
        "object_cases": len(STUDIES) * len(SUBJECTS),
        "configuration_cases": 6,
    }
    assert counts["child"] == {
        "cases": len(snapshot.memory["cases"]) - 1,
        "object_cases": len(STUDIES) * len(SUBJECTS) - 1,
        "configuration_cases": 6,
    }
    assert counts["retired_object_cases"] == 1
    tables = counts["full_profile_payloads"]
    assert tables["in_tables"] == len(STUDIES) * len(SUBJECTS)
    assert tables["case_links_parent"] > tables["case_links_child"]
    output = tmp_path / "child"
    curation.publish_curated_memory(child, output, parent=snapshot)
    stored = _published(output).memory["full_profile_retention"]
    assert stored["payload_count"] == tables["in_tables"]
    assert stored["case_payload_links"] == tables["case_links_child"]


# ------------------------------------------------------- no partial publication


def _failure_setup(parent, tmp_path: Path):
    snapshot, child = _curate(parent, _decision(parent.memory, FEMUR_A))
    work = tmp_path / "work"
    work.mkdir()
    return snapshot, child, work, _tree(parent.path)


@pytest.mark.parametrize("fault", ["unfinished", "another_population"])
def test_a_preparation_that_is_not_the_childs_publishes_nothing(
    parent, tmp_path: Path, monkeypatch, fault: str
) -> None:
    snapshot, child, work, before = _failure_setup(parent, tmp_path)
    real = curation.prepare_recall
    if fault == "unfinished":

        def faulty(memory, **kwargs):
            return {"outcome": "invalid_input", "reason": "injected"}

    else:

        def faulty(memory, **kwargs):
            return {**real(memory, **kwargs), "source_fingerprint": "0" * 64}

    monkeypatch.setattr(curation, "prepare_recall", faulty)
    with pytest.raises(curation.CurationError) as error:
        curation.publish_curated_memory(child, work / "child", parent=snapshot)
    assert error.value.code == "recall_preparation_failed"
    assert error.value.detail == (
        "injected" if fault == "unfinished" else "source_fingerprint"
    )
    assert list(work.iterdir()) == []
    assert _tree(parent.path) == before


def test_a_failure_after_the_save_removes_everything_it_staged(
    parent, tmp_path: Path, monkeypatch
) -> None:
    snapshot, child, work, before = _failure_setup(parent, tmp_path)
    real = curation.save_memory

    def save_then_fail(memory, path, **kwargs):
        real(memory, path, **kwargs)
        raise SquintMemoryError("injected_after_save")

    monkeypatch.setattr(curation, "save_memory", save_then_fail)
    with pytest.raises(SquintMemoryError, match="injected_after_save"):
        curation.publish_curated_memory(child, work / "child", parent=snapshot)
    assert list(work.iterdir()) == []
    assert _tree(parent.path) == before


@pytest.mark.parametrize("lie", ["manifest_sha256", "recall_cache"])
def test_a_readback_that_disagrees_publishes_nothing(
    parent, tmp_path: Path, monkeypatch, lie: str
) -> None:
    snapshot, child, work, before = _failure_setup(parent, tmp_path)
    if lie == "manifest_sha256":
        real_load = curation.load_memory_snapshot
        monkeypatch.setattr(
            curation,
            "load_memory_snapshot",
            lambda path: dataclasses.replace(real_load(path), sha256="0" * 64),
        )
    else:
        real_prepare = curation.prepare_recall

        def refuses_the_sidecar(memory, **kwargs):
            result = real_prepare(memory, **kwargs)
            if "cached" in kwargs:
                result = {
                    key: value
                    for key, value in result.items()
                    if key != "runtime_indexes_rebuilt"
                }
            return result

        monkeypatch.setattr(curation, "prepare_recall", refuses_the_sidecar)
    with pytest.raises(curation.CurationError) as error:
        curation.publish_curated_memory(child, work / "child", parent=snapshot)
    assert error.value.code == "publication_readback_mismatch"
    assert error.value.detail == lie
    assert list(work.iterdir()) == []
    assert _tree(parent.path) == before


def test_an_existing_output_is_refused_and_left_as_it_was(
    parent, tmp_path: Path
) -> None:
    snapshot, child = _curate(parent, _decision(parent.memory, FEMUR_A))
    output = tmp_path / "child"
    output.mkdir()
    (output / "keep.txt").write_text("not mine", encoding="utf-8")
    with pytest.raises(curation.CurationError) as error:
        curation.publish_curated_memory(child, output, parent=snapshot)
    assert error.value.code == "output_already_exists"
    assert _tree(output) == {"keep.txt": b"not mine"}


def test_an_output_inside_the_parent_directory_is_refused(parent) -> None:
    snapshot, child = _curate(parent, _decision(parent.memory, FEMUR_A))
    before = _tree(parent.path)
    with pytest.raises(curation.CurationError) as error:
        curation.publish_curated_memory(child, parent.path / "child", parent=snapshot)
    assert error.value.code == "output_overlaps_parent"
    assert sorted(path.name for path in parent.path.iterdir()) == [
        "manifest.json",
        "recall-preparation.json.xz",
    ]
    assert _tree(parent.path) == before


# --------------------------------------------------------------------- the command


def test_fingerprints_lists_identity_only_for_object_cases(parent, capsys) -> None:
    exit_code, out, err = _main(
        capsys,
        "fingerprints",
        "--memory",
        parent.path,
        "--expected-manifest-sha256",
        parent.sha,
    )
    assert (exit_code, err) == (0, "")
    listing = json.loads(out)
    assert listing["schema"] == curation.FINGERPRINTS_SCHEMA
    assert listing["manifest_sha256"] == parent.sha
    assert listing["revision"] == parent.memory["revision"]
    objects = [c for c in parent.memory["cases"] if c["subject"] in SUBJECTS]
    assert [row["case_id"] for row in listing["cases"]] == [
        c["case_id"] for c in objects
    ]
    for row, case in zip(listing["cases"], objects, strict=True):
        assert row == {
            "case_id": case["case_id"],
            "study_uid": case["study_uid"],
            "subject": case["subject"],
            "profile_fingerprint": _fingerprint(case),
        }


def test_fingerprints_can_name_cases_and_refuses_unknown_or_derived_ones(
    parent, capsys
) -> None:
    base = [
        "fingerprints",
        "--memory",
        parent.path,
        "--expected-manifest-sha256",
        parent.sha,
        "--case-id",
    ]
    exit_code, out, _ = _main(capsys, *base, FEMUR_A)
    assert exit_code == 0
    assert [row["case_id"] for row in json.loads(out)["cases"]] == [FEMUR_A]
    for bad, code in (
        ("squint-case:study-z:femur", "fingerprint_case_unknown"),
        (
            "squint-configuration:study-a:ACL",
            "fingerprint_case_is_derived_configuration",
        ),
    ):
        exit_code, out, err = _main(capsys, *base, FEMUR_A, bad)
        assert (exit_code, out) == (2, "")
        assert json.loads(err)["code"] == code
    exit_code, out, err = _main(
        capsys,
        "fingerprints",
        "--memory",
        parent.path,
        "--expected-manifest-sha256",
        "0" * 64,
    )
    assert (exit_code, json.loads(err)["code"]) == (
        2,
        "parent_manifest_sha256_mismatch",
    )


def test_the_command_prints_a_receipt_with_exact_counts_and_identities(
    parent, tmp_path: Path, capsys
) -> None:
    decisions = tmp_path / "decisions.json"
    raw = _document(_decision(parent.memory, FEMUR_A))
    decisions.write_bytes(raw)
    output = tmp_path / "child"
    exit_code, out, err = _main(capsys, *_curate_argv(parent, decisions, output))
    assert (exit_code, err) == (0, "")
    receipt = json.loads(out)
    published = _published(output)
    # The receipt names the knee package that actually ran, so a run can be audited.
    assert receipt["tool"] == {
        "script": "curate_squint_memory.py",
        "knee_package": str(Path(knee.__file__).resolve().parent),
    }
    assert receipt["parent"]["manifest_sha256"] == parent.sha
    assert receipt["decisions"] == {
        "file_sha256": hashlib.sha256(raw).hexdigest(),
        "set_sha256": published.memory["curation"]["decisions"]["set_sha256"],
        "count": 1,
    }
    assert receipt["child"]["manifest_sha256"] == published.sha256
    assert receipt["child"]["revision"] == published.memory["revision"]
    assert receipt["retired_case_ids"] == [FEMUR_A]
    assert receipt["counts"] == published.memory["curation"]["counts"]
    assert receipt["counts"]["retired_object_cases"] == 1
    assert receipt["rebuilt_configuration_case_ids"] == [
        "squint-configuration:study-a:ACL",
        "squint-configuration:study-a:MCL",
    ]


def test_the_command_runs_as_a_script_and_documents_itself(
    parent, tmp_path: Path
) -> None:
    worktree = SCRIPT.parents[1]
    env = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(worktree / "src"),
    }

    def run(*argv: object) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *[str(item) for item in argv]],
            check=False,
            cwd=tmp_path,
            env=env,
            text=True,
            capture_output=True,
            timeout=120,
        )

    helped = run("--help")
    assert helped.returncode == 0, helped.stderr
    for text in ("fingerprints", "curate", "Limitations", "--expected-manifest-sha256"):
        assert text in helped.stdout
    detailed = run("curate", "--help")
    assert detailed.returncode == 0, detailed.stderr
    for text in ("--decisions", "--output-memory", "--memory"):
        assert text in detailed.stdout

    decisions = tmp_path / "decisions.json"
    decisions.write_bytes(_document(_decision(parent.memory, FEMUR_A)))
    result = run(*_curate_argv(parent, decisions, tmp_path / "child"))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["retired_case_ids"] == [FEMUR_A]
    refused = run(*_curate_argv(parent, decisions, tmp_path / "child"))
    assert refused.returncode == 2
    assert json.loads(refused.stderr)["code"] == "output_already_exists"
