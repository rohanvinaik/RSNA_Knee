from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from knee.diagnosis.product_cases import profiles_from_manifest, profiles_from_product
from knee.diagnosis.squint_configurations import with_configuration_cases
from knee.diagnosis.squint_memory import (
    SCHEMA,
    SquintMemoryError,
    _canonical,
    _json_sha256,
    _link_configuration_full_profiles,
    full_profile_from_case,
    hydrate_full_profiles,
    load_memory,
    save_memory,
)
from knee.encoding.h5_store import write_h5
from knee.encoding.places import (
    BankSpec,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    compile_layout,
)
from knee.study.tables import LABELS


def _fixture_product(path: Path) -> tuple[dict, dict]:
    spec = LayoutSpec(
        "fixture-layout-v1",
        "fixture-carrier-v1",
        (
            BankSpec(
                "femur/signal",
                "signal",
                (MetricSpec("level", MetricKind.WORDS, ("low", "mid", "high")),),
            ),
        ),
    )
    compiled = compile_layout(spec)
    assert compiled is not None
    reference = "reference-set-fixture-v1"
    description = {
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
    uid = "study-portable-full"
    record = {
        "count_layout_id": f"{spec.version}:{compiled.fingerprint}:{reference}",
        "reference_set_identity": reference,
        "sparse_counts": [["femur/signal", 0, 5], ["femur/signal", 2, 3]],
        "status": "valid",
        "preparation_status": "prepared",
        "assembly": {"code": "assembled", "batches": []},
        "detail": "fixture record retained exactly",
    }
    manifest = {
        "study_uid": uid,
        "mode": "full",
        "product_storage": "h5",
        "spec": {"version": "fixture-spec-v1"},
        "spec_sha256": "a" * 64,
        "encoded_arrays": {},
        "object_composition": {
            "schema": "knee_object_profiles/v1",
            "carrier_identity": spec.carrier_id,
            "layout_fingerprint": compiled.fingerprint,
            "registry_fingerprint": "fixture-registry-v1",
            "layout": description,
            "objects": {"femur": record},
        },
    }
    write_h5(path, manifest, {})
    return manifest, record


def _legacy_memory(product: Path, manifest: dict, record: dict) -> dict:
    uid = manifest["study_uid"]
    composition = manifest["object_composition"]
    calls = {"ACL": 1}
    identity = {
        "subject": "femur",
        "mode": "full",
        "scope": "object:femur",
        "count_layout_id": record["count_layout_id"],
        "reference_set_identity": record["reference_set_identity"],
        "carrier_identity": composition["carrier_identity"],
        "layout_fingerprint": composition["layout_fingerprint"],
        "product_record_sha256": _json_sha256(record),
    }
    labels = {question: None for question in LABELS}
    labels["ACL"] = 1
    return {
        "schema": SCHEMA,
        "revision": "legacy-identity-only",
        "questions": list(LABELS),
        "procedure": {"id": "knee.squint-ternary/v1"},
        "source_identities": {
            uid: {
                "product_path": str(product.resolve()),
                "product_sha256": hashlib.sha256(product.read_bytes()).hexdigest(),
                "layout_fingerprint": composition["layout_fingerprint"],
                "carrier_identity": composition["carrier_identity"],
                "source_roots": {},
                "full_profile_subjects": ["femur"],
            }
        },
        "label_ledger": {uid: labels},
        "object_conditions": {},
        "object_question_roles": {},
        "cases": [
            {
                "case_id": f"squint-case:{uid}:femur",
                "study_uid": uid,
                "subject": "femur",
                "condition_calls": calls,
                "presentation_scope": {"ACL": "positive_condition_presentation"},
                "question_roles": {"ACL": "implicated"},
                "label_attribution": {},
                "profile": {
                    "schema": "knee.squint-profile/v1",
                    "subject": "femur",
                    "banks": {"coarse/femur/signal": [5, 0, 3]},
                    "source": {"procedure": "knee.squint-profile/scan-tercile-v1"},
                },
                "regions": [],
                "full_profile": identity,
                "full_source": {
                    "product_path": str(product.resolve()),
                    "product_sha256": hashlib.sha256(product.read_bytes()).hexdigest(),
                    "study_uid": uid,
                    "source_roots": {},
                },
                "teaching_source": {"kind": "official_train_csv_label"},
            }
        ],
    }


def test_public_manifest_reader_matches_product_reader() -> None:
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as temporary:
        path = Path(temporary) / "study.h5"
        manifest, _ = _fixture_product(path)
        from_product = profiles_from_product(path, mode="full")
        from_manifest = profiles_from_manifest(manifest, mode="full")
    assert from_product == from_manifest
    assert from_manifest[0].source_id == "study-portable-full"
    assert from_manifest[0].mode == "full"


@pytest.mark.parametrize("omit_receipt", [False, True])
def test_hydrated_full_profile_roundtrips_after_h5_is_removed(
    tmp_path: Path, omit_receipt: bool
) -> None:
    products = tmp_path / "products"
    products.mkdir()
    product = products / "study-portable-full.h5"
    manifest, record = _fixture_product(product)
    memory = _legacy_memory(product, manifest, record)
    original_product_sha256 = hashlib.sha256(product.read_bytes()).hexdigest()
    expected = profiles_from_product(product, mode="full")[0]

    hydrated = hydrate_full_profiles(memory, products)
    assert hydrated["revision"].endswith("+portable-full-profiles-v1")
    assert len(hydrated["full_profile_contexts"]["contexts"]) == 1
    assert len(hydrated["full_profile_payloads"]["payloads"]) == 1
    object_case = hydrated["cases"][0]
    payload_id = object_case["full_profile"]["payload_ref"]
    assert hydrated["full_profile_payloads"]["payloads"][payload_id]["record"] == record
    if omit_receipt:
        hydrated.pop("full_profile_retention")

    saved = tmp_path / "memory"
    save_memory(hydrated, saved)
    loaded = load_memory(saved)
    assert loaded["full_profile_retention"]["publication_reader_verified_pairs"] == 1
    product.unlink()
    actual = full_profile_from_case(loaded, loaded["cases"][0])
    assert actual.bundle == expected.bundle
    assert actual.source_id == "study-portable-full"
    assert actual.mode == "full"
    assert dict(actual.provenance)["adapter_mode"] == "full"
    assert dict(actual.provenance)["retained_product_sha256"] == original_product_sha256


def test_configuration_case_reuses_object_payload_reference(tmp_path: Path) -> None:
    product = tmp_path / "study-portable-full.h5"
    manifest, record = _fixture_product(product)
    memory = hydrate_full_profiles(_legacy_memory(product, manifest, record), tmp_path)
    configured = with_configuration_cases(memory)
    _link_configuration_full_profiles(configured)
    question_case = next(
        case
        for case in configured["cases"]
        if case["case_id"] == "squint-configuration:study-portable-full:ACL"
    )
    reference = question_case["full_profile_refs"]["femur"]
    object_reference = configured["cases"][0]["full_profile"]
    assert reference == {
        "payload_ref": object_reference["payload_ref"],
        "context_ref": object_reference["context_ref"],
        "availability": object_reference["availability"],
    }
    actual = full_profile_from_case(configured, question_case, subject="femur")
    assert actual.source_id == "study-portable-full"


def test_configuration_cases_created_before_hydration_resolve_offline(
    tmp_path: Path,
) -> None:
    products = tmp_path / "products"
    products.mkdir()
    product = products / "study-portable-full.h5"
    manifest, record = _fixture_product(product)
    legacy = _legacy_memory(product, manifest, record)
    configured_first = with_configuration_cases(legacy)

    hydrated = hydrate_full_profiles(configured_first, products)
    configuration = next(
        case
        for case in hydrated["cases"]
        if case["case_id"] == "squint-configuration:study-portable-full:ACL"
    )
    assert configuration["full_profiles"]["femur"].get("availability") is None
    assert configuration["full_profile_refs"]["femur"]["availability"] == (
        "retained_sparse_counts"
    )

    destination = tmp_path / "hydrated-memory"
    save_memory(hydrated, destination)
    loaded = load_memory(destination)
    product.unlink()
    stored_configuration = next(
        case
        for case in loaded["cases"]
        if case["case_id"] == "squint-configuration:study-portable-full:ACL"
    )
    actual = full_profile_from_case(loaded, stored_configuration, subject="femur")
    expected = profiles_from_manifest(manifest, mode="full")[0]
    assert actual.bundle == expected.bundle
    assert actual.source_id == "study-portable-full"


@pytest.mark.parametrize("tamper", ["context", "payload"])
def test_portable_full_table_digest_rejects_tampering(
    tmp_path: Path, tamper: str
) -> None:
    product = tmp_path / "study-portable-full.h5"
    manifest, record = _fixture_product(product)
    memory = hydrate_full_profiles(_legacy_memory(product, manifest, record), tmp_path)
    if tamper == "context":
        context_id = next(iter(memory["full_profile_contexts"]["contexts"]))
        memory["full_profile_contexts"]["contexts"][context_id]["study_uid"] = "other"
        message = "full_profile_context_invalid"
    else:
        payload_id = next(iter(memory["full_profile_payloads"]["payloads"]))
        memory["full_profile_payloads"]["payloads"][payload_id]["record"]["status"] = (
            "silent"
        )
        message = "full_profile_payload_digest_invalid"
    with pytest.raises(SquintMemoryError, match=message):
        full_profile_from_case(memory, memory["cases"][0])


def test_identity_only_legacy_case_is_named_nonportable(tmp_path: Path) -> None:
    product = tmp_path / "study-portable-full.h5"
    manifest, record = _fixture_product(product)
    legacy = _legacy_memory(product, manifest, record)
    with pytest.raises(SquintMemoryError, match="full_profile_not_portable"):
        full_profile_from_case(legacy, legacy["cases"][0])


@pytest.mark.parametrize("receipt_present", [True, False])
def test_publication_checks_later_payload_and_leaves_no_partial_memory(
    tmp_path: Path,
    receipt_present: bool,
) -> None:
    product = tmp_path / "study-portable-full.h5"
    manifest, valid_record = _fixture_product(product)
    invalid_record = {
        **valid_record,
        "sparse_counts": [["femur/signal", 999, 1]],
    }
    manifest["object_composition"]["objects"]["tibia"] = invalid_record
    write_h5(product, manifest, {})
    memory = _legacy_memory(product, manifest, valid_record)
    tibia_identity = {
        **memory["cases"][0]["full_profile"],
        "subject": "tibia",
        "count_layout_id": invalid_record["count_layout_id"],
        "reference_set_identity": invalid_record["reference_set_identity"],
        "product_record_sha256": _json_sha256(invalid_record),
    }
    tibia_case = json.loads(json.dumps(memory["cases"][0]))
    tibia_case.update(
        {
            "case_id": "squint-case:study-portable-full:tibia",
            "subject": "tibia",
            "full_profile": tibia_identity,
            "profile": {
                **tibia_case["profile"],
                "subject": "tibia",
            },
        }
    )
    memory["cases"].append(tibia_case)
    memory["source_identities"]["study-portable-full"]["full_profile_subjects"] = [
        "femur",
        "tibia",
    ]

    hydrated = hydrate_full_profiles(memory, tmp_path)
    if not receipt_present:
        del hydrated["full_profile_retention"]
    destination = tmp_path / "must-not-publish"
    with pytest.raises(SquintMemoryError, match="full_profile_manifest_rejected"):
        save_memory(hydrated, destination)
    assert not destination.exists()


def test_portable_context_keeps_reader_fields_and_discards_unused_metadata(
    tmp_path: Path,
) -> None:
    products = tmp_path / "products"
    products.mkdir()
    product = products / "study-portable-full.h5"
    manifest, record = _fixture_product(product)
    manifest["spec"]["unconsumed_definition"] = "s" * 500_000
    composition = manifest["object_composition"]
    composition["unconsumed_registry"] = {"entries": ["r" * 500_000]}
    composition["unconsumed_additions"] = {"opaque": [1, 2, 3]}
    write_h5(product, manifest, {})
    source_profile = profiles_from_manifest(manifest, mode="full")[0]
    memory = _legacy_memory(product, manifest, record)

    hydrated = hydrate_full_profiles(memory, products)
    context_id = hydrated["cases"][0]["full_profile"]["context_ref"]
    context = hydrated["full_profile_contexts"]["contexts"][context_id]
    assert set(context["manifest_fields"]) == {
        "study_uid",
        "mode",
        "product_storage",
        "spec",
        "spec_sha256",
    }
    assert context["manifest_fields"]["spec"] == {"version": "fixture-spec-v1"}
    assert set(context["object_composition"]) == {
        "schema",
        "carrier_identity",
        "layout_fingerprint",
        "registry_fingerprint",
        "layout",
    }
    assert "unconsumed_registry" not in context["object_composition"]
    assert "unconsumed_additions" not in context["object_composition"]
    assert len(_canonical(context)) < 5_000

    destination = tmp_path / "portable-memory"
    save_memory(hydrated, destination)
    loaded = load_memory(destination)
    product.unlink()
    actual = full_profile_from_case(loaded, loaded["cases"][0])
    assert actual.bundle == source_profile.bundle
    assert actual.bank_statuses == source_profile.bank_statuses
    assert actual.context == source_profile.context
    assert actual.source_id == source_profile.source_id
    assert actual.mode == source_profile.mode
    assert actual.scope == source_profile.scope
    actual_provenance = dict(actual.provenance)
    assert {
        key: actual_provenance[key] for key, _value in source_profile.provenance
    } == dict(source_profile.provenance)
