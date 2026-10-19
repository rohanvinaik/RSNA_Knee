from __future__ import annotations

from typing import Any

import numpy as np

from knee.objects.assignments import axial_mcl_components


def _measurement(
    components: list[tuple[int, list[tuple[int, int]], bool]],
    *,
    status: str = "complete",
    shape: tuple[int, int] = (12, 12),
) -> dict[str, Any]:
    labels = np.zeros(shape, dtype=np.int32)
    rows = []
    for label, points, contacted in components:
        for point in points:
            labels[point] = label
        rows.append(
            {
                "label": label,
                "pixels": len(points),
                "minimum_target_distance_mm": 0.0 if contacted else 5.0,
                "within_existing_contact_shell": contacted,
                "crop_edge_pixels": 0,
                "touches_crop_edge": False,
            }
        )
    return {
        "status": status,
        "partial_reading": status == "partial_reading",
        "labels": labels,
        "distance_to_target_mm": np.zeros(shape, dtype=np.float64),
        "target_pixels": 1,
        "available_target_pixels": 1,
        "components": rows,
    }


def _mask(shape: tuple[int, int], *points: tuple[int, int]) -> np.ndarray:
    result = np.zeros(shape, dtype=bool)
    for point in points:
        result[point] = True
    return result


def test_unknown_bone_context_stays_neutral_and_unique_largest_is_selected() -> None:
    measurement = _measurement(
        [(1, [(4, 4), (4, 5), (5, 4)], True), (2, [(8, 8)], True)]
    )

    result = axial_mcl_components(measurement)

    assert result["status"] == "identified"
    assert result["selected_component_id"] == 1
    assert int(np.asarray(result["selected"]).sum()) == 3
    assert (
        result["bone_context"]["femur"]["status"]
        == "unknown_native_support_unavailable"
    )
    assert (
        result["bone_context"]["tibia"]["status"]
        == "unknown_native_support_unavailable"
    )


def test_known_native_bone_conflict_excludes_whole_component_only() -> None:
    measurement = _measurement(
        [(1, [(4, 4), (4, 5), (5, 4)], True), (2, [(8, 8), (8, 9)], True)]
    )
    support = _mask((12, 12), (4, 4))

    result = axial_mcl_components(
        measurement,
        {
            "femur": {
                "status": "resolved_native_support",
                "mask": support,
                "metadata": {"slice": 3, "support": "a3_femur_plane_region"},
            }
        },
    )

    assert result["status"] == "identified"
    assert result["selected_component_id"] == 2
    assert result["components"][0]["known_bone_intersection_pixels"] == 1
    assert result["components"][0]["bone_intersection_pixels"] == {"femur": 1}
    assert result["components"][0]["excluded_by_resolved_bone"] is True
    assert result["components"][1]["excluded_by_resolved_bone"] is False


def test_all_contacted_components_conflicting_has_named_refusal() -> None:
    measurement = _measurement([(1, [(4, 4), (4, 5)], True)])

    result = axial_mcl_components(
        measurement,
        {
            "tibia": {
                "status": "resolved_native_support",
                "mask": _mask((12, 12), (4, 4)),
            }
        },
    )

    assert result["status"] == "candidate_merged_with_resolved_bone"
    assert not np.asarray(result["selected"]).any()


def test_equal_largest_nonconflicting_components_are_retained_as_tie() -> None:
    measurement = _measurement(
        [(1, [(4, 4), (4, 5)], True), (2, [(8, 8), (8, 9)], True)]
    )

    result = axial_mcl_components(measurement)

    assert result["status"] == "tied_largest_nonconflicting_components"
    assert result["largest_component_ids"] == [1, 2]
    assert not np.asarray(result["selected"]).any()


def test_partial_scope_can_resolve_body_but_crop_edge_body_remains_reading() -> None:
    partial = _measurement([(1, [(4, 4), (4, 5)], True)], status="partial_reading")
    partial_result = axial_mcl_components(partial)
    assert partial_result["status"] == "identified"
    assert partial_result["scope_partial"] is True

    edge = _measurement([(1, [(0, 4), (1, 4)], True)])
    edge_result = axial_mcl_components(edge)
    assert edge_result["status"] == "partial_reading"
    assert edge_result["selected_touches_crop_edge"] is True


def test_malformed_bone_context_is_named_and_remains_neutral() -> None:
    measurement = _measurement([(1, [(4, 4), (4, 5)], True)])

    result = axial_mcl_components(
        measurement,
        {
            "femur": {
                "status": "resolved_native_support",
                "mask": np.ones((2, 2), dtype=bool),
                "metadata": {"slice": 3},
            }
        },
    )

    assert result["status"] == "identified"
    assert (
        result["bone_context"]["femur"]["status"] == "unknown_malformed_native_support"
    )
    assert result["components"][0]["known_bone_intersection_pixels"] == 0


def test_malformed_measurement_is_named_without_selection() -> None:
    result = axial_mcl_components({"status": "complete", "labels": np.zeros(4)})
    assert result["status"] == "malformed_component_measurement"
    assert result["selected"] is None

    inconsistent = _measurement([(1, [(4, 4)], True)])
    inconsistent["components"][0]["pixels"] = 2
    result = axial_mcl_components(inconsistent)
    assert result["status"] == "malformed_component_measurement"
    assert result["selected"] is None


def test_unavailable_boundary_marks_only_the_adjacent_selected_component_partial() -> (
    None
):
    measurement = _measurement([(1, [(4, 4), (4, 5)], True)])
    measurement["partial_reading"] = True
    measurement["components"][0]["touches_unavailable_boundary"] = True

    result = axial_mcl_components(measurement)

    assert result["status"] == "partial_reading"
    assert result["selected_touches_unavailable_boundary"] is True


def test_uncontacted_component_with_missing_source_support_is_named_unknown() -> None:
    measurement = _measurement([(1, [(4, 4)], False)])
    measurement["target_pixels"] = 2
    measurement["available_target_pixels"] = 1

    result = axial_mcl_components(measurement)

    assert result["status"] == "contact_unknown_partial_source"


def test_empty_and_failed_measurements_keep_distinct_named_outcomes() -> None:
    empty = axial_mcl_components(_measurement([]))
    assert empty["status"] == "measured_empty"
    failed = axial_mcl_components({"status": "target_unavailable", "labels": None})
    assert failed["status"] == "measurement_target_unavailable"


def test_invalid_labels_never_allocate_a_sparse_label_domain() -> None:
    for label in (-1, 1_000_000_000):
        measurement = _measurement([(1, [(4, 4)], True)])
        measurement["labels"][4, 4] = label
        result = axial_mcl_components(measurement)
        assert result["status"] == "malformed_component_measurement"


def test_unknown_context_preserves_why_it_cannot_exclude() -> None:
    result = axial_mcl_components(
        _measurement([(1, [(4, 4)], True)]),
        {
            "femur": {
                "status": "unknown_invalid_native_support_context",
                "reasons": ["invalid_slice_type"],
            }
        },
    )
    assert result["status"] == "identified"
    assert result["bone_context"]["femur"]["reasons"] == ["invalid_slice_type"]
