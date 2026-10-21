from knee.collapse._atlas_reference import ANTERIOR_CONTACTS_LPS_MM
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


def test_study_catalogue_keeps_cartilage_unobserved_and_diffuse_gaps_explicit():
    sites = reference_sites()
    for name in ("patellar_cartilage", "trochlear_cartilage"):
        assert name in OBJECTS
        site = sites[name]
        assert site.status == "anatomical_reference"
        assert site.point_mps_mm is not None
        assert site.span_mm is not None
        assert site.construction == "between_anatomical_neighbours"
        assert all(
            plane["kind"] == "anatomical_construction" for plane in site.key_planes
        )
        assert "not cartilage thickness" in site.reason
        assert ideal_vector(name, "patella") is not None
        assert ideal_vector(name, "femur") is not None

    for name in ("air", "skin", "muscle"):
        assert sites[name].status == "reference_not_defined"
        assert sites[name].point_mps_mm is None
        assert sites[name].span_mm is None

    record = StudyMap().record()
    for name in ("patellar_cartilage", "trochlear_cartilage"):
        assert name in record["objects"]
        assert record["objects"][name]["status"] != "complete"
        assert all(
            plane["outcome"] == "not_supplied"
            for plane in record["objects"][name]["key_planes"].values()
        )


def test_patellar_and_trochlear_guides_use_existing_facing_contacts():
    sites = reference_sites()
    patella = sites["patella"].point_mps_mm
    patella_span = sites["patella"].span_mm
    assert patella is not None and patella_span is not None
    femur_front = ANTERIOR_CONTACTS_LPS_MM["femur_at_patella"][1]
    patella_back = ANTERIOR_CONTACTS_LPS_MM["patella_back_at_patella"][1]
    broad_search_span = (
        patella_span[0],
        abs(patella_back - femur_front),
        patella_span[2],
    )

    patellar = sites["patellar_cartilage"]
    trochlear = sites["trochlear_cartilage"]
    assert patellar.point_mps_mm == (patella[0], patella_back, patella[2])
    assert trochlear.point_mps_mm == (patella[0], femur_front, patella[2])
    assert patellar.span_mm == broad_search_span
    assert trochlear.span_mm == broad_search_span
    assert patellar.point_mps_mm[1] == patella_back
    assert trochlear.point_mps_mm[1] == femur_front
    assert "search guide" in patellar.reason
    assert "search guide" in trochlear.reason
    assert "measured boundary" in patellar.reason
    assert "extracted cartilage label" in trochlear.reason

    expected = tuple(
        sites["patella"].point_mps_mm[i] - patellar.point_mps_mm[i] for i in range(3)
    )
    assert ideal_vector("patellar_cartilage", "patella").anatomical_mm == expected


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
