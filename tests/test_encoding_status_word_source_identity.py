from __future__ import annotations

from dataclasses import replace

import numpy as np

from knee.encoding.carrier import HadamardCarrier
from knee.encoding.composition import (
    CompositionCode,
    StudyComposer,
    prepare_composition,
)
from knee.encoding.places import (
    BankSpec,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    PlaceReading,
    compile_layout,
    encode_places,
)
from knee.encoding.scoped import ScopedEncoding


def _word_fixture():
    carrier = HadamardCarrier.from_banks(("form",))
    base = compile_layout(
        LayoutSpec(
            "status-v1",
            carrier.identity,
            (
                BankSpec(
                    "form",
                    "shape",
                    (MetricSpec("status", MetricKind.WORDS, ("open", "closed")),),
                ),
            ),
        )
    )
    assert base is not None
    profile = {
        "object": "ligament",
        "provenance": "native",
        "kind": "reading",
        "support": "slice_profile",
        "view": ["sagittal", "fat-suppressed", "fluid"],
        "readings": [{"bank": "form", "metric": "status", "value": "status_words"}],
        "references": [],
    }
    declaration = {
        "version": "status-test-v1",
        "view_roles": [["sagittal", "fat-suppressed", "fluid"]],
        "bank_plans": [
            {
                "base_bank": "form",
                "lens": "profile-status",
                "scale_scope": "series-slice",
            }
        ],
    }
    result = prepare_composition(base, [profile], declaration)
    assert result.code is CompositionCode.OK and result.prepared is not None
    prepared = result.prepared
    map_record = {
        "schema": "study_map/v1",
        "objects": {"ligament": {"status": "unavailable", "key_planes": {}}},
    }
    return base, prepared, profile, map_record


def _scoped(
    base,
    profile,
    indices,
    words,
    *,
    digest="status-digest",
    selected=None,
    observation_code="reading",
    bad_ref=False,
):
    indices = np.asarray(indices, dtype=np.int64)
    words = np.asarray(words, dtype=np.str_)
    encoded = encode_places(
        base,
        {
            ("form", "status"): PlaceReading(
                "form", "status", words, np.ones(words.shape, dtype=np.bool_)
            )
        },
        {},
    )
    assert encoded.bundle is not None
    artifact = "series-profile.npz.xz"
    descriptor = {"artifact": artifact, "digest": digest, "shape": [12], "dtype": "<i2"}
    source_ref = dict(descriptor)
    if bad_ref:
        source_ref["digest"] = "different-digest"
    observation = {
        "object": profile["object"],
        "provenance": profile["provenance"],
        "kind": profile["kind"],
        "support": profile["support"],
        "view": profile["view"],
        "series_uid": "series-1",
        "slices": indices.tolist(),
        "artifact": artifact,
        "code": observation_code,
    }
    metadata = {
        "observation": observation,
        "bindings": [{"bank": "form", "metric": "status", "source": "status_words"}],
        "source_refs": {"status_array": descriptor},
        "status_word_source": {
            "array": "status_array",
            "source_ref": source_ref,
            "codes": {"open": 1, "closed": 2},
            "measured_status_names": ["open", "closed"],
            "selected_status_names": selected or [str(value) for value in words],
            "unit": "categorical-per-slice",
            "scope": "native acquisition slice profile",
        },
        "scope_address": {
            "series_uid": "series-1",
            "view": list(profile["view"]),
            "axis": "native_series_slice_index",
            "measurement": "status_array",
        },
        "source_address": {"series_uid": "series-1", "slice_indices": indices.tolist()},
    }
    return ScopedEncoding("ok", encoded, indices[:, None], "series_slice", metadata)


def test_actual_composer_deduplicates_overlapping_slices_for_shared_status_vector():
    base, prepared, profile, map_record = _word_fixture()
    composer = StudyComposer(prepared, map_record)
    first = _scoped(
        base,
        profile,
        [1, 2],
        ["open", "closed"],
        selected=["open", "closed"],
        observation_code="identified",
    )
    overlap = _scoped(
        base,
        profile,
        [2, 3],
        ["closed", "open"],
        selected=["closed", "open"],
        observation_code="reading",
    )
    disjoint = _scoped(base, profile, [7], ["open"], selected=["open"])
    first_result = composer.add("ligament", 0, 0, first, profile)
    overlap_result = composer.add("ligament", 0, 1, overlap, profile)
    disjoint_result = composer.add("ligament", 0, 2, disjoint, profile)
    assert (
        first_result.code
        is overlap_result.code
        is disjoint_result.code
        is CompositionCode.OK
    )
    assembled = composer.finalize().objects["ligament"].assembly
    assert assembled is not None
    assert sum(count for _, _, count in assembled.profile.entries) == 4
    assert len(assembled.batches) == 3
    assert len({batch.measurement_source_identity for batch in assembled.batches}) == 1
    retained = {
        int(index)
        for result in (first_result, overlap_result, disjoint_result)
        for batch in result.batches
        for index in batch.addresses.coordinates[:, 0]
    }
    assert retained == {1, 2, 3, 7}


def test_status_identity_uses_verified_descriptor_and_codes_but_not_subset_or_selected_names():
    base, prepared, profile, map_record = _word_fixture()
    composer = StudyComposer(prepared, map_record)
    a = _scoped(
        base, profile, [4], ["open"], selected=["open"], observation_code="identified"
    )
    b = _scoped(
        base, profile, [5], ["closed"], selected=["closed"], observation_code="reading"
    )
    a_added = composer.add("ligament", 0, 0, a, profile)
    b_added = composer.add("ligament", 0, 1, b, profile)
    assert a_added.code is b_added.code is CompositionCode.OK
    assert (
        a_added.batches[0].measurement_source_identity
        == b_added.batches[0].measurement_source_identity
    )

    contradictory = _scoped(
        base, profile, [4], ["closed"], digest="different-status-digest"
    )
    c_added = composer.add("ligament", 0, 2, contradictory, profile)
    assert c_added.code is CompositionCode.OK
    assert (
        c_added.batches[0].measurement_source_identity
        != a_added.batches[0].measurement_source_identity
    )

    baseline_identity = a_added.batches[0].measurement_source_identity
    for key, value in (
        ("codes", {"open": 2, "closed": 1}),
        ("measured_status_names", ["closed"]),
        ("scope", "different producer scope"),
    ):
        altered_metadata = dict(a.metadata)
        altered_status = dict(altered_metadata["status_word_source"])
        altered_status[key] = value
        altered_metadata["status_word_source"] = altered_status
        altered = replace(a, metadata=altered_metadata)
        result = composer.add("ligament", 0, 10 + len(key), altered, profile)
        assert result.code is CompositionCode.OK
        assert result.batches[0].measurement_source_identity != baseline_identity


def test_status_source_descriptor_must_match_retained_source_reference():
    base, prepared, profile, map_record = _word_fixture()
    bad = _scoped(base, profile, [0], ["open"], bad_ref=True)
    result = StudyComposer(prepared, map_record).add("ligament", 0, 0, bad, profile)
    assert result.code is CompositionCode.MEASUREMENT_SOURCE_UNAVAILABLE
    assert result.detail == "measurement_source_unavailable"
    assert not result.batches
