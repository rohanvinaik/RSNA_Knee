"""Each question's cheap readings, named before any score (lane W6).

The thesis (What an <Object> Is §7.6, §8.4): the cosine is taken over only the
banks a question reads; which banks those are is named before the run it
judges; no bank carries a weight and none is chosen because it separates
confirmed cases. Until now raw squint recall compared every bank both profiles
had. This module states, for each of the twelve questions, which cheap
territory banks it reads.

Nothing here is a new catalog. ``declarations.QUESTIONS`` supplies each
question's objects and its full-profile prefixes; ``squint_contracts`` supplies
each object's role (necessary -> defining, alternatives -> alternative,
supporting -> supporting). This module only adapts those declarations to the
cheap v2 bank names (``squint_interfaces.territory_bank_name``):

* Every declared object, whatever its role, is read over its own places
  (territory role ``object``). This is the cheap form of the declarations'
  rule that every declared object reads its own measured content ("Measured
  context objects remain available alongside the primary tissue").
* Each is read with every metric the cheap writer measures, in every
  direction it writes, at both scales it writes (10 mm squint, 2 mm
  refinement) and in every acquisition view: the declarations' "including
  each view, scale and direction". The vocabulary is the writer's
  (``squint_profiles.profile_window``) and is listed explicitly, so a new
  direction or scale is a new measurement that needs a new selection version,
  never a silent match.
* The territory's ``context`` role (an object's surroundings) is not read,
  with one sourced exception. No declaration or contract names an object's
  surroundings as a reading; a question's context is its declared supporting
  objects, read over their own places, recorded in ``not_selected``. The
  exception is the MCL question's own ligament: the domain document describes
  the normal MCL as "a uniformly low-signal line, with no surrounding oedema or
  internal signal" (OBJECTS_AND_CONDITIONS §4, Ligaments, source [C]), so its
  surroundings are part of how medicine reads it (the lead's decision,
  SQUINT_TRAINING_BUILD §10). Context banks never count as reading the
  defining tissue itself.
* No cheap bank is compared with a full-profile bank. The full prefixes are
  carried unchanged for the full payload's own adapter, and every full family
  is listed as unavailable in the cheap route, with the contracts' own
  unmeasured predicates and stated limits.

``select_cheap_banks`` reads bank names only, like ``select_question_banks``:
a selected but silent bank stays silent, counts never influence the choice,
and an empty or incompatible result is a named code, never every bank. A name
is a cheap v2 bank only if it is exactly what ``territory_bank_name`` writes,
either bare (an object's own profile) or qualified ``object/<subject>/`` (a
role-qualified configuration profile, ``squint_configurations``). v1 names,
full-profile facet names and anything else are never selected, whatever
characters they share with a selected name.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable, Mapping
from functools import lru_cache
from typing import Any

from knee.diagnosis.declarations import question_for
from knee.diagnosis.squint_contracts import ContractError, contract_for
from knee.diagnosis.squint_interfaces import (
    ROLE_CONTEXT,
    ROLE_NAMES,
    ROLE_OBJECT,
    SELECTION_SCHEMA,
    TERRITORY_PROCEDURE,
    parse_territory_bank_name,
    selection_code,
    territory_bank_name,
)

__all__ = [
    "CHEAP_DIRECTIONS",
    "CHEAP_METRICS",
    "CHEAP_SCALES_MM",
    "SELECTED",
    "SELECTION_VERSION",
    "QuestionSelectionError",
    "question_selection",
    "select_cheap_banks",
]

SELECTION_VERSION = "knee.squint-questions/declared-object-places-v2"
SELECTED = "selected"

# The cheap writer's vocabulary, as squint_profiles.profile_window writes it:
# patient-LPS half-spaces around the window's median tile centre, thirds of
# the window's slices, and the overview (row/column for the two gradients).
_LPS_DIRECTIONS = (
    "patient_lps_left",
    "patient_lps_right",
    "patient_lps_posterior",
    "patient_lps_anterior",
    "patient_lps_superior",
    "patient_lps_inferior",
)
_DEPTH_DIRECTIONS = ("stack_depth_first", "stack_depth_middle", "stack_depth_last")
CHEAP_DIRECTIONS: dict[str, tuple[str, ...]] = {
    "signal_median": ("overview", *_LPS_DIRECTIONS, *_DEPTH_DIRECTIONS),
    "signal_minimum": ("overview", *_LPS_DIRECTIONS, *_DEPTH_DIRECTIONS),
    "signal_maximum": ("overview", *_LPS_DIRECTIONS, *_DEPTH_DIRECTIONS),
    "local_range": ("overview", *_LPS_DIRECTIONS, *_DEPTH_DIRECTIONS),
    "gradient_row": ("row", *_LPS_DIRECTIONS, *_DEPTH_DIRECTIONS),
    "gradient_column": ("column", *_LPS_DIRECTIONS, *_DEPTH_DIRECTIONS),
}
CHEAP_METRICS: tuple[str, ...] = tuple(CHEAP_DIRECTIONS)
#: read_study_squints' 10 mm squint and refine_window's 2 mm refinement.
CHEAP_SCALES_MM: tuple[float, ...] = (10.0, 2.0)

_CONTRACT_ROLES = (
    ("necessary", "defining"),
    ("alternatives", "alternative"),
    ("supporting", "supporting"),
)
_OBJECT_ROLE = ROLE_NAMES[ROLE_OBJECT]
_QUALIFIER = "object/"

_DECLARATIONS = "knee.diagnosis.declarations"
_CONTRACTS = "knee.diagnosis.squint_contracts"
_WRITER = "knee.diagnosis.squint_profiles"

#: (question, subject) pairs whose surroundings a source names as part of the
#: reading, with that source. Only these read the territory's context role.
_SURROUNDINGS: dict[tuple[str, str], str] = {
    ("MCL", "mcl"): (
        "docs/OBJECTS_AND_CONDITIONS.md §4 Ligaments, MCL: 'a uniformly low-signal "
        "line, with no surrounding oedema or internal signal' [C]"
    ),
}

_FULL_FAMILY_REASON = (
    "read only in the full payload, through its own canonical adapter; the cheap "
    "writer's tile statistics of acquired signal never share a full family's "
    "measurement definition, so no cheap bank is compared with it"
)

# Readings a contract's own words state are not measured, keyed by question:
# (subjects, reading, code, a phrase of the contract limit that says so).
# An entry is written only while its phrase is in the contract's limits.
_LIMIT_READINGS: dict[str, tuple[tuple[tuple[str, ...], str, str, str], ...]] = {
    "Medial OA": (
        (
            ("femur", "tibia"),
            "medial_compartment_subdivision",
            "whole_object_not_subdivided",
            "a whole bone is not a medial subdivision",
        ),
    ),
    "Lateral OA": (
        (
            ("femur", "tibia"),
            "lateral_compartment_subdivision",
            "whole_object_not_subdivided",
            "a whole bone is not a lateral subdivision",
        ),
    ),
    "Synovitis": (
        (
            ("synovium",),
            "contrast_enhancement",
            "not_marked_in_acquisition_tags",
            "no tag marks contrast",
        ),
    ),
    "Contusion": (
        (
            ("femur", "tibia", "patella"),
            "marrow_as_separate_object",
            "not_independently_encoded",
            "marrow is not an independently encoded object",
        ),
    ),
    "Fracture": (
        (
            ("femur", "tibia", "patella", "fibula"),
            "marrow_as_separate_object",
            "not_independently_encoded",
            "marrow is not an independently encoded object",
        ),
    ),
}


class QuestionSelectionError(ValueError):
    """A named reason a question's selection cannot be derived."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _subject_roles(question_id: str) -> tuple[Any, Any, dict[str, str]]:
    """The declared objects in declaration order, each with its contract role."""
    try:
        declaration = question_for(question_id)
    except KeyError as error:
        raise QuestionSelectionError("question_unknown") from error
    try:
        contract = contract_for(question_id)
    except ContractError as error:
        raise QuestionSelectionError("contract_unknown") from error
    by_subject: dict[str, str] = {}
    for field, role in _CONTRACT_ROLES:
        for subject in getattr(contract, field):
            if subject in by_subject:
                raise QuestionSelectionError("contract_roles_overlap")
            by_subject[subject] = role
    objects = tuple(declaration.objects)
    if len(set(objects)) != len(objects):
        raise QuestionSelectionError("declaration_objects_duplicate")
    if set(objects) != set(by_subject):
        raise QuestionSelectionError("declaration_contract_subjects_differ")
    return declaration, contract, {subject: by_subject[subject] for subject in objects}


def _full_by_subject(declaration: Any, subjects: Iterable[str]) -> dict[str, list[str]]:
    """Each declared full prefix under the one object it names."""
    grouped: dict[str, list[str]] = {subject: [] for subject in subjects}
    for prefix in declaration.bank_prefixes:
        owners = [
            subject for subject in grouped if prefix.startswith(f"object/{subject}/")
        ]
        if len(owners) != 1:
            raise QuestionSelectionError("full_prefix_subject_unattributed")
        grouped[owners[0]].append(prefix)
    return grouped


def _full_family(prefix: str) -> str:
    """The base bank a declared prefix ``object/<s>/facet:["<bank>",`` selects."""
    _, marker, rest = prefix.partition('/facet:["')
    family, comma, _ = rest.partition('",')
    if not marker or not comma or not family:
        raise QuestionSelectionError("full_prefix_unparsed")
    return family


def _descriptor(question_id: str, subject: str, role: str, full: list[str]) -> dict:
    return {
        "subject": subject,
        "subject_role": role,
        "role": _OBJECT_ROLE,
        "reads": "the subject's own places in its territory",
        "metrics": list(CHEAP_METRICS),
        "directions": {
            metric: list(CHEAP_DIRECTIONS[metric]) for metric in CHEAP_METRICS
        },
        "scales_mm": list(CHEAP_SCALES_MM),
        "views": "every acquisition view; a bank is compared only under its identical name",
        "full_prefixes": list(full),
        "full_counterpart": (
            "none comparable: these full prefixes select the same object's full "
            "payload, which is read through its own adapter and never against a cheap bank"
        ),
        "source": {
            "subject": f"{_DECLARATIONS}.question_for({question_id!r}).objects",
            "subject_role": f"{_CONTRACTS}.contract_for({question_id!r}) role fields",
            "role": (
                f"{_DECLARATIONS} module note: every declared object reads its own "
                "measured content; 'Measured context objects remain available "
                "alongside the primary tissue'"
            ),
            "metrics_directions_scales": (
                f"{_WRITER}.profile_window and refine_window writer vocabulary; "
                f"{_DECLARATIONS} module note: 'including each view, scale and direction'"
            ),
            "full_prefixes": f"{_DECLARATIONS}.question_for({question_id!r}).bank_prefixes",
        },
    }


def _surroundings_descriptor(
    question_id: str, subject: str, role: str, source: str
) -> dict:
    """The sourced exception: a subject's surroundings read over its context tiles."""
    descriptor = _descriptor(question_id, subject, role, [])
    descriptor["role"] = ROLE_NAMES[ROLE_CONTEXT]
    descriptor["reads"] = "the subject's surroundings in its territory (context tiles)"
    descriptor["full_counterpart"] = "none: the full payload has no surroundings family"
    descriptor["source"] = {**descriptor["source"], "role": source}
    return descriptor


def _unavailable(
    question_id: str, contract: Any, full: Mapping[str, list[str]]
) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = [
        {
            "subject": subject,
            "reading": f"full:{_full_family(prefix)}",
            "route": "cheap",
            "code": "full_family_without_cheap_bank",
            "reason": _FULL_FAMILY_REASON,
            "source": (
                f"{_DECLARATIONS}.question_for({question_id!r}).bank_prefixes: {prefix}"
            ),
        }
        for subject, prefixes in full.items()
        for prefix in prefixes
    ]
    # A source predicate belongs to the condition's own tissue.
    owners = tuple(contract.necessary) or tuple(contract.alternatives)
    entries.extend(
        {
            "subject": subject,
            "reading": predicate,
            "route": "all",
            "code": "unmeasured_source_predicate",
            "reason": (
                "the contract names this source predicate; no measured object carries it"
            ),
            "source": (
                f"{_CONTRACTS}.contract_for({question_id!r}).unmeasured_source_predicates"
            ),
        }
        for predicate in contract.unmeasured_source_predicates
        for subject in owners
    )
    for subjects, reading, code, phrase in _LIMIT_READINGS.get(question_id, ()):
        limits = [text for text in contract.limits if phrase in text]
        if len(limits) != 1:
            continue
        entries.extend(
            {
                "subject": subject,
                "reading": reading,
                "route": "all",
                "code": code,
                "reason": limits[0],
                "source": (
                    f"{_CONTRACTS}.contract_for({question_id!r}).limits: «{phrase}»"
                ),
            }
            for subject in subjects
            if subject in full
        )
    return entries


def _fingerprint(selection: Mapping[str, Any]) -> str:
    body = {key: value for key, value in selection.items() if key != "fingerprint"}
    text = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def question_selection(question_id: str) -> dict[str, Any]:
    """The cheap banks one train.csv question reads, derived before any score.

    Raises ``QuestionSelectionError`` with a named code when the question is
    unknown or its declaration and contract disagree on its subjects. The
    result is a fresh plain dict each call; ``fingerprint`` identifies its
    content for preparation and cache keys.
    """
    if not isinstance(question_id, str) or not question_id:
        raise QuestionSelectionError("question_id_invalid")
    declaration, contract, roles = _subject_roles(question_id)
    full = _full_by_subject(declaration, roles)
    selection: dict[str, Any] = {
        "schema": SELECTION_SCHEMA,
        "question_id": question_id,
        "version": SELECTION_VERSION,
        "contract_id": contract.contract_id,
        "configuration_subject": declaration.subject,
        "cheap_procedure": TERRITORY_PROCEDURE,
        "subjects": dict(roles),
        "cheap": [
            _descriptor(question_id, subject, roles[subject], full[subject])
            for subject in roles
        ]
        + [
            _surroundings_descriptor(question_id, subject, roles[subject], source)
            for (question, subject), source in _SURROUNDINGS.items()
            if question == question_id and subject in roles
        ],
        "full_prefixes": list(declaration.bank_prefixes),
        "unavailable": _unavailable(question_id, contract, full),
        "not_selected": [
            {
                "role": ROLE_NAMES[ROLE_CONTEXT],
                "subjects": [
                    subject
                    for subject in roles
                    if (question_id, subject) not in _SURROUNDINGS
                ],
                "code": "surroundings_not_declared",
                "reason": (
                    "no declaration or contract names an object's surroundings as a "
                    "reading; the question's context is its supporting objects, read "
                    "over their own places"
                ),
                "source": f"{_DECLARATIONS}.question_for({question_id!r}).objects",
            }
        ],
        "sources": {
            "subjects": f"{_DECLARATIONS}.question_for({question_id!r}).objects",
            "subject_roles": (
                f"{_CONTRACTS}.contract_for({question_id!r}) [{contract.contract_id}] "
                "necessary -> defining, alternatives -> alternative, "
                "supporting -> supporting"
            ),
            "full_prefixes": f"{_DECLARATIONS}.question_for({question_id!r}).bank_prefixes",
        },
    }
    selection["fingerprint"] = _fingerprint(selection)
    code = selection_code(selection)
    if code != "valid":
        raise QuestionSelectionError(code)
    return selection


@lru_cache(maxsize=65536)
def _classify(name: str) -> tuple[str, str, str, str, str, float] | None:
    """(form, owner, role, metric, direction, scale) of a cheap v2 name, else None.

    ``form`` is ``bare`` or ``qualified``; ``owner`` is the qualifying subject
    ("" when bare). Only exactly canonical names qualify: rewriting the parsed
    fields with ``territory_bank_name`` must give the name back.
    """
    owner = ""
    rest = name
    form = "bare"
    if name.startswith(_QUALIFIER):
        owner, sep, rest = name[len(_QUALIFIER) :].partition("/")
        if not sep or not owner:
            return None
        form = "qualified"
    fields = parse_territory_bank_name(rest)
    if fields is None:
        return None
    view = fields["view"]
    if any(not isinstance(part, str) or not part for part in view):
        return None
    scale = fields["scale_mm"]
    if not math.isfinite(scale) or scale <= 0:
        return None
    metric, direction, role = fields["metric"], fields["direction"], fields["role"]
    if not metric or not direction:
        return None
    rebuilt = territory_bank_name(
        {
            "orientation": view[0],
            "fluid_sensitive": view[1],
            "fat_suppression": view[2],
        },
        role,
        metric,
        direction,
        scale,
    )
    if rebuilt != rest:
        return None
    return form, owner, role, metric, direction, scale


def _allowed(descriptor: Mapping[str, Any]) -> tuple[set, set] | None:
    """(role, metric, direction, scale) and wildcard-direction keys, or None if malformed."""
    role = descriptor.get("role")
    metrics = descriptor.get("metrics")
    scales = descriptor.get("scales_mm")
    if not isinstance(metrics, list) or not isinstance(scales, list):
        return None
    if any(not isinstance(metric, str) or not metric for metric in metrics) or any(
        isinstance(scale, bool) or not isinstance(scale, (int, float))
        for scale in scales
    ):
        return None
    directions = descriptor.get("directions")
    exact: set = set()
    wildcard: set = set()
    if directions is None:
        wildcard = {
            (role, metric, float(scale)) for metric in metrics for scale in scales
        }
        return exact, wildcard
    if not isinstance(directions, Mapping):
        return None
    for metric in metrics:
        listed = directions.get(metric)
        if not isinstance(listed, (list, tuple)) or any(
            not isinstance(direction, str) or not direction for direction in listed
        ):
            return None
        exact.update(
            (role, metric, direction, float(scale))
            for direction in listed
            for scale in scales
        )
    return exact, wildcard


def select_cheap_banks(
    selection: Mapping[str, Any], subject: str, bank_names: Iterable[str]
) -> tuple[tuple[str, ...], str]:
    """The subject's selected cheap bank names present, sorted; else a named code.

    ``bank_names`` are one profile's bank names (a mapping's keys suffice):
    bare v2 names of ``subject``'s own profile, or ``object/<subject>/``
    qualified v2 names of a configuration profile. Counts are never read.
    Returns ``(names, "selected")`` or ``((), code)``; never every bank.
    """
    code = selection_code(selection)
    if code != "valid":
        return (), code
    if not isinstance(subject, str) or subject not in selection["subjects"]:
        return (), "subject_not_in_selection"
    descriptors = [item for item in selection["cheap"] if item["subject"] == subject]
    if not descriptors:
        return (), "subject_without_cheap_descriptor"
    exact: set = set()
    wildcard: set = set()
    for descriptor in descriptors:
        allowed = _allowed(descriptor)
        if allowed is None:
            return (), "selection_descriptor_invalid"
        exact |= allowed[0]
        wildcard |= allowed[1]
    if isinstance(bank_names, (str, bytes)) or not isinstance(bank_names, Iterable):
        return (), "bank_names_invalid"
    names = list(bank_names)
    if any(not isinstance(name, str) or not name for name in names):
        return (), "bank_names_invalid"
    if not names:
        return (), "no_bank_names"
    if len(set(names)) != len(names):
        return (), "bank_names_duplicate"
    cheap = [(name, _classify(name)) for name in names]
    cheap = [(name, fields) for name, fields in cheap if fields is not None]
    if not cheap:
        return (), "no_v2_cheap_bank"
    if len({fields[0] for _, fields in cheap}) > 1:
        return (), "bank_names_mixed_forms"
    own = [
        (name, fields)
        for name, fields in cheap
        if fields[0] == "bare" or fields[1] == subject
    ]
    if not own:
        return (), "subject_banks_absent"
    selected = sorted(
        name
        for name, (_, _, role, metric, direction, scale) in own
        if (role, metric, direction, scale) in exact
        or (role, metric, scale) in wildcard
    )
    if not selected:
        return (), "no_selected_bank_present"
    return tuple(selected), SELECTED
