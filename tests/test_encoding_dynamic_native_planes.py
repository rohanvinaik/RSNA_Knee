from __future__ import annotations

import json

import numpy as np

from knee.array_archive import open_arrays, write_npz_xz
from knee.encoding.mri_spec import make_mri_spec
from knee.encoding.operation import (
    _dynamic_native_plane_support,
    _retained_ordinary_dispositions,
    _retained_ordinary_profiles,
    digest,
    encode_study,
)
from knee.objects.assignments import OBJECT_CODES

FRAME = {
    "origin_lps": [12.0, -4.0, 8.0],
    "basis_lps": [[0.0, -1.0], [1.0, 0.0], [0.0, 0.0]],
}


def _observation(**changes):
    return {
        "artifact": "study/series.npz.xz",
        "series_uid": "series",
        "object": "medial_meniscus",
        "provenance": "native",
        "kind": "resolved",
        "support": "a4_axial_medial_meniscus_z7_support",
        "view": ["Axial", "1", "1"],
        "slices": [7],
        "row": None,
        "label": None,
        "count": 1,
        "address_frame": FRAME,
        **changes,
    }


def _record(observations):
    return {
        "artifact": "study/series.npz.xz",
        "series_uid": "series",
        "study_uid": "study",
        "slice_index": 3,
        "view": ["Axial", "1", "1"],
        "plane_frame": {
            "origin_lps": [0.0, 0.0, 0.0],
            "basis_lps": [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]],
        },
        "observations": observations,
    }


def test_dynamic_native_plane_supports_require_exact_object_view_and_slice():
    supported = _observation()
    record = _record([supported])
    profile = _retained_ordinary_profiles([record], [])[0]
    assert profile["support"] == supported["support"]
    assert profile["retained_address"]["address_frame"] == FRAME

    cases = [
        (_observation(slices=[8]), "dynamic_native_support_slice_mismatch"),
        (
            _observation(object="lateral_meniscus"),
            "dynamic_native_support_object_mismatch",
        ),
        (
            _observation(view=["Coronal", "1", "1"]),
            "dynamic_native_support_view_mismatch",
        ),
        (_observation(address_frame=None), "missing_observation_address_frame"),
        (_observation(row=0), "dynamic_native_support_address_malformed"),
    ]
    for observation, expected in cases:
        current = _record([observation])
        profiles = _retained_ordinary_profiles([current], [])
        assert profiles == []
        dispositions = _retained_ordinary_dispositions([current], [], (), profiles)
        assert dispositions[0]["disposition"] == expected


def test_native_menisci_and_ligament_key_families_are_bounded():
    candidates = [
        ("a4_medial_meniscus_z7_support", "medial_meniscus", "Sagittal"),
        ("a4_axial_lateral_meniscus_z9_support", "lateral_meniscus", "Axial"),
        ("a4_axial_mcl_z11_support", "mcl", "Axial"),
        ("a4_coronal_pcl_z12_support", "pcl", "Coronal"),
    ]
    for support, object_name, orientation in candidates:
        observation = _observation(
            support=support,
            object=object_name,
            view=[orientation, "1", "1"],
            slices=[int(support.split("_z")[-1].removesuffix("_support"))],
        )
        profile = _retained_ordinary_profiles([_record([observation])], [])[0]
        assert profile["support"] == support
        assert profile["object"] == object_name

    unsupported = _observation(
        support="a4_coronal_mcl_z11_support",
        object="mcl",
        view=["Coronal", "1", "1"],
        slices=[11],
    )
    assert _retained_ordinary_profiles([_record([unsupported])], []) == []


def test_dynamic_native_plane_key_parser_positive_and_negative_intent():
    accepted = {
        "a4_medial_meniscus_z7_support": ("medial_meniscus", "sagittal", 7),
        "a4_lateral_meniscus_z0_support": ("lateral_meniscus", "sagittal", 0),
        "a4_axial_medial_meniscus_z12_support": (
            "medial_meniscus",
            "axial",
            12,
        ),
        "a4_axial_lateral_meniscus_z9_support": (
            "lateral_meniscus",
            "axial",
            9,
        ),
        "a4_axial_pcl_z15_support": ("pcl", "axial", 15),
        "a4_axial_mcl_z13_support": ("mcl", "axial", 13),
        "a4_coronal_pcl_z22_support": ("pcl", "coronal", 22),
    }
    for support, expected in accepted.items():
        assert _dynamic_native_plane_support(support) == expected

    rejected = (
        None,
        "a4_coronal_mcl_z11_support",
        "a4_coronal_pcl_z022_support",
        "a4_axial_pcl_z-1_support",
        "a4_axial_pcl_z15",
        "a4_fibula_coarse_series_pcl_z15_support",
        "a4_axial_pcl_z" + "9" * 5000 + "_support",
        "a4_axial_pcl_z١_support",
    )
    for support in rejected:
        assert _dynamic_native_plane_support(support) is None


def test_encode_study_uses_the_dynamic_plane_frame_without_off_slice_b1_reads(
    tmp_path,
):
    spec = make_mri_spec(retained_ordinary_profiles=True)
    spec["storage"] = "npz_xz"
    support = np.zeros((4, 5), dtype=np.bool_)
    support[3, 4] = True
    arrays = {
        "a4_axial_medial_meniscus_z7_support": support,
        "acquired_plane": np.full((4, 5), 999, dtype=np.int16),
        "b1_dark": np.ones((4, 5), dtype=np.bool_),
        "b1_available": np.ones((4, 5), dtype=np.bool_),
        "b1_distance_mm": np.full((4, 5), 123.0, dtype=np.float32),
    }
    artifact = "study/series.npz.xz"
    (tmp_path / "study").mkdir()
    write_npz_xz(tmp_path / artifact, arrays.items())
    record = _record([_observation()])
    record["arrays"] = {key: {"digest": digest(value)} for key, value in arrays.items()}
    result = {
        "study_uid": "study",
        "records": [record],
        "main_records": [],
        "objects": {name: {} for name, code in OBJECT_CODES.items() if code != 0},
    }

    statuses = encode_study(
        result,
        tmp_path,
        tmp_path,
        spec,
        tmp_path / "encoded.json.xz",
    )
    generated = [
        profile
        for profile in statuses["profiles"]
        if profile.get("retained_expansion") is not None
    ]
    assert len(generated) == 1
    outcome = generated[0]["outcomes"][0]
    assert outcome["metadata"]["plane_frame"] == FRAME
    assert outcome["metadata"]["plane_frame_source"] == "observation.address_frame"
    assert set(outcome["metadata"]["source_refs"]) == {
        "a4_axial_medial_meniscus_z7_support"
    }
    assert all(
        reading["source"] == "unread"
        for reading in outcome["metadata"]["bindings"]
        if reading["bank"] != "acquisition_context"
    )
    with open_arrays(statuses["archive"]) as archive:
        assert archive[outcome["points_rc"]].tolist() == [[3, 4]]
    assert not any(
        name.startswith("b1_") or name == "acquired_plane"
        for name in outcome["metadata"]["source_refs"]
    )
    assert (
        json.loads(json.dumps(generated[0]["retained_address"]))["address_frame"]
        == FRAME
    )
