"""Compile and persist compact individual-case memory for squint inference.

The compiler reads the official study labels and already retained full
products. It does not rerun recognition or turn unlabeled conditions into
negative calls. Each case keeps its own squint profile and the exact sparse
record of its paired full profile, with shared interpretation context. Full
profiles can be read offline without opening the original H5 product.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import lzma
import math
import os
import tempfile
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from knee.study.tables import LABELS

SCHEMA = "knee.squint-memory/v1"
PROCEDURE = "knee.squint-ternary/v1"
FULL_CONTEXTS_SCHEMA = "knee.squint-full-profile-contexts/v1"
FULL_PAYLOADS_SCHEMA = "knee.squint-full-profile-payloads/v1"
FULL_PROFILE_REVISION = "portable-full-profiles-v1"

# Directly implicated presentations from docs/OBJECTS_AND_CONDITIONS.md §6.
# Context-only question roles remain in the memory without invented calls.
IMPLICATED_OBJECTS: dict[str, tuple[str, ...]] = {
    "femur": (
        "Medial OA",
        "Lateral OA",
        "PF OA",
        "Contusion",
        "Fracture",
        "ACL",
        "MCL",
    ),
    "tibia": (
        "Medial OA",
        "Lateral OA",
        "Contusion",
        "Fracture",
        "ACL",
        "MCL",
        "Medial Meniscus",
        "Lateral Meniscus",
    ),
    "patella": ("PF OA", "Contusion", "Fracture"),
    "fibula": ("Fracture",),
    "femoral_cartilage": ("Medial OA", "Lateral OA", "PF OA"),
    "tibial_cartilage": ("Medial OA", "Lateral OA"),
    "patellar_cartilage": ("PF OA",),
    "trochlear_cartilage": ("PF OA",),
    "medial_meniscus": ("Medial Meniscus", "Medial OA", "MCL"),
    "lateral_meniscus": ("Lateral Meniscus", "Lateral OA"),
    "acl": ("ACL",),
    "mcl": ("MCL",),
    "joint": ("Effusion", "Synovitis", "Baker's"),
    "joint_fluid": ("Effusion", "Synovitis"),
    "anterior_synovial_recess": ("Effusion", "Synovitis"),
    "joint_capsule": ("Effusion", "Synovitis", "Baker's"),
    "synovium": ("Synovitis", "Baker's"),
    "gastrocnemius_semimembranosus_bursa": ("Baker's",),
    "medial_gastrocnemius": ("Baker's",),
    "semimembranosus": ("Baker's",),
}


class SquintMemoryError(ValueError):
    """A named invalid bootstrap source, memory, or publication."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class MemorySnapshot:
    """One parsed memory manifest tied to the exact bytes read from disk."""

    path: Path
    sha256: str | None
    status: str
    declared_schema: str | None
    memory: dict[str, Any] | None
    error_code: str | None = None


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _json_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _full_context(manifest: dict[str, Any]) -> dict[str, Any]:
    """Keep exactly the shared product fields needed to interpret object rows."""
    composition = manifest.get("object_composition")
    if not isinstance(composition, dict) or not isinstance(
        composition.get("objects"), dict
    ):
        raise SquintMemoryError("full_product_object_composition_invalid")
    source_id = (
        manifest.get("study_uid")
        or manifest.get("studyUID")
        or manifest.get("source_id")
    )
    if not isinstance(source_id, str) or not source_id:
        raise SquintMemoryError("full_product_study_uid_invalid")
    manifest_fields = {
        key: manifest[key]
        for key in (
            "study_uid",
            "studyUID",
            "source_id",
            "mode",
            "encoding_mode",
            "product_storage",
            "spec_sha256",
            "carrier_identity",
        )
        if key in manifest
    }
    if "spec" in manifest:
        spec = manifest["spec"]
        manifest_fields["spec"] = (
            {"version": spec["version"]}
            if isinstance(spec, dict) and "version" in spec
            else {}
            if isinstance(spec, dict)
            else spec
        )
    composition_fields = (
        "schema",
        "carrier_identity",
        "layout_fingerprint",
        "registry_fingerprint",
        "layout",
    )
    return {
        "schema": "knee.squint-full-profile-context/v1",
        "study_uid": source_id,
        "manifest_fields": manifest_fields,
        "object_composition": {
            key: composition[key] for key in composition_fields if key in composition
        },
    }


def _portable_tables() -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        {"schema": FULL_CONTEXTS_SCHEMA, "contexts": {}},
        {"schema": FULL_PAYLOADS_SCHEMA, "payloads": {}},
    )


def _intern_full_context(
    manifest: dict[str, Any], contexts: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    context = _full_context(manifest)
    context_sha = _json_sha256(context)
    context_id = f"full-context:{context_sha}"
    prior_context = contexts.setdefault(context_id, context)
    if prior_context != context:
        raise SquintMemoryError("full_profile_context_hash_collision")
    return context_id, context


def _retain_full_record(
    context_id: str,
    context: dict[str, Any],
    subject: str,
    record: dict[str, Any],
    payloads: dict[str, Any],
) -> tuple[str, str]:
    """Intern one exact source object record and return its payload ID and digest."""
    record_sha = _json_sha256(record)
    payload_id = f"full-payload:{_json_sha256([context_id, context['study_uid'], subject, record_sha])}"
    payload = {
        "schema": "knee.squint-full-profile-payload/v1",
        "context_ref": context_id,
        "study_uid": context["study_uid"],
        "subject": subject,
        "record_sha256": record_sha,
        "record": record,
    }
    prior_payload = payloads.setdefault(payload_id, payload)
    if prior_payload != payload:
        raise SquintMemoryError("full_profile_payload_hash_collision")
    return payload_id, record_sha


def _sparse_count_availability(record: dict[str, Any]) -> str:
    rows = record.get("sparse_counts")
    if rows is None:
        return "missing_sparse_counts"
    if not isinstance(rows, list):
        return "malformed_sparse_counts"
    for entry in rows:
        if (
            not isinstance(entry, list)
            or len(entry) != 3
            or not isinstance(entry[0], str)
            or type(entry[1]) is not int
            or type(entry[2]) is not int
        ):
            return "malformed_sparse_counts"
    return "retained_sparse_counts"


def _read_labels(root: Path) -> dict[str, dict[str, int | None]]:
    path = root / "train.csv"
    if not path.is_file():
        raise SquintMemoryError("train_csv_missing")
    result: dict[str, dict[str, int | None]] = {}
    try:
        with path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None or len(reader.fieldnames) < 2:
                raise SquintMemoryError("train_csv_header_invalid")
            required = ("StudyInstanceUID", "Report", *LABELS)
            if tuple(reader.fieldnames) != required:
                raise SquintMemoryError("train_csv_columns_invalid")
            for row in reader:
                uid = row.get("StudyInstanceUID")
                if not isinstance(uid, str) or not uid or uid in result:
                    raise SquintMemoryError("train_csv_study_uid_invalid_or_duplicate")
                calls: dict[str, int | None] = {}
                for question in LABELS:
                    raw = row.get(question)
                    if raw == "":
                        calls[question] = None
                    elif raw in ("0", "1"):
                        calls[question] = int(raw)
                    else:
                        raise SquintMemoryError("train_csv_label_invalid")
                result[uid] = calls
    except (OSError, UnicodeError, csv.Error) as error:
        raise SquintMemoryError("train_csv_read_failed") from error
    return result


def _series_index(study: dict[str, Any]) -> dict[str, dict[str, Any]]:
    series = study.get("series")
    if not isinstance(series, list):
        raise SquintMemoryError("squint_series_missing")
    indexed: dict[str, dict[str, Any]] = {}
    for item in series:
        if not isinstance(item, dict):
            raise SquintMemoryError("squint_series_record_invalid")
        uid = item.get("series_uid")
        if not isinstance(uid, str) or not uid or uid in indexed:
            raise SquintMemoryError("squint_series_uid_invalid_or_duplicate")
        indexed[uid] = item
    return indexed


def _question_object_roles() -> dict[str, dict[str, str]]:
    """Join the frozen question object lists to direct SOP implications."""
    from knee.diagnosis.declarations import QUESTIONS

    roles: dict[str, dict[str, str]] = {}
    for question in QUESTIONS:
        for subject in question.objects:
            by_question = roles.setdefault(subject, {})
            by_question[question.question_id] = (
                "implicated"
                if subject in IMPLICATED_OBJECTS
                and question.question_id in IMPLICATED_OBJECTS[subject]
                else "context"
            )
    return roles


def _condition_calls(
    subject: str, labels: dict[str, int | None]
) -> tuple[dict[str, int], dict[str, str]]:
    """Retain signed labels while distinguishing normal from mixed presentations."""
    applicable = IMPLICATED_OBJECTS.get(subject, ())
    positive_exists = any(labels.get(question) == 1 for question in applicable)
    calls: dict[str, int] = {}
    scopes: dict[str, str] = {}
    for question in applicable:
        value = labels.get(question)
        if value is None:
            continue
        digit = 1 if value == 1 else -1
        calls[question] = digit
        if digit == 1:
            scopes[question] = "positive_condition_presentation"
        elif positive_exists:
            scopes[question] = "condition_negative_with_other_positive_presentation"
        else:
            scopes[question] = "normal_for_this_condition_only"
    return calls, scopes


def _coordinate_bbox(
    subject: str,
    series_uid: str,
    slice_index: int,
    entry: dict[str, Any],
    address: dict[str, Any],
    verified_arrays: Mapping[str, np.ndarray] | None,
) -> tuple[int, int, int, int] | None:
    """Resolve one exact native support from its public coordinate member."""
    if verified_arrays is None:
        return None
    links = entry.get("links")
    if not isinstance(links, list):
        return None
    for link in links:
        if not isinstance(link, dict) or link.get("coordinate_field") != "points_rc":
            continue
        member = link.get("coordinate_member")
        if not isinstance(member, str) or not member or member not in verified_arrays:
            continue
        metadata = link.get("metadata")
        if not isinstance(metadata, dict):
            raise SquintMemoryError("support_coordinate_metadata_invalid")
        observation = metadata.get("observation")
        if not isinstance(observation, dict):
            raise SquintMemoryError("support_coordinate_observation_invalid")
        if (
            link.get("profile_object") != subject
            or observation.get("series_uid") != series_uid
            or observation.get("slices") != [slice_index]
            or observation.get("support") != address.get("observation_support")
            or observation.get("view") != address.get("observation_view")
        ):
            continue
        native_shape = address.get("native_shape_rc")
        if native_shape is None:
            native_shape = metadata.get("native_shape_rc")
        if (
            not isinstance(native_shape, list)
            or len(native_shape) != 2
            or any(type(value) is not int or value <= 0 for value in native_shape)
        ):
            raise SquintMemoryError("support_coordinate_shape_invalid")
        points = np.asarray(verified_arrays[member])
        if (
            points.ndim != 2
            or points.shape[1] != 2
            or points.dtype.kind not in "iu"
            or points.dtype.kind == "b"
        ):
            raise SquintMemoryError("support_coordinate_array_invalid")
        declared_count = link.get("place_count")
        if (
            type(declared_count) is not int
            or declared_count < 0
            or len(points) != declared_count
        ):
            raise SquintMemoryError("support_coordinate_count_mismatch")
        if points.size == 0:
            return None
        if (
            np.any(points < 0)
            or np.any(points[:, 0] >= native_shape[0])
            or np.any(points[:, 1] >= native_shape[1])
        ):
            raise SquintMemoryError("support_coordinate_out_of_bounds")
        return (
            int(points[:, 0].min()),
            int(points[:, 0].max()) + 1,
            int(points[:, 1].min()),
            int(points[:, 1].max()) + 1,
        )
    return None


def _support_bbox(
    subject: str,
    series_uid: str,
    slice_index: int,
    support_ownership: dict[str, Any],
    source_roots: dict[str, Any],
    artifact_arrays: dict[Path, dict[str, np.ndarray]],
    verified_arrays: Mapping[str, np.ndarray] | None = None,
) -> tuple[int, int, int, int] | None:
    """Return native bounds for support at this target series and observation slice."""
    owner = (
        support_ownership.get(subject) if isinstance(support_ownership, dict) else None
    )
    entries = owner.get("addressed_supports", []) if isinstance(owner, dict) else []
    candidates: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        address = entry.get("source_address")
        if not isinstance(address, dict):
            continue
        if address.get("target_series_uid") != series_uid:
            continue
        observation_slices = address.get("observation_slices")
        if (
            not isinstance(observation_slices, list)
            or slice_index not in observation_slices
        ):
            continue
        if address.get("address_kind") != "native_rc":
            continue
        if address.get("geometry_status") != "available":
            continue
        candidates.append((entry, address))
    for entry, address in candidates:
        coordinate_bbox = _coordinate_bbox(
            subject, series_uid, slice_index, entry, address, verified_arrays
        )
        if coordinate_bbox is not None:
            return coordinate_bbox
        public_member_available = verified_arrays is not None and any(
            isinstance(link, dict)
            and link.get("coordinate_field") == "points_rc"
            and isinstance(link.get("coordinate_member"), str)
            and link.get("coordinate_member") in verified_arrays
            for link in entry.get("links", [])
        )
        if public_member_available:
            continue
        root_name = address.get("source_root")
        artifact = address.get("observation_artifact")
        if not isinstance(root_name, str) or not isinstance(artifact, str):
            continue
        source_root = source_roots.get(root_name)
        if not isinstance(source_root, str) or not source_root:
            continue
        root_path = Path(source_root).resolve()
        artifact_path = (root_path / artifact).resolve()
        try:
            artifact_path.relative_to(root_path)
        except ValueError:
            continue
        if not artifact_path.is_file():
            continue
        arrays = artifact_arrays.get(artifact_path)
        if arrays is None:
            try:
                raw = (
                    lzma.decompress(artifact_path.read_bytes())
                    if artifact_path.suffix == ".xz"
                    else artifact_path.read_bytes()
                )
                with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
                    lineage = address.get("lineage")
                    support_array = (
                        lineage.get("support_array")
                        if isinstance(lineage, dict)
                        else None
                    )
                    support_name = address.get("observation_support")
                    desired = [
                        name
                        for name in (support_array, support_name, "a1_objects")
                        if isinstance(name, str) and name
                    ]
                    names = set(desired)
                    for name in desired:
                        names.add(f"{name}_slices")
                    names.update(
                        (
                            "a3_bone_plane_labels",
                            "a3_bone_plane_slices",
                            "a3_femur_plane_region",
                            "a3_femur_plane_slices",
                            "a3_tibia_plane_region",
                            "a3_tibia_plane_slices",
                        )
                    )
                    arrays = {
                        name: archive[name] for name in archive.files if name in names
                    }
            except (OSError, EOFError, lzma.LZMAError, ValueError):
                continue
            artifact_arrays[artifact_path] = arrays
        support_name = address.get("observation_support")
        lineage = address.get("lineage")
        support_array = (
            lineage.get("support_array") if isinstance(lineage, dict) else None
        )
        candidates_names: list[str] = []
        for name in (support_array, support_name, "a1_objects"):
            if (
                isinstance(name, str)
                and name in arrays
                and name not in candidates_names
            ):
                candidates_names.append(name)
        label = address.get("observation_label")
        for array_name in candidates_names:
            array = np.asarray(arrays[array_name])
            native_shape = address.get("native_shape_rc")
            if (
                not isinstance(native_shape, list)
                or len(native_shape) != 2
                or any(type(value) is not int or value <= 0 for value in native_shape)
            ):
                continue
            if array.ndim == 3:
                slice_key = {
                    "a3_bone_plane_labels": "a3_bone_plane_slices",
                    "a3_femur_plane_region": "a3_femur_plane_slices",
                    "a3_tibia_plane_region": "a3_tibia_plane_slices",
                }.get(array_name, f"{array_name.removesuffix('_labels')}_slices")
                if (
                    slice_key not in arrays
                    and "a3_bone_plane_slices" in arrays
                    and array_name == "a3_bone_plane_labels"
                ):
                    slice_key = "a3_bone_plane_slices"
                if slice_key in arrays:
                    source_slices = np.asarray(arrays[slice_key]).reshape(-1)
                    choices = np.flatnonzero(source_slices == slice_index)
                    row = address.get("observation_row")
                    if (
                        choices.size != 1
                        or type(row) is not int
                        or row != int(choices[0])
                        or not 0 <= row < array.shape[0]
                    ):
                        continue
                    array = array[row]
                else:
                    row = address.get("observation_row")
                    if type(row) is not int or not 0 <= row < array.shape[0]:
                        continue
                    array = array[row]
            if array.ndim != 2 or array.shape != tuple(native_shape):
                continue
            mask = array == label if type(label) is int else array != 0
            rows, cols = np.nonzero(mask)
            if rows.size:
                return (
                    int(rows.min()),
                    int(rows.max()) + 1,
                    int(cols.min()),
                    int(cols.max()) + 1,
                )
    return None


def _geometry_window(
    series: dict[str, Any],
    point_lps: list[float] | None,
    slice_index: int,
    support_bbox: tuple[int, int, int, int] | None = None,
) -> tuple[tuple[int, int, int, int, int, int], dict[str, Any]] | None:
    """Project retained support bounds or an LPS keypoint to squint tiles."""
    stack = series.get("stack")
    centres = getattr(stack, "centres_lps", None)
    bounds = getattr(stack, "bounds_rc", None)
    shape = series.get("shape")
    if centres is None or bounds is None or not isinstance(shape, (tuple, list)):
        return None
    if len(shape) != 3:
        return None
    z_count, native_rows, native_cols = (int(value) for value in shape)
    if not 0 <= slice_index < z_count:
        return None
    plane = centres[slice_index]
    tile_rows = int(plane.shape[0])
    tile_cols = int(plane.shape[1])
    if support_bbox is not None:
        sr0, sr1, sc0, sc1 = support_bbox
        overlaps: list[tuple[int, int]] = []
        for tile_r in range(tile_rows):
            for tile_c in range(tile_cols):
                tr0, tr1, tc0, tc1 = (int(value) for value in bounds[tile_r, tile_c])
                if tr0 < sr1 and sr0 < tr1 and tc0 < sc1 and sc0 < tc1:
                    overlaps.append((tile_r, tile_c))
        if overlaps:
            tile_r0 = min(item[0] for item in overlaps)
            tile_r1 = max(item[0] for item in overlaps) + 1
            tile_c0 = min(item[1] for item in overlaps)
            tile_c1 = max(item[1] for item in overlaps) + 1
            tile_window = (
                slice_index,
                slice_index + 1,
                tile_r0,
                tile_r1,
                tile_c0,
                tile_c1,
            )
            r0, r1, c0, c1 = sr0, sr1, sc0, sc1
        else:
            return None
    else:
        if (
            not isinstance(point_lps, list)
            or len(point_lps) != 3
            or any(
                not isinstance(value, (int, float)) or not math.isfinite(value)
                for value in point_lps
            )
        ):
            return None
        best: tuple[float, int, int] | None = None
        for tile_r in range(tile_rows):
            for tile_c in range(tile_cols):
                center = plane[tile_r, tile_c]
                distance_sq = sum(
                    (float(center[i]) - float(point_lps[i])) ** 2 for i in range(3)
                )
                candidate = (distance_sq, tile_r, tile_c)
                if best is None or candidate < best:
                    best = candidate
        if best is None:
            return None
        _, tile_r, tile_c = best
        r0, r1, c0, c1 = (int(value) for value in bounds[tile_r, tile_c])
        tile_window = (
            slice_index,
            slice_index + 1,
            tile_r,
            tile_r + 1,
            tile_c,
            tile_c + 1,
        )
    if not (0 <= r0 < r1 <= native_rows and 0 <= c0 < c1 <= native_cols):
        return None
    geometry = series.get("geometry")
    spacing = None
    if isinstance(geometry, dict):
        spacing_values = geometry.get("spacing")
        if spacing_values is not None and 0 <= slice_index < len(spacing_values):
            spacing = [float(value) for value in spacing_values[slice_index]]
    sample_extent = [float(r1 - r0), float(c1 - c0)]
    if spacing is not None and len(spacing) == 2:
        sample_extent = [(r1 - r0) * spacing[0], (c1 - c0) * spacing[1]]
    region = {
        "source_window": list(tile_window),
        "native_bounds_rc": [r0, r1, c0, c1],
        "relative_extent": [
            (r1 - r0) / native_rows,
            (c1 - c0) / native_cols,
        ],
        "sample_extent_mm": sample_extent,
        "source_point_lps": None
        if point_lps is None
        else [float(value) for value in point_lps],
    }
    return tile_window, region


def _profile_regions(
    study: dict[str, Any],
    full_records: dict[str, Any],
    series_by_uid: dict[str, dict[str, Any]],
    support_ownership: dict[str, Any],
    source_roots: dict[str, Any],
    object_contexts: dict[str, Any],
    verified_arrays: Mapping[str, np.ndarray] | None = None,
) -> tuple[dict[str, dict], dict[str, list[dict]]]:
    from knee.diagnosis.squint_profiles import (
        merge_profiles,
        profile_window,
        refine_window,
    )

    profiles_by_subject: dict[str, list[dict]] = {}
    regions_by_subject: dict[str, list[dict]] = {}
    artifact_arrays: dict[Path, dict[str, np.ndarray]] = {}
    for subject, record in full_records.items():
        context = record.get("spatial_context")
        point = context.get("point_lps") if isinstance(context, dict) else None
        keyplanes = context.get("keyplanes", {}) if isinstance(context, dict) else {}
        choices: list[dict[str, Any]] = []
        if isinstance(keyplanes, dict):
            for orientation in ("sagittal", "coronal", "axial"):
                plane = keyplanes.get(orientation)
                if isinstance(plane, dict) and plane.get("outcome") == "selected":
                    choices.append(
                        {
                            **plane,
                            "orientation_name": orientation,
                            "selection_source": "spatial_context.keyplanes",
                        }
                    )
        if not choices:
            context_record = (
                object_contexts.get(subject, {})
                if isinstance(object_contexts, dict)
                else {}
            )
            decisions = (
                context_record.get("definition_decisions", [])
                if isinstance(context_record, dict)
                else []
            )
            for decision in decisions:
                if (
                    not isinstance(decision, dict)
                    or decision.get("code") != "identified"
                ):
                    continue
                view = decision.get("view")
                if not isinstance(view, list) or not view:
                    continue
                choices.append(
                    {
                        "orientation_name": str(view[0]).lower(),
                        "series_uid": decision.get("series_uid"),
                        "slice": decision.get("slice_index"),
                        "view": {
                            "orientation": view[0],
                            "fluid_sensitive": view[1],
                            "fat_suppression": view[2],
                        },
                        "outcome": "identified",
                        "selection_source": "object_contexts.definition_decisions",
                    }
                )
        if not choices:
            owner = (
                support_ownership.get(subject, {})
                if isinstance(support_ownership, dict)
                else {}
            )
            addressed = (
                owner.get("addressed_supports", []) if isinstance(owner, dict) else []
            )
            seen_addresses: set[tuple[str, int, tuple[str, ...]]] = set()
            for entry in addressed:
                address = (
                    entry.get("source_address") if isinstance(entry, dict) else None
                )
                if not isinstance(address, dict):
                    continue
                series_uid = address.get("target_series_uid")
                slice_index = address.get("record_slice_index")
                view = address.get("record_view")
                if (
                    not isinstance(series_uid, str)
                    or type(slice_index) is not int
                    or not isinstance(view, list)
                ):
                    continue
                identity = (
                    series_uid,
                    slice_index,
                    tuple(str(value) for value in view),
                )
                if identity in seen_addresses:
                    continue
                seen_addresses.add(identity)
                choices.append(
                    {
                        "orientation_name": str(view[0]).lower() if view else "unknown",
                        "series_uid": series_uid,
                        "slice": slice_index,
                        "view": {
                            "orientation": view[0],
                            "fluid_sensitive": view[1],
                            "fat_suppression": view[2],
                        }
                        if len(view) == 3
                        else None,
                        "outcome": "retained_support_address",
                        "selection_source": "support_ownership.addressed_supports",
                    }
                )
                if len(choices) >= 3:
                    break
        for plane in choices:
            orientation = plane.get("orientation_name")
            series_uid = plane.get("series_uid")
            slice_index = plane.get("slice")
            series = (
                series_by_uid.get(series_uid) if isinstance(series_uid, str) else None
            )
            if series is None or type(slice_index) is not int:
                continue
            support_bbox = _support_bbox(
                subject,
                series_uid,
                slice_index,
                support_ownership,
                source_roots,
                artifact_arrays,
                verified_arrays,
            )
            result = _geometry_window(
                series,
                point if isinstance(point, list) else None,
                slice_index,
                support_bbox,
            )
            if result is None:
                continue
            window, region = result
            profile = profile_window(series, window, subject=subject)
            if not isinstance(profile, dict):
                raise SquintMemoryError("profile_window_result_invalid")
            stack = series.get("stack")
            if getattr(stack, "code", None) == "present":
                refined = refine_window(series, window, subject=subject, tile_mm=2.0)
                if not isinstance(refined, dict):
                    raise SquintMemoryError("refine_window_result_invalid")
                combined = merge_profiles((profile, refined), subject=subject)
                region["fine_refinement"] = "measured_or_silent"
            else:
                combined = profile
                region["fine_refinement"] = "unavailable_coarse_series"
            profiles_by_subject.setdefault(subject, []).append(combined)
            view = series.get("view")
            region.update(
                {
                    "orientation": orientation,
                    "view": view,
                    "series_uid": series_uid,
                    "source_slice": slice_index,
                    "support_source": plane.get("selection_source"),
                    "support_code": plane.get("outcome"),
                    "extent_source": "retained_object_support"
                    if support_bbox is not None
                    else "retained_physical_location",
                }
            )
            regions_by_subject.setdefault(subject, []).append(region)
    merged: dict[str, dict] = {}
    for subject, profiles in profiles_by_subject.items():
        result = merge_profiles(profiles, subject=subject)
        if not isinstance(result, dict):
            raise SquintMemoryError("merge_profiles_result_invalid")
        merged[subject] = result
    return merged, regions_by_subject


def _plain_profile(profile: dict[str, Any]) -> dict[str, Any]:
    subject = profile.get("subject")
    banks = profile.get("banks")
    source = profile.get("source")
    if not isinstance(subject, str) or not isinstance(banks, dict):
        raise SquintMemoryError("squint_profile_invalid")
    clean_banks: dict[str, list[int]] = {}
    for name, counts in banks.items():
        if (
            not isinstance(name, str)
            or not name
            or not isinstance(counts, (tuple, list))
            or len(counts) != 3
        ):
            raise SquintMemoryError("squint_profile_bank_invalid")
        values: list[int] = []
        for value in counts:
            if type(value) is not int or value < 0:
                raise SquintMemoryError("squint_profile_count_invalid")
            values.append(value)
        clean_banks[name] = values

    def compact_source(source_record: dict[str, Any]) -> dict[str, Any]:
        result = {
            key: value
            for key, value in source_record.items()
            if key != "series_context"
        }
        context = source_record.get("series_context")
        if isinstance(context, dict):
            calibration = context.get("calibration")
            calibration_hash = None
            if isinstance(calibration, dict):
                calibration_hash = hashlib.sha256(
                    json.dumps(
                        calibration,
                        sort_keys=True,
                        separators=(",", ":"),
                        allow_nan=False,
                    ).encode("utf-8")
                ).hexdigest()
            result["series_context"] = {
                "api": context.get("api"),
                "study_uid": context.get("study_uid"),
                "series_uid": context.get("series_uid"),
                "tile_mm": context.get("tile_mm"),
                "procedure": context.get("procedure"),
                "geometry_status": context.get("geometry_status"),
                "calibration_sha256": calibration_hash,
                "calibration": calibration,
            }
        lineage = source_record.get("lineage")
        if isinstance(lineage, list):
            result["lineage"] = [
                compact_source(item) for item in lineage if isinstance(item, dict)
            ]
        return result

    return {
        "schema": "knee.squint-profile/v1",
        "subject": subject,
        "banks": clean_banks,
        "source": compact_source(source) if isinstance(source, dict) else {},
    }


def _link_configuration_full_profiles(memory: dict[str, Any]) -> None:
    """Point composed question cases at the canonical payload refs they already use."""
    canonical: dict[tuple[str, str], dict[str, str]] = {}
    for case in memory.get("cases", []):
        full = case.get("full_profile")
        if (
            isinstance(full, dict)
            and isinstance(case.get("study_uid"), str)
            and isinstance(case.get("subject"), str)
            and isinstance(full.get("payload_ref"), str)
            and isinstance(full.get("context_ref"), str)
        ):
            canonical[(case["study_uid"], case["subject"])] = {
                "payload_ref": full["payload_ref"],
                "context_ref": full["context_ref"],
                "availability": full.get("availability"),
            }
    for case in memory.get("cases", []):
        if not str(case.get("case_id", "")).startswith("squint-configuration:"):
            continue
        uid = case.get("study_uid")
        subjects = case.get("full_profiles")
        if not isinstance(uid, str) or not isinstance(subjects, dict):
            continue
        refs = {
            subject: canonical[(uid, subject)]
            for subject in subjects
            if (uid, subject) in canonical
        }
        if refs:
            case["full_profile_refs"] = refs


def _full_profile_retention_receipt(memory: dict[str, Any]) -> dict[str, Any]:
    contexts = memory.get("full_profile_contexts", {}).get("contexts", {})
    payloads = memory.get("full_profile_payloads", {}).get("payloads", {})
    linked = 0
    for case in memory.get("cases", []):
        full = case.get("full_profile")
        if isinstance(full, dict) and isinstance(full.get("payload_ref"), str):
            linked += 1
        refs = case.get("full_profile_refs")
        if isinstance(refs, dict):
            linked += len(refs)
    return {
        "schema": "knee.squint-full-profile-retention/v1",
        "context_count": len(contexts) if isinstance(contexts, dict) else 0,
        "payload_count": len(payloads) if isinstance(payloads, dict) else 0,
        "case_payload_links": linked,
        "publication_reader_verified_pairs": None,
    }


def full_profile_from_case(
    memory: dict[str, Any], case: dict[str, Any], *, subject: str | None = None
):
    """Reconstruct one full canonical-object Profile from portable sparse rows.

    `subject` is required for a question-composition case, whose full object
    roles remain separate payload references. This function never opens the
    original H5 or source-root path.
    """
    clean = _validate_memory(memory)
    case_id = case.get("case_id") if isinstance(case, dict) else None
    if not isinstance(case_id, str):
        raise SquintMemoryError("full_profile_case_identity_invalid")
    retained_case = next(
        (item for item in clean["cases"] if item.get("case_id") == case_id), None
    )
    if retained_case is None or retained_case != case:
        raise SquintMemoryError("full_profile_case_not_in_memory")
    if subject is None:
        if retained_case.get("subject", "").startswith("diagnosis/"):
            raise SquintMemoryError("full_profile_object_subject_required")
        subject = retained_case.get("subject")
    if not isinstance(subject, str) or not subject:
        raise SquintMemoryError("full_profile_object_subject_invalid")
    refs = retained_case.get("full_profile_refs")
    if isinstance(refs, dict):
        linked_reference = refs.get(subject)
        identities = retained_case.get("full_profiles")
        identity = identities.get(subject) if isinstance(identities, dict) else None
        if isinstance(linked_reference, dict) and isinstance(identity, dict):
            reference = {**identity, **linked_reference}
        else:
            reference = linked_reference
    elif subject == retained_case.get("subject"):
        full = retained_case.get("full_profile")
        reference = full if isinstance(full, dict) else None
    else:
        reference = None
    if not isinstance(reference, dict):
        raise SquintMemoryError("full_profile_not_portable")
    if not isinstance(reference.get("payload_ref"), str) or not isinstance(
        reference.get("context_ref"), str
    ):
        raise SquintMemoryError("full_profile_not_portable")
    return _full_profile_from_validated_case(clean, retained_case, reference, subject)


def _full_profile_from_validated_case(
    clean: dict[str, Any],
    retained_case: dict[str, Any],
    reference: dict[str, Any],
    subject: str,
):
    from knee.diagnosis.models import Profile
    from knee.diagnosis.product_cases import profiles_from_manifest

    if reference.get("availability") != "retained_sparse_counts":
        raise SquintMemoryError(
            "full_profile_" + str(reference.get("availability", "counts_unavailable"))
        )
    context_ref = reference.get("context_ref")
    payload_ref = reference.get("payload_ref")
    context_table = clean.get("full_profile_contexts")
    payload_table = clean.get("full_profile_payloads")
    contexts = (
        context_table.get("contexts") if isinstance(context_table, dict) else None
    )
    payloads = (
        payload_table.get("payloads") if isinstance(payload_table, dict) else None
    )
    if not isinstance(contexts, dict) or not isinstance(payloads, dict):
        raise SquintMemoryError("full_profile_tables_missing")
    context = contexts.get(context_ref)
    payload = payloads.get(payload_ref)
    if not isinstance(context, dict) or not isinstance(payload, dict):
        raise SquintMemoryError("full_profile_reference_missing")
    if payload.get("context_ref") != context_ref:
        raise SquintMemoryError("full_profile_context_reference_mismatch")
    if (
        payload.get("study_uid") != retained_case.get("study_uid")
        or payload.get("subject") != subject
        or context.get("study_uid") != retained_case.get("study_uid")
    ):
        raise SquintMemoryError("full_profile_source_identity_mismatch")
    record = payload.get("record")
    if not isinstance(record, dict) or _json_sha256(record) != payload.get(
        "record_sha256"
    ):
        raise SquintMemoryError("full_profile_payload_digest_mismatch")
    identity = (
        retained_case.get("full_profiles", {}).get(subject)
        if isinstance(retained_case.get("full_profiles"), dict)
        else reference
    )
    if not isinstance(identity, dict):
        identity = reference
    if identity.get("product_record_sha256") != payload.get("record_sha256"):
        raise SquintMemoryError("full_profile_record_identity_mismatch")
    if identity.get("count_layout_id") != record.get("count_layout_id"):
        raise SquintMemoryError("full_profile_layout_identity_mismatch")
    manifest_fields = context.get("manifest_fields")
    composition = context.get("object_composition")
    if not isinstance(manifest_fields, dict) or not isinstance(composition, dict):
        raise SquintMemoryError("full_profile_context_malformed")
    manifest = dict(manifest_fields)
    manifest["object_composition"] = {**composition, "objects": {subject: record}}
    mode = identity.get("mode", "full")
    try:
        profiles = profiles_from_manifest(manifest, mode=mode)
    except (TypeError, ValueError) as error:
        raise SquintMemoryError("full_profile_manifest_rejected") from error
    profile = next((item for item in profiles if item.subject == subject), None)
    if profile is None or profile.source_id != retained_case.get("study_uid"):
        raise SquintMemoryError("full_profile_reader_result_mismatch")
    expected = {
        "carrier_identity": identity.get("carrier_identity"),
        "layout_fingerprint": identity.get("layout_fingerprint"),
        "reference_set_identity": identity.get("reference_set_identity"),
    }
    provenance = dict(profile.provenance)
    for key, value in expected.items():
        if value is not None and provenance.get(key) != value:
            raise SquintMemoryError(f"full_profile_{key}_mismatch")
    source_records = retained_case.get("full_sources")
    source_record = (
        source_records.get(subject)
        if isinstance(source_records, dict)
        else retained_case.get("full_source", {})
    )
    product_sha = (
        source_record.get("product_sha256", "")
        if isinstance(source_record, dict)
        else ""
    )
    provenance.update(
        {
            "retained_case_id": retained_case["case_id"],
            "retained_payload_ref": payload_ref,
            "retained_product_sha256": product_sha,
        }
    )
    return Profile(
        subject=profile.subject,
        bundle=profile.bundle,
        mode=profile.mode,
        scope=profile.scope,
        source_id=retained_case["study_uid"],
        context=profile.context,
        bank_statuses=profile.bank_statuses,
        provenance=tuple(
            sorted((key, str(value)) for key, value in provenance.items())
        ),
    )


def hydrate_full_profiles(memory: dict[str, Any], products: Path) -> dict[str, Any]:
    """Attach portable full sparse records from already retained H5 manifests.

    This performs no DICOM reads or anatomical recognition. Product bytes must
    match the exact digest already recorded by the memory's source identity.
    """
    from knee.encoding.product import open_product

    clean = json.loads(_canonical(_validate_memory(memory)))
    contexts_table, payloads_table = _portable_tables()
    context_cache: dict[str, tuple[str, dict[str, Any]]] = {}
    product_root = Path(products)
    by_uid = {path.stem: path for path in product_root.glob("*.h5") if path.is_file()}
    source_identities = clean.get("source_identities")
    if not isinstance(source_identities, dict):
        raise SquintMemoryError("source_identities_invalid")
    cases_by_source: dict[str, list[dict[str, Any]]] = {}
    for item in clean["cases"]:
        if isinstance(item.get("full_profile"), dict):
            cases_by_source.setdefault(item.get("study_uid", ""), []).append(item)
    for uid, cases in cases_by_source.items():
        source = source_identities.get(uid)
        path = by_uid.get(uid)
        if not isinstance(source, dict) or path is None:
            raise SquintMemoryError("full_profile_source_product_missing")
        expected_digest = source.get("product_sha256")
        if not isinstance(expected_digest, str) or _digest(path) != expected_digest:
            raise SquintMemoryError("full_profile_source_product_digest_mismatch")
        with open_product(path) as product:
            manifest = product.manifest
        manifest_uid = (
            manifest.get("study_uid")
            or manifest.get("studyUID")
            or manifest.get("source_id")
        )
        if manifest_uid != uid:
            raise SquintMemoryError("full_profile_source_study_uid_mismatch")
        context_id = _json_sha256(_full_context(manifest))
        cached = context_cache.get(context_id)
        if cached is None:
            context_ref, context = _intern_full_context(
                manifest, contexts_table["contexts"]
            )
            context_cache[context_id] = (context_ref, context)
        else:
            context_ref, context = cached
        composition = manifest.get("object_composition")
        records = composition.get("objects") if isinstance(composition, dict) else None
        if not isinstance(records, dict):
            raise SquintMemoryError("full_profile_source_objects_missing")
        for case in cases:
            subject = case.get("subject")
            record = records.get(subject) if isinstance(subject, str) else None
            if not isinstance(record, dict):
                raise SquintMemoryError("full_profile_source_object_missing")
            payload_ref, record_sha = _retain_full_record(
                context_ref, context, subject, record, payloads_table["payloads"]
            )
            full = case["full_profile"]
            if (
                full.get("product_record_sha256") != record_sha
                or full.get("count_layout_id") != record.get("count_layout_id")
                or full.get("reference_set_identity")
                != record.get("reference_set_identity")
                or full.get("layout_fingerprint")
                != context["object_composition"].get("layout_fingerprint")
                or full.get("carrier_identity")
                != context["object_composition"].get("carrier_identity")
            ):
                raise SquintMemoryError("full_profile_source_record_identity_mismatch")
            full.update(
                {
                    "availability": _sparse_count_availability(record),
                    "context_ref": context_ref,
                    "payload_ref": payload_ref,
                }
            )
    clean["full_profile_contexts"] = contexts_table
    clean["full_profile_payloads"] = payloads_table
    clean["revision"] = (
        clean["revision"]
        if FULL_PROFILE_REVISION in clean["revision"]
        else f"{clean['revision']}+{FULL_PROFILE_REVISION}"
    )
    _link_configuration_full_profiles(clean)
    clean["full_profile_retention"] = _full_profile_retention_receipt(clean)
    return _validate_memory(clean)


def compile_bootstrap(
    root: Path,
    products: Path,
    out: Path,
    *,
    selected_uids: tuple[str, ...] | None = None,
    io_workers: int = 8,
) -> dict:
    """Build individual squint cases from existing H5 products and train.csv."""
    from knee.diagnosis.squint_configurations import with_configuration_cases
    from knee.diagnosis.squint_profiles import read_study_squints

    root, products, out = Path(root), Path(products), Path(out)
    if type(io_workers) is not int or io_workers < 1:
        raise SquintMemoryError("io_workers_invalid")
    labels = _read_labels(root)
    available = {path.stem: path for path in products.glob("*.h5") if path.is_file()}
    if selected_uids is None:
        uids = tuple(
            sorted(
                uid
                for uid, row in labels.items()
                if all(value is not None for value in row.values())
            )
        )
    else:
        if not isinstance(selected_uids, tuple) or any(
            not isinstance(uid, str) or not uid for uid in selected_uids
        ):
            raise SquintMemoryError("selected_uids_invalid")
        if len(set(selected_uids)) != len(selected_uids):
            raise SquintMemoryError("selected_uids_duplicate")
        uids = selected_uids
    if not uids:
        raise SquintMemoryError("bootstrap_studies_empty")
    missing_labels = [uid for uid in uids if uid not in labels]
    missing_products = [uid for uid in uids if uid not in available]
    if missing_labels:
        raise SquintMemoryError("bootstrap_label_missing")
    if missing_products:
        raise SquintMemoryError("bootstrap_product_missing")

    cases: list[dict[str, Any]] = []
    source_identities: dict[str, dict[str, Any]] = {}
    label_ledger: dict[str, dict[str, int | None]] = {}
    full_contexts, full_payloads = _portable_tables()
    for uid in uids:
        product_path = available[uid]
        # Keep the product's exact object records and shared interpretation
        # context. Reconstructing all full CountBundles here would materialize
        # many silent layout rows.
        from knee.encoding.product import open_product

        squint_study = read_study_squints(root, uid, io_workers=io_workers)
        series_by_uid = _series_index(squint_study)
        with open_product(product_path) as product:
            manifest = product.manifest
            if manifest.get("study_uid") != uid:
                raise SquintMemoryError("product_study_uid_mismatch")
            composition = manifest.get("object_composition")
            if not isinstance(composition, dict) or not isinstance(
                composition.get("objects"), dict
            ):
                raise SquintMemoryError("product_object_composition_invalid")
            raw_objects = composition["objects"]
            context_ref, portable_context = _intern_full_context(
                manifest, full_contexts["contexts"]
            )
            roots = manifest.get("source_roots", {})
            ownership = manifest.get("support_ownership", {})
            contexts = manifest.get("object_contexts", {})
            source_identities[uid] = {
                "product_path": str(product_path.resolve()),
                "product_sha256": _digest(product_path),
                "layout_fingerprint": composition.get("layout_fingerprint"),
                "carrier_identity": composition.get("carrier_identity"),
                "source_roots": roots if isinstance(roots, dict) else {},
                "full_profile_subjects": sorted(raw_objects),
            }
            full_records = raw_objects
            cheap_by_subject, regions_by_subject = _profile_regions(
                squint_study,
                raw_objects,
                series_by_uid,
                ownership if isinstance(ownership, dict) else {},
                roots if isinstance(roots, dict) else {},
                contexts if isinstance(contexts, dict) else {},
                product.arrays,
            )
        label_ledger[uid] = dict(labels[uid])
        question_roles = _question_object_roles()
        for subject, full_record in full_records.items():
            roles = question_roles.get(subject)
            if roles is None:
                continue
            cheap = cheap_by_subject.get(subject)
            if cheap is None:
                continue
            calls, call_scopes = _condition_calls(subject, labels[uid])
            full_source = source_identities[uid]
            case_id = f"squint-case:{uid}:{subject}"
            payload_ref, record_sha = _retain_full_record(
                context_ref,
                portable_context,
                subject,
                full_record,
                full_payloads["payloads"],
            )
            cases.append(
                {
                    "case_id": case_id,
                    "study_uid": uid,
                    "subject": subject,
                    "condition_calls": calls,
                    "presentation_scope": call_scopes
                    or {
                        "kind": "structural_context",
                        "label_scope": "condition_not_asked_or_unlabeled",
                    },
                    "question_roles": roles,
                    "label_attribution": {
                        question: {
                            "source": "train.csv",
                            "source_path": str((root / "train.csv").resolve()),
                            "study_uid": uid,
                            "condition": question,
                        }
                        for question in calls
                    },
                    "profile": _plain_profile(cheap),
                    "regions": regions_by_subject.get(subject, []),
                    "full_profile": {
                        "subject": subject,
                        "mode": "full",
                        "scope": f"object:{subject}",
                        "count_layout_id": full_record.get("count_layout_id"),
                        "reference_set_identity": full_record.get(
                            "reference_set_identity"
                        ),
                        "carrier_identity": composition.get("carrier_identity"),
                        "layout_fingerprint": composition.get("layout_fingerprint"),
                        "product_record_sha256": record_sha,
                        "availability": _sparse_count_availability(full_record),
                        "context_ref": context_ref,
                        "payload_ref": payload_ref,
                    },
                    "full_source": {
                        "product_path": full_source["product_path"],
                        "product_sha256": full_source["product_sha256"],
                        "study_uid": uid,
                        "source_roots": full_source["source_roots"],
                    },
                    "teaching_source": {
                        "kind": "official_train_csv_label",
                        "revision": "bootstrap-2026-10-21-native-supports-v2",
                    },
                }
            )
        del (
            squint_study,
            series_by_uid,
            cheap_by_subject,
            regions_by_subject,
            full_records,
        )
    memory = {
        "schema": SCHEMA,
        "revision": "bootstrap-2026-10-21-native-supports-v2",
        "procedure": {
            "id": PROCEDURE,
            "tile_mm": 10.0,
            "mode_pair": ["full", "squint"],
        },
        "questions": list(LABELS),
        "object_conditions": {
            key: list(value) for key, value in IMPLICATED_OBJECTS.items()
        },
        "object_question_roles": _question_object_roles(),
        "source_identities": source_identities,
        "full_profile_contexts": full_contexts,
        "full_profile_payloads": full_payloads,
        "label_ledger": label_ledger,
        "cases": cases,
    }
    memory["revision"] = f"{memory['revision']}+{FULL_PROFILE_REVISION}"
    memory = with_configuration_cases(memory)
    _link_configuration_full_profiles(memory)
    memory["full_profile_retention"] = _full_profile_retention_receipt(memory)
    from knee.diagnosis.squint_locator import prepare_recall

    preparation_started = time.perf_counter()
    prepared_recall = prepare_recall(memory)
    preparation_seconds = time.perf_counter() - preparation_started
    if prepared_recall.get("outcome") != "prepared":
        raise SquintMemoryError("bootstrap_recall_preparation_failed")
    publication = save_memory(memory, out, prepared_recall=prepared_recall)
    configuration_case_count = len(memory["cases"]) - len(cases)
    return {
        "schema": SCHEMA,
        "path": str((out / "manifest.json").resolve()),
        "study_count": len(uids),
        "case_count": len(memory["cases"]),
        "object_case_count": len(cases),
        "configuration_case_count": configuration_case_count,
        "source_count": len(source_identities),
        "source_identities": source_identities,
        "revision": memory["revision"],
        "recall_preparation_seconds": preparation_seconds,
        "recall_preparation_cache": publication.get("recall_preparation_cache"),
    }


def _validate_memory(memory: object) -> dict[str, Any]:
    if not isinstance(memory, dict) or memory.get("schema") != SCHEMA:
        raise SquintMemoryError("memory_schema_invalid")
    if not isinstance(memory.get("revision"), str) or not memory["revision"]:
        raise SquintMemoryError("memory_revision_invalid")
    cases = memory.get("cases")
    if not isinstance(cases, list):
        raise SquintMemoryError("memory_cases_invalid")
    case_ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise SquintMemoryError("memory_case_invalid")
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id or case_id in case_ids:
            raise SquintMemoryError("memory_case_id_invalid_or_duplicate")
        case_ids.add(case_id)
        if not isinstance(case.get("study_uid"), str) or not isinstance(
            case.get("subject"), str
        ):
            raise SquintMemoryError("memory_case_identity_invalid")
        calls = case.get("condition_calls")
        if not isinstance(calls, dict) or any(
            question not in LABELS or type(digit) is not int or digit not in (-1, 1)
            for question, digit in calls.items()
        ):
            raise SquintMemoryError("memory_case_calls_invalid")
        profile = case.get("profile")
        if (
            not isinstance(profile, dict)
            or profile.get("schema") != "knee.squint-profile/v1"
        ):
            raise SquintMemoryError("memory_case_profile_invalid")
        banks = profile.get("banks")
        if not isinstance(banks, dict):
            raise SquintMemoryError("memory_case_banks_invalid")
        for name, counts in banks.items():
            if (
                not isinstance(name, str)
                or not name
                or not isinstance(counts, list)
                or len(counts) != 3
            ):
                raise SquintMemoryError("memory_case_bank_invalid")
            if any(type(value) is not int or value < 0 for value in counts):
                raise SquintMemoryError("memory_case_count_invalid")
        regions = case.get("regions")
        if not isinstance(regions, list) or any(
            not isinstance(region, dict) for region in regions
        ):
            raise SquintMemoryError("memory_case_regions_invalid")
    contexts_table = memory.get("full_profile_contexts")
    payloads_table = memory.get("full_profile_payloads")
    if (contexts_table is None) != (payloads_table is None):
        raise SquintMemoryError("full_profile_tables_incomplete")
    if contexts_table is None and any(
        isinstance(case.get("full_profile"), dict)
        and (
            "payload_ref" in case["full_profile"]
            or "context_ref" in case["full_profile"]
        )
        or "full_profile_refs" in case
        for case in cases
    ):
        raise SquintMemoryError("full_profile_tables_missing")
    contexts: dict[str, Any] = {}
    payloads: dict[str, Any] = {}
    if contexts_table is not None:
        if (
            not isinstance(contexts_table, dict)
            or contexts_table.get("schema") != FULL_CONTEXTS_SCHEMA
            or not isinstance(contexts_table.get("contexts"), dict)
            or not isinstance(payloads_table, dict)
            or payloads_table.get("schema") != FULL_PAYLOADS_SCHEMA
            or not isinstance(payloads_table.get("payloads"), dict)
        ):
            raise SquintMemoryError("full_profile_tables_malformed")
        contexts = contexts_table["contexts"]
        payloads = payloads_table["payloads"]
        for context_id, context in contexts.items():
            if (
                not isinstance(context_id, str)
                or not isinstance(context, dict)
                or context.get("schema") != "knee.squint-full-profile-context/v1"
                or context_id != f"full-context:{_json_sha256(context)}"
            ):
                raise SquintMemoryError("full_profile_context_invalid")
        for payload_id, payload in payloads.items():
            if (
                not isinstance(payload_id, str)
                or not isinstance(payload, dict)
                or payload.get("schema") != "knee.squint-full-profile-payload/v1"
                or payload.get("context_ref") not in contexts
                or not isinstance(payload.get("study_uid"), str)
                or not isinstance(payload.get("subject"), str)
                or not isinstance(payload.get("record"), dict)
            ):
                raise SquintMemoryError("full_profile_payload_invalid")
            record_sha = _json_sha256(payload["record"])
            expected_id = f"full-payload:{_json_sha256([payload['context_ref'], payload['study_uid'], payload['subject'], record_sha])}"
            if (
                payload_id != expected_id
                or payload.get("record_sha256") != record_sha
                or contexts[payload["context_ref"]].get("study_uid")
                != payload["study_uid"]
            ):
                raise SquintMemoryError("full_profile_payload_digest_invalid")
        for case in cases:
            full = case.get("full_profile")
            if isinstance(full, dict) and (
                "payload_ref" in full or "context_ref" in full
            ):
                payload = payloads.get(full.get("payload_ref"))
                context = contexts.get(full.get("context_ref"))
                if (
                    not isinstance(payload, dict)
                    or not isinstance(context, dict)
                    or payload.get("context_ref") != full.get("context_ref")
                    or payload.get("study_uid") != case.get("study_uid")
                    or payload.get("subject") != case.get("subject")
                    or full.get("product_record_sha256") != payload.get("record_sha256")
                    or full.get("count_layout_id")
                    != payload.get("record", {}).get("count_layout_id")
                    or full.get("reference_set_identity")
                    != payload.get("record", {}).get("reference_set_identity")
                    or full.get("carrier_identity")
                    != context.get("object_composition", {}).get("carrier_identity")
                    or full.get("layout_fingerprint")
                    != context.get("object_composition", {}).get("layout_fingerprint")
                ):
                    raise SquintMemoryError("full_profile_case_reference_invalid")
            refs = case.get("full_profile_refs")
            if refs is not None:
                if not isinstance(refs, dict):
                    raise SquintMemoryError("full_profile_case_role_refs_invalid")
                for subject, reference in refs.items():
                    payload = (
                        payloads.get(reference.get("payload_ref"))
                        if isinstance(reference, dict)
                        else None
                    )
                    if (
                        not isinstance(subject, str)
                        or not isinstance(reference, dict)
                        or not isinstance(payload, dict)
                        or payload.get("context_ref") != reference.get("context_ref")
                        or payload.get("study_uid") != case.get("study_uid")
                        or payload.get("subject") != subject
                    ):
                        raise SquintMemoryError(
                            "full_profile_case_role_reference_invalid"
                        )
    if memory.get("questions") != list(LABELS):
        raise SquintMemoryError("memory_questions_invalid")
    return memory


def _canonical(memory: dict[str, Any]) -> bytes:
    return json.dumps(
        memory,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def save_memory(
    memory: dict, path: Path, *, prepared_recall: Mapping[str, Any] | None = None
) -> dict:
    """Atomically publish one immutable memory directory without pickle."""
    if not isinstance(path, Path):
        raise SquintMemoryError("memory_path_required")
    clean = json.loads(_canonical(_validate_memory(memory)))
    destination = path.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise SquintMemoryError("memory_already_exists")
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    try:
        data = _canonical(clean)
        manifest_path = temporary / "manifest.json"
        with manifest_path.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        # Read each distinct retained sparse payload through the public adapter
        # before publishing. Reuse the validated manifest so the complete
        # memory is not rehashed for every profile; release each dense bundle
        # before resolving the next one.
        if clean.get("full_profile_contexts") is not None:
            retention = _full_profile_retention_receipt(clean)
            clean["full_profile_retention"] = retention
            try:
                readback = json.loads(manifest_path.read_text(encoding="utf-8"))
                _validate_memory(readback)
                verified_payloads: set[str] = set()
                unavailable: dict[str, int] = {}
                verified_count = 0
                for case in readback["cases"]:
                    reference = case.get("full_profile")
                    if not isinstance(reference, dict):
                        continue
                    payload_ref = reference.get("payload_ref")
                    if (
                        not isinstance(payload_ref, str)
                        or payload_ref in verified_payloads
                    ):
                        continue
                    verified_payloads.add(payload_ref)
                    if reference.get("availability") != "retained_sparse_counts":
                        state = str(
                            reference.get("availability", "availability_missing")
                        )
                        unavailable[state] = unavailable.get(state, 0) + 1
                        continue
                    profile = _full_profile_from_validated_case(
                        readback, case, reference, case["subject"]
                    )
                    if profile.source_id != case.get("study_uid"):
                        raise SquintMemoryError(
                            "full_profile_publication_readback_mismatch"
                        )
                    verified_count += 1
                    del profile
                retention["publication_reader_verified_pairs"] = verified_count
                retention["publication_reader_unavailable_payloads"] = unavailable
                data = _canonical(clean)
                with manifest_path.open("wb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
            except (
                OSError,
                UnicodeError,
                json.JSONDecodeError,
                StopIteration,
            ) as error:
                raise SquintMemoryError(
                    "full_profile_publication_readback_failed"
                ) from error
        recall_cache_receipt = None
        if prepared_recall is not None:
            from knee.diagnosis.squint_locator import persisted_recall_cache
            from knee.json_store import dump_json_atomic

            cache = persisted_recall_cache(clean, prepared_recall)
            cache["memory_manifest_sha256"] = hashlib.sha256(data).hexdigest()
            cache["memory_revision"] = clean["revision"]
            cache_path = dump_json_atomic(temporary / "recall-preparation.json", cache)
            recall_cache_receipt = {
                "schema": cache["schema"],
                "path": str((destination / cache_path.name).resolve()),
                "sha256": hashlib.sha256(cache_path.read_bytes()).hexdigest(),
                "bytes": cache_path.stat().st_size,
                "memory_manifest_sha256": cache["memory_manifest_sha256"],
            }
        directory_fd = os.open(temporary, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        if destination.exists():
            raise SquintMemoryError("memory_already_exists")
        os.replace(temporary, destination)
        parent_fd = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    except Exception:
        if temporary.exists():
            import shutil

            shutil.rmtree(temporary)
        raise
    return {
        "schema": SCHEMA,
        "manifest": str(destination / "manifest.json"),
        "sha256": hashlib.sha256(data).hexdigest(),
        "case_count": len(clean["cases"]),
        "recall_preparation_cache": recall_cache_receipt,
    }


def inspect_memory_snapshot(path: Path | None) -> MemorySnapshot:
    """Read one manifest byte sequence and classify it without a second read."""
    if path is None:
        return MemorySnapshot(
            Path(), None, "unavailable", None, None, "memory_manifest_missing"
        )
    requested = Path(path)
    manifest_path = requested / "manifest.json" if requested.is_dir() else requested
    if not manifest_path.is_file():
        return MemorySnapshot(
            manifest_path.resolve(),
            None,
            "unavailable",
            None,
            None,
            "memory_manifest_missing",
        )
    try:
        raw = manifest_path.read_bytes()
    except FileNotFoundError:
        return MemorySnapshot(
            manifest_path.resolve(),
            None,
            "unavailable",
            None,
            None,
            "memory_manifest_missing",
        )
    except OSError:
        return MemorySnapshot(
            manifest_path.resolve(),
            None,
            "invalid",
            None,
            None,
            "memory_manifest_invalid",
        )
    digest = hashlib.sha256(raw).hexdigest()
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError):
        return MemorySnapshot(
            manifest_path.resolve(),
            digest,
            "invalid",
            None,
            None,
            "memory_manifest_invalid",
        )
    declared_schema = value.get("schema") if isinstance(value, dict) else None
    if declared_schema != SCHEMA:
        status = "legacy" if isinstance(value, dict) else "invalid"
        error = None if status == "legacy" else "memory_schema_invalid"
        return MemorySnapshot(
            manifest_path.resolve(), digest, status, declared_schema, None, error
        )
    try:
        memory = _validate_memory(value)
    except SquintMemoryError as error:
        return MemorySnapshot(
            manifest_path.resolve(), digest, "invalid", SCHEMA, None, error.code
        )
    return MemorySnapshot(manifest_path.resolve(), digest, "squint", SCHEMA, memory)


def load_memory_snapshot(path: Path) -> MemorySnapshot:
    """Load a validated squint memory and retain the exact input digest."""
    snapshot = inspect_memory_snapshot(path)
    if snapshot.status == "squint":
        return snapshot
    raise SquintMemoryError(snapshot.error_code or "memory_schema_invalid")


def load_memory(path: Path) -> dict:
    """Read and validate a squint memory directory or its manifest path."""
    snapshot = load_memory_snapshot(path)
    assert snapshot.memory is not None
    return snapshot.memory
