"""Declarative sparse place-to-row encoding for exact count bundles.

The caller declares the bank/metric layout and supplies every reading,
availability mask, and numeric reference.  This module does not fit a middle,
invent a profile, or assign domain meaning to a row.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

import numpy as np
from numpy.typing import NDArray

from knee.encoding.counts import BankLayout as CountBankLayout
from knee.encoding.counts import CountBundle, CountLayout


class MetricKind(StrEnum):
    DIGIT = "digit"
    WORDS = "words"


class EncodingCode(StrEnum):
    OK = "ok"
    SILENT = "silent"
    MISSING_REFERENCE = "missing_reference"
    INVALID_INPUT = "invalid_input"
    IDENTITY_MISMATCH = "identity_mismatch"


@dataclass(frozen=True, slots=True)
class MetricSpec:
    name: str
    kind: MetricKind
    words: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BankSpec:
    name: str
    facet: str
    metrics: tuple[MetricSpec, ...]


@dataclass(frozen=True, slots=True)
class LayoutSpec:
    version: str
    carrier_id: str
    banks: tuple[BankSpec, ...]


@dataclass(frozen=True, slots=True)
class MetricRows:
    bank: str
    facet: str
    metric: str
    start: int
    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CompiledLayout:
    version: str
    carrier_id: str
    banks: tuple[BankSpec, ...]
    fingerprint: str
    count_layout: CountLayout
    metric_rows: tuple[MetricRows, ...]


@dataclass(frozen=True, slots=True)
class NumericReference:
    layout_fingerprint: str
    bank: str
    metric: str
    reference_id: str
    source: str
    units: str
    low: int | float
    high: int | float


@dataclass(frozen=True, slots=True)
class PlaceReading:
    bank: str
    metric: str
    values: NDArray[np.generic]
    available: NDArray[np.bool_]


@dataclass(frozen=True, slots=True)
class MetricEncoding:
    status: EncodingCode
    bank: str
    metric: str
    row_codes: NDArray[np.int16]
    row_names: tuple[str, ...]
    source_values: NDArray[np.generic]
    source_available: NDArray[np.bool_]
    nonfinite_available_count: int
    reference: NumericReference | None = None


@dataclass(frozen=True, slots=True)
class EncodingResult:
    status: EncodingCode
    bundle: CountBundle | None
    metrics: tuple[MetricEncoding, ...]
    reference_set_fingerprint: str | None = None


def _finite_reference_number(value: object) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    return False


def compile_layout(spec: LayoutSpec) -> CompiledLayout | None:
    """Validate a caller's ordered layout and assign sequential bank rows."""
    if not isinstance(spec, LayoutSpec):
        return None
    if not isinstance(spec.version, str) or not spec.version:
        return None
    if not isinstance(spec.carrier_id, str) or not spec.carrier_id:
        return None
    if not isinstance(spec.banks, tuple) or not spec.banks:
        return None
    bank_names: set[str] = set()
    metric_rows: list[MetricRows] = []
    count_banks: list[CountBankLayout] = []
    canonical_banks: list[dict[str, object]] = []
    for bank in spec.banks:
        if not isinstance(bank, BankSpec):
            return None
        if not isinstance(bank.name, str) or not bank.name or bank.name in bank_names:
            return None
        if not isinstance(bank.facet, str) or not bank.facet:
            return None
        if not isinstance(bank.metrics, tuple) or not bank.metrics:
            return None
        bank_names.add(bank.name)
        metric_names: set[str] = set()
        bank_rows: list[dict[str, object]] = []
        row_names: list[str] = []
        for metric in bank.metrics:
            if not isinstance(metric, MetricSpec):
                return None
            if (
                not isinstance(metric.name, str)
                or not metric.name
                or metric.name in metric_names
            ):
                return None
            metric_names.add(metric.name)
            if metric.kind is MetricKind.DIGIT:
                if metric.words != ():
                    return None
                names = ("-1", "0", "+1")
            elif metric.kind is MetricKind.WORDS:
                if not isinstance(metric.words, tuple) or not metric.words:
                    return None
                if any(not isinstance(word, str) or not word for word in metric.words):
                    return None
                if len(set(metric.words)) != len(metric.words):
                    return None
                names = metric.words
            else:
                return None
            metric_rows.append(
                MetricRows(bank.name, bank.facet, metric.name, len(row_names), names)
            )
            row_names.extend(names)
            bank_rows.append(
                {"name": metric.name, "kind": metric.kind.value, "rows": list(names)}
            )
        if len(row_names) > 512:
            return None
        count_banks.append(CountBankLayout(bank.name, 512))
        canonical_banks.append(
            {"name": bank.name, "facet": bank.facet, "metrics": bank_rows}
        )
    canonical = {
        "version": spec.version,
        "carrier_id": spec.carrier_id,
        "banks": canonical_banks,
    }
    serialized = json.dumps(
        canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    fingerprint = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    count_layout = CountLayout(
        layout_id=f"{spec.version}:{fingerprint}",
        carrier_id=spec.carrier_id,
        banks=tuple(count_banks),
    )
    return CompiledLayout(
        spec.version,
        spec.carrier_id,
        spec.banks,
        fingerprint,
        count_layout,
        tuple(metric_rows),
    )


def _valid_reading(reading: object, bank: str, metric: MetricSpec) -> bool:
    if not isinstance(reading, PlaceReading):
        return False
    if reading.bank != bank or reading.metric != metric.name:
        return False
    if not isinstance(reading.values, np.ndarray):
        return False
    if metric.kind is MetricKind.DIGIT and reading.values.dtype.kind not in "iuf":
        return False
    if metric.kind is MetricKind.WORDS and reading.values.dtype.kind not in "Ub":
        return False
    if (
        not isinstance(reading.available, np.ndarray)
        or reading.available.dtype.kind != "b"
    ):
        return False
    return reading.values.shape == reading.available.shape


def _valid_reference(
    reference: object, layout: CompiledLayout, bank: str, metric: str
) -> EncodingCode:
    if not isinstance(reference, NumericReference):
        return EncodingCode.INVALID_INPUT
    if (
        reference.layout_fingerprint != layout.fingerprint
        or reference.bank != bank
        or reference.metric != metric
    ):
        return EncodingCode.IDENTITY_MISMATCH
    if any(
        not isinstance(value, str) or not value
        for value in (reference.reference_id, reference.source, reference.units)
    ):
        return EncodingCode.INVALID_INPUT
    if not _finite_reference_number(reference.low) or not _finite_reference_number(
        reference.high
    ):
        return EncodingCode.INVALID_INPUT
    if reference.low > reference.high:
        return EncodingCode.INVALID_INPUT
    return EncodingCode.OK


def _metric_rows(layout: CompiledLayout, bank: str, metric: str) -> MetricRows:
    return next(
        item
        for item in layout.metric_rows
        if item.bank == bank and item.metric == metric
    )


def _reference_value(value: float) -> dict[str, object]:
    return {"type": type(value).__name__, "value": value}


def _reference_set_fingerprint(
    layout: CompiledLayout,
    references: Mapping[tuple[str, str], NumericReference],
) -> str | None:
    rows: list[dict[str, object]] = []
    for bank in layout.banks:
        for metric in bank.metrics:
            if metric.kind is not MetricKind.DIGIT:
                continue
            key = (bank.name, metric.name)
            reference = references.get(key)
            if reference is None:
                rows.append(
                    {"bank": bank.name, "metric": metric.name, "reference": None}
                )
                continue
            if not isinstance(reference, NumericReference):
                return None
            if (
                not _finite_reference_number(reference.low)
                or not _finite_reference_number(reference.high)
                or not all(
                    isinstance(value, str) and value
                    for value in (
                        reference.layout_fingerprint,
                        reference.bank,
                        reference.metric,
                        reference.reference_id,
                        reference.source,
                        reference.units,
                    )
                )
            ):
                return None
            rows.append(
                {
                    "bank": bank.name,
                    "metric": metric.name,
                    "reference": {
                        "layout_fingerprint": reference.layout_fingerprint,
                        "bank": reference.bank,
                        "metric": reference.metric,
                        "reference_id": reference.reference_id,
                        "source": reference.source,
                        "units": reference.units,
                        "low": _reference_value(reference.low),
                        "high": _reference_value(reference.high),
                    },
                }
            )
    canonical = {"layout_fingerprint": layout.fingerprint, "references": rows}
    serialized = json.dumps(
        canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _bound_count_layout(
    layout: CompiledLayout, reference_set_fingerprint: str
) -> CountLayout:
    return CountLayout(
        layout_id=(
            f"{layout.version}:{layout.fingerprint}:{reference_set_fingerprint}"
        ),
        carrier_id=layout.carrier_id,
        banks=tuple(CountBankLayout(bank.name, 512) for bank in layout.banks),
    )


def _reference_edge_is_exact_float64(value: float) -> bool:
    if isinstance(value, int):
        return -(1 << 53) <= value <= (1 << 53)
    return True


def _can_vectorize_digit_compare(
    values: NDArray[np.generic], low: float, high: float
) -> bool:
    """Return true only when widening values and edges to float64 is exact."""
    if not (
        _reference_edge_is_exact_float64(low) and _reference_edge_is_exact_float64(high)
    ):
        return False
    if values.dtype.kind == "f":
        return values.dtype.itemsize <= 8
    if values.dtype.kind in "iu":
        return values.dtype.itemsize <= 4
    return False


def _digit_row_codes(
    values: NDArray[np.generic],
    available: NDArray[np.bool_],
    low: float,
    high: float,
    row_start: int,
) -> tuple[NDArray[np.int16], int]:
    """Encode digits with an exact vector path or exact scalar fallback."""
    row_codes = np.full(values.shape, -1, dtype=np.int16)
    finite = np.isfinite(values)
    writable = available & finite
    nonfinite_count = int(np.count_nonzero(available & ~finite))
    if _can_vectorize_digit_compare(values, low, high):
        # float16/32 and small integers widen losslessly; float64 stays as-is.
        widened = values.astype(np.float64, copy=False)
        low64 = float(low)
        high64 = float(high)
        row_codes[writable & (widened < low64)] = row_start
        row_codes[writable & (widened > high64)] = row_start + 2
        middle = writable & (widened >= low64) & (widened <= high64)
        row_codes[middle] = row_start + 1
        return row_codes, nonfinite_count

    # Exact fallback for 64-bit integers/unsafe edges. NumPy scalars become
    # their native Python scalar without changing integer precision.
    for index in np.ndindex(values.shape):
        if not writable[index]:
            continue
        value = values[index].item()
        if value < low:
            row_codes[index] = row_start
        elif value > high:
            row_codes[index] = row_start + 2
        else:
            row_codes[index] = row_start + 1
    return row_codes, nonfinite_count


def encode_places(
    layout: CompiledLayout,
    readings: Mapping[tuple[str, str], PlaceReading],
    references: Mapping[tuple[str, str], NumericReference],
) -> EncodingResult:
    """Encode all declared metrics into sparse row indexes and exact counts.

    A row code of -1 means this place did not write that metric.  Digit row
    indexes 0, 1, 2 name the distinct -1, 0, +1 rows respectively.
    """
    if (
        not isinstance(layout, CompiledLayout)
        or not isinstance(readings, Mapping)
        or not isinstance(references, Mapping)
    ):
        return EncodingResult(EncodingCode.INVALID_INPUT, None, ())
    expected = {
        (bank.name, metric.name): metric
        for bank in layout.banks
        for metric in bank.metrics
    }
    if set(readings) != set(expected):
        return EncodingResult(EncodingCode.INVALID_INPUT, None, ())
    if any(
        key not in expected or not isinstance(key, tuple) or len(key) != 2
        for key in readings
    ):
        return EncodingResult(EncodingCode.INVALID_INPUT, None, ())
    reference_fp = _reference_set_fingerprint(layout, references)
    if reference_fp is None:
        return EncodingResult(EncodingCode.INVALID_INPUT, None, ())
    if any(
        key not in expected or not isinstance(key, tuple) or len(key) != 2
        for key in references
    ):
        return EncodingResult(EncodingCode.INVALID_INPUT, None, ())

    shapes: set[tuple[int, ...]] = set()
    for key, reading in readings.items():
        if not _valid_reading(reading, key[0], expected[key[0], key[1]]):
            return EncodingResult(EncodingCode.INVALID_INPUT, None, ())
        shapes.add(reading.values.shape)
    if len(shapes) > 1 or not shapes:
        return EncodingResult(EncodingCode.INVALID_INPUT, None, ())
    bank_counts: dict[str, list[int]] = {
        bank.name: [0]
        * next(
            item for item in layout.count_layout.banks if item.name == bank.name
        ).row_count
        for bank in layout.banks
    }
    encoded: list[MetricEncoding] = []
    any_invalid = False
    identity_mismatch = False
    missing_reference = False
    any_written = False
    for bank in layout.banks:
        for metric in bank.metrics:
            key = (bank.name, metric.name)
            rows = _metric_rows(layout, bank.name, metric.name)
            reading = readings.get(key)
            if reading is None:
                return EncodingResult(EncodingCode.INVALID_INPUT, None, tuple(encoded))
            row_codes = np.full(reading.values.shape, -1, dtype=np.int16)
            status = EncodingCode.OK
            nonfinite_count = 0
            if metric.kind is MetricKind.DIGIT:
                reference = references.get(key)
                if reference is None:
                    if np.any(reading.available):
                        status = EncodingCode.MISSING_REFERENCE
                        missing_reference = True
                    else:
                        status = EncodingCode.SILENT
                else:
                    status = _valid_reference(reference, layout, bank.name, metric.name)
                    if status is EncodingCode.IDENTITY_MISMATCH:
                        identity_mismatch = True
                    elif status is EncodingCode.OK:
                        row_codes, nonfinite_count = _digit_row_codes(
                            reading.values,
                            reading.available,
                            reference.low,
                            reference.high,
                            rows.start,
                        )
            else:
                word_to_row = {
                    word: rows.start + index for index, word in enumerate(metric.words)
                }
                if key in references:
                    status = EncodingCode.INVALID_INPUT
                elif reading.values.dtype.kind == "b":
                    boolean_values = reading.values.astype(np.bool_, copy=False)
                    false_row = word_to_row.get("False")
                    true_row = word_to_row.get("True")
                    observed_false = reading.available & ~boolean_values
                    observed_true = reading.available & boolean_values
                    if (np.any(observed_false) and false_row is None) or (
                        np.any(observed_true) and true_row is None
                    ):
                        status = EncodingCode.INVALID_INPUT
                    else:
                        if false_row is not None:
                            row_codes[observed_false] = false_row
                        if true_row is not None:
                            row_codes[observed_true] = true_row
                else:
                    unknown = reading.available & ~np.isin(reading.values, metric.words)
                    if np.any(unknown):
                        status = EncodingCode.INVALID_INPUT
                    else:
                        for word, row in word_to_row.items():
                            row_codes[reading.available & (reading.values == word)] = (
                                row
                            )

            if status is EncodingCode.INVALID_INPUT:
                any_invalid = True
                row_codes.fill(-1)
            elif status is EncodingCode.IDENTITY_MISMATCH:
                identity_mismatch = True
                row_codes.fill(-1)
            elif status is EncodingCode.MISSING_REFERENCE:
                pass
            else:
                selected_codes = (
                    row_codes[row_codes >= 0].astype(np.intp, copy=False) - rows.start
                )
                metric_counts = np.bincount(selected_codes, minlength=len(rows.names))
                for offset, count in enumerate(metric_counts):
                    bank_counts[bank.name][rows.start + offset] += int(count)
                if selected_codes.size:
                    any_written = True
                else:
                    status = EncodingCode.SILENT
            row_codes.flags.writeable = False
            encoded.append(
                MetricEncoding(
                    status,
                    bank.name,
                    metric.name,
                    row_codes,
                    rows.names,
                    reading.values,
                    reading.available,
                    nonfinite_count,
                    references.get(key) if metric.kind is MetricKind.DIGIT else None,
                )
            )

    if identity_mismatch:
        return EncodingResult(
            EncodingCode.IDENTITY_MISMATCH, None, tuple(encoded), reference_fp
        )
    if any_invalid:
        return EncodingResult(
            EncodingCode.INVALID_INPUT, None, tuple(encoded), reference_fp
        )
    bundle = CountBundle(
        _bound_count_layout(layout, reference_fp),
        tuple(tuple(bank_counts[bank.name]) for bank in layout.banks),
    )
    if missing_reference:
        overall = EncodingCode.MISSING_REFERENCE
    else:
        overall = EncodingCode.OK if any_written else EncodingCode.SILENT
    return EncodingResult(overall, bundle, tuple(encoded), reference_fp)


def decode_count_names(
    layout: CompiledLayout,
    bundle: CountBundle,
    reference_set_fingerprint: str,
) -> tuple[tuple[str, str, str, str, int], ...] | None:
    """Return every bank/facet/metric/row name and its exact count."""
    if not isinstance(layout, CompiledLayout) or not isinstance(bundle, CountBundle):
        return None
    if (
        not isinstance(reference_set_fingerprint, str)
        or len(reference_set_fingerprint) != 64
        or any(
            character not in "0123456789abcdef"
            for character in reference_set_fingerprint
        )
    ):
        return None
    expected_layout = _bound_count_layout(layout, reference_set_fingerprint)
    if bundle.layout != expected_layout:
        return None
    if not isinstance(bundle.counts, tuple) or len(bundle.counts) != len(layout.banks):
        return None
    assigned_rows: list[set[int]] = [set() for _ in layout.banks]
    for bank_index, bank in enumerate(layout.banks):
        for row in layout.metric_rows:
            if row.bank == bank.name:
                assigned_rows[bank_index].update(
                    range(row.start, row.start + len(row.names))
                )
        bank_counts = bundle.counts[bank_index]
        if not isinstance(bank_counts, tuple) or len(bank_counts) != 512:
            return None
        if any(
            not isinstance(count, int) or isinstance(count, bool) or count < 0
            for count in bank_counts
        ):
            return None
        if any(
            count != 0
            for row_index, count in enumerate(bank_counts)
            if row_index not in assigned_rows[bank_index]
        ):
            return None
    out: list[tuple[str, str, str, str, int]] = []
    for bank_index, bank in enumerate(layout.banks):
        for row in layout.metric_rows:
            if row.bank != bank.name:
                continue
            for offset, row_name in enumerate(row.names):
                out.append(
                    (
                        bank.name,
                        row.facet,
                        row.metric,
                        row_name,
                        bundle.counts[bank_index][row.start + offset],
                    )
                )
    return tuple(out)
