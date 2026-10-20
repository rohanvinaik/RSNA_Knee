"""Retain exact array members that back the study's anatomical object table.

This module prepares dependencies from already-retained observations and copies them only
when the encoder has opened their source archive. It does not open archives or reinterpret
packed, trace, or coarse addresses.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from knee.receipt import digest


class ObjectSourceError(ValueError):
    """A named refusal to publish an object source dependency."""

    def __init__(self, code: str, detail: str | None = None):
        self.code = code
        self.detail = detail
        super().__init__(code if detail is None else f"{code}: {detail}")


@dataclass(frozen=True, slots=True)
class _Candidate:
    record: Mapping[str, Any]
    root: Path
    root_name: str
    artifact: str | None
    resolved: Path | None


@dataclass(frozen=True, slots=True)
class _Dependency:
    object_name: str
    observation_index: int | None
    role: str
    artifact: str
    resolved_path: Path
    member: str
    expected_digest: str
    source_address: Mapping[str, Any]


class ObjectSourcePlan:
    """Dependencies and object metadata to materialize during an existing open pass."""

    def __init__(
        self,
        *,
        archive_path: Path,
        object_table: dict[str, dict[str, Any]],
        dependencies: Sequence[_Dependency],
    ) -> None:
        self.archive_path = archive_path.resolve()
        self.artifacts = tuple(
            sorted({item.resolved_path for item in dependencies}, key=str)
        )
        self._objects = object_table
        self._dependencies = tuple(dependencies)
        self._by_path: dict[Path, list[_Dependency]] = {}
        for dep in self._dependencies:
            self._by_path.setdefault(dep.resolved_path, []).append(dep)
        self._materialized: dict[tuple[str, str, str], dict[str, Any]] = {}
        self._emitted_by_source: dict[tuple[str, str, str], str] = {}
        self._emitted_keys: set[str] = set()
        self._seen_artifacts: set[Path] = set()
        self._finished = False

    def retain_artifact(
        self,
        path: str | Path,
        archive_mapping: Mapping[str, Any],
        verified_arrays: MutableMapping[tuple[str, str], np.ndarray],
        emitted_arrays: MutableMapping[str, np.ndarray],
    ) -> None:
        """Copy planned members from an archive already opened by the encoder."""
        if self._finished:
            raise ObjectSourceError("plan_already_finished")
        try:
            resolved = Path(path).resolve()
        except (TypeError, OSError, ValueError) as error:
            raise ObjectSourceError(
                "invalid_opened_artifact_path", str(error)
            ) from error
        dependencies = self._by_path.get(resolved)
        if not dependencies:
            return
        self._seen_artifacts.add(resolved)
        for dep in dependencies:
            source_key = (str(dep.resolved_path), dep.member, dep.expected_digest)
            if source_key in self._materialized:
                continue
            cached = verified_arrays.get((dep.member, dep.expected_digest))
            if cached is not None:
                array = cached
            else:
                try:
                    array = archive_mapping[dep.member]
                except (KeyError, OSError, ValueError, TypeError) as error:
                    raise ObjectSourceError(
                        "source_member_unavailable", f"{dep.artifact}:{dep.member}"
                    ) from error
            if not isinstance(array, np.ndarray):
                raise ObjectSourceError(
                    "source_member_not_ndarray", f"{dep.artifact}:{dep.member}"
                )
            if array.dtype.hasobject:
                raise ObjectSourceError(
                    "object_dtype_source_refused", f"{dep.artifact}:{dep.member}"
                )
            if cached is not None:
                # The shared encoder cache only contains values after its source digest check.
                actual_digest = dep.expected_digest
            else:
                actual_digest = digest(array)
                if actual_digest != dep.expected_digest:
                    raise ObjectSourceError(
                        "source_member_digest_mismatch",
                        f"{dep.artifact}:{dep.member}",
                    )
                verified_arrays[(dep.member, dep.expected_digest)] = array
            emitted_key = self._emitted_by_source.get(source_key)
            if emitted_key is None:
                emitted_key = self._next_key()
                if emitted_key in emitted_arrays:
                    raise ObjectSourceError("emitted_key_collision", emitted_key)
                emitted_arrays[emitted_key] = array
                self._emitted_by_source[source_key] = emitted_key
                self._emitted_keys.add(emitted_key)
            ref = {
                "archive": str(self.archive_path),
                "name": emitted_key,
                "digest": actual_digest,
                "dtype": array.dtype.str,
                "shape": list(array.shape),
            }
            self._materialized[source_key] = {
                "active": ref,
                "source": {
                    "artifact": dep.artifact,
                    "member": dep.member,
                    "digest": dep.expected_digest,
                    "root_name": dep.source_address.get("root_name"),
                    "owner_series_uid": dep.source_address.get("owner_series_uid"),
                },
            }

    def _next_key(self) -> str:
        index = len(self._emitted_keys)
        while f"object_source_{index:06d}" in self._emitted_keys:
            index += 1
        return f"object_source_{index:06d}"

    def finish(self) -> dict[str, Any]:
        if self._finished:
            raise ObjectSourceError("plan_already_finished")
        missing_artifacts = set(self.artifacts) - self._seen_artifacts
        if missing_artifacts:
            raise ObjectSourceError(
                "planned_artifact_not_opened",
                ", ".join(str(path) for path in sorted(missing_artifacts, key=str)),
            )
        missing_dependencies = [
            dep
            for dep in self._dependencies
            if (str(dep.resolved_path), dep.member, dep.expected_digest)
            not in self._materialized
        ]
        if missing_dependencies:
            first = missing_dependencies[0]
            raise ObjectSourceError(
                "planned_member_not_materialized",
                f"{first.artifact}:{first.member}",
            )

        for entry in self._objects.values():
            observation_rows = entry.pop("_pending_observations", [])
            finished_rows: list[dict[str, Any]] = []
            for row in observation_rows:
                support_source = row.pop("_support_source", None)
                companion_sources = row.pop("_companion_sources", [])
                if support_source is not None:
                    source_key = tuple(support_source["key"])
                    materialized = self._materialized[source_key]
                    row["support"] = {
                        **materialized,
                        "role": "observation_support",
                    }
                else:
                    row["support"] = None
                companions = []
                for companion in companion_sources:
                    source_key = tuple(companion["key"])
                    materialized = self._materialized[source_key]
                    companions.append(
                        {
                            "role": companion["role"],
                            **materialized,
                        }
                    )
                row["companions"] = companions
                finished_rows.append(row)
            entry["observations"] = finished_rows
            field_rows = entry.pop("_pending_associated_fields", [])
            finished_fields = []
            for field in field_rows:
                source_key = tuple(field["key"])
                materialized = self._materialized[source_key]
                finished_fields.append({"path": field["path"], **materialized})
            entry["associated_field_references"] = finished_fields
            statuses = {row["source_status"] for row in finished_rows}
            if (
                any(row["support"] is not None for row in finished_rows)
                or finished_fields
            ):
                entry["status"] = "source_arrays_retained"
            elif "unresolved_only" in statuses:
                entry["status"] = "unresolved_only"
            elif "target_only" in statuses:
                entry["status"] = "target_only"
            elif finished_rows:
                entry["status"] = "observations_without_array_support"
            elif entry.get("unresolved"):
                entry["status"] = "unresolved_only"
            else:
                entry["status"] = "no_observation_record"
        self._finished = True
        return {
            "schema": "knee-object-sources/v1",
            "status": "complete",
            "archive": str(self.archive_path),
            "objects": self._objects,
            "array_count": len(self._emitted_keys),
        }


def prepare_object_sources(
    result: Mapping[str, Any],
    candidates: Sequence[tuple[Mapping[str, Any], Path, str]],
    archive_path: str | Path,
) -> ObjectSourcePlan:
    """Prepare exact source dependencies without opening any source archive."""
    if not isinstance(result, Mapping):
        raise ObjectSourceError("malformed_study_result")
    study_uid = result.get("study_uid")
    if not isinstance(study_uid, str) or not study_uid:
        raise ObjectSourceError("study_uid_unavailable")
    object_summaries = result.get("objects")
    if not isinstance(object_summaries, Mapping):
        raise ObjectSourceError("object_catalogue_unavailable")
    if not isinstance(candidates, Sequence) or isinstance(candidates, (str, bytes)):
        raise ObjectSourceError("candidate_records_malformed")
    archive = Path(archive_path)
    if not archive.is_absolute():
        raise ObjectSourceError("final_archive_path_must_be_absolute")

    normalized: list[_Candidate] = []
    for item in candidates:
        if not isinstance(item, tuple) or len(item) != 3:
            raise ObjectSourceError("candidate_record_malformed")
        record, root, root_name = item
        if not isinstance(record, Mapping) or not isinstance(root_name, str):
            raise ObjectSourceError("candidate_record_malformed")
        root_path = Path(root).resolve()
        artifact = record.get("artifact")
        if not isinstance(artifact, str) or not artifact:
            normalized.append(_Candidate(record, root_path, root_name, None, None))
            continue
        resolved = _resolve_artifact(root_path, artifact)
        if resolved is None:
            normalized.append(_Candidate(record, root_path, root_name, artifact, None))
        else:
            normalized.append(
                _Candidate(record, root_path, root_name, artifact, resolved)
            )

    table: dict[str, dict[str, Any]] = {}
    for name, summary in object_summaries.items():
        if not isinstance(name, str) or not name or not isinstance(summary, Mapping):
            raise ObjectSourceError("object_catalogue_entry_malformed")
        table[name] = {
            "summary": _json_copy(summary),
            "summary_role": "original_object_summary_provenance",
            "unresolved": [],
            "_pending_observations": [],
            "_pending_associated_fields": [],
        }

    dependencies: list[_Dependency] = []
    seen_dependencies: set[tuple[str, str, str]] = set()
    for candidate in normalized:
        record = candidate.record
        if record.get("study_uid") != study_uid:
            continue
        observations = record.get("observations", [])
        if not isinstance(observations, list):
            raise ObjectSourceError("record_observations_malformed")
        for observation_index, observation in enumerate(observations):
            if not isinstance(observation, Mapping):
                raise ObjectSourceError("observation_row_malformed")
            object_name = observation.get("object")
            if not isinstance(object_name, str) or not object_name:
                raise ObjectSourceError("observation_object_name_malformed")
            if object_name not in table:
                raise ObjectSourceError(
                    "observation_object_not_catalogued", str(object_name)
                )
            carrying_address = _source_address(candidate, observation)
            row: dict[str, Any] = {
                "observation": _json_copy(observation),
                "observation_role": "original_source_observation_provenance",
                "carrying_record_address": carrying_address,
                "source_address": carrying_address,
                "source_status": "no_array_support",
            }
            support = observation.get("support")
            artifact = observation.get("artifact") or candidate.artifact
            if support is not None and support != "" and not isinstance(support, str):
                raise ObjectSourceError("observation_support_malformed", object_name)
            if support is None or support == "":
                if (
                    observation.get("kind") == "target"
                    or observation.get("provenance") == "projected"
                ):
                    row["source_status"] = "target_only"
                table[object_name]["_pending_observations"].append(row)
                continue
            if not isinstance(artifact, str) or not artifact:
                raise ObjectSourceError("observation_artifact_unavailable", object_name)
            owner = _unique_owner(normalized, study_uid, artifact)
            if owner is None:
                raise ObjectSourceError(
                    "source_owner_record_missing", f"{artifact}:{support}"
                )
            source_address = _source_address(owner, observation)
            row["source_address"] = source_address
            expected = _record_digest(owner.record, support)
            if expected is None:
                raise ObjectSourceError(
                    "support_digest_unavailable", f"{artifact}:{support}"
                )
            support_dep = _dependency(
                object_name,
                observation_index,
                "observation_support",
                owner,
                support,
                expected,
                source_address,
            )
            _add_dependency(support_dep, dependencies, seen_dependencies)
            row["_support_source"] = {
                "key": _dep_key(support_dep),
            }
            row["source_status"] = (
                "projected_target_support_retained"
                if observation.get("kind") == "target"
                or observation.get("provenance") == "projected"
                else "support_retained"
            )
            companion_rows = []
            for member, role in _declared_companions(owner.record, observation):
                companion_digest = _record_digest(owner.record, member)
                if companion_digest is None:
                    raise ObjectSourceError(
                        "declared_companion_digest_unavailable",
                        f"{artifact}:{member}:{role}",
                    )
                companion_dep = _dependency(
                    object_name,
                    observation_index,
                    role,
                    owner,
                    member,
                    companion_digest,
                    source_address,
                )
                _add_dependency(companion_dep, dependencies, seen_dependencies)
                companion_rows.append({"role": role, "key": _dep_key(companion_dep)})
            row["_companion_sources"] = companion_rows
            table[object_name]["_pending_observations"].append(row)

    # Marrow and any future associated source references are represented as explicit existing
    # artifact/member/digest triples. Only these named references are traversed.
    for object_name, summary in object_summaries.items():
        associated = (
            summary.get("associated_fields") if isinstance(summary, Mapping) else None
        )
        for ref_path, reference in _associated_references(associated):
            artifact = reference.get("artifact")
            member = reference.get("name", reference.get("member"))
            expected = reference.get("digest")
            if (
                not isinstance(artifact, str)
                or not isinstance(member, str)
                or not isinstance(expected, str)
            ):
                raise ObjectSourceError(
                    "associated_field_reference_malformed", f"{object_name}:{ref_path}"
                )
            owner = _unique_owner(normalized, study_uid, artifact)
            if owner is None:
                raise ObjectSourceError(
                    "associated_source_owner_record_missing", f"{artifact}:{member}"
                )
            record_digest = _record_digest(owner.record, member)
            if record_digest is None or record_digest != expected:
                raise ObjectSourceError(
                    "associated_source_digest_mismatch", f"{artifact}:{member}"
                )
            dep = _dependency(
                object_name,
                None,
                f"associated_field:{ref_path}",
                owner,
                member,
                expected,
                _source_address(owner, {}),
            )
            _add_dependency(dep, dependencies, seen_dependencies)
            table[object_name]["_pending_associated_fields"].append(
                {"path": ref_path, "key": _dep_key(dep)}
            )

    # Preserve full unresolved records separately from their compact object-summary counts.
    for candidate in normalized:
        record = candidate.record
        if record.get("study_uid") != study_uid:
            continue
        unresolved = record.get("observations_unresolved", [])
        if not isinstance(unresolved, list):
            raise ObjectSourceError("record_unresolved_rows_malformed")
        for row in unresolved:
            if not isinstance(row, Mapping):
                raise ObjectSourceError("unresolved_row_malformed")
            object_name = row.get("object")
            if not isinstance(object_name, str) or not object_name:
                raise ObjectSourceError("unresolved_object_name_malformed")
            if object_name not in table:
                raise ObjectSourceError("unresolved_object_not_catalogued", object_name)
            table[object_name]["unresolved"].append(_json_copy(row))

    return ObjectSourcePlan(
        archive_path=archive,
        object_table=table,
        dependencies=dependencies,
    )


def _resolve_artifact(root: Path, artifact: str) -> Path | None:
    candidate = Path(artifact)
    resolved = (
        candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    )
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None
    return resolved


def _unique_owner(
    candidates: Sequence[_Candidate], study_uid: str, artifact: str
) -> _Candidate | None:
    owners = [
        item
        for item in candidates
        if item.record.get("study_uid") == study_uid and item.artifact == artifact
    ]
    if len(owners) != 1:
        if not owners:
            return None
        raise ObjectSourceError("source_owner_record_ambiguous", artifact)
    owner = owners[0]
    if owner.resolved is None:
        raise ObjectSourceError("source_artifact_path_invalid", artifact)
    return owner


def _record_digest(record: Mapping[str, Any], member: str) -> str | None:
    arrays = record.get("arrays")
    if not isinstance(arrays, Mapping):
        return None
    descriptor = arrays.get(member)
    if not isinstance(descriptor, Mapping):
        return None
    value = descriptor.get("digest")
    return value if isinstance(value, str) and value else None


def _source_address(
    owner: _Candidate, observation: Mapping[str, Any]
) -> dict[str, Any]:
    return _json_copy(
        {
            "root_name": owner.root_name,
            "owner_artifact": owner.artifact,
            "owner_series_uid": owner.record.get("series_uid"),
            "owner_view": _json_copy(owner.record.get("view")),
            "owner_slice_index": owner.record.get("slice_index"),
            "target_series_uid": observation.get("series_uid"),
            "observation_artifact": observation.get("artifact"),
            "target_view": _json_copy(observation.get("view")),
            "target_slices": _json_copy(observation.get("slices")),
            "row": observation.get("row"),
            "label": observation.get("label"),
            "support_address_kind": observation.get("support_address_kind"),
            "address_frame": _json_copy(observation.get("address_frame")),
        }
    )


def _dependency(
    object_name: str,
    observation_index: int | None,
    role: str,
    owner: _Candidate,
    member: str,
    expected_digest: str,
    address: Mapping[str, Any],
) -> _Dependency:
    if owner.resolved is None or owner.artifact is None:
        raise ObjectSourceError("source_artifact_path_invalid", str(owner.artifact))
    return _Dependency(
        object_name=object_name,
        observation_index=observation_index,
        role=role,
        artifact=owner.artifact,
        resolved_path=owner.resolved,
        member=member,
        expected_digest=expected_digest,
        source_address=dict(address),
    )


def _dep_key(dep: _Dependency) -> tuple[str, str, str]:
    return (str(dep.resolved_path), dep.member, dep.expected_digest)


def _add_dependency(
    dep: _Dependency,
    dependencies: list[_Dependency],
    seen: set[tuple[str, str, str]],
) -> None:
    key = _dep_key(dep)
    if key not in seen:
        dependencies.append(dep)
        seen.add(key)


def _declared_companions(
    record: Mapping[str, Any], observation: Mapping[str, Any]
) -> tuple[tuple[str, str], ...]:
    """Return only companion arrays declared by the existing source-family layouts."""
    support = observation.get("support")
    if not isinstance(support, str):
        return ()
    companions: list[tuple[str, str]] = []
    if support == "a3_fibula_axial_region":
        names = (
            "a3_fibula_axial_offsets",
            "a3_fibula_axial_shapes",
            "a3_fibula_axial_slices",
            "a3_fibula_axial_target",
            "a3_fibula_axial_available",
            "a3_fibula_axial_origin_lps",
            "a3_fibula_axial_basis_lps",
            "a3_fibula_axial_normal_lps",
            "a3_fibula_axial_thickness_mm",
        )
        companions.extend((name, "fibula_axial_layout") for name in names)
    elif support.startswith("a3_posterior_trace_") and support.endswith("_points_lps"):
        prefix = support[: -len("_points_lps")]
        names = tuple(
            f"{prefix}_{suffix}"
            for suffix in ("offsets", "slices", "starts", "stops", "light", "flank")
        )
        companions.extend((name, "posterior_trace_layout") for name in names)
    elif support.startswith("a3_") and support.endswith("_profile_area_mm2"):
        status = support[: -len("area_mm2")] + "status"
        companions.append((status, "native_slice_profile_status"))
    elif support == "a4_joint_axial_profile_white":
        names = (
            "a4_joint_axial_profile_offsets",
            "a4_joint_axial_profile_slices",
            "a4_joint_axial_profile_rc",
            "a4_joint_axial_profile_valid",
            "a4_joint_axial_profile_light",
        )
        companions.extend((name, "joint_axial_profile_layout") for name in names)
    else:
        coarse = _coarse_companions(record, support)
        if "coarse_" in support and not coarse:
            raise ObjectSourceError("unsupported_coarse_support_layout", support)
        companions.extend(coarse)
    return tuple(companions)


def _coarse_companions(
    record: Mapping[str, Any], support: str
) -> list[tuple[str, str]]:
    layouts: list[tuple[str, tuple[str, ...]]] = []
    if support.startswith("a4_axial_coarse_"):
        suffix = support.removeprefix("a4_axial_coarse_")
        prefix = "a4_axial_coarse_"
        if suffix in {"femur_body", "femur_seeds", "tibia_body", "tibia_seeds"}:
            bone = suffix.split("_")[0]
            family = ("median", "depth", f"{bone}_body", f"{bone}_seeds")
        elif suffix in {"femur_estimate_body", "tibia_estimate_body"}:
            bone = suffix.split("_")[0]
            family = ("median", "depth", f"{bone}_estimate_body")
        else:
            return []
        layouts.append((prefix, family))
    elif support.startswith("a4_patella_coarse_"):
        suffix = support.removeprefix("a4_patella_coarse_")
        if suffix not in {"patella_body", "patella_seeds"}:
            return []
        layouts.append(
            ("a4_patella_coarse_", ("median", "depth", "patella_body", "patella_seeds"))
        )
    else:
        key_planes = record.get("fibula_key_planes")
        if not isinstance(key_planes, Mapping):
            return []
        for item in key_planes.values():
            if not isinstance(item, Mapping):
                continue
            prefix = item.get("arrays_prefix")
            if (
                isinstance(prefix, str)
                and prefix
                and support in {f"{prefix}_fibula_body", f"{prefix}_fibula_seeds"}
            ):
                layouts.append(
                    (
                        f"{prefix}_",
                        ("median", "depth", "fibula_body", "fibula_seeds"),
                    )
                )
                break
    result: list[tuple[str, str]] = []
    for prefix, suffixes in layouts:
        result.extend(
            (f"{prefix}{name}", "native_coarse_block_layout")
            for name in (
                "offsets",
                "shapes",
                "slices",
                "windows_rc",
                "block_px",
                "block_mm",
                *suffixes,
            )
        )
    return result


def _associated_references(value: Any, path: str = "associated_fields"):
    if isinstance(value, Mapping):
        if "artifact" in value and ("name" in value or "member" in value):
            yield path, value
            return
        for key, item in value.items():
            yield from _associated_references(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _associated_references(item, f"{path}[{index}]")


def _json_copy(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_copy(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_copy(item) for item in value]
    if isinstance(value, list):
        return [_json_copy(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        raise ObjectSourceError("array_in_metadata_refused")
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise ObjectSourceError("non_json_metadata_value", type(value).__name__)
