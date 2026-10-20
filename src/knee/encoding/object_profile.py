"""Exact assembly of per-place rowcodes into one unified object profile.

This module only assembles rowcodes that were already produced under a common
registry-bound layout.  It performs no address conversion, anatomy
identification, inference, resampling, thresholding, or persistence, and it
never relabels an already encoded CountBundle.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from enum import StrEnum

import numpy as np

from knee.encoding.counts import CountBundle, CountLayout
from knee.encoding.places import (
    CompiledLayout,
    LayoutSpec,
    MetricRows,
    _bound_count_layout,
    compile_layout,
    decode_count_names,
)

__all__ = [
    "PLACE_CONFLICT",
    "PLACE_COUNTED",
    "PLACE_DUPLICATE",
    "PLACE_NOT_ASSEMBLED",
    "PLACE_NO_MEASUREMENT",
    "AddressKind",
    "BankFacet",
    "BatchRecord",
    "ConflictRecord",
    "FacetCoordinate",
    "IssueRecord",
    "ObjectAssemblyResult",
    "ObjectProfile",
    "PlaceAddressBatch",
    "ProfileCode",
    "ProfileLayout",
    "RowcodeBatch",
    "SourceLink",
    "assemble_object_profile",
    "compile_profile_layout",
    "registry_fingerprint",
    "registry_problem",
    "validate_profile_layout",
]

# Compact per-place status codes stored in int8 arrays.
PLACE_NO_MEASUREMENT = 0
PLACE_COUNTED = 1
PLACE_DUPLICATE = 2
PLACE_CONFLICT = 3
PLACE_NOT_ASSEMBLED = 4


class AddressKind(StrEnum):
    NATIVE_RC = "native_rc"
    PATIENT_LPS = "patient_lps"
    COARSE_GRID_RC = "coarse_grid_rc"
    SERIES_SLICE = "series_slice"


class ProfileCode(StrEnum):
    OK = "ok"
    VALID = "valid"
    SILENT = "silent"
    PARTIAL = "partial"
    CONFLICTING = "conflicting"
    MISMATCH = "mismatch"
    MALFORMED = "malformed"
    FACET_MAPPING_CONFLICT = "facet_mapping_conflict"


@dataclass(frozen=True, slots=True)
class FacetCoordinate:
    view_role: str
    lens: str
    scale: str | int
    direction: str | None


@dataclass(frozen=True, slots=True)
class BankFacet:
    bank: str
    coordinate: FacetCoordinate


@dataclass(frozen=True, slots=True)
class SourceLink:
    """Batch-level original lineage; per-place links are (batch, index)."""

    observation: str
    artifact: str
    array_name: str
    index_lineage: str


@dataclass(frozen=True, slots=True, eq=False)
class PlaceAddressBatch:
    kind: str
    frame_identity: str
    coordinates: np.ndarray


@dataclass(frozen=True, slots=True, eq=False)
class RowcodeBatch:
    bank: str
    metric: str
    facet_coordinate: FacetCoordinate
    measurement_source_identity: str
    layout_fingerprint: str
    count_layout: CountLayout
    reference_set_identity: str
    rowcodes: np.ndarray
    addresses: PlaceAddressBatch
    source_link: SourceLink


def _plain_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _nes(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _coordinate_ok(c: object) -> bool:
    if not isinstance(c, FacetCoordinate):
        return False
    if not _nes(c.view_role) or not _nes(c.lens):
        return False
    if not (_nes(c.scale) or _plain_int(c.scale)):
        return False
    return c.direction is None or _nes(c.direction)


def registry_problem(registry: object) -> str | None:
    """Name a registry defect, or None when every bank maps exactly once."""
    if not isinstance(registry, tuple) or not registry:
        return "invalid_registry"
    seen: dict[str, FacetCoordinate] = {}
    for item in registry:
        if (
            not isinstance(item, BankFacet)
            or not _nes(item.bank)
            or not _coordinate_ok(item.coordinate)
        ):
            return "invalid_registry"
        if item.bank in seen:
            if seen[item.bank] != item.coordinate:
                return "facet_mapping_conflict"
            return "duplicate_bank_mapping"
        seen[item.bank] = item.coordinate
    return None


def registry_fingerprint(registry: tuple[BankFacet, ...]) -> str | None:
    """Canonical (bank-sorted) fingerprint of a valid registry."""
    if registry_problem(registry) is not None:
        return None
    rows = [
        {
            "bank": item.bank,
            "view_role": item.coordinate.view_role,
            "lens": item.coordinate.lens,
            "scale": {
                "type": type(item.coordinate.scale).__name__,
                "value": item.coordinate.scale,
            },
            "direction": item.coordinate.direction,
        }
        for item in sorted(registry, key=lambda i: i.bank)
    ]
    text = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _registry_version(declared: str, fingerprint: str) -> str:
    return f"{declared}:facet-registry:{fingerprint}"


@dataclass(frozen=True, slots=True)
class ProfileLayout:
    declared_version: str
    registry: tuple[BankFacet, ...]
    registry_fingerprint: str
    compiled: CompiledLayout
    reference_set_identity: str
    count_layout: CountLayout


def compile_profile_layout(
    spec: LayoutSpec,
    registry: tuple[BankFacet, ...],
    reference_set_identity: str,
) -> ProfileLayout | None:
    """Bind the registry into the actual LayoutSpec version, then compile."""
    if not isinstance(spec, LayoutSpec) or not _nes(spec.version):
        return None
    if not _nes(reference_set_identity):
        return None
    if registry_problem(registry) is not None:
        return None
    if not isinstance(spec.banks, tuple) or not spec.banks:
        return None
    spec_banks = set()
    for bank in spec.banks:
        name = getattr(bank, "name", None)
        if not _nes(name):
            return None
        spec_banks.add(name)
    if spec_banks != {item.bank for item in registry}:
        return None
    fingerprint = registry_fingerprint(registry)
    if fingerprint is None:
        return None
    bound_spec = replace(spec, version=_registry_version(spec.version, fingerprint))
    compiled = compile_layout(bound_spec)
    if compiled is None:
        return None
    canonical = tuple(sorted(registry, key=lambda i: i.bank))
    return ProfileLayout(
        spec.version,
        canonical,
        fingerprint,
        compiled,
        reference_set_identity,
        _bound_count_layout(compiled, reference_set_identity),
    )


def _bind_profile_layout_reference(
    layout: ProfileLayout, reference_set_identity: str
) -> ProfileLayout | None:
    """Reuse a validated immutable bank layout with a new reference identity."""
    if not isinstance(layout, ProfileLayout) or not _nes(reference_set_identity):
        return None
    return replace(
        layout,
        reference_set_identity=reference_set_identity,
        count_layout=_bound_count_layout(layout.compiled, reference_set_identity),
    )


def validate_profile_layout(layout: object) -> bool:
    """Verify the registry/version/fingerprint/CountLayout binding."""
    if not isinstance(layout, ProfileLayout):
        return False
    if not isinstance(layout.compiled, CompiledLayout):
        return False
    if not _nes(layout.declared_version) or not _nes(layout.reference_set_identity):
        return False
    if registry_problem(layout.registry) is not None:
        return False
    fingerprint = registry_fingerprint(layout.registry)
    if fingerprint is None or fingerprint != layout.registry_fingerprint:
        return False
    if layout.compiled.version != _registry_version(
        layout.declared_version, fingerprint
    ):
        return False
    recompiled = compile_layout(
        LayoutSpec(
            layout.compiled.version, layout.compiled.carrier_id, layout.compiled.banks
        )
    )
    if recompiled != layout.compiled:
        return False
    if {b.name for b in layout.compiled.banks} != {i.bank for i in layout.registry}:
        return False
    return layout.count_layout == _bound_count_layout(
        layout.compiled, layout.reference_set_identity
    )


def _validate_prepared_profile_layout(
    layout: object,
    shared_compiled: CompiledLayout,
) -> bool:
    """Check an immutable profile binding against its already compiled layout."""
    if not isinstance(layout, ProfileLayout) or layout.compiled is not shared_compiled:
        return False
    if not _nes(layout.declared_version) or not _nes(layout.reference_set_identity):
        return False
    if registry_problem(layout.registry) is not None:
        return False
    fingerprint = registry_fingerprint(layout.registry)
    if fingerprint is None or fingerprint != layout.registry_fingerprint:
        return False
    if shared_compiled.version != _registry_version(
        layout.declared_version, fingerprint
    ):
        return False
    if {b.name for b in shared_compiled.banks} != {i.bank for i in layout.registry}:
        return False
    return layout.count_layout == _bound_count_layout(
        shared_compiled, layout.reference_set_identity
    )


@dataclass(frozen=True, slots=True)
class IssueRecord:
    batch_ordinal: int
    code: ProfileCode
    fields: tuple[str, ...]
    detail: str
    source_link: SourceLink | None


@dataclass(frozen=True, slots=True, eq=False)
class ConflictRecord:
    """Observed-code conflicts of one event stream; every link is retained."""

    bank: str
    metric: str
    facet_coordinate: FacetCoordinate
    measurement_source_identity: str
    address_kind: str
    frame_identity: str
    event_count: int
    link_batch: np.ndarray
    link_place: np.ndarray
    link_event: np.ndarray
    link_rowcode: np.ndarray


@dataclass(frozen=True, slots=True, eq=False)
class BatchRecord:
    ordinal: int
    status: ProfileCode
    detail: str
    bank: str | None
    metric: str | None
    facet_coordinate: FacetCoordinate | None
    measurement_source_identity: str | None
    source_link: SourceLink | None
    place_count: int
    row_status: np.ndarray
    counted: int
    duplicate: int
    conflict: int
    no_measurement: int


@dataclass(frozen=True, slots=True)
class ObjectProfile:
    """Sparse exact profile: only nonzero (bank, row, count) entries."""

    object_name: str
    count_layout: CountLayout | None
    entries: tuple[tuple[str, int, int], ...]

    def to_count_bundle(self) -> CountBundle | None:
        layout = self.count_layout
        if not isinstance(layout, CountLayout):
            return None
        index = {bank.name: i for i, bank in enumerate(layout.banks)}
        tables = [[0] * bank.row_count for bank in layout.banks]
        for bank, row, count in self.entries:
            if bank not in index or not _plain_int(row) or not _plain_int(count):
                return None
            if count < 0 or not 0 <= row < layout.banks[index[bank]].row_count:
                return None
            tables[index[bank]][row] += count
        return CountBundle(layout, tuple(tuple(t) for t in tables))


@dataclass(frozen=True, slots=True)
class ObjectAssemblyResult:
    object_name: str
    code: ProfileCode
    outcomes: tuple[ProfileCode, ...]
    profile: ObjectProfile
    batches: tuple[BatchRecord, ...]
    conflicts: tuple[ConflictRecord, ...]
    mismatches: tuple[IssueRecord, ...]
    malformed: tuple[IssueRecord, ...]
    profile_layout: ProfileLayout | None

    def to_count_bundle(self) -> CountBundle | None:
        """Explicit exact CountBundle under the common reference-bound layout."""
        return self.profile.to_count_bundle()

    def decoded_names(self):
        bundle = self.to_count_bundle()
        if bundle is None or self.profile_layout is None:
            return None
        return decode_count_names(
            self.profile_layout.compiled,
            bundle,
            self.profile_layout.reference_set_identity,
        )


def _header_problem(b: RowcodeBatch) -> str | None:
    for name in (
        "bank",
        "metric",
        "measurement_source_identity",
        "layout_fingerprint",
        "reference_set_identity",
    ):
        if not _nes(getattr(b, name)):
            return f"invalid_{name}"
    if not _coordinate_ok(b.facet_coordinate):
        return "invalid_facet_coordinate"
    if not isinstance(b.count_layout, CountLayout):
        return "invalid_count_layout"
    link = b.source_link
    if not isinstance(link, SourceLink) or not all(
        _nes(v)
        for v in (link.observation, link.artifact, link.array_name, link.index_lineage)
    ):
        return "invalid_source_link"
    if not isinstance(b.addresses, PlaceAddressBatch):
        return "invalid_addresses"
    return None


def _address_problem(a: PlaceAddressBatch) -> str | None:
    try:
        kind = AddressKind(a.kind)
    except ValueError:
        return "invalid_address_kind"
    if not _nes(a.frame_identity):
        return "invalid_frame_identity"
    c = a.coordinates
    if not isinstance(c, np.ndarray) or c.ndim != 2:
        return "coordinates_must_be_2d_array"
    if kind is not AddressKind.PATIENT_LPS:
        width = 1 if kind is AddressKind.SERIES_SLICE else 2
        if c.shape[1] != width or c.dtype.kind not in "iu":
            return f"{kind.value}_requires_integer_n_by_{width}"
        if c.size:
            if c.dtype.kind == "i" and int(c.min()) < 0:
                return "native_rc_negative"
            if (
                c.dtype.kind == "u"
                and c.dtype.itemsize >= 8
                and int(c.max()) > np.iinfo(np.int64).max
            ):
                return "native_rc_too_large"
    else:
        if c.shape[1] != 3 or c.dtype != np.float64:
            return "patient_lps_requires_float64_n_by_3"
        if not bool(np.all(np.isfinite(c))):
            return "patient_lps_nonfinite"
    return None


def _payload_problem(b: RowcodeBatch, rows: MetricRows) -> str | None:
    rc = b.rowcodes
    if not isinstance(rc, np.ndarray) or rc.ndim != 1 or rc.dtype != np.int16:
        return "rowcodes_must_be_1d_int16"
    problem = _address_problem(b.addresses)
    if problem:
        return problem
    if b.addresses.coordinates.shape[0] != rc.shape[0]:
        return "address_rowcode_length_mismatch"
    if rc.size:
        if int(rc.min()) < -1:
            return "row_code_below_no_measurement"
        observed = rc[rc >= 0]
        if observed.size:
            lo, hi = rows.start, rows.start + len(rows.names)
            if int(observed.min()) < lo or int(observed.max()) >= hi:
                return "row_code_outside_metric_rows"
    return None


def _screen(b, pl, coord_by_bank, rows_by_key):
    if not isinstance(b, RowcodeBatch):
        return ProfileCode.MALFORMED, (), "not_a_rowcode_batch"
    problem = _header_problem(b)
    if problem:
        return ProfileCode.MALFORMED, ("header",), problem
    fields = tuple(
        name
        for name, bad in (
            ("layout_fingerprint", b.layout_fingerprint != pl.compiled.fingerprint),
            ("count_layout", b.count_layout != pl.count_layout),
            (
                "reference_set_identity",
                b.reference_set_identity != pl.reference_set_identity,
            ),
        )
        if bad
    )
    if fields:
        return (
            ProfileCode.MISMATCH,
            fields,
            (
                "identity differs from the profile layout; re-encode retained "
                "per-place rows under the registry-bound layout"
            ),
        )
    expected = coord_by_bank.get(b.bank)
    rows = rows_by_key.get((b.bank, b.metric))
    if expected is None or rows is None:
        return ProfileCode.MALFORMED, ("bank", "metric"), "unknown_bank_or_metric"
    if b.facet_coordinate != expected:
        return (
            ProfileCode.FACET_MAPPING_CONFLICT,
            ("facet_coordinate",),
            "batch facet differs from the registry facet of its bank",
        )
    problem = _payload_problem(b, rows)
    if problem:
        return ProfileCode.MALFORMED, ("payload",), problem
    return None


def _safe_len(b: object) -> int:
    rc = getattr(b, "rowcodes", None)
    return int(rc.shape[0]) if isinstance(rc, np.ndarray) and rc.ndim >= 1 else 0


def _canonical_coordinates(a: PlaceAddressBatch) -> np.ndarray:
    if a.kind != AddressKind.PATIENT_LPS:
        return a.coordinates.astype(np.int64)
    return a.coordinates + 0.0  # folds -0.0 into 0.0; exact otherwise


def _empty_profile_result(name, code, records, issues, layout):
    mism = tuple(i for i in issues if i.code is not ProfileCode.MALFORMED)
    mal = tuple(i for i in issues if i.code is ProfileCode.MALFORMED)
    return ObjectAssemblyResult(
        name if isinstance(name, str) else "",
        code,
        (code,),
        ObjectProfile(
            name if isinstance(name, str) else "",
            layout.count_layout if isinstance(layout, ProfileLayout) else None,
            (),
        ),
        tuple(records),
        (),
        mism,
        mal,
        layout if isinstance(layout, ProfileLayout) else None,
    )


def _assemble_object_profile(
    object_name: str,
    profile_layout: ProfileLayout,
    batches,
    shared_compiled: CompiledLayout | None = None,
) -> ObjectAssemblyResult:
    """Assemble one object's sparse exact profile from rowcode batches."""
    if not isinstance(batches, (list, tuple)):
        return _empty_profile_result(
            object_name, ProfileCode.MALFORMED, (), (), profile_layout
        )
    layout_ok = _nes(object_name) and (
        validate_profile_layout(profile_layout)
        if shared_compiled is None
        else _validate_prepared_profile_layout(profile_layout, shared_compiled)
    )

    n_batches = len(batches)
    status: list[ProfileCode | None] = [None] * n_batches
    detail = [""] * n_batches
    row_status: list[np.ndarray | None] = [None] * n_batches
    issues: list[IssueRecord] = []

    coord_by_bank: dict = {}
    rows_by_key: dict = {}
    if layout_ok:
        coord_by_bank = {i.bank: i.coordinate for i in profile_layout.registry}
        rows_by_key = {
            (r.bank, r.metric): r for r in profile_layout.compiled.metric_rows
        }

    groups: dict[tuple, list[int]] = {}
    for i, b in enumerate(batches):
        if not layout_ok:
            verdict = (
                ProfileCode.MALFORMED,
                ("profile_layout",),
                "profile_layout_or_object_invalid",
            )
        else:
            verdict = _screen(b, profile_layout, coord_by_bank, rows_by_key)
        if verdict is not None:
            code, fields, why = verdict
            status[i], detail[i] = code, why
            row_status[i] = np.full(_safe_len(b), PLACE_NOT_ASSEMBLED, dtype=np.int8)
            issues.append(
                IssueRecord(
                    i,
                    code,
                    fields,
                    why,
                    getattr(b, "source_link", None)
                    if isinstance(getattr(b, "source_link", None), SourceLink)
                    else None,
                )
            )
            continue
        key = (
            b.facet_coordinate,
            b.measurement_source_identity,
            str(AddressKind(b.addresses.kind).value),
            b.addresses.frame_identity,
            b.bank,
            b.metric,
        )
        groups.setdefault(key, []).append(i)

    counts: dict[tuple[str, int], int] = {}
    conflicts: list[ConflictRecord] = []
    for key, idxs in groups.items():
        bank, metric = key[4], key[5]
        lens = np.array([batches[i].rowcodes.shape[0] for i in idxs], dtype=np.int64)
        starts = np.concatenate(([0], np.cumsum(lens)[:-1])).astype(np.int64)
        codes = np.concatenate([batches[i].rowcodes for i in idxs])
        gstat = np.zeros(codes.shape[0], dtype=np.int8)
        obs = np.flatnonzero(codes >= 0)
        if obs.size:
            coords = np.concatenate(
                [_canonical_coordinates(batches[i].addresses) for i in idxs]
            )[obs]
            _, inv = np.unique(coords, axis=0, return_inverse=True)
            inv = np.asarray(inv).reshape(-1)
            oc = codes[obs].astype(np.int32)
            nev = int(np.max(inv, axis=0)) + 1
            minc = np.full(nev, 1 << 30, dtype=np.int32)
            maxc = np.full(nev, -1, dtype=np.int32)
            np.minimum.at(minc, inv, oc)
            np.maximum.at(maxc, inv, oc)
            conflict_ev = minc != maxc
            entry_conflict = conflict_ev[inv]
            first = np.full(nev, inv.shape[0], dtype=np.int64)
            np.minimum.at(first, inv, np.arange(inv.shape[0], dtype=np.int64))
            is_first = np.zeros(inv.shape[0], dtype=bool)
            is_first[first] = True
            gstat[obs[entry_conflict]] = PLACE_CONFLICT
            gstat[obs[is_first & ~entry_conflict]] = PLACE_COUNTED
            gstat[obs[~is_first & ~entry_conflict]] = PLACE_DUPLICATE
            bc = np.bincount(minc[~conflict_ev])
            for row in np.flatnonzero(bc):
                k = (bank, int(row))
                counts[k] = counts.get(k, 0) + int(bc[row])
            if bool(entry_conflict.any()):
                total = codes.shape[0]
                ord_arr = np.repeat(np.array(idxs, dtype=np.int32), lens)
                place_arr = np.arange(total, dtype=np.int64) - np.repeat(starts, lens)
                sel = obs[entry_conflict]
                conflicts.append(
                    ConflictRecord(
                        bank,
                        metric,
                        key[0],
                        key[1],
                        key[2],
                        key[3],
                        int(np.count_nonzero(conflict_ev)),
                        ord_arr[sel],
                        place_arr[sel],
                        inv[entry_conflict].astype(np.int64),
                        codes[sel].copy(),
                    )
                )
        for k, i in enumerate(idxs):
            row_status[i] = gstat[starts[k] : starts[k] + lens[k]].copy()

    records: list[BatchRecord] = []
    for i, b in enumerate(batches):
        rs = row_status[i]
        assert rs is not None
        rs.flags.writeable = False
        n_counted = int(np.count_nonzero(rs == PLACE_COUNTED))
        n_dup = int(np.count_nonzero(rs == PLACE_DUPLICATE))
        n_conf = int(np.count_nonzero(rs == PLACE_CONFLICT))
        n_none = int(np.count_nonzero(rs == PLACE_NO_MEASUREMENT))
        if status[i] is None:
            if n_conf:
                status[i] = ProfileCode.CONFLICTING
            elif n_counted + n_dup == 0:
                status[i] = ProfileCode.SILENT
            elif n_none:
                status[i] = ProfileCode.PARTIAL
            else:
                status[i] = ProfileCode.VALID
        verdict_status = status[i]
        assert verdict_status is not None
        is_batch = isinstance(b, RowcodeBatch)
        link = getattr(b, "source_link", None)
        coord = getattr(b, "facet_coordinate", None)
        records.append(
            BatchRecord(
                i,
                verdict_status,
                detail[i],
                getattr(b, "bank", None) if is_batch else None,
                getattr(b, "metric", None) if is_batch else None,
                coord if isinstance(coord, FacetCoordinate) else None,
                getattr(b, "measurement_source_identity", None) if is_batch else None,
                link if isinstance(link, SourceLink) else None,
                int(rs.shape[0]),
                rs,
                n_counted,
                n_dup,
                n_conf,
                n_none,
            )
        )

    present = {r.status for r in records}
    if not layout_ok:
        code = ProfileCode.MALFORMED
    else:
        code = None
        for candidate in (
            ProfileCode.MALFORMED,
            ProfileCode.MISMATCH,
            ProfileCode.FACET_MAPPING_CONFLICT,
            ProfileCode.CONFLICTING,
        ):
            if candidate in present:
                code = candidate
                break
        if code is None:
            if not present or present == {ProfileCode.SILENT}:
                code = ProfileCode.SILENT
            elif present & {ProfileCode.PARTIAL, ProfileCode.SILENT}:
                code = ProfileCode.PARTIAL
            else:
                code = ProfileCode.OK
    order = (
        ProfileCode.MALFORMED,
        ProfileCode.MISMATCH,
        ProfileCode.FACET_MAPPING_CONFLICT,
        ProfileCode.CONFLICTING,
        ProfileCode.PARTIAL,
        ProfileCode.SILENT,
        ProfileCode.VALID,
    )
    outcomes = tuple(c for c in order if c in present) or (code,)

    if layout_ok:
        bank_order = {
            b.name: i for i, b in enumerate(profile_layout.count_layout.banks)
        }
        entries = tuple(
            (bank, row, count)
            for (bank, row), count in sorted(
                counts.items(), key=lambda kv: (bank_order[kv[0][0]], kv[0][1])
            )
            if count
        )
        profile = ObjectProfile(object_name, profile_layout.count_layout, entries)
    else:
        profile = ObjectProfile(
            object_name if isinstance(object_name, str) else "",
            profile_layout.count_layout
            if isinstance(profile_layout, ProfileLayout)
            else None,
            (),
        )
    return ObjectAssemblyResult(
        object_name if isinstance(object_name, str) else "",
        code,
        outcomes,
        profile,
        tuple(records),
        tuple(conflicts),
        tuple(i for i in issues if i.code is not ProfileCode.MALFORMED),
        tuple(i for i in issues if i.code is ProfileCode.MALFORMED),
        profile_layout if isinstance(profile_layout, ProfileLayout) else None,
    )


def assemble_object_profile(
    object_name: str,
    profile_layout: ProfileLayout,
    batches,
) -> ObjectAssemblyResult:
    """Assemble with full standalone layout validation."""
    return _assemble_object_profile(object_name, profile_layout, batches)


def _assemble_prepared_object_profile(
    object_name: str,
    profile_layout: ProfileLayout,
    batches,
    shared_compiled: CompiledLayout,
) -> ObjectAssemblyResult:
    """Assemble under a shared layout already compiled by preparation."""
    return _assemble_object_profile(
        object_name, profile_layout, batches, shared_compiled
    )
