from __future__ import annotations

import json
from dataclasses import replace

import numpy as np

from knee.collapse import anatomical_relations
from knee.collapse.anatomical_relations import SOURCE, relationships_for
from knee.encoding import mri_definition_context as definition
from knee.encoding.carrier import ROW_WIDTH
from knee.encoding.mri_spec import make_mri_spec
from knee.encoding.operation import validate_spec


def _acl_relations() -> list[dict[str, object]]:
    return relationships_for(("acl", "femur", "tibia"))["acl"]


def _counts(prepared, bundle) -> tuple[int, ...]:
    assert bundle.layout.carrier_id == prepared.carrier.identity
    return bundle.counts[0]


def test_preparation_is_shared_stable_and_definition_only() -> None:
    first = definition.prepare_definition_context()
    second = definition.prepare_definition_context()
    assert first.code is definition.DefinitionCode.OK
    assert first is second
    assert first.prepared is not None
    prepared = first.prepared
    assert len(prepared.statement_words) <= ROW_WIDTH
    assert len(prepared.statement_words) == len(set(prepared.statement_words))
    assert prepared.layout.version == "knee-authored-definition-context-v1"
    assert prepared.layout.carrier_id == prepared.carrier.identity
    assert prepared.layout.count_layout.carrier_id == prepared.carrier.identity
    measured_layout = validate_spec(make_mri_spec())["layout"]
    assert prepared.layout.fingerprint != measured_layout.fingerprint
    assert prepared.layout.count_layout != measured_layout.count_layout
    assert prepared.layout.banks[0].name == "authored_definition"
    assert prepared.layout.banks[0].metrics[0].name == "relation_statement"
    assert "anatomical_definition" in prepared.statement_words[0]


def test_exact_authored_relation_encodes_full_statement_without_spatial_address() -> (
    None
):
    preparation = definition.prepare_definition_context()
    assert preparation.prepared is not None
    prepared = preparation.prepared
    relations = _acl_relations()

    result = definition.encode_definition_context(prepared, "acl", relations)

    assert result.code is definition.DefinitionCode.OK
    assert result.address_kind == "object_definition"
    assert result.coordinates is None
    assert result.original_relation_records == tuple(relations)
    assert result.unique_relation_records == tuple(relations)
    assert result.row_codes is not None and result.row_codes.shape == (1,)
    assert json.loads(result.statement_words[0]) == relations[0]
    assert result.unique_row_codes is not None
    assert result.unique_row_codes.shape == (1,)
    assert result.bundle is not None
    assert result.vector is not None
    assert result.vector.dtype == np.dtype(np.int32)
    assert result.vector.shape == (1, ROW_WIDTH)
    assert result.layout_fingerprint == prepared.layout.fingerprint
    assert result.carrier_identity == prepared.carrier.identity
    assert result.count_layout_identity == result.bundle.layout.layout_id
    counts = _counts(prepared, result.bundle)
    row = int(result.row_codes[0])
    assert counts[row] == 1
    np.testing.assert_array_equal(
        prepared.carrier.decode(result.vector), [result.bundle.counts[0]]
    )


def test_identical_declaration_counts_once_but_retains_each_original_record() -> None:
    preparation = definition.prepare_definition_context()
    assert preparation.prepared is not None
    relation = _acl_relations()[0]

    result = definition.encode_definition_context(
        preparation.prepared, "acl", [relation, dict(relation)]
    )

    assert result.code is definition.DefinitionCode.OK
    assert len(result.original_relation_records) == 2
    assert len(result.unique_relation_records) == 1
    assert result.row_codes is not None
    assert result.row_codes[0] == result.row_codes[1]
    assert result.unique_row_codes is not None
    assert result.unique_row_codes.shape == (1,)
    assert result.bundle is not None
    counts = _counts(preparation.prepared, result.bundle)
    assert counts[int(result.row_codes[0])] == 1
    assert sum(counts) == 1


def test_missing_incomplete_and_empty_authored_contexts_are_distinct() -> None:
    prepared = definition.prepare_definition_context().prepared
    assert prepared is not None

    missing = definition.encode_definition_context(prepared, "acl", None)
    incomplete = definition.encode_definition_context(prepared, "acl", [])
    no_definition = definition.encode_definition_context(prepared, "fibula", [])

    assert missing.code is definition.DefinitionCode.CONTEXT_UNAVAILABLE
    assert incomplete.code is definition.DefinitionCode.RELATIONS_INCOMPLETE
    assert no_definition.code is definition.DefinitionCode.NO_AUTHORED_DEFINITION
    for result in (missing, incomplete, no_definition):
        assert result.bundle is None
        assert result.vector is None
        assert result.row_codes is None


def test_changed_relation_fields_never_become_an_authored_row() -> None:
    prepared = definition.prepare_definition_context().prepared
    assert prepared is not None
    original = _acl_relations()[0]
    changes = (
        ("predicate", "between"),
        ("targets", ["tibia", "femur"]),
        ("qualifier", "invented qualifier"),
    )
    for field, value in changes:
        changed = dict(original)
        changed[field] = value
        result = definition.encode_definition_context(prepared, "acl", [changed])
        assert result.code is definition.DefinitionCode.RELATION_NOT_AUTHORED
        assert result.bundle is None
        assert result.vector is None


def test_incomplete_multi_relation_context_does_not_encode_a_partial_definition() -> (
    None
):
    prepared = definition.prepare_definition_context().prepared
    assert prepared is not None
    mcl_relations = relationships_for(("mcl", "femur", "tibia", "medial_meniscus"))[
        "mcl"
    ]
    assert len(mcl_relations) == 2

    partial = definition.encode_definition_context(prepared, "mcl", mcl_relations[:1])

    assert partial.code is definition.DefinitionCode.RELATIONS_INCOMPLETE
    assert partial.bundle is None
    assert partial.vector is None


def test_source_basis_subject_and_malformed_records_have_named_refusals() -> None:
    prepared = definition.prepare_definition_context().prepared
    assert prepared is not None
    original = _acl_relations()[0]

    wrong_source = dict(original, source="another source")
    wrong_basis = dict(original, basis="measured_relation")
    wrong_subject = dict(original, subject="pcl")
    extra_field = dict(original, satisfied=True)
    wrong_targets_type = dict(original, targets=("femur", "tibia"))

    source_refusal = definition.encode_definition_context(
        prepared, "acl", [wrong_source]
    )
    assert source_refusal.code is definition.DefinitionCode.SOURCE_MISMATCH
    assert source_refusal.original_relation_records == (wrong_source,)
    assert (
        definition.encode_definition_context(prepared, "acl", [wrong_basis]).code
        is definition.DefinitionCode.BASIS_MISMATCH
    )
    assert (
        definition.encode_definition_context(prepared, "acl", [wrong_subject]).code
        is definition.DefinitionCode.SUBJECT_MISMATCH
    )
    for malformed in (extra_field, wrong_targets_type, "acl"):
        result = definition.encode_definition_context(prepared, "acl", [malformed])
        assert result.code is definition.DefinitionCode.RECORD_MALFORMED
        assert result.bundle is None


def test_unknown_object_and_nonsequence_context_are_not_negative_rows() -> None:
    prepared = definition.prepare_definition_context().prepared
    assert prepared is not None

    unknown = definition.encode_definition_context(prepared, "not_an_object", [])
    malformed = definition.encode_definition_context(prepared, "acl", "not records")

    assert unknown.code is definition.DefinitionCode.OBJECT_NOT_IN_RELATION_CATALOGUE
    assert malformed.code is definition.DefinitionCode.RELATIONS_MALFORMED
    assert unknown.bundle is None and malformed.bundle is None


def test_malformed_prepared_vocabulary_is_a_named_refusal() -> None:
    prepared = definition.prepare_definition_context().prepared
    assert prepared is not None
    malformed = replace(prepared, word_to_row={})

    result = definition.encode_definition_context(malformed, "acl", _acl_relations())

    assert result.code is definition.DefinitionCode.PREPARATION_INVALID
    assert result.bundle is None


def test_preparation_refuses_a_word_vocabulary_larger_than_the_carrier(
    monkeypatch,
) -> None:
    definition.prepare_definition_context.cache_clear()
    over_limit = tuple(
        (
            "femur",
            f"predicate_{index}",
            ("tibia",),
            f"qualifier_{index}",
            SOURCE,
        )
        for index in range(ROW_WIDTH + 1)
    )
    monkeypatch.setattr(anatomical_relations, "RELATIONSHIPS", over_limit)
    try:
        result = definition.prepare_definition_context()
        assert result.code is definition.DefinitionCode.VOCABULARY_TOO_LARGE
        assert result.prepared is None
    finally:
        definition.prepare_definition_context.cache_clear()
