"""Input-available region descriptions through the installed exact encoders.

The caller owns region selection, producer eligibility and numeric references.
Neither a failed object rule nor its code removes the region's observations.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, replace
from typing import Any

import numpy as np

from knee.diagnosis.models import Profile
from knee.encoding.coarse_adapter import CoarseBlockLayout, encode_coarse_observation
from knee.encoding.handoff import encode_observation
from knee.encoding.places import CompiledLayout, EncodingResult, NumericReference


@dataclass(frozen=True, slots=True)
class CheapDescription:
    status: str
    profile: Profile | None
    encoding: EncodingResult | None
    coordinates: np.ndarray | None
    address_kind: str
    metadata: dict


def _summarize_sparse_row(
    counts: tuple[int, ...], row_count: int
) -> tuple[bool, tuple[tuple[int, str], ...], bool]:
    if len(counts) != row_count:
        raise ValueError("pair_count_row_cardinality_mismatch")
    speaking = False
    reusable = type(counts) is tuple
    nonzero: list[tuple[int, str]] = []
    for row_index, value in enumerate(counts):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError("pair_count_value_invalid")
        reusable = reusable and type(value) is int
        if value:
            speaking = True
            nonzero.append((row_index, str(value)))
    return speaking, tuple(nonzero), reusable


def source_disposition(provenance: str, kind: str, scope: str, mode: str) -> str:
    """Name source eligibility without interpreting an object's success code."""
    if provenance != "native":
        return "native_reading_required"
    if kind != "reading":
        return "region_reading_required"
    if not scope.startswith("region:") or not scope[7:].strip():
        return "explicit_region_scope_required"
    if not mode.startswith("cheap/") or not mode[6:].strip():
        return "explicit_cheap_mode_required"
    return "eligible"


def _detached(array: np.ndarray) -> np.ndarray:
    detached = array.copy()
    detached.flags.writeable = False
    return detached


def _detach_encoding(encoded: EncodingResult) -> EncodingResult:
    return replace(
        encoded,
        metrics=tuple(
            replace(
                metric,
                row_codes=_detached(metric.row_codes),
                source_values=_detached(metric.source_values),
                source_available=_detached(metric.source_available),
            )
            for metric in encoded.metrics
        ),
    )


def build_cheap_profile(
    *,
    subject: str,
    source_id: str,
    scope: str,
    mode: str,
    producer: str,
    dependencies: tuple[str, ...],
    record: Mapping[str, Any],
    observation: Mapping[str, Any],
    arrays: Mapping[str, np.ndarray],
    spec: CompiledLayout,
    bindings: Sequence[Mapping[str, Any]],
    references: Mapping[tuple[str, str], NumericReference],
    geometry: Mapping[str, Any] | CoarseBlockLayout,
    context: tuple[tuple[str, str], ...] = (),
) -> CheapDescription:
    """Encode one caller-located native or coarse region, without recognition.

    ``geometry`` is the acquired plane's explicit LPS frame or the installed
    coarse layout naming retained grid/window/block arrays. ``observation``
    names a region support, not an accepted object mask. All array digests,
    source addresses and availability use the existing adapter contracts.

    Each compiled metric needs a binding, including explicit ``unread`` where
    unavailable. No reference is synthesized. Source values, nonfinite values,
    metric statuses and row codes survive independently of the caller's arrays.
    ``producer`` and ordered ``dependencies`` declare the actual procedure;
    root must verify it was available at this stage, before using the profile.
    """
    address_kind = (
        "coarse_grid_rc" if isinstance(geometry, CoarseBlockLayout) else "native_rc"
    )
    metadata = {
        "api": "knee.diagnosis.cheap.build_cheap_profile/v1",
        "subject": subject,
        "source_id": source_id,
        "scope": scope,
        "mode": mode,
        "producer": producer,
        "dependencies": dependencies,
        "observation": deepcopy(dict(observation))
        if isinstance(observation, Mapping)
        else None,
    }

    def refused(code: str, detail: str = "") -> CheapDescription:
        return CheapDescription(
            code, None, None, None, address_kind, {**metadata, "detail": detail}
        )

    if any(
        not isinstance(value, str) or not value.strip()
        for value in (subject, source_id, scope, mode, producer)
    ):
        return refused("invalid_identity")
    if (
        not isinstance(dependencies, tuple)
        or any(not isinstance(item, str) or not item.strip() for item in dependencies)
        or len(set(dependencies)) != len(dependencies)
    ):
        return refused("invalid_dependencies")
    if (
        not isinstance(context, tuple)
        or any(
            not isinstance(item, tuple)
            or len(item) != 2
            or any(not isinstance(value, str) or not value for value in item)
            for item in context
        )
        or len({item[0] for item in context}) != len(context)
    ):
        return refused("invalid_context")
    if not isinstance(record, Mapping) or not isinstance(observation, Mapping):
        return refused("invalid_source")
    if any(
        not isinstance(observation.get(field), str) for field in ("provenance", "kind")
    ) or any(
        not isinstance(source.get(field), str) or not source[field].strip()
        for source in (record, observation)
        for field in ("artifact", "series_uid")
    ):
        return refused("invalid_source_identity")
    disposition = source_disposition(
        observation.get("provenance", ""), observation.get("kind", ""), scope, mode
    )
    if disposition != "eligible":
        return refused(disposition)
    if (
        not isinstance(spec, CompiledLayout)
        or not isinstance(arrays, Mapping)
        or not isinstance(references, Mapping)
        or not isinstance(bindings, Sequence)
        or isinstance(bindings, (str, bytes))
        or any(not isinstance(binding, Mapping) for binding in bindings)
    ):
        return refused("invalid_encoding_inputs")
    if not isinstance(geometry, (Mapping, CoarseBlockLayout)):
        return refused("explicit_geometry_required")

    source_record = dict(record)
    source_observation = dict(observation)
    source_bindings = [dict(binding) for binding in bindings]
    try:
        # Profile provenance uses the JSON exchange format. Reject a malformed
        # address before encoding, rather than failing while publishing it.
        json.dumps(source_observation, sort_keys=True, allow_nan=False)
        json.dumps(source_bindings, sort_keys=True, allow_nan=False)
        if isinstance(geometry, CoarseBlockLayout):
            addressed = encode_coarse_observation(
                source_record,
                source_observation,
                arrays,
                spec,
                source_bindings,
                references,
                geometry,
            )
            coordinates = addressed.coordinates
        else:
            json.dumps(dict(geometry), sort_keys=True, allow_nan=False)
            if "address_frame" in source_observation and (
                source_observation["address_frame"] != dict(geometry)
            ):
                return refused("contradictory_geometry")
            source_observation["address_frame"] = deepcopy(dict(geometry))
            addressed = encode_observation(
                source_record,
                source_observation,
                arrays,
                spec,
                source_bindings,
                references,
            )
            coordinates = addressed.points_rc
    except (TypeError, ValueError, KeyError, IndexError, AttributeError) as error:
        return refused("invalid_source", str(error))

    metadata.update(deepcopy(addressed.metadata))
    encoded = addressed.encoding
    if encoded is None:
        return CheapDescription(
            addressed.status, None, None, None, address_kind, metadata
        )
    encoded = _detach_encoding(encoded)
    detached_coordinates = None if coordinates is None else _detached(coordinates)
    if encoded.bundle is None:
        return CheapDescription(
            addressed.status,
            None,
            encoded,
            detached_coordinates,
            address_kind,
            metadata,
        )
    # Preserve every metric status; a bank with any missing reference must not
    # be reported as wholly read just because another metric wrote a row.
    statuses = tuple(
        (
            bank.name,
            ";".join(
                f"{metric.metric}={metric.status.value}"
                for metric in encoded.metrics
                if metric.bank == bank.name
            ),
        )
        for bank in spec.banks
    )
    provenance = (
        ("api", metadata["api"]),
        ("producer", producer),
        ("dependencies", json.dumps(dependencies)),
        ("address_kind", address_kind),
        ("observation", json.dumps(source_observation, sort_keys=True)),
        ("bindings", json.dumps(source_bindings, sort_keys=True)),
        (
            "geometry",
            json.dumps(
                metadata.get("scope_address", source_observation.get("address_frame")),
                sort_keys=True,
            ),
        ),
        ("source_refs", json.dumps(metadata.get("source_refs", {}), sort_keys=True)),
    )
    profile = Profile(
        subject, encoded.bundle, mode, scope, source_id, context, statuses, provenance
    )
    return CheapDescription(
        addressed.status, profile, encoded, detached_coordinates, address_kind, metadata
    )


def pair_descriptions(
    full: Profile, cheap: Profile, *, counts_mode: str = "dense"
) -> dict:
    """Record source/bank calibration without cross-mode resemblance claims.

    Common speaking bank *names* do not establish common measurement semantics.
    Counts from each side are inspectable; no similarity or diagnostic call is
    calculated, even where the names or stored row counts happen to agree.
    """
    if not isinstance(full, Profile) or not isinstance(cheap, Profile):
        raise TypeError("profiles_required")
    if full.subject != cheap.subject:
        raise ValueError("pair_subject_mismatch")
    if counts_mode not in ("dense", "sparse"):
        raise ValueError("pair_counts_mode_invalid")

    sparse_cache: dict[
        int, tuple[tuple[int, ...], bool, tuple[tuple[int, str], ...]]
    ] = {}

    def summarize(profile: Profile) -> dict[str, dict]:
        summary: dict[str, dict] = {}
        for bank, counts in zip(
            profile.bundle.layout.banks, profile.bundle.counts, strict=True
        ):
            if counts_mode == "dense":
                if len(counts) != bank.row_count:
                    raise ValueError("pair_count_row_cardinality_mismatch")
                speaking = any(counts)
                count_record = list(counts)
            else:
                cached = sparse_cache.get(id(counts))
                if cached is None or cached[0] is not counts:
                    speaking, sparse_rows, reusable = _summarize_sparse_row(
                        counts, bank.row_count
                    )
                    if reusable:
                        sparse_cache[id(counts)] = (counts, speaking, sparse_rows)
                else:
                    if len(counts) != bank.row_count:
                        raise ValueError("pair_count_row_cardinality_mismatch")
                    _, speaking, sparse_rows = cached
                count_record = {
                    "row_count": bank.row_count,
                    "nonzero_rows": [[row, value] for row, value in sparse_rows],
                }
            summary[bank.name] = {
                "speaking": speaking,
                "counts": count_record,
            }
        return summary

    full_summary = summarize(full)
    cheap_summary = summarize(cheap)
    full_speaking = {name for name, item in full_summary.items() if item["speaking"]}
    cheap_speaking = {name for name, item in cheap_summary.items() if item["speaking"]}
    names = sorted(full_summary.keys() | cheap_summary.keys())
    full_names = set(full_summary)
    cheap_names = set(cheap_summary)

    def identity(profile: Profile) -> dict:
        result = {
            "subject": profile.subject,
            "source_id": profile.source_id,
            "mode": profile.mode,
            "scope": profile.scope,
            "layout_id": profile.bundle.layout.layout_id,
            "carrier_id": profile.bundle.layout.carrier_id,
            "context": list(profile.context),
            "bank_statuses": list(profile.bank_statuses),
            "provenance": list(profile.provenance),
        }
        if counts_mode == "sparse":
            result["layout_banks"] = [
                {"name": bank.name, "row_count": bank.row_count}
                for bank in profile.bundle.layout.banks
            ]
        return result

    result = {
        "api": "knee.diagnosis.cheap.pair_descriptions/v1",
        "full": identity(full),
        "cheap": identity(cheap),
        "comparison_performed": False,
        "meaning": "source pairing only; no cross-mode similarity or semantic equivalence",
        "common_speaking_banks": sorted(full_speaking & cheap_speaking),
        "differing_availability_banks": sorted(full_speaking ^ cheap_speaking),
        "full_silent_banks": sorted(set(names) - full_speaking),
        "cheap_silent_banks": sorted(set(names) - cheap_speaking),
        "banks": [
            {
                "bank": name,
                "full_counts": full_summary[name]["counts"]
                if name in full_summary
                else None,
                "cheap_counts": cheap_summary[name]["counts"]
                if name in cheap_summary
                else None,
            }
            for name in names
        ],
    }
    if counts_mode == "sparse":
        result["counts_mode"] = "sparse_exact_integer_rows"
        result["bank_name_sets"] = {
            "common": sorted(full_names & cheap_names),
            "full_only": sorted(full_names - cheap_names),
            "cheap_only": sorted(cheap_names - full_names),
            "common_speaking": sorted(full_speaking & cheap_speaking),
            "differing_availability": sorted(full_speaking ^ cheap_speaking),
        }
    return result
