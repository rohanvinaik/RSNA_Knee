"""How voices compete inside a condition finding, and what reaches the competition output.

Rohan, 2026-10-21: «Let warranted configuration recall decide» — an explicit
decision on the recall consumer, never a lesion-count threshold. Around it the
written contract (docs/SQUINT_PRODUCTION_CONTRACT.md, SQUINT_TRAINING_BUILD §4
and §10) keeps four limits, and these tests pin each one with both signs:

* an explicitly marked ``decision_scope="grade_only"`` voice contributes its
  comparisons to ranking but has no authority to assign, defeat or veto;
* "conflicting warranted configuration/anatomical evidence stays open": a normal
  reading of a site the matched configuration compared opposes it, yet "one
  normal bone still cannot rule out another site", so it never defeats alone;
* an explicit local positive at one site is its own warrant: a normal reading at
  another site neither erases nor vetoes it;
* supporting tissue is context: "it cannot substitute for unread defining
  tissue", so a normal context reading, or a configuration case that compared
  only context, can neither decide nor oppose.

Nothing is a cutoff: a decision never depends on how close a cosine is, and the
number that reaches the competition is only the fixed serialization
``p = (3*r + 1 + e) / 9`` of the tier and the exact signed cosines.

Every test builds its evidence by hand in the public ``recall`` row convention
(``case_terms`` rows with ``case_id``, ``call``, ``terms = {dot, left_norm_sq,
right_norm_sq}`` and the banks they spoke through) and calls ``combine_condition``
directly. A test that fails on the current contract is an honest statement of
what the contract owes; none is marked as expected to fail.
"""

from __future__ import annotations

import csv
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from knee.diagnosis.squint_contracts import combine_condition
from knee.diagnosis.squint_interfaces import territory_bank_name
from knee.diagnosis.submission import (
    SUBMISSION_COLUMNS,
    validate_submission,
    write_submission,
)
from knee.study.tables import LABELS

TIER = {"defeated": 0, "open": 1, "assigned": 2}
INTERVAL = {
    "defeated": (Fraction(1, 9), Fraction(2, 9)),
    "open": (Fraction(4, 9), Fraction(5, 9)),
    "assigned": (Fraction(7, 9), Fraction(8, 9)),
}

# The anatomical roles of the declared contracts (docs/OBJECTS_AND_CONDITIONS.md,
# squint_contracts): which tissue defines a condition, and which only surrounds it.
DEFINING = {
    "ACL": ("acl",),
    "Medial Meniscus": ("medial_meniscus",),
    "Effusion": ("joint_fluid", "anterior_synovial_recess"),
    "Fracture": ("femur", "tibia", "patella", "fibula"),
    "Contusion": ("femur", "tibia", "patella"),
    "Medial OA": (
        "femur",
        "tibia",
        "femoral_cartilage",
        "tibial_cartilage",
        "medial_meniscus",
    ),
    "PF OA": ("patella", "femur", "patellar_cartilage", "trochlear_cartilage"),
}
CONTEXT = {
    "ACL": ("femur", "tibia", "pcl"),
    "Medial Meniscus": ("femur", "tibia", "joint"),
    "Effusion": ("joint", "joint_capsule", "quadriceps_fat_pad", "prefemoral_fat_pad"),
    "Medial OA": ("joint",),
}


# ---------------------------------------------------------------------------
# builders
# ---------------------------------------------------------------------------


def _row(
    case_id: str,
    call: int,
    banks: tuple[str, ...] = ("bank",),
    *,
    k: int = 1,
    m: int = 2,
    scope: str | None = None,
) -> dict:
    """A sourced-trust case row whose squared cosine is exactly (k/m)**2."""
    row = {
        "case_id": case_id,
        "call": call,
        "terms": {"dot": k, "left_norm_sq": m, "right_norm_sq": m},
        "common_speaking_banks": list(banks),
        "trust": {"numerator": 1, "denominator": 2, "source": "sourced-envelope"},
        "reaches_trust": True,
    }
    if scope is not None:
        row["call_scope"] = scope
    return row


def _voice(outcome: str, *rows: dict, **extra: object) -> dict:
    return {"outcome": outcome, "case_terms": list(rows), "vetoed_answers": [], **extra}


def _normal(site: str, *, k: int = 1, m: int = 2) -> dict:
    """A warranted normal reading of one object for the question."""
    return _voice("absent", _row(f"{site}-normal", -1, (f"{site}-bank",), k=k, m=m))


def _positive(site: str, *, scope: str | None = None, k: int = 1, m: int = 2) -> dict:
    """A warranted positive reading of one object for the question."""
    row = _row(f"{site}-positive", 1, (f"{site}-bank",), k=k, m=m, scope=scope)
    return _voice("present", row)


def _covering(
    case_id: str, call: int, subjects: tuple[str, ...], *, k: int = 1, m: int = 2
) -> dict:
    """A whole-case row that compared exactly the named object roles."""
    measured_bank = territory_bank_name(
        {
            "orientation": "Sagittal",
            "fluid_sensitive": "0",
            "fat_suppression": "0",
        },
        "object",
        "signal_median",
        "overview",
        10.0,
    )
    banks = tuple(f"object/{subject}/{measured_bank}" for subject in subjects)
    return _row(case_id, call, banks, k=k, m=m)


def _configuration(
    call: int,
    subjects: tuple[str, ...],
    *,
    scope: str | None = None,
    k: int = 1,
    m: int = 2,
) -> dict:
    """A warranted whole-condition recall voice that compared the named roles."""
    case_id = "config-pos" if call == 1 else "config-neg"
    row = _covering(case_id, call, subjects, k=k, m=m)
    extra = {} if scope is None else {"decision_scope": scope}
    return _voice("present" if call == 1 else "absent", row, **extra)


def _key(question: str) -> str:
    return f"diagnosis/{question}"


def _fraction(record: dict) -> Fraction:
    return Fraction(int(record["numerator"]), int(record["denominator"]))


def _sq(row: dict) -> Fraction:
    terms = row["terms"]
    return Fraction(terms["dot"] ** 2, terms["left_norm_sq"] * terms["right_norm_sq"])


# ---------------------------------------------------------------------------
# a configuration that was read as grade-only grades; it never decides or vetoes
# ---------------------------------------------------------------------------

GRADE_ONLY_CASES = [
    ("ACL", 1, DEFINING["ACL"]),
    ("ACL", -1, DEFINING["ACL"]),
    ("Medial Meniscus", 1, DEFINING["Medial Meniscus"]),
    ("Medial Meniscus", -1, DEFINING["Medial Meniscus"]),
    ("Effusion", 1, ("joint_fluid",)),
    ("Effusion", -1, DEFINING["Effusion"]),
    ("Fracture", 1, ("femur",)),
    ("Fracture", -1, DEFINING["Fracture"]),
    ("Medial OA", -1, DEFINING["Medial OA"]),
]


@pytest.mark.parametrize(
    ("question", "call", "covered"),
    GRADE_ONLY_CASES,
    ids=[f"{q}:{'+' if c == 1 else '-'}" for q, c, _ in GRADE_ONLY_CASES],
)
def test_grade_only_configuration_grades_but_never_decides(
    question: str, call: int, covered: tuple[str, ...]
) -> None:
    """The same covered, warranted configuration decides under ``decide`` and only
    grades under ``grade_only``; the grade it carries is identical in both."""
    key = _key(question)
    decided = combine_condition(
        question, {key: _configuration(call, covered, scope="decide")}
    )
    graded = combine_condition(
        question, {key: _configuration(call, covered, scope="grade_only")}
    )

    # sign one: the evidence is covered and warranted, so it can decide
    assert decided["outcome"] == ("assigned" if call == 1 else "defeated")
    assert decided["evidence"]["decided_by"] == [key]
    # sign two: read as grade-only it holds no authority to assign or defeat
    assert graded["outcome"] == "open", (graded["outcome"], graded["reason"])
    assert graded["evidence"]["decided_by"] == []
    assert graded["rank"]["tier"] == "open"
    # it is graded, not discarded: the exact support terms are those of the
    # deciding twin, and only the tier moves
    for field in ("s_plus", "s_minus", "e"):
        assert graded["rank"][field] == decided["rank"][field]
    moved = _fraction(graded["rank"]["exact"]) - _fraction(decided["rank"]["exact"])
    assert moved == (Fraction(-1, 3) if call == 1 else Fraction(1, 3))


VETO_CASES = [
    ("ACL", "acl", DEFINING["ACL"]),
    ("Fracture", "femur", DEFINING["Fracture"]),
    ("Effusion", "joint_fluid", DEFINING["Effusion"]),
]


@pytest.mark.parametrize(
    ("question", "site", "covered"), VETO_CASES, ids=[case[0] for case in VETO_CASES]
)
def test_grade_only_configuration_cannot_veto_a_decisive_anatomical_reading(
    question: str, site: str, covered: tuple[str, ...]
) -> None:
    """Only warranted configuration evidence can conflict with anatomy. A negative
    configuration with authority stops an explicit positive at ``open``; the same
    negative read as grade-only is not warranted, so the anatomy still decides."""
    key = _key(question)
    positive = _positive(site)
    warranted = combine_condition(
        question,
        {site: positive, key: _configuration(-1, covered, scope="decide")},
    )
    graded = combine_condition(
        question,
        {site: positive, key: _configuration(-1, covered, scope="grade_only")},
    )

    assert warranted["outcome"] == "open", (warranted["outcome"], warranted["reason"])
    assert graded["outcome"] == "assigned", (graded["outcome"], graded["reason"])
    assert graded["evidence"]["decided_by"] == [site]
    # the grade-only disagreement is kept for ranking, not hidden
    assert graded["rank"]["negative_case_ids"] == ["config-neg"]
    assert graded["rank"]["positive_case_ids"] == [f"{site}-positive"]


# ---------------------------------------------------------------------------
# a normal reading opposes a matched configuration, but one site never rules out all
# ---------------------------------------------------------------------------

PARTIAL_NORMAL = [
    ("Fracture", ("femur", "tibia"), "femur"),
    ("Contusion", ("femur", "patella"), "patella"),
    ("Effusion", ("joint_fluid",), "joint_fluid"),
    ("Medial OA", ("femur", "tibia"), "tibia"),
    ("PF OA", ("patella", "femur"), "femur"),
]


@pytest.mark.parametrize(
    ("question", "covered", "normal_site"),
    PARTIAL_NORMAL,
    ids=[f"{q}:{site}" for q, _, site in PARTIAL_NORMAL],
)
def test_partial_normal_opposes_a_matched_configuration_without_ruling_out_all_sites(
    question: str, covered: tuple[str, ...], normal_site: str
) -> None:
    """A warranted normal at one site the matched case compared is not nothing:
    the configuration may not assign over it. It is not everything either: the
    other sites stay unobserved, so the condition is open, never defeated."""
    key = _key(question)
    matched = _configuration(1, covered)
    alone = combine_condition(question, {key: matched})
    normal_alone = combine_condition(question, {normal_site: _normal(normal_site)})
    opposed = combine_condition(
        question, {key: matched, normal_site: _normal(normal_site)}
    )

    # control one: with nothing against it the covered configuration decides
    assert alone["outcome"] == "assigned"
    assert alone["evidence"]["decided_by"] == [key]
    # control two: that normal reading cannot rule out the condition by itself
    assert normal_alone["outcome"] == "open"
    assert normal_alone["evidence"]["decided_by"] == []
    # together they oppose: neither assigned over the normal nor defeated by it
    assert opposed["outcome"] == "open", (opposed["outcome"], opposed["reason"])
    assert opposed["evidence"]["decided_by"] == []
    assert opposed["rank"]["tier"] == "open"
    # and the disagreement stays in the finding rather than being resolved away
    assert opposed["evidence"]["readings"][normal_site]["state"] == "negative"
    assert opposed["rank"]["positive_case_ids"] == ["config-pos"]
    assert opposed["rank"]["negative_case_ids"] == [f"{normal_site}-normal"]


@pytest.mark.parametrize(
    "question", ["Fracture", "Effusion", "Medial OA"], ids=lambda name: name
)
def test_every_site_normal_beside_a_matched_positive_configuration_stays_open(
    question: str,
) -> None:
    """Both warranted voices stand and disagree: not assigned, not defeated."""
    sites = DEFINING[question]
    result = combine_condition(
        question,
        {
            _key(question): _configuration(1, sites[:1]),
            **{site: _normal(site) for site in sites},
        },
    )
    assert result["outcome"] == "open", (result["outcome"], result["reason"])
    assert result["evidence"]["decided_by"] == []
    assert {state["state"] for state in result["evidence"]["readings"].values()} >= {
        "negative"
    }
    assert result["rank"]["positive_case_ids"] == ["config-pos"]


# ---------------------------------------------------------------------------
# an explicit local positive is its own warrant
# ---------------------------------------------------------------------------

LOCAL_POSITIVE = [
    ("Fracture", "femur", "tibia"),
    ("Fracture", "fibula", "femur"),
    ("Contusion", "tibia", "patella"),
    ("Effusion", "joint_fluid", "anterior_synovial_recess"),
]


@pytest.mark.parametrize(
    ("question", "site_a", "site_b"),
    LOCAL_POSITIVE,
    ids=[f"{q}:{a}+{b}" for q, a, b in LOCAL_POSITIVE],
)
def test_an_explicit_local_positive_is_not_vetoed_by_a_normal_at_another_site(
    question: str, site_a: str, site_b: str
) -> None:
    key = _key(question)
    normal_b = _normal(site_b)
    plain = combine_condition(question, {site_a: _positive(site_a), site_b: normal_b})
    # the normal is neither erased nor allowed to veto
    assert plain["outcome"] == "assigned"
    assert plain["evidence"]["decided_by"] == [site_a]
    assert plain["evidence"]["readings"][site_b]["state"] == "negative"
    # a matched whole-case configuration that compared both sites is opposed by
    # that normal; the explicit positive beside it still stands on its own
    with_configuration = combine_condition(
        question,
        {
            site_a: _positive(site_a),
            site_b: normal_b,
            key: _configuration(1, (site_a, site_b)),
        },
    )
    assert with_configuration["outcome"] == "assigned", (
        with_configuration["outcome"],
        with_configuration["reason"],
    )
    assert with_configuration["evidence"]["readings"][site_a]["state"] == "positive"


@pytest.mark.parametrize(
    ("question", "site_a", "site_b"),
    [("Fracture", "femur", "tibia"), ("Contusion", "tibia", "patella")],
)
def test_a_study_level_presentation_is_not_an_explicit_local_positive(
    question: str, site_a: str, site_b: str
) -> None:
    """The control for the test above: the same trusted positive case, carrying
    the study-level scope the compiler writes, localizes nothing and so decides
    nothing; it is the explicit local reading that carries authority."""
    presentation = _positive(site_a, scope="positive_condition_presentation")
    result = combine_condition(
        question, {site_a: presentation, site_b: _normal(site_b)}
    )
    explicit = combine_condition(
        question, {site_a: _positive(site_a), site_b: _normal(site_b)}
    )
    assert explicit["outcome"] == "assigned"
    assert result["outcome"] == "open"
    reading = result["evidence"]["readings"][site_a]
    assert reading["code"] == "study_positive_presentation_not_localized"
    assert result["rank"]["positive_case_ids"] == [f"{site_a}-positive"]


@pytest.mark.parametrize(
    ("question", "site"), [("Fracture", "femur"), ("Effusion", "joint_fluid")]
)
def test_a_covered_negative_configuration_stops_an_explicit_positive_at_open(
    question: str, site: str
) -> None:
    """Warranted voices that disagree stay open; neither silently wins."""
    result = combine_condition(
        question,
        {
            site: _positive(site),
            _key(question): _configuration(-1, DEFINING[question]),
        },
    )
    assert result["outcome"] == "open", (result["outcome"], result["reason"])
    assert result["evidence"]["decided_by"] == []
    assert result["rank"]["positive_case_ids"] == [f"{site}-positive"]
    assert result["rank"]["negative_case_ids"] == ["config-neg"]


# ---------------------------------------------------------------------------
# context cannot speak
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("question", sorted(CONTEXT))
def test_a_normal_context_tissue_cannot_defeat_assign_or_oppose(question: str) -> None:
    key = _key(question)
    defining = DEFINING[question]
    context_normal = {name: _normal(name) for name in CONTEXT[question]}

    silent = combine_condition(question, dict(context_normal))
    matched = combine_condition(
        question, {**context_normal, key: _configuration(1, defining[:1])}
    )
    own_tissue = combine_condition(
        question, {**context_normal, **{name: _normal(name) for name in defining}}
    )

    # it cannot defeat or assign while the defining tissue is unread
    assert silent["outcome"] == "open"
    assert silent["evidence"]["decided_by"] == []
    # it cannot oppose a matched configuration of the defining tissue
    assert matched["outcome"] == "assigned", (matched["outcome"], matched["reason"])
    assert matched["evidence"]["decided_by"] == [key]
    # control: normal readings of the defining tissue itself do speak
    assert own_tissue["outcome"] == "defeated"
    assert set(own_tissue["evidence"]["decided_by"]) == set(defining)


@pytest.mark.parametrize("question", sorted(CONTEXT))
def test_a_configuration_case_that_compared_only_context_cannot_speak(
    question: str,
) -> None:
    key = _key(question)
    context = CONTEXT[question]
    positive = _covering("context-pos", 1, context)
    negative = _covering("context-neg", -1, context)

    only_context = combine_condition(
        question, {key: _voice("unresolved_conflict", positive, negative)}
    )
    assert only_context["outcome"] == "open"
    assert only_context["evidence"]["decided_by"] == []
    # each comparison still grades the open band
    assert only_context["rank"]["positive_case_ids"] == ["context-pos"]
    assert only_context["rank"]["negative_case_ids"] == ["context-neg"]

    # and it creates no categorical conflict: beside a case that compared the
    # defining tissue, that case still decides
    own = _covering("own-pos", 1, DEFINING[question][:1])
    beside = combine_condition(
        question, {key: _voice("unresolved_conflict", own, negative)}
    )
    assert beside["outcome"] == "assigned", (beside["outcome"], beside["reason"])
    assert beside["rank"]["negative_case_ids"] == ["context-neg"]


# ---------------------------------------------------------------------------
# no cutoff and no new readout
# ---------------------------------------------------------------------------

MAGNITUDES = [(1, 1000), (1, 10), (1, 2), (9, 10), (1, 1)]


def _scenarios(k: int, m: int) -> dict[str, tuple[str, dict]]:
    """Voices whose supporting cosine is (k/m)**2, one per kind of decision."""
    fracture = _key("Fracture")
    return {
        "object_positive": ("ACL", {"acl": _positive("acl", k=k, m=m)}),
        "object_negative": ("ACL", {"acl": _normal("acl", k=k, m=m)}),
        "matched_configuration": (
            "Fracture",
            {fracture: _configuration(1, ("femur",), k=k, m=m)},
        ),
        "negative_configuration": (
            "Fracture",
            {fracture: _configuration(-1, DEFINING["Fracture"], k=k, m=m)},
        ),
        "partial_normal_opposing": (
            "Fracture",
            {
                fracture: _configuration(1, ("femur", "tibia"), k=k, m=m),
                "femur": _normal("femur", k=k, m=m),
            },
        ),
        "grade_only_configuration": (
            "Fracture",
            {fracture: _configuration(1, ("femur",), scope="grade_only", k=k, m=m)},
        ),
        "explicit_local_positive": (
            "Fracture",
            {
                "femur": _positive("femur", k=k, m=m),
                "tibia": _normal("tibia", k=k, m=m),
            },
        ),
    }


@pytest.mark.parametrize("kind", sorted(_scenarios(1, 2)))
def test_a_decision_never_depends_on_how_close_the_cosine_is(kind: str) -> None:
    """Trust is already settled by the source-backed envelope each case reached; the
    contract adds no cutoff of its own. Whatever a scenario decides, it decides
    identically from a cosine near zero to exactly one, and only the grade moves
    inside the tier."""
    results = []
    for k, m in MAGNITUDES:
        question, evidence = _scenarios(k, m)[kind]
        results.append(combine_condition(question, evidence))

    assert len({item["outcome"] for item in results}) == 1
    assert len({item["reason"] for item in results}) == 1
    assert len({tuple(item["evidence"]["decided_by"]) for item in results}) == 1
    for item in results:
        low, high = INTERVAL[item["outcome"]]
        assert low <= _fraction(item["rank"]["exact"]) <= high
        assert 0.0 < item["probability"] < 1.0


@pytest.mark.parametrize("kind", sorted(_scenarios(1, 2)))
def test_the_value_is_only_the_fixed_serialization_of_tier_and_exact_cosines(
    kind: str,
) -> None:
    """Whatever the finding decides, its value is (3r+1+e)/9 with ``r`` its tier and
    ``e = (1 + best positive - best negative) / 2`` over the case rows that graded;
    a loud supporting voice adds nothing and no other readout appears."""
    question, evidence = _scenarios(3, 4)[kind]
    loud_context = _voice(
        "present", _row("context-loud", 1, ("context-bank",), k=1, m=1)
    )
    context = {name: loud_context for name in CONTEXT.get(question, ())}
    result = combine_condition(question, {**evidence, **context})

    grading = [
        row
        for name, voice in evidence.items()
        if name in DEFINING[question] or name == _key(question)
        for row in voice["case_terms"]
    ]
    s_plus = max((_sq(row) for row in grading if row["call"] == 1), default=Fraction(0))
    s_minus = max(
        (_sq(row) for row in grading if row["call"] == -1), default=Fraction(0)
    )
    grade = (1 + s_plus - s_minus) / 2
    expected = (Fraction(3 * TIER[result["outcome"]] + 1) + grade) / 9

    assert result["rank"]["tier"] == result["outcome"]
    assert _fraction(result["rank"]["exact"]) == expected
    assert result["probability"] == result["rank"]["value"] == float(expected)
    assert result["rank"]["formula"] == "p=(3*r+1+e)/9"


# ---------------------------------------------------------------------------
# what reaches the competition output
# ---------------------------------------------------------------------------


def _study_values(evidence: dict[str, dict[str, dict]]) -> dict[str, float]:
    """One study's twelve competition values, each its own finding's rank value."""
    return {
        question: combine_condition(question, evidence.get(question, {}))["rank"][
            "value"
        ]
        for question in LABELS
    }


def _written(tmp_path: Path, studies: dict[str, dict[str, float]]) -> dict:
    template = tmp_path / "template.csv"
    with template.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(SUBMISSION_COLUMNS)
        for uid in studies:
            writer.writerow((uid, *("0" for _ in LABELS)))
    output = tmp_path / "submission.csv"
    write_submission(
        template,
        output,
        list(studies.items()),
        source_provenance={"source": "synthetic findings"},
    )
    validate_submission(template, output)
    with output.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.reader(stream))
    assert tuple(rows[0]) == SUBMISSION_COLUMNS
    return {row[0]: dict(zip(LABELS, row[1:], strict=True)) for row in rows[1:]}


def test_findings_reach_the_competition_csv_in_the_tier_they_decided(
    tmp_path: Path,
) -> None:
    """Twelve ordered columns, each strictly inside (0, 1), and the tier a finding
    decided is the band its competition value lies in: a configuration that only
    grades reaches the output as an open grade, never as an assignment."""
    fracture = _key("Fracture")
    configuration = {
        "Fracture": {fracture: _configuration(1, ("femur",), scope="decide")}
    }
    graded = {"Fracture": {fracture: _configuration(1, ("femur",), scope="grade_only")}}
    studies = {
        "decided": _study_values(configuration),
        "graded": _study_values(graded),
        "unread": _study_values({}),
    }
    written = _written(tmp_path, studies)

    assert tuple(LABELS) == SUBMISSION_COLUMNS[1:]
    for uid, values in studies.items():
        for question in LABELS:
            cell = Decimal(written[uid][question])
            assert Decimal(0) < cell < Decimal(1)
            assert cell == Decimal(str(values[question]))
    # a study nothing was read for is the neutral open grade in every column
    assert {Decimal(cell) for cell in written["unread"].values()} == {Decimal("0.5")}
    # sign one: the covered, deciding configuration lands in the assigned band
    low, high = INTERVAL["assigned"]
    assert low <= Fraction(written["decided"]["Fracture"]) <= high
    # sign two: the same evidence read as grade-only lands in the open band
    low, high = INTERVAL["open"]
    assert low <= Fraction(written["graded"]["Fracture"]) <= high
    # the other eleven conditions were untouched by either
    for question in LABELS:
        if question != "Fracture":
            assert written["decided"][question] == written["graded"][question]
