"""Corrected direct caller-intent checks for the frozen diagnostic-memory contract.

These tests intentionally use small exact count bundles. They exercise case
recall, teaching, and role composition without loading study data or fitting a
similarity threshold.
"""

from __future__ import annotations

from knee.diagnosis.composition import compose_question_profile
from knee.diagnosis.models import Call, Case, Profile, Question, Snapshot, Trust
from knee.diagnosis.retrieval import recall
from knee.diagnosis.teaching import teach_from_labels
from knee.encoding.counts import BankLayout, CountBundle, CountLayout, cosine_terms


def _layout(*, layout_id: str = "layout:diagnostic:v1") -> CountLayout:
    return CountLayout(
        layout_id=layout_id,
        carrier_id="carrier:512:v1",
        banks=(BankLayout("signal", 4), BankLayout("context", 4)),
    )


def _profile(
    *,
    subject: str = "diagnosis/ACL",
    mode: str = "full-native-v1",
    scope: str = "object:acl",
    source_id: str = "source:one",
    counts: tuple[tuple[int, ...], ...] = ((1, 0, 0, 0), (0, 0, 0, 0)),
    layout_id: str = "layout:diagnostic:v1",
    reference: str = "reference:v1",
) -> Profile:
    return Profile(
        subject=subject,
        bundle=CountBundle(_layout(layout_id=layout_id), counts),
        mode=mode,
        scope=scope,
        source_id=source_id,
        context=(("reference", reference), ("view", "sagittal")),
        bank_statuses=(("signal", "measured"), ("context", "silent")),
        provenance=(("reader", "independent"),),
    )


def _case(
    case_id: str,
    digit: int | None,
    *,
    counts: tuple[tuple[int, ...], ...] = ((1, 0, 0, 0), (0, 0, 0, 0)),
    study_uid: str | None = None,
    mode: str = "full-native-v1",
    layout_id: str = "layout:diagnostic:v1",
    reference: str = "reference:v1",
) -> Case:
    calls = (
        ()
        if digit is None
        else (Call("ACL", digit, "independent-call", "scope retained"),)
    )
    uid = study_uid or f"study:{case_id}"
    profile = _profile(
        source_id=f"profile:{case_id}",
        counts=counts,
        mode=mode,
        layout_id=layout_id,
        reference=reference,
    )
    return Case(case_id, uid, profile, calls, "teaching-r1")


def _question(*, context_keys: tuple[str, ...] = ()) -> Question:
    return Question(
        question_id="ACL",
        subject="diagnosis/ACL",
        objects=("acl",),
        banks=("signal",),
        context_keys=context_keys,
    )


def _trusted(*cases: Case, trust: tuple[Trust, ...] | None = None) -> Snapshot:
    if trust is None:
        # Zero is an explicit exact rational level, not an empirically chosen
        # medical threshold. It makes the semantic counterexample exercise all
        # signed cases that share a measured bank.
        trust = tuple(
            Trust(case.case_id, "ACL", 0, 1, "synthetic-intent-test") for case in cases
        )
    return Snapshot("memory-r1", tuple(cases), tuple(trust))


def _outcome(result: dict[str, object]) -> str:
    """Read the named result while keeping the direct recall call in each test."""
    value = result.get("outcome")
    assert isinstance(value, str)
    return value


def test_individual_cases_are_not_replaced_by_an_aggregate_illusion() -> None:
    query = _profile(counts=((1, 0, 0, 0), (0, 0, 0, 0)))
    positive = _case("positive-one", 1, counts=((1, 0, 0, 0), (0, 0, 0, 0)))
    negative = _case("negative-one", -1, counts=((0, 1, 0, 0), (0, 0, 0, 0)))

    result = recall(query, _question(), _trusted(positive, negative))

    assert _outcome(result) == "unresolved_conflict"
    assert result["nearest_positive_case_id"] == "positive-one"
    assert result["nearest_negative_case_id"] == "negative-one"
    rows = result["case_terms"]
    by_case_id = {row["case_id"]: row for row in rows}
    assert by_case_id["positive-one"] != by_case_id["negative-one"]


def test_farther_trusted_opposite_case_still_speaks() -> None:
    query = _profile(counts=((1, 0, 0, 0), (0, 0, 0, 0)))
    near_positive = _case("near-positive", 1, counts=((1, 0, 0, 0), (0, 0, 0, 0)))
    farther_negative = _case("far-negative", -1, counts=((0, 1, 0, 0), (0, 0, 0, 0)))

    result = recall(query, _question(), _trusted(near_positive, farther_negative))

    assert _outcome(result) == "unresolved_conflict"
    assert "near-positive" in result["speaking_case_ids"]
    assert "far-negative" in result["speaking_case_ids"]


def test_missing_question_call_does_not_become_negative() -> None:
    query = _profile()
    unasked = _case("unasked", None)

    result = recall(query, _question(), Snapshot("memory-r1", (unasked,)))

    assert _outcome(result) == "unresolved_no_precedent"
    assert result.get("nearest_negative_case_id") is None


def test_unknown_trust_produces_proposal_not_diagnosis() -> None:
    query = _profile()
    positive = _case("untrusted-positive", 1)

    result = recall(query, _question(), Snapshot("memory-r1", (positive,)))

    assert _outcome(result) == "proposal"
    assert result["nearest_positive_case_id"] == "untrusted-positive"


def test_measured_middle_is_content_and_silent_bank_is_omitted() -> None:
    query = _profile(counts=((0, 1, 0, 0), (0, 0, 0, 0)))
    middle = _case("middle", 1, counts=((0, 1, 0, 0), (0, 0, 0, 0)))
    terms = cosine_terms(query.bundle, middle.profile.bundle, ("signal", "context"))
    silent = _case("silent", -1, counts=((0, 0, 0, 0), (0, 0, 0, 0)))

    result = recall(query, _question(), _trusted(middle, silent))

    assert terms.code.value == "ok"
    assert terms.terms is not None
    assert terms.terms.included_banks == ("signal",)
    assert _outcome(result) != "absent"
    assert "silent" not in result["speaking_case_ids"]


def test_incompatible_mode_or_reference_is_named_not_compared() -> None:
    query = _profile(reference="reference:v1")
    wrong_mode = _case("wrong-mode", 1, mode="cheap-native-v1")
    wrong_reference = _case("wrong-reference", -1, reference="reference:v2")

    mode_result = recall(
        query, _question(context_keys=("reference",)), _trusted(wrong_mode)
    )
    reference_result = recall(
        query, _question(context_keys=("reference",)), _trusted(wrong_reference)
    )

    assert _outcome(mode_result) == "incompatible_encoding"
    assert _outcome(reference_result) == "incompatible_encoding"


def test_arbitrary_region_scope_does_not_match_an_object_scoped_question() -> None:
    from dataclasses import replace

    query = _profile(scope="object:acl")
    region_case = _case("region-case", 1)
    region_case = replace(
        region_case, profile=replace(region_case.profile, scope="region:caller-region")
    )

    result = recall(query, _question(), _trusted(region_case))

    assert _outcome(result) == "incompatible_encoding"
    assert result["incompatible_case_ids"] == ["region-case"]


def test_excluding_same_study_prevents_self_case_from_deciding() -> None:
    query = _profile(source_id="study:self")
    self_case = _case("self", 1, study_uid="study:self")

    result = recall(
        query, _question(), _trusted(self_case), exclude_study_uid="study:self"
    )

    assert _outcome(result) == "unresolved_no_precedent"
    assert result.get("nearest_positive_case_id") is None


def test_role_swap_changes_composite_profile_without_pooling_roles() -> None:
    from dataclasses import replace

    question = Question(
        "Medial OA",
        "diagnosis/Medial OA",
        ("femoral_cartilage", "tibial_cartilage"),
        banks=("object/femoral_cartilage/signal", "object/tibial_cartilage/signal"),
    )
    femoral = _profile(
        subject="femoral_cartilage",
        scope="object:femoral_cartilage",
        counts=((1, 0, 0, 0), (0, 0, 0, 0)),
    )
    tibial = _profile(
        subject="tibial_cartilage",
        scope="object:tibial_cartilage",
        counts=((0, 1, 0, 0), (0, 0, 0, 0)),
    )

    ordered = compose_question_profile((femoral, tibial), question)
    permuted = compose_question_profile((tibial, femoral), question)
    evidence_swapped = compose_question_profile(
        (
            replace(femoral, bundle=tibial.bundle),
            replace(tibial, bundle=femoral.bundle),
        ),
        question,
    )

    assert ordered.bundle.layout.banks != ()
    assert all(bank.name.startswith("object/") for bank in ordered.bundle.layout.banks)
    assert ordered.bundle.counts == permuted.bundle.counts
    assert ordered.bundle.counts != evidence_swapped.bundle.counts


def test_proportional_counts_have_equal_cosine_and_do_not_encode_extent() -> None:
    unit = _profile(counts=((1, 0, 0, 0), (0, 0, 0, 0)))
    doubled = _profile(counts=((2, 0, 0, 0), (0, 0, 0, 0)))

    terms = cosine_terms(unit.bundle, doubled.bundle, ("signal",))

    assert terms.terms is not None
    # Cosine terms are proportional; counts alone carry no scale distinction.
    assert terms.terms.dot**2 == terms.terms.left_norm_sq * terms.terms.right_norm_sq


def test_teaching_keeps_labels_as_calls_not_count_rows() -> None:
    source = _profile(source_id="source:study-one")
    profiles = {"study-one": (source,)}
    positive, positive_receipt = teach_from_labels(
        profiles,
        {"study-one": {"ACL": 1}},
        revision="teach-r1",
    )
    negative, negative_receipt = teach_from_labels(
        profiles,
        {"study-one": {"ACL": 0}},
        revision="teach-r2",
    )

    assert positive.cases[0].profile.bundle.counts == source.bundle.counts
    assert negative.cases[0].profile.bundle.counts == source.bundle.counts
    assert positive.cases[0].calls[0].digit == 1
    assert negative.cases[0].calls[0].digit == -1
    assert positive_receipt != negative_receipt
