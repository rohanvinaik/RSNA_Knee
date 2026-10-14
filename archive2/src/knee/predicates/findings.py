"""The twelve findings as named decisions, each on the subject the object model gives it.

THE PREDICATES stage (`knee.predicates`), tasks 4.1 and 6.4 of `every-stage-renders`. Its warrant
is the founder, 2026-10-11: *"A fracture isn't some vague line-y thing you look for in a whole
study/image--it's a break in the structural coherence of a 'bone' object."* So a finding is a
PREDICATE VIOLATION on a subject, never a pattern found in a field.

**What this build decides: nothing about a knee.** Every one of the twelve abstains, and the point
of the unit is that each abstains for the RIGHT REASON -- the first thing actually missing, in the
order of causes, READ from the records of the stages below and never hardcoded:

  - **Findings 2-11 take a construction.** Each names the structural KIND it requires (a facing
    pair's interstice, its content, a span, the envelope, its lining -- `knee.relations.KINDS`),
    and reads the study's `Interstice` records of that kind from every series' relations record.
    None constructed → `subject_unconstructed`. Exactly one → its two indexed extents are the
    subjects. Several → `dispatch_undeclared`: the rule choosing WHICH construction is this
    finding's subject (medial against lateral, one series' pair against another's) is the
    founder's, task 4.1, and this unit refuses to guess it. Until 2026-10-12 this function wrote
    `relation_constructed=False` and two zero indices into every call; the Codex reading of the
    handoff named that as the defect ("Each finding needs its actual subject and measurement
    records supplied explicitly"), and task 6.4 removed it.
  - **Findings 0-1 take a population**: the integer-indexed extents `read_ownership` resolves.
    Their subject is indefinite ("an object"), so they abstain for a different reason -- the
    predicate's FORM has not been given (`__init__.py` records the finer forms as the founder's
    to teach).

The lead's first answer said the missing selector *would be* femur/tibia identity. Both readers
independently found the same provable error: that contradicts the founder verbatim -- *"we don't
need to be able to link numbered objects to anatomical roles to do this"* -- and it smuggles the
kind-label framing back in as the GROUND of the refusal. Readings:
`chapters/02-collapse/readings/predicate-dispatch-*`.

**No anatomical name appears here, in the record OR in this code.** A finding is keyed by INDEX
and carries the STRUCTURAL REQUIREMENT its subject must satisfy. `REQUIREMENTS` is in the object
model's table order (`docs/OBJECT_MODEL.md`, "The twelve findings as predicates"), which is NOT
the competition's column order; the correspondence from index to the competition's column names
belongs to `knee.output`, where the foreign schema is met, and it is declared and checked there.

**No decided branch exists, and that is not a stub.** `e`, the expected correspondence, is
hand-given and has not been supplied, so the comparison has no declared correspondence to make.
Writing one would either invent a bar (law 4) or create a path the route never runs.

**This module reads no bar and carries no `ComputeContract`.** Every value `finding_code` inspects
is a fact a caller already established, and there is no numeric kernel here.

Record: `openspec/changes/every-stage-renders/specs/abstaining-findings/spec.md` and
`specs/route-composition/spec.md`, tasks 4.1 and 6.4.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from knee.absence import absence_code
from knee.relations.shell import Interstice
from knee.telemetry import ledger

#: How a requirement is satisfied: by a population an earlier stage resolved, or by a construction
#: it built. Not a bar -- the two words name which stage owns the subject's existence.
SATISFACTIONS: tuple[str, ...] = ("population", "construction")

#: Every code this unit admits. All ten are refusals or abstentions: none decides anything about a
#: knee, because no correspondence has been declared to decide against.
CODES: tuple[str, ...] = (
    "prior_outcome_refused",
    "invalid_request",
    "subject_population_empty",
    "subject_unconstructed",
    "dispatch_undeclared",
    "subject_unresolved",
    "subjects_not_distinct",
    "form_not_given",
    "correspondence_undeclared",
    "reading_not_taken",
)

#: The structural requirement each finding's subject must satisfy, the stage that owns its
#: existence, how many subjects it names, and the KIND of construction it selects from. Index
#: only; no anatomical word. The order is the object model's table order; the mapping to the
#: competition's columns is `knee.output`'s. `object` is the kind of a population requirement
#: and is never looked up among constructions.
REQUIREMENTS: tuple[tuple[int, str, str, int, str], ...] = (
    (0, "an object", "population", 1, "object"),
    (1, "an object", "population", 1, "object"),
    (2, "an interstice of a facing pair", "construction", 2, "facing_pair"),
    (3, "an interstice of a facing pair", "construction", 2, "facing_pair"),
    (4, "an interstice of a facing pair", "construction", 2, "facing_pair"),
    (5, "the content of an interstice", "construction", 2, "content"),
    (6, "the content of an interstice", "construction", 2, "content"),
    (7, "the content of an interstice", "construction", 2, "content"),
    (8, "a span attached to two objects", "construction", 2, "span"),
    (9, "an envelope", "construction", 2, "envelope"),
    (10, "the lining of an envelope", "construction", 2, "lining"),
    (11, "an envelope", "construction", 2, "envelope"),
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
    "dispatch_undeclared": (
        "several constructions of the required kind exist and the rule selecting this "
        "finding's subject among them has not been given"
    ),
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
    candidates: int,
    subject_population: int,
    form_given: bool,
    correspondence_declared: bool,
    prior_outcome_offered: bool,
) -> str:
    """Name the first thing missing for one finding, in the order of causes.

    TOTAL over its arguments and it never raises. Every argument is a fact a caller established:
    `satisfied_by` and `subjects_required` come from this finding's declared requirement;
    `candidates` is how many constructions of the required kind the relations records hold for
    this study; `first_subject` and `second_subject` are the integer extent indices of the one
    candidate when there is exactly one, with 0 meaning "none"; and nothing here asks what either
    extent IS.

    **It reads a RELATION between its subjects, not a property of one.** For a requirement naming
    two subjects it asks whether their relation is constructed, whether BOTH are resolved, and
    whether they are DISTINCT -- a pair of identical indices is one extent and not a relation at
    all. Findings whose subject the object model gives as a single object (a population
    requirement) read that object's population and are not asked for a relation: the founder's
    own sentence makes a fracture a predicate on one object.

    **`prior_outcome_offered` is refused FIRST, before validity.** An input that could only move a
    decision toward an answer already known is the graver violation, and reporting it first means
    no path exists on which such an input is read and then acted upon.

    The order after that is the order of causes. `subject_unconstructed` says nothing about
    resolution, because the remedies are opposite. `dispatch_undeclared` precedes every subject
    check because with several candidates there IS no first and second subject to check: the
    choice among them is a rule the founder has not given, and reading one of them would be
    guessing it. `form_not_given` precedes `correspondence_undeclared` because a correspondence is
    declared FOR a form.

    `reading_not_taken` completes the function. It is reachable only when a subject exists, a form
    has been given and a correspondence declared -- none of which this build supplies.

    post: __return__ in CODES
    post: not prior_outcome_offered or __return__ == "prior_outcome_refused"
    post: __return__ != "reading_not_taken" or (form_given and correspondence_declared)
    post: __return__ != "subjects_not_distinct" or first_subject == second_subject
    post: __return__ != "subject_population_empty" or satisfied_by == "population"
    post: __return__ != "subject_unconstructed" or (satisfied_by == "construction" and candidates == 0)
    post: __return__ != "dispatch_undeclared" or (satisfied_by == "construction" and candidates > 1)
    """
    if prior_outcome_offered:
        return "prior_outcome_refused"
    if satisfied_by not in SATISFACTIONS:
        return "invalid_request"
    if subjects_required not in (1, 2):
        return "invalid_request"
    if (
        first_subject < 0
        or second_subject < 0
        or subject_population < 0
        or candidates < 0
    ):
        return "invalid_request"
    if satisfied_by == "population":
        if subject_population == 0:
            return "subject_population_empty"
    else:
        if candidates == 0:
            return "subject_unconstructed"
        if candidates > 1:
            return "dispatch_undeclared"
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
    """One finding's standing: what it required, what it read, the code it returned, and why.

    `index` is the finding's position in the object model's table and carries no name.
    `requirement` is structural. `subjects` are the two indexed extents the finding read when
    exactly one construction of its kind existed, else (0, 0); `candidates` is how many it found.
    `code` is a member of `CODES`, never a number and never a probability -- a confidence is
    `knee.output`'s lossy projection of this record, never the reverse.
    """

    index: int
    requirement: str
    code: str
    reason: str
    subjects: tuple[int, int] = (0, 0)
    candidates: int = 0
    profiles: int = 0


@dataclass(frozen=True, slots=True)
class FindingsReading:
    """The twelve, with the stage's own code naming what it had to work with.

    `code` comes from `knee.absence`: `present` when some series resolved a partition,
    `predecessor_absent` when no series reading was handed over at all. `findings` always holds
    TWELVE entries whatever the code -- a finding that could not be evaluated is an abstention with
    its reason, never a missing row. An absent row would let a consumer read silence as a negative.

    `series_with_profiles` counts the series whose bundles stage wrote at least one profile: the
    reading a population finding's form would be read against, once that form is given.
    """

    code: str
    why: str
    findings: tuple[Finding, ...]
    series_with_population: int
    series_with_construction: int
    series_with_profiles: int = 0


@dataclass(frozen=True, slots=True)
class _Facts:
    """What the series handed over, aggregated once per study."""

    population: int
    construction: int
    rows: int
    constructions: tuple[Interstice, ...]
    series_with_profiles: int
    profiles: int


def _series_facts(series: object) -> _Facts:
    """What the series handed over: partitions, constructions, profiles, and the row count.

    `rows` is the ROW COUNT, or -1 when the argument is not iterable at all. Those are two
    different silences and the stage reports them as two: nothing handed over against a record
    that was handed over and held no series.

    Deliberately defensive, like `read_ownership`: the stage is total over anything, so a
    malformed row is read as contributing nothing rather than raising. `population` counts SERIES,
    never extents -- summing extents across planes would double-count one knee, and taking a
    maximum would discard the rest; neither is a fact anybody measured. The constructions are read
    off each row's relations record and kept whole, so a finding selects from what the relations
    stage actually built and never from a flag. The profiles are counted off each row's bundles
    record: they are what a population finding's form reads, once the form is given.
    """
    # Narrowed by name before it is iterated (task 7.8): an argument that is not iterable at all
    # is the "nothing handed over" silence, and the type checker can now see it is never iterated.
    if not isinstance(series, Iterable):
        return _Facts(0, 0, -1, (), 0, 0)
    try:
        rows = tuple(series)
    except TypeError:
        return _Facts(0, 0, -1, (), 0, 0)
    population = 0
    construction = 0
    with_profiles = 0
    profiles = 0
    constructions: list[Interstice] = []
    for row in rows:
        if getattr(getattr(row, "ownership", None), "code", "") == "present":
            population += 1
        relations = getattr(row, "relations", None)
        built = getattr(relations, "interstices", ())
        try:
            found = tuple(item for item in built if isinstance(item, Interstice))
        except TypeError:
            found = ()
        if found:
            construction += 1
            constructions.extend(found)
        written = getattr(getattr(row, "bundles", None), "profiles", ())
        count = len(written) if isinstance(written, tuple) else 0
        if count:
            with_profiles += 1
            profiles += count
    return _Facts(
        population,
        construction,
        len(rows),
        tuple(constructions),
        with_profiles,
        profiles,
    )


def _one_finding(
    index: int,
    requirement: str,
    satisfied_by: str,
    subjects_required: int,
    kind: str,
    facts: _Facts,
    correspondence_declared: bool,
) -> Finding:
    """One finding's standing, from the subject facts this study's stages actually produced.

    The candidates are the constructions of this finding's KIND, read from the relations records.
    With exactly one, its two extents are the subjects; with none or several the subject indices
    are (0, 0) because there is no subject to name, and `finding_code` reaches the construction
    and dispatch checks BEFORE it looks at them -- which is what makes `subject_unconstructed` and
    `dispatch_undeclared` honest answers rather than claims about resolution.

    A population finding carries the number of profiles the bundles stage wrote for its
    population: the reading its form will be read against. The form is not given, so the count
    is carried and nothing is decided from it.

    A per-study count of series that constructed *something* is deliberately NOT read here: it
    cannot tell finding 2's requirement from finding 9's, and
    `test_a_global_construction_count_never_supplies_a_subject` is the must-not that refuses it.
    """
    candidates = tuple(item for item in facts.constructions if item.kind == kind)
    first, second = (
        (candidates[0].first, candidates[0].second) if len(candidates) == 1 else (0, 0)
    )
    code = finding_code(
        satisfied_by=satisfied_by,
        subjects_required=subjects_required,
        first_subject=first,
        second_subject=second,
        candidates=len(candidates),
        subject_population=facts.population,
        form_given=False,
        correspondence_declared=correspondence_declared,
        prior_outcome_offered=False,
    )
    return Finding(
        index=index,
        requirement=requirement,
        code=code,
        reason=finding_reason(requirement, code),
        subjects=(first, second),
        candidates=len(candidates),
        profiles=facts.profiles if satisfied_by == "population" else 0,
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
    facts = _series_facts(series)
    rows = facts.rows
    # Recorded by the CONSUMER at the point of reading (route-composition): what this stage took
    # from ownership, from relations and from the bundles, counted as the facts it read -- and
    # only when series records were handed over (task 7.14): with none, no ownership, relations
    # or bundles record exists to have been read, and `code` below names that silence.
    if rows > 0:
        ledger.record(
            "ownership.consumed_by.predicates",
            series=rows,
            with_population=facts.population,
        )
        ledger.record(
            "relations.consumed_by.predicates",
            series=rows,
            constructions=len(facts.constructions),
        )
        ledger.record(
            "vectors.consumed_by.predicates",
            series=rows,
            profiles=facts.profiles,
        )
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
            kind,
            facts,
            correspondence_declared,
        )
        for index, requirement, satisfied_by, subjects_required, kind in REQUIREMENTS
    )
    ledger.record("predicates.produced", findings=len(findings))
    if rows < 0:
        why = "no series reading was handed to this stage"
    elif rows == 0:
        why = "a series reading was handed over and it held no series"
    else:
        why = (
            f"{facts.population} of {rows} series resolved a partition; "
            f"{facts.construction} resolved a construction "
            f"({len(facts.constructions)} in all); "
            f"{facts.series_with_profiles} wrote profiles ({facts.profiles} in all)"
        )
    return FindingsReading(
        code=code,
        why=why,
        findings=findings,
        series_with_population=facts.population,
        series_with_construction=facts.construction,
        series_with_profiles=facts.series_with_profiles,
    )
