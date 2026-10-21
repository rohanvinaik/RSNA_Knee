"""The reference's anatomical and dimensional obligations, independent of study data."""

import math

import numpy as np
import pytest

from knee.collapse.anatomy_map import (
    MAP_OBJECTS,
    REFERENCE_BREADTH_MM,
    ideal_vector,
    reference_sites,
    target_span_mm,
)
from knee.collapse.relative import expected_point, key_plane, reference_position
from knee.objects.assignments import OBJECT_CODES


def test_reference_covers_every_named_object_without_fabricating_field_locations():
    sites = reference_sites()
    assert set(sites) == (set(OBJECT_CODES) - {"unassigned"}) | {"recess"}
    assert set(MAP_OBJECTS) == set(sites)
    assert {name for name, site in sites.items() if site.point_mps_mm is None} == {
        "air",
        "skin",
        "muscle",
        "subcutaneous_fat",
    }
    assert ideal_vector("air", "femur") is None
    assert ideal_vector("femur", "air") is None
    assert all(site.source and site.reason for site in sites.values())


def test_anatomical_directions_and_relations_remain_visible():
    sites = reference_sites()

    def p(name):
        value = sites[name].point_mps_mm
        assert value is not None
        return np.asarray(value)

    assert p("patella")[1] < p("femur")[1]  # anterior
    assert p("femur")[2] > p("tibia")[2]
    assert p("medial_meniscus")[0] > p("lateral_meniscus")[0]
    assert p("mcl")[0] > p("lcl")[0]
    assert p("fibula")[0] < p("tibia")[0]  # lateral
    assert p("popliteal_artery")[1] < p("popliteal_vein")[1]
    assert p("quadriceps_fat_pad")[1] < p("prefemoral_fat_pad")[1]
    assert p("quadriceps_tendon")[2] > p("patella")[2]
    assert p("semimembranosus")[0] > 0
    assert p("semimembranosus")[1] > p("tibia")[1]
    np.testing.assert_allclose(
        p("gastrocnemius_semimembranosus_bursa"),
        (p("semimembranosus") + p("medial_gastrocnemius")) / 2,
    )
    assert sites["semimembranosus"].construction == "between_anatomical_neighbours"
    assert sites["semimembranosus"].key_planes[0]["kind"] == "anatomical_construction"


def test_every_pair_uses_one_coherent_reference_and_keeps_scale():
    sites = reference_sites()
    nodes = [name for name, site in sites.items() if site.point_mps_mm is not None]
    for a in nodes:
        for b in nodes:
            ab = ideal_vector(a, b)
            ba = ideal_vector(b, a)
            doubled = ideal_vector(a, b, REFERENCE_BREADTH_MM * 2)
            assert ab is not None and ba is not None and doubled is not None
            np.testing.assert_allclose(
                ab.anatomical_mm, -np.asarray(ba.anatomical_mm), atol=1e-12
            )
            np.testing.assert_allclose(
                doubled.anatomical_mm, np.asarray(ab.anatomical_mm) * 2
            )
            # The bones are ordinary nodes; paths through either bone compose to
            # the same displacement, rather than maintaining unrelated maps.
            af = ideal_vector(a, "femur")
            fb = ideal_vector("femur", b)
            assert af is not None and fb is not None
            np.testing.assert_allclose(
                np.asarray(af.anatomical_mm) + fb.anatomical_mm,
                ab.anatomical_mm,
                atol=1e-12,
            )
    assert target_span_mm("patella", REFERENCE_BREADTH_MM * 2) == pytest.approx(
        np.asarray(target_span_mm("patella")) * 2
    )


@pytest.mark.parametrize("scale", [0, -1, math.inf, math.nan])
def test_invalid_scale_cannot_create_an_expected_point(scale):
    with pytest.raises(ValueError):
        ideal_vector("femur", "patella", scale)


def test_one_reference_serves_both_knees_from_three_observed_planes():
    planes = [
        key_plane(
            "femur",
            orientation,
            series_uid=orientation,
            slice=2,
            normal=normal,
            origin_lps=(10, 20, 30),
            reason="test observed key plane",
        )
        for orientation, normal in (
            ("sagittal", (1, 0, 0)),
            ("coronal", (0, 1, 0)),
            ("axial", (0, 0, 1)),
        )
    ]
    observed = reference_position("femur", planes)
    ideal = ideal_vector("femur", "patella")
    assert ideal is not None
    right = expected_point(observed, ideal, "R")
    left = expected_point(observed, ideal, "L")
    assert right.point_lps is not None and left.point_lps is not None
    assert right.point_lps[0] - 10 == pytest.approx(10 - left.point_lps[0])
    assert right.point_lps[1:] == pytest.approx(left.point_lps[1:])
    assert right.point_lps[1] < 20
    assert right.point_lps[2] > 30


def test_interstitial_guides_use_facing_surfaces_not_bone_reference_centres():
    sites = reference_sites()
    recess = sites["anterior_synovial_recess"].point_mps_mm
    quadriceps = sites["quadriceps_fat_pad"].point_mps_mm
    prefemoral = sites["prefemoral_fat_pad"].point_mps_mm
    tendon = sites["quadriceps_tendon"].point_mps_mm
    assert (
        recess is not None
        and quadriceps is not None
        and prefemoral is not None
        and tendon is not None
    )
    # Independent source-label boundary measurements, atlas i282/k80:
    # posterior patellar surface and anterior femoral surface.
    assert -25.65396818 < recess[1] < -20.38450445
    # At superior pole S43.5, the two adjacent femoral front surfaces
    # bound the interpolated cortex. Both pads must stay anterior to it.
    assert tendon[1] < quadriceps[1] < prefemoral[1] < -19.27514366
    assert quadriceps[0] == prefemoral[0] == tendon[0]
    assert "SPL" in sites["prefemoral_fat_pad"].source
