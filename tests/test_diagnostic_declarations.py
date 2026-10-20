"""Intent: select measured anatomy, preserve roles, and never infer a diagnosis.

These direct caller tests cover acceptance and refusal before Detective pins the
mechanical selection. Actual MRI declarations supply the expanded facet names;
labels, acquisition/status metadata and silent rows cannot become injury facts.
"""

from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace

import pytest

from knee.diagnosis.declarations import (
    QUESTIONS,
    _bank_selection,
    _question,
    question_for,
    select_question_banks,
)
from knee.diagnosis.models import Question
from knee.encoding.counts import (
    BankLayout,
    CountBundle,
    CountCode,
    CountLayout,
    cosine_terms,
)
from knee.encoding.facets import BankFacetPlan, expand_facets
from knee.encoding.mri_spec import make_mri_spec
from knee.encoding.places import BankSpec, LayoutSpec, MetricKind, MetricSpec
from knee.objects.assignments import OBJECT_CODES

CONDITIONS = (
    "ACL",
    "MCL",
    "Medial Meniscus",
    "Lateral Meniscus",
    "Medial OA",
    "Lateral OA",
    "PF OA",
    "Effusion",
    "Synovitis",
    "Baker's",
    "Contusion",
    "Fracture",
)


def bundle_for(names: tuple[str, ...], count: int = 0) -> CountBundle:
    row = (count,) + (0,) * 511
    return CountBundle(
        CountLayout(
            "test-content-layout",
            "test-carrier",
            tuple(BankLayout(n, 512) for n in names),
        ),
        tuple(row for _ in names),
    )


@pytest.fixture(scope="module")
def declared_expansion():
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
    return result.expansion


def test_registry_has_exact_twelve_ids_subjects_and_canonical_sources():
    assert isinstance(QUESTIONS, tuple)
    assert tuple(q.question_id for q in QUESTIONS) == CONDITIONS
    for question in QUESTIONS:
        assert question_for(question.question_id) is question
        assert question.subject == "diagnosis/" + question.question_id
        assert isinstance(question.objects, tuple)
        assert len(set(question.objects)) == len(question.objects)
        assert set(question.objects) <= (set(OBJECT_CODES) - {"unassigned"})
        assert question.banks == ()
        assert question.bank_prefixes
        with pytest.raises(FrozenInstanceError):
            question.subject = "changed"


@pytest.mark.parametrize(
    "unknown", ["acl", " ACL", "Baker’s", "Bakers", "", "unknown", None, True, []]
)
def test_unknown_condition_is_never_normalized_or_guessed(unknown):
    with pytest.raises(KeyError):
        question_for(unknown)


def test_anatomy_keeps_compartments_surfaces_and_family_scope():
    assert question_for("ACL").objects == ("acl", "femur", "tibia", "pcl")
    assert "medial_meniscus" in question_for("MCL").objects
    assert "lateral_meniscus" not in question_for("MCL").objects
    assert "medial_meniscus" in question_for("Medial OA").objects
    assert "lateral_meniscus" not in question_for("Medial OA").objects
    assert "lateral_meniscus" in question_for("Lateral OA").objects
    assert "medial_meniscus" not in question_for("Lateral OA").objects
    assert set(question_for("PF OA").objects) == {
        "patella",
        "femur",
        "patellar_cartilage",
        "trochlear_cartilage",
    }
    assert "synovium" in question_for("Synovitis").objects
    assert "anterior_synovial_recess" in question_for("Effusion").objects
    assert "joint_capsule" in question_for("Effusion").objects
    assert {
        "gastrocnemius_semimembranosus_bursa",
        "semimembranosus",
        "medial_gastrocnemius",
    } <= set(question_for("Baker's").objects)
    assert question_for("Contusion").objects == ("femur", "tibia", "patella")
    assert question_for("Fracture").objects == ("femur", "tibia", "patella", "fibula")


def test_binding_uses_only_the_sources_actual_content_families(declared_expansion):
    question = _question("ACL", ("acl",))
    boolean = next(
        e.bank for e in declared_expansion.mapping if e.base_bank == "lens_boolean"
    )
    area = next(
        e.bank
        for e in declared_expansion.mapping
        if e.base_bank == "native_profile_area"
    )
    acquisition = next(
        e.bank
        for e in declared_expansion.mapping
        if e.base_bank == "acquisition_context"
    )
    names = tuple(f"object/acl/{n}" for n in (boolean, area, acquisition))
    assert question.subject == "diagnosis/ACL"
    assert question.objects == ("acl",)
    assert select_question_banks(question, bundle_for(names)) == (names[0],)


@pytest.mark.parametrize("question", QUESTIONS, ids=CONDITIONS)
def test_defaults_select_actual_expanded_content_and_exclude_metadata(
    question, declared_expansion
):
    names = tuple(
        f"object/{obj}/{bank.bank}"
        for obj in question.objects
        for bank in declared_expansion.mapping
    )
    bundle = bundle_for(names)
    selected = select_question_banks(question, bundle)
    assert selected
    by_original_name = {b.bank: b.base_bank for b in declared_expansion.mapping}
    for name in selected:
        _, obj, original = name.split("/", 2)
        assert obj in question.objects
        assert by_original_name[original] not in {
            "acquisition_context",
            "native_profile_status",
            "fibula_packed_target",
        }
    # Every default prefix is bound to a real installed bank, not a guessed name.
    assert all(any(n.startswith(p) for n in selected) for p in question.bank_prefixes)
    assert select_question_banks(question, bundle_for(names, count=7)) == selected


def test_default_prefixes_preserve_view_scale_direction_and_source_role(
    declared_expansion,
):
    facets = [e for e in declared_expansion.mapping if e.base_bank == "lens_boolean"]
    names = tuple(f"object/medial_meniscus/{e.bank}" for e in facets)
    swapped = tuple(f"object/lateral_meniscus/{e.bank}" for e in facets)
    unqualified = tuple(e.bank for e in facets)
    lookalike = tuple(
        n.replace('"lens_boolean",', '"lens_boolean_extra",') for n in names
    )
    query = bundle_for(names + swapped + unqualified + lookalike)
    assert select_question_banks(question_for("Medial Meniscus"), query) == names
    assert select_question_banks(question_for("Lateral Meniscus"), query) == swapped
    assert {e.direction for e in facets} == {
        None,
        *((m, p, s) for m in (-1, 0, 1) for p in (-1, 0, 1) for s in (-1, 0, 1)),
    }
    assert len({e.view_role for e in facets}) == 12


def test_silent_selected_content_remains_silent_and_metadata_cannot_speak(
    declared_expansion,
):
    content = next(
        e.bank for e in declared_expansion.mapping if e.base_bank == "lens_boolean"
    )
    metadata = next(
        e.bank
        for e in declared_expansion.mapping
        if e.base_bank == "acquisition_context"
    )
    names = (f"object/acl/{content}", f"object/acl/{metadata}")
    silent = bundle_for(names)
    observed_metadata = replace(silent, counts=(silent.counts[0], (1,) + (0,) * 511))
    selected = select_question_banks(question_for("ACL"), observed_metadata)
    assert selected == (names[0],)
    assert (
        cosine_terms(observed_metadata, observed_metadata, selected).code
        is CountCode.SILENT
    )
    assert select_question_banks(question_for("ACL"), bundle_for((names[1],))) == ()


def test_explicit_selection_overrides_prefixes_and_keeps_layout_order():
    question = Question(
        "custom",
        "diagnosis/custom",
        ("acl",),
        banks=("relation", "content"),
        bank_prefixes=("other/",),
    )
    assert select_question_banks(
        question, bundle_for(("content", "other/x", "relation"))
    ) == ("content", "relation")
    assert select_question_banks(question, bundle_for(("other/x",))) == ()


def test_measured_context_can_be_explicit_without_an_all_bank_fallback():
    question = Question(
        "contextual",
        "diagnosis/contextual",
        ("acl",),
        bank_prefixes=("measured_neighbourhood/",),
    )
    names = (
        "study_uid",
        "status",
        "acquisition_context",
        "measured_neighbourhood/fluid",
    )
    assert select_question_banks(question, bundle_for(names)) == (names[-1],)
    assert (
        select_question_banks(replace(question, bank_prefixes=()), bundle_for(names))
        == ()
    )
    assert (
        select_question_banks(replace(question, banks=("missing",)), bundle_for(names))
        == ()
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("banks", ("",)),
        ("bank_prefixes", ("",)),
        ("banks", "content"),
        ("bank_prefixes", ["content"]),
        ("banks", (None,)),
        ("banks", ("content", "content")),
        ("bank_prefixes", ("x", "x")),
    ],
)
def test_malformed_selectors_are_refused(field, value):
    question = replace(question_for("ACL"), **{field: value})
    with pytest.raises(ValueError, match="invalid_question_bank_selectors"):
        select_question_banks(question, bundle_for(("content",)))


@pytest.mark.parametrize(
    "bad_question", [None, SimpleNamespace(banks=(), bank_prefixes=())]
)
def test_non_question_boundary_is_refused_even_when_truthy(bad_question):
    with pytest.raises(TypeError, match="^question_required$"):
        select_question_banks(bad_question, bundle_for(("a",)))


@pytest.mark.parametrize(
    "bad_bundle",
    [
        None,
        CountBundle(None, ()),
        SimpleNamespace(layout=CountLayout("x", "c", (BankLayout("x", 512),))),
        CountBundle(SimpleNamespace(banks=(BankLayout("x", 512),)), ()),
    ],
)
def test_non_bundle_or_non_layout_is_refused_even_when_truthy(bad_bundle):
    with pytest.raises(TypeError, match="^count_bundle_required$"):
        select_question_banks(question_for("ACL"), bad_bundle)


@pytest.mark.parametrize(
    "bad_banks",
    [
        [BankLayout("x", 512)],
        ("bad",),
        (BankLayout("good", 512), "bad"),
        (SimpleNamespace(name="x"),),
        (BankLayout(1, 512),),
        (BankLayout("", 512),),
    ],
)
def test_bank_layout_boundary_checks_every_bank_and_name(bad_banks):
    with pytest.raises(ValueError, match="^invalid_bank_layout$"):
        select_question_banks(
            question_for("ACL"), CountBundle(CountLayout("x", "c", bad_banks), ())
        )


def test_duplicate_names_have_a_named_refusal():
    with pytest.raises(ValueError, match="^duplicate_bank_names$"):
        select_question_banks(question_for("ACL"), bundle_for(("a", "a")))


def test_empty_layout_has_no_selected_evidence():
    assert select_question_banks(question_for("ACL"), bundle_for(())) == ()


@pytest.mark.parametrize(
    "bank,explicit,prefixes,expected",
    [
        ("a", ("a",), ("b",), "selected_explicit"),
        ("b", ("a",), ("b",), "outside_explicit"),
        ("abc", (), ("a",), "selected_prefix"),
        ("abc", (), ("x", "a"), "selected_prefix"),
        ("abc", (), ("x",), "outside_prefix"),
        ("abc", (), (), "undeclared"),
    ],
)
def test_direct_selection_decision_both_signs(bank, explicit, prefixes, expected):
    assert _bank_selection(bank, explicit, prefixes) == expected
