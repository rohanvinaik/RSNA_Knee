"""Two-sign intent tests for the near-miss records (Lane A), on small hand-built profiles.

Each intent is pinned with the case that must happen and the opposite case that must not.
Banks are written with the real territory-v2 names so their meaning parses.
"""

from __future__ import annotations

import copy
import json
from fractions import Fraction

from knee.diagnosis import squint_near_miss as nm

PROCEDURE = "knee.squint-profile/leg-tercile-territory-v2"
FORBIDDEN_WORDS = (
    "censor",
    "split",
    "verdict",
    "threshold",
    "alpha",
    "p_value",
    "significant_difference",
    "the_difference",
    "promoted",
    "largest_difference",
)


def bank(
    view=("Coronal", "0", "0"),
    role="context",
    metric="gradient_column",
    direction="column",
    scale="10mm",
):
    shown = json.dumps(list(view), separators=(",", ":"))
    return f"squint/v2/view={shown}/role={role}/metric={metric}/direction={direction}/scale={scale}"


SHARED = bank(direction="aaa")
QUERY_BANKS = {
    SHARED: (3, 1, 0)
}  # the admitted case's own profile, and the failure's bundle in the stub world
# What an inference record states for two precedents against QUERY_BANKS over [SHARED]:
# P1 = (1, 3, 0): dot 3*1 + 1*3 = 6, left 9 + 1 = 10, right 1 + 9 = 10; P2 = (0, 4, 0): dot 4, left 10, right 16.
CONSISTENT_TERMS = {
    "squint-case:P1:femur": {
        "dot": 6,
        "left_norm_sq": 10,
        "right_norm_sq": 10,
        "common_speaking_banks": [SHARED],
    },
    "squint-case:P2:femur": {
        "dot": 4,
        "left_norm_sq": 10,
        "right_norm_sq": 16,
        "common_speaking_banks": [SHARED],
    },
}


def entry(case_id, subject, study, banks, procedure=PROCEDURE, **extra):
    return {
        "case_id": case_id,
        "subject": subject,
        "study_uid": study,
        "procedure": procedure,
        "banks": banks,
        **extra,
    }


def keys_below(value):
    """Every dictionary key anywhere in a JSON-like value."""
    found = set()
    if isinstance(value, dict):
        for key, item in value.items():
            found.add(str(key))
            found |= keys_below(item)
    elif isinstance(value, list):
        for item in value:
            found |= keys_below(item)
    return found


# ------------------------------------------------------------------ identical profiles, named non-difference


def test_identical_profiles_give_a_named_non_difference():
    banks = {bank(direction="all"): (2, 2, 0), bank(direction="column"): (0, 3, 1)}
    result = nm.decoded_differences(banks, copy.deepcopy(banks))
    assert result["state"] == nm.STATE_AGREE
    assert result["statement"] == nm.STATEMENTS[nm.STATE_AGREE]
    assert result["compared_cell_count"] == 6
    assert result["differing_cell_count"] == 0
    assert all(
        item["difference"]["exact"] == "0"
        for item in result["differences_sorted_for_display"]
    )


def test_profiles_that_differ_are_not_a_non_difference():
    left = {bank(direction="all"): (2, 2, 0)}
    right = {bank(direction="all"): (0, 2, 2)}
    result = nm.decoded_differences(left, right)
    assert result["state"] == nm.STATE_DIFFERENCES
    assert result["differing_cell_count"] == 2
    assert result["statement"] == nm.STATEMENTS[nm.STATE_DIFFERENCES]


def test_shares_are_exact_fractions_not_floats():
    # 1/3 of 3 and 2/6 of 6 are the same share exactly; 1/3 against 333/1000 is not.
    same = nm.decoded_differences({bank(): (1, 1, 1)}, {bank(): (2, 2, 2)})
    assert same["state"] == nm.STATE_AGREE
    near = nm.decoded_differences({bank(): (1, 1, 1)}, {bank(): (333, 334, 333)})
    assert near["state"] == nm.STATE_DIFFERENCES
    by_row = {
        item["row"]: Fraction(item["difference"]["exact"])
        for item in near["differences_sorted_for_display"]
    }
    assert by_row == {0: Fraction(1, 3000), 1: Fraction(-1, 1500), 2: Fraction(1, 3000)}
    # Sorted for display by size: the middle row (1/1500) first, then the two tied rows in row order.
    assert [item["row"] for item in near["differences_sorted_for_display"]] == [1, 0, 2]


# ------------------------------------------------------------------ silent and one-sided banks


def test_a_bank_silent_on_one_side_is_excluded_and_listed():
    silent = bank(direction="aaa")
    read_on_both = bank(direction="bbb")
    only_failure = bank(direction="ccc")
    only_precedent = bank(direction="ddd")
    quiet_both = bank(direction="eee")
    failure = {
        silent: (3, 0, 0),
        read_on_both: (1, 1, 1),
        only_failure: (0, 2, 0),
        quiet_both: (0, 0, 0),
    }
    precedent = {
        silent: (0, 0, 0),
        read_on_both: (1, 1, 1),
        only_precedent: (1, 0, 0),
        quiet_both: (0, 0, 0),
    }
    result = nm.decoded_differences(failure, precedent)
    assert result["shared_banks"] == [read_on_both]
    assert result["failure_only_banks"] == [silent, only_failure]
    assert result["precedent_only_banks"] == [only_precedent]
    assert result["silent_banks"] == [quiet_both]
    compared = {item["bank"] for item in result["differences_sorted_for_display"]}
    assert compared == {read_on_both}


def test_a_bank_read_on_both_sides_is_compared():
    name = bank(direction="aaa")
    result = nm.decoded_differences({name: (3, 0, 0)}, {name: (1, 1, 1)})
    assert result["shared_banks"] == [name]
    assert result["failure_only_banks"] == []
    assert {item["bank"] for item in result["differences_sorted_for_display"]} == {name}


def test_no_shared_bank_is_named_and_compares_nothing():
    result = nm.decoded_differences(
        {bank(direction="aaa"): (1, 0, 0)}, {bank(direction="bbb"): (1, 0, 0)}
    )
    assert result["state"] == nm.STATE_NO_SHARED_BANK
    assert result["compared_cell_count"] == 0
    assert result["differences_sorted_for_display"] == []
    assert result["failure_only_banks"] != [] and result["precedent_only_banks"] != []


def test_malformed_banks_are_listed_not_compared():
    name = bank(direction="aaa")
    result = nm.decoded_differences(
        {name: (1, 0)}, {name: (1, 0, 0)}
    )  # different row layouts
    assert result["malformed_banks"] == [name]
    assert result["shared_banks"] == []
    result = nm.decoded_differences({name: (-1, 0, 0)}, {name: (1, 0, 0)})
    assert result["malformed_banks"] == [name]


# ------------------------------------------------------------------ a single shared bank, never promoted


def test_a_single_shared_bank_difference_is_reported_never_promoted():
    a, b, c = bank(direction="aaa"), bank(direction="bbb"), bank(direction="ccc")
    failure = {a: (2, 2, 0), b: (4, 0, 0), c: (1, 1, 2)}
    precedent = {a: (2, 2, 0), b: (0, 4, 0), c: (1, 1, 2)}
    result = nm.decoded_differences(failure, precedent)
    differing = [
        item
        for item in result["differences_sorted_for_display"]
        if item["difference"]["exact"] != "0"
    ]
    assert {item["bank"] for item in differing} == {b}
    assert len(differing) == 2
    # Both banks that agree stay in the list, unchanged and unlabelled.
    agreeing = [
        item
        for item in result["differences_sorted_for_display"]
        if item["difference"]["exact"] == "0"
    ]
    assert {item["bank"] for item in agreeing} >= {a, c}
    assert not (
        set(FORBIDDEN_WORDS)
        & {
            word
            for key in keys_below(result)
            for word in FORBIDDEN_WORDS
            if word in key
        }
    )


def test_when_everything_agrees_nothing_is_reported_as_different():
    banks = {bank(direction="aaa"): (4, 0, 0)}
    result = nm.decoded_differences(banks, copy.deepcopy(banks))
    assert [
        item
        for item in result["differences_sorted_for_display"]
        if item["difference"]["exact"] != "0"
    ] == []


def test_each_decoded_reading_carries_its_bank_meaning():
    name = bank(
        view=("Sagittal", "1", "1"),
        role="object",
        metric="signal_median",
        direction="patient_lps_anterior",
        scale="10mm",
    )
    result = nm.decoded_differences({name: (1, 0, 0)}, {name: (0, 1, 0)})
    item = result["differences_sorted_for_display"][0]
    assert item["meaning"] == {
        "view": ["Sagittal", "1", "1"],
        "role": "object",
        "metric": "signal_median",
        "direction": "patient_lps_anterior",
        "scale": "10mm",
    }
    assert item["bank"] == name
    assert (
        item["failure"]["fraction"] == "1/1" and item["precedent"]["fraction"] == "0/1"
    )


# ------------------------------------------------------------------ tie order is canonical


def test_tie_order_is_canonical_and_size_comes_first():
    a, b, c = bank(direction="aaa"), bank(direction="bbb"), bank(direction="ccc")
    # Inserted out of name order on purpose.
    failure = {c: (3, 1, 0), b: (4, 0, 0), a: (4, 0, 0)}
    precedent = {c: (0, 1, 3), b: (0, 4, 0), a: (0, 4, 0)}
    result = nm.decoded_differences(failure, precedent)
    order = [
        (item["bank"], item["row"]) for item in result["differences_sorted_for_display"]
    ]
    assert order == [
        (a, 0),
        (a, 1),  # |difference| 1, tied: bank name then row index
        (b, 0),
        (b, 1),
        (c, 0),
        (c, 2),  # |difference| 3/4
        (a, 2),
        (b, 2),
        (c, 1),  # agreeing rows last, still canonical
    ]


def test_display_order_is_not_a_choice_of_the_difference():
    result = nm.decoded_differences({bank(): (4, 0, 0)}, {bank(): (0, 4, 0)})
    assert "no reading here is the significant difference" in result["display_order"]
    assert "differences_sorted_for_display" in result


# ------------------------------------------------------------------ where the other successes sit


def test_sides_are_taken_against_the_failure_value():
    name = bank(direction="aaa")
    members = [
        {"banks": {name: (2, 2, 0)}},  # 1/2: between failure 1/4 and precedent 3/4
        {"banks": {name: (4, 0, 0)}},  # 1: beyond the precedent, still its side
        {"banks": {name: (0, 4, 0)}},  # 0: beyond the failure, away from the precedent
        {"banks": {name: (1, 3, 0)}},  # 1/4: equal to the failure
        {"banks": {}},  # bank absent
        {"banks": {name: (0, 0, 0)}},  # bank silent
    ]
    sides = nm.reading_sides(name, 0, Fraction(1, 4), Fraction(3, 4), members)
    assert sides["members"] == {
        "precedent_side": [0, 1],
        "beyond_failure": [2],
        "equal_to_failure": [3],
        "bank_not_read": [4, 5],
    }
    assert sides["counts"] == {
        "precedent_side": 2,
        "beyond_failure": 1,
        "equal_to_failure": 1,
        "bank_not_read": 2,
    }
    assert sides["population_size"] == 6


def test_sides_flip_with_the_direction_of_the_precedent():
    name = bank(direction="aaa")
    members = [
        {"banks": {name: (2, 2, 0)}},  # 1/2: between failure 3/4 and precedent 1/4
        {"banks": {name: (4, 0, 0)}},  # 1: beyond the failure, away from the precedent
        {"banks": {name: (0, 4, 0)}},  # 0: beyond the precedent, still its side
    ]
    sides = nm.reading_sides(name, 0, Fraction(3, 4), Fraction(1, 4), members)
    assert sides["members"]["precedent_side"] == [0, 2]
    assert sides["members"]["beyond_failure"] == [1]


def test_no_sides_are_taken_when_the_precedent_equals_the_failure():
    name = bank(direction="aaa")
    sides = nm.reading_sides(
        name, 0, Fraction(1, 2), Fraction(1, 2), [{"banks": {name: (1, 1, 0)}}]
    )
    assert sides == {"skipped": "precedent_equals_failure_on_this_row"}


# ------------------------------------------------------------------ the comparison population


def test_population_lists_who_was_counted_and_who_was_left_out_and_why():
    name = bank()
    successes = [
        entry("S:precedent", "femur", "P", {name: (1, 0, 0)}),
        entry("S:failure-case", "femur", "F", {name: (1, 0, 0)}),
        entry("S:failure-study-other", "femur", "F", {name: (1, 0, 0)}),
        entry(
            "S:other-procedure",
            "femur",
            "O",
            {name: (1, 0, 0)},
            procedure="knee.squint-profile/other",
        ),
        entry("S:counted", "femur", "C", {name: (1, 0, 0)}),
        entry("S:tibia", "tibia", "T", {name: (1, 0, 0)}),
    ]
    population = nm.success_population(
        successes,
        subject="femur",
        failure_case_id="S:failure-case",
        failure_study_uid="F",
        failure_procedure=PROCEDURE,
        precedent_case_id="S:precedent",
    )
    assert [member["case_id"] for member in population["members"]] == ["S:counted"]
    assert population["excluded"] == [
        {"case_id": "S:failure-case", "reason": "is_the_failure_case"},
        {"case_id": "S:failure-study-other", "reason": "failure_study"},
        {"case_id": "S:other-procedure", "reason": "procedure_differs"},
        {"case_id": "S:precedent", "reason": "is_the_compared_precedent"},
    ]
    assert population["other_questions_not_considered"] == 1


def test_a_success_with_the_same_procedure_is_counted():
    name = bank()
    population = nm.success_population(
        [entry("S:one", "femur", "C", {name: (1, 0, 0)})],
        subject="femur",
        failure_case_id="x",
        failure_study_uid="F",
        failure_procedure=PROCEDURE,
        precedent_case_id="y",
    )
    assert len(population["members"]) == 1 and population["excluded"] == []


def test_lineage_kind_tells_how_each_success_was_taught():
    assert (
        nm.lineage_kind(
            {"case_id": "squint-case:S:femur", "lineage": {"call": {"call": "confirm"}}}
        )
        == nm.LINEAGE_CATALOGUE_VISUAL
    )
    assert (
        nm.lineage_kind({"case_id": "direct-visual:S:femur:x"})
        == nm.LINEAGE_DIRECT_VISUAL
    )
    assert (
        nm.lineage_kind(
            {
                "case_id": "located:S:femur:r",
                "lineage": {"call": {"identity_growth": {"kind": "k"}}},
            }
        )
        == nm.LINEAGE_ADMISSION
    )
    assert (
        nm.lineage_kind(
            {
                "case_id": "squint-case:S:x::also_positive::femur",
                "source_case_id": "squint-case:S:x",
            }
        )
        == nm.LINEAGE_ALTERNATIVE
    )


# ------------------------------------------------------------------ comparison only where compatible


def pair(precedent_procedure=PROCEDURE, precedent_subject="femur"):
    shared = bank(direction="aaa")
    failure = entry("F:case", "femur", "F", {shared: (3, 1, 0)})
    precedent = entry(
        "P:case",
        precedent_subject,
        "P",
        {shared: (1, 3, 0)},
        procedure=precedent_procedure,
    )
    successes = [
        entry("S:1", "femur", "S1", {shared: (2, 2, 0)}),
        entry("S:2", "femur", "S2", {shared: (4, 0, 0)}),
        entry("S:3", "femur", "S3", {}),
    ]
    return failure, precedent, successes


def test_a_precedent_is_compared_where_question_and_procedure_agree():
    failure, precedent, successes = pair()
    block = nm.compare_with_precedent(failure, precedent, successes)
    assert block["compatibility"]["question"] and block["compatibility"]["procedure"]
    assert block["state"] == nm.STATE_DIFFERENCES
    assert block["success_population"]["size"] == 3


def test_a_precedent_of_another_procedure_or_question_is_not_compared():
    failure, precedent, successes = pair(
        precedent_procedure="knee.squint-profile/other"
    )
    block = nm.compare_with_precedent(failure, precedent, successes)
    assert (
        block["state"] == nm.STATE_NOT_COMPARED
        and block["reason"] == "procedure_differs"
    )
    assert "differences_sorted_for_display" not in block
    failure, precedent, successes = pair(precedent_subject="tibia")
    block = nm.compare_with_precedent(failure, precedent, successes)
    assert (
        block["state"] == nm.STATE_NOT_COMPARED
        and block["reason"] == "question_differs"
    )


def test_a_precedent_whose_bundle_is_missing_is_kept_not_replaced():
    block = nm.precedent_unavailable("squint-case:P:femur")
    assert block == {
        "precedent_case_id": "squint-case:P:femur",
        "state": nm.STATE_NOT_COMPARED,
        "reason": "precedent_bundle_unavailable",
    }


def test_every_count_carries_the_case_ids_of_its_population():
    failure, precedent, successes = pair()
    block = nm.compare_with_precedent(failure, precedent, successes)
    members = block["success_population"]["members"]
    assert [member["case_id"] for member in members] == ["S:1", "S:2", "S:3"]
    assert all("lineage_kind" in member for member in members)
    for item in block["differences_sorted_for_display"]:
        side = item["success_side"]
        if "skipped" in side:
            continue
        everyone = sorted(
            index for group in side["members"].values() for index in group
        )
        assert everyone == [member["index"] for member in members]
        assert sum(side["counts"].values()) == side["population_size"] == len(members)
    row0 = next(i for i in block["differences_sorted_for_display"] if i["row"] == 0)
    # failure 3/4, precedent 1/4 on row 0: S:1 (1/2) on the precedent's side, S:2 (1) beyond the failure.
    assert row0["success_side"]["members"]["precedent_side"] == [0]
    assert row0["success_side"]["members"]["beyond_failure"] == [1]
    assert row0["success_side"]["members"]["bank_not_read"] == [2]


def test_the_row_on_which_the_precedent_equals_the_failure_takes_no_side():
    failure, precedent, successes = pair()
    block = nm.compare_with_precedent(failure, precedent, successes)
    row2 = next(i for i in block["differences_sorted_for_display"] if i["row"] == 2)
    assert row2["difference"]["exact"] == "0"
    assert row2["success_side"] == {"skipped": "precedent_equals_failure_on_this_row"}


# ------------------------------------------------------------------ the corrections


def teaching_table():
    reject_with_views = {
        "call": "reject",
        "candidate_id": "squint-case:S1:femur",
        "notes": "n1",
        "reader": "R",
        "views": [["Sagittal", "0", "0"]],
    }
    reject_without_views = {
        "call": "reject",
        "candidate_id": "squint-case:S2:tibia",
        "notes": "n2",
        "reader": "R",
    }
    confirm_negative = {
        "call": "confirm",
        "candidate_id": "squint-case:S3:patella",
        "notes": "n3",
        "reader": "R",
        "views": [["Coronal", "0", "0"]],
        "negative_views": [["Axial", "0", "0"]],
    }
    confirm_plain = {
        "call": "confirm",
        "candidate_id": "squint-case:S4:femur",
        "notes": "n4",
        "reader": "R",
        "views": [["Coronal", "0", "0"]],
    }
    confirm_alternative_only = {
        "call": "confirm",
        "candidate_id": "squint-case:S5:femur",
        "notes": "n5",
        "reader": "R",
        "views": [["Coronal", "0", "0"]],
        "also_positive": [{"identity": "tibia", "views": [["Sagittal", "0", "0"]]}],
    }
    unsure = {
        "call": "unsure",
        "candidate_id": "squint-case:S6:joint",
        "notes": "n6",
        "reader": "R",
    }
    return {
        "calls": [
            reject_with_views,
            reject_without_views,
            confirm_negative,
            confirm_plain,
            confirm_alternative_only,
            unsure,
        ],
        "negative_case_ids": [
            "squint-case:S1:femur",
            "squint-case:S2:tibia",
            "squint-case:S3:patella",
        ],
        "negative_views": {
            "squint-case:S1:femur": [["Sagittal", "0", "0"]],
            "squint-case:S2:tibia": [["Coronal", "0", "0"], ["Sagittal", "0", "0"]],
            "squint-case:S3:patella": [["Axial", "0", "0"]],
        },
    }


def identity_table():
    return {
        "cases": [
            {"case_id": "squint-case:S1:femur", "subject": "femur", "study_uid": "S1"},
            {"case_id": "squint-case:S2:tibia", "subject": "tibia", "study_uid": "S2"},
            {
                "case_id": "squint-case:S3:patella",
                "subject": "patella",
                "study_uid": "S3",
            },
        ]
    }


def test_reject_and_confirm_with_negative_views_are_corrections():
    teaching = teaching_table()
    found = nm.enumerate_corrections(teaching, identity_table())
    ids = [item["case_id"] for item in found["corrections"]]
    assert ids == [
        "squint-case:S1:femur",
        "squint-case:S2:tibia",
        "squint-case:S3:patella",
    ]
    kinds = [item["call_kind"] for item in found["corrections"]]
    assert kinds == [nm.CALL_REJECT, nm.CALL_REJECT, nm.CALL_CONFIRM_NEGATIVE_VIEWS]
    # The reviewer's own row is carried verbatim, and is a copy.
    assert found["corrections"][0]["reviewer_call"] == teaching["calls"][0]
    found["corrections"][0]["reviewer_call"]["notes"] = "changed"
    assert teaching["calls"][0]["notes"] == "n1"


def test_refusal_unsure_and_plain_confirmation_are_not_corrections():
    found = nm.enumerate_corrections(teaching_table(), identity_table())
    reasons = {item["case_id"]: item["reason"] for item in found["not_corrections"]}
    assert reasons == {
        "squint-case:S4:femur": "confirmed_without_negative_views",
        "squint-case:S5:femur": "confirmed_without_negative_views",
        "squint-case:S6:joint": "unsure_call_is_never_a_correction",
    }


def test_nothing_but_unsure_and_plain_confirmations_yields_no_record():
    teaching = teaching_table()
    teaching["calls"] = [
        row
        for row in teaching["calls"]
        if row["call"] != "reject" and "negative_views" not in row
    ]
    teaching["negative_case_ids"] = []
    teaching["negative_views"] = {}
    found = nm.enumerate_corrections(teaching, identity_table())
    assert found["corrections"] == []
    assert len(found["not_corrections"]) == 3


def test_a_scope_the_reviewer_did_not_state_is_marked_as_derived():
    found = nm.enumerate_corrections(teaching_table(), identity_table())
    by_id = {item["case_id"]: item for item in found["corrections"]}
    assert by_id["squint-case:S1:femur"]["negative_views_source"] == nm.SCOPE_STATED
    assert by_id["squint-case:S3:patella"]["negative_views_source"] == nm.SCOPE_STATED
    derived = by_id["squint-case:S2:tibia"]
    assert derived["negative_views_source"] == nm.SCOPE_DERIVED
    assert "views" not in derived["reviewer_call"]
    assert derived["negative_views"] == [["Coronal", "0", "0"], ["Sagittal", "0", "0"]]


def test_the_origin_of_a_proposal_comes_from_its_lineage():
    assert nm.proposal_origin("squint-case:S:femur", {}) == nm.ORIGIN_CATALOGUE
    assert nm.proposal_origin("direct-visual:S:femur:x", {}) == nm.ORIGIN_DRAWN
    assert (
        nm.proposal_origin("located:S:femur:r", {"identity_growth": {"kind": "k"}})
        == nm.ORIGIN_ADMISSION
    )
    assert nm.proposal_origin("something:else", {}) == nm.ORIGIN_UNCLASSIFIED


# ------------------------------------------------------------------ the expectation


SHA = "a" * 64
STUDY = "1.2.3"
ADMISSION_ID = f"located:{STUDY}:femur:rev"


def recall_row(case_id, speaks, identity="femur"):
    terms = CONSISTENT_TERMS.get(
        case_id,
        {
            "dot": 10,
            "left_norm_sq": 20,
            "right_norm_sq": 30,
            "common_speaking_banks": ["b1", "b2"],
        },
    )
    return {
        "case_id": case_id,
        "identity": identity,
        "study_uid": case_id.split(":")[1],
        "lineage": {},
        **terms,
        "squared_cosine": {"numerator": 100, "denominator": 600},
        "envelope": {
            "numerator": 1,
            "denominator": 3,
            "comparison_count": 4,
            "opponent_case_ids": ["o"],
        },
        "envelope_status": "above_envelope" if speaks else "not_above_envelope",
        "speaks": speaks,
    }


def negative_row(case_id, applies):
    term = {
        "dot": 1,
        "left_norm_sq": 2,
        "right_norm_sq": 3,
        "squared_cosine": {"numerator": 1, "denominator": 6},
        "envelope": None,
        "envelope_status": "above_envelope",
        "speaks": applies,
        "common_speaking_banks": ["b1"],
    }
    return {
        "case_id": case_id,
        "identity": "femur",
        "digit": -1,
        "study_uid": case_id.split(":")[1],
        "views": [["Sagittal", "0", "0"]],
        "applies": applies,
        "reason": "applies" if applies else "concerns_another_identity",
        "call_notes": "posterior thigh",
        "over_the_asserted_region": term,
        "with_the_surroundings": term,
    }


def inference_record(
    scale="10mm",
    study=STUDY,
    speaking=("squint-case:P1:femur", "squint-case:P2:femur"),
    identity="femur",
):
    cases = [recall_row(case_id, True) for case_id in speaking] + [
        recall_row("squint-case:P9:femur", False)
    ]
    entry_ = {
        "identity": identity,
        "outcome": "appearance_supports",
        "identity_state": "placed",
        "cases": cases,
        "speaking_case_ids": sorted(speaking),
        "negative_cases": [
            negative_row("squint-case:N1:femur", True),
            negative_row("squint-case:N2:femur", False),
        ],
    }
    if scale == "10mm":
        recall = {"objects": {"femur": entry_}}
    else:
        recall = {"objects": {}, "resolved_scale": {"objects": {"femur": entry_}}}
    return {
        "schema": "knee.squint-study/v1",
        "study_uid": study,
        "memory_revision": "rev",
        "identity_recall": recall,
    }


def growth(
    scale="10mm",
    speaking=("squint-case:P1:femur", "squint-case:P2:femur"),
    sha=SHA,
    recognized="femur",
):
    return {
        "kind": "recognition_derived_identity",
        "source": {
            "kind": "squint-inference",
            "memory_revision": "rev",
            "record_sha256": sha,
            "record_sha256_scope": "file_bytes",
        },
        "decision": {
            "identity_scale": scale,
            "recognized_identity": recognized,
            "state": "admitted",
        },
        "identity_context": {"subject": "femur"},
        "speaking_case_ids": list(speaking),
    }


def joiner(record):
    def find(sha):
        return (
            ("memory://record", record) if sha == SHA and record is not None else None
        )

    return find


def join(identity_growth, record, origin=nm.ORIGIN_ADMISSION, study=STUDY):
    return nm.join_expectation(
        origin=origin,
        proposed_identity="femur",
        study_uid=study,
        case_id=ADMISSION_ID,
        identity_growth=identity_growth,
        find_record=joiner(record),
    )


def test_an_admission_traces_to_the_precedents_that_actually_spoke():
    expectation = join(growth(), inference_record())
    assert expectation["status"] == nm.EXPECTATION_TRACED
    spoke = expectation["speaking_positive"]
    assert [voice["case_id"] for voice in spoke] == [
        "squint-case:P1:femur",
        "squint-case:P2:femur",
    ]
    assert all(voice["sign"] == 1 and voice["identity"] == "femur" for voice in spoke)
    assert spoke[0]["squared_cosine"] == {"numerator": 100, "denominator": 600}
    assert spoke[0]["dot"] == 6 and spoke[0]["common_speaking_bank_count"] == 1
    assert spoke[0]["common_speaking_banks"] == [SHARED]
    # A case that was compared and did not speak is not an expectation.
    assert "squint-case:P9:femur" not in {voice["case_id"] for voice in spoke}
    assert expectation["cases_compared"] == 3
    # Only a negative that applied is a voice against, signed -1.
    assert [(v["case_id"], v["sign"]) for v in expectation["speaking_negative"]] == [
        ("squint-case:N1:femur", -1)
    ]
    assert expectation["inference_record"]["sha256"] == SHA


def test_the_joint_scale_reads_the_resolved_scale_entry():
    expectation = join(growth(scale="10mm+2mm"), inference_record(scale="10mm+2mm"))
    assert (
        expectation["status"] == nm.EXPECTATION_TRACED
        and expectation["scale"] == "10mm+2mm"
    )
    unresolved = join(growth(scale="10mm+2mm"), inference_record(scale="10mm"))
    assert unresolved["reason"] == "no_recall_entry_for_object"


def test_a_missing_inference_record_is_expectation_unavailable_with_its_reason():
    expectation = join(growth(), None)
    assert expectation["status"] == nm.EXPECTATION_UNAVAILABLE
    assert expectation["reason"] == "inference_record_not_found"
    assert expectation["record_sha256"] == SHA
    assert expectation["explanation"] == nm.REASONS["inference_record_not_found"]


def test_a_catalogue_proposal_has_no_expectation_because_no_recall_produced_it():
    expectation = nm.join_expectation(
        origin=nm.ORIGIN_CATALOGUE,
        proposed_identity="femur",
        study_uid=STUDY,
        case_id="squint-case:S:femur",
        identity_growth=None,
        find_record=joiner(
            inference_record()
        ),  # a record exists; it is not this proposal's
    )
    assert expectation["status"] == nm.EXPECTATION_UNAVAILABLE
    assert expectation["reason"] == "structure_catalogue_proposal"
    assert "No identity recall produced it" in expectation["explanation"]


def test_a_record_that_is_not_shown_to_have_produced_the_admission_is_not_joined():
    other_study = join(growth(), inference_record(study="9.9.9"))
    assert other_study["reason"] == "inference_record_study_mismatch"
    fewer = join(growth(), inference_record(speaking=("squint-case:P1:femur",)))
    assert fewer["reason"] == "speaking_set_differs_from_growth_lineage"
    other_identity = join(growth(), inference_record(identity="tibia"))
    assert other_identity["reason"] == "recorded_identity_differs"
    unnamed = join(
        {**growth(), "source": {"kind": "squint-inference"}}, inference_record()
    )
    assert unnamed["reason"] == "inference_record_not_named"
    nothing = join(None, inference_record())
    assert nothing["reason"] == "no_identity_growth_lineage"


def test_an_unclassified_origin_has_no_expectation():
    expectation = join(growth(), inference_record(), origin=nm.ORIGIN_UNCLASSIFIED)
    assert (
        expectation["status"] == nm.EXPECTATION_UNAVAILABLE
        and expectation["reason"] == "unclassified_origin"
    )


# ------------------------------------------------------------------ the record


def a_correction(origin=nm.ORIGIN_ADMISSION):
    return {
        "case_id": ADMISSION_ID,
        "call_kind": nm.CALL_CONFIRM_NEGATIVE_VIEWS,
        "proposed_identity": "femur",
        "study_uid": STUDY,
        "origin": origin,
        "reviewer_call": {
            "call": "confirm",
            "candidate_id": ADMISSION_ID,
            "negative_views": [["Sagittal", "0", "0"]],
            "notes": "posterior thigh",
            "reader": "R",
        },
        "reader": "R",
        "negative_views": [["Sagittal", "0", "0"]],
        "negative_views_source": nm.SCOPE_STATED,
        "positive_views_after": [["Coronal", "0", "0"]],
    }


def test_an_unavailable_expectation_keeps_the_correction_and_compares_nothing():
    failure, precedent, successes = pair()
    comparisons = [nm.compare_with_precedent(failure, precedent, successes)]
    record = nm.assemble_record(
        a_correction(nm.ORIGIN_CATALOGUE),
        join(None, None, origin=nm.ORIGIN_CATALOGUE),
        comparisons,
    )
    assert record["status"] == nm.STATUS_UNAVAILABLE
    assert record["comparisons"] == []
    assert record["correction"]["reviewer_call"]["notes"] == "posterior thigh"
    assert record["expectation"]["reason"] == "structure_catalogue_proposal"


def test_a_traced_expectation_records_its_comparisons_and_nothing_more():
    failure, precedent, successes = pair()
    comparisons = [nm.compare_with_precedent(failure, precedent, successes)]
    record = nm.assemble_record(
        a_correction(), join(growth(), inference_record()), comparisons
    )
    assert record["status"] == nm.STATUS_RECORDED
    assert len(record["comparisons"]) == 1
    json.dumps(
        record
    )  # fully serialisable: exact values are strings and ints, never Fractions
    assert not [
        word
        for key in keys_below(record)
        for word in FORBIDDEN_WORDS
        if word in key.lower()
    ]


def test_a_traced_expectation_with_no_speaking_positive_is_not_recorded_as_one():
    speaking_none = inference_record(speaking=())
    expectation = join(growth(speaking=()), speaking_none)
    assert (
        expectation["status"] == nm.EXPECTATION_TRACED
        and expectation["speaking_positive"] == []
    )
    record = nm.assemble_record(a_correction(), expectation, [])
    assert record["status"] == nm.STATUS_NO_POSITIVE_SPOKE


def test_the_summary_counts_by_status_origin_and_reason():
    unavailable = nm.assemble_record(
        a_correction(nm.ORIGIN_CATALOGUE), join(None, None, origin=nm.ORIGIN_CATALOGUE)
    )
    traced = nm.assemble_record(a_correction(), join(growth(), inference_record()), [])
    summary = nm.summarize(
        [unavailable, traced],
        [
            {
                "case_id": "x",
                "call": "unsure",
                "reason": "unsure_call_is_never_a_correction",
            }
        ],
    )
    assert summary["corrections"] == 2
    assert summary["by_status"] == {nm.STATUS_UNAVAILABLE: 1, nm.STATUS_RECORDED: 1}
    assert summary["by_origin"] == {nm.ORIGIN_CATALOGUE: 1, nm.ORIGIN_ADMISSION: 1}
    assert summary["unavailable_reasons"] == {"structure_catalogue_proposal": 1}
    assert summary["not_corrections"] == {"unsure_call_is_never_a_correction": 1}


# ------------------------------------------------------------------ what the real writer writes


def test_the_enumeration_reads_what_the_real_correction_writer_writes():
    from knee.diagnosis import squint_bootstrap as writer

    case_id = ADMISSION_ID
    case = {
        "case_id": case_id,
        "subject": "femur",
        "study_uid": STUDY,
        "profile": {"banks": {}},
        "identity_growth": growth(),
    }
    admitted = {
        "call": "confirm",
        "candidate_id": case_id,
        "views": [["Coronal", "0", "0"], ["Sagittal", "0", "0"]],
        "reader": "growth",
        "notes": "admitted",
        "identity_growth": {"kind": "recognition_derived_identity"},
    }
    call = {
        "call": "confirm",
        "candidate_id": case_id,
        "views": [["Coronal", "0", "0"]],
        "negative_views": [["Sagittal", "0", "0"]],
        "reader": "reviewer",
        "notes": "sagittal is posterior thigh",
    }
    effect = {
        "effect": "facets",
        "call": call,
        "reader": "reviewer",
        "positive_views": [["Coronal", "0", "0"]],
        "negative_views": [["Sagittal", "0", "0"]],
        "alternatives": [],
    }
    provenance = {
        "review_sha256": "r" * 64,
        "reviewed_manifest_sha256": "m" * 64,
        "reviewed_revision": "rev",
    }
    record = writer._corrected_record(case, admitted, effect, provenance)
    row = writer._corrected_row(admitted, effect)
    memory = {
        "object_identity_teaching": {
            "calls": [admitted],
            "confirmed_case_ids": [case_id],
        }
    }
    teaching = writer._corrected_teaching(
        memory, {case_id: effect}, {case_id: row}, {"schema": "review-record"}
    )

    found = nm.enumerate_corrections(teaching, {"cases": [record]})
    assert len(found["corrections"]) == 1
    correction = found["corrections"][0]
    assert correction["origin"] == nm.ORIGIN_ADMISSION
    assert correction["call_kind"] == nm.CALL_CONFIRM_NEGATIVE_VIEWS
    assert correction["negative_views"] == [["Sagittal", "0", "0"]]
    assert correction["positive_views_after"] == [["Coronal", "0", "0"]]
    assert correction["admission_correction"]["effect"] == "facets"
    assert (
        correction["admission_correction"]["superseded_call"]["views"]
        == admitted["views"]
    )
    # The writer keeps the admission's own row (recognition-derived reader) as the published row;
    # the reviewer's call and name are read from the correction block, verbatim.
    assert correction["reviewer_call"] == call
    assert correction["reader"] == "reviewer"
    assert correction["published_call_row"]["reader"] == "growth"
    assert correction["negative_views_source"] == nm.SCOPE_STATED
    # And the lineage the writer copied is what the join needs.
    expectation = nm.join_expectation(
        origin=correction["origin"],
        proposed_identity=correction["proposed_identity"],
        study_uid=correction["study_uid"],
        case_id=correction["case_id"],
        identity_growth=correction["identity_growth"],
        find_record=joiner(inference_record()),
    )
    assert expectation["status"] == nm.EXPECTATION_TRACED

    whole = {
        "effect": "whole_case",
        "call": {
            "call": "reject",
            "candidate_id": case_id,
            "views": [["Coronal", "0", "0"], ["Sagittal", "0", "0"]],
            "notes": "not femur",
            "reader": "reviewer",
        },
        "reader": "reviewer",
        "positive_views": [],
        "negative_views": [["Coronal", "0", "0"], ["Sagittal", "0", "0"]],
        "alternatives": [],
    }
    record = writer._corrected_record(case, admitted, whole, provenance)
    row = writer._corrected_row(admitted, whole)
    teaching = writer._corrected_teaching(
        memory, {case_id: whole}, {case_id: row}, {"schema": "review-record"}
    )
    found = nm.enumerate_corrections(teaching, {"cases": [record]})
    assert [item["call_kind"] for item in found["corrections"]] == [nm.CALL_REJECT]
    whole_case = found["corrections"][0]
    assert whole_case["admission_correction"]["effect"] == "whole_case"
    assert whole_case["origin"] == nm.ORIGIN_ADMISSION
    assert whole_case["reviewer_call"] == whole["call"]
    assert whole_case["negative_views"] == whole["negative_views"]


# ------------------------------------------------------------------ the report's glue, on stubs


class StubView:
    def __init__(self, seeds, negatives, scale="10mm"):
        self.scale = scale
        self.preparation = {"source_pin": "q" * 64}
        self.seeds = seeds
        self.negatives = negatives
        self.seeds_by_id = {item["case_id"]: item for item in seeds}
        self.negatives_by_id = {item["case_id"]: item for item in negatives}


class StubBundles:
    def __init__(self, view):
        self.view = view
        self.scales = []

    def at(self, scale):
        self.scales.append(scale)
        return self.view


def stub_world(with_second_precedent=True, with_failure=True):
    """Two speaking precedents (P1, P2), the failure's own bundle, and three other successes."""
    seeds = [
        entry("squint-case:P1:femur", "femur", "P1", {SHARED: (1, 3, 0)}),
        entry("squint-case:S7:femur", "femur", "S7", {SHARED: (2, 2, 0)}),
        entry("squint-case:S8:femur", "femur", "S8", {SHARED: (4, 0, 0)}),
        entry("squint-case:S9:femur", "femur", "S9", {}),
    ]
    if with_second_precedent:
        seeds.append(entry("squint-case:P2:femur", "femur", "P2", {SHARED: (0, 4, 0)}))
    negatives = (
        [
            entry(
                ADMISSION_ID,
                "femur",
                STUDY,
                dict(QUERY_BANKS),
                views=[["Sagittal", "0", "0"]],
            )
        ]
        if with_failure
        else []
    )
    return StubBundles(StubView(seeds, negatives))


def hand_built_memory():
    writer_record = {
        "case_id": ADMISSION_ID,
        "subject": "femur",
        "study_uid": STUDY,
        "profile": {"banks": QUERY_BANKS},
        "identity_growth": growth(),
        "identity_correction": {
            "kind": "visual_correction_of_recognition_derived_admission",
            "corrected_by": "reviewer",
            "review_sha256": "r" * 64,
            "reviewed_manifest_sha256": "m" * 64,
            "reviewed_revision": "rev",
            "effect": "facets",
            "call": {
                "call": "confirm",
                "candidate_id": ADMISSION_ID,
                "views": [["Coronal", "0", "0"]],
                "negative_views": [["Sagittal", "0", "0"]],
                "reader": "reviewer",
                "notes": "sagittal is posterior thigh",
            },
        },
    }
    teaching = teaching_table()
    teaching["calls"].append(
        {
            "call": "confirm",
            "candidate_id": ADMISSION_ID,
            "views": [["Coronal", "0", "0"]],
            "negative_views": [["Sagittal", "0", "0"]],
            "reader": "growth",
            "notes": "admitted",
        }
    )
    teaching["negative_case_ids"].append(ADMISSION_ID)
    teaching["negative_views"][ADMISSION_ID] = [["Sagittal", "0", "0"]]
    cases = identity_table()["cases"] + [writer_record]
    return {
        "object_identity_teaching": teaching,
        "object_identity_cases": {"cases": cases},
        "object_identity_growth": {
            "rounds": [
                {
                    "admitted_case_ids": [ADMISSION_ID],
                    "parent_manifest_sha256": "p" * 64,
                    "decisions_sha256": "d" * 64,
                    "state_counts": {"admitted": 1},
                }
            ]
        },
    }


def test_each_speaking_precedent_is_compared_and_a_missing_bundle_is_kept_as_missing():
    from scripts import near_miss_report as report

    correction = {"case_id": ADMISSION_ID}
    expectation = join(growth(), inference_record())
    world = stub_world(
        with_second_precedent=False
    )  # P2 spoke in the record, its bundle is not held
    blocks = report.compare_traced(
        correction, expectation, world, QUERY_BANKS, "f" * 64
    )
    assert world.scales == ["10mm"]
    assert [block["precedent_case_id"] for block in blocks] == [
        "squint-case:P1:femur",
        "squint-case:P2:femur",
    ]
    assert blocks[0]["state"] == nm.STATE_DIFFERENCES
    assert blocks[1] == nm.precedent_unavailable("squint-case:P2:femur")
    missing_failure = report.compare_traced(
        correction, expectation, stub_world(with_failure=False), QUERY_BANKS, "f" * 64
    )
    assert {block["reason"] for block in missing_failure} == {
        "failure_bundle_unavailable"
    }


def test_build_records_keeps_every_correction_and_joins_only_where_a_recall_produced_it():
    from scripts import near_miss_report as report

    memory = hand_built_memory()
    records, not_corrections = report.build_records(
        memory, joiner(inference_record()), stub_world(), "f" * 64
    )
    by_id = {record["correction"]["case_id"]: record for record in records}
    assert len(records) == 4 and len(not_corrections) == 3
    for case_id in (
        "squint-case:S1:femur",
        "squint-case:S2:tibia",
        "squint-case:S3:patella",
    ):
        assert by_id[case_id]["status"] == nm.STATUS_UNAVAILABLE
        assert by_id[case_id]["expectation"]["reason"] == "structure_catalogue_proposal"
        assert by_id[case_id]["comparisons"] == []
    traced = by_id[ADMISSION_ID]
    assert traced["status"] == nm.STATUS_RECORDED
    assert traced["correction"]["reader"] == "reviewer"
    assert traced["correction"]["round"]["kind"] == "admission_review"
    assert traced["correction"]["growth_round"]["round_index"] == 0
    assert [block["precedent_case_id"] for block in traced["comparisons"]] == [
        "squint-case:P1:femur",
        "squint-case:P2:femur",
    ]
    assert all(
        block["state"] == nm.STATE_DIFFERENCES for block in traced["comparisons"]
    )
    # The other successes counted for P1 exclude P1 itself and, being another study's, include P2.
    population = traced["comparisons"][0]["success_population"]
    assert [member["case_id"] for member in population["members"]] == [
        "squint-case:P2:femur",
        "squint-case:S7:femur",
        "squint-case:S8:femur",
        "squint-case:S9:femur",
    ]
    assert population["excluded"] == [
        {"case_id": "squint-case:P1:femur", "reason": "is_the_compared_precedent"}
    ]


def test_the_table_shows_the_traced_record_and_the_reasons_for_the_rest():
    from scripts import near_miss_report as report

    memory = hand_built_memory()
    records, not_corrections = report.build_records(
        memory, joiner(inference_record()), stub_world(), "f" * 64
    )
    payload = {
        "memory": {"path": "memory", "manifest_sha256": "f" * 64, "cases": 7},
        "generated": "now",
        "summary": nm.summarize(records, not_corrections),
        "records": records,
        "join_check": [],
    }
    text = report.render_table(payload)
    assert "## Corrections with a recorded expectation" in text
    assert "None. No correction" not in text
    assert (
        "squint:…P1:femur" in text and "squint:…P2:femur" in text
    )  # each speaking precedent is named
    assert "precedent side" in text and "beyond failure" in text
    assert "differences_sorted" not in text  # a display, not a field dump
    assert (
        "structure_catalogue_proposal" in text
        and "confirmed_without_negative_views" in text
    )
    empty = {
        **payload,
        "records": [r for r in records if r["status"] == nm.STATUS_UNAVAILABLE],
    }
    empty["summary"] = nm.summarize(empty["records"], not_corrections)
    assert "None. No correction" in report.render_table(empty)


def test_the_record_finder_resolves_a_sha_to_the_file_it_hashes(tmp_path):
    import hashlib
    import lzma

    from scripts import near_miss_report as report

    folder = tmp_path / "studies"
    folder.mkdir()
    body = json.dumps(inference_record()).encode()
    path = folder / "1.2.3.json.xz"
    path.write_bytes(lzma.compress(body))
    (folder / "notes.json.xz").write_bytes(
        lzma.compress(b"{}")
    )  # not a per-study record: ignored
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    finder = report.RecordFinder([str(tmp_path)])
    found = finder(sha)
    assert (
        found is not None
        and found[0].endswith("1.2.3.json.xz")
        and found[1]["study_uid"] == STUDY
    )
    assert finder("0" * 64) is None
    assert finder.files_hashed == 1


def test_scope_text_and_short_id_read_plainly():
    from scripts import near_miss_report as report

    assert (
        report.scope_text([["Sagittal", "0", "0"], ["Coronal", "1", "1"]])
        == "Sagittal/0/0, Coronal/1/1"
    )
    assert report.scope_text(None) == "-"
    assert (
        report.short_id("squint-case:1.2.826.0.1.3680043.8.498.12345678:femur")
        == "squint:…345678:femur"
    )


# ------------------------------------------------------------------ the bundle that spoke


SOURCE = {
    "memory_manifest_sha256": "m" * 64,
    "scale": "10mm",
    "preparation_source_pin": "p" * 64,
}


def p1_voice():
    return join(growth(), inference_record())["speaking_positive"][0]


def p1_pair(precedent_banks=None, query_banks=None):
    failure = entry(
        ADMISSION_ID, "femur", STUDY, dict(QUERY_BANKS), views=[["Sagittal", "0", "0"]]
    )
    precedent = entry(
        "squint-case:P1:femur",
        "femur",
        "P1",
        precedent_banks if precedent_banks is not None else {SHARED: (1, 3, 0)},
    )
    successes = [entry("S:1", "femur", "S1", {SHARED: (2, 2, 0)})]
    return nm.compare_speaking_precedent(
        p1_voice(),
        QUERY_BANKS if query_banks is None else query_banks,
        failure,
        precedent,
        successes,
        SOURCE,
    )


def test_a_bundle_that_reproduces_the_recorded_terms_is_compared_and_says_where_it_came_from():
    block = p1_pair()
    assert block["bundle_matches_recorded_terms"] is True
    assert (
        block["recorded_terms_check"]["recorded"]
        == block["recorded_terms_check"]["recomputed"]
        == {"dot": 6, "left_norm_sq": 10, "right_norm_sq": 10}
    )
    assert block["state"] == nm.STATE_DIFFERENCES
    assert block["bundles_from"] == SOURCE


def test_a_precedent_bundle_that_changed_since_it_spoke_is_not_compared():
    block = p1_pair(precedent_banks={SHARED: (1, 2, 1)})  # same case id, other counts
    assert (
        block["state"] == nm.STATE_NOT_COMPARED
        and block["reason"] == "bundle_differs_from_the_one_that_spoke"
    )
    assert block["recorded_terms_check"]["matches"] is False
    assert (
        block["recorded_terms_check"]["recomputed"]
        != block["recorded_terms_check"]["recorded"]
    )
    assert (
        "differences_sorted_for_display" not in block
        and block["bundles_from"] == SOURCE
    )


def test_a_query_profile_that_is_not_the_one_that_was_recalled_is_not_compared():
    block = p1_pair(query_banks={SHARED: (2, 2, 0)})
    assert (
        block["state"] == nm.STATE_NOT_COMPARED
        and block["reason"] == "bundle_differs_from_the_one_that_spoke"
    )


def test_a_recorded_bank_that_is_silent_now_is_not_compared():
    block = p1_pair(precedent_banks={})
    assert block["state"] == nm.STATE_NOT_COMPARED
    assert block["recorded_terms_check"]["banks_unreadable_now"] == [SHARED]


def test_terms_that_name_no_banks_cannot_be_checked():
    check = nm.verify_recorded_terms(
        {"dot": 0, "left_norm_sq": 0, "right_norm_sq": 0},
        QUERY_BANKS,
        {SHARED: (1, 3, 0)},
    )
    assert check["matches"] is False and check["bank_count"] == 0


def test_the_report_leaves_a_precedent_whose_bundle_changed_uncompared():
    from scripts import near_miss_report as report

    world = stub_world()
    world.view.seeds_by_id["squint-case:P1:femur"]["banks"][SHARED] = (1, 2, 1)
    records, _ = report.build_records(
        hand_built_memory(), joiner(inference_record()), world, "f" * 64
    )
    traced = next(r for r in records if r["correction"]["case_id"] == ADMISSION_ID)
    states = {
        block["precedent_case_id"]: block["state"] for block in traced["comparisons"]
    }
    assert states == {
        "squint-case:P1:femur": nm.STATE_NOT_COMPARED,
        "squint-case:P2:femur": nm.STATE_DIFFERENCES,
    }
    assert traced["comparisons"][1]["bundles_from"]["scale"] == "10mm"
