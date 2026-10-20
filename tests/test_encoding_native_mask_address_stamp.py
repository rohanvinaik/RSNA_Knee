from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from knee.array_archive import open_arrays, write_npz_xz
from knee.collapse.physical import PlaneFrame
from knee.encoding.mri_spec import make_mri_spec
from knee.encoding.operation import (
    _retained_ordinary_dispositions,
    _retained_ordinary_profiles,
    digest,
    encode_study,
)
from knee.objects.assignments import OBJECT_CODES
from scripts import run_interiors as runner

FRAME = {
    "origin_lps": [12.0, -4.0, 7.0],
    "basis_lps": [[0.0, 1.3], [0.6, 0.0], [0.8, 0.0]],
}
VIEW = ["Axial", "1", "1"]
ARTIFACT = "study/series.npz.xz"
SUPPORT = "a4_unlisted_full_mask"
BOOL_DTYPE = np.dtype(np.bool_)


def _fixture(
    *,
    support: str = SUPPORT,
    shape: tuple[int, ...] = (2, 3, 4),
    dtype: np.dtype = BOOL_DTYPE,
    row: object = 1,
    z: int = 7,
    record_z: int = 4,
    frame: dict | None = None,
    provenance: str = "native",
    record_uid: str = "series",
    observation_uid: str = "series",
    artifact: str = ARTIFACT,
    observation_artifact: str = ARTIFACT,
    view: list[str] | None = None,
    stamp: str | None = None,
):
    volume = np.zeros((10, 3, 4), dtype=np.int16)
    series_row = SimpleNamespace(
        series_uid="series",
        anatomical_plane="Axial",
        fluid_sensitive="1",
        fat_suppression="1",
    )
    series = SimpleNamespace(row=series_row, volume=volume)
    selected = np.zeros(shape, dtype=dtype)
    if dtype.kind == "b" and len(shape) == 3:
        selected[1, 0, 1] = True
        selected[1, -1, -1] = True
    elif dtype.kind == "b" and len(shape) == 2:
        selected[0, 1] = True
        selected[-1, -1] = True
    elif dtype.kind in "iu" and len(shape) == 3:
        selected[1, 0, 1] = 3
        selected[1, 2, 3] = 3
    observation = {
        "artifact": observation_artifact,
        "series_uid": observation_uid,
        "object": "femur",
        "provenance": provenance,
        "kind": "reading",
        "support": support,
        "view": list(view or VIEW),
        "slices": [z],
        "row": row,
        "label": 3 if dtype.kind in "iu" else None,
        "count": 2,
    }
    if frame is not None:
        observation["address_frame"] = frame
    if stamp is not None:
        observation["support_address_kind"] = stamp
    record = {
        "artifact": artifact,
        "series_uid": record_uid,
        "study_uid": "study",
        "slice_index": record_z,
        "view": list(VIEW),
        "plane_frame": None,
        "observations": [observation],
    }
    own_record = {
        "artifact": ARTIFACT,
        "series_uid": "series",
        "view": list(VIEW),
    }
    own = runner.Measured(series, own_record, {}, None, None, None)
    descriptor = (tuple(selected.shape), selected.dtype.kind)
    return record, observation, own, selected, descriptor


def _attach(monkeypatch, record, observation, own, descriptor):
    frame = PlaneFrame.from_dicom(
        [12.0, -4.0, 7.0], [0.0, 1.0, 0.0, 0.0, 0.0, 1.0], [1.3, 0.6]
    )
    monkeypatch.setattr(runner, "plane_frame", lambda _series, _z: frame)
    runner.attach_full_native_mask_address_frames(
        [record],
        {"series": own},
        {ARTIFACT: {observation["support"]: descriptor}},
    )
    return frame


def test_same_owned_full_native_mask_is_stamped_and_existing_frame_is_preserved(
    monkeypatch,
):
    record, observation, own, _mask, descriptor = _fixture(
        shape=(3, 4), row=None, z=4, record_z=4, frame=FRAME
    )
    original_frame = dict(FRAME)
    _attach(monkeypatch, record, observation, own, descriptor)
    assert observation["support_address_kind"] == "native_rc"
    assert observation["address_frame"] == original_frame
    profile = _retained_ordinary_profiles([record], [])[0]
    assert profile["retained_address"]["support_address_kind"] == "native_rc"
    assert profile["retained_address"]["address_frame"] == original_frame


def test_full_native_row_mask_reaches_real_encode_study_without_migrating_b1_context(
    monkeypatch, tmp_path
):
    record, observation, own, mask, descriptor = _fixture()
    _attach(monkeypatch, record, observation, own, descriptor)
    assert observation["address_frame"] is not None
    assert observation["support_address_kind"] == "native_rc"

    arrays = {SUPPORT: mask}
    (tmp_path / "study").mkdir()
    write_npz_xz(tmp_path / ARTIFACT, arrays.items())
    record["arrays"] = {
        name: {"digest": digest(value)} for name, value in arrays.items()
    }
    own.record.update(record)
    prepared_spec = make_mri_spec(retained_ordinary_profiles=True)
    prepared_spec["storage"] = "npz_xz"
    from knee.encoding.operation import validate_spec

    prepared = validate_spec(prepared_spec)
    result = {
        "study_uid": "study",
        "records": [record],
        "main_records": [],
        "objects": {name: {} for name, code in OBJECT_CODES.items() if code != 0},
    }
    status = encode_study(
        result,
        tmp_path,
        tmp_path,
        prepared["spec"],
        tmp_path / "encoded.json.xz",
        prepared=prepared,
    )
    generated = [
        item
        for item in status["profiles"]
        if item.get("retained_expansion") is not None
    ]
    assert len(generated) == 1
    profile = generated[0]
    assert profile["retained_address"]["support_address_kind"] == "native_rc"
    outcome = profile["outcomes"][0]
    assert outcome["status"] in {"ok", "missing_reference"}
    assert outcome["metadata"]["plane_frame"] == observation["address_frame"]
    assert outcome["metadata"]["plane_frame_source"] == "observation.address_frame"
    assert set(outcome["metadata"]["source_refs"]) == {SUPPORT}
    assert all(
        binding["source"] == "unread"
        for binding in outcome["metadata"]["bindings"]
        if binding["bank"] != "acquisition_context"
    )
    assert all(
        source["source_address"]["slice_index"] == 4
        for source in outcome["metadata"]["context_sources"]
    )
    with open_arrays(status["archive"]) as stored:
        assert stored[outcome["points_rc"]].tolist() == [[0, 1], [2, 3]]


def test_unstamped_unknown_family_stays_named_unsupported():
    record, _observation, _own, _mask, _descriptor = _fixture()
    profiles = _retained_ordinary_profiles([record], [])
    assert profiles == []
    dispositions = _retained_ordinary_dispositions([record], [], (), [])
    assert dispositions[0]["disposition"] == "unsupported_family"
    assert dispositions[0]["support_address_kind"] is None


@pytest.mark.parametrize(
    "changes",
    [
        {"shape": (12, 3), "dtype": np.dtype(np.float32), "row": None},
        {"shape": (2, 3, 4), "dtype": np.dtype(np.float32), "row": 1},
        {"support": "a4_custom_crop", "shape": (2, 2), "row": None},
        {
            "support": "a4_custom_packed",
            "shape": (12, 3),
            "dtype": np.dtype(np.int16),
            "row": None,
        },
        {"shape": (2, 3, 4), "row": 2},
        {"shape": (2, 3, 4), "row": 1.0},
        {"record_uid": "different-series"},
        {"observation_artifact": "study/other.npz.xz"},
        {"observation_uid": "different-series"},
        {"view": ["Coronal", "1", "1"]},
        {"z": 10},
        {"z": -1},
        {"provenance": "laid"},
    ],
)
def test_ineligible_support_or_owner_is_never_stamped(monkeypatch, changes):
    record, observation, own, _mask, descriptor = _fixture(**changes)
    _attach(monkeypatch, record, observation, own, descriptor)
    assert observation.get("support_address_kind") is None
    profiles = _retained_ordinary_profiles([record], [])
    assert profiles == []


def test_invalid_preexisting_frame_does_not_receive_native_stamp(monkeypatch):
    invalid = {
        "origin_lps": [0.0, 1.0, 2.0],
        "basis_lps": [[1.0, 0.0], [2.0, 0.0], [0.0, 0.0]],
    }
    record, observation, own, _mask, descriptor = _fixture(
        shape=(3, 4), row=None, z=4, record_z=4, frame=invalid
    )
    _attach(monkeypatch, record, observation, own, descriptor)
    assert observation["address_frame"] == invalid
    assert observation.get("support_address_kind") is None
    assert _retained_ordinary_profiles([record], []) == []


def test_stale_stamp_is_revalidated_and_removed_for_wrong_dimensions(monkeypatch):
    record, observation, own, _mask, descriptor = _fixture(
        shape=(2, 2), row=None, z=4, record_z=4, stamp="native_rc"
    )
    _attach(monkeypatch, record, observation, own, descriptor)
    assert observation.get("support_address_kind") is None
    assert _retained_ordinary_profiles([record], []) == []


def test_retained_selector_binds_stamp_exactly(monkeypatch):
    record, observation, own, _mask, descriptor = _fixture(
        shape=(3, 4), row=None, z=4, record_z=4
    )
    _attach(monkeypatch, record, observation, own, descriptor)
    profile = _retained_ordinary_profiles([record], [])[0]
    from knee.encoding.operation import _matching_observations

    candidates = [(record, Path("/tmp"), "run")]
    assert len(list(_matching_observations(candidates, profile))) == 1
    observation["support_address_kind"] = "other"
    assert list(_matching_observations(candidates, profile)) == []


def test_laid_full_native_observation_keeps_existing_frame_attachment_without_stamp(
    monkeypatch,
):
    record, observation, own, _mask, descriptor = _fixture(
        provenance="laid", shape=(3, 4), row=None
    )
    _attach(monkeypatch, record, observation, own, descriptor)
    assert observation.get("address_frame") is not None
    assert observation.get("support_address_kind") is None
