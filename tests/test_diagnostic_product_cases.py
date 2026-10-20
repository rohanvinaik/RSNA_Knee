from __future__ import annotations

import json
from pathlib import Path

import pytest

from knee.array_archive import write_npz_xz
from knee.diagnosis import product_cases
from knee.diagnosis.composition import CompositionError, compose_question_profile
from knee.diagnosis.models import Question
from knee.diagnosis.product_cases import ProductProfileError, profiles_from_product
from knee.encoding import h5_store
from knee.encoding.places import (
    BankSpec,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    compile_layout,
)
from knee.json_store import dump_json_atomic


def _fixture_manifest() -> dict:
    spec = LayoutSpec(
        "retained-v1",
        "carrier-retained-v1",
        (
            BankSpec(
                "signal", "signal facet", (MetricSpec("tone", MetricKind.DIGIT, ()),)
            ),
        ),
    )
    compiled = compile_layout(spec)
    assert compiled is not None
    reference = "reference:signal:v1"
    count_id = f"{compiled.version}:{compiled.fingerprint}:{reference}"
    return {
        "study_uid": "study-001",
        "encoded_arrays": {},
        "object_composition": {
            "schema": "knee_object_profiles/v1",
            "carrier_identity": compiled.carrier_id,
            "layout_fingerprint": compiled.fingerprint,
            "registry_fingerprint": "registry-digest",
            "layout": {
                "version": compiled.version,
                "carrier_id": compiled.carrier_id,
                "fingerprint": compiled.fingerprint,
                "banks": [
                    {
                        "name": "signal",
                        "facet": "signal facet",
                        "metrics": [{"name": "tone", "kind": "digit", "words": []}],
                    }
                ],
            },
            "registry": [],
            "objects": {
                "joint_fluid": {
                    "status": "partial",
                    "preparation_status": "ok",
                    "detail": "",
                    "reference_set_identity": reference,
                    "count_layout_id": count_id,
                    "sparse_counts": [["signal", 4, 2], ["signal", 9, 1]],
                    "assembly": {
                        "code": "partial",
                        "outcomes": ["partial", "silent"],
                        "batches": [{"bank": "signal", "status": "partial"}],
                        "conflicts": [],
                        "mismatches": [],
                        "malformed": [],
                    },
                    "batch_index_maps": [],
                    "spatial_context": None,
                }
            },
            "additions": [],
        },
    }


def _write_product(tmp_path: Path, fmt: str) -> Path:
    manifest = _fixture_manifest()
    if fmt == "h5":
        pytest.importorskip("h5py")
        path = tmp_path / "product.h5"
        h5_store.write_h5(path, manifest, {})
        return path
    archive = tmp_path / "product.npz.xz"
    write_npz_xz(archive, ())
    manifest["archive"] = archive.name
    path = tmp_path / "product.json.xz"
    dump_json_atomic(path, manifest)
    return path


@pytest.mark.parametrize("fmt", ["h5", "legacy"])
def test_profiles_from_public_product_reader_returns_detached_unified_bundle(
    tmp_path, fmt
):
    path = _write_product(tmp_path, fmt)
    profiles = profiles_from_product(path)
    assert len(profiles) == 1
    profile = profiles[0]
    assert profile.subject == "joint_fluid"
    assert profile.source_id == "study-001"
    assert profile.mode == "full"
    assert profile.bundle.layout.layout_id.endswith("reference:signal:v1")
    assert profile.bundle.counts[0][4] == 2
    assert profile.bundle.counts[0][9] == 1
    assert sum(profile.bundle.counts[0]) == 3
    assert profile.bank_statuses == (("signal", "partial"),)
    assert dict(profile.provenance)["reference_set_identity"] == "reference:signal:v1"


def test_profiles_from_product_preserves_missing_reference_as_named_error(tmp_path):
    path = _write_product(tmp_path, "legacy")
    manifest = _fixture_manifest()
    object_record = manifest["object_composition"]["objects"]["joint_fluid"]
    object_record["count_layout_id"] = None
    object_record["reference_set_identity"] = None
    object_record["assembly"] = None
    object_record["status"] = "missing_reference"
    object_record["preparation_status"] = "missing_reference"
    dump_json_atomic(path, {**manifest, "archive": "product.npz.xz"})
    with pytest.raises(ProductProfileError, match="count_layout_id_missing"):
        profiles_from_product(path)


def test_profiles_from_product_rejects_mode_and_schema_errors(tmp_path):
    path = _write_product(tmp_path, "legacy")
    with pytest.raises(ProductProfileError, match="mode_unsupported"):
        profiles_from_product(path, mode="unknown")
    manifest = _fixture_manifest()
    manifest["object_composition"]["schema"] = "future/v2"
    dump_json_atomic(path, {**manifest, "archive": "product.npz.xz"})
    with pytest.raises(ProductProfileError, match="schema_unsupported"):
        profiles_from_product(path)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda manifest: manifest["object_composition"]["layout"][
                "banks"
            ].__setitem__(0, None),
            "layout_invalid:bank_not_object",
        ),
        (
            lambda manifest: manifest["object_composition"]["layout"]["banks"][0][
                "metrics"
            ].__setitem__(0, None),
            "layout_invalid:metric_not_object",
        ),
    ],
)
def test_non_object_layout_entries_keep_named_public_errors(mutate, message):
    manifest = _fixture_manifest()
    mutate(manifest)
    with pytest.raises(ProductProfileError, match=message):
        product_cases._profiles(manifest, "full")


def test_duplicate_batch_statuses_consolidate_with_full_batch_ledger():
    manifest = _fixture_manifest()
    record = manifest["object_composition"]["objects"]["joint_fluid"]
    record["assembly"]["batches"] = [
        {"bank": "signal", "status": "partial", "observation": "sagittal-a"},
        {
            "bank": "signal",
            "status": "unavailable_new_state",
            "observation": "coronal-b",
        },
        {"bank": "signal", "status": "silent", "observation": "axial-c"},
    ]

    profile = product_cases._profiles(manifest, "full")[0]

    assert profile.bank_statuses == (
        ("signal", 'batch_statuses:["partial","silent","unavailable_new_state"]'),
    )
    provenance = dict(profile.provenance)
    ledger = json.loads(provenance["assembly_batch_ledger"])
    assert ledger == [
        {
            "batch_index": 0,
            "batch": {
                "bank": "signal",
                "status": "partial",
                "observation": "sagittal-a",
            },
        },
        {
            "batch_index": 1,
            "batch": {
                "bank": "signal",
                "status": "unavailable_new_state",
                "observation": "coronal-b",
            },
        },
        {
            "batch_index": 2,
            "batch": {"bank": "signal", "status": "silent", "observation": "axial-c"},
        },
    ]
    question = Question("joint_fluid", "diagnosis/joint_fluid", ("joint_fluid",))
    composed = compose_question_profile((profile,), question)
    assert len(dict(composed.bank_statuses)) == len(composed.bank_statuses)


def test_batch_conflict_remains_recognizable_to_composer():
    manifest = _fixture_manifest()
    record = manifest["object_composition"]["objects"]["joint_fluid"]
    record["assembly"]["batches"] = [
        {"bank": "signal", "status": "partial", "observation": "a"},
        {"bank": "signal", "status": "conflicting", "observation": "b"},
    ]

    profile = product_cases._profiles(manifest, "full")[0]

    assert profile.bank_statuses == (("signal", "conflicting"),)
    with pytest.raises(CompositionError, match="conflicting_source:joint_fluid:signal"):
        compose_question_profile(
            (profile,),
            Question("joint_fluid", "diagnosis/joint_fluid", ("joint_fluid",)),
        )


def _large_composition_manifest(object_count: int = 44, bank_count: int = 3696) -> dict:
    layout_spec = LayoutSpec(
        "retained-large-v1",
        "carrier-retained-large-v1",
        tuple(
            BankSpec(
                f"bank/{index:04d}",
                "measured-content",
                (MetricSpec("tone", MetricKind.DIGIT, ()),),
            )
            for index in range(bank_count)
        ),
    )
    compiled = compile_layout(layout_spec)
    assert compiled is not None
    reference = "reference:large:v1"
    count_id = f"{compiled.version}:{compiled.fingerprint}:{reference}"
    layout = {
        "version": compiled.version,
        "carrier_id": compiled.carrier_id,
        "fingerprint": compiled.fingerprint,
        "banks": [
            {
                "name": bank.name,
                "facet": bank.facet,
                "metrics": [
                    {"name": metric.name, "kind": metric.kind.value, "words": []}
                    for metric in bank.metrics
                ],
            }
            for bank in layout_spec.banks
        ],
    }
    objects = {
        f"object_{index:02d}": {
            "status": "partial",
            "preparation_status": "ok",
            "reference_set_identity": reference,
            "count_layout_id": count_id,
            "sparse_counts": [["bank/0000", 4, index + 1]],
            "assembly": {
                "code": "partial",
                "batches": [{"bank": "bank/0000", "status": "partial"}],
            },
        }
        for index in range(object_count)
    }
    return {
        "study_uid": "large-study",
        "object_composition": {
            "schema": "knee_object_profiles/v1",
            "carrier_identity": compiled.carrier_id,
            "layout_fingerprint": compiled.fingerprint,
            "registry_fingerprint": "large-registry",
            "layout": layout,
            "objects": objects,
        },
    }


def test_profiles_reuse_one_compilation_layout_and_zero_row_across_44_objects(
    monkeypatch,
):
    manifest = _large_composition_manifest()
    real_compile = product_cases.compile_layout
    compile_calls = 0

    def counted_compile(spec):
        nonlocal compile_calls
        compile_calls += 1
        return real_compile(spec)

    monkeypatch.setattr(product_cases, "compile_layout", counted_compile)
    profiles = product_cases._profiles(manifest, "full")

    assert compile_calls == 1
    assert len(profiles) == 44
    assert all(len(profile.bundle.layout.banks) == 3696 for profile in profiles)
    assert all(
        all(bank.row_count == 512 for bank in profile.bundle.layout.banks)
        for profile in profiles
    )
    assert tuple(bank.name for bank in profiles[0].bundle.layout.banks) == tuple(
        f"bank/{index:04d}" for index in range(3696)
    )
    assert all(
        profile.bundle.layout is profiles[0].bundle.layout for profile in profiles
    )
    assert all(
        profile.bundle.counts[1] is profiles[0].bundle.counts[1] for profile in profiles
    )
    assert profiles[0].bundle.counts[0][4] == 1
    assert profiles[-1].bundle.counts[0][4] == 44
    assert sum(map(sum, profiles[0].bundle.counts)) == 1
    assert sum(map(sum, profiles[-1].bundle.counts)) == 44


def test_sparse_bundle_matches_dense_reference_and_preserves_full_bank_layout():
    manifest = _fixture_manifest()
    composition = manifest["object_composition"]
    composition["layout"]["banks"].append(
        {
            "name": "context",
            "facet": "context facet",
            "metrics": [{"name": "view", "kind": "digit", "words": []}],
        }
    )
    spec = LayoutSpec(
        "retained-v1",
        "carrier-retained-v1",
        (
            BankSpec(
                "signal", "signal facet", (MetricSpec("tone", MetricKind.DIGIT, ()),)
            ),
            BankSpec(
                "context", "context facet", (MetricSpec("view", MetricKind.DIGIT, ()),)
            ),
        ),
    )
    compiled = compile_layout(spec)
    assert compiled is not None
    composition["layout"].update(fingerprint=compiled.fingerprint)
    composition["layout_fingerprint"] = compiled.fingerprint
    composition["objects"]["joint_fluid"].update(
        count_layout_id=f"{compiled.version}:{compiled.fingerprint}:reference:signal:v1",
        sparse_counts=[["signal", 4, 2], ["signal", 4, 3], ["signal", 9, 1]],
    )
    profile = product_cases._profiles(manifest, "full")[0]

    expected_signal = [0] * 512
    expected_signal[4] = 5
    expected_signal[9] = 1
    assert profile.bundle.layout.banks == compiled.count_layout.banks
    assert profile.bundle.counts == (tuple(expected_signal), (0,) * 512)
    assert len(profile.bundle.layout.banks) == 2


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda manifest: manifest["object_composition"]["layout"].update(
                fingerprint="wrong"
            ),
            "layout_fingerprint_mismatch",
        ),
        (
            lambda manifest: manifest["object_composition"]["objects"][
                "joint_fluid"
            ].update(sparse_counts=[["unknown", 0, 1]]),
            "sparse_count_unknown_bank",
        ),
        (
            lambda manifest: manifest["object_composition"]["objects"][
                "joint_fluid"
            ].update(sparse_counts=[["signal", 512, 1]]),
            "sparse_count_out_of_range",
        ),
    ],
)
def test_layout_and_sparse_corruption_remain_named(mutate, message):
    manifest = _fixture_manifest()
    mutate(manifest)
    with pytest.raises(ProductProfileError, match=message):
        product_cases._profiles(manifest, "full")
