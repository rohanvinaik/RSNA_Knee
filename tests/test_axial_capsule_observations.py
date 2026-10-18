from __future__ import annotations

from dataclasses import replace

from knee.collapse.observations import Observation, Unresolved
from scripts import run_interiors as run

UID = "axial-series"
AXIAL = ("Axial", "1", "1")
MEDIAL, LATERAL = run.RETINACULA


def wall(
    name: str,
    support: str,
    **overrides: object,
) -> Observation:
    fields: dict[str, object] = {
        "object": name,
        "provenance": "native",
        "kind": "resolved",
        "series_uid": UID,
        "view": AXIAL,
        "slices": (7,),
        "code": "identified",
        "count": 8,
        "off_plane_mm": 0.0,
        "support": support,
        "note": "original retinaculum section",
        "artifact": "study/axial.npz",
        "row": None,
        "label": None,
    }
    fields.update(overrides)
    return Observation(**fields)  # type: ignore[arg-type]


def test_native_walls_from_both_paths_preserve_every_source_address_and_measurement():
    source = [
        wall(MEDIAL, f"a2_{MEDIAL}"),
        wall(LATERAL, f"a2_{LATERAL}", row=None),
        wall(MEDIAL, "a3_recess_plane_medial_wall", row=2),
        wall(
            LATERAL,
            "a3_recess_plane_lateral_wall",
            row=3,
            code="agreed_with_its_partner",
        ),
    ]

    found, missing = run.axial_capsule_observations(source, [])

    assert missing == []
    assert len(found) == len(source)
    assert [observation.object for observation in found] == ["joint_capsule"] * 4
    for before, after in zip(source, found, strict=True):
        assert replace(after, object=before.object, note=before.note) == before
        assert "outer-wall band" in after.note
        assert "joint recess" in after.note
        assert "full course" in after.note
    assert source[2].row == 2 and found[2].row == 2
    assert source[3].row == 3 and found[3].row == 3


def test_axial_source_refusal_is_named_and_keeps_valid_partial_side():
    source = [wall(MEDIAL, f"a2_{MEDIAL}")]
    refused = Unresolved(
        LATERAL,
        "native",
        UID,
        AXIAL,
        "abstain_no_outboard_wall_minimum",
    )

    found, missing = run.axial_capsule_observations(source, [refused])

    assert len(found) == 1 and found[0].object == "joint_capsule"
    assert missing == [
        Unresolved(
            "joint_capsule",
            "native",
            UID,
            AXIAL,
            f"{LATERAL}:abstain_no_outboard_wall_minimum",
        )
    ]


def test_projected_laid_reading_nonaxial_and_unrelated_observations_stay_excluded():
    sources = [
        wall(MEDIAL, f"a2_{MEDIAL}", provenance="projected", kind="target"),
        wall(MEDIAL, f"a2_{MEDIAL}", provenance="laid"),
        wall(MEDIAL, f"a2_{MEDIAL}", kind="reading"),
        wall(MEDIAL, f"a2_{MEDIAL}", view=("Sagittal", "1", "1")),
        wall("joint_fluid", "a4_axial_joint_fluid"),
    ]
    silences = [
        Unresolved(MEDIAL, "laid", UID, AXIAL, "transfer_failed"),
        Unresolved(LATERAL, "native", UID, ("Coronal", "1", "1"), "not_axial"),
    ]

    found, missing = run.axial_capsule_observations(sources, silences)

    assert found == []
    assert missing == []


def test_invalid_resolved_source_fields_return_named_unknowns():
    sources = [
        wall(MEDIAL, "not_a_saved_wall_mask"),
        wall(LATERAL, f"a2_{LATERAL}", slices=(True,)),
        wall(MEDIAL, f"a2_{MEDIAL}", count=0),
        wall(LATERAL, f"a2_{LATERAL}", code="unrecognized_code"),
        wall(MEDIAL, f"a2_{MEDIAL}", label=3),
        wall(LATERAL, f"a2_{LATERAL}", artifact=""),
    ]

    found, missing = run.axial_capsule_observations(sources, [])

    assert found == []
    assert [entry.code for entry in missing] == [
        f"{MEDIAL}:source_support_unavailable",
        f"{LATERAL}:source_slice_invalid",
        f"{MEDIAL}:source_count_invalid",
        f"{LATERAL}:source_code_unavailable",
        f"{MEDIAL}:source_label_unexpected",
        f"{LATERAL}:source_artifact_unavailable",
    ]
    assert all(entry.object == "joint_capsule" for entry in missing)


def test_source_row_must_match_main_or_pointed_support_path():
    negative_row = wall(MEDIAL, "a3_recess_plane_medial_wall", row=0)
    object.__setattr__(negative_row, "row", -1)
    sources = [
        wall(MEDIAL, f"a2_{MEDIAL}", row=2),
        wall(LATERAL, "a3_recess_plane_lateral_wall", row=None),
        wall(MEDIAL, "a3_recess_plane_medial_wall", row=True),
        wall(LATERAL, "a3_recess_plane_lateral_wall", row=1.5),
        negative_row,
    ]

    found, missing = run.axial_capsule_observations(sources, [])

    assert found == []
    assert [entry.code for entry in missing] == [
        f"{MEDIAL}:source_row_invalid",
        f"{LATERAL}:source_row_invalid",
        f"{MEDIAL}:source_row_invalid",
        f"{LATERAL}:source_row_invalid",
        f"{MEDIAL}:source_row_invalid",
    ]


def test_malformed_support_and_view_are_named_for_found_sources():
    unhashable_support = wall(MEDIAL, f"a2_{MEDIAL}")
    object.__setattr__(unhashable_support, "support", [])
    malformed_view = wall(MEDIAL, f"a2_{MEDIAL}")
    object.__setattr__(malformed_view, "view", ("Axial", None, "1"))

    found, missing = run.axial_capsule_observations(
        [unhashable_support, malformed_view], []
    )

    assert found == []
    assert [entry.code for entry in missing] == [
        f"{MEDIAL}:source_support_unavailable",
        f"{MEDIAL}:source_view_invalid",
    ]


def test_malformed_native_missing_views_return_named_unknowns():
    null_view = Unresolved(MEDIAL, "native", UID, AXIAL, "source_refused")
    object.__setattr__(null_view, "view", None)
    malformed_view = Unresolved(LATERAL, "native", UID, AXIAL, "source_refused")
    object.__setattr__(malformed_view, "view", ("Axial", None, "1"))
    nonaxial = Unresolved(MEDIAL, "native", UID, ("Coronal", "1", "1"), "nonaxial")
    sources = [null_view, malformed_view, nonaxial]

    found, missing = run.axial_capsule_observations([], sources)

    assert found == []
    expected_malformed = Unresolved(
        "joint_capsule",
        "native",
        UID,
        AXIAL,
        f"{LATERAL}:source_view_invalid",
    )
    object.__setattr__(expected_malformed, "view", ("Axial", None, "1"))
    assert missing == [
        Unresolved(
            "joint_capsule",
            "native",
            UID,
            None,
            f"{MEDIAL}:source_view_invalid",
        ),
        expected_malformed,
    ]


def test_empty_inputs_return_empty_outputs():
    assert run.axial_capsule_observations([], []) == ([], [])
