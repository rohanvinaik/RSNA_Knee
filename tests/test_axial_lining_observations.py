"""Intent tests for cavity-lining observations from saved native edge masks."""

import numpy as np

from knee.collapse.observations import Observation, Unresolved
from scripts import run_interiors as run

UID = "series-axial"
AXIAL = ("Axial", "1", "1")
CORONAL = ("Coronal", "1", "1")
MEDIAL = "medial_patellar_retinaculum"
LATERAL = "lateral_patellar_retinaculum"


def wall(
    support: str,
    *,
    side: str = MEDIAL,
    slice_index: int = 22,
    row: int | None = None,
    count: int = 91,
    object_name: str = "joint_capsule",
    provenance: str = "native",
    kind: str = "resolved",
    view: tuple[str, str, str] = AXIAL,
) -> Observation:
    return Observation(
        object_name,
        provenance,
        kind,
        UID,
        view,
        (slice_index,),
        "identified",
        count,
        0.0,
        support,
        "validated source wall",
        "source/axial.npz",
        row,
        None,
    )


def test_main_and_pointed_paths_count_boolean_edges_and_preserve_wall_address():
    main_medial = np.zeros((5, 6), dtype=bool)
    main_medial[1, 2:4] = True
    main_lateral = np.zeros((5, 6), dtype=bool)
    main_lateral[3, 4] = True
    pointed_medial = np.zeros((2, 5, 6), dtype=bool)
    pointed_medial[1, 2, 1:4] = True
    pointed_lateral = np.zeros((2, 5, 6), dtype=bool)
    pointed_lateral[0, 4, 4:6] = True
    arrays = {
        "a2_retinacula_positive_inner_lining": main_medial,
        "a2_retinacula_negative_inner_lining": main_lateral,
        "a3_recess_plane_medial_lining": pointed_medial,
        "a3_recess_plane_lateral_lining": pointed_lateral,
        "a3_recess_plane_slices": np.asarray([21, 23], dtype=np.int32),
    }
    sources = [
        wall(f"a2_{MEDIAL}"),
        wall(f"a2_{LATERAL}", side=LATERAL),
        wall("a3_recess_plane_medial_wall", slice_index=23, row=1),
        wall(
            "a3_recess_plane_lateral_wall",
            side=LATERAL,
            slice_index=21,
            row=0,
        ),
    ]

    found, missing = run.cavity_lining_observations(sources, [], arrays)

    assert missing == []
    assert [item.count for item in found] == [2, 1, 3, 2]
    assert [item.support for item in found] == [
        "a2_retinacula_positive_inner_lining",
        "a2_retinacula_negative_inner_lining",
        "a3_recess_plane_medial_lining",
        "a3_recess_plane_lateral_lining",
    ]
    assert all(item.object == "synovium" for item in found)
    assert all(item.kind == "resolved" and item.label is None for item in found)
    for source, result in zip(sources, found, strict=True):
        assert result.provenance == source.provenance
        assert result.series_uid == source.series_uid
        assert result.view == source.view
        assert result.slices == source.slices
        assert result.off_plane_mm == source.off_plane_mm
        assert result.artifact == source.artifact
        assert result.row == source.row
        assert result.count != source.count
    assert all(
        mask.dtype == np.bool_ for key, mask in arrays.items() if "lining" in key
    )


def test_empty_edge_is_a_measured_reading_not_absence():
    arrays = {"a2_retinacula_positive_inner_lining": np.zeros((3, 4), dtype=bool)}

    found, missing = run.cavity_lining_observations([wall(f"a2_{MEDIAL}")], [], arrays)

    assert missing == []
    assert len(found) == 1
    assert found[0].object == "synovium"
    assert found[0].kind == "reading"
    assert found[0].count == 0
    assert found[0].code == "observed_empty_cavity_facing_edge"
    assert "absence" not in found[0].note


def test_missing_invalid_shape_and_slice_mismatch_return_named_unknowns():
    cases = [
        (
            wall(f"a2_{MEDIAL}"),
            {},
            "axial_cavity_face:source_lining_support_missing",
        ),
        (
            wall(f"a2_{LATERAL}", side=LATERAL),
            {"a2_retinacula_negative_inner_lining": np.zeros((3, 4), dtype=np.uint8)},
            "axial_cavity_face:source_lining_support_invalid",
        ),
        (
            wall(f"a2_{MEDIAL}"),
            {"a2_retinacula_positive_inner_lining": np.zeros((1, 3, 4), dtype=bool)},
            "axial_cavity_face:source_lining_address_invalid",
        ),
        (
            wall("a3_recess_plane_medial_wall", slice_index=21, row=1),
            {
                "a3_recess_plane_medial_lining": np.zeros((1, 3, 4), dtype=bool),
                "a3_recess_plane_slices": np.asarray([21], dtype=np.int32),
            },
            "axial_cavity_face:source_lining_address_invalid",
        ),
        (
            wall("a3_recess_plane_medial_wall", slice_index=22, row=0),
            {
                "a3_recess_plane_medial_lining": np.zeros((1, 3, 4), dtype=bool),
                "a3_recess_plane_slices": np.asarray([21], dtype=np.int32),
            },
            "axial_cavity_face:source_lining_slice_mismatch",
        ),
        (
            wall("a3_recess_plane_lateral_wall", side=LATERAL, slice_index=21, row=0),
            {
                "a3_recess_plane_lateral_lining": np.zeros((3, 4), dtype=bool),
                "a3_recess_plane_slices": np.asarray([21], dtype=np.int32),
            },
            "axial_cavity_face:source_lining_address_invalid",
        ),
    ]
    for source, arrays, expected_code in cases:
        found, missing = run.cavity_lining_observations([source], [], arrays)
        assert found == []
        assert len(missing) == 1
        assert missing[0].object == "synovium"
        assert missing[0].code == expected_code


def test_wall_source_refusals_keep_their_original_reason():
    reason = Unresolved("joint_capsule", "native", UID, AXIAL, "wall_rule_refused")

    found, missing = run.cavity_lining_observations([], [reason], {})

    assert found == []
    assert missing == [
        Unresolved(
            "synovium",
            "native",
            UID,
            AXIAL,
            "axial_cavity_face:wall_rule_refused",
        )
    ]


def test_non_native_nonresolved_and_non_capsule_observations_are_excluded():
    main_key = f"a2_{MEDIAL}"
    arrays = {"a2_retinacula_positive_inner_lining": np.ones((3, 4), dtype=bool)}
    sources = [
        wall(main_key, provenance="laid"),
        wall(main_key, provenance="projected", kind="target"),
        wall(main_key, kind="reading"),
        wall(main_key, object_name="joint_fluid"),
    ]

    found, missing = run.cavity_lining_observations(sources, [], arrays)

    assert found == []
    assert missing == []


def test_coronal_middle_and_pointed_supports_keep_their_native_addresses():
    middle = np.zeros((5, 6), dtype=bool)
    middle[1, 1:4] = True
    pointed = np.zeros((2, 5, 6), dtype=bool)
    pointed[1, 3, 2:6] = True
    arrays = {
        "a4_coronal_lining": middle,
        "a3_recess_plane_side_lining": pointed,
        "a3_recess_plane_slices": np.asarray([13, 15], dtype=np.int32),
    }
    sources = [
        wall("a2_joint_capsule", slice_index=15, view=CORONAL),
        wall("a3_recess_plane_capsule", slice_index=15, row=1, view=CORONAL),
    ]

    found, missing = run.cavity_lining_observations(sources, [], arrays)

    assert missing == []
    assert [row.support for row in found] == [
        "a4_coronal_lining",
        "a3_recess_plane_side_lining",
    ]
    assert [row.count for row in found] == [3, 4]
    for source, result in zip(sources, found, strict=True):
        assert result.object == "synovium"
        assert result.provenance == "native" and result.kind == "resolved"
        assert result.view == CORONAL and result.slices == source.slices
        assert result.row == source.row and result.label is None
        assert result.artifact == source.artifact
        assert result.count != source.count


def test_empty_coronal_lining_is_a_measured_reading():
    arrays = {"a4_coronal_lining": np.zeros((3, 4), dtype=bool)}

    found, missing = run.cavity_lining_observations(
        [wall("a2_joint_capsule", slice_index=15, view=CORONAL)], [], arrays
    )

    assert missing == []
    assert len(found) == 1
    assert found[0].kind == "reading" and found[0].count == 0
    assert found[0].code == "observed_empty_cavity_facing_edge"


def test_coronal_missing_invalid_and_pointed_slice_mismatch_are_named():
    cases = [
        (
            wall("a2_joint_capsule", slice_index=15, view=CORONAL),
            {},
            "coronal_cavity_face:source_lining_support_missing",
        ),
        (
            wall("a2_joint_capsule", slice_index=15, view=CORONAL),
            {"a4_coronal_lining": np.zeros((3, 4), dtype=np.uint8)},
            "coronal_cavity_face:source_lining_support_invalid",
        ),
        (
            wall("a3_recess_plane_capsule", slice_index=15, row=0, view=CORONAL),
            {
                "a3_recess_plane_side_lining": np.zeros((1, 3, 4), dtype=bool),
                "a3_recess_plane_slices": np.asarray([14], dtype=np.int32),
            },
            "coronal_cavity_face:source_lining_slice_mismatch",
        ),
    ]
    for source, arrays, expected_code in cases:
        found, missing = run.cavity_lining_observations([source], [], arrays)
        assert found == []
        assert len(missing) == 1
        assert missing[0].object == "synovium"
        assert missing[0].code == expected_code


def test_coronal_wall_refusal_keeps_reason_under_coronal_code():
    reason = Unresolved("joint_capsule", "native", UID, CORONAL, "wall_rule_refused")

    found, missing = run.cavity_lining_observations([], [reason], {})

    assert found == []
    assert missing == [
        Unresolved(
            "synovium",
            "native",
            UID,
            CORONAL,
            "coronal_cavity_face:wall_rule_refused",
        )
    ]
