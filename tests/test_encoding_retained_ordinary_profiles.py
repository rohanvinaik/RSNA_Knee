from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import numpy as np

from knee.array_archive import write_npz_xz
from knee.encoding.mri_spec import make_mri_spec
from knee.encoding.operation import (
    _expand_retained_profiles,
    _matching_observations,
    _retained_ordinary_profiles,
    digest,
    encode_study,
    validate_spec,
)
from knee.encoding.product import open_product
from knee.json_store import load_json
from knee.objects.assignments import OBJECT_CODES

FRAME = {
    "origin_lps": [0.0, 0.0, 0.0],
    "basis_lps": [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]],
}


def _observation(**changes):
    base = {
        "artifact": "study/series.npz.xz",
        "series_uid": "series",
        "object": "femur",
        "provenance": "native",
        "kind": "resolved",
        "support": "a2_joint_capsule",
        "view": ["Axial", "1", "1"],
        "slices": [4],
        "row": None,
        "label": None,
        "count": 1,
    }
    return {**base, **changes}


def _record(observations):
    return {
        "artifact": "study/series.npz.xz",
        "series_uid": "series",
        "study_uid": "study",
        "slice_index": 4,
        "view": ["Axial", "1", "1"],
        "observations": observations,
    }


def test_expansion_uses_exact_same_slice_and_explicit_row_addresses_only():
    same_slice = _observation()
    framed_row = _observation(
        support="a3_joint_plane_objects",
        kind="reading",
        slices=[7],
        row=2,
        address_frame=FRAME,
        count=9,
    )
    unframed_row = _observation(
        support="a3_joint_plane_objects", slices=[8], row=3, address_frame=None
    )
    projected = _observation(
        support="a2_joint_capsule", provenance="projected", kind="target"
    )
    unknown_family = _observation(support="a3_unlisted_plane_region", row=0)
    cross_artifact = _observation(artifact="study/other.npz.xz")
    record = _record(
        [
            same_slice,
            framed_row,
            unframed_row,
            projected,
            unknown_family,
            cross_artifact,
        ]
    )

    profiles = _retained_ordinary_profiles([record], [])
    assert len(profiles) == 2
    by_index = {p["retained_address"]["observation_index"]: p for p in profiles}
    assert set(by_index) == {0, 1}
    assert by_index[0]["support"] == "a2_joint_capsule"
    assert by_index[0]["readings"][0].get("source", "array") == "array"
    assert by_index[1]["support"] == "a3_joint_plane_objects"
    assert by_index[1]["retained_address"]["row"] == 2
    assert by_index[1]["retained_address"]["address_frame"] == FRAME
    assert all(
        x["source"] == "unread"
        for x in by_index[1]["readings"]
        if x["bank"] != "acquisition_context"
    )
    assert all(
        x["source"] == "record_context"
        for x in by_index[1]["readings"]
        if x["bank"] == "acquisition_context"
    )

    from knee.encoding.operation import _retained_ordinary_dispositions

    reasons = {
        row["observation_index"]: row["disposition"]
        for row in _retained_ordinary_dispositions([record], [], (), profiles)
    }
    assert reasons[2] == "missing_observation_address_frame"
    assert reasons[3] == "projected_target_not_observation"
    assert reasons[4] == "unsupported_family"
    assert reasons[5] == "different_owner_artifact"


def test_generated_profile_matches_only_its_exact_observation_slot():
    observations = [_observation(), _observation(count=2)]
    record = _record(observations)
    profile = _retained_ordinary_profiles([record], [])[0]
    candidates = [(record, __import__("pathlib").Path("/tmp"), "run")]

    matches = list(_matching_observations(candidates, profile))
    assert len(matches) == 1
    assert matches[0][3] is observations[0]

    changed = deepcopy(record)
    changed["observations"][0]["address_frame"] = FRAME
    assert (
        list(
            _matching_observations(
                [(changed, __import__("pathlib").Path("/tmp"), "run")], profile
            )
        )
        == []
    )


def test_expansion_is_opt_in_and_reuses_prepared_composition(monkeypatch):
    records = [_record([_observation()])]
    disabled = validate_spec(make_mri_spec())
    assert len(_expand_retained_profiles(disabled, records, [])["profiles"]) == len(
        disabled["profiles"]
    )

    enabled = validate_spec(make_mri_spec(retained_ordinary_profiles=True))
    from knee.encoding import operation

    def unexpected_recompile(*args, **kwargs):
        raise AssertionError("dynamic expansion must reuse declaration preparation")

    monkeypatch.setattr(operation, "prepare_composition", unexpected_recompile)
    original_composition = enabled["composition"]
    expanded = _expand_retained_profiles(enabled, records, [])
    assert len(expanded["profiles"]) == len(enabled["profiles"]) + 1
    assert expanded["layout"] is enabled["layout"]
    assert expanded["carrier"] is enabled["carrier"]
    assert expanded["composition"].layout is original_composition.layout
    assert expanded["composition"].carrier is original_composition.carrier
    assert expanded["composition"].expansion is original_composition.expansion
    assert (
        expanded["composition"].profile_layouts is original_composition.profile_layouts
    )
    assert (
        len(expanded["composition"].profiles) == len(original_composition.profiles) + 1
    )
    assert expanded["spec_sha256"] != enabled["spec_sha256"]
    assert (
        expanded["profiles"][-1]["retained_expansion"]
        == "ordinary_known_plane_family_v1"
    )


def test_encode_study_emits_the_generated_profile_for_its_real_owner(tmp_path):
    spec = make_mri_spec(retained_ordinary_profiles=True)
    spec["storage"] = "npz_xz"
    prepared = validate_spec(spec)
    arrays = {
        "a2_joint_capsule": np.asarray([[True, False], [False, True]]),
        "b1_dark": np.asarray([[False, True], [True, False]]),
        "b1_available": np.ones((2, 2), dtype=np.bool_),
        "acquired_plane": np.asarray([[11, 12], [13, 14]], dtype=np.int16),
        "b1_distance_mm": np.asarray([[0.0, 1.0], [2.0, 3.0]], dtype=np.float32),
    }
    artifact = "study/series.npz.xz"
    (tmp_path / "study").mkdir()
    write_npz_xz(tmp_path / artifact, arrays.items())
    observation = _observation(count=2)
    record = _record([observation])
    record["arrays"] = {
        name: {"digest": digest(array)} for name, array in arrays.items()
    }
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
        prepared["spec"],
        tmp_path / "encoded.json.xz",
        prepared=prepared,
    )

    generated = [
        profile
        for profile in statuses["profiles"]
        if profile.get("retained_expansion") is not None
    ]
    assert len(generated) == 1
    outcome = generated[0]["outcomes"][0]
    assert outcome["artifact"] == artifact
    assert outcome["status"] == "missing_reference"
    assert generated[0]["retained_address"]["slices"] == [4]
    manifest = Path(statuses["manifest"])
    assert manifest.is_file()
    saved = load_json(manifest)
    canonical_spec = json.dumps(
        saved["spec"],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    assert saved["spec_sha256"] == hashlib.sha256(canonical_spec).hexdigest()
    assert saved["spec_sha256"] != prepared["spec_sha256"]
    assert (
        statuses["retained_ordinary_expansion_state"]["expanded_observation_count"] == 1
    )


def test_coarse_factory_pads_generated_ordinary_profiles_for_every_declared_bank(
    tmp_path, monkeypatch
):
    spec = make_mri_spec(include_coarse=True, retained_ordinary_profiles=True)
    prepared = validate_spec(spec)
    arrays = {
        "a2_joint_capsule": np.asarray([[True, False], [False, True]]),
        "b1_dark": np.asarray([[False, True], [True, False]]),
        "b1_available": np.ones((2, 2), dtype=np.bool_),
        "acquired_plane": np.asarray([[11, 12], [13, 14]], dtype=np.int16),
        "b1_distance_mm": np.asarray([[0.0, 1.0], [2.0, 3.0]], dtype=np.float32),
    }
    artifact = "study/series.npz.xz"
    (tmp_path / "study").mkdir()
    write_npz_xz(tmp_path / artifact, arrays.items())
    record = _record([_observation(count=2)])
    record["arrays"] = {
        name: {"digest": digest(array)} for name, array in arrays.items()
    }
    result = {
        "study_uid": "study",
        "records": [record],
        "main_records": [],
        "objects": {name: {} for name, code in OBJECT_CODES.items() if code != 0},
    }

    from knee.encoding import operation

    def unexpected_recompile(*args, **kwargs):
        raise AssertionError("generated profiles must reuse prepared compilation")

    monkeypatch.setattr(operation, "prepare_composition", unexpected_recompile)
    statuses = encode_study(
        result,
        tmp_path,
        tmp_path,
        prepared["spec"],
        tmp_path / "encoded.json.xz",
        prepared=prepared,
    )

    generated = [
        profile
        for profile in statuses["profiles"]
        if profile.get("retained_expansion") is not None
    ]
    assert len(generated) == 1
    profile = generated[0]
    with open_product(statuses["manifest"]) as product:
        saved = product.manifest
    declared_profile = saved["spec"]["profiles"][profile["profile_index"]]
    bindings = {
        (item["bank"], item["metric"]): item for item in declared_profile["readings"]
    }
    expected = {
        (bank["name"], metric["name"])
        for bank in spec["banks"]
        for metric in bank["metrics"]
    }
    assert set(bindings) == expected
    for coarse_bank in ("coarse_unfiltered", "coarse_scale_filtered"):
        for metric in next(b for b in spec["banks"] if b["name"] == coarse_bank)[
            "metrics"
        ]:
            binding = bindings[(coarse_bank, metric["name"])]
            assert binding["source"] == "unread"
            assert binding["reason"]
    assert profile["outcomes"][0]["status"] == "missing_reference"


def test_patellofemoral_native_row_supports_keep_slice_frame_and_context(tmp_path):
    spec = make_mri_spec(retained_ordinary_profiles=True)
    spec["storage"] = "npz_xz"
    prepared = validate_spec(spec)
    patella = np.zeros((3, 4), dtype=np.bool_)
    patella[0, 1] = True
    patella[2, 3] = True
    trochlea = np.zeros((3, 4), dtype=np.bool_)
    trochlea[1, 0] = True
    patellar_rows = np.stack((patella, np.zeros_like(patella)))
    trochlear_rows = np.stack((np.zeros_like(trochlea), trochlea))
    middle_dark = np.ones((3, 4), dtype=np.bool_)
    middle_raw = np.full((3, 4), 99, dtype=np.int16)
    middle_available = np.ones((3, 4), dtype=np.bool_)
    arrays = {
        "a4_patellofemoral_patellar_cartilage_support": patellar_rows,
        "a4_patellofemoral_trochlear_cartilage_support": trochlear_rows,
        "b1_dark": middle_dark,
        "acquired_plane": middle_raw,
        "b1_available": middle_available,
        "b1_distance_mm": np.full((3, 4), 77.0, dtype=np.float32),
    }
    artifact = "study/series.npz.xz"
    (tmp_path / "study").mkdir()
    write_npz_xz(tmp_path / artifact, arrays.items())
    patellar_frame = {
        "origin_lps": [10.0, 20.0, 30.0],
        "basis_lps": [[0.0, -1.0], [1.0, 0.0], [0.0, 0.0]],
    }
    trochlear_frame = {
        "origin_lps": [-5.0, 8.0, 12.0],
        "basis_lps": [[0.5, 0.0], [0.0, 2.0], [0.0, 0.0]],
    }
    observations = [
        _observation(
            object="patellar_cartilage",
            support="a4_patellofemoral_patellar_cartilage_support",
            kind="reading",
            slices=[7],
            row=0,
            address_frame=patellar_frame,
            count=2,
        ),
        _observation(
            object="trochlear_cartilage",
            support="a4_patellofemoral_trochlear_cartilage_support",
            kind="reading",
            slices=[9],
            row=1,
            address_frame=trochlear_frame,
            count=1,
        ),
    ]
    record = _record(observations)
    record["plane_frame"] = FRAME
    record["arrays"] = {
        name: {"digest": digest(array)} for name, array in arrays.items()
    }
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
        prepared["spec"],
        tmp_path / "encoded.json.xz",
        prepared=prepared,
    )
    generated = [
        profile
        for profile in statuses["profiles"]
        if profile.get("retained_expansion") is not None
    ]
    assert len(generated) == 2
    by_object = {profile["object"]: profile for profile in generated}
    assert set(by_object) == {"patellar_cartilage", "trochlear_cartilage"}
    archive = Path(statuses["archive"])
    from knee.array_archive import open_arrays

    for name, expected_rc, expected_frame, expected_support in (
        (
            "patellar_cartilage",
            [[0, 1], [2, 3]],
            patellar_frame,
            "a4_patellofemoral_patellar_cartilage_support",
        ),
        (
            "trochlear_cartilage",
            [[1, 0]],
            trochlear_frame,
            "a4_patellofemoral_trochlear_cartilage_support",
        ),
    ):
        profile = by_object[name]
        outcome = profile["outcomes"][0]
        assert outcome["status"] == "ok"
        assert outcome["metadata"]["plane_frame"] == expected_frame
        assert outcome["metadata"]["plane_frame_source"] == "observation.address_frame"
        assert (
            outcome["metadata"]["source_refs"][expected_support]["artifact"] == artifact
        )
        assert set(outcome["metadata"]["source_refs"]) == {expected_support}
        context = outcome["metadata"]["context_sources"]
        assert profile["retained_address"]["slices"] == (
            [7] if name == "patellar_cartilage" else [9]
        )
        assert all(
            binding.get("source") == "unread"
            for binding in outcome["metadata"]["bindings"]
            if binding["bank"] != "acquisition_context"
        )
        with open_arrays(archive) as stored:
            points = stored[outcome["points_rc"]]
            assert points.tolist() == expected_rc

    for profile in generated:
        context = profile["outcomes"][0]["metadata"]["context_sources"]
        assert len(context) == 3
        assert all(item["source"] == "record_context" for item in context)
        assert [item["value"] for item in context] == ["Axial", "1", "1"]
        assert all(item["source_address"]["slice_index"] == 4 for item in context)
        assert not (
            {"b1_dark", "acquired_plane", "b1_available", "b1_distance_mm"}
            & set(profile["outcomes"][0]["metadata"]["source_refs"])
        )

    bad_frame = deepcopy(record)
    bad_frame["observations"][0]["address_frame"] = None
    profiles = _retained_ordinary_profiles([bad_frame], [])
    assert len(profiles) == 1
    from knee.encoding.operation import _retained_ordinary_dispositions

    dispositions = _retained_ordinary_dispositions([bad_frame], [], (), profiles)
    assert dispositions[0]["disposition"] == "missing_observation_address_frame"
