"""One-study-at-a-time full-profile generation for diagnostic source records.

The producer owns the mechanics of creating a retained H5 product inside the
fresh directory supplied for each study. This module reads that product
through the public reader, yields detached profiles and source evidence, then
removes only the temporary subtree it created.
"""

from __future__ import annotations

import re
import shutil
import tempfile
import time
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import Any

from knee.diagnosis.models import Profile
from knee.diagnosis.product_cases import profiles_from_product

_SAFE_UID = re.compile(r"^[A-Za-z0-9._-]+$")


class GeneratedStudyError(ValueError):
    """A named failure while producing or reading one generated study."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _study_uids(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise GeneratedStudyError("study_uids_sequence_required")
    try:
        uids = tuple(values)
    except TypeError as error:
        raise GeneratedStudyError("study_uids_sequence_required") from error
    if not uids:
        raise GeneratedStudyError("study_uids_nonempty_required")
    for uid in uids:
        if (
            not isinstance(uid, str)
            or not _SAFE_UID.fullmatch(uid)
            or uid in (".", "..")
        ):
            raise GeneratedStudyError("study_uid_invalid")
    if len(set(uids)) != len(uids):
        raise GeneratedStudyError("study_uid_duplicate")
    return uids


def _producer_identity(producer: Callable[..., object]) -> str:
    module = getattr(producer, "__module__", None)
    qualname = getattr(producer, "__qualname__", None)
    if isinstance(module, str) and module and isinstance(qualname, str) and qualname:
        return f"{module}.{qualname}"
    producer_type = type(producer)
    return f"{producer_type.__module__}.{producer_type.__qualname__}"


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def generated_studies(
    study_uids: Iterable[str],
    producer: Callable[[str, Path], Path],
    *,
    scratch_root: Path,
) -> Iterator[tuple[str, tuple[Profile, ...], dict[str, Any]]]:
    """Generate and yield detached full profiles serially, cleaning owned files.

    ``producer(uid, fresh_study_directory)`` must return a complete H5 product.
    Products written within the supplied directory are transient and are
    removed when iteration advances, fails, or closes. A producer path outside
    that directory is read but never removed. The yielded metadata includes
    the profiles themselves so the caller can persist exact source evidence
    before using them in comparisons.
    """
    uids = _study_uids(study_uids)
    if not callable(producer):
        raise GeneratedStudyError("producer_callable_required")
    if not isinstance(scratch_root, Path) or not scratch_root.is_dir():
        raise GeneratedStudyError("scratch_root_existing_directory_required")
    scratch = scratch_root.resolve()
    identity = _producer_identity(producer)

    with tempfile.TemporaryDirectory(prefix="knee-generated-", dir=scratch) as owned:
        owned_root = Path(owned)
        for study_uid in uids:
            study_directory = owned_root / study_uid
            study_directory.mkdir()
            profiles: tuple[Profile, ...] = ()
            source_metadata: dict[str, Any] = {}
            product_path: Path | None = None
            try:
                started = time.perf_counter()
                try:
                    produced = producer(study_uid, study_directory)
                except Exception as error:
                    raise GeneratedStudyError("producer_failed") from error
                producer_seconds = time.perf_counter() - started
                if not isinstance(produced, Path):
                    raise GeneratedStudyError("producer_product_path_required")
                product_path = produced.resolve()
                if product_path.suffix.lower() != ".h5":
                    raise GeneratedStudyError("generated_product_must_be_h5")
                if not product_path.is_file():
                    raise GeneratedStudyError("generated_product_missing")
                try:
                    profiles = profiles_from_product(product_path, mode="full")
                except Exception as error:
                    detail = f"{type(error).__name__}:{error}"
                    raise GeneratedStudyError(
                        f"generated_product_unreadable:{detail}"
                    ) from error
                if not profiles:
                    raise GeneratedStudyError("generated_profiles_empty")
                if any(not isinstance(profile, Profile) for profile in profiles):
                    raise GeneratedStudyError("generated_profile_record_invalid")
                if any(profile.source_id != study_uid for profile in profiles):
                    raise GeneratedStudyError("generated_product_study_uid_mismatch")

                transient = _is_within(product_path, study_directory.resolve())
                source_metadata = {
                    "api": "knee.diagnosis.generated.generated_studies/v1",
                    "source_api": "generated",
                    "study_uid": study_uid,
                    "mode": "full",
                    "producer": identity,
                    "producer_seconds": producer_seconds,
                    "full_anatomy_runs": 1,
                    "product_path": product_path,
                    "product_transient": transient,
                    "product_retained": not transient,
                    "profiles": profiles,
                }
                yield study_uid, profiles, source_metadata
            finally:
                # Drop references before deleting the product. Profiles are
                # detached by profiles_from_product and no longer need the H5.
                source_metadata = {}
                profiles = ()
                product_path = None
                shutil.rmtree(study_directory, ignore_errors=True)
