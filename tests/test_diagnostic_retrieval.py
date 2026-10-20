from dataclasses import replace

from knee.diagnosis import retrieval
from knee.diagnosis.models import Call, Case, Censor, Profile, Question, Snapshot, Trust
from knee.diagnosis.retrieval import prepare_question, prepare_snapshot, recall
from knee.encoding.counts import BankLayout, CountBundle, CountLayout


def _layout() -> CountLayout:
    return CountLayout(
        "layout:reference-a:v1",
        "carrier:v1",
        (BankLayout("content/signal", 3), BankLayout("context/view", 2)),
    )


def _profile(
    source_id: str,
    signal: tuple[int, int, int] = (1, 0, 0),
    *,
    subject: str = "diagnosis/acl",
    mode: str = "full",
    scope: str = "object:acl",
    scanner: str = "scanner-a",
) -> Profile:
    return Profile(
        subject=subject,
        bundle=CountBundle(_layout(), (signal, (1, 0))),
        mode=mode,
        scope=scope,
        source_id=source_id,
        context=(("scanner", scanner),),
    )


def _case(
    case_id: str, study_uid: str, answer: int, profile: Profile | None = None
) -> Case:
    return Case(
        case_id=case_id,
        study_uid=study_uid,
        profile=profile or _profile(f"source:{case_id}"),
        calls=(Call("acl", answer, "independent-teacher", f"call {answer}"),),
        teaching_revision="seed-v1",
    )


def _question() -> Question:
    return Question(
        question_id="acl",
        subject="diagnosis/acl",
        objects=("acl",),
        banks=("content/signal",),
        context_keys=("scanner",),
    )


def test_positive_individual_trusted_precedent_recalls_present() -> None:
    case = _case("positive", "study-positive", 1)
    snapshot = Snapshot(
        revision="memory-v1",
        cases=(case,),
        trust=(Trust(case.case_id, "acl", 1, 1, "separate-chance-study"),),
    )

    result = recall(_profile("query"), _question(), snapshot)

    assert result["outcome"] == "present"
    assert result["speaking_case_ids"] == ["positive"]
    assert result["speaking_calls"] == [1]
    assert result["nearest_positive_case_id"] == "positive"
    assert result["nearest_negative_case_id"] is None
    assert result["case_terms"][0]["terms"] == {
        "dot": 1,
        "left_norm_sq": 1,
        "right_norm_sq": 1,
    }
    assert result["case_terms"][0]["common_speaking_banks"] == ["content/signal"]


def test_negative_individual_trusted_precedent_recalls_absent() -> None:
    case = _case("negative", "study-negative", -1)
    snapshot = Snapshot(
        revision="memory-v1",
        cases=(case,),
        trust=(Trust(case.case_id, "acl", 1, 1, "separate-chance-study"),),
    )

    result = recall(_profile("query"), _question(), snapshot)

    assert result["outcome"] == "absent"
    assert result["speaking_case_ids"] == ["negative"]
    assert result["speaking_calls"] == [-1]
    assert result["nearest_positive_case_id"] is None
    assert result["nearest_negative_case_id"] == "negative"


def test_untrusted_nearest_case_is_proposal_not_diagnosis() -> None:
    case = _case("untrusted-positive", "study-positive", 1)
    result = recall(
        _profile("query"), _question(), Snapshot(revision="memory-v1", cases=(case,))
    )

    assert result["outcome"] == "proposal"
    assert result["speaking_case_ids"] == []
    assert result["nearest_positive_case_id"] == "untrusted-positive"


def test_trusted_near_miss_censor_veto_is_named_separately() -> None:
    case = _case("positive", "study-positive", 1)
    censor = Censor(
        censor_id="miss-positive-answer",
        question="acl",
        answer=1,
        profile=_profile("near-miss-source"),
        numerator=1,
        denominator=1,
        source="independently-confirmed-near-miss",
    )
    snapshot = Snapshot(
        revision="memory-v1",
        cases=(case,),
        trust=(Trust(case.case_id, "acl", 1, 1, "separate-chance-study"),),
        censors=(censor,),
    )

    result = recall(_profile("query"), _question(), snapshot)

    assert result["outcome"] == "unresolved_censored"
    assert result["speaking_case_ids"] == ["positive"]
    assert result["censor_ids"] == ["miss-positive-answer"]
    assert result["vetoed_answers"] == [1]


def test_equal_nearest_cases_remain_tied_without_identifier_tiebreak() -> None:
    first = _case("z-case", "study-z", 1)
    second = _case("a-case", "study-a", 1)

    result = recall(
        _profile("query"),
        _question(),
        Snapshot(revision="memory-v1", cases=(first, second)),
    )

    assert result["outcome"] == "proposal"
    assert result["nearest_positive_case_ids"] == ["z-case", "a-case"]
    assert result["nearest_positive_case_id"] is None


def test_every_reaching_opposite_case_conflicts_even_when_farther() -> None:
    positive = _case("near-positive", "study-positive", 1)
    negative = _case(
        "far-negative",
        "study-negative",
        -1,
        _profile("source:far-negative", signal=(0, 1, 0)),
    )
    snapshot = Snapshot(
        revision="memory-v1",
        cases=(positive, negative),
        trust=(
            Trust(positive.case_id, "acl", 1, 1, "separate-chance-study"),
            Trust(negative.case_id, "acl", 0, 1, "separate-chance-study"),
        ),
    )

    result = recall(_profile("query"), _question(), snapshot)

    assert result["outcome"] == "unresolved_conflict"
    assert set(result["speaking_case_ids"]) == {"near-positive", "far-negative"}
    assert {item["case_id"] for item in result["case_terms"]} == {
        "near-positive",
        "far-negative",
    }


def test_same_study_is_excluded_before_it_can_speak() -> None:
    case = _case("same-study", "study-query", 1)
    snapshot = Snapshot(
        revision="memory-v1",
        cases=(case,),
        trust=(Trust(case.case_id, "acl", 1, 1, "separate-chance-study"),),
    )

    result = recall(
        _profile(
            "query",
        ),
        _question(),
        snapshot,
        exclude_study_uid="study-query",
    )

    assert result["outcome"] == "unresolved_no_precedent"
    assert result["speaking_case_ids"] == []
    assert result["excluded_case_ids"] == ["same-study"]


def test_silent_selected_query_bank_is_missing_reading_not_absent() -> None:
    silent_query = _profile("query", signal=(0, 0, 0))
    case = _case("negative", "study-negative", -1)
    snapshot = Snapshot(
        revision="memory-v1",
        cases=(case,),
        trust=(Trust(case.case_id, "acl", 1, 1, "separate-chance-study"),),
    )

    result = recall(silent_query, _question(), snapshot)

    assert result["outcome"] == "unresolved_missing_reading"
    assert result["speaking_case_ids"] == []
    assert result["nearest_negative_case_id"] is None


def test_context_disagreement_is_incompatible_not_a_weak_match() -> None:
    query = _profile("query", scanner="scanner-b")
    case = _case("positive", "study-positive", 1)
    snapshot = Snapshot(
        revision="memory-v1",
        cases=(case,),
        trust=(Trust(case.case_id, "acl", 1, 1, "separate-chance-study"),),
    )

    result = recall(query, _question(), snapshot)

    assert result["outcome"] == "incompatible_encoding"
    assert result["incompatible_case_ids"] == ["positive"]
    assert result["speaking_case_ids"] == []


def test_question_prefix_selects_only_declared_matching_banks() -> None:
    case = _case("positive", "study-positive", 1)
    question = Question(
        question_id="acl",
        subject="diagnosis/acl",
        objects=("acl",),
        bank_prefixes=("content/",),
        context_keys=("scanner",),
    )

    result = recall(
        _profile("query"), question, Snapshot(revision="memory-v1", cases=(case,))
    )

    assert result["outcome"] == "proposal"
    assert result["selected_banks"] == ["content/signal"]
    assert result["case_terms"][0]["common_speaking_banks"] == ["content/signal"]


def test_boolean_call_digit_is_invalid_not_a_ternary_sign() -> None:
    malformed = Case(
        case_id="malformed",
        study_uid="study-malformed",
        profile=_profile("source:malformed"),
        calls=(Call("acl", True, "teacher"),),
        teaching_revision="seed-v1",
    )

    result = recall(
        _profile("query"),
        _question(),
        Snapshot(revision="memory-v1", cases=(malformed,)),
    )

    assert result["outcome"] == "invalid_input"
    assert result["reason"] == "invalid_call_digit"


def test_prepared_snapshot_and_question_match_direct_recall_and_are_reusable():
    positive = _case("positive", "study-positive", 1)
    negative = _case("negative", "study-negative", -1)
    snapshot = Snapshot(
        revision="memory-v1",
        cases=(positive, negative),
        trust=(
            Trust(positive.case_id, "acl", 1, 1, "independent"),
            Trust(negative.case_id, "acl", 1, 1, "independent"),
        ),
    )
    query = _profile("query")
    question = _question()
    expected = recall(query, question, snapshot)
    prepared_snapshot = prepare_snapshot(snapshot)
    prepared_question = prepare_question(query, question, prepared_snapshot)

    assert recall(query, question, prepared_snapshot) == expected
    assert recall(query, question, prepared_question) == expected
    assert (
        recall(query, question, prepared_question, exclude_study_uid="study-positive")[
            "outcome"
        ]
        == "absent"
    )
    assert recall(query, question, prepared_question) == expected


def test_projection_drops_only_query_silent_banks_but_reports_original_selection():
    layout = _layout()
    query = Profile(
        subject="diagnosis/acl",
        bundle=CountBundle(layout, ((1, 0, 0), (0, 0))),
        mode="full",
        scope="object:acl",
        source_id="query",
        context=(("scanner", "scanner-a"),),
    )
    case_profile = Profile(
        subject="diagnosis/acl",
        bundle=CountBundle(layout, ((1, 0, 0), (1, 0))),
        mode="full",
        scope="object:acl",
        source_id="case-source",
        context=(("scanner", "scanner-a"),),
    )
    case = _case("positive", "study-positive", 1, case_profile)
    snapshot = Snapshot(
        revision="memory-v1",
        cases=(case,),
        trust=(Trust(case.case_id, "acl", 1, 1, "independent"),),
    )
    question = Question(
        question_id="acl",
        subject="diagnosis/acl",
        objects=("acl",),
        banks=("content/signal", "context/view"),
        context_keys=("scanner",),
    )

    result = recall(query, question, snapshot)

    assert result["outcome"] == "present"
    assert result["selected_banks"] == ["content/signal", "context/view"]
    assert result["case_terms"][0]["common_speaking_banks"] == ["content/signal"]


def test_projected_subset_cannot_promote_originally_incompatible_layout():
    query = _profile("query")
    subset_layout = CountLayout(
        _layout().layout_id,
        _layout().carrier_id,
        (BankLayout("content/signal", 3),),
    )
    subset_profile = Profile(
        "diagnosis/acl",
        CountBundle(subset_layout, ((1, 0, 0),)),
        "full",
        "object:acl",
        "subset-source",
        context=(("scanner", "scanner-a"),),
    )
    case = _case("same-nominal-identity", "study-subset", 1, subset_profile)
    snapshot = Snapshot(
        revision="memory-v1",
        cases=(case,),
        trust=(Trust(case.case_id, "acl", 1, 1, "independent"),),
    )
    question = _question()

    expected = retrieval._recall_projected(query, question, snapshot)
    actual = recall(
        query, question, prepare_question(query, question, prepare_snapshot(snapshot))
    )

    assert expected["outcome"] == "incompatible_encoding"
    assert actual == expected
    assert actual["incompatible_case_ids"] == [case.case_id]
    assert actual["speaking_case_ids"] == []


def test_originally_compatible_malformed_bundle_remains_invalid_after_projection():
    query = _profile("query")
    malformed = Profile(
        "diagnosis/acl",
        CountBundle(_layout(), ((1, 0, 0),)),
        "full",
        "object:acl",
        "malformed-source",
        context=(("scanner", "scanner-a"),),
    )
    case = _case("malformed-compatible", "study-malformed", 1, malformed)
    snapshot = Snapshot(revision="memory-v1", cases=(case,))
    question = _question()

    expected = retrieval._recall_projected(query, question, snapshot)
    actual = recall(
        query, question, prepare_question(query, question, prepare_snapshot(snapshot))
    )

    assert expected == {
        "outcome": "invalid_input",
        "reason": "invalid_case_bundle_or_bank_selection",
    }
    assert actual == expected


def test_malformed_dict_bundle_branch_stays_named_invalid_input():
    query = _profile("query")
    malformed = Profile(
        "diagnosis/acl",
        {},
        "full",
        "object:acl",
        "malformed-dict-source",
        context=(("scanner", "scanner-a"),),
    )
    case = _case("malformed-dict", "study-malformed-dict", 1, malformed)
    snapshot = Snapshot(revision="memory-v1", cases=(case,))
    question = _question()

    expected = retrieval._recall_projected(query, question, snapshot)
    actual = recall(
        query, question, prepare_question(query, question, prepare_snapshot(snapshot))
    )

    assert expected == {
        "outcome": "invalid_input",
        "reason": "malformed_snapshot_or_question_data",
    }
    assert actual == expected


def test_originally_compatible_malformed_censor_stays_invalid_after_projection():
    query = _profile("query")
    malformed = Profile(
        "diagnosis/acl",
        CountBundle(_layout(), ((1, 0, 0),)),
        "full",
        "object:acl",
        "malformed-censor-source",
        context=(("scanner", "scanner-a"),),
    )
    censor = Censor("malformed-censor", "acl", 1, malformed, 1, 1, "independent")
    snapshot = Snapshot(revision="memory-v1", censors=(censor,))
    question = _question()

    expected = retrieval._recall_projected(query, question, snapshot)
    actual = recall(
        query, question, prepare_question(query, question, prepare_snapshot(snapshot))
    )

    assert expected == {
        "outcome": "invalid_input",
        "reason": "invalid_censor_bundle_or_bank_selection",
    }
    assert actual == expected


def test_projected_subset_cannot_promote_originally_incompatible_censor():
    query = _profile("query")
    subset_layout = CountLayout(
        _layout().layout_id,
        _layout().carrier_id,
        (BankLayout("content/signal", 3),),
    )
    subset_profile = Profile(
        "diagnosis/acl",
        CountBundle(subset_layout, ((1, 0, 0),)),
        "full",
        "object:acl",
        "subset-censor-source",
        context=(("scanner", "scanner-a"),),
    )
    censor = Censor("subset-censor", "acl", 1, subset_profile, 1, 1, "independent")
    snapshot = Snapshot(revision="memory-v1", censors=(censor,))
    question = _question()

    expected = retrieval._recall_projected(query, question, snapshot)
    actual = recall(
        query, question, prepare_question(query, question, prepare_snapshot(snapshot))
    )

    assert expected["outcome"] == "incompatible_encoding"
    assert actual == expected
    assert actual["censor_ids"] == []


def _large_profile(
    source_id: str, layout: CountLayout, zero_rows: tuple[int, ...]
) -> Profile:
    active = (1,) + (0,) * (layout.banks[0].row_count - 1)
    counts = (active,) + (zero_rows,) * (len(layout.banks) - 1)
    return Profile(
        subject="diagnosis/acl",
        bundle=CountBundle(layout, counts),
        mode="full",
        scope="object:acl",
        source_id=source_id,
        context=(),
    )


def test_production_sized_question_projection_avoids_revalidating_full_case_bundles(
    monkeypatch,
):
    bank_count = 3696
    row_count = 512
    layout = CountLayout(
        "layout:retained-reference:v1",
        "carrier:v1",
        tuple(
            BankLayout(f"content/{index:04d}", row_count) for index in range(bank_count)
        ),
    )
    zeros = (0,) * row_count
    query = _large_profile("query", layout, zeros)
    cases = tuple(
        _case(
            f"case-{index:02d}",
            f"study-{index:02d}",
            1,
            _large_profile(f"case-source-{index:02d}", layout, zeros),
        )
        for index in range(44)
    )
    snapshot = Snapshot(
        revision="large-memory-v1",
        cases=cases,
        trust=tuple(Trust(case.case_id, "acl", 1, 1, "independent") for case in cases),
    )
    question = Question(
        question_id="acl",
        subject="diagnosis/acl",
        objects=("acl",),
        bank_prefixes=("content/",),
    )
    original_valid_bundle = retrieval._counts._valid_bundle
    full_layout_checks = 0
    projected_layout_checks = 0

    def counted_valid_bundle(bundle):
        nonlocal full_layout_checks, projected_layout_checks
        if isinstance(bundle, CountBundle):
            if len(bundle.layout.banks) == bank_count:
                full_layout_checks += 1
            else:
                projected_layout_checks += 1
        return original_valid_bundle(bundle)

    monkeypatch.setattr(retrieval._counts, "_valid_bundle", counted_valid_bundle)
    prepared_snapshot = prepare_snapshot(snapshot)
    assert full_layout_checks == 44
    plan = prepare_question(query, question, prepared_snapshot)
    result = recall(query, question, plan)
    assert result["outcome"] == "present"
    assert len(result["selected_banks"]) == bank_count
    assert len(result["speaking_case_ids"]) == 44
    assert full_layout_checks == 45  # 44 cases plus the query, once each.

    for _ in range(3):
        assert recall(query, question, plan) == result
    assert full_layout_checks == 45
    assert projected_layout_checks > 0


def _group_profile(source_id: str, *, context_group: str | None = None) -> Profile:
    profile = _profile(source_id)
    if context_group is not None:
        profile = replace(
            profile, context=profile.context + (("source_group", context_group),)
        )
    return profile


def test_source_group_excludes_distinct_uid_before_comparison():
    same_group = _case(
        "same-group",
        "different-study",
        1,
        replace(
            _group_profile("source:same-group"),
            provenance=(("source_group", "family-a"),),
        ),
    )
    unrelated = _case(
        "unrelated",
        "other-study",
        -1,
        replace(
            _group_profile("source:unrelated", context_group="family-b"),
            provenance=(("source_group", "family-b"),),
        ),
    )
    snapshot = Snapshot(revision="memory-v1", cases=(same_group, unrelated))

    result = recall(
        _profile("query"),
        _question(),
        snapshot,
        exclude_source_group="family-a",
    )

    assert result["excluded_case_ids"] == ["same-group"]
    assert result["source_group_excluded_case_ids"] == ["same-group"]
    assert result["excluded_source_group"] == "family-a"
    assert result["case_terms"][0]["case_id"] == "unrelated"
    assert result["speaking_case_ids"] == []


def test_absent_or_unknown_source_group_remains_eligible():
    absent = _case("absent", "study-absent", 1, _profile("source:absent"))
    unknown = _case(
        "unknown",
        "study-unknown",
        -1,
        _group_profile("source:unknown", context_group="unknown"),
    )
    result = recall(
        _profile("query"),
        _question(),
        Snapshot(revision="memory-v1", cases=(absent, unknown)),
        exclude_source_group="family-a",
    )

    assert result["source_group_excluded_case_ids"] == []
    assert [item["case_id"] for item in result["case_terms"]] == ["absent", "unknown"]


def test_literal_unknown_source_group_is_an_exact_identifier():
    literal = _case(
        "literal-unknown",
        "study-literal-unknown",
        1,
        _group_profile("source:literal-unknown", context_group="unknown"),
    )
    result = recall(
        _profile("query"),
        _question(),
        Snapshot(revision="memory-v1", cases=(literal,)),
        exclude_source_group="unknown",
    )

    assert result["excluded_case_ids"] == ["literal-unknown"]
    assert result["source_group_excluded_case_ids"] == ["literal-unknown"]
    assert result["case_terms"] == []


def test_study_exclusion_takes_precedence_when_both_exclusions_match():
    same_uid_and_group = _case(
        "both",
        "query-study",
        1,
        replace(
            _group_profile("source:both"), provenance=(("source_group", "family-a"),)
        ),
    )
    same_group = _case(
        "group-only",
        "other-study",
        -1,
        replace(
            _group_profile("source:group-only"),
            provenance=(("source_group", "family-a"),),
        ),
    )
    result = recall(
        _profile("query"),
        _question(),
        Snapshot(revision="memory-v1", cases=(same_uid_and_group, same_group)),
        exclude_study_uid="query-study",
        exclude_source_group="family-a",
    )

    assert result["excluded_case_ids"] == ["both", "group-only"]
    assert result["source_group_excluded_case_ids"] == ["group-only"]


def test_source_group_metadata_must_agree_between_context_and_provenance():
    conflicting = _case(
        "conflict",
        "study-conflict",
        1,
        replace(
            _group_profile("source:conflict", context_group="family-a"),
            provenance=(("source_group", "family-b"),),
        ),
    )
    result = recall(
        _profile("query"),
        _question(),
        Snapshot(revision="memory-v1", cases=(conflicting,)),
        exclude_source_group="family-a",
    )

    assert result == {
        "outcome": "invalid_input",
        "reason": "conflicting_source_group_metadata",
    }


def test_query_group_metadata_conflict_is_invalid_when_group_exclusion_is_requested():
    query = replace(
        _group_profile("query", context_group="family-a"),
        provenance=(("source_group", "family-b"),),
    )
    result = recall(
        query,
        _question(),
        Snapshot(revision="memory-v1"),
        exclude_source_group="family-c",
    )

    assert result == {
        "outcome": "invalid_input",
        "reason": "conflicting_source_group_metadata",
    }


def test_source_group_exclusion_matches_direct_prepared_and_projected_recall():
    grouped = _case(
        "grouped",
        "study-grouped",
        1,
        replace(
            _group_profile("source:grouped"), provenance=(("source_group", "family-a"),)
        ),
    )
    retained = _case("retained", "study-retained", -1)
    snapshot = Snapshot(revision="memory-v1", cases=(grouped, retained))
    query = _profile("query")
    question = _question()
    kwargs = {"exclude_source_group": "family-a"}
    direct = recall(query, question, snapshot, **kwargs)
    prepared_snapshot = prepare_snapshot(snapshot)
    prepared_question = prepare_question(query, question, prepared_snapshot)

    assert recall(query, question, prepared_snapshot, **kwargs) == direct
    assert recall(query, question, prepared_question, **kwargs) == direct
    assert retrieval._recall_projected(
        query,
        question,
        snapshot,
        **kwargs,
    )["source_group_excluded_case_ids"] == ["grouped"]
    assert direct["case_terms"][0]["case_id"] == "retained"


def test_empty_source_group_preserves_legacy_recall_result():
    case = _case("case", "study-case", 1)
    snapshot = Snapshot(revision="memory-v1", cases=(case,))
    expected = recall(_profile("query"), _question(), snapshot)
    actual = recall(
        _profile("query"),
        _question(),
        snapshot,
        exclude_source_group="",
    )

    assert actual == expected


def test_non_string_source_group_is_named_invalid_input():
    result = recall(
        _profile("query"),
        _question(),
        Snapshot(revision="memory-v1"),
        exclude_source_group=["family-a"],  # type: ignore[arg-type]
    )

    assert result == {
        "outcome": "invalid_input",
        "reason": "invalid_source_group_exclusion",
    }


def test_censors_are_not_assigned_or_excluded_by_source_group():
    censor = Censor(
        "censor",
        "acl",
        1,
        replace(
            _group_profile("censor-source"), provenance=(("source_group", "family-a"),)
        ),
        1,
        1,
        "independent",
    )
    result = recall(
        _profile("query"),
        _question(),
        Snapshot(revision="memory-v1", censors=(censor,)),
        exclude_source_group="family-a",
    )

    assert result["source_group_excluded_case_ids"] == []
    assert result["censor_ids"] == ["censor"]
