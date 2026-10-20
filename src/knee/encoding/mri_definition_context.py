"""Exact, separate HDC role for authored anatomical definitions.

This module encodes only the sourced definition records already retained by
``describe_objects``. Its carrier and layout are deliberately independent of
measured MRI banks; its rows are never evidence that a relation was measured
or satisfied.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from types import MappingProxyType
from typing import Any

import numpy as np
from numpy.typing import NDArray

from knee.collapse.anatomical_relations import BASIS, SOURCE, relationships_for
from knee.collapse.study_map import OBJECTS
from knee.encoding.carrier import ROW_WIDTH, HadamardCarrier
from knee.encoding.counts import CountBundle
from knee.encoding.places import (
    BankSpec,
    CompiledLayout,
    EncodingCode,
    LayoutSpec,
    MetricEncoding,
    MetricKind,
    MetricSpec,
    PlaceReading,
    compile_layout,
    encode_places,
)

_BANK_NAME = "authored_definition"
_METRIC_NAME = "relation_statement"
_VERSION = "knee-authored-definition-context-v1"
_FIELDS = ("subject", "predicate", "targets", "qualifier", "source", "basis")


class DefinitionCode(StrEnum):
    OK = "ok"
    PREPARATION_INVALID = "preparation_invalid"
    VOCABULARY_TOO_LARGE = "definition_vocabulary_exceeds_512"
    OBJECT_NAME_MALFORMED = "object_name_malformed"
    OBJECT_NOT_IN_RELATION_CATALOGUE = "object_not_in_relation_catalogue"
    CONTEXT_UNAVAILABLE = "definition_context_unavailable"
    NO_AUTHORED_DEFINITION = "no_authored_definition"
    RELATIONS_INCOMPLETE = "retained_definition_context_incomplete"
    RELATIONS_MALFORMED = "retained_relations_malformed"
    RECORD_MALFORMED = "definition_record_malformed"
    SUBJECT_MISMATCH = "definition_subject_mismatch"
    SOURCE_MISMATCH = "definition_source_mismatch"
    BASIS_MISMATCH = "definition_basis_mismatch"
    RELATION_NOT_AUTHORED = "relation_not_in_authored_catalogue"
    ENCODING_FAILED = "definition_encoding_failed"


@dataclass(frozen=True, slots=True)
class PreparedDefinitionContext:
    """Immutable shared layout, carrier and statement vocabulary."""

    layout: CompiledLayout
    carrier: HadamardCarrier
    statement_words: tuple[str, ...]
    word_to_row: Mapping[str, int]
    known_objects: frozenset[str]
    expected_words_by_object: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True, slots=True)
class DefinitionPreparation:
    code: DefinitionCode
    prepared: PreparedDefinitionContext | None = None
    detail: str = ""


@dataclass(frozen=True, slots=True)
class DefinitionContextEncoding:
    code: DefinitionCode
    object_name: str | None = None
    address_kind: str = "object_definition"
    coordinates: None = None
    original_relation_records: tuple[Any, ...] = ()
    unique_relation_records: tuple[dict[str, Any], ...] = ()
    statement_words: tuple[str, ...] = ()
    row_codes: NDArray[np.int16] | None = None
    unique_row_codes: NDArray[np.int16] | None = None
    bundle: CountBundle | None = None
    vector: NDArray[np.int32] | None = None
    layout_fingerprint: str | None = None
    count_layout_identity: str | None = None
    carrier_identity: str | None = None
    detail: str = ""


def _statement_word(record: Mapping[str, Any]) -> str:
    """Serialize the complete typed statement with ordered targets preserved."""
    payload = {
        "basis": record["basis"],
        "predicate": record["predicate"],
        "qualifier": record["qualifier"],
        "source": record["source"],
        "subject": record["subject"],
        "targets": record["targets"],
    }
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _catalogue_records(
    by_object: Mapping[str, list[dict[str, object]]],
) -> tuple[dict[str, Any], ...]:
    records = []
    seen: set[str] = set()
    for object_name in OBJECTS:
        for record in by_object.get(object_name, ()):
            word = _statement_word(record)
            if word not in seen:
                seen.add(word)
                records.append(record)
    return tuple(records)


@lru_cache(maxsize=1)
def prepare_definition_context() -> DefinitionPreparation:
    """Prepare the shared 512-row definition-only vocabulary once."""
    by_object = relationships_for(OBJECTS)
    records = _catalogue_records(by_object)
    words = tuple(_statement_word(record) for record in records)
    if not words:
        return DefinitionPreparation(
            DefinitionCode.PREPARATION_INVALID,
            detail="authored_definition_vocabulary_is_empty",
        )
    if len(words) > ROW_WIDTH:
        return DefinitionPreparation(DefinitionCode.VOCABULARY_TOO_LARGE)
    carrier = HadamardCarrier.from_banks((_BANK_NAME,))
    layout = compile_layout(
        LayoutSpec(
            _VERSION,
            carrier.identity,
            (
                BankSpec(
                    _BANK_NAME,
                    "sourced authored anatomical definition; not measured satisfaction",
                    (
                        MetricSpec(
                            _METRIC_NAME,
                            MetricKind.WORDS,
                            words,
                        ),
                    ),
                ),
            ),
        )
    )
    if layout is None:
        return DefinitionPreparation(DefinitionCode.PREPARATION_INVALID)
    expected_words_by_object = {
        object_name: tuple(
            _statement_word(record) for record in by_object.get(object_name, ())
        )
        for object_name in OBJECTS
    }
    return DefinitionPreparation(
        DefinitionCode.OK,
        PreparedDefinitionContext(
            layout,
            carrier,
            words,
            MappingProxyType({word: index for index, word in enumerate(words)}),
            frozenset(OBJECTS),
            MappingProxyType(expected_words_by_object),
        ),
    )


def _copy_record(record: Mapping[str, Any]) -> dict[str, Any]:
    copied = dict(record)
    copied["targets"] = list(record["targets"])
    return copied


def _snapshot_input_records(value: object) -> tuple[Any, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    saved: list[Any] = []
    for record in value:
        if isinstance(record, Mapping):
            copied = dict(record)
            if isinstance(record.get("targets"), list):
                copied["targets"] = list(record["targets"])
            saved.append(copied)
        else:
            saved.append(record)
    return tuple(saved)


def _validated_records(
    prepared: PreparedDefinitionContext,
    object_name: str,
    retained_relations: object,
) -> tuple[DefinitionCode, tuple[dict[str, Any], ...], tuple[str, ...], str]:
    if retained_relations is None:
        return DefinitionCode.CONTEXT_UNAVAILABLE, (), (), "relations_missing_or_null"
    if not isinstance(retained_relations, (list, tuple)):
        return (
            DefinitionCode.RELATIONS_MALFORMED,
            (),
            (),
            "relations_must_be_a_sequence",
        )
    if not retained_relations:
        expected = prepared.expected_words_by_object.get(object_name, ())
        code = (
            DefinitionCode.RELATIONS_INCOMPLETE
            if expected
            else DefinitionCode.NO_AUTHORED_DEFINITION
        )
        return code, (), (), "retained_relation_records_missing" if expected else ""

    records: list[dict[str, Any]] = []
    words: list[str] = []
    seen: set[str] = set()
    required = set(_FIELDS)
    for index, record in enumerate(retained_relations):
        if not isinstance(record, Mapping) or set(record) != required:
            return (
                DefinitionCode.RECORD_MALFORMED,
                (),
                (),
                f"relation_{index}_fields_must_match_authored_record",
            )
        if (
            any(not isinstance(record[key], str) for key in _FIELDS if key != "targets")
            or not isinstance(record["targets"], list)
            or not record["targets"]
            or any(
                not isinstance(target, str) or not target
                for target in record["targets"]
            )
        ):
            return (
                DefinitionCode.RECORD_MALFORMED,
                (),
                (),
                f"relation_{index}_typed_fields_invalid",
            )
        if record["subject"] != object_name:
            return (
                DefinitionCode.SUBJECT_MISMATCH,
                (),
                (),
                f"relation_{index}_subject_differs_from_object",
            )
        if record["source"] != SOURCE:
            return (
                DefinitionCode.SOURCE_MISMATCH,
                (),
                (),
                f"relation_{index}_source_differs_from_authored_source",
            )
        if record["basis"] != BASIS:
            return (
                DefinitionCode.BASIS_MISMATCH,
                (),
                (),
                f"relation_{index}_basis_is_not_anatomical_definition",
            )
        copied = _copy_record(record)
        word = _statement_word(copied)
        if word not in prepared.word_to_row:
            return (
                DefinitionCode.RELATION_NOT_AUTHORED,
                (),
                (),
                f"relation_{index}_does_not_match_authored_catalogue",
            )
        records.append(copied)
        if word not in seen:
            seen.add(word)
            words.append(word)
    if set(words) != set(prepared.expected_words_by_object.get(object_name, ())):
        return (
            DefinitionCode.RELATIONS_INCOMPLETE,
            (),
            (),
            "retained_relation_set_differs_from_authored_object_context",
        )
    return DefinitionCode.OK, tuple(records), tuple(words), ""


def encode_definition_context(
    prepared: PreparedDefinitionContext,
    object_name: str,
    retained_relations: object,
) -> DefinitionContextEncoding:
    """Encode exact retained authored relations without spatial addresses."""
    original_records = _snapshot_input_records(retained_relations)
    if (
        not isinstance(prepared, PreparedDefinitionContext)
        or not isinstance(prepared.layout, CompiledLayout)
        or not isinstance(prepared.carrier, HadamardCarrier)
        or not isinstance(prepared.statement_words, tuple)
        or not isinstance(prepared.word_to_row, Mapping)
        or not isinstance(prepared.expected_words_by_object, Mapping)
        or not isinstance(prepared.known_objects, frozenset)
        or prepared.layout.carrier_id != prepared.carrier.identity
        or prepared.layout.count_layout.carrier_id != prepared.carrier.identity
        or len(prepared.layout.banks) != 1
        or prepared.layout.banks[0].name != _BANK_NAME
        or len(prepared.layout.banks[0].metrics) != 1
        or prepared.layout.banks[0].metrics[0].name != _METRIC_NAME
        or prepared.layout.banks[0].metrics[0].kind is not MetricKind.WORDS
        or prepared.layout.banks[0].metrics[0].words != prepared.statement_words
        or dict(prepared.word_to_row)
        != {word: index for index, word in enumerate(prepared.statement_words)}
    ):
        return DefinitionContextEncoding(
            DefinitionCode.PREPARATION_INVALID,
            original_relation_records=original_records,
        )
    if not isinstance(object_name, str) or not object_name:
        return DefinitionContextEncoding(
            DefinitionCode.OBJECT_NAME_MALFORMED,
            original_relation_records=original_records,
        )
    if object_name not in prepared.known_objects:
        return DefinitionContextEncoding(
            DefinitionCode.OBJECT_NOT_IN_RELATION_CATALOGUE,
            object_name=object_name,
            original_relation_records=original_records,
        )
    code, records, words, detail = _validated_records(
        prepared, object_name, retained_relations
    )
    if code is not DefinitionCode.OK:
        return DefinitionContextEncoding(
            code,
            object_name=object_name,
            original_relation_records=original_records,
            detail=detail,
        )

    values = np.asarray(words, dtype=np.str_)
    available = np.ones(values.shape, dtype=np.bool_)
    encoded = encode_places(
        prepared.layout,
        {
            (_BANK_NAME, _METRIC_NAME): PlaceReading(
                _BANK_NAME,
                _METRIC_NAME,
                values,
                available,
            )
        },
        {},
    )
    metric: MetricEncoding | None = next(
        (
            item
            for item in encoded.metrics
            if (item.bank, item.metric) == (_BANK_NAME, _METRIC_NAME)
        ),
        None,
    )
    if (
        encoded.status is not EncodingCode.OK
        or encoded.bundle is None
        or metric is None
    ):
        return DefinitionContextEncoding(
            DefinitionCode.ENCODING_FAILED,
            object_name=object_name,
            original_relation_records=records,
            detail=encoded.status.value,
        )
    try:
        vector = prepared.carrier.encode(
            np.asarray(encoded.bundle.counts, dtype=np.int64)
        )
    except (TypeError, ValueError, OverflowError) as error:
        return DefinitionContextEncoding(
            DefinitionCode.ENCODING_FAILED,
            object_name=object_name,
            original_relation_records=records,
            detail=type(error).__name__,
        )

    row_codes = np.asarray(
        [prepared.word_to_row[_statement_word(record)] for record in records],
        dtype=np.int16,
    )
    unique_row_codes = metric.row_codes.copy()
    row_codes.flags.writeable = False
    unique_row_codes.flags.writeable = False
    vector.flags.writeable = False
    # Repeated identical declarations have one word/count but keep every original link.
    unique_records = tuple(
        {_statement_word(record): record for record in records}[word] for word in words
    )
    return DefinitionContextEncoding(
        DefinitionCode.OK,
        object_name,
        original_relation_records=records,
        unique_relation_records=unique_records,
        statement_words=words,
        row_codes=row_codes,
        unique_row_codes=unique_row_codes,
        bundle=encoded.bundle,
        vector=vector,
        layout_fingerprint=prepared.layout.fingerprint,
        count_layout_identity=encoded.bundle.layout.layout_id,
        carrier_identity=prepared.carrier.identity,
    )


def serialize_definition_contexts(
    preparation: DefinitionPreparation,
    object_contexts: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, NDArray], dict[str, Any]]:
    """Publish a definition subfacet per object, separate from measured spatial banks."""
    prepared = preparation.prepared
    arrays: dict[str, NDArray] = {}
    metadata: dict[str, Any] = {
        "schema": "knee_authored_definition_context/v1",
        "role": "anatomical_definition",
        "preparation_status": preparation.code.value,
        "meaning": "sourced definitions only; not measured relation satisfaction or diagnosis",
        "objects": {},
    }
    if prepared is None:
        return arrays, metadata
    metadata.update(
        carrier_identity=prepared.carrier.identity,
        layout_fingerprint=prepared.layout.fingerprint,
        count_layout_id=prepared.layout.count_layout.layout_id,
        bank=_BANK_NAME,
        metric=_METRIC_NAME,
        statement_vocabulary=list(prepared.statement_words),
    )
    for index, (name, context) in enumerate(object_contexts.items()):
        result = encode_definition_context(
            prepared, name, context.get("anatomical_relations")
        )
        item: dict[str, Any] = {
            "status": result.code.value,
            "detail": result.detail,
            "address_kind": result.address_kind,
            "coordinates": None,
            "original_relations": list(result.original_relation_records),
            "unique_relations": list(result.unique_relation_records),
            "layout_fingerprint": result.layout_fingerprint,
            "count_layout_id": result.count_layout_identity,
            "carrier_identity": result.carrier_identity,
        }
        if result.bundle is not None:
            for field, value in (
                ("row_codes", result.row_codes),
                ("unique_row_codes", result.unique_row_codes),
                ("counts", np.asarray(result.bundle.counts, dtype=np.int64)),
                ("carrier_vector", result.vector),
            ):
                if value is not None:
                    key = f"definition_object_{index}_{field}"
                    arrays[key] = value
                    item[field] = key
        metadata["objects"][name] = item
    return arrays, metadata
