from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from fractions import Fraction
from types import MappingProxyType
from typing import Any

from knee.diagnosis.squint_interfaces import parse_territory_bank_name
from knee.diagnosis.squint_locator import (
    _banks,
    _batch_terms,
    _case_matrix,
    _exact_bank_terms,
    _mapping,
    _same_procedure,
    _source,
)

TEACHING_SCHEMA = "knee.object-identity-teaching/v1"
IDENTITY_CASES_SCHEMA = "knee.object-identity-cases/v1"
PREPARATION_SCHEMA = "knee.object-identity-recall-preparation/v1"
RECALL_SCHEMA = "knee.object-identity-recall/v1"
SANITY_SCHEMA = "knee.object-anatomical-sanity/v1"

_SPEAKING_ROLES = ("object", "context")
_SANITY_STATUSES = ("plausible", "unknown", "contradicted")
# Explicit provenance keys only; never substring matching.
_PROVENANCE_KEYS = (
    "reader",
    "source_revision",
    "source_manifest_sha256",
    "reader_sha256",
    "source_sha256",
    "review_sha256",
    "reader_manifest_sha256",
    "source_hash",
    "reader_hash",
    "review_hash",
)


def _provenance(*sources: object) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in _PROVENANCE_KEYS:
        for source in sources:
            mapping = _mapping(source)
            if mapping is not None and key in mapping:
                result[key] = copy.deepcopy(mapping[key])
                break
    return result


def _signal_banks(
    banks: Mapping[str, tuple[int, ...]], views: set[tuple[str, str, str]] | None = None
) -> dict[str, tuple[int, ...]]:
    # Only parsed territory-v2 object/context banks at exactly 10 mm speak.
    result: dict[str, tuple[int, ...]] = {}
    for name, counts in banks.items():
        parsed = parse_territory_bank_name(name)
        if parsed is None:
            continue
        if parsed.get("role") not in _SPEAKING_ROLES:
            continue
        # The bank name's own scale token, as every writer formats it (f"{tile_mm:g}mm").
        if parsed.get("scale") != "10mm":
            continue
        if views is not None and tuple(parsed.get("view", ())) not in views:
            continue
        result[name] = tuple(counts)
    return result


def _view_set(value: object) -> set[tuple[str, ...]] | None:
    """A nonempty sequence of unique exact view triples, or None."""
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        return None
    if any(
        not isinstance(view, Sequence)
        or isinstance(view, (str, bytes))
        or len(view) != 3
        or not all(isinstance(item, str) for item in view)
        for view in value
    ):
        return None
    views = {tuple(view) for view in value}
    return views if len(views) == len(value) else None


def _invalid(reason: str) -> dict[str, Any]:
    return {"outcome": "invalid_input", "reason": reason}


def _ratio(num: int, den: int) -> dict[str, str]:
    return {"numerator": str(num), "denominator": str(den)}


class _Prepared(Mapping):
    """Runtime-only validated view of one memory object and one exclusion.

    Lifetime contract: the view is valid only for the exact memory object it was
    prepared from (identity check, constant time) and the same exclusion. It holds
    a private strong reference to that object plus a frozen snapshot of the seed
    projection, matrix and envelopes, and of the negative identity cases with
    theirs; reuse never reads mutable memory content. It is not serializable and
    not a cache export. Re-prepare when the memory snapshot changes.
    """

    __slots__ = (
        "_envelopes",
        "_has_negatives",
        "_matrix",
        "_memory",
        "_negative_envelopes",
        "_negative_matrix",
        "_negatives",
        "_public",
        "_seeds",
    )

    def __init__(
        self,
        public,
        memory,
        seeds,
        matrix,
        envelopes,
        negatives=(),
        negative_matrix=None,
        negative_envelopes=(),
        has_negatives=False,
    ):
        self._public = MappingProxyType(dict(public))
        self._memory = memory
        self._seeds = seeds
        self._matrix = matrix
        self._envelopes = envelopes
        self._negatives = negatives
        self._negative_matrix = negative_matrix
        self._negative_envelopes = negative_envelopes
        self._has_negatives = has_negatives

    def __getitem__(self, key):
        return self._public[key]

    def __iter__(self):
        return iter(self._public)

    def __len__(self):
        return len(self._public)

    def __reduce__(self):
        raise TypeError("prepared identity view is runtime-only and not serializable")


def _other_view_claims(row: Mapping[str, Any]) -> set[tuple[str, ...]] | None:
    """Views a confirm call gives to a -1 or to another identity, or None."""
    claimed: set[tuple[str, ...]] = set()
    if "negative_views" in row:
        views = _view_set(row.get("negative_views"))
        if views is None:
            return None
        claimed |= views
    if "also_positive" in row:
        items = row.get("also_positive")
        if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
            return None
        for item in items:
            views = _view_set(item.get("views")) if isinstance(item, Mapping) else None
            if views is None:
                return None
            claimed |= views
    return claimed


def _record_parts(record: Mapping[str, Any]) -> tuple | dict[str, Any]:
    """Subject, study, exact banks and procedure of one identity-case record."""
    subject = record.get("subject")
    study = record.get("study_uid")
    if not isinstance(subject, str) or not subject:
        return _invalid("identity_case_subject_invalid")
    if not isinstance(study, str) or not study:
        return _invalid("identity_case_study_uid_invalid")
    profile = record.get("profile")
    banks = _banks(profile)
    if banks is None:
        return _invalid("identity_case_profile_banks_invalid")
    return subject, study, banks, _source(profile).get("procedure")


def _identity_case_records(root: Mapping[str, Any]) -> dict[str, Any]:
    """``{"records": {case_id: record}}``, or ``{"invalid": invalid_input}``."""
    table = _mapping(root.get("object_identity_cases"))
    records = table.get("cases") if table is not None else None
    if (
        table is None
        or table.get("schema") != IDENTITY_CASES_SCHEMA
        or not isinstance(records, Sequence)
        or isinstance(records, (str, bytes))
    ):
        return {"invalid": _invalid("object_identity_cases_invalid")}
    by_id: dict[str, Mapping[str, Any]] = {}
    for record in records:
        if not isinstance(record, Mapping):
            continue
        case_id = record.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            continue
        if case_id in by_id:
            return {"invalid": _invalid("duplicate_identity_case_id")}
        by_id[case_id] = record
    return {"records": by_id}


def _negative_entries(
    teaching: Mapping[str, Any],
    records: Mapping[str, Mapping[str, Any]],
    rows_by_id: Mapping[str, list[Mapping]],
    lineage: Mapping[str, Any],
) -> list[dict[str, Any]] | dict[str, Any]:
    """Ordinary negative identity cases: -1 on the proposed subject, own views.

    Only a reject call, or a confirm call's ``negative_views``, writes one.
    """
    wanted = set(teaching.get("negative_case_ids", ()))
    views_by_id = _mapping(teaching.get("negative_views"))
    if views_by_id is None:
        return _invalid("negative_views_required")
    entries: list[dict[str, Any]] = []
    for case_id, record in records.items():
        if case_id not in wanted:
            continue
        rows = rows_by_id.get(case_id, [])
        if len(rows) != 1:
            continue
        row = rows[0]
        if row.get("call") == "reject":
            stated = row.get("views")
        elif row.get("call") == "confirm" and "negative_views" in row:
            stated = row.get("negative_views")
        else:
            continue
        parts = _record_parts(record)
        if isinstance(parts, dict):
            return parts
        subject, study, banks, procedure = parts
        views = _view_set(views_by_id.get(case_id))
        if views is None:
            return _invalid("negative_views_invalid")
        if stated is not None and _view_set(stated) != views:
            return _invalid("negative_views_mismatch")
        if subject.startswith("diagnosis/"):
            continue
        entries.append(
            {
                "case_id": case_id,
                "subject": subject,
                "study_uid": study,
                "procedure": procedure,
                "procedure_view": {"source": {"procedure": procedure}},
                "views": tuple(sorted(views)),
                "banks": _signal_banks(banks, views),
                "lineage": {
                    **copy.deepcopy(dict(lineage)),
                    "call": copy.deepcopy(dict(row)),
                    "case": _provenance(
                        record, record.get("source"), _source(record.get("profile"))
                    ),
                },
            }
        )
    return entries


def _alternative_seeds(
    teaching: Mapping[str, Any],
    records: Mapping[str, Mapping[str, Any]],
    rows_by_id: Mapping[str, list[Mapping]],
    lineage: Mapping[str, Any],
) -> list[dict[str, Any]] | dict[str, Any]:
    """Positive seeds of a known alternative identity, on the called views only.

    The source case keeps its own subject and condition calls; the seed speaks
    for the alternative identity and is keyed by its own teaching entry id.
    """
    seeds: list[dict[str, Any]] = []
    for item in teaching.get("alternative_positives", ()):
        entry_id = item.get("entry_id")
        case_id = item.get("case_id")
        identity = item.get("identity")
        views = _view_set(item.get("views"))
        if views is None or not all(
            isinstance(value, str) and value for value in (entry_id, case_id, identity)
        ):
            return _invalid("alternative_positives_invalid")
        record = records.get(case_id)
        rows = rows_by_id.get(case_id, [])
        if record is None or len(rows) != 1:
            continue
        stated = rows[0].get("also_positive")
        matches = (
            [
                value
                for value in stated
                if isinstance(value, Mapping) and value.get("identity") == identity
            ]
            if isinstance(stated, Sequence) and not isinstance(stated, (str, bytes))
            else []
        )
        if len(matches) != 1:
            continue
        if _view_set(matches[0].get("views")) != views:
            return _invalid("alternative_positive_views_mismatch")
        parts = _record_parts(record)
        if isinstance(parts, dict):
            return parts
        subject, study, banks, procedure = parts
        if identity.startswith("diagnosis/") or identity == subject:
            return _invalid("alternative_positive_identity_invalid")
        seeds.append(
            {
                "case_id": entry_id,
                "subject": identity,
                "study_uid": study,
                "procedure": procedure,
                "procedure_view": {"source": {"procedure": procedure}},
                "banks": _signal_banks(banks, views),
                "lineage": {
                    **copy.deepcopy(dict(lineage)),
                    "call": copy.deepcopy(dict(rows[0])),
                    "case": _provenance(
                        record, record.get("source"), _source(record.get("profile"))
                    ),
                },
                "source_case_id": case_id,
            }
        )
    return seeds


def _identity_extensions(
    root: Mapping[str, Any],
    teaching: Mapping[str, Any],
    rows_by_id: Mapping[str, list[Mapping]],
    lineage: Mapping[str, Any],
) -> tuple[list, list, bool, bool] | dict[str, Any]:
    """Negative identity cases and alternative-identity positive seeds.

    A memory published before signed identity teaching declares neither and is
    read exactly as before. Returns (negatives, alternatives, has_negatives,
    has_alternatives) or an invalid_input record.
    """
    negative_ids = teaching.get("negative_case_ids", ())
    alternatives = teaching.get("alternative_positives", ())
    if (
        not isinstance(negative_ids, Sequence)
        or isinstance(negative_ids, (str, bytes))
        or not all(isinstance(item, str) and item for item in negative_ids)
        or len(set(negative_ids)) != len(negative_ids)
    ):
        return _invalid("negative_case_ids_invalid")
    if (
        not isinstance(alternatives, Sequence)
        or isinstance(alternatives, (str, bytes))
        or not all(isinstance(item, Mapping) for item in alternatives)
    ):
        return _invalid("alternative_positives_invalid")
    if not negative_ids and not alternatives:
        return [], [], False, False
    table = _identity_case_records(root)
    if "invalid" in table:
        return table["invalid"]
    records = table["records"]
    negatives: list | dict = []
    if negative_ids:
        negatives = _negative_entries(teaching, records, rows_by_id, lineage)
        if isinstance(negatives, dict):
            return negatives
    seeds = _alternative_seeds(teaching, records, rows_by_id, lineage)
    if isinstance(seeds, dict):
        return seeds
    return negatives, seeds, bool(negative_ids), bool(alternatives)


def _opposing_envelope(
    case: Mapping[str, Any], population: Sequence[Mapping[str, Any]], opposes
) -> Mapping[tuple[str, ...], Mapping[str, Any]]:
    """Largest exact squared cosine to each opposing case over identical banks.

    The opposing side of a positive seed is every seed of another identity; of a
    negative identity case, every positive seed of its own identity.
    """
    env: dict[tuple[str, ...], dict[str, Any]] = {}
    if isinstance(case["procedure"], str) and case["procedure"]:
        for other in population:
            if not opposes(other) or not _same_procedure(
                case["procedure_view"], other["procedure_view"]
            ):
                continue
            terms = _exact_bank_terms(case["banks"], other["banks"])
            if terms["code"] != "ok":
                continue
            key = tuple(terms["common_speaking_banks"])
            num, den = terms["cosine_squared"]
            current = env.get(key)
            if current is None:
                env[key] = {
                    "num": num,
                    "den": den,
                    "opponents": [other["case_id"]],
                    "count": 1,
                }
                continue
            current["count"] += 1
            if num * current["den"] > current["num"] * den:
                current["num"], current["den"] = num, den
                current["opponents"] = [other["case_id"]]
            elif num * current["den"] == current["num"] * den:
                current["opponents"].append(other["case_id"])
    return MappingProxyType(
        {
            key: MappingProxyType({**value, "opponents": tuple(value["opponents"])})
            for key, value in env.items()
        }
    )


def _frozen_entries(entries: Sequence[Mapping[str, Any]]) -> tuple:
    return tuple(
        MappingProxyType(
            {
                **entry,
                "banks": MappingProxyType(dict(entry["banks"])),
                "procedure_view": MappingProxyType(entry["procedure_view"]),
            }
        )
        for entry in entries
    )


def _frozen_matrix(entries: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    if not entries:
        return None
    built = _case_matrix([dict(entry["banks"]) for entry in entries])
    for array_key in ("values", "speaks", "valid"):
        built[array_key].setflags(write=False)
    return MappingProxyType(built)


def _seed_projection(seed: Mapping[str, Any]) -> dict[str, Any]:
    item = {
        "case_id": seed["case_id"],
        "subject": seed["subject"],
        "study_uid": seed["study_uid"],
        "procedure": seed["procedure"],
        "banks": sorted((k, list(v)) for k, v in seed["banks"].items()),
        "lineage": seed["lineage"],
    }
    if "source_case_id" in seed:
        item["source_case_id"] = seed["source_case_id"]
    return item


def prepare_identity(
    memory: object, *, exclude_study_uid: str | None = None
) -> Mapping[str, Any]:
    """Prepare one memory/exclusion view (see _Prepared for lifetime contract).

    The source pin is computed once from the frozen eligible seed projection and
    explicit teaching/source provenance, including the exclusion. The full memory
    is never serialized or hashed. Negative identity cases and alternative-
    identity positives are read from ``object_identity_cases`` when the teaching
    declares them; held-out exclusion removes them exactly as it removes seeds,
    before any envelope is formed.
    """
    if exclude_study_uid is not None and (
        not isinstance(exclude_study_uid, str) or not exclude_study_uid
    ):
        return _invalid("excluded_study_uid_invalid")
    root = _mapping(memory)
    if root is None:
        return _invalid("memory_must_be_object")
    cases = root.get("cases")
    if not isinstance(cases, Sequence) or isinstance(cases, (str, bytes)):
        return _invalid("memory_cases_required")
    teaching = _mapping(root.get("object_identity_teaching"))
    if teaching is None:
        return _invalid("object_identity_teaching_required")
    if teaching.get("schema") != TEACHING_SCHEMA:
        return _invalid("object_identity_teaching_schema_mismatch")
    confirmed = teaching.get("confirmed_case_ids")
    calls = teaching.get("calls")
    if not isinstance(confirmed, Sequence) or isinstance(confirmed, (str, bytes)):
        return _invalid("confirmed_case_ids_required")
    if not all(isinstance(item, str) and item for item in confirmed):
        return _invalid("confirmed_case_ids_invalid")
    if not isinstance(calls, Sequence) or isinstance(calls, (str, bytes)):
        return _invalid("teaching_calls_required")
    if not all(isinstance(row, Mapping) for row in calls):
        return _invalid("teaching_call_row_invalid")
    confirmed_set = set(confirmed)
    rows_by_id: dict[str, list[Mapping]] = {}
    for row in calls:
        candidate = row.get("candidate_id")
        if isinstance(candidate, str):
            rows_by_id.setdefault(candidate, []).append(row)
    source_lineage = _provenance(root, root.get("source"))
    teaching_lineage = _provenance(teaching)
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, Mapping):
            continue
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or case_id not in confirmed_set:
            continue
        rows = rows_by_id.get(case_id, [])
        if len(rows) != 1 or rows[0].get("call") != "confirm":
            continue
        subject = case.get("subject")
        study = case.get("study_uid")
        if not isinstance(subject, str) or not subject:
            return _invalid("seed_case_subject_invalid")
        if not isinstance(study, str) or not study:
            return _invalid("seed_case_study_uid_invalid")
        if subject.startswith("diagnosis/"):
            continue
        if case_id in seen:
            return _invalid("duplicate_seed_case_id")
        seen.add(case_id)
        profile = case.get("profile")
        banks = _banks(profile)
        if banks is None:
            return _invalid("seed_profile_banks_invalid")
        call_views = rows[0].get("views")
        selected_views: set[tuple[str, ...]] | None = None
        if call_views is not None:
            selected_views = _view_set(call_views)
            if selected_views is None:
                return _invalid("teaching_call_views_invalid")
        other_claims = _other_view_claims(rows[0])
        if other_claims is None:
            return _invalid("teaching_call_views_invalid")
        if other_claims and (selected_views is None or selected_views & other_claims):
            return _invalid("teaching_call_views_overlap")
        procedure = _source(profile).get("procedure")
        entries.append(
            {
                "case_id": case_id,
                "subject": subject,
                "study_uid": study,
                "procedure": procedure,
                "procedure_view": {"source": {"procedure": procedure}},
                "banks": _signal_banks(banks, selected_views),
                "lineage": {
                    "source": copy.deepcopy(source_lineage),
                    "teaching": copy.deepcopy(teaching_lineage),
                    "call": copy.deepcopy(dict(rows[0])),
                    "case": _provenance(case, case.get("source"), _source(profile)),
                },
            }
        )
    extensions = _identity_extensions(
        root,
        teaching,
        rows_by_id,
        {"source": source_lineage, "teaching": teaching_lineage},
    )
    if isinstance(extensions, dict):
        return extensions
    negatives, alternatives, has_negatives, has_alternatives = extensions
    for seed in alternatives:
        if seed["case_id"] in seen:
            return _invalid("duplicate_seed_case_id")
        seen.add(seed["case_id"])
        entries.append(seed)
    kept = [e for e in entries if e["study_uid"] != exclude_study_uid]
    envelopes = [
        _opposing_envelope(
            first, kept, lambda other, first=first: other["subject"] != first["subject"]
        )
        for first in kept
    ]
    kept_negatives = [n for n in negatives if n["study_uid"] != exclude_study_uid]
    negative_envelopes = [
        _opposing_envelope(
            case, kept, lambda other, case=case: other["subject"] == case["subject"]
        )
        for case in kept_negatives
    ]
    projection = {
        "exclude_study_uid": exclude_study_uid,
        "source": source_lineage,
        "teaching": teaching_lineage,
        "seeds": [_seed_projection(seed) for seed in kept],
    }
    if has_negatives:
        projection["negatives"] = [
            {
                "case_id": case["case_id"],
                "subject": case["subject"],
                "study_uid": case["study_uid"],
                "procedure": case["procedure"],
                "views": [list(view) for view in case["views"]],
                "banks": sorted((k, list(v)) for k, v in case["banks"].items()),
                "lineage": case["lineage"],
            }
            for case in kept_negatives
        ]
    pin = hashlib.sha256(
        json.dumps(
            projection, sort_keys=True, separators=(",", ":"), default=repr
        ).encode("utf-8")
    ).hexdigest()
    public = {
        "outcome": "prepared",
        "schema": PREPARATION_SCHEMA,
        "exclude_study_uid": exclude_study_uid,
        "source_pin": pin,
        "seed_count": len(kept),
    }
    if has_alternatives:
        public["alternative_positive_count"] = sum(
            "source_case_id" in seed for seed in kept
        )
    if has_negatives:
        public["negative_case_count"] = len(kept_negatives)
    return _Prepared(
        public,
        memory,
        _frozen_entries(kept),
        _frozen_matrix(kept),
        tuple(envelopes),
        negatives=_frozen_entries(kept_negatives),
        negative_matrix=_frozen_matrix(kept_negatives),
        negative_envelopes=tuple(negative_envelopes),
        has_negatives=has_negatives,
    )


def _sanity_status(sanity: object) -> str | None:
    """Read the knee.object-anatomical-sanity/v1 status; None means unknown."""
    if sanity is None:
        return "unknown"
    value = _mapping(sanity)
    if value is None or value.get("schema") != SANITY_SCHEMA:
        return None
    if value.get("identity_assertion") is not None:
        return None
    status = value.get("status")
    return status if status in _SANITY_STATUSES else None


def _proposed_name(profile: object) -> Any:
    if isinstance(profile, Mapping):
        return profile.get("subject")
    return getattr(profile, "subject", None)


def _negative_evidence(
    profile: object, query_banks: Mapping[str, Sequence[int]], prepared: _Prepared
) -> list[dict[str, Any]]:
    """Each negative identity case's exact resemblance to the query, signed -1.

    A negative case is an ordinary case on its identity's negative side. It
    speaks against that identity only strictly above its own opposing envelope,
    the largest resemblance it shares with that identity's positive seeds over
    the same banks. With no such seed it stays silent, named; it is never a veto.
    """
    negatives = prepared._negatives
    terms = _batch_terms(
        query_banks,
        [case["banks"] for case in negatives],
        matrix_cache=prepared._negative_matrix,
        compatible=[
            _same_procedure(profile, case["procedure_view"]) for case in negatives
        ],
    )
    rows: list[dict[str, Any]] = []
    for index, (case, term) in enumerate(zip(negatives, terms, strict=True)):
        if term is None or term["code"] != "ok":
            continue
        num, den = term["cosine_squared"]
        key = tuple(term["common_speaking_banks"])
        env = prepared._negative_envelopes[index].get(key)
        if env is None:
            status, speaks, env_out = "no_compatible_opposing_case", False, None
        else:
            speaks = num * env["den"] > env["num"] * den
            status = "above_envelope" if speaks else "not_above_envelope"
            env_out = {
                **_ratio(env["num"], env["den"]),
                "opponent_case_ids": list(env["opponents"]),
                "comparison_count": env["count"],
            }
        rows.append(
            {
                "case_id": case["case_id"],
                "identity": case["subject"],
                "digit": -1,
                "study_uid": case["study_uid"],
                "views": [list(view) for view in case["views"]],
                "lineage": copy.deepcopy(case["lineage"]),
                "common_speaking_banks": list(term["common_speaking_banks"]),
                "dot": term["dot"],
                "left_norm_sq": term["left_norm_sq"],
                "right_norm_sq": term["right_norm_sq"],
                "squared_cosine": _ratio(num, den),
                "envelope": env_out,
                "envelope_status": status,
                "speaks": speaks,
            }
        )
    return rows


def recall_identity(
    profile: object,
    memory: object,
    *,
    exclude_study_uid: str | None = None,
    sanity: object = None,
    prepared: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Score one query against the signed identity cases.

    Positive seeds speak for their identity and negative identity cases against
    theirs, each only above its own opposing envelope. An identity spoken for and
    against is a conflict; one spoken against only is recorded in
    ``opposed_identities`` and cannot be identified. A prepared view is valid
    only for the same memory object and exclusion it was built from; anything
    else returns invalid_preparation without scoring.
    """
    status_name = _sanity_status(sanity)
    if status_name is None:
        return _invalid("sanity_invalid")
    query_banks_all = _banks(profile)
    if query_banks_all is None:
        return _invalid("profile_banks_invalid")
    procedure = _source(profile).get("procedure")
    if not isinstance(procedure, str) or not procedure:
        return _invalid("query_procedure_missing")
    if prepared is None:
        prepared = prepare_identity(memory, exclude_study_uid=exclude_study_uid)
        if not isinstance(prepared, _Prepared):
            return dict(prepared)
    elif not isinstance(prepared, _Prepared) or prepared.get("outcome") != "prepared":
        return {"outcome": "invalid_preparation", "reason": "prepared_invalid"}
    elif prepared._memory is not memory:
        return {"outcome": "invalid_preparation", "reason": "memory_mismatch"}
    elif prepared.get("exclude_study_uid") != exclude_study_uid:
        return {"outcome": "invalid_preparation", "reason": "exclusion_mismatch"}
    seeds = prepared._seeds
    base: dict[str, Any] = {
        "schema": RECALL_SCHEMA,
        "proposed_name": _proposed_name(profile),
        "sanity": {"status": status_name},
        "prepared_view": {
            "schema": PREPARATION_SCHEMA,
            "source_pin": prepared["source_pin"],
        },
        "identity": None,
        "admitted": False,
        "speaking_identities": [],
        "cases": [],
        "nearest_identities": [],
        "nearest_cases": [],
        "calibrated_probability": False,
    }
    if prepared._has_negatives:
        base.update(negative_cases=[], opposed_identities=[], conflicted_identities=[])
    if not seeds:
        return {**base, "outcome": "silent", "reason": "no_eligible_seed_cases"}
    compatible = [_same_procedure(profile, seed["procedure_view"]) for seed in seeds]
    if not any(compatible):
        return {
            **base,
            "outcome": "silent",
            "reason": "procedure_mismatch_no_compatible_seed",
        }
    query_banks = _signal_banks(query_banks_all)
    terms = _batch_terms(
        query_banks,
        [seed["banks"] for seed in seeds],
        matrix_cache=prepared._matrix,
        compatible=compatible,
    )
    evidence: list[dict[str, Any]] = []
    missing_envelope = False
    for index, (seed, term) in enumerate(zip(seeds, terms, strict=True)):
        if term is None or term["code"] != "ok":
            continue
        num, den = term["cosine_squared"]
        key = tuple(term["common_speaking_banks"])
        env = prepared._envelopes[index].get(key)
        if env is None:
            status, speaks, env_out = "no_compatible_opposing_case", False, None
            missing_envelope = True
        else:
            speaks = num * env["den"] > env["num"] * den
            status = "above_envelope" if speaks else "not_above_envelope"
            env_out = {
                **_ratio(env["num"], env["den"]),
                "opponent_case_ids": list(env["opponents"]),
                "comparison_count": env["count"],
            }
        row = {
            "case_id": seed["case_id"],
            "identity": seed["subject"],
            "study_uid": seed["study_uid"],
            "lineage": copy.deepcopy(seed["lineage"]),
            "common_speaking_banks": list(term["common_speaking_banks"]),
            "dot": term["dot"],
            "left_norm_sq": term["left_norm_sq"],
            "right_norm_sq": term["right_norm_sq"],
            "squared_cosine": _ratio(num, den),
            "envelope": env_out,
            "envelope_status": status,
            "speaks": speaks,
        }
        if "source_case_id" in seed:
            row["source_case_id"] = seed["source_case_id"]
        evidence.append(row)
    base["cases"] = evidence
    negative_rows = (
        _negative_evidence(profile, query_banks, prepared)
        if prepared._negatives
        else []
    )
    if prepared._has_negatives:
        base["negative_cases"] = negative_rows
    if not evidence:
        return {**base, "outcome": "silent", "reason": "no_common_speaking_banks"}

    def value(item: Mapping[str, Any]) -> Fraction:
        ratio = item["squared_cosine"]
        return Fraction(int(ratio["numerator"]), int(ratio["denominator"]))

    best: dict[str, dict[str, Any]] = {}
    for item in evidence:
        current = best.get(item["identity"])
        if current is None or value(item) > value(current):
            best[item["identity"]] = item
    base["nearest_identities"] = [
        {
            "identity": name,
            "case_id": item["case_id"],
            "squared_cosine": item["squared_cosine"],
        }
        for name, item in sorted(best.items(), key=lambda kv: (-value(kv[1]), kv[0]))
    ]
    base["nearest_cases"] = [
        item["case_id"]
        for item in sorted(evidence, key=lambda e: (-value(e), e["case_id"]))
    ]
    speaking = sorted({item["identity"] for item in evidence if item["speaks"]})
    base["speaking_identities"] = speaking
    conflicted: list[str] = []
    if prepared._has_negatives:
        opposed = sorted({row["identity"] for row in negative_rows if row["speaks"]})
        conflicted = sorted(set(speaking) & set(opposed))
        base["opposed_identities"] = opposed
        base["conflicted_identities"] = conflicted
    if conflicted:
        return {
            **base,
            "outcome": "unresolved_conflict",
            "reason": "multiple_identities_above_envelope"
            if len(speaking) > 1
            else "identity_spoken_for_and_against",
        }
    if len(speaking) == 1:
        if status_name == "contradicted":
            return {
                **base,
                "outcome": "blocked_by_sanity",
                "reason": "sanity_contradicted",
                "blocked_identity": speaking[0],
            }
        return {
            **base,
            "outcome": "identified",
            "reason": "single_identity_above_envelope",
            "identity": speaking[0],
            "admitted": True,
        }
    if len(speaking) > 1:
        return {
            **base,
            "outcome": "unresolved_conflict",
            "reason": "multiple_identities_above_envelope",
        }
    if missing_envelope:
        return {
            **base,
            "outcome": "proposal",
            "reason": "no_compatible_opposing_case",
        }
    return {
        **base,
        "outcome": "unresolved_no_precedent",
        "reason": "no_case_above_envelope",
    }
