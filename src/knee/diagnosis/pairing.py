"""Pair one acquired cheap description with a retained full product by source."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from knee.diagnosis.cheap import pair_descriptions
from knee.diagnosis.models import Profile
from knee.diagnosis.product_cases import profiles_from_product
from knee.encoding.product import open_product


class DiagnosticPairingError(ValueError):
    """A named invalid or ambiguous full/cheap source pairing."""


@dataclass(frozen=True, slots=True)
class PreparedProducts:
    """Immutable run-scoped index of retained full products by declared UID."""

    paths_by_uid: Mapping[str, tuple[Path, ...]]
    source: Path


def _product_paths(products: Path) -> tuple[Path, ...]:
    if not isinstance(products, Path):
        raise DiagnosticPairingError("pair_product_path_required")
    if products.is_file():
        if products.suffix == ".h5" or products.name.endswith(".json.xz"):
            return (products.resolve(),)
        raise DiagnosticPairingError("pair_full_product_format_unsupported")
    if not products.is_dir():
        raise DiagnosticPairingError("pair_full_product_missing")
    h5_paths = tuple(sorted(path.resolve() for path in products.glob("*.h5")))
    if h5_paths:
        return h5_paths
    legacy = tuple(
        sorted(
            path.resolve()
            for path in products.glob("*.json.xz")
            if path.name != "receipt.json.xz"
        )
    )
    if legacy:
        return legacy
    raise DiagnosticPairingError("pair_full_product_directory_empty")


def _product_uid(path: Path) -> str:
    try:
        with open_product(path) as product:
            manifest = product.manifest
    except Exception as error:
        raise DiagnosticPairingError(f"pair_full_product_unreadable:{path}") from error
    if not isinstance(manifest, dict):
        raise DiagnosticPairingError("pair_full_product_manifest_invalid")
    uid = (
        manifest.get("study_uid")
        or manifest.get("studyUID")
        or manifest.get("source_id")
    )
    if not isinstance(uid, str) or not uid.strip():
        raise DiagnosticPairingError("pair_full_product_uid_missing")
    return uid


def prepare_products(products: Path) -> PreparedProducts:
    """Read each product header once and index only its declared study UID."""
    paths = _product_paths(products)
    indexed: dict[str, list[Path]] = {}
    for path in paths:
        indexed.setdefault(_product_uid(path), []).append(path)
    frozen = MappingProxyType(
        {uid: tuple(uid_paths) for uid, uid_paths in indexed.items()}
    )
    return PreparedProducts(frozen, products.resolve())


def _cheap_source_identity(profiles: tuple[Profile, ...], study_uid: str) -> str:
    if not isinstance(profiles, tuple) or not profiles:
        raise DiagnosticPairingError("pair_cheap_profiles_required")
    if not isinstance(study_uid, str) or not study_uid.strip():
        raise DiagnosticPairingError("pair_study_uid_required")
    subjects: set[str] = set()
    producers: set[str] = set()
    for profile in profiles:
        if not isinstance(profile, Profile):
            raise DiagnosticPairingError("pair_cheap_profile_invalid")
        if not isinstance(profile.subject, str) or not profile.subject.strip():
            raise DiagnosticPairingError("pair_cheap_subject_invalid")
        if profile.subject in subjects:
            raise DiagnosticPairingError(
                f"pair_cheap_duplicate_subject:{profile.subject}"
            )
        subjects.add(profile.subject)
        if not isinstance(profile.mode, str) or not profile.mode.startswith("cheap/"):
            raise DiagnosticPairingError(f"pair_cheap_mode_invalid:{profile.subject}")
        if not isinstance(profile.provenance, tuple) or any(
            not isinstance(pair, tuple)
            or len(pair) != 2
            or not isinstance(pair[0], str)
            or not isinstance(pair[1], str)
            for pair in profile.provenance
        ):
            raise DiagnosticPairingError("pair_cheap_provenance_invalid")
        provenance = dict(profile.provenance)
        if len(provenance) != len(profile.provenance):
            raise DiagnosticPairingError("pair_cheap_provenance_duplicate_key")
        source_uid = provenance.get("study_uid")
        if source_uid != study_uid:
            raise DiagnosticPairingError(
                f"pair_cheap_study_uid_mismatch:{profile.subject}"
            )
        for key, value in profile.provenance:
            if key == "producer" or key.endswith(".producer"):
                if not value.strip():
                    raise DiagnosticPairingError("pair_cheap_producer_missing_or_mixed")
                producers.add(value)
    if len(producers) != 1:
        raise DiagnosticPairingError("pair_cheap_producer_missing_or_mixed")
    return next(iter(producers))


def pair_with_products(
    profiles: tuple[Profile, ...],
    study_uid: str,
    products: Path | PreparedProducts,
) -> dict[str, Any]:
    """Return inspectable per-object source pairs without cross-mode comparison.

    ``products`` is a full-product file or a top-level directory of retained H5
    products, falling back to legacy JSON.xz manifests when no H5 files exist.
    Product identity is selected by its declared study UID and must be unique.
    The cheap profiles remain their own input-available records; this function
    never constructs anatomy, compares counts, or returns a diagnostic call.
    """
    if not isinstance(study_uid, str) or not study_uid.strip():
        raise DiagnosticPairingError("pair_study_uid_required")
    producer = _cheap_source_identity(profiles, study_uid)
    prepared = (
        products
        if isinstance(products, PreparedProducts)
        else prepare_products(products)
    )
    matching = prepared.paths_by_uid.get(study_uid, ())
    if not matching:
        if prepared.source.is_file():
            raise DiagnosticPairingError("pair_full_study_uid_mismatch")
        raise DiagnosticPairingError("pair_full_study_uid_not_found")
    if len(matching) != 1:
        raise DiagnosticPairingError("pair_full_study_uid_ambiguous")
    full_path = matching[0]
    full_profiles = profiles_from_product(full_path, mode="full")
    if not full_profiles:
        raise DiagnosticPairingError("pair_full_profiles_empty")
    if any(profile.source_id != study_uid for profile in full_profiles):
        raise DiagnosticPairingError("pair_full_study_uid_mismatch")
    full_by_subject: dict[str, Profile] = {}
    for profile in full_profiles:
        if profile.subject in full_by_subject:
            raise DiagnosticPairingError(
                f"pair_full_duplicate_subject:{profile.subject}"
            )
        full_by_subject[profile.subject] = profile

    objects: list[dict[str, Any]] = []
    for cheap in profiles:
        full = full_by_subject.get(cheap.subject)
        if full is None:
            objects.append(
                {
                    "subject": cheap.subject,
                    "status": "missing_full_object",
                    "cheap": {
                        "source_id": cheap.source_id,
                        "mode": cheap.mode,
                        "scope": cheap.scope,
                        "layout_id": cheap.bundle.layout.layout_id,
                        "carrier_id": cheap.bundle.layout.carrier_id,
                    },
                    "full": None,
                    "pair": None,
                }
            )
            continue
        objects.append(
            {
                "subject": cheap.subject,
                "status": "paired",
                "pair": pair_descriptions(full, cheap, counts_mode="sparse"),
            }
        )
    return {
        "schema": "knee.diagnostic-pairs/v1",
        "study_uid": study_uid,
        "producer": producer,
        "full_product": {
            "path": str(full_path),
            "study_uid": study_uid,
            "storage": "h5" if full_path.suffix == ".h5" else "legacy_json_xz",
        },
        "comparison_performed": False,
        "diagnostic_call": None,
        "objects": objects,
    }
