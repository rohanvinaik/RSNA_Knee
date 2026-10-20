"""Teaching and diagnostic recall through the existing production command.

The retained-product route is explicitly a reference/capacity route. The acquired
input route consumes a declared cheap procedure before anatomical reconstruction.
No procedure here invents medical references, recall radii or submission scores.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import resource
import tempfile
import time
from collections import Counter
from collections.abc import Callable, Iterable, Mapping
from contextlib import closing
from dataclasses import replace
from pathlib import Path

from knee.diagnosis.models import Profile, Question, Snapshot, Trust


class DiagnosticRunError(ValueError):
    """A named failure at the diagnostic command boundary."""


def diagnostic_action(
    mode: str | None,
    has_products: bool,
    has_inputs: bool,
    has_memory: bool,
    has_labels: bool,
) -> str:
    """Select a command from explicit inputs; missing inputs never imply health.

    post: __return__ in ('disabled', 'teach', 'infer', 'capacity',
        'invalid_mode', 'ambiguous_source', 'missing_source', 'missing_memory',
        'missing_labels')
    """
    if mode is None:
        return "disabled"
    if mode not in ("teach", "infer", "capacity"):
        return "invalid_mode"
    if has_products and has_inputs:
        return "ambiguous_source"
    if not has_products and not has_inputs:
        return "missing_source"
    if not has_memory:
        return "missing_memory"
    if mode in ("teach", "capacity") and not has_labels:
        return "missing_labels"
    return mode


def add_arguments(parser: argparse.ArgumentParser, selection) -> None:
    """Attach diagnostic operation/source options to the one production CLI."""
    selection.add_argument(
        "--diagnostic-products",
        type=Path,
        help="retained H5/legacy object products; reference/capacity input",
    )
    parser.add_argument("--diagnostic-mode", choices=("teach", "infer", "capacity"))
    selection.add_argument(
        "--diagnostic-inputs",
        type=Path,
        help="explicit acquired/coarse query procedure declaration",
    )
    parser.add_argument(
        "--diagnostic-cohort",
        type=Path,
        help="explicit study cohort declaration for diagnostic source selection",
    )
    parser.add_argument(
        "--diagnostic-partition",
        help="opaque partition name selected from --diagnostic-cohort",
    )
    parser.add_argument(
        "--diagnostic-memory",
        type=Path,
        help="immutable case memory (output for teach, input otherwise)",
    )
    parser.add_argument(
        "--diagnostic-labels",
        type=Path,
        help="independent train.csv teaching/evaluation source, never inference features",
    )
    parser.add_argument(
        "--diagnostic-output",
        type=Path,
        help="fresh directory for ternary calls and exact recall evidence",
    )
    parser.add_argument("--diagnostic-revision", default="")
    parser.add_argument(
        "--diagnostic-pair-products",
        type=Path,
        help="retained full products paired with acquired descriptions during teaching",
    )
    parser.add_argument(
        "--diagnostic-questions",
        type=Path,
        help="explicit versioned question roles and measured bank selections",
    )
    parser.add_argument(
        "--diagnostic-trust",
        type=Path,
        help="explicit sourced per-case/question rational trust declarations",
    )
    parser.add_argument(
        "--diagnostic-cases",
        type=Path,
        help="explicit attributed case calls; teaching input, never a profile feature",
    )
    parser.add_argument(
        "--diagnostic-submission-template",
        type=Path,
        help="official CSV template; enables built-in HDC readout unless overridden",
    )


def _json_bytes(value) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _save(path: Path, value) -> None:
    """Publish a JSON record after its complete bytes are durable."""
    payload = _json_bytes(value)
    fd, name = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _verified_source(output: Path, uid: str, source: dict) -> dict:
    from knee.diagnosis.evidence import load_source, retain_source

    receipt = retain_source(output, uid, source)
    loaded = load_source(Path(receipt["manifest"]))
    if (
        loaded["manifest_sha256"] != receipt["sha256"]
        or loaded["archive_sha256"] != receipt["archive_sha256"]
    ):
        raise DiagnosticRunError("diagnostic_source_readback_mismatch")
    return receipt


def _study_source(
    args, output: Path, uid: str, profiles: tuple[Profile, ...], source: dict
) -> dict:
    products = getattr(args, "diagnostic_pair_products", None)
    if products is not None:
        from knee.diagnosis.pairing import pair_with_products, prepare_products

        prepared = getattr(args, "_diagnostic_pair_index", None)
        if prepared is None:
            prepared = prepare_products(products)
            args._diagnostic_pair_index = prepared
        source = {
            **source,
            "full_cheap_pairs": pair_with_products(profiles, uid, prepared),
        }
    if source.get("source_api") == "generated":
        existing_profiles = source.get("profiles")
        if existing_profiles is not None and existing_profiles != profiles:
            raise DiagnosticRunError("diagnostic_generated_profiles_mismatch")
        source["profiles"] = profiles
        source.setdefault("study_uid", uid)
    return _verified_source(output, uid, source)


def _case_declaration(path: Path | None, cohort, partition_name: str | None):
    """Read and index explicit case rows once, retaining exact source bytes."""
    if path is None:
        return {}, None, None
    try:
        raw = path.read_bytes()
        document = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise DiagnosticRunError("diagnostic_case_document_invalid") from error
    if (
        not isinstance(document, dict)
        or set(document) != {"schema", "cases"}
        or document.get("schema") != "knee.diagnostic-case-inputs/v1"
        or not isinstance(document.get("cases"), list)
    ):
        raise DiagnosticRunError("diagnostic_case_document_shape_invalid")
    rows_by_uid: dict[str, list[dict]] = {}
    references: set[tuple[str, str]] = set()
    for row in document["cases"]:
        if not isinstance(row, dict) or set(row) != {"study_uid", "subject", "calls"}:
            raise DiagnosticRunError("diagnostic_case_record_shape_invalid")
        uid = _safe_uid(row.get("study_uid"))
        subject = row.get("subject")
        calls = row.get("calls")
        if not isinstance(subject, str) or not subject.strip() or "\0" in subject:
            raise DiagnosticRunError("diagnostic_case_subject_invalid")
        if not isinstance(calls, list) or not calls:
            raise DiagnosticRunError("diagnostic_case_calls_required")
        reference = (uid, subject)
        if reference in references:
            raise DiagnosticRunError("diagnostic_case_profile_reference_duplicate")
        references.add(reference)
        # Validate the declaration's call syntax before any source factory runs.
        call_questions: set[str] = set()
        for call in calls:
            if not isinstance(call, dict) or set(call) - {
                "question",
                "digit",
                "source",
                "words",
            }:
                raise DiagnosticRunError("diagnostic_case_call_record_invalid")
            question = call.get("question")
            digit = call.get("digit")
            source = call.get("source")
            words = call.get("words", "")
            if (
                not isinstance(question, str)
                or not question.strip()
                or "\0" in question
            ):
                raise DiagnosticRunError("diagnostic_case_question_invalid")
            if question in call_questions:
                raise DiagnosticRunError("diagnostic_case_question_duplicate")
            call_questions.add(question)
            if type(digit) is not int or digit not in (-1, 0, 1):
                raise DiagnosticRunError("diagnostic_case_digit_invalid")
            if not isinstance(source, str) or not source.strip() or "\0" in source:
                raise DiagnosticRunError("diagnostic_case_call_source_invalid")
            if not isinstance(words, str):
                raise DiagnosticRunError("diagnostic_case_call_words_invalid")
        rows_by_uid.setdefault(uid, []).append(row)

    excluded: tuple[str, ...] = ()
    if cohort is not None:
        partitions = dict(cohort.partitions)
        all_declared = {uid for members in partitions.values() for uid in members}
        unknown = set(rows_by_uid) - all_declared
        if unknown:
            raise DiagnosticRunError("diagnostic_case_study_uid_not_in_cohort")
        selected_uids = tuple(partitions[partition_name])
        excluded = tuple(sorted(set(rows_by_uid) - set(selected_uids)))
    declaration = {
        "path": str(path.resolve()),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "case_count": len(document["cases"]),
        "excluded_cohort_uids": list(excluded),
    }
    return rows_by_uid, declaration, raw


def _import_study_cases(
    uid: str,
    profiles: tuple[Profile, ...],
    rows: list[dict],
    revision: str,
    declaration: dict,
) -> tuple[tuple, dict]:
    from knee.diagnosis.case_inputs import CaseInputError, import_case_inputs

    try:
        snapshot, receipt = import_case_inputs(
            {"schema": "knee.diagnostic-case-inputs/v1", "cases": rows},
            {uid: profiles},
            revision=revision,
        )
    except CaseInputError as error:
        raise DiagnosticRunError(f"diagnostic_{error.reason}") from error
    record = {
        "source": declaration,
        "imported_case_count": len(snapshot.cases),
        "import_receipt": receipt,
    }
    return snapshot.cases, record


def _explicit_case_profiles(
    profiles: tuple[Profile, ...], composed: tuple[Profile, ...], rows: list[dict]
) -> tuple[Profile, ...]:
    """Resolve explicit subjects across canonical and composed profile sets."""
    available = (*profiles, *composed)
    for row in rows:
        subject = row["subject"]
        matches = sum(profile.subject == subject for profile in available)
        if matches > 1:
            raise DiagnosticRunError("diagnostic_case_profile_subject_ambiguous")
    return available


def _timed_studies(studies: Iterable):
    """Yield each source item and close its iterator on every exit path."""
    iterator = iter(studies)
    try:
        while True:
            started = time.perf_counter()
            try:
                item = next(iterator)
            except StopIteration:
                return
            yield item, time.perf_counter() - started
    finally:
        close = getattr(iterator, "close", None)
        if callable(close):
            close()


def _source_work(source_mode: str, source: dict, source_elapsed: float) -> dict:
    if source.get("source_api") == "generated":
        runs = source.get("full_anatomy_runs")
        seconds = source.get("producer_seconds")
        if type(runs) is not int or runs < 0:
            raise DiagnosticRunError("diagnostic_generated_full_anatomy_runs_required")
        if type(seconds) is int:
            seconds_value = float(seconds)
        elif type(seconds) is float:
            seconds_value = seconds
        else:
            raise DiagnosticRunError("diagnostic_generated_producer_seconds_required")
        if not math.isfinite(seconds_value) or seconds_value < 0:
            raise DiagnosticRunError("diagnostic_generated_producer_seconds_required")
        return {
            "full_anatomy_runs": runs,
            "producer_seconds": seconds_value,
            "source_iteration_seconds": source_elapsed,
            "fresh_product_construction": True,
            "previously_generated_product_read": False,
        }
    if source_mode == "retained_full_products_reference_route":
        return {
            "full_anatomy_runs": 0,
            "producer_seconds": None,
            "source_iteration_seconds": source_elapsed,
            "fresh_product_construction": False,
            "previously_generated_product_read": True,
        }
    if source_mode == "declared_cheap_acquired_route":
        return {
            "full_anatomy_runs": 0,
            "producer_seconds": source_elapsed,
            "source_iteration_seconds": source_elapsed,
            "fresh_product_construction": False,
            "previously_generated_product_read": False,
        }
    raise DiagnosticRunError("diagnostic_source_work_mode_unknown")


def _validate_case_source_coverage(
    case_rows: dict[str, list[dict]], seen: set[str], declaration: dict | None
) -> None:
    excluded = (
        set(declaration.get("excluded_cohort_uids", ())) if declaration else set()
    )
    missing = set(case_rows) - seen - excluded
    if missing:
        raise DiagnosticRunError("diagnostic_case_study_uid_not_supplied")


def _product_paths(source: Path) -> tuple[Path, ...]:
    if source.is_file():
        return (source,)
    if not source.is_dir():
        raise DiagnosticRunError("diagnostic_product_source_missing")
    h5 = tuple(sorted(source.glob("*.h5")))
    # A normal H5 run also has manifest files; never read both as two studies.
    paths = h5 or tuple(
        sorted(p for p in source.glob("*.json.xz") if p.name != "receipt.json.xz")
    )
    if not paths:
        raise DiagnosticRunError("diagnostic_products_empty")
    return paths


def _product_studies(paths: Iterable[Path]):
    from knee.diagnosis.product_cases import profiles_from_product

    seen: set[str] = set()
    for path in paths:
        profiles = profiles_from_product(path, mode="full")
        source_ids = {p.source_id for p in profiles}
        if len(source_ids) != 1:
            raise DiagnosticRunError(
                "diagnostic_product_study_identity_missing_or_mixed"
            )
        uid = next(iter(source_ids))
        if uid in seen:
            raise DiagnosticRunError("diagnostic_product_duplicate_study")
        seen.add(uid)
        yield (
            uid,
            profiles,
            {"product": str(path.resolve()), "mode": "retained_full_product"},
        )
        del profiles


def _product_uids(
    paths: Iterable[Path],
) -> tuple[dict[str, list[Path]], tuple[str, ...]]:
    """Read structured product identity metadata without building Profiles."""
    from knee.encoding.product import open_product

    by_uid: dict[str, list[Path]] = {}
    available: list[str] = []
    for path in paths:
        with open_product(path) as product:
            manifest = product.manifest
            if not isinstance(manifest, dict):
                raise DiagnosticRunError("diagnostic_product_manifest_invalid")
            uid = (
                manifest.get("study_uid")
                or manifest.get("studyUID")
                or manifest.get("source_id")
            )
        uid = _safe_uid(uid)
        available.append(uid)
        by_uid.setdefault(uid, []).append(path)
    return by_uid, tuple(available)


def _selected_product_paths(
    paths: Iterable[Path], cohort, partition_name: str
) -> tuple[tuple[Path, ...], tuple[str, ...]]:
    from knee.diagnosis.cohort import partition_uids

    by_uid, available = _product_uids(paths)
    selected_uids = partition_uids(cohort, partition_name, available)
    return tuple(by_uid[uid][0] for uid in selected_uids), selected_uids


def _attach_source_group(
    profiles: tuple[Profile, ...], group: str
) -> tuple[Profile, ...]:
    """Carry a declared cohort group only as profile provenance."""
    if not group:
        return profiles
    attached = []
    for profile in profiles:
        provenance = dict(profile.provenance)
        if len(provenance) != len(profile.provenance):
            raise DiagnosticRunError("diagnostic_profile_provenance_duplicate")
        prior = provenance.get("source_group")
        if prior is not None and prior != group:
            raise DiagnosticRunError("diagnostic_source_group_conflict")
        if prior is None:
            attached.append(
                replace(
                    profile,
                    provenance=(*profile.provenance, ("source_group", group)),
                )
            )
        else:
            attached.append(profile)
    return tuple(attached)


def _cohort_source_record(
    source: dict,
    receipt: dict,
    uid: str,
    group: str,
    profiles: tuple[Profile, ...],
) -> dict:
    result = {
        **source,
        "cohort": {
            "source": receipt["source"],
            "sha256": receipt["sha256"],
            "partition": receipt["partition"],
            "selected_uids": receipt["selected_uids"],
            "study_uid": uid,
            "source_group": group,
        },
    }
    if "profiles" in source:
        result["profiles"] = profiles
    return result


def _question_profiles(profiles: tuple[Profile, ...], questions: tuple[Question, ...]):
    from knee.diagnosis.composition import CompositionError, compose_question_profile

    for question in questions:
        try:
            query = compose_question_profile(profiles, question)
        except CompositionError as error:
            detail = str(error)
            if detail == "no_source_profiles" or detail.startswith(
                "source_layouts_required:"
            ):
                yield question, None, detail
                continue
            raise
        yield question, query, ""


def _safe_uid(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value in (".", "..")
        or any(ord(character) in (0, 47, 92) for character in value)
    ):
        raise DiagnosticRunError("diagnostic_invalid_study_uid")
    return value


def _with_trust(snapshot: Snapshot, path: Path | None) -> Snapshot:
    if path is None:
        return snapshot
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict) or raw.get("schema") != "knee.diagnostic-trust/v1":
        raise DiagnosticRunError("diagnostic_trust_schema_unsupported")
    levels = raw.get("levels")
    if not isinstance(levels, list):
        raise DiagnosticRunError("diagnostic_trust_levels_required")
    case_questions = {
        (c.case_id, call.question) for c in snapshot.cases for call in c.calls
    }
    held = {(t.case_id, t.question): t for t in snapshot.trust}
    for item in levels:
        if not isinstance(item, dict):
            raise DiagnosticRunError("diagnostic_trust_record_invalid")
        case_id, question = item.get("case_id"), item.get("question")
        numerator, denominator, source = (
            item.get("numerator"),
            item.get("denominator"),
            item.get("source"),
        )
        if (
            not isinstance(case_id, str)
            or not isinstance(question, str)
            or (case_id, question) not in case_questions
            or type(numerator) is not int
            or type(denominator) is not int
            or denominator <= 0
            or not 0 <= numerator <= denominator
            or not isinstance(source, str)
            or not source
        ):
            raise DiagnosticRunError("diagnostic_trust_record_invalid")
        key = case_id, question
        if key in held:
            raise DiagnosticRunError("diagnostic_trust_duplicate_case_question")
        held[key] = Trust(case_id, question, numerator, denominator, source)
    return replace(snapshot, trust=tuple(held[k] for k in sorted(held)))


def _bank_set(names, registry: dict) -> dict:
    values = tuple(names)
    identity = hashlib.sha256(_json_bytes(values)).hexdigest()
    existing = registry.setdefault(identity, list(values))
    if existing != list(values):
        raise RuntimeError("diagnostic_bank_set_digest_collision")
    return {"bank_set": identity, "count": len(values)}


def _compact_evidence(record: dict, registry: dict) -> dict:
    """Retain evidence exactly, referencing each repeated bank set once."""
    result = dict(record)
    if "selected_banks" in result:
        result["selected_banks"] = _bank_set(result["selected_banks"], registry)
    for key in ("case_terms", "censor_terms"):
        rows = []
        for row in result.get(key, []):
            item = dict(row)
            if "common_speaking_banks" in item:
                item["common_speaking_banks"] = _bank_set(
                    item["common_speaking_banks"], registry
                )
            rows.append(item)
        if key in result:
            result[key] = rows
    return result


def _evaluation(outcome: str, expected: int | None) -> str:
    if expected is None:
        return "unlabeled"
    if outcome == "proposal":
        return "proposed"
    if outcome not in ("present", "absent"):
        return "abstained"
    return "identified" if (outcome == "present") == bool(expected) else "wrong"


def _questions(path: Path | None = None):
    from knee.diagnosis.declarations import QUESTIONS

    if path is None:
        return QUESTIONS
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict) or raw.get("schema") != "knee.diagnostic-questions/v1":
        raise DiagnosticRunError("diagnostic_question_schema_unsupported")
    rows = raw.get("questions")
    if not isinstance(rows, list):
        raise DiagnosticRunError("diagnostic_question_records_required")
    originals = {q.question_id: q for q in QUESTIONS}
    known_roles = {role for q in QUESTIONS for role in q.objects}
    declared = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) - {
            "question_id",
            "objects",
            "banks",
            "bank_prefixes",
            "context_keys",
        }:
            raise DiagnosticRunError("diagnostic_question_record_invalid")
        name = row.get("question_id")
        if not isinstance(name, str) or name not in originals:
            raise DiagnosticRunError("diagnostic_question_unknown")
        if name in declared:
            raise DiagnosticRunError("diagnostic_question_duplicate")
        values = {}
        for key in ("objects", "banks", "bank_prefixes", "context_keys"):
            value = row.get(key, [])
            if (
                not isinstance(value, list)
                or any(not isinstance(v, str) or not v for v in value)
                or len(set(value)) != len(value)
            ):
                raise DiagnosticRunError("diagnostic_question_field_invalid:" + key)
            values[key] = tuple(value)
        if not values["objects"] or not set(values["objects"]) <= known_roles:
            raise DiagnosticRunError("diagnostic_question_objects_invalid")
        if not values["banks"] and not values["bank_prefixes"]:
            raise DiagnosticRunError("diagnostic_question_banks_required")
        declared[name] = Question(name, "diagnosis/" + name, **values)
    return tuple(declared.get(q.question_id, q) for q in QUESTIONS)


def run_diagnostic_cli(
    args,
    *,
    study_source: Callable[
        [tuple[str, ...] | None], Iterable[tuple[str, tuple[Profile, ...], dict]]
    ]
    | None = None,
    source_mode: str | None = None,
    probability_readout: Callable[[Mapping[str, dict]], Mapping[str, object]]
    | None = None,
) -> dict:
    """Run one requested operation, loading memory once and releasing each study."""
    mode = getattr(args, "diagnostic_mode", None)
    case_path = getattr(args, "diagnostic_cases", None)
    products_path = getattr(args, "diagnostic_products", None)
    inputs_path = getattr(args, "diagnostic_inputs", None)
    template_path = getattr(args, "diagnostic_submission_template", None)
    builtin_readout = False
    builtin_readout_policy = None
    builtin_readout_function = None
    readout_active = probability_readout is not None
    if study_source is not None and (
        products_path is not None or inputs_path is not None
    ):
        raise DiagnosticRunError("diagnostic_ambiguous_source")
    if template_path is None and probability_readout is not None:
        raise DiagnosticRunError("diagnostic_readout_and_template_must_be_paired")
    if template_path is not None and mode == "teach":
        raise DiagnosticRunError("diagnostic_readout_requires_query_mode")
    if template_path is not None and probability_readout is None:
        from knee.diagnosis.readout import POLICY_ID, readout_study

        builtin_readout_function = readout_study
        builtin_readout = True
        builtin_readout_policy = POLICY_ID
        readout_active = True
    action = diagnostic_action(
        mode,
        products_path is not None or study_source is not None,
        inputs_path is not None,
        args.diagnostic_memory is not None,
        args.diagnostic_labels is not None or case_path is not None,
    )
    if action not in ("teach", "infer", "capacity"):
        raise DiagnosticRunError("diagnostic_" + action)
    if case_path is not None and action != "teach":
        raise DiagnosticRunError("diagnostic_cases_require_teach_mode")
    cohort_path = getattr(args, "diagnostic_cohort", None)
    partition_name = getattr(args, "diagnostic_partition", None)
    if (cohort_path is None) != (partition_name is None):
        raise DiagnosticRunError("diagnostic_cohort_and_partition_must_be_paired")
    if cohort_path is not None and not isinstance(partition_name, str):
        raise DiagnosticRunError("diagnostic_cohort_and_partition_must_be_paired")
    selected_partition_name = (
        partition_name if isinstance(partition_name, str) else None
    )
    cohort = None
    cohort_receipt = None
    selected_uids: tuple[str, ...] = ()
    if cohort_path is not None:
        from knee.diagnosis.cohort import CohortError, load_cohort

        try:
            cohort = load_cohort(Path(cohort_path))
        except CohortError as error:
            raise DiagnosticRunError(f"diagnostic_{error}") from error
        partitions = dict(cohort.partitions)
        assert selected_partition_name is not None
        if selected_partition_name not in partitions:
            # Use the public selection API so unknown names keep its named error.
            from knee.diagnosis.cohort import partition_uids

            try:
                partition_uids(cohort, selected_partition_name, ())
            except CohortError as error:
                raise DiagnosticRunError(f"diagnostic_{error}") from error
            raise DiagnosticRunError("diagnostic_cohort_partition_unavailable")
        selected_uids = partitions[selected_partition_name]
        cohort_receipt = {
            "source": cohort.source,
            "sha256": cohort.sha256,
            "partition": selected_partition_name,
            "selected_uids": list(selected_uids),
        }
    case_rows, case_declaration, case_bytes = _case_declaration(
        case_path, cohort, partition_name
    )
    if getattr(args, "diagnostic_pair_products", None) is not None and (
        action != "teach" or args.diagnostic_inputs is None
    ):
        raise DiagnosticRunError("diagnostic_pairing_requires_acquired_teaching")
    if getattr(args, "draw", False):
        raise DiagnosticRunError("diagnostic_drawing_is_separate_development_work")
    if args.diagnostic_output is None:
        raise DiagnosticRunError("diagnostic_output_required")
    out = Path(args.diagnostic_output)
    out.mkdir(parents=True, exist_ok=False)
    if case_bytes is not None and case_declaration is not None:
        retained_case_source = out / "teaching-case-source.json"
        retained_case_source.write_bytes(case_bytes)
        case_declaration = {
            **case_declaration,
            "retained": str(retained_case_source.resolve()),
        }
    started = time.perf_counter()
    questions = _questions(getattr(args, "diagnostic_questions", None))
    (out / "studies").mkdir()

    bank_sets: dict = {}
    labels = None
    label_source = None
    if args.diagnostic_labels is not None and action in ("teach", "capacity"):
        from knee.diagnosis.teaching import labels_from_csv

        labels = labels_from_csv(args.diagnostic_labels)
        label_bytes = args.diagnostic_labels.read_bytes()
        (out / "teaching-source.csv").write_bytes(label_bytes)
        label_source = {
            "original": str(args.diagnostic_labels.resolve()),
            "retained": str((out / "teaching-source.csv").resolve()),
            "sha256": hashlib.sha256(label_bytes).hexdigest(),
        }
    if study_source is not None:
        selected = selected_uids if cohort is not None else None
        try:
            studies = study_source(selected)
        except Exception as error:
            raise DiagnosticRunError(
                "diagnostic_study_source_factory_failed"
            ) from error
        source_mode = source_mode or "generated_full_reference"
        if not isinstance(source_mode, str) or not source_mode.strip():
            raise DiagnosticRunError("diagnostic_generated_source_mode_invalid")
    elif products_path is not None:
        paths = _product_paths(Path(products_path))
        if cohort is not None:
            from knee.diagnosis.cohort import CohortError

            assert partition_name is not None and cohort_receipt is not None

            try:
                selected_paths, selected_uids = _selected_product_paths(
                    paths, cohort, partition_name
                )
            except CohortError as error:
                raise DiagnosticRunError(f"diagnostic_{error}") from error
            cohort_receipt["selected_uids"] = list(selected_uids)
            studies = _product_studies(selected_paths)
        else:
            studies = _product_studies(paths)
        source_mode = "retained_full_products_reference_route"
    elif inputs_path is not None:
        from knee.diagnosis.inputs import acquired_studies

        if cohort is None:
            studies = acquired_studies(args)
        else:
            studies = acquired_studies(
                args, cohort=cohort, partition_name=partition_name
            )
        source_mode = "declared_cheap_acquired_route"
    else:
        raise DiagnosticRunError("diagnostic_missing_source")
    from knee.diagnosis.store import read_store, write_store

    if action == "teach":
        if not args.diagnostic_revision:
            raise DiagnosticRunError("diagnostic_teaching_revision_required")
        from knee.diagnosis.teaching import teach_from_labels

        cases = []
        ledgers: list[dict] = []
        seen = set()
        work_by_study = []
        full_anatomy_runs = 0
        producer_seconds: float | None = None
        source_iteration_seconds = 0.0
        with closing(_timed_studies(studies)) as timed_studies:
            for (uid, profiles, source), elapsed in timed_studies:
                uid = _safe_uid(uid)
                if (
                    study_source is not None
                    and cohort is not None
                    and uid not in set(selected_uids)
                ):
                    raise DiagnosticRunError(
                        "diagnostic_generated_study_outside_partition"
                    )
                if study_source is not None:
                    if not isinstance(source, dict):
                        raise DiagnosticRunError(
                            "diagnostic_generated_source_record_invalid"
                        )
                    if source.get("source_api", "generated") != "generated":
                        raise DiagnosticRunError(
                            "diagnostic_generated_source_api_invalid"
                        )
                    source = {
                        **source,
                        "source_api": "generated",
                        "source_mode": source_mode,
                    }
                if cohort is not None:
                    from knee.diagnosis.cohort import source_group_for

                    assert cohort_receipt is not None

                    group = source_group_for(cohort, uid)
                    profiles = _attach_source_group(profiles, group)
                    source = _cohort_source_record(
                        source, cohort_receipt, uid, group, profiles
                    )
                source_work = _source_work(source_mode, source, elapsed)
                source = _study_source(args, out, uid, profiles, source)
                if uid in seen:
                    raise DiagnosticRunError("diagnostic_duplicate_study")
                seen.add(uid)
                full_anatomy_runs += source_work["full_anatomy_runs"]
                if source_work["producer_seconds"] is not None:
                    if producer_seconds is None:
                        producer_seconds = 0.0
                    producer_seconds += source_work["producer_seconds"]
                source_iteration_seconds += source_work["source_iteration_seconds"]
                work_by_study.append({"study_uid": uid, **source_work})
                composed = tuple(
                    profile
                    for _, profile, _ in _question_profiles(profiles, questions)
                    if profile is not None
                )
                taught, ledger = teach_from_labels(
                    {uid: composed},
                    {uid: labels[uid]} if labels is not None and uid in labels else {},
                    revision=args.diagnostic_revision,
                )
                cases.extend(taught.cases)
                explicit_case_count = 0
                case_record = None
                if uid in case_rows:
                    explicit_cases, case_record = _import_study_cases(
                        uid,
                        _explicit_case_profiles(profiles, composed, case_rows[uid]),
                        case_rows[uid],
                        args.diagnostic_revision,
                        case_declaration,
                    )
                    cases.extend(explicit_cases)
                    explicit_case_count = len(explicit_cases)
                ledgers.append(
                    {
                        "study_uid": uid,
                        "source": source,
                        "source_work": source_work,
                        "teaching": ledger,
                        "explicit_cases": case_record,
                        "explicit_case_count": explicit_case_count,
                    }
                )
                del profiles, composed, taught
        if not seen:
            raise DiagnosticRunError("diagnostic_no_studies")
        _validate_case_source_coverage(case_rows, seen, case_declaration)
        if study_source is not None:
            missing = set(selected_uids) - seen if cohort is not None else set()
            if missing:
                raise DiagnosticRunError(
                    "diagnostic_selected_study_missing_from_source"
                )
        snapshot = _with_trust(
            Snapshot(args.diagnostic_revision, tuple(cases)), args.diagnostic_trust
        )
        from knee.diagnosis.coverage import coverage_for_snapshot
        from knee.objects.assignments import OBJECT_CODES

        catalogue = tuple(name for name, code in OBJECT_CODES.items() if code != 0)
        coverage = coverage_for_snapshot(snapshot, questions, catalogue)
        receipt = write_store(Path(args.diagnostic_memory), snapshot)
        _save(
            out / "teaching-ledger.json",
            {
                "studies": ledgers,
                "label_source": label_source,
                "case_declaration": case_declaration,
                "coverage": coverage,
            },
        )
        result = {
            "schema": "knee.diagnostic-run/v1",
            "action": action,
            "source_mode": source_mode,
            "studies": len(seen),
            "cases": len(cases),
            "explicit_cases": sum((row["explicit_case_count"] for row in ledgers), 0),
            "coverage": str((out / "teaching-ledger.json").resolve()),
            "store": receipt,
            "memory": str(Path(args.diagnostic_memory).resolve()),
            "case_declaration": case_declaration,
        }
        if cohort_receipt is not None:
            result["cohort"] = cohort_receipt
    else:
        from knee.diagnosis.declarations import select_question_banks
        from knee.diagnosis.retrieval import prepare_snapshot, recall

        snapshot = _with_trust(
            read_store(Path(args.diagnostic_memory)), args.diagnostic_trust
        )
        prepared_memory = prepare_snapshot(snapshot)
        tallies = {q.question_id: Counter() for q in questions}
        seen = set()
        work_by_study = []
        full_anatomy_runs = 0
        producer_seconds: float | None = None
        source_iteration_seconds = 0.0
        probability_rows = []
        with closing(_timed_studies(studies)) as timed_studies:
            for (uid, profiles, source), elapsed in timed_studies:
                uid = _safe_uid(uid)
                if (
                    study_source is not None
                    and cohort is not None
                    and uid not in set(selected_uids)
                ):
                    raise DiagnosticRunError(
                        "diagnostic_generated_study_outside_partition"
                    )
                if study_source is not None:
                    if not isinstance(source, dict):
                        raise DiagnosticRunError(
                            "diagnostic_generated_source_record_invalid"
                        )
                    if source.get("source_api", "generated") != "generated":
                        raise DiagnosticRunError(
                            "diagnostic_generated_source_api_invalid"
                        )
                    source = {
                        **source,
                        "source_api": "generated",
                        "source_mode": source_mode,
                    }
                if cohort is not None:
                    from knee.diagnosis.cohort import source_group_for

                    assert cohort_receipt is not None

                    group = source_group_for(cohort, uid)
                    profiles = _attach_source_group(profiles, group)
                    source = _cohort_source_record(
                        source, cohort_receipt, uid, group, profiles
                    )
                source_work = _source_work(source_mode, source, elapsed)
                source = _study_source(args, out, uid, profiles, source)
                if uid in seen:
                    raise DiagnosticRunError("diagnostic_duplicate_study")
                seen.add(uid)
                full_anatomy_runs += source_work["full_anatomy_runs"]
                if source_work["producer_seconds"] is not None:
                    if producer_seconds is None:
                        producer_seconds = 0.0
                    producer_seconds += source_work["producer_seconds"]
                source_iteration_seconds += source_work["source_iteration_seconds"]
                work_by_study.append({"study_uid": uid, **source_work})
                records = {}
                readout_records = {}
                for question, query, missing in _question_profiles(profiles, questions):
                    if query is None:
                        evidence = {
                            "outcome": "unresolved_missing_reading",
                            "reason": missing,
                            "question_id": question.question_id,
                            "selected_banks": [],
                        }
                    else:
                        selected = select_question_banks(question, query.bundle)
                        if not selected:
                            # An explicit exact bank missing from the query layout
                            # must not fall back to a broader prefix in recall.
                            evidence = {
                                "outcome": "incompatible_encoding",
                                "reason": "question_banks_not_present_in_query_layout",
                                "question_id": question.question_id,
                                "selected_banks": [],
                            }
                        else:
                            # Freeze the exact selection; recall must not re-select.
                            declared = replace(
                                question, banks=selected, bank_prefixes=()
                            )
                            evidence = recall(
                                query,
                                declared,
                                prepared_memory,
                                exclude_study_uid=uid if action == "capacity" else "",
                                exclude_source_group=(
                                    dict(query.provenance).get(
                                        "source_group",
                                        dict(query.context).get("source_group", ""),
                                    )
                                    if action == "capacity"
                                    else ""
                                ),
                            )
                    outcome = evidence["outcome"]
                    if not isinstance(outcome, str):
                        raise DiagnosticRunError("diagnostic_recall_outcome_invalid")
                    tally = tallies[question.question_id]
                    tally[outcome] += 1
                    evidence["call"] = (
                        1 if outcome == "present" else -1 if outcome == "absent" else 0
                    )
                    if labels is not None and action == "capacity":
                        expected = labels.get(uid, {}).get(question.question_id)
                        assessment = _evaluation(outcome, expected)
                        evidence["evaluation"] = {
                            "expected": expected,
                            "assessment": assessment,
                            "same_study_excluded": True,
                        }
                        tally[assessment] += 1
                    readout_records[question.question_id] = {
                        key: value
                        for key, value in evidence.items()
                        if key != "evaluation"
                    }
                    records[question.question_id] = _compact_evidence(
                        evidence, bank_sets
                    )
                readout_details = None
                if readout_active:
                    selected_readout = (
                        builtin_readout_function
                        if builtin_readout
                        else probability_readout
                    )
                    if selected_readout is None:
                        raise DiagnosticRunError(
                            "diagnostic_probability_readout_unavailable"
                        )
                    try:
                        readout_result = selected_readout(readout_records)
                        if builtin_readout:
                            probabilities, readout_details = readout_result
                        else:
                            probabilities = readout_result
                    except Exception as error:
                        raise DiagnosticRunError(
                            "diagnostic_probability_readout_failed"
                        ) from error
                    if not isinstance(probabilities, Mapping):
                        raise DiagnosticRunError(
                            "diagnostic_probability_readout_invalid"
                        )
                    if builtin_readout and not isinstance(readout_details, Mapping):
                        raise DiagnosticRunError(
                            "diagnostic_probability_readout_details_invalid"
                        )
                    probability_rows.append((uid, probabilities))
                record = {
                    "schema": "knee.diagnostic-study/v1",
                    "study_uid": uid,
                    "source": source,
                    "memory_revision": snapshot.revision,
                    "questions": records,
                    "competition_readout": (
                        builtin_readout_policy
                        if builtin_readout
                        else "caller_supplied"
                        if readout_active
                        else "not_declared"
                    ),
                }
                if builtin_readout:
                    record["readout"] = readout_details
                _save(out / "studies" / (uid + ".json"), record)
                del profiles, query, records, record
        if not seen:
            raise DiagnosticRunError("diagnostic_no_studies")
        if study_source is not None:
            missing = set(selected_uids) - seen if cohort is not None else set()
            if missing:
                raise DiagnosticRunError(
                    "diagnostic_selected_study_missing_from_source"
                )
        _save(out / "bank-sets.json", bank_sets)
        submission_receipt = None
        if readout_active:
            from knee.diagnosis.submission import write_submission

            assert template_path is not None

            callback_name = (
                ""
                if builtin_readout
                else ".".join(
                    part
                    for part in (
                        getattr(probability_readout, "__module__", None),
                        getattr(probability_readout, "__qualname__", None),
                    )
                    if part
                )
            )
            submission_receipt = write_submission(
                Path(template_path),
                out / "submission.csv",
                probability_rows,
                source_provenance={
                    "readout_callback": (
                        "knee.diagnosis.readout:readout_study"
                        if builtin_readout
                        else callback_name or "caller_supplied_callable"
                    ),
                    "evidence_schema": "knee.diagnostic-study/v1",
                    "memory_revision": snapshot.revision,
                    **(
                        {"readout_policy": builtin_readout_policy}
                        if builtin_readout
                        else {}
                    ),
                },
            )
            _save(out / "submission-receipt.json", submission_receipt)
        result = {
            "schema": "knee.diagnostic-run/v1",
            "action": action,
            "source_mode": source_mode,
            "studies": len(seen),
            "memory_revision": snapshot.revision,
            "per_question": {name: dict(counts) for name, counts in tallies.items()},
            "same_study_excluded": action == "capacity",
            "competition_readout": (
                builtin_readout_policy
                if builtin_readout
                else "caller_supplied"
                if readout_active
                else "not_declared"
            ),
        }
        if submission_receipt is not None:
            result["submission"] = submission_receipt
        if cohort_receipt is not None:
            result["cohort"] = cohort_receipt
    result["work"] = {
        "elapsed_seconds": time.perf_counter() - started,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        * (1 if platform.system() == "Darwin" else 1024),
        "full_anatomy_runs": full_anatomy_runs,
        "producer_seconds": producer_seconds,
        "source_iteration_seconds": source_iteration_seconds,
        "studies": work_by_study,
        "source_mode": source_mode,
        "fresh_product_construction": study_source is not None,
        "previously_generated_product_read": (
            source_mode == "retained_full_products_reference_route"
        ),
        "memory_loaded_once": action != "teach",
    }
    _save(out / "receipt.json", result)
    return result
