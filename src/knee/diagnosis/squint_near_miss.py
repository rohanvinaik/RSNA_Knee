"""Near-miss RECORDS for the identity agency (SOCIETY_OF_MIND_TRAINING section 5, Lane A).

A reviewer CORRECTED an identity proposal: the call says "not this object" at some view.  A record
keeps that correction beside (a) what the memory EXPECTED, the positive precedents that actually spoke
for the proposal in the inference record that produced it, and (b) how it was wrong, the reviewer's
own call row; and it lays out (c) every decoded difference between the failure's bundle and each
speaking positive precedent, and (d) where each of those readings sits among the other successes.

It is retained teaching material for the identity agency and for the next review.  It decides
nothing (CLASSICAL_AI_BUILD_DESIGN section 5, thesis 8.6):

* no censor and no split is written, and nothing here can write one;
* no threshold, alpha, chance test, ratio or verdict, and no count of changed banks is evidence;
* no decoded reading is "the" significant difference.  Every reading over the shared banks is kept,
  sorted by size for display only;
* the expectation is only what an inference record says spoke.  No precedent is chosen after the fact:
  a correction whose proposal no recall produced is kept as ``expectation_unavailable`` with its reason;
* a refusal, an unsure call, a plain confirmation and an unreviewed proposal are never corrections.

Comparison is made only where question, view, scale and measurement meaning are compatible: the same
bank name (view, role, metric, direction and scale are in the name) and the same profile procedure.
Every count carries the case ids of the population it was counted over.

Pure functions: no I/O.  The inference records, the memory and the prepared bundles are handed in.
The profile is the squint-profile/v1 bank mapping: bank name -> exact counts of its three rows
(tiles below, within and above the leg's middle third).  ``decode_count_names`` and
``compare_named_profiles`` read CountBundle layouts and do not apply to these dictionaries; the count
is already the exact decode, and the bank's meaning comes from ``parse_territory_bank_name``.
"""

from __future__ import annotations

import copy
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from fractions import Fraction
from typing import Any

from knee.diagnosis.squint_interfaces import parse_territory_bank_name

SCHEMA = "knee.near-miss-record/v1"
RECORDS_SCHEMA = "knee.near-miss-records/v1"

# A squint bank's three rows, in order: negative, middle, positive counts.
ROW_NAMES = ("below", "middle", "above")

STATE_DIFFERENCES = "differences_present"
STATE_AGREE = "agree_on_every_shared_row"
STATE_NO_SHARED_BANK = "no_bank_read_on_both_profiles"
STATE_NOT_COMPARED = "not_compared"

STATEMENTS = {
    STATE_DIFFERENCES: "the profiles differ on at least one row of a bank both read",
    STATE_AGREE: "the profiles agree on every row of every bank both read",
    STATE_NO_SHARED_BANK: "no bank was read on both profiles, so nothing was compared",
}

DISPLAY_ORDER = (
    "absolute share difference, largest first; ties in canonical order (bank name, row index). "
    "A display order only: no reading here is the significant difference."
)

EXPECTATION_TRACED = "expectation_traced"
EXPECTATION_UNAVAILABLE = "expectation_unavailable"

STATUS_RECORDED = "expectation_recorded"
STATUS_NO_POSITIVE_SPOKE = "traced_no_positive_precedent_spoke"
STATUS_UNAVAILABLE = EXPECTATION_UNAVAILABLE

ORIGIN_ADMISSION = "recognition_derived_admission"
ORIGIN_CATALOGUE = "structure_catalogue_proposal"
ORIGIN_DRAWN = "reviewer_drawn_support"
ORIGIN_UNCLASSIFIED = "unclassified"

CALL_REJECT = "reject"
CALL_CONFIRM_NEGATIVE_VIEWS = "confirm_with_negative_views"

SCOPE_STATED = "stated_by_reviewer"
SCOPE_DERIVED = "derived_by_publisher_from_every_drawn_profile_view"

LINEAGE_ADMISSION = "recognition_derived_admission"
LINEAGE_ALTERNATIVE = "alternative_identity_positive"
LINEAGE_DIRECT_VISUAL = "direct_visual_call"
LINEAGE_CATALOGUE_VISUAL = "catalogue_visual_call"

REASONS = {
    "structure_catalogue_proposal": (
        "The proposal is the structure's bootstrap naming of a catalogue candidate (case id prefix "
        "'squint-case:'), reviewed as an uncalled proposal. No identity recall produced it and the "
        "case carries no identity_growth lineage, so no inference record holds an expectation for it."
    ),
    "reviewer_drawn_support": (
        "The support was drawn by a reviewer (case id prefix 'direct-visual:'). It is not a "
        "proposal that a recall produced, so no inference record holds an expectation for it."
    ),
    "unclassified_origin": (
        "The case id and record name no recall: no inference record can be traced for it."
    ),
    "no_identity_growth_lineage": (
        "The admission carries no identity_growth lineage naming the inference record it came from."
    ),
    "inference_record_not_named": (
        "The identity_growth lineage does not name the inference record by file-bytes sha256."
    ),
    "inference_record_not_found": (
        "No inference record with the named file-bytes sha256 was found under the searched roots."
    ),
    "inference_record_study_mismatch": (
        "The inference record found under the named sha256 belongs to another study."
    ),
    "no_recall_entry_for_object": (
        "The inference record holds no identity recall entry for the located object at the "
        "admission's scale."
    ),
    "recorded_identity_differs": (
        "The recall entry's recognized identity differs from the admission's recognized identity."
    ),
    "speaking_set_differs_from_growth_lineage": (
        "The speaking cases in the inference record are not the speaking_case_ids recorded in the "
        "admission's lineage, so the record is not shown to be the one that produced it."
    ),
}


# ----------------------------------------------------------------------------- exact bank readings


def read_counts(value: object) -> tuple[int, ...] | None:
    """A bank's exact row counts, or None unless they are nonnegative plain integers."""
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or not value:
        return None
    if any(type(item) is not int or item < 0 for item in value):
        return None
    return tuple(value)


def _reading(banks: Mapping[str, Any], name: str) -> tuple[str, tuple[int, ...] | None]:
    """("read" | "silent" | "malformed", counts) for one bank of one profile.

    Silent is an absent bank or one whose rows are all zero: nothing was read there.
    """
    if name not in banks:
        return "silent", None
    counts = read_counts(banks[name])
    if counts is None:
        return "malformed", None
    if not any(counts):
        return "silent", counts
    return "read", counts


def bank_states(
    failure_banks: Mapping[str, Any], precedent_banks: Mapping[str, Any]
) -> dict[str, list[str]]:
    """Which banks both profiles read, and which only one reads. Names only, sorted.

    ``shared`` banks have nonzero counts on both sides and the same row layout; they alone are
    compared.  A bank read on one side only, or silent on both, never counts as a difference.
    """
    result: dict[str, list[str]] = {
        "shared": [],
        "failure_only": [],
        "precedent_only": [],
        "silent_on_both": [],
        "malformed": [],
    }
    for name in sorted(set(failure_banks) | set(precedent_banks)):
        left, left_counts = _reading(failure_banks, name)
        right, right_counts = _reading(precedent_banks, name)
        if "malformed" in (left, right):
            result["malformed"].append(name)
        elif left == "read" and right == "read":
            same_layout = len(left_counts or ()) == len(right_counts or ())
            result["shared" if same_layout else "malformed"].append(name)
        elif left == "read":
            result["failure_only"].append(name)
        elif right == "read":
            result["precedent_only"].append(name)
        else:
            result["silent_on_both"].append(name)
    return result


def bank_meaning(name: str) -> dict[str, Any] | None:
    """The bank's view, role, metric, direction and scale, or None for a name that does not parse."""
    fields = parse_territory_bank_name(name)
    if fields is None:
        return None
    return {
        "view": list(fields["view"]),
        "role": fields["role"],
        "metric": fields["metric"],
        "direction": fields["direction"],
        "scale": fields["scale"],
    }


def _row_name(row: int) -> str:
    return ROW_NAMES[row] if row < len(ROW_NAMES) else f"row{row}"


def _share_view(count: int, total: int) -> dict[str, Any]:
    return {
        "count": count,
        "total": total,
        "fraction": f"{count}/{total}",
        "float": float(Fraction(count, total)),
    }


def _fraction_view(value: Fraction) -> dict[str, Any]:
    return {"exact": str(value), "float": float(value)}


# ----------------------------------------------------------------------------- decoded differences


def decoded_differences(
    failure_banks: Mapping[str, Any], precedent_banks: Mapping[str, Any]
) -> dict[str, Any]:
    """Every decoded reading of a failure's bundle against one precedent's, over the shared banks.

    For each bank both profiles read, each row's exact share (count / the bank's total) on both
    sides and their exact difference, failure minus precedent.  The list is sorted for display
    only (``DISPLAY_ORDER``); no entry is the significant difference, and a row on which the two
    agree stays in the list.  Banks read on one side only, silent on both, or malformed are listed
    by name and never counted as a difference.
    """
    states = bank_states(failure_banks, precedent_banks)
    entries: list[tuple[Fraction, str, int, dict[str, Any]]] = []
    for bank in states["shared"]:
        failure_counts = read_counts(failure_banks[bank]) or ()
        precedent_counts = read_counts(precedent_banks[bank]) or ()
        failure_total = sum(failure_counts)
        precedent_total = sum(precedent_counts)
        meaning = bank_meaning(bank)
        for row, (left, right) in enumerate(
            zip(failure_counts, precedent_counts, strict=True)
        ):
            difference = Fraction(left, failure_total) - Fraction(
                right, precedent_total
            )
            entries.append(
                (
                    abs(difference),
                    bank,
                    row,
                    {
                        "bank": bank,
                        "row": row,
                        "row_name": _row_name(row),
                        "meaning": copy.deepcopy(meaning),
                        "failure": _share_view(left, failure_total),
                        "precedent": _share_view(right, precedent_total),
                        "difference": _fraction_view(difference),
                        "absolute_difference": _fraction_view(abs(difference)),
                    },
                )
            )
    entries.sort(key=lambda item: (-item[0], item[1], item[2]))
    differing = sum(1 for magnitude, _bank, _row, _item in entries if magnitude)
    if not states["shared"]:
        state = STATE_NO_SHARED_BANK
    elif differing:
        state = STATE_DIFFERENCES
    else:
        state = STATE_AGREE
    return {
        "state": state,
        "statement": STATEMENTS[state],
        "shared_banks": states["shared"],
        "failure_only_banks": states["failure_only"],
        "precedent_only_banks": states["precedent_only"],
        "silent_banks": states["silent_on_both"],
        "malformed_banks": states["malformed"],
        "compared_cell_count": len(entries),
        "differing_cell_count": differing,
        "display_order": DISPLAY_ORDER,
        "differences_sorted_for_display": [item for _m, _b, _r, item in entries],
    }


# ----------------------------------------------------------------------------- the other successes


def lineage_kind(entry: Mapping[str, Any]) -> str:
    """How a positive case came to be taught: admission, alternative positive, direct or catalogue call."""
    call = (entry.get("lineage") or {}).get("call") or {}
    if "source_case_id" in entry:
        return LINEAGE_ALTERNATIVE
    if isinstance(call.get("identity_growth"), Mapping):
        return LINEAGE_ADMISSION
    if str(entry.get("case_id", "")).startswith("direct-visual:"):
        return LINEAGE_DIRECT_VISUAL
    return LINEAGE_CATALOGUE_VISUAL


def success_population(
    successes: Sequence[Mapping[str, Any]],
    *,
    subject: str,
    failure_case_id: str,
    failure_study_uid: str,
    failure_procedure: object,
    precedent_case_id: str,
) -> dict[str, Any]:
    """Who may be counted as an other success of this failure and this precedent.

    The population is the positive cases of the same question (the proposed identity) with the
    failure's own profile procedure, other than the compared precedent, the failure's own case, and
    any case of the failure's whole study.  Each exclusion is listed with its reason.  ``members``
    is the population in case-id order; per-reading indices refer to that order.
    """
    members: list[Mapping[str, Any]] = []
    excluded: list[dict[str, str]] = []
    other_questions = 0
    for entry in sorted(successes, key=lambda item: str(item.get("case_id"))):
        if entry.get("subject") != subject:
            other_questions += 1
            continue
        case_id = str(entry.get("case_id"))
        if case_id == precedent_case_id:
            reason = "is_the_compared_precedent"
        elif case_id == failure_case_id:
            reason = "is_the_failure_case"
        elif entry.get("study_uid") == failure_study_uid:
            reason = "failure_study"
        elif entry.get("procedure") != failure_procedure:
            reason = "procedure_differs"
        else:
            members.append(entry)
            continue
        excluded.append({"case_id": case_id, "reason": reason})
    return {
        "question": f"identity:{subject}",
        "profile_procedure": failure_procedure,
        "members": members,
        "excluded": excluded,
        "other_questions_not_considered": other_questions,
    }


def reading_sides(
    bank: str,
    row: int,
    failure_share: Fraction,
    precedent_share: Fraction,
    members: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Where each other success sits on one reading, against the failure's value.

    ``precedent_side``: strictly on the precedent's side of the failure's value (the precedent's
    own distance is not a limit); ``beyond_failure``: strictly on the other side, beyond the
    failure's value and away from the precedent; ``equal_to_failure``; ``bank_not_read``: the
    success did not read the bank (it is on neither side).  Members are indices into the
    population.  When the precedent equals the failure on this row there is no side to take.
    """
    if precedent_share == failure_share:
        return {"skipped": "precedent_equals_failure_on_this_row"}
    toward = 1 if precedent_share > failure_share else -1
    indices: dict[str, list[int]] = {
        "precedent_side": [],
        "beyond_failure": [],
        "equal_to_failure": [],
        "bank_not_read": [],
    }
    for index, member in enumerate(members):
        state, counts = _reading(member.get("banks") or {}, bank)
        if state != "read" or counts is None or row >= len(counts):
            indices["bank_not_read"].append(index)
            continue
        value = Fraction(counts[row], sum(counts))
        delta = (value - failure_share) * toward
        if delta > 0:
            indices["precedent_side"].append(index)
        elif delta < 0:
            indices["beyond_failure"].append(index)
        else:
            indices["equal_to_failure"].append(index)
    return {
        "members": indices,
        "counts": {key: len(value) for key, value in indices.items()},
        "population_size": len(members),
    }


def precedent_unavailable(case_id: str) -> dict[str, Any]:
    """A speaking precedent whose bundle the memory in hand does not hold: kept, never replaced."""
    return {
        "precedent_case_id": case_id,
        "state": STATE_NOT_COMPARED,
        "reason": "precedent_bundle_unavailable",
    }


def failure_unavailable(case_id: str) -> dict[str, Any]:
    """A speaking precedent that could not be compared because the failure's bundle is not held."""
    return {
        "precedent_case_id": case_id,
        "state": STATE_NOT_COMPARED,
        "reason": "failure_bundle_unavailable",
    }


def verify_recorded_terms(
    voice: Mapping[str, Any],
    query_banks: Mapping[str, Any] | None,
    precedent_banks: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Whether the bundles in hand are the ones that spoke, by the recorded cosine terms.

    The inference record states, for each speaking case, the banks the cosine was taken over
    (``common_speaking_banks``) and its exact terms (``dot``, ``left_norm_sq`` from the query,
    ``right_norm_sq`` from the case).  Recomputing them over exactly those banks from the query
    profile and the precedent bundle in hand reproduces the record when, and only when, both are
    the bundles that spoke.  Anything else (a bank gone silent, a count changed, no terms recorded)
    does not match, and the pair must not be compared.
    """
    banks = list(voice.get("common_speaking_banks") or ())
    recorded = {key: voice.get(key) for key in ("dot", "left_norm_sq", "right_norm_sq")}
    dot = left_sq = right_sq = 0
    missing: list[str] = []
    for name in banks:
        query = read_counts((query_banks or {}).get(name))
        precedent = read_counts((precedent_banks or {}).get(name))
        if (
            query is None
            or precedent is None
            or len(query) != len(precedent)
            or not any(query)
            or not any(precedent)
        ):
            missing.append(name)
            continue
        dot += sum(a * b for a, b in zip(query, precedent, strict=True))
        left_sq += sum(a * a for a in query)
        right_sq += sum(b * b for b in precedent)
    recomputed = {"dot": dot, "left_norm_sq": left_sq, "right_norm_sq": right_sq}
    return {
        "bank_count": len(banks),
        "recorded": recorded,
        "recomputed": recomputed,
        "banks_unreadable_now": missing,
        "matches": bool(banks) and not missing and recomputed == recorded,
    }


def compare_speaking_precedent(
    voice: Mapping[str, Any],
    query_banks: Mapping[str, Any] | None,
    failure: Mapping[str, Any],
    precedent: Mapping[str, Any],
    successes: Sequence[Mapping[str, Any]],
    bundles_from: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare the failure with a precedent that spoke, but only if its bundle is the one that spoke.

    The recorded terms are recomputed first (``verify_recorded_terms``).  A bundle that no longer
    reproduces them is a different precedent from the one the expectation names, so the pair is kept
    as ``not_compared`` with the check, never compared.  Each block says which memory, scale and
    preparation the compared bundles came from.
    """
    check = verify_recorded_terms(voice, query_banks, precedent.get("banks"))
    source = copy.deepcopy(dict(bundles_from)) if bundles_from is not None else None
    if not check["matches"]:
        return {
            "precedent_case_id": precedent.get("case_id"),
            "state": STATE_NOT_COMPARED,
            "reason": "bundle_differs_from_the_one_that_spoke",
            "recorded_terms_check": check,
            "bundles_from": source,
        }
    block = compare_with_precedent(failure, precedent, successes)
    block["bundle_matches_recorded_terms"] = True
    block["recorded_terms_check"] = check
    block["bundles_from"] = source
    return block


def compare_with_precedent(
    failure: Mapping[str, Any],
    precedent: Mapping[str, Any],
    successes: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """The failure's bundle against one speaking positive precedent, with every counted population.

    ``failure`` and ``precedent`` carry case_id, subject (the identity asserted), study_uid,
    procedure and banks.  They are compared only where the question (the identity) and the profile
    procedure are the same, and then only over banks of the same name.
    """
    if precedent is None:
        raise ValueError(
            "a missing precedent bundle is recorded with precedent_unavailable"
        )
    block: dict[str, Any] = {"precedent_case_id": precedent.get("case_id")}
    compatibility = {
        "question": failure.get("subject") == precedent.get("subject"),
        "procedure": failure.get("procedure") == precedent.get("procedure"),
        "failure_procedure": failure.get("procedure"),
        "precedent_procedure": precedent.get("procedure"),
    }
    block["precedent_identity"] = precedent.get("subject")
    block["precedent_study_uid"] = precedent.get("study_uid")
    block["failure_views"] = copy.deepcopy(failure.get("views"))
    block["precedent_views"] = copy.deepcopy(precedent.get("views"))
    block["compatibility"] = compatibility
    if not (compatibility["question"] and compatibility["procedure"]):
        reason = (
            "question_differs" if not compatibility["question"] else "procedure_differs"
        )
        return {**block, "state": STATE_NOT_COMPARED, "reason": reason}
    decoded = decoded_differences(
        failure.get("banks") or {}, precedent.get("banks") or {}
    )
    population = success_population(
        successes,
        subject=str(failure.get("subject")),
        failure_case_id=str(failure.get("case_id")),
        failure_study_uid=str(failure.get("study_uid")),
        failure_procedure=failure.get("procedure"),
        precedent_case_id=str(precedent.get("case_id")),
    )
    members = population["members"]
    for item in decoded["differences_sorted_for_display"]:
        failure_share = Fraction(item["failure"]["count"], item["failure"]["total"])
        precedent_share = Fraction(
            item["precedent"]["count"], item["precedent"]["total"]
        )
        item["success_side"] = reading_sides(
            item["bank"], item["row"], failure_share, precedent_share, members
        )
    decoded["success_population"] = {
        "question": population["question"],
        "profile_procedure": population["profile_procedure"],
        "size": len(members),
        "members": [
            {
                "index": index,
                "case_id": member.get("case_id"),
                "study_uid": member.get("study_uid"),
                "lineage_kind": lineage_kind(member),
            }
            for index, member in enumerate(members)
        ],
        "excluded": population["excluded"],
        "other_questions_not_considered": population["other_questions_not_considered"],
    }
    return {**block, **decoded}


# ----------------------------------------------------------------------------- the corrections


def proposal_origin(case_id: str, record: Mapping[str, Any] | None) -> str:
    """Where the corrected proposal came from, from its lineage and its id alone."""
    if isinstance((record or {}).get("identity_growth"), Mapping):
        return ORIGIN_ADMISSION
    if case_id.startswith("squint-case:"):
        return ORIGIN_CATALOGUE
    if case_id.startswith("direct-visual:"):
        return ORIGIN_DRAWN
    return ORIGIN_UNCLASSIFIED


def _growth_round(
    case_id: str, growth: Mapping[str, Any] | None
) -> dict[str, Any] | None:
    rounds = (growth or {}).get("rounds")
    if not isinstance(rounds, Sequence) or isinstance(rounds, (str, bytes)):
        return None
    for index, entry in enumerate(rounds):
        if isinstance(entry, Mapping) and case_id in (
            entry.get("admitted_case_ids") or ()
        ):
            return {
                "round_index": index,
                "parent_manifest_sha256": entry.get("parent_manifest_sha256"),
                "decisions_sha256": entry.get("decisions_sha256"),
                "state_counts": copy.deepcopy(entry.get("state_counts")),
            }
    return None


def _round_of(correction_block: object, teaching: Mapping[str, Any]) -> dict[str, Any]:
    """The review that made the correction, from the pins the memory itself carries."""
    if isinstance(correction_block, Mapping):
        return {
            "kind": "admission_review",
            "review_sha256": correction_block.get("review_sha256"),
            "reviewed_manifest_sha256": correction_block.get(
                "reviewed_manifest_sha256"
            ),
            "reviewed_revision": correction_block.get("reviewed_revision"),
        }
    return {
        "kind": "seed_catalogue_review",
        "teaching_review_sha256": teaching.get("review_sha256"),
        "teaching_source_manifest_sha256": teaching.get("source_manifest_sha256"),
    }


def enumerate_corrections(
    teaching: Mapping[str, Any],
    identity_cases: Mapping[str, Any] | None,
    growth: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Every reviewer call that says "not this object" at some view, and the calls that do not.

    A correction is a reject call, or a confirm call that carries ``negative_views``.  An unsure
    call, a plain confirmation and a confirmation that only names an alternative identity are
    listed as not corrections, with the reason.  Each correction keeps the reviewer's call row
    verbatim; the views the identity reader takes it to reject are the teaching table's
    ``negative_views``, and where the reviewer stated none (a reject without views) they are
    marked as derived by the publisher, not stated by the reviewer.
    """
    rows = teaching.get("calls") or []
    written = set(teaching.get("negative_case_ids") or ())
    effective = teaching.get("negative_views") or {}
    records: dict[str, Mapping[str, Any]] = {}
    for record in (identity_cases or {}).get("cases") or ():
        if isinstance(record, Mapping) and isinstance(record.get("case_id"), str):
            records[record["case_id"]] = record
    corrections: list[dict[str, Any]] = []
    not_corrections: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        case_id = str(row.get("candidate_id"))
        call = row.get("call")
        if call == "reject":
            kind = CALL_REJECT
        elif call == "confirm" and row.get("negative_views"):
            kind = CALL_CONFIRM_NEGATIVE_VIEWS
        else:
            reason = {
                "unsure": "unsure_call_is_never_a_correction",
                "confirm": "confirmed_without_negative_views",
            }.get(str(call), "not_a_reject_or_a_confirm_with_negative_views")
            not_corrections.append(
                {"case_id": case_id, "call": str(call), "reason": reason}
            )
            continue
        record = records.get(case_id)
        correction_block = (record or {}).get("identity_correction")
        if isinstance(correction_block, Mapping) and isinstance(
            correction_block.get("call"), Mapping
        ):
            # A reviewed admission: the published row is the writer's (an admission confirm row
            # narrowed to the views that still speak, or the reject row); the reviewer's own call
            # and name are in the correction block.
            reviewer_call = copy.deepcopy(dict(correction_block["call"]))
            reader = correction_block.get("corrected_by") or reviewer_call.get("reader")
            published = copy.deepcopy(dict(row))
        else:
            reviewer_call = copy.deepcopy(dict(row))
            reader = row.get("reader")
            published = None
        stated = (
            reviewer_call.get("views")
            if reviewer_call.get("call") == "reject"
            else reviewer_call.get("negative_views")
        )
        derived = reviewer_call.get("call") == "reject" and stated is None
        id_parts = case_id.split(":")
        corrections.append(
            {
                "case_id": case_id,
                "call_kind": kind,
                "proposed_identity": (
                    record.get("subject")
                    if record is not None
                    else (id_parts[2] if len(id_parts) >= 3 else None)
                ),
                "study_uid": (
                    record.get("study_uid")
                    if record is not None
                    else (id_parts[1] if len(id_parts) >= 3 else None)
                ),
                "origin": proposal_origin(case_id, record),
                "reviewer_call": reviewer_call,
                "published_call_row": published,
                "reader": reader,
                "negative_views": copy.deepcopy(effective.get(case_id)),
                "negative_views_source": SCOPE_DERIVED if derived else SCOPE_STATED,
                "positive_views_after": []
                if kind == CALL_REJECT
                else copy.deepcopy(row.get("views") or []),
                "negative_entry_written": case_id in written,
                "record_present": record is not None,
                "identity_growth": copy.deepcopy((record or {}).get("identity_growth")),
                "admission_correction": copy.deepcopy(correction_block),
                "growth_round": _growth_round(case_id, growth),
                "round": _round_of(correction_block, teaching),
            }
        )
    return {"corrections": corrections, "not_corrections": not_corrections}


# ----------------------------------------------------------------------------- the expectation


def _unavailable(code: str, **facts: Any) -> dict[str, Any]:
    return {
        "status": EXPECTATION_UNAVAILABLE,
        "reason": code,
        "explanation": REASONS[code],
        **facts,
    }


def located_name(case_id: str, identity_growth: Mapping[str, Any] | None) -> str | None:
    """The name the inference record gives the located object: its context subject, else the id's."""
    context = (identity_growth or {}).get("identity_context")
    if isinstance(context, Mapping) and isinstance(context.get("subject"), str):
        return context["subject"]
    parts = case_id.split(":")
    if len(parts) >= 3 and parts[0] == "located":
        return parts[2]
    return None


def _recall_entry(
    record: Mapping[str, Any], located: str | None, scale: object
) -> Mapping[str, Any] | None:
    recall = record.get("identity_recall")
    if not isinstance(recall, Mapping) or located is None:
        return None
    if scale == "10mm":
        objects = recall.get("objects")
    else:
        resolved = recall.get("resolved_scale")
        objects = resolved.get("objects") if isinstance(resolved, Mapping) else None
    entry = objects.get(located) if isinstance(objects, Mapping) else None
    return entry if isinstance(entry, Mapping) else None


def _terms(row: Mapping[str, Any]) -> dict[str, Any]:
    """The recorded cosine terms of one compared case, as the inference record states them."""
    return {
        "squared_cosine": copy.deepcopy(row.get("squared_cosine")),
        "dot": row.get("dot"),
        "left_norm_sq": row.get("left_norm_sq"),
        "right_norm_sq": row.get("right_norm_sq"),
        "envelope": copy.deepcopy(row.get("envelope")),
        "envelope_status": row.get("envelope_status"),
        "speaks": row.get("speaks"),
        "common_speaking_bank_count": len(row.get("common_speaking_banks") or ()),
    }


def speaking_voices(entry: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """The cases that actually spoke in one recall entry: positives for the identity, negatives against."""
    identity = entry.get("identity")
    positives = [
        {
            "case_id": row.get("case_id"),
            "identity": row.get("identity"),
            "sign": 1,
            "study_uid": row.get("study_uid"),
            **_terms(row),
            "common_speaking_banks": list(row.get("common_speaking_banks") or ()),
        }
        for row in entry.get("cases") or ()
        if isinstance(row, Mapping)
        and row.get("speaks") is True
        and row.get("identity") == identity
    ]
    negatives = []
    for row in entry.get("negative_cases") or ():
        if not isinstance(row, Mapping) or row.get("applies") is not True:
            continue
        region = row.get("over_the_asserted_region") or {}
        surroundings = row.get("with_the_surroundings") or {}
        negatives.append(
            {
                "case_id": row.get("case_id"),
                "identity": row.get("identity"),
                "sign": row.get("digit"),
                "study_uid": row.get("study_uid"),
                "views": copy.deepcopy(row.get("views")),
                "reason": row.get("reason"),
                "call_notes": row.get("call_notes"),
                "over_the_asserted_region": _terms(region),
                "with_the_surroundings": _terms(surroundings),
            }
        )
    return {"positive": positives, "negative": negatives}


def join_expectation(
    *,
    origin: str,
    proposed_identity: str | None,
    study_uid: str | None,
    case_id: str,
    identity_growth: Mapping[str, Any] | None,
    find_record: Callable[[str], tuple[str, Mapping[str, Any]] | None],
) -> dict[str, Any]:
    """What the memory expected: the precedents that spoke in the inference record that produced it.

    Only a recognition-derived admission names the record that produced it (file-bytes sha256 of
    the inference record, in its ``identity_growth`` lineage).  The record found must be of the same
    study, hold a recall entry for the located object at the admission's scale with the same
    recognized identity, and its speaking cases must be the lineage's ``speaking_case_ids``.
    Anything else is ``expectation_unavailable`` with its reason; nothing is guessed.
    """
    if origin == ORIGIN_CATALOGUE:
        return _unavailable("structure_catalogue_proposal")
    if origin == ORIGIN_DRAWN:
        return _unavailable("reviewer_drawn_support")
    if origin != ORIGIN_ADMISSION:
        return _unavailable("unclassified_origin")
    growth = identity_growth
    if not isinstance(growth, Mapping):
        return _unavailable("no_identity_growth_lineage")
    source = growth.get("source") if isinstance(growth.get("source"), Mapping) else {}
    sha = source.get("record_sha256")
    if not isinstance(sha, str) or source.get("record_sha256_scope") != "file_bytes":
        return _unavailable("inference_record_not_named")
    found = find_record(sha)
    if found is None:
        return _unavailable("inference_record_not_found", record_sha256=sha)
    path, record = found
    if record.get("study_uid") != study_uid:
        return _unavailable(
            "inference_record_study_mismatch", record_sha256=sha, path=path
        )
    decision = (
        growth.get("decision") if isinstance(growth.get("decision"), Mapping) else {}
    )
    scale = decision.get("identity_scale")
    located = located_name(case_id, growth)
    entry = _recall_entry(record, located, scale)
    if entry is None:
        return _unavailable(
            "no_recall_entry_for_object",
            record_sha256=sha,
            path=path,
            located_object=located,
            scale=scale,
        )
    recognized = decision.get("recognized_identity")
    if entry.get("identity") != recognized or (
        proposed_identity is not None and recognized != proposed_identity
    ):
        return _unavailable(
            "recorded_identity_differs",
            record_sha256=sha,
            path=path,
            recorded_identity=entry.get("identity"),
            admitted_identity=recognized,
        )
    voices = speaking_voices(entry)
    recorded = {voice["case_id"] for voice in voices["positive"]}
    lineage = set(growth.get("speaking_case_ids") or ())
    if recorded != lineage:
        return _unavailable(
            "speaking_set_differs_from_growth_lineage",
            record_sha256=sha,
            path=path,
            recorded_speaking=len(recorded),
            lineage_speaking=len(lineage),
        )
    return {
        "status": EXPECTATION_TRACED,
        "inference_record": {
            "path": path,
            "sha256": sha,
            "sha256_scope": "file_bytes",
            "study_uid": record.get("study_uid"),
            "memory_revision": record.get("memory_revision"),
            "located_object": located,
        },
        "scale": scale,
        "recalled_identity": entry.get("identity"),
        "recall_outcome": entry.get("outcome"),
        "identity_state": entry.get("identity_state"),
        "cases_compared": len(entry.get("cases") or ()),
        "speaking_positive": voices["positive"],
        "speaking_negative": voices["negative"],
    }


# ----------------------------------------------------------------------------- the record


def assemble_record(
    correction: Mapping[str, Any],
    expectation: Mapping[str, Any],
    comparisons: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """One near-miss record: the correction, its recorded expectation and its comparisons.

    ``status`` says only how much could be recorded; it never says the correction is a near miss in
    Winston's sense, which needs one significant difference that this record does not choose.
    """
    if expectation.get("status") != EXPECTATION_TRACED:
        status = STATUS_UNAVAILABLE
        comparisons = ()
    elif expectation.get("speaking_positive"):
        status = STATUS_RECORDED
    else:
        status = STATUS_NO_POSITIVE_SPOKE
    return {
        "schema": SCHEMA,
        "status": status,
        "correction": copy.deepcopy(dict(correction)),
        "expectation": copy.deepcopy(dict(expectation)),
        "comparisons": copy.deepcopy(list(comparisons)),
    }


def summarize(
    records: Sequence[Mapping[str, Any]], not_corrections: Sequence[Mapping[str, str]]
) -> dict[str, Any]:
    """Counts of the records by status, origin, call kind, reader, and of what was not a correction."""
    return {
        "corrections": len(records),
        "by_status": dict(Counter(record["status"] for record in records)),
        "by_origin": dict(
            Counter(record["correction"]["origin"] for record in records)
        ),
        "by_call_kind": dict(
            Counter(record["correction"]["call_kind"] for record in records)
        ),
        "by_proposed_identity": dict(
            sorted(
                Counter(
                    str(record["correction"]["proposed_identity"]) for record in records
                ).items()
            )
        ),
        "by_reader": dict(
            Counter(str(record["correction"]["reader"]) for record in records)
        ),
        "unavailable_reasons": dict(
            Counter(
                record["expectation"].get("reason")
                for record in records
                if record["status"] == STATUS_UNAVAILABLE
            )
        ),
        "not_corrections": dict(Counter(item["reason"] for item in not_corrections)),
        "not_corrections_by_kind_of_id": dict(
            sorted(
                Counter(
                    f"{item['reason']} / {item['case_id'].split(':')[0]}"
                    for item in not_corrections
                ).items()
            )
        ),
    }
