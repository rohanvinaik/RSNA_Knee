"""Adapter contract tests; packed slicing itself belongs to the shared primitive."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

import knee.encoding.packed_adapter as adapter_module
from knee.encoding.operation import encode_study, validate_spec
from knee.encoding.packed_adapter import PackedSupportLayout, encode_packed_observation
from knee.encoding.places import (
    BankSpec,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    NumericReference,
    compile_layout,
)
from knee.receipt import digest


@pytest.fixture
def case():
    arrays = {
        "offsets": np.asarray([0, 4, 7], dtype=np.int64),
        "shapes": np.asarray([[2, 2], [1, 3]], dtype=np.int32),
        "slices": np.asarray([7, 10], dtype=np.int32),
        "region": np.asarray([False, True, True, False, True, False, True]),
        "target": np.asarray([False, True, False, False, True, False, False]),
        "values": np.asarray([-2.0, 0.5, 2.0, 8.0, -1.0, 0.5, 3.0]),
        "available": np.ones(7, dtype=bool),
        "origin": np.asarray([[0.0, 0.0, 0.0], [1.0, 2.0, 3.0]]),
        "basis": np.stack([np.eye(3)[:, :2], np.eye(3)[:, :2]]),
        "normal": np.asarray([[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]]),
        "thickness": np.asarray([2.0, 2.5]),
    }
    owner = "fibula-owner"
    target = "axial-target"
    study_uid = "study-1"
    observation = {
        "object": "fibula",
        "provenance": "native",
        "kind": "reading",
        "artifact": f"{study_uid}/{owner}-fibula.npz.xz",
        "series_uid": target,
        "view": ["Axial", "1", "1"],
        "slices": [10],
        "row": 1,
        "support": "region",
        "label": None,
        "code": "picked",
        "count": 1,
    }
    record = {
        "study_uid": study_uid,
        "artifact": f"{study_uid}/{owner}-fibula.npz.xz",
        "series_uid": owner,
        "arrays": {name: {"digest": digest(array)} for name, array in arrays.items()},
        "axial_evidence": [
            {
                "series_uid": target,
                "view": ["Axial", "1", "1"],
                "slice": 7,
                "row": None,
                "code": "no_labels",
                "target_pixels": 0,
                "region_pixels": 0,
            },
            {
                "series_uid": target,
                "view": ["Axial", "1", "1"],
                "slice": 10,
                "row": 1,
                "code": "picked",
                "target_pixels": 1,
                "region_pixels": 2,
            },
        ],
    }
    spec = LayoutSpec(
        "test-v1",
        "carrier-test",
        (BankSpec("signal", "value", (MetricSpec("intensity", MetricKind.DIGIT),)),),
    )
    layout = compile_layout(spec)
    assert layout is not None
    reference = NumericReference(
        layout.fingerprint, "signal", "intensity", "ref-1", "fixture", "a.u.", 0.0, 1.0
    )
    packed = PackedSupportLayout(
        family="fibula_axial",
        owner_series_uid=owner,
        target_series_uid=target,
        target_view=("Axial", "1", "1"),
        offsets="offsets",
        shapes="shapes",
        slices="slices",
        packed_arrays=("region", "target", "values", "available"),
        target_pixels_array="target",
        frame_arrays={
            "origin_lps": "origin",
            "basis_lps": "basis",
            "normal_lps": "normal",
            "thickness_mm": "thickness",
        },
        count_meaning="fibula_axial_target_pixels",
    )
    bindings = (
        {
            "bank": "signal",
            "metric": "intensity",
            "value": "values",
            "available": "available",
        },
    )
    return (
        record,
        observation,
        arrays,
        layout,
        bindings,
        {("signal", "intensity"): reference},
        packed,
    )


def test_decodes_native_row_and_keeps_count_and_owner_semantics_separate(case):
    record, observation, arrays, layout, bindings, references, packed = case
    result = encode_packed_observation(
        record, observation, arrays, layout, bindings, references, packed
    )

    assert result.encoding is not None
    assert result.points_rc.tolist() == [[0, 0], [0, 2]]
    assert result.metadata["source_owner_series_uid"] == "fibula-owner"
    assert result.metadata["target_series_uid"] == "axial-target"
    assert result.metadata["packed_slice_index"] == 10
    assert result.metadata["declared_count"] == 1
    assert result.metadata["declared_count_meaning"] == "fibula_axial_target_pixels"
    assert result.metadata["packed_target_count"] == 1
    assert result.metadata["decoded_support_count"] == 2
    assert result.metadata["plane_frame"]["origin_lps"] == [1.0, 2.0, 3.0]


def test_slice_mismatch_refuses_before_decoding(case, monkeypatch):
    record, observation, arrays, layout, bindings, references, packed = case
    observation["slices"] = [11]
    calls = []
    original = adapter_module.read_packed_plane

    def spy(*args):
        calls.append(args)
        return original(*args)

    monkeypatch.setattr("knee.encoding.packed_adapter.read_packed_plane", spy)

    result = encode_packed_observation(
        record, observation, arrays, layout, bindings, references, packed
    )

    assert result.status == "packed_slice_mismatch"
    assert not calls


def test_owner_and_target_addresses_are_independently_checked(case):
    record, observation, arrays, layout, bindings, references, packed = case
    wrong_owner = dict(record, series_uid="other-owner")
    result = encode_packed_observation(
        wrong_owner, observation, arrays, layout, bindings, references, packed
    )
    assert result.status == "invalid_owner_identity"

    wrong_target = dict(observation, series_uid="other-target")
    result = encode_packed_observation(
        record, wrong_target, arrays, layout, bindings, references, packed
    )
    assert result.status == "target_series_mismatch"


def test_count_is_checked_against_retained_target_and_region_evidence(case):
    record, observation, arrays, layout, bindings, references, packed = case
    observation["count"] = 2
    result = encode_packed_observation(
        record, observation, arrays, layout, bindings, references, packed
    )
    assert result.status == "target_count_mismatch"

    observation["count"] = 1
    record["axial_evidence"][1]["region_pixels"] = 1
    result = encode_packed_observation(
        record, observation, arrays, layout, bindings, references, packed
    )
    assert result.status == "region_count_mismatch"


def test_duplicate_retained_row_evidence_is_refused(case):
    record, observation, arrays, layout, bindings, references, packed = case
    record["axial_evidence"].append(dict(record["axial_evidence"][1]))
    result = encode_packed_observation(
        record, observation, arrays, layout, bindings, references, packed
    )
    assert result.status == "packed_evidence_missing"


def test_bad_packed_array_digest_refuses(case):
    record, observation, arrays, layout, bindings, references, packed = case
    arrays = dict(arrays)
    arrays["region"] = arrays["region"].copy()
    arrays["region"][0] = not arrays["region"][0]
    result = encode_packed_observation(
        record, observation, arrays, layout, bindings, references, packed
    )
    assert result.status == "digest_mismatch"


def test_source_and_derived_digest_each_run_once(case, monkeypatch):
    record, observation, arrays, layout, bindings, references, packed = case
    original_digest = adapter_module.digest
    calls = []

    def counted(array):
        calls.append(id(array))
        return original_digest(array)

    monkeypatch.setattr(adapter_module, "digest", counted)
    result = encode_packed_observation(
        record, observation, arrays, layout, bindings, references, packed
    )

    assert result.encoding is not None
    assert len(calls) == len(set(calls))


def test_actual_retained_fibula_axial_artifact(case):
    from knee.array_archive import open_arrays

    receipt_path = Path(
        "data/readings/collapse-20261017/full-build/targeted-compute-20261018/"
        "b9b10-integrated-20261019/cohort/labeled-workers4-no-draw/main/receipt.json"
    )
    if not receipt_path.is_file():
        pytest.skip("the saved B9/B10 retained cohort is unavailable")
    receipt = json.loads(receipt_path.read_text())
    record = next(
        item
        for item in receipt["records"]
        if "a3_fibula_axial_region" in item["arrays"]
    )
    observation = next(
        item
        for item in record["observations"]
        if item.get("support") == "a3_fibula_axial_region"
    )
    array_names = (
        "a3_fibula_axial_offsets",
        "a3_fibula_axial_shapes",
        "a3_fibula_axial_slices",
        "a3_fibula_axial_region",
        "a3_fibula_axial_target",
        "a3_fibula_axial_available",
        "a3_fibula_axial_origin_lps",
        "a3_fibula_axial_basis_lps",
        "a3_fibula_axial_normal_lps",
        "a3_fibula_axial_thickness_mm",
    )
    artifact_path = receipt_path.parent / record["artifact"]
    with open_arrays(artifact_path) as archive:
        arrays = {name: archive[name] for name in array_names}
    spec = LayoutSpec(
        "retained-fibula-bool-v1",
        "test-carrier",
        (
            BankSpec(
                "target",
                "retained target mask",
                (MetricSpec("inside_target", MetricKind.WORDS, ("False", "True")),),
            ),
        ),
    )
    layout = compile_layout(spec)
    assert layout is not None
    packed = PackedSupportLayout(
        family="fibula_axial",
        owner_series_uid=record["series_uid"],
        target_series_uid=observation["series_uid"],
        target_view=tuple(observation["view"]),
        offsets="a3_fibula_axial_offsets",
        shapes="a3_fibula_axial_shapes",
        slices="a3_fibula_axial_slices",
        packed_arrays=(
            "a3_fibula_axial_region",
            "a3_fibula_axial_target",
            "a3_fibula_axial_available",
        ),
        target_pixels_array="a3_fibula_axial_target",
        frame_arrays={
            "origin_lps": "a3_fibula_axial_origin_lps",
            "basis_lps": "a3_fibula_axial_basis_lps",
            "normal_lps": "a3_fibula_axial_normal_lps",
            "thickness_mm": "a3_fibula_axial_thickness_mm",
        },
        count_meaning="fibula_axial_target_pixels",
    )
    result = encode_packed_observation(
        record,
        observation,
        arrays,
        layout,
        (
            {
                "bank": "target",
                "metric": "inside_target",
                "value": "a3_fibula_axial_target",
                "available": "a3_fibula_axial_available",
            },
        ),
        {},
        packed,
    )
    assert result.encoding is not None
    assert result.status == "ok"
    assert result.metadata["source_owner_series_uid"] == record["series_uid"]
    assert result.metadata["target_series_uid"] == observation["series_uid"]
    assert result.metadata["packed_target_count"] == 62
    assert result.metadata["decoded_support_count"] == 1784
    assert (
        result.metadata["plane_frame"]["basis_lps"]
        and len(result.metadata["plane_frame"]["basis_lps"]) == 3
    )
    assert len(result.metadata["plane_frame"]["basis_lps"][0]) == 2


def test_encode_study_uses_declared_packed_layout_on_retained_artifact(tmp_path):
    receipt_path = Path(
        "data/readings/collapse-20261017/full-build/targeted-compute-20261018/"
        "b9b10-integrated-20261019/cohort/labeled-workers4-no-draw/main/receipt.json"
    )
    if not receipt_path.is_file():
        pytest.skip("the saved B9/B10 retained cohort is unavailable")
    receipt = json.loads(receipt_path.read_text())
    record = next(
        item
        for item in receipt["records"]
        if "a3_fibula_axial_region" in item["arrays"]
    )
    spec = {
        "version": "fibula-axial-packed-test-v1",
        "banks": [
            {
                "name": "target",
                "facet": "retained target mask",
                "metrics": [
                    {
                        "name": "inside_target",
                        "kind": "words",
                        "words": ["False", "True"],
                    }
                ],
            }
        ],
        "profiles": [
            {
                "object": "fibula",
                "provenance": "native",
                "kind": "reading",
                "support": "a3_fibula_axial_region",
                "readings": [
                    {
                        "bank": "target",
                        "metric": "inside_target",
                        "value": "a3_fibula_axial_target",
                        "available": "a3_fibula_axial_available",
                    }
                ],
                "support_layout": {
                    "family": "fibula_axial",
                    "identity_sources": {
                        "owner_series_uid": "record.series_uid",
                        "artifact": "record.artifact",
                        "target_series_uid": "axial_evidence.series_uid",
                        "target_view": "axial_evidence.view",
                        "target_slice": "axial_evidence.slice",
                        "row": "observation.row_to_axial_evidence.row",
                    },
                    "offsets": "a3_fibula_axial_offsets",
                    "shapes": "a3_fibula_axial_shapes",
                    "slices": "a3_fibula_axial_slices",
                    "packed_arrays": [
                        "a3_fibula_axial_region",
                        "a3_fibula_axial_target",
                        "a3_fibula_axial_available",
                    ],
                    "target_pixels_array": "a3_fibula_axial_target",
                    "frame_arrays": {
                        "origin_lps": "a3_fibula_axial_origin_lps",
                        "basis_lps": "a3_fibula_axial_basis_lps",
                        "normal_lps": "a3_fibula_axial_normal_lps",
                        "thickness_mm": "a3_fibula_axial_thickness_mm",
                    },
                    "count_meaning": "fibula_axial_target_pixels",
                },
            }
        ],
    }
    validated = validate_spec(spec)
    profile = validated["profiles"][0]
    assert profile["support_layout"]["family"] == "fibula_axial"

    outputs = encode_study(
        {
            "study_uid": record["study_uid"],
            "records": [],
            "main_records": [record],
            "objects": {"fibula": {}},
        },
        tmp_path / "interiors",
        receipt_path.parent,
        validated["spec"],
        tmp_path / "fibula-encoding.json",
        prepared=validated,
    )

    outcome = outputs["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "ok"
    assert outcome["metadata"]["declared_count"] == 62
    assert outcome["metadata"]["decoded_support_count"] == 1784
    assert outcome["metadata"]["source_owner_series_uid"] == record["series_uid"]
    assert (
        outcome["metadata"]["target_series_uid"]
        == record["axial_evidence"][0]["series_uid"]
    )
    assert outputs["work"]["addressed_places"] == 1784


def test_support_layout_cannot_be_reused_for_other_families():
    spec = {
        "version": "invalid-v1",
        "banks": [
            {
                "name": "target",
                "facet": "target",
                "metrics": [
                    {"name": "inside", "kind": "words", "words": ["False", "True"]}
                ],
            }
        ],
        "profiles": [
            {
                "object": "tibia",
                "provenance": "native",
                "kind": "reading",
                "support": "a3_fibula_axial_region",
                "readings": [
                    {
                        "bank": "target",
                        "metric": "inside",
                        "value": "values",
                        "available": "available",
                    }
                ],
                "support_layout": {"family": "fibula_axial"},
            }
        ],
    }
    with pytest.raises(ValueError, match="invalid_packed_support_family:0"):
        validate_spec(spec)


def test_packed_adapter_broadcasts_unread_without_declaring_or_reading_an_array(case):
    record, observation, arrays, _layout, bindings, _references, packed = case
    spec = LayoutSpec(
        "unread-packed-v1",
        "carrier-test",
        (
            BankSpec(
                "signal",
                "measured signal",
                (MetricSpec("intensity", MetricKind.DIGIT),),
            ),
            BankSpec(
                "context",
                "declared context",
                (MetricSpec("classification", MetricKind.WORDS, ("present",)),),
            ),
        ),
    )
    layout = compile_layout(spec)
    assert layout is not None
    reference = NumericReference(
        layout.fingerprint, "signal", "intensity", "ref-1", "fixture", "a.u.", 0, 1
    )
    unread = {
        "bank": "context",
        "metric": "classification",
        "source": "unread",
        "reason": "no context word is retained for this packed plane",
    }
    result = encode_packed_observation(
        record,
        observation,
        arrays,
        layout,
        (*bindings, unread),
        {("signal", "intensity"): reference},
        packed,
    )
    assert result.encoding is not None
    assert result.points_rc.shape == (2, 2)
    assert result.metadata["unread_sources"] == [
        {
            "bank": "context",
            "metric": "classification",
            "source": "unread",
            "reason": "no context word is retained for this packed plane",
            "status": "unread",
            "source_address": {
                "artifact": record["artifact"],
                "series_uid": packed.target_series_uid,
                "view": list(packed.target_view),
                "slice_index": 10,
                "row": 1,
                "support": "region",
                "owner_artifact": record["artifact"],
                "owner_series_uid": "fibula-owner",
                "target_series_uid": "axial-target",
                "target_view": ["Axial", "1", "1"],
            },
        }
    ]
    metric = next(
        item
        for item in result.encoding.metrics
        if item.bank == "context" and item.metric == "classification"
    )
    assert metric.row_codes.tolist() == [-1, -1]
    assert metric.status.value == "silent"
