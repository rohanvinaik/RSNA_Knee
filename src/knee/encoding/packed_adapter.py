"""Private adapter candidate for retained packed full-resolution planes.

This layer validates the relationship between an observation and its owning
artifact, verifies the packed source arrays, delegates row decoding to
``knee.encoding.packed_planes``, then hands the resulting native 2-D planes to
the existing place encoder adapter. It does not infer anatomy or select rows.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from knee.encoding.handoff import AddressedEncoding, encode_observation
from knee.encoding.packed_planes import read_packed_plane
from knee.encoding.places import CompiledLayout, NumericReference
from knee.receipt import digest


@dataclass(frozen=True, slots=True)
class PackedSupportLayout:
    """Explicit row-address contract for one packed native-plane family.

    ``packed_arrays`` lists the support and binding arrays sharing offsets and
    shapes. ``frame_arrays`` names row-aligned frame arrays; each mapping key
    is retained in the result without converting coordinates.
    """

    family: str
    owner_series_uid: str
    target_series_uid: str
    target_view: tuple[str, str, str]
    offsets: str
    shapes: str
    slices: str
    packed_arrays: tuple[str, ...]
    target_pixels_array: str
    frame_arrays: Mapping[str, str]
    count_meaning: str


class _PackedSourceError(ValueError):
    pass


def encode_packed_observation(
    record: dict,
    observation: dict,
    arrays: Mapping[str, np.ndarray],
    layout: CompiledLayout,
    bindings: Sequence[dict],
    references: Mapping[tuple[str, str], NumericReference],
    packed: PackedSupportLayout,
    *,
    verified_arrays: dict[tuple[str, str], np.ndarray] | None = None,
) -> AddressedEncoding:
    """Encode one explicitly packed full-resolution observation.

    The fibula's owning artifact may be a different acquisition from the
    observation's target series. That exception is scoped to this declared
    family and is recorded alongside both identities. Every decoded row is
    addressed by the observation row and independently checked against its
    retained slice index.
    """
    metadata = {
        "observation": dict(observation),
        "packed_family": getattr(packed, "family", None),
    }

    def refused(code: str, detail: str = "") -> AddressedEncoding:
        return AddressedEncoding(code, None, None, {**metadata, "detail": detail})

    if not isinstance(packed, PackedSupportLayout):
        return refused("invalid_packed_layout")
    if packed.family != "fibula_axial":
        return refused("unsupported_packed_family")
    if (
        not isinstance(packed.owner_series_uid, str)
        or not packed.owner_series_uid
        or not isinstance(packed.target_series_uid, str)
        or not packed.target_series_uid
        or not isinstance(packed.target_view, tuple)
        or len(packed.target_view) != 3
        or any(not isinstance(part, str) for part in packed.target_view)
    ):
        return refused("invalid_packed_identity")
    if packed.count_meaning != "fibula_axial_target_pixels":
        return refused("invalid_count_meaning")
    if not isinstance(packed.frame_arrays, Mapping) or set(packed.frame_arrays) != {
        "origin_lps",
        "basis_lps",
        "normal_lps",
        "thickness_mm",
    }:
        return refused("invalid_packed_frame_layout")
    if (
        not isinstance(packed.packed_arrays, tuple)
        or len(set(packed.packed_arrays)) != len(packed.packed_arrays)
        or not isinstance(packed.target_pixels_array, str)
        or packed.target_pixels_array not in packed.packed_arrays
    ):
        return refused("invalid_packed_array_layout")
    if (
        observation.get("provenance") != "native"
        or observation.get("kind") != "reading"
        or observation.get("object") != "fibula"
    ):
        return refused("unsupported_observation_kind")
    if observation.get("artifact") != record.get("artifact"):
        return refused("source_artifact_mismatch")
    if record.get("series_uid") != packed.owner_series_uid:
        return refused("invalid_owner_identity")
    study_uid, artifact = record.get("study_uid"), record.get("artifact")
    if (
        not isinstance(study_uid, str)
        or not study_uid
        or artifact
        not in (
            f"{study_uid}/{packed.owner_series_uid}-fibula.npz.xz",
            f"{study_uid}/{packed.owner_series_uid}-fibula.npz",
        )
    ):
        return refused("owner_artifact_identity_mismatch")
    if observation.get("series_uid") != packed.target_series_uid:
        return refused("target_series_mismatch")
    view = observation.get("view")
    if not isinstance(view, (list, tuple)) or tuple(view) != packed.target_view:
        return refused("target_view_mismatch")
    if observation.get("support") not in packed.packed_arrays:
        return refused("support_not_declared_packed")
    row = observation.get("row")
    if not isinstance(row, int) or isinstance(row, bool) or row < 0:
        return refused("invalid_packed_row")
    slices = observation.get("slices")
    if (
        not isinstance(slices, (list, tuple))
        or len(slices) != 1
        or not isinstance(slices[0], int)
        or isinstance(slices[0], bool)
        or slices[0] < 0
    ):
        return refused("plane_address_required")
    owner_uid = record.get("series_uid")
    if not isinstance(owner_uid, str) or not owner_uid:
        return refused("invalid_owner_identity")

    loaded: dict[str, np.ndarray] = {}
    source_refs: dict[str, dict] = {}

    def read(name: object) -> np.ndarray:
        if not isinstance(name, str) or not name:
            raise _PackedSourceError("missing_array_name")
        if name in loaded:
            return loaded[name]
        if name not in arrays:
            raise _PackedSourceError("missing_array:" + name)
        expected = record.get("arrays", {}).get(name, {}).get("digest")
        if not isinstance(expected, str):
            raise _PackedSourceError("missing_digest:" + name)
        cache_key = (name, expected)
        if verified_arrays is not None and cache_key in verified_arrays:
            array = verified_arrays[cache_key]
        else:
            array = arrays[name]
            if digest(array) != expected:
                raise _PackedSourceError("digest_mismatch:" + name)
            if verified_arrays is not None:
                verified_arrays[cache_key] = array
        loaded[name] = array
        source_refs[name] = {
            "artifact": record.get("artifact"),
            "owner_series_uid": owner_uid,
            "digest": expected,
            "shape": list(array.shape),
            "dtype": array.dtype.str,
        }
        return array

    try:
        offsets, shapes, row_slices = (
            read(packed.offsets),
            read(packed.shapes),
            read(packed.slices),
        )
        if (
            offsets.ndim != 1
            or shapes.ndim != 2
            or shapes.shape[1:] != (2,)
            or row_slices.ndim != 1
            or row >= len(row_slices)
            or len(offsets) != len(row_slices) + 1
            or len(shapes) != len(row_slices)
        ):
            return refused("packed_address_shape_mismatch")
        if row_slices.dtype.kind not in "iu" or shapes.dtype.kind not in "iu":
            return refused("packed_address_dtype_mismatch")
        if int(row_slices[row]) != slices[0]:
            return refused("packed_slice_mismatch")
        evidence_rows = record.get("axial_evidence")
        if not isinstance(evidence_rows, list):
            return refused("packed_evidence_missing")
        matches = [
            item
            for item in evidence_rows
            if isinstance(item, dict)
            and isinstance(item.get("row"), int)
            and not isinstance(item.get("row"), bool)
            and item.get("row") == row
        ]
        if len(matches) != 1:
            return refused("packed_evidence_missing")
        evidence = matches[0]
        if not isinstance(evidence, dict):
            return refused("packed_evidence_malformed")
        evidence_view = evidence.get("view")
        if (
            evidence.get("series_uid") != packed.target_series_uid
            or not isinstance(evidence_view, (list, tuple))
            or tuple(evidence_view) != packed.target_view
            or not isinstance(evidence.get("slice"), int)
            or isinstance(evidence.get("slice"), bool)
            or evidence.get("slice") != slices[0]
            or evidence.get("code") != observation.get("code")
        ):
            return refused("packed_evidence_mismatch")
        target_pixels = evidence.get("target_pixels")
        region_pixels = evidence.get("region_pixels")
        if any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0
            for value in (target_pixels, region_pixels)
        ):
            return refused("packed_evidence_count_malformed")
        declared_count = observation.get("count")
        if (
            not isinstance(declared_count, int)
            or isinstance(declared_count, bool)
            or declared_count < 0
            or declared_count != target_pixels
        ):
            return refused("target_count_mismatch")
        frame: dict[str, object] = {}
        for key, name in packed.frame_arrays.items():
            frame_array = read(name)
            expected_tail = {
                "origin_lps": (3,),
                "basis_lps": (3, 2),
                "normal_lps": (3,),
                "thickness_mm": (),
            }.get(key)
            if (
                expected_tail is None
                or frame_array.shape != (len(row_slices), *expected_tail)
                or frame_array.dtype.kind not in "iuf"
                or not np.isfinite(frame_array[row]).all()
            ):
                return refused("packed_frame_shape_mismatch", key)
            frame[key] = frame_array[row].tolist()

        row_arrays: dict[str, np.ndarray] = {}
        for name in packed.packed_arrays:
            flat = read(name)
            result = read_packed_plane(flat, offsets, shapes, row)
            if result.code != "ok" or result.row != row or result.plane is None:
                return refused("packed_plane_unavailable", str(result.code))
            row_arrays[name] = result.plane

        if packed.target_pixels_array not in row_arrays:
            return refused("target_mask_not_declared_packed")
        target_mask = row_arrays[packed.target_pixels_array]
        if target_mask.dtype.kind != "b":
            return refused("target_mask_dtype_mismatch")
        if int(np.count_nonzero(target_mask)) != target_pixels:
            return refused("target_count_mismatch")

        support_name = observation["support"]
        support = row_arrays[support_name]
        label = observation.get("label")
        if label is None:
            if support.dtype.kind != "b":
                return refused("support_label_required")
            mask = support
        else:
            if not isinstance(label, int) or isinstance(label, bool):
                return refused("invalid_support_label")
            if support.dtype.kind not in "iu":
                return refused("invalid_support_label")
            mask = support == label
        support_count = int(np.count_nonzero(mask))
        if support_count != region_pixels:
            return refused("region_count_mismatch")

        normalized = dict(observation)
        normalized["row"] = None
        normalized["count"] = None
        synthetic_arrays = dict(row_arrays)
        synthetic_entries: dict[str, dict[str, str]] = {}
        derived_cache: dict[tuple[str, str], np.ndarray] = {}
        for name, array in synthetic_arrays.items():
            derived_digest = digest(array)
            synthetic_entries[name] = {"digest": derived_digest}
            derived_cache[name, derived_digest] = array
        for binding in bindings:
            source = binding.get("source", "array")
            if source == "unread":
                if any(
                    field in binding
                    for field in ("value", "available", "window", "path", "scope")
                ):
                    return refused("invalid_unread_binding")
                continue
            if source == "record_context":
                return refused("packed_record_context_unsupported")
            if binding.get("window") is not None:
                return refused("packed_window_adapter_required")
            for field in ("value", "available"):
                name = binding.get(field)
                if name is not None and name not in synthetic_arrays:
                    return refused("binding_array_not_declared_packed", str(name))
        synthetic_record = {
            "artifact": record.get("artifact"),
            "series_uid": packed.target_series_uid,
            "view": packed.target_view,
            "slice_index": slices[0],
            "plane_frame": frame,
            "arrays": synthetic_entries,
        }
        encoded = encode_observation(
            synthetic_record,
            normalized,
            synthetic_arrays,
            layout,
            bindings,
            references,
            verified_arrays=derived_cache,
        )
    except _PackedSourceError as error:
        return refused(str(error).split(":", 1)[0], str(error))
    except (KeyError, TypeError, ValueError, IndexError) as error:
        return refused("invalid_packed_binding", str(error))

    metadata = dict(encoded.metadata)
    metadata.update(
        observation=dict(observation),
        source_refs=source_refs,
        source_artifact=record.get("artifact"),
        source_owner_series_uid=owner_uid,
        target_series_uid=packed.target_series_uid,
        target_view=list(packed.target_view),
        packed_family=packed.family,
        packed_row=row,
        packed_slice_index=slices[0],
        packed_frame=frame,
        declared_count=declared_count,
        declared_count_meaning=packed.count_meaning,
        packed_target_count=int(np.count_nonzero(target_mask)),
        decoded_support_count=support_count,
    )
    for unread_source in metadata.get("unread_sources", []):
        unread_source["source_address"].update(
            owner_artifact=record.get("artifact"),
            owner_series_uid=owner_uid,
            target_series_uid=packed.target_series_uid,
            target_view=list(packed.target_view),
            row=row,
            slice_index=slices[0],
        )
    return AddressedEncoding(
        encoded.status, encoded.encoding, encoded.points_rc, metadata
    )
