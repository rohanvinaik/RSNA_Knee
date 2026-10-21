"""Intent: each question reads only the cheap banks named before any score.

The selection comes from the declarations (objects, full prefixes) and the
condition contracts (roles); counts and labels never choose a bank. Two signs:
an unselected bank cannot move the selected names or a cosine over them, a
selected bank can; an empty or incompatible result is a named code, never
every bank; v1 names and full-profile prefixes never pass as v2 descriptors.
"""

from __future__ import annotations

import inspect
import random
from dataclasses import replace
from typing import Any

import pytest

import tests.squint_upgrade_fixtures as fixture
from knee.diagnosis import squint_profiles as writer
from knee.diagnosis import squint_questions as questions
from knee.diagnosis.declarations import QUESTIONS, question_for, select_question_banks
from knee.diagnosis.squint_contracts import QUESTION_IDS, contract_for
from knee.diagnosis.squint_interfaces import (
    SELECTION_SCHEMA,
    parse_territory_bank_name,
    selection_code,
    territory_bank_name,
)
from knee.diagnosis.squint_locator import _exact_bank_terms
from knee.diagnosis.squint_questions import (
    CHEAP_DIRECTIONS,
    CHEAP_METRICS,
    CHEAP_SCALES_MM,
    SELECTED,
    QuestionSelectionError,
    question_selection,
    select_cheap_banks,
)
from knee.encoding.counts import BankLayout, CountBundle, CountLayout
from knee.encoding.facets import BankFacetPlan, expand_facets
from knee.encoding.mri_spec import make_mri_spec
from knee.encoding.places import BankSpec, LayoutSpec, MetricKind, MetricSpec

VIEW = fixture.VIEW
OTHER_VIEW = {"orientation": "Sagittal", "fluid_sensitive": "0", "fat_suppression": "0"}
_ROLE_FIELDS = (
    ("necessary", "defining"),
    ("alternatives", "alternative"),
    ("supporting", "supporting"),
)


def v2(role: str, metric: str, direction: str, scale: float, view=VIEW) -> str:
    return territory_bank_name(view, role, metric, direction, scale)


def object_and_context_banks() -> dict[str, list[int]]:
    """A v2 profile's banks: object-role banks (selected) and context ones (not)."""
    banks: dict[str, list[int]] = {}
    for index, (metric, direction, scale) in enumerate(
        (
            ("signal_median", "overview", 10.0),
            ("signal_minimum", "patient_lps_left", 10.0),
            ("gradient_row", "row", 10.0),
            ("local_range", "stack_depth_first", 2.0),
        )
    ):
        banks[v2("object", metric, direction, scale)] = [index + 1, 2, 3 - index]
        banks[v2("context", metric, direction, scale)] = [4, index, 1]
    banks[v2("object", "signal_maximum", "overview", 10.0, OTHER_VIEW)] = [0, 5, 2]
    return banks


@pytest.fixture(scope="module")
def full_facet_banks() -> tuple[str, ...]:
    """The real expanded full-profile facet names (as the declarations test builds them)."""
    spec = make_mri_spec(include_coarse=True, retained_ordinary_profiles=True)
    base = LayoutSpec(
        spec["version"],
        "test-carrier",
        tuple(
            BankSpec(
                bank["name"],
                bank["facet"],
                tuple(
                    MetricSpec(
                        m["name"], MetricKind(m["kind"]), tuple(m.get("words", ()))
                    )
                    for m in bank["metrics"]
                ),
            )
            for bank in spec["banks"]
        ),
    )
    composition = spec["object_composition"]
    result = expand_facets(
        base,
        tuple(tuple(v) for v in composition["view_roles"]),
        tuple(BankFacetPlan(**p) for p in composition["bank_plans"]),
    )
    assert result.expansion is not None
    return tuple(entry.bank for entry in result.expansion.mapping)


def count_bundle(names) -> CountBundle:
    row = (1,) + (0,) * 511
    return CountBundle(
        CountLayout(
            "test-layout", "test-carrier", tuple(BankLayout(n, 512) for n in names)
        ),
        tuple(row for _ in names),
    )


def selected_terms(selection, subject, left, right):
    """Exact cosine terms (the recall's own arithmetic) over the selected names."""
    left_names, left_code = select_cheap_banks(selection, subject, left)
    right_names, right_code = select_cheap_banks(selection, subject, right)
    assert (left_code, right_code) == (SELECTED, SELECTED)
    return (
        left_names,
        right_names,
        _exact_bank_terms(
            {name: tuple(left[name]) for name in left_names},
            {name: tuple(right[name]) for name in right_names},
        ),
    )


# --- the selection is derived, not invented ---------------------------------


def test_selections_cover_exactly_the_twelve_declared_questions():
    assert tuple(question.question_id for question in QUESTIONS) == QUESTION_IDS
    for question_id in QUESTION_IDS:
        selection = question_selection(question_id)
        assert selection_code(selection) == "valid"
        assert selection["schema"] == SELECTION_SCHEMA
        assert selection["question_id"] == question_id


@pytest.mark.parametrize("question_id", QUESTION_IDS)
def test_subjects_roles_and_full_prefixes_come_from_declarations_and_contracts(
    question_id,
):
    declaration = question_for(question_id)
    contract = contract_for(question_id)
    selection = question_selection(question_id)
    expected_roles = {
        subject: role
        for field, role in _ROLE_FIELDS
        for subject in getattr(contract, field)
    }
    # Declaration order, contract roles; nothing added, nothing dropped.
    assert list(selection["subjects"]) == list(declaration.objects)
    assert selection["subjects"] == expected_roles
    assert selection["full_prefixes"] == list(declaration.bank_prefixes)
    assert selection["configuration_subject"] == declaration.subject
    assert selection["contract_id"] == contract.contract_id
    by_subject = {}
    surroundings = []
    for descriptor in selection["cheap"]:
        if descriptor["role"] == "context":
            surroundings.append(descriptor)
            continue
        assert descriptor["subject"] not in by_subject
        by_subject[descriptor["subject"]] = descriptor
    assert list(by_subject) == list(declaration.objects)
    # The one sourced surroundings reading: the MCL question's own ligament.
    expected_surroundings = ["mcl"] if question_id == "MCL" else []
    assert [item["subject"] for item in surroundings] == expected_surroundings
    for subject, descriptor in by_subject.items():
        assert descriptor["role"] == "object"
        assert descriptor["subject_role"] == expected_roles[subject]
        assert descriptor["metrics"] == list(CHEAP_METRICS)
        assert descriptor["scales_mm"] == list(CHEAP_SCALES_MM)
        assert descriptor["directions"] == {
            metric: list(directions) for metric, directions in CHEAP_DIRECTIONS.items()
        }
        assert descriptor["full_prefixes"] == [
            prefix
            for prefix in declaration.bank_prefixes
            if prefix.startswith(f"object/{subject}/")
        ]
    # The surroundings are not read for any other subject.
    assert [row["role"] for row in selection["not_selected"]] == ["context"]
    assert selection["not_selected"][0]["subjects"] == [
        subject
        for subject in declaration.objects
        if subject not in expected_surroundings
    ]


def _v2_names(subject_role: str, metric: str = "signal_median") -> list[str]:
    view = {"orientation": "Coronal", "fluid_sensitive": "1", "fat_suppression": "1"}
    return [
        territory_bank_name(view, role, metric, "overview", 10.0)
        for role in ("object", subject_role)
    ]


def test_only_the_mcl_question_reads_the_ligaments_surroundings():
    object_name, context_name = _v2_names("context")
    names = [object_name, context_name]
    selected, code = select_cheap_banks(question_selection("MCL"), "mcl", names)
    assert code == "selected"
    assert set(selected) == {object_name, context_name}
    # The same ligament's surroundings are not read by another question.
    selected, code = select_cheap_banks(
        question_selection("Medial Meniscus"), "femur", names
    )
    assert code == "selected"
    assert selected == (object_name,)
    # Nor the ACL's surroundings by the ACL question.
    selected, code = select_cheap_banks(question_selection("ACL"), "acl", names)
    assert selected == (object_name,)
    # A selection that reads surroundings is a different selection.
    assert question_selection("MCL")["version"].endswith("-v2")


def test_selection_is_fresh_each_call_and_its_fingerprint_names_its_content():
    first = question_selection("ACL")
    second = question_selection("ACL")
    assert first == second
    first["cheap"][0]["metrics"].clear()
    first["subjects"]["acl"] = "supporting"
    assert question_selection("ACL") == second
    fingerprints = {question_selection(q)["fingerprint"] for q in QUESTION_IDS}
    assert len(fingerprints) == len(QUESTION_IDS)


def test_unknown_question_and_disagreeing_sources_are_named_refusals(monkeypatch):
    cases: tuple[tuple[Any, str], ...] = (
        ("Meniscus", "question_unknown"),
        ("", "question_id_invalid"),
        (None, "question_id_invalid"),
    )
    for value, code in cases:
        with pytest.raises(QuestionSelectionError) as error:
            question_selection(value)  # ty: ignore[invalid-argument-type]
        assert error.value.code == code
    real = contract_for("ACL")
    monkeypatch.setattr(
        questions, "contract_for", lambda _q: replace(real, supporting=("femur",))
    )
    with pytest.raises(QuestionSelectionError) as error:
        question_selection("ACL")
    assert error.value.code == "declaration_contract_subjects_differ"
    monkeypatch.setattr(
        questions,
        "contract_for",
        lambda _q: replace(real, supporting=("acl", "femur", "tibia", "pcl")),
    )
    with pytest.raises(QuestionSelectionError) as error:
        question_selection("ACL")
    assert error.value.code == "contract_roles_overlap"


@pytest.mark.parametrize("question_id", QUESTION_IDS)
def test_unavailable_readings_name_every_full_family_and_their_sources(question_id):
    selection = question_selection(question_id)
    contract = contract_for(question_id)
    full_rows = [
        row
        for row in selection["unavailable"]
        if row["code"] == "full_family_without_cheap_bank"
    ]
    # Each declared full prefix is unavailable to the cheap route exactly once.
    assert sorted(row["source"].split(": ", 1)[1] for row in full_rows) == sorted(
        selection["full_prefixes"]
    )
    for row in selection["unavailable"]:
        assert row["subject"] in selection["subjects"]
        if row["code"] == "full_family_without_cheap_bank":
            assert row["source"].endswith(row["reading"].removeprefix("full:") + '",')
        elif row["code"] == "unmeasured_source_predicate":
            assert row["reading"] in contract.unmeasured_source_predicates
        else:
            # A limit-derived row quotes the one contract limit that says it.
            phrase = row["source"].split("«", 1)[1].rstrip("»")
            assert [text for text in contract.limits if phrase in text] == [
                row["reason"]
            ]


def test_sourced_unmeasured_readings_are_listed():
    def readings(question_id):
        return {
            (row["subject"], row["reading"])
            for row in question_selection(question_id)["unavailable"]
            if row["code"] != "full_family_without_cheap_bank"
        }

    assert readings("Baker's") == {
        ("gastrocnemius_semimembranosus_bursa", "communicates_with_knee_joint")
    }
    assert readings("Medial OA") == {
        ("femur", "medial_compartment_subdivision"),
        ("tibia", "medial_compartment_subdivision"),
    }
    assert readings("Synovitis") == {("synovium", "contrast_enhancement")}
    assert readings("Contusion") == {
        (bone, "marrow_as_separate_object") for bone in ("femur", "tibia", "patella")
    }
    assert readings("ACL") == set()


# --- the writer's vocabulary, not an invented one ----------------------------


def test_selector_vocabulary_is_exactly_the_cheap_writers_vocabulary():
    record = fixture.series_record()
    profile = writer.profile_window(
        record, (0, fixture.DEPTH, 0, fixture.ROWS, 0, fixture.COLS), subject="tibia"
    )
    written = set()
    for name in profile["banks"]:
        parts = dict(part.split("=", 1) for part in name.split("/") if "=" in part)
        written.add((parts["metric"], parts["direction"], parts["scale"]))
    declared = {
        (metric, direction, "10mm")
        for metric, directions in CHEAP_DIRECTIONS.items()
        for direction in directions
    }
    assert written == declared
    coarse = inspect.signature(writer.read_study_squints).parameters["tile_mm"]
    fine = inspect.signature(writer.refine_window).parameters["tile_mm"]
    assert (coarse.default, fine.default) == CHEAP_SCALES_MM
    # The same readings under v2 object-role names are all selected; their v1
    # names are not.
    selection = question_selection("Fracture")
    renamed = {
        v2("object", metric, direction, float(scale[:-2]))
        for metric, direction, scale in written
    }
    assert set(select_cheap_banks(selection, "tibia", renamed)[0]) == renamed
    assert select_cheap_banks(selection, "tibia", profile["banks"]) == (
        (),
        "no_v2_cheap_bank",
    )


# --- two signs: what may and may not move the comparison ---------------------


def test_perturbing_an_unselected_bank_moves_neither_names_nor_cosine():
    selection = question_selection("Medial Meniscus")
    query = object_and_context_banks()
    case = object_and_context_banks()
    case[v2("object", "signal_median", "overview", 10.0)] = [3, 3, 0]
    names, _, terms = selected_terms(selection, "medial_meniscus", query, case)
    assert [(parse_territory_bank_name(name) or {}).get("role") for name in names] == [
        "object"
    ] * len(names)

    perturbed = dict(query)
    perturbed[v2("context", "signal_median", "overview", 10.0)] = [90, 0, 0]
    perturbed[v2("context", "gradient_column", "column", 10.0)] = [0, 7, 0]
    perturbed[v2("object", "signal_median", "overview", 5.0)] = [0, 0, 9]
    perturbed[v2("object", "signal_median", "object_reference", 10.0)] = [9, 0, 0]
    v1_name = (
        'squint/v1/view=["Coronal","1","1"]/metric=signal_median/'
        "direction=overview/scale=10mm"
    )
    perturbed[v1_name] = [1, 1, 1]
    perturbed_names, _, perturbed_terms = selected_terms(
        selection, "medial_meniscus", perturbed, case
    )
    assert perturbed_names == names
    assert perturbed_terms == terms
    # Comparing every common bank, as raw recall does today, is moved by them.
    case_all = dict(case)
    case_all[v2("context", "signal_median", "overview", 10.0)] = [1, 0, 0]
    assert _exact_bank_terms(query, case_all) != _exact_bank_terms(perturbed, case_all)


def test_perturbing_a_selected_bank_can_change_the_cosine():
    selection = question_selection("Medial Meniscus")
    query = object_and_context_banks()
    case = object_and_context_banks()
    case[v2("object", "signal_median", "overview", 10.0)] = [3, 3, 0]
    names, _, terms = selected_terms(selection, "medial_meniscus", query, case)
    perturbed = dict(query)
    perturbed[v2("object", "signal_median", "overview", 10.0)] = [0, 0, 6]
    perturbed_names, _, perturbed_terms = selected_terms(
        selection, "medial_meniscus", perturbed, case
    )
    assert perturbed_names == names
    assert perturbed_terms != terms


def test_names_are_returned_in_one_fixed_order_and_counts_are_never_read():
    selection = question_selection("Medial Meniscus")
    banks = object_and_context_banks()
    names = list(banks)
    random.Random(7).shuffle(names)
    first = select_cheap_banks(selection, "medial_meniscus", banks)
    assert select_cheap_banks(selection, "medial_meniscus", names) == first
    assert select_cheap_banks(selection, "medial_meniscus", tuple(reversed(names))) == (
        first
    )
    silent = {name: [0, 0, 0] for name in banks}
    assert select_cheap_banks(selection, "medial_meniscus", silent) == first
    assert list(first[0]) == sorted(first[0])


# --- named refusals, never every bank ----------------------------------------


def test_empty_or_unmatched_selection_is_a_named_code_never_every_bank():
    selection = question_selection("Medial Meniscus")
    context_only = [
        v2("context", "signal_median", "overview", 10.0),
        v2("context", "gradient_row", "row", 2.0),
    ]
    unlisted = [
        v2("object", "signal_median", "overview", 5.0),
        v2("object", "signal_median", "object_reference", 10.0),
        v2("object", "texture_entropy", "overview", 10.0),
    ]
    cases: tuple[tuple[str, Any, str], ...] = (
        ("medial_meniscus", [], "no_bank_names"),
        ("medial_meniscus", context_only, "no_selected_bank_present"),
        ("medial_meniscus", unlisted, "no_selected_bank_present"),
        ("acl", context_only, "subject_not_in_selection"),
        ("diagnosis/Medial Meniscus", context_only, "subject_not_in_selection"),
        ("medial_meniscus", "squint/v2/not-a-list", "bank_names_invalid"),
        ("medial_meniscus", [context_only[0], 3], "bank_names_invalid"),
        ("medial_meniscus", [context_only[0], ""], "bank_names_invalid"),
        ("medial_meniscus", [context_only[0]] * 2, "bank_names_duplicate"),
        ("medial_meniscus", None, "bank_names_invalid"),
    )
    for subject, names, code in cases:
        result = select_cheap_banks(selection, subject, names)  # ty: ignore[invalid-argument-type]
        assert result == ((), code)


def test_malformed_or_partial_selections_are_named_refusals():
    names = [v2("object", "signal_median", "overview", 10.0)]
    selection = question_selection("Medial Meniscus")
    broken = dict(selection, schema="other")
    assert select_cheap_banks(broken, "medial_meniscus", names) == (
        (),
        "selection_schema_invalid",
    )
    no_descriptor = dict(
        selection,
        cheap=[
            row for row in selection["cheap"] if row["subject"] != "medial_meniscus"
        ],
    )
    assert select_cheap_banks(no_descriptor, "medial_meniscus", names) == (
        (),
        "subject_without_cheap_descriptor",
    )
    for bad in (
        {"signal_median": "overview"},
        {"signal_median": ["overview", 4]},
        ["overview"],
    ):
        descriptor = dict(selection["cheap"][0], directions=bad)
        malformed = dict(selection, cheap=[descriptor, *selection["cheap"][1:]])
        assert select_cheap_banks(malformed, "medial_meniscus", names) == (
            (),
            "selection_descriptor_invalid",
        )
    descriptor = dict(selection["cheap"][0], scales_mm=[True])
    malformed = dict(selection, cheap=[descriptor, *selection["cheap"][1:]])
    assert select_cheap_banks(malformed, "medial_meniscus", names) == (
        (),
        "selection_descriptor_invalid",
    )
    # A frozen-shape descriptor without directions reads every direction of its
    # metrics and scales, and still nothing else.
    descriptor = dict(selection["cheap"][0], metrics=["signal_median"])
    descriptor.pop("directions")
    narrow = dict(selection, cheap=[descriptor])
    candidates = [
        v2("object", "signal_median", "patient_lps_left", 10.0),
        v2("object", "signal_median", "anything_written", 2.0),
        v2("object", "signal_minimum", "overview", 10.0),
        v2("context", "signal_median", "overview", 10.0),
    ]
    assert select_cheap_banks(narrow, "medial_meniscus", candidates) == (
        tuple(sorted(candidates[:2])),
        SELECTED,
    )


# --- no string coincidence across bank families ------------------------------


def test_v1_names_and_full_prefixes_never_match_a_v2_descriptor(full_facet_banks):
    selection = question_selection("Medial Meniscus")
    subject = "medial_meniscus"
    record = fixture.series_record()
    v1_names = list(
        writer.profile_window(record, (0, 3, 0, 8, 0, 8), subject=subject)["banks"]
    )
    full_names = [f"object/{subject}/{bank}" for bank in full_facet_banks]
    selected = v2("object", "signal_median", "overview", 10.0)
    near_misses = [
        f"object/{subject}/" + 'facet:["lens_raw_signal",' + selected,
        selected.replace("scale=10mm", "scale=10.0mm"),
        selected.replace('["Coronal","1","1"]', '["Coronal", "1", "1"]'),
        selected + "/extra=1",
        selected.replace("scale=10mm", "scale=nanmm"),
        selected.replace("squint/v2/", "squint/v1/"),
        selected.replace("role=object", "role=objects"),
    ]
    for names in (
        v1_names,
        [f"object/{subject}/" + name for name in v1_names],
        full_names,
        near_misses,
    ):
        assert select_cheap_banks(selection, subject, names) == (
            (),
            "no_v2_cheap_bank",
        )
    # Well-formed v2 names of metrics no selection lists: equal prefixes of
    # characters select nothing.
    unlisted_metrics = [
        selected.replace("metric=signal_median", "metric=signal_median_x"),
        selected.replace("metric=signal_median", "metric=signal_m"),
    ]
    assert select_cheap_banks(selection, subject, unlisted_metrics) == (
        (),
        "no_selected_bank_present",
    )
    near_misses += unlisted_metrics
    # Among real v2 names, the foreign ones are simply never selected.
    assert select_cheap_banks(
        selection, subject, [*v1_names, *near_misses, selected]
    ) == (
        (selected,),
        SELECTED,
    )
    # And no v2 cheap name, bare or qualified, can satisfy a full prefix.
    prefixes = tuple(selection["full_prefixes"])
    every = [
        v2(role, metric, direction, scale)
        for role in ("object", "context")
        for metric, directions in CHEAP_DIRECTIONS.items()
        for direction in directions
        for scale in CHEAP_SCALES_MM
    ]
    assert not any(name.startswith(prefixes) for name in every)
    assert not any(
        f"object/{owner}/{name}".startswith(prefixes)
        for owner in selection["subjects"]
        for name in every
    )
    # Reciprocally, the declarations' own full-route selector, given full and
    # cheap names together, picks full facets and never a cheap name.
    qualified_cheap = [f"object/{subject}/{name}" for name in every]
    chosen = select_question_banks(
        question_for("Medial Meniscus"), count_bundle([*full_names, *qualified_cheap])
    )
    assert chosen
    assert set(chosen) <= set(full_names)


def test_configuration_names_select_only_their_own_subject():
    selection = question_selection("Medial Meniscus")
    own = v2("object", "signal_median", "overview", 10.0)
    ring = v2("context", "signal_median", "overview", 10.0)
    names = [
        f"object/{subject}/{name}"
        for subject in ("medial_meniscus", "femur", "tibia")
        for name in (own, ring)
    ]
    assert select_cheap_banks(selection, "medial_meniscus", names) == (
        (f"object/medial_meniscus/{own}",),
        SELECTED,
    )
    assert select_cheap_banks(selection, "femur", names) == (
        (f"object/femur/{own}",),
        SELECTED,
    )
    # The joint was not composed: absent, never borrowed from a neighbour.
    assert select_cheap_banks(selection, "joint", names) == (
        (),
        "subject_banks_absent",
    )
    # Defining tissue read only through its surroundings is not read at all.
    assert select_cheap_banks(
        selection, "medial_meniscus", [f"object/medial_meniscus/{ring}", *names[2:]]
    ) == ((), "no_selected_bank_present")
    assert select_cheap_banks(selection, "medial_meniscus", [own, *names]) == (
        (),
        "bank_names_mixed_forms",
    )
