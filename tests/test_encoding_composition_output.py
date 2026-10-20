from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from knee.encoding.composition import (
    AddResult,
    BatchIndexMap,
    CompositionCode,
    ObjectComposition,
    StudyComposition,
    prepare_composition,
)
from knee.encoding.composition_output import (
    serialize_add_result,
    serialize_study_composition,
)
from knee.encoding.object_profile import (
    PlaceAddressBatch,
    RowcodeBatch,
    SourceLink,
    assemble_object_profile,
)
from knee.encoding.places import BankSpec, LayoutSpec, MetricKind, MetricSpec
from knee.encoding.spatial import batch_native_rc_readings, prepare_spatial_context


def _fixture():
    base = LayoutSpec(
        "base-v1",
        "base-carrier",
        (
            BankSpec(
                "signal",
                "signal facet",
                (
                    MetricSpec("tone", MetricKind.DIGIT),
                    MetricSpec("texture", MetricKind.DIGIT),
                ),
            ),
        ),
    )
    profile = {
        "object": "joint",
        "provenance": "native",
        "kind": "reading",
        "support": "native_support",
        "view": ["Coronal", "1", "2"],
        "references": [],
    }
    prepared_result = prepare_composition(
        base,
        [profile],
        {
            "version": "composition-v1",
            "view_roles": [["Coronal", "1", "2"]],
            "bank_plans": [
                {"base_bank": "signal", "lens": "white", "scale_scope": "series"}
            ],
        },
    )
    assert prepared_result.prepared is not None
    prepared = prepared_result.prepared
    layout = prepared.profile_layouts["joint"]
    expanded_bank = layout.compiled.banks[0].name
    facet = next(
        item.coordinate for item in layout.registry if item.bank == expanded_bank
    )
    codes = np.array([1, -1, 1], dtype=np.int16)
    coordinates = np.array([[2, 3], [2, 4], [5, 8]], dtype=np.int32)
    indices = np.array([0, 4, 9], dtype=np.int64)
    link = SourceLink("p0/o0", "axial-series.npz.xz", "support", "profile:0/outcome:0")
    batch = RowcodeBatch(
        expanded_bank,
        "tone",
        facet,
        "retained-white-samples",
        layout.compiled.fingerprint,
        layout.count_layout,
        layout.reference_set_identity,
        codes,
        PlaceAddressBatch("native_rc", "series/view/slice/frame", coordinates),
        link,
    )
    index_map = BatchIndexMap(
        "joint", 0, 0, 0, expanded_bank, "tone", None, indices, link
    )
    map_record = {
        "schema": "study_map/v1",
        "knee": "R",
        "scale": {"mm": 5.0, "source": "declared", "code": "ok"},
        "objects": {
            "joint": {
                "status": "complete",
                "point_lps": [10.0, 20.0, 30.0],
                "precision_mm": [1.0, 2.0, 3.0],
                "key_planes": {"axial": 11, "coronal": 7},
            }
        },
    }
    context = prepare_spatial_context(map_record, "joint")
    frame = {"origin_lps": [0.0, 0.0, 0.0], "basis_lps": [[1, 0], [0, 1], [0, 0]]}
    spatial = batch_native_rc_readings(context, coordinates, frame=frame)
    add = AddResult(
        CompositionCode.OK,
        "joint",
        0,
        0,
        spatial,
        (batch,),
        (index_map,),
        {
            "observation": {
                "object": "joint",
                "provenance": "native",
                "kind": "reading",
                "support": "native_support",
                "artifact": "axial-series.npz.xz",
                "series_uid": "series-1",
                "view": ["Coronal", "1", "2"],
                "slices": [7],
                "row": None,
            },
            "plane_frame": frame,
            "metric_note": "measured on native acquisition",
        },
    )
    assembly = assemble_object_profile("joint", layout, [batch])
    object_comp = ObjectComposition("joint", CompositionCode.OK, assembly, (index_map,))
    study = StudyComposition(
        CompositionCode.OK,
        {"joint": object_comp},
        {"joint": context},
        (add,),
    )
    return prepared, study, add, batch, indices, coordinates


def test_publication_keeps_one_shared_layout_sparse_counts_and_addressed_arrays():
    prepared, study, add, batch, indices, coordinates = _fixture()
    arrays, metadata = serialize_study_composition(study, prepared)

    assert metadata["schema"] == "knee_object_profiles/v1"
    assert metadata["carrier_identity"] == prepared.carrier.identity
    assert metadata["layout"]["fingerprint"] == prepared.layout.fingerprint
    assert len(metadata["layout"]["banks"]) == len(prepared.layout.banks)
    assert len(metadata["registry"]) == len(prepared.registry)
    joint = metadata["objects"]["joint"]
    assert (
        joint["reference_set_identity"] == prepared.object_reference_identities["joint"]
    )
    assert (
        joint["count_layout_id"]
        == prepared.profile_layouts["joint"].count_layout.layout_id
    )
    assert all(type(count) is int for _, _, count in joint["sparse_counts"])
    assert len(joint["sparse_counts"]) == 1
    assert "dense" not in joint

    batch_meta = joint["assembly"]["batches"][0]
    rowcodes = arrays[batch_meta["batch_payload"]["rowcodes"]["key"]]
    saved_rc = arrays[batch_meta["batch_payload"]["address"]["coordinates"]["key"]]
    saved_indices = arrays[batch_meta["batch_payload"]["original_place_indices"]["key"]]
    assert rowcodes is batch.rowcodes
    assert np.array_equal(saved_rc, coordinates)
    assert np.array_equal(saved_indices, indices)
    assert batch_meta["source_link"]["artifact"] == "axial-series.npz.xz"
    assert (
        batch_meta["batch_payload"]["address"]["frame_identity"]
        == "series/view/slice/frame"
    )
    assert joint["spatial_context"]["keyplanes"] == {"axial": 11, "coronal": 7}
    assert metadata["additions"][0]["metadata"]["plane_frame"] == {
        "origin_lps": [0.0, 0.0, 0.0],
        "basis_lps": [[1, 0], [0, 1], [0, 0]],
    }
    assert add.spatial is not None


def test_single_addition_serializes_native_and_lps_spatial_measurements():
    _, _, add, _, _, _ = _fixture()
    arrays, metadata = serialize_add_result(add, "sample")
    spatial = metadata["spatial"]
    for name in ("point_lps", "relative_lps_mm", "axis_digits", "joint_code"):
        key = spatial[name]["key"]
        assert key in arrays
        assert isinstance(arrays[key], np.ndarray)
    assert metadata["code"] == "ok"
    assert metadata["batches"][0]["address"]["kind"] == "native_rc"
    assert metadata["metadata"]["observation"]["view"] == ["Coronal", "1", "2"]


def test_add_result_refuses_misaligned_batch_index_maps():
    _, _, add, _, _, _ = _fixture()
    malformed = AddResult(
        add.code,
        add.object_name,
        add.profile_index,
        add.outcome_index,
        add.spatial,
        add.batches,
        (),
        add.metadata,
    )
    with pytest.raises(ValueError, match="composition_batch_index_map_count_mismatch"):
        serialize_add_result(malformed, "bad")


def test_target_only_addition_keeps_its_named_outcome_without_payload_arrays():
    negative = AddResult(
        CompositionCode.TARGET_ONLY,
        "joint",
        0,
        1,
        metadata={"target": "native target observation"},
        detail="target_only",
    )

    arrays, metadata = serialize_add_result(negative, "negative")

    assert arrays == {}
    assert metadata["code"] == "target_only"
    assert metadata["detail"] == "target_only"
    assert metadata["metadata"]["target"] == "native target observation"
    assert metadata["batches"] == []


def test_study_serialization_retains_conflicting_address_links():
    prepared, _, add, batch, indices, _coordinates = _fixture()
    conflicting_batch = replace(
        batch,
        rowcodes=np.array([0, -1, 1], dtype=np.int16),
    )
    second_link = SourceLink(
        "p1/o0", "other-acquisition.npz.xz", "support", "profile:1/outcome:0"
    )
    conflicting_batch = replace(conflicting_batch, source_link=second_link)
    second_map = BatchIndexMap(
        "joint",
        1,
        1,
        0,
        conflicting_batch.bank,
        conflicting_batch.metric,
        None,
        indices.copy(),
        second_link,
    )
    second_add = replace(
        add,
        profile_index=1,
        batches=(conflicting_batch,),
        batch_index_maps=(second_map,),
        metadata={**add.metadata, "artifact": "other-acquisition.npz.xz"},
    )
    assembly = assemble_object_profile(
        "joint", prepared.profile_layouts["joint"], [batch, conflicting_batch]
    )
    object_comp = ObjectComposition(
        "joint", CompositionCode.OK, assembly, (add.batch_index_maps[0], second_map)
    )
    study = StudyComposition(
        CompositionCode.OK,
        {"joint": object_comp},
        {},
        (add, second_add),
    )

    arrays, metadata = serialize_study_composition(study, prepared)

    conflict = metadata["objects"]["joint"]["assembly"]["conflicts"][0]
    assert metadata["objects"]["joint"]["status"] == "conflicting"
    assert metadata["objects"]["joint"]["preparation_status"] == "ok"
    assert conflict["event_count"] == 1
    assert conflict["facet_coordinate"] == {
        "view_role": batch.facet_coordinate.view_role,
        "lens": "white",
        "scale": "series",
        "direction": None,
    }
    assert arrays[conflict["link_batch"]["key"]].tolist() == [0, 1]
    assert arrays[conflict["link_place"]["key"]].tolist() == [0, 0]
    assert arrays[conflict["link_rowcode"]["key"]].tolist() == [1, 0]
    batch_links = [
        item["source_link"]["artifact"]
        for item in metadata["objects"]["joint"]["assembly"]["batches"]
    ]
    assert batch_links == ["axial-series.npz.xz", "other-acquisition.npz.xz"]
    first_coordinate_key = metadata["additions"][0]["batches"][0]["address"][
        "coordinates"
    ]["key"]
    second_coordinate_key = metadata["additions"][1]["batches"][0]["address"][
        "coordinates"
    ]["key"]
    assert first_coordinate_key == second_coordinate_key
    assert arrays[first_coordinate_key] is batch.addresses.coordinates


def test_shared_array_identity_is_stored_once_but_equal_copies_are_distinct():
    prepared, _, add, batch, indices, coordinates = _fixture()
    second_link = replace(
        batch.source_link,
        observation="p1/o0",
        artifact="second.npz.xz",
    )
    second_batch = replace(
        batch,
        source_link=second_link,
        metric="texture",
        rowcodes=np.full(
            batch.rowcodes.shape,
            next(
                row.start
                for row in prepared.profile_layouts["joint"].compiled.metric_rows
                if row.bank == batch.bank and row.metric == "texture"
            ),
            dtype=np.int16,
        ),
    )
    second_indices = BatchIndexMap(
        "joint", 1, 1, 0, batch.bank, second_batch.metric, None, indices, second_link
    )
    shared_add = replace(
        add,
        batches=(batch, second_batch),
        batch_index_maps=(add.batch_index_maps[0], second_indices),
    )

    arrays, metadata = serialize_add_result(shared_add, "shared")

    batch_descriptors = metadata["batches"]
    first_rc = batch_descriptors[0]["address"]["coordinates"]["key"]
    second_rc = batch_descriptors[1]["address"]["coordinates"]["key"]
    first_indices = batch_descriptors[0]["original_place_indices"]["key"]
    second_indices = batch_descriptors[1]["original_place_indices"]["key"]
    assert first_rc == second_rc
    assert first_indices == second_indices
    assert arrays[first_rc] is coordinates
    assert arrays[first_indices] is indices
    assert sum(key.endswith(".coordinates") for key in arrays) == 1
    assert sum(key.endswith(".original_place_indices") for key in arrays) == 1

    copied_batch = replace(
        second_batch,
        addresses=replace(
            batch.addresses,
            coordinates=np.array(coordinates, copy=True),
        ),
    )
    copied_add = replace(shared_add, batches=(batch, copied_batch))
    copied_arrays, copied_metadata = serialize_add_result(copied_add, "copied")
    copied_rc_keys = [
        item["address"]["coordinates"]["key"] for item in copied_metadata["batches"]
    ]
    assert copied_rc_keys[0] != copied_rc_keys[1]
    assert copied_arrays[copied_rc_keys[0]] is not copied_arrays[copied_rc_keys[1]]
    assert sum(key.endswith(".coordinates") for key in copied_arrays) == 2
