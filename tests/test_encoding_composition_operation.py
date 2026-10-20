"""One object consumes multiple actual views through the study publication path."""

from __future__ import annotations

from copy import deepcopy

import numpy as np
import pytest

from knee.array_archive import write_npz_xz
from knee.encoding.operation import encode_study, validate_spec
from knee.encoding.product import open_product
from knee.json_store import dump_json_atomic
from knee.receipt import digest


def _case(tmp_path):
    run = tmp_path / "recognition"
    run.mkdir()
    views = [["Sagittal", "0", "0"], ["Coronal", "0", "0"]]
    records = []
    profiles = []
    for index, view in enumerate(views):
        artifact = f"study/series-{index}.npz.xz"
        arrays = {
            "mask": np.eye(2, dtype=bool),
            "dark": np.array([[False, False], [False, True]]),
            "available": np.ones((2, 2), dtype=bool),
        }
        (run / artifact).parent.mkdir(exist_ok=True)
        write_npz_xz(run / artifact, arrays)
        observation = {
            "object": "femur",
            "series_uid": f"series-{index}",
            "view": view,
            "slices": [0],
            "artifact": artifact,
            "support": "mask",
            "row": None,
            "label": None,
            "count": 2,
            "provenance": "native",
            "kind": "resolved",
        }
        records.append(
            {
                "study_uid": "study",
                "series_uid": observation["series_uid"],
                "view": view,
                "slice_index": 0,
                "artifact": artifact,
                "observations": [observation],
                "arrays": {name: {"digest": digest(a)} for name, a in arrays.items()},
                "plane_frame": {
                    "origin_lps": [0.0, 0.0, 0.0],
                    "basis_lps": (
                        [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]]
                        if index == 0
                        else [[1.0, 0.0], [0.0, 0.0], [0.0, 1.0]]
                    ),
                },
            }
        )
        profiles.append(
            {
                "object": "femur",
                "view": view,
                "provenance": "native",
                "kind": "resolved",
                "support": "mask",
                "readings": [
                    {
                        "bank": "darkness",
                        "metric": "dark",
                        "value": "dark",
                        "available": "available",
                    }
                ],
                "references": [],
            }
        )
    spec = {
        "version": "mechanical-fixture-only-v1",
        "banks": [
            {
                "name": "darkness",
                "facet": "boolean measurement",
                "metrics": [
                    {"name": "dark", "kind": "words", "words": ["False", "True"]}
                ],
            }
        ],
        "profiles": profiles,
        "object_composition": {
            "version": "knee-mps-object-v1",
            "view_roles": [*views, ["Axial", "1", "1"]],
            "bank_plans": [
                {
                    "base_bank": "darkness",
                    "lens": "darkness",
                    "scale_scope": "native-place",
                }
            ],
        },
    }
    result = {
        "study_uid": "study",
        "records": records,
        "main_records": [],
        "objects": {
            "femur": {
                "anatomical_relations": [
                    {
                        "relation": "articulates_with",
                        "object": "tibia",
                        "source": "fixture-definition",
                    }
                ]
            }
        },
        "study_map": {
            "schema": "study_map/v1",
            "knee": "R",
            "scale": {"mm": 10.0, "source": "fixture geometry", "code": "measured"},
            "objects": {
                "femur": {
                    "status": "complete",
                    "point_lps": [0.0, 0.0, 0.0],
                    "precision_mm": [0.25, 0.25, 0.25],
                    "key_planes": {
                        "sagittal": {"slice": 0},
                        "coronal": {"slice": 0},
                        "axial": {"slice": 1},
                    },
                }
            },
        },
    }
    return run, result, spec


@pytest.mark.parametrize("storage", ["npz_xz", "h5"])
def test_one_published_object_keeps_view_and_direction_in_encoded_facets(
    tmp_path, storage
):
    if storage == "h5":
        pytest.importorskip("h5py")
    run, result, spec = _case(tmp_path)
    spec["storage"] = storage
    publication = encode_study(result, run, run, spec, tmp_path / "encoded.json")
    with open_product(publication["manifest"]) as product:
        composed = product.manifest["object_composition"]
        assert composed["schema"] == "knee_object_profiles/v1"
        assert list(composed["objects"]) == ["femur"]
        femur = composed["objects"]["femur"]
        assert femur["assembly"]["code"] == "ok"
        assert sum(count for _, _, count in femur["sparse_counts"]) == 8
        assert len({bank for bank, _, _ in femur["sparse_counts"]}) == 6
        assert femur["spatial_context"]["keyplanes"]["axial"]["slice"] == 1
        assert product.manifest["object_contexts"]["femur"]["anatomical_relations"]
        for descriptor in product.manifest["encoded_arrays"].values():
            assert descriptor["digest"]
        for name in product.arrays:
            assert (
                digest(product.arrays[name])
                == product.manifest["encoded_arrays"][name]["digest"]
            )
    assert result["objects"]["femur"]["encoding_object"]["object"] == "femur"


def test_repeated_observation_links_do_not_add_evidence_votes(tmp_path):
    run, result, spec = _case(tmp_path)
    spec["profiles"].append(deepcopy(spec["profiles"][0]))
    publication = encode_study(result, run, run, spec, tmp_path / "encoded.json")
    with open_product(publication["manifest"]) as product:
        femur = product.manifest["object_composition"]["objects"]["femur"]
        assert sum(count for _, _, count in femur["sparse_counts"]) == 8
        assert sum(b["duplicate"] for b in femur["assembly"]["batches"]) == 4
    assert publication["work"]["opened_artifacts"] == 2


def test_unavailable_geometry_keeps_known_measurements_in_overview(tmp_path):
    run, result, spec = _case(tmp_path)
    result.pop("study_map")
    publication = encode_study(result, run, run, spec, tmp_path / "encoded.json")
    with open_product(publication["manifest"]) as product:
        composed = product.manifest["object_composition"]
        assert composed["study_map_source"]["status"] == "study_map_not_retained"
        femur = composed["objects"]["femur"]
        assert sum(count for _, _, count in femur["sparse_counts"]) == 4
        assert femur["spatial_context"]["code"] == "invalid_map"
        assert all(
            b["facet_coordinate"]["direction"] is None
            for b in femur["assembly"]["batches"]
        )


def test_invalid_composition_refuses_before_source_files_are_opened(tmp_path):
    _, _, spec = _case(tmp_path)
    spec["object_composition"]["view_roles"] = []
    with pytest.raises(ValueError, match="invalid_object_composition"):
        validate_spec(spec)


def test_real_producer_map_pointer_is_on_record_while_result_holds_counts(tmp_path):
    run, result, spec = _case(tmp_path)
    actual = dump_json_atomic(run / "study" / "study_map.json", result["study_map"])
    result["records"][0]["study_map"] = {"file": str(actual.relative_to(run))}
    result["study_map"] = {"objects": 1, "complete": 1, "partial": 0}
    publication = encode_study(result, run, run, spec, tmp_path / "encoded.json")
    with open_product(publication["manifest"]) as product:
        composed = product.manifest["object_composition"]
        assert composed["study_map_source"]["status"] == "ok"
        assert composed["objects"]["femur"]["spatial_context"]["code"] == "ok"
        assert (
            sum(count for _, _, count in composed["objects"]["femur"]["sparse_counts"])
            == 8
        )
