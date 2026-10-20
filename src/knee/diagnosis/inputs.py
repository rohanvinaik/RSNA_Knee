"""One-study-at-a-time DICOM inputs for the diagnostic cheap-profile path."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

from knee.diagnosis.cheap import CheapDescription, build_cheap_profile
from knee.diagnosis.models import Profile
from knee.encoding.counts import CountCode, CountLayout, add_counts
from knee.encoding.operation import _references, validate_spec
from knee.receipt import digest
from knee.study.geometry import orientation_of, position_of, spacing_of
from knee.study.slices import Slice, read_slice

_SCHEMA = "knee.diagnostic-inputs/v1"
_MEASUREMENT_IDENTITY_VERSION = "knee.diagnostic-input-measurement/v1"


class DiagnosticInputError(ValueError):
    """A named error in the explicit diagnostic-input recipe or its sources."""


def _recipe_path(args: object) -> Path | None:
    if isinstance(args, (str, Path)):
        return Path(args)
    if isinstance(args, Mapping):
        value = args.get("diagnostic_inputs", args.get("recipe"))
    else:
        value = getattr(args, "diagnostic_inputs", getattr(args, "recipe", None))
    return Path(value) if isinstance(value, (str, Path)) else None


def _load_recipe(args: object) -> tuple[dict[str, Any], Path]:
    path = _recipe_path(args)
    if path is not None:
        try:
            raw = path.read_text(encoding="utf-8")
            value = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise DiagnosticInputError(f"invalid_recipe_file:{path}") from error
        if not isinstance(value, dict):
            raise DiagnosticInputError("recipe_must_be_object")
        return value, path.resolve().parent
    if isinstance(args, Mapping):
        value = args.get("recipe_data", args)
    else:
        value = getattr(args, "recipe_data", None)
    if not isinstance(value, Mapping):
        raise DiagnosticInputError("recipe_path_or_mapping_required")
    return dict(value), Path.cwd()


def _load_spec(value: object, base: Path) -> dict[str, Any]:
    if isinstance(value, (str, Path)):
        path = Path(value)
        if not path.is_absolute():
            path = base / path
        try:
            spec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise DiagnosticInputError(f"invalid_encoding_spec_file:{path}") from error
    else:
        spec = value
    if not isinstance(spec, dict):
        raise DiagnosticInputError("encoding_spec_must_be_object_or_path")
    return spec


def _identity(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DiagnosticInputError(f"{field}_required")
    return value


def _region_scopes(value: object) -> dict[str, tuple[str, ...]]:
    """Validate complete caller-declared regions by canonical object name."""
    if not isinstance(value, Mapping) or not value:
        raise DiagnosticInputError("region_scopes_must_be_object")
    normalized: dict[str, tuple[str, ...]] = {}
    for raw_object, raw_regions in value.items():
        object_name = _identity(raw_object, "region_scopes_object")
        if object_name != object_name.strip():
            raise DiagnosticInputError("region_scopes_object_must_be_canonical")
        if (
            not isinstance(raw_regions, list)
            or not raw_regions
            or any(
                not isinstance(region, str)
                or not region.strip()
                or region != region.strip()
                for region in raw_regions
            )
        ):
            raise DiagnosticInputError(
                f"region_scopes_nonempty_canonical_names_required:{object_name}"
            )
        if len(set(raw_regions)) != len(raw_regions):
            raise DiagnosticInputError(f"region_scopes_duplicate_name:{object_name}")
        normalized[object_name] = tuple(sorted(raw_regions))
    return normalized


def _geometry(frame_slice: Slice) -> tuple[dict[str, Any], dict[str, Any]]:
    orientation_status, orientation = orientation_of(frame_slice.header)
    position_status, position = position_of(frame_slice.header)
    spacing_status, spacing = spacing_of(frame_slice.header)
    status = {
        "orientation": orientation_status,
        "position": position_status,
        "spacing": spacing_status,
    }
    if orientation is None or position is None or spacing is None:
        raise DiagnosticInputError(
            "dicom_geometry_unavailable:" + json.dumps(status, sort_keys=True)
        )
    # The retained frame contract is three patient-axis rows by two pixel axes:
    # native rows advance along the DICOM column direction; columns along its row.
    row_dir, col_dir = orientation[:3], orientation[3:]
    frame = {
        "origin_lps": [float(value) for value in position],
        "basis_lps": [
            [float(col_dir[axis] * spacing[0]), float(row_dir[axis] * spacing[1])]
            for axis in range(3)
        ],
    }
    return frame, status


def _spec_profile(
    prepared: dict[str, Any], object_name: str, view: tuple[str, str, str]
) -> dict[str, Any]:
    matches = [
        dict(profile)
        for profile in prepared["profiles"]
        if profile.get("object") == object_name
        and profile.get("provenance") == "native"
        and profile.get("kind") == "reading"
        and profile.get("view") in (None, list(view), view)
    ]
    if len(matches) != 1:
        raise DiagnosticInputError(
            f"spec_profile_match_count:{object_name}:{list(view)}:{len(matches)}"
        )
    return matches[0]


def _support(coords: object, shape: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    if not isinstance(coords, list) or not coords:
        raise DiagnosticInputError("support_rc_nonempty_list_required")
    points: list[tuple[int, int]] = []
    for point in coords:
        if (
            not isinstance(point, list)
            or len(point) != 2
            or any(
                not isinstance(value, int) or isinstance(value, bool) for value in point
            )
        ):
            raise DiagnosticInputError("support_rc_point_must_be_integer_pair")
        row, column = point
        if not (0 <= row < shape[0] and 0 <= column < shape[1]):
            raise DiagnosticInputError("support_rc_out_of_frame")
        points.append((row, column))
    if len(set(points)) != len(points):
        raise DiagnosticInputError("support_rc_duplicate_coordinate")
    coordinates = np.asarray(points, dtype=np.int32)
    mask = np.zeros(shape, dtype=np.bool_)
    mask[coordinates[:, 0], coordinates[:, 1]] = True
    coordinates.flags.writeable = False
    mask.flags.writeable = False
    return coordinates, mask


def _view(value: object) -> tuple[str, str, str]:
    if (
        not isinstance(value, list)
        or len(value) != 3
        or any(not isinstance(part, str) or not part for part in value)
    ):
        raise DiagnosticInputError("frame_view_three_explicit_strings_required")
    return tuple(value)


def _measurement_contract_id(
    *,
    producer: str,
    mode: str,
    dependencies: tuple[str, ...],
    observations: Sequence[object],
    view_distinguished_banks: Mapping[str, Any],
    declared_profiles: Sequence[Mapping[str, Any]],
    declared_region_scopes: Sequence[str] | None = None,
) -> str:
    """Name the declared measurement semantics without study data or readings."""
    bindings: set[tuple[str, str, tuple[str, ...], str, str, str]] = set()
    if view_distinguished_banks:
        observed_objects = {
            item.get("object")
            for item in observations
            if isinstance(item, Mapping) and isinstance(item.get("object"), str)
        }
        for bank, declared_views in view_distinguished_banks.items():
            if not isinstance(bank, str) or not isinstance(declared_views, list):
                continue
            for declared_view in declared_views:
                if (
                    not isinstance(declared_view, list)
                    or len(declared_view) != 3
                    or any(not isinstance(part, str) for part in declared_view)
                ):
                    continue
                view = tuple(declared_view)
                for profile in declared_profiles:
                    if (
                        profile.get("provenance") != "native"
                        or profile.get("kind") != "reading"
                        or profile.get("object") not in observed_objects
                        or profile.get("view") not in (None, list(view), view)
                    ):
                        continue
                    object_name = profile.get("object")
                    readings = profile.get("readings")
                    if not isinstance(object_name, str) or not isinstance(
                        readings, list
                    ):
                        continue
                    for reading in readings:
                        if (
                            not isinstance(reading, Mapping)
                            or reading.get("bank") != bank
                        ):
                            continue
                        metric = reading.get("metric")
                        value = reading.get("value")
                        available = reading.get("available")
                        if all(
                            isinstance(item, str) for item in (metric, value, available)
                        ):
                            bindings.add(
                                (
                                    object_name,
                                    bank,
                                    view,
                                    f"{metric}:acquired_signal",
                                    value,
                                    available,
                                )
                            )
    else:
        for observation in observations:
            if not isinstance(observation, Mapping):
                continue
            object_name = observation.get("object")
            frame = observation.get("frame")
            view_value = frame.get("view") if isinstance(frame, Mapping) else None
            view = tuple(view_value) if isinstance(view_value, list) else ()
            raw_bindings = observation.get("binding")
            if not isinstance(raw_bindings, list):
                continue
            for binding in raw_bindings:
                if not isinstance(binding, Mapping):
                    continue
                bank = binding.get("bank")
                metric = binding.get("metric")
                source = binding.get("source")
                if all(
                    isinstance(item, str)
                    for item in (object_name, bank, metric, source)
                ):
                    bindings.add(
                        (object_name, bank, view, f"{metric}:{source}", "", "")
                    )
    normalized_bindings = [
        {
            "object": object_name,
            "bank": bank,
            "view": list(view),
            "metric_source": metric_source,
            "value": value,
            "available": available,
        }
        for object_name, bank, view, metric_source, value, available in sorted(
            bindings,
            key=lambda row: json.dumps(
                [row[0], row[1], list(row[2]), row[3], row[4], row[5]],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                default=repr,
            ),
        )
    ]
    canonical = {
        "identity_version": _MEASUREMENT_IDENTITY_VERSION,
        "producer": producer,
        "mode": mode,
        "dependencies": list(dependencies),
        "bank_view_source_bindings": normalized_bindings,
        "view_distinguished_banks": dict(view_distinguished_banks),
        "declared_region_scopes": (
            None if declared_region_scopes is None else list(declared_region_scopes)
        ),
    }
    try:
        serialized = json.dumps(
            canonical,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise DiagnosticInputError("measurement_identity_not_json") from error
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _bind_measurement_identity(
    description: CheapDescription, contract_id: str
) -> tuple[CheapDescription, str | None]:
    """Return the cheap profile under its acquisition-semantic layout identity."""
    profile = description.profile
    if profile is None:
        return description, None
    source_layout = profile.bundle.layout
    source_layout_id = source_layout.layout_id
    semantic_layout = CountLayout(
        layout_id=(f"{source_layout_id}:{_MEASUREMENT_IDENTITY_VERSION}:{contract_id}"),
        carrier_id=source_layout.carrier_id,
        banks=source_layout.banks,
    )
    semantic_bundle = replace(profile.bundle, layout=semantic_layout)
    semantic_profile = replace(
        profile,
        bundle=semantic_bundle,
        provenance=(
            *profile.provenance,
            ("measurement_contract_id", contract_id),
            ("source_count_layout_id", source_layout_id),
        ),
    )
    return replace(description, profile=semantic_profile), source_layout_id


def _frame_spec(item: object, base: Path) -> tuple[dict[str, Any], Path]:
    if not isinstance(item, Mapping):
        raise DiagnosticInputError("frame_declaration_required")
    raw_path = _identity(item.get("path"), "frame_path")
    path = Path(raw_path)
    if not path.is_absolute():
        path = base / path
    frame = {
        "path": str(path.resolve()),
        "series_uid": _identity(item.get("series_uid"), "series_uid"),
        "slice_index": item.get("slice_index"),
        "view": _view(item.get("view")),
    }
    index = frame["slice_index"]
    if not isinstance(index, int) or isinstance(index, bool) or index < 0:
        raise DiagnosticInputError("slice_index_nonnegative_integer_required")
    return frame, path.resolve()


def _bindings(
    item: object, profile: Mapping[str, Any], layout: object
) -> list[dict[str, Any]]:
    if not isinstance(item, list):
        raise DiagnosticInputError("observation_bindings_list_required")
    expected = {
        (binding["bank"], binding["metric"]) for binding in profile.get("readings", [])
    }
    seen: set[tuple[str, str]] = set()
    result: list[dict[str, Any]] = []
    for binding in item:
        if not isinstance(binding, Mapping):
            raise DiagnosticInputError("invalid_observation_binding")
        key = (binding.get("bank"), binding.get("metric"))
        if key not in expected:
            raise DiagnosticInputError("binding_not_in_spec_profile")
        if key in seen:
            raise DiagnosticInputError("duplicate_observation_binding")
        seen.add(key)
        source = binding.get("source")
        if source == "unavailable":
            reason = binding.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                raise DiagnosticInputError("unavailable_binding_reason_required")
            result.append(
                {
                    "bank": key[0],
                    "metric": key[1],
                    "source": "unavailable",
                    "reason": reason,
                }
            )
            continue
        if source != "acquired_signal":
            raise DiagnosticInputError("unsupported_binding_source")
        metric_spec = next(
            (
                metric
                for bank_spec in layout.banks
                if bank_spec.name == key[0]
                for metric in bank_spec.metrics
                if metric.name == key[1]
            ),
            None,
        )
        if metric_spec is None or metric_spec.kind.value != "digit":
            raise DiagnosticInputError("acquired_signal_requires_digit_metric")
        result.append(
            {
                "bank": key[0],
                "metric": key[1],
                "source": "acquired_signal",
            }
        )
    if seen != expected:
        raise DiagnosticInputError("observation_bindings_incomplete")
    # Restrict this input lane to the supplied raw pixel plane; a caller's
    # encoding spec controls whether those exact values have a reference.
    for bank_spec in layout.banks:
        for metric in bank_spec.metrics:
            key = (bank_spec.name, metric.name)
            if key in expected and key not in seen:
                raise DiagnosticInputError("observation_bindings_incomplete")
    return result


def _observation_profile(
    *,
    study_uid: str,
    observation: Mapping[str, Any],
    index: int,
    frame_spec: dict[str, Any],
    pixels: np.ndarray,
    frame_geometry: dict[str, Any],
    geometry_status: dict[str, Any],
    profile_spec: dict[str, Any],
    prepared: dict[str, Any],
    root: Path,
    mode: str,
    producer: str,
    dependencies: tuple[str, ...],
    context: tuple[tuple[str, str], ...],
) -> tuple[CheapDescription, dict[str, Any]]:
    object_name = _identity(observation.get("object"), "object")
    region = _identity(observation.get("region"), "region")
    scope = f"region:{region}"
    coordinates, mask = _support(observation.get("support_rc"), pixels.shape)
    finite = np.isfinite(pixels)
    finite.flags.writeable = False
    arrays = {
        "support_mask": mask,
        "frame_pixels": pixels,
        "frame_finite": finite,
    }
    record = {
        "artifact": frame_spec["path"],
        "series_uid": frame_spec["series_uid"],
        "view": list(frame_spec["view"]),
        "slice_index": frame_spec["slice_index"],
        "arrays": {
            name: {"digest": _array_digest(array)} for name, array in arrays.items()
        },
    }
    addressed_observation = {
        "object": object_name,
        "provenance": "native",
        "kind": "reading",
        "artifact": frame_spec["path"],
        "series_uid": frame_spec["series_uid"],
        "view": list(frame_spec["view"]),
        "slices": [frame_spec["slice_index"]],
        "support": "support_mask",
        "count": len(coordinates),
        "code": "caller_addressed_region",
        "note": "explicit coordinates only; no object boundary inferred",
        "address_frame": frame_geometry,
    }
    bindings = []
    for binding in observation["binding"]:
        if binding["source"] == "unavailable":
            bindings.append(
                {
                    "bank": binding["bank"],
                    "metric": binding["metric"],
                    "source": "unread",
                    "reason": binding["reason"],
                }
            )
            continue
        bindings.append(
            {
                "bank": binding["bank"],
                "metric": binding["metric"],
                "value": "frame_pixels",
                "available": "frame_finite",
            }
        )
    references = _references(profile_spec, prepared["layout"])
    description = build_cheap_profile(
        subject=object_name,
        source_id=json.dumps(
            {
                "study_uid": study_uid,
                "series_uid": frame_spec["series_uid"],
                "slice_index": frame_spec["slice_index"],
                "view": frame_spec["view"],
                "path": frame_spec["path"],
                "region": region,
                "support_sha256": _array_digest(coordinates),
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        scope=scope,
        mode=mode,
        producer=producer,
        dependencies=dependencies,
        record=record,
        observation=addressed_observation,
        arrays=arrays,
        spec=prepared["layout"],
        bindings=bindings,
        references=references,
        geometry=frame_geometry,
        context=context,
    )
    file_digest = _file_digest(Path(frame_spec["path"]))
    evidence = {
        "index": index,
        "study_uid": study_uid,
        "object": object_name,
        "region": region,
        "scope": scope,
        "bindings": tuple(dict(binding) for binding in observation["binding"]),
        "frame": {
            **frame_spec,
            "geometry": frame_geometry,
            "geometry_status": geometry_status,
        },
        "source_file_sha256": file_digest,
        "support_rc": coordinates,
        "description_status": description.status,
        "profile": description.profile,
        "encoding_status": (
            None if description.encoding is None else description.encoding.status.value
        ),
        "reference_set_fingerprint": (
            None
            if description.encoding is None
            else description.encoding.reference_set_fingerprint
        ),
        "unread_sources": tuple(description.metadata.get("unread_sources", ())),
        "array_digests": {
            name: item["digest"] for name, item in record["arrays"].items()
        },
        "recipe_root": str(root),
    }
    return description, evidence


def _array_digest(value: np.ndarray) -> str:
    return digest(value)


def _file_digest(path: Path) -> str:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as error:
        raise DiagnosticInputError(f"frame_file_unreadable:{path}") from error
    return digest.hexdigest()


def _compose_profiles(
    descriptions: Sequence[CheapDescription],
    evidence: Sequence[dict[str, Any]],
    view_distinguished_banks: Mapping[str, Any],
    declared_region_scopes: Mapping[str, Sequence[str]] | None = None,
) -> tuple[Profile, ...]:
    grouped: dict[str, list[tuple[Profile, dict[str, Any]]]] = {}
    for description, row in zip(descriptions, evidence, strict=True):
        if description.profile is None:
            raise DiagnosticInputError(f"profile_not_available:{description.status}")
        grouped.setdefault(description.profile.subject, []).append(
            (description.profile, row)
        )
    profiles: list[Profile] = []
    for subject in sorted(grouped):
        entries = sorted(
            grouped[subject],
            key=lambda item: (
                tuple(item[1]["frame"]["view"]),
                item[1]["scope"],
                item[1]["frame"]["series_uid"],
                item[1]["frame"]["slice_index"],
                item[1]["frame"]["path"],
                _array_digest(item[1]["support_rc"]),
            ),
        )
        first = entries[0][0]
        bundle = first.bundle
        scopes = sorted(profile.scope for profile, _ in entries)
        declared_scopes = (
            None
            if declared_region_scopes is None
            else declared_region_scopes.get(subject)
        )
        statuses: dict[str, list[str]] = {
            bank: [status] for bank, status in first.bank_statuses
        }
        seen_views: set[tuple[str, str, str]] = set()
        for profile, _row in entries[1:]:
            if profile.bundle.layout != bundle.layout:
                raise DiagnosticInputError(f"composition_layout_mismatch:{subject}")
        if len(entries) > 1 or view_distinguished_banks:
            for _, row in entries:
                view = tuple(row["frame"]["view"])
                if len(entries) > 1 and view in seen_views:
                    raise DiagnosticInputError(
                        f"composition_view_not_distinguished:{subject}:{view}"
                    )
                seen_views.add(view)
            for bank_layout in bundle.layout.banks:
                bank = bank_layout.name
                declared = view_distinguished_banks.get(bank)
                if (
                    not isinstance(declared, list)
                    or len(declared) != 1
                    or not isinstance(declared[0], list)
                    or len(declared[0]) != 3
                    or any(
                        not isinstance(part, str) or not part for part in declared[0]
                    )
                ):
                    raise DiagnosticInputError(
                        f"composition_bank_view_not_exclusive:{subject}:{bank}"
                    )
                eligible_view = tuple(declared[0])
                for _, row in entries:
                    actual_view = tuple(row["frame"]["view"])
                    # The count layout owns bank identity; the observation's
                    # complete explicit binding set owns per-metric source state.
                    relevant = [
                        binding
                        for binding in row["bindings"]
                        if binding["bank"] == bank
                    ]
                    if not relevant:
                        raise DiagnosticInputError(
                            f"composition_metric_binding_missing:{subject}:{bank}"
                        )
                    expected_source = (
                        "acquired_signal"
                        if actual_view == eligible_view
                        else "unavailable"
                    )
                    if any(
                        binding["source"] != expected_source for binding in relevant
                    ):
                        raise DiagnosticInputError(
                            f"composition_view_binding_mismatch:{subject}:{bank}:{actual_view}:{expected_source}"
                        )
        for profile, _row in entries[1:]:
            result = add_counts(bundle, profile.bundle)
            if result.code is not CountCode.OK or result.bundle is None:
                raise DiagnosticInputError(
                    f"composition_add_failed:{subject}:{result.code.value}"
                )
            bundle = result.bundle
            for bank, status in profile.bank_statuses:
                statuses.setdefault(bank, []).append(status)
        profile_provenance: list[tuple[str, str]] = [
            ("study_uid", entries[0][1]["study_uid"])
        ]
        if declared_scopes is not None:
            profile_provenance.append(
                (
                    "declared_region_scopes",
                    json.dumps(
                        [f"region:{region}" for region in declared_scopes],
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                )
            )
        for position, (profile, row) in enumerate(entries):
            provenance_map = dict(profile.provenance)
            if len(provenance_map) != len(profile.provenance):
                raise DiagnosticInputError(
                    f"duplicate_observation_provenance:{subject}"
                )
            for key, value in sorted(provenance_map.items()):
                profile_provenance.append((f"observation_{position:04d}.{key}", value))
            profile_provenance.append(
                (
                    f"observation_{position:04d}.frame_identity",
                    json.dumps(
                        {
                            "view": row["frame"]["view"],
                            "series_uid": row["frame"]["series_uid"],
                            "slice_index": row["frame"]["slice_index"],
                            "path": row["frame"]["path"],
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                )
            )
        profiles.append(
            Profile(
                first.subject,
                bundle,
                first.mode,
                "region:"
                + json.dumps(
                    scopes
                    if declared_scopes is None
                    else [f"region:{region}" for region in declared_scopes],
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                json.dumps(
                    [profile.source_id for profile, _ in entries], separators=(",", ":")
                ),
                first.context,
                tuple(
                    (bank, ";".join(values))
                    for bank, values in sorted(statuses.items())
                ),
                tuple(profile_provenance),
            )
        )
    return tuple(profiles)


def acquired_studies(
    args: object, *, cohort: object | None = None, partition_name: str | None = None
):
    """Yield selected explicit DICOM-backed cheap profiles one study at a time."""
    recipe, recipe_root = _load_recipe(args)
    if recipe.get("schema") != _SCHEMA:
        raise DiagnosticInputError("unsupported_recipe_schema")
    mode = _identity(recipe.get("mode"), "mode")
    if not mode.startswith("cheap/") or not mode[6:].strip():
        raise DiagnosticInputError("explicit_cheap_mode_required")
    producer = _identity(recipe.get("producer"), "producer")
    raw_dependencies = recipe.get("dependencies")
    if (
        not isinstance(raw_dependencies, list)
        or not raw_dependencies
        or any(
            not isinstance(value, str) or not value.strip()
            for value in raw_dependencies
        )
        or len(set(raw_dependencies)) != len(raw_dependencies)
    ):
        raise DiagnosticInputError("explicit_unique_dependencies_required")
    dependencies = tuple(raw_dependencies)
    raw_vdb = recipe.get("view_distinguished_banks", {})
    if not isinstance(raw_vdb, Mapping):
        raise DiagnosticInputError("view_distinguished_banks_must_be_object")
    has_region_scopes = "region_scopes" in recipe
    declared_region_scopes = (
        _region_scopes(recipe["region_scopes"]) if has_region_scopes else None
    )
    spec = _load_spec(recipe.get("encoding_spec"), recipe_root)
    prepared = validate_spec(spec)
    studies = recipe.get("studies")
    if not isinstance(studies, list):
        raise DiagnosticInputError("studies_list_required")

    if (cohort is None) != (partition_name is None):
        raise DiagnosticInputError("cohort_and_partition_must_be_paired")
    if cohort is not None:
        from knee.diagnosis.cohort import partition_uids

        available: list[str] = []
        by_uid: dict[str, list[Mapping[str, Any]]] = {}
        for study in studies:
            if not isinstance(study, Mapping):
                raise DiagnosticInputError("study_entry_must_be_object")
            uid = _identity(study.get("study_uid"), "study_uid")
            available.append(uid)
            by_uid.setdefault(uid, []).append(study)
        selected = partition_uids(cohort, partition_name, available)
        studies = [by_uid[uid][0] for uid in selected]

    for study in studies:
        if not isinstance(study, Mapping):
            raise DiagnosticInputError("study_entry_must_be_object")
        study_uid = _identity(study.get("study_uid"), "study_uid")
        raw_observations = study.get("observations")
        if not isinstance(raw_observations, list) or not raw_observations:
            raise DiagnosticInputError(f"study_observations_required:{study_uid}")
        observations_by_object: dict[str, list[object]] = {}
        for observation in raw_observations:
            if isinstance(observation, Mapping) and isinstance(
                observation.get("object"), str
            ):
                observations_by_object.setdefault(observation["object"], []).append(
                    observation
                )
        measurement_contract_ids: dict[str, str] = {}
        for object_name, object_observations in observations_by_object.items():
            object_regions = None
            if declared_region_scopes is not None:
                object_regions = declared_region_scopes.get(object_name)
                if object_regions is None:
                    raise DiagnosticInputError(
                        f"region_scopes_object_missing:{object_name}"
                    )
                for observation in object_observations:
                    region = observation.get("region")
                    if not isinstance(region, str) or region not in object_regions:
                        raise DiagnosticInputError(
                            f"region_not_declared_for_object:{object_name}:{region}"
                        )
            object_vdb = dict(raw_vdb) if raw_vdb else {}
            measurement_contract_ids[object_name] = _measurement_contract_id(
                producer=producer,
                mode=mode,
                dependencies=dependencies,
                observations=object_observations,
                view_distinguished_banks=object_vdb,
                declared_profiles=prepared["profiles"],
                declared_region_scopes=object_regions,
            )
        raw_context = study.get("context", {})
        if not isinstance(raw_context, Mapping) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in raw_context.items()
        ):
            raise DiagnosticInputError(f"study_context_invalid:{study_uid}")
        context = tuple(sorted(raw_context.items()))
        cache: dict[
            str,
            tuple[
                Slice,
                dict[str, Any],
                dict[str, Any],
                tuple[str, int, tuple[str, str, str]],
            ],
        ] = {}
        descriptions: list[CheapDescription] = []
        evidence: list[dict[str, Any]] = []
        frame_slice: Slice | None = None
        try:
            for index, raw_observation in enumerate(raw_observations):
                if not isinstance(raw_observation, Mapping):
                    raise DiagnosticInputError(
                        f"observation_must_be_object:{study_uid}:{index}"
                    )
                frame_spec, path = _frame_spec(
                    raw_observation.get("frame"), recipe_root
                )
                if str(path) not in cache:
                    try:
                        frame_slice = read_slice(path)
                    except Exception as error:
                        raise DiagnosticInputError(
                            f"dicom_frame_read_failed:{path}"
                        ) from error
                    if frame_slice.pixels.ndim != 2:
                        raise DiagnosticInputError(
                            f"single_frame_dicom_required:{path}"
                        )
                    if (
                        getattr(frame_slice.header, "StudyInstanceUID", None)
                        != study_uid
                    ):
                        raise DiagnosticInputError(f"dicom_study_uid_mismatch:{path}")
                    if (
                        getattr(frame_slice.header, "SeriesInstanceUID", None)
                        != frame_spec["series_uid"]
                    ):
                        raise DiagnosticInputError(f"dicom_series_uid_mismatch:{path}")
                    frame_geometry, geometry_status = _geometry(frame_slice)
                    cache[str(path)] = (
                        frame_slice,
                        frame_geometry,
                        geometry_status,
                        (
                            frame_spec["series_uid"],
                            frame_spec["slice_index"],
                            frame_spec["view"],
                        ),
                    )
                frame_slice, frame_geometry, geometry_status, cached_address = cache[
                    str(path)
                ]
                declared_address = (
                    frame_spec["series_uid"],
                    frame_spec["slice_index"],
                    frame_spec["view"],
                )
                if cached_address != declared_address:
                    raise DiagnosticInputError(
                        f"repeated_frame_address_mismatch:{path}"
                    )
                view = frame_spec["view"]
                object_name = _identity(raw_observation.get("object"), "object")
                profile_spec = _spec_profile(prepared, object_name, view)
                normalized_observation = dict(raw_observation)
                normalized_observation["binding"] = _bindings(
                    raw_observation.get("binding"), profile_spec, prepared["layout"]
                )
                description, row = _observation_profile(
                    study_uid=study_uid,
                    observation=normalized_observation,
                    index=index,
                    frame_spec=frame_spec,
                    pixels=frame_slice.pixels,
                    frame_geometry=frame_geometry,
                    geometry_status=geometry_status,
                    profile_spec=profile_spec,
                    prepared=prepared,
                    root=recipe_root,
                    mode=mode,
                    producer=producer,
                    dependencies=dependencies,
                    context=context,
                )
                measurement_contract_id = measurement_contract_ids[object_name]
                description, source_layout_id = _bind_measurement_identity(
                    description, measurement_contract_id
                )
                row["source_count_layout_id"] = source_layout_id
                row["measurement_contract_id"] = measurement_contract_id
                if declared_region_scopes is not None:
                    row["declared_region_scopes"] = list(
                        declared_region_scopes[object_name]
                    )
                if description.profile is None:
                    raise DiagnosticInputError(
                        f"cheap_profile_refused:{study_uid}:{index}:{description.status}"
                    )
                descriptions.append(description)
                evidence.append(row)
        finally:
            cache.clear()
            frame_slice = None
        profiles = _compose_profiles(
            descriptions, evidence, raw_vdb, declared_region_scopes
        )
        shared_measurement_arrays: dict[str, np.ndarray] = {}
        for row, description in zip(evidence, descriptions, strict=True):
            metric_rows = []
            declared_bindings = {
                (binding["bank"], binding["metric"]): binding
                for binding in row["bindings"]
            }
            if description.encoding is not None:
                for metric in description.encoding.metrics:
                    declared = declared_bindings[(metric.bank, metric.metric)]
                    if declared["source"] == "unavailable":
                        metric_rows.append(
                            {
                                "bank": metric.bank,
                                "metric": metric.metric,
                                "status": metric.status.value,
                                "source_state": "unavailable",
                                "reason": declared["reason"],
                                "row_names": metric.row_names,
                            }
                        )
                    else:
                        value_digest = _array_digest(metric.source_values)
                        available_digest = _array_digest(metric.source_available)
                        code_digest = _array_digest(metric.row_codes)
                        shared_measurement_arrays.setdefault(
                            value_digest, metric.source_values
                        )
                        shared_measurement_arrays.setdefault(
                            available_digest, metric.source_available
                        )
                        shared_measurement_arrays.setdefault(
                            code_digest, metric.row_codes
                        )
                        metric_rows.append(
                            {
                                "bank": metric.bank,
                                "metric": metric.metric,
                                "status": metric.status.value,
                                "source_state": "measured",
                                "row_names": metric.row_names,
                                "source_values_digest": value_digest,
                                "source_available_digest": available_digest,
                                "row_codes_digest": code_digest,
                                "nonfinite_available_count": metric.nonfinite_available_count,
                            }
                        )
            row["measurements"] = tuple(metric_rows)
        source_metadata = {
            "api": "knee.diagnosis.inputs.acquired_studies/v1",
            "schema": _SCHEMA,
            "study_uid": study_uid,
            "mode": mode,
            "producer": producer,
            "dependencies": dependencies,
            "encoding_spec_sha256": prepared["spec_sha256"],
            "measurement_identity_version": _MEASUREMENT_IDENTITY_VERSION,
            "measurement_contract_ids": measurement_contract_ids,
            "region_scopes": (
                None
                if declared_region_scopes is None
                else {
                    object_name: list(regions)
                    for object_name, regions in sorted(declared_region_scopes.items())
                }
            ),
            "profile_measurement_contract_ids": {
                profile.subject: measurement_contract_ids[profile.subject]
                for profile in profiles
            },
            "observations": tuple(evidence),
            "decoded_frame_count": len({row["frame"]["path"] for row in evidence}),
            "profiles_composed": len(profiles),
            "profiles": profiles,
            "profile_counts": tuple(profile.bundle.counts for profile in profiles),
            "shared_measurement_arrays": shared_measurement_arrays,
        }
        yield study_uid, profiles, source_metadata
