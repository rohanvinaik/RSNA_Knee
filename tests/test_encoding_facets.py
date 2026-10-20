from __future__ import annotations

from knee.encoding.facets import (
    MPS_DIRECTIONS,
    BankFacetPlan,
    expand_facets,
)
from knee.encoding.places import (
    BankSpec,
    LayoutSpec,
    MetricKind,
    MetricSpec,
)

V_SAG_FLUID_FS = ("sagittal", "fluid", "fat_suppressed")
V_SAG_FLUID_NONFS = ("sagittal", "fluid", "not_fat_suppressed")
V_COR_FLUID_FS = ("coronal", "fluid", "fat_suppressed")


def base_spec() -> LayoutSpec:
    return LayoutSpec(
        "knee-base-v1",
        "carrier-v1",
        (
            BankSpec(
                "light",
                "brightness",
                (
                    MetricSpec("level", MetricKind.DIGIT),
                    MetricSpec("tag", MetricKind.WORDS, ("inside", "outside")),
                ),
            ),
            BankSpec("extent", "support", (MetricSpec("area", MetricKind.DIGIT),)),
        ),
    )


def plans() -> tuple[BankFacetPlan, ...]:
    return (
        BankFacetPlan("light", "raw_light", "native_plane"),
        BankFacetPlan("extent", "interior", "native_support"),
    )


def test_expansion_covers_declared_views_and_all_28_direction_states_in_stable_order():
    views = (V_SAG_FLUID_FS, V_SAG_FLUID_NONFS, V_COR_FLUID_FS)
    result = expand_facets(base_spec(), views, plans())
    assert result.code.value == "ok"
    expanded = result.expansion
    assert expanded is not None
    assert len(MPS_DIRECTIONS) == 27
    assert len(expanded.layout_spec.banks) == 2 * len(views) * 28
    assert expanded.layout_spec.version == "knee-base-v1"
    assert expanded.layout_spec.carrier_id == "carrier-v1"
    assert (
        tuple(item.view_role for item in expanded.registry[:28])
        == (V_SAG_FLUID_FS,) * 28
    )
    assert tuple(item.direction for item in expanded.registry[:28]) == (
        None,
        *MPS_DIRECTIONS,
    )
    assert expanded.registry[28].view_role == V_SAG_FLUID_NONFS
    assert expanded.registry[56].view_role == V_COR_FLUID_FS
    assert len({item.bank for item in expanded.registry}) == len(expanded.registry)


def test_contrast_and_fat_suppression_views_remain_distinct():
    result = expand_facets(base_spec(), (V_SAG_FLUID_FS, V_SAG_FLUID_NONFS), plans())
    assert result.code.value == "ok"
    expanded = result.expansion
    assert expanded is not None
    assert expanded.bank_for("light", V_SAG_FLUID_FS, (0, 0, 0)) != expanded.bank_for(
        "light", V_SAG_FLUID_NONFS, (0, 0, 0)
    )
    assert expanded.bank_for("light", V_SAG_FLUID_FS, None) != expanded.bank_for(
        "light", V_SAG_FLUID_NONFS, None
    )


def test_known_direction_contributes_to_overview_and_its_conditioned_bank():
    result = expand_facets(base_spec(), (V_SAG_FLUID_FS,), plans())
    assert result.code.value == "ok"
    expanded = result.expansion
    assert expanded is not None
    overview = expanded.bank_for("light", V_SAG_FLUID_FS, None)
    center = expanded.bank_for("light", V_SAG_FLUID_FS, (0, 0, 0))
    oblique = expanded.bank_for("light", V_SAG_FLUID_FS, (-1, 1, 0))
    assert expanded.banks_for_reading("light", V_SAG_FLUID_FS, None) == (overview,)
    assert expanded.banks_for_reading("light", V_SAG_FLUID_FS, (0, 0, 0)) == (
        overview,
        center,
    )
    assert expanded.banks_for_reading("light", V_SAG_FLUID_FS, (-1, 1, 0)) == (
        overview,
        oblique,
    )
    assert len({overview, center, oblique}) == 3


def test_layout_expansion_preserves_base_metrics_words_order_and_facet_label():
    base = base_spec()
    result = expand_facets(base, (V_SAG_FLUID_FS,), plans())
    assert result.code.value == "ok"
    expanded = result.expansion
    assert expanded is not None
    assert expanded.layout_spec.banks[0].metrics == base.banks[0].metrics
    assert expanded.layout_spec.banks[0].facet == base.banks[0].facet
    assert (
        tuple(bank.facet for bank in expanded.layout_spec.banks[:28])
        == ("brightness",) * 28
    )
    assert expanded.layout_spec.banks[0].metrics[1].words == ("inside", "outside")
    assert base.version == "knee-base-v1" and len(base.banks) == 2


def test_registry_records_are_directly_convertible_to_shared_bankfacet_fields():
    result = expand_facets(base_spec(), (V_SAG_FLUID_FS,), plans())
    assert result.code.value == "ok"
    expanded = result.expansion
    assert expanded is not None
    record = expanded.registry[0].as_record()
    assert record == {
        "bank": expanded.registry[0].bank,
        "coordinate": {
            "view_role": V_SAG_FLUID_FS,
            "lens": "raw_light",
            "scale": "native_plane",
            "direction": None,
        },
    }


def test_output_is_declaration_stable_and_has_no_study_uid_dependency():
    a = expand_facets(base_spec(), (V_SAG_FLUID_FS, V_COR_FLUID_FS), plans())
    b = expand_facets(base_spec(), (V_SAG_FLUID_FS, V_COR_FLUID_FS), plans())
    assert a == b and a.code.value == "ok"
    assert a.expansion is not None
    assert all(not hasattr(entry, "study_uid") for entry in a.expansion.registry)


def test_duplicate_or_missing_declarations_and_views_are_named_by_refusal():
    base = base_spec()
    assert expand_facets(base, (), plans()).code.value == "invalid_view_roles"
    assert (
        expand_facets(base, (V_SAG_FLUID_FS, V_SAG_FLUID_FS), plans()).code.value
        == "duplicate_view_role"
    )
    assert (
        expand_facets(base, (V_SAG_FLUID_FS,), (plans()[0],)).code.value
        == "incomplete_bank_plans"
    )
    assert (
        expand_facets(base, (V_SAG_FLUID_FS,), (*plans(), plans()[0])).code.value
        == "duplicate_bank_plan"
    )
    assert (
        expand_facets(
            base, (V_SAG_FLUID_FS,), (BankFacetPlan("unlisted", "x", "y"), plans()[1])
        ).code.value
        == "unknown_base_bank"
    )


def test_bad_view_or_direction_does_not_collapse_to_another_facet():
    base = base_spec()
    assert (
        expand_facets(base, (("sagittal", "fluid"),), plans()).code.value
        == "invalid_view_role"
    )
    result = expand_facets(base, (V_SAG_FLUID_FS,), plans())
    assert result.code.value == "ok"
    expanded = result.expansion
    assert expanded is not None
    assert expanded.bank_for("light", V_SAG_FLUID_FS, (True, 0, 0)) is None
    assert expanded.banks_for_reading("light", V_SAG_FLUID_FS, (1.0, 0, 0)) is None
    assert expanded.bank_for("light", V_SAG_FLUID_FS, (0, 0, 0)) != expanded.bank_for(
        "light", V_SAG_FLUID_FS, None
    )


def test_scale_scope_is_explicit_and_unchanged_across_direction_conditioning():
    result = expand_facets(base_spec(), (V_SAG_FLUID_FS,), plans())
    assert result.code.value == "ok"
    expanded = result.expansion
    assert expanded is not None
    overview = expanded.bank_for("light", V_SAG_FLUID_FS, None)
    directional = expanded.bank_for("light", V_SAG_FLUID_FS, (1, 0, -1))
    entries = {entry.bank: entry for entry in expanded.registry}
    assert entries[overview].scale == "native_plane"
    assert entries[directional].scale == "native_plane"
    assert entries[overview].scale == entries[directional].scale
