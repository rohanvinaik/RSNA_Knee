"""Intent tests for the anterior-recess description of saved axial pockets."""

from knee.collapse.observations import Observation, Unresolved
from scripts import run_interiors as run

UID = "series-axial"
AXIAL = ("Axial", "1", "1")
SAGITTAL = ("Sagittal", "1", "1")


def fluid(
    *,
    kind: str = "resolved",
    code: str = "identified",
    slice_index: int = 21,
    row: int | None = 0,
    count: int | None = 37,
    provenance: str = "native",
    view: tuple[str, str, str] = AXIAL,
    support: str = "a4_axial_joint_fluid",
    object_name: str = "joint_fluid",
) -> Observation:
    return Observation(
        object_name,
        provenance,
        kind,
        UID,
        view,
        (slice_index,),
        code,
        count,
        0.0,
        support,
        "source fluid union",
        "study/series.npz",
        row,
        None,
    )


def test_main_and_pointed_fluid_supports_keep_their_native_addresses():
    sources = [
        fluid(slice_index=21, row=0, count=37),
        fluid(slice_index=22, row=None, count=41),
    ]

    found, missing = run.anterior_recess_from_axial_pockets(sources, [])

    assert missing == []
    assert len(found) == 2
    for source, result in zip(sources, found, strict=True):
        assert result.object == "anterior_synovial_recess"
        assert result.provenance == source.provenance == "native"
        assert result.kind == source.kind == "resolved"
        assert result.series_uid == source.series_uid
        assert result.view == source.view == AXIAL
        assert result.slices == source.slices
        assert result.code == source.code
        assert result.count == source.count
        assert result.off_plane_mm == source.off_plane_mm
        assert result.support == source.support == "a4_axial_joint_fluid"
        assert result.artifact == source.artifact
        assert result.row == source.row
        assert result.label is source.label is None
        assert "fluid-filled anterior patellofemoral cavity" in result.note
        assert "partial description" in result.note
        assert "full envelope" in result.note
    assert sources == [
        fluid(slice_index=21, row=0),
        fluid(slice_index=22, row=None, count=41),
    ]


def test_measured_empty_fluid_reading_stays_a_reading_without_claiming_absence():
    source = fluid(
        kind="reading",
        code="abstain_no_joint_fluid_in_patellofemoral_recesses",
        count=0,
    )

    found, missing = run.anterior_recess_from_axial_pockets([source], [])

    assert missing == []
    assert len(found) == 1
    assert found[0].object == "anterior_synovial_recess"
    assert found[0].kind == "reading"
    assert found[0].code == source.code
    assert found[0].count == 0
    assert found[0].support == source.support
    assert found[0].row == source.row
    assert "measured empty on this section" in found[0].note
    assert "does not say the cavity is absent elsewhere" in found[0].note


def test_axial_fluid_refusal_is_cloned_with_its_reason_and_unknown_status():
    source = Unresolved(
        "joint_fluid",
        "native",
        UID,
        AXIAL,
        "medial_side:selected_recess_mask_unavailable",
    )

    found, missing = run.anterior_recess_from_axial_pockets([], [source])

    assert found == []
    assert missing == [
        Unresolved(
            "anterior_synovial_recess",
            "native",
            UID,
            AXIAL,
            "axial_anterior_recess:medial_side:selected_recess_mask_unavailable",
        )
    ]
    assert source.object == "joint_fluid"
    assert source.code == "medial_side:selected_recess_mask_unavailable"


def test_partial_fluid_support_and_other_side_refusal_are_both_preserved():
    source = fluid(slice_index=21, row=0, count=19)
    refusal = Unresolved(
        "joint_fluid", "native", UID, AXIAL, "lateral_side:wall_code_unavailable"
    )

    found, missing = run.anterior_recess_from_axial_pockets([source], [refusal])

    assert len(found) == 1
    assert found[0].count == source.count
    assert found[0].support == source.support
    assert found[0].row == source.row
    assert found[0].kind == "resolved"
    assert len(missing) == 1
    assert missing[0].object == "anterior_synovial_recess"
    assert missing[0].code == "axial_anterior_recess:lateral_side:wall_code_unavailable"


def test_nonmatching_observations_and_unresolved_sources_are_excluded():
    sources = [
        fluid(object_name="joint_capsule"),
        fluid(provenance="laid"),
        fluid(provenance="projected", kind="target"),
        fluid(view=SAGITTAL),
        fluid(support="a3_recess_plane_fluid"),
    ]
    unresolved = [
        Unresolved("joint_fluid", "laid", UID, AXIAL, "transfer_failed"),
        Unresolved("joint_fluid", "native", UID, SAGITTAL, "not_axial"),
        Unresolved("joint_capsule", "native", UID, AXIAL, "other_object"),
    ]

    found, missing = run.anterior_recess_from_axial_pockets(sources, unresolved)

    assert found == []
    assert missing == []
