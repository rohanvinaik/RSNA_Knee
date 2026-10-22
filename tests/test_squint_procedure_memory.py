"""Two-sign intent tests for the procedure-experience rows (Lane C, retention only).

Each test pins one meaning with a case that must hold and the opposite case that must not.
The records are small hand-built ``knee.squint-study/v1`` records (labelled synthetic); the
real records are read by ``procedure_report.py``.
"""

from __future__ import annotations

import pytest

from knee.diagnosis import squint_procedure_memory as pe

UID = "1.2.826.0.1.3680043.8.498.1000"
OTHER_UID = "1.2.826.0.1.3680043.8.498.2000"
REV = "memory-revision-1"
RECORD_SHA = "a" * 64
SOURCE = {
    "run": "run-a",
    "record_file": "readings/run-a/studies/x.json.xz",
    "record_sha256": RECORD_SHA,
    "memory_sha256": "b" * 64,
    "memory_revision": REV,
}
NO_CALLS = {"reviewer_calls": {}, "recognition_derived_excluded": []}
NO_LABELS = {"calls": {}, "table_uids": {UID}}
BANNED_KEYS = {
    "success",
    "failure",
    "settled",
    "useful",
    "score",
    "agrees",
    "agreement",
    "helped",
    "verdict",
    "correct",
    "wrong",
}


# ----------------------------------------------------------------------- builders


def request(
    question: str, subject: str, reason: str = "proposal_without_sourced_trust"
):
    return {
        "question": question,
        "request_id": f"{question}/{subject}/bounded_zoom",
        "kind": "bounded_zoom",
        "subject": subject,
        "reason": reason,
        "scope": "object_window",
        "bounded": True,
        "full_study": False,
        "uses_existing_measurements": True,
        "discretionary": True,
    }


def question_body(outcome: str, readings: dict[str, str], requests=()):
    return {
        "finding": {
            "outcome": outcome,
            "reason": f"reason-{outcome}",
            "evidence": {
                "readings": {
                    subject: {
                        "role": role,
                        "state": "unknown",
                        "code": "proposal_without_sourced_trust",
                        "recall_outcomes": ["proposal"],
                        "trust_checked": False,
                        "speaking_case_ids": [],
                    }
                    for subject, role in readings.items()
                },
                "necessary": [s for s, r in readings.items() if r == "necessary"],
                "alternatives": [s for s, r in readings.items() if r == "alternative"],
                "supporting": [s for s, r in readings.items() if r == "supporting"],
            },
            "observation_requests": list(requests),
            "rank": {"tier": outcome},
        },
        "ranking": {},
        "objects": {},
    }


def obs(subject: str, code: str = "measured", requested_by: str | None = None):
    row: dict = {"code": code, "subject": subject}
    if code == "measured":
        row.update(
            regions=[{"series_uid": "s1", "window": [1, 2, 3, 4, 5, 6]}],
            lens="physical_squint",
            tile_mm=2.0,
            procedure="writer-v2",
            held_regions=[],
            unavailable_regions=[],
        )
    if requested_by:
        row["requested_by"] = requested_by
    return row


def recall(outcome: str, scale: str = "10mm"):
    return {
        "scale": scale,
        "outcome": outcome,
        "identity_state": "contested",
        "appearance": "silent",
        "reason": "r",
        "applicable_negative_case_ids": ["n1"],
    }


def make_record(
    *,
    uid: str = UID,
    observations=(),
    unresolved=(),
    questions=None,
    contested=("femur",),
    resolved_outcome="appearance_silent",
):
    questions = questions or {
        "ACL": question_body(
            "open",
            {"acl": "necessary", "femur": "supporting"},
            [request("ACL", "acl")],
        ),
        "MCL": question_body("assigned", {"mcl": "necessary", "femur": "supporting"}),
        "Medial Meniscus": question_body(
            "open",
            {"medial_meniscus": "necessary", "tibia": "supporting"},
            [request("Medial Meniscus", "medial_meniscus")],
        ),
    }
    return {
        "schema": "knee.squint-study/v1",
        "study_uid": uid,
        "memory_revision": REV,
        "study_status": "examined",
        "questions": questions,
        "values": {name: 0.5 for name in questions},
        "objects": {
            "femur": {
                "status": "proposal",
                "evidence": {"location_route": "structural_anchor", "source": "s"},
                "territories": [{"origin": "anchor_structure"}],
                "regions": [],
                "sanity": {"status": "unknown"},
            },
            "acl": {
                "status": "proposal",
                "evidence": {
                    "location_route": "anatomical_relation_from_structural_anchors"
                },
                "territories": [
                    {
                        "origin": "anatomical_relation",
                        "relation": {"knee_side": "left", "knee_side_status": "named"},
                        "anchors": [
                            {
                                "anchor": "patella",
                                "kind": "k",
                                "anchor_observation_status": "complete",
                                "prior_only": False,
                            }
                        ],
                    }
                ],
                "regions": [],
            },
        },
        "identity_recall": {
            "outcome": "examined",
            "objects": {s: recall("appearance_opposed") for s in contested},
            "resolved_scale": {
                "scale": "10mm+2mm",
                "contested_at_squint_scale": list(contested),
                "objects": {s: recall(resolved_outcome, "10mm+2mm") for s in contested},
            },
        },
        "identity_consumption": {
            "objects": {
                s: {
                    "identity_effect": "answers",
                    "region_read_as_subject": True,
                    "identity_state": "unconditioned",
                    "identity_scale": "10mm+2mm",
                    "squint_scale_contest": {
                        "status": "resolved_by_finer_reading",
                        "finer_look": {"code": "measured"},
                    },
                    "identity_context": {"basis": "prior_only", "contradictions": []},
                }
                for s in [*contested, "acl"]
            }
        },
        "observations": list(observations),
        "unresolved_observation_requests": list(unresolved),
        "work": {"series_read": 5, "leg_map_status": "measured"},
    }


def main_record(**kwargs):
    """Femur identity look, then ACL / MCL / Medial Meniscus first-pass zoom rows.

    The MCL finding is decided after its look, so only ACL and Medial Meniscus still list a
    request: the MCL row of the first pass matches no final request.
    """
    return make_record(
        observations=[
            obs("femur", requested_by="identity_question"),
            obs("acl"),
            obs("mcl"),
            obs("medial_meniscus"),
        ],
        unresolved=[
            request("ACL", "acl"),
            request("Medial Meniscus", "medial_meniscus"),
        ],
        **kwargs,
    )


def shared_record():
    """The femur identity look, then a condition question that asks for the same zoom."""
    return make_record(
        observations=[
            obs("femur", requested_by="identity_question"),
            obs("femur", "shared_observation_already_available"),
        ],
        unresolved=[request("ACL", "femur")],
        questions={
            "ACL": question_body(
                "open",
                {"acl": "alternative", "femur": "alternative"},
                [request("ACL", "femur")],
            )
        },
    )


def rows_of(record, labels=NO_LABELS, calls=NO_CALLS, source=SOURCE):
    return pe.experience_rows(record, source, labels=labels, call_index=calls)


def row_for(rows, index):
    return next(r for r in rows if r["row_id"].endswith(f"|{index:03d}"))


def all_keys(value):
    found = set()
    if isinstance(value, dict):
        for key, item in value.items():
            found.add(key)
            found |= all_keys(item)
    elif isinstance(value, list):
        for item in value:
            found |= all_keys(item)
    return found


# ----------------------------------------------------------------------- test 1


def test_an_unchecked_study_yields_no_success_or_failure_label():
    rows = rows_of(main_record())
    assert len(rows) == 4
    for row in rows:
        assert row["independent_outcome"]["status"] == "unchecked"
        assert not (all_keys(row) & BANNED_KEYS)
    reasons = {r["independent_outcome"]["reason"] for r in rows}
    assert reasons <= {
        "label_blank_no_call",
        "no_visual_review_call_for_this_study_and_object",
    }


def test_a_labelled_study_is_checked_with_the_label_and_still_carries_no_verdict():
    labels = {"calls": {UID: {"ACL": -1, "Medial Meniscus": 1}}, "table_uids": {UID}}
    rows = rows_of(main_record(), labels=labels)
    acl = row_for(rows, 1)
    assert acl["request"]["question"] == "ACL"
    assert acl["independent_outcome"]["status"] == "checked"
    assert acl["independent_outcome"]["call"] == -1
    assert acl["independent_outcome"]["scope"] == "study_condition"
    # the label sits beside the question's own final state; no comparison is written
    assert acl["state"]["after"]["outcome"] == "open"
    assert not (all_keys(acl) & BANNED_KEYS)
    # MCL has no label in this table: the row is unchecked, not "checked as absent"
    mcl = row_for(rows, 2)
    assert mcl["independent_outcome"] == {
        "status": "unchecked",
        "reason": "label_blank_no_call",
    }


# ----------------------------------------------------------------------- test 2


def test_a_blank_label_is_not_a_negative():
    text = (
        "StudyInstanceUID,Report,ACL,MCL,Medial Meniscus\n"
        f"{UID},report text,1,0,\n"
        f"{OTHER_UID},other report,,,\n"
    )
    labels = pe.read_label_table(text)
    assert labels["calls"][UID] == {"ACL": 1, "MCL": -1}
    assert "Medial Meniscus" not in labels["calls"][UID]
    assert OTHER_UID not in labels["calls"]
    assert labels["table_uids"] == {UID, OTHER_UID}
    rows = rows_of(main_record(), labels=labels)
    assert row_for(rows, 1)["independent_outcome"]["call"] == 1  # ACL "1" -> +1
    blank = row_for(rows, 3)  # Medial Meniscus cell is blank
    assert blank["request"]["question"] == "Medial Meniscus"
    assert blank["independent_outcome"]["status"] == "unchecked"
    assert blank["independent_outcome"]["reason"] == "label_blank_no_call"
    unlabelled = rows_of(main_record(uid=OTHER_UID), labels=labels)
    assert {r["independent_outcome"]["status"] for r in unlabelled} == {"unchecked"}


def test_a_value_that_is_not_zero_or_one_is_no_call():
    labels = pe.read_label_table(f"StudyInstanceUID,Report,ACL\n{UID},r,2\n")
    assert UID not in labels["calls"]


# ----------------------------------------------------------------------- test 3


def test_a_request_that_did_not_run_is_not_an_outcome():
    labels = {"calls": {UID: {"ACL": 1}}, "table_uids": {UID}}
    record = make_record(
        observations=[obs("acl", "deadline_before_zoom"), obs("medial_meniscus")],
        unresolved=[
            request("ACL", "acl"),
            request("Medial Meniscus", "medial_meniscus"),
        ],
    )
    rows = rows_of(record, labels=labels)
    acl = row_for(rows, 0)
    assert acl["execution"]["status"] == "not_run"
    assert acl["execution"]["reading_available"] is False
    assert acl["state"]["changed"] is None
    assert acl["independent_outcome"] == {
        "status": "unchecked",
        "reason": "request_did_not_run",
    }
    # the opposite sign: the same request, run, takes the label
    ran = rows_of(
        make_record(
            observations=[obs("acl"), obs("medial_meniscus")],
            unresolved=[
                request("ACL", "acl"),
                request("Medial Meniscus", "medial_meniscus"),
            ],
        ),
        labels=labels,
    )
    assert row_for(ran, 0)["independent_outcome"]["status"] == "checked"


def test_a_final_request_with_no_routed_row_is_listed_as_not_run_and_never_checked():
    labels = {"calls": {UID: {"ACL": 1}}, "table_uids": {UID}}
    record = make_record(
        observations=[],
        unresolved=[request("ACL", "acl")],
    )
    rows = rows_of(record, labels=labels)
    assert len(rows) == 1
    row = rows[0]
    assert row["row_id"].endswith("|u000")
    assert row["execution"]["status"] == "not_run"
    assert row["execution"]["observation_index"] is None
    assert row["state"]["changed"] is None
    assert row["independent_outcome"]["reason"] == "request_did_not_run"


def test_a_shared_row_made_no_reading_and_points_at_the_look_that_did():
    shared = row_for(rows_of(shared_record()), 1)
    assert shared["request"]["question"] == "ACL"
    assert shared["execution"]["status"] == "reading_already_available"
    assert shared["execution"]["new_reading"] is False
    # a reading is available to the question, but this request ran no look
    assert shared["execution"]["reading_available"] is True
    assert shared["execution"]["reading_supplied_by"]["observation_index"] == 0
    assert (
        shared["execution"]["reading_supplied_by"]["requested_by"]
        == "identity_question"
    )
    made = row_for(rows_of(main_record()), 1)
    assert made["execution"]["new_reading"] is True
    assert made["execution"]["reading_available"] is True
    assert made["execution"]["reading_supplied_by"]["observation_index"] == 1
    # a shared row with no earlier new reading of its subject names no supplier
    orphan = make_record(
        observations=[obs("femur", "shared_observation_already_available")],
        unresolved=[request("ACL", "femur")],
        questions=shared_record()["questions"],
    )
    assert row_for(rows_of(orphan), 0)["execution"]["reading_supplied_by"] is None


@pytest.mark.parametrize(
    ("code", "status"),
    [
        ("measured", "ran_new_reading"),
        ("shared_observation_already_available", "reading_already_available"),
        ("already_measured", "reading_already_available"),
        ("deadline_before_zoom", "not_run"),
        ("no_compatible_bounded_reading", "not_run"),
        ("something_new_the_code_does_not_know", "not_run"),
        (None, "not_run"),
    ],
)
def test_execution_status_credits_only_codes_that_say_a_reading_exists(code, status):
    assert pe.execution_status(code) == status


# ----------------------------------------------------------------------- test 4


def test_rows_keep_their_source_pins():
    rows = rows_of(main_record())
    for row in rows:
        for key, value in SOURCE.items():
            assert row["source"][key] == value
        assert row["source"]["study_uid"] == UID
        assert row["row_id"].startswith(f"run-a|{UID}|")
    other = {**SOURCE, "run": "run-b", "memory_sha256": "c" * 64}
    moved = rows_of(main_record(), source=other)
    assert {r["source"]["memory_sha256"] for r in moved} == {"c" * 64}
    assert {r["source"]["run"] for r in moved} == {"run-b"}
    assert {r["row_id"] for r in rows}.isdisjoint({r["row_id"] for r in moved})


@pytest.mark.parametrize("missing", list(SOURCE))
def test_a_row_without_its_pins_is_refused(missing):
    source = {k: v for k, v in SOURCE.items() if k != missing}
    with pytest.raises(ValueError, match=missing):
        rows_of(main_record(), source=source)


def test_a_record_of_another_schema_is_refused():
    record = main_record()
    record["schema"] = "something-else"
    with pytest.raises(ValueError, match="knee.squint-study"):
        rows_of(record)


# ----------------------------------------------------------------------- the question is reconstructed


def test_the_question_of_a_routed_row_is_reconstructed_and_says_so():
    rows = rows_of(main_record())
    acl = row_for(rows, 1)
    assert acl["request"]["question"] == "ACL"
    assert (
        acl["request"]["provenance"]["question"] == "reconstructed_by_order_and_subject"
    )
    assert acl["request"]["listed_after_the_look"] is True
    assert acl["request"]["provenance"]["first_pass_reason"] == "not_recorded"
    assert acl["question_attribution"]["status"] == "reconstructed_unique"
    assert "L1763-1792" in acl["question_attribution"]["rests_on"]
    # an identity look names its question in the record itself
    identity = row_for(rows, 0)
    assert identity["request"]["question"] == "identity"
    assert identity["request"]["provenance"]["question"] == "recorded"
    assert identity["question_attribution"]["status"] == "recorded"


def test_a_first_pass_row_no_final_request_stands_for_goes_to_the_one_question_that_fits():
    rows = rows_of(main_record())
    mcl = row_for(rows, 2)
    assert mcl["question_attribution"]["kind"] == "dropped"
    assert mcl["request"]["question"] == "MCL"
    assert mcl["request"]["listed_after_the_look"] is False
    assert mcl["request"]["reason"] is None
    assert mcl["request"]["provenance"]["reason"] == "not_recorded"
    # the question was open before the look by code and decided after it: described, not credited
    assert mcl["state"]["before"]["outcome"] == "open"
    assert mcl["state"]["before"]["provenance"] == "derived_from_code_path"
    assert mcl["state"]["before"]["reason"] is None
    assert mcl["state"]["after"]["outcome"] == "assigned"
    assert mcl["state"]["changed"] is True


def test_two_questions_that_fit_stay_ambiguous_and_none_is_picked():
    questions = {
        "ACL": question_body("open", {"acl": "necessary"}, [request("ACL", "acl")]),
        "MCL": question_body("assigned", {"mcl": "necessary"}),
        "Medial Meniscus": question_body(
            "open",
            {"medial_meniscus": "necessary", "mcl": "supporting"},
            [request("Medial Meniscus", "medial_meniscus")],
        ),
    }
    rows = rows_of(main_record(questions=questions))
    mcl = row_for(rows, 2)
    assert mcl["question_attribution"]["status"] == "ambiguous"
    assert mcl["question_attribution"]["candidates"] == ["MCL", "Medial Meniscus"]
    assert mcl["request"]["question"] is None
    assert mcl["independent_outcome"] == {
        "status": "unchecked",
        "reason": "question_not_attributed",
    }


def test_a_row_between_two_rows_of_one_question_belongs_to_that_question():
    order = ["Q1", "Q2", "Q3"]
    contracts = {"Q1": {"a", "b", "c"}, "Q2": {"b"}, "Q3": {"b"}}
    unresolved = [
        {"question": "Q1", "subject": "a"},
        {"question": "Q1", "subject": "c"},
    ]
    attributions, _ = pe.attribute_routed(["a", "b", "c"], unresolved, order, contracts)
    assert attributions[1]["kind"] == "dropped"
    assert attributions[1]["question"] == "Q1"
    # the opposite sign: when the neighbours belong to different questions, the same row is open
    split = [{"question": "Q1", "subject": "a"}, {"question": "Q3", "subject": "c"}]
    attributions, _ = pe.attribute_routed(
        ["a", "b", "c"], split, order, {**contracts, "Q3": {"b", "c"}}
    )
    assert attributions[1]["kind"] == "dropped_ambiguous"
    assert attributions[1]["candidates"] == ["Q1", "Q2", "Q3"]


def test_a_row_cannot_belong_to_a_question_before_its_earlier_neighbour():
    order = ["Q1", "Q2", "Q3"]
    contracts = {"Q1": {"b"}, "Q2": {"a", "b"}, "Q3": {"b", "c"}}
    unresolved = [
        {"question": "Q2", "subject": "a"},
        {"question": "Q3", "subject": "c"},
    ]
    attributions, _ = pe.attribute_routed(["a", "b", "c"], unresolved, order, contracts)
    assert attributions[1]["kind"] == "dropped_ambiguous"
    assert attributions[1]["candidates"] == ["Q2", "Q3"]
    # a row before every matched row may belong to any earlier question
    attributions, _ = pe.attribute_routed(
        ["b", "a"], [{"question": "Q2", "subject": "a"}], order, contracts
    )
    assert attributions[0]["candidates"] == ["Q1", "Q2"]


def test_a_row_that_no_contract_names_is_not_forced_into_a_question():
    order = ["Q1", "Q2"]
    contracts = {"Q1": {"a"}, "Q2": {"c"}}
    unresolved = [
        {"question": "Q1", "subject": "a"},
        {"question": "Q2", "subject": "c"},
    ]
    attributions, _ = pe.attribute_routed(["a", "b", "c"], unresolved, order, contracts)
    assert attributions[1]["kind"] == "dropped_no_question_fits"
    assert attributions[1]["question"] is None


def test_equal_neighbouring_subjects_make_the_alignment_ambiguous():
    ways = pe.alignments(["a", "a"], ["a"])
    assert ways == [(0,), (1,)]
    attributions, matches = pe.attribute_routed(
        ["a", "a"], [{"question": "Q1", "subject": "a"}], ["Q1"], {"Q1": {"a"}}
    )
    assert [a["kind"] for a in attributions] == ["ambiguous", "ambiguous"]
    assert matches == [[0, 1]]
    # one alignment only: unique
    assert pe.alignments(["a", "b"], ["b"]) == [(1,)]


def test_alignments_keep_order_and_never_reuse_a_row():
    assert pe.alignments(["a", "a"], ["a", "a"]) == [(0, 1)]
    assert pe.alignments(["a", "b", "a"], ["a", "a"]) == [(0, 2)]
    assert pe.alignments(["b", "a"], ["a", "b"]) == []
    assert pe.alignments(["a", "b", "c"], ["a", "c"]) == [(0, 2)]
    assert pe.alignments(["a"], []) == [()]


def test_a_catalogue_call_is_no_check_even_if_it_carried_this_records_sha():
    forged = {
        "reviewer_calls": {
            (UID, "femur"): [
                {
                    "call": "confirm",
                    "views": [["Coronal", "0", "0"]],
                    "reader": "lead",
                    "candidate_id": f"squint-case:{UID}:femur",
                    "concerns": "catalogue_case",
                    "record_sha256": RECORD_SHA,
                    "candidate_revision": REV,
                }
            ]
        }
    }
    outcome = rows_of(look_record(), calls=forged)[0]["independent_outcome"]
    assert outcome["status"] == "unchecked"
    assert outcome["reason"] == "visual_call_concerns_another_candidate"


def test_final_requests_that_are_not_a_subsequence_are_not_reconstructed():
    attributions, matches = pe.attribute_routed(
        ["a"], [{"question": "Q1", "subject": "z"}], ["Q1"], {"Q1": {"z"}}
    )
    assert attributions[0]["kind"] == "unaligned"
    assert attributions[0]["question"] is None
    assert matches == [[]]
    assert pe.alignments(["a"], ["z"]) == []


def test_too_many_alignments_are_reported_not_enumerated():
    assert pe.alignments(["a"] * 20, ["a"] * 10, cap=10) is None


def test_a_row_where_alignments_agree_is_unique_even_if_another_row_is_not():
    # rows 0 and 1 are the same subject (ambiguous which carries the request); row 2 is fixed
    attributions, _ = pe.attribute_routed(
        ["a", "a", "b"],
        [{"question": "Q1", "subject": "a"}, {"question": "Q2", "subject": "b"}],
        ["Q1", "Q2"],
        {"Q1": {"a"}, "Q2": {"b"}},
    )
    assert attributions[2]["kind"] == "aligned"
    assert attributions[2]["question"] == "Q2"
    assert attributions[0]["kind"] == "ambiguous"


# ----------------------------------------------------------------------- identity looks


def test_an_identity_look_keeps_the_scale_before_and_after_and_what_the_consumer_read():
    rows = rows_of(main_record())
    look = row_for(rows, 0)
    assert look["request"]["requested_by"] == "identity_question"
    assert look["request"]["reason"] == "contested_at_squint_scale"
    assert look["request"]["provenance"]["reason"] == "derived_from_code_path"
    state = look["state"]
    assert state["before"]["scale"] == "10mm"
    assert state["before"]["outcome"] == "appearance_opposed"
    assert state["after"]["scale"] == "10mm+2mm"
    assert state["after"]["outcome"] == "appearance_silent"
    assert state["changed"] is True
    assert state["consumed"]["identity_effect"] == "answers"
    assert state["consumed"]["region_read_as_subject"] is True
    same = rows_of(main_record(resolved_outcome="appearance_opposed"))
    assert row_for(same, 0)["state"]["changed"] is False


def test_an_identity_state_with_no_joint_comparison_is_not_called_changed_or_unchanged():
    record = main_record()
    del record["identity_recall"]["resolved_scale"]["objects"]["femur"]
    assert row_for(rows_of(record), 0)["state"]["changed"] is None


def test_an_identity_look_records_what_the_consumer_still_names_afterwards():
    record = make_record(
        observations=[obs("femur", requested_by="identity_question")], unresolved=[]
    )
    record["identity_consumption"]["objects"]["femur"]["identity_open_question"] = {
        "status": "open",
        "why": "contested",
        "run": "left_to_the_consumer_within_budget",
        "next_observations": [
            {"request": {"lens": "native-lens"}, "procedure": "residual_native_support"}
        ],
    }
    named = row_for(rows_of(record), 0)["state"]["consumed"]["open_question_after"]
    assert named["named_next_observations"] == [
        {"procedure": "residual_native_support", "lens": "native-lens"}
    ]
    assert named["run"] == "left_to_the_consumer_within_budget"
    # the opposite sign: nothing named, nothing recorded
    quiet = row_for(rows_of(main_record()), 0)["state"]["consumed"]
    assert quiet["open_question_after"] is None


def test_condition_rows_carry_the_subjects_final_identity_as_context_not_as_before():
    rows = rows_of(main_record())
    acl = row_for(rows, 1)
    final = acl["context"]["subject_identity_final"]
    assert final["identity_effect"] == "answers"
    assert final["was_contested_at_squint_scale"] is False
    assert acl["context"]["study"]["knee_side"]["value"] == "left"
    assert acl["context"]["subject"]["placing_anchors"][0]["anchor"] == "patella"


# ----------------------------------------------------------------------- visual calls


def located_id(subject="femur", uid=UID, revision=REV):
    return f"located:{uid}:{subject}:{revision}"


def memory_with_calls():
    return {
        "object_identity_teaching": {
            "calls": [
                {
                    "call": "confirm",
                    "candidate_id": located_id(),
                    "identity_growth": {"kind": "recognition_derived_identity"},
                    "reader": "recognition (not a visual call)",
                    "views": [["Coronal", "0", "0"]],
                    "notes": "admission",
                },
                {
                    "call": "reject",
                    "candidate_id": f"squint-case:{OTHER_UID}:femur",
                    "reader": "lead",
                    "views": [["Sagittal", "0", "0"]],
                    "notes": "soft tissue",
                },
            ],
            "admission_reviews": [
                {
                    "review_sha256": "r" * 64,
                    "calls": [
                        {
                            "call": "confirm",
                            "candidate_id": located_id(),
                            "reader": "root direct inspection",
                            "views": [["Coronal", "0", "0"]],
                            "notes": "bone below the joint",
                        }
                    ],
                }
            ],
        },
        "cases": [
            {
                "case_id": located_id(),
                "identity_growth": {
                    "source": {
                        "record_sha256": RECORD_SHA,
                        "record_sha256_scope": "file_bytes",
                    }
                },
            }
        ],
        "direct_visual_teaching": [],
    }


def test_a_recognition_derived_admission_is_never_an_outcome():
    index = pe.build_call_index(memory_with_calls())
    assert index["recognition_derived_excluded"] == [located_id()]
    calls = index["reviewer_calls"][(UID, "femur")]
    assert [c["source_kind"] for c in calls] == ["admission_review"]
    only_derived = {
        "object_identity_teaching": {
            "calls": memory_with_calls()["object_identity_teaching"]["calls"][:1]
        }
    }
    index = pe.build_call_index(only_derived)
    assert index["reviewer_calls"] == {}
    record = make_record(
        observations=[obs("femur", requested_by="identity_question")], unresolved=[]
    )
    outcome = rows_of(record, calls=index)[0]["independent_outcome"]
    assert outcome == {
        "status": "unchecked",
        "reason": "no_visual_review_call_for_this_study_and_object",
    }


def look_record():
    return make_record(
        observations=[obs("femur", requested_by="identity_question")], unresolved=[]
    )


def test_a_reviewers_call_on_this_runs_own_candidate_checks_the_identity_look():
    index = pe.build_call_index(memory_with_calls())
    row = rows_of(look_record(), calls=index)[0]
    outcome = row["independent_outcome"]
    assert outcome["status"] == "checked"
    assert outcome["scope"] == "reviewed_views"
    evidence = outcome["evidence"][0]
    assert evidence["call"] == "confirm"
    assert evidence["views"] == [["Coronal", "0", "0"]]
    assert evidence["reader"] == "root direct inspection"
    assert not (all_keys(row) & BANNED_KEYS)


def test_a_call_on_another_record_or_revision_is_listed_as_related_not_joined():
    index = pe.build_call_index(memory_with_calls())
    other_record = {**SOURCE, "record_sha256": "f" * 64}
    outcome = rows_of(look_record(), calls=index, source=other_record)[0][
        "independent_outcome"
    ]
    assert outcome["status"] == "unchecked"
    assert outcome["reason"] == "visual_call_concerns_another_candidate"
    assert outcome["related_calls"][0]["call"] == "confirm"
    other_revision = {**SOURCE, "memory_revision": "memory-revision-2"}
    outcome = rows_of(look_record(), calls=index, source=other_revision)[0][
        "independent_outcome"
    ]
    assert outcome["reason"] == "visual_call_concerns_another_candidate"


def test_a_catalogue_call_is_not_a_check_of_this_runs_located_region():
    index = pe.build_call_index(memory_with_calls())
    record = make_record(
        uid=OTHER_UID,
        observations=[obs("femur", requested_by="identity_question")],
        unresolved=[],
    )
    outcome = rows_of(record, calls=index)[0]["independent_outcome"]
    assert outcome["status"] == "unchecked"
    assert outcome["reason"] == "visual_call_concerns_another_candidate"
    assert outcome["related_calls"][0]["concerns"] == "catalogue_case"


def test_an_identity_call_is_never_the_outcome_of_a_condition_question():
    index = pe.build_call_index(memory_with_calls())
    record = make_record(
        observations=[obs("femur", requested_by="identity_question"), obs("acl")],
        unresolved=[request("ACL", "acl")],
    )
    rows = rows_of(record, calls=index)
    assert rows[0]["independent_outcome"]["status"] == "checked"
    acl = next(r for r in rows if r["request"]["question"] == "ACL")
    assert acl["independent_outcome"]["status"] == "unchecked"
    femur_condition = make_record(
        observations=[
            obs("femur", requested_by="identity_question"),
            obs("femur", "shared_observation_already_available"),
        ],
        unresolved=[request("ACL", "femur")],
    )
    shared = [
        r
        for r in rows_of(femur_condition, calls=index)
        if r["request"]["question"] == "ACL"
    ]
    assert shared[0]["independent_outcome"]["status"] == "unchecked"
    assert shared[0]["independent_outcome"]["reason"] == "label_blank_no_call"


# ----------------------------------------------------------------------- reporting helper


def test_tally_counts_for_reporting_and_derives_no_score():
    rows = rows_of(main_record()) + rows_of(shared_record())
    counts = pe.tally(rows, lambda r: r["execution"]["status"])
    assert counts == {"ran_new_reading": 5, "reading_already_available": 1}
    assert sum(counts.values()) == len(rows)
