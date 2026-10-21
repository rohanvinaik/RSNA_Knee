"""Adapt retained object-composition products into diagnostic Profile records.

This is a reader only: it does not recognize images, infer labels, or create
reference identities.  A profile's CountBundle is rebuilt from the product's
exact sparse count rows under the serialized layout identity.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from knee.diagnosis.models import Profile
from knee.encoding.counts import BankLayout, CountBundle, CountLayout
from knee.encoding.places import (
    BankSpec,
    CompiledLayout,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    compile_layout,
)
from knee.encoding.product import open_product


class ProductProfileError(ValueError):
    """A retained product cannot be interpreted as object Profiles."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _object_error(code: str, object_name: str | None = None) -> ProductProfileError:
    suffix = "" if object_name is None else f":{object_name}"
    return ProductProfileError(f"{code}{suffix}")


def _required_text(value: object, code: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProductProfileError(code)
    return value


def _compiled_layout(manifest: dict[str, Any]) -> CompiledLayout:
    description = manifest.get("layout")
    if not isinstance(description, dict):
        raise ProductProfileError("layout_missing_or_malformed")
    version = _required_text(description.get("version"), "layout_version_missing")
    carrier_id = _required_text(
        description.get("carrier_id"), "layout_carrier_id_missing"
    )
    banks_data = description.get("banks")
    if not isinstance(banks_data, list) or not banks_data:
        raise ProductProfileError("layout_banks_missing_or_malformed")
    banks: list[BankSpec] = []
    try:
        for bank in banks_data:
            if not isinstance(bank, dict):
                raise TypeError("bank_not_object")
            name = _required_text(bank.get("name"), "layout_bank_name_missing")
            facet = _required_text(bank.get("facet"), "layout_bank_facet_missing")
            metrics_data = bank.get("metrics")
            if not isinstance(metrics_data, list) or not metrics_data:
                raise ValueError("metrics_missing")
            metrics: list[MetricSpec] = []
            for metric in metrics_data:
                if not isinstance(metric, dict):
                    raise TypeError("metric_not_object")
                metric_name = _required_text(
                    metric.get("name"), "layout_metric_name_missing"
                )
                kind = MetricKind(metric.get("kind"))
                words = metric.get("words")
                if not isinstance(words, list) or any(
                    not isinstance(word, str) for word in words
                ):
                    raise ValueError("metric_words_malformed")
                metrics.append(MetricSpec(metric_name, kind, tuple(words)))
            banks.append(BankSpec(name, facet, tuple(metrics)))
        compiled = compile_layout(LayoutSpec(version, carrier_id, tuple(banks)))
    except (TypeError, ValueError) as error:
        raise ProductProfileError(f"layout_invalid:{error}") from error
    if compiled is None:
        raise ProductProfileError("layout_invalid")
    expected_fingerprint = description.get("fingerprint")
    if expected_fingerprint != compiled.fingerprint:
        raise ProductProfileError("layout_fingerprint_mismatch")
    if (
        composition_carrier := manifest.get("carrier_identity")
    ) and composition_carrier != compiled.carrier_id:
        raise ProductProfileError("carrier_identity_mismatch")
    composition = manifest.get("object_composition")
    if isinstance(composition, dict):
        if composition.get("carrier_identity") != compiled.carrier_id:
            raise ProductProfileError("composition_carrier_identity_mismatch")
        if composition.get("layout_fingerprint") != compiled.fingerprint:
            raise ProductProfileError("composition_layout_fingerprint_mismatch")
    return compiled


def _layout(
    compiled: CompiledLayout,
    object_name: str,
    record: dict[str, Any],
    cache: dict[tuple[str, str, tuple[BankLayout, ...]], CountLayout],
) -> CountLayout:
    count_layout_id = _required_text(
        record.get("count_layout_id"), "count_layout_id_missing"
    )
    reference_id = _required_text(
        record.get("reference_set_identity"), "reference_set_identity_missing"
    )
    banks_layout = tuple(
        BankLayout(bank.name, count_bank.row_count)
        for bank, count_bank in zip(
            compiled.banks, compiled.count_layout.banks, strict=True
        )
    )
    if count_layout_id != f"{compiled.version}:{compiled.fingerprint}:{reference_id}":
        raise _object_error("count_layout_identity_mismatch", object_name)
    key = count_layout_id, compiled.carrier_id, banks_layout
    if key not in cache:
        cache[key] = CountLayout(count_layout_id, compiled.carrier_id, banks_layout)
    return cache[key]


def _bundle(
    record: dict[str, Any],
    layout: CountLayout,
    object_name: str,
    zero_rows: dict[int, tuple[int, ...]],
) -> CountBundle:
    index = {bank.name: i for i, bank in enumerate(layout.banks)}
    observed: dict[int, list[int]] = {}
    sparse = record.get("sparse_counts")
    if not isinstance(sparse, list):
        raise _object_error("sparse_counts_missing_or_malformed", object_name)
    for entry in sparse:
        if (
            not isinstance(entry, list)
            or len(entry) != 3
            or not isinstance(entry[0], str)
            or type(entry[1]) is not int
            or type(entry[2]) is not int
        ):
            raise _object_error("sparse_count_entry_malformed", object_name)
        bank, row, count = entry
        if bank not in index:
            raise _object_error(f"sparse_count_unknown_bank:{bank}", object_name)
        bank_index = index[bank]
        bank_layout = layout.banks[bank_index]
        rows = observed.get(bank_index)
        if rows is None:
            rows = [0] * bank_layout.row_count
            observed[bank_index] = rows
        if not 0 <= row < len(rows) or count <= 0:
            raise _object_error(f"sparse_count_out_of_range:{bank}:{row}", object_name)
        rows[row] += count
    counts: list[tuple[int, ...]] = []
    for bank_index, bank_layout in enumerate(layout.banks):
        rows = observed.get(bank_index)
        if rows is not None:
            counts.append(tuple(rows))
            continue
        zero_row = zero_rows.get(bank_layout.row_count)
        if zero_row is None:
            zero_row = (0,) * bank_layout.row_count
            zero_rows[bank_layout.row_count] = zero_row
        counts.append(zero_row)
    return CountBundle(layout, tuple(counts))


def _pair_context(values: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted((key, str(value)) for key, value in values.items() if value is not None)
    )


def _aggregate_batch_status(statuses: list[str], fallback: str) -> str:
    """Return one bank status while keeping mixed states explicit."""
    if not statuses:
        return fallback
    conflict_states = {
        status
        for status in statuses
        if status in ("conflicting", "mismatch", "malformed", "facet_mapping_conflict")
    }
    if conflict_states:
        return min(conflict_states)
    distinct = sorted(set(statuses))
    if len(distinct) == 1:
        return distinct[0]
    return "batch_statuses:" + json.dumps(
        distinct, ensure_ascii=False, separators=(",", ":")
    )


def _profiles(manifest: dict[str, Any], mode: str) -> tuple[Profile, ...]:
    composition = manifest.get("object_composition")
    if (
        not isinstance(composition, dict)
        or composition.get("schema") != "knee_object_profiles/v1"
    ):
        raise ProductProfileError("object_composition_schema_unsupported")
    objects = composition.get("objects")
    if not isinstance(objects, dict):
        raise ProductProfileError("object_composition_objects_missing_or_malformed")
    compiled = _compiled_layout(composition)
    layout_cache: dict[tuple[str, str, tuple[BankLayout, ...]], CountLayout] = {}
    zero_rows: dict[int, tuple[int, ...]] = {}
    source_id = (
        manifest.get("study_uid")
        or manifest.get("studyUID")
        or manifest.get("source_id")
    )
    source_id = _required_text(source_id, "study_source_id_missing")
    source_mode = manifest.get("mode") or manifest.get("encoding_mode")
    if source_mode is not None and source_mode != mode:
        raise ProductProfileError(f"product_mode_mismatch:{source_mode}:{mode}")
    profiles: list[Profile] = []
    for object_name, record in objects.items():
        if (
            not isinstance(object_name, str)
            or not object_name
            or not isinstance(record, dict)
        ):
            raise ProductProfileError("object_record_malformed")
        layout = _layout(compiled, object_name, record, layout_cache)
        bundle = _bundle(record, layout, object_name, zero_rows)
        status = record.get("status")
        preparation = record.get("preparation_status")
        if (
            not isinstance(status, str)
            or not status
            or not isinstance(preparation, str)
            or not preparation
        ):
            raise _object_error("object_status_missing", object_name)
        assembly = record.get("assembly")
        if assembly is not None and not isinstance(assembly, dict):
            raise _object_error("assembly_malformed", object_name)
        batch_statuses: dict[str, list[str]] = {}
        batch_ledger: list[dict[str, Any]] = []
        if isinstance(assembly, dict):
            batches = assembly.get("batches")
            if not isinstance(batches, list):
                raise _object_error("assembly_batches_malformed", object_name)
            for batch_index, batch in enumerate(batches):
                if not isinstance(batch, dict):
                    raise _object_error("assembly_batch_malformed", object_name)
                batch_ledger.append({"batch_index": batch_index, "batch": batch})
                bank = batch.get("bank")
                batch_status = batch.get("status")
                if (
                    isinstance(bank, str)
                    and bank
                    and isinstance(batch_status, str)
                    and batch_status
                ):
                    batch_statuses.setdefault(bank, []).append(batch_status)
        bank_status = {
            bank.name: _aggregate_batch_status(
                batch_statuses.get(bank.name, []), status
            )
            for bank in layout.banks
        }
        for bank, aggregate in batch_statuses.items():
            if bank not in bank_status:
                bank_status[bank] = _aggregate_batch_status(aggregate, status)
        provenance = {
            "product_schema": str(composition["schema"]),
            "carrier_identity": str(composition.get("carrier_identity", "")),
            "layout_fingerprint": str(composition.get("layout_fingerprint", "")),
            "registry_fingerprint": str(composition.get("registry_fingerprint", "")),
            "reference_set_identity": str(record.get("reference_set_identity", "")),
            "count_layout_id": layout.layout_id,
            "preparation_status": preparation,
            "object_status": status,
            "assembly_status": "absent"
            if assembly is None
            else str(assembly.get("code", "unknown")),
            "product_storage": str(manifest.get("product_storage", "retained_product")),
            "study_uid": source_id,
            "adapter_mode": mode,
            "assembly_batch_ledger": json.dumps(
                batch_ledger,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        }
        if (
            isinstance(manifest.get("spec"), dict)
            and manifest["spec"].get("version") is not None
        ):
            provenance["source_spec_version"] = str(manifest["spec"]["version"])
        if manifest.get("spec_sha256") is not None:
            provenance["source_spec_sha256"] = str(manifest["spec_sha256"])
        if record.get("detail") is not None:
            provenance["detail"] = str(record["detail"])
        if source_mode is not None:
            provenance["source_mode"] = str(source_mode)
        scope = f"object:{object_name};composition:{composition.get('layout_fingerprint', '')}"
        profiles.append(
            Profile(
                subject=object_name,
                bundle=bundle,
                mode=mode,
                scope=scope,
                source_id=source_id,
                context=_pair_context(
                    {
                        "object_status": status,
                        "assembly_status": provenance["assembly_status"],
                    }
                ),
                bank_statuses=tuple(sorted(bank_status.items())),
                provenance=_pair_context(provenance),
            )
        )
    return tuple(profiles)


def profiles_from_manifest(
    manifest: dict[str, Any], mode: str = "full"
) -> tuple[Profile, ...]:
    """Read canonical per-object profiles from a product manifest.

    A retained in-memory manifest is sufficient: exact object sparse counts,
    their layout, carrier and reference identities are all represented there.
    The product-file reader delegates here after opening and validating its
    storage container.
    """
    if mode not in {"full", "cheap"}:
        raise ProductProfileError("mode_unsupported")
    if not isinstance(manifest, dict):
        raise ProductProfileError("manifest_not_an_object")
    return _profiles(manifest, mode)


def profiles_from_product(path: Path, mode: str = "full") -> tuple[Profile, ...]:
    """Read one retained product and return its canonical per-object profiles."""
    if mode not in {"full", "cheap"}:
        raise ProductProfileError("mode_unsupported")
    with open_product(path) as product:
        return profiles_from_manifest(product.manifest, mode)
