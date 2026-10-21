"""Tests for scripts/squint_object_bootstrap.py against the real shared seed API.

Only image reads are injected. Memory, snapshot, review, calls validation and
publication all use the installed knee modules. No competition data is read.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from knee.diagnosis.squint_bootstrap import (
    CALLS_SCHEMA,
    TEACHING_SCHEMA,
    SquintBootstrapError,
    validate_calls,
)
from knee.diagnosis.squint_configurations import with_configuration_cases
from knee.diagnosis.squint_identity import prepare_identity
from knee.diagnosis.squint_memory import (
    SCHEMA,
    _json_sha256,
    _link_configuration_full_profiles,
    full_profile_from_case,
    hydrate_full_profiles,
    load_memory,
    load_memory_snapshot,
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

ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / "scripts" / "squint_object_bootstrap.py"
    spec = importlib.util.spec_from_file_location("squint_object_bootstrap", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["squint_object_bootstrap"] = module
    spec.loader.exec_module(module)
    return module


MOD = _load()
UIDS = ("study-a", "study-b", "study-c", "study-d", "study-e")
REGIONS = [
    {"series_uid": "ser-ok", "view": "sag-pd", "window": [3, 4, 1, 3, 1, 3]},
    {"series_uid": "ser-nosup", "view": "cor-t1", "window": [3, 4, 1, 3, 1, 3]},
    {"series_uid": "ser-missing", "view": "ax-t2", "window": [3, 4, 1, 3, 1, 3]},
]


def cid(uid: str) -> str:
    return f"squint-case:{uid}:femur"


def fail_code(fn, *args, **kwargs):
    with pytest.raises(MOD.ObjectBootstrapError) as info:
        fn(*args, **kwargs)
    return info.value.code


def shared_code(fn, *args, **kwargs):
    with pytest.raises(SquintBootstrapError) as info:
        fn(*args, **kwargs)
    return info.value.code


def _product(path: Path, uid: str) -> tuple[dict, dict]:
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
    record = {
        "count_layout_id": f"{spec.version}:{compiled.fingerprint}:{reference}",
        "reference_set_identity": reference,
        "sparse_counts": [["femur/signal", 0, 5], ["femur/signal", 2, 3]],
        "status": "valid",
        "preparation_status": "prepared",
        "assembly": {"code": "assembled", "batches": []},
        "detail": f"fixture record for {uid}",
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


SAG_BANK = 'squint/v2/view=["Sagittal","0","0"]/role=object/metric=signal/direction=d/scale=10mm'
VIEW_REGIONS = [
    {
        "series_uid": "ser-ok",
        "view": {
            "orientation": "Sagittal",
            "fluid_sensitive": "0",
            "fat_suppression": "0",
        },
        "window": [3, 4, 1, 3, 1, 3],
    },
]


@pytest.fixture
def seed(tmp_path: Path) -> SimpleNamespace:
    return _build_seed(tmp_path, REGIONS, {})


@pytest.fixture
def seed_views(tmp_path: Path) -> SimpleNamespace:
    """Regions carry exact view triples and profiles a sagittal territory bank."""
    return _build_seed(tmp_path, VIEW_REGIONS, {SAG_BANK: [1, 0, 0]})


def _build_seed(tmp_path: Path, regions: list, extra_banks: dict) -> SimpleNamespace:
    products = tmp_path / "products"
    products.mkdir()
    cases = []
    sources = {}
    ledger = {}
    for uid in UIDS:
        product = products / (f"{uid}.h5")
        manifest, record = _product(product, uid)
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
                    "banks": {"coarse/femur/signal": [5, 0, 3], **extra_banks},
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
    for case in configured["cases"]:
        if case["case_id"].startswith("squint-case:"):
            case["regions"] = copy.deepcopy(regions)
    save_memory(configured, tmp_path / "parent")
    snapshot = load_memory_snapshot(tmp_path / "parent")
    assert any(c["subject"].startswith("diagnosis/") for c in snapshot.memory["cases"])
    for product in products.glob("*.h5"):
        product.unlink()
    return SimpleNamespace(snapshot=snapshot, memory_dir=tmp_path / "parent")


def _fake_reader(log):
    np = pytest.importorskip("numpy")

    def reader(root, study, need, product):
        log.append((study, sorted(need["slices"]), sorted(need["supports"]), product))
        pixels = np.arange(1600, dtype=np.float32).reshape(40, 40)
        grid = np.zeros((4, 4, 4), dtype=np.int64)
        for r in range(4):
            for c in range(4):
                grid[r, c] = (r * 10, r * 10 + 10, c * 10, c * 10 + 10)
        images, territories = {}, {}
        for series, z in need["slices"]:
            if series == "ser-missing":
                images[(study, series, z)] = {"code": "series_missing"}
            else:
                images[(study, series, z)] = {
                    "code": "read",
                    "pixels": pixels,
                    "bounds_rc": grid,
                    "source_path": "/raw/" + series,
                }
        for subject, series, z in need["supports"]:
            if series == "ser-ok":
                territories[(study, subject, series, z)] = {
                    "code": "resolved",
                    "native_support": {
                        "mask": np.ones((1, 6, 6), dtype=bool),
                        "offset_rc": [12, 12],
                    },
                    "mask_sha256": "m" * 64,
                    "resolver": "fake",
                }
            else:
                territories[(study, subject, series, z)] = {
                    "code": "teacher_product_unrecorded"
                }
        return images, territories, {"seconds": 0.0}

    return reader


def _window(region):
    return region["window"]


@pytest.fixture
def exported(seed, tmp_path: Path) -> SimpleNamespace:
    pytest.importorskip("numpy")
    pytest.importorskip("matplotlib")
    log = []
    out = tmp_path / "export"
    result = MOD.export_review(
        seed.snapshot.memory,
        seed.snapshot.sha256,
        tmp_path / "root",
        out,
        image_reader=_fake_reader(log),
        window_of=_window,
    )
    return SimpleNamespace(out=out, result=result, log=log)


def write_calls(out: Path, items, reader: str = "reader-one", pin: str | None = None):
    if pin is None:
        pin = hashlib.sha256((out / "review.json").read_bytes()).hexdigest()
    document = {
        "schema": CALLS_SCHEMA,
        "review_sha256": pin,
        "reader": reader,
        "calls": [{"candidate_id": c, "call": v, "notes": "n"} for c, v in items],
    }
    path = out / "human-calls.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path, pin


def admit(seed, out: Path, calls_path: Path, output: Path):
    return MOD.run_admit(
        argparse.Namespace(
            memory=seed.memory_dir,
            review=out / "review.json",
            calls=calls_path,
            output=output,
        )
    )


# ---------------------------------------------------------------- selection


def test_selection_sorted_object_only_and_filters(seed):
    memory = seed.snapshot.memory
    ids = MOD.select_case_ids(memory)
    assert ids == sorted(cid(u) for u in UIDS)
    assert MOD.select_case_ids(memory, limit=2) == ids[:2]
    assert MOD.select_case_ids(memory, study_uids=["study-c"]) == [cid("study-c")]
    assert MOD.select_case_ids(memory, case_ids=[cid("study-d"), cid("study-b")]) == [
        cid("study-b"),
        cid("study-d"),
    ]
    config_id = next(
        c["case_id"] for c in memory["cases"] if c["subject"].startswith("diagnosis/")
    )
    assert (
        fail_code(MOD.select_case_ids, memory, case_ids=[config_id])
        == "case_id_not_object_case"
    )
    assert (
        fail_code(MOD.select_case_ids, memory, case_ids=["nope"]) == "case_id_unknown"
    )
    assert (
        fail_code(MOD.select_case_ids, memory, subjects=["patella"])
        == "no_object_cases_selected"
    )
    assert fail_code(MOD.select_case_ids, memory, limit=0) == "limit_invalid"


def test_parser_defaults_and_repeats():
    args = MOD._parser().parse_args(
        [
            "export",
            "--memory",
            "m",
            "--root",
            "r",
            "--output",
            "o",
            "--study-uid",
            "A",
            "--study-uid",
            "B",
        ]
    )
    assert args.limit == 12 and args.study_uids == ["A", "B"] and args.case_ids is None


# ------------------------------------------------------------------- export


def test_review_pin_is_over_exact_file_bytes_without_self_hash(seed, exported):
    out = exported.out
    raw = (out / "review.json").read_bytes()
    pin = hashlib.sha256(raw).hexdigest()
    review = json.loads(raw.decode("utf-8"))
    assert "review_sha256" not in review
    assert exported.result["review_sha256"] == pin
    assert pin in (out / "index.md").read_text(encoding="utf-8")
    template = json.loads((out / "calls.json").read_text(encoding="utf-8"))
    assert template["review_sha256"] == pin and template["reader"] == ""
    assert template["calls"] == []
    by_id = {c["case_id"]: c for c in seed.snapshot.memory["cases"]}
    assert [c["candidate_id"] for c in review["candidates"]] == sorted(
        cid(u) for u in UIDS
    )
    for candidate in review["candidates"]:
        case = by_id[candidate["candidate_id"]]
        assert not candidate["subject"].startswith("diagnosis/")
        assert candidate["case_id"] == case["case_id"]
        assert candidate["profile_sha256"] == _json_sha256(case["profile"])
        assert candidate["full_profile"] == case["full_profile"]
        assert (
            candidate["source_product_sha256"] == case["full_source"]["product_sha256"]
        )
        assert candidate["regions"] == case["regions"]
        assert candidate["proposed_identity"] == case["subject"]
        sheet = candidate["evidence"]["sheet"]
        data = (out / sheet["file"]).read_bytes()
        assert candidate["sheet_path"] == sheet["file"]
        assert data[:4] == bytes.fromhex("89504e47")
        assert hashlib.sha256(data).hexdigest() == sheet["sha256"]
    MOD.verify_sheets(review, out)


def test_export_uses_source_identity_addresses_and_labels_unavailable(seed, exported):
    identities = seed.snapshot.memory["source_identities"]
    assert len(exported.log) == len(UIDS)
    for study, _slices, _supports, product in exported.log:
        assert product == {
            "path": identities[study]["product_path"],
            "sha256": identities[study]["product_sha256"],
        }
    review = json.loads((exported.out / "review.json").read_text(encoding="utf-8"))
    panels = {p["view_label"]: p for p in review["candidates"][0]["evidence"]["panels"]}
    assert (
        panels["sag-pd"]["image_state"] == "read"
        and panels["sag-pd"]["support_state"] == "drawn"
    )
    assert panels["sag-pd"]["support_mask_sha256"] == "m" * 64
    assert panels["cor-t1"]["image_state"] == "read"
    assert panels["cor-t1"]["support_state"] == "teacher_product_unrecorded"
    assert panels["ax-t2"]["image_state"] == "series_missing"
    assert panels["ax-t2"]["support_state"] == "not_attempted"
    assert review["candidates"][0]["evidence"]["available_views"] == [
        "cor-t1",
        "sag-pd",
    ]
    index = (exported.out / "index.md").read_text(encoding="utf-8")
    assert "UNCALLED PROPOSAL" in index and "series_missing" in index


def test_source_product_fallback_and_mismatch(seed):
    memory = copy.deepcopy(seed.snapshot.memory)
    case = next(c for c in memory["cases"] if c["case_id"] == cid("study-a"))
    first = MOD.source_product(memory, case)
    assert first["origin"] == "source_identities"
    assert first["path"] == memory["source_identities"]["study-a"]["product_path"]
    del memory["source_identities"]["study-a"]
    second = MOD.source_product(memory, case)
    assert second["origin"] == "full_source"
    assert second["path"] == case["full_source"]["product_path"]
    assert second["sha256"] == case["full_source"]["product_sha256"]
    memory = copy.deepcopy(seed.snapshot.memory)
    memory["source_identities"]["study-a"]["product_sha256"] = "0" * 64
    case = next(c for c in memory["cases"] if c["case_id"] == cid("study-a"))
    assert fail_code(MOD.source_product, memory, case) == "source_product_mismatch"


def test_reader_failure_is_labelled_not_invented(seed, tmp_path):
    pytest.importorskip("numpy")
    pytest.importorskip("matplotlib")

    def broken(root, study, need, product):
        raise ValueError("study_read_boom")

    out = tmp_path / "broken-export"
    MOD.export_review(
        seed.snapshot.memory,
        seed.snapshot.sha256,
        tmp_path,
        out,
        case_ids=[cid("study-a")],
        image_reader=broken,
        window_of=_window,
    )
    review = json.loads((out / "review.json").read_text(encoding="utf-8"))
    evidence = review["candidates"][0]["evidence"]
    assert evidence["read_receipt"]["status"] == "failed"
    assert evidence["available_views"] == []
    assert {p["image_state"] for p in evidence["panels"]} == {"study_read_failed"}
    assert {p["support_state"] for p in evidence["panels"]} == {"not_attempted"}


def test_export_refuses_existing_output(seed, tmp_path):
    out = tmp_path / "there"
    out.mkdir()
    code = fail_code(
        MOD.export_review,
        seed.snapshot.memory,
        seed.snapshot.sha256,
        tmp_path,
        out,
        image_reader=lambda *a: ({}, {}, None),
        window_of=_window,
    )
    assert code == "export_output_exists"


# ---------------------------------------------------------------- admission


def test_admit_publishes_only_confirmed_and_keeps_call_evidence(
    seed, exported, tmp_path
):
    before = copy.deepcopy(seed.snapshot.memory)
    ids = [cid(u) for u in UIDS]
    items = [
        (ids[0], "confirm"),
        (ids[1], "confirm"),
        (ids[2], "reject"),
        (ids[3], "unsure"),
    ]
    calls_path, pin = write_calls(exported.out, items)
    output = tmp_path / "child"
    result = admit(seed, exported.out, calls_path, output)
    assert result["outcome"] == "published" and result["review_sha256"] == pin
    assert result["confirmed_case_ids"] == ids[:2]
    child = load_memory(output)
    parent_cases = {c["case_id"]: c for c in before["cases"]}
    assert [c["case_id"] for c in child["cases"]] == ids[:2]
    for case in child["cases"]:
        assert case == parent_cases[case["case_id"]]
        assert case["condition_calls"] == {"ACL": 1}
        assert not case["subject"].startswith("diagnosis/")
        profile = full_profile_from_case(child, case)
        assert profile.source_id == case["study_uid"]
    teaching = child["object_identity_teaching"]
    assert teaching["schema"] == TEACHING_SCHEMA
    assert teaching["review_sha256"] == pin
    assert teaching["source_manifest_sha256"] == seed.snapshot.sha256
    assert teaching["confirmed_case_ids"] == ids[:2]
    assert {c["candidate_id"]: c["call"] for c in teaching["calls"]} == {
        ids[0]: "confirm",
        ids[1]: "confirm",
        ids[2]: "reject",
        ids[3]: "unsure",
    }
    assert ids[4] not in {c["candidate_id"] for c in teaching["calls"]}
    assert ids[4] in teaching["reviewed_candidate_ids"]
    # The fixture's drawn panels carry no exact view triple: the reject has no
    # drawn profile view to oppose, writes no negative case and says why.
    assert teaching["negative_case_ids"] == []
    assert teaching["negatives_not_written"] == [
        {"candidate_id": ids[2], "reason": "no_drawn_profile_view"}
    ]
    assert child["object_identity_cases"]["cases"] == []
    assert set(child["source_identities"]) == {"study-a", "study-b"}
    assert seed.snapshot.memory == before


def test_admit_through_main_prints_result(seed, exported, tmp_path, capsys):
    ids = [cid(u) for u in UIDS]
    calls_path, pin = write_calls(exported.out, [(ids[4], "confirm")])
    output = tmp_path / "child-main"
    result = MOD.main(
        [
            "admit",
            "--memory",
            str(seed.memory_dir),
            "--review",
            str(exported.out / "review.json"),
            "--calls",
            str(calls_path),
            "--output",
            str(output),
        ]
    )
    printed = json.loads(capsys.readouterr().out)
    assert printed["review_sha256"] == pin == result["review_sha256"]
    assert [c["case_id"] for c in load_memory(output)["cases"]] == [ids[4]]


def test_omitted_calls_are_accepted_as_uncalled(seed, exported):
    review = json.loads((exported.out / "review.json").read_text(encoding="utf-8"))
    pin = hashlib.sha256((exported.out / "review.json").read_bytes()).hexdigest()
    ids = [cid(u) for u in UIDS]
    doc = {
        "schema": CALLS_SCHEMA,
        "review_sha256": pin,
        "reader": "reader-one",
        "calls": [],
    }
    assert validate_calls(review, doc, pin)["confirmed_case_ids"] == []
    doc["calls"] = [{"candidate_id": ids[2], "call": "confirm", "notes": ""}]
    assert validate_calls(review, doc, pin)["confirmed_case_ids"] == [ids[2]]


@pytest.mark.parametrize("kind", ["empty", "reject_unsure"])
def test_no_identity_case_written_is_refused_and_nothing_written(
    seed, exported, tmp_path, kind
):
    # The fixture's drawn panels carry no exact view triple, so the reject has
    # no drawn profile view to oppose and writes no negative case.
    ids = [cid(u) for u in UIDS]
    items = [] if kind == "empty" else [(ids[0], "reject"), (ids[1], "unsure")]
    calls_path, _ = write_calls(exported.out, items)
    output = tmp_path / "child"
    assert (
        shared_code(admit, seed, exported.out, calls_path, output)
        == "no_identity_cases_written"
    )
    assert not output.exists()


def test_main_reports_refusal_code(seed, exported, tmp_path):
    calls_path, _ = write_calls(exported.out, [])
    with pytest.raises(SystemExit) as info:
        MOD.main(
            [
                "admit",
                "--memory",
                str(seed.memory_dir),
                "--review",
                str(exported.out / "review.json"),
                "--calls",
                str(calls_path),
                "--output",
                str(tmp_path / "child"),
            ]
        )
    assert str(info.value) == "no_identity_cases_written"


def test_sheet_tamper_is_refused(seed, exported, tmp_path):
    ids = [cid(u) for u in UIDS]
    calls_path, _ = write_calls(exported.out, [(ids[0], "confirm")])
    review = json.loads((exported.out / "review.json").read_text(encoding="utf-8"))
    sheet = exported.out / review["candidates"][1]["sheet_path"]
    sheet.write_bytes(sheet.read_bytes() + b"x")
    output = tmp_path / "child"
    assert (
        fail_code(admit, seed, exported.out, calls_path, output)
        == "review_sheet_sha256_mismatch"
    )
    assert not output.exists()


@pytest.mark.parametrize("escape", ["parent", "absolute"])
def test_sheet_path_escape_is_refused(seed, exported, tmp_path, escape):
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"png")
    review_path = exported.out / "review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    target = "../outside.png" if escape == "parent" else str(outside)
    review["candidates"][0]["sheet_path"] = target
    review["candidates"][0]["evidence"]["sheet"]["file"] = target
    review["candidates"][0]["evidence"]["sheet"]["sha256"] = hashlib.sha256(
        b"png"
    ).hexdigest()
    review_path.write_bytes(MOD._json_bytes(review))
    calls_path, _ = write_calls(exported.out, [(cid(UIDS[0]), "confirm")])
    output = tmp_path / "child"
    assert (
        fail_code(admit, seed, exported.out, calls_path, output)
        == "review_sheet_path_escape"
    )
    assert not output.exists()


def test_review_with_self_hash_field_is_refused(seed, exported, tmp_path):
    review_path = exported.out / "review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review["review_sha256"] = "a" * 64
    review_path.write_bytes(MOD._json_bytes(review))
    calls_path, _ = write_calls(exported.out, [(cid(UIDS[0]), "confirm")])
    assert (
        fail_code(admit, seed, exported.out, calls_path, tmp_path / "child")
        == "review_self_hash_present"
    )


def test_stale_review_pin_is_refused(seed, exported, tmp_path):
    ids = [cid(u) for u in UIDS]
    output = tmp_path / "child"
    calls_path, _ = write_calls(exported.out, [(ids[0], "confirm")], pin="0" * 64)
    assert (
        shared_code(admit, seed, exported.out, calls_path, output) == "stale_review_pin"
    )
    good_path, _ = write_calls(exported.out, [(ids[0], "confirm")])
    review_path = exported.out / "review.json"
    review_path.write_bytes(review_path.read_bytes() + b" ")
    assert (
        shared_code(admit, seed, exported.out, good_path, output) == "stale_review_pin"
    )
    assert not output.exists()


def test_stale_source_pin_is_refused(seed, exported, tmp_path):
    review_path = exported.out / "review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review["source_manifest_sha256"] = "f" * 64
    review_path.write_bytes(MOD._json_bytes(review))
    calls_path, _ = write_calls(exported.out, [(cid(UIDS[0]), "confirm")])
    output = tmp_path / "child"
    assert (
        shared_code(admit, seed, exported.out, calls_path, output) == "stale_source_pin"
    )
    assert not output.exists()


def test_empty_reader_is_refused(seed, exported, tmp_path):
    calls_path, _ = write_calls(exported.out, [(cid(UIDS[0]), "confirm")], reader="")
    assert (
        shared_code(admit, seed, exported.out, calls_path, tmp_path / "child")
        == "calls_malformed"
    )


def test_admit_publishes_a_negative_case_on_the_drawn_view(seed_views, tmp_path):
    pytest.importorskip("numpy")
    pytest.importorskip("matplotlib")
    out = tmp_path / "export-views"
    MOD.export_review(
        seed_views.snapshot.memory,
        seed_views.snapshot.sha256,
        tmp_path / "root",
        out,
        image_reader=_fake_reader([]),
        window_of=_window,
    )
    review = json.loads((out / "review.json").read_text(encoding="utf-8"))
    sagittal = ["Sagittal", "0", "0"]
    assert review["candidates"][0]["profile_views"] == [sagittal]
    ids = [cid(u) for u in UIDS]
    calls_path, pin = write_calls(out, [(ids[0], "confirm"), (ids[1], "reject")])
    output = tmp_path / "child-views"
    result = admit(seed_views, out, calls_path, output)
    assert result["confirmed_case_ids"] == [ids[0]]
    assert result["negative_case_ids"] == [ids[1]]
    child = load_memory(output)
    assert [case["case_id"] for case in child["cases"]] == [ids[0]]
    parent = {case["case_id"]: case for case in seed_views.snapshot.memory["cases"]}
    assert child["object_identity_cases"]["cases"] == [parent[ids[1]]]
    teaching = child["object_identity_teaching"]
    assert teaching["negative_views"] == {ids[1]: [sagittal]}
    assert teaching["review_sha256"] == pin
    prepared = prepare_identity(child)
    assert prepared["seed_count"] == 1 and prepared["negative_case_count"] == 1
