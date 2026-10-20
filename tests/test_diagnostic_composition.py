"""Intent: preserve exact roles/rows, silence and source identity in ONE case.

The counterexample swaps different row multiplicities between anatomical roles:
unqualified totals match exactly, but the question-composite must distinguish it.
Source acquisition words never establish a positive or negative medical call.
"""

import json
from dataclasses import replace

import pytest

from knee.diagnosis.composition import (
    CompositionError,
    PreparedComposition,
    compose_question_profile,
    source_status_code,
)
from knee.diagnosis.composition import (
    prepare_composition as prepare_diagnostic_composition,
)
from knee.diagnosis.models import Profile, Question
from knee.diagnosis.teaching import teach_from_labels
from knee.encoding.composition import prepare_composition
from knee.encoding.counts import (
    BankLayout,
    CountBundle,
    CountCode,
    CountLayout,
    cosine_terms,
)
from knee.encoding.places import BankSpec, LayoutSpec, MetricKind, MetricSpec

QUESTION = Question("Fracture", "diagnosis/Fracture", ("femur", "tibia"))
LAYOUT = CountLayout(
    "declaration:reference-v1", "carrier-v1", (BankLayout("signal", 3),)
)


def profile(name, row=(2, 0, 0), *, layout=LAYOUT, source="case-A", **kwargs):
    return Profile(
        name, CountBundle(layout, (row,)), "full", "object:" + name, source, **kwargs
    )


def test_direct_positive_intent_preserves_role_rows_and_exact_multiplicity():
    femur = profile("femur", (2, 1, 0))
    tibia = profile("tibia", (0, 0, 7))
    result = compose_question_profile([tibia, femur], QUESTION)
    assert result.subject == "diagnosis/Fracture"
    assert result.scope == "question:Fracture"
    assert result.bundle.counts == ((2, 1, 0), (0, 0, 7))
    assert tuple(b.name for b in result.bundle.layout.banks) == (
        "object/femur/signal",
        "object/tibia/signal",
    )
    assert femur.bundle.layout == LAYOUT
    assert tibia.bundle.counts == ((0, 0, 7),)
    assert result.source_id == "case-A"
    assert dict(result.provenance)["source_state_compatibility"] == "undeclared"
    assert not hasattr(result, "calls")


def test_direct_negative_intent_role_swap_is_not_unqualified_pooling():
    rows = ((2, 1, 0), (0, 0, 7))
    original = compose_question_profile(
        [profile("femur", rows[0]), profile("tibia", rows[1])], QUESTION
    )
    swapped = compose_question_profile(
        [profile("femur", rows[1]), profile("tibia", rows[0])], QUESTION
    )
    assert tuple(a + b for a, b in zip(*rows, strict=True)) == (2, 1, 7)
    assert original.bundle.layout == swapped.bundle.layout
    assert original.bundle.counts != swapped.bundle.counts
    terms = cosine_terms(
        original.bundle, swapped.bundle, ("object/femur/signal", "object/tibia/signal")
    )
    assert terms.code == CountCode.OK
    assert (terms.terms.dot, terms.terms.left_norm_sq, terms.terms.right_norm_sq) == (
        0,
        54,
        54,
    )
    assert len(original.bundle.layout.banks) == 2  # no fabricated relationship bank


def test_case_id_counts_input_order_and_status_do_not_change_encoding_identity():
    first = compose_question_profile([profile("femur"), profile("tibia")], QUESTION)
    second = compose_question_profile(
        [
            profile("tibia", (0, 8, 13), source="case-B"),
            profile(
                "femur",
                (0, 0, 0),
                source="case-B",
                bank_statuses=(("signal", "unknown"),),
            ),
        ],
        QUESTION,
    )
    assert first.bundle.layout == second.bundle.layout
    assert first.source_id != second.source_id
    assert dict(second.bank_statuses)["object/femur/signal"] == "unknown"
    assert dict(second.provenance)["object/femur/availability"] == "silent"


def test_different_object_counts_use_explicit_template_without_normal_filling():
    layouts = {"femur": LAYOUT, "tibia": LAYOUT}
    complete = compose_question_profile(
        [profile("femur"), profile("tibia", (0, 4, 0))],
        QUESTION,
        source_layouts=layouts,
    )
    partial = compose_question_profile(
        [profile("femur")], QUESTION, source_layouts=layouts
    )
    assert partial.bundle.layout == complete.bundle.layout
    assert partial.bundle.counts == ((2, 0, 0), (0, 0, 0))
    assert dict(partial.bank_statuses)["object/tibia/signal"] == "missing_source_object"
    assert (
        dict(partial.provenance)["object/tibia/availability"] == "missing_source_object"
    )
    terms = cosine_terms(partial.bundle, complete.bundle, ("object/tibia/signal",))
    assert terms.code == CountCode.SILENT


def test_missing_role_does_not_guess_other_objects_reference_declaration():
    with pytest.raises(CompositionError, match="source_layouts_required:tibia"):
        compose_question_profile([profile("femur")], QUESTION)


def test_optional_bank_must_match_declared_layout_and_stays_silent():
    layout = replace(
        LAYOUT,
        banks=LAYOUT.banks + (BankLayout("extent", 3),),
        layout_id="optional-declared",
    )
    femur = replace(
        profile("femur"), bundle=CountBundle(layout, ((2, 0, 0), (0, 0, 0)))
    )
    tibia = replace(
        profile("tibia"), bundle=CountBundle(layout, ((0, 1, 0), (0, 0, 9)))
    )
    result = compose_question_profile(
        [femur, tibia], QUESTION, source_layouts={"femur": layout, "tibia": layout}
    )
    assert dict(result.bank_statuses)["object/femur/extent"] == "silent"
    with pytest.raises(CompositionError, match="incompatible_source_layout:femur"):
        compose_question_profile(
            [profile("femur"), tibia],
            QUESTION,
            source_layouts={"femur": layout, "tibia": layout},
        )


def test_case_boundary_rejects_different_studies_even_when_counts_match():
    with pytest.raises(CompositionError, match="different_cases"):
        compose_question_profile(
            [profile("femur"), profile("tibia", source="case-B")], QUESTION
        )
    with pytest.raises(CompositionError, match="contradictory_source:study_uid"):
        compose_question_profile(
            [
                profile("femur", context=(("study_uid", "A"),)),
                profile("tibia", context=(("study_uid", "B"),)),
            ],
            QUESTION,
        )


def test_role_specific_source_ids_require_common_case_and_preserve_provenance():
    result = compose_question_profile(
        [
            profile(
                "femur",
                source="product/object-femur",
                provenance=(
                    ("study_uid", "A"),
                    ("source_state", "revision-1"),
                    ("array", "native-femur"),
                ),
            ),
            profile(
                "tibia",
                source="product/object-tibia",
                provenance=(
                    ("study_uid", "A"),
                    ("source_state", "revision-1"),
                    ("array", "native-tibia"),
                ),
            ),
        ],
        QUESTION,
    )
    assert result.source_id == "study:A"
    provenance = dict(result.provenance)
    assert provenance["study_uid"] == "A"
    assert provenance["source_state"] == "revision-1"
    assert provenance["source_state_compatibility"] == "declared_agreement"
    assert provenance["case_compatibility"] == "shared_study_uid"
    assert provenance["object/tibia/source_id"] == "product/object-tibia"
    assert json.loads(provenance["object/femur/provenance"])["array"] == "native-femur"


@pytest.mark.parametrize("field", ["study_uid", "source_state"])
def test_source_identity_conflicts_are_never_swallowed(field):
    with pytest.raises(CompositionError, match="contradictory_source"):
        compose_question_profile(
            [
                profile("femur", context=((field, "A"),), provenance=((field, "B"),)),
                profile("tibia"),
            ],
            QUESTION,
        )
    with pytest.raises(CompositionError, match="contradictory_source"):
        compose_question_profile(
            [
                profile("femur", provenance=((field, "A"),)),
                profile("tibia", provenance=((field, "B"),)),
            ],
            QUESTION,
        )
    with pytest.raises(CompositionError, match="missing_source_identity"):
        compose_question_profile(
            [profile("femur", provenance=((field, "A"),)), profile("tibia")], QUESTION
        )


def test_context_is_preserved_and_incompatibility_or_missing_context_named():
    question = replace(QUESTION, context_keys=("acquisition", "side"))
    first = profile("femur", context=(("acquisition", "FS"), ("side", "R")))
    second = profile("tibia", context=(("acquisition", "FS"),))
    result = compose_question_profile([first, second], question)
    assert dict(result.context) == {"acquisition": "FS"}
    provenance = dict(result.provenance)
    assert provenance["context_compatibility"] == "missing:side"
    assert json.loads(provenance["object/femur/context"])["side"] == "R"
    with pytest.raises(CompositionError, match="incompatible_context:acquisition"):
        compose_question_profile(
            [first, replace(second, context=(("acquisition", "nonFS"),))], question
        )


def test_changed_role_reference_identity_stays_in_composite_not_renamed_away():
    original = compose_question_profile([profile("femur"), profile("tibia")], QUESTION)
    different = replace(LAYOUT, layout_id="different-reference")
    changed = compose_question_profile(
        [profile("femur", layout=different), profile("tibia")], QUESTION
    )
    assert changed.bundle.layout.layout_id != original.bundle.layout.layout_id
    assert changed.bundle.layout.carrier_id == original.bundle.layout.carrier_id
    declarations = json.loads(dict(changed.provenance)["source_layouts"])
    assert declarations[0][1]["layout_id"] == "different-reference"
    with pytest.raises(CompositionError, match="incompatible_source_layout:femur"):
        compose_question_profile(
            [profile("femur", layout=different), profile("tibia")],
            QUESTION,
            source_layouts={"femur": LAYOUT, "tibia": LAYOUT},
        )


def test_declared_roles_and_mode_change_identity_but_never_rows():
    inputs = [profile("femur"), profile("tibia")]
    normal = compose_question_profile(inputs, QUESTION)
    cheap = compose_question_profile(
        [replace(p, mode="cheap/raw/v1") for p in inputs], QUESTION
    )
    reordered = compose_question_profile(
        inputs, replace(QUESTION, objects=("tibia", "femur"))
    )
    assert normal.bundle.layout.layout_id != cheap.bundle.layout.layout_id
    assert normal.bundle.layout.layout_id != reordered.bundle.layout.layout_id
    assert cheap.bundle.counts == normal.bundle.counts
    with pytest.raises(CompositionError, match="incompatible_modes"):
        compose_question_profile(
            [inputs[0], replace(inputs[1], mode="cheap/raw/v1")], QUESTION
        )
    with pytest.raises(CompositionError, match="incompatible_carriers"):
        compose_question_profile(
            [
                inputs[0],
                profile("tibia", layout=replace(LAYOUT, carrier_id="another-carrier")),
            ],
            QUESTION,
        )


def test_true_measured_middle_is_distinct_from_silence_and_large_counts_are_exact():
    huge = 2**80 + 7
    result = compose_question_profile(
        [profile("femur", (0, huge, 0)), profile("tibia", (0, 0, 0))], QUESTION
    )
    assert result.bundle.counts == ((0, huge, 0), (0, 0, 0))
    assert dict(result.bank_statuses) == {
        "object/femur/signal": "observed",
        "object/tibia/signal": "silent",
    }


@pytest.mark.parametrize(
    "status", ["unknown", "empty", "missing_reference", "partial", "target_only"]
)
def test_honest_unknown_empty_partial_states_are_retained(status):
    result = compose_question_profile(
        [
            profile("femur", (0, 0, 0), bank_statuses=(("signal", status),)),
            profile("tibia"),
        ],
        QUESTION,
    )
    assert dict(result.bank_statuses)["object/femur/signal"] == status
    assert result.bundle.counts[0] == (0, 0, 0)


@pytest.mark.parametrize(
    "status", ["conflicting", "mismatch", "malformed", "facet_mapping_conflict"]
)
def test_rejects_conflicting_source_status_instead_of_relabelling_it(status):
    with pytest.raises(CompositionError, match="conflicting_source"):
        compose_question_profile(
            [profile("femur", bank_statuses=(("signal", status),)), profile("tibia")],
            QUESTION,
        )
    with pytest.raises(CompositionError, match="conflicting_source"):
        compose_question_profile(
            [
                profile("femur", provenance=(("assembly_status", status),)),
                profile("tibia"),
            ],
            QUESTION,
        )


@pytest.mark.parametrize("bad", [True, -1, 1.0, "1"])
def test_rejects_noninteger_negative_and_boolean_counts(bad):
    with pytest.raises(CompositionError, match="invalid_bundle:femur"):
        compose_question_profile(
            [profile("femur", (bad, 0, 0)), profile("tibia")], QUESTION
        )


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"bank_statuses": (("unknown_bank", "silent"),)}, "unknown_status_bank"),
        ({"bank_statuses": (("signal", "silent"),)}, "contradictory_source_status"),
        (
            {"bank_statuses": (("signal", "observed"), ("signal", "silent"))},
            "duplicate_bank_statuses",
        ),
        ({"context": (("side", "R"), ("side", "L"))}, "duplicate_context"),
        (
            {"provenance": (("study_uid", "A"), ("study_uid", "B"))},
            "duplicate_provenance",
        ),
        ({"scope": "region:"}, "incompatible_scope"),
        ({"source_id": ""}, "invalid_source"),
        ({"mode": ""}, "invalid_source"),
    ],
)
def test_malformed_metadata_rejected(changes, reason):
    with pytest.raises(CompositionError, match=reason):
        compose_question_profile(
            [replace(profile("femur"), **changes), profile("tibia")], QUESTION
        )


def test_no_duplicate_roles_or_empty_invented_case():
    with pytest.raises(CompositionError, match="duplicate_object:femur"):
        compose_question_profile(
            [profile("femur"), profile("femur"), profile("tibia")], QUESTION
        )
    with pytest.raises(CompositionError, match="no_source_profiles"):
        compose_question_profile(
            [], QUESTION, source_layouts={"femur": LAYOUT, "tibia": LAYOUT}
        )
    with pytest.raises(CompositionError, match="invalid_profile"):
        compose_question_profile([None], QUESTION)
    with pytest.raises(CompositionError, match="invalid_profiles"):
        compose_question_profile("not profiles", QUESTION)


@pytest.mark.parametrize(
    "templates", [{}, {"femur": LAYOUT}, {"femur": LAYOUT, "tibia": None}]
)
def test_invalid_template_refused(templates):
    with pytest.raises(CompositionError, match="invalid_source_layouts"):
        compose_question_profile(
            [profile("femur"), profile("tibia")], QUESTION, source_layouts=templates
        )


@pytest.mark.parametrize(
    "question",
    [
        None,
        replace(QUESTION, subject="fracture"),
        replace(QUESTION, objects=()),
        replace(QUESTION, objects=("femur", "femur")),
        replace(QUESTION, objects=("femur/signal",)),
        replace(QUESTION, context_keys=("side", "side")),
    ],
)
def test_malformed_question_refused(question):
    with pytest.raises(CompositionError, match="invalid_question"):
        compose_question_profile([profile("femur"), profile("tibia")], question)


def test_unrelated_catalogue_objects_are_not_added_to_question():
    result = compose_question_profile(
        [profile("patella"), profile("femur"), profile("tibia")], QUESTION
    )
    assert len(result.bundle.layout.banks) == 2


@pytest.mark.parametrize(
    "status,speaks,expected",
    [
        ("conflicting", True, "conflicting_source"),
        ("mismatch", False, "conflicting_source"),
        ("malformed", False, "conflicting_source"),
        ("facet_mapping_conflict", False, "conflicting_source"),
        ("silent", True, "contradictory_source_status"),
        ("missing_source_object", True, "contradictory_source_status"),
        ("ok", True, "observed"),
        ("unknown", False, "silent"),
    ],
)
def test_pure_status_decision_both_signs(status, speaks, expected):
    assert source_status_code(status, speaks) == expected


def test_real_canonical_expanded_facets_are_copied_without_row_reencoding():
    base = LayoutSpec(
        "test-native/v1",
        "declared-base",
        (
            BankSpec(
                "signal",
                "acquired",
                (MetricSpec("low", MetricKind.WORDS, ("False", "True")),),
            ),
        ),
    )
    preparation = prepare_composition(
        base,
        [
            {
                "object": name,
                "provenance": "native",
                "kind": "reading",
                "support": "native_support",
                "references": [],
            }
            for name in QUESTION.objects
        ],
        {
            "version": "v1",
            "view_roles": [["Sagittal", "1", "1"], ["Coronal", "0", "0"]],
            "bank_plans": [
                {"base_bank": "signal", "lens": "acquired", "scale_scope": "series"}
            ],
        },
    )
    assert preparation.prepared is not None
    prepared = preparation.prepared
    inputs = []
    for index, role in enumerate(QUESTION.objects):
        layout = prepared.profile_layouts[role].count_layout
        rows = tuple(
            tuple((index + 2) if row == bank_index else 0 for row in range(512))
            for bank_index, bank in enumerate(layout.banks)
        )
        inputs.append(
            Profile(
                role,
                CountBundle(layout, rows),
                "full",
                "object:" + role,
                "canonical-study",
            )
        )
    result = compose_question_profile(inputs, QUESTION)
    assert result.bundle.counts == inputs[0].bundle.counts + inputs[1].bundle.counts
    names = tuple(bank.name for bank in result.bundle.layout.banks)
    assert names == tuple(
        f"object/{p.subject}/{b.name}" for p in inputs for b in p.bundle.layout.banks
    )
    assert all(bank.row_count == 512 for bank in result.bundle.layout.banks)
    declarations = json.loads(dict(result.provenance)["source_layouts"])
    assert declarations[0][1]["carrier_id"] == prepared.carrier.identity
    assert declarations[1][1]["layout_id"] == inputs[1].bundle.layout.layout_id


def test_contradictory_layout_or_carrier_declarations_refused():
    forged = replace(LAYOUT, banks=(BankLayout("other", 3),))
    with pytest.raises(CompositionError, match="contradictory_layout_identity"):
        compose_question_profile(
            [profile("femur"), profile("tibia", layout=forged)], QUESTION
        )
    different_layout = replace(forged, layout_id="another-layout")
    with pytest.raises(CompositionError, match="contradictory_carrier_banks"):
        compose_question_profile(
            [profile("femur"), profile("tibia", layout=different_layout)], QUESTION
        )


def test_empty_status_is_malformed_not_a_silent_normal_vote():
    with pytest.raises(CompositionError, match="invalid_bank_status"):
        compose_question_profile(
            [profile("femur", bank_statuses=(("signal", ""),)), profile("tibia")],
            QUESTION,
        )


def test_acquisition_metadata_is_not_a_diagnosis_or_encoding_identity():
    fs = compose_question_profile(
        [profile(name, context=(("acquisition", "FS"),)) for name in QUESTION.objects],
        QUESTION,
    )
    nonfs = compose_question_profile(
        [
            profile(name, context=(("acquisition", "non-FS"),))
            for name in QUESTION.objects
        ],
        QUESTION,
    )
    assert fs.bundle == nonfs.bundle
    assert fs.context == nonfs.context
    assert dict(fs.provenance)["object/femur/acquisition"] == "FS"
    assert dict(nonfs.provenance)["object/femur/acquisition"] == "non-FS"
    assert not any("diagnosis" in bank.name for bank in fs.bundle.layout.banks)


def test_blank_declared_context_is_named_missing_with_original_value_retained():
    result = compose_question_profile(
        [profile(name, context=(("side", ""),)) for name in QUESTION.objects],
        replace(QUESTION, context_keys=("side",)),
    )
    assert dict(result.context)["side"] == ""
    assert dict(result.provenance)["context_compatibility"] == "missing:side"


def test_count_direct_sum_agrees_with_original_carrier_vectors_exactly():
    import numpy as np

    from knee.encoding.carrier import HadamardCarrier

    carrier = HadamardCarrier.from_banks(("signal",))
    layout = CountLayout(
        "reference-declaration", carrier.identity, (BankLayout("signal", 512),)
    )
    left_rows = ((2, 1) + (0,) * 510, (0, 7) + (0,) * 510)
    right_rows = ((3, 0) + (0,) * 510, (1, 2) + (0,) * 510)
    left = compose_question_profile(
        [
            profile(name, row, layout=layout)
            for name, row in zip(QUESTION.objects, left_rows, strict=True)
        ],
        QUESTION,
    )
    right = compose_question_profile(
        [
            profile(name, row, layout=layout)
            for name, row in zip(QUESTION.objects, right_rows, strict=True)
        ],
        QUESTION,
    )
    terms = cosine_terms(
        left.bundle, right.bundle, tuple(b.name for b in left.bundle.layout.banks)
    ).terms
    lv = np.concatenate(
        [
            carrier.encode(np.array([row], dtype=np.int64)).reshape(-1)
            for row in left_rows
        ]
    ).astype(np.int64)
    rv = np.concatenate(
        [
            carrier.encode(np.array([row], dtype=np.int64)).reshape(-1)
            for row in right_rows
        ]
    ).astype(np.int64)
    assert int(lv @ rv) == 512 * terms.dot
    assert int(lv @ lv) == 512 * terms.left_norm_sq
    assert int(rv @ rv) == 512 * terms.right_norm_sq


def test_product_composition_scope_is_retained_and_bound_to_layout_fingerprint():
    product_layout = replace(LAYOUT, layout_id="retained-v1:fp-native:reference-v1")
    femur = replace(
        profile("femur", layout=product_layout),
        scope="object:femur;composition:fp-native",
        provenance=(("layout_fingerprint", "fp-native"),),
    )
    tibia = profile("tibia", layout=product_layout)

    result = compose_question_profile([femur, tibia], QUESTION)

    assert (
        dict(result.provenance)["object/femur/scope"]
        == "object:femur;composition:fp-native"
    )
    plain_object_scope = compose_question_profile(
        [profile("femur", layout=product_layout), tibia], QUESTION
    )
    assert result.bundle.layout.layout_id != plain_object_scope.bundle.layout.layout_id
    mismatch = replace(femur, provenance=(("layout_fingerprint", "other-fingerprint"),))
    with pytest.raises(CompositionError, match="incompatible_scope_identity:femur"):
        compose_question_profile([mismatch, tibia], QUESTION)


def test_cheap_region_scope_is_preserved_per_role_and_changes_identity():
    femur = replace(
        profile("femur"), mode="cheap", scope="region:coarse-femur-window-v1"
    )
    tibia = replace(
        profile("tibia"), mode="cheap", scope="region:coarse-tibia-window-v1"
    )
    changed_femur = replace(femur, scope="region:different-femur-window-v1")

    first = compose_question_profile([femur, tibia], QUESTION)
    changed = compose_question_profile([changed_femur, tibia], QUESTION)

    provenance = dict(first.provenance)
    assert provenance["object/femur/scope"] == "region:coarse-femur-window-v1"
    assert provenance["object/tibia/scope"] == "region:coarse-tibia-window-v1"
    assert first.bundle.layout.layout_id != changed.bundle.layout.layout_id


def test_per_role_object_and_assembly_statuses_do_not_contradict_the_case():
    shared = (("study_uid", "study-1"), ("source_state", "receipt-1"))
    femur = replace(
        profile("femur"),
        context=(
            ("object_status", "normal"),
            ("assembly_status", "normal"),
            ("study_uid", "study-1"),
            ("source_state", "receipt-1"),
        ),
        provenance=shared
        + (("object_status", "normal"), ("assembly_status", "normal")),
    )
    tibia = replace(
        profile("tibia"),
        context=(
            ("object_status", "partial"),
            ("assembly_status", "silent"),
            ("study_uid", "study-1"),
            ("source_state", "receipt-1"),
        ),
        provenance=shared
        + (("object_status", "partial"), ("assembly_status", "silent")),
    )

    result = compose_question_profile([femur, tibia], QUESTION)

    provenance = dict(result.provenance)
    assert provenance["object/femur/object_status"] == "normal"
    assert provenance["object/tibia/object_status"] == "partial"
    assert provenance["object/femur/assembly_status"] == "normal"
    assert provenance["object/tibia/assembly_status"] == "silent"
    assert provenance["study_uid"] == "study-1"
    assert provenance["source_state"] == "receipt-1"


def test_only_declared_question_context_keys_are_globally_compared():
    first = profile(
        "femur", context=(("object_status", "normal"), ("acquisition", "FS"))
    )
    second = profile(
        "tibia", context=(("object_status", "partial"), ("acquisition", "FS"))
    )
    result = compose_question_profile([first, second], QUESTION)
    assert result.context == ()
    assert dict(result.provenance)["object/femur/object_status"] == "normal"
    with pytest.raises(CompositionError, match="incompatible_context:acquisition"):
        compose_question_profile(
            [
                first,
                replace(
                    second,
                    context=(("object_status", "partial"), ("acquisition", "non-FS")),
                ),
            ],
            replace(QUESTION, context_keys=("acquisition",)),
        )


def test_prepared_composition_reuses_layout_and_missing_zero_rows_for_run_lifetime():
    question = QUESTION
    prepared = prepare_diagnostic_composition(
        question, {"femur": LAYOUT, "tibia": LAYOUT}
    )
    assert isinstance(prepared, PreparedComposition)
    first = prepared.compose([profile("femur", source="study-A")])
    second = prepared.compose([profile("femur", source="study-B")])

    assert first.bundle.layout is second.bundle.layout
    assert first.bundle.counts[1] is second.bundle.counts[1]
    assert not any(first.bundle.counts[1])
    assert first.source_id != second.source_id


def test_declared_study_split_and_source_group_survive_composition_and_teaching():
    femur = profile(
        "femur",
        context=(("study_uid", "study-A"), ("split", "train")),
        provenance=(("source_group", "patient-group-7"),),
    )
    tibia = profile("tibia", context=(("study_uid", "study-A"),))

    composite = compose_question_profile([femur, tibia], QUESTION)
    snapshot, receipt = teach_from_labels(
        {"study-A": [composite]},
        {"study-A": {"Fracture": 1}},
        revision="grouped-r1",
    )

    provenance = dict(composite.provenance)
    assert provenance["split"] == "train"
    assert provenance["source_group"] == "patient-group-7"
    no_group_composite = compose_question_profile(
        [
            profile("femur", context=(("study_uid", "study-A"),)),
            tibia,
        ],
        QUESTION,
    )
    assert composite.bundle.layout == no_group_composite.bundle.layout
    assert composite.bundle.counts == no_group_composite.bundle.counts
    assert len(snapshot.cases) == 1
    assert receipt["studies"] == [
        {
            "study_uid": "study-A",
            "split": "train",
            "source_group": "patient-group-7",
            "all_blank": False,
        }
    ]
    assert receipt["exclude_source_groups"] == ["patient-group-7"]
    fracture_entry = next(
        entry for entry in receipt["ledger"] if entry["question"] == "Fracture"
    )
    assert fracture_entry["split"] == "train"
    assert fracture_entry["source_group"] == "patient-group-7"
    assert json.loads(snapshot.cases[0].calls[0].words)["source_group"] == (
        "patient-group-7"
    )


@pytest.mark.parametrize("field", ["split", "source_group"])
def test_declared_group_metadata_conflicts_are_refused(field):
    with pytest.raises(CompositionError, match=f"contradictory_source:{field}"):
        compose_question_profile(
            [
                profile("femur", context=((field, "group-A"),)),
                profile("tibia", provenance=((field, "group-B"),)),
            ],
            QUESTION,
        )
    with pytest.raises(CompositionError, match=f"contradictory_source:.*:{field}"):
        compose_question_profile(
            [
                profile(
                    "femur",
                    context=((field, "group-A"),),
                    provenance=((field, "group-B"),),
                ),
                profile("tibia"),
            ],
            QUESTION,
        )


def test_undeclared_groups_stay_unknown_and_unrelated_profiles_do_not_compose():
    composite = compose_question_profile([profile("femur"), profile("tibia")], QUESTION)
    _, receipt = teach_from_labels(
        {"case-A": [composite]},
        {"case-A": {"Fracture": 1}},
        revision="unknown-group-r1",
    )
    assert "split" not in dict(composite.provenance)
    assert "source_group" not in dict(composite.provenance)
    assert receipt["studies"][0]["split"] is None
    assert receipt["studies"][0]["source_group"] is None
    assert receipt["exclude_source_groups"] == []
    with pytest.raises(CompositionError, match="different_cases"):
        compose_question_profile(
            [
                profile(
                    "femur",
                    source="unrelated-A",
                    provenance=(("source_group", "patient-group-7"),),
                ),
                profile("tibia", source="unrelated-B"),
            ],
            QUESTION,
        )
