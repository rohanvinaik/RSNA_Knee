from __future__ import annotations

import numpy as np

from knee.array_archive import open_arrays, write_npz_xz
from knee.encoding.operation import encode_study
from knee.json_store import load_json
from knee.receipt import digest


def _spec():
    return {
        "version": "sampled-profile-test-v1",
        "banks": [
            {
                "name": "sample",
                "facet": "retained sampled result",
                "metrics": [
                    {
                        "name": "white_sample",
                        "kind": "words",
                        "words": ["False", "True"],
                    }
                ],
            }
        ],
        "profiles": [
            {
                "object": "joint",
                "provenance": "native",
                "kind": "reading",
                "support": "a4_joint_axial_profile_white",
                "view": ["Axial", "1", "1"],
                "support_layout": {
                    "family": "joint_axial_profile_samples",
                    "offsets": "a4_joint_axial_profile_offsets",
                    "slices": "a4_joint_axial_profile_slices",
                    "coordinates": "a4_joint_axial_profile_rc",
                    "white": "a4_joint_axial_profile_white",
                    "valid": "a4_joint_axial_profile_valid",
                    "light": "a4_joint_axial_profile_light",
                },
                "readings": [
                    {
                        "bank": "sample",
                        "metric": "white_sample",
                        "value": "a4_joint_axial_profile_white",
                        "available": "a4_joint_axial_profile_valid",
                    }
                ],
                "references": [],
            }
        ],
    }


def _fixture(
    tmp_path,
    *,
    count=0,
    slices=(18,),
    digest_mutation=False,
    light_digest_mutation=False,
    two_dimensional_valid=False,
    two_dimensional_white=False,
):
    run_dir = tmp_path / "interiors"
    main_run = tmp_path / "main"
    artifact = "study/axial.npz.xz"
    arrays = {
        "a4_joint_axial_profile_offsets": np.array([0, 3], dtype=np.int64),
        "a4_joint_axial_profile_slices": np.array([18], dtype=np.int32),
        "a4_joint_axial_profile_rc": np.array([[2, 3], [2, 4], [5, 8]], dtype=np.int64),
        "a4_joint_axial_profile_valid": np.array([True, True, False]).reshape(
            (3, 1) if two_dimensional_valid else (3,)
        ),
        "a4_joint_axial_profile_white": np.array([False, False, False]).reshape(
            (3, 1) if two_dimensional_white else (3,)
        ),
        "a4_joint_axial_profile_light": np.array([4.0, 5.0, np.nan]),
    }
    path = run_dir / artifact
    path.parent.mkdir(parents=True, exist_ok=True)
    write_npz_xz(path, arrays)
    descriptors = {key: {"digest": digest(value)} for key, value in arrays.items()}
    if digest_mutation:
        descriptors["a4_joint_axial_profile_white"]["digest"] = "0" * 64
    if light_digest_mutation:
        descriptors["a4_joint_axial_profile_light"]["digest"] = "0" * 64
    observation = {
        "object": "joint",
        "provenance": "native",
        "kind": "reading",
        "series_uid": "axial-series",
        "view": ["Axial", "1", "1"],
        "slices": list(slices),
        "code": "abstain_no_white_sample_at_source_locations",
        "count": count,
        "off_plane_mm": 0.0,
        "support": "a4_joint_axial_profile_white",
        "artifact": artifact,
        "row": 0,
        "label": None,
    }
    record = {
        "study_uid": "study",
        "series_uid": "axial-series",
        "view": ["Axial", "1", "1"],
        "slice_index": 16,
        "artifact": artifact,
        "plane_frame": {"origin_lps": [0.0, 0.0, 0.0]},
        "axial_joint_compartment": {
            "pointed_planes": [
                {
                    "slice": 18,
                    "row": 0,
                    "support": "a4_joint_axial_profile_white",
                    "code": "abstain_no_white_sample_at_source_locations",
                    "count": count,
                }
            ]
        },
        "arrays": descriptors,
        "observations": [observation],
    }
    result = {
        "study_uid": "study",
        "records": [record],
        "main_records": [],
        "objects": {"joint": {}},
    }
    return run_dir, main_run, result


def test_encode_study_preserves_sampled_rc_row_and_white_count_meaning(tmp_path):
    run_dir, main_run, result = _fixture(tmp_path)
    links = encode_study(result, run_dir, main_run, _spec(), tmp_path / "out.json")
    manifest = load_json(links["manifest"])
    outcome = manifest["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "ok"
    assert outcome["address_kind"] == "native_rc_sample_points"
    assert outcome["metadata"]["target_slice"] == 18
    assert outcome["metadata"]["point_count"] == 3
    assert outcome["metadata"]["declared_count_meaning"] == "white_sample_count"
    assert outcome["metadata"]["measured_white_count"] == 0
    assert (
        outcome["metadata"]["target_frame_status"] == "per_slice_lps_basis_not_retained"
    )
    with open_arrays(links["archive"]) as archive:
        points = archive[outcome["points_rc"]]
        metric = outcome["metrics"][0]
        codes = archive[metric["row_codes"]]
    assert np.array_equal(points, [[2, 3], [2, 4], [5, 8]])
    assert np.array_equal(codes, [0, 0, -1])
    assert manifest["work"]["addressed_places"] == 3


def test_sample_count_is_not_confused_with_white_sample_count(tmp_path):
    run_dir, main_run, result = _fixture(tmp_path, count=3)
    links = encode_study(
        result, run_dir, main_run, _spec(), tmp_path / "bad-count.json"
    )
    outcome = load_json(links["manifest"])["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "sample_profile_white_count_mismatch"


def test_target_slice_must_match_the_selected_profile_row(tmp_path):
    run_dir, main_run, result = _fixture(tmp_path, slices=(16,))
    links = encode_study(
        result, run_dir, main_run, _spec(), tmp_path / "bad-slice.json"
    )
    outcome = load_json(links["manifest"])["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "sample_profile_slice_mismatch"


def test_sample_array_digest_is_checked_before_encoding(tmp_path):
    run_dir, main_run, result = _fixture(tmp_path, digest_mutation=True)
    links = encode_study(
        result, run_dir, main_run, _spec(), tmp_path / "bad-digest.json"
    )
    outcome = load_json(links["manifest"])["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "sample_profile_source_unavailable"
    assert outcome["metadata"]["detail"] == "sample_profile_digest_mismatch"


def test_sample_vector_payloads_must_be_one_dimensional(tmp_path):
    for field in ("valid", "white"):
        case_path = tmp_path / field
        run_dir, main_run, result = _fixture(
            case_path,
            two_dimensional_valid=field == "valid",
            two_dimensional_white=field == "white",
        )
        links = encode_study(
            result,
            run_dir,
            main_run,
            _spec(),
            case_path / "bad-shape.json",
        )
        outcome = load_json(links["manifest"])["profiles"][0]["outcomes"][0]
        assert outcome["status"] == "sample_profile_payload_shape_invalid"


def test_optional_sampled_light_read_failure_is_named(tmp_path):
    run_dir, main_run, result = _fixture(tmp_path, light_digest_mutation=True)
    spec = _spec()
    spec["banks"][0]["metrics"][0]["kind"] = "digit"
    spec["banks"][0]["metrics"][0].pop("words")
    spec["profiles"][0]["readings"][0].update(
        value="a4_joint_axial_profile_light",
        available="a4_joint_axial_profile_valid",
    )
    links = encode_study(result, run_dir, main_run, spec, tmp_path / "bad-light.json")
    outcome = load_json(links["manifest"])["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "sample_profile_source_unavailable"
    assert outcome["metadata"]["detail"] == "sample_profile_digest_mismatch"


def test_sampled_profile_accepts_unread_and_target_record_context_bindings(tmp_path):
    run_dir, main_run, result = _fixture(tmp_path)
    spec = _spec()
    spec["banks"].extend(
        [
            {
                "name": "context",
                "facet": "target acquisition descriptor",
                "metrics": [
                    {
                        "name": "view_orientation",
                        "kind": "words",
                        "words": ["Axial"],
                    }
                ],
            },
            {
                "name": "unread",
                "facet": "unretained facet",
                "metrics": [{"name": "detail", "kind": "digit"}],
            },
        ]
    )
    spec["profiles"][0]["readings"].extend(
        [
            {
                "bank": "context",
                "metric": "view_orientation",
                "source": "record_context",
                "path": ["view", 0],
                "scope": "acquisition",
            },
            {
                "bank": "unread",
                "metric": "detail",
                "source": "unread",
                "reason": "no sampled value is retained for this facet",
            },
        ]
    )
    links = encode_study(
        result, run_dir, main_run, spec, tmp_path / "shared-layout.json"
    )
    manifest = load_json(links["manifest"])
    outcome = manifest["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "ok"
    assert outcome["place_count"] == 3
    assert outcome["metadata"]["context_sources"][0]["value"] == "Axial"
    assert (
        outcome["metadata"]["context_sources"][0]["source_address"][
            "sample_slice_index"
        ]
        == 18
    )
    assert outcome["metadata"]["unread_sources"][0]["status"] == "unread"
    with open_arrays(links["archive"]) as archive:
        context_metric, unread_metric = outcome["metrics"][1:]
        assert np.array_equal(archive[context_metric["row_codes"]], [0, 0, 0])
        assert np.array_equal(archive[unread_metric["row_codes"]], [-1, -1, -1])
