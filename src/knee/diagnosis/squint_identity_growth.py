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
holds exactly the same population. Nothing admitted in a round speaks in it.

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
its lineage and is never an independent visual or clinical call. It has no
condition calls and no full profile; none is manufactured.

Decision states: ``admitted``; ``proposal`` (identified but anatomy unknown, or
nothing identified: the reason says which); ``blocked`` (a known anatomical
contradiction); ``conflict`` (recognized as another identity, which is named, or
recall's own unresolved conflict); ``opposed`` (a negative case of the proposed
identity speaks and nothing speaks for any identity); ``duplicate`` (the parent
already holds this case or a record of this object of this study); ``refused`` (a
named refusal, including ``admission_scope_unresolved``).
"""

from __future__ import annotations

import copy
import hashlib
import json
import lzma
import os
import re
import tempfile
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from knee.diagnosis.squint_identity import (
    SANITY_SCHEMA,
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
    _validate_memory,
    load_memory_snapshot,
    save_memory,
)

# v1 was the withdrawn prototype's block (candidate_states/admissions); a growth
# round record now lives in ``rounds``.
GROWTH_SCHEMA = "knee.object-identity-growth/v2"
DECISIONS_SCHEMA = "knee.identity-admission-decisions/v1"
STUDY_SCHEMA = "knee.squint-study/v1"
INFERENCE_SOURCE = "squint-inference"
MEMORY_SOURCE = "candidate-memory"
RECOGNITION_KIND = "recognition_derived_identity"
RECOGNIZER = "knee.diagnosis.squint_identity.recall_identity"
READER = (
    "knee.diagnosis.squint_identity_growth (recognition-derived; not a visual call)"
)
DECISIONS_FILE = "admission-decisions.json"
CHILD_DIRECTORY = "memory"
STATES = (
    "admitted",
    "proposal",
    "blocked",
    "conflict",
    "opposed",
    "duplicate",
    "refused",
)
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


def harvest_candidates(
    study_records: Iterable[Mapping[str, Any]],
    *,
    record_sha256s: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """One candidate per located object holding a cheap profile, in record order.

    Each candidate holds ``case_id`` (``located:<study_uid>:<subject>:<memory
    revision>``), ``study_uid``, ``subject`` (the located name, a proposal only),
    ``profile``, ``regions`` (series_uid and half-open tile window), ``sanity``
    exactly as recorded, and its ``source`` record. ``record_sha256s`` are the
    exact file-byte digests of the records, when the caller read them from disk;
    otherwise each decoded record is digested (``record_sha256``). Recall, values
    and questions already in a record are never read: the round scores afresh.
    """
    records = list(study_records)
    digests = None if record_sha256s is None else list(record_sha256s)
    if digests is not None and (
        len(digests) != len(records) or not all(_is_sha(item) for item in digests)
    ):
        raise IdentityGrowthError("record_sha256s_invalid")
    studies: set[str] = set()
    candidates: list[dict[str, Any]] = []
    for index, record in enumerate(records):
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
            "record_sha256": record_sha256(record)
            if digests is None
            else digests[index],
            "record_sha256_scope": "decoded_json" if digests is None else "file_bytes",
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
            candidates.append(
                {
                    "case_id": f"located:{uid}:{subject}:{revision}",
                    "study_uid": uid,
                    "subject": subject,
                    "profile": copy.deepcopy(profile),
                    "regions": _located_regions(located, f"{uid}:{subject}"),
                    "sanity": copy.deepcopy(located.get("sanity")),
                    "source": dict(source),
                }
            )
    return candidates


def read_inference_records(directory: Path) -> list[tuple[dict[str, Any], str]]:
    """Each per-study record of one diagnostic output directory and its byte digest.

    Reads ``<directory>/studies/*.json.xz`` (and legacy ``*.json``) in name order.
    """
    studies = Path(directory) / "studies"
    if not studies.is_dir():
        raise IdentityGrowthError("inference_studies_missing", str(directory))
    pairs: list[tuple[dict[str, Any], str]] = []
    for path in sorted(studies.iterdir()):
        compressed = path.name.endswith(".json.xz")
        if not path.is_file() or not (compressed or path.name.endswith(".json")):
            continue
        raw = path.read_bytes()
        try:
            text = lzma.decompress(raw) if compressed else raw
            record = json.loads(text.decode("utf-8"))
        except (lzma.LZMAError, UnicodeError, ValueError) as error:
            raise IdentityGrowthError(
                "inference_record_unreadable", str(path)
            ) from error
        pairs.append((record, hashlib.sha256(raw).hexdigest()))
    if not pairs:
        raise IdentityGrowthError("inference_records_missing", str(directory))
    return pairs


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
) -> list[dict[str, Any]]:
    """Candidates from the object cases of a candidate memory snapshot.

    An admitted memory candidate enters the child exactly as its source memory
    holds it, with its paired full profile; its rows travel in ``retained``. A
    missing sanity record is unknown anatomy.
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
    contexts = (memory.get("full_profile_contexts") or {}).get("contexts", {})
    payloads = (memory.get("full_profile_payloads") or {}).get("payloads", {})
    identities = memory.get("source_identities") or {}
    candidates = []
    for case_id in selected:
        case = by_id[case_id]
        payload_refs, context_refs = _full_refs(case)
        payload_rows = {ref: payloads[ref] for ref in payload_refs if ref in payloads}
        context_refs |= {
            row["context_ref"] for row in payload_rows.values() if "context_ref" in row
        }
        candidates.append(
            {
                "case_id": case_id,
                "study_uid": case["study_uid"],
                "subject": case["subject"],
                "profile": copy.deepcopy(case["profile"]),
                "regions": _decision_regions(case),
                "sanity": copy.deepcopy(sanity.get(case_id)),
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
        )
    return candidates


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
    if not support:
        reason = (
            "anatomy_unknown"
            if anatomy["status"] == "unknown"
            else "anatomy_support_unrecorded"
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


def _merge_retained(child: dict[str, Any], admitted: Sequence[Mapping]) -> None:
    """Carry each admitted memory candidate's full rows and source identity."""
    rows = {"payloads": {}, "contexts": {}}
    identities: dict[str, Any] = {}
    needed: dict[str, set[str]] = {"payloads": set(), "contexts": set()}
    for candidate in admitted:
        retained = candidate.get("retained")
        if not isinstance(retained, Mapping):
            continue
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


def _child_memory(
    parent: Mapping[str, Any],
    parent_sha256: str,
    admitted: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]],
    round_record: dict[str, Any],
) -> dict[str, Any]:
    """Every parent record, plus the admissions; shared parent parts are not mutated."""
    child = {key: value for key, value in parent.items() if key not in _RUNTIME_KEYS}
    cases = []
    calls = []
    for candidate, scored in admitted:
        lineage = _lineage(candidate, scored, parent, parent_sha256)
        case = _admitted_case(candidate, lineage)
        cases.append(case)
        calls.append(
            _admission_call(case["case_id"], scored["decision"]["views"], parent_sha256)
        )
    teaching = dict(parent["object_identity_teaching"])
    teaching["confirmed_case_ids"] = [
        *teaching.get("confirmed_case_ids", []),
        *(case["case_id"] for case in cases),
    ]
    teaching["calls"] = [*teaching.get("calls", []), *calls]
    child["object_identity_teaching"] = teaching
    child["cases"] = [*parent["cases"], *cases]
    _merge_retained(child, [candidate for candidate, _ in admitted])
    child["object_identity_growth"] = {
        "schema": GROWTH_SCHEMA,
        "rounds": [*_prior_rounds(parent), round_record],
    }
    digest = _json_sha256(
        [parent_sha256, round_record["decisions_sha256"], GROWTH_SCHEMA]
    )
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
) -> dict[str, Any]:
    """Decide every candidate against one frozen parent; publish the warranted child.

    ``output`` is a new directory. It always receives ``admission-decisions.json``
    (DECISIONS_SCHEMA). With admissions, and unless ``decisions_only``, the child is
    published by ``save_memory`` at ``output/memory`` before the decisions are
    written beside it; no admission publishes no child.
    """
    parent = _snapshot_memory(parent_snapshot, "invalid_parent_snapshot")
    if not isinstance(parent.get("object_identity_teaching"), Mapping):
        raise IdentityGrowthError("parent_identity_teaching_missing")
    _prior_rounds(parent)
    output = _check_output(output, parent_snapshot)
    items = [_check_candidate(candidate) for candidate in candidates]
    ids = [candidate["case_id"] for candidate in items]
    if len(set(ids)) != len(ids):
        raise IdentityGrowthError("duplicate_candidate_id")
    record_studies = exclusion_studies(parent)
    represented = represented_objects(parent)
    groups: dict[str | None, list[int]] = {}
    for index, candidate in enumerate(items):
        study = candidate["study_uid"]
        groups.setdefault(study if study in record_studies else None, []).append(index)
    scored: list[Any] = [None] * len(items)
    # One live preparation at a time, built only when a candidate needs recall.
    for exclusion in sorted(groups, key=lambda key: (key is not None, key or "")):
        prepared = None
        for index in groups[exclusion]:
            early = _early_decision(items[index], represented)
            if early is not None:
                scored[index] = {
                    "decision": early,
                    "recall": None,
                    "excluded_study_uid": exclusion,
                }
                continue
            if prepared is None:
                prepared = prepare_identity(parent, exclude_study_uid=exclusion)
                if prepared.get("outcome") != "prepared":
                    raise IdentityGrowthError(
                        "parent_identity_teaching_invalid", str(prepared.get("reason"))
                    )
            scored[index] = admission_decision(
                items[index],
                parent,
                prepared=prepared,
                record_studies=record_studies,
                represented=represented,
            )
        del prepared
    decisions = [entry["decision"] for entry in scored]
    document = {
        "schema": DECISIONS_SCHEMA,
        "parent": {
            "manifest_sha256": parent_snapshot.sha256,
            "revision": parent["revision"],
        },
        "decisions": decisions,
    }
    data = _decisions_bytes(document)
    decisions_sha256 = hashlib.sha256(data).hexdigest()
    counts = dict(sorted(Counter(item["state"] for item in decisions).items()))
    admitted = [
        (items[index], entry)
        for index, entry in enumerate(scored)
        if entry["decision"]["state"] == "admitted"
    ]
    receipt: dict[str, Any] = {
        "output": str(output),
        "decisions": str(output / DECISIONS_FILE),
        "decisions_sha256": decisions_sha256,
        "parent": dict(document["parent"]),
        "candidate_count": len(items),
        "state_counts": counts,
        "admitted_case_ids": [candidate["case_id"] for candidate, _ in admitted],
        "child": None,
    }
    if decisions_only or not admitted:
        output.mkdir(parents=True)
        _write_atomic(output / DECISIONS_FILE, data)
        receipt["outcome"] = "decisions_only" if decisions_only else "no_admissions"
        return receipt
    sources = sorted(
        {
            (
                str(candidate["source"].get("kind")),
                str(candidate["source"].get("memory_revision")),
            )
            for candidate in items
        }
    )
    round_record = {
        "parent_manifest_sha256": parent_snapshot.sha256,
        "parent_revision": parent["revision"],
        "scoring": "frozen_parent_only",
        "decisions_schema": DECISIONS_SCHEMA,
        "decisions_sha256": decisions_sha256,
        "candidate_count": len(items),
        "state_counts": counts,
        "admitted_case_ids": list(receipt["admitted_case_ids"]),
        "candidate_sources": [
            {"kind": kind, "memory_revision": revision} for kind, revision in sources
        ],
    }
    child = _child_memory(parent, parent_snapshot.sha256, admitted, round_record)
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
    "DECISIONS_FILE",
    "DECISIONS_SCHEMA",
    "GROWTH_SCHEMA",
    "STATES",
    "IdentityGrowthError",
    "admission_decision",
    "admission_from_recall",
    "admission_scope",
    "candidates_from_memory",
    "exclusion_studies",
    "grow_identity_memory",
    "harvest_candidates",
    "location_support",
    "read_inference_records",
    "record_sha256",
    "represented_objects",
]
