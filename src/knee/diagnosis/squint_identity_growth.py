"""Signed growth of identity memory from one frozen parent (CLASSICAL_AI_BUILD_DESIGN §7).

A growth round reads ONE frozen parent memory and a list of candidates. Production
inference supplies them (``harvest_candidates``): one per located object holding a
cheap profile, with its regions and the anatomical sanity record exactly as the
inference run wrote them. A candidate memory snapshot can supply them as well
(``candidates_from_memory``). A candidate's subject is the locator's proposal,
never an identity verdict.

Every candidate is scored against the frozen parent alone, through the existing
signed identity recall, with one shared preparation per held-out exclusion. A
candidate's study is excluded from comparison and opposing envelopes whenever any
parent record of any kind (``cases`` or ``object_identity_cases``) comes from it;
a study absent from every record kind shares the unexcluded preparation, which
holds exactly the same population. Nothing admitted in a round speaks in it. A
round streams: one inference record is decoded at a time (a real one can decode
to hundreds of MB), and only decisions and admissions outlive their candidates.

Admission (§§7.1-7.2): signed recall identifies the candidate as its own proposed
subject and no negative case speaks against it; the recorded sanity is plausible,
with at least one recorded ``supported_*`` check and no ``reversed_*`` check. A
pass is a law check on location: it is kept as location support, never as tissue.
Unknown-only anatomy keeps a proposal: not admitted, not rejected, never a
negative. The legacy recall field ``admitted`` is not a publication warrant.

Scope: the views whose banks took part in the comparisons speaking for the
identity, minus any view through which a negative case of that identity speaks.
No usable view, or malformed scope, is a named refusal, never a whole-case call.
Joint recognition does not require each view to recognize on its own.

The child keeps every parent record (signed cases, alternatives, calls, full
tables, prior growth rounds) and adds each admission to ``cases`` with a confirm
call on exactly its admitted views. An admission is recognition-derived: it carries
its lineage and is never an independent visual or clinical call. It has no full
profile; none is manufactured. Without a label file it has no condition calls.

Condition teaching (CLASSICAL_AI_BUILD_DESIGN §§5.1, 8): given the competition's
``train.csv``, each admitted inference case's study row is carried onto it through
``squint_memory.carry_condition_calls`` after every decision is made. A positive
for a condition implicating the object is a positive presentation in every view of
its admission and its normal labels speak through those views alike; a blank label
makes no call; a Fracture or Contusion positive stays
``positive_condition_presentation`` (some bone, not which), since no localized call
exists here. The calls keep ``train.csv`` (path, digest, column, study) as their
source, apart from the identity lineage. Only the rows of studies with an admitted
inference case are parsed; a study with no row (a test study) gets no calls, by
name. Labels never reach harvesting, recall, admission or query construction, so
the decisions file is the same bytes with or without them. A memory candidate
enters as its source memory holds it, its calls included.

Configuration teaching (CLASSICAL_AI_BUILD_DESIGN §§5.1, 11): a study in which a
round admits an object gets its whole-condition configuration cases built by the
seed's own scoped builder (``squint_bootstrap._rebuilt_configurations``) when the
round carried its ``train.csv`` row, and rebuilt when the parent already holds
configuration cases for it (an earlier round's or the teaching set's): one
``diagnosis/<condition>`` case per labelled question, composed from every object
case of that study in the child, the parent's and this round's, each role on
the views where its identity holds, with missing roles explicit. The call is
the official label alone, the carried row's or else the parent's ledger row's,
at ``study_condition_configuration`` scope; a blank label makes no case and the
labels never enter the composition, so a Fracture or Contusion positive stays a
study-level configuration call and relabels no object. Every role keeps its own
provenance: the recognition-derived lineage of an admission, or the visual call
of a seed. Only the clinical call is official. A rebuilt case keeps its id and
replaces the parent's version in the child only, recording that version's
digest and round, so one configuration case per study and condition is ever
live. A study in which nothing was admitted keeps its configuration cases byte
for byte, and the parent memory is never changed. A carried row joins the
child's ``label_ledger``; one differing from the parent's row is refused by
name.

Held-out studies: a candidate from a held-out study is never scored or admitted
(state ``held_out``) and its labels are never read. The held-out set is the
round's own list joined with the one its parent's growth block records, so every
child keeps its parent's held-out studies. It is recorded, sorted with the digest
of that list, in the decisions file and in the child's growth block.

Decision states: ``admitted``; ``proposal`` (identified but anatomy unknown, or
nothing identified: the reason says which); ``blocked`` (a known anatomical
contradiction); ``conflict`` (recognized as another identity, which is named, or
recall's own unresolved conflict); ``opposed`` (a negative case of the proposed
identity speaks and nothing speaks for any identity); ``duplicate`` (the parent
already holds this case or a record of this object of this study); ``refused`` (a
named refusal, including ``admission_scope_unresolved``); ``held_out`` (the
candidate's study is held out of this round).
"""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import lzma
import os
import re
import tempfile
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

from knee.diagnosis.squint_bootstrap import (
    SquintBootstrapError,
    _rebuilt_configurations,
)
from knee.diagnosis.squint_identity import (
    SANITY_SCHEMA,
    identity_condition_views,
    prepare_identity,
    recall_identity,
)
from knee.diagnosis.squint_interfaces import parse_territory_bank_name
from knee.diagnosis.squint_memory import (
    FULL_CONTEXTS_SCHEMA,
    FULL_PAYLOADS_SCHEMA,
    MemorySnapshot,
    SquintMemoryError,
    _json_sha256,
    _link_configuration_full_profiles,
    _validate_memory,
    carry_condition_calls,
    load_memory_snapshot,
    save_memory,
)
from knee.study.tables import LABELS

# v1 was the withdrawn prototype's block (candidate_states/admissions); a growth
# round record now lives in ``rounds``.
GROWTH_SCHEMA = "knee.object-identity-growth/v2"
DECISIONS_SCHEMA = "knee.identity-admission-decisions/v1"
STUDY_SCHEMA = "knee.squint-study/v1"
INFERENCE_SOURCE = "squint-inference"
MEMORY_SOURCE = "candidate-memory"
RECOGNITION_KIND = "recognition_derived_identity"
# A configuration role's identity confirmed by the seed's visual call.
SEED_CALL_KIND = "seed_visual_call"
RECOGNIZER = "knee.diagnosis.squint_identity.recall_identity"
READER = (
    "knee.diagnosis.squint_identity_growth (recognition-derived; not a visual call)"
)
DECISIONS_FILE = "admission-decisions.json"
CHILD_DIRECTORY = "memory"
HELD_OUT_SCHEMA = "knee.identity-growth-held-out/v1"
CONDITION_TEACHING_SCHEMA = "knee.identity-growth-condition-teaching/v1"
CONFIGURATION_TEACHING_SCHEMA = "knee.identity-growth-configuration-teaching/v1"
LABEL_SOURCE = "train.csv"
STATES = (
    "admitted",
    "proposal",
    "blocked",
    "conflict",
    "opposed",
    "duplicate",
    "refused",
    "held_out",
)
# The competition's train.csv header, exactly as squint_memory._read_labels reads it.
_LABEL_COLUMNS = ("StudyInstanceUID", "Report", *LABELS)
_PROFILE_SCHEMA = "knee.squint-profile/v1"
_SANITY_STATUSES = ("plausible", "unknown", "contradicted")
_RUNTIME_KEYS = frozenset(
    {"full_profile_retention", "view", "prepared_recall", "memory_manifest_sha256"}
)
_DECISION_KEYS = (
    "candidate_id",
    "study_uid",
    "subject",
    "state",
    "reason",
    "recognized_identity",
    "views",
    "support",
    "regions",
    "source",
)
_SHA = re.compile(r"[0-9a-f]{64}")


class IdentityGrowthError(ValueError):
    """A named refusal; the parent and every source stay untouched."""

    def __init__(self, code: str, detail: str | None = None):
        self.code = code
        self.detail = detail
        super().__init__(code if detail is None else f"{code}: {detail}")


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_sha(value: object) -> bool:
    return isinstance(value, str) and _SHA.fullmatch(value) is not None


def _rows(value: object) -> list | None:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return None


def _window(value: object) -> list[int] | None:
    """A half-open tile window ``[z0, z1, r0, r1, c0, c1]`` of plain ints, or None."""
    if (
        not isinstance(value, (list, tuple))
        or len(value) != 6
        or not all(type(item) is int for item in value)
    ):
        return None
    z0, z1, r0, r1, c0, c1 = value
    if not (0 <= z0 < z1 and 0 <= r0 < r1 and 0 <= c0 < c1):
        return None
    return list(value)


def record_sha256(record: object) -> str:
    """Digest of a decoded study record. Records are written allowing NaN."""
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


# ------------------------------------------------------------------ candidates


def _located_regions(located: Mapping[str, Any], label: str) -> list[dict[str, Any]]:
    regions = _rows(located.get("regions"))
    if not regions:
        raise IdentityGrowthError("study_record_regions_missing", label)
    result = []
    for region in regions:
        if not isinstance(region, Mapping):
            raise IdentityGrowthError("study_record_region_invalid", label)
        window = _window(region.get("window", region.get("source_window")))
        series_uid = region.get("series_uid")
        if window is None or not _text(series_uid):
            raise IdentityGrowthError("study_record_region_invalid", label)
        result.append({"series_uid": series_uid, "window": window})
    return result


def _harvest(
    pairs: Iterable[tuple[Mapping[str, Any], str | None]],
) -> Iterator[dict[str, Any]]:
    """Candidates of each (record, file digest or None), one record alive at a time."""
    studies: set[str] = set()
    for index, (record, digest) in enumerate(pairs):
        if not isinstance(record, Mapping) or record.get("schema") != STUDY_SCHEMA:
            raise IdentityGrowthError("study_record_invalid", str(index))
        uid = record.get("study_uid")
        revision = record.get("memory_revision")
        objects = record.get("objects")
        if not _text(uid) or not _text(revision) or not isinstance(objects, Mapping):
            raise IdentityGrowthError("study_record_invalid", str(index))
        if uid in studies:
            raise IdentityGrowthError("duplicate_study_record", uid)
        studies.add(uid)
        source = {
            "kind": INFERENCE_SOURCE,
            "record_sha256": record_sha256(record) if digest is None else digest,
            "record_sha256_scope": "decoded_json" if digest is None else "file_bytes",
            "memory_revision": revision,
        }
        for subject in sorted(objects):
            located = objects[subject]
            if not isinstance(located, Mapping):
                continue
            profile = located.get("profile")
            if not isinstance(profile, Mapping) or not isinstance(
                profile.get("banks"), Mapping
            ):
                continue
            if not _text(subject) or subject.startswith("diagnosis/"):
                raise IdentityGrowthError("study_record_subject_invalid", uid)
            yield {
                "case_id": f"located:{uid}:{subject}:{revision}",
                "study_uid": uid,
                "subject": subject,
                "profile": copy.deepcopy(profile),
                "regions": _located_regions(located, f"{uid}:{subject}"),
                "sanity": copy.deepcopy(located.get("sanity")),
                "source": dict(source),
            }


def _paired(
    records: Iterable[Mapping[str, Any]], digests: Iterable[str]
) -> Iterator[tuple[Mapping[str, Any], str]]:
    """Each record with its digest, consumed in lockstep; unequal lengths refuse."""
    remaining = iter(digests)
    for record in records:
        digest = next(remaining, None)
        if not _is_sha(digest):
            raise IdentityGrowthError("record_sha256s_invalid")
        yield record, digest
    if next(remaining, None) is not None:
        raise IdentityGrowthError("record_sha256s_invalid")


def harvest_candidates(
    study_records: Iterable[Mapping[str, Any]],
    *,
    record_sha256s: Iterable[str] | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield one candidate per located object holding a cheap profile, in record order.

    Each candidate holds ``case_id`` (``located:<study_uid>:<subject>:<memory
    revision>``), ``study_uid``, ``subject`` (the located name, a proposal only),
    ``profile``, ``regions`` (series_uid and half-open tile window), ``sanity``
    exactly as recorded, and its ``source`` record. ``record_sha256s`` are the
    exact file-byte digests of the records, when the caller read them from disk;
    otherwise each decoded record is digested (``record_sha256``). Recall, values
    and questions already in a record are never read: the round scores afresh.
    Records are consumed lazily, so a stream of them holds one at a time.
    """
    if record_sha256s is None:
        yield from _harvest((record, None) for record in study_records)
    else:
        yield from _harvest(_paired(study_records, record_sha256s))


def inference_record_paths(directory: Path) -> list[Path]:
    """The per-study record files of one diagnostic output directory, in name order.

    ``<directory>/studies/*.json.xz``, and legacy plain ``*.json``.
    """
    studies = Path(directory) / "studies"
    if not studies.is_dir():
        raise IdentityGrowthError("inference_studies_missing", str(directory))
    paths = [
        path
        for path in sorted(studies.iterdir())
        if path.is_file()
        and (path.name.endswith(".json.xz") or path.name.endswith(".json"))
    ]
    if not paths:
        raise IdentityGrowthError("inference_records_missing", str(directory))
    return paths


def _read_record(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    try:
        text = lzma.decompress(raw) if path.name.endswith(".json.xz") else raw
        record = json.loads(text.decode("utf-8"))
    except (lzma.LZMAError, UnicodeError, ValueError) as error:
        raise IdentityGrowthError("inference_record_unreadable", str(path)) from error
    return record, hashlib.sha256(raw).hexdigest()


def read_inference_records(directory: Path) -> Iterator[tuple[dict[str, Any], str]]:
    """Yield each per-study record of one output directory with its file-byte digest.

    One record is decoded at a time; a real record can decode to hundreds of MB.
    """
    for path in inference_record_paths(directory):
        yield _read_record(path)


def harvest_inference(directories: Iterable[Path]) -> Iterator[dict[str, Any]]:
    """Yield the candidates of every record of the given diagnostic output directories.

    Each record is digested over its exact file bytes and released before the next
    is read. A study appearing in more than one record is refused by name.
    """
    yield from _harvest(
        pair
        for directory in directories
        for pair in read_inference_records(Path(directory))
    )


def _full_refs(case: Mapping[str, Any]) -> tuple[set[str], set[str]]:
    payload_refs: set[str] = set()
    context_refs: set[str] = set()
    references = [case.get("full_profile")]
    role_refs = case.get("full_profile_refs")
    if isinstance(role_refs, Mapping):
        references.extend(role_refs.values())
    for reference in references:
        if not isinstance(reference, Mapping):
            continue
        if _text(reference.get("payload_ref")):
            payload_refs.add(reference["payload_ref"])
        if _text(reference.get("context_ref")):
            context_refs.add(reference["context_ref"])
    return payload_refs, context_refs


def _decision_regions(case: Mapping[str, Any]) -> list[dict[str, Any]]:
    result = []
    for region in _rows(case.get("regions")) or ():
        if not isinstance(region, Mapping):
            continue
        window = _window(region.get("window", region.get("source_window")))
        if window is not None and _text(region.get("series_uid")):
            result.append({"series_uid": region["series_uid"], "window": window})
    return result


def candidates_from_memory(
    snapshot: MemorySnapshot,
    *,
    candidate_ids: Sequence[str] | None = None,
    sanity_by_case_id: Mapping[str, Any] | None = None,
) -> Iterator[dict[str, Any]]:
    """Candidates from the object cases of a candidate memory snapshot.

    An admitted memory candidate enters the child exactly as its source memory
    holds it, with its paired full profile; its rows travel in ``retained``. A
    missing sanity record is unknown anatomy. The selection is checked at once;
    the candidates are then made one at a time as they are consumed.
    """
    memory = _snapshot_memory(snapshot, "candidate_snapshot_invalid")
    objects = [
        case for case in memory["cases"] if not case["subject"].startswith("diagnosis/")
    ]
    by_id = {case["case_id"]: case for case in objects}
    if candidate_ids is None:
        selected = [case["case_id"] for case in objects]
    else:
        selected = _rows(candidate_ids)
        if selected is None or not all(_text(item) for item in selected):
            raise IdentityGrowthError("candidate_ids_invalid")
        if len(set(selected)) != len(selected):
            raise IdentityGrowthError("candidate_ids_invalid")
        unknown = [item for item in selected if item not in by_id]
        if unknown:
            raise IdentityGrowthError("unknown_candidate", unknown[0])
    sanity = {} if sanity_by_case_id is None else sanity_by_case_id
    if not isinstance(sanity, Mapping) or any(key not in selected for key in sanity):
        raise IdentityGrowthError("sanity_map_invalid")
    return _memory_candidates(
        snapshot, memory, [by_id[item] for item in selected], sanity
    )


def _memory_candidates(
    snapshot: MemorySnapshot,
    memory: Mapping[str, Any],
    cases: Sequence[Mapping[str, Any]],
    sanity: Mapping[str, Any],
) -> Iterator[dict[str, Any]]:
    contexts = (memory.get("full_profile_contexts") or {}).get("contexts", {})
    payloads = (memory.get("full_profile_payloads") or {}).get("payloads", {})
    identities = memory.get("source_identities") or {}
    for case in cases:
        payload_refs, context_refs = _full_refs(case)
        payload_rows = {ref: payloads[ref] for ref in payload_refs if ref in payloads}
        context_refs |= {
            row["context_ref"] for row in payload_rows.values() if "context_ref" in row
        }
        yield {
            "case_id": case["case_id"],
            "study_uid": case["study_uid"],
            "subject": case["subject"],
            "profile": copy.deepcopy(case["profile"]),
            "regions": _decision_regions(case),
            "sanity": copy.deepcopy(sanity.get(case["case_id"])),
            "source": {
                "kind": MEMORY_SOURCE,
                "manifest_sha256": snapshot.sha256,
                "memory_revision": memory["revision"],
                "case_sha256": _json_sha256(case),
            },
            "retained": {
                "case": case,
                "payloads": payload_rows,
                "contexts": {
                    ref: contexts[ref] for ref in context_refs if ref in contexts
                },
                "source_identity": identities.get(case["study_uid"]),
            },
        }


def _check_candidate(candidate: object) -> Mapping[str, Any]:
    if not isinstance(candidate, Mapping):
        raise IdentityGrowthError("candidate_invalid")
    label = str(candidate.get("case_id"))
    subject = candidate.get("subject")
    if (
        not _text(candidate.get("case_id"))
        or not _text(candidate.get("study_uid"))
        or not _text(subject)
        or subject.startswith("diagnosis/")
        or not isinstance(candidate.get("source"), Mapping)
        or not _text(candidate["source"].get("kind"))
    ):
        raise IdentityGrowthError("candidate_invalid", label)
    regions = _rows(candidate.get("regions"))
    if regions is None or any(
        not isinstance(region, Mapping)
        or set(region) != {"series_uid", "window"}
        or not _text(region["series_uid"])
        or _window(region["window"]) is None
        for region in regions
    ):
        raise IdentityGrowthError("candidate_regions_invalid", label)
    return candidate


def _profile_valid(profile: object) -> bool:
    """A strict-JSON squint-profile/v1 the memory validator accepts as a case profile."""
    if not isinstance(profile, Mapping) or profile.get("schema") != _PROFILE_SCHEMA:
        return False
    banks = profile.get("banks")
    if not isinstance(banks, Mapping) or not banks:
        return False
    for name, counts in banks.items():
        if (
            not _text(name)
            or not isinstance(counts, list)
            or len(counts) != 3
            or any(type(value) is not int or value < 0 for value in counts)
        ):
            return False
    try:
        json.dumps(profile, allow_nan=False)
    except (TypeError, ValueError):
        return False
    return True


# ---------------------------------------------------------- parent populations


def exclusion_studies(memory: Mapping[str, Any]) -> frozenset[str]:
    """Studies of every record kind that can speak: ``cases`` and identity cases."""
    studies: set[str] = set()
    table = memory.get("object_identity_cases")
    records = table.get("cases") if isinstance(table, Mapping) else None
    for row in [*(_rows(memory.get("cases")) or ()), *(_rows(records) or ())]:
        if isinstance(row, Mapping) and _text(row.get("study_uid")):
            studies.add(row["study_uid"])
    return frozenset(studies)


def represented_objects(memory: Mapping[str, Any]) -> dict[str, frozenset]:
    """Case ids and (study, object) pairs the parent already holds, of either sign."""
    case_ids: set[str] = set()
    objects: set[tuple[str, str]] = set()
    table = memory.get("object_identity_cases")
    records = _rows(table.get("cases") if isinstance(table, Mapping) else None) or []
    for row in [*(_rows(memory.get("cases")) or ()), *records]:
        if not isinstance(row, Mapping):
            continue
        if _text(row.get("case_id")):
            case_ids.add(row["case_id"])
        subject, study = row.get("subject"), row.get("study_uid")
        if _text(subject) and _text(study) and not subject.startswith("diagnosis/"):
            objects.add((study, subject))
    studies = {
        row["case_id"]: row.get("study_uid")
        for row in records
        if isinstance(row, Mapping) and _text(row.get("case_id"))
    }
    teaching = memory.get("object_identity_teaching")
    alternatives = (
        teaching.get("alternative_positives") if isinstance(teaching, Mapping) else None
    )
    for item in _rows(alternatives) or ():
        if not isinstance(item, Mapping):
            continue
        if _text(item.get("entry_id")):
            case_ids.add(item["entry_id"])
        study = studies.get(item.get("case_id"))
        if _text(study) and _text(item.get("identity")):
            objects.add((study, item["identity"]))
    return {"case_ids": frozenset(case_ids), "objects": frozenset(objects)}


# -------------------------------------------------------------- the decision


def location_support(sanity: object, subject: str) -> dict[str, Any]:
    """What a recorded sanity establishes about location for ``subject``.

    ``support`` lists each recorded ``supported_*`` check of this subject: the
    relation it checked, its axis and both intervals. It says where the candidate
    lies, never what tissue it is. ``status`` None means the record is invalid.
    """
    if sanity is None:
        return {"status": "unknown", "support": [], "contradicted": False}
    if (
        not isinstance(sanity, Mapping)
        or sanity.get("schema") != SANITY_SCHEMA
        or sanity.get("identity_assertion") is not None
        or sanity.get("status") not in _SANITY_STATUSES
    ):
        return {"status": None, "support": [], "contradicted": False}
    support: list[dict[str, Any]] = []
    reversed_check = False
    for row in _rows(sanity.get("windows")) or ():
        if not isinstance(row, Mapping):
            continue
        for check in _rows(row.get("checks")) or ():
            if (
                not isinstance(check, Mapping)
                or check.get("candidate_subject", subject) != subject
                or not isinstance(check.get("result"), str)
            ):
                continue
            result = check["result"]
            if result.startswith("reversed_"):
                reversed_check = True
            elif (
                result.startswith("supported_")
                and _text(check.get("rule_id"))
                and _text(check.get("axis"))
            ):
                support.append(
                    {
                        "establishes": "location_only",
                        "rule_id": check["rule_id"],
                        "axis": check["axis"],
                        "result": result,
                        "candidate_interval": copy.deepcopy(
                            check.get("candidate_interval")
                        ),
                        "target_interval": copy.deepcopy(check.get("target_interval")),
                        "series_uid": row.get("series_uid"),
                        "window": _window(row.get("window")),
                    }
                )
    return {
        "status": sanity["status"],
        "support": support,
        "contradicted": sanity["status"] == "contradicted" or reversed_check,
    }


def _bank_views(banks: object) -> set[tuple[str, ...]] | None:
    rows = _rows(banks)
    if not rows:
        return None
    views: set[tuple[str, ...]] = set()
    for name in rows:
        parsed = parse_territory_bank_name(name)
        view = parsed.get("view") if parsed is not None else None
        if (
            not isinstance(view, list)
            or len(view) != 3
            or not all(isinstance(item, str) for item in view)
        ):
            return None
        views.add(tuple(view))
    return views


def admission_scope(recall: object, identity: str) -> dict[str, Any]:
    """The views an admission may assert, or the named refusal.

    The views whose banks took part in the comparisons speaking for ``identity``
    (alternative-identity seeds included), minus every view through which a
    negative case of ``identity`` speaks. Returns ``{"views": [...]}`` or
    ``{"refusal": "admission_scope_unresolved", "detail": ...}``.
    """

    def refusal(detail: str) -> dict[str, Any]:
        return {"refusal": "admission_scope_unresolved", "detail": detail}

    rows = _rows(recall.get("cases")) if isinstance(recall, Mapping) else None
    negatives = (
        _rows(recall.get("negative_cases", [])) if isinstance(recall, Mapping) else None
    )
    if rows is None or negatives is None:
        return refusal("recall_rows_missing")
    sides = {"for": set(), "against": set()}
    for side, entries in (("for", rows), ("against", negatives)):
        for row in entries:
            if not isinstance(row, Mapping):
                return refusal("recall_row_malformed")
            if row.get("identity") != identity or row.get("speaks") is not True:
                continue
            views = _bank_views(row.get("common_speaking_banks"))
            if views is None:
                return refusal("speaking_banks_malformed")
            sides[side] |= views
    remaining = sides["for"] - sides["against"]
    if not remaining:
        return refusal("no_usable_view")
    return {"views": [list(view) for view in sorted(remaining)]}


def _decision(
    candidate: Mapping[str, Any],
    state: str,
    reason: str,
    support: Sequence[Mapping[str, Any]],
    recognized: object = None,
    views: Sequence[Sequence[str]] = (),
) -> dict[str, Any]:
    return {
        "candidate_id": candidate["case_id"],
        "study_uid": candidate["study_uid"],
        "subject": candidate["subject"],
        "state": state,
        "reason": reason,
        "recognized_identity": recognized if _text(recognized) else None,
        "views": [list(view) for view in views],
        "support": copy.deepcopy(list(support)),
        "regions": copy.deepcopy(list(candidate["regions"])),
        "source": copy.deepcopy(dict(candidate["source"])),
    }


def admission_from_recall(
    candidate: Mapping[str, Any], recall: Mapping[str, Any]
) -> dict[str, Any]:
    """Decide one candidate from its signed recall and its recorded anatomy.

    Precedence: invalid input, known contradiction, recall's conflict, another
    recognized identity, a negative speaking alone, nothing identified, unknown
    anatomy, unresolved scope, admission.
    """
    subject = candidate["subject"]
    anatomy = location_support(candidate.get("sanity"), subject)
    support = anatomy["support"]
    outcome = recall.get("outcome") if isinstance(recall, Mapping) else None
    if outcome in (None, "invalid_input", "invalid_preparation"):
        reason = recall.get("reason") if isinstance(recall, Mapping) else None
        return _decision(candidate, "refused", str(reason or "recall_invalid"), support)
    if anatomy["status"] is None:
        return _decision(candidate, "refused", "sanity_invalid", support)
    identity = recall.get("identity")
    if anatomy["contradicted"] or outcome == "blocked_by_sanity":
        recognized = identity or recall.get("blocked_identity")
        return _decision(
            candidate, "blocked", "anatomy_contradicted", support, recognized
        )
    if outcome == "unresolved_conflict":
        return _decision(candidate, "conflict", str(recall.get("reason")), support)
    if outcome == "identified" and identity != subject:
        return _decision(
            candidate, "conflict", "recognized_as_other_identity", support, identity
        )
    if subject in (_rows(recall.get("opposed_identities")) or ()):
        return _decision(
            candidate,
            "opposed",
            "negative_case_speaks_against_proposed_identity",
            support,
        )
    if outcome != "identified":
        return _decision(
            candidate, "proposal", str(recall.get("reason") or outcome), support
        )
    if anatomy["status"] != "plausible" or not support:
        reason = (
            "anatomy_support_unrecorded"
            if anatomy["status"] == "plausible"
            else "anatomy_unknown"
        )
        return _decision(candidate, "proposal", reason, support, subject)
    scope = admission_scope(recall, subject)
    if "views" not in scope:
        return _decision(candidate, "refused", scope["refusal"], support, subject)
    return _decision(
        candidate,
        "admitted",
        "identified_with_location_support",
        support,
        subject,
        scope["views"],
    )


def _early_decision(
    candidate: Mapping[str, Any], represented: Mapping[str, frozenset]
) -> dict[str, Any] | None:
    """A decision that needs no recall: a duplicate or an unpublishable profile."""
    support = location_support(candidate.get("sanity"), candidate["subject"])["support"]
    if candidate["case_id"] in represented["case_ids"]:
        return _decision(candidate, "duplicate", "case_id_already_in_parent", support)
    if (candidate["study_uid"], candidate["subject"]) in represented["objects"]:
        return _decision(candidate, "duplicate", "object_already_in_parent", support)
    if not _profile_valid(candidate.get("profile")):
        return _decision(candidate, "refused", "candidate_profile_invalid", support)
    return None


def admission_decision(
    candidate: Mapping[str, Any],
    memory: Mapping[str, Any],
    *,
    prepared: Mapping[str, Any] | None = None,
    record_studies: frozenset[str] | None = None,
    represented: Mapping[str, frozenset] | None = None,
) -> dict[str, Any]:
    """Score one candidate against one frozen parent memory.

    Returns ``{"decision", "recall", "excluded_study_uid"}``. ``prepared`` must be
    the parent's preparation for this candidate's exclusion (any other is refused
    by recall as ``invalid_preparation``); ``record_studies`` and ``represented``
    may be passed to share them across a round.
    """
    _check_candidate(candidate)
    if not isinstance(memory, Mapping):
        raise IdentityGrowthError("parent_memory_invalid")
    studies = exclusion_studies(memory) if record_studies is None else record_studies
    exclusion = candidate["study_uid"] if candidate["study_uid"] in studies else None
    held = represented_objects(memory) if represented is None else represented
    early = _early_decision(candidate, held)
    if early is not None:
        return {"decision": early, "recall": None, "excluded_study_uid": exclusion}
    if prepared is None:
        prepared = prepare_identity(memory, exclude_study_uid=exclusion)
    recall = recall_identity(
        candidate["profile"],
        memory,
        exclude_study_uid=exclusion,
        sanity=candidate.get("sanity"),
        prepared=prepared,
    )
    return {
        "decision": admission_from_recall(candidate, recall),
        "recall": recall,
        "excluded_study_uid": exclusion,
    }


# ------------------------------------------------------------- held-out studies


def _study_uid_text(value: object) -> bool:
    """A StudyInstanceUID as written: nonempty text with no whitespace or NUL."""
    return (
        isinstance(value, str)
        and bool(value)
        and "\0" not in value
        and not any(character.isspace() for character in value)
    )


def held_out_record(study_uids: Iterable[str]) -> dict[str, Any]:
    """The record of a round's held-out studies: the sorted list and its digest.

    ``sha256`` is the strict-JSON digest of the sorted list (``_json_sha256``), so
    a later round recomputes it from the list alone.
    """
    uids = sorted(set(study_uids))
    return {"schema": HELD_OUT_SCHEMA, "study_uids": uids, "sha256": _json_sha256(uids)}


def _held_out_input(values: object) -> frozenset[str]:
    if isinstance(values, (str, bytes, Mapping)) or not isinstance(values, Iterable):
        raise IdentityGrowthError("held_out_invalid")
    uids = list(values)
    if not all(_study_uid_text(uid) for uid in uids):
        raise IdentityGrowthError("held_out_invalid")
    if len(set(uids)) != len(uids):
        raise IdentityGrowthError("held_out_duplicate")
    return frozenset(uids)


def inherited_held_out(parent: Mapping[str, Any]) -> frozenset[str]:
    """The held-out studies a parent's growth block records; a child keeps them all.

    A record that is not exactly what ``held_out_record`` writes for a nonempty
    set, its digest included, is refused by name.
    """
    block = parent.get("object_identity_growth")
    record = block.get("held_out") if isinstance(block, Mapping) else None
    if record is None:
        return frozenset()
    uids = record.get("study_uids") if isinstance(record, Mapping) else None
    if (
        not isinstance(record, Mapping)
        or set(record) != {"schema", "study_uids", "sha256"}
        or record["schema"] != HELD_OUT_SCHEMA
        or not isinstance(uids, list)
        or not uids
        or not all(_study_uid_text(uid) for uid in uids)
        or uids != sorted(set(uids))
        or record["sha256"] != _json_sha256(uids)
    ):
        raise IdentityGrowthError("parent_growth_metadata_invalid", "held_out")
    return frozenset(uids)


# ------------------------------------------------------------- study labels


def _label_source(path: object) -> dict[str, Any]:
    """The label file's exact bytes, their digest and its checked header.

    Read once, before any candidate, so a missing or malformed file is refused
    before the round begins and the rows parsed after it are these bytes. No
    study row is parsed here.
    """
    if not isinstance(path, Path):
        raise IdentityGrowthError("labels_path_invalid")
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeError) as error:
        raise IdentityGrowthError("labels_unreadable", str(path)) from error
    try:
        header = next(csv.reader(io.StringIO(text, newline="")), None)
    except csv.Error as error:
        raise IdentityGrowthError("labels_unreadable", str(path)) from error
    if header is None or tuple(header) != _LABEL_COLUMNS:
        raise IdentityGrowthError("labels_columns_invalid", str(path))
    return {
        "reference": {
            "source": LABEL_SOURCE,
            "source_path": str(path.resolve()),
            "source_sha256": hashlib.sha256(raw).hexdigest(),
        },
        "text": text,
    }


def _label_rows(
    source: Mapping[str, Any], study_uids: Iterable[str]
) -> dict[str, dict[str, int | None]]:
    """The label rows of exactly ``study_uids``; every other row is passed over.

    A row's label cells are parsed only when its StudyInstanceUID is wanted, by
    the cell rules of ``squint_memory._read_labels``: blank is no label, "0" and
    "1" are the label. The Report cell is never parsed. A wanted study absent
    from the file has no row.
    """
    wanted = set(study_uids)
    rows: dict[str, dict[str, int | None]] = {}
    if not wanted:
        return rows
    reader = csv.reader(io.StringIO(source["text"], newline=""))
    try:
        next(reader)  # the header, checked when the file was read
        for row in reader:
            if not row or row[0] not in wanted:
                continue
            uid = row[0]
            if len(row) != len(_LABEL_COLUMNS):
                raise IdentityGrowthError("labels_row_invalid", uid)
            if uid in rows:
                raise IdentityGrowthError("labels_study_uid_duplicate", uid)
            calls: dict[str, int | None] = {}
            for question, cell in zip(LABELS, row[2:], strict=True):
                if cell == "":
                    calls[question] = None
                elif cell in ("0", "1"):
                    calls[question] = int(cell)
                else:
                    raise IdentityGrowthError(
                        "labels_value_invalid", f"{uid}:{question}"
                    )
            rows[uid] = calls
    except csv.Error as error:
        raise IdentityGrowthError(
            "labels_unreadable", source["reference"]["source_path"]
        ) from error
    return rows


def _carry_labels(
    admissions: Sequence[Mapping[str, Any]], source: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, dict[str, int | None]]]:
    """Carry each admitted study's labels onto its admitted inference case.

    Runs after every decision is made, on the child's own copies. The calls,
    their scopes and the views they speak through are exactly those of
    ``carry_condition_calls`` for the case's admission call, with no localized
    call. Each call keeps its ``train.csv`` source; ``teaching_source`` and
    ``identity_growth`` stay the recognition-derived identity lineage. A study
    with no row keeps no calls, named ``no_label_row``; a memory candidate keeps
    its source's calls, named ``source_case_retained``, and its row is not read.
    Returns the round's record of what was taught, and the rows it parsed, which
    configuration teaching reads (``_teach_configurations``): the label text is
    not held past this call.
    """
    reference = source["reference"]
    rows = _label_rows(
        source,
        {
            entry["case"]["study_uid"]
            for entry in admissions
            if entry["retained"] is None
        },
    )
    taught: dict[str, dict[str, Any]] = {}
    for entry in admissions:
        case = entry["case"]
        if entry["retained"] is not None:
            taught[case["case_id"]] = {"status": "source_case_retained"}
            continue
        study = case["study_uid"]
        labels = {**reference, "study_uid": study}
        row = rows.get(study)
        if row is None:
            case["condition_teaching"] = {
                "schema": CONDITION_TEACHING_SCHEMA,
                "status": "no_label_row",
                "labels": labels,
            }
            taught[case["case_id"]] = {"status": "no_label_row"}
            continue
        try:
            carry = carry_condition_calls(case, entry["call"], row)
        except SquintMemoryError as error:
            raise IdentityGrowthError("condition_carry_invalid", error.code) from error
        calls = dict(carry["condition_calls"])
        case["condition_calls"] = calls
        case["presentation_scope"] = dict(carry["presentation_scope"])
        case["label_attribution"] = {
            question: {**labels, "condition": question, "column": question}
            for question in calls
        }
        case["condition_teaching"] = {
            "schema": CONDITION_TEACHING_SCHEMA,
            "status": "carried",
            "labels": labels,
            "carry": carry,
        }
        taught[case["case_id"]] = {"status": "carried", "condition_calls": dict(calls)}
    record = {
        "schema": CONDITION_TEACHING_SCHEMA,
        "labels": dict(reference),
        "read_study_uids": sorted(rows),
        "cases": taught,
    }
    return record, rows


def _role_links(staged: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Each role's link to its object case and that case's own identity provenance.

    ``identity_views`` are the views the role was composed on, its confirm
    call's as ``identity_condition_views`` reads them (None: a whole-case
    confirm, every view). A recognition-derived case is pinned by the digest of
    its lineage (``identity_growth``); a seed case, confirmed by a visual call,
    by its call row's digest and reader. Neither is copied.
    """
    scope = identity_condition_views(staged)
    if scope.get("outcome") != "scoped":
        raise IdentityGrowthError(
            "configuration_identity_teaching_invalid", str(scope.get("reason"))
        )
    reader = staged["object_identity_teaching"].get("reader")
    links: dict[str, dict[str, Any]] = {}
    for case in staged["cases"]:
        case_id = case["case_id"]
        if case_id not in scope["views"]:
            raise IdentityGrowthError("configuration_role_unconfirmed", case_id)
        views = scope["views"][case_id]
        [row] = scope["calls"][case_id]
        lineage = case.get("identity_growth")
        if isinstance(lineage, Mapping) and lineage.get("kind") == RECOGNITION_KIND:
            identity = {
                "kind": RECOGNITION_KIND,
                "independent_confirmation": lineage["independent_confirmation"],
                "parent_manifest_sha256": lineage["parent_manifest_sha256"],
                "lineage_sha256": _json_sha256(lineage),
            }
        else:
            identity = {
                "kind": SEED_CALL_KIND,
                "reader": row.get("reader", reader),
                "call_sha256": _json_sha256(row),
            }
        links[case["subject"]] = {
            "case_id": case_id,
            "identity_views": None
            if views is None
            else [list(view) for view in sorted(views)],
            "identity": identity,
        }
    return links


def _superseded(prior: Mapping[str, Any]) -> dict[str, Any]:
    """The parent version a rebuilt case replaces in the child: digest and round.

    ``round`` is the growth round that built that version, or None when no
    growth round did (the teaching set's own publication).
    """
    teaching = prior.get("configuration_teaching")
    built_in = teaching.get("round") if isinstance(teaching, Mapping) else None
    return {"case_sha256": _json_sha256(prior), "round": copy.deepcopy(built_in)}


def _configuration_row(
    study: str,
    carried: Mapping[str, int | None] | None,
    kept: Mapping[str, int | None] | None,
    configured: bool,
    reference: Mapping[str, Any] | None,
    parent_sha256: str,
) -> tuple[Mapping[str, int | None], dict[str, Any]] | None:
    """The official row a changed study's configurations are built from, and its source.

    The row this round carried (``carried``), named by the label file; else, for a
    study the parent holds configuration cases for (``configured``), the parent's
    ledger row (``kept``). None: no configuration is built. A carried row
    differing from the parent's is refused (``label_ledger_row_conflict``), as is
    a configured study the parent holds no row for
    (``configuration_label_row_missing``): it cannot be rebuilt.
    """
    if carried is not None and kept is not None and dict(kept) != dict(carried):
        raise IdentityGrowthError("label_ledger_row_conflict", study)
    if carried is not None:
        return carried, {**(reference or {}), "study_uid": study}
    if not configured:
        return None
    if kept is None:
        raise IdentityGrowthError("configuration_label_row_missing", study)
    labels = {
        "source": "label_ledger",
        "parent_manifest_sha256": parent_sha256,
        "study_uid": study,
    }
    return kept, labels


def _configuration_record(
    reference: Mapping[str, Any] | None,
    round_identity: Mapping[str, Any],
    studies: Iterable[str],
    cases: Sequence[Mapping[str, Any]],
    superseded: Mapping[str, str],
    added: Iterable[str],
) -> dict[str, Any]:
    """The round's record of its configuration teaching, binding the cases' content."""
    return {
        "schema": CONFIGURATION_TEACHING_SCHEMA,
        "labels": None if reference is None else dict(reference),
        "round": dict(round_identity),
        "study_uids": sorted(studies),
        "case_ids": [case["case_id"] for case in cases],
        "superseded": dict(sorted(superseded.items())),
        "cases_sha256": _json_sha256(list(cases)),
        "label_ledger_added": sorted(added),
    }


def _teach_configurations(
    parent: Mapping[str, Any],
    parent_sha256: str,
    parent_case_ids: frozenset[str],
    teaching: Mapping[str, Any],
    admissions: Sequence[Mapping[str, Any]],
    rows: Mapping[str, Mapping[str, int | None]] | None,
    reference: Mapping[str, Any] | None,
    round_identity: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Each changed study's whole-condition cases, built as the seed builds them.

    A study in which this round admitted an object is (re)built when this round
    carried its row (``rows``, ``_carry_labels``'s) or the parent already holds
    configuration cases for it, whose labels are then the parent's ledger row
    (``_configuration_row``, which refuses a row the parent holds differently).
    The seed's own scoped builder (``squint_bootstrap._rebuilt_configurations``)
    composes one case per labelled question from every object case of that study
    in the child, the parent's and this round's, each on the views where its
    identity holds in the child's ``teaching`` (the scoping preparation reads),
    with missing roles explicit, the official label as the call at
    ``study_condition_configuration`` scope and no case for a blank label.
    Proposals, held-out and non-admitted candidates never reach it. Apart from
    the builder's fields each case keeps its label source, this round and each
    role's own provenance (``_role_links``), and a role's full profile is linked
    on the new cases alone. A case whose id the parent holds for that study
    replaces the parent's version in the child only, recording it
    (``_superseded``); a parent case of that study the rebuild does not write
    (``configuration_rebuild_incomplete``), or a new id the parent holds outside
    that study (``configuration_case_conflict``), is refused by name, so one
    case per study and condition is ever live. Studies with no admission are not
    touched. Returns None when no label file was given and no study was built;
    otherwise the new cases, the replacements by id, the ledger rows they add and
    the round's record.
    """
    ledger = parent.get("label_ledger")
    if ledger is None:
        ledger = {}
    elif not isinstance(ledger, Mapping):
        raise IdentityGrowthError("parent_label_ledger_invalid")
    carried_rows = {} if rows is None else rows
    objects: dict[str, list[Mapping[str, Any]]] = {}
    held: dict[str, dict[str, Mapping[str, Any]]] = {}
    for case in parent["cases"]:
        if case["subject"].startswith("diagnosis/"):
            held.setdefault(case["study_uid"], {})[case["case_id"]] = case
        else:
            objects.setdefault(case["study_uid"], []).append(case)
    admitted: dict[str, list[Mapping[str, Any]]] = {}
    for entry in admissions:
        admitted.setdefault(entry["case"]["study_uid"], []).append(entry["case"])
    # The teaching is indexed once; each study is scoped by its own cases' rows,
    # the same views the whole block gives them, without rereading every call.
    calls_by_id: dict[str, list[Mapping[str, Any]]] = {}
    for call in teaching.get("calls", ()):
        if isinstance(call, Mapping) and isinstance(call.get("candidate_id"), str):
            calls_by_id.setdefault(call["candidate_id"], []).append(call)
    confirmed = set(teaching.get("confirmed_case_ids", ()))
    cases: list[dict[str, Any]] = []
    new: list[dict[str, Any]] = []
    replaces: dict[str, dict[str, Any]] = {}
    superseded: dict[str, str] = {}
    added: dict[str, dict[str, int | None]] = {}
    studies: list[str] = []
    for study in sorted(admitted):
        carried, kept = carried_rows.get(study), ledger.get(study)
        chosen = _configuration_row(
            study, carried, kept, study in held, reference, parent_sha256
        )
        if chosen is None:
            continue
        row, labels = chosen
        studies.append(study)
        roles = [*objects.get(study, ()), *admitted[study]]
        ids = [case["case_id"] for case in roles]
        staged = {
            "schema": parent["schema"],
            "revision": parent["revision"],
            "cases": roles,
            "object_identity_teaching": {
                **teaching,
                "confirmed_case_ids": [i for i in ids if i in confirmed],
                "calls": [call for i in ids for call in calls_by_id.get(i, ())],
            },
        }
        try:
            built, _ledger, _revision = _rebuilt_configurations(
                {"label_ledger": {study: dict(row)}}, staged
            )
        except SquintBootstrapError as error:
            raise IdentityGrowthError(
                "configuration_rebuild_invalid", f"{study}:{error.code}"
            ) from error
        _link_configuration_full_profiles({"cases": [*staged["cases"], *built]})
        links = _role_links(staged)
        previous = dict(held.get(study, {}))
        for case in built:
            prior = previous.pop(case["case_id"], None)
            if prior is None and case["case_id"] in parent_case_ids:
                raise IdentityGrowthError(
                    "configuration_case_conflict", case["case_id"]
                )
            supersedes = None if prior is None else _superseded(prior)
            case["configuration_teaching"] = {
                "schema": CONFIGURATION_TEACHING_SCHEMA,
                "labels": dict(labels),
                "round": dict(round_identity),
                "roles": {
                    subject: copy.deepcopy(links[subject])
                    for subject in sorted(case["profile"]["source"]["roles"])
                },
                "supersedes": supersedes,
            }
            cases.append(case)
            if supersedes is None:
                new.append(case)
            else:
                replaces[case["case_id"]] = case
                superseded[case["case_id"]] = supersedes["case_sha256"]
        if previous:
            raise IdentityGrowthError("configuration_rebuild_incomplete", min(previous))
        if carried is not None and kept is None:
            added[study] = dict(carried)
    if reference is None and not studies:
        return None
    return {
        "new": new,
        "replaces": replaces,
        "label_ledger": added,
        "record": _configuration_record(
            reference, round_identity, studies, cases, superseded, added
        ),
    }


# ---------------------------------------------------------------- the round


def _snapshot_memory(snapshot: object, code: str) -> dict[str, Any]:
    if (
        not isinstance(snapshot, MemorySnapshot)
        or snapshot.status != "squint"
        or not isinstance(snapshot.memory, dict)
        or not _is_sha(snapshot.sha256)
        or not isinstance(snapshot.path, Path)
    ):
        raise IdentityGrowthError(code)
    try:
        return _validate_memory(snapshot.memory)
    except SquintMemoryError as error:
        raise IdentityGrowthError(code, error.code) from error


def _prior_rounds(parent: Mapping[str, Any]) -> list[Any]:
    prior = parent.get("object_identity_growth")
    if prior is None:
        return []
    rounds = prior.get("rounds") if isinstance(prior, Mapping) else None
    if (
        not isinstance(prior, Mapping)
        or prior.get("schema") != GROWTH_SCHEMA
        or not isinstance(rounds, list)
    ):
        raise IdentityGrowthError("parent_growth_metadata_invalid")
    return rounds


def _parent_preparation(
    parent: Mapping[str, Any], exclusion: str | None
) -> Mapping[str, Any]:
    prepared = prepare_identity(parent, exclude_study_uid=exclusion)
    if prepared.get("outcome") != "prepared":
        raise IdentityGrowthError(
            "parent_identity_teaching_invalid", str(prepared.get("reason"))
        )
    return prepared


def _check_output(output: object, parent_snapshot: MemorySnapshot) -> Path:
    if (
        not isinstance(output, Path)
        or not output.name
        or ".." in output.parts
        or output.is_symlink()
    ):
        raise IdentityGrowthError("output_path_unsafe")
    if output.exists():
        raise IdentityGrowthError("output_exists", str(output))
    if output.parent.exists() and not output.parent.is_dir():
        raise IdentityGrowthError("output_path_unsafe")
    target = output.resolve()
    source = parent_snapshot.path.parent
    if target == source or source in target.parents or target in source.parents:
        raise IdentityGrowthError("output_path_unsafe")
    return output


def _decisions_bytes(document: Mapping[str, Any]) -> bytes:
    try:
        text = json.dumps(
            document, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False
        )
    except ValueError as error:
        raise IdentityGrowthError("decisions_not_strict_json") from error
    return (text + "\n").encode("utf-8")


def _write_atomic(path: Path, data: bytes) -> None:
    descriptor, name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".part"
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    except BaseException:
        Path(name).unlink(missing_ok=True)
        raise


def _lineage(
    candidate: Mapping[str, Any],
    scored: Mapping[str, Any],
    parent: Mapping[str, Any],
    parent_sha256: str,
) -> dict[str, Any]:
    decision = scored["decision"]
    recall = scored["recall"]
    identity = decision["recognized_identity"]
    speaking = sorted(
        {
            row["case_id"]
            for row in recall.get("cases", [])
            if row.get("identity") == identity and row.get("speaks") is True
        }
    )
    return {
        "schema": GROWTH_SCHEMA,
        "kind": RECOGNITION_KIND,
        "independent_confirmation": False,
        "parent_manifest_sha256": parent_sha256,
        "parent_revision": parent["revision"],
        "recognized_by": RECOGNIZER,
        "preparation_source_pin": recall["prepared_view"]["source_pin"],
        "excluded_study_uid": scored["excluded_study_uid"],
        "speaking_case_ids": speaking,
        "source": copy.deepcopy(dict(candidate["source"])),
        "decision": {
            key: copy.deepcopy(decision[key])
            for key in ("state", "reason", "recognized_identity", "views", "support")
        },
    }


def _admitted_case(candidate: Mapping[str, Any], lineage: dict[str, Any]) -> dict:
    retained = candidate.get("retained")
    if isinstance(retained, Mapping):
        # A memory candidate enters as its source memory holds it.
        case = copy.deepcopy(dict(retained["case"]))
        case["identity_growth"] = lineage
        return case
    return {
        "case_id": candidate["case_id"],
        "study_uid": candidate["study_uid"],
        "subject": candidate["subject"],
        "condition_calls": {},
        "profile": copy.deepcopy(dict(candidate["profile"])),
        "regions": copy.deepcopy(list(candidate["regions"])),
        "source": copy.deepcopy(dict(candidate["source"])),
        "teaching_source": {
            "kind": RECOGNITION_KIND,
            "parent_manifest_sha256": lineage["parent_manifest_sha256"],
        },
        "identity_growth": lineage,
    }


def _admission_call(case_id: str, views: list, parent_sha256: str) -> dict[str, Any]:
    return {
        "candidate_id": case_id,
        "call": "confirm",
        "views": copy.deepcopy(views),
        "notes": (
            "Recognition-derived identity admission against frozen parent "
            f"{parent_sha256[:16]}: joint signed recall with anatomical location "
            "support. Not an independent visual or clinical call."
        ),
        "reader": READER,
        "identity_growth": {
            "kind": RECOGNITION_KIND,
            "parent_manifest_sha256": parent_sha256,
        },
    }


def _admission(
    candidate: Mapping[str, Any],
    scored: Mapping[str, Any],
    parent: Mapping[str, Any],
    parent_sha256: str,
) -> dict[str, Any]:
    """The child's case and confirm call for one admission, made when it is decided."""
    case = _admitted_case(candidate, _lineage(candidate, scored, parent, parent_sha256))
    retained = candidate.get("retained")
    return {
        "case": case,
        "call": _admission_call(
            case["case_id"], scored["decision"]["views"], parent_sha256
        ),
        "retained": retained if isinstance(retained, Mapping) else None,
    }


def _merge_retained(child: dict[str, Any], retained_rows: Sequence[Mapping]) -> None:
    """Carry each admitted memory candidate's full rows and source identity."""
    rows = {"payloads": {}, "contexts": {}}
    identities: dict[str, Any] = {}
    needed: dict[str, set[str]] = {"payloads": set(), "contexts": set()}
    for retained in retained_rows:
        payload_refs, context_refs = _full_refs(retained["case"])
        needed["payloads"] |= payload_refs
        needed["contexts"] |= context_refs
        for kind in ("payloads", "contexts"):
            for ref, row in retained[kind].items():
                if ref in rows[kind] and rows[kind][ref] != row:
                    raise IdentityGrowthError("full_profile_reference_conflict", ref)
                rows[kind][ref] = row
                if kind == "payloads" and _text(row.get("context_ref")):
                    needed["contexts"].add(row["context_ref"])
        study = retained["case"]["study_uid"]
        if retained.get("source_identity") is not None:
            identities[study] = retained["source_identity"]
    for kind, table_key, schema in (
        ("payloads", "full_profile_payloads", FULL_PAYLOADS_SCHEMA),
        ("contexts", "full_profile_contexts", FULL_CONTEXTS_SCHEMA),
    ):
        if not needed[kind]:
            continue
        table = child.get(table_key) or {"schema": schema, kind: {}}
        merged = dict(table.get(kind, {}))
        for ref in sorted(needed[kind]):
            row = rows[kind].get(ref)
            if row is None and ref not in merged:
                raise IdentityGrowthError("full_profile_reference_missing", ref)
            if row is not None and ref in merged and merged[ref] != row:
                raise IdentityGrowthError("full_profile_reference_conflict", ref)
            if row is not None:
                merged[ref] = copy.deepcopy(row)
        child[table_key] = {**table, kind: merged}
    if identities:
        merged_identities = dict(child.get("source_identities") or {})
        for study, identity in identities.items():
            if study in merged_identities and merged_identities[study] != identity:
                raise IdentityGrowthError("source_identity_conflict", study)
            merged_identities[study] = copy.deepcopy(identity)
        child["source_identities"] = merged_identities


def _child_teaching(
    parent: Mapping[str, Any], admissions: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """The parent's identity teaching plus each admission's case id and confirm call.

    A new block; the parent's lists are not mutated. Configuration teaching
    scopes its roles by this block, the one the child keeps, read for each
    study's own cases.
    """
    teaching = dict(parent["object_identity_teaching"])
    teaching["confirmed_case_ids"] = [
        *teaching.get("confirmed_case_ids", []),
        *(entry["case"]["case_id"] for entry in admissions),
    ]
    teaching["calls"] = [
        *teaching.get("calls", []),
        *(entry["call"] for entry in admissions),
    ]
    return teaching


def _child_memory(
    parent: Mapping[str, Any],
    parent_sha256: str,
    admissions: Sequence[Mapping[str, Any]],
    round_record: dict[str, Any],
    teaching: Mapping[str, Any],
    configurations: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Every parent record, plus the admissions; shared parent parts are not mutated.

    ``teaching`` is ``_child_teaching``'s block. ``configurations`` is
    ``_teach_configurations``'s: a rebuilt case takes its parent version's place
    in the child's list (the parent is not changed), a new one follows the
    admitted object cases, and its label rows join the parent's
    ``label_ledger``, whose rows stay as they are. The growth block keeps the
    round's held-out record, the parent's held-out studies included, so the next
    round keeps honouring them. The revision binds the parent, the decisions and
    what labels and configurations taught, the configuration cases' content
    included: a child carrying labels never shares a revision with one that does
    not, nor with one whose configuration cases differ.
    """
    child = {key: value for key, value in parent.items() if key not in _RUNTIME_KEYS}
    cases = [entry["case"] for entry in admissions]
    replaces = {} if configurations is None else configurations["replaces"]
    grown = [] if configurations is None else list(configurations["new"])
    child["object_identity_teaching"] = teaching
    child["cases"] = [
        *(replaces.get(case["case_id"], case) for case in parent["cases"]),
        *cases,
        *grown,
    ]
    if configurations is not None and configurations["label_ledger"]:
        child["label_ledger"] = {
            **(parent.get("label_ledger") or {}),
            **configurations["label_ledger"],
        }
    _merge_retained(
        child,
        [entry["retained"] for entry in admissions if entry["retained"] is not None],
    )
    block: dict[str, Any] = {
        "schema": GROWTH_SCHEMA,
        "rounds": [*_prior_rounds(parent), round_record],
    }
    if round_record.get("held_out") is not None:
        block["held_out"] = copy.deepcopy(round_record["held_out"])
    child["object_identity_growth"] = block
    parts = [parent_sha256, round_record["decisions_sha256"], GROWTH_SCHEMA]
    for key in ("condition_teaching", "configuration_teaching"):
        if round_record.get(key) is not None:
            parts.append(_json_sha256(round_record[key]))
    digest = _json_sha256(parts)
    child["revision"] = f"{parent['revision']}+identity-growth-{digest[:16]}"
    return child


def _verify_child(child: dict[str, Any]) -> None:
    """The child validates, prepares, and still resolves every identity record's rows.

    ``_validate_memory`` re-checks every retained payload's digest, and
    ``save_memory`` reads back each case's full profile. Identity records come from
    the parent unchanged, whose publisher already read them back, so here each of
    their full-profile references must still resolve in the child's own tables to a
    row of the same study, subject and context; they are not decoded again.
    """
    try:
        _validate_memory(child)
    except SquintMemoryError as error:
        raise IdentityGrowthError("child_memory_invalid", error.code) from error
    prepared = prepare_identity(child)
    if prepared.get("outcome") != "prepared":
        raise IdentityGrowthError(
            "child_identity_teaching_invalid", str(prepared.get("reason"))
        )
    payloads = (child.get("full_profile_payloads") or {}).get("payloads", {})
    contexts = (child.get("full_profile_contexts") or {}).get("contexts", {})
    table = child.get("object_identity_cases")
    for record in (
        _rows(table.get("cases") if isinstance(table, Mapping) else None) or ()
    ):
        reference = record.get("full_profile") if isinstance(record, Mapping) else None
        if not isinstance(reference, Mapping) or "payload_ref" not in reference:
            continue
        payload = payloads.get(reference.get("payload_ref"))
        if (
            not isinstance(payload, Mapping)
            or reference.get("context_ref") not in contexts
            or payload.get("context_ref") != reference.get("context_ref")
            or payload.get("study_uid") != record.get("study_uid")
            or payload.get("subject") != record.get("subject")
            or payload.get("record_sha256") != reference.get("product_record_sha256")
        ):
            raise IdentityGrowthError(
                "child_identity_record_unresolved", str(record.get("case_id"))
            )


def grow_identity_memory(
    parent_snapshot: MemorySnapshot,
    candidates: Iterable[Mapping[str, Any]],
    output: Path,
    *,
    decisions_only: bool = False,
    labels: Path | None = None,
    held_out: Iterable[str] = (),
) -> dict[str, Any]:
    """Decide every candidate against one frozen parent; publish the warranted child.

    Candidates are consumed in arrival order and may be a one-shot stream: only
    each decision, and each admission's child case, outlives its candidate and its
    recall. The unexcluded preparation serves the whole round; a candidate whose
    study the parent holds is scored on that study's own held-out preparation,
    rebuilt only when the study changes (harvest yields a study's candidates
    together). ``output`` is a new directory. It always receives
    ``admission-decisions.json`` (DECISIONS_SCHEMA). With admissions, and unless
    ``decisions_only``, the child is published by ``save_memory`` at
    ``output/memory`` before the decisions are written beside it; no admission
    publishes no child.

    ``held_out`` names studies whose candidates are never scored or admitted
    (state ``held_out``); the parent's recorded held-out studies are added to
    them. A held-out study the parent already holds a record of, of any kind
    ``exclusion_studies`` counts (object, configuration, negative or
    alternative-identity), is refused by name before the round
    (``held_out_study_teaches_parent``): it would go on teaching the child, and
    the round's lineage would cite it. When any study is held out,
    ``held_out_record`` of the union is written in the decisions file and the
    child's growth block; with none, both are as before. ``labels`` is the
    competition's ``train.csv``: its bytes and header
    are read before the round, and after every decision only the rows of studies
    with an admitted inference case are parsed and carried (``_carry_labels``).
    Each such study with a row gets its whole-condition configuration cases, and
    a study the parent already holds configuration cases for has them rebuilt
    whenever an object of it is admitted, with or without a label file
    (``_teach_configurations``). Either is recorded beside
    ``condition_teaching`` as ``configuration_teaching`` in the round record and
    the receipt; without a label file and with nothing rebuilt, both stay as
    before. A label row the parent holds differently is refused by name before
    anything is written. A label file with ``decisions_only`` is refused: no
    child would hear it.
    """
    parent = _snapshot_memory(parent_snapshot, "invalid_parent_snapshot")
    if not isinstance(parent.get("object_identity_teaching"), Mapping):
        raise IdentityGrowthError("parent_identity_teaching_missing")
    ordinal = len(_prior_rounds(parent)) + 1
    if decisions_only and labels is not None:
        raise IdentityGrowthError("labels_with_decisions_only")
    held = _held_out_input(held_out) | inherited_held_out(parent)
    record_studies = exclusion_studies(parent)
    # A study the parent already learns from stays in every child and keeps
    # speaking for later admissions, so holding it out would not keep it out of
    # teaching. The declaration is refused before anything is read or written;
    # no parent record is ever dropped to make it hold.
    taught = held & record_studies
    if taught:
        raise IdentityGrowthError(
            "held_out_study_teaches_parent", ",".join(sorted(taught))
        )
    held_record = held_out_record(held) if held else None
    output = _check_output(output, parent_snapshot)
    label_source = None if labels is None else _label_source(labels)
    represented = represented_objects(parent)
    seen: set[str] = set()
    sources: set[tuple[str, str]] = set()
    decisions: list[dict[str, Any]] = []
    admitted_ids: list[str] = []
    admissions: list[dict[str, Any]] = []
    shared = None
    # The parent's preparation without one of its own studies, kept per study.
    held_preparation: tuple[str | None, Mapping[str, Any] | None] = (None, None)
    for candidate in candidates:
        _check_candidate(candidate)
        if candidate["case_id"] in seen:
            raise IdentityGrowthError("duplicate_candidate_id", candidate["case_id"])
        seen.add(candidate["case_id"])
        sources.add(
            (
                str(candidate["source"].get("kind")),
                str(candidate["source"].get("memory_revision")),
            )
        )
        if candidate["study_uid"] in held:
            # Nothing of a held-out study takes part: no recall, no admission.
            decisions.append(_decision(candidate, "held_out", "study_held_out", ()))
            continue
        early = _early_decision(candidate, represented)
        if early is not None:
            decisions.append(early)
            continue
        study = candidate["study_uid"]
        if study in record_studies:
            if held_preparation[0] != study:
                held_preparation = (study, _parent_preparation(parent, study))
            prepared = held_preparation[1]
        else:
            if shared is None:
                shared = _parent_preparation(parent, None)
            prepared = shared
        scored = admission_decision(
            candidate,
            parent,
            prepared=prepared,
            record_studies=record_studies,
            represented=represented,
        )
        decisions.append(scored["decision"])
        if scored["decision"]["state"] == "admitted":
            admitted_ids.append(candidate["case_id"])
            if not decisions_only:
                admissions.append(
                    _admission(candidate, scored, parent, parent_snapshot.sha256)
                )
    shared = held_preparation = None
    document = {
        "schema": DECISIONS_SCHEMA,
        "parent": {
            "manifest_sha256": parent_snapshot.sha256,
            "revision": parent["revision"],
        },
        "decisions": decisions,
    }
    if held_record is not None:
        document["held_out"] = held_record
    data = _decisions_bytes(document)
    decisions_sha256 = hashlib.sha256(data).hexdigest()
    round_identity = {
        "ordinal": ordinal,
        "parent_manifest_sha256": parent_snapshot.sha256,
        "decisions_sha256": decisions_sha256,
    }
    counts = dict(sorted(Counter(item["state"] for item in decisions).items()))
    receipt: dict[str, Any] = {
        "output": str(output),
        "decisions": str(output / DECISIONS_FILE),
        "decisions_sha256": decisions_sha256,
        "parent": dict(document["parent"]),
        "candidate_count": len(decisions),
        "state_counts": counts,
        "admitted_case_ids": list(admitted_ids),
        "held_out": copy.deepcopy(held_record),
        "condition_teaching": None,
        "configuration_teaching": None,
        "child": None,
    }
    if decisions_only or not admitted_ids:
        output.mkdir(parents=True)
        _write_atomic(output / DECISIONS_FILE, data)
        receipt["outcome"] = "decisions_only" if decisions_only else "no_admissions"
        if label_source is not None:
            # Nothing was admitted, so no label row was read and nothing taught.
            reference = label_source["reference"]
            receipt["condition_teaching"] = {
                "schema": CONDITION_TEACHING_SCHEMA,
                "labels": dict(reference),
                "read_study_uids": [],
                "cases": {},
            }
            receipt["configuration_teaching"] = _configuration_record(
                reference, round_identity, (), (), {}, ()
            )
        return receipt
    condition_teaching = label_rows = reference = None
    if label_source is not None:
        condition_teaching, label_rows = _carry_labels(admissions, label_source)
        reference = label_source["reference"]
    label_source = None  # the label file's text is not held past its carry
    teaching = _child_teaching(parent, admissions)
    configurations = _teach_configurations(
        parent,
        parent_snapshot.sha256,
        represented["case_ids"],
        teaching,
        admissions,
        label_rows,
        reference,
        round_identity,
    )
    round_record = {
        "parent_manifest_sha256": parent_snapshot.sha256,
        "parent_revision": parent["revision"],
        "scoring": "frozen_parent_only",
        "decisions_schema": DECISIONS_SCHEMA,
        "decisions_sha256": decisions_sha256,
        "candidate_count": len(decisions),
        "state_counts": counts,
        "admitted_case_ids": list(admitted_ids),
        "candidate_sources": [
            {"kind": kind, "memory_revision": revision}
            for kind, revision in sorted(sources)
        ],
    }
    if held_record is not None:
        round_record["held_out"] = copy.deepcopy(held_record)
    if condition_teaching is not None:
        round_record["condition_teaching"] = condition_teaching
        receipt["condition_teaching"] = copy.deepcopy(condition_teaching)
    if configurations is not None:
        round_record["configuration_teaching"] = configurations["record"]
        receipt["configuration_teaching"] = copy.deepcopy(configurations["record"])
    child = _child_memory(
        parent,
        parent_snapshot.sha256,
        admissions,
        round_record,
        teaching,
        configurations,
    )
    _verify_child(child)
    output.mkdir(parents=True)
    try:
        published = save_memory(child, output / CHILD_DIRECTORY)
    except ValueError as error:
        if not any(output.iterdir()):
            output.rmdir()
        code = getattr(error, "code", "child_not_strict_json")
        raise IdentityGrowthError("child_publication_failed", code) from error
    _write_atomic(output / DECISIONS_FILE, data)
    reloaded = load_memory_snapshot(output / CHILD_DIRECTORY)
    readback = prepare_identity(reloaded.memory)
    if readback.get("outcome") != "prepared":
        raise IdentityGrowthError("child_readback_invalid", str(readback.get("reason")))
    receipt["outcome"] = "published"
    receipt["child"] = {
        "manifest": published["manifest"],
        "sha256": published["sha256"],
        "revision": child["revision"],
        "case_count": published["case_count"],
        "identity_preparation": dict(readback),
    }
    return receipt


__all__ = [
    "CHILD_DIRECTORY",
    "CONDITION_TEACHING_SCHEMA",
    "CONFIGURATION_TEACHING_SCHEMA",
    "DECISIONS_FILE",
    "DECISIONS_SCHEMA",
    "GROWTH_SCHEMA",
    "HELD_OUT_SCHEMA",
    "LABEL_SOURCE",
    "STATES",
    "IdentityGrowthError",
    "admission_decision",
    "admission_from_recall",
    "admission_scope",
    "candidates_from_memory",
    "exclusion_studies",
    "grow_identity_memory",
    "harvest_candidates",
    "harvest_inference",
    "held_out_record",
    "inference_record_paths",
    "inherited_held_out",
    "location_support",
    "read_inference_records",
    "record_sha256",
    "represented_objects",
]
