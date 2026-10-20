from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from knee.array_archive import write_npz_xz
from knee.collapse.posterior import FOLLOWED, START_NAMES
from knee.encoding.mri_coarse_spec import append_coarse_spec, make_mri_coarse_spec
from knee.encoding.mri_secondary_spec import TRACE_OBJECTS
from knee.encoding.mri_spec import make_mri_spec
from knee.encoding.operation import digest, encode_study, validate_spec


def _record(study: str, series: str, view: tuple[str, str, str], arrays: dict):
    return {
        "study_uid": study,
        "series_uid": series,
        "view": list(view),
        "slice_index": 2,
        "artifact": f"{study}/{series}-part.npz.xz",
        "arrays": {name: {"digest": digest(value)} for name, value in arrays.items()},
    }


def _run_family(
    tmp_path: Path, family: str, trace_name: str = "popliteal_artery"
) -> dict:
    spec = make_mri_spec()
    spec["storage"] = "npz_xz"
    spec.pop("object_composition")
    profile = next(
        item
        for item in spec["profiles"]
        if item.get("support_layout", {}).get("family") == family
        and (family != "posterior_trace" or item["object"] == trace_name)
    )
    study = f"study-{family}-{trace_name if family == 'posterior_trace' else 'one'}"
    view = (
        ("Axial", "1", "1")
        if family in ("fibula_axial", "joint_axial_profile_samples")
        else ("Sagittal", "0", "0")
    )
    if family == "fibula_axial":
        region = np.asarray(
            [
                [False, True, True, False],
                [False, False, True, True],
                [False, False, False, False],
            ],
            dtype=bool,
        )
        target = np.asarray(
            [
                [False, True, False, False],
                [False, False, True, False],
                [False, False, False, False],
            ],
            dtype=bool,
        )
        available = np.ones(region.shape, dtype=bool)
        arrays = {
            "a3_fibula_axial_region": region.ravel(),
            "a3_fibula_axial_target": target.ravel(),
            "a3_fibula_axial_available": available.ravel(),
            "a3_fibula_axial_offsets": np.asarray([0, region.size], dtype=np.int64),
            "a3_fibula_axial_shapes": np.asarray([region.shape], dtype=np.int32),
            "a3_fibula_axial_slices": np.asarray([7], dtype=np.int32),
            "a3_fibula_axial_origin_lps": np.asarray([[1.0, 2.0, 3.0]]),
            "a3_fibula_axial_basis_lps": np.asarray(
                [[[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]]
            ),
            "a3_fibula_axial_normal_lps": np.asarray([[0.0, 0.0, 1.0]]),
            "a3_fibula_axial_thickness_mm": np.asarray([3.0]),
        }
        observation = {
            "object": "fibula",
            "provenance": "native",
            "kind": "reading",
            "support": "a3_fibula_axial_region",
            "view": list(view),
            "series_uid": "target-axial",
            "slices": [7],
            "row": 0,
            "count": int(target.sum()),
            "code": "source_selected",
        }
        record = _record(study, "fibula-owner", view, arrays)
        record["artifact"] = f"{study}/fibula-owner-fibula.npz.xz"
        observation["artifact"] = record["artifact"]
        record["axial_evidence"] = [
            {
                "row": 0,
                "series_uid": "target-axial",
                "view": list(view),
                "slice": 7,
                "code": "source_selected",
                "target_pixels": int(target.sum()),
                "region_pixels": int(region.sum()),
            }
        ]
    elif family == "posterior_trace":
        support = f"a3_posterior_trace_{trace_name}_points_lps"
        prefix = support.removesuffix("_points_lps")
        arrays = {
            support: np.asarray([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float64),
            f"{prefix}_offsets": np.asarray([0, 2], dtype=np.int64),
            f"{prefix}_slices": np.asarray([5], dtype=np.int32),
            f"{prefix}_starts": np.asarray(
                [START_NAMES.index(FOLLOWED)], dtype=np.int8
            ),
            f"{prefix}_stops": np.asarray([[0, 0]], dtype=np.int8),
            f"{prefix}_light": np.asarray([12.0, 14.0], dtype=np.float32),
            f"{prefix}_flank": np.asarray([3.0, 5.0], dtype=np.float32),
        }
        view = ("Sagittal", "0", "0")
        observation = {
            "object": trace_name,
            "provenance": "native",
            "kind": "reading",
            "support": support,
            "view": list(view),
            "series_uid": f"{trace_name}-target",
            "slices": [5],
            "row": 0,
            "count": 2,
            "code": "tube_followed",
        }
        record = _record(study, f"{trace_name}-owner", view, arrays)
        record["artifact"] = f"{study}/{trace_name}-owner.npz.xz"
        observation["artifact"] = record["artifact"]
        target_record = _record(study, f"{trace_name}-target", view, {})
        target_record["observations"] = [observation]
    else:
        white = np.asarray([False, True, False], dtype=bool)
        arrays = {
            "a4_joint_axial_profile_offsets": np.asarray([0, 3], dtype=np.int64),
            "a4_joint_axial_profile_slices": np.asarray([6], dtype=np.int32),
            "a4_joint_axial_profile_rc": np.asarray(
                [[1, 2], [2, 3], [3, 4]], dtype=np.int64
            ),
            "a4_joint_axial_profile_valid": np.asarray([True, True, True], dtype=bool),
            "a4_joint_axial_profile_white": white,
            "a4_joint_axial_profile_light": np.asarray(
                [10.0, 20.0, 30.0], dtype=np.float32
            ),
        }
        observation = {
            "object": "joint",
            "provenance": "native",
            "kind": "reading",
            "support": "a4_joint_axial_profile_white",
            "view": list(view),
            "series_uid": "joint-series",
            "slices": [6],
            "row": 0,
            "count": int(white.sum()),
            "code": "sampled_white",
        }
        record = _record(study, "joint-series", view, arrays)
        observation["artifact"] = record["artifact"]
        record["axial_joint_compartment"] = {
            "pointed_planes": [
                {
                    "slice": 6,
                    "row": 0,
                    "support": observation["support"],
                    "code": observation["code"],
                    "count": observation["count"],
                }
            ]
        }
    if family != "posterior_trace":
        record["observations"] = [observation]
    run_root = tmp_path / family / "run"
    output_root = tmp_path / family / "out"
    archive_path = run_root / record["artifact"]
    archive_path.parent.mkdir(parents=True)
    write_npz_xz(archive_path, arrays.items())
    validated = validate_spec(spec)
    result = {
        "study_uid": study,
        "records": [record, target_record] if family == "posterior_trace" else [record],
        "main_records": [],
        "objects": {profile["object"]: {}},
    }
    return encode_study(
        result,
        run_root,
        run_root,
        validated["spec"],
        output_root / "encoded.json.xz",
        prepared=validated,
    )


def test_factory_declares_three_secondary_families_without_numeric_norms():
    spec = make_mri_spec()
    validated = validate_spec(spec)
    families = {
        p["support_layout"]["family"]: p
        for p in spec["profiles"]
        if isinstance(p.get("support_layout"), dict)
        and p["support_layout"].get("family")
        in {"fibula_axial", "posterior_trace", "joint_axial_profile_samples"}
    }
    assert set(families) == {
        "fibula_axial",
        "posterior_trace",
        "joint_axial_profile_samples",
    }
    assert {
        p["object"]
        for p in spec["profiles"]
        if p.get("support_layout", {}).get("family") == "posterior_trace"
    } == set(TRACE_OBJECTS)
    assert validated["composition"] is not None
    assert all(p["references"] == [] for p in families.values())
    assert all(p["view"] is None for p in families.values())
    for profile in spec["profiles"]:
        bindings = {(r["bank"], r["metric"]): r for r in profile["readings"]}
        for bank_name in (
            "fibula_packed_target",
            "posterior_trace_values",
            "axial_joint_samples",
        ):
            assert any(bank == bank_name for bank, _ in bindings)
    assert all(
        all(
            (binding["source"] == "unread")
            for binding in profile["readings"]
            if binding["bank"]
            in {"fibula_packed_target", "posterior_trace_values", "axial_joint_samples"}
        )
        for profile in spec["profiles"]
        if profile.get("support_layout", {}).get("family")
        not in {"fibula_axial", "posterior_trace", "joint_axial_profile_samples"}
    )


def test_encode_study_routes_each_existing_secondary_address_family(tmp_path):
    cases = [
        ("fibula_axial", None, "a3_fibula_axial_region", "ok"),
        *[
            (
                "posterior_trace",
                name,
                f"a3_posterior_trace_{name}_points_lps",
                "missing_reference",
            )
            for name in TRACE_OBJECTS
        ],
        (
            "joint_axial_profile_samples",
            None,
            "a4_joint_axial_profile_white",
            "missing_reference",
        ),
    ]
    for family, trace_name, support, expected_status in cases:
        statuses = _run_family(tmp_path, family, trace_name or "popliteal_artery")
        profile = next(p for p in statuses["profiles"] if p["support"] == support)
        outcome = profile["outcomes"][0]
        assert outcome["status"] == expected_status
        assert outcome["place_count"] > 0
        assert statuses["work"]["addressed_places"] >= outcome["place_count"]


def test_combined_base_coarse_and_secondary_declarations_share_one_layout():
    spec = make_mri_spec(include_coarse=True)
    validated = validate_spec(spec)
    bank_names = [bank["name"] for bank in spec["banks"]]
    assert bank_names == [
        "lens_boolean",
        "lens_raw_signal",
        "lens_distance",
        "acquisition_context",
        "native_profile_area",
        "native_profile_status",
        "coarse_unfiltered",
        "coarse_scale_filtered",
        "fibula_packed_target",
        "posterior_trace_values",
        "axial_joint_samples",
    ]
    assert validated["composition"] is not None
    for profile in spec["profiles"]:
        keys = [(binding["bank"], binding["metric"]) for binding in profile["readings"]]
        assert len(keys) == len(set(keys))
        assert len(keys) == sum(len(bank["metrics"]) for bank in spec["banks"])
    secondary_profiles = [
        profile
        for profile in spec["profiles"]
        if profile.get("support_layout", {}).get("family")
        in {"fibula_axial", "posterior_trace", "joint_axial_profile_samples"}
    ]
    assert secondary_profiles
    for profile in secondary_profiles:
        bindings = {(r["bank"], r["metric"]): r for r in profile["readings"]}
        for bank_name in ("coarse_unfiltered", "coarse_scale_filtered"):
            assert all(
                bindings[(bank_name, metric["name"])]["source"] == "unread"
                for bank in spec["banks"]
                if bank["name"] == bank_name
                for metric in bank["metrics"]
            )


def test_coarse_factory_and_append_after_secondary_keep_every_binding():
    coarse_factory = make_mri_coarse_spec()
    include_coarse = make_mri_spec(include_coarse=True)
    assert coarse_factory == include_coarse
    prepared = validate_spec(coarse_factory)
    assert prepared["composition"] is not None
    expected = {
        (bank["name"], metric["name"])
        for bank in coarse_factory["banks"]
        for metric in bank["metrics"]
    }
    assert len(coarse_factory["profiles"]) == 462
    for profile in coarse_factory["profiles"]:
        bindings = [(item["bank"], item["metric"]) for item in profile["readings"]]
        assert len(bindings) == len(set(bindings))
        assert set(bindings) == expected

    base_with_secondary = make_mri_spec()
    appended = append_coarse_spec(base_with_secondary)
    assert len(appended["banks"]) == 11
    assert len(base_with_secondary["banks"]) == 9
    validate_spec(appended)
    with pytest.raises(ValueError, match="coarse_banks_already_declared"):
        append_coarse_spec(appended)
