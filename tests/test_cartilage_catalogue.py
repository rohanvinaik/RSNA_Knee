from knee.collapse.anatomical_relations import relationships_for
from knee.collapse.anatomy_map import ideal_vector, reference_sites
from knee.collapse.study_map import OBJECTS, StudyMap
from knee.encoding.mri_spec import make_mri_spec
from knee.objects.assignments import CARTILAGES, OBJECT_CODES


def test_cartilage_names_append_without_renumbering_existing_objects():
    assert OBJECT_CODES["sartorius"] == 42
    assert OBJECT_CODES["patellar_cartilage"] == 43
    assert OBJECT_CODES["trochlear_cartilage"] == 44
    assert CARTILAGES[-2:] == ("patellar_cartilage", "trochlear_cartilage")
    assert len([name for name in OBJECT_CODES if name != "unassigned"]) == 44


def test_study_and_reference_catalogues_include_named_unresolved_cartilage():
    for name in ("patellar_cartilage", "trochlear_cartilage"):
        assert name in OBJECTS
        site = reference_sites()[name]
        assert site.status == "reference_not_defined"
        assert site.point_mps_mm is None
        assert site.span_mm is None
        assert ideal_vector(name, "patella") is None
        assert ideal_vector(name, "femur") is None

    record = StudyMap().record()
    for name in ("patellar_cartilage", "trochlear_cartilage"):
        assert name in record["objects"]
        assert record["objects"][name]["status"] != "complete"
        assert all(
            plane["outcome"] == "not_supplied"
            for plane in record["objects"][name]["key_planes"].values()
        )


def test_surface_relations_are_authored_definitions_not_map_measurements():
    relations = relationships_for(
        ("patellar_cartilage", "trochlear_cartilage", "patella", "femur")
    )
    patellar = relations["patellar_cartilage"][0]
    trochlear = relations["trochlear_cartilage"][0]
    assert (patellar["predicate"], patellar["targets"]) == ("covers", ["patella"])
    assert patellar["qualifier"] == "posterior articular surface"
    assert (trochlear["predicate"], trochlear["targets"]) == ("covers", ["femur"])
    assert trochlear["qualifier"] == "facing trochlear articular surface"
    assert patellar["basis"] == trochlear["basis"] == "anatomical_definition"
    assert "OBJECTS_AND_CONDITIONS.md §4" in patellar["source"]


def test_builtin_spec_accounts_for_both_new_object_names():
    declaration = make_mri_spec(view=("Axial", "1", "1"))
    objects = {profile["object"] for profile in declaration["profiles"]}
    assert {"patellar_cartilage", "trochlear_cartilage"} <= objects
