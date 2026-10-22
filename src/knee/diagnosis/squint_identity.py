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

# What the current study's own structure already established about one located object
# (``identity_context``), and the recall conditioned on it. The context is read from the
# locator's records by ``squint_pipeline`` and carried forward to recall, diagnosis and
# admission; recognition is never repeated to make it.
CONTEXT_SCHEMA = "knee.object-identity-context/v1"
RECALL_CONTEXT_SCHEMA = "knee.object-identity-recall-in-context/v1"
#: How the study records each located object's identity in context (``infer_study``).
IDENTITY_CONSUMPTION_SCHEMA = "knee.study-identity-consumption/v2"
#: A bone located by its own structural anchor: the existing reader's territories, key
#: planes and anatomical ordering already decided which bone it is.
STRUCTURAL_READER = "structural_reader"
#: An object placed by the authored anatomy map from the study's established anchors.
MAP_RELATION = "map_relation"
#: Placed by the leg-frame prior alone, or with no usable structural anchor: nothing known.
PRIOR_ONLY = "prior_only"
IDENTITY_BASES = (STRUCTURAL_READER, MAP_RELATION, PRIOR_ONLY)
#: Which other identities each basis leaves open, by name: a bone the reader established
#: still answers to every identity but the other bones it established in the same study;
#: a placement, to the alternatives whose own proposals overlap it; the prior, to all.
CONDITIONING = {
    STRUCTURAL_READER: "every_identity_not_removed_by_structure",
    MAP_RELATION: "open_alternatives",
    PRIOR_ONLY: "unconditioned",
}
#: What the located region is, by its territories' origin (``squint_interfaces``): a
#: resolved support (``anchor_structure``, ``teacher_support``, ``residual_native_support``)
#: or proposed places (``anatomical_relation``, ``fallback_location``), never confused.
RESOLVED_SUPPORT = "resolved_support"
PROPOSED_PLACES = "proposed_places"
SUPPORT_UNRECORDED = "support_unrecorded"
SUPPORT_KINDS = (RESOLVED_SUPPORT, PROPOSED_PLACES, SUPPORT_UNRECORDED)
ESTABLISHED_BY_STRUCTURE = "established_by_structure"
APPEARANCE_SUPPORTS = "appearance_supports"
APPEARANCE_SILENT = "appearance_silent"
PLACEMENT_ONLY = "placement_only"
#: An applicable negative case speaks over the asserted region and none of the object's own
#: cases does: appearance opposes the identity. Nothing renames it.
APPEARANCE_OPPOSED = "appearance_opposed"
#: Its own cases and an applicable negative case both speak: a signed conflict, kept open.
SIGNED_CONFLICT = "signed_conflict"
CONTESTED_OUTCOMES = (APPEARANCE_OPPOSED, SIGNED_CONFLICT)

_SPEAKING_ROLES = ("object", "context")
#: The tiles of the region asserted to be the object (``squint_interfaces.ROLE_OBJECT``).
_OBJECT_ROLE = ("object",)
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
    banks: Mapping[str, tuple[int, ...]],
    views: set[tuple[str, str, str]] | None = None,
    roles: tuple[str, ...] = _SPEAKING_ROLES,
) -> dict[str, tuple[int, ...]]:
    # Only parsed territory-v2 object/context banks at exactly 10 mm speak; ``roles``
    # narrows them to the object's own tiles where a question concerns its region alone.
    result: dict[str, tuple[int, ...]] = {}
    for name, counts in banks.items():
        parsed = parse_territory_bank_name(name)
        if parsed is None:
            continue
        if parsed.get("role") not in roles:
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


def _names_list(value: object) -> list[str] | None:
    """A list of unique nonempty object names, or None."""
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item and not item.startswith("diagnosis/")
        for item in value
    ):
        return None
    return value if len(set(value)) == len(value) else None


def identity_context_code(context: object, *, subject: str | None = None) -> str:
    """``valid`` or the first named defect of one object's identity context.

    The basis names what placed the object (``STRUCTURAL_READER``, ``MAP_RELATION`` or
    ``PRIOR_ONLY``) and its ``conditioning`` which other identities that leaves open:
    every one but the bones the structural reader established elsewhere in the study
    (``removed_by_structure``), the listed ``open_alternatives``, or all
    (``unconditioned``). Neither of the first and last is enumerated: a growth round
    recalls against a parent memory that may be another revision. ``support`` names what
    the region is by its territories' origin (``SUPPORT_KINDS``). Every
    ``contradictions`` row is a recorded ``reversed_*`` law check. ``subject``, when
    given, must be the context's own.
    """
    if not isinstance(context, Mapping) or context.get("schema") != CONTEXT_SCHEMA:
        return "identity_context_invalid"
    name = context.get("subject")
    if not isinstance(name, str) or not name or name.startswith("diagnosis/"):
        return "identity_context_subject_invalid"
    if subject is not None and name != subject:
        return "identity_context_subject_mismatch"
    basis = context.get("basis")
    if basis not in IDENTITY_BASES:
        return "identity_context_basis_invalid"
    if context.get("conditioning") != CONDITIONING[basis]:
        return "identity_context_conditioning_invalid"
    alternatives = _names_list(context.get("open_alternatives"))
    if alternatives is None or name in alternatives:
        return "identity_context_alternatives_invalid"
    if basis != MAP_RELATION and alternatives:
        return "identity_context_alternatives_invalid"
    removed = _names_list(context.get("removed_by_structure"))
    if removed is None or name in removed or set(removed) & set(alternatives):
        return "identity_context_removed_invalid"
    if context.get("support") not in SUPPORT_KINDS:
        return "identity_context_support_invalid"
    contradictions = context.get("contradictions")
    if not isinstance(contradictions, list) or not all(
        isinstance(row, Mapping)
        and isinstance(row.get("result"), str)
        and row["result"].startswith("reversed_")
        for row in contradictions
    ):
        return "identity_context_contradictions_invalid"
    if not isinstance(context.get("supporting_observations"), Mapping):
        return "identity_context_observations_invalid"
    return "valid"


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

    ``_opposition`` keeps, for each seed and each common-bank key, the largest
    resemblance to each opposing identity separately; ``_envelopes`` is their maximum,
    built in the same pass. A recall in context takes the maximum over only the
    identities its context leaves open; a call without context reads ``_envelopes``.

    A negative case's reason concerns the region it asserted, so each is also held over
    its object-role banks alone (``_negative_object_matrix``), with its envelope made
    over the same banks of its identity's positive seeds
    (``_negative_object_envelopes``): the candidate's object tiles against the
    negative's object tiles.
    """

    __slots__ = (
        "_envelopes",
        "_has_negatives",
        "_matrix",
        "_memory",
        "_negative_envelopes",
        "_negative_matrix",
        "_negative_object_envelopes",
        "_negative_object_matrix",
        "_negatives",
        "_opposition",
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
        opposition=(),
        negative_object_matrix=None,
        negative_object_envelopes=(),
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
        self._opposition = opposition
        self._negative_object_matrix = negative_object_matrix
        self._negative_object_envelopes = negative_object_envelopes

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


def confirm_call_views(row: object) -> dict[str, Any]:
    """The views one confirm call establishes its identity on.

    Read exactly as ``prepare_identity`` reads a seed's call: its ``views``,
    validated as unique exact view triples, or every view of the case when it
    names none (``views`` is then None); its ``negative_views`` and
    ``also_positive`` views give those views to other tissue and must not
    overlap. Returns ``{"outcome": "views", "views": frozenset | None}`` or the
    same named invalid_input ``prepare_identity`` gives.
    """
    if not isinstance(row, Mapping) or row.get("call") != "confirm":
        return _invalid("teaching_call_not_confirm")
    call_views = row.get("views")
    selected: set[tuple[str, ...]] | None = None
    if call_views is not None:
        selected = _view_set(call_views)
        if selected is None:
            return _invalid("teaching_call_views_invalid")
    other_claims = _other_view_claims(row)
    if other_claims is None:
        return _invalid("teaching_call_views_invalid")
    if other_claims and (selected is None or selected & other_claims):
        return _invalid("teaching_call_views_overlap")
    return {
        "outcome": "views",
        "views": None if selected is None else frozenset(selected),
    }


def identity_condition_views(memory: object) -> dict[str, Any]:
    """Where each object case's identity holds, found as identity recall finds it.

    CLASSICAL_AI_BUILD_DESIGN §5.1: a case's condition evidence speaks only
    through the views where its identity holds. A case's identity record is
    the one ``prepare_identity`` makes a seed of: its id is in
    ``confirmed_case_ids`` and exactly one call row names it, a confirm. A case
    without one has its identity established in no view. Returns
    ``{"outcome": "scoped", "views": {case_id: frozenset | None}, "calls":
    {candidate_id: (row, ...)}}``, None meaning every view, or the named
    invalid_input ``prepare_identity`` gives for the same teaching. Negative and
    alternative identity records are never read here: they live outside
    ``cases`` and carry no condition evidence.
    """
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
    views: dict[str, frozenset | None] = {}
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
        if case_id in views:
            return _invalid("duplicate_seed_case_id")
        resolved = confirm_call_views(rows[0])
        if resolved["outcome"] != "views":
            return resolved
        views[case_id] = resolved["views"]
    return {
        "outcome": "scoped",
        "views": views,
        "calls": {candidate: tuple(rows) for candidate, rows in rows_by_id.items()},
    }


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
                "object_banks": _signal_banks(banks, views, _OBJECT_ROLE),
                "asserted_alternatives": _asserted_alternatives(row, views),
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


def _asserted_alternatives(
    row: Mapping[str, Any], views: set[tuple[str, ...]]
) -> tuple[str, ...]:
    """The identities a call says the negative's own views show instead, sorted.

    An ``also_positive`` entry on another view says nothing about this negative.
    """
    items = row.get("also_positive")
    found = set()
    for item in items if isinstance(items, Sequence) else ():
        if not isinstance(item, Mapping) or not isinstance(item.get("identity"), str):
            continue
        claimed = _view_set(item.get("views"))
        if claimed is not None and claimed & views:
            found.add(item["identity"])
    return tuple(sorted(found))


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


def _fold(table: dict, key: Any, num: int, den: int, case_id: str) -> None:
    """Keep the largest exact squared cosine under ``key``, its tied cases and the count."""
    current = table.get(key)
    if current is None:
        table[key] = {"num": num, "den": den, "opponents": [case_id], "count": 1}
        return
    current["count"] += 1
    if num * current["den"] > current["num"] * den:
        current["num"], current["den"] = num, den
        current["opponents"] = [case_id]
    elif num * current["den"] == current["num"] * den:
        current["opponents"].append(case_id)


def _frozen_envelope(table: Mapping[Any, Mapping[str, Any]]) -> Mapping[Any, Any]:
    return MappingProxyType(
        {
            key: MappingProxyType({**value, "opponents": tuple(value["opponents"])})
            for key, value in table.items()
        }
    )


def _opposing_envelope(
    case: Mapping[str, Any],
    population: Sequence[Mapping[str, Any]],
    opposes,
    *,
    case_banks: Mapping[str, Sequence[int]] | None = None,
    population_banks: Sequence[Mapping[str, Sequence[int]]] | None = None,
) -> Mapping[tuple[str, ...], Mapping[str, Any]]:
    """Largest exact squared cosine to each opposing case over identical banks.

    The opposing side of a negative identity case is every positive seed of its own
    identity (a positive seed's side is made by ``_seed_envelopes``). ``case_banks`` and
    ``population_banks`` (aligned with ``population``) replace each side's own banks,
    so an envelope can be made over one role of both.
    """
    env: dict[tuple[str, ...], dict[str, Any]] = {}
    left = case["banks"] if case_banks is None else case_banks
    if isinstance(case["procedure"], str) and case["procedure"]:
        for index, other in enumerate(population):
            if not opposes(other) or not _same_procedure(
                case["procedure_view"], other["procedure_view"]
            ):
                continue
            right = (
                other["banks"] if population_banks is None else population_banks[index]
            )
            terms = _exact_bank_terms(left, right)
            if terms["code"] != "ok":
                continue
            num, den = terms["cosine_squared"]
            _fold(
                env, tuple(terms["common_speaking_banks"]), num, den, other["case_id"]
            )
    return _frozen_envelope(env)


def _seed_envelopes(
    case: Mapping[str, Any], population: Sequence[Mapping[str, Any]]
) -> tuple[Mapping[Any, Any], Mapping[Any, Any]]:
    """A positive seed's opposing envelope, overall and per opposing identity.

    The opposing side is every seed of another identity. One pass makes both: the
    overall maximum (exactly the envelope a call without context reads) and, under each
    common-bank key, the largest resemblance to each other identity separately.
    """
    overall: dict[tuple[str, ...], dict[str, Any]] = {}
    by_identity: dict[tuple[str, ...], dict[str, dict[str, Any]]] = {}
    if isinstance(case["procedure"], str) and case["procedure"]:
        for other in population:
            if other["subject"] == case["subject"] or not _same_procedure(
                case["procedure_view"], other["procedure_view"]
            ):
                continue
            terms = _exact_bank_terms(case["banks"], other["banks"])
            if terms["code"] != "ok":
                continue
            key = tuple(terms["common_speaking_banks"])
            num, den = terms["cosine_squared"]
            _fold(overall, key, num, den, other["case_id"])
            _fold(
                by_identity.setdefault(key, {}),
                other["subject"],
                num,
                den,
                other["case_id"],
            )
    return _frozen_envelope(overall), MappingProxyType(
        {key: _frozen_envelope(table) for key, table in by_identity.items()}
    )


def _frozen_entries(entries: Sequence[Mapping[str, Any]]) -> tuple:
    return tuple(
        MappingProxyType(
            {
                **entry,
                **{
                    key: MappingProxyType(dict(entry[key]))
                    for key in ("banks", "object_banks")
                    if key in entry
                },
                "procedure_view": MappingProxyType(entry["procedure_view"]),
            }
        )
        for entry in entries
    )


def _frozen_matrix(
    entries: Sequence[Mapping[str, Any]], key: str = "banks"
) -> Mapping[str, Any] | None:
    if not entries:
        return None
    built = _case_matrix([dict(entry[key]) for entry in entries])
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
    seed_envelopes = [_seed_envelopes(first, kept) for first in kept]
    envelopes = [overall for overall, _by_identity in seed_envelopes]
    opposition = [by_identity for _overall, by_identity in seed_envelopes]
    kept_negatives = [n for n in negatives if n["study_uid"] != exclude_study_uid]
    negative_envelopes = [
        _opposing_envelope(
            case, kept, lambda other, case=case: other["subject"] == case["subject"]
        )
        for case in kept_negatives
    ]
    # The same envelopes over the object role of both sides: the region each asserted.
    seed_object_banks = (
        [_signal_banks(seed["banks"], roles=_OBJECT_ROLE) for seed in kept]
        if kept_negatives
        else []
    )
    negative_object_envelopes = [
        _opposing_envelope(
            case,
            kept,
            lambda other, case=case: other["subject"] == case["subject"],
            case_banks=case["object_banks"],
            population_banks=seed_object_banks,
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
        opposition=tuple(opposition),
        negative_object_matrix=_frozen_matrix(kept_negatives, "object_banks"),
        negative_object_envelopes=tuple(negative_object_envelopes),
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
    profile: object,
    query_banks: Mapping[str, Sequence[int]],
    prepared: _Prepared,
    *,
    object_role: bool = False,
) -> list[dict[str, Any]]:
    """Each negative identity case's exact resemblance to the query, signed -1.

    A negative case is an ordinary case on its identity's negative side. It
    speaks against that identity only strictly above its own opposing envelope,
    the largest resemblance it shares with that identity's positive seeds over
    the same banks. With no such seed it stays silent, named; it is never a veto.
    ``object_role`` compares the query's object tiles with the negative's object
    tiles alone, against the envelope made over those banks.
    """
    negatives = prepared._negatives
    if object_role:
        query = _signal_banks(query_banks, roles=_OBJECT_ROLE)
        bank_key = "object_banks"
        matrix = prepared._negative_object_matrix
        envelopes = prepared._negative_object_envelopes
    else:
        query = query_banks
        bank_key = "banks"
        matrix = prepared._negative_matrix
        envelopes = prepared._negative_envelopes
    terms = _batch_terms(
        query,
        [case[bank_key] for case in negatives],
        matrix_cache=matrix,
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
        env = envelopes[index].get(key)
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


def _seed_row(
    seed: Mapping[str, Any],
    term: Mapping[str, Any],
    envelope: Mapping[str, Any] | None,
    missing_status: str,
) -> dict[str, Any]:
    """One seed's exact resemblance to the query, and whether it reaches past ``envelope``.

    It speaks only strictly above the envelope; with none it stays silent under
    ``missing_status``. An envelope made over named identities names them.
    """
    num, den = term["cosine_squared"]
    if envelope is None:
        status, speaks, env_out = missing_status, False, None
    else:
        speaks = num * envelope["den"] > envelope["num"] * den
        status = "above_envelope" if speaks else "not_above_envelope"
        env_out = {
            **_ratio(envelope["num"], envelope["den"]),
            "opponent_case_ids": list(envelope["opponents"]),
            "comparison_count": envelope["count"],
        }
        if "identities" in envelope:
            env_out["opposing_identities"] = list(envelope["identities"])
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
    return row


def _envelope_over(
    table: Mapping[str, Mapping[str, Any]] | None, allowed: frozenset[str]
) -> dict[str, Any] | None:
    """The largest opposing resemblance over the ``allowed`` identities only, or None.

    ``table`` is one seed's per-identity maxima under one common-bank key. Tied
    identities and their cases are all named; the count is every comparison made with
    an allowed identity's cases over those banks.
    """
    if table is None:
        return None
    best: dict[str, Any] | None = None
    count = 0
    for identity in sorted(allowed):
        entry = table.get(identity)
        if entry is None:
            continue
        count += entry["count"]
        if best is None or entry["num"] * best["den"] > best["num"] * entry["den"]:
            best = {
                "num": entry["num"],
                "den": entry["den"],
                "opponents": list(entry["opponents"]),
                "identities": [identity],
            }
        elif entry["num"] * best["den"] == best["num"] * entry["den"]:
            best["opponents"].extend(entry["opponents"])
            best["identities"].append(identity)
    if best is not None:
        best["count"] = count
    return best


def _squared(row: Mapping[str, Any]) -> Fraction:
    ratio = row["squared_cosine"]
    return Fraction(int(ratio["numerator"]), int(ratio["denominator"]))


def _also_resembles(
    compared: Mapping[str, Sequence[tuple[int, Mapping[str, Any], Mapping[str, Any]]]],
    subject: str,
    open_set: frozenset[str],
) -> list[dict[str, Any]]:
    """Each other identity's most resembling case, as information only.

    Equal resemblance goes to the smaller case id; the list runs from the most
    resembling identity down, by name on ties.
    """
    rows = []
    for identity, items in compared.items():
        if identity == subject:
            continue
        _index, seed, term = min(
            items,
            key=lambda item: (
                -Fraction(*item[2]["cosine_squared"]),
                item[1]["case_id"],
            ),
        )
        rows.append(
            {
                "identity": identity,
                "case_id": seed["case_id"],
                "squared_cosine": _ratio(*term["cosine_squared"]),
                "compared_cases": len(items),
                "open_alternative": identity in open_set,
            }
        )
    rows.sort(key=lambda row: (-_squared(row), row["identity"]))
    return rows


def _silence_reason(
    seeds: Sequence[Mapping[str, Any]], compatible: Sequence[bool], subject: str
) -> str:
    if not seeds:
        return "no_eligible_seed_cases"
    if not any(compatible):
        return "procedure_mismatch_no_compatible_seed"
    if not any(seed["subject"] == subject for seed in seeds):
        return "no_case_of_this_identity"
    return "no_common_speaking_banks"


def _bank_views(names: Sequence[str]) -> list[list[str]]:
    """The exact view triples of parsed territory-v2 bank names, once each, sorted."""
    views = set()
    for name in names:
        parsed = parse_territory_bank_name(name)
        if parsed is not None:
            views.add(tuple(parsed["view"]))
    return [list(view) for view in sorted(views)]


def identity_is_open(context: Mapping[str, Any], identity: str) -> bool:
    """Whether ``identity`` is still possible for the region, by what structure left open.

    A placement leaves its listed alternatives open; the structural reader and the prior
    leave every identity but those structure removed (none, for the prior).
    """
    if identity == context["subject"]:
        return True
    if context["basis"] == MAP_RELATION:
        return identity in context["open_alternatives"]
    return identity not in context["removed_by_structure"]


def _opposing_set(
    table: Mapping[str, Any] | None, context: Mapping[str, Any]
) -> frozenset[str]:
    """The identities whose cases set an own case's bar, under its context."""
    if table is None:
        return frozenset()
    if context["basis"] == MAP_RELATION:
        return frozenset(context["open_alternatives"])
    return frozenset(
        identity
        for identity in table
        if identity != context["subject"] and identity_is_open(context, identity)
    )


def _without_lineage(row: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key: value for key, value in row.items() if key != "lineage"}


def _negatives_in_context(
    profile: object,
    query_banks: Mapping[str, Sequence[int]],
    prepared: _Prepared,
    context: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], int]:
    """Each negative case that speaks in either comparison, and whether it applies here.

    A negative case's reason concerns the region it asserted, so it applies when it
    speaks over the asserted region alone: the candidate's object tiles against its own
    object tiles, above its envelope over the same banks. Speaking only when the
    surroundings (the context ring) are read too, it is ``surroundings_only``. A negative
    of another identity concerns another question. One whose call asserts an alternative
    identity applies only while that alternative is still open (``identity_is_open``).
    A negative that applies takes part as an ordinary signed case; one that does not is
    recorded with its reason and changes nothing. Returns the rows and how many negative
    cases were compared at all.
    """
    if not prepared._negatives:
        return [], 0
    with_ring = {
        row["case_id"]: row
        for row in _negative_evidence(profile, query_banks, prepared)
    }
    over_region = {
        row["case_id"]: row
        for row in _negative_evidence(profile, query_banks, prepared, object_role=True)
    }
    rows = []
    for case in prepared._negatives:
        region, ring = over_region.get(case["case_id"]), with_ring.get(case["case_id"])
        speaks_region = region is not None and region["speaks"]
        if not (speaks_region or (ring is not None and ring["speaks"])):
            continue
        alternatives = list(case["asserted_alternatives"])
        if case["subject"] != context["subject"]:
            applies, reason = False, "concerns_another_identity"
        elif not speaks_region:
            applies, reason = False, "surroundings_only"
        elif alternatives and not any(
            identity_is_open(context, identity) for identity in alternatives
        ):
            applies, reason = False, "asserted_alternative_removed_by_structure"
        else:
            applies, reason = True, "speaks_over_the_asserted_region"
        rows.append(
            {
                "case_id": case["case_id"],
                "identity": case["subject"],
                "digit": -1,
                "study_uid": case["study_uid"],
                "views": [list(view) for view in case["views"]],
                "asserted_alternatives": alternatives,
                "call_notes": (case["lineage"].get("call") or {}).get("notes"),
                "applies": applies,
                "reason": reason,
                "over_the_asserted_region": _without_lineage(region),
                "with_the_surroundings": _without_lineage(ring),
                "lineage": copy.deepcopy(case["lineage"]),
            }
        )
    return rows, len(set(with_ring) | set(over_region))


def _unconditioned_speakers(
    compared: Mapping[str, Sequence[tuple[int, Mapping[str, Any], Mapping[str, Any]]]],
    prepared: _Prepared,
) -> list[str]:
    """The identities whose cases speak above their envelopes over every other identity."""
    speakers = set()
    for identity, items in compared.items():
        for index, _seed, term in items:
            envelope = prepared._envelopes[index].get(
                tuple(term["common_speaking_banks"])
            )
            num, den = term["cosine_squared"]
            if envelope is not None and num * envelope["den"] > envelope["num"] * den:
                speakers.add(identity)
                break
    return sorted(speakers)


def _recall_in_context(
    profile: object,
    query_banks_all: Mapping[str, tuple[int, ...]],
    prepared: _Prepared,
    status_name: str,
    context: Mapping[str, Any],
) -> dict[str, Any]:
    """Recall conditioned on what the current study's structure already established.

    The located object's identity is the context's subject, never renamed. Its own cases
    speak against the identities the context leaves open (``_opposing_set``): for a bone
    the structural reader established, every identity but the reader's other bones,
    which it tells apart by their observed arrangement, found in this study or not; for
    a placement, the alternatives whose own proposals overlap it; for the prior, every
    other identity. One speaking is the appearance supporting the identity; with no
    comparable opposing case it is uncalibrated.

    Negative cases apply where their reason holds for the candidate's actual support
    (``_negatives_in_context``). An applicable negative speaking with no own case is
    ``appearance_opposed``; with one, a ``signed_conflict`` kept open. Either leaves the
    identity contested and revisable. Otherwise the reader's bone is
    ``established_by_structure``, and a placement or the prior is
    ``appearance_supports``, ``appearance_silent`` or ``placement_only`` (uncalibrated).
    Every other identity's resemblance is kept as information (``also_resembles``); a
    placement also hears each open alternative against the rest
    (``open_alternative_resembles``), and the prior records which identities speak
    unconditioned. A contradicted anatomical check never blocks here: the context's
    contradictions are carried as revisable evidence for the consumers that act on them.
    """
    subject = context["subject"]
    basis = context["basis"]
    seeds = prepared._seeds
    query_banks = _signal_banks(query_banks_all)
    compatible = [_same_procedure(profile, seed["procedure_view"]) for seed in seeds]
    terms = (
        _batch_terms(
            query_banks,
            [seed["banks"] for seed in seeds],
            matrix_cache=prepared._matrix,
            compatible=compatible,
        )
        if any(compatible)
        else [None] * len(seeds)
    )
    compared: dict[str, list[tuple[int, Mapping[str, Any], Mapping[str, Any]]]] = {}
    for index, (seed, term) in enumerate(zip(seeds, terms, strict=True)):
        if term is not None and term["code"] == "ok":
            compared.setdefault(seed["subject"], []).append((index, seed, term))
    open_set = frozenset(context["open_alternatives"])

    def heard(identity: str, opposing) -> list[dict[str, Any]]:
        rows = []
        for index, seed, term in compared.get(identity, ()):
            table = prepared._opposition[index].get(
                tuple(term["common_speaking_banks"])
            )
            allowed = opposing(table)
            envelope = _envelope_over(table, allowed) if allowed else None
            missing = (
                "no_compatible_opposing_case"
                if allowed or basis != MAP_RELATION
                else "no_open_alternative"
            )
            rows.append(_seed_row(seed, term, envelope, missing))
        return rows

    own = heard(subject, lambda table: _opposing_set(table, context))
    if not own:
        appearance = "silent"
    elif any(row["speaks"] for row in own):
        appearance = "supports"
    elif all(row["envelope"] is None for row in own):
        appearance = "uncalibrated"
    else:
        appearance = "silent"
    negatives, compared_negatives = _negatives_in_context(
        profile, query_banks, prepared, context
    )
    applicable = [row["case_id"] for row in negatives if row["applies"]]
    presentation = "compared" if own else _silence_reason(seeds, compatible, subject)
    if applicable:
        outcome = SIGNED_CONFLICT if appearance == "supports" else APPEARANCE_OPPOSED
        reason = (
            "own_case_and_applicable_negative_case_speak"
            if outcome == SIGNED_CONFLICT
            else "applicable_negative_case_speaks_and_no_own_case"
        )
        state = "contested"
    elif basis == STRUCTURAL_READER:
        outcome, reason = (
            ESTABLISHED_BY_STRUCTURE,
            "identity_established_by_structural_reader",
        )
        state = "established"
    else:
        outcome = {
            "supports": APPEARANCE_SUPPORTS,
            "silent": APPEARANCE_SILENT,
            "uncalibrated": PLACEMENT_ONLY,
        }[appearance]
        reason = {
            "supports": "own_case_above_the_open_identities",
            "silent": "no_own_case_above_the_open_identities" if own else presentation,
            "uncalibrated": "no_open_alternative"
            if basis == MAP_RELATION and not open_set
            else "no_comparable_opposing_case",
        }[appearance]
        state = "placed" if basis == MAP_RELATION else "unconditioned"
    result: dict[str, Any] = {
        "schema": RECALL_CONTEXT_SCHEMA,
        "proposed_name": _proposed_name(profile),
        "identity": subject,
        "identity_basis": basis,
        "identity_state": state,
        "support": context["support"],
        "conditioning": context["conditioning"],
        "open_alternatives": sorted(open_set),
        "removed_by_structure": sorted(context["removed_by_structure"]),
        "outcome": outcome,
        "reason": reason,
        "appearance": appearance,
        "sanity": {"status": status_name},
        "prepared_view": {
            "schema": PREPARATION_SCHEMA,
            "source_pin": prepared["source_pin"],
        },
        "presentation": presentation,
        "cases": own,
        "nearest_cases": [
            row["case_id"]
            for row in sorted(own, key=lambda row: (-_squared(row), row["case_id"]))
        ],
        "speaking_case_ids": sorted(row["case_id"] for row in own if row["speaks"]),
        "also_resembles": _also_resembles(compared, subject, open_set),
        "negative_cases": negatives,
        "applicable_negative_case_ids": applicable,
        "negative_cases_compared": compared_negatives,
        "contradictions": copy.deepcopy(list(context["contradictions"])),
        "calibrated_probability": False,
    }
    if basis == STRUCTURAL_READER:
        result["established_views"] = _bank_views(list(query_banks))
    elif basis == MAP_RELATION:
        resembles: list[str] = []
        alternative_cases: list[dict[str, Any]] = []
        for alternative in sorted(open_set):
            others = (open_set | {subject}) - {alternative}
            speaking = [
                row
                for row in heard(alternative, lambda table, others=others: others)
                if row["speaks"]
            ]
            if speaking:
                resembles.append(alternative)
                alternative_cases.extend(speaking)
        result.update(
            open_alternative_resembles=resembles,
            open_alternative_cases=alternative_cases,
        )
    else:
        speakers = _unconditioned_speakers(compared, prepared)
        result.update(
            unconditioned_speaking_identities=speakers,
            unconditioned_identity=speakers[0] if len(speakers) == 1 else None,
        )
    return result


def recall_identity(
    profile: object,
    memory: object,
    *,
    exclude_study_uid: str | None = None,
    sanity: object = None,
    prepared: Mapping[str, Any] | None = None,
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Score one query against the signed identity cases.

    Without ``context``: positive seeds speak for their identity and negative identity
    cases against theirs, each only above its own opposing envelope. An identity spoken
    for and against is a conflict; one spoken against only is recorded in
    ``opposed_identities`` and cannot be identified.

    With ``context`` (``identity_context_code``), recall is conditioned on what the
    current study's structure already established (``_recall_in_context``): the
    located object keeps its identity, its own cases speak against the identities the
    context leaves open, and a negative case applies only where its reason holds for the
    candidate's actual support. A ``PRIOR_ONLY`` context leaves every identity open.

    A prepared view is valid only for the same memory object and exclusion it was built
    from; anything else returns invalid_preparation without scoring.
    """
    status_name = _sanity_status(sanity)
    if status_name is None:
        return _invalid("sanity_invalid")
    if context is not None:
        # The context's subject is the located object; the profile's name stays a
        # proposed label and can force nothing either way.
        code = identity_context_code(context)
        if code != "valid":
            return _invalid(code)
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
    if context is not None:
        return _recall_in_context(
            profile, query_banks_all, prepared, status_name, context
        )
    return _recall_unconditioned(profile, query_banks_all, prepared, status_name)


def _recall_unconditioned(
    profile: object,
    query_banks_all: Mapping[str, tuple[int, ...]],
    prepared: _Prepared,
    status_name: str,
) -> dict[str, Any]:
    """The recall without context: every identity's seeds against every other's."""
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
        env = prepared._envelopes[index].get(tuple(term["common_speaking_banks"]))
        missing_envelope = missing_envelope or env is None
        evidence.append(_seed_row(seed, term, env, "no_compatible_opposing_case"))
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
