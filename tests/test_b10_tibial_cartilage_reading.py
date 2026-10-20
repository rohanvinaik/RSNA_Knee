from types import SimpleNamespace

import numpy as np
import pytest

import scripts.run_interiors as runner
from knee.collapse.physical import PlaneFrame
from knee.study.series import Series, SeriesGeometry
from knee.study.tables import SeriesRow
from scripts.run_interiors import (
    PosteriorSource,
    _native_tibial_cartilage_references,
    _tibial_cartilage_brightness_components,
    axial_tibial_cartilage_readings,
)


def _plane_geometry(depth: int, orientation: tuple[float, ...], positions: np.ndarray):
    return SeriesGeometry(
        np.tile(np.asarray(orientation, dtype=float), (depth, 1)),
        np.asarray(positions, dtype=float),
        np.ones((depth, 2), dtype=float),
    )


def _fixture(*, reference=True, second_reference=False, tied_target_slices=False):
    uid = "1.2.3.axial"
    study_uid = "1.2.3.study"
    shape = (32, 32)
    volume = np.full((3, *shape), 10.0, dtype=np.float32)
    volume[1, 1, 6] = 16.0
    volume[1, 2, 5] = 17.0
    volume[1, 15, 15] = 20.0
    volume[1, 2, 6] = np.nan
    volume[1, 1, 7] = 15.0
    row = SeriesRow(study_uid, uid, "1", "1", "Axial")
    positions = np.asarray(((0, 0, 0), (0, 0, 1), (0, 0, 2)), dtype=float)
    if tied_target_slices:
        positions[2] = positions[1]
    geometry = _plane_geometry(3, (1, 0, 0, 0, 1, 0), positions)
    series = Series(row, (), ("stackable",), volume, geometry, (1.0, 1.0, 1.0))
    record = {
        "series_uid": uid,
        "view": ["Axial", "1", "1"],
        "slice_index": 1,
    }
    arrays = {}
    if reference:
        calibration_mask = np.zeros(shape, dtype=bool)
        calibration_mask[2, 2] = True
        if second_reference:
            calibration_mask[3, 3] = True
            candidate_rows = [
                {
                    "slice": 0,
                    "status": "selected_native_component",
                    "marrow_median": 10.0,
                    "brightness_level": 15.0,
                },
                {
                    "slice": 2,
                    "status": "selected_native_component",
                    "marrow_median": 12.0,
                    "brightness_level": 18.0,
                },
            ]
            reference_slices = np.asarray((0, 2), dtype=np.int32)
            lights = np.asarray((10.0, 12.0), dtype=np.float64)
            masks = np.stack((np.eye(32, dtype=bool), calibration_mask))
        else:
            candidate_rows = [
                {
                    "slice": 0,
                    "status": "selected_native_component",
                    "marrow_median": 10.0,
                    "brightness_level": 15.0,
                }
            ]
            reference_slices = np.asarray((0,), dtype=np.int32)
            lights = np.asarray((10.0,), dtype=np.float64)
            masks = calibration_mask[None, ...]
        record["a4_axial_femoral_cartilage_candidates"] = candidate_rows
        record["a4_axial_femoral_cartilage_coarse_context"] = [
            {
                "slice": int(z),
                "status": "section",
                "section_area_mm2": 1.0,
                "section_level": 1.0,
            }
            for z in reference_slices
        ]
        available_masks = np.ones_like(masks, dtype=bool)
        arrays.update(
            {
                "a4_axial_femoral_cartilage_context_marrow_median_values": lights,
                "a4_axial_femoral_cartilage_context_marrow_median_slices": reference_slices,
                "a4_axial_femoral_cartilage_context_selected_enclosure_values": masks.reshape(
                    -1
                ),
                "a4_axial_femoral_cartilage_context_selected_enclosure_offsets": np.arange(
                    len(masks) + 1, dtype=np.int64
                )
                * (32 * 32),
                "a4_axial_femoral_cartilage_context_selected_enclosure_shapes": np.tile(
                    (32, 32), (len(masks), 1)
                ).astype(np.int32),
                "a4_axial_femoral_cartilage_context_selected_enclosure_slices": reference_slices,
                "a4_axial_femoral_cartilage_context_available_values": available_masks.reshape(
                    -1
                ),
                "a4_axial_femoral_cartilage_context_available_offsets": np.arange(
                    len(masks) + 1, dtype=np.int64
                )
                * (32 * 32),
                "a4_axial_femoral_cartilage_context_available_shapes": np.tile(
                    (32, 32), (len(masks), 1)
                ).astype(np.int32),
                "a4_axial_femoral_cartilage_context_available_slices": reference_slices,
            }
        )
    own = SimpleNamespace(record=record, arrays=arrays, series=series)
    source_uid = "1.2.3.sagittal"
    source_frame = PlaneFrame.from_dicom(
        np.asarray((5.0, 0.0, -4.0)),
        np.asarray((0.0, 1.0, 0.0, 0.0, 0.0, 1.0)),
        np.ones(2),
    )
    source_mask = np.zeros(shape, dtype=bool)
    source_mask[5, 1] = True
    source_record = {
        "series_uid": source_uid,
        "view": ["Sagittal", "1", "1"],
        "slice_index": 0,
    }
    source = PosteriorSource(
        "tibial_cartilage",
        source_record,
        {"a3_joint_plane_reading": source_mask},
        source_frame,
        source_mask,
        "a3_joint_plane_reading",
        12,
        f"{study_uid}/{source_uid}.npz.xz",
        1,
    )
    return own, source, study_uid


def _legacy_components_oracle(raw, available, target, spacing, light):
    effective = available & np.isfinite(raw)
    bright = effective & (raw > runner.CARTILAGE_BRIGHTER * light)
    labels, count = runner.ndi.label(bright)
    distance = runner.ndi.distance_transform_edt(~target, sampling=spacing)
    support = np.zeros(raw.shape, dtype=bool)
    components = []
    contacts = []
    for label in range(1, int(count) + 1):
        component = labels == label
        rc = np.argwhere(component)
        distances = distance[component]
        contacted = bool(np.any(distances <= runner.SHELL_MM))
        if contacted:
            support |= component
            contacts.append(label)
        components.append(
            {
                "label": label,
                "pixels": int(component.sum()),
                "bbox_rc_exclusive": [
                    int(min(rc[:, 0])),
                    int(max(rc[:, 0])) + 1,
                    int(min(rc[:, 1])),
                    int(max(rc[:, 1])) + 1,
                ],
                "minimum_source_distance_mm": float(distances.min()),
                "contact_pixels_within_shell": int(
                    np.count_nonzero(component & (distance <= runner.SHELL_MM))
                ),
                "contacted": contacted,
                "touches_crop_edge": bool(
                    component[0].any()
                    or component[-1].any()
                    or component[:, 0].any()
                    or component[:, -1].any()
                ),
                "touches_unavailable_pixels": bool(
                    np.any(runner.ndi.binary_dilation(component) & ~effective)
                ),
            }
        )
    return {
        "bright": bright,
        "labels": labels.astype(np.int32, copy=False),
        "distance_mm": distance,
        "support": support,
        "component_count": int(count),
        "contact_labels": contacts,
        "components": components,
    }


def test_brightness_uses_exact_existing_threshold_and_unions_all_contacts():
    raw = np.full((9, 9), 10.0)
    raw[4, 5] = 15.0  # exactly at threshold is not brighter
    raw[4, 6] = 16.0
    raw[6, 4] = 17.0  # another contacted component; no largest winner
    raw[0, 0] = 20.0  # measured but outside source-contact shell
    available = np.ones(raw.shape, dtype=bool)
    target = np.zeros(raw.shape, dtype=bool)
    target[4, 4] = True

    result = _tibial_cartilage_brightness_components(
        raw, available, target, np.ones(2), 10.0
    )

    assert result["status"] == "measured"
    assert result["threshold"] == 15.0
    assert not result["bright"][4, 5]
    assert result["component_count"] == 3
    assert result["contact_labels"] == [2, 3]
    assert result["support"].sum() == 2
    assert [row["contacted"] for row in result["components"]] == [False, True, True]
    assert [row["minimum_source_distance_mm"] for row in result["components"]] == [
        5.656854249492381,
        2.0,
        2.0,
    ]


def test_nonfinite_and_unavailable_pixels_are_not_labeled_or_supported():
    raw = np.full((7, 7), 10.0)
    raw[3, 4] = 18.0
    raw[2, 3] = np.nan
    raw[3, 5] = 19.0
    available = np.ones(raw.shape, dtype=bool)
    available[3, 5] = (
        False  # adjacent margin exclusion already computed by production helper
    )
    available[2, 3] = False  # nonfinite exclusion from finite_of plus raw guard
    target = np.zeros(raw.shape, dtype=bool)
    target[3, 3] = True

    result = _tibial_cartilage_brightness_components(
        raw, available, target, np.ones(2), 10.0
    )

    assert result["status"] == "measured"
    assert result["bright"][3, 4]
    assert not result["labels"][2, 3]
    assert not result["labels"][3, 5]
    assert result["support"].sum() == 1
    assert result["components"][0]["touches_unavailable_pixels"] is True


def test_empty_or_malformed_inputs_keep_named_unknowns():
    raw = np.ones((3, 4), dtype=float)
    available = np.zeros(raw.shape, dtype=bool)
    target = np.ones(raw.shape, dtype=bool)
    assert (
        _tibial_cartilage_brightness_components(
            raw, available, target, np.ones(2), 1.0
        )["status"]
        == "native_availability_empty"
    )
    assert (
        _tibial_cartilage_brightness_components(
            raw, np.ones((2, 2), dtype=bool), target, np.ones(2), 1.0
        )["status"]
        == "native_measurement_unavailable"
    )
    assert (
        _tibial_cartilage_brightness_components(
            raw, np.ones(raw.shape, dtype=bool), target, np.ones(2), float("nan")
        )["status"]
        == "native_measurement_unavailable"
    )


def test_driver_profiles_actual_cross_view_source_and_addresses_native_support():
    own, source, study_uid = _fixture()

    observations, unresolved = axial_tibial_cartilage_readings(
        [own], [source], study_uid
    )[0]

    assert unresolved == []
    assert len(observations) == 1
    reading = observations[0]
    assert reading.object == "tibial_cartilage"
    assert reading.provenance == "native"
    assert reading.kind == "reading"
    assert reading.slices == (1,)  # projected source is z0 in its own SAG acquisition
    assert reading.support == "a4_axial_tibial_cartilage_brightness_support"
    support = own.arrays[reading.support]
    assert support.shape == (1, 32, 32)
    assert int(support[reading.row].sum()) == reading.count == 2
    assert own.record["a4_axial_tibial_cartilage_source_profiles"][0][
        "maximum_slices"
    ] == [1]
    result_record = own.record["a4_axial_tibial_cartilage_readings"][0]
    assert result_record["slice"] == 1
    assert result_record["references"][0]["reference_sources"][0]["source_slice"] == 0
    assert (
        "not target-slice marrow"
        in result_record["references"][0]["reference_sources"][0]["reference_meaning"]
    )
    assert result_record["window_rc_exclusive"] == [0, 12, 0, 16]
    assert own.arrays["a4_axial_tibial_cartilage_z1_available_crop"][2, 6] is np.False_
    assert not own.arrays["a4_axial_tibial_cartilage_z1_r0_bright_crop"][2, 6]


def test_driver_retains_distinct_existing_same_acquisition_references():
    own, source, study_uid = _fixture(second_reference=True)

    observations, unresolved = axial_tibial_cartilage_readings(
        [own], [source], study_uid
    )[0]

    assert unresolved == []
    assert len(observations) == 2
    reading = own.record["a4_axial_tibial_cartilage_readings"][0]
    assert [row["light"] for row in reading["references"]] == [10.0, 12.0]
    assert [row["threshold"] for row in reading["references"]] == [15.0, 18.0]
    assert [item.row for item in observations] == [0, 1]
    support = own.arrays["a4_axial_tibial_cartilage_brightness_support"]
    assert [int(support[item.row].sum()) for item in observations] == [2, 0]


def test_unavailable_reference_keeps_profile_and_names_unknown():
    own, source, study_uid = _fixture(reference=False)

    observations, unresolved = axial_tibial_cartilage_readings(
        [own], [source], study_uid
    )[0]

    assert observations == []
    assert [item.code for item in unresolved] == [
        "native_slice_1:native_brightness_reference_unavailable"
    ]
    assert own.record["a4_axial_tibial_cartilage_source_profiles"][0][
        "maximum_slices"
    ] == [1]
    assert (
        own.record["a4_axial_tibial_cartilage_source_candidates"][0]["target_slice"]
        == 1
    )


def test_reference_requires_owner_acquisition_identity():
    own, _, _ = _fixture()
    own.record["series_uid"] = "1.2.3.other-acquisition"

    references, code = _native_tibial_cartilage_references(own)

    assert references == []
    assert code == "native_brightness_reference_unavailable"


def test_profile_ties_keep_each_native_target_slice_and_empty_reading():
    own, source, study_uid = _fixture(tied_target_slices=True)

    observations, unresolved = axial_tibial_cartilage_readings(
        [own], [source], study_uid
    )[0]

    assert unresolved == []
    assert [row.slices for row in observations] == [(1,), (2,)]
    profile = own.record["a4_axial_tibial_cartilage_source_profiles"][0]
    assert profile["maximum_slices"] == [1, 2]
    assert [row.code for row in observations] == [
        "native_brightness_components_contacted",
        "measured_empty_native_brightness_contact",
    ]
    support = own.arrays["a4_axial_tibial_cartilage_brightness_support"]
    assert [int(support[row.row].sum()) for row in observations] == [2, 0]


def test_batched_components_match_legacy_values_and_reuse_distance():
    raw = np.full((13, 15), 10.0)
    raw[0, 0:2] = 18.0
    raw[3:5, 8] = 17.0
    raw[9, 4:7] = 16.0
    raw[12, 14] = 20.0
    raw[2, 9] = np.nan
    available = np.ones(raw.shape, dtype=bool)
    available[4, 9] = False
    available[2, 9] = False
    target = np.zeros(raw.shape, dtype=bool)
    target[6, 7] = True
    spacing = np.asarray((0.7, 1.3))
    distance = runner.ndi.distance_transform_edt(~target, sampling=spacing)
    expected = _legacy_components_oracle(raw, available, target, spacing, 10.0)
    calls = 0
    actual_distance = runner.ndi.distance_transform_edt

    def counted_distance(*args, **kwargs):
        nonlocal calls
        calls += 1
        return actual_distance(*args, **kwargs)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(runner.ndi, "distance_transform_edt", counted_distance)
    result = _tibial_cartilage_brightness_components(
        raw, available, target, spacing, 10.0, distance_mm=distance
    )
    monkeypatch.undo()

    assert calls == 0
    for key in ("bright", "labels", "distance_mm", "support"):
        np.testing.assert_array_equal(result[key], expected[key])
    for key in ("component_count", "contact_labels", "components"):
        assert result[key] == expected[key]


def test_multiple_references_share_one_target_distance_transform(monkeypatch):
    own, source, study_uid = _fixture(second_reference=True)
    calls = 0
    actual_distance = runner.ndi.distance_transform_edt

    def counted_distance(*args, **kwargs):
        nonlocal calls
        calls += 1
        return actual_distance(*args, **kwargs)

    monkeypatch.setattr(runner.ndi, "distance_transform_edt", counted_distance)
    observations, unresolved = axial_tibial_cartilage_readings(
        [own], [source], study_uid
    )[0]

    assert unresolved == []
    assert len(observations) == 2
    assert calls == 1


def test_malformed_reference_offsets_and_exact_brightness_identity_are_unknown():
    own, _, _ = _fixture()
    own.arrays["a4_axial_femoral_cartilage_context_selected_enclosure_offsets"] = (
        np.asarray((0, 1), dtype=np.int64)
    )
    references, code = runner._native_tibial_cartilage_references(own)
    assert references == []
    assert code == "native_brightness_reference_malformed"

    own, _, _ = _fixture()
    own.record["a4_axial_femoral_cartilage_candidates"][0]["brightness_level"] += 1e-13
    references, code = runner._native_tibial_cartilage_references(own)
    assert references == []
    assert code == "native_brightness_reference_unavailable"


def test_reference_reader_records_only_existing_calibration_fields(monkeypatch):
    own, _, _ = _fixture()
    consumed = []
    monkeypatch.setattr(
        runner,
        "reads",
        lambda product, names, stage: consumed.extend(
            f"{product}.{name}.consumed_by.{stage}" for name in names
        ),
    )

    references, code = _native_tibial_cartilage_references(own)

    assert code is None
    assert len(references) == 1
    expected_fields = {
        "marrow_median_values",
        "marrow_median_slices",
        "selected_enclosure_values",
        "selected_enclosure_offsets",
        "selected_enclosure_shapes",
        "selected_enclosure_slices",
        "available_values",
        "available_offsets",
        "available_shapes",
        "available_slices",
    }
    context_reads = {
        item
        for item in consumed
        if item.startswith("native_femoral_cartilage_context.")
    }
    assert context_reads == {
        f"native_femoral_cartilage_context.{field}.consumed_by._native_tibial_cartilage_references"
        for field in expected_fields
    }

    consumed.clear()
    del own.arrays["a4_axial_femoral_cartilage_context_available_offsets"]
    references, code = _native_tibial_cartilage_references(own)

    assert references == []
    assert code == "native_brightness_reference_unavailable"
    assert not any("available_offsets" in item for item in consumed)
    assert all(
        item.startswith("native_femoral_cartilage_context.") for item in consumed
    )
