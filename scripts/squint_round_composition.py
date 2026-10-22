"""Stage existing frozen-parent identity growth for the local training round.

This adapter does not recognize objects, reinterpret calls or publish a final
training memory. It streams exactly the records named by an inference receipt
into the existing growth publisher. The caller retains clinical teaching and
procedure experiences on the returned, actually reviewed continuation, then
publishes its own final child. Observation lineage stays on the frozen parent.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from knee.diagnosis.squint_configurations import SUPERSEDED_CONFIGURATIONS_KEY
from knee.diagnosis.squint_identity_growth import (
    grow_identity_memory,
    harvest_candidates,
)
from knee.diagnosis.squint_memory import MemorySnapshot, load_memory_snapshot
from knee.json_store import load_json

STAGE_SCHEMA = "knee.squint-round-identity-composition/v1"


class RoundCompositionError(ValueError):
    """A named refusal; source observations and published children stay intact."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class GrowthStage:
    """A continuation is usable only when ``status`` is ``ready_to_compose``."""

    status: str
    snapshot: MemorySnapshot | None
    receipt: Mapping[str, Any]


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise RoundCompositionError("composition_checkpoint_unreadable") from error


def _write_new(path: Path, document: Mapping[str, Any]) -> None:
    data = json.dumps(document, sort_keys=True, indent=2, allow_nan=False) + "\n"
    with path.open("x", encoding="utf-8") as stream:
        stream.write(data)


def _snapshot_valid(snapshot: MemorySnapshot) -> bool:
    return (
        snapshot.status == "squint"
        and isinstance(snapshot.memory, dict)
        and isinstance(snapshot.sha256, str)
        and len(snapshot.sha256) == 64
    )


def _inference_inputs(
    parent: MemorySnapshot, directories: Sequence[Path]
) -> tuple[list[dict[str, Any]], list[tuple[Path, str, str]]]:
    """Use receipt-owned records, never nearby ``*.pin.json`` checkpoint files."""
    inputs: list[dict[str, Any]] = []
    records: list[tuple[Path, str, str]] = []
    studies: set[str] = set()
    assert parent.memory is not None
    for directory in directories:
        directory = Path(directory).resolve()
        receipt_path = directory / "receipt.json"
        receipt = _json(receipt_path)
        if (
            not isinstance(receipt, Mapping)
            or receipt.get("action") != "infer"
            or receipt.get("memory_revision") != parent.memory["revision"]
            or receipt.get("memory_manifest_sha256") != parent.sha256
        ):
            raise RoundCompositionError("inference_generating_parent_mismatch")
        work = receipt.get("work")
        entries = work.get("studies") if isinstance(work, Mapping) else None
        if not isinstance(entries, list) or not entries:
            raise RoundCompositionError("inference_study_entries_missing")
        record_pins = []
        for entry in entries:
            if not isinstance(entry, Mapping):
                raise RoundCompositionError("inference_study_entry_invalid")
            uid, relative = entry.get("study_uid"), entry.get("evidence_path")
            if not isinstance(uid, str) or not uid or not isinstance(relative, str):
                raise RoundCompositionError("inference_study_entry_invalid")
            if uid in studies:
                raise RoundCompositionError("duplicate_study_record")
            studies.add(uid)
            path = (directory / relative).resolve()
            if Path(relative).is_absolute() or directory not in path.parents:
                raise RoundCompositionError("inference_record_outside_run")
            if not path.is_file():
                raise RoundCompositionError("inference_record_missing")
            digest = _digest(path)
            record_pins.append({"study_uid": uid, "file": relative, "sha256": digest})
            records.append((path, uid, digest))
        inputs.append(
            {
                "path": str(directory),
                "receipt_sha256": _digest(receipt_path),
                "records": record_pins,
            }
        )
    if not records:
        raise RoundCompositionError("inference_records_missing")
    return inputs, records


def _records(
    paths: Sequence[tuple[Path, str, str]], parent: MemorySnapshot
) -> Iterator[Mapping[str, Any]]:
    assert parent.memory is not None
    for path, uid, digest in paths:
        if _digest(path) != digest:
            raise RoundCompositionError("inference_record_changed")
        record = load_json(path)
        if (
            not isinstance(record, Mapping)
            or record.get("study_uid") != uid
            or record.get("memory_revision") != parent.memory["revision"]
            or record.get("memory_manifest_sha256", parent.sha256) != parent.sha256
        ):
            raise RoundCompositionError("inference_record_parent_or_study_mismatch")
        yield record


def _growth_snapshot(receipt: Mapping[str, Any], growth_path: Path) -> MemorySnapshot:
    child = receipt.get("child")
    if not isinstance(child, Mapping):
        raise RoundCompositionError("growth_child_receipt_missing")
    snapshot = load_memory_snapshot(growth_path / "memory")
    if (
        not _snapshot_valid(snapshot)
        or snapshot.memory is None
        or snapshot.sha256 != child.get("sha256")
        or snapshot.memory["revision"] != child.get("revision")
    ):
        raise RoundCompositionError("growth_child_checkpoint_mismatch")
    return snapshot


def _reviewed_snapshot(
    growth: MemorySnapshot,
    receipt: Mapping[str, Any],
    reviewed_path: Path,
    *,
    require_complete: bool = True,
) -> MemorySnapshot:
    reviewed = load_memory_snapshot(reviewed_path)
    if not _snapshot_valid(reviewed) or reviewed.memory is None:
        raise RoundCompositionError("reviewed_growth_child_invalid")
    teaching = reviewed.memory.get("object_identity_teaching", {})
    reviews = (
        teaching.get("admission_reviews", []) if isinstance(teaching, Mapping) else []
    )
    covered: set[str] = set()
    for review in reviews:
        if (
            isinstance(review, Mapping)
            and review.get("reviewed_manifest_sha256") == growth.sha256
        ):
            calls = review.get("calls")
            if not isinstance(calls, list):
                raise RoundCompositionError("admission_review_record_invalid")
            for call in calls:
                if not isinstance(call, Mapping) or not isinstance(
                    call.get("candidate_id"), str
                ):
                    raise RoundCompositionError("admission_review_record_invalid")
                covered.add(call["candidate_id"])
    if not covered or (
        require_complete and not set(receipt["admitted_case_ids"]).issubset(covered)
    ):
        raise RoundCompositionError("admission_review_incomplete")
    _review_continuation(growth, reviewed)
    return reviewed


def _review_continuation(growth: MemorySnapshot, reviewed: MemorySnapshot) -> None:
    """Check the existing review publisher's continuation, not a copied review claim.

    A review can correct admitted facets and rebuild their configurations. It
    cannot erase inherited signed cases, ordinary objects, experiences or source
    tables. Replaced configurations and corrected objects keep their old bodies.
    """
    assert growth.memory is not None and reviewed.memory is not None
    before, after = growth.memory, reviewed.memory
    old_teaching, new_teaching = (
        memory["object_identity_teaching"] for memory in (before, after)
    )
    old_reviews = old_teaching.get("admission_reviews", [])
    new_reviews = new_teaching.get("admission_reviews", [])
    if (
        len(new_reviews) != len(old_reviews) + 1
        or new_reviews[:-1] != old_reviews
        or new_reviews[-1].get("reviewed_manifest_sha256") != growth.sha256
    ):
        raise RoundCompositionError("reviewed_child_not_growth_continuation")
    if (
        after.get("parent_revision") != before["revision"]
        or after.get("parent_manifest_sha256") != growth.sha256
    ):
        raise RoundCompositionError("reviewed_child_parent_mismatch")
    review = new_reviews[-1]
    corrected = set(review.get("corrected_case_ids", []))
    cases = {case["case_id"]: case for case in after["cases"]}
    identity_rows = (after.get("object_identity_cases") or {}).get("cases", [])
    corrected_rows = {case["case_id"]: case for case in identity_rows}
    retired = (after.get(SUPERSEDED_CONFIGURATIONS_KEY) or {}).get("cases", [])
    retired_cases = [row.get("case") for row in retired]
    for case in before["cases"]:
        if cases.get(case["case_id"]) == case:
            continue
        if case["subject"].startswith("diagnosis/") and case in retired_cases:
            continue
        record = corrected_rows.get(case["case_id"])
        if case["case_id"] not in corrected or not isinstance(record, Mapping):
            raise RoundCompositionError("reviewed_child_lost_parent_case")
        if any(
            record.get(key) != value
            for key, value in case.items()
            if key not in {"reader", "review_sha256", "identity_correction"}
        ):
            raise RoundCompositionError("reviewed_child_changed_corrected_source")
    allowed = {
        "revision",
        "parent_revision",
        "parent_manifest_sha256",
        "cases",
        "object_identity_teaching",
        "object_identity_cases",
        SUPERSEDED_CONFIGURATIONS_KEY,
        "full_profile_retention",
        "view",
        "prepared_recall",
        "memory_manifest_sha256",
    }
    if any(
        after.get(key) != value for key, value in before.items() if key not in allowed
    ):
        raise RoundCompositionError("reviewed_child_changed_parent_store")
    inherited_rows = (before.get("object_identity_cases") or {}).get("cases", [])
    if identity_rows[: len(inherited_rows)] != inherited_rows:
        raise RoundCompositionError("reviewed_child_changed_signed_cases")
    old_calls = [
        row for row in old_teaching["calls"] if row["candidate_id"] not in corrected
    ]
    new_calls = [
        row for row in new_teaching["calls"] if row["candidate_id"] not in corrected
    ]
    if old_calls != new_calls or any(
        new_teaching.get("negative_views", {}).get(key) != value
        for key, value in old_teaching.get("negative_views", {}).items()
    ):
        raise RoundCompositionError("reviewed_child_changed_signed_calls")


def stage_identity_growth(
    parent: MemorySnapshot,
    inference_directories: Sequence[Path],
    output: Path,
    *,
    labels: Path | None = None,
    held_out: Sequence[str] = (),
    reviewed_memory: Path | None = None,
    require_admission_review: bool = True,
) -> GrowthStage:
    """Reuse frozen observations and an immutable intermediate growth publication.

    The existing review command is ``squint_object_bootstrap.py export-admissions``
    followed by ``admit``. Supply that command's reviewed child on resume. The
    caller owns the established first-round/spot-check inspection policy; the
    default requires an actual recorded review call for every new admission.
    This function never marks a published proposal accepted just for loading.
    """
    if not _snapshot_valid(parent):
        raise RoundCompositionError("composition_parent_invalid")
    if output.is_symlink():
        raise RoundCompositionError("composition_output_unsafe")
    inputs, paths = _inference_inputs(parent, inference_directories)
    pin = {
        "schema": STAGE_SCHEMA,
        "parent_sha256": parent.sha256,
        "inference": inputs,
        "labels": None
        if labels is None
        else {"path": str(labels.resolve()), "sha256": _digest(labels)},
        "held_out": sorted(held_out),
    }
    output.mkdir(parents=True, exist_ok=True)
    input_path = output / "inputs.json"
    if input_path.exists():
        if _json(input_path) != pin:
            raise RoundCompositionError("composition_inputs_changed")
    else:
        _write_new(input_path, pin)
    receipt_path = output / "receipt.json"
    growth_path = output / "identity-growth"
    if receipt_path.exists():
        receipt = _json(receipt_path)
        receipt_parent = receipt.get("parent") if isinstance(receipt, Mapping) else None
        if (
            not isinstance(receipt, Mapping)
            or not isinstance(receipt_parent, Mapping)
            or receipt_parent.get("manifest_sha256") != parent.sha256
        ):
            raise RoundCompositionError("growth_receipt_parent_mismatch")
    else:
        if growth_path.exists():
            raise RoundCompositionError("growth_checkpoint_incomplete")
        candidates = harvest_candidates(
            _records(paths, parent), record_sha256s=(digest for _, _, digest in paths)
        )
        receipt = grow_identity_memory(
            parent, candidates, growth_path, labels=labels, held_out=held_out
        )
        _write_new(receipt_path, receipt)
    if receipt.get("outcome") == "no_admissions":
        return GrowthStage("ready_to_compose", parent, receipt)
    if receipt.get("outcome") != "published":
        raise RoundCompositionError("growth_outcome_not_composable")
    growth = _growth_snapshot(receipt, growth_path)
    if require_admission_review and reviewed_memory is None:
        return GrowthStage("admission_review_required", None, receipt)
    selected = (
        _reviewed_snapshot(
            growth,
            receipt,
            reviewed_memory,
            require_complete=require_admission_review,
        )
        if reviewed_memory is not None
        else growth
    )
    return GrowthStage("ready_to_compose", selected, receipt)
