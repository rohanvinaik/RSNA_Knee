"""Three key planes -> position -> pair vectors -> expected slice and in-plane place (`knee.collapse.relative`)."""

import math

import numpy as np
import pytest

from knee.collapse import relative as rel
from knee.collapse.physical import PlaneFrame
from scripts import key_points as kp

AXIAL = (1, 0, 0, 0, 1, 0)


def rotation(ax: float, ay: float, az: float) -> np.ndarray:
    cx, sx, cy, sy, cz, sz = (
        math.cos(ax),
        math.sin(ax),
        math.cos(ay),
        math.sin(ay),
        math.cos(az),
        math.sin(az),
    )
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry @ rx


def plane(obj, orientation, normal, through, **kw):
    return rel.key_plane(
        obj,
        orientation,
        series_uid=kw.pop("series_uid", "s-" + orientation),
        slice=kw.pop("slice", 3),
        normal=normal,
        origin_lps=through,
        **kw,
    )


def triple(obj, normals, point, **kw):
    return [
        plane(obj, o, n, point, **kw)
        for o, n in zip(rel.ORIENTATIONS, normals, strict=True)
    ]


OBLIQUE = [(1.0, 0.2, -0.1), (0.15, 1.0, 0.3), (-0.2, 0.1, 1.0)]
POINT = (12.5, -40.0, 133.25)


def test_oblique_planes_intersect_at_the_point_they_all_contain():
    p = rel.reference_position("femur", triple("femur", OBLIQUE, POINT))
    assert p.status == rel.COMPLETE and p.geometry == "ok" and p.rank == 3
    assert p.point_lps == pytest.approx(POINT, abs=1e-9)
    assert p.frame == "LPS"


def test_unit_normal_scale_and_origin_slide_in_plane_change_nothing():
    # each plane built from a different, arbitrary in-plane origin (the "centroid" of nothing) and a scaled normal
    rng = np.random.default_rng(1)
    planes = []
    for o, n in zip(rel.ORIENTATIONS, OBLIQUE, strict=True):
        n = np.asarray(n)
        u = np.cross(n, [0.3, -0.7, 0.5])
        v = np.cross(n, u)
        slide = rng.normal(size=2) * 50
        origin = np.asarray(POINT) + slide[0] * u + slide[1] * v
        planes.append(plane("femur", o, n * 7.5, origin))
    assert rel.reference_position("femur", planes).point_lps == pytest.approx(
        POINT, abs=1e-8
    )


def test_offset_given_for_a_nonunit_normal_is_that_normals_offset():
    n = np.array(OBLIQUE[0]) * 3.0
    d = float(n @ POINT)
    a = rel.key_plane("x", "sagittal", series_uid="s", slice=0, normal=n, offset_mm=d)
    b = plane("x", "sagittal", OBLIQUE[0], POINT)
    assert a.offset_mm == pytest.approx(b.offset_mm)
    assert a.normal == pytest.approx(b.normal)


def test_extreme_finite_normal_and_offset_are_normalized_without_overflow():
    ordinary = rel.key_plane(
        "x", "axial", series_uid="s", slice=0, normal=(1, 1, 1), offset_mm=1.0
    )
    extreme = rel.key_plane(
        "x",
        "axial",
        series_uid="s",
        slice=0,
        normal=(1.79e308, 1.79e308, 1.79e308),
        offset_mm=1.79e308,
    )
    assert extreme.outcome == rel.SELECTED
    assert np.linalg.norm(extreme.normal) == pytest.approx(1.0)
    assert extreme.normal == pytest.approx(ordinary.normal)
    assert extreme.offset_mm == pytest.approx(ordinary.offset_mm)

    through = rel.key_plane(
        "x",
        "axial",
        series_uid="s",
        slice=0,
        normal=(1.79e308, 1.79e308, 1.79e308),
        origin_lps=(1.0, 2.0, 3.0),
    )
    assert np.linalg.norm(through.normal) == pytest.approx(1.0)
    assert through.offset_mm == pytest.approx(6.0 / np.sqrt(3.0))


def test_reversing_normal_and_offset_leaves_the_position_alone():
    planes = triple("tibia", OBLIQUE, POINT)
    flipped = [
        rel.key_plane(
            "tibia",
            p.orientation,
            series_uid=p.series_uid,
            slice=p.slice,
            normal=[-c for c in p.normal],
            offset_mm=-p.offset_mm,
        )
        for p in planes
    ]
    a = rel.reference_position("tibia", planes).point_lps
    b = rel.reference_position("tibia", flipped).point_lps
    assert a == pytest.approx(b, abs=1e-12)


def test_input_order_does_not_matter():
    planes = triple("tibia", OBLIQUE, POINT)
    a = rel.reference_position("tibia", planes)
    b = rel.reference_position("tibia", planes[::-1])
    assert a.point_lps == b.point_lps
    assert [p.orientation for p in a.planes] == list(rel.ORIENTATIONS)


def test_rigid_motion_of_the_scanner_moves_the_point_the_same_way():
    r = rotation(0.4, -0.9, 1.3)
    t = np.array([5.0, -8.0, 21.0])
    moved = [
        plane("femur", o, r @ np.asarray(n), r @ np.asarray(POINT) + t)
        for o, n in zip(rel.ORIENTATIONS, OBLIQUE, strict=True)
    ]
    got = rel.reference_position("femur", moved).point_lps
    assert got == pytest.approx(r @ np.asarray(POINT) + t, abs=1e-9)


def test_axis_aligned_views_give_x_y_z_but_only_through_the_planes():
    planes = triple("patella", [(1, 0, 0), (0, 1, 0), (0, 0, 1)], (3.0, 4.0, 5.0))
    assert rel.reference_position("patella", planes).point_lps == pytest.approx(
        (3.0, 4.0, 5.0)
    )
    # swapping which orientation LABEL a plane carries cannot change where the planes meet
    relabelled = [
        plane("patella", o, n, (3.0, 4.0, 5.0))
        for o, n in zip(
            rel.ORIENTATIONS, [(0, 0, 1), (1, 0, 0), (0, 1, 0)], strict=True
        )
    ]
    assert rel.reference_position("patella", relabelled).point_lps == pytest.approx(
        (3.0, 4.0, 5.0)
    )


def test_missing_orientations_are_partial_constraints_never_a_filled_point():
    two = triple("acl", OBLIQUE, POINT)[:2]
    p = rel.reference_position("acl", two)
    assert p.status == rel.PARTIAL and p.point_lps is None and p.rank == 2
    assert p.problems == {"axial": rel.NOT_SUPPLIED}
    cross = np.cross(two[0].normal, two[1].normal)
    assert abs(
        np.dot(p.line_direction, cross / np.linalg.norm(cross))
    ) == pytest.approx(1)
    one = rel.reference_position("acl", two[:1])
    assert one.point_lps is None and one.rank == 1 and one.line_direction is None
    none = rel.reference_position("acl", [])
    assert none.status == rel.PARTIAL and set(none.problems.values()) == {
        rel.NOT_SUPPLIED
    }


def test_each_kind_of_missing_has_its_own_code():
    planes = triple("pcl", OBLIQUE, POINT)[:1] + [
        rel.unresolved_plane("pcl", "coronal", rel.REFUSED, reason="no body"),
        rel.unresolved_plane(
            "pcl", "axial", rel.TIED, candidates=[("a", 4), ("a", 5)], reason="equal"
        ),
    ]
    p = rel.reference_position("pcl", planes)
    assert p.problems == {"coronal": "refused", "axial": "tied"}
    assert p.point_lps is None
    assert p.planes[2].candidates == (("a", 4), ("a", 5))
    absent = rel.unresolved_plane("pcl", "axial", rel.ABSENT)
    assert rel.reference_position("pcl", [absent]).problems["axial"] == "absent_in_view"
    assert len({rel.REFUSED, rel.TIED, rel.ABSENT, rel.NOT_SUPPLIED, rel.REPEATED}) == 5


def test_a_tie_and_unknown_outcomes_are_refused_at_construction():
    with pytest.raises(ValueError):
        rel.unresolved_plane("x", "axial", rel.TIED, candidates=[("a", 1)])
    with pytest.raises(ValueError):
        rel.unresolved_plane("x", "axial", rel.SELECTED)


def test_repeated_orientation_is_not_pooled_or_picked():
    planes = triple("femur", OBLIQUE, POINT)
    other = plane("femur", "axial", OBLIQUE[2], (0, 0, 999.0), series_uid="other")
    p = rel.reference_position("femur", [*planes, other])
    assert p.status == rel.PARTIAL and p.point_lps is None
    assert p.problems == {"axial": rel.REPEATED}
    assert {x.series_uid for x in p.planes if x.orientation == "axial"} == {
        "s-axial",
        "other",
    }


@pytest.mark.parametrize(
    ("kw", "code"),
    [
        ({"normal": (0, 0, 0)}, "normal_zero"),
        ({"normal": (math.nan, 0, 1)}, "normal_nonfinite"),
        ({"normal": (math.inf, 0, 1)}, "normal_nonfinite"),
        ({"normal": (1, 0)}, "normal_shape"),
        ({"normal": "abc"}, "normal_shape"),
        ({"origin_lps": (0, math.nan, 0)}, "origin_nonfinite"),
        ({"origin_lps": (0, 0)}, "origin_shape"),
        ({"origin_lps": None}, "origin_or_offset_missing"),
        ({"offset_mm": 1.0}, "origin_and_offset_both_given"),
        ({"precision_mm": -1.0}, "precision_invalid"),
    ],
)
def test_malformed_planes_keep_a_specific_invalid_code(kw, code):
    args = {"normal": (0, 0, 1), "origin_lps": (0, 0, 0)} | kw
    p = rel.key_plane("x", "axial", series_uid="s", slice=1, **args)
    assert p.outcome == rel.INVALID + code and p.normal is None
    assert not p.usable


def test_offset_nonfinite_and_unknown_orientation():
    bad = rel.key_plane(
        "x", "axial", series_uid="s", slice=1, normal=(0, 0, 1), offset_mm=math.nan
    )
    assert bad.outcome == "invalid:offset_nonfinite"
    odd = rel.key_plane(
        "x", "oblique", series_uid="s", slice=1, normal=(0, 0, 1), offset_mm=0.0
    )
    assert odd.outcome == "invalid:unknown_orientation"
    p = rel.reference_position("x", [odd])
    assert p.problems["oblique"] == "invalid:unknown_orientation"


def test_invalid_plane_makes_its_orientation_unusable():
    planes = triple("femur", OBLIQUE, POINT)
    planes[1] = rel.key_plane(
        "femur",
        "coronal",
        series_uid="c",
        slice=2,
        normal=(0, 0, 0),
        origin_lps=(0, 0, 0),
    )
    p = rel.reference_position("femur", planes)
    assert p.status == rel.PARTIAL and p.problems == {"coronal": "invalid:normal_zero"}


def test_singular_triples_are_named_and_have_no_point():
    same = triple("femur", [(1, 0, 0), (2, 0, 0), (0, 0, 1)], POINT)
    p = rel.reference_position("femur", same)
    assert p.status == rel.SINGULAR and p.point_lps is None and p.rank == 2
    coplanar = triple("femur", [(1, 0, 0), (0, 1, 0), (1, 1, 0)], POINT)
    assert rel.reference_position("femur", coplanar).status == rel.SINGULAR
    two = rel.reference_position("femur", same[:2])
    assert (
        two.status == rel.PARTIAL
        and two.geometry == "parallel_planes"
        and two.line_direction is None
    )


def test_nonfinite_solution_is_named():
    planes = triple("femur", [(1, 0, 0), (0, 1, 0), (0, 0, 1)], POINT)
    huge = rel.key_plane(
        "femur", "axial", series_uid="s", slice=0, normal=(0, 0, 1), offset_mm=1e308
    )
    # a finite plane whose inverse overflows is refused as nonfinite, never returned
    tiny = rel.key_plane(
        "femur",
        "coronal",
        series_uid="s",
        slice=0,
        normal=(1e-200, 1, 0),
        offset_mm=1e308,
    )
    p = rel.reference_position("femur", [planes[0], tiny, huge])
    assert p.point_lps is None or all(math.isfinite(v) for v in p.point_lps)


def test_mixed_objects_are_refused():
    planes = triple("femur", OBLIQUE, POINT)
    p = rel.reference_position("tibia", planes)
    assert p.status == rel.MIXED and p.point_lps is None


def test_precision_bound_follows_plane_precisions():
    planes = triple("femur", [(1, 0, 0), (0, 1, 0), (0, 0, 1)], POINT, precision_mm=0.5)
    assert rel.reference_position("femur", planes).precision_mm == pytest.approx(
        (0.5, 0.5, 0.5)
    )
    unknown = triple("femur", [(1, 0, 0), (0, 1, 0), (0, 0, 1)], POINT)
    assert rel.reference_position("femur", unknown).precision_mm is None


def test_plane_of_frame_uses_the_slices_own_frame():
    frame = PlaneFrame.from_dicom((1.0, 2.0, 3.0), AXIAL, (0.5, 0.5))
    p = rel.plane_of_frame(
        "x", "axial", series_uid="s", slice=7, frame=frame, precision_mm=1.0
    )
    assert p.normal is not None
    assert float(np.asarray(p.normal) @ (9, 9, 3.0)) == pytest.approx(p.offset_mm)
    assert abs(
        float(np.asarray(p.normal) @ (0, 0, 5.0)) - p.offset_mm
    ) == pytest.approx(2.0)


# ------------------------------------------------------------------ vectors


def positions(shift=(0.0, 0.0, 0.0), names=("femur", "tibia", "patella")):
    base = {
        "femur": (0.0, 0.0, 0.0),
        "tibia": (3.0, -4.0, 0.0),
        "patella": (0.0, 30.0, 40.0),
    }
    out = {}
    for name in names:
        p = np.asarray(base[name]) + shift
        out[name] = rel.reference_position(
            name, triple(name, OBLIQUE, p, precision_mm=0.25)
        )
    return out


def test_every_ordered_pair_reverses_and_satisfies_the_triangle_identity():
    pos = positions()
    vectors, skipped = rel.pair_vectors(pos, rel.knee_scale(100.0, "test"), "R")
    assert skipped == {} and len(vectors) == 6
    ab, ba = vectors[("femur", "tibia")], vectors[("tibia", "femur")]
    assert ab.displacement_lps == pytest.approx((3.0, -4.0, 0.0), abs=1e-9)
    assert ab.magnitude_mm == pytest.approx(5.0)
    assert ba.displacement_lps == tuple(-v for v in ab.displacement_lps)
    assert ab.direction_lps is not None and ba.direction_lps is not None
    assert ba.direction_lps == pytest.approx(tuple(-v for v in ab.direction_lps))
    assert np.linalg.norm(ab.direction_lps) == pytest.approx(1)
    bc, ac = vectors[("tibia", "patella")], vectors[("femur", "patella")]
    assert np.asarray(ab.displacement_lps) + np.asarray(
        bc.displacement_lps
    ) == pytest.approx(ac.displacement_lps, abs=1e-9)
    each = pos["femur"].precision_mm
    inverse = np.abs(np.linalg.inv([pl.normal for pl in pos["femur"].used]))
    assert each == pytest.approx(tuple(inverse @ np.full(3, 0.25)))
    assert set(ab.provenance) == {"femur", "tibia"}
    assert ab.provenance["femur"]["sagittal"]["series_uid"] == "s-sagittal"
    assert rel.reversed_vector(ba).displacement_lps == ab.displacement_lps


def test_vectors_do_not_depend_on_where_the_patient_lies():
    a, _ = rel.pair_vectors(positions(), rel.UNKNOWN_SCALE, "R")
    b, _ = rel.pair_vectors(positions((100.0, -50.0, 7.0)), rel.UNKNOWN_SCALE, "R")
    for key in a:
        assert a[key].displacement_lps == pytest.approx(
            b[key].displacement_lps, abs=1e-8
        )


def test_scale_normalizes_and_unknown_scale_stays_unknown():
    pos = positions()
    v, _ = rel.pair_vectors(pos, rel.knee_scale(50.0, "ap"), "R")
    ab = v[("femur", "tibia")]
    assert ab.normalized_distance == pytest.approx(0.1)
    assert ab.normalized_displacement == pytest.approx((0.06, -0.08, 0.0), abs=1e-12)
    u, _ = rel.pair_vectors(pos, rel.UNKNOWN_SCALE, "R")
    assert u[("femur", "tibia")].normalized_distance is None
    assert u[("femur", "tibia")].normalized_displacement is None
    assert u[("femur", "tibia")].scale.code == "scale_unknown"
    for bad, code in [
        (0, "scale_not_positive"),
        (-3, "scale_not_positive"),
        (math.nan, "scale_nonfinite"),
        (math.inf, "scale_nonfinite"),
        ("x", "scale_not_a_number"),
        (None, "scale_not_a_number"),
    ]:
        s = rel.knee_scale(bad, "src")
        assert s.mm is None and s.code == code
        w, _ = rel.pair_vectors(pos, s, "R")
        assert w[("femur", "tibia")].normalized_distance is None


def test_anatomical_orientation_mirrors_a_left_knee_and_leaves_unknown_unknown():
    pos = positions()
    r = rel.pair_vectors(pos, rel.UNKNOWN_SCALE, "R")[0][("femur", "tibia")]
    left = rel.pair_vectors(pos, rel.UNKNOWN_SCALE, "L")[0][("femur", "tibia")]
    none = rel.pair_vectors(pos, rel.UNKNOWN_SCALE, "")[0][("femur", "tibia")]
    assert rel.ANATOMICAL_AXES == ("medial", "posterior", "superior")
    assert r.anatomical_mm == pytest.approx((3.0, -4.0, 0.0), abs=1e-9)
    assert left.anatomical_mm == pytest.approx((-3.0, -4.0, 0.0), abs=1e-9)
    assert left.displacement_lps == r.displacement_lps
    assert none.anatomical_mm is None and none.orientation_code == "knee_unknown"
    assert none.anatomical_direction is None and r.orientation_code == "ok"


def test_incomplete_positions_are_listed_not_vectored_and_coincidence_is_named():
    pos = positions()
    pos["acl"] = rel.reference_position("acl", triple("acl", OBLIQUE, POINT)[:2])
    vectors, skipped = rel.pair_vectors(pos, rel.UNKNOWN_SCALE, "R")
    assert skipped == {"acl": "partial"} and all("acl" not in k for k in vectors)
    with pytest.raises(ValueError):
        rel.pair_vector(pos["femur"], pos["acl"])
    same = {n: rel.reference_position(n, triple(n, OBLIQUE, POINT)) for n in ("a", "b")}
    v = rel.pair_vectors(same, rel.knee_scale(10, "t"), "R")[0][("a", "b")]
    assert v.magnitude_mm == pytest.approx(0, abs=1e-9) or v.direction_code in (
        "ok",
        "coincident_points",
    )
    exact = {
        n: rel.reference_position(
            n, triple(n, [(1, 0, 0), (0, 1, 0), (0, 0, 1)], (1.0, 2.0, 3.0))
        )
        for n in ("a", "b")
    }
    v = rel.pair_vectors(exact, rel.knee_scale(10, "t"), "R")[0][("a", "b")]
    assert v.direction_lps is None and v.direction_code == "coincident_points"
    assert v.normalized_distance == 0.0


def test_the_ideal_is_a_separate_type_and_needs_an_observed_complete_anchor():
    pos = positions()
    ideal = rel.IdealVector("femur", "patella", (2.0, 30.0, 40.0), "anatomy: test")
    right = rel.expected_point(pos["femur"], ideal, "R")
    left = rel.expected_point(pos["femur"], ideal, "L")
    assert right.status == "expected" and right.point_lps == pytest.approx(
        (2.0, 30.0, 40.0), abs=1e-9
    )
    assert left.point_lps == pytest.approx((-2.0, 30.0, 40.0), abs=1e-9)
    assert isinstance(right, rel.ExpectedPoint) and not isinstance(right, rel.Position)
    assert right.kind == "expected_from_ideal" and right.ideal_source == "anatomy: test"
    assert rel.expected_point(pos["femur"], ideal, "").status == "knee_unknown"
    assert (
        rel.expected_point(pos["tibia"], ideal, "R").status
        == "anchor_is_not_the_ideal_origin"
    )
    partial = rel.reference_position("femur", triple("femur", OBLIQUE, POINT)[:1])
    assert rel.expected_point(partial, ideal, "R").status == "anchor_incomplete"
    bad = rel.IdealVector("femur", "patella", (math.nan, 0, 0), "x")
    assert rel.expected_point(pos["femur"], bad, "R").status == "ideal_invalid"


# ------------------------------------------------------------------ images


def stack(
    n,
    step,
    start=0.0,
    normal_axis=2,
    tilt=0.0,
    shape_origin=(0.0, 0.0),
    reverse=False,
    spacing=(1.0, 1.0),
):
    """Frames of an acquisition: slices `step` apart along its normal, stored in stack order or reversed."""
    r = rotation(tilt, 0.0, 0.0)
    if normal_axis == 2:
        orientation = AXIAL
    elif (
        normal_axis == 0
    ):  # sagittal: rows run toward the head, columns toward the back
        orientation = (0, 1, 0, 0, 0, -1)
    else:  # coronal
        orientation = (1, 0, 0, 0, 0, -1)
    row, col = np.asarray(orientation[:3], float), np.asarray(orientation[3:], float)
    row, col = r @ row, r @ col
    normal = np.cross(row, col)
    frames = []
    for k in range(n):
        origin = np.asarray([shape_origin[0], shape_origin[1], 0.0]) + normal * (
            start + k * step
        )
        frames.append(PlaneFrame.from_dicom(origin, (*row, *col), spacing))
    return frames[::-1] if reverse else frames


def test_nearest_slice_is_by_physical_distance_not_index_in_unequal_and_reversed_stacks():
    target = (10.0, 20.0, 7.4)
    coarse = stack(10, 3.0)  # planes at z = 0, 3, ... 27
    fine = stack(40, 0.5, start=-2.0)  # z = -2 ... 17.5
    reversed_fine = stack(40, 0.5, start=-2.0, reverse=True)
    pc = rel.locate_in_image(target, coarse, (50, 60))
    pf = rel.locate_in_image(target, fine, (50, 60))
    pr = rel.locate_in_image(target, reversed_fine, (50, 60))
    assert pc.off_plane_mm is not None and pf.off_plane_mm is not None
    assert pc.slice == 2 and abs(pc.off_plane_mm) == pytest.approx(1.4)
    assert pc.off_plane_mm == pytest.approx(
        coarse[2].normal() @ (np.asarray(target) - coarse[2].origin_lps)
    )
    assert pf.slice == 19 and abs(pf.off_plane_mm) == pytest.approx(0.1)
    assert fine[pf.slice].origin_lps[2] == pytest.approx(
        reversed_fine[pr.slice].origin_lps[2]
    )
    assert pr.slice == 40 - 1 - pf.slice
    assert pf.status == "ok" and pf.in_stack and pf.in_image
    assert pf.rc == pytest.approx(
        (20.0, 10.0)
    )  # row along +y, column along +x for the axial frame
    assert pc.half_step_mm == pytest.approx(1.5)


def test_in_plane_place_round_trips_through_the_frames_own_geometry():
    frames = stack(8, 2.0, tilt=0.35, spacing=(0.7, 0.55))
    f = frames[3]
    rc = np.array([[12.25, 31.5]])
    point = f.to_patient(rc)[0]
    placed = rel.locate_in_image(point, frames, (64, 64))
    assert placed.slice == 3 and placed.off_plane_mm == pytest.approx(0, abs=1e-9)
    assert placed.rc == pytest.approx((12.25, 31.5), abs=1e-9)
    # an oblique stack: the point moved along the normal changes the slice, not the in-plane place
    shifted = point + 2.0 * f.normal()
    other = rel.locate_in_image(shifted, frames, (64, 64))
    assert other.slice in (4, 2) and other.rc == pytest.approx((12.25, 31.5), abs=1e-6)


def test_sagittal_and_coronal_stacks_find_their_slices_by_their_own_normals():
    point = (-4.0, 15.3, 22.0)
    sag = stack(12, 2.0, normal_axis=0, start=-10.0)
    cor = stack(12, 2.0, normal_axis=1, start=4.0)
    s = rel.locate_in_image(point, sag, (80, 80))
    c = rel.locate_in_image(point, cor, (80, 80))
    assert s.slice is not None and s.off_plane_mm is not None
    assert c.off_plane_mm is not None
    assert abs(
        sag[s.slice].normal() @ np.asarray(point)
        - sag[s.slice].normal() @ sag[s.slice].origin_lps
    ) == pytest.approx(abs(s.off_plane_mm))
    assert abs(s.off_plane_mm) <= 1.0 + 1e-9 and abs(c.off_plane_mm) <= 1.0 + 1e-9


def test_equidistant_slices_are_a_tie_not_an_arbitrary_pick():
    frames = stack(4, 2.0)
    p = rel.locate_in_image((0, 0, 3.0), frames, (10, 10))
    assert p.status == "tied_slices" and p.tied_slices == (1, 2) and p.slice is None


def test_slice_tie_tolerance_ignores_large_in_plane_translation():
    frames = stack(2, 1.0, shape_origin=(1e15, 1e15))
    p = rel.locate_in_image((1e15, 1e15, 0.25), frames, (10, 10))
    assert p.off_plane_mm is not None
    assert p.status == "ok" and p.slice == 0
    assert abs(p.off_plane_mm) == pytest.approx(0.25)
    assert p.rc == pytest.approx((0.0, 0.0))


def test_distant_slice_does_not_set_tie_tolerance_for_nearby_candidates():
    frames = [
        *stack(2, 1.0),
        PlaneFrame.from_dicom((0.0, 0.0, 1e15), AXIAL, (1.0, 1.0)),
    ]
    p = rel.locate_in_image((0.0, 0.0, 0.25), frames, (10, 10))
    assert p.off_plane_mm is not None
    assert p.status == "ok" and p.slice == 0
    assert abs(p.off_plane_mm) == pytest.approx(0.25)


@pytest.mark.parametrize(
    ("frames", "point", "nearest"),
    [
        ([None, *stack(2, 2.0)], (0.0, 0.0, -10.0), 1),
        ([*stack(2, 2.0), None], (0.0, 0.0, 12.0), 1),
    ],
)
def test_missing_frame_at_stack_endpoint_leaves_extent_unknown(frames, point, nearest):
    p = rel.locate_in_image(point, frames, (10, 10))
    assert p.status == "extent_unknown"
    assert p.slice == nearest and p.in_stack is None
    assert p.rc == pytest.approx((0.0, 0.0))
    assert p.unusable_frames == 1


def test_outside_stack_and_outside_image_are_named_and_clipped_place_reported():
    frames = stack(5, 2.0)
    far = rel.locate_in_image((3.0, 4.0, 40.0), frames, (10, 10))
    assert far.status == "outside_stack" and far.slice == 4 and not far.in_stack
    off = rel.locate_in_image((50.0, 4.0, 4.0), frames, (10, 10))
    assert off.status == "outside_image" and off.in_image is False
    assert off.rc == pytest.approx((4.0, 50.0)) and off.clipped_rc == pytest.approx(
        (4.0, 9.5)
    )
    both = rel.locate_in_image((-50.0, 4.0, 40.0), frames, (10, 10))
    assert (
        both.status == "outside_stack_and_image"
        and both.clipped_rc == pytest.approx((4.0, -0.5))
    )
    edge = rel.locate_in_image((3.0, 4.0, 8.5), frames, (10, 10))
    assert edge.status == "ok"  # within half a step beyond the last plane


def test_unknown_extent_and_unusable_frames_are_named():
    frames = stack(5, 2.0)
    assert rel.locate_in_image((1, 1, 4.0), frames).status == "extent_unknown"
    assert rel.locate_in_image((1, 1, 4.0), []).status == "no_usable_frames"
    assert rel.locate_in_image((1, 1, 4.0), [None, None]).unusable_frames == 2
    mixed = [None, *frames[1:]]
    p = rel.locate_in_image((1, 1, 0.1), mixed, (10, 10))
    assert p.unusable_frames == 1 and p.slice == 1
    assert (
        rel.locate_in_image((math.nan, 0, 0), frames, (10, 10)).status
        == "target_invalid"
    )
    assert rel.locate_in_image((1, 1), frames, (10, 10)).status == "target_invalid"
    single = rel.locate_in_image((1, 1, 0.3), frames[:1], (10, 10))
    assert single.status == "extent_unknown" and single.in_stack is None


def test_a_selected_plane_traces_a_line_in_a_cutting_image_and_none_in_a_parallel_one():
    frames = stack(3, 2.0, normal_axis=2)
    cutter = plane("x", "sagittal", (1, 0, 0), (7.0, 0, 0))
    trace = rel.plane_trace_in_frame(cutter, frames[1])
    assert trace is not None
    a, b, e = trace
    assert (a, b, e) == pytest.approx((0.0, 1.0, 7.0))  # column 7
    parallel = plane("x", "axial", (0, 0, 1), (0, 0, 2.0))
    assert rel.plane_trace_in_frame(parallel, frames[1]) is None
    with pytest.raises(ValueError):
        rel.plane_trace_in_frame(
            rel.unresolved_plane("x", "axial", rel.REFUSED), frames[0]
        )


def test_end_to_end_planes_to_vectors_to_expected_slice():
    """key planes -> position -> pair vector -> expected point -> slice and in-plane place in another image."""
    pos = positions((10.0, 20.0, 6.0))
    vectors, _ = rel.pair_vectors(pos, rel.knee_scale(80.0, "t"), "R")
    ideal = rel.IdealVector("femur", "tibia", (3.0, -4.0, 0.0), "test ideal")
    expected = rel.expected_point(pos["femur"], ideal, "R")
    assert expected.point_lps == pytest.approx(pos["tibia"].point_lps, abs=1e-9)
    placed = rel.locate_in_image(
        expected.point_lps, stack(10, 2.0, reverse=True), (40, 40)
    )
    assert placed.status == "ok" and vectors[
        ("femur", "tibia")
    ].normalized_distance == pytest.approx(5 / 80)


# ------------------------------------------------------------------ the development CLI's construction

STUDY = "study-1"


def synthetic_study():
    sag = stack(12, 2.0, normal_axis=0, start=-10.0)
    cor = stack(10, 3.0, normal_axis=1, start=-5.0, reverse=True)
    ax = stack(16, 1.5, normal_axis=2, start=-4.0)
    info = {
        "SAG": {"frames": sag, "shape": (64, 64), "plane": "Sagittal"},
        "COR": {"frames": cor, "shape": (64, 64), "plane": "Coronal"},
        "AX": {"frames": ax, "shape": (64, 64), "plane": "Axial"},
    }
    return {STUDY: info}


def section(obj, uid, z, area, centroid):
    return {
        "study_uid": STUDY,
        "object": obj,
        "series_uid": uid,
        "slice": z,
        "support": "s",
        "row": None,
        "view": ["x", "0", "0"],
        "selection": "middle_bootstrap",
        "pixels": 10,
        "area_mm2": area,
        "diagnostic_centroid_lps": list(centroid),
    }


def spec_for(**orientations):
    return {STUDY: {"femur": orientations}}


def sel(uid, z, **extra):
    return {
        "series_uid": uid,
        "slice": z,
        "reason": "test",
        "provenance": "test",
        **extra,
    }


def test_without_selected_planes_nothing_has_a_point_and_old_schema_is_absent():
    frames = synthetic_study()
    rows = [section("femur", "SAG", 3, 5000.0, (1, 2, 3))]
    points, _ = kp.key_points(rows, {}, frames)
    record = points[STUDY]["femur"]
    assert (
        record["construction"] == "three_key_planes" and record["status"] == "partial"
    )
    assert record["position_lps"] is None and record["complete"] is False
    assert set(record["problems"].values()) == {"not_supplied"}
    assert not {"key_point", "lps", "depth_axis"} & set(record)
    assert record["key_sections"]["SAG"]["diagnostic_centroid_lps"] == [1, 2, 3]
    assert record["key_sections_role"].startswith("diagnostic_inventory")


def test_three_selected_slices_give_the_point_where_their_own_planes_meet():
    frames = synthetic_study()
    info = frames[STUDY]
    spec = spec_for(sagittal=sel("SAG", 4), coronal=sel("COR", 2), axial=sel("AX", 7))
    points, positions = kp.key_points([], spec, frames)
    pos = positions[STUDY]["femur"]
    expected = (
        info["SAG"]["frames"][4].origin_lps[0],
        info["COR"]["frames"][2].origin_lps[1],
        info["AX"]["frames"][7].origin_lps[2],
    )
    assert pos.complete and pos.point_lps == pytest.approx(expected, abs=1e-9)
    record = points[STUDY]["femur"]
    assert record["position_lps"] == pytest.approx(expected, abs=1e-9)
    for orientation, series in (
        ("sagittal", "SAG"),
        ("coronal", "COR"),
        ("axial", "AX"),
    ):
        (address,) = record["planes"][orientation]
        assert address["series_uid"] == series and address["outcome"] == "selected"
        assert (
            address["header_plane"].lower() == orientation
            and address["precision_mm"] > 0
        )


def test_no_section_centroid_or_largest_section_can_move_the_point():
    frames = synthetic_study()
    spec = spec_for(sagittal=sel("SAG", 4), coronal=sel("COR", 2), axial=sel("AX", 7))
    quiet, _ = kp.key_points([], spec, frames)
    rows = [
        section("femur", "SAG", 9, 9e9, (1e5, -1e5, 7e5)),
        section("femur", "COR", 0, 9e9, (-3e4, 2e4, 9e4)),
        section("femur", "AX", 15, 9e9, (0, 0, 0)),
        section("femur", "SAG", 4, 1.0, (123, 456, 789)),
    ]
    noisy, _ = kp.key_points(rows, spec, frames)
    assert (
        noisy[STUDY]["femur"]["position_lps"] == quiet[STUDY]["femur"]["position_lps"]
    )
    # the selected slice's own native section is attached as information, the larger sections elsewhere are not planes
    (sag,) = noisy[STUDY]["femur"]["planes"]["sagittal"]
    assert sag["native_section"]["area_mm2"] == 1.0 and sag["slice"] == 4
    (cor,) = noisy[STUDY]["femur"]["planes"]["coronal"]
    assert cor["native_section"] is None and cor["outcome"] == "selected"


def test_the_caller_selection_failures_keep_their_own_codes_and_leave_the_point_open():
    frames = synthetic_study()
    frames[STUDY]["AX"]["frames"][3] = None
    spec = spec_for(
        sagittal=sel("NOPE", 1),
        coronal=sel("SAG", 1),
        axial=sel("AX", 3),
    )
    points, _ = kp.key_points([], spec, frames)
    problems = points[STUDY]["femur"]["problems"]
    assert problems == {
        "sagittal": "invalid:series_not_in_study",
        "coronal": "invalid:orientation_disagrees_with_series",
        "axial": "invalid:frame_unavailable",
    }
    far = spec_for(
        sagittal=sel("SAG", 99),
        coronal={"outcome": "refused", "reason": "r"},
        axial={"outcome": "absent_in_view"},
    )
    points, _ = kp.key_points([], far, frames)
    assert points[STUDY]["femur"]["problems"] == {
        "sagittal": "invalid:slice_out_of_range",
        "coronal": "refused",
        "axial": "absent_in_view",
    }
    tie = spec_for(
        sagittal={
            "outcome": "tied",
            "candidates": [
                {"series_uid": "SAG", "slice": 1},
                {"series_uid": "SAG", "slice": 2},
            ],
        },
        coronal=[sel("COR", 1), sel("COR", 2)],
    )
    points, _ = kp.key_points([], tie, frames)
    record = points[STUDY]["femur"]
    assert record["problems"] == {
        "sagittal": "tied",
        "coronal": "repeated_orientation",
        "axial": "not_supplied",
    }
    assert record["planes"]["sagittal"][0]["candidates"] == [["SAG", 1], ["SAG", 2]]
    assert len(record["planes"]["coronal"]) == 2 and record["position_lps"] is None


def test_an_explicit_oblique_plane_can_be_given_and_is_solved_not_axis_aligned():
    frames = synthetic_study()
    n = (1.0, 0.3, -0.2)
    through = (4.0, 5.0, 6.0)
    spec = spec_for(
        sagittal={"series_uid": "SAG", "slice": 0, "normal": n, "origin_lps": through},
        coronal={
            "series_uid": "COR",
            "slice": 0,
            "normal": (0.1, 1.0, 0.2),
            "origin_lps": through,
        },
        axial={
            "series_uid": "AX",
            "slice": 0,
            "normal": (0.0, -0.3, 1.0),
            "origin_lps": through,
        },
    )
    _, positions = kp.key_points([], spec, frames)
    assert positions[STUDY]["femur"].point_lps == pytest.approx(through, abs=1e-9)


def test_complete_points_get_vectors_and_a_place_in_every_series():
    frames = synthetic_study()
    spec = {
        STUDY: {
            "femur": spec_for(
                sagittal=sel("SAG", 4), coronal=sel("COR", 2), axial=sel("AX", 7)
            )[STUDY]["femur"],
            "tibia": spec_for(
                sagittal=sel("SAG", 6), coronal=sel("COR", 5), axial=sel("AX", 3)
            )[STUDY]["femur"],
            "acl": spec_for(sagittal=sel("SAG", 6))[STUDY]["femur"],
        }
    }
    _, positions = kp.key_points([], spec, frames)
    vectors, images = kp.vectors_and_images(
        positions, frames, {STUDY: "R"}, {STUDY: {"mm": 100.0, "source": "test"}}, True
    )
    got = vectors[STUDY]
    assert got["scale"]["code"] == "given" and got["skipped"] == {"acl": "partial"}
    assert {(v["origin"], v["target"]) for v in got["vectors"]} == {
        ("femur", "tibia"),
        ("tibia", "femur"),
    }
    by = {(v["origin"], v["target"]): v for v in got["vectors"]}
    forward, back = by[("femur", "tibia")], by[("tibia", "femur")]
    assert back["displacement_lps"] == [-x for x in forward["displacement_lps"]]
    assert forward["normalized_distance"] == pytest.approx(
        forward["magnitude_mm"] / 100.0
    )
    assert forward["orientation_code"] == "ok" and forward["anatomical_axes"] == [
        "medial",
        "posterior",
        "superior",
    ]
    assert set(images[STUDY]) == {"femur", "tibia"}
    assert set(images[STUDY]["femur"]) == {"SAG", "COR", "AX"}
    assert images[STUDY]["femur"]["SAG"]["slice"] == 4 and images[STUDY]["femur"][
        "SAG"
    ]["off_plane_mm"] == pytest.approx(0, abs=1e-9)
    unknown, _ = kp.vectors_and_images(positions, frames, {STUDY: ""}, {}, True)
    assert unknown[STUDY]["scale"]["code"] == "scale_unknown"
    assert all(
        v["normalized_distance"] is None and v["anatomical_mm"] is None
        for v in unknown[STUDY]["vectors"]
    )
