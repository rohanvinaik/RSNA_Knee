from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from knee.array_archive import open_arrays
from knee.encoding.carrier import HadamardCarrier
from knee.encoding.places import (
    BankSpec,
    EncodingCode,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    NumericReference,
    compile_layout,
)
from knee.encoding.trace_adapter import encode_trace_observation

BASE = Path(
    "data/readings/"
    "collapse-20261017/full-build/targeted-compute-20261018/"
    "b9b10-integrated-20261019/cohort/labeled-workers4-no-draw/interiors"
)


def _layout():
    carrier = HadamardCarrier.from_banks(["trace"])
    layout = compile_layout(
        LayoutSpec(
            "trace-test-v1",
            carrier.identity,
            (
                BankSpec(
                    "trace",
                    "native_trace_reading",
                    (
                        MetricSpec("light", MetricKind.DIGIT),
                        MetricSpec("flank", MetricKind.DIGIT),
                    ),
                ),
            ),
        )
    )
    assert layout is not None
    references = {
        ("trace", "light"): NumericReference(
            layout.fingerprint,
            "trace",
            "light",
            "provided-light",
            "caller",
            "units",
            250.0,
            350.0,
        ),
        ("trace", "flank"): NumericReference(
            layout.fingerprint,
            "trace",
            "flank",
            "provided-flank",
            "caller",
            "units",
            250.0,
            350.0,
        ),
    }
    return layout, references


def _retained_case(nonempty: bool):
    if not (BASE / "receipt.json").is_file():
        pytest.skip("saved proof trace receipt is not available")
    receipt = json.loads((BASE / "receipt.json").read_text())
    records = receipt["records"]
    by_artifact = {record.get("artifact"): record for record in records}
    for target_record in records:
        for observation in target_record.get("observations", []):
            if not str(observation.get("support", "")).startswith(
                "a3_posterior_trace_"
            ):
                continue
            if bool(observation.get("count", 0)) != nonempty:
                continue
            owner_record = by_artifact.get(observation.get("artifact"))
            if owner_record is not None:
                return target_record, owner_record, observation
    raise AssertionError("retained_trace_case_not_found")


def _encode(target_record, owner_record, observation):
    artifact = BASE / observation["artifact"]
    layout, references = _layout()
    with open_arrays(artifact) as arrays:
        result = encode_trace_observation(
            target_record,
            owner_record,
            observation,
            arrays,
            layout,
            (
                {
                    "bank": "trace",
                    "metric": "light",
                    "value": observation["support"].removesuffix("_points_lps")
                    + "_light",
                },
                {
                    "bank": "trace",
                    "metric": "flank",
                    "value": observation["support"].removesuffix("_points_lps")
                    + "_flank",
                },
            ),
            references,
        )
    return result


def test_real_retained_trace_preserves_lps_points_and_numeric_readings():
    target, owner, observation = _retained_case(nonempty=True)
    result = _encode(target, owner, observation)
    assert result.status == EncodingCode.OK.value
    assert result.points_lps is not None
    assert result.points_lps.shape == (observation["count"], 3)
    assert result.metadata["owner_series_uid"] == owner["series_uid"]
    assert result.metadata["target_series_uid"] == target["series_uid"]
    assert result.metadata["addresses"] == "patient_lps_points"
    assert result.metadata["meaning"].endswith("no mask or volume")
    assert len(result.encoding.metrics) == 2
    assert result.encoding.bundle is not None
    assert sum(result.encoding.bundle.counts[0]) == observation["count"] * 2


def test_real_retained_empty_trace_stays_a_named_silent_reading():
    target, owner, observation = _retained_case(nonempty=False)
    result = _encode(target, owner, observation)
    assert observation["count"] == 0
    assert result.status == EncodingCode.SILENT.value
    assert result.points_lps is not None and result.points_lps.shape == (0, 3)
    assert result.encoding.bundle is not None
    assert not np.any(result.encoding.bundle.counts[0])


def test_target_nearest_slice_may_differ_from_record_middle_slice():
    target, owner, observation = _retained_case(nonempty=True)
    target = dict(target)
    target["slice_index"] = observation["slices"][0] - 1
    result = _encode(target, owner, observation)
    assert result.status == EncodingCode.OK.value
    assert result.metadata["slice_index"] == observation["slices"][0]


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda target, owner, obs: obs.update(row=True), "invalid_trace_row"),
        (lambda target, owner, obs: obs.update(count=1.5), "trace_count_mismatch"),
        (lambda target, owner, obs: obs.update(count=None), "trace_count_mismatch"),
        (lambda target, owner, obs: obs.update(view=None), "target_view_mismatch"),
        (
            lambda target, owner, obs: obs.update(code="wrong"),
            "trace_start_code_mismatch",
        ),
        (
            lambda target, owner, obs: target.update(series_uid="wrong"),
            "target_series_mismatch",
        ),
        (
            lambda target, owner, obs: owner.update(artifact="wrong.npz.xz"),
            "source_artifact_owner_mismatch",
        ),
        (
            lambda target, owner, obs: owner.update(main_slice="malformed"),
            "source_artifact_owner_mismatch",
        ),
    ],
)
def test_address_and_count_conflicts_are_named(mutation, expected):
    target, owner, observation = _retained_case(nonempty=True)
    target, owner, observation = dict(target), dict(owner), dict(observation)
    mutation(target, owner, observation)
    result = _encode(target, owner, observation)
    assert result.status == expected
    assert result.encoding is None


def test_bad_offsets_are_refused_without_interpreting_them_as_points():
    target, owner, observation = _retained_case(nonempty=True)
    layout, references = _layout()
    path = BASE / observation["artifact"]
    with open_arrays(path) as arrays:
        altered = {name: arrays[name] for name in arrays.files}
    offsets_name = observation["support"].removesuffix("_points_lps") + "_offsets"
    altered[offsets_name] = altered[offsets_name].copy()
    altered[offsets_name][-1] += 1
    owner = dict(owner)
    owner["arrays"] = dict(owner["arrays"])
    from knee.receipt import digest

    owner["arrays"][offsets_name] = {"digest": digest(altered[offsets_name])}
    result = encode_trace_observation(
        target,
        owner,
        observation,
        altered,
        layout,
        (
            {
                "bank": "trace",
                "metric": "light",
                "value": offsets_name.replace("offsets", "light"),
            },
            {
                "bank": "trace",
                "metric": "flank",
                "value": offsets_name.replace("offsets", "flank"),
            },
        ),
        references,
    )
    assert result.status == "invalid_trace_offsets"
    assert result.encoding is None


def test_empty_offsets_are_named_invalid_instead_of_indexing_empty_array():
    target, owner, observation = _retained_case(nonempty=True)
    layout, references = _layout()
    path = BASE / observation["artifact"]
    with open_arrays(path) as arrays:
        altered = {name: arrays[name] for name in arrays.files}
    offsets_name = observation["support"].removesuffix("_points_lps") + "_offsets"
    altered[offsets_name] = np.empty(0, dtype=np.int64)
    owner = dict(owner)
    owner["arrays"] = dict(owner["arrays"])
    from knee.receipt import digest

    owner["arrays"][offsets_name] = {"digest": digest(altered[offsets_name])}
    result = encode_trace_observation(
        target,
        owner,
        observation,
        altered,
        layout,
        (
            {
                "bank": "trace",
                "metric": "light",
                "value": offsets_name.replace("offsets", "light"),
            },
            {
                "bank": "trace",
                "metric": "flank",
                "value": offsets_name.replace("offsets", "flank"),
            },
        ),
        references,
    )
    assert result.status == "invalid_trace_offsets"
    assert result.encoding is None


def test_non_mapping_observation_and_owner_are_named():
    target, owner, observation = _retained_case(nonempty=True)
    layout, references = _layout()
    with open_arrays(BASE / observation["artifact"]) as arrays:
        none_observation = encode_trace_observation(
            target, owner, None, arrays, layout, (), references
        )
        none_owner = encode_trace_observation(
            target, None, observation, arrays, layout, (), references
        )
    assert none_observation.status == "invalid_trace_observation"
    assert none_owner.status == "invalid_trace_records"
