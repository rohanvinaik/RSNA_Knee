from types import SimpleNamespace

import numpy as np
import pytest

import scripts.run_interiors as runner
from knee.collapse.physical import PlaneFrame
from knee.study.series import Series, SeriesGeometry
from knee.study.tables import SeriesRow


def _coronal_source(target, study_uid, uid, *, row_changes=None):
    """Build an addressed native identity whose pixel center projects to AX [1, 5]."""
    target_point = target.frame.to_patient(np.asarray([[1.0, 5.0]]))[0]
    orientation = (1, 0, 0, 0, 0, 1)
    base_frame = PlaneFrame.from_dicom(
        np.zeros(3), np.asarray(orientation, dtype=float), np.ones(2)
    )
    source_rc = np.asarray((3.0, 4.0))
    origin = target_point - base_frame.basis_lps @ source_rc
    row = SeriesRow(study_uid, uid, "1", "1", "Coronal")
    geometry = SeriesGeometry(
        np.asarray([orientation], dtype=float),
        np.asarray([origin], dtype=float),
        np.ones((1, 2), dtype=float),
    )
    volume = np.zeros((1, 32, 32), dtype=np.float32)
    series = Series(row, (), ("stackable",), volume, geometry, (1.0, 1.0, 1.0))
    frame = runner.plane_frame(series, 0)
    label = runner.OBJECT_CODES["tibial_cartilage"]
    objects = np.zeros((32, 32), dtype=np.int32)
    objects[3, 4] = label
    record = {
        "series_uid": uid,
        "view": ["Coronal", "1", "1"],
        "slice_index": 0,
        "assignments": {"codes": {"tibial_cartilage": "identified"}},
    }
    observation = {
        "object": "tibial_cartilage",
        "provenance": "native",
        "kind": "resolved",
        "series_uid": uid,
        "view": ["Coronal", "1", "1"],
        "slices": [0],
        "code": "identified",
        "count": 1,
        "support": "a1_objects",
        "artifact": str(runner.artifact_of(study_uid, record)),
        "row": None,
        "label": label,
    }
    observation.update(row_changes or {})
    record["observations"] = [observation]
    measured = SimpleNamespace(
        record=record, arrays={"a1_objects": objects}, series=series, frame=frame
    )
    return measured


def _target():
    path = __file__.replace(
        "test_b10_tibial_cartilage_adapter.py",
        "test_b10_tibial_cartilage_reading.py",
    )
    import importlib.util

    spec = importlib.util.spec_from_file_location("b10_reading_fixtures", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    target, _, study_uid = module._fixture()
    target.frame = runner.plane_frame(target.series, 1)
    return target, study_uid


def test_coronal_identity_is_validated_then_handed_to_axial_reading():
    target, study_uid = _target()
    source = _coronal_source(target, study_uid, "1.2.3.coronal")

    said = runner.native_tibial_cartilage_readings([target, source], study_uid)

    axial_rows, axial_unknowns = said[0]
    assert not axial_unknowns
    assert len(axial_rows) == 1
    reading = axial_rows[0]
    assert (reading.object, reading.provenance, reading.kind) == (
        "tibial_cartilage",
        "native",
        "reading",
    )
    assert reading.view == ("Axial", "1", "1")
    assert reading.slices == (1,)
    assert reading.row == 0
    assert int(target.arrays[reading.support][reading.row].sum()) == reading.count
    assert source.record["observations"][0]["kind"] == "resolved"
    assert source.record["observations"][0]["series_uid"] == source.record["series_uid"]
    assert not any(
        row["kind"] == "resolved" and row["series_uid"] == target.record["series_uid"]
        for row in target.record.get("observations", [])
        if row.get("object") == "tibial_cartilage"
    )


@pytest.mark.parametrize(
    ("changes", "expected_fault"),
    [
        ({"view": ["Sagittal", "1", "1"]}, "source_observation_series_mismatch"),
        ({"count": 2}, "source_observation_count_mismatch"),
        ({"slices": [False]}, "source_observation_slice_mismatch"),
    ],
)
def test_malformed_coronal_identity_is_retained_as_axial_source_context_unknown(
    changes, expected_fault
):
    target, study_uid = _target()
    source = _coronal_source(
        target, study_uid, "1.2.3.coronal.bad", row_changes=changes
    )

    said = runner.native_tibial_cartilage_readings([target, source], study_uid)

    axial_rows, axial_unknowns = said[0]
    assert axial_rows == []
    assert any(
        item.code == f"source_context:{source.record['series_uid']}:{expected_fault}"
        for item in axial_unknowns
    )
    saved_faults = target.record["a4_axial_tibial_cartilage_source_faults"]
    assert any(item["code"] == expected_fault for item in saved_faults)
    assert source.record["observations"][0]["count"] == changes.get("count", 1)


def test_valid_identity_survives_alongside_malformed_identity_fault():
    target, study_uid = _target()
    valid = _coronal_source(target, study_uid, "1.2.3.coronal.good")
    malformed = _coronal_source(
        target,
        study_uid,
        "1.2.3.coronal.bad",
        row_changes={"count": 4},
    )

    said = runner.native_tibial_cartilage_readings(
        [target, valid, malformed], study_uid
    )

    axial_rows, axial_unknowns = said[0]
    assert len(axial_rows) == 1
    assert axial_rows[0].kind == "reading"
    assert int(target.arrays[axial_rows[0].support][axial_rows[0].row].sum()) == 2
    assert any(
        item.code
        == "source_context:1.2.3.coronal.bad:source_observation_count_mismatch"
        for item in axial_unknowns
    )
    assert any(
        item["code"] == "source_observation_count_mismatch"
        for item in target.record["a4_axial_tibial_cartilage_source_faults"]
    )
