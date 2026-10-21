"""Compile and persist compact individual-case memory for squint inference.

The compiler reads the official study labels and already retained full
products. It does not rerun recognition or turn unlabeled conditions into
negative calls. Each case keeps its own squint profile and the exact sparse
record of its paired full profile, with shared interpretation context. Full
profiles can be read offline without opening the original H5 product.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
import os
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
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

# Bootstrap profile writers (SQUINT_TRAINING_BUILD §§3-4). ``squint-v1`` reads
# each case region's box against the scan's own terciles; it stays the default
# so an old memory rebuilds byte for byte. ``territory-v2`` reads the object's
# own saved support (its teacher territory), the surrounding tiles as a separate
# context role and nothing outside the leg, against cutoffs over the leg alone.
# A v2 memory carries its own revision and never mixes with a v1 one.
WRITER_V1 = "squint-v1"
WRITER_TERRITORY = "territory-v2"
BOOTSTRAP_WRITERS = (WRITER_V1, WRITER_TERRITORY)
TERRITORY_REVISION = "bootstrap-2026-10-21-territory-v2"
_V1_REVISION = "bootstrap-2026-10-21-native-supports-v2"
_TERRITORY_RECEIPT_SCHEMA = "knee.squint-territory-writer/v1"
_TERRITORY_FINE_TILE_MM = 2.0

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


CONDITION_CARRY_SCHEMA = "knee.squint-condition-carry/v1"
#: Conditions a study label states for some eligible bone without naming which
#: (HOW_TO_BUILD, "Preserve study-label scope through bone recall").
MULTI_SITE_BONE_CONDITIONS = ("Fracture", "Contusion")
#: The scope of a multi-site bone positive that a supplied call localizes to
#: this object. The condition combiner keeps such a positive; it holds a
#: ``positive_condition_presentation`` one unknown, because the study label
#: alone does not say which bone.
LOCALIZED_PRESENTATION_SCOPE = "localized_condition_presentation"
_LOCALIZED_CALL_KEYS = ("question", "study_uid", "subject", "digit", "source")


def _localized_call_valid(record: object) -> bool:
    if not isinstance(record, Mapping) or not set(_LOCALIZED_CALL_KEYS) <= set(record):
        return False
    return (
        record["question"] in LABELS
        and all(
            isinstance(record[key], str) and record[key]
            for key in ("study_uid", "subject")
        )
        and type(record["digit"]) is int
        and record["digit"] in (-1, 0, 1)
        and isinstance(record["source"], Mapping)
        and bool(record["source"])
    )


def carry_condition_calls(
    case: Mapping[str, Any],
    identity_call: Mapping[str, Any],
    labels: Mapping[str, int | None],
    *,
    localized_calls: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """A study's labels on one recognized object, carried across its identity views.

    CLASSICAL_AI_BUILD_DESIGN §5.1: a diagnosis belongs to its object, so a
    positive for a condition implicating it is a positive presentation in
    every view where its identity holds at once, and its normal presentations
    speak through those views alike. ``identity_call`` is the case's confirm
    call; its views are read as identity recall reads them (every view of the
    case when it names none), and its ``negative_views``, other tissue, never
    carry. The calls and scopes are exactly ``_condition_calls``'s: a normal
    label never carries beyond them and no call is made where the label is
    blank. A Fracture or Contusion label stays ``positive_condition_presentation``
    (some bone, not which) unless ``localized_calls`` holds a sourced positive
    naming this study's object; only then is it this object's presentation
    (``LOCALIZED_PRESENTATION_SCOPE``). A localized call never creates or flips
    a call: one that cannot apply is kept, by name, in
    ``unapplied_localized_calls``. Calls naming another object are not read.
    Malformed input raises ``SquintMemoryError``.
    """
    from knee.diagnosis.squint_identity import confirm_call_views
    from knee.diagnosis.squint_locator import _bank_view

    if not isinstance(case, Mapping):
        raise SquintMemoryError("carry_case_invalid")
    case_id, study_uid, subject = (
        case.get("case_id"),
        case.get("study_uid"),
        case.get("subject"),
    )
    if not all(
        isinstance(value, str) and value for value in (case_id, study_uid, subject)
    ):
        raise SquintMemoryError("carry_case_identity_invalid")
    if subject.startswith("diagnosis/"):
        raise SquintMemoryError("carry_case_not_object")
    profile = case.get("profile")
    banks = profile.get("banks") if isinstance(profile, Mapping) else None
    if not isinstance(banks, Mapping):
        raise SquintMemoryError("carry_case_profile_invalid")
    if (
        not isinstance(identity_call, Mapping)
        or identity_call.get("candidate_id") != case_id
    ):
        raise SquintMemoryError("carry_identity_call_not_this_case")
    resolved = confirm_call_views(identity_call)
    if resolved["outcome"] != "views":
        raise SquintMemoryError(str(resolved["reason"]))
    if resolved["views"] is None:
        # A whole-case confirm holds every view the case's banks are read in.
        identity_scope = "whole_case"
        read_views = (_bank_view(name) for name in banks if isinstance(name, str))
        views = sorted({view for view in read_views if view is not None})
    else:
        identity_scope = "confirmed_views"
        views = sorted(resolved["views"])
    if not isinstance(labels, Mapping) or any(
        labels.get(question) is not None
        and (
            type(labels.get(question)) is not int or labels.get(question) not in (0, 1)
        )
        for question in IMPLICATED_OBJECTS.get(subject, ())
    ):
        raise SquintMemoryError("carry_labels_invalid")
    if isinstance(localized_calls, (str, bytes, Mapping)) or not isinstance(
        localized_calls, Sequence
    ):
        raise SquintMemoryError("carry_localized_calls_invalid")
    calls, scopes = _condition_calls(subject, dict(labels))
    applied: dict[str, list[dict[str, Any]]] = {}
    unapplied: list[dict[str, Any]] = []
    for record in localized_calls:
        if not _localized_call_valid(record):
            raise SquintMemoryError("carry_localized_call_invalid")
        if record["study_uid"] != study_uid or record["subject"] != subject:
            continue
        question = record["question"]
        if record["digit"] != 1:
            reason = "carry_is_positive_only"
        elif question not in IMPLICATED_OBJECTS.get(subject, ()):
            reason = "condition_not_implicated"
        elif question not in MULTI_SITE_BONE_CONDITIONS:
            reason = "condition_not_multi_site"
        elif labels.get(question) is None:
            reason = "label_absent"
        elif labels.get(question) != 1:
            reason = "label_not_positive"
        else:
            reason = None
        if reason is not None:
            unapplied.append({"call": copy.deepcopy(dict(record)), "reason": reason})
            continue
        scopes[question] = LOCALIZED_PRESENTATION_SCOPE
        applied.setdefault(question, []).append(copy.deepcopy(dict(record)))
    view_lists = [list(view) for view in views]
    return {
        "schema": CONDITION_CARRY_SCHEMA,
        "case_id": case_id,
        "study_uid": study_uid,
        "subject": subject,
        "identity_scope": identity_scope,
        "identity_views": view_lists,
        "condition_calls": calls,
        "presentation_scope": scopes,
        "speaks_through": {question: copy.deepcopy(view_lists) for question in calls},
        "labels": {question: labels[question] for question in calls},
        "localized_calls": applied,
        "unapplied_localized_calls": unapplied,
    }


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
    from knee.diagnosis.squint_support import support_mask

    resolved = support_mask(
        subject,
        series_uid,
        slice_index,
        support_ownership,
        source_roots,
        artifact_arrays,
        verified_arrays,
    )
    return resolved["bbox"] if resolved["code"] == "resolved" else None


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
        choices, point = _region_choices(
            subject, record, support_ownership, object_contexts
        )
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


def _region_choices(
    subject: str,
    record: dict[str, Any],
    support_ownership: dict[str, Any],
    object_contexts: dict[str, Any],
) -> tuple[list[dict[str, Any]], Any]:
    """Name the planes one object's case regions are read on, and its LPS point.

    Selected key planes first; otherwise identified definition decisions;
    otherwise up to three distinct retained support addresses. Both writers
    read the same planes, so a territory case differs from its v1 twin only in
    how each plane is read.
    """
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
            if not isinstance(decision, dict) or decision.get("code") != "identified":
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
            address = entry.get("source_address") if isinstance(entry, dict) else None
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
    return choices, point


def _territory_writer(
    leg_maps: Callable[[dict[str, Any]], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Bind the territory-v2 producers, or refuse by name before any study is read.

    The territory writer (``squint_profiles``) and the teacher support
    (``squint_support``) come from their lanes; this is the one place the
    compiler binds them. The leg map stays an explicit input: ``leg_maps`` maps
    one loaded study to its leg map per series, and defaults to
    ``squint_leg.leg_maps``. The configuration composer must accept the
    territory procedure, so configurations are rebuilt from the v2 object
    profiles, never relabelled to pass the v1 check.
    """
    from knee.diagnosis.squint_interfaces import TERRITORY_PROCEDURE

    try:
        from knee.diagnosis.squint_configurations import (
            configuration_profile,
            with_configuration_cases,
        )
        from knee.diagnosis.squint_profiles import (
            leg_calibration,
            merge_profiles,
            profile_territory,
            refine_territory,
        )
        from knee.diagnosis.squint_support import support_mask, teacher_territory
    except ImportError as error:
        raise SquintMemoryError("territory_writer_unavailable") from error
    if leg_maps is None:
        try:
            from knee.diagnosis.squint_leg import leg_maps
        except ImportError as error:
            raise SquintMemoryError("territory_leg_maps_unavailable") from error
    if not callable(leg_maps):
        raise SquintMemoryError("territory_leg_maps_invalid")
    try:
        probe = configuration_profile({}, LABELS[0], procedure=TERRITORY_PROCEDURE)
    except TypeError as error:
        raise SquintMemoryError("territory_configurations_unavailable") from error
    probe_source = probe.get("source") if isinstance(probe, dict) else None
    if (
        not isinstance(probe_source, dict)
        or probe_source.get("procedure") != TERRITORY_PROCEDURE
    ):
        raise SquintMemoryError("territory_configurations_unavailable")
    return {
        "leg_maps": leg_maps,
        "support_mask": support_mask,
        "teacher_territory": teacher_territory,
        "leg_calibration": leg_calibration,
        "profile_territory": profile_territory,
        "refine_territory": refine_territory,
        "merge_profiles": merge_profiles,
        "with_configuration_cases": with_configuration_cases,
    }


def _json_value(value: object) -> Any:
    """A JSON-safe copy of a provenance value; refuse what JSON cannot hold."""
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise SquintMemoryError("territory_address_not_json")
            result[key] = _json_value(item)
        return result
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, np.ndarray):
        return _json_value(value.tolist())
    if isinstance(value, np.generic):
        return _json_value(value.item())
    if value is None or isinstance(value, (bool, str, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise SquintMemoryError("territory_address_not_json")


def _territory_address(territory: Mapping[str, Any]) -> dict[str, Any]:
    """A territory as a JSON address: its window and every tile's role and share.

    The native support mask stays runtime-only (``squint_interfaces``); its
    slices, offset, shape, pixel count and digest identify it exactly, and its
    saved source address stays in the provenance.
    """
    from knee.diagnosis.squint_interfaces import (
        ROLE_CONTEXT,
        ROLE_OBJECT,
        ROLE_OUTSIDE_LEG,
        ROLE_UNQUERIED,
    )

    roles = np.asarray(territory["roles"])
    share = np.asarray(territory["object_share"], dtype=np.float64)
    support = territory["native_support"]
    mask = np.ascontiguousarray(support["mask"], dtype=np.bool_)
    return {
        "schema": territory["schema"],
        "origin": territory["origin"],
        "study_uid": territory["study_uid"],
        "series_uid": territory["series_uid"],
        "subject": territory["subject"],
        "tile_window": [int(value) for value in territory["tile_window"]],
        "roles": roles.astype(np.int64).tolist(),
        "role_counts": {
            "object": int(np.count_nonzero(roles == ROLE_OBJECT)),
            "context": int(np.count_nonzero(roles == ROLE_CONTEXT)),
            "outside_leg": int(np.count_nonzero(roles == ROLE_OUTSIDE_LEG)),
            "unqueried": int(np.count_nonzero(roles == ROLE_UNQUERIED)),
        },
        # NaN means no share was measured for that tile; JSON keeps it as null.
        "object_share": np.where(np.isfinite(share), share, None).tolist(),
        "native_support": {
            "slices": [int(value) for value in support["slices"]],
            "offset_rc": [int(value) for value in support["offset_rc"]],
            "shape": [int(value) for value in mask.shape],
            "pixel_count": int(np.count_nonzero(mask)),
            "mask_sha256": hashlib.sha256(mask.tobytes()).hexdigest(),
        },
        "key_planes": _json_value(territory.get("key_planes")),
        "relation": _json_value(territory.get("relation")),
        "anchors": _json_value(territory.get("anchors")),
        "provenance": _json_value(territory.get("provenance")),
    }


def _native_support_bbox(
    support: Mapping[str, Any],
) -> tuple[int, int, int, int] | None:
    """The native half-open box around the support's own pixels: an address only."""
    mask = np.asarray(support.get("mask"))
    offset = support.get("offset_rc")
    if (
        mask.dtype != np.bool_
        or mask.ndim != 3
        or not isinstance(offset, (list, tuple))
        or len(offset) != 2
    ):
        return None
    rows, cols = np.nonzero(mask.any(axis=0))
    if not rows.size:
        return None
    row_offset, col_offset = (int(value) for value in offset)
    return (
        row_offset + int(rows.min()),
        row_offset + int(rows.max()) + 1,
        col_offset + int(cols.min()),
        col_offset + int(cols.max()) + 1,
    )


def _saved_support_slices(
    subject: str, series_uid: str, support_ownership: dict[str, Any]
) -> list[int]:
    """Observation slices of this series at which the object has a saved native support.

    The same address filter as ``support_mask``: the target series, a native
    pixel address and available geometry. Coarse-grid estimates and per-slice
    profile areas are not outlines and are not listed.
    """
    owner = (
        support_ownership.get(subject) if isinstance(support_ownership, dict) else None
    )
    entries = owner.get("addressed_supports", []) if isinstance(owner, dict) else []
    slices: set[int] = set()
    for entry in entries:
        address = entry.get("source_address") if isinstance(entry, dict) else None
        if (
            not isinstance(address, dict)
            or address.get("target_series_uid") != series_uid
            or address.get("address_kind") != "native_rc"
            or address.get("geometry_status") != "available"
        ):
            continue
        observed = address.get("observation_slices")
        if isinstance(observed, list):
            slices.update(
                value for value in observed if type(value) is int and value >= 0
            )
    return sorted(slices)


def _teacher_territory(
    writer: Mapping[str, Any],
    study_uid: str,
    series: dict[str, Any],
    subject: str,
    slice_index: int,
    leg_map: Mapping[str, Any],
    support_ownership: dict[str, Any],
    source_roots: dict[str, Any],
    artifact_arrays: dict[Path, dict[str, np.ndarray]],
    verified_arrays: Mapping[str, np.ndarray] | None,
    *,
    already_read: frozenset[int] = frozenset(),
) -> tuple[dict[str, Any] | None, str, dict[str, Any]]:
    """Resolve one region's teacher territory, its key slice first.

    Where no saved outline exists at the key slice (``support_unavailable``),
    the object's other saved native supports in the same series are tried
    through the same resolver, nearest to the key slice first and the lower
    slice on a tie, skipping slices this object already reads in the series.
    Returns ``(territory, "valid", choice)`` or ``(None, reason, choice)``,
    where ``choice`` records the key slice, the slice used and every attempt
    with its code. A support that resolves nowhere in the series keeps the key
    slice's refusal; it is never replaced by a box or a keypoint tile.
    """
    series_uid = series.get("series_uid")
    choice: dict[str, Any] = {
        "key_slice": slice_index,
        "used_slice": None,
        "rule": "key_slice",
        "attempts": [],
    }

    def attempt(index: int) -> tuple[dict[str, Any] | None, str]:
        territory, code = _territory_at(
            writer,
            study_uid,
            series,
            subject,
            index,
            leg_map,
            support_ownership,
            source_roots,
            artifact_arrays,
            verified_arrays,
        )
        choice["attempts"].append({"slice": index, "code": code})
        return territory, code

    territory, reason = attempt(slice_index)
    if territory is not None:
        choice["used_slice"] = slice_index
        return territory, "valid", choice
    if reason != "support_unavailable":
        return None, reason, choice
    choice["rule"] = "nearest_saved_support_in_series"
    candidates = sorted(
        (
            index
            for index in _saved_support_slices(subject, series_uid, support_ownership)
            if index != slice_index
        ),
        key=lambda index: (abs(index - slice_index), index),
    )
    for index in candidates:
        if index in already_read:
            choice["attempts"].append(
                {"slice": index, "code": "support_slice_already_read"}
            )
            continue
        territory, _ = attempt(index)
        if territory is not None:
            distance = abs(index - slice_index)
            choice.update(
                {
                    "used_slice": index,
                    "distance_slices": distance,
                    "equally_near_slices": [
                        other
                        for other in candidates
                        if other != index and abs(other - slice_index) == distance
                    ],
                }
            )
            return territory, "valid", choice
    return None, reason, choice


def _territory_at(
    writer: Mapping[str, Any],
    study_uid: str,
    series: dict[str, Any],
    subject: str,
    slice_index: int,
    leg_map: Mapping[str, Any],
    support_ownership: dict[str, Any],
    source_roots: dict[str, Any],
    artifact_arrays: dict[Path, dict[str, np.ndarray]],
    verified_arrays: Mapping[str, np.ndarray] | None,
) -> tuple[dict[str, Any] | None, str]:
    """Resolve the saved support at one slice into a teacher territory.

    Returns ``(territory, "valid")`` or ``(None, reason)``. The reason is the
    support resolver's or the territory maker's own named code.
    """
    from knee.diagnosis.squint_interfaces import territory_code

    series_uid = series.get("series_uid")
    mask_info = writer["support_mask"](
        subject,
        series_uid,
        slice_index,
        support_ownership,
        source_roots,
        artifact_arrays,
        verified_arrays,
    )
    if not isinstance(mask_info, Mapping):
        return None, "support_result_invalid"
    if mask_info.get("code") != "resolved":
        code = mask_info.get("code")
        return None, code if isinstance(code, str) and code else "support_unresolved"
    territory = writer["teacher_territory"](
        study_uid, series, subject, mask_info, slice_index, leg_map=leg_map
    )
    if not isinstance(territory, Mapping):
        return None, "teacher_territory_result_invalid"
    code = territory.get("code", "resolved")
    if code != "resolved":
        return None, code if isinstance(code, str) and code else "territory_refused"
    grid = tuple(int(value) for value in series["stack"].median.shape)
    code = territory_code(territory, grid_shape=grid)
    if code != "valid":
        return None, code
    if (
        territory.get("origin") != "teacher_support"
        or territory.get("study_uid") != study_uid
        or territory.get("series_uid") != series_uid
        or territory.get("subject") != subject
    ):
        return None, "territory_identity_mismatch"
    support = territory.get("native_support")
    if not isinstance(support, Mapping):
        return None, "territory_native_support_missing"
    if list(support.get("slices", ())) != [slice_index]:
        return None, "territory_slice_mismatch"
    return dict(territory), "valid"


def _require_territory_profile(profile: object, subject: str) -> dict[str, Any]:
    """Return a territory-writer profile, or refuse its first named defect."""
    from knee.diagnosis.squint_interfaces import (
        TERRITORY_PROCEDURE,
        parse_territory_bank_name,
    )

    if not isinstance(profile, dict) or profile.get("schema") != (
        "knee.squint-profile/v1"
    ):
        raise SquintMemoryError("territory_profile_schema_invalid")
    if profile.get("subject") != subject:
        raise SquintMemoryError("territory_profile_subject_mismatch")
    source = profile.get("source")
    if not isinstance(source, dict) or source.get("procedure") != TERRITORY_PROCEDURE:
        raise SquintMemoryError("territory_profile_procedure_mismatch")
    banks = profile.get("banks")
    if not isinstance(banks, dict):
        raise SquintMemoryError("territory_profile_banks_invalid")
    if any(parse_territory_bank_name(name) is None for name in banks):
        raise SquintMemoryError("territory_profile_bank_not_role_named")
    return profile


def _leg_map_summary(leg_map: object, series: Mapping[str, Any]) -> dict[str, Any]:
    """Name one series' leg map and identify it by rule, counts and digest."""
    from knee.diagnosis.squint_interfaces import (
        LEG_INSIDE,
        LEG_MIXED,
        LEG_OUTSIDE,
        LEG_UNKNOWN,
        leg_map_code,
    )

    if leg_map is None:
        return {"code": "leg_map_unavailable"}
    median = getattr(series.get("stack"), "median", None)
    grid = tuple(median.shape) if isinstance(median, np.ndarray) else None
    code = leg_map_code(leg_map, grid_shape=grid)
    if code != "valid":
        return {"code": code}
    assert isinstance(leg_map, Mapping)
    codes = leg_map["codes"]
    return {
        "code": "valid",
        "rule": leg_map["rule"],
        "counts": {
            name: int(np.count_nonzero(codes == value))
            for name, value in (
                ("inside", LEG_INSIDE),
                ("outside", LEG_OUTSIDE),
                ("mixed", LEG_MIXED),
                ("unknown", LEG_UNKNOWN),
            )
        },
        "codes_sha256": hashlib.sha256(
            np.ascontiguousarray(codes).tobytes()
        ).hexdigest(),
    }


def _unprofiled_region(
    plane: Mapping[str, Any],
    series: Mapping[str, Any] | None,
    reason: str,
    choice: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """One plane a case region could not be read on, with its named reason."""
    view = series.get("view") if isinstance(series, Mapping) else plane.get("view")
    return {
        "orientation": plane.get("orientation_name"),
        "view": view,
        "series_uid": plane.get("series_uid"),
        "source_slice": plane.get("slice"),
        "key_slice": plane.get("slice"),
        "support_source": plane.get("selection_source"),
        "support_code": plane.get("outcome"),
        "writer": WRITER_TERRITORY,
        "profile_status": "not_profiled",
        "reason": reason,
        "slice_choice": None if choice is None else dict(choice),
    }


def _territory_profile_regions(
    study: dict[str, Any],
    full_records: dict[str, Any],
    series_by_uid: dict[str, dict[str, Any]],
    support_ownership: dict[str, Any],
    source_roots: dict[str, Any],
    object_contexts: dict[str, Any],
    verified_arrays: Mapping[str, np.ndarray] | None,
    *,
    subjects: frozenset[str],
    writer: Mapping[str, Any],
) -> tuple[
    dict[str, dict], dict[str, list[dict]], dict[str, list[dict]], dict[str, Any]
]:
    """Read every case region of one study over its teacher territory.

    The study's leg maps are made once, and each series' leg-only calibration
    once, shared by every object read on that series. Only subjects that can
    become cases are read. Each region is read coarse and fine over the same
    territory and the two are merged, as v1 merges its box readings. Returns
    the merged profile per subject, the profiled regions (v1's address fields
    plus the territory address), the regions left unprofiled with their named
    reasons, and the study's receipt.
    """
    from knee.diagnosis.squint_interfaces import TERRITORY_PROCEDURE

    study_uid = study.get("study_uid")
    if not isinstance(study_uid, str) or not study_uid:
        raise SquintMemoryError("squint_study_uid_invalid")
    leg_maps = writer["leg_maps"](study)
    if not isinstance(leg_maps, Mapping):
        raise SquintMemoryError("leg_maps_result_invalid")
    leg_summary = {
        uid: _leg_map_summary(leg_maps.get(uid), series)
        for uid, series in series_by_uid.items()
    }
    calibrations: dict[str, Any] = {}
    artifact_arrays: dict[Path, dict[str, np.ndarray]] = {}
    profiles_by_subject: dict[str, list[dict]] = {}
    regions_by_subject: dict[str, list[dict]] = {}
    unprofiled_by_subject: dict[str, list[dict]] = {}
    subject_counts: dict[str, dict[str, Any]] = {}
    for subject, record in full_records.items():
        if subject not in subjects:
            continue
        choices, point = _region_choices(
            subject, record, support_ownership, object_contexts
        )
        counts = subject_counts.setdefault(
            subject,
            {
                "regions": 0,
                "profiled_at_key_slice": 0,
                "profiled_at_other_slice": 0,
                "unprofiled": {},
            },
        )
        read_slices: dict[str, set[int]] = {}
        for plane in choices:
            counts["regions"] += 1
            series_uid = plane.get("series_uid")
            slice_index = plane.get("slice")
            series = (
                series_by_uid.get(series_uid) if isinstance(series_uid, str) else None
            )
            territory = None
            choice: dict[str, Any] | None = None
            if series is None:
                reason = "series_unavailable"
            elif type(slice_index) is not int:
                reason = "slice_index_invalid"
            elif getattr(series.get("stack"), "code", None) != "present":
                reason = "squint_unavailable"
            elif leg_summary[series_uid]["code"] != "valid":
                reason = leg_summary[series_uid]["code"]
            else:
                territory, reason, choice = _teacher_territory(
                    writer,
                    study_uid,
                    series,
                    subject,
                    slice_index,
                    leg_maps[series_uid],
                    support_ownership,
                    source_roots,
                    artifact_arrays,
                    verified_arrays,
                    already_read=frozenset(read_slices.get(series_uid, ())),
                )
            geometry = None
            if territory is not None and choice is not None:
                bbox = _native_support_bbox(territory["native_support"])
                geometry = (
                    None
                    if bbox is None
                    else _geometry_window(
                        series,
                        point if isinstance(point, list) else None,
                        choice["used_slice"],
                        bbox,
                    )
                )
                if geometry is None:
                    reason = "support_outside_squint_grid"
            if territory is None or geometry is None or choice is None:
                unprofiled_by_subject.setdefault(subject, []).append(
                    _unprofiled_region(plane, series, reason, choice)
                )
                counts["unprofiled"][reason] = counts["unprofiled"].get(reason, 0) + 1
                continue
            used_slice = choice["used_slice"]
            read_slices.setdefault(series_uid, set()).add(used_slice)
            counts[
                "profiled_at_key_slice"
                if used_slice == slice_index
                else "profiled_at_other_slice"
            ] += 1
            leg_map = leg_maps[series_uid]
            _, region = geometry
            calibration = calibrations.get(series_uid)
            if calibration is None:
                calibration = writer["leg_calibration"](series, leg_map)
                calibrations[series_uid] = calibration
            coarse = _require_territory_profile(
                writer["profile_territory"](
                    series, territory, leg_map, subject=subject, calibration=calibration
                ),
                subject,
            )
            try:
                fine = writer["refine_territory"](
                    series,
                    territory,
                    leg_map,
                    subject=subject,
                    tile_mm=_TERRITORY_FINE_TILE_MM,
                )
            except ValueError as error:
                # A finer reading the native geometry refuses leaves the coarse
                # reading standing; the refusal keeps its own named code.
                combined = coarse
                region["fine_refinement"] = f"refused:{error}"
            else:
                combined = _require_territory_profile(
                    writer["merge_profiles"](
                        (coarse, _require_territory_profile(fine, subject)),
                        subject=subject,
                    ),
                    subject,
                )
                region["fine_refinement"] = "measured_or_silent"
            profiles_by_subject.setdefault(subject, []).append(combined)
            region.update(
                {
                    "orientation": plane.get("orientation_name"),
                    "view": series.get("view"),
                    "series_uid": series_uid,
                    # The slice the territory was read on; the key slice is
                    # kept beside it with the reason any other slice was used.
                    "source_slice": used_slice,
                    "key_slice": slice_index,
                    "slice_choice": choice,
                    "support_source": plane.get("selection_source"),
                    "support_code": plane.get("outcome"),
                    "extent_source": "retained_object_support",
                    "writer": WRITER_TERRITORY,
                    "profile_procedure": TERRITORY_PROCEDURE,
                    "territory": _territory_address(territory),
                }
            )
            regions_by_subject.setdefault(subject, []).append(region)
    merged: dict[str, dict] = {}
    for subject, profiles in profiles_by_subject.items():
        merged[subject] = _require_territory_profile(
            writer["merge_profiles"](profiles, subject=subject), subject
        )
    reasons: dict[str, int] = {}
    for rows in unprofiled_by_subject.values():
        for row in rows:
            reasons[row["reason"]] = reasons.get(row["reason"], 0) + 1
    receipt = {
        "leg_maps": leg_summary,
        "leg_calibrated_series": sorted(calibrations),
        "profiled_regions": sum(len(rows) for rows in regions_by_subject.values()),
        "unprofiled_regions": dict(sorted(reasons.items())),
        "subjects": subject_counts,
    }
    return merged, regions_by_subject, unprofiled_by_subject, receipt


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
    writer: str = WRITER_V1,
    leg_maps: Callable[[dict[str, Any]], Mapping[str, Any]] | None = None,
) -> dict:
    """Build individual squint cases from existing H5 products and train.csv.

    ``writer`` chooses how each case region's cheap profile is read (see
    ``BOOTSTRAP_WRITERS``). Under ``territory-v2`` the leg-map producer is the
    explicit ``leg_maps`` input (default ``squint_leg.leg_maps``), and a region
    whose support does not resolve keeps its named reason, in the case's
    ``unprofiled_regions`` or, for an object left with no reading at all, in
    the memory's ``territory_writer`` receipt; it is never given a box. Full
    payloads, label calls and their scopes are the same under both writers.
    """
    from knee.diagnosis.squint_configurations import with_configuration_cases
    from knee.diagnosis.squint_interfaces import TERRITORY_PROCEDURE
    from knee.diagnosis.squint_profiles import read_study_squints

    root, products, out = Path(root), Path(products), Path(out)
    if type(io_workers) is not int or io_workers < 1:
        raise SquintMemoryError("io_workers_invalid")
    if writer not in BOOTSTRAP_WRITERS:
        raise SquintMemoryError("bootstrap_writer_unknown")
    if writer == WRITER_V1 and leg_maps is not None:
        raise SquintMemoryError("bootstrap_leg_maps_require_territory_writer")
    territory_writer = (
        _territory_writer(leg_maps) if writer == WRITER_TERRITORY else None
    )
    revision = _V1_REVISION if territory_writer is None else TERRITORY_REVISION
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
    territory_studies: dict[str, dict[str, Any]] = {}
    case_subjects = frozenset(_question_object_roles())
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
            unprofiled_by_subject: dict[str, list[dict]] = {}
            if territory_writer is None:
                cheap_by_subject, regions_by_subject = _profile_regions(
                    squint_study,
                    raw_objects,
                    series_by_uid,
                    ownership if isinstance(ownership, dict) else {},
                    roots if isinstance(roots, dict) else {},
                    contexts if isinstance(contexts, dict) else {},
                    product.arrays,
                )
            else:
                (
                    cheap_by_subject,
                    regions_by_subject,
                    unprofiled_by_subject,
                    territory_studies[uid],
                ) = _territory_profile_regions(
                    squint_study,
                    raw_objects,
                    series_by_uid,
                    ownership if isinstance(ownership, dict) else {},
                    roots if isinstance(roots, dict) else {},
                    contexts if isinstance(contexts, dict) else {},
                    product.arrays,
                    subjects=case_subjects,
                    writer=territory_writer,
                )
        label_ledger[uid] = dict(labels[uid])
        question_roles = _question_object_roles()
        for subject, full_record in full_records.items():
            roles = question_roles.get(subject)
            if roles is None:
                continue
            cheap = cheap_by_subject.get(subject)
            if cheap is None:
                if territory_writer is not None:
                    rows = unprofiled_by_subject.get(subject, [])
                    territory_studies[uid].setdefault("unprofiled_subjects", {})[
                        subject
                    ] = {
                        "reason": "no_region_profiled" if rows else "no_region_choice",
                        "regions": rows,
                    }
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
            case = {
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
                    "reference_set_identity": full_record.get("reference_set_identity"),
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
                    "revision": revision,
                },
            }
            if territory_writer is not None:
                case["unprofiled_regions"] = unprofiled_by_subject.get(subject, [])
                try:
                    _json_sha256(
                        [case["profile"], case["regions"], case["unprofiled_regions"]]
                    )
                except (TypeError, ValueError) as error:
                    raise SquintMemoryError("territory_case_not_json") from error
            cases.append(case)
        del (
            squint_study,
            series_by_uid,
            cheap_by_subject,
            regions_by_subject,
            unprofiled_by_subject,
            full_records,
        )
    memory = {
        "schema": SCHEMA,
        "revision": revision,
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
    if territory_writer is not None:
        memory["procedure"].update(
            {
                "writer": WRITER_TERRITORY,
                "profile_procedure": TERRITORY_PROCEDURE,
                "fine_tile_mm": _TERRITORY_FINE_TILE_MM,
            }
        )
        memory["territory_writer"] = _territory_receipt(territory_studies, cases)
    memory["revision"] = f"{memory['revision']}+{FULL_PROFILE_REVISION}"
    if territory_writer is None:
        memory = with_configuration_cases(memory)
    else:
        memory = territory_writer["with_configuration_cases"](
            memory, procedure=TERRITORY_PROCEDURE
        )
        _require_one_writer(memory, TERRITORY_PROCEDURE)
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
    result = {
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
    if territory_writer is not None:
        result.update(
            {
                "writer": WRITER_TERRITORY,
                "profile_procedure": TERRITORY_PROCEDURE,
                "territory_counts": memory["territory_writer"]["counts"],
            }
        )
    return result


def _territory_receipt(
    studies: dict[str, dict[str, Any]], cases: list[dict[str, Any]]
) -> dict[str, Any]:
    """The territory writer's receipt: per study, and counted over the memory."""
    from knee.diagnosis.squint_interfaces import TERRITORY_PROCEDURE

    unprofiled: dict[str, int] = {}
    by_subject: dict[str, dict[str, Any]] = {}
    for study in studies.values():
        for reason, count in study["unprofiled_regions"].items():
            unprofiled[reason] = unprofiled.get(reason, 0) + count
        for subject, counts in study["subjects"].items():
            total = by_subject.setdefault(
                subject,
                {
                    "objects_with_regions": 0,
                    "objects_kept": 0,
                    "regions": 0,
                    "profiled_at_key_slice": 0,
                    "profiled_at_other_slice": 0,
                    "unprofiled": {},
                },
            )
            total["objects_with_regions"] += int(counts["regions"] > 0)
            for key in ("regions", "profiled_at_key_slice", "profiled_at_other_slice"):
                total[key] += counts[key]
            for reason, count in counts["unprofiled"].items():
                total["unprofiled"][reason] = total["unprofiled"].get(reason, 0) + count
    for case in cases:
        if case["subject"] in by_subject:
            by_subject[case["subject"]]["objects_kept"] += 1
    return {
        "schema": _TERRITORY_RECEIPT_SCHEMA,
        "writer": WRITER_TERRITORY,
        "profile_procedure": TERRITORY_PROCEDURE,
        "fine_tile_mm": _TERRITORY_FINE_TILE_MM,
        "studies": studies,
        "counts": {
            "studies": len(studies),
            "object_cases": len(cases),
            "profiled_regions": sum(
                study["profiled_regions"] for study in studies.values()
            ),
            "unprofiled_regions": dict(sorted(unprofiled.items())),
            "objects_without_reading": sum(
                len(study.get("unprofiled_subjects", {})) for study in studies.values()
            ),
            "by_subject": dict(sorted(by_subject.items())),
        },
    }


def _require_one_writer(memory: dict[str, Any], procedure: str) -> None:
    """Refuse a memory whose case profiles were not all written by one writer."""
    for case in memory.get("cases", []):
        profile = case.get("profile") if isinstance(case, dict) else None
        source = profile.get("source") if isinstance(profile, dict) else None
        if not isinstance(source, dict) or source.get("procedure") != procedure:
            raise SquintMemoryError("memory_writer_procedure_mixed")


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
