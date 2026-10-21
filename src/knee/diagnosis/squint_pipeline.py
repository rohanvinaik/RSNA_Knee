"""Squint-first inference, bounded study lifetimes and official output.

The full reconstruction runner is a bootstrap/reference tool. This coordinator
never calls it. Each worker owns one study's decoded pixels and releases them
when its compact findings have been published. Case memory is loaded once.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import platform
import resource
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from knee.diagnosis.squint_interfaces import MEMORY_VIEW_SCHEMA
from knee.diagnosis.squint_locator import recall_source_fingerprint
from knee.diagnosis.squint_memory_view import memory_view
from knee.study.tables import LABELS

SCHEMA = "knee.squint-run/v1"
MEMORY_SCHEMA = "knee.squint-memory/v1"


class SquintRunError(ValueError):
    """A named source, output or invocation failure."""


def _manifest_path(path: Path) -> Path:
    return path / "manifest.json" if path.is_dir() else path


def is_squint_memory(path: Path | None) -> bool:
    """Select only an explicitly declared new memory; legacy stores keep their route."""
    if path is None:
        return False
    candidate = _manifest_path(Path(path))
    if not candidate.is_file():
        return False
    try:
        declaration = json.loads(candidate.read_text())
    except (OSError, ValueError, UnicodeError):
        return False
    return isinstance(declaration, dict) and declaration.get("schema") == MEMORY_SCHEMA


def _save(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    try:
        temporary.write_text(json.dumps(record, sort_keys=True, allow_nan=False))
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _table_uids(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "StudyInstanceUID" not in reader.fieldnames:
            raise SquintRunError("study_table_columns_invalid")
        rows = list(reader)
    uids = tuple(row["StudyInstanceUID"] for row in rows)
    if not uids or any(not uid or Path(uid).name != uid for uid in uids):
        raise SquintRunError("study_uid_invalid_or_empty")
    if len(set(uids)) != len(uids):
        raise SquintRunError("duplicate_study_uid")
    return uids


def _selected_uids(args) -> tuple[str, ...]:
    selected = getattr(args, "study_uid", None)
    if selected:
        uids = tuple(selected)
        if len(set(uids)) != len(uids) or any(
            not isinstance(uid, str) or not uid or Path(uid).name != uid for uid in uids
        ):
            raise SquintRunError("study_uid_invalid_or_duplicate")
        return uids
    root = Path(args.root)
    if getattr(args, "labeled", False):
        with (root / "train.csv").open(newline="", encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        uids = tuple(
            row["StudyInstanceUID"]
            for row in rows
            if all(row.get(label) in ("0", "1") for label in LABELS)
        )
        if not uids:
            raise SquintRunError("no_labeled_studies")
        return uids
    split = getattr(args, "split", None)
    if split not in ("train", "test"):
        raise SquintRunError("raw_study_selector_required")
    return _table_uids(root / (split + ".csv"))


def _empty_profile(subject: str) -> dict:
    return {
        "schema": "knee.squint-profile/v1",
        "subject": subject,
        "banks": {},
        "source": {
            "code": "object_not_located",
            "procedure": "knee.squint-profile/scan-tercile-v1",
        },
    }


def _recall_question(
    question, objects: dict, memory: dict, uid: str, excluded: bool
) -> dict:
    from knee.diagnosis.squint_locator import recall_object

    try:
        from knee.diagnosis.squint_questions import question_selection

        selection = question_selection(question.question_id)
    except (ImportError, ValueError):
        selection = None
    # One declaration reaches both anatomical and role-qualified recalls.
    # A missing adapter is explicit invalid selection, never all-bank recall.
    memory = {**memory, "recall_selection": selection}
    evidence = {}
    for subject in question.objects:
        located = objects.get(subject, {})
        profile = located.get("profile") or _empty_profile(subject)
        evidence[subject] = {
            **recall_object(
                profile,
                memory,
                question=question.question_id,
                exclude_study_uid=uid if excluded else "",
            ),
            "location_status": located.get("status", "unavailable"),
            "regions": located.get("regions", []),
        }
    from knee.diagnosis.squint_configurations import configuration_profile

    source_profiles = {
        subject: objects[subject]["profile"]
        for subject in question.objects
        if subject in objects and objects[subject].get("profile") is not None
    }
    combined = configuration_profile(source_profiles, question.question_id)
    if combined["banks"]:
        evidence[combined["subject"]] = recall_object(
            combined,
            memory,
            question=question.question_id,
            exclude_study_uid=uid if excluded else "",
        )
    return evidence


def _budget_unexamined_study(
    uid: str, memory: dict, *, reason: str, elapsed_seconds: float = 0.0
) -> dict:
    """Represent a study skipped before pixels as neutral, open evidence."""
    from knee.diagnosis.declarations import QUESTIONS
    from knee.diagnosis.squint_contracts import combine_condition, rank_condition

    questions = {}
    values = {}
    for question in QUESTIONS:
        finding = combine_condition(question.question_id, {})
        ranking = finding.get("rank")
        if not isinstance(ranking, dict):
            ranking = rank_condition(finding)
        value = ranking.get("value")
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not 0.0 < value < 1.0
        ):
            raise SquintRunError(
                "budget_unexamined_ranking_invalid:" + question.question_id
            )
        values[question.question_id] = value
        questions[question.question_id] = {
            "finding": finding,
            "ranking": ranking,
            "objects": {},
        }
    return {
        "schema": "knee.squint-study/v1",
        "study_uid": uid,
        "memory_revision": memory.get("revision", ""),
        "study_status": "not_examined_budget",
        "not_examined_reason": reason,
        "questions": questions,
        "values": values,
        "objects": {},
        "observations": [],
        "work": {
            "elapsed_seconds": elapsed_seconds,
            "full_anatomy_runs": 0,
            "bounded_zoom_runs": 0,
            "squint_stacks": 0,
            "image_reads": 0,
            "source_mode": "raw_squint_case_recall",
        },
        "unresolved_observation_requests": [],
    }


def _bounded_observation(
    request: dict, study: dict, objects: dict, attempted: set, deadline: float | None
) -> dict:
    """Apply the paired finer lens only to a requested, located native region."""
    from knee.diagnosis.squint_profiles import merge_profiles, refine_window

    subject = request.get("object", request.get("subject"))
    if not isinstance(subject, str) or subject not in objects:
        return {"code": "object_region_unavailable", "request": request}
    if subject in attempted:
        return {"code": "shared_observation_already_available", "subject": subject}
    if deadline is not None and time.monotonic() >= deadline:
        return {"code": "deadline_before_zoom", "subject": subject}
    located = objects[subject]
    profiles = []
    regions = []
    by_uid = {s["series_uid"]: s for s in study.get("series", [])}
    for region in located.get("regions", []):
        if not isinstance(region, dict):
            continue
        series = by_uid.get(region.get("series_uid"))
        window = region.get("window", region.get("source_window"))
        if series is None or not isinstance(window, (list, tuple)) or len(window) != 6:
            continue
        if deadline is not None and time.monotonic() >= deadline:
            break
        profile = refine_window(series, tuple(window), subject=subject, tile_mm=2.0)
        if profile.get("banks"):
            profiles.append(profile)
            regions.append({"series_uid": region["series_uid"], "window": list(window)})
    if not profiles:
        return {"code": "no_compatible_bounded_reading", "subject": subject}
    previous = located.get("profile")
    if previous is not None:
        profiles.insert(0, previous)
    located["profile"] = merge_profiles(profiles, subject=subject)
    attempted.add(subject)
    return {
        "code": "measured",
        "subject": subject,
        "regions": regions,
        "lens": "physical_squint",
        "tile_mm": 2.0,
    }


def infer_study(
    root: Path,
    uid: str,
    memory: dict,
    *,
    deadline: float | None = None,
    io_workers: int = 8,
    exclude_same_study: bool = False,
) -> dict:
    """Consume current-study cheap observations; never read teaching calls as features."""
    from knee.diagnosis.declarations import QUESTIONS
    from knee.diagnosis.squint_contracts import combine_condition, rank_condition
    from knee.diagnosis.squint_locator import locate_objects
    from knee.diagnosis.squint_profiles import read_study_squints

    started = time.perf_counter()
    if deadline is not None and time.monotonic() >= deadline:
        return _budget_unexamined_study(
            uid,
            memory,
            reason="study_time_budget_exhausted_before_read",
            elapsed_seconds=time.perf_counter() - started,
        )
    view = memory.get("view")
    if exclude_same_study and not (
        isinstance(view, dict)
        and view.get("schema") == MEMORY_VIEW_SCHEMA
        and uid in view.get("excluded_study_uids", ())
        and view.get("source_fingerprint") == recall_source_fingerprint(memory)
    ):
        memory, _excluded = _study_excluded_memory(memory, uid)
    study = read_study_squints(root, uid, io_workers=io_workers)
    locations = locate_objects(study, memory, deadline=deadline)
    objects = locations.get("objects", {})
    questions = {}
    values = {}
    observations = []
    attempted = set()
    for question in QUESTIONS:
        object_evidence = _recall_question(
            question, objects, memory, uid, exclude_same_study
        )
        finding = combine_condition(question.question_id, object_evidence)
        requests = (
            finding.get("observation_requests", [])
            if finding.get("outcome") == "open"
            else []
        )
        if requests:
            for request in requests:
                observations.append(
                    _bounded_observation(request, study, objects, attempted, deadline)
                )
            object_evidence = _recall_question(
                question, objects, memory, uid, exclude_same_study
            )
            finding = combine_condition(question.question_id, object_evidence)
        ranking = finding.get("rank")
        if not isinstance(ranking, dict):
            ranking = rank_condition(finding)
        value = ranking.get("value")
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise SquintRunError("ranking_value_invalid:" + question.question_id)
        if not 0.0 < value < 1.0:
            raise SquintRunError(
                "ranking_endpoint_or_out_of_range:" + question.question_id
            )
        values[question.question_id] = value
        questions[question.question_id] = {
            "finding": finding,
            "ranking": ranking,
            "objects": object_evidence,
        }
    work = {
        **study.get("work", {}),
        "elapsed_seconds": time.perf_counter() - started,
        "full_anatomy_runs": 0,
        "bounded_zoom_runs": sum(row["code"] == "measured" for row in observations),
        "source_mode": "raw_squint_case_recall",
    }
    # Neither Series nor SquintStack escapes this operation. Retained profiles
    # and addresses suffice to inspect why recall reached each finding.
    result = {
        "schema": "knee.squint-study/v1",
        "study_uid": uid,
        "memory_revision": memory.get("revision", ""),
        "study_status": "examined",
        "questions": questions,
        "values": values,
        "objects": objects,
        "observations": observations,
        "work": work,
        "unresolved_observation_requests": [
            {"question": q, **request}
            for q, record in questions.items()
            for request in record["finding"].get("observation_requests", [])
        ],
    }
    return result


def _study_excluded_memory(memory: dict, uid: str) -> tuple[dict, dict]:
    """Use the same population for capacity location, recall and preparation."""
    view = memory_view(memory, exclude_study_uids=(uid,))
    case_count = len(memory.get("cases", ()))
    censor_count = len(memory.get("censors", ()))
    return view, {
        "excluded_study_uid": uid,
        "original_case_count": case_count,
        "filtered_case_count": len(view["cases"]),
        "excluded_case_count": case_count - len(view["cases"]),
        "original_censor_count": censor_count,
        "filtered_censor_count": len(view.get("censors", ())),
        "excluded_censor_count": censor_count - len(view.get("censors", ())),
    }


def _study_budget_deadline(
    total_deadline: float,
    remaining_studies: int,
    worker_count: int,
    *,
    now: float | None = None,
) -> tuple[float, float]:
    """Allocate one bounded remaining-time share to an admitted study."""
    moment = time.monotonic() if now is None else now
    if type(remaining_studies) is not int or remaining_studies < 1:
        raise SquintRunError("remaining_studies_invalid")
    if type(worker_count) is not int or worker_count < 1:
        raise SquintRunError("worker_count_invalid")
    remaining = max(0.0, total_deadline - moment)
    active_workers = min(worker_count, remaining_studies)
    share = remaining * active_workers / remaining_studies
    return min(total_deadline, moment + share), share


def _capacity_exclusion_evidence(
    excluded: dict,
    prepared: dict | None,
    *,
    memory: dict,
    memory_digest: str,
    preparation_status: str,
) -> dict:
    prepared = prepared or {}
    excluded_count = (
        excluded["excluded_case_count"] or excluded["excluded_censor_count"]
    )
    population = {
        "status": (
            "prepared" if prepared.get("outcome") == "prepared" else preparation_status
        ),
        "source_fingerprint": prepared.get("source_fingerprint"),
        "source": prepared.get(
            "memory_source", memory.get("source", memory.get("metadata", {}))
        ),
        "memory_manifest_sha256": memory_digest,
        "case_profile_count": (
            len(prepared.get("case_profile_banks", {}))
            if isinstance(prepared.get("case_profile_banks"), dict)
            else None
        ),
    }
    return {
        **excluded,
        "exclusion_status": "applied" if excluded_count else "no_matching_attribution",
        "consumed_case_fingerprint": prepared.get("source_fingerprint"),
        "consumed_fingerprint_scope": "source_cases_calls_profiles_and_censors_v1",
        "preparation_schema": prepared.get("schema"),
        "preparation_outcome": prepared.get("outcome", preparation_status),
        "prepared_population_identity": population,
    }


def _publish_preparation_cache_bytes(
    output: Path, content: bytes, expected_sha256: str
) -> Path:
    """Atomically retain the exact validated compressed preparation sidecar."""
    destination = output / "recall-preparation.json.xz"
    temporary = output / f".{destination.name}.{os.getpid()}.tmp"
    try:
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        copied_sha256 = hashlib.sha256(temporary.read_bytes()).hexdigest()
        if copied_sha256 != expected_sha256:
            raise SquintRunError("squint_recall_cache_copy_digest_mismatch")
        os.replace(temporary, destination)
        directory_fd = os.open(output, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return destination
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def run_squint_cli(args, *, prepared_memory_snapshot=None) -> dict:
    """One production entry point, bounded concurrent studies and immutable memory."""
    from knee.diagnosis.squint_memory import (
        MemorySnapshot,
        compile_bootstrap,
        load_memory_snapshot,
    )
    from knee.diagnosis.submission import write_submission

    mode = getattr(args, "diagnostic_mode", None)
    if getattr(args, "draw", False):
        raise SquintRunError("squint_production_disallows_draw")
    if args.diagnostic_memory is None or args.diagnostic_output is None:
        raise SquintRunError("squint_memory_and_output_required")
    if any(
        getattr(args, name, None) is not None
        for name in (
            "diagnostic_products",
            "diagnostic_inputs",
            "diagnostic_readout",
            "diagnostic_trust",
            "diagnostic_questions",
            "diagnostic_cases",
            "diagnostic_scratch",
        )
    ):
        raise SquintRunError("squint_conflicting_reference_options")
    output = Path(args.diagnostic_output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    bootstrap = getattr(args, "squint_bootstrap_products", None)
    if mode == "teach":
        if bootstrap is None:
            raise SquintRunError("squint_bootstrap_products_required")
        selected = tuple(args.study_uid) if getattr(args, "study_uid", None) else None
        compiled = compile_bootstrap(
            Path(args.root),
            Path(bootstrap),
            Path(args.diagnostic_memory),
            selected_uids=selected,
        )
        result = {
            "schema": SCHEMA,
            "action": "teach",
            "store": compiled,
            "memory": str(Path(args.diagnostic_memory).resolve()),
            "work": {
                "elapsed_seconds": time.perf_counter() - started,
                "full_anatomy_runs": 0,
            },
        }
        _save(output / "receipt.json", result)
        return result
    if mode not in ("infer", "capacity") or bootstrap is not None:
        raise SquintRunError("squint_operation_invalid")
    if getattr(args, "diagnostic_labels", None) is not None:
        raise SquintRunError("squint_inference_does_not_read_label_source")
    limit = float(getattr(args, "squint_time_limit", 30000.0))
    if not math.isfinite(limit) or limit <= 0:
        raise SquintRunError("squint_time_limit_invalid")
    total_deadline = time.monotonic() + limit
    snapshot = prepared_memory_snapshot
    if snapshot is None:
        snapshot = load_memory_snapshot(Path(args.diagnostic_memory))
    if not isinstance(snapshot, MemorySnapshot):
        raise SquintRunError("squint_memory_snapshot_invalid")
    expected_path = _manifest_path(Path(args.diagnostic_memory)).resolve()
    if snapshot.path != expected_path:
        raise SquintRunError("squint_memory_snapshot_path_mismatch")
    if snapshot.status != "squint" or snapshot.memory is None:
        raise SquintRunError(snapshot.error_code or "squint_memory_snapshot_invalid")
    if not isinstance(snapshot.sha256, str):
        raise SquintRunError("squint_memory_snapshot_digest_missing")
    memory_digest = snapshot.sha256
    memory = snapshot.memory
    if mode == "capacity":
        memory = {**memory, "memory_manifest_sha256": memory_digest}
    from knee.diagnosis.squint_locator import prepare_recall
    from knee.json_store import dump_json_atomic, load_json, resolve_json_path

    uids = _selected_uids(args)
    cohort_path = getattr(args, "diagnostic_cohort", None)
    partition = getattr(args, "diagnostic_partition", None)
    cohort_receipt = None
    if (cohort_path is None) != (partition is None):
        raise SquintRunError("squint_cohort_and_partition_must_be_paired")
    if cohort_path is not None:
        from knee.diagnosis.cohort import load_cohort, partition_uids

        if not isinstance(partition, str):
            raise SquintRunError("squint_cohort_partition_invalid")
        cohort = load_cohort(Path(cohort_path))
        uids = partition_uids(cohort, partition, uids)
        cohort_receipt = {
            "path": cohort.source,
            "sha256": cohort.sha256,
            "partition": partition,
        }
    worker_count = max(1, min(int(args.workers), len(uids), 4))
    preparation_path = None
    preparation_seconds = 0.0
    preparation_cache_path = resolve_json_path(
        snapshot.path.parent / "recall-preparation.json"
    )
    cache = None
    preparation_cache_status = (
        "study_excluded_per_study" if mode == "capacity" else "missing_recomputed"
    )
    preparation_cache_bytes = None
    preparation_cache_sha256 = None
    if preparation_cache_path.is_file():
        try:
            pinned_sha256 = hashlib.sha256(
                preparation_cache_path.read_bytes()
            ).hexdigest()
            candidate = load_json(preparation_cache_path)
            loaded_bytes = preparation_cache_path.read_bytes()
            if hashlib.sha256(loaded_bytes).hexdigest() != pinned_sha256:
                candidate = None
            elif preparation_cache_path.name.endswith(".json.xz"):
                preparation_cache_bytes = loaded_bytes
                preparation_cache_sha256 = pinned_sha256
        except (OSError, ValueError, UnicodeError):
            candidate = None
            preparation_cache_bytes = None
            preparation_cache_sha256 = None
        if (
            isinstance(candidate, dict)
            and candidate.get("memory_manifest_sha256") == memory_digest
            and candidate.get("memory_revision") == memory.get("revision", "")
        ):
            cache = candidate
            if mode != "capacity":
                preparation_cache_status = "cached_candidate"
        elif mode != "capacity":
            preparation_cache_status = "invalid_recomputed"
    if mode != "capacity":
        preparation_started = time.perf_counter()
        prepared = (
            prepare_recall(memory, cached=cache)
            if cache is not None
            else prepare_recall(memory)
        )
        preparation_seconds = time.perf_counter() - preparation_started
        if not isinstance(prepared, dict) or prepared.get("outcome") != "prepared":
            raise SquintRunError("squint_recall_preparation_invalid")
        if prepared.get("runtime_indexes_rebuilt") is True:
            preparation_cache_status = "persisted_reused"
        elif cache is not None:
            preparation_cache_status = "stale_recomputed"
        memory = {**memory, "prepared_recall": prepared}
        if (
            preparation_cache_status == "persisted_reused"
            and isinstance(cache, dict)
            and preparation_cache_bytes is not None
            and preparation_cache_sha256 is not None
        ):
            preparation_path = _publish_preparation_cache_bytes(
                output, preparation_cache_bytes, preparation_cache_sha256
            )
            preparation_artifact_schema = cache.get("schema")
            preparation_artifact_source = "persisted_cache_sidecar_bytes"
        else:
            preparation_path = dump_json_atomic(
                output / "recall-preparation.json",
                {
                    "schema": prepared.get("schema"),
                    "memory_manifest_sha256": memory_digest,
                    "memory_revision": memory.get("revision", ""),
                    "cache_status": preparation_cache_status,
                    **{
                        key: prepared[key]
                        for key in (
                            "outcome",
                            "source_fingerprint",
                            "memory_source",
                            "envelopes",
                            "case_indices",
                            "censor_indices",
                        )
                        if key in prepared
                    },
                },
            )
            preparation_artifact_schema = prepared.get("schema")
            preparation_artifact_source = "computed_preparation"
        preparation_identity = {
            "source_fingerprint": prepared.get("source_fingerprint"),
            "memory_manifest_sha256": memory_digest,
            "memory_revision": memory.get("revision", ""),
        }
    else:
        preparation_artifact_schema = None
        preparation_artifact_source = "not_written"
        preparation_identity = None

    def infer_admitted_study(uid: str, deadline: float, budget_seconds: float) -> dict:
        study_memory: dict = memory
        excluded = None
        study_preparation_seconds = 0.0
        study_preparation_source = preparation_cache_status
        if mode == "capacity":
            study_memory, excluded = _study_excluded_memory(memory, uid)
        if time.monotonic() >= deadline:
            record = _budget_unexamined_study(
                uid,
                study_memory,
                reason="study_time_budget_exhausted_before_preparation",
            )
            record["work"].update(
                {
                    "study_time_budget_seconds": budget_seconds,
                    "study_budget_deadline_exhausted": True,
                    "recall_preparation_seconds": 0.0,
                    "recall_preparation_source": "not_run_budget_exhausted",
                }
            )
            if excluded is not None:
                record["capacity_exclusion"] = _capacity_exclusion_evidence(
                    excluded,
                    None,
                    memory=memory,
                    memory_digest=memory_digest,
                    preparation_status="not_run_budget_exhausted",
                )
            else:
                record["capacity_exclusion"] = {
                    "exclusion_status": "not_requested",
                    "excluded_study_uid": None,
                }
            return record
        if mode == "capacity":
            preparation_started = time.perf_counter()
            study_prepared = prepare_recall(memory, cached=cache, exclude_study_uid=uid)
            study_preparation_seconds = time.perf_counter() - preparation_started
            if (
                not isinstance(study_prepared, dict)
                or study_prepared.get("outcome") != "prepared"
            ):
                raise SquintRunError("squint_capacity_recall_preparation_invalid")
            study_memory = {
                **study_memory,
                "prepared_recall": study_prepared,
                "view": {**study_memory["view"], "preparation_code": "prepared"},
            }
            study_preparation_source = (
                "study_excluded_projected"
                if study_prepared.get("runtime_indexes_rebuilt") is True
                else "study_excluded_recomputed"
            )
        record = infer_study(
            Path(args.root),
            uid,
            study_memory,
            deadline=deadline,
            exclude_same_study=mode == "capacity",
        )
        record["work"].update(
            {
                "study_time_budget_seconds": budget_seconds,
                "study_budget_deadline_exhausted": time.monotonic() >= deadline,
                "recall_preparation_seconds": study_preparation_seconds,
                "recall_preparation_source": study_preparation_source,
            }
        )
        if excluded is not None:
            prepared = study_memory.get("prepared_recall", {})
            record["capacity_exclusion"] = _capacity_exclusion_evidence(
                excluded,
                prepared,
                memory=memory,
                memory_digest=memory_digest,
                preparation_status=study_preparation_source,
            )
        else:
            record["capacity_exclusion"] = {
                "exclusion_status": "not_requested",
                "excluded_study_uid": None,
            }
        return record

    def submit_study(pool, uid: str, remaining_studies: int):
        deadline, budget = _study_budget_deadline(
            total_deadline, remaining_studies, worker_count
        )
        return pool.submit(infer_admitted_study, uid, deadline, budget)

    rows = []
    studies = []
    tallies = {label: Counter() for label in LABELS}
    # Submit at most worker_count studies. Completed arrays are released before
    # another study is admitted, irrespective of hidden-test cohort size.
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        pending = {}
        cursor = iter(uids)
        for _ in range(worker_count):
            uid = next(cursor, None)
            if uid is not None:
                pending[uid] = submit_study(pool, uid, len(uids))
        for completed, uid in enumerate(uids, start=1):
            record = pending.pop(uid).result()
            evidence_path = dump_json_atomic(
                output / "studies" / (uid + ".json"),
                record,
                compression_preset=0,
            )
            rows.append((uid, record["values"]))
            studies.append(
                {
                    "study_uid": uid,
                    **record["work"],
                    "capacity_exclusion": record["capacity_exclusion"],
                    "evidence_path": str(evidence_path.relative_to(output)),
                    "evidence_bytes": evidence_path.stat().st_size,
                }
            )
            for label, evidence in record["questions"].items():
                tally = (
                    "not_examined_budget"
                    if record.get("study_status") == "not_examined_budget"
                    else evidence["finding"]["outcome"]
                )
                tallies[label][tally] += 1
            del record
            next_uid = next(cursor, None)
            if next_uid is not None:
                pending[next_uid] = submit_study(pool, next_uid, len(uids) - completed)
    submission = None
    template = getattr(args, "diagnostic_submission_template", None)
    if template is not None:
        submission = write_submission(
            Path(template),
            output / "submission.csv",
            rows,
            source_provenance={
                "source_mode": "raw_squint_case_recall",
                "memory_revision": memory.get("revision", ""),
                "memory_manifest_sha256": memory_digest,
            },
        )
    result = {
        "schema": SCHEMA,
        "action": mode,
        "source_mode": "raw_squint_case_recall",
        "studies": len(studies),
        "memory_revision": memory.get("revision", ""),
        "memory_manifest_sha256": memory_digest,
        "recall_preparation": {
            "path": (
                str(preparation_path.relative_to(output))
                if preparation_path is not None
                else None
            ),
            "sha256": (
                hashlib.sha256(preparation_path.read_bytes()).hexdigest()
                if preparation_path is not None
                else None
            ),
            "bytes": preparation_path.stat().st_size
            if preparation_path is not None
            else 0,
            "cache_status": preparation_cache_status,
            "seconds": preparation_seconds,
            "schema": preparation_artifact_schema,
            "preparation_schema": (
                prepared.get("schema") if mode != "capacity" else None
            ),
            "artifact_source": preparation_artifact_source,
            "identity": preparation_identity,
            "source_cache_sha256": preparation_cache_sha256,
        },
        "per_question": {q: dict(c) for q, c in tallies.items()},
        "submission": submission,
        "cohort": cohort_receipt,
        "work": {
            "elapsed_seconds": time.perf_counter() - started,
            "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            * (1 if platform.system() == "Darwin" else 1024),
            "full_anatomy_runs": 0,
            "memory_loaded_once": True,
            "recall_preparation_seconds": preparation_seconds,
            "workers": worker_count,
            "studies": studies,
        },
    }
    _save(output / "receipt.json", result)
    return result
