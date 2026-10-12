"""The twelve findings as named decisions, each on the subject the object model gives it.

THE PREDICATES stage (`knee.predicates`), task 4.1 of `every-stage-renders`. Its warrant is the
founder, 2026-10-11: *"A fracture isn't some vague line-y thing you look for in a whole
study/image--it's a break in the structural coherence of a 'bone' object."* So a finding is a
PREDICATE VIOLATION on a subject, never a pattern found in a field.

**What this build decides: nothing about a knee.** Every one of the twelve abstains, and the point
of the unit is that each abstains for the RIGHT REASON — the first thing actually missing, in the
order of causes. The dispatch answer recorded in `tasks.md` 4.1 says why, and it was corrected by
both second readers before a line was written:

  - **Findings 2-11 receive no subject at all.** `relations` returns `construction_absent`, so no
    interstice, span or envelope exists to be selected. That is a structural fact an earlier stage
    computed and reported in the shared absence vocabulary -- NOT a kind-label.
  - **Findings 0-1 DO have a candidate subject population**: the integer-indexed extents
    `read_ownership` resolves. Their subject is indefinite ("an object"), so they abstain for a
    different reason -- the predicate's FORM has not been given (`__init__.py` records the finer
    forms as the founder's to teach).

The lead's first answer said the missing selector *would be* femur/tibia identity. Both readers
independently found the same provable error: that contradicts the founder verbatim -- *"we don't
need to be able to link numbered objects to anatomical roles to do this"* -- and it smuggles the
kind-label framing back in as the GROUND of the refusal, which is the dispatch failure wearing the
costume of an answer to it. Readings: `chapters/02-collapse/readings/predicate-dispatch-*`.

**No anatomical name appears here, in the record OR in this code.** The founder's rule is that the
anatomy lives in the DESIGN and never in the record, and he includes code: writing a bone's name
into a stage's code is forbidden. A finding is keyed by INDEX and carries the STRUCTURAL
REQUIREMENT its subject must satisfy. The correspondence from index to the competition's column
names belongs to `knee.output`'s serialiser, where the foreign schema is met. Which index needs
which requirement is design knowledge, held deliberately, and it writes no anatomical word.

**No decided branch exists, and that is not a stub.** `e`, the expected correspondence, is
hand-given and has not been supplied, so the comparison has no declared correspondence to make.
Writing one would either invent a bar (law 4) or create a path the route never runs. Codex's limit
is recorded: author/date metadata establishes that a declaration EXISTS, it does not supply the
correspondence itself.

**This module reads no bar and carries no `ComputeContract`.** Every value `finding_code` inspects
is a fact a caller already established, so there is no threshold here to argue about later; and
there is no numeric kernel, hence no reference/twin pair and nothing for a contract to describe.

Record: `openspec/changes/every-stage-renders/specs/abstaining-findings/spec.md`, task 4.1.
"""

from __future__ import annotations

from dataclasses import dataclass

from knee.absence import absence_code
from knee.telemetry import ledger

#: How a requirement is satisfied: by a population an earlier stage resolved, or by a construction
#: it built. Not a bar -- the two words name which stage owns the subject's existence.
SATISFACTIONS: tuple[str, ...] = ("population", "construction")

#: Every code this unit admits. All nine are refusals or abstentions: none decides anything about a
#: knee, because no correspondence has been declared to decide against.
CODES: tuple[str, ...] = (
    "prior_outcome_refused",
    "invalid_request",
    "subject_population_empty",
    "subject_unconstructed",
    "subject_unresolved",
    "subjects_not_distinct",
    "form_not_given",
    "correspondence_undeclared",
    "reading_not_taken",
)

#: The structural requirement each finding's subject must satisfy, with the stage that owns its
#: existence and how many subjects the requirement names. Index only; no anatomical word. The
#: ordering is the competition's column order, and the mapping to those columns is `knee.output`'s.
REQUIREMENTS: tuple[tuple[int, str, str, int], ...] = (
    (0, "an object", "population", 1),
    (1, "an object", "population", 1),
    (2, "an interstice of a facing pair", "construction", 2),
    (3, "an interstice of a facing pair", "construction", 2),
    (4, "an interstice of a facing pair", "construction", 2),
    (5, "the content of an interstice", "construction", 2),
    (6, "the content of an interstice", "construction", 2),
    (7, "the content of an interstice", "construction", 2),
    (8, "a span attached to two objects", "construction", 2),
    (9, "an envelope", "construction", 2),
    (10, "the lining of an envelope", "construction", 2),
    (11, "an envelope", "construction", 2),
)

#: What each code says, so a reason reads as a sentence and the code and its words cannot drift.
#: Strings, never thresholds.
EXPLANATIONS: dict[str, str] = {
    "prior_outcome_refused": (
        "a gold label, a score or a previous outcome was offered to this decision and was refused"
    ),
    "invalid_request": "the request could not be read",
    "subject_population_empty": "no extent was resolved in any series of this study",
    "subject_unconstructed": "no such relation is constructed in this build",
    "subject_unresolved": "the relation is constructed but a subject of it is unresolved",
    "subjects_not_distinct": "the two subjects named are one and the same extent",
    "form_not_given": "the predicate's form on this subject has not been given",
    "correspondence_undeclared": "no expected correspondence has been declared for this predicate",
    "reading_not_taken": "this build takes no reading on this subject",
}


def finding_code(
    satisfied_by: str,
    subjects_required: int,
    first_subject: int,
    second_subject: int,
    relation_constructed: bool,
    subject_population: int,
    form_given: bool,
    correspondence_declared: bool,
    prior_outcome_offered: bool,
) -> str:
    """Name the first thing missing for one finding, in the order of causes.

    TOTAL over its arguments and it never raises. Every argument is a fact a caller established:
    `satisfied_by` and `subjects_required` come from this finding's declared requirement;
    `first_subject` and `second_subject` are integer extent indices with 0 meaning "none", and
    nothing here asks what either extent IS.

    **It reads a RELATION between its subjects, not a property of one** (capacity property 3). For
    a requirement naming two subjects it asks whether their relation is constructed, whether BOTH
    are resolved, and whether they are DISTINCT -- a pair of identical indices is one extent and not
    a relation at all, which no property of either subject could reveal.

    **`prior_outcome_offered` is refused FIRST, before validity.** An input that could only move a
    decision toward an answer already known is the graver violation, and reporting it first means no
    path exists on which such an input is read and then acted upon. The remedy differs from an
    unreadable request's -- "remove the label" against "fix the arguments" -- so they are two codes.

    The order after that is the order of causes: a requirement whose subject is not constructed says
    so and says nothing about resolution, because the remedies are opposite. `form_not_given`
    precedes `correspondence_undeclared` because a correspondence is declared FOR a form, so the
    form's absence makes the correspondence's absence unreportable rather than merely also true.

    `reading_not_taken` completes the function. It is reachable only when a subject exists, a form
    has been given and a correspondence declared -- none of which this build supplies -- and it says
    the honest remaining thing: the predicates stage measures nothing itself.

    post: __return__ in CODES
    post: not prior_outcome_offered or __return__ == "prior_outcome_refused"
    post: __return__ != "reading_not_taken" or (form_given and correspondence_declared)
    post: __return__ != "subjects_not_distinct" or first_subject == second_subject
    post: __return__ != "subject_population_empty" or satisfied_by == "population"
    post: __return__ != "subject_unconstructed" or satisfied_by == "construction"
    """
    if prior_outcome_offered:
        return "prior_outcome_refused"
    if satisfied_by not in SATISFACTIONS:
        return "invalid_request"
    if subjects_required not in (1, 2):
        return "invalid_request"
    if first_subject < 0 or second_subject < 0 or subject_population < 0:
        return "invalid_request"
    if satisfied_by == "population":
        if subject_population == 0:
            return "subject_population_empty"
    else:
        if not relation_constructed:
            return "subject_unconstructed"
        if first_subject == 0 or (subjects_required == 2 and second_subject == 0):
            return "subject_unresolved"
        if subjects_required == 2 and first_subject == second_subject:
            return "subjects_not_distinct"
    if not form_given:
        return "form_not_given"
    if not correspondence_declared:
        return "correspondence_undeclared"
    return "reading_not_taken"


def finding_reason(requirement: str, code: str) -> str:
    """One sentence: what this finding required, and what was missing.

    Composed rather than stored, so a code and its words cannot drift apart. An unknown code is
    named as unknown rather than silently given another code's sentence.

    post: requirement in __return__
    """
    explanation = EXPLANATIONS.get(code, "the code is not one this unit admits")
    return f"requires {requirement}; {explanation}"


@dataclass(frozen=True, slots=True)
class Finding:
    """One finding's standing: what it required, the code it returned, and why.

    `index` is the finding's position in the competition's column order and carries no name.
    `requirement` is structural. `code` is a member of `CODES`, never a number and never a
    probability -- a confidence is `knee.output`'s lossy projection of this record, never the
    reverse.
    """

    index: int
    requirement: str
    code: str
    reason: str


@dataclass(frozen=True, slots=True)
class FindingsReading:
    """The twelve, with the stage's own code naming what it had to work with.

    `code` comes from `knee.absence`: `present` when some series resolved a partition,
    `predecessor_absent` when no series reading was handed over at all. `findings` always holds
    TWELVE entries whatever the code -- a finding that could not be evaluated is an abstention with
    its reason, never a missing row. An absent row would let a consumer read silence as a negative.
    """

    code: str
    why: str
    findings: tuple[Finding, ...]
    series_with_population: int
    series_with_construction: int


def _series_facts(series: object) -> tuple[int, int, int]:
    """How many series resolved a partition, how many a construction, and how many were handed on.

    The third value is the ROW COUNT, or -1 when the argument is not iterable at all. Those are two
    different silences and the stage reports them as two: nothing handed over against a record that
    was handed over and held no series.

    Deliberately defensive, like `read_ownership`: the stage is total over anything, so a malformed
    row is read as contributing nothing rather than raising. `population` counts SERIES, never
    extents -- summing extents across planes would double-count one knee, and taking a maximum
    would discard the rest; neither is a fact anybody measured.
    """
    try:
        rows = tuple(series)  # type: ignore[call-overload]
    except TypeError:
        return 0, 0, -1
    population = 0
    construction = 0
    for row in rows:
        if getattr(getattr(row, "ownership", None), "code", "") == "present":
            population += 1
        relations_code = getattr(getattr(row, "relations", None), "code", "")
        if relations_code not in ("", "construction_absent"):
            construction += 1
    return population, construction, len(rows)


def _one_finding(
    index: int,
    requirement: str,
    satisfied_by: str,
    subjects_required: int,
    population: int,
    correspondence_declared: bool,
) -> Finding:
    """One finding's standing, from this study's subject facts.

    **The construction count is deliberately NOT a parameter here**, although the stage counts it
    and reports it. A per-study count of series that constructed *something*
    cannot tell finding 2's requirement (an interstice of a facing pair) from finding 9's (an
    envelope), so passing `construction > 0` would flip every construction-satisfied finding at
    once the moment relations built any one kind. Each would then reach the subject check with the
    0, 0 written below and come back `subject_unresolved` -- a wrong reason, and a substituted zero
    standing in for a reading nobody took, which `stage-totality` forbids.

    The two subject indices are 0 for the same reason: nothing is constructed, so there are no
    sides to name. `finding_code` reaches the construction check BEFORE it looks at them, which is
    what makes `subject_unconstructed` the honest answer rather than a claim about resolution.

    **When relations constructs, this function must take a PER-FINDING construction fact** -- which
    requirement was built, and the two extent indices that bound it -- and never a global flag.
    Recorded as an obligation on task 1.3a, and `test_a_global_construction_count_never_supplies_a
    _subject` is the must-not that refuses the shortcut in the meantime.
    """
    code = finding_code(
        satisfied_by=satisfied_by,
        subjects_required=subjects_required,
        first_subject=0,
        second_subject=0,
        relation_constructed=False,
        subject_population=population,
        form_given=False,
        correspondence_declared=correspondence_declared,
        prior_outcome_offered=False,
    )
    return Finding(
        index=index,
        requirement=requirement,
        code=code,
        reason=finding_reason(requirement, code),
    )


def read_findings(
    series: object, correspondence_declared: bool = False
) -> FindingsReading:
    """Evaluate the twelve over one study's series, each abstaining with its own reason.

    PER STUDY, not per series: a finding is a statement about the knee, and the series are the
    acquisitions it was read from. The subject facts are aggregated over the series first.

    Total over `series`: `None`, an empty tuple and a malformed object all return twelve
    abstentions, with the stage's code naming which silence it met.

    `correspondence_declared` defaults to False because `e` is hand-given and has not been supplied.
    The stage never manufactures it; a caller that one day declares one passes it here, with its
    author and date recorded where it is declared.

    This stage REFUSES a gold label or a prior score structurally: no parameter admits one, and
    `finding_code` refuses one on its first branch for a caller that reaches the decision directly.

    post: len(__return__.findings) == 12
    post: all(f.code in CODES for f in __return__.findings)
    post: __return__.code in ("present", "predecessor_absent", "predecessor_empty")
    """
    population, construction, rows = _series_facts(series)
    code = absence_code(
        construction_built=True,
        predecessor_returned=rows >= 0,
        # Unread when `rows` is -1, because `predecessor_returned` is then False and
        # `absence_code` answers before it reaches this argument.
        item_count=max(rows, 0),
        item_read=True,
    )
    findings = tuple(
        _one_finding(
            index,
            requirement,
            satisfied_by,
            subjects_required,
            population,
            correspondence_declared,
        )
        for index, requirement, satisfied_by, subjects_required in REQUIREMENTS
    )
    ledger.record("predicates.produced", findings=len(findings))
    if rows < 0:
        why = "no series reading was handed to this stage"
    elif rows == 0:
        why = "a series reading was handed over and it held no series"
    else:
        why = (
            f"{population} of {rows} series resolved a partition; "
            f"{construction} resolved a construction"
        )
    return FindingsReading(
        code=code,
        why=why,
        findings=findings,
        series_with_population=population,
        series_with_construction=construction,
    )
