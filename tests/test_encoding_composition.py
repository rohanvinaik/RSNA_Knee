from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from knee.encoding.carrier import HadamardCarrier
from knee.encoding.composition import (
    CompositionCode,
    StudyComposer,
    prepare_composition,
)
from knee.encoding.handoff import AddressedEncoding
from knee.encoding.places import (
    BankSpec,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    NumericReference,
    PlaceReading,
    compile_layout,
    encode_places,
)
from knee.encoding.scoped import ScopedEncoding
from knee.encoding.trace_adapter import TraceEncoding


def _fixture(*, ref_id="healthy", map_point=(0.0, 0.0, 0.0)):
    base_carrier = HadamardCarrier.from_banks(("intensity",))
    base_spec = LayoutSpec(
        "v1",
        base_carrier.identity,
        (
            BankSpec(
                "intensity", "signal", (MetricSpec("level", MetricKind.DIGIT, ()),)
            ),
        ),
    )
    base = compile_layout(base_spec)
    assert base is not None
    reference = {
        "bank": "intensity",
        "metric": "level",
        "reference_id": ref_id,
        "source": "healthy-reference",
        "units": "signal-unit",
        "low": 0.0,
        "high": 1.0,
    }
    profile = {
        "object": "cartilage",
        "provenance": "native",
        "kind": "reading",
        "support": "surface",
        "view": ["sagittal", "fat-suppressed", "fluid"],
        "readings": [
            {
                "bank": "intensity",
                "metric": "level",
                "value": "values",
                "available": "valid",
            }
        ],
        "references": [reference],
    }
    declaration = {
        "version": "test-v1",
        "view_roles": [["sagittal", "fat-suppressed", "fluid"]],
        "bank_plans": [
            {
                "base_bank": "intensity",
                "lens": "native-signal",
                "scale_scope": "bounded-plane",
            }
        ],
    }
    prepared_result = prepare_composition(base, [profile], declaration)
    assert prepared_result.code is CompositionCode.OK
    prepared = prepared_result.prepared
    assert prepared is not None
    numeric_reference = NumericReference(
        base.fingerprint,
        "intensity",
        "level",
        ref_id,
        "healthy-reference",
        "signal-unit",
        0.0,
        1.0,
    )
    values = np.array([0.2, 0.7, 1.5], dtype=np.float64)
    available = np.array([True, True, False], dtype=np.bool_)
    encoded = encode_places(
        base,
        {("intensity", "level"): PlaceReading("intensity", "level", values, available)},
        {("intensity", "level"): numeric_reference},
    )
    assert encoded.bundle is not None
    observation = {
        "object": "cartilage",
        "provenance": "native",
        "kind": "reading",
        "support": "surface",
        "view": ["sagittal", "fat-suppressed", "fluid"],
        "series_uid": "series-1",
        "slices": [4],
        "artifact": "record-1.npz.xz",
    }
    refs = {
        "values": {
            "artifact": observation["artifact"],
            "digest": "value-digest",
            "shape": [3],
            "dtype": "<f8",
        },
        "valid": {
            "artifact": observation["artifact"],
            "digest": "valid-digest",
            "shape": [3],
            "dtype": "|b1",
        },
    }
    addressed = AddressedEncoding(
        "encoded",
        encoded,
        np.array([[0, 0], [1, 1], [2, 2]], dtype=np.int32),
        {
            "observation": observation,
            "bindings": [
                {
                    "bank": "intensity",
                    "metric": "level",
                    "source": "array",
                    "value": "values",
                    "available": "valid",
                }
            ],
            "source_refs": refs,
            "plane_frame": {
                "origin_lps": [0.0, 0.0, 0.0],
                "basis_lps": [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]],
            },
        },
    )
    map_record = {
        "schema": "study_map/v1",
        "knee": "R",
        "objects": {
            "cartilage": {
                "status": "complete",
                "point_lps": list(map_point),
                "precision_mm": [0.1, 0.1, 0.1],
                "key_planes": {},
            }
        },
    }
    return prepared, profile, addressed, map_record


def test_preparation_binds_carrier_and_expands_overview_and_all_directions():
    prepared, _, _, _ = _fixture()
    assert prepared.layout.carrier_id == prepared.carrier.identity
    assert len(prepared.facets_by_key) == 28
    assert (
        "intensity",
        ("sagittal", "fat-suppressed", "fluid"),
        None,
    ) in prepared.facets_by_key
    center = (0, 0, 0)
    assert (
        "intensity",
        ("sagittal", "fat-suppressed", "fluid"),
        center,
    ) in prepared.facets_by_key
    assert (
        prepared.facets_by_key[
            ("intensity", ("sagittal", "fat-suppressed", "fluid"), None)
        ]
        != prepared.facets_by_key[
            ("intensity", ("sagittal", "fat-suppressed", "fluid"), center)
        ]
    )


def test_add_remaps_rowcodes_preserves_unavailable_and_keeps_address_lineage():
    prepared, profile, addressed, map_record = _fixture()
    composer = StudyComposer(prepared, map_record)
    added = composer.add("cartilage", 0, 0, addressed, profile)
    assert added.code is CompositionCode.OK
    assert added.spatial is not None
    assert len(added.batches) == 3  # overview plus centre and above directions
    overview = next(
        batch for batch in added.batches if batch.facet_coordinate.direction is None
    )
    source = addressed.encoding.metrics[0].row_codes
    expected_base_start = prepared.base_metric_rows[("intensity", "level")].start
    expected_target_start = prepared.metric_rows[
        (overview.bank, "level", "signal")
    ].start
    expected = np.where(
        source >= 0, source - expected_base_start + expected_target_start, -1
    ).astype(np.int16)
    np.testing.assert_array_equal(overview.rowcodes, expected)
    assert overview.rowcodes[-1] == -1
    assert overview.addresses.kind == "native_rc"
    np.testing.assert_array_equal(overview.addresses.coordinates, addressed.points_rc)
    assert added.batch_index_maps[0].original_place_indices.tolist() == [0, 1, 2]
    result = composer.finalize()
    assert result.objects["cartilage"].assembly is not None
    assert (
        result.objects["cartilage"].assembly.profile.count_layout
        == prepared.profile_layouts["cartilage"].count_layout
    )


def test_missing_reference_is_explicit_and_object_local_conflict_does_not_block_other_object():
    prepared, profile, _, _ = _fixture()
    assert prepared.object_codes["cartilage"] is CompositionCode.OK
    # A second object with contradictory known references is refused by name.
    _, _, _, _ = _fixture()
    base = prepared.base_layout
    base_spec = LayoutSpec(base.version, base.carrier_id, base.banks)
    profiles = [
        {**profile, "object": "a", "references": [profile["references"][0]]},
        {
            **profile,
            "object": "a",
            "references": [{**profile["references"][0], "reference_id": "other"}],
        },
        {**profile, "object": "b", "references": []},
    ]
    declaration = {
        "version": "test-v1",
        "view_roles": [["sagittal", "fat-suppressed", "fluid"]],
        "bank_plans": [
            {
                "base_bank": "intensity",
                "lens": "native-signal",
                "scale_scope": "bounded-plane",
            }
        ],
    }
    rebuilt = prepare_composition(base_spec, profiles, declaration)
    assert rebuilt.code is CompositionCode.OK
    assert rebuilt.prepared is not None
    assert (
        rebuilt.prepared.object_codes["a"] is CompositionCode.REFERENCE_MAPPING_CONFLICT
    )
    assert rebuilt.prepared.object_codes["b"] is CompositionCode.OK
    assert rebuilt.prepared.profile_layouts["b"].reference_set_identity


def test_all_conflicted_objects_keep_valid_shared_layout_without_profile_layouts():
    prepared, profile, _, map_record = _fixture()
    conflict = {
        **profile,
        "references": [{**profile["references"][0], "reference_id": "other-reference"}],
    }
    declaration = {
        "version": "test-v1",
        "view_roles": [["sagittal", "fat-suppressed", "fluid"]],
        "bank_plans": [
            {
                "base_bank": "intensity",
                "lens": "native-signal",
                "scale_scope": "bounded-plane",
            }
        ],
    }
    result = prepare_composition(prepared.base_layout, [profile, conflict], declaration)
    assert result.prepared is not None
    assert result.prepared.profile_layouts == {}
    composer = StudyComposer(result.prepared, map_record)
    finalized = composer.finalize()
    assert finalized.code is CompositionCode.OK
    assert (
        finalized.objects["cartilage"].code
        is CompositionCode.REFERENCE_MAPPING_CONFLICT
    )


def test_target_only_does_not_open_measurement_source():
    prepared, profile, addressed, map_record = _fixture()
    target_only = AddressedEncoding("target_only", None, None, addressed.metadata)
    composer = StudyComposer(prepared, map_record)
    result = composer.add("cartilage", 0, 0, target_only, profile)
    assert result.code is CompositionCode.TARGET_ONLY
    assert not result.batches
    assert composer.finalize().objects["cartilage"].assembly is not None


def test_repeated_same_measurement_and_places_do_not_double_count(monkeypatch):
    import knee.encoding.composition as composition_module

    prepared, profile, addressed, map_record = _fixture()
    calls = 0
    original = composition_module.prepare_spatial_context

    def counted_context(record, object_name):
        nonlocal calls
        calls += 1
        return original(record, object_name)

    monkeypatch.setattr(composition_module, "prepare_spatial_context", counted_context)
    composer = StudyComposer(prepared, map_record)
    assert (
        composer.add("cartilage", 0, 0, addressed, profile).code is CompositionCode.OK
    )
    assert (
        composer.add("cartilage", 0, 1, addressed, profile).code is CompositionCode.OK
    )
    result = composer.finalize().objects["cartilage"].assembly
    assert result is not None
    # One observed row for each of the two available values; the repeated
    # source/place events remain linked but do not vote twice.
    total = sum(count for _, _, count in result.profile.entries)
    assert total == 4  # two observed values, each in overview and direction bank
    assert len(result.batches) == 6
    assert calls == 1


def test_words_without_numeric_references_are_healthy_and_layout_bound():
    carrier = HadamardCarrier.from_banks(("form",))
    base = compile_layout(
        LayoutSpec(
            "word-v1",
            carrier.identity,
            (
                BankSpec(
                    "form",
                    "shape",
                    (MetricSpec("appearance", MetricKind.WORDS, ("arched", "flat")),),
                ),
            ),
        )
    )
    assert base is not None
    profile = {
        "object": "meniscus",
        "provenance": "native",
        "kind": "reading",
        "support": "shape",
        "view": ["coronal", "fat-suppressed", "fluid"],
        "readings": [
            {
                "bank": "form",
                "metric": "appearance",
                "value": "appearance",
                "available": "valid",
            }
        ],
        "references": [],
    }
    declaration = {
        "version": "words-v1",
        "view_roles": [["coronal", "fat-suppressed", "fluid"]],
        "bank_plans": [
            {
                "base_bank": "form",
                "lens": "native-outline",
                "scale_scope": "bounded-plane",
            }
        ],
    }
    result = prepare_composition(base, [profile], declaration)
    assert result.code is CompositionCode.OK
    assert result.prepared is not None
    assert result.prepared.object_codes["meniscus"] is CompositionCode.OK
    assert result.prepared.layout.carrier_id == result.prepared.carrier.identity


def test_unavailable_spatial_context_keeps_measurement_in_overview_only():
    prepared, profile, addressed, _ = _fixture()
    composer = StudyComposer(prepared, {"schema": "study_map/v1", "objects": {}})
    result = composer.add("cartilage", 0, 0, addressed, profile)
    assert result.code is CompositionCode.OK
    assert result.spatial is not None
    assert np.all(result.spatial.joint_code == -1)
    assert len(result.batches) == 1
    assert result.batches[0].facet_coordinate.direction is None


def test_reference_identity_ignores_observation_plan_but_separates_view_scopes():
    prepared, profile, _, _ = _fixture()
    declaration = {
        "version": "test-v1",
        "view_roles": [
            ["sagittal", "fat-suppressed", "fluid"],
            ["coronal", "fat-suppressed", "fluid"],
        ],
        "bank_plans": [
            {
                "base_bank": "intensity",
                "lens": "native-signal",
                "scale_scope": "bounded-plane",
            }
        ],
    }
    baseline = prepared.object_reference_identities["cartilage"]
    cheap = {
        **profile,
        "provenance": "projected",
        "kind": "reading",
        "support": "coarse",
    }
    missing = {**cheap, "references": []}
    repeated = prepare_composition(
        prepared.base_layout,
        [profile, cheap, missing],
        declaration,
    )
    assert repeated.prepared is not None
    assert repeated.prepared.object_codes["cartilage"] is CompositionCode.OK
    assert repeated.prepared.object_reference_identities["cartilage"] == baseline

    coronal = {
        **profile,
        "view": ["coronal", "fat-suppressed", "fluid"],
        "references": [
            {**profile["references"][0], "reference_id": "coronal-reference"}
        ],
    }
    split_view = prepare_composition(
        prepared.base_layout, [profile, coronal], declaration
    )
    assert split_view.prepared is not None
    assert split_view.prepared.object_codes["cartilage"] is CompositionCode.OK

    conflict = {
        **profile,
        "support": "another-reading",
        "references": [
            {**profile["references"][0], "reference_id": "different-reference"}
        ],
    }
    same_view_conflict = prepare_composition(
        prepared.base_layout,
        [profile, conflict],
        declaration,
    )
    assert same_view_conflict.prepared is not None
    assert (
        same_view_conflict.prepared.object_codes["cartilage"]
        is CompositionCode.REFERENCE_MAPPING_CONFLICT
    )


def test_all_unread_metric_keeps_overview_indices_without_direction_batches():
    prepared, profile, addressed, map_record = _fixture()
    encoded_unread = encode_places(
        prepared.base_layout,
        {
            ("intensity", "level"): PlaceReading(
                "intensity",
                "level",
                np.zeros(3, dtype=np.float64),
                np.zeros(3, dtype=np.bool_),
            )
        },
        {
            ("intensity", "level"): NumericReference(
                prepared.base_layout.fingerprint,
                "intensity",
                "level",
                "healthy",
                "healthy-reference",
                "signal-unit",
                0.0,
                1.0,
            )
        },
    )
    unread_addressed = replace(addressed, encoding=encoded_unread)
    composer = StudyComposer(prepared, map_record)
    result = composer.add("cartilage", 0, 0, unread_addressed, profile)
    assert result.code is CompositionCode.OK
    assert len(result.batches) == 1
    assert result.batches[0].facet_coordinate.direction is None
    assert np.all(result.batches[0].rowcodes == -1)
    assert result.batch_index_maps[0].original_place_indices.tolist() == [0, 1, 2]


def test_wildcard_reference_expands_to_declared_views_for_identity_and_conflict():
    prepared, profile, _, _ = _fixture()
    declaration = {
        "version": "test-v1",
        "view_roles": [["sagittal", "fat-suppressed", "fluid"]],
        "bank_plans": [
            {
                "base_bank": "intensity",
                "lens": "native-signal",
                "scale_scope": "bounded-plane",
            }
        ],
    }
    wildcard = {**profile, "view": None}
    wildcard_result = prepare_composition(prepared.base_layout, [wildcard], declaration)
    assert wildcard_result.prepared is not None
    assert wildcard_result.prepared.object_codes["cartilage"] is CompositionCode.OK
    assert (
        wildcard_result.prepared.object_reference_identities["cartilage"]
        == prepared.object_reference_identities["cartilage"]
    )

    conflict = {
        **profile,
        "references": [
            {**profile["references"][0], "reference_id": "different-meaning"}
        ],
    }
    conflict_result = prepare_composition(
        prepared.base_layout, [wildcard, conflict], declaration
    )
    assert conflict_result.prepared is not None
    assert (
        conflict_result.prepared.object_codes["cartilage"]
        is CompositionCode.REFERENCE_MAPPING_CONFLICT
    )


def test_common_compiled_layout_is_reused_across_objects_and_study_assembly(
    monkeypatch,
):
    import knee.encoding.object_profile as object_profile_module

    base_prepared, profile, _, map_record = _fixture()
    profiles = [
        {
            **profile,
            "object": f"cartilage-{index}",
            "references": [
                {
                    **profile["references"][0],
                    "reference_id": f"healthy-{index}",
                }
            ],
        }
        for index in range(12)
    ]
    declaration = {
        "version": "test-v1",
        "view_roles": [["sagittal", "fat-suppressed", "fluid"]],
        "bank_plans": [
            {
                "base_bank": "intensity",
                "lens": "native-signal",
                "scale_scope": "bounded-plane",
            }
        ],
    }
    original = object_profile_module.compile_layout
    calls = 0

    def counted_compile(spec):
        nonlocal calls
        calls += 1
        return original(spec)

    monkeypatch.setattr(object_profile_module, "compile_layout", counted_compile)
    result = prepare_composition(base_prepared.base_layout, profiles, declaration)
    assert result.code is CompositionCode.OK
    assert result.prepared is not None
    assert calls == 1
    assert len(set(result.prepared.object_reference_identities.values())) == 12
    assert all(
        profile_layout.compiled is result.prepared.layout
        for profile_layout in result.prepared.profile_layouts.values()
    )

    composer = StudyComposer(result.prepared, map_record)
    finalized = composer.finalize()
    assert calls == 2  # one full validation for the shared immutable layout
    assert set(finalized.objects) == {f"cartilage-{i}" for i in range(12)}
    assert all(obj.assembly is not None for obj in finalized.objects.values())


def test_forged_prepared_reference_layout_is_named_and_never_crashes():
    from dataclasses import replace as dataclass_replace
    from types import MappingProxyType

    prepared, _, _, map_record = _fixture()
    original_layout = prepared.profile_layouts["cartilage"]
    forged_layout = dataclass_replace(
        original_layout,
        reference_set_identity="forged-reference-identity",
        count_layout=dataclass_replace(
            original_layout.count_layout, layout_id="forged-layout"
        ),
    )
    forged_prepared = dataclass_replace(
        prepared,
        profile_layouts=MappingProxyType({"cartilage": forged_layout}),
    )
    result = StudyComposer(forged_prepared, map_record).finalize()
    assert result.code is CompositionCode.PROFILE_LAYOUT_ERROR
    assert result.objects["cartilage"].code is CompositionCode.PROFILE_LAYOUT_ERROR
    assert result.objects["cartilage"].assembly is None


def test_missing_object_profile_layout_is_refused_without_keyerror():
    from dataclasses import replace as dataclass_replace
    from types import MappingProxyType

    prepared, _, _, map_record = _fixture()
    forged = dataclass_replace(prepared, profile_layouts=MappingProxyType({}))
    composer = StudyComposer(forged, map_record)
    assert (
        composer.add("cartilage", 0, 0, object(), {}).code
        is CompositionCode.PROFILE_LAYOUT_ERROR
    )
    result = composer.finalize()
    assert result.code is CompositionCode.PROFILE_LAYOUT_ERROR
    assert result.objects["cartilage"].assembly is None


def test_swapped_facet_direction_derivative_is_refused():
    from dataclasses import replace as dataclass_replace
    from types import MappingProxyType

    prepared, _, _, map_record = _fixture()
    overview = ("intensity", ("sagittal", "fat-suppressed", "fluid"), None)
    center = ("intensity", ("sagittal", "fat-suppressed", "fluid"), (0, 0, 0))
    facets = dict(prepared.facets_by_key)
    facets[overview], facets[center] = facets[center], facets[overview]
    forged = dataclass_replace(prepared, facets_by_key=MappingProxyType(facets))
    result = StudyComposer(forged, map_record).finalize()
    assert result.code is CompositionCode.PROFILE_LAYOUT_ERROR
    assert result.objects["cartilage"].assembly is None


@pytest.mark.parametrize("table_name", ["metric_rows", "base_metric_rows"])
def test_changed_metric_row_derivatives_are_refused(table_name):
    from dataclasses import replace as dataclass_replace
    from types import MappingProxyType

    prepared, _, _, map_record = _fixture()
    table = dict(getattr(prepared, table_name))
    key = next(iter(table))
    table[key] = dataclass_replace(table[key], start=True)
    forged = dataclass_replace(prepared, **{table_name: MappingProxyType(table)})
    result = StudyComposer(forged, map_record).finalize()
    assert result.code is CompositionCode.PROFILE_LAYOUT_ERROR
    assert result.objects["cartilage"].assembly is None


def test_malformed_profile_entry_and_nonstring_scale_are_refused():
    from dataclasses import replace as dataclass_replace

    prepared, _, _, map_record = _fixture()
    profile = prepared.profiles[0]
    malformed_profile = dataclass_replace(profile, object_name=True)
    forged_profile = dataclass_replace(prepared, profiles=(malformed_profile,))
    result = StudyComposer(forged_profile, map_record).finalize()
    assert result.code is CompositionCode.PROFILE_LAYOUT_ERROR

    first = prepared.expansion.mapping[0]
    malformed_entry = dataclass_replace(first, scale_scope=1.0)
    expansion = dataclass_replace(
        prepared.expansion,
        mapping=(malformed_entry, *prepared.expansion.mapping[1:]),
    )
    forged_scale = dataclass_replace(prepared, expansion=expansion)
    result = StudyComposer(forged_scale, map_record).finalize()
    assert result.code is CompositionCode.PROFILE_LAYOUT_ERROR


def test_add_refuses_malformed_source_descriptors_and_metric_row_dtype():
    prepared, profile, addressed, map_record = _fixture()
    malformed_metadata = dict(addressed.metadata)
    malformed_refs = {
        name: dict(descriptor)
        for name, descriptor in malformed_metadata["source_refs"].items()
    }
    malformed_refs["values"]["artifact"] = "wrong-owner.npz.xz"
    malformed_metadata["source_refs"] = malformed_refs
    malformed_source = replace(addressed, metadata=malformed_metadata)
    result = StudyComposer(prepared, map_record).add(
        "cartilage", 0, 0, malformed_source, profile
    )
    assert result.code is CompositionCode.MEASUREMENT_SOURCE_UNAVAILABLE

    metrics = addressed.encoding.metrics
    bad_metric = replace(metrics[0], row_codes=metrics[0].row_codes.astype(np.int32))
    bad_encoding = replace(addressed.encoding, metrics=(bad_metric,))
    result = StudyComposer(prepared, map_record).add(
        "cartilage", 0, 0, replace(addressed, encoding=bad_encoding), profile
    )
    assert result.code is CompositionCode.METRIC_ROW_MISMATCH


def test_add_refuses_malformed_native_and_trace_coordinate_dtypes():
    prepared, profile, addressed, map_record = _fixture()
    bad_native = replace(addressed, points_rc=addressed.points_rc.astype(np.float64))
    result = StudyComposer(prepared, map_record).add(
        "cartilage", 0, 0, bad_native, profile
    )
    assert result.code is CompositionCode.SPATIAL_INPUT_MALFORMED

    bad_trace = TraceEncoding(
        addressed.status,
        addressed.encoding,
        np.array([[0.0, 0.0, 0.0]], dtype=np.float32),
        addressed.metadata,
    )
    result = StudyComposer(prepared, map_record).add(
        "cartilage", 0, 0, bad_trace, profile
    )
    assert result.code is CompositionCode.SPATIAL_INPUT_MALFORMED


@pytest.mark.parametrize("kind,width", [("coarse_grid_rc", 2), ("series_slice", 1)])
def test_scoped_measurements_keep_exact_addresses_without_inventing_point_directions(
    kind, width
):
    prepared, profile, addressed, map_record = _fixture()
    coordinates = np.arange(3 * width, dtype=np.int32).reshape(3, width)
    metadata = {
        **addressed.metadata,
        "scope_address": {"axis": kind, "unit": "retained scope"},
    }
    scoped = ScopedEncoding(
        addressed.status, addressed.encoding, coordinates, kind, metadata
    )
    composer = StudyComposer(prepared, map_record)
    result = composer.add("cartilage", 0, 0, scoped, profile)
    assert result.code is CompositionCode.OK
    assert result.spatial is None
    assert result.metadata["geometry_status"] == "scope_has_no_point_address"
    assert len(result.batches) == 1
    assert result.batches[0].facet_coordinate.direction is None
    assert result.batches[0].addresses.kind == kind
    np.testing.assert_array_equal(result.batches[0].addresses.coordinates, coordinates)
    composer.add("cartilage", 0, 1, scoped, profile)
    assembled = composer.finalize().objects["cartilage"].assembly
    assert assembled is not None
    assert sum(n for _, _, n in assembled.profile.entries) == 2


@pytest.mark.parametrize(
    "coordinates,kind",
    [
        (np.ones((3, 2), dtype=bool), "coarse_grid_rc"),
        (np.ones((3, 2), dtype=float), "coarse_grid_rc"),
        (np.ones((3, 2), dtype=np.int32), "series_slice"),
        (np.array([[-1], [2], [3]], dtype=np.int32), "series_slice"),
        (np.full((3, 1), 2**63, dtype=">u8"), "series_slice"),
        (np.ones((3, 1), dtype=np.int32), "unsupported_scope"),
    ],
)
def test_scoped_malformed_addresses_are_named_refusals(coordinates, kind):
    prepared, profile, addressed, map_record = _fixture()
    scoped = ScopedEncoding(
        addressed.status,
        addressed.encoding,
        coordinates,
        kind,
        {**addressed.metadata, "scope_address": {"axis": kind}},
    )
    result = StudyComposer(prepared, map_record).add("cartilage", 0, 0, scoped, profile)
    assert result.code is CompositionCode.SPATIAL_INPUT_MALFORMED
    assert not result.batches


@pytest.mark.parametrize("scope", [{}, {"invalid": float("nan")}])
def test_scoped_unknown_or_nonfinite_scope_cannot_be_published(scope):
    prepared, profile, addressed, map_record = _fixture()
    scoped = ScopedEncoding(
        addressed.status,
        addressed.encoding,
        np.arange(3, dtype=np.int32)[:, None],
        "series_slice",
        {**addressed.metadata, "scope_address": scope},
    )
    result = StudyComposer(prepared, map_record).add("cartilage", 0, 0, scoped, profile)
    assert result.code is CompositionCode.SPATIAL_INPUT_MALFORMED
    assert not result.batches
