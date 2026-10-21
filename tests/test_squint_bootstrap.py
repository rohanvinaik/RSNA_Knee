from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from knee.diagnosis import squint_identity
from knee.diagnosis.product_cases import profiles_from_manifest
from knee.diagnosis.squint_bootstrap import (
    CALLS_SCHEMA,
    IDENTITY_CASES_SCHEMA,
    REVIEW_SCHEMA,
    TEACHING_SCHEMA,
    SquintBootstrapError,
    _rebuilt_configurations,
    build_review,
    publish_seed_memory,
    validate_calls,
)
from knee.diagnosis.squint_configurations import with_configuration_cases
from knee.diagnosis.squint_identity import prepare_identity, recall_identity
from knee.diagnosis.squint_locator import (
    persisted_recall_cache,
    prepare_recall,
    recall_object,
)
from knee.diagnosis.squint_memory import (
    SCHEMA,
    SquintMemoryError,
    _full_profile_from_validated_case,
    _json_sha256,
    _link_configuration_full_profiles,
    full_profile_from_case,
    hydrate_full_profiles,
    load_memory,
    load_memory_snapshot,
    save_memory,
)
from knee.diagnosis.squint_memory_view import memory_view
from knee.encoding.h5_store import write_h5
from knee.encoding.places import (
    BankSpec,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    compile_layout,
)
from knee.study.tables import LABELS

UIDS = ("study-a", "study-b", "study-c", "study-d", "study-e")


def cid(uid: str) -> str:
    return f"squint-case:{uid}:femur"


def _product(
    path: Path, uid: str, subjects: tuple[str, ...] = ("femur",)
) -> tuple[dict, dict]:
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
    records = {
        subject: {
            "count_layout_id": f"{spec.version}:{compiled.fingerprint}:{reference}",
            "reference_set_identity": reference,
            "sparse_counts": [["femur/signal", 0, 5], ["femur/signal", 2, 3]],
            "status": "valid",
            "preparation_status": "prepared",
            "assembly": {"code": "assembled", "batches": []},
            "detail": f"fixture record for {uid}"
            if subject == "femur"
            else f"fixture {subject} record for {uid}",
        }
        for subject in subjects
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
            "objects": records,
        },
    }
    write_h5(path, manifest, {})
    return manifest, records[subjects[0]]


@pytest.fixture
def seed(tmp_path: Path) -> SimpleNamespace:
    products = tmp_path / "products"
    products.mkdir()
    cases = []
    sources = {}
    ledger = {}
    manifests = {}
    for uid in UIDS:
        product = products / (f"{uid}.h5")
        manifest, record = _product(product, uid)
        manifests[uid] = manifest
        composition = manifest["object_composition"]
        digest = hashlib.sha256(product.read_bytes()).hexdigest()
        labels = {question: None for question in LABELS}
        labels["ACL"] = 1
        ledger[uid] = labels
        sources[uid] = {
            "product_path": str(product.resolve()),
            "product_sha256": digest,
            "layout_fingerprint": composition["layout_fingerprint"],
            "carrier_identity": composition["carrier_identity"],
            "source_roots": {},
            "full_profile_subjects": ["femur"],
        }
        cases.append(
            {
                "case_id": cid(uid),
                "study_uid": uid,
                "subject": "femur",
                "condition_calls": {"ACL": 1},
                "presentation_scope": {"ACL": "positive_condition_presentation"},
                "question_roles": {"ACL": "implicated"},
                "label_attribution": {},
                "profile": {
                    "schema": "knee.squint-profile/v1",
                    "subject": "femur",
                    "banks": {
                        "coarse/femur/signal": [5, 0, 3],
                        'squint/v2/view=["Sagittal","0","0"]/role=object/metric=signal/direction=d/scale=10mm': [
                            1,
                            0,
                            0,
                        ],
                    },
                    "source": {"procedure": "knee.squint-profile/scan-tercile-v1"},
                },
                "regions": [],
                "full_profile": {
                    "subject": "femur",
                    "mode": "full",
                    "scope": "object:femur",
                    "count_layout_id": record["count_layout_id"],
                    "reference_set_identity": record["reference_set_identity"],
                    "carrier_identity": composition["carrier_identity"],
                    "layout_fingerprint": composition["layout_fingerprint"],
                    "product_record_sha256": _json_sha256(record),
                },
                "full_source": {
                    "product_path": str(product.resolve()),
                    "product_sha256": digest,
                    "study_uid": uid,
                    "source_roots": {},
                },
                "teaching_source": {"kind": "official_train_csv_label"},
            }
        )
    legacy = {
        "schema": SCHEMA,
        "revision": "legacy-identity-only",
        "questions": list(LABELS),
        "procedure": {"id": "knee.squint-ternary/v1"},
        "source_identities": sources,
        "label_ledger": ledger,
        "object_conditions": {},
        "object_question_roles": {},
        "cases": cases,
    }
    configured = with_configuration_cases(hydrate_full_profiles(legacy, products))
    _link_configuration_full_profiles(configured)
    save_memory(configured, tmp_path / "parent")
    snapshot = load_memory_snapshot(tmp_path / "parent")
    for product in products.glob("*.h5"):
        product.unlink()
    return SimpleNamespace(snapshot=snapshot, manifests=manifests)


def _pin(document: dict) -> str:
    return hashlib.sha256(
        json.dumps(document, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _calls(pin: str, items: list, reader: str = "reader-one") -> dict:
    return {
        "schema": CALLS_SCHEMA,
        "review_sha256": pin,
        "reader": reader,
        "calls": [
            {"candidate_id": cand, "call": value, "notes": "n"} for cand, value in items
        ],
    }


def _review(seed: SimpleNamespace, ids: list) -> dict:
    snapshot = seed.snapshot
    return build_review(snapshot.memory, snapshot.sha256, ids)


def test_publish_keeps_only_confirmed_objects(seed, tmp_path: Path) -> None:
    snapshot = seed.snapshot
    before = copy.deepcopy(snapshot.memory)
    assert any(c["subject"].startswith("diagnosis/") for c in before["cases"])
    ids = [cid(u) for u in UIDS]
    review = _review(seed, ids)
    assert review["schema"] == REVIEW_SCHEMA
    pin = _pin(review)
    calls = _calls(
        pin,
        [
            (ids[0], "confirm"),
            (ids[1], "confirm"),
            (ids[2], "reject"),
            (ids[3], "unsure"),
        ],
    )
    out = tmp_path / "child"
    result = publish_seed_memory(snapshot, review, calls, pin, out)
    assert result["outcome"] == "published"
    child = load_memory(out)
    parent_cases = {c["case_id"]: c for c in before["cases"]}
    objects = [c for c in child["cases"] if not c["subject"].startswith("diagnosis/")]
    assert [c["case_id"] for c in objects] == ids[:2]
    for case in objects:
        assert case == parent_cases[case["case_id"]]
    # The published seed keeps a diagnosis voice: its whole-condition cases are
    # rebuilt from the confirmed object cases alone. A whole-case confirm keeps
    # its role whole, so each rebuilt case is the parent's own.
    configurations = child["cases"][len(objects) :]
    assert [c["case_id"] for c in configurations] == [
        f"squint-configuration:{uid}:ACL" for uid in UIDS[:2]
    ]
    for case in configurations:
        assert case == parent_cases[case["case_id"]]
    assert (result["object_case_count"], result["configuration_case_count"]) == (2, 2)
    assert child["label_ledger"] == {
        uid: before["label_ledger"][uid] for uid in UIDS[:2]
    }
    assert set(child["source_identities"]) == {"study-a", "study-b"}
    assert len(child["full_profile_payloads"]["payloads"]) == 2
    assert len(child["full_profile_contexts"]["contexts"]) == 2
    assert child["full_profile_retention"]["payload_count"] == 2
    assert child["revision"] != before["revision"]
    assert not (out / "recall-preparation.json").exists()
    teaching = child["object_identity_teaching"]
    assert teaching["schema"] == TEACHING_SCHEMA
    assert teaching["confirmed_case_ids"] == ids[:2]
    assert teaching["reader"] == "reader-one"
    assert teaching["review_sha256"] == pin
    assert teaching["source_manifest_sha256"] == snapshot.sha256
    assert teaching["calls"] == calls["calls"][:4]
    assert teaching["full_profile_role"] == "retained_source_only"
    assert teaching["identity_scope"] == "per_call_reviewed_views_or_whole_case"
    # The reject's sheet drew no support view, so it writes no negative case.
    assert teaching["negative_case_ids"] == []
    assert teaching["negatives_not_written"] == [
        {"candidate_id": ids[2], "reason": "no_drawn_profile_view"}
    ]
    assert child["object_identity_cases"] == {
        "schema": IDENTITY_CASES_SCHEMA,
        "cases": [],
    }
    for uid, case in zip(UIDS[:2], objects, strict=True):
        expected = profiles_from_manifest(seed.manifests[uid], mode="full")[0]
        actual = full_profile_from_case(child, case)
        assert actual.bundle == expected.bundle
        assert actual.source_id == uid
    for uid, case in zip(UIDS[:2], configurations, strict=True):
        expected = profiles_from_manifest(seed.manifests[uid], mode="full")[0]
        assert full_profile_from_case(child, case, subject="femur").bundle == (
            expected.bundle
        )
    assert snapshot.memory == before


def test_review_pins_candidates(seed) -> None:
    snapshot = seed.snapshot
    review = build_review(
        snapshot.memory,
        snapshot.sha256,
        [cid("study-a")],
        sheets={cid("study-a"): "sheet.png"},
        sanity_report={"ok": True},
    )
    entry = review["candidates"][0]
    case = next(c for c in snapshot.memory["cases"] if c["case_id"] == cid("study-a"))
    assert entry["candidate_id"] == entry["case_id"] == case["case_id"]
    assert entry["profile_sha256"] == _json_sha256(case["profile"])
    assert entry["profile_views"] == [["Sagittal", "0", "0"]]
    assert entry["full_profile"] == case["full_profile"]
    assert entry["source_product_sha256"] == case["full_source"]["product_sha256"]
    assert entry["sheet_path"] == "sheet.png"
    assert review["sanity_report"] == {"ok": True}
    plain = _review(seed, [cid("study-a")])
    assert "sheet_path" not in plain["candidates"][0]
    assert "sanity_report" not in plain


@pytest.mark.parametrize("kind", ["reject_unsure", "empty"])
def test_calls_writing_no_identity_case_publish_nothing(
    seed, tmp_path: Path, kind: str
) -> None:
    # The reject's candidate has no drawn support view, so it writes no
    # negative case; unsure writes nothing. Nothing is taught, nothing written.
    ids = [cid(u) for u in UIDS[:3]]
    review = _review(seed, ids)
    pin = _pin(review)
    items = [(ids[0], "reject"), (ids[1], "unsure")] if kind == "reject_unsure" else []
    out = tmp_path / "child"
    with pytest.raises(SquintBootstrapError) as info:
        publish_seed_memory(seed.snapshot, review, _calls(pin, items), pin, out)
    assert info.value.code == "no_identity_cases_written"
    assert not out.exists()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["parent", "products"]


def test_review_selection_errors(seed) -> None:
    snapshot = seed.snapshot
    config_id = next(
        c["case_id"]
        for c in snapshot.memory["cases"]
        if c["subject"].startswith("diagnosis/")
    )
    one = cid("study-a")
    cases = [
        ([one, one], "duplicate_candidate"),
        (["nope"], "unknown_candidate"),
        ([config_id], "configuration_case_not_selectable"),
        ([], "case_ids_invalid"),
    ]
    for ids, code in cases:
        with pytest.raises(SquintBootstrapError) as info:
            build_review(snapshot.memory, snapshot.sha256, ids)
        assert info.value.code == code
    with pytest.raises(SquintBootstrapError) as info:
        build_review(snapshot.memory, "bad", [one])
    assert info.value.code == "source_manifest_sha256_invalid"


def test_stale_pins(seed, tmp_path: Path) -> None:
    ids = [cid("study-a")]
    stale = build_review(seed.snapshot.memory, "f" * 64, ids)
    pin = _pin(stale)
    out = tmp_path / "child"
    with pytest.raises(SquintBootstrapError) as info:
        publish_seed_memory(
            seed.snapshot, stale, _calls(pin, [(ids[0], "confirm")]), pin, out
        )
    assert info.value.code == "stale_source_pin"
    review = _review(seed, ids)
    pin = _pin(review)
    with pytest.raises(SquintBootstrapError) as info:
        publish_seed_memory(
            seed.snapshot, review, _calls("0" * 64, [(ids[0], "confirm")]), pin, out
        )
    assert info.value.code == "stale_review_pin"
    assert not out.exists()


def test_snapshot_drift_is_refused(seed, tmp_path: Path) -> None:
    ids = [cid("study-a"), cid("study-b")]
    review = _review(seed, ids)
    pin = _pin(review)
    calls = _calls(pin, [(ids[0], "confirm")])
    out = tmp_path / "child"

    profile_memory = copy.deepcopy(seed.snapshot.memory)
    target = next(c for c in profile_memory["cases"] if c["case_id"] == ids[1])
    target["profile"]["banks"]["coarse/femur/signal"] = [9, 0, 3]
    drifted = replace(seed.snapshot, memory=profile_memory)
    with pytest.raises(SquintBootstrapError) as info:
        publish_seed_memory(drifted, review, calls, pin, out)
    assert info.value.code == "profile_digest_mismatch"

    product_memory = copy.deepcopy(seed.snapshot.memory)
    target = next(c for c in product_memory["cases"] if c["case_id"] == ids[0])
    target["full_source"]["product_sha256"] = "0" * 64
    drifted = replace(seed.snapshot, memory=product_memory)
    with pytest.raises(SquintBootstrapError) as info:
        publish_seed_memory(drifted, review, calls, pin, out)
    assert info.value.code == "source_product_mismatch"

    ref_memory = copy.deepcopy(seed.snapshot.memory)
    target = next(c for c in ref_memory["cases"] if c["case_id"] == ids[0])
    target["full_profile"]["product_record_sha256"] = "1" * 64
    drifted = replace(seed.snapshot, memory=ref_memory)
    with pytest.raises(SquintBootstrapError) as info:
        publish_seed_memory(drifted, review, calls, pin, out)
    assert info.value.code == "invalid_snapshot_state"
    assert not out.exists()


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("duplicate", "duplicate_call"),
        ("unknown", "unknown_candidate"),
        ("bad_value", "call_value_invalid"),
        ("bad_notes", "call_notes_invalid"),
        ("no_reader", "calls_malformed"),
        ("bad_schema", "calls_malformed"),
        ("extra_key", "calls_malformed"),
        ("not_list", "calls_malformed"),
    ],
)
def test_malformed_calls(seed, tmp_path: Path, mutation: str, code: str) -> None:
    ids = [cid("study-a"), cid("study-b")]
    review = _review(seed, ids)
    pin = _pin(review)
    calls = _calls(pin, [(ids[0], "confirm")])
    record = calls["calls"][0]
    if mutation == "duplicate":
        calls["calls"].append(dict(record))
    elif mutation == "unknown":
        calls["calls"].append({"candidate_id": "nope", "call": "confirm", "notes": ""})
    elif mutation == "bad_value":
        record["call"] = "maybe"
    elif mutation == "bad_notes":
        record["notes"] = None
    elif mutation == "no_reader":
        calls["reader"] = ""
    elif mutation == "bad_schema":
        calls["schema"] = "other"
    elif mutation == "extra_key":
        record["extra"] = 1
    else:
        calls["calls"] = "confirm"
    with pytest.raises(SquintBootstrapError) as info:
        validate_calls(review, calls, pin)
    assert info.value.code == code
    out = tmp_path / "child"
    with pytest.raises(SquintBootstrapError):
        publish_seed_memory(seed.snapshot, review, calls, pin, out)
    assert not out.exists()


def test_calls_may_be_a_subset(seed) -> None:
    ids = [cid(u) for u in UIDS[:3]]
    review = _review(seed, ids)
    pin = _pin(review)
    result = validate_calls(review, _calls(pin, [(ids[2], "confirm")]), pin)
    assert result["outcome"] == "valid"
    assert result["confirmed_case_ids"] == [ids[2]]
    review["candidates"].append(copy.deepcopy(review["candidates"][0]))
    with pytest.raises(SquintBootstrapError) as info:
        validate_calls(review, _calls(pin, []), pin)
    assert info.value.code == "duplicate_candidate"


@pytest.mark.parametrize("kind", ["traversal", "inside_source", "existing", "not_path"])
def test_unsafe_output_paths(seed, tmp_path: Path, kind: str) -> None:
    ids = [cid("study-a")]
    review = _review(seed, ids)
    pin = _pin(review)
    calls = _calls(pin, [(ids[0], "confirm")])
    if kind == "traversal":
        out = tmp_path / "x" / ".." / "child"
        code = "output_path_unsafe"
    elif kind == "inside_source":
        out = seed.snapshot.path.parent / "child"
        code = "output_path_unsafe"
    elif kind == "existing":
        out = tmp_path / "exists"
        out.mkdir()
        code = "output_exists"
    else:
        out = str(tmp_path / "child")
        code = "output_path_unsafe"
    with pytest.raises(SquintBootstrapError) as info:
        publish_seed_memory(seed.snapshot, review, calls, pin, out)
    assert info.value.code == code
    assert not (tmp_path / "child").exists()
    assert not (tmp_path / "x").exists()
    assert not (seed.snapshot.path.parent / "child").exists()


def test_invalid_snapshot_state(seed, tmp_path: Path) -> None:
    ids = [cid("study-a")]
    review = _review(seed, ids)
    pin = _pin(review)
    calls = _calls(pin, [(ids[0], "confirm")])
    broken = replace(seed.snapshot, status="invalid", memory=None)
    with pytest.raises(SquintBootstrapError) as info:
        publish_seed_memory(broken, review, calls, pin, tmp_path / "child")
    assert info.value.code == "invalid_snapshot_state"
    assert not (tmp_path / "child").exists()


def test_confirmed_scoped_view_requires_drawn_evidence(seed, tmp_path: Path) -> None:
    case_id = cid("study-a")
    review = _review(seed, [case_id])
    pin = _pin(review)
    calls = _calls(pin, [(case_id, "confirm")])
    calls["calls"][0]["views"] = [["Sagittal", "0", "0"]]
    with pytest.raises(SquintBootstrapError) as info:
        validate_calls(review, calls, pin)
    assert info.value.code == "view_not_drawn"
    review["candidates"][0]["evidence"] = {
        "panels": [
            {
                "view": {
                    "orientation": "Sagittal",
                    "fluid_sensitive": "0",
                    "fat_suppression": "0",
                },
                "image_state": "read",
                "support_state": "drawn",
            }
        ]
    }
    pin = _pin(review)
    calls["review_sha256"] = pin
    result = validate_calls(review, calls, pin)
    assert result["confirmed_case_ids"] == [case_id]
    calls["calls"][0]["views"] = [["Coronal", "0", "0"]]
    with pytest.raises(SquintBootstrapError) as info:
        validate_calls(review, calls, pin)
    assert info.value.code == "view_not_available"


def test_profile_views_are_reverified_during_publication(seed, tmp_path: Path) -> None:
    case_id = cid("study-a")
    review = _review(seed, [case_id])
    review["candidates"][0]["profile_views"] = [["Coronal", "0", "0"]]
    pin = _pin(review)
    calls = _calls(pin, [(case_id, "confirm")])
    with pytest.raises(SquintBootstrapError) as info:
        publish_seed_memory(seed.snapshot, review, calls, pin, tmp_path / "child")
    assert info.value.code == "profile_views_mismatch"
    assert not (tmp_path / "child").exists()


def test_legacy_review_without_profile_views_still_accepts_whole_case(
    seed, tmp_path: Path
) -> None:
    case_id = cid("study-a")
    review = _review(seed, [case_id])
    del review["candidates"][0]["profile_views"]
    pin = _pin(review)
    calls = _calls(pin, [(case_id, "confirm")])
    assert validate_calls(review, calls, pin)["confirmed_case_ids"] == [case_id]
    output = tmp_path / "legacy-child"
    result = publish_seed_memory(seed.snapshot, review, calls, pin, output)
    assert result["outcome"] == "published"
    assert load_memory(output)["cases"][0]["case_id"] == case_id


@pytest.mark.parametrize(
    "views",
    [[], [["Sagittal", "0"]], [["Sagittal", "0", "0"], ["Sagittal", "0", "0"]]],
)
def test_scoped_call_views_must_be_nonempty_unique_triples(seed, views) -> None:
    case_id = cid("study-a")
    review = _review(seed, [case_id])
    review["candidates"][0]["evidence"] = {
        "panels": [
            {
                "view": {
                    "orientation": "Sagittal",
                    "fluid_sensitive": "0",
                    "fat_suppression": "0",
                },
                "image_state": "read",
                "support_state": "drawn",
            }
        ]
    }
    pin = _pin(review)
    calls = _calls(pin, [(case_id, "confirm")])
    calls["calls"][0]["views"] = views
    with pytest.raises(SquintBootstrapError) as info:
        validate_calls(review, calls, pin)
    assert info.value.code == "call_views_invalid"


def test_unknown_scoped_candidate_has_named_refusal(seed) -> None:
    review = _review(seed, [cid("study-a")])
    pin = _pin(review)
    calls = _calls(pin, [("not-in-review", "confirm")])
    calls["calls"][0]["views"] = [["Sagittal", "0", "0"]]
    with pytest.raises(SquintBootstrapError) as info:
        validate_calls(review, calls, pin)
    assert info.value.code == "unknown_candidate"


# ------------------------------------------------- signed identity teaching
# Each study holds one candidate with two reviewed views. study-c's femur
# candidate shows femur coronally and other tissue sagittally; study-d's
# patella candidate shows patella coronally and the femur sagittally.

SAG = ["Sagittal", "0", "0"]
COR = ["Coronal", "0", "0"]
AXIAL = ["Axial", "0", "0"]
PROCEDURE = "knee.squint-profile/scan-tercile-v1"
CONDITION = {"femur": "ACL", "patella": "PF OA"}
SIGNED_CASES = (
    ("study-a", "femur", ((SAG, (3, 0, 0)), (COR, (3, 0, 0)))),
    ("study-b", "patella", ((SAG, (0, 0, 3)), (COR, (0, 0, 3)))),
    ("study-c", "femur", ((SAG, (1, 2, 0)), (COR, (3, 0, 0)))),
    ("study-d", "patella", ((SAG, (3, 0, 0)), (COR, (0, 0, 3)))),
)
FA, PB, FC, PD = (f"squint-case:{uid}:{subject}" for uid, subject, _ in SIGNED_CASES)
ALT_FEMUR_SAG = [{"identity": "femur", "views": [SAG]}]


def territory(view: list[str]) -> str:
    return (
        "squint/v2/view="
        + json.dumps(view, separators=(",", ":"))
        + "/role=object/metric=signal/direction=d/scale=10mm"
    )


def query(by_view: dict[str, tuple], subject: str = "femur") -> dict:
    return {
        "schema": "knee.squint-profile/v1",
        "subject": subject,
        "banks": {territory(json.loads(view)): list(c) for view, c in by_view.items()},
        "source": {"procedure": PROCEDURE},
    }


S, C = json.dumps(SAG), json.dumps(COR)


@pytest.fixture
def signed(tmp_path: Path) -> SimpleNamespace:
    products = tmp_path / "products"
    products.mkdir()
    cases, sources, ledger, manifests = [], {}, {}, {}
    for uid, subject, by_view in SIGNED_CASES:
        product = products / f"{uid}.h5"
        manifest, record = _product(product, uid, (subject,))
        manifests[uid] = manifest
        composition = manifest["object_composition"]
        digest = hashlib.sha256(product.read_bytes()).hexdigest()
        labels = {question: None for question in LABELS}
        labels[CONDITION[subject]] = 1
        ledger[uid] = labels
        sources[uid] = {
            "product_path": str(product.resolve()),
            "product_sha256": digest,
            "layout_fingerprint": composition["layout_fingerprint"],
            "carrier_identity": composition["carrier_identity"],
            "source_roots": {},
            "full_profile_subjects": [subject],
        }
        banks = {f"coarse/{subject}/signal": [5, 0, 3]}
        banks.update({territory(view): list(counts) for view, counts in by_view})
        cases.append(
            {
                "case_id": f"squint-case:{uid}:{subject}",
                "study_uid": uid,
                "subject": subject,
                "condition_calls": {CONDITION[subject]: 1},
                "presentation_scope": {
                    CONDITION[subject]: "positive_condition_presentation"
                },
                "question_roles": {CONDITION[subject]: "implicated"},
                "label_attribution": {},
                "profile": {
                    "schema": "knee.squint-profile/v1",
                    "subject": subject,
                    "banks": banks,
                    "source": {"procedure": PROCEDURE},
                },
                "regions": [],
                "full_profile": {
                    "subject": subject,
                    "mode": "full",
                    "scope": f"object:{subject}",
                    "count_layout_id": record["count_layout_id"],
                    "reference_set_identity": record["reference_set_identity"],
                    "carrier_identity": composition["carrier_identity"],
                    "layout_fingerprint": composition["layout_fingerprint"],
                    "product_record_sha256": _json_sha256(record),
                },
                "full_source": {
                    "product_path": str(product.resolve()),
                    "product_sha256": digest,
                    "study_uid": uid,
                    "source_roots": {},
                },
                "teaching_source": {"kind": "official_train_csv_label"},
            }
        )
    legacy = {
        "schema": SCHEMA,
        "revision": "legacy-signed-identity",
        "questions": list(LABELS),
        "procedure": {"id": "knee.squint-ternary/v1"},
        "source_identities": sources,
        "label_ledger": ledger,
        "object_conditions": {},
        "object_question_roles": {},
        "cases": cases,
    }
    save_memory(hydrate_full_profiles(legacy, products), tmp_path / "parent")
    snapshot = load_memory_snapshot(tmp_path / "parent")
    for product in products.glob("*.h5"):
        product.unlink()
    return SimpleNamespace(snapshot=snapshot, manifests=manifests, root=tmp_path)


def _signed_review(signed: SimpleNamespace, ids: list, drawn: dict) -> dict:
    """Pin the candidates; ``drawn`` names each sheet's read, drawn views."""
    review = build_review(signed.snapshot.memory, signed.snapshot.sha256, ids)
    for candidate in review["candidates"]:
        candidate["evidence"] = {
            "panels": [
                {
                    "view": dict(
                        zip(
                            ("orientation", "fluid_sensitive", "fat_suppression"),
                            view,
                            strict=True,
                        )
                    ),
                    "image_state": "read",
                    "support_state": "drawn",
                }
                for view in drawn.get(candidate["candidate_id"], ())
            ]
        }
    return review


def _row(candidate_id: str, call: str, **extra) -> dict:
    return {"candidate_id": candidate_id, "call": call, "notes": "n", **extra}


def _signed_calls(review: dict, rows: list) -> tuple[dict, str]:
    pin = _pin(review)
    return {
        "schema": CALLS_SCHEMA,
        "review_sha256": pin,
        "reader": "reader-one",
        "calls": rows,
    }, pin


def _publish(signed: SimpleNamespace, review: dict, rows: list, name: str):
    calls, pin = _signed_calls(review, rows)
    out = signed.root / name
    result = publish_seed_memory(signed.snapshot, review, calls, pin, out)
    return result, load_memory(out), calls


def object_ids(memory: dict) -> list[str]:
    return [
        c["case_id"]
        for c in memory["cases"]
        if not c["subject"].startswith("diagnosis/")
    ]


def configuration_ids(memory: dict) -> list[str]:
    return [
        c["case_id"] for c in memory["cases"] if c["subject"].startswith("diagnosis/")
    ]


def test_reject_publishes_an_ordinary_negative_case_beside_the_cases(signed):
    parent = {c["case_id"]: c for c in signed.snapshot.memory["cases"]}
    review = _signed_review(signed, [FA, PB, FC, PD], {FC: [SAG, COR], PB: [SAG]})
    rows = [
        _row(FA, "confirm"),
        _row(PB, "confirm"),
        _row(FC, "reject"),
        _row(PD, "unsure", views=[SAG]),
    ]
    result, child, calls = _publish(signed, review, rows, "child")
    assert result["confirmed_case_ids"] == [FA, PB]
    assert result["negative_case_ids"] == [FC]
    assert object_ids(child) == [FA, PB]
    # The rejected candidate is no configuration role: study-c composes nothing.
    assert configuration_ids(child) == [
        "squint-configuration:study-a:ACL",
        "squint-configuration:study-b:PF OA",
    ]
    table = child["object_identity_cases"]
    assert table["schema"] == IDENTITY_CASES_SCHEMA
    assert table["cases"] == [parent[FC]]
    teaching = child["object_identity_teaching"]
    assert teaching["negative_case_ids"] == [FC]
    # No views: every drawn view that the profile holds.
    assert teaching["negative_views"] == {FC: [COR, SAG]}
    assert teaching["negatives_not_written"] == []
    assert teaching["alternative_positives"] == []
    assert teaching["calls"] == calls["calls"]
    assert "censors" not in child
    assert set(child["source_identities"]) == {"study-a", "study-b", "study-c"}
    # Read back offline: the fixture deleted every H5 product.
    record = table["cases"][0]
    profile = _full_profile_from_validated_case(
        child, record, record["full_profile"], record["subject"]
    )
    expected = profiles_from_manifest(signed.manifests["study-c"], mode="full")[0]
    assert profile.bundle == expected.bundle
    with pytest.raises(SquintMemoryError, match="full_profile_case_not_in_memory"):
        full_profile_from_case(child, record)
    # The identity reader meets the -1 on the loaded child.
    like_rejected = recall_identity(query({S: (1, 2, 0), C: (3, 0, 0)}), child)
    assert like_rejected["outcome"] == "unresolved_conflict"
    assert like_rejected["reason"] == "identity_spoken_for_and_against"
    assert like_rejected["conflicted_identities"] == ["femur"]
    [row] = like_rejected["negative_cases"]
    assert (row["case_id"], row["digit"], row["speaks"]) == (FC, -1, True)
    like_seed = recall_identity(query({S: (3, 0, 0), C: (3, 0, 0)}), child)
    assert like_seed["outcome"] == "identified" and like_seed["identity"] == "femur"


def test_negative_only_teaching_publishes_and_waits_for_an_opposing_side(signed):
    review = _signed_review(signed, [FC], {FC: [SAG]})
    result, child, _ = _publish(
        signed, review, [_row(FC, "reject", views=[SAG])], "child"
    )
    assert result["outcome"] == "published" and result["confirmed_case_ids"] == []
    assert child["cases"] == []
    assert [r["case_id"] for r in child["object_identity_cases"]["cases"]] == [FC]
    assert child["object_identity_teaching"]["negative_views"] == {FC: [SAG]}
    prepared = prepare_identity(child)
    assert prepared["seed_count"] == 0 and prepared["negative_case_count"] == 1
    recall = recall_identity(query({S: (1, 2, 0)}), child, prepared=prepared)
    assert recall["outcome"] == "silent"
    assert recall["reason"] == "no_eligible_seed_cases"


def test_confirm_with_negative_views_splits_one_candidate_by_view(signed):
    review = _signed_review(signed, [FA, FC], {FC: [SAG, COR]})
    rows = [
        _row(FA, "confirm"),
        _row(FC, "confirm", views=[COR], negative_views=[SAG]),
    ]
    result, child, _ = _publish(signed, review, rows, "child")
    assert result["confirmed_case_ids"] == [FA, FC]
    assert result["negative_case_ids"] == [FC]
    assert object_ids(child) == [FA, FC]
    assert [r["case_id"] for r in child["object_identity_cases"]["cases"]] == [FC]
    assert child["object_identity_teaching"]["negative_views"] == {FC: [SAG]}
    prepared = prepare_identity(child)
    seeds = {seed["case_id"]: seed for seed in prepared._seeds}
    negatives = {case["case_id"]: case for case in prepared._negatives}
    assert set(seeds[FC]["banks"]) == {territory(COR)}
    assert set(negatives[FC]["banks"]) == {territory(SAG)}


def test_also_positive_teaches_the_known_alternative_identity_outside_cases(signed):
    parent = {c["case_id"]: c for c in signed.snapshot.memory["cases"]}
    review = _signed_review(signed, [FA, PB, PD], {PD: [SAG, COR]})
    rows = [
        _row(FA, "confirm"),
        _row(PB, "confirm"),
        _row(PD, "reject", views=[SAG], also_positive=ALT_FEMUR_SAG),
    ]
    result, child, _ = _publish(signed, review, rows, "child")
    entry = f"{PD}::also_positive::femur"
    assert result["alternative_positive_ids"] == [entry]
    assert object_ids(child) == [FA, PB]
    # Neither the rejected patella nor its alternative femur becomes a role.
    assert all(":study-d:" not in case_id for case_id in configuration_ids(child))
    # The record keeps its own subject and condition calls (patella, PF OA).
    assert child["object_identity_cases"]["cases"] == [parent[PD]]
    teaching = child["object_identity_teaching"]
    assert teaching["alternative_positives"] == [
        {"entry_id": entry, "case_id": PD, "identity": "femur", "views": [SAG]}
    ]
    assert teaching["negative_views"] == {PD: [SAG]}
    prepared = prepare_identity(child)
    assert prepared["seed_count"] == 3
    assert prepared["alternative_positive_count"] == 1
    seed = next(seed for seed in prepared._seeds if seed["case_id"] == entry)
    assert (seed["subject"], seed["source_case_id"]) == ("femur", PD)
    assert set(seed["banks"]) == {territory(SAG)}
    recall = recall_identity(query({S: (3, 0, 0)}), child, prepared=prepared)
    assert recall["outcome"] == "identified" and recall["identity"] == "femur"
    assert recall["opposed_identities"] == ["patella"]


def test_unsure_writes_nothing_on_its_proposed_identity(signed):
    review = _signed_review(signed, [FA, PD], {PD: [SAG, COR]})
    _, child, _ = _publish(
        signed,
        review,
        [_row(FA, "confirm"), _row(PD, "unsure", views=[SAG])],
        "child-unsure",
    )
    assert child["object_identity_cases"]["cases"] == []
    assert child["object_identity_teaching"]["negative_case_ids"] == []
    _, child, _ = _publish(
        signed,
        review,
        [_row(FA, "confirm"), _row(PD, "unsure", also_positive=ALT_FEMUR_SAG)],
        "child-unsure-alternative",
    )
    teaching = child["object_identity_teaching"]
    assert teaching["negative_case_ids"] == []
    assert [item["identity"] for item in teaching["alternative_positives"]] == ["femur"]


def test_condition_recall_never_reads_negative_or_alternative_identity_records(signed):
    # Confirm calls scope condition evidence to their views (CLASSICAL_AI_BUILD_
    # DESIGN §5.1); rejects and alternatives, kept outside cases, never reach it.
    review = _signed_review(signed, [FA, PB, FC, PD], {FC: [SAG, COR], PD: [SAG, COR]})
    plain_rows = [_row(FA, "confirm"), _row(PB, "confirm")]
    taught_rows = [
        *plain_rows,
        _row(FC, "reject"),
        _row(PD, "reject", views=[SAG], also_positive=ALT_FEMUR_SAG),
    ]
    _, plain, _ = _publish(signed, review, plain_rows, "plain")
    _, taught, _ = _publish(signed, review, taught_rows, "taught")
    assert taught["cases"] == plain["cases"]
    assert len(taught["object_identity_cases"]["cases"]) == 2
    prepared_plain, prepared_taught = prepare_recall(plain), prepare_recall(taught)
    assert persisted_recall_cache(plain, prepared_plain) == persisted_recall_cache(
        taught, prepared_taught
    )
    for question in ("ACL", "PF OA"):
        for subject in ("femur", "patella"):
            probe = query({S: (1, 2, 0), C: (3, 0, 0)}, subject=subject)
            assert recall_object(
                probe, {**plain, "prepared_recall": prepared_plain}, question
            ) == recall_object(
                probe, {**taught, "prepared_recall": prepared_taught}, question
            )
    held_out = memory_view(taught, exclude_study_uids=("study-c",))
    assert [r["case_id"] for r in held_out["object_identity_cases"]["cases"]] == [PD]


def test_seed_rebuilds_each_configuration_role_on_its_identity_views(signed):
    """A role whose case is confirmed coronally contributes only coronal banks."""
    review = _signed_review(signed, [FA, PB, FC, PD], {FC: [SAG, COR], PD: [SAG, COR]})
    rows = [
        _row(FA, "confirm"),
        _row(PB, "confirm"),
        _row(FC, "confirm", views=[COR], negative_views=[SAG]),
        _row(PD, "reject", views=[SAG], also_positive=ALT_FEMUR_SAG),
    ]
    result, child, _ = _publish(signed, review, rows, "child")
    parent = {case["case_id"]: case for case in signed.snapshot.memory["cases"]}
    by_id = {case["case_id"]: case for case in child["cases"]}
    assert object_ids(child) == [FA, PB, FC]
    for case_id in (FA, PB, FC):
        assert by_id[case_id] == parent[case_id]
    # The rejected patella and its alternative femur are never roles.
    assert configuration_ids(child) == [
        "squint-configuration:study-a:ACL",
        "squint-configuration:study-b:PF OA",
        "squint-configuration:study-c:ACL",
    ]
    assert (result["object_case_count"], result["configuration_case_count"]) == (3, 3)
    coronal = by_id["squint-configuration:study-c:ACL"]
    assert set(coronal["profile"]["banks"]) == {"object/femur/" + territory(COR)}
    source = coronal["profile"]["source"]
    assert source["roles"]["femur"]["status"] == "present"
    assert source["roles"]["femur"]["bank_count"] == 1
    assert source["missing_roles"] == [
        {"subject": subject, "status": "missing_object_case"}
        for subject in ("acl", "tibia", "pcl")
    ]
    assert coronal["condition_calls"] == {"ACL": 1}
    assert coronal["presentation_scope"] == {"ACL": "study_condition_configuration"}
    assert coronal["label_attribution"]["ACL"]["source"] == "label_ledger"
    assert (
        coronal["full_profile_refs"]["femur"]["payload_ref"]
        == (parent[FC]["full_profile"]["payload_ref"])
    )
    # A whole-case confirm keeps every bank of its role.
    whole = by_id["squint-configuration:study-a:ACL"]
    assert set(whole["profile"]["banks"]) == {
        "object/femur/" + name for name in parent[FA]["profile"]["banks"]
    }
    ledger = signed.snapshot.memory["label_ledger"]
    assert child["label_ledger"] == {
        uid: ledger[uid] for uid in ("study-a", "study-b", "study-c")
    }
    # Preparation reads the role exactly as published: no sagittal femur bank.
    prepared = prepare_recall(child)
    index = [case["case_id"] for case in child["cases"]].index(coronal["case_id"])
    assert set(prepared["case_profile_banks"][index]) == {
        "object/femur/" + territory(COR)
    }


def test_rebuilt_configuration_keeps_the_study_scope_of_a_bone_positive(signed):
    """The study label stays the configuration's call; the femur stays unlocalized."""
    memory = copy.deepcopy(signed.snapshot.memory)
    memory["label_ledger"]["study-c"]["Fracture"] = 1
    femur = next(case for case in memory["cases"] if case["case_id"] == FC)
    femur["condition_calls"]["Fracture"] = 1
    femur["presentation_scope"]["Fracture"] = "positive_condition_presentation"
    review = _signed_review(signed, [FC], {FC: [SAG, COR]})
    calls, pin = _signed_calls(
        review, [_row(FC, "confirm", views=[COR], negative_views=[SAG])]
    )
    out = signed.root / "fracture-child"
    publish_seed_memory(
        replace(signed.snapshot, memory=memory), review, calls, pin, out
    )
    child = load_memory(out)
    by_id = {case["case_id"]: case for case in child["cases"]}
    assert by_id[FC] == femur
    assert by_id[FC]["presentation_scope"]["Fracture"] == (
        "positive_condition_presentation"
    )
    fracture = by_id["squint-configuration:study-c:Fracture"]
    assert fracture["condition_calls"] == {"Fracture": 1}
    assert fracture["presentation_scope"] == {
        "Fracture": "study_condition_configuration"
    }
    assert set(fracture["profile"]["banks"]) == {"object/femur/" + territory(COR)}
    assert fracture["profile"]["source"]["missing_roles"] == [
        {"subject": subject, "status": "missing_object_case"}
        for subject in ("tibia", "patella", "fibula")
    ]


def test_a_rejected_candidate_beside_a_confirmed_one_is_only_a_missing_role():
    """In one study a confirmed femur and a rejected patella: PF OA's patella
    role is recorded missing, never composed from the rejected record."""
    femur = {
        "case_id": "squint-case:study-x:femur",
        "study_uid": "study-x",
        "subject": "femur",
        "condition_calls": {"PF OA": 1},
        "profile": {
            "schema": "knee.squint-profile/v1",
            "subject": "femur",
            "banks": {territory(SAG): [3, 0, 0], territory(COR): [0, 0, 3]},
            "source": {"procedure": PROCEDURE},
        },
        "regions": [],
    }
    patella = {**copy.deepcopy(femur), "case_id": "squint-case:study-x:patella"}
    patella["subject"] = patella["profile"]["subject"] = "patella"
    child = {
        "schema": SCHEMA,
        "revision": "seed-fixture",
        "cases": [femur],
        "object_identity_cases": {"schema": IDENTITY_CASES_SCHEMA, "cases": [patella]},
        "object_identity_teaching": {
            "schema": TEACHING_SCHEMA,
            "confirmed_case_ids": [femur["case_id"]],
            "negative_case_ids": [patella["case_id"]],
            "negative_views": {patella["case_id"]: [SAG]},
            "alternative_positives": [],
            "calls": [
                _row(femur["case_id"], "confirm", views=[COR]),
                _row(patella["case_id"], "reject", views=[SAG]),
            ],
        },
    }
    labels = dict.fromkeys(LABELS)
    labels["PF OA"] = 1
    source = {"label_ledger": {"study-x": labels, "study-y": labels}}
    configurations, ledger, revision = _rebuilt_configurations(source, child)
    assert ledger == {"study-x": labels}
    assert revision == "seed-fixture+question-configurations-v1"
    [case] = configurations
    assert case["case_id"] == "squint-configuration:study-x:PF OA"
    assert set(case["profile"]["banks"]) == {"object/femur/" + territory(COR)}
    assert case["profile"]["source"]["missing_roles"] == [
        {"subject": subject, "status": "missing_object_case"}
        for subject in ("patella", "patellar_cartilage", "trochlear_cartilage")
    ]
    assert case["presentation_scope"] == {"PF OA": "study_condition_configuration"}
    assert child["cases"] == [femur]


def test_seed_without_a_label_ledger_rebuilds_nothing(signed):
    """No labels, no whole-condition cases: nothing is invented."""
    memory = copy.deepcopy(signed.snapshot.memory)
    del memory["label_ledger"]
    review = _signed_review(signed, [FA], {})
    calls, pin = _signed_calls(review, [_row(FA, "confirm")])
    out = signed.root / "no-ledger-child"
    result = publish_seed_memory(
        replace(signed.snapshot, memory=memory), review, calls, pin, out
    )
    child = load_memory(out)
    assert [case["case_id"] for case in child["cases"]] == [FA]
    assert "label_ledger" not in child
    assert result["configuration_case_count"] == 0


SIGNED_REFUSALS = (
    (
        {FC: [COR]},
        _row(FC, "confirm", views=[COR], negative_views=[SAG]),
        "view_not_drawn",
    ),
    ({FC: [COR]}, _row(FC, "reject", views=[SAG]), "view_not_drawn"),
    ({FC: [SAG, COR]}, _row(FC, "reject", views=[AXIAL]), "view_not_available"),
    (
        {FC: [SAG, COR]},
        _row(FC, "reject", negative_views=[SAG]),
        "negative_views_require_confirm",
    ),
    (
        {FC: [SAG, COR]},
        _row(FC, "unsure", negative_views=[SAG]),
        "negative_views_require_confirm",
    ),
    (
        {FC: [SAG, COR]},
        _row(FC, "confirm", views=[COR], negative_views=[]),
        "call_negative_views_invalid",
    ),
    (
        {FC: [SAG, COR]},
        _row(FC, "confirm", views=[COR], negative_views=[SAG, SAG]),
        "call_negative_views_invalid",
    ),
    (
        {FC: [SAG, COR]},
        _row(FC, "confirm", views=[COR], negative_views=[SAG[:2]]),
        "call_negative_views_invalid",
    ),
    (
        {FC: [SAG, COR]},
        _row(FC, "confirm", views=[COR], negative_views=[AXIAL]),
        "view_not_available",
    ),
    (
        {FC: [SAG, COR]},
        _row(FC, "confirm", views=[SAG], negative_views=[SAG]),
        "call_views_overlap",
    ),
    ({FC: [SAG, COR]}, _row(FC, "confirm", negative_views=[SAG]), "call_views_overlap"),
    (
        {PD: [SAG, COR]},
        _row(PD, "reject", also_positive="femur"),
        "call_also_positive_invalid",
    ),
    (
        {PD: [SAG, COR]},
        _row(PD, "reject", also_positive=[]),
        "call_also_positive_invalid",
    ),
    (
        {PD: [SAG, COR]},
        _row(PD, "reject", also_positive=[{"identity": "femur"}]),
        "call_also_positive_invalid",
    ),
    (
        {PD: [SAG, COR]},
        _row(
            PD, "reject", also_positive=[{"identity": "femur", "views": [SAG], "x": 1}]
        ),
        "call_also_positive_invalid",
    ),
    (
        {PD: [SAG, COR]},
        _row(
            PD,
            "reject",
            also_positive=[*ALT_FEMUR_SAG, {"identity": "femur", "views": [COR]}],
        ),
        "call_also_positive_invalid",
    ),
    (
        {PD: [SAG, COR]},
        _row(
            PD, "reject", also_positive=[{"identity": "diagnosis/ACL", "views": [SAG]}]
        ),
        "also_positive_identity_invalid",
    ),
    (
        {PD: [SAG, COR]},
        _row(PD, "reject", also_positive=[{"identity": "patella", "views": [SAG]}]),
        "also_positive_identity_is_proposed",
    ),
    (
        {PD: [SAG, COR]},
        _row(PD, "reject", also_positive=[{"identity": "tibia", "views": [SAG]}]),
        "also_positive_identity_unknown",
    ),
    (
        {PD: [SAG, COR]},
        _row(PD, "reject", also_positive=[{"identity": "femur", "views": [AXIAL]}]),
        "view_not_available",
    ),
    ({PD: [COR]}, _row(PD, "reject", also_positive=ALT_FEMUR_SAG), "view_not_drawn"),
    (
        {PD: [SAG, COR]},
        _row(PD, "confirm", views=[SAG], also_positive=ALT_FEMUR_SAG),
        "call_views_overlap",
    ),
    (
        {PD: [SAG, COR]},
        _row(PD, "confirm", also_positive=ALT_FEMUR_SAG),
        "call_views_overlap",
    ),
    ({PD: [SAG, COR]}, {**_row(PD, "reject"), "censor": True}, "calls_malformed"),
)


@pytest.mark.parametrize("drawn,row,code", SIGNED_REFUSALS)
def test_signed_call_refusals_are_named_and_write_nothing(signed, drawn, row, code):
    review = _signed_review(signed, [FA, FC, PD], drawn)
    calls, pin = _signed_calls(review, [_row(FA, "confirm"), row])
    out = signed.root / "child"
    with pytest.raises(SquintBootstrapError) as info:
        publish_seed_memory(signed.snapshot, review, calls, pin, out)
    assert info.value.code == code
    assert not out.exists()


def test_alternative_identity_membership_is_settled_where_the_memory_is_known(signed):
    review = _signed_review(signed, [FA, PD], {PD: [SAG, COR]})
    unknown = [{"identity": "tibia", "views": [SAG]}]
    calls, pin = _signed_calls(review, [_row(PD, "reject", also_positive=unknown)])
    # The review alone does not know the memory's subjects; publication does.
    assert validate_calls(review, calls, pin)["alternative_positives"][0][
        "identity"
    ] == ("tibia")
    with pytest.raises(SquintBootstrapError) as info:
        validate_calls(review, calls, pin, known_subjects={"femur", "patella"})
    assert info.value.code == "also_positive_identity_unknown"
    two = [{"identity": "femur", "views": [SAG]}, {"identity": "tibia", "views": [SAG]}]
    calls, pin = _signed_calls(review, [_row(PD, "reject", also_positive=two)])
    with pytest.raises(SquintBootstrapError) as info:
        validate_calls(review, calls, pin)
    assert info.value.code == "call_views_overlap"


def test_identity_tables_share_one_schema_name():
    assert squint_identity.IDENTITY_CASES_SCHEMA == IDENTITY_CASES_SCHEMA
    assert squint_identity.TEACHING_SCHEMA == TEACHING_SCHEMA
